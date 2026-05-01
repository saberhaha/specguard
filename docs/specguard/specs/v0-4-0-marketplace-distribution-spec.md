# v0-4-0-marketplace-distribution 设计

**日期**：2026-05-01
**适用范围**：v0.4.0：通过 Claude Code marketplace 提供安装分发路径，保留 GitHub Release tarball 作为 fallback。新增 `.claude-plugin/marketplace.json`、`plugins/<layout>/` 三个 git tracked 渲染产物、release workflow 自动 render+commit。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 新增 `.claude-plugin/marketplace.json`，列出 3 个 layout 插件，source 用 `git-subdir` 指向同 repo `plugins/<layout>/`。
2. 新增 git tracked 目录 `plugins/specguard-default/`、`plugins/superpowers/`、`plugins/openspec-sidecar/`，由 CI 在每次 release 时自动 render + commit + push（先于 tag）。
3. 修改 `.github/workflows/release.yml`：tag push 后先在 main 上 `uv run specguard-render` 三个 layout 输出到 `plugins/<layout>/`，`git add plugins/ && git commit && git push`，再继续 build tarball + GH release（tarball 保留作为 fallback）。
4. README 新增 marketplace 安装段，作为推荐路径；tarball 路径保留为 fallback。
5. design.md §2.1 Build/Release flow Mermaid 增加 marketplace push 节点；§4 数据契约新增 `marketplace.json`、`plugins/<layout>/` 两条；§7.3 增加 v0.4.0 dogfood 记录条目；§8.2 已删除清单不变。
6. 新增测试：`test_marketplace_schema.py` 断言 marketplace.json 含 3 个 layout、source 类型为 `git-subdir`、path 与版本字段；扩展 `test_release_workflow.py` 断言 release.yml 含 render+commit+push 步骤。
7. bump `core/version`、`pyproject.toml`、`uv.lock`、`tests/test_release_workflow.py::test_core_version_is_v0_3_0` → `0.4.0`。
8. 推送 main、打 `v0.4.0` tag、release 后从 marketplace 安装三个 layout 验证 `/specguard:init` + `/specguard:check` 跑通；结果写入 design §7.3。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 marketplace.json | ✓ | ✓ | - | - | - |
| #2 plugins/<layout>/ git tracked | - | ✓ | - | - | - |
| #3 release.yml 自动 render+commit | ✓ | - | ✓ | - | - |
| #4 README marketplace quickstart | - | - | - | - | - |
| #5 design.md 同步 | - | - | - | - | - |
| #6 测试新增 | - | - | - | - | - |
| #7 版本 bump 0.4.0 | - | - | - | - | - |
| #8 release + dogfood | - | - | - | - | - |

### 候选 ADR（请用户拍板）

- **ADR-0008：通过 Claude Code marketplace 分发 specguard 插件**

  覆盖改动 #1-#3。命中接口语义 + 数据格式 + 跨模块依赖。

  关键陈述：
  - 用户安装入口：`/plugin marketplace add saberhaha/specguard` → `/plugin install specguard-default@specguard`，由 Claude Code 内置 plugin 缓存机制管理生命周期，省去用户手动 `--plugin-dir`。
  - Marketplace 不支持 GitHub Release tarball 作为 source（核实：https://code.claude.com/docs/en/plugin-marketplaces，2026-05-01）；只能从 git tracked 内容拉，故 plugins/<layout>/ 必须进 git。
  - source 选 `git-subdir`：单 repo 三个 layout，sparse clone 子目录最经济；ref 用 `v0.X.Y` tag 实现版本绑定。
  - 版本解析：`plugin.json.version` 由 render 时从 `core/version` 注入；marketplace entry 不单独写 `version`（官方文档警告双写冲突）。
  - GitHub Release tarball 路径不删除，作为离线/受限网络 fallback。
  - CI 在 release 中自动 render + commit + push plugins/，再打 tag；保证 marketplace 拉到的 plugin 与 source 强一致，避免人工忘 render 导致 marketplace 用户拿到旧版本。

  **相关**：
  - ADR-0003（GitHub Release tarball 分发）— 状态保持 Accepted；tarball 路径保留为 fallback；marketplace 成为推荐路径。
  - ADR-0004（hooks_merge.py runtime 模块）— 状态保持 Accepted；marketplace 安装的 plugin 仍含 runtime/specguard/，init prompt 仍通过 `CLAUDE_PLUGIN_ROOT` 调用 hooks_merge。

### 不需要 ADR

- #4–#8：README / design / 测试 / 版本 / dogfood 同步执行 ADR-0008 已确定的方向，不引入新决策。

## 对 design.md 的影响（必填）

- §1 不动。
- §2.1 Build/Release flow Mermaid：在现有 `render plugins` → `build tarballs` 链路上新增 `commit plugins/<layout>` → `push main` → `tag v0.X.Y` 节点；marketplace.json 作为新增静态资源，与 tarball 并列。
- §2.2 / §2.3 不动。
- §3 目录结构：新增 `.claude-plugin/marketplace.json`、`plugins/<layout>/`（标注由 CI 渲染，prohibit 人工修改）。
- §4 数据契约表从 7 条扩展到 9 条：新增
  1. `.claude-plugin/marketplace.json`：必填字段 name=`specguard`、owner、3 个 plugin 条目（git-subdir source）；
  2. `plugins/<layout>/`：CI render 产物，git tracked；目录结构与 release tarball 解包后一致。
- §5 不动（init / check 行为无变化）。
- §6 不变量保持 7 条；新增不变量"marketplace.json 列出的 3 个 plugin path 必须存在 git tracked 目录"作为第 8 条。
- §7.1 风险：新增"plugins/ 与 source 脱同步导致 marketplace 用户拿旧版本" — 缓解：CI 在 release 中强制 render+commit+push，禁止只打 tag。
- §7.2 改动类型表：新增"marketplace.json schema 变更触发 plugin install 失败"行。
- §7.3 dogfood：新增 v0.4.0 marketplace 安装路径记录条目（`/plugin marketplace add` + `/plugin install` 三个 layout 各跑一次 init+check）。
- §7.4 不动。
- §8.1 v0.4+ 留位：从"Marketplace 安装"项移除（已实现）；保留 Cursor adapter / skill pressure tests。
- §8.2 已删除清单不动。
- 顶部 `Last verified against code` 同步到本切片最终 HEAD short hash。

## 1. 切片范围

**包含**

1. 新建 ADR-0008（覆盖 marketplace.json + plugins/<layout> + release.yml render+commit）；`decisions/README.md` 索引追加 0008 行；ADR-0003/0004 状态字段不变，仅在 ADR-0008 相关段落说明。
2. 新建 `.claude-plugin/marketplace.json`：
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
3. 取消 `.gitignore` 对 `plugins/` 的 ignore（如果存在）；首次本地手动 `uv run specguard-render --target claude --layout <X> --out plugins/<X>` 渲染三个 layout 到 `plugins/<layout>/` 并 git add + commit + push main（在打 v0.4.0 tag 之前）；之后 release 由 CI 接手。
4. 修改 `.github/workflows/release.yml`：在现有"Render and package layouts"步骤之前新增（同一个 job 内串行执行）：
   - 配置 git user：`git config user.name 'github-actions[bot]'`、`git config user.email '41898282+github-actions[bot]@users.noreply.github.com'`
   - 重新 render 三个 layout 到 `plugins/<layout>/`（覆盖现有 plugins/ 目录）
   - `git pull --rebase origin main`（防止 race）
   - `git add plugins/ && git commit -m "chore(release): render plugins for v${version}" --allow-empty`
   - `git push origin HEAD:main`
   - 然后才执行打 tarball 步骤
   - 关键：tag 必须先在 push commit 之后才用于 build tarball；CI 在收到 tag push 后先 push commit 到 main 再 build tarball；用 `pull --rebase` 防 race。
5. 修改 `README.md`：
   - Quickstart 段先用 marketplace 安装：
     ```bash
     claude plugin marketplace add saberhaha/specguard
     claude plugin install specguard-default@specguard
     ```
   - tarball 段保留为 "Alternative: download release tarball"。
   - quickstart 不再需要 `--plugin-dir`、不再需要 `CLAUDE_PLUGIN_ROOT` 手动设置（marketplace 安装时自动暴露）。
6. 修改 `CHANGELOG.md`：新增 v0.4.0 段，列出 marketplace.json + plugins/ tracked + CI 自动 render+commit；标记为 minor release（非 BREAKING）。
7. 重写 `docs/specguard/design.md` 见上节"对 design.md 的影响"。
8. 新增 `tests/test_marketplace_schema.py`：
   - 断言 `.claude-plugin/marketplace.json` 解析为合法 JSON
   - 断言 `name == "specguard"`、含 `owner.name` 与 `plugins` 数组长度 == 3
   - 断言 3 个 plugin name 为 specguard-default / specguard-superpowers / specguard-openspec-sidecar
   - 断言每个 source.source == "git-subdir"、含 `url` 与 `path` 字段
9. 扩展 `tests/test_release_workflow.py`：
   - 新增 `test_release_workflow_renders_and_commits_plugins`：断言 release.yml 含 `git add plugins/` 与 `git push origin main` 与 `--allow-empty` 步骤
10. bump 版本：`core/version` → `0.4.0`；`pyproject.toml.project.version` → `0.4.0`；`uv.lock` 同步；`tests/test_release_workflow.py::test_core_version_is_v0_3_0` 改名 `test_core_version_is_v0_4_0` 并断言 `0.4.0`。
11. 推送 main、打 `v0.4.0` tag、CI 完成后从 marketplace 安装三个 layout 验证 `/specguard:init` + `/specguard:check` 跑通；结果写入 design §7.3。

**不包含**

- 删除 GitHub Release tarball：保留作为 fallback；离线 / 自建 GitHub Enterprise 用户仍可用。
- 删除 `--plugin-dir` 支持：与 marketplace 互不冲突，开发期 dogfood 仍用 `--plugin-dir dist/claude/<layout>`。
- 上架 Anthropic 官方 marketplace：超出范围；用户需自行 `/plugin marketplace add saberhaha/specguard`。
- Cursor adapter / Codex adapter（v0.5+）。
- skill pressure tests（v0.5+）。
- 引入 plugin 依赖关系（plugin-dependencies）：当前 3 个 layout 互不依赖。

## 2. 验收标准

1. **ADR-0008 已落档**：`docs/specguard/decisions/0008-marketplace-distribution.md` 存在；`decisions/README.md` 索引含 0008 行；ADR-0003/0004 状态字段不变。

2. **marketplace.json + plugins/ git tracked**：`.claude-plugin/marketplace.json` 存在，`claude plugin validate .` 返回成功；`plugins/specguard-default/`、`plugins/superpowers/`、`plugins/openspec-sidecar/` 都是 git tracked 目录，每个都含 `.claude-plugin/plugin.json`、`commands/init.md`、`commands/check.md`、`runtime/specguard/__init__.py`、`runtime/specguard/hooks_merge.py`、`hooks/settings.json.snippet`。

3. **release workflow 自动 render+commit**：`.github/workflows/release.yml` 含 `uv run specguard-render` 渲染到 `plugins/<layout>/` 步骤、`git add plugins/`、`git commit --allow-empty`、`git push origin main` 步骤，且这些步骤在 build tarball 之前；`uv run pytest` 全绿。

4. **README + CHANGELOG + design.md 同步**：`README.md` Quickstart 段含 `claude plugin marketplace add saberhaha/specguard` 与 `claude plugin install specguard-default@specguard`；tarball 段保留为 "Alternative"；CHANGELOG 顶部含 `## v0.4.0` 段，列出 marketplace 新增；design.md §4 数据契约扩展为 9 条、§2.1 Mermaid 含 commit+push 节点、§7.3 含 v0.4.0 dogfood 条目；顶部 `Last verified against code` 为本切片最终 commit short hash。

5. **v0.4.0 已发布并 marketplace dogfood 通过**：`core/version` = `0.4.0`；`pyproject.toml.version` = `0.4.0`；`uv.lock` 同步；`tests/test_release_workflow.py` 期望值 = `0.4.0`；`v0.4.0` tag 已推送；CI 完成后 main 上含一次 chore(release) commit；从 marketplace 安装 specguard-default / specguard-superpowers / specguard-openspec-sidecar 三个 plugin，分别在临时 git repo 跑 `/specguard:init --ai claude --spec none` 与 `/specguard:check`，结果 0 errors / 0 warnings；dogfood 命令日志摘要写入 design §7.3。

## 3. 留给后续切片的事

- 上架 Anthropic 官方 marketplace。
- Cursor / Codex / generic adapter。
- skill pressure tests。
- PR bot / GitHub Action 治理报告。
- 中央 dashboard。
