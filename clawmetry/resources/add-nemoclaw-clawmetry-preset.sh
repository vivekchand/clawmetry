#!/usr/bin/env bash

set -euo pipefail

PRESET_NAME="clawmetry"
PRESETS_DIR="${NEMOCLAW_PRESETS_DIR:-$HOME/.nemoclaw/source/nemoclaw-blueprint/policies/presets}"
TARGET_PATH="${PRESETS_DIR}/${PRESET_NAME}.yaml"

if ! command -v nemoclaw >/dev/null 2>&1; then
  echo "nemoclaw is not installed or not on PATH." >&2
  exit 1
fi

if ! command -v install >/dev/null 2>&1; then
  echo "'install' is required but was not found on PATH." >&2
  exit 1
fi

tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

list_sandboxes() {
  nemoclaw list | awk '
    /^  Sandboxes:/ { in_list=1; next }
    /^  \* = default sandbox/ { in_list=0; next }
    in_list && /^    [^ ]/ {
      name=$1
      gsub(/\*/, "", name)
      if (name != "") print name
    }
  '
}

cat >"$tmpfile" <<'EOF'
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

preset:
  name: clawmetry
  description: "ClawMetry Cloud metrics and telemetry access"

network_policies:
  clawmetry:
    name: clawmetry
    endpoints:
      - host: "*.clawmetry.com"
        port: 443
        access: full
      - host: clawmetry.com
        port: 443
        access: full
    binaries:
      - { path: /usr/bin/python3* }
      - { path: /usr/local/bin/python3* }
      - { path: /sandbox/.openclaw/workspace/.venv/bin/python* }
      - { path: /sandbox/.openclaw/workspace/.venv/bin/clawmetry* }
      - { path: /sandbox/.venv/bin/python* }
      - { path: /sandbox/.venv/bin/clawmetry* }
EOF

if [ -w "$PRESETS_DIR" ] || { [ -e "$TARGET_PATH" ] && [ -w "$TARGET_PATH" ]; }; then
  install -d -m 755 "$PRESETS_DIR"
  install -m 644 "$tmpfile" "$TARGET_PATH"
else
  if ! command -v sudo >/dev/null 2>&1; then
    echo "Need to write ${TARGET_PATH}, but sudo is not available." >&2
    exit 1
  fi
  sudo install -d -m 755 "$PRESETS_DIR"
  sudo install -m 644 "$tmpfile" "$TARGET_PATH"
fi

echo "Installed preset at ${TARGET_PATH}"

declare -a sandbox_names
if [ "$#" -gt 0 ]; then
  sandbox_names=("$@")
else
  while IFS= read -r sandbox_name; do
    [ -n "$sandbox_name" ] && sandbox_names+=("$sandbox_name")
  done < <(list_sandboxes)
fi

if [ "${#sandbox_names[@]}" -eq 0 ]; then
  echo "No NemoClaw sandboxes found." >&2
  exit 1
fi

for sandbox_name in "${sandbox_names[@]}"; do
  echo "Applying preset '${PRESET_NAME}' to sandbox '${sandbox_name}'..."
  printf '%s\ny\n' "$PRESET_NAME" | nemoclaw "$sandbox_name" policy-add
  echo "Preset '${PRESET_NAME}' applied to sandbox '${sandbox_name}'."
done
