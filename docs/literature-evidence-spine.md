# 文献证据脊柱：现状审计与增量方案

## 审计范围

本审计沿真实运行链检查 `app.py -> core.generate_mti_report -> academic_writer.run_academic_pipeline -> academic_evidence / academic_validator`，并只读检查了 `outputs/*/state.json` 与现有学术产物。

## 当前实现能做到什么

1. 文献由侧栏 JSON 注册表进入，状态随任务保存在 `state.literature_sources`。
2. `academic_evidence.normalize_literature_registry` 目前保存 `source_id`、题名、作者、年份、简化 citation 元数据、概念、自由文本 notes、来源状态、是否允许引用和一个 verification 字段。
3. `academic-evidence.json` 把上述来源列表放在名为 `literature_evidence` 的字段中；这里实际是“来源元数据”，不是可定位的文献证据。
4. 论证规划器只拿到来源注册表，并把 `literature_evidence` 记录成 `source_id` 列表。来源存在即被当作论点支持关系，缺少“文献主张”和“原文证据”两层。
5. 提纲只分配 `source_id`；分节写作包只获得该来源的元数据、notes 和 citation 信息，拿不到可核对原文、页码/行号、证据哈希或受支持的文献主张。
6. 确定性校验可以拒绝未知来源、禁止引用状态及明显作者/年份错配，也可以要求正式引用携带 registry key；它不能证明正文观点确实由来源中的某个段落支持。
7. 通用语义审稿把来源 ID 与项目段落 ID 混在 `evidence_ids` 中，无法单独检查“主张强于原文”“断章取义”“有引文但不支持”等文献特有问题。
8. 当前历史任务没有 `literature_sources` 字段，也没有既存学术产物；因此只能诚实迁移为“无文献注册/无文献落地证据”，不能从旧报告反推或伪造文献支持。

## 核心漏洞

- “论文存在”与“论文支持当前主张”被合并为同一判断。
- `literature_evidence` 名称与内容不符，来源注册表被误当成证据库。
- 没有稳定的文献证据 ID、精确位置、原文/笔记来源、内容哈希和可验证状态。
- 没有独立的 Literature Claim，Global Claim 直接引用来源 ID，无法表达支持强度和边界。
- 写作者没有获得受限的原文证据包，模型记忆或 notes 可能被误写成来源结论。
- 校验器无法做引文逐字匹配、位置有效性、来源内容变更、章节越界引用和 claim-evidence 关系校验。
- 文献变更只有一个总哈希，不能区分 metadata、content、evidence、claim 的精确失效范围。
- 当前总质量状态没有分别暴露文献元数据、文献落地、论证支持和文献支持审校。

## 增量解决方案

在现有流水线中加入一条窄而完整的文献证据脊柱，不引入检索系统、向量库或文献管理器：

```text
Literature Source
  -> Literature Evidence（逐字文本/用户笔记 + 精确位置 + 哈希）
  -> Literature Claim（受哪些证据支持、强度与边界）
  -> Global Claim（项目证据/文献支持/混合证据/作者分析）
  -> Academic Section（只获得本节计划内的证据包）
```

具体做法：

1. 将 `academic-evidence.json` 中的注册项改名为 `literature_sources`，读取时兼容旧字段。
2. 新增规范化 `literature-evidence.jsonl` 与 `literature-claims.jsonl`，JSONL 文件为可检查交换面，state 中的 artifact 记录仍是唯一版本与依赖索引。
3. 只从用户明确提供的内嵌正文、笔记、人工摘录或可信本地文件提取；保留原文、来源、精确位置、provenance 和内容哈希。只有元数据时明确标记 `metadata_only/evidence_missing`。
4. 让论证计划引用 Literature Claim ID 和 Literature Evidence ID；只有 source ID 的旧规划不得计作文献落地支持。
5. 分节写作包仅传本节 Literature Claims、对应证据和 citation 元数据，并使用隐藏 provenance marker 绑定段落；导出的 Markdown/DOCX 隐藏内部 marker。
6. 扩展确定性校验，覆盖来源—证据—文献主张—全局主张—章节的引用完整性、逐字引文、位置、哈希、元数据、越界引用与允许引用状态。
7. 新增独立、低温、结构化的 Literature Support Review；问题只能定向映射到 Literature Claim、Global Claim 和章节，修复轮次有上限且记录前后哈希。
8. 分离 `literature_sources_version`、`literature_evidence_version`、`literature_claims_version`，让文献内容变化只失效文献下游，不重建翻译项目证据。
9. 学术总状态由项目证据、文献元数据、文献落地、论证支持、引用校验、文献支持审校共同汇总，缺少原文时保守地给出 warning/review_required，而不是假装已验证。

## 明确不做

- 不联网发现文献，不做 RAG、向量数据库、Zotero 集成或通用文献管理。
- 不从模型记忆补作者、年份、书名、原文或页码。
- 不为了该纵向改造重写翻译证据、研究模型或项目案例选择架构。
