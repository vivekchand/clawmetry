"""
Enterprise TLS bootstrap tests (clawmetry/net.py + clawmetry/doctor.py).

Covers the corporate TLS-interception fixes:
  * VERIFY_X509_STRICT (Python 3.13 default-on) is cleared on every context
    we build — while hostname checking and chain validation stay ON.
  * CLAWMETRY_CA_BUNDLE env / config ``ca_bundle`` / SSL_CERT_FILE /
    REQUESTS_CA_BUNDLE are honored, env winning over config.
  * tls_verify:false / CLAWMETRY_TLS_NO_VERIFY=1 escape hatch.
  * doctor's issuer classification (public CA vs corporate interception
    CA) using real DER certificates generated as fixtures.

Pure unit tests — no running server, no network.
"""
from __future__ import annotations

import datetime
import ssl

import pytest

from clawmetry import net
from clawmetry import doctor


# ── fixtures ───────────────────────────────────────────────────────────────

_ENV_VARS = (
    "CLAWMETRY_CA_BUNDLE", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
    "CLAWMETRY_TLS_NO_VERIFY",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    """Isolate from the developer machine: no TLS env vars, no real config."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(net, "CONFIG_PATH", str(tmp_path / "config.json"))
    yield


def _make_self_signed_pem(tmp_path, name, org, cn):
    """Generate a self-signed cert PEM; returns (path, cert)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                       critical=True)
        .sign(key, hashes.SHA256())
    )
    path = tmp_path / (name + ".pem")
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return str(path), cert


def _loaded_ca_subjects(ctx):
    return {
        tuple(rdn[0] for rdn in c.get("subject", ()))
        for c in ctx.get_ca_certs()
    }


def _has_org(ctx, org):
    return any(
        ("organizationName", org) in subj for subj in _loaded_ca_subjects(ctx)
    )


# ── strict flag ────────────────────────────────────────────────────────────

@pytest.mark.skipif(not hasattr(ssl, "VERIFY_X509_STRICT"),
                    reason="ssl build lacks VERIFY_X509_STRICT")
def test_strict_flag_cleared_on_built_context():
    ctx = net.build_ssl_context(config={})
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)


def test_built_context_still_verifies():
    """Relaxing strict mode must NOT weaken real verification."""
    ctx = net.build_ssl_context(config={})
    assert ctx.check_hostname is True
    assert ctx.verify_mode == ssl.CERT_REQUIRED


@pytest.mark.skipif(not hasattr(ssl, "VERIFY_X509_STRICT"),
                    reason="ssl build lacks VERIFY_X509_STRICT")
def test_relax_strict_verification_helper():
    ctx = ssl.create_default_context()
    ctx.verify_flags |= ssl.VERIFY_X509_STRICT
    net.relax_strict_verification(ctx)
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)


# ── CA bundle resolution + loading ────────────────────────────────────────

def test_ca_bundle_env_var(tmp_path, monkeypatch):
    path, _ = _make_self_signed_pem(tmp_path, "corp", "Contoso IT", "Contoso Root CA")
    monkeypatch.setenv("CLAWMETRY_CA_BUNDLE", path)
    ctx = net.build_ssl_context(config={})
    assert _has_org(ctx, "Contoso IT")


def test_ca_bundle_config_key(tmp_path):
    path, _ = _make_self_signed_pem(tmp_path, "corp", "Initech Sec", "Initech Root")
    ctx = net.build_ssl_context(config={"ca_bundle": path})
    assert _has_org(ctx, "Initech Sec")


def test_env_wins_over_config(tmp_path, monkeypatch):
    env_path, _ = _make_self_signed_pem(tmp_path, "env", "EnvCorp", "EnvCorp Root")
    cfg_path, _ = _make_self_signed_pem(tmp_path, "cfg", "CfgCorp", "CfgCorp Root")
    monkeypatch.setenv("CLAWMETRY_CA_BUNDLE", env_path)
    assert net.ca_bundle_path(config={"ca_bundle": cfg_path}) == env_path
    ctx = net.build_ssl_context(config={"ca_bundle": cfg_path})
    assert _has_org(ctx, "EnvCorp")
    assert not _has_org(ctx, "CfgCorp")


@pytest.mark.parametrize("var", ["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"])
def test_standard_ca_env_vars_honored(tmp_path, monkeypatch, var):
    path, _ = _make_self_signed_pem(tmp_path, "std", "StdCorp", "StdCorp Root")
    monkeypatch.setenv(var, path)
    assert net.ca_bundle_path(config={}) == path


def test_missing_bundle_is_skipped_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CA_BUNDLE", str(tmp_path / "nope.pem"))
    assert net.ca_bundle_path(config={}) == ""
    # And building a context with the bad path still succeeds.
    ctx = net.build_ssl_context(config={})
    assert ctx.verify_mode == ssl.CERT_REQUIRED


# ── escape hatch ───────────────────────────────────────────────────────────

def test_tls_verify_false_config_disables_verification():
    ctx = net.build_ssl_context(config={"tls_verify": False})
    assert ctx.check_hostname is False
    assert ctx.verify_mode == ssl.CERT_NONE


def test_tls_no_verify_env_disables_verification(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_TLS_NO_VERIFY", "1")
    ctx = net.build_ssl_context(config={})
    assert ctx.verify_mode == ssl.CERT_NONE


def test_verification_on_by_default():
    assert not net.tls_verify_disabled(config={})
    ctx = net.build_ssl_context(config={})
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_doctor_can_ignore_escape_hatch(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_TLS_NO_VERIFY", "1")
    ctx = net.build_ssl_context(config={}, allow_insecure=False)
    assert ctx.verify_mode == ssl.CERT_REQUIRED


# ── bootstrap resilience ───────────────────────────────────────────────────

def test_configure_survives_missing_truststore(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def _no_truststore(name, *a, **kw):
        if name == "truststore":
            raise ImportError("simulated: no truststore")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _no_truststore)
    ctx = net.configure_outbound_network(config={})
    assert ctx is not None
    assert ctx.verify_mode == ssl.CERT_REQUIRED


# ── doctor issuer classification (fake cert fixtures) ─────────────────────

CORPORATE_ISSUERS = [
    ("Zscaler Inc.", "Zscaler Root CA"),
    ("Netskope Inc", "ca.netskope.com"),
    ("Palo Alto Networks", "decrypt.paloaltonetworks.com"),
    ("Contoso Ltd", "Contoso Corporate Proxy CA"),
]

PUBLIC_ISSUERS = [
    ("Let's Encrypt", "R11"),
    ("DigiCert Inc", "DigiCert Global Root G2"),
    ("Google Trust Services", "WR2"),
    ("Amazon", "Amazon RSA 2048 M02"),
]


@pytest.mark.parametrize("org,cn", CORPORATE_ISSUERS)
def test_classify_corporate_issuer_from_der(tmp_path, org, cn):
    from cryptography.hazmat.primitives import serialization
    _, cert = _make_self_signed_pem(tmp_path, "c", org, cn)
    der = cert.public_bytes(serialization.Encoding.DER)
    issuer = doctor.issuer_name_from_der(der)
    assert org.split()[0].lower() in issuer.lower()
    assert doctor.classify_issuer(issuer) == "corporate"


@pytest.mark.parametrize("org,cn", PUBLIC_ISSUERS)
def test_classify_public_issuer_from_der(tmp_path, org, cn):
    from cryptography.hazmat.primitives import serialization
    _, cert = _make_self_signed_pem(tmp_path, "p", org, cn)
    der = cert.public_bytes(serialization.Encoding.DER)
    issuer = doctor.issuer_name_from_der(der)
    assert doctor.classify_issuer(issuer) == "public"


def test_classify_unknown_or_empty_is_corporate():
    assert doctor.classify_issuer("") == "corporate"
    assert doctor.classify_issuer("O=Random Startup MITM,CN=proxy") == "corporate"


def test_classify_matches_org_not_cn():
    """A CN like *.badssl.com must not substring-match the 'ssl.com' entry."""
    assert doctor.classify_issuer(
        "CN=*.badssl.com,O=BadSSL,L=San Francisco,ST=California,C=US"
    ) == "corporate"
    # But a genuine SSL.com issuer org still classifies public.
    assert doctor.classify_issuer(
        "CN=SSL.com TLS RSA Root CA 2022,O=SSL.com,C=US"
    ) == "public"


def test_intercept_vendor_detection():
    assert doctor.intercept_vendor("O=Zscaler Inc.,CN=Zscaler Root CA") == "zscaler"
    assert doctor.intercept_vendor("O=Let's Encrypt,CN=R11") == ""
    # Word boundaries: "cisco" must not match "San Francisco".
    assert doctor.intercept_vendor("O=BadSSL,L=San Francisco,C=US") == ""


def test_windows_fix_text_mentions_export_steps():
    txt = doctor._windows_fix_text("O=Zscaler Inc.,CN=Zscaler Root CA")
    assert "TLS interception detected" in txt
    assert "certmgr.msc" in txt
    assert "Trusted Root Certification Authorities" in txt
    assert "Base-64" in txt
    assert "CLAWMETRY_CA_BUNDLE" in txt
