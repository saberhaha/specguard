# specguard

> AI 辅助开发的项目治理脚手架。通过 Claude Code 的 hooks、slash commands 和 CLAUDE.md 注入，强制 AI 辅助开发遵循 living design / ADR / spec 纪律。

specguard 的定位：

- 当前只支持 Claude Code；Cursor / Codex adapter 未实现
- spec 工具中立（兼容 OpenSpec、Superpowers 或不用任何 spec 工具）
- 以脚手架方式交付（`/specguard:init`），不是日常 CLI

## 快速开始（用户）

在目标项目目录下运行（需要 curl 和 sh）：

```bash
curl -fsSL https://raw.githubusercontent.com/saberhaha/specguard/main/install.sh | sh
```

或者先下载再运行（指定 layout）：

```bash
curl -fsSL https://raw.githubusercontent.com/saberhaha/specguard/main/install.sh -o install.sh
sh install.sh specguard-default   # 可选：specguard-default / specguard-superpowers / specguard-openspec-sidecar
```

安装完成后脚本会打印 init 命令，在目标项目（git 仓库）里执行即可：

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default \
  -p '/specguard:init --ai claude --spec none'
```

随时运行治理检查：

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default \
  -p '/specguard:check'
```

可用 layout：
- `specguard-default` — design/ADR/spec 放在 `docs/specguard/`
- `specguard-superpowers` — design/ADR/spec 放在 `docs/superpowers/`
- `specguard-openspec-sidecar` — design/ADR 放在 `docs/specguard/`，specs 放在 `openspec/`

## 为什么做 specguard

OpenSpec / Spec Kit / Superpowers 专注于驱动单次 AI 编码会话。specguard 关注的是更底层的一层：

- 确保每次新对话都能读到当前架构
- 防止 AI 重新打开已决策的问题
- 在写计划前强制做 ADR 判断
- 发现代码与设计的漂移

它不是 spec 驱动开发工具的替代品，而是**架在这些工具之上的治理层**。

## 当前状态

| 项目 | 状态 |
|---|---|
| Claude Code 插件（tarball 安装） | 可用 |
| Cursor / Codex 适配器 | 未实现 |

## 开发

从源码构建插件用于本地 dogfood：

```bash
git clone https://github.com/saberhaha/specguard.git
cd specguard
uv sync
uv run pytest
uv run specguard-render --target claude --layout specguard-default --out dist/claude/specguard-default
claude --plugin-dir dist/claude/specguard-default -p '/specguard:init --ai claude --spec none'
```

参考：
- [docs/specguard/design.md](docs/specguard/design.md) — 活架构文档
- [docs/specguard/decisions/](docs/specguard/decisions/) — 架构决策记录
- [docs/specguard/specs/](docs/specguard/specs/) — 实施切片 spec
