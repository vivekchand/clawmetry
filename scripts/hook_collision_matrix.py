#!/usr/bin/env python3
"""Hook-collision reproduction harness (WO-8).

Runs ClawMetry's Claude Code hook installers against a *foreign* installer on
one settings.json, in both orders, and diffs the file at every step.

Why this exists
---------------
GitKraken's GitLens shells out to ``gk ai hook install claude-code --force``
on a very large install base.  The merge behaviour lives inside a closed
binary we cannot read, so the interesting question is not "what does gk do"
but "what does ClawMetry do to a hook it did not write".  That half is ours
and is fully testable.

The foreign writer is therefore modelled in two shapes:

  separate  — appends its own {matcher, hooks} entry.  This is what the
              co-resident ``numbat`` installer does on a real machine today,
              and it is why co-installation currently appears to work.
  merged    — appends its command into the hooks list of an entry that
              already exists.  This is the --force hazard, and it is the
              shape that used to be destroyed silently.

If a real ``gk`` binary is on PATH the harness uses it as a third, live
shape instead of guessing.  When it is not, the report says so rather than
implying GitLens itself was exercised.

Usage:  python3 scripts/hook_collision_matrix.py [--json]
Exit code is non-zero if any foreign hook was lost.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import hook_ownership  # noqa: E402

FOREIGN_CMD = "gk ai hook run pre-tool"
FOREIGN_HOOK = {"type": "command", "command": FOREIGN_CMD, "timeout": 30}
OUR_MARKERS = ("clawmetry hooks run", "clawmetry hook claude-code")


def gk_available() -> bool:
    return shutil.which("gk") is not None


# ── the foreign installer ──────────────────────────────────────────────────

def foreign_install(path: str, shape: str) -> None:
    """Model `gk ai hook install claude-code --force`."""
    if shape == "live":
        subprocess.run(["gk", "ai", "hook", "install", "claude-code", "--force"],
                       check=False, capture_output=True,
                       env={**os.environ,
                            "CLAUDE_CONFIG_DIR": os.path.dirname(path)})
        return
    settings = _read(path)
    pretool = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if shape == "merged" and pretool:
        # --force merges into the entry already holding the matcher it wants.
        pretool[0].setdefault("hooks", []).append(dict(FOREIGN_HOOK))
    else:
        pretool.append({"matcher": "Bash", "hooks": [dict(FOREIGN_HOOK)]})
    _write(path, settings)


def foreign_present(path: str) -> int:
    return json.dumps(_read(path)).count(FOREIGN_CMD)


def _read(path: str) -> dict:
    try:
        with open(path) as f:
            txt = f.read().strip()
        return json.loads(txt) if txt else {}
    except FileNotFoundError:
        return {}


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _summary(path: str) -> list:
    """One readable line per entry: who owns which hooks."""
    out = []
    for event, entries in sorted((_read(path).get("hooks") or {}).items()):
        for e in entries if isinstance(entries, list) else []:
            if not isinstance(e, dict):
                continue
            owners = []
            for h in e.get("hooks") or []:
                cmd = (h or {}).get("command") or ""
                owners.append("clawmetry" if any(m in cmd for m in OUR_MARKERS)
                              else ("gk" if "gk " in cmd else "other"))
            out.append(f"{event}[matcher={e.get('matcher', '-')}] {owners}")
    return out


# ── one scenario ───────────────────────────────────────────────────────────

def run_case(installer: str, shape: str, order: str) -> dict:
    """installer: 'manual' (clawmetry hooks install) | 'gate' (daemon gate)."""
    home = tempfile.mkdtemp()
    cfg = tempfile.mkdtemp()
    path = os.path.join(cfg, "settings.json")
    env_backup = {k: os.environ.get(k) for k in ("HOME", "CLAUDE_CONFIG_DIR")}
    os.environ["HOME"] = home
    os.environ["CLAUDE_CONFIG_DIR"] = cfg
    steps, lost = [], []
    try:
        import importlib
        from clawmetry import claude_code_gate, hooks_claude_code
        importlib.reload(claude_code_gate)
        importlib.reload(hooks_claude_code)
        policies = [{"action": "require_approval", "timeout": 300}]

        def ours_install():
            if installer == "manual":
                hooks_claude_code.install(settings_path=path)
            else:
                claude_code_gate._install(policies)

        def ours_uninstall():
            if installer == "manual":
                hooks_claude_code.uninstall(settings_path=path)
            else:
                claude_code_gate._uninstall()

        def step(label):
            steps.append({"step": label, "foreign_hooks": foreign_present(path),
                          "layout": _summary(path)})

        if order == "ours-first":
            ours_install()
            step("clawmetry install")
            foreign_install(path, shape)
            step("gk install --force")
        else:
            foreign_install(path, shape)
            step("gk install --force")
            ours_install()
            step("clawmetry install")

        baseline = foreign_present(path)
        if baseline == 0:
            lost.append("foreign hook never landed (shape not exercised)")

        ours_install()
        step("clawmetry refresh (runs every ~2s)")
        if foreign_present(path) < baseline:
            lost.append("refresh dropped a foreign hook")

        ours_uninstall()
        step("clawmetry uninstall")
        if foreign_present(path) < baseline:
            lost.append("uninstall dropped a foreign hook")

        ours_gone = not any(m in json.dumps(_read(path)) for m in OUR_MARKERS)
        if not ours_gone:
            lost.append("uninstall left our own hook behind")
    finally:
        for k, v in env_backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return {"installer": installer, "shape": shape, "order": order,
            "steps": steps, "lost": lost, "ok": not lost}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    shapes = ["separate", "merged"] + (["live"] if gk_available() else [])
    results = [run_case(i, s, o)
               for i in ("manual", "gate")
               for s in shapes
               for o in ("ours-first", "gk-first")]

    if args.json:
        print(json.dumps({"gk_on_path": gk_available(),
                          "results": results}, indent=2))
    else:
        print("Hook collision matrix — ClawMetry vs a foreign hook installer")
        print(f"real `gk` binary on PATH: {gk_available()}"
              + ("" if gk_available() else
                 "  (shapes below are modelled, GitLens itself was NOT run)"))
        print(f"installed hook timeout ceiling: "
              f"{hook_ownership.hook_timeout_ceiling_s()}s\n")
        for r in results:
            flag = "PASS" if r["ok"] else "FAIL"
            print(f"[{flag}] {r['installer']:6s} shape={r['shape']:8s} "
                  f"order={r['order']}")
            for s in r["steps"]:
                print(f"         {s['step']:32s} foreign_hooks="
                      f"{s['foreign_hooks']}  {'; '.join(s['layout'])}")
            for problem in r["lost"]:
                print(f"         !! {problem}")
        bad = [r for r in results if not r["ok"]]
        print(f"\n{len(results) - len(bad)}/{len(results)} scenarios preserved "
              f"every foreign hook.")
    return 1 if any(not r["ok"] for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
