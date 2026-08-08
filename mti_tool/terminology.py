"""术语候选提取与相关术语选择。

- 分布式采样提取（覆盖首/中/尾），不再只截取前 10000 字符；
- 合并重复候选，记录术语出现的【所有】segment_id；
- 自动术语默认 status=candidate（不得自动 locked），证据标记为
  model_knowledge 且不允许伪造 URL；
- 根据 DocumentProfile / SectionProfile 附加 domain 与 scope；
- 解析失败可重试并保留 warning，绝不静默生成空术语并宣称成功。
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from . import models
from .document_profile import distributed_sample


# ---------------- 匹配（词边界 + 大小写 + 短词防误命中）----------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def term_matches(term: str, text: str) -> bool:
    """术语是否出现在文本中。

    - CJK 术语：直接子串（中文无词界，子串即出现）；
    - ASCII/混合术语：大小写不敏感 + 字母数字边界（"AI" 不会误命中
      "MAIN" / "MTI" 中的 "MT"）。
    """
    term = (term or "").strip()
    text = text or ""
    if not term or not text:
        return False
    if _CJK_RE.search(term):
        return term in text
    pattern = re.compile(
        r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])",
        re.IGNORECASE)
    return bool(pattern.search(text))


def find_occurrences(term: str, paragraphs: List[str]) -> List[int]:
    """返回术语在全部段落中的 segment_id 列表（不是只记第一次出现）。"""
    return [i for i, p in enumerate(paragraphs) if term_matches(term, p)]


# ---------------- 外部证据 provider 接口（预留，默认不接入网络）----------------

class TermEvidenceProvider(Protocol):
    """真实外部证据 provider 接口（预留）。

    当前版本不要求接入真实搜索服务，默认在无网络/无搜索 API 下正常工作
    （NoopEvidenceProvider）。接入真实 provider 时：
    - fetch_evidence 必须返回带真实 url 的 external 证据（url 由来源返回，
      绝不允许模型自行编造）；
    - 无法获取来源时返回 []（normalize_evidence 会把无 url 的 external
      自动降级为 model_knowledge）。
    """

    name: str

    def fetch_evidence(self, term: str,
                       domain: str = "") -> List[models.TermEvidence]:
        ...


class NoopEvidenceProvider:
    """默认空 provider：不发起任何网络/API 调用。"""

    name = "noop"

    def fetch_evidence(self, term: str,
                       domain: str = "") -> List[models.TermEvidence]:
        return []


def get_provider(name: str = "noop") -> TermEvidenceProvider:
    """按名称获取 provider（未注册/未知名称一律回退到 noop，保证离线可用）。"""
    providers = {"noop": NoopEvidenceProvider()}
    return providers.get(name, providers["noop"])


# ---------------- 自动抽取 ----------------

def _extract_system_prompt(target_lang: str, n_windows: int) -> str:
    return f"""你是一位极其严谨的学术译员和术语管理专家（Terminologist）。
    用户会提供同一文档的多个分布样本（开头/中部/结尾）。请从所有样本中提取
    20 到 40 个最具代表性的【核心专业术语】（全文档去重后的数量）。

    【核心筛选规则（极其重要）】：
    1. 必须是特定学科的理论概念、专业名词、核心方法论或行业黑话（Jargon）。
    2. 🚫 绝对禁止提取：人名（如学者名/作者名）、书名、文章标题、期刊名、出版地、机构名称、年份。
    3. 🚫 绝对禁止提取：日常通用词汇（如 research, study, analysis 等无门槛词汇）。
    4. 请将其精准、符合学术规范地翻译为{target_lang}。
    5. 同一术语在多个样本中出现时只输出一次。

    请严格输出合法的 JSON 数组格式，绝对不要包含任何其他多余的解释文字，格式如下：
    [
        {{"Source": "英文专业术语1", "Target": "中文专业译名1",
          "domain": "可选：所属领域", "scope": "可选：document 或 section:<id>"}}
    ]"""


def _parse_term_array(text: str) -> Optional[List[Dict[str, Any]]]:
    """宽容解析术语数组（沿用 core.parse_json_array 的策略，独立实现避免循环依赖）。"""
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.DOTALL)
    candidate = re.sub(r"\s*```$", "", candidate, flags=re.DOTALL).strip()
    try:
        obj = json.loads(candidate)
        if isinstance(obj, list):
            return obj
    except Exception:
        pass
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\[", candidate):
        try:
            obj, _ = decoder.raw_decode(candidate[m.start():])
        except Exception:
            continue
        if isinstance(obj, list):
            return obj
    return None


def _assign_scope(entry: models.GlossaryEntry, sections: List[Dict[str, Any]]) -> str:
    """按出现位置分配 scope：全部落在同一 section 内 -> section:<id>；否则 document。"""
    occ = entry.get("occurrences") or []
    if not occ:
        return "document"
    for sec in sections or []:
        start = sec.get("start_segment")
        end = sec.get("end_segment")
        sid = sec.get("section_id")
        if start is None or end is None or not sid:
            continue
        if all(start <= i <= end for i in occ):
            return f"section:{sid}"
    return "document"


def extract_auto_terms_v2(
    paragraphs: List[str],
    target_lang: str,
    provider: str,
    api_key: str,
    model: str,
    document_profile: Optional[models.DocumentProfile] = None,
    sections: Optional[List[Dict[str, Any]]] = None,
    call_llm: Optional[Callable] = None,
) -> Tuple[List[models.GlossaryEntry], List[str]]:
    """分布式术语候选提取。返回 (entries, warnings)。

    entries：status=candidate，occurrences 为全部 segment_id，evidence 为
    model_knowledge（无 URL），domain/scope 来自画像或按出现位置推断。
    失败：返回 ([] , [warning])，绝不静默宣称成功。
    """
    warnings: List[str] = []
    samples = distributed_sample(paragraphs)
    if not samples:
        return [], ["术语抽取失败：无文本样本"]

    sample_text = "\n\n".join(
        f"【样本 {w['window'] + 1}，段落 {w['start_segment']}-{w['end_segment']}】\n{w['text']}"
        for w in samples
    )
    sys_prompt = _extract_system_prompt(target_lang, len(samples))
    if call_llm is None:
        import core
        call_llm = core.call_llm

    parsed = None
    last_err = "模型未返回内容"
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, sample_text, temperature=0.1)
            parsed = _parse_term_array(res)
            if parsed is None:
                raise ValueError("返回内容不是合法 JSON 数组")
            break
        except Exception as e:
            last_err = str(e)
            if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err \
                    or "rate limit" in last_err.lower():
                time.sleep(15)
                continue
            break
    if parsed is None:
        warnings.append("术语抽取失败（限流或返回格式异常），已跳过该步骤；"
                        "可稍后点击“继续处理”重试。")
        return [], warnings

    profile_domain = (document_profile or {}).get("domain") or ""
    sections = sections or (document_profile or {}).get("sections") or []
    merged: Dict[str, models.GlossaryEntry] = {}
    for item in parsed:
        if not isinstance(item, dict):
            continue
        src = str(item.get("Source") or item.get("source") or "").strip()
        tgt = str(item.get("Target") or item.get("target") or "").strip()
        if len(src) <= 1 or not tgt:
            continue
        key = src.casefold()
        existing = merged.get(key)
        if existing is None:
            entry = models.normalize_glossary_entry({
                "source": src, "target": tgt,
                "domain": str(item.get("domain") or "").strip() or profile_domain,
                "scope": str(item.get("scope") or "").strip(),
                "status": "candidate",
                "occurrences": find_occurrences(src, paragraphs),
                "evidence": [{
                    "evidence_type": "model_knowledge",
                    "source_name": "",
                    "note": "自动抽取（模型知识，未经人工核实）",
                    "quote": "",
                    "url": "",
                    "confidence": 0.5,
                }],
            })
            if entry is not None:
                merged[key] = entry
        else:
            # 合并重复候选：并集 occurrences；保留首次译名
            occ = set(existing["occurrences"]) | set(find_occurrences(src, paragraphs))
            existing["occurrences"] = sorted(occ)

    entries = list(merged.values())
    for e in entries:
        if not e.get("scope"):
            e["scope"] = _assign_scope(e, sections)
        e["confidence"] = 0.5
    return entries, warnings


# ---------------- 相关术语选择 ----------------

def select_glossary_for_segments(
    segments: List[str],
    glossary: List[models.GlossaryEntry],
    document_profile: Optional[models.DocumentProfile] = None,
    section_profile: Optional[Dict[str, Any]] = None,
    max_provisional: int = 5,
) -> Tuple[List[models.GlossaryEntry], List[str]]:
    """为当前批次筛选相关术语。返回 (selected_entries, injected_entry_ids)。

    规则：
    1. 只注入当前批次原文实际出现的 locked translate 条目；
    2. 只注入当前批次实际出现的 preserve 条目；
    3. provisional 条目只能作为建议，数量受限（max_provisional）；
    4. 支持 scope：global / document / section:<id> / segment:<id>；
    5. 大小写差异与词边界匹配（term_matches），避免短词 substring 误命中；
    6. rejected 条目永不注入。
    """
    if not segments or not glossary:
        return [], []
    joined = "\n".join(segments)
    selected: List[models.GlossaryEntry] = []
    seen_ids = set()
    provisional_count = 0

    for e in models.normalize_glossary(glossary):
        if e["status"] == "rejected":
            continue
        if not any(term_matches(e["source"], s) for s in segments):
            continue
        # scope 过滤
        scope = (e.get("scope") or "").strip()
        if scope and scope != "global":
            if scope == "document":
                pass  # 文档级术语对批次可见（仅当文档画像存在时视为已确认）
            elif scope.startswith("section:"):
                if not section_profile or section_profile.get("section_id") != scope[8:]:
                    continue
            elif scope.startswith("segment:"):
                seg_id = scope[8:]
                if not any(str(i) == seg_id for i in range(len(segments))):
                    continue
            else:
                continue  # 未知 scope 不注入
        if e["status"] == "provisional":
            if provisional_count >= max_provisional:
                continue
            provisional_count += 1
        if e["id"] in seen_ids:
            continue
        seen_ids.add(e["id"])
        selected.append(e)
    return selected, sorted(seen_ids)


def glossary_block(entries: List[models.GlossaryEntry]) -> str:
    """把筛选后的条目渲染成注入翻译/审校 prompt 的文本块（含 entry ID 便于审计）。"""
    locked_translate = [e for e in entries
                        if e["behavior"] == "translate" and e["status"] == "locked"]
    preserve = [e for e in entries if e["behavior"] == "preserve"]
    provisional = [e for e in entries
                   if e["behavior"] == "translate" and e["status"] != "locked"]
    lines = []
    if locked_translate:
        lines.append("【锁定术语（必须使用首选译名，不得使用禁止译名）】：")
        for e in locked_translate:
            seg = f"- {e['source']} -> {e['preferred']}（ID: {e['id']}）"
            if e["forbidden"]:
                seg += f"（禁止：{'、'.join(e['forbidden'])}）"
            lines.append(seg)
    if preserve:
        ids = "、".join(f"{e['source']}（ID: {e['id']}）" for e in preserve)
        lines.append("【必须保留原文的术语/名称】：" + ids)
    if provisional:
        lines.append("【建议术语（仅供参考，请优先采用）】：")
        for e in provisional:
            lines.append(f"- {e['source']} -> {e['target']}（ID: {e['id']}）")
    return "\n".join(lines)


def glossary_to_terms(entries: List[models.GlossaryEntry]) -> Dict[str, str]:
    """翻译行为术语 -> 扁平 dict（报告/旧接口兼容）。"""
    return {e["source"]: (e["preferred"] or e["target"])
            for e in models.normalize_glossary(entries)
            if e["behavior"] == "translate" and e["target"]}


# ---------------- 术语 QA（entry_id / segment_id 级）----------------

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]{1,}$")


def _preserve_severity(source: str) -> str:
    """保留项丢失严重度：结构标识类（型号/编号/纯标识符）-> blocking，其余 actionable。"""
    src = (source or "").strip()
    if _IDENTIFIER_RE.match(src):
        return "blocking"
    return "actionable"


def check_glossary_compliance(
    src: str,
    tgt: str,
    glossary: List[models.GlossaryEntry],
    segment_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """锁定术语的确定性合规检查（基于 entry_id + segment_id）。

    - locked translate：首选译名缺失 -> actionable；禁止译名出现 -> actionable；
    - locked preserve：丢失 -> 按类型 actionable / blocking；
    - 检查基于词边界匹配（term_matches），不依赖 reason 文本。
    """
    findings: List[Dict[str, Any]] = []
    for e in models.normalize_glossary(glossary):
        if e["status"] != "locked":
            continue
        if e["behavior"] == "preserve":
            if term_matches(e["source"], src) and not term_matches(e["source"], tgt):
                findings.append({
                    "type": "glossary", "severity": _preserve_severity(e["source"]),
                    "entry_id": e["id"], "segment_id": segment_id,
                    "reason": f"锁定保留项「{e['source']}」在译文中丢失",
                })
        else:
            preferred = e.get("preferred") or e.get("target")
            if term_matches(e["source"], src) and preferred \
                    and not term_matches(preferred, tgt):
                findings.append({
                    "type": "glossary", "severity": "actionable",
                    "entry_id": e["id"], "segment_id": segment_id,
                    "reason": f"锁定术语「{e['source']}」未使用首选译名「{preferred}」",
                })
            for fb in e.get("forbidden") or []:
                if fb and fb in tgt:
                    findings.append({
                        "type": "glossary", "severity": "actionable",
                        "entry_id": e["id"], "segment_id": segment_id,
                        "reason": f"术语「{e['source']}」使用了禁止译名「{fb}」",
                    })
    return findings


def detect_glossary_conflicts(
    pairs: List[Dict[str, str]],
    glossary: List[models.GlossaryEntry],
) -> List[Dict[str, Any]]:
    """跨段扫描：同一 locked 术语在同一范围内出现多种译法时报告冲突。

    按术语在每段译文中的实际用法分组（首选 / 禁止译名 / 其他），
    同一术语出现 ≥2 种用法即报告 actionable 冲突（带 entry_id / segment_id）。
    """
    findings: List[Dict[str, Any]] = []
    for e in models.normalize_glossary(glossary):
        if e["status"] != "locked" or e["behavior"] != "translate":
            continue
        preferred = e.get("preferred") or e.get("target")
        if not preferred:
            continue
        usages: Dict[str, List[int]] = {}
        for i, p in enumerate(pairs):
            src, tgt = (p.get("source") or ""), (p.get("target") or "")
            if not term_matches(e["source"], src):
                continue
            if preferred in tgt:
                key = f"preferred:{preferred}"
            else:
                fb_hit = next((fb for fb in e.get("forbidden") or [] if fb and fb in tgt),
                              None)
                key = f"forbidden:{fb_hit}" if fb_hit else "other:未使用首选译名"
            usages.setdefault(key, []).append(i)
        if len(usages) > 1:
            for key, segs in sorted(usages.items()):
                kind = "首选" if key.startswith("preferred:") else (
                    "禁止" if key.startswith("forbidden:") else "其他")
                label = key.split(":", 1)[1] if ":" in key else key
                for i in segs:
                    findings.append({
                        "type": "glossary", "severity": "actionable",
                        "entry_id": e["id"], "segment_id": i, "conflict": True,
                        "reason": f"锁定术语「{e['source']}」在同一范围内出现多种译法"
                                  f"（段 {i} 为{kind}译法「{label}」），需人工统一",
                    })
    return findings
