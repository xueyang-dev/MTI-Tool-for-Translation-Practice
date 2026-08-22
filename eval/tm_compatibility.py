"""TM 兼容性审计（只读分析，绝不修改 TM）。

对每条 reviewed TM 分类：
- unaffected        ：TM source 不涉及 approved terminology
- compatible        ：涉及术语，target 符合 approved preferred / allowed variant
- incompatible      ：涉及 locked 术语，但 target 使用 forbidden / 旧译法 /
                      明显不符合当前 policy（preferred mismatch）
- ambiguous         ：无法仅靠确定性规则判断（如原文原样保留、variant_allowed
                      开放集合下未见认译法）
- scope_sensitive   ：结果依赖 section/domain/scope，而 TM 缺少上下文

原则：不把 string mismatch 简单等同于错误；无法确定时归 ambiguous。

用法：
    python eval/tm_compatibility.py --tm outputs/translation_memory.json \
        --glossary eval/approved_glossary.json \
        --out-dir eval/results/round1/tm_compat \
        [--label "human-approved glossary"]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis.terminology import term_matches  # noqa: E402

CLASSIFICATIONS = ("unaffected", "compatible", "incompatible", "ambiguous",
                   "scope_sensitive")


def _matches(term: str, text: str, case_sensitive: bool = False) -> bool:
    if case_sensitive:
        if re.search(r"[\u4e00-\u9fff]", term or ""):
            return bool(term) and term in (text or "")
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(term or "")
                         + r"(?![A-Za-z0-9_])")
        return bool(pat.search(text or ""))
    return term_matches(term or "", text or "")


def _allowed_targets(e: Dict[str, Any]) -> List[str]:
    out = [str(e.get("approved_target") or e.get("preferred")
                 or e.get("target") or "").strip()]
    out += [str(v).strip() for v in (e.get("variants") or []) if str(v).strip()]
    return [v for v in out if v]


def classify_tm_entry(tm_source: str, tm_target: str,
                      glossary: List[Dict[str, Any]]) -> Dict[str, Any]:
    """对单条 TM 分类。返回 {classification, matched_entries, reasons}。"""
    matched = [
        e for e in glossary
        if _matches(str(e.get("source") or ""), tm_source,
                    bool(e.get("case_sensitive")))
    ]
    if not matched:
        return {"classification": "unaffected", "matched_entries": [],
                "reasons": []}

    per_entry: List[str] = []
    reasons: List[str] = []
    for e in matched:
        scope = str(e.get("scope") or "").strip()
        if scope and scope != "global":
            per_entry.append("scope_sensitive")
            reasons.append(f"{e.get('source')}: scope={scope}，TM 缺少上下文")
            continue
        decision = str(e.get("decision") or "approved").strip().lower()
        if decision == "scope_sensitive":
            per_entry.append("scope_sensitive")
            reasons.append(f"{e.get('source')}: 人工判定为 scope_sensitive")
            continue
        allowed = _allowed_targets(e)
        forbidden = [str(f) for f in (e.get("forbidden") or []) if str(f)]
        contains_allowed = any(
            a and _matches(a, tm_target, bool(e.get("case_sensitive")))
            for a in allowed)
        contains_forbidden = any(f and f in (tm_target or "") for f in forbidden)
        if contains_forbidden:
            per_entry.append("incompatible")
            reasons.append(
                f"{e.get('source')}: 使用禁止译名「{next(f for f in forbidden if f in tm_target)}」")
        elif contains_allowed:
            per_entry.append("compatible")
            reasons.append(f"{e.get('source')}: 命中认可译法")
        elif _matches(str(e.get("source") or ""), tm_target,
                      bool(e.get("case_sensitive"))):
            per_entry.append("ambiguous")
            reasons.append(f"{e.get('source')}: 原文保留，无法确定政策意图")
        elif decision == "variant_allowed":
            per_entry.append("ambiguous")
            reasons.append(
                f"{e.get('source')}: variant_allowed 且未见认可译法/禁止译名，"
                "无法确定性判定")
        else:
            per_entry.append("incompatible")
            expected = " / ".join(allowed) or "（无）"
            reasons.append(
                f"{e.get('source')}: 未使用首选/认可译法（期望 {expected}）")

    # 聚合：incompatible > scope_sensitive > ambiguous > compatible
    if "incompatible" in per_entry:
        classification = "incompatible"
    elif "scope_sensitive" in per_entry:
        classification = "scope_sensitive"
    elif "ambiguous" in per_entry:
        classification = "ambiguous"
    else:
        classification = "compatible"
    return {"classification": classification,
            "matched_entries": matched, "reasons": reasons}


def load_glossary(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries") or []
    return list(data)


def load_tm(path: Path) -> Dict[str, Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("TM 文件必须是 {source: {target, reviewed}} 结构")
    return {k: v for k, v in raw.items()
            if isinstance(v, dict) and v.get("reviewed")}


def run_audit(tm: Dict[str, Dict[str, Any]],
              glossary: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]],
                                                       Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for src, v in tm.items():
        tgt = str(v.get("target") or "")
        res = classify_tm_entry(src, tgt, glossary)
        matched_sources = " | ".join(
            str(e.get("source")) for e in res["matched_entries"])
        expected = ""
        if res["matched_entries"]:
            per_entry = [" / ".join(_allowed_targets(e))
                         for e in res["matched_entries"]]
            expected = " || ".join(x for x in per_entry if x)
        rows.append({
            "tm_source": src,
            "tm_target": tgt,
            "classification": res["classification"],
            "matched_glossary_source": matched_sources,
            "expected_preferred_allowed": expected,
            "reason": "；".join(res["reasons"]),
            "scope": " | ".join(
                str(e.get("scope") or "") for e in res["matched_entries"]),
        })
    counts = Counter(r["classification"] for r in rows)
    affected = sum(counts[k] for k in ("compatible", "incompatible",
                                       "ambiguous", "scope_sensitive"))
    top_conflicts: List[Dict[str, Any]] = []
    term_counter: Counter = Counter()
    for r in rows:
        if r["classification"] == "incompatible":
            for term in r["matched_glossary_source"].split(" | "):
                if term:
                    term_counter[term] += 1
    for term, n in term_counter.most_common(20):
        total = sum(1 for r in rows if term in r["matched_glossary_source"])
        top_conflicts.append({"term": term, "incompatible_entries": n,
                              "tm_entries_mentioning_term": total})
    stats = {
        "total_reviewed_tm": len(rows),
        "affected_by_glossary": affected,
        "unaffected": counts.get("unaffected", 0),
        "compatible": counts.get("compatible", 0),
        "incompatible": counts.get("incompatible", 0),
        "ambiguous": counts.get("ambiguous", 0),
        "scope_sensitive": counts.get("scope_sensitive", 0),
        "incompatible_rate_among_affected":
            round(counts.get("incompatible", 0) / max(affected, 1), 4),
        "top_conflicting_terms": top_conflicts,
    }
    return rows, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tm", default="outputs/translation_memory.json")
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--out-dir", default="eval/results/round1/tm_compat")
    ap.add_argument("--label", default="")
    args = ap.parse_args(argv)

    tm = load_tm(Path(args.tm))
    glossary = load_glossary(Path(args.glossary))
    rows, stats = run_audit(tm, glossary)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "meta": {
            "label": args.label or "（未标注）",
            "tm_path": str(Path(args.tm)),
            "glossary_path": str(Path(args.glossary)),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "只读分析；不修改 TM；确定性规则，无法确定时归 ambiguous",
        },
        "stats": stats,
    }
    (out / "tm_compatibility_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "tm_compatibility_rows.csv").open("w", encoding="utf-8",
                                                  newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows
                                else ["tm_source"])
        writer.writeheader()
        writer.writerows(rows)
    md = ["# TM 兼容性审计", "",
          f"- 标签：{report['meta']['label']}",
          f"- TM：{report['meta']['tm_path']}（{stats['total_reviewed_tm']} 条 reviewed）",
          f"- 术语表：{report['meta']['glossary_path']}", ""]
    for k, v in stats.items():
        if k != "top_conflicting_terms":
            md.append(f"- {k}: {v}")
    if stats["top_conflicting_terms"]:
        md += ["", "## 冲突最多的术语（incompatible 条目数）", ""]
        for t in stats["top_conflicting_terms"][:15]:
            md.append(f"- {t['term']}: {t['incompatible_entries']} "
                      f"（共 {t['tm_entries_mentioning_term']} 条涉及）")
    (out / "tm_compatibility_report.md").write_text("\n".join(md) + "\n",
                                                    encoding="utf-8")
    print(f"TM compatibility -> {out / 'tm_compatibility_report.json'}")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
