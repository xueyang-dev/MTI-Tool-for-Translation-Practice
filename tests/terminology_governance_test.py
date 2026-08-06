"""术语治理新增能力测试（阶段 1：数据模型 / 状态迁移 / 文档画像）。

运行方式（项目根目录）：python tests/terminology_governance_test.py
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from mti_tool import document_profile, models, state_migration, terminology


def test_document_profile_normalize_validate():
    raw = {
        "domain": "生物学",
        "subdomain": "行为生态学",
        "genre": "科普著作",
        "audience": "大众读者",
        "register": "半正式书面语",
        "style_constraints": "保留隐喻与叙事语气",
        "confidence": 0.8,
        "sections": [
            {"section_id": "s1", "start_segment": 0, "end_segment": 9,
             "topic": "引言", "domain": "生态学", "style": "叙事"},
            {"section_id": "bad", "start_segment": 9, "end_segment": 2,
             "topic": "非法区间应丢弃"},
            {"section_id": "s2", "start_segment": 10, "end_segment": 20,
             "topic": "实验方法", "domain": "行为学", "style": "说明"},
        ],
    }
    p = models.normalize_document_profile(raw)
    assert p["domain"] == "生物学"
    assert p["confidence"] == 0.8
    assert [s["section_id"] for s in p["sections"]] == ["s1", "s2"]
    assert models.validate_document_profile(p) == []

    # 垃圾输入 -> 全默认值，不抛异常
    p2 = models.normalize_document_profile("garbage")
    assert p2["domain"] == "" and p2["sections"] == []
    assert models.validate_document_profile(p2), "缺少 domain 应报问题"
    assert models.validate_document_profile(None)
    print("  ✓ DocumentProfile normalize/validate")


def test_profile_json_parse_and_degrades():
    # 合法 JSON 包裹在解释文字中也能解析
    ok = '好的：\n```json\n{"domain": "历史学", "confidence": 0.7, "sections": []}\n```'
    parsed = document_profile._parse_profile_json(ok)
    assert parsed and parsed["domain"] == "历史学"
    assert document_profile._parse_profile_json("不是 JSON") is None

    # 失败必须返回 warning + None，不能静默伪造
    paras = [f"第{i}段生物学文本。" for i in range(30)]

    def bad_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        return "抱歉，我无法完成这个任务。"

    profile, warnings = document_profile.profile_document(
        paras, "DeepSeek", "k", "deepseek-chat", call_llm=bad_llm)
    assert profile is None
    assert warnings and any("文档画像失败" in w for w in warnings)

    # 空文本 -> 失败 warning
    profile2, warnings2 = document_profile.profile_document([], "DeepSeek", "k", "m",
                                                            call_llm=bad_llm)
    assert profile2 is None and warnings2

    # 合法输出 -> 画像成功
    def good_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        return json.dumps({"domain": "动物行为学", "subdomain": "鸟类学",
                           "genre": "回忆录", "audience": "成人读者",
                           "register": "文学性书面语", "style_constraints": "保留诗意比喻",
                           "confidence": 0.9, "sections": []})

    profile3, warnings3 = document_profile.profile_document(
        paras, "DeepSeek", "k", "deepseek-chat", call_llm=good_llm)
    assert profile3 is not None and profile3["domain"] == "动物行为学"
    assert not any("失败" in w for w in warnings3)
    print("  ✓ 画像 JSON 解析 / 失败降级 / 成功校验")


def test_distributed_sample_covers_head_middle_tail():
    paras = [f"paragraph-{i}" for i in range(100)]
    wins = document_profile.distributed_sample(paras, n_windows=3, chars_per_window=10)
    assert len(wins) == 3
    starts = [w["start_segment"] for w in wins]
    assert starts[0] == 0, "必须覆盖开头"
    assert starts[-1] <= 99 and wins[-1]["end_segment"] == 99, "必须覆盖结尾"
    # 中间窗口确实落在中间区域（而不是只取开头）
    assert wins[1]["start_segment"] > 0
    assert any(40 <= w["start_segment"] <= 60 for w in wins)
    # 每窗口都带文本且字符不超上限太多
    for w in wins:
        assert w["text"]
        assert len(w["text"]) <= 10 * 3, "窗口文本应受字符上限约束"

    # 段落很少时退化为单窗口全量采样
    small = document_profile.distributed_sample(["a", "b"])
    assert len(small) == 1 and small[0]["start_segment"] == 0
    assert document_profile.distributed_sample([]) == []
    print("  ✓ 分布式采样覆盖首/中/尾")


def test_glossary_entry_normalize_excel_compat():
    raw = {"Source": "Skopos", "Target": "目的论", "Behavior": "translate",
           "Status": "locked", "Preferred": "目的论", "Forbidden": "功能对等;目的学派",
           "Scope": "global", "Note": "核心理论", "occurrences": [0, 3, 7, 3, "x"]}
    e = models.normalize_glossary_entry(raw)
    assert e["source"] == "Skopos" and e["status"] == "locked"
    assert e["forbidden"] == ["功能对等", "目的学派"]
    assert e["occurrences"] == [0, 3, 7], "occurrences 应去重排序并丢弃非法值"
    assert e["id"].startswith("t-")
    # 相同内容 -> 相同 ID
    assert models.entry_id("Skopos", "目的论", "translate") == e["id"]
    assert models.normalize_glossary_entry(None) is None
    assert models.normalize_glossary_entry({"Source": "  "}) is None
    print("  ✓ GlossaryEntry normalize（Excel 列兼容 + occurrences 归一）")


def test_evidence_no_fake_url():
    # model_knowledge 不允许带 URL：自动清除并注明
    ev = models.normalize_evidence(
        {"evidence_type": "model_knowledge", "url": "https://fake.example/x",
         "note": "模型知识"})
    assert ev["evidence_type"] == "model_knowledge"
    assert ev["url"] == ""
    assert "伪造" in ev["note"]
    assert models.validate_evidence(ev) == []

    # external 必须有真实来源 URL；没有 -> 降级为 model_knowledge
    ev2 = models.normalize_evidence(
        {"evidence_type": "external", "source_name": "某外部工具", "url": ""})
    assert ev2["evidence_type"] == "model_knowledge"
    assert ev2["url"] == "" and "降级" in ev2["note"]

    # 真实外部来源 -> 保留 URL
    ev3 = models.normalize_evidence(
        {"evidence_type": "external", "source_name": "termbase.io",
         "url": "https://termbase.io/term/123"})
    assert ev3["evidence_type"] == "external"
    assert ev3["url"].startswith("https://termbase.io")
    assert models.validate_evidence(ev3) == []

    # 非法类型 -> model_knowledge
    ev4 = models.normalize_evidence({"evidence_type": "瞎编", "url": "https://x"})
    assert ev4["evidence_type"] == "model_knowledge" and ev4["url"] == ""
    print("  ✓ 证据模型：model_knowledge 禁伪造 URL / external 来源约束")


def test_glossary_hash_deterministic():
    a = [{"source": "Skopos", "target": "目的论", "status": "locked"},
         {"source": "John Smith", "target": "约翰·史密斯", "behavior": "preserve",
          "status": "locked"}]
    b = [{"source": "John Smith", "target": "约翰·史密斯", "behavior": "preserve",
          "status": "locked"},
         {"source": "Skopos", "target": "目的论", "status": "locked"}]
    ha = models.glossary_hash(a)
    hb = models.glossary_hash(b)
    assert ha == hb, "条目顺序变化不应改变 glossary_hash"
    assert len(ha) == 64
    # 内容变化 -> 哈希变化
    c = [{"source": "Skopos", "target": "翻译目的论", "status": "locked"},
         {"source": "John Smith", "target": "约翰·史密斯", "behavior": "preserve",
          "status": "locked"}]
    assert models.glossary_hash(c) != ha

    fg = models.normalize_frozen_glossary(
        {"version": 1, "source_hash": "abc", "entries": a,
         "frozen_at": "2026-08-06T00:00:00", "frozen_by": "tester"})
    assert fg["glossary_hash"] == ha
    assert models.validate_frozen_glossary(fg) == []
    assert models.validate_frozen_glossary(None)
    # 篡改条目 -> 校验失败
    fg2 = dict(fg)
    fg2["entries"] = models.normalize_glossary(c)
    assert models.validate_frozen_glossary(fg2)
    print("  ✓ 冻结术语表哈希确定性 + 篡改校验")


def test_state_migration_old_job():
    # 模拟旧版本 state.json（只有旧字段）
    old = {
        "filename": "book.pdf",
        "p1_done": True,
        "p2_done": False,
        "p3_done": False,
        "report_enabled": True,
        "paras": ["a", "b"],
        "pairs": [],
        "auto_terms": {"MT": "机器翻译"},
        "findings": [],
        "review_stats": {},
        "tm_used_count": 0,
        "has_blocking": False,
        "warnings": [],
        "annotations_done": False,
    }
    m = state_migration.migrate_state(old)
    assert m["stage"] in ("TERMS_PREPARED", "PROFILED"), m["stage"]
    assert m["delivery_status"] == "draft"
    assert m["glossary_frozen"] is None, "旧任务不得虚假标记为已冻结"
    assert m["document_profile"] is None
    assert m["glossary"] == [] and m["auto_term_entries"] == []
    assert m["human_actions"] == []
    assert m["p1_done"] is True, "旧字段不得被改动"

    # 翻译完成但有 blocking -> review_required
    old2 = dict(old, p2_done=True, p3_done=True, has_blocking=True)
    m2 = state_migration.migrate_state(old2)
    assert m2["delivery_status"] == "review_required"
    assert m2["stage"] == "REVIEW_REQUIRED"

    # 全部完成且无 blocking -> 保持 draft，绝不自动 final
    old3 = dict(old, p2_done=True, p3_done=True, has_blocking=False,
                annotations_done=True)
    m3 = state_migration.migrate_state(old3)
    assert m3["delivery_status"] == "draft"
    assert m3["stage"] == "REPORT_GENERATED"

    # 显式 final 不被覆盖
    old4 = dict(old, delivery_status="final")
    assert state_migration.migrate_state(old4)["delivery_status"] == "final"
    print("  ✓ 旧 state 迁移（默认值 / stage / delivery / 不伪造冻结）")


def test_core_load_job_state_migrates():
    tmp = Path(tempfile.mkdtemp(prefix="mti-mig-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        jid = "mig00000000000001"
        d = core.job_dir(jid)
        d.mkdir(parents=True, exist_ok=True)
        (d / "state.json").write_text(json.dumps(
            {"filename": "old.pdf", "p1_done": True, "p2_done": True, "p3_done": True,
             "auto_terms": {}}), encoding="utf-8")
        state = core.load_job_state(jid)
        assert state is not None
        assert state["stage"] == "REPORT_GENERATED"
        assert state["delivery_status"] == "draft"
        assert state["glossary_frozen"] is None
        # 新任务默认字段齐全
        ns = core.new_job_state("new.pdf")
        for key in ("stage", "delivery_status", "document_profile", "glossary",
                    "glossary_frozen", "human_actions"):
            assert key in ns
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)
    print("  ✓ core.load_job_state 迁移 + new_job_state 新字段")


def test_term_matches_word_boundary():
    assert terminology.term_matches("Skopos", "The Skopos theory is central.")
    assert terminology.term_matches("skopos", "The SKOPOS theory is central."), "大小写不敏感"
    assert terminology.term_matches("MT", "MT is machine translation.")
    assert not terminology.term_matches("MT", "The MTI tool translates books."), \
        "短词不得在更长词内部误命中"
    assert not terminology.term_matches("AI", "The mountain is high in the main range."), \
        "AI 不得命中 MAIN/mountain 等普通词"
    assert terminology.term_matches("AI", "The AI model works.")
    assert terminology.term_matches("目的论", "翻译目的论是核心概念。"), "CJK 术语按子串匹配"
    assert not terminology.term_matches("", "text")
    assert not terminology.term_matches("x", None)
    print("  ✓ 术语匹配（大小写 + 词边界 + CJK + 短词防误命中）")


def test_find_occurrences_all_segments():
    paras = [
        "The Skopos theory guides the translation.",
        "This chapter discusses Skopos and fidelity.",
        "No term here.",
        "SKOPOS appears again at the end.",
    ]
    occ = terminology.find_occurrences("Skopos", paras)
    assert occ == [0, 1, 3], "必须记录全部出现位置，而不是只记第一次"
    assert terminology.find_occurrences("不存在的术语", paras) == []
    assert terminology.find_occurrences("MT", ["MTI is a tool"]) == [], "短词不应命中 MTI"
    print("  ✓ occurrences 记录全部 segment_id")


def test_extract_auto_terms_v2():
    paras = [f"第{i}段：The Skopos theory and the fidelity principle 是本章核心。"
             for i in range(12)]
    profile = models.normalize_document_profile(
        {"domain": "翻译学", "confidence": 0.8, "sections": []})
    calls = {"n": 0}

    def llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        calls["n"] += 1
        return json.dumps([
            {"Source": "Skopos theory", "Target": "目的论"},
            {"Source": "fidelity principle", "Target": "忠实原则"},
            {"Source": "Skopos theory", "Target": "翻译目的论", "domain": "翻译学"},
            {"Source": "MT", "Target": "机器翻译"},   # 短词但仍合法
            123,
            {"Source": None, "Target": "坏数据"},
        ])

    entries, warnings = terminology.extract_auto_terms_v2(
        paras, "简体中文", "DeepSeek", "k", "deepseek-chat",
        document_profile=profile, call_llm=llm)
    assert calls["n"] == 1
    assert warnings == []
    by_source = {e["source"]: e for e in entries}
    assert "Skopos theory" in by_source and "fidelity principle" in by_source
    # 去重：同 source 只保留一条，occurrences 取并集
    assert by_source["Skopos theory"]["target"] == "目的论", "保留首次译名"
    assert by_source["Skopos theory"]["occurrences"] == list(range(12)), \
        "重复候选应合并全部 occurrence"
    # 垃圾条目被丢弃；candidate 状态；evidence 为 model_knowledge 且无 URL
    assert "MT" in by_source and len(by_source) == 3
    assert all(e["status"] == "candidate" for e in entries), "自动术语不得自动 locked"
    assert all(e["evidence"][0]["evidence_type"] == "model_knowledge" for e in entries)
    assert all(not e["evidence"][0]["url"] for e in entries), "model_knowledge 禁 URL"
    assert by_source["Skopos theory"]["domain"] == "翻译学", "domain 来自画像/模型"
    assert all(e["scope"] == "document" for e in entries)

    # 失败：返回垃圾 -> warning，不静默宣称成功
    def bad_llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        return "很抱歉，我无法输出 JSON。"

    entries2, warnings2 = terminology.extract_auto_terms_v2(
        paras, "简体中文", "DeepSeek", "k", "m", call_llm=bad_llm)
    assert entries2 == [] and any("术语抽取失败" in w for w in warnings2)
    print("  ✓ 分布式术语抽取（去重 / 全量 occurrences / candidate / 证据 / 失败 warning）")


def _make_docx(texts):
    import io
    from docx import Document
    buf = io.BytesIO()
    doc = Document()
    for t in texts:
        doc.add_paragraph(t)
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def test_review_state_persist_and_restore():
    tmp = Path(tempfile.mkdtemp(prefix="mti-termstate-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        docx_bytes = _make_docx(["The Skopos theory 是本章核心。",
                                 "The fidelity principle 也很重要。"])
        jid = "ts000000000000001"
        calls = {"extract": 0, "translate": 0}

        def llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
            if "术语管理专家" in system_prompt:
                calls["extract"] += 1
                return json.dumps([
                    {"Source": "Skopos theory", "Target": "目的论"},
                    {"Source": "fidelity principle", "Target": "忠实原则"},
                ])
            if "学术翻译专家" in system_prompt:
                calls["translate"] += 1
                return json.dumps([f"译文：{s}" for s, _ in _numbered(user_prompt)])
            if "翻译审校专家" in system_prompt:
                return '[]'
            return "报告章节内容。"

        core.call_llm = llm
        kwargs = dict(provider="DeepSeek", api_key="k", model="deepseek-chat",
                      target_lang="简体中文", auto_term=True, enable_report=False,
                      translation_theory="目的论 (Skopos Theory)", user_glossary=[])

        # 高质量模式：术语抽取后停在审核阶段，不得翻译
        state = core.run_job_pipeline(jid, "t.docx", docx_bytes, mode="quality", **kwargs)
        assert state["p1_done"] and state["p2_done"] is False
        assert state["stage"] == "TERMS_PREPARED"
        assert state["delivery_status"] == "draft"
        assert calls["translate"] == 0
        assert len(state["glossary"]) == 2
        assert all(e["status"] == "candidate" for e in state["glossary"])
        assert any("尚未冻结" in w for w in state["warnings"])

        # 刷新/重启：从磁盘恢复，不得重新抽取，也不得翻译
        state2 = core.run_job_pipeline(jid, "t.docx", None, mode="quality", **kwargs)
        assert calls["extract"] == 1, "恢复时不得重新抽取术语"
        assert calls["translate"] == 0
        assert state2["stage"] == "TERMS_PREPARED"
        assert len(state2["glossary"]) == 2
        assert state2["auto_term_entries"][0]["occurrences"] == [0], \
            "occurrences 已持久化"

        # 冻结后：允许翻译
        frozen = core.freeze_glossary(jid, frozen_by="测试用户")
        assert frozen["glossary_frozen"]["version"] == 1
        assert frozen["glossary_frozen"]["glossary_hash"]
        state3 = core.run_job_pipeline(jid, "t.docx", None, mode="quality", **kwargs)
        assert state3["p2_done"] is True and len(state3["pairs"]) == 2

        # 修改术语再冻结 -> 新版本 + 新哈希，旧版本保留
        entries = list(frozen["glossary"])
        entries[0]["target"] = "翻译目的论"
        frozen2 = core.freeze_glossary(jid, entries=entries, frozen_by="测试用户")
        assert frozen2["glossary_frozen"]["version"] == 2
        assert frozen2["glossary_frozen"]["glossary_hash"] != \
            frozen["glossary_frozen"]["glossary_hash"]
        assert len(frozen2["glossary_versions"]) == 2
        assert frozen2["glossary_versions"][0]["glossary_hash"] == \
            frozen["glossary_frozen"]["glossary_hash"], "旧冻结状态不得被覆盖"

        # 快速模式：直接翻译，自动术语为 provisional
        jid2 = "ts000000000000002"
        state_q = core.run_job_pipeline(jid2, "q.docx", docx_bytes, mode="quick", **kwargs)
        assert state_q["p2_done"] is True
        assert all(e["status"] == "provisional" for e in state_q["glossary"])
        print("  ✓ 审核状态持久化/恢复 + 冻结门禁 + 版本化 + 快速模式")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


def _numbered(user_prompt):
    import re
    segs = [(int(m.group(1)), m.group(2).strip())
            for m in re.finditer(r'^\s*(\d+)\.\s+(.+?)\s*$', user_prompt, re.M)]
    segs.sort(key=lambda x: x[0])
    return segs


def test_apptest_term_review_panel():
    from streamlit.testing.v1 import AppTest
    tmp = Path(tempfile.mkdtemp(prefix="mti-apptest-"))
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp
    try:
        jid = "qt000000000000001"
        state = core.new_job_state("quality.docx")
        state.update(
            p1_done=True, p2_done=False, quality_mode=True, profile_done=True,
            paras=["The Skopos theory 是核心概念。",
                   "The fidelity principle 也很重要。"],
            auto_terms={"Skopos theory": "目的论"},
            glossary=[{
                "id": "t-abc123", "source": "Skopos theory", "target": "目的论",
                "proposed_target": "目的论", "preferred": "目的论", "forbidden": [],
                "behavior": "translate", "status": "candidate", "domain": "翻译学",
                "scope": "document", "note": "", "confidence": 0.5,
                "occurrences": [0],
                "evidence": [{"evidence_type": "model_knowledge", "source_name": "",
                              "note": "自动抽取", "quote": "", "url": "",
                              "confidence": 0.5}],
            }],
            stage="TERMS_PREPARED", delivery_status="draft",
        )
        core.save_job_state(jid, state)

        at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"),
                               default_timeout=30)
        at.run()
        assert not at.exception, f"应用启动异常：{at.exception}"
        subheaders = [s.value for s in at.subheader]
        assert any("术语准备与审核" in s for s in subheaders), subheaders
        labels = [b.label for b in at.button]
        assert any("冻结术语表并继续翻译" in l for l in labels), labels
        start_btns = [b for b in at.button if "开始翻译" in b.label]
        assert start_btns, "应存在「开始翻译」按钮"
        assert start_btns[0].disabled is True, "未冻结时「开始翻译」按钮必须不可执行"
        print("  ✓ AppTest：术语审核面板显示 + 冻结门（翻译按钮禁用）")
    finally:
        core.OUTPUT_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("术语治理测试（模型/迁移/画像/术语候选）：")
    test_document_profile_normalize_validate()
    test_profile_json_parse_and_degrades()
    test_distributed_sample_covers_head_middle_tail()
    test_glossary_entry_normalize_excel_compat()
    test_evidence_no_fake_url()
    test_glossary_hash_deterministic()
    test_state_migration_old_job()
    test_core_load_job_state_migrates()
    test_term_matches_word_boundary()
    test_find_occurrences_all_segments()
    test_extract_auto_terms_v2()
    test_review_state_persist_and_restore()
    test_apptest_term_review_panel()
    print("\n全部通过 ✅")
