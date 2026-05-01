# specguard ADR 索引

本目录记录 specguard 的架构决策。

## 当前 ADR

| 编号 | 标题 | 状态 | 关联 |
|---|---|---|---|
| [0001](0001-plugin-name-command-namespace.md) | 使用 plugin name 作为 Claude slash command 命名空间 | Accepted | spec §3、README、adapter plugin.json |
| [0002](0002-init-auto-merge-hooks.md) | `/specguard:init` 自动合并 hooks 到 `.claude/settings.json` | Accepted | design §3.1、§3.2、§3.3、§4 |
| [0003](0003-distribution-via-github-release.md) | 通过 GitHub Release tarball 分发 Claude plugin | Accepted | design §2、§3.1、§3.3、§6 |
| [0004](0004-python-modules-for-runtime-algorithms.md) | 将 init hooks 合并与 upgrade marker 替换下沉为 Python 模块 | Accepted | design §3.1、§3.3、§5 |
| [0005](0005-delete-check-semantic-review-package.md) | 删除 `/specguard:check semantic` review package 模式 | Accepted | design §5.3、§8 |
| [0006](0006-tighten-upgrade-interaction-and-version-handling.md) | 收紧 `/specguard:upgrade` 写入前交互与缺版本行为 | Accepted | design §5.4、§6 |

后续若出现以下情况新增 ADR：

1. 改变公开命令语义或命名
2. 改变核心目录/布局抽象
3. 引入外部依赖或 runtime
4. 改变 agent/layout adapter 边界
5. 推翻 [design.md](../design.md) 或已接受 ADR 的明确陈述

## 模板

后续创建 ADR 时复制 [TEMPLATE.md](TEMPLATE.md)。
