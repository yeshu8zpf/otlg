from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace


# ============================================================
# Path setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Basic IO helpers
# ============================================================

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ============================================================
# Import resolution for local copied Burr evaluator
# ============================================================

def _import_local_burr_modules():
    """
    Import local evaluator modules copied into this repo.
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        import wandb  # noqa: F401
    except ModuleNotFoundError:
        class _WandbStub:
            def __getattr__(self, name):
                def _noop(*args, **kwargs):
                    return None
                return _noop
        sys.modules["wandb"] = _WandbStub()

    from burr_evaluator.mapping_parser.mapping.JsonMapping import JsonMapping
    from burr_evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
    from burr_evaluator.metrics.caclulate_metrics import calculate_metrics
    return JsonMapping, D2RQMapping, calculate_metrics


# ============================================================
# Burr meta compatibility
# ============================================================

DEFAULT_BURR_META = {
    "relation_prefix": "base",
    "prefixes": [
        {"prefix": "base", "uri": "/base/"}
    ],
}


def ensure_burr_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Make meta compatible with Burr's upstream parser expectations.
    """
    out: Dict[str, Any] = {}

    if isinstance(meta, dict):
        out.update(meta)

    if "relation_prefix" not in out or not out.get("relation_prefix"):
        out["relation_prefix"] = DEFAULT_BURR_META["relation_prefix"]

    if "prefixes" not in out or not isinstance(out.get("prefixes"), list) or not out["prefixes"]:
        out["prefixes"] = list(DEFAULT_BURR_META["prefixes"])

    prefix_names = {
        p.get("prefix")
        for p in out["prefixes"]
        if isinstance(p, dict) and isinstance(p.get("prefix"), str)
    }
    if out["relation_prefix"] not in prefix_names:
        out["prefixes"].append({
            "prefix": out["relation_prefix"],
            "uri": f"/{out['relation_prefix']}/",
        })

    return out


# ============================================================
# GT resolution
# ============================================================

def find_ttl_candidates(scenario_dir: Path) -> List[Path]:
    preferred_names = [
        "groundtruth.ttl",
        "map_d2rq.ttl",
        "mapping.ttl",
        "test_mapping.ttl",
    ]
    found: List[Path] = []
    for name in preferred_names:
        p = scenario_dir / name
        if p.exists() and p.is_file():
            found.append(p)
    for p in sorted(scenario_dir.glob("*.ttl"), key=lambda x: x.name):
        if p not in found:
            found.append(p)
    return found


def resolve_gt_for_scenario(scenario_dir: Path) -> Dict[str, Any]:
    scenario_dir = scenario_dir.resolve()
    mapping_json = scenario_dir / "mapping.json"
    mappings_dir = scenario_dir / "mappings"
    meta_json = scenario_dir / "meta.json"

    result: Dict[str, Any] = {
        "kind": "missing",
        "mapping_json": None,
        "mapping_ttl": None,
        "mappings_dir": None,
        "meta_json": meta_json if meta_json.exists() and meta_json.is_file() else None,
        "json_files": [],
        "ttl_candidates": [],
    }

    if mapping_json.exists() and mapping_json.is_file():
        result["kind"] = "single_json"
        result["mapping_json"] = mapping_json
        result["json_files"] = [mapping_json]
        return result

    ttl_candidates = find_ttl_candidates(scenario_dir)
    result["ttl_candidates"] = ttl_candidates
    if ttl_candidates:
        result["kind"] = "single_ttl"
        result["mapping_ttl"] = ttl_candidates[0]
        return result

    if mappings_dir.exists() and mappings_dir.is_dir():
        json_files = sorted(
            [
                p for p in mappings_dir.glob("*.json")
                if p.is_file() and p.name.lower() != "meta.json"
            ],
            key=lambda p: p.name,
        )
        result["kind"] = "mapping_dir"
        result["mappings_dir"] = mappings_dir
        result["json_files"] = json_files
        nested_meta = mappings_dir / "meta.json"
        if nested_meta.exists() and nested_meta.is_file():
            result["meta_json"] = nested_meta
        return result

    return result


def merge_mapping_json_files(json_files: List[Path]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for path in json_files:
        data = read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"GT mapping JSON must be an object: {path}")
        for key, value in data.items():
            if key not in merged:
                if isinstance(value, list):
                    merged[key] = list(value)
                elif isinstance(value, dict):
                    merged[key] = dict(value)
                else:
                    merged[key] = value
                continue

            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key].extend(value)
            elif isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
    return merged


def default_meta_path_for_scenario(
    scenario_dir: Path,
    gt_info: Optional[Dict[str, Any]] = None,
) -> Optional[Path]:
    if gt_info is None:
        gt_info = resolve_gt_for_scenario(scenario_dir)

    meta_path = gt_info.get("meta_json")
    if isinstance(meta_path, Path) and meta_path.exists():
        return meta_path

    candidate = scenario_dir / "meta.json"
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def infer_database_name(
    scenario_dir: Path,
    explicit_database_name: Optional[str],
) -> str:
    if explicit_database_name:
        return explicit_database_name
    return scenario_dir.name


# ============================================================
# Canonicalization helpers
# ============================================================

PLACEHOLDER_RE = re.compile(r"\{\s*([^{}]+?)\s*\}")
ATAT_RE = re.compile(r"@@\s*([^.@/\s]+)\s*\.\s*([^.@/\s]+)\s*@@", re.IGNORECASE)
URI_PATTERN_KEYS = {
    "uriPattern",
    "uri_pattern",
    "uriTemplate",
    "uri_template",
    "sql_uri_pattern",
    "pattern",
}
SQL_EXPR_KEYS = {
    "sql_condition",
    "sql_join",
    "sql_column",
    "sql_columns",
    "sql_sql_expression",
    "sqlExpression",
    "sql_expression",
    "column",
    "columns",
    "condition",
    "join",
    "joinCondition",
    "join_condition",
}


def norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


def split_table_column(expr: str) -> Optional[Tuple[str, str]]:
    expr = str(expr).strip().strip('"').strip("'").strip()
    if "." not in expr:
        return None
    left, right = expr.split(".", 1)
    return left.strip().lower(), right.strip().lower()


def parse_join_equality(join_expr: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    if not isinstance(join_expr, str) or "=" not in join_expr:
        return None
    left, right = join_expr.split("=", 1)
    left_tc = split_table_column(left)
    right_tc = split_table_column(right)
    if left_tc is None or right_tc is None:
        return None
    return left_tc, right_tc


def normalize_column_expr(expr: str) -> str:
    tc = split_table_column(expr)
    if tc is None:
        return re.sub(r"\s+", " ", str(expr).strip()).lower()
    t, c = tc
    return f"{t}.{c}"


def normalize_join_expr(expr: str) -> str:
    parsed = parse_join_equality(expr)
    if parsed is None:
        return re.sub(r"\s+", " ", str(expr).strip()).lower()
    (lt, lc), (rt, rc) = parsed
    return f"{lt}.{lc} = {rt}.{rc}"


def canonical_uri_pattern_from_columns(cols: List[Tuple[str, str]]) -> str:
    return "/".join(f"@@{t}.{c}@@" for t, c in cols)


def parse_existing_uri_pattern(pattern: str) -> Optional[List[Tuple[str, str]]]:
    matches = ATAT_RE.findall(pattern or "")
    if not matches:
        return None
    return [(t.lower(), c.lower()) for t, c in matches]


def extract_placeholders_from_template(template: str) -> List[str]:
    return [m.group(1).strip() for m in PLACEHOLDER_RE.finditer(template or "")]


def normalize_placeholder_token(token: str, table_hint: Optional[str] = None) -> str:
    token = str(token).strip()
    token = token.strip("@{} ")
    token = token.replace("`", "").replace('"', "").replace("'", "")
    token = re.sub(r"\s+", "", token)

    if "." in token:
        left, right = token.split(".", 1)
        return f"@@{left.lower()}.{right.lower()}@@"

    if table_hint:
        return f"@@{table_hint.lower()}.{token.lower()}@@"

    return f"@@{token.lower()}@@"


def normalize_uri_pattern(value: str, table_hint: Optional[str] = None) -> str:
    s = str(value).strip()

    def repl_at(m: re.Match[str]) -> str:
        table = m.group(1)
        col = m.group(2)
        return f"@@{table.lower()}.{col.lower()}@@"

    s = re.sub(r"@@\s*([^.@/\s]+)\s*\.\s*([^.@/\s]+)\s*@@", repl_at, s, flags=re.IGNORECASE)

    def repl_brace(m: re.Match[str]) -> str:
        body = m.group(1)
        return normalize_placeholder_token(body, table_hint=table_hint)

    s = re.sub(r"\{\s*([^{}]+?)\s*\}", repl_brace, s)

    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("/@@"):
        s = s[1:]
    return s.lower()


def normalize_sqlish_text(value: str, table_hint: Optional[str] = None) -> str:
    s = str(value)
    s = normalize_uri_pattern(s, table_hint=table_hint)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r'"([^"]+)"', r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


# ============================================================
# Mapping structure indexing
# ============================================================

def collect_class_entries(mapping: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result = {}
    for cls in mapping.get("classes", []):
        cls_name = cls.get("class") or cls.get("name")
        if isinstance(cls_name, str):
            result[cls_name] = cls
    return result


def collect_data_props_by_class(mapping: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in mapping.get("data_properties", []):
        cls = p.get("belongsToClassMap") or p.get("belongsToClass")
        if isinstance(cls, str):
            out[cls].append(p)
    return out


def collect_object_props_by_class(mapping: Dict[str, Any]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
    outgoing: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    incoming: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in mapping.get("object_properties", []):
        b = p.get("belongsToClassMap") or p.get("belongsToClass")
        r = p.get("refersToClassMap") or p.get("refersToClass")
        if isinstance(b, str):
            outgoing[b].append(p)
        if isinstance(r, str):
            incoming[r].append(p)
    return outgoing, incoming


def infer_base_tables_for_class(
    cls_name: str,
    data_props_by_class: Dict[str, List[Dict[str, Any]]],
    outgoing_obj_props: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    counter: Counter[str] = Counter()

    for dp in data_props_by_class.get(cls_name, []):
        col = dp.get("column")
        if isinstance(col, str):
            tc = split_table_column(col)
            if tc:
                counter[tc[0]] += 1

    if not counter:
        for op in outgoing_obj_props.get(cls_name, []):
            joins = op.get("join", [])
            if not isinstance(joins, list):
                joins = [joins] if joins else []
            for j in joins:
                if not isinstance(j, str):
                    continue
                parsed = parse_join_equality(j)
                if parsed is None:
                    continue
                (lt, _), (rt, _) = parsed
                counter[lt] += 1
                counter[rt] += 1

    return [table for table, _ in counter.most_common()]


def pick_column_by_name_match(
    placeholder: str,
    candidate_columns: List[Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    ph = norm_name(placeholder)

    exact = [tc for tc in candidate_columns if norm_name(tc[1]) == ph]
    if exact:
        return exact[0]

    fuzzy = [
        tc for tc in candidate_columns
        if ph in norm_name(tc[1]) or norm_name(tc[1]) in ph
    ]
    if fuzzy:
        return fuzzy[0]

    return None


def infer_columns_from_data_props(
    cls_name: str,
    placeholders: List[str],
    data_props_by_class: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []
    for dp in data_props_by_class.get(cls_name, []):
        col = dp.get("column")
        if isinstance(col, str):
            tc = split_table_column(col)
            if tc:
                candidates.append(tc)

    out: Dict[str, Tuple[str, str]] = {}
    for ph in placeholders:
        chosen = pick_column_by_name_match(ph, candidates)
        if chosen is not None:
            out[ph] = chosen
    return out


def infer_columns_from_outgoing_object_props(
    cls_name: str,
    placeholders: List[str],
    base_tables: List[str],
    outgoing_obj_props: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Tuple[str, str]]:
    result: Dict[str, Tuple[str, str]] = {}

    for op in outgoing_obj_props.get(cls_name, []):
        target_cls = op.get("refersToClassMap") or op.get("refersToClass")
        joins = op.get("join", [])
        if not isinstance(joins, list):
            joins = [joins] if joins else []

        for j in joins:
            parsed = parse_join_equality(j)
            if parsed is None:
                continue
            left, right = parsed

            local_side = None
            if left[0] in base_tables and right[0] not in base_tables:
                local_side = left
            elif right[0] in base_tables and left[0] not in base_tables:
                local_side = right
            elif left[0] in base_tables:
                local_side = left
            elif right[0] in base_tables:
                local_side = right

            if local_side is None:
                continue

            for ph in placeholders:
                if ph in result:
                    continue
                if norm_name(ph) == norm_name(local_side[1]):
                    result[ph] = local_side

            if isinstance(target_cls, str):
                for ph in placeholders:
                    if ph in result:
                        continue
                    if norm_name(ph) == norm_name(target_cls):
                        result[ph] = local_side

    return result


def infer_columns_by_template_prefix(
    template: str,
    placeholders: List[str],
    base_tables: List[str],
) -> Dict[str, Tuple[str, str]]:
    result: Dict[str, Tuple[str, str]] = {}
    prefix = str(template).split("{", 1)[0].strip("/ ").strip().lower()
    prefix_norm = norm_name(prefix)

    preferred_table = None
    for t in base_tables:
        if norm_name(t) in prefix_norm or prefix_norm in norm_name(t):
            preferred_table = t
            break
    if preferred_table is None and base_tables:
        preferred_table = base_tables[0]

    if preferred_table is None:
        return result

    for ph in placeholders:
        result[ph] = (preferred_table, ph.lower())

    return result


def infer_class_canonical_columns(
    cls_entry: Dict[str, Any],
    mapping: Dict[str, Any],
    data_props_by_class: Dict[str, List[Dict[str, Any]]],
    outgoing_obj_props: Dict[str, List[Dict[str, Any]]],
) -> Optional[List[Tuple[str, str]]]:
    raw_id = cls_entry.get("id")
    cls_name = cls_entry.get("class") or cls_entry.get("name")
    if not isinstance(raw_id, str) or not isinstance(cls_name, str):
        return None

    existing = parse_existing_uri_pattern(raw_id)
    if existing:
        return existing

    placeholders = extract_placeholders_from_template(raw_id)
    if not placeholders:
        return None

    base_tables = infer_base_tables_for_class(cls_name, data_props_by_class, outgoing_obj_props)
    resolved: Dict[str, Tuple[str, str]] = {}

    resolved.update(
        infer_columns_from_data_props(cls_name, placeholders, data_props_by_class)
    )

    from_obj = infer_columns_from_outgoing_object_props(
        cls_name, placeholders, base_tables, outgoing_obj_props
    )
    for ph, tc in from_obj.items():
        resolved.setdefault(ph, tc)

    from_prefix = infer_columns_by_template_prefix(raw_id, placeholders, base_tables)
    for ph, tc in from_prefix.items():
        resolved.setdefault(ph, tc)

    if any(ph not in resolved for ph in placeholders):
        return None

    return [resolved[ph] for ph in placeholders]


# ============================================================
# Mapping canonicalization
# ============================================================

def canonicalize_json_mapping(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalize both GT and prediction JSON mappings into a unified,
    Burr-friendly representation before compare.
    """
    out = copy.deepcopy(mapping)

    data_props_by_class = collect_data_props_by_class(out)
    outgoing_obj_props, _ = collect_object_props_by_class(out)

    unresolved: List[Dict[str, Any]] = []

    # Canonicalize class IDs into @@table.column@@/... form
    for cls in out.get("classes", []):
        cols = infer_class_canonical_columns(
            cls,
            out,
            data_props_by_class,
            outgoing_obj_props,
        )
        if cols is None:
            unresolved.append({
                "class": cls.get("class"),
                "original_id": cls.get("id"),
            })
            if isinstance(cls.get("id"), str):
                cls["id"] = normalize_uri_pattern(cls["id"])
            continue

        cls["id"] = canonical_uri_pattern_from_columns(cols).lower()

        if "prefix" in cls and isinstance(cls["prefix"], str):
            cls["prefix"] = cls["prefix"].lower()
        if "class" in cls and isinstance(cls["class"], str):
            cls["class"] = cls["class"]
        if "name" in cls and isinstance(cls["name"], str):
            cls["name"] = cls["name"]

    # Normalize object properties
    for op in out.get("object_properties", []):
        if isinstance(op.get("property"), str):
            op["property"] = op["property"]
        if isinstance(op.get("join"), list):
            op["join"] = [normalize_join_expr(j) for j in op["join"] if isinstance(j, str)]
        elif isinstance(op.get("join"), str):
            op["join"] = [normalize_join_expr(op["join"])]

    # Normalize data properties
    for dp in out.get("data_properties", []):
        if isinstance(dp.get("column"), str):
            dp["column"] = normalize_column_expr(dp["column"])

    out["_canonicalization_debug"] = {
        "unresolved_classes": unresolved,
    }
    return out


def preprocess_mapping_json_file(
    src_path: Path,
    dst_path: Path,
) -> Dict[str, Any]:
    data = read_json(src_path)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {src_path}")
    normalized = canonicalize_json_mapping(data)
    write_json(dst_path, normalized)
    return normalized


def preprocess_mapping_json_data(
    data: Dict[str, Any],
    dst_path: Path,
) -> Dict[str, Any]:
    normalized = canonicalize_json_mapping(data)
    write_json(dst_path, normalized)
    return normalized


def preprocess_mapping_ttl_file(
    src_path: Path,
    dst_path: Path,
) -> Dict[str, Any]:
    """
    Formal TTL preprocessing:
    - parse TTL with rdflib
    - rewrite ONLY d2rq:uriPattern literal values
    - preserve all other triples untouched
    - serialize back to TTL

    This avoids breaking Turtle syntax while still normalizing uriPattern
    surface forms for fair compare.
    """
    src_path = src_path.resolve()
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    D2RQ = Namespace("http://www.wiwiss.fu-berlin.de/suhl/bizer/D2RQ/0.1#")
    uri_pred = URIRef(str(D2RQ.uriPattern))

    g = Graph()
    g.parse(src_path.as_posix(), format="turtle")

    replacements: List[Dict[str, Any]] = []
    to_replace: List[Tuple[Any, Any, Literal, Literal]] = []

    for s, p, o in g.triples((None, uri_pred, None)):
        if not isinstance(o, Literal):
            continue

        original_value = str(o)
        normalized_value = normalize_uri_pattern(original_value, table_hint=None)

        if normalized_value != original_value:
            new_lit = Literal(
                normalized_value,
                lang=o.language,
                datatype=o.datatype,
            )
            to_replace.append((s, p, o, new_lit))
            replacements.append(
                {
                    "subject": str(s),
                    "predicate": str(p),
                    "old": original_value,
                    "new": normalized_value,
                }
            )

    for s, p, old_o, new_o in to_replace:
        g.remove((s, p, old_o))
        g.add((s, p, new_o))

    serialized = g.serialize(format="turtle")
    if isinstance(serialized, bytes):
        serialized = serialized.decode("utf-8")

    write_text(dst_path, serialized)

    return {
        "num_uriPattern_rewritten": len(replacements),
        "replacements": replacements,
    }


# ============================================================
# Mapping loading
# ============================================================

def load_mapping_as_d2rq_from_json_data(
    data: Dict[str, Any],
    database_name: str,
    meta: Optional[Dict[str, Any]],
):
    JsonMapping, _, _ = _import_local_burr_modules()
    return JsonMapping(data, database_name, meta).to_D2RQ_Mapping()


def load_mapping_as_d2rq(
    mapping_path: Path,
    database_name: str,
    meta: Optional[Dict[str, Any]],
):
    JsonMapping, D2RQMapping, _ = _import_local_burr_modules()

    mapping_path = mapping_path.resolve()
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping path not found: {mapping_path}")

    suffix = mapping_path.suffix.lower()
    if suffix == ".json":
        data = read_json(mapping_path)
        return JsonMapping(data, database_name, meta).to_D2RQ_Mapping()

    if suffix in {".ttl", ".turtle"}:
        return D2RQMapping(read_text(mapping_path), database_name, meta)

    raise ValueError(f"Unsupported mapping file type: {mapping_path}")


# ============================================================
# Preprocessed file preparation
# ============================================================

def prepare_preprocessed_prediction(
    prediction_mapping_path: Path,
    workdir: Path,
) -> Dict[str, Any]:
    prediction_mapping_path = prediction_mapping_path.resolve()
    dst_path = workdir / f"prediction_preprocessed{prediction_mapping_path.suffix.lower()}"

    if prediction_mapping_path.suffix.lower() == ".json":
        canonical = preprocess_mapping_json_file(prediction_mapping_path, dst_path)
        ttl_debug = None
    elif prediction_mapping_path.suffix.lower() in {".ttl", ".turtle"}:
        ttl_debug = preprocess_mapping_ttl_file(prediction_mapping_path, dst_path)
        canonical = None
    else:
        raise ValueError(f"Unsupported prediction mapping type: {prediction_mapping_path}")


    return {
        "kind": "prediction",
        "original_path": str(prediction_mapping_path),
        "preprocessed_path": str(dst_path),
        "canonicalization_debug": canonical.get("_canonicalization_debug") if isinstance(canonical, dict) else None,
    }


def prepare_preprocessed_gt(
    scenario_dir: Path,
    gt_mapping_path: Optional[Path],
    meta_path: Optional[Path],
    workdir: Path,
) -> Dict[str, Any]:
    scenario_dir = scenario_dir.resolve()

    if gt_mapping_path is not None:
        gt_mapping_path = gt_mapping_path.resolve()
        suffix = gt_mapping_path.suffix.lower()
        dst_path = workdir / f"gt_preprocessed{suffix}"

        if suffix == ".json":
            canonical = preprocess_mapping_json_file(gt_mapping_path, dst_path)
            kind = "explicit_single_json"
        elif suffix in {".ttl", ".turtle"}:
            ttl_debug = preprocess_mapping_ttl_file(gt_mapping_path, dst_path)
            canonical = None
            kind = "explicit_single_ttl"
        else:
            raise ValueError(f"Unsupported GT mapping type: {gt_mapping_path}")

        return {
            "kind": kind,
            "original_path": str(gt_mapping_path),
            "preprocessed_path": str(dst_path),
            "meta_path": str(meta_path) if meta_path else None,
            "canonicalization_debug": canonical.get("_canonicalization_debug") if isinstance(canonical, dict) else None,
            "ttl_preprocess_debug": ttl_debug if suffix in {".ttl", ".turtle"} else None,
        }

    gt_info = resolve_gt_for_scenario(scenario_dir)
    if gt_info["kind"] == "missing":
        raise FileNotFoundError(
            f"GT mapping not found for scenario: {scenario_dir}. "
            f"Expected one of mapping.json, *.ttl, or mappings/*.json"
        )

    if gt_info["kind"] == "single_json":
        src = gt_info["mapping_json"]
        dst = workdir / "gt_preprocessed.json"
        canonical = preprocess_mapping_json_file(src, dst)
        return {
            "kind": "single_json",
            "original_path": str(src),
            "preprocessed_path": str(dst),
            "meta_path": str(meta_path) if meta_path else None,
            "canonicalization_debug": canonical.get("_canonicalization_debug") if isinstance(canonical, dict) else None,
        }

    if gt_info["kind"] == "single_ttl":
        src = gt_info["mapping_ttl"]
        dst = workdir / "gt_preprocessed.ttl"
        ttl_debug = preprocess_mapping_ttl_file(src, dst)
        return {
            "kind": "single_ttl",
            "original_path": str(src),
            "preprocessed_path": str(dst),
            "ttl_candidates": [str(p) for p in gt_info.get("ttl_candidates", [])],
            "meta_path": str(meta_path) if meta_path else None,
            "canonicalization_debug": None,
            "ttl_preprocess_debug": ttl_debug,
        }

    json_files = gt_info["json_files"]
    if not json_files:
        raise FileNotFoundError(f"No GT JSON files found under mapping dir: {gt_info['mappings_dir']}")

    merged_data = merge_mapping_json_files(json_files)
    dst = workdir / "gt_preprocessed_merged.json"
    canonical = preprocess_mapping_json_data(merged_data, dst)

    return {
        "kind": "mapping_dir_merged",
        "original_component_files": [str(p) for p in json_files],
        "preprocessed_path": str(dst),
        "meta_path": str(meta_path) if meta_path else None,
        "canonicalization_debug": canonical.get("_canonicalization_debug") if isinstance(canonical, dict) else None,
    }


# ============================================================
# Compare details (analysis only, not used for scoring)
# ============================================================

# ============================================================
# Signature-aware mismatch rendering
# ============================================================
def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]

def _stringify_sql_attr(x: Any) -> str:
    table = getattr(x, "table", None)
    attr = getattr(x, "attribute", None)
    if table is not None and attr is not None:
        return f"{str(table).lower()}.{str(attr).lower()}"
    return str(x)


def _stringify_join(x: Any) -> str:
    left = getattr(x, "left", None)
    right = getattr(x, "right", None)
    if left is not None and right is not None:
        a = _stringify_sql_attr(left)
        b = _stringify_sql_attr(right)
        return " = ".join(sorted([a, b]))
    return str(x)


def _stringify_condition(x: Any) -> str:
    left = getattr(x, "left", None)
    operator = getattr(x, "operator", None)
    right = getattr(x, "right", None)

    if left is not None and operator is not None:
        left_s = _stringify_sql_attr(left)
        right_s = repr(right)
        return f"{left_s} {operator} {right_s}"
    return str(x)


def _sorted_unique_strings(values: Iterable[str]) -> List[str]:
    return sorted(set(values))


def _class_signature_dict(obj: Any) -> Dict[str, Any]:
    """
    Signature used by Burr mapping-based class compare:
      sql_uri_pattern, sql_join, sql_condition
    """
    uri_pattern = _sorted_unique_strings(
        _stringify_sql_attr(x) for x in _as_list(getattr(obj, "sql_uri_pattern", None))
    )
    joins = _sorted_unique_strings(
        _stringify_join(x) for x in _as_list(getattr(obj, "sql_join", None))
    )
    conditions = _sorted_unique_strings(
        _stringify_condition(x) for x in _as_list(getattr(obj, "sql_condition", None))
    )

    return {
        "object_type": "class",
        "uri_pattern": uri_pattern,
        "joins": joins,
        "conditions": conditions,
    }


def _relation_signature_dict(obj: Any, *, name_based: bool) -> Dict[str, Any]:
    """
    For relation/attribute we expose a readable approximation of the fields
    Burr equality depends on.
    """
    belongs = getattr(obj, "belongsToClassMap", None) or getattr(obj, "belongsToClass", None)
    refers = getattr(obj, "refersToClassMap", None) or getattr(obj, "refersToClass", None)
    prop = getattr(obj, "property", None) or getattr(obj, "property_name", None)

    joins = _sorted_unique_strings(
        _stringify_join(x) for x in _as_list(getattr(obj, "sql_join", None))
    )
    conditions = _sorted_unique_strings(
        _stringify_condition(x) for x in _as_list(getattr(obj, "sql_condition", None))
    )
    columns = _sorted_unique_strings(
        _stringify_sql_attr(x) for x in _as_list(getattr(obj, "sql_column", None))
    )
    expressions = _sorted_unique_strings(
        str(x) for x in _as_list(getattr(obj, "sql_sql_expression", None))
    )
    patterns = _sorted_unique_strings(
        _stringify_sql_attr(x) for x in _as_list(getattr(obj, "sql_pattern", None))
    )

    if name_based:
        return {
            "object_type": "relation_or_attribute",
            "property": str(prop) if prop is not None else None,
            "belongs_to": str(belongs) if belongs is not None else None,
            "refers_to": str(refers) if refers is not None else None,
        }

    return {
        "object_type": "relation_or_attribute",
        "property": str(prop) if prop is not None else None,
        "belongs_to": str(belongs) if belongs is not None else None,
        "refers_to": str(refers) if refers is not None else None,
        "joins": joins,
        "conditions": conditions,
        "columns": columns,
        "expressions": expressions,
        "patterns": patterns,
    }


def _signature_dict(obj: Any, *, object_kind: str, name_based: bool) -> Dict[str, Any]:
    if object_kind == "classes":
        if name_based:
            return {
                "object_type": "class",
                "class_uri": str(getattr(obj, "class_uri", None)),
            }
        return _class_signature_dict(obj)

    return _relation_signature_dict(obj, name_based=name_based)


def _member_dict(obj: Any) -> Dict[str, Any]:
    """
    Show original object identity in a user-readable way, rather than collapsing
    everything into str(obj).
    """
    out: Dict[str, Any] = {
        "repr": _safe_obj_repr(obj),
    }

    mapping_id = getattr(obj, "mapping_id", None)
    if mapping_id is not None:
        out["mapping_id"] = str(mapping_id)

    class_uri = getattr(obj, "class_uri", None)
    if class_uri is not None:
        out["class_uri"] = str(class_uri)

    uri_pattern = getattr(obj, "uriPattern", None)
    if uri_pattern is not None:
        out["uriPattern_raw"] = str(uri_pattern)

    belongs = getattr(obj, "belongsToClassMap", None) or getattr(obj, "belongsToClass", None)
    refers = getattr(obj, "refersToClassMap", None) or getattr(obj, "refersToClass", None)
    prop = getattr(obj, "property", None) or getattr(obj, "property_name", None)

    if prop is not None:
        out["property"] = str(prop)
    if belongs is not None:
        out["belongs_to"] = str(belongs)
    if refers is not None:
        out["refers_to"] = str(refers)

    return out


def _group_items_by_signature(
    items: List[Any],
    *,
    object_kind: str,
    name_based: bool,
) -> List[Dict[str, Any]]:
    """
    Group equal objects by the signature Burr compare is using, but keep the
    original members visible.
    """
    groups: List[Dict[str, Any]] = []
    used = [False] * len(items)

    for i, item in enumerate(items):
        if used[i]:
            continue

        bucket = [item]
        used[i] = True

        for j in range(i + 1, len(items)):
            if used[j]:
                continue
            if item == items[j]:
                bucket.append(items[j])
                used[j] = True

        groups.append({
            "count": len(bucket),
            "signature": _signature_dict(item, object_kind=object_kind, name_based=name_based),
            "members": [_member_dict(x) for x in bucket],
        })

    groups.sort(key=lambda g: (-g["count"], json.dumps(g["signature"], sort_keys=True, ensure_ascii=False)))
    return groups

def _safe_obj_repr(obj: Any) -> str:
    try:
        s = str(obj)
        if s:
            return s
    except Exception:
        pass
    try:
        return repr(obj)
    except Exception:
        return "<unrepr-able>"
    
def _normalize_join_list_for_display(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, tuple):
        return [str(x) for x in value]
    return [str(value)]


def _display_obj_brief(obj: Any) -> str:
    """
    Render a richer one-line display for mismatch lists, close to the original
    mapping entry, so fail-case analysis can directly see property / owner /
    column / join / condition / expression details.
    """
    class_uri = getattr(obj, "class_uri", None)
    uri_pattern = getattr(obj, "uriPattern", None)
    mapping_id = getattr(obj, "mapping_id", None)

    # -------- ClassMap --------
    if class_uri is not None and uri_pattern is not None:
        parts = [
            f"uriPattern={uri_pattern}",
            f"class_uri={class_uri}",
        ]
        if mapping_id is not None and str(mapping_id) != str(class_uri):
            parts.append(f"mapping_id={mapping_id}")

        raw_join = getattr(obj, "join", None)
        raw_condition = getattr(obj, "condition", None)

        join_list = _normalize_join_list_for_display(raw_join)
        condition_list = _normalize_join_list_for_display(raw_condition)

        if join_list:
            parts.append(f"join={join_list}")
        if condition_list:
            parts.append(f"condition={condition_list}")

        return "ClassMap(" + ", ".join(parts) + ")"

    # -------- Relation / Attribute --------
    prop = getattr(obj, "property", None) or getattr(obj, "property_name", None)
    belongs = getattr(obj, "belongsToClassMap", None) or getattr(obj, "belongsToClass", None)
    refers = getattr(obj, "refersToClassMap", None) or getattr(obj, "refersToClass", None)

    if prop is not None:
        parts = [f"property={prop}"]

        if belongs is not None:
            parts.append(f"belongsTo={belongs}")
        if refers is not None:
            parts.append(f"refersTo={refers}")

        raw_type = getattr(obj, "type", None)
        raw_column = getattr(obj, "column", None)
        raw_join = getattr(obj, "join", None)
        raw_condition = getattr(obj, "condition", None)
        raw_sql_expression = getattr(obj, "sqlExpression", None) or getattr(obj, "sql_expression", None)
        raw_pattern = getattr(obj, "pattern", None)
        raw_constant = getattr(obj, "constantValue", None)
        raw_dynamic_property = getattr(obj, "dynamic_property", None)

        if raw_type is not None:
            parts.append(f"type={raw_type}")
        if raw_column is not None:
            parts.append(f"column={raw_column}")
        if raw_sql_expression is not None:
            parts.append(f"sqlExpression={raw_sql_expression}")
        if raw_pattern is not None:
            parts.append(f"pattern={raw_pattern}")
        if raw_constant is not None:
            parts.append(f"constantValue={raw_constant}")
        if raw_dynamic_property is not None:
            parts.append(f"dynamic_property={raw_dynamic_property}")

        join_list = _normalize_join_list_for_display(raw_join)
        condition_list = _normalize_join_list_for_display(raw_condition)

        if join_list:
            parts.append(f"join={join_list}")
        if condition_list:
            parts.append(f"condition={condition_list}")

        if refers is not None:
            return "Relation(" + ", ".join(parts) + ")"
        return "Attribute(" + ", ".join(parts) + ")"

    return _safe_obj_repr(obj)

def _set_eq_strategy(items: Iterable[Any], *, name_based: bool) -> None:
    for x in items:
        if hasattr(x, "set_eq_strategy"):
            x.set_eq_strategy(name_based=name_based)


def _count_strings(items: List[str]) -> Dict[str, int]:
    counter = Counter(items)
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))

def _group_original_items_by_equality(
    items: List[Any],
) -> List[List[Any]]:
    """
    Group original items by current Burr equality semantics, preserving
    every original member object.
    """
    items = list(items or [])
    used = [False] * len(items)
    groups: List[List[Any]] = []

    for i, item in enumerate(items):
        if used[i]:
            continue

        bucket = [item]
        used[i] = True

        for j in range(i + 1, len(items)):
            if used[j]:
                continue
            if item == items[j]:
                bucket.append(items[j])
                used[j] = True

        groups.append(bucket)

    return groups

def _find_equal_group_index(
    target_group: List[Any],
    other_groups: List[List[Any]],
) -> Optional[int]:
    rep = target_group[0]
    for idx, g in enumerate(other_groups):
        if rep == g[0]:
            return idx
    return None



def _bag_diff(
    reference_items: List[Any],
    learned_items: List[Any],
    *,
    name_based: bool,
    object_kind: str,  # kept for call-site compatibility
) -> Dict[str, Any]:
    """
    Bag-based diff that preserves ORIGINAL members.
    This is the key fix: do not materialize missing/extra as [representative] * n.
    """
    reference_items = list(reference_items or [])
    learned_items = list(learned_items or [])

    _set_eq_strategy(reference_items, name_based=name_based)
    _set_eq_strategy(learned_items, name_based=name_based)

    ref_groups = _group_original_items_by_equality(reference_items)
    pred_groups = _group_original_items_by_equality(learned_items)

    matched_items: List[Any] = []
    missing_items: List[Any] = []
    extra_items: List[Any] = []

    used_pred = set()

    for ref_group in ref_groups:
        pred_idx = _find_equal_group_index(ref_group, pred_groups)
        ref_members = ref_group

        if pred_idx is None:
            missing_items.extend(ref_members)
            continue

        used_pred.add(pred_idx)
        pred_members = pred_groups[pred_idx]

        common = min(len(ref_members), len(pred_members))

        # Preserve ORIGINAL members rather than duplicating representative
        matched_items.extend(ref_members[:common])
        missing_items.extend(ref_members[common:])
        extra_items.extend(pred_members[common:])

    for idx, pred_group in enumerate(pred_groups):
        if idx in used_pred:
            continue
        extra_items.extend(pred_group)

    matched_repr = [_display_obj_brief(x) for x in matched_items]
    missing_repr = [_display_obj_brief(x) for x in missing_items]
    extra_repr = [_display_obj_brief(x) for x in extra_items]

    return {
        "num_reference": len(reference_items),
        "num_prediction": len(learned_items),
        "num_matched": len(matched_items),
        "num_missing_in_prediction": len(missing_items),
        "num_extra_in_prediction": len(extra_items),
        "matched": matched_repr,
        "missing_in_prediction": missing_repr,
        "extra_in_prediction": extra_repr,
        "matched_counts": _count_strings(matched_repr),
        "missing_in_prediction_counts": _count_strings(missing_repr),
        "extra_in_prediction_counts": _count_strings(extra_repr),
    }


def _set_diff(
    reference_items: List[Any],
    learned_items: List[Any],
    *,
    name_based: bool,
    object_kind: str,  # kept for call-site compatibility
) -> Dict[str, Any]:
    """
    Set-based diff for name-based compare.
    """
    reference_items = list(reference_items or [])
    learned_items = list(learned_items or [])

    _set_eq_strategy(reference_items, name_based=name_based)
    _set_eq_strategy(learned_items, name_based=name_based)

    ref_set = set(reference_items)
    pred_set = set(learned_items)

    matched = list(ref_set & pred_set)
    missing = list(ref_set - pred_set)
    extra = list(pred_set - ref_set)

    matched_repr = [_display_obj_brief(x) for x in sorted(matched, key=_display_obj_brief)]
    missing_repr = [_display_obj_brief(x) for x in sorted(missing, key=_display_obj_brief)]
    extra_repr = [_display_obj_brief(x) for x in sorted(extra, key=_display_obj_brief)]

    return {
        "num_reference": len(ref_set),
        "num_prediction": len(pred_set),
        "num_matched": len(matched),
        "num_missing_in_prediction": len(missing),
        "num_extra_in_prediction": len(extra),
        "matched": matched_repr,
        "missing_in_prediction": missing_repr,
        "extra_in_prediction": extra_repr,
        "matched_counts": _count_strings(matched_repr),
        "missing_in_prediction_counts": _count_strings(missing_repr),
        "extra_in_prediction_counts": _count_strings(extra_repr),
    }


def build_mismatch_details(
    reference_mapping: Any,
    learned_mapping: Any,
) -> Dict[str, Any]:
    reference_classes = list(reference_mapping.get_classes())
    learned_classes = list(learned_mapping.get_classes())

    reference_relations = list(reference_mapping.get_relations())
    learned_relations = list(learned_mapping.get_relations())

    reference_attributes = list(reference_mapping.get_attributes())
    learned_attributes = list(learned_mapping.get_attributes())

    return {
        "mapping_based": {
            "classes": _bag_diff(
                reference_classes, learned_classes,
                name_based=False, object_kind="classes"
            ),
            "relations": _bag_diff(
                reference_relations, learned_relations,
                name_based=False, object_kind="relations"
            ),
            "attributes": _bag_diff(
                reference_attributes, learned_attributes,
                name_based=False, object_kind="attributes"
            ),
        },
        "name_based": {
            "classes": _set_diff(
                reference_classes, learned_classes,
                name_based=True, object_kind="classes"
            ),
            "relations": _set_diff(
                reference_relations, learned_relations,
                name_based=True, object_kind="relations"
            ),
            "attributes": _set_diff(
                reference_attributes, learned_attributes,
                name_based=True, object_kind="attributes"
            ),
        },
    }


# ============================================================
# Main compare logic
# ============================================================

def run_compare(
    scenario_dir: Path,
    prediction_mapping_path: Path,
    gt_mapping_path: Optional[Path] = None,
    meta_path: Optional[Path] = None,
    database_name: Optional[str] = None,
    keep_workdir: bool = True,
    output_json: Optional[Path] = None,
    artifacts_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Scheme A:
      1) preprocess GT / prediction files into unified canonical mapping files
      2) feed preprocessed files into unmodified Burr parser + calculate_metrics
      3) save mismatch details separately
    """
    _, _, calculate_metrics = _import_local_burr_modules()

    scenario_dir = scenario_dir.resolve()
    prediction_mapping_path = prediction_mapping_path.resolve()

    gt_info = resolve_gt_for_scenario(scenario_dir)
    if meta_path is None:
        meta_path = default_meta_path_for_scenario(scenario_dir, gt_info)
    if meta_path is not None:
        meta_path = meta_path.resolve()

    db_name = infer_database_name(scenario_dir, database_name)

    raw_meta = read_json(meta_path) if meta_path is not None and meta_path.exists() else None
    meta = ensure_burr_meta(raw_meta)

    temp_root = Path(tempfile.mkdtemp(prefix="burr_preprocess_", dir=str(PROJECT_ROOT)))
    try:
        pred_pre = prepare_preprocessed_prediction(prediction_mapping_path, temp_root)
        gt_pre = prepare_preprocessed_gt(scenario_dir, gt_mapping_path, meta_path, temp_root)

        reference_mapping = load_mapping_as_d2rq(
            Path(gt_pre["preprocessed_path"]),
            db_name,
            meta,
        )
        learned_mapping = load_mapping_as_d2rq(
            Path(pred_pre["preprocessed_path"]),
            db_name,
            meta,
        )

        metrics = calculate_metrics(reference_mapping, learned_mapping)
        mismatch_details = build_mismatch_details(reference_mapping, learned_mapping)

        report: Dict[str, Any] = {
            "mode": "burr_original_after_preprocess",
            "scenario_dir": str(scenario_dir),
            "database_name": db_name,
            "meta_path": str(meta_path) if meta_path else None,
            "effective_meta": meta,
            "gt_preprocess": gt_pre,
            "prediction_preprocess": pred_pre,
            "metrics": metrics,
            "mismatch_details": mismatch_details,
        }

        if keep_workdir:
            if artifacts_dir is not None:
                saved_dir = artifacts_dir.resolve()
            else:
                saved_dir = PROJECT_ROOT / "compare_artifacts" / scenario_dir.name
                if output_json is not None:
                    saved_dir = output_json.resolve().parent / f"{output_json.stem}_artifacts"

            saved_dir.mkdir(parents=True, exist_ok=True)
            for item in temp_root.iterdir():
                shutil.copy2(item, saved_dir / item.name)
            report["saved_preprocessed_dir"] = str(saved_dir)

        if output_json is not None:
            write_json(output_json, report)

        return report

    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Burr original compare logic after canonical preprocessing of GT and prediction mappings."
    )
    parser.add_argument(
        "--scenario_dir",
        type=Path,
        default='burr_benchmark/real-world/mondial',
        help="Scenario directory that contains GT mapping / meta.",
    )
    parser.add_argument(
        "--prediction_mapping",
        type=Path,
        default='outputs/replay_from_draft_canonical/mapping.json',
        help="Predicted mapping file (.json or .ttl).",
    )
    parser.add_argument(
        "--gt_mapping",
        type=Path,
        default=None,
        help="Optional explicit GT mapping file (.json or .ttl). If omitted, resolve from scenario_dir.",
    )
    parser.add_argument(
        "--meta_path",
        type=Path,
        default=None,
        help="Optional explicit meta.json path.",
    )
    parser.add_argument(
        "--database_name",
        type=str,
        default=None,
        help="Optional explicit database name. Defaults to scenario_dir.name.",
    )
    parser.add_argument(
        "--output_json",
        type=Path,
        default="outputs/replay_from_draft_canonical/compare_multi.json",
        help="Optional path to save compare report JSON.",
    )
    parser.add_argument(
        "--no_keep_workdir",
        action="store_true",
        help="Do not save preprocessed files.",
    )
    parser.add_argument(
        "--artifacts_dir",
        type=Path,
        default="outputs/replay_from_draft_canonical/compare_multi.json",
        help="Optional path to save compare report JSON.",
    )

    args = parser.parse_args()

    report = run_compare(
        scenario_dir=args.scenario_dir,
        prediction_mapping_path=args.prediction_mapping,
        gt_mapping_path=args.gt_mapping,
        meta_path=args.meta_path,
        database_name=args.database_name,
        keep_workdir=not args.no_keep_workdir,
        output_json=args.output_json,
        artifacts_dir=args.artifacts_dir
    )

    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()