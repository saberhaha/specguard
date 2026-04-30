# specguard upgrade

Upgrade specguard scaffolding in the current project to the plugin's current core version.

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

   Then, construct the `replacements` dict from the same rendered assets used by init/check — specifically, read each from its current source (rendered prompt embedded sections or plugin dist) before calling the upgrade function:

   ```python
   # replacements must be built before calling upgrade_project
   replacements = {
       "claude_block": <rendered CLAUDE.md block content, text between specguard markers>,
       "settings_hooks": <rendered hooks JSON snippet content>,
       "specs_template": <rendered specs/TEMPLATE.md content>,
       "decisions_template": <rendered decisions/TEMPLATE.md content>,
       "decisions_readme_rules": <rendered decisions/README.md rule sections content>,
       "version": <current plugin version string>,
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

   If `.specguard-version` is missing `plugin_source`, treat it as `local-dist` and write it back to the file.
   If `UpgradeConflict` is raised for any marker region, output `exc.manual_patch` and ask the user to apply the patch manually before retrying.
   Files outside markers are never touched.

7. Update `.specguard-version` with new version.

8. Print final report.
