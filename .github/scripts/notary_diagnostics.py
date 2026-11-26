"""Collect read-only Notary Service diagnostics with allowlisted output only.

A recognized HTTP rejection is a collected diagnostic result, not a claim that
notarization works. Build/release jobs never use this report as a signing gate.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

EXPECTED_TEAM = "8LVH596RA5"
SECRET_NAMES = ("APPLE_ID", "APPLE_TEAM_ID", "APPLE_APP_SPECIFIC_PASSWORD",
                "MACOS_SIGN_IDENTITY")
MAX_RESPONSE_BYTES = 1024 * 1024


def diagnose(environ, runner=None):
    report = {
        "configuration_complete": all(environ.get(name) for name in SECRET_NAMES),
        "configured_team_matches_expected": False,
        "configured_team_matches_identity_suffix": False,
        "notary_history_accessible": False,
        "http_status": None,
        "submission_count": None,
        "classification": "missing_configuration",
    }
    if not report["configuration_complete"]:
        return report, 1
    values = {name: environ[name] for name in SECRET_NAMES}
    if any("\0" in value or value != value.strip() for value in values.values()):
        report["classification"] = "invalid_configuration"
        return report, 1
    team = values["APPLE_TEAM_ID"]
    identity = re.search(r"\(([A-Z0-9]{10})\)$", values["MACOS_SIGN_IDENTITY"])
    report["configured_team_matches_expected"] = team == EXPECTED_TEAM
    report["configured_team_matches_identity_suffix"] = bool(identity and identity[1] == team)
    if not (report["configured_team_matches_expected"]
            and report["configured_team_matches_identity_suffix"]):
        report["classification"] = "team_configuration_mismatch"
        return report, 1
    command = ["xcrun", "notarytool", "history", "--apple-id", values["APPLE_ID"],
               "--team-id", team, "--password", values["APPLE_APP_SPECIFIC_PASSWORD"],
               "--output-format", "json"]
    runtime_environment = {name: environ[name] for name in ("PATH", "HOME", "TMPDIR", "LANG")
                           if name in environ}
    try:
        result = (runner or subprocess.run)(command, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90,
            env=runtime_environment, check=False)
    except subprocess.TimeoutExpired:
        report["classification"] = "notary_timeout"
        return report, 1
    except (OSError, ValueError):
        # Exception messages and subprocess argv can contain credentials.
        report["classification"] = "notary_invocation_failed"
        return report, 1
    stdout, stderr = result.stdout, result.stderr
    if len(stdout) + len(stderr) > MAX_RESPONSE_BYTES:
        report["classification"] = "response_too_large"
        return report, 1
    if result.returncode:
        text = (stdout + stderr).decode("utf-8", errors="replace")
        match = re.search(r"HTTP status code:\s*(\d{3})", text)
        report["http_status"] = int(match[1]) if match else None
        if "required agreement is missing or has expired" in text.lower():
            report["classification"] = "apple_agreement_gate"
        elif report["http_status"] == 401:
            report["classification"] = "authentication_rejected"
        elif report["http_status"] == 403:
            report["classification"] = "authorization_rejected"
        else:
            report["classification"] = "notary_request_failed"
        return report, 0 if match else 1
    try:
        payload = json.loads(stdout)
    except (ValueError, UnicodeError):
        report["classification"] = "unexpected_response"
        return report, 1
    history = payload.get("history") if isinstance(payload, dict) else None
    if not isinstance(history, list) or not all(isinstance(item, dict) for item in history):
        report["classification"] = "unexpected_response"
        return report, 1
    report.update(notary_history_accessible=True, submission_count=len(history),
                  classification="notary_history_accessible")
    return report, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    report, status = diagnose(os.environ)
    encoded = json.dumps(report, indent=2) + "\n"
    args.report.write_text(encoded)
    print(encoded, end="")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
