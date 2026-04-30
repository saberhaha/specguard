from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, BaseLoader, StrictUndefined

from .manifest import AdapterManifest, LayoutManifest


def render(
    repo_root: Path,
    target: str,
    layout: str,
    out_dir: Path,
) -> None:
    """Render core + layout + adapter into out_dir."""
    layout_manifest_path = repo_root / "layouts" / layout / "manifest.yaml"
    if not layout_manifest_path.is_file():
        raise FileNotFoundError(f"layout not found: {layout_manifest_path}")
    adapter_manifest_path = repo_root / "adapters" / target / "manifest.yaml"
    if not adapter_manifest_path.is_file():
        raise FileNotFoundError(f"adapter not found: {adapter_manifest_path}")

    layout_m = LayoutManifest.load(layout_manifest_path)
    adapter_m = AdapterManifest.load(adapter_manifest_path)

    version = (repo_root / "core/version").read_text().strip()

    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    # regex_escape is used inside JSON string literals; backslashes must be doubled
    # so the JSON source is valid (e.g. "design\.md" in JSON must be "design\\.md")
    env.filters["regex_escape"] = lambda s: re.escape(str(s)).replace("\\", "\\\\")

    context = {
        "paths": layout_m.paths,
        "specguard_version": version,
    }

    for entry in adapter_m.renders:
        src_path = repo_root / "adapters" / target / entry["source"]
        out_path = out_dir / entry["output"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        text = src_path.read_text()

        for inj in entry.get("inject", []) or []:
            inj_text = (repo_root / inj["source"]).read_text()
            text = text.replace(inj["marker"], inj_text)

        rendered = env.from_string(text).render(**context)
        out_path.write_text(rendered)


def main() -> None:  # entry point: specguard-render
    import argparse

    parser = argparse.ArgumentParser(prog="specguard-render")
    parser.add_argument("--target", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo", default=Path(__file__).resolve().parents[2], type=Path)
    args = parser.parse_args()

    render(
        repo_root=args.repo,
        target=args.target,
        layout=args.layout,
        out_dir=args.out,
    )
    print(f"rendered {args.target}/{args.layout} -> {args.out}")


if __name__ == "__main__":
    main()
