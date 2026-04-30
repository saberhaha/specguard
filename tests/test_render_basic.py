from pathlib import Path

import pytest

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_render_creates_dist(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    assert (out / ".claude-plugin/plugin.json").is_file()
    assert (out / "skills/design-governance/SKILL.md").is_file()
    assert (out / "commands/init.md").is_file()
    assert (out / "commands/check.md").is_file()
    assert (out / "commands/upgrade.md").is_file()
    assert (out / "hooks/settings.json.snippet").is_file()


def test_render_injects_five_laws(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    skill_md = (out / "skills/design-governance/SKILL.md").read_text()
    assert "specguard" in skill_md.lower()
    assert "<!-- inject:five-laws -->" not in skill_md  # marker replaced
    assert "ADR" in skill_md


def test_render_substitutes_paths_in_skill(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    skill_md = (out / "skills/design-governance/SKILL.md").read_text()
    assert "docs/specguard/design.md" in skill_md
    assert "{{ paths.design }}" not in skill_md


def test_render_substitutes_version(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    plugin_json = (out / ".claude-plugin/plugin.json").read_text()
    expected = (REPO / "core/version").read_text().strip()
    assert expected in plugin_json
    assert "{{ specguard_version }}" not in plugin_json


def test_render_unknown_layout_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        render(repo_root=REPO, target="claude", layout="does-not-exist", out_dir=tmp_path)


def test_render_includes_runtime_modules(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    assert (out / "runtime/specguard/__init__.py").is_file()
    assert (out / "runtime/specguard/hooks_merge.py").is_file()
    assert (out / "runtime/specguard/upgrade.py").is_file()
    src_text = (REPO / "src/specguard/hooks_merge.py").read_text()
    assert (out / "runtime/specguard/hooks_merge.py").read_text() == src_text
