from __future__ import annotations

from typing import Any, Dict


def summarize_top_level_counts(obj: Dict[str, Any]) -> Dict[str, int]:
    return {
        "num_classes": len(obj.get("classes", []) or []),
        "num_data_properties": len(obj.get("data_properties", []) or []),
        "num_object_properties": len(obj.get("object_properties", []) or []),
        "num_subclass_relations": len(obj.get("subclass_relations", []) or []),
        "num_class_mappings": len(obj.get("class_mappings", []) or []),
        "num_data_property_mappings": len(obj.get("data_property_mappings", []) or []),
        "num_object_property_mappings": len(obj.get("object_property_mappings", []) or []),
    }
