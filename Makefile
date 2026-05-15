.PHONY: test test-api test-e2e test-fast test-e2e-duckdb dev lint lint-daemon-allowlist

dev:
	OPENCLAW_GATEWAY_TOKEN=dev-token python3 dashboard.py --port 8900

test: test-api test-e2e test-e2e-duckdb

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
