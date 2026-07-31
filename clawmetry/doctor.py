"""
clawmetry doctor — enterprise network connectivity diagnostics.

Runs the exact chain a heartbeat needs (DNS → TCP → TLS → HTTP POST) against
ingest.clawmetry.com and prints pass/fail per step in plain language, so a
non-engineer on a screen-share can read it. Detects TLS-intercepting
proxies (Zscaler/Netskope/Palo Alto/…) by fetching the peer certificate
with verification off and classifying its issuer, then prints the exact
fix (export the corporate root CA → CLAWMETRY_CA_BUNDLE).

Exit code 0 only when every check passes.
"""
from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

from clawmetry import net as _net

INGEST_HOST_DEFAULT = "ingest.clawmetry.com"
TIMEOUT_S = 10

PASS = "[ OK ]"
FAIL = "[FAIL]"
WARN = "[WARN]"

# Issuer organizations of the public CAs that could plausibly sign
# clawmetry.com (or anything else on the public internet). If the issuer of
# the cert we receive matches none of these, the traffic is being re-signed
# on the customer's network. Matching is case-insensitive substring over the
# issuer RDNs (org + CN), so "DigiCert Global Root G2" matches "digicert".
WELL_KNOWN_PUBLIC_CAS = (
    "let's encrypt", "isrg", "digicert", "google trust services", "gts ",
    "amazon", "globalsign", "sectigo", "comodo", "usertrust", "godaddy",
    "go daddy", "starfield", "entrust", "identrust", "baltimore",
    "verisign", "thawte", "geotrust", "rapidssl", "cloudflare", "zerossl",
    "buypass", "ssl.com", "actalis", "certum", "quovadis", "harica",
    "telekom", "d-trust", "swisssign", "microsoft rsa", "microsoft ecc",
    "apple public", "certainly", "trustasia",
)

# Vendors whose names commonly appear in interception-proxy issuers. Only
# used to make the message friendlier — anything not in the public list is
# reported as interception either way.
KNOWN_INTERCEPT_VENDORS = (
    "zscaler", "netskope", "palo alto", "forcepoint", "bluecoat",
    "blue coat", "fortinet", "fortigate", "sophos", "mcafee", "cisco",
    "umbrella", "checkpoint", "check point", "watchguard", "mitmproxy",
    "broadcom", "symantec blue",
)


def issuer_name_from_der(der: bytes) -> str:
    """Human-readable issuer from a DER certificate.

    Uses ``cryptography`` (already a hard dependency for cloud sync);
    falls back to "" if parsing fails — never raises.
    """
    try:
        from cryptography import x509

        cert = x509.load_der_x509_certificate(der)
        return cert.issuer.rfc4514_string()
    except Exception:
        return ""


def classify_issuer(issuer: str) -> str:
    """'public' when the issuer looks like a well-known public CA, else 'corporate'.

    Matches against the issuer's O= (organization) values, not the full RDN
    string — a CN like ``*.badssl.com`` must not substring-match the
    "ssl.com" public-CA entry. Falls back to the full string only when no
    O= component exists.
    """
    low = (issuer or "").lower()
    if not low:
        return "corporate"
    import re

    orgs = re.findall(r"(?:^|,)\s*o=([^,]+)", low)
    haystack = " | ".join(orgs) if orgs else low
    for known in WELL_KNOWN_PUBLIC_CAS:
        if known in haystack:
            return "public"
    return "corporate"


def intercept_vendor(issuer: str) -> str:
    import re

    low = (issuer or "").lower()
    for vendor in KNOWN_INTERCEPT_VENDORS:
        # Word-boundary match: "cisco" must not hit "San Francisco".
        if re.search(r"\b" + re.escape(vendor) + r"\b", low):
            return vendor
    return ""


def _proxy_for_https() -> str:
    """The proxy URL urllib would use for https, or ""."""
    try:
        return urllib.request.getproxies().get("https", "") or ""
    except Exception:
        return ""


def _fetch_peer_cert_unverified(host: str, port: int, proxy: str = "") -> bytes:
    """TLS-handshake with verification OFF purely to grab the peer cert.

    This never carries application data — it exists so we can show the
    user WHO is actually terminating their TLS.
    """
    ctx = ssl._create_unverified_context()  # noqa: S323 — diagnostic fetch only
    _net.relax_strict_verification(ctx)
    sock = _open_tcp(host, port, proxy)
    try:
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            return tls.getpeercert(True) or b""
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _open_tcp(host: str, port: int, proxy: str = "") -> socket.socket:
    """TCP connection to host:port, tunnelling CONNECT through proxy if set."""
    if not proxy:
        return socket.create_connection((host, port), timeout=TIMEOUT_S)
    p = urllib.parse.urlparse(proxy if "://" in proxy else "http://" + proxy)
    sock = socket.create_connection((p.hostname, p.port or 3128), timeout=TIMEOUT_S)
    try:
        connect = "CONNECT {0}:{1} HTTP/1.1\r\nHost: {0}:{1}\r\n\r\n".format(host, port)
        sock.sendall(connect.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = sock.recv(4096)
            if not chunk:
                break
            resp = resp + chunk
        status_line = resp.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        if " 200" not in status_line:
            raise OSError("proxy CONNECT refused: " + status_line)
        return sock
    except Exception:
        sock.close()
        raise


def _windows_fix_text(issuer: str) -> str:
    vendor = intercept_vendor(issuer)
    vendor_note = (
        "  (That issuer is a {0} appliance — your IT team runs it.)\n".format(vendor)
        if vendor else ""
    )
    return (
        'TLS interception detected (issuer: {0}). Your network re-signs\n'
        "HTTPS traffic.\n"
        "{1}"
        "\n"
        "How to fix (Windows):\n"
        "  1. Press Win+R, run: certmgr.msc\n"
        "  2. Open: Trusted Root Certification Authorities > Certificates\n"
        "  3. Find your company's root CA (often named after your company\n"
        "     or the proxy vendor, e.g. the issuer shown above)\n"
        "  4. Right-click it > All Tasks > Export... > choose\n"
        '     "Base-64 encoded X.509 (.CER)" > save e.g. C:\\corp-root.cer\n'
        "  5. Point ClawMetry at it:\n"
        "       setx CLAWMETRY_CA_BUNDLE C:\\corp-root.cer\n"
        "     then restart the daemon (clawmetry sync restart).\n"
        "\n"
        "If ClawMetry was installed with the 'truststore' package (Python\n"
        "3.10+), the OS trust store is used automatically and this step is\n"
        "usually unnecessary — run doctor again after upgrading:\n"
        "  pip install --upgrade clawmetry truststore\n"
    ).format(issuer or "<unknown>", vendor_note)


def run_doctor(host: str = None, port: int = 443, out=print) -> int:
    """Run all connectivity checks. Returns process exit code (0 = all pass)."""
    if not host:
        from clawmetry.endpoints import ingest_url as _resolve_ingest_url
        host = _resolve_ingest_url()
    if "://" in host:
        parsed = urllib.parse.urlparse(host)
        port = parsed.port or 443
        host = parsed.hostname or INGEST_HOST_DEFAULT

    failures = 0
    out("ClawMetry network doctor")
    out("Target: {0}:{1}".format(host, port))
    st = _net.state()
    if st.get("configured"):
        trust = "OS trust store (truststore)" if st.get("truststore") \
            else "Python default (certifi/OpenSSL)"
        out("Trust source: " + trust)
        if st.get("ca_bundle"):
            out("Extra CA bundle: " + st["ca_bundle"])
        if st.get("verify_disabled"):
            out(WARN + " TLS verification is DISABLED (CLAWMETRY_TLS_NO_VERIFY /"
                " tls_verify:false) — insecure, pilot use only")
    out("")

    # ── 1. DNS ────────────────────────────────────────────────────────────
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        addrs = sorted({i[4][0] for i in infos})
        out("{0} DNS: {1} resolves to {2}".format(PASS, host, ", ".join(addrs[:4])))
    except Exception as e:
        failures += 1
        out("{0} DNS: could not resolve {1} ({2})".format(FAIL, host, e))
        out("       Check your internet connection / VPN, or ask IT whether")
        out("       this hostname is blocked by a web filter.")
        out("\nResult: FAIL — fix the items above and re-run `clawmetry doctor`.")
        return 1  # nothing further can work without DNS

    # ── 2. TCP ────────────────────────────────────────────────────────────
    proxy = _proxy_for_https()
    try:
        socket.create_connection((host, port), timeout=TIMEOUT_S).close()
        out("{0} TCP: direct connection to {1}:{2} works".format(PASS, host, port))
    except Exception as e:
        level = WARN if proxy else FAIL
        if not proxy:
            failures += 1
        out("{0} TCP: direct connection to {1}:{2} failed ({3})".format(
            level, host, port, e))
        if not proxy:
            out("       No HTTPS_PROXY is set. If your company requires a proxy,")
            out("       set HTTPS_PROXY (ask IT for the address) and re-run.")
    if proxy:
        try:
            _open_tcp(host, port, proxy).close()
            out("{0} TCP via proxy: {1} tunnels to {2}:{3}".format(
                PASS, proxy, host, port))
        except Exception as e:
            failures += 1
            out("{0} TCP via proxy: {1} could not reach {2}:{3} ({4})".format(
                FAIL, proxy, host, port, e))

    # ── 3. TLS handshake with our configured context ──────────────────────
    tls_ok = False
    # Mirror urllib's routing: when an HTTPS proxy is configured the real
    # heartbeat traffic tunnels through it, so the TLS check must too —
    # a direct handshake could pass while proxied traffic fails on the
    # proxy's re-signed certificate.
    tls_route = proxy
    ctx = _net.build_ssl_context(allow_insecure=True)
    try:
        raw = _open_tcp(host, port, tls_route)
        try:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                issuer = ""
                try:
                    der = tls.getpeercert(True)
                    issuer = issuer_name_from_der(der) if der else ""
                except Exception:
                    pass
        finally:
            try:
                raw.close()
            except Exception:
                pass
        tls_ok = True
        via = " via proxy" if tls_route else ""
        out("{0} TLS{1}: certificate verified (issuer: {2})".format(
            PASS, via, issuer or "unknown"))
        if issuer and classify_issuer(issuer) == "corporate":
            out("       Note: that issuer is not a public CA — your network")
            out("       re-signs HTTPS, but its root CA is trusted here. Good.")
    except Exception as e:
        failures += 1
        out("{0} TLS: handshake failed ({1})".format(FAIL, e))
        # Verification-off retry purely to FETCH the cert and show who signed it.
        issuer = ""
        try:
            der = _fetch_peer_cert_unverified(host, port, tls_route)
            issuer = issuer_name_from_der(der) if der else ""
        except Exception as e2:
            out("       (could not fetch the server certificate either: {0})".format(e2))
        if issuer:
            out("       Certificate issuer chain: " + issuer)
            if classify_issuer(issuer) == "corporate":
                out("")
                for line in _windows_fix_text(issuer).splitlines():
                    out("  " + line)
            else:
                out("       The issuer looks like a public CA — your Python")
                out("       CA bundle may be outdated. Try: pip install -U certifi")

    # ── 4. Heartbeat POST ────────────────────────────────────────────────
    if tls_ok:
        url = "https://{0}:{1}/ingest/heartbeat".format(host, port) \
            if port != 443 else "https://{0}/ingest/heartbeat".format(host)
        req = urllib.request.Request(
            url,
            data=b'{"doctor": true}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            # Global opener installed by configure_outbound_network() — this
            # exercises the exact transport the daemon heartbeat uses.
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                status = getattr(resp, "status", 200)
            out("{0} POST {1} -> HTTP {2}".format(PASS, url, status))
        except urllib.error.HTTPError as e:
            # An HTTP status (even 4xx) means the network path works —
            # the server just rejected our unauthenticated test payload.
            out("{0} POST {1} -> HTTP {2} (transport works; the server".format(
                PASS, url, e.code))
            out("       rejected the unauthenticated test payload, as expected)")
        except Exception as e:
            failures += 1
            out("{0} POST {1} failed ({2})".format(FAIL, url, e))
    else:
        failures += 1
        out("{0} POST skipped — TLS must pass first".format(FAIL))

    out("")
    if failures == 0:
        out("Result: ALL CHECKS PASSED — ClawMetry can reach the cloud.")
        return 0
    out("Result: {0} check(s) FAILED — fix the items above and re-run"
        " `clawmetry doctor`.".format(failures))
    return 1
