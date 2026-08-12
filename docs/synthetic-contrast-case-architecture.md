# Synthetic Contrast Case 架构

## 现有案例架构审计

1. 真实修订案例由 `academic-evidence.json` 中的真实 segment 表示；候选项现在明确带
   `case_type=authentic_revision` 和 `provenance.historical=true`。
2. 历史身份只存在于项目 segment 的 `initial_target` / `final_target`。合成案例不使用这两个
   字段，而使用 `synthetic_baseline.text` / `optimized_translation.text`。
3. 真实案例资格由 `has_meaningful_revision`、候选挖掘、选案和 validator 共同执行；必须存在
   有意义的历史初译—终译差异。
4. 选案通过 `selected-cases.json` 进入 `case-analysis-plans.json`，再经 outline 的 case ID
   到达 section packet。Writer 只能看到当前节已经选中的结构化案例。
5. Validator 会逐字核对 `SOURCE/INITIAL/TARGET`，并检查正文声称的实际变化是否存在于保存
   的历史 delta；无差异案例不能冒充修订案例。
6. 干净扩展点是同一条 selected case → analysis plan → outline → writer → validator 链；不需要
   第二套学术写作系统，只需让每个 case 带一等 `case_type` 并按类型选择证据和分析契约。

## 分阶段 Synthetic pipeline

```text
真实 Source Corpus
→ synthetic-error-opportunities.jsonl
→ synthetic-baselines.jsonl
→ synthetic-error-manifest.jsonl
→ synthetic-optimized-translations.jsonl
→ synthetic-case-validation.jsonl
→ mixed selected-cases.json
→ case-analysis-plans.json
→ academic outline / writer / validator
```

难点挖掘只把确定性语言信号用于缩小送审 source pool；信号本身不等于难点。Difficulty
Analyzer 必须返回源文中的精确 trigger、具体困难和可能误读机制。无精确 trigger 的机会不会
进入下一阶段。

Baseline Generator 只接收源文、上下文与 difficulty，不接收项目历史初译、项目终译或后续
优化译文。独立 Plausibility Validator 先判断该模拟译文是否可能由具备基本能力的译者产生；
只有 `plausible` 才进入 Error Diagnoser。Optimizer 接收源文、模拟基线、诊断和术语约束；
最后由 Repair Validator 分别判断错误实质性、修复正确性、修复价值及无关意义变化。

错误模式依据另行标注：只有同段 actionable/blocking 审校记录明确引用相同源文 trigger，且
理由与错误类别一致时，才记为 `project_review_pattern`；否则保守记为 `model_inference`。
单个项目审校记录也不支持人类群体频率结论。错误清单中的 `error_id` 必须贯穿 repair
decision 与 optimized translation，链条断裂时最终资格门禁拒绝该案例。

最终资格是结构化合取条件：真实源文、难点落地、基线合理、错误实质且有诊断、优化确实解决
错误、改进有价值、没有无关意义变化。Writer confidence 不能覆盖这个 gate；被拒案例保留在
validation artifact，但不会进入 selected cases。

## Provenance 与学术边界

合成案例的固定结构为：

```json
{
  "case_type": "synthetic_contrast",
  "provenance": {
    "historical": false,
    "generated_for_analysis": true
  }
}
```

正文必须使用 `SYNTHETIC_SOURCE / SIMULATED / OPTIMIZED` 引文标签，DOCX 中显示为“真实
源文 / 模拟初译 / 优化译文”。不得使用“笔者初译为”“经审校后修改为”等历史过程措辞。
Validator 将其报告为 `synthetic_case_presented_as_historical`。没有实证频率证据时，“常见
人类翻译错误”等表述报告为 `unsupported_human_error_frequency_claim`。

使用合成案例时，正文必须公开说明：模拟初译与 AI 优化都为分析阶段生成，不代表作者历史
翻译。局限部分还必须说明：这些案例只展示合理失败模式，不能证明人类译者中的实际发生频率。
混合章节用可见小标题区分“真实修订案例”和“合成对比案例”。

## 选案与分析契约

`case_selection_policy` 支持 `authentic_only`、`synthetic_only`、`mixed`，UI 默认 mixed，
并允许设置总案例上限。Mixed 模式先保留通过资格门禁的真实修订案例，再从 synthetic pool
按学术价值、置信度和错误类别多样性选择剩余案例。统计始终分列：
`authentic_revision_cases` 与 `synthetic_contrast_cases`，不会合并为“修订案例总数”。

真实案例分析链仍是“历史初译 → finding/文本差异 → 实际修订 → 历史终译”。合成案例使用
另一份契约：“翻译难点 → 合理模拟错误 → 错误诱因 → 诊断与失真 → AI 优化 → 修复验证 →
有界结论”。Theory mapping 对两类案例都必须由 Literature Evidence 支持。

## Human Evidence、UI 与生产隔离

Human Evidence 可以记录作者对模拟基线合理性或优化译文偏好的事后判断，但能力字段仍保持
`case_type=synthetic_contrast`、`has_meaningful_revision=false`，不存在 synthetic → authentic
升级路径。

学术工作区对每个 synthetic case 显示 Source、Translation Difficulty、Simulated Initial
Translation、Error Diagnosis、AI-Optimized Translation、Validation 和 Academic Eligibility。
这些 artifact 不写入 `state.pairs`、findings、repair history、术语库、项目终译或 TM。

## 局部失效

五个 synthetic artifact 使用现有 dependency hash 缓存。Difficulty、Baseline、Diagnosis、
Optimizer、Validation 版本分别失效本阶段及其 synthetic/writing 下游；不会失效历史 project
evidence、真实修订候选或 Literature Evidence。翻译源文发生变化时才从 difficulty mining
开始重建。Writer 版本未变时，旧 section 文件仍可作为逐节缓存；每节只依赖它实际引用的
case，方法/局限节另依赖 synthetic 是否启用。因此 synthetic 候选变化会重写案例节和披露节，
但不会仅因全局 selected-cases hash 改变而重写无关章节。

## 能力边界

该机制可以增强错误机制覆盖与对比分析清晰度，但不会增强历史过程证据，也不能据此宣称论文
已经达到提交标准。`model_inference` 表示一种经检查的合理错误构造，不是人类群体行为预测。

## 真实项目运行状态

已对 `ec100d8686d3891e` 启动隔离运行。系统扫描 273 个真实源文段，确定性预筛保留 48 段
交给 Difficulty Analyzer；DeepSeek 随后返回 `402 Insufficient Balance`。最新版评估正确记录
`status=failed` 并以非零状态退出，因此本次的“0 个 opportunity”是 provider 不可用，不是
语料没有翻译难点，也不是 eligibility gate 的学术结论。

失败运行仍证明两项隔离条件：历史 `state.json` 前后保持不变；真实案例 0209、0272 原样
保留。Top synthetic cases、有效拒绝分布和 mixed-case 学术比较必须在 provider 恢复后重新运行，
当前不能据此生成或推断。

2026-08-12 的最终重试仍返回 `402 Insufficient Balance`。评估报告会把该错误显示为运行失败，
并明确说明“零 opportunity”不是语料或资格判断；不会把未发生的 eligibility 决策写成“无拒绝”。
