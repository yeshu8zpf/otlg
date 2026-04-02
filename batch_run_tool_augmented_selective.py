from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def read_json(path: Path) -> Optional[Any]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_copy(path: Path, dst: Path) -> None:
    if path.exists() and path.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


def find_scenarios(root: Path) -> List[Path]:
    out: List[Path] = []
    exclude_names = {"output", "outputs", "__pycache__", ".git"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_names]
        p = Path(dirpath).resolve()
        files = set(filenames)
        subdirs = set(dirnames)
        has_sql = any(name.lower().endswith(".sql") for name in files)
        has_mapping_json = "mapping.json" in files
        has_mappings_dir = "mappings" in subdirs
        if has_mapping_json or has_mappings_dir or has_sql:
            out.append(p)

    out = sorted(set(out), key=lambda x: (len(x.parts), str(x)))
    filtered: List[Path] = []
    for p in out:
        is_parent_of_existing = any(str(existing).startswith(str(p) + os.sep) for existing in out if existing != p)
        if not is_parent_of_existing:
            filtered.append(p)
    return sorted(set(filtered), key=lambda x: str(x))


def slugify_path(p: Path, root: Path) -> str:
    rel = p.resolve().relative_to(root.resolve())
    return "__".join(rel.parts)


def classify_sql_file(path: Path) -> str:
    name = path.name.lower()
    fk_positive = ["_fk.", "_fks.", "fk.sql", "fks.sql", "schema_pg_fks", "with_fk", "with_fks"]
    fk_negative = ["no_fk", "nofk", "without_fk", "withoutfks"]
    if any(tok in name for tok in fk_negative):
        return "no_fk"
    if any(tok in name for tok in fk_positive):
        return "fk"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        text = ""
    if "foreign key" in text or " references " in text:
        return "fk"
    return "unknown"


def find_sql_files(scenario_dir: Path) -> List[Path]:
    return sorted(
        [p for p in scenario_dir.iterdir() if p.is_file() and p.suffix.lower() == ".sql"],
        key=lambda p: p.name,
    )


def choose_sql_variants(scenario_dir: Path, fk_mode: str) -> List[Tuple[str, Optional[Path]]]:
    sql_files = find_sql_files(scenario_dir)
    if not sql_files:
        return [("default", None)]

    classified = [(classify_sql_file(p), p) for p in sql_files]
    fk_files = [p for c, p in classified if c == "fk"]
    no_fk_files = [p for c, p in classified if c == "no_fk"]
    unknown_files = [p for c, p in classified if c == "unknown"]

    def choose_best_default() -> Path:
        preferred = []
        for p in sql_files:
            name = p.name.lower()
            score = 0
            if name == "schema.sql":
                score += 100
            if "schema" in name:
                score += 30
            if "fk" in name or "fks" in name:
                score += 20
            if "pg" in name:
                score += 5
            preferred.append((score, -len(name), p))
        preferred.sort(key=lambda x: (-x[0], x[1], x[2].name))
        return preferred[0][2]

    if fk_mode == "auto":
        return [("auto", choose_best_default())]
    if fk_mode == "fk":
        if fk_files:
            return [("fk", sorted(fk_files, key=lambda p: p.name)[0])]
        return [("fk_fallback", choose_best_default())]
    if fk_mode == "no_fk":
        if no_fk_files:
            return [("no_fk", sorted(no_fk_files, key=lambda p: p.name)[0])]
        if unknown_files:
            return [("no_fk_fallback", sorted(unknown_files, key=lambda p: p.name)[0])]
        return [("no_fk_fallback", choose_best_default())]
    if fk_mode == "both":
        variants: List[Tuple[str, Path]] = []
        chosen = set()
        if no_fk_files:
            p = sorted(no_fk_files, key=lambda p: p.name)[0]
            variants.append(("no_fk", p))
            chosen.add(p.resolve())
        elif unknown_files:
            p = sorted(unknown_files, key=lambda p: p.name)[0]
            variants.append(("no_fk_fallback", p))
            chosen.add(p.resolve())

        if fk_files:
            p = sorted(fk_files, key=lambda p: p.name)[0]
            if p.resolve() not in chosen:
                variants.append(("fk", p))
        else:
            p = choose_best_default()
            if p.resolve() not in chosen:
                variants.append(("fk_fallback", p))

        if not variants:
            variants.append(("auto", choose_best_default()))
        return variants

    raise ValueError(f"Unsupported fk_mode={fk_mode}")


@dataclass
class CaseResult:
    scenario_dir: str
    case_name: str
    sql_variant_name: str
    sql_file: Optional[str]
    returncode: int
    duration_sec: float
    compare_present: bool
    compare_mapping_cls_f1: Optional[float] = None
    compare_mapping_rel_f1: Optional[float] = None
    compare_mapping_attr_f1: Optional[float] = None
    compare_name_cls_f1: Optional[float] = None
    compare_name_rel_f1: Optional[float] = None
    compare_name_attr_f1: Optional[float] = None


def run_one_case(
    *,
    script_path: Path,
    scenario_dir: Path,
    scenario_root: Path,
    batch_out_root: Path,
    python_executable: str,
    model: str,
    api_url: Optional[str],
    max_rows_per_table: int,
    timeout_sec: int,
    request_timeout: float,
    run_compare: bool,
    burr_root: Optional[Path],
    sql_variant_name: str,
    sql_path: Optional[Path],
    enabled_tools: str,
    include_schema_sql: bool,
    include_sample_rows: bool,
    include_tool_context: bool,
) -> CaseResult:
    case_name = scenario_dir.name
    case_slug = slugify_path(scenario_dir, scenario_root)
    variant_slug = f"{case_slug}__{sql_variant_name}"
    case_out_dir = batch_out_root / variant_slug
    case_out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        python_executable,
        str(script_path),
        "--scenario-dir", str(scenario_dir),
        "--out-dir", str(case_out_dir),
        "--model", model,
        "--timeout", str(request_timeout),
        "--max-rows-per-table", str(max_rows_per_table),
        "--fk-mode", "auto",
        "--enabled-tools", enabled_tools,
    ]

    if api_url:
        cmd.extend(["--api-url", api_url])
    if run_compare:
        cmd.append("--run-burr-compare")
    if burr_root is not None:
        cmd.extend(["--burr-root", str(burr_root)])
    if sql_path is not None:
        cmd.extend(["--schema-path", str(sql_path)])
    if include_schema_sql:
        cmd.append("--include-schema-sql")
    if include_sample_rows:
        cmd.append("--include-sample-rows")
    if include_tool_context:
        cmd.append("--include-tool-context")

    start = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
        encoding="utf-8",
        errors="ignore",
    )
    duration_sec = time.time() - start

    write_text(case_out_dir / "_batch_stdout.log", proc.stdout or "")
    write_text(case_out_dir / "_batch_stderr.log", proc.stderr or "")
    write_text(case_out_dir / "_batch_cmd.txt", " ".join(cmd))

    if sql_path is not None:
        maybe_copy(sql_path, case_out_dir / "scenario_inputs" / sql_path.name)
    maybe_copy(scenario_dir / "meta.json", case_out_dir / "scenario_inputs" / "meta.json")
    maybe_copy(scenario_dir / "metadata.json", case_out_dir / "scenario_inputs" / "metadata.json")
    maybe_copy(scenario_dir / "mapping.json", case_out_dir / "scenario_inputs" / "mapping.json")

    compare_json = read_json(case_out_dir / "compare.json")
    compare_present = isinstance(compare_json, dict)

    mapping_cls_f1 = None
    mapping_rel_f1 = None
    mapping_attr_f1 = None
    name_cls_f1 = None
    name_rel_f1 = None
    name_attr_f1 = None

    if compare_present:
        metrics = compare_json.get("metrics", {})
        mb = metrics.get("mapping_based", {})
        nb = metrics.get("name_based", {})
        mapping_cls_f1 = mb.get("cls_f1")
        mapping_rel_f1 = mb.get("rel_f1")
        mapping_attr_f1 = mb.get("attr_f1")
        name_cls_f1 = nb.get("cls_f1")
        name_rel_f1 = nb.get("rel_f1")
        name_attr_f1 = nb.get("attr_f1")

    return CaseResult(
        scenario_dir=str(scenario_dir),
        case_name=case_name,
        sql_variant_name=sql_variant_name,
        sql_file=str(sql_path.name) if sql_path else None,
        returncode=proc.returncode,
        duration_sec=duration_sec,
        compare_present=compare_present,
        compare_mapping_cls_f1=mapping_cls_f1,
        compare_mapping_rel_f1=mapping_rel_f1,
        compare_mapping_attr_f1=mapping_attr_f1,
        compare_name_cls_f1=name_cls_f1,
        compare_name_rel_f1=name_rel_f1,
        compare_name_attr_f1=name_attr_f1,
    )


def write_summary(results: List[CaseResult], out_root: Path) -> None:
    summary_json = {
        "num_cases": len(results),
        "by_sql_variant_name": {},
        "cases": [asdict(r) for r in results],
    }
    for r in results:
        sv = r.sql_variant_name
        summary_json["by_sql_variant_name"][sv] = summary_json["by_sql_variant_name"].get(sv, 0) + 1
    write_json(out_root / "batch_summary.json", summary_json)

    csv_path = out_root / "batch_summary.csv"
    rows = [asdict(r) for r in results]
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch runner for tool-augmented baseline with FK control and selectable tool settings."
    )
    parser.add_argument("--script-path", type=str, default="baseline/tool_augmented.py")
    parser.add_argument("--scenario-root", type=str, default='../burr/real-world')
    parser.add_argument("--out-root", type=str, default="outputs/batch_tool_augmented")
    parser.add_argument("--python-executable", type=str, default=sys.executable)
    parser.add_argument("--model", type=str, default="gpt-5.4-nano")
    parser.add_argument("--api-url", type=str, default=None)
    parser.add_argument("--max-rows-per-table", type=int, default=3)
    parser.add_argument("--timeout-sec", type=int, default=1800)
    parser.add_argument("--request-timeout", type=float, default=300.0)
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--scenario-filter", type=str, default=None)
    parser.add_argument("--run-burr-compare", action="store_true")
    parser.add_argument("--burr-root", type=str, default='../burr')
    parser.add_argument("--fk-mode", type=str, default="fk", choices=["auto", "fk", "no_fk", "both"])
    parser.add_argument("--enabled-tools", type=str, default="schema_profiler")
    parser.add_argument("--include-schema-sql", action="store_true")
    parser.add_argument("--include-sample-rows", action="store_true")
    parser.add_argument("--include-tool-context", action="store_true")
    parser.set_defaults(run_burr_compare=True,
                        include_schema_sql=False,
                        )

    args = parser.parse_args()

    script_path = Path(args.script_path).resolve()
    scenario_root = Path(args.scenario_root).resolve()
    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    scenarios = find_scenarios(scenario_root)
    if args.scenario_filter:
        scenarios = [p for p in scenarios if args.scenario_filter in str(p)]
    if args.limit is not None:
        scenarios = scenarios[: args.limit]

    if not scenarios:
        raise RuntimeError(f"No scenarios found under {scenario_root}")

    expanded_cases: List[Tuple[Path, str, Optional[Path]]] = []
    for scenario_dir in scenarios:
        variants = choose_sql_variants(scenario_dir, args.fk_mode)
        for variant_name, sql_path in variants:
            expanded_cases.append((scenario_dir, variant_name, sql_path))

    run_manifest = {
        "script_path": str(script_path),
        "scenario_root": str(scenario_root),
        "out_root": str(out_root),
        "python_executable": args.python_executable,
        "model": args.model,
        "api_url": args.api_url,
        "max_rows_per_table": args.max_rows_per_table,
        "timeout_sec": args.timeout_sec,
        "request_timeout": args.request_timeout,
        "run_burr_compare": args.run_burr_compare,
        "burr_root": args.burr_root,
        "fk_mode": args.fk_mode,
        "enabled_tools": args.enabled_tools,
        "include_schema_sql": args.include_schema_sql,
        "include_sample_rows": args.include_sample_rows,
        "include_tool_context": args.include_tool_context,
        "num_scenario_dirs": len(scenarios),
        "num_expanded_cases": len(expanded_cases),
    }
    write_json(out_root / "run_manifest.json", run_manifest)

    results: List[CaseResult] = []
    for i, (scenario_dir, variant_name, sql_path) in enumerate(expanded_cases, start=1):
        print(f"[{i}/{len(expanded_cases)}] running {scenario_dir} [{variant_name}]")
        try:
            result = run_one_case(
                script_path=script_path,
                scenario_dir=scenario_dir,
                scenario_root=scenario_root,
                batch_out_root=out_root / "cases",
                python_executable=args.python_executable,
                model=args.model,
                api_url=args.api_url,
                max_rows_per_table=args.max_rows_per_table,
                timeout_sec=args.timeout_sec,
                request_timeout=args.request_timeout,
                run_compare=args.run_burr_compare,
                burr_root=Path(args.burr_root).resolve() if args.burr_root else None,
                sql_variant_name=variant_name,
                sql_path=sql_path,
                enabled_tools=args.enabled_tools,
                include_schema_sql=args.include_schema_sql,
                include_sample_rows=args.include_sample_rows,
                include_tool_context=args.include_tool_context,
            )
        except subprocess.TimeoutExpired:
            result = CaseResult(
                scenario_dir=str(scenario_dir),
                case_name=scenario_dir.name,
                sql_variant_name=variant_name,
                sql_file=str(sql_path.name) if sql_path else None,
                returncode=-999,
                duration_sec=float(args.timeout_sec),
                compare_present=False,
            )
        results.append(result)
        write_summary(results, out_root)

    write_summary(results, out_root)
    print(f"[DONE] Wrote batch summary to {out_root}")


if __name__ == "__main__":
    main()
