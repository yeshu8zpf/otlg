from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CompareConfig:
    project_root: Path
    scenario_dir: Path
    prediction_path: Path
    output_path: Path
    gt_path: Optional[Path] = None
    gt_kind: str = "ttl"  # ttl | json
    meta_path: Optional[Path] = None
    temp_dir: Optional[Path] = None