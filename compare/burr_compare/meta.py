from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_BURR_META: Dict[str, Any] = {
    "relation_prefix": "base",
    "prefixes": [
        {"prefix": "base", "uri": "/base/"},
    ],
}


def ensure_burr_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Make meta compatible with Burr parser expectations.

    Keeps the function intentionally small and conservative.
    """
    if not meta:
        return dict(DEFAULT_BURR_META)

    fixed = dict(meta)
    relation_prefix = fixed.get("relation_prefix") or DEFAULT_BURR_META["relation_prefix"]
    prefixes = fixed.get("prefixes") or []
    if not any(p.get("prefix") == relation_prefix for p in prefixes if isinstance(p, dict)):
        prefixes = list(prefixes) + [
            {
                "prefix": relation_prefix,
                "uri": f"/{relation_prefix}/",
            }
        ]
    fixed["relation_prefix"] = relation_prefix
    fixed["prefixes"] = prefixes
    return fixed
