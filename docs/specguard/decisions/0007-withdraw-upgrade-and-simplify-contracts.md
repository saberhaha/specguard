# ADR 0007: 撤回 `/specguard:upgrade` 并精简伪契约

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，确认 upgrade 是伪需求并要求一并精简同根连带的伪契约）
**取代**：ADR-0006
**相关**：
- ADR-0002（`/specguard:init` 自动合并 hooks）— 状态保持 Accepted；hooks 自动合并能力保留，但 `/specguard:check` 不再校验 hooks 合并结果（第 11、12 项删除）。
- ADR-0003（GitHub Release tarball 分发）— 状态保持 Accepted；分发渠道不变，但 `.specguard-version` 中的 `plugin_source` 字段随 `.specguard-version` 一并废弃。
- ADR-0004（init/upgrade 算法下沉为 Python 模块）— 状态保持 Accepted；`hooks_merge.py` 模块保留（init 仍调用），`upgrade.py` 模块删除。
- design.md §5.4 / §6 / §8

## Context

v0.2.1 dogfood 暴露 `/specguard:upgrade` 在 GitHub Release tarball 中找不到 `version` 文件的 bug，进一步反思该命令的真实价值时发现：

1. specguard 处于 v0.x 阶段，用户基数为 0，目前不存在真实的跨版本升级痛点。
2. 同类工具（OpenSpec、Spec Kit、Superpowers）均无 upgrade 命令的惯例，用户预期靠重新 init / 手工合并即可完成版本迁移。
3. `/specguard:upgrade` 拖出了一系列只为它服务的伪契约：`.specguard-version` 文件、`.specguard-version` 中的 `plugin_source` 字段、`.specguard/hooks.snippet.json` 持久化文件、`decisions/README.md` 中 `<!-- specguard:rules:start/end -->` marker；这些契约只在 upgrade diff/replace 流程中被读取，与 init / check / 治理价值无关。
4. `/specguard:check` 第 11~13 项（hooks.snippet.json 存在、settings.json 含 specguard hooks、`.specguard-version` 存在）作为 upgrade 的同根校验，一并属于伪契约。

## Decision

按以下范围执行撤回与精简：

1. **撤回 upgrade**：删除 `/specguard:upgrade` 命令、`core/command-prompts/upgrade.md`、`src/specguard/upgrade.py`、所有 upgrade 相关测试。
2. **删除四个伪契约**：
   - `.specguard-version` 文件（含 `specguard_version` 与 `plugin_source` 字段）；
   - `.specguard/hooks.snippet.json` 持久化文件；
   - `decisions/README.md` 中 `<!-- specguard:rules:start/end -->` marker block；
   - `.specguard-version` 中的 `plugin_source` provenance 字段（随文件一并废弃）。
3. **`/specguard:check` 收敛**：第 11 项（hooks.snippet.json 存在）、第 12 项（settings.json 含 specguard hooks）、第 13 项（`.specguard-version` 存在）作为同根连带删除，13 项收敛为 11 项。
4. **保留项**（与 upgrade 解耦、独立成立）：
   - `/specguard:init` 自动合并 hooks 到 `.claude/settings.json`：design / ADR / spec 治理价值与 upgrade 无关，保留；
   - `CLAUDE.md` 的 `<!-- specguard:start/end -->` marker：init 幂等需要，保留；
   - `src/specguard/hooks_merge.py` runtime 模块：init 仍调用，保留。

v0.3.0 标记为 BREAKING release。

## Consequences

- **正面**：
  - 移除一个伪需求功能与四个仅服务它的伪契约，降低用户认知负担与维护面。
  - design.md 数据契约从 11 条收敛到 7 条；不变量从 8 条降到 7 条；`/specguard:check` 从 13 项收敛到 11 项。
  - 周边 ADR（0002/0003/0004）核心结论仍成立，仅在本 ADR 的相关段落记录其受影响的边界字段。
- **负面**：
  - v0.3.0 是 BREAKING release，从 v0.2.x 升级的用户需手动删除 `.specguard-version`、`.specguard/hooks.snippet.json` 与 `decisions/README.md` 中的 rules marker 内容。
  - ADR-0006 失效（被本 ADR 取代）。
- **同步更新**：
  - `docs/specguard/design.md`：§5.4 删除 upgrade 章节；§6 数据契约从 11 条收敛到 7 条；§8 check 项从 13 项收敛到 11 项；不变量从 8 条降到 7 条；顶部 `Last verified against code` 更新为本切片 commit hash。
  - `docs/specguard/decisions/0006-tighten-upgrade-interaction-and-version-handling.md`：状态字段改为 `Superseded by ADR-0007`。
  - `docs/specguard/decisions/README.md`：索引表追加 0007 行。
  - 代码：删除 `core/command-prompts/upgrade.md`、`src/specguard/upgrade.py`、`tests/test_dogfood_upgrade.py`、`tests/test_render_claude_default.py` 中 upgrade 相关用例；`/specguard:check` 实现收敛到 11 项；init 不再写 `.specguard-version`、不再写 `.specguard/hooks.snippet.json`、不再写 `decisions/README.md` rules marker。
  - `README.md` / `CHANGELOG.md`：标注 v0.3.0 BREAKING、移除 upgrade 文档。

## 替代方案

- **保留 upgrade 但修 tarball version bug**：拒绝。根本问题不是实现 bug，而是伪需求；继续维护 upgrade 会持续拖动四个伪契约的演化成本。

## 未来留位

未来若出现真实用户与真实跨版本升级痛点，重新立 ADR 设计 upgrade，不复用本次撤回的实现。
