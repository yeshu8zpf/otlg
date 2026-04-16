from __future__ import annotations

import copy
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


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


def collect_object_props_by_class(
    mapping: Dict[str, Any],
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
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