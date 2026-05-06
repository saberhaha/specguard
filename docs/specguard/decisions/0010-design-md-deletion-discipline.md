# ADR 0010: design.md 减法纪律——每次修改前主动扫除冗余

**状态**：Accepted
**日期**：2026-05-02
**拍板者**：用户（@saber，对话日期 2026-05-02）
**取代**：—
**相关**：
- ADR-0005（删除 `/specguard:check semantic`）— design.md §8.2 曾复述这条删除，本 ADR 之后不再保留
- ADR-0007（撤回 `/specguard:upgrade`）— design.md §8.2 曾复述四项伪契约删除，本 ADR 之后不再保留
- design.md 顶部引言"本文档只反映'现在是什么'"
- core/rules/design-sync.md（本 ADR 落地处）

## Context

specguard 从 v0.1.0 到 v0.5.0 共 5 个切片，每个切片都做"加法"：

- 写 spec → design.md 加新段
- 撤回功能 → design.md §8.2 加"已删除"
- 发版 → README Status 表加一行历史
- dogfood → design.md §7.3 加命令日志
- 路线图变动 → design.md §8.1 加愿望条目

到 v0.5.0 末（2026-05-02 复盘）发现的真实冗余：

1. design.md §8.2"已删除"段：`/specguard:check semantic` 与 `/specguard:upgrade` 撤回各占一段，**信息已在 ADR-0005 / ADR-0007 完整保留**。design.md 复述属于历史记录，违反"只反映现在是什么"契约。
2. design.md §7.3"必须人工 dogfood"段：累积 v0.3.0 / v0.4.0 / v0.5.0 三次 dogfood 命令日志摘要。**信息属于 CHANGELOG**，design.md 不该承担 dogfood 历史。
3. design.md §8.1"v0.5+ 留位"段：列了 6 条愿望（Cursor adapter、PR bot、中央 dashboard、L2 e2e 测试、多 agent runtime、upgrade 命令）。**愿望不是架构事实**，应在 README 或 GitHub Issues。
4. README Status 表：把"哪一版加进来"当作 status 条目（v0.1.0 MVP / v0.3.0 撤回 upgrade / v0.4.0 marketplace），实质是 changelog。

CLAUDE.md 当前 design-sync 规则只规定**写入**纪律（接口变了必须同步、commit hash 必须更新），没有规定**清理**纪律。AI agent 与人类协作者都倾向只做加法，因为加法是"显得周全"的安全选择。

## Decision

在 `core/rules/design-sync.md` 增加一条减法纪律，作为 design.md 修改时的强制扫描清单。修改后 re-render 三个 layout，让规则随 plugin 注入到每个使用 specguard 的项目的 CLAUDE.md 与 SessionStart additionalContext。

减法纪律的具体规则：

> 每次修改 design.md 前（不论加段还是改段），扫一遍当前文档，下列内容**必须**移到正确位置或删除：
>
> 1. **"曾经存在但已删除/撤回"的功能描述** → 删除。完整决策已在对应 ADR；design.md 只反映"现在是什么"。
> 2. **"未来想做"的愿望清单** → 移到 README 或 GitHub Issues。"当前不支持 X"是边界（留），"未来希望支持 Y"是路线图（删）。
> 3. **历次 dogfood / 验证 / 发版的命令日志** → 移到 CHANGELOG。"如何 dogfood"是策略（留 1-2 行），"上次跑了什么"是历史（删）。
> 4. **"哪一版引入 X"的版本溯源** → 移到 CHANGELOG。Status 表只列当前能力，不列历史。

执行时机：每个切片在 commit design.md 前必须扫一遍。AI agent 在 design.md sync 任务中默认包含这步；人类协作者通过 CLAUDE.md / SessionStart hook 看到这条规则。

## Consequences

- **正面**：
  - design.md 不再混入历史与愿望，保持"当前架构唯一真相"的契约。
  - ADR / CHANGELOG / README 各自承担明确职责，避免三处文档复述同一事实导致漂移。
  - AI agent 与人类协作者都受同一规则约束（写入 CLAUDE.md），不依赖个人偏好或 agent 私有 memory。
- **负面**：
  - 每次切片多一个"减法扫描"步骤，AI agent 容易遗漏；通过 SessionStart additionalContext 注入提醒缓解。
  - 极少数情况下，"已删除功能 + 当前替代方案"的对比叙事在 design.md 里更易读。这种情况可在切片 spec 中显式申请保留，并附加理由；不通过本 ADR 的扫描默认例外。
- **同步更新**：
  - `core/rules/design-sync.md`：追加减法纪律段。
  - `CLAUDE.md`（项目根，specguard 自身使用的 specguard 块）：手动同步，因为本项目的 CLAUDE.md 是 v0.1.0 init 时落地的快照，不会自动更新。
  - `plugins/<layout>/`：CI 在下一次 release 时自动重新 render，把更新后的 design-sync 规则注入新版 plugin。
  - `decisions/README.md` 索引：追加 0010 行。

## 替代方案

- **AI agent 私有 memory**：把规则存到 `~/.claude/projects/.../memory/`。**拒绝**：只对当前 AI agent 的当前用户生效，其他协作者或其他 agent 接手时规则丢失。
- **PreToolUse:Edit hook 强制拦截**：当 Edit 目标是 design.md 时强制扫描。**拒绝**：误判成本高，写入纪律不该到强制拦截的地步；规则文本足够。
- **检测脚本（grep design.md 找 "已删除"/"未来"等关键词）**：**拒绝**：减法判断需要语义理解，正则误杀率高；规则交给 AI agent + 人类执行更合适。
