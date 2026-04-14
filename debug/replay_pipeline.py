from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from normalize import normalize_model_output_robust
from ontology_draft import OntologyDraft
from burr_compare import run_compare
from ontology_tools.verifier_lite import MappingVerifierLite


# ============================================================
# IO helpers
# ============================================================

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists() and src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def safe_exception_payload(e: Exception) -> Dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
    }


# ============================================================
# Stage runners
# ============================================================

def stage_raw_to_normalized(in_dir: Path, out_dir: Path) -> Dict[str, Any]:
    raw = read_json(in_dir / "raw_model.json")
    normalized = normalize_model_output_robust(raw)
    write_json(out_dir / "normalized.json", normalized)
    return normalized


def stage_normalized_to_draft(in_dir: Path, out_dir: Path) -> Dict[str, Any]:
    normalized = read_json(in_dir / "normalized.json")
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)
    draft_dict = draft.to_dict()
    write_json(out_dir / "draft.json", draft_dict)
    return draft_dict


def stage_draft_validate(in_dir: Path, out_dir: Path) -> Dict[str, Any]:
    draft_payload = read_json(in_dir / "draft.json")
    draft = OntologyDraft.from_dict(draft_payload, already_normalized=True)
    ok, errors = draft.validate()
    validation = {
        "ok": ok,
        "num_errors": len(errors),
        "errors": errors,
    }
    write_json(out_dir / "validation.json", validation)
    return validation


def stage_draft_verify(in_dir: Path, out_dir: Path) -> Dict[str, Any]:
    draft_payload = read_json(in_dir / "draft.json")
    verifier = MappingVerifierLite()
    report = verifier.verify_draft_dict(draft_payload)
    write_json(out_dir / "verifier.json", report)
    return report


def stage_draft_to_mapping(in_dir: Path, out_dir: Path) -> Dict[str, Any]:
    draft_payload = read_json(in_dir / "draft.json")
    draft = OntologyDraft.from_dict(draft_payload, already_normalized=True)
    mapping = draft.to_burr_mapping()
    write_json(out_dir / "mapping.json", mapping)
    return mapping


def stage_mapping_compare(
    in_dir: Path,
    out_dir: Path,
    scenario_dir: Path,
    database_name: Optional[str] = None,
    meta_path: Optional[Path] = None,
) -> Dict[str, Any]:
    mapping_path = in_dir / "mapping.json"
    if not mapping_path.exists():
        raise FileNotFoundError(f"Missing mapping.json in {in_dir}")

    try:
        compare_result = run_compare(
            scenario_dir=scenario_dir,
            pred_mapping_path=mapping_path,
            gt_mapping_path=None,
            meta_path=meta_path,
            database_name=database_name or scenario_dir.name,
        )
        write_json(out_dir / "compare.json", compare_result)
        return compare_result
    except Exception as e:
        payload = safe_exception_payload(e)
        write_json(out_dir / "compare_error.json", payload)
        raise


# ============================================================
# Pipeline entrypoints
# ============================================================

def run_from_raw(in_dir: Path, out_dir: Path) -> None:
    normalized = stage_raw_to_normalized(in_dir, out_dir)
    draft = OntologyDraft.from_dict(normalized, already_normalized=True)
    write_json(out_dir / "draft.json", draft.to_dict())

    ok, errors = draft.validate()
    write_json(out_dir / "validation.json", {"ok": ok, "num_errors": len(errors), "errors": errors})

    verifier = MappingVerifierLite()
    verifier_report = verifier.verify_draft_dict(draft.to_dict())
    write_json(out_dir / "verifier.json", verifier_report)

    mapping = draft.to_burr_mapping()
    write_json(out_dir / "mapping.json", mapping)


def run_from_normalized(in_dir: Path, out_dir: Path) -> None:
    draft_payload = stage_normalized_to_draft(in_dir, out_dir)

    draft = OntologyDraft.from_dict(draft_payload, already_normalized=True)
    ok, errors = draft.validate()
    write_json(out_dir / "validation.json", {"ok": ok, "num_errors": len(errors), "errors": errors})

    verifier = MappingVerifierLite()
    verifier_report = verifier.verify_draft_dict(draft.to_dict())
    write_json(out_dir / "verifier.json", verifier_report)

    mapping = draft.to_burr_mapping()
    write_json(out_dir / "mapping.json", mapping)


def run_from_draft(in_dir: Path, out_dir: Path) -> None:
    validation = stage_draft_validate(in_dir, out_dir)
    verifier = stage_draft_verify(in_dir, out_dir)
    mapping = stage_draft_to_mapping(in_dir, out_dir)

    print("[INFO] validation summary:", validation["ok"], validation["num_errors"])
    print("[INFO] verifier summary:", verifier.get("ok"), verifier.get("num_errors", 0))
    print(
        "[INFO] mapping counts:",
        {
            "classes": len(mapping.get("classes", [])),
            "data_properties": len(mapping.get("data_properties", [])),
            "object_properties": len(mapping.get("object_properties", [])),
        },
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay pipeline stages from an existing outputs directory."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default='outputs/replay_from_draft_canonical',
        help="Existing outputs dir, e.g. outputs/tool_augmented",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default='outputs/replay_from_draft_canonical',
        help="Where to write replayed outputs, e.g. outputs/replay_1",
    )
    parser.add_argument(
        "--start-stage",
        type=str,
        default='mapping_compare',
        choices=[
            "raw_to_normalized",
            "normalized_to_draft",
            "draft_validate",
            "draft_verify",
            "draft_to_mapping",
            "mapping_compare",
            "all_from_raw",
            "all_from_normalized",
            "all_from_draft",
        ],
    )
    parser.add_argument(
        "--scenario-dir",
        type=str,
        default='burr_benchmark/real-world/mondial',
        help="Required for mapping_compare",
    )
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--meta-path",
        type=str,
        default=None,
    )

    args = parser.parse_args()

    in_dir = Path(args.input_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy upstream files for traceability
    for name in [
        "raw_model.json",
        "normalized.json",
        "draft.json",
        "validation.json",
        "verifier.json",
        "mapping.json",
        "meta.json",
        "prompt.md",
        "tool_context.json",
        "schema_profile.json",
    ]:
        copy_if_exists(in_dir / name, out_dir / f"upstream.{name}")

    try:
        if args.start_stage == "raw_to_normalized":
            stage_raw_to_normalized(in_dir, out_dir)

        elif args.start_stage == "normalized_to_draft":
            stage_normalized_to_draft(in_dir, out_dir)

        elif args.start_stage == "draft_validate":
            stage_draft_validate(in_dir, out_dir)

        elif args.start_stage == "draft_verify":
            stage_draft_verify(in_dir, out_dir)

        elif args.start_stage == "draft_to_mapping":
            stage_draft_to_mapping(in_dir, out_dir)

        elif args.start_stage == "mapping_compare":
            if not args.scenario_dir:
                raise ValueError("--scenario-dir is required for mapping_compare")
            stage_mapping_compare(
                in_dir=in_dir,
                out_dir=out_dir,
                scenario_dir=Path(args.scenario_dir).resolve(),
                database_name=args.database_name,
                meta_path=Path(args.meta_path).resolve() if args.meta_path else None,
            )

        elif args.start_stage == "all_from_raw":
            run_from_raw(in_dir, out_dir)

        elif args.start_stage == "all_from_normalized":
            run_from_normalized(in_dir, out_dir)

        elif args.start_stage == "all_from_draft":
            run_from_draft(in_dir, out_dir)

        print(f"[OK] replay completed: {args.start_stage}")
        print(f"[OK] outputs written to: {out_dir}")

    except Exception as e:
        write_json(out_dir / "failed.meta.json", safe_exception_payload(e))
        raise


if __name__ == "__main__":
    main()