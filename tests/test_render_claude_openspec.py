from pathlib import Path

import json

from specguard.render import render

REPO = Path(__file__).resolve().parents[1]


def test_openspec_hooks_use_correct_paths(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="openspec-sidecar", out_dir=out)
    snippet = json.loads((out / "hooks/settings.json.snippet").read_text())
    found = False
    for hooks in snippet["hooks"].values():
        for matcher in hooks:
            for h in matcher["hooks"]:
                if "openspec/specs" in h.get("command", ""):
                    found = True
    assert found, "no hook referenced openspec/specs"
