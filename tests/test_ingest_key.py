"""Guards for the ingest key -- the door that lets an off-box agent be seen.

Until this existed, an agent was observable only if the ClawMetry daemon
ran on the same machine as the agent: ``/v1/*`` trusted loopback and
otherwise wanted the OpenClaw gateway token, and the write API trusted
one static secret shared by the whole install. CI jobs, containers,
serverless functions and teammates' laptops were simply invisible.

Four things are protected here, in descending order of how badly they
would hurt if they broke:

1. **An ingest key cannot read.** ``write:ingest`` grants no ``q/1``
   shape. If that ever stopped being true, a key handed to a CI runner
   would be able to pull back prompts.
2. **The gate is real.** ``dashboard.py::_check_auth`` steps aside for a
   request carrying the ingest header, so a bad key must be refused by
   ``ingest_auth`` or it is refused nowhere.
3. **Refusals say something.** Every rejection carries a sentence, not a
   bare code -- these are read inside an agent's terminal output with no
   documentation open.
4. **The old doors still work.** Loopback with no key at all is the
   zero-config local path and must not have moved.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ak(monkeypatch, tmp_path):
    """apikeys pointed at a throwaway store (never the operator's ~)."""
    store = tmp_path / "api_keys.json"
    monkeypatch.setenv("CLAWMETRY_API_KEYS_PATH", str(store))
    import clawmetry.apikeys as mod

    importlib.reload(mod)
    assert mod._store_path() == str(store)
    return mod


@pytest.fixture
def ia(ak):
    import clawmetry.ingest_auth as mod

    importlib.reload(mod)
    return mod


def _mint(ak, name="ci", scopes=("write:ingest",), origins=()):
    _, plaintext = ak.create(name, list(scopes), list(origins))
    return plaintext


class _H(dict):
    """Minimal stand-in for a Flask headers mapping (case-insensitive get)."""

    def get(self, key, default=None):
        for k, v in self.items():
            if k.lower() == str(key).lower():
                return v
        return default


# ── 1. an ingest key cannot read ────────────────────────────────────────

def test_ingest_scope_grants_no_query_shape(ak):
    record, _ = ak.create("ci", [ak.SCOPE_INGEST], [])
    assert ak.granted_shapes(record) == set(), (
        "write:ingest resolved to q/1 shapes. A key handed to a CI runner "
        "must not be able to read a single row back out."
    )
    assert ak.allows_ingest(record) is True


def test_read_scopes_do_not_grant_ingest(ak):
    for scope in ("read:metrics", "read:sessions", "read:traces", "read:content"):
        record, _ = ak.create("r-" + scope, [scope], ["http://localhost:3000"])
        assert ak.allows_ingest(record) is False, (
            f"{scope} allowed ingest. Read scopes must never imply write."
        )


def test_ingest_scope_is_not_in_the_read_contract():
    """The q/1 contract declares what can be READ. A write scope in that
    table would be a scope with no shape behind it -- a lie in the one
    place the API guide is generated from."""
    from clawmetry import apikeys, query_contract

    assert apikeys.SCOPE_INGEST not in query_contract.SCOPES
    assert apikeys.SCOPE_INGEST in apikeys.SCOPES


def test_ingest_key_refuses_to_be_a_read_key_too(ak):
    with pytest.raises(ak.ApiKeyError) as exc:
        ak.create("mixed", ["write:ingest", "read:content"], [])
    assert "one job" in str(exc.value)


def test_ingest_key_refuses_a_browser_origin(ak):
    """Ingest is server-to-server and never gets a CORS header, so an
    origin on one would be dead configuration that reads like a grant."""
    with pytest.raises(ak.ApiKeyError) as exc:
        ak.create("web", ["write:ingest"], ["https://example.com"])
    assert "--origin none" in str(exc.value)


# ── 2. the gate ─────────────────────────────────────────────────────────

def test_valid_key_authenticates(ak, ia):
    key = _mint(ak)
    record, err = ia.authenticate(_H({ia.HEADER_KEY: key}))
    assert err is None
    assert record["name"] == "ci"


def test_unknown_key_is_401(ak, ia):
    record, err = ia.authenticate(_H({ia.HEADER_KEY: "cmk_deadbeef_nope"}))
    assert record is None
    body, status = err
    assert status == 401
    assert body["error"] == "unauthorized"
    assert "revoked" in body["message"]


def test_revoked_key_is_401(ak, ia):
    rec, key = ak.create("ci", ["write:ingest"], [])
    ak.revoke(rec["id"])
    record, err = ia.authenticate(_H({ia.HEADER_KEY: key}))
    assert record is None
    assert err[1] == 401


def test_read_key_presented_to_ingest_is_403_not_401(ak, ia):
    """The distinction matters: 401 means "your key is wrong", 403 means
    "your key is fine and may not do this". Collapsing them sends people
    to regenerate a key that was never the problem."""
    key = _mint(ak, "ui", ("read:metrics",), ("http://localhost:3000",))
    record, err = ia.authenticate(_H({ia.HEADER_KEY: key}))
    assert record is None
    body, status = err
    assert status == 403
    assert "cannot push" in body["message"]


def test_missing_key_is_401_with_the_command_to_fix_it(ia):
    record, err = ia.authenticate(_H({}))
    assert record is None
    body, status = err
    assert status == 401
    assert "clawmetry key create" in body["message"]


# ── 3. routing headers ──────────────────────────────────────────────────

def test_runtime_header_is_optional(ia):
    assert ia.resolve_runtime(_H({})) == (None, None)


def test_runtime_header_accepts_a_known_and_an_unknown_runtime(ia):
    """An in-house engine is a supported case, so an unrecognised name is
    accepted -- it just has to be a name."""
    for name in ("claude_code", "my-engine", "n8n"):
        value, err = ia.resolve_runtime(_H({ia.HEADER_RUNTIME: name}))
        assert err is None and value == name


@pytest.mark.parametrize("bad", ["../etc/passwd", "a" * 41, "Robert'); DROP", ""])
def test_bad_runtime_header_is_400_or_ignored(ia, bad):
    value, err = ia.resolve_runtime(_H({ia.HEADER_RUNTIME: bad}))
    if bad == "":
        assert (value, err) == (None, None)
    else:
        assert value is None and err[1] == 400


def test_env_header_validates(ia):
    assert ia.resolve_env(_H({ia.HEADER_ENV: "production"}))[0] == "production"
    assert ia.resolve_env(_H({ia.HEADER_ENV: "team-a.staging"}))[0] == "team-a.staging"
    assert ia.resolve_env(_H({ia.HEADER_ENV: "a b"}))[1][1] == 400


def test_routing_is_stamped_onto_the_resource_attributes():
    """The headers are written into the attributes the mappers already
    read, so a header is exactly as powerful as the equivalent exporter
    setting and no mapper learns a second way to answer the question."""
    import dashboard as _d

    attrs = {"service.name": "unknown_service"}
    _d._apply_ingest_routing(attrs, "my-engine", "production")
    assert attrs["service.name"] == "my-engine"
    assert attrs["deployment.environment"] == "production"

    # No headers: the resource is left exactly as the exporter sent it.
    untouched = {"service.name": "openclaw-gateway"}
    _d._apply_ingest_routing(untouched, None, None)
    assert untouched == {"service.name": "openclaw-gateway"}


# ── 4. size cap ─────────────────────────────────────────────────────────

def test_oversize_body_is_413_before_it_is_parsed(ia):
    err = ia.check_size(b"x" * (ia.MAX_BODY_BYTES + 1))
    body, status = err
    assert status == 413
    assert "Split the batch" in body["message"]


def test_body_at_the_limit_is_accepted(ia):
    assert ia.check_size(b"x" * ia.MAX_BODY_BYTES) is None


# ── the whole prologue ──────────────────────────────────────────────────

def test_prologue_lets_an_unkeyed_request_through(ia):
    """Loopback with no key at all is the zero-config local exporter path
    and must keep working: _check_auth has already decided that request
    is allowed, and this function is not a second opinion."""
    ctx, err = ia.prologue(_H({}), b"{}")
    assert err is None
    assert ctx == {"key": None, "runtime": None, "env": None}


def test_prologue_rejects_a_bad_key_even_though_check_auth_stepped_aside(ia):
    ctx, err = ia.prologue(_H({ia.HEADER_KEY: "cmk_00000000_bad"}), b"{}")
    assert ctx is None and err[1] == 401


def test_prologue_returns_the_routing_for_a_good_key(ak, ia):
    key = _mint(ak)
    ctx, err = ia.prologue(
        _H({ia.HEADER_KEY: key,
            ia.HEADER_RUNTIME: "my-engine",
            ia.HEADER_ENV: "ci"}),
        b"{}",
    )
    assert err is None
    assert ctx["runtime"] == "my-engine"
    assert ctx["env"] == "ci"
    assert ctx["key"]["name"] == "ci"


def test_using_a_key_records_it(ak, ia):
    """`clawmetry key list` answers "is anything still using this?" before
    someone revokes it, which only works if the ingest path writes back."""
    rec, key = ak.create("ci", ["write:ingest"], [])
    ia.authenticate(_H({ia.HEADER_KEY: key}))
    after = [k for k in ak.list_keys() if k["id"] == rec["id"]][0]
    assert after["use_count"] == 1
    assert after["last_used_at"]


def test_ingest_key_is_refused_by_the_read_api(ak, monkeypatch):
    """A write-only key is a valid key, so verify() accepts it. The read
    API must still turn it away rather than hand it an index it can never
    follow up on -- found by pushing one at /api/q/1 on a live server and
    getting a 200 back."""
    import importlib

    from flask import Flask

    import routes.local_query as lq
    import routes.public_api as pub

    importlib.reload(pub)
    monkeypatch.setattr(lq, "_dispatch", lambda shape, args: {"rows": []})
    monkeypatch.setattr(lq, "_apply_24h_cap", lambda args: False)

    app = Flask(__name__)
    app.register_blueprint(pub.bp_public_api)
    client = app.test_client()

    key = _mint(ak)
    for path in ("/api/q/1", "/api/q/1/llms.txt", "/api/q/1/sessions"):
        res = client.get(path, headers={"Authorization": "Bearer " + key})
        assert res.status_code == 403, (
            f"{path} answered {res.status_code} to an ingest key. A key that "
            "cannot read any shape is not a key for the read API."
        )
