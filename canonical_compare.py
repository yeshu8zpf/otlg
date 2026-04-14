from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ============================================================
# Low-level normalization helpers
# ============================================================

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")


def _as_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x)


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _dedup_keep_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in items:
        key = json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (dict, list)) else repr(x)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def _camel_symbol(text: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", _as_str(text).strip())
    parts = [p for p in parts if p]
    if not parts:
        return "UNKNOWN"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def _snake_symbol(text: str) -> str:
    s = _as_str(text).strip()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def _safe_property_symbol(text: str) -> str:
    """
    Canonical property symbol used in canonical compare.
    Keeps semantic name, removes formatting noise.
    """
    s = _as_str(text).strip()
    if not s:
        return "unknown"
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def _safe_class_symbol(text: str) -> str:
    """
    Canonical class symbol for compare.
    Removes spaces/punctuation and normalizes to CamelCase-like token.
    """
    s = _as_str(text).strip()
    if not s:
        return "UNKNOWN"
    s = s.replace("Class:", "")
    return _camel_symbol(s)


def _parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    s = _as_str(s).strip()
    m = QUALIFIED_COL_RE.match(s)
    if not m:
        return None
    return m.group(1).lower(), m.group(2).lower()


def _normalize_column(col: str, fallback_table: str = "") -> str:
    """
    Normalize column token to 'table.column' when possible.
    """
    col = _as_str(col).strip()
    fallback_table = _as_str(fallback_table).strip()

    if not col:
        return ""

    parsed = _parse_qualified_column(col)
    if parsed:
        return f"{parsed[0]}.{parsed[1]}"

    if fallback_table and IDENT_RE.match(fallback_table) and IDENT_RE.match(col):
        return f"{fallback_table.lower()}.{col.lower()}"

    return col.lower()


def _extract_identifier_columns_from_uri_pattern(uri_pattern: str) -> List[str]:
    """
    Extract canonical identifier columns from many surface forms.

    Supported:
      @@country.code@@
      @@province.country@@/@@province.name@@
      hotel/@@hotel.id@@
      country/{code}
      province/{country}/{name}
      {country.code}
      country.code
    """
    text = _as_str(uri_pattern).strip()
    if not text:
        return []

    cols: List[str] = []

    # 1) Burr tokens @@table.column@@
    start = 0
    while True:
        i = text.find("@@", start)
        if i == -1:
            break
        j = text.find("@@", i + 2)
        if j == -1:
            break
        token = text[i + 2 : j].strip()
        token_norm = _normalize_column(token)
        if _parse_qualified_column(token_norm):
            cols.append(token_norm)
        start = j + 2

    if cols:
        return _dedup_keep_order(cols)

    # 2) Braces: {table.column} OR {column}
    brace_tokens = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\}", text)
    if brace_tokens:
        # If path looks like country/{code}, use first path segment as fallback table
        path_parts = [p.strip() for p in text.split("/") if p.strip()]
        fallback_table = ""
        if path_parts and not path_parts[0].startswith("{") and "@@" not in path_parts[0]:
            if IDENT_RE.match(path_parts[0]):
                fallback_table = path_parts[0]

        for tok in brace_tokens:
            token_norm = _normalize_column(tok, fallback_table=fallback_table)
            if _parse_qualified_column(token_norm):
                cols.append(token_norm)
        if cols:
            return _dedup_keep_order(cols)

    # 3) Plain qualified columns in path
    path_parts = [p.strip() for p in text.split("/") if p.strip()]
    for part in path_parts:
        token = part
        token = token.strip("{}")
        token_norm = _normalize_column(token)
        if _parse_qualified_column(token_norm):
            cols.append(token_norm)

    return _dedup_keep_order(cols)


def _normalize_join_string(join_str: str) -> Optional[Tuple[str, str, str]]:
    """
    Normalize join string to ('table.col', '=', 'table.col')
    """
    s = _as_str(join_str).strip()
    if not s:
        return None

    m = re.match(r"^\s*(\S+)\s*(=|!=|<>|>=|<=|>|<)\s*(\S+)\s*$", s)
    if not m:
        return None

    lhs = _normalize_column(m.group(1))
    op = m.group(2)
    rhs = _normalize_column(m.group(3))

    return lhs, op, rhs


def _normalize_joins(join_values: Any) -> Tuple[Tuple[str, str, str], ...]:
    out: List[Tuple[str, str, str]] = []

    for j in _as_list(join_values):
        if isinstance(j, list) and len(j) >= 3:
            lhs = _normalize_column(j[0])
            op = _as_str(j[1]).strip()
            rhs = _normalize_column(j[2])
            if lhs and op and rhs:
                out.append((lhs, op, rhs))
            continue

        norm = _normalize_join_string(_as_str(j))
        if norm is not None:
            out.append(norm)

    out = sorted(set(out))
    return tuple(out)


# ============================================================
# Canonical records
# ============================================================

@dataclass(frozen=True)
class CanonicalClass:
    class_uri: str
    identifier_columns: Tuple[str, ...]

    def __str__(self) -> str:
        return f"CanonicalClass(class_uri={self.class_uri}, ids={list(self.identifier_columns)})"


@dataclass(frozen=True)
class CanonicalRelation:
    property_symbol: str
    belongs_to: str
    refers_to: str
    joins: Tuple[Tuple[str, str, str], ...]

    def __str__(self) -> str:
        return (
            f"CanonicalRelation(property={self.property_symbol}, "
            f"belongs_to={self.belongs_to}, refers_to={self.refers_to}, joins={list(self.joins)})"
        )


@dataclass(frozen=True)
class CanonicalAttribute:
    property_symbol: str
    belongs_to: str
    column: str

    def __str__(self) -> str:
        return (
            f"CanonicalAttribute(property={self.property_symbol}, "
            f"belongs_to={self.belongs_to}, column={self.column})"
        )


# ============================================================
# D2RQ / Burr object canonicalization
# ============================================================

def _canonicalize_class_obj(obj: Any) -> CanonicalClass:
    """
    Supports Burr mapping_parser ClassMap-like objects.
    Expected attributes:
      - class_uri
      - uriPattern
    """
    class_uri = _safe_class_symbol(getattr(obj, "class_uri", "") or getattr(obj, "class_name", ""))
    uri_pattern = _as_str(getattr(obj, "uriPattern", "") or getattr(obj, "uri_pattern", ""))
    identifier_columns = tuple(_extract_identifier_columns_from_uri_pattern(uri_pattern))
    return CanonicalClass(class_uri=class_uri, identifier_columns=identifier_columns)


def _canonicalize_relation_obj(obj: Any) -> CanonicalRelation:
    """
    Supports Burr relation objects.
    Expected attrs:
      - property
      - belongsToClassMap
      - refersToClassMap
      - join / joins
    """
    property_symbol = _safe_property_symbol(getattr(obj, "property", ""))
    belongs_to = _safe_class_symbol(getattr(obj, "belongsToClassMap", "") or getattr(obj, "belongs_to", ""))
    refers_to = _safe_class_symbol(getattr(obj, "refersToClassMap", "") or getattr(obj, "refers_to", ""))

    joins_raw = getattr(obj, "join", None)
    if joins_raw is None:
        joins_raw = getattr(obj, "joins", None)

    joins = _normalize_joins(joins_raw)
    return CanonicalRelation(
        property_symbol=property_symbol,
        belongs_to=belongs_to,
        refers_to=refers_to,
        joins=joins,
    )


def _canonicalize_attribute_obj(obj: Any) -> CanonicalAttribute:
    """
    Supports Burr attribute/relation objects used as property bridges.
    Expected attrs:
      - property
      - belongsToClassMap
      - column
    """
    property_symbol = _safe_property_symbol(getattr(obj, "property", ""))
    belongs_to = _safe_class_symbol(getattr(obj, "belongsToClassMap", "") or getattr(obj, "belongs_to", ""))
    column = _normalize_column(getattr(obj, "column", ""))
    return CanonicalAttribute(
        property_symbol=property_symbol,
        belongs_to=belongs_to,
        column=column,
    )


# ============================================================
# Diff helpers
# ============================================================

def _bag_diff(reference_items: List[Any], learned_items: List[Any]) -> Dict[str, Any]:
    ref_counter = Counter(reference_items)
    pred_counter = Counter(learned_items)

    matched: List[str] = []
    missing: List[str] = []
    extra: List[str] = []

    all_keys = list(set(ref_counter.keys()) | set(pred_counter.keys()))
    for k in all_keys:
        ref_n = ref_counter.get(k, 0)
        pred_n = pred_counter.get(k, 0)
        common = min(ref_n, pred_n)

        matched.extend([str(k)] * common)
        if ref_n > pred_n:
            missing.extend([str(k)] * (ref_n - pred_n))
        if pred_n > ref_n:
            extra.extend([str(k)] * (pred_n - ref_n))

    return {
        "num_reference": sum(ref_counter.values()),
        "num_prediction": sum(pred_counter.values()),
        "num_matched": len(matched),
        "num_missing_in_prediction": len(missing),
        "num_extra_in_prediction": len(extra),
        "matched": matched,
        "missing_in_prediction": missing,
        "extra_in_prediction": extra,
    }


# ============================================================
# Public API
# ============================================================

def build_canonical_details(reference_mapping: Any, learned_mapping: Any) -> Dict[str, Any]:
    """
    Canonical, representation-normalized compare.
    This is NOT meant to replace Burr's official metrics.
    It complements them by removing surface-form mismatch.
    """
    ref_classes = [_canonicalize_class_obj(x) for x in reference_mapping.get_classes()]
    ref_relations = [_canonicalize_relation_obj(x) for x in reference_mapping.get_relations()]
    ref_attributes = [_canonicalize_attribute_obj(x) for x in reference_mapping.get_attributes()]

    pred_classes = [_canonicalize_class_obj(x) for x in learned_mapping.get_classes()]
    pred_relations = [_canonicalize_relation_obj(x) for x in learned_mapping.get_relations()]
    pred_attributes = [_canonicalize_attribute_obj(x) for x in learned_mapping.get_attributes()]

    class_diff = _bag_diff(ref_classes, pred_classes)
    rel_diff = _bag_diff(ref_relations, pred_relations)
    attr_diff = _bag_diff(ref_attributes, pred_attributes)

    def f1_block(diff: Dict[str, Any]) -> Dict[str, Any]:
        tp = diff["num_matched"]
        ref_n = diff["num_reference"]
        pred_n = diff["num_prediction"]

        precision = tp / pred_n if pred_n > 0 else 0.0
        recall = tp / ref_n if ref_n > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    return {
        "metrics": {
            "classes": f1_block(class_diff),
            "relations": f1_block(rel_diff),
            "attributes": f1_block(attr_diff),
        },
        "details": {
            "classes": class_diff,
            "relations": rel_diff,
            "attributes": attr_diff,
        },
    }