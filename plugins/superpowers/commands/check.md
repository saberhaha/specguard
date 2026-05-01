---
description: Check specguard governance state
---

# specguard check

Validate the governance state of the current project.

## Arguments

User-provided: $ARGUMENTS
No positional modes are supported. This command is read-only and does not create review packages or other project files.

## Structural checks

1. `docs/superpowers/design.md` exists.
2. No file matching `docs/superpowers/specs/*-design.md` for default/openspec layouts. For `superpowers` layout, treat pre-existing `*-design.md` files as warnings (legacy superpowers snapshots) rather than errors; new work should use `*-spec.md`.
3. `docs/superpowers/decisions/README.md` exists.
4. Every ADR file matches `^[0-9]{4}-[a-z0-9-]+\.md$` or is `README.md` / `TEMPLATE.md`.
5. ADR numbers are contiguous (no gaps).
6. Every ADR appears in `docs/superpowers/decisions/README.md` index.
7. Every ADR-NNNN referenced in `docs/superpowers/design.md` exists.
8. Every `Superseded by ADR-NNNN` target exists.
9. Every `*.md` under `docs/superpowers/specs` (excluding `TEMPLATE.md`) contains the heading `## ADR 级别决策识别`. For `superpowers` layout, files matching `*-design.md` are legacy snapshots and exempt from this requirement (warning only).
10. `CLAUDE.md` contains `<!-- specguard:start -->` and `<!-- specguard:end -->`.
11. `.claude/settings.json` contains entries tagged with `statusMessage` prefix `specguard:`.

If layout is `openspec-sidecar`, additionally:
- For each archived OpenSpec change, if its `design.md` mentions a decision, warn if `decisions/` has no corresponding ADR.

## Output

Print a structured report:

```
SpecGuard Check (agent=<x>, spec=<x>, layout=<x>)

✓ design.md exists
⚠️ ADR-0005 missing from decisions/README.md index
❌ design.md references ADR-0006 but file does not exist

Summary: 1 error, 1 warning
```
