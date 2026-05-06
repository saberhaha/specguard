# v0.6.0 撤回 marketplace + 新增 install.sh — 实施 plan

> 对应 spec: [v0-6-0-withdraw-marketplace-and-add-install-script-spec.md](../specs/v0-6-0-withdraw-marketplace-and-add-install-script-spec.md)
> 模式：直接在 main 分支提交

**Goal**：删除 marketplace 分发全套（marketplace.json / plugins/ / render+commit release 步骤），新增 install.sh，还原 release.yml 为纯 tarball 模式，bump v0.6.0。

---

## Task 1：ADR-0011 落档

**Files**
- Create: `docs/specguard/decisions/0011-withdraw-marketplace-and-add-install-script.md`
- Modify: `docs/specguard/decisions/0008-marketplace-distribution.md`（顶部 `**状态**` 改为 `Superseded by ADR-0011`）
- Modify: `docs/specguard/decisions/README.md`（索引追加 0011 行；0008 状态同步）

**ADR-0011 要点**
- 状态：Accepted；取代：ADR-0008
- 理由：Claude Code v2.1.123 marketplace 路径不暴露 `CLAUDE_PLUGIN_ROOT`，hooks 无法自动合并；维护 plugins/ git-tracked 产物每次 release 多一个自动 commit + ENOTEMPTY race；核心功能缺失，维护成本真实，收益为零。
- 决策：删除 marketplace 分发全套；新增 install.sh 作为 tarball 的薄封装；GitHub Release tarball 保留（ADR-0003 不变）。
- 未来留位：若 Claude Code 修复 CLAUDE_PLUGIN_ROOT 暴露，重新评估 marketplace（新立 ADR）。

**Verify**：`ls docs/specguard/decisions/0011*` 存在；ADR-0008 顶部含 `Superseded by ADR-0011`；README 含 0011 行。

**Commit**：`docs(adr): add ADR-0011 withdraw marketplace distribution`

---

## Task 2：删除 marketplace 文件

**Files**
- `git rm -r .claude-plugin/ plugins/`（22 文件）
- Delete: `tests/test_marketplace_schema.py`

**Verify**：`git ls-files | grep -E "^\.claude-plugin/|^plugins/"` 无命中；`ls tests/test_marketplace_schema.py` 报错。

**Commit**：`feat!: delete marketplace.json, plugins/, and marketplace tests`

---

## Task 3：还原 release.yml

**Files**
- Modify: `.github/workflows/release.yml`

**改动**：
- `actions/checkout@v4` 删除 `with: ref: main / fetch-depth: 0 / token:` 三行，恢复默认 checkout（tag 指向的 commit）
- 删除"Configure git user (release bot)"步骤（整段）
- 删除"Render plugins/ for marketplace"步骤（整段）
- 删除"Commit and push rendered plugins/"步骤（整段）
- 步骤名"Render and package tarballs"改回"Render and package layouts"

目标：release.yml 结构与 v0.3.0 一致（checkout → uv sync → verify tag → pytest → render dist/ → build tarball → upload）。

**Verify**：`grep -E "git push|git add plugins|ref: main|render plugins" .github/workflows/release.yml` 无命中；`uv run pytest` 全绿。

**Commit**：`feat!: restore release.yml to tarball-only mode`

---

## Task 4：新增 install.sh + 测试版本断言更新

**Files**
- Create: `install.sh`（项目根，内容见 spec §1.2，chmod +x）
- Modify: `tests/test_release_workflow.py`：删除 `test_release_workflow_renders_and_commits_plugins`；`test_core_version_is_v0_5_0` 改名 `test_core_version_is_v0_6_0`、断言 `0.6.0`

**install.sh 内容**：
```sh
#!/usr/bin/env sh
set -e
LAYOUT="${1:-specguard-default}"
VERSION=$(curl -s https://api.github.com/repos/saberhaha/specguard/releases/latest \
  | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
DEST="$HOME/.local/share/specguard/plugins/${LAYOUT}"
mkdir -p "$DEST"
curl -L "https://github.com/saberhaha/specguard/releases/latest/download/specguard-claude-${LAYOUT}-v${VERSION}.tar.gz" \
  | tar -xz -C "$DEST"
echo ""
echo "specguard ${LAYOUT} v${VERSION} installed to ${DEST}"
echo ""
echo "Run init in your project (a git repo):"
echo "  claude --plugin-dir ${DEST} -p '/specguard:init --ai claude --spec none'"
echo ""
echo "Run governance check anytime:"
echo "  claude --plugin-dir ${DEST} -p '/specguard:check'"
```

**Verify**：`sh -n install.sh` 无语法错误；`uv run pytest` 全绿（版本断言改完后）。

**Commit**：`feat: add install.sh + bump version test to 0.6.0`

---

## Task 5：bump 版本 0.6.0

**Files**
- `core/version` → `0.6.0`
- `pyproject.toml` version → `0.6.0`
- `uv lock`
- `tests/test_release_workflow.py`：`test_core_version_is_v0_5_0` → `test_core_version_is_v0_6_0`，断言 `0.6.0`

**Verify**：`cat core/version` = `0.6.0`；`uv run pytest` 全绿。

**Commit**：`chore(release): bump to v0.6.0`

---

## Task 6：design.md + README + CHANGELOG 同步

**Files**
- Modify: `docs/specguard/design.md`
  - §2.1 Mermaid：删 PD/PR/PC/PP 四节点（plugins/ render+commit+push 链路），还原 v0.3.0 形态
  - §3.5 marketplace 与 plugins/：整段删除（§3 节编号不变，原 §3.5 就是最后一节）
  - §4 数据契约：删第 8 条（marketplace.json）和第 9 条（plugins/<layout>/），9 条 → 7 条
  - §6 不变量：删第 8 条（marketplace plugin path 完整性），9 条 → 8 条
  - §7.1 风险表：删 `plugins/ 与 src/ 脱同步` 行
  - §7.2 改动类型表：删 `marketplace.json schema 修改` 行
  - 顶部 `Last verified against code`：占位，Task 7 回填
- Modify: `README.md`：快速开始改为 install.sh 用法（`curl | sh` 一行 + 本地跑两行）
- Modify: `CHANGELOG.md`：顶部新增 `## v0.6.0` 段，含 `### BREAKING`、改动列表、迁移说明（用户只需重新运行 install.sh，无需改项目文件）

**Verify**：`grep -E "marketplace|plugins/" docs/specguard/design.md` 无命中（除 ADR-0011 引用）；`grep "install.sh" README.md` 有命中；`head -10 CHANGELOG.md` 含 `## v0.6.0`。

**Commit**：`docs!: sync design.md/README/CHANGELOG for v0.6.0`

---

## Task 7：push + tag + 验证 + 回填

**Steps**
1. `git push origin main`
2. `git tag v0.6.0 && git push origin v0.6.0`
3. 等 release.yml 完成；确认 main **不再** 多出 chore(release) commit（CI 不再 push plugins/）；GH Release v0.6.0 含 3 tarball
4. 本地跑 `sh install.sh specguard-default` 验证下载安装成功
5. 回填 design.md 顶部 `Last verified against code` + commit + push

**Verify**：GH Release v0.6.0 含 3 tarball；main HEAD 是 Task 6 的 commit（无额外 CI commit）；`sh install.sh specguard-default` 打印出 claude 命令行。

---

## Self-review

- [x] Task 2（git rm）和 Task 3（release.yml）要分开 commit，方便回滚
- [x] install.sh 用 `set -e`，curl 失败不会静默继续
- [x] release.yml 不再需要 `ref: main`，默认 checkout tag 即可
- [x] 版本测试改名在 Task 5 做，避免 Task 4 中途测试失败
- [x] design.md §4 契约从 9→7（删 2 条），§6 不变量从 9→8（删 1 条），与 spec 一致
