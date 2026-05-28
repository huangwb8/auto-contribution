# BAC 工作原理教程

本文面向第一次阅读 `.bac` 文件的人，解释当前 `bac` 包如何记录贡献、每条记录里的字段是什么意思，以及验证器为什么能发现常见篡改。

## 核心概念

`.bac` 是一个单文件 ZIP 容器，默认文件名是 `project.bac`。用户通常只需要看到这一个文件；工具会在容器内部维护 manifest、事件序列和后续可扩展的证据文件。

当前 v2 容器至少包含：

```text
manifest.json
events/000000000001.json
events/000000000002.json
```

`manifest.json` 记录容器版本、事件格式、项目绑定信息、初始事件 hash 和存储约定。`events/` 下每个文件是一条 canonical JSON 事件，文件名从 `000000000001.json` 开始连续递增。当前实现不会原地修改历史事件，而是为新事件写入新的内部事件条目。

一个 `.bac` 文件可以理解为项目贡献时间线：

```text
genesis -> human_instruction -> ai_generation -> file_change -> test_result -> checkpoint
```

每条事件都会记录：

- 谁或什么来源产生了这条记录
- 这条记录描述了什么贡献或证据
- 当前项目上下文是什么
- 前一条事件的 hash 是什么
- 当前事件自身的 hash 是什么

这使 `.bac` 具备 tamper-evident 能力：它不能阻止别人编辑 ZIP 文件，但编辑、插入、删除、复制隐藏内部条目或重排历史事件后，验证器可以发现容器结构异常、hash 不匹配或链条断裂。

## 快速流程

先安装本地包：

```bash
python -m pip install -e .
```

在目标项目中初始化：

```bash
bac init
```

记录用户需求：

```bash
bac record \
  --event-type human_instruction \
  --source-type human \
  --summary "用户要求添加 BAC 验证流程"
```

记录 AI 生成或修改：

```bash
bac record \
  --event-type ai_generation \
  --source-type ai \
  --summary "AI 生成哈希链验证实现"
```

记录文件变更证据：

```bash
bac record \
  --event-type file_change \
  --source-type ai \
  --summary "更新验证器逻辑" \
  --path src/bac/core/verify.py
```

记录工具执行结果：

```bash
bac record \
  --event-type test_result \
  --source-type tool \
  --summary "单元测试通过" \
  --command-text "python -m pytest -q" \
  --exit-code 0
```

记录本地 checkpoint：

```bash
bac record \
  --event-type checkpoint \
  --source-type system \
  --summary "记录当前 head hash"
```

验证账本：

```bash
bac verify
```

查看时间线：

```bash
bac inspect
```

## 一条事件的结构

下面是简化后的事件示例：

```json
{
  "format": "bac.event.v2",
  "event_id": "bac_20260528T020756Z_c77031f6bcee4466",
  "event_type": "file_change",
  "source_type": "ai",
  "trust_level": "observed",
  "created_at": "2026-05-28T02:07:56Z",
  "project": {
    "root_path": "/path/to/project",
    "root_hash": "sha256:...",
    "git_remote": "git@github.com:example/repo.git",
    "git_commit": "abc123...",
    "git_branch": "main",
    "worktree_dirty": true
  },
  "actor": {
    "declared_name": "ai",
    "declared_kind": "ai",
    "session_id": "optional-session"
  },
  "payload": {
    "summary": "更新验证器逻辑",
    "files": [
      {
        "path": "src/bac/core/verify.py",
        "exists": true,
        "after_hash": "sha256:..."
      }
    ]
  },
  "evidence": [
    {
      "type": "git_diff_summary",
      "hash": "sha256:...",
      "redacted": false,
      "summary": " src/bac/core/verify.py | 10 +++++-----"
    }
  ],
  "redactions": [],
  "prev_event_hash": "sha256:...",
  "event_hash": "sha256:...",
  "signature": null
}
```

## 顶层字段含义

`format`

固定为 `bac.event.v2`。验证器用它判断当前事件是否属于支持的 BAC 事件格式。

`event_id`

事件唯一标识，当前由 UTC 时间戳和随机后缀组成，例如 `bac_20260528T020756Z_c77031f6bcee4466`。它方便人类定位事件，但 hash 链安全性不依赖它的不可预测性。

`event_type`

事件类型，描述这条记录“在贡献流程里代表什么”。当前支持：

- `genesis`：账本初始化事件，只能作为第一条事件
- `session_started`：会话开始
- `human_instruction`：人类需求、约束或指令
- `ai_plan`：AI 计划
- `ai_generation`：AI 生成内容、方案或代码
- `tool_command`：工具命令执行
- `file_snapshot`：文件快照
- `file_change`：文件变更
- `test_result`：测试或验证结果
- `human_review`：人类审阅意见
- `human_approval`：人类授权或确认
- `checkpoint`：记录当前 head hash，降低尾部截断风险
- `verification`：验证动作或验证结果

`source_type`

来源类型，回答“这条记录的直接来源是谁”。当前必须是以下四类之一：

- `human`：人类输入，例如需求、约束、审阅、批准、手写修改
- `ai`：AI 的推理、计划、生成、重构建议或修复意图
- `tool`：命令、测试、格式化器、linter、git 等工具输出
- `system`：BAC 工具自身或运行环境产生的系统事件

`trust_level`

信任等级，描述这条记录的可信依据。当前支持：

- `declared`：声明型记录，例如人类需求或 AI 生成说明
- `observed`：由工具观察到的事实，例如文件 hash、命令退出码、git diff 摘要
- `signed`：预留给签名事件
- `verified`：验证或 checkpoint 类事件
- `anchored`：预留给外部锚定事件

当前默认规则是：`human` 和 `ai` 的普通贡献通常是 `declared`；文件变更、测试结果和工具命令通常是 `observed`；`checkpoint` 是 `verified`。

`created_at`

事件创建时间，格式是 UTC ISO-8601，必须以 `Z` 结尾。验证器会检查时间格式，并在发现时间倒退时给出 warning。

`project`

项目上下文，用于把事件绑定到具体项目。它不是完整项目快照，而是记录关键上下文：

- `root_path`：项目根路径。若在 git 仓库内运行，优先使用 git 仓库根目录
- `root_hash`：基于 `root_path` 和 `git_remote` 计算出的项目绑定 hash
- `git_remote`：当前仓库的 `remote.origin.url`，不存在时为 `null`
- `git_commit`：当前 `HEAD` commit，不在 git 仓库或无 commit 时为 `null`
- `git_branch`：当前分支名，不存在时为 `null`
- `worktree_dirty`：运行时工作区是否有未提交改动

验证器会要求同一个 `.bac` 文件里的 `project.root_hash` 保持一致，从而发现账本被混入其它项目事件的情况。

`actor`

声明的操作者信息。默认由 CLI 参数生成：

- `declared_name`：声明名称
- `declared_kind`：声明类型
- `session_id`：可选会话标识

注意：当前 v2 里 `actor` 是声明信息，不等同于强身份认证。需要身份真实性时，应结合未来签名或外部可信身份机制。

`payload`

事件主体内容。至少会包含 `summary`。不同参数会写入不同内容：

- `--summary` 会写入 `payload.summary`
- `--path` 会收集文件快照并写入 `payload.files`
- `--command-text` 会写入 `payload.command`
- `--exit-code` 会写入 `payload.exit_code`
- `--payload-json` 会先作为附加对象写入 payload，再由 `summary` 覆盖或补充摘要
- `checkpoint` 事件会额外写入 `payload.checkpointed_head_hash`

`evidence`

证据列表。当前主要包括通过 `--path` 收集到的 `git diff --stat` 摘要。每个证据对象通常包含：

- `type`：证据类型，例如 `git_diff_summary`
- `hash`：证据内容的 sha256
- `redacted`：证据是否经过脱敏
- `summary`：人类可读的证据摘要

也可以用 `--evidence-json` 传入额外证据列表。

`redactions`

脱敏记录。BAC 会在写入前扫描 payload 和 evidence，遇到私钥、常见 API key、token、password、authorization、cookie 或过长字符串时进行脱敏或截断，并在这里记录脱敏路径和原因。

示例：

```json
[
  {
    "path": "$.command",
    "reason": "sensitive_pattern"
  }
]
```

`prev_event_hash`

前一条事件的 `event_hash`。第一条 `genesis` 事件必须是 `null`。从第二条事件开始，它必须等于上一条事件的 `event_hash`。

`event_hash`

当前事件的 sha256。计算时会先把事件转成 canonical JSON，再排除 `event_hash` 字段本身，避免循环引用。只要事件内容被修改，重新计算出的 hash 就会变化。

`signature`

签名字段。当前 v2 要求它可以是 `null` 或对象，但还没有实现签名验证。验证器遇到非空签名会报告当前尚不支持签名验证。因此目前不要把它理解为已经完成的身份真实性保障。

## CLI 参数如何变成事件

全局参数：

`--root`

目标项目根目录。默认是当前目录。所有相对路径 `.bac` 文件和 `--path` 文件快照都会基于它解析。

`--bac-file`

账本容器文件路径。默认是 `project.bac`。如果传相对路径，会放在 `--root` 下；如果传绝对路径，则直接使用该路径。

`init --force`

初始化账本。如果目标 `.bac` 已存在且非空，默认拒绝覆盖；传 `--force` 会重写。

`init --actor-name` 与 `init --actor-kind`

设置 genesis 事件的 actor。默认是 `bac` 和 `system_tool`。

`record --event-type`

设置事件类型。不能手动记录 `genesis`，因为 `genesis` 只由 `init` 创建。

`record --source-type`

设置来源类型，必须是 `human`、`ai`、`tool`、`system` 之一。

`record --trust-level`

手动指定信任等级。不传时使用默认规则。

`record --summary`

必填。写入 `payload.summary`，也是 `inspect` 时间线展示的主要文本。

`record --path`

可以重复传多次。BAC 会对每个路径记录：

- 相对路径
- 文件是否存在
- 文件内容 sha256
- 如果路径存在但不是普通文件，会标记 `kind: non_file`

同时，如果目标目录是 git 仓库，BAC 会尝试记录这些路径的 `git diff --stat` 摘要到 `evidence`。

`record --command-text` 与 `record --exit-code`

记录命令文本和退出码。BAC 当前不会替你执行命令，只记录你传入的命令和结果。因此调用方应先执行命令，再把结果写入 BAC。

`record --payload-json`

传入额外 payload 对象。必须是 JSON object，例如：

```bash
bac record \
  --event-type ai_plan \
  --source-type ai \
  --summary "制定实现计划" \
  --payload-json '{"risk":"low","scope":"docs"}'
```

`record --evidence-json`

传入额外 evidence 列表。必须是 JSON object 数组，例如：

```bash
bac record \
  --event-type verification \
  --source-type tool \
  --summary "外部检查完成" \
  --evidence-json '[{"type":"manual_check","summary":"reviewed by maintainer"}]'
```

`record --actor-name`、`record --actor-kind`、`record --session-id`

设置 actor 信息。不传时，`actor-name` 和 `actor-kind` 默认使用 `source_type`。

`--json`

让命令输出 machine-readable JSON，方便 AI tool 或脚本调用。

## 哈希链原理

BAC 的哈希链有两个关键字段：

```text
prev_event_hash -> event_hash
```

第一条 `genesis`：

```text
prev_event_hash = null
event_hash = hash(genesis_without_event_hash)
```

第二条事件：

```text
prev_event_hash = genesis.event_hash
event_hash = hash(second_event_without_event_hash)
```

第三条事件：

```text
prev_event_hash = second.event_hash
event_hash = hash(third_event_without_event_hash)
```

验证时，BAC 会从头到尾做两件事：

- 重新计算每条事件的 `event_hash`
- 检查每条事件的 `prev_event_hash` 是否等于上一条事件的 `event_hash`

因此：

- 修改历史事件内容会导致 `event_hash mismatch`
- 插入事件会导致后续 `prev_event_hash` 接不上
- 删除中间事件会导致后续 `prev_event_hash` 接不上
- 重排事件会导致链条断裂

不过，单纯本地哈希链不能完全防止尾部截断。例如攻击者删除最后几条事件后，剩余前缀本身仍可能是一条自洽链。当前 v2 用 `checkpoint` 表示“我在这里见过这个 head hash”，后续可以把 checkpoint head 发布到 git note、release artifact 或可信时间戳服务，以增强尾部截断发现能力。

## 验证器会检查什么

`bac verify` 会检查：

- `.bac` 文件存在
- `.bac` 是有效的 v2 ZIP 容器
- 容器包含 `manifest.json`
- 内部路径没有重复条目
- `events/` 事件文件名从 `000000000001.json` 开始连续递增
- `manifest.json` 与 genesis 事件一致
- 每个事件文件都是合法 JSON
- 每条事件都是 JSON object
- 必填字段齐全
- `format`、`event_type`、`source_type`、`trust_level` 合法
- `created_at` 是 UTC 时间
- `project` 字段结构合法
- `prev_event_hash` 和 `event_hash` 是 `sha256:<64位hex>` 或允许的 `null`
- 第一条事件是 `genesis`
- `genesis.prev_event_hash` 是 `null`
- 每条事件的 hash 可复算
- 每条事件正确连接到上一条事件
- 同一账本内 `project.root_hash` 不变
- checkpoint 的 `checkpointed_head_hash` 等于它自己的 `prev_event_hash`

验证结果有三种状态：

- `pass`：没有错误和警告
- `warn`：没有错误，但有警告，例如缺少 checkpoint
- `fail`：存在错误，例如 hash 不匹配或链条断裂

## Inspect 时间线

`bac inspect` 不做深度验证，它只是读取事件并输出更容易阅读的时间线：

```text
2026-05-28T02:07:26Z  genesis  system/observed  Initialized BAC ledger
2026-05-28T02:07:26Z  human_instruction  human/declared  用户要求添加 BAC 验证流程
2026-05-28T02:07:56Z  test_result  tool/observed  单元测试通过
```

每行展示：

- `created_at`
- `event_type`
- `source_type/trust_level`
- `payload.summary`

## 当前安全边界

当前 BAC v2 已支持：

- 单文件 ZIP 容器
- 追加式内部事件序列
- human、ai、tool、system 四类来源区分
- canonical JSON
- SHA-256 哈希链
- 项目上下文绑定
- 容器 manifest 校验
- 重复内部路径和事件编号缺口检测
- 文件快照 hash
- git diff 摘要证据
- 本地 checkpoint
- 敏感信息脱敏
- 账本验证和时间线查看

当前尚未实现：

- Ed25519 或其它真实签名验证
- 外部可信时间戳
- 远程或公开 anchor
- 自动执行命令并捕获 stdout/stderr
- 对文件内容语义变化的判断
- 对 actor 声明身份的真实性证明

因此，当前 `.bac` 的正确理解是：它提供可审计、可复算、篡改可发现的贡献记录基础设施；它不是不可修改文件，也不是完整身份认证系统。

## 推荐记录方式

一次较完整的 AI 协作开发可以记录为：

```text
human_instruction：用户需求和约束
ai_plan：AI 的实现计划
ai_generation：AI 生成或修改的内容摘要
file_change：涉及的关键文件快照
tool_command：重要工具命令
test_result：测试结果
human_review：用户或维护者审阅意见
human_approval：最终授权或确认
checkpoint：记录当前账本 head
```

不要把以下内容直接写进 `.bac`：

- 密钥、token、cookie、私钥
- 完整私有 prompt
- 无关隐私数据
- 大段源码全文
- 不可公开的业务资料

优先记录摘要、hash、路径、命令、退出码、diff 摘要和验证结论。这样既能保留审计价值，又能减少敏感信息泄露风险。
