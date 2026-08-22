"""Translation-stream knowledge feedback.

Observed terminology is evidence, not governance.  This module records what
the translation stream noticed and exposes it as a provisional hint for later
batches; only the existing human freeze workflow can promote it to glossary.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import models, terminology


def _parse_array(text: Any) -> Optional[List[Any]]:
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.DOTALL)
    candidate = re.sub(r"\s*```$", "", candidate, flags=re.DOTALL).strip()
    try:
        value = json.loads(candidate)
        return value if isinstance(value, list) else None
    except (TypeError, ValueError):
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\[", candidate):
        try:
            value, _ = decoder.raw_decode(candidate[match.start():])
        except (TypeError, ValueError):
            continue
        if isinstance(value, list):
            return value
    return None


def _call(call_llm: Callable, provider: str, api_key: str, model: str,
          system_prompt: str, user_prompt: str) -> Any:
    try:
        return call_llm(provider, api_key, model, system_prompt, user_prompt,
                        temperature=0.1)
    except TypeError:
        return call_llm(provider, api_key, model, system_prompt, user_prompt)


def extract_observations(
    sources: Sequence[str],
    targets: Sequence[str],
    provider: str,
    api_key: str,
    model: str,
    call_llm: Optional[Callable] = None,
) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Extract terms/entities whose translation choices may matter later."""
    if not sources or not targets:
        return [], None
    if call_llm is None:
        import core
        call_llm = core.call_llm
    numbered = "\n\n".join(
        f"段落 {i + 1}\n原文：{source}\n译文：{target}"
        for i, (source, target) in enumerate(zip(sources, targets))
    )
    system_prompt = (
        "你是翻译流知识抽取器。只从给出的原文—译文对照中发现后续批次需要保持一致的"
        "人名、称谓、固定表达、口癖或专业术语。不要抽取普通词、整句、URL、邮箱或引用。"
        "只输出 JSON 数组，每项为 {\"source_expression\": \"原文短语\","
        "\"observed_target\": \"当前实际译法\", \"kind\": \"term|name|expression\"}。"
        "不要修改任何术语表，不要输出解释。"
    )
    try:
        parsed = _parse_array(_call(
            call_llm, provider, api_key, model, system_prompt, numbered))
    except Exception as exc:
        return [], f"知识反馈调用失败：{str(exc)[:160]}"
    if parsed is None:
        return [], "知识反馈返回不是 JSON 数组"
    observations = []
    seen = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source_expression") or item.get("source") or "").strip()
        target = str(item.get("observed_target") or item.get("target") or "").strip()
        kind = str(item.get("kind") or "term").strip() or "term"
        if len(source) < 2 or not target or len(source) > 160 or len(target) > 240:
            continue
        if source.casefold() in seen or re.search(r"https?://|@", source):
            continue
        seen.add(source.casefold())
        observations.append({"source_expression": source,
                             "observed_target": target, "kind": kind})
    return observations, None


def _first_alignment(
    source_expression: str,
    paragraphs: Sequence[str],
    pairs: Sequence[Dict[str, Any]],
) -> Tuple[Optional[int], str]:
    occurrences = terminology.find_occurrences(source_expression, list(paragraphs))
    if not occurrences:
        return None, ""
    first = occurrences[0]
    if first < len(pairs):
        return first, str(pairs[first].get("target") or "").strip()
    return first, ""


def _existing_entry(source: str, glossary: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    key = source.casefold()
    for entry in models.normalize_glossary(glossary or []):
        if entry.get("source", "").casefold() == key:
            return entry
    return None


def _candidate_key(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("source") or "").casefold()


def _make_candidate(
    observation: Dict[str, str],
    paragraphs: Sequence[str],
    pairs: Sequence[Dict[str, Any]],
    segment_index: int,
) -> Dict[str, Any]:
    source = observation["source_expression"]
    occurrences = terminology.find_occurrences(source, list(paragraphs))
    first, first_target = _first_alignment(source, paragraphs, pairs)
    observed_target = observation["observed_target"] or first_target
    return {
        "source": source,
        "observed_target": observed_target,
        "first_observed_segment": first if first is not None else segment_index,
        "occurrences": occurrences,
        "observed_segments": [segment_index],
        "status": "emergent_candidate",
        "origin": "translation_observation",
        "kind": observation.get("kind") or "term",
        "confidence": 0.5,
    }


def observe_batch(
    sources: Sequence[str],
    targets: Sequence[str],
    paragraphs: Sequence[str],
    pairs_before_batch: Sequence[Dict[str, Any]],
    glossary: Sequence[Dict[str, Any]],
    batch_offset: int,
    provider: str,
    api_key: str,
    model: str,
    existing_candidates: Optional[Sequence[Dict[str, Any]]] = None,
    call_llm: Optional[Callable] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Return updated candidate queue, auditable events, and a non-fatal warning."""
    observations, warning = extract_observations(
        sources, targets, provider, api_key, model, call_llm=call_llm)
    candidates = [dict(item) for item in (existing_candidates or [])
                  if isinstance(item, dict)]
    by_source = {_candidate_key(item): item for item in candidates if _candidate_key(item)}
    events: List[Dict[str, Any]] = []
    all_pairs = list(pairs_before_batch) + [
        {"source": source, "target": target}
        for source, target in zip(sources, targets)
    ]
    for local_index, observation in enumerate(observations):
        source = observation["source_expression"]
        existing = _existing_entry(source, glossary)
        first, first_target = _first_alignment(source, paragraphs, all_pairs)
        candidate_target = observation["observed_target"] or first_target
        if existing is not None:
            preferred = existing.get("preferred") or existing.get("target")
            if (existing.get("status") == "locked" and preferred and
                    candidate_target and preferred not in candidate_target):
                events.append({
                    "type": "target_conflict",
                    "severity": "actionable",
                    "source": source,
                    "preferred_target": preferred,
                    "observed_target": candidate_target,
                    "segment_index": batch_offset + local_index,
                    "reason": f"锁定术语「{source}」的观察译法与首选译名不一致",
                })
            else:
                events.append({
                    "type": "known_consistency",
                    "source": source,
                    "observed_target": candidate_target,
                    "segment_index": batch_offset + local_index,
                })
            continue
        candidate = _make_candidate(
            observation, paragraphs, all_pairs, batch_offset + local_index)
        key = _candidate_key(candidate)
        old = by_source.get(key)
        if old is not None:
            old["occurrences"] = sorted(set(old.get("occurrences") or []) |
                                         set(candidate.get("occurrences") or []))
            old["observed_segments"] = sorted(set(old.get("observed_segments") or []) |
                                                {batch_offset + local_index})
            if not old.get("observed_target"):
                old["observed_target"] = candidate["observed_target"]
            candidate = old
        else:
            candidates.append(candidate)
            by_source[key] = candidate
        events.append({
            "type": "emergent_candidate",
            "source": candidate["source"],
            "observed_target": candidate["observed_target"],
            "first_observed_segment": candidate["first_observed_segment"],
            "occurrences": list(candidate["occurrences"]),
            "segment_index": batch_offset + local_index,
            "origin": "translation_observation",
        })
    return candidates, events, warning


def provisional_hints(
    candidates: Sequence[Dict[str, Any]],
    limit: int = 12,
) -> List[Dict[str, Any]]:
    """Expose observations as non-governing suggestions for later batches."""
    hints = []
    for candidate in list(candidates or [])[-max(0, limit):]:
        source = str(candidate.get("source") or "").strip()
        target = str(candidate.get("observed_target") or "").strip()
        if not source or not target:
            continue
        entry = models.normalize_glossary_entry({
            "source": source,
            "target": target,
            "preferred": target,
            "behavior": "translate",
            "status": "provisional",
            "scope": "document",
            "occurrences": candidate.get("occurrences") or [],
            "note": "翻译流观察所得；未经人工确认，不得视为锁定术语",
        })
        if entry is not None:
            entry["origin"] = "translation_observation"
            entry["observed_target"] = target
            hints.append(entry)
    return hints
