"""8090 Software Factory external-API client — read/write blueprints & requirements.

Auth: X-API-Key header. Key from macOS keychain.
Base URL: https://api.factory.8090.dev/v2/external-api
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import requests

BASE = "https://api.factory.8090.dev/v2/external-api"


def _key() -> str:
    """Fetch the external API key from macOS keychain (never echoed)."""
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", "clawmetry-sf-api-key", "-w"],
        text=True,
    ).strip()


def _h():
    return {"X-API-Key": _key(), "Accept": "application/json"}


def health():
    r = requests.get(f"{BASE}/health", headers=_h(), timeout=10)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


def get_blueprint(bp_id: str) -> dict:
    r = requests.get(f"{BASE}/blueprints/{bp_id}", headers=_h(), timeout=15)
    r.raise_for_status()
    return r.json()


def patch_blueprint(bp_id: str, markdown_content: str, force_new_version: bool = True) -> dict:
    r = requests.patch(
        f"{BASE}/blueprints/{bp_id}",
        headers={**_h(), "Content-Type": "application/json"},
        json={"markdown_content": markdown_content, "force_new_version": force_new_version},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def list_blueprints() -> dict:
    r = requests.get(f"{BASE}/blueprints", headers=_h(), timeout=15)
    r.raise_for_status()
    return r.json()


def get_requirement(req_id: str) -> dict:
    r = requests.get(f"{BASE}/requirements/{req_id}", headers=_h(), timeout=15)
    r.raise_for_status()
    return r.json()


def patch_requirement(req_id: str, markdown_content: str, force_new_version: bool = True) -> dict:
    r = requests.patch(
        f"{BASE}/requirements/{req_id}",
        headers={**_h(), "Content-Type": "application/json"},
        json={"markdown_content": markdown_content, "force_new_version": force_new_version},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def create_requirement(payload: dict) -> dict:
    r = requests.post(
        f"{BASE}/requirements",
        headers={**_h(), "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "health"
    if action == "health":
        code, body = health()
        print(f"HTTP {code}")
        print(json.dumps(body, indent=2) if isinstance(body, dict) else body)
    elif action == "get-bp":
        bp_id = sys.argv[2]
        d = get_blueprint(bp_id)
        env = d.get("blueprint") if isinstance(d, dict) else None
        if env:
            md = env.get("markdown_content") or env.get("content") or ""
            print(f"blueprint: id={env.get('id')} title={env.get('title') or env.get('name')}")
            print(f"markdown length: {len(md)}")
            print("--- first 400 chars ---")
            print(md[:400])
        else:
            print(json.dumps(d, indent=2)[:2000])
    elif action == "get-bp-full":
        bp_id = sys.argv[2]
        print(json.dumps(get_blueprint(bp_id), indent=2))
