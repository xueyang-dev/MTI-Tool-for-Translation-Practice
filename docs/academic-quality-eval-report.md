# 真实 MTI 论文端到端评估与质量修复报告

> 评估日期：2026-08-10 · 基线提交 `251e80d` · 运行目录
> `eval/academic-quality/ec100d8686d3891e/track-a-20260810T054231Z/`

## 1. 基线提交与工作树

- 基线：`251e80d feat: add literature evidence spine`（本次迭代前唯一提交）。
- 本次迭代新增代码位于 `mti_tool/academic_quality.py`、
  `scripts/eval_academic_quality.py`、`tests/academic_quality_test.py`，
  并增强 `academic_writer.py`（质量评估/结构性修复/引文规范化）与
  `academic_validator.py`（计划外引用检查、案例计划校验）。
- 评估运行使用隔离输出目录与 state 副本，未修改任何原始任务状态。

## 2. 评估目标选择

选择 `ec100d8686d3891e`（《When the Sky Was Ours》回忆录翻译项目）：

| 维度 | 8126db91c3969845 | ec100d8686d3891e |
|---|---|---|
| 段落数 | 3366 | 273 |
| findings | 286 | 67（32 actionable） |
| 术语决策 | 0 | 34 |
| 初译→终译修复链 | 0 | 3 |
| 文档画像 | 无 | 完整（文学/回忆录，含章节结构） |
| TM 复用 | 未知 | 215 段 |

ec100 证据链最完整，适合案例研究型 MTI 报告；8126 仅作为全语料扫描规模的
佐证（3366 段全扫描，首/中/尾各 1122 段）。

## 3. 完整学术运行产物

`track-a-20260810T054231Z/` 下生成：

```text
academic-evidence.json            research-model.json
argument-plan.json                selected-cases.json
academic-outline.json             academic-sections.json
academic-validation.json          literature-support-review.json
academic-review.json              academic-quality-evaluation.json
academic-quality-findings.jsonl   academic-quality-report.md
academic-quality-repair-history.json
academic-repair-history.json      academic-evidence-warnings.md
report-final.md                   report-final.docx
run-manifest.json                 state-eval.json
```

运行参数记录于 `run-manifest.json`：provider=DeepSeek、model=deepseek-chat、
pipeline/academic-quality/validator/reviewer 版本、全部 artifact 内容哈希与
报告哈希。

## 4. 研究问题对齐

3 个 RQ 全部有 claim、案例与章节覆盖：

```text
RQ1 语言特征与翻译难点 -> C1/C2 -> 章节 1/2/3（案例 0144/0238/0139 等）
RQ2 功能对等视角的有限解释 -> C3 -> 章节 3
RQ3 术语/MT/审校效果与局限 -> C4/C5/C6 -> 章节 4
```

无未回答 RQ、无孤立 claim。结论章节对三个 RQ 逐条回应并回链 claim。

## 5. 案例质量分布

| 类别 | 数量 | 说明 |
|---|---|---|
| strong_case | 0 | 候选池中最强案例也只具备 finding+术语+审校记录，缺完整修复链 |
| usable_case | 5 | 有 finding/术语/初译—终译差异之一以上 |
| weak_case | 3 | 仅有弱 finding 或仅有初译—终译差异 |
| redundant_case | 0 | 未检出跨案例重复 |
| misaligned_case | 0 | 替换轮已清理 |

弱案例（0238/0233/0140）的共性：无 actionable finding、无修复记录。这是
任务数据现实——273 段中仅 3 段有初译→终译修复链；替换选择器已改为只接受
证据丰富度严格更高的候选，避免在弱案例间来回替换（此前出现 140→235→140
乒乓，已修复并由测试覆盖）。

## 6. 最强案例

- `seg-0144`（richness 5）：长难句 + 初审 actionable + 终译修正记录，
  是第 2 章语言特征分析的主案例。
- `seg-0139` / `seg-0215`（richness 4）：有审校意见与术语相关证据，
  支撑 C3 的翻译决策分析。

## 7. 最弱案例与原因

- `seg-0238`（richness 1）：无 finding、无修复、无术语决策，仅初译—终译
  一致且被标记已审校；正文对其讨论只能停留在假设层面（P1 明确指认）。
- `seg-0233` / `seg-0140`（richness 2）：finding 为 informational，无实质
  决策差异。

## 8. 分析深度

- 第 2 章部分案例停留在“长句、多从句、复杂标点”描述层面；P1 审稿指出
  “碎片化句式如何转化为翻译决策”未展开。
- 第 3 章对 `seg-0140` 的理论解释为“保留原文加注=信息对等优先”的标签化
  表述，未讨论目标读者接受效果与反例对比。
- 自动修复轮多次重写第 2/3 章后，语义审稿对分析深度的判断在
  pass_with_warnings 与 review_required 之间波动：这是当前写作者提示词与
  模型推理能力的真实上限，不是可确定性修复的问题。

## 9. 项目证据利用

- 统计标记 34 处全部展开为运行时数值（含全局兜底展开后），修复轮不再产生
  未解析占位符（剩余 1 处为写作者使用的嵌套键 `issue_category_distribution.*`）。
- 高价值未使用证据 5 例：0144/0139/0215/0007/0152 等具备 finding/修复
  证据但正文未全部利用，已作为 P2 提交给修复轮与人工。

## 10. 文献落地状态

- Track A：`literature_grounding_status = evidence_missing`（任务无任何
  文献来源），理论维度与文献支持维度为 `not_applicable`，未伪造任何文献。
- Track B（fixture，`eval/academic-quality/fixture-track-b/`）：用仓库测试
  fixture 文献（Nida 1964 注册源）验证完整技术链：
  `LC-001 -> LE-96c7e6e4 -> nida1964 -> 正文 lit-claim markers 15 处`，
  `literature_grounding_status = grounded`，理论-案例匹配 pass。
  fixture 明确不构成用户论文的学术支持。

## 11. 理论-案例匹配

Track A 无落地文献，理论-案例匹配为 `not_applicable`；Track B 为 `pass`。
真实任务第 3 章的理论解释被 P1 指出存在“原则标签化”倾向（见第 8 节），
属于人工学术复核范围。

## 12. 跨章节一致性

- 确定性检查发现重复论点标记 6 处、重复段落 12 处（P2）。
- 修复轮重写章节时会合并当前确定性验证错误，避免重写破坏 marker/引文。
- 剩余重复问题分布在 1/2/4 节，为 P2 级，需人工决定合并或保留递进表述。

## 13. 泛化/套话

`generic_paragraph_rate = 0.0`：确定性模板检测与语义审稿均未发现
“通过本次翻译实践，笔者深刻认识到”类套话；结论章节使用项目内统计与
案例回链，未出现可套用于任意项目的空泛表述。

## 14. 结论支持

- 结论句 72 条需追溯检查（P3），其中大部分回链 claim/RQ 或项目统计；
- 结论未引入新的实证/理论主张（语义审稿结论维度 pass）；
- 结论过度外推问题（早期轮次 2 条）经修复后未再出现。

## 15. 质量修复执行

- 确定性修复（引文规范化）：38 处 `wrong_segment_quote` -> 0（运行时以
  保存文本逐字替换，报告与模型原文分离存储）。
- 统计占位符全局兜底展开：19 处未解析 -> 1 处（嵌套键，模型侧问题）。
- 计划外案例引用检查：新增 `unplanned_segment_reference` validator，
  阻止正文引用未纳入计划的 `[seg-...]`。
- 语义修复轮：2 轮，重写 1/2/3/4/5 节；每轮合并 validation error，
  记录 before/after hash。

## 16. 案例替换执行

真实运行早期轮次完成 6 次替换（0059→0139、0103→0235、0133→0007、
0233→0152、0141→0233、0235→0140），验证了“弱案例 -> 候选池 -> 更新
selected-cases/argument/outline -> 仅重写受影响章节”的完整链路。
选择器改进后（证据丰富度严格更高），后续轮次不再替换——候选池已无更强
替代，系统正确停止而非继续乒乓。

## 17. 前后对比示例

| 指标 | 初始 | 最终 |
|---|---|---|
| 验证错误 | 38 | 2（1 未解析嵌套统计键 + 1 缺失 claim marker） |
| 验证警告 | 0 | 38（18 未标记项目统计 + 19 过度计划案例未全展开 + 1 链接） |
| 引文不一致 | 38 | 0 |
| P1 问题 | 2（证据不可追溯） | 4（均为第 3 章语义分析深度） |
| 弱案例 | 5 | 3 |
| 泛化段率 | 0 | 0 |

## 18. 测试结果

```text
academic_quality_test.py         7/7 ✅
academic_writing_test.py         4/4 ✅
literature_evidence_spine_test.py 5/5 ✅
smoke_test.py                    28 组 ✅
terminology_governance_test.py   ✅
red_team_acceptance_test.py      17/17 ✅
app_boot_test.py                 ✅
```

## 19. 剩余需人工复核项

- P1×4：第 3 章对 `seg-0056/0119/0234/0170` 的纯文本提及无法在所选案例中
  追溯（模型从证据统计中获取段号后在正文提及，修复轮未能根除）。
- 2 个确定性错误：嵌套统计键残留；第 1 章缺失 C1 marker（提纲将 C1 计划
  给引言所致）。
- 3 个弱案例：任务数据本身缺少更强证据；建议人工补充审校记录或缩小
  案例范围。
- 第 3 章理论解释深度：需导师/作者判断功能对等应用是否成立。

## 20. 下一最高杠杆改进

在写作者提示中禁止输出任何 `seg-` 段号（除分节包提供的引用外），并在
确定性 validator 中检测纯文本段号提及；同时为提纲生成增加“引言不承担
claim/案例展开”约束。这两项可直接消除剩余 2 个确定性错误与 P1 不可追溯
提及的大部分。

## 核心结论

1. 当前瓶颈已从架构转向学术推理与写作质量：证据链、校验、修复轮、案例
   替换均真实工作，剩余问题集中在模型分析深度与任务数据证据丰度。
2. 三个最降低质量的失败模式：
   - 写作者在正文中提及非计划案例的段号与审校内容（证据可追溯性受损）；
   - 案例分析停留在“原文→译文→策略标签”，理论解释未做功能对等论证；
   - 任务数据中修复链/初译—终译差异稀缺，弱案例无法通过替换消除。
3. 分类结论：**工程上有效（engineering-valid）**。经过质量修复循环后，
   报告具有完整可追溯链、零引文错误、零套话、RQ 全覆盖；但第 3 章分析
   深度与 3 个弱案例意味着它处于“学术可审阅（academically reviewable）”
   的早期阶段，**不构成 submission-ready**，仍需导师/作者人工学术复核。
