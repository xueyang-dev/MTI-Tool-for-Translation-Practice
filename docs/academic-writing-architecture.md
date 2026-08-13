# 学术写作子系统：现状审计与迁移设计

## 学院 MTI 写作约束（2026+）

`mti_tool.thesis_constraints` 是规划、分节写作与确定性验证共同使用的唯一学院约束入口。
2026 年及以后 MTI 正式论文正文使用简体中文撰写；英文仅用于 ABSTRACT、逐字源文/译文、
术语、专名和文献信息。当前流水线负责四章正文，摘要、目录、参考文献、致谢与附录属于
完整论文装配阶段，不能因当前未生成而从规范中删除。

四章正文固定为：

1. 引言：1.1 研究背景及意义；1.2 研究问题；1.3 报告结构；
2. 翻译项目概述：2.1 项目简介；2.2 翻译流程（译前准备、翻译过程、译后管理）；
3. 翻译项目案例分析：3.1 源语文本的类型与特征；3.2 翻译难点；3.3 翻译策略与解决方案；
4. 总结与反思：4.1 研究问题回应；4.2 实践经验与可迁移方法；4.3 局限与改进方向。

章际硬约束为“研究问题 → 文本特征 → 翻译难点 → 案例证据 → 策略或解决方案 →
翻译效果 → 有界结论”。第 1 章提出研究问题，第 3 章以证据展开，第 4 章逐项回答，
且不得在结论首次引入案例。理论仅在有落地文献和具体案例映射时使用，不能替代问题分析。
修订案例仍须满足下述真实初译→终译资格门禁，案例数量由证据决定。

## 修订案例硬资格规则

真实修订案例分析只允许使用 `authentic_revision`：初译和终译均已记录，经保守规范化后
存在有意义的文本差异，且两版没有相邻段污染等完整性标记。空白或纯标点变化、系统错位
修复和污染清理均不自动构成学术修订案例。候选挖掘先执行该门禁，
再按完整修复链、关联 finding、repair history、实际文本差异和研究问题相关性排序。

`non_revision_case` 可以保留在项目证据库中，但不得进入核心修订案例池，也不能由
Human Author Evidence 升级为修订案例。案例数量策略为“优选 3 个，最低 2 个”：

- 3 个及以上：`sufficient_revision_cases`；
- 恰有 2 个：`two_case_fallback`，允许形成双案例章节，但必须披露证据稀缺；
- 少于 2 个：`insufficient_revision_cases`，停止核心案例写作并恢复历史版本或更换项目。

三个状态均不得用未修改、污染或推断出的片段回填。Human Author Evidence 只可为已通过
资格门禁的案例补充作者事后说明，不得改变 `case_role` 或初译—终译差异。

此外，学术章节可使用独立标注的 `synthetic_contrast`，但它不是第三个真实修订案例，也不
改变上述数量状态。其模拟初译和优化译文只存在于 synthetic artifact，必须通过 plausibility、
materiality 和 repair validation，并在正文公开方法与局限。详细设计见
`docs/synthetic-contrast-case-architecture.md`。

## 真实项目修订案例恢复结论（ec100d8686d3891e）

历史恢复审计曾确认只有 0272 可直接作为真实修订案例；0142 和 0209 分别受到相邻段污染
与错位重译影响。随后按源 PDF 和全量项目状态完成翻译审校收口：32 条原 actionable
finding 已逐条裁决，9 个未审校段已经复核，全部 273 段现均标记为已审校，当前
blocking/actionable 均为 0。修复前 `state.json` 已完整备份，全部历史 `initial_target`
保持不变。

作者名误译、跨段污染和相邻段复制修复（0001、0093、0101、0142、0144/0145、0201、
0209、0236、0239）带有持久
`integrity_flags`。即使终译已经修正，这些段也不能被“洗白”为论文核心案例。系统审校动作
独立记录在 `system_actions`，不会进入 `human_actions`，也不得写成作者本人意图。

修复后重新执行共享资格门禁，正式核心案例确定为 0139、0233、0272，分别覆盖文学隐喻与
叙事关系、文化专名与叙事指代、元语言回指与语义范围。三者均保存真实初译—终译差异，
且无系统完整性标记。SC-0141 仍只作为可选合成对比，不计入三项真实核心案例。最终审计、
选择报告和完整学术证据位于
`eval/academic-quality/ec100d8686d3891e/thesis-closeout-v6/`。作者问题保持撤回；分析只能引用
可观察文本效果、历史 finding 和系统修复记录，不能反推译者心理意图。

## 真实项目文献证据基线（ec100d8686d3891e）

论文收口目录 `eval/academic-quality/ec100d8686d3891e/thesis-closeout-v6/` 已建立真实文献
证据包：6 个原始全文来源、9 条有边界的 Literature Claim。5 个来源为同行评审论文，
1 个为 University of Leeds 机构库博士论文；全部来源均已取得本地 PDF，来源元数据由
期刊/机构库页面、Crossref、Semantic Scholar 或 OpenAlex 交叉核对。逐条主张只绑定
`source_text_verified` 页块，不使用 fixture、摘要转述或模型记忆。

证据覆盖翻译评价方法、文学翻译的衔接与连贯、叙事视角及其读者解释效应。英匈、英阿
和荷兰语实验结论只作为分析框架或机制证据，不得外推为英汉回忆录中的发生频率，也不能
生成译者意图或本项目读者反应。规范来源、页块、主张、核验记录和检索报告分别见
`literature-sources.json`、`literature-evidence.jsonl`、`literature-claims.jsonl`、
`literature-source-verification.json` 与 `literature-evidence-report.md`。准备命令为：

```bash
.venv/bin/python scripts/prepare_closeout_literature.py
```

该命令只读取已取得的本地 PDF 并更新隔离收口目录，不修改历史翻译状态，也不启动
Phase B。

可用以下命令重复执行只读审计；它不会调用模型或写回历史项目状态：

```bash
.venv/bin/python scripts/audit_revision_cases.py \
  --job-id ec100d8686d3891e \
  --out-dir <new-isolated-directory> \
  --canonical-questions <existing-human-evidence-questions.json> \
  --investigate-index 142
```

## 迁移前流水线（历史审计）

迁移前阶段三由 `core.run_job_pipeline` 调用 `core.generate_mti_report`。后者从
`report_evidence.evidence_text_block` 取得从第 0 段开始、最多约 9000 字符的
连续双语前缀，分别调用四个章节 prompt，再把返回文本拼成 Markdown。
`p3_sections` 负责章节级断点续写，`p3_done` 表示四章已生成，`p3_md` 用于
Streamlit 展示和 `markdown_to_word` 导出 DOCX。

## 迁移前状态模型

任务状态保存在 `outputs/<job_id>/state.json`。迁移前与学术写作有关的字段只有
`report_enabled`、`p3_sections`、`p3_md`、`p3_done` 和 `theory`。这些字段没有
记录证据、研究问题、论点、案例、提纲、验证、审稿或依赖版本，因而无法判断
旧章节是否因翻译、理论或 prompt 变化而失效。

## 已有证据

- `pairs`：稳定顺序的 source / target；新任务可能还有 initial_target、reviewed、
  from_tm、glossary_entry_ids。
- `findings`：段落级 blocking / actionable / informational，部分记录 review、
  deterministic check、suggested_target、conflict 和 resolution。
- `human_actions`：人工修复、接受风险和重译记录。
- `glossary` / `glossary_frozen` / `glossary_injection_log`：术语决策与注入记录。
- `review_stats`、`tm_used_count`、`document_profile`：可确定性重算或引用的项目统计。
- `assets.segment_id(job_id, index)`：可复用的稳定段落身份。

## 已确认缺口

1. 证据只取连续前缀；实测 273 段任务只覆盖前 79 段，不能代表全书。
2. findings、修复历史、TM 和术语证据没有进入四章写作上下文。
3. 四章没有共享的研究问题、论点计划、案例选择或提纲。
4. prompt 虽禁止伪造，运行时不验证 segment_id、引文、统计、术语或引用。
5. `p3_sections` 只按标题复用；架构或 prompt 升级后旧文本仍可混入。
6. 没有重新规划、整篇重生成、单节重生成、重新验证或重新审稿入口。
7. 报告异常与翻译异常共用顶层错误通道。
8. 历史任务的证据完整度不一；缺失 initial_target 等字段时只能标记未记录。

## 迁移约束

- 不重跑或改写阶段一、二；新学术证据可从已保存 state 重建。
- 保留 `p3_md` / `p3_done` 作为下载和旧调用兼容层，但不再作为学术状态真源。
- 旧报告首次进入新流水线时备份，不能与新章节静默混用。
- JSON 文件与现有原子 state 持久化模式兼容，不引入数据库或新依赖。
- 文献为空时允许生成项目证据型报告，但禁止模型虚构正式引用。

## 实施架构

新流水线为：

```text
Academic Evidence
→ Synthetic Difficulty / Baseline / Diagnosis / Optimization / Validation
→ Research Model
→ Literature Source Snapshot
→ Literature Evidence
→ Literature Claim
→ Argument Plan
→ Case Selection
→ Academic Outline
→ Section Writing
→ Deterministic Validation
→ Semantic Review
→ Literature Support Review
→ Targeted Repair
```

实现采用三个职责模块：证据与候选挖掘、学术编排与版本依赖、确定性验证。
每个阶段输出独立 JSON artifact，并在 `academic_state` 中记录内容 hash、版本、
状态和失效原因。写作调用只接收当前 section 所需的 global claim / case /
Literature Claim / Literature Evidence / citation metadata / statistics，语义审稿返回
结构化 issue，修订仅重写受影响 section，最多一轮自动
修复。最终 `pass` / `pass_with_warnings` / `review_required` / `fail` 状态由验证与
审稿结果共同决定，不能由写作者自行宣告。

### Canonical artifacts

所有文件位于 `outputs/<job_id>/`，并在 `academic_state.artifacts` 中记录内容 hash、
dependency hash、实现版本与更新时间：

| 文件 | 核心内容 |
|---|---|
| `academic-evidence.json` | 全量项目段落、确定性统计、过程证据与候选案例 |
| `research-model.json` | 研究主题、RQ、理论、方法、分析维度、输入来源状态 |
| `literature-sources.json` | 来源元数据、允许引用状态、内容可用性、精确 source blocks 与哈希 |
| `literature-evidence.jsonl` | Literature Evidence → source / block / exact location / exact text / provenance / hash |
| `literature-claims.jsonl` | Literature Claim → source / supporting evidence / 类型 / 置信度 / 落地状态 |
| `argument-plan.json` | Global Claim → RQ → project evidence / Literature Claim / Literature Evidence / support category |
| `synthetic-error-opportunities.jsonl` | 源文难点、精确 trigger 与可能误读机制 |
| `synthetic-baselines.jsonl` | 分析阶段生成的模拟初译及非历史 provenance |
| `synthetic-error-manifest.jsonl` | 独立 plausibility 结果、错误诊断与实质性 |
| `synthetic-optimized-translations.jsonl` | 针对诊断问题生成的 AI 优化译文 |
| `synthetic-case-validation.jsonl` | 修复正确性/价值、资格结论与拒绝原因 |
| `selected-cases.json` | 经论点相关性与证据完整度选择的案例 |
| `academic-outline.json` | section → purpose/RQ/global claim/case/Literature Claim/Literature Evidence/statistic/允许结论 |
| `academic-sections.json` | 分节正文、摘要、结构化 provenance 与 section dependency hash |
| `academic-validation.json` | 确定性错误、警告与初验/复验历史 |
| `academic-review.json` | 独立语义审稿的结构化 issue |
| `literature-support-review.json` | 文献支持强度、引文语境、释义忠实度与 claim-source 对齐问题 |
| `academic-repair-history.json` | 定点修订章节、issue、前后 hash |
| `academic-evidence-warnings.md` | 面向用户的证据缺口与未解决问题 |

### 失效传播

- 翻译证据变化：重建 project evidence 及其规划下游，但保留文献来源、证据和文献主张。
- RQ 或理论变化：保留 project/literature evidence，失效 research model 与论证下游。
- 文献 metadata 变化：更新 source 与引用/写作下游，不重建逐字 evidence 或 Literature Claim。
- 文献正文、笔记或摘录变化：失效 Literature Evidence、Literature Claim 与论证下游，不重建 project evidence。
- planner/case/outline 版本变化：失效相应规划下游。
- writer 版本变化：保留 evidence、research model、argument plan、cases、outline，
  只失效 sections、validation、review 和 repair history。
- validator/reviewer 版本变化：分别只失效验证或审稿下游。

### 已知限制

- 文献元数据核验状态由导入者提供；本流水线不联网发现或核验 DOI，也不把 metadata-only 来源冒充为落地证据。
- validator 能确定性验证来源、位置、逐字文本、哈希和关系；“释义是否过强”等语义支持问题仍由独立 Literature Support Review 判断。
- 历史任务没有记录的 initial target、术语注入和修复过程无法追溯补建。
- 语义学术审稿仍依赖模型判断；运行时只保证它与写作者分阶段、问题结构化且可定位。

自动验证只能证明来源身份、引用关系、结构和部分一致性；不能证明理论解释在
学术上必然正确，最终提交仍需人工判断。
