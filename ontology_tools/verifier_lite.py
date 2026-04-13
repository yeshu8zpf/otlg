from __future__ import annotations

from typing import Any, Dict, List


class MappingVerifierLite:
    """
    Lightweight verifier operating on canonical draft dicts
    produced by OntologyDraft.to_dict().

    Goal:
    - stay cheap / dependency-light
    - align with current OntologyDraft schema
    - return structured diagnostics for later feedback loops
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
            if isinstance(x, dict) and x.get("id"):
                out[x["id"]] = x
        return out

    def verify_class_mapping(self, class_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        class_id = class_mapping.get("class_id")
        if not class_id:
            issues.append(self._issue("error", "CLASS_MAPPING_MISSING_CLASS_ID", "class_mapping missing class_id"))

        if not class_mapping.get("instance_id_template"):
            issues.append(
                self._issue(
                    "error",
                    "CLASS_MAPPING_MISSING_INSTANCE_ID_TEMPLATE",
                    "class_mapping missing instance_id_template",
                    class_id=class_id,
                )
            )

        if not class_mapping.get("from_tables"):
            issues.append(
                self._issue(
                    "error",
                    "CLASS_MAPPING_MISSING_FROM_TABLES",
                    "class_mapping missing from_tables",
                    class_id=class_id,
                )
            )

        if not class_mapping.get("identifier_columns"):
            issues.append(
                self._issue(
                    "error",
                    "CLASS_MAPPING_MISSING_IDENTIFIER_COLUMNS",
                    "class_mapping missing identifier_columns",
                    class_id=class_id,
                )
            )

        return issues

    def verify_data_property_mapping(self, m: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        property_id = m.get("property_id")
        if not property_id:
            issues.append(
                self._issue("error", "DATA_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "data_property_mapping missing property_id")
            )

        if not m.get("from_class"):
            issues.append(
                self._issue(
                    "error",
                    "DATA_PROPERTY_MAPPING_MISSING_FROM_CLASS",
                    "data_property_mapping missing from_class",
                    property_id=property_id,
                )
            )

        if not m.get("column"):
            issues.append(
                self._issue(
                    "error",
                    "DATA_PROPERTY_MAPPING_MISSING_COLUMN",
                    "data_property_mapping missing column",
                    property_id=property_id,
                )
            )

        return issues

    def verify_object_property_mapping(self, m: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        property_id = m.get("property_id")
        if not property_id:
            issues.append(
                self._issue("error", "OBJECT_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "object_property_mapping missing property_id")
            )

        if not m.get("from_class"):
            issues.append(
                self._issue(
                    "error",
                    "OBJECT_PROPERTY_MAPPING_MISSING_FROM_CLASS",
                    "object_property_mapping missing from_class",
                    property_id=property_id,
                )
            )

        if not m.get("to_class"):
            issues.append(
                self._issue(
                    "error",
                    "OBJECT_PROPERTY_MAPPING_MISSING_TO_CLASS",
                    "object_property_mapping missing to_class",
                    property_id=property_id,
                )
            )

        if not m.get("joins"):
            issues.append(
                self._issue(
                    "error",
                    "OBJECT_PROPERTY_MAPPING_MISSING_JOINS",
                    "object_property_mapping missing joins",
                    property_id=property_id,
                )
            )

        return issues

    def verify_draft_dict(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        classes = draft.get("classes", []) or []
        data_properties = draft.get("data_properties", []) or []
        object_properties = draft.get("object_properties", []) or []

        class_mappings = draft.get("class_mappings", []) or []
        data_property_mappings = draft.get("data_property_mappings", []) or []
        object_property_mappings = draft.get("object_property_mappings", []) or []

        class_idx = self._index_by_id(classes)
        data_prop_idx = self._index_by_id(data_properties)
        object_prop_idx = self._index_by_id(object_properties)

        class_mapping_idx = {
            m["class_id"]: m for m in class_mappings
            if isinstance(m, dict) and m.get("class_id")
        }
        data_property_mapping_idx = {
            m["property_id"]: m for m in data_property_mappings
            if isinstance(m, dict) and m.get("property_id")
        }
        object_property_mapping_idx = {
            m["property_id"]: m for m in object_property_mappings
            if isinstance(m, dict) and m.get("property_id")
        }

        # 1) Class mappings
        for cm in class_mappings:
            if not isinstance(cm, dict):
                issues.append(self._issue("error", "CLASS_MAPPING_NOT_DICT", "class_mapping item is not a dict"))
                continue

            issues.extend(self.verify_class_mapping(cm))

            class_id = cm.get("class_id")
            if class_id and class_id not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "CLASS_MAPPING_UNKNOWN_CLASS",
                        f"class_mapping references unknown class {class_id}",
                        class_id=class_id,
                    )
                )

        # 2) Data property mappings
        for dm in data_property_mappings:
            if not isinstance(dm, dict):
                issues.append(self._issue("error", "DATA_PROPERTY_MAPPING_NOT_DICT", "data_property_mapping item is not a dict"))
                continue

            issues.extend(self.verify_data_property_mapping(dm))

            property_id = dm.get("property_id")
            from_class = dm.get("from_class")

            if property_id and property_id not in data_prop_idx:
                issues.append(
                    self._issue(
                        "error",
                        "DATA_PROPERTY_MAPPING_UNKNOWN_PROPERTY",
                        f"data_property_mapping references unknown property {property_id}",
                        property_id=property_id,
                    )
                )
                continue

            if from_class and from_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "DATA_PROPERTY_MAPPING_UNKNOWN_CLASS",
                        f"data_property_mapping references unknown class {from_class}",
                        property_id=property_id,
                        from_class=from_class,
                    )
                )

            prop = data_prop_idx.get(property_id)
            if prop is not None:
                domain_class = prop.get("domain_class")
                if domain_class and from_class and domain_class != from_class:
                    issues.append(
                        self._issue(
                            "error",
                            "DATA_PROPERTY_DOMAIN_MISMATCH",
                            f"data_property_mapping {property_id} uses from_class={from_class}, but property domain is {domain_class}",
                            property_id=property_id,
                            mapping_from_class=from_class,
                            property_domain=domain_class,
                        )
                    )

        # 3) Object property mappings
        for om in object_property_mappings:
            if not isinstance(om, dict):
                issues.append(self._issue("error", "OBJECT_PROPERTY_MAPPING_NOT_DICT", "object_property_mapping item is not a dict"))
                continue

            issues.extend(self.verify_object_property_mapping(om))

            property_id = om.get("property_id")
            from_class = om.get("from_class")
            to_class = om.get("to_class")

            if property_id and property_id not in object_prop_idx:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_MAPPING_UNKNOWN_PROPERTY",
                        f"object_property_mapping references unknown property {property_id}",
                        property_id=property_id,
                    )
                )
                continue

            if from_class and from_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_MAPPING_UNKNOWN_FROM_CLASS",
                        f"object_property_mapping references unknown from_class {from_class}",
                        property_id=property_id,
                        from_class=from_class,
                    )
                )

            if to_class and to_class not in class_idx:
                issues.append(
                    self._issue(
                        "error",
                        "OBJECT_PROPERTY_MAPPING_UNKNOWN_TO_CLASS",
                        f"object_property_mapping references unknown to_class {to_class}",
                        property_id=property_id,
                        to_class=to_class,
                    )
                )

            prop = object_prop_idx.get(property_id)
            if prop is not None:
                domain_class = prop.get("domain_class")
                range_class = prop.get("range_class")

                if domain_class and from_class and domain_class != from_class:
                    issues.append(
                        self._issue(
                            "error",
                            "OBJECT_PROPERTY_DOMAIN_MISMATCH",
                            f"object_property_mapping {property_id} uses from_class={from_class}, but property domain is {domain_class}",
                            property_id=property_id,
                            mapping_from_class=from_class,
                            property_domain=domain_class,
                        )
                    )

                if range_class and to_class and range_class != to_class:
                    issues.append(
                        self._issue(
                            "error",
                            "OBJECT_PROPERTY_RANGE_MISMATCH",
                            f"object_property_mapping {property_id} uses to_class={to_class}, but property range is {range_class}",
                            property_id=property_id,
                            mapping_to_class=to_class,
                            property_range=range_class,
                        )
                    )

                declared_join_paths = prop.get("join_paths") or []
                mapped_joins = om.get("joins") or []
                if declared_join_paths and mapped_joins and declared_join_paths != mapped_joins:
                    issues.append(
                        self._issue(
                            "warning",
                            "OBJECT_PROPERTY_JOIN_PATH_MISMATCH",
                            f"object_property_mapping {property_id} joins differ from object_property.join_paths",
                            property_id=property_id,
                        )
                    )

        # 4) Accepted ontology elements should be mapped
        for c in classes:
            if not isinstance(c, dict):
                continue
            if c.get("status", "accepted") == "accepted" and c.get("id") not in class_mapping_idx:
                issues.append(
                    self._issue(
                        "error",
                        "MISSING_CLASS_MAPPING",
                        f"accepted class {c.get('id')} has no class mapping",
                        class_id=c.get("id"),
                    )
                )

        for p in data_properties:
            if not isinstance(p, dict):
                continue
            if p.get("status", "accepted") == "accepted" and p.get("id") not in data_property_mapping_idx:
                issues.append(
                    self._issue(
                        "error",
                        "MISSING_DATA_PROPERTY_MAPPING",
                        f"accepted data property {p.get('id')} has no data property mapping",
                        property_id=p.get("id"),
                    )
                )

        for p in object_properties:
            if not isinstance(p, dict):
                continue
            if p.get("status", "accepted") == "accepted" and p.get("id") not in object_property_mapping_idx:
                issues.append(
                    self._issue(
                        "error",
                        "MISSING_OBJECT_PROPERTY_MAPPING",
                        f"accepted object property {p.get('id')} has no object property mapping",
                        property_id=p.get("id"),
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
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
        }