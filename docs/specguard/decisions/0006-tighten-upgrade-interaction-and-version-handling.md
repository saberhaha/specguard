# ADR 0006: 收紧 `/specguard:upgrade` 写入前交互与缺版本行为

**状态**：Superseded by ADR-0007
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，确认 upgrade 必须先展示 diff summary 并等待确认）
**取代**：—
**相关**：[design.md §5.4 / §6](../design.md) / spec [design-doc-restructure-and-v0-1-cleanup-spec.md](../specs/design-doc-restructure-and-v0-1-cleanup-spec.md)

## Context

`/specguard:upgrade` 会修改已经存在的用户项目文件，包括 `CLAUDE.md` marker block、`.claude/settings.json` 中 specguard hooks、两个 `TEMPLATE.md`、`decisions/README.md` rules marker block 和 `.specguard-version`。

这些文件属于用户项目治理入口。upgrade 如果在缺 `.specguard-version` 时复合执行 init-then-upgrade，或者在未展示差异前直接写入，会扩大命令副作用并削弱用户对写入范围的判断。

## Decision

收紧 `/specguard:upgrade` 的运行语义：

1. 缺 `.specguard-version` 时立即停止，提示用户先运行 `/specguard:init`；不在 upgrade 内执行 init-then-upgrade 复合流程。
2. 先解析 `CLAUDE_PLUGIN_ROOT` 并读取 `${CLAUDE_PLUGIN_ROOT}/version`，再与 `.specguard-version` 的 `specguard_version` 比较。
3. 版本相等时输出 `already up to date` 并退出，不执行写入。
4. 版本不同时先调用 `upgrade_project(Path("."), replacements, dry_run=True)`，展示 `UpgradeResult.diff_summary`，等待用户明确确认。
5. 用户确认后再调用 `upgrade_project(Path("."), replacements, dry_run=False)` 执行写入。

## Consequences

- **正面**：
  - upgrade 的写入边界可预测，符合"写入前展示 diff summary"的用户契约。
  - 缺版本文件被明确视为未初始化状态，避免 upgrade 偷偷承担 init 职责。
  - prompt 与 runtime API 形成明确依赖：prompt 依赖 `UpgradeResult.diff_summary` 和 `dry_run=True` 不写文件语义。
- **负面**：
  - prompt 与 `src/specguard/upgrade.py` 的 API 耦合更强；rendered command 测试必须覆盖该耦合。
  - 用户从未初始化项目升级时需要先运行一次 `/specguard:init`。
- **同步更新**：
  - `src/specguard/upgrade.py` 增加 `dry_run` 参数与 diff summary 返回值。
  - `core/command-prompts/upgrade.md` 落实 missing-version stop、already-up-to-date short-circuit、dry-run summary、confirm-before-write。
  - `tests/test_dogfood_upgrade.py` 覆盖 dry-run 不写文件与 diff summary。
  - `tests/test_render_claude_default.py` 覆盖 rendered upgrade prompt 语义。
