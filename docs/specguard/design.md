# specguard 设计（Living Architecture）

**Last verified against code**: 05d3cf3
**Authoritative for**: 当前架构、命令语义、数据契约、安全边界
**ADR 索引**: [decisions/README.md](decisions/README.md)

> 本文档是 specguard 项目当前架构唯一真相。代码与本文档不一致即为缺陷。
> 决策动机与历史在 decisions/，本文档只反映“现在是什么”。

---

## 1. 产品定位与边界

specguard 是一个项目治理脚手架：把 living design、ADR、spec discipline、Claude hooks、slash commands 打包成可安装的 Claude Code plugin。

它的边界：
- 交付治理 scaffold，不接管用户项目的业务代码生成。
- 约束 AI 协作流程，不替代 OpenSpec、Superpowers、Spec Kit。
- 当前唯一可执行 agent adapter 是 Claude Code；Cursor、Codex、generic adapter 是 v0.3+ 留位。
- 分发方式：Claude Code marketplace（`plugins/<layout>/` git-subdir）为主，GitHub Release tarball 作为 fallback（见 ADR-0008）。

## 2. 端到端流程

### 2.1 Build / Release flow

```mermaid
flowchart TD
  T[git tag v*] --> CI[CI checkout main]
  CI --> A[core assets]
  A --> RP[src/specguard/render.py render plugins/<layout>]
  L[layout manifest] --> RP
  C[claude adapter manifest] --> RP
  RP --> PD[plugins/<layout>/ git tracked]
  PD --> PR[git pull --rebase main]
  PR --> PC[git commit plugins/]
  PC --> PP[git push HEAD:main]
  PP --> RD[render dist/claude/<layout> fallback]
  RD --> M[runtime/specguard/*.py copied]
  M --> TB[release tarball]
  TB --> GR[GitHub Release]
```

tag 触发 → CI checkout main → render `plugins/<layout>/` → `pull --rebase main` 防 race → commit + push main → 继续 render `dist/` 并打 tarball 作为 fallback → 发布 GH Release（见 ADR-0008）。

### 2.2 Init flow

```mermaid
flowchart TD
  A[/specguard:init] --> B[parse --ai / --spec / --dry-run]
  B --> C[confirm rendered layout paths]
  C --> D[create missing design / decisions / spec templates]
  C --> E[insert or replace CLAUDE.md specguard block]
  C --> F[write hooks snippet to tempfile]
  F --> G[specguard.hooks_merge merges .claude/settings.json]
```

### 2.3 Check flow

```mermaid
flowchart TD
  A[/specguard:check] --> B[read project governance files]
  B --> C[run 11 structural checks]
  C --> D{errors?}
  D -->|yes| E[print error report]
  D -->|no| F[print warning / success report]
  E --> G[no project writes]
  F --> G
```

## 3. 架构分层

### 3.1 core

`core/` 保存 agent-neutral、layout-neutral 治理资产：version、rules、templates、command prompts、policies。

### 3.2 layouts

`layouts/` 描述三种目录布局：`specguard-default`、`superpowers`、`openspec-sidecar`。layout 只声明路径与 policy 注入，不包含 agent runtime 逻辑。

### 3.3 adapters/claude

`adapters/claude/` 渲染 Claude Code plugin：plugin.json、design-governance skill、init/check commands、hooks snippet。plugin name 固定为 `specguard`，没有 `commandNamespace` 字段，因此命令固定为 `/specguard:init`、`/specguard:check`（见 ADR-0001）。

### 3.4 src/specguard

`src/specguard/render.py` 是 build-time 渲染管线，负责把 `src/specguard/` 下的 `__init__.py` 与 `hooks_merge.py` 复制到 dist 的 `runtime/specguard/`。`src/specguard/hooks_merge.py` 是 runtime-safe Python module，由 `/specguard:init` rendered prompt 通过 `CLAUDE_PLUGIN_ROOT/runtime` 导入（见 ADR-0004）。

### 3.5 marketplace 与 plugins/

- `.claude-plugin/marketplace.json`：Claude Code marketplace 元数据，列出三个 plugin（specguard-default / specguard-superpowers / specguard-openspec-sidecar），每个 plugin 的 `source` 用 `git-subdir` 指向同 repo 的 `plugins/<layout>/`（见 ADR-0008）。
- `plugins/<layout>/`：CI render 产物的 git tracked 目录，对应三种 layout。**禁止人工编辑**：每次 release tag 触发时 CI 会重新渲染并 force-overwrite 该目录、再 commit + push 回 main。手工修改会在下次 release 时丢失。

## 4. 数据契约

执行强度分三类：

- **机器强制**：pytest、render、runtime module 或 hooks 能稳定执行。
- **治理强制**：`/specguard:check` 或 Claude prompt 明确检查并报告。
- **用户契约**：由文档和 ADR 约束，当前不自动执行。

| # | 契约 | 强度 | 当前语义 |
|---|---|---|---|
| 1 | `CLAUDE.md` specguard block | 机器强制 | 只替换 `<!-- specguard:start -->` 到 `<!-- specguard:end -->` 区域。 |
| 2 | `.claude/settings.json` hooks | 机器强制 | 按 `statusMessage` 前缀 `specguard:` 幂等替换 specguard hooks，保留非 specguard hooks。 |
| 3 | 禁止新 `*-design.md` | 机器强制 | hooks 阻止新 dated design 文件；superpowers 历史 `*-design.md` 为 warning。 |
| 4 | ADR 文件名 | 治理强制 | ADR 文件匹配 `^[0-9]{4}-[a-z0-9-]+\.md$`，README/TEMPLATE 例外。 |
| 5 | `docs/specguard/design.md` | 用户契约 | 当前架构唯一真相；接口、数据结构、模块边界变更必须同步。 |
| 6 | spec ADR 判断标题 | 治理强制 | 新 spec 必须含 `## ADR 级别决策识别`，存量文件可按 installed_at 豁免。 |
| 7 | ADR supersede 引用 | 治理强制 | `Superseded by ADR-NNNN` 的目标 ADR 必须存在。 |
| 8 | `.claude-plugin/marketplace.json` schema | 机器强制 | 必填 `name="specguard"`、`owner.{name,email}`、`plugins[]` 数组；每个 plugin 必填 `name`、`source.{source="git-subdir",url,path}`、`description`。plugin entry **不写** `version`，避免与 plugin.json.version 双写发散（见 ADR-0008）。 |
| 9 | `plugins/<layout>/` 结构 | 机器强制 | 必含 `.claude-plugin/plugin.json`、`commands/init.md`、`commands/check.md`、`runtime/specguard/{__init__.py,hooks_merge.py}`、`hooks/settings.json.snippet`、`skills/design-governance/SKILL.md`。`plugin.json.version` 由 render 时从 `core/version` 注入，禁止人工编辑（见 ADR-0008）。 |

## 5. 命令语义

### 5.1 `/specguard:init`

`/specguard:init` 解析 `--ai <claude|cursor|codex|generic|auto>`、`--spec <none|openspec|superpowers|auto>`、`--dry-run`。当前只有 Claude adapter 可执行；非 Claude 选项是未来 adapter 留位。init 创建缺失 scaffold、更新 CLAUDE.md marker block、用 tempfile + `specguard.hooks_merge.merge_hooks_file()` 合并 hooks 到 `.claude/settings.json`。

rendered prompt 使用 embedded assets，不在用户项目运行时搜索 plugin 源码目录；需要 Python runtime 时通过 `CLAUDE_PLUGIN_ROOT/runtime` 导入 bundled module。

### 5.2 `/specguard:check`

`/specguard:check` 是只读结构治理检查，运行 11 项 structural checks 并输出 error/warning/report。它不接受 `semantic` 模式，不创建 `.specguard/reviews/`，不生成 `prompt.md`、`context.md` 或 `findings-template.md`（见 ADR-0005）。

## 6. 不变量与安全边界

- marker 外永不修改：CLAUDE.md 与 decisions README 只改 specguard marker 内文本。
- `--dry-run` 不写用户项目文件。
- hooks 只按 `statusMessage` 前缀 `specguard:` 识别 specguard entries。
- release/runtime 边界：release tarball 必须携带 `runtime/specguard/`。
- layout/adapter 边界：layout 不实现 agent 行为；adapter 不改变 layout paths。
- check 只读：`/specguard:check` 不创建 review package 或其他项目文件。
- specguard 不执行用户项目代码：render、hooks merge 只读写治理文件与 JSON/TOML-like metadata。
- marketplace plugin path 完整性：`.claude-plugin/marketplace.json` 列出的每个 plugin `source.path` 必须对应一个 git tracked 目录且含合法 `plugin.json`；`tests/test_marketplace_schema.py::test_marketplace_plugin_paths_exist_and_have_plugin_json` 强制保证（见 ADR-0008）。
- 4 个 specguard hook 的 shell 决策由 pytest test_hook_*.py 强制覆盖（每 hook 一个文件、≥30 个用例）；模型采纳 governance context（SessionStart additionalContext、UserPromptSubmit additionalContext、Stop systemMessage）的实际行为仍需人工 dogfood 或未来 L2 真 Claude 端到端验证（见 ADR-0009）。

## 7. 测试策略

### 7.1 风险 → 测试防线

| 风险 | 测试防线 |
|---|---|
| rendered command 残留 inject marker | `tests/test_render_claude_default.py` |
| hooks merge 覆盖用户自定义 hooks | `tests/test_init_merge_hooks.py` |
| release tarball 缺 runtime | `tests/test_render_basic.py`、`tests/test_release_workflow.py` |
| layout path 漂移 | 三个 render layout 测试 |
| `plugins/` 与 `src/` 脱同步导致 marketplace 用户拿到旧版本 | `release.yml` 在 build tarball 之前强制 render+commit+push `plugins/`，`pull --rebase` 防 race；`tests/test_release_workflow.py::test_release_workflow_renders_and_commits_plugins` 断言这个步骤顺序（见 ADR-0008）。 |
| hooks shell 决策 / governance 触发词覆盖率 | `tests/test_hook_*.py`（每 hook 一个文件，覆盖 SessionStart 法则注入、PreToolUse:Write dated-design 拦截、PreToolUse:Write ADR 命名校验、Stop design 同步提醒、UserPromptSubmit 触发词检测）（见 ADR-0009） |
| hooks shell 通过但模型忽略 additionalContext / systemMessage | L2 真 Claude 端到端验证延后到未来切片（API token 消耗）；当前依赖人工 dogfood（见 ADR-0009） |

### 7.2 改动类型 → 必跑测试

| 改动类型 | 必跑测试 |
|---|---|
| command prompt | `uv run pytest tests/test_render_claude_default.py -q` |
| hooks merge runtime | `uv run pytest tests/test_init_merge_hooks.py -q` |
| render/release | `uv run pytest tests/test_render_basic.py tests/test_release_workflow.py -q` |
| release candidate | `uv run pytest` + render 三 layout |
| `marketplace.json` schema 修改 | `uv run pytest tests/test_marketplace_schema.py -q`。影响：会让所有 `marketplace add` 用户在下次 update 时重新 resolve plugin source；schema 不向前兼容会导致 plugin install 失败（见 ADR-0008）。 |
| hooks `settings.json.snippet` 修改 | `uv run pytest tests/test_hook_*.py -q`（如果改的是 hook shell 行为则同步更新对应 `test_hook_*.py` 的断言；strict xfail 用例会主动 fail 提醒同步）（见 ADR-0009）。 |

### 7.3 未覆盖风险

- Claude Code plugin runtime 对 `CLAUDE_PLUGIN_ROOT` 的暴露由 Claude Code 提供，pytest 只能覆盖 prompt 文案与本地 module 行为。
- 真 Claude 对话中的用户确认交互无法完全由 pytest 模拟，需要 dogfood。
- 模型实际是否消化 SessionStart additionalContext（governance laws 是否被采纳）、UserPromptSubmit additionalContext（ADR judgement 提醒是否被执行）、Stop systemMessage（design 同步提醒是否被注意）。这些是 LLM 行为问题，pytest 无法覆盖；shell 决策本身已由 `tests/test_hook_*.py` 强制（见 ADR-0009）。

## 8. 不在范围

- 非 Claude agent runtime：当前只支持 Claude Code；Cursor / Codex / generic adapter 未实现。
- 版本升级命令：specguard 不提供 `/specguard:upgrade`；用户从旧版本迁移依赖重新 init（见 ADR-0007）。
