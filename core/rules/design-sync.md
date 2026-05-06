- 接口、数据结构、模块边界变化 → 必须同步 `{{ paths.design }}` 对应段落（默认动作，不询问）。
- 编辑 `{{ paths.design }}` 后更新顶部 `Last verified against code` 字段为当前 commit hash。
- 不允许在 `{{ paths.design }}` 中保留与代码不一致的陈述。
- mermaid 图与文字描述若不一致，文字为准，同步修图。
- 写 ADR 后，在 `{{ paths.design }}` 对应章节末尾追加 `（见 ADR-NNNN）`，并在 `{{ paths.decisions_dir }}/README.md` 索引表加一行。
- **减法纪律**（每次修改 `{{ paths.design }}` 前扫一遍，发现以下内容必须移走或删除；见 ADR-0010）：
  1. "曾经存在但已删除/撤回"的功能描述 → 删除（完整决策已在对应 ADR；design.md 只反映"现在是什么"）。
  2. "未来想做"的愿望清单 → 移到 README 或 GitHub Issues（"当前不支持 X"是边界保留，"未来希望支持 Y"是路线图删除）。
  3. 历次 dogfood / 验证 / 发版的命令日志 → 移到 CHANGELOG（保留 1-2 行"如何 dogfood"的策略，删除"上次跑了什么"的历史）。
  4. "哪一版引入 X"的版本溯源 → 移到 CHANGELOG（Status 表只列当前能力，不列历史）。
