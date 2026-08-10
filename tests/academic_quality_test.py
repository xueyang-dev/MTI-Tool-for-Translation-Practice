"""Academic quality evaluation and structural repair tests.

Run: .venv/bin/python tests/academic_quality_test.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence, academic_quality, academic_writer
from mti_tool import literature_evidence
from tests.academic_writing_test import JOB, _state


def _findings_for(segment_index: int, severity: str = "actionable") -> list:
    return [{"segment_index": segment_index, "severity": severity,
             "type": "review", "reason": "测试 finding"}]


def _segment(segment_id: str, source: str, target: str, *, findings=None,
             initial=None, terms=(), reviewed=True):
    return {
        "segment_id": segment_id, "source": source, "target": target,
        "initial_target": initial if initial is not None else target,
        "final_target": target, "reviewed": reviewed, "from_tm": False,
        "glossary_entry_ids": list(terms), "process_evidence": {
            "findings": findings or [], "repair_history": bool(initial and initial != target),
            "injected_glossary_entry_ids": list(terms),
        },
    }


def test_case_classification():
    strong = _segment("seg-s-0000", "long source with a real problem", "终译",
                      findings=_findings_for(0), initial="初译", terms=("t1",))
    weak = _segment("seg-s-0001", "A short sentence.", "短句。", findings=[])
    assert academic_quality.classify_case(
        {"case_id": strong["segment_id"]}, strong, _findings_for(0),
        [strong["segment_id"]])[0] == "strong_case"
    cls, reasons = academic_quality.classify_case(
        {"case_id": weak["segment_id"]}, weak, [], [weak["segment_id"]])
    assert cls == "weak_case" and reasons
    misaligned = academic_quality.classify_case(
        {"case_id": strong["segment_id"]}, strong, _findings_for(0), ["other"])
    assert misaligned[0] == "misaligned_case"
    print("  ✓ 案例分类：strong/weak/misaligned")


def test_paragraph_roles_and_generic():
    assert academic_quality.classify_paragraph(
        "<!--claim:C1--> 本论点有证据支持。") == "claim"
    assert academic_quality.classify_paragraph(
        "> [SOURCE seg-x-0000]: exact quote\n[seg-x-0000]") == "evidence"
    assert academic_quality.classify_paragraph(
        "通过本次翻译实践，笔者深刻认识到翻译的复杂性。") == "generic"
    assert academic_quality.classify_paragraph(
        "从结果看可解释为对让步关系的显化，这不同于简单直译。") == "analysis"
    stats = academic_quality.paragraph_statistics([
        {"section_id": "1", "content": "<!--claim:C1--> 论点。\n\n从结果看可解释为分析。"},
        {"section_id": "2", "content": "通过本次翻译实践，笔者深刻认识到……"},
    ])
    assert stats["claim_bearing_paragraphs"] == 1
    assert stats["analysis_bearing_paragraphs"] == 1
    assert stats["generic_paragraphs"] == 1
    assert stats["generic_rate"] == round(1 / 3, 3)
    print("  ✓ 段落角色统计与高度泛化散文检测")


def test_rq_alignment():
    research = {"research_questions": [
        {"rq_id": "RQ1", "question": "如何解释？"},
        {"rq_id": "RQ2", "question": "未被回答的问题？"},
    ]}
    argument = {"claims": [
        {"claim_id": "C1", "research_question": "RQ1", "project_evidence": []},
        {"claim_id": "C2", "research_question": "RQ1", "project_evidence": []},
    ]}
    selected = {"cases": []}
    outline = {"sections": [
        {"section_id": "1", "title": "分析", "research_questions": ["RQ1"],
         "claims": ["C1"], "cases": []},
        {"section_id": "2", "title": "结论", "research_questions": [], "claims": [], "cases": []},
    ]}
    matrix = academic_quality.build_rq_matrix(research, argument, selected, outline)
    assert matrix["unanswered_rqs"] == ["RQ2"]
    assert matrix["orphan_claims"] == ["C2"]
    assert matrix["sections_without_rq"] == ["2"]
    print("  ✓ RQ 对齐：未回答 RQ / 孤立 claim / 无 RQ 章节")


def test_evidence_utilization_and_cross_section():
    case = {"case_id": "seg-s-0000"}
    selected = {"cases": [case]}
    evidence = {"candidate_cases": [], "findings": _findings_for(0),
                "project_evidence": {"segments": [
                    _segment("seg-s-0000", "src", "终译", findings=_findings_for(0),
                             initial="初译", terms=("t1",))],
                    "statistics": {}}}
    sections = [{"section_id": "3", "content": "正文没有引用任何案例。"}]
    usage = academic_quality.evidence_utilization(sections, selected, evidence)
    assert usage["high_value_unused_cases"] == ["seg-s-0000"]
    issues = academic_quality.cross_section_checks([
        {"section_id": "1", "content": "同一段落文本。\n\n[seg-s-0000] 案例一。"},
        {"section_id": "2", "content": "同一段落文本。\n\n[seg-s-0000] 案例二。"},
    ])
    types = {x["type"] for x in issues}
    assert {"duplicate_paragraph", "duplicate_case_analysis"}.issubset(types)
    print("  ✓ 证据利用缺失检测与跨节重复检测")


def _quality_inputs(weak_case: str, strong_case: str):
    state = _state()
    evidence = academic_evidence.build_academic_evidence(state, JOB, max_candidates=9)
    research = academic_writer.build_research_model(
        evidence, "目的论", {"research_questions": ["如何处理让步关系？"]})
    argument = {"claims": [{
        "claim_id": "C1", "claim": "让步关系需完整表达。", "research_question": "RQ1",
        "project_evidence": [weak_case], "literature_claims": [],
        "literature_evidence": [], "support_category": "project_evidence_only",
        "analysis_type": "AUTHOR_ANALYSIS", "confidence": "medium",
    }]}
    selected = {"cases": [{
        "case_id": weak_case, "supports_claims": ["C1"],
        "research_questions": ["RQ1"], "selection_rationale": "fixture",
    }]}
    outline = {"sections": [
        {"section_id": "1", "title": "研究设计", "research_questions": ["RQ1"],
         "claims": ["C1"], "cases": [weak_case], "literature_claims": [],
         "literature_evidence": [], "literature_sources": [],
         "required_statistics": ["total_segments"], "minimum_chars": 60},
        {"section_id": "4", "title": "结论", "research_questions": ["RQ1"],
         "claims": ["C1"], "cases": [], "literature_claims": [],
         "literature_evidence": [], "literature_sources": [],
         "required_statistics": [], "minimum_chars": 60},
    ]}
    sections = [
        {"section_id": "1", "title": "研究设计",
         "content": "<!--rq:RQ1--><!--claim:C1-->\n\n" + f"[{weak_case}] 案例正文。\n\n"
                    "从结果看可解释为项目内现象。", "provenance": {}},
        {"section_id": "4", "title": "结论",
         "content": "<!--rq:RQ1--><!--claim:C1-->\n\n结论限于项目证据。", "provenance": {}},
    ]
    return evidence, research, argument, selected, outline, sections


def test_replacement_selection():
    weak = f"seg-{JOB}-0001"
    strong = f"seg-{JOB}-0006"
    evidence, research, argument, selected, outline, sections = _quality_inputs(weak, strong)
    replacement = academic_quality.select_replacement_case(
        weak, ["C1"], selected, argument, evidence)
    assert replacement is not None and replacement["case_id"] != weak
    updated_selected, updated_argument, updated_outline, performed = \
        academic_writer._apply_case_replacements(
            [{"issue_id": "AQ-001", "case_id": weak, "section_id": "1", "reason": "弱案例"}],
            selected, argument, outline, evidence)
    assert performed and performed[0]["new_case_id"] == replacement["case_id"]
    assert updated_selected["cases"][0]["case_id"] == replacement["case_id"]
    assert replacement["case_id"] in updated_argument["claims"][0]["project_evidence"]
    assert replacement["case_id"] in updated_outline["sections"][0]["cases"]
    assert updated_outline["sections"][0]["cases"] != [weak]
    print("  ✓ 弱案例替换：候选选择 + 计划/提纲/案例传播")


def test_replacement_prefers_evidence_richness_over_mining_score():
    weak = f"seg-{JOB}-0001"
    evidence, research, argument, selected, outline, sections = _quality_inputs(weak, None)
    rich = f"seg-{JOB}-0006"
    poor = f"seg-{JOB}-0002"
    # Give the poor candidate the highest mining score but zero evidence.
    evidence["candidate_cases"] = [
        {"case_id": poor, "coverage_zone": "middle", "score": 99, "reasons": ["RQ1"]},
        {"case_id": rich, "coverage_zone": "end", "score": 1, "reasons": ["RQ1"]},
    ]
    replacement = academic_quality.select_replacement_case(
        weak, ["C1"], selected, argument, evidence)
    assert replacement["case_id"] == rich
    print("  ✓ 替换选择优先证据丰富度而非挖掘分数")


class QualityPipelineMock:
    def __init__(self):
        self.review_calls = 0
        self.written_sections = []
        self.weak_case = f"seg-{JOB}-0001"

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        weak = f"seg-{JOB}-0001"
        if "学术论证规划器" in system_prompt:
            return json.dumps({"claims": [{
                "claim_id": "C1", "claim": "让步关系需完整表达。",
                "research_question": "RQ1", "project_evidence": [weak],
                "literature_claims": [], "literature_evidence": [],
                "support_category": "project_evidence_only",
                "analysis_type": "AUTHOR_ANALYSIS", "confidence": "medium",
                "planned_sections": ["3"], "reasoning": "fixture",
                "counterargument": "fixture",
            }]}, ensure_ascii=False)
        if "学术提纲规划器" in system_prompt:
            return json.dumps({"sections": [
                {"section_id": "1", "title": "研究设计", "purpose": "fixture",
                 "research_questions": ["RQ1"], "claims": [], "cases": [],
                 "literature_claims": [], "literature_evidence": [],
                 "required_statistics": ["total_segments"], "target_words": 200,
                 "minimum_chars": 80, "allowed_conclusions": ["项目内"]},
                {"section_id": "3", "title": "案例分析", "purpose": "fixture",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [weak],
                 "literature_claims": [], "literature_evidence": [],
                 "required_statistics": [], "target_words": 300,
                 "minimum_chars": 80, "allowed_conclusions": ["有限解释"]},
                {"section_id": "4", "title": "结论", "purpose": "fixture",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [],
                 "literature_claims": [], "literature_evidence": [],
                 "required_statistics": ["repaired_segments"], "target_words": 200,
                 "minimum_chars": 80, "allowed_conclusions": ["不超证据"]},
            ]}, ensure_ascii=False)
        if "独立的 MTI 学术审稿人" in system_prompt:
            return '{"issues":[]}'
        if "Literature Support Reviewer" in system_prompt:
            return '{"issues":[]}'
        if "学术质量审稿人" in system_prompt:
            self.review_calls += 1
            if self.review_calls == 1:
                return json.dumps({
                    "dimensions": {"case_quality": "review_required"},
                    "findings": [{
                        "type": "weak_case", "dimension": "case_quality",
                        "section_id": None, "claim_id": "C1",
                        "case_id": self.weak_case, "severity": "medium",
                        "priority": "P2", "evidence": "",
                        "reason": "fixture：该案例缺少真实翻译问题证据。",
                        "recommended_action": "替换为证据更丰富的候选。",
                        "repair_action": "replace_case",
                    }],
                }, ensure_ascii=False)
            return '{"dimensions":{},"findings":[]}'
        if "证据约束型学术写作者" in system_prompt:
            payload = json.loads(user_prompt)
            packet = payload["packet"]
            section = packet["current_section"]
            self.written_sections.append(section["section_id"])
            body = "".join(f"<!--rq:{x}-->" for x in section["research_questions"])
            body += "".join(f"<!--claim:{x}-->" for x in section["claims"])
            for case in packet["cases"]:
                ev = case.get("evidence") or {}
                body += (f"\n[{ev.get('segment_id', case['case_id'])}]\n"
                         f"> [SOURCE {ev.get('segment_id', case['case_id'])}]: "
                         f"{ev.get('source', 'source')}\n"
                         f"> [TARGET {ev.get('segment_id', case['case_id'])}]: "
                         f"{ev.get('final_target', 'target')}\n"
                         "从结果看，该译文可解释为对逻辑关系的显化；这属于作者分析。")
            body += "该论证以证据链为边界。" * 4
            return body
        return "{}"


def test_end_to_end_quality_repair_with_case_replacement():
    tmp = Path(tempfile.mkdtemp(prefix="academic-quality-e2e-"))
    try:
        state = _state()
        # Make the weak case genuinely weak (no terms, no initial/final
        # difference) so the replacement selector must pick a richer candidate.
        state["pairs"][1]["glossary_entry_ids"] = []
        state["pairs"][1]["initial_target"] = state["pairs"][1]["target"]
        mock = QualityPipelineMock()
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "DeepSeek", "key", "model", tmp,
            mock, lambda current: None,
            research_settings={"research_questions": ["如何处理让步关系？"]},
            auto_repair_rounds=0, auto_quality_repair_rounds=1)
        assert state["p3_done"]
        quality_history = state["academic_state"]["academic_quality_history"]
        assert len(quality_history) >= 2, "质量修复轮应重新评估"
        assert quality_history[-1]["metrics"]["weak_cases"] == 0
        repair_artifact = academic_writer._read_artifact(
            tmp / "academic-quality-repair-history.json")
        assert repair_artifact["rounds"]
        replacement = repair_artifact["rounds"][0]["case_replacements"][0]
        assert replacement["old_case_id"] == f"seg-{JOB}-0001"
        assert replacement["new_case_id"] != replacement["old_case_id"]
        selected = academic_writer._read_artifact(tmp / "selected-cases.json")
        assert selected["cases"][0]["case_id"] == replacement["new_case_id"]
        assert replacement["new_case_id"] in state["p3_md"]
        assert replacement["old_case_id"] not in state["p3_md"]
        assert (tmp / "academic-quality-evaluation.json").is_file()
        assert (tmp / "academic-quality-report.md").is_file()
        assert (tmp / "academic-quality-findings.jsonl").is_file()
        assert "academic_quality_status" in state["academic_state"]
        print("  ✓ 端到端：质量审查发现弱案例 → 案例替换 → 重写 → 复评改善")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("学术质量测试：")
    test_case_classification()
    test_paragraph_roles_and_generic()
    test_rq_alignment()
    test_evidence_utilization_and_cross_section()
    test_replacement_selection()
    test_replacement_prefers_evidence_richness_over_mining_score()
    test_end_to_end_quality_repair_with_case_replacement()
    print("\n全部通过 ✅")
