from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from .draft_prompt_view import (
    init_empty_draft,
    bump_draft_version,
    build_draft_prompt_view,
)
from .table_update_patching import build_table_update_messages
from .schema_incremental import build_incremental_context_from_schema_file
from .incremental_normalize import (
    normalize_internal_draft_robust,
    normalize_patch_robust,
)


DRAFT_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]


@dataclass
class OrchestratorConfig:
    schema_path: Path
    out_dir: Path
    model: str
    api_url: str
    timeout: float = 300.0
    start_step: int = 0
    end_step: Optional[int] = None
    include_standard_subset: bool = True
    persist_full_incremental_context: bool = True
    run_llm: bool = True
    api_key: str = "gpt"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_paths(out_dir: Path) -> Dict[str, Path]:
    return {
        "incremental_context": out_dir / "incremental_context.json",
        "global_draft": out_dir / "global_draft.json",
        "table_runs": out_dir / "table_runs",
        "decision_log": out_dir / "decision_log.json",
        "meta": out_dir / "meta.json",
    }


def build_step_paths(table_runs_dir: Path, step_index: int, table_name: str) -> Dict[str, Path]:
    step_dir = table_runs_dir / f"{step_index:03d}_{table_name}"
    return {
        "dir": step_dir,
        "incremental_step": step_dir / "incremental_step.json",
        "draft_prompt_view": step_dir / "draft_prompt_view.json",
        "messages": step_dir / "messages.json",
        "prompt_text": step_dir / "prompt.txt",
        "raw_patch": step_dir / "raw_patch.json",
        "llm_meta": step_dir / "llm_meta.json",
        "normalized_patch": step_dir / "normalized_patch.json",
        "step_meta": step_dir / "step_meta.json",
    }


def render_messages(messages: List[Dict[str, str]]) -> str:
    chunks: List[str] = []
    for m in messages:
        chunks.append(f"[{m['role'].upper()}]\n{m['content']}")
    return "\n\n".join(chunks)


def user_prompt_from_messages(messages: List[Dict[str, str]]) -> str:
    user_parts = [m["content"] for m in messages if m.get("role") == "user"]
    return "\n\n".join(user_parts)


def append_decision_log(
    decision_log_path: Path,
    *,
    step_index: int,
    table_name: str,
    normalized_patch: Dict[str, Any],
) -> None:
    if decision_log_path.exists():
        rows = read_json(decision_log_path)
    else:
        rows = []

    rows.append(
        {
            "step_index": step_index,
            "table_name": table_name,
            "decision_summary": normalized_patch.get("decision_summary", []),
            "remaining_ambiguities": normalized_patch.get("remaining_ambiguities", []),
            "needs_probe": normalized_patch.get("needs_probe", []),
            "num_additions": _count_patch_items(normalized_patch.get("proposed_additions", {})),
            "num_revisions": _count_patch_items(normalized_patch.get("proposed_revisions", {})),
            "num_rejections": len(normalized_patch.get("proposed_rejections", [])),
            "num_merges": len(normalized_patch.get("proposed_merges", [])),
        }
    )
    write_json(decision_log_path, rows)


def _count_patch_items(section: Dict[str, Any]) -> int:
    if not isinstance(section, dict):
        return 0
    total = 0
    for v in section.values():
        if isinstance(v, list):
            total += len(v)
    return total


def apply_normalized_patch_to_draft(
    draft: Dict[str, Any],
    normalized_patch: Dict[str, Any],
    *,
    table_name: str,
    incremental_step: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    updated = json.loads(json.dumps(draft))

    for field in DRAFT_SECTION_FIELDS:
        updated.setdefault(field, [])
    updated.setdefault("draft_metadata", {})
    updated.setdefault("rejected_candidates", [])
    updated.setdefault("open_issues", [])

    additions = normalized_patch.get("proposed_additions", {}) or {}
    for field in DRAFT_SECTION_FIELDS:
        for item in additions.get(field, []) or []:
            _upsert_item(updated[field], item, field=field)

    revisions = normalized_patch.get("proposed_revisions", {}) or {}
    for field in DRAFT_SECTION_FIELDS:
        for rev in revisions.get(field, []) or []:
            target_id = rev.get("target_id")
            updated_fields = rev.get("updated_fields", {}) or {}
            if not target_id or not updated_fields:
                continue

            applied = _apply_revision(updated[field], target_id, updated_fields, field=field)
            if not applied:
                updated["open_issues"].append(
                    {
                        "issue_type": "unapplied_revision",
                        "related_table": table_name,
                        "description": f"Could not find target_id={target_id} in section={field}",
                        "payload": rev,
                    }
                )

    for rej in normalized_patch.get("proposed_rejections", []) or []:
        updated["rejected_candidates"].append(
            {
                "candidate_type": rej.get("candidate_type"),
                "target": rej.get("target"),
                "from_table": table_name,
                "reason": rej.get("reason"),
                "status": "rejected",
            }
        )

    merges = normalized_patch.get("proposed_merges", []) or []
    if merges:
        updated["open_issues"].append(
            {
                "issue_type": "pending_merge_application",
                "related_table": table_name,
                "description": "Patch proposed merges that require a stronger merge engine.",
                "payload": merges,
            }
        )

    for amb in normalized_patch.get("remaining_ambiguities", []) or []:
        updated["open_issues"].append(
            {
                "issue_type": "remaining_ambiguity",
                "related_table": table_name,
                "description": amb,
            }
        )

    for probe in normalized_patch.get("needs_probe", []) or []:
        updated["open_issues"].append(
            {
                "issue_type": "needs_probe",
                "related_table": table_name,
                "description": probe.get("question"),
                "payload": probe,
            }
        )

    bump_draft_version(updated, table_name, action="updated")
    updated = normalize_internal_draft_robust(updated, incremental_step=incremental_step)
    validate_internal_draft(updated)
    return updated


def _upsert_item(existing_list: List[Dict[str, Any]], new_item: Dict[str, Any], *, field: str) -> None:
    new_key = _draft_item_key(field, new_item)
    if not new_key:
        existing_list.append(new_item)
        return

    for i, old_item in enumerate(existing_list):
        old_key = _draft_item_key(field, old_item)
        if old_key == new_key:
            existing_list[i] = _merge_draft_items(old_item, new_item)
            return

    existing_list.append(new_item)


def _apply_revision(
    existing_list: List[Dict[str, Any]],
    target_id: str,
    updated_fields: Dict[str, Any],
    *,
    field: str,
) -> bool:
    for i, item in enumerate(existing_list):
        if _matches_target_id(item, target_id, field=field):
            existing_list[i] = _merge_draft_items(item, updated_fields)
            return True
    return False


def _matches_target_id(item: Dict[str, Any], target_id: str, *, field: str) -> bool:
    if field in {"classes", "data_properties", "object_properties"}:
        return str(item.get("id", "")) == str(target_id)

    if field == "subclass_relations":
        return str(item.get("id", "")) == str(target_id)

    if field == "class_mappings":
        return str(item.get("mapping_id", "")) == str(target_id) or str(item.get("class_id", "")) == str(target_id)

    if field == "data_property_mappings":
        return str(item.get("mapping_id", "")) == str(target_id) or str(item.get("data_property_id", "")) == str(target_id)

    if field == "object_property_mappings":
        return str(item.get("mapping_id", "")) == str(target_id) or str(item.get("object_property_id", "")) == str(target_id)

    return False


def _merge_draft_items(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    result = json.loads(json.dumps(old))

    FORCE_OVERRIDE_FIELDS = {
        "class_id",
        "from_tables",
        "identifier_kind",
        "identifier_columns",
        "bnode_id_columns",
        "instance_id_template",
        "mapping_id",
        "applies_to_class",
        "source_table",
        "source_columns",
        "value_kind",
        "join_paths",
        "condition",
        "from_class",
        "to_class",
        "target_type",
    }

    for k, v_new in new.items():
        if k not in result:
            result[k] = v_new
            continue

        v_old = result[k]

        if isinstance(v_old, dict) and isinstance(v_new, dict):
            result[k] = _merge_draft_items(v_old, v_new)
            continue

        if isinstance(v_old, list) and isinstance(v_new, list):
            result[k] = _merge_lists(v_old, v_new)
            continue

        if k in FORCE_OVERRIDE_FIELDS:
            if _is_nonempty(v_new):
                result[k] = v_new
            continue

        if _is_empty(v_old) and _is_nonempty(v_new):
            result[k] = v_new

    return result


def _merge_lists(old_list: List[Any], new_list: List[Any]) -> List[Any]:
    out: List[Any] = []
    seen = set()
    for x in old_list + new_list:
        key = _stable_key(x)
        if key in seen:
            continue
        seen.add(key)
        out.append(x)
    return out


def _stable_key(x: Any) -> str:
    try:
        return json.dumps(x, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(x)


def _is_empty(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}


def _is_nonempty(v: Any) -> bool:
    return not _is_empty(v)


def _draft_item_key(field: str, item: Dict[str, Any]) -> str:
    if field in {"classes", "data_properties", "object_properties"}:
        return str(item.get("id") or "")

    if field == "subclass_relations":
        return str(item.get("id") or f"{item.get('child_class')}->{item.get('parent_class')}")

    if field == "class_mappings":
        return str(item.get("mapping_id") or item.get("class_id") or "")

    if field == "data_property_mappings":
        return str(item.get("mapping_id") or item.get("data_property_id") or "")

    if field == "object_property_mappings":
        return str(item.get("mapping_id") or item.get("object_property_id") or "")

    return ""


def validate_internal_draft(draft: Dict[str, Any]) -> None:
    for i, cm in enumerate(draft.get("class_mappings", []) or []):
        if not cm.get("class_id"):
            raise ValueError(f"class_mappings[{i}] missing class_id: {cm}")

        kind = cm.get("identifier_kind", "")
        if kind in {"uri_pattern", "uripattern"}:
            if not cm.get("instance_id_template") and not cm.get("identifier_columns"):
                raise ValueError(f"class_mappings[{i}] uri-pattern style mapping has no template/identifier columns: {cm}")

        if kind in {"bnode", "bnodeidcolumns"}:
            if not cm.get("bnode_id_columns") and not cm.get("identifier_columns"):
                raise ValueError(f"class_mappings[{i}] bnode mapping has no identity columns: {cm}")

    for i, dpm in enumerate(draft.get("data_property_mappings", []) or []):
        if not dpm.get("data_property_id"):
            raise ValueError(f"data_property_mappings[{i}] missing data_property_id: {dpm}")

        if not dpm.get("applies_to_class"):
            raise ValueError(f"data_property_mappings[{i}] missing applies_to_class: {dpm}")

        value_kind = dpm.get("value_kind", "")
        if value_kind == "column" and not dpm.get("source_columns"):
            raise ValueError(f"data_property_mappings[{i}] value_kind=column but source_columns empty: {dpm}")

    for i, opm in enumerate(draft.get("object_property_mappings", []) or []):
        if not opm.get("object_property_id"):
            raise ValueError(f"object_property_mappings[{i}] missing object_property_id: {opm}")

        if not opm.get("from_class"):
            raise ValueError(f"object_property_mappings[{i}] missing from_class: {opm}")

        if opm.get("target_type") != "resource" and not opm.get("to_class"):
            raise ValueError(f"object_property_mappings[{i}] missing to_class for non-resource relation: {opm}")


def prepare_incremental_context(config: OrchestratorConfig) -> Dict[str, Any]:
    incremental_context = build_incremental_context_from_schema_file(config.schema_path)
    paths = build_paths(config.out_dir)
    if config.persist_full_incremental_context:
        write_json(paths["incremental_context"], incremental_context)
    return incremental_context


def run_table_incremental_orchestrator(
    *,
    config: OrchestratorConfig,
    call_llm_json_stream_fn,
    initial_draft: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    paths = build_paths(config.out_dir)
    config.out_dir.mkdir(parents=True, exist_ok=True)

    incremental_context = prepare_incremental_context(config)

    draft = initial_draft if initial_draft is not None else init_empty_draft()
    draft = normalize_internal_draft_robust(draft)
    write_json(paths["global_draft"], draft)

    steps = incremental_context.get("incremental_steps", [])
    end_step = len(steps) if config.end_step is None else min(config.end_step, len(steps))

    meta = {
        "schema_path": str(config.schema_path),
        "out_dir": str(config.out_dir),
        "model": config.model,
        "api_url": config.api_url,
        "timeout": config.timeout,
        "start_step": config.start_step,
        "end_step": end_step,
        "num_total_steps": len(steps),
        "executed_steps": [],
        "normalization_enabled": True,
    }

    for step in steps[config.start_step:end_step]:
        step_index = int(step["step_index"])
        table_name = step["new_table"]
        spaths = build_step_paths(paths["table_runs"], step_index, table_name)

        write_json(spaths["incremental_step"], step)

        draft_prompt_view = build_draft_prompt_view(draft, step)
        write_json(spaths["draft_prompt_view"], draft_prompt_view)

        messages = build_table_update_messages(
            incremental_step=step,
            draft_prompt_view=draft_prompt_view,
            include_standard_subset=config.include_standard_subset,
        )
        write_json(spaths["messages"], messages)

        prompt_text = user_prompt_from_messages(messages)
        write_text(spaths["prompt_text"], render_messages(messages))

        step_meta = {
            "step_index": step_index,
            "table_name": table_name,
            "related_existing_tables": step.get("related_existing_tables", []),
            "requires_multi_table_reasoning": step.get("multi_table_signals", {}).get("requires_multi_table_reasoning", False),
            "llm_called": config.run_llm,
            "normalization_applied": True,
        }

        if config.run_llm:
            if spaths["raw_patch"].exists():
                raw_patch = read_json(spaths["raw_patch"])
                llm_meta = read_json(spaths["llm_meta"]) if spaths["llm_meta"].exists() else {}
                step_meta["llm_called"] = False
                step_meta["raw_patch_reused"] = True
            else:
                raw_patch, llm_meta = raw_patch, llm_meta = call_llm_json_stream_fn(
                                                                    prompt=prompt_text,
                                                                    model=config.model,
                                                                    api_url=config.api_url,
                                                                    timeout=config.timeout,
                                                                    api_key=config.api_key,
                                                                )
                write_json(spaths["raw_patch"], raw_patch)
                write_json(spaths["llm_meta"], llm_meta)
                step_meta["llm_called"] = True
                step_meta["raw_patch_reused"] = False

            normalized_patch = normalize_patch_robust(raw_patch, incremental_step=step)
            write_json(spaths["normalized_patch"], normalized_patch)

            draft = apply_normalized_patch_to_draft(
                draft,
                normalized_patch,
                table_name=table_name,
                incremental_step=step,
            )
            write_json(paths["global_draft"], draft)

            append_decision_log(
                paths["decision_log"],
                step_index=step_index,
                table_name=table_name,
                normalized_patch=normalized_patch,
            )

            step_meta["patch_counts"] = {
                "additions": _count_patch_items(normalized_patch.get("proposed_additions", {})),
                "revisions": _count_patch_items(normalized_patch.get("proposed_revisions", {})),
                "rejections": len(normalized_patch.get("proposed_rejections", [])),
                "merges": len(normalized_patch.get("proposed_merges", [])),
            }

        write_json(spaths["step_meta"], step_meta)
        meta["executed_steps"].append(
            {
                "step_index": step_index,
                "table_name": table_name,
                "llm_called": config.run_llm,
            }
        )
        write_json(paths["meta"], meta)

    return {
        "incremental_context_path": str(paths["incremental_context"]),
        "global_draft_path": str(paths["global_draft"]),
        "decision_log_path": str(paths["decision_log"]),
        "meta_path": str(paths["meta"]),
        "table_runs_dir": str(paths["table_runs"]),
    }