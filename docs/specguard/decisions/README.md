# specguard ADR 索引

本目录记录 specguard 的架构决策。

## 当前 ADR

| 编号 | 标题 | 状态 | 关联 |
|---|---|---|---|
| [0001](0001-plugin-name-command-namespace.md) | 使用 plugin name 作为 Claude slash command 命名空间 | Accepted | spec §3、README、adapter plugin.json |

后续若出现以下情况新增 ADR：

1. 改变公开命令语义或命名
2. 改变核心目录/布局抽象
3. 引入外部依赖或 runtime
4. 改变 agent/layout adapter 边界
5. 推翻 [design.md](../design.md) 或已接受 ADR 的明确陈���

## 模板

后续创建 ADR 时复制 [TEMPLATE.md](TEMPLATE.md)。
