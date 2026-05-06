"""Pytest fixtures for specguard tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def rendered_snippet(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Render specguard-default once per session and return the parsed hooks snippet.

    Used by test_hook_*.py tests to extract real hook command strings driven by
    the live render pipeline (not a manual template substitution).
    """
    out = tmp_path_factory.mktemp("dist")
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    snippet_path = out / "hooks" / "settings.json.snippet"
    return json.loads(snippet_path.read_text(encoding="utf-8"))
