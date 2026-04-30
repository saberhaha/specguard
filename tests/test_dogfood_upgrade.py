import json
from pathlib import Path

import pytest

from specguard.upgrade import UpgradeConflict, upgrade_project


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def setup_project(root: Path) -> None:
    write(root / "CLAUDE.md", "before\n<!-- specguard:start -->\nold block\n<!-- specguard:end -->\nafter\n")
    write(
        root / ".claude/settings.json",
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {"hooks": [{"statusMessage": "custom: keep", "command": "echo keep"}]},
                        {"hooks": [{"statusMessage": "specguard: old", "command": "echo old"}]},
                    ]
                }
            },
            indent=2,
        )
        + "\n",
    )
    write(root / "docs/specguard/specs/TEMPLATE.md", "old specs template\n")
    write(root / "docs/specguard/decisions/TEMPLATE.md", "old decisions template\n")
    write(
        root / "docs/specguard/decisions/README.md",
        "# index\n<!-- specguard:rules:start -->\nold rules\n<!-- specguard:rules:end -->\n",
    )
    write(root / "docs/specguard/design.md", "do not touch\n")
    write(
        root / ".specguard-version",
        'specguard_version = "0.1.0"\nagent = "claude"\nspec = "specguard-default"\nlayout = "specguard-default"\ninstalled_at = "2026-04-30T00:00:00Z"\n',
    )


def replacements() -> dict:
    return {
        "claude_block": "new block\n",
        "settings_hooks": {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"statusMessage": "specguard: new", "command": "echo new"}]}
                ]
            }
        },
        "specs_template": "new specs template\n",
        "decisions_template": "new decisions template\n",
        "decisions_readme_rules": "new rules\n",
        "version": "0.2.0",
        "plugin_source": "local-dist",
    }


def test_upgrade_replaces_marker_regions_and_preserves_other_content(tmp_path: Path):
    setup_project(tmp_path)

    result = upgrade_project(tmp_path, replacements())

    assert result.changed is True
    assert (tmp_path / "docs/specguard/design.md").read_text() == "do not touch\n"
    assert (tmp_path / "CLAUDE.md").read_text() == "before\n<!-- specguard:start -->\nnew block\n<!-- specguard:end -->\nafter\n"
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    entries = settings["hooks"]["SessionStart"]
    assert entries[0]["hooks"][0]["statusMessage"] == "custom: keep"
    assert entries[1]["hooks"][0]["statusMessage"] == "specguard: new"
    assert (tmp_path / "docs/specguard/specs/TEMPLATE.md").read_text() == "new specs template\n"
    assert (tmp_path / "docs/specguard/decisions/TEMPLATE.md").read_text() == "new decisions template\n"
    assert "new rules" in (tmp_path / "docs/specguard/decisions/README.md").read_text()
    version = (tmp_path / ".specguard-version").read_text()
    assert 'specguard_version = "0.2.0"' in version
    assert 'plugin_source = "local-dist"' in version


def test_upgrade_conflict_when_claude_marker_missing(tmp_path: Path):
    setup_project(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("no markers\n")

    with pytest.raises(UpgradeConflict) as exc:
        upgrade_project(tmp_path, replacements())

    assert (tmp_path / "CLAUDE.md").read_text() == "no markers\n"
    assert (tmp_path / "docs/specguard/specs/TEMPLATE.md").read_text() == "old specs template\n"

    patch = exc.value.manual_patch
    assert patch, "manual_patch must be non-empty"
    assert "CLAUDE.md" in patch
    assert "specguard:start" in patch
    assert replacements()["claude_block"] in patch


def test_upgrade_no_write_on_decisions_readme_conflict(tmp_path: Path):
    """两阶段校验：decisions/README.md marker 缺失时，不落盘任何目标文件。"""
    setup_project(tmp_path)
    (tmp_path / "docs/specguard/decisions/README.md").write_text("# index\nno markers\n")

    with pytest.raises(UpgradeConflict) as exc:
        upgrade_project(tmp_path, replacements())

    # 所有目标文件保持原始内容
    assert (tmp_path / "CLAUDE.md").read_text() == "before\n<!-- specguard:start -->\nold block\n<!-- specguard:end -->\nafter\n"
    assert (tmp_path / "docs/specguard/specs/TEMPLATE.md").read_text() == "old specs template\n"

    patch = exc.value.manual_patch
    assert patch, "manual_patch must be non-empty"
    assert "README.md" in patch
    assert "specguard:rules:start" in patch
    assert replacements()["decisions_readme_rules"] in patch
