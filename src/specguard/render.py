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

    version = (repo_root / "core/version").read_text(encoding="utf-8").strip()

    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    # regex_escape is used inside JSON string literals; backslashes must be doubled
    # so the JSON source is valid (e.g. "design\.md" in JSON must be "design\\.md")
    env.filters["regex_escape"] = lambda s: re.escape(str(s)).replace("\\", "\\\\")

    design_dir = Path(layout_m.paths["design"]).parent

    def _relative_to_design(target: str) -> str:
        try:
            return str(Path(target).relative_to(design_dir))
        except ValueError:
            # target lives outside design's directory; fall back to a literal path
            return str(target)

    env.filters["relative_to_design"] = _relative_to_design

    context = {
        "paths": layout_m.paths,
        "specguard_version": version,
        "layout_name": layout_m.name,
    }

    policy_marker = "<!-- inject:policy -->"
    if layout_m.inject_policies:
        policy_text = "\n\n".join(
            (repo_root / p).read_text(encoding="utf-8").rstrip() for p in layout_m.inject_policies
        )
    else:
        policy_text = ""

    for entry in adapter_m.renders:
        src_path = repo_root / "adapters" / target / entry["source"]
        out_path = out_dir / entry["output"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        text = src_path.read_text(encoding="utf-8")

        for inj in entry.get("inject", []) or []:
            inj_text = (repo_root / inj["source"]).read_text(encoding="utf-8")
            if inj.get("raw"):
                inj_text = "{% raw %}" + inj_text + "{% endraw %}"
            text = text.replace(inj["marker"], inj_text)

        # layout-specific policy is wired into init prompt via marker
        text = text.replace(policy_marker, policy_text)

        rendered = env.from_string(text).render(**context)
        out_path.write_text(rendered, encoding="utf-8")

    runtime_out = out_dir / "runtime/specguard"
    runtime_out.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "hooks_merge.py", "upgrade.py"):
        (runtime_out / name).write_text((repo_root / "src/specguard" / name).read_text(encoding="utf-8"), encoding="utf-8")


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
