from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import uuid


@dataclass
class Hypothesis:
    kind: str
    statement: str
    confidence: float
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    source_tools: List[str] = field(default_factory=list)
    status: str = "proposed"   # proposed / verified / rejected / conflicted / needs_revision
    conflicts_with: List[str] = field(default_factory=list)
    canonical_key: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    verification_history: List[Dict[str, Any]] = field(default_factory=list)
    revision_hints: List[Dict[str, Any]] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"H-{uuid.uuid4().hex[:10]}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def target_key(self) -> Optional[str]:
        target_type = self.payload.get("target_type")
        target_id = self.payload.get("target_id")
        if target_type and target_id:
            return f"{target_type}:{target_id}"
        return self.canonical_key


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

    def mark_verified(self, hypothesis_id: str, note: str = "") -> None:
        h = self.items[hypothesis_id]
        h.status = "verified"
        if note:
            h.verification_history.append({"result": "verified", "note": note})

    def mark_rejected(self, hypothesis_id: str, reason: str) -> None:
        h = self.items[hypothesis_id]
        h.status = "rejected"
        h.verification_history.append({"result": "rejected", "reason": reason})
        h.evidence.append({"type": "rejection_reason", "value": reason})

    def mark_needs_revision(self, hypothesis_id: str, reason: str, issue: Optional[Dict[str, Any]] = None) -> None:
        h = self.items[hypothesis_id]
        if h.status != "rejected":
            h.status = "needs_revision"
        entry = {"result": "needs_revision", "reason": reason}
        if issue is not None:
            entry["issue"] = issue
        h.verification_history.append(entry)

    def add_revision_hint(self, hypothesis_id: str, hint: Dict[str, Any]) -> None:
        self.items[hypothesis_id].revision_hints.append(hint)

    def add_conflict(self, left_id: str, right_id: str) -> None:
        if right_id not in self.items[left_id].conflicts_with:
            self.items[left_id].conflicts_with.append(right_id)
        if left_id not in self.items[right_id].conflicts_with:
            self.items[right_id].conflicts_with.append(left_id)

        if self.items[left_id].status not in {"rejected", "verified"}:
            self.items[left_id].status = "conflicted"
        if self.items[right_id].status not in {"rejected", "verified"}:
            self.items[right_id].status = "conflicted"

    def index_by_target(self) -> Dict[str, List[Hypothesis]]:
        idx: Dict[str, List[Hypothesis]] = {}
        for h in self.items.values():
            key = h.target_key
            if not key:
                continue
            idx.setdefault(key, []).append(h)
        return idx

    def find_by_target(self, target_type: str, target_id: str) -> List[Hypothesis]:
        key = f"{target_type}:{target_id}"
        return self.index_by_target().get(key, [])

    def attach_verification_issue(
        self,
        issue: Dict[str, Any],
        *,
        target_type: Optional[str],
        target_id: Optional[str],
    ) -> None:
        if not target_type or not target_id:
            return

        matched = self.find_by_target(target_type, target_id)
        if not matched:
            return

        code = issue.get("code", "UNKNOWN")
        message = issue.get("message", "")
        level = issue.get("level", "error")

        for h in matched:
            h.verification_history.append({
                "result": "issue_attached",
                "level": level,
                "code": code,
                "message": message,
                "issue": issue,
            })

            if level == "error":
                h.status = "needs_revision" if h.status != "rejected" else h.status
            elif level == "warning" and h.status == "proposed":
                h.status = "needs_revision"

    def _infer_target_from_issue(self, issue: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        ctx = issue.get("context", {}) or {}
        code = issue.get("code", "")

        if "class_id" in ctx:
            return "class", ctx["class_id"]

        if "property_id" in ctx:
            if code.startswith("DATA_PROPERTY") or "DATA_PROPERTY" in code:
                return "data_property", ctx["property_id"]
            if code.startswith("OBJECT_PROPERTY") or "OBJECT_PROPERTY" in code:
                return "object_property", ctx["property_id"]
            # fallback
            return "mapping", ctx["property_id"]

        if "from_class" in ctx:
            return "class", ctx["from_class"]
        if "to_class" in ctx:
            return "class", ctx["to_class"]

        return None, None

    def resolve_from_verifier_report(self, report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not report:
            return {"num_attached": 0, "num_revision_hints": 0}

        attached = 0
        revision_hints = 0

        all_issues = []
        all_issues.extend(report.get("errors", []) or [])
        all_issues.extend(report.get("warnings", []) or [])

        for issue in all_issues:
            target_type, target_id = self._infer_target_from_issue(issue)
            self.attach_verification_issue(issue, target_type=target_type, target_id=target_id)

            if target_type and target_id and self.find_by_target(target_type, target_id):
                attached += 1

            hint = self._issue_to_revision_hint(issue, target_type=target_type, target_id=target_id)
            if hint and target_type and target_id:
                for h in self.find_by_target(target_type, target_id):
                    self.add_revision_hint(h.id, hint)
                    self.mark_needs_revision(h.id, hint["instruction"], issue=issue)
                    revision_hints += 1

        return {
            "num_attached": attached,
            "num_revision_hints": revision_hints,
        }

    def _issue_to_revision_hint(
        self,
        issue: Dict[str, Any],
        *,
        target_type: Optional[str],
        target_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        code = issue.get("code", "")
        ctx = issue.get("context", {}) or {}

        if code == "MISSING_CLASS_MAPPING":
            return {
                "target_type": "class",
                "target_id": ctx.get("class_id"),
                "instruction": f"Add a class_mapping for accepted class {ctx.get('class_id')}.",
                "repair_type": "add_mapping",
            }

        if code == "MISSING_DATA_PROPERTY_MAPPING":
            return {
                "target_type": "data_property",
                "target_id": ctx.get("property_id"),
                "instruction": f"Add a data_property_mapping for accepted data property {ctx.get('property_id')}.",
                "repair_type": "add_mapping",
            }

        if code == "MISSING_OBJECT_PROPERTY_MAPPING":
            return {
                "target_type": "object_property",
                "target_id": ctx.get("property_id"),
                "instruction": f"Add an object_property_mapping for accepted object property {ctx.get('property_id')}.",
                "repair_type": "add_mapping",
            }

        if code == "DATA_PROPERTY_DOMAIN_MISMATCH":
            return {
                "target_type": "data_property",
                "target_id": ctx.get("property_id"),
                "instruction": (
                    f"Revise the data property mapping/domain so that mapping from_class "
                    f"matches declared domain_class={ctx.get('property_domain')}."
                ),
                "repair_type": "fix_domain",
            }

        if code == "OBJECT_PROPERTY_DOMAIN_MISMATCH":
            return {
                "target_type": "object_property",
                "target_id": ctx.get("property_id"),
                "instruction": (
                    f"Revise the object property domain or mapping from_class so it matches "
                    f"declared domain_class={ctx.get('property_domain')}."
                ),
                "repair_type": "fix_domain",
            }

        if code == "OBJECT_PROPERTY_RANGE_MISMATCH":
            return {
                "target_type": "object_property",
                "target_id": ctx.get("property_id"),
                "instruction": (
                    f"Revise the object property range or mapping to_class so it matches "
                    f"declared range_class={ctx.get('property_range')}."
                ),
                "repair_type": "fix_range",
            }

        if code == "OBJECT_PROPERTY_JOIN_PATH_MISMATCH":
            return {
                "target_type": "object_property",
                "target_id": ctx.get("property_id"),
                "instruction": (
                    f"Reconcile object_property.join_paths and object_property_mapping.joins "
                    f"for {ctx.get('property_id')}."
                ),
                "repair_type": "fix_join_path",
            }

        return None

    def build_revision_guidance(self, max_items: int = 20) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for h in self.items.values():
            if not h.revision_hints:
                continue
            for hint in h.revision_hints:
                rows.append({
                    "hypothesis_id": h.id,
                    "kind": h.kind,
                    "status": h.status,
                    "target_key": h.target_key,
                    "statement": h.statement,
                    "instruction": hint.get("instruction"),
                    "repair_type": hint.get("repair_type"),
                    "confidence": h.confidence,
                })

        rows.sort(key=lambda x: (x["status"] != "needs_revision", -float(x["confidence"])))
        return rows[:max_items]

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
            "revision_guidance": self.build_revision_guidance(),
        }