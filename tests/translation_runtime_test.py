"""Regression tests for the long-document translation runtime additions."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import checkpoint, context, knowledge, models, repair
from transpraxis.translation_evidence import TranslationEvidenceIndex, review_translation_batch_with_evidence


def test_context_understanding_and_target_priority(tmp_path):
    paragraphs = ["The first ecological succession appears here.",
                  "The second section continues the ecological succession."]
    profile = {"sections": [{"section_id": "s1", "start_segment": 0,
                              "end_segment": 1, "topic": "生态过程"}]}

    def llm(provider, key, model, system, user, temperature=0.1):
        if "全书理解器" in system:
            return json.dumps({"summary": "全文概要", "document_arc": "发展", "themes": ["生态"]})
        return json.dumps({"summary": "单元概要", "translation_notes": ["保持术语连续"]})

    units, digests, synopsis, warnings = context.build_document_understanding(
        paragraphs, profile, "DeepSeek", "k", "m", "简体中文", call_llm=llm,
        max_workers=1)
    assert len(units) == 1 and len(digests) == 1
    assert synopsis["summary"] == "全文概要" and not warnings
    context.write_understanding_artifacts(tmp_path, units, digests, synopsis)
    assert (tmp_path / "section_digests.json").is_file()
    assert (tmp_path / "document_synopsis.json").is_file()

    pairs = [
        {"source": "a", "target": "甲", "reviewed": False},
        {"source": "b", "target": "乙", "reviewed": True},
        {"source": "c", "target": "丙", "human_accepted": True, "reviewed": True},
    ]
    selected = context.select_target_context(pairs, 3, limit=2)
    assert [item["level"] for item in selected] == ["reviewed", "human_accepted"]
    packet = context.compile_context_packet(profile, synopsis, digests[0], "glossary",
                                            ["before"], selected, ["after"], ["now"])
    assert "【全文概要】" in context.render_context_packet(packet)
    assert context.context_metadata(packet)["previous_target_levels"] == [
        "reviewed", "human_accepted"]


def test_knowledge_candidate_first_occurrence_and_locked_conflict():
    paragraphs = ["The river bank is old.", "The river bank is wide."]
    existing = [models.normalize_glossary_entry({
        "source": "river bank", "target": "河岸", "status": "locked"})]

    def llm(*args, **kwargs):
        return json.dumps([{"source_expression": "river bank",
                            "observed_target": "河流银行", "kind": "term"}])

    candidates, events, warning = knowledge.observe_batch(
        [paragraphs[1]], ["河流银行很宽。"], paragraphs,
        [{"source": paragraphs[0], "target": "河岸很老。"}], existing, 1,
        "DeepSeek", "k", "m", call_llm=llm)
    assert candidates == []
    assert warning is None
    assert events[0]["type"] == "target_conflict"
    assert events[0]["preferred_target"] == "河岸"

    candidates, events, warning = knowledge.observe_batch(
        [paragraphs[1]], ["生态演替很快。"],
        ["Ecological succession starts.", paragraphs[1]],
        [{"source": "Ecological succession starts.", "target": "生态演替开始。"}],
        [], 1, "DeepSeek", "k", "m",
        call_llm=lambda *args, **kwargs: json.dumps([{
            "source_expression": "ecological succession", "observed_target": "生态演替"}]))
    assert candidates[0]["first_observed_segment"] == 0
    assert candidates[0]["occurrences"] == [0]
    assert knowledge.provisional_hints(candidates)[0]["status"] == "provisional"


def test_evidence_requests_are_bounded_and_traced():
    index = TranslationEvidenceIndex(
        ["The field matters.", "The field repeats."],
        [{"source": "The field matters.", "target": "田野很重要。"},
         {"source": "The field repeats.", "target": "田野重复。"}],
        [], document_synopsis={"summary": "全文"})
    replies = iter([
        json.dumps({"findings": [], "evidence_requests": [{
            "tool": "find_occurrences",
            "arguments": {"source_expression": "field", "selectors": ["first", "last"]},
        }]}),
        "[]",
    ])
    findings, failed, trace = review_translation_batch_with_evidence(
        ["The field matters."], ["田野很重要。"], "", "", "中文",
        "DeepSeek", "k", "m", index,
        call_llm=lambda *args, **kwargs: next(replies))
    assert findings == [] and not failed
    assert len(index.requests) == 1
    assert trace["requests"][0]["result"][0]["segment_id"] == 0


def test_shadow_overlay_and_checkpoint_recovery(tmp_path):
    overlay = repair.create_overlay(["初译"], ["修复"], [{"segment_index": 0}], "deterministic")
    accepted = repair.evaluate_overlay(overlay, [], [])
    assert accepted["status"] == "accepted"
    assert repair.promoted_targets(accepted) == ["修复"]

    rejected = repair.evaluate_overlay(
        repair.create_overlay(["初译"], ["坏修复"], [], "deterministic"),
        [{"severity": "blocking", "reason": "结构损坏"}], [])
    assert rejected["status"] == "rejected"
    assert repair.promoted_targets(rejected) == ["初译"]

    state = {"pairs": [{"source": "s", "target": "t", "reviewed": True}]}
    tm = {}
    checkpoint.append_event(tmp_path, {
        "batch": 0, "phase": "tm_promotion_pending",
        "entries": [{"source": "s", "target": "t"}],
    })
    changed, pending = checkpoint.reconcile_translation_memory(tm, state, tmp_path)
    assert changed and pending == 1 and tm["s"]["target"] == "t"
