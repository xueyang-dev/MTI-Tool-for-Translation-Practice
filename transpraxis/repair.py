"""Formal-target / shadow-target repair lifecycle."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Sequence


def _content_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_overlay(
    formal_targets: Sequence[str],
    shadow_targets: Sequence[str],
    findings: Sequence[Dict[str, Any]],
    source: str,
    sources: Sequence[str] = (),
) -> Dict[str, Any]:
    """Create a pending repair overlay without mutating the formal target."""
    formal = list(formal_targets)
    shadow = list(shadow_targets)
    return {
        "source": source,
        "status": "pending",
        "formal_targets": formal,
        "shadow_targets": shadow,
        "finding_indexes": [item.get("segment_id", item.get("segment_index"))
                             for item in findings],
        "input_hash": _content_hash({"sources": list(sources or []),
                                      "formal_targets": formal,
                                      "findings": list(findings or [])}),
        "candidate_hash": _content_hash(shadow),
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
