from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .scenario import clean_schema_sql_for_prompt, compact_table_definitions


SYSTEM_PROMPT = """You are an ontology learning assistant for relational databases.

Your task:
Given a relational database schema, optional sampled rows, and optional tool-derived structural evidence,
construct:
1. a relational-database-derived ontology draft
2. executable mappings from database elements to ontology elements

Important:
- Focus on ontology structure and mappings, not only naming.
- Optimize for mapping-faithful output, not just plausible labels.
- Be conservative: do not add inverse object properties unless strongly justified.
- Use tool-derived evidence when available.
- Output ONLY valid JSON.
- First determine the semantic role of each database element, then decide its ontology/mapping representation.
"""


BURR_FIELD_GUIDE = """
### Burr-oriented mapping coverage
When constructing mappings, consider the full range of Burr/D2RQ-relevant fields that may be needed downstream.

For class mappings, relevant fields may include:
- id
- class
- name
- prefix
- bNodeIdColumns
- condition
- join
- subClassOf
- additionalClassDefinitionProperty
- translateWith
- mapping_id

For property mappings, relevant fields may include:
- property
- belongsToClass / belongsToClassMap
- refersToClass / refersToClassMap
- dynamicProperty
- join
- condition
- column
- uriColumn
- pattern
- uriPattern
- sqlExpression
- constantValue
- datatype
- translateWith
- mapping_id

Use these only when justified by schema / evidence. Do not invent fields unsupported by the scenario.
If a class should be blank-node based, make that explicit via bNodeIdColumns.
If a property value should be URI-valued rather than literal-valued, distinguish uriColumn / uriPattern from column / pattern.
"""


ONTOLOGY_DECISION_STANDARD = """
## Ontology / Mapping decision standard

Apply the following standards explicitly before producing the final JSON.

### A. Class decisions
1. Entity class
- Represent something as a class if it has stable identity, behaves like a domain entity,
  and naturally serves as a relation endpoint.

2. Value-domain class
- If a non-FK value column contains reusable named concepts/entities rather than free text,
  consider lifting that value domain into a class.

3. Value-object class
- If multiple columns jointly form a structured object (for example address-like bundles),
  and the object depends on a host entity and lacks a natural global URI, consider a value-object class.

4. Association class
- If a connector table has meaningful payload attributes describing the relation itself,
  prefer reification into an association class instead of collapsing to a direct relation.

5. Restricted class
- If class membership is defined by an explicit condition that changes the class extension,
  model that as a restricted class instead of turning the condition into an ordinary property.

6. Type-promotion caution
- Do NOT promote type/category/role values into subclasses by default.
- Prefer typing assertions unless there is strong evidence that the promoted class has stable ontology-level meaning.

### B. Relation decisions
1. Object property
- Use an object property when two class instances are linked semantically.

2. Conditional relation family
- If the same join skeleton supports different semantics based on a discriminator column
  (for example relationtype / role / kind), split them into distinct relations instead of one generic relation.

3. Shortcut relation
- Only materialize a shortcut relation if the direct projected relation has stable semantic meaning.
- Do not add arbitrary shortcuts blindly.

4. Extra relation caution
- A schema-supported relation may still be conservative or optional.
  Avoid inventing extra relations unless structural evidence is clear.

### C. Attribute decisions
1. Literal data property
- Use a literal property for ordinary text, numbers, dates, and scalar measurements.

2. Resource-valued property
- If a value is already a URI or should become a URI-like resource target
  (for example homepage, photo, sameAs target, mailto email), do not treat it as an ordinary literal.

3. Composed data property
- If multiple columns together form one ontology-level value
  (for example first name + last name -> full name), prefer the composed property when semantically appropriate.

4. Typing assertion
- If a column expresses instance type/category membership,
  prefer a typing assertion over an ordinary literal property.

### D. Identity decisions
1. uriPattern
- Use uriPattern when identity should be represented as a URI constructed from one or more columns.

2. uriColumn
- Use uriColumn when the database already stores the intended URI and the value should remain a resource.

3. bNodeIdColumns
- Use bNodeIdColumns when an object should exist as a node but has no natural global URI,
  and local identity anchored by host/entity columns is sufficient.

4. Multiple class maps
- The same conceptual class may require multiple class maps if the database provides multiple source identities.
  Do not collapse them blindly if source-specific identity matters.

### E. Condition and join decisions
1. Class membership condition
- A condition belongs to a class if it defines which rows instantiate that class.

2. Relation discriminator condition
- A condition belongs to a relation if it distinguishes different relation meanings.

3. Semantic filter condition
- Keep a condition if it removes semantically invalid values.

4. Non-essential guard
- Avoid adding IS NOT NULL-style conditions unless they are truly semantically necessary.
- Null guards are usually not mapping identity.

5. Essential joins
- Keep joins required to ground owner/target semantics.

6. Redundant joins
- Avoid stronger-than-necessary joins when a simpler semantically sufficient join exists.

### Default preferences
- Prefer typing assertion over subclass promotion unless subclass evidence is strong.
- Prefer literal property over value-domain class unless the value domain behaves like reusable concepts.
- Prefer value-object class over flat literals only when structured-object evidence is strong.
- Prefer minimal semantically sufficient joins over stronger joins.
- Prefer semantic conditions over non-semantic null guards.
"""


USER_PROMPT_TEMPLATE = """You are given a relational database scenario.

## Scenario path
{scenario_path}

{schema_sql_section}
{table_defs_section}
{sample_rows_section}
{tool_context_section}

{ontology_decision_standard}

## Output format
Return a JSON object with the following top-level keys:
- classes
- data_properties
- object_properties
- subclass_relations
- class_mappings
- data_property_mappings
- object_property_mappings
- diagnostics

### Canonical draft constraints
- Use exact top-level keys listed above.
- For classes, use fields:
  - id
  - label
  - status
  - confidence
  - description (optional)

- For data_properties, use fields:
  - id
  - label
  - domain
  - datatype
  - status
  - confidence

- For object_properties, use fields:
  - id
  - label
  - domain
  - range
  - join_paths
  - status
  - confidence

- For class_mappings, use fields:
  - class_id
  - instance_id_template
  - from_tables
  - identifier_columns
  - status
  - confidence
  - identifier_kind (optional: "uri_pattern" | "bnode")
  - bnode_id_columns (optional)
  - condition (optional)
  - join_paths (optional)
  - subclass_of (optional)
  - translate_with (optional)

- For data_property_mappings, use fields:
  - data_property_id
  - source_table
  - source_columns
  - applies_to_class
  - join_paths
  - value_template
  - status
  - confidence
  - value_kind (optional: "column" | "uri_column" | "pattern" | "uri_pattern" | "sql_expression" | "constant")
  - datatype (optional)
  - condition (optional)
  - translate_with (optional)
  - constant_value (optional)
  - sql_expression (optional)

- For object_property_mappings, use fields:
  - object_property_id
  - from_class
  - to_class
  - from_tables
  - join_paths
  - source_identifier_columns
  - target_identifier_columns
  - status
  - confidence
  - condition (optional)
  - dynamic_property (optional)
  - translate_with (optional)

### Join path format
Use ONLY this format:
[
  ["hotel.id", "=", "room.hotel_id"]
]

Do not output join_paths as objects or free-form strings.

### Important modeling guidance
- Prefer one object property direction unless the inverse is explicitly necessary.
- If a table is a weak entity, its identifier should reflect dependency.
- If a table is a pure connector table, prefer a relationship rather than a class.
- If a connector table has meaningful extra attributes, consider reification.
- If a class should not have a stable URI pattern and is better modeled as a blank-node-based class, say so explicitly.
- Distinguish literal-valued mappings from URI-valued mappings.
- Do not invent domain properties unsupported by schema or samples.
- When tool-derived evidence is present, treat it as strong structural guidance.
- For data properties sourced from auxiliary/value tables, include join_paths that connect the owner class instance to the value table.
- For type/category/role columns, prefer typing-aware modeling over naive literal output.
- For condition-bearing classes or relations, decide whether the condition is semantically defining or only a non-essential guard.
- For mapping-based faithfulness, preserve class restrictions, resource-valued properties, multi-source identities, and relation splitting when structurally justified.

{burr_field_guide}

Return JSON only.
"""


def build_prompt(
    scenario_path: Path,
    schema_sql_text: str,
    table_defs: Dict[str, str],
    sample_rows: Dict[str, List[Dict[str, Any]]],
    tool_context: Dict[str, Any],
    *,
    include_schema_sql: bool,
    include_table_defs: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
) -> str:
    schema_sql_section = ""
    if include_schema_sql:
        schema_sql_section = "## Compact schema SQL\n" + clean_schema_sql_for_prompt(schema_sql_text) + "\n"

    table_defs_section = ""
    if include_table_defs:
        table_defs_section = "## Parsed table definitions\n" + json.dumps(
            compact_table_definitions(table_defs), indent=2, ensure_ascii=False
        ) + "\n"

    sample_rows_section = ""
    if include_sample_rows:
        compact_sample_rows = {k: v[:3] for k, v in sorted(sample_rows.items())}
        sample_rows_section = "## Sample rows\n" + json.dumps(
            compact_sample_rows, indent=2, ensure_ascii=False
        ) + "\n"

    tool_context_section = ""
    if include_tool_context:
        tool_context_section = "## Tool-derived structural evidence\n" + json.dumps(
            tool_context, indent=2, ensure_ascii=False
        ) + "\n"

    return USER_PROMPT_TEMPLATE.format(
        scenario_path=str(scenario_path),
        schema_sql_section=schema_sql_section,
        table_defs_section=table_defs_section,
        sample_rows_section=sample_rows_section,
        tool_context_section=tool_context_section,
        ontology_decision_standard=ONTOLOGY_DECISION_STANDARD.strip(),
        burr_field_guide=BURR_FIELD_GUIDE.strip(),
    )
