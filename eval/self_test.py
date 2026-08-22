"""离线自测：用合成 fixture 跑通 A/B/C/D 四臂 + 指标 + 报告 + 盲评抽样。

不访问网络、不使用真实语料。确定性 mock LLM 使四臂产出合规译文，
用于验证 harness 本身（不是验证质量）。

用法：python eval/self_test.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(ROOT))

from docx import Document  # noqa: E402

import run_ab  # noqa: E402


def _build_fixture_corpus(fixture: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    segments = fixture["segments"]
    doc = Document()
    for p in segments:
        doc.add_paragraph(p)
    docx_path = out_dir / "corpus.docx"
    doc.save(docx_path)
    with (out_dir / "corpus.jsonl").open("w", encoding="utf-8") as f:
        for i, p in enumerate(segments):
            f.write(json.dumps({"index": i, "source": p}, ensure_ascii=False) + "\n")
    (out_dir / "corpus_meta.json").write_text(json.dumps({
        "job_id": "synthetic-fixture",
        "filename": "synthetic_eval.docx",
        "subset": [0, len(segments)],
        "full_segments": len(segments),
        "selected_segments": len(segments),
        "source_chars": sum(len(p) for p in segments),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return docx_path


def main() -> int:
    fixture = json.loads(
        (EVAL_DIR / "fixtures" / "synthetic_eval.json").read_text(encoding="utf-8"))
    out_root = EVAL_DIR / "results" / "self-test"
    if out_root.exists():
        shutil.rmtree(out_root)
    corpus_dir = out_root / "corpus"
    docx_path = _build_fixture_corpus(fixture, corpus_dir)
    glossary_path = out_root / "glossary_fixture.json"
    glossary_path.write_text(json.dumps(
        {"entries": fixture["glossary"]}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    cfg_path = out_root / "config.json"
    cfg_path.write_text(json.dumps({
        "code": {"baseline_ref": "HEAD"},
        "corpus": {"job_id": "", "subset": [0, 0]},
        "glossary": str(glossary_path),
        "tm_seed": "",
        "run": {
            "provider": "DeepSeek", "model": "deepseek-v4-flash",
            "target_lang": "简体中文",
            "translation_theory": "目的论 (Skopos Theory)",
            "style_rules": "", "enable_review": True,
            "enable_annotate": False, "enable_report": False,
        },
        "arms": ["A", "B", "C", "D"],
        "seed": 42,
        "out_dir": str(out_root / "report"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    rc = run_ab.main([
        "--config", str(cfg_path),
        "--mock",
        "--corpus-override", str(docx_path),
        "--out", str(out_root / "report"),
    ])
    if rc != 0:
        print("self-test: run_ab 失败")
        return rc

    report = json.loads(
        (out_root / "report" / "evaluation-report.json").read_text(encoding="utf-8"))
    assert "quality_score" not in json.dumps(report), "禁止单一质量分"
    assert set(report["runs"]) == {"A", "B", "C", "D"}
    for arm, m in report["runs"].items():
        assert m["terminology"]["locked_term_adoption_rate"] == 1.0, \
            f"{arm}: 合规 mock 下锁定术语采纳率应为 1.0"
        assert m["terminology"]["forbidden_term_violations"] == 0
        assert m["terminology"]["preserve_failures"] == 0
        assert m["qa"]["blocking_per_1k_chars"] == 0
        assert m["workflow"]["total_segments"] == len(fixture["segments"])
    assert report["human_review"]["status"] == "pending"
    packet = out_root / "report" / "blind_review" / "blind_review_packet.csv"
    key = out_root / "report" / "blind_review" / "blind_review_key.csv"
    assert packet.is_file() and key.is_file(), "盲评抽样包与 key 文件必须生成"
    n_rows = sum(1 for _ in packet.open(encoding="utf-8")) - 1
    assert 0 < n_rows <= 80, f"抽样段数应在 1..80：{n_rows}"
    terms_csv = out_root / "report" / "terms_adoption.csv"
    assert terms_csv.is_file()
    md = (out_root / "report" / "evaluation-report.md").read_text(encoding="utf-8")
    assert "A_to_B" in md and "A_to_D" in md
    print(f"self-test 通过：4 臂 × {len(fixture['segments'])} 段 · "
          f"盲评包 {n_rows} 段 · 无 quality_score")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
