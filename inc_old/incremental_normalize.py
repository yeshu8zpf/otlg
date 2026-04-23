
from __future__ import annotations

"""
incremental_normalize.py

Robust normalization utilities for the table-centric incremental pipeline.

Why this file exists
--------------------
The original project already has a strong normalization package for one-shot
outputs. The incremental pipeline, however, was still relying mostly on:
- prompt constraints
- light JSON shape normalization
- compare-side preprocess

This module fills that gap by adding:
1. patch-level normalization
2. internal-draft-level normalization
3. column/join qualification with table context

Design goals
------------
- Reuse the existing normalization package where possible.
- Preserve the current incremental internal draft shape.
- Guarantee internal invariants earlier, especially:
  * source_columns / identifier_columns / bnode_id_columns use table.column
  * join_paths are normalized
  * class/property ids are canonicalized
"""

from typing import Any, Dict, List, Optional, Set
import copy

from normalization.canonicalizers import (
    canonicalize_class,
    canonicalize_class_mapping,
    canonicalize_data_property,
    canonicalize_data_property_mapping,
    canonicalize_object_property,
    canonicalize_object_property_mapping,
    canonicalize_subclass_relation,
)
from normalization.helpers import (
    as_list,
    normalize_class_id,
    normalize_identifier,
    normalize_join_list,
    normalize_property_id,
    normalize_range_type,
    normalize_ws,
)


# ============================================================
# context helpers
# ============================================================

def build_known_tables(incremental_step: Optional[Dict[str, Any]] = None, draft: Optional[Dict[str, Any]] = None) -> Set[str]:
    tables: Set[str] = set()

    if incremental_step:
        new_table = incremental_step.get("new_table")
        if new_table:
            tables.add(str(new_table).lower())

        for t in incremental_step.get("related_existing_tables", []) or []:
            tables.add(str(t).lower())

        local_table = incremental_step.get("local_table", {}) or {}
        if local_table.get("name"):
            tables.add(str(local_table["name"]).lower())

        for t in (incremental_step.get("suggested_analysis_scope", {}) or {}).get(
            "recommended_tables_for_joint_analysis", []
        ) or []:
            tables.add(str(t).lower())

        related_defs = incremental_step.get("related_table_defs", {}) or {}
        for t in related_defs.keys():
            tables.add(str(t).lower())

    if draft:
        for field in ["classes", "class_mappings", "data_property_mappings", "object_property_mappings"]:
            for x in draft.get(field, []) or []:
                for t in x.get("source_tables", []) or []:
                    tables.add(str(t).lower())
                for t in x.get("from_tables", []) or []:
                    tables.add(str(t).lower())
                st = x.get("source_table")
                if st:
                    tables.add(str(st).lower())

    return {t for t in tables if t}


def default_table_hint(incremental_step: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if not incremental_step:
        return None
    local_table = incremental_step.get("local_table", {}) or {}
    if local_table.get("name"):
        return str(local_table["name"]).lower()
    if incremental_step.get("new_table"):
        return str(incremental_step["new_table"]).lower()
    return None


# ============================================================
# qualification helpers
# ============================================================

def _is_qualified_column(s: str) -> bool:
    s = str(s or "").strip()
    return "." in s and len(s.split(".", 1)[0]) > 0 and len(s.split(".", 1)[1]) > 0


def qualify_column(col: Any, *, table_hint: Optional[str], known_tables: Set[str]) -> str:
    s = normalize_identifier(col)
    if not s:
        return ""

    if _is_qualified_column(s):
        left, right = s.split(".", 1)
        return f"{left.lower()}.{right.lower()}"

    if table_hint:
        return f"{table_hint.lower()}.{s.lower()}"

    # last-resort fallback: leave as-is, but lowercased.
    # Better to preserve than invent wrong table silently.
    return s.lower()


def qualify_column_list(cols: Any, *, table_hint: Optional[str], known_tables: Set[str]) -> List[str]:
    out: List[str] = []
    for c in as_list(cols):
        qc = qualify_column(c, table_hint=table_hint, known_tables=known_tables)
        if qc:
            out.append(qc)
    # dedupe preserving order
    return list(dict.fromkeys(out))


def normalize_join_paths_scoped(
    joins: Any,
    *,
    default_table_hint: Optional[str],
    known_tables: Set[str],
) -> List[List[str]]:
    normalized = normalize_join_list(joins)
    out: List[List[str]] = []

    for j in normalized:
        if len(j) == 3:
            left, op, right = j
            left_q = qualify_column(left, table_hint=default_table_hint, known_tables=known_tables)
            right_q = qualify_column(right, table_hint=default_table_hint, known_tables=known_tables)
            out.append([left_q, op, right_q])
        else:
            out.append([normalize_identifier(x) for x in j if normalize_identifier(x)])

    return out


def infer_source_table(source_table: Any, source_columns: List[str], fallback_table_hint: Optional[str]) -> str:
    st = normalize_identifier(source_table)
    if st:
        return st.lower()
    for c in source_columns:
        if _is_qualified_column(c):
            return c.split(".", 1)[0].lower()
    return (fallback_table_hint or "").lower()


# ============================================================
# section-level normalization
# ============================================================

def normalize_class_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    c = canonicalize_class(x)

    source_tables = [str(t).lower() for t in c.get("source_tables", [])]
    identifier_columns = qualify_column_list(
        c.get("identifier_columns", []),
        table_hint=(source_tables[0] if source_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    out: Dict[str, Any] = {
        "id": c.get("id", ""),
        "label": c.get("label") or c.get("id", ""),
        "status": c.get("status", "proposed"),
        "confidence": c.get("confidence", 0.5),
        "source_tables": source_tables,
        "identifier_columns": identifier_columns,
    }

    if c.get("instance_id_template"):
        out["instance_id_template"] = c["instance_id_template"]
    if c.get("bnode_id_columns"):
        out["bnode_id_columns"] = qualify_column_list(
            c.get("bnode_id_columns", []),
            table_hint=(source_tables[0] if source_tables else default_table_hint(incremental_step)),
            known_tables=known_tables,
        )
    if c.get("condition"):
        out["condition"] = normalize_join_paths_scoped(
            c["condition"],
            default_table_hint=(source_tables[0] if source_tables else default_table_hint(incremental_step)),
            known_tables=known_tables,
        )
    if c.get("join_paths"):
        out["join_paths"] = normalize_join_paths_scoped(
            c["join_paths"],
            default_table_hint=(source_tables[0] if source_tables else default_table_hint(incremental_step)),
            known_tables=known_tables,
        )
    if c.get("subclass_of"):
        out["subclass_of"] = [normalize_class_id(v) for v in c.get("subclass_of", []) if normalize_class_id(v)]
    if c.get("translate_with"):
        out["translate_with"] = c["translate_with"]
    if c.get("mapping_id"):
        out["mapping_id"] = c["mapping_id"]
    if c.get("extras"):
        out["extras"] = c["extras"]
    if x.get("description"):
        out["description"] = normalize_ws(x.get("description"))
    return out


def normalize_data_property_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    p = canonicalize_data_property(x)

    source_columns = qualify_column_list(
        p.get("source_columns", []),
        table_hint=default_table_hint(incremental_step),
        known_tables=known_tables,
    )
    source_tables = sorted({c.split(".", 1)[0] for c in source_columns if _is_qualified_column(c)})

    out: Dict[str, Any] = {
        "id": p.get("id", ""),
        "label": p.get("label") or p.get("id", ""),
        "domain": p.get("domain_class", ""),
        "datatype": x.get("datatype") or _datatype_from_range_type(p.get("range_type")),
        "status": p.get("status", "proposed"),
        "confidence": p.get("confidence", 0.5),
        "source_tables": source_tables,
        "source_columns": source_columns,
    }

    if p.get("join_paths"):
        out["join_paths"] = normalize_join_paths_scoped(
            p["join_paths"],
            default_table_hint=(source_tables[0] if source_tables else default_table_hint(incremental_step)),
            known_tables=known_tables,
        )
    for key in ["uri_column", "pattern", "uri_pattern", "sql_expression", "constant_value", "condition", "translate_with", "mapping_id"]:
        if p.get(key):
            out[key] = p[key]
    if "description" in x and x.get("description"):
        out["description"] = normalize_ws(x["description"])
    return out


def normalize_object_property_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    p = canonicalize_object_property(x)
    out: Dict[str, Any] = {
        "id": p.get("id", ""),
        "label": p.get("label") or p.get("id", ""),
        "domain": p.get("domain_class", ""),
        "range": p.get("range_class", ""),
        "status": p.get("status", "proposed"),
        "confidence": p.get("confidence", 0.5),
        "source_tables": [str(t).lower() for t in x.get("source_tables", [])] if x.get("source_tables") else [],
    }
    if p.get("join_paths"):
        out["join_paths"] = normalize_join_paths_scoped(
            p["join_paths"],
            default_table_hint=default_table_hint(incremental_step),
            known_tables=known_tables,
        )
    for key in ["dynamic_property", "condition", "translate_with", "mapping_id"]:
        if p.get(key):
            out[key] = p[key]
    if "description" in x and x.get("description"):
        out["description"] = normalize_ws(x["description"])
    return out


def normalize_subclass_relation_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rel = canonicalize_subclass_relation(x)
    out = {
        "id": rel.get("id", ""),
        "child_class": rel.get("child_class", ""),
        "parent_class": rel.get("parent_class", ""),
    }
    if rel.get("confidence") is not None:
        out["confidence"] = rel["confidence"]
    if rel.get("status"):
        out["status"] = rel["status"]
    return out


def normalize_class_mapping_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    m = canonicalize_class_mapping(x)

    from_tables = [str(t).lower() for t in m.get("from_tables", [])]
    fallback = from_tables[0] if from_tables else default_table_hint(incremental_step)
    identifier_columns = qualify_column_list(m.get("identifier_columns", []), table_hint=fallback, known_tables=known_tables)

    out: Dict[str, Any] = {
        "class_id": m.get("class_id", ""),
        "from_tables": from_tables,
        "identifier_columns": identifier_columns,
        "instance_id_template": m.get("instance_id_template", ""),
        "status": m.get("status", "proposed"),
        "confidence": m.get("confidence", 0.5),
    }

    if m.get("identifier_kind"):
        out["identifier_kind"] = m["identifier_kind"]
    if m.get("bnode_id_columns"):
        out["bnode_id_columns"] = qualify_column_list(
            m["bnode_id_columns"], table_hint=fallback, known_tables=known_tables
        )
    if m.get("condition"):
        out["condition"] = normalize_join_paths_scoped(m["condition"], default_table_hint=fallback, known_tables=known_tables)
    if m.get("join_paths"):
        out["join_paths"] = normalize_join_paths_scoped(m["join_paths"], default_table_hint=fallback, known_tables=known_tables)
    if m.get("subclass_of"):
        out["subclass_of"] = [normalize_class_id(v) for v in m["subclass_of"] if normalize_class_id(v)]
    if m.get("translate_with"):
        out["translate_with"] = m["translate_with"]
    if m.get("mapping_id"):
        out["mapping_id"] = m["mapping_id"]
    if m.get("additional_class_definition_property"):
        out["additional_class_definition_property"] = m["additional_class_definition_property"]
    if m.get("extras"):
        out["extras"] = m["extras"]
    return out


def normalize_data_property_mapping_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    m = canonicalize_data_property_mapping(x)

    fallback = normalize_identifier(m.get("source_table")) or default_table_hint(incremental_step)
    source_columns = qualify_column_list(m.get("source_columns", []), table_hint=fallback, known_tables=known_tables)
    source_table = infer_source_table(m.get("source_table"), source_columns, fallback)

    out: Dict[str, Any] = {
        "data_property_id": m.get("property_id", ""),
        "applies_to_class": m.get("from_class", ""),
        "source_table": source_table,
        "source_columns": source_columns,
        "join_paths": normalize_join_paths_scoped(m.get("joins", []), default_table_hint=source_table, known_tables=known_tables),
        "status": m.get("status", "proposed"),
        "confidence": m.get("confidence", 0.5),
    }

    # normalize value representation
    value_kind = (m.get("value_kind") or "").lower().strip()
    if value_kind:
        out["value_kind"] = value_kind

    if value_kind == "column":
        col = m.get("column") or (source_columns[0] if source_columns else "")
        if col:
            out["source_columns"] = qualify_column_list([col], table_hint=source_table, known_tables=known_tables)
            out["source_table"] = infer_source_table(source_table, out["source_columns"], source_table)
            out["value_kind"] = "column"

    elif value_kind == "uri_column":
        uri_cols = m.get("uri_column") or source_columns
        out["source_columns"] = qualify_column_list(uri_cols, table_hint=source_table, known_tables=known_tables)
        out["source_table"] = infer_source_table(source_table, out["source_columns"], source_table)
        out["value_kind"] = "uri_column"

    elif value_kind == "pattern":
        out["value_template"] = m.get("pattern", "")

    elif value_kind == "uri_pattern":
        out["value_template"] = m.get("uri_pattern", "")

    elif value_kind == "sql_expression":
        out["sql_expression"] = m.get("sql_expression", "")

    elif value_kind == "constant":
        out["constant_value"] = m.get("constant_value")

    else:
        # fallback inference
        if m.get("uri_column"):
            out["value_kind"] = "uri_column"
            out["source_columns"] = qualify_column_list(m.get("uri_column"), table_hint=source_table, known_tables=known_tables)
        elif m.get("uri_pattern"):
            out["value_kind"] = "uri_pattern"
            out["value_template"] = m.get("uri_pattern", "")
        elif m.get("pattern"):
            out["value_kind"] = "pattern"
            out["value_template"] = m.get("pattern", "")
        elif m.get("sql_expression"):
            out["value_kind"] = "sql_expression"
            out["sql_expression"] = m.get("sql_expression", "")
        elif m.get("constant_value") is not None:
            out["value_kind"] = "constant"
            out["constant_value"] = m.get("constant_value")
        else:
            out["value_kind"] = "column"
            if source_columns:
                out["source_columns"] = source_columns

    if m.get("datatype"):
        out["datatype"] = normalize_range_type(m.get("datatype"))
    if m.get("condition"):
        out["condition"] = normalize_join_paths_scoped(m["condition"], default_table_hint=source_table, known_tables=known_tables)
    if m.get("translate_with"):
        out["translate_with"] = m["translate_with"]
    if m.get("mapping_id"):
        out["mapping_id"] = m["mapping_id"]
    return out


def normalize_object_property_mapping_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    m = canonicalize_object_property_mapping(x)

    out: Dict[str, Any] = {
        "object_property_id": m.get("property_id", ""),
        "from_class": m.get("from_class", ""),
        "to_class": m.get("to_class", ""),
        "join_paths": normalize_join_paths_scoped(m.get("joins", []), default_table_hint=default_table_hint(incremental_step), known_tables=known_tables),
        "status": m.get("status", "proposed"),
        "confidence": m.get("confidence", 0.5),
    }
    if x.get("from_tables"):
        out["from_tables"] = [str(t).lower() for t in x.get("from_tables", [])]
    if x.get("source_identifier_columns"):
        out["source_identifier_columns"] = qualify_column_list(
            x.get("source_identifier_columns", []),
            table_hint=default_table_hint(incremental_step),
            known_tables=known_tables,
        )
    if x.get("target_identifier_columns"):
        out["target_identifier_columns"] = qualify_column_list(
            x.get("target_identifier_columns", []),
            table_hint=default_table_hint(incremental_step),
            known_tables=known_tables,
        )
    if m.get("dynamic_property"):
        out["dynamic_property"] = m["dynamic_property"]
    if m.get("condition"):
        out["condition"] = normalize_join_paths_scoped(m["condition"], default_table_hint=default_table_hint(incremental_step), known_tables=known_tables)
    if m.get("translate_with"):
        out["translate_with"] = m["translate_with"]
    if m.get("mapping_id"):
        out["mapping_id"] = m["mapping_id"]
    return out


# ============================================================
# patch normalization
# ============================================================

PATCH_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]


def normalize_patch_robust(raw_patch: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "work_unit": raw_patch.get("work_unit", {}),
        "proposed_additions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_revisions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_rejections": list(raw_patch.get("proposed_rejections", []) or []),
        "proposed_merges": list(raw_patch.get("proposed_merges", []) or []),
        "decision_summary": _normalize_decision_summary(raw_patch.get("decision_summary", [])),
        "remaining_ambiguities": [str(x).strip() for x in raw_patch.get("remaining_ambiguities", []) or [] if str(x).strip()],
        "needs_probe": list(raw_patch.get("needs_probe", []) or []),
    }

    additions = raw_patch.get("proposed_additions", {}) or {}
    for field in PATCH_SECTION_FIELDS:
        for item in additions.get(field, []) or []:
            norm = _normalize_section_item(field, item, incremental_step=incremental_step)
            if norm:
                out["proposed_additions"][field].append(norm)

    revisions = raw_patch.get("proposed_revisions", {}) or {}
    if isinstance(revisions, dict):
        for field in PATCH_SECTION_FIELDS:
            for item in revisions.get(field, []) or []:
                target_id = item.get("target_id")
                updated_fields = item.get("updated_fields", {}) or {}
                norm_updated = _normalize_revision_payload(field, updated_fields, incremental_step=incremental_step)
                if target_id and norm_updated:
                    out["proposed_revisions"][field].append(
                        {
                            "target_id": str(target_id),
                            "updated_fields": norm_updated,
                        }
                    )
    elif isinstance(revisions, list):
        # 兼容模型输出 proposed_revisions=[] 的情况
        pass

    return out

def _class_id_from_patch_name(name: str) -> str:
    name = normalize_identifier(name)
    if not name:
        return ""
    if name.startswith("Class:"):
        return name
    return f"Class:{name}"


def _class_id_from_class_mapping_name(name: str) -> str:
    """
    Example:
      Conference_from_conferences -> Class:Conference
      Class:Conference_from_conferences -> Class:Conference
    """
    name = str(name or "").strip()
    if not name:
        return ""
    prefix = name.split("_from_", 1)[0]
    return _class_id_from_patch_name(prefix)


def _normalize_identity_kind(raw: str) -> str:
    raw = normalize_identifier(raw).lower()
    mapping = {
        "uripattern": "uri_pattern",
        "uri_pattern": "uri_pattern",
        "uricolumn": "uri_column",
        "uri_column": "uri_column",
        "bnodeidcolumns": "bnode",
        "bnode_id_columns": "bnode",
        "bnode": "bnode",
    }
    return mapping.get(raw, raw)


def _normalize_patch_class_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    source_table = normalize_identifier(item.get("source_table")).lower()
    ontology_class = _class_id_from_patch_name(item.get("ontology_class"))

    identity = item.get("identity", {}) or {}
    identity_type = _normalize_identity_kind(identity.get("type"))
    raw_cols = identity.get("columns", []) or []
    identifier_columns = qualify_column_list(
        raw_cols,
        table_hint=source_table,
        known_tables=known_tables,
    )

    out: Dict[str, Any] = {
        "class_id": ontology_class,
        "from_tables": [source_table] if source_table else [],
        "identifier_columns": identifier_columns,
        "instance_id_template": "",
        "status": item.get("status", "proposed"),
        "confidence": item.get("confidence"),
        "mapping_id": item.get("id"),
        "identifier_kind": identity_type,
    }

    if identity_type == "uri_pattern":
        out["instance_id_template"] = identity.get("pattern", "") or ""
    elif identity_type == "uri_column":
        # raw patch may store URI column under identity.columns
        pass
    elif identity_type == "bnode":
        out["bnode_id_columns"] = identifier_columns

    return out


def _normalize_patch_data_property_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)

    source_table = normalize_identifier(item.get("source_table")).lower()
    source_column = item.get("source_column")
    source_columns = qualify_column_list(
        [source_column] if source_column else [],
        table_hint=source_table,
        known_tables=known_tables,
    )

    ontology_property = normalize_identifier(item.get("ontology_property"))
    data_property_id = (
        ontology_property
        if ontology_property.startswith("DataProperty:")
        else f"DataProperty:{ontology_property}"
    )

    class_mapping_name = item.get("class_mapping", "")
    applies_to_class = _class_id_from_class_mapping_name(class_mapping_name)

    out: Dict[str, Any] = {
        "data_property_id": data_property_id,
        "applies_to_class": applies_to_class,
        "source_table": source_table,
        "source_columns": source_columns,
        "join_paths": [],
        "status": item.get("status", "proposed"),
        "confidence": item.get("confidence"),
        "value_kind": "column",
        "mapping_id": item.get("id"),
    }

    # Optional direct datatype hint from raw patch
    if item.get("datatype"):
        out["datatype"] = normalize_range_type(item.get("datatype"))

    return out


def _normalize_patch_object_property_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)

    source_table = normalize_identifier(item.get("source_table")).lower()
    source_column = item.get("source_column")
    source_columns = qualify_column_list(
        [source_column] if source_column else [],
        table_hint=source_table,
        known_tables=known_tables,
    )

    ontology_property = normalize_identifier(item.get("ontology_property"))
    object_property_id = (
        ontology_property
        if ontology_property.startswith("ObjectProperty:")
        else f"ObjectProperty:{ontology_property}"
    )

    class_mapping_name = item.get("class_mapping", "")
    from_class = _class_id_from_class_mapping_name(class_mapping_name)

    out: Dict[str, Any] = {
        "object_property_id": object_property_id,
        "from_class": from_class,
        "to_class": "",
        "join_paths": [],
        "status": item.get("status", "proposed"),
        "confidence": item.get("confidence"),
        "mapping_id": item.get("id"),
    }

    if source_table:
        out["from_tables"] = [source_table]

    # Raw patch special case:
    # target_type=resource means this is not a normal entity-to-entity relation,
    # but a resource-valued mapping hint carried forward for later export logic.
    target_type = normalize_identifier(item.get("target_type")).lower()
    if target_type == "resource":
        out["target_type"] = "resource"
        out["source_table"] = source_table
        out["source_columns"] = source_columns
        return out

    # If raw patch explicitly gives target class info, keep it
    if item.get("target_class"):
        out["to_class"] = _class_id_from_patch_name(item.get("target_class"))

    # Optional raw joins
    if item.get("joins"):
        out["join_paths"] = normalize_join_paths_scoped(
            item.get("joins"),
            default_table_hint=source_table,
            known_tables=known_tables,
        )

    if item.get("condition"):
        out["condition"] = normalize_join_paths_scoped(
            item.get("condition"),
            default_table_hint=source_table,
            known_tables=known_tables,
        )

    print("[DEBUG raw opm item]", item)
    print("[DEBUG ontology_property]", item.get("ontology_property"))
    print("[DEBUG class_mapping]", item.get("class_mapping"))
    print("[DEBUG source_column]", item.get("source_column"))
    print("[DEBUG normalized opm]", out)
    return out
def _normalize_section_item(field: str, item: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if field == "class_mappings":
        if "ontology_class" in item or "identity" in item or "source_table" in item:
            return _normalize_patch_class_mapping(item, incremental_step=incremental_step)
        return normalize_class_mapping_item(item, incremental_step=incremental_step)

    if field == "data_property_mappings":
        if "ontology_property" in item or "source_column" in item or "class_mapping" in item:
            return _normalize_patch_data_property_mapping(item, incremental_step=incremental_step)
        return normalize_data_property_mapping_item(item, incremental_step=incremental_step)

    if field == "object_property_mappings":
        if "ontology_property" in item or "source_column" in item or "class_mapping" in item or "target_type" in item:
            return _normalize_patch_object_property_mapping(item, incremental_step=incremental_step)
        return normalize_object_property_mapping_item(item, incremental_step=incremental_step)

    if field == "classes":
        return normalize_class_item(item, incremental_step=incremental_step)
    if field == "data_properties":
        return normalize_data_property_item(item, incremental_step=incremental_step)
    if field == "object_properties":
        return normalize_object_property_item(item, incremental_step=incremental_step)
    if field == "subclass_relations":
        return normalize_subclass_relation_item(item, incremental_step=incremental_step)

    return item


def _normalize_revision_payload(field: str, payload: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    # Revisions are partial updates. We normalize only the fields that are present.
    known_tables = build_known_tables(incremental_step)
    default_table = default_table_hint(incremental_step)
    out = copy.deepcopy(payload)

    # Generic join/condition normalization
    for key in ["join_paths", "joins", "join", "condition"]:
        if key in out:
            out[key] = normalize_join_paths_scoped(out[key], default_table_hint=default_table, known_tables=known_tables)

    # Generic column lists
    for key in ["identifier_columns", "bnode_id_columns", "source_columns", "source_identifier_columns", "target_identifier_columns"]:
        if key in out:
            out[key] = qualify_column_list(out[key], table_hint=default_table, known_tables=known_tables)

    if "source_table" in out and out["source_table"]:
        out["source_table"] = normalize_identifier(out["source_table"]).lower()

    if "class_id" in out:
        out["class_id"] = normalize_class_id(out["class_id"])
    if "from_class" in out and out["from_class"]:
        out["from_class"] = normalize_class_id(out["from_class"])
    if "to_class" in out and out["to_class"]:
        out["to_class"] = normalize_class_id(out["to_class"])
    if "applies_to_class" in out and out["applies_to_class"]:
        out["applies_to_class"] = normalize_class_id(out["applies_to_class"])

    if "data_property_id" in out and out["data_property_id"]:
        out["data_property_id"] = normalize_property_id(out["data_property_id"], "DataProperty")
    if "object_property_id" in out and out["object_property_id"]:
        out["object_property_id"] = normalize_property_id(out["object_property_id"], "ObjectProperty")
    if "datatype" in out and out["datatype"]:
        out["datatype"] = normalize_range_type(out["datatype"])

    return out


def _normalize_decision_summary(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for x in items or []:
        decision_type = normalize_identifier(x.get("decision_type"))
        status = normalize_identifier(x.get("status")).lower()
        reason = normalize_ws(x.get("reason"))
        target = normalize_identifier(x.get("target") or x.get("target_id"))
        try:
            confidence = float(x.get("confidence", 0.5))
        except Exception:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        out.append(
            {
                "decision_type": decision_type,
                "target": target,
                "status": status if status in {"accepted", "rejected", "needs_probe", "proposed"} else "proposed",
                "confidence": confidence,
                "reason": reason,
            }
        )
    return out


# ============================================================
# internal draft normalization
# ============================================================

def normalize_internal_draft_robust(draft: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "draft_metadata": copy.deepcopy(draft.get("draft_metadata", {})),
        "rejected_candidates": copy.deepcopy(draft.get("rejected_candidates", [])),
        "open_issues": copy.deepcopy(draft.get("open_issues", [])),
    }

    for field in PATCH_SECTION_FIELDS:
        normalized_items = []
        seen = set()
        for item in draft.get(field, []) or []:
            norm = _normalize_section_item(field, item, incremental_step=incremental_step)
            if not norm:
                continue
            key = _draft_item_key(field, norm)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            normalized_items.append(norm)
        out[field] = normalized_items

    # normalize metadata
    meta = out["draft_metadata"]
    meta["draft_version"] = int(meta.get("draft_version", 0) or 0)
    meta["processed_tables"] = [str(x).lower() for x in meta.get("processed_tables", []) or [] if str(x).strip()]

    return out


def _draft_item_key(field: str, item: Dict[str, Any]) -> str:
    if field in {"classes", "data_properties", "object_properties"}:
        return str(item.get("id") or "")
    if field == "subclass_relations":
        return str(item.get("id") or f"{item.get('child_class')}->{item.get('parent_class')}")
    if field == "class_mappings":
        return str(item.get("mapping_id") or item.get("class_id") or "")
    if field == "data_property_mappings":
        return str(item.get("mapping_id") or item.get("data_property_id") or "")
    if field == "object_property_mappings":
        return str(item.get("mapping_id") or item.get("object_property_id") or "")
    return ""


def _datatype_from_range_type(range_type: Optional[str]) -> str:
    rt = (range_type or "string").lower()
    mapping = {
        "string": "xsd:string",
        "integer": "xsd:integer",
        "decimal": "xsd:decimal",
        "boolean": "xsd:boolean",
        "date": "xsd:date",
        "datetime": "xsd:dateTime",
    }
    return mapping.get(rt, "xsd:string")
