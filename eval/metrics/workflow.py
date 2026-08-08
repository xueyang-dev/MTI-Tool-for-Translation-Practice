"""流程指标：审校通过率、重译率、TM 复用率、stale 段数。"""
from __future__ import annotations

from typing import Any, Dict


def compute_workflow_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    pairs = state.get("pairs") or []
    n = max(len(pairs), 1)
    reviewed = sum(1 for p in pairs if p.get("reviewed"))
    actions = state.get("human_actions") or []
    retranslated = sum(1 for a in actions if a.get("action") == "retranslated")
    stale = sum(1 for p in pairs if p.get("stale_due_to_glossary"))
    return {
        "total_segments": len(pairs),
        "review_pass_rate": round(reviewed / n, 4),
        "reviewed_segments": reviewed,
        "retranslation_rate": round(retranslated / n, 4),
        "retranslated_segments": retranslated,
        "tm_reuse_rate": round(state.get("tm_used_count", 0) / n, 4),
        "tm_reused_segments": state.get("tm_used_count", 0),
        "stale_segments": stale,
        "delivery_status": state.get("delivery_status", "draft"),
    }
