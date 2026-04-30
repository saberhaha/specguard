# specguard init

You are specguard init. Initialize governance scaffolding in the current project.

This command prompt is rendered for a specific layout. All paths below are already concrete (e.g. `docs/superpowers/design.md`), and all template/asset content is embedded literally in the sections that follow. **Do not search the plugin directory at runtime — copy from the embedded sections.**

## Arguments

User-provided: $ARGUMENTS
Supported flags:
- `--ai <claude|cursor|codex|generic|auto>`   default: auto
- `--spec <none|openspec|superpowers|auto>`   default: auto

If the resolved layout is not the one this command was rendered for (paths in this prompt assume `{{ paths.design }}`), tell the user to re-install the matching layout's plugin instead of trying to remap paths at runtime.

## Steps

1. Parse arguments. If `auto`, detect:
   - agent: presence of `.claude/`, `.cursor/`, `AGENTS.md`
   - spec: presence of `openspec/`, `docs/superpowers/`
   - If multiple detected, ask user to choose; do not silently fallback.

2. Confirm layout matches this rendered prompt. The expected paths are:
   - design: `{{ paths.design }}`
   - decisions_dir: `{{ paths.decisions_dir }}`
   - specs_dir: `{{ paths.specs_dir }}`
   - plans_dir: `{{ paths.plans_dir }}`

3. For each of the four target files below: if it exists, skip and report; if missing, create it with the embedded content. Use `Write` (do not modify existing files in this step).
   - `{{ paths.design }}` ← embedded section "design.md template"
   - `{{ paths.decisions_dir }}/README.md` ← embedded section "decisions README template"
   - `{{ paths.decisions_dir }}/TEMPLATE.md` ← embedded section "ADR template"
   - `{{ paths.specs_dir }}/TEMPLATE.md` ← embedded section "spec template"

4. Update `CLAUDE.md` (project root):
   - If the file does not exist, create it with just the specguard block from "CLAUDE.md block" below.
   - If it exists and already contains `<!-- specguard:start -->` / `<!-- specguard:end -->` markers, replace the block content (including markers) with the new block.
   - If it exists without markers, prepend the specguard block to the top, leaving existing content untouched below.
   - Do not touch any content outside the markers.

5. Hooks snippet for `.claude/settings.json`:
   - Write the embedded JSON below verbatim to `.specguard/hooks.snippet.json`. Create the `.specguard/` directory if needed.
   - Do **not** modify the existing `.claude/settings.json`. Claude Code restricts that file for safety; auto-merging it from a slash command is not reliable.
   - In your final report, instruct the user to manually merge `.specguard/hooks.snippet.json` into `.claude/settings.json` (top-level `hooks` key, additive merge by event name; entries are idempotent because each carries a `statusMessage` starting with `specguard:`).

6. Write `.specguard-version` (project root) verbatim, substituting only the `installed_at` field with the current ISO 8601 UTC timestamp:
   ```toml
   specguard_version = "{{ specguard_version }}"
   agent = "claude"
   spec = "{{ layout_name }}"
   layout = "{{ layout_name }}"
   installed_at = "<ISO 8601 UTC now>"
   ```

7. Output a structured report:
   - Created: <files>
   - Updated: <files>
   - Skipped: <files with reason>
   - Next steps: read `{{ paths.design }}`, then merge `.specguard/hooks.snippet.json` into `.claude/settings.json`, then run `/specguard:check`.

---

## Embedded asset: CLAUDE.md block

Wrap the following content between `<!-- specguard:start -->` and `<!-- specguard:end -->`.

```markdown
## SpecGuard governance rules

### Five non-negotiable laws
<!-- inject:five-laws -->

### ADR judgement checklist
<!-- inject:adr-checklist -->

### design.md sync rules
<!-- inject:design-sync -->

### Working with the surrounding spec tool
<!-- inject:policy -->
```

If `--spec none`, drop the entire "Working with the surrounding spec tool" subsection.

---

## Embedded asset: design.md template

```markdown
<!-- inject:design-template -->
```

---

## Embedded asset: decisions README template

```markdown
<!-- inject:decisions-readme-template -->
```

---

## Embedded asset: ADR template

```markdown
<!-- inject:decisions-template -->
```

---

## Embedded asset: spec template

```markdown
<!-- inject:specs-template -->
```

---

## Embedded asset: hooks settings.json snippet

This is the verbatim JSON to write to `.specguard/hooks.snippet.json` and then manually merge into `.claude/settings.json`:

```json
<!-- inject:hooks-snippet -->
```
