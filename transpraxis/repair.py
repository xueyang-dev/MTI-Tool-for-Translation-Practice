"""Formal-target / shadow-target repair lifecycle."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence


def create_overlay(
    formal_targets: Sequence[str],
    shadow_targets: Sequence[str],
    findings: Sequence[Dict[str, Any]],
    source: str,
) -> Dict[str, Any]:
    """Create a pending repair overlay without mutating the formal target."""
    return {
        "source": source,
        "status": "pending",
        "formal_targets": list(formal_targets),
        "shadow_targets": list(shadow_targets),
        "finding_indexes": [item.get("segment_index") for item in findings],
    }


def evaluate_overlay(
    overlay: Dict[str, Any],
    deterministic_findings: Sequence[Dict[str, Any]],
    blind_findings: Sequence[Dict[str, Any]] = (),
    blind_failed: bool = False,
) -> Dict[str, Any]:
    """Promote only a clean overlay; otherwise keep the formal target intact."""
    severe = lambda finding: finding.get("severity") in ("blocking", "actionable")
    if any(severe(item) for item in deterministic_findings):
        overlay["status"] = "rejected"
        overlay["rejection"] = "deterministic_qa"
    elif blind_failed:
        overlay["status"] = "rejected"
        overlay["rejection"] = "blind_review_failed"
    elif any(severe(item) for item in blind_findings):
        overlay["status"] = "rejected"
        overlay["rejection"] = "blind_review"
    else:
        overlay["status"] = "accepted"
    overlay["deterministic_findings"] = [dict(item) for item in deterministic_findings]
    overlay["blind_findings"] = [dict(item) for item in blind_findings]
    return overlay


def promoted_targets(overlay: Dict[str, Any]) -> List[str]:
    """Return candidate targets only after explicit overlay acceptance."""
    if overlay.get("status") == "accepted":
        return list(overlay.get("shadow_targets") or [])
    return list(overlay.get("formal_targets") or [])
