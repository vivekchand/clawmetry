# ClawMetry test suite

## Running locally

Most tests need a running ClawMetry server:

```bash
export CLAWMETRY_URL=http://localhost:8900
export CLAWMETRY_TOKEN=ci-test-token
make test            # full suite
make test-api        # API tests only
make test-e2e        # Playwright browser tests
```

See `Makefile` for the canonical targets.

## CI: OpenClaw available in every job

As of 2026-05-17, GitHub Actions workflows can install OpenClaw
in one step via the composite action in `.github/actions/setup-openclaw`:

```yaml
- uses: ./.github/actions/setup-openclaw
  with:
    version: latest           # or a pinned npm dist-tag/version
    gateway-token: ci-token   # exported as OPENCLAW_GATEWAY_TOKEN
```

After this step:

- `openclaw` is on PATH (`openclaw --version` works).
- `OPENCLAW_GATEWAY_TOKEN` is exported for the rest of the job. Boot the
  gateway yourself with `openclaw gateway --port 18789 --verbose &` if
  the test needs it.
- The global install is cached per-runner; cache key is
  `openclaw-<os>-<version>-v1`, effective TTL is 7 days (GitHub's
  default cache eviction policy).

The `openclaw-boot.yml` workflow is the canonical smoke gate that
proves the action works end to end (install + boot + HTTP probe +
workspace check) on every PR.

### Why this matters for downstream workflows

Until this action landed, `pr-screenshots.yml`, `e2e-nightly.yml`, and
the rest of the E2E suite ran with `OPENCLAW_GATEWAY_TOKEN=""` and no
real agent on the runner. That is the root cause of the recurring
"screenshots only render the public surfaces" complaint: with no token
the dashboard short-circuits to anon mode and never reaches the authed
screens. Workflows that want the authed surfaces should now:

1. `uses: ./.github/actions/setup-openclaw`
2. Read `OPENCLAW_GATEWAY_TOKEN` from the env when starting the
   ClawMetry dashboard process.
