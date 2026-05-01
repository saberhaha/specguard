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


def test_upgrade_raises_conflict_when_claude_md_missing(tmp_path: Path):
    """CLAUDE.md 不存在时，upgrade_project 应 raise UpgradeConflict 而非 FileNotFoundError。"""
    setup_project(tmp_path)
    (tmp_path / "CLAUDE.md").unlink()

    with pytest.raises(UpgradeConflict) as exc:
        upgrade_project(tmp_path, replacements())

    assert "CLAUDE.md" in exc.value.manual_patch


def test_upgrade_raises_conflict_when_decisions_readme_missing(tmp_path: Path):
    """decisions/README.md 不存在时，upgrade_project 应 raise UpgradeConflict 而非 FileNotFoundError。"""
    setup_project(tmp_path)
    (tmp_path / "docs/specguard/decisions/README.md").unlink()

    with pytest.raises(UpgradeConflict) as exc:
        upgrade_project(tmp_path, replacements())

    assert "README.md" in exc.value.manual_patch


def test_upgrade_no_op_when_already_current(tmp_path: Path):
    """内容一致时 upgrade_project 返回 changed=False 且不写文件。"""
    # 先完整跑一次，让文件内容收敛到与 replacements 一致
    setup_project(tmp_path)
    result1 = upgrade_project(tmp_path, replacements())
    assert result1.changed is True

    # 再跑一次：所有内容已与 replacements 一致
    import os
    mtime_before = {
        p: os.stat(p).st_mtime_ns
        for p in [
            tmp_path / "CLAUDE.md",
            tmp_path / ".claude/settings.json",
            tmp_path / "docs/specguard/specs/TEMPLATE.md",
            tmp_path / "docs/specguard/decisions/TEMPLATE.md",
            tmp_path / "docs/specguard/decisions/README.md",
            tmp_path / ".specguard-version",
        ]
    }

    result2 = upgrade_project(tmp_path, replacements())
    assert result2.changed is False

    assert {p: os.stat(p).st_mtime_ns for p in mtime_before} == mtime_before


def test_upgrade_dry_run_returns_diff_summary_without_writing(tmp_path: Path):
    setup_project(tmp_path)
    before = {
        p: p.read_text(encoding="utf-8")
        for p in [
            tmp_path / "CLAUDE.md",
            tmp_path / ".claude/settings.json",
            tmp_path / "docs/specguard/specs/TEMPLATE.md",
            tmp_path / "docs/specguard/decisions/TEMPLATE.md",
            tmp_path / "docs/specguard/decisions/README.md",
            tmp_path / ".specguard-version",
        ]
    }

    result = upgrade_project(tmp_path, replacements(), dry_run=True)

    assert result.changed is True
    assert "SpecGuard upgrade 0.1.0 → 0.2.0" in result.diff_summary
    assert "Will update:" in result.diff_summary
    assert "CLAUDE.md specguard block" in result.diff_summary
    assert ".claude/settings.json specguard hooks" in result.diff_summary
    assert "docs/specguard/specs/TEMPLATE.md" in result.diff_summary
    assert "docs/specguard/decisions/TEMPLATE.md" in result.diff_summary
    assert "docs/specguard/decisions/README.md rules" in result.diff_summary
    assert ".specguard-version" in result.diff_summary
    assert "Will not touch:" in result.diff_summary
    assert "docs/specguard/design.md content" in result.diff_summary
    assert "existing ADR files" in result.diff_summary
    assert "existing spec files" in result.diff_summary
    assert {p: p.read_text(encoding="utf-8") for p in before} == before


def test_upgrade_dry_run_no_op_summary_when_already_current(tmp_path: Path):
    setup_project(tmp_path)
    upgrade_project(tmp_path, replacements())

    result = upgrade_project(tmp_path, replacements(), dry_run=True)

    assert result.changed is False
    assert "SpecGuard upgrade 0.2.0 → 0.2.0" in result.diff_summary
    assert "No changes required." in result.diff_summary
