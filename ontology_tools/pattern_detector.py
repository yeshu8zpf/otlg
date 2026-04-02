from __future__ import annotations

from typing import Any, Dict, List

from .common import normalize_name
from .hypotheses import Hypothesis


class PatternDetector:
    def _column_map(self, table_profile: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {c["name"]: c for c in table_profile.get("columns", [])}

    def _detect_entity_tables(self, schema_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for t in schema_profile.get("tables", []):
            name = t["name"]
            pk = t.get("primary_key", [])
            fks = t.get("foreign_keys", [])
            confidence = 0.6
            evidence = []

            if pk:
                confidence += 0.1
                evidence.append({"type": "primary_key", "value": pk})
            if len(fks) <= 1:
                confidence += 0.1

            out.append(
                Hypothesis(
                    kind="ClassHypothesis",
                    statement=f"Table {name} likely maps to ontology class {name.title()}",
                    confidence=min(confidence, 0.95),
                    evidence=evidence,
                    source_tools=["SchemaProfiler", "PatternDetector"],
                    canonical_key=f"class:{normalize_name(name)}",
                    payload={"table": name, "suggested_label": name.title()},
                )
            )
        return out

    def _detect_connector_tables(self, schema_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for t in schema_profile.get("tables", []):
            name = t["name"]
            cols = self._column_map(t)
            pk = set(t.get("primary_key", []))
            fks = t.get("foreign_keys", [])
            fk_cols = [c for fk in fks for c in fk["columns"]]
            non_fk_non_pk = [c for c in cols.keys() if c not in pk and c not in fk_cols]

            if len(fks) == 2 and len(pk) >= 2:
                conf = 0.78
                evidence = [
                    {"type": "num_foreign_keys", "value": len(fks)},
                    {"type": "composite_primary_key", "value": sorted(pk)},
                ]
                payload = {
                    "table": name,
                    "foreign_keys": fks,
                    "non_fk_non_pk_columns": non_fk_non_pk,
                    "reification_candidate": len(non_fk_non_pk) > 0,
                }

                if non_fk_non_pk:
                    conf += 0.07
                    evidence.append({"type": "extra_attributes", "value": non_fk_non_pk})

                out.append(
                    Hypothesis(
                        kind="RelationshipHypothesis",
                        statement=f"Table {name} likely represents an association / N-M relation",
                        confidence=min(conf, 0.95),
                        evidence=evidence,
                        source_tools=["SchemaProfiler", "PatternDetector"],
                        canonical_key=f"assoc:{normalize_name(name)}",
                        payload=payload,
                    )
                )

                if non_fk_non_pk:
                    out.append(
                        Hypothesis(
                            kind="ReificationHypothesis",
                            statement=f"Table {name} may need reification because it has association attributes {non_fk_non_pk}",
                            confidence=0.83,
                            evidence=[
                                {"type": "association_table", "value": name},
                                {"type": "extra_attributes", "value": non_fk_non_pk},
                            ],
                            source_tools=["SchemaProfiler", "PatternDetector"],
                            canonical_key=f"reify:{normalize_name(name)}",
                            payload=payload,
                        )
                    )
        return out

    def _detect_weak_entities(self, schema_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for t in schema_profile.get("tables", []):
            name = t["name"]
            pk = set(t.get("primary_key", []))
            fks = t.get("foreign_keys", [])
            fk_cols = {c for fk in fks for c in fk["columns"]}

            if len(pk) >= 2 and fk_cols.intersection(pk):
                matched_fks = [fk for fk in fks if set(fk["columns"]).intersection(pk)]
                if matched_fks:
                    out.append(
                        Hypothesis(
                            kind="IdentifierHypothesis",
                            statement=f"Table {name} looks like a weak/dependent entity with identifying foreign key(s)",
                            confidence=0.86,
                            evidence=[
                                {"type": "composite_primary_key", "value": sorted(pk)},
                                {"type": "fk_in_pk", "value": [fk['columns'] for fk in matched_fks]},
                            ],
                            source_tools=["SchemaProfiler", "PatternDetector"],
                            canonical_key=f"weak:{normalize_name(name)}",
                            payload={
                                "table": name,
                                "primary_key": sorted(pk),
                                "identifying_foreign_keys": matched_fks,
                            },
                        )
                    )
        return out

    def _detect_boolean_hidden_relations(self, schema_profile: Dict[str, Any], instance_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for t in schema_profile.get("tables", []):
            tname = t["name"]
            cols = instance_profile.get("tables", {}).get(tname, {}).get("columns", {})
            for cname, cprof in cols.items():
                if cprof.get("is_boolean_like"):
                    out.append(
                        Hypothesis(
                            kind="AttributeOwnershipHypothesis",
                            statement=f"Column {tname}.{cname} may encode a boolean attribute or hidden relation",
                            confidence=0.68,
                            evidence=[
                                {"type": "boolean_like_values", "value": cprof.get("sample_values", [])},
                                {"type": "column", "value": f"{tname}.{cname}"},
                            ],
                            missing_evidence=["semantic_interpretation"],
                            source_tools=["InstanceProfiler", "PatternDetector"],
                            canonical_key=f"bool:{normalize_name(tname)}.{normalize_name(cname)}",
                            payload={"table": tname, "column": cname},
                        )
                    )
        return out

    def _detect_hierarchy_hints(self, schema_profile: Dict[str, Any], instance_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for t in schema_profile.get("tables", []):
            tname = t["name"]
            cols = instance_profile.get("tables", {}).get(tname, {}).get("columns", {})
            for cname, cprof in cols.items():
                if normalize_name(cname) in {"type", "kind", "category", "role"}:
                    if 0 < cprof.get("distinct_ratio", 0.0) < 0.5:
                        out.append(
                            Hypothesis(
                                kind="HierarchyHypothesis",
                                statement=f"Column {tname}.{cname} may indicate a class hierarchy or subclass partition",
                                confidence=0.71,
                                evidence=[
                                    {"type": "discriminator_column", "value": f"{tname}.{cname}"},
                                    {"type": "sample_values", "value": cprof.get("sample_values", [])},
                                ],
                                missing_evidence=["subclass_mapping_condition"],
                                source_tools=["InstanceProfiler", "PatternDetector"],
                                canonical_key=f"hier:{normalize_name(tname)}.{normalize_name(cname)}",
                                payload={"table": tname, "column": cname},
                            )
                        )
        return out

    def _detect_missing_fk_candidates(self, schema_profile: Dict[str, Any], instance_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        overlaps = instance_profile.get("cross_table_value_overlap", [])
        known_pairs = {
            (t["name"], edge["to_table"])
            for t in schema_profile.get("tables", [])
            for edge in schema_profile.get("join_graph", {}).get(t["name"], [])
        }

        for ov in overlaps:
            left_table = ov["left"].split(".", 1)[0]
            right_table = ov["right"].split(".", 1)[0]
            if (left_table, right_table) in known_pairs or (right_table, left_table) in known_pairs:
                continue

            out.append(
                Hypothesis(
                    kind="RelationshipHypothesis",
                    statement=f"Columns {ov['left']} and {ov['right']} may imply an unstated foreign-key-like relation",
                    confidence=0.63,
                    evidence=[{"type": "value_overlap", "value": ov}],
                    missing_evidence=["schema_level_constraint"],
                    source_tools=["InstanceProfiler", "PatternDetector"],
                    canonical_key=f"softfk:{normalize_name(ov['left'])}:{normalize_name(ov['right'])}",
                    payload=ov,
                )
            )
        return out

    def detect(self, schema_profile: Dict[str, Any], instance_profile: Dict[str, Any]) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        out.extend(self._detect_entity_tables(schema_profile))
        out.extend(self._detect_connector_tables(schema_profile))
        out.extend(self._detect_weak_entities(schema_profile))
        out.extend(self._detect_boolean_hidden_relations(schema_profile, instance_profile))
        out.extend(self._detect_hierarchy_hints(schema_profile, instance_profile))
        out.extend(self._detect_missing_fk_candidates(schema_profile, instance_profile))
        return out
