"""Long-document understanding and translation context compilation.

The module keeps five kinds of context separate:
document meaning, local section meaning, terminology, source neighbors, and
accepted target continuity.  It is deliberately JSON-shaped so the result can
be persisted beside a job and reused after a restart.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


DEFAULT_UNIT_CHARS = 12000
DEFAULT_DIGEST_WORKERS = 4
TARGET_CONTEXT_LEVELS = (
    "human_accepted",
    "reviewed",
    "tm_approved",
    "generated",
)


def _clean(value: Any, limit: int = 1200) -> str:
    text = "" if value is None else str(value).strip()
    return text[:limit].rstrip()


def _string_list(value: Any, limit: int = 12, item_limit: int = 160) -> List[str]:
    if isinstance(value, str):
        value = re.split(r"[,，;；\n]", value)
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    for item in value:
        item = _clean(item, item_limit)
        if item and item not in out:
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _parse_object(text: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.DOTALL)
    candidate = re.sub(r"\s*```$", "", candidate, flags=re.DOTALL).strip()
    try:
        value = json.loads(candidate)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", candidate):
        try:
            value, _ = decoder.raw_decode(candidate[match.start():])
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _call(call_llm: Callable, provider: str, api_key: str, model: str,
          system_prompt: str, user_prompt: str) -> Any:
    try:
        return call_llm(provider, api_key, model, system_prompt, user_prompt,
                        temperature=0.1)
    except TypeError:
        # Small test/dry-run providers sometimes expose the five-argument form.
        return call_llm(provider, api_key, model, system_prompt, user_prompt)


def _chunk_range(paragraphs: Sequence[str], start: int, end: int,
                 max_chars: int, unit_prefix: str, label: str,
                 kind: str) -> List[Dict[str, Any]]:
    units = []
    chunk_start = start
    chars = 0
    for index in range(start, end + 1):
        size = len(paragraphs[index])
        if index > chunk_start and chars + size > max_chars:
            units.append(_make_unit(paragraphs, chunk_start, index - 1,
                                    unit_prefix, len(units), label, kind))
            chunk_start, chars = index, 0
        chars += size
    if chunk_start <= end:
        units.append(_make_unit(paragraphs, chunk_start, end,
                                unit_prefix, len(units), label, kind))
    return units


def _make_unit(paragraphs: Sequence[str], start: int, end: int,
               prefix: str, number: int, label: str, kind: str) -> Dict[str, Any]:
    return {
        "unit_id": f"{prefix}-{number + 1}",
        "kind": kind,
        "label": _clean(label, 240),
        "start_segment": start,
        "end_segment": end,
        "source": "\n".join(paragraphs[start:end + 1]),
    }


def build_semantic_units(
    paragraphs: Sequence[str],
    document_profile: Optional[Dict[str, Any]] = None,
    max_chars: int = DEFAULT_UNIT_CHARS,
) -> List[Dict[str, Any]]:
    """Build section/cluster units from deterministic paragraph ranges.

    Profile ranges are preferred.  Gaps and documents without reliable section
    boundaries become contiguous semantic clusters, so every source paragraph
    belongs to exactly one unit.
    """
    paragraphs = [str(p or "") for p in paragraphs]
    if not paragraphs:
        return []
    max_chars = max(200, int(max_chars or DEFAULT_UNIT_CHARS))
    ranges: List[Tuple[int, int, str, str, str]] = []
    used = set()
    sections = sorted(
        (s for s in (document_profile or {}).get("sections") or []
         if isinstance(s, dict)),
        key=lambda s: (int(s.get("start_segment", -1)), int(s.get("end_segment", -1))),
    )
    for section in sections:
        try:
            start = max(0, int(section.get("start_segment")))
            end = min(len(paragraphs) - 1, int(section.get("end_segment")))
        except (TypeError, ValueError):
            continue
        if start > end or any(i in used for i in range(start, end + 1)):
            continue
        used.update(range(start, end + 1))
        sid = _clean(section.get("section_id"), 120) or f"section-{start + 1}"
        label = _clean(section.get("topic"), 240) or sid
        ranges.append((start, end, f"section-{sid}", label, "section"))

    # Fill uncovered ranges with clusters.  This also handles sparse LLM
    # section output without silently dropping source text.
    gap_start = None
    for index in range(len(paragraphs) + 1):
        covered = index < len(paragraphs) and index in used
        if index < len(paragraphs) and not covered and gap_start is None:
            gap_start = index
        if gap_start is not None and (index == len(paragraphs) or covered):
            ranges.append((gap_start, index - 1, "cluster", "", "semantic_cluster"))
            gap_start = None
    ranges.sort(key=lambda item: item[0])

    units: List[Dict[str, Any]] = []
    for start, end, prefix, label, kind in ranges:
        chunks = _chunk_range(paragraphs, start, end, max_chars, prefix, label, kind)
        for chunk in chunks:
            chunk["unit_id"] = f"unit-{len(units) + 1:04d}"
            chunk["source_range_id"] = prefix
            units.append(chunk)
    return units


def _digest_system_prompt() -> str:
    return (
        "你是长文翻译的文档理解器。只依据给出的语义单元原文，输出一个合法 JSON 对象。"
        "不要补写原文没有的事实；不确定的字段留空数组或空字符串。"
        "字段：summary（单元主旨）、key_entities（人物/地点/机构/作品）、"
        "key_terms（重要概念）、open_threads（需要后文确认的指代或叙事线索）、"
        "translation_notes（对语气、指代、术语连续性的翻译提示）。"
    )


def _normalize_digest(unit: Dict[str, Any], raw: Optional[Dict[str, Any]],
                     status: str = "model") -> Dict[str, Any]:
    raw = raw or {}
    return {
        "unit_id": unit["unit_id"],
        "kind": unit["kind"],
        "label": unit.get("label", ""),
        "start_segment": unit["start_segment"],
        "end_segment": unit["end_segment"],
        "summary": _clean(raw.get("summary") or raw.get("digest"), 1600),
        "key_entities": _string_list(raw.get("key_entities") or raw.get("entities")),
        "key_terms": _string_list(raw.get("key_terms") or raw.get("terms")),
        "open_threads": _string_list(raw.get("open_threads") or raw.get("threads")),
        "translation_notes": _string_list(raw.get("translation_notes") or raw.get("notes")),
        "status": status,
    }


def _fallback_digest(unit: Dict[str, Any]) -> Dict[str, Any]:
    source = unit.get("source", "")
    first = re.split(r"(?<=[.!?。！？])\s+", source.strip(), maxsplit=1)[0]
    digest = _normalize_digest(unit, {"summary": first or source[:600]},
                               status="deterministic_fallback")
    digest["warning"] = "模型未返回结构化语义摘要；仅使用单元首句作为临时上下文。"
    return digest


def generate_section_digests(
    units: Sequence[Dict[str, Any]],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str = "",
    call_llm: Optional[Callable] = None,
    max_workers: int = DEFAULT_DIGEST_WORKERS,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generate independent unit digests; results retain source order."""
    if not units:
        return [], ["语义摘要跳过：没有可用语义单元"]
    if call_llm is None:
        import core
        call_llm = core.call_llm
    system_prompt = _digest_system_prompt()

    def work(unit: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        user_prompt = (
            f"目标语言：{target_lang}\n"
            f"语义单元：{unit['unit_id']}（段落 {unit['start_segment']}-"
            f"{unit['end_segment']}）\n原文：\n{unit['source']}"
        )
        try:
            raw = _parse_object(_call(call_llm, provider, api_key, model,
                                      system_prompt, user_prompt))
            if raw is None:
                return _fallback_digest(unit), f"{unit['unit_id']}：返回不是结构化 JSON"
            return _normalize_digest(unit, raw), None
        except Exception as exc:  # provider failures must not corrupt the job
            return _fallback_digest(unit), f"{unit['unit_id']}：语义摘要失败（{str(exc)[:160]}）"

    results: List[Optional[Dict[str, Any]]] = [None] * len(units)
    warnings: List[str] = []
    workers = max(1, min(int(max_workers or 1), len(units)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, unit): index for index, unit in enumerate(units)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                digest, warning = future.result()
            except Exception as exc:  # defensive around custom executors/providers
                digest = _fallback_digest(units[index])
                warning = f"{units[index]['unit_id']}：语义摘要失败（{str(exc)[:160]}）"
            results[index] = digest
            if warning:
                warnings.append(warning)
    return [item for item in results if item is not None], warnings


def _synopsis_system_prompt() -> str:
    return (
        "你是长文翻译的全书理解器。根据多个语义单元摘要，输出一个合法 JSON 对象。"
        "只综合摘要中已有的信息，不臆造情节或事实。字段：summary（全书概要）、"
        "document_arc（论证/叙事发展）、themes（主题）、entities（跨单元实体）、"
        "terms（全书关键概念）、translation_notes（全书翻译连续性提示）。"
    )


def _normalize_synopsis(raw: Dict[str, Any], status: str = "model") -> Dict[str, Any]:
    return {
        "summary": _clean(raw.get("summary") or raw.get("synopsis"), 2400),
        "document_arc": _clean(raw.get("document_arc") or raw.get("arc"), 1600),
        "themes": _string_list(raw.get("themes")),
        "entities": _string_list(raw.get("entities")),
        "terms": _string_list(raw.get("terms") or raw.get("key_terms")),
        "translation_notes": _string_list(raw.get("translation_notes") or raw.get("notes")),
        "status": status,
    }


def generate_document_synopsis(
    digests: Sequence[Dict[str, Any]],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str = "",
    call_llm: Optional[Callable] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Map unit digests into one document-level synopsis."""
    if not digests:
        return {"summary": "", "status": "unavailable"}, ["全文概要跳过：没有语义摘要"]
    if call_llm is None:
        import core
        call_llm = core.call_llm
    digest_text = "\n\n".join(
        f"[{d['unit_id']} · 段 {d['start_segment']}-{d['end_segment']}]\n"
        f"主旨：{d.get('summary', '')}\n"
        f"实体：{'、'.join(d.get('key_entities') or [])}\n"
        f"概念：{'、'.join(d.get('key_terms') or [])}\n"
        f"提示：{'、'.join(d.get('translation_notes') or [])}"
        for d in digests
    )
    try:
        raw = _parse_object(_call(
            call_llm, provider, api_key, model, _synopsis_system_prompt(),
            f"目标语言：{target_lang}\n语义单元摘要：\n{digest_text}"))
        if raw is not None:
            return _normalize_synopsis(raw), []
    except Exception as exc:
        warning = f"全文概要失败（{str(exc)[:160]}）"
    else:
        warning = "全文概要失败：模型未返回结构化 JSON"

    fallback = _normalize_synopsis({
        "summary": "；".join(d.get("summary", "") for d in digests if d.get("summary"))[:2400],
        "translation_notes": [
            note for d in digests for note in (d.get("translation_notes") or [])
        ],
    }, status="deterministic_fallback")
    fallback["warning"] = warning
    return fallback, [warning]


def build_document_understanding(
    paragraphs: Sequence[str],
    document_profile: Optional[Dict[str, Any]],
    provider: str,
    api_key: str,
    model: str,
    target_lang: str = "",
    call_llm: Optional[Callable] = None,
    max_chars: int = DEFAULT_UNIT_CHARS,
    max_workers: int = DEFAULT_DIGEST_WORKERS,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """Build units, digests, and synopsis in one resumable-friendly call."""
    units = build_semantic_units(paragraphs, document_profile, max_chars=max_chars)
    digests, warnings = generate_section_digests(
        units, provider, api_key, model, target_lang, call_llm, max_workers=max_workers)
    synopsis, synopsis_warnings = generate_document_synopsis(
        digests, provider, api_key, model, target_lang, call_llm)
    return units, digests, synopsis, warnings + synopsis_warnings


def write_understanding_artifacts(
    job_root: Path,
    units: Sequence[Dict[str, Any]],
    digests: Sequence[Dict[str, Any]],
    synopsis: Dict[str, Any],
) -> None:
    """Persist the named understanding artifacts without touching state.json."""
    job_root.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("semantic_units.json", list(units)),
        ("section_digests.json", list(digests)),
        ("document_synopsis.json", synopsis),
    ):
        tmp = job_root / f"{name}.tmp"
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(job_root / name)


def digest_for_segment(digests: Sequence[Dict[str, Any]], segment_index: int) -> Optional[Dict[str, Any]]:
    for digest in digests or []:
        if digest.get("start_segment", 0) <= segment_index <= digest.get("end_segment", -1):
            return digest
    return None


def target_context_level(pair: Dict[str, Any]) -> str:
    """Return the strongest provenance available for target continuity."""
    if pair.get("human_accepted") or pair.get("accepted_by_human"):
        return "human_accepted"
    provenance = str(pair.get("target_provenance") or "")
    if provenance in ("human_accepted", "human"):
        return "human_accepted"
    if pair.get("reviewed") and (pair.get("from_tm") or provenance == "tm_approved"):
        return "tm_approved"
    if pair.get("reviewed") or provenance == "reviewed":
        return "reviewed"
    return "generated"


def select_target_context(
    pairs: Sequence[Dict[str, Any]],
    before_index: int,
    limit: int = 2,
) -> List[Dict[str, Any]]:
    """Select recent target context with explicit provenance priority."""
    candidates = []
    for index, pair in enumerate(list(pairs)[:max(0, before_index)]):
        target = pair.get("accepted_target") or pair.get("target")
        if target:
            candidates.append({
                "segment_index": index,
                "source": _clean(pair.get("source"), 800),
                "target": _clean(target, 1200),
                "level": target_context_level(pair),
            })
    selected: List[Dict[str, Any]] = []
    for level in TARGET_CONTEXT_LEVELS:
        selected.extend(item for item in reversed(candidates) if item["level"] == level)
        if len(selected) >= max(0, limit):
            break
    return sorted(selected[:max(0, limit)], key=lambda item: item["segment_index"])


def compile_context_packet(
    document_profile: Optional[Dict[str, Any]],
    document_synopsis: Optional[Dict[str, Any]],
    section_digest: Optional[Dict[str, Any]],
    glossary_text: str,
    previous_source: Sequence[str],
    previous_target: Sequence[Dict[str, Any]],
    next_source: Sequence[str],
    current_batch: Sequence[str],
    style_rules: str = "",
) -> Dict[str, Any]:
    """Compile a stable-order packet for generation/review prompts."""
    return {
        "document_profile": document_profile or {},
        "document_synopsis": document_synopsis or {},
        "section_digest": section_digest or {},
        "locked_glossary": glossary_text or "",
        "style_rules": style_rules or "",
        "previous_source_context": list(previous_source or []),
        "previous_accepted_target_context": list(previous_target or []),
        "next_source_context": list(next_source or []),
        "current_batch": list(current_batch or []),
    }


def render_context_packet(packet: Dict[str, Any]) -> str:
    """Render the packet with a stable prefix and current batch at the end."""
    profile = json.dumps(packet.get("document_profile") or {}, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":"))
    synopsis = packet.get("document_synopsis") or {}
    digest = packet.get("section_digest") or {}
    lines = [
        "【文档画像】\n" + profile,
        "【文体与翻译规则】\n" + (packet.get("style_rules") or ""),
        "【全文概要】\n" + _clean(synopsis.get("summary"), 2400),
        "【全文发展/论证】\n" + _clean(synopsis.get("document_arc"), 1600),
        "【当前语义单元摘要】\n" + _clean(digest.get("summary"), 1600),
        "【当前单元翻译提示】\n" + "、".join(digest.get("translation_notes") or []),
        "【锁定术语与范围规则】\n" + (packet.get("locked_glossary") or ""),
        "【前文原文上下文】\n" + "\n".join(
            f"- {item}" for item in packet.get("previous_source_context") or []),
        "【前文已接受译文连续性】\n" + "\n".join(
            f"- 段 {item.get('segment_index', '?')} [{item.get('level', 'generated')}] "
            f"原文：{item.get('source', '')}\n  译文：{item.get('target', '')}"
            for item in packet.get("previous_accepted_target_context") or []),
        "【后文原文上下文】\n" + "\n".join(
            f"- {item}" for item in packet.get("next_source_context") or []),
        "【待翻译段落（按序号返回等长数组）】",
    ]
    lines.extend(f"{index + 1}. {source}" for index, source in
                 enumerate(packet.get("current_batch") or []))
    return "\n\n".join(lines)


def context_metadata(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Small audit record; do not persist full prompt text in job state."""
    rendered = render_context_packet(packet)
    marker = "【待翻译段落（按序号返回等长数组）】"
    prefix_chars = rendered.find(marker)
    if prefix_chars < 0:
        prefix_chars = len(rendered)
    return {
        "section_id": (packet.get("section_digest") or {}).get("unit_id"),
        "previous_source_count": len(packet.get("previous_source_context") or []),
        "previous_target_segments": [
            item.get("segment_index") for item in packet.get("previous_accepted_target_context") or []
        ],
        "previous_target_levels": [
            item.get("level") for item in packet.get("previous_accepted_target_context") or []
        ],
        "next_source_count": len(packet.get("next_source_context") or []),
        "current_batch_count": len(packet.get("current_batch") or []),
        "prompt_chars": len(rendered),
        "context_prefix_chars": prefix_chars,
        "current_batch_chars": sum(len(item) for item in packet.get("current_batch") or []),
    }
