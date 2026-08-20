"""文档画像：确定性分布式采样 + LLM 结构化画像 + 校验与降级。

规约（目标文档）：
- 使用全文的分布式样本（长文至少覆盖开头、中部、结尾），不只取开头；
- 模型输出必须是结构化 JSON 并经过 validate；
- 失败时保留 warning 并允许人工填写，绝不静默伪造画像结果；
- 不阻断翻译（快速模式下失败也可继续）。
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import models

MIN_PARAS_FOR_WINDOWS = 3
DEFAULT_WINDOWS = 3
DEFAULT_CHARS_PER_WINDOW = 2500


def distributed_sample(
    paragraphs: List[str],
    n_windows: int = DEFAULT_WINDOWS,
    chars_per_window: int = DEFAULT_CHARS_PER_WINDOW,
) -> List[Dict[str, Any]]:
    """分布式采样：返回覆盖首、中、尾的窗口。

    每项：{"window": i, "start_segment": s, "end_segment": e, "text": str}。
    段落很少（< n_windows）时退化为全量采样，但窗口字段仍如实标注。
    """
    if not paragraphs:
        return []
    n = len(paragraphs)
    if n < MIN_PARAS_FOR_WINDOWS:
        return [{"window": 0, "start_segment": 0, "end_segment": n - 1,
                 "text": "\n".join(paragraphs)}]

    windows = []
    # 均匀切分段落空间，保证首/中/尾都被覆盖
    edges = [round(i * (n - 1) / max(1, n_windows - 1)) for i in range(n_windows)]
    edges = sorted(set(edges))
    for i, start in enumerate(edges):
        end = edges[i + 1] if i + 1 < len(edges) else n - 1
        # 从 start 起收集段落，直到字符上限
        text_parts, chars = [], 0
        seg_end = start
        for j in range(start, end + 1):
            text_parts.append(paragraphs[j])
            chars += len(paragraphs[j])
            seg_end = j
            if chars >= chars_per_window:
                break
        windows.append({
            "window": i,
            "start_segment": start,
            "end_segment": seg_end,
            "text": "\n".join(text_parts),
        })
    return windows


def _parse_profile_json(text: str) -> Optional[Dict[str, Any]]:
    """宽容解析画像 JSON：剥离 Markdown 代码块与前后解释文字。"""
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.DOTALL)
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


def _profile_system_prompt(target_lang: str = "") -> str:
    lang_hint = f"（目标语言：{target_lang}）" if target_lang else ""
    return (
        "你是一位严谨的文本分析专家。请对用户提供的文档样本做【文档画像】"
        f"{lang_hint}，输出结构化 JSON，字段如下：\n"
        '{"domain": "学科领域（如 生物学/历史学/计算机科学）",\n'
        ' "subdomain": "细分领域",\n'
        ' "genre": "文本类型（如 学术专著/回忆录/教材/论文）",\n'
        ' "audience": "目标读者",\n'
        ' "register": "语域（如 正式书面语/半正式/口语化）",\n'
        ' "style_constraints": "文体与风格约束（翻译时需要遵守的要点）",\n'
        ' "confidence": 0.0-1.0 之间的置信度数字,\n'
        ' "sections": [{"section_id": "唯一ID", "start_segment": 起始段序号, '
        '"end_segment": 结束段序号, "topic": "主题", "domain": "领域", '
        '"style": "文体"}]}\n'
        "要求：\n"
        "1. 只依据样本中的真实文本，不要臆造；不确定的字段留空字符串，"
        "不要编造具体名词。\n"
        "2. sections 可选：如果样本能可靠看出分节才给出，start/end 必须是"
        "样本中标注的段落序号（从 0 开始）；看不出分节时返回空数组 []。\n"
        "3. 严格输出合法 JSON 对象，不要包含任何解释文字。"
    )


def profile_document(
    paragraphs: List[str],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str = "",
    call_llm: Optional[Callable] = None,
) -> Tuple[Optional[models.DocumentProfile], List[str]]:
    """生成文档画像。返回 (profile, warnings)。

    失败/校验不过时返回 (None, [warning...])，由调用方决定降级策略；
    绝不返回伪造的“成功”画像。
    """
    warnings: List[str] = []
    samples = distributed_sample(paragraphs)
    if not samples:
        return None, ["文档画像失败：无文本样本"]

    # 拼样本时明确标注窗口与段落区间，便于模型给出可校验的 section 边界
    sample_text = "\n\n".join(
        f"【样本 {w['window'] + 1}，段落 {w['start_segment']}-{w['end_segment']}】\n{w['text']}"
        for w in samples
    )
    sys_prompt = _profile_system_prompt(target_lang)
    if call_llm is None:
        import core
        call_llm = core.call_llm

    last_err = "模型未返回内容"
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, sample_text, temperature=0.1)
            raw = _parse_profile_json(res)
            if raw is None:
                raise ValueError("返回内容不是合法 JSON 对象")
            profile = models.normalize_document_profile(raw)
            problems = models.validate_document_profile(profile)
            if problems and not profile.get("domain"):
                # 关键字段缺失视为画像失败（不静默伪造）
                raise ValueError("画像缺少关键字段：" + "；".join(problems))
            for p in problems:
                warnings.append(f"文档画像提示：{p}")
            return profile, warnings
        except Exception as e:
            last_err = str(e)
            if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err \
                    or "rate limit" in last_err.lower():
                import time
                time.sleep(10)
                continue
            break
    warnings.append(f"文档画像失败（{last_err[:160]}），已跳过；可在 UI 中人工填写。")
    return None, warnings
