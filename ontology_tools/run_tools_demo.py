from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from ontology_tools import SchemaProfiler, InstanceProfiler, PatternDetector, HypothesisStore


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


COPY_RE = re.compile(
    r"\\copy\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*\([^)]*\))?\s+FROM\s+'([^']+)'",
    re.IGNORECASE,
)


def parse_copy_sources(schema_sql_text: str):
    return COPY_RE.findall(schema_sql_text)


def resolve_csv_path(scenario_dir: Path, rel_csv_path: str) -> Path | None:
    p1 = (scenario_dir / rel_csv_path).resolve()
    if p1.exists():
        return p1
    p2 = (scenario_dir / Path(rel_csv_path).name).resolve()
    if p2.exists():
        return p2
    return None


def load_sample_rows_from_csv(
    scenario_dir: Path,
    schema_sql_text: str,
    max_rows_per_table: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    samples: Dict[str, List[Dict[str, Any]]] = {}
    for table_name, rel_csv_path in parse_copy_sources(schema_sql_text):
        csv_path = resolve_csv_path(scenario_dir, rel_csv_path)
        if csv_path is None:
            continue
        rows: List[Dict[str, Any]] = []
        with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                rows.append(dict(row))
                if i + 1 >= max_rows_per_table:
                    break
        samples[table_name] = rows
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ontology tools demo on a Burr scenario.")
    parser.add_argument("--scenario-dir", type=str, required=True)
    parser.add_argument("--schema-path", type=str, default=None)
    parser.add_argument("--out-dir", type=str, default="outputs/tools_demo")
    parser.add_argument("--max-rows-per-table", type=int, default=5)
    args = parser.parse_args()

    scenario_dir = Path(args.scenario_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_path = Path(args.schema_path).resolve() if args.schema_path else (scenario_dir / "schema.sql")
    schema_sql_text = read_text(schema_path)
    sample_rows = load_sample_rows_from_csv(scenario_dir, schema_sql_text, args.max_rows_per_table)

    schema_profile = SchemaProfiler().profile(schema_sql_text)
    instance_profile = InstanceProfiler().profile(sample_rows)
    hypotheses = PatternDetector().detect(schema_profile, instance_profile)

    store = HypothesisStore()
    for h in hypotheses:
        store.add(h)

    (out_dir / "schema_profile.json").write_text(json.dumps(schema_profile, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "instance_profile.json").write_text(json.dumps(instance_profile, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "hypotheses.json").write_text(json.dumps(store.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(store.summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
