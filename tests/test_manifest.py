from pathlib import Path

import pytest

from specguard.manifest import LayoutManifest, AdapterManifest, ManifestError


REPO = Path(__file__).resolve().parents[1]


def test_load_specguard_default_layout():
    m = LayoutManifest.load(REPO / "layouts/specguard-default/manifest.yaml")
    assert m.name == "specguard-default"
    assert m.paths["design"] == "docs/specguard/design.md"
    assert m.paths["decisions_dir"] == "docs/specguard/decisions"
    assert m.paths["specs_dir"] == "docs/specguard/specs"
    assert m.paths["plans_dir"] == "docs/specguard/plans"
    assert m.inject_policies == []


def test_load_superpowers_layout():
    m = LayoutManifest.load(REPO / "layouts/superpowers/manifest.yaml")
    assert m.paths["specs_dir"] == "docs/superpowers/specs"
    assert "core/policies/with-superpowers.md" in m.inject_policies


def test_load_openspec_sidecar_layout():
    m = LayoutManifest.load(REPO / "layouts/openspec-sidecar/manifest.yaml")
    assert m.paths["specs_dir"] == "openspec/specs"
    assert m.paths["changes_dir"] == "openspec/changes"


def test_load_claude_adapter():
    m = AdapterManifest.load(REPO / "adapters/claude/manifest.yaml")
    assert m.target == "claude"
    assert "skills" in m.capabilities
    assert "hooks" in m.capabilities
    assert any("plugin.json" in r["output"] for r in m.renders)


def test_layout_missing_required_path_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: bad\npaths:\n  design: x\n")  # missing other paths
    with pytest.raises(ManifestError):
        LayoutManifest.load(bad)


def test_adapter_missing_target_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("description: x\nrenders: []\n")
    with pytest.raises(ManifestError):
        AdapterManifest.load(bad)
