# specguard init

You are specguard init. Initialize governance scaffolding in the current project.

This command prompt is rendered for a specific layout. All paths below are already concrete (e.g. `docs/superpowers/design.md`), and all template/asset content is embedded literally in the sections that follow. **Do not search the plugin directory at runtime — copy from the embedded sections.**

## Arguments

User-provided: $ARGUMENTS
Supported flags:
- `--ai <claude|cursor|codex|generic|auto>`   default: auto
- `--spec <none|openspec|superpowers|auto>`   default: auto
- `--dry-run`                                 default: false; print planned file writes and hook merge diff without writing files

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

3. For each of the four target files below: if it exists, skip and report; if missing and not `--dry-run`, create it with the embedded content. If `--dry-run`, report each missing file as would-create and do not write it. Use `Write` (do not modify existing files in this step).
   - `{{ paths.design }}` ← embedded section "design.md template"
   - `{{ paths.decisions_dir }}/README.md` ← embedded section "decisions README template"
   - `{{ paths.decisions_dir }}/TEMPLATE.md` ← embedded section "ADR template"
   - `{{ paths.specs_dir }}/TEMPLATE.md` ← embedded section "spec template"

4. Update `CLAUDE.md` (project root):
   - If the file does not exist, create it with just the specguard block from "CLAUDE.md block" below.
   - If it exists and already contains `<!-- specguard:start -->` / `<!-- specguard:end -->` markers, replace the block content (including markers) with the new block.
   - If it exists without markers, prepend the specguard block to the top, leaving existing content untouched below.
   - Do not touch any content outside the markers.
   - If `--dry-run`, report the CLAUDE.md diff and do not write.

5. Hooks merge for `.claude/settings.json`:
   - Use the embedded JSON below verbatim as the snippet source.
   - Unless `--dry-run`, write it verbatim to `.specguard/hooks.snippet.json`. Create the `.specguard/` directory if needed.
   - Resolve the plugin runtime directory from the environment variable `CLAUDE_PLUGIN_ROOT`. If the variable is not set, stop and tell the user: "CLAUDE_PLUGIN_ROOT is not set — your Claude Code version or plugin runtime does not expose the plugin root. Cannot locate specguard runtime."
   - Merge the hooks by invoking the runtime module from the resolved plugin root. Use the following Python snippet (or equivalent short script):

     ```python
     import os
     import sys
     from pathlib import Path
     plugin_root = Path(os.environ["CLAUDE_PLUGIN_ROOT"])
     sys.path.insert(0, str(plugin_root / "runtime"))
     from specguard.hooks_merge import merge_hooks_file
     result = merge_hooks_file(Path(".claude/settings.json"), Path(".specguard/hooks.snippet.json"), dry_run=False)
     print(result.diff)
     ```

   - If `--dry-run`, do **not** write `.specguard/hooks.snippet.json`. Instead, write the embedded hooks JSON to a temporary file and pass that temp path to `merge_hooks_file` with `dry_run=True`:

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
     result = merge_hooks_file(Path(".claude/settings.json"), tmp_path, dry_run=True)
     print(result.diff)
     ```

   - On invalid settings JSON or `HookMergeError`, stop and ask the user to fix the issue manually before retrying.

6. Write `.specguard-version` (project root) verbatim, substituting `installed_at` with the current ISO 8601 UTC timestamp and `plugin_source` as computed below.

   Compute `plugin_source` from the marker file shipped inside the plugin:
   ```python
   marker = plugin_root / ".plugin_source"
   plugin_source = marker.read_text(encoding="utf-8").strip() if marker.exists() else "local-dist"
   # possible literal values: "github-release-v<version>" (tarball install) or "local-dist" (dev install)
   ```

   Then write:
   ```toml
   specguard_version = "{{ specguard_version }}"
   agent = "claude"
   spec = "{{ layout_name }}"
   layout = "{{ layout_name }}"
   installed_at = "<ISO 8601 UTC now>"
   plugin_source = "<computed above>"
   ```

7. Output a structured report:
   - Created: <files>
   - Updated: <files>
   - Skipped: <files with reason>
   - Hooks: auto-merged specguard hooks into `.claude/settings.json` via `specguard.hooks_merge`.
   - Next steps: read `{{ paths.design }}`, then run `/specguard:check`.

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
