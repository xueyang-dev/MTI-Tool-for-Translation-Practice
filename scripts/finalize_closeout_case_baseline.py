"""Finalize the real thesis case baseline after translation-review closeout."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import academic_evidence, case_analysis


CORE_INDEXES = (139, 233, 272)
SYSTEM_REPAIR_INDEXES = (1, 14, 93, 101, 142, 144, 145, 201, 209, 236, 239)
RATIONALES = {
    139: "文学隐喻与父子关系：修订保留“伸手”意象，同时改善汉语叙事节奏。",
    233: "文化专名与叙事指代：修正影片名误译，并恢复被泛化的明确主语。",
    272: "元语言回指与语义范围：避免把英文计词事实错误移植为中文计字事实。",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    state_path = Path("outputs") / args.job_id / "state.json"
    closeout_path = out_dir / "thesis-closeout-state.json"
    if not state_path.is_file() or not closeout_path.is_file():
        parser.error("real state or closeout state is missing")

    state = _load(state_path)
    if state.get("review_stats", {}).get("actionable") != 0 or any(
            not pair.get("reviewed") for pair in state.get("pairs") or []):
        parser.error("translation review is not closed")
    evidence = academic_evidence.build_academic_evidence(
        state, args.job_id, max_candidates=len(state.get("pairs") or []))
    segments = {x["segment_index"]: x
                for x in evidence["project_evidence"]["segments"]}
    candidates = {x["segment_index"]: x for x in evidence["candidate_cases"]}

    selected = []
    for index in CORE_INDEXES:
        segment = segments[index]
        candidate = candidates.get(index)
        if not candidate or candidate.get("academic_candidate_status") != "eligible":
            parser.error(f"core case {index:04d} is not eligible")
        if not academic_evidence.is_eligible_revision_case(segment):
            parser.error(f"core case {index:04d} fails the shared revision gate")
        selected.append({
            "case_id": segment["segment_id"],
            "segment_index": index,
            "case_type": "authentic_revision",
            "role": "core_authentic_revision",
            "eligibility": "eligible",
            "selection_rationale": RATIONALES[index],
            "source": segment["source"],
            "initial_target": segment["initial_target"],
            "final_target": segment["final_target"],
            "translation_delta": case_analysis.translation_delta(segment),
            "findings": segment["process_evidence"]["findings"],
            "repair_history": segment["process_evidence"]["repair_history"],
            "human_actions": segment["process_evidence"]["human_actions"],
            "system_actions": segment["process_evidence"]["system_actions"],
        })

    excluded = []
    for index in SYSTEM_REPAIR_INDEXES:
        segment = segments[index]
        if not segment.get("integrity_flags"):
            parser.error(f"system repair {index:04d} lost its integrity flag")
        if academic_evidence.is_eligible_revision_case(segment):
            parser.error(f"system repair {index:04d} was incorrectly promoted")
        excluded.append({
            "case_id": segment["segment_id"],
            "segment_index": index,
            "decision": "excluded_system_repair",
            "integrity_flags": segment["integrity_flags"],
        })

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    audit = {
        "schema_version": "revision-case-audit-v3",
        "job_id": args.job_id,
        "generated_at": generated_at,
        "state_source": str(state_path),
        "state_sha256": _sha256(state_path),
        "eligibility_rule": (
            "核心案例必须存在真实、有意义的初译至终译变化，且不得带有系统对齐、"
            "跨段污染或模型序列化完整性标记。"),
        "shared_gate": "transpraxis.academic_evidence.is_eligible_revision_case",
        "statistics": evidence["project_evidence"]["statistics"],
        "eligible_revision_case_count": sum(
            item.get("academic_candidate_status") == "eligible"
            for item in evidence["candidate_cases"]),
        "selected_core_cases": selected,
        "excluded_system_repairs": excluded,
        "revision_gate_relaxed": False,
        "human_author_evidence_used": False,
        "human_author_evidence_note": (
            "作者问题已撤回；本轮只使用可观察文本差异、历史finding和独立记录的"
            "system_actions，不生成或推断译者心理意图。"),
        "decision": "three_defensible_core_revision_cases",
    }
    audit["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in audit.items() if k != "content_hash"})
    _write(out_dir / "revision-case-audit-final.json", audit)

    selection = {
        "schema_version": "case-selection-v6-closeout",
        "job_id": args.job_id,
        "selection_status": "sufficient_revision_cases",
        "authentic_selection_status": "sufficient_revision_cases",
        "preferred_core_case_count": 3,
        "minimum_core_case_count": 2,
        "selected_case_count": 3,
        "authentic_revision_cases": 3,
        "synthetic_contrast_cases": 0,
        "scarcity_disclosure_required": False,
        "cases": [{key: value for key, value in item.items()
                   if key not in {"source", "initial_target", "final_target",
                                  "translation_delta", "findings", "repair_history",
                                  "human_actions", "system_actions"}}
                  for item in selected],
        "optional_supplement": {
            "case_id": "SC-0141",
            "case_type": "synthetic_contrast",
            "included_by_default": False,
            "counts_toward_authentic_core": False,
            "required_disclosure": (
                "分析阶段生成的受控合成对比，不代表作者历史初译，也不支持错误"
                "发生频率结论。"),
        },
    }
    selection["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in selection.items() if k != "content_hash"})
    _write(out_dir / "selected-cases-final.json", selection)
    _write(out_dir / "academic-evidence-final.json", evidence)

    report = """# 正式论文案例基线（翻译审校后）

## 最终决定

正式核心案例为0139、0233、0272，三者均通过共享的真实修订资格门禁。SC-0141仅保留为可选合成对比，不计入真实核心案例。

## 核心案例

1. **0139——文学隐喻与叙事关系**：初译存在汉语句法生硬问题；终译在改善表达的同时保留“伸手”意象，可讨论文学形象与人物关系的双重约束。
2. **0233——文化专名与叙事指代**：初译把影片名误作《监狱摇滚》，并把明确主语泛化为“有人”；终译同时修正文化信息和回指关系。
3. **0272——元语言回指与语义范围**：初译把源文的“五个词”错误转写为中文“五个字”；终译改为“这句话”，避免跨语言计量单位失配。

## 永久排除项

0001、0014、0093、0101、0142、0144/0145、0201、0209、0236、0239属于作者名误译、术语一致性遗漏、跨段污染、序列化输出或相邻段复制等系统修复。它们虽已修正终译，但持久完整性标记不允许其转化为真实修订案例。

## Human Evidence边界

作者问题继续保持撤回。本基线没有使用作者答案，也没有从原译文对推断译者意图。0139和0233的修复依据来自历史finding与独立记录的系统审校动作；0272只分析可观察的初译—终译差异。
"""
    (out_dir / "case-baseline-final-report.md").write_text(
        report, encoding="utf-8")

    closeout = _load(closeout_path)
    closeout["status"] = "phase_b_ready"
    closeout["formal_case_baseline"] = {
        "status": "sufficient_revision_cases",
        "core_authentic_revision_cases": [{
            "case_id": item["case_id"],
            "role": item["role"],
            "eligibility": item["eligibility"],
        } for item in selected],
        "optional_supplement": selection["optional_supplement"],
        "excluded_system_repairs": [{
            "case_id": item["case_id"], "decision": item["decision"]}
            for item in excluded],
        "usage_rules": [
            "只把0139、0233、0272作为正式核心真实修订案例。",
            "SC-0141仅在需要方法对照时使用，并明确标注为合成案例。",
            "Human Author Evidence可以丰富分析，但不能改变案例资格。",
            "不得把system_actions表述为作者本人意图或人工修订。",
        ],
        "canonical_sources": {
            "revision_audit": "revision-case-audit-final.json",
            "revision_selection": "selected-cases-final.json",
            "academic_evidence": "academic-evidence-final.json",
            "translation_review": "translation-review-audit.json",
        },
    }
    closeout["human_evidence"] = {
        "status": "not_required_system_analysis_substituted",
        "question_count": 0,
        "withdrawn_question_count": 4,
        "answers_recorded": 0,
        "phase_b_started": False,
        "author_intention_inference_allowed": False,
    }
    for stage in closeout.get("stages") or []:
        if stage.get("stage") == 2:
            stage["status"] = "completed"
        if stage.get("stage") == 5:
            stage["status"] = "completed"
    closeout["translation_review"] = {
        "status": "completed",
        "original_actionable_findings_resolved": 32,
        "unreviewed_segments_after": 0,
        "open_blocking_after": 0,
        "open_actionable_after": 0,
        "historical_initial_targets_modified": False,
        "system_actions_separated_from_human_actions": True,
        "artifacts": {
            "audit": "translation-review-audit.json",
            "report": "translation-review-report.md",
            "pre_review_backup": "translation-state-before-review.json",
            "post_review_snapshot": "translation-state-after-review.json",
        },
    }
    _write(closeout_path, closeout)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
