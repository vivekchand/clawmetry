"""The pin PR must name the routes a release adds.

**Why this exists.** clawmetry-cloud's enforcer refuses to boot when an
installed OSS route has no ``cloud_route_policy`` entry. That is the right
design — an unclassified route might serve a tenant data it should not — but
it means an OSS release that ADDS a route deadlocks the two cloud pull
requests against each other: the auto-pin PR is red on every check that
constructs the app, and a PR carrying the policy entry is red against the old
pin. Neither can be green alone, and the fix is one line of process.

Burned 2026-10-15 on 0.12.917 (``/api/delivery``). The failure presents as ~18
red checks on a PR that changed a version string, so it reads as a
catastrophe. ``scripts/list_oss_routes.py`` lets the pin PR say what is
actually going on, and these tests pin the two ways the message could lie: by
missing a route that was added, and by inventing routes that were not.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "list_oss_routes.py"

sys.path.insert(0, str(REPO / "scripts"))
import list_oss_routes as lor  # noqa: E402


def _run(*args):
    done = subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=REPO)
    return done


def _have(sha: str) -> bool:
    """Make *sha* and its parent available, fetching them if they are not.

    CI checks out at depth 1, so neither commit this test names is present
    and both route sets come back empty. A targeted depth-2 fetch costs one
    commit each and lets the real assertion run; where that is not possible
    the test skips rather than asserting against history it cannot see.
    """
    present = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                             cwd=REPO, capture_output=True)
    if present.returncode == 0:
        parent = subprocess.run(["git", "cat-file", "-e", f"{sha}^^{{commit}}"],
                                cwd=REPO, capture_output=True)
        if parent.returncode == 0:
            return True
    # GitHub refuses to serve an arbitrary commit by name unless the server
    # allows it, so this succeeds on a full local clone and fails on a
    # shallow CI checkout. The caller skips in that case;
    # ``test_the_diff_names_exactly_what_was_added`` covers the same contract
    # with no git at all, so CI is not left with nothing.
    fetched = subprocess.run(
        ["git", "fetch", "--quiet", "--depth=2", "origin", sha],
        cwd=REPO, capture_output=True)
    return fetched.returncode == 0


def test_the_route_table_is_not_empty():
    """A silent empty list would report every release as route-free, which is
    the failure mode that leaves the deadlock unannounced."""
    routes = lor.routes_at()
    assert len(routes) > 100, len(routes)
    assert "/api/delivery" in routes
    assert all(r.startswith("/") for r in routes)


@pytest.mark.skipif(
    not (REPO / ".git").exists(), reason="needs the git history")
def test_the_working_tree_and_the_same_commit_agree():
    """The two ways of listing have to see the same files.

    They did not. Reading the working tree used a non-recursive listing, so
    `routes/entitlement/` — a subpackage holding 435 of this repo's routes —
    was invisible, while reading a ref walked the whole tree. Worktree mode
    reported 537 routes and ref mode 972, and BOTH looked plausible, which is
    how a diff of the two would have announced 435 new routes on a release
    that added none.
    """
    assert lor.routes_at() == lor.routes_at("HEAD")


@pytest.mark.skipif(
    not (REPO / ".git").exists(), reason="needs the git history")
def test_a_base_that_reads_short_is_refused():
    """A partially readable base is more dangerous than an absent one.

    A shallow checkout that can resolve a ref but not serve its whole tree
    yields a short route set, and the difference between "two new routes" and
    "four hundred" is the difference between a usable instruction and one
    that sends the reader off to classify the entire API.
    """
    done = _run("--added-since", "v9.99.99")
    assert done.returncode == 2, done
    assert done.stdout.strip() == ""
    assert "incomplete" in done.stderr or "missing" in done.stderr


def test_a_decorator_argument_is_read_from_the_tree_not_the_text():
    """A regex over source text mis-reads a multi-line or computed
    decorator; ``ast`` sees the literal or nothing."""
    rules = lor._rules_from_source(
        "\n".join([
            "@bp.route('/api/plain', methods=['GET'])",
            "def a(): pass",
            "@bp.route(",
            "    '/api/wrapped',",
            "    methods=['POST'])",
            "def b(): pass",
            "@bp.route(f'/api/{computed}')",   # not a literal: must be skipped
            "def c(): pass",
            "app.add_url_rule('/api/added', view_func=d)",
            "@bp.route('relative-not-a-route')",
            "def e(): pass",
        ]), "<test>")
    assert rules == {"/api/plain", "/api/wrapped", "/api/added"}


def test_broken_source_warns_instead_of_raising():
    """A release workflow must never fail with a traceback: the message IS
    the deliverable here."""
    assert lor._rules_from_source("def oops(:\n", "<test>") == set()


@pytest.mark.skipif(
    not (REPO / ".git").exists(), reason="needs the git history")
def test_the_release_that_caused_the_deadlock_reports_its_routes():
    """0.12.917 added ``/api/delivery``; #6409 after it added nothing.

    Two real commits, so this cannot pass against a stub: ``cce45bf8ba`` is
    the Delivered tab and ``d7b3ddc3b9`` is the fix that followed it.
    """
    if not (_have("cce45bf8ba") and _have("d7b3ddc3b9")):
        pytest.skip("neither commit is reachable from this checkout")

    added = _run("--ref", "cce45bf8ba", "--added-since", "cce45bf8ba^")
    assert added.returncode == 0, added.stderr
    assert added.stdout.split() == [
        "/api/delivery", "/api/delivery/session/<path:session_id>"]

    quiet = _run("--ref", "d7b3ddc3b9", "--added-since", "d7b3ddc3b9^")
    assert quiet.returncode == 0, quiet.stderr
    assert quiet.stdout.strip() == "", quiet.stdout


def test_the_diff_names_exactly_what_was_added(tmp_path):
    """The comparison itself, with no git in the way.

    The test above uses the two real commits either side of the burn, but
    GitHub refuses to serve an arbitrary commit by name, so on a shallow CI
    checkout it can only skip — and a skipped test covers nothing. This one
    runs everywhere: two snapshots of the same module, one route added.
    """
    before = lor._rules_from_source(
        "\n".join(["@bp.route('/api/usage')", "def a(): pass",
                    "@bp.route('/api/sessions')", "def b(): pass"]), "<before>")
    after = lor._rules_from_source(
        "\n".join(["@bp.route('/api/usage')", "def a(): pass",
                    "@bp.route('/api/sessions')", "def b(): pass",
                    "@bp.route('/api/delivery')", "def c(): pass"]), "<after>")
    assert sorted(after - before) == ["/api/delivery"]
    assert sorted(before - after) == []
    # A release that adds nothing must produce nothing, not "everything".
    assert sorted(after - after) == []


def test_both_refs_unreadable_is_an_error_not_an_empty_answer():
    """The hole the first version had, found by CI.

    On a shallow checkout NEITHER ref resolved, both route sets came back
    empty, the difference was empty, and the script printed nothing and
    exited 0 — "this release added no routes". A plausible silence is the
    one outcome this script must never produce, so the working tree, which
    is always readable, is the yardstick both refs are held to.
    """
    done = _run("--ref", "deadbeef1234", "--added-since", "deadbeef1234^")
    assert done.returncode == 2, done
    assert done.stdout.strip() == ""
    assert "incomplete" in done.stderr


def test_an_unreachable_base_is_loud_not_plausible():
    """An unresolvable ref must not read as "this release added 537 routes".

    That is the specific lie this guard exists for: the pin PR would tell the
    next reader to go and classify the entire API.
    """
    done = _run("--added-since", "no-such-ref-abcdef")
    assert done.returncode == 2, done
    assert done.stdout.strip() == ""
    assert "0 routes readable" in done.stderr
    assert "working tree" in done.stderr
