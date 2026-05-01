# specguard upgrade

Upgrade specguard scaffolding in the current project to the plugin's current core version.

This command prompt is rendered for a specific layout. All embedded asset sections below contain the actual content to use at runtime. **Do not search the plugin directory at runtime — use from the embedded sections.**

## Steps

1. Read `.specguard-version`. If missing, ask user whether to treat project as legacy and run init-then-upgrade.

2. Compare `specguard_version` to plugin's `core/version`. If equal, output "already up to date" and exit.

3. Build upgrade plan by inspecting marker regions:
   - `CLAUDE.md` block between `<!-- specguard:start -->` and `<!-- specguard:end -->`
   - `.claude/settings.json` hooks identifiable by `statusMessage` prefix `specguard:`
   - `{{ paths.specs_dir }}/TEMPLATE.md`
   - `{{ paths.decisions_dir }}/TEMPLATE.md`
   - `{{ paths.decisions_dir }}/README.md` rule sections

4. Print diff summary per region. Files outside markers are never touched. Summary format:

```
SpecGuard upgrade <old> → <new>

Will update:
✓ CLAUDE.md specguard block (3 lines changed)
✓ specs/TEMPLATE.md (added new required field)
✓ UserPromptSubmit hook command updated

Will not touch:
- design.md content
- existing ADR files
- existing spec files
```

5. Ask user to confirm.

6. On confirm, call `specguard.upgrade` from the rendered plugin `runtime/` directory.

   First, resolve the plugin runtime directory from the environment variable `CLAUDE_PLUGIN_ROOT`. If the variable is not set, stop and tell the user: "CLAUDE_PLUGIN_ROOT is not set — your Claude Code version or plugin runtime does not expose the plugin root. Cannot locate specguard runtime."

   Construct `replacements` by reading from the embedded asset sections of THIS command file:

   ```python
   # replacements must be built before calling upgrade_project
   replacements = {
       "claude_block": <text inside the embedded "CLAUDE.md block" section between <!-- specguard:start --> and <!-- specguard:end --> markers>,
       "settings_hooks": json.loads(<text inside the embedded "hooks settings.json snippet" section between the ```json fences>),
       "specs_template": <text inside the embedded "spec template" section between the ```markdown fences>,
       "decisions_template": <text inside the embedded "ADR template" section between the ```markdown fences>,
       "decisions_readme_rules": <text inside the embedded "decisions README template" section between <!-- specguard:rules:start --> and <!-- specguard:rules:end --> markers>,
       "version": (plugin_root / "version").read_text(encoding="utf-8").strip(),
       "plugin_source": <value from .specguard-version plugin_source field, default "local-dist">,
   }
   ```

   Then invoke:

   ```python
   import os
   import sys
   from pathlib import Path
   plugin_root = Path(os.environ["CLAUDE_PLUGIN_ROOT"])
   sys.path.insert(0, str(plugin_root / "runtime"))
   from specguard.upgrade import upgrade_project, UpgradeConflict

   try:
       result = upgrade_project(Path("."), replacements)
       print("Upgraded:", result.changed)
   except UpgradeConflict as exc:
       print(exc.manual_patch)  # output manual_patch to the user for manual resolution
   ```

   If `.specguard-version` is missing `plugin_source`, treat it as `local-dist`.
   If `UpgradeConflict` is raised for any marker region, output `exc.manual_patch` and ask the user to apply the patch manually before retrying.
   Files outside markers are never touched.

7. Confirm `.specguard-version` was updated by `upgrade_project` (the function writes it as part of Phase 2; no separate write step is needed here).

8. Print final report.

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
```

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

This is the verbatim JSON to pass as `settings_hooks` in the replacements dict:

```json
<!-- inject:hooks-snippet -->
```
