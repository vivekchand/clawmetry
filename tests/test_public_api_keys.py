"""Guards for the keyed read API custom UIs are built on.

Three things are being protected here, in descending order of how badly
they would hurt if they broke:

1. **The CORS gate.** ``/api/q/`` is the only surface in ClawMetry that
   answers a cross-origin browser read. If ``Access-Control-Allow-Origin``
   ever went out for an origin the key did not name, any page in any tab
   could read the machine's telemetry. Several tests here exist purely to
   fail loudly if that becomes possible.
2. **The scope gate.** A key must reach exactly the queries its scopes
   cover. ``read:metrics`` in particular must never be able to return a
   prompt or a reply, which is pinned to the contract's own trust class
   rather than to a hand-kept list.
3. **Key handling.** Secrets hashed and never stored in the clear, the
   file 0600, revocation effective on the next request.

The management endpoints (mint / list / revoke) are checked too, because
they live on the ordinary dashboard blueprint on purpose and must stay
there: a read key must never be able to issue itself a better one.
"""
from __future__ import annotations

import importlib
import json
import os
import stat

import pytest


# ── fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def ak(monkeypatch, tmp_path):
    """The apikeys module pointed at a throwaway store.

    tests/ has burned this repo before by writing into the operator's real
    ~/.clawmetry, so the path override is set before the module is used
    and asserted below.
    """
    store = tmp_path / "api_keys.json"
    monkeypatch.setenv("CLAWMETRY_API_KEYS_PATH", str(store))
    import clawmetry.apikeys as mod

    importlib.reload(mod)
    assert mod._store_path() == str(store)
    return mod


@pytest.fixture
def client(ak, monkeypatch):
    """A Flask test client with just the two blueprints under test.

    Deliberately NOT the whole dashboard app: booting it drags in DuckDB
    and the runtime probes, and the thing being tested is the auth and
    CORS behaviour of these routes, which is entirely self-contained.
    ``_dispatch`` is stubbed so no test needs a populated store.
    """
    from flask import Flask

    import routes.local_query as lq
    import routes.public_api as pub

    importlib.reload(pub)

    calls = []

    def _fake_dispatch(shape, args):
        calls.append((shape, dict(args)))
        return {"rows": [{"shape_echo": shape}], "count": 1,
                "_via": "test", "_shape": shape}

    monkeypatch.setattr(lq, "_dispatch", _fake_dispatch)
    monkeypatch.setattr(lq, "_apply_24h_cap", lambda args: False)

    app = Flask(__name__)
    app.register_blueprint(pub.bp_public_api)
    c = app.test_client()
    c.dispatch_calls = calls
    c.pub = pub
    return c


def _mint(ak, name="t", scopes=("read:metrics",), origins=("http://localhost:3000",)):
    _, plaintext = ak.create(name, list(scopes), list(origins))
    return plaintext


def _auth(key):
    return {"Authorization": "Bearer " + key}


# ── the contract declares a scope for every method ──────────────────────

def test_every_contract_method_declares_a_known_scope():
    from clawmetry import query_contract as qc

    for name, spec in qc.QUERY_CONTRACT.items():
        assert spec.get("scope") in qc.SCOPES, (
            f"{name} declares scope {spec.get('scope')!r}, which is not one of "
            f"{qc.SCOPES}. A method with no scope is unreachable by any key."
        )


def test_scopes_partition_every_live_shape():
    """A live shape covered by no scope would be dead to the API forever,
    and one covered by two would make the grant ambiguous."""
    from clawmetry import query_contract as qc

    live = set(qc.live_shapes())
    covered = qc.shapes_for_scopes(qc.SCOPES)
    assert covered == live, f"uncovered: {live - covered}, phantom: {covered - live}"
    seen = set()
    for scope in qc.SCOPES:
        got = set(qc.live_methods_by_scope(scope))
        assert not (got & seen), f"{scope} overlaps an earlier scope: {got & seen}"
        seen |= got


def test_read_metrics_is_exactly_the_plaintext_trust_class():
    """The load-bearing invariant behind the whole scope model.

    ``read:metrics`` is what a browser-resident key should hold, and the
    promise attached to it is "this cannot return a prompt or a reply".
    That promise is only true while metrics-scope and plaintext-trust are
    the same set, so it is pinned rather than trusted.
    """
    from clawmetry import query_contract as qc

    metrics = set(qc.methods_by_scope(qc.SCOPE_METRICS))
    plaintext = set(qc.methods_by_trust(qc.TRUST_PLAINTEXT))
    assert metrics == plaintext, (
        "read:metrics and the plaintext trust class have diverged. "
        f"metrics-only={metrics - plaintext} plaintext-only={plaintext - metrics}. "
        "Either move the method to another scope or reclassify its trust."
    )


# ── key handling ────────────────────────────────────────────────────────

def test_secret_is_never_stored_in_the_clear(ak, tmp_path):
    _, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    raw = (tmp_path / "api_keys.json").read_text()
    secret = plaintext.split("_", 2)[2]
    assert secret not in raw
    assert plaintext not in raw
    stored = json.loads(raw)["keys"][0]
    assert stored["hash"] and stored["hash"] != secret


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits only")
def test_store_file_is_owner_only(ak, tmp_path):
    ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    mode = stat.S_IMODE((tmp_path / "api_keys.json").stat().st_mode)
    assert mode & 0o077 == 0, f"key file is group/world accessible: {oct(mode)}"


def test_verify_round_trips_and_rejects_a_tampered_secret(ak):
    _, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    assert ak.verify(plaintext)["name"] == "t"
    kid, secret = plaintext.split("_", 2)[1:]
    assert ak.verify("cmk_%s_%sx" % (kid, secret)) is None
    assert ak.verify("cmk_00000000_" + secret) is None
    assert ak.verify("") is None
    assert ak.verify("not-a-key") is None


def test_revoke_is_immediate_and_keeps_the_record(ak):
    rec, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    assert ak.revoke(rec["id"]) is True
    assert ak.verify(plaintext) is None
    assert ak.revoke(rec["id"]) is False, "revoking twice must not report success"
    assert [r["id"] for r in ak.list_keys(include_revoked=True)] == [rec["id"]]
    assert ak.list_keys() == []


def test_revoke_accepts_a_pasted_whole_key(ak):
    """People paste the key, not the id. Accepting it costs nothing and
    the alternative is a confusing 'no such key'."""
    _, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    assert ak.revoke(plaintext) is True
    assert ak.verify(plaintext) is None


def test_wildcard_origin_is_refused(ak):
    with pytest.raises(ak.ApiKeyError) as exc:
        ak.create("t", ["read:metrics"], ["*"])
    assert "wildcard" in str(exc.value).lower()


@pytest.mark.parametrize("bad", [
    "localhost:3000",                 # no scheme
    "ftp://example.com",              # not http(s)
    "https://example.com/dashboard",  # has a path
    "https://example.com?a=1",        # has a query
])
def test_malformed_origins_are_refused(ak, bad):
    with pytest.raises(ak.ApiKeyError):
        ak.create("t", ["read:metrics"], [bad])


def test_unknown_scope_is_refused_by_name(ak):
    with pytest.raises(ak.ApiKeyError) as exc:
        ak.create("t", ["read:everything"], ["http://localhost:3000"])
    assert "read:everything" in str(exc.value)


def test_a_key_needs_a_scope(ak):
    with pytest.raises(ak.ApiKeyError):
        ak.create("t", [], ["http://localhost:3000"])


def test_a_key_needs_a_name(ak):
    with pytest.raises(ak.ApiKeyError):
        ak.create("   ", ["read:metrics"], ["http://localhost:3000"])


def test_unreadable_store_reads_as_no_keys(ak, tmp_path, monkeypatch):
    """A corrupt file must degrade to 401, never to a 500 that takes the
    dashboard's own pages with it."""
    (tmp_path / "api_keys.json").write_text("{ this is not json")
    assert ak.list_keys() == []
    assert ak.verify("cmk_aaaaaaaa_whatever") is None


def test_key_cap_is_enforced(ak, monkeypatch):
    monkeypatch.setattr(ak, "MAX_KEYS", 2)
    ak.create("a", ["read:metrics"], ["http://localhost:3000"])
    rec, _ = ak.create("b", ["read:metrics"], ["http://localhost:3000"])
    with pytest.raises(ak.ApiKeyError):
        ak.create("c", ["read:metrics"], ["http://localhost:3000"])
    ak.revoke(rec["id"])
    ak.create("c", ["read:metrics"], ["http://localhost:3000"])  # a slot freed up


def test_redact_shows_the_id_and_never_the_secret(ak):
    _, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    red = ak.redact(plaintext)
    assert plaintext.split("_", 2)[1] in red
    assert plaintext.split("_", 2)[2] not in red


# ── HTTP: authentication ────────────────────────────────────────────────

def test_no_key_is_401_even_from_loopback(client):
    """The whole point of this surface: unlike the rest of the dashboard,
    being local earns nothing here."""
    r = client.get("/api/q/1/health")
    assert r.status_code == 401
    assert "clawmetry key create" in r.get_json()["error"]


def test_bad_key_is_401(client):
    r = client.get("/api/q/1/health", headers=_auth("cmk_deadbeef_nope"))
    assert r.status_code == 401


def test_revoked_key_stops_working_without_a_restart(client, ak):
    rec, plaintext = ak.create("t", ["read:metrics"], ["http://localhost:3000"])
    assert client.get("/api/q/1/health", headers=_auth(plaintext)).status_code == 200
    ak.revoke(rec["id"])
    assert client.get("/api/q/1/health", headers=_auth(plaintext)).status_code == 401


def test_x_clawmetry_key_header_also_works(client, ak):
    plaintext = _mint(ak)
    r = client.get("/api/q/1/health", headers={"X-ClawMetry-Key": plaintext})
    assert r.status_code == 200


# ── HTTP: scopes ────────────────────────────────────────────────────────

def test_granted_shape_dispatches(client, ak):
    plaintext = _mint(ak, scopes=["read:metrics"])
    r = client.get("/api/q/1/aggregates", headers=_auth(plaintext))
    assert r.status_code == 200
    body = r.get_json()
    assert body["shape"] == "aggregates"
    assert body["contract"] == "q/1"
    assert client.dispatch_calls[-1][0] == "aggregates"


def test_ungranted_shape_is_403_and_names_the_scope(client, ak):
    plaintext = _mint(ak, scopes=["read:metrics"])
    r = client.get("/api/q/1/transcript?session_id=x", headers=_auth(plaintext))
    assert r.status_code == 403
    body = r.get_json()
    assert body["required_scope"] == "read:content"
    assert body["held_scopes"] == ["read:metrics"]
    assert not client.dispatch_calls, "a refused query must never reach the store"


def test_a_metrics_key_cannot_reach_any_content_shape(client, ak):
    """The promise on the tin, checked against every shape rather than a
    representative one."""
    from clawmetry import query_contract as qc

    plaintext = _mint(ak, scopes=["read:metrics"])
    for shape in qc.live_methods_by_scope(qc.SCOPE_CONTENT):
        r = client.get(f"/api/q/1/{shape}?session_id=x", headers=_auth(plaintext))
        assert r.status_code == 403, f"{shape} was reachable with read:metrics"


def test_unknown_shape_is_404(client, ak):
    r = client.get("/api/q/1/definitely_not_a_shape", headers=_auth(_mint(ak)))
    assert r.status_code == 404


def test_planned_but_unserved_shape_is_404_not_500(client, ak):
    """`usage` is declared but not live. Reaching it must look like a typo,
    not like a crash."""
    from clawmetry import query_contract as qc

    planned = qc.methods_by_status(qc.STATUS_PLANNED)
    assert planned, "no planned methods left; drop this test or pick another"
    plaintext = _mint(ak, scopes=list(qc.SCOPES))
    for name in planned:
        r = client.get(f"/api/q/1/{name}", headers=_auth(plaintext))
        assert r.status_code == 404, name


def test_missing_required_arg_is_400_naming_the_arg(client, ak):
    plaintext = _mint(ak, scopes=["read:content"])
    r = client.get("/api/q/1/transcript", headers=_auth(plaintext))
    assert r.status_code == 400
    assert "session_id" in r.get_json()["error"]


def test_store_failure_is_503_without_leaking_internals(client, ak, monkeypatch):
    import routes.local_query as lq

    def _boom(shape, args):
        raise RuntimeError("/Users/someone/.clawmetry/clawmetry.duckdb is locked")

    monkeypatch.setattr(lq, "_dispatch", _boom)
    r = client.get("/api/q/1/health", headers=_auth(_mint(ak)))
    assert r.status_code == 503
    assert ".duckdb" not in r.get_json()["error"]
    assert "clawmetry doctor" in r.get_json()["error"]


def test_internal_dispatch_fields_are_stripped(client, ak):
    r = client.get("/api/q/1/aggregates", headers=_auth(_mint(ak)))
    assert [k for k in r.get_json() if k.startswith("_")] == []


# ── HTTP: the index and the guide ───────────────────────────────────────

def test_index_lists_only_granted_shapes(client, ak):
    plaintext = _mint(ak, scopes=["read:metrics"])
    body = client.get("/api/q/1", headers=_auth(plaintext)).get_json()
    from clawmetry import query_contract as qc

    assert {s["shape"] for s in body["shapes"]} == set(
        qc.live_methods_by_scope(qc.SCOPE_METRICS))
    held = {s["scope"] for s in body["scopes"] if s["held"]}
    assert held == {"read:metrics"}


def test_llms_txt_describes_only_what_the_key_can_run(client, ak):
    plaintext = _mint(ak, scopes=["read:metrics"])
    text = client.get("/api/q/1/llms.txt", headers=_auth(plaintext)).get_data(as_text=True)
    assert "GET /api/q/1/aggregates" in text
    assert "GET /api/q/1/transcript" not in text
    assert "Not available to this key" in text


def test_llms_txt_needs_a_key_too(client):
    assert client.get("/api/q/1/llms.txt").status_code == 401


# ── HTTP: CORS, the part that matters most ──────────────────────────────

def test_cors_header_only_for_an_origin_the_key_named(client, ak):
    plaintext = _mint(ak, origins=["http://localhost:3000"])
    ok = client.get("/api/q/1/health",
                    headers={**_auth(plaintext), "Origin": "http://localhost:3000"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert ok.headers.get("Vary") == "Origin"

    bad = client.get("/api/q/1/health",
                     headers={**_auth(plaintext), "Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in bad.headers, (
        "a key's data was made readable to an origin it never named"
    )


def test_cors_is_never_a_wildcard(client, ak):
    plaintext = _mint(ak)
    r = client.get("/api/q/1/health",
                   headers={**_auth(plaintext), "Origin": "http://localhost:3000"})
    assert r.headers.get("Access-Control-Allow-Origin") != "*"


def test_an_origin_none_key_gets_no_cors_at_all(client, ak):
    """A key created for a script must be useless from a browser, even
    from an origin some OTHER key has authorised."""
    _mint(ak, name="browser", origins=["http://localhost:3000"])
    script = _mint(ak, name="script", origins=[])
    r = client.get("/api/q/1/health",
                   headers={**_auth(script), "Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert "Access-Control-Allow-Origin" not in r.headers


def test_preflight_is_answered_only_for_a_known_origin(client, ak):
    _mint(ak, origins=["http://localhost:3000"])
    ok = client.options("/api/q/1/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    })
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    bad = client.options("/api/q/1/health", headers={
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "GET",
    })
    assert "Access-Control-Allow-Origin" not in bad.headers


def test_no_cors_when_authentication_failed(client, ak):
    """A 401 body is not interesting, but leaking a header on the failure
    path is how a probe learns which origins are authorised."""
    _mint(ak, origins=["https://known.example"])
    r = client.get("/api/q/1/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 401
    assert "Access-Control-Allow-Origin" not in r.headers


def test_origin_matching_ignores_case_and_trailing_slash(client, ak):
    plaintext = _mint(ak, origins=["https://My-UI.Example"])
    r = client.get("/api/q/1/health",
                   headers={**_auth(plaintext), "Origin": "https://my-ui.example/"})
    assert r.headers.get("Access-Control-Allow-Origin")


def test_the_api_is_get_only(client, ak):
    plaintext = _mint(ak)
    for method in ("post", "put", "delete", "patch"):
        r = getattr(client, method)("/api/q/1/health", headers=_auth(plaintext))
        assert r.status_code == 405, f"{method.upper()} was accepted"


# ── rate limiting ───────────────────────────────────────────────────────

def test_rate_limit_trips_and_says_what_to_do(client, ak, monkeypatch):
    monkeypatch.setattr(client.pub, "RATE_LIMIT_PER_MIN", 3)
    client.pub._RATE.clear()
    plaintext = _mint(ak)
    codes = [client.get("/api/q/1/health", headers=_auth(plaintext)).status_code
             for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3:] == [429, 429]
    body = client.get("/api/q/1/health", headers=_auth(plaintext)).get_json()
    assert "CLAWMETRY_API_RATE_LIMIT" in body["error"]


def test_rate_limit_is_per_key(client, ak, monkeypatch):
    monkeypatch.setattr(client.pub, "RATE_LIMIT_PER_MIN", 2)
    client.pub._RATE.clear()
    a = _mint(ak, name="a")
    b = _mint(ak, name="b")
    for _ in range(2):
        client.get("/api/q/1/health", headers=_auth(a))
    assert client.get("/api/q/1/health", headers=_auth(a)).status_code == 429
    assert client.get("/api/q/1/health", headers=_auth(b)).status_code == 200


# ── the management endpoints stay on the dashboard's own gate ───────────

@pytest.fixture
def admin(ak):
    from flask import Flask

    import routes.infra as infra

    app = Flask(__name__)
    app.register_blueprint(infra.bp_security)
    return app.test_client()


def test_management_mint_list_revoke(admin):
    made = admin.post("/api/apikeys", json={
        "name": "from-ui", "scopes": ["read:metrics"],
        "origins": ["http://localhost:5173"]}).get_json()
    assert made["ok"] and made["key"].startswith("cmk_")
    assert "hash" not in made["record"]

    listed = admin.get("/api/apikeys").get_json()
    assert [k["name"] for k in listed["keys"]] == ["from-ui"]
    assert all("hash" not in k for k in listed["keys"])

    kid = made["record"]["id"]
    assert admin.delete("/api/apikeys/" + kid).get_json()["ok"] is True
    assert admin.delete("/api/apikeys/" + kid).status_code == 404


def test_management_refuses_a_browser_key_with_no_origin(admin):
    r = admin.post("/api/apikeys", json={"name": "x", "scopes": ["read:metrics"],
                                         "origins": []})
    assert r.status_code == 400
    assert "wildcard" in r.get_json()["error"]


def test_management_allows_an_explicit_non_browser_key(admin):
    r = admin.post("/api/apikeys", json={"name": "cron", "scopes": ["read:metrics"],
                                         "origins": [], "browser": False})
    assert r.status_code == 200
    assert r.get_json()["record"]["origins"] == []


def test_management_never_carries_a_cors_header(admin, ak):
    """The read API is cross-origin readable; minting keys must not be.

    This is the specific mistake the path guard in ``public_api._add_cors``
    exists to prevent, so it is checked from the outside too.
    """
    _mint(ak, origins=["http://localhost:3000"])
    r = admin.get("/api/apikeys", headers={"Origin": "http://localhost:3000"})
    assert "Access-Control-Allow-Origin" not in r.headers


def test_management_surfaces_a_sentence_not_a_code(admin, monkeypatch):
    import clawmetry.apikeys as mod

    monkeypatch.setattr(mod, "create", lambda *a, **k: (_ for _ in ()).throw(OSError("EACCES")))
    r = admin.post("/api/apikeys", json={"name": "x", "scopes": ["read:metrics"],
                                         "origins": ["http://localhost:3000"]})
    assert r.status_code == 500
    err = r.get_json()["error"]
    assert "EACCES" not in err and "~/.clawmetry" in err
