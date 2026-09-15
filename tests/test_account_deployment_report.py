"""A sign-in tells the cloud account whether it is cloud or self-hosted.

REQ-OGV-ADC-001. The onboarding choice used to live only on the anonymous
install ping, which cannot be joined to an account for a self-hosted install
(it never registers a node). The trial sign-in call is authenticated with the
account key, so the choice rides on it.

Criterion -> tests:

* AC-OGV-ADC-001.1 -- test_signup_trial_posts_the_deployment[managed],
  tests/test_connect_provisioning_order.py (managed terminal connect)
* AC-OGV-ADC-001.2 -- test_signup_trial_posts_the_deployment[selfhost],
  tests/test_connect_otp_skip.py (keep-local terminal connect)
* AC-OGV-ADC-001.3 -- test_dashboard_trial_call_posts_the_deployment, and
  tests/test_cloud_cta_oauth.py (each dashboard sign-in names its rail)
* AC-OGV-ADC-001.4 -- test_unknown_deployment_is_never_sent,
  test_a_rejected_report_changes_nothing_about_the_signin
"""

import io
import json
import urllib.error

import pytest

import clawmetry.cli as cli
from clawmetry import onboarding_state


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_trial_server(monkeypatch, response=None, error=None):
    """Record every trial call body; answer with ``response`` or raise."""
    posted = []

    def _urlopen(req, timeout=0):
        posted.append(json.loads(req.data.decode()))
        if error is not None:
            raise error
        return _FakeResp(json.dumps(response).encode())

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    import clawmetry.license as _lic
    monkeypatch.setattr(_lic, "activate", lambda key, node_id=None, actor="": (True, "ok"))
    monkeypatch.setattr(_lic, "_node_id", lambda: "n1")
    monkeypatch.setattr(_lic, "_cloud_base", lambda: "https://app.example.com")
    return posted


def _signed_in_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps({"api_key": "cm_signed_in", "node_id": "n1"}))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


_ACTIVE = {"ok": True, "key": "CLAW1.trial.key", "expires_at": 9999999999,
           "reused": False, "expired": False}


def test_unknown_deployment_is_never_sent():
    """AC-OGV-ADC-001.4: only a recognised value rides along. A caller that
    does not know the choice must leave the account untouched, not guess."""
    body = onboarding_state.trial_signup_body
    assert body("cm_k", "managed") == {"api_key": "cm_k", "deployment": "managed"}
    assert body("cm_k", " SelfHost ") == {"api_key": "cm_k", "deployment": "selfhost"}
    for unknown in ("", None, "cloud", "selfhost_trial", "local"):
        assert body("cm_k", unknown) == {"api_key": "cm_k"}, unknown


@pytest.mark.parametrize("deployment", ["managed", "selfhost"])
def test_signup_trial_posts_the_deployment(monkeypatch, tmp_path, deployment):
    """AC-OGV-ADC-001.1 / 001.2: the terminal trial call carries the choice."""
    _signed_in_home(monkeypatch, tmp_path)
    posted = _fake_trial_server(monkeypatch, response=_ACTIVE)

    assert cli._activate_signup_trial(deployment) is True
    assert posted == [{"api_key": "cm_signed_in", "deployment": deployment}]


def test_dashboard_trial_call_posts_the_deployment(monkeypatch):
    """AC-OGV-ADC-001.3: the dashboard's shared trial helper carries it too."""
    import dashboard as _d

    posted = _fake_trial_server(monkeypatch, response=_ACTIVE)
    assert _d._activate_trial_for_key("cm_dash", deployment="selfhost") == "active"
    assert posted == [{"api_key": "cm_dash", "deployment": "selfhost"}]


def test_a_rejected_report_changes_nothing_about_the_signin(monkeypatch, tmp_path):
    """AC-OGV-ADC-001.4: a cloud that refuses the call (an older server, an
    outage) yields exactly the result the call without a deployment yields,
    and never raises into the sign-in."""
    import dashboard as _d

    _signed_in_home(monkeypatch, tmp_path)
    rejected = urllib.error.HTTPError(
        "https://app.example.com/api/license/trial/signup", 400, "Bad Request",
        None, io.BytesIO(b'{"error":"bad"}'))
    _fake_trial_server(monkeypatch, error=rejected)

    assert (cli._activate_signup_trial("managed")
            == cli._activate_signup_trial() is False)
    assert (_d._activate_trial_for_key("cm_dash", deployment="selfhost")
            == _d._activate_trial_for_key("cm_dash") == "unavailable")
