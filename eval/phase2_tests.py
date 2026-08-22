"""Phase 2 测试：术语审核表 / 盲评包 v2 / TM 兼容性 / approved 重算。

全部离线（零 provider 调用），使用合成 fixture 与临时目录。
运行：python eval/phase2_tests.py
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EVAL_DIR))

from transpraxis.terminology import term_matches  # noqa: E402

import approved_recompute  # noqa: E402
import term_audit  # noqa: E402
import tm_compatibility  # noqa: E402
from sampling import blind_review  # noqa: E402


def _mk_state(pairs, findings=None):
    return {"pairs": pairs, "findings": findings or [],
            "review_stats": {}, "tm_used_count": 0, "delivery_status": "draft"}


def _mk_pairs(n, prefix, identical_until=-1):
    pairs = []
    for i in range(n):
        tgt = f"{prefix}-译文{i}" if i >= identical_until else f"共同译文{i}"
        pairs.append({"source": f"source segment {i} with term T{i % 5}.",
                      "target": tgt, "reviewed": True, "from_tm": False})
    return pairs


def _glossary_entries():
    return [
        {"source": "Skopos theory", "target": "目的论", "preferred": "目的论",
         "forbidden": ["功能对等"], "behavior": "translate", "status": "locked",
         "scope": "global", "decision": "approved"},
        {"source": "Heading", "target": "航向", "preferred": "航向",
         "forbidden": [], "behavior": "translate", "status": "locked",
         "scope": "global", "decision": "approved", "variants": ["航向角"]},
        {"source": "bank", "target": "银行", "preferred": "银行",
         "forbidden": [], "behavior": "translate", "status": "locked",
         "scope": "section:finance", "decision": "scope_sensitive"},
        {"source": "Horizon", "target": "地平线", "preferred": "地平线",
         "forbidden": [], "behavior": "translate", "status": "locked",
         "scope": "global", "decision": "variant_allowed",
         "variants": ["天际线"]},
    ]


# ---------------- TM 兼容性分类 ----------------

def test_tm_unaffected():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "The cat sat on the mat.", "猫坐在垫子上。", g)
    assert r["classification"] == "unaffected"
    print("  ✓ TM unaffected 分类")


def test_tm_compatible():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "The Skopos theory is central.", "目的论是核心。", g)
    assert r["classification"] == "compatible"
    print("  ✓ TM compatible 分类")


def test_tm_incompatible_preferred_mismatch():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "The Skopos theory is central.", "翻译目的学派是核心。", g)
    assert r["classification"] == "incompatible"
    assert "期望" in r["reasons"][0]
    print("  ✓ TM incompatible（preferred mismatch）")


def test_tm_allowed_variants():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "Set the heading to 030.", "将航向角设为030。", g)
    assert r["classification"] == "compatible"
    print("  ✓ TM allowed variants")


def test_tm_forbidden_targets():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "Skopos theory guides the work.", "功能对等指导这项工作。", g)
    assert r["classification"] == "incompatible"
    assert "禁止" in r["reasons"][0]
    print("  ✓ TM forbidden targets")


def test_tm_scope_sensitive():
    g = _glossary_entries()
    r = tm_compatibility.classify_tm_entry(
        "The bank approved the loan.", "银行批准了贷款。", g)
    assert r["classification"] == "scope_sensitive", r
    print("  ✓ TM scope_sensitive（缺 section 上下文）")


def test_tm_ambiguous_fallback():
    g = _glossary_entries()
    # 原文保留 -> ambiguous
    r1 = tm_compatibility.classify_tm_entry(
        "Skopos theory is central.", "Skopos theory 是核心。", g)
    assert r1["classification"] == "ambiguous"
    # variant_allowed 且未见认可译法/禁止译名 -> ambiguous（不强行 incompatible）
    r2 = tm_compatibility.classify_tm_entry(
        "The horizon glowed red.", "视野泛红。", g)
    assert r2["classification"] == "ambiguous"
    print("  ✓ TM ambiguous 兜底（原文保留 / variant_allowed 开放集合）")


# ---------------- 盲评包 v2 ----------------

def test_packet_v2_balance_and_decode():
    n = 120
    segs = [f"segment {i} with Skopos theory." for i in range(n)]
    a = _mk_state(_mk_pairs(n, "A"))
    b = _mk_state(_mk_pairs(n, "B"))
    rows, keys = blind_review.sample_packet_v2(
        a, b, segs, _glossary_entries(), seed=7)
    assert len(rows) == 80
    left_a = sum(1 for k in keys if k["candidate_a_is_arm"] == "A")
    assert 36 <= left_a <= 44, f"A/B 左位应接近 50/50：{left_a}/80"
    # key 解码：candidate 必须与对应 arm 的 target 一致
    by_id = {r["packet_id"]: r for r in rows}
    for k in keys:
        r = by_id[k["packet_id"]]
        i = int(r["segment_id"])
        if k["candidate_a_is_arm"] == "A":
            assert r["candidate_a"] == a["pairs"][i]["target"]
            assert r["candidate_b"] == b["pairs"][i]["target"]
        else:
            assert r["candidate_a"] == b["pairs"][i]["target"]
            assert r["candidate_b"] == a["pairs"][i]["target"]
    # packet 不得泄露 arm 名
    assert "arm" not in " ".join(rows[0].keys()).lower()
    print(f"  ✓ 盲评包 v2：80 对 / 左位平衡 {left_a}/80 / key 可解码 / 无 arm 泄漏")


def test_packet_v2_excludes_identical_when_alternatives():
    n = 120
    segs = [f"segment {i}." for i in range(n)]
    # 前 40 段两臂相同，后 80 段有差异（有足够差异对）
    a_pairs = _mk_pairs(n, "A", identical_until=40)
    b_pairs = _mk_pairs(n, "B", identical_until=40)
    a = _mk_state(a_pairs)
    b = _mk_state(b_pairs)
    rows, _ = blind_review.sample_packet_v2(a, b, segs, [], seed=3)
    assert len(rows) == 80
    identical = [r for r in rows if r["identical"] == "1"]
    assert identical == [], "存在足够差异对时不得占用预算给相同对"
    assert all(int(r["segment_id"]) in range(40, 120) for r in rows)
    # 差异不足时：允许 identical_fallback 补齐，但必须如实标记
    a2 = _mk_state(_mk_pairs(30, "A"))
    b2 = _mk_state(_mk_pairs(30, "B"))
    rows2, _ = blind_review.sample_packet_v2(a2, b2, segs[:30], [], seed=3,
                                             max_total=30)
    assert len(rows2) == 30
    print("  ✓ 盲评包 v2：优先有效差异；不足时回退并标记")


# ---------------- approved glossary 导入 ----------------

def test_approved_glossary_import():
    tmp = Path(tempfile.mkdtemp(prefix="rt2-import-"))
    try:
        audit = tmp / "term_audit.csv"
        rows = [
            {"source": "Skopos theory", "proposed_target": "目的论",
             "decision": "approved", "approved_target": "翻译目的论",
             "variants": "", "scope": "global", "case_sensitive": ""},
            {"source": "Heading", "proposed_target": "航向",
             "decision": "variant_allowed", "approved_target": "航向",
             "variants": "航向角;机头方向", "scope": "global",
             "case_sensitive": ""},
            {"source": "bank", "proposed_target": "银行",
             "decision": "scope_sensitive", "approved_target": "银行",
             "variants": "", "scope": "section:finance", "case_sensitive": ""},
            {"source": "bank", "proposed_target": "银行",
             "decision": "scope_sensitive", "approved_target": "河岸",
             "variants": "", "scope": "global", "case_sensitive": ""},
            {"source": "MT", "proposed_target": "机器翻译",
             "decision": "rejected", "approved_target": "机器翻译",
             "variants": "", "scope": "global", "case_sensitive": ""},
            {"source": "Knots", "proposed_target": "节",
             "decision": "approved", "approved_target": "",
             "variants": "", "scope": "global", "case_sensitive": ""},
            {"source": "Horizon", "proposed_target": "地平线",
             "decision": "needs_review", "approved_target": "",
             "variants": "", "scope": "global", "case_sensitive": ""},
        ]
        with audit.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=term_audit.FIELDS,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        src_glossary = [
            {"source": "Skopos theory", "target": "目的论", "behavior": "translate"},
            {"source": "Heading", "target": "航向", "behavior": "translate"},
            {"source": "bank", "target": "银行", "behavior": "translate"},
            {"source": "MT", "target": "机器翻译", "behavior": "translate"},
            {"source": "Horizon", "target": "地平线", "behavior": "translate"},
        ]
        out = tmp / "approved_glossary.json"
        term_audit.import_approved_glossary(audit, src_glossary, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        entries = data["entries"]
        by_source = {e["source"]: e for e in entries}
        assert set(by_source) == {"Skopos theory", "Heading", "bank"}
        assert by_source["Skopos theory"]["preferred"] == "翻译目的论"
        assert by_source["Heading"]["variants"] == ["航向角", "机头方向"]
        assert by_source["Heading"]["decision"] == "variant_allowed"
        assert by_source["bank"]["scope"] == "section:finance"
        assert "MT" not in by_source and "Horizon" not in by_source
        assert "Knots" not in by_source
        assert any("缺少 approved_target" in s for s in data["skipped"])
        assert any("scope_sensitive" in s for s in data["skipped"])
        print("  ✓ approved glossary 导入（approved/variant/scope 纳入，"
              "rejected/needs_review/缺字段跳过）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- report-only 重算 ----------------

def _mk_results_dir(root: Path, n: int = 8):
    """构造最小 results-dir fixture（runs/A..D + evaluation-report.json）。"""
    for arm in "ABCD":
        run_dir = root / "runs" / arm
        job = f"job-{arm}"
        (run_dir / job).mkdir(parents=True, exist_ok=True)
        pairs = [{"source": f"Skopos theory in segment {i}.",
                  "target": f"目的论译文{i}" if i % 2 == 0 else "翻译目的学派译文",
                  "reviewed": True, "from_tm": False} for i in range(n)]
        (run_dir / job / "state.json").write_text(
            json.dumps(_mk_state(pairs), ensure_ascii=False), encoding="utf-8")
        (run_dir / "run_meta.json").write_text(json.dumps(
            {"arm": arm, "job_id": job, "segments": n, "llm_calls": 0,
             "code_ref": "test", "tm_seeded": False, "mock": True}),
            encoding="utf-8")
    report = {"runs": {arm: {"terminology": {
        "locked_term_adoption_rate": None, "forbidden_term_violations": 0,
        "preserve_failures": 0, "scope_conflicts": 0, "per_term": []},
        "qa": {}, "workflow": {}} for arm in "ABCD"}}
    (root / "evaluation-report.json").write_text(
        json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return root


def test_report_only_zero_provider_calls_and_no_overwrite():
    import core
    tmp = Path(tempfile.mkdtemp(prefix="rt2-recompute-"))
    try:
        results = _mk_results_dir(tmp / "results")
        original_bytes = (results / "evaluation-report.json").read_bytes()
        calls = {"n": 0}
        original_llm = core.call_llm

        def counting(*args, **kwargs):
            calls["n"] += 1
            return "[]"

        core.call_llm = counting
        try:
            approved = tmp / "approved_glossary.json"
            approved.write_text(json.dumps({
                "entries": [{"source": "Skopos theory", "target": "目的论",
                             "preferred": "目的论", "forbidden": [],
                             "behavior": "translate", "status": "locked",
                             "scope": "global", "decision": "approved",
                             "variants": [], "case_sensitive": False}]}),
                encoding="utf-8")
            out = tmp / "reports" / "recomputed.json"
            rc = approved_recompute.main([
                "--results-dir", str(results),
                "--approved", str(approved),
                "--out", str(out),
            ])
            assert rc == 0
            assert calls["n"] == 0, "report-only 不得调用任何 provider"
            data = json.loads(out.read_text(encoding="utf-8"))
            assert data["meta"]["status"] == "human-approved"
            assert set(data["human_approved_glossary_metrics"]) == \
                set("ABCD")
            # 原始结果未被覆盖
            assert (results / "evaluation-report.json").read_bytes() == \
                original_bytes
            assert not (results / "recomputed.json").exists()
        finally:
            core.call_llm = original_llm
        # pending 状态：无 approved glossary 时明确标注，不伪造
        out2 = tmp / "reports2" / "recomputed.json"
        approved_recompute.main([
            "--results-dir", str(results),
            "--approved", str(tmp / "missing.json"),
            "--out", str(out2),
        ])
        data2 = json.loads(out2.read_text(encoding="utf-8"))
        assert data2["meta"]["status"] == "pending_human_glossary_decisions"
        assert data2["human_approved_glossary_metrics"] is None
        print("  ✓ report-only：零 provider 调用 / 原始结果不覆盖 / pending 明确标注")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    tests = [
        test_tm_unaffected,
        test_tm_compatible,
        test_tm_incompatible_preferred_mismatch,
        test_tm_allowed_variants,
        test_tm_forbidden_targets,
        test_tm_scope_sensitive,
        test_tm_ambiguous_fallback,
        test_packet_v2_balance_and_decode,
        test_packet_v2_excludes_identical_when_alternatives,
        test_approved_glossary_import,
        test_report_only_zero_provider_calls_and_no_overwrite,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            failed += 1
            print(f"  ✗ {t.__name__}: {type(e).__name__}: {e}")
    print(f"\nphase2 tests: {len(tests) - failed}/{len(tests)} passed, "
          f"{failed} failed")
    sys.exit(1 if failed else 0)
