"""参考译文指标（可选 track）。

第一轮明确不做参考译文指标：文学翻译中参考译文不是唯一正确答案，
且需要可靠段落对齐。本模块只保留接口与说明，配置了 references 时明确报错，
避免"指标完整性"绑架第一轮实验。
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def compute_reference_metrics(state: Dict[str, Any],
                              references_path: Optional[str] = None) -> Dict[str, Any]:
    if references_path:
        raise NotImplementedError(
            "reference track 尚未启用：第一轮不做参考译文指标。"
            "后续接入时在此实现 ChrF/BLEU（辅助指标，不作为唯一答案）。")
    return {"enabled": False, "note": "第一轮无参考译文指标"}
