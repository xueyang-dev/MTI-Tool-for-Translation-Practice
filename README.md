# 🎓 MTI 翻译实践小助手 (Translation & Report Copilot)

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Ready-red.svg)

**MTI 翻译实践小助手** 是一款专为 MTI（翻译硕士）与专职译员打造的、基于大语言模型（LLMs）的本地化工作流引擎。致力于解决传统翻译实践中 **“PDF断句稀烂、术语极难统一、实践报告难写”** 的三大痛点。

## ✨ 核心特性 (Features)

- 📄 **结构清洗 (AI Parsing)**：利用大模型消除 PDF 提取带来的硬回车与乱码，尽量还原自然段落。
- 🧠 **概念化术语库 (Concept Glossary)**：翻译前自动抽取 30-50 个专业名词生成 Excel 术语库；支持锁定译名（首选/禁止译名强制生效）与保留原文（作者名、机构名等原样保留），翻译中确定性强制合规。
- 🔍 **批次翻译 + 独立审校 (Batched Translation & Review)**：按语义批次携带前后文翻译；确定性检查（占位符/URL/引用标注等保留项、源语残留、锁定术语合规）并自动修复；再由独立审校 pass 检查语义与术语，actionable 问题复验后自动修正，blocking 问题留待人工确认。
- 🧠 **翻译记忆 (Translation Memory)**：审校通过的段落自动入库，后续任务精确命中直接复用，保证跨任务术语与表达一致。
- 📝 **翻译实践报告生成 (Agentic Report Generation)**：基于 Map-Reduce 架构，分四轮自动撰写包含“长难句学理分析”的数千字 Markdown/Word 翻译实践报告初稿。
- 🛡️ **断点续传和稳定性 (Robustness)**：任务进度实时落盘到本地 `outputs/` 目录，浏览器刷新、电脑重启后都能从断点继续；内置 API 防崩限流策略与重试机制。支持 DeepSeek、OpenAI、Gemini，模型可切换。

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

## 📚 使用指南

1. 在左侧边栏配置您的 API Key（推荐使用 DeepSeek 或 Gemini），并选择模型。
2. （可选）上传您的自定义 Excel 术语库（支持 Source/Target 必选列，以及 Behavior/Status/Preferred/Forbidden 等概念化列），或勾选“智能抽取术语库”。
3. （可选）在“风格与保留规则”中维护项目级风格；按需关闭“独立审校”可跳过审校与翻译记忆（会更快但质量保障降低）。
4. 上传需处理的 PDF/DOCX 文献，点击“开始处理”。
5. 所有进度与中间产物保存在本地 `outputs/` 目录（含 `translation_memory.json` 翻译记忆）：刷新页面或重启后，在左侧“本地任务”中选择任务即可继续，无需重新上传。
6. 在页面下方“资产面板”随时下载清洗好的原文、双语对照表、实践报告与审查报告；blocking/actionable 问题会显示在审查报告中。不需要的任务可一键删除（同时清除本地进度）。

## 🤝 贡献与支持
如果你觉得这个工具拯救了你的发际线，请点一个 ⭐ Star 支持一下！欢迎提交 Issue 或 Pull Request。
