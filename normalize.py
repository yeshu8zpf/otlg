from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Collector
# ============================================================


@dataclass
class NormalizationIssue:
    level: str
    code: str
    message: str
    path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "level": self.level,
            "code": self.code,
            "message": self.message,
        }
        if self.path is not None:
            out["path"] = self.path
        if self.payload:
            out["payload"] = self.payload
        return out


@dataclass
class NormalizationCollector:
    issues: List[NormalizationIssue] = field(default_factory=list)

    def add(
        self,
        level: str,
        code: str,
        message: str,
        path: Optional[str] = None,
        **payload: Any,
    ) -> None:
        self.issues.append(
            NormalizationIssue(
                level=level,
                code=code,
                message=message,
                path=path,
                payload=payload,
            )
        )

    def report(self) -> Dict[str, Any]:
        num_errors = sum(1 for x in self.issues if x.level == "error")
        num_warnings = sum(1 for x in self.issues if x.level == "warning")
        num_infos = sum(1 for x in self.issues if x.level == "info")
        return {
            "num_errors": num_errors,
            "num_warnings": num_warnings,
            "num_infos": num_infos,
            "issues": [x.to_dict() for x in self.issues],
        }


# ============================================================
# Generic helpers
# ============================================================


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _safe_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _coerce_confidence(x: Any) -> Optional[float]:
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


def _normalize_ws(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _normalize_identifier(s: Any) -> str:
    s = _normalize_ws(s)
    return s


def _strip_prefix_if_present(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def _normalize_class_id(x: Any) -> str:
    s = _normalize_identifier(x)
    if not s:
        return ""
    if s.startswith("Class:"):
        return s
    return f"Class:{s}"


def _normalize_property_id(x: Any, kind: str) -> str:
    s = _normalize_identifier(x)
    if not s:
        return ""
    wanted = f"{kind}:"
    if s.startswith(wanted):
        return s
    if ":" in s:
        return s
    return f"{kind}:{s}"


def _normalize_range_type(x: Any) -> str:
    s = _normalize_ws(x)
    if not s:
        return "string"
    low = s.lower()
    if low in {"str", "string", "text", "varchar", "character varying"}:
        return "string"
    if low in {"int", "integer", "bigint", "smallint"}:
        return "integer"
    if low in {"float", "double", "real", "numeric", "decimal"}:
        return "decimal"
    if low in {"bool", "boolean"}:
        return "boolean"
    if low in {"date"}:
        return "date"
    if low in {"datetime", "timestamp"}:
        return "datetime"
    return s


def _build_index_by_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for x in items:
        xid = x.get("id")
        if xid:
            out[str(xid)] = x
    return out


def _find_root_payload(obj: Dict[str, Any], collector: NormalizationCollector) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        collector.add(
            "warning",
            "ROOT_NOT_DICT",
            "Root payload is not a dict; coercing to empty dict.",
        )
        return {}

    direct_signal_keys = {
        "classes",
        "data_properties",
        "object_properties",
        "subclass_relations",
        "class_mappings",
        "data_property_mappings",
        "object_property_mappings",
    }
    if any(k in obj for k in direct_signal_keys):
        return obj

    for container_key in ["ontology", "draft", "output", "result", "payload", "data"]:
        inner = obj.get(container_key)
        if isinstance(inner, dict) and any(k in inner for k in direct_signal_keys):
            collector.add(
                "info",
                "ROOT_UNWRAPPED",
                f"Unwrapped nested payload from '{container_key}'.",
                path=container_key,
            )
            return inner

    return obj


# ============================================================
# Canonicalizers
# ============================================================


def _canonicalize_class(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    cid_raw = d.get("id") or d.get("class_id") or d.get("name") or d.get("label")
    cid = _normalize_class_id(cid_raw)
    label = d.get("label") or _strip_prefix_if_present(cid, "Class:")

    source_tables = [_normalize_identifier(t) for t in _as_list(d.get("source_tables") or d.get("from_tables")) if _normalize_identifier(t)]
    identifier_columns = [_normalize_identifier(c) for c in _as_list(d.get("identifier_columns")) if _normalize_identifier(c)]

    out: Dict[str, Any] = {
        "id": cid,
        "label": _normalize_ws(label),
        "source_tables": list(dict.fromkeys(source_tables)),
        "identifier_columns": list(dict.fromkeys(identifier_columns)),
        "instance_id_template": _normalize_ws(d.get("instance_id_template") or d.get("uri_template") or ""),
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    extras = {k: v for k, v in d.items() if k not in {
        "id", "class_id", "name", "label", "source_tables", "from_tables",
        "identifier_columns", "instance_id_template", "uri_template", "status",
        "confidence", "description",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_data_property(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    pid_raw = d.get("id") or d.get("data_property_id") or d.get("property_id") or d.get("name") or d.get("label")
    pid = _normalize_property_id(pid_raw, "DataProperty")
    label = d.get("label") or _strip_prefix_if_present(pid, "DataProperty:")

    domain = d.get("domain_class") or d.get("domain") or d.get("applies_to_class") or d.get("from_class")
    range_type = d.get("range_type") or d.get("range") or d.get("datatype") or d.get("type")
    source_columns = [
        _normalize_identifier(c)
        for c in _as_list(d.get("source_columns") or d.get("columns"))
        if _normalize_identifier(c)
    ]
    if d.get("column"):
        c = _normalize_identifier(d.get("column"))
        if c:
            source_columns.append(c)

    out: Dict[str, Any] = {
        "id": pid,
        "label": _normalize_ws(label),
        "domain_class": _normalize_class_id(domain) if domain else "",
        "range_type": _normalize_range_type(range_type),
        "source_columns": list(dict.fromkeys(source_columns)),
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    extras = {k: v for k, v in d.items() if k not in {
        "id", "data_property_id", "property_id", "name", "label",
        "domain_class", "domain", "applies_to_class", "from_class",
        "range_type", "range", "datatype", "type",
        "source_columns", "columns", "column",
        "status", "confidence", "description",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_object_property(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    pid_raw = d.get("id") or d.get("object_property_id") or d.get("property_id") or d.get("name") or d.get("label")
    pid = _normalize_property_id(pid_raw, "ObjectProperty")
    label = d.get("label") or _strip_prefix_if_present(pid, "ObjectProperty:")

    domain = d.get("domain_class") or d.get("domain") or d.get("from_class")
    range_class = d.get("range_class") or d.get("range") or d.get("to_class") or d.get("target_class")
    join_paths = _as_list(d.get("join_paths") or d.get("joins"))

    out: Dict[str, Any] = {
        "id": pid,
        "label": _normalize_ws(label),
        "domain_class": _normalize_class_id(domain) if domain else "",
        "range_class": _normalize_class_id(range_class) if range_class else "",
        "join_paths": join_paths,
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    extras = {k: v for k, v in d.items() if k not in {
        "id", "object_property_id", "property_id", "name", "label",
        "domain_class", "domain", "from_class",
        "range_class", "range", "to_class", "target_class",
        "join_paths", "joins",
        "status", "confidence", "description",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_subclass_relation(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)

    child = (
        d.get("child_class")
        or d.get("child")
        or d.get("subclass")
        or d.get("sub_class")
        or d.get("source_class")
        or d.get("source")
        or d.get("from_class")
        or d.get("child_class_id")
    )
    parent = (
        d.get("parent_class")
        or d.get("parent")
        or d.get("superclass")
        or d.get("super_class")
        or d.get("target_class")
        or d.get("target")
        or d.get("to_class")
        or d.get("parent_class_id")
    )

    child = _normalize_class_id(child) if child else ""
    parent = _normalize_class_id(parent) if parent else ""

    rid = (
        d.get("id")
        or d.get("relation_id")
        or d.get("subclass_relation_id")
        or (f"SubclassRelation:{child}->{parent}" if child and parent else "")
    )

    out: Dict[str, Any] = {
        "id": _normalize_identifier(rid),
        "child_class": child,
        "parent_class": parent,
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    if d.get("description"):
        out["description"] = d.get("description")

    extras = {k: v for k, v in d.items() if k not in {
        "id", "relation_id", "subclass_relation_id",
        "child_class", "child", "subclass", "sub_class", "source_class", "source", "from_class", "child_class_id",
        "parent_class", "parent", "superclass", "super_class", "target_class", "target", "to_class", "parent_class_id",
        "status", "confidence", "description",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_class_mapping(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    class_id = _normalize_class_id(d.get("class_id") or d.get("class") or d.get("applies_to_class") or d.get("from_class"))
    from_tables = [_normalize_identifier(t) for t in _as_list(d.get("from_tables") or d.get("source_tables")) if _normalize_identifier(t)]
    identifier_columns = [_normalize_identifier(c) for c in _as_list(d.get("identifier_columns")) if _normalize_identifier(c)]

    out = {
        "class_id": class_id,
        "from_tables": list(dict.fromkeys(from_tables)),
        "identifier_columns": list(dict.fromkeys(identifier_columns)),
        "instance_id_template": _normalize_ws(d.get("instance_id_template") or d.get("uri_template") or ""),
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    extras = {k: v for k, v in d.items() if k not in {
        "class_id", "class", "applies_to_class", "from_class", "from_tables", "source_tables",
        "identifier_columns", "instance_id_template", "uri_template", "status", "confidence",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_data_property_mapping(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    property_id = _normalize_property_id(d.get("property_id") or d.get("data_property_id") or d.get("id") or d.get("label"), "DataProperty")
    source_columns = [_normalize_identifier(c) for c in _as_list(d.get("source_columns") or d.get("columns")) if _normalize_identifier(c)]
    column = _normalize_identifier(d.get("column"))
    if column and column not in source_columns:
        source_columns.append(column)

    out = {
        "property_id": property_id,
        "from_class": _normalize_class_id(d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")) if (d.get("from_class") or d.get("applies_to_class") or d.get("domain") or d.get("domain_class")) else "",
        "source_table": _normalize_identifier(d.get("source_table") or d.get("table") or ""),
        "source_columns": list(dict.fromkeys(source_columns)),
        "column": column,
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    extras = {k: v for k, v in d.items() if k not in {
        "property_id", "data_property_id", "id", "label", "from_class", "applies_to_class", "domain", "domain_class",
        "source_table", "table", "source_columns", "columns", "column", "status", "confidence",
    }}
    if extras:
        out["extras"] = extras
    return out


def _canonicalize_object_property_mapping(x: Any) -> Dict[str, Any]:
    d = _as_dict(x)
    property_id = _normalize_property_id(d.get("property_id") or d.get("object_property_id") or d.get("id") or d.get("label"), "ObjectProperty")

    out = {
        "property_id": property_id,
        "from_class": _normalize_class_id(d.get("from_class") or d.get("domain") or d.get("domain_class")) if (d.get("from_class") or d.get("domain") or d.get("domain_class")) else "",
        "to_class": _normalize_class_id(d.get("to_class") or d.get("range") or d.get("range_class") or d.get("target_class")) if (d.get("to_class") or d.get("range") or d.get("range_class") or d.get("target_class")) else "",
        "joins": _as_list(d.get("joins") or d.get("join_paths")),
        "status": _normalize_ws(d.get("status") or "proposed") or "proposed",
        "confidence": _coerce_confidence(d.get("confidence")),
    }
    extras = {k: v for k, v in d.items() if k not in {
        "property_id", "object_property_id", "id", "label",
        "from_class", "domain", "domain_class",
        "to_class", "range", "range_class", "target_class",
        "joins", "join_paths", "status", "confidence",
    }}
    if extras:
        out["extras"] = extras
    return out


# ============================================================
# Backfill / repair
# ============================================================


def _backfill_from_mappings(
    canonical: Dict[str, Any],
    collector: NormalizationCollector,
) -> Dict[str, Any]:
    canonical = copy.deepcopy(canonical)

    classes = canonical["classes"]
    data_properties = canonical["data_properties"]
    object_properties = canonical["object_properties"]

    class_mappings = canonical["class_mappings"]
    data_property_mappings = canonical["data_property_mappings"]
    object_property_mappings = canonical["object_property_mappings"]

    class_idx = _build_index_by_id(classes)
    dp_idx = _build_index_by_id(data_properties)
    op_idx = _build_index_by_id(object_properties)

    if not class_mappings:
        for c in classes:
            source_tables = c.get("source_tables") or []
            if not source_tables:
                continue
            cid = c.get("id")
            if not cid:
                continue
            identifier_columns = [str(x).strip() for x in (c.get("identifier_columns") or []) if str(x).strip()]
            class_mappings.append(
                {
                    "class_id": cid,
                    "from_tables": list(source_tables),
                    "identifier_columns": identifier_columns,
                    "instance_id_template": c.get("instance_id_template") or (
                        "{" + (identifier_columns[0] if identifier_columns else f"{source_tables[0]}.id") + "}"
                    ),
                    "status": c.get("status", "proposed"),
                    "confidence": c.get("confidence", 0.5),
                }
            )
            collector.add("info", "CLASS_MAPPING_SYNTHESIZED_FROM_CLASS", "Synthesized class mapping from class definition.", path=f"class_mappings[{cid}]", class_id=cid)

    for m in class_mappings:
        cid = m.get("class_id")
        if not cid:
            continue
        c = class_idx.get(cid)
        if c is None:
            continue

        mapped_tables = [str(t).strip() for t in (m.get("from_tables") or []) if str(t).strip()]
        mapped_ids = [str(x).strip() for x in (m.get("identifier_columns") or []) if str(x).strip()]

        if (not c.get("source_tables")) and mapped_tables:
            c["source_tables"] = mapped_tables
            collector.add("info", "CLASS_SOURCE_TABLES_BACKFILLED_FROM_MAPPING", "Backfilled source_tables from class_mapping.", path=f"classes[{cid}]", class_id=cid, source_tables=mapped_tables)
        if (not c.get("identifier_columns")) and mapped_ids:
            c["identifier_columns"] = mapped_ids
            collector.add("info", "CLASS_IDENTIFIER_COLUMNS_BACKFILLED", "Backfilled identifier_columns from class_mapping.", path=f"classes[{cid}]", class_id=cid, identifier_columns=mapped_ids)
        if (not c.get("instance_id_template")) and m.get("instance_id_template"):
            c["instance_id_template"] = m["instance_id_template"]
            collector.add("info", "CLASS_INSTANCE_TEMPLATE_BACKFILLED", "Backfilled instance_id_template from class_mapping.", path=f"classes[{cid}]", class_id=cid)

    if not data_property_mappings:
        for p in data_properties:
            pid = p.get("id")
            if not pid:
                continue
            source_columns = [str(c).strip() for c in (p.get("source_columns") or []) if str(c).strip()]
            source_table = ""
            if source_columns:
                first = source_columns[0]
                if "." in first:
                    source_table = first.split(".", 1)[0]
            data_property_mappings.append(
                {
                    "property_id": pid,
                    "from_class": p.get("domain_class"),
                    "source_table": source_table,
                    "source_columns": source_columns,
                    "column": source_columns[0] if source_columns else "",
                    "status": p.get("status", "proposed"),
                    "confidence": p.get("confidence", 0.5),
                }
            )
            collector.add("info", "DATA_PROPERTY_MAPPING_SYNTHESIZED_FROM_PROPERTY", "Synthesized data_property_mapping from data property definition.", path=f"data_property_mappings[{pid}]", property_id=pid)

    for m in data_property_mappings:
        pid = m.get("property_id")
        if not pid:
            continue
        p = dp_idx.get(pid)
        mapped_cols = [str(c).strip() for c in (m.get("source_columns") or []) if str(c).strip()]
        if m.get("column"):
            col = str(m.get("column")).strip()
            if col:
                mapped_cols.append(col)
        mapped_cols = list(dict.fromkeys(mapped_cols))

        if p is None:
            inferred_domain = m.get("from_class") or "Class:UNKNOWN"
            inferred_label = pid.split(":", 1)[-1] if ":" in str(pid) else str(pid)
            data_properties.append(
                {
                    "id": pid,
                    "label": inferred_label,
                    "domain_class": inferred_domain,
                    "range_type": "string",
                    "source_columns": mapped_cols,
                    "status": m.get("status", "proposed"),
                    "confidence": m.get("confidence", 0.5),
                }
            )
            dp_idx[pid] = data_properties[-1]
            collector.add("info", "DATA_PROPERTY_SYNTHESIZED_FROM_MAPPING", "Synthesized data property from data_property_mapping.", path=f"data_properties[{pid}]", property_id=pid)
            continue

        if (not p.get("source_columns")) and mapped_cols:
            p["source_columns"] = mapped_cols
            collector.add("info", "DATA_PROPERTY_SOURCE_COLUMNS_BACKFILLED", "Backfilled source_columns from data_property_mapping.", path=f"data_properties[{pid}]", property_id=pid, source_columns=mapped_cols)
        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
            collector.add("info", "DATA_PROPERTY_DOMAIN_BACKFILLED", "Backfilled domain_class from data_property_mapping.", path=f"data_properties[{pid}]", property_id=pid, domain_class=p["domain_class"])
        if (not p.get("status")) and m.get("status"):
            p["status"] = m["status"]
        if p.get("confidence") is None and m.get("confidence") is not None:
            p["confidence"] = m["confidence"]

    if not object_property_mappings:
        for p in object_properties:
            pid = p.get("id")
            if not pid:
                continue
            joins = p.get("join_paths") or []
            object_property_mappings.append(
                {
                    "property_id": pid,
                    "from_class": p.get("domain_class"),
                    "to_class": p.get("range_class"),
                    "joins": joins,
                    "status": p.get("status", "proposed"),
                    "confidence": p.get("confidence", 0.5),
                }
            )
            collector.add("info", "OBJECT_PROPERTY_MAPPING_SYNTHESIZED_FROM_PROPERTY", "Synthesized object_property_mapping from object property definition.", path=f"object_property_mappings[{pid}]", property_id=pid)

    for m in object_property_mappings:
        pid = m.get("property_id")
        if not pid:
            continue
        p = op_idx.get(pid)
        joins = m.get("joins") or []

        if p is None:
            inferred_domain = m.get("from_class") or "Class:UNKNOWN"
            inferred_range = m.get("to_class") or "Class:UNKNOWN"
            inferred_label = pid.split(":", 1)[-1] if ":" in str(pid) else str(pid)
            object_properties.append(
                {
                    "id": pid,
                    "label": inferred_label,
                    "domain_class": inferred_domain,
                    "range_class": inferred_range,
                    "join_paths": joins,
                    "status": m.get("status", "proposed"),
                    "confidence": m.get("confidence", 0.5),
                }
            )
            op_idx[pid] = object_properties[-1]
            collector.add("info", "OBJECT_PROPERTY_SYNTHESIZED_FROM_MAPPING", "Synthesized object property from object_property_mapping.", path=f"object_properties[{pid}]", property_id=pid)
            continue

        if (not p.get("join_paths")) and joins:
            p["join_paths"] = joins
            collector.add("info", "OBJECT_PROPERTY_JOINS_BACKFILLED", "Backfilled join_paths from object_property_mapping.", path=f"object_properties[{pid}]", property_id=pid)
        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
            collector.add("info", "OBJECT_PROPERTY_DOMAIN_BACKFILLED", "Backfilled domain_class from object_property_mapping.", path=f"object_properties[{pid}]", property_id=pid)
        if (not p.get("range_class") or p.get("range_class") == "Class:UNKNOWN") and m.get("to_class"):
            p["range_class"] = m["to_class"]
            collector.add("info", "OBJECT_PROPERTY_RANGE_BACKFILLED", "Backfilled range_class from object_property_mapping.", path=f"object_properties[{pid}]", property_id=pid)
        if (not p.get("status")) and m.get("status"):
            p["status"] = m["status"]
        if p.get("confidence") is None and m.get("confidence") is not None:
            p["confidence"] = m["confidence"]

    canonical["classes"] = classes
    canonical["data_properties"] = data_properties
    canonical["object_properties"] = object_properties
    canonical["class_mappings"] = class_mappings
    canonical["data_property_mappings"] = data_property_mappings
    canonical["object_property_mappings"] = object_property_mappings
    return canonical


# ============================================================
# Contract check
# ============================================================


def _assert_canonical_shape(canonical: Dict[str, Any], collector: NormalizationCollector) -> None:
    required_top = {
        "classes",
        "data_properties",
        "object_properties",
        "subclass_relations",
        "class_mappings",
        "data_property_mappings",
        "object_property_mappings",
        "diagnostics",
    }
    for k in required_top:
        if k not in canonical:
            collector.add("error", "MISSING_TOP_LEVEL_KEY", f"Missing canonical top-level key: {k}", key=k)

    for i, rel in enumerate(canonical.get("subclass_relations", [])):
        if not rel.get("id") or not rel.get("child_class") or not rel.get("parent_class"):
            collector.add(
                "error",
                "BAD_SUBCLASS_RELATION",
                "Canonical subclass relation missing required fields.",
                path=f"subclass_relations[{i}]",
                relation=rel,
            )


# ============================================================
# Public entrypoint
# ============================================================


def normalize_model_output_robust(model_output: Dict[str, Any]) -> Dict[str, Any]:
    collector = NormalizationCollector()
    root = _find_root_payload(model_output, collector)

    canonical: Dict[str, Any] = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "diagnostics": {},
    }

    for i, x in enumerate(_as_list(root.get("classes"))):
        c = _canonicalize_class(x)
        if not c["id"]:
            collector.add("warning", "CLASS_MISSING_ID", "Dropped class without usable id.", path=f"classes[{i}]", raw=x)
            continue
        canonical["classes"].append(c)

    for i, x in enumerate(_as_list(root.get("data_properties") or root.get("datatype_properties"))):
        p = _canonicalize_data_property(x)
        if not p["id"]:
            collector.add("warning", "DATA_PROPERTY_MISSING_ID", "Dropped data property without usable id.", path=f"data_properties[{i}]", raw=x)
            continue
        canonical["data_properties"].append(p)

    for i, x in enumerate(_as_list(root.get("object_properties"))):
        p = _canonicalize_object_property(x)
        if not p["id"]:
            collector.add("warning", "OBJECT_PROPERTY_MISSING_ID", "Dropped object property without usable id.", path=f"object_properties[{i}]", raw=x)
            continue
        canonical["object_properties"].append(p)

    for i, rel in enumerate(_as_list(root.get("subclass_relations"))):
        canon_rel = _canonicalize_subclass_relation(rel)
        if not canon_rel["child_class"] or not canon_rel["parent_class"]:
            collector.add(
                "warning",
                "SUBCLASS_RELATION_INCOMPLETE",
                "Dropped incomplete subclass relation after canonicalization.",
                path=f"subclass_relations[{i}]",
                raw=rel,
                canonical=canon_rel,
            )
            continue
        canonical["subclass_relations"].append(canon_rel)

    for i, x in enumerate(_as_list(root.get("class_mappings"))):
        m = _canonicalize_class_mapping(x)
        if not m["class_id"]:
            collector.add("warning", "CLASS_MAPPING_MISSING_CLASS_ID", "Dropped class mapping without class_id.", path=f"class_mappings[{i}]", raw=x)
            continue
        canonical["class_mappings"].append(m)

    for i, x in enumerate(_as_list(root.get("data_property_mappings"))):
        m = _canonicalize_data_property_mapping(x)
        if not m["property_id"]:
            collector.add("warning", "DATA_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "Dropped data property mapping without property_id.", path=f"data_property_mappings[{i}]", raw=x)
            continue
        canonical["data_property_mappings"].append(m)

    for i, x in enumerate(_as_list(root.get("object_property_mappings"))):
        m = _canonicalize_object_property_mapping(x)
        if not m["property_id"]:
            collector.add("warning", "OBJECT_PROPERTY_MAPPING_MISSING_PROPERTY_ID", "Dropped object property mapping without property_id.", path=f"object_property_mappings[{i}]", raw=x)
            continue
        canonical["object_property_mappings"].append(m)

    canonical["diagnostics"] = _safe_dict(root.get("diagnostics"))
    canonical = _backfill_from_mappings(canonical, collector)
    _assert_canonical_shape(canonical, collector)
    canonical["normalization_report"] = collector.report()
    return canonical
