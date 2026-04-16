from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..io_utils import read_json, write_json

_PLACEHOLDER_RE = re.compile(r"@@\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*@@")


def _normalize_placeholder(text: str) -> str:
    return _PLACEHOLDER_RE.sub(lambda m: f"@@{m.group(1).lower()}.{m.group(2).lower()}@@", text)


def _normalize_string_fields(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _normalize_string_fields(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_normalize_string_fields(x) for x in node]
    if isinstance(node, str):
        return _normalize_placeholder(node)
    return node


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _prediction_specific_rewrite(mapping: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Hook for prediction-side compare-view rewrite.

    Conservative by default: only normalizes placeholder/casing and keeps structure.
    You can extend this function with scenario-specific rules, e.g.:
    - synthesize pattern-based attributes
    - emit bNodeIdColumns for blank-node classes
    - rewrite URI-valued columns to Burr-friendly entries supported by your local chain
    """
    out = copy.deepcopy(mapping)
    out = _normalize_string_fields(out)
    debug = {
        "kind": "prediction",
        "rewrites": [],
    }
    return out, debug


def _gt_json_specific_rewrite(mapping: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Hook for GT JSON pre-processing.

    Only use representation-preserving rewrites here.
    """
    out = copy.deepcopy(mapping)
    out = _normalize_string_fields(out)
    debug = {
        "kind": "gt_json",
        "rewrites": [],
    }
    return out, debug


def preprocess_prediction_json(src: Path, dst: Path) -> Dict[str, Any]:
    mapping = read_json(src)
    fixed, debug = _prediction_specific_rewrite(mapping)
    write_json(dst, fixed)
    return debug


def preprocess_gt_json(src: Path, dst: Path) -> Dict[str, Any]:
    mapping = read_json(src)
    fixed, debug = _gt_json_specific_rewrite(mapping)
    write_json(dst, fixed)
    return debug
