
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Make project root importable when run as a standalone script copied into a project.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.llm import call_llm_json_stream
from .table_incremental_orchestrator_compat import (
    OrchestratorConfig,
    run_table_incremental_orchestrator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run table-centric incremental ontology drafting.")
    parser.add_argument("--schema", type=str, default='burr_benchmark/real-world/iswc/schema.sql', help="Path to schema.sql")
    parser.add_argument("--out_dir", type=str, default='tmp/iswc', help="Output directory")
    parser.add_argument("--model", type=str, default="gpt-5.4-nano", help="Model name")
    parser.add_argument("--api_url", type=str, default="https://www.aiapikey.net", help="API URL")
    parser.add_argument("--timeout", type=float, default=300.0, help="LLM timeout")
    parser.add_argument("--start_step", type=int, default=0, help="Start incremental step")
    parser.add_argument("--end_step", type=int, default=None, help="End incremental step (exclusive)")
    parser.add_argument("--no_standard_subset", action="store_true", help="Disable standard subset selection")
    parser.add_argument("--prepare_only", action="store_true", help="Only build incremental prompts, do not call LLM")
    parser.set_defaults(no_standard_subset=False,
                        prepare_only=False)

    args = parser.parse_args()

    if 'gpt' in args.model:
        api_key = 'gpt' 
    elif 'claude' in args.model:
        api_key = 'claude' 
    cfg = OrchestratorConfig(
        schema_path=Path(args.schema),
        out_dir=Path(args.out_dir),
        model=args.model,
        api_url=args.api_url,
        timeout=args.timeout,
        start_step=args.start_step,
        end_step=args.end_step,
        include_standard_subset=not args.no_standard_subset,
        run_llm=not args.prepare_only,
        api_key=api_key
    )

    result = run_table_incremental_orchestrator(
        config=cfg,
        call_llm_json_stream_fn=call_llm_json_stream,
    )

    print("[OK] table-centric incremental run finished")
    for k, v in result.items():
        print(f"[OK] {k}: {v}")


if __name__ == "__main__":
    main()
