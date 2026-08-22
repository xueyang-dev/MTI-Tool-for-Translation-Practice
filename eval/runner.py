"""单臂执行器：在指定代码根下运行一次完整流水线并落盘 state。

设计约束：
- 只使用 core 的公共 API，且 arm A/C 运行在 pre-governance 基线
  本地 baseline worktree 上，arm B/D 运行在当前代码上；
- 因此本文件不得 import transpraxis（基线 worktree 没有该包）；
- --mock 提供确定性 LLM（离线自测用），真实运行通过环境变量
  TRANSPRAXIS_EVAL_API_KEY 提供 API Key，并统计 LLM 调用次数。

用法（由 run_ab.py 调用）：
    PYTHONPATH=<code_root> python eval/runner.py \
        --run-dir DIR --corpus corpus.docx --glossary g.json --arm A \
        [--tm-seed tm.json] [--mock] [--code-ref <commit>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path


def _matches(term: str, text: str) -> bool:
    """词边界 + 大小写不敏感的术语匹配（runner 内嵌实现，避免依赖 transpraxis）。"""
    term = (term or "").strip()
    text = text or ""
    if not term or not text:
        return False
    if re.search(r"[\u4e00-\u9fff]", term):
        return term in text
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])",
                     re.IGNORECASE)
    return bool(pat.search(text))


def _numbered(user_prompt: str):
    segs = [(int(m.group(1)), m.group(2).strip())
            for m in re.finditer(r'^\s*(\d+)\.\s+(.+?)\s*$', user_prompt, re.M)]
    segs.sort(key=lambda x: x[0])
    return segs


def make_mock_llm(glossary_entries):
    """确定性合规 mock：锁定术语用首选译名、保留 token、补齐长度/句数。

    仅用于 eval/self_test.py 的离线自测，不用于真实评测。
    """
    def llm(provider, api_key, model, system_prompt, user_prompt, temperature=0.1):
        if "术语管理专家" in system_prompt:
            return '[]'
        if "翻译审校专家" in system_prompt:
            return '[]'
        if "学术翻译专家" in system_prompt:
            out = []
            for _, src in _numbered(user_prompt):
                parts = []
                for e in glossary_entries:
                    source = str(e.get("source") or "").strip()
                    behavior = str(e.get("behavior") or "translate").lower()
                    status = str(e.get("status") or "provisional").lower()
                    if status == "rejected" or not _matches(source, src):
                        continue
                    if behavior == "preserve":
                        parts.append(source)
                    elif status == "locked":
                        preferred = str(e.get("preferred") or e.get("target") or "").strip()
                        if preferred:
                            parts.append(preferred)
                import core as _core
                for tok, _kind in _core.extract_preserved_tokens(src).items():
                    if tok not in " ".join(parts):
                        parts.append(tok)
                if not parts:
                    parts.append("译文")
                tgt = "。".join(parts) + "。"
                need = max(int(0.2 * len(src)) + 1 - len(tgt), 0)
                tgt += "内容填充内容填充" * (need // 6 + 1)
                src_sents = _core._count_sentences(src)
                tgt_sents = tgt.count("。")
                if src_sents >= 2 and tgt_sents < src_sents * 0.5:
                    tgt += "补充句子。" * (src_sents * 2 - tgt_sents)
                out.append(tgt)
            return json.dumps(out)
        return "报告章节内容。"
    return llm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--corpus", required=True, help="corpus.docx（确定性子集）")
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--arm", required=True, choices=["A", "B", "C", "D"])
    ap.add_argument("--tm-seed", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--code-ref", default="unknown")
    ap.add_argument("--provider", default="DeepSeek")
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--target-lang", default="简体中文")
    ap.add_argument("--theory", default="目的论 (Skopos Theory)")
    ap.add_argument("--style-rules", default="保持学术书面语；专有名词、作者姓名、机构名、"
                                            "引用标注、URL 等保留原文；标点遵循目标语言规范。")
    ap.add_argument("--enable-review", action="store_true", default=True)
    args = ap.parse_args()

    import core

    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    core.OUTPUT_DIR = run_dir

    # TM 种子：arms C/D 在运行前注入审校 TM（A/B 不注入）
    if args.tm_seed:
        tm_dst = run_dir / "translation_memory.json"
        shutil.copyfile(args.tm_seed, tm_dst)

    # LLM：mock（离线自测）或真实（计数包装）
    entries = json.loads(Path(args.glossary).read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("entries") or []
    llm_calls = {"n": 0}
    if args.mock:
        core.call_llm = make_mock_llm(entries)
    else:
        original = core.call_llm

        def counted(provider, api_key, model, system_prompt, user_prompt,
                    temperature=0.1):
            llm_calls["n"] += 1
            return original(provider, api_key, model, system_prompt, user_prompt,
                            temperature)

        core.call_llm = counted

    api_key = os.environ.get("TRANSPRAXIS_EVAL_API_KEY", "")
    if not args.mock and not api_key:
        print(json.dumps({"ok": False, "error": "缺少 TRANSPRAXIS_EVAL_API_KEY"}))
        return 2

    docx_bytes = Path(args.corpus).read_bytes()
    job_id = core.file_job_id(docx_bytes)
    filename = Path(args.corpus).name
    core.save_job_state(job_id, core.new_job_state(filename))

    common = dict(
        provider=args.provider, api_key=api_key if not args.mock else "mock-key",
        model=args.model, target_lang=args.target_lang, auto_term=False,
        enable_report=False, translation_theory=args.theory,
        user_glossary=entries, style_rules=args.style_rules,
        enable_review=args.enable_review, enable_annotate=False,
    )
    t0 = time.time()
    if args.arm in ("B", "D"):
        # 新代码：先冻结术语表，再以 quality mode 运行（freeze gate 通过）
        core.freeze_glossary(job_id, entries=entries, frozen_by="eval")
        core.run_job_pipeline(job_id, filename, docx_bytes, mode="quality", **common)
    else:
        # baseline：无 mode 参数，直接运行（术语整体注入）
        core.run_job_pipeline(job_id, filename, docx_bytes, **common)

    state = core.load_job_state(job_id)
    n_segments = len(state.get("pairs") or [])
    (run_dir / "run_meta.json").write_text(json.dumps({
        "arm": args.arm,
        "code_ref": args.code_ref,
        "llm_calls": llm_calls["n"],
        "job_id": job_id,
        "segments": n_segments,
        "elapsed_s": round(time.time() - t0, 2),
        "tm_seeded": bool(args.tm_seed),
        "mock": bool(args.mock),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "job_id": job_id, "segments": n_segments,
                      "llm_calls": llm_calls["n"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
