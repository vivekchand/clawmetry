"""A release tag must never ship an unsigned desktop artifact.

Signing config is optional for forks, PRs and dev builds. On a `v*.*.*` tag it
is mandatory, because the artifact goes straight to users:

- an unsigned .exe hits the SmartScreen wall, and its unsigned NSIS uninstaller
  stub is blocked by Smart App Control, leaving the app impossible to remove
  from Settings > Apps
- an unsigned .dmg is refused by Gatekeeper outright

Both failure modes are silent in CI: the build goes green and simply omits the
signature. This guard makes that loud instead.

Scope is AUTO-DISCOVERED from the workflow rather than hard-coded, so a new
signing job (or a renamed one) is covered without anyone remembering to edit
this file. FLYWHEEL.md: "prefer guards that AUTO-DISCOVER their scope over
hand-maintained allowlists, which silently drift."
"""

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = (
    pathlib.Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "desktop-artifacts.yml"
)

# A job that hoists signing-secret presence into job-level env is, by this
# repo's own convention, a job that can sign. See the comment in the macOS job:
# `secrets` is illegal in step-level `if:`, so presence checks live in `env:`.
SIGN_FLAG = re.compile(r"^HAS_.*(SIGN|CERT)", re.IGNORECASE)

GUARD_NAME = "Require signing on release tags"


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _signable_jobs(wf):
    out = {}
    for name, cfg in (wf.get("jobs") or {}).items():
        flags = [k for k in (cfg.get("env") or {}) if SIGN_FLAG.match(k)]
        if flags:
            out[name] = (cfg, flags)
    return out


def test_workflow_parses_and_has_signing_jobs():
    """Fail loudly if the convention changes, rather than vacuously passing."""
    jobs = _signable_jobs(_workflow())
    assert jobs, (
        "No job exposes a HAS_*SIGN/CERT env flag. Either signing was removed, "
        "or the convention changed and this guard is now blind. Fix the guard."
    )


def test_every_signable_job_refuses_to_ship_unsigned_on_a_tag():
    for job_name, (cfg, flags) in _signable_jobs(_workflow()).items():
        steps = cfg.get("steps") or []
        guards = [s for s in steps if s.get("name") == GUARD_NAME]
        assert guards, (
            f"job {job_name!r} can sign but has no {GUARD_NAME!r} step, so a "
            f"release tag could ship an unsigned artifact silently"
        )
        guard = guards[0]

        cond = guard.get("if", "")
        assert "refs/tags/v" in cond, (
            f"{job_name}: guard must only fire on release tags, got if: {cond!r}"
        )
        assert any(f"env.{f}" in cond for f in flags), (
            f"{job_name}: guard must test one of {flags} so it actually "
            f"reflects whether signing is configured, got if: {cond!r}"
        )
        assert "exit 1" in (guard.get("run") or ""), (
            f"{job_name}: guard must fail the build, not merely warn"
        )

        # Fail fast: cheaper to catch a misconfiguration in seconds than after
        # a full compile, and it keeps the failure unambiguous.
        idx = steps.index(guard)
        builds = [
            i
            for i, s in enumerate(steps)
            if "build" in (s.get("name") or "").lower()
        ]
        if builds:
            assert idx < min(builds), (
                f"{job_name}: guard must run before the build steps"
            )


def test_windows_verify_asserts_a_countersignature():
    """Signed-but-not-timestamped is a three-day fuse, so assert it explicitly.

    Artifact Signing certificates are valid for three days by design. Without
    an RFC 3161 countersignature a release verifies fine at publish and then
    reads as "unknown publisher" on every user's machine within the week, which
    is worse than unsigned because it looks like tampering.
    """
    win = (_workflow().get("jobs") or {}).get("windows") or {}
    body = "\n".join((s.get("run") or "") for s in (win.get("steps") or []))
    assert "TimeStamperCertificate" in body, (
        "the Windows job must assert the countersignature is present; "
        "signtool's /tw only 'generates a warning' and cannot gate a build"
    )
