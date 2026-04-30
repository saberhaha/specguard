# specguard MVP 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付 specguard MVP —— 一个 Claude Code plugin，提供 `/sg:init` / `/sg:check` / `/sg:upgrade`，把 living design + ADR 治理体系装进任意项目；并预埋 core + agent adapters + layout adapters 的可插拔架构，未来可加 Cursor / Codex / OpenSpec inline。

**Architecture:** 单仓 `specguard/`，分三层：
1. `core/`：agent-neutral + layout-neutral 治理资产（rules / templates / command-prompts / policies）
2. `layouts/`：spec 工具兼容（specguard-default / superpowers / openspec-sidecar）
3. `adapters/claude/`：MVP 唯一 agent target，含 plugin / skill / commands / hooks

构建脚本 `build/render.py` 把 `core + layout + adapter` 渲染成 `dist/claude/specguard-plugin/` 这个可发布的 Claude plugin。

**Tech Stack:** Python 3.11+（uv 管理），PyYAML（layout/manifest 解析），Jinja2（变量替换），pytest（测试）。无 CLI 框架依赖；`specguard-render` 入口用 stdlib `argparse`。

**与 spec 的关系：** 实施 [2026-04-30-mvp-scaffold-spec.md](../specs/2026-04-30-mvp-scaffold-spec.md) 的 §1–§6。§7 不在范围内。

---

## 文件结构

```text
specguard/
├── pyproject.toml
├── .gitignore
├── README.md                          # 已存在，本计划末尾会更新
├── CHANGELOG.md
│
├── core/
│   ├── version
│   ├── rules/
│   │   ├── five-laws.md
│   │   ├── adr-checklist.md
│   │   └── design-sync.md
│   ├── templates/
│   │   ├── design.md.tpl
│   │   ├── decisions/
│   │   │   ├── README.md.tpl
│   │   │   └── TEMPLATE.md.tpl
│   │   └── specs/
│   │       └── TEMPLATE.md.tpl
│   ├── command-prompts/
│   │   ├── init.md
│   │   ├── check.md
│   │   └── upgrade.md
│   └── policies/
│       ├── with-openspec.md
│       └── with-superpowers.md
│
├── layouts/
│   ├── specguard-default/manifest.yaml
│   ├── superpowers/manifest.yaml
│   └── openspec-sidecar/manifest.yaml
│
├── adapters/
│   └── claude/
│       ├── manifest.yaml
│       ├── plugin/.claude-plugin/plugin.json.tpl
│       ├── plugin/skills/design-governance/SKILL.md.tpl
│       ├── plugin/commands/init.md.tpl
│       ├── plugin/commands/check.md.tpl
│       ├── plugin/commands/upgrade.md.tpl
│       └── plugin/hooks/settings.json.snippet.tpl
│
├── src/specguard/
│   ├── __init__.py
│   ├── render.py                       # 渲染主逻辑
│   └── manifest.py                     # adapter / layout manifest 解析
│
├── tests/
│   ├── conftest.py
│   ├── test_manifest.py
│   ├── test_render_claude_default.py
│   ├── test_render_claude_openspec.py
│   ├── test_render_claude_superpowers.py
│   └── fixtures/
│       └── (生成产物比对用)
│
└── docs/specguard/                     # 已存在，dogfood 自身治理
    ├── design.md
    ├── decisions/...
    └── specs/2026-04-30-mvp-scaffold-spec.md
```

---

## 任务总览

| Task | 内容 | 产出 |
|---|---|---|
| 1 | 项目骨架（pyproject / .gitignore / 初始 commit） | 可 `uv sync` 跑 pytest |
| 2 | 写 core/rules（五条铁律 + ADR checklist + design-sync） | 三份 md 内容固化 |
| 3 | 写 core/templates（design / decisions / specs 模板） | 模板带变量占位 |
| 4 | 写 core/command-prompts（init / check / upgrade） | 三份命令 prompt |
| 5 | 写 core/policies（with-openspec / with-superpowers） | 两份 policy |
| 6 | 写 layouts/* manifest.yaml（三个 layout） | yaml 描述 paths 与注入策略 |
| 7 | 写 adapters/claude manifest 与所有 .tpl | 含 plugin.json / SKILL / commands / hooks snippet |
| 8 | 实现 `manifest.py` 解析 + 校验 | 单元测试通过 |
| 9 | 实现 `render.py` 渲染主流程 | CLI 入口 `python -m specguard.render` |
| 10 | 写 fixture 测试：claude+default | 端到端通过 |
| 11 | 写 fixture 测试：claude+openspec、claude+superpowers | 端到端通过 |
| 12 | 渲染产物在 guard-ghost dogfood 验证 | dogfood 报告 |
| 13 | 写 CHANGELOG + 更新 README | 发布前文档就位 |

每个 task 都按 TDD：先 fail test → 写实现 → pass test → commit。

---

## Task 1: 项目骨架（uv + pyproject + pytest）

**Files:**
- Create: `specguard/pyproject.toml`
- Create: `specguard/.gitignore`
- Create: `specguard/src/specguard/__init__.py`
- Create: `specguard/tests/__init__.py`
- Create: `specguard/tests/test_smoke.py`

- [ ] **Step 1: 初始化 uv 项目并写 pyproject.toml**

写入 `pyproject.toml`：

```toml
[project]
name = "specguard"
version = "0.1.0"
description = "Project governance scaffold for AI-driven development"
requires-python = ">=3.11"
dependencies = [
    "PyYAML>=6.0",
    "Jinja2>=3.1",
]

[project.scripts]
specguard-render = "specguard.render:main"

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/specguard"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 写 .gitignore**

写入 `.gitignore`：

```text
.venv/
__pycache__/
*.pyc
.pytest_cache/
dist/
build/
*.egg-info/
```

- [ ] **Step 3: 创建 package**

写入 `src/specguard/__init__.py`：

```python
__version__ = "0.1.0"
```

写入 `tests/__init__.py`：（空文件）

- [ ] **Step 4: 写 smoke 测试**

写入 `tests/test_smoke.py`：

```python
def test_import():
    import specguard
    assert specguard.__version__ == "0.1.0"
```

- [ ] **Step 5: uv sync + pytest**

Run:
```bash
cd /Users/saber/aiworkspace/multi-agents/specguard
uv sync
uv run pytest tests/test_smoke.py -v
```

Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore src/ tests/
git commit -m "chore: bootstrap specguard project skeleton"
```

---

## Task 2: 写 core/rules（治理资产正文）

**Files:**
- Create: `core/version`
- Create: `core/rules/five-laws.md`
- Create: `core/rules/adr-checklist.md`
- Create: `core/rules/design-sync.md`

注意：core 文件中所有项目路径用变量 `{{ paths.design }}` / `{{ paths.decisions_dir }}` / `{{ paths.specs_dir }}` / `{{ paths.plans_dir }}`。

- [ ] **Step 1: 写 core/version**

写入 `core/version`：

```text
0.1.0
```

- [ ] **Step 2: 写 five-laws.md**

写入 `core/rules/five-laws.md`：

```markdown
1. `{{ paths.design }}` 是当前架构唯一真相；写代码前必须先读它。
2. 决策档案在 `{{ paths.decisions_dir }}/`；写新 ADR 前必须先查看既有 ADR。
3. 禁止新建 dated design 文件（如 `*-design.md`）；新切片写 `*-spec.md`，架构变更直接更新 design.md。
4. ADR 只用于五类硬条件：接口语义、数据格式、跨模块依赖、外部依赖、推翻既有设计；其他默认不写。
5. 接口/数据结构/模块边界变更必须同步 `{{ paths.design }}`；命中硬条件时还要写 ADR。
```

- [ ] **Step 3: 写 adr-checklist.md**

写入 `core/rules/adr-checklist.md`：

```markdown
对本次需求的每个改动点，逐条匹配五条硬条件：

- [ ] 是否改变了某个对外接口的输入/输出/失败语义/调用约束？
- [ ] 是否改变了某个文件格式、数据 schema、字段语义到不向前兼容？
- [ ] 是否新增/移除/反转了模块间依赖关系？
- [ ] 是否新增/替换/移除了第三方库、外部服务、子进程?
- [ ] 是否与 design.md 或既有 ADR 中明确陈述的约束冲突？

任意一条 yes → 候选 ADR。
所有都 no → 不写 ADR，但仍要判断是否需要同步 design.md。

候选 ADR 必须列给用户拍板，AI 不能单方面写架构 ADR。

输出格式（写入切片 spec 的"ADR 级别决策识别"节）：
- 改动点拆解（编号列表）
- 五条硬条件匹配表（表格化）
- 候选 ADR + 灰色地带（请用户拍板）
- 不需要 ADR 的改动点 + 理由
```

- [ ] **Step 4: 写 design-sync.md**

写入 `core/rules/design-sync.md`：

```markdown
- 接口、数据结构、模块边界变化 → 必须同步 `{{ paths.design }}` 对应段落（默认动作，不询问）。
- 编辑 `{{ paths.design }}` 后更新顶部 `Last verified against code` 字段为当前 commit hash。
- 不允许在 `{{ paths.design }}` 中保留与代码不一致的陈述。
- mermaid 图与文字描述若不一致，文字为准，同步修图。
- 写 ADR 后，在 `{{ paths.design }}` 对应章节末尾追加 `（见 ADR-NNNN）`，并在 `{{ paths.decisions_dir }}/README.md` 索引表加一行。
```

- [ ] **Step 5: Commit**

```bash
git add core/
git commit -m "feat(core): add governance rules (five laws, adr checklist, design sync)"
```

---

## Task 3: 写 core/templates（项目落地模板）

**Files:**
- Create: `core/templates/design.md.tpl`
- Create: `core/templates/decisions/README.md.tpl`
- Create: `core/templates/decisions/TEMPLATE.md.tpl`
- Create: `core/templates/specs/TEMPLATE.md.tpl`

模板使用 Jinja2 风格变量。`.tpl` 后缀防止 plugin 自身被 hooks 拦。

- [ ] **Step 1: 写 design.md.tpl**

写入 `core/templates/design.md.tpl`：

```markdown
# {{ project.name | default("Project") }} 设计（Living Document）

**Last verified against code**: {{ today }} @ commit `<HEAD hash>`
**Authoritative for**: 全文
**ADR 索引**: [{{ paths.decisions_dir }}/README.md]({{ paths.decisions_dir | relative_to_design }}/README.md)

> 本文档是项目架构当前真相。代码与本文档不一致即为缺陷。
> 决策动机与历史在 decisions/，本文档只反映"现在是什么"。

---

## 1. 设计方向

（待项目填入。若已有 design 内容，init 时不会覆盖此处。）

---

## 17. 与项目原则的对应

（可选：列出宪法/原则与本文章节的映射）
```

- [ ] **Step 2: 写 decisions/README.md.tpl**

写入 `core/templates/decisions/README.md.tpl`：

```markdown
# 决策档案（Architecture Decision Records）

本目录沉淀 {{ project.name | default("项目") }} 的架构决策。

## ADR 五类硬条件

只写以下五类决策：

1. 接口语义改变
2. 数据格式不兼容
3. 跨模块依赖关系改变
4. 外部依赖引入或替换
5. 推翻先前 design 或 ADR

不写 ADR：任务、实现细节、参数默认值、命名、首次实施既有设计。

## 命名规范

- `NNNN-kebab-case-slug.md`，4 位编号连续
- 例外：`README.md`、`TEMPLATE.md`

## 状态字段

- `Accepted` / `Superseded by ADR-NNNN` / `Deprecated`

## ADR 索引

| 编号 | 标题 | 状态 | 关联 design 章节 |
|---|---|---|---|
```

- [ ] **Step 3: 写 decisions/TEMPLATE.md.tpl**

写入 `core/templates/decisions/TEMPLATE.md.tpl`：

```markdown
# ADR NNNN: <一句话标题>

**状态**：Accepted | Superseded by ADR-NNNN | Deprecated
**日期**：YYYY-MM-DD
**拍板者**：用户（@用户名，对话日期 YYYY-MM-DD，参考 <文档路径> §X）| AI 推理（依据：...）
**取代**：—  或  ADR-NNNN
**相关**：design.md §X / spec docs/.../<file>.md

## Context
（1-3 段：当前情况、约束、为什么现在要决策。
**只允许写本次对话/文档中出现过的事实信息，不允许补全推理动机**。）

## Decision
（1-2 段：决定做什么。简洁，不长篇大论。）

## Consequences
- **正面**：
- **负面**：
- **同步更新**：design.md §X / 哪些代码（具体到文件路径）
```

- [ ] **Step 4: 写 specs/TEMPLATE.md.tpl**

写入 `core/templates/specs/TEMPLATE.md.tpl`：

```markdown
# <切片名> 设计补充

**日期**：YYYY-MM-DD
**适用范围**：<明确的切片边界>

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解
1. <具体改动 1>
2. ...

### 五条硬条件匹配
| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 | - | - | - | - | - |

### 候选 ADR（请用户拍板）
- ADR 候选: <标题> —— 命中条件 X+Y
- 灰色地带: <描述>

### 不需要 ADR
- #1 等：<理由>

## 对 design.md 的影响（必填）
- §X：<具体段落变化>

## 1. 切片范围
## 2. 验收标准
## 3. 留给后续切片的事
```

- [ ] **Step 5: Commit**

```bash
git add core/templates/
git commit -m "feat(core): add design/adr/spec templates"
```

---

## Task 4: 写 core/command-prompts（init/check/upgrade 三个命令的核心 prompt）

**Files:**
- Create: `core/command-prompts/init.md`
- Create: `core/command-prompts/check.md`
- Create: `core/command-prompts/upgrade.md`

- [ ] **Step 1: 写 init.md**

写入 `core/command-prompts/init.md`：

```markdown
# specguard init

You are specguard init. Initialize governance scaffolding in the current project.

## Arguments

User-provided: $ARGUMENTS
Supported flags:
- --ai <claude|cursor|codex|generic|auto>   default: auto
- --spec <none|openspec|superpowers|auto>   default: auto

## Steps

1. Parse arguments. If `auto`, detect:
   - agent: presence of `.claude/`, `.cursor/`, `AGENTS.md`
   - spec: presence of `openspec/`, `docs/superpowers/`
   - If multiple detected, ask user to choose; do not silently fallback.

2. Resolve layout:
   - `--spec none` → layout `specguard-default`
   - `--spec superpowers` → layout `superpowers`
   - `--spec openspec` → layout `openspec-sidecar`

3. For each path in layout (`paths.design`, `paths.decisions_dir`, `paths.specs_dir`, `paths.plans_dir`):
   - If file exists, skip and report.
   - If missing, render template from plugin.

4. Update `CLAUDE.md`:
   - If file exists, look for `<!-- specguard:start -->` ... `<!-- specguard:end -->` block.
   - If block exists, replace its content; if missing, insert block at top.
   - Inside block: render five-laws + adr-checklist + design-sync + (if --spec is openspec or superpowers) the corresponding policy.

5. Update `.claude/settings.json`:
   - Merge specguard hooks (identifiable by `statusMessage` prefix `specguard:`) into existing settings.
   - Do not duplicate hooks already present.

6. Write `.specguard-version`:
   ```toml
   specguard_version = "<plugin core version>"
   agent = "<resolved agent>"
   spec = "<resolved spec>"
   layout = "<resolved layout>"
   installed_at = "<ISO 8601 now>"
   ```

7. Output report:
   - Created: <files>
   - Updated: <files>
   - Skipped: <files with reason>
   - Next steps: read design.md, run /sg:check
```

- [ ] **Step 2: 写 check.md**

写入 `core/command-prompts/check.md`：

```markdown
# specguard check

Validate the governance state of the current project.

## Arguments

User-provided: $ARGUMENTS
Optional positional: `semantic` (generates AI review package; does not call any LLM)

## Structural checks

1. `{{ paths.design }}` exists and is the only design file (no other `*-design.md` under specs).
2. No file matching `{{ paths.specs_dir }}/*-design.md`.
3. `{{ paths.decisions_dir }}/README.md` exists.
4. Every ADR file matches `^[0-9]{4}-[a-z0-9-]+\.md$` or is `README.md` / `TEMPLATE.md`.
5. ADR numbers are contiguous (no gaps).
6. Every ADR appears in `{{ paths.decisions_dir }}/README.md` index.
7. Every ADR-NNNN referenced in `{{ paths.design }}` exists.
8. Every `Superseded by ADR-NNNN` target exists.
9. Every `*.md` under `{{ paths.specs_dir }}` (excluding TEMPLATE.md) contains the heading `## ADR 级别决策识别`.
10. `CLAUDE.md` contains `<!-- specguard:start -->` and `<!-- specguard:end -->`.
11. `.claude/settings.json` contains hooks tagged with `statusMessage` prefix `specguard:` matching adapter manifest.
12. `.specguard-version` exists.

If layout is `openspec-sidecar`, additionally:
- For each archived OpenSpec change, if its `design.md` mentions a decision, warn if `decisions/` has no corresponding ADR.

## Output

Print a structured report:

```
SpecGuard Check (agent=<x>, spec=<x>, layout=<x>)

✓ design.md exists
⚠️ ADR-0005 missing from decisions/README.md index
❌ design.md references ADR-0006 but file does not exist

Summary: 1 error, 1 warning
```

## Semantic mode

If argument `semantic` is provided, additionally:
1. Create `.specguard/reviews/<UTC YYYYMMDD-HHMM>/`
2. Write `prompt.md`: instructions for an LLM to review ADR Context plausibility, missed ADR judgement, design.md drift.
3. Write `context.md`: assembled excerpts from design.md, decisions index, latest spec, latest plan.
4. Write `findings-template.md`: structured output format for the LLM.
5. Do NOT call any LLM. Tell the user to feed `prompt.md + context.md` to Claude Code / Cursor / any LLM.
```

- [ ] **Step 3: 写 upgrade.md**

写入 `core/command-prompts/upgrade.md`：

```markdown
# specguard upgrade

Upgrade specguard scaffolding in the current project to the plugin's current core version.

## Steps

1. Read `.specguard-version`. If missing, ask user whether to treat project as legacy and run init-then-upgrade.

2. Compare `specguard_version` to plugin's `core/version`. If equal, output "already up to date" and exit.

3. Build upgrade plan by inspecting marker regions:
   - `CLAUDE.md` block between `<!-- specguard:start -->` and `<!-- specguard:end -->`
   - `.claude/settings.json` hooks identifiable by `statusMessage` prefix `specguard:`
   - `{{ paths.specs_dir }}/TEMPLATE.md`
   - `{{ paths.decisions_dir }}/TEMPLATE.md`
   - `{{ paths.decisions_dir }}/README.md` rule sections

4. Print diff summary per region. Files outside markers are never touched. Summary format:

```
SpecGuard upgrade <old> → <new>

Will update:
✓ CLAUDE.md specguard block (3 lines changed)
✓ specs/TEMPLATE.md (added new required field)
✓ UserPromptSubmit hook command updated

Will not touch:
- design.md content
- existing ADR files
- existing spec files
```

5. Ask user to confirm.

6. On confirm, replace marker contents only. If a marker is missing in a target file:
   - Do NOT auto-insert.
   - Report conflict and offer options: insert new block / show manual patch / skip.

7. Update `.specguard-version` with new version.

8. Print final report.
```

- [ ] **Step 4: Commit**

```bash
git add core/command-prompts/
git commit -m "feat(core): add init/check/upgrade command prompts"
```

---

## Task 5: 写 core/policies（与 OpenSpec / Superpowers 协作的注入文）

**Files:**
- Create: `core/policies/with-openspec.md`
- Create: `core/policies/with-superpowers.md`

- [ ] **Step 1: 写 with-openspec.md**

写入 `core/policies/with-openspec.md`：

```markdown
## 与 OpenSpec 协作

OpenSpec 仍按其本身流程使用：proposal / change / archive 在 `openspec/`。
specguard 仅补充以下治理约束：

1. 写 OpenSpec proposal 前，先读 `{{ paths.design }}` + `{{ paths.decisions_dir }}/`。
2. OpenSpec proposal 的 `design.md` 若产生 ADR 级别决策，必须新增 ADR 到 `{{ paths.decisions_dir }}/`。
3. OpenSpec change archive 后，若改变当前架构，必须同步 `{{ paths.design }}`。
4. 长期架构决策不得只留在 `openspec/changes/archive/`，必须沉淀到 ADR。
```

- [ ] **Step 2: 写 with-superpowers.md**

写入 `core/policies/with-superpowers.md`：

```markdown
## 与 superpowers 协作

如当前项目使用 superpowers skills，建议：

1. 设计探索阶段优先调用 `superpowers:brainstorming`。
2. 计划阶段优先调用 `superpowers:writing-plans`。
3. 实施阶段可使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`。

但以下规则**始终**优先于 superpowers 默认行为：

- 禁止新建 `{{ paths.specs_dir }}/*-design.md`。新切片用 `*-spec.md`。
- spec 必须包含 `## ADR 级别决策识别` 节。
- 进入 plan 之前必须由用户拍板候选 ADR。
- 实施过程中接口/数据/边界变更必须同步 `{{ paths.design }}`。
```

- [ ] **Step 3: Commit**

```bash
git add core/policies/
git commit -m "feat(core): add openspec/superpowers integration policies"
```

---

## Task 6: 写 layouts/* manifest.yaml

**Files:**
- Create: `layouts/specguard-default/manifest.yaml`
- Create: `layouts/superpowers/manifest.yaml`
- Create: `layouts/openspec-sidecar/manifest.yaml`

- [ ] **Step 1: 写 specguard-default**

写入 `layouts/specguard-default/manifest.yaml`：

```yaml
name: specguard-default
description: Default layout for projects without an existing spec tool.
detection:
  none: true
paths:
  design: docs/specguard/design.md
  decisions_dir: docs/specguard/decisions
  specs_dir: docs/specguard/specs
  plans_dir: docs/specguard/plans
inject_policies: []
```

- [ ] **Step 2: 写 superpowers**

写入 `layouts/superpowers/manifest.yaml`：

```yaml
name: superpowers
description: Layout for projects already using superpowers skill suite.
detection:
  exists: docs/superpowers
paths:
  design: docs/superpowers/design.md
  decisions_dir: docs/superpowers/decisions
  specs_dir: docs/superpowers/specs
  plans_dir: docs/superpowers/plans
inject_policies:
  - core/policies/with-superpowers.md
```

- [ ] **Step 3: 写 openspec-sidecar**

写入 `layouts/openspec-sidecar/manifest.yaml`：

```yaml
name: openspec-sidecar
description: SpecGuard sidecar for projects using OpenSpec. specguard manages design.md/ADR; openspec keeps its own structure.
detection:
  exists: openspec
paths:
  design: docs/specguard/design.md
  decisions_dir: docs/specguard/decisions
  specs_dir: openspec/specs
  plans_dir: docs/specguard/plans
  changes_dir: openspec/changes
inject_policies:
  - core/policies/with-openspec.md
```

- [ ] **Step 4: Commit**

```bash
git add layouts/
git commit -m "feat(layouts): add three layout manifests (default/superpowers/openspec-sidecar)"
```

---

## Task 7: 写 adapters/claude

**Files:**
- Create: `adapters/claude/manifest.yaml`
- Create: `adapters/claude/plugin/.claude-plugin/plugin.json.tpl`
- Create: `adapters/claude/plugin/skills/design-governance/SKILL.md.tpl`
- Create: `adapters/claude/plugin/commands/init.md.tpl`
- Create: `adapters/claude/plugin/commands/check.md.tpl`
- Create: `adapters/claude/plugin/commands/upgrade.md.tpl`
- Create: `adapters/claude/plugin/hooks/settings.json.snippet.tpl`

- [ ] **Step 1: 写 adapters/claude/manifest.yaml**

```yaml
target: claude
description: Claude Code plugin adapter for specguard
capabilities:
  - skills
  - commands
  - hooks
  - plugin

renders:
  - source: plugin/.claude-plugin/plugin.json.tpl
    output: .claude-plugin/plugin.json
  - source: plugin/skills/design-governance/SKILL.md.tpl
    output: skills/design-governance/SKILL.md
    inject:
      - source: core/rules/five-laws.md
        marker: <!-- inject:five-laws -->
      - source: core/rules/adr-checklist.md
        marker: <!-- inject:adr-checklist -->
      - source: core/rules/design-sync.md
        marker: <!-- inject:design-sync -->
  - source: plugin/commands/init.md.tpl
    output: commands/init.md
    inject:
      - source: core/command-prompts/init.md
        marker: <!-- inject:prompt -->
  - source: plugin/commands/check.md.tpl
    output: commands/check.md
    inject:
      - source: core/command-prompts/check.md
        marker: <!-- inject:prompt -->
  - source: plugin/commands/upgrade.md.tpl
    output: commands/upgrade.md
    inject:
      - source: core/command-prompts/upgrade.md
        marker: <!-- inject:prompt -->
  - source: plugin/hooks/settings.json.snippet.tpl
    output: hooks/settings.json.snippet
```

- [ ] **Step 2: 写 plugin.json.tpl**

写入 `adapters/claude/plugin/.claude-plugin/plugin.json.tpl`：

```json
{
  "name": "specguard",
  "version": "{{ specguard_version }}",
  "description": "Living design + ADR governance scaffold for AI-assisted projects",
  "commandNamespace": "sg"
}
```

- [ ] **Step 3: 写 SKILL.md.tpl**

写入 `adapters/claude/plugin/skills/design-governance/SKILL.md.tpl`：

```markdown
---
name: design-governance
description: Use when starting or changing a feature, writing specs or plans, making architecture decisions, updating design docs, creating ADRs, or reviewing whether AI coding work may drift from project architecture
---

# Design Governance

## Overview
specguard enforces living design + ADR governance for AI-assisted projects.
This skill is agent and spec-tool agnostic.

## Non-Negotiables
<!-- inject:five-laws -->

## Required Workflow
1. Read `{{ paths.design }}` and `{{ paths.decisions_dir }}/`.
2. Explore design before implementation.
3. Produce a slice spec containing the `## ADR 级别决策识别` section.
4. Ask the user to approve candidate ADRs.
5. Write a plan only after the spec is approved.
6. Sync `{{ paths.design }}` after interface/data/boundary changes.

## ADR Decision Assessment
<!-- inject:adr-checklist -->

## design.md Sync Rules
<!-- inject:design-sync -->

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

- [ ] **Step 4: 写 commands/*.md.tpl**

写入 `adapters/claude/plugin/commands/init.md.tpl`：

```markdown
---
description: Initialize specguard governance scaffold
argument-hint: [--ai <agent>] [--spec <tool>]
---

<!-- inject:prompt -->
```

写入 `adapters/claude/plugin/commands/check.md.tpl`：

```markdown
---
description: Check specguard governance state
argument-hint: [semantic]
---

<!-- inject:prompt -->
```

写入 `adapters/claude/plugin/commands/upgrade.md.tpl`：

```markdown
---
description: Upgrade specguard scaffold to current plugin version
---

<!-- inject:prompt -->
```

- [ ] **Step 5: 写 hooks snippet**

写入 `adapters/claude/plugin/hooks/settings.json.snippet.tpl`：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: inject five laws",
            "command": "printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"## SpecGuard governance laws\\n1. {{ paths.design }} is the single current truth.\\n2. ADR archive is at {{ paths.decisions_dir }}/. Read existing ADRs before writing a new one.\\n3. Do not create dated design files. New slices go to *-spec.md.\\n4. ADR is only for: interface semantics, data format, cross-module dependency, external dependency, overriding prior design.\\n5. Brainstorm must produce an ADR judgement before writing a plan.\"}}}'"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: block dated design",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *{{ paths.specs_dir }}/*-design.md) printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: dated design files are forbidden. Update {{ paths.design }} or write {{ paths.specs_dir }}/<topic>-spec.md instead.\"}}}' ;; *) printf '%s\\n' '{}' ;; esac"
          },
          {
            "type": "command",
            "statusMessage": "specguard: validate adr filename",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *{{ paths.decisions_dir }}/*.md) base=$(basename \"$f\"); if echo \"$base\" | grep -qE '^[0-9]{4}-[a-z0-9-]+\\.md$|^TEMPLATE\\.md$|^README\\.md$'; then printf '%s\\n' '{}'; else printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: ADR filename must be NNNN-kebab-case.md\"}}}'; fi ;; *) printf '%s\\n' '{}' ;; esac"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: design sync reminder",
            "command": "cd \"$CLAUDE_PROJECT_DIR\" 2>/dev/null || exit 0; src_changed=$(git diff --name-only HEAD 2>/dev/null | grep -c '^src/' || true); doc_changed=$(git diff --name-only HEAD 2>/dev/null | grep -cE '^({{ paths.design | regex_escape }}|{{ paths.decisions_dir | regex_escape }}/)' || true); if [ \"$src_changed\" -gt 0 ] && [ \"$doc_changed\" -eq 0 ]; then printf '%s\\n' '{\"systemMessage\":\"specguard: src/ changed but neither design.md nor decisions/ touched.\"}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: adr judgement reminder",
            "command": "p=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"prompt\") or d.get(\"user_prompt\") or \"\")'); if echo \"$p\" | grep -qiE '(write spec|write plan|implement now|开始实施|写 spec|写 plan)'; then printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"specguard: produce the ADR judgement section before entering spec/plan, and wait for user approval.\"}}}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add adapters/
git commit -m "feat(adapters/claude): add manifest and plugin templates"
```

---

## Task 8: 实现 manifest.py（解析 + 校验 layout / adapter manifest）

**Files:**
- Create: `src/specguard/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: 写失败测试**

写入 `tests/test_manifest.py`：

```python
from pathlib import Path

import pytest

from specguard.manifest import LayoutManifest, AdapterManifest, ManifestError


REPO = Path(__file__).resolve().parents[1]


def test_load_specguard_default_layout():
    m = LayoutManifest.load(REPO / "layouts/specguard-default/manifest.yaml")
    assert m.name == "specguard-default"
    assert m.paths["design"] == "docs/specguard/design.md"
    assert m.paths["decisions_dir"] == "docs/specguard/decisions"
    assert m.paths["specs_dir"] == "docs/specguard/specs"
    assert m.paths["plans_dir"] == "docs/specguard/plans"
    assert m.inject_policies == []


def test_load_superpowers_layout():
    m = LayoutManifest.load(REPO / "layouts/superpowers/manifest.yaml")
    assert m.paths["specs_dir"] == "docs/superpowers/specs"
    assert "core/policies/with-superpowers.md" in m.inject_policies


def test_load_openspec_sidecar_layout():
    m = LayoutManifest.load(REPO / "layouts/openspec-sidecar/manifest.yaml")
    assert m.paths["specs_dir"] == "openspec/specs"
    assert m.paths["changes_dir"] == "openspec/changes"


def test_load_claude_adapter():
    m = AdapterManifest.load(REPO / "adapters/claude/manifest.yaml")
    assert m.target == "claude"
    assert "skills" in m.capabilities
    assert "hooks" in m.capabilities
    assert any("plugin.json" in r["output"] for r in m.renders)


def test_layout_missing_required_path_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: bad\npaths:\n  design: x\n")  # missing other paths
    with pytest.raises(ManifestError):
        LayoutManifest.load(bad)


def test_adapter_missing_target_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("description: x\nrenders: []\n")
    with pytest.raises(ManifestError):
        AdapterManifest.load(bad)
```

- [ ] **Step 2: 跑测试，确认 fail**

```bash
uv run pytest tests/test_manifest.py -v
```

Expected: ModuleNotFoundError on `specguard.manifest`

- [ ] **Step 3: 写实现**

写入 `src/specguard/manifest.py`：

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


REQUIRED_LAYOUT_PATHS = {"design", "decisions_dir", "specs_dir", "plans_dir"}


class ManifestError(ValueError):
    """Raised when a manifest file is malformed."""


@dataclass
class LayoutManifest:
    name: str
    description: str
    paths: dict[str, str]
    inject_policies: list[str] = field(default_factory=list)
    detection: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "LayoutManifest":
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ManifestError(f"layout manifest must be a mapping: {path}")
        for key in ("name", "paths"):
            if key not in data:
                raise ManifestError(f"layout manifest missing '{key}': {path}")
        paths = data["paths"]
        if not isinstance(paths, dict):
            raise ManifestError(f"layout 'paths' must be a mapping: {path}")
        missing = REQUIRED_LAYOUT_PATHS - set(paths.keys())
        if missing:
            raise ManifestError(
                f"layout '{data['name']}' missing required paths: {sorted(missing)}"
            )
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            paths=paths,
            inject_policies=list(data.get("inject_policies") or []),
            detection=data.get("detection") or {},
        )


@dataclass
class AdapterManifest:
    target: str
    description: str
    capabilities: list[str]
    renders: list[dict[str, Any]]

    @classmethod
    def load(cls, path: Path) -> "AdapterManifest":
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ManifestError(f"adapter manifest must be a mapping: {path}")
        for key in ("target", "renders"):
            if key not in data:
                raise ManifestError(f"adapter manifest missing '{key}': {path}")
        return cls(
            target=data["target"],
            description=data.get("description", ""),
            capabilities=list(data.get("capabilities") or []),
            renders=list(data["renders"]),
        )
```

- [ ] **Step 4: 跑测试，确认 pass**

```bash
uv run pytest tests/test_manifest.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/specguard/manifest.py tests/test_manifest.py
git commit -m "feat: add layout/adapter manifest parser"
```

---

## Task 9: 实现 render.py（核心渲染流程）

**Files:**
- Create: `src/specguard/render.py`
- Create: `tests/test_render_basic.py`

注意：render.py 是 build-time 工具，把 `core + layout + adapter` 渲染成 `dist/<target>/<layout>/`。运行时（用户跑 `/sg:init`）不会调它——init 时 AI 直接读 plugin 内已渲染的 templates 与 commands。

但 plugin 自身还需要解析"用户实际 layout"的运行时变量。MVP 简化：plugin 发布时已**预渲染** specguard-default 路径；当 AI 跑 init 看到用户选 superpowers / openspec-sidecar 时，AI 自行从 commands 中的逻辑替换 `{{ paths.* }}`（command prompt 里包含三种路径表）。

→ 因此 render.py 主要负责：
1. 读 layout manifest + adapter manifest
2. 把 core/rules + core/policies inject 到 adapter templates
3. 替换 `{{ paths.* }}` 与 `{{ specguard_version }}`
4. 写到 `dist/<target>/<layout>/`

MVP **每个 layout 渲染一次**，得到三套 dist：

```text
dist/claude/specguard-default/
dist/claude/superpowers/
dist/claude/openspec-sidecar/
```

发布时 `dist/claude/<layout>/` 都打进同一个 plugin 包；AI 在 init 时根据 `--spec` 选用对应子目录的 commands / hooks。

简化：MVP 仅渲染 `specguard-default`；`/sg:init` 命令的 prompt 内置三个 layout 的 paths 表，由 AI 在运行时按用户选择改 path。

- [ ] **Step 1: 写失败测试**

写入 `tests/test_render_basic.py`：

```python
from pathlib import Path

import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_creates_dist(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    assert (out / ".claude-plugin/plugin.json").is_file()
    assert (out / "skills/design-governance/SKILL.md").is_file()
    assert (out / "commands/init.md").is_file()
    assert (out / "commands/check.md").is_file()
    assert (out / "commands/upgrade.md").is_file()
    assert (out / "hooks/settings.json.snippet").is_file()


def test_render_injects_five_laws(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    skill_md = (out / "skills/design-governance/SKILL.md").read_text()
    assert "specguard" in skill_md.lower()
    assert "<!-- inject:five-laws -->" not in skill_md  # marker replaced
    assert "ADR" in skill_md


def test_render_substitutes_paths_in_skill(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    skill_md = (out / "skills/design-governance/SKILL.md").read_text()
    assert "docs/specguard/design.md" in skill_md
    assert "{{ paths.design }}" not in skill_md


def test_render_substitutes_version(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    plugin_json = (out / ".claude-plugin/plugin.json").read_text()
    expected = (REPO / "core/version").read_text().strip()
    assert expected in plugin_json
    assert "{{ specguard_version }}" not in plugin_json


def test_render_unknown_layout_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        render(repo_root=REPO, target="claude", layout="does-not-exist", out_dir=tmp_path)
```

- [ ] **Step 2: 跑测试，确认 fail**

```bash
uv run pytest tests/test_render_basic.py -v
```

Expected: ModuleNotFoundError on `specguard.render`

- [ ] **Step 3: 写实现**

写入 `src/specguard/render.py`：

```python
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, BaseLoader, StrictUndefined

from .manifest import AdapterManifest, LayoutManifest


def render(
    repo_root: Path,
    target: str,
    layout: str,
    out_dir: Path,
) -> None:
    """Render core + layout + adapter into out_dir."""
    layout_manifest_path = repo_root / "layouts" / layout / "manifest.yaml"
    if not layout_manifest_path.is_file():
        raise FileNotFoundError(f"layout not found: {layout_manifest_path}")
    adapter_manifest_path = repo_root / "adapters" / target / "manifest.yaml"
    if not adapter_manifest_path.is_file():
        raise FileNotFoundError(f"adapter not found: {adapter_manifest_path}")

    layout_m = LayoutManifest.load(layout_manifest_path)
    adapter_m = AdapterManifest.load(adapter_manifest_path)

    version = (repo_root / "core/version").read_text().strip()

    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    env.filters["regex_escape"] = lambda s: re.escape(str(s))

    context = {
        "paths": layout_m.paths,
        "specguard_version": version,
    }

    for entry in adapter_m.renders:
        src_path = repo_root / "adapters" / target / entry["source"]
        out_path = out_dir / entry["output"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        text = src_path.read_text()

        for inj in entry.get("inject", []) or []:
            inj_text = (repo_root / inj["source"]).read_text()
            text = text.replace(inj["marker"], inj_text)

        rendered = env.from_string(text).render(**context)
        out_path.write_text(rendered)


def main() -> None:  # entry point: specguard-render
    import argparse

    parser = argparse.ArgumentParser(prog="specguard-render")
    parser.add_argument("--target", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo", default=Path(__file__).resolve().parents[2], type=Path)
    args = parser.parse_args()

    render(
        repo_root=args.repo,
        target=args.target,
        layout=args.layout,
        out_dir=args.out,
    )
    print(f"rendered {args.target}/{args.layout} -> {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试，确认 pass**

```bash
uv run pytest tests/test_render_basic.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/specguard/render.py tests/test_render_basic.py
git commit -m "feat: add render() for core + layout + adapter pipeline"
```

---

## Task 10: fixture 测试 — claude + specguard-default

**Files:**
- Create: `tests/test_render_claude_default.py`

- [ ] **Step 1: 写测试**

```python
from pathlib import Path

import json
import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    return out


def test_plugin_json_namespace(dist: Path):
    data = json.loads((dist / ".claude-plugin/plugin.json").read_text())
    assert data["name"] == "specguard"
    assert data["commandNamespace"] == "sg"


def test_skill_contains_three_injected_sections(dist: Path):
    skill = (dist / "skills/design-governance/SKILL.md").read_text()
    assert "ADR 级别决策识别" not in skill or "spec" in skill.lower()
    # all inject markers replaced
    assert "<!-- inject:" not in skill
    # paths substituted
    assert "{{" not in skill
    # contains content from each rule file
    assert "design.md" in skill
    assert "ADR" in skill


def test_command_files_have_frontmatter(dist: Path):
    for name in ("init", "check", "upgrade"):
        cmd = (dist / f"commands/{name}.md").read_text()
        assert cmd.startswith("---\n")
        assert "<!-- inject:" not in cmd


def test_hooks_snippet_is_valid_json(dist: Path):
    snippet_path = dist / "hooks/settings.json.snippet"
    text = snippet_path.read_text()
    data = json.loads(text)
    assert "hooks" in data
    assert "SessionStart" in data["hooks"]
    assert "PreToolUse" in data["hooks"]
    assert "Stop" in data["hooks"]
    assert "UserPromptSubmit" in data["hooks"]


def test_hooks_use_specguard_default_paths(dist: Path):
    snippet = (dist / "hooks/settings.json.snippet").read_text()
    assert "docs/specguard/specs" in snippet
    assert "docs/specguard/decisions" in snippet
```

- [ ] **Step 2: 跑测试**

```bash
uv run pytest tests/test_render_claude_default.py -v
```

Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_render_claude_default.py
git commit -m "test: claude+specguard-default fixture render"
```

---

## Task 11: fixture 测试 — claude + openspec-sidecar / superpowers

**Files:**
- Create: `tests/test_render_claude_openspec.py`
- Create: `tests/test_render_claude_superpowers.py`

- [ ] **Step 1: 写 openspec 测试**

```python
from pathlib import Path

import json

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_openspec_sidecar(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="openspec-sidecar", out_dir=out)
    skill = (out / "skills/design-governance/SKILL.md").read_text()
    # specs path is the openspec path
    assert "openspec/specs" in skill
    # decisions still in docs/specguard
    assert "docs/specguard/decisions" in skill


def test_openspec_hooks_use_correct_paths(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="openspec-sidecar", out_dir=out)
    snippet = json.loads((out / "hooks/settings.json.snippet").read_text())
    # check at least one hook command references openspec/specs
    found = False
    for hooks in snippet["hooks"].values():
        for matcher in hooks:
            for h in matcher["hooks"]:
                if "openspec/specs" in h.get("command", ""):
                    found = True
    assert found, "no hook referenced openspec/specs"
```

- [ ] **Step 2: 写 superpowers 测试**

```python
from pathlib import Path

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_superpowers(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="superpowers", out_dir=out)
    skill = (out / "skills/design-governance/SKILL.md").read_text()
    assert "docs/superpowers/design.md" in skill
    assert "docs/superpowers/decisions" in skill
    assert "docs/superpowers/specs" in skill
```

- [ ] **Step 3: 跑测试**

```bash
uv run pytest tests/test_render_claude_openspec.py tests/test_render_claude_superpowers.py -v
```

Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_render_claude_openspec.py tests/test_render_claude_superpowers.py
git commit -m "test: claude+openspec-sidecar and claude+superpowers fixtures"
```

---

## Task 12: dogfood 验证（在 guard-ghost 比对）

**Files:**
- Create: `tests/test_dogfood_guard_ghost.py`

注意：本 task 假设 guard-ghost 项目已在路径 `~/aiworkspace/multi-agents/guard-ghost`。本测试只检查渲染产物的 hook/SKILL 是否使用 superpowers layout 的路径，不真的去改 guard-ghost。真正在 guard-ghost 跑 `/sg:init` 是手测验收，不写自动化。

- [ ] **Step 1: 写测试**

```python
from pathlib import Path

import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]
GUARD_GHOST = Path("/Users/saber/aiworkspace/multi-agents/guard-ghost")


@pytest.mark.skipif(not GUARD_GHOST.exists(), reason="guard-ghost repo not present")
def test_superpowers_layout_matches_guard_ghost_structure(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="superpowers", out_dir=out)
    # the hooks should target docs/superpowers as guard-ghost does
    snippet = (out / "hooks/settings.json.snippet").read_text()
    assert "docs/superpowers/specs" in snippet
    assert "docs/superpowers/decisions" in snippet
    # confirm guard-ghost actually uses these paths
    assert (GUARD_GHOST / "docs/superpowers/specs").is_dir()
    assert (GUARD_GHOST / "docs/superpowers/decisions").is_dir()
```

- [ ] **Step 2: 跑测试**

```bash
uv run pytest tests/test_dogfood_guard_ghost.py -v
```

Expected: 1 passed (or skipped if guard-ghost missing)

- [ ] **Step 3: 手测说明（写到 README，不在测试里跑）**

人工流程（v0.1 验收时执行一次）：

1. 在 specguard 仓 build 出 plugin：
   ```bash
   uv run specguard-render --target claude --layout superpowers --out dist/claude/superpowers
   ```
2. 在 guard-ghost 仓内手动 link plugin（待 plugin install 流程定下来后补具体命令；MVP 阶段可手工拷贝 dist 到 `~/.claude/plugins/specguard/`）
3. `/sg:init --ai claude --spec superpowers`
4. 检查：
   - 已有 design.md / decisions/ / specs/TEMPLATE.md / CLAUDE.md 内容未被覆盖
   - CLAUDE.md 顶部新增 `<!-- specguard:start v0.1.0 -->` block
   - `.claude/settings.json` 中 specguard hooks 已合并，原 hooks 保留
   - 写出 `.specguard-version`（agent=claude / spec=superpowers / layout=superpowers）
5. `/sg:check`：期望 0 errors（warnings 可接受，list 出来）

- [ ] **Step 4: Commit**

```bash
git add tests/test_dogfood_guard_ghost.py
git commit -m "test: dogfood guard-ghost layout structure check"
```

---

## Task 13: README 更新 + CHANGELOG + 标记 v0.1.0

**Files:**
- Modify: `README.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: 更新 README**

把 README "Status" 表更新到：

```markdown
| Item | State |
|---|---|
| Brainstorm | done |
| Slice spec | done |
| Implementation plan | done |
| Code | v0.1.0 |
| Public release | not yet |
```

加 "Quickstart"：

```markdown
## Quickstart (developers)

```bash
git clone <this repo>
cd specguard
uv sync
uv run pytest
uv run specguard-render --target claude --layout specguard-default --out dist/claude/default
```

The rendered plugin is under `dist/claude/<layout>/`. To install locally, copy that directory into your Claude Code plugin path (e.g. `~/.claude/plugins/specguard/`), then in any target project run `/sg:init --ai claude --spec <none|openspec|superpowers>`. Marketplace packaging is out of MVP scope.
```

- [ ] **Step 2: 写 CHANGELOG**

```markdown
# Changelog

## v0.1.0 - 2026-04-30

Initial design + scaffolding release.

### Added
- core: five laws, ADR checklist, design sync rules
- core: design / ADR / spec templates
- core: init/check/upgrade command prompts
- core: openspec / superpowers integration policies
- layouts: specguard-default, superpowers, openspec-sidecar
- adapters/claude: plugin.json, design-governance skill, three commands, five hooks snippet
- src/specguard: manifest parser, render pipeline
- tests: manifest parser, three layout renders, dogfood path check

### Not yet
- Cursor / Codex adapter
- Python CLI for direct project install
- Built-in LLM semantic check
- OpenSpec inline layout
- PR bot / GitHub Action
```

- [ ] **Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: README quickstart + CHANGELOG v0.1.0"
git tag v0.1.0
```

---

## 完成标志（v0.1.0 Done Criteria）

1. `uv run pytest -v` 全部通过（≥ 13 测试用例）
2. `uv run specguard-render --target claude --layout specguard-default --out dist/claude/default` 成功
3. 同上 `--layout superpowers` 与 `--layout openspec-sidecar` 都成功
4. 渲染产物中无 `<!-- inject:* -->` 残留
5. 渲染产物中无 `{{ paths.* }}` / `{{ specguard_version }}` 残留
6. dogfood 手测通过：在 guard-ghost 跑 `/sg:init --ai claude --spec superpowers` 不破坏既有内容
7. README + CHANGELOG 更新

---

## 与 spec 的对应

本 plan 覆盖 [2026-04-30-mvp-scaffold-spec.md](../specs/2026-04-30-mvp-scaffold-spec.md) §1–§6：

- §1 产品定位：README + CHANGELOG 文案
- §2 架构：core / layouts / adapters/claude 物理目录
- §3 Claude adapter 内容：Task 7 全套 .tpl
- §4 用户流程：command prompts（Task 4）+ hooks snippet（Task 7）
- §5 测试策略：Task 8–12
- §6 验收标准：完成标志清单

§7 不在范围（明确切出，等 v0.2+）。
