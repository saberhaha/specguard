# v0-3-0-withdraw-upgrade-and-simplify-contracts 设计

**日期**：2026-05-01
**适用范围**：v0.3.0 BREAKING 切片：撤回 `/specguard:upgrade` 命令（伪需求），同步删除 `.specguard-version`、`.plugin_source`、`.specguard/hooks.snippet.json`、`decisions/README.md` rules marker；`/specguard:check` 从 13 项收敛到 11 项；CHANGELOG 保留历史段，v0.3.0 段显式标 BREAKING；release 后立即 dogfood 验证。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

1. 删除 `/specguard:upgrade` 命令、对应 prompt、Python runtime module 与全部 upgrade 测试。
2. 删除 init prompt 中 `.specguard-version` 写入与 `.plugin_source` marker 读取段。
3. 删除 release workflow 写 `.plugin_source` 步骤；release tarball 不再携带 `.plugin_source` 文件。
4. 删除 `core/templates/decisions/README.md.tpl` 中 `<!-- specguard:rules:start -->` ↔ `<!-- specguard:rules:end -->` marker；rules 段落变为用户自由编辑。
5. 删除 init prompt 写 `.specguard/hooks.snippet.json` 的步骤；init 直接通过 `specguard.hooks_merge` 把 hooks 合并进 `.claude/settings.json`，不再产出 snippet 中间文件。
6. 删除 `/specguard:check` 第 11 项（hooks.snippet.json 存在）、第 12 项（settings.json 含 specguard hooks）、第 13 项（`.specguard-version` 存在），13 项缩为 11 项。
7. 重写 `docs/specguard/design.md`：3 张 Mermaid（删 upgrade flow）、§4 数据契约 7 条、§5 命令语义仅 init/check、§6 不变量 7 条、§7 测试矩阵不含 upgrade、§7.3 增加 v0.3.0 dogfood 记录、§8.2 已删除清单扩充、顶部 `Last verified against code` 同步到最终 HEAD。
8. 更新 `README.md`：删除 `/specguard:upgrade` quickstart 段、Status 表对应行；quickstart tarball URL bump 到 v0.3.0。
9. 更新 `CHANGELOG.md`：保留 v0.1.0 / v0.2.0 / v0.2.1 历史段，新增 v0.3.0 段并显式标 BREAKING、列出全部移除项。
10. bump `core/version`、`pyproject.toml`、`uv.lock`、`tests/test_release_workflow.py` 到 `0.3.0`。
11. 修订测试：删除 `tests/test_dogfood_upgrade.py`；从 `tests/test_render_claude_default.py` 删除 upgrade / plugin_source / `.specguard-version` / 缺 hooks 错误 等断言；从 `tests/test_release_workflow.py` 删除 `.plugin_source` 写入断言并 bump 版本期望值；新增 `test_render_runtime_only_includes_hooks_merge` 断言 dist 下 `runtime/specguard/` 仅含 `__init__.py` 与 `hooks_merge.py`。
12. 推送 main、打 `v0.3.0` tag、触发 GitHub Release workflow；release 后从下载的 tarball 在临时 git repo 跑 `/specguard:init` + `/specguard:check`，结果写入 design §7.3。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 删除 `/specguard:upgrade` | ✓ | - | ✓ | - | ✓ |
| #2 删除 `.specguard-version` 与 `.plugin_source` 行为 | ✓ | ✓ | - | - | ✓ |
| #3 删除 release workflow 写 `.plugin_source` | - | ✓ | - | - | ✓ |
| #4 删除 decisions rules marker | - | ✓ | - | - | ✓ |
| #5 删除 `.specguard/hooks.snippet.json` 写入 | ✓ | ✓ | - | - | ✓ |
| #6 check 13 项→11 项 | ✓ | - | - | - | ✓ |
| #7 design.md 同步 | - | - | - | - | - |
| #8 README 同步 | - | - | - | - | - |
| #9 CHANGELOG 同步 | - | - | - | - | - |
| #10 版本 bump 到 0.3.0 | - | - | - | - | - |
| #11 测试修订 | - | - | - | - | - |
| #12 release + dogfood | - | - | - | - | - |

### 候选 ADR（请用户拍板）

- **ADR-0007：撤回 `/specguard:upgrade` 并简化数据契约**

  覆盖改动 #1–#6。命中接口语义 + 数据格式 + 跨模块依赖 + 推翻先前 design。

  关键陈述：
  - upgrade 是伪需求：v0.x 用户基数为 0，无真实跨版本升级痛点驱动；同类工具（OpenSpec / Spec Kit / Superpowers，基于训练数据印象）惯例无 upgrade 命令。
  - 同步删除仅服务 upgrade 的数据契约：`.specguard-version`、`.plugin_source`、decisions/README rules marker、`.specguard/hooks.snippet.json`。
  - check 第 11/12/13 项作为同根连带删除。
  - 保留：init 自动合并 hooks（design/ADR/spec 治理价值与 upgrade 无关）、CLAUDE.md marker（init 幂等需要）、`hooks_merge.py` runtime（init 仍调用）。
  - 撤回不等于永远不做。未来若出现真实用户与真实跨版本升级痛点，重新立 ADR 设计。

  **取代**：ADR-0006。
  **相关**：ADR-0002（hooks 自动合并保留，但 check 不再验证）；ADR-0003（GitHub Release 分发保留，`.plugin_source` 字段废弃）；ADR-0004（`hooks_merge.py` 模块保留，`upgrade.py` 模块删除）。这三个 ADR 的 Status 字段不变，仅在 ADR-0007 Consequences 段说明周边字段调整。

### 不需要 ADR

- #7–#12：design / README / CHANGELOG / 版本 / 测试 / release 同步执行 ADR-0007 已确定的方向，不引入新决策。

## 对 design.md 的影响（必填）

- §1 不动（产品定位与边界保持）。
- §2.1 Build/Release flow Mermaid：删除 `.plugin_source stamped` 节点。
- §2.2 Init flow Mermaid：删除 `write .specguard-version` 节点。
- §2.3 Check flow Mermaid：保持。
- §2.4 Upgrade flow Mermaid：整张图删除（4 张 Mermaid 减为 3 张）。
- §3.4 src/specguard：`upgrade.py` 段删除；render.py 描述改为复制 `__init__.py` 与 `hooks_merge.py`；删除"runtime/specguard/ 供 /specguard:upgrade 在用户项目里通过 CLAUDE_PLUGIN_ROOT/runtime 导入"，只剩 init 调用方。
- §4 数据契约表从 11 条收敛到 7 条：删除 `.specguard-version`、`.plugin_source`、decisions/README rules marker、`.specguard/hooks.snippet.json`。保留：CLAUDE.md specguard block、settings.json hooks、禁止 `*-design.md`、ADR 文件名、design.md 自身、spec ADR 判断标题、ADR supersede 引用。
- §5.2 init：删除"写 `.specguard-version`"段。
- §5.3 check：13 项改 11 项。
- §5.4 upgrade：整段删除。
- §5.5 prompt ↔ runtime API：删除 upgrade 部分，仅保留 init→`hooks_merge`。
- §6 不变量 8 条降到 7 条：删除"upgrade 两阶段写入"；release/runtime 边界文案改为"release tarball 必须携带 `runtime/specguard/`"（去掉 `.plugin_source`）。
- §7.1 风险表：删除 "upgrade conflict 后半写入"；"release tarball 缺 runtime 或 provenance" 改为 "release tarball 缺 runtime"。
- §7.2 改动类型表：删除 upgrade runtime 行。
- §7.3 必须人工 dogfood：删除 upgrade 行；新增 v0.3.0 release 后 dogfood 记录条目（init + check 在 specguard-default / superpowers / openspec-sidecar 三 layout 临时 repo 跑通）。
- §7.4 未覆盖风险：保持。
- §8.1 v0.3+ 留位：新增"upgrade 命令（如未来出现真实跨版本升级痛点重新立 ADR）"。
- §8.2 已删除：扩充列出 ADR-0007 撤回清单（`/specguard:upgrade` 命令、`.specguard-version`、`.plugin_source`、decisions/README rules marker、`.specguard/hooks.snippet.json`、check 第 11/12/13 项）。
- 顶部 `Last verified against code` 同步到本切片最终 HEAD short hash。

## 1. 切片范围

**包含**

1. 新建 ADR-0007；改 ADR-0006 状态为 `Superseded by ADR-0007`；`decisions/README.md` 索引加 0007 行。
2. 删除 upgrade 命令链：`core/command-prompts/upgrade.md`、`adapters/claude/plugin/commands/upgrade.md.tpl`、`src/specguard/upgrade.py`、`tests/test_dogfood_upgrade.py`；`adapters/claude/manifest.yaml` 删 upgrade 渲染条目；`src/specguard/render.py` 不再复制 `upgrade.py`。
3. 删除三个伪契约：
   - init prompt 不再写 `.specguard-version`、不再读 `.plugin_source` marker。
   - init prompt 不再写 `.specguard/hooks.snippet.json`，改为直接调 `specguard.hooks_merge` 把 hooks 合并进 `.claude/settings.json`。
   - `core/templates/decisions/README.md.tpl` 删除 `<!-- specguard:rules:start -->` ↔ `<!-- specguard:rules:end -->` marker。
   - `.github/workflows/release.yml` 删除 `echo "github-release-v${version}" > "${out}/.plugin_source"` 步骤。
4. check prompt 删除原第 11 项（hooks.snippet.json 存在）、第 12 项（settings.json hooks）、第 13 项（`.specguard-version`），13 项收敛为 11 项；缺 hooks 错误信息整段删除。
5. 重写 `docs/specguard/design.md`：见上节"对 design.md 的影响"。
6. 修订 `README.md`：删除 `/specguard:upgrade` quickstart 段；Status 表删 upgrade 相关行；quickstart tarball URL bump 到 v0.3.0。
7. 更新 `CHANGELOG.md`：保留 v0.1.0 / v0.2.0 / v0.2.1 历史段不变；新增 v0.3.0 段，开头显式 `### BREAKING`，列出全部移除项与迁移指引（"用户从 v0.2.x 升级：删除 `.specguard-version`、`.plugin_source`、`.specguard/hooks.snippet.json`、`decisions/README.md` 中 `<!-- specguard:rules:start/end -->` marker 内容；其余文件 init 重跑即可"）。
8. bump 版本：`core/version` → `0.3.0`；`pyproject.toml.project.version` → `0.3.0`；`uv lock` 同步；`tests/test_release_workflow.py::test_core_version_is_v0_2_1` 改为 `test_core_version_is_v0_3_0` 并断言 `0.3.0`。
9. 修订测试：
   - 删除 `tests/test_dogfood_upgrade.py`。
   - `tests/test_render_claude_default.py` 删除全部 `test_upgrade_command_*`、`test_init_command_uses_marker_for_plugin_source`、`test_check_command_treats_missing_hooks_as_error`、以及 init 测试中 `tempfile`/`plugin_source`/`specguard.hooks_merge` 与 hooks.snippet.json 路径相关断言（替换为"init 直接调用 hooks_merge"的断言）。
   - `tests/test_release_workflow.py` 删除 `test_release_workflow_writes_plugin_source_marker`；`test_core_version_is_v0_2_1` 改名 + 改值。
   - 新增 `tests/test_render_basic.py::test_render_runtime_only_includes_hooks_merge`（或就近放在合适测试文件）：断言 dist 下 `runtime/specguard/` 仅包含 `__init__.py` 与 `hooks_merge.py`。
10. 推送 main、打 `v0.3.0` tag、等 GitHub Release workflow；release 后从下载的 tarball 在 `/tmp` 下临时 git repo 跑 `claude --plugin-dir <unpacked> -p '/specguard:init --ai claude --spec none'`，再跑 `/specguard:check`，三 layout 各跑一遍；任一失败则停止并补丁；全部通过后把结果写入 design §7.3。

**不包含**

- 删除 hooks 自动合并能力：init 仍合并 hooks，hooks 是 design/ADR/spec 治理的 enforcement，与 upgrade 无关。
- 删除 `CLAUDE.md` 的 `<!-- specguard:start -->` ↔ `<!-- specguard:end -->` marker：init 幂等替换需要它。
- 删除 `src/specguard/hooks_merge.py`：init 仍调用。
- 重新设计 upgrade：撤回不等于永远不做，未来如有真实用户与真实跨版本升级痛点重新立 ADR。
- 重写 design.md 顶层结构：保持 8 节，原地修订。
- Cursor / Codex / generic adapter（v0.4+）。
- Marketplace 安装（v0.4+）。
- skill pressure tests（v0.4+）。

## 2. 验收标准

1. **ADR-0007 已落档**：`docs/specguard/decisions/0007-withdraw-upgrade-and-simplify-contracts.md` 存在；`decisions/README.md` 索引含 0007 行；`docs/specguard/decisions/0006-tighten-upgrade-interaction-and-version-handling.md` 顶部 `**状态**` 字段为 `Superseded by ADR-0007`；ADR-0001/0002/0003/0004/0005 状态字段不变。

2. **upgrade 整条命令链已删除**：`core/command-prompts/upgrade.md`、`adapters/claude/plugin/commands/upgrade.md.tpl`、`src/specguard/upgrade.py`、`tests/test_dogfood_upgrade.py` 均不存在；`adapters/claude/manifest.yaml` 不含 upgrade 渲染条目；rendered 三 layout `commands/` 目录下只有 `init.md` 与 `check.md`；rendered runtime `runtime/specguard/` 只含 `__init__.py` 与 `hooks_merge.py`；`src/specguard/render.py` 源码不引用 `upgrade.py`。

3. **三个伪契约已清干净**：
   - rendered `commands/init.md` 不含 `.specguard-version`、`.plugin_source`、`hooks.snippet.json` 任一字串；init prompt 不再向项目写这三个文件。
   - rendered `commands/check.md` 不含 `.specguard-version`、`hooks.snippet.json`、缺 hooks 错误信息相关字串。
   - rendered `decisions/README.md` 不含 `<!-- specguard:rules:start -->` 与 `<!-- specguard:rules:end -->` 任一 marker；`core/templates/decisions/README.md.tpl` 同样不含。
   - `.github/workflows/release.yml` 不含 `.plugin_source` 字串；release tarball 解包后根目录不存在 `.plugin_source` 文件。

4. **check 收敛到 11 项 + design.md 同步**：rendered `commands/check.md` 包含且仅包含编号 1–11 的结构检查；`docs/specguard/design.md` 改动包括 3 张 Mermaid（无 upgrade flow）、§4 数据契约表 7 条、§5 仅含 init/check、§6 不变量 7 条、§7.3 含 v0.3.0 dogfood 记录条目、§8.2 已删除清单含 ADR-0007 撤回项；`Last verified against code` 字段为本切片最终 commit short hash；`README.md` 不含 `/specguard:upgrade` 字串、Status 表无 upgrade 行、quickstart tarball URL 含 `v0.3.0`；`CHANGELOG.md` 顶部含 `## v0.3.0` 段，段内含 `### BREAKING` 与移除项清单及迁移指引；v0.1.0 / v0.2.0 / v0.2.1 历史段保留不变。

5. **v0.3.0 已发布并 dogfood 通过**：`core/version` = `0.3.0`；`pyproject.toml.project.version` = `0.3.0`；`uv.lock` 中 specguard 版本 = `0.3.0`；`tests/test_release_workflow.py` 期望值 = `0.3.0`；`uv run pytest` 全绿；`v0.3.0` tag 已推送到 origin；GitHub Release `v0.3.0` 含三个 layout tarball（specguard-default、superpowers、openspec-sidecar）；从 release 下载每个 tarball 在 `/tmp` 临时 git repo 跑 `/specguard:init` 与 `/specguard:check` 全部通过；dogfood 结果（每 layout 跑通 init + check 的命令日志摘要）写入 design §7.3。

## 3. 留给后续切片的事

- Cursor / Codex / generic adapter。
- Marketplace 安装（`claude plugin install specguard`）。
- skill pressure tests（系统验证 4 个 hooks 在真 Claude 对话中的拦截行为）。
- PR bot / GitHub Action 治理报告。
- 中央 dashboard。
- 未来若出现真实用户与真实跨版本升级痛点，重新立 ADR 设计 upgrade。
