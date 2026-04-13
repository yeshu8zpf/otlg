
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

# ============================================================
# Path setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology_draft import OntologyDraft
from normalize import normalize_model_output_robust
from burr_compare import run_compare
from ontology_tools import (
    SchemaProfiler,
    InstanceProfiler,
    PatternDetector,
    HypothesisStore,
    MappingVerifierLite,
)

# ============================================================
# Scenario helpers
# ============================================================

COPY_RE = re.compile(
    r"""\\copy\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*\([^)]*\))?\s+FROM\s+'([^']+)'""",
    re.IGNORECASE,
)

CREATE_TABLE_RE = re.compile(
    r"""CREATE\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\);""",
    re.IGNORECASE | re.DOTALL,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path) -> Optional[Any]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_copy(path: Path, dst: Path) -> None:
    if path.exists() and path.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


def classify_sql_file(path: Path) -> str:
    name = path.name.lower()
    fk_positive = ["_fk.", "_fks.", "fk.sql", "fks.sql", "schema_pg_fks", "with_fk", "with_fks"]
    fk_negative = ["no_fk", "nofk", "without_fk", "withoutfks"]

    if any(tok in name for tok in fk_negative):
        return "no_fk"
    if any(tok in name for tok in fk_positive):
        return "fk"

    text = read_text(path).lower()
    if "foreign key" in text or " references " in text:
        return "fk"

    return "unknown"


def find_schema_sql(scenario_dir: Path, fk_mode: str = "auto") -> Path:
    candidates = sorted(scenario_dir.glob("*.sql"), key=lambda p: p.name)
    if not candidates:
        raise FileNotFoundError(f"No .sql file found in {scenario_dir}")

    classified = [(classify_sql_file(p), p) for p in candidates]
    fk_files = [p for c, p in classified if c == "fk"]
    no_fk_files = [p for c, p in classified if c == "no_fk"]
    unknown_files = [p for c, p in classified if c == "unknown"]

    def choose_best_default() -> Path:
        scored = []
        for p in candidates:
            name = p.name.lower()
            score = 0
            if name == "schema.sql":
                score += 100
            if "schema" in name:
                score += 30
            if "fk" in name or "fks" in name:
                score += 20
            if "pg" in name:
                score += 5
            scored.append((score, -len(name), p))
        scored.sort(key=lambda x: (-x[0], x[1], x[2].name))
        return scored[0][2]

    if fk_mode == "fk":
        if fk_files:
            return sorted(fk_files, key=lambda p: p.name)[0]
        return choose_best_default()

    if fk_mode == "no_fk":
        if no_fk_files:
            return sorted(no_fk_files, key=lambda p: p.name)[0]
        if unknown_files:
            return sorted(unknown_files, key=lambda p: p.name)[0]
        return choose_best_default()

    if fk_mode == "auto":
        return choose_best_default()

    raise ValueError(f"Unsupported fk_mode={fk_mode}")


def parse_copy_sources(schema_sql_text: str) -> List[Tuple[str, str]]:
    return COPY_RE.findall(schema_sql_text)


def resolve_csv_path(scenario_dir: Path, rel_csv_path: str) -> Optional[Path]:
    p1 = (scenario_dir / rel_csv_path).resolve()
    if p1.exists():
        return p1
    p2 = (scenario_dir / Path(rel_csv_path).name).resolve()
    if p2.exists():
        return p2
    return None


def load_sample_rows_from_csv(
    scenario_dir: Path,
    schema_sql_text: str,
    max_rows_per_table: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    samples: Dict[str, List[Dict[str, Any]]] = {}
    copy_entries = parse_copy_sources(schema_sql_text)

    for table_name, rel_csv_path in copy_entries:
        csv_path = resolve_csv_path(scenario_dir, rel_csv_path)
        if csv_path is None:
            continue

        rows: List[Dict[str, Any]] = []
        try:
            with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    rows.append(dict(row))
                    if i + 1 >= max_rows_per_table:
                        break
        except Exception:
            continue

        samples[table_name] = rows

    return samples


def extract_table_definitions(schema_sql_text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for table_name, body in CREATE_TABLE_RE.findall(schema_sql_text):
        lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
        out[table_name] = "\n".join(lines).strip()
    return out


def compact_table_definitions(
    table_defs: Dict[str, str],
    max_tables: int = 40,
    max_chars_per_table: int = 1200,
) -> Dict[str, str]:
    items = sorted(table_defs.items(), key=lambda kv: kv[0])[:max_tables]
    compact: Dict[str, str] = {}
    for table_name, definition in items:
        text = definition.strip()
        if len(text) > max_chars_per_table:
            text = text[:max_chars_per_table].rstrip() + "\n... [truncated]"
        compact[table_name] = text
    return compact


def clean_schema_sql_for_prompt(schema_sql_text: str) -> str:
    text = schema_sql_text or ""
    text = re.sub(r"(?m)^\s*\\.*?$", "", text)
    text = re.sub(r"(?im)^\s*(DROP DATABASE|CREATE DATABASE|SELECT pg_terminate_backend|SET\s+default_.*?).*$", "", text)
    text = re.sub(r"(?is)INSERT\s+INTO\s+.*?;\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def summarize_top_level_counts(obj: Dict[str, Any]) -> Dict[str, int]:
    return {
        "num_classes": len(obj.get("classes", []) or []),
        "num_data_properties": len(obj.get("data_properties", []) or []),
        "num_object_properties": len(obj.get("object_properties", []) or []),
        "num_subclass_relations": len(obj.get("subclass_relations", []) or []),
        "num_class_mappings": len(obj.get("class_mappings", []) or []),
        "num_data_property_mappings": len(obj.get("data_property_mappings", []) or []),
        "num_object_property_mappings": len(obj.get("object_property_mappings", []) or []),
    }


def safe_exception_payload(e: Exception) -> Dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
    }


# ============================================================
# GT helpers (robust to Burr micro_benchmark and real-world)
# ============================================================

def resolve_gt_artifacts_for_scenario(scenario_dir: Path) -> Dict[str, Any]:
    """
    Returns a JSON-serializable summary of GT artifacts for a Burr scenario.
    """
    direct_mapping = scenario_dir / "mapping.json"
    mappings_dir = scenario_dir / "mappings"
    meta_json = scenario_dir / "meta.json"

    result: Dict[str, Any] = {
        "kind": "missing",
        "mapping_json": None,
        "mappings_dir": None,
        "meta_json": str(meta_json) if meta_json.exists() and meta_json.is_file() else None,
        "extra_files": [],
    }

    if direct_mapping.exists() and direct_mapping.is_file():
        extras: List[str] = []
        for name in ["mapping.ttl", "test_mapping.ttl"]:
            p = scenario_dir / name
            if p.exists() and p.is_file():
                extras.append(str(p))

        result["kind"] = "single_json"
        result["mapping_json"] = str(direct_mapping)
        result["extra_files"] = extras
        return result

    if mappings_dir.exists() and mappings_dir.is_dir():
        result["kind"] = "mapping_dir"
        result["mappings_dir"] = str(mappings_dir)
        result["extra_files"] = sorted(
            [str(p) for p in mappings_dir.iterdir() if p.is_file()],
            key=lambda x: x,
        )
        return result

    return result


def copy_gt_artifacts_for_scenario(scenario_dir: Path, out_dir: Path) -> Dict[str, Any]:
    gt_info = resolve_gt_artifacts_for_scenario(scenario_dir)
    copied: List[str] = []

    if gt_info["kind"] == "single_json":
        dst = out_dir / "gt.mapping.json"
        maybe_copy(gt_info["mapping_json"], dst)
        copied.append(str(dst))
        for p in gt_info["extra_files"]:
            dst_extra = out_dir / f"gt.{p.name}"
            maybe_copy(p, dst_extra)
            copied.append(str(dst_extra))

    elif gt_info["kind"] == "mapping_dir":
        dst_dir = out_dir / "gt.mappings"
        dst_dir.mkdir(parents=True, exist_ok=True)
        for p in gt_info["extra_files"]:
            dst = dst_dir / p.name
            maybe_copy(p, dst)
            copied.append(str(dst))

    if gt_info["meta_json"] is not None:
        dst_meta = out_dir / "gt.meta.json"
        maybe_copy(gt_info["meta_json"], dst_meta)
        copied.append(str(dst_meta))

    return {
        "gt_kind": gt_info["kind"],
        "copied_files": copied,
        "mapping_json": str(gt_info["mapping_json"]) if gt_info["mapping_json"] else None,
        "mappings_dir": str(gt_info["mappings_dir"]) if gt_info["mappings_dir"] else None,
        "meta_json": str(gt_info["meta_json"]) if gt_info["meta_json"] else None,
    }


# ============================================================
# Prompting
# ============================================================

SYSTEM_PROMPT = """You are an ontology learning assistant for relational databases.

Your task:
Given a relational database schema, optional sampled rows, and optional tool-derived structural evidence,
construct:
1. a relational-database-derived ontology draft
2. executable mappings from database elements to ontology elements

Important:
- Focus on ontology structure and mappings, not only naming.
- Be conservative: do not add inverse object properties unless strongly justified.
- Use tool-derived evidence when available.
- Output ONLY valid JSON.
"""

USER_PROMPT_TEMPLATE = """You are given a relational database scenario.

## Scenario path
{scenario_path}

{schema_sql_section}
{table_defs_section}
{sample_rows_section}
{tool_context_section}

## Output format
Return a JSON object with the following top-level keys:
- classes
- data_properties
- object_properties
- subclass_relations
- class_mappings
- data_property_mappings
- object_property_mappings
- diagnostics

### Canonical constraints
- Use exact top-level keys listed above.
- For classes, use fields:
  - id
  - label
  - status
  - confidence
  - description (optional)
- For data_properties, use fields:
  - id
  - label
  - domain
  - range
  - status
  - confidence
- For object_properties, use fields:
  - id
  - label
  - domain
  - range
  - join_paths
  - status
  - confidence
- For class_mappings, use fields:
  - class_id
  - instance_id_template
  - from_tables
  - identifier_columns
  - status
  - confidence
- For data_property_mappings, use fields:
  - data_property_id
  - source_table
  - source_columns
  - applies_to_class
  - value_template
  - status
  - confidence
- For object_property_mappings, use fields:
  - object_property_id
  - from_class
  - to_class
  - from_tables
  - join_paths
  - source_identifier_columns
  - target_identifier_columns
  - status
  - confidence

### Join path format
Use ONLY this format:
[
  ["hotel.id", "=", "room.hotel_id"]
]

Do not output join_paths as objects or free-form strings.

### Important modeling guidance
- Prefer one object property direction unless the inverse is explicitly necessary.
- If a table is a weak entity, its identifier should reflect dependency.
- If a table is a pure connector table, prefer a relationship rather than a class.
- If a connector table has meaningful extra attributes, consider reification.
- Do not invent domain properties unsupported by schema or samples.
- When tool-derived evidence is present, treat it as strong structural guidance.

Return JSON only.
"""


def build_prompt(
    scenario_path: Path,
    schema_sql_text: str,
    table_defs: Dict[str, str],
    sample_rows: Dict[str, List[Dict[str, Any]]],
    tool_context: Dict[str, Any],
    *,
    include_schema_sql: bool,
    include_table_defs: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
) -> str:
    schema_sql_section = ""
    if include_schema_sql:
        schema_sql_section = "## Compact schema SQL\n" + clean_schema_sql_for_prompt(schema_sql_text) + "\n"

    table_defs_section = ""
    if include_table_defs:
        table_defs_section = "## Parsed table definitions\n" + json.dumps(
            compact_table_definitions(table_defs), indent=2, ensure_ascii=False
        ) + "\n"

    sample_rows_section = ""
    if include_sample_rows:
        compact_sample_rows = {k: v[:3] for k, v in sorted(sample_rows.items())}
        sample_rows_section = "## Sample rows\n" + json.dumps(
            compact_sample_rows, indent=2, ensure_ascii=False
        ) + "\n"

    tool_context_section = ""
    if include_tool_context:
        tool_context_section = "## Tool-derived structural evidence\n" + json.dumps(
            tool_context, indent=2, ensure_ascii=False
        ) + "\n"

    return USER_PROMPT_TEMPLATE.format(
        scenario_path=str(scenario_path),
        schema_sql_section=schema_sql_section,
        table_defs_section=table_defs_section,
        sample_rows_section=sample_rows_section,
        tool_context_section=tool_context_section,
    )


# ============================================================
# LLM call
# ============================================================

def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return api_key


def extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end + 1]
        return json.loads(snippet)

    raise ValueError(f"Failed to parse JSON object from model output:\n{text[:3000]}")

import json
import time
import httpx
from typing import Any, Dict, Optional, Tuple

def call_llm_json_stream(
    prompt: str,
    model: str = "gpt-5.4-mini",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    timeout: float = 300.0,
    max_retries: int = 3,
    retry_backoff_base: float = 2.0,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "stream": True,
    }

    timeout_cfg = httpx.Timeout(
        connect=min(30.0, timeout),
        read=timeout,
        write=min(60.0, timeout),
        pool=min(30.0, timeout),
    )

    llm_meta: Dict[str, Any] = {
        "model": model,
        "api_url": api_url,
        "timeout": timeout,
        "max_retries": max_retries,
        "attempts": [],
    }

    last_exc: Optional[Exception] = None
    retryable_statuses = {429, 500, 502, 503, 504, 524}

    for attempt in range(1, max_retries + 1):
        attempt_meta: Dict[str, Any] = {"attempt": attempt, "status": "started"}
        chunks = []

        try:
            with httpx.Client(trust_env=False, http2=False, timeout=timeout_cfg) as client:
                with client.stream("POST", api_url, headers=headers, json=payload) as r:
                    attempt_meta["status_code"] = r.status_code
                    attempt_meta["response_headers"] = dict(r.headers)

                    if r.status_code != 200:
                        text = r.read().decode("utf-8", errors="replace")
                        attempt_meta["status"] = "http_error"
                        attempt_meta["response_text_preview"] = text[:5000]
                        llm_meta["attempts"].append(attempt_meta)

                        if r.status_code in retryable_statuses and attempt < max_retries:
                            time.sleep(retry_backoff_base ** (attempt - 1))
                            continue

                        raise RuntimeError(
                            f"LLM request failed with status {r.status_code}\nResponse: {text}"
                        )

                    for line in r.iter_lines():
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if not line.startswith("data: "):
                            continue

                        data = json.loads(line[6:])
                        choices = data.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            chunks.append(content)

            text = "".join(chunks)
            attempt_meta["raw_content_preview"] = text[:5000]
            model_json = extract_json_object(text)

            attempt_meta["status"] = "ok"
            llm_meta["attempts"].append(attempt_meta)
            llm_meta["status_code"] = 200
            llm_meta["response_headers"] = attempt_meta.get("response_headers", {})
            llm_meta["raw_content_preview"] = text[:5000]

            return model_json, llm_meta

        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            last_exc = e
            attempt_meta["status"] = "timeout"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                time.sleep(retry_backoff_base ** (attempt - 1))
                continue

        except httpx.HTTPError as e:
            last_exc = e
            attempt_meta["status"] = "httpx_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                time.sleep(retry_backoff_base ** (attempt - 1))
                continue

        except Exception as e:
            last_exc = e
            attempt_meta["status"] = "other_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)
            raise

    raise RuntimeError(
        f"LLM request failed after {max_retries} attempts. "
        f"Last error: {type(last_exc).__name__}: {last_exc}"
    ) from last_exc
# ============================================================
# Tool selection / compression
# ============================================================

ALL_TOOLS = {
    "schema_profiler",
    "instance_profiler",
    "pattern_detector",
    "mapping_verifier_lite",
}


def parse_enabled_tools(raw: str) -> Set[str]:
    items = {x.strip() for x in (raw or "").split(",") if x.strip()}
    unknown = sorted(items - ALL_TOOLS)
    if unknown:
        raise ValueError(f"Unknown tools: {unknown}. Supported: {sorted(ALL_TOOLS)}")
    return items


def compress_hypotheses_for_prompt(hypotheses: List[Dict[str, Any]], max_items: int = 20) -> List[Dict[str, Any]]:
    ranked = sorted(
        hypotheses,
        key=lambda x: (float(x.get("confidence", 0.0)), x.get("kind", "")),
        reverse=True,
    )
    out = []
    for h in ranked[:max_items]:
        out.append(
            {
                "kind": h.get("kind"),
                "statement": h.get("statement"),
                "confidence": h.get("confidence"),
                "payload": h.get("payload", {}),
                "evidence": h.get("evidence", [])[:3],
            }
        )
    return out


def build_tool_context(
    schema_profile: Optional[Dict[str, Any]],
    instance_profile: Optional[Dict[str, Any]],
    hypothesis_store: Optional[HypothesisStore],
    enabled_tools: Set[str],
) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {"enabled_tools": sorted(enabled_tools)}
    if schema_profile is not None:
        ctx["schema_summary"] = schema_profile.get("stats", {})
        ctx["join_graph"] = schema_profile.get("join_graph", {})
    if instance_profile is not None:
        ctx["instance_summary"] = {
            "tables": {
                t: {
                    "num_rows_sampled": prof.get("num_rows_sampled", 0),
                    "columns": {
                        c: {
                            "guessed_type": cp.get("guessed_type"),
                            "is_boolean_like": cp.get("is_boolean_like"),
                            "distinct_ratio": cp.get("distinct_ratio"),
                            "sample_values": cp.get("sample_values", [])[:5],
                        }
                        for c, cp in prof.get("columns", {}).items()
                    },
                }
                for t, prof in instance_profile.get("tables", {}).items()
            },
            "cross_table_value_overlap": instance_profile.get("cross_table_value_overlap", [])[:15],
        }
    if hypothesis_store is not None:
        ctx["hypothesis_summary"] = hypothesis_store.summary()
        ctx["hypotheses"] = compress_hypotheses_for_prompt(
            [h.to_dict() for h in hypothesis_store.items.values()],
            max_items=20,
        )
        ctx["revision_guidance"] = hypothesis_store.build_revision_guidance(max_items=15)
    return ctx


# ============================================================
# Core
# ============================================================

def run_tool_augmented_baseline(
    scenario_dir: Path,
    model: str = "gpt-5.4-nano",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    max_rows_per_table: int = 3,
    timeout: float = 300.0,
    schema_path: Optional[Path] = None,
    fk_mode: str = "auto",
    enabled_tools: Optional[Set[str]] = None,
    include_schema_sql: bool = False,
    include_table_defs: bool = True,
    include_sample_rows: bool = False,
    include_tool_context: bool = True,
) -> Tuple[OntologyDraft, Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    if enabled_tools is None:
        enabled_tools = {"schema_profiler"}

    if schema_path is None:
        schema_path = find_schema_sql(scenario_dir, fk_mode=fk_mode)
    else:
        schema_path = schema_path.resolve()

    schema_sql_text = read_text(schema_path)
    table_defs = extract_table_definitions(schema_sql_text)

    need_sample_rows = include_sample_rows or "instance_profiler" in enabled_tools or "pattern_detector" in enabled_tools
    sample_rows = load_sample_rows_from_csv(
        scenario_dir=scenario_dir,
        schema_sql_text=schema_sql_text,
        max_rows_per_table=max_rows_per_table,
    ) if need_sample_rows else {}

    schema_profile: Optional[Dict[str, Any]] = None
    instance_profile: Optional[Dict[str, Any]] = None
    store: Optional[HypothesisStore] = None

    if "schema_profiler" in enabled_tools or "pattern_detector" in enabled_tools:
        schema_profile = SchemaProfiler().profile(schema_sql_text)

    if "instance_profiler" in enabled_tools or "pattern_detector" in enabled_tools:
        instance_profile = InstanceProfiler().profile(sample_rows)

    if "pattern_detector" in enabled_tools:
        if schema_profile is None:
            schema_profile = SchemaProfiler().profile(schema_sql_text)
        if instance_profile is None:
            instance_profile = InstanceProfiler().profile(sample_rows)
        hypotheses = PatternDetector().detect(schema_profile, instance_profile)
        store = HypothesisStore()
        for h in hypotheses:
            store.add(h)

    tool_context = build_tool_context(schema_profile, instance_profile, store, enabled_tools)

    prompt = build_prompt(
        scenario_path=scenario_dir,
        schema_sql_text=schema_sql_text,
        table_defs=table_defs,
        sample_rows=sample_rows,
        tool_context=tool_context,
        include_schema_sql=include_schema_sql,
        include_table_defs=include_table_defs,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
    )

    raw_model_json, llm_meta = call_llm_json_stream(
        prompt=prompt,
        model=model,
        api_url=api_url,
        timeout=timeout,
    )

    normalized_model_json = normalize_model_output_robust(raw_model_json)
    draft = OntologyDraft.from_dict(normalized_model_json, already_normalized=True)

    lite_verification = None
    verification_feedback = None

    if "mapping_verifier_lite" in enabled_tools:
        lite_verifier = MappingVerifierLite()
        lite_verification = lite_verifier.verify_draft_dict(draft.to_dict())

        if store is not None and lite_verification is not None:
            verification_feedback = store.resolve_from_verifier_report(lite_verification)

    burr_mapping = draft.to_burr_mapping()
    validate_ok, validate_errors = draft.validate()

    meta = {
        "scenario_dir": str(scenario_dir),
        "schema_path": str(schema_path),
        "fk_mode": fk_mode,
        "model": model,
        "api_url": api_url,
        "prompt_chars": len(prompt),
        "enabled_tools": sorted(enabled_tools),
        "prompt_includes": {
            "schema_sql": include_schema_sql,
            "table_defs": include_table_defs,
            "sample_rows": include_sample_rows,
            "tool_context": include_tool_context,
        },
        "raw_model_top_level_counts": summarize_top_level_counts(raw_model_json),
        "normalized_top_level_counts": summarize_top_level_counts(normalized_model_json),
        "draft_validation": {
            "ok": validate_ok,
            "num_errors": len(validate_errors),
            "errors": validate_errors,
        },
        "lite_verification": lite_verification,
        "verification_feedback": verification_feedback,
        "tool_context_summary": {
            "schema_summary": schema_profile.get("stats", {}) if schema_profile else {},
            "hypothesis_summary": store.summary() if store else {},
            "num_cross_table_value_overlap": len(instance_profile.get("cross_table_value_overlap", [])) if instance_profile else 0,
        },
        "llm_meta": llm_meta,
        "normalization_report": draft.normalization_report(),
    }

    tool_artifacts = {
        "schema_profile": schema_profile,
        "instance_profile": instance_profile,
        "hypotheses": store.to_dict() if store else None,
        "tool_context": tool_context,
        "prompt": prompt,
        "verification_feedback": verification_feedback,
    }

    return draft, burr_mapping, meta, raw_model_json, tool_artifacts


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tool-augmented ontology learning orchestrator with selectable tools and prompt sections."
    )
    parser.add_argument("--scenario-dir", type=str, default="burr_benchmark/real-world/mondial") # burr_benchmark/micro_benchmark/nm_tables/composite_keys/university_1
    parser.add_argument("--schema-path", type=str, default=None)
    parser.add_argument("--fk-mode", type=str, default="auto", choices=["auto", "fk", "no_fk"])
    parser.add_argument("--model", type=str, default="gpt-5.4-nano")
    parser.add_argument("--api-url", type=str, default="https://www.aiapikey.net/v1/chat/completions")
    parser.add_argument("--max-rows-per-table", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--out-dir", type=str, default="outputs/tool_augmented")
    parser.add_argument("--run-burr-compare", action="store_true")
    parser.add_argument("--meta-path", type=str, default=None)
    parser.add_argument("--database-name", type=str, default=None)

    parser.add_argument(
        "--enabled-tools",
        type=str,
        default="",
        help="Comma-separated from: schema_profiler,instance_profiler,pattern_detector,mapping_verifier_lite",
    )
    parser.add_argument("--include-schema-sql", action="store_true")
    parser.add_argument("--include-sample-rows", action="store_true")
    parser.add_argument("--include-tool-context", action="store_true")
    parser.add_argument("--copy-gt-artifacts", action="store_true")
    parser.set_defaults(run_burr_compare=True)

    args = parser.parse_args()

    scenario_dir = Path(args.scenario_dir).resolve()
    schema_path = Path(args.schema_path).resolve() if args.schema_path else None
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    enabled_tools = parse_enabled_tools(args.enabled_tools)

    include_schema_sql = bool(args.include_schema_sql)
    include_table_defs = True
    include_sample_rows = bool(args.include_sample_rows)
    include_tool_context = True if not args.include_tool_context else True

    try:
        draft, burr_mapping, meta, raw_model_json, tool_artifacts = run_tool_augmented_baseline(
            scenario_dir=scenario_dir,
            schema_path=schema_path,
            fk_mode=args.fk_mode,
            model=args.model,
            api_url=args.api_url,
            max_rows_per_table=args.max_rows_per_table,
            timeout=args.timeout,
            enabled_tools=enabled_tools,
            include_schema_sql=include_schema_sql,
            include_table_defs=include_table_defs,
            include_sample_rows=include_sample_rows,
            include_tool_context=include_tool_context,
        )
    except Exception as e:
        fail_meta = {
            "scenario_dir": str(scenario_dir),
            "schema_path": str(schema_path) if schema_path else None,
            "fk_mode": args.fk_mode,
            "model": args.model,
            "api_url": args.api_url,
            "enabled_tools": sorted(enabled_tools),
            "error": safe_exception_payload(e),
        }
        write_json(out_dir / "failed.meta.json", fail_meta)
        raise

    normalized = normalize_model_output_robust(raw_model_json)

    write_json(out_dir / "raw_model.json", raw_model_json)
    write_json(out_dir / "normalized.json", normalized)
    write_json(out_dir / "draft.json", draft.to_dict())
    write_json(out_dir / "mapping.json", burr_mapping)

    if args.copy_gt_artifacts:
        meta["gt_artifacts"] = copy_gt_artifacts_for_scenario(scenario_dir, out_dir)
    else:
        meta["gt_artifacts"] = resolve_gt_artifacts_for_scenario(scenario_dir)

    write_json(out_dir / "meta.json", meta)

    if tool_artifacts["schema_profile"] is not None:
        write_json(out_dir / "schema_profile.json", tool_artifacts["schema_profile"])
    if tool_artifacts["instance_profile"] is not None:
        write_json(out_dir / "instance_profile.json", tool_artifacts["instance_profile"])
    if tool_artifacts["hypotheses"] is not None:
        write_json(out_dir / "hypotheses.json", tool_artifacts["hypotheses"])

    write_json(out_dir / "tool_context.json", tool_artifacts["tool_context"])
    write_text(out_dir / "prompt.md", tool_artifacts["prompt"])

    if args.run_burr_compare:
        try:
            compare_result = run_compare(
                scenario_dir=scenario_dir,
                pred_mapping_path=out_dir / "mapping.json",
                gt_mapping_path=None,
                meta_path=Path(args.meta_path).resolve() if args.meta_path else None,
                database_name=args.database_name or scenario_dir.name,
            )
            write_json(out_dir / "compare.json", compare_result)
        except Exception as e:
            write_json(out_dir / "compare_error.json", safe_exception_payload(e))

    print(f"[OK] scenario: {scenario_dir}")
    print(f"[OK] raw model: {out_dir / 'raw_model.json'}")
    print(f"[OK] normalized: {out_dir / 'normalized.json'}")
    print(f"[OK] draft: {out_dir / 'draft.json'}")
    print(f"[OK] mapping: {out_dir / 'mapping.json'}")
    print(f"[OK] meta: {out_dir / 'meta.json'}")
    print(f"[OK] tool context: {out_dir / 'tool_context.json'}")
    print(f"[OK] prompt: {out_dir / 'prompt.md'}")
    if (out_dir / 'schema_profile.json').exists():
        print(f"[OK] schema profile: {out_dir / 'schema_profile.json'}")
    if (out_dir / 'instance_profile.json').exists():
        print(f"[OK] instance profile: {out_dir / 'instance_profile.json'}")
    if (out_dir / 'hypotheses.json').exists():
        print(f"[OK] hypotheses: {out_dir / 'hypotheses.json'}")
    if args.run_burr_compare:
        if (out_dir / 'compare.json').exists():
            print(f"[OK] compare: {out_dir / 'compare.json'}")
        elif (out_dir / 'compare_error.json').exists():
            print(f"[WARN] compare failed: {out_dir / 'compare_error.json'}")


if __name__ == "__main__":
    main()
