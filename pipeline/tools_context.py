from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from ontology_tools import (
    HypothesisStore,
    InstanceProfiler,
    MappingVerifierLite,
    PatternDetector,
    SchemaProfiler,
)

ALL_TOOLS = {
    "schema_profiler",
    "instance_profiler",
    "pattern_detector",
    "mapping_verifier_lite",
}


def parse_enabled_tools(raw: str) -> Set[str]:
    items = {x.strip() for x in (raw or "").split(",") if x.strip()}
    unknown = sorted(items - ALL_TOOLS)
    if unknown:
        raise ValueError(f"Unknown tools: {unknown}. Supported: {sorted(ALL_TOOLS)}")
    return items


def compress_hypotheses_for_prompt(
    hypotheses: List[Dict[str, Any]],
    max_items: int = 20,
) -> List[Dict[str, Any]]:
    ranked = sorted(
        hypotheses,
        key=lambda x: (float(x.get("confidence", 0.0) or 0.0), x.get("kind", "")),
        reverse=True,
    )
    out = []
    for h in ranked[:max_items]:
        out.append(
            {
                "kind": h.get("kind"),
                "statement": h.get("statement"),
                "confidence": h.get("confidence"),
                "payload": h.get("payload", {}),
                "evidence": (h.get("evidence", []) or [])[:3],
            }
        )
    return out


def build_tool_context(
    schema_profile: Optional[Dict[str, Any]],
    instance_profile: Optional[Dict[str, Any]],
    hypothesis_store: Optional[HypothesisStore],
    enabled_tools: Set[str],
) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {"enabled_tools": sorted(enabled_tools)}

    if schema_profile is not None:
        ctx["schema_summary"] = schema_profile.get("stats", {})
        ctx["join_graph"] = schema_profile.get("join_graph", {})

    if instance_profile is not None:
        ctx["instance_summary"] = {
            "tables": {
                t: {
                    "num_rows_sampled": prof.get("num_rows_sampled", 0),
                    "columns": {
                        c: {
                            "guessed_type": cp.get("guessed_type"),
                            "is_boolean_like": cp.get("is_boolean_like"),
                            "distinct_ratio": cp.get("distinct_ratio"),
                            "sample_values": (cp.get("sample_values", []) or [])[:5],
                        }
                        for c, cp in (prof.get("columns", {}) or {}).items()
                    },
                }
                for t, prof in (instance_profile.get("tables", {}) or {}).items()
            },
            "cross_table_value_overlap": (instance_profile.get("cross_table_value_overlap", []) or [])[:15],
        }

    if hypothesis_store is not None:
        items = [h.to_dict() for h in hypothesis_store.items.values()]
        ctx["hypothesis_summary"] = hypothesis_store.summary()
        ctx["hypotheses"] = compress_hypotheses_for_prompt(items, max_items=20)
        ctx["revision_guidance"] = hypothesis_store.build_revision_guidance(max_items=15)

    return ctx


def build_validation_payload(ok: bool, errors: List[str]) -> Dict[str, Any]:
    return {
        "ok": ok,
        "num_errors": len(errors),
        "errors": list(errors),
    }


def prepare_tool_evidence(
    schema_sql_text: str,
    sample_rows: Dict[str, List[Dict[str, Any]]],
    enabled_tools: Set[str],
):
    schema_profile: Optional[Dict[str, Any]] = None
    instance_profile: Optional[Dict[str, Any]] = None
    store: Optional[HypothesisStore] = None

    if "schema_profiler" in enabled_tools or "pattern_detector" in enabled_tools:
        schema_profile = SchemaProfiler().profile(schema_sql_text)

    if "instance_profiler" in enabled_tools or "pattern_detector" in enabled_tools:
        instance_profile = InstanceProfiler().profile(sample_rows)

    if "pattern_detector" in enabled_tools:
        if schema_profile is None:
            schema_profile = SchemaProfiler().profile(schema_sql_text)
        if instance_profile is None:
            instance_profile = InstanceProfiler().profile(sample_rows)
        hypotheses = PatternDetector().detect(schema_profile, instance_profile)
        store = HypothesisStore()
        for h in hypotheses:
            store.add(h)

    tool_context = build_tool_context(schema_profile, instance_profile, store, enabled_tools)
    return schema_profile, instance_profile, store, tool_context


def run_lite_verifier(draft_dict: Dict[str, Any], enabled_tools: Set[str], store: Optional[HypothesisStore]):
    lite_verification = None
    verification_feedback = None
    verifier_payload: Dict[str, Any]

    if "mapping_verifier_lite" in enabled_tools:
        lite_verifier = MappingVerifierLite()
        lite_verification = lite_verifier.verify_draft_dict(draft_dict)
        verifier_payload = lite_verification

        if store is not None and lite_verification is not None:
            verification_feedback = store.resolve_from_verifier_report(lite_verification)
    else:
        verifier_payload = {
            "ok": True,
            "num_errors": 0,
            "num_warnings": 0,
            "num_infos": 0,
            "issues": [],
            "errors": [],
            "warnings": [],
            "infos": [],
            "disabled": True,
        }

    return lite_verification, verification_feedback, verifier_payload
