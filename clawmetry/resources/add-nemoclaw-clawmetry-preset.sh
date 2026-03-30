#!/usr/bin/env bash
# Installs ClawMetry + PyPI presets for NemoClaw sandboxes.
# Fixes slow/broken pip installs inside sandboxes by whitelisting PyPI endpoints.
# Usage: ./add-nemoclaw-clawmetry-preset.sh [sandbox1 sandbox2 ...]

set -euo pipefail

PRESETS_DIR="${NEMOCLAW_PRESETS_DIR:-$HOME/.nemoclaw/source/nemoclaw-blueprint/policies/presets}"

if ! command -v nemoclaw >/dev/null 2>&1; then
  echo "Error: nemoclaw not on PATH." >&2
  exit 1
fi

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

install_preset() {
  local name="$1" yaml="$2"
  local target="${PRESETS_DIR}/${name}.yaml"
  local tmp
  tmp="$(mktemp)"
  trap 'rm -f "$tmp"' RETURN
  printf '%s\n' "$yaml" > "$tmp"

  if [ -w "$PRESETS_DIR" ] || { [ -e "$target" ] && [ -w "$target" ]; }; then
    install -d -m 755 "$PRESETS_DIR"
    install -m 644 "$tmp" "$target"
  else
    sudo install -d -m 755 "$PRESETS_DIR"
    sudo install -m 644 "$tmp" "$target"
  fi
  echo "Installed $name at $target"
}

CLAWMETRY_YAML=$(cat <<'YAML'
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
YAML
)

PYPI_YAML=$(cat <<'YAML'
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

preset:
  name: pypi
  description: "Python Package Index (PyPI) access"

network_policies:
  pypi:
    name: pypi
    endpoints:
      - host: pypi.org
        port: 443
        access: full
      - host: files.pythonhosted.org
        port: 443
        access: full
    binaries:
      - { path: /usr/bin/python3* }
      - { path: /usr/bin/pip* }
      - { path: /usr/local/bin/python3* }
      - { path: /usr/local/bin/pip* }
      - { path: /sandbox/.venv/bin/python* }
      - { path: /sandbox/.venv/bin/pip* }
      - { path: /sandbox/.local/bin/pip* }
      - { path: /usr/local/bin/uv }
      - { path: /sandbox/.local/bin/uv }
      - { path: /sandbox/.uv/bin/uv }
      - { path: /sandbox/.cargo/bin/uv }
      - { path: /sandbox/.uv/python/*/python* }
YAML
)

echo "Installing presets..."
install_preset "clawmetry" "$CLAWMETRY_YAML"
install_preset "pypi" "$PYPI_YAML"

declare -a sandbox_names=()
if [ "$#" -gt 0 ]; then
  sandbox_names=("$@")
else
  while IFS= read -r name; do
    [ -n "$name" ] && sandbox_names+=("$name")
  done < <(list_sandboxes)
fi

if [ "${#sandbox_names[@]}" -eq 0 ]; then
  echo "No sandboxes found." >&2
  exit 0
fi

for sb in "${sandbox_names[@]}"; do
  echo "Applying to sandbox '$sb'..."
  for p in clawmetry pypi; do
    printf '%s\ny\n' "$p" | nemoclaw "$sb" policy-add 2>/dev/null \
      && echo "  Done: $p" \
      || echo "  Warning: $p (may already be applied)"
  done
done

echo ""
echo "Done. Restart sandboxes for changes to take effect."
echo "Then inside the sandbox run:"
echo "  pip install --break-system-packages uv && uv pip install clawmetry"
