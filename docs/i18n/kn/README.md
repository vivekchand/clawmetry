<!-- i18n-src:8f42d460a973 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **14 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 10. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಆದೇಶ. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ, ಮತ್ತು ಮುಗಿಯಿತು.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry, OpenClaw ಗಾಗಿ ಅಬ್ಸರ್ವಬಿಲಿಟಿಯಾಗಿ ಪ್ರಾರಂಭವಾಯಿತು, ಮತ್ತು ಈಗ ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್**ಅನ್ನು ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ಅಳೆಯುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿ ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಅನ್ನೂ ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತವಾಗಿವೆ; ಇತರ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಸಕ್ರಿಯಗೊಳ್ಳುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಬದಲಾಯಿಸಿ, ಮತ್ತು ಪ್ರತಿ ಟ್ಯಾಬ್ — ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಟೂಲ್‌ಗಳು, ಟ್ರೇಸ್‌ಗಳು — ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರುಸ್ಕೋಪ್ ಆಗುತ್ತದೆ. ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ, ಟಿಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, `/api/entitlement` ಆಕಾರ, ಮತ್ತು `clawmetry license` CLI ಗಾಗಿ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **Flow** — ಚಾನೆಲ್‌ಗಳು, ಬ್ರೈನ್, ಟೂಲ್‌ಗಳ ಮೂಲಕ ಹರಿಯುವ ಸಂದೇಶಗಳನ್ನು ಮತ್ತು ಹಿಂತಿರುಗುವುದನ್ನು ತೋರಿಸುವ ಲೈವ್ ಅನಿಮೇಟೆಡ್ ಡಯಾಗ್ರಾಮ್
- **Overview** — ಆರೋಗ್ಯ ತಪಾಸಣೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಷನ್ ಎಣಿಕೆಗಳು, ಮಾದರಿ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ಸಾಪ್ತಾಹಿಕ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾದರಿ, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಷನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ನಿಗದಿತ ಕೆಲಸಗಳು
- **Logs** — ಬಣ್ಣ-ಕೋಡ್ ಮಾಡಿದ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಷನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ಮಾರ್ಗ ನಿರ್ದೇಶನ
- **Approvals** — ವಿನಾಶಕಾರಿ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, DB ಬದಲಾವಣೆಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಸ್ಥಾಪನೆಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಒಂದೇ-ಕ್ಲಿಕ್ ಸಹಿಯ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

### 🧠 Brain — ಲೈವ್ ಏಜೆಂಟ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ಟೋಕನ್ ಬಳಕೆ ಮತ್ತು ಸೆಷನ್ ಸಾರಾಂಶ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ರಿಯಲ್-ಟೈಮ್ ಟೂಲ್ ಕರೆ ಫೀಡ್
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ಮಾದರಿ ಮತ್ತು ಸೆಷನ್ ಪ್ರಕಾರ ವೆಚ್ಚ ವಿಭಜನೆ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ವರ್ಕ್‌ಸ್ಪೇಸ್ ಫೈಲ್ ಬ್ರೌಸರ್
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ಭಂಗಿ ಮತ್ತು ಆಡಿಟ್ ಲಾಗ್
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, Slack / Discord / PagerDuty / Email ಗೆ ವೆಬ್‌ಹುಕ್‌ಗಳು
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಕೈಬರಹದ ಸಹಿಯ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ; ನೀತಿ-ಬೆಂಬಲಿತ ರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ಸ್ಥಾಪನೆ

**ಒಂದೇ-ಲೈನರ್ (ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**ಮೂಲದಿಂದ:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ಫ್ರಂಟ್‌ಎಂಡ್ ಡೆವಲಪ್‌ಮೆಂಟ್

v2 React ಆ್ಯಪ್ `frontend/` ನಲ್ಲಿ ಇರುತ್ತದೆ ಮತ್ತು v2 ಸಕ್ರಿಯಗೊಳಿಸಿ Flask
ಸರ್ವರ್ ಆರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಸೇವೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ.

ಅಭಿವೃದ್ಧಿ ಮಾಡುವಾಗ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ತೆರೆಯಿರಿ. Vite `/api` ವಿನಂತಿಗಳನ್ನು
`http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಆ್ಯಪ್ ಹೆಚ್ಚುವರಿ
CORS ಸೆಟಪ್ ಇಲ್ಲದೆ ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಸಾಗಿಸುವ ಬಂಡಲ್ ಅನ್ನು ನಿರ್ಮಿಸಲು:

```bash
cd frontend
npm run build
```

ಉತ್ಪಾದನಾ ಬಂಡಲ್ ಅನ್ನು `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲಾಗುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಅಲ್ಲದೆ ಅನೇಕ AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಗಮನಿಸುತ್ತದೆ. ಪ್ರತಿ OpenClaw-ಅಲ್ಲದ ರನ್‌ಟೈಮ್ ಒಂದು ಮೀಸಲಾದ ರೀಡರ್ ಅಡಾಪ್ಟರ್‌ಅನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಅದು ಅದರ ನೇಟಿವ್ ಸೆಷನ್ ಫಾರ್ಮ್ಯಾಟ್‌ಅನ್ನು ClawMetry ಯ ಏಕೀಕೃತ ಆಕಾರಗಳಿಗೆ ಅನುವಾದಿಸುತ್ತದೆ; ಡೀಮನ್ ಅವುಗಳನ್ನು ಅದೇ DuckDB ಸಂಗ್ರಹ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಸೇರಿಸುತ್ತದೆ, ರನ್‌ಟೈಮ್‌ನಿಂದ ಟ್ಯಾಗ್ ಮಾಡಲಾಗಿದೆ, ಮತ್ತು ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇದ್ದಾಗ Session replay ಟ್ಯಾಬ್ **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್**ಅನ್ನು ತೋರಿಸುತ್ತದೆ. ಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸುವ ಮಾರ್ಗದರ್ಶಿಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ನೋಡಿ, ಮತ್ತು OpenClaw-ಕುಟುಂಬ ಪ್ರಾಥಮಿಕ ಮಾಹಿತಿಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | ನೇಟಿವ್ | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆ |
| **PicoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಫ್ಲ್ಯಾಟ್ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಸೆಷನ್ SQLite (`data/v2-sessions`). ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು + ಚಿಂತನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | Rollout JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ. |
| **Aider** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಪ್ರಾಜೆಕ್ಟ್ `.aider.chat.history.md`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/goose`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಒಟ್ಟುಗಳು. |
| **opencode** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Pi** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.pi/agent/sessions`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Deep Agents** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.deepagents/.state/sessions.db`. ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |

"ಬೀಟಾ ಅಡಾಪ್ಟರ್" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನೈಜ ಡಿಸ್ಕ್‌ನಲ್ಲಿನ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ಒಂದು ರೀಡರ್‌ಅನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಪ್ರತಿಯೊಂದೂ ನೈಜ ಯಂತ್ರದಲ್ಲಿ ನೈಜ ಸ್ಥಾಪನೆಯ ವಿರುದ್ಧ ನಿರ್ಮಿಸಲಾಗಿದೆ + ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ಓದಲು-ಮಾತ್ರ; ಪ್ರತಿಯೊಂದೂ ಅದರ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಏನನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ ಎಂಬುದರ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ., PicoClaw/NanoClaw/Cursor ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುವುದಿಲ್ಲ). ಒಂದೇ ನೋಡ್‌ನಲ್ಲಿ ಹಲವಾರು ರನ್‌ಟೈಮ್‌ಗಳು ಚಲಿಸುತ್ತಿರುವಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಸ್ವಚ್ಛವಾದ ಆಳ-ಅಧ್ಯಯನಕ್ಕಾಗಿ ಸೆಷನ್‌ಗಳ ವೀಕ್ಷಣೆಯನ್ನು ಒಂದಕ್ಕೆ ಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್‌ಅನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ — ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಗುಣಲಕ್ಷಣ

ಮೇಲಿನ ರನ್‌ಟೈಮ್‌ಗಳೆಲ್ಲಾ ಸೆಷನ್‌ಗಳನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುತ್ತವೆ. ನಿಮ್ಮ ಸ್ವಂತ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್‌ನ ಮೇಲೆ ನೀವು ನಿರ್ಮಿಸಿದ್ದು — ಹಾಗೆ ಮಾಡುವುದಿಲ್ಲ. ClawMetry ಯ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್ಸೆಪ್ಟರ್ ಇನ್ನೂ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` env var) ಪ್ರತಿ ಕರೆಗೆ **ಹೆಸರಿಸಲಾದ ಮೂಲ**ಅನ್ನು ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಚಲಾಯಿಸುವ ಪ್ರತಿಯೊಂದು ಉತ್ಪನ್ನವೂ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನ Overview ನಲ್ಲಿ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಪ್ರಥಮ-ದರ್ಜೆಯ, ವೆಚ್ಚ-ಗುಣಲಕ್ಷಣ-ಸಾಧ್ಯವಾದ ಸಾಲಾಗಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ — ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪೂರೈಕೆದಾರರು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಮೂಲ ಸೆಟ್ ಮಾಡಿಲ್ಲವೇ? ಕರೆಗಳು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಆಗುತ್ತವೆ; ಕಾರ್ಡ್ ಮಾತ್ರ ಮರೆಯಾಗಿ ಇರುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ ಆಗಿದೆ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಉಳಿದೆಲ್ಲದರಂತೆಯೇ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗಿದೆ.

## OpenTelemetry — ಪೂರೈಕೆದಾರ-ತಟಸ್ಥ, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿ ಬೇಕಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಶಬ್ದಾರ್ಥ ಸಂಪ್ರದಾಯಗಳನ್ನು** ಬಳಸಿ, ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಎಂದಿಗೂ ಒಂದೇ ಟೂಲ್‌ಗೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿ ಸೆಷನ್ ಅನ್ನು **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ — LLM ಕರೆಗಳು, ಟೂಲ್‌ಗಳು, ಸಬ್-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ — ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector) OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ಆಥ್ ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಇಂಟರ್ವಲ್ ಐಚ್ಛಿಕ env ವೇರಿಯೇಬಲ್‌ಗಳಾಗಿವೆ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ಇಂಜೆಸ್ಟ್** — ಅಂತರ್ನಿರ್ಮಿತ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಇತರ ಯಾವುದೇ ಮೂಲದಿಂದ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (protobuf ಇಂಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನಿಮಗೆ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್, ಲೋಕಲ್-ಫಸ್ಟ್ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡ ಈಗಾಗಲೇ ಚಲಾಯಿಸುತ್ತಿರುವ ಯಾವುದೇ ಬ್ಯಾಕೆಂಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಡೇಟಾ ಸಿಗುತ್ತದೆ — ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಸ್ಥಾಪಿಸಲು ಎರಡನೇ ಏಜೆಂಟ್ ಇಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಶನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಷನ್‌ಗಳು, ಮತ್ತು ಕ್ರಾನ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನಿಮಗೆ ಕಸ್ಟಮೈಸ್ ಮಾಡುವ ಅಗತ್ಯವಿದ್ದರೆ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನೆಲ್‌ಗಳು

ClawMetry ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿಯೊಂದು OpenClaw ಚಾನೆಲ್‌ಗೆ ಲೈವ್ ಚಟುವಟಿಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ವಾಸ್ತವವಾಗಿ ಸೆಟಪ್ ಮಾಡಿದ ಚಾನೆಲ್‌ಗಳು ಮಾತ್ರ Flow ಡಯಾಗ್ರಾಮ್‌ನಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ — ಕಾನ್ಫಿಗರ್ ಮಾಡದವು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಮಾಡಲಾಗುತ್ತವೆ.

ಒಳಬರುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ವೀಕ್ಷಣೆಯನ್ನು ನೋಡಲು Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನೆಲ್ ನೋಡ್‌ಅನ್ನು ಕ್ಲಿಕ್ ಮಾಡಿ.

| ಚಾನೆಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪ್‌ಅಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ಪೂರ್ಣ | ✅ | ಸಂದೇಶಗಳು, ಅಂಕಿಅಂಶಗಳು, 10s ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ ಪೂರ್ಣ | ✅ | `~/Library/Messages/chat.db` ಅನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ ಪೂರ್ಣ | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ ಪೂರ್ಣ | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ ಪೂರ್ಣ | ✅ | ಗಿಲ್ಡ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ ಪೂರ್ಣ | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ ಪೂರ್ಣ | ✅ | ಅಂತರ್ನಿರ್ಮಿತ ವೆಬ್ UI ಸೆಷನ್‌ಗಳು |
| 📡 **IRC** | ✅ ಪೂರ್ಣ | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿಯ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ ಪೂರ್ಣ | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ ಪೂರ್ಣ | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ ಪೂರ್ಣ | ✅ | Teams ಬಾಟ್ ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ ಪೂರ್ಣ | ✅ | ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ ತಂಡ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ ಪೂರ್ಣ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ NIP-04 DM ಗಳು |
| 🟣 **Twitch** | ✅ ಪೂರ್ಣ | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ ಪೂರ್ಣ | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ ಪೂರ್ಣ | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಅನ್ನು ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ವಾಸ್ತವವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನೆಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಹಸ್ತಚಾಲಿತ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ನಿಯೋಜನೆ

ClawMetry ಅನ್ನು ಕಂಟೈನರ್‌ನಲ್ಲಿ ಚಲಾಯಿಸಲು ಬಯಸುವಿರಾ? ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ! 🐳

**Docker ನೊಂದಿಗೆ ತ್ವರಿತ ಪ್ರಾರಂಭ:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose ಉದಾಹರಣೆ:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ಚಲಾಯಿಸುವಾಗ, ClawMetry ನಿಮ್ಮ ಸೆಟಪ್‌ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡಲು ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`) ಮೌಂಟ್ ಮಾಡಿ.

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಸ್ಥಾಪಿಸಲಾಗಿದೆ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, ಅಥವಾ Deep Agents (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ — ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ಡ್ OpenShell ಕಂಟೈನರ್‌ಗಳೊಳಗೆ ಏಜೆಂಟ್‌ಗಳನ್ನು ಚಲಾಯಿಸುವ OpenClaw ಗಾಗಿ NVIDIA ಯ ಎಂಟರ್‌ಪ್ರೈಸ್ ಸೆಕ್ಯುರಿಟಿ ವ್ರ್ಯಾಪರ್.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಯಾವುದೇ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಶನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೀಮನ್, ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಇರಲಿ ಅಥವಾ OpenShell ಕಂಟೈನರ್‌ನೊಳಗೆ ಇರಲಿ, ಅವುಗಳನ್ನು ಸ್ವಯಂ-ಅನ್ವೇಷಣೆ ಮಾಡುತ್ತದೆ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry ಎರಡು ರೀತಿಯಲ್ಲಿ NemoClaw ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** — `nemoclaw` CLI ಅನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು `nemoclaw status` ಅನ್ನು ಚಲಾಯಿಸುತ್ತದೆ
2. **ಕಂಟೈನರ್ ಪತ್ತೆ** — `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಇಮೇಜ್‌ಗಳಿಗಾಗಿ ಚಾಲನೆಯಲ್ಲಿರುವ Docker ಕಂಟೈನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಷನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೈನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಮಾಡಿದ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಒಂದೇ ನೋಟದಲ್ಲಿ ಅವುಗಳನ್ನು ಪ್ರಮಾಣಿತ OpenClaw ಸೆಷನ್‌ಗಳಿಂದ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಿದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೀಮನ್

ಅತ್ಯುತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ಯ ಸಿಂಕ್ ಡೀಮನ್‌ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರ**ದಲ್ಲಿ ಚಲಾಯಿಸಿ (ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ ಒಳಗೆ ಅಲ್ಲ). ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೀಮನ್ ಚಾಲನೆಯಲ್ಲಿರುವ ಯಾವುದೇ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗಿನ ಸೆಷನ್‌ಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನೊಳಗೆ ಚಲಾಯಿಸುವುದು (ಸುಧಾರಿತ)

ನೀವು ಸಿಂಕ್ ಡೀಮನ್‌ಅನ್ನು OpenShell ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ **ಒಳಗೆ** ಚಲಾಯಿಸಲೇಬೇಕಾದರೆ, ಅದು ClawMetry ಇಂಜೆಸ್ಟ್ API ಅನ್ನು ತಲುಪಲು ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿಗೆ ಈ ಎಗ್ರೆಸ್ ನಿಯಮವನ್ನು ಸೇರಿಸಿ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ಇದನ್ನು ಅನ್ವಯಿಸಿ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ಪೋರ್ಟ್‌ಗಳು ಮತ್ತು ಎಂಡ್‌ಪಾಯಿಂಟ್‌ಗಳು

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೋಟೋಕಾಲ್ | ಅಗತ್ಯವಿದೆಯೇ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೀಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | ಕಂಟೈನರ್ ಸೆಷನ್ ಅನ್ವೇಷಣೆಗಾಗಿ |

ಸಿಂಕ್ ಡೀಮನ್ ಕೇವಲ `ingest.clawmetry.com` ಗೆ ಹೊರಹೋಗುವ HTTPS ಕರೆಗಳನ್ನು ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಒಳಬರುವ ಪೋರ್ಟ್‌ಗಳ ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ನಿಯೋಜನೆ

SSH ಟನಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ, ಮತ್ತು Docker ಗಾಗಿ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಪರೀಕ್ಷೆ

ಈ ಪ್ರಾಜೆಕ್ಟ್ ಅನ್ನು BrowserStack ನೊಂದಿಗೆ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ಹೊಸ ಯಂತ್ರದಲ್ಲಿ `clawmetry` CLI ಅನ್ನು ಮೊದಲ ಬಾರಿಗೆ ಚಲಾಯಿಸಿದಾಗ ClawMetry
`https://app.clawmetry.com/api/install` ಗೆ ಒಂದು ಅನಾಮಧೇಯ "ಮೊದಲ ರನ್" ಪಿಂಗ್
ಕಳುಹಿಸುತ್ತದೆ. ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು ಎಣಿಸಲು (OSS ಪ್ರಾಜೆಕ್ಟ್‌ಗಾಗಿ ನಮ್ಮಲ್ಲಿರುವ ಏಕೈಕ
ಮಾರ್ಕೆಟಿಂಗ್ ಮೆಟ್ರಿಕ್) ಮತ್ತು ನಮ್ಮ ಬಳಕೆದಾರರು ಯಾವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳನ್ನು
ಸ್ಥಾಪಿಸಿದ್ದಾರೆ ಎಂಬುದನ್ನು ತಿಳಿಯಲು ನಾವು ಇದನ್ನು ಬಳಸುತ್ತೇವೆ.

**ಪ್ರತಿ ಇನ್‌ಸ್ಟಾಲ್‌ಗೆ ನಿಖರವಾಗಿ ಒಂದು POST**, ಇದು ಒಳಗೊಂಡಿದೆ:

| ಫೀಲ್ಡ್ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಲಾದ ಯಾದೃಚ್ಛಿಕ UUID | ಡೀಡಪ್; ನಿಮ್ಮ ಇಮೇಲ್ ಅಥವಾ api_key ಗೆ ಲಿಂಕ್ ಆಗಿಲ್ಲ |
| `version` | `0.12.167` | ಯಾವ ಆವೃತ್ತಿಗಳು ಬಳಕೆಯಲ್ಲಿವೆ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ಆವೃತ್ತಿ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ಮುಂದೆ ನಾವು ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಇಂಟಿಗ್ರೇಟ್ ಮಾಡಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು CI ಗದ್ದಲದಿಂದ ಪ್ರತ್ಯೇಕಿಸಿ |

**ನಾವು ಕಳುಹಿಸದಿರುವುದು**: IP (ಕ್ಲೌಡ್ ವಿನಂತಿಯಿಂದ ಸರ್ವರ್-ಬದಿಯಲ್ಲಿ ದೇಶ ಕೋಡ್
ಪಡೆಯುತ್ತದೆ, ನಂತರ IP ಅನ್ನು ತಿರಸ್ಕರಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ಹೆಸರು, ಬಳಕೆದಾರಹೆಸರು,
ವರ್ಕ್‌ಸ್ಪೇಸ್ ಪಥ, ಫೈಲ್ ವಿಷಯಗಳು, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, ಯಾವುದೇ PII
ಅಥವಾ ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟ ವಿಷಯ. ವೈರ್ ಪೇಲೋಡ್
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದಾಗಿದೆ.

**ಆಪ್ಟ್ ಔಟ್** (ಈ ಕೆಳಗಿನ ಯಾವುದಾದರೂ ಒಂದು ಇದನ್ನು ಶಾಶ್ವತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವೈಫಲ್ಯವು `clawmetry` ಚಲಾಯಿಸುವುದನ್ನು ಎಂದಿಗೂ ತಡೆಯುವುದಿಲ್ಲ —
ಪಿಂಗ್ 3 ಸೆಕೆಂಡುಗಳ ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೀಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫಾರ್ಗೆಟ್ ಆಗಿದೆ.

## ಸ್ಟಾರ್ ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಲೈಸೆನ್ಸ್

MIT

---

<p align="center">
  <strong>🦞 ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ</strong><br>
  <sub>ನಿರ್ಮಿಸಿದವರು <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ಪರಿಸರ ವ್ಯವಸ್ಥೆಯ ಭಾಗ</sub>
</p>
