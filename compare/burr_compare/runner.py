from __future__ import annotations

import json
import shutil
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .gt_resolution import (
    default_meta_path_for_scenario,
    infer_database_name,
    resolve_gt_ttl,
)


@dataclass
class CompareConfig:
    project_root: Path
    scenario_dir: Path
    prediction_path: Path
    output_path: Path
    gt_path: Optional[Path] = None
    gt_kind: str = "ttl"
    meta_path: Optional[Path] = None
    temp_dir: Optional[Path] = None


def ensure_wandb_stub() -> None:
    """
    Burr evaluator imports wandb in some modules.
    If wandb is unavailable, inject a minimal stub so we do not need
    to modify Burr source code or install wandb just for local compare.
    """
    try:
        import wandb  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    if "wandb" in sys.modules:
        return

    wandb_stub = types.ModuleType("wandb")

    def _noop(*args, **kwargs):
        return None

    wandb_stub.init = _noop
    wandb_stub.log = _noop
    wandb_stub.finish = _noop
    wandb_stub.login = _noop
    wandb_stub.watch = _noop
    wandb_stub.config = {}

    sys.modules["wandb"] = wandb_stub


def import_burr_modules(project_root: Path) -> Tuple[object, object, object]:
    """
    Import Burr evaluator modules from local project checkout.
    Returns:
        MappingParserClass, calculate_metrics function, CanonicalMapping class
    """
    project_root = Path(project_root).resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    ensure_wandb_stub()

    from burr_evaluator.mapping_parser.mapping.MappingParser import MappingParser
    from burr_evaluator.metrics.caclulate_metrics import calculate_metrics
    from burr_evaluator.mapping_parser.mapping.Mapping import Mapping

    return MappingParser, calculate_metrics, Mapping


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def ensure_burr_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    meta = dict(meta or {})
    meta.setdefault("database", "unknown")
    meta.setdefault("concepts", [])
    meta.setdefault("relations", [])
    meta.setdefault("attributes", [])
    return meta



def preprocess_prediction_json(src: Path, dst: Path) -> Dict[str, Any]:
    """
    For now, prediction json is already in the expected format.
    Copy it to a temp location so the pipeline is uniform.
    """
    obj = read_json(src)
    write_json(dst, obj)
    return {
        "kind": "prediction_json",
        "src": str(src),
        "dst": str(dst),
        "top_level_keys": list(obj.keys()) if isinstance(obj, dict) else None,
    }


def preprocess_gt_json(src: Path, dst: Path) -> Dict[str, Any]:
    """
    GT json has already been merged if needed outside this function.
    Just copy it to temp.
    """
    obj = read_json(src)
    write_json(dst, obj)
    return {
        "kind": "gt_json",
        "src": str(src),
        "dst": str(dst),
        "top_level_keys": list(obj.keys()) if isinstance(obj, dict) else None,
    }


def preprocess_gt_ttl(src: Path, dst: Path) -> Dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "kind": "gt_ttl",
        "src": str(src),
        "dst": str(dst),
    }


def _normalize_metrics_output(raw_metrics: Any) -> Dict[str, Any]:
    """
    Burr's calculate_metrics may return either:
      1) {
           "mapping_based": {...},
           "name_based": {...}
         }
      2) a single flat metric dict
    Normalize to a predictable dict.
    """
    if isinstance(raw_metrics, dict):
        if "mapping_based" in raw_metrics or "name_based" in raw_metrics:
            out: Dict[str, Any] = {}
            if "mapping_based" in raw_metrics:
                out["mapping_based"] = raw_metrics["mapping_based"]
            if "name_based" in raw_metrics:
                out["name_based"] = raw_metrics["name_based"]
            return out

        return {"default": raw_metrics}

    return {"default": raw_metrics}


def run_compare(config: CompareConfig) -> Dict[str, Any]:
    project_root = Path(config.project_root).resolve()
    scenario_dir = Path(config.scenario_dir).resolve()
    prediction_path = Path(config.prediction_path).resolve()
    output_path = Path(config.output_path).resolve()

    if not prediction_path.exists():
        raise FileNotFoundError(f"Prediction file not found: {prediction_path}")
    if not scenario_dir.exists():
        raise FileNotFoundError(f"Scenario dir not found: {scenario_dir}")

    meta_path = (
        Path(config.meta_path).resolve()
        if config.meta_path is not None
        else default_meta_path_for_scenario(scenario_dir).resolve()
    )

    temp_dir = (
        Path(config.temp_dir).resolve()
        if config.temp_dir is not None
        else output_path.parent / f"{output_path.stem}_tmp"
    )
    temp_dir.mkdir(parents=True, exist_ok=True)

    pred_preprocessed = temp_dir / "prediction.preprocessed.json"
    gt_preprocessed = (
        temp_dir / "gt.preprocessed.ttl"
        if config.gt_kind == "ttl"
        else temp_dir / "gt.preprocessed.json"
    )

    pred_meta = preprocess_prediction_json(prediction_path, pred_preprocessed)

    if config.gt_kind == "ttl":
        gt_src = (
            Path(config.gt_path).resolve()
            if config.gt_path is not None
            else resolve_gt_ttl(scenario_dir)
        )
        gt_meta = preprocess_gt_ttl(gt_src, gt_preprocessed)
    elif config.gt_kind == "json":
        if config.gt_path is None:
            raise ValueError("gt_path must be provided when gt_kind='json'")
        gt_src = Path(config.gt_path).resolve()
        if not gt_src.exists():
            raise FileNotFoundError(f"GT json not found: {gt_src}")
        gt_meta = preprocess_gt_json(gt_src, gt_preprocessed)
    else:
        raise ValueError(f"Unsupported gt_kind: {config.gt_kind}")

    MappingParser, calculate_metrics, Mapping = import_burr_modules(project_root)

    meta = {}
    if meta_path.exists():
        try:
            meta = read_json(meta_path)
        except Exception:
            meta = {}
    meta = ensure_burr_meta(meta)
    meta.setdefault("database", infer_database_name(scenario_dir))

    gt_mapping = MappingParser.parse_from_file(str(gt_preprocessed), meta)
    pred_mapping = MappingParser.parse_from_file(str(pred_preprocessed), meta)

    raw_metrics = calculate_metrics(gt_mapping, pred_mapping)
    metrics = _normalize_metrics_output(raw_metrics)

    result = {
        "scenario_dir": str(scenario_dir),
        "prediction_path": str(prediction_path),
        "gt_path": str(gt_src),
        "gt_kind": config.gt_kind,
        "meta_path": str(meta_path) if meta_path else None,
        "preprocess": {
            "prediction": pred_meta,
            "gt": gt_meta,
        },
        "metrics": metrics,
    }

    write_json(output_path, result)
    return result