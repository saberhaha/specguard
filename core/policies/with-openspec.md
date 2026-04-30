## 与 OpenSpec 协作

OpenSpec 仍按其本身流程使用：proposal / change / archive 在 `openspec/`。
specguard 仅补充以下治理约束：

1. 写 OpenSpec proposal 前，先读 `{{ paths.design }}` + `{{ paths.decisions_dir }}/`。
2. OpenSpec proposal 的 `design.md` 若产生 ADR 级别决策，必须新增 ADR 到 `{{ paths.decisions_dir }}/`。
3. OpenSpec change archive 后，若改变当前架构，必须同步 `{{ paths.design }}`。
4. 长期架构决策不得只留在 `openspec/changes/archive/`，必须沉淀到 ADR。
