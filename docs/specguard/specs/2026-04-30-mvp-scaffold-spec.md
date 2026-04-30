# specguard MVP 脚手架插件设计补充

**日期**：2026-04-30
**状态**：Superseded（部分）by [2026-04-30-v0.1.1-dogfood-fix-spec.md](2026-04-30-v0.1.1-dogfood-fix-spec.md) 与 [decisions/0001-plugin-name-command-namespace.md](../decisions/0001-plugin-name-command-namespace.md)
**适用范围**：specguard 独立仓的 MVP。目标是交付一个 Claude Code plugin：原计划 `/sg:init`、`/sg:check`、`/sg:upgrade`（见后述 supersede），并预留多 agent / 多 spec 工具的可插拔架构。

> **Superseded 内容**:
> - 改动点 #6、#7 与 §3 中关于 `/sg:*` 命名的决策被 ADR-0001 推翻 → 实际命令为 `/specguard:init`、`/specguard:check`、`/specguard:upgrade`
> - §3 / §4 中"`/sg:init` 自动 merge `.claude/settings.json` hooks"被 v0.1.1 spec 推翻 → 实际写出 `.specguard/hooks.snippet.json`，由用户手动 merge

---

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 创建独立产品仓 `specguard`，不放在 guard-ghost 内。
2. 定位为项目治理脚手架（governance scaffold），不是日常 CLI，也不是 OpenSpec 替代品。
3. 设计 core + agent adapters + layout adapters 的双维度可插拔架构。
4. MVP 只实现 `--ai claude` adapter，但预留 Cursor / Codex / generic。
5. MVP 支持 `--spec none|openspec|superpowers`，其中 OpenSpec 采用 sidecar 兼容模式，Superpowers 采用 existing layout 兼容模式。
6. Slash commands 命名为短前缀 `/sg:init`、`/sg:check`、`/sg:upgrade`。
7. `/sg:init` 支持显式参数：`--ai <claude|cursor|codex|generic|auto>` 与 `--spec <none|openspec|superpowers|auto>`；默认 `auto`。
8. 取消 `/sg:new-adr` 与 `/sg:new-spec`，日常创建 ADR/spec 由 skill 引导 AI 直接 Write。
9. Claude adapter 提供 `design-governance` skill、三个 commands、五个 hooks。
10. `/sg:check semantic` 不内置 LLM 调用，只生成 review package。
11. `/sg:upgrade` 使用 marker 区块升级框架内容，保护用户自定义内容。
12. 默认 layout 不依赖 superpowers，使用 `docs/specguard/`；检测到 OpenSpec / Superpowers 时按参数或 auto 选择对应 layout。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 独立仓 | - | - | - | - | - |
| #2 产品定位 | - | - | - | - | - |
| #3 双维度可插拔架��� | ✓ | - | ✓ | - | - |
| #4 MVP 只实现 Claude adapter | - | - | - | - | - |
| #5 支持 spec tool layout | ✓ | - | ✓ | - | - |
| #6 `/sg:*` 命名 | ✓ | - | - | - | - |
| #7 `/sg:init` 参数 | ✓ | - | - | - | - |
| #8 取消 new-adr/new-spec | ✓ | - | - | - | - |
| #9 Claude skill/commands/hooks | ✓ | - | ✓ | - | - |
| #10 semantic check review package | ✓ | - | - | - | - |
| #11 marker upgrade | ✓ | - | - | - | - |
| #12 默认 layout = docs/specguard | ✓ | - | - | - | - |

### 候选 ADR（请用户拍板）

本 spec 是 specguard 项目的第一个切片设计，尚无已接受 ADR 可被推翻；上表中命中硬条件的内容属于 MVP 公开接口与架构边界，但已在本 spec 内由用户逐步拍板。**暂不单独拆 ADR**。

后续若以下内容发生变化，应新增 ADR：

- 命令前缀从 `/sg:*` 改为其他形式
- core / agent adapter / layout adapter 三层边界变化
- 从 Claude-first plugin 改为 CLI-first 或内置 LLM-first
- 从 OpenSpec sidecar 改为 OpenSpec inline 默认模式
- 引入 Python CLI 或内置 LLM SDK

### 不需要 ADR 的改动

- 目录中 `.tpl` 后缀、manifest.yaml 格式、render.py 具体实现属于实现细节，写在 plan 和代码中即可。
- hooks 的具体 shell/python 命令属于 Claude adapter 实现细节；只要不改变对用户的治理语义，不单独写 ADR。
- README / CHANGELOG / LICENSE 的文本结构不需要 ADR。

---

## 对 design.md 的影响（必填）

- `docs/specguard/design.md`：后续实施完成后，应把本 spec 中的核心架构（core / adapters / layouts / commands / hooks）同步为当前真相。
- `docs/specguard/decisions/`：MVP 暂无独立 ADR；若实施过程中改变本 spec 已拍板的命令、adapter、layout 边界，需要新增 ADR。

---

## 1. 产品定位

specguard 是一个**项目治理脚手架**，用于给 AI 主导开发的项目装上 living design + ADR 治理外壳，并通过 skill / rules / hooks 让 AI 自动遵守。

它不是：

- OpenSpec / Spec Kit / Superpowers 的替代品
- 日常命令行工具
- AI coding agent
- 内置 LLM reviewer

它是：

- agent-neutral 的治理资产集合
- 可渲染到不同 AI 工具的 adapter 框架
- 可兼容不同 spec 工具 layout 的 sidecar
- 通过脚手架初始化项目治理规则的工具

---

## 2. 架构：core + agent adapters + layout adapters

specguard 使用两个独立维度的可插拔架构：

```text
                Spec layout / spec 工具
                        ↕
                ┌───────┴────────┐
                │   specguard    │
                │      core      │
                └───────┬────────┘
                        ↕
                Agent / runtime
```

### core

`core/` 放 agent-neutral + layout-neutral 的治理资产：

```text
core/
├── rules/
│   ├── five-laws.md
│   ├── adr-checklist.md
│   └── design-sync.md
├── templates/
│   ├── design.md.tpl
│   ├── decisions/
│   │   ├── README.md.tpl
│   │   └── TEMPLATE.md.tpl
│   └── specs/
│       └── TEMPLATE.md.tpl
├── command-prompts/
│   ├── init.md
│   ├── check.md
│   └── upgrade.md
├── policies/
│   ├── with-openspec.md
│   ├── with-superpowers.md
│   └── with-speckit.md        # v0.3
└── version
```

规则：

- core 不出现 Claude / Cursor / Codex 等 agent 名字
- core 不写死 `docs/superpowers/`、`openspec/` 等路径
- core 使用变量：`{{ paths.design }}`、`{{ paths.decisions_dir }}`、`{{ paths.specs_dir }}`、`{{ paths.plans_dir }}`

### agent adapters

MVP 只实现 Claude adapter：

```text
adapters/claude/
├── manifest.yaml
├── .claude-plugin/
│   └── plugin.json              # name: specguard, commandNamespace: sg
├── skills/
│   └── design-governance/
│       └── SKILL.md.tpl
├── commands/
│   ├── init.md.tpl              # → /sg:init
│   ├── check.md.tpl             # → /sg:check
│   └── upgrade.md.tpl           # → /sg:upgrade
└── hooks/
    └── settings.json.snippet
```

未来新增：

```text
adapters/cursor/
adapters/codex/
adapters/generic/
```

### layout adapters

MVP 支持三种 layout：

```text
layouts/
├── specguard-default/
│   └── manifest.yaml
├── superpowers/
│   └── manifest.yaml
└── openspec-sidecar/
    └── manifest.yaml
```

| layout | design/ADR 位置 | spec/change 位置 | 用途 |
|---|---|---|---|
| `specguard-default` | `docs/specguard/` | `docs/specguard/specs/` | 没有现有 spec 工具的新项目 |
| `superpowers` | `docs/superpowers/` | `docs/superpowers/specs/` / `plans/` | 已用 superpowers 的项目 |
| `openspec-sidecar` | `docs/specguard/` | `openspec/specs/` + `openspec/changes/` | 已用 OpenSpec 的项目，specguard 作为 governance sidecar |

---

## 3. Claude adapter 内容

### Skill：`specguard:design-governance`

frontmatter：

```yaml
---
name: design-governance
description: Use when starting or changing a feature, writing specs or plans, making architecture decisions, updating design docs, creating ADRs, or reviewing whether AI coding work may drift from project architecture
---
```

主体：

```markdown
# Design Governance

## Overview
specguard enforces living design + ADR governance for AI-assisted projects.
This skill is agent and spec-tool agnostic.

## Non-Negotiables
<!-- inject:five-laws -->

## Required Workflow
1. Read {{ paths.design }} and {{ paths.decisions_dir }}/
2. Explore design before implementation
3. Produce a slice spec containing the ADR Decision Assessment section
4. Ask the user to approve candidate ADRs
5. Write a plan only after the spec is approved
6. Sync {{ paths.design }} after interface/data/boundary changes

## ADR Decision Assessment
<!-- inject:adr-checklist -->

## design.md Sync Rules
<!-- inject:design-sync -->

## Optional Integrations
- If superpowers is available: use superpowers:brainstorming and superpowers:writing-plans for exploration and planning.
- If OpenSpec is the spec tool: write change proposals under openspec/changes/, but ADR judgement and design.md sync still follow this skill.

## When NOT to Write ADR
- Tasks
- Implementation details
- Parameter defaults
- Naming choices
- First implementation of an existing design

## Common Mistakes
- Creating new dated design files
- Writing ADR for every task
- Treating design.md as historical archive instead of current truth
- Skipping ADR assessment before plan
```

### Commands

#### `/sg:init`

签名：

```text
/sg:init [--ai <claude|cursor|codex|generic|auto>] [--spec <none|openspec|superpowers|auto>]
```

默认：`--ai auto --spec auto`

行为：

1. 解析参数
2. `auto` 时探测 agent/spec 工具
3. 冲突时让用户拍板
4. 推导 layout
5. 渲染 templates / rules / hooks
6. 合并 CLAUDE.md 与 `.claude/settings.json`
7. 写 `.specguard-version`
8. 输出 created / updated / skipped 报告

#### `/sg:check`

签名：

```text
/sg:check [semantic]
```

默认执行结构检查：

- design.md 存在且唯一
- 不存在 dated design 文件
- ADR 文件名格式
- ADR 编号连续
- README 索引完整
- design.md 引用的 ADR 存在
- spec 是否含 `ADR 级别决策识别` 节
- CLAUDE.md 是否含 specguard marker
- settings.json 是否含 specguard hooks
- `.specguard-version` 是否存在

带 `semantic` 时生成 review package：

```text
.specguard/reviews/YYYYMMDD-HHMM/
├── prompt.md
├── context.md
└── findings-template.md
```

不调用 LLM。

#### `/sg:upgrade`

行为：

1. 读 `.specguard-version`
2. 对比 plugin 当前版本
3. 找 marker 区块：CLAUDE.md、settings hooks、TEMPLATE.md、README 规则段
4. 输出 diff 摘要
5. 用户确认后替换 marker 内框架内容
6. 保护 marker 外用户内容
7. 更新 `.specguard-version`

### Hooks

Claude adapter 安装五个 hooks：

| Hook | 行为 |
|---|---|
| SessionStart | 注入五条铁律 + ADR 判定简版 |
| PreToolUse / Write | 拒绝 `{{ paths.specs_dir }}/*-design.md` |
| PreToolUse / Write | 校验 `{{ paths.decisions_dir }}/*.md` 文件名 |
| Stop | `src/` 改了但 design/ADR 未改时提醒 |
| UserPromptSubmit | 用户提到写 spec/plan/开始实施时提醒先做 ADR 判定 |

Cursor / Codex adapter 没有 hooks，未来 README 需说明治理强度差异。

---

## 4. 用户流程

### 首次安装

Claude Code 用户：

```text
claude plugin install specguard
/sg:init
```

显式模式：

```text
/sg:init --ai claude --spec openspec
/sg:init --ai claude --spec superpowers
/sg:init --ai claude --spec none
```

自动检测：

- `.claude/` → claude
- `.cursor/` → cursor（v0.2 才支持，MVP 明确拒绝并给替代方案）
- `AGENTS.md` → codex（v0.2+）
- `openspec/` → openspec
- `docs/superpowers/` → superpowers

### 已有 OpenSpec 项目

```text
/sg:init --ai claude --spec openspec
```

生成：

```text
docs/specguard/design.md
docs/specguard/decisions/
CLAUDE.md（注入 with-openspec policy）
.claude/settings.json
.specguard-version
```

不侵入 `openspec/` 内部目录。

### 已有 Superpowers 项目

```text
/sg:init --ai claude --spec superpowers
```

生成/合并：

```text
docs/superpowers/design.md
docs/superpowers/decisions/
docs/superpowers/specs/TEMPLATE.md
CLAUDE.md（注入 with-superpowers policy）
.claude/settings.json
.specguard-version
```

### 新需求

用户说："我要做 P2 Hook 引擎"。

流程：

1. `design-governance` skill 自动加载
2. AI 读 design.md + decisions/
3. AI 进入设计探索（若 superpowers 可用，优先用 superpowers:brainstorming）
4. AI 输出 ADR 判定报告
5. 用户拍板候选 ADR
6. AI 写切片 spec
7. AI 写 plan（若 superpowers 可用，优先用 writing-plans）
8. 实施
9. 同步 design.md
10. `/sg:check`

---

## 5. 测试策略与验收标准

### Layer 1：render 单元测试

验证：

- `build/render.py --target claude --layout specguard-default` 能生成 Claude plugin
- 所有 `<!-- inject:* -->` marker 被替换
- 所有 `{{ paths.* }}` 变量被替换
- `plugin.json` 中 `commandNamespace = "sg"`

### Layer 2：fixture 端到端生成测试

三个 fixture：

1. `empty-claude`：`/sg:init --ai claude --spec none`
2. `claude-with-openspec`：`/sg:init --ai claude --spec openspec`
3. `claude-with-superpowers`：`/sg:init --ai claude --spec superpowers`

检查生成文件、marker、hooks、`.specguard-version`。

### Layer 3：skill 行为测试

按 `superpowers:writing-skills` 做 TDD：

RED：不用 skill，让 subagent 在以下压力场景中失败：

1. 用户要求直接写 plan，实现 Hook 引擎
2. 用户要求新增 run delete，直接实现
3. 用户说小改不用文档，直接动手

GREEN：加载 `design-governance` skill 后，同样场景必须：

- 先读 design.md + decisions/
- 输出 ADR 判定报告
- 候选 ADR 交用户拍板
- 不写 dated design
- 不跳过 spec 直接 plan/implementation

### Layer 4：dogfood

用 guard-ghost 验证：

```text
/sg:init --ai claude --spec superpowers
/sg:check
```

期望：

- 不覆盖已有 design.md / ADR
- 不重复注入 CLAUDE.md block
- 不重复 hooks
- `.specguard-version` 记录正确
- `/sg:check` 0 errors / 可接受 warnings

---

## 6. 验收标准

MVP 发布前必须满足：

1. Claude plugin render 通过
2. 三个 fixture init 通过
3. 三个 skill pressure scenarios 通过（RED 失败、GREEN 通过）
4. `/sg:check` 能发现：缺 design、dated design、ADR 命名错误、ADR 引用缺失、spec 缺 ADR 判定节、缺 hooks
5. `/sg:upgrade` 能 marker upgrade 且保护用户内容
6. guard-ghost dogfood 通过
7. README 明确说明：
   - specguard 不依赖 superpowers
   - OpenSpec / Superpowers 是可选 layout
   - MVP 只支持 Claude target
   - Cursor / Codex adapter 尚未支持
   - Claude target 有 hooks，其他 target 未来可能没有等价 hooks

---

## 7. 不在 MVP 范围

- Cursor / Codex / Copilot adapter
- Python CLI / PyPI
- 内置 LLM 调用
- OpenSpec inline layout
- Spec Kit adapter
- PR bot / GitHub Action
- dashboard
- contract/golden fixtures 层

---

## 8. 下一步

本 spec 经用户 review 通过后，进入 implementation plan：

1. 建立 specguard 仓基础结构
2. 编写 core/rules 与 templates
3. 编写 Claude adapter templates
4. 编写 render.py
5. 编写 fixture 测试
6. 编写 skill pressure tests
7. 在 guard-ghost dogfood
