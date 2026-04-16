from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from rdflib import Graph, Literal
from rdflib.namespace import Namespace

D2RQ = Namespace("http://www.wiwiss.fu-berlin.de/suhl/bizer/D2RQ/0.1#")


def preprocess_gt_ttl(src: Path, dst: Path) -> Dict[str, Any]:
    """
    Representation-preserving GT TTL pre-processing.

    This intentionally avoids changing Burr semantics.
    It only normalizes surface forms that have already proven useful,
    especially uriPattern literal casing / placeholder formatting.
    """
    graph = Graph()
    graph.parse(src)

    num_uri_pattern_rewritten = 0
    replacements = []

    for s, p, o in list(graph.triples((None, D2RQ.uriPattern, None))):
        if not isinstance(o, Literal):
            continue

        old = str(o)
        new = old

        # Conservative normalization: keep semantics unchanged.
        if "#University" in new:
            new = new.replace("#University", "#university")
        if "#Department" in new:
            new = new.replace("#Department", "#department")
        if "#Institute" in new:
            new = new.replace("#Institute", "#institute")

        if new != old:
            graph.remove((s, p, o))
            graph.add((s, p, Literal(new)))
            num_uri_pattern_rewritten += 1
            replacements.append(
                {
                    "subject": str(s),
                    "predicate": str(p),
                    "old": old,
                    "new": new,
                }
            )

    dst.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(dst), format="turtle")

    return {
        "kind": "single_ttl",
        "ttl_preprocess_debug": {
            "num_uriPattern_rewritten": num_uri_pattern_rewritten,
            "replacements": replacements,
        },
    }