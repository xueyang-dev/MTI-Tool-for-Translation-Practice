"""Bounded evidence access and evidence-guided translation review."""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import terminology


class TranslationEvidenceIndex:
    """Read-only, bounded evidence surface for a translation reviewer."""

    ALLOWED_TOOLS = {
        "get_segment", "get_neighbors", "find_occurrences", "get_term",
        "get_document_profile", "get_document_synopsis", "get_section_digest",
        "get_translation_history", "get_findings",
    }

    def __init__(
        self,
        paragraphs: Sequence[str],
        pairs: Sequence[Dict[str, Any]],
        glossary: Sequence[Dict[str, Any]],
        document_profile: Optional[Dict[str, Any]] = None,
        document_synopsis: Optional[Dict[str, Any]] = None,
        section_digests: Optional[Sequence[Dict[str, Any]]] = None,
        findings: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        self.paragraphs = list(paragraphs or [])
        self.pairs = list(pairs or [])
        self.glossary = list(glossary or [])
        self.document_profile = document_profile or {}
        self.document_synopsis = document_synopsis or {}
        self.section_digests = list(section_digests or [])
        self.findings = list(findings or [])
        self.requests: List[Dict[str, Any]] = []

    def get_segment(self, segment_id: int) -> Dict[str, Any]:
        try:
            index = int(segment_id)
        except (TypeError, ValueError):
            return {}
        if not 0 <= index < len(self.paragraphs):
            return {}
        pair = self.pairs[index] if index < len(self.pairs) else {}
        return {
            "segment_id": index,
            "source": self.paragraphs[index],
            "target": pair.get("target", ""),
            "initial_target": pair.get("initial_target", ""),
            "accepted_target": pair.get("accepted_target", ""),
            "target_provenance": pair.get("target_provenance", ""),
            "reviewed": bool(pair.get("reviewed")),
            "from_tm": bool(pair.get("from_tm")),
        }

    def get_neighbors(self, segment_id: int, before: int = 3,
                      after: int = 3) -> List[Dict[str, Any]]:
        try:
            index = int(segment_id)
            before = max(0, min(5, int(before)))
            after = max(0, min(5, int(after)))
        except (TypeError, ValueError):
            return []
        start = max(0, index - before)
        end = min(len(self.paragraphs), index + after + 1)
        return [self.get_segment(i) for i in range(start, end) if i != index]

    def find_occurrences(self, source_expression: str,
                         selectors: Sequence[str] = ("first", "middle", "last")) -> List[Dict[str, Any]]:
        indices = terminology.find_occurrences(source_expression, self.paragraphs)
        if not indices:
            return []
        chosen = []
        if "first" in selectors:
            chosen.append(indices[0])
        if "middle" in selectors:
            chosen.append(indices[len(indices) // 2])
        if "last" in selectors:
            chosen.append(indices[-1])
        return [self.get_segment(i) for i in dict.fromkeys(chosen)]

    def get_term(self, term_id: Optional[str] = None,
                 source: Optional[str] = None) -> Dict[str, Any]:
        for entry in self.glossary:
            if term_id and entry.get("id") == term_id:
                return dict(entry)
            if source and str(entry.get("source") or "").casefold() == str(source).casefold():
                return dict(entry)
        return {}

    def get_document_profile(self) -> Dict[str, Any]:
        return dict(self.document_profile)

    def get_document_synopsis(self) -> Dict[str, Any]:
        return dict(self.document_synopsis)

    def get_section_digest(self, section_id: Optional[str] = None,
                           segment_id: Optional[int] = None) -> Dict[str, Any]:
        for digest in self.section_digests:
            if section_id and digest.get("unit_id") == section_id:
                return dict(digest)
            if segment_id is not None and digest.get("start_segment", 0) <= int(segment_id) <= digest.get("end_segment", -1):
                return dict(digest)
        return {}

    def get_translation_history(self, segment_id: int) -> Dict[str, Any]:
        segment = self.get_segment(segment_id)
        if not segment:
            return {}
        return {key: segment.get(key) for key in (
            "segment_id", "source", "initial_target", "target", "accepted_target",
            "target_provenance", "reviewed", "from_tm")}

    def get_findings(self, segment_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if segment_id is None:
            return [dict(item) for item in self.findings]
        try:
            index = int(segment_id)
        except (TypeError, ValueError):
            return []
        return [dict(item) for item in self.findings
                if item.get("segment_index") == index or item.get("segment_id") == index]

    def request(self, tool: str, **arguments: Any) -> Any:
        """Execute one allow-listed evidence request and record its trace."""
        if tool not in self.ALLOWED_TOOLS:
            raise ValueError(f"不支持的证据工具：{tool}")
        if tool == "get_segment":
            result = self.get_segment(arguments.get("segment_id"))
        elif tool == "get_neighbors":
            result = self.get_neighbors(arguments.get("segment_id"),
                                         arguments.get("before", 3),
                                         arguments.get("after", 3))
        elif tool == "find_occurrences":
            result = self.find_occurrences(
                arguments.get("source_expression") or arguments.get("source") or "",
                arguments.get("selectors") or ("first", "middle", "last"))
        elif tool == "get_term":
            result = self.get_term(arguments.get("term_id"), arguments.get("source"))
        elif tool == "get_document_profile":
            result = self.get_document_profile()
        elif tool == "get_document_synopsis":
            result = self.get_document_synopsis()
        elif tool == "get_section_digest":
            result = self.get_section_digest(arguments.get("section_id"),
                                             arguments.get("segment_id"))
        elif tool == "get_translation_history":
            result = self.get_translation_history(arguments.get("segment_id"))
        else:
            result = self.get_findings(arguments.get("segment_id"))
        self.requests.append({"tool": tool, "arguments": dict(arguments), "result": result})
        return result


def _parse_payload(text: Any) -> Optional[Any]:
    if not isinstance(text, str) or not text.strip():
        return None
    candidate = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.DOTALL)
    candidate = re.sub(r"\s*```$", "", candidate, flags=re.DOTALL).strip()
    try:
        return json.loads(candidate)
    except (TypeError, ValueError):
        decoder = json.JSONDecoder()
        for marker in ("[", "{"):
            for match in re.finditer(re.escape(marker), candidate):
                try:
                    value, _ = decoder.raw_decode(candidate[match.start():])
                except (TypeError, ValueError):
                    continue
                return value
    return None


def _normalize_findings(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity")
        if severity not in ("blocking", "actionable", "informational"):
            continue
        index = item.get("segment_index")
        if not isinstance(index, int):
            continue
        record = {
            "segment_index": index,
            "severity": severity,
            "reason": str(item.get("reason") or "审校发现问题"),
        }
        if item.get("suggested_target"):
            record["suggested_target"] = str(item["suggested_target"])
        out.append(record)
    return out


def _call(call_llm: Callable, provider: str, api_key: str, model: str,
          system_prompt: str, user_prompt: str) -> Any:
    try:
        return call_llm(provider, api_key, model, system_prompt, user_prompt,
                        temperature=0.2)
    except TypeError:
        return call_llm(provider, api_key, model, system_prompt, user_prompt)


def review_translation_batch_with_evidence(
    sources: Sequence[str],
    targets: Sequence[str],
    glossary_text: str,
    style_rules: str,
    target_lang: str,
    provider: str,
    api_key: str,
    model: str,
    evidence_index: TranslationEvidenceIndex,
    call_llm: Optional[Callable] = None,
    max_rounds: int = 2,
    blind: bool = False,
) -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Review a batch, allowing at most two rounds of explicit evidence requests."""
    if call_llm is None:
        import core
        call_llm = core.call_llm
    numbered = "\n".join(
        f"{i + 1}. 原文：{source}\n   译文：{target}"
        for i, (source, target) in enumerate(zip(sources, targets))
    )
    system_prompt = (
        "你是一位独立的翻译审校专家，负责审查机器译文。"
        + ("这是盲审：不要提及修复候选或内部流程。" if blind else "")
        + "只报告真实存在的问题，不要为低风险或主观偏好制造 finding。"
        "severity 只允许 blocking、actionable、informational。"
        "如果需要全文证据，先在 evidence_requests 中请求工具；拿到证据后再作最终判断。"
        "严格输出 JSON 对象：{\"findings\": [...], \"evidence_requests\": "
        "[{\"tool\": \"get_segment\", \"arguments\": {}}]}。"
        "若无问题 findings 必须为空数组。\n" + glossary_text + "\n" + style_rules
    )
    base_prompt = f"待审校段落（目标语言：{target_lang}）：\n{numbered}"
    prompt = base_prompt
    trace: Dict[str, Any] = {"blind": blind, "rounds": [], "requests": [], "decision": ""}
    latest_findings: List[Dict[str, Any]] = []
    for round_index in range(max(1, int(max_rounds or 1))):
        try:
            payload = _parse_payload(_call(
                call_llm, provider, api_key, model, system_prompt, prompt))
        except Exception as exc:
            trace["decision"] = "failed"
            trace["error"] = str(exc)[:240]
            return [], True, trace
        if isinstance(payload, list):
            latest_findings = _normalize_findings(payload)
            trace["rounds"].append({"round": round_index, "findings": latest_findings,
                                    "requests": []})
            trace["decision"] = "clean" if not latest_findings else "findings"
            return latest_findings, False, trace
        if not isinstance(payload, dict):
            trace["decision"] = "failed"
            return [], True, trace
        latest_findings = _normalize_findings(payload.get("findings"))
        raw_requests = payload.get("evidence_requests") or payload.get("requests") or []
        requests = [item for item in raw_requests if isinstance(item, dict)][:5]
        round_trace = {"round": round_index, "findings": latest_findings, "requests": []}
        evidence = []
        for request in requests:
            tool = str(request.get("tool") or request.get("type") or "")
            arguments = request.get("arguments") or request.get("args") or {}
            if not isinstance(arguments, dict):
                arguments = {}
            try:
                result = evidence_index.request(tool, **arguments)
            except (TypeError, ValueError) as exc:
                result = {"error": str(exc)}
            round_trace["requests"].append({"tool": tool, "arguments": arguments,
                                            "result": result})
            trace["requests"].append(round_trace["requests"][-1])
            evidence.append({"tool": tool, "result": result})
        trace["rounds"].append(round_trace)
        if not evidence:
            trace["decision"] = "findings" if latest_findings else "clean"
            return latest_findings, False, trace
        prompt = base_prompt + (
            "\n\n【按审校请求返回的证据】\n" +
            json.dumps(evidence, ensure_ascii=False, indent=2) +
            "\n请基于证据作最终判断；本轮不要再请求证据。")
    trace["decision"] = "failed"
    return latest_findings, True, trace
