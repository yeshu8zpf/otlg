from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .io_utils import maybe_copy


def resolve_gt_artifacts_for_scenario(scenario_dir: Path) -> Dict[str, Any]:
    direct_mapping = scenario_dir / "mapping.json"
    mappings_dir = scenario_dir / "mappings"
    meta_json = scenario_dir / "meta.json"

    result: Dict[str, Any] = {
        "kind": "missing",
        "mapping_json": None,
        "mappings_dir": None,
        "meta_json": str(meta_json) if meta_json.exists() and meta_json.is_file() else None,
        "extra_files": [],
    }

    if direct_mapping.exists() and direct_mapping.is_file():
        extras: List[str] = []
        for name in ["mapping.ttl", "test_mapping.ttl", "groundtruth.ttl", "map_d2rq.ttl"]:
            p = scenario_dir / name
            if p.exists() and p.is_file():
                extras.append(str(p))

        result["kind"] = "single_json"
        result["mapping_json"] = str(direct_mapping)
        result["extra_files"] = extras
        return result

    if mappings_dir.exists() and mappings_dir.is_dir():
        result["kind"] = "mapping_dir"
        result["mappings_dir"] = str(mappings_dir)
        result["extra_files"] = sorted(
            [str(p) for p in mappings_dir.iterdir() if p.is_file()],
            key=lambda x: x,
        )
        return result

    return result


def copy_gt_artifacts_for_scenario(scenario_dir: Path, out_dir: Path) -> Dict[str, Any]:
    gt_info = resolve_gt_artifacts_for_scenario(scenario_dir)
    copied: List[str] = []

    if gt_info["kind"] == "single_json":
        dst = out_dir / "gt.mapping.json"
        maybe_copy(gt_info["mapping_json"], dst)
        copied.append(str(dst))
        for p in gt_info["extra_files"]:
            p_path = Path(p)
            dst_extra = out_dir / f"gt.{p_path.name}"
            maybe_copy(p_path, dst_extra)
            copied.append(str(dst_extra))

    elif gt_info["kind"] == "mapping_dir":
        dst_dir = out_dir / "gt.mappings"
        dst_dir.mkdir(parents=True, exist_ok=True)
        for p in gt_info["extra_files"]:
            p_path = Path(p)
            dst = dst_dir / p_path.name
            maybe_copy(p_path, dst)
            copied.append(str(dst))

    if gt_info["meta_json"] is not None:
        dst_meta = out_dir / "gt.meta.json"
        maybe_copy(gt_info["meta_json"], dst_meta)
        copied.append(str(dst_meta))

    return {
        "gt_kind": gt_info["kind"],
        "copied_files": copied,
        "mapping_json": str(gt_info["mapping_json"]) if gt_info["mapping_json"] else None,
        "mappings_dir": str(gt_info["mappings_dir"]) if gt_info["mappings_dir"] else None,
        "meta_json": str(gt_info["meta_json"]) if gt_info["meta_json"] else None,
    }
