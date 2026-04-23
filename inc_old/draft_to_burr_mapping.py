
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_qualified_column(col: str, source_table: str | None = None) -> str:
    col = str(col or "").strip()
    if not col:
        return ""
    if "." in col:
        left, right = col.split(".", 1)
        return f"{left.lower()}.{right.lower()}"
    if source_table:
        return f"{str(source_table).lower()}.{col.lower()}"
    return col.lower()


def validate_pred_mapping(mapping: Dict[str, Any]) -> None:
    for i, x in enumerate(mapping.get("data_properties", [])):
        col = x.get("column")
        if col is not None and "." not in col:
            raise ValueError(f"Invalid column at data_properties[{i}]: {col}")
        uri_col = x.get("uriColumn")
        if uri_col is not None and "." not in uri_col:
            raise ValueError(f"Invalid uriColumn at data_properties[{i}]: {uri_col}")

    for i, x in enumerate(mapping.get("classes", [])):
        for c in x.get("bNodeIdColumns", []) or []:
            if "." not in c:
                raise ValueError(f"Invalid bNodeIdColumns entry at classes[{i}]: {c}")


def convert_global_draft_to_burr_mapping(global_draft: Dict[str, Any]) -> Dict[str, Any]:
    class_defs = {x["id"]: x for x in global_draft.get("classes", []) if x.get("id")}
    data_prop_defs = {x["id"]: x for x in global_draft.get("data_properties", []) if x.get("id")}
    obj_prop_defs = {x["id"]: x for x in global_draft.get("object_properties", []) if x.get("id")}

    class_mappings = global_draft.get("class_mappings", [])
    data_prop_mappings = global_draft.get("data_property_mappings", [])
    obj_prop_mappings = global_draft.get("object_property_mappings", [])

    burr_classes: List[Dict[str, Any]] = []
    burr_data_properties: List[Dict[str, Any]] = []
    burr_object_properties: List[Dict[str, Any]] = []

    class_map_id_by_class: Dict[str, str] = {}

    for cm in class_mappings:
        class_id = cm.get("class_id")
        if not class_id:
            continue

        class_def = class_defs.get(class_id, {})
        mapping_id = cm.get("mapping_id") or class_id
        class_map_id_by_class[class_id] = mapping_id

        item: Dict[str, Any] = {
            "id": mapping_id,
            "class": class_id,
            "name": class_def.get("label", class_id),
        }

        identifier_kind = cm.get("identifier_kind")
        if identifier_kind == "bnode":
            bnode_cols = cm.get("bnode_id_columns") or cm.get("identifier_columns") or []
            item["bNodeIdColumns"] = [
                ensure_qualified_column(c, (cm.get("from_tables") or [None])[0]) for c in bnode_cols
            ]
        else:
            if cm.get("instance_id_template"):
                item["uriPattern"] = cm["instance_id_template"]
            elif cm.get("identifier_columns"):
                cols = cm["identifier_columns"]
                if len(cols) == 1:
                    item["uriPattern"] = f"{class_id.lower()}/@@{ensure_qualified_column(cols[0], (cm.get('from_tables') or [None])[0])}@@"

        if cm.get("condition"):
            item["condition"] = cm["condition"]
        if cm.get("join_paths"):
            item["join"] = _normalize_join_paths(cm["join_paths"])
        if cm.get("subclass_of"):
            item["subClassOf"] = cm["subclass_of"]
        if cm.get("translate_with"):
            item["translateWith"] = cm["translate_with"]

        burr_classes.append(item)

    for dpm in data_prop_mappings:
        prop_id = dpm.get("data_property_id") or dpm.get("property_id")
        if not prop_id:
            continue

        prop_def = data_prop_defs.get(prop_id, {})
        applies_to_class = dpm.get("applies_to_class") or dpm.get("from_class")
        belongs_to_class_map = class_map_id_by_class.get(applies_to_class, applies_to_class)

        item: Dict[str, Any] = {
            "property": prop_id,
            "belongsToClassMap": belongs_to_class_map,
        }

        source_columns = dpm.get("source_columns", []) or []
        value_kind = dpm.get("value_kind")
        source_table = dpm.get("source_table")

        if value_kind == "column":
            if source_columns:
                item["column"] = ensure_qualified_column(source_columns[0], source_table)
        elif value_kind == "uri_column":
            if source_columns:
                item["uriColumn"] = ensure_qualified_column(source_columns[0], source_table)
        elif value_kind == "pattern":
            if dpm.get("value_template"):
                item["pattern"] = dpm["value_template"]
        elif value_kind == "uri_pattern":
            if dpm.get("value_template"):
                item["uriPattern"] = dpm["value_template"]
        elif value_kind == "constant":
            if dpm.get("constant_value") is not None:
                item["constantValue"] = dpm["constant_value"]
        elif value_kind == "sql_expression":
            if dpm.get("sql_expression"):
                item["sqlExpression"] = dpm["sql_expression"]
        else:
            if source_columns:
                item["column"] = ensure_qualified_column(source_columns[0], source_table)

        datatype = dpm.get("datatype") or prop_def.get("datatype")
        if datatype:
            item["datatype"] = datatype

        if dpm.get("join_paths"):
            item["join"] = _normalize_join_paths(dpm["join_paths"])
        if dpm.get("condition"):
            item["condition"] = dpm["condition"]
        if dpm.get("translate_with"):
            item["translateWith"] = dpm["translate_with"]

        burr_data_properties.append(item)

    for opm in obj_prop_mappings:
        prop_id = opm.get("object_property_id") or opm.get("property_id")
        if not prop_id:
            continue

        prop_def = obj_prop_defs.get(prop_id, {})
        from_class = opm.get("from_class") or prop_def.get("domain")
        to_class = opm.get("to_class") or opm.get("range")

        item: Dict[str, Any] = {
            "property": prop_id,
            "belongsToClassMap": class_map_id_by_class.get(from_class, from_class),
            "refersToClassMap": class_map_id_by_class.get(to_class, to_class),
        }

        if opm.get("join_paths"):
            item["join"] = _normalize_join_paths(opm["join_paths"])
        if opm.get("condition"):
            item["condition"] = opm["condition"]
        if opm.get("dynamic_property"):
            item["dynamicProperty"] = opm["dynamic_property"]
        if opm.get("translate_with"):
            item["translateWith"] = opm["translate_with"]

        burr_object_properties.append(item)

    mapping = {
        "classes": burr_classes,
        "data_properties": burr_data_properties,
        "object_properties": burr_object_properties,
    }
    validate_pred_mapping(mapping)
    return mapping


def _normalize_join_paths(join_paths: List[Any]) -> List[str]:
    out: List[str] = []
    for j in join_paths:
        if isinstance(j, list) and len(j) == 3:
            out.append(f"{j[0]} {j[1]} {j[2]}")
        elif isinstance(j, str):
            out.append(j)
    return out


def convert_global_draft_file(global_draft_path: Path, out_mapping_path: Path) -> Dict[str, Any]:
    draft = read_json(global_draft_path)
    mapping = convert_global_draft_to_burr_mapping(draft)
    write_json(out_mapping_path, mapping)
    return mapping
