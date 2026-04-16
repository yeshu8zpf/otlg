from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional


def infer_database_name(scenario_dir: Path) -> str:
    return scenario_dir.name


def default_meta_path_for_scenario(scenario_dir: Path) -> Path:
    return scenario_dir / "meta.json"


def find_ttl_candidates(scenario_dir: Path) -> List[Path]:
    candidates: List[Path] = []
    for name in ["groundtruth.ttl", "test_mapping.ttl", "mapping.ttl"]:
        p = scenario_dir / name
        if p.exists():
            candidates.append(p)
    return candidates


def resolve_gt_ttl(scenario_dir: Path, explicit_gt: Optional[Path] = None) -> Path:
    if explicit_gt is not None:
        return explicit_gt
    candidates = find_ttl_candidates(scenario_dir)
    if not candidates:
        raise FileNotFoundError(f"No GT TTL found under {scenario_dir}")
    return candidates[0]


def merge_mapping_json_files(paths: Iterable[Path]) -> dict:
    merged = {
        "classes": [],
        "data_properties": [],
        "object_properties": [],
        "translation_tables": [],
    }
    for path in paths:
        import json
        obj = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        for key in merged:
            merged[key].extend(obj.get(key, []))
    return merged
