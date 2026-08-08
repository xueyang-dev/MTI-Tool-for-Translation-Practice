"""CSV 报告：逐术语采纳表 + 逐臂 findings 摘要。"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


def write_terms_csv(runs: Dict[str, Dict[str, Any]], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "terms_adoption.csv"
    arms = sorted(runs.keys())
    # 收集所有术语（以第一个有 per_term 的臂为准，其余臂按 term 补齐）
    terms: Dict[str, Dict[str, Any]] = {}
    for arm in arms:
        for row in (runs[arm].get("terminology") or {}).get("per_term") or []:
            key = row.get("term")
            if key and key not in terms:
                terms[key] = {"term": key,
                              "preferred": row.get("preferred", ""),
                              "behavior": row.get("behavior", "translate")}
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = ["term", "preferred", "behavior"] + [
            f"{arm}_occurrences" for arm in arms] + [
            f"{arm}_adopted" for arm in arms] + [
            f"{arm}_rate" for arm in arms]
        writer.writerow(header)
        for key, info in terms.items():
            row = [info["term"], info.get("preferred", ""), info.get("behavior", "")]
            for arm in arms:
                per = {r["term"]: r for r in
                       (runs[arm].get("terminology") or {}).get("per_term") or []}
                r = per.get(key) or {}
                row.append(r.get("occurrences", 0))
            for arm in arms:
                per = {r["term"]: r for r in
                       (runs[arm].get("terminology") or {}).get("per_term") or []}
                r = per.get(key) or {}
                row.append(r.get("adopted", 0))
            for arm in arms:
                per = {r["term"]: r for r in
                       (runs[arm].get("terminology") or {}).get("per_term") or []}
                r = per.get(key) or {}
                row.append(r.get("rate", ""))
            writer.writerow(row)
    return p


def write_findings_csv(states: Dict[str, Dict[str, Any]], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "findings_summary.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["arm", "severity", "type", "count"])
        for arm in sorted(states.keys()):
            counts: Dict[str, int] = {}
            for fd in states[arm].get("findings") or []:
                key = (fd.get("severity"), fd.get("type"))
                counts[key] = counts.get(key, 0) + 1
            for (sev, typ), n in sorted(counts.items()):
                writer.writerow([arm, sev, typ, n])
    return p
