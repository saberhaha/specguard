# v0.5.0 Hooks Pressure Tests — 实施 plan

> 对应 spec: [v0-5-0-hooks-pressure-tests-spec.md](../specs/v0-5-0-hooks-pressure-tests-spec.md)
> 模式：Subagent-Driven（main 分支直接提交）

**Goal**：把 4 个 specguard hook 的 shell 决策层升级为可重复 pytest（L1 层），不调真 Claude / 不烧 token。

**约束**：仅测试现状；hook shell 不动；大写 `.MD` 等已知边界用 pytest.mark 记录而不修改 hook。

---

## Task 1：ADR-0009 落档

**Files**
- Create: `docs/specguard/decisions/0009-hooks-pressure-tests.md`
- Modify: `docs/specguard/decisions/README.md`（索引追加 0009 行）

**ADR-0009 要点**
- 状态：Accepted
- 日期：2026-05-02
- 相关：ADR-0002（hooks 自动合并 — 状态保持 Accepted；本 ADR 不动 hooks 自动合并行为，只新增对 hooks shell 输出的 pytest 覆盖）
- 决策：5 个独立测试文件（每 hook 一个），从 rendered settings.json.snippet 提取 command 字段，用 subprocess sh -c 跑，断言 stdout JSON。L1 范围；模型采纳 context 行为留 L2。
- 替代方案：单文件 5 class（拒绝，文件粒度更清晰）；直接读模板字符串模板替换（拒绝，与 render 脱带）。
- 影响：design.md §6 不变量 8→9 条；§7.1 风险表 hooks 行 改写；§7.4 收紧未覆盖范围至模型行为；§8.1 移除 skill pressure tests 已实现条目、新增 L2 留位。

**Verify**：`ls docs/specguard/decisions/0009*` 存在；README 索引含 0009 行；ADR-0002 状态字段未变。

**Commit**：`docs(adr): add ADR-0009 hooks shell decision pressure tests`

---

## Task 2：测试 helper

**Files**
- Create: `tests/_hook_helpers.py`

**内容要点**
- `extract_hook_command(snippet: dict, event: str, status_message: str) -> str`：在 snippet["hooks"][event] 中按 `statusMessage` 找到 entry，返回 command 字符串。
- `run_hook_command(command: str, stdin_json: str = "{}", env: dict | None = None, cwd: Path | None = None) -> tuple[dict, str]`：subprocess.run sh -c command，输入 stdin_json，10s timeout，返回 `(parsed_stdout_dict, raw_stdout_text)`；空 stdout 返回 `({}, "")`；非合法 JSON 抛异常。

**Files**
- Modify: `tests/conftest.py`（如不存在则新建）

**内容要点**
- 模块级 fixture `rendered_snippet(tmp_path_factory)`：跑 `specguard.render.render(repo_root=REPO, target='claude', layout='specguard-default', out_dir=tmp_path_factory.mktemp('dist'))`，读 `dist/hooks/settings.json.snippet`，json.loads 后返回 dict；scope=session。

**Verify**：`uv run python -c "import tests._hook_helpers"` 不报错。

**Commit**（与 Task 3 合并提交，避免半成品）

---

## Task 3：5 个 hook 测试文件

按 spec §1.3 列出 5 个文件 + 25+ 用例。每个文件结构：

```python
import json
from tests._hook_helpers import extract_hook_command, run_hook_command


def test_<scenario>(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, "<event>", "<statusMessage>")
    out, _ = run_hook_command(cmd, stdin_json='<mock_json>')
    assert <expectation on out>
```

**5 个文件**（各文件用例与 spec 严格对应）：

### tests/test_hook_session_start.py
- `test_session_start_emits_five_laws`：空输入 `{}` → out["hookSpecificOutput"]["hookEventName"] == "SessionStart"；`additionalContext` 含五条法则关键词。
- `test_session_start_paths_substituted`：断言 `additionalContext` 含 `docs/specguard/design.md`、`docs/specguard/decisions`、无 `{{` 残留。

### tests/test_hook_pretooluse_dated_design.py
- `test_block_dated_design_at_specs_root`：`docs/specguard/specs/foo-design.md` → deny。
- `test_block_dated_design_in_subdir`：`docs/specguard/specs/v0/foo-design.md` → deny。
- `test_allow_spec_file`：`docs/specguard/specs/foo-spec.md` → `{}`。
- `test_allow_design_md_root`：`docs/specguard/design.md` → `{}`。
- `test_allow_other_path`：`src/foo.py` → `{}`。
- `test_known_limitation_uppercase_extension`：`docs/specguard/specs/foo-design.MD` → `{}`（pytest.mark.xfail(strict=True, reason="known: hook is case-sensitive, see ADR-0009")）— 用 strict=True 让若未来 hook 修了变 deny，测试 fail 提醒同步更新。

### tests/test_hook_pretooluse_adr_filename.py
- `test_allow_valid_adr_name`：`0001-foo.md` / `0042-multi-word.md` / `9999-z-z-z.md` → `{}`。
- `test_allow_readme_template`：`docs/specguard/decisions/README.md`、`docs/specguard/decisions/TEMPLATE.md` → `{}`。
- `test_deny_two_digit_number`：`docs/specguard/decisions/01-foo.md` → deny。
- `test_deny_three_digit_number`：`docs/specguard/decisions/001-foo.md` → deny。
- `test_deny_uppercase`：`docs/specguard/decisions/0001-FOO.md` → deny。
- `test_deny_space`：`docs/specguard/decisions/0001 foo.md` → deny。
- `test_deny_no_number`：`docs/specguard/decisions/foo.md` → deny。
- `test_allow_non_decisions_path`：`docs/specguard/specs/0001-foo.md`（不是 decisions/）→ `{}`。

### tests/test_hook_stop_design_sync.py
- 用 `tmp_path` 创建 git 临时 repo（pytest fixture），通过 monkeypatch 设 `CLAUDE_PROJECT_DIR=str(tmp_path)`：
  - `test_only_src_changed`：repo 中改 `src/foo.py` 后未 commit → 期望 systemMessage 含 "design.md nor decisions/"。
  - `test_src_and_design_changed`：同时改 `src/foo.py` + `docs/specguard/design.md` → `{}`。
  - `test_only_design_changed`：仅改 `docs/specguard/design.md` → `{}`。
  - `test_no_changes`：repo clean → `{}`。
  - `test_no_git_repo`：`CLAUDE_PROJECT_DIR=/nonexistent/abs/path` → 静默 exit（stdout 为空或 `{}`，不抛异常）。

### tests/test_hook_userprompt_adr.py
- `test_trigger_english_write_spec`：prompt key='prompt' value='please write spec for foo' → additionalContext。
- `test_trigger_english_write_plan`：'write plan now' → additionalContext。
- `test_trigger_english_implement_now`：'implement now' → additionalContext。
- `test_trigger_chinese_kaishi_shishi`：'开始实施' → additionalContext。
- `test_trigger_chinese_xie_spec`：'写 spec' → additionalContext。
- `test_trigger_chinese_xie_plan`：'写 plan' → additionalContext。
- `test_no_trigger_normal_chat`：'tell me about the design' → `{}`。
- `test_no_trigger_question`：'what does this hook do?' → `{}`。
- `test_trigger_in_middle_sentence`：'hey, please write a spec for the new feature' → additionalContext（grep -i 命中 'write spec'）。
- 注意：mock 用 `user_prompt` 与 `prompt` 双 key 都跑一遍（hook 同时支持两 key，spec 中已说明）。

**Verify**：`uv run pytest tests/test_hook_*.py -v` 全绿；总用例数 ≥ 25（实际目标 ~30）。

**Commit**：`feat(tests): add hook shell pressure tests for 5 events`

---

## Task 4：design.md / CHANGELOG 同步

**Files**
- Modify: `docs/specguard/design.md`：
  - §6 不变量 8→9 条，新增第 9 条（hooks shell 决策由 pytest 覆盖；模型采纳 context 行为留 L2）
  - §7.1 风险表：hooks 行改写为 "hooks shell 决策 / governance 触发词覆盖率 → tests/test_hook_*.py"；新增风险 "hooks shell 通过但模型忽略 additionalContext / systemMessage"，缓解 "L2 真 Claude 端到端验证延后"
  - §7.2 改动类型表：新增 "hooks settings.json.snippet 修改 → tests/test_hook_*.py"
  - §7.3 dogfood：去掉对 hooks shell 行为的人工 dogfood 责任；新增 v0.5.0 dogfood 占位（待 release 后回填）
  - §7.4 未覆盖：把"hooks 实际行为"改写为"模型实际是否消化 SessionStart additionalContext / UserPromptSubmit additionalContext / Stop systemMessage"
  - §8.1 v0.5+ 留位：移除"skill pressure tests"项；新增"L2 真 Claude 端到端 hook 触发验证"
  - 顶部 `Last verified against code`（占位，Task 7 后回填）

- Modify: `CHANGELOG.md`：顶部新增 `## v0.5.0 - 2026-05-02` 段：
  - Added: 5 个 hook 测试文件、`tests/_hook_helpers.py`、模块级 rendered_snippet fixture
  - Changed: design.md §6/§7.1/§7.4 收紧 hooks 覆盖边界
  - Notes: 大写扩展名等已知边界用 pytest.mark.xfail 固化；L2 真 Claude 端到端测试延后

**Verify**：`grep -c "hook_session_start\|hook_pretooluse\|hook_stop\|hook_userprompt" docs/specguard/design.md` ≥ 1；`head -20 CHANGELOG.md` 含 `## v0.5.0`。

**Commit**：`docs: sync design.md / CHANGELOG for v0.5.0 hook pressure tests`

---

## Task 5：版本 bump v0.5.0

**Files**
- Modify: `core/version` → `0.5.0`
- Modify: `pyproject.toml.project.version` → `0.5.0`
- Modify: `uv.lock`（`uv lock` 同步）
- Modify: `tests/test_release_workflow.py`：`test_core_version_is_v0_4_0` 改名 `test_core_version_is_v0_5_0`、断言 `0.5.0`
- Re-render：跑 `uv run specguard-render --target claude --layout <X> --out plugins/<X>` 三个 layout，让 plugins/<layout>/.claude-plugin/plugin.json.version → 0.5.0

**Verify**：`jq -r .version plugins/specguard-default/.claude-plugin/plugin.json` == `0.5.0`；`uv run pytest` 全绿（≥ 67 个 test）。

**Commit**：`chore(release): bump to v0.5.0`

---

## Task 6：push + tag

**Steps**
1. `git push origin main`（推 Task 1-5 所有 commit）
2. `git tag v0.5.0 && git push origin v0.5.0`
3. 等 release.yml 完成；确认 main 上多出 `chore(release): render plugins for v0.5.0` commit；GH Release v0.5.0 含三个 tarball

**Verify**：GH Release v0.5.0 含 3 tarball；main 末尾 commit message 含 "render plugins for v0.5.0"；`git pull origin main` 后 `jq -r .version plugins/specguard-default/.claude-plugin/plugin.json` == `0.5.0`。

---

## Task 7：spot-check dogfood + 回填

**Steps**
1. `git pull origin main` 拉 CI 自动 push 的 chore(release) commit
2. 在 `/tmp/sg-dog-v050/specguard-default/repo` 临时 git repo 跑 `claude --plugin-dir <unpacked tarball> -p '/specguard:init --ai claude --spec none'`
3. 检查 `.claude/settings.json` 含 5 个 specguard hook entry（grep `specguard:`）
4. 手动触发一次 dated design block：开 Claude session，让它 Write `docs/specguard/specs/foo-design.md`，确认实际被 deny（错误信息含 "specguard: dated design files are forbidden"）
5. 回填 design.md 顶部 `Last verified against code` short hash + §7.3 v0.5.0 dogfood 记录
6. `git commit + git push origin main`

**Verify**：design.md §7.3 含 v0.5.0 条目（spot-check 描述 + 一个 dated design block 的实际触发证据）；顶部 hash = main HEAD。

---

## Self-review

- [x] 每个 task 都列文件 + 改动 + verify + commit message
- [x] 没有占位
- [x] Task 5 re-render 与 Task 3 测试不冲突（plugins/<layout>/ 内嵌 plugin.json.version 改变，rendered_snippet fixture 用同 render 流程，版本变化不影响 hooks 内容）
- [x] dogfood spot-check 范围明确（init + hooks merge + 1 个 deny case）
- [x] 与 spec §1 包含 7 条改动一一对应
