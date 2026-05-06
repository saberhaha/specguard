"""Pressure tests for Stop hook (specguard: design sync reminder).

Verifies the rendered hook script emits a systemMessage when the working
tree has src/ changes without corresponding design.md / decisions/ updates,
and stays silent in all other cases.

Uses a tmp_path git repo + monkeypatch CLAUDE_PROJECT_DIR so the hook
operates against a reproducible local state.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests._hook_helpers import extract_hook_command, run_hook_command


EVENT = "Stop"
STATUS = "specguard: design sync reminder"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Create a tmp git repo with src/ + docs/specguard/design.md committed."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n", encoding="utf-8")
    design = tmp_path / "docs" / "specguard"
    design.mkdir(parents=True)
    (design / "design.md").write_text("# design\n", encoding="utf-8")
    decisions = design / "decisions"
    decisions.mkdir()
    (decisions / "README.md").write_text("# decisions\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init", "-q")
    return tmp_path


def _env_with(repo: Path) -> dict:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    return env


def test_only_src_changed_emits_reminder(rendered_snippet, repo):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    (repo / "src" / "foo.py").write_text("x = 2\n", encoding="utf-8")

    out, _ = run_hook_command(cmd, "{}", env=_env_with(repo))
    assert "design" in out.get("systemMessage", "").lower()


def test_src_and_design_changed_no_reminder(rendered_snippet, repo):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    (repo / "src" / "foo.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "docs" / "specguard" / "design.md").write_text("# updated\n", encoding="utf-8")

    out, _ = run_hook_command(cmd, "{}", env=_env_with(repo))
    assert out == {}


def test_only_design_changed_no_reminder(rendered_snippet, repo):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    (repo / "docs" / "specguard" / "design.md").write_text("# updated\n", encoding="utf-8")

    out, _ = run_hook_command(cmd, "{}", env=_env_with(repo))
    assert out == {}


def test_no_changes_no_reminder(rendered_snippet, repo):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, "{}", env=_env_with(repo))
    assert out == {}


def test_no_git_repo_silent(rendered_snippet, tmp_path):
    """Pointing CLAUDE_PROJECT_DIR at a non-repo path must not raise; output empty."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    nonrepo = tmp_path / "not_a_repo"
    nonrepo.mkdir()
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(nonrepo)

    out, _ = run_hook_command(cmd, "{}", env=env)
    assert out == {}


def test_decisions_change_counts_as_doc(rendered_snippet, repo):
    """Touching decisions/<file>.md must count as doc change, suppressing reminder."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    (repo / "src" / "foo.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "docs" / "specguard" / "decisions" / "0001-foo.md").write_text(
        "# adr\n", encoding="utf-8"
    )
    _git(repo, "add", "docs/specguard/decisions/0001-foo.md")
    # leave src/foo.py modified, ADR file staged

    out, _ = run_hook_command(cmd, "{}", env=_env_with(repo))
    assert out == {}
