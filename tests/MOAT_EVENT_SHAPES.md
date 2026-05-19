# MOAT Event Shapes

This manifest is the source of truth for synthetic event shapes used by the
MOAT suite. Every synthetic event type below must have a live-fixture sibling
so OpenClaw event-shape drift cannot be hidden by synthetic-only tests.

| event_type | synthetic_test_file | live_fixture_test_file | last_verified_date |
|---|---|---|---|
| agent.heartbeat | tests/test_moat_e2e_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| message | tests/test_moat_cloud_roundtrip_e2e.py, tests/test_moat_cloud_sync_e2e.py, tests/test_moat_cross_repo_version_skew.py, tests/test_moat_e2e_regression_1129.py, tests/test_moat_send_message_e2e.py, tests/test_moat_tier1_daemon_proxy_sweep.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| model.completed | tests/test_moat_e2e_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| prompt.submitted | tests/test_moat_e2e_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| session.ended | tests/test_moat_e2e_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| session_start | tests/test_moat_send_message_e2e.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| tool_call | tests/test_moat_e2e_regression_1129.py, tests/test_moat_send_message_e2e.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
| trace.artifacts | tests/test_moat_e2e_regression_1129.py | tests/test_moat_live_openclaw_e2e.py | 2026-05-18 |
