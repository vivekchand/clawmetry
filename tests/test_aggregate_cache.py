"""query_aggregates must be TTL-cached so the daemon doesn't re-run the heavy
full-table dedupe on every dashboard poll (CPU-budget, FLYWHEEL.md)."""
import importlib


def _store(tmp_path, monkeypatch, ttl):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", ttl)
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    ls.invalidate_aggregate_cache()
    return ls, ls.LocalStore(read_only=False)


def _counting_fetch(st, monkeypatch, calls):
    real = st._fetch
    def counting(sql, params):
        if "deduped" in sql:
            calls["n"] += 1
        return real(sql, params)
    monkeypatch.setattr(st, "_fetch", counting)


def test_second_call_is_cached(tmp_path, monkeypatch):
    ls, st = _store(tmp_path, monkeypatch, "60")
    calls = {"n": 0}
    _counting_fetch(st, monkeypatch, calls)
    st.query_aggregates(since="2026-01-01")
    st.query_aggregates(since="2026-01-01")
    assert calls["n"] == 1, f"expected 1 SQL run (2nd cached), got {calls['n']}"
    st.query_aggregates(since="2026-02-01")   # different params -> recompute
    assert calls["n"] == 2


def test_ttl_zero_disables_cache(tmp_path, monkeypatch):
    ls, st = _store(tmp_path, monkeypatch, "0")
    calls = {"n": 0}
    _counting_fetch(st, monkeypatch, calls)
    st.query_aggregates(since="2026-01-01")
    st.query_aggregates(since="2026-01-01")
    assert calls["n"] == 2
