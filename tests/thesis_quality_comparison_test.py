"""Regression checks for v6 academic-quality comparison."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval/academic-quality/ec100d8686d3891e/thesis-closeout-v6"


def main() -> None:
    value = json.loads((OUT / "academic-quality-comparison.json").read_text())
    assert len(value["historical_runs"]) == 3
    assert value["new_run"]["validation_status"] == "pass"
    assert value["new_run"]["quality_finding_count"] == 0
    assert value["new_run"]["cases_used_in_report"] == 3
    assert value["new_run"]["high_value_unused_cases"] == 0
    assert value["delta_from_best_historical"]["quality_findings"] < 0
    review = (OUT / "supervisor-review-brief-v6.md").read_text()
    assert "pending_supervisor_review" in review
    assert "系统不得代签" in review
    print("thesis quality comparison: PASS")


if __name__ == "__main__":
    main()
