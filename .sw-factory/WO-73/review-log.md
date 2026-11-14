# Independent OSS seam review

## Round 1: detailed robotics RPC allowlist and bearer boundary

Verdict: APPROVED after one corrected security finding. Reviewer cloud_ci did not
author or edit the four implementation/test files.

The initial change guarded only mutations. Independent actual Pro/plugin tests
reproduced all eight detailed reads accepting forged operator=True on the
ordinary dashboard-mounted internal Blueprint. The author corrected the exact
allowlist so all eight reads and four writes require the actual daemon bearer
before obtaining the store. No wildcard operation, raw SQL, actuator operation,
paid implementation, or new cloud relay query shape is exposed. Legacy read
behavior remains unchanged; entitlement and unavailable results remain plugin
owned. Actual daemon lifecycle and bearer ownership remain unchanged.

Independent exact changed test files:131 passed. The real Pro daemon HTTP helper,
private detail/artifact ACL, all12 forged-operator denial cases and normal legacy
operations also passed within the qualified full robotics run:664 passed with11
existing or optional dependency skips. No model, cloud, credential or robot call
was made. Evidence and exact source hashes:
/private/tmp/clawmetry-whitebox-oss-independent-review.json.

A broader existing local_server_proxy test file produced four failures only in
cleanup calls to _cleanup_discovery_file, which is absent from baseline HEAD;
133 tests in that combined run passed. This pre-existing test/source mismatch is
outside these four diffs and is reported to the primary agent, not waived or
claimed green. No tests were weakened or skipped to obtain this verdict.
