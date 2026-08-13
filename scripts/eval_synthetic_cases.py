"""Run Synthetic Contrast Case generation on a saved job without mutating it."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from mti_tool import academic_evidence, academic_writer, synthetic_cases


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--provider", default="OpenCode Go")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--model", default="glm-5.2")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-scan", type=int, default=16)
    parser.add_argument("--max-opportunities", type=int, default=8)
    parser.add_argument("--case-limit", type=int, default=5)
    args = parser.parse_args()
    env_key = {
        "DeepSeek": "DEEPSEEK_API_KEY",
        "OpenCode Go": "OPENCODE_GO_API_KEY",
        "OpenAI": "OPENAI_API_KEY",
        "Gemini": "GEMINI_API_KEY",
    }.get(args.provider, "MTI_API_KEY")
    api_key = args.api_key or os.environ.get(env_key) or os.environ.get(
        "MTI_API_KEY") or getpass.getpass("Provider API key: ")
    if not api_key:
        parser.error("API key is required")

    state_path = Path("outputs") / args.job_id / "state.json"
    out_dir = Path(args.out_dir)
    if not state_path.is_file():
        parser.error(f"state not found: {state_path}")
    if out_dir.exists():
        parser.error("out-dir already exists; use a new isolated directory")
    out_dir.mkdir(parents=True)

    before_hash = _sha256(state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    evidence = academic_evidence.build_academic_evidence(state, args.job_id)
    opportunities = synthetic_cases.mine_error_opportunities(
        evidence, core.call_llm, args.provider, api_key, args.model,
        args.max_scan, args.max_opportunities)
    baselines = synthetic_cases.generate_baselines(
        opportunities, core.call_llm, args.provider, api_key, args.model)
    manifest = synthetic_cases.build_error_manifest(
        baselines, core.call_llm, args.provider, api_key, args.model)
    optimized = synthetic_cases.optimize_translations(
        manifest, core.call_llm, args.provider, api_key, args.model,
        evidence.get("project_evidence", {}).get("glossary", []))
    validation = synthetic_cases.validate_synthetic_cases(
        optimized, core.call_llm, args.provider, api_key, args.model, evidence)
    selected = academic_writer.select_academic_cases(
        {}, {"claims": []}, evidence, limit=args.case_limit,
        synthetic_artifact=validation, policy="mixed")
    after_hash = _sha256(state_path)
    state_unchanged = before_hash == after_hash
    run_status = validation.get("pipeline_status", "complete")
    if not state_unchanged:
        run_status = "failed"

    artifacts = {
        "synthetic-error-opportunities.jsonl": opportunities,
        "synthetic-baselines.jsonl": baselines,
        "synthetic-error-manifest.jsonl": manifest,
        "synthetic-optimized-translations.jsonl": optimized,
        "synthetic-case-validation.jsonl": validation,
    }
    for filename, artifact in artifacts.items():
        academic_writer._write_artifact(out_dir / filename, artifact)
    _write_json(out_dir / "selected-cases.json", selected)

    selected_synthetic = [x for x in selected["cases"]
                          if x.get("case_type") == "synthetic_contrast"]
    rejected = [x for x in validation.get("items", [])
                if not x.get("validation", {}).get("academic_case_eligible")]
    metrics = {
        "total_source_segments_scanned": opportunities.get("total_source_segments", 0),
        "screened_for_difficulty": opportunities.get("screened_segments", 0),
        "difficulty_opportunities_found": opportunities.get("opportunities_found", 0),
        **(validation.get("metrics") or {}),
    }
    pipeline_error = str(opportunities.get("model_call_error") or
                         validation.get("model_call_error") or "")
    lines = [
        "# Synthetic Contrast Case Evaluation",
        "",
        f"- job: `{args.job_id}`",
        f"- authentic cases retained: {', '.join(x['case_id'].rsplit('-', 1)[-1] for x in selected['cases'] if x.get('case_type') == 'authentic_revision') or 'none'}",
        f"- synthetic cases selected: {len(selected_synthetic)}",
        f"- synthetic pipeline status: `{run_status}`",
        f"- historical state modified: {'no' if state_unchanged else 'yes'}",
        "",
    ]
    if run_status == "failed":
        lines.extend([
            "## Run failure", "",
            f"- Provider/stage error: {pipeline_error or 'unknown provider/stage failure'}",
            "- Interpretation: no candidate verdict is available; zero opportunities is not "
            "a corpus or eligibility conclusion.", "",
        ])
    lines.extend(["## Run metrics", ""])
    lines.extend(f"- {key}: {value}" for key, value in metrics.items())
    lines.extend(["", "## Selected synthetic cases", ""])
    if not selected_synthetic:
        lines.append("None selected; the pipeline failed before eligibility decisions."
                     if run_status == "failed" else "None selected.")
    for case in selected_synthetic:
        lines.extend([
            f"### {case['case_id']}", "",
            f"- Source: {case.get('source_text', '')}",
            f"- Difficulty: {(case.get('difficulty') or {}).get('reason', '')}",
            f"- Synthetic Initial Translation: {(case.get('synthetic_baseline') or {}).get('text', '')}",
            f"- Why It Is Plausible: {(case.get('baseline_plausibility') or {}).get('reason', '')}",
            f"- Error Diagnosis: {(case.get('error') or {}).get('diagnosis', '')}",
            f"- Optimized Translation: {(case.get('optimized_translation') or {}).get('text', '')}",
            f"- Actual Delta: {json.dumps(case.get('actual_delta') or {}, ensure_ascii=False)}",
            f"- Repair Validation: {(case.get('validation') or {}).get('reason', '')}",
            f"- Academic Value: {(case.get('difficulty') or {}).get('academic_value', '')}",
            f"- Theory Potential: {case.get('theory_potential', '')}",
            f"- Limitations: {'; '.join(case.get('limitations') or [])}", "",
        ])
    lines.extend(["## Rejected synthetic cases", ""])
    if not rejected:
        lines.append("No rejection decisions were produced because the pipeline failed."
                     if run_status == "failed" else "None.")
    for case in rejected:
        if case.get("baseline_plausibility", {}).get("status") != "plausible":
            reason = "baseline_implausible"
        elif case.get("error", {}).get("baseline_already_adequate"):
            reason = "baseline_already_adequate"
        elif case.get("error", {}).get("materiality") not in {"major", "moderate"}:
            reason = "error_non_material"
        elif case.get("optimized_translation", {}).get(
                "generation_status") != "generated":
            reason = "optimization_not_generated"
        else:
            reason = ", ".join((case.get("validation") or {}).get(
                "rejected_reasons") or ["not eligible"])
        lines.append(f"- {case['case_id']}: {reason}")
    lines.extend([
        "", "## Authentic / synthetic comparison", "",
        "| Dimension | Authentic revisions 0209/0272 | Synthetic contrasts |",
        "|---|---|---|",
        "| Evidence provenance | Saved historical initial/final evidence | Analysis-generated baseline and AI optimization |",
        "| Analysis strength | Direct evidence of an actual change; rationale may be missing | Clear controlled error/repair mechanism after validation |",
        "| Historical process claims | Supported only to the extent recorded | Not supported |",
        "| Error and repair clarity | Depends on surviving project records | Explicitly constructed and independently checked |",
        "| Theory use | Requires grounded Literature Evidence | Also requires grounded Literature Evidence |",
        "| Limitation | Sparse process rationale | No empirical human-error frequency inference |",
        "", "The two case types are complementary. Synthetic cases broaden mechanism analysis but do not become revision history.",
    ])
    (out_dir / "synthetic-case-evaluation-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    run = {
        "job_id": args.job_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": args.provider,
        "model": args.model,
        "versions": {key: value for key, value in academic_writer.VERSIONS.items()
                     if key.startswith("synthetic_") or key == "case_selection_version"},
        "metrics": metrics,
        "status": run_status,
        "pipeline_error": pipeline_error,
        "state_sha256_before": before_hash,
        "state_sha256_after": after_hash,
        "historical_state_unchanged": state_unchanged,
        "selected_authentic_cases": [x["case_id"] for x in selected["cases"]
                                      if x.get("case_type") == "authentic_revision"],
        "selected_synthetic_cases": [x["case_id"] for x in selected_synthetic],
    }
    _write_json(out_dir / "run-manifest.json", run)
    print(out_dir)
    return 0 if run_status == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
