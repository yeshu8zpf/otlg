from __future__ import annotations

from typing import Any, Dict

from .backfill import backfill_from_mappings
from .canonicalizers import (
    canonicalize_class,
    canonicalize_class_mapping,
    canonicalize_data_property,
    canonicalize_data_property_mapping,
    canonicalize_object_property,
    canonicalize_object_property_mapping,
    canonicalize_subclass_relation,
)
from .collector import NormalizationCollector
from .contracts import assert_canonical_shape
from .helpers import as_list, find_root_payload, safe_dict


def normalize_model_output_robust(model_output: Dict[str, Any]) -> Dict[str, Any]:
    collector = NormalizationCollector()
    root = find_root_payload(model_output, collector)

    canonical: Dict[str, Any] = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "diagnostics": {},
    }

    for i, x in enumerate(as_list(root.get("classes"))):
        c = canonicalize_class(x)
        if not c["id"]:
            collector.add("warning", "CLASS_MISSING_ID", "Dropped class without usable id.", path=f"classes[{i}]", raw=x)
            continue
        canonical["classes"].append(c)

    for i, x in enumerate(as_list(root.get("data_properties") or root.get("datatype_properties"))):
        p = canonicalize_data_property(x)
        if not p["id"]:
            collector.add("warning", "DATA_PROPERTY_MISSING_ID", "Dropped data property without usable id.", path=f"data_properties[{i}]", raw=x)
            continue
        canonical["data_properties"].append(p)

    for i, x in enumerate(as_list(root.get("object_properties"))):
        p = canonicalize_object_property(x)
        if not p["id"]:
            collector.add("warning", "OBJECT_PROPERTY_MISSING_ID", "Dropped object property without usable id.", path=f"object_properties[{i}]", raw=x)
            continue
        canonical["object_properties"].append(p)

    for i, rel in enumerate(as_list(root.get("subclass_relations"))):
        canon_rel = canonicalize_subclass_relation(rel)
        if not canon_rel["child_class"] or not canon_rel["parent_class"]:
            collector.add(
                "warning",
                "SUBCLASS_RELATION_INCOMPLETE",
                "Dropped incomplete subclass relation after canonicalization.",
                path=f"subclass_relations[{i}]",
                raw=rel,
                canonical=canon_rel,
            )
            continue
        canonical["subclass_relations"].append(canon_rel)

    for i, x in enumerate(as_list(root.get("class_mappings"))):
        m = canonicalize_class_mapping(x)
        if not m["class_id"]:
            collector.add("warning", "CLASS_MAPPING_MISSING_CLASS_ID", "Dropped class mapping without class_id.", path=f"class_mappings[{i}]", raw=x)
            continue
        canonical["class_mappings"].append(m)

    for i, x in enumerate(as_list(root.get("data_property_mappings"))):
        m = canonicalize_data_property_mapping(x)
        if not m["property_id"]:
            collector.add("warning", "DATA_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "Dropped data property mapping without property_id.", path=f"data_property_mappings[{i}]", raw=x)
            continue
        canonical["data_property_mappings"].append(m)

    for i, x in enumerate(as_list(root.get("object_property_mappings"))):
        m = canonicalize_object_property_mapping(x)
        if not m["property_id"]:
            collector.add("warning", "OBJECT_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "Dropped object property mapping without property_id.", path=f"object_property_mappings[{i}]", raw=x)
            continue
        canonical["object_property_mappings"].append(m)

    canonical["diagnostics"] = safe_dict(root.get("diagnostics"))
    canonical = backfill_from_mappings(canonical, collector)
    assert_canonical_shape(canonical, collector)
    canonical["normalization_report"] = collector.report()
    return canonical
