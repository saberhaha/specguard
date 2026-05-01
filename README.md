# specguard

> Project governance scaffold for AI-driven development. Living design + ADR + spec discipline, delivered as a Claude Code plugin (Cursor / Codex coming later).

specguard is:

- agent-neutral (Claude Code first)
- spec-tool-neutral (works with OpenSpec, Superpowers, or none)
- delivered as scaffolding (`/specguard:init`), not a daily CLI

## Quickstart (users)

Add the specguard marketplace and install a layout:

```bash
claude plugin marketplace add saberhaha/specguard
claude plugin install specguard-default@specguard
```

Available plugins (one per layout):

- `specguard-default` — design/ADR/spec under `docs/specguard/`
- `specguard-superpowers` — design/ADR/spec under `docs/superpowers/`
- `specguard-openspec-sidecar` — design/ADR under `docs/specguard/`, specs under `openspec/`

Run init from inside the target project (a real git repo):

```bash
claude -p '/specguard:init --ai claude --spec none'
```

`/specguard:init` creates the living design / ADR / spec scaffold, updates `CLAUDE.md`, and merges hooks into `.claude/settings.json` automatically. Use `--dry-run` to preview without writing.

Run governance check anytime:

```bash
claude -p '/specguard:check'
```

### Alternative: download release tarball

For offline / restricted-network / private GitHub Enterprise users where marketplace install is not available:

```bash
mkdir -p ~/.local/share/specguard/plugins/specguard-default
curl -L https://github.com/saberhaha/specguard/releases/latest/download/specguard-claude-specguard-default-v0.4.0.tar.gz \
  | tar -xz -C ~/.local/share/specguard/plugins/specguard-default
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default \
  -p '/specguard:init --ai claude --spec none'
```

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
| Marketplace install (`/plugin install ...@specguard`) | shipped (v0.4.0) |
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
