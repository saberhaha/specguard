"""CLI integration tests for specguard init and check commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from specguard.cli import main


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        check=True, cwd=path,
    )


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _git_init(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_init_creates_scaffold(project: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--layout", "specguard-default"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert (project / "docs/specguard/design.md").exists()
    assert (project / "docs/specguard/decisions/README.md").exists()
    assert (project / "docs/specguard/specs/TEMPLATE.md").exists()
    assert (project / "CLAUDE.md").exists()


def test_init_merges_hooks(project: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--layout", "specguard-default"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    settings = project / ".claude/settings.json"
    assert settings.exists()
    assert "specguard:" in settings.read_text()


def test_init_dry_run_no_writes(project: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--layout", "specguard-default", "--dry-run"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert not (project / "docs/specguard/design.md").exists()
    assert not (project / "CLAUDE.md").exists()


def test_init_skips_existing_files(project: Path):
    runner = CliRunner()
    runner.invoke(main, ["init"], catch_exceptions=False)
    result2 = runner.invoke(main, ["init"], catch_exceptions=False)
    assert result2.exit_code == 0
    assert "Skipped (exists)" in result2.output


def test_check_passes_after_init(project: Path):
    runner = CliRunner()
    runner.invoke(main, ["init"], catch_exceptions=False)
    result = runner.invoke(main, ["check"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "0 error(s)" in result.output


def test_check_fails_missing_design(project: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["check"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "❌" in result.output


def test_check_fails_missing_hooks(project: Path):
    runner = CliRunner()
    runner.invoke(main, ["init"], catch_exceptions=False)
    settings = project / ".claude/settings.json"
    settings.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
    result = runner.invoke(main, ["check"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "hooks" in result.output
