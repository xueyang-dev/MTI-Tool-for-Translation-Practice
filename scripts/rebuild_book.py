"""用确定性段落重建修复既有翻译任务（一次性迁移脚本）。

背景：旧版阶段一用 LLM 清洗 PDF 文本，造成碎句/过度合并；审校环节的整段替换
又导致部分长段译文被截断。本脚本：
1. 用 core.extract_pdf_paragraphs 重新提取段落（确定性、可复现）；
2. 把旧译文按字符流对齐到新段落：仅复用"覆盖完整且本身合格"的旧译文
   （截断疑似段落一律不复用），注入翻译记忆；
3. 其余段落走修复后的 translate_stage（完整性检查 + 修复 + 独立审校）；
4. 产出新的双语对照/译文/审查报告。

用法（项目根目录）：
    DEEPSEEK_API_KEY=... .venv/bin/python scripts/rebuild_book.py \
        --job <旧job_id> --pdf <源PDF路径> [--review]
"""
import argparse
import bisect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core


def norm(s):
    """对齐用归一化：统一引号/破折号/省略号，去全部空白，小写。"""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("…", "...")
    return re.sub(r"\s+", "", s).lower()


def is_cjk(text):
    return any("一" <= ch <= "鿿" for ch in text)


def align_reuse(new_paras, old_pairs):
    """字符流对齐：返回 {new_idx: joined_target}（仅完整覆盖且旧译文合格时复用）。"""
    boundaries, parts, pos = [], [], 0
    for j, p in enumerate(new_paras):
        n = norm(p)
        boundaries.append((pos, pos + len(n), j))
        parts.append(n)
        pos += len(n)
    stream = "".join(parts)
    starts = [b[0] for b in boundaries]

    def para_at(p):
        return boundaries[bisect.bisect_right(starts, p) - 1][2]

    # 旧段落 -> 新段落区间（仅记录完整落在流中的映射）
    old_span = {}
    pos = 0
    skipped_suspect, not_found = 0, 0
    for oi, pr in enumerate(old_pairs):
        src, tgt = pr.get("source", ""), pr.get("target", "")
        n = norm(src)
        if not n:
            continue
        # 截断疑似/空译文不参与复用，逼迫对应新段落重译
        if not tgt.strip() or core.is_incomplete_translation(src, tgt):
            skipped_suspect += 1
            continue
        p = stream.find(n, pos)
        if p < 0:
            p = stream.find(n)
            if p < 0:
                not_found += 1
                continue
        old_span[oi] = (para_at(p), para_at(p + len(n) - 1))
        pos = p + len(n)

    cover = {}
    for oi, (a, b) in old_span.items():
        if a == b:
            cover.setdefault(a, []).append(oi)
    reused = {}
    for j, ois in cover.items():
        ois.sort()
        joined_src = "".join(norm(old_pairs[oi]["source"]) for oi in ois)
        if joined_src != norm(new_paras[j]):
            continue
        sep = "" if is_cjk(old_pairs[ois[0]]["target"]) else " "
        reused[j] = sep.join(old_pairs[oi]["target"].strip() for oi in ois)
    stats = {"old_total": len(old_pairs), "skipped_suspect": skipped_suspect,
             "not_found": not_found, "reused": len(reused), "new_total": len(new_paras)}
    return reused, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="旧任务 job_id")
    ap.add_argument("--pdf", required=True, help="源 PDF 路径")
    ap.add_argument("--review", action="store_true", help="重译段落启用独立审校")
    ap.add_argument("--provider", default="OpenCode Go")
    ap.add_argument("--model", default="glm-5.2")
    ap.add_argument("--target-lang", default="简体中文")
    args = ap.parse_args()

    import os
    env_key = {"OpenCode Go": "OPENCODE_GO_API_KEY",
               "DeepSeek": "DEEPSEEK_API_KEY", "OpenAI": "OPENAI_API_KEY",
               "Gemini": "GEMINI_API_KEY"}.get(args.provider, "TRANSPRAXIS_API_KEY")
    api_key = os.environ.get(env_key) or os.environ.get("TRANSPRAXIS_API_KEY")
    if not api_key:
        sys.exit(f"请设置 {env_key} 或 TRANSPRAXIS_API_KEY 环境变量")

    old_state = core.load_job_state(args.job)
    if not old_state:
        sys.exit(f"找不到旧任务 {args.job}")
    pdf_path = Path(args.pdf)
    file_bytes = pdf_path.read_bytes()

    print("【1/4】确定性段落重建...")
    new_paras = core.extract_pdf_paragraphs(file_bytes)
    if not new_paras:
        sys.exit("PDF 无文本层，无法重建")
    print(f"  新段落数：{len(new_paras)}（旧：{len(old_state['paras'])}）")

    print("【2/4】字符流对齐，复用合格旧译文...")
    reused, stats = align_reuse(new_paras, old_state["pairs"])
    print(f"  复用 {stats['reused']}/{stats['new_total']} 段；"
          f"旧译文截断疑似跳过 {stats['skipped_suspect']} 段；"
          f"旧文本被 LLM 改动无法定位 {stats['not_found']} 段")

    # 新任务：job_id 派生自文件哈希 + v2 标记，旧任务保留可回滚
    new_job = core.file_job_id(file_bytes + b"-v2")
    print(f"【3/4】新任务 {new_job}：重译剩余 {len(new_paras) - stats['reused']} 段...")
    core.save_source(new_job, file_bytes)
    state = core.new_job_state(pdf_path.name)
    state["paras"] = new_paras
    state["p1_done"] = True
    state["auto_terms"] = old_state.get("auto_terms") or {}
    core.save_job_state(new_job, state)

    # 复用译文注入翻译记忆（标记 reviewed，translate_stage 精确命中直接用）
    tm = core.load_tm()
    for j, tgt in reused.items():
        tm[new_paras[j].replace("\n", " ")] = {"target": tgt, "reviewed": True}
    core.save_tm(tm)

    glossary = core.normalize_glossary(
        [{"source": k, "target": v, "behavior": "translate", "status": "provisional"}
         for k, v in state["auto_terms"].items()])
    core.translate_stage(state, new_job, glossary, args.provider, api_key, args.model,
                         args.target_lang, style_rules="", enable_review=args.review,
                         on_status=lambda m: print(f"  {m}"),
                         on_caption=lambda m: print(f"  {m}"))
    state["p2_done"] = True
    core.save_job_state(new_job, state)

    print("【4/4】完成。state 保存在 outputs/" + new_job)
    print(json.dumps(state["review_stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
