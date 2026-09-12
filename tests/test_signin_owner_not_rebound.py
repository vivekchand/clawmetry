"""A rejected account must not become the owner for its next sign-in."""
from unittest.mock import patch

import pytest
from flask import Flask


@pytest.mark.parametrize("mode", ["managed", "selfhost"])
def test_retry_cannot_turn_another_account_into_the_machine_owner(mode):
    import dashboard as d
    from routes.overview import bp_overview
    from tests.test_verify_otp_opens_dashboard import _FakeResp, KEY

    owner = {"key": "cm_original_owner"}

    def pair(key):
        owner["key"] = key
        return "n1", "active"

    def connect(key):
        pair(key)
        return "n1", "enc", "active"

    app = Flask(__name__)
    app.before_request(d._check_auth)
    app.register_blueprint(bp_overview)
    with patch.object(d, "GATEWAY_TOKEN", "test-gateway-secret"), \
         patch.object(d, "_SERVER_HOST", "127.0.0.1"), \
         patch.object(d, "_read_cloud_token", lambda: owner["key"]), \
         patch.object(d, "_selfhost_signin_with_key", pair), \
         patch.object(d, "_full_connect_with_key", connect), \
         patch("urllib.request.urlopen", lambda *a, **k: _FakeResp()):
        for _ in range(2):
            response = app.test_client().post(
                "/api/cloud-cta/verify-otp", base_url="http://untrusted.example:8900",
                headers={"Origin": "http://untrusted.example:8900"},
                json={"email": "other@example.com", "code": "123456", "mode": mode},
            )
            assert response.status_code == 403
            assert "dashboard_token" not in response.get_json()
        assert owner["key"] != KEY
