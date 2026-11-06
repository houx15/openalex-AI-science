#!/usr/bin/env bash
# Block commits whose staged changes contain credential-like strings.
# Patterns target real credential formats, not words like "secret" in paper titles.
set -euo pipefail
patterns='(AKIA|ASIA)[A-Z0-9]{16}|X-Amz-(Signature|Security-Token|Credential)=|-----BEGIN [A-Z ]*PRIVATE KEY-----|"key"[[:space:]]*:[[:space:]]*"[0-9a-f]{32}"|(api[_-]?key|access[_-]?token|secret[_-]?access[_-]?key)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_-]{16,}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}'
if git diff --cached -U0 --no-color | grep '^+' | grep -nEi "$patterns"; then
  echo "pre-commit: possible credential in staged changes (lines above). Commit blocked." >&2
  exit 1
fi
