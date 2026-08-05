import streamlit as st

import core

# ================= 页面全局设置 =================
st.set_page_config(page_title="MTI 翻译实践小助手", page_icon="🎓", layout="wide")

if "doc_states" not in st.session_state:
    st.session_state.doc_states = {}

# ================= UI 界面绘制 =================
st.title("🎓 MTI 翻译实践小助手 (Pro版)")

with st.sidebar:
    st.header("⚙️ 引擎设置")
    ai_provider = st.selectbox("核心引擎", list(core.MODELS.keys()))
    ai_model = st.selectbox("模型", core.MODELS[ai_provider])
    api_key = st.text_input(f"请输入 {ai_provider} API Key", type="password")
    target_lang = st.selectbox("目标语言", ["简体中文", "English", "日本語"])

    st.divider()
    st.header("🛠️ 进阶功能")
    auto_term = st.checkbox("🤖 智能抽取术语库 (翻译前执行)", value=True,
                            help="大模型自动提取专有名词并生成 Excel 术语库")
    enable_report = st.checkbox("📝 自动生成实践报告", value=True)
    enable_review = st.checkbox("🔍 独立审校 (Review)", value=True,
                                help="翻译后由独立审校 pass 检查语义/术语问题；通过审校的段落才会进入翻译记忆")
    translation_theory = st.selectbox("案例分析理论", [
        "目的论 (Skopos Theory)",
        "交际翻译与语义翻译 (Newmark)",
        "功能对等理论 (Nida)",
        "文本类型理论 (Reiss)",
    ])
    style_rules = st.text_area(
        "风格与保留规则（可选）",
        value="保持学术书面语；专有名词、作者姓名、机构名、引用标注、URL 等保留原文；"
              "标点遵循目标语言规范。",
        help="这些规则会注入翻译与审校 prompt，作为项目级风格/保留规则。",
    )

    st.divider()
    st.header("📂 本地任务（断点续传）")
    saved_jobs = core.list_jobs()
    if saved_jobs:
        job_choices = [f"{j['state'].get('filename', '?')} · {core.progress_label(j['state'])}"
                       for j in saved_jobs]
        resume_choice = st.selectbox("选择要继续的任务（可不重新上传文件）", ["— 不继续 —"] + job_choices)
    else:
        resume_choice = None
        st.caption("暂无本地任务。进度保存在 outputs/ 目录，刷新或重启后仍可继续。")

col1, col2 = st.columns(2)
with col1:
    termbase_file = st.file_uploader("导入已有术语库 (.xlsx, 可选)", type=["xlsx"])
    user_glossary = []
    if termbase_file:
        try:
            user_glossary = core.parse_termbase(termbase_file)
            if user_glossary:
                locked = sum(1 for e in user_glossary
                             if str(e.get("status") or "").lower() == "locked")
                st.success(f"✅ 已导入 {len(user_glossary)} 条术语（锁定 {locked} 条）")
            else:
                st.warning("术语表为空（未找到有效的 Source/Target 行）")
        except ValueError as e:
            st.warning(f"⚠️ {e}（将使用空术语库继续）")
with col2:
    uploaded_files = st.file_uploader("待翻译文档 (支持多文件与断点续传)",
                                      type=["pdf", "docx"], accept_multiple_files=True)

# ================= 核心处理流（断点续传状态机，实时落盘）=================
if st.button("🚀 开始 / 继续处理 (断点续传)", type="primary", use_container_width=True):
    has_resume = bool(saved_jobs and resume_choice and resume_choice != "— 不继续 —")
    if not uploaded_files and not has_resume:
        st.error("请上传文件，或在左侧选择要继续的本地任务！")
    else:
        tasks = []
        seen = set()
        for f in uploaded_files:
            file_bytes = f.read()
            job_id = core.file_job_id(file_bytes)
            if job_id in seen:
                continue
            seen.add(job_id)
            tasks.append({"job_id": job_id, "filename": f.name, "file_bytes": file_bytes})
        if has_resume:
            job = saved_jobs[job_choices.index(resume_choice)]
            if job["job_id"] not in seen:
                tasks.append({"job_id": job["job_id"],
                              "filename": job["state"].get("filename", "?"),
                              "file_bytes": None})

        overall_bar = st.progress(0)
        for task_idx, task in enumerate(tasks):
            job_id, filename, file_bytes = task["job_id"], task["filename"], task["file_bytes"]
            state = st.session_state.doc_states.get(job_id) or core.load_job_state(job_id) \
                or core.new_job_state(filename)
            st.session_state.doc_states[job_id] = state

            if state["p1_done"] and state["p2_done"] and (not enable_report or state["p3_done"]):
                overall_bar.progress((task_idx + 1) / len(tasks))
                continue

            try:
                with st.status(f"⚙️ 正在处理: {filename}", expanded=True) as status:
                    state = core.run_job_pipeline(
                        job_id, filename, file_bytes,
                        provider=ai_provider, api_key=api_key, model=ai_model,
                        target_lang=target_lang, auto_term=auto_term,
                        enable_report=enable_report, translation_theory=translation_theory,
                        user_glossary=user_glossary,
                        style_rules=style_rules, enable_review=enable_review,
                        on_status=lambda label: status.update(label=label, state="running"),
                        on_caption=lambda text: st.caption(text),
                    )
                    st.session_state.doc_states[job_id] = state
                    for warn in state.get("warnings", []):
                        st.warning(warn)
                    if state["p1_done"] and state["p2_done"] \
                            and (not enable_report or state["p3_done"]):
                        if state.get("has_blocking"):
                            status.update(
                                label=f"⚠️ {filename} 流程完成，但有 blocking 问题待确认（见资产面板审查报告）",
                                state="complete")
                        else:
                            status.update(label=f"🎉 {filename} 全部流程圆满完成！", state="complete")
            except Exception as e:
                st.error(f"⚠️ {filename} 处理中断: {e}。进度已保存到本地 outputs/ 目录，"
                         f"刷新页面后可在左侧「本地任务」继续！")
                st.session_state.doc_states[job_id] = \
                    core.load_job_state(job_id) or st.session_state.doc_states[job_id]

            overall_bar.progress((task_idx + 1) / len(tasks))

# ================= 动态渲染过程资产面板（基于磁盘任务，刷新后仍可用）=================
saved_jobs_after = core.list_jobs()
if saved_jobs_after:
    st.divider()
    st.header("📦 项目过程资产沉淀")
    for job in saved_jobs_after:
        state = job["state"]
        filename = state.get("filename", "?")
        with st.expander(f"📁 资产面板: {filename}", expanded=True):
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)

            with col_d1:
                if state.get("p1_done") and state.get("paras"):
                    st.download_button(
                        "📥 1. 洗净后原文",
                        core.paragraphs_to_word(state["paras"]),
                        file_name=f"阶段1_清洗原文_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d1_{job['job_id']}", use_container_width=True)
            with col_d2:
                if state.get("auto_terms"):
                    st.download_button(
                        "🧠 1.5 提取术语库",
                        core.dict_to_excel(state["auto_terms"]),
                        file_name=f"自动抽词库_{filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dt_{job['job_id']}", use_container_width=True)
            with col_d3:
                if state.get("p2_done") and state.get("pairs"):
                    st.download_button(
                        "📥 2. 双语对照表",
                        core.pairs_to_word(state["pairs"]),
                        file_name=f"阶段2_双语对照_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d2_{job['job_id']}", use_container_width=True)
            with col_d4:
                if state.get("p3_done") and state.get("p3_md"):
                    st.download_button(
                        "📝 3. 翻译实践报告",
                        core.markdown_to_word(state["p3_md"], state.get("theory") or translation_theory),
                        file_name=f"阶段3_实践报告_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d3_{job['job_id']}", use_container_width=True)

            if state.get("p2_done"):
                stats = state.get("review_stats") or {}
                st.caption(
                    f"🔍 审校：{stats.get('reviewed_segments', 0)} 段通过 · "
                    f"blocking {stats.get('blocking', 0)} · actionable {stats.get('actionable', 0)} · "
                    f"informational {stats.get('informational', 0)} · "
                    f"记忆复用 {state.get('tm_used_count', 0)} 段")
                if state.get("findings"):
                    st.download_button(
                        "🧾 审查报告 (.md)",
                        core.findings_report_md(state),
                        file_name=f"审查报告_{filename}.md",
                        mime="text/markdown",
                        key=f"rr_{job['job_id']}", use_container_width=True)

            if state.get("p3_md"):
                st.markdown(state["p3_md"])

            if st.button("🗑 删除该任务及本地进度", key=f"del_{job['job_id']}"):
                core.delete_job(job["job_id"])
                st.session_state.doc_states.pop(job["job_id"], None)
                st.rerun()
