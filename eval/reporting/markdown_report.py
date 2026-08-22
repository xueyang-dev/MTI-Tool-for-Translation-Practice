"""Markdown 摘要报告（人类可读，不含源码正文）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def write_markdown_report(report: Dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "evaluation-report.md"
    meta = report["meta"]
    lines = [
        "# TransPraxis / 译践 评测报告（Evaluation Report）",
        "",
        f"- 语料：{meta.get('corpus', {}).get('job_id', '?')} "
        f"子集 {meta.get('corpus', {}).get('subset', '?')}",
        f"- 术语表：{meta.get('glossary', '?')}",
        f"- TM 种子：{meta.get('tm_seed', '无')}",
        f"- 代码：baseline={meta.get('baseline_ref', '?')} "
        f"current={meta.get('current_ref', '?')}",
        f"- 模型：{meta.get('run', {}).get('provider', '?')} / "
        f"{meta.get('run', {}).get('model', '?')}",
        f"- 时间：{meta.get('created_at', '?')}",
        "",
        "## 分臂结果",
        "",
        "| 指标 | A | B | C | D |",
        "|---|---|---|---|---|",
    ]
    runs = report["runs"]
    arms = sorted(runs.keys())
    blocks = ("terminology", "qa", "workflow")
    for block in blocks:
        keys: Dict[str, str] = {}
        for arm in arms:
            for k, v in (runs[arm].get(block) or {}).items():
                if k != "per_term":
                    keys[k] = ""
        for k in keys:
            cells = []
            for arm in arms:
                v = (runs[arm].get(block) or {}).get(k)
                cells.append("-" if v is None else str(v))
            lines.append(f"| {block}.{k} | " + " | ".join(cells) + " |")
    lines += ["", "## 臂间增量（Governance × Reviewed TM）", ""]
    for name, delta in (report.get("deltas") or {}).items():
        lines.append(f"**{name}**")
        for block, values in delta.items():
            if values:
                lines.append(f"- {block}: " +
                             "，".join(f"{k}={v}" for k, v in values.items()))
    lines += ["", "## 人工盲评", "",
              f"- 状态：{report.get('human_review', {}).get('status', 'pending')}",
              f"- 抽样包：{report.get('human_review', {}).get('packet', '未生成')}",
              "",
              "> 本报告只做多维诊断，不提供单一质量分。",
    ]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p
