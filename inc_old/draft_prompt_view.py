
from __future__ import annotations

"""
draft_prompt_view.py

Utilities for:
1. initializing an internal global draft
2. extracting a relevant draft slice for a newly added table
3. compressing that slice into a prompt-friendly view

Design principles
-----------------
- Keep the internal draft as the single source of truth.
- Never pass the full internal draft to the LLM.
- Build a compact prompt view consisting of:
  - global accepted summary
  - relevant local draft slice
  - related rejected candidates
  - related open issues

This module is intentionally independent from the rest of the pipeline so it can
be plugged into a table-centric incremental ontology drafting loop.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
import copy
import json


# ============================================================
# Internal draft schema helpers
# ============================================================

def init_empty_draft() -> Dict[str, Any]:
    """
    Initialize an empty internal draft.

    The structure stays close to the current project draft/mapping format
    while adding metadata useful for incremental processing.
    """
    return {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "draft_metadata": {
            "processed_tables": [],
            "table_history": [],
            "draft_version": 0,
        },
        "rejected_candidates": [],
        "open_issues": [],
    }


def bump_draft_version(draft: Dict[str, Any], table_name: str, action: str = "updated") -> None:
    meta = draft.setdefault("draft_metadata", {})
    meta["draft_version"] = int(meta.get("draft_version", 0)) + 1
    processed = meta.setdefault("processed_tables", [])
    if table_name not in processed:
        processed.append(table_name)
    history = meta.setdefault("table_history", [])
    history.append(
        {
            "table": table_name,
            "action": action,
            "version": meta["draft_version"],
        }
    )


# ============================================================
# Table-context helpers
# ============================================================

def collect_context_tables(incremental_step: Dict[str, Any]) -> List[str]:
    """
    Tables that should be considered when the new table is processed.
    """
    scope = incremental_step.get("suggested_analysis_scope", {}) or {}
    recommended = scope.get("recommended_tables_for_joint_analysis")
    if recommended:
        return sorted(dict.fromkeys(recommended))
    new_table = incremental_step.get("new_table")
    related = incremental_step.get("related_existing_tables", []) or []
    tables = [new_table] if new_table else []
    tables.extend(related)
    return sorted(dict.fromkeys(tables))


def collect_context_columns(incremental_step: Dict[str, Any]) -> Set[str]:
    """
    Extract a set of table.column-like and plain column references useful for
    relevance matching. This is intentionally heuristic.
    """
    cols: Set[str] = set()
    local_table = incremental_step.get("local_table", {}) or {}
    table_name = local_table.get("name") or incremental_step.get("new_table")
    for c in local_table.get("columns", []) or []:
        name = c["name"] if isinstance(c, dict) else str(c)
        cols.add(name.lower())
        if table_name:
            cols.add(f"{table_name.lower()}.{name.lower()}")

    for fk in incremental_step.get("local_fk_edges", []) or []:
        for c in fk.get("source_columns", []) or []:
            cols.add(c.lower())
            if fk.get("source_table"):
                cols.add(f"{fk['source_table'].lower()}.{c.lower()}")
        for c in fk.get("target_columns", []) or []:
            cols.add(c.lower())
            if fk.get("target_table"):
                cols.add(f"{fk['target_table'].lower()}.{c.lower()}")

    return cols


# ============================================================
# Draft slicing
# ============================================================

def extract_relevant_draft_slice(
    draft: Dict[str, Any],
    incremental_step: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract the part of the internal draft that is relevant to the new table.

    Current strategy:
    - build a context table set from the incremental step
    - keep draft elements whose serialized form mentions one of these tables
      or related columns
    - preserve related rejected candidates and open issues too

    This is intentionally conservative and heuristic, but much shorter than
    passing the full draft.
    """
    context_tables = collect_context_tables(incremental_step)
    context_columns = collect_context_columns(incremental_step)

    result = {
        "classes": _filter_elements(draft.get("classes", []), context_tables, context_columns),
        "data_properties": _filter_elements(draft.get("data_properties", []), context_tables, context_columns),
        "object_properties": _filter_elements(draft.get("object_properties", []), context_tables, context_columns),
        "subclass_relations": _filter_elements(draft.get("subclass_relations", []), context_tables, context_columns),
        "class_mappings": _filter_elements(draft.get("class_mappings", []), context_tables, context_columns),
        "data_property_mappings": _filter_elements(draft.get("data_property_mappings", []), context_tables, context_columns),
        "object_property_mappings": _filter_elements(draft.get("object_property_mappings", []), context_tables, context_columns),
        "related_rejected_candidates": _filter_elements(draft.get("rejected_candidates", []), context_tables, context_columns),
        "related_open_issues": _filter_elements(draft.get("open_issues", []), context_tables, context_columns),
    }
    return result


def _filter_elements(
    elements: List[Dict[str, Any]],
    context_tables: List[str],
    context_columns: Set[str],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for elem in elements:
        blob = json.dumps(elem, ensure_ascii=False).lower()
        keep = False
        for t in context_tables:
            if t.lower() in blob:
                keep = True
                break
        if not keep:
            for c in context_columns:
                if c in blob:
                    keep = True
                    break
        if keep:
            out.append(copy.deepcopy(elem))
    return out


# ============================================================
# Prompt-friendly view construction
# ============================================================

def build_draft_prompt_view(
    draft: Dict[str, Any],
    incremental_step: Dict[str, Any],
    *,
    max_items_per_section: int = 12,
) -> Dict[str, Any]:
    """
    Build a compact prompt-facing draft view.

    Output structure:
    {
      "global_summary": ...,
      "relevant_draft_slice": ...,
      "related_rejected_candidates": ...,
      "related_open_issues": ...,
      "update_focus": ...
    }
    """
    relevant = extract_relevant_draft_slice(draft, incremental_step)

    return {
        "global_summary": build_global_summary(draft),
        "relevant_draft_slice": compress_relevant_slice(relevant, max_items_per_section=max_items_per_section),
        "related_rejected_candidates": compress_rejected_candidates(
            relevant.get("related_rejected_candidates", []),
            max_items=max_items_per_section,
        ),
        "related_open_issues": compress_open_issues(
            relevant.get("related_open_issues", []),
            max_items=max_items_per_section,
        ),
        "update_focus": build_update_focus(incremental_step),
    }


def build_global_summary(draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a very compact global summary.
    """
    classes = [x.get("id") or x.get("label") for x in draft.get("classes", [])]
    data_props = [_short_data_property(x) for x in draft.get("data_properties", [])]
    obj_props = [_short_object_property(x) for x in draft.get("object_properties", [])]

    return {
        "num_classes": len(draft.get("classes", [])),
        "num_data_properties": len(draft.get("data_properties", [])),
        "num_object_properties": len(draft.get("object_properties", [])),
        "accepted_classes": _topn([x for x in classes if x], 20),
        "accepted_data_properties": _topn([x for x in data_props if x], 20),
        "accepted_object_properties": _topn([x for x in obj_props if x], 20),
        "processed_tables": draft.get("draft_metadata", {}).get("processed_tables", []),
        "draft_version": draft.get("draft_metadata", {}).get("draft_version", 0),
    }


def compress_relevant_slice(
    relevant_slice: Dict[str, Any],
    *,
    max_items_per_section: int = 12,
) -> Dict[str, Any]:
    """
    Compress relevant slice to prompt-friendly representations.
    Keep the structure but shorten each item.
    """
    return {
        "classes": _topn([_compress_class(x) for x in relevant_slice.get("classes", [])], max_items_per_section),
        "data_properties": _topn([_compress_data_property(x) for x in relevant_slice.get("data_properties", [])], max_items_per_section),
        "object_properties": _topn([_compress_object_property(x) for x in relevant_slice.get("object_properties", [])], max_items_per_section),
        "class_mappings": _topn([_compress_class_mapping(x) for x in relevant_slice.get("class_mappings", [])], max_items_per_section),
        "data_property_mappings": _topn(
            [_compress_data_property_mapping(x) for x in relevant_slice.get("data_property_mappings", [])],
            max_items_per_section,
        ),
        "object_property_mappings": _topn(
            [_compress_object_property_mapping(x) for x in relevant_slice.get("object_property_mappings", [])],
            max_items_per_section,
        ),
    }


def compress_rejected_candidates(
    rejected_candidates: List[Dict[str, Any]],
    *,
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    out = []
    for x in rejected_candidates[:max_items]:
        out.append(
            {
                "candidate_type": x.get("candidate_type") or x.get("element_kind"),
                "target": x.get("target") or x.get("target_id"),
                "from_table": x.get("from_table"),
                "reason": x.get("reason"),
            }
        )
    return out


def compress_open_issues(
    open_issues: List[Dict[str, Any]],
    *,
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    out = []
    for x in open_issues[:max_items]:
        out.append(
            {
                "issue_type": x.get("issue_type"),
                "related_table": x.get("related_table"),
                "description": x.get("description"),
            }
        )
    return out


def build_update_focus(incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    """
    What the LLM should focus on for this table update.
    """
    signals = incremental_step.get("multi_table_signals", {}) or {}
    return {
        "new_table": incremental_step.get("new_table"),
        "related_existing_tables": incremental_step.get("related_existing_tables", []),
        "requires_multi_table_reasoning": signals.get("requires_multi_table_reasoning", False),
        "analysis_reasons": incremental_step.get("suggested_analysis_scope", {}).get("reason", []),
        "recommended_tables_for_joint_analysis": incremental_step.get("suggested_analysis_scope", {}).get(
            "recommended_tables_for_joint_analysis", []
        ),
    }


# ============================================================
# Compression helpers
# ============================================================

def _compress_class(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": x.get("id"),
        "label": x.get("label"),
        "source_tables": x.get("source_tables", []),
        "status": x.get("status"),
    }


def _compress_data_property(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": x.get("id"),
        "label": x.get("label"),
        "domain": x.get("domain"),
        "datatype": x.get("datatype"),
        "source_tables": x.get("source_tables", []),
    }


def _compress_object_property(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": x.get("id"),
        "label": x.get("label"),
        "domain": x.get("domain"),
        "range": x.get("range"),
        "source_tables": x.get("source_tables", []),
    }


def _compress_class_mapping(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "class_id": x.get("class_id"),
        "from_tables": x.get("from_tables", []),
        "identifier_columns": x.get("identifier_columns", []),
        "identifier_kind": x.get("identifier_kind"),
        "condition": x.get("condition", []),
    }


def _compress_data_property_mapping(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data_property_id": x.get("data_property_id"),
        "source_table": x.get("source_table"),
        "source_columns": x.get("source_columns", []),
        "applies_to_class": x.get("applies_to_class"),
        "value_kind": x.get("value_kind"),
        "join_paths": x.get("join_paths", []),
        "condition": x.get("condition", []),
    }


def _compress_object_property_mapping(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "object_property_id": x.get("object_property_id"),
        "from_class": x.get("from_class"),
        "to_class": x.get("to_class"),
        "from_tables": x.get("from_tables", []),
        "join_paths": x.get("join_paths", []),
        "condition": x.get("condition", []),
    }


def _short_data_property(x: Dict[str, Any]) -> str:
    pid = x.get("id") or x.get("label")
    domain = x.get("domain")
    if pid and domain:
        return f"{pid}({domain})"
    return str(pid) if pid else ""


def _short_object_property(x: Dict[str, Any]) -> str:
    pid = x.get("id") or x.get("label")
    domain = x.get("domain")
    range_ = x.get("range")
    if pid and domain and range_:
        return f"{pid}({domain} -> {range_})"
    return str(pid) if pid else ""


def _topn(items: List[Any], n: int) -> List[Any]:
    return items[:n]


# ============================================================
# Optional utility for prompt serialization
# ============================================================

def render_prompt_view_text(prompt_view: Dict[str, Any]) -> str:
    """
    Render the prompt-facing draft view as compact JSON text.
    Useful if you want to insert it directly into a user prompt.
    """
    return json.dumps(prompt_view, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Small self-test / demo
    draft = init_empty_draft()
    draft["classes"].append(
        {
            "id": "Person",
            "label": "Person",
            "status": "accepted",
            "confidence": 0.95,
            "source_tables": ["persons"],
        }
    )
    draft["data_properties"].append(
        {
            "id": "person_name",
            "label": "name",
            "domain": "Person",
            "datatype": "xsd:string",
            "status": "accepted",
            "confidence": 0.9,
            "source_tables": ["persons"],
        }
    )
    draft["class_mappings"].append(
        {
            "class_id": "Person",
            "instance_id_template": "persons/@@persons.perid@@",
            "from_tables": ["persons"],
            "identifier_columns": ["persons.perid"],
            "identifier_kind": "uri_pattern",
            "status": "accepted",
            "confidence": 0.95,
        }
    )
    bump_draft_version(draft, "persons", action="added")

    incremental_step = {
        "new_table": "organizations",
        "related_existing_tables": ["persons"],
        "local_table": {
            "name": "organizations",
            "columns": [
                {"name": "orgid"},
                {"name": "name"},
                {"name": "address"},
                {"name": "location"},
                {"name": "postcode"},
                {"name": "country"},
            ],
        },
        "local_fk_edges": [],
        "suggested_analysis_scope": {
            "recommended_tables_for_joint_analysis": ["organizations", "persons"],
            "reason": ["connected_to_existing_tables", "structured_value_object_bundle"],
        },
        "multi_table_signals": {
            "requires_multi_table_reasoning": True
        },
    }

    prompt_view = build_draft_prompt_view(draft, incremental_step)
    print(render_prompt_view_text(prompt_view))
