# Verified source evidence

Actual official Jumper native35-second replay through the built-in main package, with an unmodified pinned upstream and official imported tabletop scene. The host supplies22 named measured hinge positions/velocities; torque is unavailable. No reset or per-frame pose teleport.

- Shared run: `535dbf83af5849969f3e3d34d266d72d`
- 7,000 control steps, all finite, zero resets; measured minimum full-body margin0.3102791896m; maximum tilt10.253523883degrees.
- All366 events arrived:351 observations,3 requests,3 taskdecisions,6 nativecontrollerreceipts,1 declined-task incident, start/end. Zero journal drops/errors, fully flushed.
- Actual daemon journal worker in a separate process discovered the source, persisted the complete run to its owned scratch DuckDB. Dashboard was forced into normal `_ProxyStore` and read via authenticated localhost RPC; no handler file reads or second writer.
- Actual desktop and390px browser rendered22 joints, clearance, decisions and receipts with zero JavaScript errors and no horizontal overflow. Local screenshot/report paths are in context.md, no raw user data or credentials are committed.
- Generic snapshot11,474bytes includes bounded traces; legacy Asimov APIs stay filtered. Native incident delivery disabled via isolated preferences for this replay; shared preference, receipt and cooldown behavior has separate focused integration tests. No phone-delivery claim.
- Clean candidate wheel installs into freshvenv with no clawmetry_pro, MuJoCo, NumPy or ONNXRuntime; observer imported and wrote/flushed a named hardware-frame journal. Wheel contains physical_ai package, routes and static/template assets. Candidateversion is not a publishedrelease claim.

Independentreviews: root/observer/UI approved by cloud_guard_review; store/query/snapshot/alerts approved round2 by runtime_gate_diagnosis after strictcursor fix. Current sourcefiles are complete; public release/cloud/live verification remains pending and will be recorded separately.

## Source support upgrade qualification

A previous collector can consume an unsupported Jumper header to EOF. The new persistent support-registry ledger causes one bounded replay per file when support changes, including old databases with no ledger. Five new regression cases cover a real DuckDB close/reopen after a legacy EOF cursor, restart midway through one-line replay batches, registry expansion with existing Asimov/Jumper evidence and incident deduplication, unchanged unsupported sources that are not opened even after body append, transaction failure/retry, and inode replacement or truncation. The focused store, legacy journal/daemon, query-contract and authenticated RPC suite passes 133 tests in 12.04 seconds.

Upgrade cost is a bounded re-read of retained journals, not a new polling loop. No source file is rewritten. Existing event identities suppress duplicate events and notifications. Registry support and cursor progress commit in the same transaction, so an interrupted batch retries. Missing historical segments cannot be recovered; hardware performance and phone delivery are outside this qualification. Independent review by runtime_gate_diagnosis is approved in review-log.md Round 3, including 121 passing tests, one optional skip and a separate incident-before-commit rollback/retry probe that sent no duplicate notification.

The parent also qualified the actual native replay journal above against a scratch database with a deliberately simulated legacy EOF cursor and absent support ledger. A separate upgraded daemon recovered all 366 actual source records and 22 named joints. The dashboard used authenticated `_ProxyStore` reads; desktop and 390px mobile views had zero JavaScript errors. The bounded snapshot was 11,476 bytes. Report and screenshots remain local at `/private/tmp/jumper-upgrade-native-proof/`, with the qualifier at `/private/tmp/qualify_jumper_upgrade.py`. The old cursor state was simulated; the recovered journal was captured from the actual MuJoCo run. This does not establish hardware performance or phone delivery, which was disabled for the qualification.

The parent inspected the CI visual bot's desktop Logs and mobile Brain before/after pairs. The observed differences were the intended Physical AI navigation and header reflow plus changing log-stream content. No newly blank screen or obscured content was found in those inspected pairs.
