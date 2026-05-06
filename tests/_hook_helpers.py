"""Helpers for shell-decision pressure tests of specguard hooks (ADR-0009)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def extract_hook_command(snippet: dict[str, Any], event: str, status_message: str) -> str:
    """Locate a hook command by event name + statusMessage in a rendered snippet.

    Args:
        snippet: Parsed JSON content of `hooks/settings.json.snippet`.
        event: Top-level hook event name, e.g. "SessionStart", "PreToolUse",
            "Stop", "UserPromptSubmit".
        status_message: The `statusMessage` field that uniquely identifies the
            hook entry within the event group (e.g. "specguard: block dated design").

    Returns:
        The shell command string to run.

    Raises:
        KeyError: if event or matching statusMessage is not found.
    """
    groups = snippet["hooks"][event]
    for group in groups:
        for hook in group.get("hooks", []):
            if hook.get("statusMessage") == status_message:
                return hook["command"]
    raise KeyError(
        f"hook with event={event!r} statusMessage={status_message!r} not found"
    )


def run_hook_command(
    command: str,
    stdin_json: str = "{}",
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    timeout: float = 10.0,
) -> tuple[dict[str, Any], str]:
    """Run a hook command via `sh -c` with mocked stdin and return parsed stdout.

    Args:
        command: The shell command (single string).
        stdin_json: JSON text fed to the command's stdin.
        env: Optional process environment (merged with os.environ if None left
            untouched, callers should pass full env if they need overrides).
        cwd: Working directory for the subprocess.
        timeout: Hard timeout in seconds.

    Returns:
        Tuple of (parsed_stdout, raw_stdout_text). Empty stdout returns ({}, "").

    Raises:
        json.JSONDecodeError: if non-empty stdout is not valid JSON.
        subprocess.TimeoutExpired: on hook timeout.
    """
    result = subprocess.run(
        ["sh", "-c", command],
        input=stdin_json,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=str(cwd) if cwd else None,
    )
    raw = result.stdout
    stripped = raw.strip()
    if not stripped:
        return {}, raw
    # Use raw_decode so trailing characters (e.g. an extra '}' from hook
    # template typos that Claude Code's lenient parser tolerates) do not
    # break the test. ADR-0009 freezes hook behavior; format bugs in the
    # hook stdout are recorded by individual test cases, not by failing
    # this helper.
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(stripped)
    return obj, raw
