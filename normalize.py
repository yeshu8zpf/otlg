from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple
import copy
import json
import re


# ============================================================
# Normalization report
# ============================================================

class NormalizationCollector:
    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []

    def add(
        self,
        level: str,
        code: str,
        message: str,
        path: Optional[str] = None,
        **payload: Any,
    ) -> None:
        self.messages.append(
            {
                "level": level,
                "code": code,
                "message": message,
                "path": path,
                "payload": payload,
            }
        )

    def summary(self) -> Dict[str, Any]:
        by_level: Dict[str, int] = {}
        by_code: Dict[str, int] = {}
        for m in self.messages:
            by_level[m["level"]] = by_level.get(m["level"], 0) + 1
            by_code[m["code"]] = by_code.get(m["code"], 0) + 1
        return {
            "ok": not any(m["level"] == "error" for m in self.messages),
            "num_messages": len(self.messages),
            "by_level": by_level,
            "by_code": by_code,
            "messages": self.messages,
        }


# ============================================================
# General helpers
# ============================================================

QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")
JOIN_RE = re.compile(r"^\s*(\S+)\s*(=|!=|<>|>=|<=|>|<)\s*(\S+)\s*$")


def _safe_dict(x: Any) -> Dict[str, Any]:
    return dict(x) if isinstance(x, dict) else {}


def _safe_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _dedup_keep_order(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in items:
        key = json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (dict, list)) else str(x)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    m = QUALIFIED_COL_RE.match((s or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _normalize_class_id(x: str) -> str:
    x = str(x or "").strip()
    if not x:
        return "Class:UNKNOWN"
    if x.startswith("Class:"):
        return x
    return f"Class:{x}"


def _normalize_data_property_id(domain_class: str, label: str) -> str:
    d = _normalize_class_id(domain_class).replace("Class:", "")
    label = str(label or "").strip() or "UNKNOWN"
    if label.startswith("DataProperty:"):
        return label
    return f"DataProperty:{d}.{label}"


def _normalize_object_property_id(domain_class: str, label: str) -> str:
    d = _normalize_class_id(domain_class).replace("Class:", "")
    label = str(label or "").strip() or "UNKNOWN"
    if label.startswith("ObjectProperty:"):
        return label
    return f"ObjectProperty:{d}.{label}"


def _normalize_xsd_type(x: Any) -> str:
    s = str(x or "").strip()
    if not s:
        return "string"

    s_low = s.lower()
    if s_low.startswith("xsd:"):
        s_low = s_low.split(":", 1)[1]

    mapping = {
        "string": "string",
        "text": "string",
        "str": "string",
        "integer": "integer",
        "int": "integer",
        "long": "integer",
        "float": "float",
        "double": "float",
        "decimal": "float",
        "bool": "boolean",
        "boolean": "boolean",
        "date": "date",
        "datetime": "datetime",
        "timestamp": "datetime",
        "literal": "string",
    }
    return mapping.get(s_low, s_low)


def _extract_identifier_columns_from_template(template: str) -> List[str]:
    template = str(template or "")
    cols: List[str] = []

    # Burr @@table.col@@
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

    # Python style {table.col}
    cols.extend(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}", template))

    # Looser fallback for {id} / {hotel_id} if from_tables known later
    return _dedup_keep_order([c for c in cols if c])


def _normalize_join_string(s: str) -> List[str]:
    s = str(s or "").strip()
    if not s:
        return []
    m = JOIN_RE.match(s)
    if m:
        return [m.group(1), m.group(2), m.group(3)]
    toks = s.split()
    return toks if toks else []


def _normalize_join_object(j: Dict[str, Any]) -> List[str]:
    j = _safe_dict(j)
    cond = str(j.get("join_condition", "")).strip()
    if cond:
        return _normalize_join_string(cond)

    left = j.get("left")
    op = j.get("op", "=")
    right = j.get("right")
    if left and right:
        return [str(left).strip(), str(op).strip(), str(right).strip()]

    return []


def _normalize_join_any(x: Any) -> List[str]:
    if isinstance(x, str):
        return _normalize_join_string(x)
    if isinstance(x, list):
        toks = [str(t).strip() for t in x if str(t).strip()]
        if len(toks) == 1:
            return _normalize_join_string(toks[0])
        return toks
    if isinstance(x, dict):
        return _normalize_join_object(x)
    return []


def _normalize_join_list(x: Any) -> List[List[str]]:
    out: List[List[str]] = []
    for item in _safe_list(x):
        j = _normalize_join_any(item)
        if j:
            out.append(j)
    return out


def _label_to_prop_fragment(label: str) -> str:
    s = str(label or "").strip()
    if not s:
        return "UNKNOWN"
    return s.replace(" ", "_")


def _pick_first_present(d: Dict[str, Any], keys: List[str]) -> Tuple[Any, Optional[str]]:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k], k
    return None, None


# ============================================================
# Canonical key alias tables
# ============================================================

CLASS_ALIASES = {
    "id": ["id", "class_id"],
    "label": ["label", "name", "class", "class_name", "concept"],
    "description": ["description", "comment", "definition"],
    "source_tables": ["source_tables", "tables", "from_tables"],
    "status": ["status"],
    "confidence": ["confidence", "score", "probability"],
}

DATA_PROPERTY_ALIASES = {
    "id": ["id", "data_property_id", "property_id"],
    "label": ["label", "property", "name"],
    "domain_class": ["domain_class", "domain", "belongsToClassMap", "applies_to_class", "from_class"],
    "range_type": ["range_type", "range", "type", "datatype"],
    "source_columns": ["source_columns", "columns"],
    "status": ["status"],
    "confidence": ["confidence", "score", "probability"],
    "description": ["description", "comment", "definition"],
}

OBJECT_PROPERTY_ALIASES = {
    "id": ["id", "object_property_id", "property_id"],
    "label": ["label", "property", "name"],
    "domain_class": ["domain_class", "domain", "belongsToClassMap", "from_class"],
    "range_class": ["range_class", "range", "refersToClassMap", "to_class"],
    "join_paths": ["join_paths", "joins", "join"],
    "status": ["status"],
    "confidence": ["confidence", "score", "probability"],
    "description": ["description", "comment", "definition"],
}

CLASS_MAPPING_ALIASES = {
    "class_id": ["class_id", "id", "class", "label", "name"],
    "instance_id_template": ["instance_id_template", "uri_template", "instance_uri_template", "id_template"],
    "from_tables": ["from_tables", "tables"],
    "where": ["where", "conditions", "filters"],
    "joins": ["joins", "join", "join_paths"],
    "identifier_columns": ["identifier_columns", "id_columns", "key_columns"],
}

DATA_PROPERTY_MAPPING_ALIASES = {
    "property_id": ["property_id", "data_property_id", "id"],
    "from_class": ["from_class", "applies_to_class", "domain_class", "belongsToClassMap"],
    "column": ["column"],
    "source_columns": ["source_columns", "columns"],
    "source_table": ["source_table"],
    "value_template": ["value_template"],
}

OBJECT_PROPERTY_MAPPING_ALIASES = {
    "property_id": ["property_id", "object_property_id", "id"],
    "from_class": ["from_class", "domain_class", "belongsToClassMap"],
    "to_class": ["to_class", "range_class", "refersToClassMap"],
    "joins": ["joins", "join", "join_paths"],
    "from_tables": ["from_tables", "tables"],
    "source_identifier_columns": ["source_identifier_columns"],
    "target_identifier_columns": ["target_identifier_columns"],
    "where": ["where", "conditions", "filters"],
}


# ============================================================
# Canonicalization helpers
# ============================================================

def _canonicalize_by_aliases(
    x: Dict[str, Any],
    aliases: Dict[str, List[str]],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    x = _safe_dict(x)
    out: Dict[str, Any] = {}
    used_keys = set()

    for canonical_key, alias_list in aliases.items():
        value, chosen = _pick_first_present(x, alias_list)
        if chosen is not None:
            out[canonical_key] = value
            used_keys.add(chosen)
            if chosen != canonical_key:
                collector.add(
                    "info",
                    "FIELD_ALIAS_CANONICALIZED",
                    f"Canonicalized field '{chosen}' to '{canonical_key}'.",
                    path=path,
                    from_key=chosen,
                    to_key=canonical_key,
                )

    extras = {k: v for k, v in x.items() if k not in used_keys}
    if extras:
        out["extras"] = extras
        collector.add(
            "info",
            "EXTRA_FIELDS_PRESERVED",
            "Preserved non-canonical fields in extras.",
            path=path,
            extra_keys=sorted(extras.keys()),
        )

    return out


# ============================================================
# Per-section robust normalization
# ============================================================

def _normalize_class_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, CLASS_ALIASES, collector, path)

    label = str(out.get("label") or "UNKNOWN").strip()
    out["label"] = label
    out["id"] = _normalize_class_id(out.get("id") or label)
    out["source_tables"] = [str(t).strip() for t in _safe_list(out.get("source_tables")) if str(t).strip()]
    out["status"] = str(out.get("status") or "accepted")
    if "confidence" in out and out["confidence"] is not None:
        try:
            out["confidence"] = float(out["confidence"])
        except Exception:
            collector.add("warning", "BAD_CONFIDENCE", "Failed to cast class confidence to float.", path=path, value=out["confidence"])
            out["confidence"] = None
    return out


def _normalize_data_property_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, DATA_PROPERTY_ALIASES, collector, path)

    label = str(out.get("label") or "UNKNOWN").strip()
    domain_class = _normalize_class_id(out.get("domain_class") or "UNKNOWN")
    range_type = _normalize_xsd_type(out.get("range_type"))

    out["label"] = label
    out["domain_class"] = domain_class
    out["range_type"] = range_type
    out["source_columns"] = [str(c).strip() for c in _safe_list(out.get("source_columns")) if str(c).strip()]
    out["status"] = str(out.get("status") or "accepted")
    out["id"] = out.get("id") or _normalize_data_property_id(domain_class, _label_to_prop_fragment(label))

    if "confidence" in out and out["confidence"] is not None:
        try:
            out["confidence"] = float(out["confidence"])
        except Exception:
            collector.add("warning", "BAD_CONFIDENCE", "Failed to cast data property confidence to float.", path=path, value=out["confidence"])
            out["confidence"] = None

    return out


def _normalize_object_property_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, OBJECT_PROPERTY_ALIASES, collector, path)

    label = str(out.get("label") or "UNKNOWN").strip()
    domain_class = _normalize_class_id(out.get("domain_class") or "UNKNOWN")
    range_class = _normalize_class_id(out.get("range_class") or "UNKNOWN")

    out["label"] = label
    out["domain_class"] = domain_class
    out["range_class"] = range_class
    out["join_paths"] = _normalize_join_list(out.get("join_paths"))
    out["status"] = str(out.get("status") or "accepted")
    out["reified"] = bool(out.get("reified", False))
    out["id"] = out.get("id") or _normalize_object_property_id(domain_class, _label_to_prop_fragment(label))

    if "confidence" in out and out["confidence"] is not None:
        try:
            out["confidence"] = float(out["confidence"])
        except Exception:
            collector.add("warning", "BAD_CONFIDENCE", "Failed to cast object property confidence to float.", path=path, value=out["confidence"])
            out["confidence"] = None

    return out


def _normalize_class_mapping_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, CLASS_MAPPING_ALIASES, collector, path)

    class_id_raw = out.get("class_id")
    instance_id_template = str(out.get("instance_id_template") or "").strip()

    if class_id_raw:
        if str(class_id_raw).startswith("Class:"):
            out["class_id"] = class_id_raw
        else:
            # here class_id may be label-like
            out["class_id"] = _normalize_class_id(class_id_raw)
    else:
        out["class_id"] = "Class:UNKNOWN"
        collector.add("warning", "CLASS_MAPPING_CLASS_ID_UNKNOWN", "Could not infer class_id.", path=path)

    out["instance_id_template"] = instance_id_template
    out["from_tables"] = [str(t).strip() for t in _safe_list(out.get("from_tables")) if str(t).strip()]
    out["where"] = [str(w).strip() for w in _safe_list(out.get("where")) if str(w).strip()]
    out["joins"] = _normalize_join_list(out.get("joins"))

    identifier_columns = [str(c).strip() for c in _safe_list(out.get("identifier_columns")) if str(c).strip()]
    if not identifier_columns and instance_id_template:
        identifier_columns = _extract_identifier_columns_from_template(instance_id_template)
        if identifier_columns:
            collector.add(
                "info",
                "IDENTIFIER_COLUMNS_INFERRED_FROM_TEMPLATE",
                "Inferred identifier_columns from instance_id_template.",
                path=path,
                identifier_columns=identifier_columns,
            )

    # fallback for {id} / {room_number} style templates if from_tables has exactly one table
    if not identifier_columns and instance_id_template and len(out["from_tables"]) == 1:
        table = out["from_tables"][0]
        bare = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", instance_id_template)
        if bare:
            identifier_columns = [f"{table}.{b}" for b in bare]
            collector.add(
                "warning",
                "IDENTIFIER_COLUMNS_WEAKLY_INFERRED",
                "Weakly inferred identifier_columns from bare template placeholders and single from_table.",
                path=path,
                identifier_columns=identifier_columns,
            )

    out["identifier_columns"] = identifier_columns
    return out


def _normalize_data_property_mapping_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, DATA_PROPERTY_MAPPING_ALIASES, collector, path)

    property_id = out.get("property_id") or "DataProperty:UNKNOWN.UNKNOWN"
    from_class = _normalize_class_id(out.get("from_class") or "UNKNOWN")

    column = str(out.get("column") or "").strip()
    source_columns = [str(c).strip() for c in _safe_list(out.get("source_columns")) if str(c).strip()]
    source_table = str(out.get("source_table") or "").strip()

    if not column and source_columns:
        column = source_columns[0]
        collector.add("info", "COLUMN_FROM_SOURCE_COLUMNS", "Filled column from source_columns[0].", path=path, column=column)

    if not column and source_table and out.get("value_template"):
        bare = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", str(out["value_template"]))
        if len(bare) == 1:
            column = f"{source_table}.{bare[0]}"
            collector.add(
                "warning",
                "COLUMN_WEAKLY_INFERRED",
                "Weakly inferred column from source_table + value_template.",
                path=path,
                column=column,
            )

    out["property_id"] = property_id
    out["from_class"] = from_class
    out["column"] = column
    return out


def _normalize_object_property_mapping_entry(
    x: Dict[str, Any],
    collector: NormalizationCollector,
    path: str,
) -> Dict[str, Any]:
    out = _canonicalize_by_aliases(x, OBJECT_PROPERTY_MAPPING_ALIASES, collector, path)

    out["property_id"] = out.get("property_id") or "ObjectProperty:UNKNOWN.UNKNOWN"
    out["from_class"] = _normalize_class_id(out.get("from_class") or "UNKNOWN")
    out["to_class"] = _normalize_class_id(out.get("to_class") or "UNKNOWN")
    out["joins"] = _normalize_join_list(out.get("joins"))
    out["from_tables"] = [str(t).strip() for t in _safe_list(out.get("from_tables")) if str(t).strip()]
    out["source_identifier_columns"] = [str(c).strip() for c in _safe_list(out.get("source_identifier_columns")) if str(c).strip()]
    out["target_identifier_columns"] = [str(c).strip() for c in _safe_list(out.get("target_identifier_columns")) if str(c).strip()]
    out["where"] = [str(w).strip() for w in _safe_list(out.get("where")) if str(w).strip()]
    return out


# ============================================================
# Cross-layer backfilling
# ============================================================

def _build_index_by_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for x in items:
        xid = x.get("id")
        if xid:
            out[xid] = x
    return out


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

    # --------------------------------------------------------
    # 1) Backfill class mappings from classes if missing
    # --------------------------------------------------------
    if not class_mappings:
        for c in classes:
            source_tables = c.get("source_tables") or []
            if not source_tables:
                continue

            cid = c.get("id")
            if not cid:
                continue

            from_tables = [str(t).strip() for t in source_tables if str(t).strip()]
            identifier_columns = [str(x).strip() for x in (c.get("identifier_columns") or []) if str(x).strip()]

            class_mappings.append(
                {
                    "class_id": cid,
                    "from_tables": from_tables,
                    "identifier_columns": identifier_columns,
                    "instance_id_template": c.get("instance_id_template") or (
                        "{"
                        + (identifier_columns[0] if identifier_columns else f"{from_tables[0]}.id")
                        + "}"
                    ),
                    "status": c.get("status", "proposed"),
                    "confidence": c.get("confidence", 0.5),
                }
            )
            collector.add(
                "info",
                "CLASS_MAPPING_SYNTHESIZED_FROM_CLASS",
                "Synthesized class mapping from class definition.",
                path=f"class_mappings[{cid}]",
                class_id=cid,
            )

    # Repair existing classes from class mappings
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
            collector.add(
                "info",
                "CLASS_SOURCE_TABLES_BACKFILLED_FROM_MAPPING",
                "Backfilled source_tables from class_mapping.",
                path=f"classes[{cid}]",
                class_id=cid,
                source_tables=mapped_tables,
            )

        if (not c.get("identifier_columns")) and mapped_ids:
            c["identifier_columns"] = mapped_ids
            collector.add(
                "info",
                "CLASS_IDENTIFIER_COLUMNS_BACKFILLED",
                "Backfilled identifier_columns from class_mapping.",
                path=f"classes[{cid}]",
                class_id=cid,
                identifier_columns=mapped_ids,
            )

        if (not c.get("instance_id_template")) and m.get("instance_id_template"):
            c["instance_id_template"] = m["instance_id_template"]
            collector.add(
                "info",
                "CLASS_INSTANCE_TEMPLATE_BACKFILLED",
                "Backfilled instance_id_template from class_mapping.",
                path=f"classes[{cid}]",
                class_id=cid,
                instance_id_template=m["instance_id_template"],
            )

    # --------------------------------------------------------
    # 2) Backfill data property mappings from data properties if missing
    # --------------------------------------------------------
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
            collector.add(
                "info",
                "DATA_PROPERTY_MAPPING_SYNTHESIZED_FROM_PROPERTY",
                "Synthesized data_property_mapping from data property definition.",
                path=f"data_property_mappings[{pid}]",
                property_id=pid,
            )

    # Repair existing data properties from mappings
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
            collector.add(
                "info",
                "DATA_PROPERTY_SYNTHESIZED_FROM_MAPPING",
                "Synthesized data property from data_property_mapping.",
                path=f"data_properties[{pid}]",
                property_id=pid,
            )
            continue

        if (not p.get("source_columns")) and mapped_cols:
            p["source_columns"] = mapped_cols
            collector.add(
                "info",
                "DATA_PROPERTY_SOURCE_COLUMNS_BACKFILLED",
                "Backfilled source_columns from data_property_mapping.",
                path=f"data_properties[{pid}]",
                property_id=pid,
                source_columns=mapped_cols,
            )

        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
            collector.add(
                "info",
                "DATA_PROPERTY_DOMAIN_BACKFILLED",
                "Backfilled domain_class from data_property_mapping.",
                path=f"data_properties[{pid}]",
                property_id=pid,
                domain_class=p["domain_class"],
            )

        if (not p.get("status")) and m.get("status"):
            p["status"] = m["status"]

        if p.get("confidence") is None and m.get("confidence") is not None:
            p["confidence"] = m["confidence"]

    # --------------------------------------------------------
    # 3) Backfill object property mappings from object properties if missing
    # --------------------------------------------------------
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
            collector.add(
                "info",
                "OBJECT_PROPERTY_MAPPING_SYNTHESIZED_FROM_PROPERTY",
                "Synthesized object_property_mapping from object property definition.",
                path=f"object_property_mappings[{pid}]",
                property_id=pid,
            )

    # Repair existing object properties from mappings
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
            collector.add(
                "info",
                "OBJECT_PROPERTY_SYNTHESIZED_FROM_MAPPING",
                "Synthesized object property from object_property_mapping.",
                path=f"object_properties[{pid}]",
                property_id=pid,
            )
            continue

        if (not p.get("join_paths")) and joins:
            p["join_paths"] = joins
            collector.add(
                "info",
                "OBJECT_PROPERTY_JOINS_BACKFILLED",
                "Backfilled join_paths from object_property_mapping.",
                path=f"object_properties[{pid}]",
                property_id=pid,
            )

        if (not p.get("domain_class") or p.get("domain_class") == "Class:UNKNOWN") and m.get("from_class"):
            p["domain_class"] = m["from_class"]
            collector.add(
                "info",
                "OBJECT_PROPERTY_DOMAIN_BACKFILLED",
                "Backfilled domain_class from object_property_mapping.",
                path=f"object_properties[{pid}]",
                property_id=pid,
            )

        if (not p.get("range_class") or p.get("range_class") == "Class:UNKNOWN") and m.get("to_class"):
            p["range_class"] = m["to_class"]
            collector.add(
                "info",
                "OBJECT_PROPERTY_RANGE_BACKFILLED",
                "Backfilled range_class from object_property_mapping.",
                path=f"object_properties[{pid}]",
                property_id=pid,
            )

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
# Public robust normalization API
# ============================================================

def normalize_model_output_robust(obj: Dict[str, Any]) -> Dict[str, Any]:
    collector = NormalizationCollector()
    root = copy.deepcopy(_safe_dict(obj))

    top_level_defaults = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": [],
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "diagnostics": {},
        "extras": {},
    }

    for k, default in top_level_defaults.items():
        if k not in root or root[k] is None:
            root[k] = copy.deepcopy(default)
            collector.add("info", "TOP_LEVEL_DEFAULT_INSERTED", f"Inserted missing top-level key '{k}'.", path=k)

    canonical = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "subclass_relations": _safe_list(root.get("subclass_relations")),
        "class_mappings": [],
        "data_property_mappings": [],
        "object_property_mappings": [],
        "diagnostics": _safe_dict(root.get("diagnostics")),
        "extras": _safe_dict(root.get("extras")),
    }

    for i, x in enumerate(_safe_list(root.get("classes"))):
        canonical["classes"].append(_normalize_class_entry(x, collector, f"classes[{i}]"))

    for i, x in enumerate(_safe_list(root.get("data_properties"))):
        canonical["data_properties"].append(_normalize_data_property_entry(x, collector, f"data_properties[{i}]"))

    for i, x in enumerate(_safe_list(root.get("object_properties"))):
        canonical["object_properties"].append(_normalize_object_property_entry(x, collector, f"object_properties[{i}]"))

    for i, x in enumerate(_safe_list(root.get("class_mappings"))):
        canonical["class_mappings"].append(_normalize_class_mapping_entry(x, collector, f"class_mappings[{i}]"))

    for i, x in enumerate(_safe_list(root.get("data_property_mappings"))):
        canonical["data_property_mappings"].append(_normalize_data_property_mapping_entry(x, collector, f"data_property_mappings[{i}]"))

    for i, x in enumerate(_safe_list(root.get("object_property_mappings"))):
        canonical["object_property_mappings"].append(_normalize_object_property_mapping_entry(x, collector, f"object_property_mappings[{i}]"))

    canonical = _backfill_from_mappings(canonical, collector)

    # preserve unknown top-level keys
    known_top_level = set(top_level_defaults.keys())
    extra_top_level = {k: v for k, v in root.items() if k not in known_top_level}
    if extra_top_level:
        canonical["extras"]["unknown_top_level_keys"] = extra_top_level
        collector.add(
            "info",
            "UNKNOWN_TOP_LEVEL_KEYS_PRESERVED",
            "Preserved unknown top-level keys in extras.unknown_top_level_keys.",
            path="root",
            keys=sorted(extra_top_level.keys()),
        )

    canonical["extras"]["normalization_report"] = collector.summary()
    return canonical