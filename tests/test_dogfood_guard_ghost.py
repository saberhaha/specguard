from pathlib import Path

import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]
GUARD_GHOST = Path("/Users/saber/aiworkspace/multi-agents/guard-ghost")


@pytest.mark.skipif(not GUARD_GHOST.exists(), reason="guard-ghost repo not present")
def test_superpowers_layout_matches_guard_ghost_structure(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="superpowers", out_dir=out)
    # the hooks should target docs/superpowers as guard-ghost does
    snippet = (out / "hooks/settings.json.snippet").read_text()
    assert "docs/superpowers/specs" in snippet
    assert "docs/superpowers/decisions" in snippet
    # confirm guard-ghost actually uses these paths
    assert (GUARD_GHOST / "docs/superpowers/specs").is_dir()
    assert (GUARD_GHOST / "docs/superpowers/decisions").is_dir()
