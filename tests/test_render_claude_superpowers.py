from pathlib import Path

import json

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_superpowers(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="superpowers", out_dir=out)
    snippet = (out / "hooks/settings.json.snippet").read_text()
    assert "docs/superpowers/specs" in snippet
    assert "docs/superpowers/decisions" in snippet
