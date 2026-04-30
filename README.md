# specguard

> **WIP — design phase only**

specguard is a project governance scaffold for AI-driven development. It installs a *living design + ADR* system into a project, plus optional skill/commands/hooks for AI coding agents.

It is:

- agent-neutral (Claude Code first, Cursor / Codex / generic later)
- spec-tool-neutral (works with OpenSpec, Superpowers, or none)
- delivered as scaffolding (`/sg:init`), not a daily CLI

This repository is currently in the design phase. See:

- [docs/specguard/design.md](docs/specguard/design.md) — living architecture document (WIP)
- [docs/specguard/decisions/](docs/specguard/decisions/) — architecture decision records
- [docs/specguard/specs/](docs/specguard/specs/) — implementation slice specs

The first slice is described in [docs/specguard/specs/2026-04-30-mvp-scaffold-spec.md](docs/specguard/specs/2026-04-30-mvp-scaffold-spec.md).

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
| Brainstorm | done |
| Slice spec | done |
| Implementation plan | done |
| Code | v0.1.0 |
| Public release | not yet |

This README will be replaced with a real product README once the MVP is implemented.

## Quickstart (developers)

```bash
git clone <this repo>
cd specguard
uv sync
uv run pytest
uv run specguard-render --target claude --layout specguard-default --out dist/claude/default
```

The rendered plugin is under `dist/claude/<layout>/`. To install locally, copy that directory into your Claude Code plugin path (e.g. `~/.claude/plugins/specguard/`), then in any target project run `/sg:init --ai claude --spec <none|openspec|superpowers>`. Marketplace packaging is out of MVP scope.
