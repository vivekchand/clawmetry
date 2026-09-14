"""``clawmetry trace report``: agent-session provenance for a change.

REQ-OBS-PRP-001 (Software Factory requirement 4e224b46-71a6-4d32-933d-7fb6bfde30d0),
vivekchand/clawmetry#5946. The logic lives in :mod:`clawmetry.pr_provenance`;
this module is only the command line around it.

Usage::

    clawmetry trace report [--repo PATH] [--base SHA] [--head SHA]
        [--bundle FILE | --export-bundle FILE]
        [--scanner-sarif FILE ...] [--sarif-out FILE] [--markdown-out FILE] [--json-out FILE]
        [--fail-on warning|critical --on-missing-evidence fail|pass]
        [--max-evidence-age-hours N] [--exceptions FILE] [--actor NAME] [--comment-pr N]

Two sources of evidence. On the machine the agent ran on, the report reads
the local store and ``--export-bundle`` writes what it found. On a CI runner,
which has no store, ``--bundle`` reads that file with no store and no network.

The gate is off unless ``--fail-on`` is given, and refuses to run without an
explicit ``--on-missing-evidence``. Exit codes: 0 report written (gate passed
or off), 1 gate failed, 2 usage or configuration error.

Nothing a session was asked, and no tool output, is ever written. Stdlib-only,
like the rest of ``clawmetry trace``, so it runs from the CLI fast path
without the dashboard import.
"""
from __future__ import annotations

import argparse
import json
import os

from clawmetry import pr_provenance as pp


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="clawmetry trace report",
        description=("Link a change's files to the agent sessions that wrote them, as "
                     "SARIF and markdown. The gate is off unless --fail-on is given."))
    ap.add_argument("--repo", default=None, help="repository (default: current directory)")
    ap.add_argument("--base", default=None,
                    help="base commit (default: merge base with the remote's default branch)")
    ap.add_argument("--head", default="HEAD", help="head commit (default: HEAD)")
    ap.add_argument("--bundle", metavar="FILE",
                    help="read an exported provenance bundle instead of the local store")
    ap.add_argument("--export-bundle", metavar="FILE",
                    help="write the provenance bundle for a CI runner to read")
    ap.add_argument("--scanner-sarif", action="append", default=[], metavar="FILE",
                    help="SARIF from an existing scanner to annotate (repeatable)")
    ap.add_argument("--sarif-out", metavar="FILE")
    ap.add_argument("--markdown-out", metavar="FILE")
    ap.add_argument("--json-out", metavar="FILE")
    ap.add_argument("--fail-on", choices=pp.GATE_THRESHOLDS, default=None,
                    help="enable the gate at this severity")
    ap.add_argument("--on-missing-evidence", choices=pp.EVIDENCE_BEHAVIOURS, default=None,
                    help="required with --fail-on: what missing/stale/invalid evidence does")
    ap.add_argument("--max-evidence-age-hours", type=float, default=None)
    ap.add_argument("--exceptions", metavar="FILE", help="JSON file of approved exceptions")
    ap.add_argument("--actor", default=None,
                    help="who ran the gate (default: GITHUB_ACTOR / BUILD_REQUESTEDFOR)")
    ap.add_argument("--comment-pr", metavar="N", type=int, default=None,
                    help="post or update one comment on this GitHub pull request")
    return ap


def _read_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"Cannot read {what} {path}: {exc}")
        return None


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _from_bundle(args, repo, commits, changed, base_sha, head_sha):
    # A bundle committed inside the change is not itself agent work, and the
    # commit that adds it cannot be covered by the bundle it adds.
    rel = pp.repo_relative(os.path.abspath(args.bundle), repo)
    ignored = [c["sha"] for c in commits if rel and c["files"] and set(c["files"]) <= {rel}]
    changed = [p for p in changed if p != rel]
    raw = _read_json(args.bundle, "provenance bundle")
    evidence = pp.assess_evidence(
        raw if raw is not None else {"kind": "unreadable"},
        range_shas=[c["sha"] for c in commits], head_sha=head_sha,
        max_age_hours=args.max_evidence_age_hours, ignored_shas=ignored)
    evidence["source"] = "bundle"
    # Invalid evidence contributes nothing: its links cannot be trusted.
    trusted = raw if evidence["status"] != pp.EVIDENCE_INVALID else {}
    view = dict(trusted or {})
    view["links"] = {p: list((view.get("links") or {}).get(p) or []) for p in changed}
    view.setdefault("sessions", [])
    view.setdefault("base_sha", base_sha)
    view.setdefault("head_sha", head_sha)
    return view, evidence


def _from_store(args, repo, commits, changed, base_sha, head_sha):
    evidence = {"status": pp.EVIDENCE_OK, "reason": "", "source": "store",
                "covered": len(commits), "uncovered": [], "head_sha": head_sha}
    try:
        from clawmetry.cli_cmds._common import get_read_store
        store, source = get_read_store()
    except Exception as exc:
        store, source = None, ""
        evidence.update(status=pp.EVIDENCE_MISSING, source="none",
                        reason=f"no provenance bundle and the local store is unavailable ({exc})")
    if store is not None:
        links, meta, incidents = pp.collect_from_store(
            store, repo=repo, commits=commits, changed_files=changed)
        evidence["source"] = f"store ({source})"
    else:
        links, meta, incidents = {p: [] for p in changed}, {}, {}
    view = pp.build_bundle(
        project=pp.git_project(repo), base_sha=base_sha, head_sha=head_sha, commits=commits,
        changed_files=changed, links=links, sessions=meta, incidents_by_session=incidents,
        generated_by=os.environ.get("USER") or "")
    return view, evidence, store is not None


def report_main(rest) -> int:
    try:
        args = _parser().parse_args(rest)
    except SystemExit as exc:
        return 0 if not exc.code else 2

    if args.bundle and args.export_bundle:
        print("--bundle and --export-bundle are mutually exclusive: export reads the local store.")
        return 2
    if args.on_missing_evidence and not args.fail_on:
        print("--on-missing-evidence only applies to an enabled gate; add --fail-on.")
        return 2

    repo = os.path.abspath(args.repo or os.getcwd())
    head_sha = pp.git_rev_parse(repo, args.head)
    if not head_sha:
        print(f"Not a git repository, or no commit {args.head!r}: {repo}")
        return 2
    base = args.base
    if not base:
        ref = pp.git_default_base_ref(repo)
        base = pp.git_merge_base(repo, ref, head_sha) if ref else ""
        if not base:
            print("Could not work out the base commit; pass --base <sha>.")
            return 2
    base_sha = pp.git_rev_parse(repo, base)
    if not base_sha:
        print(f"No commit {base!r} in {repo}.")
        return 2
    if base_sha == head_sha and not args.base:
        # On the default branch itself the inferred change is empty, and an
        # empty change "passes" everything. Say so instead of reporting it.
        print("Nothing to report: the inferred base is the head commit (this checkout is on "
              "the default branch). Pass --base <sha> for the change you mean.")
        return 2

    commits = pp.git_commits(repo, base_sha, head_sha)
    changed = pp.git_changed_files(repo, base_sha, head_sha)

    if args.bundle:
        view, evidence = _from_bundle(args, repo, commits, changed, base_sha, head_sha)
    else:
        view, evidence, have_store = _from_store(args, repo, commits, changed, base_sha, head_sha)
        if args.export_bundle:
            if not have_store:
                print("Not exporting: the local store is unavailable, so the bundle would "
                      "claim no agent touched this change.")
                return 2
            _write(args.export_bundle, json.dumps(view, indent=2, sort_keys=True) + "\n")

    scanner_docs = []
    for path in args.scanner_sarif:
        doc = _read_json(path, "scanner SARIF")
        if not isinstance(doc, dict):
            return 2
        scanner_docs.append(doc)
    runs, annotated = pp.annotate_scanner_runs(scanner_docs, view, repo)

    exceptions = []
    if args.exceptions:
        doc = _read_json(args.exceptions, "exceptions file")
        if doc is None:
            return 2
        exceptions = pp.load_exceptions(doc)

    actor = (args.actor or os.environ.get("GITHUB_ACTOR")
             or os.environ.get("BUILD_REQUESTEDFOR") or "")
    try:
        decision = pp.evaluate_gate(
            bundle=view, evidence=evidence, annotated=annotated, fail_on=args.fail_on,
            on_missing_evidence=args.on_missing_evidence, exceptions=exceptions, actor=actor)
    except pp.GateConfigError as exc:
        print(f"Gate not evaluated: {exc}")
        return 2

    sarif = pp.to_sarif(view, runs)
    sarif["runs"][0]["properties"]["clawmetry"].update(
        {"evidence": {k: v for k, v in evidence.items() if k != "digest_note"}, "gate": decision})
    markdown = pp.render_markdown(view, evidence, decision, annotated)

    if args.sarif_out:
        _write(args.sarif_out, json.dumps(sarif, indent=2) + "\n")
    if args.markdown_out:
        _write(args.markdown_out, markdown + "\n")
    if args.json_out:
        _write(args.json_out, json.dumps({
            "rule_version": pp.RULE_VERSION, "evidence": evidence, "gate": decision,
            "links": view.get("links"), "sessions": view.get("sessions"),
            "scanner_findings_on_linked_files": annotated,
        }, indent=2, default=str) + "\n")

    linked = sum(1 for r in (view.get("links") or {}).values() if r)
    print(f"  change      {base_sha[:9]}..{head_sha[:9]}  ({len(commits)} commits, "
          f"{len(view.get('links') or {})} files)")
    print(f"  evidence    {evidence['status']} from {evidence.get('source')}"
          + (f"  ({evidence['reason']})" if evidence.get("reason") else ""))
    print(f"  linked      {linked} file(s) to {len(view.get('sessions') or [])} session(s); "
          "association, not proof of cause")
    if scanner_docs:
        print(f"  scanners    {len(annotated)} finding(s) on agent-linked files")
    if args.export_bundle:
        print(f"  bundle      {args.export_bundle}  ({view['digest']})")
        print(f"              {pp.DIGEST_NOTE}")
    if decision["enabled"]:
        print(f"  gate        {decision['outcome'].upper()} at {decision['threshold']}; "
              f"{len(decision['blocking'])} blocking, "
              f"{len(decision['exceptions_applied'])} exception(s) applied, "
              f"{len(decision['exceptions_expired'])} expired; actor {decision['actor']}")
        for reason in decision["reasons"]:
            print(f"              {reason}")
    else:
        print("  gate        not enabled (report only)")

    if args.comment_pr:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        repository = os.environ.get("GITHUB_REPOSITORY") or ""
        if not token or not repository:
            print("  comment     NOT posted: GITHUB_TOKEN and GITHUB_REPOSITORY are required")
        else:
            res = pp.upsert_pr_comment(
                repository=repository, pr_number=args.comment_pr, token=token, body=markdown,
                api_url=os.environ.get("GITHUB_API_URL") or "https://api.github.com")
            state = res.get("action") if res.get("ok") else f"NOT posted: {res.get('error')}"
            print(f"  comment     {state}")

    return 1 if decision["outcome"] == "fail" else 0
