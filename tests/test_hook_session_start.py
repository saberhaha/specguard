"""Pressure tests for the SessionStart hook (specguard: inject five laws).

Verifies the rendered hook script emits the SessionStart event with the
five governance laws and the layout's resolved paths substituted in.
"""

from __future__ import annotations

from tests._hook_helpers import extract_hook_command, run_hook_command


EVENT = "SessionStart"
STATUS = "specguard: inject five laws"


def test_session_start_emits_five_laws(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, "{}")

    spec = out["hookSpecificOutput"]
    assert spec["hookEventName"] == "SessionStart"
    ctx = spec["additionalContext"]
    # Each of the five laws must be present (key phrases).
    assert "single current truth" in ctx
    assert "ADR archive is at" in ctx
    assert "dated design files" in ctx
    assert "interface semantics" in ctx
    assert "Brainstorm must produce an ADR judgement" in ctx


def test_session_start_paths_substituted(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, raw = run_hook_command(cmd, "{}")

    ctx = out["hookSpecificOutput"]["additionalContext"]
    # Layout-specific paths injected via render.
    assert "docs/specguard/design.md" in ctx
    assert "docs/specguard/decisions" in ctx
    # No unresolved Jinja markers.
    assert "{{" not in raw
    assert "{{ paths" not in ctx
