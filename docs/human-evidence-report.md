# 人类证据摄入（Human Evidence Intake）实现与真实评估报告

> 基线提交 `3e043c2` · 新运行
> `eval/academic-quality/ec100d8686d3891e/track-a-humanevidence-20260810T093330Z/`

## 1. 基线提交

本轮开始前 `main` 干净、HEAD=`3e043c2`；所有旧评估产物保留；未重跑翻译；
未做破坏性 Git 操作。

## 2. 证据缺口审计

见 [human-evidence-audit.md](human-evidence-audit.md)。结论：缺口此前以自由
文本（`recommended_human_evidence`）存在，未结构化、未聚合、未分类可恢复性；
case 级失效可通过 `section_key` 实现；已有 `human_actions` 溯源模式可复用。

## 3. Human Author Evidence 设计

新增一等证据类 `HUMAN_AUTHOR_EVIDENCE`（作者事后提供的解释），与
`PROJECT_EVIDENCE`（翻译流程同期记录）、`LITERATURE_EVIDENCE`（学术来源）、
`AUTHOR_ANALYSIS`（学术分析推导）严格区分。HE 永不改写项目记录。

## 4. Human Evidence Need schema

`human-evidence-needs.json`：`need_id / case_id / segment_ids / missing_evidence
/ reason / affected_dimensions / academic_value / recoverability / status`。
需求由 `contract_completion` 的 weak/missing 维度与 `case_analysis_depth`
的 weak/missing 维度聚合生成，同一缺失事实只生成一条 need。

## 5. 问题生成行为

`human-evidence-questions.json` 中的问题由确定性模板生成（无 LLM），每个
问题携带 `source / initial_target / final_target` 上下文，避免让作者重开
项目文件。模板示例：

- translator_rationale：“这里你为什么选择最终这个译法（“{终译}”）？如果采用
  更直白的表达，会损失什么？”
- reader_response：“你预期中文读者从这一句（“{终译}”）获得什么感受或理解？”
- repair_reason：“这段从初译“{初译}”改为“{终译}”，是出于什么考虑？”

## 6. 去重与优先级

- 去重：`(case_id, question_type)` 确定性去重，同案例同类型只问一次；
- 优先级：`critical > high > medium > low`；阻塞 P1 论点的需求为 critical；
- 每案例最多 2 个问题（默认），避免过度盘问。

## 7. 溯源规则

- 用户答案**原文保存**（`answer`），派生学术解释（`derived_interpretation`）
  另行存储且初始为 null；系统不把用户口语改写为更强事实表述；
- `provenance` 记录 `type=user_answer / recorded_at / interface`；
- 答案默认 scope=case，不静默推广为全局原则。

## 8. 证据冲突行为

- “不知道/不记得/没有相关记录/没印象/想不起来”等 → 状态
  `unavailable_after_human_check`，**不生成任何理由**，问题关闭且不再重复问；
- 答案引号文本与已记录 `initial_target` 明显不同 → `conflicted /
  contradicted`，需人工复核；
- 无法核实 → `not_corroborated`（不妄断为假）；
- 支持 `superseded / withdrawn / needs_clarification` 更正路径，历史保留。

## 9. Evidence-Adequacy 集成

`case_capabilities`：`user_confirmed` HE 使
`source_final_only → source_final_plus_author_rationale`，`can_support`
增加 `translator_rationale / decision_reasoning`（有 reader_response 证据时
增加 `reader_response_claim`）；`cannot_support` 相应收窄。能力升级基于
结构化字段而非编造项目历史。

## 10. Stale/Dependency 行为

- HE hash 进入 `argument_dep` 与 `case_analysis_dep`：新 HE → 论点与案例分析
  计划重规划；
- `section_key` 只包含**该节案例的 plans 子集 hash + 该节案例的 HE hash**：
  HE 变化仅使受影响章节重写，未受影响章节复用缓存（测试断言 rewritten ⊆
  {案例所在节}）；
- 原始项目证据、文献证据、无关案例与章节不受影响。

## 11. Writer 行为

writer packet 的 `case_analyses` 携带 plan 的 `human_evidence`（作者原文）与
`human_evidence_ids`；提示词要求：引用 HE 时表述为“作者后来解释/译者后来说
明”，保留 `<!--human-ev:HE-...-->` marker，不得把事后解释写成项目同期过程，
不得推广为全局翻译原则。

## 12. Validator/Reviewer 变化

- 校验未知/不可用/矛盾 HE 的引用（`unknown_human_evidence`、
  `unusable_human_evidence`、`conflicted_human_evidence`、论点级引用检查）；
- quality 状态暴露 `human_evidence_status`（待回答/关键问题/已确认/无法回忆/
  矛盾/证据提升案例数）；
- 存在未解决的 critical 人类问题 → 学术状态 `review_required`。

## 13. UI 变化

学术工作区新增“人类证据收件箱”：显示每个问题的案例、原文、终译、问题、
为什么重要（needs 的理由），提供答案输入框；支持“不记得/没有相关记录”；
提交后状态即时显示（含矛盾提示）。不暴露内部 ID 为主 UX。

## 14. 测试

```text
human_evidence_test.py  5/5 ✅
case_analysis_test.py   5/5 ✅
academic_quality_test.py 7/7 ✅
academic_writing_test.py 4/4 ✅
literature_evidence_spine_test.py 5/5 ✅
smoke_test.py / terminology / red-team 17/17 / app_boot ✅
```

覆盖：需求生成、问题具体性与去重、答案摄入（provenance/原文保留）、
“不知道”、矛盾、能力升级与 case 范围、端到端摄入闭环（问题→答案→重规划→
仅重写受影响章节→写入）、red-team 防护。

## 15. Red-team 结果

- “不记得”不会变成理由：`unavailable_after_human_check` 后能力不升级；
- 用户答案原样保留，`derived_interpretation` 为空（无静默改写）；
- 跨案例引用 HE 被计划器拒绝（human_evidence_ids 校验为空）；
- fixture 摄入路径验证：HE → plan 引用 → 正文 marker → 验证通过。

## 16. 真实问题（0138 / 0152 / 0140）

三个目标案例在本轮运行中未被同时选中（本轮选中 0144/0215/0233/0235/0141/
0007/0059/0139），故基于前两轮真实运行的 plans/quality 为其生成定向问题
（不伪造答案），存于
`human-evidence-questions-target-cases.json`：

| 案例 | 缺失证据 | 可恢复性 | 问题（节选） | 提升维度 | 价值 |
|---|---|---|---|---|---|
| 0138 | translator_rationale | human_recoverable | 这里你为什么选择最终这个译法（“我们走进了阿扎里亚和露丝的房间……”）？ | decision_rationale/bounded_conclusion | high |
| 0138 | reader_response | human_recoverable | 你预期中文读者从这一句获得什么感受或理解？ | translation_effect | high |
| 0140 | translator_rationale | human_recoverable | 这里你为什么选择最终这个译法（“露丝端上咖啡……格瓦（Geva）……”）？ | decision_rationale | high |
| 0140 | reader_response | human_recoverable | 你预期中文读者从这一句获得什么感受或理解？ | translation_effect | high |
| 0152 | translator_rationale | human_recoverable | 这里你为什么选择最终这个译法（“晚饭后，我再次向西穿过Wadi Seder……”）？ | decision_rationale | high |
| 0152 | reader_response | human_recoverable | 你预期中文读者从这一句获得什么感受或理解？ | translation_effect | high |

三个案例均为 `source_final_only` 或仅有弱过程证据：无 actionable finding、
无初译—终译差异（0152 的 `translation_delta.changed=false`），故系统不推断
理由，只问作者。

本轮运行自身生成的 11 个问题（5 个选中证据受限案例 × 1–2）见
`human-evidence-questions.json`，全部为 high 值、带完整上下文。

## 17. 估算人工负担

3 个目标案例共 6 个问题（每案例 2 个，每个一句话），预计作者 10–15 分钟
可完成；“不知道/没有相关记录”可直接作答，不产生额外追问。

## 18. 剩余局限

- 本轮为自动化开发运行：**未向真实作者提问、未把 fixture 答案放入真实论文
  状态**；真实摄入路径由 fixture 测试验证；
- 本轮 writer 在 4 节正文中出现 12 处理论点名（无落地文献），被
  `theory_name_dropping` 捕获并列为 P1——提示词遵从在不同运行间波动，仍需
  更强制约（例如写作后确定性剥离无文献理论句）；
- 写作者自创统计键问题仍存在（本轮 1 个未解析 token）；
- HE 摄入后的真实论文重生成尚未执行（等待作者回答）。

## 19. 提交状态

本轮改动待提交；提交后 HEAD 将前移，工作树干净。

## Fixture 完整链路

```text
Weak Case (seg-academicfixture01-0001, source_final_only)
→ HN-...: translator_rationale（human_recoverable, high）
→ HQ-...: “这里你为什么选择最终这个译法（“终译”）？……”
→ User Answer: “我选这个译法是因为直译会让叙述者显得过于正式……”
→ HE-0001: user_confirmed, answer 原文保存, provenance recorded_at/interface
→ 能力升级: source_final_only → source_final_plus_author_rationale
→ case_analysis_dep 变化 → 案例分析计划重规划（human_evidence_ids=[HE-0001]）
→ section_key(该案例所在节) 变化 → 仅重写该节（测试断言 rewritten ⊆ {节3}）
→ 正文含 <!--human-ev:HE-0001--> 与“作者后来解释：……”
→ 确定性验证通过 → 质量复评
```

## “I don't remember”链路

```text
HQ-... → User Answer: “不记得了。”
→ HE status=unavailable_after_human_check
→ 问题关闭（不再追问）
→ case_capabilities 不变（仍 source_final_only，无 translator_rationale）
→ 不产生任何理由文本，案例保持证据有限
```

## 三个问题的回答

1. **系统现在是否知道自动化推理何时到达证据边界、应向作者请求什么最小信息？**
   是。`contract_completion` + `case_analysis_depth` 的 weak/missing 维度被
   聚合为结构化 need（类型/可恢复性/影响维度/价值），只对 `human_recoverable`
   且高价值的缺口生成 1–2 个带上下文的具体问题；`system_recoverable`、
   `historically_unrecoverable`、`not_worth_requesting` 不打扰作者。
2. **用户答案能否在不被误述为项目历史证据的前提下改善学术推理？**
   能。答案原文保存并带 provenance；能力升级只改变 `can_support`
   （`source_final_plus_author_rationale`），不触碰 `initial_target` 等项目
   记录；writer 只能以“作者后来解释”表述并保留 marker；矛盾答案被标记
   `conflicted` 且不可用于写作；“不记得”不产生理由。
3. **真实剩余弱案例实际需要多少个人类问题？**
   9 个案例维度缺口收敛为 3 个案例 × 2 个问题 = **6 个问题**（全部 high 值：
   每案例 1 个 translator_rationale + 1 个 reader_response）。若作者表示
   “不记得”，问题立即关闭，案例保持证据有限，不会重复追问。

> 本报告不声称论文达到提交标准；HE 摄入的真实作者回答尚未发生，论文仍处
> 于需要作者/导师人工输入与复核的阶段。
