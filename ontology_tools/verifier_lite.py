from __future__ import annotations

from typing import Any, Dict, List, Optional


class MappingVerifierLite:
    """
    Lightweight verifier operating on canonical draft dicts
    produced by OntologyDraft.to_dict().

    Design goals:
    - cheap / dependency-light
    - aligned with current OntologyDraft schema
    - verify effective consistency, not only local field presence
    - produce structured diagnostics for later feedback loops
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

    def _index_by_key(
        self,
        items: List[Dict[str, Any]],
        key: str,
    ) -> Dict[str, Dict[str, Any]]:
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
        return list(dict.fromkeys(out))

    def _status_is_exportable(self, status: Optional[str]) -> bool:
        s = str(status or "").strip().lower()
        if not s:
            return True
        return s not in {"rejected", "invalid", "discarded", "dropped"}

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
        # Duplicate IDs
        # ----------------------------------------------------
        if len(class_idx) != len(classes):
            issues.append(self._issue("error", "DUPLICATE_CLASS_ID", "Duplicate class ids detected."))
        if len(dp_idx) != len(data_properties):
            issues.append(self._issue("error", "DUPLICATE_DATA_PROPERTY_ID", "Duplicate data property ids detected."))
        if len(op_idx) != len(object_properties):
            issues.append(self._issue("error", "DUPLICATE_OBJECT_PROPERTY_ID", "Duplicate object property ids detected."))

        # ----------------------------------------------------
        # Classes and class mappings
        # ----------------------------------------------------
        for c in classes:
            cid = str(c.get("id") or "").strip()
            if not cid:
                issues.append(self._issue("error", "CLASS_MISSING_ID", "Class missing id.", item=c))
                continue

            cm = cm_idx.get(cid)
            source_tables = self._non_empty_strings(c.get("source_tables"))
            exportable = self._status_is_exportable(c.get("status"))

            if exportable and cm is None:
                issues.append(
                    self._issue(
                        "error",
                        "CLASS_MISSING_MAPPING",
                        "Exportable class has no class_mapping.",
                        class_id=cid,
                    )
                )

            if cm is not None:
                mapped_tables = self._non_empty_strings(cm.get("from_tables"))
                if not source_tables and not mapped_tables:
                    issues.append(
                        self._issue(
                            "error",
                            "CLASS_NO_SOURCE_TABLES",
                            "Class has neither source_tables nor class_mapping.from_tables.",
                            class_id=cid,
                        )
                    )
                if not str(cm.get("instance_id_template") or "").strip():
                    issues.append(
                        self._issue(
                            "error",
                            "CLASS_MAPPING_NO_INSTANCE_TEMPLATE",
                            "class_mapping missing instance_id_template.",
                            class_id=cid,
                        )
                    )

        # ----------------------------------------------------
        # Data properties and mappings
        # ----------------------------------------------------
        for p in data_properties:
            pid = str(p.get("id") or "").strip()
            if not pid:
                issues.append(self._issue("error", "DATA_PROPERTY_MISSING_ID", "Data property missing id.", item=p))
                continue

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
            exportable = self._status_is_exportable(p.get("status"))

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

            property_cols = self._non_empty_strings(p.get("source_columns"))
            mapping_cols = []
            if dm is not None:
                mapping_cols.extend(self._non_empty_strings(dm.get("source_columns")))
                if str(dm.get("column") or "").strip():
                    mapping_cols.append(str(dm["column"]).strip())

            effective_cols = list(dict.fromkeys(property_cols + mapping_cols))
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
                if not source_table and not effective_cols:
                    issues.append(
                        self._issue(
                            "warning",
                            "DATA_PROPERTY_MAPPING_WEAK_GROUNDING",
                            "Data property mapping has weak grounding: no source_table and no effective source columns.",
                            property_id=pid,
                        )
                    )

        # ----------------------------------------------------
        # Object properties and mappings
        # ----------------------------------------------------
        for p in object_properties:
            pid = str(p.get("id") or "").strip()
            if not pid:
                issues.append(self._issue("error", "OBJECT_PROPERTY_MISSING_ID", "Object property missing id.", item=p))
                continue

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
            exportable = self._status_is_exportable(p.get("status"))

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

            property_joins = self._norm_list(p.get("join_paths"))
            mapping_joins = self._norm_list(om.get("joins") if om is not None else [])
            effective_joins = property_joins or mapping_joins

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

                if domain_class and from_class and domain_class != from_class:
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
                if range_class and to_class and range_class != to_class:
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

        # ----------------------------------------------------
        # Subclass relations
        # ----------------------------------------------------
        for rel in subclass_relations:
            child = str(rel.get("child_class") or "").strip()
            parent = str(rel.get("parent_class") or "").strip()
            if child and child not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_UNKNOWN_CHILD",
                        "Subclass relation references unknown child class.",
                        child_class=child,
                    )
                )
            if parent and parent not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "SUBCLASS_UNKNOWN_PARENT",
                        "Subclass relation references unknown parent class.",
                        parent_class=parent,
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