"""统一报告组装：多维指标 + 臂间增量，不合成单一 quality_score。"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _scalar_delta(a: Dict[str, Any], b: Dict[str, Any],
                  keys: Iterable[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = round(vb - va, 4)
    return out


def compute_deltas(runs: Dict[str, Dict[str, Any]],
                   pairs: List[str]) -> Dict[str, Dict[str, Any]]:
    """按给定配对计算各指标块增量（如 A→B、A→C、B→D、A→D）。"""
    blocks = ("terminology", "qa", "workflow")
    deltas: Dict[str, Dict[str, Any]] = {}
    for name in pairs:
        left, right = name.split("_to_")
        if left not in runs or right not in runs:
            continue
        out: Dict[str, Any] = {}
        for block in blocks:
            keys = [k for k in (runs[right].get(block) or {}).keys()
                    if k not in ("per_term",)]
            out[block] = _scalar_delta(runs[left].get(block) or {},
                                       runs[right].get(block) or {}, keys)
        deltas[name] = out
    return deltas


def build_report(meta: Dict[str, Any],
                 runs: Dict[str, Dict[str, Any]],
                 deltas: Dict[str, Dict[str, Any]],
                 human_review: Dict[str, Any]) -> Dict[str, Any]:
    """统一 evaluation-report.json：多维结果，无 quality_score。"""
    return {
        "meta": meta,
        "runs": runs,
        "deltas": deltas,
        "human_review": human_review,
    }
