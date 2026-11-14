#!/usr/bin/env python3
"""Bridge user bug reports to the public GitHub tracker, and fixes back.

Run by .github/workflows/bug-report-sync.yml on a schedule.

Why a workflow and not a call from the cloud service: filing an issue needs
a credential with write access to this repo. Actions already has one scoped
to exactly this repo for the length of one job (``GITHUB_TOKEN``), so the
alternative -- minting a long-lived PAT and parking it in a web service
that accepts anonymous public POSTs -- buys a few minutes of latency at the
cost of a standing credential. The founder email is sent by the intake the
moment a report lands, so nothing urgent waits on this tick.

Each pass does two things:

  pending  -> file an issue, send the issue number back
  tracking -> report each issue's state back, so an issue closed as
              completed flips the ticket to "fixed" and emails the person
              who reported it

The reporter's email never appears here: the intake does not include it in
the sync payload, and this script never asks for it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API_BASE = os.environ.get("CLAWMETRY_API_BASE", "https://app.clawmetry.com").rstrip("/")
SYNC_URL = API_BASE + "/api/_internal/bug-reports/sync"
TOKEN = os.environ.get("CLAWMETRY_BUGSYNC_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "vivekchand/clawmetry")
DRY_RUN = os.environ.get("DRY_RUN", "").strip().lower() in ("1", "true", "yes")

SEVERITY_LABEL = {
    "blocking": "severity:blocking",
    "major": "severity:major",
    "normal": "severity:normal",
    "minor": "severity:minor",
}


def _request(method: str, url: str, payload: dict = None) -> dict:
    # CLAWMETRY_API_BASE is settable from the workflow env; urlopen honours
    # whatever scheme it is given, so pin it to http(s) before the call.
    if not url.startswith(("https://", "http://")):
        raise ValueError("sync URL must be http(s)")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"X-Internal-Token": TOKEN, "Content-Type": "application/json",
                 "User-Agent": "clawmetry-bug-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310 - scheme checked above
        body = resp.read().decode("utf-8") or "{}"
    parsed = json.loads(body)
    return parsed if isinstance(parsed, dict) else {}


def issue_body(report: dict) -> str:
    """The public issue text.

    Carries what a contributor needs to reproduce, and nothing that
    identifies the person who reported it. The ticket id is the join key
    back to the private row, which is where the email lives.
    """
    env_rows = [
        ("ClawMetry", report.get("version")),
        ("Runtime", report.get("runtime")),
        ("Platform", report.get("platform")),
        ("Python", report.get("python_version")),
        ("Reported from", report.get("source")),
        ("Screen", report.get("surface")),
    ]
    env = "\n".join(f"| {k} | {v} |" for k, v in env_rows if v)
    body = (report.get("body") or "").strip() or "_No further detail given._"
    out = [
        body,
        "",
        f"**How much it is holding them up:** {report.get('severity') or 'normal'}",
        "",
    ]
    if env:
        out += ["<details><summary>Environment</summary>", "",
                "| | |", "|---|---|", env, "", "</details>", ""]
    if report.get("has_screenshot"):
        # Named, never embedded: the image went to us, not to a public tracker.
        out += ["A screenshot came with this report. It is held privately with "
                "the report, not attached here.", ""]
    out += [
        "---",
        f"Reported through the dashboard's Report a bug dialog. Tracking id "
        f"`{report.get('ticket')}`; the reporter is emailed automatically when "
        f"this issue closes, so closing it as completed is the whole workflow.",
    ]
    return "\n".join(out)


def file_issue(report: dict) -> dict:
    """Create the issue with gh and return the update to send back."""
    ticket = report.get("ticket") or ""
    title = (report.get("title") or "").strip()[:140]
    # Must not collide with the auto-close prefixes in close-bot-noise.yml --
    # those exist to keep agent chatter out of the tracker, and a real user's
    # report is the opposite of that.
    subject = f"[{ticket}] {title}"
    labels = ["bug", "user-report"]
    sev = SEVERITY_LABEL.get(report.get("severity") or "")
    if sev:
        labels.append(sev)
    cmd = ["gh", "issue", "create", "--repo", REPO,
           "--title", subject, "--body", issue_body(report)]
    for label in labels:
        cmd += ["--label", label]
    if DRY_RUN:
        print(f"[dry-run] would file: {subject}")
        return {}
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # A missing label is the common cause; retry once with no labels so a
        # label-management detail never blocks a real user's report.
        print(f"[warn] gh issue create failed for {ticket}: {proc.stderr.strip()}")
        proc = subprocess.run(
            ["gh", "issue", "create", "--repo", REPO,
             "--title", subject, "--body", issue_body(report)],
            capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"[error] retry failed for {ticket}: {proc.stderr.strip()}")
            return {}
    url = proc.stdout.strip().splitlines()[-1].strip()
    number = url.rstrip("/").rsplit("/", 1)[-1]
    try:
        number = int(number)
    except ValueError:
        print(f"[error] could not read an issue number from {url!r}")
        return {}
    print(f"[ok] {ticket} -> #{number}")
    return {"ticket": ticket, "issue_number": number,
            "issue_url": url, "state": "open"}


def issue_state(ticket: str, number: int) -> dict:
    proc = subprocess.run(
        ["gh", "issue", "view", str(number), "--repo", REPO,
         "--json", "state,stateReason,url"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[warn] cannot read issue #{number}: {proc.stderr.strip()}")
        return {}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {}
    return {"ticket": ticket,
            "issue_number": number,
            "issue_url": data.get("url") or "",
            "state": (data.get("state") or "").lower(),
            "state_reason": (data.get("stateReason") or "").lower()}


def main() -> int:
    if not TOKEN:
        print("CLAWMETRY_BUGSYNC_TOKEN is not set; nothing to do.")
        return 0
    try:
        work = _request("GET", SYNC_URL)
    except urllib.error.HTTPError as exc:
        print(f"[error] sync pull failed: HTTP {exc.code}")
        return 1
    except Exception as exc:
        print(f"[error] sync pull failed: {exc}")
        return 1

    updates = []
    for report in work.get("pending") or []:
        upd = file_issue(report)
        if upd:
            updates.append(upd)
    for row in work.get("tracking") or []:
        upd = issue_state(row.get("ticket"), row.get("gh_issue_number"))
        if upd:
            updates.append(upd)

    if not updates:
        print("Nothing to sync.")
        return 0
    if DRY_RUN:
        print(json.dumps(updates, indent=2))
        return 0
    try:
        res = _request("POST", SYNC_URL, {"updates": updates})
    except Exception as exc:
        print(f"[error] sync push failed: {exc}")
        return 1
    print(f"Applied {res.get('applied', 0)} update(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
