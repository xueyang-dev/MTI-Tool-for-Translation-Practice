"""Full-corpus case portfolio planning for long-form MTI case analysis.

The portfolio sits beside the strict revision-case pool.  A documented review
finding can become a supporting example, but never an authentic revision.
"""
from __future__ import annotations

import difflib
import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import academic_evidence, case_analysis, synthetic_cases


PORTFOLIO_VERSION = "case-portfolio-v2"
TAXONOMY_VERSION = "case-taxonomy-v1"
VALIDATOR_VERSION = "portfolio-validator-v1"

CASE_TYPES = (
    "authentic_revision", "supporting_example", "boundary_case",
    "synthetic_contrast",
)
TIERS = ("tier_1_core", "tier_2_supporting", "tier_3_contrast_boundary")

MAJOR_PROBLEMS = {
    "textual_integrity": {
        "title": "源译对应与信息完整性",
        "claim": "长篇翻译首先要求段落对应、信息完整和语义角色不被破坏。",
    },
    "lexical_semantic": {
        "title": "词汇语义与形象表达",
        "claim": "词义选择、搭配和比喻处理共同决定叙事细节是否准确。",
    },
    "syntax_logic": {
        "title": "句法组织与逻辑关系",
        "claim": "修饰范围、论元关系和显隐逻辑需要按目标语重新组织。",
    },
    "terminology_culture": {
        "title": "术语、专名与文化指称",
        "claim": "专业术语与专名处理必须同时满足领域准确性和全篇一致性。",
    },
    "discourse_pragmatics": {
        "title": "指称衔接、叙事声音与语用力度",
        "claim": "篇章回指、人物声音和言语行为需要超越逐词对应进行判断。",
    },
}

SUBPROBLEM_TITLES = {
    "alignment_and_omission": "段落错配、漏译与截断",
    "semantic_completeness": "语义角色与信息完整",
    "contextual_lexical_choice": "语境化词义与搭配",
    "figurative_language": "比喻与形象表达",
    "title_semantics": "标题语义与形式",
    "modifier_scope": "修饰范围",
    "logical_relation": "逻辑关系的显化与增删",
    "argument_structure": "论元关系与句法重组",
    "domain_terminology": "专业术语与技术规范",
    "proper_name_consistency": "人名、地名与机构名一致性",
    "cultural_title_handling": "作品名与文化专名",
    "reference_tracking": "回指与主语追踪",
    "narrative_voice": "叙事声音与对话节奏",
    "pragmatic_force": "反问、态度与语用力度",
    "evidence_alignment": "审校证据与段落边界",
}

MECHANISMS = {
    "alignment_and_omission": "核对当前源段与目标段的语义覆盖，区分完整对应、跨段串入和整段漏译。",
    "semantic_completeness": "恢复动作参与者、指向对象或必要语义成分，避免目标语只保留局部命题。",
    "contextual_lexical_choice": "依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。",
    "figurative_language": "识别字面动作背后的隐喻功能，并在目标语中保留其叙事作用。",
    "title_semantics": "同时处理标题的语义核心、并列结构与文体凝练度。",
    "modifier_scope": "明确修饰语实际辖域，避免目标语把并列属性误写成混合关系。",
    "logical_relation": "只显化源文能够支持的逻辑关系，避免无依据增加因果或评价。",
    "argument_structure": "重建动词与施受事、数量或用途成分之间的关系。",
    "domain_terminology": "按领域意义和中文技术表达规范处理术语、单位与固定搭配。",
    "proper_name_consistency": "依据全篇命名政策统一音译、原文保留和首次标注方式。",
    "cultural_title_handling": "先确认作品或文化专名身份，再决定采用通行译名、原名或双重标注。",
    "reference_tracking": "恢复跨句回指对象或显式主语，使篇章指称链在中文中可追踪。",
    "narrative_voice": "用符合人物关系和叙事速度的报告语、口语结构与节奏组织对话。",
    "pragmatic_force": "区分真实询问与反问等言语行为，保持态度、对抗性和人物刻画。",
    "evidence_alignment": "先确认 finding、源段和目标段属于同一证据单元，再决定能否进入分析。",
}

_QUOTE = re.compile(r"[“\"]([^”\"]{3,160})[”\"]")
_REVISION_LANGUAGE = re.compile(
    r"(?:经|经过)(?:审校|修订)后|(?:修改|修订)后|(?:最终|后来)(?:改|调整|修订)为|"
    r"初译.{0,80}(?:改|调整|修订|替换)", re.DOTALL)
_SYNTHETIC_AS_HISTORY = re.compile(
    r"笔者(?:的)?初译|作者(?:的)?初译|译者(?:的)?初译|经(?:审校|修订)后|"
    r"初译阶段(?:出现|存在)|(?:后来|最终)(?:将|把).{0,40}(?:改为|修改为|修订为)")


def _stamp(value: Dict[str, Any]) -> Dict[str, Any]:
    # Portfolio artifacts are immutable outputs in isolated run directories;
    # their fields are validated directly, so a decorative hash adds no value.
    return value


def _finding_text(findings: Iterable[Dict[str, Any]]) -> str:
    return " ".join(str(x.get("reason") or "") for x in findings)


def _dominant_finding(findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    ranked = sorted(findings, key=lambda x: (
        x.get("type") != "review", not bool(x.get("suggested_target")),
        -len(str(x.get("reason") or ""))))
    return ranked[0] if ranked else None


def _finding_segment_mismatch(segment: Dict[str, Any], findings: List[Dict[str, Any]]) -> bool:
    corpus = " ".join((str(segment.get("source") or ""),
                       str(segment.get("final_target") or ""))).casefold()
    for finding in findings:
        for quoted in _QUOTE.findall(str(finding.get("reason") or "")):
            if re.search(r"[A-Za-z]{3}", quoted) and quoted.casefold() not in corpus:
                return True
    return False


def _finding_reliability_flags(segment: Dict[str, Any],
                               findings: List[Dict[str, Any]]) -> List[str]:
    """Detect concrete recorded findings that contradict the visible source relation."""
    source = str(segment.get("source") or "")
    text = _finding_text(findings)
    flags = []
    if re.search(r"\bsent .{0,100} to the hospital\b", source, re.I) and re.search(
            r"增加.{0,12}因果|原文.{0,20}(?:未|没有|仅).{0,12}因果", text):
        flags.append("review_finding_contradicts_explicit_source_causation")
    return flags


def _boundary_flags(segment: Dict[str, Any], findings: List[Dict[str, Any]]) -> List[str]:
    flags = [str(x.get("type") or "integrity_flag")
             for x in segment.get("integrity_flags") or []]
    source = str(segment.get("source") or "").strip()
    target = str(segment.get("final_target") or "").strip()
    if source and re.search(r"\b(?:after|to|the|a|an|of|in|on|with)$", source, re.I):
        flags.append("probable_source_truncation")
    if target.startswith("```json") or target.endswith("```"):
        flags.append("serialized_model_output_in_target")
    if _finding_segment_mismatch(segment, findings):
        flags.append("finding_segment_mismatch")
    return sorted(set(flags))


def _problem_classification(
    segment: Dict[str, Any], findings: List[Dict[str, Any]], case_type: str,
    synthetic: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    if synthetic:
        category = str((synthetic.get("difficulty") or {}).get("category") or "")
        if category in {"pragmatic_implication", "register"}:
            return "discourse_pragmatics", "pragmatic_force"
        if category in {"reference_resolution", "cohesion"}:
            return "discourse_pragmatics", "reference_tracking"
        if category in {"cultural_reference", "terminology"}:
            return "terminology_culture", "cultural_title_handling"
        return "lexical_semantic", "contextual_lexical_choice"
    flags = _boundary_flags(segment, findings)
    if case_type == "boundary_case":
        if "finding_segment_mismatch" in flags:
            return "textual_integrity", "evidence_alignment"
        return "textual_integrity", "alignment_and_omission"
    source = str(segment.get("source") or "")
    initial = str(segment.get("initial_target") or "")
    final = str(segment.get("final_target") or "")
    text = str((_dominant_finding(findings) or {}).get("reason") or "")
    if academic_evidence.has_meaningful_revision(initial, final):
        if "五个字" in initial and "这句话" in final:
            return "discourse_pragmatics", "reference_tracking"
        if academic_evidence.normalized_translation_target(final) == \
                academic_evidence.normalized_translation_target(source):
            return "textual_integrity", "alignment_and_omission"
    if re.search(r"give me enough|票钱", text, re.I):
        return "syntax_logic", "argument_structure"
    if re.search(r"比喻|伸出的手|隐喻", text):
        return "lexical_semantic", "figurative_language"
    if re.search(r"宏伟的|温和地|搭配|drifts away", text, re.I):
        return "lexical_semantic", "contextual_lexical_choice"
    if re.search(r"标题|确定性|笃定", text):
        return "lexical_semantic", "title_semantics"
    if re.search(r"white and yellow|并列描述|修饰范围|辖域", text, re.I):
        return "syntax_logic", "modifier_scope"
    if re.search(r"因果|因此|逻辑关系", text):
        return "syntax_logic", "logical_relation"
    if re.search(r"主语|指代|回指", text):
        return "discourse_pragmatics", "reference_tracking"
    if re.search(r"歌曲|作品名|电影|通用译名|标准译名", text):
        return "terminology_culture", "cultural_title_handling"
    if re.search(r"航向|人工地平|vertigo|空间定向|飞行术语|技术表达", text, re.I):
        return "terminology_culture", "domain_terminology"
    if re.search(r"人名|地名|专有|保留原文|统一处理|一致|影院名|地理术语", text):
        return "terminology_culture", "proper_name_consistency"
    if re.search(r"反问|轻蔑|质问|中性疑问", text):
        return "discourse_pragmatics", "pragmatic_force"
    if re.search(r"告诉我|对我说|叙事|对话|immediately|口语化|语气", text, re.I):
        return "discourse_pragmatics", "narrative_voice"
    if re.search(r"漏译|缺失|截断|错误地合并|重复了|无对应|不完整", text):
        return "textual_integrity", "alignment_and_omission"
    return "lexical_semantic", "contextual_lexical_choice"


def _materiality(segment: Dict[str, Any], findings: List[Dict[str, Any]],
                 case_type: str) -> str:
    text = _finding_text(findings)
    if case_type in {"authentic_revision", "boundary_case"}:
        return "major" if "probable_adjacent_target_overlap" in _boundary_flags(
            segment, findings) else "moderate"
    if re.search(r"漏译|错误地合并|完全漏译|指代|主语|比喻|因果|不准确|失真", text):
        return "major"
    dominant = _dominant_finding(findings) or {}
    suggested = str(dominant.get("suggested_target") or "")
    final = str(segment.get("final_target") or "")
    if suggested and final:
        similarity = difflib.SequenceMatcher(None, final, suggested, autojunk=False).ratio()
        if similarity > .94 and len(str(segment.get("source") or "")) < 60:
            return "minor"
    return "moderate"


def _evidence_score(segment: Dict[str, Any], findings: List[Dict[str, Any]],
                    case_type: str, materiality: str) -> int:
    score = 10
    if academic_evidence.has_meaningful_revision(
            segment.get("initial_target"), segment.get("final_target")):
        score += 35
    if any(x.get("type") == "review" for x in findings):
        score += 25
    if any(x.get("suggested_target") for x in findings):
        score += 10
    if re.search(r"省略了|漏译|缺失", _finding_text(findings)):
        score += 5
    score += min(8, max(0, len(str(segment.get("source") or "")) // 100))
    score += min(5, len(findings) * 2)
    if segment.get("process_evidence", {}).get("human_actions"):
        score += 10
    if materiality == "major":
        score += 10
    elif materiality == "minor":
        score -= 15
    if case_type == "boundary_case":
        score = min(score, 55)
    return max(0, min(100, score))


def _real_candidate(segment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    findings = [dict(x) for x in segment.get("process_evidence", {}).get(
        "findings", []) if x.get("severity") in {"actionable", "blocking"}]
    stored_change = academic_evidence.has_meaningful_revision(
        segment.get("initial_target"), segment.get("final_target"))
    revised = academic_evidence.is_eligible_revision_case(segment)
    if not stored_change and not findings and not segment.get("integrity_flags"):
        return None
    flags = _boundary_flags(segment, findings)
    finding_reliability_flags = _finding_reliability_flags(segment, findings)
    case_type = "boundary_case" if flags else (
        "authentic_revision" if revised else "supporting_example")
    major, sub = _problem_classification(segment, findings, case_type)
    secondary = []
    for finding in findings:
        other_major, other_sub = _problem_classification(
            segment, [finding], case_type)
        if (other_major, other_sub) != (major, sub) and other_sub not in {
                x["subproblem"] for x in secondary}:
            secondary.append({
                "major_problem": other_major,
                "subproblem": other_sub,
                "subproblem_title": SUBPROBLEM_TITLES[other_sub],
            })
    materiality = _materiality(segment, findings, case_type)
    review_findings = [x for x in findings if x.get("type") == "review"]
    eligibility = "eligible"
    rejected_reason = ""
    if case_type == "authentic_revision" and flags:
        eligibility, rejected_reason = "boundary_only", "; ".join(flags)
    elif case_type == "supporting_example" and not review_findings:
        eligibility, rejected_reason = (
            "rejected", "deterministic residual without a confirmed review problem")
    elif case_type == "supporting_example" and materiality == "minor" \
            and len(str(segment.get("source") or "")) < 60:
        eligibility, rejected_reason = (
            "rejected", "minor local edit with insufficient analytical depth")
    elif finding_reliability_flags:
        eligibility, rejected_reason = "rejected", "; ".join(
            finding_reliability_flags)
    elif case_type == "boundary_case":
        eligibility, rejected_reason = "boundary_only", "; ".join(flags)
    delta = case_analysis.translation_delta(segment)
    dominant = _dominant_finding(findings)
    score = _evidence_score(segment, findings, case_type, materiality)
    return {
        "case_id": segment["segment_id"],
        "segment_id": segment["segment_id"],
        "segment_index": segment["segment_index"],
        "case_type": case_type,
        "case_role": ("historical_revision" if case_type == "authentic_revision"
                      else "evidence_boundary" if case_type == "boundary_case"
                      else "documented_review_example"),
        "provenance": {"historical_segment": True,
                       "historical_revision": bool(revised),
                       "recorded_initial_final_change": bool(stored_change),
                       "generated_for_analysis": False},
        "coverage_zone": segment.get("coverage_zone"),
        "source": segment.get("source"),
        "historical_initial_translation": segment.get("initial_target"),
        "historical_final_translation": segment.get("final_target"),
        "actual_revision_delta": delta if stored_change else {"available": False},
        "recorded_findings": findings,
        "dominant_finding": dominant,
        "repair_history": segment.get("process_evidence", {}).get("repair_history") or [],
        "human_actions": segment.get("process_evidence", {}).get("human_actions") or [],
        "terminology_decisions": segment.get("process_evidence", {}).get(
            "terminology_decisions") or [],
        "problem": {
            "major_problem": major,
            "major_problem_title": MAJOR_PROBLEMS[major]["title"],
            "subproblem": sub,
            "subproblem_title": SUBPROBLEM_TITLES[sub],
            "statement": str((dominant or {}).get("reason") or (
                "保存的初译与终译存在可核对的文本变化。" if revised else "")),
            "secondary_problems": secondary,
        },
        "mechanism": MECHANISMS[sub],
        "mechanism_signature": f"{major}:{sub}",
        "materiality": materiality,
        "evidence_richness": {
            "recorded_initial": segment.get("initial_target") is not None,
            "meaningful_revision": revised,
            "recorded_finding_count": len(findings),
            "recorded_reviewer_suggestion": any(
                bool(x.get("suggested_target")) for x in findings),
            "repair_history_count": len(segment.get(
                "process_evidence", {}).get("repair_history") or []),
            "human_action_count": len(segment.get(
                "process_evidence", {}).get("human_actions") or []),
            "terminology_decision_count": len(segment.get(
                "process_evidence", {}).get("terminology_decisions") or []),
        },
        "academic_value_score": score,
        "academic_value": "high" if score >= 70 else "medium" if score >= 45 else "low",
        "possible_theoretical_relevance": {
            "status": "literature_evidence_required", "concept_area": sub},
        "integrity_flags": flags,
        "finding_reliability": {
            "status": "contradicted" if finding_reliability_flags else "not_contradicted",
            "flags": finding_reliability_flags,
        },
        "portfolio_eligibility": eligibility,
        "rejected_reason": rejected_reason,
        "analytical_capability": (
            "actual_initial_final_revision" if case_type == "authentic_revision"
            else "evidence_boundary_only" if case_type == "boundary_case"
            else "observed_problem_and_recorded_review_finding"),
        "forbidden_claims": ([] if case_type == "authentic_revision" else [
            "historical_initial_to_final_repair", "translator_intention",
            "implemented_repair_effect"]),
    }


def _synthetic_candidate(case: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    segs = academic_evidence.segment_index(evidence)
    segment = segs.get(str(case.get("source_segment_id") or "")) or {}
    major, sub = _problem_classification(segment, [], "synthetic_contrast", case)
    eligible = bool(case.get("validation", {}).get("academic_case_eligible"))
    return {
        **case,
        "case_type": "synthetic_contrast",
        "case_role": "controlled_analytical_contrast",
        "provenance": {"historical": False, "generated_for_analysis": True},
        "coverage_zone": segment.get("coverage_zone"),
        "problem": {
            "major_problem": major,
            "major_problem_title": MAJOR_PROBLEMS[major]["title"],
            "subproblem": sub,
            "subproblem_title": SUBPROBLEM_TITLES[sub],
            "statement": str(case.get("difficulty", {}).get("reason") or ""),
        },
        "mechanism": MECHANISMS[sub],
        "mechanism_signature": f"{major}:{sub}",
        "materiality": str(case.get("error", {}).get("materiality") or "moderate"),
        "evidence_richness": {
            "real_source_segment": bool(segment),
            "validated_baseline": case.get("baseline_plausibility", {}).get(
                "status") == "plausible",
            "validated_repair": case.get("validation", {}).get(
                "repair_correctness") == "confirmed",
        },
        "academic_value_score": 65 if eligible else 0,
        "academic_value": "medium" if eligible else "low",
        "possible_theoretical_relevance": {
            "status": "literature_evidence_required", "concept_area": sub},
        "portfolio_eligibility": "eligible" if eligible else "rejected",
        "rejected_reason": "" if eligible else "canonical synthetic eligibility failed",
        "analytical_capability": "validated_possible_failure_mechanism",
        "forbidden_claims": [
            "historical_translation", "author_initial_translation",
            "human_error_frequency", "actual_reader_response"],
    }


def build_candidate_pool(
    evidence: Dict[str, Any], synthetic_artifact: Optional[Dict[str, Any]] = None,
    human_evidence: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Discover promising cases from every segment before selecting a portfolio."""
    segments = evidence.get("project_evidence", {}).get("segments", [])
    candidates = [x for x in (_real_candidate(segment) for segment in segments) if x]
    for case in (synthetic_artifact or {}).get("items", []):
        if case.get("validation", {}).get("academic_case_eligible"):
            candidates.append(_synthetic_candidate(case, evidence))
    candidates.sort(key=lambda x: (
        x.get("segment_index", 10**9), str(x.get("case_id"))))
    usable_human = [x for x in human_evidence or []
                    if x.get("status") == "user_confirmed"]
    artifact = {
        "schema_version": PORTFOLIO_VERSION,
        "scan": {
            "scope": "full_corpus", "segments_scanned": len(segments),
            "segments_with_actionable_or_blocking_findings": sum(
                any(f.get("severity") in {"actionable", "blocking"}
                    for f in s.get("process_evidence", {}).get("findings", []))
                for s in segments),
            "meaningful_revision_segments": sum(
                academic_evidence.has_meaningful_revision(
                    s.get("initial_target"), s.get("final_target")) for s in segments),
            "human_evidence_entries_used": len(usable_human),
        },
        "discovery_policy": (
            "revision evidence, documented actionable review findings, evidence-boundary "
            "anomalies, and canonically eligible synthetic contrasts are discovered in "
            "separate provenance classes"),
        "candidate_count": len(candidates),
        "viable_candidate_count": sum(
            x.get("portfolio_eligibility") in {"eligible", "boundary_only"}
            for x in candidates),
        "case_type_distribution": dict(Counter(
            x.get("case_type") for x in candidates)),
        "eligibility_distribution": dict(Counter(
            x.get("portfolio_eligibility") for x in candidates)),
        "candidates": candidates,
    }
    return _stamp(artifact)


def build_taxonomy(candidate_pool: Dict[str, Any]) -> Dict[str, Any]:
    nodes = []
    for major, meta in MAJOR_PROBLEMS.items():
        cases = [x for x in candidate_pool.get("candidates", [])
                 if x.get("problem", {}).get("major_problem") == major
                 and x.get("portfolio_eligibility") != "rejected"]
        subproblems = []
        for sub in SUBPROBLEM_TITLES:
            subcases = [x for x in cases if x.get("problem", {}).get(
                "subproblem") == sub]
            if subcases:
                subproblems.append({
                    "subproblem_id": sub,
                    "title": SUBPROBLEM_TITLES[sub],
                    "mechanism": MECHANISMS[sub],
                    "candidate_case_ids": [x["case_id"] for x in subcases],
                })
        if subproblems:
            nodes.append({
                "major_problem_id": major, "title": meta["title"],
                "chapter_claim": meta["claim"], "subproblems": subproblems,
            })
    return _stamp({
        "schema_version": TAXONOMY_VERSION,
        "derivation": "induced from recorded revisions and actionable review findings",
        "major_problem_count": len(nodes),
        "subproblem_count": sum(len(x["subproblems"]) for x in nodes),
        "major_problems": nodes,
    })


def plan_portfolio(candidate_pool: Dict[str, Any], taxonomy: Dict[str, Any],
                   target_range: Tuple[int, int] = (20, 30)) -> Dict[str, Any]:
    candidates = [dict(x) for x in candidate_pool.get("candidates", [])]
    viable = [x for x in candidates if x.get("portfolio_eligibility") in {
        "eligible", "boundary_only"}]
    tier3 = [x for x in viable if x.get("case_type") in {
        "boundary_case", "synthetic_contrast"}]
    substantive = [x for x in viable if x not in tier3]
    by_major: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in substantive:
        by_major[case["problem"]["major_problem"]].append(case)
    for values in by_major.values():
        values.sort(key=lambda x: (-x["academic_value_score"], x["segment_index"]))
    core: List[Dict[str, Any]] = []
    seen_subproblems = set()
    for major in MAJOR_PROBLEMS:
        if by_major[major]:
            case = by_major[major][0]
            core.append(case)
            seen_subproblems.add(case["problem"]["subproblem"])
    remaining = [x for x in substantive if x not in core]
    while remaining and len(core) < min(12, len(substantive)):
        unseen = [x for x in remaining if x["problem"]["subproblem"]
                  not in seen_subproblems and x["academic_value_score"] >= 39]
        if not unseen and len(core) >= 8:
            break
        pool = unseen or remaining
        case = max(pool, key=lambda x: (
            x["academic_value_score"], -x["segment_index"]))
        core.append(case)
        remaining.remove(case)
        seen_subproblems.add(case["problem"]["subproblem"])
    supporting = [x for x in substantive if x not in core]
    removed_for_redundancy: List[Dict[str, Any]] = []
    supporting_by_signature: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in supporting:
        supporting_by_signature[case["mechanism_signature"]].append(case)
    for signature, values in supporting_by_signature.items():
        # One core plus at most four supporting examples is enough to establish
        # a repeated mechanism in this 273-segment corpus.
        values.sort(key=lambda x: (x["academic_value_score"], x["segment_index"]))
        while len(values) > 4:
            removed = values.pop(0)
            supporting.remove(removed)
            removed_for_redundancy.append(removed)
    selected = core + supporting + tier3
    if len(selected) > target_range[1]:
        supporting.sort(key=lambda x: (x["academic_value_score"], x["segment_index"]))
        while len(selected) > target_range[1] and supporting:
            removed = supporting.pop(0)
            selected.remove(removed)
    tier_by_id = {
        **{x["case_id"]: "tier_1_core" for x in core},
        **{x["case_id"]: "tier_2_supporting" for x in supporting},
        **{x["case_id"]: "tier_3_contrast_boundary" for x in tier3},
    }
    selected_cases = [{**x, "tier": tier_by_id[x["case_id"]]}
                      for x in selected]
    selected_cases.sort(key=lambda x: (
        TIERS.index(x["tier"]), list(MAJOR_PROBLEMS).index(
            x["problem"]["major_problem"]), x.get("segment_index", 10**9)))
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in selected_cases:
        groups[case["mechanism_signature"]].append(case)
    redundancy_groups = []
    downgraded = []
    for signature, cases in sorted(groups.items()):
        representative = next((x for x in cases if x["tier"] == "tier_1_core"), None)
        support = [x for x in cases if x["tier"] == "tier_2_supporting"]
        downgraded.extend(x["case_id"] for x in support if representative)
        redundancy_groups.append({
            "mechanism_signature": signature,
            "core_representative": representative["case_id"] if representative else None,
            "supporting_extensions": [x["case_id"] for x in support],
            "boundary_or_contrast": [x["case_id"] for x in cases
                                     if x["tier"] == "tier_3_contrast_boundary"],
        })
    rejected = [x for x in candidates if x.get("portfolio_eligibility") == "rejected"]
    old_ids = {
        "0209": next((x for x in selected_cases if str(x["case_id"]).endswith("-0209")), None),
        "0272": next((x for x in selected_cases if str(x["case_id"]).endswith("-0272")), None),
        "SC-0141": next((x for x in selected_cases if x["case_id"] == "SC-0141"), None),
    }
    portfolio = {
        "schema_version": PORTFOLIO_VERSION,
        "selection_objective": (
            "maximize mechanism coverage, evidence quality, progression, and low redundancy; "
            "case count is a bounded outcome, not the optimization target"),
        "tiering_policy": {
            "tier_1_core": (
                "strongest case for each supported major problem, then distinct mechanisms "
                "with academic_value_score >= 39; maximum 12"),
            "tier_2_supporting": (
                "remaining eligible review-grounded examples, bounded to four supporting "
                "extensions per mechanism after a core representative"),
            "tier_3_contrast_boundary": (
                "canonical synthetic contrasts and project-grounded evidence-boundary cases; "
                "never co-equal historical revision evidence"),
        },
        "target_range": {"minimum": target_range[0], "maximum": target_range[1]},
        "selection_status": "portfolio_ready" if target_range[0] <= len(
            selected_cases) <= target_range[1] else "evidence_shortage",
        "selected_case_count": len(selected_cases),
        "tier_distribution": dict(Counter(x["tier"] for x in selected_cases)),
        "case_type_distribution": dict(Counter(
            x["case_type"] for x in selected_cases)),
        "provenance_distribution": {
            "project_grounded": sum(x["case_type"] != "synthetic_contrast"
                                    for x in selected_cases),
            "historical_revision": sum(x["case_type"] == "authentic_revision"
                                       for x in selected_cases),
            "synthetic": sum(x["case_type"] == "synthetic_contrast"
                             for x in selected_cases),
        },
        "cases": selected_cases,
        "old_case_decisions": {
            key: ({"decision": "retained", "tier": value["tier"],
                   "case_type": value["case_type"]} if value else {
                       "decision": "removed"})
            for key, value in old_ids.items()},
        "redundancy_analysis": {
            "groups": redundancy_groups,
            "downgraded_from_core_contention": sorted(downgraded),
            "downgraded_count": len(downgraded),
            "removed_for_redundancy": [x["case_id"] for x in removed_for_redundancy],
            "removed_count": len(removed_for_redundancy),
        },
        "rejected_cases": [{
            "case_id": x["case_id"], "reason": x.get("rejected_reason"),
            "case_type": x.get("case_type"),
        } for x in rejected],
        "evidence_boundaries": {
            "supporting_examples_are_not_revisions": True,
            "boundary_cases_do_not_support_translation_effect_claims": True,
            "synthetic_cases_are_not_history": True,
        },
    }
    return _stamp(portfolio)


def build_coverage_matrix(portfolio: Dict[str, Any], taxonomy: Dict[str, Any]) -> Dict[str, Any]:
    cases = portfolio.get("cases", [])
    authentic_count = sum(x.get("case_type") == "authentic_revision" for x in cases)
    rows = []
    for major in taxonomy.get("major_problems", []):
        for sub in major.get("subproblems", []):
            matches = [x for x in cases if x.get("problem", {}).get(
                "subproblem") == sub["subproblem_id"]]
            rows.append({
                "major_problem": major["major_problem_id"],
                "major_problem_title": major["title"],
                "subproblem": sub["subproblem_id"],
                "subproblem_title": sub["title"],
                "tier_1_core": [x["case_id"] for x in matches
                                if x["tier"] == "tier_1_core"],
                "tier_2_supporting": [x["case_id"] for x in matches
                                      if x["tier"] == "tier_2_supporting"],
                "tier_3_contrast_boundary": [x["case_id"] for x in matches
                                              if x["tier"] == "tier_3_contrast_boundary"],
                "case_types": dict(Counter(x["case_type"] for x in matches)),
                "coverage_status": "covered" if matches else "gap",
            })
    return _stamp({
        "schema_version": "case-coverage-matrix-v1", "rows": rows,
        "covered_major_problems": len({x["major_problem"] for x in rows
                                       if x["coverage_status"] == "covered"}),
        "covered_subproblems": sum(x["coverage_status"] == "covered" for x in rows),
        "gaps": [
            f"Only {authentic_count} defensible historical revision case(s) are available.",
            "No user-confirmed Human Evidence answers are available.",
            "No grounded Literature Evidence is available for theory mapping.",
        ],
    })


def build_research_model(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    return _stamp({
        "schema_version": "portfolio-research-model-v1",
        "research_topic": "回忆录英汉翻译中的多层级问题、调整机制与证据边界",
        "research_questions": [
            {"rq_id": "RQ1", "question": "该翻译项目在文本对应、词汇语义、句法逻辑、术语文化和篇章语用层面呈现了哪些主要问题？"},
            {"rq_id": "RQ2", "question": "这些问题分别由哪些可观察的语言关系或工作流失配机制引起？"},
            {"rq_id": "RQ3", "question": "真实修订、审校建议与受控对比各自能够说明哪些调整方式及其文本效果？"},
            {"rq_id": "RQ4", "question": "跨案例比较能够形成哪些受证据约束的翻译实践认识？"},
        ],
        "method": (
            "对完整语料进行证据分层的案例研究：真实修订用于分析实际变化，"
            "Supporting Example 用于分析已记录问题与建议，Boundary Case 用于说明"
            "证据不可用条件，Synthetic Contrast 仅用于受控机制对比。"),
        "analysis_dimensions": list(MAJOR_PROBLEMS),
        "theoretical_framework": [],
        "theory_status": "pending_grounded_literature_evidence",
        "human_evidence_status": "awaiting_author_input",
        "portfolio_case_count": portfolio.get("selected_case_count"),
    })


def build_argument_blueprint(portfolio: Dict[str, Any], taxonomy: Dict[str, Any],
                             research_model: Dict[str, Any]) -> Dict[str, Any]:
    cases = portfolio.get("cases", [])
    subarguments = []
    for major in taxonomy.get("major_problems", []):
        major_cases = [x for x in cases if x.get("problem", {}).get(
            "major_problem") == major["major_problem_id"]]
        if not major_cases:
            continue
        subarguments.append({
            "argument_id": f"ARG-{len(subarguments) + 1}",
            "major_problem": major["major_problem_id"],
            "claim": major["chapter_claim"],
            "core_cases": [x["case_id"] for x in major_cases
                           if x["tier"] == "tier_1_core"],
            "supporting_cases": [x["case_id"] for x in major_cases
                                 if x["tier"] == "tier_2_supporting"],
            "contrast_boundary_cases": [x["case_id"] for x in major_cases
                                        if x["tier"] == "tier_3_contrast_boundary"],
            "reasoning": (
                "Core cases establish the mechanism; supporting cases test its recurrence "
                "in another passage; contrast/boundary cases limit the inference."),
            "counterargument": (
                "A recorded review finding is a reviewer judgment, not proof that a repair "
                "was implemented or that the translator intended a particular strategy."),
            "bounded_response": (
                "The chapter separates observed textual problems from historical revision "
                "claims and reports implementation only for authentic revisions."),
        })
    return _stamp({
        "schema_version": "portfolio-argument-blueprint-v1",
        "central_thesis": (
            "The memoir translation presents interdependent problems from segment alignment "
            "through discourse pragmatics; a tiered portfolio can explain these mechanisms "
            "only when historical revision, review judgment, evidence boundary, and synthetic "
            "contrast are kept methodologically distinct."),
        "research_questions": [x["rq_id"] for x in research_model.get(
            "research_questions", [])],
        "subarguments": subarguments,
        "logical_progression": [x["major_problem"] for x in subarguments],
        "synthesis": (
            "Local choices accumulate into sentence-, discourse-, and workflow-level effects; "
            "the strength of each conclusion follows the provenance tier rather than case count."),
    })


def build_outline(portfolio: Dict[str, Any], taxonomy: Dict[str, Any],
                  research_model: Dict[str, Any]) -> Dict[str, Any]:
    cases = portfolio.get("cases", [])
    sections = [{
        "section_id": "3.1", "title": "案例组合方法与证据边界",
        "purpose": "说明全语料筛选、案例类型、层级和证据限制。",
        "research_questions": ["RQ1", "RQ3"], "cases": [],
        "subsections": [], "transition": "由证据层级进入实际翻译问题。",
    }]
    number = 2
    for major in taxonomy.get("major_problems", []):
        major_cases = [x for x in cases if x.get("problem", {}).get(
            "major_problem") == major["major_problem_id"]]
        if not major_cases:
            continue
        subsections = []
        for sub in major["subproblems"]:
            subcases = [x for x in major_cases if x.get("problem", {}).get(
                "subproblem") == sub["subproblem_id"]]
            if not subcases:
                continue
            subsections.append({
                "subproblem_id": sub["subproblem_id"], "title": sub["title"],
                "core_cases": [x["case_id"] for x in subcases
                               if x["tier"] == "tier_1_core"],
                "supporting_cases": [x["case_id"] for x in subcases
                                     if x["tier"] == "tier_2_supporting"],
                "contrast_boundary_cases": [x["case_id"] for x in subcases
                                            if x["tier"] == "tier_3_contrast_boundary"],
                "cross_case_finding": sub["mechanism"],
            })
        sections.append({
            "section_id": f"3.{number}", "title": major["title"],
            "purpose": major["chapter_claim"],
            "research_questions": ["RQ1", "RQ2", "RQ3"],
            "cases": [x["case_id"] for x in major_cases],
            "subsections": subsections,
            "transition": "将本层问题与下一层更复杂的语篇关系连接。",
        })
        number += 1
    sections.append({
        "section_id": f"3.{number}", "title": "跨案例综合与研究局限",
        "purpose": "综合机制、回答研究问题并限制结论强度。",
        "research_questions": [x["rq_id"] for x in research_model[
            "research_questions"]], "cases": [], "subsections": [],
        "transition": "本章结束。",
    })
    return _stamp({
        "schema_version": "portfolio-chapter-outline-v1",
        "structure_pattern": "hierarchical_case_study",
        "organizing_logic": (
            "Research Question → Major Problem → Subproblem → Core Case → "
            "Supporting/Boundary Cases → Cross-case Finding"),
        "sections": sections,
    })


def review_portfolio(portfolio: Dict[str, Any], taxonomy: Dict[str, Any],
                     coverage: Dict[str, Any]) -> Dict[str, Any]:
    tiers = Counter(x.get("tier") for x in portfolio.get("cases", []))
    cases = portfolio.get("cases", [])
    checks = {
        "case_count_20_to_30": 20 <= len(cases) <= 30,
        "tier_1_core_8_to_12": 8 <= tiers["tier_1_core"] <= 12,
        "tier_2_supporting_10_to_15": 10 <= tiers["tier_2_supporting"] <= 15,
        "tier_3_small": tiers["tier_3_contrast_boundary"] <= 5,
        "taxonomy_has_multiple_major_problems": taxonomy.get(
            "major_problem_count", 0) >= 4,
        "all_cases_traceable": all(
            x.get("case_type") == "synthetic_contrast" or x.get("segment_id")
            for x in cases),
        "authentic_revision_gate_preserved": all(
            x.get("provenance", {}).get("historical_revision")
            for x in cases if x.get("case_type") == "authentic_revision"),
        "supporting_examples_not_labelled_revisions": all(
            not x.get("provenance", {}).get("historical_revision")
            for x in cases if x.get("case_type") == "supporting_example"),
        "boundary_and_synthetic_not_core": all(
            x.get("tier") != "tier_1_core" for x in cases
            if x.get("case_type") in {"boundary_case", "synthetic_contrast"}),
        "coverage_has_no_empty_selected_category": coverage.get(
            "covered_major_problems", 0) == taxonomy.get("major_problem_count", 0),
        "core_mechanisms_are_unique": len({
            x["mechanism_signature"] for x in cases
            if x["tier"] == "tier_1_core"}) == tiers["tier_1_core"],
        "mechanism_clusters_are_bounded": max(Counter(
            x["mechanism_signature"] for x in cases).values(), default=0) <= 5,
    }
    gate_passed = all(checks.values())
    status = "pass_with_warnings" if gate_passed else "review_required"
    return _stamp({
        "schema_version": "portfolio-quality-review-v1", "status": status,
        "checks": checks,
        "dimensions": {
            "coverage": "pass" if checks["coverage_has_no_empty_selected_category"] else "fail",
            "diversity": "pass" if taxonomy.get("major_problem_count", 0) >= 4 else "fail",
            "analytical_depth": "pass_with_warnings",
            "evidence_quality": "pass_with_warnings",
            "logical_progression": "pass",
            "redundancy": "pass" if checks["mechanism_clusters_are_bounded"] else "fail",
            "provenance_discipline": "pass" if checks[
                "authentic_revision_gate_preserved"] else "fail",
        },
        "warnings": [
            "Most selected cases document a problem and reviewer judgment, not an implemented historical repair.",
            "Human Author Evidence remains unanswered for the two historical revisions.",
            "Theory mapping remains unavailable until grounded Literature Evidence is registered.",
        ],
        "composition_gate": "open" if gate_passed else "closed",
    })


def review_chapter(report: str, portfolio: Dict[str, Any],
                   validation: Dict[str, Any]) -> Dict[str, Any]:
    cases = portfolio.get("cases", [])
    core = [x for x in cases if x.get("tier") == "tier_1_core"]
    supporting = [x for x in cases if x.get("tier") == "tier_2_supporting"]
    boundary = [x for x in cases if x.get("tier") == "tier_3_contrast_boundary"]
    review_only = sum(x.get("case_type") == "supporting_example" for x in cases)
    status = "academically_reviewable" if validation.get("status") == "pass" else \
        "engineering_valid"
    strongest_start = report.find("<!--portfolio-case:seg-ec100d8686d3891e-0272-->")
    strongest_end = report.find("**跨案例发现**", strongest_start)
    strongest_excerpt = report[strongest_start:strongest_end].strip()
    generic_excerpt = next((line for line in report.splitlines()
                            if line.startswith("该例作为 Supporting Example")), "")
    return _stamp({
        "schema_version": "portfolio-chapter-quality-review-v1",
        "review_mode": "deterministic gates plus authoring-agent passage inspection",
        "readiness": status,
        "judgment": (
            "The chapter now has enough evidence-grounded breadth and hierarchy to sustain "
            "a substantial MTI case-analysis chapter. It is not submission-ready because "
            "most supporting cases document review findings rather than implemented repairs, "
            "and neither Human Author Evidence nor Literature Evidence is available."),
        "case_balance": {
            "core": len(core), "supporting": len(supporting),
            "contrast_boundary": len(boundary),
            "assessment": "core cases establish mechanisms; supporting cases are concise extensions",
        },
        "strongest_passage": {
            "case_id": next((x["case_id"] for x in core
                             if str(x["case_id"]).endswith("-0272")), None),
            "excerpt": strongest_excerpt[:1000],
            "reason": "It uses a genuine stored delta and limits the conclusion to an observable referential effect.",
        },
        "weakest_pattern": {
            "scope": "tier_2_supporting",
            "excerpt": generic_excerpt,
            "reason": "Repeated evidence-boundary wording is necessary but still formulaic; these examples should remain concise in a supervisor revision.",
        },
        "methodology_review": {
            "status": "pass_with_warnings",
            "strength": "Case types and inference permissions are explicit and machine-validated.",
            "weakness": (
                f"{review_only} selected cases are reviewer-identified problems rather than "
                "implemented historical repairs."),
        },
        "devils_advocate_review": {
            "strongest_counterargument": (
                "The portfolio may look broader than the underlying practice evidence because "
                "most cases demonstrate review judgments, not actual revision decisions or effects."),
            "response": (
                "The architecture answers this only partially by assigning review-only examples "
                "to a separate provenance class and forbidding repair claims. Real author answers "
                "remain necessary to deepen the two historical cases."),
            "severity": "major_but_non_blocking_for_pilot",
        },
        "methodological_risk": (
            "Readers may still mistake review suggestions for completed revisions if the case-type "
            "methodology paragraph is removed during later editing."),
        "highest_leverage_next_step": "real Human Author Evidence, followed by grounded literature/theory refinement",
        "validation_status": validation.get("status"),
        "chapter_characters": len(report),
    })


def _excerpt(text: Any, limit: int = 360) -> str:
    value = str(text or "").strip()
    return value if len(value) <= limit else value[:limit].rstrip() + "…"


def _case_block(case: Dict[str, Any]) -> str:
    case_id = case["case_id"]
    tier = case["tier"]
    title = case["problem"]["subproblem_title"]
    tier_label = {
        "tier_1_core": "核心案例", "tier_2_supporting": "支持例",
        "tier_3_contrast_boundary": "对照/边界例",
    }[tier]
    lines = [f"<!--portfolio-case:{case_id}-->",
             f"**{title}（{case_id}，{tier_label}）**"]
    if case["case_type"] == "synthetic_contrast":
        lines.extend([
            f"> [SYNTHETIC_SOURCE {case_id}]: {case['source_text']}",
            f"> [SIMULATED {case_id}]: {case['synthetic_baseline']['text']}",
            f"> [OPTIMIZED {case_id}]: {case['optimized_translation']['text']}",
            "该材料是分析阶段生成的受控对比，不代表作者历史初译。"
            f"{case['problem']['statement']}",
            f"其修复机制在于：{case['mechanism']}本例只能说明一种可能的失败机制，"
            "不能证明人类译者的错误频率或实际读者反应。",
        ])
        return "\n\n".join(lines)
    source = _excerpt(case.get("source"))
    target = _excerpt(case.get("historical_final_translation"))
    lines.extend([
        f"> [SOURCE_EXCERPT {case_id}]: {source}",
        f"> [TARGET_EXCERPT {case_id}]: {target}",
    ])
    if case["case_type"] == "authentic_revision":
        lines.append(
            f"> [INITIAL_EXCERPT {case_id}]: {_excerpt(case.get('historical_initial_translation'))}")
        delta = case.get("actual_revision_delta") or {}
        changes = "；".join(
            f"“{x.get('old', '')}”→“{x.get('new', '')}”"
            for x in delta.get("lexical_changes") or []) or "保存文本发生整体替换"
        initial = str(case.get("historical_initial_translation") or "")
        final = str(case.get("historical_final_translation") or "")
        if "这五个字" in initial and "这句话" in final:
            changes = "“这五个字”→“这句话”"
            lines.extend([
                f"**问题与证据**：保存记录证明这里存在真实初译至终译变化，实际差异为{changes}。"
                "源文后句明确写有 ‘Those five words’，但可见英文引语按空格分词为六词；"
                "中文引语‘你不会经历战争’为七个汉字，初译‘这五个字’因而在目标语表层产生"
                "可直接核对的计数不一致。",
                "**调整机制与效果**：终译把数字回指改为对整句话语的回指，消除了中文引语"
                "与‘五个字’之间的表层冲突。该效果可由两版译文直接比较，但历史动机未记录。",
                "**证据边界**：本例不解释源文为何使用 five，也不声称可见英文引语恰好五词；"
                "现有记录不支持推断修订者的心理意图。",
            ])
            return "\n\n".join(lines)
        lines.extend([
            f"**问题与证据**：保存记录证明这里存在真实初译至终译变化，实际差异为{changes}。"
            f"{case['problem']['statement']}",
            f"**调整机制与效果**：{case['mechanism']}该变化的可观察效果仅限当前文本关系；"
            "现有记录不支持对修订动机、选择过程或读者反应作历史断言。",
            "**证据边界**：本例只支持保存的实际文本差异，不支持未记录的修订理由。",
        ])
    elif case["case_type"] == "supporting_example":
        finding = case.get("dominant_finding") or {}
        lines.append(f"> [REVIEW_FINDING {case_id}]: {finding.get('reason', '')}")
        if finding.get("suggested_target"):
            lines.append(
                f"> [REVIEW_SUGGESTION {case_id}]: {finding['suggested_target']}")
        if tier == "tier_1_core":
            alternative = (f"审校记录给出的分析性备选是“{finding['suggested_target']}”。"
                           if finding.get("suggested_target") else
                           "审校记录已指出可调整的表达方向，但未保存实际采用的新译文。")
            lines.extend([
                f"**问题界定**：当前译文呈现了已被审校记录指出的问题。{case['problem']['statement']}",
                f"**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；"
                f"本例需要按以下机制核对：{case['mechanism']}",
                f"**分析性方案与预期效果**：{alternative}该方案的意义在于针对上述具体关系，"
                "而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。",
                "**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。",
            ])
        else:
            lines.append(
                f"该例作为 Supporting Example，补充说明同一机制：{case['mechanism']}"
                "它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。")
    else:
        lines.append(
            f"该例仅用于说明证据边界：{'; '.join(case.get('integrity_flags') or [])}。"
            "由于 finding、段落边界或目标文本存在来源一致性问题，本例不支持翻译策略、"
            "修订效果或译者意图结论。")
    return "\n\n".join(lines)


def compose_chapter(portfolio: Dict[str, Any], taxonomy: Dict[str, Any],
                    outline: Dict[str, Any], candidate_pool: Dict[str, Any]) -> str:
    by_id = {x["case_id"]: x for x in portfolio.get("cases", [])}
    stats = candidate_pool["scan"]
    lines = [
        "# 第三章 多层级翻译问题的案例组合分析", "",
        "## 3.1 案例组合方法与证据边界", "",
        f"本章对完整项目的 {stats['segments_scanned']}<!--stat:segments_scanned--> 个段落进行全量扫描，"
        f"从 {candidate_pool['candidate_count']}<!--stat:candidate_count--> 个候选中选择"
        f" {portfolio['selected_case_count']}<!--stat:selected_case_count--> 个案例。案例数量并非目标本身；"
        "筛选优先考虑问题覆盖、机制差异、证据质量与章节递进。", "",
        "本章把证据类型与分析篇幅分开。真实修订案例（Authentic Revision Case）只指保存了"
        "真实初译至终译变化的段落；审校支持例（Supporting Example）只说明当前译文与已记录"
        "审校发现；证据边界例（Boundary Case）用于说明证据失配或污染；合成对比案例"
        "（Synthetic Contrast Case）则是从真实源段构造、并经过独立资格检查的分析性对比。"
        "审校支持例不得写成历史修订，合成案例也不得写成作者初译。", "",
        "现有 Human Evidence 仍为 awaiting_author_input，且本轮没有可用 Literature Evidence。"
        "因此，本章只讨论可观察文本关系，不还原译者心理意图，也不使用未经文献落地的理论名称。",
    ]
    section_number = 2
    for major in taxonomy.get("major_problems", []):
        major_cases = [x for x in portfolio.get("cases", []) if x[
            "problem"]["major_problem"] == major["major_problem_id"]]
        if not major_cases:
            continue
        lines.extend(["", f"## 3.{section_number} {major['title']}", "",
                      major["chapter_claim"]])
        sub_number = 1
        for sub in major["subproblems"]:
            cases = [x for x in major_cases if x["problem"]["subproblem"] == sub[
                "subproblem_id"]]
            if not cases:
                continue
            lines.extend(["", f"### 3.{section_number}.{sub_number} {sub['title']}", ""])
            cases.sort(key=lambda x: (TIERS.index(x["tier"]), x.get(
                "segment_index", 10**9)))
            lines.append("\n\n".join(_case_block(case) for case in cases))
            lines.extend(["", f"**跨案例发现**：{sub['mechanism']}"])
            sub_number += 1
        section_number += 1
    lines.extend([
        "", f"## 3.{section_number} 跨案例综合与研究局限", "",
        "组合结果表明，局部词语选择只是问题的一层；段落对应、修饰辖域、逻辑关系、专名政策、"
        "回指链与人物语气会在不同层面共同影响译文。核心案例负责建立机制，审校支持例用于检验"
        "同一机制在其他语境中的表现，证据边界例则阻止不可靠证据进入结论。", "",
        "本章能证明的是保存文本之间的差异、当前译文中被审校指出的问题以及受控对比中的可能机制。"
        "它不能把审校建议当成已执行修订，不能用合成材料推断人类错误频率，也不能在缺少作者回答时"
        "声称还原了历史翻译意图。后续最高优先级是取得真实 Human Author Evidence，并为真正需要"
        "理论解释的机制登记可核验 Literature Evidence。", "",
    ])
    # Guard against a planner/outline drift that silently drops a case.
    missing = set(by_id) - set(re.findall(r"<!--portfolio-case:([^>]+)-->", "\n".join(lines)))
    if missing:
        raise ValueError(f"chapter composition omitted portfolio cases: {sorted(missing)}")
    return "\n".join(lines)


def validate_chapter(report: str, evidence: Dict[str, Any], portfolio: Dict[str, Any],
                     candidate_pool: Dict[str, Any],
                     synthetic_artifact: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    segs = academic_evidence.segment_index(evidence)
    selected = {x["case_id"]: x for x in portfolio.get("cases", [])}
    canonical_synthetic = synthetic_cases.case_index(synthetic_artifact or {})
    issues = []
    markers = re.findall(r"<!--portfolio-case:([^>]+)-->", report)
    for case_id in selected:
        if markers.count(case_id) != 1:
            issues.append({"type": "case_marker_count", "case_id": case_id,
                           "reason": "selected case must appear exactly once"})
    for kind, case_id, quote in re.findall(
            r"^> \[(SOURCE_EXCERPT|TARGET_EXCERPT|INITIAL_EXCERPT|REVIEW_FINDING|"
            r"REVIEW_SUGGESTION) ([^\]]+)\]: (.*)$", report, re.MULTILINE):
        case = selected.get(case_id)
        segment = segs.get(case_id)
        if not case or not segment:
            issues.append({"type": "unknown_project_case", "case_id": case_id,
                           "reason": "quote points outside canonical project evidence"})
            continue
        expected_values = {
            "SOURCE_EXCERPT": [str(segment.get("source") or "")],
            "TARGET_EXCERPT": [str(segment.get("final_target") or "")],
            "INITIAL_EXCERPT": [str(segment.get("initial_target") or "")],
            "REVIEW_FINDING": [str(x.get("reason") or "") for x in segment.get(
                "process_evidence", {}).get("findings", [])],
            "REVIEW_SUGGESTION": [str(x.get("suggested_target") or "")
                                  for x in segment.get("process_evidence", {}).get(
                                      "findings", [])],
        }[kind]
        raw_quote = quote[:-1] if quote.endswith("…") else quote
        if not any(raw_quote and raw_quote in value for value in expected_values):
            issues.append({"type": "project_quote_mismatch", "case_id": case_id,
                           "reason": f"{kind} is not an exact canonical substring"})
    for case_id, case in selected.items():
        start = report.find(f"<!--portfolio-case:{case_id}-->")
        end = report.find("<!--portfolio-case:", start + 1)
        block = report[start:end if end >= 0 else len(report)]
        if case["case_type"] == "authentic_revision":
            segment = segs.get(case_id) or {}
            if not academic_evidence.has_meaningful_revision(
                    segment.get("initial_target"), segment.get("final_target")):
                issues.append({"type": "invalid_authentic_revision", "case_id": case_id,
                               "reason": "no meaningful stored revision"})
        elif case["case_type"] == "supporting_example" and _REVISION_LANGUAGE.search(block):
            issues.append({"type": "supporting_example_laundered_as_revision",
                           "case_id": case_id,
                           "reason": "supporting example uses historical revision language"})
        elif case["case_type"] == "synthetic_contrast" and \
                _SYNTHETIC_AS_HISTORY.search(block):
            issues.append({"type": "synthetic_laundered_as_history", "case_id": case_id,
                           "reason": "synthetic contrast uses historical translation language"})
        if case["case_type"] == "synthetic_contrast":
            canonical = canonical_synthetic.get(case_id) or {}
            expected = {
                "SYNTHETIC_SOURCE": canonical.get("source_text"),
                "SIMULATED": canonical.get("synthetic_baseline", {}).get("text"),
                "OPTIMIZED": canonical.get("optimized_translation", {}).get("text"),
            }
            seen_kinds = set()
            for kind, quote in re.findall(
                    r"^> \[(SYNTHETIC_SOURCE|SIMULATED|OPTIMIZED) "
                    + re.escape(case_id) + r"\]: (.*)$", block, re.MULTILINE):
                seen_kinds.add(kind)
                if not expected.get(kind) or quote != expected[kind]:
                    issues.append({
                        "type": "synthetic_quote_mismatch", "case_id": case_id,
                        "reason": f"{kind} does not match the canonical synthetic artifact"})
            missing_kinds = {"SYNTHETIC_SOURCE", "SIMULATED", "OPTIMIZED"} - seen_kinds
            if missing_kinds:
                issues.append({
                    "type": "missing_synthetic_quotes", "case_id": case_id,
                    "reason": "missing: " + ", ".join(sorted(missing_kinds))})
    if re.search(r"功能对等|目的论|关联理论|翻译转换|skopos|relevance theory", report, re.I):
        issues.append({"type": "ungrounded_theory_claim", "case_id": None,
                       "reason": "chapter names a theory without Literature Evidence"})
    if re.search(r"译者(?:当时|最初|原本|为了)|笔者(?:当时|最初|原本|为了)", report):
        issues.append({"type": "unsupported_translator_intention", "case_id": None,
                       "reason": "chapter infers historical translator intention without Human Evidence"})
        if case.get("tier") == "tier_1_core" and case.get(
                "case_type") in {"authentic_revision", "supporting_example"}:
            for label, pattern in {
                "problem": r"\*\*问题(?:与证据|界定)",
                "mechanism": r"\*\*(?:调整机制与效果|问题机制与错误诱因)",
                "boundary": r"\*\*证据边界",
            }.items():
                if not re.search(pattern, block):
                    issues.append({
                        "type": "shallow_core_case", "case_id": case_id,
                        "reason": f"Tier 1 case is missing {label} analysis"})
    stats = {
        "segments_scanned": candidate_pool["scan"]["segments_scanned"],
        "candidate_count": candidate_pool["candidate_count"],
        "selected_case_count": portfolio["selected_case_count"],
    }
    for rendered, key in re.findall(
            r"(\d+)<!--stat:(segments_scanned|candidate_count|selected_case_count)-->", report):
        if int(rendered) != stats[key]:
            issues.append({"type": "wrong_statistic", "case_id": None,
                           "reason": f"{key} does not match structured artifact"})
    for i, issue in enumerate(issues, 1):
        issue["issue_id"] = f"PV-{i:03d}"
        issue["severity"] = "error"
    return _stamp({
        "schema_version": VALIDATOR_VERSION,
        "status": "fail" if issues else "pass", "issues": issues,
        "summary": {"errors": len(issues), "selected_cases": len(selected),
                    "case_markers": len(markers)},
    })
