"""预定义 Style Profiles + Quick Profiling 结构化推荐。

设计约束（TransPraxis 工程原则）：
- LLM 不做"自由发明风格"，只在预定义 profile 集合中选择，并允许少量参数微调；
- 推荐结果必须是结构化 JSON，归一化后成为可版本化 artifact（style_profile_id）；
- 失败时确定性降级（general + 0 置信度 + warning），绝不静默伪造推荐；
- 采样复用 document_profile.distributed_sample 的首/中/尾分布式策略，
  普通文档只需 3000-6000 字符即可判断文体。
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import models
from .document_profile import distributed_sample

# ---------------- 预定义 Style Profiles ----------------

STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "academic": {
        "name": "学术书面语",
        "summary": "正式 · 客观 · 术语保守 · 保留引文",
        "params": {
            "register": "formal",
            "terminology": "conservative",
            "citation_preservation": "strict",
            "sentence_strategy": "moderate_explication",
            "proper_names": "preserve_original_on_first_occurrence",
            "rhetoric": "restrained",
            "target_density": "medium-high",
        },
        "rules": [
            "保持正式、克制、客观的表达风格",
            "术语遵循术语库并保持全文一致，专有名词首次出现时保留原文",
            "严格保留引文、引用标注、作者名与机构名",
            "适度显化复杂句的逻辑关系，句式遵循目标语言规范",
        ],
    },
    "technical": {
        "name": "专业技术",
        "summary": "准确 · 简洁 · 术语一致 · 保留代码与符号",
        "params": {
            "register": "neutral",
            "terminology": "strict",
            "citation_preservation": "normal",
            "sentence_strategy": "split_long",
            "proper_names": "preserve_original",
            "rhetoric": "plain",
            "target_density": "high",
        },
        "rules": [
            "术语严格遵循术语库并保持全文一致",
            "句式简洁，优先保证步骤与逻辑清晰",
            "数字、单位、代码、命令与路径保持原样",
        ],
    },
    "professional": {
        "name": "通用专业",
        "summary": "规范 · 中性 · 清晰",
        "params": {
            "register": "semi_formal",
            "terminology": "balanced",
            "citation_preservation": "normal",
            "sentence_strategy": "moderate_restructure",
            "proper_names": "common_usage",
            "rhetoric": "neutral",
            "target_density": "medium",
        },
        "rules": [
            "表达规范、中性、清晰，避免口语化",
            "术语优先遵循术语库，专有名词采用通行译法",
            "保留数字、日期、引用标注与 URL",
        ],
    },
    "literary": {
        "name": "文学表达",
        "summary": "保留语气与意象 · 译文自然",
        "params": {
            "register": "artistic",
            "terminology": "creative",
            "citation_preservation": "light",
            "sentence_strategy": "recreate_rhythm",
            "proper_names": "common_usage",
            "rhetoric": "expressive",
            "target_density": "low-medium",
        },
        "rules": [
            "保留原文叙事语气、人物口吻与意象",
            "对话保持自然，不做不必要的书面化处理",
            "人名与地名优先采用通行译法",
        ],
    },
    "legal": {
        "name": "法律文书",
        "summary": "严谨 · 术语锁定 · 保留条款结构",
        "params": {
            "register": "formal",
            "terminology": "locked",
            "citation_preservation": "strict",
            "sentence_strategy": "preserve_structure",
            "proper_names": "preserve_original",
            "rhetoric": "precise",
            "target_density": "high",
        },
        "rules": [
            "术语严格遵循术语库，法条与条款编号保持原样",
            "句式严谨，保留原文条款结构与逻辑连接",
            "引用的法律文本、判例编号与日期不得改写",
        ],
    },
    "publicity": {
        "name": "宣传推广",
        "summary": "流畅 · 有感染力 · 适度本地化",
        "params": {
            "register": "persuasive",
            "terminology": "light",
            "citation_preservation": "light",
            "sentence_strategy": "free_restructure",
            "proper_names": "localized",
            "rhetoric": "engaging",
            "target_density": "low",
        },
        "rules": [
            "译文流畅自然，保持原文的感染力与号召力",
            "可适度本地化表达，让目标读者产生共鸣",
            "品牌名、产品名与专有名词保留官方译法",
        ],
    },
    "general": {
        "name": "通用",
        "summary": "自然通顺 · 中性",
        "params": {
            "register": "neutral",
            "terminology": "balanced",
            "citation_preservation": "normal",
            "sentence_strategy": "moderate_restructure",
            "proper_names": "common_usage",
            "rhetoric": "neutral",
            "target_density": "medium",
        },
        "rules": [
            "译文自然通顺，符合目标语言表达习惯",
            "专有名词、数字、引用标注与 URL 保留原文",
        ],
    },
}

STYLE_IDS: List[str] = list(STYLE_PROFILES)


def style_profile_id(profile: Dict[str, Any]) -> str:
    """稳定 ID：规范化 JSON 的 sha256 前 12 位，供版本化引用。"""
    canonical = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def profile_to_rules(profile: Dict[str, Any]) -> str:
    """把选中的 Style Profile（含微调参数）转成翻译管线使用的规则文本。"""
    profile = profile or {}
    base_id = profile.get("selected") or profile.get("recommended_style") or "general"
    rules = list(STYLE_PROFILES.get(base_id, STYLE_PROFILES["general"])["rules"])
    adjustments = profile.get("adjustments") or {}
    for key, label in (("formality", "表达正式度"),
                       ("terminology", "术语保守程度"),
                       ("restructuring", "句法重构幅度"),
                       ("form_preservation", "原文形式保留")):
        value = adjustments.get(key)
        if isinstance(value, (int, float)):
            rules.append(f"{label}：{int(value)}/100")
    return "；".join(rules) + "。" if rules else "保持原文风格。"


# ---------------- 结构化推荐 ----------------

def _parse_json_object(text: Any) -> Optional[Dict[str, Any]]:
    """宽容解析 JSON 对象：剥离 Markdown 代码块与前后解释文字。"""
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.DOTALL)
    candidate = re.sub(r"\s*```$", "", candidate, flags=re.DOTALL).strip()
    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", candidate):
        try:
            obj, _ = decoder.raw_decode(candidate[m.start():])
        except Exception:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _style_prompt(target_lang: str = "") -> str:
    lang_hint = f"（目标语言：{target_lang}）" if target_lang else ""
    profile_lines = "\n".join(
        f"- {pid}（{meta['name']}）：{meta['summary']}"
        for pid, meta in STYLE_PROFILES.items())
    return (
        "你是一位严谨的文本分析专家。请基于用户提供的文档样本做【快速画像与风格推荐】"
        f"{lang_hint}，输出单一合法 JSON 对象，不要包含任何解释文字。\n"
        "可选风格（只允许从中选择，不得自创风格）：\n"
        f"{profile_lines}\n"
        "JSON 结构：\n"
        '{\n'
        ' "document_profile": {\n'
        '   "domain": "学科领域，如 传播学/环境人文学",\n'
        '   "subdomain": "细分领域",\n'
        '   "genre": "文本类型，如 学术专著/教材/访谈/营销文案",\n'
        '   "audience": "目标读者",\n'
        '   "register": "语域，如 正式书面语/半正式/口语化",\n'
        '   "style_constraints": "文体与风格约束（翻译时要遵守的要点）",\n'
        '   "confidence": 0.0-1.0,\n'
        '   "sections": []\n'
        ' },\n'
        ' "style_recommendation": {\n'
        '   "document_type": "文档类型细分，如 academic_monograph",\n'
        '   "domain": ["领域标签数组"],\n'
        '   "register": "语域标签",\n'
        '   "target_audience": "目标读者",\n'
        '   "recommended_style": "必须是上述可选风格之一",\n'
        '   "confidence": 0.0-1.0,\n'
        '   "reasons": ["2-4 条中文依据，如：理论术语密集；学术引用频繁；长句比例较高；面向专业读者"],\n'
        '   "recommended_rules": {}\n'
        ' }\n'
        '}\n'
        "要求：\n"
        "1. 只依据样本中的真实文本，不要臆造；不确定的字段留空。\n"
        "2. recommended_style 必须在给定列表内，这是硬约束。\n"
        "3. reasons 使用中文，简明具体。"
    )


def _normalize_style_recommendation(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return _fallback_recommendation()
    recommended = raw.get("recommended_style")
    if recommended not in STYLE_PROFILES:
        recommended = "general"
    reasons = raw.get("reasons")
    if not isinstance(reasons, list):
        reasons = []
    reasons = [str(r).strip() for r in reasons if str(r).strip()][:4]
    domains = raw.get("domain")
    if not isinstance(domains, list):
        domains = []
    domains = [str(d).strip() for d in domains if str(d).strip()][:6]
    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    rules = raw.get("recommended_rules")
    if not isinstance(rules, dict):
        rules = {}
    return {
        "document_type": str(raw.get("document_type") or ""),
        "domain": domains,
        "register": str(raw.get("register") or ""),
        "target_audience": str(raw.get("target_audience") or ""),
        "recommended_style": recommended,
        "confidence": confidence,
        "reasons": reasons,
        "recommended_rules": rules,
    }


def _fallback_recommendation() -> Dict[str, Any]:
    return {
        "document_type": "",
        "domain": [],
        "register": "",
        "target_audience": "",
        "recommended_style": "general",
        "confidence": 0.0,
        "reasons": ["无法完成自动画像（未配置 AI 引擎或模型调用失败），请手动选择风格"],
        "recommended_rules": {},
    }


def quick_profile(
    paragraphs: List[str],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str = "",
    call_llm: Optional[Callable] = None,
) -> Tuple[models.DocumentProfile, Dict[str, Any], List[str]]:
    """快速画像 + 风格推荐。

    返回 (document_profile, style_recommendation, warnings)。
    一次 LLM 调用同时产出文档画像与风格推荐；任何失败都走确定性降级，
    绝不返回伪造的成功结果。
    """
    warnings: List[str] = []
    samples = distributed_sample(paragraphs)
    if not samples:
        warnings.append("快速画像失败：无可用的文本样本")
        return models.default_document_profile(), _fallback_recommendation(), warnings

    sample_text = "\n\n".join(
        f"【样本 {w['window'] + 1}，段落 {w['start_segment']}-{w['end_segment']}】\n{w['text']}"
        for w in samples)
    if call_llm is None:
        import core
        call_llm = core.call_llm

    last_err = "模型未返回内容"
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, _style_prompt(target_lang),
                           sample_text, temperature=0.1)
            raw = _parse_json_object(res)
            if raw is None:
                raise ValueError("返回内容不是合法 JSON 对象")
            doc_raw = raw.get("document_profile")
            style_raw = raw.get("style_recommendation")
            if not isinstance(style_raw, dict):
                raise ValueError("缺少 style_recommendation 字段")
            doc_profile = models.normalize_document_profile(doc_raw)
            style_rec = _normalize_style_recommendation(style_raw)
            return doc_profile, style_rec, warnings
        except Exception as exc:  # noqa: BLE001 - LLM 输出不可控，统一降级
            last_err = str(exc)
    warnings.append(f"快速画像失败（{last_err}），已降级为通用风格")
    return models.default_document_profile(), _fallback_recommendation(), warnings
