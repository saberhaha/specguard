# v0.4.0 Marketplace 分发 — 实施 plan

> 对应 spec: [v0-4-0-marketplace-distribution-spec.md](../specs/v0-4-0-marketplace-distribution-spec.md)
> 模式：Subagent-Driven（main 分支直接提交）

**Goal**：通过 Claude Code marketplace 提供 `/plugin install <layout>@specguard` 安装路径；保留 tarball 作为 fallback；CI 自动 render+commit+push plugins/。

**约束**：marketplace.json 用 git-subdir 指向同 repo plugins/<layout>/；plugin.json.version 由 render 时从 core/version 注入；不双写 marketplace entry version。

---

## Task 1：ADR-0008 落档

**Files**
- Create: `docs/specguard/decisions/0008-marketplace-distribution.md`
- Modify: `docs/specguard/decisions/README.md`（索引追加 0008 行）

**ADR-0008 内容要点**
- 状态：Accepted
- 日期：2026-05-01
- 相关：ADR-0003（GitHub Release tarball 分发，状态保持 Accepted，tarball 作为 fallback）；ADR-0004（hooks_merge.py runtime 模块，状态保持 Accepted）
- 决策：单 repo + git-subdir 三 layout marketplace；CI 自动 render + commit + push plugins/；plugin.json.version 由 render 注入；marketplace entry 不写 version
- 理由：marketplace 不支持 GitHub Release tarball 作为 source（核实 https://code.claude.com/docs/en/plugin-marketplaces，2026-05-01）；用户期望 `/plugin install` 安装路径
- Consequences：plugins/ 进 git tracked；release.yml 增加自动 render commit push 步骤；race 防护用 pull --rebase；GitHub Release tarball 路径保留

**Verify**：`ls docs/specguard/decisions/0008*` 存在；README 索引含 0008 行。

**Commit**：`docs(adr): add ADR-0008 marketplace distribution`

---

## Task 2：首次本地 render plugins/<layout>/

**Steps**
1. 检查 `.gitignore` 是否含 `plugins/`，若有则取消该 ignore（保留其它 ignore 不动）
2. 本地跑 3 次 render：
   ```bash
   uv run specguard-render --target claude --layout specguard-default --out plugins/specguard-default
   uv run specguard-render --target claude --layout superpowers --out plugins/superpowers
   uv run specguard-render --target claude --layout openspec-sidecar --out plugins/openspec-sidecar
   ```
3. 验证每个 plugin 目录含：`.claude-plugin/plugin.json`、`commands/init.md`、`commands/check.md`、`runtime/specguard/__init__.py`、`runtime/specguard/hooks_merge.py`、`hooks/settings.json.snippet`、`skills/design-governance/SKILL.md`
4. 验证每个 `plugin.json.version` == `0.3.0`（当前版本，下个 task 才 bump）

**Verify**：`find plugins/ -type f | wc -l` ~= 21（3 layout × 7 文件）；`jq -r .version plugins/specguard-default/.claude-plugin/plugin.json` == `0.3.0`。

**Commit**：`feat(marketplace): add rendered plugins for three layouts`（先不 push，下面还有 Task 3）

---

## Task 3：marketplace.json

**Files**
- Create: `.claude-plugin/marketplace.json`

**内容**
```json
{
  "name": "specguard",
  "owner": { "name": "saber", "email": "lixiukuan@users.noreply.github.com" },
  "description": "Project governance scaffold for AI-driven development",
  "plugins": [
    {
      "name": "specguard-default",
      "source": { "source": "git-subdir", "url": "https://github.com/saberhaha/specguard.git", "path": "plugins/specguard-default" },
      "description": "specguard with design/ADR/spec under docs/specguard/"
    },
    {
      "name": "specguard-superpowers",
      "source": { "source": "git-subdir", "url": "https://github.com/saberhaha/specguard.git", "path": "plugins/superpowers" },
      "description": "specguard with design/ADR/spec under docs/superpowers/"
    },
    {
      "name": "specguard-openspec-sidecar",
      "source": { "source": "git-subdir", "url": "https://github.com/saberhaha/specguard.git", "path": "plugins/openspec-sidecar" },
      "description": "specguard with design/ADR under docs/specguard/, specs under openspec/"
    }
  ]
}
```

**Verify**：`claude plugin validate .` 返回成功（无 error）；`jq` 能解析 JSON。

**Commit**（与 Task 2 合并提交，避免半提交状态）：`feat(marketplace): add marketplace.json + initial rendered plugins`

---

## Task 4：release.yml 自动 render+commit+push

**Files**
- Modify: `.github/workflows/release.yml`

**改动**：在 "Render and package layouts" 步骤之前插入新步骤（同一 job，串行执行）：

```yaml
      - name: Configure git user (release bot)
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
      - name: Render plugins/ for marketplace
        run: |
          for layout in specguard-default superpowers openspec-sidecar; do
            uv run specguard-render --target claude --layout "${layout}" --out "plugins/${layout}"
          done
      - name: Commit and push rendered plugins/
        run: |
          version=$(cat core/version)
          git pull --rebase origin main
          git add plugins/
          git commit -m "chore(release): render plugins for v${version}" --allow-empty
          git push origin HEAD:main
```

**Verify**：`grep -n "git push origin HEAD:main\|render plugins for v\|git-subdir" .github/workflows/release.yml`；`uv run pytest tests/test_release_workflow.py` 在新断言下应失败（待 Task 6 才补断言）。

**Commit**：`feat(release): auto-render and commit plugins/ on tag`

---

## Task 5：版本 bump v0.4.0

**Files**
- Modify: `core/version` → `0.4.0`
- Modify: `pyproject.toml.project.version` → `0.4.0`
- Modify: `uv.lock`（`uv lock` 同步）
- Modify: `tests/test_release_workflow.py`：`test_core_version_is_v0_3_0` 改名 `test_core_version_is_v0_4_0`、断言 `0.4.0`
- Re-render：跑 Task 2 的 3 个 render 命令，让 plugins/<layout>/.claude-plugin/plugin.json.version 也变成 `0.4.0`

**Verify**：`jq -r .version plugins/specguard-default/.claude-plugin/plugin.json` == `0.4.0`；`uv run pytest` 全绿。

**Commit**：`chore(release): bump to v0.4.0`

---

## Task 6：测试新增 + design.md / README / CHANGELOG 同步

**Files**
- Create: `tests/test_marketplace_schema.py`：
  - 断言 `.claude-plugin/marketplace.json` 是合法 JSON
  - `name == "specguard"`、`owner.name == "saber"`、`plugins` 长度 == 3
  - 每个 plugin source.source == "git-subdir"、含 `url` 和 `path`
  - 3 个 plugin name 与 path 对应正确
- Modify: `tests/test_release_workflow.py`：新增 `test_release_workflow_renders_and_commits_plugins`，断言 release.yml 含 `git add plugins/`、`git push origin HEAD:main`、`--allow-empty`、`uv run specguard-render`
- Modify: `docs/specguard/design.md`：
  - §2.1 Mermaid 增加 `commit plugins` → `push main` → `tag` → `build tarball` 节点
  - §3 增加 `.claude-plugin/marketplace.json` 与 `plugins/<layout>/` 描述
  - §4 数据契约 7→9 条（新增 marketplace.json schema 与 plugins/<layout>/ 结构）
  - §6 不变量 7→8 条（新增 marketplace.json plugin path 必须 git tracked）
  - §7.1 风险表新增 plugins/ 与 source 脱同步行
  - §7.3 dogfood 新增 v0.4.0 marketplace 安装条目（占位，Task 8 后回填）
  - §8.1 v0.4+ 留位移除 marketplace 项（已实现）
- Modify: `README.md`：
  - Quickstart 段先用 marketplace 安装（`claude plugin marketplace add saberhaha/specguard` + `claude plugin install specguard-default@specguard`）
  - tarball 段降级为 "Alternative: download release tarball"
  - Status 表更新到 v0.4.0
- Modify: `CHANGELOG.md`：顶部新增 `## v0.4.0 - 2026-05-01` 段，列出 marketplace 新增；标记为 minor release（非 BREAKING）

**Verify**：`uv run pytest` 全绿；`grep "claude plugin marketplace add" README.md` 有命中；`head -20 CHANGELOG.md` 含 `## v0.4.0`；`grep -c "marketplace" docs/specguard/design.md` ≥ 5。

**Commit**：`docs: sync design/README/CHANGELOG + tests for v0.4.0 marketplace`

---

## Task 7：push + tag + dogfood + 回填

**Steps**
1. `git push origin main`（推 Task 1-6 所有 commit）
2. `git tag v0.4.0 && git push origin v0.4.0`
3. 等 release.yml 完成；确认 main 上多出 `chore(release): render plugins for v0.4.0` commit、GH Release v0.4.0 含三个 tarball
4. dogfood：3 个 layout 各跑一次：
   ```bash
   mkdir -p /tmp/sg-mkt-v040/<layout> && cd /tmp/sg-mkt-v040/<layout>
   git init && git commit --allow-empty -m init
   claude plugin marketplace add saberhaha/specguard
   claude plugin install specguard-<layout>@specguard
   claude -p '/specguard:init --ai claude --spec none'
   claude -p '/specguard:check'
   ```
5. 任一失败 → 停止 + 补丁 + 重发 patch tag
6. 全通过后 `git pull origin main` 拉到 CI commit，回填 design.md §7.3 dogfood 记录 + 顶部 `Last verified against code` short hash
7. `git commit + git push origin main`

**Verify**：GH Release `v0.4.0` 含 3 tarball；`/plugin install specguard-<layout>@specguard` 三个 layout 全部成功；`/specguard:init` + `/specguard:check` 都 0 errors / 0 warnings；design.md §7.3 含 v0.4.0 marketplace 条目；顶部 hash = main HEAD。

---

## Self-review

- [x] 每个 task 都列文件 + 改动 + verify + commit message
- [x] 没有占位
- [x] Task 5 re-render 与 Task 2 初始 render 一致（都是 3 个 layout 跑同一命令）
- [x] Task 4 release.yml 改动与 spec §1.4 完全对齐（pull --rebase + push HEAD:main + --allow-empty）
- [x] Task 6 测试覆盖 marketplace schema + release workflow 新步骤
- [x] dogfood 命令可直接复制（spec §2.5 验收标准对应）
- [x] 与 spec §1 包含 11 条改动一一对应
