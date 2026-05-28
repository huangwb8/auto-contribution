# Changelog

本文件记录项目重要变更，格式遵循 Keep a Changelog，并优先维护 `[Unreleased]`。

## [Unreleased]

### Added（新增）

- 明确项目定位为 `bensz auto contribution` 贡献归因与审计系统，核心产物为 `.bac` 文件。
- 补充 `.bac` 的初始设计边界：追加式事件、哈希链、签名、项目上下文绑定与篡改可发现。
- 新增 `.bac` 系统架构设计方案，说明轻核心、多适配器、事件模型、验证流程、威胁模型与 MVP 路线。
- 实现 BAC MVP：新增 Python CLI 与 library，支持 `bac init`、`bac record`、`bac verify`、`bac inspect`，以 JSON Lines 追加式事件账本记录贡献。
- 新增 canonical JSON、SHA-256 哈希链、项目上下文绑定、本地 checkpoint、敏感信息脱敏、贡献时间线展示和机器可读验证报告。
- 新增测试覆盖 canonicalization、哈希链验证、篡改检测、脱敏策略、checkpoint 和 CLI 端到端流程。

### Changed（变更）

- 将项目名、Python 发行包名、说明文档和工作区文件统一调整为 `bensz-auto-contribution`，使仓库命名与产品定位保持一致。
- 将初始化生成的通用项目说明替换为面向 AI tool 集成和人机贡献区分的项目指令。
- 更新 README，补充安装方式、CLI 使用示例、`.bac` 格式说明、MVP 安全边界和验证命令。

## [1.0.0] - 2026-05-26

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
