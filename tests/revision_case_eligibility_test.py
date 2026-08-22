"""Regression tests for genuine initial→final revision eligibility.

Run: .venv/bin/python tests/revision_case_eligibility_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import academic_evidence, academic_quality, academic_validator
from transpraxis import academic_writer, case_analysis, human_evidence


JOB = "revisionfixture"


def _pair(source: str, initial: str, final: str) -> dict:
    return {"source": source, "initial_target": initial, "target": final,
            "reviewed": True, "from_tm": False, "glossary_entry_ids": []}


def _state(pairs: list[dict], findings: list[dict] | None = None) -> dict:
    return {"paras": [x["source"] for x in pairs], "pairs": pairs,
            "findings": findings or [], "human_actions": [], "glossary": []}


def _validation_inputs(case_id: str):
    research = {"research_questions": [{"rq_id": "RQ1", "question": "如何修订？"}]}
    argument = {"claims": [{"claim_id": "C1", "research_question": "RQ1",
                             "project_evidence": [case_id]}]}
    selected = {"cases": [{"case_id": case_id}]}
    outline = {"sections": [{"section_id": "3", "title": "案例分析",
                              "research_questions": ["RQ1"], "claims": ["C1"],
                              "cases": [case_id], "literature_claims": [],
                              "literature_evidence": [], "literature_sources": [],
                              "required_statistics": [], "minimum_chars": 1}]}
    return research, argument, selected, outline


def test_eligibility_gate_and_case_role():
    pairs = [
        _pair("unchanged", "译文相同。", "译文相同。"),
        _pair("revised", "旧译。", "新译。"),
        _pair("formatting", "只有 空格。", "只有空格。"),
        _pair("punctuation", "标点，变化。", "标点变化。"),
    ]
    evidence = academic_evidence.build_academic_evidence(_state(pairs), JOB)
    candidates = {x["segment_index"]: x for x in evidence["candidate_cases"]}
    assert set(candidates) == {1}
    assert candidates[1]["case_role"] == "revision_case"
    segments = evidence["project_evidence"]["segments"]
    assert segments[0]["case_role"] == "non_revision_case"
    assert segments[2]["case_role"] == "non_revision_case"
    assert case_analysis.translation_delta(segments[2])["formatting_only"]
    assert academic_evidence.has_meaningful_revision(
        pairs[3]["initial_target"], pairs[3]["target"],
        allow_formatting_revision=True)
    print("  ✓ unchanged/formatting-only excluded; meaningful revision eligible")


def test_finding_without_revision_stays_excluded():
    findings = [{"segment_index": 0, "severity": "actionable", "type": "review",
                 "reason": "存在审校建议", "suggested_target": "建议译文。"}]
    evidence = academic_evidence.build_academic_evidence(
        _state([_pair("source", "未改。", "未改。")], findings), JOB)
    assert evidence["candidate_cases"] == []
    stats = evidence["project_evidence"]["statistics"]
    assert stats["meaningfully_revised_segments"] == 0
    assert stats["revision_cases_with_findings"] == 0
    print("  ✓ finding without revision remains ineligible")


def test_neighbor_overlap_requires_review_and_is_not_selected():
    following = "下一段终译内容很长，用于确认重译结果没有错误并入相邻段落。" * 3
    evidence = academic_evidence.build_academic_evidence(_state([
        _pair("source one", "本段初译。", "本段终译。" + following),
        _pair("source two", "下一段旧译。", following),
    ]), JOB)
    candidates = {x["segment_index"]: x for x in evidence["candidate_cases"]}
    assert candidates[0]["academic_candidate_status"] == "review_required"
    assert candidates[0]["features"]["integrity_flags"][0]["type"] == \
        "probable_adjacent_target_overlap"
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    assert all(x["segment_index"] != 0 for x in selected["cases"])
    assert selected["selection_status"] == "insufficient_revision_cases"
    print("  ✓ probable adjacent-target overlap stays in pool but is not selected")


def test_adjacent_initial_contamination_is_not_a_revision_case():
    evidence = academic_evidence.build_academic_evidence(_state([
        _pair("previous source", "那是夏天，或是夏末。那是午后。",
              "那是夏天，或是夏末。那是午后。"),
        _pair("RIOT IN CELL BLOCK 11", "那是夏天，或是夏末。那是午后。",
              "RIOT IN CELL BLOCK 11"),
    ]), JOB)
    candidate = next(x for x in evidence["candidate_cases"]
                     if x["segment_index"] == 1)
    assert candidate["academic_candidate_status"] == "review_required"
    assert candidate["features"]["integrity_flags"][0]["type"] == \
        "probable_adjacent_initial_target_overlap"
    segment = evidence["project_evidence"]["segments"][1]
    assert not academic_evidence.is_eligible_revision_case(segment)
    adequacy = case_analysis.evidence_adequacy(segment)
    assert adequacy["case_role"] == "revision_evidence_boundary"
    assert not adequacy["capabilities"]["has_meaningful_revision"]
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    assert not selected["cases"]
    assert selected["selection_status"] == "insufficient_revision_cases"
    print("  ✓ adjacent initial contamination is a system boundary, not revision evidence")


def test_persisted_system_repair_flag_survives_after_text_is_corrected():
    pair = _pair("cross-page source", "旧译。", "按源文边界修复后的译文。")
    pair["integrity_flags"] = [{
        "type": "system_boundary_repair",
        "reason": "historical target contained adjacent paragraph content",
    }]
    evidence = academic_evidence.build_academic_evidence(_state([pair]), JOB)
    segment = evidence["project_evidence"]["segments"][0]
    candidate = evidence["candidate_cases"][0]
    assert segment["integrity_flags"] == pair["integrity_flags"]
    assert candidate["academic_candidate_status"] == "review_required"
    assert not academic_evidence.is_eligible_revision_case(segment)
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    assert selected["authentic_revision_cases"] == 0
    print("  ✓ persisted system-repair provenance cannot become a core case after correction")


def test_two_case_fallback_is_explicit_and_outline_safe():
    evidence = academic_evidence.build_academic_evidence(_state([
        _pair("source one", "旧译一。", "新译一。"),
        _pair("source two", "旧译二。", "新译二。"),
        _pair("source three", "未修改。", "未修改。"),
    ]), JOB)
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    assert selected["selection_status"] == "two_case_fallback"
    assert selected["preferred_core_case_count"] == 3
    assert selected["minimum_core_case_count"] == 2
    assert selected["selected_case_count"] == 2
    assert selected["scarcity_disclosure_required"]
    assert "第三个案例" in selected["scarcity_disclosure"]
    assert all(x["case_role"] == "revision_case" for x in selected["cases"])

    outline = academic_writer._fallback_outline(
        {"research_questions": [], "target_words": 4000}, {"claims": []}, selected)
    analysis = outline["sections"][-1]
    assert len(analysis["cases"]) == 2
    assert outline["case_count_policy"]["status"] == "two_case_fallback"
    assert any("第三" in x for x in analysis["allowed_conclusions"])
    print("  ✓ two genuine cases form an explicit, outline-safe fallback")


def test_two_case_validator_requires_disclosure_but_not_third_case():
    evidence = academic_evidence.build_academic_evidence(_state([
        _pair("source one", "旧译一。", "新译一。"),
        _pair("source two", "旧译二。", "新译二。"),
    ]), JOB)
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    outline = {"sections": []}
    disclosed = (
        "现有项目证据仅支持两个通过修订资格门禁的核心案例；"
        "未用弱证据补足第三个案例。\n"
        "<!--case-count-policy:two_case_fallback-->")
    result = academic_validator.validate_academic_report(
        disclosed, evidence, {"research_questions": []}, {"claims": []},
        selected, outline)
    types = {x["type"] for x in result["issues"]}
    assert "insufficient_core_revision_cases" not in types
    assert "missing_revision_evidence_scarcity_disclosure" not in types
    assert "wrong_core_case_count_claim" not in types

    hidden = academic_validator.validate_academic_report(
        "本文选择三个核心案例展开分析。", evidence,
        {"research_questions": []}, {"claims": []}, selected, outline)
    hidden_types = {x["type"] for x in hidden["issues"]}
    assert "missing_revision_evidence_scarcity_disclosure" in hidden_types
    assert "wrong_core_case_count_claim" in hidden_types
    print("  ✓ validator accepts two cases and rejects hidden three-case claims")


def test_human_evidence_cannot_promote_unchanged_case():
    evidence = academic_evidence.build_academic_evidence(
        _state([_pair("source", "未改。", "未改。")]), JOB)
    segment = evidence["project_evidence"]["segments"][0]
    adequacy = case_analysis.evidence_adequacy(segment)
    entry = {"human_evidence_id": "HE-1", "case_id": segment["segment_id"],
             "question_type": "translator_rationale", "status": "user_confirmed"}
    upgraded = human_evidence.case_capabilities(
        segment["segment_id"], [entry], adequacy)
    assert upgraded["case_role"] == "non_revision_case"
    assert not upgraded["capabilities"]["has_meaningful_revision"]
    plans = {"plans": [{"case_id": segment["segment_id"],
                        "translation_delta": case_analysis.translation_delta(segment),
                        "problem": {}, "recommended_human_evidence": []}]}
    assert human_evidence.build_evidence_needs(evidence, plans)["needs"] == []
    print("  ✓ Human Author Evidence cannot manufacture revision eligibility")


def test_human_evidence_enriches_but_does_not_reclassify_revision():
    evidence = academic_evidence.build_academic_evidence(
        _state([_pair("source", "旧译。", "新译。")]), JOB)
    segment = evidence["project_evidence"]["segments"][0]
    case_id = segment["segment_id"]
    adequacy = case_analysis.evidence_adequacy(segment)
    original_delta = case_analysis.translation_delta(segment)
    entries = [
        {"human_evidence_id": "HE-1", "case_id": case_id,
         "question_type": "repair_reason", "status": "user_confirmed"},
        {"human_evidence_id": "HE-2", "case_id": case_id,
         "question_type": "reader_response", "status": "user_confirmed"},
    ]
    enriched = human_evidence.case_capabilities(case_id, entries, adequacy)
    assert enriched["case_role"] == "revision_case"
    assert enriched["capabilities"]["has_meaningful_revision"]
    assert enriched["capabilities"]["has_revision_rationale"]
    assert "reader_response_claim" in enriched["can_support"]
    assert case_analysis.translation_delta(segment) == original_delta
    print("  ✓ Human Evidence enriches analysis without changing eligibility")


def test_quality_and_validator_reject_invented_revision():
    evidence = academic_evidence.build_academic_evidence(
        _state([_pair("source", "相同译文。", "相同译文。")]), JOB)
    segment = evidence["project_evidence"]["segments"][0]
    case_id = segment["segment_id"]
    # Deliberately inject the ineligible case to exercise defense-in-depth.
    evidence["candidate_cases"] = [{"case_id": case_id, "segment_id": case_id,
                                     "case_role": "non_revision_case", "score": 99}]
    research, argument, selected, outline = _validation_inputs(case_id)
    report = (f"## 3 案例分析\n<!--rq:RQ1--><!--claim:C1-->\n[{case_id}]\n"
              f"> [SOURCE {case_id}]: source\n"
              f"> [INITIAL {case_id}]: 相同译文。\n"
              f"> [TARGET {case_id}]: 相同译文。\n"
              "经过修订，初译最终改为当前译文。")
    result = academic_validator.validate_academic_report(
        report, evidence, research, argument, selected, outline)
    types = {x["type"] for x in result["issues"]}
    assert "non_revision_case_used_as_revision_analysis" in types
    assert "invented_revision" in types

    diagnostics = academic_quality.deterministic_diagnostics(
        research, argument, selected, outline,
        [{"section_id": "3", "content": report}], evidence)
    findings = academic_quality._deterministic_findings(diagnostics)
    assert any(x["type"] == "non_revision_case_used_as_revision_analysis"
               and x["priority"] == "P1" for x in findings)
    print("  ✓ invented revision is P1 and validation failure")


def test_real_delta_and_described_change_pass():
    evidence = academic_evidence.build_academic_evidence(
        _state([_pair("source", "旧译表达。", "新译表达。")]), JOB)
    segment = evidence["project_evidence"]["segments"][0]
    case_id = segment["segment_id"]
    research, argument, selected, outline = _validation_inputs(case_id)
    report = (f"## 3 案例分析\n<!--rq:RQ1--><!--claim:C1-->\n[{case_id}]\n"
              f"> [SOURCE {case_id}]: source\n"
              f"> [INITIAL {case_id}]: 旧译表达。\n"
              f"> [TARGET {case_id}]: 新译表达。\n"
              "将“旧译表达”改为“新译表达”，呈现了实际修订。")
    result = academic_validator.validate_academic_report(
        report, evidence, research, argument, selected, outline)
    forbidden = {"non_revision_case_used_as_revision_analysis", "invented_revision",
                 "wrong_initial_translation", "wrong_final_translation",
                 "described_revision_not_in_stored_delta"}
    assert not (forbidden & {x["type"] for x in result["issues"]})
    print("  ✓ correctly described stored delta passes revision checks")


if __name__ == "__main__":
    print("真实修订案例资格测试：")
    test_eligibility_gate_and_case_role()
    test_finding_without_revision_stays_excluded()
    test_neighbor_overlap_requires_review_and_is_not_selected()
    test_adjacent_initial_contamination_is_not_a_revision_case()
    test_persisted_system_repair_flag_survives_after_text_is_corrected()
    test_two_case_fallback_is_explicit_and_outline_safe()
    test_two_case_validator_requires_disclosure_but_not_third_case()
    test_human_evidence_cannot_promote_unchanged_case()
    test_human_evidence_enriches_but_does_not_reclassify_revision()
    test_quality_and_validator_reject_invented_revision()
    test_real_delta_and_described_change_pass()
    print("\n全部通过 ✅")
