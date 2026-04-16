from __future__ import annotations

import json
from typing import Any, Dict

from .helpers import (
    as_list,
    as_str,
    coerce_float01,
    dedup_keep_order,
    ensure_qualified_column,
    field_names,
    infer_tables_from_template,
    normalize_class_id,
    normalize_data_property_id,
    normalize_join,
    normalize_object_property_id,
    safe_dict,
    split_kwargs,
)
from .types import (
    ClassDef,
    ClassMapping,
    DataPropertyDef,
    DataPropertyMapping,
    ObjectPropertyDef,
    ObjectPropertyMapping,
    SubclassRelation,
)


def _build_dataclass(cls, data: Dict[str, Any]):
    known, extra = split_kwargs(cls, data)

    if cls.__name__ == "SubclassRelation":
        if "child_class" not in known:
            child = data.get("child_class") or data.get("child") or data.get("subclass") or data.get("sub_class") or data.get("source_class") or data.get("source") or data.get("from_class") or data.get("child_class_id")
            if child:
                known["child_class"] = normalize_class_id(child)
        if "parent_class" not in known:
            parent = data.get("parent_class") or data.get("parent") or data.get("superclass") or data.get("super_class") or data.get("target_class") or data.get("target") or data.get("to_class") or data.get("parent_class_id")
            if parent:
                known["parent_class"] = normalize_class_id(parent)
        if "id" not in known:
            child = known.get("child_class", "")
            parent = known.get("parent_class", "")
            if child and parent:
                known["id"] = f"SubclassRelation:{child}->{parent}"

    if cls.__name__ == "DataPropertyDef":
        if "domain_class" not in known:
            domain = data.get("domain_class") or data.get("domain") or data.get("from_class") or data.get("applies_to_class")
            if domain:
                known["domain_class"] = normalize_class_id(domain)
        if "id" not in known:
            label = data.get("label") or data.get("name") or data.get("property_id") or data.get("data_property_id")
            domain = known.get("domain_class", "Class:UNKNOWN")
            if label:
                known["id"] = normalize_data_property_id(domain, str(label))
        if "range_type" not in known:
            rt = data.get("range_type") or data.get("range") or data.get("datatype") or data.get("type")
            known["range_type"] = as_str(rt) or "string"
        if "join_paths" not in known:
            joins = data.get("join_paths") or data.get("joins") or data.get("join") or []
            known["join_paths"] = [normalize_join(j) for j in as_list(joins) if normalize_join(j)]
        if "condition" not in known and data.get("condition") is not None:
            known["condition"] = [normalize_join(j) for j in as_list(data.get("condition")) if normalize_join(j)]

    if cls.__name__ == "ObjectPropertyDef":
        if "domain_class" not in known:
            domain = data.get("domain_class") or data.get("domain") or data.get("from_class")
            if domain:
                known["domain_class"] = normalize_class_id(domain)
        if "range_class" not in known:
            r = data.get("range_class") or data.get("range") or data.get("to_class") or data.get("target_class")
            if r:
                known["range_class"] = normalize_class_id(r)
        if "id" not in known:
            label = data.get("label") or data.get("name") or data.get("property_id") or data.get("object_property_id")
            domain = known.get("domain_class", "Class:UNKNOWN")
            if label:
                known["id"] = normalize_object_property_id(domain, str(label))
        if "join_paths" not in known:
            joins = data.get("join_paths") or data.get("joins") or data.get("join") or []
            known["join_paths"] = [normalize_join(j) for j in as_list(joins) if normalize_join(j)]
        if "condition" not in known and data.get("condition") is not None:
            known["condition"] = [normalize_join(j) for j in as_list(data.get("condition")) if normalize_join(j)]

    if cls.__name__ == "DataPropertyMapping":
        if "property_id" not in known:
            pid = data.get("property_id") or data.get("data_property_id") or data.get("id")
            if pid:
                known["property_id"] = as_str(pid)
        if "from_class" not in known:
            domain = data.get("from_class") or data.get("domain_class") or data.get("applies_to_class")
            if domain:
                known["from_class"] = normalize_class_id(domain)
        if "column" not in known and data.get("column"):
            known["column"] = as_str(data.get("column"))
        if "source_columns" not in known:
            cols = data.get("source_columns") or []
            known["source_columns"] = [str(x) for x in as_list(cols) if str(x).strip()]
        if "joins" not in known:
            joins = data.get("joins") or data.get("join_paths") or data.get("join") or []
            known["joins"] = [normalize_join(j) for j in as_list(joins) if normalize_join(j)]
        if "condition" not in known and data.get("condition") is not None:
            known["condition"] = [normalize_join(j) for j in as_list(data.get("condition")) if normalize_join(j)]

    if cls.__name__ == "ObjectPropertyMapping":
        if "property_id" not in known:
            pid = data.get("property_id") or data.get("object_property_id") or data.get("id")
            if pid:
                known["property_id"] = as_str(pid)
        if "from_class" not in known:
            domain = data.get("from_class") or data.get("domain_class") or data.get("domain")
            if domain:
                known["from_class"] = normalize_class_id(domain)
        if "to_class" not in known:
            r = data.get("to_class") or data.get("range_class") or data.get("range") or data.get("target_class")
            if r:
                known["to_class"] = normalize_class_id(r)
        if "joins" not in known:
            joins = data.get("joins") or data.get("join_paths") or data.get("join") or []
            known["joins"] = [normalize_join(j) for j in as_list(joins) if normalize_join(j)]
        if "condition" not in known and data.get("condition") is not None:
            known["condition"] = [normalize_join(j) for j in as_list(data.get("condition")) if normalize_join(j)]

    try:
        obj = cls(**known)
    except TypeError as e:
        payload = {
            "target_class": cls.__name__,
            "known": known,
            "all_data": data,
            "missing_or_bad_fields_hint": str(e),
        }
        raise TypeError(f"Failed to build {cls.__name__}: {json.dumps(payload, ensure_ascii=False, default=str)}") from e

    existing_extras = safe_dict(data.get("extras"))
    if hasattr(obj, "extras"):
        obj.extras = {**existing_extras, **extra}
    return obj


def build_class_def(data: Dict[str, Any]) -> ClassDef:
    return _build_dataclass(ClassDef, data)


def build_data_property_def(data: Dict[str, Any]) -> DataPropertyDef:
    return _build_dataclass(DataPropertyDef, data)


def build_object_property_def(data: Dict[str, Any]) -> ObjectPropertyDef:
    return _build_dataclass(ObjectPropertyDef, data)


def build_subclass_relation(data: Dict[str, Any]) -> SubclassRelation:
    return _build_dataclass(SubclassRelation, data)


def build_class_mapping(data: Dict[str, Any]) -> ClassMapping:
    return _build_dataclass(ClassMapping, data)


def build_data_property_mapping(data: Dict[str, Any]) -> DataPropertyMapping:
    return _build_dataclass(DataPropertyMapping, data)


def build_object_property_mapping(data: Dict[str, Any]) -> ObjectPropertyMapping:
    return _build_dataclass(ObjectPropertyMapping, data)
