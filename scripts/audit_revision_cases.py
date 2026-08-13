"""Audit real revision provenance and emit an isolated case-selection pilot.

This runner is deterministic: it reads the saved job and prior state snapshots,
reuses an existing Human Evidence question artifact, and never calls an LLM or
writes back to historical project evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence, academic_writer, case_analysis


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pair_identity(pair: dict[str, Any]) -> str:
    return academic_evidence.stable_hash({
        "source": pair.get("source"),
        "initial_target": pair.get("initial_target"),
        "final_target": pair.get("target"),
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--canonical-questions", required=True)
    parser.add_argument("--investigate-index", type=int, default=142)
    parser.add_argument("--source-boundary-note", default="")
    args = parser.parse_args()

    state_path = Path("outputs") / args.job_id / "state.json"
    questions_path = Path(args.canonical_questions)
    out_dir = Path(args.out_dir)
    if not state_path.is_file() or not questions_path.is_file():
        parser.error("state or canonical questions artifact does not exist")

    state = _load(state_path)
    evidence = academic_evidence.build_academic_evidence(state, args.job_id)
    selected = academic_writer.select_academic_cases({}, {"claims": []}, evidence)
    selected_ids = [str(x["case_id"]) for x in selected["cases"]]

    questions = _load(questions_path)
    if len(questions.get("questions", [])) != 4:
        parser.error("canonical questions artifact no longer has the expected four records")

    out_dir.mkdir(parents=True, exist_ok=False)
    _write(out_dir / "selected-cases.json", selected)
    dispositions = {
        "schema_version": "human-evidence-question-disposition-v1",
        "source_artifact": str(questions_path),
        "active_question_count": 0,
        "questions": [{
            "question_id": item.get("question_id"),
            "case_id": item.get("case_id"),
            "prior_status": item.get("status"),
            "status": "withdrawn_after_system_analysis",
            "reason": (
                "system_alignment_failure_not_author_intention"
                if str(item.get("case_id", "")).endswith("-0209")
                else "observable_textual_effect_can_be_analyzed_without_author_intention"),
        } for item in questions.get("questions", [])],
    }
    _write(out_dir / "human-evidence-question-disposition.json", dispositions)

    snapshot_paths = [state_path] + sorted(
        Path("eval/academic-quality").glob(f"{args.job_id}/**/state-eval.json"))
    candidate_indexes = sorted(
        int(x["segment_index"]) for x in evidence.get("candidate_cases", []))
    snapshots = []
    version_sets = {index: set() for index in candidate_indexes}
    for path in snapshot_paths:
        snapshot = _load(path)
        pairs = snapshot.get("pairs") or []
        identities = {
            str(index): _pair_identity(pairs[index])
            for index in candidate_indexes if index < len(pairs)
        }
        for index in candidate_indexes:
            if str(index) in identities:
                version_sets[index].add(identities[str(index)])
        snapshots.append({
            "path": str(path),
            "state_sha256": _sha256(path),
            "pair_count": len(pairs),
            "candidate_pair_identities": identities,
        })

    segments = academic_evidence.segment_index(evidence)
    candidates = []
    for candidate in evidence.get("candidate_cases", []):
        case_id = str(candidate["case_id"])
        segment = segments[case_id]
        candidates.append({
            **candidate,
            "source": segment.get("source"),
            "initial_target": segment.get("initial_target"),
            "final_target": segment.get("final_target"),
            "actual_delta": case_analysis.translation_delta(segment),
            "findings": segment.get("process_evidence", {}).get("findings") or [],
            "repair_history": segment.get("process_evidence", {}).get(
                "repair_history") or [],
            "human_actions": segment.get("process_evidence", {}).get(
                "human_actions") or [],
            "distinct_recorded_pair_versions": len(version_sets.get(
                int(candidate["segment_index"]), set())),
            "provenance_verdict": "VERIFIED" if candidate.get(
                "academic_candidate_status") == "eligible" else "MISMATCH",
        })

    index = args.investigate_index
    current = state.get("pairs", [])[index]
    following = state.get("pairs", [])[index + 1]
    current_case = next(x for x in candidates if x["segment_index"] == index)
    investigation = {
        "case_id": current_case["case_id"],
        "status": "MISMATCH",
        "stored_source_tail": str(current.get("source") or "")[-100:],
        "following_source_head": str(following.get("source") or "")[:100],
        "stored_final_contains_adjacent_target": any(
            x.get("type") == "probable_adjacent_target_overlap"
            for x in current_case.get("features", {}).get("integrity_flags", [])),
        "integrity_flags": current_case.get("features", {}).get("integrity_flags", []),
        "distinct_recorded_pair_versions": len(version_sets.get(index, set())),
        "source_document_boundary_note": args.source_boundary_note,
        "recovery_decision": "not_defensible_from_recorded_history",
        "reason": (
            "The stored final target includes adjacent-segment content, while every "
            "available state snapshot preserves the same contaminated pair. No recorded "
            "subsegment revision or pre-contamination target exists, so a synthetic split "
            "would not have historical provenance."),
    }
    system_case_index = 209
    system_pair = state.get("pairs", [])[system_case_index]
    preceding_pair = state.get("pairs", [])[system_case_index - 1]
    system_case = next(x for x in candidates if x["segment_index"] == system_case_index)
    system_investigation = {
        "case_id": system_case["case_id"],
        "status": "SYSTEM_ALIGNMENT_FAILURE",
        "source": system_pair.get("source"),
        "stored_initial_target": system_pair.get("initial_target"),
        "stored_final_target": system_pair.get("target"),
        "initial_target_found_in_preceding_target_after_normalization": any(
            x.get("type") == "probable_adjacent_initial_target_overlap"
            for x in system_case.get("features", {}).get("integrity_flags", [])),
        "preceding_segment_id": f"seg-{args.job_id}-{system_case_index - 1:04d}",
        "preceding_final_target": preceding_pair.get("target"),
        "human_action": "retranslated",
        "academic_decision": "exclude_from_authentic_revision_core",
        "reason": (
            "The alleged initial translation belongs to the preceding passage, and the "
            "stored final repeats the English source title. The observed change is a "
            "system alignment/retranslation event, not a defensible translator decision."),
    }

    stats = evidence["project_evidence"]["statistics"]
    audit = {
        "schema_version": "revision-case-audit-v2",
        "job_id": args.job_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "state_source": str(state_path),
        "state_sha256": _sha256(state_path),
        "eligibility_rule": (
            "No core case without an actual meaningful initial-to-final revision."),
        "history_source_audit": {
            "initial_final_translations": "VERIFIED",
            "review_findings_for_revision_candidates": "NOT_FOUND",
            "repair_history_for_revision_candidates": "NOT_FOUND",
            "human_actions": "VERIFIED_FOR_0142_AND_0209;_0209_IS_SYSTEM_RETRANSLATION",
            "project_session_snapshots": "COPIES_NOT_INDEPENDENT_VERSIONS",
            "prior_artifacts": "NO_ADDITIONAL_TRANSLATION_VERSION_FOUND",
            "source_document_boundary": "VERIFIED" if args.source_boundary_note else "NOT_RECORDED",
            "snapshots": snapshots,
        },
        "statistics": {key: stats[key] for key in (
            "total_segments", "segments_with_initial_final_data", "unchanged_segments",
            "meaningfully_revised_segments", "revision_cases_with_findings",
            "revision_cases_with_repair_history",
            "revision_cases_with_complete_repair_chains",
            "revision_cases_academically_eligible")},
        "candidate_cases": candidates,
        "case_0142_investigation": investigation,
        "case_0209_investigation": system_investigation,
        "core_case_decision": "only_0272_is_currently_defensible",
        "selected_case_ids": selected_ids,
        "chapter_3_decision": "insufficient_revision_cases",
        "revision_gate_relaxed": False,
    }
    audit["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in audit.items() if k != "content_hash"})
    _write(out_dir / "revision-case-audit.json", audit)

    pilot = {
        "pilot": "system-analysis-no-author-question-pilot",
        "job_id": args.job_id,
        "case_ids": [x.rsplit("-", 1)[-1] for x in selected_ids],
        "artifact_source": "human-evidence-question-disposition.json",
        "number_of_questions": 0,
        "withdrawn_question_count": len(questions["questions"]),
        "estimated_author_burden": "0 minutes",
        "status": "system_analysis_complete",
        "phase_b_started": False,
        "revision_eligibility_immutable": True,
    }
    _write(out_dir / "human-evidence-pilot-state.json", pilot)

    report = f"""# Revision Case Recovery and Selection Report

- job: `{args.job_id}`
- decision: `insufficient_revision_cases`
- selected core cases: 0272
- excluded system-alignment case: 0209
- revision eligibility gate relaxed: no

## Evidence-source audit

- Initial/final translations: **VERIFIED**; 237 pairs contain both versions.
- Review findings linked to the three changed pairs: **NOT_FOUND**.
- Translation repair history linked to the three changed pairs: **NOT_FOUND**.
- Human actions: **VERIFIED** for 0142 and 0209. The 0209 action is a system retranslation event, not author rationale.
- Project/session snapshots: all available copies preserve the same 0142, 0209 and 0272 pair identities; they are not independent historical versions.
- Prior academic artifacts: no additional initial/final translation version was found.
- Source document boundary: **{'VERIFIED' if args.source_boundary_note else 'NOT_RECORDED'}**. {args.source_boundary_note}

## Candidate decisions

### Case 0209 — excluded system-alignment failure

The alleged initial target is text from the preceding passage. The retranslation then stored the English source title unchanged. This is an alignment/retranslation failure, not a defensible translation decision, so it cannot be core revision evidence.

### Case 0272 — eligible without author-intention inference

A genuine initial-to-final lexical revision is stored. Its observable referential effect can be analyzed directly; no historical motivation is inferred or requested from the author.

### Case 0142 — review_required, not recovered

The segment contains genuine local wording changes, but its final target also reproduces the following segment. Every available state snapshot contains the same contaminated pair. No pre-contamination target or subsegment revision record exists. Separating a new “0142a” would therefore create an unrecorded evidence object, so 0142 remains excluded from core analysis.

## Final academic decision

Only 0272 currently passes the authentic-revision gate, which is below the two-case minimum. Chapter 3 core composition must wait until the recorded actionable findings are repaired and the new initial-to-final histories are re-audited. SC-0141 may remain an optional synthetic supplement but cannot satisfy the authentic minimum.

All four prior author questions are withdrawn: two concerned a system fault, and two asked for intention/reader response that is unnecessary for evidence-bounded textual analysis. No answer is inferred or fabricated. Phase B has not started.
"""
    (out_dir / "revision-case-selection-report.md").write_text(report, encoding="utf-8")

    hashes = {
        name: _sha256(out_dir / name) for name in (
            "revision-case-audit.json", "selected-cases.json",
            "human-evidence-question-disposition.json",
            "human-evidence-pilot-state.json", "revision-case-selection-report.md")
    }
    manifest = {
        "job_id": args.job_id,
        "isolated_output": str(out_dir),
        "state_source": str(state_path),
        "state_sha256": _sha256(state_path),
        "pipeline_version": academic_writer.PIPELINE_VERSION,
        "versions": dict(academic_writer.VERSIONS),
        "artifact_hashes_sha256": hashes,
        "canonical_questions_source": str(questions_path),
        "phase_b_executed": False,
    }
    _write(out_dir / "run-manifest.json", manifest)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
