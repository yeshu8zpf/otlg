from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .common import (
    ALTER_TABLE_FK_RE,
    CREATE_TABLE_RE,
    FK_INLINE_RE,
    PRIMARY_KEY_RE,
    split_sql_columns,
)


@dataclass
class ColumnProfile:
    name: str
    raw_type: str = ""
    nullable: Optional[bool] = None
    is_primary_key_part: bool = False
    is_foreign_key_part: bool = False
    references: Optional[Dict[str, Any]] = None


@dataclass
class ForeignKeyProfile:
    columns: List[str]
    ref_table: str
    ref_columns: List[str]


@dataclass
class TableProfile:
    name: str
    columns: List[ColumnProfile] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyProfile] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    raw_sql_body: str = ""


class SchemaProfiler:
    def _split_body_items(self, body: str) -> List[str]:
        items = []
        current = []
        depth = 0

        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1

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

    def _parse_alter_table_fks(self, schema_sql: str) -> List[tuple[str, ForeignKeyProfile]]:
        out: List[tuple[str, ForeignKeyProfile]] = []
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

    def profile(self, schema_sql: str) -> Dict[str, Any]:
        tables: Dict[str, TableProfile] = {}

        # First pass: CREATE TABLE blocks
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
                    if col.is_primary_key:
                        if col.name not in tp.primary_key:
                            tp.primary_key.append(col.name)

                    if "UNIQUE" in upper and col.name not in tp.primary_key:
                        tp.unique_constraints.append([col.name])

                fk = self._parse_inline_fk_from_item(item)
                if fk is not None:
                    tp.foreign_keys.append(fk)

                pk_match = PRIMARY_KEY_RE.search(item)
                if pk_match:
                    tp.primary_key = split_sql_columns(pk_match.group(1))

            tables[table_name] = tp

        # Second pass: ALTER TABLE ... FOREIGN KEY ...
        for table_name, fk in self._parse_alter_table_fks(schema_sql or ""):
            if table_name not in tables:
                tables[table_name] = TableProfile(name=table_name)
            tables[table_name].foreign_keys.append(fk)

        # Deduplicate FKs
        for tp in tables.values():
            tp.foreign_keys = self._dedup_foreign_keys(tp.foreign_keys)

        # Build join graph
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
                        "from_columns": fk.columns,
                        "to_columns": fk.referenced_columns,
                        "joins": joins,
                    }
                )
            join_graph[table_name] = edges

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
                    "primary_key": tp.primary_key,
                    "foreign_keys": [
                        {
                            "columns": fk.columns,
                            "referenced_table": fk.referenced_table,
                            "referenced_columns": fk.referenced_columns,
                        }
                        for fk in tp.foreign_keys
                    ],
                    "unique_constraints": tp.unique_constraints,
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