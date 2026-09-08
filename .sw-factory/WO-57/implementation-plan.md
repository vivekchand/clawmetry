# WO-57 Implementation Plan: Claude Code native telemetry

Requirement: a4bd3c7e-8bb9-4b80-92c7-d74dbe0fd504 (AC-RSO-CCT-001.1..9)
Blueprint: 9ae95403-7668-416b-bf67-db4eca150ef5
Branch: cc-native-otel (worktree off origin/main 0f13ef398)

## Facts that shape the design (verified in-tree)

- Claude Code default `service.name` is `claude-code` (binary string check, v2.1.259); `_otlp_service_name_to_agent_type` slugifies it to `claude_code`.
- The daemon stamps transcript sessions as `claude_code:<uuid>` (`sync.py:10294/14853`); OTel `session.id` is the bare uuid. Join = prefix.
- `put_otlp_batch` treats a session as daemon-owned when it has any `events` row whose id does not start with `otlp:`; it then drops ALL OTLP events for that session.
- `_process_otlp_metrics` only knows `openclaw.*` names; `otlp_json.decode` rejects `metrics` (501) -> Claude Code metrics need JSON metric shims to work on a vanilla install.
- dashboard.py defines the OTLP handlers twice; the SECOND is live (11349 metrics, 11575 _otel_to_row, 11861 traces, 12234 logs). Only the live copies are edited; the dead copies get a DEAD COPY marker where missing.
- Claude Code has no default OTLP protocol; `http/json` is what we write.

## Steps

1. `docs/enterprise.md`, `docs/OPENTELEMETRY.md`: fix variable name, show the exact block (AC .9).
2. `clawmetry/otlp_json.py`: add `_NumberDataPoint`, `_Metric` (sum/gauge/histogram duck-typed `HasField` + `.data_points`), `_ScopeMetrics`, `_ResourceMetrics`, `_MetricsRequest`; `decode(kind="metrics")` returns it. `dashboard._otlp_request` already routes JSON to this module; `_get_data_points`/`_get_dp_value`/`_get_dp_attrs` duck-type through.
3. `dashboard.py` live `_process_otlp_metrics`: map `claude_code.token.usage` (type input/output/cacheRead/cacheCreation), `claude_code.cost.usage`, `claude_code.session.count`, `claude_code.lines_of_code.count`, `claude_code.commit.count`, `claude_code.pull_request.count`, `claude_code.active_time.total`, `claude_code.code_edit_tool.decision` -> metrics cache (tokens with cache fields; cost) + `otlp_records` ledger rows (event_name = metric name, attributes carry the data point). (AC .4)
4. `dashboard.py` live `_process_otlp_logs`: session-id prefixing for `claude_code` emitters; new event suffix sets -> typed events `permission_mode_changed`, `api_refusal`, `api_error`, `mcp_server_connection`, `auth`, `user_prompt`, `assistant_response`, rejected `tool_decision`; `_otlp: true` provenance. (AC .5)
5. `dashboard.py` live `_otel_to_row` + `_process_otlp_traces`: read `cache_read_tokens`/`cache_creation_tokens`/`tool_name`; prefix session id for claude_code; exclude claude_code from `materialize_otlp_sessions`; `blocked_on_user` spans -> `waiting_on_user` event with duration so turn anatomy / session views can sum it. (AC .6)
6. `clawmetry/local_store.py` `put_otlp_batch`: daemon-owned rule drops only `tool_call`/`tool_result`/`llm_call` duplicates; OTel-only event types pass through. (AC .7)
7. `clawmetry/instrument_claude.py` + `cli.py` fast path + parser: install/uninstall/status, probe, managed lock refusal, marker `~/.clawmetry/hooks_installed.json["claude_code_otel"]`. (AC .1, .2, .3)
8. `routes/meta.py` `/api/otel-status` `claude_code` block; `cli.py` status line + `_status_snapshot` key; `local_store.latest_otlp_record_ts(service_name)` allowlisted in `routes/local_query._DAEMON_METHODS`. (AC .8)
9. `routes/turn_anatomy.py`: sum `waiting_on_user` events per turn as `waiting_on_you_ms`. (AC .6 per-turn)
10. Tests: `tests/test_instrument_claude.py`, `tests/test_otlp_claude_code_signals.py`, doc test; AC manifest + baseline; CHANGELOG.
