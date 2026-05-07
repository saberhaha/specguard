{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: inject five laws",
            "command": "printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"## SpecGuard governance laws\\n1. {{ paths.design }} is the single current truth.\\n2. ADR archive is at {{ paths.decisions_dir }}/. Read existing ADRs before writing a new one.\\n3. Do not create dated design files. New slices go to *-spec.md.\\n4. ADR is only for: interface semantics, data format, cross-module dependency, external dependency, overriding prior design.\\n5. Brainstorm must produce an ADR judgement before writing a plan.\"}}}'"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: block dated design",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *{{ paths.specs_dir }}/*-design.md) printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: dated design files are forbidden. Update {{ paths.design }} or write {{ paths.specs_dir }}/<topic>-spec.md instead.\"}}}' ;; *) printf '%s\\n' '{}' ;; esac"
          },
          {
            "type": "command",
            "statusMessage": "specguard: validate adr filename",
            "command": "f=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"tool_input\",{}).get(\"file_path\",\"\"))'); case \"$f\" in *{{ paths.decisions_dir }}/*.md) base=$(basename \"$f\"); if echo \"$base\" | grep -qE '^[0-9]{4}-[a-z0-9-]+\\.md$|^TEMPLATE\\.md$|^README\\.md$'; then printf '%s\\n' '{}'; else printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"specguard: ADR filename must be NNNN-kebab-case.md\"}}}'; fi ;; *) printf '%s\\n' '{}' ;; esac"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: design sync reminder",
            "command": "cd \"$CLAUDE_PROJECT_DIR\" 2>/dev/null || exit 0; src_changed=$(git diff --name-only HEAD 2>/dev/null | grep -c '^src/' || true); doc_changed=$(git diff --name-only HEAD 2>/dev/null | grep -cE '^({{ paths.design | regex_escape }}|{{ paths.decisions_dir | regex_escape }}/)' || true); if [ \"$src_changed\" -gt 0 ] && [ \"$doc_changed\" -eq 0 ]; then printf '%s\\n' '{\"systemMessage\":\"specguard: src/ changed but neither design.md nor decisions/ touched.\"}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "statusMessage": "specguard: adr judgement reminder",
            "command": "p=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"prompt\") or d.get(\"user_prompt\") or \"\")'); if echo \"$p\" | grep -qiE '(write spec|write plan|implement now|开始实施|写 spec|写 plan)'; then printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"specguard: produce the ADR judgement section before entering spec/plan, and wait for user approval.\"}}}'; else printf '%s\\n' '{}'; fi"
          }
        ]
      }
    ]
  }
}
