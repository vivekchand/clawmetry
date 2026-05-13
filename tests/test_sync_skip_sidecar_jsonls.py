"""Regression test for #1129 (bug 1).

The cloud sync daemon must NOT ingest OpenClaw's trace-artifact sidecar
files (`*.trajectory.jsonl`, `*.checkpoint.jsonl`, `*.deleted.jsonl`)
into DuckDB. They live next to the real session jsonl, are typically
much larger, and downstream `_canonical_session_file()` would split
them at the first `.jsonl`, producing phantom session_ids like
`<uuid>.trajectory` that pollute `/api/sessions` and
`/api/brain-history`.

The dashboard read-path already excludes these (dashboard.py,
routes/sessions.py, routes/brain.py, routes/usage.py). This test pins
the daemon ingest behavior to the same exclusion.
"""

import os
import tempfile

from clawmetry.sync import _canonical_session_file, _list_session_jsonls


def test_list_session_jsonls_skips_trajectory_checkpoint_deleted_sidecars():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Real session files we DO want to ingest.
        keep = [
            "aaa.jsonl",
            "ccc.jsonl.reset.1234567890",
        ]
        # Sidecar files we MUST skip.
        skip = [
            "aaa.trajectory.jsonl",
            "aaa.checkpoint.jsonl",
            "bbb.deleted.jsonl",
        ]
        for name in keep + skip:
            with open(os.path.join(tmpdir, name), "w") as f:
                f.write("")

        result = _list_session_jsonls(tmpdir)
        result_names = sorted(os.path.basename(p) for p in result)

        assert result_names == sorted(keep), (
            f"Expected only {sorted(keep)}, got {result_names}"
        )

        # Explicit assertions for the bug we're fixing.
        for sidecar in skip:
            assert sidecar not in result_names, (
                f"Sidecar {sidecar!r} must be excluded from sync ingest "
                f"(it would create a phantom session_id in DuckDB)"
            )


def test_canonical_session_file_unchanged_for_sidecars():
    """Document that `_canonical_session_file()` does NOT itself filter
    sidecars — it splits at the first `.jsonl` and would produce a
    phantom session_id. The exclusion happens upstream in
    `_list_session_jsonls()`, so this function never sees these names
    in production. If that contract ever changes, this test will need
    revisiting.
    """
    # Sanity: real sessions and reset archives canonicalize as expected.
    assert _canonical_session_file("aaa.jsonl") == "aaa.jsonl"
    assert _canonical_session_file("aaa.jsonl.reset.1234567890") == "aaa.jsonl"
    assert _canonical_session_file("/some/path/aaa.jsonl") == "aaa.jsonl"

    # Sidecar names: `_canonical_session_file()` splits at the first
    # `.jsonl`, so it returns the full sidecar basename unchanged
    # (e.g. `foo.trajectory.jsonl` → `foo.trajectory.jsonl`). That is
    # exactly the phantom-session_id form the upstream filter prevents.
    # Documents the upstream-filter contract: this function never sees
    # these names in production after the _list_session_jsonls fix.
    assert (
        _canonical_session_file("foo.trajectory.jsonl") == "foo.trajectory.jsonl"
    )
    assert (
        _canonical_session_file("foo.checkpoint.jsonl") == "foo.checkpoint.jsonl"
    )
    assert _canonical_session_file("foo.deleted.jsonl") == "foo.deleted.jsonl"
