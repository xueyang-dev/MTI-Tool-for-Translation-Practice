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
from . import academic_validator

PIPELINE_VERSION = "academic-pipeline-v1"
VERSIONS = {
    "evidence_version": academic_evidence.SCHEMA_VERSION,
    "research_model_version": "research-model-v1",
    "literature_version": "literature-registry-v1",
    "argument_plan_version": "argument-planner-v1",
    "case_selection_version": "case-selector-v1",
    "outline_version": "academic-outline-v1",
    "writer_version": "academic-writer-v1",
    "validator_version": academic_validator.VALIDATOR_VERSION,
    "reviewer_version": "academic-reviewer-v1",
}

ARTIFACT_FILES = {
    "evidence": "academic-evidence.json",
    "research_model": "research-model.json",
    "argument_plan": "argument-plan.json",
    "selected_cases": "selected-cases.json",
    "outline": "academic-outline.json",
    "sections": "academic-sections.json",
    "validation": "academic-validation.json",
    "review": "academic-review.json",
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
        "artifact_history": [],
        "validation_history": [],
        "review_history": [],
        "repair_history": [],
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
    for key in ("artifacts", "artifact_history", "validation_history",
                "review_history", "repair_history", "forced_sections",
                "stale_reasons", "versions"):
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


def _save_artifact(
    state: Dict[str, Any], artifact_dir: Path, name: str, value: Dict[str, Any],
    dependency_hash: str, version: str,
) -> Dict[str, Any]:
    academic = _state(state)
    old = academic["artifacts"].get(name)
    if old and old.get("content_hash") != value.get("content_hash"):
        academic["artifact_history"].append({**old, "name": name,
                                              "superseded_at": _now()})
    filename = ARTIFACT_FILES[name]
    _write_json(artifact_dir / filename, value)
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
    value = _read_json(artifact_dir / ARTIFACT_FILES[name])
    if not value:
        return None
    content_hash = value.get("content_hash") or academic_evidence.stable_hash(value)
    return value if content_hash == record.get("content_hash") else None


def _invalidate_names(state: Dict[str, Any], names: Sequence[str], reason: str) -> None:
    academic = _state(state)
    for name in names:
        record = academic["artifacts"].pop(name, None)
        if record:
            academic["artifact_history"].append({**record, "name": name,
                                                  "invalidated_at": _now(),
                                                  "reason": reason})
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
        if old.get("evidence_version") != versions["evidence_version"] \
                or old.get("literature_version") != versions["literature_version"]:
            _invalidate_names(state, list(ARTIFACT_FILES), "evidence schema/version changed")
        elif old.get("research_model_version") != versions["research_model_version"] \
                or old.get("argument_plan_version") != versions["argument_plan_version"] \
                or old.get("case_selection_version") != versions["case_selection_version"] \
                or old.get("outline_version") != versions["outline_version"]:
            _invalidate_names(state, ["research_model", "argument_plan", "selected_cases",
                                      "outline", "sections", "validation", "review",
                                      "repair_history"], "academic planning version changed")
        elif old.get("writer_version") != versions["writer_version"]:
            _invalidate_names(state, ["sections", "validation", "review", "repair_history"],
                              "writer version changed")
        elif old.get("validator_version") != versions["validator_version"]:
            _invalidate_names(state, ["validation", "review"], "validator version changed")
        elif old.get("reviewer_version") != versions["reviewer_version"]:
            _invalidate_names(state, ["review"], "reviewer version changed")
    academic["versions"] = versions


def invalidate_academic_state(
    state: Dict[str, Any], scope: str = "all", section_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark academic artifacts stale without touching translation work."""
    if scope == "all":
        names = list(ARTIFACT_FILES)
    elif scope == "planning":
        names = ["argument_plan", "selected_cases", "outline", "sections",
                 "validation", "review", "repair_history"]
    elif scope == "writer":
        names = ["sections", "validation", "review", "repair_history"]
    elif scope == "validation":
        names = ["validation", "review"]
    elif scope == "review":
        names = ["review"]
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
    input_hash = academic_evidence.stable_hash({
        "settings": settings,
        "literature": academic_evidence.normalize_literature_registry(literature),
    })
    old_hash = academic.get("input_hash")
    if old_hash and old_hash != input_hash:
        _invalidate_names(state, ["research_model", "argument_plan", "selected_cases",
                                  "outline", "sections", "validation", "review",
                                  "repair_history"], "research/literature settings changed")
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
        _invalidate_names(state, list(ARTIFACT_FILES), "translation evidence changed")
    academic["translation_evidence_hash"] = translation_hash
    academic["input_hash"] = input_hash
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
        "writing_style": settings.get("writing_style") or "规范、克制的中文 MTI 学术书面语",
        "report_requirements": settings.get("report_requirements") or "翻译实践报告",
        "target_words": int(settings.get("target_words") or 4200),
        "settings_provenance": {
            "research_topic": "user_confirmed" if settings.get("research_topic") else "default_inferred",
            "theoretical_framework": "user_confirmed" if settings.get("theoretical_framework")
            else "pipeline_input",
            "method": "user_confirmed" if settings.get("method") else "default_inferred",
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
            "literature_evidence": [],
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
) -> Dict[str, Any]:
    system = (
        "你是学术论证规划器。只规划可由输入证据支持的主要论点，不写正文，不补造文献。"
        "必须区分 PROJECT_EVIDENCE、LITERATURE_EVIDENCE 和 AUTHOR_ANALYSIS。"
        "输出 JSON：{\"claims\":[{\"claim_id\":\"C1\",\"claim\":\"...\","
        "\"research_question\":\"RQ1\",\"project_evidence\":[\"seg-...\"或\"metric:...\"],"
        "\"literature_evidence\":[\"source-id\"],\"analysis_type\":\"AUTHOR_ANALYSIS\","
        "\"confidence\":\"low|medium|high\",\"planned_sections\":[\"1\"],"
        "\"reasoning\":\"...\",\"counterargument\":\"...\"}]}。"
    )
    payload = {
        "research_model": research_model,
        "project_statistics": evidence.get("project_evidence", {}).get("statistics", {}),
        "candidate_cases": _candidate_summaries(evidence),
        "literature_registry": evidence.get("literature_evidence", []),
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False)) or _fallback_argument_plan(
                         research_model, evidence)
    valid_rqs = {x["rq_id"] for x in research_model.get("research_questions", [])}
    valid_segments = set(academic_evidence.segment_index(evidence))
    valid_metrics = {f"metric:{x}" for x in
                     evidence.get("project_evidence", {}).get("statistics", {})}
    valid_lit = set(academic_evidence.literature_index(evidence))
    claims = []
    for i, item in enumerate(raw.get("claims") or []):
        if not isinstance(item, dict):
            continue
        rq = str(item.get("research_question") or "")
        claim_text = str(item.get("claim") or "").strip()
        project = [str(x) for x in item.get("project_evidence") or []
                   if str(x) in valid_segments or str(x) in valid_metrics]
        literature = [str(x) for x in item.get("literature_evidence") or []
                      if str(x) in valid_lit]
        if not claim_text or rq not in valid_rqs or not (project or literature):
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
            "literature_evidence": literature,
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
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def select_academic_cases(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    evidence: Dict[str, Any], limit: int = 8,
) -> Dict[str, Any]:
    candidates = academic_evidence.candidate_index(evidence)
    selected: Dict[str, Dict[str, Any]] = {}
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
        item = next((x for x in evidence.get("candidate_cases", [])
                     if x.get("coverage_zone") == zone), None)
        if item and len(selected) < limit:
            selected.setdefault(item["case_id"], {
                **item, "supports_claims": [], "research_questions": []})
    for item in evidence.get("candidate_cases", []):
        if len(selected) >= limit:
            break
        selected.setdefault(item["case_id"], {
            **item, "supports_claims": [], "research_questions": []})
    cases = list(selected.values())[:limit]
    for case in cases:
        case["supports_claims"] = sorted(set(case["supports_claims"]))
        case["research_questions"] = sorted(set(case["research_questions"]))
        case["selection_rationale"] = (
            "；".join(case.get("reasons") or []) or "whole-corpus coverage")
    artifact = {
        "schema_version": VERSIONS["case_selection_version"],
        "selection_policy": "argument relevance > complete process chain > representativeness > complexity",
        "cases": cases,
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _fallback_outline(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any],
) -> Dict[str, Any]:
    claims = [c["claim_id"] for c in argument_plan.get("claims", [])]
    rqs = [r["rq_id"] for r in research_model.get("research_questions", [])]
    cases = [c["case_id"] for c in selected_cases.get("cases", [])]
    total = int(research_model.get("target_words") or 4200)
    return {"sections": [
        {"section_id": "1", "title": "翻译项目与研究设计", "purpose": "界定项目、研究问题、方法与证据边界。",
         "research_questions": rqs, "claims": claims[:1], "cases": [], "literature": [],
         "required_statistics": ["total_segments", "translated_segments"],
         "target_words": round(total * .2), "minimum_chars": 300,
         "allowed_conclusions": ["仅陈述证据库可支持的项目特征"]},
        {"section_id": "2", "title": "翻译过程、术语与质量控制", "purpose": "分析术语、TM、审校和修复证据。",
         "research_questions": rqs[-1:], "claims": claims[-1:], "cases": cases[:2], "literature": [],
         "required_statistics": ["reviewed_segments", "tm_reuse_count", "actionable_findings"],
         "target_words": round(total * .25), "minimum_chars": 350,
         "allowed_conclusions": ["区分可观察流程效果与推断"]},
        {"section_id": "3", "title": "理论框架下的案例分析", "purpose": "用完整证据链分析代表性翻译决策。",
         "research_questions": rqs, "claims": claims, "cases": cases, "literature": [],
         "required_statistics": [], "target_words": round(total * .4), "minimum_chars": 600,
         "allowed_conclusions": ["理论解释必须表述为作者分析而非真实心理意图"]},
        {"section_id": "4", "title": "结论、局限与反思", "purpose": "回答研究问题并限定结论外推。",
         "research_questions": rqs, "claims": claims, "cases": [], "literature": [],
         "required_statistics": ["repaired_segments", "term_conflicts"],
         "target_words": round(total * .15), "minimum_chars": 250,
         "allowed_conclusions": ["结论强度不得超过项目与文献证据"]},
    ], "planner_fallback": True}


def build_academic_outline(
    research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    selected_cases: Dict[str, Any], evidence: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
) -> Dict[str, Any]:
    system = (
        "你是 MTI 学术提纲规划器。提纲必须服务研究问题，并且只能引用给定 claim、case、"
        "literature 和 statistic id。只输出 JSON：{\"sections\":[{\"section_id\":\"1\","
        "\"title\":\"...\",\"purpose\":\"...\",\"research_questions\":[\"RQ1\"],"
        "\"claims\":[\"C1\"],\"cases\":[\"seg-...\"],\"literature\":[\"source-id\"],"
        "\"required_statistics\":[\"total_segments\"],\"target_words\":900,"
        "\"minimum_chars\":300,\"allowed_conclusions\":[\"...\"]}]}。"
    )
    payload = {
        "research_model": research_model,
        "argument_plan": argument_plan,
        "selected_cases": selected_cases,
        "available_literature_ids": list(academic_evidence.literature_index(evidence)),
        "available_statistics": list(evidence.get("project_evidence", {}).get("statistics", {})),
    }
    raw = _call_json(call_llm, provider, api_key, model, system,
                     json.dumps(payload, ensure_ascii=False)) or _fallback_outline(
                         research_model, argument_plan, selected_cases)
    valid_claims = {x["claim_id"] for x in argument_plan.get("claims", [])}
    valid_cases = {x["case_id"] for x in selected_cases.get("cases", [])}
    valid_rqs = {x["rq_id"] for x in research_model.get("research_questions", [])}
    valid_lit = set(academic_evidence.literature_index(evidence))
    valid_stats = set(evidence.get("project_evidence", {}).get("statistics", {}))
    sections = []
    for i, item in enumerate(raw.get("sections") or []):
        if not isinstance(item, dict):
            continue
        section_id = str(item.get("section_id") or i + 1)
        sections.append({
            "section_id": section_id,
            "title": str(item.get("title") or f"章节 {section_id}").strip(),
            "purpose": str(item.get("purpose") or "").strip(),
            "research_questions": [str(x) for x in item.get("research_questions") or []
                                   if str(x) in valid_rqs],
            "claims": [str(x) for x in item.get("claims") or [] if str(x) in valid_claims],
            "cases": [str(x) for x in item.get("cases") or [] if str(x) in valid_cases],
            "literature": [str(x) for x in item.get("literature") or [] if str(x) in valid_lit],
            "required_statistics": [str(x) for x in item.get("required_statistics") or []
                                    if str(x) in valid_stats],
            "target_words": max(200, int(item.get("target_words") or 700)),
            "minimum_chars": max(100, int(item.get("minimum_chars") or 200)),
            "allowed_conclusions": _as_list(item.get("allowed_conclusions")),
        })
    if len(sections) < 3:
        sections = _fallback_outline(research_model, argument_plan, selected_cases)["sections"]
        fallback = True
    else:
        fallback = bool(raw.get("planner_fallback"))
    # Deterministically guarantee graph coverage; the writer cannot silently lose a claim/RQ.
    analysis = max(sections, key=lambda x: len(x["cases"]))
    for claim_id in valid_claims:
        if not any(claim_id in x["claims"] for x in sections):
            analysis["claims"].append(claim_id)
    for rq_id in valid_rqs:
        if not any(rq_id in x["research_questions"] for x in sections):
            analysis["research_questions"].append(rq_id)
    artifact = {
        "schema_version": VERSIONS["outline_version"],
        "sections": sections,
        "planner_fallback": fallback,
    }
    artifact["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def _section_packet(
    section: Dict[str, Any], research_model: Dict[str, Any],
    argument_plan: Dict[str, Any], selected_cases: Dict[str, Any],
    evidence: Dict[str, Any], outline: Dict[str, Any],
    prior_summaries: List[Dict[str, str]],
) -> Dict[str, Any]:
    claims = {x["claim_id"]: x for x in argument_plan.get("claims", [])}
    cases = {x["case_id"]: x for x in selected_cases.get("cases", [])}
    segments = academic_evidence.segment_index(evidence)
    literature = academic_evidence.literature_index(evidence)
    case_term_ids = set()
    for case_id in section.get("cases", []):
        case_term_ids.update((segments.get(case_id) or {}).get(
            "process_evidence", {}).get("injected_glossary_entry_ids", []))
    all_terms = evidence.get("project_evidence", {}).get("glossary", [])
    if "术语" in (section.get("title", "") + section.get("purpose", "")):
        terminology = all_terms[:30]
    else:
        terminology = [x for x in all_terms if x.get("id") in case_term_ids]
    return {
        "research_model": research_model,
        "global_outline": [
            {k: x.get(k) for k in ("section_id", "title", "purpose",
                                    "research_questions", "claims", "cases")}
            for x in outline.get("sections", [])
        ],
        "current_section": section,
        "claims": [claims[x] for x in section.get("claims", []) if x in claims],
        "cases": [{**cases[x], "evidence": segments.get(x)} for x in section.get("cases", [])
                  if x in cases and x in segments],
        "literature": [literature[x] for x in section.get("literature", [])
                       if x in literature and literature[x].get("citation_allowed")],
        "statistics": {x: evidence.get("project_evidence", {}).get("statistics", {}).get(x)
                       for x in section.get("required_statistics", [])},
        "terminology_decisions": terminology,
        "prior_section_summaries": prior_summaries,
        "writing_constraints": {
            "claim_marker": "<!--claim:C1-->",
            "rq_marker": "<!--rq:RQ1-->",
            "source_quote": "> [SOURCE seg-...]: exact source",
            "target_quote": "> [TARGET seg-...]: exact final target",
            "project_statistic": "{{STAT:metric_name}}",
            "terminology_decision": "{{TERM:entry_id}}",
            "formal_citation": "[@source_id]",
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
        "项目事实或文献。引用案例时必须逐字复制 packet 中 source/final_target，使用指定"
        "SOURCE/TARGET 格式；项目数字只能用 {{STAT:key}}；正式文献只能用 [@source_id]；"
        "项目术语决策用 {{TERM:entry_id}}。每个落实的 claim 和 RQ 分别保留 HTML marker。"
        "理论解释必须写成作者分析，例如‘从结果看可解释为’，不得冒充译者真实意图。"
        "无文献证据时，不得从模型记忆补作者、年份、书名或理论命题。只输出章节正文。"
    )
    if repair:
        system += ("这是定点修订：仅修复给定 issues，保持当前章节的有效论点、证据和 marker，"
                   "输出完整修订后章节，不写修订说明。")
    user = {"packet": packet}
    if repair:
        user.update({"existing_section": existing, "issues": repair_issues})
    raw = call_llm(provider, api_key, model, system,
                   json.dumps(user, ensure_ascii=False), temperature=0.2)
    text = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", (raw or "").strip(),
                  flags=re.DOTALL)
    if not text:
        raise RuntimeError("学术写作模型返回空章节")
    return academic_validator.expand_evidence_tokens(text, packet_to_evidence(packet))


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
            "literature_evidence": packet.get("literature", [])}


def _compose_report(sections: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"## {item['section_id']} {item['title']}\n\n{item['content'].strip()}"
        for item in sections) + "\n"


def _semantic_review(
    report_md: str, research_model: Dict[str, Any], argument_plan: Dict[str, Any],
    outline: Dict[str, Any], selected_cases: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
) -> Dict[str, Any]:
    system = (
        "你是独立的 MTI 学术审稿人，不是写作者。检查不受确定性验证覆盖的推理问题："
        "unsupported_conclusion、weak_evidence、case_claim_mismatch、theory_case_mismatch、"
        "overgeneralization、duplicate_argument、contradiction、descriptive_not_analytical、"
        "chapter_drift、conclusion_too_strong。只输出 JSON：{\"issues\":[{\"issue_id\":"
        "\"AR-001\",\"section_id\":\"3\",\"type\":\"weak_evidence\","
        "\"claim_id\":\"C1\",\"evidence_ids\":[\"seg-...\"],"
        "\"severity\":\"low|medium|high\",\"reason\":\"...\","
        "\"suggested_action\":\"...\"}]}。不得改写正文。"
    )
    payload = {
        "research_model": research_model,
        "argument_plan": argument_plan,
        "outline": outline,
        "selected_case_ids": [x["case_id"] for x in selected_cases.get("cases", [])],
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


def _quality_status(
    validation: Dict[str, Any], review: Dict[str, Any], evidence: Dict[str, Any],
) -> str:
    if validation.get("status") == "fail":
        return "fail"
    if review.get("status") == "review_required":
        return "review_required"
    if validation.get("status") == "pass_with_warnings" or review.get("issues") \
            or evidence.get("limitations"):
        return "pass_with_warnings"
    return "pass"


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
) -> str:
    """Run or resume the complete academic evidence-to-repair pipeline."""
    artifact_dir = Path(artifact_dir)
    academic = _state(state)
    _legacy_backup(state, artifact_dir)
    sync_versions(state)
    academic.update(status="in_progress", last_error="", updated_at=_now())
    settings, literature = prepare_academic_inputs(
        state, theory, research_settings, literature_sources)

    def stage(name: str, label: str) -> None:
        academic["current_stage"] = name
        academic["status"] = "in_progress"
        if on_status:
            on_status(label)
        save_state(state)

    try:
        stage("evidence", "【学术写作 1/8】构建全语料学术证据库...")
        evidence_new = academic_evidence.build_academic_evidence(
            state, job_id, literature)
        evidence_dep = academic_evidence.stable_hash({
            "translation": evidence_new["content_hash"],
            "version": VERSIONS["evidence_version"],
        })
        evidence = _load_valid_artifact(state, artifact_dir, "evidence", evidence_dep,
                                        VERSIONS["evidence_version"])
        if evidence is None:
            evidence = _save_artifact(state, artifact_dir, "evidence", evidence_new,
                                      evidence_dep, VERSIONS["evidence_version"])

        stage("research_model", "【学术写作 2/8】建立研究问题与理论框架...")
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

        stage("argument_plan", "【学术写作 3/8】规划研究论点与证据关系...")
        argument_dep = academic_evidence.stable_hash({
            "evidence": evidence["content_hash"], "research": research_model["content_hash"],
            "literature": academic_evidence.stable_hash(evidence.get("literature_evidence", [])),
            "version": VERSIONS["argument_plan_version"],
        })
        argument_plan = _load_valid_artifact(
            state, artifact_dir, "argument_plan", argument_dep,
            VERSIONS["argument_plan_version"])
        if argument_plan is None:
            argument_plan = build_argument_plan(
                research_model, evidence, call_llm, provider, api_key, model)
            argument_plan = _save_artifact(
                state, artifact_dir, "argument_plan", argument_plan, argument_dep,
                VERSIONS["argument_plan_version"])

        case_dep = academic_evidence.stable_hash({
            "argument": argument_plan["content_hash"], "evidence": evidence["content_hash"],
            "version": VERSIONS["case_selection_version"],
        })
        selected_cases = _load_valid_artifact(
            state, artifact_dir, "selected_cases", case_dep,
            VERSIONS["case_selection_version"])
        if selected_cases is None:
            selected_cases = select_academic_cases(research_model, argument_plan, evidence)
            selected_cases = _save_artifact(
                state, artifact_dir, "selected_cases", selected_cases, case_dep,
                VERSIONS["case_selection_version"])

        stage("outline", "【学术写作 4/8】生成证据约束型学术提纲...")
        outline_dep = academic_evidence.stable_hash({
            "research": research_model["content_hash"],
            "argument": argument_plan["content_hash"],
            "cases": selected_cases["content_hash"],
            "literature": academic_evidence.stable_hash(evidence.get("literature_evidence", [])),
            "version": VERSIONS["outline_version"],
        })
        outline = _load_valid_artifact(
            state, artifact_dir, "outline", outline_dep, VERSIONS["outline_version"])
        if outline is None:
            outline = build_academic_outline(
                research_model, argument_plan, selected_cases, evidence,
                call_llm, provider, api_key, model)
            outline = _save_artifact(state, artifact_dir, "outline", outline, outline_dep,
                                     VERSIONS["outline_version"])

        stage("writing", "【学术写作 5/8】按论点与分节证据撰写正文...")
        sections_dep = academic_evidence.stable_hash({
            "outline": outline["content_hash"], "evidence": evidence["content_hash"],
            "writer": VERSIONS["writer_version"],
        })
        section_artifact = _load_valid_artifact(
            state, artifact_dir, "sections", sections_dep, VERSIONS["writer_version"])
        existing = {x["section_id"]: x for x in (section_artifact or {}).get("sections", [])}
        forced = set(academic.get("forced_sections") or [])
        written: List[Dict[str, Any]] = []
        prior_summaries: List[Dict[str, str]] = []
        for plan in outline.get("sections", []):
            sid = plan["section_id"]
            section_key = academic_evidence.stable_hash({
                "plan": plan, "claims": argument_plan["content_hash"],
                "cases": selected_cases["content_hash"], "writer": VERSIONS["writer_version"],
            })
            old = existing.get(sid)
            if old and old.get("dependency_hash") == section_key and sid not in forced:
                item = old
            else:
                packet = _section_packet(plan, research_model, argument_plan,
                                         selected_cases, evidence, outline, prior_summaries)
                content = _write_section(packet, call_llm, provider, api_key, model)
                item = {
                    "section_id": sid, "title": plan["title"], "content": content,
                    "summary": re.sub(r"<!--.*?-->", "", content)[:240],
                    "dependency_hash": section_key,
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

        stage("validation", "【学术写作 6/8】执行确定性证据与结构验证...")
        validation = academic_validator.validate_academic_report(
            report_md, evidence, research_model, argument_plan, selected_cases, outline)
        validation = _locate_validation_issues(validation, written)
        academic["validation_history"].append(validation)

        stage("review", "【学术写作 7/8】执行独立语义学术审稿...")
        review = _semantic_review(
            report_md, research_model, argument_plan, outline, selected_cases,
            call_llm, provider, api_key, model)
        academic["review_history"].append(review)

        repair_history = {"schema_version": "academic-repair-v1", "rounds": []}
        if auto_repair_rounds > 0:
            repair_issues = [x for x in validation.get("issues", []) if x["severity"] == "error"]
            repair_issues += [x for x in review.get("issues", [])
                              if x["severity"] in ("medium", "high")]
            affected = sorted({str(x.get("section_id")) for x in repair_issues
                               if x.get("section_id")})
            if affected:
                stage("repair", "【学术写作 8/8】定点修订受影响章节并重新验证...")
                by_id = {x["section_id"]: x for x in written}
                plan_by_id = {x["section_id"]: x for x in outline.get("sections", [])}
                for sid in affected:
                    packet = _section_packet(plan_by_id[sid], research_model, argument_plan,
                                             selected_cases, evidence, outline,
                                             prior_summaries)
                    issues = [x for x in repair_issues if str(x.get("section_id")) == sid]
                    old_content = by_id[sid]["content"]
                    new_content = _write_section(
                        packet, call_llm, provider, api_key, model,
                        repair_issues=issues, existing=old_content)
                    by_id[sid]["content"] = new_content
                    by_id[sid]["summary"] = re.sub(r"<!--.*?-->", "", new_content)[:240]
                    repair_history["rounds"].append({
                        "round": 1, "section_id": sid,
                        "issue_ids": [x.get("issue_id") for x in issues],
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
                validation = academic_validator.validate_academic_report(
                    report_md, evidence, research_model, argument_plan, selected_cases, outline)
                validation = _locate_validation_issues(validation, written)
                academic["validation_history"].append(validation)
                review = _semantic_review(
                    report_md, research_model, argument_plan, outline, selected_cases,
                    call_llm, provider, api_key, model)
                academic["review_history"].append(review)

        validation_artifact = {**validation,
                               "runs": academic["validation_history"][-2:]}
        validation_artifact["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in validation_artifact.items() if k != "content_hash"})
        validation_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "evidence": evidence["content_hash"], "validator": VERSIONS["validator_version"],
        })
        _save_artifact(state, artifact_dir, "validation", validation_artifact,
                       validation_dep, VERSIONS["validator_version"])
        review_dep = academic_evidence.stable_hash({
            "report": academic_evidence.stable_hash(report_md),
            "argument": argument_plan["content_hash"], "reviewer": VERSIONS["reviewer_version"],
        })
        _save_artifact(state, artifact_dir, "review", review, review_dep,
                       VERSIONS["reviewer_version"])
        repair_history["content_hash"] = academic_evidence.stable_hash(
            {k: v for k, v in repair_history.items() if k != "content_hash"})
        _save_artifact(state, artifact_dir, "repair_history", repair_history,
                       academic_evidence.stable_hash(repair_history["rounds"]), "academic-repair-v1")

        quality = _quality_status(validation, review, evidence)
        warning_md = academic_validator.render_warnings_markdown(validation, review, evidence)
        (artifact_dir / "academic-evidence-warnings.md").write_text(
            warning_md, encoding="utf-8")
        state["p3_md"] = report_md
        state["p3_sections"] = [[x["title"], x["content"]] for x in written]
        state["p3_done"] = True
        state["theory"] = theory
        academic.update(
            status=quality, quality_status=quality, current_stage="completed",
            last_error="", updated_at=_now(),
            warnings_file="academic-evidence-warnings.md",
        )
        save_state(state)
        return report_md
    except Exception as exc:
        academic.update(status="failed", quality_status="fail",
                        last_error=str(exc)[:500], updated_at=_now())
        state["p3_done"] = False
        save_state(state)
        raise RuntimeError(f"学术写作阶段失败：{exc}") from exc
