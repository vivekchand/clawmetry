"""File roots and loopback trust must hold at the HTTP boundary.

AC-OBS-LADC-005.1: file and cache containment before reads and writes.
AC-OBS-LADC-005.2: linked roots work; outside links are refused.
AC-OBS-LADC-005.3: the peer, Host and forwarding headers control local trust.
AC-OBS-LADC-005.4: direct clients and authenticated proxies keep working.
"""
import pytest
from flask import Flask, jsonify

import dashboard
from routes import infra, meta, sessions, skills


@pytest.fixture(scope="session", autouse=True)
def server():
    """These tests own their HTTP app and never boot the user's dashboard."""
    yield None


@pytest.fixture
def surface(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "ok.txt").write_text("INSIDE", encoding="utf-8")
    outside = tmp_path / "workspace_evil"
    outside.mkdir()
    (outside / "secret.txt").write_text("OUTSIDE", encoding="utf-8")
    monkeypatch.setattr(dashboard, "WORKSPACE", str(workspace))
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "boundary-test-token")
    monkeypatch.setattr(infra, "is_local_store_read_enabled", lambda: False)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.before_request(dashboard._check_auth)
    app.register_blueprint(infra.bp_memory)
    app.register_blueprint(skills.bp_skills)
    app.register_blueprint(sessions.bp_sessions)
    app.register_blueprint(meta.bp_auth)
    monkeypatch.setattr(skills, "_find_skill_dir", lambda _: str(workspace))

    @app.route("/api/boundary-probe", methods=["GET", "POST"])
    def probe():
        return jsonify(ok=True)

    return app.test_client(), workspace, outside


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
@pytest.mark.parametrize("escape", ["../workspace_evil/secret.txt", "../elsewhere/secret.txt", "absolute"])
def test_file_rejects_escape(surface, method, escape):
    client, _, outside = surface
    path = str(outside / "secret.txt") if escape == "absolute" else escape
    if method == "GET":
        response = client.get("/api/file", query_string={"path": path})
    else:
        response = client.open("/api/file", method=method, json={"path": path, "content": "changed"})
    assert response.status_code == 403
    assert (outside / "secret.txt").read_text(encoding="utf-8") == "OUTSIDE"
    assert not (outside.parent / "elsewhere").exists()


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_file_still_reads_and_writes_inside_root(surface, method):
    client, workspace, _ = surface
    if method == "GET":
        response = client.get("/api/file", query_string={"path": "nested/../ok.txt"})
        assert response.get_json()["content"] == "INSIDE"
    else:
        response = client.open("/api/file", method=method, json={"path": "nested/new.txt", "content": "saved"})
        assert (workspace / "nested/new.txt").read_text(encoding="utf-8") == "saved"
    assert response.status_code == 200


def test_store_fast_path_cannot_skip_containment(surface, monkeypatch):
    client, _, _ = surface
    monkeypatch.setattr(infra, "is_local_store_read_enabled", lambda: True)
    calls = []
    monkeypatch.setattr(infra, "_try_local_store_file", lambda path: calls.append(path) or {"content": "cached"})
    response = client.get("/api/file", query_string={"path": "../workspace_evil/secret.txt"})
    assert response.status_code == 403
    assert calls == []
    assert client.get("/api/file?path=ok.txt").get_json()["content"] == "cached"


def test_skill_file_rejects_prefix_collision(surface):
    client, _, _ = surface
    response = client.get("/api/skills/example/file", query_string={"path": "../workspace_evil/secret.txt"})
    assert response.status_code == 400


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_symlink_escape_is_refused_but_symlinked_workspace_works(surface, monkeypatch, method):
    client, workspace, outside = surface
    try:
        (workspace / "escape").symlink_to(outside, target_is_directory=True)
        alias = workspace.parent / "workspace_alias"
        alias.symlink_to(workspace, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this host")
    monkeypatch.setattr(dashboard, "WORKSPACE", str(alias))
    assert client.get("/api/file?path=ok.txt").status_code == 200
    if method == "GET":
        response = client.get("/api/file?path=escape/secret.txt")
    else:
        response = client.open("/api/file", method=method, json={"path": "escape/new.txt", "content": "changed"})
    assert response.status_code == 403
    assert not (outside / "new.txt").exists()


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8900", "localhost.evil.example", "127.0.0.1.evil.example"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_rebound_request_needs_credentials_even_with_same_origin(surface, host, method):
    client, _, _ = surface
    response = client.open("/api/boundary-probe", method=method,
                           base_url="http://" + host, headers={"Origin": "http://" + host})
    assert response.status_code == 401


@pytest.mark.parametrize("header", ["X-Forwarded-For", "X-Real-IP", "Forwarded"])
def test_proxy_headers_do_not_get_loopback_exemption(surface, header):
    client, _, _ = surface
    assert client.get("/api/boundary-probe", headers={header: "203.0.113.1"}).status_code == 401


@pytest.mark.parametrize("host", ["localhost", "LOCALHOST:8900", "127.0.0.1:8900", "[::1]:8900"])
def test_direct_loopback_remains_zero_config(surface, host):
    client, _, _ = surface
    assert client.get("/api/file?path=ok.txt", base_url="http://" + host).status_code == 200


def test_authenticated_reverse_proxy_still_works(surface):
    client, _, _ = surface
    response = client.get("/api/file?path=ok.txt", base_url="http://dashboard.example",
                          headers={"X-Forwarded-For": "203.0.113.1", "Authorization": "Bearer boundary-test-token"})
    assert response.status_code == 200


@pytest.mark.parametrize("authorized", [False, True])
@pytest.mark.parametrize("headers", [{"Host": "evil.example"}, {"X-Forwarded-For": "203.0.113.1"}])
def test_bootstrap_keeps_its_stricter_refusal_contract(surface, authorized, headers):
    client, _, _ = surface
    headers = dict(headers)
    if authorized:
        headers["Authorization"] = "Bearer boundary-test-token"
    response = client.get("/api/auth/detected-token", headers=headers)
    assert response.status_code == 403
    assert "token" not in response.get_json()


@pytest.mark.parametrize("path", [None, [], {}, 3, "bad\0path"])
def test_invalid_write_paths_do_not_crash(surface, path):
    client, _, _ = surface
    assert client.post("/api/file", json={"path": path, "content": "x"}).status_code == 400


def test_filesystem_root_workspace(surface, monkeypatch):
    client, workspace, _ = surface
    monkeypatch.setattr(dashboard, "WORKSPACE", workspace.anchor)
    response = client.get("/api/file", query_string={"path": str(workspace / "ok.txt")})
    assert response.status_code == 200


@pytest.mark.parametrize("url", [
    "/api/transcript/linked",
    "/api/transcript-events/linked",
    "/api/session-model-journey/linked",
    "/api/sessions/linked/cost-breakdown",
    "/api/sessions/linked/export",
    "/api/sessions/linked/config-drift",
    "/api/sessions/linked/lexical-drift",
    "/api/sessions/linked/intent-divergence",
    "/api/sessions/linked/intent-drift",
])
def test_session_fallbacks_refuse_outside_links(surface, monkeypatch, url):
    client, workspace, outside = surface
    target = outside / "secret.jsonl"
    target.write_text('{}\n', encoding="utf-8")
    try:
        (workspace / "linked.jsonl").symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this host")
    monkeypatch.setattr(dashboard, "SESSIONS_DIR", str(workspace))
    monkeypatch.setattr(sessions, "is_local_store_read_enabled", lambda: False)
    assert client.get(url).status_code == 403


def test_rebound_file_read_and_write_over_real_http(surface):
    import threading

    import requests
    from werkzeug.serving import make_server

    client, _, outside = surface
    httpd = make_server("127.0.0.1", 0, client.application)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:" + str(httpd.server_port)
    session = requests.Session()
    session.trust_env = False
    try:
        assert session.get(base + "/api/file?path=ok.txt", timeout=5).status_code == 200
        headers = {"Host": "evil.example", "Origin": "http://evil.example"}
        assert session.get(base + "/api/file?path=ok.txt", headers=headers, timeout=5).status_code == 401
        assert session.post(base + "/api/file", headers=headers,
                            json={"path": "../workspace_evil/planted.txt", "content": "x"},
                            timeout=5).status_code == 401
        assert not (outside / "planted.txt").exists()
        response = session.get(base + "/api/file", params={"path": "../workspace_evil/secret.txt"}, timeout=5)
        assert response.status_code == 403
    finally:
        session.close()
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
