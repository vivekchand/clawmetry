# Sync daemon restart reliability

## Problem and evidence

`clawmetry sync --restart` reported success while leaving an older sync daemon
running. On Linux without a user systemd bus, the service activation failed, but
the fallback treated any `clawmetry.sync` process on the machine as proof that
this user's service was active. This included a daemon running under another
user and a stale daemon in this user's store. The old process then kept its
pre-update plugin registry, so Pro's Physical AI collector did not run and
robot journals were unavailable in ClawMetry.

## Required behavior

- **AC-SYNC-RESTART-001:** `sync --restart` restarts the daemon that owns the
  current user's `~/.clawmetry` store and loads the installed extensions.
- **AC-SYNC-RESTART-002:** A systemd service is reported active only when the
  service manager confirms it; an unrelated process is not service evidence.
- **AC-SYNC-RESTART-003:** Restart detection and shutdown are scoped to the
  current store's recorded PID and verified process identity. A command must
  not stop another user's ClawMetry daemon.
- **AC-SYNC-RESTART-004:** The old daemon receives a graceful stop and drains
  its local event buffer before the new daemon claims the store lock.
- **AC-SYNC-RESTART-005:** If the old daemon cannot stop or the new daemon
  cannot start, the command reports failure instead of claiming success.

## Scope and alternatives

This corrects start, restart and status behavior for the existing local
collector. It does not change the collection interval, event schema, cloud
transport, or UI refresh cadence. Searching all machine processes is rejected:
it crosses user boundaries and does not prove that a service manager owns a
process. Requiring systemd is rejected because supported Linux environments may
not provide a user D-Bus session; detached-process fallback remains supported.

## Design and risks

Use the current user's sync PID record and its start-time identity as the
process source of truth. On Linux, use the service manager for a managed
service; if it is unavailable, restart only that user's recorded daemon and
wait for graceful lock release before starting a replacement. Existing
SIGTERM handling drains the local store. If shutdown exceeds the bounded wait,
return a clear error and preserve the store rather than launching a competing
writer.

The main risks are stale PID records, service-manager races and lock-release
timing. PID start-time validation, service-manager result checks and tests for
another user's unrelated process cover these cases. Revert the CLI change to
restore the prior behavior; no database migration is required.

## Verification

Regression tests cover a failed user-systemd call while another user's daemon
is running, an existing same-user detached daemon, managed-service restart,
graceful stop ordering and a failed restart. Live verification checks that the
new daemon PID owns the store lock, Pro's robotics handler is registered in
that daemon, and an event written by the robot reaches the local Robotics API
without waiting for cloud sync.
