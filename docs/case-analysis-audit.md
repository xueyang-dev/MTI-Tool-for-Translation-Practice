# 案例分析推理深度审计（真实任务 ec100d8686d3891e）

> 审计对象：`eval/academic-quality/ec100d8686d3891e/track-a-20260810T054231Z/`
> 的 `academic-sections.json` 第 3 章与 `academic-quality-evaluation.json` 的
> P1 findings（4 条 weak_analysis，全部指向第 3 章）。

## 现状事实

- 第 3 章 7062 字符、4 个小节，但 `SOURCE/TARGET` 引文块数量为 0：所有案例
  分析都没有展示原文、初译或终译的逐字文本。
- 正文以纯文本提及 `seg-234/170/144/152/139/56/119`，其中 234/170/56/119
  不在 `selected_cases`（8 个案例）中，无法在项目证据中追溯。
- 全部案例均属“审校建议层面”，没有一例展示
  `源文 → 初译 → finding → 修复 → 终译` 的链条；唯一有修复链的
  `seg-144` 未被用作链条展示。
- 大量“若直译为……译文读者需要额外进行语用推理”的反事实假设，未标注为
  分析性对比（counterfactual rendering）。
- 理论解释为统一模板：“从功能对等理论的视角看，这一调整体现了对
  XX（信息对等/效果对等/语义准确性）优先性的落实”，未绑定具体
  源语特征 → 目标语功能需求 → 变换机制的映射。

## 失败模式分类（基于上述证据）

| 类别 | 证据 | 严重度 |
|---|---|---|
| `evidence_presentation_missing` | 引文块为 0，读者无法核实案例 | 高 |
| `strategy_label_only` / `theory_label_only` | 每案例同构“XX策略→更自然/更准确”或“理论视角→XX优先” | 高 |
| `unmarked_counterfactual` | “若直译则语义悬空”未标注为反事实对比 | 中 |
| `unsupported_process_claim` | 部分过程表述（如审校未采纳）未标明证据来源（139 例外） | 中 |
| `missing_translation_delta` | 有初译/终译差异的 144 未展示差异链 | 高 |
| `weak_theory_connection` | 理论概念宽泛套用，无机制映射 | 高 |
| `overgeneralized_case_conclusion` | 3.4 从局部案例外推“回忆录文体对翻译的约束” | 中 |
| `repetitive_structure` | 四小节同构模板，大量重复限制性声明 | 低 |
| `unplanned_segment_mention` | 正文纯文本提及非选中案例段号 | 高 |

## 本轮改造目标

1. 每个案例分析前先生成结构化分析计划（问题/证据/备选/理由/效果/理论映射/
   有界结论），由 writer 实现而非即兴发挥。
2. 案例分析必须展示逐字证据（引文块）与可用的初译—终译差异。
3. 反事实与备选方案必须显式标注，不得伪装成过程历史。
4. 证据不足时输出 `recommended_human_evidence`，不得编造过程或意图。
5. 理论连接必须给出概念 ↔ 源语特征 ↔ 目标语功能需求的映射；无落地文献时
   禁止理论点名。
