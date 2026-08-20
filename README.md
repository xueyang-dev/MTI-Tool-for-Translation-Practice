# 🎓 TransPraxis / 译践 (Translation & Report Copilot)

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Ready-red.svg)

**TransPraxis / 译践** 是一款专为 MTI（翻译硕士）与专职译员打造的、基于大语言模型（LLMs）的本地化工作流引擎。致力于解决传统翻译实践中 **“PDF断句稀烂、术语极难统一、实践报告难写”** 的三大痛点。

产品名称固定为 **TransPraxis / 译践**；GitHub 仓库使用 `TransPraxis`，Python 发行包、导入命名空间与启动命令统一使用 `transpraxis`。


## ✨ 核心特性 (Features)

- 📄 **确定性段落重建 (Deterministic Parsing)**：直接读取 PDF 版面结构（块/行/首行缩进）重建自然段落，确定性完成连字符修复、跨页合并、页眉页脚与页码剔除，分段结果稳定可复现，不再依赖大模型自由裁量。
- 🧠 **概念化术语库 (Concept Glossary)**：翻译前自动抽取 30-50 个专业名词生成 Excel 术语库；支持锁定译名（首选/禁止译名强制生效）与保留原文（作者名、机构名等原样保留），翻译中确定性强制合规。
- 🧬 **术语治理与证据追踪 (Terminology Governance)**：新增文档画像（分布式采样首/中/尾，失败仅警告不阻断）、术语候选提取（记录术语在**全部段落**的出现位置与 model_knowledge 证据，默认 candidate 不会自动锁定）、Streamlit 术语审核面板（编辑/锁定/拒绝/保存草稿/冻结），冻结生成版本化 `glossary_hash`，修改后再冻结生成新版本而不会悄悄覆盖旧冻结状态。
- 🎯 **相关术语注入 (Related-Term Injection)**：翻译时只把当前批次**实际出现**的 locked translate / preserve 条目注入 prompt（provisional 仅作受限建议），支持 global / document / section:<id> / segment:<id> 范围与词边界匹配，每批实际注入的术语 entry ID 都写入审计日志。
- 🚦 **交付门禁 (Delivery Gates)**：交付状态 draft → review_required → approved/final；翻译完成但有 blocking 时为 review_required，draft 资产文件名带 `draft_` 前缀，绝不显示为最终交付；支持“标记已人工修复 / 接受风险并说明 / 重新翻译指定段落”，所有人工处理记录（finding ID、动作、说明、时间戳）落盘，只有 blocking 被解决或明确接受后才能进入 final。
- 📦 **标准资产导出 (Standard Assets)**：TBX 术语库、TMX 翻译记忆（仅审校通过且无 blocking/actionable 的段落）、JSONL 双语段落（含 segment_id / glossary_entry_ids / findings / delivery_status）、`delivery_manifest.json` 交付清单，全部带结构校验。
- 🧾 **证据约束型学术写作 (Evidence-Grounded Academic Writing)**：全文项目证据 → 文献来源快照 → 精确文献证据 → Literature Claim → Global Claim → 案例与提纲 → 分节写作 → 确定性验证 → 独立学术/文献支持审稿 → 定点修订。系统区分“论文已登记”和“具体段落支持主张”；metadata-only 文献不会被冒充为落地证据。
- 🔍 **批次翻译 + 独立审校 (Batched Translation & Review)**：按语义批次携带前后文翻译；确定性检查（译文完整性/漏译、占位符/URL/引用标注等保留项、源语残留、锁定术语合规）并自动修复；再由独立审校 pass 检查语义与术语，actionable 建议经复验（含完整性门槛）后自动修正，blocking 问题留待人工确认。
- 🎨 **三色自动标注 (Auto-Marking)**：翻译完成后自动标注学习重点并在双语对照表中同时高亮原文与译文——生僻词/难词、专业名词（特殊译法，含术语表确定性覆盖）、翻译难点句（语序调整、拆合句、文化负载词处理等特别译法）三类颜色可在界面自定义。标注经过确定性过滤：14k 常用词表 + 词形还原、全书词频、单 token 限制、称谓/全常用词短语拦截，避免常用词被滥标为"生僻词"。
- 🧠 **翻译记忆 (Translation Memory)**：审校通过的段落自动入库，后续任务精确命中直接复用，保证跨任务术语与表达一致。
- 📝 **可恢复、可重生成的论文工作区**：研究问题、理论框架、论点、案例、提纲、章节、验证与审稿结果均作为版本化 JSON artifact 落盘；支持整篇、规划、单节、验证和审稿的独立重生成，无需重跑翻译。
- 🛡️ **断点续传和稳定性 (Robustness)**：任务进度实时落盘到本地 `outputs/` 目录，浏览器刷新、电脑重启后都能从断点继续；内置 API 防崩限流策略与重试机制。支持 OpenCode Go（Chat Completions 模型）、DeepSeek、OpenAI、Gemini、OpenRouter、SiliconFlow、Moonshot、Zhipu、Qwen 及任意 OpenAI 兼容中转站，模型可切换并支持连通性测试。
- 🖋️ **产出排版 (Typography)**：生成的 Word 文档默认西文 Times New Roman、中文宋体，可直接用于 MTI 练习排版。

> 📚 实战经验与内部规约（含多次真实事故的根因与防线）见 [docs/经验总结.md](docs/经验总结.md)，改动代码前建议先读。

## 🚀 极速启动 (Quick Start)

### 1. 环境安装
请确保已安装 Python 3.9 或更高版本；虚拟环境与依赖由启动器自动完成，无需手动安装。

### 2. 一键启动（HTML GUI，Windows / macOS / Linux）
同一个 HTML 界面在三个平台共享同一入口：

- **Windows**：双击 `start.bat`
- **macOS**：双击 `start.command`（或终端运行 `./start.sh`）
- **Linux**：终端运行 `./start.sh`

首次运行会自动创建 `venv` 虚拟环境并安装依赖，随后启动本地服务并自动打开界面。
也可手动运行 `python gui.py`：

```bash
python gui.py                    # 自动打开浏览器
python gui.py --browser          # 强制用浏览器打开
python gui.py --no-browser       # 只启动服务，不打开界面
python gui.py --port 9000        # 指定端口（被占用时自动顺延）
```

安装可选依赖后，`gui.py` 会改用原生桌面窗口渲染同一 HTML 界面
（未安装则自动回退浏览器）：

```bash
python -m pip install -r requirements-desktop.txt
```

### 3. 多平台 / 多设备使用
手机、平板或局域网内其它电脑也可以直接使用同一界面：

```bash
python gui.py --lan
```

启动后会打印局域网地址（如 `http://192.168.x.x:8501`），同一 Wi-Fi / 局域网内的
设备用浏览器打开即可，无需安装任何东西。关闭窗口或按 `Ctrl+C` 即停止服务。

### 4. 三种界面预设
- **⚡ 快速**：跳过自动术语抽取与独立审校，保留翻译记忆和基础一致性检查；自动标注、实践报告默认关闭。适合试译、草稿与快速预览。
- **📘 标准（默认）**：自动抽取术语并复用翻译记忆，保留基础一致性检查；候选术语冻结、独立审校、自动标注和实践报告默认关闭。适合日常翻译任务。
- **🎓 学术增强**：自动术语抽取 → 候选审核与冻结 → 翻译 → 独立审校 → 学术证据与实践报告。自动标注仍按需开启。

三种预设下，导入的锁定术语都会直接强制生效，也都可以在后续步骤中调整高级设置和交付内容。

## 📚 使用指南

1. 在左侧边栏配置引擎与 API Key（默认 DeepSeek 官方 API / deepseek-v4-flash），选择模型与翻译预设（快速 / 标准 / 学术增强）。引擎支持 OpenCode Go、DeepSeek、OpenAI、Gemini、OpenRouter、SiliconFlow、Moonshot(Kimi)、Zhipu(GLM)、Qwen(DashScope)，以及任意 **OpenAI /chat/completions 兼容中转站**（填入 base_url + 模型名即可，one-api/new-api 等均可）；点「🔌 测试连接」可先验证 Key 与模型名。
2. （可选）导入术语库或翻译记忆，支持 `.xlsx` / `.csv`（Source/Target 列，可带 Behavior/Status/Preferred/Forbidden）、`.tbx`（Trados MultiTerm 等，导入即锁定）、`.tmx`（Trados / memoQ 导出，并入全局翻译记忆）；或勾选“智能抽取术语库”。
3. （可选）用“风格模板”配置风格与保留规则（学术书面语 / 文学叙事 / 技术文档 / 自定义），规则会注入翻译与审校 prompt，决定译文语气、保留项与标点习惯；标注颜色可自定义。
4. 上传需处理的 PDF/DOCX 文献，点击“开始处理”。
5. 学术增强预设（或手动开启“审核并冻结候选术语”）下，在“术语准备与审核”面板完成候选术语审核（可编辑译名/锁定/拒绝/保存草稿）后点击“冻结术语表并继续翻译”。
6. 所有进度与中间产物保存在本地 `outputs/` 目录（含 `translation_memory.json` 翻译记忆）：刷新页面或重启后，在左侧“本地任务”中选择任务即可继续，无需重新上传。翻译记忆可在「资产与交付」页查看与清空。
7. 翻译完成后，资产面板显示交付状态；blocking 问题需在面板中“标记已人工修复 / 接受风险 / 重新翻译”处理，之后点击“确认交付 (final)”。
8. 在“学术写作设置”中可维护研究问题、分析维度、字数与文献来源注册表；来源可包含受信任的本地 PDF/DOCX/Markdown/TXT 路径、用户笔记或人工摘录。资产面板可沿来源查看证据、Literature Claim、Global Claim、章节和文献支持审校问题。实践报告仍是 AI 初稿；即使验证通过，最终理论判断也必须人工核查。

### 命令行
命令行默认使用 OpenCode Go，并开启自动术语、独立审校、自动标注和实践报告；`--quality` 额外开启严格术语治理：
```bash
export TRANSPRAXIS_API_KEY="你的 API Key"
python scripts/translate_pdf.py "文档.pdf" --target-lang 简体中文 --quality
```

需要低 token 快速翻译时，显式关闭三个可选阶段：

```bash
python scripts/translate_pdf.py "文档.pdf" --no-review --no-report --no-annotate
```

### Python 包安装与发布验证

Release 中的 wheel 或当前源码均可安装，安装后使用 `transpraxis` 启动：

```bash
python -m pip install .
transpraxis
```

维护者可复现执行发布门禁：

```bash
python -m pip install ".[test]"
python -m pytest -q
python -m pip wheel . --no-deps --wheel-dir dist
```

## 🤝 贡献与支持
如果你觉得这个工具拯救了你的发际线，请点一个 ⭐ Star 支持一下！欢迎提交 Issue 或 Pull Request。
