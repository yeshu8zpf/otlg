from __future__ import annotations

from dataclasses import dataclass, field, asdict, fields
from typing import Any, Dict, List, Optional, Tuple, Iterable
import copy
import json
import re

from normalize import normalize_model_output_robust


# ============================================================
# Regex / low-level helpers
# ============================================================

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")



def _to_burr_safe_property_name(label: str) -> str:
    s = str(label or "").strip()
    if not s:
        return "UNKNOWN"
    # spaces -> underscore
    s = re.sub(r"\s+", "_", s)
    # remove characters unsafe for Burr/D2RQ local names
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    # collapse repeated underscores
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "UNKNOWN"


def parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    s = (s or "").strip()
    m = QUALIFIED_COL_RE.match(s)
    if not m:
        return None
    return m.group(1), m.group(2)


def _field_names(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def _safe_dict(x: Any) -> Dict[str, Any]:
    return dict(x) if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _as_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x)


def _dedup_keep_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in items:
        key = json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (dict, list)) else repr(x)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def _split_kwargs(cls, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    allowed = _field_names(cls)
    known = {k: v for k, v in data.items() if k in allowed and k != "extras"}
    extra = {k: v for k, v in data.items() if k not in allowed}
    return known, extra


def _build_dataclass(cls, data: Dict[str, Any]):
    known, extra = _split_kwargs(cls, data)
    try:
        obj = cls(**known)
    except TypeError as e:
        payload = {
            "target_class": cls.__name__,
            "known": known,
            "all_data": data,
            "missing_or_bad_fields_hint": str(e),
        }
        raise TypeError(
            f"Failed to build {cls.__name__}: {json.dumps(payload, ensure_ascii=False, default=str)}"
        ) from e

    existing_extras = _safe_dict(data.get("extras"))
    if hasattr(obj, "extras"):
        obj.extras = {**existing_extras, **extra}
    return obj


# ============================================================
# ID / template helpers
# ============================================================

def _normalize_class_id(label: str) -> str:
    label = _as_str(label).strip()
    if not label:
        return "Class:UNKNOWN"
    if label.startswith("Class:"):
        return label
    return f"Class:{label}"


def _normalize_data_property_id(domain_class: str, label: str) -> str:
    domain_label = _normalize_class_id(domain_class).replace("Class:", "")
    label = _as_str(label).strip() or "UNKNOWN"
    if label.startswith("DataProperty:"):
        return label
    return f"DataProperty:{domain_label}.{label}"


def _normalize_object_property_id(domain_class: str, label: str) -> str:
    domain_label = _normalize_class_id(domain_class).replace("Class:", "")
    label = _as_str(label).strip() or "UNKNOWN"
    if label.startswith("ObjectProperty:"):
        return label
    return f"ObjectProperty:{domain_label}.{label}"


def _extract_identifier_columns(template: str) -> List[str]:
    template = _as_str(template)
    cols: List[str] = []

    # Burr style: @@table.column@@
    start = 0
    while True:
        i = template.find("@@", start)
        if i == -1:
            break
        j = template.find("@@", i + 2)
        if j == -1:
            break
        cols.append(template[i + 2:j].strip())
        start = j + 2

    # Python style: {table.column}
    cols.extend(
        re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}", template)
    )

    return _dedup_keep_order([c for c in cols if c])


def _infer_tables_from_template(template: str) -> List[str]:
    cols = _extract_identifier_columns(template)
    tables: List[str] = []
    for c in cols:
        parsed = parse_qualified_column(c)
        if parsed:
            t, _ = parsed
            if t not in tables:
                tables.append(t)

    if not tables:
        guess = _as_str(template).split("/", 1)[0].strip()
        if guess and IDENT_RE.match(guess):
            tables.append(guess)

    return tables


def _normalize_join(join_value: Any) -> List[str]:
    """
    Normalize a join condition into token form:
      ["table1.col1", "=", "table2.col2"]

    Tolerates:
      - already-tokenized list
      - single string like 'a.id = b.a_id'
    """
    if isinstance(join_value, list):
        tokens = [str(x).strip() for x in join_value if str(x).strip()]
        return tokens

    if isinstance(join_value, str):
        text = join_value.strip()
        if not text:
            return []

        m = re.match(r"^\s*(\S+)\s*(=|!=|<>|>=|<=|>|<)\s*(\S+)\s*$", text)
        if m:
            return [m.group(1), m.group(2), m.group(3)]

        tokens = text.split()
        return [t for t in tokens if t]

    return [str(join_value)]


def _join_to_burr_string(join_tokens: List[str]) -> str:
    return " ".join([str(x) for x in join_tokens if str(x).strip()])


def _label_from_class_id(class_id: str) -> str:
    cid = _normalize_class_id(class_id)
    return cid.replace("Class:", "")


# ============================================================
# Normalization report helper
# ============================================================

@dataclass
class NormalizationMessage:
    level: str
    code: str
    message: str
    path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizationReport:
    ok: bool = True
    messages: List[NormalizationMessage] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        out = {"ok": self.ok, "num_messages": len(self.messages)}
        by_level: Dict[str, int] = {}
        by_code: Dict[str, int] = {}
        for m in self.messages:
            by_level[m.level] = by_level.get(m.level, 0) + 1
            by_code[m.code] = by_code.get(m.code, 0) + 1
        out["by_level"] = by_level
        out["by_code"] = by_code
        out["stats"] = self.stats
        return out


def get_normalization_report(obj: Dict[str, Any]) -> NormalizationReport:
    """
    Read normalization report from normalize_model_output_robust(obj).
    """
    normalized = normalize_model_output_robust(obj)
    report_obj = _safe_dict(_safe_dict(normalized.get("extras")).get("normalization_report"))

    report = NormalizationReport(ok=bool(report_obj.get("ok", True)))
    report.stats = _safe_dict(report_obj.get("stats"))
    for msg in _as_list(report_obj.get("messages")):
        msg = _safe_dict(msg)
        report.messages.append(
            NormalizationMessage(
                level=str(msg.get("level", "info")),
                code=str(msg.get("code", "UNKNOWN")),
                message=str(msg.get("message", "")),
                path=msg.get("path"),
                payload=_safe_dict(msg.get("payload")),
            )
        )
    return report


# ============================================================
# Core ontology structures
# ============================================================

@dataclass
class ClassDef:
    id: str
    label: str
    description: Optional[str] = None
    source_tables: List[str] = field(default_factory=list)
    status: str = "accepted"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyDef:
    id: str
    label: str
    domain_class: str
    range_type: str = "string"
    source_columns: List[str] = field(default_factory=list)
    status: str = "accepted"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectPropertyDef:
    id: str
    label: str
    domain_class: str
    range_class: str
    join_paths: List[List[str]] = field(default_factory=list)
    reified: bool = False
    status: str = "accepted"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubclassRelation:
    id: str
    child_class: str
    parent_class: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    status: str = "accepted"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Mapping layer
# ============================================================

@dataclass
class ClassMapping:
    class_id: str
    instance_id_template: str
    from_tables: List[str] = field(default_factory=list)
    where: List[str] = field(default_factory=list)
    joins: List[List[str]] = field(default_factory=list)
    identifier_columns: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyMapping:
    property_id: str
    from_class: str
    column: str
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectPropertyMapping:
    property_id: str
    from_class: str
    to_class: str
    joins: List[List[str]] = field(default_factory=list)
    where: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Higher-level diagnostics
# ============================================================

@dataclass
class Hypothesis:
    id: str
    kind: str
    statement: str
    confidence: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    missing_evidence: List[str] = field(default_factory=list)
    source_tools: List[str] = field(default_factory=list)
    status: str = "open"
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conflict:
    id: str
    left: str
    right: str
    reason: str
    severity: str = "medium"
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolTrace:
    tool_name: str
    input_summary: Dict[str, Any] = field(default_factory=dict)
    output_summary: Dict[str, Any] = field(default_factory=dict)
    rationale: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Diagnostics:
    hypotheses: List[Hypothesis] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    tool_traces: List[ToolTrace] = field(default_factory=list)
    confidence: Dict[str, float] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Top-level draft
# ============================================================

KNOWN_TOP_LEVEL_KEYS = {
    "classes",
    "data_properties",
    "object_properties",
    "subclass_relations",
    "class_mappings",
    "data_property_mappings",
    "object_property_mappings",
    "diagnostics",
    "extras",
}


@dataclass
class OntologyDraft:
    classes: List[ClassDef] = field(default_factory=list)
    data_properties: List[DataPropertyDef] = field(default_factory=list)
    object_properties: List[ObjectPropertyDef] = field(default_factory=list)
    subclass_relations: List[SubclassRelation] = field(default_factory=list)

    class_mappings: List[ClassMapping] = field(default_factory=list)
    data_property_mappings: List[DataPropertyMapping] = field(default_factory=list)
    object_property_mappings: List[ObjectPropertyMapping] = field(default_factory=list)

    diagnostics: Diagnostics = field(default_factory=Diagnostics)
    extras: Dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------------
    # Index helpers
    # --------------------------------------------------------
    def class_index(self) -> Dict[str, ClassDef]:
        return {c.id: c for c in self.classes}

    def data_property_index(self) -> Dict[str, DataPropertyDef]:
        return {p.id: p for p in self.data_properties}

    def object_property_index(self) -> Dict[str, ObjectPropertyDef]:
        return {p.id: p for p in self.object_properties}

    def class_mapping_index(self) -> Dict[str, ClassMapping]:
        return {m.class_id: m for m in self.class_mappings}

    def data_property_mapping_index(self) -> Dict[str, DataPropertyMapping]:
        return {m.property_id: m for m in self.data_property_mappings}

    def object_property_mapping_index(self) -> Dict[str, ObjectPropertyMapping]:
        return {m.property_id: m for m in self.object_property_mappings}

    # --------------------------------------------------------
    # Debug / trace helpers
    # --------------------------------------------------------
    def normalization_report(self) -> Dict[str, Any]:
        return _safe_dict(self.extras.get("normalization_report"))

    def normalization_messages(
        self,
        level: Optional[str] = None,
        code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        messages = _as_list(self.normalization_report().get("messages"))
        out = []
        for m in messages:
            md = _safe_dict(m)
            if level is not None and md.get("level") != level:
                continue
            if code is not None and md.get("code") != code:
                continue
            out.append(md)
        return out

    def root_cause_summary(self) -> Dict[str, Any]:
        ok, validation_errors = self.validate()
        nr = self.normalization_report()
        return {
            "normalization_summary": {
                "ok": nr.get("ok", True),
                "num_messages": len(_as_list(nr.get("messages"))),
                "by_level": self._count_by_key(_as_list(nr.get("messages")), "level"),
                "by_code": self._count_by_key(_as_list(nr.get("messages")), "code"),
            },
            "validation_ok": ok,
            "validation_num_errors": len(validation_errors),
            "validation_errors": validation_errors,
        }

    @staticmethod
    def _count_by_key(items: List[Dict[str, Any]], key: str) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for x in items:
            k = str(_safe_dict(x).get(key, "UNKNOWN"))
            out[k] = out.get(k, 0) + 1
        return out

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------
    def _is_exportable_status(self, status: Optional[str]) -> bool:
        s = str(status or "").strip().lower()
        if not s:
            return True
        return s not in {"rejected", "invalid", "discarded", "dropped"}

    def validate(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        class_idx = self.class_index()
        dp_idx = self.data_property_index()
        op_idx = self.object_property_index()

        class_ids = set(class_idx.keys())
        data_prop_ids = set(dp_idx.keys())
        object_prop_ids = set(op_idx.keys())

        if len(class_ids) != len(self.classes):
            errors.append("Duplicate class ids found.")
        if len(data_prop_ids) != len(self.data_properties):
            errors.append("Duplicate data property ids found.")
        if len(object_prop_ids) != len(self.object_properties):
            errors.append("Duplicate object property ids found.")

        class_map_idx = self.class_mapping_index()
        dp_map_idx = self.data_property_mapping_index()
        op_map_idx = self.object_property_mapping_index()

        # Classes
        for c in self.classes:
            if self._is_exportable_status(c.status):
                cm = class_map_idx.get(c.id)
                if cm is None:
                    errors.append(f"Class {c.id} has no class mapping.")
                else:
                    cm_from_tables = getattr(cm, "from_tables", None) or []
                    cm_instance_id_template = getattr(cm, "instance_id_template", None)

                    effective_tables = list(dict.fromkeys((c.source_tables or []) + cm_from_tables))
                    if not effective_tables:
                        errors.append(
                            f"Class {c.id} has neither source_tables nor class_mapping.from_tables."
                        )
                    if not cm_instance_id_template:
                        errors.append(f"Class mapping for {c.id} has no instance_id_template.")

        # Data properties
        for p in self.data_properties:
            if p.domain_class not in class_ids:
                errors.append(f"Data property {p.id} references unknown domain class {p.domain_class}.")

            dm = dp_map_idx.get(p.id)
            if self._is_exportable_status(p.status):
                if dm is None:
                    errors.append(f"Data property {p.id} has no data_property_mapping.")
                else:
                    effective_cols = list(p.source_columns or [])

                    dm_column = getattr(dm, "column", None)
                    if dm_column:
                        effective_cols.append(dm_column)

                    dm_source_columns = getattr(dm, "source_columns", None)
                    if dm_source_columns:
                        effective_cols.extend(dm_source_columns)

                    effective_cols = [c for c in dict.fromkeys(effective_cols) if c]

                    if not effective_cols:
                        errors.append(
                            f"Data property {p.id} has neither source_columns nor a usable data_property_mapping column."
                        )

                    dm_from_class = getattr(dm, "from_class", None)
                    if dm_from_class and p.domain_class and dm_from_class != p.domain_class:
                        errors.append(
                            f"Data property {p.id} domain mismatch: property={p.domain_class}, mapping={dm_from_class}."
                        )

        # Object properties
        for p in self.object_properties:
            if p.domain_class not in class_ids:
                errors.append(f"Object property {p.id} references unknown domain class {p.domain_class}.")
            if p.range_class not in class_ids:
                errors.append(f"Object property {p.id} references unknown range class {p.range_class}.")

            om = op_map_idx.get(p.id)
            if self._is_exportable_status(p.status):
                if om is None:
                    errors.append(f"Object property {p.id} has no object_property_mapping.")
                else:
                    om_joins = getattr(om, "joins", None) or []
                    effective_joins = (p.join_paths or []) or om_joins
                    if not effective_joins:
                        errors.append(
                            f"Object property {p.id} has neither join_paths nor object_property_mapping.joins."
                        )

                    om_from_class = getattr(om, "from_class", None)
                    om_to_class = getattr(om, "to_class", None)

                    if om_from_class and p.domain_class and om_from_class != p.domain_class:
                        errors.append(
                            f"Object property {p.id} domain mismatch: property={p.domain_class}, mapping={om_from_class}."
                        )
                    if om_to_class and p.range_class and om_to_class != p.range_class:
                        errors.append(
                            f"Object property {p.id} range mismatch: property={p.range_class}, mapping={om_to_class}."
                        )

        # Subclass relations
        for rel in self.subclass_relations:
            if rel.child_class not in class_ids:
                errors.append(f"Subclass relation references unknown child class {rel.child_class}.")
            if rel.parent_class not in class_ids:
                errors.append(f"Subclass relation references unknown parent class {rel.parent_class}.")

        return len(errors) == 0, errors
    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(
        cls,
        obj: Dict[str, Any],
        *,
        already_normalized: bool = False,
    ) -> "OntologyDraft":
        normalized = copy.deepcopy(obj) if already_normalized else normalize_model_output_robust(obj)
        diagnostics_obj = _safe_dict(normalized.get("diagnostics"))

        draft = cls(
            classes=[_build_dataclass(ClassDef, x) for x in _as_list(normalized.get("classes"))],
            data_properties=[_build_dataclass(DataPropertyDef, x) for x in _as_list(normalized.get("data_properties"))],
            object_properties=[_build_dataclass(ObjectPropertyDef, x) for x in _as_list(normalized.get("object_properties"))],
            subclass_relations=[_build_dataclass(SubclassRelation, x) for x in _as_list(normalized.get("subclass_relations"))],

            class_mappings=[_build_dataclass(ClassMapping, x) for x in _as_list(normalized.get("class_mappings"))],
            data_property_mappings=[_build_dataclass(DataPropertyMapping, x) for x in _as_list(normalized.get("data_property_mappings"))],
            object_property_mappings=[_build_dataclass(ObjectPropertyMapping, x) for x in _as_list(normalized.get("object_property_mappings"))],

            diagnostics=Diagnostics(
                hypotheses=[_build_dataclass(Hypothesis, x) for x in _as_list(diagnostics_obj.get("hypotheses"))],
                conflicts=[_build_dataclass(Conflict, x) for x in _as_list(diagnostics_obj.get("conflicts"))],
                tool_traces=[_build_dataclass(ToolTrace, x) for x in _as_list(diagnostics_obj.get("tool_traces"))],
                confidence=_safe_dict(diagnostics_obj.get("confidence")),
                extras={
                    **_safe_dict(diagnostics_obj.get("extras")),
                    **{k: v for k, v in diagnostics_obj.items() if k not in _field_names(Diagnostics)}
                },
            ),
            extras={
                **_safe_dict(normalized.get("extras")),
                **{k: v for k, v in normalized.items() if k not in KNOWN_TOP_LEVEL_KEYS}
            },
        )

        return draft

    @classmethod
    def from_json(
        cls,
        text: str,
        *,
        already_normalized: bool = False,
    ) -> "OntologyDraft":
        return cls.from_dict(json.loads(text), already_normalized=already_normalized)

    @classmethod
    def from_burr_mapping(cls, burr_mapping: Dict[str, Any]) -> "OntologyDraft":
        return cls.from_dict(
            {
                "classes": burr_mapping.get("classes", []),
                "data_properties": burr_mapping.get("data_properties", []),
                "object_properties": burr_mapping.get("object_properties", []),
            }
        )

    # --------------------------------------------------------
    # Conversion back to Burr mapping
    # --------------------------------------------------------


    def to_burr_mapping(self) -> Dict[str, Any]:
        class_map_idx = self.class_mapping_index()
        dp_map_idx = self.data_property_mapping_index()
        op_map_idx = self.object_property_mapping_index()

        out: Dict[str, Any] = {
            "classes": [],
            "object_properties": [],
            "data_properties": [],
        }

        # Classes
        for c in self.classes:
            if not self._is_exportable_status(c.status):
                continue

            cm = class_map_idx.get(c.id)
            if cm is None:
                continue
            if not cm.instance_id_template:
                continue

            item = {
                "id": cm.instance_id_template,
                "class": c.label,
                "name": c.label,
            }
            if c.extras:
                item.update(c.extras)
            out["classes"].append(item)

        # Object properties
        for p in self.object_properties:
            if not self._is_exportable_status(p.status):
                continue

            om = op_map_idx.get(p.id)
            if om is None:
                continue

            joins = om.joins or p.join_paths or []
            if not joins:
                continue

            item = {
                "property": _to_burr_safe_property_name(p.label),
                "belongsToClassMap": _label_from_class_id(om.from_class or p.domain_class),
                "refersToClassMap": _label_from_class_id(om.to_class or p.range_class),
                "join": [_join_to_burr_string(j) for j in joins],
            }
            if p.extras:
                item.update(p.extras)
            out["object_properties"].append(item)

        # Data properties
        for p in self.data_properties:
            if not self._is_exportable_status(p.status):
                continue

            dm = dp_map_idx.get(p.id)
            if dm is None:
                continue

            effective_column = getattr(dm, "column", None)
            if not effective_column:
                dm_source_columns = getattr(dm, "source_columns", None) or []
                if dm_source_columns:
                    effective_column = dm_source_columns[0]
                elif p.source_columns:
                    effective_column = p.source_columns[0]

            if not effective_column:
                continue

            item = {
                "property": _to_burr_safe_property_name(p.label),
                "belongsToClassMap": _label_from_class_id(dm.from_class or p.domain_class),
                "column": effective_column,
            }
            if p.extras:
                item.update(p.extras)
            out["data_properties"].append(item)

        return out

    # --------------------------------------------------------
    # Optional convenience constructors
    # --------------------------------------------------------
    def add_class(
        self,
        label: str,
        instance_id_template: str,
        source_tables: Optional[List[str]] = None,
        description: Optional[str] = None,
        confidence: Optional[float] = None,
        where: Optional[List[str]] = None,
        joins: Optional[List[List[str]]] = None,
        identifier_columns: Optional[List[str]] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> str:
        class_id = _normalize_class_id(label)

        if source_tables is None:
            source_tables = _infer_tables_from_template(instance_id_template)
        if identifier_columns is None:
            identifier_columns = _extract_identifier_columns(instance_id_template)

        if class_id not in self.class_index():
            self.classes.append(
                ClassDef(
                    id=class_id,
                    label=label,
                    description=description,
                    source_tables=source_tables or [],
                    status="accepted",
                    confidence=confidence,
                    extras=extras or {},
                )
            )

        if class_id not in self.class_mapping_index():
            self.class_mappings.append(
                ClassMapping(
                    class_id=class_id,
                    instance_id_template=instance_id_template,
                    from_tables=source_tables or [],
                    where=where or [],
                    joins=joins or [],
                    identifier_columns=identifier_columns or [],
                    extras={},
                )
            )

        return class_id

    def add_data_property(
        self,
        domain_class: str,
        label: str,
        column: str,
        range_type: str = "string",
        confidence: Optional[float] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> str:
        domain_class = _normalize_class_id(domain_class)
        property_id = _normalize_data_property_id(domain_class, label)

        if property_id not in self.data_property_index():
            self.data_properties.append(
                DataPropertyDef(
                    id=property_id,
                    label=label,
                    domain_class=domain_class,
                    range_type=range_type,
                    source_columns=[column] if column else [],
                    status="accepted",
                    confidence=confidence,
                    extras=extras or {},
                )
            )

        if property_id not in self.data_property_mapping_index():
            self.data_property_mappings.append(
                DataPropertyMapping(
                    property_id=property_id,
                    from_class=domain_class,
                    column=column,
                    extras={},
                )
            )

        return property_id

    def add_object_property(
        self,
        domain_class: str,
        label: str,
        range_class: str,
        joins: List[List[str]],
        confidence: Optional[float] = None,
        reified: bool = False,
        extras: Optional[Dict[str, Any]] = None,
    ) -> str:
        domain_class = _normalize_class_id(domain_class)
        range_class = _normalize_class_id(range_class)
        property_id = _normalize_object_property_id(domain_class, label)

        if property_id not in self.object_property_index():
            self.object_properties.append(
                ObjectPropertyDef(
                    id=property_id,
                    label=label,
                    domain_class=domain_class,
                    range_class=range_class,
                    join_paths=joins or [],
                    reified=reified,
                    status="accepted",
                    confidence=confidence,
                    extras=extras or {},
                )
            )

        if property_id not in self.object_property_mapping_index():
            self.object_property_mappings.append(
                ObjectPropertyMapping(
                    property_id=property_id,
                    from_class=domain_class,
                    to_class=range_class,
                    joins=joins or [],
                    where=[],
                    extras={},
                )
            )

        return property_id