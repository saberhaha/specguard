# ADR 0012: CLI-first 方案——以 `specguard` CLI 替代 slash command

**状态**：Accepted
**日期**：2026-05-07
**拍板者**：用户（@saber，2026-05-07）
**取代**：—
**相关**：
- ADR-0004（hooks_merge.py 保留，调用方从 init prompt 改为 CLI）
- ADR-0011（tarball 分发保留，install.sh 改为安装 CLI）

## Context

ADR-0011 以 `install.sh` 替代了 marketplace 分发，但 slash command（`/specguard:init` / `/specguard:check`）仍依赖 Claude Code plugin runtime 在运行时暴露 `CLAUDE_PLUGIN_ROOT` 环境变量。v0.4.0 dogfood（Claude Code v2.1.123）已确认该 env 在 marketplace 安装路径下不暴露，hooks 合并步骤无法完成——核心功能缺失。

`--plugin-dir` 方式可绕过 marketplace，但要求用户每次启动 claude 时手动附加参数，侵入正常使用体验，不可接受。

参考 OpenSpec 路径（`npm install -g` + `openspec init`）：CLI 工具完全不依赖 AI runtime，直接在项目目录写文件，用户体验简洁、可进 CI。specguard 现有 Python 代码（`hooks_merge.py` / `manifest.py` / `render.py`）已具备全部能力，缺少的只是一个 CLI 入口。

## Decision

1. 新增 `src/specguard/cli.py`，基于 `click` 提供 `specguard init` 和 `specguard check` 两个子命令。
2. `specguard init [--layout] [--ai] [--spec] [--dry-run]`：读 layout manifest → 创建 scaffold 文件 → 更新 CLAUDE.md block → 调用 `hooks_merge` 合并 hooks；完全不依赖 `CLAUDE_PLUGIN_ROOT`。
3. `specguard check [--layout]`：Python 实现 11 项结构检查；`errors > 0` 时 `exit 1`。
4. `pyproject.toml` 新增 `click>=8.0` 依赖；新增 entry point `specguard = "specguard.cli:main"`。
5. 删除 `core/command-prompts/init.md`、`core/command-prompts/check.md`、`adapters/claude/plugin/commands/` 目录、`adapters/claude/plugin/skills/` 目录。
6. `install.sh` 改为下载 Python sdist → `pip install`；`release.yml` 改出 Python sdist（`uv build`）。
7. hooks（4 个 shell 脚本注入 `.claude/settings.json`）继续保留，是 specguard 核心价值；触发方式从"slash command 调 Python runtime"改为"CLI 直接调 Python"。

## Consequences

- **正面**：
  - 用户安装后直接运行 `specguard init`，无需 `--plugin-dir`，不依赖 Claude Code plugin runtime。
  - `specguard check` 可进 CI，退出码语义明确（`exit 1` 表示检查失败）。
  - 消除对 `CLAUDE_PLUGIN_ROOT` 上游 bug 的依赖，核心功能恢复正常工作。
- **负面**：
  - 用户需要 Python 环境（`pip install`）；不再有 slash command 的"对话内随手调用"体验。
- **同步更新**：
  - `docs/specguard/design.md`：§1 / §2 / §3 / §5 / §8 更新分发方式与模块边界描述；顶部 `Last verified against code` 更新。
  - `pyproject.toml`：新增 `click>=8.0` 依赖及 entry point。
  - `install.sh`：改为 pip 安装流程。
  - `.github/workflows/release.yml`：改出 Python sdist。
  - `README`：更新安装与使用说明。
  - `CHANGELOG`：记录 v0.7.0 breaking change。
  - `docs/specguard/decisions/README.md`：索引追加 0012 行。
- **已拒绝替代方案**：
  - 修复 `CLAUDE_PLUGIN_ROOT` 暴露问题：属于上游 Claude Code bug，不在 specguard 控制范围，拒绝。
  - slash command 与 CLI 并存：增加维护成本，两套逻辑容易漂移，拒绝。
