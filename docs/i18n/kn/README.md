<!-- i18n-src:191e9094d7fa -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಆಲೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **14 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 10. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಕಮಾಂಡ್. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆದುಕೊಳ್ಳುತ್ತದೆ ಮತ್ತು ನಿಮ್ಮ ಕೆಲಸ ಮುಗಿಯಿತು.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry OpenClaw ಗಾಗಿ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿಯಾಗಿ ಆರಂಭವಾಯಿತು, ಮತ್ತು ಈಗ ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್** ಅನ್ನು ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ಅಳೆಯುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿ ಪ್ರತಿ ರನ್‌ಟೈಮ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತವಾಗಿವೆ; ಇತರ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಸಕ್ರಿಯಗೊಳ್ಳುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಬದಲಾಯಿಸಿ ಮತ್ತು ಪ್ರತಿ ಟ್ಯಾಬ್ ಕೂಡ - ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಟೂಲ್‌ಗಳು, ಟ್ರೇಸ್‌ಗಳು - ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರು-ವ್ಯಾಪ್ತಿಗೊಳ್ಳುತ್ತದೆ. ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, `/api/entitlement` ಆಕಾರ, ಮತ್ತು `clawmetry license` CLI ಗಾಗಿ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **Flow** — ಚಾನೆಲ್‌ಗಳು, ಬ್ರೈನ್, ಟೂಲ್‌ಗಳ ಮೂಲಕ ಹರಿಯುವ ಮತ್ತು ಮರಳಿ ಬರುವ ಸಂದೇಶಗಳನ್ನು ತೋರಿಸುವ ಲೈವ್ ಆ್ಯನಿಮೇಟೆಡ್ ಡಯಾಗ್ರಾಮ್
- **Overview** — ಆರೋಗ್ಯ ಪರೀಕ್ಷೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಷನ್ ಎಣಿಕೆಗಳು, ಮಾದರಿ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ವಾರದ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾದರಿ, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಷನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ನಿಗದಿತ ಕೆಲಸಗಳು
- **Logs** — ಬಣ್ಣ-ಕೋಡೆಡ್ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಷನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ಮಾರ್ಗ ಮಾಡುತ್ತದೆ
- **Approvals** — ವಿನಾಶಕಾರಿ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಷ್‌ಗಳು, DB ಮ್ಯುಟೇಶನ್‌ಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಒಂದೇ-ಕ್ಲಿಕ್ ಸಹಿ-ಮಾಡುವಿಕೆಯ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ

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

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಕೈಯಾರೆ ಸಹಿ-ಮಾಡುವಿಕೆಯ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ; ನೀತಿ-ಬೆಂಬಲಿತ ರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ಗಾಗಿ ಪೂರ್ವ-ಎಕ್ಸಿಕ್ಯೂಶನ್ ಬ್ಲಾಕಿಂಗ್** — ಒಂದೇ ಕಮಾಂಡ್
ಒಂದು PreToolUse ಹುಕ್ ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುತ್ತದೆ, ಅದು ಹೊಂದಾಣಿಕೆಯಾಗುವ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಾಯಿಸುವ *ಮೊದಲು* ವಿರಾಮಗೊಳಿಸುತ್ತದೆ ಮತ್ತು ನಿಮ್ಮ ನಿರ್ಧಾರಕ್ಕಾಗಿ ಕಾಯುತ್ತದೆ (ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಒಂದೇ ಟ್ಯಾಪ್‌ನಲ್ಲಿ
[ಕ್ಲೌಡ್ ಪುಷ್ ನೋಟಿಫಿಕೇಶನ್‌ಗಳು](https://app.clawmetry.com/push) ಸಕ್ರಿಯಗೊಳಿಸಿದಾಗ):

```bash
clawmetry hooks install     # ~/.claude/settings.json ಗೆ ಬರೆಯುತ್ತದೆ (ಇಡೆಂಪೊಟೆಂಟ್)
clawmetry hooks status      # ಏನು ಸಂಪರ್ಕಿಸಲಾಗಿದೆ + ಎಷ್ಟು ನೀತಿಗಳು ಸಕ್ರಿಯವಾಗಿವೆ
clawmetry hooks uninstall   # ClawMetry ಯ ಎಂಟ್ರಿಗಳನ್ನು ಮಾತ್ರ ತೆಗೆದುಹಾಕುತ್ತದೆ
```

ಒಂದು ನಿರಾಕರಣೆ ಆ ಒಂದೇ ಟೂಲ್ ಕರೆಯನ್ನು ಮಾತ್ರ ತಡೆಯುತ್ತದೆ - ಏಜೆಂಟ್ ತನ್ನ ಸೆಷನ್ ಅನ್ನು ಉಳಿಸಿಕೊಳ್ಳುತ್ತದೆ ಮತ್ತು ಮತ್ತೊಂದು ವಿಧಾನವನ್ನು ಪ್ರಯತ್ನಿಸಬಹುದು. ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ ಅನುಮೋದಿಸುವುದು Claude Code ನ ಸ್ವಂತ
ಅನುಮತಿ ಪ್ರಾಂಪ್ಟ್ ಅನ್ನು ಬಿಟ್ಟುಬಿಡುತ್ತದೆ (ನೀವು ಈಗಾಗಲೇ ಉತ್ತರಿಸಿದ್ದೀರಿ). ಹೊಂದಾಣಿಕೆಯಾಗದ ಟೂಲ್‌ಗಳಿಗೆ ~40ms ವೆಚ್ಚವಾಗುತ್ತದೆ ಮತ್ತು
Claude Code ನ ಸಾಮಾನ್ಯ ಅನುಮತಿ ಫ್ಲೋಗೆ ಹೋಗುತ್ತವೆ. Claude Code ಸ್ವತಃ ನಿಮಗಾಗಿ ಕಾಯುತ್ತಿರುವಾಗಲೂ ನಿಮಗೆ ಫೋನ್
ಪುಷ್ ಸಿಗುತ್ತದೆ (`permission_prompt` / `idle_prompt` ನೋಟಿಫಿಕೇಶನ್‌ಗಳು).

## ಇನ್‌ಸ್ಟಾಲ್

**ಒನ್-ಲೈನರ್ (ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ):**
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

## v2 ಫ್ರಂಟ್‌ಎಂಡ್ ಅಭಿವೃದ್ಧಿ

v2 React ಆ್ಯಪ್ `frontend/` ನಲ್ಲಿ ಇದೆ ಮತ್ತು Flask
ಸರ್ವರ್ ಅನ್ನು v2 ಸಕ್ರಿಯಗೊಳಿಸಿ ಪ್ರಾರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಸರ್ವ್ ಆಗುತ್ತದೆ.

ಅಭಿವೃದ್ಧಿ ಮಾಡುವಾಗ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

```bash
# ಟರ್ಮಿನಲ್ 1: Flask API/ಸರ್ವರ್ :8900 ನಲ್ಲಿ
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ಟರ್ಮಿನಲ್ 2: Vite ಡೆವ್ ಸರ್ವರ್ :5173 ನಲ್ಲಿ
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ತೆರೆಯಿರಿ. Vite `/api` ವಿನಂತಿಗಳನ್ನು
`http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಆ್ಯಪ್ ಹೆಚ್ಚುವರಿ CORS ಸೆಟಪ್ ಇಲ್ಲದೆ ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಬರುವ ಬಂಡಲ್ ಅನ್ನು ಬಿಲ್ಡ್ ಮಾಡಲು:

```bash
cd frontend
npm run build
```

ಉತ್ಪಾದನಾ ಬಂಡಲ್ `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲಾಗುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಅಲ್ಲ, ಅನೇಕ AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಗಮನಿಸುತ್ತದೆ. ಪ್ರತಿ ಓಪನ್‌ಕ್ಲಾ ಅಲ್ಲದ ರನ್‌ಟೈಮ್ ತನ್ನ ಸ್ಥಳೀಯ ಸೆಷನ್ ಫಾರ್ಮ್ಯಾಟ್ ಅನ್ನು ClawMetry ಯ ಏಕೀಕೃತ ಆಕಾರಗಳಾಗಿ ಭಾಷಾಂತರಿಸುವ ಸಮರ್ಪಿತ ರೀಡರ್ ಅಡಾಪ್ಟರ್ ಅನ್ನು ಹೊಂದಿದೆ; ಡೀಮನ್ ಅವುಗಳನ್ನು ಅದೇ DuckDB ಸ್ಟೋರ್ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಇಂಜೆಸ್ಟ್ ಮಾಡುತ್ತದೆ, ರನ್‌ಟೈಮ್‌ನೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗಿದೆ, ಮತ್ತು ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇದ್ದಾಗ Session replay ಟ್ಯಾಬ್ ಒಂದು **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್** ಅನ್ನು ತೋರಿಸುತ್ತದೆ. ಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸುವ ಮಾರ್ಗದರ್ಶಿಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ನೋಡಿ, ಮತ್ತು OpenClaw-ಕುಟುಂಬ ಪ್ರೈಮರ್‌ಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

[Perplexity ಯ numbat](https://github.com/perplexityai/numbat) ಏಜೆಂಟ್-ಸೆಕ್ಯುರಿಟಿ ಟೂಲ್ ಅನ್ನು ಚಲಾಯಿಸುತ್ತಿದ್ದೀರಾ? ClawMetry ಅದರ ಶೋಧನೆಗಳು ಮತ್ತು ಜಾರಿ ನಿರ್ಧಾರಗಳನ್ನು ತಕ್ಷಣ ಇಂಜೆಸ್ಟ್ ಮಾಡುತ್ತದೆ - ನೋಡಿ [`docs/NUMBAT.md`](docs/NUMBAT.md).

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | ಸ್ಥಳೀಯ | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡಲಾಗಿದೆ |
| **PicoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಫ್ಲಾಟ್ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಸೆಷನ್ SQLite (`data/v2-sessions`). ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು + ಆಲೋಚನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ರೋಲ್‌ಔಟ್ JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ. |
| **Aider** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ ಪ್ರಾಜೆಕ್ಟ್‌ಗೆ `.aider.chat.history.md`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/goose`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಒಟ್ಟುಗಳು. |
| **opencode** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Pi** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.pi/agent/sessions`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Deep Agents** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.deepagents/.state/sessions.db`. ಟ್ರಾನ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **n8n** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.n8n/database.sqlite`. ವರ್ಕ್‌ಫ್ಲೋ ಎಕ್ಸಿಕ್ಯೂಶನ್‌ಗಳು, ನೋಡ್ ರನ್‌ಗಳು, AI Agent ಪ್ರಾಂಪ್ಟ್‌ಗಳು, n8n ದಾಖಲಿಸುವಲ್ಲಿ ಮಾದರಿ + ಟೋಕನ್‌ಗಳು. |
| **Antigravity** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | `~/.gemini/<flavor>/brain/` ಅಡಿಯಲ್ಲಿ ಬ್ರೈನ್ JSONL. ಸಂಭಾಷಣೆಗಳು, ಟೂಲ್ ಹಂತಗಳು, ಆಲೋಚನೆ, ಪ್ರತಿ-ಜನರೇಶನ್ Gemini ಟೋಕನ್ ವಿಭಜನೆ + ವೆಚ್ಚ, ಹಿನ್ನೆಲೆ-ಜನರೇಶನ್ ಬರ್ನ್. |

"ಬೀಟಾ ಅಡಾಪ್ಟರ್" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನಿಜವಾದ ಆನ್-ಡಿಸ್ಕ್ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ಒಂದು ರೀಡರ್ ಅನ್ನು ಒದಗಿಸುತ್ತದೆ, ಪ್ರತಿಯೊಂದನ್ನೂ ನಿಜವಾದ ಯಂತ್ರದಲ್ಲಿನ ನಿಜವಾದ ಇನ್‌ಸ್ಟಾಲ್‌ಗೆ ಎದುರಾಗಿ ನಿರ್ಮಿಸಲಾಗಿದೆ + ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ರೀಡ್-ಓನ್ಲಿ; ಪ್ರತಿಯೊಂದೂ ತನ್ನ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಏನನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ ಎಂಬುದರ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ. PicoClaw/NanoClaw/Cursor ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುವುದಿಲ್ಲ). ಒಂದೇ ನೋಡ್‌ನಲ್ಲಿ ಹಲವಾರು ರನ್‌ಟೈಮ್‌ಗಳು ಚಲಾಯಿಸುತ್ತಿರುವಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಸೆಷನ್‌ಗಳ ವೀಕ್ಷಣೆಯನ್ನು ಸ್ವಚ್ಛ ಆಳ-ಡೈವ್‌ಗಾಗಿ ಒಂದಕ್ಕೆ ವ್ಯಾಪ್ತಿಗೊಳಿಸುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್ ಅನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ - ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಆಟ್ರಿಬ್ಯೂಶನ್

ಮೇಲಿನ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್‌ಗಳು ಸೆಷನ್‌ಗಳನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುತ್ತವೆ. ನೀವು OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್‌ನಲ್ಲಿ ನಿರ್ಮಿಸಿದ ನಿಮ್ಮ ಸ್ವಂತ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** ಹಾಗೆ ಮಾಡುವುದಿಲ್ಲ. ClawMetry ಯ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್‌ಸೆಪ್ಟರ್ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಇನ್ನೂ ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ
clawmetry.track.set_source("support-agent")   # ಈ ಉತ್ಪನ್ನಕ್ಕೆ ಹೆಸರಿಡಿ

# ...ನಿಮ್ಮ ಏಜೆಂಟ್ ಸಾಮಾನ್ಯದಂತೆ ಚಲಾಯಿಸುತ್ತದೆ; ಪ್ರತಿ LLM ಕರೆ ಈಗ ಟ್ರ್ಯಾಕ್ + ಆಟ್ರಿಬ್ಯೂಟ್ ಆಗುತ್ತದೆ.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` env var) ಪ್ರತಿ ಕರೆಯನ್ನು **ಹೆಸರಿಸಿದ ಮೂಲ**ದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಚಲಾಯಿಸುವ ಪ್ರತಿ ಉತ್ಪನ್ನವು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನ Overview ನಲ್ಲಿ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಪ್ರಥಮ-ದರ್ಜೆ, ವೆಚ್ಚ-ಆಟ್ರಿಬ್ಯೂಟ್ ಮಾಡಬಹುದಾದ ಸಾಲಾಗಿ ಕಾಣಿಸುತ್ತದೆ - ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪ್ರೊವೈಡರ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಮೂಲ ಸೆಟ್ ಮಾಡಿಲ್ಲವೇ? ಕರೆಗಳು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಆಗುತ್ತವೆ; ಕಾರ್ಡ್ ಮಾತ್ರ ಮರೆಯಾಗಿಯೇ ಉಳಿಯುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಬೇರೆಲ್ಲದರಂತೆ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟ್ ಆಗಿ.

## OpenTelemetry - ವೆಂಡರ್-ನ್ಯೂಟ್ರಲ್, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಗಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಸೆಮ್ಯಾಂಟಿಕ್ ಕನ್ವೆನ್ಶನ್ಸ್** ಬಳಸಿ ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಎಂದಿಗೂ ಒಂದೇ ಟೂಲ್‌ಗೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿ ಸೆಷನ್ ಅನ್ನು **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ - LLM ಕರೆಗಳು, ಟೂಲ್‌ಗಳು, ಸಬ್-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ - OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# ಸಮಾನವಾಗಿ:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ಆಥ್ ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಮಧ್ಯಂತರ ಐಚ್ಛಿಕ env var ಗಳಾಗಿವೆ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ಹೆಚ್ಚುವರಿ HTTP ಹೆಡರ್‌ಗಳು
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ಸೆಕೆಂಡುಗಳು (ಡೀಫಾಲ್ಟ್ 60)
```

**ಇಂಜೆಸ್ಟ್** - ಬಿಲ್ಟ್-ಇನ್ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಬೇರೆ ಯಾವುದರಿಂದಲಾದರೂ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (ಪ್ರೋಟೋಬಫ್ ಇಂಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನಿಮಗೆ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್, ಸ್ಥಳೀಯ-ಪ್ರಥಮ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡವು ಈಗಾಗಲೇ ಚಲಾಯಿಸುತ್ತಿರುವ ಯಾವುದೇ ಬ್ಯಾಕೆಂಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಡೇಟಾ ಎರಡೂ ಸಿಗುತ್ತವೆ - ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು ಎರಡನೇ ಏಜೆಂಟ್ ಇಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಶನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಬೇಕಾಗಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಷನ್‌ಗಳು ಮತ್ತು ಕ್ರಾನ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನೀವು ಕಸ್ಟಮೈಸ್ ಮಾಡಬೇಕಾದರೆ:

```bash
clawmetry --port 9000              # ಕಸ್ಟಮ್ ಪೋರ್ಟ್ (ಡೀಫಾಲ್ಟ್: 8900)
clawmetry --host 127.0.0.1         # ಕೇವಲ ಲೋಕಲ್‌ಹೋಸ್ಟ್‌ಗೆ ಬೈಂಡ್ ಮಾಡಿ
clawmetry --workspace ~/mybot      # ಕಸ್ಟಮ್ ವರ್ಕ್‌ಸ್ಪೇಸ್ ಪಥ
clawmetry --name "Alice"           # Flow ವಿಶುವಲೈಸೇಶನ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಹೆಸರು
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನೆಲ್‌ಗಳು

ClawMetry ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿ OpenClaw ಚಾನೆಲ್‌ಗೆ ಲೈವ್ ಚಟುವಟಿಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ನಿಜವಾಗಿ ಸೆಟಪ್ ಆಗಿರುವ ಚಾನೆಲ್‌ಗಳು ಮಾತ್ರ Flow ಡಯಾಗ್ರಾಮ್‌ನಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ - ಕಾನ್ಫಿಗರ್ ಆಗದವುಗಳು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಯಾಗಿರುತ್ತವೆ.

Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನೆಲ್ ನೋಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ, ಒಳಬರುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ವೀಕ್ಷಣೆಯನ್ನು ನೋಡಲು.

| ಚಾನೆಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪ್‌ಅಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ಪೂರ್ಣ | ✅ | ಸಂದೇಶಗಳು, ಅಂಕಿಅಂಶಗಳು, 10 ಸೆ ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ ಪೂರ್ಣ | ✅ | `~/Library/Messages/chat.db` ಅನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ ಪೂರ್ಣ | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ ಪೂರ್ಣ | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ ಪೂರ್ಣ | ✅ | ಗಿಲ್ಡ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ ಪೂರ್ಣ | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನೆಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ ಪೂರ್ಣ | ✅ | ಬಿಲ್ಟ್-ಇನ್ ವೆಬ್ UI ಸೆಷನ್‌ಗಳು |
| 📡 **IRC** | ✅ ಪೂರ್ಣ | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿಯ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ ಪೂರ್ಣ | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ ಪೂರ್ಣ | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ ಪೂರ್ಣ | ✅ | Teams ಬಾಟ್ ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ ಪೂರ್ಣ | ✅ | ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ ತಂಡ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ ಪೂರ್ಣ | ✅ | LINE ಮೆಸೇಜಿಂಗ್ API |
| ⚡ **Nostr** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ NIP-04 DM ಗಳು |
| 🟣 **Twitch** | ✅ ಪೂರ್ಣ | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ ಪೂರ್ಣ | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ ಪೂರ್ಣ | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಅನ್ನು ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ನಿಜವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನೆಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಕೈಯಾರೆ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

ClawMetry ಅನ್ನು ಒಂದು ಕಂಟೈನರ್‌ನಲ್ಲಿ ಚಲಾಯಿಸಲು ಬಯಸುತ್ತೀರಾ? ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ! 🐳

**Docker ನೊಂದಿಗೆ ತ್ವರಿತ ಆರಂಭ:**

```bash
# ಇಮೇಜ್ ಅನ್ನು ಬಿಲ್ಡ್ ಮಾಡಿ
docker build -t clawmetry .

# ಡೀಫಾಲ್ಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳೊಂದಿಗೆ ಚಲಾಯಿಸಿ
docker run -p 8900:8900 clawmetry

# ಅಥವಾ ನಿಮ್ಮ ಏಜೆಂಟ್ ನ ಡೇಟಾ ಡೈರ್ ಅನ್ನು ಮೌಂಟ್ ಮಾಡಿ (ತೋರಿಸಲಾಗಿದೆ: OpenClaw ನ ~/.openclaw)
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

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ಚಲಾಯಿಸುವಾಗ, ನಿಮ್ಮ ಏಜೆಂಟ್ ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`) ಮೌಂಟ್ ಮಾಡಿ ಇದರಿಂದ ClawMetry ನಿಮ್ಮ ಸೆಟಪ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡಬಹುದು.

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಇನ್‌ಸ್ಟಾಲ್ ಆಗುತ್ತದೆ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ಅಥವಾ Antigravity (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ - ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗೆ ಏಜೆಂಟ್‌ಗಳನ್ನು ಚಲಾಯಿಸುವ NVIDIA ಯ ಎಂಟರ್‌ಪ್ರೈಸ್ ಸೆಕ್ಯುರಿಟಿ ವ್ರ್ಯಾಪರ್ OpenClaw ಗಾಗಿ.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಯಾವುದೇ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಶನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೀಮನ್ ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಅಥವಾ OpenShell ಕಂಟೈನರ್‌ನ ಒಳಗೆ ಇರಲಿ, ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಶೋಧಿಸುತ್ತದೆ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry NemoClaw ಅನ್ನು ಎರಡು ವಿಧಗಳಲ್ಲಿ ಪತ್ತೆ ಮಾಡುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** - `nemoclaw` CLI ಗಾಗಿ ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಹಿತಿ ಪಡೆಯಲು `nemoclaw status` ಅನ್ನು ಚಲಾಯಿಸುತ್ತದೆ
2. **ಕಂಟೈನರ್ ಪತ್ತೆ** - `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಇಮೇಜ್‌ಗಳಿಗಾಗಿ ಚಾಲನೆಯಲ್ಲಿರುವ Docker ಕಂಟೈನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಷನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೈನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಮಾಡಿದ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ಒಂದೇ ನೋಟದಲ್ಲಿ ಅವುಗಳನ್ನು ಪ್ರಮಾಣಿತ OpenClaw ಸೆಷನ್‌ಗಳಿಂದ ಬೇರ್ಪಡಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಿದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೀಮನ್

ಉತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ಯ ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರ**ದಲ್ಲಿ ಚಲಾಯಿಸಿ (ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಒಳಗೆ ಅಲ್ಲ). ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# ಹೋಸ್ಟ್‌ನಲ್ಲಿ (ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಹೊರಗೆ)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೀಮನ್ ಚಾಲನೆಯಲ್ಲಿರುವ ಯಾವುದೇ OpenShell ಕಂಟೈನರ್‌ಗಳ ಒಳಗೆ ಸೆಷನ್‌ಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಒಳಗೆ ಚಲಾಯಿಸುವುದು (ಸುಧಾರಿತ)

ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು OpenShell ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್‌ನ **ಒಳಗೆ** ಚಲಾಯಿಸಬೇಕಾದರೆ, ಅದು ClawMetry ಇಂಜೆಸ್ಟ್ API ಅನ್ನು ತಲುಪಬಹುದೆಂದು ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿಗೆ ಈ ಎಗ್ರೆಸ್ ನಿಯಮವನ್ನು ಸೇರಿಸಿ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ಈ ಮೂಲಕ ಅನ್ವಯಿಸಿ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ಪೋರ್ಟ್‌ಗಳು ಮತ್ತು ಎಂಡ್‌ಪಾಯಿಂಟ್‌ಗಳು

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೋಟೋಕಾಲ್ | ಅಗತ್ಯವಿದೆಯೇ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೀಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker ಸಾಕೆಟ್ (`/var/run/docker.sock`) | — | Unix ಸಾಕೆಟ್ | ಕಂಟೈನರ್ ಸೆಷನ್ ಶೋಧನೆಗಾಗಿ |

ಸಿಂಕ್ ಡೀಮನ್ `ingest.clawmetry.com` ಗೆ ಮಾತ್ರ ಔಟ್‌ಬೌಂಡ್ HTTPS ಕರೆಗಳನ್ನು ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಇನ್‌ಬೌಂಡ್ ಪೋರ್ಟ್‌ಗಳ ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

SSH ಟನಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ, ಮತ್ತು Docker ಗಾಗಿ **[ಕ್ಲೌಡ್ ಟೆಸ್ಟಿಂಗ್ ಗೈಡ್](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಪರೀಕ್ಷೆ

ಈ ಪ್ರಾಜೆಕ್ಟ್ ಅನ್ನು BrowserStack ನೊಂದಿಗೆ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ClawMetry ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್-ಲೈಫ್‌ಸೈಕಲ್ ಪಿಂಗ್‌ಗಳನ್ನು
`https://app.clawmetry.com/api/install` ಗೆ ಕಳುಹಿಸುತ್ತದೆ: ನೀವು ಹೊಸ ಯಂತ್ರದಲ್ಲಿ ಮೊದಲ ಬಾರಿಗೆ `clawmetry` CLI ಅನ್ನು ಚಲಾಯಿಸಿದಾಗ ಒಂದು `install` ಪಿಂಗ್, ಹೊಸ ಆವೃತ್ತಿಗೆ ಅಪ್‌ಗ್ರೇಡ್ ಮಾಡಿದ ನಂತರ ಮೊದಲ ರನ್‌ನಲ್ಲಿ ಒಂದು `update` ಪಿಂಗ್, ಮತ್ತು ನೀವು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್-ಒಳಗಿನ ಆನ್‌ಬೋರ್ಡಿಂಗ್ ಆಯ್ಕೆಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿದಾಗ ಒಂದು `onboarded` ಪಿಂಗ್. ನಿಜವಾದ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು ಎಣಿಸಲು (ಕಚ್ಚಾ PyPI ಡೌನ್‌ಲೋಡ್ ಸಂಖ್ಯೆಗಳು ~98% ಮಿರರ್‌ಗಳು, CI, ಮತ್ತು ಆಟೋ-ಅಪ್‌ಡೇಟ್ ಮರು-ಡೌನ್‌ಲೋಡ್‌ಗಳಾಗಿವೆ) ಮತ್ತು ಯಾವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳು ಮತ್ತು ಆವೃತ್ತಿಗಳು ನಿಜವಾಗಿ ಬಳಕೆಯಲ್ಲಿವೆ ಎಂದು ತಿಳಿಯಲು ನಾವು ಇದನ್ನು ಬಳಸುತ್ತೇವೆ.

**ಪ್ರತಿ ಆವೃತ್ತಿಗೆ ಪ್ರತಿ ಲೈಫ್‌ಸೈಕಲ್ ಈವೆಂಟ್‌ಗೆ ಗರಿಷ್ಠ ಒಂದು POST**, ಇದನ್ನು ಒಳಗೊಂಡಿದೆ:

| ಫೀಲ್ಡ್ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಲಾದ ಯಾದೃಚ್ಛಿಕ UUID | ಡಿಡುಪ್; ನೀವು ಸ್ಪಷ್ಟವಾಗಿ Cloud ಸಿಂಕ್ ಸಂಪರ್ಕಿಸುವವರೆಗೆ ಅನಾಮಧೇಯ (ಆಗ ದೃಢೀಕೃತ ಡೀಮನ್ ಹಾರ್ಟ್‌ಬೀಟ್ ಅದನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಈ ಇನ್‌ಸ್ಟಾಲ್ ಅನ್ನು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ) |
| `event` | `install` / `update` / `onboarded` | ಹೊಸ ಇನ್‌ಸ್ಟಾಲ್ ವರ್ಸಸ್ ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ಒಂದರ ಅಪ್‌ಗ್ರೇಡ್ |
| `version` | `0.12.167` | ಬಳಕೆಯಲ್ಲಿರುವ ಆವೃತ್ತಿಗಳು ಯಾವುವು |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ಆವೃತ್ತಿ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ನಾವು ಮುಂದೆ ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಸಂಯೋಜಿಸಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು CI ಶಬ್ದದಿಂದ ಬೇರ್ಪಡಿಸಲು |

**ನಾವು ಕಳುಹಿಸದಿರುವುದು**: IP (ಕ್ಲೌಡ್ ವಿನಂತಿಯಿಂದ ಸರ್ವರ್-ಸೈಡ್‌ನಲ್ಲಿ ದೇಶ ಕೋಡ್ ಅನ್ನು ಪಡೆಯುತ್ತದೆ, ನಂತರ IP ಅನ್ನು ತಿರಸ್ಕರಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ಹೆಸರು, ಬಳಕೆದಾರಹೆಸರು, ವರ್ಕ್‌ಸ್ಪೇಸ್ ಪಥ, ಫೈಲ್ ವಿಷಯಗಳು, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, PII ಅಥವಾ ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟ ಯಾವುದೇ ವಿಷಯ. ವೈರ್ ಪೇಲೋಡ್
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದಾಗಿದೆ.

**ಆಪ್ಟ್ ಔಟ್** (ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದು ಅದನ್ನು ಶಾಶ್ವತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ಪ್ರತಿ-ಶೆಲ್
export DO_NOT_TRACK=1                          # W3C ಅಡ್ಡ-ಟೂಲ್ ಮಾನದಂಡ
touch ~/.clawmetry/notelemetry                 # ಶಾಶ್ವತ ಫೈಲ್ ಗುರುತು
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವೈಫಲ್ಯವು `clawmetry` ಚಲಾಯಿಸುವುದನ್ನು ಎಂದಿಗೂ ತಡೆಯುವುದಿಲ್ಲ - ಪಿಂಗ್ 3 ಸೆ ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೀಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫಾರ್ಗೆಟ್ ಆಗಿದೆ.

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
  <sub>ನಿರ್ಮಿಸಿದವರು <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ಪರಿಸರ ವ್ಯವಸ್ಥೆಯ ಭಾಗ</sub>
</p>
