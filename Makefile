.PHONY: test test-api test-e2e test-fast dev lint

dev:
	OPENCLAW_GATEWAY_TOKEN=dev-token python3 dashboard.py --port 8900

test: test-api test-e2e

test-fast:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_api.py -v

test-api:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_api.py -v

test-e2e:
	CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=dev-token python3 -m pytest tests/test_e2e.py -v

lint: lint-py lint-js

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

.PHONY: lint lint-py lint-js
