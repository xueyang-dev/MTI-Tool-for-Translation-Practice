# Phase 1 解释报告（Interpretation）— 人工术语表版

> 只基于实际运行数据。没有合成质量分；无法证明的结论一律不声称。
> 语料：When the Sky Was Ours 前 300 段（28,922 字符）；模型：DeepSeek
> deepseek-chat；TM：真实 3590 条 reviewed TM；单次运行（无温度抽样）。
> 人工术语审核已完成（2026-08）：40 条中 approved=34、rejected=1（Heading）、
> needs_review=5（其中 3 条在确定性全文语料中无出现）；approved_glossary.json
> 由审核表导入，未自动决策。

## 1. Terminology Evidence

### 自动术语表口径（第一轮原结果）

| 指标 | A（基线） | B（治理） | C（基线+TM） | D（治理+TM） |
|---|---|---|---|---|
| 锁定术语采纳率 | 94.9% | 96.6% | 88.1% | 88.1% |
| forbidden 违反 | 0 | 0 | 0 | 0 |
| preserve 失败 | 0 | 0 | 0 | 0 |
| scope 冲突 | 0 | 10 | 0 | 10 |

### 人工术语表口径（零 API 重算，34 条）

| 指标 | A | B | C | D |
|---|---|---|---|---|
| 锁定术语采纳率 | **98.2%** | **98.2%** | **92.9%** | **92.9%** |
| forbidden 违反 | 0 | 0 | 0 | 0 |
| preserve 失败 | 0 | 0 | 0 | 0 |
| scope 冲突 | 0 | 10 | 0 | 10 |

- 自动→人工术语表：A +3.3pp、B +1.6pp、C/D +4.7pp——自动术语表中
  **Heading**（动词用法导致 66.7% 采纳）是主要噪声源，人工排除后各臂
  采纳率普遍上升。
- **A 与 B 的人工口径采纳率相同（98.2%）**：排除争议术语后，治理栈在
  "术语合规生成"上相对旧代码没有额外提升（旧代码本来就整体注入同一份
  锁定术语表）；治理栈的可观测差异转移到了检测层（B/D 标记 10 处冲突）。

## 2. QA / Process Evidence

| 指标 | A | B | C | D |
|---|---|---|---|---|
| blocking（每千字符） | 0.0 | 0.0 | 0.069 | 0.104 |
| actionable（每千字符） | 0.069 | 0.588 | 0.346 | 1.176 |
| 自动修复段数 | 0 | 10 | 0 | 1 |
| 审校通过率 | 99.3% | 97.3% | 100% | 100% |

- B 的 actionable 高于 A：全部 occurrence 检查 + 冲突检测的检测面更宽。
- 注：B 的 10 处 conflict 在人工术语表口径下仍存在——来源不是 Heading，
  而是其余术语的跨段译法不一致（详见 findings_summary.csv / state findings）。

## 3. TM Compatibility Evidence

### 自动术语表（provisional）

3590 条中涉及 373 · compatible 325 · **incompatible 48（占受影响 12.9%）** ·
主要冲突 Heading 23、Knots 10、Squadron 7。

### 人工术语表（正式）

| 指标 | 数值 |
|---|---|
| total reviewed TM | 3590 |
| affected by glossary | 347 |
| compatible | 330 |
| **incompatible** | **17（占受影响 4.9%）** |
| ambiguous / scope_sensitive | 0 / 0 |

主要冲突：Instructor 6/9、Squadron 5/147、Horizon 3/17、Navigator 2/40，
其余各 1 条。Heading 相关 23 条不兼容已随人工拒绝而消失。
48 → 17：约三分之二的"不兼容"是自动术语表自身质量问题，而非 TM 问题。

## 4. Human Review Status

- 术语审核：**已完成**（34 approved / 1 rejected / 5 needs_review）。
- blind_review_packet_v2.csv：80 对，全部有效差异（identical=0），
  类别 random 38 + random_fill 4 + term_dense 15 + repair_review 13 +
  long_dense 10，左位平衡 40/40。
- **80 对盲评尚未填写**：因此本报告不声称
  "Governance improves overall translation quality"，
  只报告机器可观测结果。

## 5. 对七个问题的回答

1. **Governance 是否提高 terminology compliance？**
   人工术语表口径下 A=B=98.2%：治理栈没有带来术语合规生成的额外提升
   （旧代码同样注入锁定术语）。自动口径的 +1.7pp 主要来自 Heading 噪声。
2. **提升主要在 generation 还是 detection/repair？**
   证据指向 **detection/repair**：B 自动修复 10 段、标记 10 冲突；
   generation 层面无可见差异。
3. **TM 是否降低 terminology compliance？**
   是：C/D（92.9%）低于 A/B（98.2%）——历史 TM 中仍有 17 条与人工
   术语表不兼容的译文被复用。
4. **reviewed TM 实际不兼容多少？**
   **17/3590（0.5%），占受影响 4.9%**（人工术语表口径）。
5. **D 进入 review_required 是否合理？**
   合理：TM 复用带入不合规译文时如实暴露（3 blocking + 34 actionable），
   阻止 final，符合设计。
6. **自动与人工 glossary 指标差多少？**
   A +3.3pp、B +1.6pp、C/D +4.7pp（采纳率）；TM 不兼容 48→17。
7. **是否值得全文四臂运行？**
   机器证据已就绪，但**盲评未完成**；先完成 80 对盲评再决定。

## 6. Limitations

- 单次运行、单一模型、单一书、300 段子集；增量是点估计。
- 5 条 needs_review 术语未纳入 approved glossary（3 条在全文语料中
  无出现，待二次终审）。
- TM 兼容性为确定性规则分类；无 scope 条目，scope_sensitive 分类为空。
- 盲评未完成前，任何"整体质量提升"的表述都不可用。

## Recommendation

**READY_FOR_HUMAN_REVIEW**

术语表已人工定稿、机器指标与 TM 审计已按人工术语表重算（零 API）。
剩余唯一阻塞：80 对盲评（packet 与 key 已就绪）。盲评完成后：
若 A/B 无系统性差异且术语/TM 证据支持，再评估 READY_FOR_FULL_DOCUMENT_RUN。
