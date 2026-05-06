"""Pressure tests for PreToolUse:Write ADR filename validation hook.

Verifies the rendered hook script denies Write attempts to
``<decisions_dir>/<bad-name>.md`` while allowing valid ADR filenames
(``NNNN-kebab-case.md``), ``README.md``, and ``TEMPLATE.md``.
"""

from __future__ import annotations

import json

from tests._hook_helpers import extract_hook_command, run_hook_command


EVENT = "PreToolUse"
STATUS = "specguard: validate adr filename"

DECISIONS_DIR = "docs/specguard/decisions"


def _make_input(path: str) -> str:
    return json.dumps({"tool_input": {"file_path": path}})


def _is_deny(out: dict) -> bool:
    return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def test_allow_valid_adr_name_simple(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/0001-foo.md"))
    assert out == {}


def test_allow_valid_adr_name_multiword(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/0042-multi-word-name.md"))
    assert out == {}


def test_allow_valid_adr_high_number(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/9999-z-z-z.md"))
    assert out == {}


def test_allow_readme(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/README.md"))
    assert out == {}


def test_allow_template(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/TEMPLATE.md"))
    assert out == {}


def test_deny_two_digit_number(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/01-foo.md"))
    assert _is_deny(out)


def test_deny_three_digit_number(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/001-foo.md"))
    assert _is_deny(out)


def test_deny_uppercase_slug(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/0001-FOO.md"))
    assert _is_deny(out)


def test_deny_space_in_name(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/0001 foo.md"))
    assert _is_deny(out)


def test_deny_no_number_prefix(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(f"{DECISIONS_DIR}/foo.md"))
    assert _is_deny(out)


def test_allow_non_decisions_path(rendered_snippet):
    """File outside decisions/ must not be checked even if filename violates."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input("docs/specguard/specs/0001-foo.md"))
    assert out == {}
