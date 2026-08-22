"""clawmetry/onboarding_state.py — the ONE writer for the first-run gate's
choice file, ``~/.clawmetry/onboarding.json``.

Why this module exists (founder live-hit 2026-08-22): a machine onboarded
through ``clawmetry connect`` (paid ``cloud_pro`` account, local-only mode)
opened http://localhost:8900 and was shown the first-run gate again, asked
to pick managed-vs-self-host and sign in a second time. ``clawmetry status``
on the same machine printed the linked account and plan happily. Nothing was
out of sync between two installs — there is only one install. The CLI
onboarding paths simply never wrote the file the browser gate reads, so the
gate fell through every check it has and defaulted to "this install still
owes a choice".

The contract is now: **every path that completes onboarding records it here**,
so the dashboard gate only ever fires for an install that genuinely made no
choice (``pip install clawmetry && clawmetry`` and straight to the browser):

  * ``clawmetry connect`` / ``clawmetry login``  -> ``managed``
    (or ``selfhost_trial`` on the keep-local sign-in)
  * ``clawmetry onboard`` / ``clawmetry setup``  -> whichever branch ran,
    including the no-account free tier (``selfhost_free``)
  * ``clawmetry activate`` / ``clawmetry license activate`` -> recorded from
    the activated tier (see ``clawmetry/license.py::activate``)
  * the desktop shell's onboarding pane (``desktop/onboarding.py``)
  * the browser gate itself (``routes/onboarding.py``)

``selfhost_free`` is recorded but NOT postable through
``/api/onboarding/complete``: the wizard's "no account, no cloud" answer is a
real, explicit choice and must stop the re-prompt, but the browser gate has
no matching flow, so letting a POST claim it would let the gate be skipped
with nothing behind it. Hence two tuples: :data:`CHOICES` (what the gate
accepts over HTTP) and :data:`RECORDED_CHOICES` (what may legitimately sit in
the file).

Everything here is best-effort and never raises: a failed write means the
gate re-prompts (annoying), while an exception would break the onboarding
command itself (broken).
"""

from __future__ import annotations

import json
import logging
import os
import time

log = logging.getLogger(__name__)

# What the browser gate may record over HTTP.
CHOICES = ("managed", "selfhost_license", "selfhost_trial")
# Everything that may legitimately appear in the file. The CLI's free
# local tier has no browser flow behind it, so it is recordable but not
# postable (see module docstring).
RECORDED_CHOICES = CHOICES + ("selfhost_free",)


def state_path() -> str:
    """Absolute path of the gate's choice file.

    Resolved on every call, not once at import: the test suite (and the
    desktop shell's sandboxed runs) point ``HOME`` at a temp dir, and a
    constant frozen at import time would write to the real home anyway.
    """
    return os.path.expanduser("~/.clawmetry/onboarding.json")


def read_choice() -> str:
    """Return the recorded choice, or ``''`` when there is none.

    Unknown/corrupt content reads as no choice — the gate must fail toward
    asking, never toward silently skipping.
    """
    try:
        with open(state_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return ""
        choice = str(data.get("choice", "")).strip().lower()
        return choice if choice in RECORDED_CHOICES else ""
    except Exception:
        return ""


def record_choice(choice: str, *, source: str = "", path: str = "") -> bool:
    """Persist ``choice`` as this install's completed onboarding.

    ``source`` is free-form provenance for debugging (``"cli:connect"``,
    ``"desktop_shell"``, ...) and is ignored by every reader.

    ``path`` overrides the destination. Callers that already own a
    monkeypatchable path constant (the desktop shell) pass theirs, so
    adopting this writer does not silently make their tests — or a
    sandboxed run — write to the real home directory.

    Written atomically (tmp + ``os.replace``) so a crash mid-write cannot
    leave a truncated file that reads as "no choice" — or worse, as a
    corrupt file some future reader trips over. Returns True on success.
    """
    choice = str(choice or "").strip().lower()
    if choice not in RECORDED_CHOICES:
        log.warning("onboarding_state: refusing to record unknown choice %r", choice)
        return False
    path = str(path) if path else state_path()
    payload = {"choice": choice, "completed_at": int(time.time())}
    if source:
        payload["source"] = source
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, path)
        return True
    except Exception as exc:
        log.warning("onboarding_state: cannot persist choice: %s", exc)
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False
