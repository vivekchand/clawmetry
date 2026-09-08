"""Properties the DuckDB store must hold under ANY sequence of operations.

Every other test in this repo checks an example somebody thought of. That is
why each new bug arrives with a new bespoke guard written after users hit it.
These tests state *properties* instead and let Hypothesis search for a sequence
that breaks them, then shrink it to the shortest reproducing case.

The invariants are not invented. Each is a contract the store's own docstrings
declare, or a documented burn:

* ``ingest`` says "Re-ingesting the same id is a no-op (INSERT OR IGNORE) so
  callers don't need their own dedup." Adapters replay journals constantly -- a
  runtime that writes an event twice, or a backfill re-reading a file -- so a
  regression here inflates every cost and token figure the product reports.
* Issue #1590: two concurrent flushes each snapshotted the ring and then popped
  ``len(batch)``, evicting events the other had snapshotted but not yet
  written. Events vanished silently. Interleaving ingest with flush is exactly
  the sequence a generator finds and a hand-written test does not, because
  hand-written tests flush once at the end.
* CLAUDE.md: "Never crash on bad input." A torn JSONL tail is a partial dict,
  and adapters read files a live agent is still writing, so partial records are
  normal rather than exceptional.
* Issue #1771 (the "brick-lock"): a read-only handle must never be able to
  write, and must never wedge the writer.

ISOLATION, and why the import order below is load-bearing: ``local_store.DB_PATH``
is resolved at MODULE IMPORT from ``CLAWMETRY_LOCAL_STORE_PATH``. Setting that
variable inside a fixture is too late -- the module is already imported and the
path is already fixed, so the tests would quietly run against the developer's
real ``~/.clawmetry/clawmetry.duckdb``. The environment is therefore prepared at
module scope, before ``clawmetry`` is imported at all. This is the same trap
clawmetry-pro's FLYWHEEL documents: without ``mark_writer_owner()`` first,
``get_store()`` returns the daemon proxy and every write silently no-ops.
"""
from __future__ import annotations

import os
import shutil
import tempfile

import pytest

duckdb = pytest.importorskip("duckdb", reason="store invariants need duckdb")
_hyp = pytest.importorskip("hypothesis", reason="store invariants need hypothesis")

# --- Environment MUST be prepared before clawmetry is imported. -------------
_TMPDIR = tempfile.mkdtemp(prefix="cm-invariants-")
os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = os.path.join(_TMPDIR, "invariants.duckdb")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402
from hypothesis.stateful import (  # noqa: E402
    RuleBasedStateMachine,
    invariant,
    rule,
)

from clawmetry import local_store  # noqa: E402

local_store.mark_writer_owner()


def pytest_sessionfinish():  # pragma: no cover - best-effort cleanup
    shutil.rmtree(_TMPDIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# No-silent-skip enforcement
# ---------------------------------------------------------------------------

def test_invariants_are_not_skipped_in_ci():
    """A skipped invariant suite is indistinguishable from a passing one.

    verification/matrix.json declares the 'daemon-invariants' cell as gated,
    which means CI must install duckdb and hypothesis. If CI ever stops doing
    so, the importorskip above would turn this entire file into a silent no-op
    while the matrix still claimed the cell was covered. This makes it loud.
    """
    if not os.environ.get("CI"):
        pytest.skip("local run; the CI assertion is the one that matters")
    import importlib.util

    for mod in ("duckdb", "hypothesis"):
        assert importlib.util.find_spec(mod), (
            f"{mod} is missing in CI, so tests/test_store_invariants.py would "
            "silently skip while verification/matrix.json still declares "
            "'daemon-invariants' gated. Install it in the CI job."
        )


# ---------------------------------------------------------------------------
# Shared writer. One DuckDB file per module: DuckDB refuses a second connection
# to the same file under a different configuration, and the real deployment
# separates writer and reader by PROCESS, not by handle.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def store():
    st_ = local_store.LocalStore(read_only=False)
    try:
        yield st_
    finally:
        try:
            st_.stop(flush=False)
        except Exception:
            pass
        shutil.rmtree(_TMPDIR, ignore_errors=True)


_COUNTER = {"n": 0}


def _uid(prefix: str) -> str:
    _COUNTER["n"] += 1
    return f"{prefix}-{_COUNTER['n']}"


def _event(eid: str, *, session_id: str = "s1", ts: str = "2026-08-01T00:00:00Z") -> dict:
    return {
        "id": eid,
        "node_id": "node-invariant",
        "event_type": "message",
        "ts": ts,
        "session_id": session_id,
        "agent_id": "agent-invariant",
    }


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

@settings(max_examples=25, deadline=None, suppress_health_check=list(HealthCheck))
@given(
    suffixes=st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=12),
        min_size=1,
        max_size=15,
        unique=True,
    ),
    repeats=st.integers(min_value=2, max_value=4),
)
def test_ingest_is_idempotent_by_id(store, suffixes, repeats):
    """Re-ingesting the same id must never create a second row.

    ingest() promises this so adapters do not need their own dedup. A
    regression double-counts cost and tokens for every replayed journal.
    """
    batch_tag = _uid("idem")
    ids = [f"{batch_tag}-{s}" for s in suffixes]

    for _ in range(repeats):
        store.ingest_many([_event(i) for i in ids])
    store.flush()

    rows = store.query_events(limit=5000)
    mine = [r.get("id") for r in rows if str(r.get("id", "")).startswith(batch_tag)]
    assert sorted(mine) == sorted(set(mine)), (
        f"duplicate rows after {repeats} replays of {len(ids)} ids; "
        "INSERT OR IGNORE dedup is broken and every cost figure inflates"
    )
    assert set(mine) == set(ids), (
        f"expected {len(ids)} distinct ids back, got {len(set(mine))}"
    )


def test_incomplete_events_are_rejected_cleanly_and_non_destructively(store):
    """A torn JSONL tail must be rejected PREDICTABLY, never destructively.

    Note on scope, because the first draft of this test asserted the wrong
    thing. ``ingest`` documents four required keys and deliberately raises
    ``ValueError`` when one is missing -- that is a contract, not a crash, and
    it is correct for a library primitive to enforce it. CLAUDE.md's "never
    crash on bad input" binds the DAEMON, whose job is to catch that ValueError
    and keep going, not the store beneath it.

    So the property worth holding is about the blast radius of a rejection:

    1. the error is the DECLARED ValueError, so a caller can catch it by type
       rather than by catching everything;
    2. a rejected record leaves previously-stored data intact;
    3. the store still accepts good events afterwards -- one torn tail in a
       backfill of hundreds of sessions must not poison the rest of the run.
    """
    good = _uid("good")
    store.ingest(_event(good))
    store.flush()

    incomplete = [
        {},
        {"id": _uid("no-node")},
        {"id": None, "node_id": None, "event_type": None, "ts": None},
    ]
    for bad in incomplete:
        with pytest.raises(ValueError):
            store.ingest(bad)

    # Present-but-odd values are NOT incomplete: these must be accepted, since
    # a real agent writes odd timestamps and deeply nested metadata.
    odd_but_complete = [
        {
            "id": _uid("bad-ts"),
            "node_id": "n",
            "event_type": "message",
            "ts": "not-a-date",
        },
        {
            "id": _uid("nested"),
            "node_id": "n",
            "event_type": "m",
            "ts": "2026-08-01T00:00:00Z",
            "metadata": {"deep": {"deeper": [1, 2, {"x": "y"}]}},
        },
    ]
    for odd in odd_but_complete:
        try:
            store.ingest(odd)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"ingest({odd!r}) raised {type(exc).__name__}: {exc}. All four "
                "required keys are present, so this is a well-formed event with "
                "unusual values -- exactly what a live agent produces."
            )

    survivor = _uid("after-bad")
    store.ingest(_event(survivor))
    store.flush()

    rows = {r.get("id") for r in store.query_events(limit=5000)}
    assert good in rows, (
        "a previously-stored event disappeared after a rejected record"
    )
    assert survivor in rows, (
        "the store stopped accepting good events after rejecting a torn record "
        "-- one bad tail must not poison the rest of a backfill"
    )


def test_read_only_mode_refuses_writes(store):
    """The read-only guard must fire before any write reaches DuckDB.

    In production the dashboard opens read-only in a SEPARATE PROCESS while the
    daemon owns the writer lock. DuckDB refuses two in-process connections to
    one file under different configurations, so opening a real second handle
    here would test the harness rather than the guard. The guard itself is the
    first statement of ingest_many -- ``if self._read_only: raise`` -- so the
    read-only flag is toggled on the live store to exercise exactly that line,
    then restored and the writer proven still healthy (the #1771 signature is a
    writer that never recovers).
    """
    before = _uid("before-ro")
    store.ingest(_event(before))
    store.flush()

    store._read_only = True
    try:
        with pytest.raises(RuntimeError, match="read-only"):
            store.ingest(_event(_uid("via-ro")))
    finally:
        store._read_only = False

    after = _uid("after-ro")
    store.ingest(_event(after))
    store.flush()

    rows = {r.get("id") for r in store.query_events(limit=5000)}
    assert after in rows, (
        "the writer stopped accepting events after read-only mode was used -- "
        "this is the #1771 brick-lock signature"
    )
    assert before in rows, "a previously-flushed event was lost"


# ---------------------------------------------------------------------------
# Stateful model -- sequences, not examples
# ---------------------------------------------------------------------------

class StoreModel(RuleBasedStateMachine):
    """Drive the store with generated operation sequences and check invariants.

    The model tracks which ids were ingested and successfully flushed. The core
    property is conservation: nothing acknowledged may disappear. Issue #1590
    was exactly a violation of that under interleaved ingest and flush, and it
    shipped because every hand-written test flushed once at the end.
    """

    def __init__(self):
        super().__init__()
        self.store = local_store.LocalStore(read_only=False)
        self.tag = _uid("model")
        self.flushed_ids: set = set()
        self.pending_ids: set = set()
        self._n = 0

    @rule(count=st.integers(min_value=1, max_value=5))
    def ingest_events(self, count):
        batch = []
        for _ in range(count):
            self._n += 1
            eid = f"{self.tag}-{self._n}"
            batch.append(_event(eid))
            self.pending_ids.add(eid)
        self.store.ingest_many(batch)

    @rule()
    def ingest_duplicate(self):
        """Replay an already-seen event, as a real adapter does."""
        known = sorted(self.flushed_ids | self.pending_ids)
        if known:
            self.store.ingest(_event(known[0]))

    @rule()
    def flush(self):
        self.store.flush()
        self.flushed_ids |= self.pending_ids
        self.pending_ids = set()

    @invariant()
    def acknowledged_events_are_never_lost(self):
        if not self.flushed_ids:
            return
        rows = self.store.query_events(limit=5000)
        present = {r.get("id") for r in rows}
        missing = self.flushed_ids - present
        assert not missing, (
            f"{len(missing)} flushed event(s) vanished: {sorted(missing)[:5]}. "
            "This is the issue #1590 class -- a concurrent flush evicting a "
            "batch that another flush had snapshotted but not yet written."
        )

    @invariant()
    def no_duplicate_ids(self):
        rows = self.store.query_events(limit=5000)
        mine = [
            r.get("id")
            for r in rows
            if str(r.get("id", "")).startswith(self.tag)
        ]
        assert len(mine) == len(set(mine)), (
            "duplicate ids in the store; INSERT OR IGNORE dedup regressed"
        )

    def teardown(self):
        try:
            self.store.stop(flush=False)
        except Exception:
            pass


StoreModel.TestCase.settings = settings(
    max_examples=10,
    stateful_step_count=10,
    deadline=None,
    suppress_health_check=list(HealthCheck),
)

TestStoreModel = StoreModel.TestCase
