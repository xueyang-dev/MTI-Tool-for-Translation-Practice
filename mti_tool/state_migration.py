"""任务状态机与旧 state.json 迁移。

阶段（stage）：
    INGESTED -> PROFILED -> TERMS_PREPARED -> GLOSSARY_FROZEN -> TRANSLATED
    -> ANNOTATED -> REPORT_GENERATED -> REVIEW_REQUIRED / FINAL

兼容性：
- 旧任务只有 p1_done / p2_done / p3_done / annotations_done；
- migrate_state 只补默认值，不把旧任务虚假标记为 glossary 已冻结；
- 交付状态（delivery_status）默认 draft；旧任务即使全部完成也保持 draft，
  需要人工确认后才进入 final。
"""
from __future__ import annotations

from typing import Any, Dict

STAGES = (
    "INGESTED", "PROFILED", "TERMS_PREPARED", "GLOSSARY_FROZEN", "TRANSLATED",
    "ANNOTATED", "REPORT_GENERATED", "REVIEW_REQUIRED", "FINAL",
)

DELIVERY_STATUSES = ("draft", "review_required", "approved", "final")


def _default_new_fields() -> Dict[str, Any]:
    """新增字段的默认值（旧任务加载时补齐，避免 KeyError）。"""
    return {
        "stage": "INGESTED",
        "delivery_status": "draft",
        "document_profile": None,
        "profile_done": False,
        "profile_warnings": [],
        "auto_term_entries": [],
        "glossary": [],
        "glossary_draft": [],
        "glossary_frozen": None,
        "glossary_versions": [],
        "glossary_injection_log": [],
        "human_actions": [],
        "delivery_manifest": {},
        "exported_assets": [],
        "quality_mode": False,
        "quality_bypass": False,
        "delivery_notes": "",
    }


def derive_stage(state: Dict[str, Any]) -> str:
    """由现有里程碑标志推导当前阶段（不修改状态）。"""
    if not state.get("p1_done"):
        return "INGESTED"
    if not state.get("profile_done") and not state.get("p2_done"):
        return "PROFILED"
    if not state.get("p2_done"):
        if state.get("glossary_frozen"):
            return "GLOSSARY_FROZEN"
        if state.get("auto_term_entries") or state.get("auto_terms") or \
                state.get("glossary") or state.get("glossary_draft"):
            return "TERMS_PREPARED"
        return "PROFILED"
    if state.get("has_blocking"):
        return "REVIEW_REQUIRED"
    if state.get("p3_done") or not state.get("report_enabled", True):
        return "REPORT_GENERATED"
    if state.get("annotations_done"):
        return "ANNOTATED"
    return "TRANSLATED"


def derive_delivery_status(state: Dict[str, Any]) -> str:
    """由现有状态推导交付状态。

    规则：翻译完成且有 blocking -> review_required；
    其余保持 draft（final 只能由人工确认产生，旧任务不得自动变 final）。
    """
    if state.get("p2_done") and state.get("has_blocking"):
        return "review_required"
    return "draft"


def migrate_state(state: Any) -> Dict[str, Any]:
    """迁移旧任务状态：补默认字段、推导 stage 与 delivery_status。

    不修改 p1/p2/p3 等旧字段；不清空旧数据；glossary_frozen 保持 None。
    """
    if not isinstance(state, dict):
        return dict(_default_new_fields())
    out = dict(state)
    for key, default in _default_new_fields().items():
        if key not in out or out[key] is None:
            out[key] = default

    # 旧任务可能把新字段存成空串/空 dict，统一归一化
    if out.get("glossary") == {}:
        out["glossary"] = []
    if out.get("auto_term_entries") == {}:
        out["auto_term_entries"] = []

    out["stage"] = derive_stage(out)
    # 只在不显式设置过交付状态时推导；显式 final/approved 不覆盖
    if out.get("delivery_status") not in ("approved", "final"):
        out["delivery_status"] = derive_delivery_status(out)
    return out
