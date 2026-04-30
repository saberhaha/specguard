# specguard check

Validate the governance state of the current project.

## Arguments

User-provided: $ARGUMENTS
Optional positional: `semantic` (generates AI review package; does not call any LLM)

## Structural checks

1. `{{ paths.design }}` exists and is the only design file (no other `*-design.md` under specs).
2. No file matching `{{ paths.specs_dir }}/*-design.md`.
3. `{{ paths.decisions_dir }}/README.md` exists.
4. Every ADR file matches `^[0-9]{4}-[a-z0-9-]+\.md$` or is `README.md` / `TEMPLATE.md`.
5. ADR numbers are contiguous (no gaps).
6. Every ADR appears in `{{ paths.decisions_dir }}/README.md` index.
7. Every ADR-NNNN referenced in `{{ paths.design }}` exists.
8. Every `Superseded by ADR-NNNN` target exists.
9. Every `*.md` under `{{ paths.specs_dir }}` (excluding TEMPLATE.md) contains the heading `## ADR 级别决策识别`.
10. `CLAUDE.md` contains `<!-- specguard:start -->` and `<!-- specguard:end -->`.
11. `.claude/settings.json` contains hooks tagged with `statusMessage` prefix `specguard:` matching adapter manifest.
12. `.specguard-version` exists.

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
