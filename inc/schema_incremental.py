from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import re


CREATE_TABLE_RE = re.compile(r"create\s+table\s+[`\"]?([a-zA-Z0-9_]+)[`\"]?\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)
FK_RE = re.compile(
    r"foreign\s+key\s*\((.*?)\)\s*references\s+[`\"]?([a-zA-Z0-9_]+)[`\"]?\s*\((.*?)\)",
    re.IGNORECASE | re.DOTALL,
)
PK_INLINE_RE = re.compile(r"primary\s+key", re.IGNORECASE)


def _split_sql_items(block: str) -> List[str]:
    items = []
    cur = []
    depth = 0
    for ch in block:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            item = "".join(cur).strip()
            if item:
                items.append(item)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        items.append(tail)
    return items


def _parse_columns_and_fks(table_name: str, block: str) -> Dict[str, Any]:
    columns: List[Dict[str, Any]] = []
    fks: List[Dict[str, Any]] = []
    pk_columns: List[str] = []

    items = _split_sql_items(block)
    for raw in items:
        s = raw.strip()

        fk_m = FK_RE.search(s)
        if fk_m:
            src_cols = [x.strip(" `\"") for x in fk_m.group(1).split(",")]
            target_table = fk_m.group(2).strip(" `\"")
            tgt_cols = [x.strip(" `\"") for x in fk_m.group(3).split(",")]
            fks.append({
                "source_table": table_name,
                "source_columns": src_cols,
                "target_table": target_table,
                "target_columns": tgt_cols,
            })
            continue

        lower = s.lower()
        if lower.startswith("primary key"):
            inner = s[s.find("(") + 1 : s.rfind(")")]
            pk_columns.extend([x.strip(" `\"") for x in inner.split(",") if x.strip()])
            continue

        parts = s.split()
        if not parts:
            continue
        col_name = parts[0].strip(" `\"")
        col_type = parts[1] if len(parts) > 1 else ""
        is_pk_inline = bool(PK_INLINE_RE.search(s))
        if is_pk_inline:
            pk_columns.append(col_name)

        columns.append({
            "name": col_name,
            "type": col_type,
            "raw": s,
            "is_primary_key": is_pk_inline,
        })

    for c in columns:
        if c["name"] in pk_columns:
            c["is_primary_key"] = True

    return {"columns": columns, "fks": fks}


def parse_schema_sql(schema_sql: str) -> Dict[str, Any]:
    tables: Dict[str, Any] = {}
    all_fks: List[Dict[str, Any]] = []

    for m in CREATE_TABLE_RE.finditer(schema_sql):
        table_name = m.group(1)
        body = m.group(2)
        parsed = _parse_columns_and_fks(table_name, body)
        tables[table_name] = {
            "name": table_name,
            "columns": parsed["columns"],
            "fks": parsed["fks"],
        }
        all_fks.extend(parsed["fks"])

    return {"tables": tables, "foreign_keys": all_fks}


def _related_existing_tables(table_name: str, all_fks: List[Dict[str, Any]]) -> List[str]:
    rel = []
    for fk in all_fks:
        if fk["source_table"] == table_name:
            rel.append(fk["target_table"])
        if fk["target_table"] == table_name:
            rel.append(fk["source_table"])
    return sorted(dict.fromkeys(rel))


def _local_fk_edges(table_name: str, all_fks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [fk for fk in all_fks if fk["source_table"] == table_name or fk["target_table"] == table_name]


def _signals_for_table(table_def: Dict[str, Any], related_tables: List[str]) -> Dict[str, Any]:
    col_names = [c["name"].lower() for c in table_def.get("columns", [])]
    fk_count = len(table_def.get("fks", []))
    many_fk_targets = fk_count >= 2
    connector_like = many_fk_targets and len(col_names) <= 4
    address_like_bundle = [x for x in ["address", "location", "postcode", "country"] if x in col_names]
    association_class_likelihood = connector_like and len(col_names) > fk_count
    requires_multi_table_reasoning = bool(related_tables) or connector_like or bool(address_like_bundle)

    return {
        "many_fk_targets": many_fk_targets,
        "connector_like": connector_like,
        "association_class_likelihood": association_class_likelihood,
        "address_like_bundle": address_like_bundle,
        "requires_multi_table_reasoning": requires_multi_table_reasoning,
    }


def build_incremental_context_from_schema_text(schema_sql: str) -> Dict[str, Any]:
    parsed = parse_schema_sql(schema_sql)
    tables = parsed["tables"]
    all_fks = parsed["foreign_keys"]

    steps = []
    table_names = list(tables.keys())

    for i, table_name in enumerate(table_names):
        local_table = tables[table_name]
        related = _related_existing_tables(table_name, all_fks)
        local_fk_edges = _local_fk_edges(table_name, all_fks)
        signals = _signals_for_table(local_table, related)

        recommended = [table_name] + related
        reasons = []
        if related:
            reasons.append("connected_to_existing_tables")
        if signals["connector_like"]:
            reasons.append("connector_like")
        if signals["address_like_bundle"]:
            reasons.append("structured_value_object_bundle")

        steps.append({
            "step_index": i,
            "new_table": table_name,
            "related_existing_tables": related,
            "local_table": local_table,
            "local_fk_edges": local_fk_edges,
            "related_table_defs": {t: tables[t] for t in related if t in tables},
            "multi_table_signals": signals,
            "suggested_analysis_scope": {
                "recommended_tables_for_joint_analysis": recommended,
                "reason": reasons,
            },
        })

    return {
        "tables": list(tables.keys()),
        "incremental_steps": steps,
    }


def build_incremental_context_from_schema_file(schema_path: str | Path) -> Dict[str, Any]:
    schema_path = Path(schema_path)
    schema_sql = schema_path.read_text(encoding="utf-8")
    return build_incremental_context_from_schema_text(schema_sql)
