"""核心逻辑冒烟测试：解析、持久化、文档生成、端到端流水线与断点续传。

运行方式（项目根目录）：python tests/smoke_test.py
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from docx import Document


def test_parse_json_array():
    assert core.parse_json_array('["a", "b"]') == ["a", "b"]
    assert core.parse_json_array('```json\n["a"]\n```') == ["a"]
    assert core.parse_json_array('好的，结果如下：\n[{"Source": "MT", "Target": "机器翻译"}] 请查收') \
        == [{"Source": "MT", "Target": "机器翻译"}]
    assert core.parse_json_array('[1, 2] [3, 4]') == [1, 2]
    assert core.parse_json_array('不是 JSON') is None
    assert core.parse_json_array('') is None
    assert core.parse_json_array(None) is None
    print("  ✓ parse_json_array")


def test_misc_helpers():
    assert core.clean_xml_chars("a\x00b\x1fc") == "abc"
    assert core.clean_xml_chars(123) == "123"
    assert core.is_rate_limited(Exception("429 Too Many Requests"))
    assert core.is_rate_limited(Exception("RESOURCE_EXHAUSTED"))
    assert core.is_rate_limited(Exception("rate limit exceeded"))
    assert not core.is_rate_limited(Exception("boom"))
    assert core.call_llm("Nope", "k", "m", "s", "u") == ""
    assert core.file_job_id(b"x") == core.file_job_id(b"x")
    assert core.file_job_id(b"x") != core.file_job_id(b"y")
    print("  ✓ misc helpers")


def test_doc_generation():
    for buf in (core.paragraphs_to_word(["段落一"]),
                core.pairs_to_word([{"source": "a", "target": "b"}]),
                core.markdown_to_word("# 标题\n\n**加粗** 正文\n\n- 列表项", "目的论")):
        assert buf.getvalue().startswith(b"PK"), "生成的 docx 应为有效 zip"
    assert core.dict_to_excel({"MT": "机器翻译"}).getvalue().startswith(b"PK")
    print("  ✓ docx / xlsx 生成")


def test_termbase_parsing():
    buf = core.dict_to_excel({"MT": "机器翻译", "CAT": "计算机辅助翻译"})
    assert core.parse_termbase(buf) == {"MT": "机器翻译", "CAT": "计算机辅助翻译"}
    try:
        core.parse_termbase(io.BytesIO(b"not an excel"))
        raise AssertionError("应抛出 ValueError")
    except ValueError:
        pass
    print("  ✓ 术语库解析与错误提示")


def test_job_store():
    tmp = Path(tempfile.mkdtemp(prefix="mti-test-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        jid = "abcdef1234567890"
        assert core.load_job_state(jid) is None
        state = core.new_job_state("demo.pdf")
        state["paras"] = ["p1", "p2"]
        core.save_job_state(jid, state)
        loaded = core.load_job_state(jid)
        assert loaded["paras"] == ["p1", "p2"]
        assert loaded["filename"] == "demo.pdf"
        jobs = core.list_jobs()
        assert any(j["job_id"] == jid for j in jobs)
        assert core.progress_label(loaded) == "待处理"
        loaded.update(p1_done=True, p2_done=True, p3_done=True)
        assert core.progress_label(loaded) == "已完成"
        # 损坏的 state.json 不应崩溃
        (core.job_dir(jid) / "state.json").write_text("{broken", encoding="utf-8")
        assert core.load_job_state(jid) is None
        (core.job_dir(jid) / "state.json").write_text(
            core.job_state_path(jid).read_text() if False else '{"filename": "x"}', encoding="utf-8")
        assert core.load_job_state(jid)["filename"] == "x"
        core.delete_job(jid)
        assert core.load_job_state(jid) is None
        assert all(j["job_id"] != jid for j in core.list_jobs())
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)
    print("  ✓ 任务持久化（落盘/读取/列出/删除）")


def _make_docx(texts):
    buf = io.BytesIO()
    doc = Document()
    for t in texts:
        doc.add_paragraph(t)
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def _fake_llm_factory():
    """返回 (fake_llm, calls)：术语/翻译/报告均返回固定内容。"""
    calls = []

    def fake_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        calls.append(system_prompt[:10])
        if "术语管理专家" in system_prompt:
            return '[{"Source": "MT", "Target": "机器翻译"}, {"Source": "CAT", "Target": "计算机辅助翻译"}, 123, {"Source": null, "Target": "坏数据"}]'
        if "学术翻译专家" in system_prompt:
            return f"译文：{user_prompt}"
        if "学术排版专家" in system_prompt:
            return '["段落一", "段落二"]'
        return "这是报告章节内容，包含 **加粗** 与列表。\n\n- 要点一\n- 要点二"

    return fake_llm, calls


def test_e2e_pipeline():
    tmp = Path(tempfile.mkdtemp(prefix="mti-e2e-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        fake_llm, calls = _fake_llm_factory()
        core.call_llm = fake_llm
        docx_bytes = _make_docx(["这是第一段，涉及术语 MT。", "这是第二段，涉及术语 CAT。"])
        jid = "e2e0000000000001"
        state = core.run_job_pipeline(
            jid, "demo.docx", docx_bytes,
            provider="DeepSeek", api_key="test-key", model="deepseek-chat",
            target_lang="简体中文", auto_term=True, enable_report=True,
            translation_theory="目的论 (Skopos Theory)", user_termbase={})
        assert state["p1_done"] and len(state["paras"]) == 2
        assert state["auto_terms"] == {"MT": "机器翻译", "CAT": "计算机辅助翻译"}
        assert state["p2_done"] and len(state["pairs"]) == 2
        assert state["pairs"][0]["target"].startswith("译文：")
        assert state["p3_done"]
        assert state["p3_md"].count("## ") == 4, "报告应包含四个章节"
        # 幂等：已完成任务再次运行不产生额外 LLM 调用
        n_before = len(calls)
        state2 = core.run_job_pipeline(
            jid, "demo.docx", None,
            provider="DeepSeek", api_key="test-key", model="deepseek-chat",
            target_lang="简体中文", auto_term=True, enable_report=True,
            translation_theory="目的论 (Skopos Theory)", user_termbase={})
        assert len(calls) == n_before
        assert state2["p3_md"] == state["p3_md"]
        # 源文件已留存，可删除后重跑阶段一
        assert core.load_source(jid) == docx_bytes
        print("  ✓ 端到端流水线（清洗/术语/翻译/报告/幂等）")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_resume_translation():
    tmp = Path(tempfile.mkdtemp(prefix="mti-resume-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        docx_bytes = _make_docx(["这是第一段，内容足够长以通过过滤。",
                                 "这是第二段，内容足够长以通过过滤。",
                                 "这是第三段，内容足够长以通过过滤。"])
        jid = "e2e0000000000002"

        def flaky_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
            if "学术翻译专家" in system_prompt:
                if "第二段" in user_prompt:
                    raise RuntimeError("模拟网络中断")
                return f"译文：{user_prompt}"
            if "术语管理专家" in system_prompt:
                return '[]'  # 空术语表
            return "报告章节内容。"

        core.call_llm = flaky_llm
        try:
            core.run_job_pipeline(
                jid, "demo.docx", docx_bytes,
                provider="DeepSeek", api_key="test-key", model="deepseek-chat",
                target_lang="简体中文", auto_term=True, enable_report=True,
                translation_theory="目的论 (Skopos Theory)", user_termbase={})
            raise AssertionError("应在第二段翻译处抛出异常")
        except RuntimeError as e:
            assert "模拟网络中断" in str(e)

        # 中断后：阶段一已完成、只翻译了第一段，且已落盘
        mid = core.load_job_state(jid)
        assert mid["p1_done"] and len(mid["pairs"]) == 1
        assert any("术语抽取失败" in w for w in mid["warnings"])
        assert sum("术语抽取失败" in w for w in mid["warnings"]) == 1

        # 模拟刷新后继续：不传文件字节，直接从磁盘恢复
        fake_llm, _ = _fake_llm_factory()
        core.call_llm = fake_llm
        state = core.run_job_pipeline(
            jid, "demo.docx", None,
            provider="DeepSeek", api_key="test-key", model="deepseek-chat",
            target_lang="简体中文", auto_term=True, enable_report=True,
            translation_theory="目的论 (Skopos Theory)", user_termbase={})
        assert state["p2_done"] and len(state["pairs"]) == 3
        assert state["pairs"][0]["target"] == "译文：这是第一段，内容足够长以通过过滤。"
        assert state["pairs"][1]["target"] == "译文：这是第二段，内容足够长以通过过滤。"
        assert state["p3_done"]
        print("  ✓ 翻译中断 -> 磁盘断点续传")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_resume_report_sections():
    tmp = Path(tempfile.mkdtemp(prefix="mti-report-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        docx_bytes = _make_docx(["这是第一段，内容足够长以通过过滤。"])
        jid = "e2e0000000000003"

        class FlakyReport:
            def __init__(self):
                self.report_calls = 0

            def __call__(self, provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
                if "学术翻译专家" in system_prompt:
                    return f"译文：{user_prompt}"
                if "术语管理专家" in system_prompt:
                    return '[]'
                if "MTI（翻译硕士）导师" in system_prompt:
                    self.report_calls += 1
                    if self.report_calls == 4:
                        raise RuntimeError("模拟报告中断")
                return "报告章节内容。"

        flaky = FlakyReport()
        core.call_llm = flaky
        try:
            core.run_job_pipeline(
                jid, "demo.docx", docx_bytes,
                provider="DeepSeek", api_key="test-key", model="deepseek-chat",
                target_lang="简体中文", auto_term=True, enable_report=True,
                translation_theory="目的论 (Skopos Theory)", user_termbase={})
            raise AssertionError("应在第四章节处抛出异常")
        except RuntimeError as e:
            assert "报告章节" in str(e)

        mid = core.load_job_state(jid)
        assert len(mid["p3_sections"]) == 3, "前三章应已落盘"
        assert not mid["p3_done"]

        fake_llm, _ = _fake_llm_factory()
        core.call_llm = fake_llm
        state = core.run_job_pipeline(
            jid, "demo.docx", None,
            provider="DeepSeek", api_key="test-key", model="deepseek-chat",
            target_lang="简体中文", auto_term=True, enable_report=True,
            translation_theory="目的论 (Skopos Theory)", user_termbase={})
        assert state["p3_done"]
        assert len(state["p3_sections"]) == 4
        assert state["p3_md"].count("## ") == 4
        assert flaky.report_calls == 4, "续跑时只应生成缺失的第四章"
        print("  ✓ 报告章节级断点续写")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_source():
    tmp = Path(tempfile.mkdtemp(prefix="mti-missing-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        try:
            core.run_job_pipeline(
                "e2e0000000000004", "x.pdf", None,
                provider="DeepSeek", api_key="k", model="deepseek-chat",
                target_lang="简体中文", auto_term=True, enable_report=True,
                translation_theory="目的论 (Skopos Theory)", user_termbase={})
            raise AssertionError("缺少源文件时应抛出 ValueError")
        except ValueError:
            pass
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)
    print("  ✓ 缺少源文件的防护")


if __name__ == "__main__":
    print("core 冒烟测试：")
    test_parse_json_array()
    test_misc_helpers()
    test_doc_generation()
    test_termbase_parsing()
    test_job_store()
    test_e2e_pipeline()
    test_resume_translation()
    test_resume_report_sections()
    test_missing_source()
    print("\n全部通过 ✅")
