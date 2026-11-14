# Built-in OSS Physical AI adapter for Jumper

## User requirements and scope

The user clarified that all adapter code must live in vivekchand/clawmetry and ship in the ordinary `pip install clawmetry && clawmetry` path. The separate Mizu project is only for the companion simulation, scenes, robot skills and video. Jumper uses the same common observation/governance architecture as other supported digital or physical agents; no external adapter package, Pro license or simulator dependencies are required for its built-in observation.

## Reuse and architecture

Fresh isolated OSS worktree on f7a4428abc20e895af95187a17f69a6267a3e357. Preserve dirty user checkout and paid adapters. Reuse the public robotics.v1 journal, bounded asynchronous JournalWriter, daemon ingestion on local_store's owned DuckDB handle, local query proxy, encrypted snapshots, extension navigation and shared incident_alerts preferences/receipts. Do not create another DuckDB store or generic plugin for this built-in adapter. Never copy private Pro implementations.

- `clawmetry/physical_ai/`: generic shared journal/monitor/task gate APIs and built-in `adapters/jumper.py` state normalization and observer bridge. Stdlib-only imports. Simulator execution remains in Mizu demo project.
- Extend existing free projection with explicit Jumper source kinds and generic queries/snapshot while preserving Asimov-only API/source filtering and old data.
- `routes/physical_ai.py`, template/static JS/CSS: free shared Physical AI view, bounded daemon queries, source-specific labels, activity/decision/incident history, no raw-file reads in handlers. Built-in navigation works without Pro. Retain paid UI link when present.
- Add ordinary CLI dispatch for Jumper observe/import/inspect as appropriate; ordinary dashboard startup auto-discovers supported robotics journals. Unpublished internal robot state cannot be inferred: clearly explain telemetry bridge/connection needs and do not probe robot control endpoints or auto-install SDKs.
- Task decisions and monitors feed robotics evidence plus shared incident_alerts, with user channel preferences, delivery receipts and privacy preserved. No direct process-kill semantics for physical machines. Simulator controls stay opt-in; hardware controls require verified supported transport and are not invented.
- Mizu project imports built-in OSS APIs and contains only scenes, simulation host, companion skills, web demo and film tooling. Rewrite its PR/title/readme to that actual scope; no separate install required by a Jumper owner for ClawMetry support.

## Steps

1. Read existing shared journal/projection/daemon/query/alert/nav contracts, record exact supported interfaces and acceptance.
2. Parallel: (A) generic projection/query/snapshot backward-compatible support; (B) public Physical AI route/UI/navigation; (C) built-in observer/guard/monitor/CLI and real publisher-to-daemon evidence path. Different owners edit assigned files.
3. Port actual native Mizu runs to built-in APIs, verify observer -> journal -> daemon writer -> DuckDB -> routes -> rendered UI, decision/refusal/native receipt and shared alert delivery. No synthetic seeds for claimed working pipeline.
4. Qualify malformed/stale/duplicate inputs, no Pro imports or MuJoCo/ONNX required, free and paid coexistence, CPU bounded discovery/polling, existing Asimov regressions and shared query contracts.
5. Ship OSS PR/green required CI, separate [RELEASE] PR, inspect public wheel for adapter, deliver cloud snapshot/freeview parity and verify served artifact. Update Mizu demo source imports and docs, video links and public playground from the real released integration.
6. Independent reviews with fixes recorded, useful local/hosted screenshots, actual version/provenance and limitations. Do not claim hardware qualification, arbitrary attacks prevented, hard containment or delivered phone alerts without direct evidence.

## Pre-merge upgrade correction

An earlier daemon can consume an unsupported Jumper header to EOF before the adapter is installed. Add a durable canonical source-support token and ignored-source classification ledger without changing the legacy cursor columns. Replay once on a missing or changed registry token, preserving bounded batches, restart progress and transaction rollback. Verify an actual legacy cursor/database reopen, multi-pass replay, source-registry expansion, unchanged unsupported no-open scans, Asimov/event/notification deduplication and interrupted upgrade retry. Independent store review is required before the next push.
