
from __future__ import annotations

"""
schema_incremental.py

Extract incremental table-addition contexts from a relational schema SQL file.

Goal
----
Given only a schema.sql file, simulate an incremental schema arrival process:
tables are added one by one, and for each newly added table we output the local
context that should be considered when updating a global ontology draft.

This is designed for table-centric incremental ontology drafting.

Main features
-------------
1. Parse CREATE TABLE blocks from a schema SQL file.
2. Extract:
   - table order in the file
   - columns
   - primary keys
   - foreign keys
3. Build a schema graph.
4. For each incremental table addition step, produce:
   - local table definition
   - neighboring existing tables
   - relevant FK edges involving the new table
   - heuristic multi-table signals:
       * connector table
       * self-reference
       * multi-target / many-FK pattern
       * weak-entity / dependency pattern
       * possible association-class pattern
5. Export a JSON file for later prompt/context construction.

Usage
-----
python schema_incremental.py --schema /path/to/schema.sql --out /path/to/incremental_context.json

Optional:
python schema_incremental.py --schema /path/to/schema.sql --out /path/to/incremental_context.json --neighbor_hops 1
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import json
import re


# =========================
# Data structures
# =========================

@dataclass
class ColumnDef:
    name: str
    raw_type: str
    nullable: Optional[bool] = None
    is_primary_inline: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ForeignKeyDef:
    source_table: str
    source_columns: List[str]
    target_table: str
    target_columns: List[str]
    raw_sql: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TableDef:
    name: str
    create_sql: str
    columns: List[ColumnDef] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyDef] = field(default_factory=list)

    def column_names(self) -> List[str]:
        return [c.name for c in self.columns]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "create_sql": self.create_sql,
            "columns": [c.to_dict() for c in self.columns],
            "primary_key": self.primary_key,
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
        }


@dataclass
class IncrementalStep:
    step_index: int
    new_table: str
    schema_order_prefix: List[str]
    local_table: Dict[str, Any]
    related_existing_tables: List[str]
    related_table_defs: Dict[str, Dict[str, Any]]
    local_fk_edges: List[Dict[str, Any]]
    reverse_fk_edges: List[Dict[str, Any]]
    connected_component_tables: List[str]
    multi_table_signals: Dict[str, Any]
    suggested_analysis_scope: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =========================
# SQL parsing helpers
# =========================

CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+([`\"\[]?[\w]+[`\"\]]?(?:\.[`\"\[]?[\w]+[`\"\]]?)?)\s*\(",
    re.IGNORECASE | re.MULTILINE,
)

FK_RE = re.compile(
    r"FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([`\"\[]?[\w]+[`\"\]]?(?:\.[`\"\[]?[\w]+[`\"\]]?)?)\s*\((.*?)\)",
    re.IGNORECASE | re.DOTALL,
)

PK_RE = re.compile(
    r"PRIMARY\s+KEY\s*\((.*?)\)",
    re.IGNORECASE | re.DOTALL,
)


def normalize_ident(name: str) -> str:
    name = name.strip()
    if "." in name:
        parts = [p.strip().strip('`"[]') for p in name.split(".")]
        return parts[-1]
    return name.strip('`"[]')


def split_top_level_items(body: str) -> List[str]:
    items: List[str] = []
    cur: List[str] = []
    depth = 0
    in_single = False
    in_double = False

    for ch in body:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                item = "".join(cur).strip()
                if item:
                    items.append(item)
                cur = []
                continue
        cur.append(ch)

    tail = "".join(cur).strip()
    if tail:
        items.append(tail)
    return items


def extract_create_table_blocks(sql_text: str) -> List[Tuple[str, str, str]]:
    """
    Return list of (table_name, full_create_sql, body_sql) in file order.
    """
    matches = list(CREATE_TABLE_RE.finditer(sql_text))
    blocks: List[Tuple[str, str, str]] = []

    for i, m in enumerate(matches):
        table_name_raw = m.group(1)
        table_name = normalize_ident(table_name_raw)
        start = m.start()
        open_paren_idx = sql_text.find("(", m.start())
        if open_paren_idx == -1:
            continue

        depth = 0
        end_idx = None
        for j in range(open_paren_idx, len(sql_text)):
            ch = sql_text[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end_idx = j
                    break
        if end_idx is None:
            continue

        stmt_end = sql_text.find(";", end_idx)
        if stmt_end == -1:
            stmt_end = end_idx
        full_stmt = sql_text[start:stmt_end + 1].strip()
        body = sql_text[open_paren_idx + 1:end_idx].strip()
        blocks.append((table_name, full_stmt, body))

    return blocks


def parse_column_item(item: str) -> Optional[ColumnDef]:
    s = item.strip()
    upper = s.upper()
    if upper.startswith("PRIMARY KEY") or upper.startswith("FOREIGN KEY") or upper.startswith("CONSTRAINT") or upper.startswith("UNIQUE") or upper.startswith("KEY ") or upper.startswith("INDEX "):
        return None

    # Very lightweight parse: first token = column name, rest starts with type
    parts = s.split()
    if len(parts) < 2:
        return None

    col_name = normalize_ident(parts[0])
    # raw type = until constraint-like token
    constraint_tokens = {"NOT", "NULL", "PRIMARY", "REFERENCES", "UNIQUE", "CHECK", "DEFAULT", "CONSTRAINT"}
    type_tokens: List[str] = []
    for tok in parts[1:]:
        if tok.upper() in constraint_tokens:
            break
        type_tokens.append(tok)

    raw_type = " ".join(type_tokens) if type_tokens else parts[1]
    nullable = None
    if "NOT NULL" in upper:
        nullable = False
    elif re.search(r"\bNULL\b", upper):
        nullable = True

    is_primary_inline = "PRIMARY KEY" in upper

    return ColumnDef(
        name=col_name,
        raw_type=raw_type.strip(),
        nullable=nullable,
        is_primary_inline=is_primary_inline,
    )


def parse_table_block(table_name: str, full_sql: str, body_sql: str) -> TableDef:
    items = split_top_level_items(body_sql)
    columns: List[ColumnDef] = []
    primary_key: List[str] = []
    foreign_keys: List[ForeignKeyDef] = []

    for item in items:
        col = parse_column_item(item)
        if col is not None:
            columns.append(col)
            if col.is_primary_inline and col.name not in primary_key:
                primary_key.append(col.name)

    for item in items:
        item_stripped = item.strip()

        pk_match = PK_RE.search(item_stripped)
        if pk_match:
            cols = [normalize_ident(x) for x in pk_match.group(1).split(",")]
            for c in cols:
                if c not in primary_key:
                    primary_key.append(c)

        fk_match = FK_RE.search(item_stripped)
        if fk_match:
            source_cols = [normalize_ident(x) for x in fk_match.group(1).split(",")]
            target_table = normalize_ident(fk_match.group(2))
            target_cols = [normalize_ident(x) for x in fk_match.group(3).split(",")]
            foreign_keys.append(
                ForeignKeyDef(
                    source_table=table_name,
                    source_columns=source_cols,
                    target_table=target_table,
                    target_columns=target_cols,
                    raw_sql=item_stripped,
                )
            )

    return TableDef(
        name=table_name,
        create_sql=full_sql,
        columns=columns,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
    )


# =========================
# Graph and heuristics
# =========================

def build_reverse_fk_index(tables: Dict[str, TableDef]) -> Dict[str, List[ForeignKeyDef]]:
    reverse: Dict[str, List[ForeignKeyDef]] = {t: [] for t in tables}
    for table in tables.values():
        for fk in table.foreign_keys:
            reverse.setdefault(fk.target_table, []).append(fk)
    return reverse


def bfs_component(start: str, tables: Dict[str, TableDef], reverse_fks: Dict[str, List[ForeignKeyDef]], allowed_tables: Optional[set[str]] = None) -> List[str]:
    seen = set([start])
    queue = [start]

    while queue:
        cur = queue.pop(0)
        neighbors = set()

        for fk in tables[cur].foreign_keys:
            neighbors.add(fk.target_table)
        for rfk in reverse_fks.get(cur, []):
            neighbors.add(rfk.source_table)

        for nb in neighbors:
            if allowed_tables is not None and nb not in allowed_tables:
                continue
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)

    return sorted(seen)


def detect_connector_like(table: TableDef) -> Dict[str, Any]:
    fk_cols = set()
    for fk in table.foreign_keys:
        fk_cols.update(fk.source_columns)

    pk_set = set(table.primary_key)
    non_fk_cols = [c.name for c in table.columns if c.name not in fk_cols]
    payload_cols = [c for c in non_fk_cols if c not in pk_set]

    num_fk = len(table.foreign_keys)
    pk_mostly_fk = bool(pk_set) and len(pk_set.intersection(fk_cols)) >= max(1, len(pk_set) - 1)

    connector_like = num_fk >= 2
    association_likelihood = connector_like and len(payload_cols) > 0

    return {
        "connector_like": connector_like,
        "num_foreign_keys": num_fk,
        "fk_columns": sorted(fk_cols),
        "payload_columns": payload_cols,
        "pk_mostly_fk": pk_mostly_fk,
        "association_class_likelihood": association_likelihood,
    }


def detect_self_reference(table: TableDef) -> Dict[str, Any]:
    self_fks = [fk.to_dict() for fk in table.foreign_keys if fk.target_table == table.name]
    return {
        "self_referential": len(self_fks) > 0,
        "self_fk_edges": self_fks,
    }


def detect_multi_target_pattern(table: TableDef) -> Dict[str, Any]:
    # Heuristic: multiple FK-like columns to different semantic targets, or many FKs total.
    target_tables = [fk.target_table for fk in table.foreign_keys]
    unique_targets = sorted(set(target_tables))
    return {
        "many_fk_targets": len(unique_targets) >= 2,
        "target_tables": unique_targets,
    }


def detect_weak_entity_pattern(table: TableDef) -> Dict[str, Any]:
    fk_cols = set()
    for fk in table.foreign_keys:
        fk_cols.update(fk.source_columns)
    pk_set = set(table.primary_key)
    dependent_pk = bool(pk_set) and len(pk_set.intersection(fk_cols)) >= 1
    return {
        "weak_entity_like": dependent_pk and len(table.foreign_keys) >= 1,
        "pk_columns": table.primary_key,
    }


def detect_value_bundle_signals(table: TableDef) -> Dict[str, Any]:
    cols = {c.name.lower() for c in table.columns}
    address_bundle = sorted(cols.intersection({"address", "postcode", "country", "location", "city", "street"}))
    name_bundle = sorted(cols.intersection({"firstname", "lastname"}))
    geo_bundle = sorted(cols.intersection({"latitude", "longitude", "area", "elevation"}))
    return {
        "address_like_bundle": address_bundle if len(address_bundle) >= 2 else [],
        "name_like_bundle": name_bundle if len(name_bundle) >= 2 else [],
        "geo_scalar_bundle": geo_bundle if len(geo_bundle) >= 2 else [],
    }


def build_incremental_steps(tables_in_order: List[TableDef], neighbor_hops: int = 1) -> List[IncrementalStep]:
    table_map = {t.name: t for t in tables_in_order}
    reverse_fks = build_reverse_fk_index(table_map)

    steps: List[IncrementalStep] = []
    seen_tables: List[str] = []

    for idx, table in enumerate(tables_in_order):
        seen_tables.append(table.name)
        seen_set = set(seen_tables)

        local_fks = [fk.to_dict() for fk in table.foreign_keys if fk.target_table in seen_set]
        reverse_local_fks = [
            fk.to_dict() for fk in reverse_fks.get(table.name, [])
            if fk.source_table in seen_set and fk.source_table != table.name
        ]

        related_existing = sorted(
            {fk["target_table"] for fk in local_fks if fk["target_table"] != table.name}.union(
                {fk["source_table"] for fk in reverse_local_fks if fk["source_table"] != table.name}
            )
        )

        component_tables = bfs_component(
            start=table.name,
            tables=table_map,
            reverse_fks=reverse_fks,
            allowed_tables=seen_set,
        )

        related_table_defs = {
            tname: table_map[tname].to_dict()
            for tname in component_tables
            if tname != table.name
        }

        signals = {}
        signals.update(detect_connector_like(table))
        signals.update(detect_self_reference(table))
        signals.update(detect_multi_target_pattern(table))
        signals.update(detect_weak_entity_pattern(table))
        signals.update(detect_value_bundle_signals(table))
        signals["requires_multi_table_reasoning"] = (
            signals["connector_like"]
            or signals["self_referential"]
            or signals["many_fk_targets"]
            or len(related_existing) > 0
        )

        suggested_scope = {
            "local_only_ok": (
                not signals["requires_multi_table_reasoning"]
                and len(related_existing) == 0
            ),
            "recommended_tables_for_joint_analysis": sorted(set([table.name] + related_existing)),
            "recommended_component_tables": component_tables,
            "reason": _scope_reason(signals, related_existing),
        }

        steps.append(
            IncrementalStep(
                step_index=idx,
                new_table=table.name,
                schema_order_prefix=list(seen_tables),
                local_table=table.to_dict(),
                related_existing_tables=related_existing,
                related_table_defs=related_table_defs,
                local_fk_edges=local_fks,
                reverse_fk_edges=reverse_local_fks,
                connected_component_tables=component_tables,
                multi_table_signals=signals,
                suggested_analysis_scope=suggested_scope,
            )
        )

    return steps


def _scope_reason(signals: Dict[str, Any], related_existing: List[str]) -> List[str]:
    reasons: List[str] = []
    if signals.get("connector_like"):
        reasons.append("connector_like_table")
    if signals.get("association_class_likelihood"):
        reasons.append("possible_association_class")
    if signals.get("self_referential"):
        reasons.append("self_reference")
    if signals.get("many_fk_targets"):
        reasons.append("multi_target_or_multi_neighbor_pattern")
    if signals.get("weak_entity_like"):
        reasons.append("weak_entity_or_dependency_pattern")
    if signals.get("address_like_bundle"):
        reasons.append("structured_value_object_bundle")
    if len(related_existing) > 0:
        reasons.append("connected_to_existing_tables")
    if not reasons:
        reasons.append("local_table_may_be_analyzed_independently")
    return reasons


# =========================
# Public API
# =========================

def parse_schema_sql(schema_sql_text: str) -> List[TableDef]:
    blocks = extract_create_table_blocks(schema_sql_text)
    tables = [parse_table_block(name, full_sql, body) for name, full_sql, body in blocks]
    return tables


def build_incremental_context_from_schema_text(schema_sql_text: str, neighbor_hops: int = 1) -> Dict[str, Any]:
    tables = parse_schema_sql(schema_sql_text)
    steps = build_incremental_steps(tables, neighbor_hops=neighbor_hops)

    return {
        "num_tables": len(tables),
        "table_order": [t.name for t in tables],
        "tables": {t.name: t.to_dict() for t in tables},
        "incremental_steps": [s.to_dict() for s in steps],
    }


def build_incremental_context_from_schema_file(schema_path: Path, neighbor_hops: int = 1) -> Dict[str, Any]:
    text = schema_path.read_text(encoding="utf-8")
    return build_incremental_context_from_schema_text(text, neighbor_hops=neighbor_hops)


# =========================
# CLI
# =========================

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract incremental table-addition contexts from schema.sql")
    parser.add_argument("--schema", type=str, required=True, help="Path to schema.sql")
    parser.add_argument("--out", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--neighbor_hops", type=int, default=1, help="Reserved for future neighborhood expansion")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    out_path = Path(args.out)

    result = build_incremental_context_from_schema_file(schema_path, neighbor_hops=args.neighbor_hops)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] schema: {schema_path}")
    print(f"[OK] output: {out_path}")
    print(f"[OK] tables: {result['num_tables']}")


if __name__ == "__main__":
    main()
