from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CompareArtifacts:
    gt_original: Path
    prediction_original: Path
    gt_preprocessed: Path
    prediction_preprocessed: Path


@dataclass
class CompareDebug:
    gt_preprocess: Dict[str, Any] = field(default_factory=dict)
    prediction_preprocess: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GTInfo:
    kind: str
    original_path: Path
    preprocessed_path: Optional[Path] = None
    meta_path: Optional[Path] = None
    debug: Dict[str, Any] = field(default_factory=dict)
