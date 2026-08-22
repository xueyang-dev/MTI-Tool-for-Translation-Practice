"""交付状态机、人工处理记录与定点重译。

交付状态：draft -> review_required -> approved/final
- 翻译完成但有 blocking -> review_required；
- draft 资产可下载，但不得显示为最终交付完成；
- 人工处理记录（finding ID / action / note / timestamp）全部落盘；
- 只有 blocking 被解决或明确接受风险后才能进入 final；
- retranslate_segments 抽取自 scripts/fix_segments.py 的能力（不破坏原脚本）。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

DELIVERY_STATUSES = ("draft", "review_required", "approved", "final")
_HUMAN_ACTIONS = ("human_fixed", "accepted_risk", "retranslated",
                  "approve_final", "bypass_freeze")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def finding_id(f: Dict[str, Any], index: Optional[int] = None) -> str:
    """稳定 finding ID：优先用已有 id，否则由内容确定性生成（不依赖 reason 文本顺序）。"""
    existing = f.get("id")
    if existing:
        return str(existing)
    payload = json.dumps({
        "type": f.get("type"),
        "entry_id": f.get("entry_id"),
        "segment_index": f.get("segment_index"),
        "reason": f.get("reason"),
    }, ensure_ascii=False, sort_keys=True)
    return "f-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def unresolved_findings(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """未解决且需要人工处理的 findings（blocking / actionable，未被标记 resolved）。"""
    out = []
    for f in state.get("findings") or []:
        if f.get("resolved"):
            continue
        if f.get("severity") in ("blocking", "actionable"):
            out.append(f)
    return out


def unresolved_blocking(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [f for f in unresolved_findings(state) if f.get("severity") == "blocking"]


def add_human_action(state: Dict[str, Any], finding_id_: str, action: str,
                     note: str = "", actor: str = "user") -> Dict[str, Any]:
    state.setdefault("human_actions", []).append({
        "finding_id": finding_id_,
        "action": action,
        "note": note,
        "timestamp": now_iso(),
        "actor": actor,
    })
    return state


def mark_findings(state: Dict[str, Any], finding_ids: List[str], action: str,
                  note: str = "", actor: str = "user") -> Tuple[Dict[str, Any], List[str]]:
    """标记指定 findings 为已处理，并写入人工处理记录。返回 (state, marked_ids)。"""
    ids = set(finding_ids or [])
    marked: List[str] = []
    for f in state.get("findings") or []:
        fid = finding_id(f)
        if fid in ids and not f.get("resolved"):
            f["resolved"] = True
            f["resolution"] = {"action": action, "note": note,
                               "timestamp": now_iso(), "actor": actor}
            add_human_action(state, fid, action, note, actor)
            marked.append(fid)
    return state, marked


def compute_delivery_status(state: Dict[str, Any]) -> str:
    """由当前状态推导交付状态；final/approved 只能由人工确认产生。"""
    if not state.get("p2_done"):
        return "draft"
    if unresolved_blocking(state):
        return "review_required"
    current = state.get("delivery_status")
    if current in ("approved", "final"):
        return current
    return "draft"


def approve_delivery(state: Dict[str, Any], note: str = "", actor: str = "user",
                     accept_blocking: bool = False) -> Tuple[Dict[str, Any], bool, List[str]]:
    """人工交付确认 -> final。

    - 存在未解决 blocking 且未接受风险 -> 拒绝进入 final，返回错误说明；
    - accept_blocking=True：把所有未解决 blocking 记录为 accepted_risk 后进入 final；
    - 全部人工处理记录保存到 state["human_actions"]。
    """
    blockers = unresolved_blocking(state)
    if blockers:
        if not accept_blocking:
            ids = "、".join(finding_id(f) for f in blockers)
            return state, False, [f"存在未解决的 blocking 问题，不能进入 final：{ids}"]
        for f in blockers:
            state, _ = mark_findings(state, [finding_id(f)], "accepted_risk",
                                     note or "接受风险（人工确认）", actor)
    state["delivery_status"] = "final"
    state["stage"] = "FINAL"
    # Delivery approval is document-scoped authority.  It does not prove that
    # the user inspected and accepted every segment, so segment-level
    # human_accepted fields remain unchanged.
    state["delivery_approved_by_human"] = True
    state["delivery_approval"] = {
        "timestamp": now_iso(), "actor": actor, "note": note,
    }
    add_human_action(state, "*delivery*", "approve_final", note, actor)
    return state, True, []


def retranslate_segments(
    job_id: str,
    indexes: List[int],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str,
    style_rules: str = "",
    glossary: Optional[List[Dict[str, Any]]] = None,
    on_status=None,
    on_caption=None,
    actor: str = "user",
) -> Tuple[Dict[str, Any], List[int]]:
    """重新翻译指定段落（抽取自 scripts/fix_segments.py 的能力）。

    每段：前后文 + 批次翻译 + 完整性把关 + 自动修复一轮；
    保留并关闭该段旧问题，另存最终复验 findings，重算统计与交付状态。
    """
    import core

    state = core.load_job_state(job_id)
    if state is None:
        raise ValueError(f"找不到任务 {job_id}")
    paras, pairs = state["paras"], state["pairs"]
    indexes = sorted({int(i) for i in indexes if 0 <= int(i) < len(pairs)})
    if not indexes:
        return state, []
    glossary = core.normalize_glossary(
        glossary if glossary is not None else state.get("glossary") or [])
    glossary_text = core.glossary_block(glossary)

    fixed: List[int] = []
    for idx in indexes:
        src = pairs[idx]["source"]
        ctx_prev = paras[max(0, idx - 2):idx]
        ctx_next = paras[idx + 1:idx + 3]
        try:
            tgt = core.translate_batch([src], ctx_prev, ctx_next, glossary_text,
                                       style_rules, target_lang, provider, api_key,
                                       model)[0]
            tgt = core.clean_xml_chars(tgt).replace("\n", " ")
            section_profile = core._batch_section_profile(
                state.get("document_profile"), idx, 1)
            findings = core.check_translation_batch(
                [src], [tgt], glossary, target_lang,
                section_profile=section_profile)
            fixable = [f for f in findings if f["severity"] in ("blocking", "actionable")]
            if fixable:
                repaired = core.repair_batch([src], [tgt], fixable, glossary_text,
                                             style_rules, target_lang, provider,
                                             api_key, model)
                if repaired and repaired[0].strip() \
                        and not core.is_incomplete_translation(src, repaired[0]):
                    tgt = core.clean_xml_chars(repaired[0]).replace("\n", " ")
            remaining = core.check_translation_batch(
                [src], [tgt], glossary, target_lang,
                section_profile=section_profile)
            pairs[idx]["target"] = tgt
            pairs[idx]["initial_target"] = tgt
            pairs[idx]["from_tm"] = False
            pairs[idx]["reviewed"] = False  # 重译后需重新审校，不进 TMX final memory
            pairs[idx]["review_status"] = "not_reviewed"
            pairs[idx]["target_provenance"] = "generated"
            for key in ("accepted_target", "human_accepted", "accepted_by_human"):
                pairs[idx].pop(key, None)
            for old in state.get("findings", []):
                if old.get("segment_index") != idx or old.get("resolved") \
                        or old.get("severity") not in ("blocking", "actionable"):
                    continue
                old["resolved"] = True
                old["resolution"] = {
                    "action": "retranslated", "note": f"重新翻译段 {idx}",
                    "timestamp": now_iso(), "actor": actor,
                }
                add_human_action(
                    state, finding_id(old), "retranslated", f"重新翻译段 {idx}",
                    actor)
            for finding in remaining:
                state["findings"].append({
                    **finding, "segment_index": idx, "segment_id": idx})
            add_human_action(state, f"segment:{idx}", "retranslated",
                             f"重新翻译段 {idx}", actor)
            fixed.append(idx)
            if on_caption:
                on_caption(f"✅ 段 {idx} 已重译（{len(src)} -> {len(tgt)} 字符）")
        except Exception as e:
            if on_caption:
                on_caption(f"⚠️ 段 {idx} 重译失败：{str(e)[:120]}")

    if fixed:
        from . import knowledge
        state["knowledge_candidates"] = knowledge.discard_candidates_for_segments(
            state.get("knowledge_candidates") or [], fixed)
    stats = state.setdefault("review_stats", {})
    stats["blocking"] = sum(1 for f in state["findings"]
                            if f["severity"] == "blocking" and not f.get("resolved"))
    stats["actionable"] = sum(1 for f in state["findings"]
                              if f["severity"] == "actionable" and not f.get("resolved"))
    stats["informational"] = sum(1 for f in state["findings"]
                                 if f["severity"] == "informational" and not f.get("resolved"))
    state["has_blocking"] = stats["blocking"] > 0
    if fixed:
        # Re-translation changes the released document; the old document-level
        # approval no longer covers the new content.
        state["delivery_status"] = "draft"
        state["delivery_approved_by_human"] = False
        state["delivery_approval"] = None
        if state.get("stage") in ("FINAL", "REVIEW_REQUIRED"):
            state["stage"] = "REVIEW_REQUIRED" if state["has_blocking"] else "TRANSLATED"
    state["delivery_status"] = compute_delivery_status(state)
    core.save_job_state(job_id, state)
    return state, fixed
