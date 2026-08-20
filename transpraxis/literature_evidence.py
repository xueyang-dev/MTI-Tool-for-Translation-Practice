"""Deterministic literature source snapshots, evidence and grounded claims.

This is intentionally a local, bounded pipeline.  It reads only material the
user registered (embedded text/notes/excerpts or an explicit local path), keeps
exact source locations, and never discovers or completes bibliography entries.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .academic_evidence import normalize_literature_registry, stable_hash

SOURCES_VERSION = "literature-sources-v1"
EVIDENCE_VERSION = "literature-evidence-v1"
CLAIMS_VERSION = "literature-claims-v1"

CLAIM_TYPES = {
    "theory_definition", "theoretical_position", "empirical_finding",
    "method_claim", "contextual_claim", "limitation", "user_interpretation",
}


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _split_piece(text: str, maximum: int = 1200) -> List[str]:
    text = text.strip()
    if not text:
        return []
    return [text[i:i + maximum] for i in range(0, len(text), maximum)]


def _block(source_id: str, text: str, location: Dict[str, Any], provenance: str,
           evidence_type: str, verification_status: str,
           origin_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    exact = str(text or "").strip()
    if not exact:
        return None
    identity = {
        "source_id": source_id, "location": location, "text": exact,
        "provenance": provenance, "origin_id": origin_id,
    }
    block_id = "LB-" + stable_hash(identity)[:16]
    return {
        "block_id": block_id,
        "text": exact,
        "location": location,
        "provenance": provenance,
        "evidence_type": evidence_type,
        "verification_status": verification_status,
        "origin_id": origin_id,
        "content_hash": stable_hash(identity),
    }


def _paragraph_blocks(source_id: str, text: str, kind: str,
                      provenance: str = "source_text_verified") -> List[Dict[str, Any]]:
    lines = str(text or "").splitlines()
    out: List[Dict[str, Any]] = []
    heading: Optional[str] = None
    start: Optional[int] = None
    buffer: List[str] = []

    def flush(end_line: int) -> None:
        nonlocal start, buffer
        joined = "\n".join(buffer).strip()
        if not joined or start is None:
            start, buffer = None, []
            return
        for chunk_index, piece in enumerate(_split_piece(joined), 1):
            location = {
                "kind": kind, "line_start": start, "line_end": end_line,
                "heading": heading, "chunk": chunk_index,
            }
            item = _block(source_id, piece, location, provenance,
                          "source_passage", "source_text_verified")
            if item:
                out.append(item)
        start, buffer = None, []

    for line_number, line in enumerate(lines, 1):
        if kind == "markdown" and re.match(r"^#{1,6}\s+", line.strip()):
            flush(line_number - 1)
            heading = re.sub(r"^#{1,6}\s+", "", line.strip())
            continue
        if not line.strip():
            flush(line_number - 1)
            continue
        if start is None:
            start = line_number
        buffer.append(line)
    flush(len(lines))
    return out


def _pdf_blocks(source_id: str, path: Path) -> List[Dict[str, Any]]:
    try:
        import fitz
    except Exception as exc:  # pragma: no cover - dependency is optional at runtime
        raise RuntimeError(f"PDF extraction unavailable: {exc}") from exc
    out: List[Dict[str, Any]] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            page_text = page.get_text("text") or ""
            for chunk_index, piece in enumerate(_split_piece(page_text), 1):
                item = _block(
                    source_id, piece,
                    {"kind": "pdf_page", "page": page_index + 1,
                     "chunk": chunk_index},
                    "source_text_verified", "source_passage",
                    "source_text_verified",
                )
                if item:
                    out.append(item)
    return out


def _docx_blocks(source_id: str, path: Path) -> List[Dict[str, Any]]:
    from docx import Document

    out: List[Dict[str, Any]] = []
    heading: Optional[str] = None
    for paragraph_index, paragraph in enumerate(Document(path).paragraphs, 1):
        text = paragraph.text.strip()
        if not text:
            continue
        style = str(getattr(paragraph.style, "name", "") or "")
        if style.casefold().startswith("heading"):
            heading = text
            continue
        for chunk_index, piece in enumerate(_split_piece(text), 1):
            item = _block(
                source_id, piece,
                {"kind": "docx_paragraph", "paragraph": paragraph_index,
                 "heading": heading, "chunk": chunk_index},
                "source_text_verified", "source_passage",
                "source_text_verified",
            )
            if item:
                out.append(item)
    return out


def _structured_blocks(source_id: str, values: Iterable[Any], *, kind: str,
                       provenance: str, evidence_type: str,
                       verification_status: str) -> List[Dict[str, Any]]:
    out = []
    for index, value in enumerate(values or [], 1):
        if isinstance(value, dict):
            text = value.get("text") or value.get("excerpt") or value.get("note")
            origin_id = str(value.get("note_id") or value.get("excerpt_id")
                            or value.get("passage_id") or f"{kind}-{index}")
            location = value.get("location") if isinstance(value.get("location"), dict) else {}
        else:
            text = value
            origin_id = f"{kind}-{index}"
            location = {}
        canonical_location = {"kind": kind, "origin_id": origin_id, **location}
        item = _block(source_id, str(text or ""), canonical_location, provenance,
                      evidence_type, verification_status, origin_id)
        if item:
            out.append(item)
    return out


def _materialize_source(source: Dict[str, Any], maximum_blocks: int) \
        -> Tuple[Dict[str, Any], List[str]]:
    source = dict(source)
    source_id = source["source_id"]
    warnings: List[str] = []
    blocks: List[Dict[str, Any]] = []
    binary_hash: Optional[str] = None

    local_path = source.get("local_source_path")
    if local_path:
        path = Path(local_path).expanduser()
        if not path.is_file():
            warnings.append(f"{source_id}: local source path is unavailable: {local_path}")
        else:
            try:
                raw = path.read_bytes()
                binary_hash = _sha_bytes(raw)
                suffix = path.suffix.casefold()
                if suffix == ".pdf":
                    blocks.extend(_pdf_blocks(source_id, path))
                elif suffix == ".docx":
                    blocks.extend(_docx_blocks(source_id, path))
                elif suffix in (".md", ".markdown", ".txt"):
                    kind = "markdown" if suffix in (".md", ".markdown") else "text_lines"
                    blocks.extend(_paragraph_blocks(
                        source_id, raw.decode("utf-8"), kind))
                else:
                    warnings.append(f"{source_id}: unsupported local source type: {suffix}")
            except Exception as exc:
                warnings.append(f"{source_id}: source extraction failed: {exc}")

    embedded = source.get("content")
    if isinstance(embedded, str) and embedded.strip():
        content_format = str(source.get("content_format") or "text").casefold()
        kind = "markdown" if content_format in ("md", "markdown") else "text_lines"
        blocks.extend(_paragraph_blocks(source_id, embedded, kind))
        binary_hash = binary_hash or _sha_bytes(embedded.encode("utf-8"))

    blocks.extend(_structured_blocks(
        source_id, source.get("notes") or [], kind="user_note",
        provenance="user_note", evidence_type="note",
        verification_status="user_attested"))
    blocks.extend(_structured_blocks(
        source_id, source.get("manual_excerpts") or [], kind="manual_excerpt",
        provenance="manual_excerpt", evidence_type="excerpt",
        verification_status="user_attested"))
    blocks.extend(_structured_blocks(
        source_id, source.get("extracted_passages") or [], kind="model_extracted_passage",
        provenance="model_extracted_from_source", evidence_type="source_passage",
        verification_status="needs_review"))

    seen_blocks = set()
    all_blocks = []
    for item in blocks:
        if item["block_id"] not in seen_blocks:
            seen_blocks.add(item["block_id"])
            all_blocks.append(item)
    bounded = len(all_blocks) > maximum_blocks
    kept = all_blocks[:maximum_blocks]
    provenances = {x["provenance"] for x in kept}
    if any(x == "source_text_verified" for x in provenances):
        availability = source.get("content_availability")
        if availability not in ("full_text_available", "partial_text_available"):
            availability = "full_text_available"
    elif provenances & {"manual_excerpt", "model_extracted_from_source"}:
        availability = "partial_text_available"
    elif "user_note" in provenances:
        availability = "notes_only"
    else:
        availability = "metadata_only"

    source_content_hash = stable_hash({
        "binary_hash": binary_hash,
        "blocks": [{"block_id": x["block_id"], "content_hash": x["content_hash"]}
                   for x in kept],
    }) if kept or binary_hash else None
    canonical = {
        key: value for key, value in source.items()
        if key not in {"content", "notes", "manual_excerpts", "extracted_passages"}
    }
    canonical.update({
        "content_availability": availability,
        "content_hash": source_content_hash,
        "source_file_hash": binary_hash,
        "content_blocks": kept,
        "content_block_count": len(kept),
        "content_blocks_bounded": bounded,
    })
    metadata = {k: v for k, v in canonical.items()
                if k not in {"content_hash", "source_file_hash", "content_blocks", "content_block_count",
                             "content_blocks_bounded", "metadata_hash"}}
    canonical["metadata_hash"] = stable_hash(metadata)
    return canonical, warnings


def build_literature_sources(sources: Optional[Iterable[Dict[str, Any]]],
                             maximum_blocks_per_source: int = 80) -> Dict[str, Any]:
    normalized = normalize_literature_registry(sources)
    materialized = []
    warnings: List[str] = []
    for source in normalized:
        item, item_warnings = _materialize_source(source, maximum_blocks_per_source)
        materialized.append(item)
        warnings.extend(item_warnings)
    metadata_hash = stable_hash([
        {k: v for k, v in x.items()
         if k not in {"content_blocks", "content_hash", "source_file_hash"}}
        for x in materialized
    ])
    sources_content_hash = stable_hash([
        {"source_id": x["source_id"], "content_hash": x.get("content_hash")}
        for x in materialized
    ])
    artifact = {
        "schema_version": SOURCES_VERSION,
        "sources": materialized,
        "sources_metadata_hash": metadata_hash,
        "sources_content_hash": sources_content_hash,
        "warnings": warnings,
    }
    artifact["content_hash"] = stable_hash(
        {k: v for k, v in artifact.items() if k != "content_hash"})
    return artifact


def build_literature_evidence(source_artifact: Dict[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for source in source_artifact.get("sources") or []:
        blocks = source.get("content_blocks") or []
        for block in blocks:
            evidence_id = "LE-" + stable_hash({
                "source_id": source["source_id"], "block_id": block["block_id"]
            })[:16]
            item = {
                "evidence_id": evidence_id,
                "source_id": source["source_id"],
                "source_block_id": block["block_id"],
                "location": block["location"],
                "evidence_text": block["text"],
                "note": block["text"] if block["evidence_type"] == "note" else None,
                "evidence_type": block["evidence_type"],
                "provenance": block["provenance"],
                "verification_status": block["verification_status"],
                "source_content_hash": source.get("content_hash"),
                "eligible_for_claim": bool(block["text"]),
            }
            item["content_hash"] = stable_hash(
                {k: v for k, v in item.items() if k != "content_hash"})
            items.append(item)
        if not blocks:
            item = {
                "evidence_id": "LE-" + stable_hash({
                    "source_id": source["source_id"], "metadata_only": True})[:16],
                "source_id": source["source_id"],
                "source_block_id": None,
                "location": {"kind": "metadata_only"},
                "evidence_text": "",
                "note": None,
                "evidence_type": "metadata_only",
                "provenance": "metadata_only",
                "verification_status": "metadata_only",
                "source_content_hash": source.get("content_hash"),
                "eligible_for_claim": False,
            }
            item["content_hash"] = stable_hash(
                {k: v for k, v in item.items() if k != "content_hash"})
            items.append(item)
    artifact = {"schema_version": EVIDENCE_VERSION, "items": items}
    artifact["content_hash"] = stable_hash(items)
    return artifact


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(text or "").strip(),
                       flags=re.DOTALL)
    try:
        value = json.loads(candidate)
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def build_literature_claims(
    source_artifact: Dict[str, Any], evidence_artifact: Dict[str, Any],
    call_llm: Callable, provider: str, api_key: str, model: str,
    maximum_evidence_items: int = 80,
) -> Dict[str, Any]:
    """Classify bounded exact evidence into claims; never create source text."""
    sources = {x["source_id"]: x for x in source_artifact.get("sources") or []}
    evidence = {x["evidence_id"]: x for x in evidence_artifact.get("items") or []}
    usable = [x for x in evidence.values() if x.get("eligible_for_claim")]
    usable_total = len(usable)
    usable = usable[:maximum_evidence_items]
    system = (
        "你是文献主张抽取器。只把输入中的逐字证据归纳为范围克制的 Literature Claim；"
        "不得补充输入外的作者、年份、理论、原文或事实。Literature Claim 不是引文，也不是"
        "整篇报告的 Global Claim。每条必须绑定同一 source_id 下至少一个 evidence_id。只输出"
        "JSON：{\"claims\":[{\"statement\":\"...\",\"source_id\":\"...\","
        "\"evidence_ids\":[\"LE-...\"],\"claim_type\":\"theory_definition|"
        "theoretical_position|empirical_finding|method_claim|contextual_claim|limitation|"
        "user_interpretation\",\"confidence\":\"low|medium|high\"}]}。"
    )
    payload = {
        "sources": [{k: x.get(k) for k in (
            "source_id", "title", "authors", "year", "source_type",
            "verification_status", "content_availability")}
            for x in sources.values()],
        "evidence": [{k: x.get(k) for k in (
            "evidence_id", "source_id", "location", "evidence_text",
            "evidence_type", "provenance", "verification_status")}
            for x in usable],
    }
    raw: Optional[Dict[str, Any]] = None
    if usable:
        user_prompt = json.dumps(payload, ensure_ascii=False)
        for attempt in range(2):
            suffix = "" if attempt == 0 else "\n上次输出无效；仅输出合法 JSON 对象。"
            response = call_llm(provider, api_key, model, system + suffix,
                                user_prompt, temperature=0.1)
            raw = _parse_json(response)
            if raw is not None:
                break
    claims: List[Dict[str, Any]] = []
    rejected = 0
    for item in (raw or {}).get("claims") or []:
        if not isinstance(item, dict):
            rejected += 1
            continue
        statement = _text(item.get("statement"))
        source_id = str(item.get("source_id") or "")
        evidence_ids = [str(x) for x in item.get("evidence_ids") or []]
        evidence_ids = list(dict.fromkeys(x for x in evidence_ids
                                          if x in evidence and evidence[x].get(
                                              "source_id") == source_id
                                          and evidence[x].get("eligible_for_claim")))
        if not statement or source_id not in sources or not evidence_ids:
            rejected += 1
            continue
        provenances = {evidence[x].get("provenance") for x in evidence_ids}
        if provenances <= {"source_text_verified"}:
            grounded = "grounded"
        elif "model_extracted_from_source" in provenances:
            grounded = "needs_review"
        else:
            grounded = "grounded_user_material"
        claim_type = str(item.get("claim_type") or "contextual_claim")
        if claim_type not in CLAIM_TYPES:
            claim_type = "contextual_claim"
        confidence = str(item.get("confidence") or "low").lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "low"
        claim = {
            "literature_claim_id": f"LC-{len(claims) + 1:03d}",
            "statement": statement,
            "source_id": source_id,
            "supporting_evidence_ids": evidence_ids,
            "claim_type": claim_type,
            "confidence": confidence,
            "evidence_grounded_status": grounded,
        }
        claim["content_hash"] = stable_hash(
            {k: v for k, v in claim.items() if k != "content_hash"})
        claims.append(claim)
    artifact = {
        "schema_version": CLAIMS_VERSION,
        "items": claims,
        "extraction": {
            "bounded": usable_total > maximum_evidence_items,
            "evidence_items_considered": len(usable),
            "rejected_claims": rejected,
            "status": "complete" if raw is not None else (
                "evidence_missing" if not usable else "model_failed"),
        },
    }
    artifact["content_hash"] = stable_hash(claims)
    return artifact


def source_index(artifact: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {x["source_id"]: x for x in artifact.get("sources") or []}


def evidence_index(artifact: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {x["evidence_id"]: x for x in artifact.get("items") or []}


def claim_index(artifact: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {x["literature_claim_id"]: x for x in artifact.get("items") or []}
