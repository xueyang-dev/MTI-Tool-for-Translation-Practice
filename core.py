"""MTI 翻译实践小助手 —— 核心逻辑层（与 Streamlit UI 解耦，便于测试）。

职责：大模型路由、文档清洗、术语抽取、双语翻译、报告生成、任务进度持久化。
"""
import hashlib
import io
import json
import re
import shutil
import time
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from google import genai
from openai import OpenAI

# ================= 常量 =================
# 任务进度与过程文件的本地存储目录（已加入 .gitignore）
OUTPUT_DIR = Path("outputs")

# 各家模型可选列表（UI 中可切换；如模型下线，在这里更换即可）
MODELS = {
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "OpenAI": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
    "Gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
}


# ================= 基础工具函数 =================
def clean_xml_chars(text):
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)


def parse_json_array(text):
    """从 LLM 输出中稳健地解析 JSON 数组；解析失败返回 None。

    依次尝试：整体解析 -> 去掉 Markdown 代码块后解析 -> 从每个 '[' 位置做
    raw_decode（可容忍输出前后夹带解释文字）。
    """
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = text.strip()
    candidate = re.sub(r'^```(?:json)?\s*', '', candidate, flags=re.DOTALL)
    candidate = re.sub(r'\s*```$', '', candidate, flags=re.DOTALL).strip()

    try:
        obj = json.loads(candidate)
        if isinstance(obj, list):
            return obj
    except Exception:
        pass

    decoder = json.JSONDecoder()
    for m in re.finditer(r'\[', candidate):
        try:
            obj, _ = decoder.raw_decode(candidate[m.start():])
        except Exception:
            continue
        if isinstance(obj, list):
            return obj
    return None


def parse_translation_array(res, expected):
    """解析翻译响应，支持多种模型实际输出形态：
    1. JSON 数组；2. JSON 对象 {"1": "..."}；3. 编号行（1. 译文 / 1、译文）；
    4. 单段时接受任意非空文本。全部失败返回 None。
    """
    arr = parse_json_array(res)
    if arr is not None and len(arr) == expected:
        return arr
    if isinstance(res, str):
        candidate = res.strip()
        candidate = re.sub(r'^```(?:json)?\s*', '', candidate, flags=re.DOTALL)
        candidate = re.sub(r'\s*```$', '', candidate, flags=re.DOTALL).strip()
        try:
            obj = json.loads(candidate)
        except Exception:
            obj = None
        if isinstance(obj, dict):
            out = []
            for i in range(1, expected + 1):
                v = obj.get(str(i))
                if not isinstance(v, str) or not v.strip():
                    return None
                out.append(v.strip())
            return out
    if isinstance(res, str):
        numbered = re.findall(r'^\s*(\d+)[.)、]\s*(.+?)\s*$', res, re.M)
        if numbered:
            numbered.sort(key=lambda x: int(x[0]))
            texts = [t for _, t in numbered]
            if len(texts) >= expected:
                out = [t for t in texts[:expected] if t.strip()]
                if len(out) == expected:
                    return out
    if expected == 1 and isinstance(res, str) and res.strip():
        # 单段兜底：去掉编号前缀后按整段接受，交给确定性检查与审校把关
        return [re.sub(r'^\s*\d+[.)、]\s*', '', res).strip()]
    return None


def is_rate_limited(err):
    s = str(err)
    return '429' in s or 'RESOURCE_EXHAUSTED' in s or 'rate limit' in s.lower()


def call_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
    """底层大模型统一路由（超时 150 秒，模型可配置）。"""
    if provider == "DeepSeek":
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=150.0)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        return (res.choices[0].message.content or "").strip()
    if provider == "OpenAI":
        client = OpenAI(api_key=api_key, timeout=150.0)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        return (res.choices[0].message.content or "").strip()
    if provider == "Gemini":
        try:
            client = genai.Client(api_key=api_key,
                                  http_options=genai.types.HttpOptions(timeout=150_000))
        except (AttributeError, TypeError):
            client = genai.Client(api_key=api_key)
        res = client.models.generate_content(
            model=model,
            contents=user_prompt,
            system_instruction=system_prompt,
            config=genai.types.GenerateContentConfig(temperature=temperature),
        )
        return (res.text or "").strip()
    return ""


def parse_termbase(file_stream):
    """解析用户上传的术语库 Excel，返回概念化术语条目列表。

    必选列：Source / Target；可选列：Behavior（translate/preserve）、
    Status（locked/provisional）、Preferred（首选译名）、Forbidden（禁止译名，
    可用 ; 或 , 分隔）、Scope、Note。解析失败抛出 ValueError（不再静默吞错）。
    """
    try:
        df = pd.read_excel(file_stream)
    except Exception as e:
        raise ValueError(f"无法读取 Excel 文件：{e}") from e
    df.columns = [str(c).strip() for c in df.columns]
    if "Source" not in df.columns or "Target" not in df.columns:
        raise ValueError("术语库缺少 Source / Target 列，请检查表头")
    df = df.dropna(subset=["Source", "Target"])
    entries = []
    for _, row in df.iterrows():
        entry = {"source": str(row["Source"]).strip(),
                 "target": str(row["Target"]).strip()}
        for col, key in (("Behavior", "behavior"), ("Status", "status"),
                         ("Preferred", "preferred"), ("Scope", "scope"),
                         ("Note", "note")):
            if col in df.columns and pd.notna(row[col]):
                entry[key] = str(row[col]).strip()
        if "Forbidden" in df.columns and pd.notna(row["Forbidden"]):
            entry["forbidden"] = [x.strip() for x in
                                  re.split(r"[;；,，]", str(row["Forbidden"])) if x.strip()]
        entries.append(entry)
    return entries


def extract_auto_terms(paragraphs, target_lang, provider, api_key, model):
    """自动抽取术语库：采样前 10000 字符 + 强规则过滤；失败返回空 dict 并留待重试。"""
    sample_text = "\n".join(paragraphs)[:10000]
    sys_prompt = f"""你是一位极其严谨的学术译员和术语管理专家（Terminologist）。
    请从以下文本中提取 30 到 50 个最具代表性的【核心专业术语】。

    【核心筛选规则（极其重要）】：
    1. 必须是特定学科的理论概念、专业名词、核心方法论或行业黑话（Jargon）。
    2. 🚫 绝对禁止提取：人名（如学者名/作者名）、书名、文章标题、期刊名、出版地、机构名称、年份。
    3. 🚫 绝对禁止提取：日常通用词汇（如 research, study, analysis 等无门槛词汇）。
    4. 请将其精准、符合学术规范地翻译为{target_lang}。

    请严格输出合法的 JSON 数组格式，绝对不要包含任何其他多余的解释文字，格式如下：
    [
        {{"Source": "英文专业术语1", "Target": "中文专业译名1"}},
        {{"Source": "英文专业术语2", "Target": "中文专业译名2"}}
    ]"""

    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, sample_text, temperature=0.1)
            term_list = parse_json_array(res)
            if term_list is None:
                raise ValueError("返回内容不是合法 JSON 数组")
            filtered_terms = {}
            for item in term_list:
                if not isinstance(item, dict):
                    continue
                src, tgt = item.get("Source"), item.get("Target")
                if isinstance(src, str) and isinstance(tgt, str):
                    src, tgt = src.strip(), tgt.strip()
                    if len(src) > 1 and tgt:
                        filtered_terms[src] = tgt
            return filtered_terms
        except Exception as e:
            if is_rate_limited(e):
                time.sleep(15)
            else:
                break
    return {}


# ================= 概念化术语表（对齐 localize-anything 的 Glossary 模型）=================
def normalize_glossary(entries):
    """标准化术语条目：{source, target, behavior, status, preferred, forbidden, scope, note}。

    - behavior: translate（需翻译）| preserve（保留原文）
    - status: locked（锁定，确定性强制）| provisional（建议，仅提示）
    - preferred: 锁定后的首选译名；forbidden: 禁止出现的译名
    """
    out = []
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        source = str(e.get("source") or "").strip()
        target = str(e.get("target") or "").strip()
        if not source:
            continue
        behavior = str(e.get("behavior") or "translate").strip().lower()
        if behavior not in ("translate", "preserve"):
            behavior = "translate"
        status = str(e.get("status") or "provisional").strip().lower()
        if status not in ("locked", "provisional"):
            status = "provisional"
        preferred = str(e.get("preferred") or target).strip()
        forbidden = [str(x).strip() for x in (e.get("forbidden") or []) if str(x).strip()]
        out.append({
            "source": source, "target": target, "behavior": behavior, "status": status,
            "preferred": preferred, "forbidden": forbidden,
            "scope": str(e.get("scope") or "").strip(),
            "note": str(e.get("note") or "").strip(),
        })
    return out


def glossary_block(glossary):
    """把术语表渲染成注入翻译/审校 prompt 的文本块。"""
    locked_translate = [e for e in glossary if e["behavior"] == "translate" and e["status"] == "locked"]
    preserve = [e for e in glossary if e["behavior"] == "preserve"]
    provisional = [e for e in glossary if e["behavior"] == "translate" and e["status"] != "locked"]
    lines = []
    if locked_translate:
        lines.append("【锁定术语（必须使用首选译名，不得使用禁止译名）】：")
        for e in locked_translate:
            seg = f"- {e['source']} -> {e['preferred']}"
            if e["forbidden"]:
                seg += f"（禁止：{'、'.join(e['forbidden'])}）"
            lines.append(seg)
    if preserve:
        lines.append("【必须保留原文的术语/名称】：" + "、".join(e["source"] for e in preserve))
    if provisional:
        lines.append("【建议术语（仅供参考，请优先采用）】：")
        for e in provisional:
            lines.append(f"- {e['source']} -> {e['target']}")
    return "\n".join(lines)


def glossary_to_terms(glossary):
    """翻译行为术语 -> 扁平 dict（供报告生成等场景使用）。"""
    return {e["source"]: (e["preferred"] or e["target"])
            for e in glossary if e["behavior"] == "translate" and e["target"]}


def check_glossary_compliance(src, tgt, glossary):
    """锁定术语的确定性合规检查：首选译名缺失、禁止译名出现、保留项丢失。"""
    findings = []
    for e in glossary:
        if e["status"] != "locked":
            continue
        if e["behavior"] == "preserve":
            if e["source"] in src and e["source"] not in tgt:
                findings.append({"type": "glossary", "severity": "actionable",
                                 "reason": f"锁定保留项「{e['source']}」在译文中丢失"})
        else:
            preferred = e.get("preferred") or e.get("target")
            if e["source"] in src and preferred and preferred not in tgt:
                findings.append({"type": "glossary", "severity": "actionable",
                                 "reason": f"锁定术语「{e['source']}」未使用首选译名「{preferred}」"})
            for fb in e.get("forbidden") or []:
                if fb and fb in tgt:
                    findings.append({"type": "glossary", "severity": "actionable",
                                     "reason": f"术语「{e['source']}」使用了禁止译名「{fb}」"})
    return findings


# ================= 确定性检查（对齐 localize-anything 的机械检查）=================
PRESERVE_RE = re.compile(
    r'(?P<placeholder>%[sd]|%1\$[sd]|\{[A-Za-z_][A-Za-z0-9_]*\}|\{\{[A-Za-z_][A-Za-z0-9_]*\}\})'
    r'|(?P<url>https?://\S+|www\.\S+)'
    r'|(?P<email>[\w.+-]+@[\w-]+(?:\.[\w-]+)+)'
    r'|(?P<doi>10\.\d{4,9}/[^\s]+)'
    r'|(?P<citation>\[\d+(?:[-,]\s*\d+)*\])',
    re.IGNORECASE,
)

PRESERVE_SEVERITY = {
    "placeholder": "blocking",   # 占位符损坏 = 结构破坏，绝不可自动放行
    "url": "actionable",
    "email": "actionable",
    "doi": "actionable",
    "citation": "actionable",
}


def extract_preserved_tokens(text):
    """提取源文本中必须原样保留的 token（占位符/URL/邮箱/DOI/引用标注）。"""
    return {m.group(0): m.lastgroup for m in PRESERVE_RE.finditer(text or "")}


def find_residuals(src, tgt, target_lang):
    """检测目标语言中残留的源语言片段。

    返回 [(片段, severity)]：连续 ≥2 个源语单词/较长汉字串 -> actionable；
    单个词（可能是专有名词）-> informational。启发式，不替代审校。
    """
    tgt_clean = PRESERVE_RE.sub(" ", tgt or "")
    if target_lang == "English":
        source_runs = set(re.findall(r'[\u4e00-\u9fff]{2,}', src or ""))
        return [(c, "actionable" if len(c) >= 4 else "informational")
                for c in re.findall(r'[\u4e00-\u9fff]{2,}', tgt_clean)
                if any(c in run for run in source_runs)]
    src_words = set(w.lower() for w in re.findall(r'[A-Za-z]{5,}', src or ""))
    allowed = {"mti"}  # 产品名等明确保留词白名单（审校负责语义判断）
    words = re.findall(r'[A-Za-z]{5,}', tgt_clean)
    hits = [w for w in words if w.lower() in src_words and w.lower() not in allowed]
    result, run = [], []
    for w in words:
        if w in hits:
            run.append(w)
        else:
            if run:
                result.append((" ".join(run),
                               "actionable" if len(run) >= 2 else "informational"))
                run = []
    if run:
        result.append((" ".join(run), "actionable" if len(run) >= 2 else "informational"))
    return result


def check_translation_batch(sources, targets, glossary, target_lang):
    """确定性检查一批译文：空译、保留项丢失、源语残留、锁定术语合规。"""
    findings = []
    for i, (src, tgt) in enumerate(zip(sources, targets)):
        if not tgt.strip():
            findings.append({"segment_index": i, "type": "check", "severity": "blocking",
                             "reason": "译文为空"})
            continue
        for token, kind in extract_preserved_tokens(src).items():
            if token not in tgt:
                findings.append({"segment_index": i, "type": "check",
                                 "severity": PRESERVE_SEVERITY.get(kind, "actionable"),
                                 "reason": f"保留项 {kind}「{token}」在译文中丢失"})
        for residual, sev in find_residuals(src, tgt, target_lang):
            findings.append({"segment_index": i, "type": "check", "severity": sev,
                             "reason": f"疑似残留源语片段「{residual}」"})
        findings.extend(check_glossary_compliance(src, tgt, glossary))
        for f in findings:
            if "segment_index" not in f:
                f["segment_index"] = i
    return findings


# ================= 语义批次（对齐 localize-anything 的上下文批次）=================
BATCH_SIZE = 4
MAX_BATCH_CHARS = 1600


def make_batches(paragraphs, batch_size=BATCH_SIZE, max_chars=MAX_BATCH_CHARS):
    """把段落聚成语义批次：≤batch_size 段且累计 ≤max_chars 字符。"""
    batches, cur, n = [], [], 0
    for p in paragraphs:
        if cur and (len(cur) >= batch_size or n + len(p) > max_chars):
            batches.append(cur)
            cur, n = [], 0
        cur.append(p)
        n += len(p)
    if cur:
        batches.append(cur)
    return batches


# ================= 翻译记忆（对齐 localize-anything 的 TM：仅收录审校通过段落）=================
def tm_path():
    return OUTPUT_DIR / "translation_memory.json"


def load_tm():
    p = tm_path()
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_tm(tm):
    p = tm_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(tm, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


# ================= 翻译 / 修复 / 审校（对齐 localize-anything 的三通道）=================
def _translator_system(glossary_text, style_rules, target_lang):
    return (f"你是一位学术翻译专家，请将用户提供的段落翻译成{target_lang}。\n"
            f"规则：只翻译可翻译的正文；作者姓名、机构名、品牌名、URL、邮箱、DOI、"
            f"引用标注（如 [12]）等保留原文；译文须与原文一一对应并保持顺序。\n"
            f"{glossary_text}\n"
            f"{style_rules}\n"
            "请严格输出合法的 JSON 字符串数组，不要包含任何解释文字。")


def translate_batch(segments, ctx_prev, ctx_next, glossary_text, style_rules, target_lang,
                    provider, api_key, model):
    """翻译一个语义批次，返回与 segments 等长的译文列表；失败抛出 RuntimeError。"""
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(segments))
    context = ""
    if ctx_prev:
        context += "【前文上下文】：\n" + "\n".join(f"- {s}" for s in ctx_prev) + "\n\n"
    if ctx_next:
        context += "【后文上下文】：\n" + "\n".join(f"- {s}" for s in ctx_next) + "\n\n"
    sys_prompt = _translator_system(glossary_text, style_rules, target_lang)
    user_prompt = f"{context}待翻译段落（按序号返回等长译文数组）：\n{numbered}"
    last_err, last_res = None, None
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, user_prompt, temperature=0.3)
            last_res = res
            arr = parse_translation_array(res, len(segments))
            if arr is None:
                raise ValueError(f"译文数量不匹配：期望 {len(segments)}，"
                                 f"响应预览：{(res or '')[:160]!r}")
            # 空项不直接判死：交给确定性检查与自动修复环节兜底
            return [item.strip() if isinstance(item, str) else "" for item in arr]
        except Exception as e:
            last_err = e
            if is_rate_limited(e):
                time.sleep(15)
            else:
                break
    if len(segments) == 1 and last_res and str(last_res).strip():
        # 单段兜底：接受模型原始输出，交由确定性检查/修复把关
        return [re.sub(r'^\s*\d+[.)、]\s*', '', str(last_res)).strip()]
    raise RuntimeError(f"批次翻译失败：{last_err or '模型返回格式异常或数量不匹配'}")


def repair_batch(sources, targets, findings, glossary_text, style_rules, target_lang,
                 provider, api_key, model):
    """根据确定性检查发现的问题自动修复一批译文；返回与 sources 等长的译文列表。"""
    numbered = "\n".join(
        f"{i + 1}. 原文：{s}\n   译文：{t}" for i, (s, t) in enumerate(zip(sources, targets)))
    issues = "\n".join(f"- 段落 {f['segment_index'] + 1}: [{f['severity']}] {f['reason']}"
                       for f in findings)
    sys_prompt = _translator_system(glossary_text, style_rules, target_lang)
    user_prompt = ("以下译文未通过检查，请仅修正有问题的段落，其余段落保持原样，"
                   f"返回与段落数相同的 JSON 字符串数组：\n\n{numbered}\n\n问题清单：\n{issues}")
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, user_prompt, temperature=0.2)
            arr = parse_json_array(res)
            if arr is None or len(arr) != len(sources):
                raise ValueError("修复结果数量不匹配")
            return [clean_xml_chars(str(x)).strip() if isinstance(x, str) else "" for x in arr]
        except Exception as e:
            if is_rate_limited(e):
                time.sleep(15)
            else:
                break
    raise RuntimeError("自动修复失败：模型返回格式异常")


def review_translation_batch(sources, targets, glossary_text, style_rules, target_lang,
                             provider, api_key, model):
    """独立审校一个批次（与翻译分离的 prompt/上下文），返回 (findings, failed)。"""
    numbered = "\n".join(
        f"{i + 1}. 原文：{s}\n   译文：{t}" for i, (s, t) in enumerate(zip(sources, targets)))
    sys_prompt = (f"你是一位独立的翻译审校专家，负责审查机器译文。请检查：语义准确性、术语一致性、"
                  f"漏译/增译、目标语言自然度与风格。只报告真实存在的问题，"
                  f"不要为低风险或主观偏好制造 finding。\n"
                  f"severity 只允许以下三种：blocking（结构/占位符/语义严重错误）、"
                  f"actionable（应修正的问题）、informational（建议）。\n"
                  "如果整批译文没有问题，请严格返回空数组 []，不要输出任何 informational 备注。\n"
                  f"{glossary_text}\n"
                  f"{style_rules}\n"
                  '请严格输出 JSON 数组，每项格式：{"segment_index": 0, "severity": "actionable", '
                  '"reason": "问题说明", "suggested_target": "可选：修正后的译文"}')
    user_prompt = f"待审校段落（目标语言：{target_lang}）：\n{numbered}"
    for _attempt in range(3):
        try:
            res = call_llm(provider, api_key, model, sys_prompt, user_prompt, temperature=0.2)
            arr = parse_json_array(res)
            if arr is None:
                return [], True
            return arr, False
        except Exception as e:
            if is_rate_limited(e):
                time.sleep(15)
            else:
                break
    return [], True


def translate_stage(state, job_id, glossary, provider, api_key, model, target_lang,
                    style_rules, enable_review, on_status=None, on_caption=None):
    """阶段二：语义批次翻译 + 确定性检查/修复 + 独立审校 + 翻译记忆。

    对齐 localize-anything 经验：
    - 语义批次：≤4 段一组，携带前后文，保留每批落盘的断点粒度；
    - 概念化术语表：锁定术语强制首选译名/禁止译名，保留项强制原样；
    - 确定性检查：占位符/URL/引用等保留项、残留原文、锁定术语合规，问题自动修复一轮；
    - 独立审校：actionable 建议经确定性复验后应用，blocking 记录给用户确认；
    - 翻译记忆：仅审校通过的段落入库，精确命中直接复用。
    """
    tm = load_tm()
    paras = state["paras"]
    pairs = state["pairs"]
    batches = make_batches(paras)

    # 断点：从第一个未完成批次继续；若中间批次不完整则截断重译
    cum_end, start_batch = 0, 0
    for bi, b in enumerate(batches):
        prev_end = cum_end
        cum_end += len(b)
        if cum_end > len(pairs):
            if len(pairs) > prev_end:
                del pairs[prev_end:]
            start_batch = bi
            break
    else:
        start_batch = len(batches)

    stats = state.setdefault("review_stats", {
        "reviewed_segments": 0, "batches_reviewed": 0,
        "blocking": 0, "actionable": 0, "informational": 0, "review_failed": 0,
    })
    findings_all = state.setdefault("findings", [])
    glossary_text = glossary_block(glossary)

    for bi in range(start_batch, len(batches)):
        batch = batches[bi]
        offset = sum(len(b) for b in batches[:bi])
        if on_status:
            on_status(f"【阶段二】双语翻译与术语严格注入...（批次 {bi + 1}/{len(batches)}）")
        if on_caption:
            on_caption(f"🌍 正在翻译第 {offset + 1}-{offset + len(batch)} 段（共 {len(paras)} 段）...")

        ctx_prev = paras[max(0, offset - 2):offset]
        ctx_next = paras[min(len(paras), offset + len(batch)):min(len(paras), offset + len(batch) + 2)]

        # 1) 翻译记忆精确命中直接复用
        batch_pairs = [None] * len(batch)
        to_translate = []  # (index, clean_source)
        for i, para in enumerate(batch):
            clean_src = para.replace('\n', ' ')
            hit = tm.get(clean_src)
            if hit and hit.get("reviewed") and hit.get("target"):
                batch_pairs[i] = {"source": clean_src, "target": hit["target"],
                                  "reviewed": True, "from_tm": True}
                state["tm_used_count"] = state.get("tm_used_count", 0) + 1
            else:
                to_translate.append((i, clean_src))

        # 2) 未命中段落批次翻译
        if to_translate:
            texts = [t for _, t in to_translate]
            try:
                targets = translate_batch(texts, ctx_prev, ctx_next, glossary_text, style_rules,
                                          target_lang, provider, api_key, model)
            except RuntimeError:
                # 批次解析失败时降级为逐段翻译，保证进度不中断
                if len(texts) == 1:
                    raise
                if on_caption:
                    on_caption("⚠️ 批次翻译返回格式异常，降级为逐段翻译...")
                targets = []
                for t in texts:
                    targets.append(translate_batch([t], ctx_prev, ctx_next, glossary_text,
                                                   style_rules, target_lang, provider,
                                                   api_key, model)[0])
            for (i, src), tgt in zip(to_translate, targets):
                batch_pairs[i] = {"source": src, "target": clean_xml_chars(tgt).replace('\n', ' '),
                                  "reviewed": False, "from_tm": False}

        batch_sources = [p["source"] for p in batch_pairs]
        batch_targets = [p["target"] for p in batch_pairs]
        findings = check_translation_batch(batch_sources, batch_targets, glossary, target_lang)

        # 3) 确定性问题自动修复（一轮）
        fixable = [f for f in findings if f["severity"] in ("blocking", "actionable")]
        if fixable and len(fixable) <= 8:
            if on_caption:
                on_caption(f"🔧 发现 {len(fixable)} 个确定性问题，正在自动修复...")
            try:
                repaired = repair_batch(batch_sources, batch_targets, fixable, glossary_text,
                                        style_rules, target_lang, provider, api_key, model)
                if repaired and len(repaired) == len(batch_pairs):
                    for j, p in enumerate(batch_pairs):
                        if not p["from_tm"] and repaired[j] and repaired[j].strip():
                            p["target"] = clean_xml_chars(repaired[j]).replace('\n', ' ')
                batch_targets = [p["target"] for p in batch_pairs]
                findings = check_translation_batch(batch_sources, batch_targets, glossary, target_lang)
            except Exception:
                pass  # 修复失败则保留原译文与 finding

        # 4) 独立审校：actionable 建议复验后应用；blocking 记录给用户
        if enable_review:
            stats["batches_reviewed"] += 1
            rfindings, failed = review_translation_batch(
                batch_sources, batch_targets, glossary_text, style_rules, target_lang,
                provider, api_key, model)
            if failed:
                stats["review_failed"] += 1
            for rf in rfindings:
                sev = rf.get("severity")
                if sev not in ("blocking", "actionable", "informational"):
                    continue
                idx = rf.get("segment_index")
                if not isinstance(idx, int) or not (0 <= idx < len(batch_pairs)):
                    continue
                record = {"segment_index": offset + idx, "severity": sev, "type": "review",
                          "reason": str(rf.get("reason") or "审校发现问题")}
                if sev == "actionable" and rf.get("suggested_target") \
                        and not batch_pairs[idx]["from_tm"]:
                    suggested = clean_xml_chars(rf["suggested_target"]).replace('\n', ' ').strip()
                    if suggested:
                        old_target = batch_pairs[idx]["target"]
                        batch_pairs[idx]["target"] = suggested
                        recheck = check_translation_batch(
                            [batch_sources[idx]], [suggested], glossary, target_lang)
                        if any(f["severity"] in ("blocking", "actionable") for f in recheck):
                            batch_pairs[idx]["target"] = old_target  # 复验不过则回滚
                            record["suggested_target"] = suggested
                            findings_all.append(record)
                        continue
                findings_all.append(record)

        # 审校可能修改过译文：对最终译文整体复验一次确定性检查
        findings = check_translation_batch(
            batch_sources, [p["target"] for p in batch_pairs], glossary, target_lang)

        # 记录仍未解决的确定性问题
        for f in findings:
            if f["severity"] in ("blocking", "actionable", "informational"):
                findings_all.append({"segment_index": offset + f["segment_index"],
                                     "severity": f["severity"], "type": "check",
                                     "reason": f["reason"]})

        # 5) 审校通过的段落 -> 翻译记忆
        if enable_review:
            for j, p in enumerate(batch_pairs):
                seg_findings = [f for f in findings_all if f.get("segment_index") == offset + j
                                and f["severity"] in ("blocking", "actionable")]
                if not seg_findings and not p["from_tm"]:
                    p["reviewed"] = True
                    tm[p["source"]] = {"target": p["target"], "reviewed": True}
                    stats["reviewed_segments"] += 1
            save_tm(tm)

        pairs.extend(batch_pairs)
        save_job_state(job_id, state)  # 每批落盘，断点粒度 = 一个批次

    stats["blocking"] = sum(1 for f in findings_all if f["severity"] == "blocking")
    stats["actionable"] = sum(1 for f in findings_all if f["severity"] == "actionable")
    stats["informational"] = sum(1 for f in findings_all if f["severity"] == "informational")
    state["has_blocking"] = stats["blocking"] > 0
    return state


def findings_report_md(state):
    """把审查结果渲染成 Markdown 报告（下载/展示用）。"""
    stats = state.get("review_stats") or {}
    lines = [
        "# 翻译审查报告", "",
        "## 概览",
        f"- 已审校段落：{stats.get('reviewed_segments', 0)}",
        f"- 审校批次：{stats.get('batches_reviewed', 0)}",
        f"- 审校失败批次：{stats.get('review_failed', 0)}",
        f"- 翻译记忆复用：{state.get('tm_used_count', 0)} 段",
        f"- blocking：{stats.get('blocking', 0)}",
        f"- actionable：{stats.get('actionable', 0)}",
        f"- informational：{stats.get('informational', 0)}",
        "", "## 待处理问题",
    ]
    findings = state.get("findings") or []
    if not findings:
        lines.append("无。")
    else:
        for f in findings:
            line = f"- 第 {f.get('segment_index', -1) + 1} 段 [{f.get('severity')}] {f.get('reason')}"
            if f.get("suggested_target"):
                line += f"（建议译文：{f['suggested_target']}）"
            lines.append(line)
    return "\n".join(lines)


# ================= 文档/表格生成 =================
def dict_to_excel(term_dict):
    df = pd.DataFrame(list(term_dict.items()), columns=["Source", "Target"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output


def paragraphs_to_word(paragraphs):
    doc = Document()
    doc.add_heading('阶段一：清洗后原文提取', 0)
    for p in paragraphs:
        doc.add_paragraph(p)
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out


def pairs_to_word(pairs):
    """双语对照表 -> Word 表格。"""
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    table.rows[0].cells[0].text = "原文"
    table.rows[0].cells[1].text = "译文"
    for pair in pairs:
        row = table.add_row().cells
        row[0].text = pair['source']
        row[1].text = pair['target']
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out


def _add_formatted_runs(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0:
            run.bold = True


def markdown_to_word(md_text, theory):
    doc = Document()
    md_text = re.sub(r'```markdown|```', '', md_text).strip()
    title = doc.add_heading(f'翻译实践报告：基于{theory}', 0)
    title.alignment = 1
    for line in md_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith(('- ', '* ')):
            p = doc.add_paragraph(style='List Bullet')
            _add_formatted_runs(p, line[2:])
        elif line.startswith('> '):
            p = doc.add_paragraph(style='Intense Quote')
            _add_formatted_runs(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_formatted_runs(p, line)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io


# ================= 任务持久化（真正的断点续传）=================
def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def job_dir(job_id):
    return OUTPUT_DIR / job_id


def job_state_path(job_id):
    return job_dir(job_id) / "state.json"


def new_job_state(filename):
    return {
        "filename": filename,
        "p1_done": False,
        "p2_done": False,
        "p3_done": False,
        "report_enabled": True,
        "paras": [],
        "pairs": [],
        "auto_terms": {},
        "findings": [],
        "review_stats": {
            "reviewed_segments": 0, "batches_reviewed": 0,
            "blocking": 0, "actionable": 0, "informational": 0, "review_failed": 0,
        },
        "tm_used_count": 0,
        "has_blocking": False,
        "p3_md": "",
        "p3_sections": [],
        "theory": "",
        "warnings": [],
    }


def load_job_state(job_id):
    p = job_state_path(job_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_job_state(job_id, state):
    """原子写入（先写临时文件再替换），避免中断写坏 state.json。"""
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "state.json.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(d / "state.json")


def list_jobs():
    jobs = []
    _ensure_output_dir()
    for d in sorted(OUTPUT_DIR.iterdir()):
        sp = d / "state.json"
        if sp.is_file():
            try:
                s = json.loads(sp.read_text(encoding="utf-8"))
            except Exception:
                continue
            jobs.append({"job_id": d.name, "state": s})
    return jobs


def delete_job(job_id):
    d = job_dir(job_id)
    if d.exists():
        shutil.rmtree(d)


def file_job_id(file_bytes):
    """以文件内容哈希作为任务 ID：同一文件重传可自动续传，不同文件不会串状态。"""
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def save_source(job_id, file_bytes):
    """留存源文件，刷新页面后即使不重新上传也能继续（如重做阶段一）。"""
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "source.bin").write_bytes(file_bytes)


def load_source(job_id):
    p = job_dir(job_id) / "source.bin"
    return p.read_bytes() if p.is_file() else None


def progress_label(state):
    if state.get("p1_done") and state.get("p2_done") and \
            (state.get("p3_done") or not state.get("report_enabled", True)):
        return "已完成"
    if state.get("p2_done"):
        return "报告生成中"
    if state.get("p1_done"):
        return "翻译中"
    return "待处理"


# ================= 阶段三：报告生成（Map-Reduce + 章节级断点）=================
def generate_mti_report(bilingual_pairs, termbase_dict, theory, provider, api_key,
                        model, state, job_id, on_status=None):
    """四段式报告生成；每个章节完成后立即落盘，中途失败可从已完成的章节续写。"""
    sample_texts = ""
    char_count = 0
    for pair in bilingual_pairs:
        chunk = f"【原文】{pair['source']}\n【译文】{pair['target']}\n\n"
        sample_texts += chunk
        char_count += len(chunk)
        if char_count > 8000:
            break

    term_str = "\n".join(f"{k} -> {v}" for k, v in termbase_dict.items()) if termbase_dict else "无术语提取"

    prompts = [
        (
            "一、 翻译项目概述与文本特征分析",
            f"请基于以下双语语料样本，撰写翻译实践报告的【第一部分】。\n"
            f"要求：详尽分析源文本的语言风格、专业领域、词法（如专有名词、长难句）与句法特点，"
            f"以及由此带来的总体翻译难点。字数要求 800-1000 字。严禁输出其他章节的内容。\n\n"
            f"语料样本：\n{sample_texts}"
        ),
        (
            "二、 术语管理与验证",
            f"请撰写翻译实践报告的【第二部分】。\n"
            f"请基于以下核心术语表，详细评估本次翻译中术语库的执行情况。"
            f"请至少选取 4 个核心术语，深度剖析其翻译策略（如直译、意译、增词、转换等）"
            f"及其对提升文本专业性的贡献。字数要求 800-1000 字。\n\n术语表：\n{term_str}"
        ),
        (
            f"三、 基于【{theory}】的案例分析",
            f"这是本报告的最核心章节。请基于以下双语语料样本和【{theory}】的理论框架，撰写报告的【第三部分】。\n"
            f"要求：精准抽取 4-5 个最具代表性的长难句或特殊表达案例。每个案例必须独立成段并包含：\n"
            f"1. 原译文对照\n2. 翻译难点深度剖析\n"
            f"3. 严谨的学理分析（明确指出具体的翻译技巧，并用【{theory}】的核心概念论证“为何如此翻译”）。\n"
            f"本部分字数要求不少于 1500 字，必须极具学术深度。\n\n语料样本：\n{sample_texts}"
        ),
        (
            "四、 翻译项目复盘与反思",
            f"请结合上述关于【{theory}】的翻译实践，撰写报告的【第四部分】。\n"
            f"要求：深刻总结机器翻译（MT）在此类文本中的局限性、本地化术语库强干预的实际效果，"
            f"以及作为译后编辑（MTPE）在双语能力和理论运用层面的收获。字数要求 600-800 字。"
        ),
    ]
    base_system_prompt = "你是一位拥有深厚学术背景的 MTI（翻译硕士）导师及资深学术期刊审稿人。" \
                         "请严格使用学术书面语，逻辑严密，杜绝任何 AI 常见的口语化或套话表达。"

    valid_titles = {title for title, _ in prompts}
    sections = [s for s in state.get("p3_sections", []) if s and s[0] in valid_titles]
    state["p3_sections"] = sections

    for idx, (section_title, user_prompt) in enumerate(prompts):
        if any(s[0] == section_title for s in sections):
            continue
        if on_status:
            on_status(f"【阶段三】正在深度撰写：{section_title} ({idx + 1}/4)...")
        last_err, success = None, False
        for _attempt in range(3):
            try:
                section_content = call_llm(provider, api_key, model, base_system_prompt,
                                           user_prompt, temperature=0.5)
                section_content = re.sub(r'^```markdown|```$', '',
                                         section_content.strip(), flags=re.MULTILINE)
                if not section_content.strip():
                    raise RuntimeError("模型返回空内容")
                sections.append([section_title, section_content.strip()])
                state["p3_sections"] = sections
                save_job_state(job_id, state)  # 章节级断点
                time.sleep(2)
                success = True
                break
            except Exception as e:
                last_err = e
                if is_rate_limited(e):
                    time.sleep(20)
                else:
                    break
        if not success:
            raise RuntimeError(f"报告章节「{section_title}」生成失败：{last_err}")

    return "".join(f"## {t}\n\n{c}\n\n---\n\n" for t, c in sections)


# ================= 主流程：单文档完整流水线 =================
def run_job_pipeline(job_id, filename, file_bytes, *, provider, api_key, model,
                     target_lang, auto_term, enable_report, translation_theory,
                     user_glossary=None, style_rules="", enable_review=True,
                     on_status=None, on_caption=None):
    """执行单个文档的完整流程；每个里程碑实时落盘，刷新/重启后均可继续。"""
    _ensure_output_dir()
    base = new_job_state(filename)
    state = load_job_state(job_id) or base
    state = {**base, **state}  # 兼容旧版本状态缺字段
    state["report_enabled"] = bool(enable_report)
    warnings = state.setdefault("warnings", [])

    # 全部完成 -> 直接返回
    if state["p1_done"] and state["p2_done"] and (not enable_report or state["p3_done"]):
        return state

    # ---------------- 阶段一：排版清洗 ----------------
    if not state["p1_done"]:
        if on_status:
            on_status("【阶段一】AI 智能排版与断句清洗...")
        if file_bytes is None:
            file_bytes = load_source(job_id)
        if file_bytes is None:
            raise ValueError("缺少源文件，请重新上传后再继续")

        paragraphs = []
        if filename.lower().endswith(".pdf"):
            doc_pdf = fitz.open(stream=file_bytes, filetype="pdf")
            raw_chunks, current_chunk = [], ""
            for page in doc_pdf:
                text = page.get_text("text").strip()
                if text:
                    current_chunk += text + "\n\n"
                if len(current_chunk) > 2500:
                    raw_chunks.append(current_chunk)
                    current_chunk = ""
            if current_chunk:
                raw_chunks.append(current_chunk)
            doc_pdf.close()

            sys_p1 = "你是一个学术排版专家。剔除页眉页脚、合并换行截断的句子。严格返回JSON数组（List[str]）。"
            for idx, chunk in enumerate(raw_chunks):
                if on_caption:
                    on_caption(f"📡 清洗区块 {idx + 1}/{len(raw_chunks)}...")
                success = False
                for _attempt in range(3):
                    try:
                        result_text = call_llm(provider, api_key, model, sys_p1, f"文本：\n{chunk}")
                        parsed = parse_json_array(result_text)
                        if parsed is not None:
                            for p in parsed:
                                if isinstance(p, str):
                                    for sub_p in re.split(r'\n+', clean_xml_chars(p)):
                                        if len(sub_p.strip()) > 5:
                                            paragraphs.append(sub_p.strip())
                            success = True
                            time.sleep(1)
                            break
                    except Exception as e:
                        if is_rate_limited(e):
                            time.sleep(10)
                        else:
                            break
                if not success:
                    # 模型清洗失败时降级：直接使用原始文本
                    for sub_p in re.split(r'\n+', clean_xml_chars(chunk)):
                        if len(sub_p.strip()) > 5:
                            paragraphs.append(sub_p.strip())
        elif filename.lower().endswith(".docx"):
            doc_word = Document(io.BytesIO(file_bytes))
            for p in doc_word.paragraphs:
                for sub_p in re.split(r'\n+', clean_xml_chars(p.text)):
                    if len(sub_p.strip()) > 5:
                        paragraphs.append(sub_p.strip())

        if not paragraphs:
            raise ValueError("未提取到有效文本")
        state["paras"] = paragraphs
        state["p1_done"] = True
        save_source(job_id, file_bytes)  # 留存源文件，刷新后无需重新上传
        save_job_state(job_id, state)

    # ---------------- 阶段 1.5：智能抽取术语 ----------------
    if auto_term and not state["auto_terms"]:
        if on_status:
            on_status("【阶段1.5】正在 AI 智能抽取全文核心术语...")
        if on_caption:
            on_caption("🤖 正在从前言样本中提取行业词汇...")
        extracted = extract_auto_terms(state["paras"], target_lang, provider, api_key, model)
        state["auto_terms"] = extracted
        if extracted:
            if on_caption:
                on_caption(f"✅ 成功提取 {len(extracted)} 个专属术语并注入翻译引擎")
        else:
            msg = "术语抽取失败（限流或返回格式异常），已跳过该步骤；可稍后点击“继续处理”重试。"
            if msg not in warnings:
                warnings.append(msg)
        save_job_state(job_id, state)
    auto_entries = [{"source": k, "target": v, "behavior": "translate",
                     "status": "provisional"}
                    for k, v in (state["auto_terms"] or {}).items()]
    glossary = normalize_glossary(list(user_glossary or []) + auto_entries)
    final_termbase = glossary_to_terms(glossary)

    # ---------------- 阶段二：双语翻译（批次 + 确定性检查 + 独立审校 + 翻译记忆）----------------
    if not state["p2_done"]:
        if on_status:
            on_status("【阶段二】双语翻译与术语严格注入（批次翻译 + 确定性检查 + 独立审校）...")
        translate_stage(state, job_id, glossary, provider, api_key, model, target_lang,
                        style_rules, enable_review, on_status=on_status, on_caption=on_caption)
        state["p2_done"] = True
        save_job_state(job_id, state)

    # ---------------- 阶段三：报告生成 ----------------
    if enable_report and not state["p3_done"]:
        if on_status:
            on_status(f"【阶段三】基于《{translation_theory}》生成报告...")
        report_md = generate_mti_report(state["pairs"], final_termbase, translation_theory,
                                        provider, api_key, model, state, job_id,
                                        on_status=on_status)
        if not report_md.strip():
            raise RuntimeError("报告内容为空，请点击“继续处理”重试")
        state["p3_md"] = report_md
        state["theory"] = translation_theory
        state["p3_done"] = True
        save_job_state(job_id, state)

    return state
