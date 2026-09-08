# Development

## Run from source

```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

See [ARCHITECTURE.md](../ARCHITECTURE.md) for the layout and
[CONTRIBUTING.md](../CONTRIBUTING.md) for the contribution flow.

## v2 frontend

The v2 React app lives in `frontend/` and is served at `/v2` when the Flask
server is started with v2 enabled.

Use two terminals while developing:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

Open `http://localhost:5173/v2/`. Vite proxies `/api` requests to
`http://localhost:8900`, so the React app can talk to the local Flask server
without extra CORS setup.

To build the bundle that ships with the Python package:

```bash
cd frontend
npm run build
```

The production bundle is written to `clawmetry/static/v2/dist/`.

## CLI options

Most people don't need any config. ClawMetry auto-detects your workspace, logs, sessions, and crons.

If you do need to customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

All options: `clawmetry --help`

## Requirements

- Python 3.8+
- Flask (installed automatically via pip)
- At least one agent runtime on the same machine (see [compatibility.md](compatibility.md)), or mounted volumes when running in [Docker](DOCKER.md)
- macOS, Linux or Windows

## Testing

```bash
make test        # full suite (needs a running server)
make test-api    # API tests only
make test-e2e    # Playwright E2E
make lint        # syntax + lint
```

Cross-browser E2E runs on BrowserStack.
Cloud deploys: see the [Cloud Testing Guide](CLOUD_TESTING.md).
