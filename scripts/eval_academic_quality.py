"""Run the full academic pipeline on a real saved job in an isolated namespace.

Reads the saved job state read-only (deep copy), runs the complete
evidence-grounded pipeline including academic quality evaluation and bounded
structural repair, and writes all artifacts plus a reproducibility manifest to
an isolated output directory.  It never writes back to the original job state.

Usage:
    .venv/bin/python scripts/eval_academic_quality.py \
        --job-id ec100d8686d3891e \
        --theory "功能对等理论" \
        --research-questions "如何解释?" --research-questions "如何评价?" \
        --provider DeepSeek --api-key sk-... --model deepseek-chat \
        --out-dir eval/academic-quality/ec100d8686d3891e
"""
from __future__ import annotations

import argparse
import copy
import getpass
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from mti_tool import academic_evidence, academic_writer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--theory", default="功能对等理论")
    parser.add_argument("--research-questions", action="append", default=[])
    parser.add_argument("--provider", default="OpenCode Go")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--model", default="glm-5.2")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--resume", action="store_true",
                        help="Resume from an existing state-eval.json in out-dir "
                             "instead of re-copying the source job state.")
    parser.add_argument("--literature-json", default="")
    parser.add_argument("--tag", default="eval")
    parser.add_argument("--quality-rounds", type=int, default=1)
    args = parser.parse_args()
    env_key = {"OpenCode Go": "OPENCODE_GO_API_KEY",
               "DeepSeek": "DEEPSEEK_API_KEY", "OpenAI": "OPENAI_API_KEY",
               "Gemini": "GEMINI_API_KEY"}.get(args.provider, "MTI_API_KEY")
    args.api_key = args.api_key or os.environ.get(env_key) or os.environ.get(
        "MTI_API_KEY") or getpass.getpass("Provider API key: ")
    if not args.api_key:
        parser.error("API key is required")

    source_state_path = Path("outputs") / args.job_id / "state.json"
    if not source_state_path.is_file():
        print(f"state not found: {source_state_path}", file=sys.stderr)
        return 2
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    resume_state_path = out_dir / "state-eval.json"
    if args.resume and resume_state_path.is_file():
        state = json.loads(resume_state_path.read_text(encoding="utf-8"))
        print(f"resuming from {resume_state_path}")
    else:
        original = json.loads(source_state_path.read_text(encoding="utf-8"))
        state = copy.deepcopy(original)
    segments = len(state.get("pairs") or [])
    print(f"job={args.job_id} segments={segments} "
          f"findings={len(state.get('findings') or [])} "
          f"glossary={len(state.get('glossary') or [])} "
          f"literature={len(state.get('literature_sources') or [])}")

    if not args.resume:
        out_dir = out_dir / f"{args.tag}-{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    literature = []
    if args.literature_json:
        raw = json.loads(Path(args.literature_json).read_text(encoding="utf-8"))
        literature = raw.get("sources") or raw.get("literature_sources") or []

    research_settings = {}
    if args.research_questions:
        research_settings["research_questions"] = args.research_questions

    def save_state(current) -> None:
        (out_dir / "state-eval.json").write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md = academic_writer.run_academic_pipeline(
        state, args.job_id, args.theory, args.provider, args.api_key, args.model,
        artifact_dir=out_dir, call_llm=core.call_llm, save_state=save_state,
        research_settings=research_settings, literature_sources=literature,
        on_status=lambda label: print(label, flush=True),
        auto_repair_rounds=1, auto_quality_repair_rounds=args.quality_rounds)

    (out_dir / "report-final.md").write_text(report_md, encoding="utf-8")
    docx = core.markdown_to_word(report_md, args.theory).getvalue()
    (out_dir / "report-final.docx").write_bytes(docx)

    artifact_names = list(academic_writer.ARTIFACT_FILES)
    hashes = {}
    for name in artifact_names:
        value = academic_writer._read_artifact(out_dir / academic_writer.ARTIFACT_FILES[name])
        hashes[name] = (value or {}).get("content_hash")
    quality = academic_writer._read_artifact(
        out_dir / academic_writer.ARTIFACT_FILES["academic_quality"]) or {}
    manifest = {
        "job_id": args.job_id,
        "state_source": str(source_state_path),
        "isolated_output": str(out_dir),
        "timestamp": timestamp,
        "segments": segments,
        "provider": args.provider,
        "model": args.model,
        "theory": args.theory,
        "research_settings": research_settings,
        "pipeline_version": academic_writer.PIPELINE_VERSION,
        "versions": dict(academic_writer.VERSIONS),
        "artifact_hashes": hashes,
        "report_md_hash": academic_evidence.stable_hash(report_md),
        "quality_summary": {
            "dimensions": quality.get("dimensions"),
            "metrics": quality.get("metrics"),
            "finding_count": len(quality.get("findings") or []),
        },
    }
    (out_dir / "run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nrun complete -> {out_dir}")
    print("dimensions:", json.dumps(quality.get("dimensions"), ensure_ascii=False))
    metrics = quality.get("metrics") or {}
    print("metrics:", json.dumps(
        {k: v for k, v in metrics.items()
         if k not in ("paragraph_roles", "evidence_utilization")},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
