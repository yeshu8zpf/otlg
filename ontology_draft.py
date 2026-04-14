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
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "UNKNOWN"

def _to_burr_safe_classmap_name(label: str) -> str:
    """
    Make a Turtle/D2RQ-safe class map name.
    Examples:
      "Ethnic Group" -> "EthnicGroup"
      "Country Population Record" -> "CountryPopulationRecord"
      "GDP" -> "GDP"
    """
    s = str(label or "").strip()
    if not s:
        return "UNKNOWN"

    # Split on non-alnum boundaries, then CamelCase-join.
    parts = re.split(r"[^A-Za-z0-9]+", s)
    parts = [p for p in parts if p]
    if not parts:
        return "UNKNOWN"

    return "".join(p[:1].upper() + p[1:] for p in parts)


def _ensure_qualified_column(column: str, source_table: str = "") -> str:
    """
    Ensure a column is in 'table.column' form when possible.
    If already qualified, keep it unchanged.
    If unqualified and source_table is available, prefix it.
    """
    col = _as_str(column).strip()
    tbl = _as_str(source_table).strip()

    if not col:
        return ""

    if parse_qualified_column(col) is not None:
        return col

    if tbl and IDENT_RE.match(tbl):
        return f"{tbl}.{col}"

    return col


def _ensure_burr_template(template: str, fallback_table: str = "", fallback_identifier_columns: Optional[List[str]] = None) -> str:
    """
    Convert/repair instance_id_template into a form Burr can consume.
    Preferred token form: @@table.column@@

    Supported inputs:
    - @@table.column@@
    - {table.column}
    - table/@@table.id@@
    - plain table.column (will wrap)
    """
    text = _as_str(template).strip()
    fallback_identifier_columns = fallback_identifier_columns or []

    if not text and fallback_identifier_columns:
        col = _ensure_qualified_column(fallback_identifier_columns[0], fallback_table)
        if parse_qualified_column(col):
            return f"@@{col}@@"

    if not text:
        return ""

    # Already contains Burr token(s)
    if "@@" in text:
        return text

    # Replace {table.column} -> @@table.column@@
    def repl(m):
        inner = m.group(1).strip()
        inner = _ensure_qualified_column(inner, fallback_table)
        return f"@@{inner}@@"

    text = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}", repl, text)

    if "@@" in text:
        return text

    # Plain qualified column -> wrap
    if parse_qualified_column(text):
        return f"@@{text}@@"

    # If it looks like an unqualified column and we have fallback table
    maybe = _ensure_qualified_column(text, fallback_table)
    if parse_qualified_column(maybe):
        return f"@@{maybe}@@"

    return text

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
    Normalize a join condition into token form: ["table1.col1", "=", "table2.col2"]
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
    raw = cid.replace("Class:", "")
    return _to_burr_safe_classmap_name(raw)


def _coerce_float01(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        v = float(x)
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v
    except Exception:
        return None


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
    raw = _safe_dict(obj.get("normalization_report"))
    issues = []
    for x in _as_list(raw.get("issues")):
        d = _safe_dict(x)
        issues.append(
            NormalizationMessage(
                level=_as_str(d.get("level")) or "info",
                code=_as_str(d.get("code")) or "UNKNOWN",
                message=_as_str(d.get("message")),
                path=d.get("path"),
                payload=_safe_dict(d.get("payload")),
            )
        )

    stats = {
        "num_errors": raw.get("num_errors", 0),
        "num_warnings": raw.get("num_warnings", 0),
        "num_infos": raw.get("num_infos", 0),
    }
    ok = stats["num_errors"] == 0
    return NormalizationReport(ok=ok, messages=issues, stats=stats)


# ============================================================
# Dataclasses
# ============================================================

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
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyDef:
    id: str
    label: str
    domain_class: str
    range_type: str = "string"
    source_columns: List[str] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    description: str = ""
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
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPropertyMapping:
    property_id: str
    from_class: str = ""
    source_table: str = ""
    column: str = ""
    source_columns: List[str] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectPropertyMapping:
    property_id: str
    from_class: str = ""
    to_class: str = ""
    joins: List[List[str]] = field(default_factory=list)
    status: str = "proposed"
    confidence: Optional[float] = None
    extras: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Defensive builder
# ============================================================

def _build_dataclass(cls, data: Dict[str, Any]):
    known, extra = _split_kwargs(cls, data)

    # Defensive alias repair for schema drift
    if cls.__name__ == "SubclassRelation":
        if "child_class" not in known:
            child = (
                data.get("child_class")
                or data.get("child")
                or data.get("subclass")
                or data.get("sub_class")
                or data.get("source_class")
                or data.get("source")
                or data.get("from_class")
                or data.get("child_class_id")
            )
            if child:
                known["child_class"] = _normalize_class_id(child)

        if "parent_class" not in known:
            parent = (
                data.get("parent_class")
                or data.get("parent")
                or data.get("superclass")
                or data.get("super_class")
                or data.get("target_class")
                or data.get("target")
                or data.get("to_class")
                or data.get("parent_class_id")
            )
            if parent:
                known["parent_class"] = _normalize_class_id(parent)

        if "id" not in known:
            child = known.get("child_class", "")
            parent = known.get("parent_class", "")
            if child and parent:
                known["id"] = f"SubclassRelation:{child}->{parent}"

    if cls.__name__ == "DataPropertyDef":
        if "domain_class" not in known:
            domain = data.get("domain_class") or data.get("domain") or data.get("from_class") or data.get("applies_to_class")
            if domain:
                known["domain_class"] = _normalize_class_id(domain)
        if "id" not in known:
            label = data.get("label") or data.get("name") or data.get("property_id") or data.get("data_property_id")
            domain = known.get("domain_class", "Class:UNKNOWN")
            if label:
                known["id"] = _normalize_data_property_id(domain, str(label))
        if "range_type" not in known:
            rt = data.get("range_type") or data.get("range") or data.get("datatype") or data.get("type")
            known["range_type"] = _as_str(rt) or "string"

    if cls.__name__ == "ObjectPropertyDef":
        if "domain_class" not in known:
            domain = data.get("domain_class") or data.get("domain") or data.get("from_class")
            if domain:
                known["domain_class"] = _normalize_class_id(domain)
        if "range_class" not in known:
            r = data.get("range_class") or data.get("range") or data.get("to_class") or data.get("target_class")
            if r:
                known["range_class"] = _normalize_class_id(r)
        if "id" not in known:
            label = data.get("label") or data.get("name") or data.get("property_id") or data.get("object_property_id")
            domain = known.get("domain_class", "Class:UNKNOWN")
            if label:
                known["id"] = _normalize_object_property_id(domain, str(label))
        if "join_paths" not in known:
            joins = data.get("join_paths") or data.get("joins") or []
            known["join_paths"] = [_normalize_join(j) for j in _as_list(joins)]

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
# Main Draft object
# ============================================================

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

    # --------------------------------------------------------
    # Constructors
    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        already_normalized: bool = False,
    ) -> "OntologyDraft":
        normalized = copy.deepcopy(payload)
        if not already_normalized:
            normalized = normalize_model_output_robust(payload)

        report = get_normalization_report(normalized)

        draft = cls(
            classes=[_build_dataclass(ClassDef, x) for x in _as_list(normalized.get("classes"))],
            data_properties=[_build_dataclass(DataPropertyDef, x) for x in _as_list(normalized.get("data_properties"))],
            object_properties=[_build_dataclass(ObjectPropertyDef, x) for x in _as_list(normalized.get("object_properties"))],
            subclass_relations=[_build_dataclass(SubclassRelation, x) for x in _as_list(normalized.get("subclass_relations"))],
            class_mappings=[_build_dataclass(ClassMapping, x) for x in _as_list(normalized.get("class_mappings"))],
            data_property_mappings=[_build_dataclass(DataPropertyMapping, x) for x in _as_list(normalized.get("data_property_mappings"))],
            object_property_mappings=[_build_dataclass(ObjectPropertyMapping, x) for x in _as_list(normalized.get("object_property_mappings"))],
            diagnostics=_safe_dict(normalized.get("diagnostics")),
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

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

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
            "diagnostics": copy.deepcopy(self.diagnostics),
            "normalization_report": self.normalization_report(),
        }
        if self.extras:
            out["extras"] = copy.deepcopy(self.extras)
        return out

    # --------------------------------------------------------
    # Indexes
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Internal repair
    # --------------------------------------------------------

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
                c.source_tables = _infer_tables_from_template(c.instance_id_template)
            if not c.identifier_columns and c.instance_id_template:
                c.identifier_columns = _extract_identifier_columns(c.instance_id_template)

        for p in self.data_properties:
            p.domain_class = _normalize_class_id(p.domain_class)
            if not p.id:
                p.id = _normalize_data_property_id(p.domain_class, p.label)

            dm = dpm_idx.get(p.id)
            if dm:
                if not dm.from_class:
                    dm.from_class = p.domain_class
                if not p.source_columns:
                    cols = []
                    if dm.column:
                        cols.append(dm.column)
                    cols.extend(dm.source_columns or [])
                    p.source_columns = _dedup_keep_order([c for c in cols if c])
                if not p.domain_class and dm.from_class:
                    p.domain_class = _normalize_class_id(dm.from_class)

        for p in self.object_properties:
            p.domain_class = _normalize_class_id(p.domain_class)
            p.range_class = _normalize_class_id(p.range_class)
            if not p.id:
                p.id = _normalize_object_property_id(p.domain_class, p.label)

            om = opm_idx.get(p.id)
            if om:
                if not om.from_class:
                    om.from_class = p.domain_class
                if not om.to_class:
                    om.to_class = p.range_class
                if not p.join_paths and om.joins:
                    p.join_paths = [list(j) for j in om.joins]

        # Ensure mappings point to normalized class ids
        for m in self.class_mappings:
            m.class_id = _normalize_class_id(m.class_id)
        for m in self.data_property_mappings:
            if m.from_class:
                m.from_class = _normalize_class_id(m.from_class)
        for m in self.object_property_mappings:
            if m.from_class:
                m.from_class = _normalize_class_id(m.from_class)
            if m.to_class:
                m.to_class = _normalize_class_id(m.to_class)

        # Normalize subclass relation ids / targets
        for rel in self.subclass_relations:
            rel.child_class = _normalize_class_id(rel.child_class)
            rel.parent_class = _normalize_class_id(rel.parent_class)
            if not rel.id and rel.child_class and rel.parent_class:
                rel.id = f"SubclassRelation:{rel.child_class}->{rel.parent_class}"

        # Optional: synthesize minimal class mappings if absent
        if not self.class_mappings:
            for c in self.classes:
                if c.source_tables or c.instance_id_template:
                    self.class_mappings.append(
                        ClassMapping(
                            class_id=c.id,
                            from_tables=list(c.source_tables or _infer_tables_from_template(c.instance_id_template)),
                            identifier_columns=list(c.identifier_columns or _extract_identifier_columns(c.instance_id_template)),
                            instance_id_template=c.instance_id_template or "",
                            status=c.status or "proposed",
                            confidence=c.confidence,
                        )
                    )

    # --------------------------------------------------------
    # Shared effective closure helpers
    # --------------------------------------------------------

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
                out.extend(_infer_tables_from_template(cm.instance_id_template))
        if not out and c.instance_id_template:
            out.extend(_infer_tables_from_template(c.instance_id_template))
        return _dedup_keep_order([x for x in out if x])

    def _effective_identifier_columns(self, c: ClassDef, cm: Optional[ClassMapping]) -> List[str]:
        out = list(c.identifier_columns or [])
        if cm is not None:
            out.extend(cm.identifier_columns or [])
            if not out and cm.instance_id_template:
                out.extend(_extract_identifier_columns(cm.instance_id_template))
        if not out and c.instance_id_template:
            out.extend(_extract_identifier_columns(c.instance_id_template))
        return _dedup_keep_order([x for x in out if x])

    def _effective_instance_id_template(self, c: ClassDef, cm: Optional[ClassMapping]) -> str:
        if cm is not None and cm.instance_id_template:
            return cm.instance_id_template
        return c.instance_id_template or ""

    def _effective_data_property_columns(
        self,
        p: DataPropertyDef,
        dm: Optional[DataPropertyMapping],
    ) -> List[str]:
        out = list(p.source_columns or [])
        if dm is not None:
            if dm.column:
                out.append(dm.column)
            out.extend(dm.source_columns or [])
        return _dedup_keep_order([x for x in out if x])

    def _effective_object_property_joins(
        self,
        p: ObjectPropertyDef,
        om: Optional[ObjectPropertyMapping],
    ) -> List[List[str]]:
        if p.join_paths:
            return [list(_normalize_join(j)) for j in p.join_paths if _normalize_join(j)]
        if om is not None and om.joins:
            return [list(_normalize_join(j)) for j in om.joins if _normalize_join(j)]
        return []

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

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
                    if not effective_tables:
                        errors.append(
                            f"Class {c.id} has neither source_tables nor class_mapping.from_tables."
                        )
                    effective_template = self._effective_instance_id_template(c, cm)
                    if not effective_template:
                        errors.append(f"Class mapping for {c.id} has no instance_id_template.")

        for p in self.data_properties:
            if p.domain_class not in class_ids:
                errors.append(f"Data property {p.id} references unknown domain class {p.domain_class}.")

            if self._is_exportable_status(p.status):
                dm = dp_map_idx.get(p.id)
                if dm is None:
                    errors.append(f"Data property {p.id} has no data_property_mapping.")
                else:
                    effective_cols = self._effective_data_property_columns(p, dm)
                    if not effective_cols:
                        errors.append(
                            f"Data property {p.id} has neither source_columns nor a usable data_property_mapping column."
                        )
                    if dm.from_class and p.domain_class and dm.from_class != p.domain_class:
                        errors.append(
                            f"Data property {p.id} domain mismatch: property={p.domain_class}, mapping={dm.from_class}."
                        )

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
                    if not effective_joins:
                        errors.append(
                            f"Object property {p.id} has neither join_paths nor object_property_mapping.joins."
                        )
                    if om.from_class and p.domain_class and om.from_class != p.domain_class:
                        errors.append(
                            f"Object property {p.id} domain mismatch: property={p.domain_class}, mapping={om.from_class}."
                        )
                    if om.to_class and p.range_class and om.to_class != p.range_class:
                        errors.append(
                            f"Object property {p.id} range mismatch: property={p.range_class}, mapping={om.to_class}."
                        )

        for rel in self.subclass_relations:
            if rel.child_class not in class_ids:
                errors.append(f"Subclass relation references unknown child class {rel.child_class}.")
            if rel.parent_class not in class_ids:
                errors.append(f"Subclass relation references unknown parent class {rel.parent_class}.")

        return len(errors) == 0, errors

    # --------------------------------------------------------
    # Export
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

            effective_tables = self._effective_class_tables(c, cm)
            effective_identifier_columns = self._effective_identifier_columns(c, cm)
            effective_template = self._effective_instance_id_template(c, cm)

            fallback_table = effective_tables[0] if effective_tables else ""
            repaired_template = _ensure_burr_template(
                effective_template,
                fallback_table=fallback_table,
                fallback_identifier_columns=effective_identifier_columns,
            )
            if not repaired_template:
                continue

            safe_class_name = _to_burr_safe_classmap_name(c.label)

            item = {
                "id": repaired_template,
                "class": safe_class_name,
                "name": safe_class_name,
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

            joins = self._effective_object_property_joins(p, om)
            if not joins:
                continue

            repaired_joins = []
            for j in joins:
                norm = _normalize_join(j)
                if len(norm) >= 3:
                    lhs = norm[0]
                    op = norm[1]
                    rhs = norm[2]
                    repaired_joins.append([lhs, op, rhs])
                else:
                    repaired_joins.append(norm)

            item = {
                "property": _to_burr_safe_property_name(p.label),
                "belongsToClassMap": _label_from_class_id(om.from_class or p.domain_class),
                "refersToClassMap": _label_from_class_id(om.to_class or p.range_class),
                "join": [_join_to_burr_string(j) for j in repaired_joins],
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

            effective_cols = self._effective_data_property_columns(p, dm)
            if not effective_cols:
                continue

            source_table = _as_str(dm.source_table).strip()
            repaired_cols = [_ensure_qualified_column(col, source_table) for col in effective_cols]
            repaired_cols = [c for c in repaired_cols if c]

            if not repaired_cols:
                continue

            item = {
                "property": _to_burr_safe_property_name(p.label),
                "belongsToClassMap": _label_from_class_id(dm.from_class or p.domain_class),
                "column": repaired_cols[0],
            }
            if p.extras:
                item.update(p.extras)
            out["data_properties"].append(item)

        return out