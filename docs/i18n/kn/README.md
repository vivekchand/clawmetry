<!-- i18n-src:9a05336fbdc1 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **14 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 10. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಒಂದು ಕಮಾಂಡ್. ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂ ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆದುಕೊಳ್ಳುತ್ತದೆ, ಅಷ್ಟೇ ಸಾಕು.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry OpenClaw ಗಾಗಿ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿಯಾಗಿ ಆರಂಭವಾಯಿತು, ಈಗ ಅದು ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್**ಅನ್ನು ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ಅಳೆಯುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿನ ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಅನ್ನೂ ಸ್ವಯಂ ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತವಾಗಿವೆ; ಉಳಿದ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಸಕ್ರಿಯಗೊಳ್ಳುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಬದಲಾಯಿಸಿ ಮತ್ತು ಪ್ರತಿಯೊಂದು ಟ್ಯಾಬ್ - ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಟೂಲ್‌ಗಳು, ಟ್ರೇಸ್‌ಗಳು - ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರು-ವ್ಯಾಪ್ತಿಗೊಳ್ಳುತ್ತದೆ. ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, `/api/entitlement` ಆಕಾರ, ಮತ್ತು `clawmetry license` CLI ಗಾಗಿ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **Flow** — ಚಾನೆಲ್‌ಗಳು, ಬ್ರೈನ್, ಟೂಲ್‌ಗಳ ಮೂಲಕ ಹರಿಯುವ ಸಂದೇಶಗಳನ್ನು ತೋರಿಸುವ ಲೈವ್ ಅನಿಮೇಟೆಡ್ ಡಯಾಗ್ರಾಂ ಮತ್ತು ಹಿಂತಿರುಗುವ ಪ್ರವಾಹ
- **Overview** — ಆರೋಗ್ಯ ಪರಿಶೀಲನೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಷನ್ ಎಣಿಕೆಗಳು, ಮಾಡೆಲ್ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ವಾರದ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾಡೆಲ್, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಷನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ನಿಗದಿತ ಜಾಬ್‌ಗಳು
- **Logs** — ಬಣ್ಣ-ಕೋಡ್ ಮಾಡಲಾದ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ನೋಟ್‌ಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಷನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ಮಾರ್ಗಗಳು
- **Approvals** — ವಿನಾಶಕಾರಿ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, DB ಮ್ಯುಟೇಷನ್‌ಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಒಂದು-ಕ್ಲಿಕ್ ಸೈನ್-ಆಫ್ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

### 🧠 Brain — ಲೈವ್ ಏಜೆಂಟ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ಟೋಕನ್ ಬಳಕೆ ಮತ್ತು ಸೆಷನ್ ಸಾರಾಂಶ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ರಿಯಲ್-ಟೈಮ್ ಟೂಲ್ ಕರೆ ಫೀಡ್
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ಮಾಡೆಲ್ ಮತ್ತು ಸೆಷನ್ ಮೂಲಕ ವೆಚ್ಚ ವಿಭಜನೆ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ವರ್ಕ್‌ಸ್ಪೇಸ್ ಫೈಲ್ ಬ್ರೌಸರ್
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ಭಂಗಿ ಮತ್ತು ಆಡಿಟ್ ಲಾಗ್
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, Slack / Discord / PagerDuty / Email ಗೆ ವೆಬ್‌ಹುಕ್‌ಗಳು
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಕೈಪಿಡಿ ಸೈನ್-ಆಫ್ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ; ಪಾಲಿಸಿ-ಬೆಂಬಲಿತ ರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ಗಾಗಿ ಪೂರ್ವ-ಎಕ್ಸಿಕ್ಯೂಷನ್ ಬ್ಲಾಕಿಂಗ್** — ಒಂದೇ ಕಮಾಂಡ್ ಒಂದು
PreToolUse ಹುಕ್ ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುತ್ತದೆ, ಇದು ಹೊಂದಾಣಿಕೆಯಾಗುವ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ರನ್ ಆಗುವ *ಮೊದಲು* ವಿರಾಮಗೊಳಿಸಿ ನಿಮ್ಮ ನಿರ್ಧಾರಕ್ಕಾಗಿ ಕಾಯುತ್ತದೆ (ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಒಂದೇ ಟ್ಯಾಪ್,
[ಕ್ಲೌಡ್ ಪುಶ್ ಅಧಿಸೂಚನೆಗಳು](https://app.clawmetry.com/push) ಸಕ್ರಿಯಗೊಳಿಸಿದಾಗ):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ಒಂದು ನಿರಾಕರಣೆ ಆ ಒಂದೇ ಟೂಲ್ ಕರೆಯನ್ನು ಮಾತ್ರ ತಡೆಯುತ್ತದೆ - ಏಜೆಂಟ್ ತನ್ನ ಸೆಷನ್ ಅನ್ನು ಇಟ್ಟುಕೊಳ್ಳುತ್ತದೆ ಮತ್ತು ಇನ್ನೊಂದು ವಿಧಾನವನ್ನು ಪ್ರಯತ್ನಿಸಬಹುದು. ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ ಅನುಮೋದಿಸುವುದು Claude Code ಯ ಸ್ವಂತ
ಅನುಮತಿ ಪ್ರಾಂಪ್ಟ್ ಅನ್ನು ಬಿಟ್ಟುಬಿಡುತ್ತದೆ (ನೀವು ಈಗಾಗಲೇ ಉತ್ತರಿಸಿದ್ದೀರಿ). ಹೊಂದಾಣಿಕೆಯಾಗದ ಟೂಲ್‌ಗಳಿಗೆ ಸುಮಾರು 40ms ವೆಚ್ಚವಾಗುತ್ತದೆ ಮತ್ತು
Claude Code ಯ ಸಾಮಾನ್ಯ ಅನುಮತಿ ಹರಿವಿಗೆ ಬೀಳುತ್ತವೆ. Claude Code ಸ್ವತಃ ನಿಮಗಾಗಿ ಕಾಯುತ್ತಿರುವಾಗಲೂ ನಿಮಗೆ ಫೋನ್ ಪುಶ್ ಸಿಗುತ್ತದೆ (`permission_prompt` /
`idle_prompt` ಅಧಿಸೂಚನೆಗಳು).

## ಇನ್‌ಸ್ಟಾಲ್

**ಒಂದು-ಸಾಲಿನ (ಶಿಫಾರಸು ಮಾಡಲಾದ):**
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

v2 React ಆ್ಯಪ್ `frontend/` ನಲ್ಲಿ ಇದೆ ಮತ್ತು v2 ಸಕ್ರಿಯಗೊಳಿಸಿ Flask
ಸರ್ವರ್ ಆರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಸೇವೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ.

ಅಭಿವೃದ್ಧಿಪಡಿಸುವಾಗ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

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
`http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಆ್ಯಪ್ ಹೆಚ್ಚುವರಿ CORS ಸೆಟಪ್ ಇಲ್ಲದೆ ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಸಾಗುವ ಬಂಡಲ್ ಅನ್ನು ನಿರ್ಮಿಸಲು:

```bash
cd frontend
npm run build
```

ಪ್ರೊಡಕ್ಷನ್ ಬಂಡಲ್ ಅನ್ನು `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲಾಗುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಅಲ್ಲ, ಅನೇಕ AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನೂ ಗಮನಿಸುತ್ತದೆ. OpenClaw ಅಲ್ಲದ ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್ ಒಂದು ಮೀಸಲಾದ ರೀಡರ್ ಅಡಾಪ್ಟರ್ ಅನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಇದು ಅದರ ಸ್ಥಳೀಯ ಸೆಷನ್ ಫಾರ್ಮ್ಯಾಟ್ ಅನ್ನು ClawMetry ಯ ಏಕೀಕೃತ ಆಕಾರಗಳಿಗೆ ಭಾಷಾಂತರಿಸುತ್ತದೆ; ಡೀಮನ್ ಅವುಗಳನ್ನು ರನ್‌ಟೈಮ್‌ನಿಂದ ಟ್ಯಾಗ್ ಮಾಡಿ ಅದೇ DuckDB ಸ್ಟೋರ್ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಸೇರಿಸುತ್ತದೆ, ಮತ್ತು ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇದ್ದಾಗ Session replay ಟ್ಯಾಬ್ ಒಂದು **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್** ಅನ್ನು ತೋರಿಸುತ್ತದೆ. ಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸುವ ಮಾರ್ಗದರ್ಶಿಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ಮತ್ತು OpenClaw-ಕುಟುಂಬ ಪ್ರೈಮರ್‌ಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | ಸ್ಥಳೀಯ | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆಯಾದ |
| **PicoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಫ್ಲ್ಯಾಟ್ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಸೆಷನ್ SQLite (`data/v2-sessions`). ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು + ಚಿಂತನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ರೋಲ್‌ಔಟ್ JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್. |
| **Aider** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ ಪ್ರಾಜೆಕ್ಟ್‌ಗೆ `.aider.chat.history.md`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/goose`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಒಟ್ಟು ಟೋಕನ್‌ಗಳು. |
| **opencode** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Pi** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.pi/agent/sessions`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Deep Agents** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.deepagents/.state/sessions.db`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾಡೆಲ್, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **n8n** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.n8n/database.sqlite`. ವರ್ಕ್‌ಫ್ಲೋ ಎಕ್ಸಿಕ್ಯೂಷನ್‌ಗಳು, ನೋಡ್ ರನ್‌ಗಳು, AI Agent ಪ್ರಾಂಪ್ಟ್‌ಗಳು, n8n ದಾಖಲಿಸಿದಲ್ಲಿ ಮಾಡೆಲ್ + ಟೋಕನ್‌ಗಳು. |

"ಬೀಟಾ ಅಡಾಪ್ಟರ್" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನಿಜವಾದ ಆನ್-ಡಿಸ್ಕ್ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ಒಂದು ರೀಡರ್ ಅನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಪ್ರತಿಯೊಂದನ್ನೂ ನಿಜವಾದ ಯಂತ್ರದಲ್ಲಿನ ನಿಜವಾದ ಇನ್‌ಸ್ಟಾಲ್ ವಿರುದ್ಧ ನಿರ್ಮಿಸಿ + ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ಓದಲು-ಮಾತ್ರ; ಪ್ರತಿಯೊಂದೂ ಅದರ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಏನನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ ಎಂಬುದರ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ. PicoClaw/NanoClaw/Cursor ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುವುದಿಲ್ಲ). ಒಂದೇ ನೋಡ್‌ನಲ್ಲಿ ಹಲವಾರು ರನ್‌ಟೈಮ್‌ಗಳು ರನ್ ಆದಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಸ್ಪಷ್ಟ ಆಳ-ಡೈವ್‌ಗಾಗಿ ಸೆಷನ್‌ಗಳ ವೀಕ್ಷಣೆಯನ್ನು ಒಂದಕ್ಕೆ ವ್ಯಾಪ್ತಿಗೊಳಿಸುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್ ಅನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ — ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಆಟ್ರಿಬ್ಯೂಷನ್

ಮೇಲಿನ ರನ್‌ಟೈಮ್‌ಗಳೆಲ್ಲ ಸೆಷನ್‌ಗಳನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುತ್ತವೆ. ನಿಮ್ಮ ಸ್ವಂತ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** - OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್‌ನ ಮೇಲೆ ನೀವು ನಿರ್ಮಿಸಿದ್ದು - ಹಾಗೆ ಮಾಡುವುದಿಲ್ಲ. ClawMetry ಯ ಜೀರೋ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಇನ್ನೂ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` ಎನ್ವ್ ವೇರಿಯಬಲ್) ಪ್ರತಿ ಕರೆಯನ್ನೂ ಒಂದು **ಹೆಸರಿಸಿದ ಮೂಲ**ದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ರನ್ ಮಾಡುವ ಪ್ರತಿಯೊಂದು ಉತ್ಪನ್ನವೂ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನ Overview ನಲ್ಲಿ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಪ್ರಥಮ-ದರ್ಜೆ, ವೆಚ್ಚ-ಆಟ್ರಿಬ್ಯೂಟಬಲ್ ಸಾಲಾಗಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ - ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪೂರೈಕೆದಾರರು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಯಾವುದೇ ಮೂಲವನ್ನು ಹೊಂದಿಸದಿದ್ದರೆ? ಕರೆಗಳನ್ನು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡಲಾಗುತ್ತದೆ; ಕಾರ್ಡ್ ಕೇವಲ ಮರೆಯಾಗಿ ಉಳಿಯುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಉಳಿದೆಲ್ಲದರಂತೆಯೇ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟ್ ಆಗಿ.

## OpenTelemetry — ವೆಂಡರ್-ನ್ಯೂಟ್ರಲ್, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಗೆ ಬೇಕಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಸೆಮ್ಯಾಂಟಿಕ್ ಸಂಪ್ರದಾಯಗಳನ್ನು** ಬಳಸಿ, ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಎಂದಿಗೂ ಒಂದೇ ಟೂಲ್‌ಗೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿಯೊಂದು ಸೆಷನ್ ಅನ್ನೂ **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ - LLM ಕರೆಗಳು, ಟೂಲ್‌ಗಳು, ಸಬ್-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ - ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector) OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ಅಥೆಂಟಿಕೇಷನ್ ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಮಧ್ಯಂತರ ಐಚ್ಛಿಕ ಎನ್ವ್ ವೇರಿಯಬಲ್‌ಗಳಾಗಿವೆ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ಇಂಜೆಸ್ಟ್** — ಒಳಗೊಂಡಿರುವ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಬೇರೆ ಯಾವುದೇ ಮೂಲದಿಂದ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (protobuf ಇಂಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನಿಮಗೆ ಜೀರೋ-ಕಾನ್ಫಿಗ್, ಸ್ಥಳೀಯ-ಮೊದಲ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡ ಈಗಾಗಲೇ ಚಲಾಯಿಸುತ್ತಿರುವ ಯಾವುದೇ ಬ್ಯಾಕ್‌ಎಂಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಡೇಟಾ ಸಿಗುತ್ತದೆ - ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಎರಡನೇ ಏಜೆಂಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುವ ಅಗತ್ಯವಿಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಷನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಷನ್‌ಗಳು, ಮತ್ತು ಕ್ರಾನ್‌ಗಳನ್ನು ಸ್ವಯಂ ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನಿಮಗೆ ಕಸ್ಟಮೈಸ್ ಮಾಡುವ ಅಗತ್ಯವಿದ್ದರೆ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನೆಲ್‌ಗಳು

ClawMetry ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿಯೊಂದು OpenClaw ಚಾನೆಲ್‌ಗೂ ಲೈವ್ ಚಟುವಟಿಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ನಿಜವಾಗಿ ಸೆಟಪ್ ಆಗಿರುವ ಚಾನೆಲ್‌ಗಳು ಮಾತ್ರ Flow ಡಯಾಗ್ರಾಂನಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ - ಕಾನ್ಫಿಗರ್ ಆಗದವು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಯಾಗುತ್ತವೆ.

Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನೆಲ್ ನೋಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಒಳಬರುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ವೀಕ್ಷಣೆಯನ್ನು ನೋಡಿ.

| ಚಾನೆಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪ್‌ಅಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ಪೂರ್ಣ | ✅ | ಸಂದೇಶಗಳು, ಅಂಕಿಅಂಶಗಳು, 10s ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ ಪೂರ್ಣ | ✅ | `~/Library/Messages/chat.db` ಅನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ ಪೂರ್ಣ | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ ಪೂರ್ಣ | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ ಪೂರ್ಣ | ✅ | ಗಿಲ್ಡ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ ಪೂರ್ಣ | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ ಪೂರ್ಣ | ✅ | ಒಳಗೊಂಡಿರುವ ವೆಬ್ UI ಸೆಷನ್‌ಗಳು |
| 📡 **IRC** | ✅ ಪೂರ್ಣ | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿಯ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ ಪೂರ್ಣ | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ ಪೂರ್ಣ | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ ಪೂರ್ಣ | ✅ | Teams ಬಾಟ್ ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ ಪೂರ್ಣ | ✅ | ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ ತಂಡ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ ಪೂರ್ಣ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ NIP-04 DMಗಳು |
| 🟣 **Twitch** | ✅ ಪೂರ್ಣ | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ ಪೂರ್ಣ | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ ಪೂರ್ಣ | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಅನ್ನು ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ನಿಜವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನೆಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಕೈಪಿಡಿ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

ClawMetry ಅನ್ನು ಕಂಟೈನರ್‌ನಲ್ಲಿ ರನ್ ಮಾಡಬೇಕೇ? ಸಮಸ್ಯೆ ಇಲ್ಲ! 🐳

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

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ರನ್ ಮಾಡುವಾಗ, ClawMetry ನಿಮ್ಮ ಸೆಟಪ್ ಅನ್ನು ಸ್ವಯಂ ಪತ್ತೆ ಮಾಡಲು ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`) ಮೌಂಟ್ ಮಾಡಿ.

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಇನ್‌ಸ್ಟಾಲ್ ಆಗುತ್ತದೆ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಒಂದು AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, ಅಥವಾ n8n (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ - NVIDIA ಯ ಎಂಟರ್‌ಪ್ರೈಸ್ ಸೆಕ್ಯುರಿಟಿ ರ‍್ಯಾಪರ್ OpenClaw ಗಾಗಿ, ಇದು ಏಜೆಂಟ್‌ಗಳನ್ನು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗೆ ರನ್ ಮಾಡುತ್ತದೆ.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಯಾವುದೇ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಷನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೀಮನ್ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಶೋಧಿಸುತ್ತದೆ, ಅವು ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಇರಲಿ ಅಥವಾ OpenShell ಕಂಟೈನರ್‌ನ ಒಳಗೆ ಇರಲಿ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry NemoClaw ಅನ್ನು ಎರಡು ರೀತಿಯಲ್ಲಿ ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** — `nemoclaw` CLI ಅನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಹಿತಿಗಾಗಿ `nemoclaw status` ಅನ್ನು ರನ್ ಮಾಡುತ್ತದೆ
2. **ಕಂಟೈನರ್ ಪತ್ತೆ** — `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಇಮೇಜ್‌ಗಳಿಗಾಗಿ ರನ್ ಆಗುತ್ತಿರುವ Docker ಕಂಟೈನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳ ಮೂಲಕ ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಷನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೈನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಆದ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಅವುಗಳನ್ನು ಸ್ಟ್ಯಾಂಡರ್ಡ್ OpenClaw ಸೆಷನ್‌ಗಳಿಂದ ಒಂದೇ ನೋಟದಲ್ಲಿ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಲಾದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೀಮನ್

ಅತ್ಯುತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ಯ ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರ**ದಲ್ಲಿ ರನ್ ಮಾಡಿ (ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ ಒಳಗೆ ಅಲ್ಲ). ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ಪಾಲಿಸಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೀಮನ್ ಯಾವುದೇ ರನ್ ಆಗುತ್ತಿರುವ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗಿನ ಸೆಷನ್‌ಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಒಳಗೆ ರನ್ ಮಾಡುವುದು (ಸುಧಾರಿತ)

ನೀವು ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು OpenShell ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ **ಒಳಗೆ** ರನ್ ಮಾಡಬೇಕಾದರೆ, ಅದು ClawMetry ಇಂಜೆಸ್ಟ್ API ಅನ್ನು ತಲುಪಲು ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ಪಾಲಿಸಿಗೆ ಈ ಎಗ್ರೆಸ್ ನಿಯಮವನ್ನು ಸೇರಿಸಿ:

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

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೊಟೋಕಾಲ್ | ಅಗತ್ಯ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೀಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker ಸಾಕೆಟ್ (`/var/run/docker.sock`) | — | Unix ಸಾಕೆಟ್ | ಕಂಟೈನರ್ ಸೆಷನ್ ಶೋಧನೆಗಾಗಿ |

ಸಿಂಕ್ ಡೀಮನ್ ಕೇವಲ `ingest.clawmetry.com` ಗೆ ಔಟ್‌ಬೌಂಡ್ HTTPS ಕರೆಗಳನ್ನು ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಇನ್‌ಬೌಂಡ್ ಪೋರ್ಟ್‌ಗಳ ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

SSH ಟನಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ, ಮತ್ತು Docker ಗಾಗಿ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಟೆಸ್ಟಿಂಗ್

ಈ ಪ್ರಾಜೆಕ್ಟ್ ಅನ್ನು BrowserStack ನೊಂದಿಗೆ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ClawMetry ಹೊಸ ಯಂತ್ರದಲ್ಲಿ ನೀವು ಮೊದಲ ಬಾರಿ `clawmetry` CLI ಅನ್ನು ರನ್ ಮಾಡಿದಾಗ
`https://app.clawmetry.com/api/install` ಗೆ ಒಂದೇ ಅನಾಮಧೇಯ "ಮೊದಲ ರನ್" ಪಿಂಗ್ ಕಳುಹಿಸುತ್ತದೆ. ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು ಎಣಿಸಲು (OSS ಪ್ರಾಜೆಕ್ಟ್‌ಗಾಗಿ ನಮ್ಮ ಬಳಿ ಇರುವ ಏಕೈಕ
ಮಾರ್ಕೆಟಿಂಗ್ ಮೆಟ್ರಿಕ್) ಮತ್ತು ನಮ್ಮ ಬಳಕೆದಾರರು ಯಾವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿದ್ದಾರೆಂದು ತಿಳಿಯಲು ನಾವು ಇದನ್ನು ಬಳಸುತ್ತೇವೆ.

**ಪ್ರತಿ ಇನ್‌ಸ್ಟಾಲ್‌ಗೆ ನಿಖರವಾಗಿ ಒಂದು POST**, ಇದು ಒಳಗೊಂಡಿದೆ:

| ಫೀಲ್ಡ್ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಲಾದ ಯಾದೃಚ್ಛಿಕ UUID | ಡುಪ್ಲಿಕೇಟ್ ತಪ್ಪಿಸಲು; ನಿಮ್ಮ ಇಮೇಲ್ ಅಥವಾ api_key ಗೆ ಲಿಂಕ್ ಮಾಡಿಲ್ಲ |
| `version` | `0.12.167` | ಯಾವ ವರ್ಷನ್‌ಗಳು ಬಳಕೆಯಲ್ಲಿವೆ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ವರ್ಷನ್ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ನಾವು ಮುಂದೆ ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಸಂಯೋಜಿಸಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು CI ಶಬ್ದದಿಂದ ಬೇರ್ಪಡಿಸಿ |

**ನಾವು ಕಳುಹಿಸದೇ ಇರುವುದು**: IP (ಕ್ಲೌಡ್ ವಿನಂತಿಯಿಂದ ಸರ್ವರ್-ಸೈಡ್‌ನಲ್ಲಿ ದೇಶದ ಕೋಡ್ ಅನ್ನು
ಪಡೆದುಕೊಳ್ಳುತ್ತದೆ, ನಂತರ IP ಅನ್ನು ತಿರಸ್ಕರಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ಹೆಸರು, ಬಳಕೆದಾರಹೆಸರು, ವರ್ಕ್‌ಸ್ಪೇಸ್
ಪಥ, ಫೈಲ್ ಒಳಗಿನ ವಿಷಯ, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, ಯಾವುದೇ PII ಅಥವಾ
ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟ ವಿಷಯ. ವೈರ್ ಪೇಲೋಡ್ ಅನ್ನು
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದು.

**ಆಪ್ಟ್ ಔಟ್** ಮಾಡಿ (ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದು ಶಾಶ್ವತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವಿಫಲತೆಯು `clawmetry` ರನ್ ಆಗುವುದನ್ನು ಎಂದಿಗೂ ತಡೆಯುವುದಿಲ್ಲ - ಈ
ಪಿಂಗ್ 3 ಸೆಕೆಂಡ್ ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೀಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫರ್ಗೆಟ್ ಆಗಿದೆ.

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
