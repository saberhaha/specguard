---
description: Initialize specguard governance scaffold
argument-hint: "[--ai <agent>] [--spec <tool>] [--dry-run]"
---

# specguard init

You are specguard init. Initialize governance scaffolding in the current project.

This command prompt is rendered for a specific layout. All paths below are already concrete (e.g. `docs/superpowers/design.md`), and all template/asset content is embedded literally in the sections that follow. **Do not search the plugin directory at runtime — copy from the embedded sections.**

## Arguments

User-provided: $ARGUMENTS
Supported flags:
- `--ai <claude|cursor|codex|generic|auto>`   default: auto
- `--spec <none|openspec|superpowers|auto>`   default: auto
- `--dry-run`                                 default: false; print planned file writes and hook merge diff without writing files

If the resolved layout is not the one this command was rendered for (paths in this prompt assume `docs/specguard/design.md`), tell the user to re-install the matching layout's plugin instead of trying to remap paths at runtime.

## Steps

1. Parse arguments. If `auto`, detect:
   - agent: presence of `.claude/`, `.cursor/`, `AGENTS.md`
   - spec: presence of `openspec/`, `docs/superpowers/`
   - If multiple detected, ask user to choose; do not silently fallback.

2. Confirm layout matches this rendered prompt. The expected paths are:
   - design: `docs/specguard/design.md`
   - decisions_dir: `docs/specguard/decisions`
   - specs_dir: `openspec/specs`
   - plans_dir: `docs/specguard/plans`

3. For each of the four target files below: if it exists, skip and report; if missing and not `--dry-run`, create it with the embedded content. If `--dry-run`, report each missing file as would-create and do not write it. Use `Write` (do not modify existing files in this step).
   - `docs/specguard/design.md` ← embedded section "design.md template"
   - `docs/specguard/decisions/README.md` ← embedded section "decisions README template"
   - `docs/specguard/decisions/TEMPLATE.md` ← embedded section "ADR template"
   - `openspec/specs/TEMPLATE.md` ← embedded section "spec template"

4. Update `CLAUDE.md` (project root):
   - If the file does not exist, create it with just the specguard block from "CLAUDE.md block" below.
   - If it exists and already contains `<!-- specguard:start -->` / `<!-- specguard:end -->` markers, replace the block content (including markers) with the new block.
   - If it exists without markers, prepend the specguard block to the top, leaving existing content untouched below.
   - Do not touch any content outside the markers.
   - If `--dry-run`, report the CLAUDE.md diff and do not write.

5. Hooks merge for `.claude/settings.json`:
   - Use the embedded JSON below verbatim as the snippet source.
   - Resolve the plugin runtime directory from the environment variable `CLAUDE_PLUGIN_ROOT`. If the variable is not set, stop and tell the user: "CLAUDE_PLUGIN_ROOT is not set — your Claude Code version or plugin runtime does not expose the plugin root. Cannot locate specguard runtime."
   - Write the embedded hooks JSON to a temporary file. Then merge the hooks by invoking the runtime module from the resolved plugin root:

     ```python
     import os
     import sys
     import tempfile
     from pathlib import Path
     plugin_root = Path(os.environ["CLAUDE_PLUGIN_ROOT"])
     sys.path.insert(0, str(plugin_root / "runtime"))
     from specguard.hooks_merge import merge_hooks_file
     with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
         tmp.write(HOOKS_JSON_CONTENT)
         tmp_path = Path(tmp.name)
     result = merge_hooks_file(Path(".claude/settings.json"), tmp_path, dry_run=DRY_RUN_FLAG)
     print(result.diff)
     ```

   - Set `DRY_RUN_FLAG` to `True` when `--dry-run` is active, `False` otherwise.
   - On invalid settings JSON or `HookMergeError`, stop and ask the user to fix the issue manually before retrying.

6. Output a structured report:
   - Created: <files>
   - Updated: <files>
   - Skipped: <files with reason>
   - Hooks: auto-merged specguard hooks into `.claude/settings.json` via `specguard.hooks_merge`.
   - Next steps: read `docs/specguard/design.md`, then run `/specguard:check`.

---

## Embedded asset: CLAUDE.md block

Wrap the following content between `<!-- specguard:start -->` and `<!-- specguard:end -->`.

```markdown
## SpecGuard governance rules

### Five non-negotiable laws
1. `docs/specguard/design.md` 是当前架构唯一真相；写代码前必须先读它。
2. 决策档案在 `docs/specguard/decisions/`；写新 ADR 前必须先查看既有 ADR。
3. 禁止新建 dated design 文件（如 `*-design.md`）；新切片写 `openspec/specs/<topic>-spec.md`，架构变更直接更新 design.md。
4. ADR 只用于五类硬条件：接口语义、数据格式、跨模块依赖、外部依赖、推翻既有设计；其他默认不写。
5. 接口/数据结构/模块边界变更必须同步 `docs/specguard/design.md`；命中硬条件时还要写 ADR。


### ADR judgement checklist
对本次需求的每个改动点，逐条匹配五条硬条件：

- [ ] 是否改变了某个对外接口的输入/输出/失败语义/调用约束？
- [ ] 是否改变了某个文件格式、数据 schema、字段语义到不向前兼容？
- [ ] 是否新增/移除/反转了模块间依赖关系？
- [ ] 是否新增/替换/移除了第三方库、外部服务、子进程?
- [ ] 是否与 design.md 或既有 ADR 中明确陈述的约束冲突？

任意一条 yes → 候选 ADR。
所有都 no → 不写 ADR，但仍要判断是否需要同步 design.md。

候选 ADR 必须列给用户拍板，AI 不能单方面写架构 ADR。

输出格式（写入切片 spec 的"ADR 级别决策识别"节）：
- 改动点拆解（编号列表）
- 五条硬条件匹配表（表格化）
- 候选 ADR + 灰色地带（请用户拍板）
- 不需要 ADR 的改动点 + 理由


### design.md sync rules
- 接口、数据结构、模块边界变化 → 必须同步 `docs/specguard/design.md` 对应段落（默认动作，不询问）。
- 编辑 `docs/specguard/design.md` 后更新顶部 `Last verified against code` 字段为当前 commit hash。
- 不允许在 `docs/specguard/design.md` 中保留与代码不一致的陈述。
- mermaid 图与文字描述若不一致，文字为准，同步修图。
- 写 ADR 后，在 `docs/specguard/design.md` 对应章节末尾追加 `（见 ADR-NNNN）`，并在 `docs/specguard/decisions/README.md` 索引表加一行。


### Working with the surrounding spec tool
## 与 OpenSpec 协作

OpenSpec 仍按其本身流程使用：proposal / change / archive 在 `openspec/`。
specguard 仅补充以下治理约束：

1. 写 OpenSpec proposal 前，先读 `docs/specguard/design.md` + `docs/specguard/decisions/`。
2. OpenSpec proposal 的 `design.md` 若产生 ADR 级别决策，必须新增 ADR 到 `docs/specguard/decisions/`。
3. OpenSpec change archive 后，若改变当前架构，必须同步 `docs/specguard/design.md`。
4. 长期架构决策不得只留在 `openspec/changes/archive/`，必须沉淀到 ADR。
```

If `--spec none`, drop the entire "Working with the surrounding spec tool" subsection.

---

## Embedded asset: design.md template

```markdown
# {{ project.name | default("Project") }} 设计（Living Document）

**Last verified against code**: {{ today }} @ commit `<HEAD hash>`
**Authoritative for**: 全文
**ADR 索引**: [{{ paths.decisions_dir }}/README.md]({{ paths.decisions_dir | relative_to_design }}/README.md)

> 本文档是项目架构当前真相。代码与本文档不一致即为缺陷。
> 决策动机与历史在 decisions/，本文档只反映"现在是什么"。

---

## 1. 设计方向

（待项目填入。若已有 design 内容，init 时不会覆盖此处。）

---

## 17. 与项目原则的对应

（可选：列出宪法/原则与本文章节的映射）

```

---

## Embedded asset: decisions README template

```markdown
# 决策档案（Architecture Decision Records）

本目录沉淀 {{ project.name | default("项目") }} 的架构决策。

## ADR 五类硬条件

只写以下五类决策：

1. 接口语义改变
2. 数据格式不兼容
3. 跨模块依赖关系改变
4. 外部依赖引入或替换
5. 推翻先前 design 或 ADR

不写 ADR：任务、实现细节、参数默认值、命名、首次实施既有设计。

## 命名规范

- `NNNN-kebab-case-slug.md`，4 位编号连续
- 例外：`README.md`、`TEMPLATE.md`

## 状态字段

- `Accepted` / `Superseded by ADR-NNNN` / `Deprecated`

## ADR 索引

| 编号 | 标题 | 状态 | 关联 design 章节 |
|---|---|---|---|

```

---

## Embedded asset: ADR template

```markdown
# ADR NNNN: <一句话标题>

**状态**：Accepted | Superseded by ADR-NNNN | Deprecated
**日期**：YYYY-MM-DD
**拍板者**：用户（@用户名，对话日期 YYYY-MM-DD，参考 <文档路径> §X）| AI 推理（依据：...）
**取代**：—  或  ADR-NNNN
**相关**：design.md §X / spec docs/.../<file>.md

## Context
（1-3 段：当前情况、约束、为什么现在要决策。
**只允许写本次对话/文档中出现过的事实信息，不允许补全推理动机**。）

## Decision
（1-2 段：决定做什么。简洁，不长篇大论。）

## Consequences
- **正面**：
- **负面**：
- **同步更新**：design.md §X / 哪些代码（具体到文件路径）

```

---

## Embedded asset: spec template

```markdown
# <切片名> 设计补充

**日期**：YYYY-MM-DD
**适用范围**：<明确的切片边界>

## ADR 级别决策识别（必填，不允许空）

### 改动点拆解
1. <具体改动 1>
2. ...

### 五条硬条件匹配
| 改动点 | 接口语义 | 数据格式 | 跨模块依赖 | 外部依赖 | 推翻先前 |
|---|:-:|:-:|:-:|:-:|:-:|
| #1 | - | - | - | - | - |

### 候选 ADR（请用户拍板）
- ADR 候选: <标题> —— 命中条件 X+Y
- 灰色地带: <描述>

### 不需要 ADR
- #1 等：<理由>

## 对 design.md 的影响（必填）
- §X：<具体段落变化>

## 1. 切片范围
## 2. 验收标准
## 3. 留给后续切片的事

```

---

## Embedded asset: hooks settings.json snippet

This is the verbatim JSON used as the hooks snippet source for `specguard.hooks_merge`.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: inject five laws",
            "command": "printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"## SpecGuard governance laws\\n1. docs/specguard/design.md is the single current truth.\\n2. ADR archive is at docs/specguard/decisions/. Read existing ADRs before writing a new one.\\n3. Do not create dated design files. New slices go to *-spec.md.\\n4. ADR is only for: interface semantics, data format, cross-module dependency, external dependency, overriding prior design.\\n5. Brainstorm must produce an ADR judgement before writing a plan.\"}}}'"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: block dated design",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *openspec/specs/*-design.md) printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: dated design files are forbidden. Update docs/specguard/design.md or write openspec/specs/<topic>-spec.md instead.\"}}}' ;; *) printf '%s\\n' '{}' ;; esac"
          },
          {
            "type": "command",
            "statusMessage": "specguard: validate adr filename",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *docs/specguard/decisions/*.md) base=$(basename \"$f\"); if echo \"$base\" | grep -qE '^[0-9]{4}-[a-z0-9-]+\\.md$|^TEMPLATE\\.md$|^README\\.md$'; then printf '%s\\n' '{}'; else printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: ADR filename must be NNNN-kebab-case.md\"}}}'; fi ;; *) printf '%s\\n' '{}' ;; esac"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: design sync reminder",
            "command": "cd \"$CLAUDE_PROJECT_DIR\" 2>/dev/null || exit 0; src_changed=$(git diff --name-only HEAD 2>/dev/null | grep -c '^src/' || true); doc_changed=$(git diff --name-only HEAD 2>/dev/null | grep -cE '^(docs/specguard/design\\.md|docs/specguard/decisions/)' || true); if [ \"$src_changed\" -gt 0 ] && [ \"$doc_changed\" -eq 0 ]; then printf '%s\\n' '{\"systemMessage\":\"specguard: src/ changed but neither design.md nor decisions/ touched.\"}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: adr judgement reminder",
            "command": "p=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"prompt\") or d.get(\"user_prompt\") or \"\")'); if echo \"$p\" | grep -qiE '(write spec|write plan|implement now|开始实施|写 spec|写 plan)'; then printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"specguard: produce the ADR judgement section before entering spec/plan, and wait for user approval.\"}}}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ]
  }
}

```
