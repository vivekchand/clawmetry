<!-- i18n-src:02b789586c7d -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಆಲೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **14 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 10 ಇತರೆ. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಇಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಆದೇಶ. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ, ಮತ್ತು ನೀವು ಮುಗಿಸಿದಿರಿ.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry OpenClaw ಗಾಗಿ ಅಬ್ಸರ್ವಬಿಲಿಟಿಯಾಗಿ ಪ್ರಾರಂಭವಾಯಿತು, ಮತ್ತು ಈಗ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್** ಅನ್ನು ಅಳೆಯುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿ ಪ್ರತಿ ರನ್‌ಟೈಮ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತವಾಗಿವೆ; ಉಳಿದ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಸಕ್ರಿಯಗೊಳ್ಳುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಬದಲಿಸಿ ಮತ್ತು ಪ್ರತಿ ಟ್ಯಾಬ್ ಕೂಡ - ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಟೂಲ್‌ಗಳು, ಟ್ರೇಸ್‌ಗಳು - ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರುಸ್ಕೋಪ್ ಆಗುತ್ತದೆ. ನಿಖರವಾದ ಉಚಿತ/ಪೇಯ್ಡ್ ವಿಭಜನೆ, ಟಿಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, `/api/entitlement` ಶೇಪ್, ಮತ್ತು `clawmetry license` CLI ಗಾಗಿ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **Flow** — ಚಾನೆಲ್‌ಗಳು, ಬ್ರೈನ್, ಟೂಲ್‌ಗಳು ಮತ್ತು ಹಿಂತಿರುಗಿ ಹರಿಯುವ ಸಂದೇಶಗಳನ್ನು ತೋರಿಸುವ ಲೈವ್ ಆನಿಮೇಟೆಡ್ ಡಯಾಗ್ರಾಮ್
- **Overview** — ಆರೋಗ್ಯ ಪರಿಶೀಲನೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಷನ್ ಎಣಿಕೆಗಳು, ಮಾಡೆಲ್ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ವಾರದ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾಡೆಲ್, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಷನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ನಿಗದಿತ ಜಾಬ್‌ಗಳು
- **Logs** — ಕಲರ್-ಕೋಡೆಡ್ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಷನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ಎರರ್-ರೇಟ್ ಟ್ರಿಗ್ಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡುತ್ತದೆ
- **Approvals** — ಒಂದೇ ಕ್ಲಿಕ್ ಸೈನ್-ಆಫ್‌ನ ಹಿಂದೆ ವಿನಾಶಕಾರಿ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, DB ಮ್ಯುಟೇಶನ್‌ಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಗೇಟ್ ಮಾಡಿ

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

### 🧠 Brain — ಲೈವ್ ಏಜೆಂಟ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ಟೋಕನ್ ಬಳಕೆ ಮತ್ತು ಸೆಷನ್ ಸಾರಾಂಶ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ರಿಯಲ್-ಟೈಮ್ ಟೂಲ್ ಕರೆ ಫೀಡ್
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ಮಾಡೆಲ್ ಮತ್ತು ಸೆಷನ್ ಪ್ರಕಾರ ವೆಚ್ಚದ ವಿಭಜನೆ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ವರ್ಕ್‌ಸ್ಪೇಸ್ ಫೈಲ್ ಬ್ರೌಸರ್
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ಪೊಸ್ಚರ್ ಮತ್ತು ಆಡಿಟ್ ಲಾಗ್
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ಬಜೆಟ್ ಮಿತಿಗಳು, ಎರರ್-ರೇಟ್ ಟ್ರಿಗ್ಗರ್‌ಗಳು, Slack / Discord / PagerDuty / Email ಗೆ ವೆಬ್‌ಹುಕ್‌ಗಳು
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಮ್ಯಾನ್ಯುಯಲ್ ಸೈನ್-ಆಫ್‌ನ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ; ಪಾಲಿಸಿ-ಬೆಂಬಲಿತ ರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ಗಾಗಿ ಎಕ್ಸಿಕ್ಯೂಶನ್‌ಗೆ ಮೊದಲಿನ ಬ್ಲಾಕಿಂಗ್** — ಒಂದೇ ಆದೇಶವು ಹೊಂದಾಣಿಕೆಯಾಗುವ ಟೂಲ್
ಕರೆಗಳನ್ನು ಅವು ರನ್ ಆಗುವ *ಮೊದಲೇ* ವಿರಮಿಸುವ ಮತ್ತು ನಿಮ್ಮ ನಿರ್ಧಾರಕ್ಕಾಗಿ ಕಾಯುವ
PreToolUse ಹುಕ್ ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುತ್ತದೆ (
[ಕ್ಲೌಡ್ ಪುಶ್ ನೋಟಿಫಿಕೇಶನ್‌ಗಳು](https://app.clawmetry.com/push) ಸಕ್ರಿಯಗೊಳಿಸಿದಾಗ ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಒಂದೇ ಟ್ಯಾಪ್):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ಒಂದು ಡಿನೈ ಆ ಒಂದೇ ಟೂಲ್ ಕರೆಯನ್ನು ಮಾತ್ರ ಬ್ಲಾಕ್ ಮಾಡುತ್ತದೆ — ಏಜೆಂಟ್ ತನ್ನ ಸೆಷನ್ ಅನ್ನು ಉಳಿಸಿಕೊಳ್ಳುತ್ತದೆ ಮತ್ತು
ಬೇರೆ ವಿಧಾನವನ್ನು ಪ್ರಯತ್ನಿಸಬಹುದು. ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ ಅನುಮೋದಿಸುವುದು Claude Code ನ ಸ್ವಂತ
ಅನುಮತಿ ಪ್ರಾಂಪ್ಟ್ ಅನ್ನು ಬಿಟ್ಟುಬಿಡುತ್ತದೆ (ನೀವು ಈಗಾಗಲೇ ಉತ್ತರಿಸಿದ್ದೀರಿ). ಹೊಂದಾಣಿಕೆಯಾಗದ ಟೂಲ್‌ಗಳಿಗೆ ~40ms ವೆಚ್ಚವಾಗುತ್ತದೆ ಮತ್ತು
Claude Code ನ ಸಾಮಾನ್ಯ ಅನುಮತಿ ಫ್ಲೋಗೆ ಬೀಳುತ್ತವೆ. Claude Code ಸ್ವತಃ ನಿಮಗಾಗಿ ಕಾಯುತ್ತಿರುವಾಗಲೂ ನಿಮಗೆ ಫೋನ್ ಪುಶ್ ಸಿಗುತ್ತದೆ (`permission_prompt` /
`idle_prompt` ನೋಟಿಫಿಕೇಶನ್‌ಗಳು).

## ಇನ್‌ಸ್ಟಾಲ್

**ಒಂದೇ-ಸಾಲಿನ (ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ):**
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

## v2 ಫ್ರಂಟೆಂಡ್ ಡೆವಲಪ್‌ಮೆಂಟ್

v2 React ಆ್ಯಪ್ `frontend/` ನಲ್ಲಿ ಇದೆ ಮತ್ತು Flask
ಸರ್ವರ್ ಅನ್ನು v2 ಸಕ್ರಿಯಗೊಳಿಸಿ ಪ್ರಾರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಸರ್ವ್ ಮಾಡಲಾಗುತ್ತದೆ.

ಡೆವಲಪ್ ಮಾಡುವಾಗ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

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

`http://localhost:5173/v2/` ಅನ್ನು ತೆರೆಯಿರಿ. Vite `/api` ವಿನಂತಿಗಳನ್ನು
`http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಆ್ಯಪ್ ಹೆಚ್ಚುವರಿ CORS ಸೆಟಪ್ ಇಲ್ಲದೆ
ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಶಿಪ್ ಆಗುವ ಬಂಡಲ್ ಅನ್ನು ಬಿಲ್ಡ್ ಮಾಡಲು:

```bash
cd frontend
npm run build
```

ಪ್ರೊಡಕ್ಷನ್ ಬಂಡಲ್ ಅನ್ನು `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲಾಗುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಮಾತ್ರವಲ್ಲ, ಹಲವಾರು AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಗಮನಿಸುತ್ತದೆ. ಪ್ರತಿಯೊಂದು OpenClaw-ಅಲ್ಲದ ರನ್‌ಟೈಮ್ ಒಂದು ಸಮರ್ಪಿತ ರೀಡರ್ ಅಡಾಪ್ಟರ್ ಅನ್ನು ಶಿಪ್ ಮಾಡುತ್ತದೆ, ಅದು ಅದರ ಸ್ಥಳೀಯ ಸೆಷನ್ ಫಾರ್ಮ್ಯಾಟ್ ಅನ್ನು ClawMetry ನ ಏಕೀಕೃತ ಶೇಪ್‌ಗಳಿಗೆ ಭಾಷಾಂತರಿಸುತ್ತದೆ; ಡೆಮನ್ ಅವುಗಳನ್ನು ಅದೇ DuckDB ಸ್ಟೋರ್ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಇಂಜೆಸ್ಟ್ ಮಾಡುತ್ತದೆ, ರನ್‌ಟೈಮ್‌ನೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಮತ್ತು ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇರುವಾಗ Session replay ಟ್ಯಾಬ್ ಒಂದು **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್** ಅನ್ನು ತೋರಿಸುತ್ತದೆ. ಸಂಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸುವ ಗೈಡ್‌ಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ನೋಡಿ, ಮತ್ತು OpenClaw-ಫ್ಯಾಮಿಲಿ ಪ್ರೈಮರ್‌ಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | Native | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆ |
| **PicoClaw** | Beta adapter | ಫ್ಲಾಟ್ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | Beta adapter | ಪ್ರತಿ-ಸೆಷನ್ SQLite (`data/v2-sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು + ಚಿಂತನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್. |
| **Aider** | Beta adapter | ಪ್ರತಿ ಪ್ರಾಜೆಕ್ಟ್‌ಗೆ `.aider.chat.history.md`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಒಟ್ಟು ಟೋಕನ್‌ಗಳು. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. ವರ್ಕ್‌ಫ್ಲೋ ಎಕ್ಸಿಕ್ಯೂಶನ್‌ಗಳು, ನೋಡ್ ರನ್‌ಗಳು, AI Agent ಪ್ರಾಂಪ್ಟ್‌ಗಳು, n8n ದಾಖಲಿಸುವಲ್ಲಿ ಮಾಡೆಲ್ + ಟೋಕನ್‌ಗಳು. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` ಅಡಿಯಲ್ಲಿ Brain JSONL. ಸಂಭಾಷಣೆಗಳು, ಟೂಲ್ ಹಂತಗಳು, ಚಿಂತನೆ, ಪ್ರತಿ-ಜನರೇಶನ್ Gemini ಟೋಕನ್ ವಿಭಜನೆ + ವೆಚ್ಚ, ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್-ಜನರೇಶನ್ ಬರ್ನ್. |

"Beta adapter" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನೈಜ ಆನ್-ಡಿಸ್ಕ್ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ರೀಡರ್ ಅನ್ನು ಶಿಪ್ ಮಾಡುತ್ತದೆ, ಪ್ರತಿಯೊಂದನ್ನೂ ನೈಜ ಯಂತ್ರದಲ್ಲಿನ ನೈಜ ಇನ್‌ಸ್ಟಾಲ್‌ನ ವಿರುದ್ಧ ನಿರ್ಮಿಸಿ + ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ರೀಡ್-ಒನ್ಲಿ; ಪ್ರತಿಯೊಂದೂ ಅದರ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಏನನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ ಎಂಬುದರ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ. PicoClaw/NanoClaw/Cursor ಡಿಸ್ಕ್‌ಗೆ ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಬರೆಯುವುದಿಲ್ಲ). ಒಂದೇ ನೋಡ್‌ನಲ್ಲಿ ಹಲವಾರು ರನ್‌ಟೈಮ್‌ಗಳು ರನ್ ಆಗುವಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಕ್ಲೀನ್ ಡೀಪ್-ಡೈವ್‌ಗಾಗಿ ಸೆಷನ್‌ಗಳ ವೀಕ್ಷಣೆಯನ್ನು ಒಂದಕ್ಕೆ ಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್ ಅನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ — ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಆ್ಯಟ್ರಿಬ್ಯೂಷನ್

ಮೇಲಿನ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್‌ಗಳು ಸೆಷನ್‌ಗಳನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುತ್ತವೆ. ನಿಮ್ಮ ಸ್ವಂತ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್ ಮೇಲೆ ನೀವು ನಿರ್ಮಿಸಿದ್ದು — ಇದನ್ನು ಮಾಡುವುದಿಲ್ಲ. ClawMetry ನ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಇನ್ನೂ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` env var) ಪ್ರತಿ ಕರೆಯನ್ನು **ಹೆಸರಿಸಿದ ಮೂಲ**ದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ರನ್ ಮಾಡುವ ಪ್ರತಿಯೊಂದು ಉತ್ಪನ್ನವೂ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನ Overview ನಲ್ಲಿನ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಪ್ರಥಮ-ದರ್ಜೆ, ವೆಚ್ಚ-ಆ್ಯಟ್ರಿಬ್ಯೂಟಬಲ್ ಸಾಲಾಗಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ — ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪ್ರೊವೈಡರ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಮೂಲವನ್ನು ಸೆಟ್ ಮಾಡಿಲ್ಲವೇ? ಕರೆಗಳು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಆಗುತ್ತವೆ; ಕಾರ್ಡ್ ಮಾತ್ರ ಮರೆಯಾಗಿ ಉಳಿಯುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಉಳಿದೆಲ್ಲದರಂತೆ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟೆಡ್.

## OpenTelemetry — ವೆಂಡರ್-ನ್ಯೂಟ್ರಲ್, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿ ಬೇಕಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಸೆಮ್ಯಾಂಟಿಕ್ ಕನ್ವೆನ್ಷನ್‌ಗಳನ್ನು** ಬಳಸಿ ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಎಂದಿಗೂ ಒಂದೇ ಟೂಲ್‌ಗೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿ ಸೆಷನ್ ಅನ್ನು **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ — LLM ಕರೆಗಳು, ಟೂಲ್‌ಗಳು, ಸಬ್-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ — OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಇಂಟರ್ವಲ್ ಐಚ್ಛಿಕ env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ಇಂಜೆಸ್ಟ್** — ಬಿಲ್ಟ್-ಇನ್ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಬೇರೆ ಯಾವುದರಿಂದಲಾದರೂ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (protobuf ಇಂಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನಿಮಗೆ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್, ಲೋಕಲ್-ಫಸ್ಟ್ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡ ಈಗಾಗಲೇ ರನ್ ಮಾಡುತ್ತಿರುವ ಯಾವುದೇ ಬ್ಯಾಕೆಂಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಡೇಟಾ ಸಿಗುತ್ತದೆ — ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು ಎರಡನೇ ಏಜೆಂಟ್ ಇಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಶನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಷನ್‌ಗಳು ಮತ್ತು ಕ್ರಾನ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನೀವು ಕಸ್ಟಮೈಸ್ ಮಾಡಬೇಕಾದರೆ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನೆಲ್‌ಗಳು

ClawMetry ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿ OpenClaw ಚಾನೆಲ್‌ಗೆ ಲೈವ್ ಚಟುವಟಿಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ವಾಸ್ತವವಾಗಿ ಸೆಟಪ್ ಆಗಿರುವ ಚಾನೆಲ್‌ಗಳು ಮಾತ್ರ Flow ಡಯಾಗ್ರಾಮ್‌ನಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ — ಕಾನ್ಫಿಗರ್ ಆಗದವುಗಳು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಯಾಗುತ್ತವೆ.

ಒಳಬರುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ವೀಕ್ಷಣೆಯನ್ನು ನೋಡಲು Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನೆಲ್ ನೋಡ್ ಅನ್ನು ಕ್ಲಿಕ್ ಮಾಡಿ.

| ಚಾನೆಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪ್‌ಅಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | ಸಂದೇಶಗಳು, ಅಂಕಿಅಂಶಗಳು, 10s ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` ಅನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ Full | ✅ | ಗಿಲ್ಡ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ Full | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ Full | ✅ | ಬಿಲ್ಟ್-ಇನ್ ವೆಬ್ UI ಸೆಷನ್‌ಗಳು |
| 📡 **IRC** | ✅ Full | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿಯ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams ಬಾಟ್ ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ Full | ✅ | ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ ಟೀಮ್ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ Full | ✅ | ವಿಕೇಂದ್ರೀಕೃತ, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | ವಿಕೇಂದ್ರೀಕೃತ NIP-04 DM ಗಳು |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಅನ್ನು ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ವಾಸ್ತವವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನೆಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಮ್ಯಾನ್ಯುಯಲ್ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

ClawMetry ಅನ್ನು ಕಂಟೈನರ್‌ನಲ್ಲಿ ರನ್ ಮಾಡಬೇಕೇ? ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ! 🐳

**Docker ನೊಂದಿಗೆ ಕ್ವಿಕ್ ಸ್ಟಾರ್ಟ್:**

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

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ರನ್ ಮಾಡುವಾಗ, ClawMetry ನಿಮ್ಮ ಸೆಟಪ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡಬಹುದಂತೆ ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`) ಮೌಂಟ್ ಮಾಡಿ.

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಇನ್‌ಸ್ಟಾಲ್ ಆಗುತ್ತದೆ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ಅಥವಾ Antigravity (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ — sandboxed OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗೆ ಏಜೆಂಟ್‌ಗಳನ್ನು ರನ್ ಮಾಡುವ OpenClaw ಗಾಗಿ NVIDIA ನ ಎಂಟರ್‌ಪ್ರೈಸ್ ಸೆಕ್ಯುರಿಟಿ ವ್ರ್ಯಾಪರ್.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಶನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೆಮನ್ ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಇರಲಿ ಅಥವಾ OpenShell ಕಂಟೈನರ್‌ನ ಒಳಗೆ ಇರಲಿ, ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಶೋಧಿಸುತ್ತದೆ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry ಎರಡು ವಿಧಾನಗಳಲ್ಲಿ NemoClaw ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** — `nemoclaw` CLI ಇದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು sandbox ಮಾಹಿತಿ ಪಡೆಯಲು `nemoclaw status` ಅನ್ನು ರನ್ ಮಾಡುತ್ತದೆ
2. **ಕಂಟೈನರ್ ಪತ್ತೆ** — `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಇಮೇಜ್‌ಗಳಿಗಾಗಿ ರನ್ ಆಗುತ್ತಿರುವ Docker ಕಂಟೈನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳ ಮೂಲಕ ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಷನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೈನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಆದ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ಒಂದೇ ನೋಟದಲ್ಲಿ ನೀವು ಅವುಗಳನ್ನು ಪ್ರಮಾಣಿತ OpenClaw ಸೆಷನ್‌ಗಳಿಂದ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಲಾದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೆಮನ್

ಅತ್ಯುತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ನ ಸಿಂಕ್ ಡೆಮನ್ ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರ**ದಲ್ಲಿ ರನ್ ಮಾಡಿ (sandbox ಒಳಗೆ ಅಲ್ಲ). ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ಪಾಲಿಸಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೆಮನ್ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ರನ್ ಆಗುತ್ತಿರುವ ಯಾವುದೇ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗಿನ ಸೆಷನ್‌ಗಳನ್ನು ಕಂಡುಕೊಳ್ಳುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ sandbox ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ sandbox ಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox ಒಳಗೆ ರನ್ ಮಾಡುವುದು (ಸುಧಾರಿತ)

ನೀವು ಸಿಂಕ್ ಡೆಮನ್ ಅನ್ನು OpenShell sandbox ನ **ಒಳಗೆ** ರನ್ ಮಾಡಲೇಬೇಕಾದರೆ, ಅದು ClawMetry ಇಂಜೆಸ್ಟ್ API ಅನ್ನು ತಲುಪಬಹುದಂತೆ ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ಪಾಲಿಸಿಗೆ ಈ ಎಗ್ರೆಸ್ ನಿಯಮವನ್ನು ಸೇರಿಸಿ:

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

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೊಟೊಕಾಲ್ | ಅಗತ್ಯವಿದೆಯೇ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೆಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker ಸಾಕೆಟ್ (`/var/run/docker.sock`) | — | Unix ಸಾಕೆಟ್ | ಕಂಟೈನರ್ ಸೆಷನ್ ಶೋಧನೆಗಾಗಿ |

ಸಿಂಕ್ ಡೆಮನ್ ಕೇವಲ `ingest.clawmetry.com` ಗೆ ಔಟ್‌ಬೌಂಡ್ HTTPS ಕರೆಗಳನ್ನು ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಇನ್‌ಬೌಂಡ್ ಪೋರ್ಟ್‌ಗಳ ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

SSH ಟನಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ, ಮತ್ತು Docker ಗಾಗಿ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಟೆಸ್ಟಿಂಗ್

ಈ ಪ್ರಾಜೆಕ್ಟ್ ಅನ್ನು BrowserStack ನೊಂದಿಗೆ ಟೆಸ್ಟ್ ಮಾಡಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ClawMetry ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್-ಲೈಫ್‌ಸೈಕಲ್ ಪಿಂಗ್‌ಗಳನ್ನು
`https://app.clawmetry.com/api/install` ಗೆ ಕಳುಹಿಸುತ್ತದೆ: ಹೊಸ ಯಂತ್ರದಲ್ಲಿ ನೀವು `clawmetry` CLI ಅನ್ನು
ಮೊದಲ ಬಾರಿಗೆ ರನ್ ಮಾಡಿದಾಗ ಒಂದು `install` ಪಿಂಗ್, ಹೊಸ ಆವೃತ್ತಿಗೆ ಅಪ್‌ಗ್ರೇಡ್ ಮಾಡಿದ ನಂತರದ ಮೊದಲ ರನ್‌ನಲ್ಲಿ ಒಂದು `update`
ಪಿಂಗ್, ಮತ್ತು ನೀವು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿನ ಆನ್‌ಬೋರ್ಡಿಂಗ್ ಆಯ್ಕೆಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿದಾಗ ಒಂದು `onboarded`
ಪಿಂಗ್. ನಿಜವಾದ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು ಎಣಿಸಲು ನಾವು ಇದನ್ನು ಬಳಸುತ್ತೇವೆ (ಕಚ್ಚಾ PyPI ಡೌನ್‌ಲೋಡ್
ಸಂಖ್ಯೆಗಳು ~98% ಮಿರರ್‌ಗಳು, CI, ಮತ್ತು ಆಟೋ-ಅಪ್‌ಡೇಟ್ ಮರು-ಡೌನ್‌ಲೋಡ್‌ಗಳು) ಮತ್ತು ಪ್ರಪಂಚದಲ್ಲಿ ವಾಸ್ತವವಾಗಿ ಇರುವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳು ಮತ್ತು
ಆವೃತ್ತಿಗಳನ್ನು ತಿಳಿಯಲು ಬಳಸುತ್ತೇವೆ.

**ಪ್ರತಿ ಆವೃತ್ತಿಗೆ ಪ್ರತಿ ಲೈಫ್‌ಸೈಕಲ್ ಈವೆಂಟ್‌ಗೆ ಗರಿಷ್ಠ ಒಂದು POST**, ಇದರಲ್ಲಿ ಇವು ಇರುತ್ತವೆ:

| ಫೀಲ್ಡ್ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಿದ ಯಾದೃಚ್ಛಿಕ UUID | ಡಿಡುಪ್; ನೀವು ಸ್ಪಷ್ಟವಾಗಿ Cloud sync ಅನ್ನು ಸಂಪರ್ಕಿಸುವವರೆಗೆ ಅನಾಮಧೇಯ (ಅಂತಹ ಪ್ರಮಾಣೀಕೃತ ಡೆಮನ್ ಹಾರ್ಟ್‌ಬೀಟ್ ನಂತರ ಇದನ್ನು ಹೊಂದಿರುತ್ತದೆ, ಈ ಇನ್‌ಸ್ಟಾಲ್ ಅನ್ನು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ) |
| `event` | `install` / `update` / `onboarded` | ಹೊಸ ಇನ್‌ಸ್ಟಾಲ್ vs ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ಒಂದರ ಅಪ್‌ಗ್ರೇಡ್ |
| `version` | `0.12.167` | ಪ್ರಪಂಚದಲ್ಲಿ ಯಾವ ಆವೃತ್ತಿಗಳಿವೆ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ಆವೃತ್ತಿ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ನಾವು ಮುಂದೆ ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಇಂಟಿಗ್ರೇಟ್ ಮಾಡಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು CI ಶಬ್ದದಿಂದ ಪ್ರತ್ಯೇಕಿಸಿ |

**ನಾವು ಕಳುಹಿಸದಿರುವುದು**: IP (ಕ್ಲೌಡ್ ವಿನಂತಿಯಿಂದ ಸರ್ವರ್-ಸೈಡ್ ಆಗಿ ದೇಶದ ಕೋಡ್ ಅನ್ನು
ಪಡೆಯುತ್ತದೆ, ನಂತರ IP ಅನ್ನು ತಿರಸ್ಕರಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ಹೆಸರು, ಬಳಕೆದಾರಹೆಸರು, ವರ್ಕ್‌ಸ್ಪೇಸ್
ಪಥ, ಫೈಲ್ ವಿಷಯಗಳು, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, ಯಾವುದೇ PII ಅಥವಾ ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟ ಮಾಹಿತಿ. ವೈರ್ ಪೇಲೋಡ್
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದಾಗಿದೆ.

**ಆಪ್ಟ್ ಔಟ್** (ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದು ಇದನ್ನು ಶಾಶ್ವತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವೈಫಲ್ಯವು `clawmetry` ಅನ್ನು ರನ್ ಆಗುವುದರಿಂದ ಎಂದಿಗೂ ತಡೆಯುವುದಿಲ್ಲ — ಪಿಂಗ್
3 ಸೆಕೆಂಡ್ ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೆಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫಾರ್ಗೆಟ್ ಆಗಿದೆ.

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
  <strong>🦞 ನಿಮ್ಮ ಏಜೆಂಟ್ ಆಲೋಚಿಸುವುದನ್ನು ನೋಡಿ</strong><br>
  <sub>ನಿರ್ಮಿಸಿದವರು <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ಇಕೋಸಿಸ್ಟಂನ ಭಾಗ</sub>
</p>
