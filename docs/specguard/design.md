# specguard 设计（Living Document）

**Last verified against code**: 2026-04-30 @ commit `525b997`
**Authoritative for**: 全文
**ADR 索引**: [decisions/README.md](decisions/README.md)

> 本文档是 specguard 项目当前架构唯一真相。代码与本文档不一致即为缺陷。
> 决策动机与历史在 decisions/，本文档只反映"现在是什么"。

---

## 1. 项目定位

specguard 是一个**项目治理脚手架**：把 living design + ADR 治理体系装进任意 AI 协作的项目，并通过 skill / rules / hooks 让 AI 自动遵守。

它**不是** OpenSpec / Spec Kit / Superpowers 的替代品；它是叠在它们之上的治理层。

---

## 2. 三层架构

```
core/  (agent-neutral + layout-neutral 资产)
   ↑
layouts/  (3 种 spec 工具 layout)
   ↑
adapters/<target>/  (MVP 仅 claude)
   ↑
src/specguard/render.py  (build-time 渲染管线)
   ↓
dist/<target>/<layout>/  (可发布的 plugin 包)
```

### core/

agent-neutral + layout-neutral 治理资产，路径全部使用 `{{ paths.* }}` 变量：

- [core/version](../../core/version) — 当前 specguard 版本（`0.1.0`）
- [core/rules/](../../core/rules) — 五条铁律 / ADR checklist / design 同步规则
- [core/templates/](../../core/templates) — design.md / decisions/* / specs/* 模板（注入 init prompt 时按 `raw: true` 不让 Jinja 求值）
- [core/command-prompts/](../../core/command-prompts) — init / check / upgrade 三个命令的核心 prompt
- [core/policies/](../../core/policies) — 与 OpenSpec / Superpowers 协作的 policy 段

### layouts/

每种 layout 一个 [manifest.yaml](../../layouts/specguard-default/manifest.yaml)，描述：
- `name`：layout 名（写入 `.specguard-version` `layout` 字段）
- `paths.{design, decisions_dir, specs_dir, plans_dir, [changes_dir]}`：项目内目标路径
- `inject_policies`：要嵌入 init prompt 的 core/policies 文件

| layout | design/ADR 位置 | spec 位置 |
|---|---|---|
| `specguard-default` | `docs/specguard/` | `docs/specguard/specs/` |
| `superpowers` | `docs/superpowers/` | `docs/superpowers/specs/` |
| `openspec-sidecar` | `docs/specguard/` | `openspec/specs/` + `openspec/changes/` |

### adapters/claude/

唯一 agent target。[adapters/claude/manifest.yaml](../../adapters/claude/manifest.yaml) 列出 6 个渲染条目：

1. `plugin/.claude-plugin/plugin.json.tpl` → `.claude-plugin/plugin.json`
2. `plugin/skills/design-governance/SKILL.md.tpl` → `skills/design-governance/SKILL.md`，注入 5 laws / ADR checklist / design-sync
3. `plugin/commands/init.md.tpl` → `commands/init.md`，注入 prompt + 5 laws + ADR checklist + design-sync + policy + 4 个 template（`raw`）+ hooks snippet
4. `plugin/commands/check.md.tpl` → `commands/check.md`，注入 prompt
5. `plugin/commands/upgrade.md.tpl` → `commands/upgrade.md`，注入 prompt
6. `plugin/hooks/settings.json.snippet.tpl` → `hooks/settings.json.snippet`

**关键决定**：plugin name = `specguard`，**没有** `commandNamespace` 字段，因此 Claude Code 的 slash 命令固定为 `/specguard:init`、`/specguard:check`、`/specguard:upgrade`（见 [ADR-0001](decisions/0001-plugin-name-command-namespace.md)）。

### src/specguard/

- [manifest.py](../../src/specguard/manifest.py) — `LayoutManifest.load()` / `AdapterManifest.load()`，解析 + 校验 yaml manifest，缺字段抛 `ManifestError`
- [render.py](../../src/specguard/render.py) — `render(repo_root, target, layout, out_dir)` 把 core + layout + adapter 渲染到 `dist/<target>/<layout>/`：
  1. 加载 layout / adapter manifest
  2. 给 Jinja2 注册 `regex_escape`（双反斜杠化以适配 JSON 字面量）和 `relative_to_design`（路径相对 design dir）filter
  3. 上下文 = `{paths, specguard_version, layout_name}`
  4. 按 manifest `renders` 列表逐文件处理：先把 inject 文件文本替换 marker（标 `raw: true` 的注入会被 `{% raw %}{% endraw %}` 包住，避免 Jinja 求值），再替换 layout-specific policy marker，最后整体过 Jinja 渲染
- console script `specguard-render` = `specguard.render:main`，stdlib `argparse`

---

## 3. `/specguard:*` 命令运行时行为

### `/specguard:init`

1. 解析 `--ai` `--spec`（auto 时探测 `.claude/`、`docs/superpowers/`、`openspec/`）
2. 校验 layout 与本次渲染产物匹配（不允许运行时改 paths）
3. 用 prompt 内嵌的 4 个 template 写出缺失的 design.md / decisions README+TEMPLATE / specs/TEMPLATE.md
4. 在 `CLAUDE.md` 顶部插入或替换 `<!-- specguard:start --> ... <!-- specguard:end -->` 块（块内含 5 laws / ADR checklist / design-sync / 选中 layout 的 policy）
5. 写出 `.specguard/hooks.snippet.json`（不直接改 `.claude/settings.json`，由用户手动合并；详见 [ADR-0001](decisions/0001-plugin-name-command-namespace.md) 的 Consequences 段及 [v0.1.1 spec](specs/2026-04-30-v0.1.1-dogfood-fix-spec.md) §1.3）
6. 写出 `.specguard-version`（`specguard_version`、`agent`、`spec=layout_name`、`layout=layout_name`、`installed_at`）

### `/specguard:check`

13 项结构检查：design 存在、specs 下无 dated design 文件（superpowers layout 下降级为 warning）、ADR 命名 + 编号连续 + 索引 + 引用、spec 含 `## ADR 级别决策识别`、CLAUDE.md 含 specguard 标记、`.specguard/hooks.snippet.json` 存在、`.claude/settings.json` 已合并 specguard hooks（缺失为 warning）、`.specguard-version` 存在。

`semantic` 模式只生成 review package（prompt + context + findings template），不调用任何 LLM。

### `/specguard:upgrade`

读 `.specguard-version`，对比 plugin 当前 `core/version`，按 marker 区块（CLAUDE.md specguard 块 / hooks snippet / TEMPLATE.md / decisions/README 规则段）输出 diff + 用户确认后替换；marker 外内容永不动。MVP 未做端到端 dogfood（v0.2 计划）。

---

## 4. Hooks

由 [adapters/claude/plugin/hooks/settings.json.snippet.tpl](../../adapters/claude/plugin/hooks/settings.json.snippet.tpl) 渲染产生，4 个 event：

| event | 行为 |
|---|---|
| SessionStart | 注入 5 条铁律 |
| PreToolUse / Write | 拒绝 `*-design.md`（dated design）+ 校验 ADR 文件名 `NNNN-kebab-case.md` |
| Stop | `src/` 改但 design / decisions/ 未改时 systemMessage 提醒 |
| UserPromptSubmit | 用户提到"写 spec / 写 plan / 开始实施"时 additionalContext 提醒先做 ADR 判定 |

所有 hook 都用 `python3 -c` 解析 stdin JSON（不依赖 jq）；所有 `statusMessage` 以 `specguard:` 前缀，便于 idempotent merge 与 check 验证。

---

## 5. 测试矩阵

`tests/` 下：

- [test_smoke.py](../../tests/test_smoke.py) — package 可 import
- [test_manifest.py](../../tests/test_manifest.py) — LayoutManifest / AdapterManifest 解析 + 缺字段错误
- [test_render_basic.py](../../tests/test_render_basic.py) — render 产物存在 / inject 替换 / 路径替换 / version 替换 / 未知 layout 抛错
- [test_render_claude_default.py](../../tests/test_render_claude_default.py) — 5 项断言：plugin.json 无 commandNamespace、SKILL 三段注入、commands frontmatter、hooks snippet 是合法 JSON、hooks 含正确 paths
- [test_render_claude_openspec.py](../../tests/test_render_claude_openspec.py) — 2 项断言
- [test_render_claude_superpowers.py](../../tests/test_render_claude_superpowers.py) — 1 项断言
- [test_dogfood_guard_ghost.py](../../tests/test_dogfood_guard_ghost.py) — guard-ghost 路径结构匹配（guard-ghost 不在则 skip）

合计 21 测试，全绿是构建产物可发布的硬条件。

---

## 6. 不在范围（v0.2+）

- Cursor / Codex / generic adapter
- Marketplace 打包 / `claude plugin install specguard`
- `/specguard:upgrade` 端到端 dogfood
- `/specguard:check semantic` 真实 review package 验收
- skill pressure tests
- PR bot / GitHub Action / 中央 dashboard
