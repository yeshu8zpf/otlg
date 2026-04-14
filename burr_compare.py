from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from canonical_compare import build_canonical_details

# ============================================================
# Path setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Basic IO helpers
# ============================================================

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


# ============================================================
# Import resolution for your repo
# ============================================================

def _import_local_burr_modules():
    """
    Import local evaluator modules.
    Some copied Burr evaluator files import optional logging deps like wandb
    at module import time. We provide a tiny stub if wandb is unavailable.
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        import wandb  # noqa: F401
    except ModuleNotFoundError:
        class _WandbStub:
            def __getattr__(self, name):
                def _noop(*args, **kwargs):
                    return None
                return _noop

        sys.modules["wandb"] = _WandbStub()

    from burr_evaluator.mapping_parser.mapping.JsonMapping import JsonMapping
    from burr_evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
    from burr_evaluator.metrics.caclulate_metrics import calculate_metrics

    return JsonMapping, D2RQMapping, calculate_metrics


# ============================================================
# GT resolution
# ============================================================

def find_ttl_candidates(scenario_dir: Path) -> List[Path]:
    """
    Burr-style GT TTL forms that appear in real-world datasets.
    """
    preferred_names = [
        "groundtruth.ttl",
        "map_d2rq.ttl",
        "mapping.ttl",
        "test_mapping.ttl",
    ]

    found: List[Path] = []
    for name in preferred_names:
        p = scenario_dir / name
        if p.exists() and p.is_file():
            found.append(p)

    for p in sorted(scenario_dir.glob("*.ttl"), key=lambda x: x.name):
        if p not in found:
            found.append(p)

    return found


def resolve_gt_for_scenario(scenario_dir: Path) -> Dict[str, Any]:
    """
    Compatible with the GT forms used in Burr / your repo:

      1) single_json:
         scenario_dir / mapping.json

      2) single_ttl:
         scenario_dir / groundtruth.ttl
         scenario_dir / map_d2rq.ttl
         scenario_dir / mapping.ttl
         scenario_dir / test_mapping.ttl
         or any *.ttl at scenario root

      3) mapping_dir:
         scenario_dir / mappings / *.json   (excluding meta.json)
         merged before evaluation

    Returns:
      {
        "kind": "single_json" | "single_ttl" | "mapping_dir" | "missing",
        "mapping_json": Path | None,
        "mapping_ttl": Path | None,
        "mappings_dir": Path | None,
        "meta_json": Path | None,
        "json_files": List[Path],
        "ttl_candidates": List[Path],
      }
    """
    scenario_dir = scenario_dir.resolve()
    mapping_json = scenario_dir / "mapping.json"
    mappings_dir = scenario_dir / "mappings"
    meta_json = scenario_dir / "meta.json"

    result: Dict[str, Any] = {
        "kind": "missing",
        "mapping_json": None,
        "mapping_ttl": None,
        "mappings_dir": None,
        "meta_json": meta_json if meta_json.exists() and meta_json.is_file() else None,
        "json_files": [],
        "ttl_candidates": [],
    }

    if mapping_json.exists() and mapping_json.is_file():
        result["kind"] = "single_json"
        result["mapping_json"] = mapping_json
        result["json_files"] = [mapping_json]
        return result

    ttl_candidates = find_ttl_candidates(scenario_dir)
    result["ttl_candidates"] = ttl_candidates
    if ttl_candidates:
        result["kind"] = "single_ttl"
        result["mapping_ttl"] = ttl_candidates[0]
        return result

    if mappings_dir.exists() and mappings_dir.is_dir():
        json_files = sorted(
            [
                p for p in mappings_dir.glob("*.json")
                if p.is_file() and p.name.lower() != "meta.json"
            ],
            key=lambda p: p.name,
        )
        result["kind"] = "mapping_dir"
        result["mappings_dir"] = mappings_dir
        result["json_files"] = json_files

        nested_meta = mappings_dir / "meta.json"
        if nested_meta.exists() and nested_meta.is_file():
            result["meta_json"] = nested_meta

        return result

    return result


def merge_mapping_json_files(json_files: List[Path]) -> Dict[str, Any]:
    """
    Merge mapping fragments the same way Burr's experiment setup merges them:
    - list values -> extend
    - dict values -> update
    - other values -> overwrite
    """
    merged: Dict[str, Any] = {}

    for path in json_files:
        data = read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"GT mapping JSON must be an object: {path}")

        for key, value in data.items():
            if key not in merged:
                if isinstance(value, list):
                    merged[key] = list(value)
                elif isinstance(value, dict):
                    merged[key] = dict(value)
                else:
                    merged[key] = value
                continue

            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key].extend(value)
            elif isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value

    return merged


# ============================================================
# Meta / database helpers
# ============================================================

def default_meta_path_for_scenario(
    scenario_dir: Path,
    gt_info: Optional[Dict[str, Any]] = None,
) -> Optional[Path]:
    if gt_info is None:
        gt_info = resolve_gt_for_scenario(scenario_dir)

    meta_path = gt_info.get("meta_json")
    if isinstance(meta_path, Path) and meta_path.exists():
        return meta_path

    candidate = scenario_dir / "meta.json"
    if candidate.exists() and candidate.is_file():
        return candidate

    return None


def infer_database_name(
    scenario_dir: Path,
    explicit_database_name: Optional[str],
) -> str:
    if explicit_database_name:
        return explicit_database_name
    return scenario_dir.name


# ============================================================
# Mapping loading
# ============================================================

def load_mapping_as_d2rq_from_json_data(
    data: Dict[str, Any],
    database_name: str,
    meta: Optional[Dict[str, Any]],
):
    JsonMapping, _, _ = _import_local_burr_modules()
    return JsonMapping(data, database_name, meta).to_D2RQ_Mapping()


def load_mapping_as_d2rq(
    mapping_path: Path,
    database_name: str,
    meta: Optional[Dict[str, Any]],
):
    JsonMapping, D2RQMapping, _ = _import_local_burr_modules()

    mapping_path = mapping_path.resolve()
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping path not found: {mapping_path}")

    suffix = mapping_path.suffix.lower()
    if suffix == ".json":
        data = read_json(mapping_path)
        return JsonMapping(data, database_name, meta).to_D2RQ_Mapping()
    if suffix in {".ttl", ".turtle"}:
        return D2RQMapping(read_text(mapping_path), database_name, meta)

    raise ValueError(f"Unsupported mapping file type: {mapping_path}")


def load_gt_mapping_as_d2rq(
    scenario_dir: Path,
    gt_mapping_path: Optional[Path],
    meta_path: Optional[Path],
    database_name: str,
):
    meta = read_json(meta_path) if meta_path is not None and meta_path.exists() else None

    if gt_mapping_path is not None:
        return load_mapping_as_d2rq(gt_mapping_path, database_name, meta), {
            "gt_mode": "explicit_single",
            "gt_mapping_path": str(gt_mapping_path),
            "meta_path": str(meta_path) if meta_path else None,
        }

    gt_info = resolve_gt_for_scenario(scenario_dir)
    if gt_info["kind"] == "missing":
        raise FileNotFoundError(
            f"GT mapping not found for scenario: {scenario_dir}. "
            f"Expected one of: mapping.json, preferred *.ttl "
            f"(groundtruth.ttl/map_d2rq.ttl/...), or mappings/*.json"
        )

    if gt_info["kind"] == "single_json":
        path = gt_info["mapping_json"]
        return load_mapping_as_d2rq(path, database_name, meta), {
            "gt_mode": "single_json",
            "gt_mapping_path": str(path),
            "meta_path": str(meta_path) if meta_path else None,
        }

    if gt_info["kind"] == "single_ttl":
        path = gt_info["mapping_ttl"]
        return load_mapping_as_d2rq(path, database_name, meta), {
            "gt_mode": "single_ttl",
            "gt_mapping_path": str(path),
            "ttl_candidates": [str(p) for p in gt_info.get("ttl_candidates", [])],
            "meta_path": str(meta_path) if meta_path else None,
        }

    json_files = gt_info["json_files"]
    if not json_files:
        raise FileNotFoundError(f"No GT JSON files found under mapping dir: {gt_info['mappings_dir']}")

    merged_data = merge_mapping_json_files(json_files)
    d2rq = load_mapping_as_d2rq_from_json_data(merged_data, database_name, meta)
    return d2rq, {
        "gt_mode": "mapping_dir_merged",
        "gt_mapping_dir": str(gt_info["mappings_dir"]),
        "gt_component_files": [str(p) for p in json_files],
        "num_gt_component_files": len(json_files),
        "meta_path": str(meta_path) if meta_path else None,
    }


# ============================================================
# Compare
# ============================================================
from collections import Counter


def _safe_obj_repr(obj: Any) -> str:
    """
    Stable debug string for compare details.
    Prefer str(obj); fall back to repr(obj).
    """
    try:
        s = str(obj)
        if s:
            return s
    except Exception:
        pass
    try:
        return repr(obj)
    except Exception:
        return f"<unreprable {type(obj).__name__}>"


def _set_eq_strategy(items: List[Any], *, name_based: bool) -> None:
    """
    Burr mapping objects support set_eq_strategy(name_based=...).
    This mutates their equality/hash semantics for comparison.
    """
    for x in items:
        if hasattr(x, "set_eq_strategy"):
            x.set_eq_strategy(name_based=name_based)


def _bag_diff(
    reference_items: List[Any],
    learned_items: List[Any],
    *,
    name_based: bool,
) -> Dict[str, Any]:
    """
    Bag-based diff, aligned with Burr mapping-based metric logic.
    Keeps multiplicity via Counter.
    """
    reference_items = list(reference_items or [])
    learned_items = list(learned_items or [])

    _set_eq_strategy(reference_items, name_based=name_based)
    _set_eq_strategy(learned_items, name_based=name_based)

    ref_counter = Counter(reference_items)
    pred_counter = Counter(learned_items)

    matched: List[str] = []
    missing: List[str] = []
    extra: List[str] = []

    all_keys = list(set(ref_counter.keys()) | set(pred_counter.keys()))
    for k in all_keys:
        ref_n = ref_counter.get(k, 0)
        pred_n = pred_counter.get(k, 0)
        common = min(ref_n, pred_n)

        matched.extend([_safe_obj_repr(k)] * common)
        if ref_n > pred_n:
            missing.extend([_safe_obj_repr(k)] * (ref_n - pred_n))
        if pred_n > ref_n:
            extra.extend([_safe_obj_repr(k)] * (pred_n - ref_n))

    return {
        "num_reference": sum(ref_counter.values()),
        "num_prediction": sum(pred_counter.values()),
        "num_matched": len(matched),
        "num_missing_in_prediction": len(missing),
        "num_extra_in_prediction": len(extra),
        "matched": matched,
        "missing_in_prediction": missing,
        "extra_in_prediction": extra,
        "matched_counts": _count_strings(matched),
        "missing_in_prediction_counts": _count_strings(missing),
        "extra_in_prediction_counts": _count_strings(extra),
    }


def _set_diff(
    reference_items: List[Any],
    learned_items: List[Any],
    *,
    name_based: bool,
) -> Dict[str, Any]:
    """
    Set-based diff, aligned with Burr name-based metric logic.
    """
    reference_items = list(reference_items or [])
    learned_items = list(learned_items or [])

    _set_eq_strategy(reference_items, name_based=name_based)
    _set_eq_strategy(learned_items, name_based=name_based)

    ref_set = set(reference_items)
    pred_set = set(learned_items)

    matched = [_safe_obj_repr(x) for x in (ref_set & pred_set)]
    missing = [_safe_obj_repr(x) for x in (ref_set - pred_set)]
    extra = [_safe_obj_repr(x) for x in (pred_set - ref_set)]

    matched.sort()
    missing.sort()
    extra.sort()

    return {
        "num_reference": len(ref_set),
        "num_prediction": len(pred_set),
        "num_matched": len(matched),
        "num_missing_in_prediction": len(missing),
        "num_extra_in_prediction": len(extra),
        "matched": matched,
        "missing_in_prediction": missing,
        "extra_in_prediction": extra,
        "matched_counts": _count_strings(matched),
        "missing_in_prediction_counts": _count_strings(missing),
        "extra_in_prediction_counts": _count_strings(extra),
    }

def _count_strings(items: List[str]) -> List[Dict[str, Any]]:
    c = Counter(items)
    return [
        {"item": k, "count": v}
        for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

def build_detailed_compare(reference_mapping: Any, learned_mapping: Any) -> Dict[str, Any]:
    """
    Return fine-grained TP/FP/FN-style details for:
    - mapping_based (bag semantics)
    - name_based (set semantics)

    Categories:
    - classes
    - relations
    - attributes
    """
    ref_classes = list(reference_mapping.get_classes())
    ref_relations = list(reference_mapping.get_relations())
    ref_attributes = list(reference_mapping.get_attributes())

    pred_classes = list(learned_mapping.get_classes())
    pred_relations = list(learned_mapping.get_relations())
    pred_attributes = list(learned_mapping.get_attributes())

    return {
        "mapping_based": {
            "classes": _bag_diff(ref_classes, pred_classes, name_based=False),
            "relations": _bag_diff(ref_relations, pred_relations, name_based=False),
            "attributes": _bag_diff(ref_attributes, pred_attributes, name_based=False),
        },
        "name_based": {
            "classes": _set_diff(ref_classes, pred_classes, name_based=True),
            "relations": _set_diff(ref_relations, pred_relations, name_based=True),
            "attributes": _set_diff(ref_attributes, pred_attributes, name_based=True),
        },
    }


def compare_mappings(learned_mapping, reference_mapping) -> Dict[str, Any]:
    """
    Return:
    - original Burr metrics/details
    - canonical, representation-normalized compare
    """
    _, _, calculate_metrics = _import_local_burr_modules()

    metrics = calculate_metrics(reference_mapping, learned_mapping)
    details = build_detailed_compare(reference_mapping, learned_mapping)
    canonical_compare = build_canonical_details(reference_mapping, learned_mapping)

    return {
        "metrics": metrics,
        "details": details,
        "canonical_compare": canonical_compare,
    }


def run_compare(
    scenario_dir: Path,
    pred_mapping_path: Path,
    gt_mapping_path: Optional[Path] = None,
    meta_path: Optional[Path] = None,
    database_name: Optional[str] = None,
) -> Dict[str, Any]:
    scenario_dir = scenario_dir.resolve()
    pred_mapping_path = pred_mapping_path.resolve()

    if not pred_mapping_path.exists():
        raise FileNotFoundError(f"Predicted mapping not found: {pred_mapping_path}")

    gt_info = resolve_gt_for_scenario(scenario_dir)
    effective_meta_path = Path(meta_path).resolve() if meta_path is not None else default_meta_path_for_scenario(scenario_dir, gt_info)
    effective_database_name = infer_database_name(scenario_dir, database_name)
    meta = read_json(effective_meta_path) if effective_meta_path is not None and effective_meta_path.exists() else None

    learned_mapping = load_mapping_as_d2rq(
        pred_mapping_path,
        effective_database_name,
        meta,
    )

    reference_mapping, gt_resolution = load_gt_mapping_as_d2rq(
        scenario_dir=scenario_dir,
        gt_mapping_path=Path(gt_mapping_path).resolve() if gt_mapping_path is not None else None,
        meta_path=effective_meta_path,
        database_name=effective_database_name,
    )

    compare_payload = compare_mappings(learned_mapping, reference_mapping)

    result = {
        "scenario_dir": str(scenario_dir),
        "pred_mapping_path": str(pred_mapping_path),
        "database_name": effective_database_name,
        "meta_path": str(effective_meta_path) if effective_meta_path else None,
        **gt_resolution,
        **compare_payload,
    }
    return result


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run comparison between a predicted mapping and the GT mapping(s) for a scenario."
    )
    parser.add_argument("--scenario-dir", type=str, required=True)
    parser.add_argument("--pred-mapping-path", type=str, required=True)
    parser.add_argument("--gt-mapping-path", type=str, default=None)
    parser.add_argument("--meta-path", type=str, default=None)
    parser.add_argument("--database-name", type=str, default=None)
    parser.add_argument("--out-path", type=str, default=None)

    args = parser.parse_args()

    result = run_compare(
        scenario_dir=Path(args.scenario_dir).resolve(),
        pred_mapping_path=Path(args.pred_mapping_path).resolve(),
        gt_mapping_path=Path(args.gt_mapping_path).resolve() if args.gt_mapping_path else None,
        meta_path=Path(args.meta_path).resolve() if args.meta_path else None,
        database_name=args.database_name,
    )

    if args.out_path:
        write_json(Path(args.out_path).resolve(), result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
