"""Streamlit AppTest 启动冒烟测试：应用应能正常渲染，且空提交给出错误提示而非崩溃。"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core


def main():
    root = Path(__file__).resolve().parent.parent
    from streamlit.testing.v1 import AppTest

    tmp = Path(tempfile.mkdtemp(prefix="app-boot-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        app_source = (root / "app.py").read_text(encoding="utf-8")
        assert ':has([data-testid="stFileChip"]) .tp-upload-copy' in app_source \
            and 'animation: tp-upload-bar' in app_source \
            and '[data-testid="stFileChipName"]::before' in app_source, \
            "上传中的 Streamlit FileChip 应重绘为带状态的全宽文件卡"
        assert 'label, [data-testid="stWidgetLabel"]' in app_source \
            and '[data-testid="stTextInput"] input::placeholder' in app_source \
            and '[role="listbox"] [role="option"]' in app_source \
            and 'opacity: 1 !important' in app_source, \
            "表单标签、输入占位符和说明文字必须保持可读对比度"
        assert '[data-testid="stRadioOption"]' in app_source \
            and '[data-testid="stSliderThumbValue"]' in app_source \
            and 'var(--tp-primary) !important' in app_source, \
            "风格调整的单选项和滑块必须使用可读文字与品牌蓝"
        assert 'tp-history-copy' in app_source \
            and 'history_item_' in app_source, \
            "历史任务名称与进度必须使用明确的高对比度展示容器"
        # 预置一个本地任务，确保「资产与交付 / 学术写作」Tabs 一定渲染
        jid = "ab000000000000001"
        state = core.new_job_state("boot_fixture.pdf")
        state.update(p1_done=True, p2_done=True, paras=["hello"],
                     pairs=[{"source": "hello", "target": "你好"}],
                     stage="DONE",
                     delivery_status="draft")
        core.save_job_state(jid, state)
        pending = core.new_job_state("pending_fixture.docx")
        pending.update(p1_done=True, p2_done=False, quality_mode=True, glossary=[])
        core.save_job_state("ab000000000000002", pending)
        job_root = core.job_dir(jid)
        (job_root / "literature-sources.json").write_text(json.dumps({
            "sources": [{"source_id": "s1", "title": "测试来源"}]}, ensure_ascii=False),
            encoding="utf-8")
        (job_root / "literature-evidence.jsonl").write_text(
            json.dumps({"evidence_id": "e1", "source_id": "s1"}, ensure_ascii=False) + "\n",
            encoding="utf-8")
        (job_root / "literature-claims.jsonl").write_text(
            json.dumps({"literature_claim_id": "lc1", "source_id": "s1",
                        "evidence_grounded_status": "grounded"}, ensure_ascii=False) + "\n",
            encoding="utf-8")
        (job_root / "argument-plan.json").write_text(json.dumps({
            "claims": [{"claim_id": "g1", "literature_claims": ["lc1"]}]},
            ensure_ascii=False), encoding="utf-8")
        (job_root / "academic-outline.json").write_text(json.dumps({
            "sections": [{"section_id": "sec1", "title": "测试章节",
                          "claims": ["g1"]}]}, ensure_ascii=False),
            encoding="utf-8")

        at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
        at.run()
        assert not at.exception, f"应用启动异常：{at.exception}"
        assert at.session_state["app_view"] == "new" \
            and not at.session_state["workspace_mode"], \
            "打开应用时应进入新建任务初始页，未完成任务从历史任务进入"
        assert any("TransPraxis" in m.value and "译践" in m.value
                   for m in at.sidebar.markdown), \
            "侧栏应显示 TransPraxis / 译践 品牌锁定"
        assert any("tp-provider is-unverified" in m.value for m in at.sidebar.markdown), \
            "未经连接测试的 Provider 不应显示绿色已连接状态"
        assert any("新建翻译任务" in m.value for m in at.markdown), \
            "应直接进入四步任务工作流，不显示营销 Hero"
        sidebar_labels = [b.label for b in at.sidebar.button]
        assert all(label in sidebar_labels for label in
                   ["01  文档与画像", "02  翻译策略", "03  交付内容",
                    "04  确认运行"]), \
            "侧栏应提供四步任务导航"
        new_task = next(b for b in at.sidebar.button if b.label == "新建任务")
        assert new_task.icon == ":material/add:", \
            "新建任务应表现为独立创建动作，不应与当前步骤使用同一语义"
        assert any(s.label == "目标语言" for s in at.selectbox), \
            "目标语言选择框应紧邻文档输入"
        assert any(b.label == "添加术语库" for b in at.button), \
            "术语库应使用添加附件按钮，不应使用开关"
        assert not at.toggle, "首屏不应以 Toggle 表达术语库附件操作"
        assert next(b for b in at.button if b.label == "下一步").disabled, \
            "未上传原文时下一步必须禁用"
        next(b for b in at.sidebar.button if b.label == "02  翻译策略").click()
        at.run()
        assert at.session_state["task_step"] == 1, "未上传原文时不能越过文档步骤"
        assert any("请先上传原文" in warning.value for warning in at.warning), \
            "被拦截时应给出明确操作提示"
        at.file_uploader[0].upload(
            "sample.docx", b"ui-state",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        at.run()
        assert any("sample.docx" in m.value for m in at.markdown), \
            "上传后应以文件状态卡替代空 Dropzone"
        assert any("已上传，等待解析" in m.value for m in at.markdown), \
            "文件卡应使用明确的上传/解析状态语义"
        assert not at.file_uploader, \
            "文件进入任务状态后只能显示自定义文件卡，不能保留原生上传条"
        assert not any("文件已就绪" in m.value for m in at.markdown), \
            "未解析的文档不能同时显示已就绪"
        assert not any("拖入文件或点击选择" in m.value for m in at.markdown), \
            "选中文件后不能继续显示空状态文案"
        at.session_state["source_parse_state"] = "parsing"
        at.run()
        assert any("正在解析" in m.value and "progress_activity" in m.value
                   for m in at.markdown), "解析阶段应显示明确文案与加载图标"
        assert not any("已上传，等待解析" in m.value for m in at.markdown), \
            "同一时刻只能显示一个文件状态"
        at.session_state["source_parse_state"] = "parsed"
        at.run()
        assert any("文件已就绪" in m.value and "tp-source-ready" in m.value
                   for m in at.markdown), \
            "解析完成后应切换到文件已就绪"
        entry_btn = next(b for b in at.button if b.label == "开始智能画像")
        assert entry_btn.icon == ":material/auto_awesome:", \
            "智能画像入口应自带智能图标"
        assert not any("智能风格建议" in m.value for m in at.markdown), \
            "初始状态不展示风格建议卡，点击后才出现"
        entry_btn.click()
        at.run()
        assert at.status and "风格" in at.status[0].label, \
            "智能画像执行时应显示进度状态，而不是白屏"
        assert any("未配置 AI 引擎" in w.value for w in at.warning), \
            "未配置 AI 引擎时画像应降级并给出明确提示"
        assert any("无法完成自动画像" in m.value for m in at.markdown), \
            "画像失败后应确定性降级为通用风格，而不是伪造推荐"
        assert any(b.label == "前往配置 API Key" for b in at.button), \
            "未配置 AI 引擎时应提供前往配置入口"
        assert any(b.label == "重试" for b in at.button), \
            "降级结果应允许重试"
        next(b for b in at.button if b.label == "调整").click()
        at.run()
        assert any(r.label == "基础风格" for r in at.radio), \
            "风格调整面板应显示基础风格单选项"
        assert all(any(s.label == label for s in at.slider) for label in (
            "表达正式度", "句法重构幅度", "术语保守程度", "原文形式保留")), \
            "风格调整面板应显示四个可调参数"
        next(b for b in at.button if b.label == "应用风格").click()
        at.run()
        assert at.session_state["style_selection"]["source"] == "user_override", \
            "应用风格后应记录为用户覆盖"
        next(b for b in at.button if b.label == "重试").click()
        at.run()
        assert any(b.label == "前往配置 API Key" for b in at.button), \
            "重试后仍未配置引擎时继续提供配置引导"
        next(b for b in at.button if b.label == "前往配置 API Key").click()
        at.run()
        assert at.session_state["app_view"] == "settings", \
            "前往配置应跳转到 AI 引擎设置页"
        next(b for b in at.sidebar.button if b.label == "新建任务").click()
        at.run()
        remove_source = next(b for b in at.button if b.label == "移除原文")
        assert remove_source.icon == ":material/delete_outline:", \
            "低频移除操作应收进文件卡并使用轻量图标"
        assert any("已保存" in m.value for m in at.markdown), \
            "已有输入时底部操作栏应反馈保存状态"
        assert not next(b for b in at.button if b.label == "下一步").disabled, \
            "上传原文后下一步必须变为可用"
        remove_source.click()
        at.run()
        assert "task_files" not in at.session_state, \
            "移除原文后不能被旧上传状态重新写回"
        assert at.file_uploader and not at.file_uploader[0].value, \
            "移除原文后应重置文件选择器"
        assert next(b for b in at.button if b.label == "下一步").disabled, \
            "移除原文后下一步必须重新禁用"
        at.file_uploader[0].upload(
            "sample.docx", b"ui-state",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        at.run()
        next(b for b in at.sidebar.button if b.label == "02  翻译策略").click()
        at.run()
        assert at.session_state["task_step"] == 2, "完成文档步骤后可进入翻译策略"
        assert next(b for b in at.sidebar.button
                    if b.label == "01  文档与画像").icon == \
            ":material/check_circle:", "完成步骤应使用完成状态节点"
        assert all(any(text in m.value for m in at.markdown) for text in (
            "快速生成可读初稿", "兼顾质量与效率", "适合需要完整过程证据的任务",
            "翻译 → 基础检查", "术语增强 → 翻译 → 基础检查",
            "术语治理 → 翻译 → 独立审校 → 学术证据",
            "最快", "成本最低", "术语更一致", "成本适中", "证据最完整", "耗时较长",
            "推荐")), \
            "三个预设必须直接说明工作流、取舍与推荐项"
        assert any("tp-preset-tag" in m.value for m in at.markdown), \
            "预设卡片应使用紧凑标签而不是长句描述"
        assert not any("自动术语 · 翻译记忆" in m.value for m in at.markdown), \
            "折叠的高级设置不应在右侧展示配置摘要，展开后再看内容"
        next(b for b in at.button if b.label == "切换高级设置").click()
        at.run()
        assert all(any(c.label == label for c in at.toggle) for label in (
            "自动术语抽取", "复用翻译记忆", "独立审校", "审核并冻结候选术语")), \
            "翻译策略只应展示影响翻译过程的有效配置"
        assert any("基础一致性检查" in m.value and "始终开启" in m.value
                   for m in at.markdown), \
            "基础一致性检查应使用只读状态而不是禁用复选框"
        assert not any(c.label in ("重点标注版", "实践报告") for c in at.toggle), \
            "下游输出不能混入翻译策略"
        strict_toggle = next(c for c in at.toggle if c.label == "审核并冻结候选术语")
        strict_toggle.set_value(True)
        at.run()
        assert any("标准 · 已调整" in m.value for m in at.markdown), \
            "修改预设后必须明确显示已调整"
        next(b for b in at.button if b.label == "选择标准预设").click()
        at.run()
        assert not any("标准 · 已调整" in m.value for m in at.markdown), \
            "恢复标准预设后应恢复默认配置状态"
        next(b for b in at.button if b.label == "下一步").click()
        at.run()
        assert at.session_state["task_step"] == 3, "翻译策略完成后可进入输出设置"
        assert all(any(c.label == label for c in at.toggle) for label in (
            "重点标注版", "生成实践报告")), "重点标注与报告应归入输出步骤"
        assert not any(s.label == "译文风格" for s in at.selectbox), \
            "风格选择已移入 Step 01 画像流程，交付页不再出现风格下拉"
        assert all(any(c.label == label for c in at.checkbox) for label in (
            "纯译文 DOCX", "双语对照 DOCX", "PDF 译文",
            "术语表 XLSX", "TBX", "TMX", "JSONL")), \
            "交付页应按 译文/语言资产 分组提供交付格式勾选"
        assert not any("风格与保留规则" in (t.label or "")
                       for t in at.text_area), \
            "交付页不应暴露可编辑风格规则"
        assert not any(s.label == "理论框架" for s in at.selectbox), \
            "实践报告关闭时不应显示理论框架"
        next(c for c in at.toggle if c.label == "生成实践报告").set_value(True)
        at.run()
        assert any(s.label == "理论框架" and s.value == "自动推荐（建议）"
                   for s in at.selectbox), \
            "只有实践报告开启后才显示证据约束的理论框架"
        assert any("参考文献与理论资料" in m.value for m in at.markdown), \
            "实践报告应让普通用户从参考文献与理论资料开始"
        assert any(f.label == "上传参考资料" for f in at.file_uploader), \
            "普通模式应上传论文等参考资料"
        assert any(e.label == "高级选项" for e in at.expander), \
            "已有 JSON 注册表应收纳在高级选项中"
        assert not any(f.label == "文献证据注册表（可选）" for f in at.file_uploader), \
            "普通界面不应再暴露工程化的注册表上传项"
        next(f for f in at.file_uploader if f.label == "上传参考资料").upload(
            "theory.md", b"# Theory\n\nA grounded paragraph.", "text/markdown")
        at.run()
        assert at.session_state["literature_upload_sources"][0]["source_type"] == "md", \
            "普通参考资料应转换为内部来源，而不是要求用户准备 JSON"
        at.session_state["task_files"][0]["name"] = \
            'sample"><img src=x onerror=alert(1)>.docx'
        at.session_state["task_glossary_name"] = '<svg onload=alert(1)>.tbx'
        at.session_state["task_glossary_count"] = 1
        next(b for b in at.button if b.label == "下一步").click()
        at.run()
        assert at.session_state["task_step"] == 4, "输出设置完成后可进入确认运行"
        assert all(any(text in m.value for m in at.markdown) for text in (
            "任务配置", "将生成", "运行环境", "双语译文", "翻译实践报告")), \
            "确认页应分别汇总配置、交付物与运行环境"
        confirmation_html = "\n".join(
            m.value for m in at.markdown if "tp-confirm-stack" in m.value)
        assert "<img src=x" not in confirmation_html \
            and "&lt;img src=x" in confirmation_html \
            and "<svg onload" not in confirmation_html \
            and "&lt;svg onload" in confirmation_html, \
            "上传文件名和术语库名进入自定义 HTML 前必须转义"
        assert any(b.label == "前往设置" for b in at.button), \
            "AI 引擎未配置时应提供直接的设置入口"
        assert not any(s.label in ("Provider", "Model", "服务商", "模型", "核心引擎")
                       for s in at.selectbox), "模型配置不应占据新建任务首屏"

        # Provider 设置是独立页面，模型目录仍按 A-Z 排序并支持中转站。
        at.session_state["model_choice_DeepSeek"] = "deepseek-chat"
        next(b for b in at.sidebar.button if b.label == "设置").click()
        at.run()
        assert not at.exception, f"打开设置页异常：{at.exception}"
        engine_select = next(s for s in at.selectbox if s.label == "服务商")
        assert engine_select.value == "DeepSeek"
        assert "自定义中转站" in engine_select.options
        model_select = next(s for s in at.selectbox if s.label == "模型")
        assert model_select.value == "deepseek-v4-flash", \
            "已退役的历史模型配置应回落到当前默认模型"
        model_opts = [o for o in model_select.options if o is not None]
        assert model_opts == sorted(model_opts, key=str.casefold)
        # API 配置必须跨页面保留（persist_state="session"）
        model_select.select("deepseek-v4-pro")
        at.run()
        next(t for t in at.text_input if t.label == "API 密钥").set_value("sk-persist")
        at.run()
        next(b for b in at.sidebar.button if b.label == "新建任务").click()
        at.run()
        next(b for b in at.sidebar.button if b.label == "设置").click()
        at.run()
        assert next(s for s in at.selectbox if s.label == "模型").value == \
            "deepseek-v4-pro", "切换页面后模型选择必须保留"
        assert next(t for t in at.text_input if t.label == "API 密钥").value == \
            "sk-persist", "切换页面后 API 密钥必须保留"
        next(b for b in at.button if b.label == "保存配置").click()
        at.run()
        saved_cfg = core.load_provider_config()
        assert saved_cfg and saved_cfg["provider"] == "DeepSeek" \
            and saved_cfg["model"] == "deepseek-v4-pro" \
            and saved_cfg["api_key"] == "sk-persist", \
            "保存配置应把服务商/模型/密钥写入本地配置文件"

        old_fetch_models = core.fetch_provider_models
        core.fetch_provider_models = lambda *args, **kwargs: (
            True, ["relay-model-b", "relay-model-a"], "已获取 2 个可用模型")
        try:
            at.session_state["provider_choice"] = "自定义中转站"
            at.session_state["api_key_自定义中转站"] = "sk-relay"
            at.session_state["custom_base_url"] = "https://relay.example.com/v1"
            at.run()
            assert any(b.label == "获取可用模型" and not b.disabled for b in at.button), \
                "填写 API Key 与地址后应允许获取中转站模型目录"
            next(b for b in at.button if b.label == "获取可用模型").click()
            at.run()
            fetched_select = next(s for s in at.selectbox if s.label == "模型")
            assert fetched_select.options == ["relay-model-a", "relay-model-b"] \
                and fetched_select.value in fetched_select.options, \
                "获取模型目录后应使用排序后的模型选择框"
            assert any("已获取 2 个可用模型" in m.value for m in at.success), \
                "模型目录获取成功应反馈数量"
        finally:
            core.fetch_provider_models = old_fetch_models

        print("AppTest 启动测试通过 ✅")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
