from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import json

from .incremental_normalize import normalize_patch_robust
from .draft_apply import apply_normalized_patch_to_draft

from .tools.value_sample_tool import build_revision_value_sample_evidence
PATCH_SECTION_FIELDS = [
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
]



@dataclass
class RevisionEngineConfig:
    model: str
    api_url: str
    api_key: str
    timeout: float
    out_dir: Path

    db_path: Optional[Path] = None
    schema_sql_path: Optional[Path] = None
    enable_value_sampling: bool = False
    sample_limit: int = 8
    distinct_limit: int = 20


REVISION_DECISION_STANDARDS = [
    "Inspect all columns in the current local revision scope, not only pre-flagged columns.",
    "Use a class-level condition when a column behaves as a row-selection signal for class membership rather than as an ordinary semantic attribute.",
    "Binary, status-like, publication-state-like, and flag-like columns require explicit review as possible class filters.",
    "Do not dismiss a binary/status column as an ordinary attribute without explicitly explaining why it is not a class filter.",
    "Do not convert ordinary descriptive attributes such as title, abstract, name, location, year, or free-text description into class-level conditions unless there is strong evidence.",
    "If a candidate filter column partitions rows into a semantically meaningful subset, prefer revising the class mapping over leaving the class scope over-broad.",
    "If evidence is weak, keep class_mappings.condition as [] and record the uncertainty in remaining_ambiguities or needs_probe.",
    "Use uri_pattern only when there is a stable row identity suitable for global resource construction.",
    "Use bnode when the mapped object is better modeled as a local structural/value object than as a globally identified entity.",
    "A URI-like literal column may remain a data property with datatype xsd:anyURI if no entity-to-entity relation is justified.",
    "If revising a class mapping changes class scope or identity strategy, revise affected attributes and relations if necessary.",
    "Prefer local, minimal revisions over regenerating the entire draft.",
    "Output a revision patch, not a full regenerated draft.",
]


def _json_clone(obj: Any) -> Any:
    return json.loads(json.dumps(obj))


def _collect_related_tables(incremental_step: Dict[str, Any]) -> List[str]:
    out: List[str] = []

    new_table = incremental_step.get("new_table")
    if isinstance(new_table, str) and new_table.strip():
        out.append(new_table.strip())

    for t in incremental_step.get("related_existing_tables", []) or []:
        if isinstance(t, str) and t.strip():
            out.append(t.strip())

    # Deduplicate, preserve order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


def _extract_local_tables_payload(incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact schema slice for revision.
    We intentionally inspect all columns in the local scope rather than pre-filtering.
    """
    payload: Dict[str, Any] = {
        "new_table": incremental_step.get("new_table"),
        "related_existing_tables": incremental_step.get("related_existing_tables", []),
        "local_table": incremental_step.get("local_table", {}),
        "related_tables": incremental_step.get("related_tables", []),
        "multi_table_signals": incremental_step.get("multi_table_signals", {}),
    }
    return payload


def _draft_item_mentions_scope(item: Dict[str, Any], scope_tables: List[str]) -> bool:
    scope = set(scope_tables)

    for key in ["source_tables", "from_tables"]:
        vals = item.get(key, []) or []
        for v in vals:
            if isinstance(v, str) and v in scope:
                return True

    for key in ["source_table"]:
        v = item.get(key)
        if isinstance(v, str) and v in scope:
            return True

    for key in [
        "identifier_columns",
        "bnode_id_columns",
        "source_columns",
        "source_identifier_columns",
        "target_identifier_columns",
        "join_paths",
        "condition",
    ]:
        vals = item.get(key, []) or []
        for v in vals:
            if isinstance(v, str):
                for t in scope:
                    if v.startswith(f"{t}.") or f"{t}." in v:
                        return True

    return False


def _build_local_draft_slice(draft: Dict[str, Any], incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep only the parts of the draft relevant to:
    - the new table
    - directly related existing tables
    This keeps revision focused and prompt size bounded.
    """
    scope_tables = _collect_related_tables(incremental_step)

    out: Dict[str, Any] = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "draft_metadata": _json_clone(draft.get("draft_metadata", {})),
        "open_issues": [],
    }

    # 1) First keep directly scoped mappings / entities
    for field in PATCH_SECTION_FIELDS:
        for item in draft.get(field, []) or []:
            if isinstance(item, dict) and _draft_item_mentions_scope(item, scope_tables):
                out[field].append(_json_clone(item))

    # 2) Expand by referenced class/property ids so the slice is semantically usable
    class_ids = set()
    data_prop_ids = set()
    obj_prop_ids = set()
    class_map_ids = set()

    for cm in out["class_mappings"]:
        if cm.get("class_id"):
            class_ids.add(cm["class_id"])
        if cm.get("mapping_id"):
            class_map_ids.add(cm["mapping_id"])

    for dpm in out["data_property_mappings"]:
        if dpm.get("data_property_id"):
            data_prop_ids.add(dpm["data_property_id"])
        if dpm.get("applies_to_class"):
            class_ids.add(dpm["applies_to_class"])

    for opm in out["object_property_mappings"]:
        if opm.get("object_property_id"):
            obj_prop_ids.add(opm["object_property_id"])
        if opm.get("from_class"):
            class_ids.add(opm["from_class"])
        if opm.get("to_class"):
            class_ids.add(opm["to_class"])

    # 3) Pull in referenced ontology objects even if they themselves do not mention the table directly
    def append_if_missing(field: str, item: Dict[str, Any], key_fn) -> None:
        existing = {key_fn(x) for x in out[field] if isinstance(x, dict)}
        k = key_fn(item)
        if k not in existing:
            out[field].append(_json_clone(item))

    for c in draft.get("classes", []) or []:
        if c.get("id") in class_ids:
            append_if_missing("classes", c, lambda x: x.get("id"))

    for dp in draft.get("data_properties", []) or []:
        if dp.get("id") in data_prop_ids or dp.get("domain") in class_ids:
            append_if_missing("data_properties", dp, lambda x: x.get("id"))

    for op in draft.get("object_properties", []) or []:
        if op.get("id") in obj_prop_ids:
            append_if_missing("object_properties", op, lambda x: x.get("id"))

    for sr in draft.get("subclass_relations", []) or []:
        if sr.get("child_class") in class_ids or sr.get("parent_class") in class_ids:
            append_if_missing("subclass_relations", sr, lambda x: x.get("id"))

    # 4) Pull in relevant open issues for local scope
    for issue in draft.get("open_issues", []) or []:
        related_table = issue.get("related_table")
        if related_table in scope_tables:
            out["open_issues"].append(_json_clone(issue))

    return out


def _build_revision_scope(draft: Dict[str, Any], incremental_step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the local revision scope:
    - all columns of the new table
    - all columns of related tables
    - current draft slice relevant to this local area
    """
    return {
        "scope_tables": _collect_related_tables(incremental_step),
        "schema_scope": _extract_local_tables_payload(incremental_step),
        "draft_slice": _build_local_draft_slice(draft, incremental_step),
    }


def _default_revision_targets(revision_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Revision in this version is scope-based rather than pre-suspicion-based.
    We still create explicit targets so the prompt is structured.
    """
    targets: List[Dict[str, Any]] = []

    draft_slice = revision_scope.get("draft_slice", {}) or {}
    schema_scope = revision_scope.get("schema_scope", {}) or {}

    for cm in draft_slice.get("class_mappings", []) or []:
        targets.append(
            {
                "target_type": "class_mapping",
                "target_id": cm.get("mapping_id"),
                "current_class_id": cm.get("class_id"),
                "from_tables": cm.get("from_tables", []),
                "focus": [
                    "condition necessity",
                    "identity strategy correctness",
                    "class scope too broad or too narrow",
                    "possible downstream impact on related properties and relations",
                ],
            }
        )

    for opm in draft_slice.get("object_property_mappings", []) or []:
        targets.append(
            {
                "target_type": "object_property_mapping",
                "target_id": opm.get("mapping_id"),
                "current_property_id": opm.get("object_property_id"),
                "focus": [
                    "join sufficiency",
                    "need for extra condition",
                    "wrong target class",
                    "should this remain a relation or become a literal mapping",
                ],
            }
        )

    for dpm in draft_slice.get("data_property_mappings", []) or []:
        targets.append(
            {
                "target_type": "data_property_mapping",
                "target_id": dpm.get("mapping_id"),
                "current_property_id": dpm.get("data_property_id"),
                "focus": [
                    "ordinary literal vs class-defining signal",
                    "datatype mismatch",
                    "possible move from attribute to condition-bearing class revision",
                ],
            }
        )

    # Always include one scope-level target so the model can revise even if explicit mapping lists are sparse
    targets.append(
        {
            "target_type": "scope_review",
            "target_id": schema_scope.get("new_table"),
            "focus": [
                "inspect all columns in local scope",
                "look for class-defining conditions",
                "look for over-broad class mappings",
                "look for identity mistakes",
                "look for relation/attribute revisions implied by class revision",
            ],
        }
    )
    return targets

def _build_column_role_review(revision_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
    schema_scope = revision_scope.get("schema_scope", {}) or {}
    local_table = schema_scope.get("local_table", {}) or {}
    table_name = str(local_table.get("name", "")).strip()

    out: List[Dict[str, Any]] = []
    for col in local_table.get("columns", []) or []:
        col_name = str(col.get("name", "")).strip()
        if not col_name:
            continue

        candidate_roles = ["ordinary_attribute"]

        lowered = col_name.lower()
        if lowered.endswith("id") or lowered in {"conference", "personid", "paperid", "topicid"}:
            candidate_roles.append("relation_key")
        if lowered in {"publish", "published", "status", "state", "type", "kind", "category", "flag", "active", "valid"}:
            candidate_roles.append("class_filter")
            candidate_roles.append("status_attribute")
        if lowered in {"uri", "homepage", "photo"}:
            candidate_roles.append("possible_relation_indicator")

        out.append(
            {
                "column": f"{table_name}.{col_name}",
                "candidate_roles": candidate_roles,
                "must_decide": True,
            }
        )
    return out
def _build_revision_messages(
    draft: Dict[str, Any],
    incremental_step: Dict[str, Any],
    revision_scope: Dict[str, Any],
    revision_targets: List[Dict[str, Any]],
    external_evidence: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, str]]:
    external_evidence = external_evidence or []

    strict_revision_patch_schema = {
        "work_unit": {
            "table": "string",
            "related_tables": ["string"],
        },
        "proposed_additions": {
            "classes": [],
            "data_properties": [],
            "object_properties": [],
            "subclass_relations": [],
            "class_mappings": [],
            "data_property_mappings": [],
            "object_property_mappings": [],
        },
        "proposed_revisions": {
            "classes": [
                {
                    "target_id": "Class:Example",
                    "updated_fields": {
                        "description": "..."
                    }
                }
            ],
            "data_properties": [],
            "object_properties": [],
            "subclass_relations": [],
            "class_mappings": [
                {
                    "target_id": "Paper_from_papers",
                    "updated_fields": {
                        "condition": ["papers.publish = 1"]
                    }
                }
            ],
            "data_property_mappings": [],
            "object_property_mappings": [],
        },
        "proposed_rejections": [],
        "proposed_merges": [],
        "decision_summary": [
            {
                "decision_type": "REV-CONDITION",
                "target": "Paper_from_papers",
                "status": "accepted",
                "confidence": 0.85,
                "reason": "..."
            }
        ],
        "remaining_ambiguities": [],
        "needs_probe": [
            {
                "probe_type": "value_sample",
                "target": "papers.publish",
                "question": "..."
            }
        ],
    }
    column_role_review = _build_column_role_review(revision_scope)
    user_payload = {
        "task": "Revise the current local draft slice. Inspect all columns in the current local scope. Output a revision patch only.",
        "incremental_step": incremental_step,
        "revision_scope": revision_scope,
        "revision_targets": revision_targets,
        "external_evidence": external_evidence,
        "decision_standards": REVISION_DECISION_STANDARDS,
        "strict_revision_patch_schema": strict_revision_patch_schema,
        "column_role_review": column_role_review,
        "hard_rules": [
            "This is a revision pass, not a full regeneration pass.",
            "Prefer proposed_revisions over proposed_additions unless genuinely new ontology objects are necessary.",
            "Inspect all columns in the current local scope; do not rely only on pre-flagged columns.",
            "If no justified revision is needed, return empty proposed_revisions for that section.",
            "Do not invent unsupported conditions.",
            "If uncertain, keep condition as [] and use remaining_ambiguities or needs_probe.",
            "If revising a class mapping changes class scope or identity strategy, revise affected attributes and relations if necessary.",
            "Return valid JSON only.",
            "For every plausibly filter-like column in column_role_review, explicitly justify in decision_summary whether it is treated as a class filter, a status attribute, or an ordinary attribute.",
            "Do not treat a column as a foreign key unless the schema or evidence explicitly supports that interpretation.",
        ]
    }

    return [
        {
            "role": "system",
            "content": (
                "You are a post-draft ontology/mapping revision assistant. "
                "Your job is to inspect the current local draft scope, review all columns in the relevant local tables, "
                "explicitly assess plausible class-filter columns, and output a JSON revision patch only."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
        },
    ]


def _empty_normalized_patch(table: str, related_tables: List[str]) -> Dict[str, Any]:
    return {
        "work_unit": {
            "table": table,
            "related_tables": related_tables,
        },
        "proposed_additions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_revisions": {k: [] for k in PATCH_SECTION_FIELDS},
        "proposed_rejections": [],
        "proposed_merges": [],
        "decision_summary": [],
        "remaining_ambiguities": [],
        "needs_probe": [],
        "normalization_warnings": [],
    }


def run_draft_revision_pass(
    *,
    draft: Dict[str, Any],
    incremental_step: Dict[str, Any],
    config: RevisionEngineConfig,
    call_llm_json_stream_fn,
    evidence_provider: Optional[Callable[[Dict[str, Any]], List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """
    Post-draft second pass:
    - inspect local scope
    - generate revision patch
    - normalize patch
    - apply patch
    """
    revision_scope = _build_revision_scope(draft, incremental_step)
    revision_targets = _default_revision_targets(revision_scope)

    external_evidence: List[Dict[str, Any]] = []

    if config.enable_value_sampling:
        try:
            external_evidence.extend(
                build_revision_value_sample_evidence(
                    revision_scope=revision_scope,
                    db_path=config.db_path,
                    schema_sql_path=config.schema_sql_path,
                    sample_limit=config.sample_limit,
                    distinct_limit=config.distinct_limit,
                )
            )
        except Exception as e:
            external_evidence.append(
                {
                    "type": "value_sample_error",
                    "message": str(e),
                }
            )

    # optional custom evidence provider
    if evidence_provider is not None:
        try:
            external_evidence.extend(
                evidence_provider(
                    {
                        "incremental_step": incremental_step,
                        "revision_scope": revision_scope,
                        "revision_targets": revision_targets,
                    }
                ) or []
            )
        except Exception as e:
            external_evidence.append(
                {
                    "type": "evidence_provider_error",
                    "message": str(e),
                }
            )

    messages = _build_revision_messages(
        draft=draft,
        incremental_step=incremental_step,
        revision_scope=revision_scope,
        revision_targets=revision_targets,
        external_evidence=external_evidence,
    )

    prompt = "\n\n".join([m["content"] for m in messages if m["role"] == "user"])

    raw_revision_patch, llm_meta = call_llm_json_stream_fn(
        prompt=prompt,
        model=config.model,
        api_url=config.api_url,
        timeout=config.timeout,
        api_key=config.api_key,
    )

    normalized_revision_patch = normalize_patch_robust(
        raw_revision_patch,
        incremental_step=incremental_step,
    )

    updated_draft = apply_normalized_patch_to_draft(
        draft,
        normalized_revision_patch,
        table_name=incremental_step.get("new_table", ""),
        incremental_step=incremental_step,
    )

    return {
        "revision_scope": revision_scope,
        "revision_targets": revision_targets,
        "external_evidence": external_evidence,
        "revision_messages": messages,
        "raw_revision_patch": raw_revision_patch,
        "revision_llm_meta": llm_meta,
        "normalized_revision_patch": normalized_revision_patch,
        "updated_draft": updated_draft,
    }