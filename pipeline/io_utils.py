from __future__ import annotations

import json
import shutil
import traceback
from pathlib import Path
from typing import Any, Dict, Optional


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path) -> Optional[Any]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_copy(path: Path | str | None, dst: Path) -> None:
    if not path:
        return
    src = Path(path)
    if src.exists() and src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def safe_exception_payload(e: Exception) -> Dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
    }
