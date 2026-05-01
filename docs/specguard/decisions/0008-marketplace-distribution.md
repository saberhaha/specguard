# ADR 0008: 通过 Claude Code marketplace 分发 specguard plugin

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01）
**取代**：—
**相关**：
- ADR-0003（GitHub Release tarball 分发）— 状态保持 Accepted；tarball 路径作为 marketplace 不可达（离线 / 受限网络 / 私有 GitHub Enterprise）时的 fallback 渠道。
- ADR-0004（hooks_merge.py runtime 模块）— 状态保持 Accepted；marketplace 安装的 plugin 仍包含 `runtime/specguard/`，`/specguard:init` 仍通过 `CLAUDE_PLUGIN_ROOT` 调用 `hooks_merge`。
- design.md §2 / §3.1 / §6 / spec docs/specguard/specs/v0-4-0-marketplace-distribution-spec.md

## Context

v0.3.0 用户安装 specguard 的实际路径仍是：从 GitHub Release 页面手动下载 tarball、解压、再向 Claude Code 传 `--plugin-dir <解压目录>`。该流程需要用户处理本地路径与解压步骤，与 Claude Code 在 v1.x 引入的内置 plugin marketplace 体验（`/plugin marketplace add` + `/plugin install`）相比明显粗糙。

核实 Claude Code 官方 marketplace 文档（2026-05-01，https://code.claude.com/docs/en/plugin-marketplaces）：

1. marketplace plugin source 仅支持 git tracked 内容（`git`、`git-subdir`、`github` 等），**不支持** GitHub Release tarball asset 作为 plugin source。
2. marketplace entry 中可选写 `version` 字段，但官方文档明确提示：若 `marketplace.json` 与 plugin 自身 `plugin.json` 同时声明 version，将出现双写不一致风险。

这两条事实共同约束了：要走 marketplace 分发，rendered plugin 产物必须进 git tracked；version 只能由一处声明。

specguard 当前已有三种 layout（`specguard-default`、`specguard-superpowers`、`specguard-openspec-sidecar`），三种均有真实使用场景，不能只发其中一个。

## Decision

按以下范围引入 marketplace 分发：

1. **单 repo 布局**：在当前 specguard repo 根新增 `.claude-plugin/marketplace.json`，列出 3 个 plugin（`specguard-default`、`specguard-superpowers`、`specguard-openspec-sidecar`），各自 `source` 用 `git-subdir` 指向同 repo 的 `plugins/<layout>/` 子目录。
2. **rendered 产物 git tracked**：plugin rendered 产物落在 `plugins/specguard-default/`、`plugins/superpowers/`、`plugins/openspec-sidecar/` 三个子目录，提交进 git。
3. **CI 自动 render + commit + push**：`release.yml` 在 tag push 触发后，单 job 内串行执行 render 三个 layout 到 `plugins/`、`git pull --rebase`、`git commit --allow-empty`、`git push origin HEAD:main`，再 build tarball。
4. **版本注入策略**：`plugin.json.version` 由 render 时从 `core/version` 注入；`marketplace.json` entry 不写 `version` 字段，避免双写冲突（符合官方文档警告）。
5. **保留 tarball 路径**：GitHub Release tarball 不删除，作为离线 / 受限网络 / 私有 GitHub Enterprise 用户的 fallback。
6. **CI race 防护**：单 job 串行执行（render → pull --rebase → commit → push HEAD:main → build tarball），不并发触发。

## Consequences

- **正面**：
  - 用户安装路径从"下载 tarball + 解压 + `--plugin-dir`"简化为 `/plugin marketplace add saberhaha/specguard` + `/plugin install <layout>`。
  - 三个 layout 通过 marketplace 一并发布，覆盖现有所有使用场景。
  - tarball 渠道保留，离线 / 受限网络用户不受影响。
- **负面**：
  - main 分支历史每次 release 多出一类 `chore(release): render plugins for v...` commit；语义类似 npm publish 把 `dist/` 提交到 git。
  - `plugins/` 目录下文件不能由人工编辑，否则会被 CI render 覆盖；通过 `README` 与 `CHANGELOG` 显式提示。
  - design.md 数据契约从 7 条扩展到 9 条（新增 `marketplace.json` schema、`plugins/<layout>/` 结构）；不变量从 7 条扩展到 8 条（新增 "`marketplace.json` 列出的 plugin path 必须 git tracked"）。
- **同步更新**：
  - `docs/specguard/design.md`：§2 / §3.1 / §6 同步 marketplace 渠道、`plugins/<layout>/` 结构、新增数据契约与不变量；顶部 `Last verified against code` 更新为本切片 commit hash。
  - `docs/specguard/decisions/README.md`：索引表追加 0008 行。
  - 代码：新增 `.claude-plugin/marketplace.json`、`plugins/specguard-default/`、`plugins/superpowers/`、`plugins/openspec-sidecar/`；`release.yml` 增加 render + commit + push 步骤。
  - `README.md` / `CHANGELOG.md`：补充 marketplace 安装路径与 tarball fallback 说明。

## 替代方案

- **独立 specguard-marketplace repo + git-subdir**：双 repo 维护成本高（marketplace.json 与 rendered 产物分别在两个 repo，release 流程需跨 repo 同步），拒绝。
- **同 repo 3 个 release branch（每个 layout 一个 branch）**：non-standard 布局，git-subdir 语义被复用为 layout 选择器，可读性差，拒绝。
- **仅发 specguard-default 一个 layout**：丢失 superpowers / openspec-sidecar 用户场景，拒绝。

## 未来留位

未来若 Anthropic marketplace API 支持 GitHub Release tarball 作为 plugin source，可考虑撤回 `plugins/` git tracked，回到 ADR-0003 纯 tarball 路径；撤回需新立 ADR。
