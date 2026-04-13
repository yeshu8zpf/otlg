from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .common import (
    ALTER_TABLE_FK_RE,
    CREATE_TABLE_RE,
    FK_INLINE_RE,
    PRIMARY_KEY_RE,
    split_sql_columns,
)


# ============================================================
# Data structures
# ============================================================


@dataclass
class ColumnProfile:
    name: str
    sql_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    raw_sql: str = ""


@dataclass
class ForeignKeyProfile:
    columns: List[str]
    referenced_table: str
    referenced_columns: List[str]


@dataclass
class TableProfile:
    name: str
    columns: List[ColumnProfile] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyProfile] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    raw_sql_body: str = ""


# ============================================================
# Profiler
# ============================================================


class SchemaProfiler:
    """
    Extracts lightweight structural information from schema SQL.

    Output shape:
    {
      "tables": {
        table_name: {
          "name": ...,
          "columns": [...],
          "primary_key": [...],
          "foreign_keys": [...],
          "unique_constraints": [...],
          "raw_sql_body": ...
        }
      },
      "join_graph": {
        table_name: [
          {
            "to_table": ...,
            "from_columns": [...],
            "to_columns": [...],
            "joins": [["a.x", "=", "b.y"], ...]
          }
        ]
      },
      "stats": {
        "num_tables": ...,
        "num_columns": ...,
        "num_foreign_keys": ...
      }
    }
    """

    # --------------------------------------------------------
    # Internal parsing helpers
    # --------------------------------------------------------

    def _split_body_items(self, body: str) -> List[str]:
        """
        Split CREATE TABLE body by top-level commas only.
        Handles nested parentheses in types/constraints.
        """
        items: List[str] = []
        current: List[str] = []
        depth = 0

        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)

            if ch == "," and depth == 0:
                item = "".join(current).strip()
                if item:
                    items.append(item)
                current = []
            else:
                current.append(ch)

        tail = "".join(current).strip()
        if tail:
            items.append(tail)

        return items

    def _parse_column_def(self, item: str) -> Optional[ColumnProfile]:
        item = item.strip()
        upper = item.upper()

        if (
            upper.startswith("PRIMARY KEY")
            or upper.startswith("FOREIGN KEY")
            or upper.startswith("UNIQUE")
            or upper.startswith("CONSTRAINT")
            or upper.startswith("CHECK")
        ):
            return None

        parts = item.split()
        if not parts:
            return None

        name = parts[0].strip('"')
        sql_type = parts[1] if len(parts) > 1 else "UNKNOWN"

        return ColumnProfile(
            name=name,
            sql_type=sql_type,
            is_nullable=("NOT NULL" not in upper),
            is_primary_key=("PRIMARY KEY" in upper),
            raw_sql=item,
        )

    def _parse_inline_fk_from_item(self, item: str) -> Optional[ForeignKeyProfile]:
        m = FK_INLINE_RE.search(item)
        if not m:
            return None

        cols = split_sql_columns(m.group(1))
        ref_table = m.group(2)
        ref_cols = split_sql_columns(m.group(3))

        return ForeignKeyProfile(
            columns=cols,
            referenced_table=ref_table,
            referenced_columns=ref_cols,
        )

    def _parse_unique_constraint(self, item: str) -> Optional[List[str]]:
        text = item.strip()
        upper = text.upper()

        if upper.startswith("UNIQUE"):
            start = text.find("(")
            end = text.rfind(")")
            if start != -1 and end != -1 and end > start:
                return split_sql_columns(text[start + 1 : end])

        if upper.startswith("CONSTRAINT") and "UNIQUE" in upper:
            unique_pos = upper.find("UNIQUE")
            sub = text[unique_pos:]
            start = sub.find("(")
            end = sub.rfind(")")
            if start != -1 and end != -1 and end > start:
                return split_sql_columns(sub[start + 1 : end])

        return None

    def _parse_alter_table_fks(self, schema_sql: str) -> List[Tuple[str, ForeignKeyProfile]]:
        out: List[Tuple[str, ForeignKeyProfile]] = []
        for m in ALTER_TABLE_FK_RE.finditer(schema_sql or ""):
            table = m.group("table")
            cols = split_sql_columns(m.group("cols"))
            ref_table = m.group("ref_table")
            ref_cols = split_sql_columns(m.group("ref_cols"))

            out.append(
                (
                    table,
                    ForeignKeyProfile(
                        columns=cols,
                        referenced_table=ref_table,
                        referenced_columns=ref_cols,
                    ),
                )
            )
        return out

    def _dedup_foreign_keys(self, fks: List[ForeignKeyProfile]) -> List[ForeignKeyProfile]:
        seen = set()
        out: List[ForeignKeyProfile] = []
        for fk in fks:
            key = (
                tuple(fk.columns),
                fk.referenced_table,
                tuple(fk.referenced_columns),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(fk)
        return out

    def _dedup_unique_constraints(self, constraints: List[List[str]]) -> List[List[str]]:
        seen = set()
        out: List[List[str]] = []
        for cols in constraints:
            key = tuple(cols)
            if key in seen:
                continue
            seen.add(key)
            out.append(cols)
        return out

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def profile(self, schema_sql: str) -> Dict[str, Any]:
        tables: Dict[str, TableProfile] = {}

        # --------------------------------------------
        # Pass 1: parse CREATE TABLE blocks
        # --------------------------------------------
        for table_name, body in CREATE_TABLE_RE.findall(schema_sql or ""):
            tp = TableProfile(
                name=table_name,
                raw_sql_body=body,
            )

            items = self._split_body_items(body)

            for item in items:
                col = self._parse_column_def(item)
                if col is not None:
                    tp.columns.append(col)

                    upper = item.upper()
                    if col.is_primary_key and col.name not in tp.primary_key:
                        tp.primary_key.append(col.name)

                    unique_cols = self._parse_unique_constraint(item)
                    if unique_cols:
                        tp.unique_constraints.append(unique_cols)

                fk = self._parse_inline_fk_from_item(item)
                if fk is not None:
                    tp.foreign_keys.append(fk)

                pk_match = PRIMARY_KEY_RE.search(item)
                if pk_match:
                    tp.primary_key = split_sql_columns(pk_match.group(1))

            tables[table_name] = tp

        # --------------------------------------------
        # Pass 2: parse ALTER TABLE ... FOREIGN KEY ...
        # --------------------------------------------
        for table_name, fk in self._parse_alter_table_fks(schema_sql or ""):
            if table_name not in tables:
                tables[table_name] = TableProfile(name=table_name)
            tables[table_name].foreign_keys.append(fk)

        # --------------------------------------------
        # Dedup and normalize
        # --------------------------------------------
        for tp in tables.values():
            tp.foreign_keys = self._dedup_foreign_keys(tp.foreign_keys)
            tp.unique_constraints = self._dedup_unique_constraints(tp.unique_constraints)

        # --------------------------------------------
        # Build join graph
        # --------------------------------------------
        join_graph: Dict[str, List[Dict[str, Any]]] = {}
        for table_name, tp in tables.items():
            edges: List[Dict[str, Any]] = []

            for fk in tp.foreign_keys:
                pairs = list(zip(fk.columns, fk.referenced_columns))
                joins = [
                    [f"{table_name}.{src}", "=", f"{fk.referenced_table}.{dst}"]
                    for src, dst in pairs
                ]
                edges.append(
                    {
                        "to_table": fk.referenced_table,
                        "from_columns": list(fk.columns),
                        "to_columns": list(fk.referenced_columns),
                        "joins": joins,
                    }
                )

            join_graph[table_name] = edges

        # --------------------------------------------
        # Stats
        # --------------------------------------------
        num_columns = sum(len(tp.columns) for tp in tables.values())
        num_foreign_keys = sum(len(tp.foreign_keys) for tp in tables.values())

        return {
            "tables": {
                name: {
                    "name": tp.name,
                    "columns": [
                        {
                            "name": c.name,
                            "sql_type": c.sql_type,
                            "is_nullable": c.is_nullable,
                            "is_primary_key": c.is_primary_key,
                            "raw_sql": c.raw_sql,
                        }
                        for c in tp.columns
                    ],
                    "primary_key": list(tp.primary_key),
                    "foreign_keys": [
                        {
                            "columns": list(fk.columns),
                            "referenced_table": fk.referenced_table,
                            "referenced_columns": list(fk.referenced_columns),
                        }
                        for fk in tp.foreign_keys
                    ],
                    "unique_constraints": [list(x) for x in tp.unique_constraints],
                    "raw_sql_body": tp.raw_sql_body,
                }
                for name, tp in tables.items()
            },
            "join_graph": join_graph,
            "stats": {
                "num_tables": len(tables),
                "num_columns": num_columns,
                "num_foreign_keys": num_foreign_keys,
            },
        }