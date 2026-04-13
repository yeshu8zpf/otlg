from __future__ import annotations

from typing import Any, Dict, List, Optional


class MappingVerifierLite:
    """
    Lightweight verifier over canonical draft dicts.

    Design goals:
    - cheap
    - dependency-light
    - aligned with current normalize -> draft schema
    - check effective closure instead of only local field presence
    - produce structured issues for future feedback loops
    """

    def _issue(self, level: str, code: str, message: str, **context: Any) -> Dict[str, Any]:
        return {
            "level": level,
            "code": code,
            "message": message,
            "context": context,
        }

    def _index_by_id(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for x in items or []:
            xid = x.get("id")
            if xid:
                out[str(xid)] = x
        return out

    def _index_by_key(self, items: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for x in items or []:
            k = x.get(key)
            if k:
                out[str(k)] = x
        return out

    def _norm_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _non_empty_strings(self, xs: Any) -> List[str]:
        out: List[str] = []
        for x in self._norm_list(xs):
            s = str(x).strip()
            if s:
                out.append(s)
        # stable dedup
        return list(dict.fromkeys(out))

    def _status_is_exportable(self, status: Optional[str]) -> bool:
        s = str(status or "").strip().lower()
        if not s:
            return True
        return s not in {"rejected", "invalid", "discarded", "dropped"}

    def _effective_class_tables(
        self,
        c: Dict[str, Any],
        cm: Optional[Dict[str, Any]],
    ) -> List[str]:
        out = []
        out.extend(self._non_empty_strings(c.get("source_tables")))
        if cm is not None:
            out.extend(self._non_empty_strings(cm.get("from_tables")))
        return list(dict.fromkeys(out))

    def _effective_identifier_columns(
        self,
        c: Dict[str, Any],
        cm: Optional[Dict[str, Any]],
    ) -> List[str]:
        out = []
        out.extend(self._non_empty_strings(c.get("identifier_columns")))
        if cm is not None:
            out.extend(self._non_empty_strings(cm.get("identifier_columns")))
        return list(dict.fromkeys(out))

    def _effective_instance_template(
        self,
        c: Dict[str, Any],
        cm: Optional[Dict[str, Any]],
    ) -> str:
        if cm is not None and str(cm.get("instance_id_template") or "").strip():
            return str(cm.get("instance_id_template")).strip()
        return str(c.get("instance_id_template") or "").strip()

    def _effective_data_property_columns(
        self,
        p: Dict[str, Any],
        dm: Optional[Dict[str, Any]],
    ) -> List[str]:
        out = []
        out.extend(self._non_empty_strings(p.get("source_columns")))
        if dm is not None:
            out.extend(self._non_empty_strings(dm.get("source_columns")))
            column = str(dm.get("column") or "").strip()
            if column:
                out.append(column)
        return list(dict.fromkeys(out))

    def _effective_object_property_joins(
        self,
        p: Dict[str, Any],
        om: Optional[Dict[str, Any]],
    ) -> List[Any]:
        property_joins = self._norm_list(p.get("join_paths"))
        if property_joins:
            return property_joins
        if om is not None:
            return self._norm_list(om.get("joins"))
        return []

    def verify_draft_dict(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        classes = draft.get("classes", []) or []
        data_properties = draft.get("data_properties", []) or []
        object_properties = draft.get("object_properties", []) or []
        subclass_relations = draft.get("subclass_relations", []) or []
        class_mappings = draft.get("class_mappings", []) or []
        data_property_mappings = draft.get("data_property_mappings", []) or []
        object_property_mappings = draft.get("object_property_mappings", []) or []

        class_idx = self._index_by_id(classes)
        dp_idx = self._index_by_id(data_properties)
        op_idx = self._index_by_id(object_properties)

        cm_idx = self._index_by_key(class_mappings, "class_id")
        dpm_idx = self._index_by_key(data_property_mappings, "property_id")
        opm_idx = self._index_by_key(object_property_mappings, "property_id")

        # ----------------------------------------------------
        # Duplicates
        # ----------------------------------------------------
        if len(class_idx) != len(classes):
            issues.append(self._issue("error", "DUPLICATE_CLASS_ID", "Duplicate class ids detected."))
        if len(dp_idx) != len(data_properties):
            issues.append(self._issue("error", "DUPLICATE_DATA_PROPERTY_ID", "Duplicate data property ids detected."))
        if len(op_idx) != len(object_properties):
            issues.append(self._issue("error", "DUPLICATE_OBJECT_PROPERTY_ID", "Duplicate object property ids detected."))

        # ----------------------------------------------------
        # Classes
        # ----------------------------------------------------
        for c in classes:
            cid = str(c.get("id") or "").strip()
            if not cid:
                issues.append(self._issue("error", "CLASS_MISSING_ID", "Class missing id.", item=c))
                continue

            exportable = self._status_is_exportable(c.get("status"))
            cm = cm_idx.get(cid)

            if exportable and cm is None:
                issues.append(
                    self._issue(
                        "error",
                        "CLASS_MISSING_MAPPING",
                        "Exportable class has no class_mapping.",
                        class_id=cid,
                    )
                )
                continue

            effective_tables = self._effective_class_tables(c, cm)
            effective_identifier_columns = self._effective_identifier_columns(c, cm)
            effective_instance_template = self._effective_instance_template(c, cm)

            if exportable and not effective_tables:
                issues.append(
                    self._issue(
                        "error",
                        "CLASS_NO_SOURCE_TABLES",
                        "Class has neither source_tables nor class_mapping.from_tables.",
                        class_id=cid,
                    )
                )

            if exportable and not effective_instance_template:
                issues.append(
                    self._issue(
                        "error",
                        "CLASS_MAPPING_NO_INSTANCE_TEMPLATE",
                        "Class has no effective instance_id_template.",
                        class_id=cid,
                    )
                )

            if exportable and not effective_identifier_columns:
                issues.append(
                    self._issue(
                        "warning",
                        "CLASS_NO_IDENTIFIER_COLUMNS",
                        "Class has no effective identifier_columns.",
                        class_id=cid,
                    )
                )

        # ----------------------------------------------------
        # Data properties
        # ----------------------------------------------------
        for p in data_properties:
            pid = str(p.get("id") or "").strip()
            if not pid:
                issues.append(self._issue("error", "DATA_PROPERTY_MISSING_ID", "Data property missing id.", item=p))
                continue

            exportable = self._status_is_exportable(p.get("status"))
            domain_class = str(p.get("domain_class") or "").strip()
            if domain_class and domain_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "DATA_PROPERTY_UNKNOWN_DOMAIN",
                        "Data property references unknown domain class.",
                        property_id=pid,
                        domain_class=domain_class,
                    )
                )

            dm = dpm_idx.get(pid)
            if exportable and dm is None:
                issues.append(
                    self._issue(
                        "error",
                        "DATA_PROPERTY_MISSING_MAPPING",
                        "Exportable data property has no data_property_mapping.",
                        property_id=pid,
                    )
                )
                continue

            effective_cols = self._effective_data_property_columns(p, dm)
            if exportable and not effective_cols:
                issues.append(
                    self._issue(
                        "error",
                        "DATA_PROPERTY_NO_EFFECTIVE_SOURCE_COLUMNS",
                        "Data property has neither source_columns nor usable data_property_mapping columns.",
                        property_id=pid,
                    )
                )

            if dm is not None:
                from_class = str(dm.get("from_class") or "").strip()
                if from_class and domain_class and from_class != domain_class:
                    issues.append(
                        self._issue(
                            "warning",
                            "DATA_PROPERTY_DOMAIN_MISMATCH",
                            "domain_class and data_property_mapping.from_class disagree.",
                            property_id=pid,
                            domain_class=domain_class,
                            from_class=from_class,
                        )
                    )

                source_table = str(dm.get("source_table") or "").strip()
                if exportable and not source_table and not effective_cols:
                    issues.append(
                        self._issue(
                            "warning",
                            "DATA_PROPERTY_MAPPING_WEAK_GROUNDING",
                            "Data property mapping has weak grounding: no source_table and no effective source columns.",
                            property_id=pid,
                        )
                    )

                if exportable and effective_cols and not source_table:
                    issues.append(
                        self._issue(
                            "info",
                            "DATA_PROPERTY_MAPPING_SOURCE_TABLE_MISSING",
                            "Data property has effective columns but source_table is empty.",
                            property_id=pid,
                            effective_columns=effective_cols,
                        )
                    )

        # ----------------------------------------------------
        # Object properties
        # ----------------------------------------------------
        for p in object_properties:
            pid = str(p.get("id") or "").strip()
            if not pid:
                issues.append(self._issue("error", "OBJECT_PROPERTY_MISSING_ID", "Object property missing id.", item=p))
                continue

            exportable = self._status_is_exportable(p.get("status"))
            domain_class = str(p.get("domain_class") or "").strip()
            range_class = str(p.get("range_class") or "").strip()

            if domain_class and domain_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_UNKNOWN_DOMAIN",
                        "Object property references unknown domain class.",
                        property_id=pid,
                        domain_class=domain_class,
                    )
                )
            if range_class and range_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_UNKNOWN_RANGE",
                        "Object property references unknown range class.",
                        property_id=pid,
                        range_class=range_class,
                    )
                )

            om = opm_idx.get(pid)
            if exportable and om is None:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_MISSING_MAPPING",
                        "Exportable object property has no object_property_mapping.",
                        property_id=pid,
                    )
                )
                continue

            effective_joins = self._effective_object_property_joins(p, om)
            if exportable and not effective_joins:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_NO_EFFECTIVE_JOINS",
                        "Object property has neither join_paths nor object_property_mapping.joins.",
                        property_id=pid,
                    )
                )

            if om is not None:
                from_class = str(om.get("from_class") or "").strip()
                to_class = str(om.get("to_class") or "").strip()

                if from_class and domain_class and from_class != domain_class:
                    issues.append(
                        self._issue(
                            "warning",
                            "OBJECT_PROPERTY_DOMAIN_MISMATCH",
                            "domain_class and object_property_mapping.from_class disagree.",
                            property_id=pid,
                            domain_class=domain_class,
                            from_class=from_class,
                        )
                    )

                if to_class and range_class and to_class != range_class:
                    issues.append(
                        self._issue(
                            "warning",
                            "OBJECT_PROPERTY_RANGE_MISMATCH",
                            "range_class and object_property_mapping.to_class disagree.",
                            property_id=pid,
                            range_class=range_class,
                            to_class=to_class,
                        )
                    )

                if exportable and effective_joins and (not from_class or not to_class):
                    issues.append(
                        self._issue(
                            "warning",
                            "OBJECT_PROPERTY_MAPPING_CLASS_ENDPOINTS_WEAK",
                            "Object property has joins but object_property_mapping lacks from_class or to_class.",
                            property_id=pid,
                            from_class=from_class,
                            to_class=to_class,
                        )
                    )

        # ----------------------------------------------------
        # Subclass relations
        # ----------------------------------------------------
        for rel in subclass_relations:
            rid = str(rel.get("id") or "").strip()
            child = str(rel.get("child_class") or "").strip()
            parent = str(rel.get("parent_class") or "").strip()

            if not rid:
                issues.append(
                    self._issue(
                        "warning",
                        "SUBCLASS_RELATION_MISSING_ID",
                        "Subclass relation missing id.",
                        relation=rel,
                    )
                )
            if not child:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_RELATION_MISSING_CHILD",
                        "Subclass relation missing child_class.",
                        relation_id=rid,
                        relation=rel,
                    )
                )
            elif child not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_UNKNOWN_CHILD",
                        "Subclass relation references unknown child class.",
                        relation_id=rid,
                        child_class=child,
                    )
                )

            if not parent:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_RELATION_MISSING_PARENT",
                        "Subclass relation missing parent_class.",
                        relation_id=rid,
                        relation=rel,
                    )
                )
            elif parent not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_UNKNOWN_PARENT",
                        "Subclass relation references unknown parent class.",
                        relation_id=rid,
                        parent_class=parent,
                    )
                )

        # ----------------------------------------------------
        # Cross checks: mappings that point nowhere
        # ----------------------------------------------------
        for class_id in cm_idx:
            if class_id not in class_idx:
                issues.append(
                    self._issue(
                        "warning",
                        "ORPHAN_CLASS_MAPPING",
                        "class_mapping points to missing class.",
                        class_id=class_id,
                    )
                )

        for property_id in dpm_idx:
            if property_id not in dp_idx:
                issues.append(
                    self._issue(
                        "warning",
                        "ORPHAN_DATA_PROPERTY_MAPPING",
                        "data_property_mapping points to missing data property.",
                        property_id=property_id,
                    )
                )

        for property_id in opm_idx:
            if property_id not in op_idx:
                issues.append(
                    self._issue(
                        "warning",
                        "ORPHAN_OBJECT_PROPERTY_MAPPING",
                        "object_property_mapping points to missing object property.",
                        property_id=property_id,
                    )
                )

        errors = [x for x in issues if x["level"] == "error"]
        warnings = [x for x in issues if x["level"] == "warning"]
        infos = [x for x in issues if x["level"] == "info"]

        return {
            "ok": len(errors) == 0,
            "num_errors": len(errors),
            "num_warnings": len(warnings),
            "num_infos": len(infos),
            "issues": issues,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
        }