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
    diff = "".join(
        difflib.unified_diff(
            before.splitlines(True),
            after.splitlines(True),
            fromfile=str(settings_path),
            tofile=str(settings_path),
        )
    )
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
    return any(
        isinstance(hook, dict) and str(hook.get("statusMessage", "")).startswith("specguard:")
        for hook in hooks
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HookMergeError(f"invalid {label} JSON: {path}: {exc}") from exc


def _format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
