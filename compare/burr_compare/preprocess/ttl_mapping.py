from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import Namespace

from ..canonicalize import (
    normalize_column_expr,
    normalize_join_expr,
    normalize_uri_pattern,
)
from ..io_utils import write_text


D2RQ = Namespace("http://www.wiwiss.fu-berlin.de/suhl/bizer/D2RQ/0.1#")


def _split_csv_columns(value: str) -> List[str]:
    parts = []
    for x in str(value).split(","):
        x = x.strip()
        if x:
            parts.append(x)
    return parts


def _normalize_bnode_id_columns(value: str) -> str:
    cols = _split_csv_columns(value)
    normed = [normalize_column_expr(c) for c in cols if str(c).strip()]
    return ", ".join(normed)


def _normalize_pattern_literal(value: str) -> str:
    # For compare-view purposes, we reuse uri-pattern style placeholder normalization.
    # This keeps @@table.col@@ / {table.col} forms aligned across GT/prediction.
    return normalize_uri_pattern(value, table_hint=None)


def _normalize_uri_column_literal(value: str) -> str:
    return normalize_column_expr(value)


def _normalize_datatype_literal(value: str) -> str:
    # Be conservative: do not lower-case full URIs blindly.
    # Just normalize whitespace.
    return re.sub(r"\s+", " ", str(value).strip())


def _normalize_translate_with_literal(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def _normalize_condition_literal(value: str) -> str:
    """
    Normalize table.column references and whitespace while preserving quoted constants.
    Example:
      organizations.type = 'U'   -> organizations.type = 'U'
      PERSONS.EMAIL='A@B'        -> persons.email = 'A@B'
    """
    text = str(value).strip()

    # Normalize qualified column names outside quotes
    def repl_qualified(m: re.Match[str]) -> str:
        table = m.group(1).lower()
        col = m.group(2).lower()
        return f"{table}.{col}"

    # Split by single-quoted / double-quoted segments so we don't lowercase constants
    parts = re.split(r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")", text)
    normalized_parts: List[str] = []

    for i, part in enumerate(parts):
        if i % 2 == 1:
            # quoted literal, keep as-is
            normalized_parts.append(part)
        else:
            # outside quotes: normalize qualified columns and whitespace
            part = re.sub(
                r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b",
                repl_qualified,
                part,
            )
            part = re.sub(r"\s*(=|!=|<>|>=|<=|>|<)\s*", r" \1 ", part)
            part = re.sub(r"\s+", " ", part).strip()
            normalized_parts.append(part)

    return "".join(normalized_parts).strip()


def _literal_with_same_meta(old: Literal, new_text: str) -> Literal:
    return Literal(new_text, lang=old.language, datatype=old.datatype)


def preprocess_gt_ttl(src: Path, dst: Path) -> Dict[str, Any]:
    """
    Compare-view GT TTL preprocessing.

    Goals:
    - Keep Burr evaluator unchanged.
    - Normalize surface representation of GT TTL fields that affect matching.
    - For fields Burr does not fully consume (notably uriColumn), add a compatible
      mirror predicate so compare can still use the information.
    """
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    g = Graph()
    g.parse(src.as_posix(), format="turtle")

    replacements: List[Dict[str, Any]] = []
    additions: List[Dict[str, Any]] = []

    uri_pattern_pred = URIRef(str(D2RQ.uriPattern))
    pattern_pred = URIRef(str(D2RQ.pattern))
    uri_column_pred = URIRef(str(D2RQ.uriColumn))
    column_pred = URIRef(str(D2RQ.column))
    condition_pred = URIRef(str(D2RQ.condition))
    datatype_pred = URIRef(str(D2RQ.datatype))
    bnode_id_cols_pred = URIRef(str(D2RQ.bNodeIdColumns))
    join_pred = URIRef(str(D2RQ.join))
    translate_with_pred = URIRef(str(D2RQ.translateWith))
    additional_class_def_prop_pred = URIRef(str(D2RQ.additionalClassDefinitionProperty))

    # 1) Normalize uriPattern
    for s, p, o in list(g.triples((None, uri_pattern_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = normalize_uri_pattern(old, table_hint=None)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 2) Normalize pattern
    for s, p, o in list(g.triples((None, pattern_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = _normalize_pattern_literal(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 3) Normalize uriColumn and mirror -> column for Burr compare compatibility
    for s, p, o in list(g.triples((None, uri_column_pred, None))):
        if not isinstance(o, Literal):
            continue

        old = str(o)
        new = _normalize_uri_column_literal(old)

        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )
        else:
            new_lit = o

        # Mirror uriColumn -> column if no column already exists on this bridge
        has_column = any(True for _ in g.triples((s, column_pred, None)))
        if not has_column:
            mirrored = Literal(str(new_lit), lang=new_lit.language, datatype=new_lit.datatype)
            g.add((s, column_pred, mirrored))
            additions.append(
                {
                    "subject": str(s),
                    "predicate": str(column_pred),
                    "derived_from": str(uri_column_pred),
                    "value": str(mirrored),
                }
            )

    # 4) Normalize column literals too, if present
    for s, p, o in list(g.triples((None, column_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = normalize_column_expr(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 5) Normalize bNodeIdColumns
    for s, p, o in list(g.triples((None, bnode_id_cols_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = _normalize_bnode_id_columns(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 6) Normalize joins
    for s, p, o in list(g.triples((None, join_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = normalize_join_expr(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 7) Normalize conditions conservatively
    for s, p, o in list(g.triples((None, condition_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = _normalize_condition_literal(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 8) Normalize datatype literals conservatively
    for s, p, o in list(g.triples((None, datatype_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = _normalize_datatype_literal(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 9) Normalize translateWith
    for s, p, o in list(g.triples((None, translate_with_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = _normalize_translate_with_literal(old)
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    # 10) Normalize additionalClassDefinitionProperty conservatively
    for s, p, o in list(g.triples((None, additional_class_def_prop_pred, None))):
        if not isinstance(o, Literal):
            continue
        old = str(o)
        new = re.sub(r"\s+", " ", old.strip())
        if new != old:
            new_lit = _literal_with_same_meta(o, new)
            g.remove((s, p, o))
            g.add((s, p, new_lit))
            replacements.append(
                {"subject": str(s), "predicate": str(p), "old": old, "new": new}
            )

    serialized = g.serialize(format="turtle")
    if isinstance(serialized, bytes):
        serialized = serialized.decode("utf-8")

    write_text(dst, serialized)

    return {
        "kind": "single_ttl",
        "ttl_preprocess_debug": {
            "num_replacements": len(replacements),
            "num_additions": len(additions),
            "replacements": replacements,
            "additions": additions,
        },
    }