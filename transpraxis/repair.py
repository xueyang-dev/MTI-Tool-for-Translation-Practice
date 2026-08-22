"""Formal-target / shadow-target repair lifecycle."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence


def _content_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _input_hash(overlay: Dict[str, Any]) -> str:
    return _content_hash({
        "sources": list(overlay.get("input_sources") or []),
        "formal_targets": list(overlay.get("formal_targets") or []),
        "findings": list(overlay.get("input_findings") or []),
        "finding_segment_ids": list(overlay.get("finding_segment_ids") or []),
    })


def create_overlay(
    formal_targets: Sequence[str],
    shadow_targets: Sequence[str],
    findings: Sequence[Dict[str, Any]],
    source: str,
    sources: Sequence[str] = (),
    finding_segment_ids: Optional[Sequence[int]] = None,
) -> Dict[str, Any]:
    """Create a pending repair overlay without mutating the formal target."""
    formal = list(formal_targets)
    shadow = list(shadow_targets)
    finding_records = [dict(item) for item in findings or []]
    segment_ids = list(finding_segment_ids) if finding_segment_ids is not None else [
        item.get("segment_id", item.get("segment_index")) for item in finding_records
    ]
    if len(segment_ids) == len(finding_records):
        for item, segment_id in zip(finding_records, segment_ids):
            item["segment_id"] = segment_id
            item.pop("segment_index", None)
    return {
        "source": source,
        "status": "pending",
        "formal_targets": formal,
        "shadow_targets": shadow,
        "finding_segment_ids": segment_ids,
        "input_sources": list(sources or []),
        "input_findings": finding_records,
        "input_hash": _input_hash({
            "input_sources": list(sources or []),
            "formal_targets": formal,
            "input_findings": finding_records,
            "finding_segment_ids": segment_ids,
        }),
        "candidate_hash": _content_hash(shadow),
    }


def evaluate_overlay(
    overlay: Dict[str, Any],
    deterministic_findings: Sequence[Dict[str, Any]],
    blind_findings: Sequence[Dict[str, Any]] = (),
    blind_failed: bool = False,
    review_identity: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Promote only a clean overlay; otherwise keep the formal target intact."""
    severe = lambda finding: finding.get("severity") in ("blocking", "actionable")
    candidate_hash = overlay.get("candidate_hash")
    candidate_matches = candidate_hash == _content_hash(overlay.get("shadow_targets") or [])
    input_matches = not {"input_sources", "input_findings"}.issubset(overlay) \
        or overlay.get("input_hash") == _input_hash(overlay)
    identity_matches = review_identity is None or all(
        review_identity.get(key) == overlay.get(key)
        for key in ("input_hash", "candidate_hash")
    )
    if candidate_hash and not candidate_matches:
        overlay["status"] = "rejected"
        overlay["rejection"] = "candidate_hash_mismatch"
    elif not input_matches:
        overlay["status"] = "rejected"
        overlay["rejection"] = "input_hash_mismatch"
    elif not identity_matches:
        overlay["status"] = "rejected"
        overlay["rejection"] = "blind_review_identity_mismatch"
    elif any(severe(item) for item in deterministic_findings):
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
