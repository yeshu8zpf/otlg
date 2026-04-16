from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizationIssue:
    level: str
    code: str
    message: str
    path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "level": self.level,
            "code": self.code,
            "message": self.message,
        }
        if self.path is not None:
            out["path"] = self.path
        if self.payload:
            out["payload"] = self.payload
        return out


@dataclass
class NormalizationCollector:
    issues: List[NormalizationIssue] = field(default_factory=list)

    def add(self, level: str, code: str, message: str, path: Optional[str] = None, **payload: Any) -> None:
        self.issues.append(
            NormalizationIssue(level=level, code=code, message=message, path=path, payload=payload)
        )

    def report(self) -> Dict[str, Any]:
        num_errors = sum(1 for x in self.issues if x.level == "error")
        num_warnings = sum(1 for x in self.issues if x.level == "warning")
        num_infos = sum(1 for x in self.issues if x.level == "info")
        return {
            "num_errors": num_errors,
            "num_warnings": num_warnings,
            "num_infos": num_infos,
            "issues": [x.to_dict() for x in self.issues],
        }
