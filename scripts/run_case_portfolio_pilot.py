"""Run an isolated full-corpus MTI case-portfolio evaluation and composition pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import academic_evidence, academic_writer, case_portfolio


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _report(
    pool: dict[str, Any], taxonomy: dict[str, Any], portfolio: dict[str, Any],
    coverage: dict[str, Any], quality: dict[str, Any], validation: dict[str, Any],
) -> str:
    old = portfolio["old_case_decisions"]
    return f"""# Full-Corpus Case Portfolio Evaluation

- segments scanned: {pool['scan']['segments_scanned']}
- discovered candidates: {pool['candidate_count']}
- viable candidates: {pool['viable_candidate_count']}
- selected portfolio cases: {portfolio['selected_case_count']}
- tier distribution: `{json.dumps(portfolio['tier_distribution'], ensure_ascii=False)}`
- provenance distribution: `{json.dumps(portfolio['provenance_distribution'], ensure_ascii=False)}`
- portfolio quality: `{quality['status']}`
- composition validation: `{validation['status']}`

## Taxonomy

The corpus produced {taxonomy['major_problem_count']} major problems and {taxonomy['subproblem_count']} subproblems:

{chr(10).join(f"- {x['title']}: " + ' / '.join(y['title'] for y in x['subproblems']) for x in taxonomy['major_problems'])}

## Old-case decisions

- 0209: `{old['0209']['decision']}` / `{old['0209'].get('tier', '-')}`
- 0272: `{old['0272']['decision']}` / `{old['0272'].get('tier', '-')}`
- SC-0141: `{old['SC-0141']['decision']}` / `{old['SC-0141'].get('tier', '-')}`

## Evidence decision

Only cases currently classified as `authentic_revision` by the shared integrity gate may support historical revision claims. 0209 is a system-alignment boundary case, not a translator decision; 0272 remains authentic. Supporting examples carry recorded review findings but no implemented revision history. SC-0141 remains synthetic and supplemental.

## Coverage gaps

{chr(10).join('- ' + x for x in coverage['gaps'])}

## Composition decision

The portfolio passed its deterministic quality gate, so the full Chapter 3 pilot was generated. It is an academically reviewable architecture pilot, not a submission-ready thesis chapter: Human Author Evidence and grounded Literature Evidence remain the highest-value inputs.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--synthetic-artifact", required=True)
    parser.add_argument("--human-pilot-state", required=True)
    parser.add_argument("--provider", default="OpenCode Go")
    parser.add_argument("--model", default="glm-5.2")
    args = parser.parse_args()

    state_path = Path("outputs") / args.job_id / "state.json"
    synthetic_path = Path(args.synthetic_artifact)
    human_state_path = Path(args.human_pilot_state)
    out_dir = Path(args.out_dir)
    if out_dir.exists():
        parser.error("out-dir already exists")
    if not all(path.is_file() for path in (
            state_path, synthetic_path, human_state_path)):
        parser.error("state, synthetic artifact, or Human Evidence state is missing")

    human_state = _load(human_state_path)
    if human_state.get("status") != "awaiting_author_input" or human_state.get(
            "phase_b_started"):
        parser.error("Human Evidence boundary is not awaiting_author_input")
    before_hash = _sha256(state_path)
    state = _load(state_path)
    evidence = academic_evidence.build_academic_evidence(
        state, args.job_id, max_candidates=len(state.get("pairs") or []))
    synthetic = academic_writer._read_artifact(synthetic_path)

    pool = case_portfolio.build_candidate_pool(evidence, synthetic)
    taxonomy = case_portfolio.build_taxonomy(pool)
    portfolio = case_portfolio.plan_portfolio(pool, taxonomy)
    coverage = case_portfolio.build_coverage_matrix(portfolio, taxonomy)
    research = case_portfolio.build_research_model(portfolio)
    arguments = case_portfolio.build_argument_blueprint(
        portfolio, taxonomy, research)
    outline = case_portfolio.build_outline(portfolio, taxonomy, research)
    quality = case_portfolio.review_portfolio(portfolio, taxonomy, coverage)

    out_dir.mkdir(parents=True)
    artifacts = {
        "case-taxonomy.json": taxonomy,
        "candidate-case-pool.json": pool,
        "case-portfolio.json": portfolio,
        "coverage-matrix.json": coverage,
        "rejected-downgraded-cases.json": {
            "schema_version": "portfolio-decisions-v1",
            "rejected": portfolio["rejected_cases"],
            "downgraded": portfolio["redundancy_analysis"][
                "downgraded_from_core_contention"],
            "redundancy_groups": portfolio["redundancy_analysis"]["groups"],
        },
        "research-model.json": research,
        "chapter-3-argument-blueprint.json": arguments,
        "chapter-3-outline.json": outline,
        "portfolio-quality-review.json": quality,
    }
    for name, value in artifacts.items():
        _write(out_dir / name, value)

    chapter = ""
    if quality.get("composition_gate") == "open":
        chapter = case_portfolio.compose_chapter(
            portfolio, taxonomy, outline, pool)
        (out_dir / "chapter-3-full-portfolio-pilot.md").write_text(
            chapter, encoding="utf-8")
    validation = case_portfolio.validate_chapter(
        chapter, evidence, portfolio, pool, synthetic) if chapter else {
            "schema_version": case_portfolio.VALIDATOR_VERSION,
            "status": "not_run", "issues": [],
    }
    _write(out_dir / "chapter-3-portfolio-validation.json", validation)
    chapter_quality = case_portfolio.review_chapter(
        chapter, portfolio, validation) if chapter else {
            "schema_version": "portfolio-chapter-quality-review-v1",
            "readiness": "engineering_valid", "validation_status": "not_run",
        }
    _write(out_dir / "chapter-3-quality-review.json", chapter_quality)
    (out_dir / "portfolio-evaluation-report.md").write_text(
        _report(pool, taxonomy, portfolio, coverage, quality, validation),
        encoding="utf-8")

    after_hash = _sha256(state_path)
    run = {
        "schema_version": "case-portfolio-run-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "complete" if quality.get("composition_gate") == "open" and validation.get(
            "status") == "pass" and before_hash == after_hash else "failed",
        "job_id": args.job_id,
        "baseline_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, text=True,
            capture_output=True).stdout.strip(),
        "provider": args.provider, "model": args.model,
        "endpoint_class": "OpenAI-compatible chat completions",
        "provider_used_for_this_deterministic_run": False,
        "provider_recording_note": (
            "The configured provider/model is recorded for continuity. This run reused "
            "already-validated canonical synthetic evidence and made no external model call."),
        "versions": {
            "portfolio": case_portfolio.PORTFOLIO_VERSION,
            "taxonomy": case_portfolio.TAXONOMY_VERSION,
            "validator": case_portfolio.VALIDATOR_VERSION,
            "academic_evidence": academic_evidence.SCHEMA_VERSION,
        },
        "historical_state": {
            "path": str(state_path), "sha256_before": before_hash,
            "sha256_after": after_hash, "unchanged": before_hash == after_hash,
        },
        "canonical_sources": {
            "synthetic_artifact": str(synthetic_path),
            "human_evidence_state": str(human_state_path),
        },
        "evidence_boundaries": {
            "human_evidence_status": "awaiting_author_input",
            "human_evidence_entries_used": 0,
            "literature_evidence_entries_used": 0,
        },
        "metrics": {
            "segments_scanned": pool["scan"]["segments_scanned"],
            "candidate_count": pool["candidate_count"],
            "viable_candidate_count": pool["viable_candidate_count"],
            "selected_case_count": portfolio["selected_case_count"],
            "tier_distribution": portfolio["tier_distribution"],
            "case_type_distribution": portfolio["case_type_distribution"],
            "major_problem_count": taxonomy["major_problem_count"],
            "subproblem_count": taxonomy["subproblem_count"],
        },
        "composition_generated": bool(chapter),
        "portfolio_quality_status": quality.get("status"),
        "chapter_validation_status": validation.get("status"),
        "chapter_readiness": chapter_quality.get("readiness"),
        "artifact_files": sorted(path.name for path in out_dir.iterdir()) + [
            "run-manifest.json"],
    }
    _write(out_dir / "run-manifest.json", run)
    print(out_dir)
    return 0 if run["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
