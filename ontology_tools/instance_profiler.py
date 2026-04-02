from __future__ import annotations

from typing import Any, Dict, List, Set

from .common import guess_basic_type, guess_is_boolean_like


class InstanceProfiler:
    def _profile_column(self, values: List[Any]) -> Dict[str, Any]:
        vals = [str(v) if v is not None else "" for v in values]
        non_empty = [v for v in vals if v != ""]
        distinct = len(set(non_empty))
        total = len(vals)
        null_count = sum(1 for v in vals if v == "")
        distinct_ratio = (distinct / len(non_empty)) if non_empty else 0.0
        return {
            "sample_values": non_empty[:10],
            "guessed_type": guess_basic_type(non_empty),
            "is_boolean_like": guess_is_boolean_like(non_empty),
            "null_ratio": (null_count / total) if total else 0.0,
            "distinct_ratio": distinct_ratio,
            "num_non_empty": len(non_empty),
        }

    def _collect_overlap(self, sample_rows: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        col_sets: Dict[str, Set[str]] = {}
        for table, rows in sample_rows.items():
            if not rows:
                continue
            columns = sorted({k for r in rows for k in r.keys()})
            for col in columns:
                key = f"{table}.{col}"
                vals = {str(r.get(col)).strip() for r in rows if str(r.get(col)).strip() != ""}
                col_sets[key] = vals

        keys = sorted(col_sets.keys())
        overlaps: List[Dict[str, Any]] = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                if a.split(".", 1)[0] == b.split(".", 1)[0]:
                    continue
                sa, sb = col_sets[a], col_sets[b]
                if not sa or not sb:
                    continue
                inter = sa.intersection(sb)
                if not inter:
                    continue
                ratio = min(len(inter) / len(sa), len(inter) / len(sb))
                if ratio >= 0.3:
                    overlaps.append(
                        {
                            "left": a,
                            "right": b,
                            "shared_count": len(inter),
                            "overlap_ratio_min_side": ratio,
                            "examples": sorted(list(inter))[:10],
                        }
                    )
        return overlaps

    def profile(self, sample_rows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        tables: Dict[str, Any] = {}
        for table, rows in sample_rows.items():
            table_profile = {
                "num_rows_sampled": len(rows),
                "columns": {},
            }
            all_cols = sorted({k for row in rows for k in row.keys()})
            for col in all_cols:
                values = [row.get(col) for row in rows]
                table_profile["columns"][col] = self._profile_column(values)
            tables[table] = table_profile

        overlaps = self._collect_overlap(sample_rows)

        return {
            "tables": tables,
            "cross_table_value_overlap": overlaps,
        }
