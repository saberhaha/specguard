# Changelog

## v0.2.0 - 2026-05-01

### Added
- GitHub Release tarball packaging for three Claude layouts (specguard-default, superpowers, openspec-sidecar) via .github/workflows/release.yml.
- `src/specguard/hooks_merge.py`: idempotent merge of `.specguard/hooks.snippet.json` into `.claude/settings.json` by `statusMessage` prefix.
- `src/specguard/upgrade.py`: two-phase replacement of CLAUDE.md block, settings hooks, two TEMPLATE.md files, decisions/README.md rules section, and `.specguard-version`; raises `UpgradeConflict` with copy-paste manual_patch when markers are missing.
- `runtime/specguard/` is bundled into rendered plugin so `/specguard:init` and `/specguard:upgrade` import the algorithms via `CLAUDE_PLUGIN_ROOT`.
- `/specguard:init --dry-run` previews changes without writing project files.
- `.specguard-version` carries `plugin_source` (`github-release-vX.Y.Z` or `local-dist`).

### Changed
- `/specguard:check` reports missing specguard hooks as an error.
- README quickstart targets users (download release tarball) instead of developers (clone + render).

### Notes
- Marketplace install is still out of scope (deferred to a later version).

## v0.1.0 - 2026-04-30

Initial design + scaffolding release.

### Added
- core: five laws, ADR checklist, design sync rules
- core: design / ADR / spec templates
- core: init/check/upgrade command prompts
- core: openspec / superpowers integration policies
- layouts: specguard-default, superpowers, openspec-sidecar
- adapters/claude: plugin.json, design-governance skill, three commands, hooks snippet (4 events)
- src/specguard: manifest parser, render pipeline
- tests: manifest parser, three layout renders, dogfood path check

### Not yet
- Cursor / Codex adapter
- Python CLI for direct project install
- Built-in LLM semantic check
- OpenSpec inline layout
- PR bot / GitHub Action
