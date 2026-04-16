from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def coerce_confidence(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        v = float(x)
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v
    except Exception:
        return None


def normalize_ws(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def normalize_identifier(s: Any) -> str:
    return normalize_ws(s)


def strip_prefix_if_present(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def normalize_class_id(x: Any) -> str:
    s = normalize_identifier(x)
    if not s:
        return ""
    if s.startswith("Class:"):
        return s
    return f"Class:{s}"


def normalize_property_id(x: Any, kind: str) -> str:
    s = normalize_identifier(x)
    if not s:
        return ""
    wanted = f"{kind}:"
    if s.startswith(wanted):
        return s
    if ":" in s:
        return s
    return f"{kind}:{s}"


def normalize_range_type(x: Any) -> str:
    s = normalize_ws(x)
    if not s:
        return "string"
    low = s.lower()
    if low in {"str", "string", "text", "varchar", "character varying"}:
        return "string"
    if low in {"int", "integer", "bigint", "smallint"}:
        return "integer"
    if low in {"float", "double", "real", "numeric", "decimal"}:
        return "decimal"
    if low in {"bool", "boolean"}:
        return "boolean"
    if low == "date":
        return "date"
    if low in {"datetime", "timestamp"}:
        return "datetime"
    return s


def normalize_join(join_value: Any) -> List[str]:
    if isinstance(join_value, list):
        return [str(x).strip() for x in join_value if str(x).strip()]
    if isinstance(join_value, str):
        text = join_value.strip()
        if not text:
            return []
        m = re.match(r"^\s*(\S+)\s*(=|!=|<>|>=|<=|>|<)\s*(\S+)\s*$", text)
        if m:
            return [m.group(1), m.group(2), m.group(3)]
        return [t for t in text.split() if t]
    return [str(join_value)]


def normalize_join_list(x: Any) -> List[List[str]]:
    out: List[List[str]] = []
    for j in as_list(x):
        norm = normalize_join(j)
        if norm:
            out.append(norm)
    return out


def normalize_column_list(x: Any) -> List[str]:
    out: List[str] = []
    for c in as_list(x):
        s = normalize_identifier(c)
        if s:
            out.append(s)
    return list(dict.fromkeys(out))


def normalize_optional_string(x: Any) -> str:
    return normalize_ws(x)


def build_index_by_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for x in items:
        xid = x.get("id")
        if xid:
            out[str(xid)] = x
    return out


def find_root_payload(obj: Dict[str, Any], collector) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        collector.add("warning", "ROOT_NOT_DICT", "Root payload is not a dict; coercing to empty dict.")
        return {}

    direct_signal_keys = {
        "classes",
        "data_properties",
        "object_properties",
        "subclass_relations",
        "class_mappings",
        "data_property_mappings",
        "object_property_mappings",
    }
    if any(k in obj for k in direct_signal_keys):
        return obj

    for container_key in ["ontology", "draft", "output", "result", "payload", "data"]:
        inner = obj.get(container_key)
        if isinstance(inner, dict) and any(k in inner for k in direct_signal_keys):
            collector.add("info", "ROOT_UNWRAPPED", f"Unwrapped nested payload from '{container_key}'.", path=container_key)
            return inner

    return obj
