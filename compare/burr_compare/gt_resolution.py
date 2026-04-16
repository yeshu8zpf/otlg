from __future__ import annotations

from pathlib import Path
from typing import Optional


def default_meta_path_for_scenario(scenario_dir: Path) -> Path:
    return scenario_dir / "meta.json"


def infer_database_name(scenario_dir: Path) -> str:
    return scenario_dir.name


def resolve_gt_ttl(scenario_dir: Path, gt_path: Optional[Path] = None) -> Path:
    if gt_path is not None:
        if not gt_path.exists():
            raise FileNotFoundError(f"GT TTL not found: {gt_path}")
        return gt_path

    candidates = [
        scenario_dir / "groundtruth.ttl",
        scenario_dir / "mapping.ttl",
        scenario_dir / "test_mapping.ttl",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError(
        f"Could not find GT TTL under {scenario_dir}. "
        f"Tried: {[str(x) for x in candidates]}"
    )