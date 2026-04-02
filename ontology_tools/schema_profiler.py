from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .common import CREATE_TABLE_RE, FK_INLINE_RE, PRIMARY_KEY_RE, split_sql_columns


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
        if upper.startswith("PRIMARY KEY") or upper.startswith("FOREIGN KEY") or upper.startswith("UNIQUE") or upper.startswith("CONSTRAINT"):
            return None

        parts = item.split()
        if not parts:
            return None
        name = parts[0]
        raw_type = parts[1] if len(parts) > 1 else ""

        nullable = None
        if "NOT NULL" in upper:
            nullable = False
        elif "NULL" in upper:
            nullable = True

        return ColumnProfile(name=name, raw_type=raw_type, nullable=nullable)

    def profile(self, schema_sql_text: str) -> Dict[str, Any]:
        tables: List[TableProfile] = []

        for table_name, body in CREATE_TABLE_RE.findall(schema_sql_text):
            table = TableProfile(name=table_name, raw_sql_body=body.strip())
            items = self._split_body_items(body)

            for item in items:
                col = self._parse_column_def(item)
                if col is not None:
                    table.columns.append(col)

                pk_match = PRIMARY_KEY_RE.search(item)
                if pk_match:
                    table.primary_key = split_sql_columns(pk_match.group(1))

                fk_match = FK_INLINE_RE.search(item)
                if fk_match:
                    columns = split_sql_columns(fk_match.group(1))
                    ref_table = fk_match.group(2).strip()
                    ref_columns = split_sql_columns(fk_match.group(3))
                    table.foreign_keys.append(
                        ForeignKeyProfile(columns=columns, ref_table=ref_table, ref_columns=ref_columns)
                    )

            col_idx = {c.name: c for c in table.columns}
            for c in table.primary_key:
                if c in col_idx:
                    col_idx[c].is_primary_key_part = True
            for fk in table.foreign_keys:
                for c in fk.columns:
                    if c in col_idx:
                        col_idx[c].is_foreign_key_part = True
                        col_idx[c].references = {
                            "table": fk.ref_table,
                            "columns": fk.ref_columns,
                        }

            tables.append(table)

        join_graph: Dict[str, List[Dict[str, Any]]] = {}
        for t in tables:
            join_graph[t.name] = []
        for t in tables:
            for fk in t.foreign_keys:
                join_graph[t.name].append(
                    {
                        "to_table": fk.ref_table,
                        "columns": fk.columns,
                        "ref_columns": fk.ref_columns,
                    }
                )

        return {
            "tables": [asdict(t) for t in tables],
            "join_graph": join_graph,
            "stats": {
                "num_tables": len(tables),
                "num_foreign_keys": sum(len(t.foreign_keys) for t in tables),
                "num_composite_primary_keys": sum(1 for t in tables if len(t.primary_key) > 1),
            },
        }
