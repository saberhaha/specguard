# Distribution and Auto Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.2.0 with GitHub Release tarball distribution, automatic hook merging, and testable upgrade behavior.

**Architecture:** Runtime-sensitive logic moves from prompt-only behavior into pure Python modules: `hooks_merge.py` handles settings.json hook merging; `upgrade.py` handles marker replacement and legacy `.specguard-version` updates. Claude command prompts call these modules instead of reimplementing algorithms in prose.

**Tech Stack:** Python 3.11+, stdlib `json`/`difflib`/`pathlib`/`tempfile`, PyYAML/Jinja2 existing render stack, pytest, GitHub Actions.

---

## File Structure

- Create `src/specguard/hooks_merge.py`: pure functions for loading snippet/settings JSON, identifying specguard hook entries, merging by `statusMessage`, dry-run diff, atomic write.
- Create `src/specguard/upgrade.py`: pure functions for replacing marker regions, replacing specguard hooks in settings JSON, updating `.specguard-version`, generating conflicts/manual patches.
- Modify `core/command-prompts/init.md`: describe `--dry-run`, call `specguard.hooks_merge`, write `plugin_source`.
- Modify `core/command-prompts/check.md`: make missing settings hooks an error.
- Modify `core/command-prompts/upgrade.md`: call `specguard.upgrade`, define legacy `plugin_source` behavior.
- Modify `adapters/claude/plugin/commands/init.md.tpl`: add `[--dry-run]` to `argument-hint`.
- Modify `adapters/claude/manifest.yaml` and/or render pipeline if needed so release tarball includes importable Python modules.
- Modify `core/version` and `pyproject.toml`: bump to `0.2.0`.
- Create `tests/test_init_merge_hooks.py`: TDD coverage for hook merge behavior.
- Create `tests/test_dogfood_upgrade.py`: TDD coverage for marker upgrade behavior.
- Create `.github/workflows/release.yml`: build 3 layout tarballs on tag.
- Modify `README.md`: user-first install instructions.
- Modify `CHANGELOG.md`: add v0.2.0 section.
- Modify `docs/specguard/design.md`: final test count and verified commit after implementation.

---

### Task 1: Hook Merge Module

**Files:**
- Create: `src/specguard/hooks_merge.py`
- Create: `tests/test_init_merge_hooks.py`

- [ ] **Step 1: Write failing tests for hook merge**

Create `tests/test_init_merge_hooks.py`:

```python
import json
from pathlib import Path

import pytest

from specguard.hooks_merge import HookMergeError, merge_hooks_file


def snippet() -> dict:
    return {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "statusMessage": "specguard: inject five laws", "command": "echo specguard"}]}
            ],
            "Stop": [
                {"hooks": [{"type": "command", "statusMessage": "specguard: design sync reminder", "command": "echo stop"}]}
            ],
        }
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_merge_creates_settings_when_missing(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    assert result.changed is True
    data = read_json(settings_path)
    assert data["hooks"]["SessionStart"][0]["hooks"][0]["statusMessage"] == "specguard: inject five laws"
    assert data["hooks"]["Stop"][0]["hooks"][0]["statusMessage"] == "specguard: design sync reminder"


def test_merge_preserves_non_specguard_hooks(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())
    write_json(settings_path, {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "statusMessage": "custom: keep", "command": "echo keep"}]}]}}})

    merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    entries = read_json(settings_path)["hooks"]["SessionStart"]
    assert entries[0]["hooks"][0]["statusMessage"] == "custom: keep"
    assert entries[1]["hooks"][0]["statusMessage"] == "specguard: inject five laws"


def test_merge_is_idempotent(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)
    first = settings_path.read_text()
    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)
    second = settings_path.read_text()

    assert result.changed is False
    assert second == first


def test_dry_run_does_not_write_settings(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())

    result = merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path, dry_run=True)

    assert result.changed is True
    assert "specguard: inject five laws" in result.diff
    assert not settings_path.exists()


def test_invalid_settings_json_is_not_overwritten(tmp_path: Path):
    snippet_path = tmp_path / ".specguard/hooks.snippet.json"
    settings_path = tmp_path / ".claude/settings.json"
    write_json(snippet_path, snippet())
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("{invalid")

    with pytest.raises(HookMergeError):
        merge_hooks_file(settings_path=settings_path, snippet_path=snippet_path)

    assert settings_path.read_text() == "{invalid"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest tests/test_init_merge_hooks.py -q
```

Expected: fails with `ModuleNotFoundError: No module named 'specguard.hooks_merge'`.

- [ ] **Step 3: Implement minimal hook merge module**

Create `src/specguard/hooks_merge.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import tempfile
from typing import Any


class HookMergeError(ValueError):
    pass


@dataclass(frozen=True)
class HookMergeResult:
    changed: bool
    diff: str


def merge_hooks_file(settings_path: Path, snippet_path: Path, dry_run: bool = False) -> HookMergeResult:
    snippet = _read_json(snippet_path, "hooks snippet")
    if not isinstance(snippet, dict) or not isinstance(snippet.get("hooks"), dict):
        raise HookMergeError(f"invalid hooks snippet: {snippet_path}")

    if settings_path.exists():
        settings = _read_json(settings_path, "Claude settings")
    else:
        settings = {"hooks": {}}

    if not isinstance(settings, dict):
        raise HookMergeError(f"Claude settings must be a JSON object: {settings_path}")

    before = _format_json(settings)
    merged = merge_hooks(settings, snippet)
    after = _format_json(merged)
    diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(settings_path), tofile=str(settings_path)))
    changed = before != after

    if changed and not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(settings_path, after)

    return HookMergeResult(changed=changed, diff=diff)


def merge_hooks(settings: dict[str, Any], snippet: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(settings))
    merged_hooks = merged.setdefault("hooks", {})
    if not isinstance(merged_hooks, dict):
        raise HookMergeError("Claude settings 'hooks' must be an object")

    for event, snippet_entries in snippet["hooks"].items():
        existing_entries = merged_hooks.get(event, [])
        if not isinstance(existing_entries, list) or not isinstance(snippet_entries, list):
            raise HookMergeError(f"hook event must be a list: {event}")
        kept = [entry for entry in existing_entries if not _is_specguard_entry(entry)]
        merged_hooks[event] = kept + snippet_entries

    return merged


def _is_specguard_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return False
    return any(isinstance(hook, dict) and str(hook.get("statusMessage", "")).startswith("specguard:") for hook in hooks)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HookMergeError(f"invalid {label} JSON: {path}: {exc}") from exc


def _format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
```

- [ ] **Step 4: Run hook merge tests**

Run:

```bash
uv run pytest tests/test_init_merge_hooks.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/specguard/hooks_merge.py tests/test_init_merge_hooks.py
git commit -m "feat: add specguard hook merge module"
```

---

### Task 2: Upgrade Module

**Files:**
- Create: `src/specguard/upgrade.py`
- Create: `tests/test_dogfood_upgrade.py`

- [ ] **Step 1: Write failing tests for marker upgrade**

Create `tests/test_dogfood_upgrade.py`:

```python
import json
from pathlib import Path

import pytest

from specguard.upgrade import UpgradeConflict, upgrade_project


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def setup_project(root: Path) -> None:
    write(root / "CLAUDE.md", "before\n<!-- specguard:start -->\nold block\n<!-- specguard:end -->\nafter\n")
    write(root / ".claude/settings.json", json.dumps({"hooks": {"SessionStart": [{"hooks": [{"statusMessage": "custom: keep", "command": "echo keep"}]}, {"hooks": [{"statusMessage": "specguard: old", "command": "echo old"}]}]}}}, indent=2) + "\n")
    write(root / "docs/specguard/specs/TEMPLATE.md", "old specs template\n")
    write(root / "docs/specguard/decisions/TEMPLATE.md", "old decisions template\n")
    write(root / "docs/specguard/decisions/README.md", "# index\n<!-- specguard:rules:start -->\nold rules\n<!-- specguard:rules:end -->\n")
    write(root / "docs/specguard/design.md", "do not touch\n")
    write(root / ".specguard-version", 'specguard_version = "0.1.0"\nagent = "claude"\nspec = "specguard-default"\nlayout = "specguard-default"\ninstalled_at = "2026-04-30T00:00:00Z"\n')


def replacements() -> dict:
    return {
        "claude_block": "new block\n",
        "settings_hooks": {"hooks": {"SessionStart": [{"hooks": [{"statusMessage": "specguard: new", "command": "echo new"}]}]}},
        "specs_template": "new specs template\n",
        "decisions_template": "new decisions template\n",
        "decisions_readme_rules": "new rules\n",
        "version": "0.2.0",
        "plugin_source": "local-dist",
    }


def test_upgrade_replaces_marker_regions_and_preserves_other_content(tmp_path: Path):
    setup_project(tmp_path)

    result = upgrade_project(tmp_path, replacements())

    assert result.changed is True
    assert (tmp_path / "docs/specguard/design.md").read_text() == "do not touch\n"
    assert (tmp_path / "CLAUDE.md").read_text() == "before\n<!-- specguard:start -->\nnew block\n<!-- specguard:end -->\nafter\n"
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    entries = settings["hooks"]["SessionStart"]
    assert entries[0]["hooks"][0]["statusMessage"] == "custom: keep"
    assert entries[1]["hooks"][0]["statusMessage"] == "specguard: new"
    assert (tmp_path / "docs/specguard/specs/TEMPLATE.md").read_text() == "new specs template\n"
    assert (tmp_path / "docs/specguard/decisions/TEMPLATE.md").read_text() == "new decisions template\n"
    assert "new rules" in (tmp_path / "docs/specguard/decisions/README.md").read_text()
    version = (tmp_path / ".specguard-version").read_text()
    assert 'specguard_version = "0.2.0"' in version
    assert 'plugin_source = "local-dist"' in version


def test_upgrade_conflict_when_claude_marker_missing(tmp_path: Path):
    setup_project(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("no markers\n")

    with pytest.raises(UpgradeConflict):
        upgrade_project(tmp_path, replacements())

    assert (tmp_path / "CLAUDE.md").read_text() == "no markers\n"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest tests/test_dogfood_upgrade.py -q
```

Expected: fails with `ModuleNotFoundError: No module named 'specguard.upgrade'`.

- [ ] **Step 3: Implement minimal upgrade module**

Create `src/specguard/upgrade.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .hooks_merge import merge_hooks


class UpgradeConflict(ValueError):
    pass


@dataclass(frozen=True)
class UpgradeResult:
    changed: bool


def upgrade_project(root: Path, replacements: dict[str, Any]) -> UpgradeResult:
    original: dict[Path, str] = {}
    paths = [
        root / "CLAUDE.md",
        root / ".claude/settings.json",
        root / "docs/specguard/specs/TEMPLATE.md",
        root / "docs/specguard/decisions/TEMPLATE.md",
        root / "docs/specguard/decisions/README.md",
        root / ".specguard-version",
    ]
    try:
        for path in paths:
            original[path] = path.read_text()

        updated: dict[Path, str] = {}
        updated[root / "CLAUDE.md"] = _replace_between(original[root / "CLAUDE.md"], "<!-- specguard:start -->", "<!-- specguard:end -->", replacements["claude_block"])
        updated[root / ".claude/settings.json"] = _format_json(merge_hooks(json.loads(original[root / ".claude/settings.json"]), replacements["settings_hooks"]))
        updated[root / "docs/specguard/specs/TEMPLATE.md"] = replacements["specs_template"]
        updated[root / "docs/specguard/decisions/TEMPLATE.md"] = replacements["decisions_template"]
        updated[root / "docs/specguard/decisions/README.md"] = _replace_between(original[root / "docs/specguard/decisions/README.md"], "<!-- specguard:rules:start -->", "<!-- specguard:rules:end -->", replacements["decisions_readme_rules"])
        updated[root / ".specguard-version"] = _update_version(original[root / ".specguard-version"], replacements["version"], replacements["plugin_source"])
    except Exception:
        for path, text in original.items():
            path.write_text(text)
        raise

    changed = any(original[path] != text for path, text in updated.items())
    for path, text in updated.items():
        path.write_text(text)
    return UpgradeResult(changed=changed)


def _replace_between(text: str, start: str, end: str, replacement: str) -> str:
    start_idx = text.find(start)
    end_idx = text.find(end)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise UpgradeConflict(f"missing marker region: {start} ... {end}")
    before = text[: start_idx + len(start)]
    after = text[end_idx:]
    return before + "\n" + replacement + after


def _update_version(text: str, version: str, plugin_source: str) -> str:
    lines = []
    saw_version = False
    saw_source = False
    for line in text.splitlines():
        if line.startswith("specguard_version ="):
            lines.append(f'specguard_version = "{version}"')
            saw_version = True
        elif line.startswith("plugin_source ="):
            lines.append(f'plugin_source = "{plugin_source}"')
            saw_source = True
        else:
            lines.append(line)
    if not saw_version:
        lines.insert(0, f'specguard_version = "{version}"')
    if not saw_source:
        lines.append(f'plugin_source = "{plugin_source}"')
    return "\n".join(lines) + "\n"


def _format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 4: Run upgrade tests**

Run:

```bash
uv run pytest tests/test_dogfood_upgrade.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/specguard/upgrade.py tests/test_dogfood_upgrade.py
git commit -m "feat: add specguard upgrade module"
```

---

### Task 3: Render Runtime Modules into Plugin Artifact

**Files:**
- Modify: `src/specguard/render.py`
- Modify: `tests/test_render_basic.py`

- [ ] **Step 1: Write failing render test**

Add to `tests/test_render_basic.py`:

```python

def test_render_includes_runtime_modules(tmp_path: Path):
    out = tmp_path / "dist"
    render(repo_root=REPO, target="claude", layout="specguard-default", out_dir=out)
    assert (out / "runtime/specguard/hooks_merge.py").is_file()
    assert (out / "runtime/specguard/upgrade.py").is_file()
    assert (out / "runtime/specguard/__init__.py").is_file()
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
uv run pytest tests/test_render_basic.py::test_render_includes_runtime_modules -q
```

Expected: fails because `runtime/specguard/hooks_merge.py` does not exist.

- [ ] **Step 3: Copy runtime modules during render**

In `src/specguard/render.py`, after the render loop, add:

```python
    runtime_out = out_dir / "runtime/specguard"
    runtime_out.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "hooks_merge.py", "upgrade.py"):
        (runtime_out / name).write_text((repo_root / "src/specguard" / name).read_text())
```

- [ ] **Step 4: Run render test**

Run:

```bash
uv run pytest tests/test_render_basic.py::test_render_includes_runtime_modules -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/specguard/render.py tests/test_render_basic.py
git commit -m "feat: include runtime modules in plugin render"
```

---

### Task 4: Command Prompt Updates

**Files:**
- Modify: `core/command-prompts/init.md`
- Modify: `core/command-prompts/check.md`
- Modify: `core/command-prompts/upgrade.md`
- Modify: `adapters/claude/plugin/commands/init.md.tpl`
- Modify: `tests/test_render_claude_default.py`

- [ ] **Step 1: Write failing render assertions**

Add to `tests/test_render_claude_default.py`:

```python

def test_init_command_mentions_auto_merge_and_dry_run(dist: Path):
    cmd = (dist / "commands/init.md").read_text()
    assert "--dry-run" in cmd
    assert "specguard.hooks_merge" in cmd
    assert "plugin_source" in cmd


def test_check_command_treats_missing_hooks_as_error(dist: Path):
    cmd = (dist / "commands/check.md").read_text()
    assert "missing specguard hooks" in cmd
    assert "error" in cmd.lower()


def test_upgrade_command_mentions_python_runtime(dist: Path):
    cmd = (dist / "commands/upgrade.md").read_text()
    assert "specguard.upgrade" in cmd
    assert "plugin_source" in cmd
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest tests/test_render_claude_default.py -q
```

Expected: new tests fail.

- [ ] **Step 3: Update command prompts**

Modify these sections:

`adapters/claude/plugin/commands/init.md.tpl` frontmatter:

```markdown
argument-hint: "[--ai <agent>] [--spec <tool>] [--dry-run]"
```

`core/command-prompts/init.md` supported flags:

```markdown
- `--dry-run`                         default: false; print planned file writes and hook merge diff without writing files
```

Replace init Step 5 with:

```markdown
5. Hooks for `.claude/settings.json`:
   - Write the embedded JSON below verbatim to `.specguard/hooks.snippet.json` unless `--dry-run` is set.
   - Merge it into `.claude/settings.json` by calling the rendered plugin runtime module:
     `python3 -c 'import sys; sys.path.insert(0, "runtime"); from specguard.hooks_merge import merge_hooks_file; print(merge_hooks_file(Path(".claude/settings.json"), Path(".specguard/hooks.snippet.json"), dry_run=<true|false>).diff)'`
   - Preserve non-specguard hooks. Replace existing specguard hooks by `statusMessage` prefix `specguard:`.
   - If `.claude/settings.json` is invalid JSON, stop and tell the user to fix it manually.
```

Also update `.specguard-version` block to include:

```toml
plugin_source = "local-dist"
```

`core/command-prompts/check.md` item 12:

```markdown
12. `.claude/settings.json` contains hooks tagged with `statusMessage` prefix `specguard:` matching `.specguard/hooks.snippet.json`; if missing, report an error.
```

`core/command-prompts/upgrade.md` step 3:

```markdown
3. Build and apply the upgrade plan by calling `specguard.upgrade` from the rendered plugin runtime. Treat missing `plugin_source` as `local-dist` and write it back after upgrade.
```

- [ ] **Step 4: Run render tests**

Run:

```bash
uv run pytest tests/test_render_claude_default.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core/command-prompts/init.md core/command-prompts/check.md core/command-prompts/upgrade.md adapters/claude/plugin/commands/init.md.tpl tests/test_render_claude_default.py
git commit -m "feat: update specguard command prompts for v0.2"
```

---

### Task 5: Version and Release Workflow

**Files:**
- Modify: `core/version`
- Modify: `pyproject.toml`
- Create: `.github/workflows/release.yml`
- Create/Modify: `tests/test_release_workflow.py`

- [ ] **Step 1: Write workflow structure test**

Create `tests/test_release_workflow.py`:

```python
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def test_release_workflow_builds_three_layout_tarballs():
    workflow = yaml.safe_load((REPO / ".github/workflows/release.yml").read_text())
    assert workflow["on"]["push"]["tags"] == ["v*"]
    text = (REPO / ".github/workflows/release.yml").read_text()
    assert "specguard-default" in text
    assert "superpowers" in text
    assert "openspec-sidecar" in text
    assert "tar -czf" in text
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
uv run pytest tests/test_release_workflow.py -q
```

Expected: fails because workflow file does not exist.

- [ ] **Step 3: Bump versions and create workflow**

Set `core/version` to:

```text
0.2.0
```

Set `pyproject.toml` project version to:

```toml
version = "0.2.0"
```

Create `.github/workflows/release.yml`:

```yaml
name: release

on:
  push:
    tags:
      - "v*"

jobs:
  build-plugin-artifacts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest
      - name: Render and package layouts
        run: |
          version=$(cat core/version)
          mkdir -p release
          for layout in specguard-default superpowers openspec-sidecar; do
            out="dist/claude/${layout}"
            uv run specguard-render --target claude --layout "${layout}" --out "${out}"
            tar -czf "release/specguard-claude-${layout}-v${version}.tar.gz" -C "${out}" .
          done
      - uses: softprops/action-gh-release@v2
        with:
          files: release/*.tar.gz
```

- [ ] **Step 4: Run workflow test and full tests**

Run:

```bash
uv run pytest tests/test_release_workflow.py -q
uv run pytest -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add core/version pyproject.toml .github/workflows/release.yml tests/test_release_workflow.py
git commit -m "feat: add release artifact workflow"
```

---

### Task 6: README and Changelog

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README user quickstart**

Replace the current README quickstart with:

```markdown
## Quickstart

Download a Claude plugin artifact from the latest GitHub Release and unpack it somewhere stable:

```bash
mkdir -p ~/.local/share/specguard/plugins
curl -L <release-tarball-url> | tar -xz -C ~/.local/share/specguard/plugins/specguard-default
```

Run init from inside the target project:

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default -p '/specguard:init --ai claude --spec none'
```

`/specguard:init` creates the living design / ADR / spec scaffold, updates `CLAUDE.md`, writes `.specguard/hooks.snippet.json`, and automatically merges the hooks into `.claude/settings.json`.

Run checks anytime:

```bash
claude --plugin-dir ~/.local/share/specguard/plugins/specguard-default -p '/specguard:check'
```

### Development quickstart

```bash
git clone <this repo>
cd specguard
uv sync
uv run pytest
uv run specguard-render --target claude --layout specguard-default --out dist/claude/specguard-default
```
```

- [ ] **Step 2: Update CHANGELOG**

Add above v0.1.0:

```markdown
## v0.2.0 - 2026-05-01

### Added
- GitHub Release tarball packaging for three Claude layouts.
- Automatic `.claude/settings.json` hook merge during `/specguard:init`.
- Python runtime modules for hook merge and upgrade marker replacement.
- End-to-end upgrade test coverage for v0.1.x projects.

### Changed
- `/specguard:check` reports missing specguard hooks as an error.
- `.specguard-version` includes `plugin_source`.
```

- [ ] **Step 3: Verify README no longer instructs manual hook merge in quickstart**

Run:

```bash
grep -n "manually merge\|manual merge\|手动合并" README.md || true
```

Expected: no output in quickstart. If development notes mention v0.1.x history, keep it outside quickstart.

- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: update specguard v0.2 user docs"
```

---

### Task 7: Design Sync and Final Verification

**Files:**
- Modify: `docs/specguard/design.md`

- [ ] **Step 1: Update design.md test matrix and version fields**

After implementation, update `docs/specguard/design.md`:

- `core/version` line to `0.2.0`
- test matrix to include new test files and actual test count from pytest
- `Last verified against code` to the current commit hash after implementation commits

- [ ] **Step 2: Run full tests**

Run:

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Render all layouts**

Run:

```bash
uv run specguard-render --target claude --layout specguard-default --out /tmp/specguard-default
uv run specguard-render --target claude --layout superpowers --out /tmp/specguard-superpowers
uv run specguard-render --target claude --layout openspec-sidecar --out /tmp/specguard-openspec-sidecar
```

Expected: each command prints `rendered claude/<layout> -> ...`; each output has `.claude-plugin/plugin.json`, `commands/`, `skills/`, `hooks/`, `runtime/specguard/`.

- [ ] **Step 4: Run git diff review**

Run:

```bash
git diff --stat
git diff -- docs/specguard/design.md
```

Expected: design.md reflects implemented behavior and no stale v0.1 manual merge wording remains.

- [ ] **Step 5: Commit**

```bash
git add docs/specguard/design.md
git commit -m "docs: sync design for specguard v0.2"
```
