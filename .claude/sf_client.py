#!/usr/bin/env python3
"""Minimal 8090 Software Factory external-API client.

Key resolution: SF_API_KEY env var (cloud runs) first, macOS keychain service
'clawmetry-sf-api-key' second (laptop runs). Never passed on the command line.
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import ssl

try:
    import certifi
except ImportError:  # pragma: no cover - cloud images ship a working trust store
    certifi = None

BASE = "https://api.factory.8090.dev/v2/external-api"


def _key():
    """SF_API_KEY env var (cloud) first, macOS keychain (laptop) as fallback.

    Never accept the key on the command line: the auto-mode classifier blocks it
    and it would land in shell history.
    """
    env = os.environ.get("SF_API_KEY")
    if env:
        return env.strip()
    try:
        return subprocess.check_output(
            ["security", "find-generic-password", "-s", "clawmetry-sf-api-key", "-w"],
            text=True,
        ).strip()
    except Exception as exc:
        raise SystemExit(
            "No Software Factory API key. Set SF_API_KEY in the environment, or on "
            "macOS store it as keychain service 'clawmetry-sf-api-key'."
        ) from exc


def call(method, path, body=None, params=None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-API-Key", _key())
    req.add_header("Content-Type", "application/json")
    try:
        ctx = ssl.create_default_context(cafile=certifi.where() if certifi else None)
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode()[:2000]}


if __name__ == "__main__":
    method, path = sys.argv[1], sys.argv[2]
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
    body = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
    print(json.dumps(call(method, path, body, params), indent=2)[:20000])
