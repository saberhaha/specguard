from pathlib import Path

import pytest

from specguard.manifest import LayoutManifest, ManifestError

REPO = Path(__file__).resolve().parents[1]


def test_load_specguard_default():
    m = LayoutManifest.load(REPO / "layouts/specguard-default/manifest.yaml")
    assert m.name == "specguard-default"
    assert m.paths["design"] == "docs/specguard/design.md"
    assert m.paths["decisions_dir"] == "docs/specguard/decisions"


def test_load_superpowers():
    m = LayoutManifest.load(REPO / "layouts/superpowers/manifest.yaml")
    assert m.paths["design"] == "docs/superpowers/design.md"


def test_load_openspec_sidecar():
    m = LayoutManifest.load(REPO / "layouts/openspec-sidecar/manifest.yaml")
    assert m.paths["specs_dir"] == "openspec/specs"


def test_missing_required_path(tmp_path: Path):
    bad = tmp_path / "manifest.yaml"
    bad.write_text("name: bad\npaths:\n  design: x\n")
    with pytest.raises(ManifestError, match="missing required paths"):
        LayoutManifest.load(bad)
