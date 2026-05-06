# specguard 设计（Living Architecture）

**Last verified against code**: 0d0d312
**Authoritative for**: 当前架构、命令语义、数据契约、安全边界
**ADR 索引**: [decisions/README.md](decisions/README.md)

> 本文档是 specguard 项目当前架构唯一真相。代码与本文档不一致即为缺陷。
> 决策动机与历史在 decisions/，本文档只反映“现在是什么”。

---

## 1. 产品定位与边界

specguard 是一个项目治理脚手架：通过 Claude Code 的 hooks、slash commands 和 CLAUDE.md 注入，强制 AI 辅助开发遵循 living design / ADR / spec 纪律。

它的边界：
- 交付治理 scaffold，不接管用户项目的业务代码生成。
- 约束 AI 协作流程，不替代 OpenSpec、Superpowers、Spec Kit。
- 当前唯一可执行 agent adapter 是 Claude Code；Cursor、Codex、generic adapter 未实现。
- 分发方式：GitHub Release tarball（见 ADR-0011）。

## 2. 端到端流程

### 2.1 Build / Release flow

```mermaid
flowchart TD
  T[git tag v*] --> CI[CI checkout]
  CI --> A[core assets]
  A --> RP[src/specguard/render.py]
  L[layout manifest] --> RP
  C[claude adapter manifest] --> RP
  RP --> RD[dist/claude/<layout>]
  RD --> M[runtime/specguard/*.py copied]
  M --> TB[release tarball]
  TB --> GR[GitHub Release]
```

tag 触发 → CI checkout → render dist/ → build tarball → 发布 GH Release（见 ADR-0003）。

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
| 6 | spec ADR 判断标题 | 治理强制 | 新 spec 必须含 `## ADR 级别决策识别`。 |
| 7 | ADR supersede 引用 | 治理强制 | `Superseded by ADR-NNNN` 的目标 ADR 必须存在。 |

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
- 4 个 specguard hook 的 shell 决策由 pytest `tests/test_hook_*.py` 强制覆盖（见 ADR-0009）；模型采纳 governance context 的实际行为仍需人工 dogfood 或未来 L2 验证。

## 7. 测试策略

### 7.1 风险 → 测试防线

| 风险 | 测试防线 |
|---|---|
| rendered command 残留 inject marker | `tests/test_render_claude_default.py` |
| hooks merge 覆盖用户自定义 hooks | `tests/test_init_merge_hooks.py` |
| release tarball 缺 runtime | `tests/test_render_basic.py`、`tests/test_release_workflow.py` |
| layout path 漂移 | 三个 render layout 测试 |
| hooks shell 决策 / governance 触发词覆盖率 | `tests/test_hook_*.py`（见 ADR-0009） |
| hooks shell 通过但模型忽略 additionalContext / systemMessage | 人工 dogfood；L2 真 Claude 端到端验证延后（见 ADR-0009） |

### 7.2 改动类型 → 必跑测试

| 改动类型 | 必跑测试 |
|---|---|
| command prompt | `uv run pytest tests/test_render_claude_default.py -q` |
| hooks merge runtime | `uv run pytest tests/test_init_merge_hooks.py -q` |
| render/release | `uv run pytest tests/test_render_basic.py tests/test_release_workflow.py -q` |
| release candidate | `uv run pytest` + render 三 layout |
| hooks `settings.json.snippet` 修改 | `uv run pytest tests/test_hook_*.py -q`（见 ADR-0009） |

### 7.3 未覆盖风险

- `CLAUDE_PLUGIN_ROOT` 的暴露由 Claude Code runtime 决定，pytest 无法覆盖。
- 模型是否真正遵循 SessionStart / UserPromptSubmit / Stop 注入的 governance context 是 LLM 行为问题，pytest 无法覆盖；hook shell 决策本身已由 `tests/test_hook_*.py` 强制（见 ADR-0009）。

## 8. 不在范围

- 非 Claude agent runtime：当前只支持 Claude Code；Cursor / Codex / generic adapter 未实现。
- 版本升级命令：specguard 不提供 `/specguard:upgrade`；用户迁移到新版本重跑 `/specguard:init` 即可（见 ADR-0007）。
