# v0.7.0 CLI-first 实施 plan

> 对应 spec: [v0-7-0-cli-first-spec.md](../specs/v0-7-0-cli-first-spec.md)
> 模式：main 分支直接提交

**Goal**：`specguard init` / `specguard check` 替代 slash command；删除 commands + skill；install.sh 安装 Python CLI。

---

## Task 1：ADR-0012 落档

**Files**
- Create: `docs/specguard/decisions/0012-cli-first.md`
- Modify: `docs/specguard/decisions/README.md`（索引追加 0012 行）

**ADR-0012 要点**
- 状态：Accepted；日期：2026-05-07
- 相关：ADR-0004（hooks_merge.py 保留，调用方从 init prompt 改为 CLI）；ADR-0011（tarball 分发保留，install.sh 改为安装 CLI）
- 决策：新增 `src/specguard/cli.py`，`specguard init` 直接写文件 + 合并 hooks；`specguard check` 实现 11 项检查 + exit code；删除 slash commands + design-governance skill；`install.sh` 改为 `pip install`
- 理由：slash command 依赖 `CLAUDE_PLUGIN_ROOT`，Claude Code marketplace 路径不暴露该 env；`--plugin-dir` 入侵用户使用体验；CLI 工具（参考 OpenSpec）不依赖任何 AI runtime

**Verify**：文件存在；README 含 0012 行。

**Commit**：`docs(adr): add ADR-0012 CLI-first approach`

---

## Task 2：新增 `src/specguard/cli.py`

**Files**
- Create: `src/specguard/cli.py`

**实现要点**

```python
import click
from pathlib import Path
from .manifest import LayoutManifest
from .hooks_merge import merge_hooks_file
# ... scaffold 写文件逻辑
```

**`specguard init` 子命令**：
- 参数：`--layout specguard-default`、`--ai claude`、`--spec none`、`--dry-run`
- 从 `layouts/<layout>/manifest.yaml` 读 paths
- 创建缺失文件（design.md 模板、decisions/README.md、decisions/TEMPLATE.md、specs/TEMPLATE.md）；已存在则跳过并报告
- 更�� CLAUDE.md specguard block（`<!-- specguard:start/end -->`），不存在则新建
- 调用 `merge_hooks_file(settings_path, snippet_path)` 合并 hooks
- hooks snippet 从 `adapters/claude/plugin/hooks/settings.json.snippet.tpl` 渲染后写入临时文件
- `--dry-run` 打印计划，不写文件
- 打印结构化报告：Created / Updated / Skipped

**`specguard check` 子命令**：
- 参数：`--layout specguard-default`
- 实现 11 项检查（直接翻译 `core/command-prompts/check.md` 的逻辑为 Python）
- 输出 `✓ / ⚠️ / ❌` 格式
- exit 1 if errors > 0，else exit 0

**Verify**：
```bash
cd /tmp && git init test-cli && cd test-cli
uv run specguard init --layout specguard-default --ai claude --spec none
ls docs/specguard/design.md docs/specguard/decisions/README.md CLAUDE.md
cat .claude/settings.json | grep specguard
uv run specguard check
```

**Commit**（与 Task 3 合并）

---

## Task 3：pyproject.toml + 测试

**Files**
- Modify: `pyproject.toml`（新增 `click>=8.0` 依赖；新增 entry point `specguard = "specguard.cli:main"`）
- Create: `tests/test_cli.py`

**test_cli.py 用例**：
```python
from click.testing import CliRunner
from specguard.cli import main

def test_init_creates_scaffold(tmp_path):
    # git init + specguard init -> 断言文件存在
    
def test_init_dry_run_no_writes(tmp_path):
    # --dry-run 后文件不存在

def test_init_merges_hooks(tmp_path):
    # settings.json 含 specguard: hooks

def test_check_passes_after_init(tmp_path):
    # init 后 check exit 0

def test_check_fails_missing_design(tmp_path):
    # 无 design.md，check exit 1

def test_check_fails_missing_hooks(tmp_path):
    # settings.json 无 specguard hooks，check exit 1
```

**Verify**：`uv sync && uv run pytest tests/test_cli.py -v` 全绿。

**Commit**：`feat: add specguard CLI (init + check commands)`

---

## Task 4：删除 slash commands + skill

**Files（git rm）**
- `core/command-prompts/init.md`
- `core/command-prompts/check.md`
- `adapters/claude/plugin/commands/init.md.tpl`
- `adapters/claude/plugin/commands/check.md.tpl`
- `adapters/claude/plugin/skills/` 目录（含 SKILL.md.tpl）
- `adapters/claude/plugin/manifest.yaml`（如存在）

**Modify**：`adapters/claude/manifest.yaml`：删除 commands + skills render 条目；只保留 hooks snippet render。

**Verify**：`ls adapters/claude/plugin/commands/` 为空或目录不存在；`ls adapters/claude/plugin/skills/` 不存在；`uv run specguard-render --target claude --layout specguard-default --out /tmp/sg-render-check` 不报错（只 render hooks snippet）；`ls /tmp/sg-render-check/` 只含 hooks/。

**Commit**：`feat!: remove slash commands and design-governance skill`

---

## Task 5：修改 install.sh + release.yml

**Files**
- Modify: `install.sh`（改为下载 Python sdist → pip install → 打印 `specguard init` 提示）
- Modify: `.github/workflows/release.yml`（新增 `uv build` 步骤；release assets 改为 Python sdist）

**install.sh 新逻辑**：
```sh
#!/usr/bin/env sh
set -e
VERSION=$(curl -s https://api.github.com/repos/saberhaha/specguard/releases/latest \
  | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
TMPDIR=$(mktemp -d)
curl -L "https://github.com/saberhaha/specguard/releases/latest/download/specguard-${VERSION}.tar.gz" \
  | tar -xz -C "$TMPDIR"
pip install --quiet "$TMPDIR/specguard-${VERSION}"
rm -rf "$TMPDIR"
echo "specguard v${VERSION} 已安装。"
echo "在目标项目（git 仓库）里运行："
echo "  specguard init"
```

**release.yml 新增步骤**（在 pytest 之后）：
```yaml
- name: Build Python package
  run: uv build --out-dir release/
```

上传 `release/*.tar.gz`（现在包含 Python sdist，不再有 plugin tarballs）。

**Verify**：`sh -n install.sh` 无语法错误；release.yml 含 `uv build`。

**Commit**：`feat: update install.sh to pip install CLI; release sdist`

---

## Task 6：bump 版本 + 测试修订 + design.md / README / CHANGELOG

**Files**
- `core/version` → `0.7.0`
- `pyproject.toml` version → `0.7.0`
- `uv lock`
- `tests/test_release_workflow.py`：版本断言改为 `0.7.0`；删除或更新已失效的 render 断言
- `tests/test_render_claude_default.py`：删除 commands/skill 相关断言（init_command_* / check_command_* / skill_*）
- `tests/test_render_basic.py`：更新 render 产出预期（不再有 commands/，只有 hooks/）
- `docs/specguard/design.md`：按 spec §"对 design.md 的影响"更新
- `README.md`：quickstart 改为 `sh install.sh` → `specguard init`
- `CHANGELOG.md`：新增 v0.7.0 段（BREAKING：slash commands 删除）

**Verify**：`uv run pytest` 全绿；`head -5 CHANGELOG.md` 含 v0.7.0。

**Commit**：`chore!: bump to v0.7.0; sync docs and tests for CLI-first`

---

## Task 7：push + tag + 验证

1. `git push origin main`
2. `git tag v0.7.0 && git push origin v0.7.0`
3. 等 release.yml 完成；确认 GH Release v0.7.0 含 Python sdist
4. `sh install.sh` 验证安装成功；`specguard --version` 可运行
5. 在临时 git repo 跑 `specguard init` → `specguard check` 验证全流程
6. 回填 design.md `Last verified against code` hash

---

## Self-review

- [x] Task 2 CLI 的 hooks snippet 来源需要确认：`adapters/claude/plugin/hooks/settings.json.snippet.tpl` 是 Jinja 模板，需要 render 才能用。CLI 应该 render 它（传入 layout paths），不能直接读模板文本。
- [x] Task 4 删 slash commands 后，`test_render_claude_default.py` 里 commands 相关断言全部失效，Task 6 必须同步删除这些测试。
- [x] Task 5 release.yml 删掉三个 layout plugin tarball 的构建（不再需要 plugin，只需 Python sdist）。
- [x] `check.md` 的 11 项检查现在要翻译成 Python 代码——这是 Task 2 里工作量最大的部分，确保 paths 从 layout manifest 读而不是硬编码。
- [x] Task 7 dogfood 前需要确认 `pip install` 后 `specguard` 命令在 PATH 里。
