# specguard check

Validate the governance state of the current project.

## Arguments

User-provided: $ARGUMENTS
Optional positional: `semantic` (generates AI review package; does not call any LLM)

## Structural checks

1. `{{ paths.design }}` exists.
2. No file matching `{{ paths.specs_dir }}/*-design.md` for default/openspec layouts. For `superpowers` layout, treat pre-existing `*-design.md` files as warnings (legacy superpowers snapshots) rather than errors; new work should use `*-spec.md`.
3. `{{ paths.decisions_dir }}/README.md` exists.
4. Every ADR file matches `^[0-9]{4}-[a-z0-9-]+\.md$` or is `README.md` / `TEMPLATE.md`.
5. ADR numbers are contiguous (no gaps).
6. Every ADR appears in `{{ paths.decisions_dir }}/README.md` index.
7. Every ADR-NNNN referenced in `{{ paths.design }}` exists.
8. Every `Superseded by ADR-NNNN` target exists.
9. Every `*.md` under `{{ paths.specs_dir }}` (excluding `TEMPLATE.md` and pre-existing files older than `.specguard-version` `installed_at` if available) contains the heading `## ADR 级别决策识别`. For `superpowers` layout, files matching `*-design.md` are legacy snapshots and exempt from this requirement (warning only).
10. `CLAUDE.md` contains `<!-- specguard:start -->` and `<!-- specguard:end -->`.
11. `.specguard/hooks.snippet.json` exists.
12. `.claude/settings.json` contains hooks tagged with `statusMessage` prefix `specguard:` matching `.specguard/hooks.snippet.json`; if missing, report a warning with manual merge instructions, not a hard error.
13. `.specguard-version` exists.

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

## Semantic mode

If argument `semantic` is provided, additionally:
1. Create `.specguard/reviews/<UTC YYYYMMDD-HHMM>/`
2. Write `prompt.md`: instructions for an LLM to review ADR Context plausibility, missed ADR judgement, design.md drift.
3. Write `context.md`: assembled excerpts from design.md, decisions index, latest spec, latest plan.
4. Write `findings-template.md`: structured output format for the LLM.
5. Do NOT call any LLM. Tell the user to feed `prompt.md + context.md` to Claude Code / Cursor / any LLM.
