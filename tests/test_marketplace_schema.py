"""Test marketplace.json schema and content."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"


def _load():
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def test_marketplace_file_exists():
    assert MARKETPLACE.is_file()


def test_marketplace_required_top_level_fields():
    data = _load()
    assert data["name"] == "specguard"
    assert "owner" in data
    assert data["owner"]["name"] == "saber"
    assert "plugins" in data
    assert isinstance(data["plugins"], list)


def test_marketplace_does_not_pin_version():
    """marketplace entry must not set version (avoid double-write with plugin.json)."""
    data = _load()
    for plugin in data["plugins"]:
        assert "version" not in plugin, (
            f"plugin {plugin['name']} pins version in marketplace.json; "
            "official docs warn against double-write with plugin.json"
        )


def test_marketplace_lists_three_plugins():
    data = _load()
    names = sorted(p["name"] for p in data["plugins"])
    assert names == [
        "specguard-default",
        "specguard-openspec-sidecar",
        "specguard-superpowers",
    ]


def test_marketplace_plugins_use_git_subdir_source():
    data = _load()
    expected_paths = {
        "specguard-default": "plugins/specguard-default",
        "specguard-superpowers": "plugins/superpowers",
        "specguard-openspec-sidecar": "plugins/openspec-sidecar",
    }
    for plugin in data["plugins"]:
        src = plugin["source"]
        assert src["source"] == "git-subdir", f"{plugin['name']} source.source != git-subdir"
        assert src["url"] == "https://github.com/saberhaha/specguard.git"
        assert src["path"] == expected_paths[plugin["name"]]


def test_marketplace_plugin_paths_exist_and_have_plugin_json():
    """Each marketplace path must point to a git-tracked plugin directory."""
    data = _load()
    for plugin in data["plugins"]:
        path = REPO / plugin["source"]["path"]
        assert path.is_dir(), f"plugin path {path} does not exist"
        assert (path / ".claude-plugin" / "plugin.json").is_file(), (
            f"plugin {plugin['name']} missing plugin.json at {path}"
        )


def test_rendered_plugin_versions_match_core_version():
    core_version = (REPO / "core/version").read_text().strip()
    data = _load()
    for plugin in data["plugins"]:
        plugin_json = json.loads(
            (REPO / plugin["source"]["path"] / ".claude-plugin" / "plugin.json").read_text()
        )
        assert plugin_json["version"] == core_version, (
            f"plugin {plugin['name']} version {plugin_json['version']} != core/version {core_version}"
        )
