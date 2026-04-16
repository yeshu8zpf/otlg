from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .helpers import as_list, as_str, safe_dict


@dataclass
class NormalizationMessage:
    level: str
    code: str
    message: str
    path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizationReport:
    ok: bool = True
    messages: List[NormalizationMessage] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        out = {"ok": self.ok, "num_messages": len(self.messages)}
        by_level: Dict[str, int] = {}
        by_code: Dict[str, int] = {}
        for m in self.messages:
            by_level[m.level] = by_level.get(m.level, 0) + 1
            by_code[m.code] = by_code.get(m.code, 0) + 1
        out["by_level"] = by_level
        out["by_code"] = by_code
        out["stats"] = self.stats
        return out


def get_normalization_report(obj: Dict[str, Any]) -> NormalizationReport:
    raw = safe_dict(obj.get("normalization_report"))
    issues = []
    for x in as_list(raw.get("issues")):
        d = safe_dict(x)
        issues.append(
            NormalizationMessage(
                level=as_str(d.get("level")) or "info",
                code=as_str(d.get("code")) or "UNKNOWN",
                message=as_str(d.get("message")),
                path=d.get("path"),
                payload=safe_dict(d.get("payload")),
            )
        )
    stats = {
        "num_errors": raw.get("num_errors", 0),
        "num_warnings": raw.get("num_warnings", 0),
        "num_infos": raw.get("num_infos", 0),
    }
    ok = stats["num_errors"] == 0
    return NormalizationReport(ok=ok, messages=issues, stats=stats)
