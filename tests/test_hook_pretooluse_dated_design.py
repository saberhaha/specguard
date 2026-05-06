"""Pressure tests for PreToolUse:Write dated-design hook.

Verifies the rendered hook script denies Write attempts targeting
``<specs_dir>/*-design.md`` while allowing legitimate file writes.
"""

from __future__ import annotations

import json

import pytest

from tests._hook_helpers import extract_hook_command, run_hook_command


EVENT = "PreToolUse"
STATUS = "specguard: block dated design"

SPECS_DIR = "docs/specguard/specs"


def _make_input(path: str) -> str:
    return json.dumps({"tool_input": {"file_path": path}})


def _is_deny(out: dict) -> bool:
    return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def test_block_dated_design_at_specs_root(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{SPECS_DIR}/foo-design.md"))
    assert _is_deny(out)


def test_block_dated_design_in_subdir(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{SPECS_DIR}/v0/foo-design.md"))
    assert _is_deny(out)


def test_allow_spec_file(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{SPECS_DIR}/foo-spec.md"))
    assert out == {}


def test_allow_design_md_root(rendered_snippet):
    """design.md itself is not inside specs/ — must not be blocked."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input("docs/specguard/design.md"))
    assert out == {}


def test_allow_other_path(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input("src/foo.py"))
    assert out == {}


@pytest.mark.xfail(strict=True, reason="known: hook is case-sensitive on extension (.MD not blocked)")
def test_known_limitation_uppercase_extension(rendered_snippet):
    """Current hook glob is *-design.md (lowercase). An uppercase .MD extension
    bypasses the check. Locked as xfail per ADR-0009: hook logic not modified
    in this slice. If a future slice fixes this, the test will fail (strict=True)
    signalling the assertion should flip to assert _is_deny(out)."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{SPECS_DIR}/foo-design.MD"))
    assert _is_deny(out)
