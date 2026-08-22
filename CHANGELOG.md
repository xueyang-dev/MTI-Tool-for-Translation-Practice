# Changelog

本文件记录 TransPraxis / 译践 的用户可见变更。当前公开版本为 `v0.2.1`。

## [0.2.1] - 2026-08-22

`v0.2.1` supersedes the earlier public builds and is published from the
scrubbed repository baseline. Earlier tags, releases, and downloadable build
artifacts were withdrawn during the repository-history cleanup.

### Runtime hardening

- Review failures remain non-acceptance and cannot promote reviewed state, translation memory, or knowledge feedback.
- Review, evidence, repair, findings, and persisted state now use unambiguous batch-local ordinals and document-global segment identity; repair review is tied to the exact candidate/input being evaluated.
- Blind review stays independent of formal targets, repair provenance, and prior repair decisions; delivery approval remains document-level human authority rather than fabricated segment acceptance.
- Knowledge observations are bound to verified source/target segments, semantic batching preserves context boundaries, and long-document digest/resume reduction remains bounded and restartable.
- Malformed ranges degrade safely, while checkpoint and Translation Memory recovery remain idempotent across interruption points.
- Uploaded XML rejects entity declarations, and user-controlled labels are escaped before entering custom HTML.

### Packaging and release validation

- Project metadata is versioned as `0.2.1`; the `transpraxis` package, console entrypoint, package resources, and cross-platform launchers are validated from an installed wheel.
- Python 3.10 or newer is required. GitHub Actions validates Python 3.10, 3.11, and 3.12, pytest, sdist/wheel contents, isolated wheel installation, and CLI smoke.
- Runtime dependency floors exclude the vulnerable Starlette 0.x line; dependency auditing reports no known vulnerabilities in the resolved release environment.

### Installation and known limitations

- Use `python -m pip install .` from source or install the `transpraxis-0.2.1` wheel, then run `transpraxis` (or `python gui.py` from source).
- Translation, review, and academic writing require a configured LLM provider. AI-generated translation and reports remain drafts that require appropriate human review for high-stakes or academic submission use.
- `--lan` remains trusted-LAN-only with no authentication; saved provider credentials and local task state remain on the host machine.

## [0.2.0] - 2026-08-22

> Superseded by `v0.2.1`; its public tag and release were withdrawn during repository-history cleanup.

### Highlights

- 统一 TransPraxis / 译践 品牌、Python 包名 `transpraxis` 与 `transpraxis` console entrypoint；补齐 Windows、macOS、Linux 启动器及 package resources。
- 强化确定性文档解析、语义批次与上下文边界，支持长文档的可恢复处理。
- 增加术语治理、范围化术语注入、翻译证据、独立审校、定点修复与 delivery gate，明确区分草稿、审校与最终交付。
- 将 Translation Memory、checkpoint、任务状态、文献证据和学术写作 artifact 绑定到可恢复的本地工作流。
- 完善本地 Streamlit 工作区、provider/model 配置、标准 TBX/TMX/JSONL/manifest 资产导出，以及学术报告的证据约束流程。

### Packaging and support

- 支持 Python 3.9+；源码可通过 `python -m pip install .` 安装，wheel 可直接交给 pip 安装，安装后使用 `transpraxis` 启动。
- 发布验证包括 sdist/wheel 构建、隔离 wheel 安装、console help 和已安装 Streamlit app/resource 定位。

### Known limitations

- 翻译、审校和学术写作需要用户配置相应的远程 LLM provider；生成的实践报告仍是 AI 初稿，理论判断和最终提交必须人工核查。
- `--lan` 是受信任局域网模式，当前没有认证层；它会让其它局域网设备访问共享的本地任务状态与已保存 provider 配置，不应暴露到不受信任网络。
- 本地测试可能产生 PyMuPDF/SwigPy 兼容性告警。
