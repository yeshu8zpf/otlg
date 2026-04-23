
from __future__ import annotations

"""
table_incremental_orchestrator.py

A minimal orchestrator for table-centric incremental ontology drafting.

It wires together:
- schema_incremental.py
- draft_prompt_view.py
- table_update_patching.py

Goal
----
For each incremental table-addition step:
1. load / maintain a global internal draft
2. build a compact draft prompt view
3. construct a table-update prompt
4. optionally call an LLM
5. normalize the returned patch
6. save all intermediate artifacts

This file is intentionally designed to be easy to plug into an existing pipeline.

What it does NOT do yet
-----------------------
- sophisticated patch-to-draft application
- global reconciliation / merge resolution
- advanced verifier loop
- retry / fallback logic
- direct Burr compare integration

Those can be layered on top later.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import json

from draft_prompt_view import (
    init_empty_draft,
    bump_draft_version,
    build_draft_prompt_view,
)
from table_update_patching import (
    build_table_update_messages,
    build_table_update_payload,
    normalize_patch_output,
)
from schema_incremental import build_incremental_context_from_schema_file


# ============================================================
# Types
# ============================================================

LLMCallFn = Callable[[List[Dict[str, str]], str, str, float, bool], Dict[str, Any]]


@dataclass
class OrchestratorConfig:
    schema_path: Path
    out_dir: Path
    model: str
    api_url: str
    temperature: float = 0.0
    stream: bool = False
    start_step: int = 0
    end_step: Optional[int] = None
    include_standard_subset: bool = True
    persist_full_incremental_context: bool = True


# ============================================================
# JSON helpers
# ============================================================

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ============================================================
# Paths
# ============================================================

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
        "normalized_patch": step_dir / "normalized_patch.json",
        "step_meta": step_dir / "step_meta.json",
    }


# ============================================================
# Decision log
# ============================================================

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


# ============================================================
# Draft update
# ============================================================

def apply_normalized_patch_to_draft(
    draft: Dict[str, Any],
    normalized_patch: Dict[str, Any],
    *,
    table_name: str,
) -> Dict[str, Any]:
    """
    Minimal patch application.

    Current behavior:
    - append proposed additions
    - append proposed revisions as open issues if not directly applied
    - record rejections
    - record ambiguities and probe requests
    - bump draft version

    This is intentionally conservative.
    It avoids silently corrupting the global draft with risky automatic revisions.
    """
    updated = json.loads(json.dumps(draft))  # deep copy via JSON-safe structure

    # Apply additions directly
    additions = normalized_patch.get("proposed_additions", {})
    for field in [
        "classes",
        "data_properties",
        "object_properties",
        "subclass_relations",
        "class_mappings",
        "data_property_mappings",
        "object_property_mappings",
    ]:
        for item in additions.get(field, []):
            if not _already_exists(updated.get(field, []), item):
                updated[field].append(item)

    # Revisions are recorded as open issues in this minimal first version
    revisions = normalized_patch.get("proposed_revisions", {})
    if _count_patch_items(revisions) > 0:
        updated.setdefault("open_issues", []).append(
            {
                "issue_type": "pending_revision_application",
                "related_table": table_name,
                "description": "Patch proposed revisions that require a stronger revision engine.",
                "payload": revisions,
            }
        )

    # Rejections
    for rej in normalized_patch.get("proposed_rejections", []):
        updated.setdefault("rejected_candidates", []).append(
            {
                "candidate_type": rej.get("candidate_type"),
                "target": rej.get("target"),
                "from_table": table_name,
                "reason": rej.get("reason"),
                "status": "rejected",
            }
        )

    # Merges are also recorded as open issues for now
    merges = normalized_patch.get("proposed_merges", [])
    if merges:
        updated.setdefault("open_issues", []).append(
            {
                "issue_type": "pending_merge_application",
                "related_table": table_name,
                "description": "Patch proposed merges that require a stronger merge engine.",
                "payload": merges,
            }
        )

    # Ambiguities and probes
    for amb in normalized_patch.get("remaining_ambiguities", []):
        updated.setdefault("open_issues", []).append(
            {
                "issue_type": "remaining_ambiguity",
                "related_table": table_name,
                "description": amb,
            }
        )

    for probe in normalized_patch.get("needs_probe", []):
        updated.setdefault("open_issues", []).append(
            {
                "issue_type": "needs_probe",
                "related_table": table_name,
                "description": probe.get("question"),
                "payload": probe,
            }
        )

    bump_draft_version(updated, table_name, action="updated")
    return updated


def _already_exists(existing_list: List[Dict[str, Any]], new_item: Dict[str, Any]) -> bool:
    new_id = _extract_id(new_item)
    if not new_id:
        return False
    for old in existing_list:
        if _extract_id(old) == new_id:
            return True
    return False


def _extract_id(item: Dict[str, Any]) -> Optional[str]:
    for key in ("id", "class_id", "data_property_id", "object_property_id"):
        if key in item and item[key]:
            return str(item[key])
    return None


# ============================================================
# Core orchestration
# ============================================================

def prepare_incremental_context(config: OrchestratorConfig) -> Dict[str, Any]:
    incremental_context = build_incremental_context_from_schema_file(config.schema_path)
    paths = build_paths(config.out_dir)
    if config.persist_full_incremental_context:
        write_json(paths["incremental_context"], incremental_context)
    return incremental_context


def run_table_incremental_orchestrator(
    *,
    config: OrchestratorConfig,
    llm_call_fn: Optional[LLMCallFn] = None,
    initial_draft: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point.

    If llm_call_fn is None:
        - the function still builds and saves prompts/messages for each step
        - raw/normalized patch files will not be created
        - draft will not be updated automatically

    Expected llm_call_fn signature:
        fn(messages, model, api_url, temperature, stream) -> raw_json_dict
    """
    paths = build_paths(config.out_dir)
    config.out_dir.mkdir(parents=True, exist_ok=True)

    incremental_context = prepare_incremental_context(config)

    draft = initial_draft if initial_draft is not None else init_empty_draft()
    write_json(paths["global_draft"], draft)

    steps = incremental_context.get("incremental_steps", [])
    if config.end_step is None:
        end_step = len(steps)
    else:
        end_step = min(config.end_step, len(steps))

    meta = {
        "schema_path": str(config.schema_path),
        "out_dir": str(config.out_dir),
        "model": config.model,
        "api_url": config.api_url,
        "temperature": config.temperature,
        "stream": config.stream,
        "start_step": config.start_step,
        "end_step": end_step,
        "num_total_steps": len(steps),
        "executed_steps": [],
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
        write_text(spaths["prompt_text"], _render_messages(messages))

        step_meta = {
            "step_index": step_index,
            "table_name": table_name,
            "related_existing_tables": step.get("related_existing_tables", []),
            "requires_multi_table_reasoning": step.get("multi_table_signals", {}).get(
                "requires_multi_table_reasoning", False
            ),
            "llm_called": llm_call_fn is not None,
        }

        if llm_call_fn is not None:
            raw_patch = llm_call_fn(
                messages,
                config.model,
                config.api_url,
                config.temperature,
                config.stream,
            )
            write_json(spaths["raw_patch"], raw_patch)

            normalized_patch = normalize_patch_output(raw_patch)
            write_json(spaths["normalized_patch"], normalized_patch)

            draft = apply_normalized_patch_to_draft(
                draft,
                normalized_patch,
                table_name=table_name,
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
                "llm_called": llm_call_fn is not None,
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


def _render_messages(messages: List[Dict[str, str]]) -> str:
    chunks: List[str] = []
    for m in messages:
        chunks.append(f"[{m['role'].upper()}]\n{m['content']}")
    return "\n\n".join(chunks)


# ============================================================
# Optional adapter for existing llm call style
# ============================================================

def wrap_simple_llm_call(call_fn: Callable[..., Dict[str, Any]]) -> LLMCallFn:
    """
    Helper if you already have a function with a more keyword-style signature.
    This wrapper expects the target call_fn to accept:
      messages=..., model=..., api_url=..., temperature=..., stream=...
    """
    def _wrapped(
        messages: List[Dict[str, str]],
        model: str,
        api_url: str,
        temperature: float,
        stream: bool,
    ) -> Dict[str, Any]:
        return call_fn(
            messages=messages,
            model=model,
            api_url=api_url,
            temperature=temperature,
            stream=stream,
        )
    return _wrapped


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    # Demo mode: prompt-building only, no LLM call
    cfg = OrchestratorConfig(
        schema_path=Path("/mnt/data/nonexistent_schema.sql"),
        out_dir=Path("/mnt/data/table_incremental_demo"),
        model="gpt-5.4-mini",
        api_url="https://example.com/v1/chat/completions",
        start_step=0,
        end_step=0,
    )
    print("This module is intended to be imported and called from your pipeline.")
