# ADR 0009: specguard hooks 的 shell 决策由 pytest 强制覆盖

**状态**：Accepted
**日期**：2026-05-02
**拍板者**：用户（@saber，对话日期 2026-05-02）
**取代**：—
**相关**：
- ADR-0002（`/specguard:init` 自动合并 hooks 到 `.claude/settings.json`）— 状态保持 Accepted；本 ADR 不修改 hooks 自动合并行为，只新增对 hooks shell 输出的 pytest 覆盖。
- design.md §6 / §7.1 / §7.4 / §8.1
- spec docs/specguard/specs/v0-5-0-hooks-pressure-tests-spec.md

## Context

design.md §7.4 当前把 "hooks 实际行为" 整体列为 "未覆盖风险，需要人工 dogfood"。这条边界对 specguard 的 4 个 hook（SessionStart 注入治理 5 法、PreToolUse:Write 拦截 dated design、PreToolUse:Write 校验 ADR 文件名、Stop 提示 design 同步、UserPromptSubmit 检测 ADR 触发关键词）的 **shell 决策层** 而言过宽：

1. 每个 hook 的 shell 输入（Claude Code 注入的 mock JSON）和输出（决策 JSON：deny / additionalContext / systemMessage）是确定的，可用 `subprocess` 完全自动化覆盖。
2. 不可自动覆盖的部分仅剩 "模型是否真的采纳 SessionStart 的 additionalContext / UserPromptSubmit 的 additionalContext / Stop 的 systemMessage"，这部分依赖真 Claude，留在人工 dogfood + 未来 L2 真 Claude 端到端验证范围。
3. 当前 hook shell 行为的具体边界（例如 `.MD` 大写扩展是否被 `case "$path" in *-design.md)` 命中）只能靠人工偶发发现；自动化测试可以一次性锁住所有边界，并把已知边界用 xfail 固化。

## Decision

1. **测试文件布局**：每个 hook 一个独立测试文件，命名约定 `tests/test_hook_<event>_<scenario>.py`：
   - `test_hook_session_start.py`
   - `test_hook_pretooluse_dated_design.py`
   - `test_hook_pretooluse_adr_filename.py`
   - `test_hook_stop_design_sync.py`
   - `test_hook_userprompt_adr.py`
2. **fixture 来源**：测试 fixture 从 rendered `hooks/settings.json.snippet` 提取 hook command 字段，**不允许** 直接读 `adapters/claude/plugin/hooks/settings.json.snippet.tpl` 模板源码做手工 `{{ paths.* }}` 替换，确保测试与 render 流程同步。
3. **驱动方式**：`subprocess.run(['sh', '-c', cmd], input=mock_json, ...)` 跑 hook shell，断言 stdout 解析后的决策 JSON。
4. **已知边界处理**：本切片范围严格限定在 "测试现状"，**不修改任何 hook shell 逻辑**。已知漏洞（如 `.MD` 大写扩展未被拦截）以 `pytest.mark.xfail(strict=True)` 固化为已知行为；未来若修 hook，xfail 会主动 fail，强制回到本 ADR 重新评估。
5. **测试覆盖矩阵**（共 ≥25 case）：
   - **SessionStart**：发出的 JSON 含五条 governance laws 全文、event name 正确、路径占位已替换无 `{{` 残留。
   - **PreToolUse:Write dated design**：根目录与嵌套 `specs/*-design.md` 必 deny；`spec.md` 必放过；非 `specs/` 路径必放过；`.MD` 大写边界以 xfail 固化。
   - **PreToolUse:Write adr filename**：合法 `0001-foo.md` / `README.md` / `TEMPLATE.md` 放过；2 位、3 位编号、含大写、含空格、无编号 deny；非 `decisions/` 路径不误杀。
   - **Stop**：用临时 git repo + `monkeypatch CLAUDE_PROJECT_DIR` 跑 4 种 git diff 状态（无改动 / 仅 src 改动 / 仅 design.md 改动 / src + design.md 同时改动）；非 git 仓库静默退出。
   - **UserPromptSubmit**：英文（write spec / write plan / implement now）+ 中文（开始实施 / 写 spec / 写 plan）触发；普通对话不触发；中段触发（`grep -i` 子串命中）。
6. **测试命名约定** `test_hook_<event>_<scenario>` 写入本 ADR Decision 段固化，后续新增 hook 测试沿用。

## Consequences

- **正面**：
  - design.md §6 不变量从 8 条扩展到 9 条：新增 "4 个 specguard hook 的 shell 决策由 `tests/test_hook_*.py` 强制覆盖"。
  - design.md §7.1 风险表 "hooks 行为只能人工 dogfood" 改写为 "hooks shell 决策由 `test_hook_*.py` 覆盖；模型对 additionalContext / systemMessage 的实际采纳由人工 dogfood + 未来 L2"。
  - design.md §7.4 把 "hooks 实际行为" 收紧为 "模型实际是否消化 additionalContext / systemMessage"；shell 决策层移出风险列表。
  - 已知 hook 边界（如大小写敏感的扩展匹配）从 "偶发人工发现" 转为 xfail 显式固化，行为变更时 strict=True 主动报警。
  - 后续修改 hook shell 行为必须同步对应 `test_hook_*.py`，不会出现 "改了 hook 没人发现 case 反转" 的失踪。
- **负面**：
  - tests 目录新增 5 个文件、≥25 个 case，CI 跑测时间略增（subprocess 拉起 sh，单 case 数十毫秒级）。
  - L2 真 Claude 端到端验证（需要 API token、消耗成本）不在本切片范围，design.md §8.1 留位。
- **同步更新**：
  - `docs/specguard/design.md`：§6 不变量第 9 条新增；§7.1 风险表对应行重写；§7.4 收紧 hooks 风险描述；§8.1 移除 "skill pressure tests" 已实现项、新增 "L2 真 Claude 端到端 hook 触发验证" 留位；顶部 `Last verified against code` 更新为本切片 commit hash。
  - `docs/specguard/decisions/README.md`：索引表追加 0009 行。
  - 代码：新增 `tests/test_hook_session_start.py`、`tests/test_hook_pretooluse_dated_design.py`、`tests/test_hook_pretooluse_adr_filename.py`、`tests/test_hook_stop_design_sync.py`、`tests/test_hook_userprompt_adr.py`（本切片后续 task 实施，本 ADR 不直接落代码）。

## 替代方案

- **单文件 5 class 分组**：所有 hook 测试塞进一个 `test_hooks.py`，按 hook 分 class。拒绝：5 个独立文件粒度更清晰，按 hook 单独跑更快，且与 "测试命名直接体现 hook event" 的可读性目标一致。
- **直接读 `adapters/claude/plugin/hooks/settings.json.snippet.tpl` 模板源码做手动 `{{ paths.* }}` 替换**：拒绝。与 render 流程脱带，模板路径变化时测试不会同步发现，违反 "测试基于实际产物" 原则。
- **本切片同时修复已知 hook 漏洞**（如 `.MD` 大写扩展）：拒绝。本 ADR 范围严格控制在 "测试现状"，hook shell 行为修改属于独立切片，避免范围漂移；xfail(strict=True) 已经把已知漏洞固化，未来修复时会主动触发回归提示。

## 未来可能撤回的条件

L2 真 Claude 端到端测试（真 API token + 真模型采纳验证）落地后，本 ADR 的 L1 / L2 分层可能合并；但 L1（subprocess shell）与 L2（真模型 + token）不是替代关系——L1 仍是 CI 必跑、L2 是定期跑。撤回需新立 ADR。
