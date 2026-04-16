from __future__ import annotations

import argparse
from pathlib import Path

from .runner import CompareConfig, run_compare


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Thin Burr wrapper with GT/pred preprocessing")
    p.add_argument("--project-root", type=Path, default=Path("."))
    p.add_argument("--scenario-dir", type=Path, required=True)
    p.add_argument("--prediction-path", type=Path, required=True)
    p.add_argument("--output-path", type=Path, required=True)
    p.add_argument("--gt-path", type=Path, default=None)
    p.add_argument("--gt-kind", choices=["ttl", "json"], default="ttl")
    p.add_argument("--meta-path", type=Path, default=None)
    p.add_argument("--temp-dir", type=Path, default=None)
    return p


def main() -> None:
    args = build_parser().parse_args()
    cfg = CompareConfig(
        project_root=args.project_root,
        scenario_dir=args.scenario_dir,
        prediction_path=args.prediction_path,
        output_path=args.output_path,
        gt_path=args.gt_path,
        gt_kind=args.gt_kind,
        meta_path=args.meta_path,
        temp_dir=args.temp_dir,
    )
    run_compare(cfg)
