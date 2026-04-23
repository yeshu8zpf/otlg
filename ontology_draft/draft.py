from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from normalization.runner import normalize_model_output_robust

from .builder import (
    build_class_def,
    build_class_mapping,
    build_data_property_def,
    build_data_property_mapping,
    build_object_property_def,
    build_object_property_mapping,
    build_subclass_relation,
)
from .helpers import (
    as_list,
    as_str,
    coerce_float01,
    copy_deep,
    dedup_keep_order,
    ensure_burr_template,
    ensure_qualified_column,
    extract_identifier_columns,
    infer_tables_from_template,
    join_to_burr_string,
    label_from_class_id,
    normalize_class_id,
    normalize_data_property_id,
    normalize_join,
    normalize_object_property_id,
    safe_dict,
    to_burr_safe_classmap_name,
    to_burr_safe_property_name,
)
from .report import NormalizationReport, get_normalization_report
from .types import (
    ClassDef,
    ClassMapping,
    DataPropertyDef,
    DataPropertyMapping,
    ObjectPropertyDef,
    ObjectPropertyMapping,
    SubclassRelation,
)


@dataclass
class OntologyDraft:
    classes: List[ClassDef] = field(default_factory=list)
    data_properties: List[DataPropertyDef] = field(default_factory=list)
    object_properties: List[ObjectPropertyDef] = field(default_factory=list)
    subclass_relations: List[SubclassRelation] = field(default_factory=list)

    class_mappings: List[ClassMapping] = field(default_factory=list)
    data_property_mappings: List[DataPropertyMapping] = field(default_factory=list)
    object_property_mappings: List[ObjectPropertyMapping] = field(default_factory=list)

    diagnostics: Dict[str, Any] = field(default_factory=dict)
    normalization_report_obj: Optional[NormalizationReport] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], already_normalized: bool = False) -> "OntologyDraft":
        normalized = copy_deep(payload)
        if not already_normalized:
            normalized = normalize_model_output_robust(payload)

        report = get_normalization_report(normalized)

        draft = cls(
            classes=[build_class_def(x) for x in as_list(normalized.get("classes"))],
            data_properties=[build_data_property_def(x) for x in as_list(normalized.get("data_properties"))],
            object_properties=[build_object_property_def(x) for x in as_list(normalized.get("object_properties"))],
            subclass_relations=[build_subclass_relation(x) for x in as_list(normalized.get("subclass_relations"))],
            class_mappings=[build_class_mapping(x) for x in as_list(normalized.get("class_mappings"))],
            data_property_mappings=[build_data_property_mapping(x) for x in as_list(normalized.get("data_property_mappings"))],
            object_property_mappings=[build_object_property_mapping(x) for x in as_list(normalized.get("object_property_mappings"))],
            diagnostics=safe_dict(normalized.get("diagnostics")),
            normalization_report_obj=report,
            extras={
                k: v
                for k, v in normalized.items()
                if k not in {
                    "classes",
                    "data_properties",
                    "object_properties",
                    "subclass_relations",
                    "class_mappings",
                    "data_property_mappings",
                    "object_property_mappings",
                    "diagnostics",
                    "normalization_report",
                }
            },
        )
        draft._repair_internal_consistency()
        return draft

    def normalization_report(self) -> Dict[str, Any]:
        if self.normalization_report_obj is None:
            return {}
        return self.normalization_report_obj.summary()

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "classes": [asdict(x) for x in self.classes],
            "data_properties": [asdict(x) for x in self.data_properties],
            "object_properties": [asdict(x) for x in self.object_properties],
            "subclass_relations": [asdict(x) for x in self.subclass_relations],
            "class_mappings": [asdict(x) for x in self.class_mappings],
            "data_property_mappings": [asdict(x) for x in self.data_property_mappings],
            "object_property_mappings": [asdict(x) for x in self.object_property_mappings],
            "diagnostics": copy_deep(self.diagnostics),
            "normalization_report": self.normalization_report(),
        }
        if self.extras:
            out["extras"] = copy_deep(self.extras)
        return out

    def class_index(self) -> Dict[str, ClassDef]:
        return {x.id: x for x in self.classes if x.id}

    def data_property_index(self) -> Dict[str, DataPropertyDef]:
        return {x.id: x for x in self.data_properties if x.id}

    def object_property_index(self) -> Dict[str, ObjectPropertyDef]:
        return {x.id: x for x in self.object_properties if x.id}

    def class_mapping_index(self) -> Dict[str, ClassMapping]:
        return {x.class_id: x for x in self.class_mappings if x.class_id}

    def data_property_mapping_index(self) -> Dict[str, DataPropertyMapping]:
        return {x.property_id: x for x in self.data_property_mappings if x.property_id}

    def object_property_mapping_index(self) -> Dict[str, ObjectPropertyMapping]:
        return {x.property_id: x for x in self.object_property_mappings if x.property_id}

    def _is_exportable_status(self, status: Optional[str]) -> bool:
        s = str(status or "").strip().lower()
        if not s:
            return True
        return s not in {"rejected", "invalid", "discarded", "dropped"}

    def _effective_class_tables(self, c: ClassDef, cm: Optional[ClassMapping]) -> List[str]:
        out = list(c.source_tables or [])
        if cm is not None:
            out.extend(cm.from_tables or [])
            if not out and cm.instance_id_template:
                out.extend(infer_tables_from_template(cm.instance_id_template))
        if not out and c.instance_id_template:
            out.extend(infer_tables_from_template(c.instance_id_template))
        return dedup_keep_order([x for x in out if x])

    def _effective_identifier_columns(self, c: ClassDef, cm: Optional[ClassMapping]) -> List[str]:
        out = list(c.identifier_columns or [])
        if cm is not None:
            out.extend(cm.identifier_columns or [])
            if not out and cm.instance_id_template:
                out.extend(extract_identifier_columns(cm.instance_id_template))
        if not out and c.instance_id_template:
            out.extend(extract_identifier_columns(c.instance_id_template))
        if not out:
            out.extend(c.bnode_id_columns or [])
            if cm is not None:
                out.extend(cm.bnode_id_columns or [])
        return dedup_keep_order([x for x in out if x])

    def _effective_instance_id_template(self, c: ClassDef, cm: Optional[ClassMapping]) -> str:
        if cm is not None and cm.instance_id_template:
            return cm.instance_id_template
        return c.instance_id_template or ""

    def _effective_data_property_columns(self, p: DataPropertyDef, dm: Optional[DataPropertyMapping]) -> List[str]:
        out = list(p.source_columns or [])
        if dm is not None:
            if dm.column:
                out.append(dm.column)
            out.extend(dm.source_columns or [])
            out.extend(dm.uri_column or [])
        out.extend(p.uri_column or [])
        return dedup_keep_order([x for x in out if x])

    def _effective_data_property_joins(self, p: DataPropertyDef, dm: Optional[DataPropertyMapping]) -> List[List[str]]:
        if p.join_paths:
            return [list(normalize_join(j)) for j in p.join_paths if normalize_join(j)]
        if dm is not None and dm.joins:
            return [list(normalize_join(j)) for j in dm.joins if normalize_join(j)]
        return []

    def _effective_object_property_joins(self, p: ObjectPropertyDef, om: Optional[ObjectPropertyMapping]) -> List[List[str]]:
        if p.join_paths:
            return [list(normalize_join(j)) for j in p.join_paths if normalize_join(j)]
        if om is not None and om.joins:
            return [list(normalize_join(j)) for j in om.joins if normalize_join(j)]
        return []

    def _repair_internal_consistency(self) -> None:
        class_idx = self.class_index()
        cm_idx = self.class_mapping_index()
        dpm_idx = self.data_property_mapping_index()
        opm_idx = self.object_property_mapping_index()

        for c in self.classes:
            if not c.source_tables:
                cm = cm_idx.get(c.id)
                if cm and cm.from_tables:
                    c.source_tables = list(cm.from_tables)
            if not c.identifier_columns:
                cm = cm_idx.get(c.id)
                if cm and cm.identifier_columns:
                    c.identifier_columns = list(cm.identifier_columns)
            if not c.instance_id_template:
                cm = cm_idx.get(c.id)
                if cm and cm.instance_id_template:
                    c.instance_id_template = cm.instance_id_template
            if not c.source_tables and c.instance_id_template:
                c.source_tables = infer_tables_from_template(c.instance_id_template)
            if not c.identifier_columns and c.instance_id_template:
                c.identifier_columns = extract_identifier_columns(c.instance_id_template)
            if not c.bnode_id_columns:
                cm = cm_idx.get(c.id)
                if cm and cm.bnode_id_columns:
                    c.bnode_id_columns = list(cm.bnode_id_columns)
            for key in ["join_paths", "condition", "subclass_of", "additional_class_definition_property", "translate_with"]:
                if not getattr(c, key):
                    cm = cm_idx.get(c.id)
                    if cm is not None and getattr(cm, key, None):
                        setattr(c, key, copy_deep(getattr(cm, key)))

        for p in self.data_properties:
            p.domain_class = normalize_class_id(p.domain_class)
            if not p.id:
                p.id = normalize_data_property_id(p.domain_class, p.label)
            dm = dpm_idx.get(p.id)
            if dm:
                if not dm.from_class:
                    dm.from_class = p.domain_class
                if not p.source_columns:
                    cols = []
                    if dm.column:
                        cols.append(dm.column)
                    cols.extend(dm.source_columns or [])
                    cols.extend(dm.uri_column or [])
                    p.source_columns = dedup_keep_order([c for c in cols if c])
                if not p.join_paths and dm.joins:
                    p.join_paths = [list(normalize_join(j)) for j in dm.joins if normalize_join(j)]
                if not p.domain_class and dm.from_class:
                    p.domain_class = normalize_class_id(dm.from_class)
                for key in ["datatype", "dynamic_property", "uri_column", "pattern", "uri_pattern", "sql_expression", "constant_value", "condition", "translate_with", "mapping_id"]:
                    if not getattr(p, key) and getattr(dm, key, None):
                        setattr(p, key, copy_deep(getattr(dm, key)))

        for p in self.object_properties:
            p.domain_class = normalize_class_id(p.domain_class)
            p.range_class = normalize_class_id(p.range_class)
            if not p.id:
                p.id = normalize_object_property_id(p.domain_class, p.label)
            om = opm_idx.get(p.id)
            if om:
                if not om.from_class:
                    om.from_class = p.domain_class
                if not om.to_class:
                    om.to_class = p.range_class
                if not p.join_paths and om.joins:
                    p.join_paths = [list(normalize_join(j)) for j in om.joins if normalize_join(j)]
                for key in ["dynamic_property", "condition", "translate_with", "mapping_id"]:
                    if not getattr(p, key) and getattr(om, key, None):
                        setattr(p, key, copy_deep(getattr(om, key)))

        for m in self.class_mappings:
            m.class_id = normalize_class_id(m.class_id)
            if not m.from_tables and m.instance_id_template:
                m.from_tables = infer_tables_from_template(m.instance_id_template)
            if not m.identifier_columns and m.instance_id_template:
                m.identifier_columns = extract_identifier_columns(m.instance_id_template)

        for m in self.data_property_mappings:
            if m.from_class:
                m.from_class = normalize_class_id(m.from_class)
            if m.joins:
                m.joins = [list(normalize_join(j)) for j in m.joins if normalize_join(j)]

        for m in self.object_property_mappings:
            if m.from_class:
                m.from_class = normalize_class_id(m.from_class)
            if m.to_class:
                m.to_class = normalize_class_id(m.to_class)
            if m.joins:
                m.joins = [list(normalize_join(j)) for j in m.joins if normalize_join(j)]

        for rel in self.subclass_relations:
            rel.child_class = normalize_class_id(rel.child_class)
            rel.parent_class = normalize_class_id(rel.parent_class)
            if not rel.id and rel.child_class and rel.parent_class:
                rel.id = f"SubclassRelation:{rel.child_class}->{rel.parent_class}"

        if not self.class_mappings:
            for c in self.classes:
                if c.source_tables or c.instance_id_template or c.bnode_id_columns:
                    self.class_mappings.append(
                        ClassMapping(
                            class_id=c.id,
                            from_tables=list(c.source_tables or infer_tables_from_template(c.instance_id_template)),
                            identifier_columns=list(c.identifier_columns or extract_identifier_columns(c.instance_id_template)),
                            instance_id_template=c.instance_id_template or "",
                            status=c.status or "proposed",
                            confidence=c.confidence,
                            bnode_id_columns=list(c.bnode_id_columns or []),
                            join_paths=copy_deep(c.join_paths),
                            condition=copy_deep(c.condition),
                            subclass_of=list(c.subclass_of),
                            additional_class_definition_property=list(c.additional_class_definition_property),
                            translate_with=list(c.translate_with),
                            mapping_id=c.mapping_id,
                            prefix=c.prefix,
                        )
                    )

    def validate(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        class_idx = self.class_index()
        data_prop_idx = self.data_property_index()
        object_prop_idx = self.object_property_index()

        class_ids = set(class_idx.keys())
        data_prop_ids = set(data_prop_idx.keys())
        object_prop_ids = set(object_prop_idx.keys())

        if len(class_ids) != len(self.classes):
            errors.append("Duplicate class ids found.")
        if len(data_prop_ids) != len(self.data_properties):
            errors.append("Duplicate data property ids found.")
        if len(object_prop_ids) != len(self.object_properties):
            errors.append("Duplicate object property ids found.")

        class_map_idx = self.class_mapping_index()
        dp_map_idx = self.data_property_mapping_index()
        op_map_idx = self.object_property_mapping_index()

        for c in self.classes:
            if self._is_exportable_status(c.status):
                cm = class_map_idx.get(c.id)
                if cm is None:
                    errors.append(f"Class {c.id} has no class mapping.")
                else:
                    effective_tables = self._effective_class_tables(c, cm)
                    effective_template = self._effective_instance_id_template(c, cm)
                    if not effective_tables and not (c.bnode_id_columns or cm.bnode_id_columns):
                        errors.append(f"Class {c.id} has neither source_tables nor class_mapping.from_tables nor bNodeIdColumns.")
                    if not effective_template and not (c.bnode_id_columns or cm.bnode_id_columns):
                        errors.append(f"Class mapping for {c.id} has no instance_id_template and no bNodeIdColumns.")

        for p in self.data_properties:
            if p.domain_class not in class_ids:
                errors.append(f"Data property {p.id} references unknown domain class {p.domain_class}.")
            if self._is_exportable_status(p.status):
                dm = dp_map_idx.get(p.id)
                if dm is None:
                    errors.append(f"Data property {p.id} has no data_property_mapping.")
                else:
                    effective_cols = self._effective_data_property_columns(p, dm)
                    if not effective_cols and not (p.pattern or p.uri_pattern or p.sql_expression or p.constant_value is not None):
                        errors.append(f"Data property {p.id} has neither source_columns/uriColumn nor pattern/uriPattern/sqlExpression/constantValue.")
                    if dm.from_class and p.domain_class and dm.from_class != p.domain_class:
                        errors.append(f"Data property {p.id} domain mismatch: property={p.domain_class}, mapping={dm.from_class}.")

        for p in self.object_properties:
            if p.domain_class not in class_ids:
                errors.append(f"Object property {p.id} references unknown domain class {p.domain_class}.")
            if p.range_class not in class_ids:
                errors.append(f"Object property {p.id} references unknown range class {p.range_class}.")
            if self._is_exportable_status(p.status):
                om = op_map_idx.get(p.id)
                if om is None:
                    errors.append(f"Object property {p.id} has no object_property_mapping.")
                else:
                    effective_joins = self._effective_object_property_joins(p, om)
                    if not effective_joins and not p.dynamic_property:
                        errors.append(f"Object property {p.id} has neither join_paths/object_property_mapping.joins nor dynamicProperty.")
                    if om.from_class and p.domain_class and om.from_class != p.domain_class:
                        errors.append(f"Object property {p.id} domain mismatch: property={p.domain_class}, mapping={om.from_class}.")
                    if om.to_class and p.range_class and om.to_class != p.range_class:
                        errors.append(f"Object property {p.id} range mismatch: property={p.range_class}, mapping={om.to_class}.")

        for rel in self.subclass_relations:
            if rel.child_class not in class_ids:
                errors.append(f"Subclass relation references unknown child class {rel.child_class}.")
            if rel.parent_class not in class_ids:
                errors.append(f"Subclass relation references unknown parent class {rel.parent_class}.")

        return len(errors) == 0, errors

    def to_burr_mapping(self) -> Dict[str, Any]:
        class_map_idx = self.class_mapping_index()
        dp_map_idx = self.data_property_mapping_index()
        op_map_idx = self.object_property_mapping_index()

        out: Dict[str, Any] = {
            "classes": [],
            "object_properties": [],
            "data_properties": [],
        }

        for c in self.classes:
            if not self._is_exportable_status(c.status):
                continue
            cm = class_map_idx.get(c.id)
            if cm is None:
                continue

            effective_tables = self._effective_class_tables(c, cm)
            effective_identifier_columns = self._effective_identifier_columns(c, cm)
            effective_template = self._effective_instance_id_template(c, cm)
            fallback_table = effective_tables[0] if effective_tables else ""
            repaired_template = ensure_burr_template(
                effective_template,
                fallback_table=fallback_table,
                fallback_identifier_columns=effective_identifier_columns,
            )

            safe_class_name = to_burr_safe_classmap_name(c.label)
            item = {
                "class": safe_class_name,
                "name": safe_class_name,
            }

            # Prefer blank-node encoding if available and no stable template
            bnode_cols = dedup_keep_order([x for x in (c.bnode_id_columns or []) + (cm.bnode_id_columns or []) if x])
            if bnode_cols and (cm.identifier_kind == "bnode" or not repaired_template):
                item["bNodeIdColumns"] = bnode_cols
            elif repaired_template:
                item["id"] = repaired_template
            else:
                continue

            if c.prefix or cm.prefix:
                item["prefix"] = c.prefix or cm.prefix
            if c.mapping_id or cm.mapping_id:
                item["mapping_id"] = c.mapping_id or cm.mapping_id
            if c.join_paths or cm.join_paths:
                item["join"] = [join_to_burr_string(j) for j in (c.join_paths or cm.join_paths) if j]
            if c.condition or cm.condition:
                item["condition"] = [join_to_burr_string(j) for j in (c.condition or cm.condition) if j]
            if c.subclass_of or cm.subclass_of:
                item["subClassOf"] = list(c.subclass_of or cm.subclass_of)
            if c.additional_class_definition_property or cm.additional_class_definition_property:
                item["additionalClassDefinitionProperty"] = list(c.additional_class_definition_property or cm.additional_class_definition_property)
            if c.translate_with or cm.translate_with:
                item["translateWith"] = list(c.translate_with or cm.translate_with)

            if c.extras:
                item.update(c.extras)
            out["classes"].append(item)

        for p in self.object_properties:
            if not self._is_exportable_status(p.status):
                continue
            om = op_map_idx.get(p.id)
            if om is None:
                continue

            joins = self._effective_object_property_joins(p, om)
            item = {
                "property": to_burr_safe_property_name(p.label),
                "belongsToClassMap": label_from_class_id(om.from_class or p.domain_class),
                "refersToClassMap": label_from_class_id(om.to_class or p.range_class),
            }
            if joins:
                item["join"] = [join_to_burr_string(list(normalize_join(j))) for j in joins if normalize_join(j)]
            if p.dynamic_property or om.dynamic_property:
                item["dynamicProperty"] = p.dynamic_property or om.dynamic_property
            if p.condition or om.condition:
                item["condition"] = [join_to_burr_string(j) for j in (p.condition or om.condition) if j]
            if p.translate_with or om.translate_with:
                item["translateWith"] = list(p.translate_with or om.translate_with)
            if p.mapping_id or om.mapping_id:
                item["mapping_id"] = p.mapping_id or om.mapping_id
            if p.extras:
                item.update(p.extras)
            out["object_properties"].append(item)

        for p in self.data_properties:
            if not self._is_exportable_status(p.status):
                continue
            dm = dp_map_idx.get(p.id)
            if dm is None:
                continue

            effective_cols = self._effective_data_property_columns(p, dm)
            source_table = as_str(dm.source_table).strip()
            repaired_cols = [ensure_qualified_column(col, source_table) for col in effective_cols]
            repaired_cols = [c for c in repaired_cols if c]
            joins = self._effective_data_property_joins(p, dm)

            item = {
                "property": to_burr_safe_property_name(p.label),
                "belongsToClassMap": label_from_class_id(dm.from_class or p.domain_class),
            }

            # Choose one of Burr-supported value carriers
            if repaired_cols:
                item["column"] = repaired_cols[0]
            elif p.uri_column or dm.uri_column:
                item["uriColumn"] = (p.uri_column or dm.uri_column)[0]
            elif p.pattern or dm.pattern:
                item["pattern"] = p.pattern or dm.pattern
            elif p.uri_pattern or dm.uri_pattern:
                item["uriPattern"] = p.uri_pattern or dm.uri_pattern
            elif p.sql_expression or dm.sql_expression:
                item["sqlExpression"] = p.sql_expression or dm.sql_expression
            elif p.constant_value is not None or dm.constant_value is not None:
                item["constantValue"] = p.constant_value if p.constant_value is not None else dm.constant_value
            else:
                continue

            if joins:
                item["join"] = [join_to_burr_string(list(normalize_join(j))) for j in joins if normalize_join(j)]
            if p.datatype or dm.datatype:
                item["datatype"] = p.datatype or dm.datatype
            if p.condition or dm.condition:
                item["condition"] = [join_to_burr_string(j) for j in (p.condition or dm.condition) if j]
            if p.translate_with or dm.translate_with:
                item["translateWith"] = list(p.translate_with or dm.translate_with)
            if p.mapping_id or dm.mapping_id:
                item["mapping_id"] = p.mapping_id or dm.mapping_id
            if p.dynamic_property or dm.dynamic_property:
                item["dynamicProperty"] = p.dynamic_property or dm.dynamic_property
            if p.extras:
                item.update(p.extras)
            out["data_properties"].append(item)

        return out
