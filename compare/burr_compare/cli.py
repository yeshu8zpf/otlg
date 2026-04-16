from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run_compare
from .types import CompareConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Burr compare with pre-processing.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--scenario-dir", type=Path, required=True)
    parser.add_argument("--prediction-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--gt-path", type=Path, default=None)
    parser.add_argument("--gt-kind", choices=["ttl", "json"], default="ttl")
    parser.add_argument("--meta-path", type=Path, default=None)
    parser.add_argument("--temp-dir", type=Path, default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = CompareConfig(
        project_root=args.project_root,
        scenario_dir=args.scenario_dir,
        prediction_path=args.prediction_path,
        output_path=args.output_path,
        gt_path=args.gt_path,
        gt_kind=args.gt_kind,
        meta_path=args.meta_path,
        temp_dir=args.temp_dir,
    )
    run_compare(config)