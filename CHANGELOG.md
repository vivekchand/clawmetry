## [0.12.79] — 2026-03-26

### Added
- feat: Model Attribution tab (GH #300/#305) — dedicated `Models` nav tab with turn distribution bars, primary vs fallback labelling, cost-per-model, per-session model table, model switch event timeline, and configurable fallback rate alert threshold; backend `/api/usage/model-attribution` already served fallbackRate/fallbackAlert; this PR wires it to a full standalone UI page

## v0.12.63 (2026-03-22)
- fix: robust Ollama detection -- PATH fallback + HTTP ping to localhost:11434
- feat: sync daemon heartbeat includes ollama status (installed, running, models)

## [0.12.71] — 2026-03-22

### Fixed
- Security posture scan timeout — JS client timeout increased 8s → 25s, gateway API timeout 5s → 8s (fixes "Posture scan failed: timeout" error)

### Added
- Screenshots of all OSS dashboard tabs in README (Brain, Overview, Flow, Tokens, Memory, Security)

## [0.12.69] — 2026-03-22

### Fixed
- Updated logo to new lobster SVG, embedded as base64 data URI (works offline)
- Brain stream now shows full content — removed single-line ellipsis truncation, wraps by default

## [0.12.68] — 2026-03-22

### Fixed
- Remove duplicate type filter pills in Brain tab — type chips now use a dedicated container with `innerHTML =` instead of `+=`
- Remove non-working Graph view toggle from Brain tab — live list feed is now the default with no toggle

## [0.12.66] — 2026-03-22

### Removed
- Agents, Context, and Channels tabs from OSS dashboard (simplifies to 7 core tabs)
- Backend routes: `/api/subagents`, `/api/context-inspector`, `/api/channel-metrics`

### Fixed
- CI: removed stale tests for deleted routes

## [0.12.65] — 2026-03-22

### Fixed
- Remove stale tests for deleted API routes (`/api/channel-metrics`, `/api/subagents`, `/api/context-inspector`)

## [0.12.64] — 2026-03-22

### Removed
- **Agents tab** — removed sub-agent gantt/timeline view (confusing, stale sessions with no active/idle filter)
- **Context tab** — removed workspace context inspector (not actionable for most users)
- **Channels tab** — removed per-channel OTLP metrics tab (requires OTLP setup, shows empty state for most)
- Corresponding backend API routes: `/api/subagents`, `/api/subagent/<id>/activity`, `/api/context-inspector`, `/api/channel-metrics`
- OTLP queue lane depth metrics storage (channels-only feature)

Simplifies OSS dashboard to 7 core tabs: **Flow, Brain, Overview, Crons, Tokens, Memory, Security**

## [0.12.60] — 2026-03-19

### Added
- **Channels tab**: per-channel observability with webhook error rates, message duration p50/p99, queue depth, and cost attribution grouped by channel
- OTLP status indicator in `clawmetry status` CLI command with restart hint
- New `/api/channel-metrics` endpoint for per-channel OTLP metrics

## [0.12.59] — 2026-03-19

### Fixed
- Add `/api/memory` and `/api/flow` route aliases for E2E health checks
- Recent-first sync strategy for Brain feed

## [0.12.57] — 2026-03-17

### Added
- Click-to-expand brain stream events (click any row to see full detail text)
- Hover highlight on brain event rows

## [0.12.56] — 2026-03-17

### Fixed
- Initial sync no longer hangs on large session directories (batch size 10 → 200, 5K event cap per cycle, newest-first, incremental state saving)

## [0.12.55] — 2026-03-17

### Fixed
- Store raw passphrase in config instead of derived hash (show what the user typed, not gibberish)

## [0.12.54] — 2026-03-17

### Fixed
- Support arbitrary passphrases as encryption keys (auto-derives 256-bit AES key via SHA-256)
- Existing configs with raw passphrases self-heal on next sync

## [0.12.53] — 2026-03-17

### Fixed
- NameError crash on encryption key prompt (`_input` not defined in `_cmd_connect`)

## [0.12.52] — 2026-03-17

### Improved
- Always show encryption key prompt during onboard and connect (full transparency)
- Existing key shown masked with option to keep or replace

## [0.12.51] — 2026-03-17

### Added
- Prompt for custom encryption key during `clawmetry connect` (press Enter to auto-generate)

---

## [0.12.45] — 2026-03-15

### Fixed
- `clawmetry connect --key` no longer crashes in non-interactive shells (SSH, CI/CD, Docker)
- Sync daemon retries on 401/503 (cloud cold-start resilience)

---

## [0.12.44] — 2026-03-15

### Fixed
- Sync daemon `_post()` retries once on 401/503 responses (cloud cold-start resilience)
- Prevents sync daemon from permanently skipping sessions when Cloud Run returns transient auth errors

---

## [0.12.43] — 2026-03-15

### Fixed
- `sync_crons` now sends full schedule object, state (lastRunAtMs, lastDurationMs, nextRunAtMs, lastError, consecutiveFailures), and task description to cloud
- Maps `consecutiveErrors` field (OpenClaw's actual field name) to `consecutiveFailures` for renderer compatibility

---

## [0.10.11] — 2026-02-28

### Fixed
- Dark mode now correctly forced on load — initTheme() was overriding body dark mode with localStorage light default

---

## [0.10.10] — 2026-02-28

### Changed
- Dark mode always on, remove theme toggle (merged via PR #37)

---

## [0.10.9] — 2026-02-28

### Changed
- Dark mode is now the permanent default — removed theme toggle button

---

## [0.10.8] — 2026-02-28

### Fixed
- Auth check runs before boot sequence — login overlay shows immediately if token invalid/missing
- Boot overlay no longer covers the login prompt on stale token
- Overview request storm on boot: removed duplicate loadAll() call, added in-flight guard

---

## [0.10.7] — 2026-02-28

### Fixed
- Port conflict check moved to daemon mode only — foreground mode was false-positive blocking all ports

---

## [0.10.6] — 2026-02-28

### Fixed
- Port conflict: only kill our own stale clawmetry process, not arbitrary apps on the same port
- Clear error message if another app is already using the port

---

## [0.10.5] — 2026-02-28

### Fixed
- Installer now auto-starts daemon immediately after install via full binary path (works with curl|bash)

---

## [0.10.4] — 2026-02-28

### Fixed
- Hide `clawmetry connect` command from help (cloud integration not yet production ready)

---

## [0.10.3] — 2026-02-28

### Fixed
- Architecture diagram boxes broken due to emoji double-width characters — switched to pure ASCII +---+ style

---

# Changelog

## [0.11.0] - 2026-03-01

### Added
- Brain tab: unified real-time activity stream for main agent + all sub-agents
- Brain tab: filter pills with glow highlight, chart filtering by agent
- Brain tab: `/api/brain-history` + `/api/brain-stream` endpoints
- Brain tab: spinner feedback on pill click
- Nav reorder: Flow | Overview | Brain | Crons | Tokens | Memory

### Fixed
- Windows CI: UTF-8 encoding, stdout handling
- E2E tests: auth token injection per-page, boot overlay dismissal
- Sub-Agents tab removed from nav


All notable changes to ClawMetry are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [0.10.1] — 2026-02-28

### Fixed
- Hide OTLP "not available" error from startup banner — only shows when otel is actually installed

---

## [0.10.0] — 2026-02-28

### Added
- **18 channel live popups** — all OpenClaw channels now show live message bubbles in Flow:
  iMessage (chat.db), WhatsApp, Signal, Discord, Slack, Webchat, IRC, BlueBubbles,
  Google Chat, MS Teams, Mattermost, Matrix, LINE, Nostr, Twitch, Feishu, Zalo
- **Cost Optimizer** — llmfit integration detects local models runnable on your hardware;
  Apple Metal speed correction; task-level savings recommendations; ollama pull commands
- **Full test suite** — pytest API tests, Playwright E2E, BrowserStack cross-browser tests
- **CI matrix** — Linux/macOS/Windows on every PR via GitHub Actions
- **BrowserStack CI** — Chrome, Firefox, Safari, Edge on merge to main
- **Auto-publish workflow** — `git tag vX.Y.Z && git push --tags` publishes to PyPI
- **Makefile** — `make dev`, `make test-fast`, `make test`, `make lint`
- `CHANGELOG.md` — this file

### Fixed
- Gateway token not found on restart (`openclaw.json` missing from config search path)
- New channels (iMessage etc.) missing from `KNOWN_CHANNELS` list
- Overview page channel nodes not rendering (getElementById on unappended DOM clone)
- Unconfigured channels (Signal/WhatsApp) showing in Flow when not in config
- `grep`/`tail`/`pgrep` subprocess calls replaced with pure Python (Windows compatibility)
- `/tmp/openclaw` hardcoded log paths replaced with `_get_log_dirs()` cross-platform helper
- Windows UTF-8 crash — 🦞 emoji in BANNER failed on cp1252 encoding
- `setup.py` reading `dashboard.py` without `encoding="utf-8"` (Windows pip install failure)

### Changed
- Channel nodes in Flow now hide automatically if not configured in `openclaw.json`
- Only channels actually set up appear in Flow/Overview visualizations

---

## [0.9.17] — 2026-02-23

- Gateway auth theme fix
- Context inspector spec branch
- Various stability improvements

---

## [0.9.x] — 2026-02-13 to 2026-02-23

- Initial public release
- Flow visualization, Overview, Sessions, Crons, Usage, Logs, Memory, Transcripts tabs
- Telegram channel support
- Sub-agent tracking
- Cost tracking and budget alerts
- OTLP receiver (experimental)

## [0.10.2] — 2026-02-28

### Added
- Full CLI with subcommands: `clawmetry start/stop/restart/status/connect/uninstall`
- Daemon support: launchd (macOS) + systemd (Linux) — auto-starts on login
- Architecture overview on startup matching clawmetry.com/how-it-works
- `clawmetry --help` and `clawmetry help` 
