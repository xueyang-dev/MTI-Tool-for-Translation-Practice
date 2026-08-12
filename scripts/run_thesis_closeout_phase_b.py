"""Generate and validate the evidence-bounded v6 four-chapter Chinese draft.

This runner is deterministic.  It uses the frozen real case baseline and local
literature artifacts, makes no external model call, and never fabricates Human
Author Evidence or translator intention.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mti_tool import academic_evidence, academic_quality, academic_validator
from mti_tool import academic_writer, thesis_constraints


JOB_ID = "ec100d8686d3891e"
CASE_IDS = [
    f"seg-{JOB_ID}-0139",
    f"seg-{JOB_ID}-0233",
    f"seg-{JOB_ID}-0272",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _stamp(value: dict[str, Any]) -> dict[str, Any]:
    value["content_hash"] = academic_evidence.stable_hash(
        {key: item for key, item in value.items() if key != "content_hash"})
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _research_model() -> dict[str, Any]:
    constraints = thesis_constraints.build_constraints({"submission_year": 2026})
    return _stamp({
        "schema_version": academic_writer.VERSIONS["research_model_version"],
        "research_topic": "英语文学性军事回忆录汉译中的叙事关系、文化信息与语篇回指",
        "research_questions": [
            {
                "rq_id": "RQ1",
                "question": "源语文本的文学性回忆叙事呈现出哪些与人物关系、文化信息和语篇回指有关的翻译难点？",
                "provenance": "system_analysis_confirmed",
            },
            {
                "rq_id": "RQ2",
                "question": "三项有记录的初译—终译变化分别如何处理上述难点，其可观察文本效果是什么？",
                "provenance": "system_analysis_confirmed",
            },
            {
                "rq_id": "RQ3",
                "question": "证据化审校流程如何约束案例选择和质量判断，其适用边界是什么？",
                "provenance": "system_analysis_confirmed",
            },
        ],
        "theoretical_framework": [
            "功能—语用翻译评价",
            "语篇衔接与指称分析",
            "叙事视角标记分析",
        ],
        "method": "基于项目状态、初译—终译差异、审校记录与可核验文献证据的描述性案例研究",
        "analysis_dimensions": [
            "源译对应", "人物关系与隐喻", "文化专名", "指称链",
            "叙事视角", "元语言回指", "证据边界",
        ],
        "expected_contribution": [
            "以逐字项目证据替代笼统的优劣判断",
            "区分可观察的文本效果、系统修复记录与不可观察的译者心理意图",
            "说明系统完整性修复不能转化为论文核心修订案例",
        ],
        "institutional_constraints": constraints,
        "submission_year": 2026,
        "body_language": "zh-CN",
        "writing_style": "规范、克制、问题驱动的中文MTI学术书面语",
        "report_requirements": "翻译实践报告四章正文",
        "target_words": 10000,
        "settings_provenance": {
            "research_topic": "system_analysis_confirmed",
            "theoretical_framework": "grounded_literature_evidence",
            "method": "project_evidence_derived",
            "body_language": "institutional_rule",
        },
    })


def _argument_plan() -> dict[str, Any]:
    claims = [
        {
            "claim_id": "C1",
            "claim": "本报告的质量判断以源文、初译、终译和过程记录的可检验比较为基础，而不以脱离文本的总体印象代替分析。",
            "research_question": "RQ3",
            "project_evidence": ["metric:total_segments"],
            "literature_claims": ["LC-001", "LC-002"],
            "literature_evidence": ["LE-e5ded84745ab50ba", "LE-7570ee4c4bb53468"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "high",
            "planned_sections": ["1"],
            "reasoning": "项目保存完整段落证据；House文献支持把语言描述、解释和评价分开。",
            "counterargument": "可检验不等于结论必然正确，仍需导师判断理论解释是否充分。",
        },
        {
            "claim_id": "C2",
            "claim": "源文本的文学性军事回忆叙事要求把人物关系意象、文化对象身份和回指形式放入各自语篇链中分析。",
            "research_question": "RQ1",
            "project_evidence": CASE_IDS,
            "literature_claims": ["LC-004", "LC-007"],
            "literature_evidence": ["LE-3998419e29ec39a1", "LE-0009ea2f3fde992f"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "medium",
            "planned_sections": ["3"],
            "reasoning": "三案例覆盖隐喻、文化专名/人称回指和元语言回指；文献提供语篇分析维度。",
            "counterargument": "三案例不能穷尽全书所有文本特征。",
        },
        {
            "claim_id": "C3",
            "claim": "项目的可追溯工作流能够区分当前待处理问题、历史问题和系统完整性修复，从而为正式案例资格提供边界。",
            "research_question": "RQ3",
            "project_evidence": [
                "metric:reviewed_segments", "metric:actionable_findings",
                "metric:recorded_actionable_findings", "metric:tm_reuse_count",
            ],
            "literature_claims": [],
            "literature_evidence": [],
            "human_author_evidence": [],
            "support_category": "project_evidence_only",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "high",
            "planned_sections": ["2"],
            "reasoning": "这些数字和状态均由最终项目证据确定性重算。",
            "counterargument": "流程记录能证明发生了什么，不能自动证明每一项语言判断最佳。",
        },
        {
            "claim_id": "C4",
            "claim": "案例0139的修订同时处理汉语叙事节奏和反复出现的手部意象，使人物关系仍可在语篇链中被识别。",
            "research_question": "RQ2",
            "project_evidence": [CASE_IDS[0]],
            "literature_claims": ["LC-007", "LC-009"],
            "literature_evidence": ["LE-0009ea2f3fde992f", "LE-e7bd2ad9342a7490"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "medium",
            "planned_sections": ["3"],
            "reasoning": "初译、终译、审校问题和修复说明均已记录；文献只提供叙事视角分析维度。",
            "counterargument": "没有作者回答，不能把终译文本效果写成译者当时的心理动机。",
        },
        {
            "claim_id": "C5",
            "claim": "案例0233的修订解决了影片名误译和明确主语泛化两个不同层次的问题，恢复文化对象身份和局部指称链。",
            "research_question": "RQ2",
            "project_evidence": [CASE_IDS[1]],
            "literature_claims": ["LC-004", "LC-008"],
            "literature_evidence": ["LE-d74ce265282f2156", "LE-79875e659daeb23e"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "medium",
            "planned_sections": ["3"],
            "reasoning": "片名和主语差异可逐字比较；文献支持在语篇链中分析指称与视角标记。",
            "counterargument": "读者效果没有在本项目中实验测量，只能表述为文本层解释。",
        },
        {
            "claim_id": "C6",
            "claim": "案例0272把目标语中不成立的计字回指改为整句回指，避免源语计词单位机械迁移到汉语。",
            "research_question": "RQ2",
            "project_evidence": [CASE_IDS[2]],
            "literature_claims": ["LC-004"],
            "literature_evidence": ["LE-3998419e29ec39a1"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "medium",
            "planned_sections": ["3"],
            "reasoning": "可观察差异只有“这五个字”至“这句话”；指称文献用于限定分析方法。",
            "counterargument": "没有同期审校记录或修订理由，不能宣称已恢复历史动机。",
        },
        {
            "claim_id": "C7",
            "claim": "三案例能够回答本项目的具体研究问题，但单一项目、三项核心修订和跨语言文献不能支持普遍发生率或读者反应结论。",
            "research_question": "RQ3",
            "project_evidence": ["metric:revision_cases_academically_eligible"],
            "literature_claims": ["LC-006"],
            "literature_evidence": ["LE-e628d716576bbbfa"],
            "human_author_evidence": [],
            "support_category": "mixed_evidence",
            "analysis_type": "AUTHOR_ANALYSIS",
            "confidence": "high",
            "planned_sections": ["4"],
            "reasoning": "宏观结构研究明确限制单一指标外推，本项目也没有读者实验或作者回答。",
            "counterargument": "局限不否定案例的项目内解释价值。",
        },
    ]
    return _stamp({
        "schema_version": academic_writer.VERSIONS["argument_plan_version"],
        "claims": claims,
        "planner_fallback": False,
        "rejected_source_only_support": 0,
    })


def _selected_cases(base: dict[str, Any]) -> dict[str, Any]:
    selected = dict(base)
    selected["selection_policy"] = "authentic_only"
    selected["requested_case_count"] = 3
    selected["eligible_case_count"] = 22
    selected["revision_candidate_pool_count"] = 31
    supports = {
        CASE_IDS[0]: (["C2", "C4"], ["RQ1", "RQ2"]),
        CASE_IDS[1]: (["C2", "C5"], ["RQ1", "RQ2"]),
        CASE_IDS[2]: (["C2", "C6"], ["RQ1", "RQ2"]),
    }
    selected["cases"] = [{
        **item,
        "supports_claims": supports[item["case_id"]][0],
        "research_questions": supports[item["case_id"]][1],
        "coverage_zone": (
            "middle" if item["segment_index"] == 139 else "end"),
        "academic_candidate_status": "eligible",
    } for item in base["cases"]]
    return _stamp(selected)


def _outline(research: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    constraints = research["institutional_constraints"]
    chapters = thesis_constraints.chapter_index(constraints)
    sections = [
        {
            "section_id": "1", "title": chapters["1"]["title"],
            "purpose": chapters["1"]["purpose"],
            "required_subsections": chapters["1"]["required_subsections"],
            "research_questions": ["RQ1", "RQ2", "RQ3"],
            "claims": ["C1"], "cases": [],
            "literature_claims": ["LC-001", "LC-002"],
            "literature_evidence": ["LE-e5ded84745ab50ba", "LE-7570ee4c4bb53468"],
            "literature_sources": ["house2001-tqa"],
            "required_statistics": ["total_segments"],
            "target_words": 1800, "minimum_chars": 900,
            "allowed_conclusions": ["说明研究问题和证据边界，不预告未经分析的答案"],
        },
        {
            "section_id": "2", "title": chapters["2"]["title"],
            "purpose": chapters["2"]["purpose"],
            "required_subsections": chapters["2"]["required_subsections"],
            "research_questions": ["RQ3"], "claims": ["C3"], "cases": [],
            "literature_claims": [], "literature_evidence": [],
            "literature_sources": [],
            "required_statistics": [
                "reviewed_segments", "tm_reuse_count", "actionable_findings",
                "recorded_actionable_findings"],
            "target_words": 2300, "minimum_chars": 1400,
            "allowed_conclusions": ["区分系统动作、人工动作与不可观察意图"],
        },
        {
            "section_id": "3", "title": chapters["3"]["title"],
            "purpose": chapters["3"]["purpose"],
            "required_subsections": chapters["3"]["required_subsections"],
            "research_questions": ["RQ1", "RQ2"],
            "claims": ["C2", "C4", "C5", "C6"], "cases": CASE_IDS,
            "case_groups": {"authentic_revision": CASE_IDS,
                            "synthetic_contrast": []},
            "literature_claims": ["LC-004", "LC-007", "LC-008", "LC-009"],
            "literature_evidence": [
                "LE-3998419e29ec39a1", "LE-d74ce265282f2156",
                "LE-0009ea2f3fde992f", "LE-79875e659daeb23e",
                "LE-e7bd2ad9342a7490"],
            "literature_sources": [
                "karoly-et-al-2022-cohesion", "eekhof-et-al-2020-vpip",
                "van-krieken-2018-perspective", "al-herz-2016-narrative-pov"],
            "required_statistics": [],
            "target_words": 4500, "minimum_chars": 3000,
            "allowed_conclusions": [
                "只分析保存的初译—终译差异和可观察文本效果",
                "不得把system_actions表述为作者本人意图",
                "不得把荷兰语、英匈或英阿研究外推为本项目读者实验结果",
            ],
        },
        {
            "section_id": "4", "title": chapters["4"]["title"],
            "purpose": chapters["4"]["purpose"],
            "required_subsections": chapters["4"]["required_subsections"],
            "research_questions": ["RQ1", "RQ2", "RQ3"],
            "claims": ["C7"], "cases": [],
            "literature_claims": ["LC-006"],
            "literature_evidence": ["LE-e628d716576bbbfa"],
            "literature_sources": ["karoly-et-al-2022-macrostructure"],
            "required_statistics": ["revision_cases_academically_eligible"],
            "target_words": 1400, "minimum_chars": 900,
            "allowed_conclusions": [
                "逐项回应研究问题", "不引入新案例", "不声称已完成导师人工复核"],
        },
    ]
    return _stamp({
        "schema_version": academic_writer.VERSIONS["outline_version"],
        "sections": sections,
        "planner_fallback": False,
        "institutional_constraints": constraints,
        "case_count_policy": {
            "status": "sufficient_revision_cases", "preferred": 3,
            "minimum": 2, "selected": 3, "scarcity_disclosure": ""},
    })


def _case_block(segment: dict[str, Any]) -> str:
    case_id = segment["segment_id"]
    return (
        f"[{case_id}]\n"
        f"> [SOURCE {case_id}]: {segment['source']}\n"
        f"> [INITIAL {case_id}]: {segment['initial_target']}\n"
        f"> [TARGET {case_id}]: {segment['final_target']}"
    )


def _chapters(segments: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chapter1 = """### 1.1 研究背景及意义

本报告以英语文学性军事回忆录《当天空属于我们时》的汉译实践为对象。源文将飞行训练、战争记忆、家庭关系和成长经验编织在同一叙事中，既包含飞机操纵、航向和军旅经历等专业信息，也包含口语对话、文化专名、意象复现和时间跨度较大的回忆。此类文本的翻译困难并不只表现为某个词“是否译对”，还表现为人物关系是否在叙述中延续、文化对象是否被正确识别、指称形式是否与目标语的表达单位匹配。

翻译实践报告若只以“准确、流畅、自然”等总体判断评价译文，难以说明问题发生在哪里，也无法验证所谓策略是否真正作用于文本。House关于翻译质量评价的讨论强调，应把语言描述、解释性比较与社会价值判断区分开来，译文评价必须回到源文—译文关系及具体语境。<!--claim:C1--><!--lit-claim:LC-001--><!--lit-evidence:LE-e5ded84745ab50ba-->House（2001）<!--cite:house2001-tqa-->提出的功能—语用分析也提示，语言形式、语域、体裁和语境需要结合考察，而不能用单一标签代替逐例论证。<!--lit-claim:LC-002--><!--lit-evidence:LE-7570ee4c4bb53468-->

本项目共保存273<!--stat:total_segments-->个源译段。报告在全量证据审计后，只选择通过真实初译—终译资格门禁且没有系统完整性标记的三项案例。研究意义主要有两点：其一，以逐字证据呈现初译问题、终译变化和文本效果，使案例分析能够被复查；其二，把语言修订与系统对齐修复严格分开，避免把段落复制、跨段污染或未翻译标题误写成译者的翻译决策。

在研究方法上，本报告不以终译是否“顺眼”作为案例入选标准，而是先核对源文、历史初译和当前终译，再检查审校问题、修复记录与完整性标记。只有存在真实且有意义的双版本变化、同时没有系统错位或跨段污染的段落，才进入修订案例池；随后再按问题互补性选取三项核心案例。文献在此承担概念界定和分析限制功能，不能替代项目文本证据。由于没有取得可核验的译者同期说明，本报告不追溯推断翻译意图，也不把技术性修复记录表述为译者自述。

### 1.2 研究问题

本报告围绕以下问题展开：<!--rq:RQ1-->

第一，源语文本的文学性回忆叙事呈现出哪些与人物关系、文化信息和语篇回指有关的翻译难点？<!--rq:RQ2-->

第二，三项有记录的初译—终译变化分别如何处理上述难点，其可观察文本效果是什么？<!--rq:RQ3-->

第三，证据化审校流程如何约束案例选择和质量判断，其适用边界是什么？

### 1.3 报告结构

全文按学院规定分为四章。第一章说明研究背景、研究问题与报告结构。第二章介绍项目、译前准备、翻译过程和译后管理，重点交代证据是如何保存、复核和分类的。第三章先归纳回忆录的文本特征和实际难点，再分析三项真实修订案例，分别讨论人物关系中的隐喻、文化专名与指称链、跨语言元语言回指。第四章逐项回应研究问题，提炼项目内可迁移的方法，并说明单一项目、缺少作者说明和没有读者实验等限制。
"""

    chapter2 = """### 2.1 项目简介

源文件题名为WHEN THE SKY WAS OURS，作者栏记录为ZE’EV RAZ，版权页注明该英语文本由Sarah Mageni从希伯来语译出。因而，本项目处理的是英语版本向简体中文的翻译，不对希伯来语原作与英语译本之间的关系作二手推断。文本体裁可概括为带有文学叙事特征的军事回忆录：叙述主体在童年、飞行训练和战争经历之间往返，专业飞行语汇与家庭记忆、历史人物、歌曲和影片名称并置。

项目以段落为基本处理单位，同时保存源文、初译、终译、审校状态、翻译记忆来源和审校问题。最终状态中，273<!--stat:reviewed_segments-->个段落均已完成审校；其中188<!--stat:tm_reuse_count-->个段落记录为翻译记忆复用。这里的“复用”只是过程事实，不直接等同于质量合格；段落仍须满足源译对应和当前审校问题准入要求。

### 2.2 翻译流程

项目流程由译前准备、翻译过程和译后管理三个阶段构成。<!--claim:C3--><!--rq:RQ3-->其核心不是把模型输出直接视为成品，而是让每一轮文本变化都能回到可核验的段落证据，并把语言修订、系统修复和未解决问题分开记录。

#### 2.2.1 译前准备

译前首先识别文本体裁、受众和文体约束。项目画像将文本归入文学领域中的回忆录/自传体小说，目标读者为对以色列历史、军事和家庭故事感兴趣的普通中文读者；文体要求是保持第一人称回忆叙事、对话的口语感以及历史文化信息的可识别性。由于文本同时含有飞机型号、飞行状态、以色列地名和人物名，译前准备不能只建立词表，还需要预先区分三类项目：技术术语需要概念稳定，人物和地名需要全篇一致，作品名称需要先确认文化对象身份再决定中文呈现。

项目没有把未经冻结的术语判断写成论文中的既定事实。最终证据显示术语冲突为零，但这只说明当前规则下没有记录到冲突，并不证明所有专名译法都存在唯一标准答案。对影片名《牢狱大暴动》的处理另行核验了作品身份；对人名、地名和飞行器名称则以同一文本内部的一致性和中文可读性为主要判断依据。

#### 2.2.2 翻译过程

翻译阶段按语义批次处理段落，并保存初译和后续终译。初译记录的作用不是展示一个人为构造的“错误版本”，而是保留实际文本演变；若初译缺失，就不能在论文中补造。对已保存双版本的段落，系统只把词汇或内容发生有意义变化者列入修订候选，空格和纯标点变化不计入核心案例。

翻译记忆用于复用已经审校的源译对，但复用段仍受完整性检查约束。项目后续发现，历史状态中个别段落存在上一段译文复制、跨页内容提前并入和结构化输出残留等问题。这些问题说明，仅有“已审校”或“来自翻译记忆”的状态记录不足以证明源译对应；因此又增加了对相邻段近重复、异常长度比例和跨页边界的定向检查。

#### 2.2.3 译后管理

译后管理先处理历史审校记录，再进行全量对齐补遗。原项目有三十二条待处理审校问题；复核过程中另建立两条用于纠正错挂或遗漏的技术性审校记录，因此历史累计可处理问题为34<!--stat:recorded_actionable_findings-->条。所有原问题均按“接受并修复、驳回误报、纠正错挂”记录处置，而不是为了清零机械采纳。当前待处理问题为0<!--stat:actionable_findings-->条。

全量补遗还识别出作者名误译、相邻段复制、跨段污染、英文标题未翻译和结构化输出残留等系统完整性问题。修复前后的完整状态均单独保存，历史初译没有被覆盖。相关段落带有持久完整性标记：即使终译已经恢复正确，它们也不能转化为论文核心修订案例。技术性修复记录与作者证据分开保存，也不表述为作者本人的翻译意图。

这一流程最终形成两条相互独立的判断线：语言层面判断某一终译是否较好地处理了可观察问题；证据层面判断该段是否有资格支持“真实修订案例”的历史性叙述。前者成立不必然推出后者成立，系统故障修复正是二者必须分离的原因。
"""

    case139 = _case_block(segments[CASE_IDS[0]])
    case233 = _case_block(segments[CASE_IDS[1]])
    case272 = _case_block(segments[CASE_IDS[2]])
    chapter3 = f"""### 3.1 源语文本的类型与特征

源文本的基本类型是第一人称军事回忆录，但其语言并非单一的纪实说明。叙述在飞行操作、童年记忆、家庭交流和历史事件之间切换，常以短句、对话和突转保持口述感，又通过反复出现的手、目光、声音和飞行感知组织人物关系。Eekhof等（2020）<!--cite:eekhof-et-al-2020-vpip-->把叙事视角区分为感知、认知和情感等维度，并指出视角可以通过词汇标记被系统识别。<!--lit-claim:LC-007--><!--lit-evidence:LE-0009ea2f3fde992f-->该框架在本报告中只用于识别叙述焦点，不直接移植其荷兰语词表。

第二类特征是文化信息密集。人名、地名、军史事件、歌曲和影片标题往往同时承担指称和情节功能。译名若指向错误对象，问题不仅是“名称不统一”，还可能改变人物选择、对话含义或场景背景。第三类特征是语篇回指。Károly等（2022a）<!--cite:karoly-et-al-2022-cohesion-->指出，指称形式通过与文本中其他成分的关系获得解释，不能脱离语篇链孤立分析。<!--lit-claim:LC-004--><!--lit-evidence:LE-3998419e29ec39a1-->本项目中的人称主语、指示词和计量表达都需要在前后句中确认所指。

### 3.2 翻译难点

结合全量审校和正式案例门禁，本报告把主要难点归纳为三个层次。<!--rq:RQ1--><!--claim:C2-->第一，文学意象与人物关系同时存在时，中文若只追求抽象释义，可能抹去贯穿语篇的形象；若逐词直译，又可能产生生硬句法。第二，文化专名和人称指代位于同一叙事段时，一个错误片名与一个被泛化的主语会分别破坏文化对象身份和局部视角。van Krieken（2018）<!--cite:van-krieken-2018-perspective-->的实验说明，上下文视角标记可能影响读者把歧义感知归于人物还是叙述者。<!--lit-claim:LC-008--><!--lit-evidence:LE-79875e659daeb23e-->本报告只借用这种机制解释文本差异，不声称本项目已经测量中文读者反应。

第三，源语对自身语言形式作计数或命名时，译文不能机械搬运原来的语言单位。英语中的words与汉语中的“字”不处于同一计量层级；若译文引语实际字数与后文计量冲突，读者会在同一目标语表层看到不一致。三个难点分别由以下三项真实修订展开。<!--rq:RQ2-->

### 3.3 翻译策略与解决方案

#### 3.3.1 真实修订案例0139：隐喻保留与叙事节奏

{case139}

该段的难点集中在父子关系的间接呈现。源文先写父亲修理机器和“我”对其能力的敬畏，随后以多年后的焊接请求回到二人的交流方式。初译“他却以他一贯的方式回答”信息完整，但结构拖沓；“你需要那个做什么”带有英语句法痕迹；末句“再次避开了我伸出的手”保留了形象，却与前句衔接松散。审校记录曾建议直接改为“再次回避了我的请求”，这种处理能消除生硬感，却会把可视的手部意象完全抽象化。

修复记录采取了不同处理：将“你需要那个做什么？”改为“学那个干什么？”，把问句压缩为符合父亲口吻的汉语反问；同时把“再次避开了我伸出的手”调整为“又一次避开了我伸向他的手”。终译没有删除“手”，而是通过“我伸向他”的方向关系把动作和请求重新连接。这样处理的可观察效果不是笼统的“更自然”，而是两点：问句的宾语从含混的“那个”恢复为具体行为“学”，手部意象则继续承担父亲拒绝亲近或拒绝回应的叙事功能。<!--claim:C4-->

Al Herz（2016）<!--cite:al-herz-2016-narrative-pov-->的英阿个案显示，局部词汇语法变化可能与宏观叙事视角和人物塑造相关。<!--lit-claim:LC-009--><!--lit-evidence:LE-e7bd2ad9342a7490-->该结论不能直接外推到本项目，但可以说明为何本例不能只比较单个问句：末尾的“手”仍需放回家庭访问、父亲手势和身体记忆构成的语篇环境中。终译保留意象是系统审校记录中的修复选择，不等于已获得作者关于创作意图的说明。

#### 3.3.2 真实修订案例0233：文化对象识别与明确回指

{case233}

本例包含两个相互独立但共同影响场景理解的问题。其一，初译把Riot in Cell Block 11处理为《监狱摇滚》，后者会使中文读者联想到另一部以音乐为显著特征的影片，而该段随后叙述的是牢房暴动、狱警和囚犯。修复记录在核验影片身份后，将“《监狱摇滚》”改为“《牢狱大暴动》”，使片名与后文情节同指一个文化对象。其二，源文在平票之后写He whispered quietly，初译用“有人轻声嘀咕”把男性单数回指改成了不定人称。终译将“有人轻声嘀咕”改为“他低声念叨”，恢复了原文保留的男性视角位置。<!--claim:C5-->

这两项变化分别作用于文化指称和人称指称。前者避免对象识别错误，后者没有擅自指定“他”究竟是哪一名男孩，而是保留源文同等程度的指称信息。Károly等（2022a）关于指称关系不能孤立解释的论述在此提供了分析方法。<!--lit-claim:LC-004--><!--lit-evidence:LE-d74ce265282f2156-->对“他”的解释需要结合平票、男孩与女孩的分组以及后续阿莫斯发言，不能把终译的明确代词误写成已解决全部人物身份歧义。van Krieken的实验结果同样只说明视角标记可能影响解释路径，不构成本项目的读者效果数据。

#### 3.3.3 真实修订案例0272：元语言计量与整句回指

{case272}

源文第二句为Those five words，其中five描述英语表达的词数。初译写“这五个字”，但中文引语“你不会经历战争”在目标语表层并不是五个汉字。问题由此从源语事实转变为译文内部矛盾：读者会自然地把“五个字”理解为对前述中文引语的计字。终译将“这五个字”改为“这句话”，不再复制源语的计词单位，而是保留其核心指称功能——指向马蒂刚刚说出的整句言语。<!--claim:C6-->

该修订的优势可以精确表述为：它消除了目标语可直接核对的数量冲突，同时没有改变“这段话五十年来持续回响”的时间意义。其代价是弱化了源文five所带来的形式强调。若要保留数字，必须重写前面的引语，使目标语计量重新成立，但那会改变马蒂话语的词汇选择；现有记录没有显示曾采用这一备选方案。因此，本报告只确认“这五个字”至“这句话”的实际变化及其文本效果，不推断当时为何作出修订。

#### 3.3.4 跨案例综合

三个案例体现了由局部形式进入语篇功能的不同路径。0139要求在汉语节奏调整中保留人物关系意象；0233要求先识别文化对象，再维持人称回指的信息量；0272要求区分英语计词与汉语计字，并把回指单位调整为目标语中成立的“句”。共同点不在于它们使用同一个策略标签，而在于终译都消除了一个可定位的问题，同时保留源文仍需传递的关系。

这种比较也说明证据边界的重要性。前两例有审校问题和技术性修复说明，可以讨论记录在案的问题与解决方式；第三例只有真实双版本，没有同期审校记录，因而只能分析可观察差异。任何一例都不能据此推出文学翻译中的普遍错误频率，也不能把技术性修复记录写成真实作者的心理活动。
"""

    chapter4 = """### 4.1 研究问题回应

<!--rq:RQ1-->对于第一个研究问题，本项目的文学性军事回忆叙事至少呈现三类相互关联的难点：人物关系通过意象和口吻间接显现，文化专名与人物指称共同参与场景建构，源语元语言表达需要根据汉语计量和回指习惯重新建立内部一致性。这些难点都超出孤立词义替换，需要回到段落和语篇链中判断。

<!--rq:RQ2-->对于第二个研究问题，三项真实修订分别显示：汉语句法压缩可以与意象保留并行；文化对象核验和代词信息量恢复可以在同一段落分别处理；源语计词单位不宜机械转写为汉语计字单位，改用整句回指能够消除目标语内部冲突。这些回答只描述保存文本中的变化和效果，不生成译者未记录的动机。

<!--rq:RQ3--><!--claim:C7-->对于第三个研究问题，证据化流程的主要作用是设置结论边界。当前全量候选中有22<!--stat:revision_cases_academically_eligible-->项修订通过共享资格门禁，正式论文再按问题互补性和证据完整度选择三项核心案例；作者名误译、相邻段复制和跨段污染等系统修复则因持久完整性标记被排除。该区分使“译文已被修好”与“该段可以证明真实翻译修订”不再混为一谈。

### 4.2 实践经验与可迁移方法

<!--claim:C7-->第一，案例选择应晚于全量源译对齐检查。若先写论文、后检查段落边界，系统错位很容易被包装为所谓翻译策略。第二，初译、终译、审校问题和修复动作应分别保存；只有文本差异而没有过程说明时，仍可开展有限的文本分析，但不能补写历史理由。第三，文化专名核验与语篇指称分析需要分层进行：前者回答“对象是谁”，后者回答“表达在上下文中指向谁或什么”。第四，质量评价需要指出具体维度和可观察变化，避免用“更准确、更流畅”代替论证。

Károly等（2022b）<!--cite:karoly-et-al-2022-macrostructure-->指出，同一文学翻译个案中的不同宏观指标可能给出不同甚至彼此制约的结果。<!--lit-claim:LC-006--><!--lit-evidence:LE-e628d716576bbbfa-->这提醒本项目：一个案例在指称上改善，并不自动意味着其节奏、文化说明或文体效果同样最优；评价必须保留维度差异。

### 4.3 局限与改进方向

<!--claim:C7-->本报告首先受单一项目和案例规模限制。三项核心案例能够展示不同问题机制，却不能代表英语回忆录汉译中的发生率。其次，文献证据来自翻译评价、英匈文学翻译、荷兰语叙事视角实验和英阿小说翻译个案；它们提供分析概念与限制条件，但不能替代英汉语料或本项目的中文读者实验。再次，本报告没有可核验的译者同期说明；技术性修复记录只能证明审校时采用了何种判断，不能还原真实译者的心理意图。

<!--claim:C7-->后续改进可从三个方向展开：一是由导师逐项复核三案例的问题定义、理论映射和结论强度；二是在不改写历史证据的前提下，补做中文读者小规模理解测试，检验代词和元语言回指的实际效果；三是将全量对齐扫描前移到翻译阶段，在终译保存前阻止相邻段复制和跨页污染。当前四章正文已通过确定性结构与证据验证后，仍应视为送导师审阅稿，而不是未经人工复核即可提交的定稿。
"""
    return [
        {"section_id": "1", "title": "引言", "content": chapter1},
        {"section_id": "2", "title": "翻译项目概述", "content": chapter2},
        {"section_id": "3", "title": "翻译项目案例分析", "content": chapter3},
        {"section_id": "4", "title": "总结与反思", "content": chapter4},
    ]


def _report(sections: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"## {item['section_id']} {item['title']}\n\n{item['content'].strip()}"
        for item in sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence = _load(out_dir / "academic-evidence-final.json")
    baseline = _load(out_dir / "selected-cases-final.json")
    literature_sources = _load(out_dir / "literature-sources.json")
    literature_evidence = academic_writer._read_artifact(
        out_dir / "literature-evidence.jsonl") or {}
    literature_claims = academic_writer._read_artifact(
        out_dir / "literature-claims.jsonl") or {}
    segment_index = academic_evidence.segment_index(evidence)
    if not all(case_id in segment_index for case_id in CASE_IDS):
        parser.error("formal case baseline is missing from academic evidence")

    research = _research_model()
    arguments = _argument_plan()
    selected = _selected_cases(baseline)
    outline = _outline(research, arguments)
    sections = _chapters(segment_index)
    report = _report(sections)
    validation = academic_validator.validate_academic_report(
        report, evidence, research, arguments, selected, outline,
        literature_sources, literature_evidence, literature_claims,
        human_evidence=[])
    diagnostics = academic_quality.deterministic_diagnostics(
        research, arguments, selected, outline, sections, evidence)
    quality_findings = academic_quality._deterministic_findings(diagnostics)
    quality = _stamp({
        "schema_version": "deterministic-academic-quality-v1",
        "status": "pass" if not quality_findings else "review_required",
        "review_type": "deterministic_only_no_external_model",
        "dimensions": {
            "research_alignment": "pass" if not diagnostics["rq_matrix"][
                "unanswered_rqs"] else "review_required",
            "case_quality": "pass" if all(
                item["class"] in {"strong_case", "usable_case"}
                for item in diagnostics["case_quality"]) else "review_required",
            "evidence_utilization": "pass" if not diagnostics[
                "evidence_utilization"]["high_value_unused_cases"]
                else "review_required",
            "cross_section_coherence": "pass" if not diagnostics[
                "cross_section_checks"] else "review_required",
            "semantic_academic_judgment": "pending_supervisor_review",
        },
        "findings": quality_findings,
        "diagnostics": diagnostics,
        "limitation": (
            "未调用外部模型，也未冒充导师人工审稿；语义充分性由导师复核。"),
    })

    artifacts = {
        "research-model-v6.json": research,
        "argument-plan-v6.json": arguments,
        "selected-cases-v6.json": selected,
        "academic-outline-v6.json": outline,
        "academic-sections-v6.json": _stamp({
            "schema_version": "academic-sections-v6-closeout",
            "sections": sections,
            "body_language": "zh-CN",
            "generation_mode": "deterministic_evidence_bounded_authoring",
            "external_model_used": False,
        }),
        "academic-validation-v6.json": validation,
        "academic-quality-v6.json": quality,
    }
    for name, value in artifacts.items():
        _write(out_dir / name, value)
    report_path = out_dir / "thesis-body-v6.md"
    report_path.write_text(report, encoding="utf-8")

    closeout_path = out_dir / "thesis-closeout-state.json"
    closeout = _load(closeout_path)
    closeout["status"] = (
        "automated_validation_complete_supervisor_review_pending"
        if validation["status"] in {"pass", "pass_with_warnings"}
        and quality["status"] == "pass" else "phase_b_review_required")
    closeout["human_evidence"]["phase_b_started"] = True
    closeout["literature_evidence"]["phase_b_started"] = True
    for stage in closeout.get("stages") or []:
        if stage.get("stage") == 6:
            stage["status"] = "completed" if validation["status"] in {
                "pass", "pass_with_warnings"} else "review_required"
        if stage.get("stage") == 7:
            stage["status"] = "supervisor_review_pending"
    closeout["phase_b"] = {
        "status": "completed" if validation["status"] in {
            "pass", "pass_with_warnings"} and quality["status"] == "pass"
            else "review_required",
        "external_model_used": False,
        "human_author_evidence_entries_used": 0,
        "system_actions_presented_as_author_intention": False,
        "body_language": "zh-CN",
        "chapter_count": 4,
        "core_case_ids": CASE_IDS,
        "validation_status": validation["status"],
        "deterministic_quality_status": quality["status"],
        "semantic_review_status": "pending_supervisor_review",
        "artifacts": sorted([*artifacts, report_path.name]),
    }
    _write(closeout_path, closeout)

    manifest = _stamp({
        "schema_version": "thesis-phase-b-run-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "job_id": JOB_ID,
        "status": closeout["phase_b"]["status"],
        "external_model_used": False,
        "state_source": "translation-state-after-review.json",
        "input_hashes": {
            name: _sha256(out_dir / name) for name in (
                "academic-evidence-final.json", "selected-cases-final.json",
                "literature-sources.json", "literature-evidence.jsonl",
                "literature-claims.jsonl")},
        "output_hashes": {
            name: _sha256(out_dir / name) for name in [*artifacts, report_path.name]},
    })
    _write(out_dir / "phase-b-run-manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "validation": validation["status"],
        "validation_issues": validation["summary"],
        "quality": quality["status"],
        "quality_findings": len(quality_findings),
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
