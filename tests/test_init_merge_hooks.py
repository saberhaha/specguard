import json
from pathlib import Path

import pytest

from specguard.hooks_merge import HookMergeError, merge_hooks_file


def snippet() -> dict:
    return {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "statusMessage": "specguard: inject five laws", "command": "echo specguard"}]}
            ],
            "Stop": [
                {"hooks": [{"type": "command", "statusMessage": "specguard: design sync reminder", "command": "echo stop"}]}
            ],
        }
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_merge_creates_settings_when_missing(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    assert result.changed is True
    data = read_json(settings_path)
    assert data["hooks"]["SessionStart"][0]["hooks"][0]["statusMessage"] == "specguard: inject five laws"
    assert data["hooks"]["Stop"][0]["hooks"][0]["statusMessage"] == "specguard: design sync reminder"


def test_merge_preserves_non_specguard_hooks(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())
    write_json(
        settings_path,
        {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "command", "statusMessage": "custom: keep", "command": "echo keep"}]}
                ]
            }
        },
    )

    merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    entries = read_json(settings_path)["hooks"]["SessionStart"]
    assert entries[0]["hooks"][0]["statusMessage"] == "custom: keep"
    assert entries[1]["hooks"][0]["statusMessage"] == "specguard: inject five laws"


def test_merge_is_idempotent(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)
    first = settings_path.read_text()
    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)
    second = settings_path.read_text()

    assert result.changed is False
    assert second == first


def test_dry_run_does_not_write_settings(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path, dry_run=True)

    assert result.changed is True
    assert "specguard: inject five laws" in result.diff
    assert not settings_path.exists()


def test_invalid_settings_json_is_not_overwritten(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("{invalid")

    with pytest.raises(HookMergeError):
        merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    assert settings_path.read_text() == "{invalid"
