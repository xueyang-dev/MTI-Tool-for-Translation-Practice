# TransPraxis / 译践 Evaluation Harness（评测工具）

目标不是"证明新版更好"，而是建立一套以后每次改 prompt、模型、TM、术语策略
都能重复使用的评测工具。第一轮实验用 `outputs/` 里的真实书
（When the Sky Was Ours）做语料，**所有真实数据严格 local-only**。

## 两条证据轨道（禁止混成一个 leaderboard）

### 1. 受控 A/B/C/D（`run_ab.py`）

| Run | 代码 | Governance | Reviewed TM |
|---|---|---|---|
| A | pre-governance（`b4ae9ac` worktree） | 无 | 无 |
| B | current（quality mode：画像/冻结/相关注入） | 有 | 无 |
| C | pre-governance | 无 | 有 |
| D | current + quality mode | 有 | 有 |

四臂共用同一 provider / model / temperature（代码内固定）/ 批次参数 /
TM policy；TM 有无完全由种子控制（C/D 注入 `outputs/translation_memory.json`）。

可回答：A→B 治理增量；A→C reviewed TM 增量；B→D 治理之上再加 TM；
A→D 完整新工作流 vs 裸基线。

### 2. 历史生态证据（`history.py`，只读）

回答：真实书籍规模下历史任务暴露什么问题；新系统是否覆盖已知 failure modes；
3590 条真实 reviewed TM 能否安全加载；新 pipeline 能否在历史资产上工作。
只读 `outputs/`，不修改历史任务。

## 使用

```bash
# 离线自测（合成 fixture + 确定性 mock，不访问网络）
.venv/bin/python eval/self_test.py

# 真实评测（需要 TRANSPRAXIS_EVAL_API_KEY；默认子集 [0,300)）
TRANSPRAXIS_EVAL_API_KEY=sk-... .venv/bin/python eval/run_ab.py \
    --config eval/config.example.json

# 指定子集 / 全文 / 指定臂
.venv/bin/python eval/run_ab.py --config ... --segments 0:500
.venv/bin/python eval/run_ab.py --config ... --segments all --arms BD

# 从历史任务导出术语表（local-only；--lock 会明确标注"未经人工审核"）
.venv/bin/python eval/run_ab.py --config ... \
    --glossary-from-job 8126db91c3969845 --lock
```

输出统一写入 `eval/results/<ts>/`：

- `evaluation-report.json`：多维指标（terminology / qa / workflow / human_review）
  与臂间增量；**没有**单一 quality_score；
- `evaluation-report.md` / `terms_adoption.csv` / `findings_summary.csv`；
- `blind_review/`：盲评抽样包（约 80 段）与 key 文件（映射关系，local-only）。

## 盲评协议（人工评审在机器评测之后）

抽样结构：40 随机 + 10 术语密集 + 10 曾触发 repair/review + 10 长句/高信息密度
+ 10 跨段上下文依赖，去重后 ≤80 段。每段随机映射为 Candidate A / Candidate B，
评审者不知道哪个是 quality；映射关系只在 `blind_review_key.csv`（local-only）。
错误类型学字段：terminology / fidelity / fluency / omission / comment + 整体偏好。
至少一位双语评审；要升级证据等级再加独立第二人。

## 指标定义（全部从 state 计算，四臂同代码）

- `terminology.locked_term_adoption_rate`：锁定 translate 术语出现段中采用首选
  译名的比例（词边界匹配）；`forbidden_term_violations` / `preserve_failures` /
  `scope_conflicts` 同理；
- `qa.blocking|actionable|informational_per_1k_chars`：按源文本千字符归一；
  `automatic_repair_rate` = 初译≠终译的非 TM 段比例；
- `workflow.review_pass_rate` / `retranslation_rate` / `tm_reuse_rate` /
  `stale_segments`。

## 数据卫生（硬性规定）

- 真实语料（source.bin、译文、TM、抽样正文）只出现在 `eval/results/`
  与 `eval/.worktrees/`（均 gitignored）；
- 入库的只有：工具代码、聚合指标、合成 fixture；
- A 臂通过 git worktree 固定到 `b4ae9ac`，不拷贝旧代码到仓库。

## 已知边界

- `metrics/reference.py` 只留接口：第一轮不做参考译文指标（文学翻译中参考译文
  不是唯一正确答案；且需要可靠段落对齐）。配置了 references 会明确报错；
- `--glossary-from-job --lock` 是自动化锁定，未经人工审核——正式结论前应改用
  人工审核过的术语表 JSON；
- mock LLM 只用于 harness 自测，绝不进入真实评测；
- 第一轮默认 300 段子集控成本，信号确认后再跑全文。
