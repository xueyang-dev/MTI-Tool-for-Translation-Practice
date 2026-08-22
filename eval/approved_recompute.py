"""用人工审核后的 approved glossary 重算 300 段四臂指标（report-only，零 API）。

输出到本地评测目录的 JSON / Markdown 报告，
明确区分 original_auto_glossary_metrics 与 human_approved_glossary_metrics；
不覆盖第一次实验结果（eval/results/round1/ 只读）。

人工审核尚未完成时：human_approved_glossary_metrics 为 null，
报告 status = "pending_human_glossary_decisions"，不伪造数字。

用法：
    python eval/approved_recompute.py \
        --results-dir eval/results/round1 \
        --approved eval/approved_glossary.json \
        --out eval/results/recomputed.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval.metrics import aggregate, qa_density, terminology, workflow  # noqa: E402
from eval.run_ab import load_existing_runs  # noqa: E402


def _metrics_for_states(states: Dict[str, Dict[str, Any]],
                        glossary_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for arm, state in states.items():
        out[arm] = {
            "terminology": terminology.compute_terminology_metrics(
                state, glossary_entries),
            "qa": qa_density.compute_qa_density(state),
            "workflow": workflow.compute_workflow_metrics(state),
        }
    return out


def _load_approved(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries") or []
    return list(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="eval/results/round1")
    ap.add_argument("--approved", default="eval/approved_glossary.json")
    ap.add_argument("--out",
                    default="eval/results/recomputed.json")
    args = ap.parse_args(argv)

    results = Path(args.results_dir)
    states, _metas = load_existing_runs(results)
    if not states:
        print(f"results-dir 没有可用运行结果：{results}")
        return 2

    original_report_path = results / "evaluation-report.json"
    if not original_report_path.is_file():
        print(f"缺少原始报告：{original_report_path}")
        return 2
    original = json.loads(original_report_path.read_text(encoding="utf-8"))
    original_metrics = original.get("runs") or {}

    approved_path = Path(args.approved)
    approved_entries: List[Dict[str, Any]] = []
    status = "pending_human_glossary_decisions"
    if approved_path.is_file():
        approved_entries = _load_approved(approved_path)
        status = "human-approved" if approved_entries else \
            "pending_human_glossary_decisions"
    if status != "human-approved":
        approved_metrics = None
    else:
        approved_metrics = _metrics_for_states(states, approved_entries)

    report = {
        "meta": {
            "results_dir": str(results),
            "approved_glossary": str(approved_path),
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "report-only：未调用任何 provider；原始结果未被修改",
        },
        "original_auto_glossary_metrics": original_metrics,
        "human_approved_glossary_metrics": approved_metrics,
    }
    if approved_metrics and original_metrics:
        comparison: Dict[str, Any] = {}
        for arm in sorted(set(original_metrics) & set(approved_metrics)):
            comparison[arm] = aggregate.compute_deltas(
                {"auto": original_metrics[arm], "human": approved_metrics[arm]},
                ["auto_to_human"]).get("auto_to_human")
        report["auto_to_human_deltas"] = comparison

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    md_path = out.with_suffix(".md")
    lines = ["# 300 段结果重算（approved glossary）", "",
             f"- 状态：{status}",
             f"- 原始结果：{results / 'evaluation-report.json'}（未修改）",
             f"- approved glossary：{approved_path}", ""]
    if approved_metrics:
        lines += ["## human_approved_glossary_metrics", ""]
        for arm in sorted(approved_metrics):
            t = approved_metrics[arm]["terminology"]
            lines.append(f"- {arm}: adoption={t.get('locked_term_adoption_rate')} "
                         f"forbidden={t.get('forbidden_term_violations')} "
                         f"preserve={t.get('preserve_failures')} "
                         f"conflicts={t.get('scope_conflicts')}")
    else:
        lines += [
            "## human_approved_glossary_metrics",
            "",
            "**pending human glossary decisions**：term_audit.csv 的人工 decision "
            "尚未填写，未生成任何人工术语表指标。",
        ]
    lines += ["", "## original_auto_glossary_metrics", ""]
    for arm in sorted(original_metrics):
        t = original_metrics[arm]["terminology"]
        lines.append(f"- {arm}: adoption={t.get('locked_term_adoption_rate')} "
                     f"forbidden={t.get('forbidden_term_violations')} "
                     f"preserve={t.get('preserve_failures')} "
                     f"conflicts={t.get('scope_conflicts')}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"recomputed report -> {out}（status={status}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
