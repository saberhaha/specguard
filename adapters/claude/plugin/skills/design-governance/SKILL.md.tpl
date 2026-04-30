---
name: design-governance
description: Use when starting or changing a feature, writing specs or plans, making architecture decisions, updating design docs, creating ADRs, or reviewing whether AI coding work may drift from project architecture
---

# Design Governance

## Overview
specguard enforces living design + ADR governance for AI-assisted projects.
This skill is agent and spec-tool agnostic.

## Non-Negotiables
<!-- inject:five-laws -->

## Required Workflow
1. Read `{{ paths.design }}` and `{{ paths.decisions_dir }}/`.
2. Explore design before implementation.
3. Produce a slice spec containing the `## ADR 级别决策识别` section.
4. Ask the user to approve candidate ADRs.
5. Write a plan only after the spec is approved.
6. Sync `{{ paths.design }}` after interface/data/boundary changes.

## ADR Decision Assessment
<!-- inject:adr-checklist -->

## design.md Sync Rules
<!-- inject:design-sync -->

## When NOT to Write ADR
- Tasks
- Implementation details
- Parameter defaults
- Naming choices
- First implementation of an existing design

## Common Mistakes
- Creating new dated design files
- Writing ADR for every task
- Treating design.md as historical archive instead of current truth
- Skipping ADR assessment before plan
