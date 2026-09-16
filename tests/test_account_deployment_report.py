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
* AC-OGV-ADC-004.1 -- test_the_body_names_the_operating_system_and_client,
  test_signup_trial_posts_the_deployment
* AC-OGV-ADC-004.2 -- test_the_body_names_the_operating_system_and_client
  (CLAWMETRY_LAUNCHER=desktop, inherited by a spawned `clawmetry connect`)
* AC-OGV-ADC-004.3 -- test_an_unrecognised_operating_system_is_omitted,
  test_unknown_deployment_is_never_sent
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


def test_unknown_deployment_is_never_sent(monkeypatch):
    """AC-OGV-ADC-001.4: only a recognised value rides along. A caller that
    does not know the choice must leave the account untouched, not guess."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.delenv("CLAWMETRY_LAUNCHER", raising=False)
    monkeypatch.delenv("CLAWMETRY_DESKTOP_VERSION", raising=False)
    body = onboarding_state.trial_signup_body
    base = {"api_key": "cm_k", "os": "Linux", "client": "cli"}
    assert body("cm_k", "managed") == {**base, "deployment": "managed"}
    assert body("cm_k", " SelfHost ") == {**base, "deployment": "selfhost"}
    for unknown in ("", None, "cloud", "selfhost_trial", "local"):
        assert body("cm_k", unknown) == base, unknown


def test_the_body_names_the_operating_system_and_client(monkeypatch):
    """AC-OGV-ADC-004.1 and AC-OGV-ADC-004.2: every sign-in reports what it runs on. The
    desktop shell exports CLAWMETRY_LAUNCHER, which a `clawmetry connect` it
    spawns inherits, so both are read from the machine rather than passed in."""
    monkeypatch.delenv("CLAWMETRY_LAUNCHER", raising=False)
    monkeypatch.delenv("CLAWMETRY_DESKTOP_VERSION", raising=False)
    for reported, expected in (("Darwin", "Darwin"), ("Windows", "Windows"),
                               ("Linux", "Linux")):
        monkeypatch.setattr("platform.system", lambda r=reported: r)
        assert onboarding_state.trial_signup_body("cm_k")["os"] == expected
        assert onboarding_state.trial_signup_body("cm_k")["client"] == "cli"

    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    assert onboarding_state.trial_signup_body("cm_k")["client"] == "desktop"
    monkeypatch.delenv("CLAWMETRY_LAUNCHER")
    monkeypatch.setenv("CLAWMETRY_DESKTOP_VERSION", "1.2.3")
    assert onboarding_state.trial_signup_body("cm_k")["client"] == "desktop"


@pytest.mark.parametrize("reported", ["Haiku", "", "linux-gnu"])
def test_an_unrecognised_operating_system_is_omitted(monkeypatch, reported):
    """AC-OGV-ADC-004.3: an account keeps the operating system it had rather
    than being handed a name the cloud does not know."""
    monkeypatch.setattr("platform.system", lambda: reported)
    assert "os" not in onboarding_state.trial_signup_body("cm_k")


@pytest.mark.parametrize("deployment", ["managed", "selfhost"])
def test_signup_trial_posts_the_deployment(monkeypatch, tmp_path, deployment):
    """AC-OGV-ADC-001.1 / 001.2: the terminal trial call carries the choice,
    beside what the machine runs (pinned here; CI runs three real OSes)."""
    _signed_in_home(monkeypatch, tmp_path)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.delenv("CLAWMETRY_LAUNCHER", raising=False)
    monkeypatch.delenv("CLAWMETRY_DESKTOP_VERSION", raising=False)
    posted = _fake_trial_server(monkeypatch, response=_ACTIVE)

    assert cli._activate_signup_trial(deployment) is True
    assert posted == [{"api_key": "cm_signed_in", "deployment": deployment,
                       "os": "Linux", "client": "cli"}]


def test_dashboard_trial_call_posts_the_deployment(monkeypatch):
    """AC-OGV-ADC-001.3: the dashboard's shared trial helper carries it too."""
    import dashboard as _d

    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    posted = _fake_trial_server(monkeypatch, response=_ACTIVE)
    assert _d._activate_trial_for_key("cm_dash", deployment="selfhost") == "active"
    assert posted == [{"api_key": "cm_dash", "deployment": "selfhost",
                       "os": "Darwin", "client": "desktop"}]


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
