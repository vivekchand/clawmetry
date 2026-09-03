<!--lint disable strong-marker-->

# Review Log: WO-57

**Work Order:** WO-57 — Claude Code native telemetry: instrument command, claude_code.* metric/event/span mapping, session join, status
**Initialized At (UTC):** 2026-09-03T17:25:12Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Round 1

### Requirements Alignment

**Blocking:**

**Advisory:**

### Blueprint Alignment

**Blocking:**

**Advisory:**

### Architecture And Conventions

**Blocking:**

**Advisory:**

### Tests And Build

**Commands run:**

**Blocking:**

**Advisory:**

### User-Facing Verification

**Skipped:** _yes/no_ - _reason if yes_

**Evidence:**

**Blocking:**

**Advisory:**

### Security, Privacy, And Data Safety

**Skipped:** _yes/no_ - _reason if yes_

**Blocking:**

**Advisory:**

### Round 1 Verdict

- Total blocking:
- Total advisory:
- Files reviewed:
- **Verdict:** _APPROVED or CHANGES_REQUESTED_

---

<!-- Subsequent rounds: copy the structure above and increment the round number. -->


## Round 1 (2026-09-03) — two delegates, bucket A (receiver/store) + bucket B (CLI/docs)

Verdict: CHANGES_REQUESTED (both buckets).

Blocking, all fixed in commit 2:
- A1 `_cc_metric` tile push not retry-safe (no `_otlp_seen` gate) — requirements AC .4. Fixed: record id computed first, push gated.
- A2 cache fields named `cache_read`/`cache_write`, unread by anything, and `total: n` inflated the tokens tile — requirements AC .4. Fixed: transcript spelling `cache_read_tokens`/`cache_write_tokens`, `total: 0`, surfaced as `cacheReadTokens`/`cacheWriteTokens` in the OTel usage aggregate.
- B1 single-entry marker let a user-level record claim keys in a project file and let uninstall remove keys from the wrong file — requirements AC .1 / data safety. Fixed: marker keyed by realpath per settings file; uninstall/status refuse files with no record.
- B2 `_read_json` crashed on corrupt settings/marker (JSONDecodeError traceback on `--status`/`--uninstall`) — never crash on bad input. Fixed: strict read for install (refuses, never overwrites), tolerant read elsewhere, `unreadable` surfaced.
- B3 Windows managed-settings path was the legacy ProgramData location Claude Code no longer reads — AC .3. Fixed: ProgramFiles first, ProgramData kept as legacy, `managed-settings.d/*.json` globbed, output states only file-based policy was checked.

Advisory, fixed: A3 cross-batch parent lookup for `blocked_on_user` tool names (store read); A4 Claude Code no longer excluded from span materialization (existing transcript row is left alone by the materializer's own guard); A5 `user_prompt` is a turn boundary on daemon-free sessions only, `api_error`/`api_refusal`/rejected `tool_decision` render as zero-width markers; A6 absent data-point values stored as null; A7 temporality preference pinned to `delta` in the block and cumulative sums kept off tiles; A8 prompt/response text capped at 4000 chars and tagged `content: true`, literal `<REDACTED>` dropped; A9 decoder docstring, `configured: null` when status cannot be asked; B4 realpath write-through for symlinks; B5 non-object `env` refused; B6 explicit-endpoint message; B8 `== "1"` test.

Advisory, not done (stated): B4 read-modify-write has no lock against Claude Code's own saves (window is one JSON dump; comment added). Registry/plist/server-managed policy not checked (output says so).


## Round 2 (2026-09-03) — fresh delegate over both buckets

Verdict: APPROVED. Every round-1 blocking item verified against code (A1, A2, B1, B2, B3), seven targeted probes passed (vanished marker path, deleted env block, legacy marker shape, `query_spans` signature and allowlist, no duplicate session on a daemon machine, protobuf temporality enum, typed-event field namespace).

Advisories, addressed in commit 3: (1) `_dp_value_or_none` on the protobuf path used `HasField("sum")`, which raises for NumberDataPoint, so an absent value became 0; now `WhichOneof("value")` first, per-name guards after, with a protobuf test. (2) `_write_marker` swallowed failures and install still reported success; now returns a bool, surfaced as `marker_written` plus a printed warning, with a test. (4) `OSError` on the settings file read no longer reads as "not valid JSON". (5) `content` tag renamed `has_content` so a future attribute of that name is not clobbered.

Advisory accepted as documented: (3) spans arriving before the daemon's first transcript poll create an OTLP-sourced row that the transcript upsert replaces on the next cycle (blueprint ADR-003 states it).
