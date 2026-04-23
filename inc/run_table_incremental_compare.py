
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .draft_to_burr_mapping import convert_global_draft_file
from pipeline.compare_adapter import run_burr_compare_wrapper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--global_draft", type=str, required=True)
    parser.add_argument("--scenario_dir", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--gt_path", type=str, default=None)
    args = parser.parse_args()

    project_root = Path("/root/ontology")
    global_draft_path = Path(args.global_draft)
    scenario_dir = Path(args.scenario_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mapping_path = out_dir / "mapping.json"
    compare_output_path = out_dir / "compare.json"

    convert_global_draft_file(global_draft_path, mapping_path)

    compare_result = run_burr_compare_wrapper(
        project_root=project_root,
        scenario_dir=scenario_dir,
        prediction_path=mapping_path,
        output_path=compare_output_path,
        gt_path=Path(args.gt_path) if args.gt_path else None,
    )

    compare_output_path.write_text(
        json.dumps(compare_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[OK] mapping:", mapping_path)
    print("[OK] compare:", compare_output_path)


if __name__ == "__main__":
    main()
