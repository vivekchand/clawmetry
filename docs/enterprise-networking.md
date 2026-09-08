# Enterprise Networking: Corporate Proxies & TLS Interception

If ClawMetry works at home but on a corporate machine the daemon logs
something like:

```
WARNING Heartbeat failed: network error POSTing
https://ingest.clawmetry.com/ingest/heartbeat: <urlopen error
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
CA cert does not include key usage extension (_ssl.c:1032)>
```

this page is for you. **Start with:**

```
clawmetry doctor
```

It checks DNS → TCP → proxy → TLS → a heartbeat POST, prints pass/fail per
step in plain language, and — when your network re-signs HTTPS — tells you
exactly which certificate authority is doing it and how to fix it. Exit
code is 0 only when everything passes, so it also works in scripts.

## What is TLS interception?

Many companies route all HTTPS traffic through a security proxy (Zscaler,
Netskope, Palo Alto, Forcepoint, Fortinet, …). The proxy decrypts your
traffic for inspection and re-encrypts it with a certificate signed by the
**company's own root CA** instead of a public one. That root CA is
installed in the operating system's trust store by your IT team — but:

1. Python does not always use the OS trust store, so the corporate CA
   looks untrusted, and
2. Python 3.13 turned on strict X.509 validation
   (`VERIFY_X509_STRICT`) by default, which rejects many corporate CAs
   outright because they lack the `keyUsage` extension.

Either one produces `CERTIFICATE_VERIFY_FAILED`.

## What ClawMetry does automatically

Since this release, the daemon, the CLI, and the dashboard all run a TLS
bootstrap at startup (`clawmetry/net.py`):

* **OS trust store** — via the [`truststore`](https://pypi.org/project/truststore/)
  package (installed automatically on Python 3.10+), certificate validation
  uses the Windows certificate store / macOS Keychain / Linux CA directory.
  If IT already pushed the corporate root CA to your machine (they almost
  always have), things just work. On Python 3.8/3.9, or if injection
  fails, ClawMetry logs a line and falls back to Python's default trust.
* **Relaxed strict validation** — `VERIFY_X509_STRICT` is cleared on the
  contexts ClawMetry creates. Certificate **verification itself stays on**:
  hostname checking and chain validation are untouched.
* **Proxy environment variables** — `HTTPS_PROXY`, `HTTP_PROXY`, and
  `NO_PROXY` are honored by every outbound call, and re-read at **daemon**
  start (the daemon is launched by launchd/systemd/Task Scheduler, not
  your shell, so it can't assume it inherited them).

## Custom CA bundle

If the OS trust store doesn't have your corporate root CA, point ClawMetry
at a PEM file. It is loaded **in addition to** the normal trust store:

* `CLAWMETRY_CA_BUNDLE=/path/to/corp-root.pem` (env var — wins), or
* `"ca_bundle": "/path/to/corp-root.pem"` in `~/.clawmetry/config.json`.

The standard `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` env vars are also
honored if already set (precedence: `CLAWMETRY_CA_BUNDLE` > config
`ca_bundle` > `SSL_CERT_FILE` > `REQUESTS_CA_BUNDLE`).

### Windows walkthrough: exporting the corporate root CA

1. Press <kbd>Win</kbd>+<kbd>R</kbd>, type `certmgr.msc`, press Enter.
2. Open **Trusted Root Certification Authorities → Certificates**.
3. Find your company's root CA. It is usually named after your company or
   the proxy vendor — `clawmetry doctor` prints the exact issuer name to
   look for.
4. Right-click it → **All Tasks → Export…** → choose
   **"Base-64 encoded X.509 (.CER)"** → save it, e.g. `C:\corp-root.cer`.
5. Set the env var (persistently) and restart the daemon:

   ```bat
   setx CLAWMETRY_CA_BUNDLE C:\corp-root.cer
   clawmetry sync restart
   ```

6. Verify: `clawmetry doctor` should now show all checks green.

On Python 3.10+ with `truststore` active this is usually unnecessary —
step 0 is simply `pip install --upgrade clawmetry` and re-running doctor.

## Proxy configuration

If your network requires an explicit proxy (doctor's "TCP: direct
connection failed" + no `HTTPS_PROXY` hint), ask IT for the proxy address
and set:

```bat
:: Windows (persistent)
setx HTTPS_PROXY http://proxy.corp.example:8080
setx NO_PROXY localhost,127.0.0.1
```

```bash
# macOS / Linux
export HTTPS_PROXY=http://proxy.corp.example:8080
export NO_PROXY=localhost,127.0.0.1
```

Then restart the daemon (`clawmetry sync restart`) — the daemon reads
these at its own startup, so a var set only in your terminal session won't
reach an already-running daemon.

## Last resort: disabling TLS verification

For a time-boxed pilot where the root CA can't be exported yet:

* `CLAWMETRY_TLS_NO_VERIFY=1` (env), or
* `"tls_verify": false` in `~/.clawmetry/config.json`.

This disables certificate verification entirely — traffic to
clawmetry.com can be read or tampered with by anyone on the network path.
The daemon logs a loud warning on every start while it's active. Use the
CA-bundle route above instead as soon as possible.

## Quick reference

| Setting | Where | Effect |
|---|---|---|
| `clawmetry doctor` | CLI | Diagnose DNS/TCP/proxy/TLS/heartbeat, detect interception |
| `CLAWMETRY_CA_BUNDLE` | env | Extra PEM CA bundle (highest precedence) |
| `ca_bundle` | `~/.clawmetry/config.json` | Extra PEM CA bundle |
| `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` | env | Honored if already set |
| `HTTPS_PROXY` / `HTTP_PROXY` / `NO_PROXY` | env | Outbound proxy routing |
| `CLAWMETRY_TLS_NO_VERIFY=1` / `tls_verify: false` | env / config | **Insecure** — disable verification (pilot only) |
