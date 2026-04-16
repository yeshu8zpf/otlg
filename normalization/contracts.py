from __future__ import annotations

from typing import Any, Dict


def assert_canonical_shape(canonical: Dict[str, Any], collector) -> None:
    required_top = {
        "classes",
        "data_properties",
        "object_properties",
        "subclass_relations",
        "class_mappings",
        "data_property_mappings",
        "object_property_mappings",
        "diagnostics",
    }
    for k in required_top:
        if k not in canonical:
            collector.add("error", "MISSING_TOP_LEVEL_KEY", f"Missing canonical top-level key: {k}", key=k)

    for i, rel in enumerate(canonical.get("subclass_relations", [])):
        if not rel.get("id") or not rel.get("child_class") or not rel.get("parent_class"):
            collector.add(
                "error",
                "BAD_SUBCLASS_RELATION",
                "Canonical subclass relation missing required fields.",
                path=f"subclass_relations[{i}]",
                relation=rel,
            )
