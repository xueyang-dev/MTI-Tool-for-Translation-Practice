"""Academic pipeline checks. Run: python tests/academic_writing_test.py"""
from __future__ import annotations

import json
import io
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence, academic_validator, academic_writer
import core
from docx import Document


JOB = "academicfixture01"


def _state(n=12):
    pairs = []
    for i in range(n):
        source = (f"Although segment {i} contains several clauses, the pilot continued "
                  "because the mission mattered, which required careful judgment.")
        initial = f"第{i}段初译。"
        target = f"尽管第{i}段包含多个分句，飞行员仍继续执行任务，因为任务需要审慎判断。"
        pairs.append({
            "source": source, "target": target, "initial_target": initial,
            "reviewed": True, "from_tm": i == 5, "glossary_entry_ids": ["term-1"],
        })
    return {
        "filename": "fixture.docx", "paras": [x["source"] for x in pairs],
        "pairs": pairs,
        "findings": [
            {"segment_index": 0, "severity": "actionable", "type": "review",
             "reason": "初译遗漏让步关系", "suggested_target": pairs[0]["target"]},
            {"segment_index": n // 2, "severity": "blocking", "type": "check",
             "reason": "译文疑似截断", "resolved": True},
            {"segment_index": n - 1, "severity": "informational", "type": "review",
             "reason": "结尾段语气处理可接受"},
        ],
        "human_actions": [{"finding_id": "segment:0", "action": "retranslated",
                           "note": "重译", "timestamp": "2026-08-09T00:00:00Z"}],
        "glossary": [{"id": "term-1", "source": "pilot", "target": "飞行员",
                      "preferred": "飞行员", "status": "locked",
                      "behavior": "translate"}],
        "review_stats": {"reviewed_segments": n, "blocking": 1,
                         "actionable": 1, "informational": 1},
        "tm_used_count": 1,
        "document_profile": {"genre": "回忆录", "sections": []},
        "p1_done": True, "p2_done": True, "p3_done": False,
        "report_enabled": True, "p3_md": "", "p3_sections": [], "theory": "",
    }


def test_whole_corpus_evidence_and_candidates():
    evidence = academic_evidence.build_academic_evidence(_state(), JOB, max_candidates=9)
    coverage = evidence["coverage_policy"]
    assert coverage["scan_scope"] == "whole_corpus"
    assert coverage["segments_scanned"] == 12
    zones = {x["coverage_zone"] for x in evidence["candidate_cases"]}
    assert zones == {"beginning", "middle", "end"}
    stats = evidence["project_evidence"]["statistics"]
    assert stats["total_segments"] == 12 and stats["tm_reuse_count"] == 1
    assert stats["actionable_findings"] == 1 and stats["blocking_findings"] == 1
    first = evidence["project_evidence"]["segments"][0]
    assert first["process_evidence"]["repair_history"]
    assert first["availability"]["initial_target"] == "recorded"
    print("  ✓ 全语料证据 / 首中尾覆盖 / 确定性候选 / 流程统计")


def _artifacts_for_validation():
    evidence = academic_evidence.build_academic_evidence(
        _state(), JOB,
        literature_sources=[{
            "source_id": "nida1964", "title": "Toward a Science of Translating",
            "authors": ["Eugene Nida"], "year": 1964,
            "source_status": "verified", "citation_allowed": True,
        }])
    research = academic_writer.build_research_model(
        evidence, "功能对等理论", {"research_questions": ["如何处理让步关系？"]})
    seg = f"seg-{JOB}-0000"
    argument = {"claims": [{
        "claim_id": "C1", "claim": "让步关系需完整表达。", "research_question": "RQ1",
        "project_evidence": [seg], "literature_evidence": ["nida1964"],
        "analysis_type": "AUTHOR_ANALYSIS", "confidence": "medium",
    }]}
    selected = {"cases": [{"case_id": seg}]}
    outline = {"sections": [
        {"section_id": "1", "title": "研究设计", "research_questions": ["RQ1"],
         "claims": ["C1"], "cases": [seg], "literature": ["nida1964"],
         "required_statistics": ["total_segments"], "minimum_chars": 20},
        {"section_id": "2", "title": "结论", "research_questions": ["RQ1"],
         "claims": ["C1"], "cases": [], "literature": [],
         "required_statistics": [], "minimum_chars": 20},
    ]}
    return evidence, research, argument, selected, outline


def test_validator_rejects_fabrication():
    evidence, research, argument, selected, outline = _artifacts_for_validation()
    expanded = academic_validator.expand_evidence_tokens(
        "理论来源为 [@nida1964]。", evidence)
    assert "<!--cite:nida1964-->" in expanded and "[@nida1964]" not in expanded
    seg = f"seg-{JOB}-0000"
    report = f"""## 1 研究设计
<!--rq:RQ1--><!--claim:C1--> 本项目共有999<!--stat:total_segments-->段 [@unknown]。Wrong (2020) [@nida1964]。
[{seg}]
> [SOURCE {seg}]: 错误引文
> [TARGET {seg}]: {evidence['project_evidence']['segments'][0]['final_target']}
[seg-{JOB}-9999] <!--term:unknown-->
"""
    result = academic_validator.validate_academic_report(
        report, evidence, research, argument, selected, outline)
    types = {x["type"] for x in result["issues"]}
    assert {"invented_segment_id", "wrong_segment_quote", "wrong_project_statistic",
            "unknown_literature_citation", "unknown_terminology_decision",
            "citation_metadata_mismatch", "missing_required_section"}.issubset(types)
    assert result["status"] == "fail"
    print("  ✓ validator 拒绝伪造段号 / 错引文 / 假统计 / 未登记术语与文献 / 缺章")


def test_dependency_staleness():
    state = _state()
    state["academic_state"] = academic_writer.default_academic_state()
    state["academic_state"]["versions"] = dict(academic_writer.VERSIONS)
    state["academic_state"]["artifacts"] = {
        name: {"file": filename, "content_hash": name, "dependency_hash": name,
               "version": "old"}
        for name, filename in academic_writer.ARTIFACT_FILES.items()
    }
    changed = dict(academic_writer.VERSIONS, writer_version="academic-writer-v2")
    academic_writer.sync_versions(state, changed)
    assert "evidence" in state["academic_state"]["artifacts"]
    assert "argument_plan" in state["academic_state"]["artifacts"]
    assert "sections" not in state["academic_state"]["artifacts"]

    state["academic_state"]["input_hash"] = "old"
    academic_writer.prepare_academic_inputs(
        state, "目的论", {"research_questions": ["新的研究问题"]}, [])
    assert "evidence" in state["academic_state"]["artifacts"]
    assert "argument_plan" not in state["academic_state"]["artifacts"]

    legacy = _state()
    legacy.update(p3_done=True, p3_md="旧四段式报告", p3_sections=[["旧章", "正文"]])
    academic_writer.prepare_academic_inputs(legacy, "目的论", {}, [])
    assert not legacy["p3_done"], "无 dependency artifact 的旧报告不得被早退复用"
    print("  ✓ writer 版本只失效正文；研究问题变化失效规划下游")


class PipelineMock:
    def __init__(self):
        self.review_calls = 0
        self.repaired_sections = []
        self.inject_fake_segment = True

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        seg = f"seg-{JOB}-0000"
        if "学术论证规划器" in system_prompt:
            return json.dumps({"claims": [{
                "claim_id": "C1", "claim": "完整表达让步关系有助于保持叙事逻辑。",
                "research_question": "RQ1", "project_evidence": [seg],
                "literature_evidence": [], "analysis_type": "AUTHOR_ANALYSIS",
                "confidence": "medium", "planned_sections": ["3"],
                "reasoning": "该案例保留初译、审校和终译。",
                "counterargument": "单个案例不能代表全书。",
            }]}, ensure_ascii=False)
        if "学术提纲规划器" in system_prompt:
            return json.dumps({"sections": [
                {"section_id": "1", "title": "研究设计", "purpose": "界定研究问题",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [],
                 "literature": [], "required_statistics": ["total_segments"],
                 "target_words": 200, "minimum_chars": 80,
                 "allowed_conclusions": ["项目内结论"]},
                {"section_id": "2", "title": "过程证据", "purpose": "分析流程",
                 "research_questions": ["RQ3"], "claims": [], "cases": [],
                 "literature": [], "required_statistics": ["tm_reuse_count"],
                 "target_words": 200, "minimum_chars": 80,
                 "allowed_conclusions": ["不外推"]},
                {"section_id": "3", "title": "案例分析", "purpose": "分析翻译决策",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [seg],
                 "literature": [], "required_statistics": [],
                 "target_words": 300, "minimum_chars": 80,
                 "allowed_conclusions": ["有限理论解释"]},
                {"section_id": "4", "title": "结论与局限", "purpose": "回答研究问题",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [],
                 "literature": [], "required_statistics": ["repaired_segments"],
                 "target_words": 200, "minimum_chars": 80,
                 "allowed_conclusions": ["不超过证据强度"]},
            ]}, ensure_ascii=False)
        if "独立的 MTI 学术审稿人" in system_prompt:
            self.review_calls += 1
            if self.review_calls == 1:
                return json.dumps({"issues": [{
                    "issue_id": "AR-1", "section_id": "2",
                    "type": "descriptive_not_analytical", "claim_id": None,
                    "evidence_ids": [], "severity": "medium",
                    "reason": "过程统计尚未解释其证据边界。",
                    "suggested_action": "补充统计只描述当前项目的限制。",
                }]}, ensure_ascii=False)
            return '{"issues":[]}'
        if "证据约束型学术写作者" in system_prompt:
            payload = json.loads(user_prompt)
            packet = payload["packet"]
            section = packet["current_section"]
            repairing = "existing_section" in payload
            if repairing:
                self.repaired_sections.append(section["section_id"])
            markers = "".join(f"<!--rq:{x}-->" for x in section["research_questions"])
            markers += "".join(f"<!--claim:{x}-->" for x in section["claims"])
            body = markers + "本节只依据已记录项目证据展开，所有解释均限定于当前任务。"
            for key in section["required_statistics"]:
                body += f"本项目相应指标为 {{{{STAT:{key}}}}}，该数字不支持总体外推。"
            for case in packet["cases"]:
                ev = case["evidence"]
                body += (f"\n[{ev['segment_id']}]\n"
                         f"> [SOURCE {ev['segment_id']}]: {ev['source']}\n"
                         f"> [TARGET {ev['segment_id']}]: {ev['final_target']}\n"
                         "从结果看，该译文可解释为对让步逻辑的显化；这属于作者分析，"
                         "并不声称还原译者的心理意图。")
            body += "该论证以证据链为边界，不把单一案例扩展为普遍规律。" * 5
            if section["section_id"] == "3" and not repairing and self.inject_fake_segment:
                body += f"\n[seg-{JOB}-9999]"
            return body
        return "{}"


def test_end_to_end_pipeline_and_targeted_repair():
    tmp = Path(tempfile.mkdtemp(prefix="academic-pipeline-"))
    try:
        state = _state()
        mock = PipelineMock()
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "DeepSeek", "key", "model", tmp,
            mock, lambda current: None, auto_repair_rounds=1)
        required = set(academic_writer.ARTIFACT_FILES.values()) | {
            "academic-evidence-warnings.md"}
        assert required.issubset({x.name for x in tmp.iterdir()})
        assert state["p3_done"] and state["academic_state"]["quality_status"] == \
            "pass_with_warnings"
        initial = state["academic_state"]["validation_history"][0]
        final = state["academic_state"]["validation_history"][-1]
        assert any(x["type"] == "invented_segment_id" for x in initial["issues"])
        assert final["status"] == "pass"
        assert set(mock.repaired_sections) == {"2", "3"}

        outline = json.loads((tmp / "academic-outline.json").read_text())
        argument = json.loads((tmp / "argument-plan.json").read_text())
        evidence = json.loads((tmp / "academic-evidence.json").read_text())
        section3 = next(x for x in outline["sections"] if x["section_id"] == "3")
        claim = next(x for x in argument["claims"] if x["claim_id"] in section3["claims"])
        case_id = section3["cases"][0]
        assert case_id in claim["project_evidence"]
        assert case_id in academic_evidence.segment_index(evidence)
        doc = Document(io.BytesIO(core.markdown_to_word(
            state["p3_md"], "目的论").getvalue()))
        doc_text = "\n".join(p.text for p in doc.paragraphs)
        assert "<!--claim:" not in doc_text and "<!--stat:" not in doc_text

        old_dependencies = {
            name: state["academic_state"]["artifacts"][name]["dependency_hash"]
            for name in ("evidence", "argument_plan", "sections")}
        state["pairs"][0]["target"] += "（人工更新）"
        mock.inject_fake_segment = False
        mock.review_calls = 1
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "DeepSeek", "key", "model", tmp,
            mock, lambda current: None, auto_repair_rounds=0)
        for name in old_dependencies:
            assert state["academic_state"]["artifacts"][name]["dependency_hash"] != \
                old_dependencies[name], f"翻译证据变化应失效 {name}"
        print("  ✓ mock E2E：证据→论点→案例→提纲→写作→验证→审稿→定点修订")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("学术写作架构测试：")
    test_whole_corpus_evidence_and_candidates()
    test_validator_rejects_fabrication()
    test_dependency_staleness()
    test_end_to_end_pipeline_and_targeted_repair()
    print("\n全部通过 ✅")
