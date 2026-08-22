"""Historical / ecological evidence（历史生态证据，只读）。

与受控 A/B/C/D 分开，不进入同一 leaderboard。回答历史任务迁移和流程回归问题；
输入任务必须由操作者在本机提供。

本模块只读 outputs/，不修改任何历史任务。

用法：
    python eval/history.py --output-dir eval/results/<ts>/history
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from transpraxis import state_migration

# 已知流程 failure modes -> 回归测试覆盖
KNOWN_FAILURE_MODES = [
    ("LLM 分段清洗（非确定性）", "tests/smoke_test.py::test_pdf_extraction"),
    ("批次格式解析/降级", "tests/smoke_test.py::test_parse_translation_array"),
    ("截断译文被整段替换", "tests/smoke_test.py::test_review_truncated_suggestion_rollback"),
    ("TM 污染（装饰行/非法条目）", "tests/smoke_test.py::test_tm_sanitize_on_load"),
    ("标注滥标常用词", "tests/smoke_test.py::test_annotation_filters"),
    ("断点粒度/续传", "tests/smoke_test.py::test_resume_translation"),
    ("术语表变更后旧译文失效", "tests/red_team_acceptance_test.py::test_p0_glossary_staleness"),
    ("accept-risk 进入 TMX", "tests/red_team_acceptance_test.py::test_accept_risk_not_tmx_trusted"),
    ("scope 串扰", "tests/red_team_acceptance_test.py::test_scope_cross_contamination_qa_and_conflicts"),
]


def _analyze_job(job_id: str, job_dir: Path) -> Dict[str, Any]:
    """读取单个历史任务（只读）。"""
    sp = job_dir / "state.json"
    if not sp.is_file():
        return {"job_id": job_id, "error": "no state.json"}
    try:
        raw = json.loads(sp.read_text(encoding="utf-8"))
    except Exception as e:
        return {"job_id": job_id, "error": f"corrupt state.json: {e}"}
    state = state_migration.migrate_state(raw)
    pairs = state.get("pairs") or []
    findings = state.get("findings") or []
    incomplete = [i for i, p in enumerate(pairs)
                  if core.is_incomplete_translation(p.get("source", ""),
                                                    p.get("target", ""))]
    return {
        "job_id": job_id,
        "filename": state.get("filename", "?"),
        "segments": len(state.get("paras") or []),
        "pairs": len(pairs),
        "p1_done": state.get("p1_done"),
        "p2_done": state.get("p2_done"),
        "p3_done": state.get("p3_done"),
        "delivery_status": state.get("delivery_status"),
        "stage": state.get("stage"),
        "blocking": sum(1 for f in findings if f.get("severity") == "blocking"),
        "actionable": sum(1 for f in findings if f.get("severity") == "actionable"),
        "informational": sum(1 for f in findings if f.get("severity") == "informational"),
        "incomplete_suspects": len(incomplete),
        "reviewed_segments": sum(1 for p in pairs if p.get("reviewed")),
        "tm_reused": state.get("tm_used_count", 0),
        "migrated_without_error": True,
        "glossary_frozen": state.get("glossary_frozen") is not None,
        "has_source_bin": (job_dir / "source.bin").is_file(),
        "has_new_fields": all(k in state for k in (
            "delivery_status", "glossary", "glossary_frozen", "human_actions",
            "document_profile")),
    }


def _analyze_tm(tm_path: Path) -> Dict[str, Any]:
    if not tm_path.is_file():
        return {"error": "no translation_memory.json", "entries": 0}
    tm = core.load_tm()
    raw = json.loads(tm_path.read_text(encoding="utf-8"))
    total_raw = len(raw) if isinstance(raw, dict) else 0
    incomplete = []
    for src, v in tm.items():
        tgt = (v or {}).get("target", "")
        if core.is_incomplete_translation(src, tgt):
            incomplete.append(src)
    return {
        "raw_entries": total_raw,
        "trusted_after_sanitize": len(tm),
        "incomplete_in_trusted_tm": len(incomplete),
        "tm_usable": len(incomplete) == 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="eval/results/history")
    ap.add_argument("--outputs-dir", default="outputs")
    ap.add_argument("--job-ids", default=None,
                    help="逗号分隔；缺省分析 outputs/ 下全部任务")
    args = ap.parse_args()

    outputs_dir = Path(args.outputs_dir)
    tm_path = outputs_dir / "translation_memory.json"
    job_ids = [x.strip() for x in (args.job_ids or "").split(",") if x.strip()]
    jobs: List[Dict[str, Any]] = []
    if job_ids:
        for jid in job_ids:
            d = outputs_dir / jid
            if d.is_dir():
                jobs.append(_analyze_job(jid, d))
    else:
        for d in sorted(outputs_dir.iterdir()):
            if d.is_dir() and (d / "state.json").is_file():
                jobs.append(_analyze_job(d.name, d))

    tm_info = _analyze_tm(tm_path)
    report = {
        "meta": {
            "track": "historical / ecological evidence（与受控 A/B/C/D 分开）",
            "outputs_dir": str(outputs_dir),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "只读分析；不修改历史任务；结果与抽样正文均 local-only",
        },
        "jobs": jobs,
        "tm": tm_info,
        "known_failure_mode_coverage": [
            {"failure_mode": fm, "regression_test": test}
            for fm, test in KNOWN_FAILURE_MODES
        ],
    }
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "history_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# 历史生态证据（Historical / Ecological Evidence）", "",
          f"- outputs：{outputs_dir} · 时间：{report['meta']['created_at']}", "",
          "## TM 状态", ""]
    for k, v in tm_info.items():
        md.append(f"- {k}: {v}")
    md += ["", "## 历史任务", ""]
    for j in jobs:
        md.append(f"- `{j.get('job_id')}` {j.get('filename', '?')}："
                  f"{j.get('segments')} 段 / {j.get('pairs')} 对 · "
                  f"blocking {j.get('blocking')} · actionable {j.get('actionable')} · "
                  f"incomplete_suspects {j.get('incomplete_suspects')} · "
                  f"stage {j.get('stage')}")
    md += ["", "## 已知 failure mode 覆盖", ""]
    for fm, test in KNOWN_FAILURE_MODES:
        md.append(f"- {fm} → `{test}`")
    (out / "history_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"history report -> {out / 'history_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
