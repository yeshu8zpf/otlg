from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClassDef:
    id: str
    label: str
    source_tables: List[str] = field(default_factory=list)
    identifier_columns: List[str] = field(default_factory=list)
    instance_id_template: str = ""
    status: str = "proposed"
    confidence: Optional[float] = None
    description: str = ""
    # Burr/D2RQ related
    prefix: str = ""
    mapping_id: str = ""
    bnode_id_columns: List[str] = field(default_factory=list)
    join_paths: List[List[str]] = field(default_factory=list)
    condition: List[List[str]] = field(default_factory=list)
    subclass_of: List[str] = field(default_factory=list)
    additional_class_definition_property: List[str] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyDef:
    id: str
    label: str
    domain_class: str
    range_type: str = "string"
    source_columns: List[str] = field(default_factory=list)
    join_paths: List[List[str]] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    description: str = ""
    # Burr/D2RQ related
    mapping_id: str = ""
    datatype: str = ""
    dynamic_property: str = ""
    uri_column: List[str] = field(default_factory=list)
    pattern: str = ""
    uri_pattern: str = ""
    sql_expression: str = ""
    constant_value: Any = None
    condition: List[List[str]] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectPropertyDef:
    id: str
    label: str
    domain_class: str
    range_class: str
    join_paths: List[List[str]] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    description: str = ""
    # Burr/D2RQ related
    mapping_id: str = ""
    dynamic_property: str = ""
    condition: List[List[str]] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubclassRelation:
    id: str
    child_class: str
    parent_class: str
    status: str = "proposed"
    confidence: Optional[float] = None
    description: str = ""
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassMapping:
    class_id: str
    from_tables: List[str] = field(default_factory=list)
    identifier_columns: List[str] = field(default_factory=list)
    instance_id_template: str = ""
    status: str = "proposed"
    confidence: Optional[float] = None
    # Burr/D2RQ related
    identifier_kind: str = ""
    prefix: str = ""
    mapping_id: str = ""
    bnode_id_columns: List[str] = field(default_factory=list)
    join_paths: List[List[str]] = field(default_factory=list)
    condition: List[List[str]] = field(default_factory=list)
    subclass_of: List[str] = field(default_factory=list)
    additional_class_definition_property: List[str] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyMapping:
    property_id: str
    from_class: str = ""
    source_table: str = ""
    column: str = ""
    source_columns: List[str] = field(default_factory=list)
    joins: List[List[str]] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    # Burr/D2RQ related
    value_kind: str = ""
    mapping_id: str = ""
    datatype: str = ""
    uri_column: List[str] = field(default_factory=list)
    pattern: str = ""
    uri_pattern: str = ""
    sql_expression: str = ""
    constant_value: Any = None
    condition: List[List[str]] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    dynamic_property: str = ""
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectPropertyMapping:
    property_id: str
    from_class: str = ""
    to_class: str = ""
    joins: List[List[str]] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    # Burr/D2RQ related
    mapping_id: str = ""
    dynamic_property: str = ""
    condition: List[List[str]] = field(default_factory=list)
    translate_with: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)
