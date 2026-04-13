from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple

CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)

FK_INLINE_RE = re.compile(
    r"FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)",
    re.IGNORECASE | re.DOTALL,
)

ALTER_TABLE_FK_RE = re.compile(
    r"""
    ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>[A-Za-z_][A-Za-z0-9_]*)
    .*?
    FOREIGN\s+KEY\s*\((?P<cols>[^)]*)\)
    \s+REFERENCES\s+(?P<ref_table>[A-Za-z_][A-Za-z0-9_]*)
    \s*\((?P<ref_cols>[^)]*)\)
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

PRIMARY_KEY_RE = re.compile(
    r"PRIMARY\s+KEY\s*\((.*?)\)",
    re.IGNORECASE | re.DOTALL,
)

QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")


def safe_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    m = QUALIFIED_COL_RE.match((s or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def split_sql_columns(text: str) -> List[str]:
    parts = [p.strip() for p in text.split(",")]
    return [p for p in parts if p]


def normalize_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def guess_is_boolean_like(values: List[str]) -> bool:
    normalized = {str(v).strip().lower() for v in values if str(v).strip() != ""}
    if not normalized:
        return False
    allowed = {"0", "1", "true", "false", "t", "f", "yes", "no", "y", "n"}
    return normalized.issubset(allowed)


def guess_basic_type(values: List[str]) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip() != ""]
    if not cleaned:
        return "unknown"

    def is_int(x: str) -> bool:
        try:
            int(x)
            return True
        except Exception:
            return False

    def is_float(x: str) -> bool:
        try:
            float(x)
            return True
        except Exception:
            return False

    if all(is_int(v) for v in cleaned):
        return "integer"
    if all(is_float(v) for v in cleaned):
        return "float"
    if guess_is_boolean_like(cleaned):
        return "boolean"
    return "string"
