from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def test_release_workflow_builds_three_layout_tarballs():
    workflow_path = REPO / ".github/workflows/release.yml"
    assert workflow_path.is_file()
    workflow = yaml.safe_load(workflow_path.read_text())
    on = workflow["on"] if "on" in workflow else workflow[True]
    assert on["push"]["tags"] == ["v*"]
    text = workflow_path.read_text()
    for layout in ("specguard-default", "superpowers", "openspec-sidecar"):
        assert layout in text
    assert "tar -czf" in text
    assert "softprops/action-gh-release" in text
    assert "contents: write" in text
    assert "uv sync --frozen" in text


def test_core_version_is_v0_4_0():
    version = (REPO / "core/version").read_text().strip()
    assert version == "0.4.0"


def test_release_workflow_has_tag_version_guard():
    workflow_path = REPO / ".github/workflows/release.yml"
    text = workflow_path.read_text()
    assert "Verify tag matches core/version" in text
    assert '[ "${ref#v}" != "${version}" ]' in text


def test_release_workflow_renders_and_commits_plugins():
    """Release workflow must render plugins/, commit, and push to main before building tarballs."""
    workflow_path = REPO / ".github/workflows/release.yml"
    text = workflow_path.read_text()
    # checkout main (not detached tag) so we can push commits
    assert "ref: main" in text
    # render targets plugins/<layout>
    assert 'uv run specguard-render --target claude --layout "${layout}" --out "plugins/${layout}"' in text
    # race protection
    assert "git pull --rebase origin main" in text
    # commit + push
    assert "git add plugins/" in text
    assert "--allow-empty" in text
    assert "git push origin HEAD:main" in text
    # render+commit must precede tarball build
    render_idx = text.index("Render plugins/ for marketplace")
    commit_idx = text.index("Commit and push rendered plugins/")
    tarball_idx = text.index("Render and package tarballs")
    assert render_idx < commit_idx < tarball_idx

