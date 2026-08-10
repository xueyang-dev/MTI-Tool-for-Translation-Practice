"""Deterministic integrity checks for evidence-grounded MTI reports."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from .academic_evidence import literature_index, segment_index, stable_hash
from . import literature_evidence

SCHEMA_VERSION = "academic-validation-v2"
VALIDATOR_VERSION = "validator-v2"

_SEGMENT_REF = re.compile(r"\[(seg-[A-Za-z0-9_-]+-\d{4,})\]")
_QUOTE = re.compile(
    r"^\s*>\s*\[(SOURCE|TARGET)\s+(seg-[A-Za-z0-9_-]+-\d{4,})\]:\s*(.*)$",
    re.MULTILINE,
)
_STAT = re.compile(r"(-?\d[\d,.]*(?:%)?)<!--stat:([A-Za-z0-9_.-]+)-->")
_CITATION = re.compile(
    r"(?:\[@([A-Za-z0-9_.:-]+)\]|<!--cite:([A-Za-z0-9_.:-]+)-->)")
_TERM = re.compile(r"<!--term:([A-Za-z0-9_.:-]+)-->")
_CLAIM = re.compile(r"<!--claim:([A-Za-z0-9_.:-]+)-->")
_RQ = re.compile(r"<!--rq:([A-Za-z0-9_.:-]+)-->")
_LIT_CLAIM = re.compile(r"<!--lit-claim:([A-Za-z0-9_.:-]+)-->")
_LIT_EVIDENCE = re.compile(r"<!--lit-evidence:([A-Za-z0-9_.:-]+)-->")
_LIT_QUOTE = re.compile(
    r"^\s*>\s*\[LITERATURE\s+(LE-[A-Za-z0-9_-]+)\]:\s*(.*)$", re.MULTILINE)
_FORMAL_AUTHOR_YEAR = re.compile(
    r"(?:\b[A-Z][A-Za-z'’-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'’-]+)?\s*"
    r"\((?:19|20)\d{2}[a-z]?\)|\([A-Z][A-Za-z'’-]+(?:\s+et\s+al\.)?,\s*"
    r"(?:19|20)\d{2}[a-z]?\))"
)


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _issue(issue_type: str, reason: str, *, severity: str = "error",
           section_id: Optional[str] = None, claim_id: Optional[str] = None,
           evidence_id: Optional[str] = None,
           suggested_action: str = "") -> Dict[str, Any]:
    return {
        "issue_id": "",
        "type": issue_type,
        "severity": severity,
        "section_id": section_id,
        "claim_id": claim_id,
        "evidence_id": evidence_id,
        "reason": reason,
        "suggested_action": suggested_action,
    }


def _statistics(evidence: Dict[str, Any]) -> Dict[str, Any]:
    return evidence.get("project_evidence", {}).get("statistics", {})


def _value_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def expand_evidence_tokens(text: str, evidence: Dict[str, Any]) -> str:
    """Replace explicit metric/term tokens with values and provenance markers."""
    stats = _statistics(evidence)
    glossary = {str(x.get("id")): x for x in
                evidence.get("project_evidence", {}).get("glossary", [])
                if x.get("id")}
    literature = literature_index(evidence)

    def stat_repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in stats or isinstance(stats[key], (dict, list)):
            return match.group(0)
        return f"{_value_text(stats[key])}<!--stat:{key}-->"

    def term_repl(match: re.Match) -> str:
        key = match.group(1)
        entry = glossary.get(key)
        if not entry:
            return match.group(0)
        value = entry.get("preferred") or entry.get("target") or entry.get("source") or key
        return f"{value}<!--term:{key}-->"

    def cite_repl(match: re.Match) -> str:
        key = match.group(1)
        source = literature.get(key)
        if not source:
            return match.group(0)
        citation = source.get("citation_metadata") or source.get("citation") or {}
        visible = str(citation.get("in_text") or "").strip()
        if not visible:
            authors = source.get("authors") or []
            author = str(authors[0]).strip() if authors else ""
            surname = author.split()[-1] if author else ""
            year = str(source.get("year") or "").strip()
            if surname and year:
                visible = f"{surname}（{year}）"
            elif source.get("title"):
                visible = f"《{source['title']}》"
            else:
                visible = key
        return f"{visible}<!--cite:{key}-->"

    text = re.sub(r"\{\{STAT:([A-Za-z0-9_.-]+)\}\}", stat_repl, text)
    text = re.sub(r"\{\{TERM:([A-Za-z0-9_.:-]+)\}\}", term_repl, text)
    return re.sub(r"\[@([A-Za-z0-9_.:-]+)\]", cite_repl, text)


def _section_map(report_md: str, outline: Dict[str, Any]) -> Dict[str, str]:
    wanted = [str(x.get("section_id")) for x in outline.get("sections", [])]
    positions = []
    for match in re.finditer(r"^##\s+([^\s]+)(?:\s+.*)?$", report_md, re.MULTILINE):
        if match.group(1) in wanted:
            positions.append((match.group(1), match.start(), match.end()))
    out = {}
    for i, (section_id, _start, body_start) in enumerate(positions):
        body_end = positions[i + 1][1] if i + 1 < len(positions) else len(report_md)
        out[section_id] = report_md[body_start:body_end].strip()
    return out


def validate_academic_report(
    report_md: str,
    evidence: Dict[str, Any],
    research_model: Dict[str, Any],
    argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any],
    outline: Dict[str, Any],
    literature_sources_artifact: Optional[Dict[str, Any]] = None,
    literature_evidence_artifact: Optional[Dict[str, Any]] = None,
    literature_claims_artifact: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate identity, provenance, statistics, citations and structure."""
    issues: List[Dict[str, Any]] = []
    segs = segment_index(evidence)
    if literature_sources_artifact is None:
        literature_sources_artifact = {
            "sources": list(literature_index(evidence).values())}
    literature = literature_evidence.source_index(literature_sources_artifact)
    lit_evidence = literature_evidence.evidence_index(
        literature_evidence_artifact or {})
    lit_claims = literature_evidence.claim_index(literature_claims_artifact or {})
    claims = {str(c.get("claim_id")): c for c in argument_plan.get("claims", [])}
    rqs = {str(r.get("rq_id")): r for r in research_model.get("research_questions", [])}
    glossary = {str(x.get("id")): x for x in
                evidence.get("project_evidence", {}).get("glossary", [])
                if x.get("id")}
    stats = _statistics(evidence)
    sections = _section_map(report_md, outline)

    if not report_md.strip():
        issues.append(_issue("empty_report", "报告内容为空。"))

    # Literature source -> exact block -> literature evidence -> literature
    # claim -> global claim integrity.  Source existence alone is never support.
    for source_id, source in literature.items():
        citation = source.get("citation_metadata") or source.get("citation") or {}
        if citation.get("title") and _norm(citation.get("title")) != _norm(source.get("title")):
            issues.append(_issue(
                "literature_metadata_mismatch",
                f"来源 {source_id} 的 citation title 与注册题名不一致。",
                evidence_id=source_id))
        if citation.get("year") and str(citation.get("year")) != str(source.get("year")):
            issues.append(_issue(
                "literature_metadata_mismatch",
                f"来源 {source_id} 的 citation year 与注册年份不一致。",
                evidence_id=source_id))
        citation_authors = citation.get("authors")
        if citation_authors and [_norm(x) for x in citation_authors] != [
                _norm(x) for x in source.get("authors") or []]:
            issues.append(_issue(
                "literature_metadata_mismatch",
                f"来源 {source_id} 的 citation authors 与注册作者不一致。",
                evidence_id=source_id))
        block_hashes = []
        for block in source.get("content_blocks") or []:
            identity = {
                "source_id": source_id, "location": block.get("location"),
                "text": block.get("text"), "provenance": block.get("provenance"),
                "origin_id": block.get("origin_id"),
            }
            expected_block_hash = stable_hash(identity)
            expected_block_id = "LB-" + expected_block_hash[:16]
            if block.get("content_hash") != expected_block_hash or block.get(
                    "block_id") != expected_block_id:
                issues.append(_issue(
                    "literature_source_block_hash_mismatch",
                    f"来源 {source_id} 的 block {block.get('block_id')} 哈希或身份无效。",
                    evidence_id=block.get("block_id")))
            block_hashes.append({
                "block_id": block.get("block_id"),
                "content_hash": block.get("content_hash"),
            })
        if block_hashes or source.get("source_file_hash"):
            expected_source_hash = stable_hash({
                "binary_hash": source.get("source_file_hash"), "blocks": block_hashes})
            if source.get("content_hash") != expected_source_hash:
                issues.append(_issue(
                    "literature_source_content_hash_mismatch",
                    f"来源 {source_id} 的内容哈希与保存 block/file snapshot 不一致。",
                    evidence_id=source_id))

    for evidence_id, item in lit_evidence.items():
        source_id = str(item.get("source_id") or "")
        source = literature.get(source_id)
        if not source:
            issues.append(_issue(
                "literature_evidence_source_missing",
                f"文献证据 {evidence_id} 指向不存在的来源 {source_id}。",
                evidence_id=evidence_id))
            continue
        if item.get("source_content_hash") != source.get("content_hash"):
            issues.append(_issue(
                "literature_source_hash_mismatch",
                f"文献证据 {evidence_id} 的来源内容哈希与来源快照不一致。",
                evidence_id=evidence_id))
        if item.get("evidence_type") == "metadata_only":
            continue
        block_id = item.get("source_block_id")
        blocks = {x.get("block_id"): x for x in source.get("content_blocks") or []}
        block = blocks.get(block_id)
        if not block:
            issues.append(_issue(
                "invalid_literature_location",
                f"文献证据 {evidence_id} 的 source block/location 不存在。",
                evidence_id=evidence_id))
            continue
        if block.get("location") != item.get("location"):
            issues.append(_issue(
                "invalid_literature_location",
                f"文献证据 {evidence_id} 的精确位置与来源快照不一致。",
                evidence_id=evidence_id))
        if str(block.get("text") or "") != str(item.get("evidence_text") or ""):
            issues.append(_issue(
                "literature_evidence_text_mismatch",
                f"文献证据 {evidence_id} 的逐字文本与来源快照不一致。",
                evidence_id=evidence_id))
        expected_hash = stable_hash({k: v for k, v in item.items() if k != "content_hash"})
        if item.get("content_hash") != expected_hash:
            issues.append(_issue(
                "literature_evidence_hash_mismatch",
                f"文献证据 {evidence_id} 的内容哈希无效。",
                evidence_id=evidence_id))

    for literature_claim_id, claim in lit_claims.items():
        source_id = str(claim.get("source_id") or "")
        if source_id not in literature:
            issues.append(_issue(
                "literature_claim_source_missing",
                f"文献主张 {literature_claim_id} 指向不存在的来源 {source_id}。",
                evidence_id=literature_claim_id))
        support_ids = [str(x) for x in claim.get("supporting_evidence_ids") or []]
        if not support_ids:
            issues.append(_issue(
                "literature_claim_without_evidence",
                f"文献主张 {literature_claim_id} 没有逐字证据支持。",
                evidence_id=literature_claim_id))
        for evidence_id in support_ids:
            item = lit_evidence.get(evidence_id)
            if not item:
                issues.append(_issue(
                    "literature_claim_unknown_evidence",
                    f"文献主张 {literature_claim_id} 引用未知证据 {evidence_id}。",
                    evidence_id=evidence_id))
            elif item.get("source_id") != source_id or not item.get("eligible_for_claim"):
                issues.append(_issue(
                    "literature_claim_evidence_mismatch",
                    f"文献主张 {literature_claim_id} 与证据 {evidence_id} 的来源或资格不匹配。",
                    evidence_id=evidence_id))
        expected_claim_hash = stable_hash(
            {k: v for k, v in claim.items() if k != "content_hash"})
        if claim.get("content_hash") != expected_claim_hash:
            issues.append(_issue(
                "literature_claim_hash_mismatch",
                f"文献主张 {literature_claim_id} 的内容哈希无效。",
                evidence_id=literature_claim_id))

    for global_claim_id, global_claim in claims.items():
        literature_claim_ids = [str(x) for x in global_claim.get("literature_claims") or []]
        literature_evidence_ids = [str(x) for x in global_claim.get("literature_evidence") or []]
        for literature_claim_id in literature_claim_ids:
            if literature_claim_id not in lit_claims:
                issues.append(_issue(
                    "global_claim_unknown_literature_claim",
                    f"全局论点 {global_claim_id} 引用未知文献主张 {literature_claim_id}。",
                    claim_id=global_claim_id, evidence_id=literature_claim_id))
        allowed_support = {
            evidence_id for literature_claim_id in literature_claim_ids
            for evidence_id in (lit_claims.get(literature_claim_id) or {}).get(
                "supporting_evidence_ids") or []
        }
        for evidence_id in literature_evidence_ids:
            if evidence_id in literature:
                issues.append(_issue(
                    "argument_plan_source_id_without_grounding",
                    f"全局论点 {global_claim_id} 仅引用 paper/source ID {evidence_id}，没有文献主张与逐字证据。",
                    claim_id=global_claim_id, evidence_id=evidence_id))
            elif evidence_id not in lit_evidence:
                issues.append(_issue(
                    "global_claim_unknown_literature_evidence",
                    f"全局论点 {global_claim_id} 引用未知文献证据 {evidence_id}。",
                    claim_id=global_claim_id, evidence_id=evidence_id))
            elif evidence_id not in allowed_support:
                issues.append(_issue(
                    "global_claim_literature_support_mismatch",
                    f"全局论点 {global_claim_id} 的证据 {evidence_id} 不属于其文献主张。",
                    claim_id=global_claim_id, evidence_id=evidence_id))
        support_category = str(global_claim.get("support_category") or "")
        if support_category in {"literature_supported", "mixed_evidence"} and not (
                literature_claim_ids and literature_evidence_ids):
            issues.append(_issue(
                "global_claim_missing_literature_grounding",
                f"全局论点 {global_claim_id} 标记为 {support_category}，但缺少文献主张或逐字证据。",
                claim_id=global_claim_id))

    for seg_id in sorted(set(_SEGMENT_REF.findall(report_md))):
        if seg_id not in segs:
            issues.append(_issue(
                "invented_segment_id", f"不存在的段落引用：{seg_id}",
                evidence_id=seg_id, suggested_action="删除引用或改用证据库中的 segment_id。"))
    planned_case_ids = {str(x.get("case_id")) for x in selected_cases.get("cases", [])}
    for section in outline.get("sections", []):
        planned_case_ids.update(str(x) for x in section.get("cases") or [])
    for seg_id in sorted(set(_SEGMENT_REF.findall(report_md))):
        if seg_id not in planned_case_ids:
            issues.append(_issue(
                "unplanned_segment_reference",
                f"正文引用了未纳入分节案例计划的段落：{seg_id}。",
                evidence_id=seg_id,
                suggested_action="删除该引用，或先在案例选择与提纲中纳入该案例。"))

    for kind, seg_id, quote in _QUOTE.findall(report_md):
        if seg_id not in segs:
            continue
        expected = segs[seg_id]["source" if kind == "SOURCE" else "final_target"]
        if _norm(quote) != _norm(expected):
            issues.append(_issue(
                "wrong_segment_quote",
                f"{kind} 引文与 {seg_id} 的保存文本不一致。",
                evidence_id=seg_id,
                suggested_action="逐字使用学术证据库中的原文或终译。"))

    for rendered, key in _STAT.findall(report_md):
        if key not in stats or isinstance(stats.get(key), (dict, list)):
            issues.append(_issue(
                "unknown_project_statistic", f"未知项目统计：{key}",
                evidence_id=f"metric:{key}", suggested_action="改用 evidence.statistics 中的指标。"))
        elif rendered.replace(",", "") != _value_text(stats[key]).replace(",", ""):
            issues.append(_issue(
                "wrong_project_statistic",
                f"统计 {key} 报告为 {rendered}，证据值为 {_value_text(stats[key])}。",
                evidence_id=f"metric:{key}", suggested_action="使用 {{STAT:%s}} 占位符。" % key))
    if "{{STAT:" in report_md:
        issues.append(_issue("unresolved_statistic_token", "报告仍含未解析的统计占位符。"))

    # Conservative check for numeric claims explicitly framed as project totals.
    project_terms = re.compile(r"本(?:项目|次|文)|全文|段落|审校|复用|术语|发现")
    for line in report_md.splitlines():
        if line.lstrip().startswith(">"):
            continue
        if project_terms.search(line) and re.search(r"\d+(?:\.\d+)?(?:%|段|条|处|次)", line) \
                and "<!--stat:" not in line:
            issues.append(_issue(
                "unmarked_project_statistic",
                f"项目数字缺少统计来源标记：{_norm(line)[:100]}",
                severity="warning",
                suggested_action="改用 {{STAT:metric_name}}，或明确说明该数字不是项目统计。"))

    for evidence_id, quote in _LIT_QUOTE.findall(report_md):
        item = lit_evidence.get(evidence_id)
        if not item:
            issues.append(_issue(
                "unknown_literature_quote_evidence",
                f"文献直接引语引用未知证据 {evidence_id}。",
                evidence_id=evidence_id))
        elif _norm(quote) != _norm(item.get("evidence_text")):
            issues.append(_issue(
                "literature_quote_mismatch",
                f"文献直接引语与 {evidence_id} 的保存文本不一致。",
                evidence_id=evidence_id))
    for literature_claim_id in sorted(set(_LIT_CLAIM.findall(report_md))):
        if literature_claim_id not in lit_claims:
            issues.append(_issue(
                "unknown_literature_claim_marker",
                f"正文包含未知文献主张 marker：{literature_claim_id}。",
                evidence_id=literature_claim_id))
    for evidence_id in sorted(set(_LIT_EVIDENCE.findall(report_md))):
        if evidence_id not in lit_evidence:
            issues.append(_issue(
                "unknown_literature_evidence_marker",
                f"正文包含未知文献证据 marker：{evidence_id}。",
                evidence_id=evidence_id))

    citation_ids = {a or b for a, b in _CITATION.findall(report_md)}
    for source_id in sorted(citation_ids):
        source = literature.get(source_id)
        if not source:
            issues.append(_issue(
                "unknown_literature_citation", f"文献注册表中不存在：{source_id}",
                evidence_id=source_id, suggested_action="删除或先登记并核验该来源。"))
        elif not source.get("citation_allowed") or source.get(
                "allowed_citation_status") == "not_allowed":
            issues.append(_issue(
                "uncitable_literature_source",
                f"来源 {source_id} 的状态不允许正式引用。",
                evidence_id=source_id, suggested_action="核验来源后更新 citation_allowed。"))
        else:
            marker_pattern = (r"(?:\[@" + re.escape(source_id) + r"\]|<!--cite:"
                              + re.escape(source_id) + r"-->)")
            for marker in re.finditer(marker_pattern, report_md):
                line_start = report_md.rfind("\n", 0, marker.start()) + 1
                line_end = report_md.find("\n", marker.end())
                line = report_md[line_start:line_end if line_end >= 0 else len(report_md)]
                visible_line = re.sub(r"\[@[^\]]+\]|<!--.*?-->", "", line)
                years = set(re.findall(r"(?:19|20)\d{2}", visible_line))
                registered_year = str(source.get("year") or "")
                if years and registered_year and registered_year not in years:
                    issues.append(_issue(
                        "citation_metadata_mismatch",
                        f"引用 {source_id} 所在句年份 {sorted(years)} 与注册年份 {registered_year} 不一致。",
                        evidence_id=source_id,
                        suggested_action="按 literature registry 修正作者—年份信息。"))
                visible_author_year = _FORMAL_AUTHOR_YEAR.search(visible_line)
                authors = source.get("authors") or []
                if visible_author_year and authors:
                    author = str(authors[0]).strip()
                    tokens = [x.casefold() for x in author.split() if x]
                    if tokens and not any(x in visible_line.casefold()
                                          for x in (tokens[0], tokens[-1])):
                        issues.append(_issue(
                            "citation_metadata_mismatch",
                            f"引用 {source_id} 所在句作者与注册作者 {author} 不一致。",
                            evidence_id=source_id,
                            suggested_action="按 literature registry 修正作者—年份信息。"))
    for match in _FORMAL_AUTHOR_YEAR.finditer(report_md):
        line_start = report_md.rfind("\n", 0, match.start()) + 1
        line_end = report_md.find("\n", match.end())
        line = report_md[line_start:line_end if line_end >= 0 else len(report_md)]
        if "[@" not in line:
            issues.append(_issue(
                "unregistered_formal_citation",
                f"正式作者—年份引用没有 registry key：{match.group(0)}",
                evidence_id=match.group(0),
                suggested_action="使用 [@source_id] 绑定文献注册表，或删除未核验引用。"))

    for entry_id in sorted(set(_TERM.findall(report_md))):
        if entry_id not in glossary:
            issues.append(_issue(
                "unknown_terminology_decision", f"未知术语决策：{entry_id}",
                evidence_id=entry_id, suggested_action="改用已保存的 glossary entry id。"))
    if "{{TERM:" in report_md:
        issues.append(_issue("unresolved_term_token", "报告仍含未解析的术语占位符。"))

    for plan_section in outline.get("sections", []):
        section_id = str(plan_section.get("section_id"))
        body = sections.get(section_id)
        if body is None:
            issues.append(_issue(
                "missing_required_section", f"缺少提纲要求的章节 {section_id}。",
                section_id=section_id, suggested_action="按 academic-outline 重写该节。"))
            continue
        min_chars = int(plan_section.get("minimum_chars") or 120)
        visible = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        if len(re.sub(r"\s+", "", visible)) < min_chars:
            issues.append(_issue(
                "section_too_short", f"章节 {section_id} 未达到完整性下限 {min_chars} 字符。",
                severity="warning", section_id=section_id,
                suggested_action="补足论证，而不是机械扩写。"))
        for claim_id in plan_section.get("claims") or []:
            if claim_id not in claims:
                issues.append(_issue(
                    "outline_unknown_claim", f"章节 {section_id} 引用未知论点 {claim_id}。",
                    section_id=section_id, claim_id=claim_id))
            elif f"<!--claim:{claim_id}-->" not in body:
                issues.append(_issue(
                    "missing_planned_claim", f"章节 {section_id} 未落实论点 {claim_id}。",
                    section_id=section_id, claim_id=claim_id,
                    suggested_action="围绕该 claim 与其证据补写或调整提纲。"))
        for case_id in plan_section.get("cases") or []:
            if case_id not in segs:
                issues.append(_issue(
                    "outline_unknown_case", f"章节 {section_id} 引用未知案例 {case_id}。",
                    section_id=section_id, evidence_id=case_id))
            elif case_id not in body:
                planned = [str(x) for x in plan_section.get("cases") or []]
                used = sum(1 for x in planned if x in body)
                severity = "error" if used == 0 else "warning"
                issues.append(_issue(
                    "missing_selected_case", f"章节 {section_id} 未使用已选案例 {case_id}。",
                    section_id=section_id, evidence_id=case_id,
                    severity=severity,
                    suggested_action="使用该案例，或重新规划案例选择；"
                                     "若该节已展开部分案例，可删除未展开案例的计划。"))
        for rq_id in plan_section.get("research_questions") or []:
            if rq_id not in rqs:
                issues.append(_issue(
                    "outline_unknown_research_question",
                    f"章节 {section_id} 引用未知研究问题 {rq_id}。",
                    section_id=section_id))
            elif f"<!--rq:{rq_id}-->" not in body:
                issues.append(_issue(
                    "missing_research_question_link",
                    f"章节 {section_id} 未标明对研究问题 {rq_id} 的回应。",
                    severity="warning", section_id=section_id))

        planned_lit_claims = {str(x) for x in plan_section.get(
            "literature_claims") or []}
        planned_lit_evidence = {str(x) for x in plan_section.get(
            "literature_evidence") or []}
        if plan_section.get("literature") and not (
                planned_lit_claims and planned_lit_evidence):
            issues.append(_issue(
                "outline_source_id_without_grounding",
                f"章节 {section_id} 只规划了 paper/source ID，没有文献主张与逐字证据。",
                section_id=section_id))
        for literature_claim_id in planned_lit_claims:
            if literature_claim_id not in lit_claims:
                issues.append(_issue(
                    "outline_unknown_literature_claim",
                    f"章节 {section_id} 引用未知文献主张 {literature_claim_id}。",
                    section_id=section_id, evidence_id=literature_claim_id))
            elif f"<!--lit-claim:{literature_claim_id}-->" not in body:
                issues.append(_issue(
                    "missing_planned_literature_claim",
                    f"章节 {section_id} 未落实文献主张 {literature_claim_id}。",
                    section_id=section_id, evidence_id=literature_claim_id))
        for evidence_id in planned_lit_evidence:
            if evidence_id not in lit_evidence:
                issues.append(_issue(
                    "outline_unknown_literature_evidence",
                    f"章节 {section_id} 引用未知文献证据 {evidence_id}。",
                    section_id=section_id, evidence_id=evidence_id))
            elif f"<!--lit-evidence:{evidence_id}-->" not in body and not re.search(
                    r"\[LITERATURE\s+" + re.escape(evidence_id) + r"\]", body):
                issues.append(_issue(
                    "missing_planned_literature_evidence",
                    f"章节 {section_id} 未使用文献证据 {evidence_id}。",
                    section_id=section_id, evidence_id=evidence_id))
        planned_sources = {str(x) for x in plan_section.get(
            "literature_sources") or []}
        planned_sources.update(
            str(lit_evidence[x].get("source_id")) for x in planned_lit_evidence
            if x in lit_evidence)
        used_sources = {a or b for a, b in _CITATION.findall(body)}
        for source_id in sorted(used_sources - planned_sources):
            issues.append(_issue(
                "section_literature_outside_plan",
                f"章节 {section_id} 引用了计划外文献 {source_id}。",
                section_id=section_id, evidence_id=source_id,
                suggested_action="删除该引用，或先在论证计划中绑定文献主张与证据。"))
        for literature_claim_id in set(_LIT_CLAIM.findall(body)) - planned_lit_claims:
            issues.append(_issue(
                "section_literature_claim_outside_plan",
                f"章节 {section_id} 使用了计划外文献主张 {literature_claim_id}。",
                section_id=section_id, evidence_id=literature_claim_id))
        for evidence_id in set(_LIT_EVIDENCE.findall(body)) - planned_lit_evidence:
            issues.append(_issue(
                "section_literature_evidence_outside_plan",
                f"章节 {section_id} 使用了计划外文献证据 {evidence_id}。",
                section_id=section_id, evidence_id=evidence_id))

    selected_ids = {str(x.get("case_id")) for x in selected_cases.get("cases", [])}
    candidate_ids = {str(x.get("case_id")) for x in evidence.get("candidate_cases", [])}
    for case_id in selected_ids:
        if case_id not in candidate_ids or case_id not in segs:
            issues.append(_issue(
                "invalid_selected_case", f"选中案例不在候选池或证据库中：{case_id}",
                evidence_id=case_id))

    for i, item in enumerate(issues, 1):
        item["issue_id"] = f"AV-{i:03d}"
    counts = Counter(x["severity"] for x in issues)
    status = "fail" if counts.get("error") else (
        "pass_with_warnings" if counts.get("warning") else "pass")
    result = {
        "schema_version": SCHEMA_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "status": status,
        "issues": issues,
        "summary": {
            "errors": counts.get("error", 0),
            "warnings": counts.get("warning", 0),
            "segment_references": len(_SEGMENT_REF.findall(report_md)),
            "statistics_markers": len(_STAT.findall(report_md)),
            "citation_markers": len(_CITATION.findall(report_md)),
            "literature_claim_markers": len(_LIT_CLAIM.findall(report_md)),
            "literature_evidence_markers": len(_LIT_EVIDENCE.findall(report_md)),
            "literature_quote_markers": len(_LIT_QUOTE.findall(report_md)),
            "claim_markers": len(_CLAIM.findall(report_md)),
            "research_question_markers": len(_RQ.findall(report_md)),
        },
    }
    result["content_hash"] = stable_hash({k: v for k, v in result.items()
                                          if k != "content_hash"})
    return result


def render_warnings_markdown(
    validation: Dict[str, Any],
    review: Optional[Dict[str, Any]] = None,
    literature_review: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    quality_dimensions: Optional[Dict[str, str]] = None,
) -> str:
    lines = ["# 学术证据与质量警告", ""]
    lines.append(f"- 确定性验证：{validation.get('status', 'unknown')}")
    if review:
        lines.append(f"- 语义审稿：{review.get('status', 'unknown')}")
    if literature_review:
        lines.append(f"- 文献支持审校：{literature_review.get('status', 'unknown')}")
    if quality_dimensions:
        lines.extend(["", "## 质量维度", ""])
        lines.extend(f"- {key}: {value}" for key, value in quality_dimensions.items())
    limitations = (evidence or {}).get("limitations") or []
    if limitations:
        lines.extend(["", "## 缺失或受限证据", ""])
        lines.extend(f"- {item}" for item in limitations)
    all_issues = list(validation.get("issues") or []) \
        + list((review or {}).get("issues") or []) \
        + list((literature_review or {}).get("issues") or [])
    if all_issues:
        lines.extend(["", "## 未解决问题", ""])
        for item in all_issues:
            lines.append(
                f"- `{item.get('issue_id', '?')}` [{item.get('severity', '?')}] "
                f"{item.get('section_id') or '-'}：{item.get('reason', '')}")
    else:
        lines.extend(["", "未发现确定性来源错误；这不等于学术解释已经由人工确认。"])
    lines.extend(["", "> 自动验证可核对来源身份、结构和可计算的一致性，不能证明理论解释必然正确。"])
    return "\n".join(lines) + "\n"
