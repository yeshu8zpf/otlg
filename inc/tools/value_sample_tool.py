from __future__ import annotations

import ast
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ValueSampleToolConfig:
    db_path: Optional[Path] = None
    schema_sql_path: Optional[Path] = None
    sample_limit: int = 8
    distinct_limit: int = 20


# -----------------------------
# shared helpers
# -----------------------------

def _split_table_column(col: str) -> Optional[Tuple[str, str]]:
    s = str(col or "").strip()
    if "." not in s:
        return None
    t, c = s.split(".", 1)
    t = t.strip()
    c = c.strip()
    if not t or not c:
        return None
    return t, c


def _quote_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _dedupe_preserve_order(xs: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# -----------------------------
# sqlite path
# -----------------------------

def _safe_fetchall(conn: sqlite3.Connection, sql: str) -> List[tuple]:
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()


def _sample_one_column_sqlite(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    *,
    sample_limit: int,
    distinct_limit: int,
) -> Dict[str, Any]:
    qt = _quote_ident(table)
    qc = _quote_ident(column)

    result: Dict[str, Any] = {
        "source": "sqlite_db",
        "table": table,
        "column": column,
        "sample_values": [],
        "distinct_count": None,
        "null_count": None,
        "row_count": None,
        "non_null_ratio": None,
        "top_distinct_values": [],
    }

    try:
        row_count = _safe_fetchall(conn, f"SELECT COUNT(*) FROM {qt}")[0][0]
        null_count = _safe_fetchall(conn, f"SELECT COUNT(*) FROM {qt} WHERE {qc} IS NULL")[0][0]
        distinct_count = _safe_fetchall(
            conn, f"SELECT COUNT(DISTINCT {qc}) FROM {qt} WHERE {qc} IS NOT NULL"
        )[0][0]

        samples = _safe_fetchall(
            conn,
            f"SELECT {qc} FROM {qt} WHERE {qc} IS NOT NULL LIMIT {int(sample_limit)}"
        )

        top_vals = _safe_fetchall(
            conn,
            f"""
            SELECT {qc}, COUNT(*) AS cnt
            FROM {qt}
            WHERE {qc} IS NOT NULL
            GROUP BY {qc}
            ORDER BY cnt DESC
            LIMIT {int(distinct_limit)}
            """
        )

        result["row_count"] = row_count
        result["null_count"] = null_count
        result["distinct_count"] = distinct_count
        result["sample_values"] = [x[0] for x in samples]
        result["top_distinct_values"] = [{"value": x[0], "count": x[1]} for x in top_vals]
        result["non_null_ratio"] = (
            float(row_count - null_count) / float(row_count) if row_count else None
        )
    except Exception as e:
        result["error"] = str(e)

    return result


def sample_columns_from_sqlite(
    *,
    db_path: Path,
    qualified_columns: List[str],
    sample_limit: int = 8,
    distinct_limit: int = 20,
) -> List[Dict[str, Any]]:
    if not db_path.exists():
        return [
            {
                "type": "value_sample_error",
                "message": f"Database file does not exist: {db_path}",
            }
        ]

    parsed: List[Tuple[str, str]] = []
    for qc in qualified_columns:
        tc = _split_table_column(qc)
        if tc is not None:
            parsed.append(tc)

    if not parsed:
        return []

    conn = sqlite3.connect(str(db_path))
    try:
        out = []
        for table, column in parsed:
            out.append(
                _sample_one_column_sqlite(
                    conn,
                    table,
                    column,
                    sample_limit=sample_limit,
                    distinct_limit=distinct_limit,
                )
            )
        return out
    finally:
        conn.close()


# -----------------------------
# schema.sql fallback path
# -----------------------------

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*VALUES\s*(.*?);",
    re.IGNORECASE | re.DOTALL,
)


def _normalize_sql_literal(token: str) -> Any:
    s = token.strip()
    if not s:
        return None

    if s.upper() == "NULL":
        return None

    # quoted string
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        inner = s[1:-1].replace("''", "'")
        return inner

    # integer
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except Exception:
            return s

    # float
    if re.fullmatch(r"-?\d+\.\d+", s):
        try:
            return float(s)
        except Exception:
            return s

    return s


def _split_value_tuples(values_blob: str) -> List[str]:
    """
    Split:
      (...), (...), (...)
    into each tuple body string, preserving commas inside quoted strings.
    """
    out: List[str] = []
    depth = 0
    in_str = False
    i = 0
    start = None
    blob = values_blob.strip()

    while i < len(blob):
        ch = blob[i]

        if ch == "'":
            if in_str:
                # escaped quote ''
                if i + 1 < len(blob) and blob[i + 1] == "'":
                    i += 2
                    continue
                in_str = False
            else:
                in_str = True
            i += 1
            continue

        if not in_str:
            if ch == "(":
                if depth == 0:
                    start = i + 1
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(blob[start:i])
                    start = None

        i += 1

    return out


def _split_tuple_fields(tuple_body: str) -> List[str]:
    """
    Split one tuple body:
      1, 'abc', NULL, 'x,y'
    preserving commas inside quoted strings.
    """
    fields: List[str] = []
    cur: List[str] = []
    in_str = False
    i = 0
    s = tuple_body

    while i < len(s):
        ch = s[i]

        if ch == "'":
            cur.append(ch)
            if in_str:
                if i + 1 < len(s) and s[i + 1] == "'":
                    cur.append(s[i + 1])
                    i += 2
                    continue
                in_str = False
            else:
                in_str = True
            i += 1
            continue

        if ch == "," and not in_str:
            fields.append("".join(cur).strip())
            cur = []
            i += 1
            continue

        cur.append(ch)
        i += 1

    if cur:
        fields.append("".join(cur).strip())

    return fields


def _parse_insert_rows_from_sql_text(sql_text: str) -> Dict[str, Dict[str, List[Any]]]:
    """
    Return:
      {
        "papers": {
          "paperid": [...],
          "publish": [...],
          ...
        },
        ...
      }
    """
    table_col_values: Dict[str, Dict[str, List[Any]]] = {}

    for m in _INSERT_RE.finditer(sql_text):
        table = m.group(1).strip().lower()
        raw_cols = m.group(2)
        raw_values_blob = m.group(3)

        cols = [c.strip().strip('"').lower() for c in raw_cols.split(",")]
        tuples = _split_value_tuples(raw_values_blob)

        if table not in table_col_values:
            table_col_values[table] = {c: [] for c in cols}
        else:
            for c in cols:
                table_col_values[table].setdefault(c, [])

        for tup in tuples:
            fields = _split_tuple_fields(tup)
            if len(fields) != len(cols):
                # skip malformed row rather than crashing
                continue
            for c, raw_v in zip(cols, fields):
                table_col_values[table][c].append(_normalize_sql_literal(raw_v))

    return table_col_values


def _sample_one_column_from_sql_dump(
    parsed_dump: Dict[str, Dict[str, List[Any]]],
    table: str,
    column: str,
    *,
    sample_limit: int,
    distinct_limit: int,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "source": "schema_sql_dump",
        "table": table,
        "column": column,
        "sample_values": [],
        "distinct_count": None,
        "null_count": None,
        "row_count": None,
        "non_null_ratio": None,
        "top_distinct_values": [],
    }

    table_data = parsed_dump.get(table.lower())
    if not table_data:
        result["error"] = f"Table not found in SQL dump inserts: {table}"
        return result

    values = table_data.get(column.lower())
    if values is None:
        result["error"] = f"Column not found in SQL dump inserts: {table}.{column}"
        return result

    row_count = len(values)
    null_count = sum(1 for v in values if v is None)
    non_null = [v for v in values if v is not None]

    counts: Dict[str, int] = {}
    for v in non_null:
        k = repr(v)
        counts[k] = counts.get(k, 0) + 1

    # keep first representative value for each repr
    repr_to_value: Dict[str, Any] = {}
    for v in non_null:
        repr_to_value.setdefault(repr(v), v)

    top_keys = sorted(counts.keys(), key=lambda k: (-counts[k], k))[:distinct_limit]

    result["row_count"] = row_count
    result["null_count"] = null_count
    result["distinct_count"] = len(counts)
    result["sample_values"] = non_null[:sample_limit]
    result["top_distinct_values"] = [
        {"value": repr_to_value[k], "count": counts[k]} for k in top_keys
    ]
    result["non_null_ratio"] = float(len(non_null)) / float(row_count) if row_count else None
    return result


def sample_columns_from_schema_sql(
    *,
    schema_sql_path: Path,
    qualified_columns: List[str],
    sample_limit: int = 8,
    distinct_limit: int = 20,
) -> List[Dict[str, Any]]:
    if not schema_sql_path.exists():
        return [
            {
                "type": "value_sample_error",
                "message": f"Schema SQL file does not exist: {schema_sql_path}",
            }
        ]

    sql_text = schema_sql_path.read_text(encoding="utf-8", errors="ignore")
    parsed_dump = _parse_insert_rows_from_sql_text(sql_text)

    out: List[Dict[str, Any]] = []
    for qc in qualified_columns:
        tc = _split_table_column(qc)
        if tc is None:
            continue
        table, column = tc
        out.append(
            _sample_one_column_from_sql_dump(
                parsed_dump,
                table,
                column,
                sample_limit=sample_limit,
                distinct_limit=distinct_limit,
            )
        )
    return out


# -----------------------------
# unified revision evidence entry
# -----------------------------

def build_revision_value_sample_evidence(
    *,
    revision_scope: Dict[str, Any],
    db_path: Optional[Path] = None,
    schema_sql_path: Optional[Path] = None,
    sample_limit: int = 8,
    distinct_limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Priority:
    1. db_path if provided and exists
    2. schema_sql_path fallback
    """
    qualified_columns: List[str] = []

    schema_scope = revision_scope.get("schema_scope", {}) or {}
    local_table = schema_scope.get("local_table", {}) or {}
    local_table_name = str(local_table.get("name", "")).strip()

    for col in local_table.get("columns", []) or []:
        col_name = str(col.get("name", "")).strip()
        if local_table_name and col_name:
            qualified_columns.append(f"{local_table_name}.{col_name}")

    draft_slice = revision_scope.get("draft_slice", {}) or {}

    for dpm in draft_slice.get("data_property_mappings", []) or []:
        for qc in dpm.get("source_columns", []) or []:
            if isinstance(qc, str) and "." in qc:
                qualified_columns.append(qc)

    for cm in draft_slice.get("class_mappings", []) or []:
        for cond in cm.get("condition", []) or []:
            if isinstance(cond, str):
                tokens = (
                    cond.replace("=", " ")
                    .replace(">", " ")
                    .replace("<", " ")
                    .replace("(", " ")
                    .replace(")", " ")
                    .split()
                )
                for tok in tokens:
                    if "." in tok:
                        qualified_columns.append(tok.strip())

    qualified_columns = _dedupe_preserve_order(qualified_columns)

    if db_path is not None and db_path.exists():
        samples = sample_columns_from_sqlite(
            db_path=db_path,
            qualified_columns=qualified_columns,
            sample_limit=sample_limit,
            distinct_limit=distinct_limit,
        )
        return [
            {
                "type": "value_samples",
                "backend": "sqlite_db",
                "db_path": str(db_path),
                "columns": qualified_columns,
                "results": samples,
            }
        ]

    if schema_sql_path is not None and schema_sql_path.exists():
        samples = sample_columns_from_schema_sql(
            schema_sql_path=schema_sql_path,
            qualified_columns=qualified_columns,
            sample_limit=sample_limit,
            distinct_limit=distinct_limit,
        )
        return [
            {
                "type": "value_samples",
                "backend": "schema_sql_dump",
                "schema_sql_path": str(schema_sql_path),
                "columns": qualified_columns,
                "results": samples,
            }
        ]

    return [
        {
            "type": "value_sample_error",
            "message": "Neither usable db_path nor schema_sql_path was provided for value sampling.",
            "columns": qualified_columns,
        }
    ]