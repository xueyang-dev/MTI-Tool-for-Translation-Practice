"""Regression checks for the real closeout case baseline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval/academic-quality/ec100d8686d3891e/thesis-closeout-v6"


def main() -> None:
    audit = json.loads((OUT / "revision-case-audit-final.json").read_text())
    selection = json.loads((OUT / "selected-cases-final.json").read_text())
    evidence = json.loads((OUT / "academic-evidence-final.json").read_text())
    closeout = json.loads((OUT / "thesis-closeout-state.json").read_text())
    selected = [item["segment_index"] for item in audit["selected_core_cases"]]
    assert selected == [139, 233, 272]
    assert selection["authentic_revision_cases"] == 3
    assert selection["synthetic_contrast_cases"] == 0
    assert selection["optional_supplement"]["case_id"] == "SC-0141"
    segments = {x["segment_index"]: x
                for x in evidence["project_evidence"]["segments"]}
    assert all(academic_evidence.is_eligible_revision_case(segments[i])
               for i in selected)
    for index in (1, 14, 93, 101, 142, 144, 145, 201, 209, 236, 239):
        assert segments[index]["integrity_flags"]
        assert not academic_evidence.is_eligible_revision_case(segments[index])
    assert all(not segments[i]["process_evidence"]["human_actions"]
               for i in (139, 233, 272))
    assert segments[139]["process_evidence"]["system_actions"]
    assert segments[233]["process_evidence"]["system_actions"]
    assert closeout["formal_case_baseline"]["status"] == \
        "sufficient_revision_cases"
    assert closeout["human_evidence"]["answers_recorded"] == 0
    # The author-question path was withdrawn, but the later explicitly
    # requested system-analysis Phase B has completed without human evidence.
    assert closeout["human_evidence"]["phase_b_started"] is True
    assert closeout["phase_b"]["human_author_evidence_entries_used"] == 0
    assert closeout["phase_b"][
        "system_actions_presented_as_author_intention"] is False
    print("closeout case baseline: PASS")


if __name__ == "__main__":
    main()
