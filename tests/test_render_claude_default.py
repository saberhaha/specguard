from pathlib import Path

import json
import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    return out


def test_plugin_json_manifest(dist: Path):
    data = json.loads((dist / ".claude-plugin/plugin.json").read_text())
    assert data["name"] == "specguard"
    assert "commandNamespace" not in data


def test_skill_contains_three_injected_sections(dist: Path):
    skill = (dist / "skills/design-governance/SKILL.md").read_text()
    assert "ADR 级别决策识别" not in skill or "spec" in skill.lower()
    # all inject markers replaced
    assert "<!-- inject:" not in skill
    # paths substituted
    assert "{{" not in skill
    # contains content from each rule file
    assert "design.md" in skill
    assert "ADR" in skill


def test_command_files_have_frontmatter(dist: Path):
    for name in ("init", "check", "upgrade"):
        cmd = (dist / f"commands/{name}.md").read_text()
        assert cmd.startswith("---\n")
        assert "<!-- inject:" not in cmd


def test_hooks_snippet_is_valid_json(dist: Path):
    snippet_path = dist / "hooks/settings.json.snippet"
    text = snippet_path.read_text()
    data = json.loads(text)
    assert "hooks" in data
    assert "SessionStart" in data["hooks"]
    assert "PreToolUse" in data["hooks"]
    assert "Stop" in data["hooks"]
    assert "UserPromptSubmit" in data["hooks"]


def test_hooks_use_specguard_default_paths(dist: Path):
    snippet = (dist / "hooks/settings.json.snippet").read_text()
    assert "docs/specguard/specs" in snippet
    assert "docs/specguard/decisions" in snippet


def test_init_command_mentions_auto_merge_and_dry_run(dist: Path):
    cmd = (dist / "commands/init.md").read_text()
    assert "--dry-run" in cmd
    assert "CLAUDE_PLUGIN_ROOT" in cmd
    assert "tempfile" in cmd
    assert "specguard.hooks_merge" in cmd
    assert "plugin_source" in cmd


def test_check_command_treats_missing_hooks_as_error(dist: Path):
    cmd = (dist / "commands/check.md").read_text()
    assert "missing specguard hooks" in cmd
    assert "error" in cmd.lower()
    assert "matching `.specguard/hooks.snippet.json`" not in cmd
    assert "matching .specguard/hooks.snippet.json" not in cmd


def test_upgrade_command_mentions_python_runtime(dist: Path):
    cmd = (dist / "commands/upgrade.md").read_text()
    assert "specguard.upgrade" in cmd
    assert "CLAUDE_PLUGIN_ROOT" in cmd
    assert "replacements = {" in cmd
    assert "claude_block" in cmd
    assert "settings_hooks" in cmd
    assert "specs_template" in cmd
    assert "decisions_template" in cmd
    assert "decisions_readme_rules" in cmd
    assert "version" in cmd
    assert "plugin_source" in cmd
    assert "manual_patch" in cmd


def test_init_command_uses_marker_for_plugin_source(dist: Path):
    cmd = (dist / "commands/init.md").read_text()
    # plugin_source must be computed from the marker file, not hardcoded
    assert 'marker = plugin_root / ".plugin_source"' in cmd
    # no hardcoded "local-dist" as the direct value in the .specguard-version block
    assert 'plugin_source = "local-dist"' not in cmd
    # plugin_source must still be mentioned somewhere (e.g. in the toml block or comment)
    assert "plugin_source" in cmd


def test_upgrade_command_embeds_asset_sections(dist: Path):
    cmd = (dist / "commands/upgrade.md").read_text(encoding="utf-8")
    assert "<!-- specguard:start -->" in cmd
    assert "<!-- specguard:end -->" in cmd
    assert "<!-- specguard:rules:start -->" in cmd
    assert "<!-- specguard:rules:end -->" in cmd
    assert "specguard: inject five laws" in cmd  # from hooks snippet
    # No marker placeholders should remain (rendered)
    assert "<!-- inject:" not in cmd


def test_check_command_removes_semantic_review_package(dist: Path):
    cmd = (dist / "commands/check.md").read_text(encoding="utf-8")
    assert "semantic" not in cmd
    assert "Optional positional: `semantic`" not in cmd
    assert "## Semantic mode" not in cmd
    assert ".specguard/reviews" not in cmd
    assert "findings-template" not in cmd
    assert "Do NOT call any LLM" not in cmd


def test_check_command_prefers_init_for_missing_hooks(dist: Path):
    cmd = (dist / "commands/check.md").read_text(encoding="utf-8")
    assert "missing specguard hooks" in cmd
    assert "run `/specguard:init` to auto-merge" in cmd
    assert "manually merge `.specguard/hooks.snippet.json`" in cmd
    assert cmd.index("run `/specguard:init` to auto-merge") < cmd.index("manually merge `.specguard/hooks.snippet.json`")


def test_init_command_hooks_section_describes_auto_merge(dist: Path):
    cmd = (dist / "commands/init.md").read_text(encoding="utf-8")
    assert "auto-merged into `.claude/settings.json` via `specguard.hooks_merge`" in cmd
    assert "then manually merge into `.claude/settings.json`" not in cmd


def test_upgrade_command_requires_version_and_confirmed_diff(dist: Path):
    cmd = (dist / "commands/upgrade.md").read_text(encoding="utf-8")
    assert "If `.specguard-version` is missing, stop" in cmd
    assert "run `/specguard:init` first" in cmd
    assert "Do not run init-then-upgrade" in cmd
    assert 'plugin_root / "version"' in cmd
    assert "already up to date" in cmd
    assert "dry_run=True" in cmd
    assert "diff_summary" in cmd
    assert "Ask user to confirm" in cmd
    assert "dry_run=False" in cmd
