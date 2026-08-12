"""Regression checks for the real v6 four-chapter Phase B artifact."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval/academic-quality/ec100d8686d3891e/thesis-closeout-v6"


def main() -> None:
    validation = json.loads((OUT / "academic-validation-v6.json").read_text())
    quality = json.loads((OUT / "academic-quality-v6.json").read_text())
    closeout = json.loads((OUT / "thesis-closeout-state.json").read_text())
    report = (OUT / "thesis-body-v6.md").read_text()
    assert validation["status"] in {"pass", "pass_with_warnings"}
    assert validation["summary"]["errors"] == 0
    assert quality["status"] == "pass"
    assert report.count("\n## ") == 3
    assert all(heading in report for heading in (
        "### 1.1 研究背景及意义", "### 1.2 研究问题", "### 1.3 报告结构",
        "### 2.1 项目简介", "#### 2.2.1 译前准备", "#### 2.2.2 翻译过程",
        "#### 2.2.3 译后管理", "### 3.1 源语文本的类型与特征",
        "### 3.2 翻译难点", "### 3.3 翻译策略与解决方案",
        "### 4.1 研究问题回应", "### 4.2 实践经验与可迁移方法",
        "### 4.3 局限与改进方向"))
    for case in ("0139", "0233", "0272"):
        assert f"seg-ec100d8686d3891e-{case}" in report
    assert "SC-0141" not in report
    assert "<!--human-ev:" not in report
    assert closeout["phase_b"]["semantic_review_status"] == \
        "pending_supervisor_review"
    print("thesis Phase B: PASS")


if __name__ == "__main__":
    main()
