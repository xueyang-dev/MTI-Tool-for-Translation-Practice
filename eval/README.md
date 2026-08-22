# TransPraxis Evaluation Harness

评测工具用于比较术语治理、翻译记忆、审校和交付流程的可观测差异。仓库只包含工具代码与合成 fixture；本地任务、源文、译文、翻译记忆和盲评映射均不得提交。

## 使用

```bash
# 离线自测
.venv/bin/python eval/self_test.py

# 使用本地任务进行评测；任务 ID、API key 和输出目录仅在本机配置
TRANSPRAXIS_EVAL_API_KEY=your-key .venv/bin/python eval/run_ab.py \
    --config eval/config.example.json
```

发布的配置示例不包含任务 ID。需要评测本地任务时，在未提交的配置文件中填写
`corpus.job_id`，或通过命令行传入本地任务参数。

评测结果统一写入被 Git 忽略的 `eval/results/`；盲评 key、源文、译文、TM 和抽样正文只保存在本地。

## 评测范围

- 术语采纳、禁止译名、保留项和范围冲突；
- blocking / actionable / informational 发现与自动修复；
- 翻译记忆复用、审校通过率和交付状态；
- 合成 fixture 上的盲评采样、指标聚合与报告生成。

评测结果只描述可计算指标，不替代人工翻译质量判断，也不构成任何特定项目的报告结论。
