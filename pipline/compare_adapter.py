from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    from compare.burr_compare import CompareConfig, run_compare
except Exception:
    CompareConfig = None
    run_compare = None


def run_burr_compare_wrapper(
    *,
    project_root: Path,
    scenario_dir: Path,
    prediction_path: Path,
    output_path: Path,
    gt_path: Optional[Path] = None,
    gt_kind: str = "ttl",
    meta_path: Optional[Path] = None,
    temp_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if CompareConfig is None or run_compare is None:
        raise RuntimeError("compare.burr_compare package is not importable")

    config = CompareConfig(
        project_root=project_root,
        scenario_dir=scenario_dir,
        prediction_path=prediction_path,
        output_path=output_path,
        gt_path=gt_path,
        gt_kind=gt_kind,
        meta_path=meta_path,
        temp_dir=temp_dir,
    )
    return run_compare(config)
