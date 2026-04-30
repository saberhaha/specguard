from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


REQUIRED_LAYOUT_PATHS = {"design", "decisions_dir", "specs_dir", "plans_dir"}


class ManifestError(ValueError):
    """Raised when a manifest file is malformed."""


@dataclass
class LayoutManifest:
    name: str
    description: str
    paths: dict[str, str]
    inject_policies: list[str] = field(default_factory=list)
    detection: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "LayoutManifest":
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ManifestError(f"layout manifest must be a mapping: {path}")
        for key in ("name", "paths"):
            if key not in data:
                raise ManifestError(f"layout manifest missing '{key}': {path}")
        paths = data["paths"]
        if not isinstance(paths, dict):
            raise ManifestError(f"layout 'paths' must be a mapping: {path}")
        missing = REQUIRED_LAYOUT_PATHS - set(paths.keys())
        if missing:
            raise ManifestError(
                f"layout '{data['name']}' missing required paths: {sorted(missing)}"
            )
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            paths=paths,
            inject_policies=list(data.get("inject_policies") or []),
            detection=data.get("detection") or {},
        )


@dataclass
class AdapterManifest:
    target: str
    description: str
    capabilities: list[str]
    renders: list[dict[str, Any]]

    @classmethod
    def load(cls, path: Path) -> "AdapterManifest":
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ManifestError(f"adapter manifest must be a mapping: {path}")
        for key in ("target", "renders"):
            if key not in data:
                raise ManifestError(f"adapter manifest missing '{key}': {path}")
        return cls(
            target=data["target"],
            description=data.get("description", ""),
            capabilities=list(data.get("capabilities") or []),
            renders=list(data["renders"]),
        )
