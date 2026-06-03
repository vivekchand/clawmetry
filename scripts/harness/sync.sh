#!/usr/bin/env bash
# Sync every monitored agent-harness source into a local checkout so we can audit
# what each exposes vs what ClawMetry observes. Reads scripts/harness/manifest.json.
#
# Idempotent: first run clones (shallow), later runs fast-forward pull. repo=null
# entries (closed source / URL unknown) are skipped with a note.
#
#   scripts/harness/sync.sh                 # clone/pull into ../harness (manifest default)
#   HARNESS_DIR=/tmp/h scripts/harness/sync.sh   # override target dir
#   DEPTH=50 scripts/harness/sync.sh        # deeper history (default: shallow depth=1)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
MANIFEST="$HERE/manifest.json"
[ -f "$MANIFEST" ] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }

# Resolve clone dir: env override > manifest clone_dir (relative to repo root) > ../harness
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
DEFAULT_DIR="$(python3 -c "import json,os;m=json.load(open('$MANIFEST'));print(os.path.normpath(os.path.join('$REPO_ROOT', m.get('clone_dir','../harness'))))")"
HARNESS_DIR="${HARNESS_DIR:-$DEFAULT_DIR}"
DEPTH="${DEPTH:-1}"
mkdir -p "$HARNESS_DIR"
echo "[harness-sync] target: $HARNESS_DIR (depth=$DEPTH)"

# Emit "runtime<TAB>repo" for entries that have a repo.
python3 - "$MANIFEST" <<'PY' | while IFS=$'\t' read -r rt repo; do
import json, sys
m = json.load(open(sys.argv[1]))
for h in m["harnesses"]:
    if h.get("repo"):
        print(f"{h['runtime']}\t{h['repo']}")
PY
  dest="$HARNESS_DIR/$rt"
  if [ -d "$dest/.git" ]; then
    echo "[harness-sync] $rt: pull"
    git -C "$dest" remote set-url origin "$repo" 2>/dev/null || true
    git -C "$dest" fetch --depth "$DEPTH" origin >/dev/null 2>&1 \
      && git -C "$dest" reset --hard "@{upstream}" >/dev/null 2>&1 \
      && echo "[harness-sync] $rt: up to date @ $(git -C "$dest" rev-parse --short HEAD)" \
      || echo "[harness-sync] $rt: pull FAILED (kept existing checkout)"
  else
    echo "[harness-sync] $rt: clone $repo"
    rm -rf "$dest"
    if git clone --depth "$DEPTH" "$repo" "$dest" >/dev/null 2>&1; then
      echo "[harness-sync] $rt: cloned @ $(git -C "$dest" rev-parse --short HEAD)"
    else
      echo "[harness-sync] $rt: clone FAILED ($repo)"
    fi
  fi
done

# Report the skipped (closed / unknown) harnesses so the gap is visible, not silent.
python3 - "$MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
skipped = [h for h in m["harnesses"] if not h.get("repo")]
if skipped:
    print("[harness-sync] no public source (audited from on-disk format instead): "
          + ", ".join(f"{h['runtime']} ({h.get('note','')[:40]})" for h in skipped))
PY
echo "[harness-sync] done."
