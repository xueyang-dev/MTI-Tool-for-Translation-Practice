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
    """解析用户上传的术语库 Excel；解析失败抛出 ValueError（不再静默吞错）。"""
    try:
        df = pd.read_excel(file_stream)
    except Exception as e:
        raise ValueError(f"无法读取 Excel 文件：{e}") from e
    df.columns = [str(c).strip() for c in df.columns]
    if "Source" not in df.columns or "Target" not in df.columns:
        raise ValueError("术语库缺少 Source / Target 列，请检查表头")
    df = df.dropna(subset=["Source", "Target"])
    return dict(zip(df["Source"].astype(str).str.strip(),
                    df["Target"].astype(str).str.strip()))


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
                     user_termbase, on_status=None, on_caption=None):
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
    final_termbase = dict(user_termbase)
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
    if state["auto_terms"]:
        final_termbase.update(state["auto_terms"])

    # ---------------- 阶段二：双语翻译 ----------------
    if not state["p2_done"]:
        if on_status:
            on_status("【阶段二】双语翻译与术语严格注入...")
        bilingual_pairs = state["pairs"]  # 已翻译部分（断点）
        start_idx = len(bilingual_pairs)

        term_prompt = ("\n【强制术语】：\n" + "\n".join(f"- {k} -> {v}" for k, v in final_termbase.items())
                       if final_termbase else "")
        sys_prompt = f"你是一个学术翻译专家，请翻译成{target_lang}。纯作者信息保留原文。{term_prompt}"

        for i in range(start_idx, len(state["paras"])):
            para = state["paras"][i]
            if on_caption:
                on_caption(f"🌍 正在翻译第 {i + 1}/{len(state['paras'])} 段...")
            trans, last_err = "", None
            for _attempt in range(3):
                try:
                    trans = call_llm(provider, api_key, model, sys_prompt, para, temperature=0.3)
                    time.sleep(1)
                    break
                except Exception as e:
                    last_err = e
                    if is_rate_limited(e):
                        time.sleep(15)
                    else:
                        break
            if not trans.strip():
                raise RuntimeError(f"第 {i + 1} 段翻译失败：{last_err or '模型返回空内容'}")
            bilingual_pairs.append({
                "source": para.replace('\n', ' '),
                "target": clean_xml_chars(trans).replace('\n', ' '),
            })
            save_job_state(job_id, state)  # 每段落盘，真正的细粒度断点

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
