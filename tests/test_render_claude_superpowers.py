from pathlib import Path

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_superpowers(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="superpowers", out_dir=out)
    skill = (out / "skills/design-governance/SKILL.md").read_text()
    assert "docs/superpowers/design.md" in skill
    assert "docs/superpowers/decisions" in skill
    assert "docs/superpowers/specs" in skill
