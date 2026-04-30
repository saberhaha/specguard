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


def test_core_version_is_v0_2_0():
    version = (REPO / "core/version").read_text().strip()
    assert version == "0.2.0"
