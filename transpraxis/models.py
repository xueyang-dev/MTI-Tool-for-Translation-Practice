"""统一数据模型：DocumentProfile / SectionProfile / TermEvidence / GlossaryEntry / FrozenGlossary。

设计原则：
- 所有模型都是可 JSON 序列化的 TypedDict（与现有 state.json / Excel 导入兼容）；
- 每个模型提供统一的 normalize（补默认值、纠错、类型强制）与 validate（返回问题列表，
  由调用方决定降级策略，不抛异常）；
- glossary_hash 由规范化后的冻结条目确定性生成：条目顺序变化不影响哈希。
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, TypedDict

# ---------------- 常量 ----------------

BEHAVIORS = ("translate", "preserve")
STATUSES = ("candidate", "provisional", "locked", "rejected")
EVIDENCE_TYPES = ("user", "local_termbase", "project_override", "model_knowledge", "external")
SCOPES = ("global", "document", "section", "segment")

_DEFAULT_CONFIDENCE = 0.5


# ---------------- 基础工具 ----------------

def clean_str(value: Any, default: str = "", max_len: Optional[int] = None) -> str:
    """字符串清洗：None/非字符串 -> default；去首尾空白；可选截断。"""
    if value is None:
        return default
    if not isinstance(value, str):
        value = str(value)
    out = value.strip()
    if max_len is not None and len(out) > max_len:
        out = out[:max_len].rstrip()
    return out


def clean_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_float(value: Any, default: float = _DEFAULT_CONFIDENCE) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return max(0.0, min(1.0, f))


def clean_str_list(value: Any) -> List[str]:
    """字符串列表归一化：接受 list[str]、逗号/分号分隔字符串。"""
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[;；,，]", value)
    elif isinstance(value, (list, tuple)):
        parts = value
    else:
        return []
    return [clean_str(p) for p in parts if clean_str(p)]


def _stable_json(obj: Any) -> str:
    """键排序的稳定 JSON 序列化（用于确定性哈希与规范化比较）。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def stable_id(*parts: str, prefix: str = "t") -> str:
    """由内容确定性生成短 ID：相同内容永远得到相同 ID。"""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ---------------- SectionProfile / DocumentProfile ----------------

class SectionProfile(TypedDict, total=False):
    section_id: str
    start_segment: int
    end_segment: int
    topic: str
    domain: str
    style: str


class DocumentProfile(TypedDict, total=False):
    domain: str
    subdomain: str
    genre: str
    audience: str
    register: str
    style_constraints: str
    confidence: float
    sections: List[SectionProfile]


def default_document_profile() -> DocumentProfile:
    return {
        "domain": "",
        "subdomain": "",
        "genre": "",
        "audience": "",
        "register": "",
        "style_constraints": "",
        "confidence": 0.0,
        "sections": [],
    }


def normalize_section_profile(raw: Any, index: int = 0) -> Optional[SectionProfile]:
    if raw is None or not isinstance(raw, dict):
        return None
    start = clean_int(raw.get("start_segment"), default=-1)
    end = clean_int(raw.get("end_segment"), default=-1)
    if start < 0 or end < 0 or end < start:
        return None
    return {
        "section_id": clean_str(raw.get("section_id"), default=f"section-{index + 1}"),
        "start_segment": start,
        "end_segment": end,
        "topic": clean_str(raw.get("topic")),
        "domain": clean_str(raw.get("domain")),
        "style": clean_str(raw.get("style")),
    }


def normalize_document_profile(raw: Any) -> DocumentProfile:
    """归一化文档画像：补默认值、类型强制；无效 section 丢弃。"""
    base = default_document_profile()
    if not isinstance(raw, dict):
        return base
    out: DocumentProfile = {
        "domain": clean_str(raw.get("domain")),
        "subdomain": clean_str(raw.get("subdomain")),
        "genre": clean_str(raw.get("genre")),
        "audience": clean_str(raw.get("audience")),
        "register": clean_str(raw.get("register")),
        "style_constraints": clean_str(raw.get("style_constraints")),
        "confidence": clean_float(raw.get("confidence"), default=0.0),
        "sections": [],
    }
    raw_sections = raw.get("sections")
    if isinstance(raw_sections, list):
        for i, sec in enumerate(raw_sections):
            norm = normalize_section_profile(sec, index=i)
            if norm is not None:
                out["sections"].append(norm)
    return out


def validate_document_profile(profile: Optional[DocumentProfile]) -> List[str]:
    """返回问题列表；空列表表示可接受。domain 缺失/置信度过低视为有疑问。"""
    if not profile:
        return ["文档画像缺失"]
    errors = []
    if not profile.get("domain"):
        errors.append("文档画像缺少 domain（领域）")
    if (profile.get("confidence") or 0) < 0.2:
        errors.append("文档画像置信度过低，结论仅供参考")
    for sec in profile.get("sections") or []:
        if not sec.get("topic") and not sec.get("domain"):
            errors.append(f"章节 {sec.get('section_id', '?')} 缺少 topic/domain")
    return errors


# ---------------- TermEvidence ----------------

class TermEvidence(TypedDict, total=False):
    evidence_type: str
    source_name: str
    note: str
    quote: str
    url: str
    confidence: float


def normalize_evidence(raw: Any) -> Optional[TermEvidence]:
    """归一化证据条目。

    约束（防止模型伪造来源）：
    - model_knowledge 一律不允许附带 URL（有则清空并在 note 中说明）；
    - external 只有在真实外部 provider 返回了来源时才允许保存 URL；
      没有 URL 的 external 自动降级为 model_knowledge。
    """
    if raw is None or not isinstance(raw, dict):
        return None
    etype = clean_str(raw.get("evidence_type")).lower()
    if etype not in EVIDENCE_TYPES:
        etype = "model_knowledge"
    url = clean_str(raw.get("url"), max_len=2048)
    note = clean_str(raw.get("note"), max_len=2000)
    source_name = clean_str(raw.get("source_name"), max_len=200)

    if etype == "model_knowledge" and url:
        note = (note + "；[已清除疑似伪造 URL]").strip("；") if note else "[已清除疑似伪造 URL]"
        url = ""
    if etype == "external":
        if not url:
            etype = "model_knowledge"
            note = (note + "；[无真实外部来源，已降级为模型知识]").strip("；") \
                if note else "[无真实外部来源，已降级为模型知识]"
            source_name = ""
    return {
        "evidence_type": etype,
        "source_name": source_name,
        "note": note,
        "quote": clean_str(raw.get("quote"), max_len=2000),
        "url": url,
        "confidence": clean_float(raw.get("confidence")),
    }


def validate_evidence(ev: Optional[TermEvidence]) -> List[str]:
    if not ev:
        return ["证据条目缺失"]
    errors = []
    etype = ev.get("evidence_type")
    if etype not in EVIDENCE_TYPES:
        errors.append(f"非法 evidence_type：{etype!r}")
    if etype == "model_knowledge" and ev.get("url"):
        errors.append("model_knowledge 不允许附带 URL")
    if etype == "external" and not ev.get("url"):
        errors.append("external 证据必须有真实来源 URL")
    if etype in ("user", "local_termbase", "project_override") and not ev.get("source_name"):
        errors.append(f"{etype} 证据缺少 source_name")
    return errors


# ---------------- GlossaryEntry（术语候选 / 术语表条目）----------------

class GlossaryEntry(TypedDict, total=False):
    id: str
    source: str
    proposed_target: str
    target: str
    preferred: str
    forbidden: List[str]
    behavior: str
    status: str
    domain: str
    scope: str
    note: str
    confidence: float
    occurrences: List[int]
    evidence: List[TermEvidence]


def entry_id(source: str, target: str, behavior: str) -> str:
    """由内容确定性生成条目 ID：source+target+behavior 相同则 ID 相同。"""
    return stable_id(clean_str(source).casefold(), clean_str(target).casefold(),
                     clean_str(behavior), prefix="t")


def normalize_glossary_entry(raw: Any) -> Optional[GlossaryEntry]:
    """归一化单条术语。

    兼容现有 Excel 列：Source / Target / Behavior / Status / Preferred /
    Forbidden / Scope / Note。新字段：id / proposed_target / domain /
    confidence / occurrences / evidence。
    """
    if raw is None or not isinstance(raw, dict):
        return None
    source = clean_str(raw.get("source") or raw.get("Source"))
    if not source:
        return None
    target = clean_str(raw.get("target") or raw.get("Target"))
    proposed_target = clean_str(raw.get("proposed_target"), default=target)

    behavior = clean_str(raw.get("behavior") or raw.get("Behavior")).lower()
    if behavior not in BEHAVIORS:
        behavior = "translate"
    status = clean_str(raw.get("status") or raw.get("Status")).lower()
    if status not in STATUSES:
        status = "provisional"

    preferred = clean_str(raw.get("preferred") or raw.get("Preferred"), default=target)
    forbidden = clean_str_list(raw.get("forbidden") or raw.get("Forbidden"))

    occurrences: List[int] = []
    raw_occ = raw.get("occurrences")
    if isinstance(raw_occ, list):
        occurrences = [clean_int(x, default=-1) for x in raw_occ]
        occurrences = sorted({x for x in occurrences if x >= 0})

    evidence: List[TermEvidence] = []
    raw_ev = raw.get("evidence")
    if isinstance(raw_ev, list):
        for ev in raw_ev:
            norm = normalize_evidence(ev)
            if norm is not None:
                evidence.append(norm)

    return {
        "id": clean_str(raw.get("id"), default=entry_id(source, target, behavior)),
        "source": source,
        "proposed_target": proposed_target,
        "target": target,
        "preferred": preferred,
        "forbidden": forbidden,
        "behavior": behavior,
        "status": status,
        "domain": clean_str(raw.get("domain")),
        "scope": clean_str(raw.get("scope") or raw.get("Scope")),
        "note": clean_str(raw.get("note") or raw.get("Note")),
        "confidence": clean_float(raw.get("confidence")),
        "occurrences": occurrences,
        "evidence": evidence,
    }


def normalize_glossary(entries: Any) -> List[GlossaryEntry]:
    """归一化术语表（保留顺序，丢弃非法条目；重复 source 不去重，交由上层处理）。"""
    if not isinstance(entries, (list, tuple)):
        return []
    return [e for e in (normalize_glossary_entry(x) for x in entries) if e is not None]


def validate_glossary_entry(e: Optional[GlossaryEntry]) -> List[str]:
    if not e:
        return ["术语条目缺失"]
    errors = []
    if not e.get("source"):
        errors.append("术语条目缺少 source")
    if e.get("behavior") not in BEHAVIORS:
        errors.append(f"非法 behavior：{e.get('behavior')!r}")
    if e.get("status") not in STATUSES:
        errors.append(f"非法 status：{e.get('status')!r}")
    if e.get("behavior") == "translate" and not e.get("preferred"):
        errors.append(f"translate 术语「{e.get('source')}」缺少 preferred 译名")
    if e.get("status") == "locked" and not e.get("preferred"):
        errors.append(f"locked 术语「{e.get('source')}」缺少首选译名")
    for ev in e.get("evidence") or []:
        errors.extend(validate_evidence(ev))
    return errors


# ---------------- FrozenGlossary ----------------

class FrozenGlossary(TypedDict, total=False):
    version: int
    source_hash: str
    entries: List[GlossaryEntry]
    frozen_at: str
    glossary_hash: str
    frozen_by: str


def glossary_hash(entries: List[GlossaryEntry]) -> str:
    """由规范化后的冻结条目确定性生成哈希。

    相同条目、顺序不同 -> 相同哈希；任何条目内容变化 -> 哈希变化。
    forbidden / evidence 列表顺序、无关空白、键顺序不进入语义哈希；
    frozen_at / frozen_by / version 不属于条目内容，不参与哈希。
    """
    # 按规范化内容排序实现顺序无关
    canonical = sorted(
        (c for c in (_canonical_entry_json(e) for e in entries) if c is not None),
        key=lambda s: (len(s), s))
    return hashlib.sha256(_stable_json(canonical).encode("utf-8")).hexdigest()


def _canonical_entry_json(entry: Any) -> Optional[str]:
    """条目 -> 语义稳定的规范化 JSON 字符串。

    forbidden 排序、evidence 按稳定 JSON 排序、occurrences 已排序；
    无关空白在 normalize 中剥离。用于 glossary_hash 与 entries_equal。
    """
    norm = normalize_glossary_entry(entry)
    if norm is None:
        return None
    norm = dict(norm)
    norm["forbidden"] = sorted(norm["forbidden"])
    norm["evidence"] = sorted(
        json.dumps(ev, ensure_ascii=False, sort_keys=True)
        for ev in norm["evidence"])
    return _stable_json(norm)


def normalize_frozen_glossary(raw: Any) -> Optional[FrozenGlossary]:
    if not isinstance(raw, dict):
        return None
    entries = normalize_glossary(raw.get("entries"))
    if not entries:
        return None
    return {
        "version": clean_int(raw.get("version"), default=1),
        "source_hash": clean_str(raw.get("source_hash")),
        "entries": entries,
        "frozen_at": clean_str(raw.get("frozen_at")),
        "glossary_hash": glossary_hash(entries),
        "frozen_by": clean_str(raw.get("frozen_by")),
    }


def validate_frozen_glossary(fg: Optional[FrozenGlossary]) -> List[str]:
    if not fg:
        return ["冻结术语表缺失"]
    errors = []
    if not fg.get("entries"):
        errors.append("冻结术语表为空")
    if fg.get("glossary_hash") != glossary_hash(fg.get("entries") or []):
        errors.append("glossary_hash 与条目内容不一致（术语表可能被篡改）")
    if not fg.get("frozen_at"):
        errors.append("冻结术语表缺少 frozen_at 时间戳")
    for e in fg.get("entries") or []:
        errors.extend(validate_glossary_entry(e))
    return errors


def entries_equal(a: List[GlossaryEntry], b: List[GlossaryEntry]) -> bool:
    """按内容比较两组条目（忽略顺序），用于判断冻结后是否发生修改。"""
    def key(entries: List[GlossaryEntry]) -> List[str]:
        return sorted(
            (c for c in (_canonical_entry_json(e) for e in entries) if c is not None),
            key=lambda s: (len(s), s))
    return key(a) == key(b)


# ---------------- 便捷导出 ----------------

def glossary_to_plain_entries(entries: List[GlossaryEntry]) -> List[Dict[str, Any]]:
    """转成旧版 core.normalize_glossary 的扁平 dict 视图（保持旧 API/测试兼容）。"""
    return [
        {
            "source": e["source"], "target": e["target"], "behavior": e["behavior"],
            "status": e["status"], "preferred": e["preferred"],
            "forbidden": list(e["forbidden"]), "scope": e["scope"], "note": e["note"],
        }
        for e in normalize_glossary(entries)
    ]
