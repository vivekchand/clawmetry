"""Tests for ``GET /api/entitlement/runtime-detection``.

The endpoint pairs :func:`clawmetry.runtime_probe.probe_runtimes` with the
resolved entitlement so the dashboard renders "runtimes on this machine +
which unlock at which tier" off a single round-trip. Tests pin:

* The response envelope has the expected keys (a paywall CTA card reading
  ``.probes`` / ``.counts`` / ``.actionable_tier`` would silently blank on
  drift).
* Per-row decoration is correct: free runtimes are always ``allowed``, paid
  runtimes are ``allowed`` iff the resolved tier grants them, and each row
  carries the paid ``required_tier`` / ``required_tier_label`` needed to
  unlock it.
* ``counts`` and ``detected_locked`` correctly reflect planted-on-disk
  fixture probes.
* ``actionable_tier`` = the cheapest tier that unlocks EVERY detected +
  locked runtime -- so the CTA card renders "Upgrade to Cloud Starter" once,
  not per-row.
* The endpoint never 5xxs: probe / resolver / import failures fall through
  to the neutral empty envelope so the frontend card stays rendered.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client with bp_entitlement and a clean HOME/USERPROFILE.

    Both HOME and USERPROFILE are set because ``os.path.expanduser`` on
    Windows honours only USERPROFILE (see #3850).
    """
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client(), tmp_path


# ── shape invariants ─────────────────────────────────────────────────────────

_EXPECTED_ENVELOPE_KEYS = frozenset(
    {
        "current_tier",
        "current_tier_label",
        "grace",
        "enforced",
        "probes",
        "counts",
        "detected_locked",
        "actionable_tier",
        "actionable_tier_label",
    }
)

_EXPECTED_COUNT_KEYS = frozenset(
    {
        "total",
        "detected",
        "detected_free",
        "detected_locked",
        "unlocked",
        "locked",
    }
)

_EXPECTED_ROW_KEYS = frozenset(
    {
        "id",
        "label",
        "free",
        "found",
        "allowed",
        "required_tier",
        "required_tier_label",
    }
)


def test_envelope_shape_stable(client):
    c, _ = client
    resp = c.get("/api/entitlement/runtime-detection")
    assert resp.status_code == 200
    body = resp.get_json()
    assert _EXPECTED_ENVELOPE_KEYS.issubset(body.keys())
    assert _EXPECTED_COUNT_KEYS.issubset(body["counts"].keys())


def test_every_probe_row_has_stable_keys(client):
    c, _ = client
    body = c.get("/api/entitlement/runtime-detection").get_json()
    assert body["probes"], "probes should never be empty on a healthy resolve"
    for row in body["probes"]:
        assert _EXPECTED_ROW_KEYS.issubset(row.keys()), row


def test_probes_cover_full_catalogue(client):
    """Every runtime in the probe catalogue appears exactly once."""
    from clawmetry.runtime_probe import RUNTIME_PROBES

    c, _ = client
    body = c.get("/api/entitlement/runtime-detection").get_json()
    ids = [r["id"] for r in body["probes"]]
    assert len(ids) == len(set(ids)), "duplicate probe ids in response"
    assert set(ids) == {p.id for p in RUNTIME_PROBES}
    assert body["counts"]["total"] == len(RUNTIME_PROBES)


# ── tier decoration ──────────────────────────────────────────────────────────


def test_oss_install_free_runtimes_allowed_paid_locked(client):
    c, _ = client
    body = c.get("/api/entitlement/runtime-detection").get_json()
    assert body["current_tier"] == "oss"

    rows = {r["id"]: r for r in body["probes"]}
    # openclaw + nemoclaw are free-forever -> always allowed and required_tier=oss.
    for rid in ("openclaw", "nemoclaw"):
        assert rows[rid]["free"] is True
        assert rows[rid]["allowed"] is True
        assert rows[rid]["required_tier"] == "oss"
        assert rows[rid]["required_tier_label"] == "OSS"

    # Paid runtimes -> not allowed on OSS, required_tier is a paid rung.
    for rid in ("claude_code", "cursor", "codex", "aider"):
        assert rows[rid]["free"] is False
        assert rows[rid]["allowed"] is False
        assert rows[rid]["required_tier"] not in (None, "", "oss")


def test_grace_flag_reflects_enforce_env(monkeypatch, tmp_path):
    """Top-level ``grace`` / ``enforced`` mirror the resolver, so the UI can
    show "would be locked" copy without a second round-trip."""
    from routes.entitlement import bp_entitlement

    for enforce, expected_grace, expected_enforced in (
        ("0", True, False),
        ("1", False, True),
    ):
        monkeypatch.setenv("CLAWMETRY_ENFORCE", enforce)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))

        import clawmetry.entitlements as e

        importlib.reload(e)
        e.invalidate()

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        client = app.test_client()

        body = client.get("/api/entitlement/runtime-detection").get_json()
        assert body["grace"] is expected_grace
        assert body["enforced"] is expected_enforced

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)


# ── on-disk fixtures drive detection ─────────────────────────────────────────


def test_planted_paid_runtime_detected_and_locked(client):
    c, home = client
    (home / ".claude" / "projects").mkdir(parents=True)

    body = c.get("/api/entitlement/runtime-detection").get_json()
    rows = {r["id"]: r for r in body["probes"]}
    assert rows["claude_code"]["found"] is True
    assert rows["claude_code"]["allowed"] is False
    assert "claude_code" in body["detected_locked"]
    assert body["counts"]["detected"] >= 1
    assert body["counts"]["detected_locked"] >= 1


def test_planted_free_runtime_detected_and_allowed(client):
    """OpenClaw's default paths -> found=True, allowed=True (free-forever).

    Its presence must NOT bump ``detected_locked``.
    """
    c, home = client
    openclaw_dir = home / ".openclaw"
    openclaw_dir.mkdir(parents=True)
    (openclaw_dir / "openclaw.json").write_text("{}")

    body = c.get("/api/entitlement/runtime-detection").get_json()
    rows = {r["id"]: r for r in body["probes"]}
    assert rows["openclaw"]["found"] is True
    assert rows["openclaw"]["allowed"] is True
    assert "openclaw" not in body["detected_locked"]


def test_multiple_paid_runtimes_actionable_tier_covers_all(client):
    """``actionable_tier`` is the ONE tier that unlocks every detected +
    locked runtime -- the CTA card renders "Upgrade to X" once, not N times.
    """
    c, home = client
    (home / ".claude" / "projects").mkdir(parents=True)  # claude_code
    (home / ".codex" / "sessions").mkdir(parents=True)  # codex

    body = c.get("/api/entitlement/runtime-detection").get_json()

    assert set(body["detected_locked"]) >= {"claude_code", "codex"}

    # min_tier_for_runtimes over any subset of PAID_RUNTIMES today collapses
    # to cloud_starter (single-rung ladder for paid runtimes).
    from clawmetry import entitlements as e

    expected = e.min_tier_for_runtimes(body["detected_locked"])
    assert body["actionable_tier"] == expected
    assert body["actionable_tier_label"] == e.tier_label(expected)


def test_no_paid_runtimes_actionable_tier_none(client):
    """A machine with only free runtimes present -> no CTA to render."""
    c, home = client
    (home / ".openclaw").mkdir(parents=True)
    (home / ".openclaw" / "openclaw.json").write_text("{}")

    body = c.get("/api/entitlement/runtime-detection").get_json()
    assert body["detected_locked"] == []
    assert body["actionable_tier"] is None
    assert body["actionable_tier_label"] is None


# ── counts arithmetic ────────────────────────────────────────────────────────


def test_counts_are_consistent_with_rows(client):
    """counts.total == len(probes); counts.unlocked + counts.locked == total;
    counts.detected == rows with found=True; counts.detected_locked == rows
    with found=True AND allowed=False."""
    c, home = client
    (home / ".claude" / "projects").mkdir(parents=True)
    (home / ".openclaw").mkdir(parents=True)
    (home / ".openclaw" / "openclaw.json").write_text("{}")

    body = c.get("/api/entitlement/runtime-detection").get_json()
    rows = body["probes"]
    counts = body["counts"]

    assert counts["total"] == len(rows)
    assert counts["unlocked"] + counts["locked"] == counts["total"]
    assert counts["detected"] == sum(1 for r in rows if r["found"])
    assert counts["detected_free"] == sum(
        1 for r in rows if r["found"] and r["free"]
    )
    assert counts["detected_locked"] == sum(
        1 for r in rows if r["found"] and not r["allowed"]
    )
    assert counts["detected_locked"] == len(body["detected_locked"])


# ── never 5xx ────────────────────────────────────────────────────────────────


def test_endpoint_survives_probe_failure(monkeypatch, tmp_path):
    """A broken probe module -> empty envelope, not 500."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    from clawmetry import runtime_probe as _probe

    monkeypatch.setattr(
        _probe,
        "probe_runtimes",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    resp = app.test_client().get("/api/entitlement/runtime-detection")
    assert resp.status_code == 200
    body = resp.get_json()
    # Envelope keys still present, probes empty, no NoneType-in-len errors.
    assert _EXPECTED_ENVELOPE_KEYS.issubset(body.keys())
    assert body["probes"] == []
    assert body["counts"]["total"] == 0
    assert body["detected_locked"] == []
    assert body["actionable_tier"] is None


def test_endpoint_survives_resolver_failure(monkeypatch, tmp_path):
    """Resolver blowing up -> falls back to OSS-free view, still 200."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    import clawmetry.entitlements as e

    importlib.reload(e)
    monkeypatch.setattr(
        e, "get_entitlement", lambda force=False: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    resp = app.test_client().get("/api/entitlement/runtime-detection")
    assert resp.status_code == 200
    body = resp.get_json()
    # OSS-free fallback -> current_tier="oss", free runtimes still allowed.
    assert body["current_tier"] == "oss"
    assert body["probes"], "OSS-free fallback should still list probes"
    free_row = next(r for r in body["probes"] if r["id"] == "openclaw")
    assert free_row["allowed"] is True
