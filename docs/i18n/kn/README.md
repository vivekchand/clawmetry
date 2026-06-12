<!-- i18n-src:48548997be76 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **12 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗಾಗಿ** ರಿಯಲ್-ಟೈಮ್ ಅವಲೋಕನ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು 8 ಇತರ. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗಾಗಿ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ಒಂದು ಆದೇಶ. ಯಾವುದೇ ಕಾನ್ಫಿಗರೇಶನ್ ಇಲ್ಲ. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆದುಕೊಳ್ಳುತ್ತದೆ, ನೀವು ಸಿದ್ಧರಾಗಿದ್ದೀರಿ.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry ಮೊದಲು OpenClaw ಗಾಗಿ ಅವಲೋಕನ ಉಪಕರಣವಾಗಿ ಪ್ರಾರಂಭವಾಯಿತು, ಈಗ ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್**ಅನ್ನು ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ಅಳೆಯುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದ ಮೇಲಿನ ಪ್ರತಿ ರನ್‌ಟೈಮ್ ಅನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಉಚಿತ; ಇತರ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವ-ಹೋಸ್ಟ್ ಮಾಡಿದ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಕೆಲಸ ಮಾಡುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್ ಬದಲಾಯಿಸಿ ಮತ್ತು ಪ್ರತಿ ಟ್ಯಾಬ್ — ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಉಪಕರಣಗಳು, ಟ್ರೇಸ್‌ಗಳು — ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರುಹೊಂದಿಕೊಳ್ಳುತ್ತದೆ.

## ನೀವು ಏನನ್ನು ಪಡೆಯುತ್ತೀರಿ

- **Flow** — ಚಾನಲ್‌ಗಳು, ಬ್ರೈನ್, ಉಪಕರಣಗಳ ಮೂಲಕ ಸಂದೇಶಗಳ ಹರಿವನ್ನು ತೋರಿಸುವ ಲೈವ್ ಅನಿಮೇಟೆಡ್ ರೇಖಾಚಿತ್ರ
- **Overview** — ಆರೋಗ್ಯ ತಪಾಸಣೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಶನ್ ಎಣಿಕೆಗಳು, ಮಾದರಿ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ಸಾಪ್ತಾಹಿಕ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾದರಿ, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಶನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ನಿಗದಿತ ಕೆಲಸಗಳು
- **Logs** — ಬಣ್ಣ-ಕೋಡ್ ಮಾಡಿದ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಶನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗ್ಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡುತ್ತದೆ
- **Approvals** — ವಿನಾಶಕಾರಿ ಅಳಿಸುವಿಕೆ, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, DB ಮ್ಯುಟೇಶನ್‌ಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಒಂದು-ಕ್ಲಿಕ್ ಅನುಮೋದನೆಯ ಹಿಂದೆ ನಿಯಂತ್ರಿಸಿ

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

### 🧠 Brain — ಲೈವ್ ಏಜೆಂಟ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ಟೋಕನ್ ಬಳಕೆ ಮತ್ತು ಸೆಶನ್ ಸಾರಾಂಶ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ರಿಯಲ್-ಟೈಮ್ ಟೂಲ್ ಕಾಲ್ ಫೀಡ್
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ಮಾದರಿ ಮತ್ತು ಸೆಶನ್ ಮೂಲಕ ವೆಚ್ಚ ವಿಭಜನೆ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ವರ್ಕ್‌ಸ್ಪೇಸ್ ಫೈಲ್ ಬ್ರೌಸರ್
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ಭದ್ರತಾ ಸ್ಥಿತಿ ಮತ್ತು ಆಡಿಟ್ ಲಾಗ್
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗ್ಗರ್‌ಗಳು, Slack / Discord / PagerDuty / Email ಗೆ ವೆಬ್‌ಹುಕ್‌ಗಳು
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಹಸ್ತಚಾಲಿತ ಅನುಮೋದನೆಯ ಹಿಂದೆ ನಿಯಂತ್ರಿಸಿ; ನೀತಿ-ಬೆಂಬಲಿತ ಸಂರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ಸ್ಥಾಪಿಸಿ

**ಒಂದೇ ಆದೇಶ (ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ):**
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

## v2 ಫ್ರಂಟೆಂಡ್ ಅಭಿವೃದ್ಧಿ

v2 React ಅಪ್ಲಿಕೇಶನ್ `frontend/` ನಲ್ಲಿದೆ ಮತ್ತು v2 ಸಕ್ರಿಯಗೊಳಿಸಿದಾಗ Flask ಸರ್ವರ್ ಪ್ರಾರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಲಭ್ಯವಾಗುತ್ತದೆ.

ಅಭಿವೃದ್ಧಿ ಸಮಯದಲ್ಲಿ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

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

`http://localhost:5173/v2/` ತೆರೆಯಿರಿ. Vite `/api` ವಿನಂತಿಗಳನ್ನು `http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಅಪ್ಲಿಕೇಶನ್ ಹೆಚ್ಚುವರಿ CORS ಹೊಂದಾಣಿಕೆಯಿಲ್ಲದೆ ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಸೇರಿಸಲಾಗುವ ಬಂಡಲ್ ಅನ್ನು ನಿರ್ಮಿಸಲು:

```bash
cd frontend
npm run build
```

ಪ್ರೊಡಕ್ಷನ್ ಬಂಡಲ್ `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲ್ಪಡುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಅಲ್ಲ, ಅನೇಕ AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಅವಲೋಕಿಸುತ್ತದೆ. ಪ್ರತಿ OpenClaw-ಅಲ್ಲದ ರನ್‌ಟೈಮ್ ಒಂದು ಮೀಸಲಾದ ರೀಡರ್ ಅಡಾಪ್ಟರ್ ಅನ್ನು ಹೊಂದಿದೆ, ಅದು ಅದರ ಸ್ಥಳೀಯ ಸೆಶನ್ ಫಾರ್ಮ್ಯಾಟ್ ಅನ್ನು ClawMetry ಯ ಏಕೀಕೃತ ರೂಪಗಳಾಗಿ ಭಾಷಾಂತರಿಸುತ್ತದೆ; ಡೀಮನ್ ಅವುಗಳನ್ನು ರನ್‌ಟೈಮ್‌ನೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಿ ಅದೇ DuckDB ಸ್ಟೋರ್ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಸೇರಿಸುತ್ತದೆ, ಮತ್ತು Session ರಿಪ್ಲೇ ಟ್ಯಾಬ್ ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇದ್ದಾಗ **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್** ತೋರಿಸುತ್ತದೆ. ಸಂಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸುವ ಮಾರ್ಗದರ್ಶಿಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ನೋಡಿ, ಮತ್ತು OpenClaw-ಕುಟುಂಬ ಪ್ರೈಮರ್‌ಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | ಸ್ಥಳೀಯ | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆ |
| **PicoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಚಪ್ಪಟೆ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಸೆಶನ್-ಪ್ರತಿ SQLite (`data/v2-sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು + ಯೋಚನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ರೋಲ್‌ಔಟ್ JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ. |
| **Aider** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರಾಜೆಕ್ಟ್-ಪ್ರತಿ `.aider.chat.history.md`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/goose`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಒಟ್ಟುಗಳು. |
| **opencode** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |

"ಬೀಟಾ ಅಡಾಪ್ಟರ್" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನೈಜ ಡಿಸ್ಕ್-ಮೇಲಿನ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ರೀಡರ್ ಕಳುಹಿಸುತ್ತದೆ, ಪ್ರತಿಯೊಂದನ್ನು ನೈಜ ಯಂತ್ರದಲ್ಲಿ ನೈಜ ಸ್ಥಾಪನೆಯ ವಿರುದ್ಧ ನಿರ್ಮಿಸಲಾಗಿದೆ ಮತ್ತು ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ಓದು-ಮಾತ್ರ; ಪ್ರತಿಯೊಂದೂ ಅದರ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಸಂಗ್ರಹಿಸುವ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ. PicoClaw/NanoClaw/Cursor ಡಿಸ್ಕ್‌ಗೆ ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಬರೆಯುವುದಿಲ್ಲ). ಒಂದು ನೋಡ್‌ನಲ್ಲಿ ಹಲವು ರನ್‌ಟೈಮ್‌ಗಳು ಚಾಲಿತವಾದಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಸ್ವಚ್ಛ ಆಳ-ಧ್ಯಾನಕ್ಕಾಗಿ ಸೆಶನ್‌ಗಳ ನೋಟವನ್ನು ಒಂದಕ್ಕೆ ವ್ಯಾಪ್ತಿಗೊಳಿಸುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್ ಟ್ರ್ಯಾಕ್ ಮಾಡಿ — ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಆರೋಪಣೆ

ಮೇಲಿನ ರನ್‌ಟೈಮ್‌ಗಳು ಎಲ್ಲಾ ಡಿಸ್ಕ್‌ಗೆ ಸೆಶನ್‌ಗಳನ್ನು ಬರೆಯುತ್ತವೆ. OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್‌ನಲ್ಲಿ ನಿರ್ಮಿಸಿದ ನಿಮ್ಮ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** ಹಾಗೆ ಮಾಡುವುದಿಲ್ಲ. ClawMetry ಯ ಝೀರೋ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್‌ಸೆಪ್ಟರ್ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಇನ್ನೂ ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` env var) ಪ್ರತಿ ಕರೆಯನ್ನು **ಹೆಸರಿಸಿದ ಮೂಲ**ದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಚಲಾಯಿಸುವ ಪ್ರತಿ ಉತ್ಪನ್ನ Overview ನ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಮೊದಲ-ದರ್ಜೆ, ವೆಚ್ಚ-ಆರೋಪಣೀಯ ಸಾಲಾಗಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ — ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪೂರೈಕೆದಾರರು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಯಾವುದೇ ಮೂಲ ಹೊಂದಿಸಲಾಗಿಲ್ಲವೇ? ಕರೆಗಳನ್ನು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡಲಾಗುತ್ತದೆ; ಕಾರ್ಡ್ ಮಾತ್ರ ಮರೆಯಾಗಿ ಉಳಿಯುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಬೇರೆ ಎಲ್ಲದರಂತೆ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟೆಡ್.

## OpenTelemetry — ವಿಕ್ರೇತಾ-ತಟಸ್ಥ, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಯಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಸಿಮ್ಯಾಂಟಿಕ್ ಸಂಪ್ರದಾಯಗಳನ್ನು** ಬಳಸಿ ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಒಂದು ಉಪಕರಣಕ್ಕೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿ ಸೆಶನ್ — LLM ಕರೆಗಳು, ಉಪಕರಣಗಳು, ಉಪ-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ — ಅನ್ನು ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector) OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ಅಥ್ ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಮಧ್ಯಂತರ ಐಚ್ಛಿಕ env ವೇರಿಯಬಲ್‌ಗಳಾಗಿವೆ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ಇನ್‌ಜೆಸ್ಟ್** — ಅಂತರ್ನಿರ್ಮಿತ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಬೇರೆ ಎಲ್ಲದರಿಂದ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (ಪ್ರೊಟೊಬಫ್ ಇನ್‌ಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನೀವು ಝೀರೋ-ಕಾನ್ಫಿಗ್, ಲೋಕಲ್-ಫಸ್ಟ್ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡ ಈಗಾಗಲೇ ಬಳಸುವ ಯಾವ ಬ್ಯಾಕೆಂಡ್‌ನಲ್ಲೂ ನಿಮ್ಮ ಡೇಟಾವನ್ನು ಪಡೆಯುತ್ತೀರಿ — ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಯಾವುದೇ ಎರಡನೇ ಏಜೆಂಟ್ ಸ್ಥಾಪಿಸಬೇಕಿಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಶನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಶನ್‌ಗಳು ಮತ್ತು crons ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನೀವು ಕಸ್ಟಮೈಸ್ ಮಾಡಬೇಕಾದರೆ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನಲ್‌ಗಳು

ClawMetry ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿ OpenClaw ಚಾನಲ್‌ಗಾಗಿ ಲೈವ್ ಚಟುವಟಿಕೆ ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ವಾಸ್ತವವಾಗಿ ಹೊಂದಿಸಲಾದ ಚಾನಲ್‌ಗಳು ಮಾತ್ರ Flow ರೇಖಾಚಿತ್ರದಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ — ಕಾನ್ಫಿಗರ್ ಮಾಡದವುಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಮಾಡಲಾಗುತ್ತದೆ.

ಒಳಬರುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ನೋಟ ನೋಡಲು Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನಲ್ ನೋಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ.

| ಚಾನಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಸಂದೇಶಗಳು, ಸ್ಟ್ಯಾಟ್ಸ್, 10s ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ ಸಂಪೂರ್ಣ | ✅ | `~/Library/Messages/chat.db` ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ ಸಂಪೂರ್ಣ | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ ಸಂಪೂರ್ಣ | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಗಿಲ್ಡ್ + ಚಾನಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ ಸಂಪೂರ್ಣ | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಅಂತರ್ನಿರ್ಮಿತ ವೆಬ್ UI ಸೆಶನ್‌ಗಳು |
| 📡 **IRC** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ ಸಂಪೂರ್ಣ | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ ಸಂಪೂರ್ಣ | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ ಸಂಪೂರ್ಣ | ✅ | Teams ಬಾಟ್ ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಸ್ವ-ಹೋಸ್ಟ್ ತಂಡ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಡಿಸೆಂಟ್ರಲೈಸ್ಡ್, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ ಸಂಪೂರ್ಣ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ಸಂಪೂರ್ಣ | ✅ | ಡಿಸೆಂಟ್ರಲೈಸ್ಡ್ NIP-04 DMs |
| 🟣 **Twitch** | ✅ ಸಂಪೂರ್ಣ | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ ಸಂಪೂರ್ಣ | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ ಸಂಪೂರ್ಣ | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ವಾಸ್ತವವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಹಸ್ತಚಾಲಿತ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ನಿಯೋಜನೆ

ClawMetry ಅನ್ನು ಕಂಟೈನರ್‌ನಲ್ಲಿ ಚಲಾಯಿಸಲು ಬಯಸುವಿರಾ? ಸಮಸ್ಯೆಯಿಲ್ಲ! 🐳

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

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ಚಾಲಿತವಾದಾಗ, ClawMetry ನಿಮ್ಮ ಸೆಟಪ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡಲು ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು ಮೌಂಟ್ ಮಾಡಿ (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`).

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಸ್ಥಾಪಿತ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಒಂದು AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, ಅಥವಾ PicoClaw (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ — NVIDIA ಯ ಎಂಟರ್‌ಪ್ರೈಸ್ ಭದ್ರತಾ ಆವರಣ, ಅದು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ OpenShell ಕಂಟೈನರ್‌ಗಳಲ್ಲಿ ಏಜೆಂಟ್‌ಗಳನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, OpenClaw ಗಾಗಿ.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಶನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೀಮನ್ ಸೆಶನ್ ಫೈಲ್‌ಗಳು ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಇರಲಿ ಅಥವಾ OpenShell ಕಂಟೈನರ್‌ನೊಳಗೆ ಇರಲಿ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry ಎರಡು ರೀತಿಯಲ್ಲಿ NemoClaw ಅನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** — `nemoclaw` CLI ಗಾಗಿ ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಹಿತಿ ಪಡೆಯಲು `nemoclaw status` ಚಲಾಯಿಸುತ್ತದೆ
2. **ಕಂಟೈನರ್ ಪತ್ತೆ** — `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಚಿತ್ರಗಳಿಗಾಗಿ ಚಾಲಿತ Docker ಕಂಟೈನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಶನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೈನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಮಾಡಿದ ಸೆಶನ್ ಫೈಲ್‌ಗಳಿಗೆ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಅವುಗಳನ್ನು ನೇರ ನೋಟದಲ್ಲಿ ಪ್ರಮಾಣಿತ OpenClaw ಸೆಶನ್‌ಗಳಿಂದ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಿದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೀಮನ್

ಅತ್ಯುತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ಯ ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರದ ಮೇಲೆ** (ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನೊಳಗೆ ಅಲ್ಲ) ಚಲಾಯಿಸಿ. ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೀಮನ್ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಚಾಲಿತ OpenShell ಕಂಟೈನರ್‌ಗಳೊಳಗಿನ ಸೆಶನ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ ಕಡೆಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನೊಳಗೆ ಚಾಲಿತ (ಮುಂದುವರಿದ)

ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು OpenShell ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನೊಳಗೆ **ಚಲಾಯಿಸಬೇಕಾದರೆ**, ಅದು ClawMetry ಇನ್‌ಜೆಸ್ಟ್ API ತಲುಪಲು ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿಗೆ ಈ ಎಗ್ರೆಸ್ ನಿಯಮ ಸೇರಿಸಿ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ಇದರೊಂದಿಗೆ ಅನ್ವಯಿಸಿ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ಪೋರ್ಟ್‌ಗಳು ಮತ್ತು ಎಂಡ್‌ಪಾಯಿಂಟ್‌ಗಳು

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೋಟೋಕಾಲ್ | ಅಗತ್ಯ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೀಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | ಕಂಟೈನರ್ ಸೆಶನ್ ಶೋಧನೆಗಾಗಿ |

ಸಿಂಕ್ ಡೀಮನ್ `ingest.clawmetry.com` ಗೆ ಮಾತ್ರ ಔಟ್‌ಬೌಂಡ್ HTTPS ಕರೆಗಳನ್ನು ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಒಳಬರುವ ಪೋರ್ಟ್‌ಗಳು ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ನಿಯೋಜನೆ

SSH ಟನೆಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ ಮತ್ತು Docker ಗಾಗಿ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಪರೀಕ್ಷೆ

ಈ ಯೋಜನೆಯನ್ನು BrowserStack ನೊಂದಿಗೆ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ClawMetry ಹೊಸ ಯಂತ್ರದಲ್ಲಿ `clawmetry` CLI ಮೊದಲ ಬಾರಿಗೆ ಚಲಾಯಿಸಿದಾಗ `https://app.clawmetry.com/api/install` ಗೆ ಒಂದೇ ಅನಾಮಧೇಯ "ಮೊದಲ ರನ್" ಪಿಂಗ್ ಕಳುಹಿಸುತ್ತದೆ. ನಾವು ಇದನ್ನು ಸ್ಥಾಪನೆಗಳನ್ನು ಎಣಿಸಲು (OSS ಯೋಜನೆಗಾಗಿ ನಾವು ಹೊಂದಿರುವ ಏಕೈಕ ಮಾರ್ಕೆಟಿಂಗ್ ಮೆಟ್ರಿಕ್) ಮತ್ತು ನಮ್ಮ ಬಳಕೆದಾರರು ಯಾವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳನ್ನು ಸ್ಥಾಪಿಸಿದ್ದಾರೆ ಎಂದು ತಿಳಿಯಲು ಬಳಸುತ್ತೇವೆ.

**ಸ್ಥಾಪನೆಗೆ ನಿಖರವಾಗಿ ಒಂದು POST**, ಒಳಗೊಂಡಿದೆ:

| ಕ್ಷೇತ್ರ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಿದ ಯಾದೃಚ್ಛಿಕ UUID | ಡೀಡಪ್; ನಿಮ್ಮ ಇಮೇಲ್ ಅಥವಾ api_key ಗೆ ಸಂಪರ್ಕಿಸಲಾಗಿಲ್ಲ |
| `version` | `0.12.167` | ಯಾವ ಆವೃತ್ತಿಗಳು ಪ್ರಚಲಿತದಲ್ಲಿವೆ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ಆವೃತ್ತಿ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ನಾವು ಮುಂದೆ ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಸಂಯೋಜಿಸಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಸ್ಥಾಪನೆಗಳನ್ನು CI ಶಬ್ದದಿಂದ ಪ್ರತ್ಯೇಕಿಸಿ |

**ನಾವು ಕಳುಹಿಸದಿರುವುದು**: IP (ಕ್ಲೌಡ್ ವಿನಂತಿಯಿಂದ ಸರ್ವರ್-ಸೈಡ್‌ನಲ್ಲಿ ದೇಶ ಕೋಡ್ ಪಡೆಯುತ್ತದೆ, ನಂತರ IP ತ್ಯಜಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ನೇಮ್, ಬಳಕೆದಾರಹೆಸರು, ವರ್ಕ್‌ಸ್ಪೇಸ್ ಪಾಥ್, ಫೈಲ್ ವಿಷಯಗಳು, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, ಯಾವುದೇ PII ಅಥವಾ ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟ ಮಾಹಿತಿ. ವೈರ್ ಪೇಲೋಡ್ [`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದಾಗಿದೆ.

**ಆಪ್ಟ್ ಔಟ್** (ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದು ಶಾಶ್ವತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವೈಫಲ್ಯ ಎಂದಿಗೂ `clawmetry` ಚಾಲನೆಯನ್ನು ತಡೆಯುವುದಿಲ್ಲ — ಪಿಂಗ್ 3 s ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೀಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫರ್ಗೆಟ್ ಆಗಿದೆ.

## Star ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಪರವಾನಗಿ

MIT

---

<p align="center">
  <strong>🦞 ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ</strong><br>
  <sub>ನಿರ್ಮಿಸಿದ್ದು <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ಪರಿಸರ ವ್ಯವಸ್ಥೆಯ ಭಾಗ</sub>
</p>
