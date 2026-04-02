from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology_draft import OntologyDraft
from normalize import normalize_model_output_robust
from burr_compare import run_compare


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def summarize_top_level_counts(obj: Dict[str, Any]) -> Dict[str, int]:
    return {
        "num_classes": len(obj.get("classes", []) or []),
        "num_data_properties": len(obj.get("data_properties", []) or []),
        "num_object_properties": len(obj.get("object_properties", []) or []),
        "num_subclass_relations": len(obj.get("subclass_relations", []) or []),
        "num_class_mappings": len(obj.get("class_mappings", []) or []),
        "num_data_property_mappings": len(obj.get("data_property_mappings", []) or []),
        "num_object_property_mappings": len(obj.get("object_property_mappings", []) or []),
    }


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_preview(title: str, obj: Any, limit: int = 2000) -> None:
    print_section(title)
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    if len(text) > limit:
        print(text[:limit] + "\n... [truncated]")
    else:
        print(text)


def build_compare_markdown(compare_result: Dict[str, Any]) -> str:
    metrics = compare_result["metrics"]
    gt_counts = compare_result["gt_counts"]
    pred_counts = compare_result["pred_counts"]

    lines = []
    lines.append("# Normalize Debug + Burr Compare")
    lines.append("")
    lines.append(f"- Scenario dir: `{compare_result.get('scenario_dir')}`")
    lines.append(f"- GT mapping: `{compare_result.get('gt_mapping_path')}`")
    lines.append(f"- Pred mapping: `{compare_result.get('pred_mapping_path')}`")
    lines.append(f"- Database name: `{compare_result.get('database_name')}`")
    lines.append("")
    lines.append("## Parsed element counts")
    lines.append("")
    lines.append(f"- GT: classes={gt_counts['num_classes']}, relations={gt_counts['num_relations']}, attributes={gt_counts['num_attributes']}")
    lines.append(f"- Prediction: classes={pred_counts['num_classes']}, relations={pred_counts['num_relations']}, attributes={pred_counts['num_attributes']}")
    lines.append("")

    for metric_name in ["mapping_based", "name_based"]:
        m = metrics[metric_name]
        lines.append(f"## {metric_name}")
        lines.append("")
        lines.append("| category | precision | recall | f1 |")
        lines.append("|---|---:|---:|---:|")
        lines.append(f"| classes | {m['cls_precision']:.4f} | {m['cls_recall']:.4f} | {m['cls_f1']:.4f} |")
        lines.append(f"| relations | {m['rel_precision']:.4f} | {m['rel_recall']:.4f} | {m['rel_f1']:.4f} |")
        lines.append(f"| attributes | {m['attr_precision']:.4f} | {m['attr_recall']:.4f} | {m['attr_f1']:.4f} |")
        lines.append("")

    return "\n".join(lines)


def safe_exception_payload(e: Exception) -> Dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug robust normalization for raw_model.json and optionally run Burr evaluation.")
    parser.add_argument(
        "--input",
        type=str,
        default='outputs/one_shot/hotel.raw_model.json',
        help="Path to raw_model.json",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/debug_normalize",
        help="Directory to write normalized/debug outputs",
    )
    parser.add_argument(
        "--scenario-dir",
        type=str,
        default="../burr/micro_benchmark/attributes/weak_entity/hotel",
        help="Optional Burr scenario directory. If provided, also run Burr comparison against scenario_dir/mapping.json.",
    )
    parser.add_argument(
        "--gt-mapping",
        type=str,
        default=None,
        help="Optional explicit GT mapping path for Burr comparison.",
    )
    parser.add_argument(
        "--meta-path",
        type=str,
        default=None,
        help="Optional explicit meta.json path for Burr comparison.",
    )
    parser.add_argument(
        "--burr-root",
        type=str,
        default=str((PROJECT_ROOT / "../burr").resolve()),
        help="Path to local Burr repository root.",
    )
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
        help="Optional database name passed into Burr parsers.",
    )
    parser.add_argument(
        "--print-full-normalized",
        action="store_true",
        help="Print full normalized JSON to stdout",
    )
    parser.add_argument(
        "--print-report-messages",
        action="store_true",
        help="Print normalization report messages to stdout",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    scenario_dir = Path(args.scenario_dir).resolve() if args.scenario_dir else None
    gt_mapping = Path(args.gt_mapping).resolve() if args.gt_mapping else None
    meta_path = Path(args.meta_path).resolve() if args.meta_path else None
    burr_root = Path(args.burr_root).resolve()

    stem = input_path.stem

    raw = read_json(input_path)

    print_section("INPUT")
    print(f"input_path: {input_path}")
    print(f"out_dir: {out_dir}")
    if scenario_dir:
        print(f"scenario_dir: {scenario_dir}")
    if gt_mapping:
        print(f"gt_mapping: {gt_mapping}")
    print(f"burr_root: {burr_root}")

    print_section("RAW TOP-LEVEL COUNTS")
    print(json.dumps(summarize_top_level_counts(raw), indent=2, ensure_ascii=False))

    normalized = normalize_model_output_robust(raw)

    normalized_path = out_dir / f"{stem}.normalized.json"
    write_json(normalized_path, normalized)

    report = ((normalized.get("extras") or {}).get("normalization_report") or {})
    report_path = out_dir / f"{stem}.normalization_report.json"
    write_json(report_path, report)

    print_section("NORMALIZED TOP-LEVEL COUNTS")
    print(json.dumps(summarize_top_level_counts(normalized), indent=2, ensure_ascii=False))

    print_section("NORMALIZATION SUMMARY")
    summary = {
        "ok": report.get("ok", True),
        "num_messages": report.get("num_messages", len(report.get("messages", []) or [])),
        "by_level": report.get("by_level", {}),
        "by_code": report.get("by_code", {}),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.print_report_messages:
        print_preview("NORMALIZATION REPORT MESSAGES", report.get("messages", []), limit=20000)

    print_preview("NORMALIZED DATA PROPERTIES", normalized.get("data_properties", []), limit=8000)
    print_preview("NORMALIZED DATA PROPERTY MAPPINGS", normalized.get("data_property_mappings", []), limit=8000)
    print_preview("NORMALIZED OBJECT PROPERTIES", normalized.get("object_properties", []), limit=8000)
    print_preview("NORMALIZED OBJECT PROPERTY MAPPINGS", normalized.get("object_property_mappings", []), limit=8000)

    if args.print_full_normalized:
        print_preview("FULL NORMALIZED JSON", normalized, limit=200000)

    draft = None
    draft_error = None

    try:
        draft = OntologyDraft.from_dict(normalized, already_normalized=True)
    except Exception as e:
        draft_error = safe_exception_payload(e)

    if draft_error is not None:
        draft_error_path = out_dir / f"{stem}.draft_error.json"
        write_json(draft_error_path, draft_error)

        print_section("DRAFT CONSTRUCTION FAILED")
        print(json.dumps(draft_error, indent=2, ensure_ascii=False))
        return

    draft_path = out_dir / f"{stem}.draft.json"
    write_json(draft_path, draft.to_dict())

    print_section("DRAFT CONSTRUCTION OK")
    print(f"draft_path: {draft_path}")

    validate_ok, validate_errors = draft.validate()
    validation = {
        "ok": validate_ok,
        "num_errors": len(validate_errors),
        "errors": validate_errors,
    }
    validation_path = out_dir / f"{stem}.validation.json"
    write_json(validation_path, validation)

    print_section("DRAFT VALIDATION")
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    burr_mapping = None
    burr_mapping_path: Optional[Path] = None

    try:
        burr_mapping = draft.to_burr_mapping()
        burr_mapping_path = out_dir / f"{stem}.burr_mapping.json"
        write_json(burr_mapping_path, burr_mapping)

        print_section("BURR MAPPING TOP-LEVEL COUNTS")
        print(json.dumps(summarize_top_level_counts(burr_mapping), indent=2, ensure_ascii=False))
        print(f"burr_mapping_path: {burr_mapping_path}")

        print_preview("BURR MAPPING DATA PROPERTIES", burr_mapping.get("data_properties", []), limit=8000)
        print_preview("BURR MAPPING OBJECT PROPERTIES", burr_mapping.get("object_properties", []), limit=8000)

    except Exception as e:
        burr_error = safe_exception_payload(e)
        burr_error_path = out_dir / f"{stem}.burr_mapping_error.json"
        write_json(burr_error_path, burr_error)

        print_section("BURR MAPPING CONVERSION FAILED")
        print(json.dumps(burr_error, indent=2, ensure_ascii=False))
        return

    # --------------------------------------------------------
    # Optional Burr comparison
    # --------------------------------------------------------
    if scenario_dir is not None and burr_mapping_path is not None:
        print_section("RUNNING BURR COMPARISON")

        try:
            compare_result = run_compare(
                scenario_dir=scenario_dir,
                pred_mapping_path=burr_mapping_path,
                gt_mapping_path=gt_mapping,
                meta_path=meta_path,
                burr_root=burr_root,
                database_name=args.database_name,
            )

            compare_json_path = out_dir / f"{stem}.compare.json"
            write_json(compare_json_path, compare_result)

            compare_md_path = out_dir / f"{stem}.compare.md"
            write_text(compare_md_path, build_compare_markdown(compare_result))

            print(json.dumps(compare_result, indent=2, ensure_ascii=False))
            print(f"compare_json_path: {compare_json_path}")
            print(f"compare_md_path: {compare_md_path}")

        except Exception as e:
            compare_error = safe_exception_payload(e)
            compare_error_path = out_dir / f"{stem}.compare_error.json"
            write_json(compare_error_path, compare_error)

            print_section("BURR COMPARISON FAILED")
            print(json.dumps(compare_error, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()