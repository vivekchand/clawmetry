#!/usr/bin/env python3
"""Detect flaky E2E tests and append them to tests/quarantine.txt.

A test is classified as flaky when:
  - It failed in a recent watched CI run (junit artifact), AND
  - There exists a LATER run for the SAME head commit (SHA) that PASSED.

Failed-then-passed on the same commit == flaky; add to quarantine.txt so
the per-PR gate is not blocked by intermittent failures.

Watched workflows (WATCHED_WORKFLOWS constant):
  - oss-golden-path.yml -- uploads junit-c1c5-{run_id} (C1+C5 gate)
  - ci.yml              -- uploads junit-e2e-critical-{run_id} (e2e-critical job)
  - cross-repo-handoff.yml -- uploads junit-c4-{run_id} (C4 gate)

Usage
-----
  GITHUB_TOKEN=ghp_xxx python3 scripts/auto_quarantine.py
  python3 scripts/auto_quarantine.py --dry-run
  python3 scripts/auto_quarantine.py --lookback 50

Exit codes
----------
  0  No new flaky tests found (or --dry-run mode)
  1  Script error (missing token, API failure, etc.)
  2  New flaky tests written to tests/quarantine.txt (caller should open a PR)

Tracking: vivekchand/clawmetry#3730 (C7)
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

OWNER = os.environ.get("REPO_OWNER", "vivekchand")
REPO = os.environ.get("REPO_NAME", "clawmetry")

# Each entry: (workflow_filename, junit_artifact_name_prefix).
# Artifact for run {run_id} is named "{prefix}-{run_id}".
# C7 requirement: flaky tests in ANY required-check workflow must be
# quarantined within 24h.
WATCHED_WORKFLOWS: list[tuple[str, str]] = [
    # C1+C5 gate: uploads junit-c1c5-{run_id}.
    ("oss-golden-path.yml", "junit-c1c5"),
    # e2e-critical job in ci.yml: uploads junit-e2e-critical-{run_id}.
    # Without this entry, flaky tests in TestTabsLoad / TestAllTabsPostAuth
    # would block PRs without ever reaching quarantine.txt (C7 coverage gap).
    ("ci.yml", "junit-e2e-critical"),
    # C4 cross-repo handoff: uploads junit-c4-{run_id}.
    # T1-T4 (landing signup, cloud boot, daemon pair, first sync event) depend
    # on subprocess startup timing. Watching ensures any flakiness in the startup
    # sequence is quarantined within 24h instead of silently blocking PRs.
    ("cross-repo-handoff.yml", "junit-c4"),
]


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


class _CaptureRedirect(urllib.request.BaseHandler):
    """Capture redirect responses instead of following them.

    GitHub's artifact download endpoint issues a 302 redirect to a presigned
    S3 URL. We must NOT forward our Authorization header to S3 (S3 rejects
    duplicate auth), so we capture the Location and re-fetch without it.
    """

    def http_error_301(self, req, fp, code, msg, headers):  # noqa: PLR0913
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_302(self, req, fp, code, msg, headers):  # noqa: PLR0913
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_303(self, req, fp, code, msg, headers):  # noqa: PLR0913
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_307(self, req, fp, code, msg, headers):  # noqa: PLR0913
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_308(self, req, fp, code, msg, headers):  # noqa: PLR0913
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def _api(path: str, *, token: str) -> dict | list:
    """GET a GitHub API endpoint and return parsed JSON."""
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "clawmetry-auto-quarantine/1.0",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub GET {path} => {exc.code}: {body}") from exc


def _download_zip(artifact_id: int, *, token: str) -> bytes:
    """Download a GitHub artifact ZIP file, following the S3 redirect."""
    url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}"
        f"/actions/artifacts/{artifact_id}/zip"
    )
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "clawmetry-auto-quarantine/1.0",
    }
    req = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(_CaptureRedirect())
    try:
        with opener.open(req) as resp:  # noqa: S310
            return resp.read()  # unlikely -- GitHub always redirects
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            location = exc.headers.get("Location", "")
            if not location:
                raise RuntimeError(
                    f"Redirect from artifacts/{artifact_id}/zip had no Location header"
                ) from exc
            # S3 presigned URL -- no Authorization header needed or wanted
            with urllib.request.urlopen(location) as s3_resp:  # noqa: S310
                return s3_resp.read()
        body = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Download artifact {artifact_id} => {exc.code}: {body}"
        ) from exc


# ---------------------------------------------------------------------------
# JUnit XML parsing
# ---------------------------------------------------------------------------


def _classname_to_file_and_class(classname: str) -> tuple[str, str | None]:
    """Split a JUnit classname into (file_path, class_name_or_None).

    pytest generates classname like:
      "tests.test_e2e_oss_golden_path"            (module-level function)
      "tests.test_e2e_oss_golden_path.TestClass"  (class method)

    Returns:
      file_path: "tests/test_e2e_oss_golden_path.py"
      class_name: "TestClass" or None
    """
    parts = classname.split(".")
    # A trailing PascalCase component is a class name, not a module segment
    if parts and parts[-1] and parts[-1][0].isupper():
        class_name: str | None = parts[-1]
        module_parts = parts[:-1]
    else:
        class_name = None
        module_parts = parts
    file_path = "/".join(module_parts) + ".py"
    return file_path, class_name


def _parse_junit_xml(xml_bytes: bytes) -> set[str]:
    """Return pytest node IDs of all FAILED/ERRORED test cases in a JUnit XML blob."""
    failed: set[str] = set()
    try:
        root = ET.fromstring(xml_bytes)  # noqa: S314
    except ET.ParseError as exc:
        print(f"  WARN: could not parse JUnit XML: {exc}", file=sys.stderr)
        return failed

    # Support both <testsuite> root and <testsuites> wrapper
    suites = (
        [root]
        if root.tag == "testsuite"
        else root.findall("testsuite")
    )
    for suite in suites:
        for tc in suite.findall("testcase"):
            if tc.find("failure") is None and tc.find("error") is None:
                continue  # test passed or was skipped
            classname = tc.get("classname", "")
            name = tc.get("name", "")
            file_path, class_name = _classname_to_file_and_class(classname)
            if class_name:
                node_id = f"{file_path}::{class_name}::{name}"
            else:
                node_id = f"{file_path}::{name}"
            failed.add(node_id)
    return failed


def _extract_junit_from_zip(zip_bytes: bytes) -> set[str]:
    """Extract all JUnit XML files from a zip blob and return all failing test IDs."""
    failed: set[str] = set()
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
            if not xml_names:
                print("  WARN: artifact ZIP contains no XML files", file=sys.stderr)
                return failed
            for xml_name in xml_names:
                xml_data = zf.read(xml_name)
                failed |= _parse_junit_xml(xml_data)
    except zipfile.BadZipFile as exc:
        print(f"  WARN: artifact is not a valid ZIP: {exc}", file=sys.stderr)
    return failed


# ---------------------------------------------------------------------------
# Core flakiness detection
# ---------------------------------------------------------------------------


def _get_workflow_id(workflow_file: str, token: str) -> int:
    """Return the numeric workflow ID for workflow_file."""
    data = _api(f"/repos/{OWNER}/{REPO}/actions/workflows", token=token)
    for wf in data.get("workflows", []):
        if workflow_file in wf.get("path", ""):
            return int(wf["id"])
    raise RuntimeError(
        f"Workflow {workflow_file!r} not found in {OWNER}/{REPO}. "
        "Check that the workflow file exists and REPO_OWNER/REPO_NAME are correct."
    )


def _get_runs(workflow_id: int, lookback: int, token: str) -> list[dict]:
    """Return the N most recent completed workflow runs, newest first."""
    data = _api(
        f"/repos/{OWNER}/{REPO}/actions/workflows/{workflow_id}/runs"
        f"?per_page={lookback}&status=completed",
        token=token,
    )
    return data.get("workflow_runs", [])


def _find_artifact_id(run_id: int, artifact_prefix: str, token: str) -> int | None:
    """Return the artifact ID for {artifact_prefix}-{run_id}, or None."""
    data = _api(
        f"/repos/{OWNER}/{REPO}/actions/runs/{run_id}/artifacts",
        token=token,
    )
    target = f"{artifact_prefix}-{run_id}"
    for art in data.get("artifacts", []):
        if art.get("name", "") == target:
            return int(art["id"])
    return None


def _detect_flaky_in_workflow(
    workflow_file: str,
    artifact_prefix: str,
    lookback: int,
    token: str,
) -> set[str]:
    """Detect flaky tests in a single workflow.

    A test is flaky when it failed in one run then passed on a re-run of the
    same commit (same head_sha, higher run_number).
    """
    print(f"Scanning {lookback} recent runs of {workflow_file} in {OWNER}/{REPO} ...")
    try:
        workflow_id = _get_workflow_id(workflow_file, token)
    except RuntimeError as exc:
        print(f"  WARN: {exc} -- skipping {workflow_file}")
        return set()

    runs = _get_runs(workflow_id, lookback, token)
    print(f"  Fetched {len(runs)} completed run(s).")

    if not runs:
        print("  No completed runs found.")
        return set()

    # Index: sha -> list of (run_number, conclusion)
    sha_runs: dict[str, list[tuple[int, str]]] = {}
    for run in runs:
        sha = run.get("head_sha", "")
        num = run.get("run_number", 0)
        conclusion = run.get("conclusion") or ""
        if sha:
            sha_runs.setdefault(sha, []).append((num, conclusion))

    # Sort each SHA's runs by run_number ascending so "later" means higher number
    for sha in sha_runs:
        sha_runs[sha].sort(key=lambda t: t[0])

    flaky_tests: set[str] = set()

    failed_runs = [r for r in runs if r.get("conclusion") == "failure"]
    print(f"  Found {len(failed_runs)} failed run(s) to inspect.")

    for run in failed_runs:
        run_id = run["id"]
        run_num = run.get("run_number", 0)
        sha = run.get("head_sha", "")

        # Is there a later run for the same SHA that passed?
        later_passed = any(
            num > run_num and conc == "success"
            for num, conc in sha_runs.get(sha, [])
        )
        if not later_passed:
            print(
                f"  Run #{run_num} (id={run_id}, sha={sha[:8]}): "
                "failed, no later pass -- not classified as flaky"
            )
            continue

        print(
            f"  Run #{run_num} (id={run_id}, sha={sha[:8]}): "
            "failed then passed on re-run -> checking JUnit XML"
        )

        artifact_id = _find_artifact_id(run_id, artifact_prefix, token)
        if artifact_id is None:
            print(
                f"    No {artifact_prefix}-{run_id} artifact found "
                "(run may predate JUnit XML upload step)"
            )
            continue

        try:
            zip_bytes = _download_zip(artifact_id, token=token)
        except RuntimeError as exc:
            print(f"    WARN: could not download artifact {artifact_id}: {exc}")
            continue

        failing = _extract_junit_from_zip(zip_bytes)
        if failing:
            print(f"    Flaky tests found ({len(failing)}): {sorted(failing)}")
            flaky_tests |= failing
        else:
            print("    No failing tests in JUnit XML (or no XML in artifact)")

    return flaky_tests


def detect_flaky_tests(lookback: int, token: str) -> set[str]:
    """Return the set of test node IDs that appear to be flaky.

    Scans every workflow in WATCHED_WORKFLOWS. A test is flaky when it
    failed in a workflow run then passed on a later re-run of the same
    commit.
    """
    all_flaky: set[str] = set()
    for workflow_file, artifact_prefix in WATCHED_WORKFLOWS:
        all_flaky |= _detect_flaky_in_workflow(
            workflow_file, artifact_prefix, lookback, token
        )
    return all_flaky


# ---------------------------------------------------------------------------
# quarantine.txt helpers
# ---------------------------------------------------------------------------


def _quarantine_path() -> str:
    """Return the absolute path to tests/quarantine.txt."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "tests", "quarantine.txt"))


def _read_quarantine(path: str) -> tuple[str, set[str]]:
    """Return (raw_content, set_of_test_ids) from quarantine.txt."""
    try:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        return "", set()

    existing: set[str] = set()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing.add(stripped)
    return content, existing


def _write_quarantine(path: str, existing_content: str, new_tests: set[str]) -> None:
    """Append new_tests to quarantine.txt with an auto-quarantine comment."""
    today = datetime.date.today().isoformat()
    lines_to_add = [
        f"# Auto-quarantined by auto_quarantine.py on {today}: "
        "failed then passed on re-run",
    ]
    for tid in sorted(new_tests):
        lines_to_add.append(tid)

    # Ensure existing content ends with exactly one newline before appending
    content = existing_content.rstrip("\n") + "\n"
    content += "\n".join(lines_to_add) + "\n"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Detect flaky E2E tests (failed then passed on re-run) and "
            "append them to tests/quarantine.txt."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be quarantined but do not write quarantine.txt",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=30,
        metavar="N",
        help="Number of recent workflow runs to scan per workflow (default: 30)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print(
            "Error: GITHUB_TOKEN is not set.\n"
            "Set it before running:\n"
            "  export GITHUB_TOKEN=ghp_xxx\n"
            "  python3 scripts/auto_quarantine.py --dry-run",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        flaky = detect_flaky_tests(args.lookback, token)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    quarantine_file = _quarantine_path()
    existing_content, existing_ids = _read_quarantine(quarantine_file)
    new_flaky = flaky - existing_ids

    if not new_flaky:
        msg = (
            f"Scanning {args.lookback} runs per workflow... 0 new flaky tests found"
            + (" (dry run)." if args.dry_run else ". quarantine.txt unchanged.")
        )
        print(msg)
        sys.exit(0)

    print(f"\n{len(new_flaky)} new flaky test(s) detected:")
    for tid in sorted(new_flaky):
        print(f"  {tid}")

    if args.dry_run:
        print(
            f"\n--dry-run: would add {len(new_flaky)} test(s) to {quarantine_file}"
        )
        print(
            f"Scanning {args.lookback} runs per workflow... "
            f"{len(new_flaky)} new flaky tests found (dry run)."
        )
        sys.exit(0)

    _write_quarantine(quarantine_file, existing_content, new_flaky)
    print(f"\nWrote {len(new_flaky)} new test(s) to {quarantine_file}")
    sys.exit(2)


if __name__ == "__main__":
    main()
