# Human Evidence Intake 现状审计

> 基线 `3e043c2`。审计对象：`case_analysis.py`、`academic_writer.py`、
> `academic_quality.py`、`academic_validator.py`、`academic_evidence.py`。

## 1. 缺失证据如何表示

- 案例级：`case-analysis-plans.json` 的每个 plan 有 `evidence_level`
  （rich/partial/source_final_only）、`can_support`/`cannot_support`、
  `translation_delta`、`contract_completion`（10 组件 strong/adequate/weak/
  missing/not_applicable）。
- 缺口描述：`plan.recommended_human_evidence` 为自由文本列表（例如
  “需要确认审校建议是否被采纳”），未结构化，无法去重、无法映射到维度、
  无法驱动提问优先级。
- 质量层：`case_analysis_depth` 的 weak 维度带 reason，但不回写为 need。

## 2. 多个弱维度是否指向同一缺失事实

- 目前不聚合。`decision_rationale=weak`、`translation_effect=weak`、
  `bounded_conclusion=weak` 可能同源于“缺少译者理由”，但三者各自产生
  reason，未合并为一条 need。

## 3. 是否区分证据缺失与模型不确定

- 区分。`evidence_level` 与 `cannot_support` 是确定性能力约束；
  `contract_completion` 的 weak/missing 来自规划器判断。两者并存但无显式
  “可恢复性”分类（human_recoverable / system_recoverable /
  historically_unrecoverable / not_worth_requesting）。

## 4. 下游能否 case 级失效

- 可以，通过现有 `section_key`（含 plan/claims/cases/literature/
  case_analysis hash）。若在 section_key 中加入“该节案例的 human evidence
  hash”，HE 变化只使受影响 section 的 key 失效；未受影响 section 复用缓存。
- `case_analysis_plans` 是单 artifact，HE 变化可整体重规划（1 次 LLM）。
- 原始项目证据与文献证据不受影响（依赖 hash 不含 HE）。

## 5. 已有用户交互/溯源模式

- `state["human_actions"]`：翻译交付流程的人工记录（actor/action/note/
  timestamp），可复用其 provenance 风格；
- `state["human_read_log"]` 类字段（文献阅读记录）也按“用户确认+时间戳”
  保存。新证据类应遵循相同持久化约定（state 内列表 + 原子写）。

## 6. 结论

需要新增：结构化 Evidence Need（类型/可恢复性/影响维度/价值）、问题生成
（去重+优先级+上下文）、HE 摄入（原文保存/状态机/不知道/矛盾）、能力升级
（source_final_only → +translator_rationale）、case 级失效（section_key 加
HE hash）、冲突验证与质量状态暴露。现有架构可自然承载，无需新框架。
