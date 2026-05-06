# ADR 0011: 撤回 marketplace 分发并以 install.sh 替代

**状态**：Accepted
**日期**：2026-05-02
**拍板者**：用户（@saber，对话日期 2026-05-02）
**取代**：ADR-0008
**相关**：
- ADR-0003（GitHub Release tarball 分发）— 状态保持 Accepted；tarball 路径保留，不受本决策影响。

## Context

ADR-0008 在 v0.4.0 引入 marketplace 分发：`.claude-plugin/marketplace.json` 列出 3 个 layout，`plugins/<layout>/` git-tracked 目录存放 rendered 产物，`release.yml` 在每次 tag push 后自动执行 render + commit + push。

v0.4.0 dogfood（2026-05-01，Claude Code v2.1.123）发现两个上游限制，已记录在 ADR-0008 Consequences：

1. marketplace 安装路径**不暴露 `CLAUDE_PLUGIN_ROOT`** 给 slash command runtime，导致 `/specguard:init` hooks 合并步骤按设计停止——核心功能缺失。
2. 同一 marketplace 多次执行 `plugin install` 存在 `ENOTEMPTY` race，缓存目录可能瞬时缺失。

维护成本：每次 release 多出一个自动 commit（`chore(release): render plugins for vX.Y.Z`）+ `git pull --rebase` race 风险；收益：零（核心功能因上游限制无法正常工作）。

用户决策（2026-05-02）：删除 marketplace 分发全套，以 `install.sh` 替代。

## Decision

1. 删除 `.claude-plugin/marketplace.json` + `plugins/<layout>/` 三个 git-tracked 目录（共 21 文件）。
2. 删除 `tests/test_marketplace_schema.py` + `tests/test_release_workflow.py` 中的 `test_release_workflow_renders_and_commits_plugins` 测试用例。
3. 还原 `.github/workflows/release.yml`：删除 checkout main / render plugins / commit+push 三个步骤，恢复为纯 tarball 模式。
4. 新增 `install.sh`（项目根）：接受可选参数 `<layout>`（默认 `specguard-default`），curl 下载最新 tarball，解压到 `~/.local/share/specguard/plugins/<layout>/`，打印后续 claude 命令。
5. GitHub Release tarball 分发（ADR-0003）保持不变。

## Consequences

- **正面**：
  - `release.yml` 简化为纯 tarball 模式，无自动 commit / pull --rebase race 风险。
  - design.md 数据契约从 9 条降回 7 条（移除 `marketplace.json` schema 与 `plugins/<layout>/` 结构两条）。
  - 代码库删除 22 个文件（21 个 plugins/ 产物 + `marketplace.json`）。
- **负面**：
  - 用户安装路径从 2 行命令（`marketplace add` + `install`）变为 1 行 `install.sh`；安装体验略粗糙，但 hooks 合并恢复正常工作。
- **同步更新**：
  - `docs/specguard/design.md`：§3.5 / §4 / §6 / §7.1 / §7.2 删除 marketplace 相关内容；§2.1 Mermaid 图同步移除 marketplace 节点；顶部 `Last verified against code` 更新。
  - `docs/specguard/decisions/README.md`：索引追加 0011 行，0008 行状态同步为 `Superseded by ADR-0011`。
  - `docs/specguard/decisions/0008-marketplace-distribution.md`：顶部状态改为 `Superseded by ADR-0011`。
  - 代码：删除 `.claude-plugin/marketplace.json`、`plugins/` 三个子目录、相关测试；还原 `release.yml`；新增 `install.sh`。
- **未来**：若 Claude Code 修复 `CLAUDE_PLUGIN_ROOT` 暴露问题，可重新评估 marketplace 分发路径，届时新立 ADR。
