# ADR 0003: 通过 GitHub Release tarball 分发 Claude plugin

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，P0+P1 范围确认）
**取代**：—
**相关**：[design.md §2 / §3.1 / §3.3 / §6](../design.md) / spec [distribution-and-auto-hooks-spec.md](../specs/distribution-and-auto-hooks-spec.md)

## Context

v0.1.x 的实际使用路径是：用户 clone specguard 仓库、执行 `uv sync`、运行 `specguard-render`、再用 `claude --plugin-dir dist/claude/<layout>` 指向本地构建产物。这是开发者路径，不是通用工具的用户路径。

当前 design.md §6 把 Marketplace 打包、`/specguard:upgrade` 端到端 dogfood列为 v0.2+ 事项。用户明确选择 P0+P1 一起做，目标是先让别人不用 clone 源码也能使用，同时补上升级闭环。

## Decision

v0.2 起，specguard 的 Claude plugin 首个对外分发渠道采用 GitHub Release tarball，不等待 marketplace。

1. **Release artifact**：tag 触发 GitHub Actions，分别渲染三个 layout 并发布 tarball：
   - `specguard-claude-specguard-default-vX.Y.Z.tar.gz`
   - `specguard-claude-superpowers-vX.Y.Z.tar.gz`
   - `specguard-claude-openspec-sidecar-vX.Y.Z.tar.gz`
2. **artifact 内容**：tarball 根目录即 Claude plugin 根目录，至少包含 `.claude-plugin/plugin.json`、`skills/`、`commands/`、`hooks/`。
3. **版本来源记录**：`.specguard-version` schema 新增必填字段：
   ```toml
   plugin_source = "github-release-vX.Y.Z" # 或 "local-dist"
   ```
   通过 release tarball 初始化时写 `github-release-vX.Y.Z`；本地 `dist/` dogfood 时写 `local-dist`。
4. **upgrade 端到端语义**：`/specguard:upgrade` 必须按 design.md §3.3 的 5 个 marker 区域执行 diff 与替换。marker 缺失时报 conflict 并输出 manual patch，不自动插入。
5. **README 用户路径**：README 顶部提供用户安装路径；开发者 render 路径下移为 development section。
6. **Marketplace**：暂不作为 v0.2 交付项；未来如果 marketplace 可用，再新增 ADR 评估是否替换或并行 GitHub Release 渠道。

## Consequences

- **正面**：
  - 用户不再需要 clone 源码、安装 uv 或理解 render 管线即可试用。
  - `.specguard-version.plugin_source` 让 upgrade 与问题排查能区分 release 安装和本地 dogfood。
  - GitHub Release 是可控的中间形态，适合 v0.x 快速迭代。
- **负面**：
  - 引入 GitHub Release / GitHub Actions 作为外部分发依赖。
  - `.specguard-version` schema 发生变化，upgrade 必须兼容没有 `plugin_source` 的 v0.1.x 项目。
  - tarball 安装仍不是 marketplace 级别的一键安装，用户仍需保存 plugin 目录并用 `claude --plugin-dir` 指定。
- **同步更新**：
  - [docs/specguard/design.md](../design.md) §2 增加 release artifact 说明；§3.1 `.specguard-version` 字段增加 `plugin_source`；§3.3 增加 v0.1.x 缺字段兼容；§6 移除 `/specguard:upgrade` 端到端 dogfood，保留 marketplace。
  - [core/command-prompts/init.md](../../../core/command-prompts/init.md) 写 `.specguard-version` 时新增 `plugin_source`。
  - [core/command-prompts/upgrade.md](../../../core/command-prompts/upgrade.md) 对 v0.1.x 缺少 `plugin_source` 的项目按 legacy local install 处理并补写字段。
  - 新增 `.github/workflows/release.yml`。
  - README 改为用户安装优先。
  - 新增测试：release artifact 结构测试、upgrade legacy `.specguard-version` 测试。
