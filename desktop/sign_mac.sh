#!/usr/bin/env bash
# Sign + (optionally) notarize + staple a ClawMetry.app produced by
# desktop/build_mac.spec. Idempotent; safe to re-run.
#
# Usage:
#     desktop/sign_mac.sh path/to/ClawMetry.app
#
# Environment variables the script reads:
#     MACOS_SIGN_IDENTITY            (required)  Full codesign identity string, e.g.
#                                                "Developer ID Application: InstaLabs LLC (8LVH596RA5)"
#     APPLE_ID, APPLE_TEAM_ID,       (optional)  If all three are set, the script
#     APPLE_APP_SPECIFIC_PASSWORD                also submits to notarytool and staples.
#                                                Otherwise it just signs and stops.
#     ENTITLEMENTS                   (optional)  Path to entitlements.plist. Defaults
#                                                to desktop/entitlements.plist next to
#                                                this script.
#
# The CI workflow (.github/workflows/desktop-artifacts.yml) does the same
# steps directly in YAML; this script is for local one-off signing.

set -euo pipefail

APP="${1:-}"
if [[ -z "$APP" || ! -d "$APP" ]]; then
  echo "usage: $0 path/to/ClawMetry.app" >&2
  exit 2
fi

: "${MACOS_SIGN_IDENTITY:?set MACOS_SIGN_IDENTITY to your Developer ID string}"

HERE="$(cd "$(dirname "$0")" && pwd)"
ENTITLEMENTS="${ENTITLEMENTS:-$HERE/entitlements.plist}"
if [[ ! -f "$ENTITLEMENTS" ]]; then
  echo "entitlements plist not found at $ENTITLEMENTS" >&2
  exit 3
fi

echo "== codesign =="
# --deep signs every embedded framework and dylib; --timestamp is
# required for notarization; --options=runtime turns on Hardened
# Runtime which the entitlements file then relaxes.
codesign --force --deep --timestamp \
  --options runtime \
  --entitlements "$ENTITLEMENTS" \
  --sign "$MACOS_SIGN_IDENTITY" \
  "$APP"

echo "== verify =="
codesign --verify --deep --strict --verbose=2 "$APP"

if [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "${APPLE_APP_SPECIFIC_PASSWORD:-}" ]]; then
  echo "== notarize =="
  TMPZIP="$(mktemp -d)/ClawMetry.zip"
  ditto -c -k --keepParent "$APP" "$TMPZIP"
  xcrun notarytool submit "$TMPZIP" \
    --apple-id "$APPLE_ID" \
    --team-id "$APPLE_TEAM_ID" \
    --password "$APPLE_APP_SPECIFIC_PASSWORD" \
    --wait
  echo "== staple =="
  xcrun stapler staple "$APP"
  xcrun stapler validate "$APP"
  rm -f "$TMPZIP"
else
  echo "== skipping notarization (APPLE_ID / APPLE_TEAM_ID / APPLE_APP_SPECIFIC_PASSWORD not all set) =="
  echo "   The app is signed but will still trigger Gatekeeper warnings on first launch."
fi

echo "== done =="
