from pathlib import Path

import json

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def dist(tmp_path: Path) -> Path:
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    return out


def test_plugin_json_manifest(tmp_path: Path):
    out = dist(tmp_path)
    data = json.loads((out / ".claude-plugin/plugin.json").read_text())
    assert data["name"] == "specguard"
    assert "commandNamespace" not in data


def test_hooks_snippet_is_valid_json(tmp_path: Path):
    out = dist(tmp_path)
    snippet_path = out / "hooks/settings.json.snippet"
    data = json.loads(snippet_path.read_text())
    assert "hooks" in data
    assert "SessionStart" in data["hooks"]
    assert "PreToolUse" in data["hooks"]
    assert "Stop" in data["hooks"]
    assert "UserPromptSubmit" in data["hooks"]


def test_hooks_use_specguard_default_paths(tmp_path: Path):
    out = dist(tmp_path)
    snippet = (out / "hooks/settings.json.snippet").read_text()
    assert "docs/specguard/specs" in snippet
    assert "docs/specguard/decisions" in snippet
