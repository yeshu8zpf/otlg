
from __future__ import annotations

"""
Strict prompt specification for table-centric incremental ontology drafting.

Design goal:
- Force the LLM to emit ONE stable patch schema.
- Avoid alias drift such as ontology_class_id / ontology_class, class_mapping_id / class_mapping, etc.
- Keep the patch schema close to the internal draft schema and close to Burr-style mapping needs.
"""

from typing import Any, Dict, List
import json
from textwrap import dedent


STRICT_PATCH_SCHEMA = {
    "work_unit": {
        "table": "string",
        "related_tables": ["string"]
    },
    "proposed_additions": {
        "classes": [
            {
                "id": "Class:Conference",
                "label": "Conference",
                "description": "string",
                "source_tables": ["conferences"],
                "identifier_columns": ["conferences.confid"]
            }
        ],
        "data_properties": [
            {
                "id": "DataProperty:hasConferenceName",
                "label": "has conference name",
                "domain": "Class:Conference",
                "datatype": "xsd:string",
                "description": "string"
            }
        ],
        "object_properties": [
            {
                "id": "ObjectProperty:paperPublishedInConference",
                "label": "paper published in conference",
                "domain": "Class:Paper",
                "range": "Class:Conference",
                "description": "string"
            }
        ],
        "subclass_relations": [
            {
                "id": "Subclass:Child_to_Parent",
                "child_class": "Class:Child",
                "parent_class": "Class:Parent"
            }
        ],
        "class_mappings": [
            {
                "mapping_id": "Conference_from_conferences",
                "class_id": "Class:Conference",
                "from_tables": ["conferences"],
                "identifier_kind": "uri_pattern",
                "identifier_columns": ["conferences.confid"],
                "instance_id_template": "conferences/@@conferences.confid@@",
                "bnode_id_columns": []
            }
        ],
        "data_property_mappings": [
            {
                "mapping_id": "hasConferenceName_from_Name",
                "data_property_id": "DataProperty:hasConferenceName",
                "applies_to_class": "Class:Conference",
                "source_table": "conferences",
                "source_columns": ["conferences.name"],
                "value_kind": "column",
                "value_template": "",
                "sql_expression": "",
                "constant_value": "",
                "datatype": "xsd:string",
                "join_paths": [],
                "condition": []
            }
        ],
        "object_property_mappings": [
            {
                "mapping_id": "paperPublishedInConference_from_Conference",
                "object_property_id": "ObjectProperty:paperPublishedInConference",
                "from_class": "Class:Paper",
                "to_class": "Class:Conference",
                "from_tables": ["papers"],
                "source_identifier_columns": ["papers.paperid"],
                "target_identifier_columns": ["conferences.confid"],
                "join_paths": [["papers.conference", "=", "conferences.confid"]],
                "condition": [],
                "target_type": "entity"
            }
        ]
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
    "decision_summary": [
        {
            "decision_type": "C-ENTITY",
            "target": "Class:Conference",
            "status": "accepted",
            "confidence": 0.95,
            "reason": "string"
        }
    ],
    "remaining_ambiguities": ["string"],
    "needs_probe": [
        {
            "probe_type": "value_sample",
            "target": "conferences.date",
            "question": "string"
        }
    ]
}


PATCH_SCHEMA_RULES = dedent("""
Use the EXACT field names shown in STRICT_PATCH_SCHEMA.
Do NOT rename fields.
Do NOT introduce aliases.
Do NOT output ontology_class, ontology_class_id, ontology_property, ontology_property_id,
class_mapping, class_mapping_id, source_column, database_column, source_table/database_table
variants outside the exact schema below.
Do NOT output extras, payload, metadata, wrapper objects, or nested containers unless they
appear in the strict schema.
Do NOT output plain strings in decision_summary. decision_summary MUST be a list of objects.
If a section is empty, output [] for that section. Never omit a section. Never output null.
All identifiers must already use the internal canonical prefixes:
- class ids: Class:...
- data properties: DataProperty:...
- object properties: ObjectProperty:...
Use fully-qualified table.column format everywhere in mappings and joins.
For identifier_kind, only use one of:
- uri_pattern
- uri_column
- bnode
For target_type in object_property_mappings, only use one of:
- entity
- resource
Default rule for URI-like database columns:
- If the column is just a stored URI value and NOT evidence of a relation to another ontology class,
  model it as a data property with datatype xsd:anyURI.
- Only use object_property_mappings when there is clear evidence of an entity-to-entity relation.
""")


STRICT_EXAMPLE = dedent("""
Correct class mapping example:
{
  "mapping_id": "Conference_from_conferences",
  "class_id": "Class:Conference",
  "from_tables": ["conferences"],
  "identifier_kind": "uri_pattern",
  "identifier_columns": ["conferences.confid"],
  "instance_id_template": "http://example.org/conference/{ConfID}",
  "bnode_id_columns": []
}

Wrong examples that must NOT appear:
- {"id": "Conference_from_conferences", "ontology_class": "Conference", "source_table": "conferences", ...}
- {"ontology_class_id": "Conference", "database_table": "conferences", ...}
- {"ontology_property": "hasConferenceName", "source_column": "Name", ...}
- {"ontology_property_id": "hasConferenceName", "database_column": "conferences.Name", ...}
- ["Created Conference class ...", "Used uriPattern ..."] as decision_summary
""")


SYSTEM_PROMPT_TABLE_UPDATE = """You are an ontology learning assistant for relational databases.

You must output ONLY a JSON patch that follows the strict patch schema.
Your output is machine-consumed. Schema drift is a serious error.
"""


def choose_standard_sections(incremental_step: Dict[str, Any]) -> List[str]:
    # Keep it simple and stable; shorter prompt reduces API fragility.
    return [
        "Represent stable entities as classes.",
        "Use fully-qualified table.column references in mappings.",
        "Use data properties for literal and URI-valued columns unless there is clear entity-to-entity evidence.",
        "Only add object properties for real relations with grounded joins.",
        "Do not expose identifier support columns as ontology properties unless semantically justified.",
    ]


def build_table_update_user_prompt(
    *,
    incremental_step: Dict[str, Any],
    draft_prompt_view: Dict[str, Any],
    include_standard_subset: bool = True,
) -> str:
    standards = choose_standard_sections(incremental_step) if include_standard_subset else []
    standards_text = "\n".join(f"- {x}" for x in standards)

    return dedent(
        f"""
        You are given a newly added table in an incremental ontology learning process.

        ## Current task
        Update the current global ontology/mapping draft based on the new table.

        ## New table incremental context
        {json.dumps(incremental_step, ensure_ascii=False, indent=2)}

        ## Current draft view
        {json.dumps(draft_prompt_view, ensure_ascii=False, indent=2)}

        ## Local decision reminders
        {standards_text if standards_text else "(omitted)"}

        ## STRICT OUTPUT RULES
        {PATCH_SCHEMA_RULES}

        ## STRICT PATCH SCHEMA
        {json.dumps(STRICT_PATCH_SCHEMA, ensure_ascii=False, indent=2)}

        ## EXAMPLES
        {STRICT_EXAMPLE}

        ## Additional instructions
        - Return JSON only.
        - Do NOT add commentary outside JSON.
        - Keep unchanged sections empty.
        - If evidence is weak, record it in remaining_ambiguities or needs_probe.
        """
    ).strip()


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


def render_messages_text(messages: List[Dict[str, str]]) -> str:
    return "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages)
