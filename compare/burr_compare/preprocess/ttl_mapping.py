from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import Namespace

from ..canonicalize import normalize_uri_pattern
from ..io_utils import write_text


def preprocess_gt_ttl(src: Path, dst: Path) -> Dict[str, Any]:
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    d2rq = Namespace("http://www.wiwiss.fu-berlin.de/suhl/bizer/D2RQ/0.1#")
    uri_pred = URIRef(str(d2rq.uriPattern))

    g = Graph()
    g.parse(src.as_posix(), format="turtle")

    replacements: List[Dict[str, Any]] = []
    to_replace: List[Tuple[Any, Any, Literal, Literal]] = []

    for s, p, o in g.triples((None, uri_pred, None)):
        if not isinstance(o, Literal):
            continue

        old = str(o)
        new = normalize_uri_pattern(old, table_hint=None)

        if new != old:
            new_lit = Literal(new, lang=o.language, datatype=o.datatype)
            to_replace.append((s, p, o, new_lit))
            replacements.append(
                {
                    "subject": str(s),
                    "predicate": str(p),
                    "old": old,
                    "new": new,
                }
            )

    for s, p, old_o, new_o in to_replace:
        g.remove((s, p, old_o))
        g.add((s, p, new_o))

    serialized = g.serialize(format="turtle")
    if isinstance(serialized, bytes):
        serialized = serialized.decode("utf-8")

    write_text(dst, serialized)

    return {
        "kind": "single_ttl",
        "ttl_preprocess_debug": {
            "num_uriPattern_rewritten": len(replacements),
            "replacements": replacements,
        },
    }