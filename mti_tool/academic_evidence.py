"""Canonical evidence store for MTI academic writing.

This module is deliberately deterministic.  It scans the complete saved
translation state, assigns stable identities, computes project statistics and
mines an explainable pool of academically useful candidate cases.  It never
asks a model to count, invent missing history, or verify literature.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import assets
from . import report_evidence

SCHEMA_VERSION = "academic-evidence-v1"
ALLOWED_SOURCE_STATUSES = {
    "verified", "user_provided", "imported_notes", "unverified_candidate",
}
CITABLE_SOURCE_STATUSES = {"verified", "user_provided"}

_SUBORDINATION = re.compile(
    r"\b(?:although|because|before|after|while|whereas|which|that|who|whom|"
    r"whose|when|where|if|unless|since|as|despite|whether)\b",
    re.IGNORECASE,
)
_PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+\s+){0,2}\w+(?:ed|en)\b",
    re.IGNORECASE,
)


def stable_hash(value: Any) -> str:
    """Stable SHA-256 for JSON-compatible academic artifacts."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_literature_registry(
    sources: Optional[Iterable[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Normalize a pragmatic literature registry without inventing metadata."""
    out: List[Dict[str, Any]] = []
    seen = set()
    for i, raw in enumerate(sources or []):
        if not isinstance(raw, dict):
            continue
        source_id = str(raw.get("source_id") or f"source-{i + 1:03d}").strip()
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        status = str(raw.get("source_status") or "unverified_candidate").strip()
        if status not in ALLOWED_SOURCE_STATUSES:
            status = "unverified_candidate"
        authors = raw.get("authors") or []
        if isinstance(authors, str):
            authors = [x.strip() for x in re.split(r"[;；]", authors) if x.strip()]
        citation = raw.get("citation") if isinstance(raw.get("citation"), dict) else {}
        entry = {
            "source_id": source_id,
            "title": str(raw.get("title") or "").strip(),
            "authors": [str(x).strip() for x in authors if str(x).strip()],
            "year": raw.get("year"),
            "citation": citation,
            "concepts": [str(x).strip() for x in (raw.get("concepts") or [])
                         if str(x).strip()],
            "notes": [str(x).strip() for x in (raw.get("notes") or [])
                      if str(x).strip()],
            "source_status": status,
            "citation_allowed": bool(
                raw.get("citation_allowed", status in CITABLE_SOURCE_STATUSES)),
            "verification": raw.get("verification") or None,
        }
        # User-provided metadata may be cited, but remains visibly distinct from
        # independently verified literature.
        if status not in CITABLE_SOURCE_STATUSES:
            entry["citation_allowed"] = False
        out.append(entry)
    return out


def _location(profile: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
    location = {"paragraph": index, "section_id": None, "chapter": None,
                "topic": None, "recorded": False}
    for section in (profile or {}).get("sections") or []:
        start, end = section.get("start_segment"), section.get("end_segment")
        if isinstance(start, int) and isinstance(end, int) and start <= index <= end:
            location.update({
                "section_id": section.get("section_id"),
                "chapter": section.get("section_id"),
                "topic": section.get("topic"),
                "recorded": True,
            })
            break
    return location


def _zone(index: int, total: int) -> str:
    if total <= 1:
        return "beginning"
    ratio = index / max(1, total - 1)
    if ratio < 1 / 3:
        return "beginning"
    if ratio < 2 / 3:
        return "middle"
    return "end"


def _term_density(source: str, glossary: Iterable[Dict[str, Any]]) -> Tuple[int, List[str]]:
    folded = source.casefold()
    ids = []
    for term in glossary:
        needle = str(term.get("source") or "").strip().casefold()
        if needle and needle in folded:
            ids.append(str(term.get("id") or needle))
    return len(ids), ids


def _candidate_features(
    segment: Dict[str, Any],
    glossary: List[Dict[str, Any]],
) -> Dict[str, Any]:
    source = segment["source"]
    findings = segment["process_evidence"]["findings"]
    initial = segment.get("initial_target")
    final = segment.get("final_target") or ""
    term_count, term_ids = _term_density(source, glossary)
    punctuation = len(re.findall(r"[,;:—–\-()\[\]\"“”‘’]", source))
    clauses = len(_SUBORDINATION.findall(source))
    blocking = sum(f.get("severity") == "blocking" for f in findings)
    actionable = sum(f.get("severity") == "actionable" for f in findings)
    informational = sum(f.get("severity") == "informational" for f in findings)
    repaired = bool(initial is not None and initial != final) or any(
        f.get("suggested_target") for f in findings) or bool(
            segment["process_evidence"]["human_actions"])
    conflict = any(bool(f.get("conflict")) for f in findings)
    complete_chain = bool(
        source and initial is not None and final and findings and repaired)

    score = 0.0
    reasons: List[str] = []
    if complete_chain:
        score += 10
        reasons.append("complete_translation_evidence_chain")
    if blocking:
        score += 7 + min(blocking, 2)
        reasons.append("blocking_finding")
    if actionable:
        score += 5 + min(actionable, 3)
        reasons.append("actionable_finding")
    if repaired:
        score += 6
        reasons.append("repair_or_initial_final_change")
    if conflict:
        score += 5
        reasons.append("terminology_conflict")
    if term_count:
        score += min(4, term_count * 1.5)
        reasons.append("terminology_dense")
    if segment.get("from_tm"):
        score += 1
        reasons.append("tm_reuse")
    if len(source) >= 180:
        score += min(5, len(source) / 100)
        reasons.append("long_source")
    if clauses >= 2:
        score += min(4, clauses)
        reasons.append("clause_complexity")
    if punctuation >= 5:
        score += min(3, punctuation / 3)
        reasons.append("punctuation_complexity")
    if _PASSIVE.search(source):
        score += 1.5
        reasons.append("passive_construction")
    if re.search(r"[\"“”‘’]|—|–", source):
        score += 1
        reasons.append("quotation_or_dash_complexity")
    if informational and not (blocking or actionable):
        score += min(1, informational * 0.2)

    return {
        "score": round(score, 3),
        "reasons": reasons,
        "features": {
            "source_chars": len(source),
            "clause_markers": clauses,
            "punctuation_count": punctuation,
            "term_count": term_count,
            "term_entry_ids": term_ids,
            "blocking_findings": blocking,
            "actionable_findings": actionable,
            "informational_findings": informational,
            "repair_evidence": repaired,
            "complete_evidence_chain": complete_chain,
            "terminology_conflict": conflict,
            "tm_reuse": bool(segment.get("from_tm")),
        },
    }


def mine_candidate_cases(
    segments: List[Dict[str, Any]],
    glossary: Optional[List[Dict[str, Any]]] = None,
    max_candidates: int = 80,
) -> List[Dict[str, Any]]:
    """Scan every segment, then retain a bounded, explainable candidate pool."""
    scored = []
    for segment in segments:
        details = _candidate_features(segment, glossary or [])
        scored.append({
            "case_id": segment["segment_id"],
            "segment_id": segment["segment_id"],
            "segment_index": segment["segment_index"],
            "coverage_zone": segment["coverage_zone"],
            **details,
        })
    scored.sort(key=lambda x: (-x["score"], x["segment_index"]))

    # Keep whole-corpus coverage explicit even when the highest scores cluster.
    chosen: Dict[str, Dict[str, Any]] = {}
    per_zone = min(3, max(1, max_candidates // 3))
    for zone in ("beginning", "middle", "end"):
        for item in [x for x in scored if x["coverage_zone"] == zone][:per_zone]:
            if len(chosen) >= max_candidates:
                break
            chosen[item["segment_id"]] = item
    for item in scored:
        if len(chosen) >= max_candidates:
            break
        if item["score"] > 0:
            chosen[item["segment_id"]] = item
    return sorted(chosen.values(), key=lambda x: (-x["score"], x["segment_index"]))


def _project_statistics(state: Dict[str, Any], segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    findings = state.get("findings") or []
    by_severity = Counter(str(f.get("severity") or "unknown") for f in findings)
    by_type = Counter(str(f.get("type") or "unknown") for f in findings)
    repaired = set()
    for segment in segments:
        if segment.get("initial_target") is not None \
                and segment.get("initial_target") != segment.get("final_target"):
            repaired.add(segment["segment_index"])
        if segment["process_evidence"]["repair_history"] or \
                segment["process_evidence"]["human_actions"]:
            repaired.add(segment["segment_index"])
    stats = {
        "total_segments": len(state.get("paras") or state.get("pairs") or []),
        "translated_segments": len(state.get("pairs") or []),
        "reviewed_segments": sum(bool(p.get("reviewed")) for p in state.get("pairs") or []),
        "blocking_findings": by_severity.get("blocking", 0),
        "actionable_findings": by_severity.get("actionable", 0),
        "informational_findings": by_severity.get("informational", 0),
        "repaired_segments": len(repaired),
        "term_conflicts": sum(bool(f.get("conflict")) for f in findings),
        "tm_reuse_count": sum(bool(p.get("from_tm")) for p in state.get("pairs") or []),
        "issue_category_distribution": dict(sorted(by_type.items())),
        "repair_category_distribution": {
            "initial_final_changed": sum(
                p.get("initial_target") is not None
                and p.get("initial_target") != p.get("target")
                for p in state.get("pairs") or []),
            "suggested_target_recorded": sum(bool(f.get("suggested_target")) for f in findings),
            "human_action_recorded": len(state.get("human_actions") or []),
        },
        "coverage_distribution": dict(Counter(s["coverage_zone"] for s in segments)),
    }
    return stats


def build_academic_evidence(
    state: Dict[str, Any],
    job_id: str,
    literature_sources: Optional[Iterable[Dict[str, Any]]] = None,
    max_candidates: int = 80,
) -> Dict[str, Any]:
    """Build the canonical PROJECT/LITERATURE/AUTHOR evidence artifact."""
    pairs = state.get("pairs") or []
    glossary = state.get("glossary") or []
    glossary_by_id = {str(e.get("id")): e for e in glossary if e.get("id")}
    findings_by_seg: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for finding in state.get("findings") or []:
        idx = finding.get("segment_index")
        if isinstance(idx, int):
            findings_by_seg[idx].append(dict(finding))

    segments = []
    for i, pair in enumerate(pairs):
        base = report_evidence.build_segment_evidence(state, job_id, i)
        injected = list(pair.get("glossary_entry_ids") or [])
        segments.append({
            "evidence_type": "PROJECT_EVIDENCE",
            "segment_id": assets.segment_id(job_id, i),
            "segment_index": i,
            "source": pair.get("source", ""),
            "initial_target": pair.get("initial_target"),
            "final_target": pair.get("target", ""),
            "reviewed": bool(pair.get("reviewed")),
            "from_tm": bool(pair.get("from_tm")),
            "coverage_zone": _zone(i, len(pairs)),
            "location": _location(state.get("document_profile"), i),
            "process_evidence": {
                "findings": findings_by_seg.get(i, []),
                "deterministic_findings": base.get("deterministic_findings") or [],
                "review_findings": base.get("review_findings") or [],
                "repair_history": base.get("repair_history") or [],
                "human_actions": base.get("human_actions") or [],
                "terminology_decisions": [glossary_by_id[x] for x in injected
                                          if x in glossary_by_id],
                "injected_glossary_entry_ids": injected,
            },
            "availability": {
                "initial_target": "recorded" if pair.get("initial_target") is not None
                else "not_recorded",
                "findings": "recorded" if i in findings_by_seg else "not_recorded",
                "repair_history": "recorded" if base.get("repair_history")
                else "not_recorded",
                "terminology_decisions": "recorded" if injected else "not_recorded",
                "location": "recorded" if _location(
                    state.get("document_profile"), i)["recorded"] else "not_recorded",
            },
        })

    candidates = mine_candidate_cases(segments, glossary, max_candidates=max_candidates)
    literature = normalize_literature_registry(literature_sources)
    statistics = _project_statistics(state, segments)
    limitations = []
    if any(s["availability"]["initial_target"] == "not_recorded" for s in segments):
        limitations.append(
            "Historical job: initial translations, glossary injection, or repair history may be unavailable.")
    if not literature:
        limitations.append(
            "No literature registry was provided; formal theoretical citations and literature-derived claims are unavailable.")
    elif any(x.get("source_status") == "user_provided" for x in literature):
        limitations.append(
            "User-provided literature metadata is citable by policy but has not been independently verified by this runtime.")
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "evidence_classes": {
            "PROJECT_EVIDENCE": "facts recorded by the translation workflow",
            "LITERATURE_EVIDENCE": "registered external or user-provided sources",
            "AUTHOR_ANALYSIS": "interpretation produced during academic planning/writing",
        },
        "coverage_policy": {
            "segments_scanned": len(segments),
            "scan_scope": "whole_corpus",
            "candidate_limit": max_candidates,
            "zones": ["beginning", "middle", "end"],
            "zone_minimum_candidates": min(3, max(1, len(segments) // 3))
            if segments else 0,
            "bounded": len(segments) > max_candidates,
        },
        "project_evidence": {
            "segments": segments,
            "statistics": statistics,
            "document_profile": state.get("document_profile"),
            "glossary": glossary,
        },
        "literature_evidence": literature,
        "author_analysis": [],
        "candidate_cases": candidates,
        "limitations": limitations,
    }
    artifact["content_hash"] = stable_hash({k: v for k, v in artifact.items()
                                            if k != "content_hash"})
    return artifact


def segment_index(evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {s["segment_id"]: s for s in
            evidence.get("project_evidence", {}).get("segments", [])}


def candidate_index(evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {c["case_id"]: c for c in evidence.get("candidate_cases", [])}


def literature_index(evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {s["source_id"]: s for s in evidence.get("literature_evidence", [])}
