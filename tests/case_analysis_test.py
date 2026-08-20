"""Case analysis depth, evidence adequacy and reasoning repair tests.

Run: .venv/bin/python tests/case_analysis_test.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import academic_evidence, academic_quality, academic_writer
from transpraxis import case_analysis
from tests.academic_writing_test import JOB, _state


def _segment(index: int, *, changed: bool = True, findings=True,
             repair=True, terms=("t1",)):
    source = (f"Segment {index} contains a long clause with a difficult "
              "reference that must be resolved carefully.")
    initial = f"第{index}段初译版本，处理方式较为直接。"
    final = f"第{index}段终译版本，采用更明确的指称表达。"
    if not changed:
        final = initial
    process = {
        "findings": ([{"segment_index": index, "severity": "actionable",
                       "type": "review", "reason": "指称不清",
                       "suggested_target": final}] if findings else []),
        "repair_history": [{"segment_index": index}] if repair else [],
        "injected_glossary_entry_ids": list(terms),
    }
    return {
        "segment_id": f"seg-{JOB}-{index:04d}", "segment_index": index,
        "source": source, "initial_target": initial, "final_target": final,
        "reviewed": True, "from_tm": False, "glossary_entry_ids": list(terms),
        "process_evidence": process,
    }


def test_translation_delta_and_adequacy():
    changed = _segment(0, changed=True, findings=True, repair=True)
    unchanged = _segment(1, changed=False, findings=False, repair=False, terms=())
    delta = case_analysis.translation_delta(changed)
    assert delta["available"] and delta["changed"]
    assert delta["lexical_changes"] or delta["structural_changes"]
    assert delta["finding_link"] and delta["repair_link"]
    assert case_analysis.translation_delta(unchanged)["unchanged"]

    rich = case_analysis.evidence_adequacy(changed)
    assert rich["evidence_level"] == "rich_process_evidence"
    assert "revision_reasoning" in rich["can_support"]
    assert "historical_revision_reasoning" not in rich["cannot_support"]
    poor = case_analysis.evidence_adequacy(unchanged)
    assert poor["evidence_level"] == "source_final_only"
    assert "process_claims" in poor["cannot_support"]
    print("  ✓ translation_delta 与 evidence_adequacy 分类")


def test_weak_analysis_diagnostics():
    label_only = "本例采用了意译策略，使译文更加自然。"
    assert case_analysis.detect_strategy_label_without_mechanism(label_only)
    assert not case_analysis.detect_strategy_label_without_mechanism(
        "本例采用意译，因为直译会破坏指称的清晰性，改为显化指称后读者无需回读。")
    assert case_analysis.detect_unsupported_quality_effect(
        "该策略有效提升了译文的准确性和可读性。")
    assert not case_analysis.detect_unsupported_quality_effect(
        "该处理提升了指称的清晰性：终译显化了先行词，读者无需回读。")
    assert case_analysis.detect_unsupported_process_claim(
        "译者最初考虑直译，后来改为意译。")
    assert case_analysis.detect_case_to_general_rule_overreach(
        "因此，在文学翻译中应当灵活采用意译策略。")
    assert not case_analysis.detect_case_to_general_rule_overreach(
        "在该案例中，重组从句使因果逻辑显化，同时保留了叙述节奏。")
    print("  ✓ 策略标签/空泛效果/伪造过程/过度外推确定性诊断")


def _quality_inputs_with_case(segment):
    evidence = academic_evidence.build_academic_evidence(_state(), JOB)
    evidence["project_evidence"]["segments"] = [segment]
    evidence["candidate_cases"] = [{
        "case_id": segment["segment_id"], "coverage_zone": "beginning",
        "score": 10, "reasons": ["fixture"]}]
    research = academic_writer.build_research_model(
        evidence, "目的论", {"research_questions": ["如何处理指称？"]})
    argument = {"claims": [{
        "claim_id": "C1", "claim": "指称处理需考虑读者理解。",
        "research_question": "RQ1", "project_evidence": [segment["segment_id"]],
        "literature_claims": [], "literature_evidence": [],
        "support_category": "project_evidence_only",
        "analysis_type": "AUTHOR_ANALYSIS", "confidence": "medium",
    }]}
    selected = {"cases": [{
        "case_id": segment["segment_id"], "supports_claims": ["C1"],
        "research_questions": ["RQ1"], "selection_rationale": "fixture",
    }]}
    outline = {"sections": [{
        "section_id": "3", "title": "案例分析", "research_questions": ["RQ1"],
        "claims": ["C1"], "cases": [segment["segment_id"]],
        "literature_claims": [], "literature_evidence": [],
        "literature_sources": [], "required_statistics": [],
        "minimum_chars": 20,
    }]}
    return evidence, research, argument, selected, outline


class DepthMock:
    def __init__(self, depth: dict):
        self.depth = depth

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        return json.dumps({"dimensions": {}, "findings": [],
                           "case_analysis_depth": self.depth},
                          ensure_ascii=False)


def test_depth_evaluation_and_vacuous_gaming():
    segment = _segment(3, changed=True, findings=True, repair=True)
    evidence, research, argument, selected, outline = _quality_inputs_with_case(segment)
    case_id = segment["segment_id"]
    sections = [{"section_id": "3", "title": "案例分析",
                 "content": f"<!--rq:RQ1--><!--claim:C1-->\n[{case_id}]\n"
                            "> [SOURCE %s]: %s\n> [TARGET %s]: %s\n"
                            "问题：源文指称悬空；初译未显化；终译显化先行词。"
                            "理由：显化后读者无需回读。效果：指称清晰性。"
                            "结论限于本案例。"
                            % (case_id, segment["source"], case_id, segment["final_target"]),
                 "provenance": {}}]
    depth = {case_id: {d: {"status": "strong" if d != "theory_mapping" else "not_applicable",
                           "reason": "具体证据链完整"}
                       for d in case_analysis.DEPTH_DIMENSIONS}}
    quality = academic_quality.evaluate_quality(
        research, argument, selected, outline, sections, evidence, {}, {}, {},
        {"status": "pass"}, DepthMock(depth), "x", "x", "x")
    summary = quality["metrics"]["case_analysis_depth_summary"]
    assert summary["problem_definition"]["strong"] == 1
    assert summary["theory_mapping"]["not_applicable"] == 1

    vacuous = {case_id: {d: {"status": "weak",
                             "reason": "包含所有标题但无具体文本特征与证据"}
                         for d in case_analysis.DEPTH_DIMENSIONS}}
    quality2 = academic_quality.evaluate_quality(
        research, argument, selected, outline, sections, evidence, {}, {}, {},
        {"status": "pass"}, DepthMock(vacuous), "x", "x", "x")
    assert quality2["metrics"]["case_analysis_depth_summary"]["decision_rationale"]["weak"] == 1
    print("  ✓ 深度评估与空洞游戏化判 weak")


class AnalysisPlannerMock:
    def __init__(self, plan):
        self.plan = plan

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        if "案例分析规划器" in system_prompt:
            return json.dumps({"plans": [self.plan]}, ensure_ascii=False)
        return "{}"


def test_evidence_poor_plan_downgrade():
    segment = _segment(4, changed=False, findings=False, repair=False, terms=())
    evidence, research, argument, selected, outline = _quality_inputs_with_case(segment)
    plan = {
        "case_id": segment["segment_id"],
        "problem": {"type": "reference_resolution", "statement": "指称需显化。",
                    "grounded": True},
        "initial_failure": {"description": "初译失败因为直译。", "type": "error"},
        "alternatives": [{"label": "historical_alternative", "text": "译者曾考虑直译。"}],
        "decision_rationale": "显化更清晰。",
        "translation_effect": {"dimension": "reference_clarity",
                               "demonstrated_by": "终译显化先行词"},
        "theory_mapping": None,
        "bounded_conclusion": "本案例显化指称有效。",
        "recommended_human_evidence": ["需要译者解释或原稿历史"],
    }
    plans = case_analysis.build_case_analysis_plans(
        evidence, selected, argument, {"items": []},
        AnalysisPlannerMock(plan), "x", "x", "x")
    item = plans["plans"][0]
    assert item["evidence_level"] == "source_final_only"
    assert item["problem"]["grounded"] is False
    assert item["initial_failure"] is None
    assert item["alternatives"][0]["label"] == "analytical_comparison"
    assert item["theory_connection_status"] == "not_applicable"
    assert item["recommended_human_evidence"]
    print("  ✓ 证据贫乏案例：grounded 降级、历史备选降级、人工证据建议")


class ReasoningRepairMock:
    def __init__(self):
        self.rewritten = []

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        case_id = f"seg-{JOB}-0000"
        if "案例分析规划器" in system_prompt:
            return json.dumps({"plans": [{
                "case_id": case_id,
                "problem": {"type": "reference_resolution",
                            "statement": "源文指称悬空，直译导致读者无法确定先行词。",
                            "grounded": True},
                "initial_failure": {"description": "初译未显化先行词。"},
                "alternatives": [{"label": "counterfactual_rendering",
                                  "text": "若直译则先行词悬空。"}],
                "decision_rationale": "终译显化先行词，消除回读。",
                "translation_effect": {"dimension": "reference_clarity",
                                       "demonstrated_by": "终译补充先行词"},
                "theory_mapping": None,
                "bounded_conclusion": "本案例的显化处理提升指称清晰性。",
                "recommended_human_evidence": [],
            }]}, ensure_ascii=False)
        if "学术论证规划器" in system_prompt:
            return json.dumps({"claims": [{
                "claim_id": "C1", "claim": "指称处理需考虑读者理解。",
                "research_question": "RQ1", "project_evidence": [case_id],
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
                 "required_statistics": ["total_segments"], "target_words": 100,
                 "minimum_chars": 40, "allowed_conclusions": ["项目内"]},
                {"section_id": "3", "title": "案例分析", "purpose": "fixture",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [case_id],
                 "literature_claims": [], "literature_evidence": [],
                 "required_statistics": [], "target_words": 200,
                 "minimum_chars": 60, "allowed_conclusions": ["有限解释"]},
                {"section_id": "5", "title": "结论", "purpose": "fixture",
                 "research_questions": ["RQ1"], "claims": ["C1"], "cases": [],
                 "literature_claims": [], "literature_evidence": [],
                 "required_statistics": [], "target_words": 100,
                 "minimum_chars": 40, "allowed_conclusions": ["不超证据"]},
            ]}, ensure_ascii=False)
        if "学术质量审稿人" in system_prompt:
            return json.dumps({"dimensions": {}, "findings": [],
                               "case_analysis_depth": {case_id: {
                                   "problem_definition": {"status": "adequate",
                                                          "reason": "问题具体"},
                                   "evidence_use": {"status": "adequate",
                                                    "reason": "使用引文与 finding"},
                                   "initial_failure_or_alternative": {
                                       "status": "adequate", "reason": "有备选标注"},
                                   "decision_rationale": {"status": "adequate",
                                                          "reason": "理由具体"},
                                   "translation_effect": {"status": "adequate",
                                                          "reason": "维度明确"},
                                   "theory_mapping": {"status": "not_applicable",
                                                      "reason": "无文献"},
                                   "bounded_conclusion": {"status": "strong",
                                                          "reason": "限定本案例"},
                               }}}, ensure_ascii=False)
        if "证据约束型学术写作者" in system_prompt:
            payload = json.loads(user_prompt)
            packet = payload["packet"]
            section = packet["current_section"]
            self.rewritten.append(("repair" if "existing_section" in payload else "write",
                                   section["section_id"]))
            analyses = payload["packet"].get("case_analyses") or []
            body = "".join(f"<!--rq:{x}-->" for x in section["research_questions"])
            body += "".join(f"<!--claim:{x}-->" for x in section["claims"])
            body += "\n" + "\n".join(
                f"{x['markdown_prefix']} {x['heading_id']} {x['title']}\n本小节按学院框架展开。"
                for x in (packet.get("writing_constraints") or {}).get(
                    "required_subsections", []))
            for analysis in analyses:
                problem = analysis.get("problem", {})
                body += (f"\n问题：{problem.get('statement', '')}\n"
                         f"[{case_id}]\n> [SOURCE {case_id}]: "
                         f"{payload['packet']['cases'][0]['evidence']['source']}\n"
                         f"> [TARGET {case_id}]: "
                         f"{payload['packet']['cases'][0]['evidence']['final_target']}\n"
                         "初译未显化先行词；终译显化后读者无需回读。"
                         "（反事实对比：若直译则先行词悬空。）"
                         "效果维度：指称清晰性。结论限于本案例。")
            body += "该论证以证据链为边界。" * 4
            return body
        return "{}"


def test_reasoning_repair_end_to_end():
    tmp = Path(tempfile.mkdtemp(prefix="case-analysis-e2e-"))
    try:
        state = _state()
        mock = ReasoningRepairMock()
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "x", "x", "x", tmp,
            mock, lambda current: None,
            research_settings={"research_questions": ["如何处理指称？"]},
            auto_repair_rounds=0, auto_quality_repair_rounds=1)
        assert state["p3_done"]
        assert (tmp / "case-analysis-plans.json").is_file()
        plans = json.loads((tmp / "case-analysis-plans.json").read_text(encoding="utf-8"))
        assert plans["plans"][0]["problem"]["grounded"]
        assert plans["plans"][0]["bounded_conclusion"]
        quality = json.loads((tmp / "academic-quality-evaluation.json").read_text(
            encoding="utf-8"))
        depth = quality["diagnostics"]["case_analysis_depth"]
        case_id = f"seg-{JOB}-0000"
        assert case_id in depth
        assert depth[case_id]["bounded_conclusion"]["status"] == "strong"
        report = state["p3_md"]
        assert "反事实对比" in report and "结论限于本案例" in report
        assert "译者最初" not in report
        print("  ✓ 推理修复端到端：规划→受约束写作→深度评估→复评")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("案例分析推理测试：")
    test_translation_delta_and_adequacy()
    test_weak_analysis_diagnostics()
    test_depth_evaluation_and_vacuous_gaming()
    test_evidence_poor_plan_downgrade()
    test_reasoning_repair_end_to_end()
    print("\n全部通过 ✅")
