from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from specguard.hooks_merge import merge_hooks


class UpgradeConflict(ValueError):
    """Raised when a required marker is missing or reversed in a managed file."""

    def __init__(self, message: str, manual_patch: str):
        super().__init__(message)
        self.manual_patch = manual_patch


@dataclass(frozen=True)
class UpgradeResult:
    changed: bool
    diff_summary: str


def upgrade_project(root: Path, replacements: dict[str, Any], dry_run: bool = False) -> UpgradeResult:
    """Two-phase upgrade: read+validate everything, then write everything.

    Phase 1: Read all inputs, validate markers, build updated content in memory.
    Phase 2: Write all files only after all validations succeed.
    """

    # ---------- Phase 1: read, validate, build new content in memory ----------

    # 1. CLAUDE.md: replace between <!-- specguard:start --> and <!-- specguard:end -->
    claude_path = root / "CLAUDE.md"
    if not claude_path.exists():
        patch = (
            f"# Manual patch for {claude_path}\n"
            f"CLAUDE.md is missing. Create it with the following content:\n"
            f"<!-- specguard:start -->\n"
            f"{replacements['claude_block']}"
            f"<!-- specguard:end -->\n"
        )
        raise UpgradeConflict(
            f"required file missing: {claude_path}",
            manual_patch=patch,
        )
    claude_original = claude_path.read_text(encoding="utf-8")
    claude_new = _replace_between_markers(
        claude_original,
        "<!-- specguard:start -->",
        "<!-- specguard:end -->",
        replacements["claude_block"],
        str(claude_path),
    )

    # 2. .claude/settings.json: merge specguard hooks
    settings_path = root / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in {settings_path}: {exc}") from exc
    else:
        settings = {"hooks": {}}
    if not isinstance(settings, dict):
        raise ValueError(f"settings.json must be a JSON object: {settings_path}")
    merged_settings = merge_hooks(settings, replacements["settings_hooks"])
    settings_new = json.dumps(merged_settings, indent=2, sort_keys=True) + "\n"

    # 3. docs/specguard/specs/TEMPLATE.md: full replacement
    specs_template_path = root / "docs" / "specguard" / "specs" / "TEMPLATE.md"
    specs_template_new = replacements["specs_template"]

    # 4. docs/specguard/decisions/TEMPLATE.md: full replacement
    decisions_template_path = root / "docs" / "specguard" / "decisions" / "TEMPLATE.md"
    decisions_template_new = replacements["decisions_template"]

    # 5. docs/specguard/decisions/README.md: replace between marker lines
    decisions_readme_path = root / "docs" / "specguard" / "decisions" / "README.md"
    if not decisions_readme_path.exists():
        patch = (
            f"# Manual patch for {decisions_readme_path}\n"
            f"decisions/README.md is missing. Create it with the following content:\n"
            f"<!-- specguard:rules:start -->\n"
            f"{replacements['decisions_readme_rules']}"
            f"<!-- specguard:rules:end -->\n"
        )
        raise UpgradeConflict(
            f"required file missing: {decisions_readme_path}",
            manual_patch=patch,
        )
    decisions_readme_original = decisions_readme_path.read_text(encoding="utf-8")
    decisions_readme_new = _replace_between_markers(
        decisions_readme_original,
        "<!-- specguard:rules:start -->",
        "<!-- specguard:rules:end -->",
        replacements["decisions_readme_rules"],
        str(decisions_readme_path),
    )

    # 6. .specguard-version: update/add specguard_version and plugin_source
    version_path = root / ".specguard-version"
    version_original = version_path.read_text(encoding="utf-8") if version_path.exists() else ""
    version_new = _update_version_file(
        version_original,
        replacements["version"],
        replacements["plugin_source"],
    )

    # ---------- Phase 2: write only changed files ----------

    settings_current = settings_path.read_text(encoding="utf-8") if settings_path.exists() else ""
    specs_current = specs_template_path.read_text(encoding="utf-8") if specs_template_path.exists() else ""
    decisions_template_current = decisions_template_path.read_text(encoding="utf-8") if decisions_template_path.exists() else ""

    changed = (
        claude_new != claude_original
        or settings_new != settings_current
        or specs_template_new != specs_current
        or decisions_template_new != decisions_template_current
        or decisions_readme_new != decisions_readme_original
        or version_new != version_original
    )

    changed_regions: list[str] = []
    if claude_new != claude_original:
        changed_regions.append("CLAUDE.md specguard block")
    if settings_new != settings_current:
        changed_regions.append(".claude/settings.json specguard hooks")
    if specs_template_new != specs_current:
        changed_regions.append("docs/specguard/specs/TEMPLATE.md")
    if decisions_template_new != decisions_template_current:
        changed_regions.append("docs/specguard/decisions/TEMPLATE.md")
    if decisions_readme_new != decisions_readme_original:
        changed_regions.append("docs/specguard/decisions/README.md rules")
    if version_new != version_original:
        changed_regions.append(".specguard-version")

    diff_summary = _build_diff_summary(
        _read_installed_version(version_original),
        replacements["version"],
        changed_regions,
    )

    if dry_run:
        return UpgradeResult(changed=changed, diff_summary=diff_summary)

    if claude_new != claude_original:
        claude_path.write_text(claude_new, encoding="utf-8")

    if settings_new != settings_current:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(settings_new, encoding="utf-8")

    if specs_template_new != specs_current:
        specs_template_path.parent.mkdir(parents=True, exist_ok=True)
        specs_template_path.write_text(specs_template_new, encoding="utf-8")

    if decisions_template_new != decisions_template_current:
        decisions_template_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_template_path.write_text(decisions_template_new, encoding="utf-8")

    if decisions_readme_new != decisions_readme_original:
        decisions_readme_path.write_text(decisions_readme_new, encoding="utf-8")

    if version_new != version_original:
        version_path.write_text(version_new, encoding="utf-8")

    return UpgradeResult(changed=changed, diff_summary=diff_summary)


def _replace_between_markers(text: str, start_marker: str, end_marker: str, new_content: str, source: str) -> str:
    """Replace content between start_marker and end_marker lines, preserving the marker lines themselves.

    Raises UpgradeConflict if either marker is missing or they appear in reversed order.
    """
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        patch = (
            f"# Manual patch for {source}\n"
            f"Insert the following block at an appropriate location:\n"
            f"{start_marker}\n"
            f"{new_content}"
            f"{end_marker}\n"
        )
        raise UpgradeConflict(
            f"required markers not found in {source}: "
            f"start={start_marker!r} found={start_idx != -1}, "
            f"end={end_marker!r} found={end_idx != -1}",
            manual_patch=patch,
        )

    if end_idx < start_idx:
        patch = (
            f"# Manual patch for {source}\n"
            f"Markers appear in reversed order. Re-insert the block in the correct order:\n"
            f"{start_marker}\n"
            f"{new_content}"
            f"{end_marker}\n"
        )
        raise UpgradeConflict(
            f"markers appear in reversed order in {source}: "
            f"start_marker at {start_idx}, end_marker at {end_idx}",
            manual_patch=patch,
        )

    # Find end of the start marker line (include its trailing newline)
    start_line_end = text.find("\n", start_idx)
    if start_line_end == -1:
        start_line_end = len(text)
    else:
        start_line_end += 1  # include the newline

    # The end_marker line starts at end_idx; keep it (and its newline) in the result
    before = text[:start_line_end]
    after = text[end_idx:]

    return before + new_content + after


def _update_version_file(text: str, version: str, plugin_source: str) -> str:
    """Update specguard_version and plugin_source in .specguard-version, preserving other lines."""
    lines = text.splitlines(keepends=True)
    version_set = False
    plugin_source_set = False
    result: list[str] = []

    for line in lines:
        if re.match(r'^specguard_version\s*=', line):
            result.append(f'specguard_version = "{version}"\n')
            version_set = True
        elif re.match(r'^plugin_source\s*=', line):
            result.append(f'plugin_source = "{plugin_source}"\n')
            plugin_source_set = True
        else:
            result.append(line)

    if not version_set:
        result.append(f'specguard_version = "{version}"\n')
    if not plugin_source_set:
        result.append(f'plugin_source = "{plugin_source}"\n')

    return "".join(result)


def _read_installed_version(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r'^specguard_version\s*=\s*["\']([^"\']+)["\']', line)
        if match:
            return match.group(1)
    return "unknown"


def _build_diff_summary(old_version: str, new_version: str, changed_regions: list[str]) -> str:
    lines = [f"SpecGuard upgrade {old_version} → {new_version}", ""]
    if changed_regions:
        lines.append("Will update:")
        lines.extend(f"✓ {region}" for region in changed_regions)
    else:
        lines.append("No changes required.")
    lines.extend(
        [
            "",
            "Will not touch:",
            "- docs/specguard/design.md content",
            "- existing ADR files",
            "- existing spec files",
        ]
    )
    return "\n".join(lines) + "\n"
