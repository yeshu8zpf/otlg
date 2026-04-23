
from __future__ import annotations

"""
Robust patch normalization aligned with the strict prompt schema.

Key design:
1. Internal draft schema is intentionally close to patch schema.
2. We still support a wide range of legacy / drifting aliases.
3. We normalize to a single canonical internal schema that is friendly to Burr export.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import copy
import json
import re
from .revision_normalize import (
    normalize_revision_updated_fields,
    is_effective_revision_payload,
)


PATCH_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]


# ----------------------------
# small helpers
# ----------------------------
def _should_keep_normalized_item(field: str, item: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False

    if field == "classes":
        return bool(item.get("id"))

    if field == "data_properties":
        return bool(item.get("id"))

    if field == "object_properties":
        return bool(item.get("id"))

    if field == "subclass_relations":
        return bool(item.get("id")) and bool(item.get("child_class")) and bool(item.get("parent_class"))

    if field == "class_mappings":
        return (
            bool(item.get("mapping_id"))
            and bool(item.get("class_id"))
            and bool(item.get("identifier_kind"))
            and (
                bool(item.get("identifier_columns"))
                or bool(item.get("bnode_id_columns"))
                or bool(item.get("instance_id_template"))
            )
        )

    if field == "data_property_mappings":
        value_kind = item.get("value_kind", "")
        if not (
            item.get("mapping_id")
            and item.get("data_property_id")
            and item.get("applies_to_class")
            and value_kind
        ):
            return False

        if value_kind == "column":
            return bool(item.get("source_columns"))
        if value_kind in {"pattern", "uri_pattern"}:
            return bool(item.get("value_template"))
        if value_kind == "sql_expression":
            return bool(item.get("sql_expression"))
        if value_kind == "constant":
            return item.get("constant_value", "") not in ("", None)
        return True

    if field == "object_property_mappings":
        if not (
            item.get("mapping_id")
            and item.get("object_property_id")
            and item.get("from_class")
        ):
            return False

        if item.get("target_type") == "resource":
            return True

        return bool(item.get("to_class"))

    return bool(item)


def _class_id_from_patch_name(name: str) -> str:
    """
    Normalize various class-name spellings into internal canonical form:
      Class:SomeName
    """
    name = normalize_ws(str(name or ""))
    if not name:
        return ""

    lower = name.lower()
    if lower.startswith("class:"):
        suffix = name.split(":", 1)[1].strip()
        return f"Class:{normalize_identifier(suffix)}" if normalize_identifier(suffix) else ""

    normalized = normalize_identifier(name)
    if not normalized:
        return ""

    return f"Class:{normalized}"

def normalize_ws(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip())


def normalize_identifier(x: Any) -> str:
    return normalize_ws(x)


def as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def pick_first(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return default


def get_str(d: Dict[str, Any], *keys: str, default: str = "") -> str:
    v = pick_first(d, list(keys), default=default)
    return normalize_identifier(v)


def get_list(d: Dict[str, Any], *keys: str) -> List[Any]:
    v = pick_first(d, list(keys), default=[])
    return as_list(v)


def normalize_class_id(x: Any) -> str:
    s = normalize_identifier(x)
    if not s:
        return ""
    return s if s.startswith("Class:") else f"Class:{s}"


def normalize_property_id(x: Any, prefix: str) -> str:
    s = normalize_identifier(x)
    if not s:
        return ""
    return s if s.startswith(prefix + ":") else f"{prefix}:{s}"


def normalize_range_type(x: Any) -> str:
    s = normalize_identifier(x)
    if not s:
        return "xsd:string"
    mapping = {
        "string": "xsd:string",
        "integer": "xsd:integer",
        "int": "xsd:integer",
        "date": "xsd:date",
        "datetime": "xsd:dateTime",
        "timestamp": "xsd:dateTime",
        "anyuri": "xsd:anyURI",
        "uri": "xsd:anyURI",
        "boolean": "xsd:boolean",
        "decimal": "xsd:decimal",
    }
    return mapping.get(s.lower(), s)


def _is_qualified_column(s: str) -> bool:
    s = normalize_identifier(s)
    return "." in s and len(s.split(".", 1)[0]) > 0 and len(s.split(".", 1)[1]) > 0


def build_known_tables(incremental_step: Optional[Dict[str, Any]] = None, draft: Optional[Dict[str, Any]] = None) -> Set[str]:
    tables: Set[str] = set()
    if incremental_step:
        for k in ["new_table"]:
            v = incremental_step.get(k)
            if v:
                tables.add(str(v).lower())
        local_table = incremental_step.get("local_table", {}) or {}
        if local_table.get("name"):
            tables.add(str(local_table["name"]).lower())
        for t in incremental_step.get("related_existing_tables", []) or []:
            tables.add(str(t).lower())
        for t in (incremental_step.get("suggested_analysis_scope", {}) or {}).get("recommended_tables_for_joint_analysis", []) or []:
            tables.add(str(t).lower())
    if draft:
        for sec in ["classes", "class_mappings", "data_property_mappings", "object_property_mappings"]:
            for x in draft.get(sec, []) or []:
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


def qualify_column(col: Any, *, table_hint: Optional[str], known_tables: Set[str]) -> str:
    s = normalize_identifier(col)
    if not s:
        return ""
    if _is_qualified_column(s):
        left, right = s.split(".", 1)
        return f"{left.lower()}.{right.lower()}"
    if table_hint:
        return f"{table_hint.lower()}.{s.lower()}"
    return s.lower()


def split_or_qualify_database_column(database_column: str, *, default_table: Optional[str], known_tables: Set[str]) -> Tuple[str, List[str]]:
    s = normalize_identifier(database_column)
    if not s:
        return normalize_identifier(default_table).lower(), []
    if _is_qualified_column(s):
        left, right = s.split(".", 1)
        return left.lower(), [f"{left.lower()}.{right.lower()}"]
    q = qualify_column(s, table_hint=default_table, known_tables=known_tables)
    if _is_qualified_column(q):
        left, _ = q.split(".", 1)
        return left.lower(), [q]
    return normalize_identifier(default_table).lower(), [q] if q else []


def qualify_column_list(cols: Any, *, table_hint: Optional[str], known_tables: Set[str]) -> List[str]:
    out: List[str] = []
    for c in as_list(cols):
        qc = qualify_column(c, table_hint=table_hint, known_tables=known_tables)
        if qc:
            out.append(qc)
    return list(dict.fromkeys(out))


def normalize_join_paths_scoped(joins: Any, *, default_table_hint: Optional[str], known_tables: Set[str]) -> List[List[str]]:
    out: List[List[str]] = []
    for j in as_list(joins):
        if isinstance(j, list):
            if len(j) == 3:
                left, op, right = j
                out.append([
                    qualify_column(left, table_hint=default_table_hint, known_tables=known_tables),
                    normalize_identifier(op),
                    qualify_column(right, table_hint=default_table_hint, known_tables=known_tables),
                ])
            else:
                norm = [normalize_identifier(x) for x in j if normalize_identifier(x)]
                if norm:
                    out.append(norm)
        elif isinstance(j, str):
            s = normalize_identifier(j)
            if not s:
                continue
            # tolerate "a = b"
            m = re.match(r"^\s*([A-Za-z0-9_\.]+)\s*(=|!=|<>|<=|>=|<|>)\s*([A-Za-z0-9_\.]+)\s*$", s)
            if m:
                left, op, right = m.groups()
                out.append([
                    qualify_column(left, table_hint=default_table_hint, known_tables=known_tables),
                    op,
                    qualify_column(right, table_hint=default_table_hint, known_tables=known_tables),
                ])
            else:
                out.append([s])
    return out


def _normalize_identity_kind(raw: str) -> str:
    raw = normalize_identifier(raw).lower()
    mapping = {
        "uripattern": "uri_pattern",
        "uri_pattern": "uri_pattern",
        "uricolumn": "uri_column",
        "uri_column": "uri_column",
        "bnode": "bnode",
        "bnodeidcolumns": "bnode",
        "bnode_id_columns": "bnode",
    }
    return mapping.get(raw, raw or "uri_pattern")


# ----------------------------
# alias-aware raw canonicalization
# ----------------------------

def canonicalize_raw_class_patch(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "class_id": normalize_class_id(
            get_str(item, "id", "class_id", "ontology_class", "ontology_class_id")
        ),
        "label": get_str(item, "label", default=""),
        "description": get_str(item, "description", "rationale"),
        "source_tables": [str(t).lower() for t in get_list(item, "source_tables") if normalize_identifier(t)],
        "identifier_columns": get_list(item, "identifier_columns"),
    }


def canonicalize_raw_data_property_patch(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data_property_id": normalize_property_id(
            get_str(item, "id", "data_property_id", "ontology_data_property", "ontology_property", "ontology_property_id"),
            "DataProperty",
        ),
        "label": get_str(item, "label"),
        "domain": normalize_class_id(get_str(item, "domain", "applies_to_class", "class_id")),
        "datatype": normalize_range_type(get_str(item, "datatype", "range", default="xsd:string")),
        "description": get_str(item, "description"),
    }


def canonicalize_raw_object_property_patch(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "object_property_id": normalize_property_id(
            get_str(item, "id", "object_property_id", "ontology_object_property", "ontology_property", "ontology_property_id"),
            "ObjectProperty",
        ),
        "label": get_str(item, "label"),
        "domain": normalize_class_id(get_str(item, "domain", "from_class")),
        "range": normalize_class_id(get_str(item, "range", "to_class", "target_class")),
        "description": get_str(item, "description"),
    }


def parse_identity_block(item: Dict[str, Any]) -> Dict[str, Any]:
    identity = item.get("identity", {}) or {}
    identity_source = item.get("identity_source", {}) or {}

    kind = _normalize_identity_kind(
        pick_first(
            {
                "a": get_str(identity, "type"),
                "b": get_str(item, "identity_strategy"),
            },
            ["a", "b"],
            default="uri_pattern",
        )
    )

    pattern = pick_first(
        {
            "a": get_str(identity, "pattern"),
            "b": get_str(identity_source, "pattern"),
            "c": get_str(item, "uri_pattern", "identifier_pattern", "instance_id_template"),
        },
        ["a", "b", "c"],
        default="",
    )

    columns = pick_first(
        {
            "a": get_list(identity, "columns"),
            "b": get_list(identity_source, "columns"),
            "c": get_list(item, "identifier_columns", "bnode_id_columns"),
        },
        ["a", "b", "c"],
        default=[],
    )

    return {
        "kind": kind,
        "pattern": normalize_identifier(pattern),
        "columns": as_list(columns),
    }


def _class_id_from_class_mapping_name(name: str) -> str:
    s = normalize_identifier(name)
    if not s:
        return ""
    prefix = s.split("_from_", 1)[0]
    return normalize_class_id(prefix)


def canonicalize_raw_class_mapping(item: Dict[str, Any]) -> Dict[str, Any]:
    identity = parse_identity_block(item)
    return {
        "mapping_id": get_str(item, "mapping_id", "id"),
        "class_id": normalize_class_id(get_str(item, "class_id", "ontology_class", "ontology_class_id")),
        "source_table": get_str(item, "source_table", "database_table", "table"),
        "identity_kind": identity["kind"],
        "identity_pattern": identity["pattern"],
        "identity_columns": identity["columns"],
        "description": get_str(item, "description", "rationale"),
    }


def canonicalize_raw_data_property_mapping(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mapping_id": get_str(item, "mapping_id", "id"),
        "data_property_id": normalize_property_id(
            get_str(item, "data_property_id", "ontology_data_property", "ontology_property", "ontology_property_id"),
            "DataProperty",
        ),
        "source_table": get_str(item, "source_table", "database_table", "table"),
        "source_column": get_str(item, "source_column", "column"),
        "database_column": get_str(item, "database_column"),
        "class_mapping_id": get_str(item, "class_mapping_id", "class_mapping", "belongsToClassMap"),
        "datatype": normalize_range_type(get_str(item, "datatype", "range", "column_type")),
        "description": get_str(item, "description"),
    }


def canonicalize_raw_object_property_mapping(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mapping_id": get_str(item, "mapping_id", "id"),
        "object_property_id": normalize_property_id(
            get_str(item, "object_property_id", "ontology_object_property", "ontology_property", "ontology_property_id"),
            "ObjectProperty",
        ),
        "source_table": get_str(item, "source_table", "database_table", "table"),
        "source_column": get_str(item, "source_column", "column"),
        "database_column": get_str(item, "database_column"),
        "class_mapping_id": get_str(item, "class_mapping_id", "class_mapping", "belongsToClassMap"),
        "target_type": get_str(item, "target_type", default="entity").lower(),
        "target_class": normalize_class_id(get_str(item, "target_class", "to_class", "range_class")),
        "joins": pick_first(item, ["joins", "join_paths", "join"], default=[]),
        "condition": pick_first(item, ["condition"], default=[]),
        "description": get_str(item, "description"),
    }


# ----------------------------
# normalize section items into canonical internal draft schema
# ----------------------------

def normalize_class_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)
    raw = canonicalize_raw_class_patch(x)
    source_tables = [str(t).lower() for t in raw["source_tables"]]
    table_hint = source_tables[0] if source_tables else default_table_hint(incremental_step)
    identifier_columns = qualify_column_list(raw["identifier_columns"], table_hint=table_hint, known_tables=known_tables)

    return {
        "id": raw["class_id"],
        "label": raw["label"] or raw["class_id"].replace("Class:", ""),
        "description": raw["description"],
        "status": x.get("status", "proposed"),
        "confidence": x.get("confidence"),
        "source_tables": source_tables,
        "identifier_columns": identifier_columns,
    }


def normalize_data_property_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    raw = canonicalize_raw_data_property_patch(x)
    return {
        "id": raw["data_property_id"],
        "label": raw["label"] or raw["data_property_id"].replace("DataProperty:", ""),
        "domain": raw["domain"],
        "datatype": raw["datatype"],
        "description": raw["description"],
        "status": x.get("status", "proposed"),
        "confidence": x.get("confidence"),
        "source_tables": [],
        "source_columns": [],
    }


def normalize_object_property_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    raw = canonicalize_raw_object_property_patch(x)
    return {
        "id": raw["object_property_id"],
        "label": raw["label"] or raw["object_property_id"].replace("ObjectProperty:", ""),
        "domain": raw["domain"],
        "range": raw["range"],
        "description": raw["description"],
        "status": x.get("status", "proposed"),
        "confidence": x.get("confidence"),
        "source_tables": [],
    }


def normalize_subclass_relation_item(x: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    child = normalize_class_id(get_str(x, "child_class"))
    parent = normalize_class_id(get_str(x, "parent_class"))
    return {
        "id": get_str(x, "id") or f"{child}_to_{parent}",
        "child_class": child,
        "parent_class": parent,
        "status": x.get("status", "proposed"),
        "confidence": x.get("confidence"),
    }


def _normalize_patch_class_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)

    mapping_id = _get_str(item, ["mapping_id", "id"])
    class_id = _class_id_from_patch_name(
        _get_str(item, ["class_id", "ontology_class", "ontology_class_id"])
    )

    from_tables = [
        normalize_identifier(t).lower()
        for t in _get_list(item, ["from_tables"])
        if normalize_identifier(t)
    ]

    if not from_tables:
        source_table = normalize_identifier(
            _get_str(item, ["source_table", "database_table", "table"])
        ).lower()
        if source_table:
            from_tables = [source_table]

    identity = item.get("identity", {}) or {}

    identifier_kind = _normalize_identity_kind(
        _get_str(
            {
                "a": _get_str(identity, ["type"]),
                "b": _get_str(item, ["identity_strategy", "identifier_kind"]),
            },
            ["a", "b"],
        )
    )

    identifier_columns = qualify_column_list(
        _get_list(
            {
                "a": _get_list(identity, ["columns"]),
                "b": _get_list(item, ["identifier_columns"]),
            },
            ["a", "b"],
        ),
        table_hint=(from_tables[0] if from_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    if not from_tables:
        inferred = _infer_table_from_qualified_columns(identifier_columns)
        if inferred:
            from_tables = [inferred]

    instance_id_template = _get_str(
        {
            "a": _get_str(identity, ["pattern"]),
            "b": _get_str(item, ["instance_id_template", "uri_pattern"]),
        },
        ["a", "b"],
    )

    bnode_id_columns = qualify_column_list(
        _get_list(item, ["bnode_id_columns"]),
        table_hint=(from_tables[0] if from_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    return {
        "mapping_id": mapping_id,
        "class_id": class_id,
        "from_tables": from_tables,
        "identifier_kind": identifier_kind,
        "identifier_columns": identifier_columns,
        "instance_id_template": instance_id_template,
        "bnode_id_columns": bnode_id_columns,
        "status": item.get("status", "proposed"),
        "confidence": item.get("confidence"),
        "description": _get_str(item, ["description"]),
    }


def _normalize_patch_data_property_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)

    mapping_id = _get_str(item, ["mapping_id", "id"])
    data_property_id = normalize_property_id(
        _get_str(item, ["data_property_id", "ontology_property", "ontology_property_id", "ontology_data_property"]),
        "DataProperty",
    )
    applies_to_class = _class_id_from_patch_name(
        _get_str(item, ["applies_to_class", "domain", "class_id"])
    )

    source_table = normalize_identifier(
        _get_str(item, ["source_table", "database_table", "table"])
    ).lower()

    source_columns = _get_list(item, ["source_columns"])

    database_column = _get_str(item, ["database_column"])
    if database_column and not source_columns:
        source_columns = [database_column]

    source_column = _get_str(item, ["source_column", "column"])
    if source_column and not source_columns:
        source_columns = [source_column]

    source_columns = qualify_column_list(
        source_columns,
        table_hint=(source_table or default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    if not source_table:
        source_table = _infer_table_from_qualified_columns(source_columns)

    value_kind = _get_str(item, ["value_kind"], default="column").lower() or "column"

    value_template = _get_str(item, ["value_template", "pattern", "uri_pattern"])
    sql_expression = _get_str(item, ["sql_expression"])
    constant_value = item.get("constant_value", "")

    datatype = normalize_range_type(_get_str(item, ["datatype", "range"], default=""))

    join_paths = normalize_join_paths_scoped(
        item.get("join_paths", []),
        default_table_hint=(source_table or default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    condition = normalize_join_paths_scoped(
        item.get("condition", []),
        default_table_hint=(source_table or default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    return {
        "mapping_id": mapping_id,
        "data_property_id": data_property_id,
        "applies_to_class": applies_to_class,
        "source_table": source_table,
        "source_columns": source_columns,
        "value_kind": value_kind,
        "value_template": value_template,
        "sql_expression": sql_expression,
        "constant_value": constant_value,
        "datatype": datatype,
        "join_paths": join_paths,
        "condition": condition,
    }

def _normalize_patch_object_property_mapping(item: Dict[str, Any], *, incremental_step=None) -> Dict[str, Any]:
    known_tables = build_known_tables(incremental_step)

    mapping_id = _get_str(item, ["mapping_id", "id"])
    object_property_id = normalize_property_id(
        _get_str(item, ["object_property_id", "ontology_property", "ontology_property_id"]),
        "ObjectProperty",
    )
    from_class = _class_id_from_patch_name(
        _get_str(item, ["from_class", "domain"])
    )
    to_class = _class_id_from_patch_name(
        _get_str(item, ["to_class", "range", "target_class"])
    )

    from_tables = [
        normalize_identifier(t).lower()
        for t in _get_list(item, ["from_tables"])
        if normalize_identifier(t)
    ]

    source_identifier_columns = qualify_column_list(
        _get_list(item, ["source_identifier_columns"]),
        table_hint=(from_tables[0] if from_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    target_identifier_columns = qualify_column_list(
        _get_list(item, ["target_identifier_columns"]),
        table_hint=None,
        known_tables=known_tables,
    )

    join_paths = normalize_join_paths_scoped(
        item.get("join_paths", []),
        default_table_hint=(from_tables[0] if from_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    condition = normalize_join_paths_scoped(
        item.get("condition", []),
        default_table_hint=(from_tables[0] if from_tables else default_table_hint(incremental_step)),
        known_tables=known_tables,
    )

    target_type = _get_str(item, ["target_type"], default="entity").lower() or "entity"

    return {
        "mapping_id": mapping_id,
        "object_property_id": object_property_id,
        "from_class": from_class,
        "to_class": to_class,
        "from_tables": from_tables,
        "source_identifier_columns": source_identifier_columns,
        "target_identifier_columns": target_identifier_columns,
        "join_paths": join_paths,
        "condition": condition,
        "target_type": target_type,
    }

def _pick_first_nonempty(obj: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for k in keys:
        if k in obj and obj[k] not in (None, "", [], {}):
            return obj[k]
    return default


def _get_str(obj: Dict[str, Any], keys: List[str], default: str = "") -> str:
    v = _pick_first_nonempty(obj, keys, default)
    if v is None:
        return default
    return normalize_ws(str(v))


def _get_list(obj: Dict[str, Any], keys: List[str], default: Optional[List[Any]] = None) -> List[Any]:
    if default is None:
        default = []
    v = _pick_first_nonempty(obj, keys, default)
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _infer_table_from_qualified_columns(cols: List[str]) -> str:
    for c in cols:
        if isinstance(c, str) and "." in c:
            return c.split(".", 1)[0].lower()
    return ""

def _normalize_section_item(field: str, item: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        return {}

    if field == "classes":
        return normalize_class_item(item, incremental_step=incremental_step)

    if field == "data_properties":
        return normalize_data_property_item(item, incremental_step=incremental_step)

    if field == "object_properties":
        return normalize_object_property_item(item, incremental_step=incremental_step)

    if field == "subclass_relations":
        return normalize_subclass_relation_item(item, incremental_step=incremental_step)

    if field == "class_mappings":
        return _normalize_patch_class_mapping(item, incremental_step=incremental_step)

    if field == "data_property_mappings":
        return _normalize_patch_data_property_mapping(item, incremental_step=incremental_step)

    if field == "object_property_mappings":
        return _normalize_patch_object_property_mapping(item, incremental_step=incremental_step)

    return item


def _normalize_revision_payload(
    field: str,
    updated_fields: Dict[str, Any],
    *,
    incremental_step: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # revision payload must remain partial
    return normalize_revision_updated_fields(field, updated_fields)


def _normalize_decision_summary(items: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        items = [items]

    for x in items:
        if isinstance(x, dict):
            out.append(
                {
                    "decision_type": normalize_identifier(x.get("decision_type")),
                    "target": normalize_identifier(x.get("target")),
                    "status": normalize_identifier(x.get("status")).lower() or "proposed",
                    "confidence": _to_confidence(x.get("confidence", 0.5)),
                    "reason": normalize_ws(x.get("reason")),
                }
            )
        elif isinstance(x, str):
            s = normalize_ws(x)
            if s:
                out.append(
                    {
                        "decision_type": "UNSTRUCTURED_NOTE",
                        "target": "",
                        "status": "proposed",
                        "confidence": 0.5,
                        "reason": s,
                    }
                )
    return out


def _to_confidence(v: Any) -> float:
    try:
        x = float(v)
    except Exception:
        x = 0.5
    return max(0.0, min(1.0, x))

def _normalize_work_unit(work_unit: Any, *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not isinstance(work_unit, dict):
        work_unit = {}

    table = normalize_identifier(
        work_unit.get("table")
        or (incremental_step or {}).get("new_table")
        or ""
    ).lower()

    related_tables = [
        normalize_identifier(x).lower()
        for x in as_list(work_unit.get("related_tables", []))
        if normalize_identifier(x)
    ]

    return {
        "table": table,
        "related_tables": related_tables,
    }


def _normalize_string_list(xs: Any) -> List[str]:
    if xs is None:
        return []
    if not isinstance(xs, list):
        xs = [xs]
    out = []
    for x in xs:
        s = normalize_ws(str(x))
        if s:
            out.append(s)
    return out


def _normalize_probe_list(xs: Any) -> List[Dict[str, Any]]:
    if xs is None:
        return []
    if not isinstance(xs, list):
        xs = [xs]

    out: List[Dict[str, Any]] = []
    for x in xs:
        if isinstance(x, dict):
            probe_type = normalize_identifier(x.get("probe_type"))
            target = normalize_identifier(x.get("target")).lower()
            question = normalize_ws(x.get("question"))
            out.append(
                {
                    "probe_type": probe_type,
                    "target": target,
                    "question": question,
                }
            )
        else:
            s = normalize_ws(str(x))
            if s:
                out.append(
                    {
                        "probe_type": "unspecified",
                        "target": "",
                        "question": s,
                    }
                )
    return out

def _dedupe_preserve_order(xs: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _enrich_data_properties_from_mappings(patch: Dict[str, Any]) -> None:
    """
    Backfill source_tables/source_columns on ontology-level data_properties
    using data_property_mappings in the same normalized patch.
    """
    additions = patch.get("proposed_additions", {}) or {}
    data_properties = additions.get("data_properties", []) or []
    data_property_mappings = additions.get("data_property_mappings", []) or []

    grouped: Dict[str, Dict[str, List[str]]] = {}

    for m in data_property_mappings:
        prop_id = str(m.get("data_property_id") or "").strip()
        if not prop_id:
            continue

        grouped.setdefault(prop_id, {"source_tables": [], "source_columns": []})

        source_table = str(m.get("source_table") or "").strip().lower()
        if source_table:
            grouped[prop_id]["source_tables"].append(source_table)

        for col in m.get("source_columns", []) or []:
            col_s = str(col).strip().lower()
            if col_s:
                grouped[prop_id]["source_columns"].append(col_s)

    for p in data_properties:
        prop_id = str(p.get("id") or "").strip()
        if not prop_id:
            continue

        info = grouped.get(prop_id)
        if not info:
            continue

        existing_tables = [str(x).strip().lower() for x in (p.get("source_tables", []) or []) if str(x).strip()]
        existing_columns = [str(x).strip().lower() for x in (p.get("source_columns", []) or []) if str(x).strip()]

        p["source_tables"] = _dedupe_preserve_order(existing_tables + info["source_tables"])
        p["source_columns"] = _dedupe_preserve_order(existing_columns + info["source_columns"])
def _enrich_object_properties_from_mappings(patch: Dict[str, Any]) -> None:
    """
    Backfill source_tables on ontology-level object_properties
    using object_property_mappings in the same normalized patch.
    """
    additions = patch.get("proposed_additions", {}) or {}
    object_properties = additions.get("object_properties", []) or []
    object_property_mappings = additions.get("object_property_mappings", []) or []

    grouped: Dict[str, Dict[str, List[str]]] = {}

    for m in object_property_mappings:
        prop_id = str(m.get("object_property_id") or "").strip()
        if not prop_id:
            continue

        grouped.setdefault(prop_id, {"source_tables": []})

        for t in m.get("from_tables", []) or []:
            t_s = str(t).strip().lower()
            if t_s:
                grouped[prop_id]["source_tables"].append(t_s)

    for p in object_properties:
        prop_id = str(p.get("id") or "").strip()
        if not prop_id:
            continue

        info = grouped.get(prop_id)
        if not info:
            continue

        existing_tables = [str(x).strip().lower() for x in (p.get("source_tables", []) or []) if str(x).strip()]
        p["source_tables"] = _dedupe_preserve_order(existing_tables + info["source_tables"])

def _coerce_patch_section_container(obj: Any) -> Dict[str, Any]:
    """
    Normalize proposed_additions / proposed_revisions outer container.

    Accept:
    - dict
    - [dict]  -> unwrap
    - anything else -> empty dict
    """
    if isinstance(obj, dict):
        return obj

    if isinstance(obj, list):
        # common drift: proposed_additions becomes [ {...} ]
        if len(obj) == 1 and isinstance(obj[0], dict):
            return obj[0]

        # try to merge multiple dicts conservatively
        merged: Dict[str, Any] = {}
        for x in obj:
            if not isinstance(x, dict):
                continue
            for k, v in x.items():
                if k not in merged:
                    merged[k] = v
                else:
                    if isinstance(merged[k], list) and isinstance(v, list):
                        merged[k] = merged[k] + v
                    elif not merged[k] and v:
                        merged[k] = v
        return merged

    return {}

def _is_effective_revision_payload(d: Dict[str, Any]) -> bool:
    """
    Return True only if updated_fields contains at least one genuinely non-empty update.
    Empty strings / empty lists / empty dicts / None do NOT count as effective changes.
    """
    if not isinstance(d, dict):
        return False

    for v in d.values():
        if v not in ("", None, [], {}):
            return True
    return False
def normalize_patch_robust(raw_patch: Dict[str, Any], *, incremental_step: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    warnings: List[Dict[str, Any]] = []

    out: Dict[str, Any] = {
        "work_unit": _normalize_work_unit(raw_patch.get("work_unit", {}), incremental_step=incremental_step),
        "proposed_additions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_revisions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_rejections": list(raw_patch.get("proposed_rejections", []) or []),
        "proposed_merges": list(raw_patch.get("proposed_merges", []) or []),
        "decision_summary": _normalize_decision_summary(raw_patch.get("decision_summary", [])),
        "remaining_ambiguities": _normalize_string_list(raw_patch.get("remaining_ambiguities", [])),
        "needs_probe": _normalize_probe_list(raw_patch.get("needs_probe", [])),
        "normalization_warnings": warnings,
    }

    additions = _coerce_patch_section_container(raw_patch.get("proposed_additions", {}))
    for field in PATCH_SECTION_FIELDS:
        raw_items = additions.get(field, [])
        if raw_items is None:
            raw_items = []
        if not isinstance(raw_items, list):
            raw_items = [raw_items]

        for item in raw_items:
            norm = _normalize_section_item(field, item, incremental_step=incremental_step)

            if not _should_keep_normalized_item(field, norm):
                warnings.append(
                    {
                        "section": field,
                        "message": "Dropped empty normalized item",
                        "raw_item": norm if norm else item,
                    }
                )
                continue

            out["proposed_additions"][field].append(norm)

    revisions = _coerce_patch_section_container(raw_patch.get("proposed_revisions", {}))
    for field in PATCH_SECTION_FIELDS:
        raw_items = revisions.get(field, [])
        if raw_items is None:
            raw_items = []
        if not isinstance(raw_items, list):
            raw_items = [raw_items]

        for item in raw_items:
            if not isinstance(item, dict):
                warnings.append(
                    {
                        "section": field,
                        "message": "Dropped non-dict revision item",
                        "raw_item": item,
                    }
                )
                continue

            target_id = item.get("target_id")
            updated_fields = item.get("updated_fields", {}) or {}

            norm_updated = _normalize_revision_payload(
                field,
                updated_fields,
                incremental_step=incremental_step,
            )
            
            if not target_id or not norm_updated or not _is_effective_revision_payload(norm_updated):
                warnings.append(
                    {
                        "section": field,
                        "message": "Dropped revision with empty or ineffective updated_fields",
                        "raw_item": item,
                    }
                )
                continue

            out["proposed_revisions"][field].append(
                {
                    "target_id": str(target_id),
                    "updated_fields": norm_updated,
                }
            )

    _enrich_data_properties_from_mappings(out)
    _enrich_object_properties_from_mappings(out)
    return out
def _is_nonempty_mapping_object(field: str, obj: Dict[str, Any]) -> bool:
    if field == "class_mappings":
        return bool(obj.get("class_id"))
    if field == "data_property_mappings":
        return bool(obj.get("data_property_id") and obj.get("applies_to_class"))
    if field == "object_property_mappings":
        return bool(obj.get("object_property_id") and obj.get("from_class"))
    if field in {"classes", "data_properties", "object_properties"}:
        return bool(obj.get("id"))
    return True


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
        seen = set()
        for item in draft.get(field, []) or []:
            try:
                norm = _normalize_section_item(field, item, incremental_step=incremental_step)
            except Exception:
                continue
            key = _draft_item_key(field, norm)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            if norm:
                out[field].append(norm)

    meta = out["draft_metadata"]
    meta["draft_version"] = int(meta.get("draft_version", 0) or 0)
    meta["processed_tables"] = [str(x).lower() for x in meta.get("processed_tables", []) or [] if normalize_identifier(x)]

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

