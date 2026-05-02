# v0-5-0-hooks-pressure-tests 设计

**日期**：2026-05-02
**适用范围**：v0.5.0：把 4 个 specguard hook（SessionStart / PreToolUse:Write 两个 / Stop / UserPromptSubmit）的 shell 决策行为升级为可重复的自动化压力测试。仅 L1 层（mock JSON 输入 → expected JSON 输出），不调真 Claude CLI、不烧 token、CI 可跑。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 新增 5 个 pytest 测试文件（每 hook 一个）：
   - `tests/test_hook_session_start.py`
   - `tests/test_hook_pretooluse_dated_design.py`
   - `tests/test_hook_pretooluse_adr_filename.py`
   - `tests/test_hook_stop_design_sync.py`
   - `tests/test_hook_userprompt_adr.py`
2. 新增公共 fixture / helper（最小复用，不强行抽抽象）：
   - `tests/conftest.py` 或 `tests/_hook_helpers.py`：从 rendered `hooks/settings.json.snippet` 提取指定 hook command 字段；通过 `subprocess.run(['sh', '-c', cmd], input=mock_json, capture_output=True)` 跑脚本；解析 stdout JSON 返回断言对象。
   - render 一次缓存到 `tmp_path` 模块级 fixture，避免 5 文件各 render。
3. 修改 `docs/specguard/design.md`：§6 不变量、§7.1 风险表、§7.4 未覆盖风险段同步——把"hooks 实际行为只能通过人工 dogfood 验证"这一条收紧为"hooks shell 决策由 pytest 强制；模型采纳 governance laws 仍需人工 dogfood"。
4. 修改 `CHANGELOG.md`：v0.5.0 段，列出 5 个 hook pressure test 文件 + 测试矩阵覆盖范围。
5. bump 版本：`core/version` → `0.5.0`、`pyproject.toml` → `0.5.0`、`uv.lock`、`tests/test_release_workflow.py::test_core_version_is_v0_4_0` 改名 + 改值。
6. 新版本 release：CI 自动 render + commit `plugins/<layout>/`（plugin.json.version 自动到 0.5.0）+ tarball；推送 `v0.5.0` tag。
7. dogfood：跑 `uv run pytest` 全绿；release 后从 tarball 在临时 git repo 跑 `/specguard:init` + `/specguard:check` 确认 5 个 hook 实际触发与 pytest 断言一致；结果写入 design §7.3。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 5 个 hook pressure test 文件 | - | - | - | - | ✓ |
| #2 测试 helper（subprocess + rendered snippet） | - | - | ✓ | - | - |
| #3 design.md §6/§7.1/§7.4 同步 | - | - | - | - | ✓ |
| #4 CHANGELOG 同步 | - | - | - | - | - |
| #5 版本 bump 0.5.0 | - | - | - | - | - |
| #6 release | - | - | - | - | - |
| #7 dogfood | - | - | - | - | - |

### 候选 ADR（请用户拍板）

- **ADR-0009：把 hooks shell 决策从"必须人工 dogfood"升级为 pytest 强制**

  覆盖改动 #1–#3。命中跨模块依赖 + 推翻先前设计。

  关键陈述：
  - 当前 design §7.4 把 hooks 真实行为列为"未覆盖风险，需人工 dogfood"。这条边界对 4 个 hook 的 **shell 决策层**过宽——shell 输入输出确定，可用 subprocess 完全覆盖。
  - 不可覆盖的部分（模型是否采纳 SessionStart additionalContext、UserPromptSubmit additionalContext 是否真的让模型执行 ADR judgement、Stop systemMessage 是否被模型注意）保留在人工 dogfood 范围。
  - 测试覆盖矩阵：
    - **SessionStart**：发出的 JSON 含 5 条 governance laws 全文、events name 正确。
    - **PreToolUse:Write dated design**：写 `<specs_dir>/foo-design.md` 必 deny；写 `<specs_dir>/sub/foo-design.md` 嵌套路径必 deny；写 `<specs_dir>/foo-spec.md` 必 `{}`；写 `<specs_dir>/foo-design.MD` 大小写边界（当前 case 不命中，记录已知漏洞）；写 `docs/other/foo-design.md` 必 `{}`。
    - **PreToolUse:Write adr filename**：合法 `0001-foo.md` / `README.md` / `TEMPLATE.md` / `0042-multi-word-name.md` 必 `{}`；非法 `foo.md` / `01-foo.md`（3 位编号） / `0001-FOO.md`（大写） / `0001 foo.md`（空格） 必 deny；非 decisions 路径写任何文件必 `{}`（不误杀）。
    - **Stop**：mock git diff 输出有 src/ 改动 + 无 design 改动 → 发 systemMessage；都改了 → `{}`；都没改 → `{}`；非 git 仓库 → 静默 exit。这一条在测试中通过 fake `git` 在 PATH 里替换实现。
    - **UserPromptSubmit**：触发词 `write spec` / `write plan` / `开始实施` / `写 spec` / `写 plan` / `implement now` 必发 additionalContext；普通对话 `tell me about X` 必 `{}`；混合带前后缀的句子也必触发（`please write spec for foo`）。
  - 此 ADR 同时确定测试命名约定：`test_hook_<event>_<scenario>.py`，每个 hook 一个文件。

  **相关**：ADR-0002（hooks 自动合并 — 不动；hooks 内容仍由 rendered snippet 决定）。

### 不需要 ADR

- #4–#7：CHANGELOG / 版本 / release / dogfood 同步执行 ADR-0009 已确定的方向，不引入新决策。

## 对 design.md 的影响（必填）

- §1 不动。
- §2 不动（不增删流程）。
- §3 不动。
- §4 不动（数据契约不变）。
- §5 不动（命令语义不变）。
- §6 不变量保持 8 条；新增第 9 条："4 个 specguard hook 的 shell 决策由 pytest 自动化压力测试覆盖（test_hook_*.py，每 hook 一文件）；模型采纳 governance context 仍需人工 dogfood"。
- §7.1 风险表：删除"hooks 行为只能通过人工 dogfood 验证"这一行，改写为"hooks shell 决策 / governance 触发词覆盖率 → tests/test_hook_*.py"；新增风险"hooks shell 决策被 pretest 覆盖但模型忽略 additionalContext / systemMessage"，缓解写"L2 真 Claude 端到端验证延后到未来���片"。
- §7.2 改动类型表：新增"hooks settings.json.snippet 修改"行，必跑测试 `tests/test_hook_*.py`。
- §7.3 dogfood：保留人工 dogfood 范围（init/check/marketplace），但去掉对 hooks shell 行为的 dogfood 责任；新增 v0.5.0 dogfood 占位条目。
- §7.4 未覆盖风险：把"hooks 实际行为"改为"模型实际是否消化 SessionStart additionalContext / UserPromptSubmit additionalContext / Stop systemMessage"——shell 层已自动化，剩下的是模型行为，pytest 不能覆盖。
- §8.1 v0.5+ 留位：从"skill pressure tests"项移除（已实现 L1 层）；保留"L2 真 Claude 端到端 hook 触发验证"作为新留位；保留 Cursor / Codex adapter / PR bot 等。
- §8.2 已删除清单不动。
- 顶部 `Last verified against code` 同步到本切片最终 HEAD short hash。

## 1. 切片范围

**包含**

1. ADR-0009 落档：`docs/specguard/decisions/0009-hooks-pressure-tests.md`；`decisions/README.md` 索引追加 0009 行；ADR-0002 状态保持 Accepted（仅相关引用）。
2. `tests/_hook_helpers.py` 或 `tests/conftest.py` 增加 helper：
   - 模块级 fixture `rendered_hooks_snippet`：跑一次 `specguard.render.render(target='claude', layout='specguard-default', out_dir=tmp_path)`，读 `hooks/settings.json.snippet`，返回 dict（已 JSON 解析）。
   - helper `extract_hook_command(snippet, event, status_message)`：根据 `hookEventName` 与 `statusMessage` 定位到 `command` 字符串。
   - helper `run_hook_command(command, stdin_json: str)`：`subprocess.run(['sh', '-c', command], input=stdin_json, capture_output=True, text=True, timeout=10)`，解析 stdout 为 dict（空字符串或 `{}` 都正常处理）。
3. 5 个测试文件：

   ### tests/test_hook_session_start.py
   - `test_session_start_emits_five_laws`：mock 空输入 `{}`，断言输出 dict 含 `hookSpecificOutput.hookEventName == "SessionStart"`、`additionalContext` 文本含五条法则的关键词（"design.md is the single current truth"、"ADR archive"、"dated design files"、"interface semantics"、"Brainstorm must produce an ADR judgement"）。
   - `test_session_start_paths_substituted`：断言 `additionalContext` 中已注入 `docs/specguard/design.md`、`docs/specguard/decisions`，无 `{{` 残留。

   ### tests/test_hook_pretooluse_dated_design.py
   - `test_block_dated_design_at_specs_root`：mock `{"tool_input":{"file_path":"docs/specguard/specs/foo-design.md"}}` → deny。
   - `test_block_dated_design_in_subdir`：mock `docs/specguard/specs/v0/foo-design.md` → deny。
   - `test_allow_spec_file`：mock `docs/specguard/specs/foo-spec.md` → `{}`（即 `{}` 字符串，解析为空 dict）。
   - `test_allow_design_md_root`：mock `docs/specguard/design.md` → `{}`（不在 specs/ 路径，不命中）。
   - `test_allow_other_path`：mock `src/foo.py` → `{}`。
   - `test_known_limitation_uppercase_extension`：mock `docs/specguard/specs/foo-design.MD` → 当前 hook 不命中（大小写敏感），断言为 `{}` 并加 pytest.mark 注释为已知漏洞，未来若 hook 加大小写宽容再调整断言。

   ### tests/test_hook_pretooluse_adr_filename.py
   - `test_allow_valid_adr_name`：`0001-foo.md` / `0042-multi-word.md` / `9999-z-z-z.md` → `{}`。
   - `test_allow_readme_template`：`README.md` / `TEMPLATE.md` → `{}`。
   - `test_deny_short_number`：`01-foo.md`（2 位）/ `001-foo.md`（3 位）→ deny。
   - `test_deny_uppercase`：`0001-FOO.md` → deny。
   - `test_deny_space`：`0001 foo.md` → deny。
   - `test_deny_no_number`：`foo.md` → deny。
   - `test_allow_non_decisions_path`：`docs/specguard/specs/0001-foo.md`（不在 decisions/ 下）→ `{}`。

   ### tests/test_hook_stop_design_sync.py
   - 用 `tmp_path` 临时 git repo + monkeypatch `CLAUDE_PROJECT_DIR`：在临时 repo 中各模拟 4 种 git diff 状态：
     - 仅 src/ 改动 → 期望 `systemMessage` 含 "design sync"
     - src/ + design.md 都改动 → `{}`
     - 仅 design.md 改动 → `{}`
     - 都没改 → `{}`
   - `test_outside_git_repo`：`CLAUDE_PROJECT_DIR=/nonexistent` → 不报错，stdout 为空或 `{}`。

   ### tests/test_hook_userprompt_adr.py
   - `test_trigger_english_write_spec`：prompt = `please write spec for foo` → additionalContext。
   - `test_trigger_english_write_plan`：`write plan now` → additionalContext。
   - `test_trigger_english_implement_now`：`implement now` → additionalContext。
   - `test_trigger_chinese_kaishi_shishi`：`开始实施` → additionalContext。
   - `test_trigger_chinese_xie_spec`：`写 spec` → additionalContext。
   - `test_trigger_chinese_xie_plan`：`写 plan` → additionalContext。
   - `test_no_trigger_normal_chat`：`tell me about the design` → `{}`。
   - `test_no_trigger_question`：`what does this hook do?` → `{}`。
   - `test_trigger_in_middle_sentence`：`hey, please write a spec for the new feature` → additionalContext（grep -i 命中）。

4. 修改 `docs/specguard/design.md`：§6 / §7.1 / §7.2 / §7.3 / §7.4 / §8.1 按上节"对 design.md 的影响"修改；顶部 `Last verified against code` 同步。
5. 修改 `CHANGELOG.md`：新增 v0.5.0 段，列出 5 个 hook 测试文件 + 测试矩阵覆盖（5 hook × 多 case）；标记 minor（非 BREAKING）。
6. bump `core/version` → `0.5.0`、`pyproject.toml.version` → `0.5.0`、`uv.lock`、`tests/test_release_workflow.py::test_core_version_is_v0_4_0` → `0.5.0`。
7. 推送 main、打 `v0.5.0` tag、CI 自动 render plugins/ + tarball；release 完成后从 tarball 跑 specguard-default init+check 验证 hooks 实际触发（spot check，确认 hooks shell 与 pytest 断言行为一致）；结果回填 design §7.3。

**不包含**

- L2 真 Claude 端到端测试：调 Claude CLI / API、烧 token 验证模型是否采纳 governance context。延后到独立切片（v0.6+）。
- L3 dogfood 机器人：留位。
- 修改 hooks shell 行为本身：本切片只测试现状，不调整 hook 逻辑（即使发现 case 不命中也只是 pytest.mark 记录）。
- Cursor / Codex adapter（v0.6+）。
- skill pressure test（design-governance skill 调用率验证需要真 Claude 对话，属于 L2，本切片不覆盖）。

## 2. 验收标准

1. **ADR-0009 已落档**：`docs/specguard/decisions/0009-hooks-pressure-tests.md` 存在；`decisions/README.md` 索引含 0009 行；ADR-0002 状态字段不变。

2. **5 个 hook 测试文件齐全**：`tests/test_hook_{session_start,pretooluse_dated_design,pretooluse_adr_filename,stop_design_sync,userprompt_adr}.py` 全部存在；helper 在 `tests/conftest.py` 或 `tests/_hook_helpers.py`；`uv run pytest tests/test_hook_*.py -v` 全绿；总用例数 ≥ 25（5 hook 平均 5+ case）。

3. **设计文档同步**：`docs/specguard/design.md` §6 不变量为 9 条；§7.1 风险表含 hook pressure test 行；§7.4 收紧"未覆盖"为"模型采纳 context 行为"；§8.1 移除 "skill pressure tests" 项、新增 L2 真 Claude 端到端留位；顶部 `Last verified against code` 为本切片最终 commit short hash；`CHANGELOG.md` 顶部含 `## v0.5.0` 段。

4. **v0.5.0 已发布**：`core/version` = `0.5.0`；`pyproject.toml.version` = `0.5.0`；`uv.lock` 同步；`uv run pytest` 全绿（≥ 67 个 test：现有 42 + 新增 25+）；`v0.5.0` tag 已推送；GH Release v0.5.0 含三个 tarball；`plugins/<layout>/.claude-plugin/plugin.json.version` = `0.5.0`（CI 自动 render 验证）。

5. **Spot-check dogfood**：从 v0.5.0 tarball 在临时 git repo 跑 `/specguard:init`，确认 hook merge 后 `.claude/settings.json` 含 5 个 specguard hook entry；手动触发一次 dated design block（尝试用 Write 工具写 specs/foo-design.md）确认实际被 deny；结果摘要写入 design §7.3 v0.5.0 dogfood 条目。

## 3. 留给后续切片的事

- L2 真 Claude 端到端 hook 触发验证（API token 消耗版）。
- Cursor / Codex / generic adapter。
- skill 调用率验证（design-governance skill description 触发条件优化）。
- PR bot / GitHub Action 治理报告。
- 中央 dashboard。
