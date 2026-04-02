from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Hypothesis:
    kind: str
    statement: str
    confidence: float
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    source_tools: List[str] = field(default_factory=list)
    status: str = "proposed"
    conflicts_with: List[str] = field(default_factory=list)
    canonical_key: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"H-{uuid.uuid4().hex[:10]}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HypothesisStore:
    def __init__(self) -> None:
        self.items: Dict[str, Hypothesis] = {}

    def add(self, hypothesis: Hypothesis) -> None:
        self.items[hypothesis.id] = hypothesis

    def get(self, hypothesis_id: str) -> Hypothesis:
        return self.items[hypothesis_id]

    def list(self, *, kind: str | None = None, status: str | None = None) -> List[Hypothesis]:
        out = list(self.items.values())
        if kind is not None:
            out = [h for h in out if h.kind == kind]
        if status is not None:
            out = [h for h in out if h.status == status]
        return out

    def mark_verified(self, hypothesis_id: str) -> None:
        self.items[hypothesis_id].status = "verified"

    def mark_rejected(self, hypothesis_id: str, reason: str) -> None:
        h = self.items[hypothesis_id]
        h.status = "rejected"
        h.evidence.append({"type": "rejection_reason", "value": reason})

    def add_conflict(self, left_id: str, right_id: str) -> None:
        if right_id not in self.items[left_id].conflicts_with:
            self.items[left_id].conflicts_with.append(right_id)
        if left_id not in self.items[right_id].conflicts_with:
            self.items[right_id].conflicts_with.append(left_id)

    def summary(self) -> Dict[str, Any]:
        by_kind: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for h in self.items.values():
            by_kind[h.kind] = by_kind.get(h.kind, 0) + 1
            by_status[h.status] = by_status.get(h.status, 0) + 1
        return {
            "num_hypotheses": len(self.items),
            "by_kind": by_kind,
            "by_status": by_status,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypotheses": [h.to_dict() for h in self.items.values()],
            "summary": self.summary(),
        }
