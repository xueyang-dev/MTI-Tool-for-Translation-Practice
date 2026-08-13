"""Regression check for the real ec100 closeout literature packet."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_writer
from scripts.prepare_closeout_literature import DEFAULT_OUT, prepare


def test_closeout_literature_packet() -> None:
    manifest = prepare(DEFAULT_OUT)
    sources = academic_writer._read_artifact(DEFAULT_OUT / "literature-sources.json")
    evidence = academic_writer._read_artifact(DEFAULT_OUT / "literature-evidence.jsonl")
    claims = academic_writer._read_artifact(DEFAULT_OUT / "literature-claims.jsonl")
    verification = academic_writer._read_artifact(
        DEFAULT_OUT / "literature-source-verification.json")
    state = json.loads((DEFAULT_OUT / "thesis-closeout-state.json").read_text(
        encoding="utf-8"))

    assert manifest["source_count"] == 6 and manifest["claim_count"] == 9
    assert manifest["historical_translation_state_modified"] is False
    assert manifest["phase_b_started"] is False
    assert len(sources["sources"]) == 6
    assert all(item["allowed_citation_status"] == "allowed" for item in sources["sources"])
    assert all(item.get("source_file_hash") for item in sources["sources"])
    assert verification["status"] == "verified_with_declared_boundaries"
    assert verification["sources_verified"] == 6

    evidence_by_id = {item["evidence_id"]: item for item in evidence["items"]}
    source_ids = {item["source_id"] for item in sources["sources"]}
    assert len(claims["items"]) == 9
    for claim in claims["items"]:
        assert claim["source_id"] in source_ids
        assert claim["boundary"]
        assert claim["evidence_grounded_status"] == "grounded"
        assert claim["supporting_evidence_ids"]
        for evidence_id in claim["supporting_evidence_ids"]:
            item = evidence_by_id[evidence_id]
            assert item["source_id"] == claim["source_id"]
            assert item["provenance"] == "source_text_verified"
            assert item["verification_status"] == "source_text_verified"

    assert state["literature_evidence"]["status"] == "grounded_phase2_ready"
    assert state["literature_evidence"]["phase_b_started"] is False
    assert next(x for x in state["stages"] if x["stage"] == 4)["status"] == "completed"


if __name__ == "__main__":
    test_closeout_literature_packet()
    print("closeout literature evidence: PASS")
