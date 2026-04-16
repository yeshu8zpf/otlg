from __future__ import annotations

import copy
from typing import Any, Dict

from .helpers import build_index_by_id, normalize_join_list


def backfill_from_mappings(canonical: Dict[str, Any], collector) -> Dict[str, Any]:
    canonical = copy.deepcopy(canonical)

    classes = canonical["classes"]
    data_properties = canonical["data_properties"]
    object_properties = canonical["object_properties"]
    class_mappings = canonical["class_mappings"]
    data_property_mappings = canonical["data_property_mappings"]
    object_property_mappings = canonical["object_property_mappings"]

    class_idx = build_index_by_id(classes)
    dp_idx = build_index_by_id(data_properties)
    op_idx = build_index_by_id(object_properties)

    if not class_mappings:
        for c in classes:
            source_tables = c.get("source_tables") or []
            if not source_tables or not c.get("id"):
                continue
            identifier_columns = [str(x).strip() for x in (c.get("identifier_columns") or []) if str(x).strip()]
            class_mappings.append(
                {
                    "class_id": c["id"],
                    "from_tables": list(source_tables),
                    "identifier_columns": identifier_columns,
                    "instance_id_template": c.get("instance_id_template") or (
                        "{" + (identifier_columns[0] if identifier_columns else f"{source_tables[0]}.id") + "}"
                    ),
                    "status": c.get("status", "proposed"),
                    "confidence": c.get("confidence", 0.5),
                    "bnode_id_columns": c.get("bnode_id_columns"),
                    "condition": c.get("condition"),
                    "join_paths": c.get("join_paths"),
                    "subclass_of": c.get("subclass_of"),
                    "additional_class_definition_property": c.get("additional_class_definition_property"),
                    "translate_with": c.get("translate_with"),
                    "mapping_id": c.get("mapping_id"),
                }
            )
            collector.add("info", "CLASS_MAPPING_SYNTHESIZED_FROM_CLASS", "Synthesized class mapping from class definition.", path=f"class_mappings[{c['id']}]", class_id=c["id"])

    for m in class_mappings:
        cid = m.get("class_id")
        if not cid:
            continue
        c = class_idx.get(cid)
        if c is None:
            continue
        if (not c.get("source_tables")) and m.get("from_tables"):
            c["source_tables"] = m["from_tables"]
        if (not c.get("identifier_columns")) and m.get("identifier_columns"):
            c["identifier_columns"] = m["identifier_columns"]
        if (not c.get("instance_id_template")) and m.get("instance_id_template"):
            c["instance_id_template"] = m["instance_id_template"]
        for key in ["bnode_id_columns", "condition", "join_paths", "subclass_of", "additional_class_definition_property", "translate_with", "mapping_id"]:
            if (not c.get(key)) and m.get(key):
                c[key] = m[key]

    if not data_property_mappings:
        for p in data_properties:
            pid = p.get("id")
            if not pid:
                continue
            source_columns = [str(c).strip() for c in (p.get("source_columns") or []) if str(c).strip()]
            source_table = ""
            if source_columns and "." in source_columns[0]:
                source_table = source_columns[0].split(".", 1)[0]
            data_property_mappings.append(
                {
                    "property_id": pid,
                    "from_class": p.get("domain_class"),
                    "source_table": source_table,
                    "source_columns": source_columns,
                    "column": source_columns[0] if source_columns else "",
                    "joins": p.get("join_paths") or [],
                    "status": p.get("status", "proposed"),
                    "confidence": p.get("confidence", 0.5),
                    "datatype": p.get("datatype"),
                    "uri_column": p.get("uri_column"),
                    "pattern": p.get("pattern"),
                    "uri_pattern": p.get("uri_pattern"),
                    "sql_expression": p.get("sql_expression"),
                    "constant_value": p.get("constant_value"),
                    "condition": p.get("condition"),
                    "translate_with": p.get("translate_with"),
                    "mapping_id": p.get("mapping_id"),
                }
            )

    for m in data_property_mappings:
        pid = m.get("property_id")
        if not pid:
            continue
        p = dp_idx.get(pid)
        mapped_cols = [str(c).strip() for c in (m.get("source_columns") or []) if str(c).strip()]
        if m.get("column"):
            col = str(m.get("column")).strip()
            if col:
                mapped_cols.append(col)
        mapped_cols = list(dict.fromkeys(mapped_cols))
        mapped_joins = normalize_join_list(m.get("joins") or m.get("join_paths") or m.get("join"))

        if p is None:
            data_properties.append(
                {
                    "id": pid,
                    "label": pid.split(":", 1)[-1],
                    "domain_class": m.get("from_class") or "Class:UNKNOWN",
                    "range_type": "string",
                    "source_columns": mapped_cols,
                    "join_paths": mapped_joins,
                    "status": m.get("status", "proposed"),
                    "confidence": m.get("confidence", 0.5),
                    "datatype": m.get("datatype"),
                    "uri_column": m.get("uri_column"),
                    "pattern": m.get("pattern"),
                    "uri_pattern": m.get("uri_pattern"),
                    "sql_expression": m.get("sql_expression"),
                    "constant_value": m.get("constant_value"),
                    "condition": m.get("condition"),
                    "translate_with": m.get("translate_with"),
                    "mapping_id": m.get("mapping_id"),
                }
            )
            dp_idx[pid] = data_properties[-1]
            continue

        if (not p.get("source_columns")) and mapped_cols:
            p["source_columns"] = mapped_cols
        if (not p.get("join_paths")) and mapped_joins:
            p["join_paths"] = mapped_joins
        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
        for key in ["datatype", "uri_column", "pattern", "uri_pattern", "sql_expression", "constant_value", "condition", "translate_with", "mapping_id"]:
            if (not p.get(key)) and m.get(key):
                p[key] = m[key]

    if not object_property_mappings:
        for p in object_properties:
            pid = p.get("id")
            if not pid:
                continue
            object_property_mappings.append(
                {
                    "property_id": pid,
                    "from_class": p.get("domain_class"),
                    "to_class": p.get("range_class"),
                    "joins": p.get("join_paths") or [],
                    "status": p.get("status", "proposed"),
                    "confidence": p.get("confidence", 0.5),
                    "dynamic_property": p.get("dynamic_property"),
                    "condition": p.get("condition"),
                    "translate_with": p.get("translate_with"),
                    "mapping_id": p.get("mapping_id"),
                }
            )

    for m in object_property_mappings:
        pid = m.get("property_id")
        if not pid:
            continue
        p = op_idx.get(pid)
        joins = normalize_join_list(m.get("joins") or m.get("join_paths") or m.get("join"))
        if p is None:
            object_properties.append(
                {
                    "id": pid,
                    "label": pid.split(":", 1)[-1],
                    "domain_class": m.get("from_class") or "Class:UNKNOWN",
                    "range_class": m.get("to_class") or "Class:UNKNOWN",
                    "join_paths": joins,
                    "status": m.get("status", "proposed"),
                    "confidence": m.get("confidence", 0.5),
                    "dynamic_property": m.get("dynamic_property"),
                    "condition": m.get("condition"),
                    "translate_with": m.get("translate_with"),
                    "mapping_id": m.get("mapping_id"),
                }
            )
            op_idx[pid] = object_properties[-1]
            continue

        if (not p.get("join_paths")) and joins:
            p["join_paths"] = joins
        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
        if (not p.get("range_class") or p.get("range_class") == "Class:UNKNOWN") and m.get("to_class"):
            p["range_class"] = m["to_class"]
        for key in ["dynamic_property", "condition", "translate_with", "mapping_id"]:
            if (not p.get(key)) and m.get(key):
                p[key] = m[key]

    canonical["classes"] = classes
    canonical["data_properties"] = data_properties
    canonical["object_properties"] = object_properties
    canonical["class_mappings"] = class_mappings
    canonical["data_property_mappings"] = data_property_mappings
    canonical["object_property_mappings"] = object_property_mappings
    return canonical
