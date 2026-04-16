This package is a split refactor of the original `normalize.py`.

Public entrypoint:
- `from normalization import normalize_model_output_robust`

Coverage added for Burr/D2RQ-related fields:
- class-side:
  - `bNodeIdColumns`
  - `condition`
  - `join_paths`
  - `subclass_of`
  - `additional_class_definition_property`
  - `translate_with`
  - `mapping_id`
- data-property-side:
  - `uri_column`
  - `pattern`
  - `uri_pattern`
  - `sql_expression`
  - `constant_value`
  - `datatype`
  - `condition`
  - `translate_with`
  - `dynamic_property`
  - `mapping_id`
- object-property-side:
  - `dynamic_property`
  - `condition`
  - `translate_with`
  - `mapping_id`

A compatibility `normalize.py` shim is included.
