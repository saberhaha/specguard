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
    for name in ("init", "check"):
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


def test_check_command_removes_semantic_review_package(dist: Path):
    cmd = (dist / "commands/check.md").read_text(encoding="utf-8")
    assert "semantic" not in cmd
    assert "Optional positional: `semantic`" not in cmd
    assert "## Semantic mode" not in cmd
    assert ".specguard/reviews" not in cmd
    assert "findings-template" not in cmd
    assert "Do NOT call any LLM" not in cmd


def test_check_command_validates_hooks_in_settings(dist: Path):
    cmd = (dist / "commands/check.md").read_text(encoding="utf-8")
    assert "statusMessage" in cmd
    assert "specguard:" in cmd


def test_init_command_hooks_section_describes_auto_merge(dist: Path):
    cmd = (dist / "commands/init.md").read_text(encoding="utf-8")
    assert "auto-merged" in cmd.lower() or "hooks_merge" in cmd

