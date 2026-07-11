# MOAT Event Shapes

This manifest is the source of truth for synthetic event shapes used by the
MOAT suite. Every synthetic event type below must have a live-fixture sibling
so OpenClaw event-shape drift cannot be hidden by synthetic-only tests.

| event_type | synthetic_test_file | live_fixture_test_file | last_verified_date |
|---|---|---|---|
| agent.heartbeat | tests/test_moat_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| message | tests/test_moat_cloud_roundtrip_e2e.py, tests/test_moat_cloud_sync_e2e.py, tests/test_moat_cross_repo_version_skew.py, tests/test_moat_regression_1129.py, tests/test_moat_send_message_e2e.py, tests/test_moat_tier1_daemon_proxy_sweep.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| model.completed | tests/test_moat_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| prompt.submitted | tests/test_moat_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| session.ended | tests/test_moat_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| session_start | tests/test_moat_send_message_e2e.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| tool_call | tests/test_moat_regression_1129.py, tests/test_moat_send_message_e2e.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| test.crash_recovery | tests/test_moat_daemon_crash_recovery.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-20 |
| trace.artifacts | tests/test_moat_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |

## Cloud-sync roundtrip coverage

The encrypted upload → cloud cache → dashboard decrypt arc is covered by
`tests/test_moat_cloud_roundtrip_e2e.py` (5 hermetic tests, wired into CI
since 2026-05-17, no live cloud infra required):

| Test | Contract locked in |
|------|--------------------|
| `test_envelope_shape_matches_documented_contract` | `{key, ttl_s, blob}` cross-repo envelope; cache key format; no plaintext leaks |
| `test_mock_cloud_receives_and_stores_ciphertext` | Heartbeat POST delivers ciphertext to mock cloud; stored under correct key |
| `test_stored_ciphertext_decrypts_to_original_events` | AES-256-GCM roundtrip; decrypted payload matches v3 event shape + content |
| `test_cloud_brain_endpoint_serves_blob_back` | `/api/cloud/brain?key=…` returns blob with correct `_source`/`_shape` fields |
| `test_dashboard_client_decrypt_reproduces_original` | Served blob decrypts byte-for-byte to what the daemon originally encrypted |

Resolves the P0 gap tracked in issue #1456.
