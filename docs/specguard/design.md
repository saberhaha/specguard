# specguard 设计（Living Document）

**Last verified against code**: 2026-05-01 @ commit `3a04488`
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
dist/<target>/<layout>/  (可发布的 plugin 包；v0.2 起由 GitHub Actions 打包为 release tarball，见 ADR-0003)
```

### core/

agent-neutral + layout-neutral 治理资产，路径全部使用 `{{ paths.* }}` 变量：

- [core/version](../../core/version) — 当前 specguard 版本（`0.2.0`）
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
5. `plugin/commands/upgrade.md.tpl` → `commands/upgrade.md`，注入 prompt + 5 laws / ADR checklist / design-sync + 4 个 template（`raw`）+ hooks snippet；upgrade prompt 由这些 embedded sections 构造 `upgrade_project()` 的 replacements（见 [ADR-0004](decisions/0004-python-modules-for-runtime-algorithms.md)）
6. `plugin/hooks/settings.json.snippet.tpl` → `hooks/settings.json.snippet`

**关键决定**：plugin name = `specguard`，**没有** `commandNamespace` 字段，因此 Claude Code 的 slash 命令固定为 `/specguard:init`、`/specguard:check`、`/specguard:upgrade`（见 [ADR-0001](decisions/0001-plugin-name-command-namespace.md)）。

### src/specguard/

- [manifest.py](../../src/specguard/manifest.py) — `LayoutManifest.load()` / `AdapterManifest.load()`，解析 + 校验 yaml manifest，缺字段抛 `ManifestError`
- [render.py](../../src/specguard/render.py) — `render(repo_root, target, layout, out_dir)` 把 core + layout + adapter 渲染到 `dist/<target>/<layout>/`：
  1. 加载 layout / adapter manifest
  2. 给 Jinja2 注册 `regex_escape`（双反斜杠化以适配 JSON 字面量）和 `relative_to_design`（路径相对 design dir）filter
  3. 上下文 = `{paths, specguard_version, layout_name}`
  4. 按 manifest `renders` 列表逐文件处理：先把 inject 文件文本替换 marker（标 `raw: true` 的注入会被 `{% raw %}{% endraw %}` 包住，避免 Jinja 求值），再替换 layout-specific policy marker，最后整体过 Jinja 渲染
  5. 把 `src/specguard/{__init__,hooks_merge,upgrade}.py` 复制到 `<out_dir>/runtime/specguard/`，供 `/specguard:init` 与 `/specguard:upgrade` 在用户项目里通过 `CLAUDE_PLUGIN_ROOT/runtime` 导入（见 [ADR-0004](decisions/0004-python-modules-for-runtime-algorithms.md)）
  - 所有文本 IO 使用显式 `encoding="utf-8"`
- [hooks_merge.py](../../src/specguard/hooks_merge.py) — `.claude/settings.json` 与 `.specguard/hooks.snippet.json` 的解析、合并、幂等替换、dry-run diff 文本生成；由 `/specguard:init` prompt 调用（见 [ADR-0004](decisions/0004-python-modules-for-runtime-algorithms.md)）
- [upgrade.py](../../src/specguard/upgrade.py) — 5 个 marker 区域（CLAUDE.md / settings.json hooks / specs TEMPLATE / decisions TEMPLATE / decisions README 规则段）的检测、diff、替换、conflict 识别、`.specguard-version` legacy 补写；由 `/specguard:upgrade` prompt 调用（见 [ADR-0004](decisions/0004-python-modules-for-runtime-algorithms.md)）
- console script `specguard-render` = `specguard.render:main`，stdlib `argparse`

---

## 3. `/specguard:*` 命令运行时行为

### `/specguard:init`

1. 解析 `--ai` `--spec`（auto 时探测 `.claude/`、`docs/superpowers/`、`openspec/`）
2. 校验 layout 与本次渲染产物匹配（不允许运行时改 paths）
3. 用 prompt 内嵌的 4 个 template 写出缺失的 design.md / decisions README+TEMPLATE / specs/TEMPLATE.md
4. 在 `CLAUDE.md` 顶部插入或替换 `<!-- specguard:start --> ... <!-- specguard:end -->` 块（块内含 5 laws / ADR checklist / design-sync / 选中 layout 的 policy）
5. 写出 `.specguard/hooks.snippet.json`，并按 `statusMessage` 前缀 `specguard:` 自动幂等合并到 `.claude/settings.json`；支持 `--dry-run` 仅打印 diff 不落盘（见 [ADR-0002](decisions/0002-init-auto-merge-hooks.md)，推翻 [ADR-0001](decisions/0001-plugin-name-command-namespace.md) Consequences 中"不自动改 settings.json"约束）
6. 写出 `.specguard-version`（`specguard_version`、`agent`、`spec=layout_name`、`layout=layout_name`、`installed_at`、`plugin_source` ∈ {`github-release-vX.Y.Z`, `local-dist`}）；`plugin_source` 通过 plugin root 下的 `.plugin_source` marker 识别 release tarball，缺失时 fallback 到 `local-dist`（见 [ADR-0003](decisions/0003-distribution-via-github-release.md)）

### `/specguard:check`

13 项结构检查：design 存在、specs 下无 `*-design.md`（superpowers layout 下对老 `*-design.md` 文件降级为 warning，新文件仍要求 `*-spec.md`）、`decisions/README.md` 存在、ADR 文件名匹配 `^[0-9]{4}-[a-z0-9-]+\.md$`、ADR 编号连续、ADR 在索引中、design 引用的 ADR 存在、`Superseded by` 目标存在、spec 含 `## ADR 级别决策识别`（superpowers layout 下 `*-design.md` 例外）、CLAUDE.md 含 specguard 标记、`.specguard/hooks.snippet.json` 存在、`.claude/settings.json` 已合并 specguard hooks（缺失为 error，见 [ADR-0002](decisions/0002-init-auto-merge-hooks.md)）、`.specguard-version` 存在。

`semantic` 模式只生成 review package（prompt + context + findings template），不调用任何 LLM。

### `/specguard:upgrade`

读 `.specguard-version`，对比 plugin 当前 `core/version`，按 5 个 marker 区块输出 diff + 用户确认后替换；marker 外内容永不动：
1. CLAUDE.md `<!-- specguard:start -->` ↔ `<!-- specguard:end -->` 块
2. `.claude/settings.json` 中 `statusMessage` 前缀为 `specguard:` 的 hook 条目
3. `{{ paths.specs_dir }}/TEMPLATE.md`
4. `{{ paths.decisions_dir }}/TEMPLATE.md`
5. `{{ paths.decisions_dir }}/README.md` 规则段

对 v0.1.x（`.specguard-version` 缺 `plugin_source`）的项目按 legacy local install 处理，升级后补写 `plugin_source = "local-dist"`（见 [ADR-0003](decisions/0003-distribution-via-github-release.md)）。v0.1.x 的 `decisions/README.md` 不含 `<!-- specguard:rules:start -->` / `<!-- specguard:rules:end -->` marker；升级时会触发 `UpgradeConflict.manual_patch`，由用户显式复制 patch 后重试。

---

## 4. Hooks

由 [adapters/claude/plugin/hooks/settings.json.snippet.tpl](../../adapters/claude/plugin/hooks/settings.json.snippet.tpl) 渲染产生，4 个 event：

| event | 行为 |
|---|---|
| SessionStart | 注入 5 条铁律 |
| PreToolUse / Write | 拒绝 `*-design.md`（dated design）+ 校验 ADR 文件名 `NNNN-kebab-case.md` |
| Stop | `src/` 改但 design / decisions/ 未改时 systemMessage 提醒 |
| UserPromptSubmit | 用户提到"写 spec / 写 plan / 开始实施"时 additionalContext 提醒先做 ADR 判定 |

所有 hook 都用 `python3 -c` 解析 stdin JSON（不依赖 jq）；所有 `statusMessage` 以 `specguard:` 前缀，便于 idempotent merge 与 check 验证。`/specguard:init` 自动按该前缀把 specguard 条目幂等合并到 `.claude/settings.json`；非 specguard 条目原样保留（见 [ADR-0002](decisions/0002-init-auto-merge-hooks.md)）。

---

## 5. 测试矩阵

`tests/` 下：

- [test_smoke.py](../../tests/test_smoke.py) — package 可 import
- [test_manifest.py](../../tests/test_manifest.py) — LayoutManifest / AdapterManifest 解析 + 缺字段错误
- [test_render_basic.py](../../tests/test_render_basic.py) — render 产物存在 / inject 替换 / 路径替换 / version 替换 / 未知 layout 抛错 / runtime 模块复制到 dist
- [test_render_claude_default.py](../../tests/test_render_claude_default.py) — 9 项断言：plugin.json 无 commandNamespace、SKILL 三段注入、commands frontmatter、hooks snippet 是合法 JSON、hooks 含正确 paths、init 含 `--dry-run` + `specguard.hooks_merge` + `CLAUDE_PLUGIN_ROOT` + tempfile + `.plugin_source` marker 读取、check 把缺失 hooks 当 error、upgrade 含 `specguard.upgrade` + `replacements = {` + `manual_patch`、upgrade command 嵌入 CLAUDE block / decisions README rules marker / hooks snippet 且无 `<!-- inject:` 残留
- [test_render_claude_openspec.py](../../tests/test_render_claude_openspec.py) — 2 项断言
- [test_render_claude_superpowers.py](../../tests/test_render_claude_superpowers.py) — 1 项断言
- [test_dogfood_guard_ghost.py](../../tests/test_dogfood_guard_ghost.py) — guard-ghost 路径结构匹配（guard-ghost 不在则 skip）
- [test_init_merge_hooks.py](../../tests/test_init_merge_hooks.py) — hooks 合并算法 / 幂等 / dry-run / 非法 JSON 不覆盖 / 保留非 specguard 条目
- [test_dogfood_upgrade.py](../../tests/test_dogfood_upgrade.py) — 5 marker upgrade / marker 缺失或文件缺失 conflict 不写 / no-op 时 `changed=False` 且不改 mtime / `.specguard-version` legacy 补 `plugin_source` / `UpgradeConflict.manual_patch` 含路径 + marker + 新内容
- [test_release_workflow.py](../../tests/test_release_workflow.py) — `.github/workflows/release.yml` 监听 `v*` tag、覆盖 3 个 layout、写 `.plugin_source = github-release-v${version}`、tag 与 `core/version` 校验、`tar -czf`、`softprops/action-gh-release`、`contents: write` 权限、`uv sync --frozen`、`core/version` 等于 `0.2.0`

合计 42 测试，全绿是构建产物可发布的硬条件。

---

## 6. 不在范围（v0.3+）

- Cursor / Codex / generic adapter
- Marketplace 打包 / `claude plugin install specguard`
- `/specguard:check semantic` 真实 review package 验收
- skill pressure tests
- PR bot / GitHub Action / 中央 dashboard
