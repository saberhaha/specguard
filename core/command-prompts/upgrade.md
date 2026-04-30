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

6. On confirm, replace marker contents only. If a marker is missing in a target file:
   - Do NOT auto-insert.
   - Report conflict and offer options: insert new block / show manual patch / skip.

7. Update `.specguard-version` with new version.

8. Print final report.
