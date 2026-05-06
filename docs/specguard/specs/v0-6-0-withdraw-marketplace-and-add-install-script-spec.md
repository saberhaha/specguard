# v0-6-0-withdraw-marketplace-and-add-install-script 设计

**日期**：2026-05-02
**适用范围**：v0.6.0：撤回 marketplace 分发（ADR-0008），删除 `.claude-plugin/marketplace.json` 与 `plugins/` git-tracked 目录，新增 `install.sh` 作为用户安装入口，还原 release.yml 至纯 tarball 模式。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 新增 `install.sh`：接受可选参数 `<layout>`（默认 `specguard-default`），从 GitHub Release 下载最新 tarball，解压到 `~/.local/share/specguard/plugins/<layout>/`，打印后续要跑的 claude 命令。
2. 删除 `.claude-plugin/marketplace.json` 与 `plugins/` 目录（3 layout × 7 文件 = 21 文件）。
3. 修改 `.github/workflows/release.yml`：删除"Configure git user"、"Render plugins/ for marketplace"、"Commit and push rendered plugins/"三个步骤；保留 checkout 改回 tag（不再需要 checkout main）。
4. 删除 `tests/test_marketplace_schema.py`；删除 `tests/test_release_workflow.py::test_release_workflow_renders_and_commits_plugins`。
5. 同步 `docs/specguard/design.md`：删 §3.5（marketplace 与 plugins/）、数据契约第 8/9 条、不变量第 8 条、§7.1 风险表 marketplace 行、§7.2 改动类型表 marketplace 行；§3 节编号随删除段调整。
6. 更新 `README.md`：快速开始改为 `curl .../install.sh | sh`（或 `sh install.sh`），删 marketplace 段。
7. 更新 `CHANGELOG.md`：顶部新增 v0.6.0 段。
8. ADR-0008 状态改为 `Superseded by ADR-0011`；新建 ADR-0011。
9. bump `core/version` → `0.6.0`、`pyproject.toml` → `0.6.0`、`uv.lock`、`tests/test_release_workflow.py` 版本断言。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 新增 install.sh | ✓ | - | - | - | - |
| #2 删 marketplace.json + plugins/ | ✓ | ✓ | - | - | ✓ |
| #3 release.yml 还原 tarball-only | - | - | ✓ | - | ✓ |
| #4 删测试 | - | - | - | - | - |
| #5-9 文档/版本同步 | - | - | - | - | - |

### 候选 ADR（已拍板）

- **ADR-0011：撤回 marketplace 分发，以 install.sh 替代**
  - 取代：ADR-0008
  - 覆盖改动 #1-#3
  - 核心理由：marketplace 在 Claude Code v2.1.123 下 `CLAUDE_PLUGIN_ROOT` 不暴露，hooks 无法自动合并，核心功能缺失；维护 `plugins/` git-tracked 产物每次 release 多一个自动 commit + ENOTEMPTY race，维护成本真实，收益为零；`install.sh` 是对现有 tarball 分发的薄封装，无额外机制依赖。
  - GitHub Release tarball 分发（ADR-0003）保持不变。

### 不需要 ADR

- #4-#9：执行已确定方向，不引入新决策。

## 对 design.md 的影响

- §3.5 marketplace 与 plugins/：整段删除。
- §4 数据契约：第 8 条（marketplace.json schema）、第 9 条（plugins/<layout>/ 结构）删除，9 条 → 7 条。
- §6 不变量：第 8 条（marketplace plugin path 完整性）删除，9 条 → 8 条。
- §7.1 风险表：删除 `plugins/ 与 src/ 脱同步` 行；对应的 release.yml 约束也随 release.yml 简化而消失。
- §7.2 改动类型表：删除 `marketplace.json schema 修改` 行。
- §2.1 Build/Release flow Mermaid：还原为 v0.3.0 形态（删 PD/PR/PC/PP 四个节点，即 plugins/ render+commit+push 链路）。
- 顶部 `Last verified against code` 同步到本切片最终 HEAD。

## 1. 切片范围

**包含**

1. 新建 ADR-0011；ADR-0008 状态改为 `Superseded by ADR-0011`；`decisions/README.md` 索引更新。
2. 新建 `install.sh`（项目根）：
   ```bash
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
3. `git rm -r .claude-plugin/ plugins/`（删 22 文件：marketplace.json + 21 rendered 文件）。
4. 修改 `.github/workflows/release.yml`：
   - `actions/checkout@v4` 恢复默认（不再需要 `ref: main` + `fetch-depth: 0`）
   - 删除"Configure git user"步骤
   - 删除"Render plugins/ for marketplace"步骤
   - 删除"Commit and push rendered plugins/"步骤
   - "Render and package tarballs"步骤名改回"Render and package layouts"
5. 删除 `tests/test_marketplace_schema.py`；从 `tests/test_release_workflow.py` 删除 `test_release_workflow_renders_and_commits_plugins`。
6. 同步 `docs/specguard/design.md`（见上节）。
7. 更新 `README.md`：快速开始改为 `install.sh` 用法，一行 curl + sh 或本地跑。
8. 更新 `CHANGELOG.md`：v0.6.0 段，标记 BREAKING（marketplace 删除），列出：删除 marketplace.json / plugins/ / test_marketplace_schema.py，新增 install.sh，release.yml 还原。
9. bump 版本到 0.6.0。

**不包含**

- 删除 GitHub Release tarball 构建（保留）。
- 修改 hooks 行为（不在本切片）。
- Cursor / Codex adapter（后续）。

## 2. 验收标准

1. **ADR-0011 落档**：`docs/specguard/decisions/0011-withdraw-marketplace-and-add-install-script.md` 存在；ADR-0008 状态为 `Superseded by ADR-0011`；decisions/README.md 索引含 0011 行。
2. **marketplace 完全清除**：`.claude-plugin/` 目录不存在；`plugins/` 目录不存在；`git ls-files | grep -E "^\.claude-plugin/|^plugins/"` 无命中；`tests/test_marketplace_schema.py` 不存在；`tests/test_release_workflow.py` 不含 `renders_and_commits_plugins`。
3. **install.sh 可用**：`sh install.sh --help` 或 `sh install.sh specguard-default` 能正确解析参数；脚本通过 `shellcheck install.sh`（如有）；README 快速开始只有 install.sh 路径。
4. **release.yml 还原**：不含 `git push origin HEAD:main`、`git add plugins/`、`ref: main`；只含 render dist/ + build tarball + upload；`uv run pytest` 全绿。
5. **v0.6.0 发布**：`core/version` = `0.6.0`；`uv run pytest` 全绿（原 78 passed 减去 marketplace 测试，约 70 passed）；v0.6.0 tag 推送；GH Release 含 3 tarball；`sh install.sh specguard-default` 可成功下载安装。

## 3. 留给后续切片

- Cursor / Codex adapter。
- 若 Claude Code 上游修复 `CLAUDE_PLUGIN_ROOT` 暴露，重新评估 marketplace 是否值得恢复（新立 ADR）。
