<!--lint disable strong-marker-->

# Review Log: WO-NODE-ACK-001

**Work Order:** WO-NODE-ACK-001 — Preserve the original hosted node action acknowledgement
**Initialized At (UTC):** 2026-10-15T13:50:19Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Round 1: Original-path diagnosis and red-before guards

Author evidence, not an independent approval. Root's actual hosted save delivered one action twice approximately 0.66 seconds apart. An isolated actual LocalStore diagnostic reproduced the same-values case: two acknowledgements (confirmed success, then unconfirmed failure), one retained nonce and all six true preferences unchanged. Result posting was intercepted; no live action was sent.

Six meaningful real-store guards failed before the product edit, including duplicate result ownership, retained expired/malformed duplicate handling, reopen, first failure/interrupted claim, publication loss and concurrency. Evidence is saved at `/tmp/clawmetry-node-qa/node-ack-red.log`. The original path therefore required the approved ownership correction. Factory requirement/design and the saved plan preceded implementation.

**Verdict: CHANGES_REQUESTED on the original implementation.** The product correction and independent subsequent verdicts follow below. Released and hosted verification are pending, not implied by this reproduction.

---

<!-- Subsequent rounds: copy the structure above and increment the round number. -->

## Round 2: Independent cloud and acknowledgement ownership review

Reviewer: `/root/node_cloud`, independent of the implementation author. The initialized Round 1 template above is preserved.

### Requirements and blueprint alignment

Reviewed the approved acknowledgement addendum in requirements `d33e1d0b-43c1-4d3f-8d0d-8de6628d0583`, design `2dffd534-2073-4af2-b943-d6dbed701ee1`, the local implementation plan, and the original Node activity integration contract. All four acknowledgement acceptance criteria are represented by meaningful real-store tests. The implementation preserves bounded claim retention rather than adding a durable receipt or automatic retry contract.

### Architecture, transport and security

Reviewed `clawmetry/sync.py`, `tests/test_node_activity_wiring.py`, `docs/acceptance_criteria.json` and `docs/ac_coverage_baseline.json`. Separately inspected the cloud heartbeat dual-queue merge, durable DELETE/RETURNING action claim, opaque cache write path and action-status reader. Neither transport requires one result per delivery; the browser requires one matching confirmed result per request.

The existing lock now classifies a retained duplicate only after authenticated decryption and exact node/request binding, and before expiry or operation errors can publish a replacement result. A duplicate returns without mutation or acknowledgement. An unclaimed action still requires the original freshness, closed schema, capacity and durable claim checks before mutation. Concurrent callers serialize, original apply/readback failures cannot become success through a duplicate, and the first executor retains result ownership. There is no new dependency, schema, cloud plaintext or independent polling. Existing unknown-result semantics remain deliberate: a crash or lost result upload requires a fresh operator request.

Blocking findings: none. Advisory findings: none.

### Tests and build evidence

Independently ran the source checkout with isolated audit storage, no gateway conftest, and a preinstalled NullHandler to avoid writing test warnings into the live daemon log:

`CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-qa/ack-cloud-independent-audit.db PYTHONPATH=. /tmp/cm-cloud-node918/bin/python -c 'import logging, pytest; logging.getLogger("clawmetry-sync").addHandler(logging.NullHandler()); raise SystemExit(pytest.main(["--noconftest", "-q", "tests/test_node_activity_wiring.py", "tests/test_node_activity.py"]))'`

Result: **63 passed**. This covers real DuckDB persistence, retained changed-body/malformed/expired duplicates, reopen, concurrent delivery, historical review, original failure, incomplete claim, publication loss and fresh-request recovery. Existing authentication, ledger saturation and ledger read failure regressions also pass. `git diff --check` passed. Inspected the author's red-before evidence at `/tmp/clawmetry-node-qa/node-ack-red.log`: six focused regressions failed on the prior implementation because duplicate delivery appended a failure result after the successful original result.

### User-visible verification and delivery boundary

No UI assets changed. Parent's actual hosted save and sanitized audit already establish the production trigger: two deliveries of one action about 0.66 seconds apart, one retained claim, and a duplicate failure replacing the initial acknowledgement. The isolated integration tests validate the correction, but do not establish deployed success. Root retains release inspection and actual hosted preference/review verification; cloud merge/deploy remains held until root supplies the inspected next wheel.

### Verdict

**APPROVED** for the reviewed implementation, test and acceptance-record bucket. Total blocking: 0. Total advisory: 0. Production completion remains pending the authorized release, cloud pin/deploy gates and actual hosted confirmation.

## Round 3: Independent fixture-only follow-up

Reviewer: `/root/node_cloud`. Reviewed the final test-only delta adding `logging` and the autouse `isolated_sync_environment` fixture. Pytest applies scratch home/audit paths and a temporary NullHandler before dependent fixtures import the daemon; monkeypatch restores the previous environment and logger handlers afterward. This prevents test warnings reaching the live daemon log and does not alter product execution, relay behavior or assertions. Product code is unchanged from Round 2.

Independently ran the wiring file through ordinary `python -m pytest --noconftest` without the external NullHandler launcher: **27 passed in 0.88 seconds**. `git diff --check` passed. **APPROVED**, with no blocking or advisory findings. The release and actual hosted confirmation boundary from Round 2 remains unchanged.

## Parent verification note

Root independently inspected the minimal ordering/return diff and confirmed it matches the approved contract. Root also independently ran the isolated wiring suite: 27 passed. The complete implementation review is the independent cloud delegate's verdict above, rather than author self-review.
