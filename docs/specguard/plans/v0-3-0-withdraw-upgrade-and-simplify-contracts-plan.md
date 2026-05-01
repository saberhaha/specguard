# v0.3.0 撤回 upgrade 与简化数据契约 — 实施 plan

> 对应 spec: [v0-3-0-withdraw-upgrade-and-simplify-contracts-spec.md](../specs/v0-3-0-withdraw-upgrade-and-simplify-contracts-spec.md)
> 模式：Subagent-Driven（main 分支直接提交，每 task 完成后 spec review + quality review）

**Goal**：撤回 `/specguard:upgrade`、删除四个伪契约、check 收敛 11 项、design.md 同步、release v0.3.0、dogfood 验证。

**约束**：保持 CLAUDE.md 的 `<!-- specguard:start/end -->` marker（init 幂等需要）；保留 `hooks_merge.py`（init 仍调用）。

---

## Task 1：ADR-0007 落档 + ADR-0006 superseded

**Files**
- Create: `docs/specguard/decisions/0007-withdraw-upgrade-and-simplify-contracts.md`
- Modify: `docs/specguard/decisions/0006-tighten-upgrade-interaction-and-version-handling.md`（顶部 `**状态**` 字段改为 `Superseded by ADR-0007`）
- Modify: `docs/specguard/decisions/README.md`（索引表追加 0007 行）

**ADR-0007 内容要点**
- 状态：Accepted
- 取代：ADR-0006
- 相关：ADR-0002（hooks 合并保留，check 不再验证）、ADR-0003（GitHub Release 保留，`.plugin_source` 字段废弃）、ADR-0004（`hooks_merge.py` 保留，`upgrade.py` 删除）— 这三者状态不变
- 决策：撤回 `/specguard:upgrade` + 同步删 `.specguard-version`、`.plugin_source`、`.specguard/hooks.snippet.json`、decisions/README rules marker；check 第 11/12/13 项一并删除
- 理由：v0.x 用户基数为 0，无真实跨版本痛点；同类工具（OpenSpec/Spec Kit/Superpowers）惯例无 upgrade
- Consequences：周边 ADR 字段调整（不动 Status）；未来若有真实痛点重新立 ADR

**Verify**：`ls docs/specguard/decisions/0007*` 存在；`grep "Superseded by ADR-0007" docs/specguard/decisions/0006-*.md`；README 索引含 0007 行。

**Commit**：`docs(adr): add ADR-0007 withdrawing /specguard:upgrade and simplifying contracts`

---

## Task 2：删除 upgrade 命令链

**Files**
- Delete: `core/command-prompts/upgrade.md`
- Delete: `adapters/claude/plugin/commands/upgrade.md.tpl`
- Delete: `src/specguard/upgrade.py`
- Delete: `tests/test_dogfood_upgrade.py`

**Verify**：以上 4 个 path 不存在；`grep -r "upgrade" src/specguard/` 仅剩无关命中（如 docstring 偶发提及不算）。

**Commit**：`feat!: remove /specguard:upgrade command chain`

---

## Task 3：adapter manifest + render.py 同步

**Files**
- Modify: `adapters/claude/manifest.yaml`（删除 upgrade.md.tpl 渲染条目）
- Modify: `src/specguard/render.py`（runtime 复制元组从 `("__init__.py", "hooks_merge.py", "upgrade.py")` 改为 `("__init__.py", "hooks_merge.py")`）

**Verify**：`uv run specguard-render --target claude --layout specguard-default --out /tmp/sg-t3` → `ls /tmp/sg-t3/commands/` 只有 `init.md` 和 `check.md`；`ls /tmp/sg-t3/runtime/specguard/` 只有 `__init__.py` 和 `hooks_merge.py`。

**Commit**：`feat!: drop upgrade from claude manifest and runtime bundle`

---

## Task 4：init.md prompt + decisions README 模板

**Files**
- Modify: `core/command-prompts/init.md`
  - 删除 Step 6（写 `.specguard-version`）整段
  - 删除读 `.plugin_source` marker 段
  - Step 5：把"实际写 `.specguard/hooks.snippet.json` 再合并"改为"用 tempfile 持有 snippet 内容，调 `hooks_merge.merge_hooks_file(settings_path, tempfile_path, dry_run=...)`"，dry-run / 实际跑共用 tempfile 路径；不再向项目写 `.specguard/hooks.snippet.json`
- Modify: `core/templates/decisions/README.md.tpl`
  - 删除 `<!-- specguard:rules:start -->` 与 `<!-- specguard:rules:end -->` 两行 marker（包裹的内容保留）

**Verify**：`uv run specguard-render ...`，rendered `commands/init.md` 不含 `.specguard-version`、`.plugin_source`、`hooks.snippet.json` 字串；rendered `decisions/README.md` 不含 `specguard:rules` 字串。

**Commit**：`feat!: drop .specguard-version, .plugin_source, hooks.snippet.json, rules markers`

---

## Task 5：check.md 收敛 + 测试修订

**Files**
- Modify: `core/command-prompts/check.md`
  - 删除第 11 项（hooks.snippet.json 存在）
  - 删除第 12 项（settings.json 含 specguard hooks 错误）
  - 删除第 13 项（`.specguard-version` 存在）
  - 第 9 项移除依赖 `.specguard-version installed_at` 的豁免逻辑
  - 顶部"共 13 项"改为"共 11 项"
- Modify: `tests/test_render_basic.py`
  - 删除 upgrade.md 存在断言
  - `test_render_includes_runtime_modules`：仅断言 `__init__.py` 与 `hooks_merge.py`，加断言 `upgrade.py` 不存在
- Modify: `tests/test_render_claude_default.py`
  - 删除 `test_upgrade_command_*` 全部
  - 删除 `test_init_command_uses_marker_for_plugin_source`
  - 删除 `test_check_command_treats_missing_hooks_as_error`
  - init 测试中 `tempfile` / `plugin_source` / `hooks.snippet.json` 路径相关断言改为"init 直接调用 hooks_merge"语义断言
- Modify: `tests/test_release_workflow.py`
  - 删除 `test_release_workflow_writes_plugin_source_marker`

**Verify**：`uv run pytest -x` 全绿（版本相关 test 还会失败，留给 Task 6 修）。

**Commit**：`feat!: collapse /specguard:check from 13 to 11 items`

---

## Task 6：release workflow + 版本 bump

**Files**
- Modify: `.github/workflows/release.yml`（删除 `echo "github-release-v${version}" > "${out}/.plugin_source"` 步骤）
- Modify: `core/version` → `0.3.0`
- Modify: `pyproject.toml` `version` → `0.3.0`
- Modify: `uv.lock`（`uv lock` 同步）
- Modify: `tests/test_release_workflow.py`：`test_core_version_is_v0_2_1` 改名 `test_core_version_is_v0_3_0`、断言 `0.3.0`

**Verify**：`grep -n plugin_source .github/workflows/release.yml` 无命中；`uv run pytest` 全绿。

**Commit**：`chore(release)!: drop .plugin_source step and bump to 0.3.0`

---

## Task 7：design.md / README / CHANGELOG 同步

**Files**
- Modify: `docs/specguard/design.md`（按 spec §"对 design.md 的影响"重写）
  - §2 Mermaid 4→3（删 Upgrade flow）
  - §2.1 删 `.plugin_source stamped` 节点
  - §2.2 删 `write .specguard-version` 节点
  - §3.4 删 upgrade.py 段；render.py 描述改为只复制 2 个 runtime 模块
  - §4 数据契约 11→7（删 `.specguard-version`、`.plugin_source`、decisions/README rules marker、`.specguard/hooks.snippet.json`）
  - §5.2 init 删写 `.specguard-version` 段
  - §5.3 check 13→11
  - §5.4 upgrade 整段删
  - §5.5 删 upgrade prompt↔runtime API
  - §6 不变量 8→7（删 upgrade 两阶段；release/runtime 边界改"必须携带 runtime/specguard/"）
  - §7.1 风险表删 upgrade conflict；改 release 风险文案
  - §7.2 删 upgrade runtime 行
  - §7.3 删 upgrade dogfood 行；新增 v0.3.0 dogfood 记录条目（Task 8 完成后回填）
  - §8.1 新增"upgrade 命令（如未来出现真实跨版本升级痛点重新立 ADR）"
  - §8.2 已删除清单扩充列出 ADR-0007 撤回项
  - 顶部 `Last verified against code` → 本切片最终 commit short hash（Task 8 之后回填）
- Modify: `README.md`
  - 删除 `/specguard:upgrade` quickstart 段（第 37-42 行）
  - Status 表删 upgrade 相关行（"Auto hook merge + Release tarball" 行的 upgrade 措辞调整或保留 release-only）
  - quickstart tarball URL `v0.2.1` → `v0.3.0`
  - init 文案"writes `.specguard/hooks.snippet.json`"删除
- Modify: `CHANGELOG.md`
  - 顶部新增 `## v0.3.0 - 2026-05-01` 段
  - 段开头 `### BREAKING`
  - 列出全部移除项：`/specguard:upgrade` 命令、`.specguard-version`、`.plugin_source`、`.specguard/hooks.snippet.json`、decisions/README rules marker、check 第 11/12/13 项
  - 迁移指引：用户从 v0.2.x 升级 → 删除上述 marker 内容；其余文件 init 重跑即可
  - v0.2.1 / v0.2.0 / v0.1.0 历史段保留不变

**Verify**：`grep -c "upgrade" docs/specguard/design.md` 仅剩 §8.1 留位与 §8.2 已删除清单两类合理命中；`grep upgrade README.md` 无 `/specguard:upgrade` 命中；`head -30 CHANGELOG.md` 含 `## v0.3.0` 与 `### BREAKING`。

**Commit**：`docs!: sync design.md/README/CHANGELOG for v0.3.0 BREAKING release`

---

## Task 8：push + tag + dogfood + 回填

**Steps**
1. `git push origin main`
2. `git tag v0.3.0 && git push origin v0.3.0`
3. 等 GitHub Release workflow 完成；确认三个 layout tarball 存在
4. dogfood：在 `/tmp` 下三个临时 git repo（每 layout 一个）跑：
   ```bash
   mkdir -p /tmp/sg-dog-<layout> && cd /tmp/sg-dog-<layout>
   git init && git commit --allow-empty -m init
   curl -L https://github.com/saberhaha/specguard/releases/download/v0.3.0/specguard-claude-<layout>-v0.3.0.tar.gz | tar -xz -C ./plugin
   claude --plugin-dir ./plugin -p '/specguard:init --ai claude --spec none'
   claude --plugin-dir ./plugin -p '/specguard:check'
   ```
5. 任一失败 → 停止 + 补丁 + 重发 patch tag
6. 全通过后回填 `docs/specguard/design.md` §7.3 dogfood 记录 + 顶部 `Last verified against code` short hash
7. `git commit -m "docs: record v0.3.0 dogfood results" && git push`

**Verify**：GH Release `v0.3.0` 含三 tarball；三 layout dogfood 全通；design.md §7.3 含 v0.3.0 条目；顶部 hash 与最新 main HEAD 一致。

---

## Self-review（写完上面后自查）

- [ ] 每个 task 都列出具体文件 + 改动 + verify + commit message
- [ ] 没有 "TBD" / "适当处理" / "类似 Task X" 之类占位
- [ ] Task 5 的测试函数名和 Task 4 的 init 改动方向一致（hooks 走 tempfile）
- [ ] Task 8 的 dogfood 命令可直接复制执行
- [ ] 与 spec §"包含" 12 条改动点一一对应（#1-12 全覆盖）
