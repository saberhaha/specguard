# ADR 0001: 使用 plugin name 作为 Claude slash command 命名空间

**状态**：Accepted
**日期**：2026-04-30
**拍板者**：用户（@saber，对话日期 2026-04-30，dogfood 验证阶段选择 `/specguard:init` 方案）
**取代**：—
**相关**：[design.md §2](../design.md) / [spec 2026-04-30-mvp-scaffold-spec.md §3](../specs/2026-04-30-mvp-scaffold-spec.md)（已部分 superseded）/ [v0.1.1 dogfood-fix spec](../specs/2026-04-30-v0.1.1-dogfood-fix-spec.md)

## Context

specguard MVP spec 原计划让 Claude Code plugin 使用短命令 `/sg:init`、`/sg:check`、`/sg:upgrade`，并在 `plugin.json` 中加入 `commandNamespace: "sg"`。

在 dogfood 验证阶段，`claude plugin validate dist/claude/superpowers` 返回错误：`root: Unrecognized key: "commandNamespace"`。本机已安装的官方 superpowers plugin 的 `.claude-plugin/plugin.json` 也不包含 `commandNamespace` 字段；Claude Code 的命令命名空间由 plugin name 决定。

用户在 2026-04-30 的对话中选择保留 plugin name `specguard`，接受命令变为 `/specguard:init`、`/specguard:check`、`/specguard:upgrade`。

## Decision

Claude adapter 不再使用 `commandNamespace` 字段。specguard 的 Claude Code slash commands 使用 plugin name 作为命名空间：`/specguard:init`、`/specguard:check`、`/specguard:upgrade`。

## Consequences

- **正面**：plugin manifest 符合 Claude Code 当前校验规则；命令命名与产品名一致。
- **负面**：命令比原计划 `/sg:*` 更长；原 MVP spec 中关于短前缀的表述需要按此 ADR 修正理解。
- **同步更新**：README.md、adapter plugin.json 模板、command prompt 文案、render 测试、design.md、MVP spec supersede 标记。
- **运行时约束**：Claude Code 出于安全考虑不适合让 slash command 自动改写 `.claude/settings.json`；`/specguard:init` 写出 `.specguard/hooks.snippet.json`，由用户手动合并 hooks。
