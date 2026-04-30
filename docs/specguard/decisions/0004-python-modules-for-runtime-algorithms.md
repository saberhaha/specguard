# ADR 0004: 将 init hooks 合并与 upgrade marker 替换下沉为 Python 模块

**状态**：Accepted
**日期**：2026-05-01
**拍板者**：用户（@saber，对话日期 2026-05-01，选择方案 A）
**取代**：—
**相关**：[design.md §3.1 / §3.3 / §5](../design.md) / spec [distribution-and-auto-hooks-spec.md](../specs/distribution-and-auto-hooks-spec.md)

## Context

v0.1.x 的 `/specguard:init`、`/specguard:check`、`/specguard:upgrade` 是 Claude Code slash command prompt，由 LLM 按 prompt 执行。ADR-0002 要求 `/specguard:init` 自动幂等合并 hooks；ADR-0003 要求 `/specguard:upgrade` 端到端替换 5 个 marker 区域。

这些行为如果只写在 prompt 中，无法被 `pytest` 稳定覆盖；只能依赖真 Claude dogfood，难以进入 CI。用户已确认选择方案 A：把核心算法落成 Python module，prompt 调用 module，测试直接覆盖 module。

## Decision

新增两个纯 Python 模块承载可测试核心逻辑：

1. `src/specguard/hooks_merge.py`
   - 负责 `.claude/settings.json` 与 `.specguard/hooks.snippet.json` 的解析、合并、幂等替换、dry-run diff 文本生成。
   - 对外暴露可由测试和 prompt 调用的函数；CLI prompt 不重新实现合并算法。
2. `src/specguard/upgrade.py`
   - 负责 5 个 marker 区域的检测、diff 生成、替换、conflict 识别、legacy `.specguard-version` 补写 `plugin_source`。
   - 对外暴露可由测试和 prompt 调用的函数；CLI prompt 不重新实现 marker 替换算法。

command prompt 的职责收敛为：解析用户参数、说明行为、调用 Python 模块、汇报结果。

## Consequences

- **正面**：
  - hooks 合并与 upgrade 替换可被 `pytest` 稳定覆盖，满足 ADR-0002/0003 的验收要求。
  - slash command prompt 变薄，减少 LLM 运行时自由发挥导致的漂移。
  - 后续如果增加 Python CLI 或其它 agent adapter，可复用同一算法。
- **负面**：
  - Claude plugin 在目标项目运行时需要能 import `specguard` Python package；release tarball 必须携带或安装该 package 的可用路径，否则 prompt 调用会失败。
  - adapter command prompt 与 Python module 之间形成新的跨模块依赖，需要在 render/release artifact 结构中明确。
- **同步更新**：
  - [docs/specguard/design.md](../design.md) §3.1、§3.3、§5 增加 `hooks_merge.py` / `upgrade.py` 模块说明与测试项。
  - [docs/specguard/specs/distribution-and-auto-hooks-spec.md](../specs/distribution-and-auto-hooks-spec.md) ADR 识别节补充 ADR-0004。
  - [adapters/claude/manifest.yaml](../../../adapters/claude/manifest.yaml) 或 release workflow 需要保证 Python module 可被目标项目调用。
