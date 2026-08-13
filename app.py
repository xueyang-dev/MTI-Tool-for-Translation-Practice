"""MTI Tool Streamlit 界面层。

信息架构：左侧产品导航 + 四步任务创建 + 运行后任务工作台。AI Provider
与翻译记忆属于全局设置；学术报告属于翻译后的下游工作流，不占据文档首屏。
"""
import json
import re
from html import escape

import pandas as pd
import streamlit as st

import core
from mti_tool import assets as _assets
from mti_tool import delivery as _delivery
from mti_tool import report_evidence as _report_evidence

# ================= 页面全局设置 =================
st.set_page_config(page_title="MTI Tool", page_icon="M", layout="wide",
                   initial_sidebar_state="expanded")

if "doc_states" not in st.session_state:
    st.session_state.doc_states = {}
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None
if "task_step" not in st.session_state:
    st.session_state.task_step = 1
if "provider_configured" not in st.session_state:
    st.session_state.provider_configured = False
if "provider_connection_status" not in st.session_state:
    st.session_state.provider_connection_status = "unverified"
_initial_jobs = core.list_jobs()
_pending_quality_job = next((
    job["job_id"] for job in _initial_jobs
    if job["state"].get("p1_done") and not job["state"].get("p2_done")
    and job["state"].get("quality_mode")
    and job["state"].get("glossary") is not None
), None)
if _pending_quality_job and "app_view" not in st.session_state:
    st.session_state.update(app_view="workspace", workspace_mode=True,
                            active_job_id=_pending_quality_job)

# ================= 设计系统（Research IDE 国际蓝） =================
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
 --mti-canvas: #f7f8fa;
 --mti-surface: #ffffff;
 --mti-ink: #111827;
 --mti-sub: #6b7280;
 --mti-faint: #9ca3af;
 --mti-line: #e5e7eb;
 --mti-blue: #2563eb;
 --mti-blue-deep: #1d4ed8;
 --mti-blue-soft: #eff6ff;
 --mti-success: #16a34a;
 --mti-danger: #dc2626;
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
 font-family: 'Manrope', ui-sans-serif, system-ui, -apple-system,
 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC',
 sans-serif !important;
}

.stApp {
 background: var(--mti-canvas);
}
[data-testid="stHeader"] { display: none; }
[data-testid="stDecoration"] { display: none; }
footer { visibility: hidden; }
[data-testid="stMainBlockContainer"] {
 width: min(100%, 1152px); max-width: 1152px; margin-left: 0; margin-right: auto;
 padding: 1.5rem 3.5rem 4rem;
}

/* ---------- Typography ---------- */
h1, h2, h3, h4, [data-testid="stHeadingWithActionElements"] {
 color: var(--mti-ink) !important;
 letter-spacing: -.02em; font-weight: 650;
}
h1 { font-size: 30px !important; line-height: 1.25 !important; }
h2 { font-size: 20px !important; }
h3 { font-size: 16px !important; }
p, label, input, textarea, [data-baseweb="select"] { font-size: 14px !important; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--mti-sub); }
a { color: var(--mti-blue); }
hr { border-color: var(--mti-line); }
::selection { background: rgba(37,99,235,.16); }

/* ---------- Product shell ---------- */
[data-testid="stSidebar"] {
 background: var(--mti-surface); border-right: 1px solid var(--mti-line);
 width: 236px !important; min-width: 236px !important;
}
[data-testid="stSidebarContent"] { padding-top: 20px; padding-bottom: 82px; }
[data-testid="stSidebarContent"] [data-testid="stVerticalBlock"] { gap: .5rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height: 1.5; }
[data-testid="stSidebar"] .stButton > button {
 min-height: 36px; justify-content: flex-start; border-color: transparent;
 background: transparent; color: #4b5563; font-weight: 500;
}
[data-testid="stSidebar"] .stButton > button:hover {
 background: #f3f4f6; border-color: transparent; color: var(--mti-ink);
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
 background: var(--mti-blue-soft); border-color: transparent; color: var(--mti-blue-deep);
}
.mti-brand { padding: 2px 4px 18px; }
.mti-brand strong { display: block; font-size: 18px; color: var(--mti-ink); letter-spacing: -.02em; }
.mti-brand span { display: block; margin-top: 4px; font-size: 11px; color: #7b8493; line-height: 1.5; }
.mti-nav-label { margin: 18px 0 8px; font-size: 11px; font-weight: 700; letter-spacing: .06em; color: #7b8493; }
.mti-nav-divider { height: 1px; margin: 14px 0 4px; background: var(--mti-line); }
.st-key-new_task_action .stButton > button {
 border-color: var(--mti-line); background: #fff; color: var(--mti-ink); font-weight: 600;
}
.st-key-task_steps { position: relative; gap: 0 !important; margin: 0 0 6px; }
.st-key-task_steps::before {
 content: ""; position: absolute; left: 17px; top: 21px; height: calc(100% - 42px);
 width: 1px; background: #d7dce3;
}
.st-key-task_steps .stButton { position: relative; z-index: 1; margin: 0; }
.st-key-task_steps .stButton > button {
 min-height: 42px; padding: 0 8px; background: transparent; border-color: transparent;
}
.st-key-task_steps .stButton > button > div { width: 100%; }
.st-key-task_steps .stButton > button > div > span {
 display: grid !important; grid-template-columns: 18px minmax(0,1fr);
 column-gap: 8px; align-items: center; width: 100%;
}
.st-key-task_steps .stButton > button[kind="primary"] {
 background: transparent; border-color: transparent; color: var(--mti-blue-deep); font-weight: 650;
}
.st-key-task_steps button[data-testid="stBaseButton-primary"] {
 background: transparent !important; border-color: transparent !important;
 color: var(--mti-blue-deep) !important;
}
.st-key-task_steps [data-testid="stIconMaterial"] {
 position: relative; z-index: 2; background: var(--mti-surface); border-radius: 50%;
}
[class*="st-key-task_step_done_"] [data-testid="stIconMaterial"] { color: var(--mti-success); }
[class*="st-key-task_step_current_"] [data-testid="stIconMaterial"] { color: var(--mti-blue); }
[class*="st-key-task_step_pending_"] [data-testid="stIconMaterial"] { color: #a3aab5; }
.mti-engine-row, .mti-summary, .mti-pipeline {
 border: 1px solid var(--mti-line); border-radius: 10px; background: var(--mti-surface);
}
.mti-engine-row { padding: 12px 14px; margin: 6px 0 18px; }
.mti-engine-row strong { font-size: 13px; color: var(--mti-ink); }
.mti-engine-row span { display: block; margin-top: 3px; font-size: 12px; color: var(--mti-sub); }
.st-key-provider_status {
 position: fixed; left: 16px; bottom: 12px; z-index: 30; width: 204px;
 margin: 0; padding: 11px 2px 0; border-top: 1px solid var(--mti-line);
 background: var(--mti-surface);
}
.st-key-provider_status [data-testid="stHorizontalBlock"] { align-items: center; gap: 6px; }
.st-key-provider_status .stButton > button {
 min-height: 30px; padding: 2px 6px; justify-content: flex-end; color: var(--mti-blue-deep);
}
.mti-provider { position: relative; padding-left: 17px; }
.mti-provider::before {
 content: ""; position: absolute; left: 2px; top: 5px; width: 8px; height: 8px;
 border-radius: 50%; background: var(--mti-surface); border: 1px solid #98a2b3;
}
.mti-provider.is-connected::before { background: var(--mti-success); border-color: var(--mti-success); }
.mti-provider.is-error::before { background: var(--mti-danger); border-color: var(--mti-danger); }
.mti-provider strong { display: block; font-size: 13px; color: var(--mti-ink); font-weight: 600; }
.mti-provider span { display: block; margin-top: 2px; color: var(--mti-sub); font-size: 11px; overflow-wrap: anywhere; }
.mti-title { margin: 3px 0 20px; }
.mti-title h1 { margin: 0; font-size: 30px; font-weight: 650; color: var(--mti-ink); letter-spacing: -.025em; }
.mti-title p { margin: 6px 0 0; color: var(--mti-sub); font-size: 14px; }
.mti-section-title { margin: 0 0 4px; font-size: 19px; font-weight: 650; color: var(--mti-ink); }
.mti-section-sub { margin: 0 0 12px; font-size: 13px; color: #667085; }
.mti-summary { padding: 18px 20px; }
.mti-summary-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 18px 28px; }
.mti-summary-item span { display: block; font-size: 12px; color: var(--mti-sub); }
.mti-summary-item strong { display: block; margin-top: 4px; font-size: 14px; color: var(--mti-ink); font-weight: 600; }
.mti-flow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.mti-flow span { font-size: 12px; color: var(--mti-sub); }
.mti-flow b { color: #c4c7ce; font-weight: 500; }

/* ---------- Controls & cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
 border: 1px solid var(--mti-line); border-radius: 10px;
 background: var(--mti-surface); box-shadow: none;
}
.stButton > button, [data-testid="stDownloadButton"] > button {
 min-height: 40px; border-radius: 8px; font-weight: 600; cursor: pointer;
 border: 1px solid var(--mti-line); background: var(--mti-surface); color: var(--mti-ink);
 box-shadow: none; transition: border-color .15s ease, background .15s ease, color .15s ease;
}
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
 border-color: #bfdbfe; color: var(--mti-blue-deep); background: #f8fbff;
}
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
 background: var(--mti-blue); border: 1px solid var(--mti-blue); color: #fff; box-shadow: none;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
 background: var(--mti-blue-deep); border-color: var(--mti-blue-deep); color: #fff;
}
.stButton > button:disabled,
button[data-testid="stBaseButton-primary"]:disabled {
 opacity: 1; cursor: not-allowed; box-shadow: none;
 background: #dbe4f5 !important; border-color: #dbe4f5 !important; color: #8293b4 !important;
}
.stButton > button:focus-visible, [data-testid="stDownloadButton"] > button:focus-visible,
button[data-baseweb="tab"]:focus-visible, summary:focus-visible {
 outline: 3px solid rgba(37,99,235,.28) !important;
 outline-offset: 2px;
}

/* ---------- Tabs ---------- */
[data-testid="stTabs"] [role="tablist"] {
 background: transparent; border-bottom: 1px solid var(--mti-line); padding: 0; gap: 22px;
}
button[data-baseweb="tab"] {
 border-radius: 0 !important; padding: 7px 0 9px; font-weight: 550; color: var(--mti-sub); background: transparent;
}
button[data-baseweb="tab"]:hover { color: var(--mti-blue-deep); }
button[data-baseweb="tab"][aria-selected="true"] {
 background: transparent; color: var(--mti-blue-deep); box-shadow: inset 0 -2px var(--mti-blue);
}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }

/* ---------- 输入控件 ---------- */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
 border-radius: 8px !important; border-color: var(--mti-line) !important;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-baseweb="select"] > div { min-height: 40px; }
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
 border-color: var(--mti-blue) !important;
 box-shadow: 0 0 0 3px rgba(37,99,235,.16) !important;
}
.stSelectbox .react-aria-ComboBox > div {
 border-radius: 8px !important; border: 1px solid var(--mti-line) !important;
 background: var(--mti-surface) !important; color: var(--mti-ink) !important;
 box-shadow: none !important;
}
.stSelectbox [role="combobox"] {
 border: 0 !important; border-radius: 8px !important; background: transparent !important;
 color: var(--mti-ink) !important; box-shadow: none !important;
}
.stSelectbox [role="combobox"] *,
.stSelectbox [role="combobox"] svg { color: var(--mti-ink) !important; fill: currentColor !important; }
.stSelectbox .react-aria-ComboBox button {
 background: transparent !important; border: 0 !important; color: var(--mti-ink) !important;
 box-shadow: none !important;
}
.stSelectbox .react-aria-ComboBox button svg,
.stSelectbox .react-aria-ComboBox button [data-testid="stIconMaterial"] {
 color: var(--mti-ink) !important; fill: currentColor !important; visibility: visible !important;
}
[data-baseweb="select"] > div:focus-within {
 border-color: var(--mti-blue) !important;
 box-shadow: 0 0 0 3px rgba(37,99,235,.16) !important;
}
.stSelectbox .react-aria-ComboBox > div:focus-within {
 border-color: var(--mti-blue) !important;
 box-shadow: 0 0 0 3px rgba(37,99,235,.16) !important;
}
[data-testid="stFileUploaderDropzone"] {
 min-height: 148px; border-radius: 10px; border: 1px dashed #cbd5e1; background: #fff;
 transition: all .15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
 border-color: var(--mti-blue); background: var(--mti-blue-soft);
}
.st-key-source_documents { position: relative; }
.mti-source-label {
 margin: 0 0 8px; color: var(--mti-ink); font-size: 14px; font-weight: 600; line-height: 20px;
}
.st-key-source_documents .mti-upload-copy {
 position: absolute; z-index: 2; pointer-events: none; top: 80px; left: 0; right: 0;
 display: flex; flex-direction: column; align-items: center; text-align: center;
}
.mti-upload-copy .material-symbols-rounded {
 margin-bottom: 5px; color: var(--mti-blue); font-size: 20px;
 font-family: "Material Symbols Rounded" !important; font-weight: normal;
 font-style: normal; line-height: 1; letter-spacing: normal; text-transform: none;
 white-space: nowrap; word-wrap: normal; direction: ltr;
 -webkit-font-feature-settings: "liga"; -webkit-font-smoothing: antialiased;
 font-feature-settings: "liga";
}
.mti-upload-copy span { color: var(--mti-ink); font-size: 14px; font-weight: 600; }
.mti-upload-copy small { margin-top: 5px; color: #7b8493; font-size: 12px; }
.st-key-source_documents [data-testid="stFileUploaderDropzone"] {
 position: relative; padding: 0; align-items: stretch; justify-content: stretch; cursor: pointer;
}
.st-key-source_documents [data-testid="stFileUploaderDropzone"] > div { width: 100%; }
.st-key-source_documents [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
.st-key-source_documents [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
 position: absolute; inset: 0; width: 100%; height: 100%; transform: none;
 border: 0 !important; background: transparent !important; color: transparent !important;
}
.st-key-source_documents [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] p,
.st-key-source_documents [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] svg,
.st-key-source_documents [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] [data-testid="stIconMaterial"] {
 visibility: hidden;
}
.st-key-source_documents [data-testid="stFileUploaderDropzone"]:focus-within {
 border-color: var(--mti-blue); box-shadow: 0 0 0 3px rgba(37,99,235,.16);
}
.st-key-source_documents [data-testid="stFileUploaderFile"] { display: none; }
.mti-source-file {
 display: flex; align-items: center; gap: 12px; min-height: 74px; padding: 12px 14px;
 border: 1px solid var(--mti-line); border-radius: 10px; background: var(--mti-surface);
}
.mti-source-file .material-symbols-rounded {
 color: var(--mti-blue); font-size: 22px; font-family: "Material Symbols Rounded" !important;
 font-weight: normal; font-style: normal; line-height: 1; letter-spacing: normal;
 text-transform: none; white-space: nowrap; font-feature-settings: "liga";
}
.mti-source-file-copy { min-width: 0; flex: 1; }
.mti-source-file-copy strong { display: block; color: var(--mti-ink); font-size: 14px; overflow-wrap: anywhere; }
.mti-source-file-copy span { display: block; margin-top: 3px; color: var(--mti-sub); font-size: 12px; }
.mti-source-file-status { color: var(--mti-blue-deep); font-size: 12px; font-weight: 600; white-space: nowrap; }
.mti-source-file-status.is-parsing { color: #b45309; }
.mti-source-file-status.is-parsed { color: var(--mti-success); }
.mti-source-file-status.is-error { color: var(--mti-danger); }
.st-key-source_file_summary { margin-bottom: 8px; }
.st-key-source_file_card { position: relative; min-height: 74px; }
.st-key-source_file_card .mti-source-file { padding-right: 54px; }
.st-key-source_file_card > [data-testid="stElementContainer"]:has(.mti-source-file) {
 position: relative; z-index: 1;
}
.st-key-source_file_card > [data-testid="stElementContainer"]:has(.stButton) {
 position: absolute !important; right: 10px; top: 50%; z-index: 3;
 width: 36px !important; height: 36px !important; transform: translateY(-50%);
}
.st-key-source_file_card .stButton {
 width: 36px; height: 36px; margin: 0;
}
.st-key-source_file_card .stButton button {
 min-height: 36px !important; height: 36px !important; width: 36px; padding: 0;
 border-color: transparent !important; color: #7b8493 !important;
 background: transparent !important; box-shadow: none !important;
}
.st-key-source_file_card .stButton button:hover {
 border-color: #fecaca !important; background: #fef2f2 !important;
 color: var(--mti-danger) !important;
}
.st-key-source_file_card .stButton p {
 position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
 overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}
.st-key-target_language_field { max-width: 340px; margin-top: 12px; }
.st-key-target_language_field label,
.st-key-target_language_field [data-testid="stWidgetLabel"] {
 color: var(--mti-ink) !important; opacity: 1 !important; font-weight: 600 !important;
}
.mti-field-head { margin-top: 14px; }
.mti-field-head strong { display: block; color: var(--mti-ink); font-size: 14px; }
.mti-field-head span { display: block; margin-top: 4px; color: #667085; font-size: 13px; }
.st-key-termbase_attach { max-width: 340px; margin-top: 10px; }
.st-key-termbase_attach .stButton > button {
 background: var(--mti-surface) !important; border-color: var(--mti-line) !important;
 color: var(--mti-ink) !important;
}
.st-key-termbase_attach .stButton > button:hover {
 background: #f8fbff !important; border-color: #bfdbfe !important; color: var(--mti-blue-deep) !important;
}
.st-key-termbase_picker { max-width: 620px; margin-top: 8px; }
.st-key-termbase_picker [data-testid="stFileUploaderDropzone"] { min-height: 96px; }
.mti-attachment {
 display: flex; align-items: center; min-height: 62px; padding: 11px 13px;
 border: 1px solid var(--mti-line); border-radius: 8px; background: #fff;
}
.mti-attachment strong { display: block; color: var(--mti-ink); font-size: 13px; overflow-wrap: anywhere; }
.mti-attachment span { display: block; margin-top: 3px; color: var(--mti-sub); font-size: 12px; }
.st-key-termbase_attached { max-width: 620px; margin-top: 10px; }
.st-key-termbase_attached [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-termbase_attached .stButton > button { color: var(--mti-danger); }
.st-key-task_action_bar {
 position: fixed; left: calc(236px + 3.5rem); bottom: 0; z-index: 20;
 width: min(calc(100vw - 236px - 7rem), 1040px); margin: 0; padding: 10px 0 8px;
 border-top: 1px solid var(--mti-line); background: rgba(247,248,250,.98);
}
.st-key-task_action_bar [data-testid="stHorizontalBlock"] { align-items: center; }
.mti-autosave { color: #667085; font-size: 12px; }
.mti-autosave.is-saved { color: var(--mti-success); }
.st-key-task_action_bar button[data-testid="stBaseButton-primary"] {
 transition: background .18s ease, border-color .18s ease, color .18s ease, opacity .18s ease;
}
.st-key-library_nav .stButton > button {
 display: flex; align-items: center; justify-content: flex-start;
 gap: 12px; padding-left: 9px; text-align: left;
}
.st-key-library_nav .stButton > button > div { width: 100%; }
.st-key-library_nav .stButton > button [data-testid="stIconMaterial"] { flex: 0 0 32px; }
.st-key-library_nav .stButton > button [data-testid="stMarkdownContainer"] { flex: 1 1 auto; min-width: 0; }
.st-key-library_nav .stButton > button > div > span {
 display: grid; grid-template-columns: 32px minmax(0,1fr); column-gap: 12px;
 align-items: center; width: 100%;
}
.st-key-library_nav .stButton > button [data-testid="stIconMaterial"] {
 width: 32px; margin: 0; color: #667085; font-size: 18px;
}
.st-key-library_nav .stButton > button p { margin: 0; }
/* ---------- Translation strategy ---------- */
.st-key-preset_cards { margin-top: 8px; }
.st-key-preset_cards [data-testid="stHorizontalBlock"] { align-items: stretch; gap: 12px; }
[class*="st-key-preset_card_"] { position: relative; height: 180px; }
.mti-preset-card {
 height: 180px; padding: 16px; border: 1px solid var(--mti-line); border-radius: 10px;
 background: var(--mti-surface); transition: border-color .18s ease, background .18s ease;
}
[class*="st-key-preset_card_"]:has(button:hover) .mti-preset-card {
 border-color: #bfdbfe; background: #f8fbff;
}
[class*="st-key-preset_card_"][class*="_selected"] .mti-preset-card {
 border-color: var(--mti-blue); background: var(--mti-blue-soft);
}
.mti-preset-head { display: flex; align-items: center; gap: 8px; min-height: 22px; }
.mti-preset-head .material-symbols-rounded {
 color: #98a2b3; font-family: "Material Symbols Rounded" !important;
 font-size: 18px; font-weight: normal; line-height: 1; font-feature-settings: "liga";
}
[class*="st-key-preset_card_"][class*="_selected"] .mti-preset-head .material-symbols-rounded {
 color: var(--mti-blue);
}
.mti-preset-head strong { color: var(--mti-ink); font-size: 15px; font-weight: 650; }
.mti-preset-badge {
 margin-left: auto; padding: 2px 7px; border-radius: 999px; background: #dbeafe;
 color: var(--mti-blue-deep); font-size: 11px; font-weight: 650;
}
.mti-preset-purpose { margin: 14px 0 0; color: #475467; font-size: 13px; }
.mti-preset-flow { margin: 16px 0 0; color: var(--mti-ink); font-size: 13px; font-weight: 650; }
.mti-preset-tradeoff { margin: 14px 0 0; color: var(--mti-sub); font-size: 12px; }
[class*="st-key-preset_card_"] .stButton {
 position: absolute; inset: 0; z-index: 3; margin: 0;
}
[class*="st-key-preset_card_"] .stButton > button {
 width: 100%; height: 180px; min-height: 180px; padding: 0; border: 0 !important;
 background: transparent !important; color: transparent !important; box-shadow: none !important;
}
[class*="st-key-preset_card_"] .stButton > button:focus-visible {
 outline: 3px solid rgba(37,99,235,.28) !important; outline-offset: 2px;
}
.st-key-strategy_advanced { margin-top: 16px; }
.st-key-strategy_advanced {
 border: 1px solid var(--mti-line); border-radius: 10px; background: var(--mti-surface);
 overflow: hidden;
}
.st-key-strategy_advanced .stButton > button {
 min-height: 44px; padding: 10px 14px; border: 0; border-radius: 0;
 background: var(--mti-surface); color: var(--mti-ink);
}
.st-key-strategy_advanced .stButton > button:hover { background: #f8fafc; }
.st-key-strategy_advanced .stButton > button:focus { box-shadow: none !important; }
.mti-strategy-state {
 margin: -4px 14px 12px 44px; color: var(--mti-sub); font-size: 12px;
}
.mti-strategy-state strong { color: var(--mti-blue-deep); font-weight: 650; }
.st-key-advanced_body { border-top: 1px solid var(--mti-line); padding: 4px 16px 14px; }
.mti-advanced-group { margin: 14px 0 6px; color: #475467; font-size: 12px; font-weight: 700; }
.st-key-strategy_advanced [data-testid="stToggle"] { margin: 0; }
.st-key-strategy_advanced [data-testid="stToggle"] label {
 min-height: 42px; padding: 8px 0; color: var(--mti-ink) !important;
}
.st-key-strategy_advanced [data-testid="stToggle"] [role="switch"] {
 background: #d0d5dd !important; border-color: #d0d5dd !important;
}
.st-key-strategy_advanced [data-testid="stToggle"] [role="switch"][aria-checked="true"] {
 background: var(--mti-blue) !important; border-color: var(--mti-blue) !important;
}
.st-key-strategy_advanced [data-testid="stToggle"] p { color: var(--mti-ink) !important; }
.st-key-strategy_advanced [data-testid="stCheckbox"] p { color: var(--mti-ink) !important; }
.st-key-strategy_advanced [data-testid="stCheckbox"] label > div:first-of-type {
 background: var(--mti-surface) !important; border-color: #98a2b3 !important;
}
.st-key-strategy_advanced [data-testid="stCheckbox"] label[data-selected="true"] > div:first-of-type {
 background: var(--mti-blue) !important; border-color: var(--mti-blue) !important;
}
.st-key-strategy_advanced [data-testid="stCheckbox"] label[data-selected="true"] svg {
 stroke: #fff !important;
}
.st-key-analysis_theory { max-width: 520px; margin-top: 8px; }
.mti-report-helper { margin: 0 0 4px; color: var(--mti-sub); font-size: 12px; }

/* ---------- 容器类组件 ---------- */
[data-testid="stExpander"] {
 border: 1px solid var(--mti-line) !important;
 border-radius: 10px !important; background: #fff; box-shadow: none; overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 600; color: var(--mti-ink); }
[data-testid="stExpander"] summary:hover { color: var(--mti-blue-deep); }
[data-testid="stAlert"] { border-radius: 8px; }
[data-testid="stDataFrame"] {
 border: 1px solid var(--mti-line); border-radius: 12px; overflow: hidden;
}
[data-testid="stProgress"] [role="progressbar"] > div { background: var(--mti-blue); }
[data-testid="stStatusWidget"] {
 border-radius: 14px; border-color: var(--mti-line) !important;
}

/* ---------- 响应式与减少动态效果 ---------- */
@media (max-width: 767px) {
 [data-testid="stSidebar"] { width: 236px !important; min-width: 236px !important; }
 [data-testid="stMainBlockContainer"] { width: 100%; padding: 1rem .875rem 3rem; }
 .mti-title h1 { font-size: 26px; }
 .mti-summary-grid { grid-template-columns: 1fr; gap: 14px; }
 .st-key-preset_cards [data-testid="stHorizontalBlock"] { flex-direction: column; }
 [class*="st-key-preset_card_"], .mti-preset-card { height: 164px; }
 [data-testid="stTabs"] [role="tablist"] { overflow-x: auto; scrollbar-width: none; }
 [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display: none; }
 button[data-baseweb="tab"] { min-height: 40px; white-space: nowrap; }
 .st-key-target_language_field, .st-key-termbase_attach, .st-key-termbase_picker,
 .st-key-termbase_attached { max-width: none; }
 .st-key-task_action_bar {
  position: sticky; left: auto; bottom: 0; width: 100%; margin-top: 26px;
 }
 .st-key-provider_status { position: static; width: auto; }
}

@media (prefers-reduced-motion: reduce) {
 *, *::before, *::after {
 scroll-behavior: auto !important;
 transition-duration: .01ms !important;
 animation-duration: .01ms !important;
 animation-iteration-count: 1 !important;
 }
}
"""
st.markdown("<style>" + _CSS + "</style>", unsafe_allow_html=True)

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
            return "冲突"
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


def _page_title(title, sub):
    st.markdown(
        f'<div class="mti-title"><h1>{title}</h1><p>{sub}</p></div>',
 unsafe_allow_html=True)


def _step_title(number, title, sub):
    st.markdown(
        f'<div class="mti-section-title">{title}</div>'
        f'<div class="mti-section-sub">{sub}</div>', unsafe_allow_html=True)


def _go_to_step(step):
    st.session_state.task_step = step


def _request_step(step):
    if step > 1 and not st.session_state.get("task_files"):
        st.session_state.step_gate_message = "请先上传原文。"
        st.session_state.task_step = 1
        return
    st.session_state.pop("step_gate_message", None)
    st.session_state.task_step = step


def _reset_provider_connection():
    st.session_state.provider_configured = False
    st.session_state.provider_connection_status = "unverified"
    st.session_state.pop("provider_test_feedback", None)


_PRESET_CONFIGS = {
    "快速": {
        "auto_term": False, "use_tm": True,
        "enable_review": False, "enable_annotate": False, "enable_report": False,
    },
    "标准": {
        "auto_term": True, "use_tm": True,
        "enable_review": False, "enable_annotate": False, "enable_report": False,
    },
    "学术增强": {
        "auto_term": True, "use_tm": True,
        "enable_review": True, "enable_annotate": True, "enable_report": True,
    },
}


def _apply_preset(label):
    for key in ("strategy_auto_term", "strategy_use_tm", "strategy_review",
                "strategy_annotate", "strategy_report"):
        st.session_state.pop(key, None)
    st.session_state.translation_preset = label
    st.session_state.strategy_config = dict(_PRESET_CONFIGS[label])


def _strategy_is_adjusted(label, config):
    return any(config.get(key) != value
               for key, value in _PRESET_CONFIGS[label].items())


def _toggle_advanced_strategy():
    st.session_state.strategy_advanced_open = not st.session_state.get(
        "strategy_advanced_open", False)


def _set_strategy_option(option, widget_key):
    config = dict(st.session_state.strategy_config)
    config[option] = bool(st.session_state[widget_key])
    st.session_state.strategy_config = config


def _render_task_actions(*, back_step=None, next_step=None, next_label="下一步",
                         next_disabled=False, run=False):
    with st.container(key="task_action_bar"):
        status_col, back_col, next_col = st.columns([2.6, .8, .8])
        has_inputs = bool(st.session_state.get("task_files"))
        save_text = "已保存" if has_inputs else "更改会自动保存"
        save_class = "mti-autosave is-saved" if has_inputs else "mti-autosave"
        status_col.markdown(f'<span class="{save_class}">{save_text}</span>',
                            unsafe_allow_html=True)
        if back_step is not None:
            back_col.button("上一步", width="stretch", on_click=_go_to_step,
                            args=(back_step,), key=f"back_to_{back_step}")
        if run:
            return next_col.button(next_label, type="primary", width="stretch",
                                   disabled=next_disabled, key="run_task")
        next_col.button(next_label, type="primary", icon=":material/arrow_forward:",
                        width="stretch", on_click=_request_step, args=(next_step,),
                        disabled=next_disabled, key=f"next_to_{next_step}")
    return False


def _remove_task_termbase():
    for key in ("task_glossary", "task_glossary_name", "task_glossary_count"):
        st.session_state.pop(key, None)
    st.session_state.show_termbase_picker = False


def _remove_source_documents():
    st.session_state.pop("task_files", None)
    st.session_state.pop("source_parse_state", None)
    st.session_state.pop("step_gate_message", None)


def _source_file_html(task_files):
    total_size = sum(len(item.get("bytes") or b"") for item in task_files)
    count = len(task_files)
    first_name = escape(task_files[0].get("name") or "未命名文档")
    name = first_name if count == 1 else f"{first_name} 等 {count} 个文件"
    parse_state = st.session_state.get("source_parse_state", "uploaded")
    page_total = sum(int(item.get("pages") or 0) for item in task_files)
    parsed_detail = f"{_format_size(total_size)} · " \
        f'{f"{page_total:,} 页 · " if page_total else ""}解析完成'
    meta = {
        "uploaded": (f"{_format_size(total_size)} · 已上传 · 等待解析", "已上传"),
        "parsing": (f"{_format_size(total_size)} · 正在解析", "解析中"),
        "parsed": (parsed_detail, "解析完成"),
        "error": (f"{_format_size(total_size)} · 解析失败", "解析失败"),
    }
    detail, status = meta.get(parse_state, meta["uploaded"])
    return (
        '<div class="mti-source-file">'
        '<span class="material-symbols-rounded" aria-hidden="true">description</span>'
        f'<div class="mti-source-file-copy"><strong>{name}</strong>'
        f'<span>{detail}</span></div>'
        f'<span class="mti-source-file-status is-{parse_state}">{status}</span></div>'
    )


def _preset_card_html(label):
    cards = {
        "快速": ("快速获得可读初稿", "翻译", "最快 · 成本最低"),
        "标准": ("适合大多数翻译任务", "翻译 → 质量检查", "平衡质量与成本"),
        "学术增强": ("适合 MTI 实践报告", "翻译 → 独立审校 → 证据分析",
                 "质量最高 · 耗时较长"),
    }
    purpose, workflow, tradeoff = cards[label]
    badge = '<span class="mti-preset-badge">推荐</span>' if label == "标准" else ""
    icon = "radio_button_checked" if label == st.session_state.get(
        "translation_preset", "标准") else "radio_button_unchecked"
    return (
        '<div class="mti-preset-card">'
        '<div class="mti-preset-head">'
        f'<span class="material-symbols-rounded" aria-hidden="true">{icon}</span>'
        f'<strong>{label}</strong>{badge}</div>'
        f'<p class="mti-preset-purpose">{purpose}</p>'
        f'<p class="mti-preset-flow">{workflow}</p>'
        f'<p class="mti-preset-tradeoff">{tradeoff}</p></div>'
    )


def _format_size(size):
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


def _summary_html(filename, target_lang, preset_label, glossary_name):
    workflow = {
        "快速": "翻译",
        "标准": "翻译 → 质量检查",
        "学术增强": "翻译 → 审校 → 证据分析 → 实践报告",
    }[preset_label]
    return (
        '<div class="mti-summary"><div class="mti-summary-grid">'
        f'<div class="mti-summary-item"><span>原文</span><strong>{filename}</strong></div>'
        f'<div class="mti-summary-item"><span>目标语言</span><strong>{target_lang}</strong></div>'
        f'<div class="mti-summary-item"><span>模式</span><strong>{preset_label}</strong></div>'
        f'<div class="mti-summary-item"><span>术语库</span><strong>{glossary_name}</strong></div>'
        '<div class="mti-summary-item" style="grid-column:1/-1"><span>工作流</span>'
        f'<strong>{workflow}</strong></div></div></div>')


def _render_profile_editor(job_id, state, box=None):
    box = box or st
    profile = state.get("document_profile") or {}
    with box.expander("文档画像（AI 生成，可修改后保存）", expanded=False):
        c1, c2, c3 = box.columns(3)
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
        style_constraints = box.text_area(
            "风格约束 style_constraints",
            value=profile.get("style_constraints") or "", key=f"pf_sc_{job_id}")
        if box.button("保存文档画像", key=f"pf_save_{job_id}"):
            core.save_document_profile(job_id, {
                "domain": domain, "subdomain": subdomain, "genre": genre,
                "audience": audience, "register": register,
                "style_constraints": style_constraints, "confidence": confidence,
                "sections": profile.get("sections") or [],
            })
            st.rerun()
        secs = profile.get("sections") or []
        if secs:
            box.caption("分节：" + "；".join(
                f"{x.get('section_id')}（段落 {x.get('start_segment')}-{x.get('end_segment')}"
                f"，{x.get('topic') or x.get('domain') or '?'}）" for x in secs))
        elif not state.get("profile_done"):
            box.caption("画像未生成（AI 失败或已跳过），可在此人工填写后保存。")

def _asset_prefix(state):
    """draft/final 资产文件名前缀：非 final 一律明确标注 draft。"""
    return "final_" if state.get("delivery_status") == "final" else "draft_"


# ================= 可视化辅助（证据链流程 / 术语状态） =================
def _chain_flow(stages):
    """横向流程卡片。"""
    boxes = []
    for i, (label, value, sub, color) in enumerate(stages):
        boxes.append(
            f'<div style="flex:1 1 130px;min-width:110px;padding:8px 12px;'
            f'border:1px solid {color}44;border-left:4px solid {color};'
            f'border-radius:8px;text-align:center;background:{color}10;">'
            f'<div style="font-size:12px;color:{color};font-weight:600;">{label}</div>'
            f'<div style="font-size:20px;font-weight:700;margin-top:1px;">{value}</div>'
            + (f'<div style="font-size:11px;opacity:.75;">{sub}</div>' if sub else "")
            + "</div>")
        if i < len(stages) - 1:
            boxes.append('<div style="align-self:center;color:#94a3b8;padding:0 2px;">→</div>')
    return ('<div style="display:flex;align-items:stretch;gap:2px;flex-wrap:wrap;'
            'margin:2px 0 8px;">' + "".join(boxes) + "</div>")


def _glossary_status_chips(entries):
    counts = {}
    for entry in entries:
        status = str(entry.get("status") or "provisional")
        counts[status] = counts.get(status, 0) + 1
    conflicts = sum(1 for entry in entries if _conflict(entry, entries))
    meta = [("候选", "candidate", "#64748b"), ("建议", "provisional", "#d97706"),
            ("已锁定", "locked", "#16a34a"), ("已拒绝", "rejected", "#dc2626")]
    chips = []
    for label, status, color in meta:
        chips.append(f'<span style="display:inline-block;padding:2px 12px;margin:0 6px 4px 0;'
                     f'border-radius:999px;border:1px solid {color};color:{color};'
                     f'font-size:13px;font-weight:600;">{label} {counts.get(status, 0)}</span>')
    conflict_label = f"冲突 {conflicts}" if conflicts else "无冲突"
    chips.append(f'<span style="display:inline-block;padding:2px 12px;border-radius:999px;'
                 f'border:1px solid #94a3b8;color:#64748b;font-size:13px;">{conflict_label}</span>')
    return '<div>' + "".join(chips) + "</div>"


def _merge_edited_entries(entries, edited_rows):
    """把编辑器可见行的修改合并回完整术语表。"""
    edited_by_id = {}
    new_rows = []
    for entry in edited_rows:
        entry_id = entry.get("id")
        if entry_id:
            edited_by_id[str(entry_id)] = entry
        else:
            new_rows.append(entry)
    merged = [edited_by_id.get(str(entry.get("id")), entry) for entry in entries]
    merged.extend(new_rows)
    return merged

# ================= Product shell / state =================
providers = sorted(core.PROVIDERS, key=str.casefold)
default_provider = "DeepSeek" if "DeepSeek" in providers else providers[0]
ai_provider = st.session_state.get("provider_choice", default_provider)
if ai_provider not in core.PROVIDERS:
    ai_provider = default_provider
provider_cfg = core.PROVIDERS[ai_provider]
model_opts = sorted(provider_cfg.get("models") or [], key=str.casefold)
default_model = "deepseek-v4-flash" if "deepseek-v4-flash" in model_opts \
    else (model_opts[0] if model_opts else "")
ai_model = st.session_state.get(f"model_choice_{ai_provider}", default_model)
api_key = st.session_state.get(f"api_key_{ai_provider}", "")
api_base = st.session_state.get("custom_base_url", "") \
    if provider_cfg.get("custom_base_url") else None
saved_jobs = core.list_jobs()
app_view = st.session_state.get("app_view", "new")
workspace_mode = st.session_state.get("workspace_mode", False)

with st.sidebar:
    st.markdown('<div class="mti-brand"><strong>MTI Tool</strong>'
                '<span>Translation Practice Workspace</span></div>',
                unsafe_allow_html=True)
    with st.container(key="new_task_action"):
        if st.button("新建任务", icon=":material/add:", width="stretch"):
            st.session_state.update(app_view="new", workspace_mode=False, task_step=1)
            st.rerun()
    if workspace_mode or st.session_state.get("active_job_id"):
        if st.button("当前任务", width="stretch", type="primary" if app_view == "workspace" else "secondary"):
            st.session_state.app_view = "workspace"
            st.rerun()
    if app_view == "new" and not workspace_mode:
        st.markdown('<div class="mti-nav-divider"></div>'
                    '<div class="mti-nav-label">当前任务</div>', unsafe_allow_html=True)
        with st.container(key="task_steps"):
            current_step = st.session_state.task_step
            for number, label in ((1, "文档"), (2, "翻译策略"), (3, "输出"), (4, "确认运行")):
                status = "done" if number < current_step else "current" if number == current_step else "pending"
                icon = ":material/check_circle:" if status == "done" \
                    else ":material/radio_button_checked:" if status == "current" \
                    else ":material/radio_button_unchecked:"
                if st.button(f"{number:02d}  {label}", icon=icon,
                             key=f"task_step_{status}_{number}", width="stretch",
                             type="primary" if status == "current" else "secondary"):
                    _request_step(number)
                    st.rerun()
    st.markdown('<div class="mti-nav-label">资料库</div>', unsafe_allow_html=True)
    with st.container(key="library_nav"):
        if st.button("历史任务", icon=":material/history:", width="stretch",
                     type="primary" if app_view == "history" else "secondary"):
            st.session_state.app_view = "history"
            st.rerun()
        if st.button("术语库与记忆", icon=":material/menu_book:", width="stretch",
                     type="primary" if app_view == "library" else "secondary"):
            st.session_state.app_view = "library"
            st.rerun()
        if st.button("设置", icon=":material/settings:", width="stretch",
                     type="primary" if app_view == "settings" else "secondary"):
            st.session_state.app_view = "settings"
            st.rerun()
    with st.container(key="provider_status"):
        provider_col, manage_col = st.columns([3, 1])
        connection_status = st.session_state.get("provider_connection_status", "unverified")
        provider_col.markdown(f'<div class="mti-provider is-{connection_status}">'
                              f'<strong>{ai_provider}</strong>'
                              f'<span>{ai_model or "未配置模型"}</span></div>',
                              unsafe_allow_html=True)
        if manage_col.button("管理", key="manage_provider"):
            st.session_state.app_view = "settings"
            st.rerun()

# Pipeline defaults; preset is a template and strategy_config is the effective configuration.
preset_label = st.session_state.get("translation_preset", "标准")
if preset_label not in _PRESET_CONFIGS:
    preset_label = "标准"
if "strategy_config" not in st.session_state:
    st.session_state.strategy_config = dict(_PRESET_CONFIGS[preset_label])
strategy_config = st.session_state.strategy_config
auto_term = strategy_config["auto_term"]
use_tm = strategy_config["use_tm"]
enable_review = strategy_config["enable_review"]
enable_annotate = strategy_config["enable_annotate"]
enable_report = strategy_config["enable_report"]
mode = "quality" if preset_label == "学术增强" or enable_report else "quick"
quality = mode == "quality"
target_lang = st.session_state.get("target_lang", "简体中文")
user_glossary = st.session_state.get("task_glossary", [])
uploaded_files = []
run_clicked = False
resume_choice = None
job_choices = [f"{j['state'].get('filename', '?')} {core.progress_label(j['state'])}"
               for j in saved_jobs]
style_rules = st.session_state.get(
    "style_rules", "保持学术书面语；专有名词、作者姓名、机构名、引用标注、URL 等保留原文；标点遵循目标语言规范。")
annotation_colors = st.session_state.get("annotation_colors", {
    "rare": "C00000", "domain": "BF8F00", "hard": "008080"})
theory_choice = st.session_state.get("translation_theory_choice", "自动推荐")
if theory_choice == "自定义":
    translation_theory = st.session_state.get("custom_translation_theory", "").strip() \
        or "自定义理论框架"
elif theory_choice == "自动推荐":
    translation_theory = "基于文本类型与可用文献证据自动选择理论框架"
else:
    translation_theory = theory_choice
literature_sources = st.session_state.get("literature_sources")
research_settings = st.session_state.get("research_settings", {
    "target_words": 4200, "submission_year": 2026, "body_language": "zh-CN",
    "case_selection_policy": "mixed", "case_limit": 5,
    "analysis_dimensions": ["文本特征", "术语管理", "翻译策略", "译后编辑与质量控制"],
})

# ================= Main views =================
setup_placeholder = st.empty()
with setup_placeholder.container():
    if app_view == "settings":
        _page_title("AI 引擎", "配置一次，所有新任务自动使用当前连接")
        pc1, pc2 = st.columns(2)
        ai_provider = pc1.selectbox("服务商", providers,
                                    index=providers.index(ai_provider), key="provider_choice",
                                    on_change=_reset_provider_connection)
        provider_cfg = core.PROVIDERS[ai_provider]
        model_opts = sorted(provider_cfg.get("models") or [], key=str.casefold)
        if model_opts:
            default_model = "deepseek-v4-flash" if "deepseek-v4-flash" in model_opts else model_opts[0]
            ai_model = pc2.selectbox("模型", model_opts,
                                     index=model_opts.index(st.session_state.get(
                                         f"model_choice_{ai_provider}", default_model)),
                                     key=f"model_choice_{ai_provider}",
                                     on_change=_reset_provider_connection)
        else:
            ai_model = pc2.text_input("模型", key=f"model_choice_{ai_provider}",
                                     placeholder=provider_cfg.get("model_hint") or "model-name",
                                     on_change=_reset_provider_connection)
        api_key = st.text_input("API 密钥", type="password", key=f"api_key_{ai_provider}",
                                on_change=_reset_provider_connection)
        if provider_cfg.get("custom_base_url"):
            api_base = st.text_input("API 地址", key="custom_base_url",
                                     placeholder="https://your-relay.example.com/v1",
                                     on_change=_reset_provider_connection)
        else:
            api_base = None
        st.caption(f"接口地址：{provider_cfg.get('base_url') or '由服务商管理'}")
        if st.button("测试连接", type="primary", disabled=not (api_key and ai_model)):
            with st.spinner("正在验证连接…"):
                ok, msg = core.test_provider(ai_provider, api_key, ai_model, base_url=api_base)
            st.session_state.provider_configured = ok
            st.session_state.provider_connection_status = "connected" if ok else "error"
            st.session_state.provider_test_feedback = (ok, msg)
            st.rerun()
        if feedback := st.session_state.get("provider_test_feedback"):
            ok, msg = feedback
            (st.success if ok else st.error)(msg)

    elif app_view == "new" and not workspace_mode:
        _page_title("新建翻译任务", "上传文档并配置翻译工作流")
        step = st.session_state.task_step

        if step == 1:
            _step_title(1, "文档", "配置本次翻译任务的输入材料")
            if gate_message := st.session_state.pop("step_gate_message", None):
                st.warning(gate_message, icon=":material/info:")
            task_files = st.session_state.get("task_files") or []
            if task_files:
                first_job = core.load_job_state(core.file_job_id(task_files[0]["bytes"]))
                if first_job and first_job.get("p1_done"):
                    st.session_state.source_parse_state = "parsed"
                    if first_job.get("source_page_count"):
                        task_files[0]["pages"] = first_job["source_page_count"]
                with st.container(key="source_file_summary"):
                    st.markdown('<div class="mti-source-label">原文</div>',
                                unsafe_allow_html=True)
                    with st.container(key="source_file_card"):
                        st.markdown(_source_file_html(task_files), unsafe_allow_html=True)
                        st.button("移除原文", icon=":material/delete_outline:",
                                  key="remove_source", help="移除原文",
                                  on_click=_remove_source_documents)
            else:
                with st.container(key="source_documents"):
                    st.markdown('<div class="mti-source-label">原文</div>'
                                '<div class="mti-upload-copy">'
                                '<span class="material-symbols-rounded" aria-hidden="true">upload_file</span>'
                                '<span>拖入文件或点击选择</span>'
                                '<small>支持 PDF、DOCX · 单文件最大 200 MB</small></div>',
                                unsafe_allow_html=True)
                    uploaded_files = st.file_uploader("原文", type=["pdf", "docx"],
                                                      accept_multiple_files=True,
                                                      label_visibility="collapsed",
                                                      help="支持 PDF 和 DOCX，可一次添加多个文件")
                if uploaded_files:
                    st.session_state.task_files = [
                        {"name": f.name, "bytes": f.getvalue()} for f in uploaded_files
                    ]
                    st.session_state.source_parse_state = "uploaded"
                    st.rerun()
            with st.container(key="target_language_field"):
                target_lang = st.selectbox(
                    "目标语言", ["简体中文", "繁体中文", "English", "日本語", "한국어",
                    "Deutsch", "Français", "Español", "Русский", "Português",
                                 "Italiano", "العربية"], key="target_lang")
            term_label = st.session_state.get("task_glossary_name", "未添加")
            st.markdown('<div class="mti-field-head"><strong>术语库</strong>'
                        '<span>可选 · 用于保持术语与专名一致</span></div>',
                        unsafe_allow_html=True)
            if term_label == "未添加":
                with st.container(key="termbase_attach"):
                    if st.button("添加术语库", icon=":material/attach_file:",
                                 key="add_termbase"):
                        st.session_state.show_termbase_picker = True
                        st.rerun()
            else:
                with st.container(key="termbase_attached"):
                    attached_col, remove_col = st.columns([4, 1])
                    count = st.session_state.get("task_glossary_count")
                    count_text = f"{count:,} 条术语" if count is not None else "已添加"
                    attached_col.markdown(
                        f'<div class="mti-attachment"><div><strong>{term_label}</strong>'
                        f'<span>{count_text}</span></div></div>', unsafe_allow_html=True)
                    remove_col.button("移除", key="remove_termbase",
                                      on_click=_remove_task_termbase, width="stretch")
            if st.session_state.get("show_termbase_picker") and term_label == "未添加":
                with st.container(key="termbase_picker"):
                    termbase_file = st.file_uploader(
                        "选择术语库文件", type=["xlsx", "csv", "tbx", "tmx"],
                        help="支持 Trados / memoQ 常用的 TBX、TMX，以及 Excel、CSV")
                if termbase_file:
                    try:
                        if termbase_file.name.lower().endswith(".tmx"):
                            result = core.import_tmx(termbase_file)
                            st.session_state.task_glossary = []
                            st.session_state.task_glossary_count = result["added"]
                            st.success(f"已并入翻译记忆 {result['added']} 条")
                        else:
                            parser = core.parse_termbase if termbase_file.name.lower().endswith(".xlsx") \
                                else core.parse_termbase_csv if termbase_file.name.lower().endswith(".csv") \
                                else core.parse_termbase_tbx
                            st.session_state.task_glossary = parser(termbase_file)
                            st.session_state.task_glossary_count = len(st.session_state.task_glossary)
                            st.success(f"已添加 {len(st.session_state.task_glossary)} 条参考术语")
                            st.session_state.task_glossary_name = termbase_file.name
                        st.session_state.show_termbase_picker = False
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))
            _render_task_actions(next_step=2,
                                 next_disabled=not st.session_state.get("task_files"))

        elif step == 2:
            _step_title(2, "翻译策略", "选择适合本次任务的工作流；需要时可调整高级设置")
            with st.container(key="preset_cards"):
                preset_columns = st.columns(3)
                for column, label in zip(preset_columns, _PRESET_CONFIGS):
                    state = "selected" if label == preset_label else "idle"
                    with column.container(key=f"preset_card_{label}_{state}"):
                        st.markdown(_preset_card_html(label), unsafe_allow_html=True)
                        if st.button(f"选择{label}预设", key=f"choose_preset_{label}"):
                            _apply_preset(label)
                            st.toast(f"已恢复“{label}”预设")
                            st.rerun()
            strategy_config = st.session_state.strategy_config
            adjusted = _strategy_is_adjusted(preset_label, strategy_config)
            with st.container(key="strategy_advanced"):
                advanced_open = st.session_state.get("strategy_advanced_open", False)
                state_text = f'<strong>{preset_label} · 已调整</strong>' if adjusted \
                    else f'当前使用“{preset_label}”的默认配置'
                st.button("高级设置", icon=":material/expand_less:" if advanced_open
                          else ":material/chevron_right:", key="toggle_strategy_advanced",
                          on_click=_toggle_advanced_strategy, width="stretch")
                st.markdown(f'<div class="mti-strategy-state">{state_text}</div>',
                            unsafe_allow_html=True)
                if advanced_open:
                    with st.container(key="advanced_body"):
                        st.markdown('<div class="mti-advanced-group">翻译辅助</div>',
                                    unsafe_allow_html=True)
                        st.toggle("术语抽取", value=strategy_config["auto_term"],
                                  key="strategy_auto_term", on_change=_set_strategy_option,
                                  args=("auto_term", "strategy_auto_term"))
                        st.toggle("使用翻译记忆", value=strategy_config["use_tm"],
                                  key="strategy_use_tm", on_change=_set_strategy_option,
                                  args=("use_tm", "strategy_use_tm"),
                                  help="精确复用已通过审校的历史译文")
                        st.markdown('<div class="mti-advanced-group">质量控制</div>',
                                    unsafe_allow_html=True)
                        st.toggle("独立审校", value=strategy_config["enable_review"],
                                  key="strategy_review", on_change=_set_strategy_option,
                                  args=("enable_review", "strategy_review"))
                        st.toggle("标记值得分析的翻译案例",
                                  value=strategy_config["enable_annotate"],
                                  key="strategy_annotate", on_change=_set_strategy_option,
                                  args=("enable_annotate", "strategy_annotate"))
                        st.markdown('<div class="mti-advanced-group">学术工作流</div>',
                                    unsafe_allow_html=True)
                        st.toggle("生成实践报告", value=strategy_config["enable_report"],
                                  key="strategy_report", on_change=_set_strategy_option,
                                  args=("enable_report", "strategy_report"))
                        if strategy_config["enable_report"]:
                            st.markdown('<p class="mti-report-helper">仅在生成实践报告时使用</p>',
                                        unsafe_allow_html=True)
                            with st.container(key="analysis_theory"):
                                theory_choice = st.selectbox("案例分析理论", [
                                    "自动推荐", "目的论 (Skopos Theory)",
                                    "交际翻译与语义翻译 (Newmark)", "功能对等理论 (Nida)",
                                    "文本类型理论 (Reiss)", "生态翻译学 (Hu Gengshen)",
                                    "自定义"], key="translation_theory_choice")
                                if theory_choice == "自定义":
                                    custom_theory = st.text_input(
                                        "自定义理论框架", key="custom_translation_theory",
                                        placeholder="输入理论名称或分析框架")
                                    translation_theory = custom_theory.strip() \
                                        or "自定义理论框架"
                                elif theory_choice == "自动推荐":
                                    translation_theory = \
                                        "基于文本类型与可用文献证据自动选择理论框架"
                                else:
                                    translation_theory = theory_choice
            _render_task_actions(back_step=1, next_step=3)

        elif step == 3:
            _step_title(3, "输出", "选择译文风格；学术报告将在翻译与证据阶段完成后生成")
            _STYLE_TEMPLATES = {
                "学术书面语": "保持学术书面语；专有名词、作者姓名、机构名、引用标注、URL 等保留原文；标点遵循目标语言规范。",
                "文学叙事": "保留原文叙事语气、人物口吻与意象；对话不要书面化；人名地名采用通行译法。",
                "技术文档": "术语与术语表严格一致；句式简洁；数字、单位、代码、命令和路径原样保留。",
                "自定义": "",
            }
            style_template = st.selectbox("译文风格", list(_STYLE_TEMPLATES), key="style_template")
            if style_template == "自定义":
                style_rules = st.text_area("风格与保留规则", key="style_rules",
                                           placeholder="说明语气、强制保留内容和标点规范")
            else:
                style_rules = st.text_area("风格与保留规则", value=_STYLE_TEMPLATES[style_template],
                                           key=f"style_rules_{style_template}")
                st.session_state.style_rules = style_rules
            if enable_report:
                with st.expander("报告证据（可选）", expanded=False):
                    literature_registry_file = st.file_uploader(
                        "文献证据注册表（可选）", type=["json"], key="literature_registry")
                    if literature_registry_file:
                        loaded_literature = json.load(literature_registry_file)
                        if isinstance(loaded_literature, dict):
                            loaded_literature = loaded_literature.get("sources") or []
                        st.session_state.literature_sources = loaded_literature
            _render_task_actions(back_step=2, next_step=4)

        else:
            _step_title(4, "确认运行", "检查本次任务配置，然后开始工作流")
            task_files = st.session_state.get("task_files") or []
            filename_summary = task_files[0]["name"] if len(task_files) == 1 \
                else f"{len(task_files)} 个文档"
            glossary_name = st.session_state.get("task_glossary_name", "未添加")
            st.markdown(_summary_html(filename_summary, target_lang, preset_label,
                                      glossary_name), unsafe_allow_html=True)
            st.markdown('<div class="mti-engine-row"><strong>AI 引擎</strong>'
                        f'<span>{ai_provider} · {ai_model or "未配置"}</span></div>',
                        unsafe_allow_html=True)
            if not api_key:
                st.warning("开始前请前往“设置”配置 AI 服务商和 API 密钥。")
            run_clicked = _render_task_actions(
                back_step=3, next_label="开始任务", run=True,
                next_disabled=not (task_files and api_key and ai_model))

    elif app_view == "workspace" or workspace_mode:
        _page_title("任务工作区", "任务进度、质量状态与交付资产")
        active_state = core.load_job_state(st.session_state.get("active_job_id")) \
            if st.session_state.get("active_job_id") else None
        stage_label = core.progress_label(active_state) if active_state else "等待任务开始"
        done_profile = bool(active_state and active_state.get("p1_done"))
        done_translation = bool(active_state and active_state.get("p2_done"))
        done_report = bool(active_state and active_state.get("p3_done"))
        evidence_done = bool(done_report or (active_state and active_state.get("p2_done")
                                             and active_state.get("findings") is not None))
        pipeline_items = [
            ("done" if done_profile else "active", "文档解析"),
            ("done" if done_profile else "pending", "段落重建"),
            ("done" if active_state and active_state.get("auto_terms") else "pending", "术语抽取"),
            ("done" if done_translation else "pending", "批次翻译"),
            ("done" if done_translation and active_state.get("review_stats") else "pending", "独立审校"),
            ("done" if evidence_done else "pending", "Evidence"),
            ("done" if done_report else "active" if evidence_done and active_state \
                and active_state.get("report_enabled") else "pending", "实践报告"),
        ]
        pleft, pright = st.columns([1, 2.5])
        with pleft:
            rows = "".join(
                f'<div style="padding:6px 0;color:{"#111827" if state == "active" else "#16a34a" if state == "done" else "#9ca3af"}">'
                f'{"●" if state == "active" else "✓" if state == "done" else "○"}&nbsp;&nbsp;{label}</div>'
                for state, label in pipeline_items)
            st.markdown(f'<div class="mti-pipeline" style="padding:16px 18px">'
                        f'<div class="mti-section-sub" style="margin-bottom:8px">处理流程</div>{rows}</div>',
                        unsafe_allow_html=True)
        with pright:
            st.subheader(stage_label)
            if active_state:
                progress_steps = sum((done_profile, done_translation, done_report))
                st.progress(progress_steps / 3)
                st.caption(f"当前阶段 {active_state.get('stage') or 'PREPARE'}")
            else:
                st.caption("从“新建任务”开始，或在“历史任务”中继续已有任务。")
    elif app_view == "history":
        _page_title("历史任务", "继续任务或查看已经生成的交付资产")
    elif app_view == "library":
        _page_title("术语库与翻译记忆", "管理跨任务复用的术语与已审校译文")

core.set_llm_base_url(api_base if provider_cfg.get("custom_base_url") else None)

if app_view == "settings":
    st.stop()
if app_view == "library":
    with st.container(border=True):
        _tm = core.load_tm()
        st.metric("已审校记忆", len(_tm))
        st.caption("翻译时精确命中会自动复用；通过独立审校的段落会自动入库。")
        if _tm:
            for _src in list(_tm)[-8:]:
                st.text(f"{(_src or '')[:54]} → {(_tm[_src].get('target') or '')[:54]}")
            _tm_confirm = st.checkbox("确认清空全部翻译记忆", key="library_tm_clear_confirm")
            if st.button("清空翻译记忆", disabled=not _tm_confirm, key="library_tm_clear"):
                core.save_tm({})
                st.rerun()
    st.stop()
if app_view == "history":
    if not saved_jobs:
        st.info("暂无历史任务。")
    else:
        for job in saved_jobs:
            hc1, hc2 = st.columns([4, 1])
            hc1.markdown(f"**{job['state'].get('filename', '?')}** \n"
                         f"{core.progress_label(job['state'])}")
            if hc2.button("打开", key=f"open_history_{job['job_id']}", width="stretch"):
                st.session_state.update(active_job_id=job["job_id"], app_view="workspace",
                                        workspace_mode=True)
                st.rerun()
    st.stop()
if app_view == "new" and not workspace_mode and not run_clicked:
    st.stop()

# ================= 核心处理流（断点续传状态机，实时落盘）=================
pending_job = st.session_state.pop("pending_continue_job", None)

tasks = []
seen = set()
if run_clicked:
    task_inputs = st.session_state.get("task_files") or []
    has_resume = bool(saved_jobs and resume_choice and resume_choice != "— 不继续 —")
    if not task_inputs and not has_resume:
        st.error("请先上传待翻译文档，或在「上传与开始」卡片中选择要继续的本地任务。")
    else:
        st.session_state.update(workspace_mode=True, app_view="workspace")
        setup_placeholder.empty()
        _page_title("任务工作区", "任务正在运行，进度会自动保存")
        wp_left, wp_right = st.columns([1, 2.5])
        with wp_left:
            st.markdown('<div class="mti-pipeline" style="padding:16px 18px">'
                        '<div class="mti-section-sub" style="margin-bottom:8px">处理流程</div>'
                        '<div class="mti-flow" style="display:block;line-height:2.15">'
                        '<span>文档解析</span><br/><span>段落重建</span><br/>'
                        '<span>术语抽取</span><br/><span>批次翻译</span><br/>'
                        '<span>独立审校</span><br/><span>Evidence</span><br/>'
                        '<span>实践报告</span></div></div>', unsafe_allow_html=True)
        wp_status = wp_right.empty()
        wp_status.info("准备工作流…")
        for f in task_inputs:
            file_bytes = f["bytes"]
            job_id = core.file_job_id(file_bytes)
            if job_id in seen:
                continue
            seen.add(job_id)
            tasks.append({"job_id": job_id, "filename": f["name"],
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

        # Report dependencies (research settings, literature, writer version) are
        # checked inside the backend before its early return.  Only skip here
        # when academic writing is explicitly disabled.
        if state["p1_done"] and state["p2_done"] and not enable_report \
                and (not enable_annotate or state.get("annotations_done")):
            overall_bar.progress((task_idx + 1) / len(tasks))
            continue

        try:
            if task["file_bytes"] is not None:
                st.session_state.source_parse_state = "parsing"
            with st.status(f"正在处理：{filename}", expanded=True) as status:
                state = core.run_job_pipeline(
                    job_id, filename, file_bytes,
                    provider=ai_provider, api_key=api_key, model=ai_model,
                    target_lang=target_lang, auto_term=auto_term,
                    enable_report=enable_report, translation_theory=translation_theory,
                    user_glossary=user_glossary,
                    style_rules=style_rules, enable_review=enable_review,
                    enable_annotate=enable_annotate, use_tm=use_tm, mode=mode,
                    research_settings=research_settings,
                    literature_sources=literature_sources,
                    on_status=lambda label: (
                        status.update(label=label, state="running"),
                        wp_status.info(label) if run_clicked else None),
                    on_caption=lambda text: st.caption(text),
                )
                st.session_state.doc_states[job_id] = state
                st.session_state.active_job_id = job_id
                if state.get("p1_done"):
                    st.session_state.source_parse_state = "parsed"
                for warn in state.get("warnings", []):
                    st.warning(warn)
                if state["p1_done"] and state["p2_done"] \
                        and (not enable_report or state["p3_done"]):
                    academic_quality = (state.get("academic_state") or {}).get(
                        "quality_status") if enable_report else None
                    if academic_quality in ("fail", "failed"):
                        status.update(
                            label=f"{filename} 翻译完成，但学术报告验证失败（可单独重验/重生成）",
                            state="error")
                    elif academic_quality == "review_required":
                        status.update(
                            label=f"{filename} 翻译完成，学术报告需要人工复核",
                            state="complete")
                    elif academic_quality == "pass_with_warnings":
                        status.update(
                            label=f"{filename} 报告已生成并通过验证，但存在证据警告",
                            state="complete")
                    elif state.get("has_blocking"):
                        status.update(
                            label=f"{filename} 流程完成，但有 blocking 问题待确认（见资产面板审查报告）",
                            state="complete")
                    else:
                        status.update(
                            label=f"{filename} 流程完成（交付状态：draft，"
                                  f"可在资产面板确认最终交付）",
                            state="complete")
                else:
                    status.update(
                        label=f"{filename} 进度已保存（当前阶段：{state.get('stage', '?')}），"
                              f"可在下方继续操作",
                        state="complete")
        except Exception as e:
            if task["file_bytes"] is not None and not state.get("p1_done"):
                st.session_state.source_parse_state = "error"
            if "学术写作阶段失败" in str(e):
                st.error(f"{filename} 翻译已保存，但学术写作失败：{e}。"
                         "可在下方学术写作工作区重新生成，不需要重跑翻译。")
            else:
                st.error(f"{filename} 翻译流程中断: {e}。进度已保存到本地 outputs/ 目录，"
                         f"刷新页面后可在「上传与开始」卡片中选择本地任务继续！")
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
        box = st.container(border=True)
        box.subheader(f"术语准备与审核：{astate.get('filename', '?')}")
        _render_profile_editor(active, astate, box)

        entries = astate.get("glossary") or []
        frozen = astate.get("glossary_frozen")
        bypassed = astate.get("quality_bypass")
        if frozen:
            box.success(f"术语表已冻结：版本 v{frozen.get('version')} "
                        f"hash {str(frozen.get('glossary_hash', ''))[:12]}… "
                       f"冻结时间 {frozen.get('frozen_at', '')}")
        elif bypassed:
            box.info("已选择跳过人工冻结：术语以 provisional 建议注入翻译。")
        else:
            box.warning("术语尚未冻结：仍有候选术语待人工审核，「开始翻译」不可执行。"
                       "请完成审核后冻结，或选择跳过冻结。")

        box.markdown(_glossary_status_chips(entries), unsafe_allow_html=True)
        fc1, fc2, fc3 = box.columns([2, 1, 1])
        filter_status = fc1.selectbox(
            "状态筛选", ["全部", "locked", "provisional", "candidate", "rejected"],
            key=f"gfilter_status_{active}")
        only_conflicts = fc2.checkbox("只看冲突项", key=f"gfilter_conflict_{active}")
        filter_text = fc3.text_input("搜索源术语", key=f"gfilter_text_{active}")

        df = _glossary_dataframe(entries, astate.get("paras") or [])
        view_mask = pd.Series(True, index=df.index)
        if filter_status != "全部":
            view_mask &= df["status"].eq(filter_status)
        if only_conflicts:
            view_mask &= df["冲突"].eq("冲突")
        if filter_text.strip():
            view_mask &= df["source"].str.contains(filter_text.strip(), case=False, na=False)
        df_view = df[view_mask]
        if not view_mask.all():
            box.caption(f"已按条件筛选：显示 {len(df_view)} / {len(df)} 条术语。")

        edited = box.data_editor(
            df_view,
            key=f"glossary_editor_{active}",
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
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

        c1, c2, c3 = box.columns(3)
        if c1.button("保存草稿", key=f"gs_{active}", width="stretch"):
            core.save_glossary_draft(
                active, _merge_edited_entries(entries, _df_to_entries(edited)))
            st.rerun()
        if c2.button("锁定选中术语", disabled=not sel_ids, key=f"gl_{active}",
                          width="stretch"):
            core.set_glossary_entry_status(active, sel_ids, "locked")
            st.rerun()
        if c3.button("拒绝选中术语", disabled=not sel_ids, key=f"gr_{active}",
                          width="stretch"):
            core.set_glossary_entry_status(active, sel_ids, "rejected")
            st.rerun()

        c4, c5, c6 = box.columns(3)
        if c4.button("冻结术语表并继续翻译", key=f"gf_{active}",
                          width="stretch"):
            core.freeze_glossary(
                active, entries=_merge_edited_entries(entries, _df_to_entries(edited)),
                frozen_by="用户")
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if c5.button("跳过冻结并翻译", key=f"gb_{active}",
                          width="stretch"):
            core.save_glossary_draft(
                active, _merge_edited_entries(entries, _df_to_entries(edited)))
            core.bypass_freeze(active)
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if c6.button("开始翻译", disabled=not (frozen or bypassed),
                     key=f"gt_{active}", width="stretch"):
            st.session_state["pending_continue_job"] = active
            st.rerun()
        if frozen and not bypassed:
            if box.button("返回修改（解除冻结）", key=f"gu_{active}",
                          width="stretch"):
                core.unfreeze_glossary(active)
                st.rerun()
        if not frozen and not bypassed:
            box.caption("翻译未开始：请先「冻结术语表并继续翻译」，"
                       "或选择跳过冻结（快速模式）。")

# ================= 动态渲染过程资产面板（基于磁盘任务，刷新后仍可用）=================
tab_delivery, tab_academic = st.tabs(
    ["资产与交付", "实践报告"], key="main_tabs")

with tab_delivery:
    st.header("项目过程资产")
    with st.expander("翻译记忆（全局复用）", expanded=False):
        _tm = core.load_tm()
        st.caption(f"当前 {len(_tm)} 条已审校条目；精确命中时自动复用（跨任务全局）。")
        if _tm:
            with st.expander("预览最近条目", expanded=False):
                for _src in list(_tm)[-8:]:
                    st.caption(f"**{(_src or '')[:56]}** → {(_tm[_src].get('target') or '')[:56]}")
            _tm_confirm = st.checkbox("确认清空全部翻译记忆", key="tm_clear_confirm")
            if st.button("清空翻译记忆", disabled=not _tm_confirm,
                         key="tm_clear_go", width="stretch"):
                core.save_tm({})
                st.success("翻译记忆已清空")
                st.rerun()
        else:
            st.caption("暂无条目：翻译并通过独立审校的段落会自动入库。")
    if not saved_jobs_after:
        st.caption("暂无本地任务。上传文件并开始处理后，任务资产会显示在这里。")
    for job in saved_jobs_after:
        state = job["state"]
        filename = state.get("filename", "?")
        is_active = job["job_id"] == st.session_state.get("active_job_id")
        with st.expander(f"资产与交付: {filename}", expanded=is_active):
            dstatus = state.get("delivery_status") or "draft"
            if dstatus == "final":
                st.success("交付状态：最终交付（final）")
            elif dstatus == "review_required":
                st.warning(f"交付状态：{core.delivery_status_label(state)}"
                           "（存在 blocking，未最终交付）")
            else:
                st.caption(f"交付状态：{core.delivery_status_label(state)}"
                           "（当前为 draft 资产，尚未最终交付）")
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)

            with col_d1:
                if state.get("p1_done") and state.get("paras"):
                    st.download_button(
 "1. 洗净后原文",
                        core.paragraphs_to_word(state["paras"]),
                        file_name=f"{_asset_prefix(state)}阶段1_清洗原文_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
 key=f"d1_{job['job_id']}", width="stretch")
            with col_d2:
                if state.get("auto_terms"):
                    st.download_button(
 "1.5 提取术语库",
                        core.dict_to_excel(state["auto_terms"]),
                        file_name=f"{_asset_prefix(state)}自动抽词库_{filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
 key=f"dt_{job['job_id']}", width="stretch")
            with col_d3:
                if state.get("p2_done") and state.get("pairs"):
                    st.download_button(
 "2. 双语对照表",
                        core.pairs_to_word(state["pairs"],
                                           annotations=state.get("annotations"),
                                           colors=annotation_colors),
                        file_name=f"{_asset_prefix(state)}阶段2_双语对照_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
 key=f"d2_{job['job_id']}", width="stretch")
            with col_d4:
                if state.get("p3_md"):
                    st.download_button(
 "3. 翻译实践报告",
                        core.markdown_to_word(state["p3_md"], state.get("theory") or translation_theory),
                        file_name=f"{_asset_prefix(state)}阶段3_实践报告_{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
 key=f"d3_{job['job_id']}", width="stretch")

            if state.get("document_profile"):
                prof = state["document_profile"]
                st.caption(
                    f"画像：领域 {prof.get('domain') or '?'} · "
 f"类型 {prof.get('genre') or '?'} 语域 {prof.get('register') or '?'} "
                    f"置信度 {prof.get('confidence') or 0}")

            if state.get("p2_done"):
                stats = state.get("review_stats") or {}
                st.caption(
                    f"审校：{stats.get('reviewed_segments', 0)} 段通过 · "
                    f"blocking {stats.get('blocking', 0)} · actionable {stats.get('actionable', 0)} · "
                    f"informational {stats.get('informational', 0)} · "
                    f"记忆复用 {state.get('tm_used_count', 0)} 段")
                exported = _assets.export_all(
                    state, job["job_id"], target_lang, ai_provider, ai_model,
                    source_filename=filename)
                ea1, ea2, ea3, ea4 = st.columns(4)
                with ea1:
                    st.download_button("TBX 术语库", exported["terms.tbx"],
                                       file_name=f"{_asset_prefix(state)}terms_{filename}.tbx",
                                       mime="application/xml", key=f"tbx_{job['job_id']}", width="stretch")
                with ea2:
                    st.download_button("TMX 翻译记忆", exported["memory.tmx"],
                                       file_name=f"{_asset_prefix(state)}memory_{filename}.tmx",
                                       mime="application/xml", key=f"tmx_{job['job_id']}", width="stretch")
                with ea3:
                    st.download_button("JSONL 双语段落", exported["bilingual.jsonl"],
                                       file_name=f"{_asset_prefix(state)}bilingual_{filename}.jsonl",
                                       mime="application/x-jsonlines", key=f"jl_{job['job_id']}", width="stretch")
                with ea4:
                    st.download_button("交付清单 manifest", exported["delivery_manifest.json"],
                                       file_name=f"{_asset_prefix(state)}delivery_manifest_{filename}.json",
                                       mime="application/json", key=f"mf_{job['job_id']}", width="stretch")
                st.download_button(
                    "案例证据包 (.jsonl)",
                    _report_evidence.export_segment_evidence_jsonl(state, job["job_id"]).encode("utf-8"),
                    file_name=f"{_asset_prefix(state)}segment_evidence_{filename}.jsonl",
                    mime="application/x-jsonlines", key=f"ev_{job['job_id']}", width="stretch")

                unresolved = _delivery.unresolved_findings(state)
                if dstatus == "review_required" and unresolved:
                    chosen = []
                    for finding in unresolved:
                        fid = _delivery.finding_id(finding)
                        label = (f"`{fid}` 段 {finding.get('segment_index', -1) + 1} "
                                 f"[{finding.get('severity')}] {finding.get('reason')}")
                        if st.checkbox(label, key=f"fd_{job['job_id']}_{fid}"):
                            chosen.append(fid)
                    note = st.text_input("处理说明", key=f"fdnote_{job['job_id']}")
                    dc1, dc2, dc3 = st.columns(3)
                    if dc1.button("标记已人工修复", disabled=not chosen,
                                  key=f"fdfix_{job['job_id']}", width="stretch"):
                        core.mark_findings_resolved(job["job_id"], chosen, "human_fixed", note or "人工修复")
                        st.rerun()
                    if dc2.button("重新翻译选中段落", disabled=not chosen,
                                  key=f"fdrt_{job['job_id']}", width="stretch"):
                        idxs = sorted({finding.get("segment_index") for finding in unresolved
                                       if _delivery.finding_id(finding) in chosen
                                       and isinstance(finding.get("segment_index"), int)})
                        core.retranslate_segments(
                            job["job_id"], idxs, ai_provider, api_key, ai_model,
                            target_lang, style_rules=style_rules,
                            on_caption=lambda text: st.caption(text))
                        st.rerun()
                    if dc3.button("接受风险并进入 final", key=f"fdacc_{job['job_id']}", width="stretch"):
                        core.approve_delivery(job["job_id"], note or "接受风险", accept_blocking=True)
                        st.rerun()
                elif dstatus != "final":
                    note2 = st.text_input("交付说明（可选）", key=f"fdn_{job['job_id']}")
                    if st.button("确认交付 (final)", key=f"fdok_{job['job_id']}"):
                        core.approve_delivery(job["job_id"], note2 or "人工确认交付")
                        st.rerun()
                if state.get("human_actions"):
                    with st.expander("人工处理记录"):
                        for action in state["human_actions"][-20:]:
                            st.caption(f"{action.get('timestamp')} {action.get('action')} "
                                       f"{action.get('finding_id')} {action.get('note')}")
                if state.get("findings"):
                    st.download_button("审查报告 (.md)", core.findings_report_md(state),
                                       file_name=f"{_asset_prefix(state)}审查报告_{filename}.md",
                                       mime="text/markdown", key=f"rr_{job['job_id']}", width="stretch")

            if state.get("p3_md"):
                st.markdown(state["p3_md"])
                st.caption("报告为 AI 生成初稿：案例需对照双语表逐条人工核查后再使用。")

                with st.expander("术语治理审计（注入日志 / 冻结版本）", expanded=False):
                    versions = state.get("glossary_versions") or []
                    if versions:
                        st.caption(f"冻结版本 {len(versions)} 个（内容变化才产生新版本，旧版本不覆盖）")
                        st.dataframe(pd.DataFrame([{
                            "版本": v.get("version"),
                            "冻结时间": (v.get("frozen_at") or "")[:19],
                            "glossary_hash": str(v.get("glossary_hash") or "")[:16],
                            "条数": len(v.get("entries") or []),
                        } for v in versions]), hide_index=True, width="stretch")
                    else:
                        st.caption("暂无冻结版本（快速模式跳过冻结时不生成版本）。")
                    injections = state.get("glossary_injection_log") or []
                    if injections:
                        st.caption(
                            f"翻译批次注入日志 {len(injections)} 批"
                            "（每批实际注入的术语 entry ID 均有记录）")
                        st.dataframe(pd.DataFrame([{
                            "批次": x.get("batch"),
                            "起始段": x.get("offset"),
                            "注入条数": len(x.get("entry_ids") or []),
                            "术语版本": x.get("glossary_version") or "-",
                            "hash": str(x.get("glossary_hash") or "")[:16],
                        } for x in injections[-100:]]), hide_index=True,
                                   width="stretch")
                    else:
                        st.caption("暂无批次注入日志。")

                del_key = f"confirm_del_{job['job_id']}"
                if st.button("删除该任务及本地进度", key=f"del_{job['job_id']}",
                          width="stretch"):
                    st.session_state[del_key] = True
                if st.session_state.get(del_key):
                    st.warning("删除后该任务的全部本地进度（翻译、术语、报告、资产）不可恢复。")
                    dc1, dc2 = st.columns(2)
                    if dc1.button("确认删除", key=f"del_yes_{job['job_id']}",
                          width="stretch"):
                        core.delete_job(job["job_id"])
                        st.session_state.doc_states.pop(job["job_id"], None)
                        st.session_state.pop(del_key, None)
                        st.rerun()
                    if dc2.button("取消", key=f"del_no_{job['job_id']}",
                          width="stretch"):
                        st.session_state.pop(del_key, None)
                        st.rerun()

with tab_academic:
    st.header("学术写作工作区")
    if not saved_jobs_after:
        st.caption("暂无本地任务。上传文件并开始处理后，学术写作工作区会显示在这里。")
    for job in saved_jobs_after:
        state = job["state"]
        filename = state.get("filename", "?")
        is_active = job["job_id"] == st.session_state.get("active_job_id")
        with st.expander(f"学术写作: {filename}", expanded=is_active):
            if state.get("p2_done"):
                academic = state.get("academic_state") or {}
                quality = academic.get("quality_status") or academic.get("status") or "not_started"
                st.subheader("学术写作工作区")
                if quality == "pass":
                    st.success("学术状态：验证通过（仍需人工学术判断后提交）")
                elif quality == "pass_with_warnings":
                    st.warning("学术状态：通过，但存在证据缺口或低等级警告")
                elif quality in ("review_required", "fail", "failed"):
                    st.error(f"学术状态：{core.academic_status_label(state)}")
                else:
                    st.caption(f"学术状态：{core.academic_status_label(state)} · "
                               f"当前阶段 {academic.get('current_stage') or 'not_started'}")
                if academic.get("quality_dimensions"):
                    st.caption("质量维度：" + " · ".join(
                        f"{key}={value}" for key, value in academic[
                            "quality_dimensions"].items()))

                aevidence = core.load_academic_artifact(job["job_id"], "evidence")
                literature_sources_artifact = core.load_academic_artifact(
                    job["job_id"], "literature_sources")
                literature_evidence_artifact = core.load_academic_artifact(
                    job["job_id"], "literature_evidence")
                literature_claims_artifact = core.load_academic_artifact(
                    job["job_id"], "literature_claims")
                argument_artifact = core.load_academic_artifact(job["job_id"], "argument_plan")
                selected_cases = core.load_academic_artifact(job["job_id"], "selected_cases")
                outline_artifact = core.load_academic_artifact(job["job_id"], "outline")
                case_plans_artifact = core.load_academic_artifact(
                    job["job_id"], "case_analysis_plans")
                synthetic_artifact = core.load_academic_artifact(
                    job["job_id"], "synthetic_validation")
                validation_artifact = core.load_academic_artifact(job["job_id"], "validation")
                review_artifact = core.load_academic_artifact(job["job_id"], "review")
                literature_review_artifact = core.load_academic_artifact(
                    job["job_id"], "literature_support_review")
                quality_artifact = core.load_academic_artifact(
                    job["job_id"], "academic_quality")
                quality_repair_artifact = core.load_academic_artifact(
                    job["job_id"], "quality_repair_history")
                if aevidence:
                    astats = aevidence.get("project_evidence", {}).get("statistics", {})
                    coverage = aevidence.get("coverage_policy", {})
                    st.caption(
                        f"证据：扫描 {coverage.get('segments_scanned', 0)} 段（全语料） · "
                        f"候选案例 {len(aevidence.get('candidate_cases') or [])} · "
                        f"修复证据段 {astats.get('repaired_segments', 0)} · "
                        f"TM 复用 {astats.get('tm_reuse_count', 0)}")
                if selected_cases or outline_artifact:
                    st.caption(
                        f"真实修订案例 {(selected_cases or {}).get('authentic_revision_cases', 0)} · "
                        f"合成对比案例 {(selected_cases or {}).get('synthetic_contrast_cases', 0)} · "
                        f"提纲章节 {len((outline_artifact or {}).get('sections') or [])}")
                if synthetic_artifact:
                    synthetic_metrics = synthetic_artifact.get("metrics") or {}
                    if synthetic_artifact.get("pipeline_status") == "failed":
                        st.warning("合成对比案例生成失败；当前仅保留已验证的真实案例。")
                    st.caption(
                        f"合成案例：已生成模拟初译 "
 f"{synthetic_metrics.get('synthetic_baselines_generated', 0)} "
 f"不合理基线淘汰 {synthetic_metrics.get('baselines_rejected_as_implausible', 0)} "
                        f"学术合格 {synthetic_metrics.get('academically_eligible_synthetic_cases', 0)}")
                    with st.expander("查看 Synthetic Contrast Cases"):
                        for case in synthetic_artifact.get("items", []):
                            validation = case.get("validation") or {}
                            st.markdown(
 f"**{case.get('case_id')} Synthetic Contrast Case** — "
                                f"{'eligible' if validation.get('academic_case_eligible') else 'rejected'}")
                            st.caption(f"Source：{(case.get('source_text') or '')[:180]}")
                            st.caption(
                                f"Translation Difficulty：{(case.get('difficulty') or {}).get('reason') or '-'}")
                            st.caption(
                                f"Simulated Initial Translation："
                                f"{(case.get('synthetic_baseline') or {}).get('text') or '-'}")
                            st.caption(f"Error Diagnosis：{(case.get('error') or {}).get('diagnosis') or '-'}")
                            st.caption(
                                f"AI-Optimized Translation："
                                f"{(case.get('optimized_translation') or {}).get('text') or '-'}")
                            st.caption(
                                f"Validation：plausibility="
 f"{(case.get('baseline_plausibility') or {}).get('status', '-')} "
 f"repair={validation.get('repair_correctness', '-')} "
                                f"academic eligibility={validation.get('academic_case_eligible', False)}")
                if case_plans_artifact and case_plans_artifact.get("plans"):
                    plans = case_plans_artifact["plans"]
                    depth = (quality_artifact.get("diagnostics") or {}).get(
                        "case_analysis_depth") or {} if quality_artifact else {}
                    with st.expander("查看案例分析计划与质量"):
                        for plan in plans:
                            problem = plan.get("problem") or {}
                            effect = plan.get("translation_effect") or {}
                            mapping = plan.get("theory_mapping") or {}
                            depth_entry = depth.get(plan.get("case_id")) or {}
                            depth_line = " · ".join(
                                f"{k}={v.get('status', '?')}"
                                for k, v in list(depth_entry.items())[:5]) or "未评估"
                            st.markdown(
                                f"**{plan.get('case_id')} · "
                                f"{'Synthetic Contrast Case' if plan.get('case_type') == 'synthetic_contrast' else 'Authentic Revision Case'}** "
                                f"— {plan.get('evidence_level')} · "
                                f"深度：{depth_line}")
                            st.caption(
                                f"问题：{problem.get('statement') or '未计划'}"
                                f"{'（已落地）' if problem.get('grounded') else '（证据不足）'} · "
                                f"效果维度：{effect.get('dimension') or '-'} · "
                                f"理论：{mapping.get('concept') or plan.get('theory_connection_status')}")
                            human = plan.get("recommended_human_evidence") or []
                            if human:
                                st.caption("需要人工证据：" + "；".join(human[:3]))
                questions_artifact = core.load_academic_artifact(
                    job["job_id"], "human_evidence_questions")
                human_status = academic.get("human_evidence_status") or {}
                if human_status or (questions_artifact and questions_artifact.get("questions")):
                    st.subheader("人类证据收件箱")
                    if human_status:
                        st.caption(
                            f"待回答问题 {human_status.get('unanswered', 0)} · "
                            f"关键问题 {human_status.get('critical_questions', 0)} · "
                            f"已确认证据 {human_status.get('answered', 0)} · "
                            f"确认无法回忆 {human_status.get('unavailable_after_check', 0)} · "
                            f"矛盾 {human_status.get('conflicted', 0)}")
                    open_questions = [
                        q for q in (questions_artifact or {}).get("questions", [])
                        if q.get("status") == "open"]
                    if open_questions:
                        for q in open_questions:
                            case_id = q.get("case_id", "")
                            question = q.get("question", "")
                            context = q.get("context") or {}
                            with st.expander(
                                    f"{case_id} · {q.get('question_type', '')} · "
                                    f"{q.get('priority', '')}"):
                                st.caption(f"原文：{context.get('source', '')[:120]}")
                                if context.get("case_type") == "synthetic_contrast":
                                    st.caption(
                                        f"模拟初译：{context.get('synthetic_initial_translation', '')[:120]}")
                                    st.caption(
                                        f"优化译文：{context.get('optimized_translation', '')[:120]}")
                                else:
                                    st.caption(f"终译：{context.get('final_target', '')[:120]}")
                                st.markdown(f"**{question}**")
                                st.caption(
                                    "若不知道或没有相关记录，直接输入“不记得/没有相关记录”。")
                                answer = st.text_area(
                                    "你的回答", key=f"he_answer_{job['job_id']}_{q['question_id']}",
                                    height=70)
                                if st.button("提交证据",
                                             key=f"he_submit_{job['job_id']}_{q['question_id']}",
                                             disabled=not api_key):
                                    if not answer.strip():
                                        st.warning("请填写回答，或输入“不记得”。")
                                    else:
                                        try:
                                            entry = core.record_human_evidence(
                                                job["job_id"], q["question_id"], answer)
                                            st.success(
                                                f"已记录证据 {entry.get('human_evidence_id')} "
                                                f"（状态：{entry.get('status')}）。"
                                                "受影响章节将在下次重新生成时更新。")
                                        except Exception as exc:
                                            st.error(str(exc))
                if literature_sources_artifact:
                    lit_sources = literature_sources_artifact.get("sources") or []
                    lit_evidence_items = (literature_evidence_artifact or {}).get("items") or []
                    lit_claim_items = (literature_claims_artifact or {}).get("items") or []
                    grounded_count = sum(
                        x.get("evidence_grounded_status") in {
                            "grounded", "grounded_user_material"}
                        for x in lit_claim_items)
                    total_global = len((argument_artifact or {}).get("claims") or [])
                    total_sections = len((outline_artifact or {}).get("sections") or [])
                    st.markdown(_chain_flow([
                        ("文献来源", len(lit_sources), "已登记", "#2563eb"),
                        ("文献证据", len(lit_evidence_items), "逐字+位置+hash", "#0d9488"),
                        ("文献主张", len(lit_claim_items), f"已落地 {grounded_count}", "#7c3aed"),
                        ("全局论点", total_global, "", "#db2777"),
                        ("章节", total_sections, "", "#16a34a"),
                    ]), unsafe_allow_html=True)
                    if lit_sources:
                        with st.expander("按来源查看 来源→证据→主张→论点→章节 链路"):
                            source_options = {
                                f"{x.get('source_id')} · {x.get('title') or '未命名来源'}":
                                x.get("source_id") for x in lit_sources}
                            selected_source_id = st.selectbox(
                                "文献来源", source_options, key=f"lit_source_{job['job_id']}")
                            selected_source_id = source_options[selected_source_id]
                            selected_source = next(
                                x for x in lit_sources
                                if x.get("source_id") == selected_source_id)
                            st.json({k: v for k, v in selected_source.items()
                                     if k != "content_blocks"})
                            source_evidence = [x for x in lit_evidence_items
                                               if x.get("source_id") == selected_source_id]
                            source_claims = [x for x in lit_claim_items
                                             if x.get("source_id") == selected_source_id]
                            source_lc_ids = {x.get("literature_claim_id") for x in source_claims}
                            global_claims = [
                                x for x in (argument_artifact or {}).get("claims") or []
                                if source_lc_ids & set(x.get("literature_claims") or [])]
                            global_claim_ids = {x.get("claim_id") for x in global_claims}
                            source_sections = [
                                x for x in (outline_artifact or {}).get("sections") or []
                                if global_claim_ids & set(x.get("claims") or [])]
                            st.markdown(_chain_flow([
                                ("文献证据", len(source_evidence), "", "#0d9488"),
                                ("文献主张", len(source_claims), "", "#7c3aed"),
                                ("全局论点", len(global_claims), "", "#db2777"),
                                ("章节", len(source_sections), "", "#16a34a"),
                            ]), unsafe_allow_html=True)
                            if source_evidence:
                                st.dataframe(source_evidence, width="stretch")
                            if source_claims:
                                st.dataframe(source_claims, width="stretch")
                if validation_artifact:
                    summary = validation_artifact.get("summary") or {}
                    st.caption(
                        f"确定性验证：{validation_artifact.get('status')} · "
 f"错误 {summary.get('errors', 0)} 警告 {summary.get('warnings', 0)}")
                if review_artifact:
                    st.caption(
                        f"语义审稿：{review_artifact.get('status')} · "
                        f"问题 {len(review_artifact.get('issues') or [])}")
                if literature_review_artifact:
                    st.caption(
                        f"文献支持审校：{literature_review_artifact.get('status')} · "
                        f"问题 {len(literature_review_artifact.get('issues') or [])}")
                    if literature_review_artifact.get("issues"):
                        st.dataframe(literature_review_artifact["issues"],
                                   width="stretch")
                if quality_artifact:
                    q_dims = quality_artifact.get("dimensions") or {}
                    q_findings = quality_artifact.get("findings") or []
                    q_metrics = quality_artifact.get("metrics") or {}
                    aq_status = q_dims.get("literature_support") or "pass"
                    q_status_label = {
                        "pass": "通过", "pass_with_warnings": "通过（有警告）",
                        "review_required": "需复核", "fail": "失败",
                        "not_applicable": "不适用"}.get(aq_status, aq_status)
                    st.caption(
                        f"学术质量：发现 {len(q_findings)} 项 · 强案例 "
                        f"{q_metrics.get('strong_cases', 0)} · 弱案例 "
                        f"{q_metrics.get('weak_cases', 0)} · 泛化段率 "
                        f"{q_metrics.get('generic_paragraph_rate', 0)}")
                    if q_findings:
                        st.dataframe(q_findings, width="stretch")
                    if quality_repair_artifact and quality_repair_artifact.get("rounds"):
                        st.caption(
                            f"质量修复 {len(quality_repair_artifact['rounds'])} 轮 · "
                            f"案例替换 "
                            f"{sum(len(r.get('case_replacements') or []) for r in quality_repair_artifact['rounds'])}")

                def _queue_academic(scope, section_id=None):
                    if not api_key:
                        st.warning("请先在侧栏填写 API Key。")
                        return
                    core.invalidate_academic_report(job["job_id"], scope, section_id)
                    st.session_state["pending_continue_job"] = job["job_id"]
                    st.rerun()

                ac1, ac2, ac3, ac4, ac5, ac6 = st.columns(6)
                if ac1.button("重生成整篇", key=f"academic_all_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("all")
                if ac2.button("重做规划", key=f"academic_plan_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("planning")
                if ac3.button("重新验证", key=f"academic_val_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("validation")
                if ac4.button("重新审稿", key=f"academic_review_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("review")
                if ac5.button("文献审校", key=f"literature_review_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("literature_review")
                if ac6.button("质量重评", key=f"quality_review_{job['job_id']}",
                          width="stretch"):
                    _queue_academic("quality")
                if outline_artifact and outline_artifact.get("sections"):
                    section_options = {
                        f"{x['section_id']} {x['title']}": x["section_id"]
                        for x in outline_artifact["sections"]}
                    chosen_section = st.selectbox(
                        "定点重生成章节", list(section_options),
                        key=f"academic_section_{job['job_id']}")
                    if st.button("重生成选中章节", key=f"academic_section_go_{job['job_id']}"):
                        _queue_academic("section", section_options[chosen_section])
                warning_path = core.job_dir(job["job_id"]) / "academic-evidence-warnings.md"
                if warning_path.is_file():
                    st.download_button(
                        "下载学术证据警告",
                        warning_path.read_bytes(),
                        file_name=f"academic-evidence-warnings_{filename}.md",
                        mime="text/markdown", key=f"academic_warn_{job['job_id']}",
                                   width="stretch")
