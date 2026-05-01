# Changelog

## v0.4.0 - 2026-05-01

### Added

- `.claude-plugin/marketplace.json`: declares specguard marketplace with three plugin entries (`specguard-default`, `specguard-superpowers`, `specguard-openspec-sidecar`) using `git-subdir` source pointing to same-repo `plugins/<layout>/`. Users can now install via `claude plugin marketplace add saberhaha/specguard` + `claude plugin install <name>@specguard`.
- `plugins/specguard-default/`, `plugins/superpowers/`, `plugins/openspec-sidecar/`: rendered plugin trees committed to git (required because Claude Code marketplace does not support GitHub Release tarball as plugin source).
- Release workflow auto-renders `plugins/<layout>/`, pull-rebases main, commits with `--allow-empty`, and pushes `HEAD:main` before building tarballs. Marketplace stays synchronized with source on every tag (ADR-0008).

### Changed

- README quickstart now leads with marketplace install; tarball download moved to "Alternative" section for offline / restricted-network use.
- Status table records v0.4.0 marketplace shipping.

### Notes

- GitHub Release tarball distribution is preserved as fallback **and remains the recommended quickstart in v0.4.0** because of the limitations below.
- Local development still uses `--plugin-dir dist/claude/<layout>` after `uv run specguard-render`.

### Known limitations (Claude Code v2.1.123, verified 2026-05-01)

1. Marketplace-installed plugins are not exposed via `CLAUDE_PLUGIN_ROOT`. `/specguard:init` therefore stops before merging hooks; use the tarball quickstart for full auto-merge.
2. `claude plugin install` for multiple plugins under the same marketplace can briefly fail with `ENOTEMPTY: directory not empty` on the cache directory; a retry typically succeeds.

Both limitations are upstream Claude Code issues and not specguard bugs.

## v0.3.0 - 2026-05-01

### BREAKING

Withdrew `/specguard:upgrade` command and simplified data contracts (ADR-0007 supersedes ADR-0006).

#### Removed
- `/specguard:upgrade` command, prompt, Python runtime module (`upgrade.py`), and all upgrade tests.
- `.specguard-version` file (no longer written by init or checked by check).
- `.plugin_source` provenance marker (no longer stamped into release tarball).
- `.specguard/hooks.snippet.json` intermediate file (init now uses a tempfile for hooks merge).
- `<!-- specguard:rules:start -->` / `<!-- specguard:rules:end -->` markers in `decisions/README.md`.
- `/specguard:check` items 11 (hooks.snippet.json), 12 (settings.json hooks error), 13 (.specguard-version). Check now has 11 structural items.

#### Changed
- `/specguard:init` hooks merge uses a tempfile instead of writing `.specguard/hooks.snippet.json`.
- `/specguard:check` item 11 now validates `.claude/settings.json` contains `specguard:` hooks (previously item 12 with error-level severity; now a simple check).
- Release tarball no longer contains `.plugin_source` file.

#### Migration from v0.2.x
- Delete `.specguard-version` from your project root (if present).
- Delete `.specguard/hooks.snippet.json` (if present).
- Delete `.plugin_source` from your plugin directory (if present).
- Remove `<!-- specguard:rules:start -->` and `<!-- specguard:rules:end -->` markers from `decisions/README.md` (keep the content between them).
- Re-run `/specguard:init` to update `CLAUDE.md` and hooks.

## v0.2.1 - 2026-05-01

### Changed
- `/specguard:check` no longer accepts the v0.1 `semantic` review package mode; semantic findings should be produced in the current Claude conversation rather than written to `.specguard/reviews/`.
- `/specguard:upgrade` now stops when `.specguard-version` is missing, short-circuits with `already up to date` when the installed version equals the plugin version, and requires a dry-run diff summary plus user confirmation before writing files.

### Fixed
- README Development instructions now clone `https://github.com/saberhaha/specguard.git` instead of using a placeholder URL.
- `/specguard:init` embedded hooks snippet wording now matches the auto-merge behavior implemented by `specguard.hooks_merge`.

## v0.2.0 - 2026-05-01

### Added
- GitHub Release tarball packaging for three Claude layouts (specguard-default, superpowers, openspec-sidecar) via .github/workflows/release.yml; release workflow writes `.plugin_source = github-release-v<version>` into each tarball and fails fast if the pushed tag does not match `core/version`.
- `src/specguard/hooks_merge.py`: idempotent merge of `.specguard/hooks.snippet.json` into `.claude/settings.json` by `statusMessage` prefix.
- `src/specguard/upgrade.py`: two-phase replacement of CLAUDE.md block, settings hooks, two TEMPLATE.md files, decisions/README.md rules section, and `.specguard-version`; raises `UpgradeConflict` with copy-paste manual_patch when markers or required files are missing, and no-ops without rewriting unchanged files.
- `runtime/specguard/` is bundled into rendered plugin so `/specguard:init` and `/specguard:upgrade` import the algorithms via `CLAUDE_PLUGIN_ROOT`; `/specguard:upgrade` now embeds the templates and hooks snippet it needs to construct runtime replacements.
- `/specguard:init --dry-run` previews changes without writing project files.
- `.specguard-version` carries `plugin_source` (`github-release-vX.Y.Z` or `local-dist`).

### Changed
- `/specguard:check` reports missing specguard hooks as an error.
- README quickstart targets users (download release tarball) instead of developers (clone + render).

### Notes
- Marketplace install is still out of scope (deferred to a later version).
- v0.1.x projects upgrading to v0.2.0 may need to apply the `UpgradeConflict.manual_patch` for `decisions/README.md` once, because v0.2.0 introduces the `<!-- specguard:rules:start -->` / `<!-- specguard:rules:end -->` managed rule markers.

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
