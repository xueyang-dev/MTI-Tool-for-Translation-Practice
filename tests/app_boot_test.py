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
        # 预置一个本地任务，确保「资产与交付 / 学术写作」Tabs 一定渲染
        jid = "ab000000000000001"
        state = core.new_job_state("boot_fixture.pdf")
        state.update(p1_done=True, p2_done=True, paras=["hello"],
                     pairs=[{"source": "hello", "target": "你好"}],
                     stage="DONE",
                     delivery_status="draft")
        core.save_job_state(jid, state)
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
        assert any("MTI Tool" in m.value for m in at.sidebar.markdown), \
            "侧栏应显示克制的产品品牌"
        assert any("mti-provider is-unverified" in m.value for m in at.sidebar.markdown), \
            "未经连接测试的 Provider 不应显示绿色已连接状态"
        assert any("新建翻译任务" in m.value for m in at.markdown), \
            "应直接进入四步任务工作流，不显示营销 Hero"
        sidebar_labels = [b.label for b in at.sidebar.button]
        assert all(label in sidebar_labels for label in
                   ["01  文档", "02  翻译策略", "03  输出", "04  确认运行"]), \
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
        at.session_state["task_files"] = [{"name": "sample.docx", "bytes": b"ui-state"}]
        at.run()
        assert any("sample.docx" in m.value for m in at.markdown), \
            "上传后应以文件状态卡替代空 Dropzone"
        assert any("已上传 · 等待解析" in m.value for m in at.markdown), \
            "文件卡应使用明确的上传/解析状态语义"
        assert not any("文件已就绪" in m.value for m in at.markdown), \
            "未解析的文档不能同时显示已就绪"
        remove_source = next(b for b in at.button if b.label == "移除原文")
        assert remove_source.icon == ":material/delete_outline:", \
            "低频移除操作应收进文件卡并使用轻量图标"
        assert any("已保存" in m.value for m in at.markdown), \
            "已有输入时底部操作栏应反馈保存状态"
        assert not next(b for b in at.button if b.label == "下一步").disabled, \
            "上传原文后下一步必须变为可用"
        next(b for b in at.sidebar.button if b.label == "02  翻译策略").click()
        at.run()
        assert at.session_state["task_step"] == 2, "完成文档步骤后可进入翻译策略"
        assert next(b for b in at.sidebar.button if b.label == "01  文档").icon == \
            ":material/check_circle:", "完成步骤应使用完成状态节点"
        assert all(any(text in m.value for m in at.markdown) for text in (
            "快速获得可读初稿", "翻译 → 质量检查", "质量最高 · 耗时较长", "推荐")), \
            "三个预设必须直接说明工作流、取舍与推荐项"
        assert not any("案例分析理论" == s.label for s in at.selectbox), \
            "实践报告关闭时不应显示案例分析理论"
        next(b for b in at.button if b.label == "高级设置").click()
        at.run()
        assert all(any(c.label == label for c in at.toggle) for label in (
            "术语抽取", "使用翻译记忆", "独立审校",
            "标记值得分析的翻译案例", "生成实践报告")), \
            "高级设置应展示有效配置而非内部参数面板"
        report_toggle = next(c for c in at.toggle if c.label == "生成实践报告")
        report_toggle.set_value(True)
        at.run()
        assert any("标准 · 已调整" in m.value for m in at.markdown), \
            "修改预设后必须明确显示已调整"
        assert any(s.label == "案例分析理论" for s in at.selectbox), \
            "只有生成实践报告开启时才显示案例分析理论"
        next(b for b in at.button if b.label == "选择标准预设").click()
        at.run()
        assert not any(s.label == "案例分析理论" for s in at.selectbox), \
            "恢复标准预设后应收起无关的学术字段"
        assert not any(s.label in ("Provider", "Model", "服务商", "模型", "核心引擎")
                       for s in at.selectbox), "模型配置不应占据新建任务首屏"

        # Provider 设置是独立页面，模型目录仍按 A-Z 排序并支持中转站。
        next(b for b in at.sidebar.button if b.label == "设置").click()
        at.run()
        assert not at.exception, f"打开设置页异常：{at.exception}"
        engine_select = next(s for s in at.selectbox if s.label == "服务商")
        assert engine_select.value == "DeepSeek"
        assert "自定义中转站" in engine_select.options
        model_select = next(s for s in at.selectbox if s.label == "模型")
        model_opts = [o for o in model_select.options if o is not None]
        assert model_opts == sorted(model_opts, key=str.casefold)

        print("AppTest 启动测试通过 ✅")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
