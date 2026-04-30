1. `{{ paths.design }}` 是当前架构唯一真相；写代码前必须先读它。
2. 决策档案在 `{{ paths.decisions_dir }}/`；写新 ADR 前必须先查看既有 ADR。
3. 禁止新建 dated design 文件（如 `*-design.md`）；新切片写 `*-spec.md`，架构变更直接更新 design.md。
4. ADR 只用于五类硬条件：接口语义、数据格式、跨模块依赖、外部依赖、推翻既有设计；其他默认不写。
5. 接口/数据结构/模块边界变更必须同步 `{{ paths.design }}`；命中硬条件时还要写 ADR。
