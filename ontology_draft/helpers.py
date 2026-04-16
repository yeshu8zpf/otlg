from __future__ import annotations

import copy
import json
import re
from dataclasses import fields
from typing import Any, Dict, Iterable, List, Optional, Tuple

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")


def to_burr_safe_property_name(label: str) -> str:
    s = str(label or "").strip()
    if not s:
        return "UNKNOWN"
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "UNKNOWN"


def to_burr_safe_classmap_name(label: str) -> str:
    s = str(label or "").strip()
    if not s:
        return "UNKNOWN"
    parts = re.split(r"[^A-Za-z0-9]+", s)
    parts = [p for p in parts if p]
    if not parts:
        return "UNKNOWN"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def as_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x)


def safe_dict(x: Any) -> Dict[str, Any]:
    return dict(x) if isinstance(x, dict) else {}


def dedup_keep_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in items:
        key = json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (dict, list)) else repr(x)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def field_names(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def split_kwargs(cls, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    allowed = field_names(cls)
    known = {k: v for k, v in data.items() if k in allowed and k != "extras"}
    extra = {k: v for k, v in data.items() if k not in allowed}
    return known, extra


def normalize_class_id(label: str) -> str:
    label = as_str(label).strip()
    if not label:
        return "Class:UNKNOWN"
    if label.startswith("Class:"):
        return label
    return f"Class:{label}"


def normalize_data_property_id(domain_class: str, label: str) -> str:
    domain_label = normalize_class_id(domain_class).replace("Class:", "")
    label = as_str(label).strip() or "UNKNOWN"
    if label.startswith("DataProperty:"):
        return label
    return f"DataProperty:{domain_label}.{label}"


def normalize_object_property_id(domain_class: str, label: str) -> str:
    domain_label = normalize_class_id(domain_class).replace("Class:", "")
    label = as_str(label).strip() or "UNKNOWN"
    if label.startswith("ObjectProperty:"):
        return label
    return f"ObjectProperty:{domain_label}.{label}"


def parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    s = (s or "").strip()
    m = QUALIFIED_COL_RE.match(s)
    if not m:
        return None
    return m.group(1), m.group(2)


def extract_identifier_columns(template: str) -> List[str]:
    template = as_str(template)
    cols: List[str] = []
    start = 0
    while True:
        i = template.find("@@", start)
        if i == -1:
            break
        j = template.find("@@", i + 2)
        if j == -1:
            break
        cols.append(template[i + 2:j].strip())
        start = j + 2
    cols.extend(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}", template))
    return dedup_keep_order([c for c in cols if c])


def infer_tables_from_template(template: str) -> List[str]:
    cols = extract_identifier_columns(template)
    tables: List[str] = []
    for c in cols:
        parsed = parse_qualified_column(c)
        if parsed:
            t, _ = parsed
            if t not in tables:
                tables.append(t)
    if not tables:
        guess = as_str(template).split("/", 1)[0].strip()
        if guess and IDENT_RE.match(guess):
            tables.append(guess)
    return tables


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


def join_to_burr_string(join_tokens: List[str]) -> str:
    return " ".join([str(x) for x in join_tokens if str(x).strip()])


def label_from_class_id(class_id: str) -> str:
    cid = normalize_class_id(class_id)
    raw = cid.replace("Class:", "")
    return to_burr_safe_classmap_name(raw)


def coerce_float01(x: Any) -> Optional[float]:
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


def ensure_qualified_column(column: str, source_table: str = "") -> str:
    col = as_str(column).strip()
    tbl = as_str(source_table).strip()
    if not col:
        return ""
    if parse_qualified_column(col) is not None:
        return col
    if tbl and IDENT_RE.match(tbl):
        return f"{tbl}.{col}"
    return col


def ensure_burr_template(
    template: str,
    fallback_table: str = "",
    fallback_identifier_columns: Optional[List[str]] = None,
) -> str:
    text = as_str(template).strip()
    fallback_identifier_columns = fallback_identifier_columns or []

    if not text and fallback_identifier_columns:
        col = ensure_qualified_column(fallback_identifier_columns[0], fallback_table)
        if parse_qualified_column(col):
            return f"@@{col}@@"

    if not text:
        return ""

    if "@@" in text:
        return text

    def repl(m):
        inner = m.group(1).strip()
        inner = ensure_qualified_column(inner, fallback_table)
        return f"@@{inner}@@"

    text = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}", repl, text)
    if "@@" in text:
        return text

    if parse_qualified_column(text):
        return f"@@{text}@@"

    maybe = ensure_qualified_column(text, fallback_table)
    if parse_qualified_column(maybe):
        return f"@@{maybe}@@"

    return text


def copy_deep(x: Any) -> Any:
    return copy.deepcopy(x)
