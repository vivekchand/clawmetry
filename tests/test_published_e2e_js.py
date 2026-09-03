"""The browser-side decrypt path is published, and it really works.

The August 2026 security review's finding 9 was that the JavaScript which
receives the encryption key and decrypts the snapshot is served by
app.clawmetry.com and published nowhere, so "end-to-end encrypted" rested on
trusting vendor conduct rather than on anything a user could check.

``clawmetry/static/js/cm-e2e.js`` is the answer: it holds every line in the
browser that touches the key, it ships in the wheel, and the hosted dashboard
serves it from the installed package.

The test that matters here is `test_published_js_decrypts_real_daemon_output`.
It encrypts with the real `encrypt_payload` the daemon uses and decrypts with
the real published JavaScript under node. Asserting the file merely *contains*
"AES-GCM" would pass against a file that cannot decrypt anything.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry.sync import encrypt_payload, generate_encryption_key  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E2E_JS = os.path.join(REPO, "clawmetry", "static", "js", "cm-e2e.js")

_BROWSER_SHIMS = """
const { webcrypto } = require('crypto');
globalThis.crypto = webcrypto;
globalThis.atob = s => Buffer.from(s, 'base64').toString('binary');
globalThis.btoa = s => Buffer.from(s, 'binary').toString('base64');
globalThis.TextEncoder = require('util').TextEncoder;
globalThis.TextDecoder = require('util').TextDecoder;
globalThis.localStorage = { store:{},
  getItem(k){return this.store[k]||null;},
  setItem(k,v){this.store[k]=v;},
  removeItem(k){delete this.store[k];} };
globalThis.window = globalThis;
globalThis.history = { calls: [], replaceState(a,b,url){ this.calls.push(url); } };
globalThis.location = { hash:'', pathname:'/cloud', search:'' };
globalThis.fetch = (url, opts) => { globalThis.__fetches.push([url, opts]); return Promise.resolve({}); };
globalThis.__fetches = [];
"""


def _node(script_body, location_hash=""):
    """Run the published file under node with browser shims and return stdout."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    js = open(E2E_JS, encoding="utf-8").read()
    prog = (
        _BROWSER_SHIMS
        + f"globalThis.location.hash = {json.dumps(location_hash)};\n"
        + js
        + "\n"
        + script_body
    )
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(prog)
        path = fh.name
    try:
        r = subprocess.run(["node", path], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"node failed: {r.stderr[:600]}"
        return r.stdout.strip()
    finally:
        os.unlink(path)


def test_the_published_file_exists_and_is_not_bundled():
    assert os.path.exists(E2E_JS), "the published decrypt path is missing"
    src = open(E2E_JS, encoding="utf-8").read()
    assert len(src) > 2000, "suspiciously small — is this a stub?"
    # A minified or bundled file cannot be audited by the person relying on it.
    longest = max(len(line) for line in src.splitlines())
    assert longest < 400, (
        f"a {longest}-char line suggests minification; this file must stay readable"
    )


def test_published_js_decrypts_real_daemon_output():
    """The whole point: our encrypt, their decrypt, real crypto both sides."""
    key = generate_encryption_key()
    payload = {
        "display_name": "Reset the prod database password",
        "events": [{"id": "ev-1", "tool": "Bash"}],
        "n": 42,
    }
    blob = encrypt_payload(payload, key)
    out = _node(
        f"window.cmE2E.decryptBlob({json.dumps(blob)}, {json.dumps(key)})"
        f".then(r => console.log(JSON.stringify(r)));"
    )
    assert json.loads(out) == payload


def test_a_wrong_key_returns_null_rather_than_throwing():
    """An unreadable blob is an empty card, never a broken page."""
    blob = encrypt_payload({"x": 1}, generate_encryption_key())
    out = _node(
        f"window.cmE2E.decryptBlob({json.dumps(blob)}, "
        f"{json.dumps(generate_encryption_key())})"
        f".then(r => console.log(JSON.stringify(r)));"
    )
    assert out == "null"


def test_the_key_is_imported_non_extractable_and_decrypt_only():
    src = open(E2E_JS, encoding="utf-8").read()
    assert "'raw', b64url(nk), { name: 'AES-GCM' }, false, ['decrypt']" in src, (
        "importKey must stay extractable=false with ['decrypt'] only, so nothing "
        "later in the page can read the key back out or encrypt with it"
    )


def test_the_encryption_key_is_never_put_in_a_request():
    """One fetch in the file, and it must not carry the key."""
    key = "SECRETKEYVALUE1234567890"
    token = "cm_acct_abcdef123456"
    out = _node(
        "console.log(JSON.stringify(globalThis.__fetches));",
        location_hash=f"#token={token}&key={key}&node=mac",
    )
    fetches = json.loads(out)
    assert len(fetches) == 1, f"expected exactly one request, got {fetches}"
    url, opts = fetches[0]
    blob = json.dumps([url, opts])
    assert key not in blob, "the encryption key reached a request"
    assert token in blob, "the account token is what the claim call carries"
    assert url == "/api/cloud/auto-claim"


def test_the_fragment_is_cleared_from_the_address_bar():
    """A key left in the URL lands in history and in browser sync."""
    out = _node(
        "console.log(JSON.stringify(globalThis.history.calls));",
        location_hash="#token=cm_acct_abcdef123456&key=SECRETKEY123456&node=mac",
    )
    calls = json.loads(out)
    assert calls, "consumeFragment never cleared the fragment"
    for url in calls:
        assert "key=" not in (url or ""), f"the key survived in the URL: {url}"
        assert "token=" not in (url or ""), f"the token survived in the URL: {url}"


def test_the_key_is_stored_namespaced_by_account():
    """Two accounts in one browser must not read each other's keys."""
    out = _node(
        "console.log(JSON.stringify(Object.keys(globalThis.localStorage.store)));",
        location_hash="#token=cm_acct_abcdef123456&key=SECRETKEY123456&node=mac",
    )
    keys = json.loads(out)
    assert any(k.startswith("cm-enc-key-mac-cm_acct_abcdef") for k in keys), keys


def test_storage_key_requires_both_node_and_account():
    out = _node(
        "console.log(JSON.stringify([window.cmE2E.storageKeyFor('', 'cm_x'),"
        " window.cmE2E.storageKeyFor('mac', ''),"
        " window.cmE2E.storageKeyFor('mac', 'cm_acct_abcdef123456')]));"
    )
    a, b, c = json.loads(out)
    assert a is None and b is None
    # slice(0, 16) of the account token — the namespace, not the whole key
    assert c == "cm-enc-key-mac-cm_acct_abcdef12"


def test_published_js_inflates_a_gzip_blob():
    """The daemon gzips large blobs before encrypting them once the server
    advertises the codec; the published decryptor must read both forms."""
    key = generate_encryption_key()
    payload = {"rows": [{"i": i, "line": "same transcript line " * 6} for i in range(300)]}
    blob = encrypt_payload(payload, key, compress=True)
    plain_blob = encrypt_payload(payload, key, compress=False)
    assert len(blob) < len(plain_blob) / 3
    out = _node(
        f"window.cmE2E.decryptBlob({json.dumps(blob)}, {json.dumps(key)})"
        f".then(r => console.log(JSON.stringify(r)));"
    )
    assert json.loads(out) == payload
