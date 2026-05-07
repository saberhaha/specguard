"""Pytest fixtures for specguard tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jinja2 import BaseLoader, Environment, StrictUndefined

from specguard.manifest import LayoutManifest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def rendered_snippet() -> dict:
    """Render the hooks snippet directly from the tpl file for specguard-default layout.

    Used by test_hook_*.py to extract hook command strings without going through
    the render pipeline (which was removed in v0.8.0 cleanup).
    """
    layout_m = LayoutManifest.load(REPO / "layouts/specguard-default/manifest.yaml")
    tpl_path = REPO / "adapters/claude/plugin/hooks/settings.json.snippet.tpl"

    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    env.filters["regex_escape"] = lambda s: re.escape(str(s)).replace("\\", "\\\\")

    context = {
        "paths": layout_m.paths,
        "specguard_version": (REPO / "core/version").read_text().strip(),
        "layout_name": layout_m.name,
    }
    rendered = env.from_string(tpl_path.read_text(encoding="utf-8")).render(**context)
    return json.loads(rendered)
