# 🎓 MTI 翻译实践小助手 (Translation & Report Copilot)

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Ready-red.svg)

**MTI 翻译实践小助手** 是一款专为 MTI（翻译硕士）与专职译员打造的、基于大语言模型（LLMs）的本地化工作流引擎。致力于解决传统翻译实践中 **“PDF断句稀烂、术语极难统一、实践报告难写”** 的三大痛点。

## ✨ 核心特性 (Features)

- 📄 **确定性段落重建 (Deterministic Parsing)**：直接读取 PDF 版面结构（块/行/首行缩进）重建自然段落，确定性完成连字符修复、跨页合并、页眉页脚与页码剔除，分段结果稳定可复现，不再依赖大模型自由裁量。
- 🧠 **概念化术语库 (Concept Glossary)**：翻译前自动抽取 30-50 个专业名词生成 Excel 术语库；支持锁定译名（首选/禁止译名强制生效）与保留原文（作者名、机构名等原样保留），翻译中确定性强制合规。
- 🧬 **术语治理与证据追踪 (Terminology Governance)**：新增文档画像（分布式采样首/中/尾，失败仅警告不阻断）、术语候选提取（记录术语在**全部段落**的出现位置与 model_knowledge 证据，默认 candidate 不会自动锁定）、Streamlit 术语审核面板（编辑/锁定/拒绝/保存草稿/冻结），冻结生成版本化 `glossary_hash`，修改后再冻结生成新版本而不会悄悄覆盖旧冻结状态。
- 🎯 **相关术语注入 (Related-Term Injection)**：翻译时只把当前批次**实际出现**的 locked translate / preserve 条目注入 prompt（provisional 仅作受限建议），支持 global / document / section:<id> / segment:<id> 范围与词边界匹配，每批实际注入的术语 entry ID 都写入审计日志。
- 🚦 **交付门禁 (Delivery Gates)**：交付状态 draft → review_required → approved/final；翻译完成但有 blocking 时为 review_required，draft 资产文件名带 `draft_` 前缀，绝不显示为最终交付；支持“标记已人工修复 / 接受风险并说明 / 重新翻译指定段落”，所有人工处理记录（finding ID、动作、说明、时间戳）落盘，只有 blocking 被解决或明确接受后才能进入 final。
- 📦 **标准资产导出 (Standard Assets)**：TBX 术语库、TMX 翻译记忆（仅审校通过且无 blocking/actionable 的段落）、JSONL 双语段落（含 segment_id / glossary_entry_ids / findings / delivery_status）、`delivery_manifest.json` 交付清单，全部带结构校验。
- 🧾 **证据约束型学术写作 (Evidence-Grounded Academic Writing)**：全文项目证据 → 文献来源快照 → 精确文献证据 → Literature Claim → Global Claim → 案例与提纲 → 分节写作 → 确定性验证 → 独立学术/文献支持审稿 → 定点修订。系统区分“论文已登记”和“具体段落支持主张”；metadata-only 文献不会被冒充为落地证据。
- 🔍 **批次翻译 + 独立审校 (Batched Translation & Review)**：按语义批次携带前后文翻译；确定性检查（译文完整性/漏译、占位符/URL/引用标注等保留项、源语残留、锁定术语合规）并自动修复；再由独立审校 pass 检查语义与术语，actionable 建议经复验（含完整性门槛）后自动修正，blocking 问题留待人工确认。
- 🎨 **三色自动标注 (Auto-Marking)**：翻译完成后自动标注学习重点并在双语对照表中同时高亮原文与译文——生僻词/难词标红，专业名词（特殊译法，含术语表确定性覆盖）标黄，翻译难点句（语序调整、拆合句、文化负载词处理等特别译法）标青绿。标注经过确定性过滤：14k 常用词表 + 词形还原、全书词频、单 token 限制、称谓/全常用词短语拦截，避免常用词被滥标为"生僻词"。
- 🧠 **翻译记忆 (Translation Memory)**：审校通过的段落自动入库，后续任务精确命中直接复用，保证跨任务术语与表达一致。
- 📝 **可恢复、可重生成的论文工作区**：研究问题、理论框架、论点、案例、提纲、章节、验证与审稿结果均作为版本化 JSON artifact 落盘；支持整篇、规划、单节、验证和审稿的独立重生成，无需重跑翻译。
- 🛡️ **断点续传和稳定性 (Robustness)**：任务进度实时落盘到本地 `outputs/` 目录，浏览器刷新、电脑重启后都能从断点继续；内置 API 防崩限流策略与重试机制。支持 DeepSeek、OpenAI、Gemini，模型可切换。
- 🖋️ **产出排版 (Typography)**：生成的 Word 文档默认西文 Times New Roman、中文宋体，可直接用于 MTI 练习排版。

> 📚 实战经验与内部规约（含多次真实事故的根因与防线）见 [docs/经验总结.md](docs/经验总结.md)，改动代码前建议先读。

## 🚀 极速启动 (Quick Start)

### 1. 环境安装
请确保已安装 Python 3.9 或更高版本。

- **Windows**：直接双击项目目录下的 `start.bat` 即可一键启动，首次运行会自动创建虚拟环境并安装依赖。
- **macOS / Linux**：在终端中运行：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 2. 运行程序
Windows 用户直接双击 `start.bat`；其他系统执行 `streamlit run app.py` 后浏览器会自动打开。

### 3. 两种翻译模式
- **快速模式（默认）**：自动术语作为 provisional 建议直接翻译，体验与旧版一致。
- **高质量模式**：文档画像 → 术语候选提取 → **人工审核与冻结** → 相关术语注入 → 翻译。术语未冻结时「开始翻译」按钮不可执行，并明确显示原因；刷新/重启后自动恢复到术语审核阶段，不会重新抽取。

## 📚 使用指南

1. 在左侧边栏配置您的 API Key（推荐使用 DeepSeek 或 Gemini），选择模型与翻译模式（快速 / 高质量）。
2. （可选）上传您的自定义 Excel 术语库（支持 Source/Target 必选列，以及 Behavior/Status/Preferred/Forbidden 等概念化列），或勾选“智能抽取术语库”。
3. （可选）在“风格与保留规则”中维护项目级风格；按需关闭“独立审校”可跳过审校与翻译记忆（会更快但质量保障降低）。
4. 上传需处理的 PDF/DOCX 文献，点击“开始处理”。
5. 高质量模式下，在“术语准备与审核”面板完成术语审核（可编辑译名/锁定/拒绝/保存草稿）后点击“冻结术语表并继续翻译”。
6. 所有进度与中间产物保存在本地 `outputs/` 目录（含 `translation_memory.json` 翻译记忆）：刷新页面或重启后，在左侧“本地任务”中选择任务即可继续，无需重新上传。
7. 翻译完成后，资产面板显示交付状态；blocking 问题需在面板中“标记已人工修复 / 接受风险 / 重新翻译”处理，之后点击“确认交付 (final)”。
8. 在“学术写作设置”中可维护研究问题、分析维度、字数与文献来源注册表；来源可包含受信任的本地 PDF/DOCX/Markdown/TXT 路径、用户笔记或人工摘录。资产面板可沿来源查看证据、Literature Claim、Global Claim、章节和文献支持审校问题。实践报告仍是 AI 初稿；即使验证通过，最终理论判断也必须人工核查。

### 命令行
`scripts/translate_pdf.py` 支持 `--quality` 开启高质量模式（术语冻结后才开始翻译），默认快速模式：
```bash
python scripts/translate_pdf.py "文档.pdf" --target-lang 简体中文 --quality
```

## 🤝 贡献与支持
如果你觉得这个工具拯救了你的发际线，请点一个 ⭐ Star 支持一下！欢迎提交 Issue 或 Pull Request。
