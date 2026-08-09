# 学术写作子系统：现状审计与迁移设计

## 当前流水线

当前阶段三由 `core.run_job_pipeline` 调用 `core.generate_mti_report`。后者从
`report_evidence.evidence_text_block` 取得从第 0 段开始、最多约 9000 字符的
连续双语前缀，分别调用四个章节 prompt，再把返回文本拼成 Markdown。
`p3_sections` 负责章节级断点续写，`p3_done` 表示四章已生成，`p3_md` 用于
Streamlit 展示和 `markdown_to_word` 导出 DOCX。

## 当前状态模型

任务状态保存在 `outputs/<job_id>/state.json`。与学术写作有关的字段只有
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
→ Research Model
→ Argument Plan
→ Case Selection
→ Academic Outline
→ Section Writing
→ Deterministic Validation
→ Semantic Review
→ Targeted Repair
```

实现采用三个职责模块：证据与候选挖掘、学术编排与版本依赖、确定性验证。
每个阶段输出独立 JSON artifact，并在 `academic_state` 中记录内容 hash、版本、
状态和失效原因。写作调用只接收当前 section 所需的 claim / case / literature /
statistics，语义审稿返回结构化 issue，修订仅重写受影响 section，最多一轮自动
修复。最终 `pass` / `pass_with_warnings` / `review_required` / `fail` 状态由验证与
审稿结果共同决定，不能由写作者自行宣告。

### Canonical artifacts

所有文件位于 `outputs/<job_id>/`，并在 `academic_state.artifacts` 中记录内容 hash、
dependency hash、实现版本与更新时间：

| 文件 | 核心内容 |
|---|---|
| `academic-evidence.json` | PROJECT/LITERATURE/AUTHOR 三类证据、全量段落、确定性统计、候选案例 |
| `research-model.json` | 研究主题、RQ、理论、方法、分析维度、输入来源状态 |
| `argument-plan.json` | claim → RQ → project/literature evidence → planned section |
| `selected-cases.json` | 经论点相关性与证据完整度选择的案例 |
| `academic-outline.json` | section → purpose/RQ/claim/case/literature/statistic/允许结论 |
| `academic-sections.json` | 分节正文、摘要与 section dependency hash |
| `academic-validation.json` | 确定性错误、警告与初验/复验历史 |
| `academic-review.json` | 独立语义审稿的结构化 issue |
| `academic-repair-history.json` | 定点修订章节、issue、前后 hash |
| `academic-evidence-warnings.md` | 面向用户的证据缺口与未解决问题 |

### 失效传播

- 翻译证据变化：重建 evidence，并通过 dependency hash 重建规划和正文。
- RQ、理论或文献变化：保留翻译 evidence，失效 research model 下游。
- planner/case/outline 版本变化：失效相应规划下游。
- writer 版本变化：保留 evidence、research model、argument plan、cases、outline，
  只失效 sections、validation、review 和 repair history。
- validator/reviewer 版本变化：分别只失效验证或审稿下游。

### 已知限制

- literature registry 的 `verified` 状态由导入者提供；本迭代不联网核验 DOI 或全文。
- validator 能验证引用身份和登记元数据，但不能证明文献内容确实支持全部语义主张。
- 历史任务没有记录的 initial target、术语注入和修复过程无法追溯补建。
- 语义学术审稿仍依赖模型判断；运行时只保证它与写作者分阶段、问题结构化且可定位。

自动验证只能证明来源身份、引用关系、结构和部分一致性；不能证明理论解释在
学术上必然正确，最终提交仍需人工判断。
