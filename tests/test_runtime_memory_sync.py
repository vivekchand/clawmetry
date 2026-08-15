"""Per-runtime memory/skills sync: ingest, entitlement, and the cloud push.

Memory is NOT node-wide. Each runtime keeps its long-lived context somewhere
different on disk (``clawmetry/runtime_memory.py`` is the catalog), and the
daemon used to sync only the OpenClaw workspace — so a machine running Claude
Code and no OpenClaw produced zero ``memory_blobs`` rows, no cache push, and a
cloud Memory tab stuck on "Syncing memory files…" forever.

The ingest + push half of that fix is covered here:

  1. Every detected runtime's files land tagged with the owning runtime and
     the category they came from.
  2. Re-running is a sha256 no-op, so an idle laptop doesn't rewrite the table
     on every tick.
  3. A paid runtime the user is not entitled to is never ingested — the daemon
     must not be a side door around the 402 the /files route returns.
  4. …and never shipped either, so a DOWNGRADE stops serving rows that were
     ingested while the entitlement was live.
  5. Rows are pulled PER RUNTIME. With one global most-recent-N, the noisiest
     runtime (429 Claude Code files on the author's laptop) eats the whole
     budget and a quieter runtime's Memory tab renders empty — the original
     bug, one layer down.
  6. Files are deduped on (runtime, path), not path: several runtimes read the
     same file on disk (AGENTS.md is Codex + opencode + Copilot).
  7. Over-budget files stay LISTED with empty content rather than vanishing —
     a tree that hides files is lying about what the agent's memory is.
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
    """Fresh DuckDB + a fake catalog of three runtimes rooted in tmp_path."""
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

    roots = {}
    for rt, names in (
        ("openclaw", ["SOUL.md"]),
        ("claude_code", ["CLAUDE.md", "notes.md"]),
        ("codex", ["AGENTS.md"]),
    ):
        d = tmp_path / rt
        d.mkdir()
        for n in names:
            (d / n).write_text(f"# {rt} {n}\n")
        roots[rt] = str(d)

    def fake_list_runtimes():
        return [{"id": r, "label": r, "present": True} for r in roots] + [
            {"id": "cursor", "label": "Cursor", "present": False},
        ]

    def fake_list_files(runtime_id, category=None):
        root = roots.get(runtime_id)
        if not root or (category or "memory") != "memory":
            return {"runtime": runtime_id, "groups": []}
        files = [{"path": n, "size": os.path.getsize(os.path.join(root, n)),
                  "mtime": int(os.path.getmtime(os.path.join(root, n)))}
                 for n in sorted(os.listdir(root))]
        return {"runtime": runtime_id, "groups": [
            {"root": root, "exists": True, "category": "memory",
             "scope": "global", "files": files},
        ]}

    monkeypatch.setattr(rm, "list_runtimes", fake_list_runtimes)
    monkeypatch.setattr(rm, "list_files", fake_list_files)

    config = {
        "node_id": "node-rt-mem",
        "api_key": "cm_rt_mem_token",
        "encryption_key": s.generate_encryption_key(),
    }
    yield s, ls, config, roots
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _entitle(monkeypatch, *, denied=()):
    """Force the entitlement resolver to deny exactly `denied`."""
    import clawmetry.entitlements as ent

    class _Ent:
        def allows_runtime(self, rt):
            return rt not in denied

    monkeypatch.setattr(ent, "get_entitlement", lambda *a, **k: _Ent())
    monkeypatch.setattr(ent, "FREE_RUNTIMES", frozenset({"openclaw"}))


def _by_runtime(ls):
    out: dict = {}
    for r in ls.get_store().query_memory_blobs(limit=500):
        out.setdefault(r["agent_type"], []).append(r["path"])
    return out


def test_every_detected_runtime_is_ingested_and_tagged(sync_env, monkeypatch):
    s, ls, config, _ = sync_env
    _entitle(monkeypatch)
    assert s.sync_runtime_memory_files(config, {}, {}) == 4
    by_rt = _by_runtime(ls)
    assert sorted(by_rt) == ["claude_code", "codex", "openclaw"]
    assert len(by_rt["claude_code"]) == 2
    rows = ls.get_store().query_memory_blobs(agent_type="codex", limit=10)
    assert rows and rows[0]["category"] == "memory"
    assert rows[0]["root"], "root column must be populated for the viewer"


def test_reingest_is_a_noop_when_nothing_changed(sync_env, monkeypatch):
    s, _, config, _ = sync_env
    _entitle(monkeypatch)
    assert s.sync_runtime_memory_files(config, {}, {}) == 4
    assert s.sync_runtime_memory_files(config, {}, {}) == 0


def test_changed_file_is_picked_up(sync_env, monkeypatch):
    s, _, config, roots = sync_env
    _entitle(monkeypatch)
    s.sync_runtime_memory_files(config, {}, {})
    with open(os.path.join(roots["claude_code"], "notes.md"), "w") as fh:
        fh.write("# claude_code notes.md CHANGED\n")
    assert s.sync_runtime_memory_files(config, {}, {}) == 1


def test_locked_paid_runtime_is_never_ingested(sync_env, monkeypatch):
    """The daemon must not be a side door around the memory paywall:
    /api/runtimes/<rt>/files returns 402 for an unentitled paid runtime, so
    the daemon must not ship its contents to cloud either."""
    s, ls, config, _ = sync_env
    _entitle(monkeypatch, denied=("claude_code",))
    s.sync_runtime_memory_files(config, {}, {})
    by_rt = _by_runtime(ls)
    assert "claude_code" not in by_rt
    assert {"openclaw", "codex"} <= set(by_rt)


def test_downgrade_stops_shipping_rows_ingested_while_entitled(
        sync_env, monkeypatch):
    """Ingest-time gating alone is not enough: rows written during a paid
    period would keep riding the heartbeat after the entitlement lapsed."""
    s, _, config, _ = sync_env
    _entitle(monkeypatch)
    s.sync_runtime_memory_files(config, {}, {})
    assert s._build_memory_cache_pushes(config), "sanity: pushes while entitled"

    _entitle(monkeypatch, denied=("claude_code",))
    s._memory_push_state["fingerprint"] = None      # force a rebuild
    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    shipped = {f["runtime"] for f in payload["memory_state"]["files"]}
    assert "claude_code" not in shipped
    assert "openclaw" in shipped


def test_one_chatty_runtime_cannot_crowd_out_the_others(sync_env, monkeypatch):
    """Rows are pulled per runtime. A single global most-recent-N query lets
    the noisiest runtime take the whole budget, and the crowded-out runtime's
    Memory tab renders empty — the bug this branch exists to fix."""
    s, ls, config, _ = sync_env
    _entitle(monkeypatch)
    monkeypatch.setattr(s, "MEMORY_CACHE_LIMIT", 2)
    for i in range(8):
        ls.get_store().ingest_memory_blob({
            "agent_type": "claude_code", "path": f"/x/filler{i}.md",
            "blob": f"# filler {i}\n", "category": "memory", "root": "/x",
        })
    s.sync_runtime_memory_files(config, {}, {})
    s._memory_push_state["fingerprint"] = None
    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    shipped = {}
    for f in payload["memory_state"]["files"]:
        shipped[f["runtime"]] = shipped.get(f["runtime"], 0) + 1
    assert shipped["claude_code"] == 2, "per-runtime cap applies"
    assert shipped.get("openclaw"), "quiet runtime still represented"
    assert shipped.get("codex"), "quiet runtime still represented"


def test_a_file_shared_by_two_runtimes_survives_under_both(sync_env, monkeypatch):
    """AGENTS.md is read by Codex, opencode and Copilot alike. Deduping on
    path alone kept it for whichever runtime sorted first and left the file
    invisible under every other one."""
    s, ls, config, _ = sync_env
    _entitle(monkeypatch)
    shared = "/Users/x/AGENTS.md"
    for rt in ("codex", "openclaw"):
        ls.get_store().ingest_memory_blob({
            "agent_type": rt, "path": shared, "blob": "# shared\n",
            "category": "memory", "root": "/Users/x",
        })
    s._memory_push_state["fingerprint"] = None
    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    owners = {f["runtime"] for f in payload["memory_state"]["files"]
              if f["path"] == shared}
    assert owners == {"codex", "openclaw"}
    bodies = [c for c in payload["memory_content"] if c["path"] == shared]
    assert {c.get("runtime") for c in bodies} == {"codex", "openclaw"}, \
        "contents must be runtime-tagged too, or the viewer picks the wrong copy"


def test_over_budget_files_are_listed_without_content_not_hidden(
        sync_env, monkeypatch):
    """A tree that silently hides files lies about what the agent's memory is."""
    s, _, config, _ = sync_env
    _entitle(monkeypatch)
    monkeypatch.setattr(s, "MEMORY_CACHE_TOTAL_BUDGET", 30)
    s.sync_runtime_memory_files(config, {}, {})
    s._memory_push_state["fingerprint"] = None
    payload = s.decrypt_payload(
        s._build_memory_cache_pushes(config)[0]["blob"],
        config["encryption_key"])
    files = payload["memory_state"]["files"]
    assert len(files) == 4, "every file stays listed"
    assert payload["_content_dropped"] > 0
    assert any(not c["content"] for c in payload["memory_content"])


def test_unchanged_snapshot_is_not_repushed_every_heartbeat(sync_env, monkeypatch):
    """It runs to megabytes of ciphertext; pushing it every 60s was pure
    egress for a payload that changes hourly at best."""
    s, _, config, _ = sync_env
    _entitle(monkeypatch)
    s.sync_runtime_memory_files(config, {}, {})
    assert len(s._build_memory_cache_pushes(config)) == 1
    assert s._build_memory_cache_pushes(config) == []


def test_content_change_defeats_the_push_floor(sync_env, monkeypatch):
    """The floor is a rate limit on UNCHANGED content, not on updates."""
    s, ls, config, roots = sync_env
    _entitle(monkeypatch)
    s.sync_runtime_memory_files(config, {}, {})
    s._build_memory_cache_pushes(config)
    with open(os.path.join(roots["codex"], "AGENTS.md"), "w") as fh:
        fh.write("# codex AGENTS.md CHANGED\n")
    s.sync_runtime_memory_files(config, {}, {})
    assert len(s._build_memory_cache_pushes(config)) == 1
