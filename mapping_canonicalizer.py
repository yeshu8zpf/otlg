from __future__ import annotations

import copy
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Basic helpers
# ============================================================

PLACEHOLDER_RE = re.compile(r"\{\s*([^{}]+?)\s*\}")
ATAT_RE = re.compile(r"@@\s*([^.@/\s]+)\s*\.\s*([^.@/\s]+)\s*@@", re.IGNORECASE)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def split_table_column(expr: str) -> Optional[Tuple[str, str]]:
    expr = expr.strip().strip('"').strip("'").strip()
    if "." not in expr:
        return None
    left, right = expr.split(".", 1)
    return left.strip().lower(), right.strip().lower()


def parse_join_equality(join_expr: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Example:
      "Province.Country = Country.Code"
      -> (("province", "country"), ("country", "code"))
    """
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
        return expr.strip().lower()
    t, c = tc
    return f"{t}.{c}"


def normalize_join_expr(expr: str) -> str:
    parsed = parse_join_equality(expr)
    if parsed is None:
        return re.sub(r"\s+", " ", expr.strip()).lower()
    (lt, lc), (rt, rc) = parsed
    return f"{lt}.{lc} = {rt}.{rc}"


def canonical_uri_pattern_from_columns(cols: List[Tuple[str, str]]) -> str:
    return "/".join(f"@@{t}.{c}@@" for t, c in cols)


def parse_existing_uri_pattern(pattern: str) -> Optional[List[Tuple[str, str]]]:
    """
    Extract @@table.column@@ tokens from an already-benchmark-like pattern.
    """
    matches = ATAT_RE.findall(pattern or "")
    if not matches:
        return None
    return [(t.lower(), c.lower()) for t, c in matches]


def extract_placeholders_from_template(template: str) -> List[str]:
    return [m.group(1).strip() for m in PLACEHOLDER_RE.finditer(template or "")]


def strip_literal_prefix(template: str) -> str:
    """
    country/{Code} -> {Code}
    province/{Country}/{Name} -> {Country}/{Name}
    """
    if not isinstance(template, str):
        return ""
    idx = template.find("{")
    if idx == -1:
        return template
    return template[idx:]


# ============================================================
# Index building from mapping JSON
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
    """
    returns:
      outgoing[class] = object props where belongsToClassMap == class
      incoming[class] = object props where refersToClassMap == class
    """
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
    """
    Heuristic:
      1. Count tables from data properties of this class.
      2. If empty, fall back to left/right join tables from outgoing object properties.
      3. Sort by frequency.
    """
    counter: Counter[str] = Counter()

    for dp in data_props_by_class.get(cls_name, []):
        col = dp.get("column")
        if isinstance(col, str):
            tc = split_table_column(col)
            if tc:
                counter[tc[0]] += 1

    if not counter:
        for op in outgoing_obj_props.get(cls_name, []):
            for j in op.get("join", []) if isinstance(op.get("join"), list) else [op.get("join")]:
                if not isinstance(j, str):
                    continue
                parsed = parse_join_equality(j)
                if parsed is None:
                    continue
                (lt, _), (rt, _) = parsed
                counter[lt] += 1
                counter[rt] += 1

    return [table for table, _ in counter.most_common()]


# ============================================================
# Placeholder -> column inference
# ============================================================

def pick_column_by_name_match(
    placeholder: str,
    candidate_columns: List[Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    ph = norm_name(placeholder)

    exact = [tc for tc in candidate_columns if norm_name(tc[1]) == ph]
    if exact:
        return exact[0]

    # softer fallback: placeholder token contained in column or vice versa
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
    """
    Use object properties where this class is the source.
    Typical for reified classes such as CountryLanguageUse / Border.
    """
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

            # Prefer the side whose table is a base table of the current class.
            local_side = None
            remote_side = None

            if left[0] in base_tables and right[0] not in base_tables:
                local_side, remote_side = left, right
            elif right[0] in base_tables and left[0] not in base_tables:
                local_side, remote_side = right, left
            elif left[0] in base_tables:
                local_side, remote_side = left, right
            elif right[0] in base_tables:
                local_side, remote_side = right, left

            if local_side is None:
                continue

            # Rule 1: placeholder name matches local column name
            for ph in placeholders:
                if ph in result:
                    continue
                if norm_name(ph) == norm_name(local_side[1]):
                    result[ph] = local_side

            # Rule 2: placeholder name matches target class name
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
    cls_name: str,
    base_tables: List[str],
) -> Dict[str, Tuple[str, str]]:
    """
    Use the literal prefix before the first placeholder, e.g.
      country/{Code} -> prefix 'country'
      province-population-record/{Country}/{Province}/{Year} -> prefix 'province-population-record'

    This is only a weak fallback.
    """
    result: Dict[str, Tuple[str, str]] = {}
    prefix = template.split("{", 1)[0].strip("/ ").strip().lower()
    prefix_norm = norm_name(prefix)

    # try base tables first
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
    """
    Main compiler for prediction-like class templates.
    """
    raw_id = cls_entry.get("id")
    cls_name = cls_entry.get("class") or cls_entry.get("name")
    if not isinstance(raw_id, str) or not isinstance(cls_name, str):
        return None

    # Case 1: already benchmark-like
    existing = parse_existing_uri_pattern(raw_id)
    if existing:
        return existing

    placeholders = extract_placeholders_from_template(raw_id)
    if not placeholders:
        return None

    base_tables = infer_base_tables_for_class(cls_name, data_props_by_class, outgoing_obj_props)

    resolved: Dict[str, Tuple[str, str]] = {}

    # Stage A: exact/fuzzy matches from data properties
    resolved.update(
        infer_columns_from_data_props(cls_name, placeholders, data_props_by_class)
    )

    # Stage B: use outgoing object properties + base tables
    from_obj = infer_columns_from_outgoing_object_props(
        cls_name, placeholders, base_tables, outgoing_obj_props
    )
    for ph, tc in from_obj.items():
        resolved.setdefault(ph, tc)

    # Stage C: weak fallback from template prefix
    from_prefix = infer_columns_by_template_prefix(raw_id, placeholders, cls_name, base_tables)
    for ph, tc in from_prefix.items():
        resolved.setdefault(ph, tc)

    # All placeholders must be resolved
    if any(ph not in resolved for ph in placeholders):
        return None

    return [resolved[ph] for ph in placeholders]


# ============================================================
# Mapping-wide canonicalization
# ============================================================

def canonicalize_class_ids(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(mapping)

    data_props_by_class = collect_data_props_by_class(out)
    outgoing_obj_props, _ = collect_object_props_by_class(out)

    unresolved: List[Dict[str, Any]] = []

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
            continue

        cls["id"] = canonical_uri_pattern_from_columns(cols).lower()

        # Normalize name / prefix casing too
        if "prefix" in cls and isinstance(cls["prefix"], str):
            cls["prefix"] = cls["prefix"].lower()

    # Also normalize columns / joins globally
    for dp in out.get("data_properties", []):
        if isinstance(dp.get("column"), str):
            dp["column"] = normalize_column_expr(dp["column"])

    for op in out.get("object_properties", []):
        joins = op.get("join", [])
        if isinstance(joins, list):
            op["join"] = [normalize_join_expr(j) for j in joins if isinstance(j, str)]
        elif isinstance(joins, str):
            op["join"] = [normalize_join_expr(joins)]

    out["_canonicalization_debug"] = {
        "unresolved_classes": unresolved,
    }
    return out


def canonicalize_mapping_file(input_path: Path, output_path: Path) -> Dict[str, Any]:
    mapping = load_json(input_path)
    canonical = canonicalize_class_ids(mapping)
    dump_json(output_path, canonical)
    return canonical