"""定点重译任务中的问题段落（截断/审校 blocking），并清洗翻译记忆。

用法（项目根目录）：
    OPENCODE_GO_API_KEY=... .venv/bin/python scripts/fix_segments.py --job <job_id>
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--provider", default="OpenCode Go")
    ap.add_argument("--model", default="glm-5.2")
    ap.add_argument("--target-lang", default="简体中文")
    args = ap.parse_args()

    env_key = {"OpenCode Go": "OPENCODE_GO_API_KEY",
               "DeepSeek": "DEEPSEEK_API_KEY", "OpenAI": "OPENAI_API_KEY",
               "Gemini": "GEMINI_API_KEY"}.get(args.provider, "TRANSPRAXIS_API_KEY")
    api_key = os.environ.get(env_key) or os.environ.get("TRANSPRAXIS_API_KEY")
    if not api_key:
        sys.exit(f"请设置 {env_key} 或 TRANSPRAXIS_API_KEY")

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
    pairs = state["pairs"]

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
    # 3) 复用产品共享的定点重译和最终复验，避免脚本与 UI 分叉。
    state, fixed = core.retranslate_segments(
        args.job, to_fix, args.provider, api_key, args.model, args.target_lang,
        glossary=glossary, actor="system")
    stats = state.get("review_stats") or {}
    print(f"完成：重译 {len(fixed)}/{len(to_fix)} 段；"
          f"blocking {stats['blocking']} · actionable {stats['actionable']} · "
          f"informational {stats['informational']}")


if __name__ == "__main__":
    main()
