from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import traceback
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import httpx


# ============================================================
# Project imports
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology_draft import OntologyDraft
from mapping_verifier import MappingVerifier
from normalize import normalize_model_output_robust
from burr_compare import run_compare


# ============================================================
# Read Burr scenario
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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def classify_sql_file(path: Path) -> str:
    """
    Roughly classify a SQL file into:
      - 'fk': likely FK-enriched schema
      - 'no_fk': likely original / no-FK schema
      - 'unknown': cannot tell confidently
    """
    name = path.name.lower()

    fk_positive = [
        "_fk.",
        "_fks.",
        "fk.sql",
        "fks.sql",
        "schema_pg_fks",
        "with_fk",
        "with_fks",
    ]
    fk_negative = [
        "no_fk",
        "nofk",
        "without_fk",
        "withoutfks",
    ]

    if any(tok in name for tok in fk_negative):
        return "no_fk"
    if any(tok in name for tok in fk_positive):
        return "fk"

    # Fallback: inspect content
    try:
        text = read_text(path).lower()
    except Exception:
        text = ""

    if "foreign key" in text or " references " in text:
        return "fk"

    return "unknown"


def find_schema_sql(scenario_dir: Path, fk_mode: str = "auto") -> Path:
    """
    Choose a SQL schema file from a scenario directory.

    fk_mode:
      - 'auto': choose the most likely default schema
      - 'fk': prefer FK-enriched schema
      - 'no_fk': prefer original / no-FK schema
    """
    candidates = sorted(scenario_dir.glob("*.sql"), key=lambda p: p.name)
    if not candidates:
        raise FileNotFoundError(f"No .sql file found in {scenario_dir}")

    classified = [(classify_sql_file(p), p) for p in candidates]
    fk_files = [p for c, p in classified if c == "fk"]
    no_fk_files = [p for c, p in classified if c == "no_fk"]
    unknown_files = [p for c, p in classified if c == "unknown"]

    def choose_best_default() -> Path:
        # Prefer schema-like names first, then FK-like names, then shorter names
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
    """
    Return list of (table_name, relative_csv_path).
    Supports:
      \\copy hotel FROM '...'
      \\copy hotel(id, name) FROM '...'
    """
    return COPY_RE.findall(schema_sql_text)


def resolve_csv_path(scenario_dir: Path, rel_csv_path: str) -> Optional[Path]:
    """
    Burr repo often stores paths in SQL as train_data/...,
    but the actual CSV files may be directly inside scenario_dir.
    So we try:
      1) scenario_dir / rel_csv_path
      2) scenario_dir / basename(rel_csv_path)
    """
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

def clean_schema_sql_for_prompt(schema_sql_text: str) -> str:
    """
    Keep only schema-relevant SQL for prompting:
    - CREATE TABLE
    - CREATE INDEX
    - ALTER TABLE ... FOREIGN KEY / constraints

    Drop:
    - INSERT INTO ...
    - database setup commands like \\c, \\set
    - DROP/CREATE DATABASE
    - other non-structural statements
    """
    text = schema_sql_text or ""
    lines = text.splitlines()

    kept_blocks: List[str] = []
    current_block: List[str] = []

    def flush_block():
        nonlocal current_block
        if current_block:
            block = "\n".join(current_block).strip()
            if block:
                kept_blocks.append(block)
            current_block = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        low = stripped.lower()

        # Skip blank lines, but preserve block boundaries
        if not stripped:
            flush_block()
            continue

        # Drop psql/meta commands and DB-level setup
        if stripped.startswith("\\"):
            flush_block()
            continue
        if low.startswith("drop database"):
            flush_block()
            continue
        if low.startswith("create database"):
            flush_block()
            continue
        if low.startswith("select pg_terminate_backend"):
            flush_block()
            continue
        if low.startswith("set "):
            flush_block()
            continue

        # Drop insert statements entirely
        if low.startswith("insert into "):
            flush_block()
            continue

        # Keep structural SQL and comments near it
        if (
            low.startswith("create table ")
            or low.startswith("create index ")
            or low.startswith("alter table ")
            or low.startswith("--")
        ):
            current_block.append(line)
        else:
            # Ignore all other statements for prompt compactness
            flush_block()

    flush_block()

    # Final cleanup: remove repeated blank lines
    compact = "\n\n".join(block for block in kept_blocks if block.strip())
    compact = re.sub(r"\n{3,}", "\n\n", compact).strip()
    return compact
def extract_table_definitions(schema_sql_text: str) -> Dict[str, str]:
    """
    Extract compact CREATE TABLE definitions only.

    Returns:
      table_name -> compact definition string including:
        - column definitions
        - PRIMARY KEY lines
        - inline FOREIGN KEY lines if present

    It will NOT include:
      - INSERT INTO ...
      - CREATE INDEX ...
      - ALTER TABLE ...
      - database setup commands
    """
    out: Dict[str, str] = {}

    if not schema_sql_text:
        return out

    matches = CREATE_TABLE_RE.findall(schema_sql_text)
    for table_name, body in matches:
        # Normalize whitespace a bit, but keep line structure readable
        lines = [ln.rstrip() for ln in body.splitlines()]
        lines = [ln for ln in lines if ln.strip()]

        definition = "\n".join(lines).strip()
        out[table_name] = definition

    return out
def compact_table_definitions(
    table_defs: Dict[str, str],
    max_tables: int = 30,
    max_chars_per_table: int = 1200,
) -> Dict[str, str]:
    """
    Keep table definitions compact for prompting.
    """
    items = sorted(table_defs.items(), key=lambda kv: kv[0])
    items = items[:max_tables]

    compact: Dict[str, str] = {}
    for table_name, definition in items:
        text = definition.strip()
        if len(text) > max_chars_per_table:
            text = text[:max_chars_per_table].rstrip() + "\n... [truncated]"
        compact[table_name] = text

    return compact


# ============================================================
# Ground-truth mapping discovery / copy
# ============================================================

def is_micro_benchmark_scenario(scenario_dir: Path) -> bool:
    parts = {p.lower() for p in scenario_dir.parts}
    return "micro_benchmark" in parts


def find_ground_truth_mapping_file(scenario_dir: Path) -> Optional[Path]:
    candidate = scenario_dir / "mapping.json"
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def find_optional_ground_truth_artifacts(scenario_dir: Path) -> List[Path]:
    names = [
        "mapping.ttl",
        "test_mapping.ttl",
    ]
    out: List[Path] = []
    for name in names:
        p = scenario_dir / name
        if p.exists() and p.is_file():
            out.append(p)
    return out


def copy_ground_truth_mapping_if_available(
    scenario_dir: Path,
    out_dir: Path,
    copy_optional_artifacts: bool = True,
) -> Tuple[Optional[Path], Optional[Path], Optional[str], List[str]]:
    """
    Copy GT mapping into out_dir if found.

    Returns:
      (src_mapping_json, dst_mapping_json, warning_message, copied_optional_artifact_paths)
    """
    copied_optional: List[str] = []

    if not is_micro_benchmark_scenario(scenario_dir):
        return None, None, (
            "Automatic GT mapping copy is currently only supported for Burr micro_benchmark "
            "scenarios, where GT is canonically stored as mapping.json."
        ), copied_optional

    src = find_ground_truth_mapping_file(scenario_dir)
    if src is None:
        return None, None, "mapping.json not found in scenario directory.", copied_optional

    dst = out_dir / "gt.mapping.json"
    shutil.copy2(src, dst)

    if copy_optional_artifacts:
        for artifact in find_optional_ground_truth_artifacts(scenario_dir):
            if artifact.name == "mapping.ttl":
                artifact_dst = out_dir / "gt.mapping.ttl"
            elif artifact.name == "test_mapping.ttl":
                artifact_dst = out_dir / "gt.test_mapping.ttl"
            else:
                artifact_dst = out_dir / artifact.name

            shutil.copy2(artifact, artifact_dst)
            copied_optional.append(str(artifact_dst))

    return src, dst, None, copied_optional


# ============================================================
# Prompt construction
# ============================================================

SYSTEM_PROMPT = """You are an ontology learning assistant for relational databases.

Your task:
Given a relational database schema and a few sample rows, construct:
1. a relational-database-derived ontology draft
2. executable mappings from database elements to ontology elements

Important:
- Do NOT merely copy table names to classes blindly.
- Consider weak entities, connector tables, N-to-M tables, boolean hidden concepts, hierarchies, and denormalized structures.
- Focus on structure and mappings, not just naming.
- Output ONLY valid JSON.
- The JSON must conform to the OntologyDraft structure described by the user.
"""

USER_PROMPT_TEMPLATE = """You are given a relational database scenario.

## Scenario path
{scenario_path}

## Schema SQL
{schema_sql}

## Parsed table definitions
{table_defs_json}

## Sample rows
{sample_rows_json}

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

### Expected semantics
- classes: ontology classes
- data_properties: object -> literal properties
- object_properties: object -> object relationships
- subclass_relations: hierarchy edges
- class_mappings: how class instances are constructed from database rows
- data_property_mappings: how data properties map to columns
- object_property_mappings: how object properties map using joins
- diagnostics: may contain empty lists if uncertain

### Important constraints
- Every accepted class should have a class mapping.
- Every accepted data property should have a data_property_mapping.
- Every accepted object property should have an object_property_mapping.
- object_properties must include join_paths.
- class_mappings must include:
  - class_id
  - instance_id_template
  - from_tables
  - identifier_columns
- Use IDs like:
  - Class:Hotel
  - DataProperty:Room.bed_number
  - ObjectProperty:Hotel.rooms
- Use status="accepted" for the main output.
- confidence can be a float in [0,1].

### Notes
- If a table is just a connector table, prefer representing it as an object property unless it clearly needs reification.
- If a table is a weak entity, ensure the identifier captures the dependency (e.g. composite key).
- If there is evidence for hierarchy, include subclass_relations and explain evidence briefly.

Return JSON only.
"""


def build_prompt(
    scenario_path: Path,
    schema_sql_text: str,
    table_defs: Dict[str, str],
    sample_rows: Dict[str, List[Dict[str, Any]]],
) -> str:
    cleaned_schema_sql = clean_schema_sql_for_prompt(schema_sql_text)
    compact_defs = compact_table_definitions(table_defs)

    # Keep sample rows compact as well
    compact_sample_rows: Dict[str, List[Dict[str, Any]]] = {}
    for table_name, rows in sorted(sample_rows.items()):
        compact_sample_rows[table_name] = rows[:3]

    prompt = f"""You are given a relational database scenario.

## Scenario path
{scenario_path}

## Compact schema SQL
{cleaned_schema_sql}

## Parsed table definitions
{json.dumps(compact_defs, indent=2, ensure_ascii=False)}

## Sample rows
{json.dumps(compact_sample_rows, indent=2, ensure_ascii=False)}

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

### Expected semantics
- classes: ontology classes
- data_properties: object -> literal properties
- object_properties: object -> object relationships
- subclass_relations: hierarchy edges
- class_mappings: how class instances are constructed from database rows
- data_property_mappings: how data properties map to columns
- object_property_mappings: how object properties map using joins
- diagnostics: may contain empty lists if uncertain

### Important constraints
- Every accepted class should have a class mapping.
- Every accepted data property should have a data_property_mapping.
- Every accepted object property should have an object_property_mapping.
- object_properties must include join_paths.
- class_mappings must include:
  - class_id
  - instance_id_template
  - from_tables
  - identifier_columns
- Use IDs like:
  - Class:Hotel
  - DataProperty:Room.bed_number
  - ObjectProperty:Hotel.rooms
- Use status="accepted" for the main output.
- confidence can be a float in [0,1].

### Modeling guidance
- Prefer ontology structures that are strongly supported by schema and samples.
- If a table is just a connector table, prefer representing it as an object property unless it clearly needs reification.
- If a table is a weak entity, ensure the identifier captures the dependency (e.g. composite key).
- If there is evidence for hierarchy, include subclass_relations and explain evidence briefly.
- Do not invent unnecessary inverse object properties unless strongly justified.
- Be conservative when evidence is weak.

Return JSON only.
"""
    return prompt


# ============================================================
# OpenAI-compatible chat.completions call
# ============================================================

def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return api_key


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Try to extract a JSON object from raw model text.
    Handles fenced code blocks and extra commentary.
    """
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


import time
import httpx


def call_llm_json(
    prompt: str,
    model: str = "gpt-5.4-mini",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    timeout: float = 120.0,
    max_retries: int = 3,
    retry_backoff_base: float = 2.0,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns:
      model_json, llm_meta
    """
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

    for attempt in range(1, max_retries + 1):
        attempt_meta: Dict[str, Any] = {
            "attempt": attempt,
            "status": "started",
        }

        try:
            with httpx.Client(trust_env=False, http2=False, timeout=timeout_cfg) as client:
                r = client.post(api_url, headers=headers, json=payload)

            attempt_meta["status_code"] = r.status_code
            attempt_meta["response_headers"] = dict(r.headers)

            if r.status_code != 200:
                attempt_meta["status"] = "http_error"
                attempt_meta["response_text_preview"] = r.text[:5000]
                llm_meta["attempts"].append(attempt_meta)

                # 5xx / 429 usually worth retrying
                if r.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                    sleep_s = retry_backoff_base ** (attempt - 1)
                    attempt_meta["sleep_before_retry_sec"] = sleep_s
                    time.sleep(sleep_s)
                    continue

                raise RuntimeError(
                    f"LLM request failed with status {r.status_code}\nResponse: {r.text}"
                )

            try:
                data = r.json()
            except Exception as e:
                attempt_meta["status"] = "bad_json_response"
                attempt_meta["response_text_preview"] = r.text[:5000]
                llm_meta["attempts"].append(attempt_meta)
                raise RuntimeError(f"Response is not valid JSON: {r.text}") from e

            attempt_meta["response_json_preview"] = json.dumps(data, ensure_ascii=False)[:5000]

            try:
                text = data["choices"][0]["message"]["content"]
            except Exception as e:
                attempt_meta["status"] = "bad_response_shape"
                llm_meta["attempts"].append(attempt_meta)
                raise RuntimeError(
                    f"Could not extract choices[0].message.content from response: "
                    f"{json.dumps(data, ensure_ascii=False)[:2000]}"
                ) from e

            attempt_meta["raw_content_preview"] = str(text)[:5000]

            model_json = extract_json_object(text)

            attempt_meta["status"] = "ok"
            llm_meta["attempts"].append(attempt_meta)
            llm_meta["status_code"] = r.status_code
            llm_meta["response_headers"] = dict(r.headers)
            llm_meta["raw_content_preview"] = str(text)[:5000]

            return model_json, llm_meta

        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            last_exc = e
            attempt_meta["status"] = "timeout"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                sleep_s = retry_backoff_base ** (attempt - 1)
                attempt_meta["sleep_before_retry_sec"] = sleep_s
                time.sleep(sleep_s)
                continue

        except httpx.HTTPError as e:
            last_exc = e
            attempt_meta["status"] = "httpx_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                sleep_s = retry_backoff_base ** (attempt - 1)
                attempt_meta["sleep_before_retry_sec"] = sleep_s
                time.sleep(sleep_s)
                continue

        except Exception as e:
            last_exc = e
            attempt_meta["status"] = "other_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            llm_meta["attempts"].append(attempt_meta)
            raise

    raise RuntimeError(
        f"LLM request failed after {max_retries} attempts. "
        f"Last error: {type(last_exc).__name__}: {last_exc}"
    ) from last_exc


# ============================================================
# Utilities
# ============================================================

def summarize_top_level_counts(obj: Dict[str, Any]) -> Dict[str, Any]:
    obj = dict(obj or {})
    return {
        "num_classes": len(obj.get("classes", []) or []),
        "num_data_properties": len(obj.get("data_properties", []) or []),
        "num_object_properties": len(obj.get("object_properties", []) or []),
        "num_subclass_relations": len(obj.get("subclass_relations", []) or []),
        "num_class_mappings": len(obj.get("class_mappings", []) or []),
        "num_data_property_mappings": len(obj.get("data_property_mappings", []) or []),
        "num_object_property_mappings": len(obj.get("object_property_mappings", []) or []),
    }


def extract_normalization_summary(draft: OntologyDraft) -> Dict[str, Any]:
    report = (draft.extras or {}).get("normalization_report", {}) or {}
    messages = report.get("messages", []) or []

    by_level: Dict[str, int] = {}
    by_code: Dict[str, int] = {}
    for m in messages:
        level = str((m or {}).get("level", "info"))
        code = str((m or {}).get("code", "UNKNOWN"))
        by_level[level] = by_level.get(level, 0) + 1
        by_code[code] = by_code.get(code, 0) + 1

    return {
        "ok": report.get("ok", True),
        "num_messages": len(messages),
        "by_level": by_level,
        "by_code": by_code,
        "stats": report.get("stats", {}) or {},
    }


def safe_exception_payload(e: Exception) -> Dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
    }


# ============================================================
# Main baseline routine
# ============================================================

def run_one_shot_baseline(
    scenario_dir: Path,
    model: str = "gpt-5.4-nano",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    max_rows_per_table: int = 5,
    timeout: float = 120.0,
    schema_path: Optional[Path] = None,
) -> Tuple[OntologyDraft, Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], str]:
    """
    Returns:
      draft,
      burr_mapping,
      meta,
      raw_model_json,
      normalized_model_json,
      prompt
    """
    if schema_path is None:
        schema_path = find_schema_sql(scenario_dir)
    else:
        schema_path = schema_path.resolve()

    schema_sql_text = read_text(schema_path)

    table_defs = extract_table_definitions(schema_sql_text)
    sample_rows = load_sample_rows_from_csv(
        scenario_dir=scenario_dir,
        schema_sql_text=schema_sql_text,
        max_rows_per_table=max_rows_per_table,
    )

    prompt = build_prompt(
        scenario_path=scenario_dir,
        schema_sql_text=schema_sql_text,
        table_defs=table_defs,
        sample_rows=sample_rows,
    )

    raw_model_json, llm_meta = call_llm_json(
        prompt=prompt,
        model=model,
        api_url=api_url,
        timeout=timeout,
    )

    normalized_model_json = normalize_model_output_robust(raw_model_json)

    try:
        draft = OntologyDraft.from_dict(normalized_model_json, already_normalized=True)
    except Exception as e:
        meta = {
            "scenario_dir": str(scenario_dir),
            "schema_path": str(schema_path),
            "num_tables": len(table_defs),
            "sampled_tables": sorted(sample_rows.keys()),
            "prompt_chars": len(prompt),
            "model": model,
            "api_url": api_url,
            "stage": "draft_construction_failed",
            "raw_model_top_level_counts": summarize_top_level_counts(raw_model_json),
            "normalized_top_level_counts": summarize_top_level_counts(normalized_model_json),
            "llm_meta": llm_meta,
            "draft_error": safe_exception_payload(e),
        }
        raise RuntimeError(
            "Failed during OntologyDraft construction.\n"
            f"{json.dumps(meta, ensure_ascii=False, indent=2)[:12000]}"
        ) from e

    verifier = MappingVerifier(draft)
    report = verifier.verify()

    burr_mapping = draft.to_burr_mapping()

    validate_ok, validate_errors = draft.validate()
    normalization_summary = extract_normalization_summary(draft)

    meta = {
        "scenario_dir": str(scenario_dir),
        "schema_path": str(schema_path),
        "num_tables": len(table_defs),
        "sampled_tables": sorted(sample_rows.keys()),
        "prompt_chars": len(prompt),
        "model": model,
        "api_url": api_url,

        "raw_model_top_level_counts": summarize_top_level_counts(raw_model_json),
        "normalized_top_level_counts": summarize_top_level_counts(normalized_model_json),
        "draft_top_level_counts": {
            "num_classes": len(draft.classes),
            "num_data_properties": len(draft.data_properties),
            "num_object_properties": len(draft.object_properties),
            "num_subclass_relations": len(draft.subclass_relations),
            "num_class_mappings": len(draft.class_mappings),
            "num_data_property_mappings": len(draft.data_property_mappings),
            "num_object_property_mappings": len(draft.object_property_mappings),
        },

        "llm_meta": llm_meta,
        "normalization_summary": normalization_summary,
        "normalization_report": (draft.extras or {}).get("normalization_report", {}) or {},

        "draft_validation": {
            "ok": validate_ok,
            "num_errors": len(validate_errors),
            "errors": validate_errors,
        },

        "verification_summary": report.summary(),
        "verification_errors": [
            {
                "level": x.level,
                "code": x.code,
                "message": x.message,
                "context": x.context,
            }
            for x in report.errors
        ],
        "verification_warnings": [
            {
                "level": x.level,
                "code": x.code,
                "message": x.message,
                "context": x.context,
            }
            for x in report.warnings
        ],
    }

    return draft, burr_mapping, meta, raw_model_json, normalized_model_json, prompt


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="One-shot ontology learning baseline with debug outputs, optional schema override, and optional Burr compare."
    )
    parser.add_argument(
        "--scenario-dir",
        type=str,
        default="../burr/micro_benchmark/attributes/weak_entity/hotel",
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default=None,
        help="Optional explicit SQL schema path. If set, overrides automatic schema discovery.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5.4-nano",
        help="Model name for your OpenAI-compatible provider",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="https://www.aiapikey.net/v1/chat/completions",
        help="OpenAI-compatible chat.completions endpoint",
    )
    parser.add_argument(
        "--max-rows-per-table",
        type=int,
        default=5,
        help="Number of sample rows to include per table",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/one_shot",
        help="Directory to write outputs",
    )

    parser.add_argument(
        "--run-burr-compare",
        action="store_true",
        help="If set, run Burr comparison and save compare.json / compare_error.json.",
    )
    parser.add_argument(
        "--burr-root",
        type=str,
        default=None,
        help="Path to local Burr repository root, used when --run-burr-compare is enabled.",
    )
    parser.add_argument(
        "--meta-path",
        type=str,
        default=None,
        help="Optional explicit meta.json path for Burr comparison.",
    )
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
        help="Optional database name override for Burr comparison.",
    )

    # Debug-friendly booleans: default True
    parser.add_argument("--dump-prompt", dest="dump_prompt", action="store_true")
    parser.add_argument("--save-raw-model-json", dest="save_raw_model_json", action="store_true")
    parser.add_argument("--save-normalized-json", dest="save_normalized_json", action="store_true")
    parser.add_argument("--copy-gt-mapping", dest="copy_gt_mapping", action="store_true")
    parser.add_argument(
    "--fk-mode",
    type=str,
    default="auto",
    choices=["auto", "fk", "no_fk"],
    help="How to choose schema SQL when --schema-path is not explicitly provided.",
)

    parser.set_defaults(
        dump_prompt=True,
        save_raw_model_json=True,
        save_normalized_json=True,
        copy_gt_mapping=True,
    )

    args = parser.parse_args()

    scenario_dir = Path(args.scenario_dir).resolve()
    schema_path = Path(args.schema_path).resolve() if args.schema_path else None
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    effective_schema_path = (
    schema_path if schema_path is not None
    else find_schema_sql(scenario_dir, fk_mode=args.fk_mode)
)

    try:
        (
            draft,
            burr_mapping,
            meta,
            raw_model_json,
            normalized_model_json,
            prompt,
        ) = run_one_shot_baseline(
            scenario_dir=scenario_dir,
            model=args.model,
            api_url=args.api_url,
            max_rows_per_table=args.max_rows_per_table,
            timeout=args.timeout,
            schema_path=effective_schema_path,
        )
    except Exception as e:
        fail_meta = {
            "scenario_dir": str(scenario_dir),
            "schema_path": str(effective_schema_path),
            "model": args.model,
            "api_url": args.api_url,
            "error": safe_exception_payload(e),
        }
        fail_meta_path = out_dir / "failed.meta.json"
        write_json(fail_meta_path, fail_meta)
        raise

    draft_path = out_dir / "draft.json"
    burr_mapping_path = out_dir / "mapping.json"
    meta_path = out_dir / "meta.json"

    draft_path.write_text(draft.to_json(indent=2), encoding="utf-8")
    write_json(burr_mapping_path, burr_mapping)
    write_json(meta_path, meta)

    if args.save_raw_model_json:
        raw_model_json_path = out_dir / "raw_model.json"
        write_json(raw_model_json_path, raw_model_json)

    if args.save_normalized_json:
        normalized_json_path = out_dir / "normalized.json"
        write_json(normalized_json_path, normalized_model_json)

    if args.dump_prompt:
        prompt_path = out_dir / "prompt.md"
        write_text(prompt_path, prompt)

    gt_src_path = None
    gt_dst_path = None
    gt_warning = None
    gt_optional_paths: List[str] = []

    if args.copy_gt_mapping:
        gt_src_path, gt_dst_path, gt_warning, gt_optional_paths = copy_ground_truth_mapping_if_available(
            scenario_dir=scenario_dir,
            out_dir=out_dir,
            copy_optional_artifacts=True,
        )

        meta["gt_mapping"] = {
            "copied": gt_dst_path is not None,
            "source_path": str(gt_src_path) if gt_src_path else None,
            "copied_path": str(gt_dst_path) if gt_dst_path else None,
            "optional_artifacts_copied": gt_optional_paths,
            "warning": gt_warning,
        }
        write_json(meta_path, meta)

    if args.run_burr_compare:
        compare_json_path = out_dir / "compare.json"
        compare_error_path = out_dir / "compare_error.json"
        try:
            compare_result = run_compare(
                scenario_dir=scenario_dir,
                pred_mapping_path=burr_mapping_path,
                gt_mapping_path=None,
                meta_path=Path(args.meta_path).resolve() if args.meta_path else None,
                burr_root=Path(args.burr_root).resolve() if args.burr_root else None,
                database_name=args.database_name or scenario_dir.name,
            )
            write_json(compare_json_path, compare_result)
        except Exception as e:
            write_json(compare_error_path, safe_exception_payload(e))

    print(f"[OK] scenario: {scenario_dir}")
    print(f"[OK] schema: {effective_schema_path}")
    print(f"[OK] draft: {draft_path}")
    print(f"[OK] mapping: {burr_mapping_path}")
    print(f"[OK] meta: {meta_path}")

    if args.save_raw_model_json:
        print(f"[OK] raw model json: {out_dir / 'raw_model.json'}")

    if args.save_normalized_json:
        print(f"[OK] normalized json: {out_dir / 'normalized.json'}")

    if args.dump_prompt:
        print(f"[OK] prompt: {out_dir / 'prompt.md'}")

    if args.run_burr_compare:
        if (out_dir / "compare.json").exists():
            print(f"[OK] compare: {out_dir / 'compare.json'}")
        elif (out_dir / "compare_error.json").exists():
            print(f"[WARN] compare failed: {out_dir / 'compare_error.json'}")

    if args.copy_gt_mapping:
        if gt_dst_path is not None:
            print(f"[OK] gt mapping copied: {gt_dst_path}")
            for p in gt_optional_paths:
                print(f"[OK] gt optional artifact copied: {p}")
        else:
            print(f"[WARN] gt mapping not copied: {gt_warning}")


if __name__ == "__main__":
    main()