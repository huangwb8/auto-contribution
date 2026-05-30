# Changelog

本文件记录项目重要变更，格式遵循 Keep a Changelog，并优先维护 `[Unreleased]`。

## [Unreleased]

## [1.2.0] - 2026-05-30

### Added（新增）

- 新增 private-anchor 客户端核心：支持盲化 `anchor_hash`、anchor request/receipt schema 校验、Ed25519 receipt 验签、anchored checkpoint 和 `verify --require-anchor`。
- 新增 CLI 锚定工作流：`bac init --mode/--anchor-url`、`bac config set/get`、`bac anchor request/import/push`，保持本地记录优先，远程失败不影响已有账本。
- 新增 `server/` reference anchor server：提供 FastAPI + SQLite + Ed25519 签名的 `/healthz`、public keys、anchor 创建、receipt 查询、ledger receipt 查询和只读 `/admin` 页面，并补充 Docker Compose 部署说明。
- 新增 `anchor` 与 `server` 可选依赖组，用于签名验签和自托管服务端。

### Changed（变更）

- 调整 private-anchor 实施计划：从单纯外部锚定协议升级为本地端与 `./server` 自托管服务端协同的完整路线，明确默认 `hybrid` 模式、可选 `local` 模式、Docker 部署、后台管理、服务端 API、密钥管理和隐私边界。
- 将 `anchor_status` 从单一 `anchored` 细分为 `not_anchored`、`local_checkpoint`、`receipt_valid` 和 `receipt_invalid`，更准确区分本地 checkpoint 与远程 signed receipt。

## [1.1.2] - 2026-05-30

### Added（新增）

- 新增 PyPI 发布流程：加入 GitHub Actions Trusted Publishing 工作流、发布指南和 README 入口，并补充 PyPI 元数据。

### Fixed（修复）

- 修正 README 与中文 README 抬头徽章：版本展示改为读取 GitHub 最新 tag，避免硬编码版本号与发布标签漂移；同时明确 `.bac` 格式徽章标签。

### Changed（变更）

- 根据 `init-project` 最新规范优化 `AGENTS.md`：补充 BAC 默认贡献记录约定、Single Source of Truth 维护规则，以及 `CLAUDE.md` 引用关系检查要求。
- 补充发布版本约束：执行发布任务时版本永远以用户明确指定值为准，并要求先同步 `pyproject.toml` 后再打 tag 与发布。

## [1.1.0] - 2026-05-29

### Added（新增）

- 新增中文 README 入口 `README.zh-CN.md`，与英文主 README 形成双语文档结构，便于中英文读者阅读项目定位、快速开始、格式说明和安全边界。
- 新增 MIT `LICENSE` 文件，使 README 许可证徽章与项目元数据指向一致。

### Changed（变更）

- 将 `.bac` 从 v1 JSON Lines 账本重构为 v2 单文件 ZIP 容器：内部包含 `manifest.json` 和连续编号的 `events/*.json` 事件条目，保持用户侧单文件体验，同时为后续 artifacts、checkpoint、签名和索引扩展预留空间。
- 将事件格式升级为 `bac.event.v2`，验证器新增 v2 容器检查，包括 ZIP 有效性、重复内部路径、事件编号缺口、manifest 与 genesis 一致性，以及原有哈希链和 checkpoint 验证。
- 将项目版本升级到 `2.0.0`。该版本不兼容未正式使用的 v1 JSON Lines `.bac` 文件。
- 更新 README 的产品定位说明，明确 BAC 是 AI-人类协作过程记录与辅助审计系统，不替代论文署名、作者贡献声明或最终学术责任判断。
- 将 README 调整为英文主文档，并参考 `bensz-channel` 的开源项目首页风格增加居中抬头、徽章、语言切换和 Star History 展示。

## [1.0.0] - 2026-05-28

### Added（新增）

- 明确项目定位为 `bensz auto contribution` 贡献归因与审计系统，核心产物为 `.bac` 文件。
- 补充 `.bac` 的初始设计边界：追加式事件、哈希链、签名、项目上下文绑定与篡改可发现。
- 新增 `.bac` 系统架构设计方案，说明轻核心、多适配器、事件模型、验证流程、威胁模型与 MVP 路线。
- 实现 BAC MVP：新增 Python CLI 与 library，支持 `bac init`、`bac record`、`bac verify`、`bac inspect`，以 JSON Lines 追加式事件账本记录贡献。
- 新增 canonical JSON、SHA-256 哈希链、项目上下文绑定、本地 checkpoint、敏感信息脱敏、贡献时间线展示和机器可读验证报告。
- 新增测试覆盖 canonicalization、哈希链验证、篡改检测、脱敏策略、checkpoint 和 CLI 端到端流程。
- 新增 BAC 工作原理教程，解释 `.bac` 事件字段、CLI 参数映射、哈希链验证机制和当前安全边界。

### Changed（变更）

- 将项目名、Python 发行包名、说明文档和工作区文件统一调整为 `bensz-auto-contribution`，使仓库命名与产品定位保持一致。
- 将初始化生成的通用项目说明替换为面向 AI tool 集成和人机贡献区分的项目指令。
- 更新 README，补充安装方式、CLI 使用示例、`.bac` 格式说明、MVP 安全边界和验证命令。

## [0.1.0] - 2026-05-26

### Added（新增）

- 初始化 AI 项目指令文件：生成 `AGENTS.md`、`CLAUDE.md`、`README.md` 与 `.gitignore`
- 配置项目工程原则、工作流和变更记录规范

### Changed（变更）

### Fixed（修复）

---

## 记录规则

- 必须记录影响项目行为、结构、工作流、工程原则、指令文件或关键配置的变更
- 记录应说明改了什么、为什么改，以及影响范围
- 版本号遵循 SemVer：bug fix 递增修订号，新功能递增次版本号，破坏性变更递增主版本号

```markdown
## [版本号] - YYYY-MM-DD

### Added（新增）
- 新增了 XXX：用途是 YYY

### Changed（变更）
- 修改了 XXX：原因是 YYY，影响是 ZZZ

### Fixed（修复）
- 修复了 XXX：表现是 YYY，修复方式是 ZZZ
```
