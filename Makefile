.PHONY: test test-api test-e2e test-e2e-duckdb test-fast test-workflow test-moat test-moat-real moat-check moat-check-drive dev lint lint-daemon-allowlist

dev:
	OPENCLAW_GATEWAY_TOKEN=dev-token python3 dashboard.py --port 8900

test: test-api test-e2e test-e2e-duckdb test-workflow

test-fast:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_api.py -v

test-api:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_api.py -v

test-e2e:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_e2e.py -v

# Self-contained: drives the daemon ingest helper + relay shapes against an
# isolated DuckDB file. No live server, no gateway, no network. ~5s.
test-e2e-duckdb:
	python3 -m pytest tests/test_e2e_duckdb_relay.py -v

test-workflow:
	python3 -m pytest tests/test_e2e_nightly_workflow.py -v

# MOAT verifier suite (issue #1491 / PRD #1133 invariant #3). Hermetic —
# no live server, no gateway, no network. ~10s locally. Mirror the CI
# job in .github/workflows/ci.yml (moat-tests). If you add a file here,
# add it there too.
test-moat:
	python3 -m pytest \
	    tests/test_moat_send_message_e2e.py \
	    tests/test_moat_event_shape_manifest_guard.py \
	    tests/test_moat_e2e_regression_1129.py \
	    tests/test_e2e_real_openclaw_pipeline.py \
	    tests/test_duckdb_fastpath_v3_invariants.py \
	    tests/test_moat_cloud_roundtrip_e2e.py \
	    tests/test_channel_event_chokepoint.py \
	    tests/test_no_direct_get_store_in_routes.py \
	    tests/test_local_query_api.py \
	    -q

# MOAT real-data E2E (2026-05-19 mandate). Drives a REAL ``openclaw agent
# --local`` turn, ingests via the daemon, then asserts every endpoint
# called out in the user mandate (overview / channels / crons /
# system-health on top of the sibling test's sessions / transcript /
# usage / brain-history / flow). Requires the ``openclaw`` binary on
# PATH (skipped cleanly otherwise). ~45s end-to-end. Memory pin:
# feedback_synthetic_tests_missed_real_event_shape.md.
test-moat-real:
	python3 -m pytest tests/test_moat_real_e2e.py -v

# MOAT keystone bar (docs/MOAT_BAR.md Section 5, AC#1). The 13-endpoint
# verifier that drives a real openclaw turn (or skips it via --no-drive)
# and asserts every UI-backing API surface returns non-zero, correctly
# shaped data. Hard-gate on every PR via the moat-keystone job in
# .github/workflows/ci.yml. ~2s in --no-drive mode against a warm
# DuckDB; 30-60s when driving a real openclaw turn.
#
# Requires: dashboard listening on 127.0.0.1:8900 AND sync daemon
# running (writes ~/.clawmetry/local_query.json). Locally:
#   make dev   # starts dashboard
#   python3 -m clawmetry.sync   # starts daemon
#   make moat-check
moat-check:
	@python3 scripts/accuracy_harness/keystone_e2e.py --no-drive

# Drive mode (real openclaw agent turn -> +2 events in DuckDB -> 13
# probes). Costs LLM tokens, so runs nightly on main via
# .github/workflows/moat-keystone-drive-nightly.yml — never per-PR.
moat-check-drive:
	@python3 scripts/accuracy_harness/keystone_e2e.py

lint: lint-py lint-js lint-daemon-allowlist

# Issue #1267: every `local_store_via_daemon("X")` / `_ls_call("X")` call
# in routes/ must reference a method that's in the daemon's allowlist
# (routes/local_query.py:_DAEMON_METHODS). Catches the gap that produced
# the 3-PR cascade #1258 → #1260 → #1266 (forgot to add new methods to
# the allowlist; daemon returned 400; fast-paths fell through to slow
# legacy paths; surfaced as 6 s timeouts).
lint-daemon-allowlist:
	@python3 scripts/lint_daemon_allowlist.py

lint-py:
	python3 -c "import ast; ast.parse(open('dashboard.py').read()); print('Python syntax OK')"
	ruff check dashboard.py dashboard_claudecode.py clawmetry/

# v0.12.165 shipped clawmetry/static/js/app.js with a missing `}` (PR #753).
# Browsers threw "Unexpected end of input" on first parse, killing every
# function in the bundle and stranding the dashboard on its boot overlay.
# `node --check` is the cheapest possible gate — runs in <100ms per file
# and would have failed the offending PR locally and in CI.
lint-js:
	@if command -v node >/dev/null 2>&1; then \
	    for f in clawmetry/static/js/*.js; do \
	        node --check "$$f" || { echo "JS PARSE FAILED: $$f"; exit 1; }; \
	    done; \
	    echo "JS syntax OK"; \
	else \
	    echo "WARN: node not installed — skipping JS syntax check (CI installs node automatically)"; \
	fi

.PHONY: lint lint-py lint-js lint-daemon-allowlist
