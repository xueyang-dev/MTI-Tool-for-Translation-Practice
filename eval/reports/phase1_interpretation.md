# Phase 1 解释报告（Interpretation）

> 只基于实际运行数据。没有合成质量分；无法证明的结论一律不声称。
> 语料：When the Sky Was Ours 前 300 段（28,922 字符）；模型：DeepSeek
> deepseek-chat；术语表：40 条自动导出并锁定（**未经人工审核**）；
> TM：真实 3590 条 reviewed TM；单次运行（无温度抽样）。

## 1. Terminology Evidence

| 指标 | A（基线） | B（治理） | C（基线+TM） | D（治理+TM） |
|---|---|---|---|---|
| 锁定术语采纳率 | 94.9% | 96.6% | 88.1% | 88.1% |
| forbidden 违反 | 0 | 0 | 0 | 0 |
| preserve 失败 | 0 | 0 | 0 | 0 |
| scope 冲突 | 0 | 10 | 0 | 10 |

- A→B：采纳率 +1.7pp；B 额外标记 10 处跨段术语冲突并自动修复 10 段。
- C/D：95% 复用历史 TM 后采纳率降至 88.1% —— 历史 reviewed TM 与当前
  自动锁定术语表不兼容（详见 TM Compatibility Evidence）。
- 注意：自动术语表不是 ground truth（如 Horizon→地平线、Heading→航向的
  低采纳可能含合法上下文变体），数字是诊断不是判决。

## 2. QA / Process Evidence

| 指标 | A | B | C | D |
|---|---|---|---|---|
| blocking（每千字符） | 0.0 | 0.0 | 0.069 | 0.104 |
| actionable（每千字符） | 0.069 | 0.588 | 0.346 | 1.176 |
| 自动修复段数 | 0 | 10 | 0 | 1 |
| 审校通过率 | 99.3% | 97.3% | 100% | 100% |

- B 的 actionable 高于 A：治理栈（全部 occurrence 检查 + 冲突检测）检测面更宽，
  这是 detection 层的工作证据，不代表生成质量下降。
- D 的 actionable 最高：TM 复用带入的历史不合规译文被逐段暴露。

## 3. TM Compatibility Evidence（provisional：自动术语表，人工决策未定）

- 总数 3590 · 涉及术语 373 · compatible 325 · **incompatible 48** ·
  ambiguous 0 · scope_sensitive 0 · 受影响中不兼容率 **12.9%**
- 主要冲突术语：Heading 23/29、Knots 10/10、Squadron 7/147、
  Instructor 6/9、Horizon 5/17、Artificial horizon 3/3、Control tower 3/13
- 结论（provisional）：历史 reviewed TM 与自动锁定术语表存在系统性不一致，
  集中在航向/速度/军语类术语；人工术语表确定后需重算。
- 历史生态证据（history.py）：TM 消毒后 3590 条全部可信、无截断条目；
  历史任务中有 95+20 段 incomplete suspects（e4947f1e/fc221c）——治理栈要
  覆盖的真实失败模式。

## 4. Human Review Status

- blind_review_packet_v2.csv：80 对，全部为有效差异对（identical=0）；
  类别分布：random 38 + random_fill 4 + term_dense 15 + repair_review 13 +
  long_dense 10；Candidate A/B 左位平衡 40/40。
- key 文件 local-only；评审指南 BLIND_REVIEW_GUIDE.md 已生成。
- **人工评审尚未填写**：因此本报告**不声称**
  "Governance improves overall translation quality"，
  只报告机器可观测结果。

## 5. 对七个问题的回答

1. **Governance 是否提高 terminology compliance？**
   自动术语表口径下 +1.7pp（94.9%→96.6%），且冲突被显式检测。点估计，需
   人工术语表 + 多次运行确认。
2. **提升主要在 generation 还是 detection/repair？**
   主要证据在 detection/repair：B 自动修复 10 段、标记 10 冲突；generation
   增量（+1.7pp）在 300 段内微弱。结论：第一轮证据支持
   "检测/修复层提升" 而非 "生成层大幅提升"。
3. **TM 是否降低 terminology compliance？**
   是：C/D 采纳率 88.1%，低于 A（94.9%）。历史 TM 按旧 provisional 术语
   体系积累，与新的锁定术语表不一致。
4. **reviewed TM 实际不兼容多少？**
   provisional：48/3590（1.3%），占受影响条目 12.9%。人工术语表审核后重算。
5. **D 进入 review_required 是否合理？**
   合理。TM 复用引入不合规译文，系统如实暴露（3 blocking + 34 actionable），
   阻止 final——这是治理栈期望行为，不是故障。
6. **自动与人工 glossary 指标差多少？**
   **pending human glossary decisions**（term_audit.csv 未填写），不伪造。
7. **是否值得全文四臂运行？**
   否。盲评未完成、术语表未人工审核；先在 300 段上完成两者再决定。

## 6. Limitations

- 单次运行、单一模型、单一书、300 段子集；增量是点估计。
- 自动术语表未经人工审核，采纳率口径本身待定。
- TM 兼容性为确定性规则分类，无法确定的已归 ambiguous（当前 0 条，因为
  自动术语表全为 global scope 且无原文保留型命中）；scope_sensitive 分类
  需人工术语表提供 scope 后才会有意义。
- 盲评未完成前，任何"整体质量提升"的表述都不可用。

## Recommendation

**READY_FOR_HUMAN_REVIEW**

先完成：(1) term_audit.csv 人工 decision；(2) 80 对盲评。两者完成后，
用 approved_glossary 重算（零 API），再评估是否 READY_FOR_FULL_DOCUMENT_RUN。
