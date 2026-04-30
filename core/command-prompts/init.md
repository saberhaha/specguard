# specguard init

You are specguard init. Initialize governance scaffolding in the current project.

## Arguments

User-provided: $ARGUMENTS
Supported flags:
- --ai <claude|cursor|codex|generic|auto>   default: auto
- --spec <none|openspec|superpowers|auto>   default: auto

## Steps

1. Parse arguments. If `auto`, detect:
   - agent: presence of `.claude/`, `.cursor/`, `AGENTS.md`
   - spec: presence of `openspec/`, `docs/superpowers/`
   - If multiple detected, ask user to choose; do not silently fallback.

2. Resolve layout:
   - `--spec none` → layout `specguard-default`
   - `--spec superpowers` → layout `superpowers`
   - `--spec openspec` → layout `openspec-sidecar`

3. For each path in layout (`paths.design`, `paths.decisions_dir`, `paths.specs_dir`, `paths.plans_dir`):
   - If file exists, skip and report.
   - If missing, render template from plugin.

4. Update `CLAUDE.md`:
   - If file exists, look for `<!-- specguard:start -->` ... `<!-- specguard:end -->` block.
   - If block exists, replace its content; if missing, insert block at top.
   - Inside block: render five-laws + adr-checklist + design-sync + (if --spec is openspec or superpowers) the corresponding policy.

5. Update `.claude/settings.json`:
   - Merge specguard hooks (identifiable by `statusMessage` prefix `specguard:`) into existing settings.
   - Do not duplicate hooks already present.

6. Write `.specguard-version`:
   ```toml
   specguard_version = "<plugin core version>"
   agent = "<resolved agent>"
   spec = "<resolved spec>"
   layout = "<resolved layout>"
   installed_at = "<ISO 8601 now>"
   ```

7. Output report:
   - Created: <files>
   - Updated: <files>
   - Skipped: <files with reason>
   - Next steps: read design.md, run /sg:check
