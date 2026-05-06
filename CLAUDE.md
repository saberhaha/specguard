<!-- specguard:start -->
## SpecGuard governance rules

### Five non-negotiable laws
1. `docs/specguard/design.md` 是当前架构唯一真相；写代码前必须先读它。
2. 决策档案在 `docs/specguard/decisions/`；写新 ADR 前必须先查看既有 ADR。
3. 禁止新建 dated design 文件（如 `*-design.md`）；新切片写 `docs/specguard/specs/<topic>-spec.md`，架构变更直接更新 design.md。
4. ADR 只用于五类硬条件：接口语义、数据格式、跨模块依赖、外部依赖、推翻既有设计；其他默认不写。
5. 接口/数据结构/模块边界变更必须同步 `docs/specguard/design.md`；命中硬条件时还要写 ADR。


### ADR judgement checklist
对本次需求的每个改动点，逐条匹配五条硬条件：

- [ ] 是否改变了某个对外接口的输入/输出/失败语义/调用约束？
- [ ] 是否改变了某个文件格式、数据 schema、字段语义到不向前兼容？
- [ ] 是否新增/移除/反转了模块间依赖关系？
- [ ] 是否新增/替换/移除了第三方库、外部服务、子进程?
- [ ] 是否与 design.md 或既有 ADR 中明确陈述的约束冲突？

任意一条 yes → 候选 ADR。
所有都 no → 不写 ADR，但仍要判断是否需要同步 design.md。

候选 ADR 必须列给用户拍板，AI 不能单方面写架构 ADR。

输出格式（写入切片 spec 的"ADR 级别决策识别"节）：
- 改动点拆解（编号列表）
- 五条硬条件匹配表（表格化）
- 候选 ADR + 灰色地带（请用户拍板）
- 不需要 ADR 的改动点 + 理由


### design.md sync rules
- 接口、数据结构、模块边界变化 → 必须同步 `docs/specguard/design.md` 对应段落（默认动作，不询问）。
- 编辑 `docs/specguard/design.md` 后更新顶部 `Last verified against code` 字段为当前 commit hash。
- 不允许在 `docs/specguard/design.md` 中保留与代码不一致的陈述。
- mermaid 图与文字描述若不一致，文字为准，同步修图。
- 写 ADR 后，在 `docs/specguard/design.md` 对应章节末尾追加 `（见 ADR-NNNN）`，并在 `docs/specguard/decisions/README.md` 索引表加一行。
<!-- specguard:end -->
