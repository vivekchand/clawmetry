<!--
Closes issue #1268. The MOAT checklist below catches the class of bug
that produced the 3-PR cascade #1258 → #1260 → #1266 today (forgot
allowlist + treated empty-fastpath as miss).

Drop the irrelevant sections; keep what applies to your change.
-->

## Summary

<!-- 1-3 bullets on what + why -->

## Test plan

<!-- Bulleted markdown checklist of the things you actually verified -->
- [ ]

---

### MOAT fast-path test plan (only when adding/modifying a daemon-proxy `_try_local_store_*` helper)

If this PR touches a `local_store_via_daemon(...)` call, a `_ls_call(...)` wrapper, or the `_DAEMON_METHODS` allowlist in `routes/local_query.py`, every box below should be ticked before merge:

- [ ] `make lint-daemon-allowlist` passes locally (CI also runs this — see `scripts/lint_daemon_allowlist.py` from PR #1272)
- [ ] `curl -w '%{time_total}\n' http://localhost:8900/api/<endpoint>` returns **<500 ms** with **populated** local DuckDB
- [ ] Same curl returns **<500 ms** with **empty** local DuckDB tables — proves the fast-path returns `[]` not `None` (the bug PR #1266 fixed)
- [ ] Same curl after `launchctl bootout gui/$(id -u)/com.clawmetry.sync` (daemon stopped) — handler degrades to legacy path with reasonable error, doesn't 500
- [ ] Response JSON includes `_source: "local_store"` (or `"daemon_proxy"` for system-health-style aggregates)
- [ ] After deploy, `tail ~/.clawmetry/sync.log` shows `POST /__local_query__/query_<method> HTTP/1.1 200` per request — proves the proxy is hot, not a silent fall-through

### Release plan (only for `[RELEASE]` PRs)

- [ ] PR title starts with `[RELEASE]` so `release-on-merge.yml` auto-bumps + publishes (per `reference_release_process.md`)
- [ ] After auto-publish: `pip install --upgrade --no-cache-dir clawmetry==<bump>` then `launchctl kickstart -k gui/$(id -u)/com.clawmetry.dashboard com.clawmetry.sync` to verify on the host
