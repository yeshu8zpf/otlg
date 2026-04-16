from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .io_utils import read_text


COPY_RE = re.compile(
    r"""\\copy\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*\([^)]*\))?\s+FROM\s+'([^']+)'""",
    re.IGNORECASE,
)

CREATE_TABLE_RE = re.compile(
    r"""CREATE\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\);""",
    re.IGNORECASE | re.DOTALL,
)


def classify_sql_file(path: Path) -> str:
    name = path.name.lower()
    fk_positive = ["_fk.", "_fks.", "fk.sql", "fks.sql", "schema_pg_fks", "with_fk", "with_fks"]
    fk_negative = ["no_fk", "nofk", "without_fk", "withoutfks"]

    if any(tok in name for tok in fk_negative):
        return "no_fk"
    if any(tok in name for tok in fk_positive):
        return "fk"

    text = read_text(path).lower()
    if "foreign key" in text or " references " in text:
        return "fk"

    return "unknown"


def find_schema_sql(scenario_dir: Path, fk_mode: str = "auto") -> Path:
    candidates = sorted(scenario_dir.glob("*.sql"), key=lambda p: p.name)
    if not candidates:
        raise FileNotFoundError(f"No .sql file found in {scenario_dir}")

    classified = [(classify_sql_file(p), p) for p in candidates]
    fk_files = [p for c, p in classified if c == "fk"]
    no_fk_files = [p for c, p in classified if c == "no_fk"]
    unknown_files = [p for c, p in classified if c == "unknown"]

    def choose_best_default() -> Path:
        scored = []
        for p in candidates:
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
            scored.append((score, -len(name), p))
        scored.sort(key=lambda x: (-x[0], x[1], x[2].name))
        return scored[0][2]

    if fk_mode == "fk":
        if fk_files:
            return sorted(fk_files, key=lambda p: p.name)[0]
        return choose_best_default()

    if fk_mode == "no_fk":
        if no_fk_files:
            return sorted(no_fk_files, key=lambda p: p.name)[0]
        if unknown_files:
            return sorted(unknown_files, key=lambda p: p.name)[0]
        return choose_best_default()

    if fk_mode == "auto":
        return choose_best_default()

    raise ValueError(f"Unsupported fk_mode={fk_mode}")


def parse_copy_sources(schema_sql_text: str) -> List[Tuple[str, str]]:
    return COPY_RE.findall(schema_sql_text)


def resolve_csv_path(scenario_dir: Path, rel_csv_path: str) -> Optional[Path]:
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
    copy_entries = parse_copy_sources(schema_sql_text)

    for table_name, rel_csv_path in copy_entries:
        csv_path = resolve_csv_path(scenario_dir, rel_csv_path)
        if csv_path is None:
            continue

        rows: List[Dict[str, Any]] = []
        try:
            with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    rows.append(dict(row))
                    if i + 1 >= max_rows_per_table:
                        break
        except Exception:
            continue

        samples[table_name] = rows

    return samples


def extract_table_definitions(schema_sql_text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for table_name, body in CREATE_TABLE_RE.findall(schema_sql_text):
        lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
        out[table_name] = "\n".join(lines).strip()
    return out


def compact_table_definitions(
    table_defs: Dict[str, str],
    max_tables: int = 40,
    max_chars_per_table: int = 1200,
) -> Dict[str, str]:
    items = sorted(table_defs.items(), key=lambda kv: kv[0])[:max_tables]
    compact: Dict[str, str] = {}
    for table_name, definition in items:
        text = definition.strip()
        if len(text) > max_chars_per_table:
            text = text[:max_chars_per_table].rstrip() + "\n... [truncated]"
        compact[table_name] = text
    return compact


def clean_schema_sql_for_prompt(schema_sql_text: str) -> str:
    text = schema_sql_text or ""
    text = re.sub(r"(?m)^\s*\\.*?$", "", text)
    text = re.sub(
        r"(?im)^\s*(DROP DATABASE|CREATE DATABASE|SELECT pg_terminate_backend|SET\s+default_.*?).*$",
        "",
        text,
    )
    text = re.sub(r"(?is)INSERT\s+INTO\s+.*?;\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text
