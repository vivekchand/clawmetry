# Migration checklist — Move proprietary code into clawmetry-pro

Follow this checklist when extracting paid/enterprise code from the OSS repo into clawmetry-pro.

1. Define entitlement surface
   - Finalize `entitlements.*` API (types, behavior) in OSS and add minimal unit tests.
   - Add feature flags in OSS using `entitlements.allows_feature(...)` guard calls.

2. Create clawmetry-pro package
   - Move runtime adapters, license server, billing, advanced analytics, and cloud relay into `clawmetry-pro/`.
   - Implement entry point via `clawmetry.extensions` or setuptools entry_points to register the extension when installed.

3. Provide mocks and SDK
   - Add `clawmetry-pro/mock_pro.py` for CI/local smoke tests.
   - Publish a lightweight SDK or interface package to allow integration tests without secrets.

4. CI and build changes
   - Ensure OSS CI builds and tests without `clawmetry-pro` installed.
   - Add a separate CI workflow in `clawmetry-pro` repo that depends on OSS release tags.
   - Add smoke tests in OSS that run when `clawmetry-pro` is present (use mocks otherwise).

5. Documentation & examples
   - Update FLYWHEEL.md and AGENTS.md with the split and extension install instructions.
   - Add a short public README (already present) and link to migration checklist.

6. Security & compliance
   - Sanitize any example configs (no secrets in repo).
   - Produce a security summary and testing notes; include contact for audit requests.

7. Release & packaging
   - Publish `clawmetry-pro` as a separate package/wheel; integrate with license server if applicable.
   - Update OSS to detect and enable pro features when the extension is installed.

Notes
- Keep commits small and atomic. Use the migration checklist as a PR template for each major move.
- Test all changes against the local dev flow `make dev` and `make test-api` before merging.
