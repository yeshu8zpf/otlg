from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from .burr_imports import import_burr_modules
from .gt_resolution import (
    default_meta_path_for_scenario,
    infer_database_name,
    resolve_gt_ttl,
)
from .io_utils import read_json, write_json
from .meta import ensure_burr_meta
from .preprocess import preprocess_gt_json, preprocess_gt_ttl, preprocess_prediction_json
from .types import CompareConfig


def _read_meta(meta_path: Path) -> Dict[str, Any]:
    if not meta_path.exists():
        return ensure_burr_meta(None)
    return ensure_burr_meta(read_json(meta_path))


def run_compare(config: CompareConfig) -> Dict[str, Any]:
    JsonMapping, D2RQMapping, calculate_metrics = import_burr_modules(config.project_root)

    scenario_dir = config.scenario_dir
    meta_path = config.meta_path or default_meta_path_for_scenario(scenario_dir)
    meta = _read_meta(meta_path)
    database_name = infer_database_name(scenario_dir)

    temp_root = config.temp_dir or Path(tempfile.mkdtemp(prefix="burr_preprocess_"))
    temp_root.mkdir(parents=True, exist_ok=True)

    pred_preprocessed = temp_root / "prediction_preprocessed.json"
    pred_debug = preprocess_prediction_json(config.prediction_path, pred_preprocessed)

    if config.gt_kind == "ttl":
        gt_original = resolve_gt_ttl(scenario_dir, config.gt_path)
        gt_preprocessed = temp_root / "gt_preprocessed.ttl"
        gt_debug = preprocess_gt_ttl(gt_original, gt_preprocessed)
        gt_mapping = D2RQMapping(str(gt_preprocessed), database_name, meta)

    elif config.gt_kind == "json":
        gt_original = config.gt_path
        if gt_original is None:
            raise ValueError("gt_path is required when gt_kind='json'")
        gt_preprocessed = temp_root / "gt_preprocessed.json"
        gt_debug = preprocess_gt_json(gt_original, gt_preprocessed)
        gt_mapping = JsonMapping(read_json(gt_preprocessed), database_name, meta)

    else:
        raise ValueError(f"Unsupported gt_kind: {config.gt_kind}")

    pred_mapping = JsonMapping(read_json(pred_preprocessed), database_name, meta)

    mapping_based = calculate_metrics(
        gt_mapping,
        pred_mapping,
        equality_mode="mapping_based",
    )
    name_based = calculate_metrics(
        gt_mapping,
        pred_mapping,
        equality_mode="name_based",
    )

    result = {
        "mode": "burr_original_after_preprocess",
        "scenario_dir": str(scenario_dir),
        "database_name": database_name,
        "meta_path": str(meta_path),
        "effective_meta": meta,
        "gt_preprocess": {
            "original_path": str(gt_original),
            "preprocessed_path": str(gt_preprocessed),
            **gt_debug,
        },
        "prediction_preprocess": {
            "original_path": str(config.prediction_path),
            "preprocessed_path": str(pred_preprocessed),
            **pred_debug,
        },
        "metrics": {
            "mapping_based": mapping_based,
            "name_based": name_based,
        },
    }

    write_json(config.output_path, result)
    return result