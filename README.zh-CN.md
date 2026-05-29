<div align="center">

# 🧭 Bensz Auto Contribution

**面向人类-AI 软件协作的篡改可发现贡献归因系统**

[![Release](https://img.shields.io/github/v/tag/huangwb8/bensz-auto-contribution?label=release&color=blue)](https://github.com/huangwb8/bensz-auto-contribution/tags)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![BAC Format](https://img.shields.io/badge/BAC_format-v2-7C3AED.svg)](docs/bac-tutorial.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English](README.md) | [中文](README.zh-CN.md)

</div>

---

## ✨ 项目简介

Bensz Auto Contribution，简称 **BAC**，是面向 AI 编程工具的贡献归因与审计系统。它的核心产物是 `.bac` 文件：一个绑定到具体项目、追加式、篡改可发现的贡献记录，用于区分哪些内容来自人类、哪些来自 AI、哪些来自工具执行，以及开发过程中观察到了哪些证据。

BAC 不声称文件“绝对无法被修改”。它的目标是通过结构化事件、canonical JSON、哈希链、本地 checkpoint、项目上下文绑定，以及为签名和可信时间戳预留的字段，让篡改行为可被发现。

**🌟 核心亮点**：BAC 为 AI 编程会话提供可持续保存的审计轨迹。它帮助团队说明 AI 使用情况、复核协作边界、验证生成内容，并在需要时回溯开发过程，而不是把人类意图、AI 生成、工具输出和文件证据混成一团模糊描述。

### 核心特性

- 🧑‍💻 **人类-AI 贡献归因**：明确区分 `human`、`ai`、`tool`、`system` 四类来源。
- 🧾 **追加式事件模型**：用有序事件记录贡献历史，避免覆盖旧记录。
- 🔗 **哈希链验证**：发现事件内容修改、插入、删除、重复或重排。
- 📦 **单文件 `.bac` 容器**：使用 ZIP-based v2 账本，内部包含 `manifest.json` 和 canonical JSON 事件。
- 🛡️ **清晰安全边界**：定位为 tamper-evident，不夸大成不可修改。
- 🧠 **AI Tool 友好**：面向 Codex CLI、Claude Code 和其它 Agent 编程环境设计。
- 🔍 **证据感知记录**：支持记录文件 hash、git diff 摘要、命令文本、退出码、测试结果和 checkpoint。
- 🧼 **敏感信息脱敏**：默认避免写入密钥、完整私有提示词或无关用户数据。

---

<div align="center">

### ⭐ 如果这个项目对你有帮助，请点个 Star 支持一下！

构建可靠的 AI 协作贡献归因，需要认真设计、测试和威胁建模。你的 Star 能帮助更多开发者发现 BAC。

[![Star History Chart](https://api.star-history.com/svg?repos=huangwb8/bensz-auto-contribution&type=Date)](https://star-history.com/#huangwb8/bensz-auto-contribution&Date)

</div>

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 无运行时第三方依赖

### 安装

```bash
python -m pip install bensz-auto-contribution

# 从源码或开发模式安装
python -m pip install -e .
```

### 基础使用

创建单文件 `.bac` 容器，并写入 genesis event：

```bash
bac init
```

记录人类需求：

```bash
bac record \
  --event-type human_instruction \
  --source-type human \
  --summary "Add BAC verification workflow"
```

记录 AI 生成或实现意图：

```bash
bac record \
  --event-type ai_generation \
  --source-type ai \
  --summary "Implemented hash-chain verifier"
```

记录工具执行结果：

```bash
bac record \
  --event-type test_result \
  --source-type tool \
  --summary "Unit tests passed" \
  --command-text "python -m unittest discover -s tests -v" \
  --exit-code 0
```

记录本地 checkpoint，降低尾部截断风险：

```bash
bac record \
  --event-type checkpoint \
  --source-type system \
  --summary "Local checkpoint"
```

验证完整性：

```bash
bac verify
```

查看贡献时间线：

```bash
bac inspect
```

所有命令都支持 `--root` 指定目标项目根目录，支持 `--bac-file` 指定自定义 `.bac` 路径。`init`、`record`、`verify`、`inspect` 均支持 `--json` 输出，便于 AI tool 或其它自动化流程调用。

## 🧩 BAC 的定位

BAC 是过程记录与辅助审计系统，不是最终贡献裁判。

在 AI 辅助科研、写作和软件开发场景中，BAC 可以记录人类需求、约束、审阅、手写修改、最终批准，也可以记录 AI 草稿、重构建议、生成代码、命令输出、测试、引用检查、构建日志、文件快照和 diff 摘要。

这些记录可以支持 AI 使用披露、内部复核、合规说明和争议回溯。它不会自动判定学术署名、法律归属或最终责任；这些判断仍然需要结合项目制度、机构规则、期刊规范和人工判断。

## 📦 `.bac` 格式

默认文件名为 `project.bac`。从外部看它是一个文件；内部是 ZIP 容器，至少包含：

```text
manifest.json
events/000000000001.json
events/000000000002.json
```

`manifest.json` 记录容器版本、事件格式、项目绑定信息、初始事件 hash 和存储约定。`events/` 下每个文件是一条 canonical JSON 事件，文件名从 `000000000001.json` 开始连续递增。

每条 BAC 事件包含：

- `format`：当前为 `bac.event.v2`
- `event_type`：如 `genesis`、`human_instruction`、`ai_generation`、`tool_command`、`file_change`、`test_result`、`checkpoint`
- `source_type`：固定为 `human`、`ai`、`tool`、`system` 之一
- `trust_level`：固定为 `declared`、`observed`、`signed`、`verified`、`anchored` 之一
- `project`：项目根路径、项目绑定 hash、git remote、commit、branch 和 dirty 状态
- `payload`：摘要、命令、文件快照或事件特定内容
- `evidence`：diff 摘要、文件 hash、命令结果或其它可验证证据
- `redactions`：被脱敏的字段与原因
- `prev_event_hash` 与 `event_hash`：形成可验证哈希链

验证器会检查文件是否为有效 ZIP 容器、内部路径是否重复、事件编号是否连续、manifest 是否与 genesis 事件一致，以及事件哈希链是否可复算。

字段解释和工作原理见 [BAC 工作原理教程](docs/bac-tutorial.md)。

## 🛡️ 安全模型

BAC 是 **tamper-evident**，即篡改可发现；它不是 tamper-proof。

它可以发现常见完整性问题，例如事件内容被编辑、事件缺失、事件重排、ZIP 内部路径重复、事件编号断裂、genesis 元数据不一致、哈希链断裂和 checkpoint 不一致。

如果没有外部 anchor，纯本地哈希链不能完全防止尾部截断。因此 BAC 当前支持本地 checkpoint，并为后续 Ed25519 签名、git note、发布产物、可信时间戳或外部透明日志预留扩展空间。

## 🧪 开发与验证

运行测试：

```bash
python -m pytest -q
python -m unittest discover -s tests -v
```

当前测试覆盖 canonicalization、v2 容器结构、哈希链复算、篡改检测、重复内部路径检测、checkpoint 验证、敏感信息脱敏和 CLI 端到端流程。

本地构建并检查 PyPI 发布包：

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

项目通过 GitHub Actions 和 PyPI Trusted Publishing 发布到 PyPI。详见 [PyPI 发布流程](docs/pypi-release.md)。

## 🗂️ 目录结构

```text
bensz-auto-contribution/
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── README.zh-CN.md
├── docs
│   ├── bac-tutorial.md
│   ├── pypi-release.md
│   └── plans
├── pyproject.toml
├── src
│   └── bac
│       ├── adapters
│       ├── core
│       ├── report
│       ├── service
│       └── storage
└── tests
```

## 🤖 AI 辅助开发

本仓库包含 AI 编程工具项目指令：

- `AGENTS.md` 用于 OpenAI Codex CLI
- `CLAUDE.md` 用于 Claude Code

修改贡献归因逻辑时，需要保持安全边界表述准确：BAC 提供可验证、篡改可发现的记录，不应被描述成无法修改。

## 🤝 贡献

欢迎围绕 `.bac` 文件格式、威胁模型、AI tool 集成、验证逻辑、签名与时间戳、开发者体验提交 Issue 和 Pull Request。

## 📄 许可证

MIT License
