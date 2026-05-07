"""specguard CLI — init and check commands."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

import click
from jinja2 import BaseLoader, Environment, StrictUndefined

from .hooks_merge import merge_hooks_file
from .manifest import LayoutManifest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYOUTS_DIR = REPO_ROOT / "layouts"
ADAPTERS_DIR = REPO_ROOT / "adapters"


def _repo_root() -> Path:
    """Return the specguard package repo root (where layouts/ lives)."""
    return REPO_ROOT


def _load_layout(layout: str) -> LayoutManifest:
    manifest_path = _repo_root() / "layouts" / layout / "manifest.yaml"
    if not manifest_path.is_file():
        raise click.ClickException(
            f"Layout '{layout}' not found. Available: "
            + ", ".join(p.name for p in (_repo_root() / "layouts").iterdir() if p.is_dir())
        )
    return LayoutManifest.load(manifest_path)


def _render_template(tpl_path: Path, context: dict) -> str:
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    env.filters["relative_to_design"] = lambda target: str(
        Path(target).relative_to(Path(context["paths"]["design"]).parent)
        if Path(target) != Path(context["paths"]["design"]).parent
        else target
    )
    return env.from_string(tpl_path.read_text(encoding="utf-8")).render(**context)


def _specguard_block(paths: dict, ai: str, spec: str) -> str:
    """Render the CLAUDE.md specguard block from core rules."""
    repo = _repo_root()
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    context = {"paths": paths}

    def _render_rule(name: str) -> str:
        raw = (repo / "core/rules" / name).read_text(encoding="utf-8")
        return env.from_string(raw).render(**context).strip()

    five_laws = _render_rule("five-laws.md")
    adr_checklist = _render_rule("adr-checklist.md")
    design_sync = _render_rule("design-sync.md")

    block = (
        "## SpecGuard governance rules\n\n"
        "### Five non-negotiable laws\n" + five_laws + "\n\n"
        "### ADR judgement checklist\n" + adr_checklist + "\n\n"
        "### design.md sync rules\n" + design_sync + "\n"
    )
    return f"<!-- specguard:start -->\n{block}\n<!-- specguard:end -->"


def _update_claude_md(project_root: Path, block: str, dry_run: bool) -> str:
    claude_md = project_root / "CLAUDE.md"
    start = "<!-- specguard:start -->"
    end = "<!-- specguard:end -->"

    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        if start in content and end in content:
            new_content = re.sub(
                re.escape(start) + r".*?" + re.escape(end),
                block,
                content,
                flags=re.DOTALL,
            )
            action = "Updated"
        else:
            new_content = block + "\n\n" + content
            action = "Updated"
    else:
        new_content = block + "\n"
        action = "Created"

    if not dry_run:
        claude_md.write_text(new_content, encoding="utf-8")
    return f"{action}: CLAUDE.md"


@click.group()
@click.version_option(package_name="specguard")
def main() -> None:
    """specguard — project governance scaffold for AI-driven development."""


@main.command()
@click.option("--layout", default="specguard-default", show_default=True,
              help="Layout to use (specguard-default / superpowers / openspec-sidecar)")
@click.option("--ai", default="claude", show_default=True,
              help="AI agent (claude / cursor / codex / generic)")
@click.option("--spec", default="none", show_default=True,
              help="Spec tool (none / openspec / superpowers)")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print planned actions without writing files")
def init(layout: str, ai: str, spec: str, dry_run: bool) -> None:
    """Initialize governance scaffold in the current project."""
    project_root = Path.cwd()
    layout_m = _load_layout(layout)
    paths = layout_m.paths
    repo = _repo_root()

    context = {
        "paths": paths,
        "project": {"name": project_root.name},
        "today": str(date.today()),
        "layout_name": layout_m.name,
        "specguard_version": (repo / "core/version").read_text().strip(),
    }

    results: list[str] = []

    # --- scaffold files ---
    file_map = {
        Path(paths["design"]): repo / "core/templates/design.md.tpl",
        Path(paths["decisions_dir"]) / "README.md": repo / "core/templates/decisions/README.md.tpl",
        Path(paths["decisions_dir"]) / "TEMPLATE.md": repo / "core/templates/decisions/TEMPLATE.md.tpl",
        Path(paths["specs_dir"]) / "TEMPLATE.md": repo / "core/templates/specs/TEMPLATE.md.tpl",
    }
    for dest_rel, tpl_path in file_map.items():
        dest = project_root / dest_rel
        if dest.exists():
            results.append(f"Skipped (exists): {dest_rel}")
        else:
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(_render_template(tpl_path, context), encoding="utf-8")
            results.append(f"{'Would create' if dry_run else 'Created'}: {dest_rel}")

    # --- CLAUDE.md ---
    block = _specguard_block(paths, ai, spec)
    results.append(_update_claude_md(project_root, block, dry_run))

    # --- hooks ---
    hooks_tpl = repo / "adapters/claude/plugin/hooks/settings.json.snippet.tpl"
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    env.filters["regex_escape"] = lambda s: re.escape(str(s)).replace("\\", "\\\\")
    snippet_text = env.from_string(hooks_tpl.read_text(encoding="utf-8")).render(**context)

    settings_path = project_root / ".claude/settings.json"
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(snippet_text)
        tmp_path = Path(tmp.name)

    result = merge_hooks_file(settings_path, tmp_path, dry_run=dry_run)
    if result.changed:
        results.append(f"{'Would merge' if dry_run else 'Merged'}: hooks into .claude/settings.json")
    else:
        results.append("Skipped (unchanged): hooks")
    tmp_path.unlink(missing_ok=True)

    # --- report ---
    click.echo("\nspecguard init" + (" (dry-run)" if dry_run else ""))
    click.echo("─" * 40)
    for line in results:
        click.echo(f"  {line}")
    click.echo(f"\nNext: read {paths['design']}, then run `specguard check`")


@main.command()
@click.option("--layout", default="specguard-default", show_default=True)
def check(layout: str) -> None:
    """Validate governance state of the current project."""
    project_root = Path.cwd()
    layout_m = _load_layout(layout)
    paths = layout_m.paths

    errors: list[str] = []
    warnings: list[str] = []
    ok: list[str] = []

    def pass_(msg: str) -> None:
        ok.append(f"✓ {msg}")

    def warn(msg: str) -> None:
        warnings.append(f"⚠️  {msg}")

    def fail(msg: str) -> None:
        errors.append(f"❌ {msg}")

    # 1. design.md exists
    design = project_root / paths["design"]
    if design.exists():
        pass_("design.md exists")
    else:
        fail(f"{paths['design']} not found")

    # 2. no *-design.md in specs_dir
    specs_dir = project_root / paths["specs_dir"]
    if specs_dir.exists():
        dated = [f for f in specs_dir.rglob("*-design.md")]
        if dated:
            if layout == "superpowers":
                for f in dated:
                    warn(f"legacy *-design.md: {f.relative_to(project_root)}")
            else:
                for f in dated:
                    fail(f"dated design file forbidden: {f.relative_to(project_root)}")
        else:
            pass_("no *-design.md in specs/")

    # 3. decisions/README.md exists
    decisions_dir = project_root / paths["decisions_dir"]
    decisions_readme = decisions_dir / "README.md"
    if decisions_readme.exists():
        pass_("decisions/README.md exists")
    else:
        fail(f"{paths['decisions_dir']}/README.md not found")

    # 4 + 5. ADR filenames valid and contiguous
    adr_pattern = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
    exempt = {"README.md", "TEMPLATE.md"}
    adr_numbers: list[int] = []
    if decisions_dir.exists():
        for f in sorted(decisions_dir.iterdir()):
            if f.name in exempt or not f.name.endswith(".md"):
                continue
            m = adr_pattern.match(f.name)
            if not m:
                fail(f"ADR filename invalid: {f.name}")
            else:
                adr_numbers.append(int(m.group(1)))
    if adr_numbers:
        expected = list(range(adr_numbers[0], adr_numbers[0] + len(adr_numbers)))
        if adr_numbers == expected:
            pass_("ADR filenames valid and contiguous")
        else:
            gaps = sorted(set(expected) - set(adr_numbers))
            fail(f"ADR numbering gaps: {gaps}")
    else:
        pass_("ADR filenames valid (no ADRs yet)")

    # 6. every ADR in index
    if decisions_readme.exists() and adr_numbers:
        index_text = decisions_readme.read_text(encoding="utf-8")
        for num in adr_numbers:
            tag = f"{num:04d}"
            if tag not in index_text:
                warn(f"ADR-{tag} missing from decisions/README.md index")
        pass_("ADR index checked")

    # 7. design.md ADR references exist
    if design.exists() and decisions_dir.exists():
        design_text = design.read_text(encoding="utf-8")
        refs = re.findall(r"ADR-(\d{4})", design_text)
        for ref in refs:
            files = list(decisions_dir.glob(f"{ref}-*.md"))
            if not files:
                fail(f"design.md references ADR-{ref} but file not found")
        if refs:
            pass_("design.md ADR references exist")

    # 8. Superseded-by targets exist
    if decisions_dir.exists():
        for adr_file in decisions_dir.glob("*.md"):
            if adr_file.name in exempt:
                continue
            text = adr_file.read_text(encoding="utf-8")
            targets = re.findall(r"Superseded by ADR-(\d{4})", text)
            for t in targets:
                if not list(decisions_dir.glob(f"{t}-*.md")):
                    fail(f"{adr_file.name}: Superseded by ADR-{t} not found")
        pass_("Superseded-by targets checked")

    # 9. spec files have ADR heading
    if specs_dir.exists():
        for spec_file in specs_dir.glob("*.md"):
            if spec_file.name == "TEMPLATE.md":
                continue
            if layout == "superpowers" and spec_file.name.endswith("-design.md"):
                continue
            content = spec_file.read_text(encoding="utf-8")
            if "## ADR 级别决策识别" not in content:
                fail(f"{spec_file.name} missing '## ADR 级别决策识别'")
        pass_("spec ADR heading checked")

    # 10. CLAUDE.md has specguard markers
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        if "<!-- specguard:start -->" in text and "<!-- specguard:end -->" in text:
            pass_("CLAUDE.md has specguard markers")
        else:
            fail("CLAUDE.md missing <!-- specguard:start/end --> markers")
    else:
        fail("CLAUDE.md not found")

    # 11. .claude/settings.json has specguard hooks
    settings = project_root / ".claude/settings.json"
    if settings.exists():
        text = settings.read_text(encoding="utf-8")
        if "specguard:" in text:
            pass_(".claude/settings.json has specguard hooks")
        else:
            fail(".claude/settings.json missing specguard: hooks — run `specguard init`")
    else:
        fail(".claude/settings.json not found — run `specguard init`")

    # --- report ---
    click.echo(f"\nSpecGuard Check (layout={layout})")
    click.echo("─" * 40)
    for line in ok + warnings + errors:
        click.echo(f"  {line}")
    click.echo(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        sys.exit(1)
