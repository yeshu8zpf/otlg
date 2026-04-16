from __future__ import annotations

from typing import Any, Dict

from .helpers import (
    as_dict,
    as_list,
    coerce_confidence,
    normalize_class_id,
    normalize_column_list,
    normalize_identifier,
    normalize_join_list,
    normalize_optional_string,
    normalize_property_id,
    normalize_range_type,
    normalize_ws,
    strip_prefix_if_present,
)


def canonicalize_class(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    cid_raw = d.get("id") or d.get("class_id") or d.get("name") or d.get("label")
    cid = normalize_class_id(cid_raw)
    label = d.get("label") or strip_prefix_if_present(cid, "Class:")

    out: Dict[str, Any] = {
        "id": cid,
        "label": normalize_ws(label),
        "source_tables": normalize_column_list(d.get("source_tables") or d.get("from_tables")),
        "identifier_columns": normalize_column_list(d.get("identifier_columns")),
        "instance_id_template": normalize_ws(d.get("instance_id_template") or d.get("uri_template") or ""),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    # Burr/D2RQ-related optional class-side fields
    if d.get("prefix") is not None:
        out["prefix"] = normalize_optional_string(d.get("prefix")).lower()
    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("join") is not None or d.get("join_paths") is not None:
        out["join_paths"] = normalize_join_list(d.get("join_paths") or d.get("join"))
    if d.get("bNodeIdColumns") is not None or d.get("bnode_id_columns") is not None:
        out["bnode_id_columns"] = normalize_column_list(d.get("bNodeIdColumns") or d.get("bnode_id_columns"))
    if d.get("subClassOf") is not None or d.get("subclass_of") is not None:
        out["subclass_of"] = [normalize_class_id(v) for v in as_list(d.get("subClassOf") or d.get("subclass_of")) if normalize_class_id(v)]
    if d.get("additionalClassDefinitionProperty") is not None or d.get("additional_class_definition_property") is not None:
        out["additional_class_definition_property"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("additionalClassDefinitionProperty") or d.get("additional_class_definition_property"))
            if normalize_optional_string(v)
        ]
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]

    return out


def canonicalize_data_property(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    pid_raw = d.get("id") or d.get("data_property_id") or d.get("property_id") or d.get("name") or d.get("label")
    pid = normalize_property_id(pid_raw, "DataProperty")
    label = d.get("label") or strip_prefix_if_present(pid, "DataProperty:")
    domain = d.get("domain_class") or d.get("domain") or d.get("applies_to_class") or d.get("from_class")
    range_type = d.get("range_type") or d.get("range") or d.get("datatype") or d.get("type")
    source_columns = normalize_column_list(d.get("source_columns") or d.get("columns"))
    if d.get("column"):
        c = normalize_identifier(d.get("column"))
        if c and c not in source_columns:
            source_columns.append(c)

    out: Dict[str, Any] = {
        "id": pid,
        "label": normalize_ws(label),
        "domain_class": normalize_class_id(domain) if domain else "",
        "range_type": normalize_range_type(range_type),
        "source_columns": source_columns,
        "join_paths": normalize_join_list(d.get("join_paths") or d.get("joins") or d.get("join")),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))
    if d.get("datatype") is not None:
        out["datatype"] = normalize_range_type(d.get("datatype"))
    if d.get("dynamicProperty") is not None or d.get("dynamic_property") is not None:
        out["dynamic_property"] = normalize_optional_string(d.get("dynamicProperty") or d.get("dynamic_property"))
    if d.get("uriColumn") is not None or d.get("uri_column") is not None:
        out["uri_column"] = normalize_column_list(d.get("uriColumn") or d.get("uri_column"))
    if d.get("pattern") is not None:
        out["pattern"] = normalize_optional_string(d.get("pattern"))
    if d.get("uriPattern") is not None or d.get("uri_pattern") is not None:
        out["uri_pattern"] = normalize_optional_string(d.get("uriPattern") or d.get("uri_pattern"))
    if d.get("sqlExpression") is not None or d.get("sql_expression") is not None:
        out["sql_expression"] = normalize_optional_string(d.get("sqlExpression") or d.get("sql_expression"))
    if d.get("constantValue") is not None or d.get("constant_value") is not None:
        out["constant_value"] = d.get("constantValue") if d.get("constantValue") is not None else d.get("constant_value")
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]

    return out


def canonicalize_object_property(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    pid_raw = d.get("id") or d.get("object_property_id") or d.get("property_id") or d.get("name") or d.get("label")
    pid = normalize_property_id(pid_raw, "ObjectProperty")
    label = d.get("label") or strip_prefix_if_present(pid, "ObjectProperty:")
    domain = d.get("domain_class") or d.get("domain") or d.get("from_class")
    range_class = d.get("range_class") or d.get("range") or d.get("to_class") or d.get("target_class")

    out: Dict[str, Any] = {
        "id": pid,
        "label": normalize_ws(label),
        "domain_class": normalize_class_id(domain) if domain else "",
        "range_class": normalize_class_id(range_class) if range_class else "",
        "join_paths": normalize_join_list(d.get("join_paths") or d.get("joins") or d.get("join")),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))
    if d.get("dynamicProperty") is not None or d.get("dynamic_property") is not None:
        out["dynamic_property"] = normalize_optional_string(d.get("dynamicProperty") or d.get("dynamic_property"))
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]

    return out


def canonicalize_subclass_relation(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    child = d.get("child_class") or d.get("child") or d.get("subclass") or d.get("sub_class") or d.get("source_class") or d.get("source") or d.get("from_class") or d.get("child_class_id")
    parent = d.get("parent_class") or d.get("parent") or d.get("superclass") or d.get("super_class") or d.get("target_class") or d.get("target") or d.get("to_class") or d.get("parent_class_id")

    child = normalize_class_id(child) if child else ""
    parent = normalize_class_id(parent) if parent else ""

    rid = d.get("id") or d.get("relation_id") or d.get("subclass_relation_id") or (f"SubclassRelation:{child}->{parent}" if child and parent else "")

    return {
        "id": normalize_identifier(rid),
        "child_class": child,
        "parent_class": parent,
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }


def canonicalize_class_mapping(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    out = {
        "class_id": normalize_class_id(d.get("class_id") or d.get("class") or d.get("applies_to_class") or d.get("from_class")),
        "from_tables": normalize_column_list(d.get("from_tables") or d.get("source_tables")),
        "identifier_columns": normalize_column_list(d.get("identifier_columns")),
        "instance_id_template": normalize_ws(d.get("instance_id_template") or d.get("uri_template") or ""),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }

    if d.get("identifier_kind") is not None:
        out["identifier_kind"] = normalize_optional_string(d.get("identifier_kind")).lower()
    if d.get("bNodeIdColumns") is not None or d.get("bnode_id_columns") is not None:
        out["bnode_id_columns"] = normalize_column_list(d.get("bNodeIdColumns") or d.get("bnode_id_columns"))
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("join_paths") is not None or d.get("join") is not None:
        out["join_paths"] = normalize_join_list(d.get("join_paths") or d.get("join"))
    if d.get("subClassOf") is not None or d.get("subclass_of") is not None:
        out["subclass_of"] = [normalize_class_id(v) for v in as_list(d.get("subClassOf") or d.get("subclass_of")) if normalize_class_id(v)]
    if d.get("additionalClassDefinitionProperty") is not None or d.get("additional_class_definition_property") is not None:
        out["additional_class_definition_property"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("additionalClassDefinitionProperty") or d.get("additional_class_definition_property"))
            if normalize_optional_string(v)
        ]
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]
    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))

    return out


def canonicalize_data_property_mapping(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    source_columns = normalize_column_list(d.get("source_columns") or d.get("columns"))
    column = normalize_identifier(d.get("column"))
    if column and column not in source_columns:
        source_columns.append(column)

    out = {
        "property_id": normalize_property_id(d.get("property_id") or d.get("data_property_id") or d.get("id") or d.get("label"), "DataProperty"),
        "from_class": normalize_class_id(d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")) if (d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")) else "",
        "source_table": normalize_identifier(d.get("source_table") or d.get("table") or ""),
        "source_columns": source_columns,
        "column": column,
        "joins": normalize_join_list(d.get("joins") or d.get("join_paths") or d.get("join")),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }

    if d.get("value_kind") is not None:
        out["value_kind"] = normalize_optional_string(d.get("value_kind")).lower()
    if d.get("uriColumn") is not None or d.get("uri_column") is not None:
        out["uri_column"] = normalize_column_list(d.get("uriColumn") or d.get("uri_column"))
    if d.get("pattern") is not None:
        out["pattern"] = normalize_optional_string(d.get("pattern"))
    if d.get("uriPattern") is not None or d.get("uri_pattern") is not None:
        out["uri_pattern"] = normalize_optional_string(d.get("uriPattern") or d.get("uri_pattern"))
    if d.get("sqlExpression") is not None or d.get("sql_expression") is not None:
        out["sql_expression"] = normalize_optional_string(d.get("sqlExpression") or d.get("sql_expression"))
    if d.get("constantValue") is not None or d.get("constant_value") is not None:
        out["constant_value"] = d.get("constantValue") if d.get("constantValue") is not None else d.get("constant_value")
    if d.get("datatype") is not None:
        out["datatype"] = normalize_range_type(d.get("datatype"))
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]
    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))

    return out


def canonicalize_object_property_mapping(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    out = {
        "property_id": normalize_property_id(d.get("property_id") or d.get("object_property_id") or d.get("id") or d.get("label"), "ObjectProperty"),
        "from_class": normalize_class_id(d.get("from_class") or d.get("domain") or d.get("domain_class")) if (d.get("from_class") or d.get("domain") or d.get("domain_class")) else "",
        "to_class": normalize_class_id(d.get("to_class") or d.get("range") or d.get("range_class") or d.get("target_class")) if (d.get("to_class") or d.get("range") or d.get("range_class") or d.get("target_class")) else "",
        "joins": normalize_join_list(d.get("joins") or d.get("join_paths") or d.get("join")),
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }

    if d.get("dynamicProperty") is not None or d.get("dynamic_property") is not None:
        out["dynamic_property"] = normalize_optional_string(d.get("dynamicProperty") or d.get("dynamic_property"))
    if d.get("condition") is not None:
        out["condition"] = normalize_join_list(d.get("condition"))
    if d.get("translateWith") is not None or d.get("translate_with") is not None:
        out["translate_with"] = [
            normalize_optional_string(v)
            for v in as_list(d.get("translateWith") or d.get("translate_with"))
            if normalize_optional_string(v)
        ]
    if d.get("mapping_id") is not None:
        out["mapping_id"] = normalize_optional_string(d.get("mapping_id"))

    return out
