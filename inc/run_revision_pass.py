from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from inc.draft_revision_engine import DraftRevisionEngine, RevisionEngineConfig
from pipeline.llm import call_llm_json_stream


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True)
    parser.add_argument("--step", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--api_url", default="https://www.aiapikey.net/v1/chat/completions")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--api_key", default="gpt")
    args = parser.parse_args()

    draft = read_json(Path(args.draft))
    incremental_step = read_json(Path(args.step))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = DraftRevisionEngine(RevisionEngineConfig())
    result = engine.run_revision_pass(
        draft=draft,
        incremental_step=incremental_step,
        call_llm_json_stream_fn=call_llm_json_stream,
        model=args.model,
        api_url=args.api_url,
        timeout=args.timeout,
        api_key=args.api_key,
        evidence_provider=None,
    )

    write_json(out_dir / "revision_targets.json", result["targets"])
    write_json(out_dir / "raw_revision_patch.json", result["raw_revision_patch"])
    write_json(out_dir / "normalized_revision_patch.json", result["normalized_revision_patch"])
    write_json(out_dir / "updated_draft.json", result["updated_draft"])
    write_json(out_dir / "revision_messages.json", result["messages"])
    if "llm_meta" in result:
        write_json(out_dir / "revision_llm_meta.json", result["llm_meta"])


if __name__ == "__main__":
    main()
