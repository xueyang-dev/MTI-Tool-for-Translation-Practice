"""命令行翻译器：使用 TransPraxis / 译践 核心流水线翻译 PDF/DOCX（含批次翻译、确定性检查、独立审校、翻译记忆）。

用法：
  # 环境变量提供 API Key（DeepSeek/OpenCode Go/OpenAI/Gemini 任一）
  export TRANSPRAXIS_API_KEY=sk-xxx
  # 翻译整个文档
  python scripts/translate_pdf.py "文档.pdf" --target-lang 简体中文
  # 只翻译前 40 页
  python scripts/translate_pdf.py "文档.pdf" --pages 1-40
  # 关闭审校（更快，但无翻译记忆与质量保障）
  python scripts/translate_pdf.py "文档.pdf" --no-review

结果输出到 --out 目录（默认 ~/Downloads/TransPraxis-翻译输出/）：
  阶段1_清洗原文.docx / 阶段2_双语对照.docx / 审查报告.md
任务进度保存在项目 outputs/ 目录，中断后重新运行同一条命令即可继续。
"""
import argparse
import hashlib
import io
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz

import core


def resolve_key_and_model(provider, model):
    env_keys = {
        "DeepSeek": ("TRANSPRAXIS_API_KEY", "DEEPSEEK_API_KEY"),
        "OpenCode Go": ("TRANSPRAXIS_API_KEY", "OPENCODE_GO_API_KEY"),
        "OpenAI": ("TRANSPRAXIS_API_KEY", "OPENAI_API_KEY"),
        "Gemini": ("TRANSPRAXIS_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"),
    }
    key = next((os.environ.get(k) for k in env_keys.get(provider, ["TRANSPRAXIS_API_KEY"])
                if os.environ.get(k)), None)
    if not key:
        raise SystemExit(
            f"未找到 {provider} API Key。请先设置环境变量，例如：\n"
            f"  export TRANSPRAXIS_API_KEY=你的Key\n"
            f"（或 DEEPSEEK_API_KEY / OPENCODE_GO_API_KEY / OPENAI_API_KEY / "
            f"GEMINI_API_KEY）")
    if not model:
        model = core.MODELS[provider][0]
    return key, model


def load_document(path, pages=None):
    """读取 PDF/DOCX；--pages 仅对 PDF 生效（按页裁剪）。返回 (filename, bytes, stable_job_id)。"""
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"文件不存在：{path}")
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if pages and path.suffix.lower() == ".pdf":
        start, end = (int(x) for x in pages.split("-"))
        doc = fitz.open(path)
        buf = io.BytesIO()
        with fitz.open() as out:
            out.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
            out.save(buf)
        doc.close()
        print(f"已裁剪第 {start}-{end} 页（共 {end - start + 1} 页）")
        # 用「原文件哈希 + 页码范围」生成稳定任务 ID：每次裁剪字节可能不同，但任务必须可续传
        job_id = hashlib.sha256(f"{original_hash}::pages::{start}-{end}".encode()).hexdigest()[:16]
        return path.name, buf.getvalue(), job_id
    job_id = original_hash[:16]
    return path.name, path.read_bytes(), job_id


def main():
    ap = argparse.ArgumentParser(description="TransPraxis / 译践 命令行翻译器")
    ap.add_argument("document", help="PDF 或 DOCX 路径")
    ap.add_argument("--provider", default="OpenCode Go", choices=list(core.MODELS))
    ap.add_argument("--model", default=None, help="默认取该 provider 第一个模型")
    ap.add_argument("--target-lang", default="简体中文",
                    choices=["简体中文", "English", "日本語"])
    ap.add_argument("--pages", default=None, help="仅 PDF：如 1-40，默认全部")
    ap.add_argument("--out", default=str(Path.home() / "Downloads" / "TransPraxis-翻译输出"))
    ap.add_argument("--no-review", action="store_true", help="关闭独立审校与翻译记忆")
    ap.add_argument("--no-report", action="store_true", help="不生成实践报告（默认生成）")
    ap.add_argument("--no-annotate", action="store_true",
                    help="关闭三色自动标注（生僻词/专业名词/难点句高亮，默认开启）")
    ap.add_argument("--quality", action="store_true",
                    help="开启严格术语治理（文档画像→候选术语审核冻结）；"
                         "审校、标注与报告由各自选项控制")
    ap.add_argument("--job-id", default=None, help="续跑指定任务 ID（跳过自动计算）")
    args = ap.parse_args()

    api_key, model = resolve_key_and_model(args.provider, args.model)
    filename, file_bytes, auto_job_id = load_document(args.document, args.pages)
    job_id = args.job_id or auto_job_id

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"▶ 开始处理：{filename}（{len(file_bytes) / 1024:.0f} KB，provider={args.provider}，"
          f"model={model}，review={'开' if not args.no_review else '关'}）")

    def on_status(label):
        print(f"[{time.strftime('%H:%M:%S')}] {label}")

    def on_caption(text):
        print(f"    · {text}")

    state = core.load_job_state(job_id)
    if state:
        print(f"ℹ 任务 {job_id} 已有进度（{core.progress_label(state)}），继续执行…")
    else:
        print(f"ℹ 新任务 ID：{job_id}")

    state = core.run_job_pipeline(
        job_id, filename, file_bytes,
        provider=args.provider, api_key=api_key, model=model,
        target_lang=args.target_lang, auto_term=True,
        enable_report=not args.no_report,
        translation_theory="目的论 (Skopos Theory)",
        user_glossary=[], style_rules="保持学术书面语与叙事风格；人名、地名、机构名、飞机型号、"
                                      "引用标注、URL 保留原文；标点遵循中文规范。",
        enable_review=not args.no_review,
        enable_annotate=not args.no_annotate,
        strict_terminology_governance=args.quality,
        on_status=on_status, on_caption=on_caption,
    )

    # 导出产物
    if state.get("p1_done"):
        (out_dir / "阶段1_清洗原文.docx").write_bytes(
            core.paragraphs_to_word(state["paras"]).getvalue())
    if state.get("p2_done") and state.get("pairs"):
        (out_dir / "阶段2_双语对照.docx").write_bytes(
            core.pairs_to_word(state["pairs"],
                               annotations=state.get("annotations")).getvalue())
    if state.get("p3_md"):
        (out_dir / "阶段3_实践报告.md").write_text(state["p3_md"], encoding="utf-8")
    (out_dir / "审查报告.md").write_text(core.findings_report_md(state), encoding="utf-8")
    (out_dir / "自动抽词库.xlsx").write_bytes(
        core.dict_to_excel(state.get("auto_terms") or {}).getvalue())

    stats = state.get("review_stats") or {}
    print(f"\n✔ 处理完成，用时 {(time.time() - t0) / 60:.1f} 分钟")
    print(f"  段落：{len(state.get('paras') or [])} · 译文：{len(state.get('pairs') or [])} 段")
    print(f"  审校：{stats.get('reviewed_segments', 0)} 段通过 · "
          f"blocking {stats.get('blocking', 0)} · actionable {stats.get('actionable', 0)} · "
          f"informational {stats.get('informational', 0)}")
    print(f"  翻译记忆复用：{state.get('tm_used_count', 0)} 段")
    if state.get("findings"):
        print("  ⚠ 存在待处理问题，详见审查报告。")
    print(f"  输出目录：{out_dir}")


if __name__ == "__main__":
    main()
