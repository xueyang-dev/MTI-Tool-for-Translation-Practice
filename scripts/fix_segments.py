"""定点重译任务中的问题段落（截断/审校 blocking），并清洗翻译记忆。

用法（项目根目录）：
    DEEPSEEK_API_KEY=... .venv/bin/python scripts/fix_segments.py --job <job_id>
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--provider", default="DeepSeek")
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--target-lang", default="简体中文")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("请设置 DEEPSEEK_API_KEY")

    # 1) 清洗翻译记忆：剔除截断/不完整译文（备份原文件）
    tm_file = core.tm_path()
    if tm_file.is_file():
        shutil.copy(tm_file, tm_file.with_suffix(".json.bak"))
    tm = core.load_tm()
    poison = [k for k, v in tm.items()
              if core.is_incomplete_translation(k, (v or {}).get("target", ""))]
    for k in poison:
        del tm[k]
    core.save_tm(tm)
    print(f"翻译记忆：剔除 {len(poison)} 条不完整译文，剩余 {len(tm)} 条")

    state = core.load_job_state(args.job)
    if not state:
        sys.exit(f"找不到任务 {args.job}")
    paras, pairs = state["paras"], state["pairs"]

    # 2) 待修复集合：完整性规则命中 + 审校 blocking
    flagged = {i for i, pr in enumerate(pairs)
               if core.is_incomplete_translation(pr["source"], pr["target"])}
    review_blocked = {f["segment_index"] for f in state.get("findings", [])
                      if f.get("severity") == "blocking" and f.get("type") == "review"}
    to_fix = sorted(flagged | review_blocked)
    print(f"待重译段落：{len(to_fix)}（完整性 {len(flagged)} + 审校 blocking {len(review_blocked - flagged)}）")
    if not to_fix:
        return

    glossary = core.normalize_glossary(
        [{"source": k, "target": v, "behavior": "translate", "status": "provisional"}
         for k, v in (state.get("auto_terms") or {}).items()])
    glossary_text = core.glossary_block(glossary)

    # 3) 逐段重译（带前后文），完整性把关 + 自动修复一轮
    fixed = 0
    for n, idx in enumerate(to_fix, 1):
        src = pairs[idx]["source"]
        ctx_prev = paras[max(0, idx - 2):idx]
        ctx_next = paras[idx + 1:idx + 3]
        try:
            tgt = core.translate_batch([src], ctx_prev, ctx_next, glossary_text, "",
                                       args.target_lang, args.provider, api_key, args.model)[0]
            tgt = core.clean_xml_chars(tgt).replace("\n", " ")
            findings = core.check_translation_batch([src], [tgt], glossary, args.target_lang)
            fixable = [f for f in findings if f["severity"] in ("blocking", "actionable")]
            if fixable:
                repaired = core.repair_batch([src], [tgt], fixable, glossary_text, "",
                                             args.target_lang, args.provider, api_key, args.model)
                if repaired and repaired[0].strip() \
                        and not core.is_incomplete_translation(src, repaired[0]):
                    tgt = core.clean_xml_chars(repaired[0]).replace("\n", " ")
            pairs[idx]["target"] = tgt
            pairs[idx]["from_tm"] = False
            pairs[idx]["reviewed"] = False
            fixed += 1
            print(f"  [{n}/{len(to_fix)}] 段 {idx} 已重译（{len(src)} -> {len(tgt)} 字符）")
        except Exception as e:
            print(f"  [{n}/{len(to_fix)}] 段 {idx} 重译失败：{str(e)[:120]}")
        if n % 10 == 0:
            core.save_job_state(args.job, state)  # 中途落盘
        time.sleep(0.5)

    # 4) 清理已修复段落的旧 findings，重算统计
    fixed_set = set(to_fix)
    state["findings"] = [f for f in state.get("findings", [])
                         if f.get("segment_index") not in fixed_set
                         or f.get("severity") == "informational"]
    # 复验：仍不完整的段落重新记录 blocking
    for i in to_fix:
        pr = pairs[i]
        if core.is_incomplete_translation(pr["source"], pr["target"]):
            state["findings"].append({"segment_index": i, "severity": "blocking",
                                      "type": "check", "reason": "重译后仍疑似不完整，需人工核对"})
    stats = state.setdefault("review_stats", {})
    stats["blocking"] = sum(1 for f in state["findings"] if f["severity"] == "blocking")
    stats["actionable"] = sum(1 for f in state["findings"] if f["severity"] == "actionable")
    stats["informational"] = sum(1 for f in state["findings"] if f["severity"] == "informational")
    state["has_blocking"] = stats["blocking"] > 0
    core.save_job_state(args.job, state)
    print(f"完成：重译 {fixed}/{len(to_fix)} 段；"
          f"blocking {stats['blocking']} · actionable {stats['actionable']} · "
          f"informational {stats['informational']}")


if __name__ == "__main__":
    main()
