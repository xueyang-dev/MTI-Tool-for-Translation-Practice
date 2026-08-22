"""人工术语审核：生成审核表 + 导入审核结果。

Task 1：
1) 生成 eval/term_audit.csv —— 自动填充统计（occurrences / sample_contexts /
   current_adoption_rate），decision 与 approved_target 等人工字段留空；
   **不替用户决定术语**，自动 glossary 不是 ground truth。
2) 审核完成后从 term_audit.csv 导入 eval/approved_glossary.json ——
   只纳入 decision ∈ {approved, scope_sensitive, variant_allowed} 且
   approved_target 明确的条目；scope_sensitive 必须填写 scope，否则跳过并警告。

用法：
    python eval/term_audit.py --results-dir eval/results/round1 \
        --out eval/term_audit.csv
    python eval/term_audit.py --import-audit eval/term_audit.csv \
        --out eval/approved_glossary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import models  # noqa: E402
from transpraxis.terminology import term_matches  # noqa: E402

DECISIONS = ("approved", "rejected", "scope_sensitive", "variant_allowed",
             "needs_review")
FIELDS = [
    "source", "proposed_target", "current_status", "occurrences",
    "sample_contexts", "current_adoption_rate", "decision",
    "approved_target", "variants", "scope", "case_sensitive", "notes",
]


def _load_glossary(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries") or []
    return models.normalize_glossary(data)


def _load_corpus(path: Path) -> List[str]:
    segs: List[str] = []
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            for line in f:
                segs.append(json.loads(line)["source"])
    return segs


def _load_pairs(state_path: Path) -> List[Dict[str, Any]]:
    if not state_path.is_file():
        return []
    return json.loads(state_path.read_text(encoding="utf-8")).get("pairs") or []


def _context_snippets(segments: List[str], term: str, limit: int = 3,
                      width: int = 60) -> List[str]:
    out = []
    for seg in segments:
        if term_matches(term, seg):
            out.append(seg[:width] + ("…" if len(seg) > width else ""))
            if len(out) >= limit:
                break
    return out


def generate_audit_rows(glossary: List[Dict[str, Any]],
                        segments: List[str],
                        pairs: List[Dict[str, Any]],
                        contexts_segments: List[str] | None = None) -> List[Dict[str, str]]:
    """自动填充统计；decision/approved_target/variants/scope/case_sensitive 留空。"""
    ctx_segs = contexts_segments if contexts_segments is not None else segments
    rows: List[Dict[str, str]] = []
    for e in glossary:
        term = e["source"]
        occ = [i for i, seg in enumerate(segments) if term_matches(term, seg)]
        adopted = 0
        if e["behavior"] != "preserve":
            pref = e.get("preferred") or e["target"] or ""
            for i in occ:
                if 0 <= i < len(pairs) and pref \
                        and term_matches(pref, pairs[i].get("target", "")):
                    adopted += 1
        rate = round(adopted / len(occ), 4) if occ else None
        notes = []
        if rate is not None and rate < 0.9:
            notes.append("低采纳率，请人工判断是否 scope_sensitive / variant_allowed")
        elif rate is not None and rate < 1.0:
            notes.append("未完全采纳，建议人工确认")
        if e.get("status") == "locked":
            notes.append("当前为自动锁定（未经人工审核），非 ground truth")
        rows.append({
            "source": term,
            "proposed_target": e.get("target") or "",
            "current_status": e.get("status") or "",
            "occurrences": str(len(occ)),
            "sample_contexts": " || ".join(
                _context_snippets(ctx_segs, term)) if ctx_segs else "",
            "current_adoption_rate": "" if rate is None else str(rate),
            "decision": "",
            "approved_target": "",
            "variants": "",
            "scope": e.get("scope") or "global",
            "case_sensitive": "",
            "notes": "；".join(notes),
        })
    return rows


def write_audit_csv(rows: List[Dict[str, str]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def import_approved_glossary(audit_path: Path,
                             source_glossary: List[Dict[str, Any]],
                             out_path: Path) -> Path:
    """从人工审核表生成 approved_glossary.json（只纳入明确确认的规则）。"""
    with audit_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_source = {e["source"].casefold(): e for e in source_glossary}
    entries: List[Dict[str, Any]] = []
    skipped: List[str] = []
    for row in rows:
        decision = (row.get("decision") or "").strip().lower()
        if decision not in ("approved", "scope_sensitive", "variant_allowed"):
            continue
        source = (row.get("source") or "").strip()
        approved_target = (row.get("approved_target") or "").strip()
        if not source:
            continue
        orig = by_source.get(source.casefold()) or {}
        behavior = orig.get("behavior", "translate")
        if behavior == "preserve":
            approved_target = approved_target or source
        elif not approved_target:
            skipped.append(f"{source}: {decision} 缺少 approved_target")
            continue
        scope = (row.get("scope") or "").strip() or "global"
        if decision == "scope_sensitive" and scope == "global":
            skipped.append(f"{source}: scope_sensitive 但未填写有效 scope")
            continue
        variants = [v.strip() for v in
                    (row.get("variants") or "").replace("；", ";").split(";")
                    if v.strip()]
        entries.append({
            "source": source,
            "target": approved_target,
            "preferred": approved_target,
            "forbidden": list(orig.get("forbidden") or []),
            "behavior": behavior,
            "status": "locked",
            "scope": scope,
            "decision": decision,
            "note": f"human-approved ({decision})",
            "variants": variants,
            "case_sensitive": (row.get("case_sensitive") or "").strip().lower()
            in ("true", "yes", "1"),
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "source_audit": str(audit_path),
        "human_reviewed": True,
        "entries": entries,
        "skipped": skipped,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="eval/results/round1")
    ap.add_argument("--out", default="eval/term_audit.csv")
    ap.add_argument("--import-audit", default=None,
                    help="从审核表导入 approved_glossary.json")
    ap.add_argument("--glossary", default=None,
                    help="源术语表（缺省用 results-dir/glossary_eval.json）")
    ap.add_argument("--glossary-out", default="eval/approved_glossary.json")
    ap.add_argument("--contexts-corpus", default=None,
                    help="可选：全文 jsonl（用于补全 sample_contexts，"
                         "避免子集外的术语上下文为 NaN）")
    args = ap.parse_args(argv)

    results = Path(args.results_dir)
    glossary_path = Path(args.glossary) if args.glossary else \
        results / "glossary_eval.json"
    if not glossary_path.is_file():
        print(f"找不到术语表：{glossary_path}")
        return 2
    glossary = _load_glossary(glossary_path)

    if args.import_audit:
        audit = Path(args.import_audit)
        if not audit.is_file():
            print(f"找不到审核表：{audit}")
            return 2
        out = Path(args.glossary_out)
        import_approved_glossary(audit, glossary, out)
        print(f"approved glossary -> {out}")
        return 0

    segments = _load_corpus(results / "corpus.jsonl")
    contexts_segments = _load_corpus(Path(args.contexts_corpus)) \
        if args.contexts_corpus else None
    # 用 governance 臂（B）的译文计算 current_adoption_rate
    pairs = _load_pairs(results / "runs" / "B" /
                        _first_job_id(results / "runs" / "B") / "state.json") \
        if (results / "runs" / "B").is_dir() else []
    rows = generate_audit_rows(glossary, segments, pairs, contexts_segments)
    out = Path(args.out)
    write_audit_csv(rows, out)
    print(f"term audit -> {out}（{len(rows)} 条；decision 留空，待人工填写）")
    return 0


def _first_job_id(run_dir: Path) -> str:
    for p in sorted(run_dir.iterdir()):
        if p.is_dir():
            return p.name
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
