"""Discretionary outbound calls must be off for self-hosted/air-gapped installs.

ClawMetry Enterprise self-hosted is sold on "your data never leaves your
network". A CISO validates that claim with tcpdump during a pilot, not by
reading the docs — so every discretionary destination needs a test, and the
gate needs to fail closed.

"Discretionary" excludes the deployment's own configured ingest endpoint: that
push is the product, and repointing it is exactly what self-hosting means.

Covers the three ways an operator declares this deployment private:
  * CLAWMETRY_ENDPOINT   — traffic repointed at a customer-run server
  * SELF_HOSTED          — this process *is* the customer's server
  * CLAWMETRY_OFFLINE    — air-gapped

The SELF_HOSTED case is the one that regressed: the server container does not
set CLAWMETRY_ENDPOINT (it *is* the endpoint), so a gate keyed only on
is_custom_endpoint() let the server itself phone home.
"""

import pytest

from clawmetry import endpoints


PRIVATE_ENVS = [
    pytest.param({"CLAWMETRY_ENDPOINT": "https://clawmetry.internal.acme.com"}, id="custom-endpoint"),
    pytest.param({"CLAWMETRY_INGEST_URL": "https://clawmetry.internal.acme.com"}, id="legacy-ingest-url"),
    pytest.param({"SELF_HOSTED": "true"}, id="self-hosted"),
    pytest.param({"CLAWMETRY_SELF_HOSTED": "1"}, id="self-hosted-alias"),
    pytest.param({"CLAWMETRY_OFFLINE": "1"}, id="offline"),
    pytest.param({"CLAWMETRY_OFFLINE": "yes"}, id="offline-yes"),
    pytest.param({"SELF_HOSTED": "on"}, id="self-hosted-on"),
]

ALL_KEYS = [
    "CLAWMETRY_ENDPOINT",
    "CLAWMETRY_INGEST_URL",
    "CLAWMETRY_APP_BASE",
    "SELF_HOSTED",
    "CLAWMETRY_SELF_HOSTED",
    "CLAWMETRY_OFFLINE",
    "CLAWMETRY_TELEMETRY_URL",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    """Start every test from a managed-cloud default, with no user config file."""
    for key in ALL_KEYS:
        monkeypatch.delenv(key, raising=False)
    # endpoints.py reads ~/.clawmetry/config.json and memoises on mtime; point
    # it somewhere empty so a developer's real config cannot flip a result.
    monkeypatch.setattr(endpoints, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(endpoints, "_cfg_cache", None)
    yield


def test_managed_cloud_default_is_not_suppressed():
    """The default install still phones home — otherwise the tests below prove nothing."""
    assert endpoints.egress_suppressed() is False


@pytest.mark.parametrize("env", PRIVATE_ENVS)
def test_private_deployments_suppress_egress(monkeypatch, env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert endpoints.egress_suppressed() is True


@pytest.mark.parametrize("falsy", ["", "0", "false", "no", "off"])
def test_falsy_flags_do_not_suppress(monkeypatch, falsy):
    """A disabled flag must not accidentally read as "private"."""
    monkeypatch.setenv("SELF_HOSTED", falsy)
    monkeypatch.setenv("CLAWMETRY_OFFLINE", falsy)
    assert endpoints.egress_suppressed() is False


@pytest.mark.parametrize("env", PRIVATE_ENVS)
def test_install_telemetry_url_empty_when_private(monkeypatch, env):
    """clawmetry.telemetry resolves to "" — no managed-cloud install ping."""
    from clawmetry import telemetry

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert telemetry._resolve_telemetry_url() == ""


def test_install_telemetry_url_set_on_managed_cloud():
    from clawmetry import telemetry

    assert telemetry._resolve_telemetry_url() == telemetry.TELEMETRY_URL_DEFAULT


def test_explicit_telemetry_url_still_wins(monkeypatch):
    """An operator pointing telemetry at their OWN collector is honoured."""
    from clawmetry import telemetry

    monkeypatch.setenv("SELF_HOSTED", "true")
    monkeypatch.setenv("CLAWMETRY_TELEMETRY_URL", "https://collector.acme.internal/i")
    assert telemetry._resolve_telemetry_url() == "https://collector.acme.internal/i"


def test_telemetry_fails_closed_when_the_gate_raises(monkeypatch):
    """A broken/older endpoints module must not produce a surprise phone-home.

    The pre-existing code swallowed the error and fell through to the default
    managed-cloud URL, so a partially-installed package meant a customer's
    self-hosted server pinged out. Now the except branch returns "".
    """
    from clawmetry import telemetry

    def _boom():
        raise ImportError("simulated partial install")

    monkeypatch.setattr(endpoints, "egress_suppressed", _boom)
    assert telemetry._resolve_telemetry_url() == ""


@pytest.mark.parametrize("env", PRIVATE_ENVS)
def test_public_ip_lookup_skipped_when_private(monkeypatch, env):
    """api.ipify.org is a third party nobody in the deployment agreed to.

    Only feeds a cosmetic startup banner line, so suppressing it costs nothing.
    """
    import dashboard

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    def _fail(*a, **kw):  # pragma: no cover - must never run
        raise AssertionError("get_public_ip() made a network call in a private deployment")

    monkeypatch.setattr("urllib.request.urlopen", _fail)
    assert dashboard.get_public_ip() is None


def test_public_ip_helper_fails_closed(monkeypatch):
    """If the suppression check itself raises, suppress rather than call out."""
    import dashboard

    monkeypatch.setattr(
        endpoints, "egress_suppressed", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    assert dashboard._egress_suppressed() is True


@pytest.mark.parametrize("env", PRIVATE_ENVS)
def test_unattended_update_never_checks_pypi_when_private(monkeypatch, env):
    """An air-gapped node hitting pypi.org can only time out; a monitored one
    shows unexplained egress mid-review. Upgrades there are the operator's."""
    from clawmetry import cli

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    # Explicitly re-arm the unrelated kill switch so this test proves the
    # egress gate is what stopped the call, not the CI/auto-update check.
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")

    def _fail(*a, **kw):  # pragma: no cover - must never run
        raise AssertionError("unattended update reached pypi.org in a private deployment")

    monkeypatch.setattr("urllib.request.urlopen", _fail)
    target, reason = cli._unattended_update_target("0.0.1")
    assert target is None
    assert "self-hosted" in reason or "offline" in reason
