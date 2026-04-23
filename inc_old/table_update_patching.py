
from __future__ import annotations

"""
table_update_patching.py

Define:
1. patch schema for table-centric incremental ontology drafting
2. prompt builder for asking the LLM to update the global draft when a new table arrives

This module is designed to work with:
- schema_incremental.py
- draft_prompt_view.py

Design principles
-----------------
- The LLM should NOT rewrite the full ontology draft.
- The LLM should produce a LOCAL PATCH only.
- The patch is defined over the current global draft state.
- The prompt should include:
  - the new table and local structural context
  - compact current draft view
  - a subset of the ontology/mapping decision standard
  - a strict patch output schema
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import json
from textwrap import dedent


# ============================================================
# Patch schema
# ============================================================

PATCH_SCHEMA_DESCRIPTION = """
Return a JSON object with the following top-level keys:

- work_unit
- proposed_additions
- proposed_revisions
- proposed_rejections
- proposed_merges
- decision_summary
- remaining_ambiguities
- needs_probe

Detailed schema:

1. work_unit
{
  "table": "new_table_name",
  "related_tables": ["table_a", "table_b", ...]
}

2. proposed_additions
{
  "classes": [...],
  "data_properties": [...],
  "object_properties": [...],
  "subclass_relations": [...],
  "class_mappings": [...],
  "data_property_mappings": [...],
  "object_property_mappings": [...]
}

3. proposed_revisions
{
  "classes": [...],
  "data_properties": [...],
  "object_properties": [...],
  "subclass_relations": [...],
  "class_mappings": [...],
  "data_property_mappings": [...],
  "object_property_mappings": [...]
}

Each revision object must contain:
- target_id
- updated_fields

Example:
{
  "target_id": "Person",
  "updated_fields": {
    "description": "Updated description"
  }
}

4. proposed_rejections
[
  {
    "candidate_type": "C-TYPE-PROMOTED | A-LITERAL | R-OBJECT | ...",
    "target": "candidate identifier or label",
    "reason": "why this interpretation should be rejected"
  }
]

5. proposed_merges
[
  {
    "winner_id": "kept element id",
    "loser_id": "merged-away element id",
    "element_kind": "class | data_property | object_property | class_mapping | data_property_mapping | object_property_mapping",
    "reason": "why these two should be merged"
  }
]

6. decision_summary
[
  {
    "decision_type": "C-ENTITY | C-VALUE-OBJECT | C-ASSOCIATION | C-RESTRICTED | C-TYPE-PROMOTED | R-OBJECT | R-SHORTCUT | R-ASSOCIATION-LINK | R-CONDITIONAL-FAMILY | A-LITERAL | A-RESOURCE | A-COMPOSED | A-TYPING | I-URI-PATTERN | I-URI-COLUMN | I-BNODE | I-MULTI-SOURCE | K-CLASS-MEMBERSHIP | K-REL-DISCRIMINATOR | K-SEMANTIC-FILTER | K-NONESSENTIAL-GUARD | K-ESSENTIAL-JOIN | K-REDUNDANT-JOIN",
    "target": "element id or candidate name",
    "status": "accepted | rejected | needs_probe",
    "confidence": 0.0,
    "reason": "short reason"
  }
]

7. remaining_ambiguities
[
  "string description of unresolved ambiguity"
]

8. needs_probe
[
  {
    "probe_type": "value_sample | join_check | discriminator_check | identity_check | semantic_probe",
    "target": "table/column/bundle/condition/join",
    "question": "what needs to be verified"
  }
]

Important:
- Return JSON only.
- Do NOT return the full draft.
- Only propose changes caused by the newly added table and its local neighborhood.
- Be conservative: if evidence is weak, prefer revision/rejection/needs_probe over speculative additions.
"""


PATCH_OUTPUT_TEMPLATE = {
    "work_unit": {
        "table": "new_table_name",
        "related_tables": ["related_table_1", "related_table_2"]
    },
    "proposed_additions": {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": []
    },
    "proposed_revisions": {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": []
    },
    "proposed_rejections": [],
    "proposed_merges": [],
    "decision_summary": [],
    "remaining_ambiguities": [],
    "needs_probe": []
}


# ============================================================
# Decision standard subset helpers
# ============================================================

STANDARD_SECTIONS = {
    "class_core": """
### Class decisions
- Represent something as an entity class if it has stable identity, behaves like a domain entity, and naturally serves as a relation endpoint.
- If a non-FK value column contains reusable named concepts/entities rather than free text, consider a value-domain class.
- If multiple columns jointly form a structured object (for example address-like bundles), and the object depends on a host entity and lacks a natural global URI, consider a value-object class.
- If class membership is defined by an explicit condition that changes the class extension, model that as a restricted class.
- Do NOT promote type/category/role values into subclasses by default; prefer typing assertions unless subclass evidence is strong.
""".strip(),

    "relation_core": """
### Relation decisions
- Use an object property when two class instances are linked semantically.
- If a connector table has meaningful payload attributes describing the relation itself, prefer reification into an association class instead of collapsing to a direct relation.
- If the same join skeleton supports different semantics based on a discriminator column, split them into distinct relations instead of one generic relation.
- Only materialize shortcut relations if the projected direct relation has stable semantic meaning.
""".strip(),

    "attribute_core": """
### Attribute decisions
- Use a literal property for ordinary text, numbers, dates, and scalar measurements.
- If a value is already a URI or should become a URI-like resource target, do not treat it as an ordinary literal.
- If multiple columns together form one ontology-level value, prefer the composed property when semantically appropriate.
- If a column expresses instance type/category membership, prefer a typing assertion over an ordinary literal property.
""".strip(),

    "identity_core": """
### Identity decisions
- Use uriPattern when identity should be represented as a URI constructed from one or more columns.
- Use uriColumn when the database already stores the intended URI and the value should remain a resource.
- Use bNodeIdColumns when an object should exist as a node but has no natural global URI, and local identity anchored by host/entity columns is sufficient.
- The same conceptual class may require multiple class maps if the database provides multiple source identities.
""".strip(),

    "condition_join_core": """
### Condition and join decisions
- A condition belongs to a class if it defines which rows instantiate that class.
- A condition belongs to a relation if it distinguishes different relation meanings.
- Keep a condition if it removes semantically invalid values.
- Avoid adding IS NOT NULL-style conditions unless they are truly semantically necessary.
- Keep joins required to ground owner/target semantics.
- Avoid stronger-than-necessary joins when a simpler semantically sufficient join exists.
""".strip(),

    "default_preferences": """
### Default preferences
- Prefer typing assertion over subclass promotion unless subclass evidence is strong.
- Prefer literal property over value-domain class unless the value domain behaves like reusable concepts.
- Prefer value-object class over flat literals only when structured-object evidence is strong.
- Prefer minimal semantically sufficient joins over stronger joins.
- Prefer semantic conditions over non-semantic null guards.
""".strip(),
}


def choose_standard_sections(incremental_step: Dict[str, Any]) -> List[str]:
    """
    Select the most relevant decision-standard blocks for the current table.

    This is heuristic but much shorter than always inserting the full standard.
    """
    sections = {"class_core", "relation_core", "attribute_core", "identity_core", "condition_join_core", "default_preferences"}

    signals = incremental_step.get("multi_table_signals", {}) or {}
    local_table = incremental_step.get("local_table", {}) or {}
    col_names = {
        (c["name"] if isinstance(c, dict) else str(c)).lower()
        for c in local_table.get("columns", []) or []
    }

    chosen = set()

    # Always include defaults
    chosen.add("default_preferences")

    # Class-related situations
    if signals.get("association_class_likelihood") or signals.get("weak_entity_like") or signals.get("address_like_bundle") or "publish" in col_names:
        chosen.add("class_core")

    # Relation-related situations
    if signals.get("connector_like") or signals.get("many_fk_targets") or "relationtype" in col_names or len(incremental_step.get("local_fk_edges", [])) > 0:
        chosen.add("relation_core")

    # Attribute-related situations
    if any(x in col_names for x in ["firstname", "lastname", "homepage", "email", "photo", "uri", "url"]):
        chosen.add("attribute_core")

    # Identity-related situations
    if signals.get("address_like_bundle") or any(x in col_names for x in ["homepage", "email", "photo", "uri", "url"]):
        chosen.add("identity_core")

    # Condition/join-related situations
    if "publish" in col_names or "status" in col_names or "relationtype" in col_names or len(incremental_step.get("local_fk_edges", [])) > 0:
        chosen.add("condition_join_core")

    # Fallback: if nothing special happened, still keep class + relation + attribute
    if len(chosen) == 1:
        chosen.update({"class_core", "relation_core", "attribute_core"})

    order = ["class_core", "relation_core", "attribute_core", "identity_core", "condition_join_core", "default_preferences"]
    return [x for x in order if x in chosen]


def render_standard_subset(section_names: List[str]) -> str:
    blocks = [STANDARD_SECTIONS[x] for x in section_names if x in STANDARD_SECTIONS]
    return "\n\n".join(blocks)


# ============================================================
# Prompt builder
# ============================================================

SYSTEM_PROMPT_TABLE_UPDATE = """You are an ontology learning assistant for relational databases.

Your task is NOT to regenerate the full ontology draft from scratch.

Instead, you are given:
1. a newly added table and its local structural context,
2. a compact view of the current global draft,
3. ontology/mapping decision standards.

You must determine how the new table should UPDATE the current draft.

Important:
- Think in a mapping-based way, not only a naming-based way.
- Be conservative.
- Only propose changes that are justified by the new table and its local multi-table neighborhood.
- Prefer explicit rejections or needs_probe over speculative additions when evidence is weak.
- Return JSON only.
"""


def build_table_update_user_prompt(
    *,
    incremental_step: Dict[str, Any],
    draft_prompt_view: Dict[str, Any],
    include_standard_subset: bool = True,
) -> str:
    """
    Build the user prompt for a single table-update round.
    """
    standard_sections = choose_standard_sections(incremental_step) if include_standard_subset else []
    standard_text = render_standard_subset(standard_sections) if include_standard_subset else ""

    prompt = dedent(
        f"""
        You are given a newly added table in an incremental ontology learning process.

        ## Current task
        Update the current global ontology/mapping draft based on the new table.

        ## New table incremental context
        {json.dumps(incremental_step, ensure_ascii=False, indent=2)}

        ## Current draft view
        {json.dumps(draft_prompt_view, ensure_ascii=False, indent=2)}

        ## Decision standard subset
        {standard_text if standard_text else "(omitted)"}

        ## Patch output schema
        {PATCH_SCHEMA_DESCRIPTION}

        ## Required JSON skeleton
        {json.dumps(PATCH_OUTPUT_TEMPLATE, ensure_ascii=False, indent=2)}

        ## Additional instructions
        - Do NOT restate the full ontology.
        - Do NOT rewrite unchanged elements.
        - Only propose additions/revisions/rejections/merges caused by this new table.
        - If the new table may affect existing classes, properties, or mappings, propose targeted revisions.
        - If the new table can only be understood jointly with related tables, reason over the recommended joint analysis scope.
        - If evidence is insufficient, put the issue into remaining_ambiguities or needs_probe.
        - Return JSON only.
        """
    ).strip()

    return prompt


def build_table_update_messages(
    *,
    incremental_step: Dict[str, Any],
    draft_prompt_view: Dict[str, Any],
    include_standard_subset: bool = True,
) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT_TABLE_UPDATE},
        {
            "role": "user",
            "content": build_table_update_user_prompt(
                incremental_step=incremental_step,
                draft_prompt_view=draft_prompt_view,
                include_standard_subset=include_standard_subset,
            ),
        },
    ]


def build_table_update_payload(
    *,
    incremental_step: Dict[str, Any],
    draft_prompt_view: Dict[str, Any],
    model: str,
    temperature: float = 0.0,
    stream: bool = False,
    include_standard_subset: bool = True,
) -> Dict[str, Any]:
    return {
        "model": model,
        "messages": build_table_update_messages(
            incremental_step=incremental_step,
            draft_prompt_view=draft_prompt_view,
            include_standard_subset=include_standard_subset,
        ),
        "temperature": temperature,
        "stream": stream,
    }


# ============================================================
# Patch normalization / parsing helpers
# ============================================================

def normalize_patch_output(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal normalization to ensure required top-level keys exist.

    This does NOT validate deep structure yet.
    """
    out = {
        "work_unit": raw_json.get("work_unit", {}),
        "proposed_additions": raw_json.get("proposed_additions", {}),
        "proposed_revisions": raw_json.get("proposed_revisions", {}),
        "proposed_rejections": raw_json.get("proposed_rejections", []),
        "proposed_merges": raw_json.get("proposed_merges", []),
        "decision_summary": raw_json.get("decision_summary", []),
        "remaining_ambiguities": raw_json.get("remaining_ambiguities", []),
        "needs_probe": raw_json.get("needs_probe", []),
    }

    # Ensure addition/revision containers exist
    for section in ["proposed_additions", "proposed_revisions"]:
        container = out[section]
        if not isinstance(container, dict):
            container = {}
        out[section] = {
            "classes": container.get("classes", []),
            "data_properties": container.get("data_properties", []),
            "object_properties": container.get("object_properties", []),
            "subclass_relations": container.get("subclass_relations", []),
            "class_mappings": container.get("class_mappings", []),
            "data_property_mappings": container.get("data_property_mappings", []),
            "object_property_mappings": container.get("object_property_mappings", []),
        }

    return out


# ============================================================
# Optional utility for debugging
# ============================================================

def render_messages_text(messages: List[Dict[str, str]]) -> str:
    """
    Render system + user prompt as plain text for debugging or saving.
    """
    chunks = []
    for m in messages:
        chunks.append(f"[{m['role'].upper()}]\n{m['content']}")
    return "\n\n".join(chunks)


if __name__ == "__main__":
    # Small demo
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
                {"name": "homepage"},
            ],
        },
        "local_fk_edges": [],
        "multi_table_signals": {
            "address_like_bundle": ["address", "location", "postcode", "country"],
            "requires_multi_table_reasoning": True,
        },
        "suggested_analysis_scope": {
            "recommended_tables_for_joint_analysis": ["organizations", "persons"],
            "reason": ["structured_value_object_bundle", "connected_to_existing_tables"],
        },
    }

    draft_prompt_view = {
        "global_summary": {
            "accepted_classes": ["Person"],
            "accepted_data_properties": ["person_name(Person)"],
            "accepted_object_properties": [],
            "processed_tables": ["persons"],
            "draft_version": 1,
        },
        "relevant_draft_slice": {
            "classes": [{"id": "Person", "label": "Person", "source_tables": ["persons"], "status": "accepted"}],
            "data_properties": [],
            "object_properties": [],
            "class_mappings": [],
            "data_property_mappings": [],
            "object_property_mappings": [],
        },
        "related_rejected_candidates": [],
        "related_open_issues": [],
        "update_focus": {
            "new_table": "organizations",
            "related_existing_tables": ["persons"],
            "requires_multi_table_reasoning": True,
        },
    }

    msgs = build_table_update_messages(
        incremental_step=incremental_step,
        draft_prompt_view=draft_prompt_view,
    )
    print(render_messages_text(msgs))
