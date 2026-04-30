# distribution-and-auto-hooks 设计补充

**日期**：2026-05-01
**适用范围**：v0.2.0 一次性交付：让 specguard 通过 GitHub Release tarball 对外分发，并把 `/specguard:init` 的 hooks 合并由"手动"改为"自动"，同时把 `/specguard:upgrade` 端到端跑通。

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解

**P0 分发**
1. 新增 GitHub Actions workflow：tag 触发渲染 3 个 layout 的 tarball 并上传 GitHub Release。
2. 新增 `.specguard-version` 字段 `plugin_source`（`github-release-vX.Y.Z` 或 `local-dist`），由 init 写入。
3. README 顶部改为"从 GitHub Release 下载 → claude --plugin-dir → /specguard:init"用户视角；开发者 render 路径下移为 development 段。

**P1-A 自动合并 hooks**
4. 新增 `src/specguard/hooks_merge.py`，承载 `.claude/settings.json` 与 `.specguard/hooks.snippet.json` 的解析、合并、幂等替换与 dry-run diff 生成。
5. `/specguard:init` 第 5 步改为：写 `.specguard/hooks.snippet.json` → 调用 `specguard.hooks_merge` 读 `.claude/settings.json`（或视为空） → 按 event 名 union + `specguard:` 前缀幂等替换 → atomic 写回。
6. `/specguard:init` 新增 `--dry-run` 标志：仅打印将要合并的 diff 与 snippet 内容，不落盘。
7. `/specguard:check` 第 12 项：`.claude/settings.json` 缺失 specguard hooks 由 warning 升为 error。
8. 新增 `tests/test_init_merge_hooks.py`：覆盖空 settings.json、已含 specguard hooks 幂等、已含其它 hooks 不被破坏、非法 JSON 报错、dry-run 不落盘。

**P1-B upgrade 端到端**
9. 新增 `src/specguard/upgrade.py`，承载 5 个 marker 区域的检测、diff、替换、conflict 识别、`.specguard-version` legacy 补写。
10. `/specguard:upgrade` 调用 `specguard.upgrade` 真实执行 design.md §3.3 列出的 5 个 marker 区域 diff 与替换；marker 缺失时输出 manual patch，不自动插入。
11. `/specguard:upgrade` 兼容 v0.1.x（`.specguard-version` 缺 `plugin_source`）：按 `local-dist` 视为 legacy，升级后补写字段。
12. 新增 `tests/test_dogfood_upgrade.py`：在 fixture 项目从 v0.1.0 升至 v0.2.0，断言 5 个 marker 区域正确替换、marker 外不变、`.specguard-version` 更新含 `plugin_source`。

**版本机械动作**
13. `core/version` 由 `0.1.0` 升为 `0.2.0`。
14. CHANGELOG.md 增加 `## v0.2.0`。

### 五条硬条件匹配

| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 GitHub Actions release | - | - | - | ✓ | - |
| #2 `.specguard-version.plugin_source` | - | ✓ | - | - | - |
| #3 README 用户视角 | - | - | - | - | - |
| #4 hooks_merge.py 模块 | - | - | ✓ | - | - |
| #5 init 自动合并 settings.json | ✓ | - | ✓ | ✓ | ✓ |
| #6 init `--dry-run` | ✓ | - | - | - | - |
| #7 check 第 12 项 warning→error | ✓ | - | - | - | ✓ |
| #8 init 合并测试 | - | - | - | - | - |
| #9 upgrade.py 模块 | - | - | ✓ | - | - |
| #10 upgrade 5 marker 落地 | ✓ | - | ✓ | - | - |
| #11 upgrade 兼容 v0.1.x | ✓ | ✓ | - | - | - |
| #12 upgrade dogfood 测试 | - | - | - | - | - |
| #13 core/version 升级 | - | - | - | - | - |
| #14 CHANGELOG | - | - | - | - | - |

### 候选 ADR（已用户拍板）

- **[ADR-0002](../decisions/0002-init-auto-merge-hooks.md)**：`/specguard:init` 自动合并 hooks。覆盖改动 #5、#6、#7（合并算法 + dry-run + check 升级一并写在 Consequences）。命中接口语义、外部依赖、推翻先前。
- **[ADR-0003](../decisions/0003-distribution-via-github-release.md)**：GitHub Release tarball 分发。覆盖改动 #1、#2、#10、#11（artifact + plugin_source + upgrade 落地 + legacy 兼容一并写在 Consequences）。命中外部依赖、数据格式（schema 变更）、接口语义（upgrade 首次实装）。
- **[ADR-0004](../decisions/0004-python-modules-for-runtime-algorithms.md)**：init hooks 合并与 upgrade marker 替换下沉为 Python module。覆盖改动 #4、#9 的可测试实现边界。命中跨模块依赖。

灰色地带项已按"偏严"约定全部并入上述 ADR 的 Consequences 段，不再单独立号。

### 不需要 ADR

- #3 README：纯文档调整。
- #8、#12：测试新增，无对外语义变化。
- #13、#14：版本号 / CHANGELOG，机械动作。

## 对 design.md 的影响（必填）

- **§2 三层架构**：在 `dist/<target>/<layout>/` 节点后说明 v0.2 起此目录被 GitHub Actions 打包为 release tarball；新增引用 `（见 ADR-0003）`。
- **§3.1 `/specguard:init`**：
  - 第 5 步重写为"写 snippet → 合并到 `.claude/settings.json`（按 `specguard:` 前缀幂等）→ 支持 `--dry-run`"，追加 `（见 ADR-0002）`。
  - 第 6 步 `.specguard-version` 字段列表增加 `plugin_source`，追加 `（见 ADR-0003）`。
- **§3.2 `/specguard:check`**：第 12 项措辞由"缺失为 warning"改为"缺失为 error"，追加 `（见 ADR-0002）`。
- **§3.3 `/specguard:upgrade`**：删掉"MVP 未做端到端 dogfood"句；增加"对 v0.1.x 缺 `plugin_source` 的项目按 legacy 处理并补写字段"；追加 `（见 ADR-0003）`。
- **§4 Hooks**：在末段补一句"hooks 通过 `/specguard:init` 自动合并到 `.claude/settings.json`，去重依据 `statusMessage` 前缀"，追加 `（见 ADR-0002）`。
- **§5 测试矩阵**：新增 2 行（test_init_merge_hooks、test_dogfood_upgrade）；总数从 21 调至预期值（实现完成后核对再写）。
- **§6 不在范围**：移除 `/specguard:upgrade 端到端 dogfood`；保留 marketplace、Cursor/Codex、semantic check、skill pressure tests、PR bot。

## 1. 切片范围

**包含**
- 新增 `.github/workflows/release.yml`（tag 触发，渲染并打包 3 份 tarball）。
- 新增 `src/specguard/hooks_merge.py` 与 `src/specguard/upgrade.py`。
- 修改 `core/command-prompts/init.md`：调用 `specguard.hooks_merge` + dry-run + 写 `plugin_source`。
- 修改 `core/command-prompts/check.md`：第 12 项 → error。
- 修改 `core/command-prompts/upgrade.md`：调用 `specguard.upgrade` + 5 marker + legacy 兼容 + 补写 `plugin_source`。
- 修改 `adapters/claude/plugin/commands/init.md.tpl`：`argument-hint` 增加 `[--dry-run]`。
- 修改 `adapters/claude/manifest.yaml` 或 release workflow：确保 release tarball 中 Python module 可被 prompt 调用。
- 修改 `core/version`：`0.1.0` → `0.2.0`。
- 新增测试 `tests/test_init_merge_hooks.py` 与 `tests/test_dogfood_upgrade.py`。
- 修改 README：用户视角优先；移除"手动合并 snippet"步骤。
- 修改 CHANGELOG：新增 v0.2.0 节。
- 同步 [design.md](../design.md) 上述段落。

**不包含**
- Marketplace 打包 / `claude plugin install specguard`（保留 design.md §6）。
- Cursor / Codex / generic adapter。
- `/specguard:check semantic` 真实 review package 验收。
- skill pressure tests。
- PR bot / GitHub Action 治理报告。

## 2. 验收标准

每条验收都要给出 `命中改动点 → 验证手段 → 期望结果`。

1. **GitHub Release 构建**：在 fork 仓库打 tag `v0.2.0-test`，workflow 产出 3 个 tarball 上传到 release 页面；下载 `specguard-claude-specguard-default-v0.2.0-test.tar.gz` 解包后，根目录直接是 plugin 结构（`.claude-plugin/plugin.json` 等）。覆盖 #1。
2. **plugin.json version 正确**：tarball 内 `.claude-plugin/plugin.json` 的 `version` 字段等于 tag 中的 `0.2.0-test`（来自 `core/version`）。覆盖 #1、#11。
3. **init 自动合并（空 settings.json）**：在 fixture 项目无 `.claude/settings.json` 情况下调用 `specguard.hooks_merge`，结束后 `.claude/settings.json` 含 SessionStart/PreToolUse/Stop/UserPromptSubmit 4 个 event 的 specguard 条目，且 `.specguard/hooks.snippet.json` 内容一致。覆盖 #4、#5、#8。
4. **init 自动合并（已有非 specguard hooks）**：fixture 项目 `.claude/settings.json` 已含一条非 specguard SessionStart hook，调用 `specguard.hooks_merge` 后该条原样保留，specguard 条目追加在数组末尾。覆盖 #4、#5、#8。
5. **init 幂等**：在 #4 状态下再调用一次 `specguard.hooks_merge`，settings.json 内容不变（specguard 条目不重复，文件 byte-equal 或 JSON-equal）。覆盖 #4、#5、#8。
6. **init dry-run**：调用 `specguard.hooks_merge` 的 dry-run 路径时不创建任何文件（包括 `.specguard/`、`.claude/settings.json`、`docs/...`），但输出包含 diff。覆盖 #4、#6、#8。
7. **init 非法 settings.json**：fixture 项目 `.claude/settings.json` 是非法 JSON 时，`specguard.hooks_merge` 报错并指向手工修复路径，原文件未被覆盖。覆盖 #4、#5、#8。
8. **`.specguard-version` 含 plugin_source**：通过 release tarball 安装时为 `github-release-v0.2.0`，本地 dogfood 时为 `local-dist`。覆盖 #2。
9. **check 升级**：fixture 项目缺 specguard hooks 时 `/specguard:check` 输出 ❌（error）而非 ⚠️（warning），summary `errors >= 1`。覆盖 #7。
10. **upgrade dogfood v0.1.0 → v0.2.0**：在 v0.1.0 fixture 项目（包含 v0.1.0 状态的 CLAUDE.md 块、TEMPLATE 文件、settings.json hooks、`.specguard-version` 无 `plugin_source`）上调用 `specguard.upgrade`：
    - design.md 内容未被改动；
    - CLAUDE.md `<!-- specguard:start -->` ↔ `<!-- specguard:end -->` 之间内容已替换为 v0.2.0 版本，marker 外原样；
    - settings.json 中 `statusMessage` 前缀 `specguard:` 的 hook 条目被替换，其它 hook 原样；
    - `specs/TEMPLATE.md`、`decisions/TEMPLATE.md`、`decisions/README.md` 规则段被替换；
    - `.specguard-version` 更新为 `0.2.0`，且补齐 `plugin_source = "local-dist"`（dogfood 上下文）。覆盖 #9、#10、#11、#12。
11. **upgrade marker 缺失 conflict**：fixture CLAUDE.md 缺 specguard 标记时，`specguard.upgrade` 报 conflict 并输出 manual patch，不修改文件。覆盖 #9、#10。
12. **README 用户视角**：README 第一段 quickstart 不再要求 `git clone <this repo>`；改为 `curl -L ... | tar -xz` + `claude --plugin-dir`；development 段保留 render 流程。覆盖 #3。
13. **测试矩阵**：`uv run pytest` 全绿，新增的 2 个测试文件被 collect 到。覆盖 #8、#12。

## 3. 留给后续切片的事

- Marketplace / `claude plugin install specguard` 评估（v0.3+）。
- Cursor / Codex / generic adapter（v0.3+）。
- `/specguard:check semantic` 真实 review package 端到端验收。
- skill pressure tests（治理铁律的对抗测试）。
- PR bot / GitHub Action 治理报告（CI 强制治理）。
- 跨 layout 的 release artifact signing / checksum（如需要）。
