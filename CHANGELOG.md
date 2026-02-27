# Changelog

All notable changes to ClawMetry are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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
