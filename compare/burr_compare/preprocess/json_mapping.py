from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from ..canonicalize import canonicalize_json_mapping
from ..io_utils import read_json, write_json


def _prediction_specific_rewrite(
    mapping: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = canonicalize_json_mapping(mapping)
    debug: Dict[str, Any] = {
        "kind": "prediction",
        "canonicalization_debug": out.get("_canonicalization_debug"),
    }
    return out, debug


def _gt_json_specific_rewrite(
    mapping: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = canonicalize_json_mapping(mapping)
    debug: Dict[str, Any] = {
        "kind": "gt_json",
        "canonicalization_debug": out.get("_canonicalization_debug"),
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