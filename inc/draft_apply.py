from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .draft_prompt_view import bump_draft_version
from .incremental_normalize import normalize_internal_draft_robust


DRAFT_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]


def apply_normalized_patch_to_draft(
    draft: Dict[str, Any],
    normalized_patch: Dict[str, Any],
    *,
    table_name: str,
    incremental_step: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Apply a normalized patch to the internal draft.

    Behavior:
    1. additions: upsert/merge into existing draft
    2. revisions: apply field-level updates for supported sections
    3. rejections: append to rejected_candidates
    4. merges: keep as open_issues for now
    5. ambiguities/probes: append to open_issues
    6. normalize + validate final draft
    """
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
    """
    Insert new item if absent; otherwise merge into existing item.
    """
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
    """
    Field-level update on an existing draft item.
    """
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
        return (
            str(item.get("mapping_id", "")) == str(target_id)
            or str(item.get("class_id", "")) == str(target_id)
        )

    if field == "data_property_mappings":
        return (
            str(item.get("mapping_id", "")) == str(target_id)
            or str(item.get("data_property_id", "")) == str(target_id)
        )

    if field == "object_property_mappings":
        return (
            str(item.get("mapping_id", "")) == str(target_id)
            or str(item.get("object_property_id", "")) == str(target_id)
        )

    return False


def _merge_draft_items(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conservative merge:
    - dicts: recursive merge
    - lists: union preserving order
    - force-override selected structural fields when new value is non-empty
    - otherwise only fill empty old values with non-empty new values
    """
    result = json.loads(json.dumps(old))

    FORCE_OVERRIDE_FIELDS = {
        "class_id",
        "from_tables",
        "identifier_kind",
        "identifier_columns",
        "bnode_id_columns",
        "instance_id_template",
        "mapping_id",
        "condition",
        "applies_to_class",
        "source_table",
        "source_columns",
        "value_kind",
        "join_paths",
        "from_class",
        "to_class",
        "target_type",
        "source_identifier_columns",
        "target_identifier_columns",
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
    """
    Minimal validation for incremental draft.
    Raise early for malformed mappings instead of carrying them downstream.
    """

    for i, cm in enumerate(draft.get("class_mappings", []) or []):
        if not cm.get("class_id"):
            raise ValueError(f"class_mappings[{i}] missing class_id: {cm}")

        kind = cm.get("identifier_kind", "")
        if kind in {"uri_pattern", "uripattern"}:
            if not cm.get("instance_id_template") and not cm.get("identifier_columns"):
                raise ValueError(
                    f"class_mappings[{i}] uri-pattern style mapping has no template/identifier columns: {cm}"
                )

        if kind in {"bnode", "bnodeidcolumns"}:
            if not cm.get("bnode_id_columns") and not cm.get("identifier_columns"):
                raise ValueError(
                    f"class_mappings[{i}] bnode mapping has no identity columns: {cm}"
                )

    for i, dpm in enumerate(draft.get("data_property_mappings", []) or []):
        if not dpm.get("data_property_id"):
            raise ValueError(f"data_property_mappings[{i}] missing data_property_id: {dpm}")

        if not dpm.get("applies_to_class"):
            raise ValueError(f"data_property_mappings[{i}] missing applies_to_class: {dpm}")

        value_kind = dpm.get("value_kind", "")
        if value_kind == "column" and not dpm.get("source_columns"):
            raise ValueError(
                f"data_property_mappings[{i}] value_kind=column but source_columns empty: {dpm}"
            )

    for i, opm in enumerate(draft.get("object_property_mappings", []) or []):
        if not opm.get("object_property_id"):
            raise ValueError(f"object_property_mappings[{i}] missing object_property_id: {opm}")

        if not opm.get("from_class"):
            raise ValueError(f"object_property_mappings[{i}] missing from_class: {opm}")

        if opm.get("target_type") != "resource" and not opm.get("to_class"):
            raise ValueError(
                f"object_property_mappings[{i}] missing to_class for non-resource relation: {opm}"
            )