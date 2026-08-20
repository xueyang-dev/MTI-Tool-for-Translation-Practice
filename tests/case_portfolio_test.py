"""Full-corpus case portfolio checks. Run: python tests/case_portfolio_test.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import academic_evidence, case_portfolio


JOB = "portfoliofixture"


def _pair(source, target, initial=None, reviewed=True):
    return {"source": source, "target": target, "initial_target": initial,
            "reviewed": reviewed}


def _state():
    pairs = [
        _pair("TITLE", "TITLE", "错配文本"),
        _pair("The plane is in a gentle turn.", "飞机正在温和地转弯。",
              "飞机正在温和地转弯。"),
        _pair("He evaded the outstretched hand.", "他避开伸出的手。",
              "他避开伸出的手。"),
        _pair("Clean segment.", "正确段落。", "正确段落。"),
    ]
    return {
        "pairs": pairs, "paras": [x["source"] for x in pairs],
        "findings": [
            {"segment_index": 1, "severity": "actionable", "type": "review",
             "reason": "‘温和地转弯’搭配生硬，建议改为‘平缓地转弯’。",
             "suggested_target": "飞机正在平缓地转弯。"},
            {"segment_index": 2, "severity": "actionable", "type": "review",
             "reason": "‘outstretched hand’是比喻，直译会削弱请求被拒的含义。"},
        ],
        "human_actions": [], "glossary": [],
    }


def _portfolio():
    evidence = academic_evidence.build_academic_evidence(
        _state(), JOB, max_candidates=10)
    pool = case_portfolio.build_candidate_pool(evidence)
    taxonomy = case_portfolio.build_taxonomy(pool)
    portfolio = case_portfolio.plan_portfolio(pool, taxonomy, target_range=(1, 30))
    return evidence, pool, taxonomy, portfolio


def test_case_types_do_not_launder_review_findings():
    _, pool, _, _ = _portfolio()
    by_index = {x["segment_index"]: x for x in pool["candidates"]}
    assert by_index[0]["case_type"] == "authentic_revision"
    assert by_index[1]["case_type"] == "supporting_example"
    assert by_index[1]["provenance"]["historical_revision"] is False
    assert "historical_initial_to_final_repair" in by_index[1]["forbidden_claims"]
    assert 3 not in by_index
    print("  ✓ review findings remain supporting evidence, never revision history")


def test_taxonomy_and_tiers_form_a_hierarchy():
    _, _, taxonomy, portfolio = _portfolio()
    assert taxonomy["major_problem_count"] >= 1
    assert all(x.get("tier") in case_portfolio.TIERS for x in portfolio["cases"])
    assert all(x["tier"] != "tier_1_core" for x in portfolio["cases"]
               if x["case_type"] in {"boundary_case", "synthetic_contrast"})
    print("  ✓ corpus taxonomy and case tiers remain explicit")


def test_composition_and_validator_preserve_provenance():
    evidence, pool, taxonomy, portfolio = _portfolio()
    coverage = case_portfolio.build_coverage_matrix(portfolio, taxonomy)
    research = case_portfolio.build_research_model(portfolio)
    outline = case_portfolio.build_outline(portfolio, taxonomy, research)
    report = case_portfolio.compose_chapter(portfolio, taxonomy, outline, pool)
    validation = case_portfolio.validate_chapter(
        report, evidence, portfolio, pool)
    assert validation["status"] == "pass", validation["issues"]
    tampered = report.replace(
        "该例记录的是审校问题和建议，不是已经发生的修订。",
        "经过审校后，译文最终改为了建议译文。", 1)
    invalid = case_portfolio.validate_chapter(
        tampered, evidence, portfolio, pool)
    assert "supporting_example_laundered_as_revision" in {
        x["type"] for x in invalid["issues"]}
    print("  ✓ composition validation rejects supporting-as-revision laundering")


def test_core_mechanisms_are_unique_and_clusters_bounded():
    _, _, taxonomy, portfolio = _portfolio()
    coverage = case_portfolio.build_coverage_matrix(portfolio, taxonomy)
    review = case_portfolio.review_portfolio(portfolio, taxonomy, coverage)
    assert review["checks"]["core_mechanisms_are_unique"]
    assert review["checks"]["mechanism_clusters_are_bounded"]
    print("  ✓ redundancy control keeps one core per mechanism and bounded clusters")


def test_validator_requires_exact_synthetic_quotes_and_no_ungrounded_theory():
    evidence, pool, taxonomy, portfolio = _portfolio()
    synthetic_case = {
        "case_id": "SC-0001", "case_type": "synthetic_contrast",
        "source_segment_id": f"seg-{JOB}-0001", "source_text": "The plane turns.",
        "synthetic_baseline": {"text": "飞机温和转弯。"},
        "optimized_translation": {"text": "飞机平缓转弯。"},
        "difficulty": {"category": "register", "reason": "搭配差异"},
        "error": {"materiality": "moderate"},
        "validation": {"academic_case_eligible": True,
                       "repair_correctness": "confirmed"},
        "provenance": {"historical": False, "generated_for_analysis": True},
        "tier": "tier_3_contrast_boundary", "problem": {
            "major_problem": "discourse_pragmatics", "subproblem": "pragmatic_force",
            "subproblem_title": "反问、态度与语用力度"},
        "mechanism": "保持语用力度。", "mechanism_signature": "x:y",
    }
    portfolio = {**portfolio, "cases": portfolio["cases"] + [synthetic_case],
                 "selected_case_count": portfolio["selected_case_count"] + 1}
    report = """<!--portfolio-case:SC-0001-->
> [SYNTHETIC_SOURCE SC-0001]: Wrong source
> [SIMULATED SC-0001]: 飞机温和转弯。
> [OPTIMIZED SC-0001]: 飞机平缓转弯。
本例不是作者历史初译。功能对等理论可以解释它。
"""
    artifact = {"items": [synthetic_case]}
    result = case_portfolio.validate_chapter(
        report, evidence, portfolio, pool, artifact)
    types = {x["type"] for x in result["issues"]}
    assert "synthetic_quote_mismatch" in types
    assert "ungrounded_theory_claim" in types
    print("  ✓ exact synthetic provenance and theory grounding are enforced")


def test_contradicted_review_finding_is_rejected():
    state = {
        "pairs": [_pair(
            "That legendary run sent some of us to the hospital.",
            "那次长跑，因此有人被送进医院。",
            "那次长跑，因此有人被送进医院。")],
        "paras": ["That legendary run sent some of us to the hospital."],
        "findings": [{
            "segment_index": 0, "severity": "actionable", "type": "review",
            "reason": "译文中的‘因此’增加了因果关系，原文仅陈述事实。",
        }],
        "human_actions": [], "glossary": [],
    }
    evidence = academic_evidence.build_academic_evidence(state, JOB)
    pool = case_portfolio.build_candidate_pool(evidence)
    case = pool["candidates"][0]
    assert case["portfolio_eligibility"] == "rejected"
    assert case["finding_reliability"]["status"] == "contradicted"
    print("  ✓ source-contradicted review findings cannot enter the portfolio")


if __name__ == "__main__":
    print("全语料案例组合测试：")
    test_case_types_do_not_launder_review_findings()
    test_taxonomy_and_tiers_form_a_hierarchy()
    test_composition_and_validator_preserve_provenance()
    test_core_mechanisms_are_unique_and_clusters_bounded()
    test_validator_requires_exact_synthetic_quotes_and_no_ungrounded_theory()
    test_contradicted_review_finding_is_rejected()
    print("\n全部通过 ✅")
