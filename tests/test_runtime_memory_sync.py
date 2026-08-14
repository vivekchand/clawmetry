"""Memory is per-runtime, not "whatever is in the OpenClaw workspace".

Every supported runtime keeps its long-lived context somewhere different on
disk (``clawmetry/runtime_memory.py`` is the catalog). The daemon used to sync
ONLY the OpenClaw workspace files, so a machine running Claude Code — and no
OpenClaw — produced zero ``memory_blobs`` rows, no memory cache push, and a
cloud Memory tab stuck on "Syncing memory files…" waiting for a heartbeat that
had nothing to send.

Covered here:
  1. ``_local_ingest_runtime_memory`` ingests each detected runtime's memory
     files tagged with that runtime (``agent_type``).
  2. Re-running is a no-op — the store dedups on sha256, so an unchanged
     laptop does not rewrite the table every tick.
  3. OpenClaw is left to ``_local_ingest_memory_files`` (no double rows under
     two different path spellings).
  4. The cloud cache push carries the per-file ``runtime`` tag + per-runtime
     counts, which is what lets the cloud Memory tab scope to the runtime
     picked in the header switcher.
  5. Rows are pulled PER RUNTIME, so a runtime with hundreds of memory files
     cannot crowd another runtime out of the pushed blob.
  6. An unchanged blob is not re-pushed on every heartbeat (it is ~megabytes
     of ciphertext; pushing it 60x an hour was pure egress).
  7. ``list_all_files`` merges runtimes for the "All" scope and drops runtimes
     the caller is not entitled to.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_env(tmp_path, monkeypatch):
    """Fresh DuckDB + a fake two-runtime catalog rooted in tmp_path."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "s.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.runtime_memory as rm
    import clawmetry.sync as s
    importlib.reload(s)

    cc_dir = tmp_path / "claude" / "memory"
    cc_dir.mkdir(parents=True)
    (cc_dir / "CLAUDE.md").write_text("# Claude Code\nproject rules\n")
    (cc_dir / "notes.md").write_text("# Notes\nremember this\n")
    cx_dir = tmp_path / "codex"
    cx_dir.mkdir(parents=True)
    (cx_dir / "AGENTS.md").write_text("# Codex\nagent rules\n")
    oc_dir = tmp_path / "openclaw"
    oc_dir.mkdir(parents=True)
    (oc_dir / "SOUL.md").write_text("# Soul\n")

    def fake_list_runtimes():
        return [
            {"id": "openclaw", "label": "OpenClaw", "present": True},
            {"id": "claude_code", "label": "Claude Code", "present": True},
            {"id": "codex", "label": "Codex", "present": True},
            {"id": "cursor", "label": "Cursor", "present": False},
        ]

    def fake_list_files(runtime_id, category=None):
        roots = {
            "openclaw": str(oc_dir),
            "claude_code": str(cc_dir),
            "codex": str(cx_dir),
        }
        root = roots.get(runtime_id)
        if not root:
            return {"runtime": runtime_id, "groups": []}
        files = [{"path": n, "size": os.path.getsize(os.path.join(root, n)),
                  "mtime": int(os.path.getmtime(os.path.join(root, n)))}
                 for n in sorted(os.listdir(root))]
        return {"runtime": runtime_id, "groups": [
            {"root": root, "exists": True, "category": "memory", "files": files},
        ]}

    monkeypatch.setattr(rm, "list_runtimes", fake_list_runtimes)
    monkeypatch.setattr(rm, "list_files", fake_list_files)

    config = {
        "node_id": "node-rt-mem",
        "api_key": "cm_rt_mem_token",
        "encryption_key": s.generate_encryption_key(),
    }
    yield s, ls, config
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _rows_by_runtime(ls):
    rows = ls.get_store().query_memory_blobs(limit=500)
    out: dict = {}
    for r in rows:
        out.setdefault(r["agent_type"], []).append(r["path"])
    return out


def test_ingests_each_runtimes_memory_tagged_with_that_runtime(sync_env):
    s, ls, _ = sync_env
    assert s._local_ingest_runtime_memory() == 3   # 2 claude_code + 1 codex
    by_rt = _rows_by_runtime(ls)
    assert sorted(by_rt) == ["claude_code", "codex"]
    assert len(by_rt["claude_code"]) == 2
    assert any(p.endswith("CLAUDE.md") for p in by_rt["claude_code"])
    assert any(p.endswith("AGENTS.md") for p in by_rt["codex"])


def test_reingest_is_a_noop_when_nothing_changed(sync_env):
    s, _, _ = sync_env
    assert s._local_ingest_runtime_memory() == 3
    assert s._local_ingest_runtime_memory() == 0


def test_changed_file_is_picked_up(sync_env, tmp_path):
    s, ls, _ = sync_env
    s._local_ingest_runtime_memory()
    (tmp_path / "claude" / "memory" / "notes.md").write_text("# Notes\nCHANGED\n")
    assert s._local_ingest_runtime_memory() == 1


def test_openclaw_is_left_to_the_workspace_ingest(sync_env):
    """OpenClaw rows come from _local_ingest_memory_files, which owns the
    cloud-facing path spelling. Ingesting it here too would produce two rows
    for the same file under different names."""
    s, ls, _ = sync_env
    s._local_ingest_runtime_memory()
    assert "openclaw" not in _rows_by_runtime(ls)


def test_locked_paid_runtime_is_never_ingested_or_shipped(sync_env, monkeypatch):
    """The daemon must not be a side door around the memory paywall.

    ``/api/runtimes/<rt>/files`` returns 402 for a paid runtime the user is
    not entitled to. If the daemon ingested it anyway, the file would ride the
    heartbeat to the cloud Memory tab and render there for free — so both use
    the same predicate."""
    s, ls, config = sync_env
    from clawmetry import runtime_memory as rm
    monkeypatch.setattr(rm, "runtime_is_locked",
                        lambda rt: rt == "claude_code")

    assert s._local_ingest_runtime_memory() == 1        # codex only
    by_rt = _rows_by_runtime(ls)
    assert "claude_code" not in by_rt
    assert "codex" in by_rt

    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    assert {f["runtime"] for f in payload["memory_state"]["files"]} == {"codex"}


def test_downgrade_stops_shipping_rows_ingested_while_entitled(sync_env, monkeypatch):
    """Rows already in the store from a paid period must stop riding the
    heartbeat once the entitlement lapses — otherwise a downgrade keeps
    serving them to the cloud Memory tab."""
    s, ls, config = sync_env
    s._local_ingest_runtime_memory()
    from clawmetry import runtime_memory as rm
    monkeypatch.setattr(rm, "runtime_is_locked", lambda rt: rt == "claude_code")
    s._mark_memory_cache_dirty()

    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    assert {f["runtime"] for f in payload["memory_state"]["files"]} == {"codex"}


def test_cache_push_tags_each_file_with_its_runtime(sync_env):
    s, _, config = sync_env
    s._local_ingest_runtime_memory()
    pushes = s._build_memory_cache_pushes(config)
    assert len(pushes) == 1
    payload = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    files = payload["memory_state"]["files"]
    assert files, "cache push must carry the memory file list"
    assert {f["runtime"] for f in files} == {"claude_code", "codex"}
    assert all(c.get("runtime") for c in payload["memory_content"])
    assert {r["id"]: r["files"] for r in payload["runtimes"]} == {
        "claude_code": 2, "codex": 1,
    }


def test_one_chatty_runtime_cannot_crowd_out_the_others(sync_env, monkeypatch):
    """Rows are pulled per runtime. With a single global most-recent-N query, a
    node with hundreds of Claude Code auto-memory files pushed a blob with
    nothing else in it and the OpenClaw Memory tab went blank."""
    s, ls, config = sync_env
    monkeypatch.setattr(s, "MEMORY_CACHE_LIMIT", 2)
    for extra in range(6):
        ls.get_store().ingest_memory_blob({
            "agent_type": "claude_code", "path": f"~/.claude/x{extra}.md",
            "blob": f"# filler {extra}\n",
        })
    s._local_ingest_runtime_memory()
    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    by_rt = {}
    for f in payload["memory_state"]["files"]:
        by_rt[f["runtime"]] = by_rt.get(f["runtime"], 0) + 1
    assert by_rt["claude_code"] == 2      # capped
    assert by_rt["codex"] == 1            # still represented


def test_unchanged_blob_is_not_repushed_every_heartbeat(sync_env):
    s, _, config = sync_env
    s._local_ingest_runtime_memory()
    assert len(s._build_memory_cache_pushes(config)) == 1
    assert s._build_memory_cache_pushes(config) == []
    s._mark_memory_cache_dirty()
    assert len(s._build_memory_cache_pushes(config)) == 1


def test_ttl_refresh_repushes_the_cached_blob(sync_env):
    s, _, config = sync_env
    s._local_ingest_runtime_memory()
    s._build_memory_cache_pushes(config)
    s._memory_cache_entry["pushed_at"] = 0     # older than the refresh window
    assert len(s._build_memory_cache_pushes(config)) == 1


def test_list_all_files_merges_runtimes_and_honours_the_entitlement_gate(
        tmp_path, monkeypatch):
    """The "All runtimes" scope must not become a side door around the
    per-runtime 402: locked runtimes are dropped from the merge."""
    from clawmetry import runtime_memory as rm

    a = tmp_path / "a"; a.mkdir(); (a / "MEMORY.md").write_text("a\n")
    b = tmp_path / "b"; b.mkdir(); (b / "CLAUDE.md").write_text("b\n")
    empty = tmp_path / "empty"; empty.mkdir()

    monkeypatch.setattr(rm, "_catalog", lambda: [
        rm.RuntimeCatalogEntry(id="openclaw", label="OpenClaw", roots=(
            rm.RootSpec("memory", str(a), ("*.md",), "Agent memory"),)),
        rm.RuntimeCatalogEntry(id="claude_code", label="Claude Code", roots=(
            rm.RootSpec("memory", str(b), ("*.md",), "Global CLAUDE.md"),
            rm.RootSpec("memory", str(empty), ("*.md",), "Project memory"),
            rm.RootSpec("memory", str(tmp_path / "gone"), ("*.md",), "Absent"),)),
    ])

    merged = rm.list_all_files(category="memory")
    assert merged["runtime"] == "all"
    assert [g["runtime"] for g in merged["groups"]] == ["openclaw", "claude_code"]
    for g in merged["groups"]:
        assert g["files"], "empty + absent roots are dropped from the merge"
        assert g["label"].startswith(g["runtime_label"])

    kept = rm.list_all_files(category="memory", exclude_runtimes=["claude_code"])
    assert {g["runtime"] for g in kept["groups"]} == {"openclaw"}
