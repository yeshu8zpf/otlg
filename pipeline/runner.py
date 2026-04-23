from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from normalization.runner import normalize_model_output_robust
from ontology_draft.draft import OntologyDraft

from .compare_adapter import run_burr_compare_wrapper
from .gt_artifacts import copy_gt_artifacts_for_scenario, resolve_gt_artifacts_for_scenario
from .io_utils import read_json, safe_exception_payload, write_json, write_text
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


STAGE_ORDER = {
    "llm": 0,
    "normalize": 1,
    "draft": 2,
    "mapping": 3,
    "compare": 4,
}


def _stage_paths(out_dir: Path) -> Dict[str, Path]:
    return {
        "raw_model": out_dir / "raw_model.json",
        "normalized": out_dir / "normalized.json",
        "draft": out_dir / "draft.json",
        "validation": out_dir / "validation.json",
        "verifier": out_dir / "verifier.json",
        "mapping": out_dir / "mapping.json",
        "meta": out_dir / "meta.json",
        "schema_profile": out_dir / "schema_profile.json",
        "instance_profile": out_dir / "instance_profile.json",
        "hypotheses": out_dir / "hypotheses.json",
        "tool_context": out_dir / "tool_context.json",
        "prompt": out_dir / "prompt.md",
        "compare": out_dir / "compare.json",
        "compare_error": out_dir / "compare_error.json",
        "failed_meta": out_dir / "failed.meta.json",
        "compare_preprocessed": out_dir / "compare_preprocessed",
    }


def _should_run(current_stage: str, start_stage: str) -> bool:
    return STAGE_ORDER[current_stage] >= STAGE_ORDER[start_stage]


def _infer_start_stage(paths: Dict[str, Path], run_burr_compare: bool) -> Optional[str]:
    if not paths["raw_model"].exists():
        return "llm"
    if not paths["normalized"].exists():
        return "normalize"
    if not paths["draft"].exists():
        return "draft"
    if not paths["mapping"].exists():
        return "mapping"
    if run_burr_compare and not paths["compare"].exists():
        return "compare"
    return None


def _load_prompt_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


from compare.burr_compare.gt_resolution import merge_mapping_json_files

def _resolve_pipeline_gt_for_compare(scenario_dir: Path, out_dir: Path) -> tuple[Path | None, str]:
    mappings_dir = scenario_dir / "mappings"
    if mappings_dir.exists() and mappings_dir.is_dir():
        json_parts = sorted(
            p for p in mappings_dir.glob("*.json")
            if p.name != "meta.json"
        )
        if json_parts:
            merged_gt_path = out_dir / "gt_merged.json"
            merged_gt = merge_mapping_json_files(json_parts)
            write_json(merged_gt_path, merged_gt)
            return merged_gt_path, "json"

    # fallback: let compare resolve ttl by itself
    return None, "ttl"

def _build_shared_inputs(
    *,
    scenario_dir: Path,
    schema_path: Optional[Path],
    fk_mode: str,
    max_rows_per_table: int,
    enabled_tools: Set[str],
    include_schema_sql: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
) -> Dict[str, Any]:
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
        include_table_defs=True,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
    )

    return {
        "schema_path": schema_path,
        "schema_sql_text": schema_sql_text,
        "table_defs": table_defs,
        "sample_rows": sample_rows,
        "schema_profile": schema_profile,
        "instance_profile": instance_profile,
        "store": store,
        "tool_context": tool_context,
        "prompt": prompt,
    }


def _build_meta(
    *,
    scenario_dir: Path,
    schema_path: Path,
    fk_mode: str,
    model: str,
    api_url: str,
    enabled_tools: Set[str],
    include_schema_sql: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
    prompt: str,
    raw_model_json: Dict[str, Any],
    normalized_model_json: Dict[str, Any],
    draft: OntologyDraft,
    burr_mapping: Dict[str, Any],
    validation_payload: Dict[str, Any],
    verifier_payload: Dict[str, Any],
    verification_feedback: Dict[str, Any],
    schema_profile: Optional[Dict[str, Any]],
    instance_profile: Optional[Dict[str, Any]],
    store: Any,
    llm_meta: Dict[str, Any],
    fail_fast_on_invalid_draft: bool,
    resume: str,
    requested_start_from: Optional[str],
    effective_start_from: str,
    reused_files: list[str],
    rerun_files: list[str],
) -> Dict[str, Any]:
    return {
        "scenario_dir": str(scenario_dir),
        "schema_path": str(schema_path),
        "fk_mode": fk_mode,
        "model": model,
        "api_url": api_url,
        "prompt_chars": len(prompt),
        "enabled_tools": sorted(enabled_tools),
        "prompt_includes": {
            "schema_sql": include_schema_sql,
            "table_defs": True,
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
        "resume": resume,
        "requested_start_from": requested_start_from,
        "effective_start_from": effective_start_from,
        "reused_files": reused_files,
        "rerun_files": rerun_files,
    }


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

    shared = _build_shared_inputs(
        scenario_dir=scenario_dir,
        schema_path=schema_path,
        fk_mode=fk_mode,
        max_rows_per_table=max_rows_per_table,
        enabled_tools=enabled_tools,
        include_schema_sql=include_schema_sql,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
    )

    raw_model_json, llm_meta = call_llm_json_stream(
        prompt=shared["prompt"],
        model=model,
        api_url=api_url,
        timeout=timeout,
    )

    normalized_model_json = normalize_model_output_robust(raw_model_json)
    draft = OntologyDraft.from_dict(normalized_model_json, already_normalized=True)

    validate_ok, validate_errors = draft.validate()
    validation_payload = build_validation_payload(validate_ok, validate_errors)

    _, verification_feedback, verifier_payload = run_lite_verifier(
        draft.to_dict(), enabled_tools, shared["store"]
    )

    if fail_fast_on_invalid_draft and not validate_ok:
        raise RuntimeError(
            "Draft validation failed and fail_fast_on_invalid_draft=True. "
            f"num_errors={len(validate_errors)}"
        )

    burr_mapping = draft.to_burr_mapping()

    meta = _build_meta(
        scenario_dir=scenario_dir,
        schema_path=shared["schema_path"],
        fk_mode=fk_mode,
        model=model,
        api_url=api_url,
        enabled_tools=enabled_tools,
        include_schema_sql=include_schema_sql,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
        prompt=shared["prompt"],
        raw_model_json=raw_model_json,
        normalized_model_json=normalized_model_json,
        draft=draft,
        burr_mapping=burr_mapping,
        validation_payload=validation_payload,
        verifier_payload=verifier_payload,
        verification_feedback=verification_feedback,
        schema_profile=shared["schema_profile"],
        instance_profile=shared["instance_profile"],
        store=shared["store"],
        llm_meta=llm_meta,
        fail_fast_on_invalid_draft=fail_fast_on_invalid_draft,
        resume="off",
        requested_start_from=None,
        effective_start_from="llm",
        reused_files=[],
        rerun_files=["raw_model.json", "normalized.json", "draft.json", "mapping.json"],
    )

    tool_artifacts = {
        "schema_profile": shared["schema_profile"],
        "instance_profile": shared["instance_profile"],
        "hypotheses": shared["store"].to_dict() if shared["store"] else None,
        "tool_context": shared["tool_context"],
        "prompt": shared["prompt"],
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
    resume: str = "auto",
    start_from: Optional[str] = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _stage_paths(out_dir)

    if start_from is not None:
        effective_start_from = start_from
    elif resume == "auto":
        inferred = _infer_start_stage(paths, run_burr_compare)
        effective_start_from = inferred if inferred is not None else "compare"
    else:
        effective_start_from = "llm"

    reused_files: list[str] = []
    rerun_files: list[str] = []

    shared = _build_shared_inputs(
        scenario_dir=scenario_dir,
        schema_path=schema_path,
        fk_mode=fk_mode,
        max_rows_per_table=max_rows_per_table,
        enabled_tools=enabled_tools,
        include_schema_sql=include_schema_sql,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
    )

    schema_path_resolved = shared["schema_path"]
    prompt = shared["prompt"]
    schema_profile = shared["schema_profile"]
    instance_profile = shared["instance_profile"]
    store = shared["store"]
    tool_context = shared["tool_context"]


    # Persist pre-LLM artifacts immediately so failures in the LLM stage
    # still leave reproducible inputs on disk.
    write_text(paths["prompt"], prompt)
    write_json(paths["tool_context"], tool_context)

    if schema_profile is not None:
        write_json(paths["schema_profile"], schema_profile)
    if instance_profile is not None:
        write_json(paths["instance_profile"], instance_profile)
    if store is not None:
        write_json(paths["hypotheses"], store.to_dict())

    raw_model_json: Dict[str, Any]
    llm_meta: Dict[str, Any]

    if _should_run("llm", effective_start_from):
        rerun_files.append("raw_model.json")
        try:
            raw_model_json, llm_meta = call_llm_json_stream(
                prompt=prompt,
                model=model,
                api_url=api_url,
                timeout=timeout,
            )
            write_json(paths["raw_model"], raw_model_json)
        except Exception as e:
            fail_meta = {
                "scenario_dir": str(scenario_dir),
                "schema_path": str(schema_path_resolved) if schema_path_resolved else None,
                "fk_mode": fk_mode,
                "model": model,
                "api_url": api_url,
                "enabled_tools": sorted(enabled_tools),
                "resume": resume,
                "requested_start_from": start_from,
                "effective_start_from": effective_start_from,
                "error": safe_exception_payload(e),
            }
            write_json(paths["failed_meta"], fail_meta)
            raise
    else:
        reused_files.append("raw_model.json")
        raw_model_json = read_json(paths["raw_model"])
        prev_meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
        llm_meta = prev_meta.get("llm_meta", {})

    normalized_model_json: Dict[str, Any]
    if _should_run("normalize", effective_start_from):
        rerun_files.append("normalized.json")
        normalized_model_json = normalize_model_output_robust(raw_model_json)
        write_json(paths["normalized"], normalized_model_json)
    else:
        reused_files.append("normalized.json")
        normalized_model_json = read_json(paths["normalized"])

    draft: OntologyDraft
    if _should_run("draft", effective_start_from):
        rerun_files.extend(["draft.json", "validation.json", "verifier.json"])
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

        write_json(paths["draft"], draft.to_dict())
        write_json(paths["validation"], validation_payload)
        write_json(paths["verifier"], verifier_payload)
    else:
        reused_files.extend(["draft.json", "validation.json", "verifier.json"])
        draft = OntologyDraft.from_dict(read_json(paths["draft"]), already_normalized=True)
        validation_payload = read_json(paths["validation"])
        verifier_payload = read_json(paths["verifier"])
        prev_meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
        verification_feedback = prev_meta.get("verification_feedback", {})

    burr_mapping: Dict[str, Any]
    if _should_run("mapping", effective_start_from):
        rerun_files.append("mapping.json")
        burr_mapping = draft.to_burr_mapping()
        write_json(paths["mapping"], burr_mapping)
    else:
        reused_files.append("mapping.json")
        burr_mapping = read_json(paths["mapping"])

    meta = _build_meta(
        scenario_dir=scenario_dir,
        schema_path=schema_path_resolved,
        fk_mode=fk_mode,
        model=model,
        api_url=api_url,
        enabled_tools=enabled_tools,
        include_schema_sql=include_schema_sql,
        include_sample_rows=include_sample_rows,
        include_tool_context=include_tool_context,
        prompt=prompt,
        raw_model_json=raw_model_json,
        normalized_model_json=normalized_model_json,
        draft=draft,
        burr_mapping=burr_mapping,
        validation_payload=validation_payload,
        verifier_payload=verifier_payload,
        verification_feedback=verification_feedback,
        schema_profile=schema_profile,
        instance_profile=instance_profile,
        store=store,
        llm_meta=llm_meta,
        fail_fast_on_invalid_draft=fail_fast_on_invalid_draft,
        resume=resume,
        requested_start_from=start_from,
        effective_start_from=effective_start_from,
        reused_files=reused_files,
        rerun_files=rerun_files,
    )

    if copy_gt_artifacts:
        meta["gt_artifacts"] = copy_gt_artifacts_for_scenario(scenario_dir, out_dir)
    else:
        meta["gt_artifacts"] = resolve_gt_artifacts_for_scenario(scenario_dir)

    write_json(paths["meta"], meta)

    if schema_profile is not None:
        write_json(paths["schema_profile"], schema_profile)
    if instance_profile is not None:
        write_json(paths["instance_profile"], instance_profile)
    if store is not None:
        write_json(paths["hypotheses"], store.to_dict())


    if run_burr_compare:
        if _should_run("compare", effective_start_from):
            rerun_files.append("compare.json")
            try:
                gt_path_for_compare, gt_kind_for_compare = _resolve_pipeline_gt_for_compare(
                    scenario_dir=scenario_dir,
                    out_dir=out_dir,
                )

                compare_result = run_burr_compare_wrapper(
                    project_root=project_root,
                    scenario_dir=scenario_dir,
                    prediction_path=paths["mapping"],
                    output_path=paths["compare"],
                    gt_path=gt_path_for_compare,
                    gt_kind=gt_kind_for_compare,
                    meta_path=meta_path,
                    temp_dir=paths["compare_preprocessed"],
                )
                write_json(paths["compare"], compare_result)
                if paths["compare_error"].exists():
                    paths["compare_error"].unlink()
            except Exception as e:
                write_json(paths["compare_error"], safe_exception_payload(e))
        else:
            if paths["compare"].exists():
                reused_files.append("compare.json")

    print(f"[OK] scenario: {scenario_dir}")
    print(f"[OK] effective start: {effective_start_from}")
    print(f"[OK] reused files: {reused_files}")
    print(f"[OK] rerun files: {rerun_files}")
    print(f"[OK] raw model: {paths['raw_model']}")
    print(f"[OK] normalized: {paths['normalized']}")
    print(f"[OK] draft: {paths['draft']}")
    print(f"[OK] validation: {paths['validation']}")
    print(f"[OK] verifier: {paths['verifier']}")
    print(f"[OK] mapping: {paths['mapping']}")
    print(f"[OK] meta: {paths['meta']}")
    print(f"[OK] tool context: {paths['tool_context']}")
    print(f"[OK] prompt: {paths['prompt']}")

    if paths["schema_profile"].exists():
        print(f"[OK] schema profile: {paths['schema_profile']}")
    if paths["instance_profile"].exists():
        print(f"[OK] instance profile: {paths['instance_profile']}")
    if paths["hypotheses"].exists():
        print(f"[OK] hypotheses: {paths['hypotheses']}")

    if run_burr_compare:
        if paths["compare"].exists():
            print(f"[OK] compare: {paths['compare']}")
        elif paths["compare_error"].exists():
            print(f"[WARN] compare failed: {paths['compare_error']}")