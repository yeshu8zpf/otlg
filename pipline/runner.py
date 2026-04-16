from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from normalization.runner import normalize_model_output_robust
from ontology_draft import OntologyDraft

from .cache import try_load_cached_run
from .compare_adapter import run_burr_compare_wrapper
from .gt_artifacts import copy_gt_artifacts_for_scenario, resolve_gt_artifacts_for_scenario
from .io_utils import safe_exception_payload, write_json, write_text
from .llm import call_llm_json_stream
from .prompting import build_prompt
from .scenario import (
    extract_table_definitions,
    find_schema_sql,
    load_sample_rows_from_csv,
    read_text,
)
from .summary import summarize_top_level_counts
from .tools_context import (
    build_validation_payload,
    prepare_tool_evidence,
    run_lite_verifier,
)


def run_tool_augmented_baseline(
    scenario_dir: Path,
    model: str = "gpt-5.4-nano",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    max_rows_per_table: int = 3,
    timeout: float = 300.0,
    schema_path: Optional[Path] = None,
    fk_mode: str = "auto",
    enabled_tools: Optional[Set[str]] = None,
    include_schema_sql: bool = False,
    include_table_defs: bool = True,
    include_sample_rows: bool = False,
    include_tool_context: bool = True,
    fail_fast_on_invalid_draft: bool = False,
) -> Tuple[
    OntologyDraft,
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
]:
    if enabled_tools is None:
        enabled_tools = {"schema_profiler"}

    if schema_path is None:
        schema_path = find_schema_sql(scenario_dir, fk_mode=fk_mode)
    else:
        schema_path = schema_path.resolve()

    schema_sql_text = read_text(schema_path)
    table_defs = extract_table_definitions(schema_sql_text)

    need_sample_rows = (
        include_sample_rows
        or "instance_profiler" in enabled_tools
        or "pattern_detector" in enabled_tools
    )
    sample_rows = (
        load_sample_rows_from_csv(
            scenario_dir=scenario_dir,
            schema_sql_text=schema_sql_text,
            max_rows_per_table=max_rows_per_table,
        )
        if need_sample_rows
        else {}
    )

    schema_profile, instance_profile, store, tool_context = prepare_tool_evidence(
        schema_sql_text=schema_sql_text,
        sample_rows=sample_rows,
        enabled_tools=enabled_tools,
    )

    prompt = build_prompt(
        scenario_path=scenario_dir,
        schema_sql_text=schema_sql_text,
        table_defs=table_defs,
        sample_rows=sample_rows,
        tool_context=tool_context,
        include_schema_sql=include_schema_sql,
        include_table_defs=include_table_defs,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
    )

    raw_model_json, llm_meta = call_llm_json_stream(
        prompt=prompt,
        model=model,
        api_url=api_url,
        timeout=timeout,
    )

    normalized_model_json = normalize_model_output_robust(raw_model_json)
    draft = OntologyDraft.from_dict(normalized_model_json, already_normalized=True)

    validate_ok, validate_errors = draft.validate()
    validation_payload = build_validation_payload(validate_ok, validate_errors)

    _, verification_feedback, verifier_payload = run_lite_verifier(
        draft.to_dict(), enabled_tools, store
    )

    if fail_fast_on_invalid_draft and not validate_ok:
        raise RuntimeError(
            "Draft validation failed and fail_fast_on_invalid_draft=True. "
            f"num_errors={len(validate_errors)}"
        )

    burr_mapping = draft.to_burr_mapping()

    meta = {
        "scenario_dir": str(scenario_dir),
        "schema_path": str(schema_path),
        "fk_mode": fk_mode,
        "model": model,
        "api_url": api_url,
        "prompt_chars": len(prompt),
        "enabled_tools": sorted(enabled_tools),
        "prompt_includes": {
            "schema_sql": include_schema_sql,
            "table_defs": include_table_defs,
            "sample_rows": include_sample_rows,
            "tool_context": include_tool_context,
        },
        "raw_model_top_level_counts": summarize_top_level_counts(raw_model_json),
        "normalized_top_level_counts": summarize_top_level_counts(normalized_model_json),
        "draft_top_level_counts": summarize_top_level_counts(draft.to_dict()),
        "mapping_top_level_counts": summarize_top_level_counts(
            {
                "classes": burr_mapping.get("classes", []),
                "data_properties": burr_mapping.get("data_properties", []),
                "object_properties": burr_mapping.get("object_properties", []),
                "subclass_relations": [],
                "class_mappings": [],
                "data_property_mappings": [],
                "object_property_mappings": [],
            }
        ),
        "draft_validation": validation_payload,
        "lite_verification_summary": {
            "ok": verifier_payload.get("ok"),
            "num_errors": verifier_payload.get("num_errors", 0),
            "num_warnings": verifier_payload.get("num_warnings", 0),
            "num_infos": verifier_payload.get("num_infos", 0),
        },
        "verification_feedback": verification_feedback,
        "tool_context_summary": {
            "schema_summary": schema_profile.get("stats", {}) if schema_profile else {},
            "hypothesis_summary": store.summary() if store else {},
            "num_cross_table_value_overlap": len(
                (instance_profile.get("cross_table_value_overlap", []) if instance_profile else [])
            ),
        },
        "llm_meta": llm_meta,
        "normalization_report": draft.normalization_report(),
        "fail_fast_on_invalid_draft": fail_fast_on_invalid_draft,
    }

    tool_artifacts = {
        "schema_profile": schema_profile,
        "instance_profile": instance_profile,
        "hypotheses": store.to_dict() if store else None,
        "tool_context": tool_context,
        "prompt": prompt,
        "verification_feedback": verification_feedback,
    }

    return (
        draft,
        burr_mapping,
        meta,
        raw_model_json,
        normalized_model_json,
        validation_payload,
        verifier_payload,
        tool_artifacts,
    )


def execute_run(
    *,
    project_root: Path,
    scenario_dir: Path,
    schema_path: Optional[Path],
    fk_mode: str,
    model: str,
    api_url: str,
    max_rows_per_table: int,
    timeout: float,
    out_dir: Path,
    run_burr_compare: bool,
    meta_path: Optional[Path],
    database_name: Optional[str],
    enabled_tools: Set[str],
    include_schema_sql: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
    copy_gt_artifacts: bool,
    fail_fast_on_invalid_draft: bool,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    cached = try_load_cached_run(out_dir)

    if cached is not None:
        (
            draft,
            burr_mapping,
            meta,
            raw_model_json,
            normalized_model_json,
            validation_payload,
            verifier_payload,
            tool_artifacts,
        ) = cached
        print(f"[CACHE HIT] Reusing existing outputs from {out_dir}")
    else:
        try:
            (
                draft,
                burr_mapping,
                meta,
                raw_model_json,
                normalized_model_json,
                validation_payload,
                verifier_payload,
                tool_artifacts,
            ) = run_tool_augmented_baseline(
                scenario_dir=scenario_dir,
                schema_path=schema_path,
                fk_mode=fk_mode,
                model=model,
                api_url=api_url,
                max_rows_per_table=max_rows_per_table,
                timeout=timeout,
                enabled_tools=enabled_tools,
                include_schema_sql=include_schema_sql,
                include_table_defs=True,
                include_sample_rows=include_sample_rows,
                include_tool_context=include_tool_context,
                fail_fast_on_invalid_draft=fail_fast_on_invalid_draft,
            )
        except Exception as e:
            fail_meta = {
                "scenario_dir": str(scenario_dir),
                "schema_path": str(schema_path) if schema_path else None,
                "fk_mode": fk_mode,
                "model": model,
                "api_url": api_url,
                "enabled_tools": sorted(enabled_tools),
                "error": safe_exception_payload(e),
            }
            write_json(out_dir / "failed.meta.json", fail_meta)
            raise

    write_json(out_dir / "raw_model.json", raw_model_json)
    write_json(out_dir / "normalized.json", normalized_model_json)
    write_json(out_dir / "draft.json", draft.to_dict())
    write_json(out_dir / "validation.json", validation_payload)
    write_json(out_dir / "verifier.json", verifier_payload)
    write_json(out_dir / "mapping.json", burr_mapping)

    if copy_gt_artifacts:
        meta["gt_artifacts"] = copy_gt_artifacts_for_scenario(scenario_dir, out_dir)
    else:
        meta["gt_artifacts"] = resolve_gt_artifacts_for_scenario(scenario_dir)

    write_json(out_dir / "meta.json", meta)

    if tool_artifacts["schema_profile"] is not None:
        write_json(out_dir / "schema_profile.json", tool_artifacts["schema_profile"])
    if tool_artifacts["instance_profile"] is not None:
        write_json(out_dir / "instance_profile.json", tool_artifacts["instance_profile"])
    if tool_artifacts["hypotheses"] is not None:
        write_json(out_dir / "hypotheses.json", tool_artifacts["hypotheses"])

    write_json(out_dir / "tool_context.json", tool_artifacts["tool_context"])
    write_text(out_dir / "prompt.md", tool_artifacts["prompt"])

    if run_burr_compare:
        try:
            compare_output_path = out_dir / "compare.json"
            compare_temp_dir = out_dir / "compare_preprocessed"

            compare_result = run_burr_compare_wrapper(
                project_root=project_root,
                scenario_dir=scenario_dir,
                prediction_path=out_dir / "mapping.json",
                output_path=compare_output_path,
                gt_path=None,
                gt_kind="ttl",
                meta_path=meta_path,
                temp_dir=compare_temp_dir,
            )
            write_json(compare_output_path, compare_result)
        except Exception as e:
            write_json(out_dir / "compare_error.json", safe_exception_payload(e))

    print(f"[OK] scenario: {scenario_dir}")
    print(f"[OK] raw model: {out_dir / 'raw_model.json'}")
    print(f"[OK] normalized: {out_dir / 'normalized.json'}")
    print(f"[OK] draft: {out_dir / 'draft.json'}")
    print(f"[OK] validation: {out_dir / 'validation.json'}")
    print(f"[OK] verifier: {out_dir / 'verifier.json'}")
    print(f"[OK] mapping: {out_dir / 'mapping.json'}")
    print(f"[OK] meta: {out_dir / 'meta.json'}")
    print(f"[OK] tool context: {out_dir / 'tool_context.json'}")
    print(f"[OK] prompt: {out_dir / 'prompt.md'}")

    if (out_dir / "schema_profile.json").exists():
        print(f"[OK] schema profile: {out_dir / 'schema_profile.json'}")
    if (out_dir / "instance_profile.json").exists():
        print(f"[OK] instance profile: {out_dir / 'instance_profile.json'}")
    if (out_dir / "hypotheses.json").exists():
        print(f"[OK] hypotheses: {out_dir / 'hypotheses.json'}")

    if run_burr_compare:
        if (out_dir / "compare.json").exists():
            print(f"[OK] compare: {out_dir / 'compare.json'}")
        elif (out_dir / "compare_error.json").exists():
            print(f"[WARN] compare failed: {out_dir / 'compare_error.json'}")
