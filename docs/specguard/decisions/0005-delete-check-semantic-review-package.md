# ADR 0005: 删除 `/specguard:check semantic` review package 模式

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，确认删除 v0.1 semantic review package 残留）
**取代**：—
**相关**：[design.md §5.3 / §8](../design.md) / spec [design-doc-restructure-and-v0-1-cleanup-spec.md](../specs/design-doc-restructure-and-v0-1-cleanup-spec.md)

## Context

v0.1 的 `/specguard:check semantic` 会生成 `.specguard/reviews/<UTC>/`，其中包含给另一个 LLM 使用的 `prompt.md`、`context.md`、`findings-template.md`。这来自早期工具型心智：把 semantic review 当成离线 review package 生成器。

现在 `/specguard:check` 本身就是 Claude Code slash command，运行环境已经是 LLM 对话。继续生成另一个 LLM 的 prompt/context/findings-template 会让命令边界变复杂，也会误导用户以为 specguard 有单独的 LLM review 子系统。

## Decision

删除 `/specguard:check semantic` review package 模式。

`/specguard:check` 在 v0.2.1 起只表达结构治理检查：读取当前项目文件、输出 error/warning/report，不创建 `.specguard/reviews/`，不生成 `prompt.md` / `context.md` / `findings-template.md`。

未来如果需要语义审查，应在 `/specguard:check` 的当前 Claude 对话内直接输出 findings，而不是恢复 review package 目录。

## Consequences

- **正面**：
  - `/specguard:check` 的用户心智收敛为只读治理检查。
  - 删除 v0.1 残留的数据契约，避免 `.specguard/reviews/` 被误认为稳定产物。
  - design.md 不再描述未被当前产品定位支持的 review package。
- **负面**：
  - 已经依赖 `.specguard/reviews/` 离线包的用户需要改为在当前 Claude 对话中请求语义 review。
- **同步更新**：
  - `core/command-prompts/check.md` 删除 `semantic` 参数与 Semantic mode 小节。
  - `docs/specguard/design.md` §5 / §8 记录该模式已删除。
  - `tests/test_render_claude_default.py` 断言 rendered `commands/check.md` 不含 semantic review package 文案。
