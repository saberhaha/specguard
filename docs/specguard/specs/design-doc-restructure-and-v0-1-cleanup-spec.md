# design-doc-restructure-and-v0-1-cleanup 设计补充

**日期**：2026-05-01
**适用范围**：v0.2.1 文档与命令语义整理切片：重构 `docs/specguard/design.md` 为 AI 协作优先的 living architecture 文档，清理 v0.1 残留的 semantic review package 设计与误导性文案，并补齐 `/specguard:upgrade` 已声明但未落实的交互语义。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

**A. design.md 重构**
1. 将 `docs/specguard/design.md` 重构为 8 节：产品定位与边界、端到端流程、架构分层、数据契约、命令语义、不变量与安全边界、测试策略、不在范围。
2. 在 §2 新增 4 张 Mermaid 图：Build / Release flow、Init flow、Check flow、Upgrade flow。
3. 在 §4 新增集中式数据契约清单（11 条），包含执行强度三级：机器强制、治理强制、用户契约。
4. 在 §5 新增命令语义：通用规则、`/specguard:init`、`/specguard:check`、`/specguard:upgrade`、prompt ↔ runtime Python API。
5. 在 §6 新增不变量与安全边界，覆盖 marker 外永不动、dry-run 不写项目文件、upgrade 两阶段写入、hooks 前缀识别、release/runtime 边界、layout/adapter 边界、check 只读、specguard 不执行用户项目代码。
6. 在 §7 将测试矩阵从文件清单重构为风险 → 测试防线 / 改动类型 → 必跑测试 / 必须人工 dogfood / 未覆盖风险。
7. 在 §8 保留 v0.3+ 不在范围，同时新增“已删除”小节记录 semantic review package 删除。

**B. v0.1 残留清理**
8. 删除 `/specguard:check semantic` review package 模式：`core/command-prompts/check.md` 不再接受 `semantic` 作为生成 `.specguard/reviews/<UTC>/` 的模式；design.md 不再描述 `.specguard/reviews/` 数据契约。
9. 修正 `core/command-prompts/init.md` embedded hooks snippet 文案，将 “manually merge” 改为“auto-merged via hooks_merge”；不改变 hooks JSON 本身。
10. 修正 `/specguard:check` 第 12 项的 error message：优先提示运行 `/specguard:init` 自动合并，手动 merge 仅作为 fallback，不作为主路径。
11. 修正 README Development 段 `git clone <this repo>` 占位符为 `git clone https://github.com/saberhaha/specguard.git`。

**C. upgrade 语义补齐**
12. `/specguard:upgrade` 缺 `.specguard-version` 时停止并提示先运行 `/specguard:init`，不执行 init-then-upgrade 复合流程。
13. `/specguard:upgrade` 读取 `${CLAUDE_PLUGIN_ROOT}/version` 与 `.specguard-version.specguard_version`；相等时输出 “already up to date” 并退出，不做写入。
14. `specguard.upgrade.upgrade_project()` 增加 dry-run / diff summary 能力，使 prompt 能先展示 diff summary、等待用户确认后再写入。
15. `/specguard:upgrade` prompt 落实“展示 diff summary → 等待用户确认 → 写入”的交互语义。

**D. 保留的未来留位 / 兼容契约（不改）**
16. 保留 `/specguard:init --ai <claude|cursor|codex|generic|auto>`：这是未来 adapter 留位；v0.2 仍只有 `claude` 可执行。
17. 保留 `/specguard:init --spec <none|openspec|superpowers|auto>`：这是 runtime 用户便利接口；若探测结果与当前 rendered layout 不匹配，提示用户安装对应 layout plugin。
18. 保留 check 对 pre-existing spec 文件的豁免：用于存量项目采纳 specguard。
19. 保留 superpowers layout 对老 `*-design.md` 的 warning 例外：用于兼容 superpowers 历史快照。
20. 保留 §8 的 skill pressure tests / PR bot / marketplace / multi-agent adapter 等 v0.3+ 不在范围条目。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1-#7 design.md 结构重构 | - | - | - | - | - |
| #8 删除 `/specguard:check semantic` review package | ✓ | - | - | - | ✓ |
| #9 init hooks 文案修正 | - | - | - | - | - |
| #10 check hooks error message 优化 | ✓ | - | - | - | - |
| #11 README clone URL 修正 | - | - | - | - | - |
| #12 upgrade 缺 `.specguard-version` 停止 | ✓ | - | - | - | ✓ |
| #13 upgrade already-up-to-date 短路 | ✓ | - | - | - | - |
| #14 upgrade dry-run / diff summary API | ✓ | - | ✓ | - | - |
| #15 upgrade diff summary + 用户确认 | ✓ | - | - | - | ✓ |
| #16-#20 保留接口留位 / 兼容契约 | - | - | - | - | - |

### 候选 ADR（请用户拍板）

- **ADR-0005：删除 `/specguard:check semantic` review package 模式**  
  覆盖改动 #8。命中接口语义变化 + 推翻先前 design。理由：`/specguard:check` 本身已经运行在 Claude（LLM）里，让一个 LLM 生成另一个 LLM 的 prompt/context/findings-template 是 v0.1 工具型心智残留。未来如需语义审查，应由 Claude 在 check 对话内直接输出 findings，不写 `.specguard/reviews/`。

- **ADR-0006：收紧 `/specguard:upgrade` 写入前交互与缺版本行为**  
  覆盖改动 #12、#14、#15，并记录 #13 为已声明语义的实现补齐。命中接口语义变化 + 跨模块依赖（prompt 依赖 `upgrade_project(..., dry_run=True)` 的 diff summary）。理由：upgrade 修改已有用户项目文件，必须在写入前展示 diff summary 并等待用户确认；缺 `.specguard-version` 表示项目尚未初始化，不应在 upgrade 内复合执行 init。

### 灰色地带

- **#10 check hooks error message 优化**：仍然允许手动 merge 作为 fallback，但不再作为主路径。属于文案与用户引导修正，不单独立 ADR。
- **#13 already-up-to-date 短路**：design/prompt 已声明该行为，本次只是补齐实现，不单独立 ADR；若实现中发现需要新增版本文件或改 `.specguard-version` schema，再另行 ADR。
- **#14 dry-run / diff summary API**：可被视为 Python API 扩展。由于它服务于 #15 的命令交互语义，纳入 ADR-0006，不单独立号。

### 不需要 ADR

- #1-#7：design.md 结构重组，不改变接口/数据/依赖。
- #9：删除 v0.1 手动 merge 文案残留，不改变实际行为。
- #11：README URL 文案修正。
- #16-#20：明确保留现有接口留位 / 兼容契约，不改变行为。

## 对 design.md 的影响（必填）

- 全文重构为 8 节：产品定位与边界、端到端流程、架构分层、数据契约、命令语义、不变量与安全边界、测试策略、不在范围。
- §2 新增 4 张 Mermaid 图，分别表达 build/release、init、check、upgrade。
- §4 新增 11 条数据契约：`.specguard-version`、`.plugin_source`、CLAUDE.md specguard 块、decisions README rules marker、settings hooks、hooks snippet、`*-design.md` 禁令、ADR 文件名、design.md 本身、spec ADR 判断标题、ADR supersede 引用。
- §5 删除 semantic review package 描述，改为 `/specguard:check` 默认只读；新增 upgrade diff/confirm 与 already-up-to-date 语义。
- §6 抽出横向不变量与安全边界。
- §7 将测试文件列表改为风险驱动测试策略。
- §8 保留 v0.3+ 不在范围，同时记录 semantic review package 已删除。
- 更新顶部 `Last verified against code` 字段为实施完成后的 HEAD short hash。

## 1. 切片范围

**包含**
- 新增 ADR-0005 与 ADR-0006，并更新 `docs/specguard/decisions/README.md`。
- 重写 `docs/specguard/design.md`，保持与当前代码一致，并显式标注本切片新增/删除的命令语义。
- 修改 `core/command-prompts/check.md`：删除 `semantic` 参数与 `.specguard/reviews/` 生成逻辑；优化第 12 项 error message。
- 修改 `core/command-prompts/init.md`：修正 hooks snippet embedded section 的 “manually merge” 残留文案。
- 修改 `core/command-prompts/upgrade.md`：缺 `.specguard-version` 时停止并提示 init；明确 already-up-to-date 短路；落实 diff summary + 用户确认流程。
- 修改 `src/specguard/upgrade.py`：增加 dry-run / diff summary 能力，并让 `UpgradeResult` 携带 diff summary（字段名在 implementation plan 中最终确定）。
- 修改 `tests/test_render_claude_default.py` / `tests/test_dogfood_upgrade.py`：覆盖 semantic 删除、init 文案、check message、upgrade dry-run diff、already-up-to-date prompt 文案。
- 修改 README Development URL 为真实 GitHub URL。
- 修改 CHANGELOG：新增 v0.2.1 或 Unreleased 节，记录 semantic 删除和 upgrade 交互补齐。

**不包含**
- 多 agent adapter（Cursor / Codex / generic）实现。
- marketplace 分发。
- skill pressure tests 实现。
- PR bot / GitHub Action 治理报告。
- 中央 dashboard。
- 将 semantic 审查改造成真实 LLM review 功能。

## 2. 验收标准

1. **ADR**：`docs/specguard/decisions/0005-*.md` 与 `0006-*.md` 存在，`decisions/README.md` 已索引。
2. **design.md 结构**：`docs/specguard/design.md` 包含 8 个一级/二级主章节，且 §2 包含 4 个 Mermaid 图块。
3. **数据契约**：design.md §4 包含 11 条契约，并包含执行强度三级说明。
4. **semantic 删除**：rendered `commands/check.md` 不包含 `semantic`、`.specguard/reviews`、`findings-template`、`Do NOT call any LLM` 等旧 review package 文案。
5. **check 行为**：rendered `commands/check.md` 第 12 项仍将缺失 specguard hooks 视为 error，且优先提示 `/specguard:init` 自动合并；手动 merge 仅作为 fallback。
6. **init 文案**：rendered `commands/init.md` hooks embedded section 不再出现 “manually merge into `.claude/settings.json`” 作为主路径文案。
7. **upgrade 缺版本**：rendered `commands/upgrade.md` 明确：缺 `.specguard-version` 时停止并提示先运行 `/specguard:init`，不执行 init-then-upgrade 复合流程。
8. **upgrade 短路**：rendered `commands/upgrade.md` 明确读取 `${CLAUDE_PLUGIN_ROOT}/version`，若与 `.specguard-version.specguard_version` 相等则输出 “already up to date” 并退出。
9. **upgrade diff/confirm**：rendered `commands/upgrade.md` 明确先 dry-run 生成 diff summary、展示给用户、等待确认后才写入。
10. **upgrade runtime API**：`tests/test_dogfood_upgrade.py` 覆盖 `upgrade_project(..., dry_run=True)` 不写文件且返回 diff summary；确认后写入路径仍通过现有 happy path 测试。
11. **README**：README Development 段使用 `git clone https://github.com/saberhaha/specguard.git`。
12. **测试**：`uv run pytest` 全绿；三 layout render 成功；rendered commands 无 `<!-- inject:` 残留。
13. **design sync**：`Last verified against code` 更新到最终 HEAD；design.md 中不再描述 `.specguard/reviews/`。

## 3. 留给后续切片的事

- Cursor / Codex / generic adapter。
- marketplace 安装路径。
- skill pressure tests。
- PR bot / GitHub Action 治理报告。
- 中央 dashboard。
- 未来如需语义审查，在 `/specguard:check` 对话内直接输出 findings，不恢复 review package 目录，除非重新立 ADR。
