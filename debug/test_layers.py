from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

# Make project root importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from normalize import normalize_model_output_robust
from ontology_draft import OntologyDraft
from ontology_tools.schema_profiler import SchemaProfiler
from ontology_tools.verifier_lite import MappingVerifierLite


# ============================================================
# Pretty helpers
# ============================================================

def title(name: str) -> None:
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)


def dump(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


# ============================================================
# Fixtures
# ============================================================

def raw_fixture_alias_heavy() -> Dict[str, Any]:
    """
    Intentionally messy raw model output to test normalize robustness.
    Covers:
    - subclass/superclass aliases
    - domain/range aliases
    - property mappings carrying grounding
    - object property joins in mapping
    - proposed status
    """
    return {
        "classes": [
            {
                "name": "Country",
                "label": "Country",
                "from_tables": ["country"],
                "identifier_columns": ["country.code"],
                "instance_id_template": "@@country.code@@",
                "status": "proposed",
                "confidence": 0.95,
            },
            {
                "name": "GeographicalFeature",
                "label": "GeographicalFeature",
                "from_tables": ["geo_feature"],
                "identifier_columns": ["geo_feature.id"],
                "instance_id_template": "@@geo_feature.id@@",
                "status": "proposed",
                "confidence": 0.80,
            },
            {
                "name": "Desert",
                "label": "Desert",
                "from_tables": ["desert"],
                "identifier_columns": ["desert.id"],
                "instance_id_template": "@@desert.id@@",
                "status": "proposed",
                "confidence": 0.80,
            },
        ],
        "data_properties": [
            {
                "name": "countryName",
                "label": "countryName",
                "domain": "Country",
                "range": "string",
                "status": "proposed",
                "confidence": 0.90,
            }
        ],
        "object_properties": [
            {
                "name": "hasFeature",
                "label": "hasFeature",
                "domain": "Country",
                "range": "GeographicalFeature",
                "status": "proposed",
                "confidence": 0.85,
            }
        ],
        "subclass_relations": [
            {
                "subclass": "Desert",
                "superclass": "GeographicalFeature",
                "status": "proposed",
                "confidence": 0.70,
            }
        ],
        "class_mappings": [
            {
                "class_id": "Country",
                "from_tables": ["country"],
                "identifier_columns": ["country.code"],
                "instance_id_template": "@@country.code@@",
                "status": "proposed",
                "confidence": 0.95,
            },
            {
                "class_id": "GeographicalFeature",
                "from_tables": ["geo_feature"],
                "identifier_columns": ["geo_feature.id"],
                "instance_id_template": "@@geo_feature.id@@",
                "status": "proposed",
                "confidence": 0.80,
            },
            {
                "class_id": "Desert",
                "from_tables": ["desert"],
                "identifier_columns": ["desert.id"],
                "instance_id_template": "@@desert.id@@",
                "status": "proposed",
                "confidence": 0.80,
            },
        ],
        "data_property_mappings": [
            {
                "data_property_id": "countryName",
                "applies_to_class": "Country",
                "source_table": "country",
                "source_columns": ["country.name"],
                "status": "proposed",
                "confidence": 0.88,
            }
        ],
        "object_property_mappings": [
            {
                "object_property_id": "hasFeature",
                "from_class": "Country",
                "to_class": "GeographicalFeature",
                "join_paths": [["country.code", "=", "geo_feature.country_code"]],
                "status": "proposed",
                "confidence": 0.84,
            }
        ],
        "diagnostics": {
            "note": "synthetic smoke test payload"
        },
    }


def raw_fixture_property_grounding_only_in_mapping() -> Dict[str, Any]:
    """
    Tests that validate/export accept effective grounding from mapping
    even when property.source_columns is empty.
    """
    return {
        "classes": [
            {
                "name": "Country",
                "label": "Country",
                "from_tables": ["country"],
                "identifier_columns": ["country.code"],
                "instance_id_template": "@@country.code@@",
                "status": "proposed",
            }
        ],
        "data_properties": [
            {
                "name": "countryName",
                "label": "countryName",
                "domain": "Country",
                "range": "string",
                "status": "proposed",
            }
        ],
        "class_mappings": [
            {
                "class_id": "Country",
                "from_tables": ["country"],
                "identifier_columns": ["country.code"],
                "instance_id_template": "@@country.code@@",
                "status": "proposed",
            }
        ],
        "data_property_mappings": [
            {
                "data_property_id": "countryName",
                "applies_to_class": "Country",
                "source_table": "country",
                "column": "country.name",
                "status": "proposed",
            }
        ],
    }


def schema_sql_fixture_alter_fk() -> str:
    return """
CREATE TABLE parent (
    id INT PRIMARY KEY,
    name TEXT
);

CREATE TABLE child (
    id INT PRIMARY KEY,
    parent_id INT,
    note TEXT
);

ALTER TABLE child
ADD CONSTRAINT fk_parent
FOREIGN KEY (parent_id)
REFERENCES parent(id);
""".strip()


# ============================================================
# Tests: normalize
# ============================================================

def test_normalize_contract() -> None:
    title("TEST 1: normalize contract / alias handling")

    raw = raw_fixture_alias_heavy()
    normalized = normalize_model_output_robust(raw)

    dump({
        "top_level_counts": {
            k: len(normalized.get(k, []) or [])
            for k in [
                "classes",
                "data_properties",
                "object_properties",
                "subclass_relations",
                "class_mappings",
                "data_property_mappings",
                "object_property_mappings",
            ]
        },
        "normalization_report": normalized.get("normalization_report", {}),
    })

    rels = normalized["subclass_relations"]
    assert_true(len(rels) == 1, "Expected 1 subclass relation after normalization.")
    rel = rels[0]

    assert_true("id" in rel and rel["id"], "Subclass relation should have synthesized id.")
    assert_true(rel["child_class"] == "Class:Desert", "Expected child_class=Class:Desert")
    assert_true(rel["parent_class"] == "Class:GeographicalFeature", "Expected parent_class=Class:GeographicalFeature")

    dp = normalized["data_properties"][0]
    assert_true(dp["domain_class"] == "Class:Country", "Expected normalized data property domain_class.")
    assert_true(dp["range_type"] == "string", "Expected normalized range_type=string")

    ok("normalize contract looks good")


# ============================================================
# Tests: draft construction
# ============================================================

def test_draft_from_normalized() -> None:
    title("TEST 2: draft construction from normalized payload")

    raw = raw_fixture_alias_heavy()
    normalized = normalize_model_output_robust(raw)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)

    assert_true(len(draft.classes) == 3, "Expected 3 classes in draft.")
    assert_true(len(draft.subclass_relations) == 1, "Expected 1 subclass relation in draft.")
    assert_true(draft.subclass_relations[0].child_class == "Class:Desert", "Subclass child mismatch.")
    assert_true(draft.subclass_relations[0].parent_class == "Class:GeographicalFeature", "Subclass parent mismatch.")

    ok("draft construction succeeded")


# ============================================================
# Tests: validate effective columns
# ============================================================

def test_validate_effective_columns() -> None:
    title("TEST 3: validate should accept effective columns from mapping")

    raw = raw_fixture_property_grounding_only_in_mapping()
    normalized = normalize_model_output_robust(raw)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)

    valid, errors = draft.validate()
    dump({"valid": valid, "errors": errors})

    assert_true(valid, f"Draft should validate successfully, but got errors: {errors}")

    ok("validate() accepts mapping-provided grounding")


# ============================================================
# Tests: verifier alignment
# ============================================================

def test_verifier_alignment() -> None:
    title("TEST 4: verifier should align with validate semantics")

    raw = raw_fixture_property_grounding_only_in_mapping()
    normalized = normalize_model_output_robust(raw)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)

    valid, errors = draft.validate()
    verifier = MappingVerifierLite()
    report = verifier.verify_draft_dict(draft.to_dict())

    dump({
        "validate": {"ok": valid, "errors": errors},
        "verifier_summary": {
            "ok": report["ok"],
            "num_errors": report["num_errors"],
            "num_warnings": report["num_warnings"],
            "num_infos": report["num_infos"],
        },
    })

    assert_true(valid, "validate() should pass on this fixture.")
    assert_true(report["ok"], f"verifier should also pass, but got errors: {report['errors']}")

    ok("verifier and validate are aligned on effective grounding")


# ============================================================
# Tests: export
# ============================================================

def test_export_proposed_status() -> None:
    title("TEST 5: export should not drop proposed-but-valid items")

    raw = raw_fixture_alias_heavy()
    normalized = normalize_model_output_robust(raw)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)

    valid, errors = draft.validate()
    assert_true(valid, f"Draft must validate before export test. Errors: {errors}")

    mapping = draft.to_burr_mapping()
    dump(mapping)

    assert_true(len(mapping["classes"]) >= 1, "Expected exported class mappings.")
    assert_true(len(mapping["data_properties"]) >= 1, "Expected exported data properties.")
    assert_true(len(mapping["object_properties"]) >= 1, "Expected exported object properties.")

    ok("export keeps proposed-but-valid structures")


# ============================================================
# Tests: schema profiler
# ============================================================

def test_schema_profiler_alter_fk() -> None:
    title("TEST 6: schema profiler should parse ALTER TABLE FK")

    sql = schema_sql_fixture_alter_fk()
    profile = SchemaProfiler().profile(sql)

    dump({
        "stats": profile["stats"],
        "join_graph": profile["join_graph"],
    })

    assert_true(profile["stats"]["num_tables"] == 2, "Expected 2 tables.")
    assert_true(profile["stats"]["num_foreign_keys"] == 1, "Expected 1 foreign key.")

    child_edges = profile["join_graph"].get("child", [])
    assert_true(len(child_edges) == 1, "Expected one edge from child.")
    assert_true(child_edges[0]["to_table"] == "parent", "Expected child -> parent edge.")

    joins = child_edges[0]["joins"]
    assert_true(joins == [["child.parent_id", "=", "parent.id"]], "Unexpected join graph contents.")

    ok("schema profiler parses ALTER TABLE foreign keys")


# ============================================================
# Tests: end-to-end small chain
# ============================================================

def test_end_to_end_small_chain() -> None:
    title("TEST 7: end-to-end small chain (raw -> normalize -> draft -> validate -> verifier -> export)")

    raw = raw_fixture_alias_heavy()

    normalized = normalize_model_output_robust(raw)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)

    valid, errors = draft.validate()
    verifier = MappingVerifierLite()
    verifier_report = verifier.verify_draft_dict(draft.to_dict())
    exported = draft.to_burr_mapping()

    dump({
        "normalized_counts": {
            k: len(normalized.get(k, []) or [])
            for k in [
                "classes",
                "data_properties",
                "object_properties",
                "subclass_relations",
                "class_mappings",
                "data_property_mappings",
                "object_property_mappings",
            ]
        },
        "validate": {"ok": valid, "errors": errors},
        "verifier": {
            "ok": verifier_report["ok"],
            "num_errors": verifier_report["num_errors"],
            "num_warnings": verifier_report["num_warnings"],
            "num_infos": verifier_report["num_infos"],
        },
        "export_counts": {
            "classes": len(exported.get("classes", [])),
            "data_properties": len(exported.get("data_properties", [])),
            "object_properties": len(exported.get("object_properties", [])),
        },
    })

    assert_true(valid, f"End-to-end draft validation failed: {errors}")
    assert_true(verifier_report["ok"], f"Verifier failed: {verifier_report['errors']}")
    assert_true(len(exported["classes"]) > 0, "Expected exported classes.")
    assert_true(len(exported["data_properties"]) > 0, "Expected exported data properties.")
    assert_true(len(exported["object_properties"]) > 0, "Expected exported object properties.")

    ok("end-to-end small chain passes")


# ============================================================
# Runner
# ============================================================

def main() -> None:
    tests = [
        test_normalize_contract,
        test_draft_from_normalized,
        test_validate_effective_columns,
        test_verifier_alignment,
        test_export_proposed_status,
        test_schema_profiler_alter_fk,
        test_end_to_end_small_chain,
    ]

    num_passed = 0
    for test_fn in tests:
        try:
            test_fn()
            num_passed += 1
        except Exception as e:
            fail(f"{test_fn.__name__} failed: {type(e).__name__}: {e}")
            raise

    title("SUMMARY")
    ok(f"Passed {num_passed}/{len(tests)} smoke tests")


if __name__ == "__main__":
    main()