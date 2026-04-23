from __future__ import annotations

from typing import Any, Dict, List, Set
import copy
import json


def init_empty_draft() -> Dict[str, Any]:
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
    history.append({"table": table_name, "action": action, "version": meta["draft_version"]})


def collect_context_tables(incremental_step: Dict[str, Any]) -> List[str]:
    scope = incremental_step.get("suggested_analysis_scope", {}) or {}
    recommended = scope.get("recommended_tables_for_joint_analysis")
    if recommended:
        return sorted(dict.fromkeys(recommended))
    tables = []
    if incremental_step.get("new_table"):
        tables.append(incremental_step["new_table"])
    tables.extend(incremental_step.get("related_existing_tables", []) or [])
    return sorted(dict.fromkeys([t for t in tables if t]))


def collect_context_columns(incremental_step: Dict[str, Any]) -> Set[str]:
    cols: Set[str] = set()
    local_table = incremental_step.get("local_table", {}) or {}
    table_name = local_table.get("name") or incremental_step.get("new_table")
    for c in local_table.get("columns", []) or []:
        name = c["name"] if isinstance(c, dict) else str(c)
        cols.add(name.lower())
        if table_name:
            cols.add(f"{table_name.lower()}.{name.lower()}")

    for fk in incremental_step.get("local_fk_edges", []) or []:
        st = str(fk.get("source_table") or "").lower()
        tt = str(fk.get("target_table") or "").lower()
        for c in fk.get("source_columns", []) or []:
            cols.add(str(c).lower())
            if st:
                cols.add(f"{st}.{str(c).lower()}")
        for c in fk.get("target_columns", []) or []:
            cols.add(str(c).lower())
            if tt:
                cols.add(f"{tt}.{str(c).lower()}")
    return cols


def _filter_elements(elements: List[Dict[str, Any]], context_tables: List[str], context_columns: Set[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for elem in elements:
        blob = json.dumps(elem, ensure_ascii=False).lower()
        keep = any(t.lower() in blob for t in context_tables) or any(c in blob for c in context_columns)
        if keep:
            out.append(copy.deepcopy(elem))
    return out


def extract_relevant_draft_slice(draft: Dict[str, Any], incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    context_tables = collect_context_tables(incremental_step)
    context_columns = collect_context_columns(incremental_step)
    return {
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


def _topn(items: List[Any], n: int) -> List[Any]:
    return items[:n]


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
        "mapping_id": x.get("mapping_id"),
        "from_tables": x.get("from_tables", []),
        "identifier_kind": x.get("identifier_kind"),
        "identifier_columns": x.get("identifier_columns", []),
        "instance_id_template": x.get("instance_id_template", ""),
    }


def _compress_data_property_mapping(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data_property_id": x.get("data_property_id"),
        "mapping_id": x.get("mapping_id"),
        "applies_to_class": x.get("applies_to_class"),
        "source_table": x.get("source_table"),
        "source_columns": x.get("source_columns", []),
        "value_kind": x.get("value_kind"),
    }


def _compress_object_property_mapping(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "object_property_id": x.get("object_property_id"),
        "mapping_id": x.get("mapping_id"),
        "from_class": x.get("from_class"),
        "to_class": x.get("to_class"),
        "from_tables": x.get("from_tables", []),
        "join_paths": x.get("join_paths", []),
        "target_type": x.get("target_type"),
    }


def build_global_summary(draft: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "num_classes": len(draft.get("classes", [])),
        "num_data_properties": len(draft.get("data_properties", [])),
        "num_object_properties": len(draft.get("object_properties", [])),
        "accepted_classes": _topn([x.get("id") for x in draft.get("classes", []) if x.get("id")], 20),
        "accepted_data_properties": _topn([x.get("id") for x in draft.get("data_properties", []) if x.get("id")], 20),
        "accepted_object_properties": _topn([x.get("id") for x in draft.get("object_properties", []) if x.get("id")], 20),
        "processed_tables": draft.get("draft_metadata", {}).get("processed_tables", []),
        "draft_version": draft.get("draft_metadata", {}).get("draft_version", 0),
    }


def compress_relevant_slice(relevant_slice: Dict[str, Any], *, max_items_per_section: int = 12) -> Dict[str, Any]:
    return {
        "classes": _topn([_compress_class(x) for x in relevant_slice.get("classes", [])], max_items_per_section),
        "data_properties": _topn([_compress_data_property(x) for x in relevant_slice.get("data_properties", [])], max_items_per_section),
        "object_properties": _topn([_compress_object_property(x) for x in relevant_slice.get("object_properties", [])], max_items_per_section),
        "class_mappings": _topn([_compress_class_mapping(x) for x in relevant_slice.get("class_mappings", [])], max_items_per_section),
        "data_property_mappings": _topn([_compress_data_property_mapping(x) for x in relevant_slice.get("data_property_mappings", [])], max_items_per_section),
        "object_property_mappings": _topn([_compress_object_property_mapping(x) for x in relevant_slice.get("object_property_mappings", [])], max_items_per_section),
    }


def compress_rejected_candidates(rejected_candidates: List[Dict[str, Any]], *, max_items: int = 12) -> List[Dict[str, Any]]:
    out = []
    for x in rejected_candidates[:max_items]:
        out.append({
            "candidate_type": x.get("candidate_type") or x.get("element_kind"),
            "target": x.get("target") or x.get("target_id"),
            "from_table": x.get("from_table"),
            "reason": x.get("reason"),
        })
    return out


def compress_open_issues(open_issues: List[Dict[str, Any]], *, max_items: int = 12) -> List[Dict[str, Any]]:
    out = []
    for x in open_issues[:max_items]:
        out.append({
            "issue_type": x.get("issue_type"),
            "related_table": x.get("related_table"),
            "description": x.get("description"),
        })
    return out


def build_update_focus(incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    signals = incremental_step.get("multi_table_signals", {}) or {}
    return {
        "new_table": incremental_step.get("new_table"),
        "related_existing_tables": incremental_step.get("related_existing_tables", []),
        "requires_multi_table_reasoning": signals.get("requires_multi_table_reasoning", False),
        "analysis_reasons": (incremental_step.get("suggested_analysis_scope", {}) or {}).get("reason", []),
        "recommended_tables_for_joint_analysis": (incremental_step.get("suggested_analysis_scope", {}) or {}).get("recommended_tables_for_joint_analysis", []),
    }


def build_draft_prompt_view(draft: Dict[str, Any], incremental_step: Dict[str, Any], *, max_items_per_section: int = 12) -> Dict[str, Any]:
    relevant = extract_relevant_draft_slice(draft, incremental_step)
    return {
        "global_summary": build_global_summary(draft),
        "relevant_draft_slice": compress_relevant_slice(relevant, max_items_per_section=max_items_per_section),
        "related_rejected_candidates": compress_rejected_candidates(relevant.get("related_rejected_candidates", []), max_items=max_items_per_section),
        "related_open_issues": compress_open_issues(relevant.get("related_open_issues", []), max_items=max_items_per_section),
        "update_focus": build_update_focus(incremental_step),
    }


def render_prompt_view_text(prompt_view: Dict[str, Any]) -> str:
    return json.dumps(prompt_view, ensure_ascii=False, indent=2)
