from __future__ import annotations

import re
import os
import sys
import types
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def server():
    """These unit tests use Flask's test client and do not need a live server."""
    yield


def test_cli_v2_flag_sets_enabled_env_and_delegates_to_dashboard(
    monkeypatch, capsys
):
    from clawmetry import cli

    called = {}

    def fake_dashboard_main():
        called["argv"] = list(sys.argv)

    monkeypatch.delenv("CLAWMETRY_V2_ENABLED", raising=False)
    monkeypatch.delenv("CLAWMETRY_V2", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["clawmetry", "--v2", "--host", "127.0.0.1", "--port", "8900"],
    )
    monkeypatch.setitem(
        sys.modules, "dashboard", types.SimpleNamespace(main=fake_dashboard_main)
    )
    monkeypatch.setitem(
        sys.modules,
        "clawmetry.telemetry",
        types.SimpleNamespace(maybe_ping=lambda _version: None),
    )

    cli.main()

    assert sys.argv == ["clawmetry", "--host", "127.0.0.1", "--port", "8900"]
    assert called["argv"] == sys.argv
    assert os.environ["CLAWMETRY_V2_ENABLED"] == "1"
    assert "CLAWMETRY_V2" not in os.environ

    out = capsys.readouterr().out
    assert "/v2" in out
    assert "back to v1 at /" in out


def test_v2_is_404_when_blueprint_is_not_registered():
    app = Flask(__name__)
    client = app.test_client()

    assert client.get("/v2").status_code == 404


def test_v2_root_serves_react_bundle():
    from clawmetry.v2.routes import bp_v2

    app = Flask(__name__)
    app.register_blueprint(bp_v2)

    response = app.test_client().get("/v2")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<div id="root"></div>' in html
    assert 'src="/v2/assets/' in html


def test_v2_client_routes_fall_back_to_react_bundle():
    from clawmetry.v2.routes import bp_v2

    app = Flask(__name__)
    app.register_blueprint(bp_v2)

    response = app.test_client().get("/v2/anything/react/router/owns")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.get_data(as_text=True)


def test_v2_assets_are_served_from_vite_bundle():
    from clawmetry.v2.routes import bp_v2

    app = Flask(__name__)
    app.register_blueprint(bp_v2)
    client = app.test_client()

    index = client.get("/v2").get_data(as_text=True)
    match = re.search(r'src="(/v2/assets/[^"]+\.js)"', index)
    assert match is not None

    response = client.get(match.group(1))

    assert response.status_code == 200
    assert "javascript" in response.content_type
