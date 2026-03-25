# Fix: Skip OTP verification on Docker/container reconnects

## Problem

When running `clawmetry connect --key cm_xxx --foreground` in a Docker container, the daemon requires OTP email verification **every time** it starts. This makes it impossible to auto-restart the sync daemon in Docker/headless environments because:

1. `_verify_key_ownership()` is called whenever `--key` is passed
2. In containers without a TTY, OTP input fails immediately
3. Even with a PTY, a new OTP email is sent on every restart

## Fix

### 1. Skip OTP for already-verified keys

In `_cmd_connect()`, before calling `_verify_key_ownership()`, check if the config already has the same API key saved. If so, this is a reconnect/restart — not a new connection — and OTP can be safely skipped.

- **First connect** → full OTP verification (secure)
- **Restart with same key** → skip OTP (already verified)
- **Different key** → require OTP (new connection)

### 2. Graceful systemd fallback in containers

`_register_systemd()` now checks if `systemctl` is available before calling it. In Docker containers without systemd, it falls back to `_start_subprocess()` instead of failing.

## Testing

- `clawmetry connect --key cm_xxx` — first time: OTP prompt as before ✅
- `clawmetry connect --key cm_xxx --foreground` (restart in Docker) — skips OTP ✅
- `clawmetry connect --key cm_NEW_KEY` — requires OTP ✅
- Linux container without systemd — falls back to subprocess ✅
