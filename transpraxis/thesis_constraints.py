"""Configurable report-structure metadata for the writing pipeline."""
from __future__ import annotations

from typing import Any, Dict, Mapping


SCHEMA_VERSION = "transpraxis-report-constraints-v1"


def _sections(settings: Mapping[str, Any]) -> list[Dict[str, Any]]:
    raw = settings.get("report_sections") or settings.get("outline_sections") or []
    sections: list[Dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if isinstance(item, str):
            item = {"title": item}
        if not isinstance(item, Mapping):
            continue
        section_id = str(item.get("section_id") or index)
        title = str(item.get("title") or f"Section {section_id}").strip()
        required = []
        for subsection in item.get("required_subsections") or []:
            if isinstance(subsection, str):
                subsection = {"title": subsection}
            if not isinstance(subsection, Mapping):
                continue
            heading_id = str(subsection.get("heading_id") or "").strip()
            heading_title = str(subsection.get("title") or "").strip()
            if heading_id and heading_title:
                required.append({
                    "heading_id": heading_id,
                    "title": heading_title,
                    "level": int(subsection.get("level") or 2),
                    "markdown_prefix": "#" * (int(subsection.get("level") or 2) + 1),
                })
        sections.append({
            "section_id": section_id,
            "title": title,
            "purpose": str(item.get("purpose") or "").strip(),
            "required_subsections": required,
        })
    return sections


def build_constraints(settings: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Return user-supplied report metadata without imposing a template."""
    settings = dict(settings or {})
    sections = _sections(settings)
    language = str(settings.get("body_language") or "").strip()
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "translation_practice_report",
        "body_language": {
            "language": language,
            "status": "configured" if language else "unspecified",
        },
        "document_scope": {
            "body_chapters": [x["section_id"] for x in sections],
            "current_pipeline_scope": "configured_sections",
        },
        "chapters": sections,
        "cross_chapter_chain": list(settings.get("cross_chapter_chain") or []),
        "case_analysis_contract": [
            "problem_and_question_link",
            "source_and_context",
            "recorded_translation_evidence",
            "decision_rationale",
            "bounded_conclusion",
        ],
        "evidence_rules": {
            "do_not_reconstruct_missing_translation": True,
            "do_not_infer_unobserved_intention": True,
            "theory_is_optional_and_must_be_grounded": True,
            "case_count_follows_evidence": True,
        },
        "style_rules": {
            "academic_register": settings.get("writing_style") or "规范、克制、证据驱动的书面语",
            "toc_max_heading_depth": int(settings.get("toc_max_heading_depth") or 3),
        },
    }


def chapter_index(constraints: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(x["section_id"]): dict(x)
            for x in constraints.get("chapters") or []}
