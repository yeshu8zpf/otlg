from __future__ import annotations

from typing import Any, Dict, List


class MappingVerifierLite:
    def verify_class_mapping(self, class_mapping: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not class_mapping.get("class_id"):
            errors.append("class_mapping missing class_id")
        if not class_mapping.get("instance_id_template"):
            errors.append("class_mapping missing instance_id_template")
        if not class_mapping.get("from_tables"):
            errors.append("class_mapping missing from_tables")
        if not class_mapping.get("identifier_columns"):
            errors.append("class_mapping missing identifier_columns")
        return errors

    def verify_data_property_mapping(self, m: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not m.get("property_id"):
            errors.append("data_property_mapping missing property_id")
        if not m.get("from_class"):
            errors.append("data_property_mapping missing from_class")
        if not m.get("column"):
            errors.append("data_property_mapping missing column")
        return errors

    def verify_object_property_mapping(self, m: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not m.get("property_id"):
            errors.append("object_property_mapping missing property_id")
        if not m.get("from_class"):
            errors.append("object_property_mapping missing from_class")
        if not m.get("to_class"):
            errors.append("object_property_mapping missing to_class")
        if not m.get("joins"):
            errors.append("object_property_mapping missing joins")
        return errors

    def verify_draft_dict(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        class_ids = {c.get("id") for c in draft.get("classes", []) if c.get("id")}
        data_prop_ids = {p.get("id") for p in draft.get("data_properties", []) if p.get("id")}
        object_prop_ids = {p.get("id") for p in draft.get("object_properties", []) if p.get("id")}

        for cm in draft.get("class_mappings", []):
            errors.extend(self.verify_class_mapping(cm))
            if cm.get("class_id") and cm["class_id"] not in class_ids:
                errors.append(f"class_mapping references unknown class {cm['class_id']}")

        for dm in draft.get("data_property_mappings", []):
            errors.extend(self.verify_data_property_mapping(dm))
            if dm.get("property_id") and dm["property_id"] not in data_prop_ids:
                errors.append(f"data_property_mapping references unknown property {dm['property_id']}")

        for om in draft.get("object_property_mappings", []):
            errors.extend(self.verify_object_property_mapping(om))
            if om.get("property_id") and om["property_id"] not in object_prop_ids:
                errors.append(f"object_property_mapping references unknown property {om['property_id']}")

        return {
            "ok": len(errors) == 0,
            "num_errors": len(errors),
            "errors": errors,
        }
