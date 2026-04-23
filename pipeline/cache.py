from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ontology_draft import OntologyDraft

from .io_utils import read_json, read_text


def load_json_if_exists(path: Path) -> Optional[Any]:
    if path.exists() and path.is_file():
        return read_json(path)
    return None


def try_load_cached_run(out_dir: Path) -> Optional[Tuple[
    OntologyDraft,
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
]]:
    raw_model_path = out_dir / "raw_model.json"
    normalized_path = out_dir / "normalized.json"
    draft_path = out_dir / "draft.json"
    validation_path = out_dir / "validation.json"
    verifier_path = out_dir / "verifier.json"
    mapping_path = out_dir / "mapping.json"
    meta_path = out_dir / "meta.json"

    required = [
        raw_model_path,
        normalized_path,
        draft_path,
        validation_path,
        verifier_path,
        mapping_path,
        meta_path,
    ]
    if not all(p.exists() and p.is_file() for p in required):
        return None

    raw_model_json = read_json(raw_model_path)
    normalized_model_json = read_json(normalized_path)
    draft_json = read_json(draft_path)
    validation_payload = read_json(validation_path)
    verifier_payload = read_json(verifier_path)
    burr_mapping = read_json(mapping_path)
    meta = read_json(meta_path)

    if not isinstance(raw_model_json, dict):
        return None
    if not isinstance(normalized_model_json, dict):
        return None
    if not isinstance(draft_json, dict):
        return None
    if not isinstance(validation_payload, dict):
        return None
    if not isinstance(verifier_payload, dict):
        return None
    if not isinstance(burr_mapping, dict):
        return None
    if not isinstance(meta, dict):
        return None

    draft = OntologyDraft.from_dict(draft_json, already_normalized=True)

    tool_artifacts = {
        "schema_profile": load_json_if_exists(out_dir / "schema_profile.json"),
        "instance_profile": load_json_if_exists(out_dir / "instance_profile.json"),
        "hypotheses": load_json_if_exists(out_dir / "hypotheses.json"),
        "tool_context": load_json_if_exists(out_dir / "tool_context.json") or {},
        "prompt": read_text(out_dir / "prompt.md") if (out_dir / "prompt.md").exists() else "",
        "verification_feedback": meta.get("verification_feedback"),
    }

    return (
        draft,
        burr_mapping,
        meta,
        raw_model_json,
        normalized_model_json,
        validation_payload,
        verifier_payload,
        tool_artifacts,
    )
