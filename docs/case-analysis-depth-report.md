# 案例分析推理深度改造报告（真实任务评估）

> 基线提交 `ef16a87` · 新运行
> `eval/academic-quality/ec100d8686d3891e/track-a-deepreason-20260810T085020Z/`
> 对比旧运行 `track-a-20260810T054231Z/`。

## 1. 基线提交

- 本轮开始前 `main` 干净，HEAD=`ef16a87`；旧评估产物未改动。
- 本轮新增：`transpraxis/case_analysis.py`（Analysis Contract、translation
  delta、evidence adequacy、规划器）、`tests/case_analysis_test.py`、
  `docs/case-analysis-audit.md`；扩展 `academic_writer.py`（案例分析规划
  阶段、结构化 writer packet 与推理修复动作）与 `academic_quality.py`
  （分析深度 7 维评估、策略标签/空泛效果/伪造过程/过度外推/理论点名诊断、
  段落角色细分）。

## 2. 剩余推理失败审计

审计见 [case-analysis-audit.md](case-analysis-audit.md)。旧第 3 章的核心
失败：7062 字符但 0 个逐字引文块；全部案例停留在“审校建议”层面；每段同构
“理论视角→XX优先”模板；大量未标注的反事实假设；正文纯文本提及 4 个非选中
案例段号；有修复链的 `seg-0144` 未展示差异链。

## 3. Analysis Contract 设计

`case_analysis.ANALYSIS_CONTRACT` 定义 10 个推理组件（问题、困难证据、
初始方案/失败、备选方案、最终决策、决策理由、翻译效果、理论连接、证据
边界、有界结论）。它作为**语义契约**写入 `case-analysis-plans.json`，
writer 只接收 `analysis_contract_text`，不要求十个段落机械排列。规划器为
每个选中案例输出结构化 plan，并做确定性校验：

- 证据贫乏案例（`source_final_only`）的 `problem.grounded` 强制为 false、
  `initial_failure` 置空、`historical_alternative` 降级为
  `analytical_comparison`；
- 无落地文献时 `theory_mapping` 置 null、`theory_connection_status` 为
  `not_applicable`；
- `translation_effect` 必须同时给出维度与 `demonstrated_by` 文本依据。

## 4. 证据充分性行为

`evidence_adequacy` 确定性分类：

| 级别 | 可支持 | 不可支持 |
|---|---|---|
| rich_process_evidence | 文本分析/决策/修订推理/错误-修复分析 | — |
| partial_process_evidence | 文本分析/决策/有限过程推断 | 历史修订推理 |
| source_final_only | 文本分析/译者解释/理论分析 | 历史修订推理/过程断言/初始失败推理 |

真实运行 8 个选中案例中 3 个 `source_final_only`（0138/0152/0007 等），
其分析被明确限定，未出现“译者最初考虑/机器翻译失败因为”类断言
（`unsupported_process_claim_count = 0`）。

## 5. Translation Delta 行为

`translation_delta` 对初译—终译差异做确定性文本 diff（词级替换、结构增删、
finding 链接、修复链接）。真实运行中 3 个有初译—终译差异的案例（0139/0144/
0215）在 plan 中携带 delta，写作者在第 3 章展示了
`源文引文块 → 初译引文块 → finding → 备选 → 终译` 的完整链条；其余案例
明确说明“初译与终译一致，过程差异不可用”。

## 6. 理论-案例映射行为

Track A 无落地文献，`theory_mapping` 全部为 `not_applicable`，正文
`theory_name_dropping_count = 0`（旧运行第 3 章通篇“功能对等视角”标签）。
Track B fixture 运行仍验证 grounded 文献链（上一轮已提交）。本轮新增
`same_theory_reused_mechanically` 检测：若全部映射案例共用同一概念则告警。

## 7. Writer 变化

结构化 packet 新增 `case_analyses`（plan + contract 文本 + 完成度）与
`writing_constraints.analysis_contract`；系统提示词要求：先问题后证据、
备选必须标注标签、效果必须指明维度与文本特征、理论仅在 mapping 存在时
提及、结论限于本案例、禁止 packet 外段号、证据不足时明说并列出人工证据。
修复提示词支持 9 种推理动作（补问题分析/补过程证据/缩小论点/机制替换
策略标签/补理论映射/补效果解释/删除伪造历史/降级无据质量判断/限定结论）。

## 8. 推理质量诊断

确定性 + 语义双层诊断（metrics）：

```text
strategy_label_only_count             0
unsupported_quality_effect_count      0
unsupported_process_claim_count       0
overgeneralized_case_conclusion_count 0
theory_name_dropping_count            0
```

深度评估（`case_analysis_depth`，8 案例 7 维度）：

| 维度 | strong | adequate | weak | not_applicable |
|---|---|---|---|---|
| problem_definition | 3 | 3 | 2 | 0 |
| evidence_use | 0 | 6 | 2 | 0 |
| initial_failure_or_alternative | 3 | 2 | 1 | 2 |
| decision_rationale | 0 | 1 | 5 | 2 |
| translation_effect | 0 | 2 | 4 | 2 |
| theory_mapping | 0 | 1 | 2 | 5 |
| bounded_conclusion | 3 | 3 | 2 | 0 |

weak 维度均带证据化理由（如“initial_target 未记录，无法对比初译与终译”、
“审校建议是否被采纳未记录，效果无法验证”），不是空泛评分。

## 9. 结构化修复行为

修复轮按 plan/issue 的 `repair_action` 处理；重写时合并当前确定性验证
错误；修复历史记录 before/after hash 与动作。真实运行质量修复 2 轮，
替换轮次为 0（候选池无更强案例时正确停止，不再乒乓）。

## 10. 证据丰富建议

每个证据不足的案例在 `case-analysis-plans.json` 输出
`recommended_human_evidence`。真实运行示例：

- 0215：需确认审校建议是否被采纳、终译是否保留原文专名；
- 0140/0141：需初译记录或审校决策动机说明；
- 0138/0152：需该段的具体翻译问题说明或过程记录。

UI（学术工作区）新增“案例分析计划与质量”展开器，展示每个案例的
evidence level、问题及 grounded 状态、效果维度、理论状态、深度维度状态
与人工证据需求。

## 11. 测试

```text
case_analysis_test.py        5/5 ✅（delta/adequacy/诊断/空洞游戏化/证据贫乏/推理修复 E2E）
academic_quality_test.py     7/7 ✅
academic_writing_test.py     4/4 ✅
literature_evidence_spine_test.py 5/5 ✅
smoke_test.py                ✅
terminology_governance_test.py ✅
red_team_acceptance_test.py  17/17 ✅
app_boot_test.py             ✅
```

防游戏化测试覆盖：包含全部分析标题但内容空洞的段落被判
`decision_rationale=weak`；带“问题：句子很难/理由：它很复杂/策略：意译/
效果：更自然”的 vacuous 分析在 7 个维度全 weak。

## 12. 真实评估结果

新运行（`track-a-deepreason-20260810T085020Z`）：273 段、8 选中案例、
3 RQ 全覆盖、6 claim 无孤立、泛化段率 0、文献 `evidence_missing`
（诚实，无落地文献）。确定性验证按调整后规则重验为 1 error
（写作者自创统计键 `{{STAT:coverage_distribution}}` 等 12 处残留，
模型侧真实瓶颈）+ 3 warnings。

## 13. 第 3 章前后对比

| 指标 | 旧运行 | 新运行 |
|---|---|---|
| 章节长度 | 7062 | 6003 |
| 逐字引文块 | 0 | 4 |
| 非选中案例提及 | 4 个（234/170/56/119） | 0 |
| 反事实/备选标注 | 无 | 有（counterfactual_rendering 等） |
| 效果维度+文本依据 | 无 | 有（terminological_precision 等） |
| 理论点名 | 通篇“功能对等视角” | 0（无文献即不点名） |
| 策略标签无机制 | 有（P1 指认） | 0 |
| 证据边界/人工建议 | 少量重复声明 | 每案例显式列出 |
| 有界结论 | 部分 | 每案例 3.1.3/3.2.3 结构 |
| 验证错误（调整规则后） | 2 | 1 |

## 14. 3 个最强案例分析

- `seg-0215`（Atlit/Rabbits Hideaway/Chair Hill 专名）：问题定义 strong、
  初译/终译引文齐备、finding 原文引用、备选标注
  `counterfactual_rendering`、效果维度 terminological_precision 且给出
  “应保留原文”文本依据、结论限定于审校建议层面并列出人工证据。
- `seg-0139`（outstretched hand 隐喻）：7 维度中 6 个 adequate/strong，
  展示父子对话语境与“回避了我的请求”调整，理论映射 adequate。
- `seg-0144`（长难句截断）：问题定义与初始失败 strong，引文链完整，
  结论限定本案例。

## 15. 3 个最弱案例分析

- `seg-0138` / `seg-0152`：`source_final_only`，问题定义与证据使用 weak；
  系统诚实降级（未编造过程），并给出人工证据建议——属**证据稀缺失败**。
- `seg-0140`：问题/证据 adequate，但决策理由与效果 weak——审校建议是否
  被采纳未记录，系统明确写“无法进一步断言实际效果”——属**证据稀缺失败**
  （非模型推理失败）。

## 16. 剩余证据局限

- 12 处写作者自创统计键（`source_chars_0144` 等）残留，修复轮未根除；
- 3 个 `source_final_only` 案例无法产生过程性分析；
- 无落地文献，理论映射整体 not_applicable；
- 全部案例的“效果”止于审校建议层面，无读者反应数据。

## 17. 工作树/提交状态

本轮改动待提交（工作树含新增文件与扩展）。提交后 HEAD 将前移。

## 三个问题的回答

1. **第 3 章是否因为模型写得更长而改善？** 否。章节从 7062 字符缩短到
   6003，但引文块从 0→4、反事实/备选从无到有、理论点名从通篇到 0、
   效果判断从空泛到“维度+文本依据”。改善来自**结构化推理（plan→writer）
   与证据约束（adequacy gate、引用校验、禁止 packet 外段号）**，不是更
   冗长的散文。
2. **剩余弱案例是模型推理失败还是证据稀缺？** 8 个案例中，2 个
   （0138/0152）和 1 个（0140 的效果/理由）是证据稀缺失败——系统已诚实
   降级并给出人工证据建议；没有案例属于“模型编造失败”。weak 维度均带
   证据化理由。
3. **下一瓶颈是自动化推理还是人工输入？** 人工学术输入现在是最高杠杆：
   剩余弱维度全部需要补初译记录、审校采纳状态或读者反应数据；自动化能
   做的是继续收窄写作者自创统计键等模型侧细节。报告**不构成
   submission-ready**，需导师/作者人工复核后进入下一轮。
