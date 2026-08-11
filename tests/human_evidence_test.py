"""Human evidence intake tests: needs, questions, answers, staleness, writer.

Run: .venv/bin/python tests/human_evidence_test.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence, academic_writer
from mti_tool import case_analysis, human_evidence
from tests.academic_writing_test import JOB, _state


def _weak_case_segment():
    return {
        "segment_id": f"seg-{JOB}-0138", "segment_index": 138,
        "source": "He never mentioned the accident again.",
        "initial_target": "他从未再提及那次事故。",
        "final_target": "他再也没有提起那次事故。",
        "reviewed": True, "from_tm": False, "glossary_entry_ids": [],
        "process_evidence": {"findings": [], "repair_history": [],
                             "injected_glossary_entry_ids": []},
    }


def _weak_case_plans(evidence):
    segment = _weak_case_segment()
    evidence["project_evidence"]["segments"] = [segment]
    evidence["candidate_cases"] = [{
        "case_id": segment["segment_id"], "coverage_zone": "beginning",
        "score": 1, "reasons": []}]
    selected = {"cases": [{
        "case_id": segment["segment_id"], "supports_claims": ["C1"],
        "research_questions": ["RQ1"], "selection_rationale": "fixture"}]}
    argument = {"claims": [{
        "claim_id": "C1", "claim": "该案例可作有限文本分析。",
        "research_question": "RQ1", "project_evidence": [segment["segment_id"]],
        "literature_claims": [], "literature_evidence": [],
        "human_author_evidence": [],
        "support_category": "project_evidence_only",
        "analysis_type": "AUTHOR_ANALYSIS", "confidence": "low",
    }]}
    plans = case_analysis.build_case_analysis_plans(
        evidence, selected, argument, {"items": []},
        lambda *a, **k: "{}", "x", "x", "x")
    return segment, selected, argument, plans


def test_needs_and_questions():
    evidence = academic_evidence.build_academic_evidence(_state(), JOB)
    segment, selected, argument, plans = _weak_case_plans(evidence)
    needs = human_evidence.build_evidence_needs(evidence, plans)
    assert needs["needs"], "弱案例应产生证据需求"
    need = needs["needs"][0]
    assert need["case_id"] == segment["segment_id"]
    assert need["recoverability"] == "human_recoverable"
    assert need["academic_value"] in ("critical", "high", "medium", "low")
    assert need["affected_dimensions"]
    questions = human_evidence.generate_questions(needs, evidence, plans)
    assert questions["questions"]
    question = questions["questions"][0]
    assert "为什么" in question["question"] or "考虑" in question["question"]
    assert question["context"]["source"] and question["context"]["final_target"]
    # Dedup: same case + type yields one question.
    same_type = [q for q in questions["questions"]
                 if q["question_type"] == question["question_type"]]
    assert len(same_type) == 1
    print("  ✓ 需求生成/可恢复性/问题具体性/去重")


def test_answer_recording_statuses():
    evidence = academic_evidence.build_academic_evidence(_state(), JOB)
    segment, selected, argument, plans = _weak_case_plans(evidence)
    needs = human_evidence.build_evidence_needs(evidence, plans)
    questions = human_evidence.generate_questions(needs, evidence, plans)
    q = questions["questions"][0]

    entry, updated = human_evidence.record_human_answer(
        questions, q["question_id"],
        "我选这个译法是因为直译会让叙述者显得过于正式，"
        "而周围段落都是口语化叙述。", evidence)
    assert entry["status"] == "user_confirmed"
    assert entry["provenance"]["type"] == "user_answer"
    assert entry["provenance"]["interface"] == "academic_workspace"
    assert entry["answer"].startswith("我选这个译法")
    assert entry["content_hash"]
    assert updated["questions"][0]["status"] == "answered"

    entry2, _ = human_evidence.record_human_answer(
        questions, q["question_id"], "不记得了。", evidence)
    assert entry2["status"] == "unavailable_after_human_check"

    # Contradiction: user claims an initial version that differs from record.
    evidence2 = academic_evidence.build_academic_evidence(_state(), JOB)
    seg0 = evidence2["project_evidence"]["segments"][0]
    stored_initial = seg0["initial_target"]
    assert stored_initial
    conflicting = {"questions": [{
        "question_id": "HQ-0001", "question_type": "initial_translation_missing",
        "question": "初译是什么？", "case_id": seg0["segment_id"],
        "segment_ids": [seg0["segment_id"]], "status": "open",
        "context": {}, "priority": "high", "need_ids": ["HN-1"]}]}
    entry3, _ = human_evidence.record_human_answer(
        conflicting, "HQ-0001",
        "初译是“一个与记录完全不同的版本。”", evidence2)
    assert entry3["status"] == "conflicted"
    assert entry3["conflict_status"] == "contradicted"
    print("  ✓ 答案摄入/不知道/矛盾检测")


def test_capability_upgrade_and_scope():
    segment = _weak_case_segment()
    adequacy = case_analysis.evidence_adequacy(segment)
    assert adequacy["capabilities"]["has_meaningful_revision"]
    assert "translator_rationale" not in adequacy["can_support"]
    entry = {
        "human_evidence_id": "HE-0001", "case_id": segment["segment_id"],
        "question_type": "translator_rationale", "status": "user_confirmed",
        "conflict_status": "consistent", "answer": "因为直译太正式。",
    }
    upgraded = human_evidence.case_capabilities(
        segment["segment_id"], [entry], adequacy)
    assert "translator_rationale" in upgraded["can_support"]
    assert upgraded["capabilities"]["has_revision_rationale"]
    # Scope: evidence for another case does not upgrade this one.
    other = {**entry, "case_id": f"seg-{JOB}-9999"}
    unchanged = human_evidence.case_capabilities(
        segment["segment_id"], [other], adequacy)
    assert not unchanged["capabilities"]["has_revision_rationale"]

    # Human evidence cannot turn an unchanged segment into a revision case.
    non_revision = {**segment, "initial_target": segment["final_target"]}
    non_revision_adequacy = case_analysis.evidence_adequacy(non_revision)
    blocked = human_evidence.case_capabilities(
        segment["segment_id"], [entry], non_revision_adequacy)
    assert blocked["case_role"] == "non_revision_case"
    assert not blocked["capabilities"]["has_meaningful_revision"]
    assert "translator_rationale" not in blocked["can_support"]
    print("  ✓ 能力升级与 case 范围约束")


class HumanEvidencePipelineMock:
    def __init__(self):
        self.rewritten_sections = []
        self.human_answer = ("我选这个译法是因为直译会让叙述者显得过于正式，"
                             "而周围段落是口语化叙述。")

    def __call__(self, provider, api_key, model, system_prompt, user_prompt,
                 temperature=0.1):
        case_id = f"seg-{JOB}-0001"
        if "学术论证规划器" in system_prompt:
            return json.dumps({"claims": [{
                "claim_id": "C1", "claim": "指称处理需考虑读者理解。",
                "research_question": "RQ1", "project_evidence": [case_id],
                "literature_claims": [], "literature_evidence": [],
                "human_author_evidence": [], "support_category": "project_evidence_only",
                "analysis_type": "AUTHOR_ANALYSIS", "confidence": "medium",
                "planned_sections": ["3"], "reasoning": "fixture",
                "counterargument": "fixture",
            }]}, ensure_ascii=False)
        if "案例分析规划器" in system_prompt:
            payload = json.loads(user_prompt)
            he = [x for x in payload.get("human_evidence") or []
                  if x.get("case_id") == case_id]
            return json.dumps({"plans": [{
                "case_id": case_id,
                "problem": {"type": "reference_resolution",
                            "statement": "源文指称悬空。", "grounded": True},
                "initial_failure": None,
                "alternatives": [],
                "decision_rationale": (
                    "作者后来解释："
                    + (he[0]["answer"] if he else "（暂无作者解释）")),
                "translation_effect": None,
                "theory_mapping": None,
                "bounded_conclusion": "本案例结论限于指称处理。",
                "recommended_human_evidence": [],
                "human_evidence_ids": [x["human_evidence_id"] for x in he],
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
                                                    "reason": "有证据"},
                                   "initial_failure_or_alternative": {
                                       "status": "not_applicable", "reason": ""},
                                   "decision_rationale": {"status": "adequate",
                                                          "reason": "有理由"},
                                   "translation_effect": {"status": "not_applicable",
                                                          "reason": ""},
                                   "theory_mapping": {"status": "not_applicable",
                                                      "reason": ""},
                                   "bounded_conclusion": {"status": "strong",
                                                          "reason": "限定本案例"},
                               }}}, ensure_ascii=False)
        if "证据约束型学术写作者" in system_prompt:
            payload = json.loads(user_prompt)
            section = payload["packet"]["current_section"]
            self.rewritten_sections.append(section["section_id"])
            analyses = payload["packet"].get("case_analyses") or []
            body = "".join(f"<!--rq:{x}-->" for x in section["research_questions"])
            body += "".join(f"<!--claim:{x}-->" for x in section["claims"])
            for analysis in analyses:
                he = analysis.get("human_evidence") or []
                for item in he:
                    body += f"<!--human-ev:{item['human_evidence_id']}-->"
                    body += f"作者后来解释：{item['answer']}"
                body += (f"\n[{case_id}]\n> [SOURCE {case_id}]: source\n"
                         f"> [TARGET {case_id}]: target\n"
                         "本节分析限于本案例。" * 4)
            return body
        return "{}"


def test_intake_to_targeted_regeneration():
    tmp = Path(tempfile.mkdtemp(prefix="human-evidence-e2e-"))
    try:
        state = _state()
        mock = HumanEvidencePipelineMock()
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "x", "x", "x", tmp,
            mock, lambda current: None,
            research_settings={"research_questions": ["如何处理指称？"]},
            auto_repair_rounds=0, auto_quality_repair_rounds=1)
        questions = academic_writer._read_artifact(
            tmp / "human-evidence-questions.json")
        open_questions = [
            q for q in questions["questions"]
            if q["status"] == "open" and q["case_id"] == f"seg-{JOB}-0001"]
        assert open_questions, "证据受限案例应产生待回答问题"
        question = open_questions[0]

        # Simulate the UI intake path.
        import core
        old_job_dir = core.job_dir
        core.OUTPUT_DIR = tmp.parent / "outputs-e2e"
        core.OUTPUT_DIR.mkdir(exist_ok=True)
        (core.OUTPUT_DIR / JOB).mkdir(exist_ok=True)
        # The pipeline wrote artifacts into tmp; copy them into the job dir for
        # record_human_evidence to read.
        for name, filename in academic_writer.ARTIFACT_FILES.items():
            src = tmp / filename
            if src.is_file():
                (core.OUTPUT_DIR / JOB / filename).write_bytes(src.read_bytes())
        state_path = core.OUTPUT_DIR / JOB / "state.json"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        entry = core.record_human_evidence(JOB, question["question_id"],
                                           mock.human_answer)
        assert entry["status"] == "user_confirmed"
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        assert saved["human_evidence"][-1]["human_evidence_id"] == \
            entry["human_evidence_id"]
        assert saved["human_evidence"][-1]["answer"] == mock.human_answer
        core.job_dir = old_job_dir

        # Resume: HE should invalidate case plans and only the affected section.
        state = json.loads(state_path.read_text(encoding="utf-8"))
        mock2 = HumanEvidencePipelineMock()
        mock2.rewritten_sections = []
        academic_writer.run_academic_pipeline(
            state, JOB, "目的论", "x", "x", "x", tmp,
            mock2, lambda current: None,
            research_settings={"research_questions": ["如何处理指称？"]},
            auto_repair_rounds=0, auto_quality_repair_rounds=0,
            human_evidence_sources=state.get("human_evidence"))
        plans = academic_writer._read_artifact(tmp / "case-analysis-plans.json")
        plan = next(p for p in plans["plans"] if p["case_id"] == f"seg-{JOB}-0001")
        assert plan["human_evidence_ids"], "规划应引用可用人类证据"
        assert "作者后来解释" in plan["decision_rationale"]
        # Only section 3 (the case section) may have been rewritten; sections
        # 1 and 5 (no case) must be reused.  The mock rewrites any section it
        # is asked to; assert it was asked for at most sections with cases.
        rewritten = set(mock2.rewritten_sections)
        assert rewritten, "受影响章节应被重写"
        assert rewritten <= {"3"}, f"未受影响章节不应重写：{rewritten}"
        report = state.get("p3_md") or ""
        assert "<!--human-ev:HE-0001-->" in report
        assert "作者后来解释" in report
        print("  ✓ 摄入闭环：问题→答案→证据→重规划→仅重写受影响章节→写入")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(Path("/tmp") / "outputs-e2e", ignore_errors=True)


def test_red_team_guards():
    evidence = academic_evidence.build_academic_evidence(_state(), JOB)
    segment, selected, argument, plans = _weak_case_plans(evidence)
    needs = human_evidence.build_evidence_needs(evidence, plans)
    questions = human_evidence.generate_questions(needs, evidence, plans)
    q = questions["questions"][0]
    # 1. "I don't remember" must not become a rationale.
    entry, _ = human_evidence.record_human_answer(
        questions, q["question_id"], "不记得", evidence)
    assert entry["status"] == "unavailable_after_human_check"
    adequacy = case_analysis.evidence_adequacy(segment)
    upgraded = human_evidence.case_capabilities(
        segment["segment_id"], [entry], adequacy)
    assert upgraded["evidence_level"] == adequacy["evidence_level"]
    assert not upgraded["capabilities"]["has_revision_rationale"]
    # 2. Answer stays verbatim; no silent rewrite.
    entry2, _ = human_evidence.record_human_answer(
        questions, q["question_id"], "我改它是因为读起来顺。", evidence)
    assert entry2["answer"] == "我改它是因为读起来顺。"
    assert entry2["derived_interpretation"] is None
    # 3. Case scope: plan validation rejects HE from another case.
    foreign = {**entry2, "human_evidence_id": "HE-FOREIGN",
               "case_id": f"seg-{JOB}-9999"}
    plans2 = case_analysis.build_case_analysis_plans(
        evidence, selected, argument, {"items": []},
        lambda *a, **k: json.dumps({"plans": [{
            "case_id": segment["segment_id"], "problem": {
                "type": "other", "statement": "x", "grounded": True},
            "human_evidence_ids": ["HE-FOREIGN"],
            "decision_rationale": "基于作者解释",
            "bounded_conclusion": "限定本案例",
        }]}, ensure_ascii=False), "x", "x", "x", [foreign])
    assert plans2["plans"][0]["human_evidence_ids"] == []
    print("  ✓ red-team：不记得不产生理由/答案原样保留/跨案例引用被拒绝")


if __name__ == "__main__":
    print("人类证据摄入测试：")
    test_needs_and_questions()
    test_answer_recording_statuses()
    test_capability_upgrade_and_scope()
    test_intake_to_targeted_regeneration()
    test_red_team_guards()
    print("\n全部通过 ✅")
