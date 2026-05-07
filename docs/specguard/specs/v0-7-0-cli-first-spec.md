# v0-7-0-cli-first 设计

**日期**：2026-05-07
**适用范围**：v0.7.0：以独立 CLI（`specguard init` / `specguard check`）替代 Claude Code slash command。CLI 直接写文件 + 合并 hooks，不依赖 Claude Code plugin runtime。删除 slash commands 和 design-governance skill。`install.sh` 改为安装 Python CLI。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 新增 `src/specguard/cli.py`：`specguard init` 子命令（`--layout`、`--ai`、`--spec`、`--dry-run`）+ `specguard check` 子命令（exit code 0/1）。复用现有 `hooks_merge.py`、`manifest.py`、`render.py` 逻辑。
2. `pyproject.toml`：新增 `click` 依赖；新增 entry point `specguard = "specguard.cli:main"`。
3. 删除 Claude Code slash command 相关文件：`core/command-prompts/init.md`、`core/command-prompts/check.md`、`adapters/claude/plugin/commands/init.md.tpl`、`adapters/claude/plugin/commands/check.md.tpl`、`adapters/claude/plugin/skills/design-governance/SKILL.md.tpl`；`adapters/claude/manifest.yaml` 删 commands + skills render 条目。
4. `install.sh` 改写：下载 tarball → 解压 → 从解压目录 `pip install --quiet .`（wheel 已包含在 tarball 中）或用 `uv tool install` → 打印"现在在项目里跑 `specguard init`"。
5. release.yml：tarball 除了现有的 rendered plugin 文件，还需打包 Python wheel（`uv build`）；或直接在 tarball 根目录包含 `pyproject.toml` + `src/` 让用户 `pip install`。
6. 同步 design.md / README / CHANGELOG；bump `core/version` → `0.7.0`。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 新增 cli.py | ✓ | - | ✓ | - | ✓ |
| #2 新增 click 依赖 + entry point | - | - | - | ✓ | - |
| #3 删�� slash commands + skill | ✓ | - | ✓ | - | ✓ |
| #4 install.sh 改写 | ✓ | - | - | - | ✓ |
| #5 release tarball 含可安装包 | - | ✓ | - | - | ✓ |
| #6 文档/版本同步 | - | - | - | - | - |

### 候选 ADR（已拍板）

**ADR-0012：以独立 CLI 替代 Claude Code slash command**

覆盖改动 #1-#5。全部五条硬条件均命中。

关键陈述：
- slash command 依赖 `CLAUDE_PLUGIN_ROOT` 暴露（Claude Code plugin runtime），Claude Code v2.1.123 marketplace 安装路径不暴露该 env，导致 hooks 合并失败；`--plugin-dir` 方式则要求用户每次启动 claude 时手动加参数，严重入侵使用体验。
- CLI 工具（参考 OpenSpec：`npm install -g @fission-ai/openspec` → `openspec init`）直接用 Python 实现，`specguard init` 在目标项目里直接写文件 + 合并 hooks，完全不依赖 Claude Code runtime。
- hooks（4 个 shell 脚本注入 `.claude/settings.json`）是 specguard 核心价值，继续保留；只是触发方式从"slash command 调 Python runtime"改为"CLI 直接调 Python"。
- design-governance skill 也依赖 plugin 机制，同步删除。

取代：—（无先前 ADR 涵盖 CLI 方式）
相关：ADR-0001（plugin name/command namespace — 命令方式改变，但 ADR-0001 只说 plugin name 不动，本 ADR 说命令从 slash 改为 CLI，不冲突）；ADR-0004（Python modules for runtime — `hooks_merge.py` 保留，只是调用方从 init prompt 改为 CLI）；ADR-0011（install.sh — 继续沿用 tarball 分发，install.sh 改为安装 CLI 而不只是解压）

### 不需要 ADR

- #6：文档 / 版本 bump，执行已确定方向。

## 对 design.md 的影响

- §1 产品定位：将"通过 Claude Code 的 hooks、slash commands 和 CLAUDE.md 注入"改为"通过 CLI（`specguard init` / `specguard check`）和 Claude hooks"；删除"Claude Code 插件形式"的描述。
- §2：删 Init flow Mermaid（由 CLI 替代，不再是 Claude prompt 流程）；Check flow Mermaid 也删（改为 CLI）；Build/Release flow Mermaid 更新（tarball 包含可安装 Python 包）。
- §3：§3.3 adapters/claude 删除 commands/skills 描述（只保留 hooks snippet）；§3.4 src/specguard 增加 `cli.py` 描述。
- §4 数据契约：保持 7 条不变（CLI 不引入新的数据契约，现有 CLAUDE.md block / hooks / ADR 文件名等契约继续有效）。
- §5 命令语义：§5.1 `/specguard:init` → `specguard init CLI`；§5.2 `/specguard:check` → `specguard check CLI`；重写为 CLI 参数/行为语义。
- §6 不变量：不变（所有不变量在 CLI 模式下仍成立）。
- §7 测试策略：§7.2 改动类型表新增"cli.py 修改 → pytest tests/test_cli.py"。
- §8 不在范围：删"非 Claude agent runtime：当前只支持 Claude Code"（CLI 不依赖 agent）。

## 1. 切片范围

**包含**

1. ADR-0012 落档；`decisions/README.md` 索引追加 0012 行。

2. 新增 `src/specguard/cli.py`：
   - `specguard init [--layout <layout>] [--ai <claude|cursor|codex|generic|auto>] [--spec <none|openspec|superpowers|auto>] [--dry-run]`
     - `--layout` 默认 `specguard-default`，可选 `superpowers` / `openspec-sidecar`
     - 读取对应 layout manifest 获取 paths
     - 创建缺失的 scaffold 文件（design.md 模板、decisions/README.md、decisions/TEMPLATE.md、specs/TEMPLATE.md）
     - 更新 CLAUDE.md specguard block（`<!-- specguard:start -->` / `<!-- specguard:end -->`）
     - 调用 `hooks_merge.merge_hooks_file()` 合并 hooks 到 `.claude/settings.json`
     - `--dry-run` 打印计划操作，不写文件
   - `specguard check [--layout <layout>]`
     - 实现 check.md 里的 11 项结构检查
     - 输出 ✓ / ⚠️ / ❌ 格式报告
     - errors > 0 时 exit 1，否则 exit 0

3. 修改 `pyproject.toml`：
   - 新增依赖 `click>=8.0`
   - 新增 entry point `specguard = "specguard.cli:main"`

4. 删除 slash command 相关文件（git rm）：
   - `core/command-prompts/init.md`
   - `core/command-prompts/check.md`
   - `adapters/claude/plugin/commands/init.md.tpl`
   - `adapters/claude/plugin/commands/check.md.tpl`
   - `adapters/claude/plugin/skills/design-governance/SKILL.md.tpl`
   - `adapters/claude/plugin/skills/design-governance/` 目录
   - `adapters/claude/plugin/manifest.yaml`（plugin-level，不是 adapter manifest）如存在

5. 修改 `adapters/claude/manifest.yaml`：删除 commands + skills render 条目；只保留 hooks snippet render。

6. 修改 `install.sh`：
   ```sh
   #!/usr/bin/env sh
   set -e
   VERSION=$(curl -s https://api.github.com/repos/saberhaha/specguard/releases/latest \
     | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
   TMPDIR=$(mktemp -d)
   curl -L "https://github.com/saberhaha/specguard/releases/latest/download/specguard-v${VERSION}.tar.gz" \
     | tar -xz -C "$TMPDIR"
   pip install --quiet "$TMPDIR/specguard-${VERSION}"
   rm -rf "$TMPDIR"
   echo ""
   echo "specguard v${VERSION} installed."
   echo ""
   echo "在目标项目（git 仓库）里初始化治理脚手架："
   echo "  specguard init"
   echo ""
   echo "随时运行治理检查："
   echo "  specguard check"
   ```

7. 修改 `release.yml`：
   - 新增 `uv build` 步骤，生成 `dist/specguard-X.Y.Z.tar.gz`（Python sdist，不同于 plugin tarball）
   - release assets 新增这个 Python package tarball
   - 删除或保留三个 layout tarball（plugin tarball 现在只含 hooks snippet，install.sh 不再需要它）——**建议直接删除三个 layout tarball**，改为只发 Python package tarball；用户 `pip install` 后 hooks snippet 从 Python 包里读。

8. 新增 `tests/test_cli.py`：
   - `test_init_creates_scaffold`：在 tmp_path 临时 git repo 跑 `specguard init`，断言文件被创建
   - `test_init_dry_run_no_writes`：`--dry-run` 不写文件
   - `test_init_merges_hooks`：`.claude/settings.json` 含 `specguard:` hooks
   - `test_check_passes_on_fresh_init`：init 后 check 返回 exit 0
   - `test_check_fails_missing_design`：无 design.md 时 check 返回 exit 1
   - `test_check_fails_missing_hooks`：settings.json 无 specguard hooks 时 check 返回 exit 1

9. 同步 `docs/specguard/design.md`（见上节）；更新 `README.md` quickstart 为 `pip install` 或 `install.sh` → `specguard init`；`CHANGELOG.md` 新增 v0.7.0 段；bump `core/version` → `0.7.0`。

**不包含**

- PyPI 发布（`pip install specguard` 从 PyPI 装）：留到后续切片。
- `specguard update` 命令（自动检查新版本）：留到后续。
- Cursor / Codex adapter。
- hooks snippet 在 CLI 里的嵌入方式（当前从 layout manifest 旁边的 tpl 文件读；CLI 需要打包进去——本切片先从 `src/specguard/templates/` 或 `adapters/claude/plugin/hooks/` 读，不改 hook 内容本身）。

## 2. 验收标准

1. **ADR-0012 落档**：`docs/specguard/decisions/0012-cli-first.md` 存在；索引含 0012 行。

2. **CLI 可用**：`specguard init` 在临时 git repo 创建完整 scaffold（design.md / decisions / specs / CLAUDE.md block）并合并 hooks；`specguard check` 在 init 后返回 exit 0，缺失 design.md 时返回 exit 1；`specguard --help` 打印帮助；`uv run pytest tests/test_cli.py` 全绿。

3. **slash commands + skill 已删除**：`core/command-prompts/` 无 init.md / check.md；`adapters/claude/plugin/commands/` 无 tpl 文件；`adapters/claude/plugin/skills/` 不存在或为空；`uv run pytest` 全绿（旧 render 测试中关于 commands/skill 的断言已同步删除）。

4. **install.sh 安装 CLI**：`sh install.sh` 后 `specguard --version` 可运行；不再需要 `--plugin-dir`。

5. **v0.7.0 已发布**：`core/version` = `0.7.0`；release assets 含 Python sdist；`specguard init` + `specguard check` 在真实 git 项目跑通。

## 3. 留给后续切片

- PyPI 发布（`pip install specguard`）。
- `specguard update` 自检新版本。
- Cursor / Codex adapter。
- design-governance skill 以 specguard CLI 结果为基础重建（不依赖 plugin runtime）。
