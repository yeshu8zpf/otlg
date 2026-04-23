from __future__ import annotations

from typing import Any, Dict, List, Optional


PATCH_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]


def _norm_str(v: Any) -> str:
    return str(v).strip()


def _norm_str_list(vals: Any) -> List[str]:
    if vals is None:
        return []
    if not isinstance(vals, list):
        vals = [vals]
    return [str(x).strip() for x in vals if str(x).strip()]


def _norm_float(v: Any) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except Exception:
        return None


def _keep_if_present_str(out: Dict[str, Any], src: Dict[str, Any], key: str) -> None:
    if key in src:
        v = src.get(key)
        if v is not None:
            out[key] = _norm_str(v)


def _keep_if_present_list(out: Dict[str, Any], src: Dict[str, Any], key: str) -> None:
    if key in src:
        out[key] = _norm_str_list(src.get(key))


def _normalize_partial_class_mapping_update(updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    for key in [
        "mapping_id",
        "class_id",
        "identifier_kind",
        "instance_id_template",
        "description",
        "status",
    ]:
        _keep_if_present_str(out, updated_fields, key)

    for key in [
        "from_tables",
        "identifier_columns",
        "bnode_id_columns",
        "condition",
    ]:
        _keep_if_present_list(out, updated_fields, key)

    if "identifier_kind" in out:
        kind = out["identifier_kind"].lower()
        if kind == "uripattern":
            kind = "uri_pattern"
        out["identifier_kind"] = kind

    if "confidence" in updated_fields:
        out["confidence"] = _norm_float(updated_fields.get("confidence"))

    return out


def _normalize_partial_data_property_mapping_update(updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    for key in [
        "mapping_id",
        "data_property_id",
        "applies_to_class",
        "source_table",
        "value_kind",
        "value_template",
        "sql_expression",
        "datatype",
        "description",
        "status",
    ]:
        _keep_if_present_str(out, updated_fields, key)

    for key in ["source_columns", "join_paths", "condition"]:
        _keep_if_present_list(out, updated_fields, key)

    if "constant_value" in updated_fields:
        out["constant_value"] = updated_fields.get("constant_value")

    if "confidence" in updated_fields:
        out["confidence"] = _norm_float(updated_fields.get("confidence"))

    return out


def _normalize_partial_object_property_mapping_update(updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    for key in [
        "mapping_id",
        "object_property_id",
        "from_class",
        "to_class",
        "target_type",
        "source_table",
        "description",
        "status",
    ]:
        _keep_if_present_str(out, updated_fields, key)

    for key in [
        "source_columns",
        "source_identifier_columns",
        "target_identifier_columns",
        "join_paths",
        "condition",
    ]:
        _keep_if_present_list(out, updated_fields, key)

    if "confidence" in updated_fields:
        out["confidence"] = _norm_float(updated_fields.get("confidence"))

    return out


def _normalize_partial_generic_update(updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in updated_fields.items():
        if isinstance(v, list):
            out[k] = _norm_str_list(v)
        elif isinstance(v, str):
            out[k] = _norm_str(v)
        else:
            out[k] = v
    return out


def normalize_revision_updated_fields(field: str, updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize revision payload as a PARTIAL update.

    IMPORTANT:
    - only normalize keys explicitly present
    - never synthesize missing fields
    - never expand into a full object schema
    """
    if not isinstance(updated_fields, dict):
        return {}

    if field == "class_mappings":
        return _normalize_partial_class_mapping_update(updated_fields)

    if field == "data_property_mappings":
        return _normalize_partial_data_property_mapping_update(updated_fields)

    if field == "object_property_mappings":
        return _normalize_partial_object_property_mapping_update(updated_fields)

    return _normalize_partial_generic_update(updated_fields)


def is_effective_revision_payload(d: Dict[str, Any]) -> bool:
    """
    True iff updated_fields contains at least one real non-empty change.
    Empty strings / empty lists / empty dicts / None do not count.
    """
    if not isinstance(d, dict):
        return False

    for v in d.values():
        if v not in ("", None, [], {}):
            return True
    return False