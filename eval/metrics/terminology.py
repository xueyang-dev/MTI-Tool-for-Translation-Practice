"""术语一致性指标（reference-free，机器可算）。

与具体运行代码无关：统一从 state.pairs + 冻结术语表计算，
四臂（A/B/C/D）使用同一套指标函数，保证可比。
"""
from __future__ import annotations

from typing import Any, Dict, List

from transpraxis import models
from transpraxis.terminology import term_matches


def compute_terminology_metrics(state: Dict[str, Any],
                                glossary_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算锁定术语的采纳率、禁止译名违反、保留失败、scope 冲突。"""
    pairs = state.get("pairs") or []
    entries = models.normalize_glossary(glossary_entries)
    total_src = total_adopted = 0
    forbidden_violations = 0
    preserve_failures = 0
    per_term: List[Dict[str, Any]] = []

    for e in entries:
        if e["status"] != "locked":
            continue
        if e["behavior"] == "preserve":
            fails = 0
            for p in pairs:
                src, tgt = p.get("source", ""), p.get("target", "")
                if term_matches(e["source"], src) \
                        and not term_matches(e["source"], tgt):
                    fails += 1
            preserve_failures += fails
            per_term.append({
                "term": e["source"], "behavior": "preserve", "failures": fails,
            })
            continue
        preferred = e.get("preferred") or e.get("target") or ""
        src_segs = [p for p in pairs if term_matches(e["source"], p.get("source", ""))]
        adopted = [p for p in src_segs if preferred
                   and term_matches(preferred, p.get("target", ""))]
        fb_hits = 0
        for p in src_segs:
            tgt = p.get("target", "")
            if any(fb and fb in tgt for fb in (e.get("forbidden") or [])):
                fb_hits += 1
        total_src += len(src_segs)
        total_adopted += len(adopted)
        forbidden_violations += fb_hits
        per_term.append({
            "term": e["source"],
            "preferred": preferred,
            "occurrences": len(src_segs),
            "adopted": len(adopted),
            "rate": round(len(adopted) / len(src_segs), 4) if src_segs else None,
            "forbidden_violations": fb_hits,
        })

    scope_conflicts = sum(1 for f in (state.get("findings") or [])
                          if f.get("conflict"))
    return {
        "locked_term_adoption_rate":
            round(total_adopted / total_src, 4) if total_src else None,
        "forbidden_term_violations": forbidden_violations,
        "preserve_failures": preserve_failures,
        "scope_conflicts": scope_conflicts,
        "per_term": per_term,
    }
