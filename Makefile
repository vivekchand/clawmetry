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

lint:
	python3 -c "import ast; ast.parse(open('dashboard.py').read()); print('Syntax OK')"
	ruff check dashboard.py || true
