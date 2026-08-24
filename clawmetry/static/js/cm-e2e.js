/* cm-e2e.js — everything in the browser that touches your encryption key.
 *
 * WHY THIS FILE EXISTS, AND WHY IT IS HERE
 *
 * ClawMetry says your cloud snapshot is end-to-end encrypted with a key that
 * never leaves your machine. The encryption itself is done by the daemon on
 * your computer and is auditable in this repository. The DECRYPTION happens in
 * your browser, in JavaScript that app.clawmetry.com serves you.
 *
 * An external security review in August 2026 made the obvious point: if the
 * code that receives your key and decrypts your data is written by us, served
 * by us on every page load, and published nowhere, then "end-to-end encrypted"
 * is a promise about our conduct rather than something you can check. Every
 * other part of the claim was verifiable and this part was not.
 *
 * So this file is the whole of it — the code that reads the key out of the URL
 * fragment, decides where to store it, and decrypts blobs with it — and it
 * lives in the public repository, ships inside the versioned wheel on PyPI,
 * and is served verbatim. The hosted dashboard's Flask app points its static
 * folder at the installed package, so the bytes your browser runs are the
 * bytes published under that version. Nothing is minified or bundled, on
 * purpose: a build step would put something between what you can read and what
 * you run.
 *
 * HOW TO CHECK THAT FOR YOURSELF
 *
 *   curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
 *   pip download --no-deps clawmetry==<version> -d /tmp/cm
 *   unzip -p /tmp/cm/clawmetry-<version>-py3-none-any.whl \
 *         clawmetry/static/js/cm-e2e.js > published.js
 *   diff served.js published.js && echo "identical"
 *
 * The page also pins this file with a Subresource Integrity hash, so you can
 * compare the `integrity=` attribute in the page source against
 * `openssl dgst -sha384 -binary published.js | openssl base64 -A`.
 *
 * WHAT THIS DOES NOT PROVE
 *
 * We serve the page that loads this file, so we could serve a different page.
 * SRI protects you from a compromised CDN, not from the vendor. What it buys
 * you is that a substitution has to be deliberate, visible in the page source,
 * and different from a published artifact anyone can fetch — instead of an
 * invisible change to an unpublished blob. If you need a guarantee that does
 * not involve trusting us at all, run local-only or self-host; both remove
 * this file from the picture entirely.
 *
 * THE INVARIANTS THIS FILE KEEPS
 *
 *   1. The key arrives in the URL FRAGMENT. Browsers never transmit a
 *      fragment, so it does not reach our logs, a Referer header, or any
 *      intermediary.
 *   2. The key is removed from the address bar as soon as it is read, so it
 *      does not linger in history or get carried off by browser sync.
 *   3. The key is imported as non-extractable and decrypt-only, so nothing
 *      later in the page can read it back out of the crypto subsystem.
 *   4. The key is never put in a request. Not a body, not a header, not a
 *      query parameter. Search this file for `fetch` and you will find one
 *      call, and it carries the ACCOUNT token, never the encryption key.
 */
(function () {
  'use strict';

  /* base64url -> bytes. Tolerates missing padding, which is how the daemon
   * emits both the key and the blob. */
  function b64url(s) {
    s = String(s || '').replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var bin = atob(s);
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  /* A key is either real AES key material (16/24/32 bytes of base64url) or a
   * passphrase the user typed. A passphrase is hashed to 32 bytes so it can be
   * used as an AES-256 key. This mirrors _derive_key_for_storage on the daemon
   * side; the daemon additionally salts and scrypts a typed passphrase before
   * storing it, so what reaches here is normally already real key material. */
  function normalizeKey(k) {
    try {
      var raw = b64url(k);
      if (raw.byteLength === 16 || raw.byteLength === 24 || raw.byteLength === 32) {
        return Promise.resolve(k);
      }
    } catch (e) { /* not base64 — fall through to hashing */ }
    var enc = new TextEncoder().encode(k);
    return crypto.subtle.digest('SHA-256', enc).then(function (hash) {
      var b = new Uint8Array(hash), s = '';
      for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
      return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    });
  }

  /* Where a node's key lives in localStorage. Namespaced by node AND by the
   * first 16 chars of the account token, so two accounts used in one browser
   * cannot read each other's keys out of shared storage. */
  function storageKeyFor(nodeId, accountToken) {
    var acct = String(accountToken || '').slice(0, 16);
    if (!nodeId || !acct) return null;
    return 'cm-enc-key-' + nodeId + '-' + acct;
  }

  /* AES-256-GCM, nonce = first 12 bytes, matching encrypt_payload in
   * clawmetry/sync.py. importKey is given extractable=false and ['decrypt'],
   * so the key cannot be read back out or used to encrypt anything. Returns
   * null rather than throwing: a blob we cannot read is an empty card, never
   * a broken page. */
  function decryptBlob(blob, keyB64) {
    try {
      return normalizeKey(keyB64).then(function (nk) {
        return crypto.subtle.importKey(
          'raw', b64url(nk), { name: 'AES-GCM' }, false, ['decrypt']
        );
      }).then(function (ck) {
        var raw = b64url(blob);
        return crypto.subtle.decrypt(
          { name: 'AES-GCM', iv: raw.slice(0, 12) }, ck, raw.slice(12)
        );
      }).then(function (pt) {
        return JSON.parse(new TextDecoder().decode(pt));
      }).catch(function () { return null; });
    } catch (e) {
      return Promise.resolve(null);
    }
  }

  /* Read the hand-off out of the URL fragment and clear it.
   *
   * `clawmetry connect` opens:
   *     https://app.clawmetry.com/cloud#token=<account>&key=<enc>&node=<id>
   *
   * Both values are in the fragment. Until August 2026 the account token was
   * in the query string instead, which meant every connect wrote a live
   * account credential into the server's request log and the user's history.
   */
  function consumeFragment() {
    var h = window.location.hash || '';
    if (h.indexOf('key=') < 0 && h.indexOf('token=') < 0) return;

    var hp = new URLSearchParams(h.substring(1));
    var token = hp.get('token') || '';
    var key = hp.get('key') || '';
    var node = hp.get('node') || window.CLOUD_NODE_ID || '';

    if (token && token.indexOf('cm_') === 0) {
      try { localStorage.setItem('clawmetry-token', token); } catch (e) {}
      /* One-step onboarding. The server can no longer see the token in the
       * URL, so it is handed over in a POST body, which is not part of the
       * logged request line. Best effort: the daemon also learns about the
       * claim by polling /api/cloud/claim-status. This is the only request in
       * this file, and it carries the ACCOUNT token, never the encryption
       * key. */
      try {
        fetch('/api/cloud/auto-claim', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: token })
        }).catch(function () {});
      } catch (e) {}
    }

    if (key && node) {
      var resolvedToken = token;
      if (!resolvedToken) {
        resolvedToken = window.CLOUD_TOKEN || '';
        if (!resolvedToken) {
          try { resolvedToken = localStorage.getItem('clawmetry-token') || ''; } catch (e) {}
        }
      }
      var sk = storageKeyFor(node, resolvedToken);
      if (sk) {
        try {
          localStorage.setItem(sk, key);
          localStorage.removeItem('cm-enc-skipped-' + sk);
        } catch (e) {}
      }
    }

    /* Clear the fragment unconditionally, even on a path that stored nothing.
     * A key left in the address bar ends up in history and, when the user has
     * browser sync on, on the vendor's servers. */
    try {
      history.replaceState(null, '', window.location.pathname + window.location.search);
    } catch (e) {}
  }

  window.cmE2E = {
    b64url: b64url,
    normalizeKey: normalizeKey,
    storageKeyFor: storageKeyFor,
    decryptBlob: decryptBlob,
    consumeFragment: consumeFragment
  };

  /* Names the rest of the dashboard already binds to. Kept so this file is
   * the single implementation rather than a second copy of one. */
  window._cmNormKey = normalizeKey;
  window.cmDecryptBlob = decryptBlob;

  consumeFragment();
})();
