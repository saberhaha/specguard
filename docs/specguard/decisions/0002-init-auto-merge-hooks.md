# ADR 0002: `/specguard:init` 自动合并 hooks 到 `.claude/settings.json`

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，"P0+P1 一起做"+"我偏严"决策）
**取代**：—（推翻 [ADR-0001](0001-plugin-name-command-namespace.md) Consequences 段中"不自动改 settings.json"运行时约束）
**相关**：[design.md §3.1 / §3.2 / §3.3 / §4](../design.md) / spec [distribution-and-auto-hooks-spec.md](../specs/distribution-and-auto-hooks-spec.md)

## Context

ADR-0001 在 dogfood v0.1.0 阶段确定的运行时约束是：`/specguard:init` 不直接修改 `.claude/settings.json`，只写出 `.specguard/hooks.snippet.json` 由用户手动合并。原因是当时担心 slash command 自动改写 `.claude/settings.json` 不可靠。

实际使用暴露两个问题：
1. 用户在初次 `/specguard:init` 之后大概率忘记手动合并 snippet，导致 hooks 实际未生效；
2. `/specguard:check` 第 12 项把"`.claude/settings.json` 缺少 specguard hooks"列为 warning 而非 error，使配置漂移在治理层面被默认接受。

随着 v0.2 准备首次对外分发（见 [ADR-0003](0003-distribution-via-github-release.md)），这条手动步骤变成产品体验的硬阻塞。同时，hooks 条目通过 `statusMessage` 前缀 `specguard:` 已经有稳定的标记机制，幂等合并可控。

## Decision

`/specguard:init` 在第 5 步直接合并 hooks 到 `.claude/settings.json`，规则如下：

1. **写出 snippet 仍保留**：先把内嵌 JSON 写入 `.specguard/hooks.snippet.json`，作为可审计的 source-of-truth。
2. **读 → 合并 → 写**：随后读取现有 `.claude/settings.json`（不存在则视为空 `{"hooks": {}}`），按下述算法合并 specguard hooks，再写回。
3. **合并算法**：
   - 顶层按 event 名做 union；保留所有非 specguard 顶层键。
   - 同 event 内逐条扫描数组：仅当某条 hook 命令字符串包含 `statusMessage` 字段且值以 `specguard:` 开头时，视为 specguard 条目，按 `statusMessage` 值做幂等替换；非 specguard 条目原样保留。
   - 顺序：specguard 条目追加在该 event 数组末尾，不打断已有顺序。
4. **`--dry-run` 标志**：`/specguard:init --dry-run` 只打印将要合并的 diff（包含 snippet 写入与 settings.json 合并预览），不落盘。本标志为新增对外语义。
5. **失败语义**：
   - 现有 `.claude/settings.json` 不是合法 JSON：报错并指向手工修复，不覆盖原文件。
   - 写回时使用 atomic replace（先写 `.tmp` 再 rename），避免半写状态。
6. **`/specguard:check` 第 12 项升为 error**：缺失 specguard hooks 不再是 warning。

## Consequences

- **正面**：
  - init 一步到位，用户体验从"两步且容易忘记"变为"一条命令完成"。
  - check 严格性提升，治理层不再默认接受配置漂移。
  - dry-run 提供了"先看再改"的安全边界，回应原 ADR-0001 的安全顾虑。
- **负面**：
  - 修改用户工程内的 `.claude/settings.json` 是侵入式行为，破坏 ADR-0001 第 4 条 Consequence 的承诺；如用户 settings.json 包含未知 schema，幂等性依赖 `specguard:` 前缀这一软约定。
  - dry-run 增加一条对外 flag，需要在 README、command prompt、check 行为中保持一致。
- **同步更新**：
  - [docs/specguard/design.md](../design.md) §3.1 第 5 步、§3.2 第 12 项、§4 末尾追加 `（见 ADR-0002）`；§6 移除 `/specguard:upgrade 端到端 dogfood` 之外不再属于本轮范围的条目。
  - [core/command-prompts/init.md](../../../core/command-prompts/init.md) 第 5 步重写：写 snippet → 读 settings.json → 合并 → 写回；新增 `--dry-run` 描述。
  - [core/command-prompts/check.md](../../../core/command-prompts/check.md) 第 12 项措辞：缺失为 error。
  - [adapters/claude/plugin/commands/init.md.tpl](../../../adapters/claude/plugin/commands/init.md.tpl) frontmatter `argument-hint` 增加 `[--dry-run]`。
  - [README.md](../../../README.md) Quickstart：移除"手动合并 snippet"步骤。
  - 新增测试：`tests/test_init_merge_hooks.py`（合并算法 + 幂等性 + dry-run）。
