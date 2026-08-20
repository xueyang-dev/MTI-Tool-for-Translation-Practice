"""Canonical institutional constraints for MTI translation-practice reports."""
from __future__ import annotations

from typing import Any, Dict, Mapping


SCHEMA_VERSION = "transpraxis-thesis-constraints-v1"
CHINESE_BODY_EFFECTIVE_YEAR = 2026

CHAPTERS = (
    {
        "section_id": "1",
        "title": "引言",
        "purpose": "交代研究背景与意义，提出研究问题，并说明报告结构。",
        "required_subsections": (
            ("1.1", "研究背景及意义"),
            ("1.2", "研究问题"),
            ("1.3", "报告结构"),
        ),
    },
    {
        "section_id": "2",
        "title": "翻译项目概述",
        "purpose": "说明项目事实、本人职责以及译前、译中和译后的真实过程。",
        "required_subsections": (
            ("2.1", "项目简介"),
            ("2.2", "翻译流程"),
            ("2.2.1", "译前准备"),
            ("2.2.2", "翻译过程"),
            ("2.2.3", "译后管理"),
        ),
    },
    {
        "section_id": "3",
        "title": "翻译项目案例分析",
        "purpose": "由源语文本特征识别实际难点，并以真实证据说明对应策略与解决方案。",
        "required_subsections": (
            ("3.1", "源语文本的类型与特征"),
            ("3.2", "翻译难点"),
            ("3.3", "翻译策略与解决方案"),
        ),
    },
    {
        "section_id": "4",
        "title": "总结与反思",
        "purpose": "逐项回答研究问题，提炼项目内经验，并说明局限与改进方向。",
        "required_subsections": (
            ("4.1", "研究问题回应"),
            ("4.2", "实践经验与可迁移方法"),
            ("4.3", "局限与改进方向"),
        ),
    },
)


def build_constraints(settings: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Return the single constraint object shared by planning, writing and validation."""
    settings = dict(settings or {})
    try:
        submission_year = int(settings.get("submission_year") or 2026)
    except (TypeError, ValueError):
        submission_year = 2026
    requested_language = str(settings.get("body_language") or "").strip()
    if submission_year >= CHINESE_BODY_EFFECTIVE_YEAR:
        body_language = "zh-CN"
        language_status = "required"
        language_reason = "学院规则：2026年及以后 MTI 学位论文正文使用中文撰写。"
    else:
        body_language = requested_language or "unspecified"
        language_status = "project_configured"
        language_reason = "2026年前项目按当年学院规则或用户配置处理。"

    chapters = [{
        **{k: v for k, v in chapter.items() if k != "required_subsections"},
        "required_subsections": [
            {"heading_id": heading_id, "title": title,
             "level": heading_id.count(".") + 1,
             "markdown_prefix": "#" * (heading_id.count(".") + 2)}
            for heading_id, title in chapter["required_subsections"]
        ],
    } for chapter in CHAPTERS]
    return {
        "schema_version": SCHEMA_VERSION,
        "degree_type": "MTI",
        "report_type": "translation_practice_report",
        "submission_year": submission_year,
        "body_language": {
            "language": body_language,
            "status": language_status,
            "effective_from": CHINESE_BODY_EFFECTIVE_YEAR,
            "reason": language_reason,
        },
        "document_scope": {
            "front_matter": ["中文摘要", "ABSTRACT", "目录"],
            "body_chapters": [x["section_id"] for x in CHAPTERS],
            "back_matter": ["参考文献", "致谢", "附录"],
            "current_pipeline_scope": "body_chapters",
            "chinese_abstract_chars": [400, 600],
            "keywords_per_language": [5, 8],
        },
        "chapters": chapters,
        "cross_chapter_chain": [
            "research_question",
            "source_text_feature",
            "translation_difficulty",
            "case_evidence",
            "strategy_or_solution",
            "translation_effect",
            "bounded_conclusion",
        ],
        "research_question_policy": {
            "recommended_count": [2, 3],
            "declare_in_chapter": "1",
            "develop_in_chapter": "3",
            "answer_in_chapter": "4",
        },
        "case_analysis_contract": [
            "problem_and_rq_link",
            "source_and_context",
            "recorded_initial_translation_if_available",
            "recorded_final_translation",
            "specific_initial_problem",
            "repair_evidence_or_explicit_evidence_gap",
            "decision_rationale",
            "translation_effect",
            "bounded_case_conclusion",
        ],
        "evidence_rules": {
            "revision_case_requires_recorded_initial_final_difference": True,
            "do_not_reconstruct_initial_translation": True,
            "do_not_infer_translator_intention": True,
            "theory_is_optional_and_must_be_grounded": True,
            "case_count_follows_evidence": True,
            "conclusion_must_not_introduce_new_case_evidence": True,
        },
        "style_rules": {
            "author_reference": "笔者",
            "avoid_first_person_pronoun": "我",
            "academic_register": "规范、克制、问题驱动的中文 MTI 学术书面语",
            "toc_max_heading_depth": 3,
        },
    }


def chapter_index(constraints: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(x["section_id"]): dict(x) for x in constraints.get("chapters") or []}
