"""The organisation key: one secret, shared by the people in one organisation.

Why this exists
---------------
Every encrypted payload ClawMetry produces today is sealed with a key that
belongs to ONE machine and lives in ONE person's browser. That is correct for
a single operator and it is exactly why a colleague opening a teammate's node
gets the ``team_view_locked`` terminal state the cloud already ships: there is
no key in the system that means "readable by the people I work with".

The organisation key is that key. It is created on a machine, handed between
people out of band, and **never sent to the hosted service** -- which keeps the
property the product sells: content leaves the machine sealed, and the service
stores ciphertext it cannot read.

What the service does learn is the key's FINGERPRINT (see :func:`fingerprint`).
A fingerprint identifies; it never decrypts. It exists so a member holding the
wrong key can be told exactly that, instead of being shown an empty screen and
left to guess whether their team has no sessions or they have the wrong secret.

What this module deliberately does not do
-----------------------------------------
It does not decide who is in an organisation -- membership lives in the cloud's
team model and is the only thing that grants access. Holding a key is not
membership: the service serves ciphertext to members, and the key opens it.
Both are required, and they fail independently, which is the point.

It also does not rotate keys or wrap per-member copies. That is a key hierarchy
and the reasons for not shipping one now are recorded in ADR-001 of the Team
Sessions blueprint, along with what it costs us.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Optional

# The config field. Kept distinct from ``encryption_key`` (the node key) so a
# machine can hold both: the node key still seals anything private to this
# machine, the organisation key seals what colleagues are meant to read.
CONFIG_FIELD = "org_encryption_key"

# How many hex characters of the digest we publish. 16 is plenty to tell two
# keys apart for a human, and short enough to read out loud over a call.
FINGERPRINT_CHARS = 16


def generate() -> str:
    """Return a fresh 256-bit organisation key, base64url, no padding.

    Mirrors the node key's shape so every path that already accepts a key --
    the CLI prompt, the browser's paste box -- accepts this one unchanged.
    """
    import base64

    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def normalize(key: str) -> str:
    """Coerce whatever a human pasted into the key the cipher wants.

    Delegates to the node key's normaliser so a passphrase is derived the same
    way in both cases. Two normalisers would eventually disagree, and the
    symptom of disagreement is data that will not open.
    """
    from clawmetry.sync import _normalize_encryption_key

    return _normalize_encryption_key((key or "").strip())


def fingerprint(key: str) -> str:
    """A short, public identifier for a key. Never a way back to the key.

    SHA-256 over the NORMALISED key, so a passphrase and the key it derives
    produce the same fingerprint -- otherwise a member who typed the passphrase
    and one who pasted the derived key would be told they disagree when they
    hold the same secret.
    """
    k = (key or "").strip()
    if not k:
        return ""
    try:
        k = normalize(k)
    except Exception:
        # A key we cannot normalise still deserves a stable fingerprint --
        # better to report a mismatch than to report nothing at all.
        pass
    return hashlib.sha256(k.encode("utf-8")).hexdigest()[:FINGERPRINT_CHARS]


def get(config: Optional[dict] = None) -> str:
    """The organisation key for this machine, or "" when it has none.

    Environment first so a container can be handed a key without a writable
    config file; the config file otherwise.
    """
    env = (os.environ.get("CLAWMETRY_ORG_KEY") or "").strip()
    if env:
        return env
    if config is None:
        try:
            from clawmetry.sync import load_config

            config = load_config() or {}
        except Exception:
            return ""
    return str((config or {}).get(CONFIG_FIELD) or "").strip()


def content_key(config: Optional[dict] = None) -> str:
    """The key that should seal this machine's shareable content.

    The organisation key when the machine has one, the node key otherwise. ONE
    copy is sealed, never two: a second encryption of the same title is a
    second thing that can disagree with the first.

    Callers must treat a missing key as "do not upload", never as "upload in
    the clear" -- a fallback to plaintext is the failure this whole area exists
    to prevent.
    """
    org = get(config)
    if org:
        return org
    if config is None:
        try:
            from clawmetry.sync import load_config

            config = load_config() or {}
        except Exception:
            return ""
    return str((config or {}).get("encryption_key") or "").strip()


def is_org_sealed(config: Optional[dict] = None) -> bool:
    """True when this machine's content is sealed for an organisation.

    Read by the heartbeat so the cloud can tell a browser which key it needs,
    and by the CLI so ``clawmetry status`` can say plainly which of the two
    secrets a person must hold to read this machine.
    """
    return bool(get(config))
