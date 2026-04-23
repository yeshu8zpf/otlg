
from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.llm import call_llm_json_stream
from .table_incremental_orchestrator_compat import (
    OrchestratorConfig,
    run_table_incremental_orchestrator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run table-centric incremental ontology drafting.")
    parser.add_argument("--schema", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--api_url", type=str, required=True)
    parser.add_argument("--api_key", type=str, default="gpt")
    parser.add_argument("--timeout", type=float, default=300.0)

    parser.add_argument("--start_step", type=int, default=0)
    parser.add_argument("--end_step", type=int, default=None)
    parser.add_argument("--prepare_only", action="store_true")

    parser.add_argument("--disable_standard_subset", action="store_true")
    parser.add_argument("--no_persist_incremental_context", action="store_true")

    parser.add_argument("--enable_revision_pass", action="store_true")
    parser.add_argument("--revision_model", type=str, default=None)
    parser.add_argument("--revision_api_url", type=str, default=None)
    parser.add_argument("--revision_api_key", type=str, default=None)
    parser.add_argument("--revision_timeout", type=float, default=None)

    parser.add_argument("--revision_db_path", type=str, default=None)
    parser.add_argument("--revision_enable_value_sampling", action="store_true")
    parser.add_argument("--revision_sample_limit", type=int, default=8)
    parser.add_argument("--revision_distinct_limit", type=int, default=20)
    args = parser.parse_args()

    cfg = OrchestratorConfig(
        schema_path=Path(args.schema),
        out_dir=Path(args.out_dir),
        model=args.model,
        api_url=args.api_url,
        timeout=args.timeout,
        start_step=args.start_step,
        end_step=args.end_step,
        include_standard_subset=not args.disable_standard_subset,
        persist_full_incremental_context=not args.no_persist_incremental_context,
        run_llm=not args.prepare_only,
        api_key=args.api_key,

        enable_revision_pass=args.enable_revision_pass,
        revision_model=args.revision_model,
        revision_api_url=args.revision_api_url,
        revision_api_key=args.revision_api_key,
        revision_timeout=args.revision_timeout,

        revision_db_path=Path(args.revision_db_path) if args.revision_db_path else None,
        revision_enable_value_sampling=args.revision_enable_value_sampling,
        revision_sample_limit=args.revision_sample_limit,
        revision_distinct_limit=args.revision_distinct_limit,
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
