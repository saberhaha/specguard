"""Pressure tests for UserPromptSubmit hook (specguard: adr judgement reminder).

Verifies the rendered hook script emits an ADR-judgement reminder when
the user prompt contains trigger keywords (English + Chinese), and stays
silent otherwise. Both ``prompt`` and ``user_prompt`` JSON keys are tested.
"""

from __future__ import annotations

import json

import pytest

from tests._hook_helpers import extract_hook_command, run_hook_command


EVENT = "UserPromptSubmit"
STATUS = "specguard: adr judgement reminder"


def _make_input(text: str, key: str = "prompt") -> str:
    return json.dumps({key: text})


def _is_triggered(out: dict) -> bool:
    spec = out.get("hookSpecificOutput", {})
    return (
        spec.get("hookEventName") == "UserPromptSubmit"
        and "ADR" in spec.get("additionalContext", "")
    )


@pytest.mark.parametrize(
    "text",
    [
        "please write spec for foo",
        "write plan now",
        "implement now",
        "开始实施",
        "写 spec",
        "写 plan",
    ],
)
def test_trigger_keyword_emits_reminder(rendered_snippet, text):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(text))
    assert _is_triggered(out)


@pytest.mark.parametrize(
    "text",
    [
        "tell me about the design",
        "what does this hook do?",
        "explain ADR-0009",
    ],
)
def test_no_trigger_normal_chat(rendered_snippet, text):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input(text))
    assert out == {}


def test_trigger_in_middle_of_sentence(rendered_snippet):
    """grep -i is substring-based — trigger word inside a longer sentence still fires."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(
        cmd, _make_input("hey, please write spec for the new feature")
    )
    assert _is_triggered(out)


def test_user_prompt_key_also_works(rendered_snippet):
    """Hook supports both 'prompt' and 'user_prompt' JSON keys."""
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, _make_input("write plan", key="user_prompt"))
    assert _is_triggered(out)


def test_empty_prompt_no_trigger(rendered_snippet):
    cmd = extract_hook_command(rendered_snippet, EVENT, STATUS)
    out, _ = run_hook_command(cmd, "{}")
    assert out == {}
