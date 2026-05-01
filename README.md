# specguard

> Project governance scaffold for AI-driven development. Living design + ADR + spec discipline, delivered as a Claude Code plugin (Cursor / Codex coming later).

specguard is:

- agent-neutral (Claude Code first)
- spec-tool-neutral (works with OpenSpec, Superpowers, or none)
- delivered as scaffolding (`/specguard:init`), not a daily CLI

## Quickstart (users)

Download a Claude plugin tarball from the latest GitHub Release and unpack it somewhere stable:

```bash
mkdir -p ~/.local/share/specguard/plugins/specguard-default
curl -L https://github.com/saberhaha/specguard/releases/latest/download/specguard-claude-specguard-default-v0.4.0.tar.gz \
  | tar -xz -C ~/.local/share/specguard/plugins/specguard-default
```

Run init from inside the target project (a real git repo):

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default \
  -p '/specguard:init --ai claude --spec none'
```

`/specguard:init` creates the living design / ADR / spec scaffold, updates `CLAUDE.md`, and merges hooks into `.claude/settings.json` automatically. Use `--dry-run` to preview without writing.

Run governance check anytime:

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default \
  -p '/specguard:check'
```

Available layouts:

- `specguard-default` — design/ADR/spec under `docs/specguard/`
- `superpowers` — design/ADR/spec under `docs/superpowers/`
- `openspec-sidecar` — design/ADR under `docs/specguard/`, specs under `openspec/`

### Alternative: marketplace install (preview)

A `.claude-plugin/marketplace.json` is published with three plugins (`specguard-default`, `specguard-superpowers`, `specguard-openspec-sidecar`):

```bash
claude plugin marketplace add saberhaha/specguard
claude plugin install specguard-default@specguard
```

**Known limitations on Claude Code v2.1.123 (verified 2026-05-01):**

1. Marketplace-installed plugins are not exposed via `CLAUDE_PLUGIN_ROOT` — `/specguard:init` will create governance scaffolding but stop before merging hooks. Use the tarball quickstart above for full hook auto-merge.
2. Installing multiple plugins from the same marketplace can hit `ENOTEMPTY` race on the cache directory; retry usually succeeds.

Both limitations are tracked against Claude Code; specguard publishes the marketplace anyway so it's available once those bugs land in a Claude Code release.

## Why

OpenSpec / Spec Kit / Superpowers focus on driving a single AI coding session. specguard focuses on the layer underneath:

- making sure every new conversation reads the current architecture
- preventing AI from re-opening past decisions
- forcing ADR judgement before plans
- catching drift between code and design

It is not a replacement for spec-driven development tools. It is a **governance layer that sits on top of them**.

## Status

| Item | State |
|---|---|
| MVP scaffold | shipped (v0.1.0) |
| Withdraw upgrade + simplify contracts | shipped (v0.3.0) |
| Marketplace install (preview, blocked on Claude Code limitations) | shipped (v0.4.0) |
| Cursor / Codex adapter | not yet |

## Development

Render the plugin from source for local dogfood:

```bash
git clone https://github.com/saberhaha/specguard.git
cd specguard
uv sync
uv run pytest
uv run specguard-render --target claude --layout specguard-default --out dist/claude/specguard-default
claude --plugin-dir dist/claude/specguard-default -p '/specguard:init --ai claude --spec none'
```

See:
- [docs/specguard/design.md](docs/specguard/design.md) — living architecture document
- [docs/specguard/decisions/](docs/specguard/decisions/) — architecture decision records
- [docs/specguard/specs/](docs/specguard/specs/) — implementation slice specs
