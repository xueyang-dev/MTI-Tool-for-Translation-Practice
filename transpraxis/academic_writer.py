"""Evidence-grounded academic writing orchestration.

The LLM performs semantic planning, prose writing and critique.  This module
owns durable artifacts, dependency hashes, scoped packets, resume behavior and
targeted section repair.  Translation state remains untouched.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from . import academic_evidence
from . import academic_quality
from . import academic_validator
from . import case_analysis
from . import human_evidence
from . import literature_evidence
from . import synthetic_cases
from . import thesis_constraints

PIPELINE_VERSION = "academic-pipeline-v6"
VERSIONS = {
    "evidence_version": academic_evidence.SCHEMA_VERSION,
    "thesis_constraints_version": thesis_constraints.SCHEMA_VERSION,
    "research_model_version": "research-model-v2",
    "literature_sources_version": literature_evidence.SOURCES_VERSION,
    "literature_evidence_version": literature_evidence.EVIDENCE_VERSION,
    "literature_claims_version": literature_evidence.CLAIMS_VERSION,
    "argument_plan_version": "argument-planner-v2",
    "synthetic_opportunity_version": synthetic_cases.OPPORTUNITY_VERSION,
    "synthetic_baseline_version": synthetic_cases.BASELINE_VERSION,
    "synthetic_error_manifest_version": synthetic_cases.ERROR_MANIFEST_VERSION,
    "synthetic_optimizer_version": synthetic_cases.OPTIMIZER_VERSION,
    "synthetic_validation_version": synthetic_cases.VALIDATION_VERSION,
    "case_selection_version": "case-selector-v4",
    "outline_version": "academic-outline-v5",
    "writer_version": "academic-writer-v6",
    "validator_version": academic_validator.VALIDATOR_VERSION,
    "reviewer_version": "academic-reviewer-v1",
    "literature_reviewer_version": "literature-support-reviewer-v1",
    "academic_quality_version": academic_quality.QUALITY_VERSION,
    "case_analysis_version": case_analysis.ANALYSIS_VERSION,
    "human_evidence_version": human_evidence.HUMAN_EVIDENCE_VERSION,
}

ARTIFACT_FILES = {
    "evidence": "academic-evidence.json",
    "research_model": "research-model.json",
    "literature_sources": "literature-sources.json",
    "literature_evidence": "literature-evidence.jsonl",
    "literature_claims": "literature-claims.jsonl",
    "argument_plan": "argument-plan.json",
    "synthetic_opportunities": "synthetic-error-opportunities.jsonl",
    "synthetic_baselines": "synthetic-baselines.jsonl",
    "synthetic_error_manifest": "synthetic-error-manifest.jsonl",
    "synthetic_optimized": "synthetic-optimized-translations.jsonl",
    "synthetic_validation": "synthetic-case-validation.jsonl",
    "selected_cases": "selected-cases.json",
    "outline": "academic-outline.json",
    "sections": "academic-sections.json",
    "validation": "academic-validation.json",
    "review": "academic-review.json",
    "literature_support_review": "literature-support-review.json",
    "academic_quality": "academic-quality-evaluation.json",
    "case_analysis_plans": "case-analysis-plans.json",
    "human_evidence": "human-academic-evidence.jsonl",
    "human_evidence_needs": "human-evidence-needs.json",
    "human_evidence_questions": "human-evidence-questions.json",
    "quality_repair_history": "academic-quality-repair-history.json",
    "repair_history": "academic-repair-history.json",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_academic_state() -> Dict[str, Any]:
    return {
        "pipeline_version": PIPELINE_VERSION,
        "status": "not_started",
        "current_stage": "not_started",
        "quality_status": None,
        "versions": {},
        "artifacts": {},
        "forced_sections": [],
        "stale_reasons": [],
        "last_error": "",
        "updated_at": None,
    }


def _state(state: Dict[str, Any]) -> Dict[str, Any]:
    current = state.get("academic_state")
    base = default_academic_state()
    if isinstance(current, dict):
        for key, value in base.items():
            current.setdefault(key, value)
        base = current
    for key in ("artifact_history", "validation_history", "review_history",
                "literature_review_history", "academic_quality_history", "repair_history"):
        base.pop(key, None)
    for key in ("artifacts", "forced_sections", "stale_reasons", "versions"):
        if not isinstance(base.get(key), (dict if key in ("artifacts", "versions") else list)):
            base[key] = {} if key in ("artifacts", "versions") else []
    state["academic_state"] = base
    return base


def _write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _write_jsonl(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    metadata = {k: v for k, v in value.items() if k not in {"items", "content_hash"}}
    metadata["record_type"] = "artifact_metadata"
    lines = [json.dumps(metadata, ensure_ascii=False, sort_keys=True)]
    lines.extend(json.dumps(item, ensure_ascii=False, sort_keys=True)
                 for item in value.get("items") or [])
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_jsonl(path: Path) -> Optional[Dict[str, Any]]:
    try:
        records = [json.loads(line) for line in path.read_text(
            encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return None
    if not records:
        return None
    metadata = records[0] if records[0].get("record_type") == "artifact_metadata" else {}
    items = records[1:] if metadata else records
    value = {k: v for k, v in metadata.items() if k != "record_type"}
    value["items"] = items
    value["content_hash"] = academic_evidence.stable_hash(items)
    return value


def _write_artifact(path: Path, value: Dict[str, Any]) -> None:
    if path.suffix == ".jsonl":
        _write_jsonl(path, value)
    else:
        _write_json(path, value)


def _read_artifact(path: Path) -> Optional[Dict[str, Any]]:
    return _read_jsonl(path) if path.suffix == ".jsonl" else _read_json(path)


def _save_artifact(
    state: Dict[str, Any], artifact_dir: Path, name: str, value: Dict[str, Any],
    dependency_hash: str, version: str,
) -> Dict[str, Any]:
    academic = _state(state)
    filename = ARTIFACT_FILES[name]
    _write_artifact(artifact_dir / filename, value)
    academic["artifacts"][name] = {
        "file": filename,
        "content_hash": value.get("content_hash") or academic_evidence.stable_hash(value),
        "dependency_hash": dependency_hash,
        "version": version,
        "updated_at": _now(),
    }
    academic["updated_at"] = _now()
    return value


def _load_valid_artifact(
    state: Dict[str, Any], artifact_dir: Path, name: str,
    dependency_hash: str, version: str,
) -> Optional[Dict[str, Any]]:
    record = _state(state)["artifacts"].get(name) or {}
    if record.get("dependency_hash") != dependency_hash or record.get("version") != version:
        return None
    value = _read_artifact(artifact_dir / ARTIFACT_FILES[name])
    if not value:
        return None
    content_hash = value.get("content_hash") or academic_evidence.stable_hash(value)
    return value if content_hash == record.get("content_hash") else None


def _load_reusable_sections(artifact_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Keep same-writer section cache available after an upstream invalidation."""
    value = _read_artifact(artifact_dir / ARTIFACT_FILES["sections"]) or {}
    if value.get("schema_version") != VERSIONS["writer_version"]:
        return {}
    return {str(x.get("section_id")): x for x in value.get("sections", [])
            if x.get("section_id") and x.get("dependency_hash")}


def _section_dependency_hash(
    plan: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any], evidence: Dict[str, Any],
    literature_sources_artifact: Dict[str, Any],
    literature_evidence_artifact: Dict[str, Any],
    literature_claims_artifact: Dict[str, Any],
    case_plans: Dict[str, Any], human_entries: Iterable[Dict[str, Any]],
) -> str:
    """Hash only case-selection state that can affect this section."""
    case_ids = set(plan.get("cases") or [])
    scoped_cases = [x for x in selected_cases.get("cases", [])
                    if x.get("case_id") in case_ids]
    section_id = str(plan.get("section_id") or "")
    return academic_evidence.stable_hash({
        "plan": plan,
        "claims": argument_plan["content_hash"],
        "evidence": evidence["content_hash"],
        "cases": academic_evidence.stable_hash(scoped_cases),
        "synthetic_policy": selected_cases.get("synthetic_contrast_cases", 0)
        if section_id in {"1", "4"} else None,
        "case_count_policy": selected_cases.get("authentic_selection_status")
        if section_id in {"3", "4"} else None,
        "writer": VERSIONS["writer_version"],
        "literature_sources": literature_sources_artifact["sources_metadata_hash"],
        "literature_evidence": literature_evidence_artifact["content_hash"],
        "literature_claims": literature_claims_artifact["content_hash"],
        "case_analysis": academic_evidence.stable_hash([
            {k: p.get(k) for k in (
                "case_id", "problem", "initial_failure", "alternatives",
                "decision_rationale", "translation_effect", "theory_mapping",
                "bounded_conclusion", "human_evidence_ids", "human_evidence")}
            for p in case_plans.get("plans", []) if p.get("case_id") in case_ids]),
        "human_evidence": academic_evidence.stable_hash([
            {k: x.get(k) for k in ("human_evidence_id", "status",
                                   "answer", "question_type")}
            for x in human_entries if str(x.get("case_id")) in case_ids]),
    })


def _invalidate_names(state: Dict[str, Any], names: Sequence[str], reason: str) -> None:
    academic = _state(state)
    for name in names:
        academic["artifacts"].pop(name, None)
    if reason not in academic["stale_reasons"]:
        academic["stale_reasons"].append(reason)
    if set(names) & {"research_model", "argument_plan", "selected_cases", "outline",
                     "sections", "validation", "review"}:
        state["p3_done"] = False
        academic["status"] = "stale"


def sync_versions(state: Dict[str, Any], versions: Optional[Dict[str, str]] = None) -> None:
    """Invalidate only artifacts affected by architecture/prompt version changes."""
    versions = dict(versions or VERSIONS)
    academic = _state(state)
    old = academic.get("versions") or {}
    if old:
        if old.get("evidence_version") != versions["evidence_version"]:
            _invalidate_names(state, list(ARTIFACT_FILES), "evidence schema/version changed")
        elif old.get("literature_sources_version") != versions["literature_sources_version"]:
            _invalidate_names(state, [
                "literature_sources", "literature_evidence", "literature_claims",
                "argument_plan", "outline", "sections", "validation", "review",
                "literature_support_review", "repair_history",
            ], "literature source schema/version changed")
        elif old.get("literature_evidence_version") != versions["literature_evidence_version"]:
            _invalidate_names(state, [
                "literature_evidence", "literature_claims", "argument_plan", "outline",
                "sections", "validation", "review", "literature_support_review",
                "repair_history",
            ], "literature evidence schema/version changed")
        elif old.get("literature_claims_version") != versions["literature_claims_version"]:
            _invalidate_names(state, [
                "literature_claims", "argument_plan", "outline", "sections",
                "validation", "review", "literature_support_review", "repair_history",
            ], "literature claim schema/version changed")
        elif old.get("synthetic_opportunity_version") != \
                versions["synthetic_opportunity_version"]:
            _invalidate_names(state, [
                "synthetic_opportunities", "synthetic_baselines",
                "synthetic_error_manifest", "synthetic_optimized",
                "synthetic_validation", "selected_cases", "case_analysis_plans",
                "outline", "sections", "validation", "review", "academic_quality",
            ], "synthetic difficulty mining version changed")
        elif old.get("synthetic_baseline_version") != \
                versions["synthetic_baseline_version"]:
            _invalidate_names(state, [
                "synthetic_baselines", "synthetic_error_manifest",
                "synthetic_optimized", "synthetic_validation", "selected_cases",
                "case_analysis_plans", "outline", "sections", "validation", "review",
                "academic_quality",
            ], "synthetic baseline generator version changed")
        elif old.get("synthetic_error_manifest_version") != \
                versions["synthetic_error_manifest_version"]:
            _invalidate_names(state, [
                "synthetic_error_manifest", "synthetic_optimized",
                "synthetic_validation", "selected_cases", "case_analysis_plans",
                "outline", "sections", "validation", "review", "academic_quality",
            ], "synthetic diagnosis version changed")
        elif old.get("synthetic_optimizer_version") != \
                versions["synthetic_optimizer_version"]:
            _invalidate_names(state, [
                "synthetic_optimized", "synthetic_validation", "selected_cases",
                "case_analysis_plans", "outline", "sections", "validation", "review",
                "academic_quality",
            ], "synthetic optimizer version changed")
        elif old.get("synthetic_validation_version") != \
                versions["synthetic_validation_version"]:
            _invalidate_names(state, [
                "synthetic_validation", "selected_cases", "case_analysis_plans",
                "outline", "sections", "validation", "review", "academic_quality",
            ], "synthetic validation policy changed")
        elif old.get("thesis_constraints_version") != \
                versions["thesis_constraints_version"] \
                or old.get("research_model_version") != versions["research_model_version"] \
                or old.get("argument_plan_version") != versions["argument_plan_version"] \
                or old.get("case_selection_version") != versions["case_selection_version"] \
                or old.get("outline_version") != versions["outline_version"]:
            _invalidate_names(state, ["research_model", "argument_plan", "selected_cases",
                                      "outline", "sections", "validation", "review",
                                      "literature_support_review", "repair_history"],
                              "academic planning version changed")
        elif old.get("writer_version") != versions["writer_version"]:
            _invalidate_names(state, ["sections", "validation", "review",
                                      "literature_support_review", "repair_history"],
                              "writer version changed")
        elif old.get("validator_version") != versions["validator_version"]:
            _invalidate_names(state, ["validation", "review", "literature_support_review"],
                              "validator version changed")
        elif old.get("reviewer_version") != versions["reviewer_version"]:
            _invalidate_names(state, ["review"], "reviewer version changed")
        elif old.get("literature_reviewer_version") != \
                versions["literature_reviewer_version"]:
            _invalidate_names(state, ["literature_support_review"],
                              "literature reviewer version changed")
        elif old.get("academic_quality_version") != \
                versions["academic_quality_version"]:
            _invalidate_names(state, ["academic_quality", "quality_repair_history"],
                              "academic quality version changed")
        elif old.get("case_analysis_version") != \
                versions["case_analysis_version"]:
            _invalidate_names(state, [
                "case_analysis_plans", "outline", "sections", "validation",
                "review", "literature_support_review", "academic_quality",
                "quality_repair_history", "repair_history",
            ], "case analysis version changed")
    academic["versions"] = versions


def invalidate_academic_state(
    state: Dict[str, Any], scope: str = "all", section_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark academic artifacts stale without touching translation work."""
    if scope == "all":
        names = list(ARTIFACT_FILES)
    elif scope == "planning":
        names = ["literature_claims", "argument_plan", "selected_cases", "outline",
                 "sections", "validation", "review", "literature_support_review",
                 "repair_history"]
    elif scope == "writer":
        names = ["sections", "validation", "review", "literature_support_review",
                 "repair_history"]
    elif scope == "validation":
        names = ["validation", "review", "literature_support_review"]
    elif scope == "review":
        names = ["review"]
    elif scope == "literature_review":
        names = ["literature_support_review"]
    elif scope == "quality":
        names = ["academic_quality", "quality_repair_history"]
    elif scope == "case_analysis":
        names = ["case_analysis_plans", "outline", "sections", "validation",
                 "review", "literature_support_review", "academic_quality",
                 "quality_repair_history", "repair_history"]
    elif scope == "section":
        names = ["validation", "review"]
        if section_id and section_id not in _state(state)["forced_sections"]:
            _state(state)["forced_sections"].append(section_id)
    else:
        raise ValueError(f"未知学术重生成范围：{scope}")
    _invalidate_names(state, names, f"manual regeneration: {scope}")
    state["p3_done"] = False
    _state(state)["status"] = "stale"
    return state


def prepare_academic_inputs(
    state: Dict[str, Any], theory: str,
    research_settings: Optional[Dict[str, Any]] = None,
    literature_sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Persist user inputs and invalidate downstream work when they change."""
    academic = _state(state)
    settings = dict(state.get("research_settings") or {})
    if research_settings:
        settings.update(research_settings)
    settings["theoretical_framework"] = settings.get("theoretical_framework") or [theory]
    literature = list(
        literature_sources if literature_sources is not None
        else state.get("literature_sources") or [])
    settings_hash = academic_evidence.stable_hash(settings)
    literature_input_hash = academic_evidence.stable_hash(
        academic_evidence.normalize_literature_registry(literature))
    old_settings_hash = academic.get("research_settings_hash")
    if old_settings_hash and old_settings_hash != settings_hash:
        _invalidate_names(state, ["research_model", "argument_plan", "selected_cases",
                                  "outline", "sections", "validation", "review",
                                  "literature_support_review", "repair_history"],
                          "research settings changed")
        state["p3_done"] = False
    elif not old_settings_hash and academic.get("input_hash") and \
            academic.get("input_hash") != academic_evidence.stable_hash({
                "settings": settings_hash, "literature": literature_input_hash}):
        _invalidate_names(state, ["research_model", "argument_plan", "selected_cases",
                                  "outline", "sections", "validation", "review",
                                  "literature_support_review", "repair_history"],
                          "legacy academic inputs changed")
        state["p3_done"] = False
    old_literature_hash = academic.get("literature_input_hash")
    if old_literature_hash and old_literature_hash != literature_input_hash:
        _invalidate_names(state, [
            "literature_sources", "argument_plan", "outline", "sections", "validation", "review",
            "literature_support_review", "repair_history",
        ], "literature inputs changed")
        state["p3_done"] = False
    elif state.get("p3_done") and not academic.get("artifacts"):
        # Old prompt-only report: force the compatibility wrapper to back it up
        # and rebuild rather than returning early.
        state["p3_done"] = False
        academic["stale_reasons"].append("legacy report has no academic dependencies")
    translation_hash = academic_evidence.stable_hash({
        "pairs": [
            {k: pair.get(k) for k in ("source", "initial_target", "target", "reviewed",
                                      "from_tm", "glossary_entry_ids", "stale_due_to_glossary")}
            for pair in state.get("pairs") or []
        ],
        "findings": state.get("findings") or [],
        "human_actions": state.get("human_actions") or [],
        "glossary": state.get("glossary") or [],
        "glossary_frozen": state.get("glossary_frozen"),
        "document_profile": state.get("document_profile"),
    })
    old_translation_hash = academic.get("translation_evidence_hash")
    if old_translation_hash and old_translation_hash != translation_hash:
        _invalidate_names(state, [
            "evidence", "synthetic_opportunities", "synthetic_baselines",
            "synthetic_error_manifest", "synthetic_optimized", "synthetic_validation",
            "research_model", "argument_plan", "selected_cases", "outline", "sections",
            "validation", "review", "literature_support_review", "repair_history",
        ], "translation evidence changed")
    academic["translation_evidence_hash"] = translation_hash
    academic["research_settings_hash"] = settings_hash
    academic["literature_input_hash"] = literature_input_hash
    academic["input_hash"] = academic_evidence.stable_hash({
        "settings": settings_hash, "literature": literature_input_hash})
    state["research_settings"] = settings
    state["literature_sources"] = literature
    return settings, literature


def _parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(),
                       flags=re.DOTALL)
    try:
        value = json.loads(candidate)
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", candidate):
        try:
            value, _ = decoder.raw_decode(candidate[match.start():])
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _call_json(
    call_llm: Callable, provider: str, api_key: str, model: str,
    system_prompt: str, user_prompt: str,
) -> Optional[Dict[str, Any]]:
    for attempt in range(2):
        suffix = "" if attempt == 0 else "\n上次返回无法解析；本次只输出合法 JSON 对象。"
        raw = call_llm(provider, api_key, model, system_prompt + suffix,
                       user_prompt, temperature=0.1)
        parsed = _parse_json_object(raw)
        if parsed is not None:
            return parsed
    return None


def _as_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [x.strip() for x in re.split(r"[\n;；]", value) if x.strip()]
    return [str(x).strip() for x in (value or []) if str(x).strip()]


def build_research_model(
    evidence: Dict[str, Any], theory: str,
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    settings = dict(settings or {})
    institutional_constraints = thesis_constraints.build_constraints(settings)
    framework = _as_list(settings.get("theoretical_framework")) or [theory]
    provided_rqs = _as_list(settings.get("research_questions"))
    default_rqs = [
        "源文本的主要语言特征与可证实的翻译难点是什么？",
        f"代表性翻译决策从{framework[0]}视角可作何种有限解释？",
        "术语治理、机器翻译、审校与译后编辑在本项目中呈现了哪些可追溯效果与局限？",
    ]
    rqs = provided_rqs or default_rqs
    profile = evidence.get("project_evidence", {}).get("document_profile") or {}
    artifact = {
        "schema_version": VERSIONS["research_model_version"],
        "research_topic": settings.get("research_topic") or
        f"{profile.get('genre') or '源文本'}翻译实践的证据化分析",
        "research_questions": [
            {"rq_id": f"RQ{i + 1}", "question": question,
             "provenance": "user_confirmed" if provided_rqs else "default_inferred"}
            for i, question in enumerate(rqs)
        ],
        "theoretical_framework": framework,
        "method": settings.get("method") or "基于项目过程证据的案例研究与描述性统计",
        "analysis_dimensions": _as_list(settings.get("analysis_dimensions")) or [
            "文本特征", "术语管理", "翻译策略", "译后编辑与质量控制"],
        "expected_contribution": _as_list(settings.get("expected_contribution")) or [
            "以可追溯项目证据解释翻译决策，而非还原译者不可观察的心理意图",
            "说明机器翻译、术语治理与人工审校的作用边界",
        ],
        "institutional_constraints": institutional_constraints,
        "submission_year": institutional_constraints["submission_year"],
        "body_language": institutional_constraints["body_language"]["language"],
        "writing_style": settings.get("writing_style") or institutional_constraints[
            "style_rules"]["academic_register"],
        "report_requirements": settings.get("report_requirements") or "翻译实践报告",
        "target_words": int(settings.get("target_words") or 4200),
        "settings_provenance": {
            "research_topic": "user_confirmed" if settings.get("research_topic") else "default_inferred",
            "theoretical_framework": "user_confirmed" if settings.get("theoretical_framework")
            else "pipeline_input",
            "method": "user_confirmed" if settings.get("method") else "default_inferred",
            "body_language": "institutional_rule" if institutional_constraints[
                "body_language"]["status"] == "required" else "project_configured",
        },
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _candidate_summaries(evidence: Dict[str, Any], limit: int = 40) -> List[Dict[str, Any]]:
    segs = academic_evidence.segment_index(evidence)
    pool = evidence.get("candidate_cases", [])
    picked: Dict[str, Dict[str, Any]] = {}
    per_zone = max(3, limit // 6)
    for zone in ("beginning", "middle", "end"):
        for item in [x for x in pool if x.get("coverage_zone") == zone][:per_zone]:
            picked[item["case_id"]] = item
    for item in pool:
        if len(picked) >= limit:
            break
        picked[item["case_id"]] = item
    out = []
    for candidate in sorted(picked.values(), key=lambda x: (
            -x.get("score", 0), x.get("segment_index", 0)))[:limit]:
        segment = segs.get(candidate["segment_id"], {})
        out.append({
            **candidate,
            "source": segment.get("source", "")[:600],
            "initial_target": segment.get("initial_target"),
            "final_target": segment.get("final_target", "")[:600],
            "findings": segment.get("process_evidence", {}).get("findings", [])[:5],
        })
    return out


def _fallback_argument_plan(
    research_model: Dict[str, Any], evidence: Dict[str, Any],
) -> Dict[str, Any]:
    candidates = evidence.get("candidate_cases", [])
    stats = evidence.get("project_evidence", {}).get("statistics", {})
    claims = []
    for i, rq in enumerate(research_model.get("research_questions", [])):
        case_ids = [x["case_id"] for x in candidates[i::max(1, len(
            research_model.get("research_questions", [])))][:2]]
        claims.append({
            "claim_id": f"C{i + 1}",
            "claim": f"对 {rq['rq_id']} 的回答必须限定在已记录项目证据与可核验文献范围内。",
            "research_question": rq["rq_id"],
            "project_evidence": case_ids + (["metric:total_segments"] if stats else []),
            "literature_claims": [],
            "literature_evidence": [],
            "support_category": "project_evidence_only",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "low",
            "planned_sections": [str(i + 1)],
            "reasoning": "自动保守规划；需要写作阶段基于所列证据展开。",
            "counterargument": "历史任务可能缺少完整初译与修复记录。",
        })
    return {"claims": claims, "planner_fallback": True}


def build_argument_plan(
    research_model: Dict[str, Any], evidence: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
    literature_sources_artifact: Optional[Dict[str, Any]] = None,
    literature_evidence_artifact: Optional[Dict[str, Any]] = None,
    literature_claims_artifact: Optional[Dict[str, Any]] = None,
    human_evidence_entries: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    system = (
        "你是学术论证规划器。只规划可由输入证据支持的主要论点，不写正文，不补造文献。"
        "必须区分 PROJECT_EVIDENCE、LITERATURE_EVIDENCE 和 AUTHOR_ANALYSIS。"
        "输出 JSON：{\"claims\":[{\"claim_id\":\"C1\",\"claim\":\"...\","
        "\"research_question\":\"RQ1\",\"project_evidence\":[\"seg-...\"或\"metric:...\"],"
        "\"literature_claims\":[\"LC-001\"],\"literature_evidence\":[\"LE-...\"],"
        "\"support_category\":\"project_evidence_only|literature_supported|mixed_evidence|"
        "author_analysis\",\"analysis_type\":\"AUTHOR_ANALYSIS\","
        "\"human_author_evidence\":[\"HE-...\"],"
        "\"confidence\":\"low|medium|high\",\"planned_sections\":[\"1\"],"
        "\"reasoning\":\"...\",\"counterargument\":\"...\"}]}。"
    )
    payload = {
        "research_model": research_model,
        "project_statistics": evidence.get("project_evidence", {}).get("statistics", {}),
        "candidate_cases": _candidate_summaries(evidence),
        "literature_sources": [
            {k: v for k, v in x.items() if k != "content_blocks"}
            for x in (literature_sources_artifact or {}).get("sources", [])],
        "literature_claims": (literature_claims_artifact or {}).get("items", []),
        "literature_evidence": (literature_evidence_artifact or {}).get("items", []),
        "human_author_evidence": [
            {k: x.get(k) for k in ("human_evidence_id", "case_id",
                                   "question_type", "answer")}
            for x in (human_evidence_entries or [])
            if x.get("status") == "user_confirmed"],
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False)) or _fallback_argument_plan(
                         research_model, evidence)
    valid_rqs = {x["rq_id"] for x in research_model.get("research_questions", [])}
    valid_segments = set(academic_evidence.segment_index(evidence))
    valid_human = {
        x.get("human_evidence_id") for x in (human_evidence_entries or [])
        if x.get("status") == "user_confirmed"}
    human_case = {
        x.get("human_evidence_id"): x.get("case_id")
        for x in (human_evidence_entries or [])}
    valid_metrics = {f"metric:{x}" for x in
                     evidence.get("project_evidence", {}).get("statistics", {})}
    source_index = literature_evidence.source_index(literature_sources_artifact or {})
    literature_claims = {
        claim_id: claim for claim_id, claim in literature_evidence.claim_index(
            literature_claims_artifact or {}).items()
        if (source_index.get(claim.get("source_id")) or {}).get("citation_allowed")
        and claim.get("evidence_grounded_status") != "evidence_missing"
    }
    valid_lit_evidence = literature_evidence.evidence_index(
        literature_evidence_artifact or {})
    claims = []
    rejected_source_only = 0
    for i, item in enumerate(raw.get("claims") or []):
        if not isinstance(item, dict):
            continue
        rq = str(item.get("research_question") or "")
        claim_text = str(item.get("claim") or "").strip()
        project = [str(x) for x in item.get("project_evidence") or []
                   if str(x) in valid_segments or str(x) in valid_metrics]
        lit_claim_ids = [str(x) for x in item.get("literature_claims") or []
                         if str(x) in literature_claims]
        allowed_lit_evidence = {
            evidence_id for claim_id in lit_claim_ids
            for evidence_id in literature_claims[claim_id].get(
                "supporting_evidence_ids") or []
        }
        raw_lit_evidence = [str(x) for x in item.get("literature_evidence") or []]
        literature = [x for x in raw_lit_evidence
                      if x in valid_lit_evidence and x in allowed_lit_evidence]
        human_ids = [
            str(x) for x in item.get("human_author_evidence") or []
            if str(x) in valid_human
            and human_case.get(str(x)) in project]
        rejected_source_only += sum(
            x not in valid_lit_evidence for x in raw_lit_evidence)
        requested_category = str(item.get("support_category") or "")
        if project and lit_claim_ids and literature:
            support_category = "mixed_evidence"
        elif lit_claim_ids and literature:
            support_category = "literature_supported"
        elif project:
            support_category = "project_evidence_only"
        else:
            support_category = "author_analysis"
        if requested_category == "author_analysis" and not project and not literature:
            support_category = "author_analysis"
        if not claim_text or rq not in valid_rqs:
            continue
        analysis_type = str(item.get("analysis_type") or "AUTHOR_ANALYSIS")
        if analysis_type not in ("PROJECT_EVIDENCE", "LITERATURE_EVIDENCE",
                                 "AUTHOR_ANALYSIS"):
            analysis_type = "AUTHOR_ANALYSIS"
        claims.append({
            "claim_id": f"C{len(claims) + 1}",
            "claim": claim_text,
            "research_question": rq,
            "project_evidence": project,
            "literature_claims": lit_claim_ids if literature else [],
            "literature_evidence": literature,
            "human_author_evidence": human_ids,
            "support_category": support_category,
            "analysis_type": analysis_type,
            "confidence": str(item.get("confidence") or "low"),
            "planned_sections": _as_list(item.get("planned_sections")) or ["3"],
            "reasoning": str(item.get("reasoning") or "").strip(),
            "counterargument": str(item.get("counterargument") or "").strip(),
        })
    if not claims:
        claims = _fallback_argument_plan(research_model, evidence)["claims"]
    artifact = {
        "schema_version": VERSIONS["argument_plan_version"],
        "claims": claims,
        "planner_fallback": bool(raw.get("planner_fallback")),
        "rejected_source_only_support": rejected_source_only,
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def select_academic_cases(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    evidence: Dict[str, Any], limit: int = 3,
    synthetic_artifact: Optional[Dict[str, Any]] = None,
    policy: str = "mixed", preferred_authentic_count: int = 3,
    minimum_authentic_count: int = 2,
) -> Dict[str, Any]:
    if policy not in {"authentic_only", "synthetic_only", "mixed"}:
        policy = "mixed"
    revision_pool = academic_evidence.candidate_index(evidence)
    candidates = {case_id: item for case_id, item in revision_pool.items()
                  if item.get("academic_candidate_status", "eligible") == "eligible"}
    eligible_pool = list(candidates.values())
    selected: Dict[str, Dict[str, Any]] = {}
    if policy != "synthetic_only":
        for claim in argument_plan.get("claims", []):
            for evidence_id in claim.get("project_evidence") or []:
                if evidence_id not in candidates:
                    continue
                case = selected.setdefault(evidence_id, {
                    **candidates[evidence_id], "supports_claims": [],
                    "research_questions": [],
                })
                case["supports_claims"].append(claim["claim_id"])
                case["research_questions"].append(claim["research_question"])
        for zone in ("beginning", "middle", "end"):
            item = next((x for x in eligible_pool
                         if x.get("coverage_zone") == zone), None)
            if item and len(selected) < limit:
                selected.setdefault(item["case_id"], {
                    **item, "supports_claims": [], "research_questions": []})
        for item in eligible_pool:
            if len(selected) >= limit:
                break
            selected.setdefault(item["case_id"], {
                **item, "supports_claims": [], "research_questions": []})
    cases = list(selected.values())[:limit]
    authentic_count = len(cases)
    if policy != "authentic_only" and len(cases) < limit:
        segs = academic_evidence.segment_index(evidence)
        for item in synthetic_cases.select_diverse_cases(
                synthetic_artifact or {}, limit - len(cases)):
            source_segment = segs.get(str(item.get("source_segment_id") or "")) or {}
            cases.append({
                **item,
                "coverage_zone": source_segment.get("coverage_zone"),
                "academic_candidate_status": "eligible",
                "supports_claims": [],
                "research_questions": [],
                "selection_rationale": (
                    "eligible synthetic contrast with independently confirmed repair"),
            })
    for case in cases:
        case["supports_claims"] = sorted(set(case["supports_claims"]))
        case["research_questions"] = sorted(set(case["research_questions"]))
        if case.get("case_type") == "authentic_revision":
            case["selection_rationale"] = (
                "；".join(case.get("reasons") or []) or "whole-corpus coverage")
    minimum = min(minimum_authentic_count, preferred_authentic_count)
    if policy == "synthetic_only":
        authentic_status = "not_applicable"
        recommendations = []
        scarcity_disclosure = ""
    elif authentic_count >= preferred_authentic_count:
        authentic_status = "sufficient_revision_cases"
        recommendations: List[str] = []
        scarcity_disclosure = ""
    elif authentic_count >= minimum:
        authentic_status = "two_case_fallback"
        recommendations = [
            "retain_verified_authentic_cases",
            "disclose_revision_evidence_scarcity",
            "do_not_backfill_with_ineligible_cases",
            "use_only_explicitly_labeled_eligible_synthetic_contrasts",
        ]
        scarcity_disclosure = (
            f"现有项目证据仅支持 {authentic_count} 个通过修订资格门禁的真实修订案例；"
            "未用弱证据或无真实修订的片段补足第三个案例。")
    else:
        authentic_status = "insufficient_revision_cases"
        recommendations = [
            "recover_historical_translation_versions_or_revision_records",
            "do_not_backfill_with_ineligible_cases",
            "use_only_explicitly_labeled_eligible_synthetic_contrasts",
        ]
        scarcity_disclosure = (
            f"现有项目证据仅支持 {authentic_count} 个通过修订资格门禁的真实修订案例，"
            f"少于最低要求 {minimum} 个。")
    synthetic_count = len(cases) - authentic_count
    selection_status = (
        "mixed_case_selection" if authentic_count and synthetic_count else
        "synthetic_only_selection" if synthetic_count else
        "no_eligible_synthetic_cases" if policy == "synthetic_only" else
        authentic_status)
    artifact = {
        "schema_version": VERSIONS["case_selection_version"],
        "selection_policy": policy,
        "preference_order": (
            "verified authentic revision > eligible synthetic contrast > "
            "weak authentic evidence > unsupported reconstructed history"),
        "eligibility_rule": "case_type_specific_gate",
        "requested_case_count": limit,
        "preferred_core_case_count": preferred_authentic_count,
        "minimum_core_case_count": minimum,
        "case_count_policy": "authentic_and_synthetic_pools_remain_distinct",
        "eligible_case_count": len(candidates),
        "revision_candidate_pool_count": len(revision_pool),
        "eligible_synthetic_case_count": sum(
            x.get("validation", {}).get("academic_case_eligible")
            for x in (synthetic_artifact or {}).get("items", [])),
        "synthetic_pipeline_status": (synthetic_artifact or {}).get(
            "pipeline_status", "not_run"),
        "selected_case_count": len(cases),
        "authentic_revision_cases": authentic_count,
        "synthetic_contrast_cases": synthetic_count,
        "authentic_selection_status": authentic_status,
        "selection_status": selection_status,
        "scarcity_disclosure_required": authentic_status in {
            "two_case_fallback", "insufficient_revision_cases"},
        "synthetic_methodology_disclosure_required": synthetic_count > 0,
        "synthetic_limitation_disclosure_required": synthetic_count > 0,
        "scarcity_disclosure": scarcity_disclosure,
        "scarcity_recommendations": recommendations,
        "cases": cases,
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _fallback_outline(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any],
) -> Dict[str, Any]:
    constraints = research_model.get("institutional_constraints") or \
        thesis_constraints.build_constraints(research_model)
    required_chapters = thesis_constraints.chapter_index(constraints)
    claims = [c["claim_id"] for c in argument_plan.get("claims", [])]
    rqs = [r["rq_id"] for r in research_model.get("research_questions", [])]
    cases = [c["case_id"] for c in selected_cases.get("cases", [])]
    authentic_cases = [c["case_id"] for c in selected_cases.get("cases", [])
                       if c.get("case_type") == "authentic_revision"]
    synthetic_case_ids = [c["case_id"] for c in selected_cases.get("cases", [])
                          if c.get("case_type") == "synthetic_contrast"]
    total = int(research_model.get("target_words") or 4200)
    case_status = selected_cases.get(
        "authentic_selection_status", selected_cases.get("selection_status"))
    scarcity = str(selected_cases.get("scarcity_disclosure") or "")
    analysis_conclusions = ["理论解释必须表述为作者分析而非真实心理意图"]
    conclusion_limits = ["结论强度不得超过项目与文献证据"]
    if case_status == "two_case_fallback" and scarcity:
        analysis_conclusions.append(scarcity)
        conclusion_limits.append("明确披露核心修订案例只有两个，不补造第三案例")
    if synthetic_case_ids:
        analysis_conclusions.append(
            "合成对比案例必须标为模拟初译/优化译文，不能写成作者历史修订")
        conclusion_limits.append(
            "合成案例只展示合理失败模式，不证明人类译者中的发生频率")
    return {"sections": [
        {"section_id": "1", "title": required_chapters["1"]["title"],
         "purpose": required_chapters["1"]["purpose"],
         "required_subsections": required_chapters["1"]["required_subsections"],
         "research_questions": rqs, "claims": claims[:1], "cases": [],
         "literature_claims": [], "literature_evidence": [], "literature_sources": [],
         "required_statistics": ["total_segments", "translated_segments"],
         "target_words": round(total * .2), "minimum_chars": 300,
         "allowed_conclusions": ["仅陈述证据库可支持的项目特征"]},
        {"section_id": "2", "title": required_chapters["2"]["title"],
         "purpose": required_chapters["2"]["purpose"],
         "required_subsections": required_chapters["2"]["required_subsections"],
         "research_questions": rqs[-1:], "claims": claims[-1:], "cases": [],
         "literature_claims": [], "literature_evidence": [], "literature_sources": [],
         "required_statistics": ["reviewed_segments", "tm_reuse_count", "actionable_findings"],
         "target_words": round(total * .25), "minimum_chars": 350,
         "allowed_conclusions": ["区分可观察流程效果与推断"]},
        {"section_id": "3", "title": required_chapters["3"]["title"],
         "purpose": required_chapters["3"]["purpose"],
         "required_subsections": required_chapters["3"]["required_subsections"],
         "research_questions": rqs, "claims": claims, "cases": cases,
         "case_groups": {"authentic_revision": authentic_cases,
                         "synthetic_contrast": synthetic_case_ids},
         "literature_claims": [], "literature_evidence": [], "literature_sources": [],
         "required_statistics": [], "target_words": round(total * .4), "minimum_chars": 600,
         "allowed_conclusions": analysis_conclusions},
        {"section_id": "4", "title": required_chapters["4"]["title"],
         "purpose": required_chapters["4"]["purpose"],
         "required_subsections": required_chapters["4"]["required_subsections"],
         "research_questions": rqs, "claims": claims, "cases": [],
         "literature_claims": [], "literature_evidence": [], "literature_sources": [],
         "required_statistics": ["repaired_segments", "term_conflicts"],
         "target_words": round(total * .15), "minimum_chars": 250,
         "allowed_conclusions": conclusion_limits},
    ], "planner_fallback": True,
        "institutional_constraints": constraints,
        "case_count_policy": {
            "status": case_status,
            "preferred": selected_cases.get("preferred_core_case_count", 3),
            "minimum": selected_cases.get("minimum_core_case_count", 2),
            "selected": len(cases),
            "scarcity_disclosure": scarcity,
        }}


def build_academic_outline(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any], evidence: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
    literature_sources_artifact: Optional[Dict[str, Any]] = None,
    literature_evidence_artifact: Optional[Dict[str, Any]] = None,
    literature_claims_artifact: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    constraints = research_model.get("institutional_constraints") or \
        thesis_constraints.build_constraints(research_model)
    required_chapters = thesis_constraints.chapter_index(constraints)
    system = (
        "你是 MTI 学术提纲规划器。提纲必须服务研究问题，并且只能引用给定 claim、case、"
        "literature claim、literature evidence 和 statistic id。只输出 JSON："
        "{\"sections\":[{\"section_id\":\"1\","
        "\"title\":\"...\",\"purpose\":\"...\",\"research_questions\":[\"RQ1\"],"
        "\"claims\":[\"C1\"],\"cases\":[\"seg-...\"],"
        "\"literature_claims\":[\"LC-001\"],"
        "\"literature_evidence\":[\"LE-...\"],"
        "\"required_statistics\":[\"total_segments\"],\"target_words\":900,"
        "\"minimum_chars\":300,\"allowed_conclusions\":[\"...\"]}]}。"
        "必须严格生成学院规定的四章，section_id 依次为 1、2、3、4；章名、功能和"
        "required_subsections 以 institutional_constraints 为准，不得用通用 IMRaD 或"
        "自由章节替代。第1章提出研究问题，第3章用文本特征、难点、案例和解决方案展开，"
        "第4章逐项回答研究问题且不得引入新案例证据。"
        "案例数量以 selected_cases.case_count_policy 为准；two_case_fallback 是合格的"
        "双案例结构，不得虚构或要求第三个案例，并须在案例分析或结论中披露证据稀缺。"
        "若存在 synthetic_contrast，必须与 authentic_revision 分组，并规划方法说明和局限；"
        "不得把模拟初译写成历史初译。"
    )
    payload = {
        "research_model": research_model,
        "argument_plan": argument_plan,
        "selected_cases": selected_cases,
        "literature_sources": [
            {k: v for k, v in x.items() if k != "content_blocks"}
            for x in (literature_sources_artifact or {}).get("sources", [])],
        "literature_claims": (literature_claims_artifact or {}).get("items", []),
        "literature_evidence": (literature_evidence_artifact or {}).get("items", []),
        "available_statistics": list(evidence.get("project_evidence", {}).get("statistics", {})),
        "institutional_constraints": constraints,
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False)) or _fallback_outline(
                         research_model, argument_plan, selected_cases)
    valid_claims = {x["claim_id"] for x in argument_plan.get("claims", [])}
    valid_cases = {x["case_id"] for x in selected_cases.get("cases", [])}
    valid_rqs = {x["rq_id"] for x in research_model.get("research_questions", [])}
    lit_sources = literature_evidence.source_index(literature_sources_artifact or {})
    lit_evidence = literature_evidence.evidence_index(literature_evidence_artifact or {})
    lit_claims = literature_evidence.claim_index(literature_claims_artifact or {})
    valid_stats = set(evidence.get("project_evidence", {}).get("statistics", {}))
    sections = []
    for i, item in enumerate(raw.get("sections") or []):
        if not isinstance(item, dict):
            continue
        section_id = str(item.get("section_id") or i + 1)
        section_lit_claims = [str(x) for x in item.get("literature_claims") or []
                              if str(x) in lit_claims]
        allowed_evidence = {
            evidence_id for claim_id in section_lit_claims
            for evidence_id in lit_claims[claim_id].get("supporting_evidence_ids") or []
        }
        section_lit_evidence = [
            str(x) for x in item.get("literature_evidence") or []
            if str(x) in lit_evidence and str(x) in allowed_evidence
        ]
        section_sources = sorted({
            lit_evidence[x]["source_id"] for x in section_lit_evidence
            if lit_evidence[x].get("source_id") in lit_sources
        })
        sections.append({
            "section_id": section_id,
            "title": required_chapters.get(section_id, {}).get(
                "title") or str(item.get("title") or f"章节 {section_id}").strip(),
            "purpose": required_chapters.get(section_id, {}).get(
                "purpose") or str(item.get("purpose") or "").strip(),
            "required_subsections": required_chapters.get(section_id, {}).get(
                "required_subsections", []),
            "research_questions": [str(x) for x in item.get("research_questions") or []
                                   if str(x) in valid_rqs],
            "claims": [str(x) for x in item.get("claims") or [] if str(x) in valid_claims],
            "cases": [str(x) for x in item.get("cases") or [] if str(x) in valid_cases],
            "literature_claims": section_lit_claims if section_lit_evidence else [],
            "literature_evidence": section_lit_evidence,
            "literature_sources": section_sources,
            "required_statistics": [str(x) for x in item.get("required_statistics") or []
                                    if str(x) in valid_stats],
            "target_words": max(200, int(item.get("target_words") or 700)),
            "minimum_chars": max(100, int(item.get("minimum_chars") or 200)),
            "allowed_conclusions": _as_list(item.get("allowed_conclusions")),
        })
    if {x["section_id"] for x in sections} != set(required_chapters):
        sections = _fallback_outline(research_model, argument_plan, selected_cases)["sections"]
        fallback = True
    else:
        fallback = bool(raw.get("planner_fallback"))
    # Deterministically guarantee graph coverage; the writer cannot silently lose a claim/RQ.
    section_by_id = {x["section_id"]: x for x in sections}
    analysis = section_by_id["3"]
    conclusion = section_by_id["4"]
    # Institutional chapter roles are deterministic: cases belong to Chapter
    # 3, while Chapter 4 answers the RQs without introducing case evidence.
    for section in sections:
        if section["section_id"] != "3":
            section["cases"] = []
    analysis["cases"] = [str(x.get("case_id")) for x in selected_cases.get(
        "cases", []) if x.get("case_id")]
    for section in (section_by_id["1"], analysis, conclusion):
        section["research_questions"] = sorted(valid_rqs)
    analysis["claims"] = sorted(valid_claims)
    conclusion["claims"] = sorted(valid_claims)
    for claim_id in valid_claims:
        if not any(claim_id in x["claims"] for x in sections):
            analysis["claims"].append(claim_id)
    for rq_id in valid_rqs:
        if not any(rq_id in x["research_questions"] for x in sections):
            analysis["research_questions"].append(rq_id)
    # Bound per-section case load and guarantee every selected case has a
    # section.  A section that plans 8 cases cannot realistically develop all
    # of them, which otherwise produces impossible validation errors.
    case_claims: Dict[str, set] = {}
    for claim in argument_plan.get("claims", []):
        for case_id in claim.get("project_evidence") or []:
            case_claims.setdefault(str(case_id), set()).add(claim["claim_id"])
    selected_ids = {str(x.get("case_id")) for x in selected_cases.get("cases", [])}
    selected_by_id = {str(x.get("case_id")): x
                      for x in selected_cases.get("cases", [])}
    for section in sections:
        section["cases"] = section["cases"][:max(4, len(selected_ids))]
    assigned = {case_id for section in sections for case_id in section["cases"]}
    for case_id in sorted(selected_ids - assigned):
        if case_id not in case_claims and selected_by_id.get(case_id, {}).get(
                "case_type") != "synthetic_contrast":
            # Zone-coverage candidates without a claim binding do not need a
            # section; forcing them in would create impossible validation.
            continue
        best = analysis if selected_by_id.get(case_id, {}).get(
            "case_type") == "synthetic_contrast" else max(
                sections, key=lambda x: len(
                    set(x["claims"]) & (case_claims.get(case_id) or set())))
        best["cases"].append(case_id)
    claims_by_id = {x["claim_id"]: x for x in argument_plan.get("claims", [])}
    for section in sections:
        for claim_id in section["claims"]:
            global_claim = claims_by_id.get(claim_id) or {}
            for literature_claim_id in global_claim.get("literature_claims") or []:
                if literature_claim_id in lit_claims and literature_claim_id not in section[
                        "literature_claims"]:
                    section["literature_claims"].append(literature_claim_id)
            for evidence_id in global_claim.get("literature_evidence") or []:
                if evidence_id in lit_evidence and evidence_id not in section[
                        "literature_evidence"]:
                    section["literature_evidence"].append(evidence_id)
        section["literature_sources"] = sorted({
            lit_evidence[x]["source_id"] for x in section["literature_evidence"]
            if x in lit_evidence and lit_evidence[x].get("source_id") in lit_sources
        })
        section["case_groups"] = {
            "authentic_revision": [case_id for case_id in section["cases"]
                                     if selected_by_id.get(case_id, {}).get(
                                         "case_type") == "authentic_revision"],
            "synthetic_contrast": [case_id for case_id in section["cases"]
                                    if selected_by_id.get(case_id, {}).get(
                                        "case_type") == "synthetic_contrast"],
        }
    artifact = {
        "schema_version": VERSIONS["outline_version"],
        "institutional_constraints": constraints,
        "sections": sections,
        "planner_fallback": fallback,
        "case_count_policy": {
            "status": selected_cases.get(
                "authentic_selection_status", selected_cases.get("selection_status")),
            "preferred": selected_cases.get("preferred_core_case_count", 3),
            "minimum": selected_cases.get("minimum_core_case_count", 2),
            "selected": len(selected_cases.get("cases", [])),
            "scarcity_disclosure": selected_cases.get("scarcity_disclosure", ""),
        },
        "case_groups": {
            "authentic_revision": [case_id for case_id, item in selected_by_id.items()
                                     if item.get("case_type") == "authentic_revision"],
            "synthetic_contrast": [case_id for case_id, item in selected_by_id.items()
                                    if item.get("case_type") == "synthetic_contrast"],
        },
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _section_packet(
    section: Dict[str, Any], research_model: Dict[str, Any],
    argument_plan: Dict[str, Any], selected_cases: Dict[str, Any],
    evidence: Dict[str, Any], outline: Dict[str, Any],
    prior_summaries: List[Dict[str, str]],
    literature_sources_artifact: Optional[Dict[str, Any]] = None,
    literature_evidence_artifact: Optional[Dict[str, Any]] = None,
    literature_claims_artifact: Optional[Dict[str, Any]] = None,
    case_analysis_plans: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    claims = {x["claim_id"]: x for x in argument_plan.get("claims", [])}
    cases = {x["case_id"]: x for x in selected_cases.get("cases", [])}
    segments = academic_evidence.segment_index(evidence)
    lit_sources = literature_evidence.source_index(literature_sources_artifact or {})
    lit_evidence = literature_evidence.evidence_index(literature_evidence_artifact or {})
    lit_claims = literature_evidence.claim_index(literature_claims_artifact or {})
    plans = case_analysis.plan_index(case_analysis_plans or {})
    case_term_ids = set()
    for case_id in section.get("cases", []):
        selected = cases.get(case_id) or {}
        source_id = case_id if selected.get("case_type") == "authentic_revision" \
            else selected.get("source_segment_id")
        case_term_ids.update((segments.get(str(source_id)) or {}).get(
            "process_evidence", {}).get("injected_glossary_entry_ids", []))
    all_terms = evidence.get("project_evidence", {}).get("glossary", [])
    if "术语" in (section.get("title", "") + section.get("purpose", "")):
        terminology = all_terms[:30]
    else:
        terminology = [x for x in all_terms if x.get("id") in case_term_ids]
    available_segment_ids = list(segments)
    if len(available_segment_ids) > 40:
        available_segment_ids = available_segment_ids[:39] + [available_segment_ids[-1]]
    available_evidence = [
        {key: (segments.get(segment_id) or {}).get(key)
         for key in ("segment_id", "source", "initial_target", "final_target")}
        for segment_id in available_segment_ids
    ]
    return {
        "research_model": research_model,
        "global_outline": [
            {k: x.get(k) for k in ("section_id", "title", "purpose",
                                    "research_questions", "claims", "cases",
                                    "literature_claims", "literature_evidence")}
            for x in outline.get("sections", [])
        ],
        "current_section": section,
        "claims": [claims[x] for x in section.get("claims", []) if x in claims],
        # This is an index of available evidence, not implicit case selection;
        # only the explicit ``cases`` list may be used as a case in the report.
        "available_segment_ids": available_segment_ids,
        "available_evidence": available_evidence,
        "cases": [{
            **cases[x],
            "evidence": segments.get(x) if cases[x].get(
                "case_type") == "authentic_revision" else cases[x],
        } for x in section.get("cases", []) if x in cases],
        "case_analyses": [{
            **plans[x],
            "analysis_contract_text": case_analysis.render_analysis_contract(plans[x]),
            "contract_completion": case_analysis.contract_completion(plans[x]),
        } for x in section.get("cases", []) if x in plans],
        "literature_sources": [
            {k: v for k, v in lit_sources[x].items() if k != "content_blocks"}
            for x in section.get("literature_sources", []) if x in lit_sources
            and lit_sources[x].get("citation_allowed")],
        "literature_claims": [lit_claims[x] for x in section.get(
            "literature_claims", []) if x in lit_claims],
        "literature_evidence": [lit_evidence[x] for x in section.get(
            "literature_evidence", []) if x in lit_evidence],
        "statistics": {x: evidence.get("project_evidence", {}).get("statistics", {}).get(x)
                       for x in section.get("required_statistics", [])},
        "terminology_decisions": terminology,
        "prior_section_summaries": prior_summaries,
        "writing_constraints": {
            "institutional_constraints": research_model.get(
                "institutional_constraints") or outline.get(
                    "institutional_constraints") or thesis_constraints.build_constraints(
                        research_model),
            "required_subsections": section.get("required_subsections") or [],
            "claim_marker": "<!--claim:C1-->",
            "rq_marker": "<!--rq:RQ1-->",
            "source_quote": "> [SOURCE seg-...]: exact source",
            "initial_quote": "> [INITIAL seg-...]: exact initial target",
            "target_quote": "> [TARGET seg-...]: exact final target",
            "synthetic_source_quote": "> [SYNTHETIC_SOURCE SC-...]: exact source",
            "synthetic_baseline_quote": "> [SIMULATED SC-...]: exact simulated baseline",
            "synthetic_optimized_quote": "> [OPTIMIZED SC-...]: exact AI optimization",
            "project_statistic": "{{STAT:metric_name}}",
            "terminology_decision": "{{TERM:entry_id}}",
            "formal_citation": "[@source_id]",
            "literature_quote": "> [LITERATURE LE-...]: exact evidence text",
            "literature_claim_marker": "<!--lit-claim:LC-001-->",
            "literature_evidence_marker": "<!--lit-evidence:LE-...-->",
            "analysis_contract": "按 case_analyses 中的 analysis_contract_text 逐项落实",
            "evidence_level_policy": (
                "authentic_revision 必须有真实初译→终译；synthetic_contrast 必须通过"
                "独立合成资格门禁；两者不得互相转换"),
            "case_count_policy": {
                "status": selected_cases.get(
                    "authentic_selection_status", selected_cases.get("selection_status")),
                "preferred": selected_cases.get("preferred_core_case_count", 3),
                "minimum": selected_cases.get("minimum_core_case_count", 2),
                "selected": len(selected_cases.get("cases", [])),
                "scarcity_disclosure": selected_cases.get("scarcity_disclosure", ""),
                "required_marker": "<!--case-count-policy:two_case_fallback-->"
                if selected_cases.get(
                    "authentic_selection_status", selected_cases.get(
                        "selection_status")) == "two_case_fallback" else "",
            },
            "synthetic_case_policy": {
                "present": bool(selected_cases.get("synthetic_contrast_cases")),
                "methodology_marker": "<!--synthetic-methodology-->",
                "methodology_disclosure": (
                    "合成对比案例以真实源文为基础，模拟初译与优化译文均为分析阶段生成，"
                    "不代表作者的历史翻译；其合理性、错误实质性与修复有效性分别经过检查。"),
                "limitation_marker": "<!--synthetic-limitation-->",
                "limitation_disclosure": (
                    "合成案例只能展示合理的翻译失败模式，不能证明此类错误在人类译者中的"
                    "实际发生频率。"),
            },
        },
    }


def _write_section(
    packet: Dict[str, Any], call_llm: Callable, provider: str, api_key: str,
    model: str, repair_issues: Optional[List[Dict[str, Any]]] = None,
    existing: str = "",
) -> str:
    repair = bool(repair_issues)
    system = (
        "你是 MTI 证据约束型学术写作者。根据论点计划写当前章节，不得新增主要论点、"
        "项目事实或文献。authentic_revision 必须逐字使用 SOURCE/INITIAL/TARGET；"
        "synthetic_contrast 必须逐字使用 SYNTHETIC_SOURCE/SIMULATED/OPTIMIZED，"
        "并明确称为‘模拟初译’和‘优化译文’。项目数字只能用 {{STAT:key}}；正式文献只能用 [@source_id]；"
        "文献直接引语必须逐字复制 literature_evidence 并使用 LITERATURE 格式；文献释义必须"
        "同时保留 lit-claim 与 lit-evidence marker，并引用对应 source_id；"
        "项目术语决策用 {{TERM:entry_id}}。每个落实的 claim 和 RQ 分别保留 HTML marker。"
        "理论解释必须写成作者分析，例如‘从结果看可解释为’，不得冒充译者真实意图。"
        "无文献证据时，不得从模型记忆补作者、年份、书名或理论命题。只输出章节正文。"
    )
    constraints = (packet.get("writing_constraints") or {}).get(
        "institutional_constraints") or {}
    language = (constraints.get("body_language") or {}).get("language")
    if language == "zh-CN":
        system += (
            " 学院规则要求2026年及以后 MTI 正式论文正文使用简体中文。本节的论述、分析、"
            "标题和过渡语必须使用中文；英文仅限逐字源文/译文引语、术语、专名和参考文献"
            "信息，不得生成英文论述段落。涉及作者本人统一称‘笔者’，不用‘我’。"
        )
    required_subsections = (packet.get("writing_constraints") or {}).get(
        "required_subsections") or []
    if required_subsections:
        system += (
            " 当前章必须按 required_subsections 的顺序使用可见标题，并逐项采用其中的"
            "markdown_prefix，格式为‘markdown_prefix 编号 标题’，不得省略、改名或压平层级。"
        )
    count_policy = (packet.get("writing_constraints") or {}).get(
        "case_count_policy") or {}
    if count_policy.get("status") == "two_case_fallback":
        system += (
            " 本项目采用 two_case_fallback：两个真实修订案例已满足最低核心案例结构。"
            "不得要求、暗示或补写第三案例。当前章节若承担案例分析或结论功能，须明确说明"
            "修订证据稀缺，并逐字保留 <!--case-count-policy:two_case_fallback--> marker；"
            f"可使用的披露语句为：{count_policy.get('scarcity_disclosure')}"
        )
    synthetic_policy = (packet.get("writing_constraints") or {}).get(
        "synthetic_case_policy") or {}
    section_id = str((packet.get("current_section") or {}).get("section_id") or "")
    if synthetic_policy.get("present"):
        system += (
            " 合成案例绝不能使用‘笔者初译为、经审校后修改为、初译阶段出现、最终将其"
            "修改为’等历史过程措辞，也不得称其为常见/普遍人类错误，除非 packet 提供"
            "实证频率证据。允许的表述是‘为考察可能偏差，构造如下模拟初译’。"
        )
        if section_id == "1":
            system += (
                " 本节须包含方法披露及 marker："
                f"{synthetic_policy.get('methodology_disclosure')}"
                f"{synthetic_policy.get('methodology_marker')}。")
        if section_id == "3":
            system += (
                " 若本节含两类案例，使用‘真实修订案例’与‘合成对比案例’两个可见小标题。")
        if section_id == "4":
            system += (
                " 本节须包含局限披露及 marker："
                f"{synthetic_policy.get('limitation_disclosure')}"
                f"{synthetic_policy.get('limitation_marker')}。")
    if packet.get("case_analyses"):
        system += (
            " 案例分析必须按 packet.case_analyses 的 analysis_contract_text 实现："
            "authentic_revision 按历史初译→finding/文本差异→实际修订→历史终译；"
            "synthetic_contrast 按翻译难点→合理模拟错误→错误诱因与诊断→意义/功能失真→"
            "AI 优化→修复机制与有效性→有界结论。备选方案必须标注 historical_alternative / analytical_comparison / "
            "counterfactual_rendering；没有证据的备选一律 counterfactual_rendering）、"
            "最终决策与理由、翻译效果（指明具体维度与文本特征，禁止‘更自然/更准确’式"
            "空泛判断）、理论连接（仅当 theory_mapping 存在；否则禁止提及任何理论名称）、"
            "证据边界与有界结论（只限本案例，禁止外推为一般规则）。必须使用与 case_type"
            "对应的逐字标签，并使正文描述的变化与 artifact 一致。禁止：编造译者意图或"
            "过程历史；提及 packet 之外任何 seg 段号；把反事实备选写成历史事实。证据不足"
            "时明确写‘本项目证据不足以支持…’，并列出 recommended_human_evidence 所需"
            "的人工证据。"
            " 若案例带 human_evidence（作者事后解释），可在 decision_rationale 中引用，"
            "表述为‘作者后来解释/译者后来说明’，并保留 <!--human-ev:HE-...--> marker；"
            "不得把作者事后解释写成项目同期过程；human_evidence 仅限该案例使用，"
            "不得推广为全局翻译原则。"
        )
    if repair:
        system += ("这是定点修订：仅修复给定 issues，保持当前章节的有效论点、证据和 marker，"
                   "输出完整修订后章节，不写修订说明。按 issue 的 repair_action 处理："
                   "add_missing_problem_analysis 补具体翻译问题与证据；add_process_evidence "
                   "只用 packet 中可用过程证据；narrow_claim / narrow 缩小论点范围；"
                   "replace_strategy_label_with_mechanism 用机制解释替换策略标签；"
                   "add_theory_case_mapping 仅在 packet 提供 theory_mapping 时补充映射；"
                   "add_translation_effect_explanation 补效果维度与文本证据；"
                   "remove_fake_process_history 删除无证据的过程/意图断言；"
                   "downgrade_unsupported_quality_claim 删除或降级无据质量判断；"
                   "bound_case_conclusion 将结论限定为本案例。")
    user = {"packet": packet}
    if repair:
        user.update({"existing_section": existing, "issues": repair_issues})
    raw = None
    for attempt in range(2):
        try:
            raw = call_llm(provider, api_key, model, system,
                           json.dumps(user, ensure_ascii=False), temperature=0.2)
            break
        except Exception as exc:
            if attempt == 1:
                raise
            if not _is_transient_llm_error(exc):
                raise
            # Transient network/provider failure: one bounded retry.
            if repair:
                user["retry_notice"] = (
                    "上次调用失败，本次请只输出章节正文，不要输出任何解释。")
            else:
                user["retry_notice"] = "上次调用失败，本次请直接输出章节正文。"
    text = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", (raw or "").strip(),
                  flags=re.DOTALL)
    if not text:
        raise RuntimeError("学术写作模型返回空章节")
    return academic_validator.expand_evidence_tokens(text, packet_to_evidence(packet))


def _is_transient_llm_error(exc: Exception) -> bool:
    module = type(exc).__module__ or ""
    if module.startswith("openai"):
        return True
    message = str(exc).lower()
    return any(keyword in message for keyword in (
        "timeout", "connection", "rate limit", "network"))


def _packet_provenance(packet: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "global_claim_ids": [x.get("claim_id") for x in packet.get("claims", [])],
        "project_evidence_ids": [x.get("case_id") for x in packet.get("cases", [])
                                 if x.get("case_type") == "authentic_revision"],
        "synthetic_case_ids": [x.get("case_id") for x in packet.get("cases", [])
                               if x.get("case_type") == "synthetic_contrast"],
        "literature_claim_ids": [x.get("literature_claim_id")
                                 for x in packet.get("literature_claims", [])],
        "literature_evidence_ids": [x.get("evidence_id")
                                    for x in packet.get("literature_evidence", [])],
        "literature_source_ids": [x.get("source_id")
                                  for x in packet.get("literature_sources", [])],
        "support_categories": sorted({
            str(x.get("support_category")) for x in packet.get("claims", [])
            if x.get("support_category")
        }),
    }


def packet_to_evidence(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal evidence shape used for token expansion in a scoped packet."""
    glossary = list(packet.get("terminology_decisions") or [])
    for case in packet.get("cases", []):
        for term in (case.get("evidence") or {}).get("process_evidence", {}).get(
                "terminology_decisions", []):
            if term not in glossary:
                glossary.append(term)
    return {"project_evidence": {"statistics": packet.get("statistics", {}),
                                  "glossary": glossary},
            "literature_sources": packet.get("literature_sources", [])}


def _compose_report(sections: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"## {item['section_id']} {item['title']}\n\n{item['content'].strip()}"
        for item in sections) + "\n"


_QUOTE_LINE = re.compile(
    r"^>\s*\[(SOURCE|INITIAL|TARGET|SYNTHETIC_SOURCE|SIMULATED|OPTIMIZED)\s+"
    r"([A-Za-z0-9_-]+)\]:\s*(.*)$", re.MULTILINE)


def normalize_report_quotes(
    report_md: str, evidence: Dict[str, Any],
    selected_cases: Optional[Dict[str, Any]] = None,
) -> str:
    """Deterministically replace segment quotes with the exact saved text.

    The writer is instructed to copy quotes verbatim, but a bounded repair loop
    cannot guarantee byte-exact output from every provider.  This pass makes
    the final report quote-consistent by construction while the saved sections
    artifact keeps the model's original prose for auditability.
    """
    segs = academic_evidence.segment_index(evidence)
    selected = {str(x.get("case_id")): x
                for x in (selected_cases or {}).get("cases", [])}

    def repl(match: re.Match) -> str:
        kind, case_id, _ = match.groups()
        if kind in {"SOURCE", "INITIAL", "TARGET"}:
            segment = segs.get(case_id)
            if not segment:
                return match.group(0)
            exact = segment[{"SOURCE": "source", "INITIAL": "initial_target",
                             "TARGET": "final_target"}[kind]]
        else:
            case = selected.get(case_id) or {}
            exact = {
                "SYNTHETIC_SOURCE": case.get("source_text"),
                "SIMULATED": case.get("synthetic_baseline", {}).get("text"),
                "OPTIMIZED": case.get("optimized_translation", {}).get("text"),
            }[kind]
            if not exact:
                return match.group(0)
        return f"> [{kind} {case_id}]: {exact}"

    return _QUOTE_LINE.sub(repl, report_md)


def finalize_report_tokens(
    report_md: str, evidence: Dict[str, Any],
    selected_cases: Optional[Dict[str, Any]] = None,
) -> str:
    """Apply quote normalisation plus full-evidence token expansion.

    The scoped packet only carries a section's planned statistics, but writers
    sometimes emit other globally valid {{STAT:key}} tokens; expanding against
    the full evidence store keeps the final report self-consistent while the
    scoped packet remains the writer's authority during drafting.
    """
    return academic_validator.expand_evidence_tokens(
        normalize_report_quotes(report_md, evidence, selected_cases), evidence)


def _semantic_review(
    report_md: str, research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    outline: Dict[str, Any], selected_cases: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
) -> Dict[str, Any]:
    system = (
        "你是独立的 MTI 学术审稿人，不是写作者。检查不受确定性验证覆盖的推理问题："
        "unsupported_conclusion、weak_evidence、case_claim_mismatch、theory_case_mismatch、"
        "overgeneralization、duplicate_argument、contradiction、descriptive_not_analytical、"
        "chapter_drift、conclusion_too_strong、synthetic_case_presented_as_historical、"
        "unsupported_human_error_frequency_claim。synthetic_contrast 只能作为明确标注的"
        "分析实验，不能支持作者历史过程。还要按 institutional_constraints 检查四章功能与"
        "章际链条：研究问题是否在第1章提出、第3章展开、第4章逐项回答，文本特征—翻译难点"
        "—案例证据—策略/方案—效果—结论是否贯通，以及第4章是否引入了新案例。"
        "只输出 JSON：{\"issues\":[{\"issue_id\":"
        "\"AR-001\",\"section_id\":\"3\",\"type\":\"weak_evidence\","
        "\"claim_id\":\"C1\",\"evidence_ids\":[\"seg-...\"],"
        "\"severity\":\"low|medium|high\",\"reason\":\"...\","
        "\"suggested_action\":\"...\"}]}。不得改写正文。"
    )
    payload = {
        "research_model": research_model,
        "institutional_constraints": research_model.get("institutional_constraints") or {},
        "argument_plan": argument_plan,
        "outline": outline,
        "selected_cases": [
            {"case_id": x.get("case_id"), "case_type": x.get("case_type"),
             "provenance": x.get("provenance")}
            for x in selected_cases.get("cases", [])],
        "report": report_md,
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False))
    valid_sections = {str(x["section_id"]) for x in outline.get("sections", [])}
    valid_claims = {str(x["claim_id"]) for x in argument_plan.get("claims", [])}
    valid_evidence = {str(x["case_id"]) for x in selected_cases.get("cases", [])}
    for claim in argument_plan.get("claims", []):
        valid_evidence.update(str(x) for x in claim.get("project_evidence") or [])
        valid_evidence.update(str(x) for x in claim.get("literature_evidence") or [])
    issues = []
    if raw is None:
        issues.append({
            "issue_id": "AR-001", "section_id": None, "type": "review_failed",
            "claim_id": None, "evidence_ids": [], "severity": "medium",
            "reason": "语义学术审稿未返回可解析的结构化结果。",
            "suggested_action": "重新运行学术审稿。",
        })
    else:
        for i, item in enumerate(raw.get("issues") or []):
            if not isinstance(item, dict):
                continue
            section_id = str(item.get("section_id") or "") or None
            claim_id = str(item.get("claim_id") or "") or None
            if section_id not in valid_sections:
                section_id = None
            if claim_id not in valid_claims:
                claim_id = None
            severity = str(item.get("severity") or "medium").lower()
            if severity not in ("low", "medium", "high"):
                severity = "medium"
            reason = str(item.get("reason") or "").strip()
            action = str(item.get("suggested_action") or "").strip()
            evidence_ids = [x for x in _as_list(item.get("evidence_ids"))
                            if x in valid_evidence]
            if not section_id or not reason or not action:
                continue
            issues.append({
                "issue_id": f"AR-{len(issues) + 1:03d}",
                "section_id": section_id,
                "type": str(item.get("type") or "weak_evidence"),
                "claim_id": claim_id,
                "evidence_ids": evidence_ids,
                "severity": severity,
                "reason": reason,
                "suggested_action": action,
            })
        if raw.get("issues") and not issues:
            issues.append({
                "issue_id": "AR-001", "section_id": None, "type": "review_failed",
                "claim_id": None, "evidence_ids": [], "severity": "medium",
                "reason": "语义审稿只返回了无法定位或不完整的意见。",
                "suggested_action": "重新运行审稿并要求绑定有效 section/claim/evidence id。",
            })
    status = "review_required" if any(x["severity"] in ("medium", "high") for x in issues) \
        else ("pass_with_warnings" if issues else "pass")
    artifact = {"schema_version": VERSIONS["reviewer_version"], "status": status,
                "issues": issues}
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _literature_support_review(
    report_md: str, argument_plan: Dict[str, Any], outline: Dict[str, Any],
    literature_sources_artifact: Dict[str, Any],
    literature_evidence_artifact: Dict[str, Any],
    literature_claims_artifact: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
) -> Dict[str, Any]:
    issue_types = {
        "unsupported_by_evidence", "support_too_weak", "claim_too_broad",
        "claim_stronger_than_source", "quotation_context_mismatch",
        "paraphrase_distorts_source", "theory_case_mismatch",
        "citation_present_but_not_supportive",
    }
    source_ids = set(literature_evidence.source_index(literature_sources_artifact))
    evidence_ids = set(literature_evidence.evidence_index(literature_evidence_artifact))
    literature_claim_ids = set(literature_evidence.claim_index(literature_claims_artifact))
    global_claim_ids = {str(x.get("claim_id")) for x in argument_plan.get("claims", [])}
    section_ids = {str(x.get("section_id")) for x in outline.get("sections", [])}
    used_claim_ids = {
        str(x) for claim in argument_plan.get("claims", [])
        for x in claim.get("literature_claims") or []
    }
    if not used_claim_ids:
        artifact = {
            "schema_version": VERSIONS["literature_reviewer_version"],
            "status": "not_applicable", "issues": [],
            "reviewed_literature_claims": 0,
        }
        artifact["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in artifact.items() if k != "content_hash"})
        return artifact
    all_claims = literature_evidence.claim_index(literature_claims_artifact)
    scoped_claims = [all_claims[x] for x in sorted(used_claim_ids) if x in all_claims]
    scoped_evidence_ids = {
        evidence_id for claim in scoped_claims
        for evidence_id in claim.get("supporting_evidence_ids") or []
    }
    all_evidence = literature_evidence.evidence_index(literature_evidence_artifact)
    scoped_evidence = [all_evidence[x] for x in sorted(scoped_evidence_ids)
                       if x in all_evidence]
    scoped_source_ids = {x.get("source_id") for x in scoped_evidence}
    all_sources = literature_evidence.source_index(literature_sources_artifact)
    scoped_sources = [
        {k: v for k, v in all_sources[x].items() if k != "content_blocks"}
        for x in sorted(scoped_source_ids) if x in all_sources]
    system = (
        "你是独立的 Literature Support Reviewer，以低推断强度核对 Literature Claim、逐字"
        "Literature Evidence、Global Claim 与实际章节。不要改写正文，不检查一般文风。只输出"
        "JSON：{\"issues\":[{\"type\":\"unsupported_by_evidence|support_too_weak|"
        "claim_too_broad|claim_stronger_than_source|quotation_context_mismatch|"
        "paraphrase_distorts_source|theory_case_mismatch|citation_present_but_not_supportive\","
        "\"section_id\":\"3\",\"global_claim_id\":\"C1\","
        "\"literature_claim_id\":\"LC-001\",\"literature_evidence_ids\":[\"LE-...\"],"
        "\"source_id\":\"source-id\",\"severity\":\"low|medium|high\","
        "\"reason\":\"...\",\"repair_action\":\"narrow|replace_evidence|remove|rewrite|"
        "downgrade|mark_author_interpretation\"}]}。每条意见必须能定位到章节和文献主张。"
    )
    payload = {
        "literature_sources": scoped_sources,
        "literature_evidence": scoped_evidence,
        "literature_claims": scoped_claims,
        "argument_plan": argument_plan,
        "outline": outline,
        "report": report_md,
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False))
    issues = []
    if raw is None:
        issues.append({
            "issue_id": "LR-001", "type": "unsupported_by_evidence",
            "section_id": None, "global_claim_id": None,
            "literature_claim_id": None, "literature_evidence_ids": [],
            "source_id": None, "severity": "medium",
            "reason": "文献支持审校未返回可解析的结构化结果。",
            "repair_action": "downgrade",
        })
    else:
        for item in raw.get("issues") or []:
            if not isinstance(item, dict):
                continue
            section_id = str(item.get("section_id") or "")
            global_claim_id = str(item.get("global_claim_id") or "")
            literature_claim_id = str(item.get("literature_claim_id") or "")
            source_id = str(item.get("source_id") or "")
            if section_id not in section_ids or literature_claim_id not in literature_claim_ids:
                continue
            if global_claim_id not in global_claim_ids:
                global_claim_id = None
            if source_id not in source_ids:
                source_id = None
            item_evidence = [str(x) for x in item.get("literature_evidence_ids") or []
                             if str(x) in evidence_ids]
            issue_type = str(item.get("type") or "unsupported_by_evidence")
            if issue_type not in issue_types:
                issue_type = "unsupported_by_evidence"
            severity = str(item.get("severity") or "medium").lower()
            if severity not in {"low", "medium", "high"}:
                severity = "medium"
            action = str(item.get("repair_action") or "downgrade")
            if action not in {"narrow", "replace_evidence", "remove", "rewrite",
                              "downgrade", "mark_author_interpretation"}:
                action = "downgrade"
            reason = str(item.get("reason") or "").strip()
            if not reason:
                continue
            issues.append({
                "issue_id": f"LR-{len(issues) + 1:03d}", "type": issue_type,
                "section_id": section_id, "global_claim_id": global_claim_id,
                "literature_claim_id": literature_claim_id,
                "literature_evidence_ids": item_evidence,
                "source_id": source_id, "severity": severity,
                "reason": reason, "repair_action": action,
            })
    status = "review_required" if any(x["severity"] in {"medium", "high"}
                                      for x in issues) else (
        "pass_with_warnings" if issues else "pass")
    artifact = {
        "schema_version": VERSIONS["literature_reviewer_version"],
        "status": status, "issues": issues,
        "reviewed_literature_claims": len(used_claim_ids),
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _locate_validation_issues(
    validation: Dict[str, Any], sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    for issue in validation.get("issues", []):
        if issue.get("section_id"):
            continue
        needle = issue.get("evidence_id")
        if needle:
            needles = [str(needle)]
            if str(needle).startswith("metric:"):
                needles.append(str(needle).split(":", 1)[1])
            for section in sections:
                if any(x in section.get("content", "") for x in needles):
                    issue["section_id"] = section["section_id"]
                    break
    return validation


def _apply_case_replacements(
    replacements: List[Dict[str, Any]], selected_cases: Dict[str, Any],
    argument_plan: Dict[str, Any], outline: Dict[str, Any],
    evidence: Dict[str, Any],
    synthetic_validation_artifact: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """Replace weak/misaligned cases and propagate to plan/outline/sections."""
    cases = list(selected_cases.get("cases", []))
    case_by_id = {str(x.get("case_id")): x for x in cases}
    claims_by_id = {x["claim_id"]: x for x in argument_plan.get("claims", [])}
    affected_sections: set = set()
    performed: List[Dict[str, Any]] = []
    for replacement in replacements:
        old_id = str(replacement.get("case_id") or "")
        old = case_by_id.get(old_id)
        if not old:
            continue
        claim_ids = [str(x) for x in old.get("supports_claims") or []]
        new_candidate = academic_quality.select_replacement_case(
            old_id, claim_ids, selected_cases, argument_plan, evidence,
            synthetic_validation_artifact)
        if not new_candidate:
            continue
        new_id = str(new_candidate["case_id"])
        if new_id in case_by_id:
            continue
        new_case = {
            **new_candidate,
            "supports_claims": sorted(set(claim_ids)),
            "research_questions": sorted(set(old.get("research_questions") or [])),
            "selection_rationale": (
                f"replacement of {old_id}: {replacement.get('reason', '')[:160]}"),
        }
        cases = [new_case if str(x.get("case_id")) == old_id else x for x in cases]
        case_by_id = {str(x.get("case_id")): x for x in cases}
        for claim_id in claim_ids:
            claim = claims_by_id.get(claim_id)
            if not claim:
                continue
            project = claim.get("project_evidence") or []
            claim["project_evidence"] = [
                new_id if str(x) == old_id else x for x in project]
        for section in outline.get("sections", []):
            section_cases = section.get("cases") or []
            if old_id in section_cases:
                section["cases"] = [new_id if x == old_id else x for x in section_cases]
                affected_sections.add(str(section["section_id"]))
        performed.append({
            "old_case_id": old_id, "new_case_id": new_id,
            "claim_ids": claim_ids, "reason": replacement.get("reason", ""),
            "issue_id": replacement.get("issue_id", ""),
        })
    selected_cases["cases"] = cases
    return selected_cases, argument_plan, outline, performed


def _run_quality_repair_round(
    written: List[Dict[str, Any]], report_md: str, evidence: Dict[str, Any],
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any], outline: Dict[str, Any],
    literature_sources_artifact: Dict[str, Any],
    literature_evidence_artifact: Dict[str, Any],
    literature_claims_artifact: Dict[str, Any],
    synthetic_validation_artifact: Dict[str, Any],
    case_analysis_plans: Dict[str, Any],
    human_evidence_entries: Iterable[Dict[str, Any]],
    quality: Dict[str, Any], validation: Dict[str, Any],
    prior_summaries: List[Dict[str, str]],
    call_llm: Callable, provider: str, api_key: str, model: str,
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any], Dict[str, Any],
           Dict[str, Any], Dict[str, Any], List[Dict[str, Any]],
           List[Dict[str, Any]]]:
    """One bounded quality-repair round: replace weak cases, rewrite affected
    sections, re-validate and re-review. Returns updated artifacts and the
    round ledger (before/after hashes)."""
    plan = academic_quality.quality_repair_plan(quality, outline)
    affected_sections: set = set()
    performed_replacements: List[Dict[str, Any]] = []
    if plan["case_replacements"]:
        selected_cases, argument_plan, outline, performed = _apply_case_replacements(
            plan["case_replacements"], selected_cases, argument_plan, outline, evidence,
            synthetic_validation_artifact)
        performed_replacements = performed
        new_ids = {x["new_case_id"] for x in performed}
        affected_sections.update(
            str(x["section_id"]) for x in outline.get("sections", [])
            if new_ids & set(x.get("cases") or []))
    text_by_section: Dict[str, List[Dict[str, Any]]] = {}
    for item in plan["text_repairs"]:
        if item["repair_action"] == "remove":
            continue
        text_by_section.setdefault(item["section_id"], []).append(item)
    affected_sections.update(text_by_section)
    affected_sections = {x for x in affected_sections if x}

    by_id = {x["section_id"]: x for x in written}
    plan_by_id = {x["section_id"]: x for x in outline.get("sections", [])}
    round_ledger: List[Dict[str, Any]] = []
    for sid in sorted(affected_sections):
        if sid not in plan_by_id:
            continue
        packet = _section_packet(
            plan_by_id[sid], research_model, argument_plan, selected_cases, evidence,
            outline, prior_summaries, literature_sources_artifact,
            literature_evidence_artifact, literature_claims_artifact,
            case_analysis_plans)
        issues = [x for x in plan["text_repairs"] if x.get("section_id") == sid]
        # Merge current deterministic validation errors so a quality rewrite
        # cannot silently drop markers, quotes or statistic placeholders.
        validation_errors = [x for x in (validation.get("issues") or [])
                             if x.get("severity") == "error"
                             and str(x.get("section_id")) == sid]
        seen = {x.get("issue_id") for x in issues}
        for issue in validation_errors:
            if issue.get("issue_id") not in seen:
                issues.append(issue)
                seen.add(issue.get("issue_id"))
        old_content = by_id[sid]["content"]
        new_content = _write_section(
            packet, call_llm, provider, api_key, model,
            repair_issues=issues, existing=old_content)
        by_id[sid]["content"] = new_content
        by_id[sid]["summary"] = re.sub(r"<!--.*?-->", "", new_content)[:240]
        by_id[sid]["provenance"] = _packet_provenance(packet)
        round_ledger.append({
            "section_id": sid,
            "issue_ids": [x.get("issue_id") for x in issues],
            "before_hash": academic_evidence.stable_hash(old_content),
            "after_hash": academic_evidence.stable_hash(new_content),
            "repaired_at": _now(),
        })
    written = [by_id[x["section_id"]] for x in outline.get("sections", [])]
    report_md = _compose_report(written)
    report_md = finalize_report_tokens(report_md, evidence, selected_cases)
    validation = academic_validator.validate_academic_report(
        report_md, evidence, research_model, argument_plan, selected_cases, outline,
        literature_sources_artifact, literature_evidence_artifact,
        literature_claims_artifact, human_evidence_entries,
        synthetic_validation_artifact)
    validation = _locate_validation_issues(validation, written)
    review = _semantic_review(
        report_md, research_model, argument_plan, outline, selected_cases,
        call_llm, provider, api_key, model)
    literature_review = _literature_support_review(
        report_md, argument_plan, outline, literature_sources_artifact,
        literature_evidence_artifact, literature_claims_artifact,
        call_llm, provider, api_key, model)
    quality = academic_quality.evaluate_quality(
        research_model, argument_plan, selected_cases, outline, written, evidence,
        literature_sources_artifact, literature_evidence_artifact,
        literature_claims_artifact, validation, call_llm, provider, api_key, model,
        case_analysis_plans)
    return (written, report_md, validation, review, literature_review, quality,
            performed_replacements, round_ledger)


def _quality_status(
    validation: Dict[str, Any], review: Dict[str, Any], evidence: Dict[str, Any],
    literature_sources_artifact: Dict[str, Any],
    literature_evidence_artifact: Dict[str, Any],
    literature_claims_artifact: Dict[str, Any],
    literature_support_review: Dict[str, Any], argument_plan: Dict[str, Any],
) -> Tuple[str, Dict[str, str]]:
    sources = literature_sources_artifact.get("sources") or []
    lit_items = [x for x in literature_evidence_artifact.get("items") or []
                 if x.get("eligible_for_claim")]
    lit_claims = literature_claims_artifact.get("items") or []
    if not sources:
        metadata_status = grounding_status = "not_applicable"
    else:
        metadata_status = "pass" if all(
            x.get("verification_status") == "metadata_verified"
            and (x.get("allowed_citation_status") != "allowed"
                 or x.get("citation_allowed"))
            for x in sources) else "pass_with_warnings"
        if not lit_items or not lit_claims:
            grounding_status = "pass_with_warnings"
        elif any(x.get("evidence_grounded_status") == "needs_review" for x in lit_claims):
            grounding_status = "review_required"
        else:
            grounding_status = "pass"
    dimensions = {
        "project_evidence": "pass" if evidence.get(
            "project_evidence", {}).get("segments") else "fail",
        "literature_metadata": metadata_status,
        "literature_grounding": grounding_status,
        "argument_support": "fail" if any(
            x.get("support_category") in {"literature_supported", "mixed_evidence"}
            and not (x.get("literature_claims") and x.get("literature_evidence"))
            for x in argument_plan.get("claims", [])) else "pass",
        "citation_validation": validation.get("status", "fail"),
        "general_review": review.get("status", "review_required"),
        "literature_support_review": literature_support_review.get(
            "status", "not_applicable"),
    }
    if validation.get("status") == "fail":
        return "fail", dimensions
    if review.get("status") == "review_required" or grounding_status == "review_required" \
            or literature_support_review.get("status") == "review_required":
        return "review_required", dimensions
    if validation.get("status") == "pass_with_warnings" or review.get("issues") \
            or evidence.get("limitations") or metadata_status == "pass_with_warnings" \
            or grounding_status == "pass_with_warnings" \
            or literature_support_review.get("issues"):
        return "pass_with_warnings", dimensions
    return "pass", dimensions


def _legacy_backup(state: Dict[str, Any], artifact_dir: Path) -> None:
    academic = _state(state)
    if academic["artifacts"] or not (state.get("p3_md") or state.get("p3_sections")):
        return
    path = artifact_dir / "legacy-report-before-academic-v1.md"
    if not path.exists() and state.get("p3_md"):
        path.write_text(state["p3_md"], encoding="utf-8")
    sections_path = artifact_dir / "legacy-report-sections-before-academic-v1.json"
    if not sections_path.exists() and state.get("p3_sections"):
        _write_json(sections_path, {"sections": state["p3_sections"]})
    state["p3_md"] = ""
    state["p3_sections"] = []
    state["p3_done"] = False
    academic["stale_reasons"].append("legacy prompt-only report invalidated and backed up")


def run_academic_pipeline(
    state: Dict[str, Any], job_id: str, theory: str,
    provider: str, api_key: str, model: str, artifact_dir: Path,
    call_llm: Callable, save_state: Callable[[Dict[str, Any]], None],
    research_settings: Optional[Dict[str, Any]] = None,
    literature_sources: Optional[Iterable[Dict[str, Any]]] = None,
    on_status: Optional[Callable[[str], None]] = None,
    auto_repair_rounds: int = 1,
    auto_quality_repair_rounds: int = 1,
    human_evidence_sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> str:
    """Run or resume the complete academic evidence-to-repair pipeline."""
    artifact_dir = Path(artifact_dir)
    academic = _state(state)
    validation_runs: List[Dict[str, Any]] = []
    quality_runs: List[Dict[str, Any]] = []
    _legacy_backup(state, artifact_dir)
    sync_versions(state)
    academic.update(status="in_progress", last_error="", updated_at=_now())
    settings, literature = prepare_academic_inputs(
        state, theory, research_settings, literature_sources)
    human_entries = list(
        human_evidence_sources if human_evidence_sources is not None
        else state.get("human_evidence") or [])
    state["human_evidence"] = human_entries

    def stage(name: str, label: str) -> None:
        academic["current_stage"] = name
        academic["status"] = "in_progress"
        if on_status:
            on_status(label)
        save_state(state)

    try:
        stage("evidence", "【学术写作 1/10】构建全语料项目证据库...")
        evidence_new = academic_evidence.build_academic_evidence(
            state, job_id)
        evidence_dep = academic_evidence.stable_hash({
            "translation": evidence_new["content_hash"],
            "version": VERSIONS["evidence_version"],
        })
        evidence = _load_valid_artifact(state, artifact_dir, "evidence", evidence_dep,
                                        VERSIONS["evidence_version"])
        if evidence is None:
            evidence = _save_artifact(state, artifact_dir, "evidence", evidence_new,
                                      evidence_dep, VERSIONS["evidence_version"])

        synthetic_policy = str(settings.get("case_selection_policy") or "mixed")
        if synthetic_policy not in {"authentic_only", "synthetic_only", "mixed"}:
            synthetic_policy = "mixed"
        synthetic_enabled = synthetic_policy != "authentic_only"
        max_scan = max(1, int(settings.get("synthetic_max_scan") or 16))
        max_opportunities = max(1, int(settings.get(
            "synthetic_max_opportunities") or 8))

        stage("synthetic_opportunities", "【学术写作】挖掘合成对比案例的翻译难点...")
        synthetic_opportunity_dep = academic_evidence.stable_hash({
            "evidence": evidence["content_hash"], "enabled": synthetic_enabled,
            "max_scan": max_scan, "max_opportunities": max_opportunities,
            "version": VERSIONS["synthetic_opportunity_version"],
        })
        synthetic_opportunities = _load_valid_artifact(
            state, artifact_dir, "synthetic_opportunities", synthetic_opportunity_dep,
            VERSIONS["synthetic_opportunity_version"])
        if synthetic_opportunities is None:
            synthetic_opportunities = synthetic_cases.mine_error_opportunities(
                evidence, call_llm, provider, api_key, model, max_scan, max_opportunities) \
                if synthetic_enabled else {
                    "schema_version": VERSIONS["synthetic_opportunity_version"],
                    "items": [], "content_hash": academic_evidence.stable_hash([]),
                    "total_source_segments": len(evidence.get(
                        "project_evidence", {}).get("segments", [])),
                    "screened_segments": 0, "opportunities_found": 0,
                }
            synthetic_opportunities = _save_artifact(
                state, artifact_dir, "synthetic_opportunities", synthetic_opportunities,
                synthetic_opportunity_dep, VERSIONS["synthetic_opportunity_version"])

        stage("synthetic_baselines", "【学术写作】生成分析用模拟初译...")
        synthetic_baseline_dep = academic_evidence.stable_hash({
            "opportunities": synthetic_opportunities["content_hash"],
            "version": VERSIONS["synthetic_baseline_version"],
        })
        synthetic_baselines = _load_valid_artifact(
            state, artifact_dir, "synthetic_baselines", synthetic_baseline_dep,
            VERSIONS["synthetic_baseline_version"])
        if synthetic_baselines is None:
            synthetic_baselines = synthetic_cases.generate_baselines(
                synthetic_opportunities, call_llm, provider, api_key, model)
            synthetic_baselines = _save_artifact(
                state, artifact_dir, "synthetic_baselines", synthetic_baselines,
                synthetic_baseline_dep, VERSIONS["synthetic_baseline_version"])

        stage("synthetic_error_manifest", "【学术写作】独立检查模拟初译并诊断错误...")
        synthetic_error_dep = academic_evidence.stable_hash({
            "baselines": synthetic_baselines["content_hash"],
            "version": VERSIONS["synthetic_error_manifest_version"],
        })
        synthetic_error_manifest = _load_valid_artifact(
            state, artifact_dir, "synthetic_error_manifest", synthetic_error_dep,
            VERSIONS["synthetic_error_manifest_version"])
        if synthetic_error_manifest is None:
            synthetic_error_manifest = synthetic_cases.build_error_manifest(
                synthetic_baselines, call_llm, provider, api_key, model)
            synthetic_error_manifest = _save_artifact(
                state, artifact_dir, "synthetic_error_manifest",
                synthetic_error_manifest, synthetic_error_dep,
                VERSIONS["synthetic_error_manifest_version"])

        stage("synthetic_optimization", "【学术写作】生成并约束 AI 优化译文...")
        synthetic_optimizer_dep = academic_evidence.stable_hash({
            "errors": synthetic_error_manifest["content_hash"],
            "terminology": academic_evidence.stable_hash(
                evidence.get("project_evidence", {}).get("glossary", [])),
            "version": VERSIONS["synthetic_optimizer_version"],
        })
        synthetic_optimized = _load_valid_artifact(
            state, artifact_dir, "synthetic_optimized", synthetic_optimizer_dep,
            VERSIONS["synthetic_optimizer_version"])
        if synthetic_optimized is None:
            synthetic_optimized = synthetic_cases.optimize_translations(
                synthetic_error_manifest, call_llm, provider, api_key, model,
                evidence.get("project_evidence", {}).get("glossary", []))
            synthetic_optimized = _save_artifact(
                state, artifact_dir, "synthetic_optimized", synthetic_optimized,
                synthetic_optimizer_dep, VERSIONS["synthetic_optimizer_version"])

        stage("synthetic_validation", "【学术写作】独立验证错误实质性与修复有效性...")
        synthetic_validation_dep = academic_evidence.stable_hash({
            "optimized": synthetic_optimized["content_hash"],
            "version": VERSIONS["synthetic_validation_version"],
        })
        synthetic_validation = _load_valid_artifact(
            state, artifact_dir, "synthetic_validation", synthetic_validation_dep,
            VERSIONS["synthetic_validation_version"])
        if synthetic_validation is None:
            synthetic_validation = synthetic_cases.validate_synthetic_cases(
                synthetic_optimized, call_llm, provider, api_key, model, evidence)
            synthetic_validation = _save_artifact(
                state, artifact_dir, "synthetic_validation", synthetic_validation,
                synthetic_validation_dep, VERSIONS["synthetic_validation_version"])

        stage("literature_evidence", "【学术写作 2/10】固化文献来源与逐字证据...")
        literature_sources_new = literature_evidence.build_literature_sources(literature)
        literature_sources_dep = academic_evidence.stable_hash({
            "source_snapshot": literature_sources_new["content_hash"],
            "version": VERSIONS["literature_sources_version"],
        })
        literature_sources_artifact = _load_valid_artifact(
            state, artifact_dir, "literature_sources", literature_sources_dep,
            VERSIONS["literature_sources_version"])
        if literature_sources_artifact is None:
            literature_sources_artifact = _save_artifact(
                state, artifact_dir, "literature_sources", literature_sources_new,
                literature_sources_dep, VERSIONS["literature_sources_version"])

        literature_evidence_new = literature_evidence.build_literature_evidence(
            literature_sources_artifact)
        literature_evidence_dep = academic_evidence.stable_hash({
            "source_content": literature_sources_artifact["sources_content_hash"],
            "version": VERSIONS["literature_evidence_version"],
        })
        literature_evidence_artifact = _load_valid_artifact(
            state, artifact_dir, "literature_evidence", literature_evidence_dep,
            VERSIONS["literature_evidence_version"])
        if literature_evidence_artifact is None:
            literature_evidence_artifact = _save_artifact(
                state, artifact_dir, "literature_evidence", literature_evidence_new,
                literature_evidence_dep, VERSIONS["literature_evidence_version"])

        stage("research_model", "【学术写作 3/10】建立研究问题与理论框架...")
        model_new = build_research_model(evidence, theory, settings)
        research_dep = academic_evidence.stable_hash({
            "settings": model_new["content_hash"], "evidence_profile":
            evidence.get("project_evidence", {}).get("document_profile"),
            "version": VERSIONS["research_model_version"],
        })
        research_model = _load_valid_artifact(
            state, artifact_dir, "research_model", research_dep,
            VERSIONS["research_model_version"])
        if research_model is None:
            research_model = _save_artifact(
                state, artifact_dir, "research_model", model_new, research_dep,
                VERSIONS["research_model_version"])

        stage("literature_claims", "【学术写作 4/10】从文献证据抽取受限主张...")
        literature_claims_dep = academic_evidence.stable_hash({
            "evidence": literature_evidence_artifact["content_hash"],
            "version": VERSIONS["literature_claims_version"],
        })
        literature_claims_artifact = _load_valid_artifact(
            state, artifact_dir, "literature_claims", literature_claims_dep,
            VERSIONS["literature_claims_version"])
        if literature_claims_artifact is None:
            literature_claims_new = literature_evidence.build_literature_claims(
                literature_sources_artifact, literature_evidence_artifact,
                call_llm, provider, api_key, model)
            literature_claims_artifact = _save_artifact(
                state, artifact_dir, "literature_claims", literature_claims_new,
                literature_claims_dep, VERSIONS["literature_claims_version"])

        stage("argument_plan", "【学术写作 5/10】规划研究论点与证据关系...")
        argument_dep = academic_evidence.stable_hash({
            "evidence": evidence["content_hash"], "research": research_model["content_hash"],
            "literature_source_policy": literature_sources_artifact[
                "sources_metadata_hash"],
            "literature_evidence": literature_evidence_artifact["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
            "human_evidence": human_evidence.evidence_hash(human_entries),
            "version": VERSIONS["argument_plan_version"],
        })
        argument_plan = _load_valid_artifact(
            state, artifact_dir, "argument_plan", argument_dep,
            VERSIONS["argument_plan_version"])
        if argument_plan is None:
            argument_plan = build_argument_plan(
                research_model, evidence, call_llm, provider, api_key, model,
                literature_sources_artifact, literature_evidence_artifact,
                literature_claims_artifact, human_entries)
            argument_plan = _save_artifact(
                state, artifact_dir, "argument_plan", argument_plan, argument_dep,
                VERSIONS["argument_plan_version"])

        case_dep = academic_evidence.stable_hash({
            "argument": argument_plan["content_hash"], "evidence": evidence["content_hash"],
            "synthetic": synthetic_validation["content_hash"],
            "policy": synthetic_policy,
            "limit": int(settings.get("case_limit") or 5),
            "version": VERSIONS["case_selection_version"],
        })
        selected_cases = _load_valid_artifact(
            state, artifact_dir, "selected_cases", case_dep,
            VERSIONS["case_selection_version"])
        if selected_cases is None:
            selected_cases = select_academic_cases(
                research_model, argument_plan, evidence,
                limit=max(1, int(settings.get("case_limit") or 5)),
                synthetic_artifact=synthetic_validation, policy=synthetic_policy,
                preferred_authentic_count=max(1, int(settings.get(
                    "preferred_authentic_case_count") or 3)),
                minimum_authentic_count=max(1, int(settings.get(
                    "minimum_authentic_case_count") or 2)))
            selected_cases = _save_artifact(
                state, artifact_dir, "selected_cases", selected_cases, case_dep,
                VERSIONS["case_selection_version"])

        stage("case_analysis", "【学术写作 6/11】规划案例分析证据契约...")
        human_evidence_artifact = {
            "schema_version": VERSIONS["human_evidence_version"],
            "items": human_entries,
        }
        human_evidence_artifact["content_hash"] = academic_evidence.stable_hash(
            human_entries)
        _save_artifact(state, artifact_dir, "human_evidence",
                       human_evidence_artifact,
                       academic_evidence.stable_hash(human_entries),
                       VERSIONS["human_evidence_version"])
        human_evidence_hash = human_evidence.evidence_hash(human_entries)
        case_analysis_dep = academic_evidence.stable_hash({
            "evidence": evidence["content_hash"],
            "argument": argument_plan["content_hash"],
            "cases": selected_cases["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
            "human_evidence": human_evidence_hash,
            "version": VERSIONS["case_analysis_version"],
        })
        case_plans = _load_valid_artifact(
            state, artifact_dir, "case_analysis_plans", case_analysis_dep,
            VERSIONS["case_analysis_version"])
        if case_plans is None:
            case_plans = case_analysis.build_case_analysis_plans(
                evidence, selected_cases, argument_plan, literature_claims_artifact,
                call_llm, provider, api_key, model, human_entries)
            case_plans = _save_artifact(
                state, artifact_dir, "case_analysis_plans", case_plans,
                case_analysis_dep, VERSIONS["case_analysis_version"])

        stage("outline", "【学术写作 6/10】生成证据约束型学术提纲...")
        outline_dep = academic_evidence.stable_hash({
            "research": research_model["content_hash"],
            "institutional_constraints": academic_evidence.stable_hash(
                research_model.get("institutional_constraints") or {}),
            "argument": argument_plan["content_hash"],
            "cases": selected_cases["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
            "literature_evidence": literature_evidence_artifact["content_hash"],
            "version": VERSIONS["outline_version"],
        })
        outline = _load_valid_artifact(
            state, artifact_dir, "outline", outline_dep, VERSIONS["outline_version"])
        if outline is None:
            outline = build_academic_outline(
                research_model, argument_plan, selected_cases, evidence,
                call_llm, provider, api_key, model,
                literature_sources_artifact, literature_evidence_artifact,
                literature_claims_artifact)
            outline = _save_artifact(state, artifact_dir, "outline", outline, outline_dep,
                                     VERSIONS["outline_version"])

        stage("writing", "【学术写作 7/10】按论点与分节证据撰写正文...")
        sections_dep = academic_evidence.stable_hash({
            "outline": outline["content_hash"], "evidence": evidence["content_hash"],
            "literature_sources": literature_sources_artifact["sources_metadata_hash"],
            "literature_evidence": literature_evidence_artifact["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
            "writer": VERSIONS["writer_version"],
        })
        section_artifact = _load_valid_artifact(
            state, artifact_dir, "sections", sections_dep, VERSIONS["writer_version"])
        existing = ({x["section_id"]: x
                     for x in (section_artifact or {}).get("sections", [])}
                    if section_artifact else _load_reusable_sections(artifact_dir))
        forced = set(academic.get("forced_sections") or [])
        written: List[Dict[str, Any]] = []
        prior_summaries: List[Dict[str, str]] = []
        for plan in outline.get("sections", []):
            sid = plan["section_id"]
            section_key = _section_dependency_hash(
                plan, argument_plan, selected_cases, evidence,
                literature_sources_artifact, literature_evidence_artifact,
                literature_claims_artifact, case_plans, human_entries)
            old = existing.get(sid)
            if old and old.get("dependency_hash") == section_key and sid not in forced:
                item = old
            else:
                packet = _section_packet(plan, research_model, argument_plan,
                                         selected_cases, evidence, outline, prior_summaries,
                                         literature_sources_artifact,
                                         literature_evidence_artifact,
                                         literature_claims_artifact, case_plans)
                content = _write_section(packet, call_llm, provider, api_key, model)
                item = {
                    "section_id": sid, "title": plan["title"], "content": content,
                    "summary": re.sub(r"<!--.*?-->", "", content)[:240],
                    "dependency_hash": section_key,
                    "provenance": _packet_provenance(packet),
                }
            written.append(item)
            prior_summaries.append({"section_id": sid, "summary": item["summary"]})
            partial = {"schema_version": VERSIONS["writer_version"], "sections": written}
            partial["content_hash"] = academic_evidence.stable_hash(
                {k: v for k, v in partial.items() if k != "content_hash"})
            _save_artifact(state, artifact_dir, "sections", partial, sections_dep,
                           VERSIONS["writer_version"])
            save_state(state)
        academic["forced_sections"] = []
        report_md = _compose_report(written)
        report_md = finalize_report_tokens(report_md, evidence, selected_cases)

        stage("validation", "【学术写作 8/10】执行确定性证据与结构验证...")
        validation = academic_validator.validate_academic_report(
            report_md, evidence, research_model, argument_plan, selected_cases, outline,
            literature_sources_artifact, literature_evidence_artifact,
            literature_claims_artifact, human_entries, synthetic_validation)
        validation = _locate_validation_issues(validation, written)
        validation_runs.append(validation)

        stage("review", "【学术写作 9/10】执行独立语义与文献支持审稿...")
        review = _semantic_review(
            report_md, research_model, argument_plan, outline, selected_cases,
            call_llm, provider, api_key, model)
        literature_support_review = _literature_support_review(
            report_md, argument_plan, outline, literature_sources_artifact,
            literature_evidence_artifact, literature_claims_artifact,
            call_llm, provider, api_key, model)

        repair_history = {"schema_version": "academic-repair-v1", "rounds": []}
        if auto_repair_rounds > 0:
            repair_issues = [x for x in validation.get("issues", []) if x["severity"] == "error"]
            repair_issues += [x for x in review.get("issues", [])
                              if x["severity"] in ("medium", "high")]
            repair_issues += [x for x in literature_support_review.get("issues", [])
                              if x["severity"] in ("medium", "high")]
            affected = sorted({str(x.get("section_id")) for x in repair_issues
                               if x.get("section_id")})
            if affected:
                stage("repair", "【学术写作 10/10】定点修订受影响章节并重新验证...")
                by_id = {x["section_id"]: x for x in written}
                plan_by_id = {x["section_id"]: x for x in outline.get("sections", [])}
                for sid in affected:
                    packet = _section_packet(plan_by_id[sid], research_model, argument_plan,
                                             selected_cases, evidence, outline,
                                             prior_summaries,
                                             literature_sources_artifact,
                                             literature_evidence_artifact,
                                             literature_claims_artifact, case_plans)
                    issues = [x for x in repair_issues if str(x.get("section_id")) == sid]
                    old_content = by_id[sid]["content"]
                    new_content = _write_section(
                        packet, call_llm, provider, api_key, model,
                        repair_issues=issues, existing=old_content)
                    by_id[sid]["content"] = new_content
                    by_id[sid]["summary"] = re.sub(r"<!--.*?-->", "", new_content)[:240]
                    by_id[sid]["provenance"] = _packet_provenance(packet)
                    repair_history["rounds"].append({
                        "round": 1, "section_id": sid,
                        "issue_ids": [x.get("issue_id") for x in issues],
                        "global_claim_ids": sorted({str(x.get("global_claim_id")
                                                        or x.get("claim_id")) for x in issues
                                                    if x.get("global_claim_id")
                                                    or x.get("claim_id")}),
                        "literature_claim_ids": sorted({str(x.get(
                            "literature_claim_id")) for x in issues
                            if x.get("literature_claim_id")}),
                        "repair_actions": sorted({str(x.get("repair_action")) for x in issues
                                                  if x.get("repair_action")}),
                        "before_hash": academic_evidence.stable_hash(old_content),
                        "after_hash": academic_evidence.stable_hash(new_content),
                        "repaired_at": _now(),
                    })
                written = [by_id[x["section_id"]] for x in outline.get("sections", [])]
                section_artifact = {"schema_version": VERSIONS["writer_version"],
                                    "sections": written}
                section_artifact["content_hash"] = academic_evidence.stable_hash(
                    {k: v for k, v in section_artifact.items() if k != "content_hash"})
                _save_artifact(state, artifact_dir, "sections", section_artifact,
                               sections_dep, VERSIONS["writer_version"])
                report_md = _compose_report(written)
                report_md = finalize_report_tokens(report_md, evidence, selected_cases)
                validation = academic_validator.validate_academic_report(
                    report_md, evidence, research_model, argument_plan, selected_cases, outline,
                    literature_sources_artifact, literature_evidence_artifact,
                    literature_claims_artifact, human_entries, synthetic_validation)
                validation = _locate_validation_issues(validation, written)
                validation_runs.append(validation)
                review = _semantic_review(
                    report_md, research_model, argument_plan, outline, selected_cases,
                    call_llm, provider, api_key, model)
                literature_support_review = _literature_support_review(
                    report_md, argument_plan, outline, literature_sources_artifact,
                    literature_evidence_artifact, literature_claims_artifact,
                    call_llm, provider, api_key, model)

        validation_artifact = {**validation, "runs": validation_runs[-2:]}
        validation_artifact["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in validation_artifact.items() if k != "content_hash"})
        validation_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "evidence": evidence["content_hash"], "validator": VERSIONS["validator_version"],
            "synthetic": synthetic_validation["content_hash"],
            "literature_sources": literature_sources_artifact["content_hash"],
            "literature_evidence": literature_evidence_artifact["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
        })
        _save_artifact(state, artifact_dir, "validation", validation_artifact,
                       validation_dep, VERSIONS["validator_version"])
        review_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "argument": argument_plan["content_hash"], "reviewer": VERSIONS["reviewer_version"],
        })
        _save_artifact(state, artifact_dir, "review", review, review_dep,
                       VERSIONS["reviewer_version"])
        literature_review_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "argument": argument_plan["content_hash"],
            "literature_sources": literature_sources_artifact["content_hash"],
            "literature_evidence": literature_evidence_artifact["content_hash"],
            "literature_claims": literature_claims_artifact["content_hash"],
            "reviewer": VERSIONS["literature_reviewer_version"],
        })
        _save_artifact(state, artifact_dir, "literature_support_review",
                       literature_support_review, literature_review_dep,
                       VERSIONS["literature_reviewer_version"])
        repair_history["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in repair_history.items() if k != "content_hash"})
        _save_artifact(state, artifact_dir, "repair_history", repair_history,
                       academic_evidence.stable_hash(repair_history["rounds"]), "academic-repair-v1")

        # ---- Academic quality evaluation + bounded structural repair ----
        stage("academic_quality", "【学术写作 11/11】评估学术质量并执行结构性修复...")
        quality_evaluation = academic_quality.evaluate_quality(
            research_model, argument_plan, selected_cases, outline, written, evidence,
            literature_sources_artifact, literature_evidence_artifact,
            literature_claims_artifact, validation, call_llm, provider, api_key, model,
            case_plans)
        quality_runs.append(quality_evaluation)
        quality_repair_history = {"schema_version": "academic-quality-repair-v1",
                                  "rounds": []}
        quality_round = 0
        while auto_quality_repair_rounds > 0 \
                and quality_round < auto_quality_repair_rounds:
            plan = academic_quality.quality_repair_plan(quality_evaluation, outline)
            if not plan["case_replacements"] and not plan["text_repairs"]:
                break
            quality_round += 1
            (written, report_md, validation, review, literature_support_review,
             quality_evaluation, performed_replacements, round_ledger) = _run_quality_repair_round(
                written, report_md, evidence, research_model, argument_plan,
                selected_cases, outline, literature_sources_artifact,
                literature_evidence_artifact, literature_claims_artifact,
                synthetic_validation, case_plans, human_entries, quality_evaluation,
                validation, prior_summaries, call_llm, provider, api_key, model)
            _save_artifact(state, artifact_dir, "selected_cases", selected_cases,
                           case_dep, VERSIONS["case_selection_version"])
            _save_artifact(state, artifact_dir, "argument_plan", argument_plan,
                           argument_dep, VERSIONS["argument_plan_version"])
            _save_artifact(state, artifact_dir, "outline", outline, outline_dep,
                           VERSIONS["outline_version"])
            section_artifact = {"schema_version": VERSIONS["writer_version"],
                                "sections": written}
            section_artifact["content_hash"] = academic_evidence.stable_hash(
                {k: v for k, v in section_artifact.items() if k != "content_hash"})
            _save_artifact(state, artifact_dir, "sections", section_artifact,
                           sections_dep, VERSIONS["writer_version"])
            validation_runs.append(validation)
            quality_runs.append(quality_evaluation)
            quality_repair_history["rounds"].append({
                "round": quality_round,
                "case_replacements": performed_replacements,
                "section_rewrites": round_ledger,
                "issue_ids": [x.get("issue_id") for x in plan["case_replacements"]]
                             + [x.get("issue_id") for x in plan["text_repairs"]],
                "completed_at": _now(),
            })
        quality_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "argument": argument_plan["content_hash"],
            "quality_version": VERSIONS["academic_quality_version"],
        })
        quality_artifact = {**quality_evaluation, "runs": quality_runs[-2:]}
        quality_artifact["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in quality_artifact.items() if k != "content_hash"})
        _save_artifact(state, artifact_dir, "academic_quality", quality_artifact,
                       quality_dep,
                       VERSIONS["academic_quality_version"])
        (artifact_dir / "academic-quality-report.md").write_text(
            academic_quality.render_quality_report(quality_evaluation), encoding="utf-8")
        (artifact_dir / "academic-quality-findings.jsonl").write_text(
            "\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True)
                      for x in quality_evaluation.get("findings", [])) + "\n",
            encoding="utf-8")
        quality_repair_history["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in quality_repair_history.items() if k != "content_hash"})
        _save_artifact(state, artifact_dir, "quality_repair_history",
                       quality_repair_history,
                       academic_evidence.stable_hash(quality_repair_history["rounds"]),
                       "academic-quality-repair-v1")

        # ---- Human evidence needs and questions (no LLM: deterministic) ----
        needs_artifact = human_evidence.build_evidence_needs(
            evidence, case_plans, quality_evaluation)
        _save_artifact(state, artifact_dir, "human_evidence_needs", needs_artifact,
                       academic_evidence.stable_hash({
                           "case_plans": case_plans["content_hash"],
                           "quality": quality_evaluation["content_hash"],
                           "version": VERSIONS["human_evidence_version"],
                       }), VERSIONS["human_evidence_version"])
        questions_artifact = human_evidence.generate_questions(
            needs_artifact, evidence, case_plans)
        _save_artifact(state, artifact_dir, "human_evidence_questions",
                       questions_artifact,
                       academic_evidence.stable_hash({
                           "needs": needs_artifact["content_hash"],
                           "version": VERSIONS["human_evidence_version"],
                       }), VERSIONS["human_evidence_version"])
        open_questions = [q for q in questions_artifact.get("questions", [])
                          if q.get("status") == "open"]
        critical_open = [q for q in open_questions
                         if q.get("priority") == "critical"]
        human_evidence_status = {
            "cases_needing_human_evidence": len({
                q.get("case_id") for q in open_questions}),
            "questions_generated": len(open_questions),
            "critical_questions": len(critical_open),
            "unanswered": len(open_questions),
            "answered": sum(1 for q in questions_artifact.get("questions", [])
                            if q.get("status") == "answered"),
            "unavailable_after_check": sum(
                1 for x in human_entries
                if x.get("status") == "unavailable_after_human_check"),
            "conflicted": sum(1 for x in human_entries
                              if x.get("status") == "conflicted"),
            "cases_improved_after_evidence": sum(
                1 for x in human_entries if x.get("status") == "user_confirmed"),
        }
        academic["human_evidence_status"] = human_evidence_status

        quality, quality_dimensions = _quality_status(
            validation, review, evidence, literature_sources_artifact,
            literature_evidence_artifact, literature_claims_artifact,
            literature_support_review, argument_plan)
        aq_status = "pass"
        dimension_values = list((quality_evaluation.get("dimensions") or {}).values())
        if any(x == "fail" for x in dimension_values):
            aq_status = "fail"
        elif any(x == "review_required" for x in dimension_values):
            aq_status = "review_required"
        elif any(x == "pass_with_warnings" for x in dimension_values):
            aq_status = "pass_with_warnings"
        if critical_open:
            aq_status = "review_required"
        warning_md = academic_validator.render_warnings_markdown(
            validation, review, literature_support_review, evidence, quality_dimensions)
        (artifact_dir / "academic-evidence-warnings.md").write_text(
            warning_md, encoding="utf-8")
        state["p3_md"] = report_md
        state["p3_sections"] = [[x["title"], x["content"]] for x in written]
        state["p3_done"] = True
        state["theory"] = theory
        academic.update(
            status=quality, quality_status=quality, current_stage="completed",
            quality_dimensions=quality_dimensions,
            academic_quality_status=aq_status,
            last_error="", updated_at=_now(),
            warnings_file="academic-evidence-warnings.md",
            quality_report_file="academic-quality-report.md",
        )
        save_state(state)
        return report_md
    except Exception as exc:
        academic.update(status="failed", quality_status="fail",
                        last_error=str(exc)[:500], updated_at=_now())
        state["p3_done"] = False
        save_state(state)
        raise RuntimeError(f"学术写作阶段失败：{exc}") from exc
