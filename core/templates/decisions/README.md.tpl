# 决策档案（Architecture Decision Records）

本目录沉淀 {{ project.name | default("项目") }} 的架构决策。

<!-- specguard:rules:start -->
## ADR 五类硬条件

只写以下五类决策：

1. 接口语义改变
2. 数据格式不兼容
3. 跨模块依赖关系改变
4. 外部依赖引入或替换
5. 推翻先前 design 或 ADR

不写 ADR：任务、实现细节、参数默认值、命名、首次实施既有设计。

## 命名规范

- `NNNN-kebab-case-slug.md`，4 位编号连续
- 例外：`README.md`、`TEMPLATE.md`

## 状态字段

- `Accepted` / `Superseded by ADR-NNNN` / `Deprecated`
<!-- specguard:rules:end -->

## ADR 索引

| 编号 | 标题 | 状态 | 关联 design 章节 |
|---|---|---|---|
