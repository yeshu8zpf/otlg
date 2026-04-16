from __future__ import annotations

from typing import Any, Dict, Optional


DEFAULT_BURR_META: Dict[str, Any] = {
    "relation_prefix": "base",
    "prefixes": [
        {"prefix": "base", "uri": "/base/"},
    ],
}


def ensure_burr_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not meta:
        return dict(DEFAULT_BURR_META)

    out = dict(DEFAULT_BURR_META)
    out.update(meta)

    prefixes = meta.get("prefixes")
    if not prefixes:
        out["prefixes"] = list(DEFAULT_BURR_META["prefixes"])

    return out