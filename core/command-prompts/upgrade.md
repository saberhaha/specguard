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

6. On confirm, call `specguard.upgrade` from the rendered plugin `runtime/` directory:

   ```python
   import sys; sys.path.insert(0, "runtime")
   from pathlib import Path
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
