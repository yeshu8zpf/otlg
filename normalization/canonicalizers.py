from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

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


QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")
BRACE_TOKEN_RE = re.compile(r"\{([^{}]+)\}")
AT_TOKEN_RE = re.compile(r"@@(.*?)@@")


def _split_table_column(x: str) -> Optional[Tuple[str, str]]:
    x = str(x or "").strip()
    m = QUALIFIED_COL_RE.match(x)
    if not m:
        return None
    return m.group(1), m.group(2)


def _normalize_qualified_column(x: str) -> str:
    tc = _split_table_column(x)
    if not tc:
        return normalize_identifier(x)
    return f"{tc[0].lower()}.{tc[1].lower()}"


def _build_identifier_lookup(identifier_columns: List[str]) -> Dict[str, str]:
    """
    Map:
      ConfID -> conferences.confid
      confid -> conferences.confid
    """
    out: Dict[str, str] = {}
    for col in identifier_columns:
        tc = _split_table_column(col)
        if not tc:
            continue
        table, attr = tc[0].lower(), tc[1].lower()
        fq = f"{table}.{attr}"
        out[attr] = fq
        out[attr.lower()] = fq
        out[tc[1]] = fq
    return out


def _infer_table_hint(
    source_tables: List[str],
    identifier_columns: List[str],
    template: str,
) -> str:
    if source_tables:
        return str(source_tables[0]).strip().lower()

    for col in identifier_columns:
        tc = _split_table_column(col)
        if tc:
            return tc[0].lower()

    # prefix-based fallback: conference/... -> conferences
    prefix = str(template or "").strip().split("/", 1)[0].strip().lower()
    irregular = {
        "person": "persons",
        "conference": "conferences",
        "organization": "organizations",
        "paper": "papers",
        "topic": "topics",
    }
    if prefix in irregular:
        return irregular[prefix]
    if prefix:
        return prefix if prefix.endswith("s") else prefix + "s"
    return ""


def _canonicalize_instance_id_template(
    template: str,
    identifier_columns: List[str],
    source_tables: List[str],
) -> str:
    """
    Examples:
      conference/{ConfID} -> conference/@@conferences.confid@@
      person/{PerID}      -> person/@@persons.perid@@
      topic/{TopicID}     -> topic/@@topics.topicid@@
      @@persons.perid@@   -> @@persons.perid@@
    """
    template = normalize_ws(template)
    if not template:
        return ""

    identifier_columns = [_normalize_qualified_column(c) for c in identifier_columns if str(c).strip()]
    lookup = _build_identifier_lookup(identifier_columns)
    table_hint = _infer_table_hint(source_tables, identifier_columns, template)

    def replace_brace_token(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        if not token:
            return match.group(0)

        tc = _split_table_column(token)
        if tc:
            return f"@@{tc[0].lower()}.{tc[1].lower()}@@"

        fq = lookup.get(token) or lookup.get(token.lower())
        if fq:
            return f"@@{fq}@@"

        if table_hint:
            return f"@@{table_hint}.{token.lower()}@@"

        return f"@@{token.lower()}@@"

    def replace_at_token(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        if not token:
            return match.group(0)

        tc = _split_table_column(token)
        if tc:
            return f"@@{tc[0].lower()}.{tc[1].lower()}@@"

        fq = lookup.get(token) or lookup.get(token.lower())
        if fq:
            return f"@@{fq}@@"

        if table_hint:
            return f"@@{table_hint}.{token.lower()}@@"

        return f"@@{token.lower()}@@"

    out = BRACE_TOKEN_RE.sub(replace_brace_token, template)
    out = AT_TOKEN_RE.sub(replace_at_token, out)
    return out


def canonicalize_class(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    cid_raw = d.get("id") or d.get("class_id") or d.get("name") or d.get("label")
    cid = normalize_class_id(cid_raw)
    label = d.get("label") or strip_prefix_if_present(cid, "Class:")

    source_tables = normalize_column_list(d.get("source_tables") or d.get("from_tables"))
    identifier_columns = normalize_column_list(d.get("identifier_columns"))

    instance_id_template = _canonicalize_instance_id_template(
        d.get("instance_id_template") or d.get("uri_template") or "",
        identifier_columns=identifier_columns,
        source_tables=source_tables,
    )

    out: Dict[str, Any] = {
        "id": cid,
        "label": normalize_ws(label),
        "source_tables": source_tables,
        "identifier_columns": identifier_columns,
        "instance_id_template": instance_id_template,
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

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
        out["subclass_of"] = [
            normalize_class_id(v)
            for v in as_list(d.get("subClassOf") or d.get("subclass_of"))
            if normalize_class_id(v)
        ]
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

    extras = {
        k: v
        for k, v in d.items()
        if k
        not in {
            "id", "class_id", "name", "label",
            "source_tables", "from_tables",
            "identifier_columns",
            "instance_id_template", "uri_template",
            "status", "confidence", "description",
            "prefix", "mapping_id",
            "condition", "join", "join_paths",
            "bNodeIdColumns", "bnode_id_columns",
            "subClassOf", "subclass_of",
            "additionalClassDefinitionProperty", "additional_class_definition_property",
            "translateWith", "translate_with",
        }
    }
    if extras:
        out["extras"] = extras
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

    extras = {
        k: v
        for k, v in d.items()
        if k
        not in {
            "id", "data_property_id", "property_id", "name", "label",
            "domain_class", "domain", "applies_to_class", "from_class",
            "range_type", "range", "datatype", "type",
            "source_columns", "columns", "column",
            "join_paths", "joins", "join",
            "status", "confidence", "description",
            "mapping_id", "dynamicProperty", "dynamic_property",
            "uriColumn", "uri_column", "pattern", "uriPattern", "uri_pattern",
            "sqlExpression", "sql_expression", "constantValue", "constant_value",
            "condition", "translateWith", "translate_with",
        }
    }
    if extras:
        out["extras"] = extras
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

    extras = {
        k: v
        for k, v in d.items()
        if k
        not in {
            "id", "object_property_id", "property_id", "name", "label",
            "domain_class", "domain", "from_class",
            "range_class", "range", "to_class", "target_class",
            "join_paths", "joins", "join",
            "status", "confidence", "description",
            "mapping_id", "dynamicProperty", "dynamic_property",
            "condition", "translateWith", "translate_with",
        }
    }
    if extras:
        out["extras"] = extras
    return out


def canonicalize_subclass_relation(x: Any) -> Dict[str, Any]:
    d = as_dict(x)

    child = (
        d.get("child_class")
        or d.get("child")
        or d.get("subclass")
        or d.get("sub_class")
        or d.get("source_class")
        or d.get("source")
        or d.get("from_class")
        or d.get("child_class_id")
    )
    parent = (
        d.get("parent_class")
        or d.get("parent")
        or d.get("superclass")
        or d.get("super_class")
        or d.get("target_class")
        or d.get("target")
        or d.get("to_class")
        or d.get("parent_class_id")
    )

    child = normalize_class_id(child) if child else ""
    parent = normalize_class_id(parent) if parent else ""

    rid = (
        d.get("id")
        or d.get("relation_id")
        or d.get("subclass_relation_id")
        or (f"SubclassRelation:{child}->{parent}" if child and parent else "")
    )

    out: Dict[str, Any] = {
        "id": normalize_identifier(rid),
        "child_class": child,
        "parent_class": parent,
        "status": normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")
    return out


def canonicalize_class_mapping(x: Any) -> Dict[str, Any]:
    d = as_dict(x)

    from_tables = normalize_column_list(d.get("from_tables") or d.get("source_tables"))
    identifier_columns = normalize_column_list(d.get("identifier_columns"))

    instance_id_template = _canonicalize_instance_id_template(
        d.get("instance_id_template") or d.get("uri_template") or "",
        identifier_columns=identifier_columns,
        source_tables=from_tables,
    )

    out = {
        "class_id": normalize_class_id(d.get("class_id") or d.get("class") or d.get("applies_to_class") or d.get("from_class")),
        "from_tables": from_tables,
        "identifier_columns": identifier_columns,
        "instance_id_template": instance_id_template,
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
        out["subclass_of"] = [
            normalize_class_id(v)
            for v in as_list(d.get("subClassOf") or d.get("subclass_of"))
            if normalize_class_id(v)
        ]
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

    extras = {
        k: v
        for k, v in d.items()
        if k
        not in {
            "class_id", "class", "applies_to_class", "from_class",
            "from_tables", "source_tables",
            "identifier_columns",
            "instance_id_template", "uri_template",
            "status", "confidence",
            "identifier_kind",
            "bNodeIdColumns", "bnode_id_columns",
            "condition", "join_paths", "join",
            "subClassOf", "subclass_of",
            "additionalClassDefinitionProperty", "additional_class_definition_property",
            "translateWith", "translate_with",
            "mapping_id",
        }
    }
    if extras:
        out["extras"] = extras
    return out


def canonicalize_data_property_mapping(x: Any) -> Dict[str, Any]:
    d = as_dict(x)
    property_id = normalize_property_id(d.get("property_id") or d.get("data_property_id") or d.get("id") or d.get("label"), "DataProperty")
    source_columns = normalize_column_list(d.get("source_columns") or d.get("columns"))
    column = normalize_identifier(d.get("column"))
    if column and column not in source_columns:
        source_columns.append(column)

    out = {
        "property_id": property_id,
        "from_class": normalize_class_id(
            d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")
        ) if (d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")) else "",
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
    property_id = normalize_property_id(d.get("property_id") or d.get("object_property_id") or d.get("id") or d.get("label"), "ObjectProperty")

    out = {
        "property_id": property_id,
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