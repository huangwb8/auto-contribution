# bensz-auto-contribution

`bensz-auto-contribution` 是 `bensz auto contribution` 的原型项目，目标是为 AI 编程工具提供一个可调用的 tool，用来创建和验证 `.bac` 文件。

`.bac` 文件用于记录某个具体项目里人类与 AI 的贡献边界。它应该忠实记录需求来源、AI 生成内容、工具执行结果、人工确认、文件改动与验证证据，并通过哈希链、签名和追加式事件模型让篡改行为可发现。

## 定位

BAC 是一个过程记录与辅助审计系统，不是最终贡献裁判。它的核心价值是忠实记录协作过程中哪些步骤来自人类、哪些步骤来自 AI、哪些结果来自工具执行，以及这些步骤发生时的项目上下文和验证证据。

在论文写作等 AI-人类协作场景中，BAC 可以用于记录人类提出研究问题、写作约束、审阅意见和最终确认，记录 AI 生成草稿、修改建议、润色方案和重构内容，也记录引用检查、编译、测试、diff 摘要等工具证据。这些记录可以帮助团队进行投稿合规说明、AI 使用披露、内部审计和争议回溯。

BAC 不自动判定最终学术作者身份，也不声称能完全还原真实智力贡献。论文作者贡献通常涉及思想来源、实验设计、论证责任、人工审阅和伦理合规等复杂判断，应由项目团队、期刊规范或相关机构结合 BAC 记录和其它材料共同确认。

## 特性

- 贡献归因：区分 human、ai、tool、system 等来源
- 追加式记录：避免覆盖历史事件，保留贡献时间线
- 篡改可发现：通过摘要链、签名和上下文绑定验证 `.bac` 完整性
- 项目绑定：将贡献记录关联到仓库状态、文件路径和操作证据
- AI tool 集成：面向 Codex、Claude Code 等 AI 编程环境设计调用接口

## 快速开始

### 环境要求

- Python 3.10+
- 无运行时第三方依赖

### 安装

```bash
python -m pip install -e .
```

### 使用

```bash
# 创建单文件 project.bac 容器，并写入 genesis event
bac init

# 记录人类需求
bac record \
  --event-type human_instruction \
  --source-type human \
  --summary "Add BAC verification workflow"

# 记录 AI 生成或修改意图
bac record \
  --event-type ai_generation \
  --source-type ai \
  --summary "Implemented hash-chain verifier"

# 记录工具命令结果
bac record \
  --event-type test_result \
  --source-type tool \
  --summary "Unit tests passed" \
  --command-text "python -m unittest discover -s tests -v" \
  --exit-code 0

# 记录本地 checkpoint，降低尾部截断风险
bac record \
  --event-type checkpoint \
  --source-type system \
  --summary "Local checkpoint"

# 验证 .bac 完整性
bac verify

# 查看贡献时间线
bac inspect
```

所有命令都支持 `--root` 指定项目根目录，支持 `--bac-file` 指定 `.bac` 文件路径。`init`、`record`、`verify`、`inspect` 均支持 `--json` 输出，便于 AI tool 或其它自动化流程调用。

## 设计边界

- `.bac` 记录协作过程和证据，不替代论文署名、作者贡献声明或学术责任判断
- `.bac` 的安全目标是 tamper-evident，即篡改可发现，不宣称文件本身绝对无法被修改
- `.bac` 不应记录敏感密钥、完整私有提示词或无关用户隐私
- 任何 AI 贡献记录都应尽量关联实际 diff、命令输出、测试结果或用户确认
- 涉及签名、哈希、身份和时间戳的逻辑必须有测试覆盖
- 当前 v2 支持单文件 ZIP 容器、未签名事件、哈希链验证、本地 checkpoint 和敏感信息脱敏；Ed25519 签名与外部可信时间戳保留为后续扩展

## `.bac` 格式

默认文件名为 `project.bac`。外部表现为一个 `.bac` 文件，内部是 ZIP 容器，至少包含：

```text
manifest.json
events/000000000001.json
events/000000000002.json
```

`manifest.json` 记录容器版本、事件格式、项目绑定信息、初始事件 hash 和存储约定。`events/` 下每个文件是一条 canonical JSON 事件，文件名从 `000000000001.json` 开始连续递增。验证器会检查容器是否为有效 ZIP、内部路径是否重复、事件编号是否连续、manifest 是否与 genesis 事件一致，以及事件哈希链是否完整。

每条事件包含：

- `format`：固定为 `bac.event.v2`
- `event_type`：如 `genesis`、`human_instruction`、`ai_generation`、`tool_command`、`file_change`、`test_result`、`checkpoint`
- `source_type`：固定区分 `human`、`ai`、`tool`、`system`
- `trust_level`：区分 `declared`、`observed`、`signed`、`verified`、`anchored`
- `project`：记录项目根路径、项目绑定 hash、git remote、commit、branch 和 dirty 状态
- `payload`：记录摘要、命令、文件快照等事件内容
- `evidence`：记录 diff 摘要、文件摘要等可验证证据
- `redactions`：记录脱敏字段和原因
- `prev_event_hash` 与 `event_hash`：形成可复算哈希链

`event_hash` 基于排序后的 canonical JSON 计算，可发现历史事件内容修改、插入、删除中间事件和重排。ZIP 只提供单文件封装，不被描述为物理不可篡改；BAC 的安全目标仍然是通过容器结构、事件序列、哈希链和 checkpoint 实现 tamper-evident。没有外部 anchor 时，单纯哈希链不能完全发现尾部截断；本地 `checkpoint` 用于记录当前 head hash，后续可扩展到 git note、发布产物或可信时间戳服务。

更多字段解释、CLI 参数映射和哈希链原理见 [BAC 工作原理教程](docs/bac-tutorial.md)。

## 开发与验证

```bash
python -m pytest -q
python -m unittest discover -s tests -v
```

核心测试覆盖 canonicalization、v2 容器结构、哈希链复算、篡改检测、重复内部路径检测、checkpoint 验证、敏感信息脱敏和 CLI 端到端流程。

## 目录结构

```
bensz-auto-contribution/
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── pyproject.toml
├── src
│   └── bac
│       ├── adapters
│       ├── core
│       ├── report
│       ├── service
│       └── storage
├── tests
├── docs
│   └── plans
├── README.md
├── Prompts.md
├── .gitignore
└── bensz-auto-contribution.code-workspace
```

## AI 辅助开发

本项目配置了 AI 辅助开发支持，可以使用以下工具进行智能开发：

### Claude Code

使用 `CLAUDE.md` 作为项目指令。

```bash
# 在项目目录启动 Claude Code
claude

# Claude Code 会自动读取 CLAUDE.md 理解项目上下文
```

### OpenAI Codex CLI

使用 `AGENTS.md` 作为项目指令。

```bash
# 在项目目录启动 Codex CLI
codex

# Codex 会自动读取 AGENTS.md 理解项目上下文
```

### AI 开发最佳实践

1. **新功能开发**：描述需求，AI 会按照项目工作流进行开发
2. **代码审查**：请求 AI 审查代码，它会按照工程原则给出建议
3. **文档更新**：AI 会自动同步更新相关文档
4. **问题排查**：描述问题现象，AI 会分析并给出解决方案
5. **变更记录**：**重要** - 凡是项目的更新，都要统一在 `CHANGELOG.md` 文件里记录。这是项目管理的强制性要求。

## 贡献

欢迎围绕 `.bac` 文件格式、威胁模型、AI tool 协议、验证机制和开发者体验提交 Issue 和 Pull Request。

## 许可证

MIT License
