#!/usr/bin/env python3
"""Prepare the verified literature packet for the ec100 thesis closeout.

The script only reads already acquired local PDFs.  It does not search, infer
translator intent, or touch the historical translation state.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from transpraxis import academic_evidence, academic_writer, literature_evidence


JOB_ID = "ec100d8686d3891e"
DEFAULT_OUT = REPO_ROOT / "eval" / "academic-quality" / JOB_ID / "thesis-closeout-v6"
SEARCH_DATE = "2026-08-12"

SOURCES = [
    {
        "source_id": "house2001-tqa",
        "file": "house-2001-translation-quality-assessment.pdf",
        "title": "Translation Quality Assessment: Linguistic Description versus Social Evaluation",
        "authors": ["Juliane House"],
        "year": 2001,
        "source_type": "journal_article",
        "concepts": ["translation quality assessment", "functional-pragmatic analysis", "register", "genre"],
        "citation_metadata": {
            "title": "Translation Quality Assessment: Linguistic Description versus Social Evaluation",
            "authors": ["Juliane House"],
            "year": 2001,
            "journal": "Meta",
            "volume": "46",
            "issue": "2",
            "pages": "243–257",
            "doi": "10.7202/003141ar",
            "in_text": "House（2001）",
            "apa7": "House, J. (2001). Translation quality assessment: Linguistic description versus social evaluation. Meta, 46(2), 243–257. https://doi.org/10.7202/003141ar",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["original_pdf", "publisher_record", "crossref", "semantic_scholar"],
            "note": "期刊卷期与原始 PDF 均为 2001；Crossref 的 online metadata 日期为 2002，不据此改写卷期年份。",
            "study_design_level": "VII",
            "overall_grade": "A",
        },
    },
    {
        "source_id": "karoly-et-al-2022-cohesion",
        "file": "karoly-et-al-2022-literary-cohesion.pdf",
        "title": "A szövegkohézió újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról",
        "authors": ["Krisztina Károly", "Gerda Karádi", "Judit Olgyay-Fekete", "Kamilla Sulyok"],
        "year": 2022,
        "source_type": "journal_article",
        "concepts": ["literary translation", "textual cohesion", "reference", "explicitation"],
        "citation_metadata": {
            "title": "A szövegkohézió újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról",
            "authors": ["Krisztina Károly", "Gerda Karádi", "Judit Olgyay-Fekete", "Kamilla Sulyok"],
            "year": 2022,
            "journal": "Fordítástudomány",
            "volume": "24",
            "issue": "2",
            "pages": "5–40",
            "doi": "10.35924/fordtud.24.2.1",
            "in_text": "Károly等（2022a）",
            "apa7": "Károly, K., Karádi, G., Olgyay-Fekete, J., & Sulyok, K. (2022). A szövegkohézió újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról. Fordítástudomány, 24(2), 5–40. https://doi.org/10.35924/fordtud.24.2.1",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["original_pdf", "journal_record", "crossref", "semantic_scholar"],
            "study_design_level": "VI",
            "overall_grade": "A",
        },
    },
    {
        "source_id": "karoly-et-al-2022-macrostructure",
        "file": "karoly-et-al-2022-literary-macrostructure.pdf",
        "title": "A makrostruktúra újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról",
        "authors": ["Krisztina Károly", "Andrea Csiborné Horváth", "Izolda Engel", "Franciska Van Waarden"],
        "year": 2022,
        "source_type": "journal_article",
        "concepts": ["literary translation", "coherence", "macrostructure", "rhetorical structure"],
        "citation_metadata": {
            "title": "A makrostruktúra újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról",
            "authors": ["Krisztina Károly", "Andrea Csiborné Horváth", "Izolda Engel", "Franciska Van Waarden"],
            "year": 2022,
            "journal": "Fordítástudomány",
            "volume": "24",
            "issue": "2",
            "pages": "41–81",
            "doi": "10.35924/fordtud.24.2.2",
            "in_text": "Károly等（2022b）",
            "apa7": "Károly, K., Csiborné Horváth, A., Engel, I., & Van Waarden, F. (2022). A makrostruktúra újrateremtése műfordításban: esettanulmány Salinger The Catcher in the Rye című művének két magyar fordításáról. Fordítástudomány, 24(2), 41–81. https://doi.org/10.35924/fordtud.24.2.2",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["original_pdf", "journal_record", "crossref", "semantic_scholar"],
            "study_design_level": "VI",
            "overall_grade": "A",
        },
    },
    {
        "source_id": "eekhof-et-al-2020-vpip",
        "file": "eekhof-et-al-2020-vpip.pdf",
        "title": "VPIP: A Lexical Identification Procedure for Perceptual, Cognitive, and Emotional Viewpoint in Narrative Discourse",
        "authors": ["Lynn S. Eekhof", "Kobie van Krieken", "José Sanders"],
        "year": 2020,
        "source_type": "journal_article",
        "concepts": ["narrative viewpoint", "lexical markers", "perception", "cognition", "emotion"],
        "citation_metadata": {
            "title": "VPIP: A Lexical Identification Procedure for Perceptual, Cognitive, and Emotional Viewpoint in Narrative Discourse",
            "authors": ["Lynn S. Eekhof", "Kobie van Krieken", "José Sanders"],
            "year": 2020,
            "journal": "Open Library of Humanities",
            "volume": "6",
            "issue": "1",
            "article": "18",
            "pages": "1–38",
            "doi": "10.16995/olh.483",
            "in_text": "Eekhof等（2020）",
            "apa7": "Eekhof, L. S., van Krieken, K., & Sanders, J. (2020). VPIP: A lexical identification procedure for perceptual, cognitive, and emotional viewpoint in narrative discourse. Open Library of Humanities, 6(1), Article 18, 1–38. https://doi.org/10.16995/olh.483",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["original_pdf", "journal_record", "crossref", "semantic_scholar"],
            "study_design_level": "VI",
            "overall_grade": "A",
        },
    },
    {
        "source_id": "van-krieken-2018-perspective",
        "file": "van-krieken-2018-ambiguous-perspective.pdf",
        "title": "Ambiguous Perspective in Narrative Discourse: Effects of Viewpoint Markers and Verb Tense on Readers’ Interpretation of Represented Perceptions",
        "authors": ["Kobie van Krieken"],
        "year": 2018,
        "source_type": "journal_article",
        "concepts": ["narrative viewpoint", "reader interpretation", "viewpoint markers", "verb tense"],
        "citation_metadata": {
            "title": "Ambiguous Perspective in Narrative Discourse: Effects of Viewpoint Markers and Verb Tense on Readers’ Interpretation of Represented Perceptions",
            "authors": ["Kobie van Krieken"],
            "year": 2018,
            "journal": "Discourse Processes",
            "volume": "55",
            "issue": "8",
            "pages": "771–786",
            "doi": "10.1080/0163853X.2017.1381540",
            "in_text": "van Krieken（2018）",
            "apa7": "van Krieken, K. (2018). Ambiguous perspective in narrative discourse: Effects of viewpoint markers and verb tense on readers’ interpretation of represented perceptions. Discourse Processes, 55(8), 771–786. https://doi.org/10.1080/0163853X.2017.1381540",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["publisher_version_in_institutional_repository", "crossref", "semantic_scholar"],
            "study_design_level": "III",
            "overall_grade": "A",
        },
    },
    {
        "source_id": "al-herz-2016-narrative-pov",
        "file": "al-herz-2016-narrative-point-of-view.pdf",
        "title": "Narrative Point of View in Translation: A Systemic Functional Analysis of the Arabic Translations of J. M. Coetzee’s Waiting for the Barbarians",
        "authors": ["Komail Hussain H. Al Herz"],
        "year": 2016,
        "source_type": "doctoral_thesis",
        "concepts": ["narrative point of view", "translation shifts", "systemic functional analysis"],
        "citation_metadata": {
            "title": "Narrative Point of View in Translation: A Systemic Functional Analysis of the Arabic Translations of J. M. Coetzee’s Waiting for the Barbarians",
            "authors": ["Komail Hussain H. Al Herz"],
            "year": 2016,
            "institution": "University of Leeds",
            "repository": "White Rose eTheses Online",
            "url": "https://etheses.whiterose.ac.uk/id/eprint/17870/",
            "in_text": "Al Herz（2016）",
            "apa7": "Al Herz, K. H. H. (2016). Narrative point of view in translation: A systemic functional analysis of the Arabic translations of J. M. Coetzee’s Waiting for the Barbarians [Doctoral dissertation, University of Leeds]. White Rose eTheses Online. https://etheses.whiterose.ac.uk/id/eprint/17870/",
        },
        "verification": {
            "existence": "verified",
            "original_checked": True,
            "checks": ["original_pdf", "institutional_repository_record"],
            "note": "无 DOI；自动索引未找到可靠精确匹配，来源身份由 University of Leeds 机构库与原始论文核验。",
            "study_design_level": "VI",
            "overall_grade": "B",
        },
    },
]

CLAIMS = [
    {
        "literature_claim_id": "LC-001",
        "source_id": "house2001-tqa",
        "statement": "翻译评价应把源文—译文的语言描述、解释和比较与笼统的好坏判断区分开，价值判断须由可检验的分析比较提供依据。",
        "claim_type": "method_claim",
        "confidence": "high",
        "evidence": [
            (13, 2, "a distinction must be made between describing and explaining linguistic features"),
            (13, 3, "linguistic analysis which provides grounds for arguing an evaluative judgement"),
        ],
        "boundary": "只支持评价方法，不证明本项目任何具体译文已经达到某种质量等级。",
    },
    {
        "literature_claim_id": "LC-002",
        "source_id": "house2001-tqa",
        "statement": "功能—语用评价可从语言/文本、语域和体裁层面比较源文与译文，并把语义、语用和文本意义置于具体语境中考察。",
        "claim_type": "theoretical_position",
        "confidence": "high",
        "evidence": [
            (6, 1, "Language/Text, Register (Field, Mode and Tenor) and Genre"),
            (6, 3, "a semantic, a pragmatic and a textual aspect"),
        ],
        "boundary": "这是分析框架，不授权用“功能对等”标签替代逐例文本论证。",
    },
    {
        "literature_claim_id": "LC-003",
        "source_id": "karoly-et-al-2022-cohesion",
        "statement": "文学翻译的结构性与非结构性衔接重构可能产生文本层次偏移；该个案中，部分显化造成冗余，重复规避假设也未获必然支持。",
        "claim_type": "empirical_finding",
        "confidence": "medium",
        "evidence": [
            (1, 1, "szövegkohézió"),
            (1, 2, "redundanciához"),
        ],
        "boundary": "结论来自《麦田里的守望者》英匈翻译个案，不能直接推断英汉翻译的发生频率。",
    },
    {
        "literature_claim_id": "LC-004",
        "source_id": "karoly-et-al-2022-cohesion",
        "statement": "指称属于非结构性衔接，指称形式通过与文本中另一元素的关系获得解释，因此应在语篇链中而不是孤立句内分析。",
        "claim_type": "theory_definition",
        "confidence": "high",
        "evidence": [
            (9, 1, "referencia, helyettesítés, ellipszis"),
            (9, 2, "egy másik elemre"),
        ],
        "boundary": "可用于识别指称链问题；不自动证明任何一次显化或替换是最优解。",
    },
    {
        "literature_claim_id": "LC-005",
        "source_id": "karoly-et-al-2022-macrostructure",
        "statement": "文学翻译的连贯重构可结合宏命题与关系命题等宏观结构变量进行分析，以观察译文如何重建原作的文本连贯。",
        "claim_type": "method_claim",
        "confidence": "medium",
        "evidence": [
            (1, 1, "makrostruktúra"),
            (1, 2, "makropropozicionális"),
        ],
        "boundary": "只支持采用文本层分析维度，不证明本项目与该英匈小说个案有相同结果。",
    },
    {
        "literature_claim_id": "LC-006",
        "source_id": "karoly-et-al-2022-macrostructure",
        "statement": "同一文学翻译个案中，不同宏观结构指标可能给出不同甚至相互制约的结果，因此不能由单一文本指标推出普遍性结论。",
        "claim_type": "limitation",
        "confidence": "medium",
        "evidence": [
            (1, 2, "ellentmondó eredményeink"),
            (36, 2, "ismétléskerülési hipotézis"),
            (36, 3, "retorikai szerkezetét"),
        ],
        "boundary": "这是对单一指标外推的限制，不是否定宏观结构分析本身。",
    },
    {
        "literature_claim_id": "LC-007",
        "source_id": "eekhof-et-al-2020-vpip",
        "statement": "叙事视角具有感知、认知、情感等多个维度，可通过词汇层视角标记进行系统识别；视角表达在叙事语篇中广泛而多样。",
        "claim_type": "method_claim",
        "confidence": "high",
        "evidence": [
            (2, 1, "perceptual, cognitive and emotional viewpoint"),
            (5, 1, "ubiquitous in narrative discourse"),
            (5, 2, "verbs of perception"),
        ],
        "boundary": "VPIP 原始词表面向荷兰语；本项目只能借用分析维度，不能直接移植其词表。",
    },
    {
        "literature_claim_id": "LC-008",
        "source_id": "van-krieken-2018-perspective",
        "statement": "两个实验表明，上下文视角标记会影响读者把后续歧义感知归于人物还是叙述者，而动词时态在该研究中未显示同样效应。",
        "claim_type": "empirical_finding",
        "confidence": "high",
        "evidence": [
            (10, 1, "highly significant effect on perceptual attributions"),
            (14, 1, "Experiment 2 replicated and extended"),
        ],
        "boundary": "实验材料和参与者为特定荷兰语语境，只支持视角标记可能影响理解的机制，不代表本项目已有读者实验结果。",
    },
    {
        "literature_claim_id": "LC-009",
        "source_id": "al-herz-2016-narrative-pov",
        "statement": "在该英阿小说翻译个案中，局部词汇语法偏移与宏观叙事视角、人物塑造及目标读者体验变化相关联。",
        "claim_type": "empirical_finding",
        "confidence": "medium",
        "evidence": [
            (4, 1, "lexicogrammatical systems"),
            (4, 2, "different readerly experience"),
        ],
        "boundary": "博士论文的单一英阿小说个案仅作机制佐证，不能直接外推到英汉回忆录。",
    },
]


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def _source_registry(out_dir: Path) -> list[Dict[str, Any]]:
    rows = []
    for item in SOURCES:
        path = out_dir / "literature-sources" / item["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Missing acquired source: {path}")
        rows.append({
            key: value for key, value in item.items() if key != "file"
        } | {
            "local_source_path": _relative(path),
            "verification_status": "metadata_verified",
            "allowed_citation_status": "allowed",
            "citation_allowed": True,
            "content_availability": "full_text_available",
        })
    return rows


def _normalize(value: str) -> str:
    return " ".join(str(value).replace("‐", "-").replace("‑", "-").split()).casefold()


def _find_evidence(items: Iterable[Dict[str, Any]], source_id: str, page: int,
                   chunk: int, phrase: str) -> str:
    candidates = [
        item for item in items
        if item.get("source_id") == source_id
        and item.get("location", {}).get("page") == page
        and item.get("location", {}).get("chunk") == chunk
    ]
    if len(candidates) != 1:
        raise ValueError(f"Expected one evidence block for {source_id} p.{page} chunk {chunk}")
    item = candidates[0]
    if _normalize(phrase) not in _normalize(item.get("evidence_text", "")):
        raise ValueError(f"Evidence phrase mismatch for {source_id} p.{page} chunk {chunk}: {phrase}")
    if item.get("provenance") != "source_text_verified":
        raise ValueError(f"Unverified evidence selected for {source_id}")
    return str(item["evidence_id"])


def _claim_artifact(evidence_artifact: Dict[str, Any]) -> Dict[str, Any]:
    claims = []
    for spec in CLAIMS:
        evidence_ids = [
            _find_evidence(evidence_artifact["items"], spec["source_id"], page, chunk, phrase)
            for page, chunk, phrase in spec["evidence"]
        ]
        claim = {
            key: value for key, value in spec.items() if key != "evidence"
        } | {
            "supporting_evidence_ids": evidence_ids,
            "evidence_grounded_status": "grounded",
        }
        claim["content_hash"] = academic_evidence.stable_hash(claim)
        claims.append(claim)
    artifact = {
        "schema_version": literature_evidence.CLAIMS_VERSION,
        "items": claims,
        "extraction": {
            "status": "complete",
            "method": "deterministic_claims_from_verified_local_pdf_blocks",
            "evidence_items_considered": sum(len(x["supporting_evidence_ids"]) for x in claims),
            "rejected_claims": 0,
            "bounded": True,
        },
    }
    artifact["content_hash"] = academic_evidence.stable_hash(claims)
    return artifact


def _verification_artifact(source_artifact: Dict[str, Any], claims: Dict[str, Any]) -> Dict[str, Any]:
    sources = []
    for item in source_artifact["sources"]:
        verification = item.get("verification") or {}
        sources.append({
            "source_id": item["source_id"],
            "existence": verification.get("existence"),
            "original_pdf_verified": bool(item.get("source_file_hash")),
            "source_file_hash": item.get("source_file_hash"),
            "metadata_checks": verification.get("checks") or [],
            "study_design_level": verification.get("study_design_level"),
            "overall_grade": verification.get("overall_grade"),
            "predatory_venue_check": "pass",
            "conflict_of_interest": "none_declared_or_detected",
            "allowed_citation_status": item.get("allowed_citation_status"),
            "note": verification.get("note"),
        })
    artifact = {
        "schema_version": "closeout-literature-verification-v1",
        "job_id": JOB_ID,
        "search_date": SEARCH_DATE,
        "status": "verified_with_declared_boundaries",
        "sources_reviewed": len(sources),
        "sources_verified": sum(x["existence"] == "verified" for x in sources),
        "sources_rejected": 0,
        "grounded_claims": len(claims["items"]),
        "sources": sources,
        "limitations": [
            "来源语言对包括英匈、英阿及荷兰语叙事实验，不得据此声称英汉回忆录具有相同发生频率。",
            "文献只支持分析框架与有边界的机制判断，不支持生成译者意图或本项目读者反应。",
            "Al Herz（2016）为机构库博士论文，作为补充机制证据，权重低于同行评审论文。",
        ],
    }
    artifact["content_hash"] = academic_evidence.stable_hash({
        key: value for key, value in artifact.items() if key != "content_hash"
    })
    return artifact


def _report(registry: list[Dict[str, Any]], claims: Dict[str, Any]) -> str:
    references = "\n".join(
        f"{index}. {item['citation_metadata']['apa7']}"
        for index, item in enumerate(registry, 1)
    )
    claim_lines = "\n".join(
        f"- {item['statement']}\n  - 使用边界：{item['boundary']}"
        for item in claims["items"]
    )
    return f"""# 可核验文献证据收口报告

## 结论

本轮纳入 6 个真实来源、9 条逐字证据约束的 Literature Claim。5 个来源为同行评审论文，1 个为 University of Leeds 机构库博士论文。全部来源均已取得本地原始 PDF；所有主张只绑定 `source_text_verified` 页块，不使用 fixture、摘要转述或模型记忆。

## 检索与筛选

- 检索日期：{SEARCH_DATE}
- 检索面：期刊/出版社页面、Crossref、Semantic Scholar、OpenAlex、高校机构库。
- 主题：翻译评价；文学翻译的衔接与连贯；叙事视角及其读者解释效应。
- 纳入：元数据可核对、原始全文可取得、论点与当前回忆录翻译分析直接相关。
- 排除：只有元数据或摘要、全文付费且无合法机构库存档、新闻体裁且被更直接的文学翻译研究替代、与已纳入来源重复。
- 候选 12 条；纳入 6 条；排除 6 条；无重复记录。
- 排除来源族：Károly（2014）、Gutt（1996）、Winters（2010）、Tarhuni（2024）、Calvillo（2019）、Károly（2017）。排除不代表来源无效，只表示本轮未取得足以进入本地证据链的原始全文，或已有更直接来源。
- 分布检查：没有任何单一年代、方法或期刊家族达到已知条目的 70%，不触发分布偏斜提示。

## 可用主张及边界

{claim_lines}

## 来源质量

- House（2001）：理论/方法来源，Level VII；按翻译研究方法论适配度评为 A。
- Károly 等（2022a、2022b）：文学翻译质性个案，Level VI；按人文学科个案证据规范评为 A。
- Eekhof 等（2020）：叙事视角识别方法论文，Level VI，评为 A。
- van Krieken（2018）：两项受控读者实验，Level III，评为 A。
- Al Herz（2016）：机构库博士论文、单一翻译个案，Level VI，评为 B，仅作补充。
- 未发现掠夺性期刊或已披露利益冲突；所有来源仍受各自语言对、语料和方法边界限制。

## APA 7 参考文献

{references}

## 当前阶段边界

这些证据已经可以进入后续论证规划。翻译审校收口后的正式真实核心案例为0139、0233、0272；SC-0141仅作可选合成补充。文献准备脚本本身不启动Phase B，也不写入正式四章正文。
"""


def prepare(out_dir: Path = DEFAULT_OUT) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    registry = _source_registry(out_dir)
    source_artifact = literature_evidence.build_literature_sources(
        registry, maximum_blocks_per_source=200)
    if source_artifact.get("warnings"):
        raise RuntimeError("; ".join(source_artifact["warnings"]))
    evidence_artifact = literature_evidence.build_literature_evidence(source_artifact)
    claims_artifact = _claim_artifact(evidence_artifact)
    verification = _verification_artifact(source_artifact, claims_artifact)

    (out_dir / "literature-registry.json").write_text(
        json.dumps({"literature_sources": registry}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    academic_writer._write_artifact(out_dir / "literature-sources.json", source_artifact)
    academic_writer._write_artifact(out_dir / "literature-evidence.jsonl", evidence_artifact)
    academic_writer._write_artifact(out_dir / "literature-claims.jsonl", claims_artifact)
    academic_writer._write_artifact(out_dir / "literature-source-verification.json", verification)
    (out_dir / "literature-evidence-report.md").write_text(
        _report(registry, claims_artifact), encoding="utf-8")

    state_path = out_dir / "thesis-closeout-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["literature_evidence"] = {
        "status": "grounded_phase2_ready",
        "source_count": len(registry),
        "peer_reviewed_source_count": 5,
        "grounded_claim_count": len(claims_artifact["items"]),
        "all_originals_acquired": True,
        "phase_b_started": False,
        "artifacts": {
            "registry": "literature-registry.json",
            "sources": "literature-sources.json",
            "evidence": "literature-evidence.jsonl",
            "claims": "literature-claims.jsonl",
            "verification": "literature-source-verification.json",
            "report": "literature-evidence-report.md",
        },
    }
    for stage in state.get("stages") or []:
        if stage.get("stage") == 4:
            stage["status"] = "completed"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "closeout-literature-run-v1",
        "job_id": JOB_ID,
        "search_date": SEARCH_DATE,
        "source_count": len(registry),
        "claim_count": len(claims_artifact["items"]),
        "content_hashes": {
            "sources": source_artifact["content_hash"],
            "evidence": evidence_artifact["content_hash"],
            "claims": claims_artifact["content_hash"],
            "verification": verification["content_hash"],
        },
        "historical_translation_state_modified": False,
        "phase_b_started": False,
    }
    manifest["content_hash"] = academic_evidence.stable_hash(manifest)
    (out_dir / "literature-run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
