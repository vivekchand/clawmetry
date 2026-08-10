#!/usr/bin/env bash
# Sign + notarize + staple a ClawMetry.app or the wrapping .dmg.
# Idempotent; safe to re-run.
#
# Usage:
#     desktop/sign_mac.sh path/to/ClawMetry.app       # or .dmg
#
# Environment variables the script reads:
#     MACOS_SIGN_IDENTITY            (required)  Full codesign identity string, e.g.
#                                                "Developer ID Application: InstaLabs LLC (8LVH596RA5)"
#     APPLE_ID, APPLE_TEAM_ID,       (optional)  If all three are set, the script
#     APPLE_APP_SPECIFIC_PASSWORD                also submits to notarytool and staples.
#                                                Otherwise it just signs and stops.
#     ENTITLEMENTS                   (optional)  Path to entitlements.plist. Defaults
#                                                to desktop/entitlements.plist next to
#                                                this script. Only used when signing a .app.

set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "usage: $0 path/to/ClawMetry.app-or-dmg" >&2
  exit 2
fi
if [[ ! -e "$TARGET" ]]; then
  echo "not found: $TARGET" >&2
  exit 2
fi

: "${MACOS_SIGN_IDENTITY:?set MACOS_SIGN_IDENTITY to your Developer ID string}"

HERE="$(cd "$(dirname "$0")" && pwd)"
ENTITLEMENTS="${ENTITLEMENTS:-$HERE/entitlements.plist}"

kind="unknown"
case "$TARGET" in
  *.app)  kind="app" ;;
  *.dmg)  kind="dmg" ;;
esac
if [[ "$kind" == "unknown" ]]; then
  echo "target must end in .app or .dmg (got $TARGET)" >&2
  exit 2
fi

echo "== codesign ($kind) =="
if [[ "$kind" == "app" ]]; then
  if [[ ! -f "$ENTITLEMENTS" ]]; then
    echo "entitlements plist not found at $ENTITLEMENTS" >&2
    exit 3
  fi
  # --deep signs every embedded framework and dylib; --timestamp is
  # required for notarization; --options=runtime turns on Hardened
  # Runtime which the entitlements file then relaxes.
  codesign --force --deep --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$MACOS_SIGN_IDENTITY" \
    "$TARGET"
else
  # DMGs don't take entitlements; sign the container only.
  codesign --force --timestamp --sign "$MACOS_SIGN_IDENTITY" "$TARGET"
fi

echo "== verify =="
codesign --verify --verbose=2 "$TARGET"

if [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "${APPLE_APP_SPECIFIC_PASSWORD:-}" ]]; then
  echo "== notarize =="
  if [[ "$kind" == "app" ]]; then
    TMPZIP="$(mktemp -d)/$(basename "$TARGET").zip"
    ditto -c -k --keepParent "$TARGET" "$TMPZIP"
    SUBMIT="$TMPZIP"
  else
    SUBMIT="$TARGET"
  fi
  xcrun notarytool submit "$SUBMIT" \
    --apple-id "$APPLE_ID" \
    --team-id "$APPLE_TEAM_ID" \
    --password "$APPLE_APP_SPECIFIC_PASSWORD" \
    --wait
  echo "== staple =="
  xcrun stapler staple "$TARGET"
  xcrun stapler validate "$TARGET"
  [[ "$kind" == "app" ]] && rm -f "$SUBMIT" || true
else
  echo "== skipping notarization (APPLE_ID / APPLE_TEAM_ID / APPLE_APP_SPECIFIC_PASSWORD not all set) =="
  echo "   The $kind is signed but will still trigger Gatekeeper warnings."
fi

echo "== done =="
