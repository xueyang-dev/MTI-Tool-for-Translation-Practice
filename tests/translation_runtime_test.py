"""Regression tests for the long-document translation runtime additions."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from transpraxis import checkpoint, context, delivery, knowledge, models, repair
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
        ["Ecological succession continues."], ["生态演替很快。"],
        ["Ecological succession starts.", "Ecological succession continues."],
        [{"source": "Ecological succession starts.", "target": "生态演替开始。"}],
        [], 1, "DeepSeek", "k", "m",
        call_llm=lambda *args, **kwargs: json.dumps([{
            "segment_id": 1, "source_expression": "ecological succession",
            "observed_target": "生态演替"}]))
    assert candidates[0]["first_observed_segment"] == 1
    assert candidates[0]["occurrences"] == [0, 1]
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
    assert overlay["input_hash"] and overlay["candidate_hash"]
    assert overlay["candidate_hash"] != repair.create_overlay(
        ["初译"], ["另一修复"], [], "deterministic")["candidate_hash"]
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


def test_review_failed_must_not_mark_segment_reviewed_or_promote_tm_or_knowledge(tmp_path):
    old_output, old_call = core.OUTPUT_DIR, core.call_llm
    try:
        core.OUTPUT_DIR = tmp_path

        def llm(provider, key, model, system, user, temperature=0.1):
            if "独立的翻译审校专家" in system:
                raise RuntimeError("review provider timeout")
            if "学术翻译专家" in system:
                return json.dumps(["这是译文。"])
            return "[]"

        core.call_llm = llm
        state = core.new_job_state("failed-review.docx")
        state["paras"] = ["The source sentence is safe."]
        result = core.translate_stage(
            state, "failed-review-job", [], "DeepSeek", "k", "m", "简体中文", "",
            enable_review=True, use_tm=True)
        pair = result["pairs"][0]
        assert pair["review_status"] == "review_failed"
        assert pair["reviewed"] is False
        assert result["review_stats"]["review_failed"] == 1
        assert result["knowledge_candidates"] == []
        assert core.load_tm() == {}
    finally:
        core.OUTPUT_DIR, core.call_llm = old_output, old_call


def test_evidence_segment_id_is_global_across_later_batches():
    paragraphs = [f"source {index}" for index in range(40)]
    pairs = [{"source": source, "target": f"target {index}"}
             for index, source in enumerate(paragraphs)]
    index = TranslationEvidenceIndex(paragraphs, pairs, [])
    replies = iter([
        json.dumps({"findings": [], "evidence_requests": [{
            "tool": "get_segment", "arguments": {"segment_id": 36},
        }]}),
        json.dumps({"findings": [{
            "segment_id": 36, "severity": "actionable", "reason": "问题",
            "evidence_refs": ["E1"],
        }]}),
    ])
    findings, failed, trace = review_translation_batch_with_evidence(
        [paragraphs[36]], ["candidate"], "", "", "中文", "p", "k", "m", index,
        call_llm=lambda *args, **kwargs: next(replies), segment_ids=[36])
    assert not failed and findings[0]["segment_id"] == 36
    assert trace["requests"][0]["result"]["segment_id"] == 36
    assert trace["completion_receipt"]["reviewed_segment_ids"] == [36]


def test_blind_review_cannot_read_formal_or_initial_target():
    index = TranslationEvidenceIndex(
        ["source"], [{"source": "source", "target": "formal",
                      "initial_target": "initial", "accepted_target": "accepted",
                      "target_provenance": "reviewed", "reviewed": True}], [],
        blind=True, candidate_targets={0: "candidate"})
    segment = index.request("get_segment", segment_id=0)
    history = index.request("get_translation_history", segment_id=0)
    assert segment == {"segment_id": 0, "source": "source", "target": "candidate"}
    assert history == segment
    assert "formal" not in json.dumps(segment, ensure_ascii=False)
    assert "initial" not in json.dumps(history, ensure_ascii=False)
    assert index.request("get_findings") == []


def test_delivery_approval_does_not_imply_segment_human_acceptance():
    state = {"p2_done": True, "pairs": [{"source": "s", "target": "t"}]}
    state, ok, errors = delivery.approve_delivery(state)
    assert ok and not errors
    assert state["delivery_approved_by_human"] is True
    assert state["pairs"][0].get("human_accepted") is None
    assert state["pairs"][0].get("target_provenance") is None


def test_multiple_observations_from_one_segment_keep_correct_provenance():
    payload = json.dumps([
        {"segment_id": 5, "source_expression": "alpha",
         "observed_target": "阿尔法", "kind": "term"},
        {"segment_id": 5, "source_expression": "beta",
         "observed_target": "贝塔", "kind": "term"},
    ])
    candidates, events, warning = knowledge.observe_batch(
        ["alpha beta"], ["阿尔法和贝塔"], ["alpha beta"],
        [{}, {}, {}, {}, {}], [], 5, "p", "k", "m",
        call_llm=lambda *args, **kwargs: payload, segment_ids=[5])
    assert warning is None and len(candidates) == 2
    assert {item["first_observed_segment"] for item in candidates} == {5}
    assert {item["segment_id"] for item in events} == {5}


def test_batch_must_not_cross_semantic_unit_boundary():
    batches = core.make_batches(
        ["a", "b", "c", "d"], batch_size=4, max_chars=100,
        semantic_units=[{"start_segment": 0, "end_segment": 1},
                        {"start_segment": 2, "end_segment": 3}])
    assert batches == [["a", "b"], ["c", "d"]]


def test_understanding_resume_reuses_completed_unit_digests(tmp_path):
    paragraphs = ["First unit.", "Second unit."]
    profile = {"sections": [
        {"section_id": "one", "start_segment": 0, "end_segment": 0},
        {"section_id": "two", "start_segment": 1, "end_segment": 1},
    ]}
    units = context.build_semantic_units(paragraphs, profile)
    saved_digest = {
        "unit_id": units[0]["unit_id"], "kind": units[0]["kind"],
        "label": units[0]["label"], "start_segment": 0, "end_segment": 0,
        "summary": "already saved", "key_entities": [], "key_terms": [],
        "open_threads": [], "translation_notes": [], "status": "model",
    }
    context.write_understanding_artifacts(
        tmp_path, units, [saved_digest], {"summary": "", "status": "pending"})
    calls = []

    def llm(provider, key, model, system, user, temperature=0.1):
        calls.append(system)
        if "全书理解器" in system:
            return json.dumps({"summary": "book"})
        return json.dumps({"summary": "new unit"})

    _, digests, synopsis, warnings = context.build_document_understanding(
        paragraphs, profile, "p", "k", "m", "中文", call_llm=llm,
        max_workers=1, checkpoint_dir=tmp_path)
    assert digests[0]["summary"] == "already saved"
    assert len(calls) == 2  # only the missing unit digest plus synopsis
    assert synopsis["summary"] == "book" and not warnings


def test_synopsis_uses_hierarchical_reduce_for_long_digest_list():
    digests = [{
        "unit_id": f"unit-{index}", "start_segment": index, "end_segment": index,
        "summary": "x" * 300, "key_entities": [], "key_terms": [],
        "translation_notes": [],
    } for index in range(8)]
    calls = []

    def llm(provider, key, model, system, user, temperature=0.1):
        calls.append(user)
        return json.dumps({"summary": "reduced", "document_arc": "arc"})

    synopsis, warnings = context.generate_document_synopsis(
        digests, "p", "k", "m", "中文", call_llm=llm, max_chunk_chars=700)
    assert synopsis["summary"] == "reduced" and not warnings
    assert len(calls) > 1


def test_evidence_final_round_cannot_request_more_evidence():
    replies = iter([
        json.dumps({"findings": [], "evidence_requests": [{
            "tool": "get_segment", "arguments": {"segment_id": 0},
        }]}),
        json.dumps({"findings": [], "evidence_requests": [{
            "tool": "get_segment", "arguments": {"segment_id": 0},
        }]}),
    ])
    index = TranslationEvidenceIndex(["source"], [{"target": "target"}], [])
    findings, failed, trace = review_translation_batch_with_evidence(
        ["source"], ["target"], "", "", "中文", "p", "k", "m", index,
        call_llm=lambda *args, **kwargs: next(replies))
    assert findings == [] and failed
    assert trace["completion_receipt"]["status"] == "failed"


def test_malformed_section_ranges_are_skipped_not_crashed():
    units = context.build_semantic_units(
        ["a", "b"], {"sections": [
            {"start_segment": None, "end_segment": 1},
            {"start_segment": "unknown", "end_segment": 1},
            {"start_segment": 0, "end_segment": 1},
        ]})
    assert len(units) == 1 and units[0]["start_segment"] == 0
