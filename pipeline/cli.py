from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from .runner import execute_run
from .tools_context import parse_enabled_tools


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tool-augmented ontology learning orchestrator with layered outputs."
    )
    parser.add_argument("--scenario-dir", type=str, default="burr_benchmark/real-world/iswc")
    parser.add_argument("--schema-path", type=str, default=None)
    parser.add_argument("--fk-mode", type=str, default="fk", choices=["auto", "fk", "no_fk"])
    parser.add_argument("--model", type=str, default="gpt-5.4-nano")
    parser.add_argument("--api-url", type=str, default="https://www.aiapikey.net/v1/chat/completions")
    parser.add_argument("--max-rows-per-table", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--out-dir", type=str, default="outputs/iswc")
    parser.add_argument("--run-burr-compare", action="store_true")
    parser.add_argument("--meta-path", type=str, default=None)
    parser.add_argument("--database-name", type=str, default=None)

    parser.add_argument(
        "--enabled-tools",
        type=str,
        default="schema_profiler",
        help="Comma-separated from: schema_profiler,instance_profiler,pattern_detector,mapping_verifier_lite",
    )
    parser.add_argument("--include-schema-sql", action="store_true")
    parser.add_argument("--include-sample-rows", action="store_true")
    parser.add_argument("--include-tool-context", action="store_true")
    parser.add_argument("--copy-gt-artifacts", action="store_true")
    parser.add_argument("--fail-fast-on-invalid-draft", action="store_true")

    parser.add_argument(
        "--resume",
        choices=["auto", "off"],
        default="auto",
    )

    parser.add_argument(
        "--start-from",
        choices=["llm", "normalize", "draft", "mapping", "compare"],
        default=None,
    )

    parser.set_defaults(
        run_burr_compare=True,
        include_sample_rows=False,
        include_schema_sql=False,
        copy_gt_artifacts=True,
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scenario_dir = Path(args.scenario_dir).resolve()
    schema_path = Path(args.schema_path).resolve() if args.schema_path else None
    out_dir = Path(args.out_dir).resolve()
    meta_path = Path(args.meta_path).resolve() if args.meta_path else None

    execute_run(
        project_root=PROJECT_ROOT,
        scenario_dir=scenario_dir,
        schema_path=schema_path,
        fk_mode=args.fk_mode,
        model=args.model,
        api_url=args.api_url,
        max_rows_per_table=args.max_rows_per_table,
        timeout=args.timeout,
        out_dir=out_dir,
        run_burr_compare=bool(args.run_burr_compare),
        meta_path=meta_path,
        database_name=args.database_name,
        enabled_tools=parse_enabled_tools(args.enabled_tools),
        include_schema_sql=bool(args.include_schema_sql),
        include_sample_rows=bool(args.include_sample_rows),
        include_tool_context=True if not args.include_tool_context else True,
        copy_gt_artifacts=bool(args.copy_gt_artifacts),
        fail_fast_on_invalid_draft=bool(args.fail_fast_on_invalid_draft),
    )
