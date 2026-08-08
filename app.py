"""MTI 翻译实践小助手 —— Streamlit 界面层。

新增“术语准备与审核”面板：
- 高质量模式：术语冻结后才能开始翻译（未冻结时翻译按钮不可执行并显示原因）；
- 文档画像可查看、可人工修改后保存；
- 快速模式：自动术语作为 provisional 直接翻译（原体验不变）；
- 刷新/重启后自动恢复到术语审核阶段，不重新抽取。
"""
import json
import re

import pandas as pd
import streamlit as st

import core
from mti_tool import assets as _assets
from mti_tool import delivery as _delivery

# ================= 页面全局设置 =================
st.set_page_config(page_title="MTI 翻译实践小助手", page_icon="🎓", layout="wide")

if "doc_states" not in st.session_state:
    st.session_state.doc_states = {}
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None

# ================= 术语审核面板工具函数 =================
_EVIDENCE_LABELS = {
    "user": "用户提供", "local_termbase": "本地术语库",
    "project_override": "项目覆盖", "model_knowledge": "模型知识",
    "external": "外部来源",
}


def _evidence_label(e):
    evs = e.get("evidence") or []
    parts = []
    for ev in evs[:2]:
        label = _EVIDENCE_LABELS.get(ev.get("evidence_type"), ev.get("evidence_type"))
        note = (ev.get("note") or "").strip()
        parts.append(f"{label}：{note}" if note else label)
    return "；".join(parts)


def _conflict(e, entries):
    src = (e.get("source") or "").casefold()
    pref = e.get("preferred") or e.get("target")
    for other in entries:
        if other is e:
            continue
        if (other.get("source") or "").casefold() == src \
                and (other.get("preferred") or other.get("target")) != pref:
            return "⚠️ 冲突"
    return ""


def _first_context(e, paras, width=60):
    occ = e.get("occurrences") or []
    if not occ or not paras:
        return ""
    first = occ[0]
    if not (0 <= first < len(paras)):
        return ""
    text = paras[first]
    return text[:width] + ("…" if len(text) > width else "")


def _glossary_dataframe(entries, paras):
    rows = []
    for e in entries:
        rows.append({
            "选择": False,
            "id": e.get("id", ""),
            "source": e.get("source", ""),
            "proposed_target": e.get("proposed_target") or e.get("target", ""),
            "target": e.get("target", ""),
            "preferred": e.get("preferred", ""),
            "forbidden": "；".join(e.get("forbidden") or []),
            "behavior": e.get("behavior", "translate"),
            "status": e.get("status", "provisional"),
            "domain": e.get("domain", ""),
            "scope": e.get("scope", ""),
            "note": e.get("note", ""),
            "confidence": float(e.get("confidence") or 0.5),
            "出现次数": len(e.get("occurrences") or []),
            "上下文": _first_context(e, paras),
            "证据": _evidence_label(e),
            "冲突": _conflict(e, entries),
            "payload": json.dumps(e, ensure_ascii=False),
        })
    return pd.DataFrame(rows)


def _df_to_entries(df):
    entries = []
    for _, row in df.iterrows():
        base = {}
        payload = row.get("payload")
        if isinstance(payload, str) and payload.strip():
            try:
                base = json.loads(payload)
            except Exception:
                base = {}
        if not isinstance(base, dict):
            base = {}
        base = dict(base)

        def _s(key):
            v = row.get(key)
            return "" if pd.isna(v) else str(v).strip()

        base.update({
            "source": _s("source"),
            "proposed_target": _s("proposed_target"),
            "target": _s("target") or _s("proposed_target"),
            "preferred": _s("preferred") or _s("target") or _s("proposed_target"),
            "forbidden": [x.strip() for x in re.split(r"[;；]", _s("forbidden"))
                          if x.strip()],
            "behavior": (_s("behavior") or "translate").lower(),
            "status": (_s("status") or "provisional").lower(),
            "domain": _s("domain"),
            "scope": _s("scope"),
            "note": _s("note"),
        })
        try:
            base["confidence"] = float(row.get("confidence") or 0.5)
        except (TypeError, ValueError):
            base["confidence"] = 0.5
        entries.append(base)
    return entries


def _render_profile_editor(job_id, state):
    profile = state.get("document_profile") or {}
    with st.expander("📋 文档画像（AI 生成，可修改后保存）", expanded=False):
        c1, c2, c3 = st.columns(3)
        domain = c1.text_input("领域 domain", value=profile.get("domain") or "",
                               key=f"pf_d_{job_id}")
        subdomain = c2.text_input("细分领域 subdomain",
                                  value=profile.get("subdomain") or "",
                                  key=f"pf_sd_{job_id}")
        genre = c3.text_input("文本类型 genre", value=profile.get("genre") or "",
                              key=f"pf_g_{job_id}")
        audience = c1.text_input("读者 audience", value=profile.get("audience") or "",
                                 key=f"pf_a_{job_id}")
        register = c2.text_input("语域 register", value=profile.get("register") or "",
                                 key=f"pf_r_{job_id}")
        confidence = c3.slider("置信度", 0.0, 1.0,
                               float(profile.get("confidence") or 0.0),
                               key=f"pf_c_{job_id}")
        style_constraints = st.text_area(
            "风格约束 style_constraints",
            value=profile.get("style_constraints") or "", key=f"pf_sc_{job_id}")
        if st.button("💾 保存文档画像", key=f"pf_save_{job_id}"):
            core.save_document_profile(job_id, {
                "domain": domain, "subdomain": subdomain, "genre": genre,
                "audience": audience, "register": register,
                "style_constraints": style_constraints, "confidence": confidence,
                "sections": profile.get("sections") or [],
            })
            st.rerun()
        secs = profile.get("sections") or []
        if secs:
            st.caption("分节：" + "；".join(
                f"{s.get('section_id')}（段落 {s.get('start_segment')}-{s.get('end_segment')}"
                f"，{s.get('topic') or s.get('domain') or '?'}）" for s in secs))
        elif not state.get("profile_done"):
            st.caption("⚠️ 画像未生成（AI 失败或已跳过），可在此人工填写后保存。")


def _asset_prefix(state):
    """draft/final 资产文件名前缀：非 final 一律明确标注 draft。"""
    return "final_" if state.get("delivery_status") == "final" else "draft_"


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
    mode_label = st.selectbox(
        "翻译模式", ["快速模式", "高质量模式"], index=0,
        help="快速模式：自动术语作为建议（provisional）直接翻译；"
             "高质量模式：术语审核冻结后才能开始翻译。")
    mode = "quality" if mode_label == "高质量模式" else "quick"
    auto_term = st.checkbox("🤖 智能抽取术语库 (翻译前执行)", value=True,
                            help="大模型自动提取专有名词并生成 Excel 术语库")
    enable_report = st.checkbox("📝 自动生成实践报告", value=True)
    enable_review = st.checkbox("🔍 独立审校 (Review)", value=True,
                                help="翻译后由独立审校 pass 检查语义/术语问题；通过审校的段落才会进入翻译记忆")
    enable_annotate = st.checkbox("🎨 自动标注学习重点（红/黄/青绿）", value=True,
                                  help="生僻词标红、专业名词（特殊译法）标黄、翻译难点句标青绿，"
                                       "在双语对照表中同时高亮原文与译文")
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
        resume_choice = st.selectbox("选择要继续的任务（可不重新上传文件）",
                                     ["— 不继续 —"] + job_choices)
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
run_clicked = st.button("🚀 开始 / 继续处理 (断点续传)", type="primary",
                        use_container_width=True)
pending_job = st.session_state.pop("pending_continue_job", None)

tasks = []
seen = set()
if run_clicked:
    has_resume = bool(saved_jobs and resume_choice and resume_choice != "— 不继续 —")
    if not uploaded_files and not has_resume:
        st.error("请上传文件，或在左侧选择要继续的本地任务！")
    else:
        for f in uploaded_files:
            file_bytes = f.read()
            job_id = core.file_job_id(file_bytes)
            if job_id in seen:
                continue
            seen.add(job_id)
            tasks.append({"job_id": job_id, "filename": f.name,
                          "file_bytes": file_bytes})
        if has_resume:
            job = saved_jobs[job_choices.index(resume_choice)]
            if job["job_id"] not in seen:
                tasks.append({"job_id": job["job_id"],
                              "filename": job["state"].get("filename", "?"),
                              "file_bytes": None})
                st.session_state.active_job_id = job["job_id"]
elif pending_job:
    job = next((j for j in (saved_jobs or []) if j["job_id"] == pending_job), None)
    if job:
        tasks.append({"job_id": job["job_id"],
                      "filename": job["state"].get("filename", "?"),
                      "file_bytes": None})
        st.session_state.active_job_id = job["job_id"]

if tasks:
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
                    enable_annotate=enable_annotate, mode=mode,
                    on_status=lambda label: status.update(label=label, state="running"),
                    on_caption=lambda text: st.caption(text),
                )
                st.session_state.doc_states[job_id] = state
                st.session_state.active_job_id = job_id
                for warn in state.get("warnings", []):
                    st.warning(warn)
                if state["p1_done"] and state["p2_done"] \
                        and (not enable_report or state["p3_done"]):
                    if state.get("has_blocking"):
                        status.update(
                            label=f"⚠️ {filename} 流程完成，但有 blocking 问题待确认（见资产面板审查报告）",
                            state="complete")
                    else:
                        status.update(
                            label=f"✅ {filename} 流程完成（交付状态：draft，"
                                  f"可在资产面板确认最终交付）",
                            state="complete")
                else:
                    status.update(
                        label=f"⏸ {filename} 进度已保存（当前阶段：{state.get('stage', '?')}），"
                              f"可在下方继续操作",
                        state="complete")
        except Exception as e:
            st.error(f"⚠️ {filename} 处理中断: {e}。进度已保存到本地 outputs/ 目录，"
                     f"刷新页面后可在左侧「本地任务」继续！")
            st.session_state.doc_states[job_id] = \
                core.load_job_state(job_id) or st.session_state.doc_states[job_id]

        overall_bar.progress((task_idx + 1) / len(tasks))

# ================= 术语准备与审核面板（刷新/重启后自动恢复）=================
saved_jobs_after = core.list_jobs()
active = st.session_state.get("active_job_id")
if active is None and saved_jobs_after:
    for job in saved_jobs_after:
        s = job["state"]
        if s.get("p1_done") and not s.get("p2_done") and s.get("quality_mode") \
                and s.get("glossary") is not None:
            active = job["job_id"]
            break
st.session_state.active_job_id = active

if active:
    astate = core.load_job_state(active)
    if astate and astate.get("p1_done") and not astate.get("p2_done") \
            and astate.get("quality_mode") and astate.get("glossary") is not None:
        st.divider()
        st.subheader(f"🧬 术语准备与审核：{astate.get('filename', '?')}")
        _render_profile_editor(active, astate)

        entries = astate.get("glossary") or []
        frozen = astate.get("glossary_frozen")
        bypassed = astate.get("quality_bypass")
        if frozen:
            st.success(f"✅ 术语表已冻结：版本 v{frozen.get('version')} · "
                       f"hash {str(frozen.get('glossary_hash', ''))[:12]}… · "
                       f"冻结时间 {frozen.get('frozen_at', '')}")
        elif bypassed:
            st.info("⚡ 已选择跳过人工冻结（快速模式）：术语以 provisional 建议注入翻译。")
        else:
            st.warning("⛔ 术语尚未冻结：高质量模式下「开始翻译」不可执行。"
                       "请完成审核后冻结，或选择跳过冻结。")

        df = _glossary_dataframe(entries, astate.get("paras") or [])
        edited = st.data_editor(
            df,
            key=f"glossary_editor_{active}",
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "选择": st.column_config.CheckboxColumn("选择", default=False),
                "id": st.column_config.TextColumn("ID", disabled=True),
                "source": st.column_config.TextColumn("源术语", required=True),
                "proposed_target": st.column_config.TextColumn("建议译名"),
                "target": st.column_config.TextColumn("目标译名"),
                "preferred": st.column_config.TextColumn("首选译名"),
                "forbidden": st.column_config.TextColumn("禁止译名（;分隔）"),
                "behavior": st.column_config.SelectboxColumn(
                    "行为", options=["translate", "preserve"]),
                "status": st.column_config.SelectboxColumn(
                    "状态", options=["candidate", "provisional", "locked", "rejected"]),
                "domain": st.column_config.TextColumn("领域"),
                "scope": st.column_config.TextColumn("范围"),
                "note": st.column_config.TextColumn("备注"),
                "confidence": st.column_config.NumberColumn(
                    "置信度", min_value=0.0, max_value=1.0, step=0.05),
                "出现次数": st.column_config.NumberColumn("出现次数", disabled=True),
                "上下文": st.column_config.TextColumn("部分上下文", disabled=True),
                "证据": st.column_config.TextColumn("证据", disabled=True),
                "冲突": st.column_config.TextColumn("冲突", disabled=True),
                "payload": st.column_config.TextColumn("payload", disabled=True),
            },
        )

        selected = edited[edited["选择"].fillna(False)] if "选择" in edited.columns \
            else edited.iloc[0:0]
        sel_ids = [str(x) for x in selected["id"].tolist() if str(x)]

        c1, c2, c3 = st.columns(3)
        if c1.button("💾 保存草稿", key=f"gs_{active}", use_container_width=True):
            core.save_glossary_draft(active, _df_to_entries(edited))
            st.rerun()
        if c2.button("🔒 锁定选中术语", disabled=not sel_ids, key=f"gl_{active}",
                     use_container_width=True):
            core.set_glossary_entry_status(active, sel_ids, "locked")
            st.rerun()
        if c3.button("🚫 拒绝选中术语", disabled=not sel_ids, key=f"gr_{active}",
                     use_container_width=True):
            core.set_glossary_entry_status(active, sel_ids, "rejected")
            st.rerun()

        c4, c5, c6 = st.columns(3)
        if c4.button("❄️ 冻结术语表并继续翻译", key=f"gf_{active}",
                     use_container_width=True):
            core.freeze_glossary(active, entries=_df_to_entries(edited), frozen_by="用户")
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if c5.button("⚡ 跳过冻结（快速模式）并翻译", key=f"gb_{active}",
                     use_container_width=True):
            core.save_glossary_draft(active, _df_to_entries(edited))
            core.bypass_freeze(active)
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if c6.button("🚀 开始翻译", disabled=not (frozen or bypassed),
                     key=f"gt_{active}", use_container_width=True):
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if not frozen and not bypassed:
            st.caption("⛔ 翻译未开始：请先「冻结术语表并继续翻译」，"
                       "或选择跳过冻结（快速模式）。")

# ================= 动态渲染过程资产面板（基于磁盘任务，刷新后仍可用）=================
if saved_jobs_after:
    st.divider()
    st.header("📦 项目过程资产沉淀")
    for job in saved_jobs_after:
        state = job["state"]
        filename = state.get("filename", "?")
        with st.expander(f"📁 资产面板: {filename}", expanded=True):
            dstatus = state.get("delivery_status") or "draft"
            if dstatus == "final":
                st.success("✅ 交付状态：最终交付（final）")
            elif dstatus == "review_required":
                st.warning(f"⚠️ 交付状态：{core.delivery_status_label(state)}"
                           "（存在 blocking，未最终交付）")
            else:
                st.caption(f"📦 交付状态：{core.delivery_status_label(state)}"
                           "（当前为 draft 资产，尚未最终交付）")
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)

            with col_d1:
                if state.get("p1_done") and state.get("paras"):
                    st.download_button(
                        "📥 1. 洗净后原文",
                        core.paragraphs_to_word(state["paras"]),
                        file_name=f"{_asset_prefix(state)}阶段1_清洗原文_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d1_{job['job_id']}", use_container_width=True)
            with col_d2:
                if state.get("auto_terms"):
                    st.download_button(
                        "🧠 1.5 提取术语库",
                        core.dict_to_excel(state["auto_terms"]),
                        file_name=f"{_asset_prefix(state)}自动抽词库_{filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dt_{job['job_id']}", use_container_width=True)
            with col_d3:
                if state.get("p2_done") and state.get("pairs"):
                    st.download_button(
                        "📥 2. 双语对照表",
                        core.pairs_to_word(state["pairs"],
                                           annotations=state.get("annotations")),
                        file_name=f"{_asset_prefix(state)}阶段2_双语对照_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d2_{job['job_id']}", use_container_width=True)
            with col_d4:
                if state.get("p3_done") and state.get("p3_md"):
                    st.download_button(
                        "📝 3. 翻译实践报告",
                        core.markdown_to_word(state["p3_md"], state.get("theory") or translation_theory),
                        file_name=f"{_asset_prefix(state)}阶段3_实践报告_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"d3_{job['job_id']}", use_container_width=True)

            if state.get("document_profile"):
                prof = state["document_profile"]
                st.caption(
                    f"📋 画像：领域 {prof.get('domain') or '?'} · "
                    f"类型 {prof.get('genre') or '?'} · 语域 {prof.get('register') or '?'} · "
                    f"置信度 {prof.get('confidence') or 0}")

            if state.get("p2_done"):
                stats = state.get("review_stats") or {}
                st.caption(
                    f"🔍 审校：{stats.get('reviewed_segments', 0)} 段通过 · "
                    f"blocking {stats.get('blocking', 0)} · actionable {stats.get('actionable', 0)} · "
                    f"informational {stats.get('informational', 0)} · "
                    f"记忆复用 {state.get('tm_used_count', 0)} 段")
                exported = _assets.export_all(
                    state, job["job_id"], target_lang, ai_provider, ai_model,
                    source_filename=filename)
                ea1, ea2, ea3, ea4 = st.columns(4)
                with ea1:
                    st.download_button(
                        "🏷 TBX 术语库",
                        exported["terms.tbx"],
                        file_name=f"{_asset_prefix(state)}terms_{filename}.tbx",
                        mime="application/xml", key=f"tbx_{job['job_id']}",
                        use_container_width=True)
                with ea2:
                    st.download_button(
                        "🧠 TMX 翻译记忆",
                        exported["memory.tmx"],
                        file_name=f"{_asset_prefix(state)}memory_{filename}.tmx",
                        mime="application/xml", key=f"tmx_{job['job_id']}",
                        use_container_width=True)
                with ea3:
                    st.download_button(
                        "🗒 JSONL 双语段落",
                        exported["bilingual.jsonl"],
                        file_name=f"{_asset_prefix(state)}bilingual_{filename}.jsonl",
                        mime="application/x-jsonlines",
                        key=f"jl_{job['job_id']}", use_container_width=True)
                with ea4:
                    st.download_button(
                        "📦 交付清单 manifest",
                        exported["delivery_manifest.json"],
                        file_name=f"{_asset_prefix(state)}delivery_manifest_{filename}.json",
                        mime="application/json", key=f"mf_{job['job_id']}",
                        use_container_width=True)
                unresolved = _delivery.unresolved_findings(state)
                if dstatus == "review_required" and unresolved:
                    chosen = []
                    for f in unresolved:
                        fid = _delivery.finding_id(f)
                        label = (f"`{fid}` 段 {f.get('segment_index', -1) + 1} "
                                 f"[{f.get('severity')}] {f.get('reason')}")
                        if st.checkbox(label, key=f"fd_{job['job_id']}_{fid}"):
                            chosen.append(fid)
                    note = st.text_input("处理说明", key=f"fdnote_{job['job_id']}")
                    dc1, dc2, dc3 = st.columns(3)
                    if dc1.button("✅ 标记已人工修复", disabled=not chosen,
                                  key=f"fdfix_{job['job_id']}",
                                  use_container_width=True):
                        core.mark_findings_resolved(job["job_id"], chosen,
                                                    "human_fixed", note or "人工修复")
                        st.rerun()
                    if dc2.button("🔄 重新翻译选中段落", disabled=not chosen,
                                  key=f"fdrt_{job['job_id']}",
                                  use_container_width=True):
                        idxs = sorted({
                            f.get("segment_index") for f in unresolved
                            if _delivery.finding_id(f) in chosen
                            and isinstance(f.get("segment_index"), int)})
                        core.retranslate_segments(
                            job["job_id"], idxs, ai_provider, api_key, ai_model,
                            target_lang, style_rules=style_rules,
                            on_caption=lambda t: st.caption(t))
                        st.rerun()
                    if dc3.button("⚠️ 接受风险并进入 final",
                                  key=f"fdacc_{job['job_id']}",
                                  use_container_width=True):
                        core.approve_delivery(job["job_id"], note or "接受风险",
                                              accept_blocking=True)
                        st.rerun()
                elif dstatus != "final":
                    note2 = st.text_input("交付说明（可选）", key=f"fdn_{job['job_id']}")
                    if st.button("✅ 确认交付 (final)", key=f"fdok_{job['job_id']}"):
                        core.approve_delivery(job["job_id"], note2 or "人工确认交付")
                        st.rerun()
                if state.get("human_actions"):
                    with st.expander("📜 人工处理记录"):
                        for ha in state["human_actions"][-20:]:
                            st.caption(f"{ha.get('timestamp')} · {ha.get('action')} · "
                                       f"{ha.get('finding_id')} · {ha.get('note')}")
                if state.get("findings"):
                    st.download_button(
                        "🧾 审查报告 (.md)",
                        core.findings_report_md(state),
                        file_name=f"{_asset_prefix(state)}审查报告_{filename}.md",
                        mime="text/markdown",
                        key=f"rr_{job['job_id']}", use_container_width=True)

            if state.get("p3_md"):
                st.markdown(state["p3_md"])

            if st.button("🗑 删除该任务及本地进度", key=f"del_{job['job_id']}"):
                core.delete_job(job["job_id"])
                st.session_state.doc_states.pop(job["job_id"], None)
                st.rerun()
