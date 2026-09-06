"""MD5/SHA-1 digests that are *not* being used as a security primitive.

ClawMetry hashes a lot of things that have nothing to do with secrecy: a
dedup id for an ingested event, a change-detection hash over a cron file, a
fingerprint over a tool call's arguments, a trace/span id derived from a
session id. Every one of those wants a cheap, stable, short digest. None of
them is defending against an adversary who gets to choose the input, so the
collision weakness that retired MD5 and SHA-1 for signatures does not apply.

Two things go wrong when those call sites reach for ``hashlib`` directly:

1. **A restricted crypto provider refuses them.** When the interpreter's
   OpenSSL is built or configured to allow only approved algorithms (a
   FIPS-mode host, which is the normal build on several enterprise Linux
   distributions), ``hashlib.md5(b"...")`` does not return a weak digest --
   it raises ``ValueError``. The daemon's cron ingest, memory-file ingest and
   event dedup would all fail on such a host, and none of them is doing
   cryptography. ``usedforsecurity=False`` is the documented way to say so,
   and it is what keeps a non-security digest available where the provider
   restricts the algorithm.

2. **The keyword cannot simply be passed everywhere.** ``usedforsecurity=``
   reached hashlib's constructors in CPython 3.9, and ``setup.py`` still
   declares ``python_requires=">=3.8"``. On 3.8 passing it is a
   ``TypeError``, not a no-op -- so a bare kwarg trades one crash for
   another. The version check lives here, once, instead of at fifteen call
   sites.

Use these for identifiers, dedup keys, fingerprints and change detection.
Do **not** use them for anything an attacker is trying to forge: passwords,
signatures, tokens, or integrity checks over untrusted content. Those want
SHA-256 (or the ``cryptography`` package, which the cloud-sync path already
depends on), not a documented-as-non-security MD5.

What the two scanners say about this page
----------------------------------------

Collecting the calls into this module is what makes the risk acceptance
reviewable: there are exactly four ``hashlib`` constructor calls in the
package now, all of them on this page, instead of fifteen scattered ones.
That same collection is why both scanners point here.

* **bandit B324** flags a weak digest built without ``usedforsecurity``.
  Only the two 3.8 fallbacks qualify, and ``# nosec B324`` clears them.
  That marker works: bandit reports zero B324 for this file.
* **CodeQL ``py/weak-sensitive-data-hashing``** flags all four, because it
  tracks the *caller's* value into the sink: a ``session_id``, ``job_id`` or
  ``trace_id`` reaching a weak digest reads as sensitive data being hashed.
  It does not treat ``usedforsecurity=False`` as an answer, so the
  declaration does not clear it.

  **There is no in-code way to clear it either, and that was measured, not
  assumed.** An ``# codeql[py/weak-sensitive-data-hashing]`` comment was put
  on all four calls and pushed; CodeQL re-ran and reported the same four
  high-severity alerts, merely renumbered (977-980 became 981-984, because
  moving the lines mints new alert identities). This repository runs code
  scanning through **default setup** -- there is no
  ``.github/workflows/codeql.yml`` and no ``.github/codeql/`` config -- so
  there is no query filter to add, and inline suppression comments are a
  CodeQL *CLI* feature that default setup does not honour. The annotations
  were removed again rather than left as decoration that reads like a fix.

  So those four alerts clear **only** by being dismissed in the
  repository's Security tab, or by moving these digests off MD5/SHA-1 --
  which rewrites bytes that are already persisted (event dedup keys, trace
  ids, cron change hashes) and so needs its own migration. That choice
  belongs to a maintainer, not to this docstring.

On the substance: the values concerned are identifiers ClawMetry itself
minted and already stores in plaintext beside the digest -- the digest is a
shorter name for a row, not a way of protecting it -- so there is nothing
here for a collision or a preimage to win. That is a judgement about
*these* four lines; it is not a licence to add a fifth, and
``tests/test_nonsecret_hash.py`` holds the ratchet that keeps new call
sites out.
"""

import hashlib
import sys

#: CPython gained ``usedforsecurity=`` on the hashlib constructors in 3.9.
#: Below that the keyword raises TypeError, so it has to be omitted rather
#: than passed and ignored.
_ACCEPTS_USEDFORSECURITY = sys.version_info >= (3, 9)


def md5(data=b""):
    """An MD5 digest object declared as not-for-security.

    Signature matches ``hashlib.md5``: pass the bytes up front, or call
    ``.update()`` on the returned object.
    """
    if _ACCEPTS_USEDFORSECURITY:
        return hashlib.md5(data, usedforsecurity=False)
    # py3.8 has no usedforsecurity kwarg; see module docstring.
    return hashlib.md5(data)  # nosec B324


def sha1(data=b""):
    """A SHA-1 digest object declared as not-for-security.

    Signature matches ``hashlib.sha1``.
    """
    if _ACCEPTS_USEDFORSECURITY:
        return hashlib.sha1(data, usedforsecurity=False)
    # py3.8 has no usedforsecurity kwarg; see module docstring.
    return hashlib.sha1(data)  # nosec B324
