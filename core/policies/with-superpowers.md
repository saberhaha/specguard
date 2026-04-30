## 与 superpowers 协作

如当前项目使用 superpowers skills，建议：

1. 设计探索阶段优先调用 `superpowers:brainstorming`。
2. 计划阶段优先调用 `superpowers:writing-plans`。
3. 实施阶段可使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`。

但以下规则**始终**优先于 superpowers 默认行为：

- 禁止新建 `{{ paths.specs_dir }}/*-design.md`。新切片用 `*-spec.md`。
- spec 必须包含 `## ADR 级别决策识别` 节。
- 进入 plan 之前必须由用户拍板候选 ADR。
- 实施过程中接口/数据/边界变更必须同步 `{{ paths.design }}`。
