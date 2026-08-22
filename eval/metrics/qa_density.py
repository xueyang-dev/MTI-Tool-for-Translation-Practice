"""QA 密度指标：blocking/actionable/informational 每千字符、自动修复率。"""
from __future__ import annotations

from typing import Any, Dict


def compute_qa_density(state: Dict[str, Any]) -> Dict[str, Any]:
    pairs = state.get("pairs") or []
    findings = state.get("findings") or []
    src_chars = sum(len(p.get("source", "")) for p in pairs)
    def _count(sev: str) -> int:
        return sum(1 for f in findings if f.get("severity") == sev)
    blocking, actionable, informational = _count("blocking"), \
        _count("actionable"), _count("informational")
    # 自动修复/审校调整：初译与终译不同的非 TM 段
    adjusted = sum(1 for p in pairs
                   if p.get("initial_target") and not p.get("from_tm")
                   and p.get("initial_target") != p.get("target"))
    translated = sum(1 for p in pairs if not p.get("from_tm"))
    stats = state.get("review_stats") or {}
    return {
        "source_chars": src_chars,
        "blocking_per_1k_chars": round(blocking / max(src_chars, 1) * 1000, 4),
        "actionable_per_1k_chars": round(actionable / max(src_chars, 1) * 1000, 4),
        "informational_per_1k_chars": round(informational / max(src_chars, 1) * 1000, 4),
        "blocking_total": blocking,
        "actionable_total": actionable,
        "informational_total": informational,
        "automatic_repair_rate":
            round(adjusted / max(translated, 1), 4) if translated else None,
        "adjusted_segments": adjusted,
        "review_failed_batches": stats.get("review_failed", 0),
    }
