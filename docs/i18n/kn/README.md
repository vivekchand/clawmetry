<!-- i18n-src:7cfb63716507 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಚಿಂತಿಸುವುದನ್ನು ನೋಡಿ.** **14 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 10. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಕಮಾಂಡ್. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ ಮತ್ತು ನಿಮ್ಮ ಕೆಲಸ ಮುಗಿಯಿತು.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry OpenClaw ಗಾಗಿ ಅಬ್ಸರ್ವಬಿಲಿಟಿಯಾಗಿ ಪ್ರಾರಂಭವಾಯಿತು, ಮತ್ತು ಈಗ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ **ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್** ಅನ್ನು ಮೀಟರ್ ಮಾಡುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿ ಪ್ರತಿ ರನ್‌ಟೈಮ್ ಅನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw ಮತ್ತು NemoClaw ಓಪನ್-ಸೋರ್ಸ್ ಆಪ್‌ನಲ್ಲಿ ಉಚಿತವಾಗಿವೆ; ಇತರ ರನ್‌ಟೈಮ್‌ಗಳು ClawMetry Cloud ಅಥವಾ ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ Pro ಲೈಸೆನ್ಸ್‌ನೊಂದಿಗೆ ಬೆಳಗುತ್ತವೆ. ಹೆಡರ್‌ನಿಂದ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಬದಲಾಯಿಸಿ ಮತ್ತು ಪ್ರತಿ ಟ್ಯಾಬ್ - ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಟೂಲ್‌ಗಳು, ಟ್ರೇಸ್‌ಗಳು - ಆ ರನ್‌ಟೈಮ್‌ಗೆ ಮರುಸ್ಕೋಪ್ ಆಗುತ್ತದೆ. ನಿಖರ ಉಚಿತ/ಪಾವತಿತ ವಿಭಜನೆ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, `/api/entitlement` ಆಕಾರ ಮತ್ತು `clawmetry license` CLI ಗಾಗಿ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **Flow** — ಚಾನಲ್‌ಗಳು, ಬ್ರೈನ್, ಟೂಲ್‌ಗಳ ಮೂಲಕ ಹರಿಯುವ ಸಂದೇಶಗಳನ್ನು ಮತ್ತು ಹಿಂತಿರುಗುವುದನ್ನು ತೋರಿಸುವ ಲೈವ್ ಅನಿಮೇಟೆಡ್ ಡಯಾಗ್ರಾಂ
- **Overview** — ಆರೋಗ್ಯ ತಪಾಸಣೆಗಳು, ಚಟುವಟಿಕೆ ಹೀಟ್‌ಮ್ಯಾಪ್, ಸೆಷನ್ ಎಣಿಕೆಗಳು, ಮಾದರಿ ಮಾಹಿತಿ
- **Usage** — ದೈನಂದಿನ/ಸಾಪ್ತಾಹಿಕ/ಮಾಸಿಕ ವಿಭಜನೆಗಳೊಂದಿಗೆ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚ ಟ್ರ್ಯಾಕಿಂಗ್
- **Sessions** — ಮಾದರಿ, ಟೋಕನ್‌ಗಳು, ಕೊನೆಯ ಚಟುವಟಿಕೆಯೊಂದಿಗೆ ಸಕ್ರಿಯ ಏಜೆಂಟ್ ಸೆಷನ್‌ಗಳು
- **Crons** — ಸ್ಥಿತಿ, ಮುಂದಿನ ರನ್, ಅವಧಿಯೊಂದಿಗೆ ಶೆಡ್ಯೂಲ್ಡ್ ಜಾಬ್‌ಗಳು
- **Logs** — ಬಣ್ಣ-ಕೋಡೆಡ್ ರಿಯಲ್-ಟೈಮ್ ಲಾಗ್ ಸ್ಟ್ರೀಮಿಂಗ್
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ದೈನಂದಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ
- **Transcripts** — ಸೆಷನ್ ಇತಿಹಾಸಗಳನ್ನು ಓದಲು ಚಾಟ್-ಬಬಲ್ UI
- **Alerts** — ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ-ದರ ಟ್ರಿಗರ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್ ಪತ್ತೆ; Slack, Discord, PagerDuty, Telegram, Email ಗೆ ಮಾರ್ಗ ನೀಡುತ್ತದೆ
- **Approvals** — ವಿನಾಶಕಾರಿ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, DB ಮ್ಯುಟೇಶನ್‌ಗಳು, sudo, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು, ನೆಟ್‌ವರ್ಕ್ ಕರೆಗಳನ್ನು ಒಂದು-ಕ್ಲಿಕ್ ಸಹಿ-ಆಫ್‌ನ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ

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

### ✋ Approvals — ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಹಸ್ತಚಾಲಿತ ಸಹಿ-ಆಫ್‌ನ ಹಿಂದೆ ಗೇಟ್ ಮಾಡಿ; ನೀತಿ-ಬೆಂಬಲಿತ ರಕ್ಷಣಾ ನಿಯಮಗಳು
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ಗಾಗಿ ಎಕ್ಸಿಕ್ಯೂಶನ್-ಪೂರ್ವ ಬ್ಲಾಕಿಂಗ್** — ಒಂದು ಕಮಾಂಡ್ ಒಂದು
PreToolUse ಹುಕ್ ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುತ್ತದೆ ಅದು ಹೊಂದಾಣಿಕೆಯಾಗುವ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ರನ್ ಆಗುವ *ಮೊದಲು* ವಿರಾಮಗೊಳಿಸಿ ನಿಮ್ಮ ನಿರ್ಧಾರಕ್ಕಾಗಿ ಕಾಯುತ್ತದೆ
([cloud push notifications](https://app.clawmetry.com/push) ಸಕ್ರಿಯಗೊಳಿಸಿದಾಗ ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಒಂದೇ ಟ್ಯಾಪ್):

```bash
clawmetry hooks install     # ~/.claude/settings.json ಬರೆಯುತ್ತದೆ (ಇಡೆಂಪೊಟೆಂಟ್)
clawmetry hooks status      # ಏನು ವೈರ್ ಆಗಿದೆ + ಎಷ್ಟು ನೀತಿಗಳು ಸಕ್ರಿಯವಾಗಿವೆ
clawmetry hooks uninstall   # ClawMetry ನ ಎಂಟ್ರಿಗಳನ್ನು ಮಾತ್ರ ತೆಗೆದುಹಾಕುತ್ತದೆ
```

ಒಂದು ನಿರಾಕರಣೆ ಆ ಒಂದು ಟೂಲ್ ಕರೆಯನ್ನು ಮಾತ್ರ ಬ್ಲಾಕ್ ಮಾಡುತ್ತದೆ — ಏಜೆಂಟ್ ತನ್ನ ಸೆಷನ್ ಅನ್ನು ಉಳಿಸಿಕೊಳ್ಳುತ್ತದೆ ಮತ್ತು
ಬೇರೊಂದು ವಿಧಾನವನ್ನು ಪ್ರಯತ್ನಿಸಬಹುದು. ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ ಅನುಮೋದಿಸುವುದು Claude Code ನ ಸ್ವಂತ
ಅನುಮತಿ ಪ್ರಾಂಪ್ಟ್ ಅನ್ನು ಬಿಟ್ಟುಬಿಡುತ್ತದೆ (ನೀವು ಈಗಾಗಲೇ ಉತ್ತರಿಸಿದ್ದೀರಿ). ಹೊಂದಾಣಿಕೆಯಾಗದ ಟೂಲ್‌ಗಳಿಗೆ ~40ms ವೆಚ್ಚವಾಗುತ್ತದೆ ಮತ್ತು
Claude Code ನ ಸಾಮಾನ್ಯ ಅನುಮತಿ ಫ್ಲೋಗೆ ಬೀಳುತ್ತವೆ. Claude Code ತಾನೇ ನಿಮಗಾಗಿ ಕಾಯುತ್ತಿರುವಾಗಲೂ ನಿಮಗೆ ಫೋನ್
ಪುಶ್ ಸಿಗುತ್ತದೆ (`permission_prompt` / `idle_prompt` ಅಧಿಸೂಚನೆಗಳು).

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ

**ಒಂದು-ಸಾಲಿನ (ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ):**
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

v2 React ಆಪ್ `frontend/` ನಲ್ಲಿ ಇರುತ್ತದೆ ಮತ್ತು Flask
ಸರ್ವರ್ ಅನ್ನು v2 ಸಕ್ರಿಯಗೊಳಿಸಿ ಪ್ರಾರಂಭಿಸಿದಾಗ `/v2` ನಲ್ಲಿ ಸೇವೆ ನೀಡಲಾಗುತ್ತದೆ.

ಅಭಿವೃದ್ಧಿ ಮಾಡುವಾಗ ಎರಡು ಟರ್ಮಿನಲ್‌ಗಳನ್ನು ಬಳಸಿ:

```bash
# ಟರ್ಮಿನಲ್ 1: :8900 ನಲ್ಲಿ Flask API/ಸರ್ವರ್
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ಟರ್ಮಿನಲ್ 2: :5173 ನಲ್ಲಿ Vite dev ಸರ್ವರ್
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ತೆರೆಯಿರಿ. Vite `/api` ವಿನಂತಿಗಳನ್ನು
`http://localhost:8900` ಗೆ ಪ್ರಾಕ್ಸಿ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ React ಆಪ್ ಹೆಚ್ಚುವರಿ CORS ಸೆಟಪ್ ಇಲ್ಲದೆ
ಸ್ಥಳೀಯ Flask ಸರ್ವರ್‌ನೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.

Python ಪ್ಯಾಕೇಜ್‌ನೊಂದಿಗೆ ಬರುವ ಬಂಡಲ್ ಅನ್ನು ನಿರ್ಮಿಸಲು:

```bash
cd frontend
npm run build
```

ಪ್ರೊಡಕ್ಷನ್ ಬಂಡಲ್ ಅನ್ನು `clawmetry/static/v2/dist/` ಗೆ ಬರೆಯಲಾಗುತ್ತದೆ.

## ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ ಹೊಂದಾಣಿಕೆ

ClawMetry ಕೇವಲ OpenClaw ಅಲ್ಲದೆ ಅನೇಕ AI-ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಅಬ್ಸರ್ವ್ ಮಾಡುತ್ತದೆ. OpenClaw ಅಲ್ಲದ ಪ್ರತಿ ರನ್‌ಟೈಮ್ ಒಂದು ಮೀಸಲಾದ ರೀಡರ್ ಅಡಾಪ್ಟರ್ ಅನ್ನು ಹೊಂದಿದೆ ಅದು ಅದರ ಸ್ಥಳೀಯ ಸೆಷನ್ ಫಾರ್ಮ್ಯಾಟ್ ಅನ್ನು ClawMetry ನ ಏಕೀಕೃತ ಆಕಾರಗಳಿಗೆ ಭಾಷಾಂತರಿಸುತ್ತದೆ; ಡೀಮನ್ ಅವುಗಳನ್ನು ಅದೇ DuckDB ಸ್ಟೋರ್ + ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್‌ಗೆ ಇಂಜೆಸ್ಟ್ ಮಾಡುತ್ತದೆ, ರನ್‌ಟೈಮ್‌ನೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗಿದೆ, ಮತ್ತು ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಇದ್ದಾಗ Session replay ಟ್ಯಾಬ್ ಒಂದು **ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್** ಅನ್ನು ತೋರಿಸುತ್ತದೆ. ಪೂರ್ಣ ಮ್ಯಾಟ್ರಿಕ್ಸ್ + ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಸೇರಿಸಲು ಮಾರ್ಗದರ್ಶಿಗಾಗಿ [`docs/compatibility.md`](docs/compatibility.md) ಮತ್ತು OpenClaw-ಕುಟುಂಬ ಪ್ರೈಮರ್‌ಗಾಗಿ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ನೋಡಿ.

[Perplexity ಯ numbat](https://github.com/perplexityai/numbat) ಏಜೆಂಟ್-ಭದ್ರತಾ ಟೂಲ್ ಅನ್ನು ರನ್ ಮಾಡುತ್ತಿದ್ದೀರಾ? ClawMetry ಅದರ ಸಂಶೋಧನೆಗಳು ಮತ್ತು ಜಾರಿ ನಿರ್ಧಾರಗಳನ್ನು ಬಾಕ್ಸ್‌ನಿಂದ ಹೊರಗೆ ಇಂಜೆಸ್ಟ್ ಮಾಡುತ್ತದೆ — [`docs/NUMBAT.md`](docs/NUMBAT.md) ನೋಡಿ.

| ರನ್‌ಟೈಮ್ / ಏಜೆಂಟ್ | ಸ್ಥಿತಿ | ಟಿಪ್ಪಣಿಗಳು |
|---|---|---|
| **OpenClaw** | ಸ್ಥಳೀಯ | ಉಲ್ಲೇಖ ರನ್‌ಟೈಮ್, ಸ್ವಯಂ-ಪತ್ತೆಯಾಗಿದೆ |
| **PicoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಫ್ಲಾಟ್ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು. |
| **NanoClaw** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಸೆಷನ್ SQLite (`data/v2-sessions`). ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು + ಸಂದೇಶ ಎಣಿಕೆಗಳು. |
| **Hermes** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.hermes/state.db`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್‌ಗಳು/ವೆಚ್ಚ. |
| **Claude Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.claude/projects/.../<id>.jsonl`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು + ಚಿಂತನೆ, ಟೋಕನ್ ಬಳಕೆ. |
| **Codex** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ರೋಲ್‌ಔಟ್ JSONL `~/.codex/sessions/...`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Cursor** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `state.vscdb`. ಚಾಟ್/ಕಂಪೋಸರ್ ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ. |
| **Aider** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | ಪ್ರತಿ-ಪ್ರಾಜೆಕ್ಟ್ `.aider.chat.history.md`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೋಕನ್ ಎಣಿಕೆಗಳು. |
| **Goose** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/goose`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಒಟ್ಟುಗಳು. |
| **opencode** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.local/share/opencode`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Qwen Code** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.qwen/projects/.../chats`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್ ಬಳಕೆ. |
| **Pi** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | JSONL `~/.pi/agent/sessions`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **Deep Agents** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.deepagents/.state/sessions.db`. ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು, ಮಾದರಿ, ಟೂಲ್ ಕರೆಗಳು, ಟೋಕನ್‌ಗಳು + ವೆಚ್ಚ. |
| **n8n** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | SQLite `~/.n8n/database.sqlite`. ವರ್ಕ್‌ಫ್ಲೋ ಎಕ್ಸಿಕ್ಯೂಶನ್‌ಗಳು, ನೋಡ್ ರನ್‌ಗಳು, AI Agent ಪ್ರಾಂಪ್ಟ್‌ಗಳು, n8n ದಾಖಲಿಸಿದಲ್ಲಿ ಮಾದರಿ + ಟೋಕನ್‌ಗಳು. |
| **Antigravity** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | `~/.gemini/<flavor>/brain/` ಅಡಿಯಲ್ಲಿ ಬ್ರೈನ್ JSONL. ಸಂಭಾಷಣೆಗಳು, ಟೂಲ್ ಹಂತಗಳು, ಚಿಂತನೆ, ಪ್ರತಿ-ಜನರೇಶನ್ Gemini ಟೋಕನ್ ವಿಭಜನೆ + ವೆಚ್ಚ, ಹಿನ್ನೆಲೆ-ಜನರೇಶನ್ ಬರ್ನ್. |
| **GitHub Copilot** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | `~/.copilot/session-state/` ಅಡಿಯಲ್ಲಿ Copilot CLI `events.jsonl` + ಪ್ರತಿ-ಕರೆ ಬಳಕೆ ಲೆಡ್ಜರ್ `session-store.db`. ಸಂಭಾಷಣೆಗಳು, ಟೂಲ್ ಕರೆಗಳು, ಮಾದರಿ ರೂಟಿಂಗ್, ಕ್ಯಾಶ್-ಅರಿವಿನ ಟೋಕನ್ ವಿಭಜನೆ, ವೆಂಡರ್-ಬಿಲ್ ಮಾಡಿದ AI-ಕ್ರೆಡಿಟ್ ವೆಚ್ಚ. |
| **Grok** | ಬೀಟಾ ಅಡಾಪ್ಟರ್ | xAI Grok Build CLI (`~/.grok/bin/grok` ಅಡಿಯಲ್ಲಿ Rust ಬೈನರಿ): ಜಾಗತಿಕ ಈವೆಂಟ್ ಲಾಗ್ `~/.grok/logs/unified.jsonl` + ಪ್ರತಿ-ಸೆಷನ್ `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. ಸಂಭಾಷಣೆಗಳು, ಪ್ರತಿ-ಟರ್ನ್ ಟೋಕನ್ ವಿಭಜನೆ, ಮಾದರಿ ರೂಟಿಂಗ್, ಮತ್ತು `~/.grok/upload_queue/` ಅಡಿಯಲ್ಲಿ ಸ್ಟೇಜ್ ಮಾಡಿದ CLI ಯ ಔಟ್‌ಬೌಂಡ್ ರೆಪೊ ಪೇಲೋಡ್ ಆದ್ದರಿಂದ ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಏನು ಬಿಟ್ಟುಹೋಗಿದೆ ಎಂದು ನೀವು ನೋಡಬಹುದು. |

"ಬೀಟಾ ಅಡಾಪ್ಟರ್" ಎಂದರೆ ClawMetry ಆ ರನ್‌ಟೈಮ್‌ನ ನೈಜ ಆನ್-ಡಿಸ್ಕ್ ಫಾರ್ಮ್ಯಾಟ್‌ಗಾಗಿ ಒಂದು ರೀಡರ್ ಅನ್ನು ಶಿಪ್ ಮಾಡುತ್ತದೆ, ಪ್ರತಿಯೊಂದನ್ನೂ ನೈಜ ಯಂತ್ರದಲ್ಲಿ ನೈಜ ಇನ್‌ಸ್ಟಾಲ್ ವಿರುದ್ಧ ನಿರ್ಮಿಸಿ + ಪರಿಶೀಲಿಸಲಾಗಿದೆ (`tests/fixtures/runtimes/<rt>/` ನೋಡಿ). ಅಡಾಪ್ಟರ್‌ಗಳು ಓದಲು-ಮಾತ್ರ; ಪ್ರತಿಯೊಂದೂ ಅದರ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಏನನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ ಎಂಬುದರ ಬಗ್ಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ (ಉದಾ. PicoClaw/NanoClaw/Cursor ಡಿಸ್ಕ್‌ಗೆ ಟೋಕನ್ ವೆಚ್ಚವನ್ನು ಬರೆಯುವುದಿಲ್ಲ). ಒಂದೇ ನೋಡ್‌ನಲ್ಲಿ ಹಲವಾರು ರನ್‌ಟೈಮ್‌ಗಳು ರನ್ ಆದಾಗ, ರನ್‌ಟೈಮ್ ಸ್ವಿಚರ್ ಸ್ವಚ್ಛ ಡೀಪ್-ಡೈವ್‌ಗಾಗಿ ಸೆಷನ್‌ಗಳ ವೀಕ್ಷಣೆಯನ್ನು ಒಂದಕ್ಕೆ ಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

## ಯಾವುದೇ SDK ಏಜೆಂಟ್ ಅನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ — ಔಟ್-ಲೂಪ್ ವೆಚ್ಚ ಗುಣಲಕ್ಷಣ

ಮೇಲಿನ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್‌ಗಳು ಸೆಷನ್‌ಗಳನ್ನು ಡಿಸ್ಕ್‌ಗೆ ಬರೆಯುತ್ತವೆ. ನಿಮ್ಮ ಸ್ವಂತ **ಪ್ರೊಡಕ್ಷನ್ ಏಜೆಂಟ್** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ಅಥವಾ ಸರಳ `httpx` ಲೂಪ್‌ನಲ್ಲಿ ನೀವು ನಿರ್ಮಿಸಿದ್ದು — ಬರೆಯುವುದಿಲ್ಲ. ClawMetry ಯ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್ ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಇನ್ನೂ `httpx`/`requests` ಅನ್ನು ಮಂಕಿ-ಪ್ಯಾಚಿಂಗ್ ಮಾಡುವ ಮೂಲಕ ಅದರ LLM ಕರೆಗಳನ್ನು (ವೆಚ್ಚ, ಟೋಕನ್‌ಗಳು, ಲೇಟೆನ್ಸಿ, ದೋಷಗಳು) ಸೆರೆಹಿಡಿಯುತ್ತದೆ:

```python
import clawmetry.track            # ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ
clawmetry.track.set_source("support-agent")   # ಈ ಉತ್ಪನ್ನವನ್ನು ಹೆಸರಿಸಿ

# ...ನಿಮ್ಮ ಏಜೆಂಟ್ ಸಾಮಾನ್ಯವಾಗಿ ರನ್ ಆಗುತ್ತದೆ; ಪ್ರತಿ LLM ಕರೆ ಈಗ ಟ್ರ್ಯಾಕ್ + ಗುಣಲಕ್ಷಣಗೊಳಿಸಲಾಗಿದೆ.
```

`set_source()` (ಅಥವಾ `CLAWMETRY_SOURCE=support-agent` env var) ಪ್ರತಿ ಕರೆಯನ್ನು ಒಂದು **ಹೆಸರಿಸಿದ ಮೂಲ**ದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ರನ್ ಮಾಡುವ ಪ್ರತಿ ಉತ್ಪನ್ನವು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನ Overview ನಲ್ಲಿರುವ **🔌 Out-loop sources** ಕಾರ್ಡ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಪ್ರಥಮ ದರ್ಜೆಯ, ವೆಚ್ಚ-ಗುಣಲಕ್ಷಣ ಮಾಡಬಹುದಾದ ಸಾಲಿನಂತೆ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ — ಪ್ರತಿ ಏಜೆಂಟ್‌ಗೆ ಕರೆಗಳು, ಪೂರೈಕೆದಾರರು, ಲೇಟೆನ್ಸಿ, ದೋಷ ದರ. ಯಾವುದೇ ಮೂಲ ಸೆಟ್ ಮಾಡಿಲ್ಲವೇ? ಕರೆಗಳು ಇನ್ನೂ ಟ್ರ್ಯಾಕ್ ಆಗುತ್ತವೆ; ಕಾರ್ಡ್ ಮಾತ್ರ ಮರೆಯಾಗಿಯೇ ಉಳಿಯುತ್ತದೆ.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ಇದು ರನ್‌ಟೈಮ್ ಅಡಾಪ್ಟರ್‌ಗಳು ಫೀಡ್ ಮಾಡುವ ಅದೇ ಡೇಟಾ ಲೇಯರ್ (DuckDB → ಕ್ಲೌಡ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್), ಆದ್ದರಿಂದ ಔಟ್-ಲೂಪ್ ಮೂಲಗಳು ಎಲ್ಲದರಂತೆಯೇ ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸಿಂಕ್ ಆಗುತ್ತವೆ, E2E-ಎನ್‌ಕ್ರಿಪ್ಟೆಡ್.

## OpenTelemetry — ವೆಂಡರ್-ನ್ಯೂಟ್ರಲ್, ನಿಮ್ಮ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಗಾದರೂ ಕಳುಹಿಸಿ

ClawMetry **GenAI ಸೆಮ್ಯಾಂಟಿಕ್ ಕನ್ವೆನ್ಶನ್‌ಗಳನ್ನು** ಬಳಸಿ, ಎರಡೂ ದಿಕ್ಕುಗಳಲ್ಲಿ **OpenTelemetry** ಮಾತನಾಡುತ್ತದೆ, ಆದ್ದರಿಂದ ನಿಮ್ಮ ಏಜೆಂಟ್ ಟ್ರೇಸ್‌ಗಳು ಎಂದಿಗೂ ಒಂದೇ ಟೂಲ್‌ಗೆ ಲಾಕ್ ಆಗುವುದಿಲ್ಲ.

ಪ್ರತಿ ಸೆಷನ್ ಅನ್ನು **ಎಕ್ಸ್‌ಪೋರ್ಟ್** ಮಾಡಿ — LLM ಕರೆಗಳು, ಟೂಲ್‌ಗಳು, ಸಬ್-ಏಜೆಂಟ್‌ಗಳು, ಟೋಕನ್‌ಗಳು, ವೆಚ್ಚ — OTLP/HTTP GenAI ಸ್ಪ್ಯಾನ್‌ಗಳಾಗಿ ಯಾವುದೇ ಕಲೆಕ್ಟರ್‌ಗೆ (Datadog, Grafana, Honeycomb, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# ಸಮಾನಾರ್ಥಕವಾಗಿ:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ಆಥ್ ಹೆಡರ್‌ಗಳು ಮತ್ತು ಪೋಲ್ ಇಂಟರ್ವಲ್ ಐಚ್ಛಿಕ env var ಗಳಾಗಿವೆ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ಹೆಚ್ಚುವರಿ HTTP ಹೆಡರ್‌ಗಳು
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ಸೆಕೆಂಡುಗಳು (ಡೀಫಾಲ್ಟ್ 60)
```

**ಇಂಜೆಸ್ಟ್** — ಅಂತರ್ನಿರ್ಮಿತ OTLP ರಿಸೀವರ್ `/v1/traces` ಮತ್ತು `/v1/metrics` ನಲ್ಲಿ ಬೇರೆಲ್ಲದರಿಂದ ಟ್ರೇಸ್‌ಗಳು ಮತ್ತು ಮೆಟ್ರಿಕ್‌ಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ (protobuf ಇಂಜೆಸ್ಟ್‌ಗಾಗಿ `pip install clawmetry[otel]`).

ನಿಮಗೆ ಶೂನ್ಯ-ಕಾನ್ಫಿಗ್, ಸ್ಥಳೀಯ-ಮೊದಲ ClawMetry ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ **ಮತ್ತು** ನಿಮ್ಮ ತಂಡ ಈಗಾಗಲೇ ರನ್ ಮಾಡುತ್ತಿರುವ ಯಾವುದೇ ಬ್ಯಾಕೆಂಡ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಡೇಟಾ ಸಿಗುತ್ತದೆ — ಯಾವುದೇ ಲಾಕ್-ಇನ್ ಇಲ್ಲ, ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು ಎರಡನೇ ಏಜೆಂಟ್ ಇಲ್ಲ.

## ಕಾನ್ಫಿಗರೇಶನ್

ಹೆಚ್ಚಿನ ಜನರಿಗೆ ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಅಗತ್ಯವಿಲ್ಲ. ClawMetry ನಿಮ್ಮ ವರ್ಕ್‌ಸ್ಪೇಸ್, ಲಾಗ್‌ಗಳು, ಸೆಷನ್‌ಗಳು ಮತ್ತು ಕ್ರಾನ್‌ಗಳನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

ನೀವು ಕಸ್ಟಮೈಸ್ ಮಾಡಬೇಕಾದರೆ:

```bash
clawmetry --port 9000              # ಕಸ್ಟಮ್ ಪೋರ್ಟ್ (ಡೀಫಾಲ್ಟ್: 8900)
clawmetry --host 127.0.0.1         # ಕೇವಲ localhost ಗೆ ಬೈಂಡ್ ಮಾಡಿ
clawmetry --workspace ~/mybot      # ಕಸ್ಟಮ್ ವರ್ಕ್‌ಸ್ಪೇಸ್ ಪಥ
clawmetry --name "Alice"           # Flow ವಿಷುವಲೈಸೇಶನ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಹೆಸರು
```

ಎಲ್ಲಾ ಆಯ್ಕೆಗಳು: `clawmetry --help`

## ಬೆಂಬಲಿತ ಚಾನಲ್‌ಗಳು

ನೀವು ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಪ್ರತಿ OpenClaw ಚಾನಲ್‌ಗೆ ClawMetry ಲೈವ್ ಚಟುವಟಿಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ನಿಮ್ಮ `openclaw.json` ನಲ್ಲಿ ವಾಸ್ತವವಾಗಿ ಸೆಟಪ್ ಆಗಿರುವ ಚಾನಲ್‌ಗಳು ಮಾತ್ರ Flow ಡಯಾಗ್ರಾಂನಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ — ಕಾನ್ಫಿಗರ್ ಮಾಡದವುಗಳು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಮರೆಮಾಡಲ್ಪಡುತ್ತವೆ.

Flow ನಲ್ಲಿ ಯಾವುದೇ ಚಾನಲ್ ನೋಡ್ ಅನ್ನು ಕ್ಲಿಕ್ ಮಾಡಿ ಆಗಮಿಸುವ/ಹೊರಹೋಗುವ ಸಂದೇಶ ಎಣಿಕೆಗಳೊಂದಿಗೆ ಲೈವ್ ಚಾಟ್ ಬಬಲ್ ವೀಕ್ಷಣೆಯನ್ನು ನೋಡಲು.

| ಚಾನಲ್ | ಸ್ಥಿತಿ | ಲೈವ್ ಪಾಪ್‌ಅಪ್ | ಟಿಪ್ಪಣಿಗಳು |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ಪೂರ್ಣ | ✅ | ಸಂದೇಶಗಳು, ಅಂಕಿಅಂಶಗಳು, 10s ರಿಫ್ರೆಶ್ |
| 💬 **iMessage** | ✅ ಪೂರ್ಣ | ✅ | `~/Library/Messages/chat.db` ಅನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ |
| 💚 **WhatsApp** | ✅ ಪೂರ್ಣ | ✅ | WhatsApp Web (Baileys) ಮೂಲಕ |
| 🔵 **Signal** | ✅ ಪೂರ್ಣ | ✅ | signal-cli ಮೂಲಕ |
| 🟣 **Discord** | ✅ ಪೂರ್ಣ | ✅ | ಗಿಲ್ಡ್ + ಚಾನಲ್ ಪತ್ತೆ |
| 🟪 **Slack** | ✅ ಪೂರ್ಣ | ✅ | ವರ್ಕ್‌ಸ್ಪೇಸ್ + ಚಾನಲ್ ಪತ್ತೆ |
| 🌐 **Webchat** | ✅ ಪೂರ್ಣ | ✅ | ಅಂತರ್ನಿರ್ಮಿತ ವೆಬ್ UI ಸೆಷನ್‌ಗಳು |
| 📡 **IRC** | ✅ ಪೂರ್ಣ | ✅ | ಟರ್ಮಿನಲ್-ಶೈಲಿಯ ಬಬಲ್ UI |
| 🍏 **BlueBubbles** | ✅ ಪೂರ್ಣ | ✅ | BlueBubbles REST API ಮೂಲಕ iMessage |
| 🔵 **Google Chat** | ✅ ಪೂರ್ಣ | ✅ | Chat API ವೆಬ್‌ಹುಕ್‌ಗಳ ಮೂಲಕ |
| 🟣 **MS Teams** | ✅ ಪೂರ್ಣ | ✅ | Teams bot ಪ್ಲಗಿನ್ ಮೂಲಕ |
| 🔷 **Mattermost** | ✅ ಪೂರ್ಣ | ✅ | ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ ತಂಡ ಚಾಟ್ |
| 🟩 **Matrix** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ, E2EE ಬೆಂಬಲ |
| 🟢 **LINE** | ✅ ಪೂರ್ಣ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ಪೂರ್ಣ | ✅ | ವಿಕೇಂದ್ರೀಕೃತ NIP-04 DM ಗಳು |
| 🟣 **Twitch** | ✅ ಪೂರ್ಣ | ✅ | IRC ಸಂಪರ್ಕದ ಮೂಲಕ ಚಾಟ್ |
| 🔷 **Feishu/Lark** | ✅ ಪೂರ್ಣ | ✅ | WebSocket ಈವೆಂಟ್ ಚಂದಾದಾರಿಕೆ |
| 🔵 **Zalo** | ✅ ಪೂರ್ಣ | ✅ | Zalo Bot API |

> **ಸ್ವಯಂ-ಪತ್ತೆ:** ClawMetry ನಿಮ್ಮ `~/.openclaw/openclaw.json` ಅನ್ನು ಓದುತ್ತದೆ ಮತ್ತು ನೀವು ವಾಸ್ತವವಾಗಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಚಾನಲ್‌ಗಳನ್ನು ಮಾತ್ರ ರೆಂಡರ್ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಹಸ್ತಚಾಲಿತ ಸೆಟಪ್ ಅಗತ್ಯವಿಲ್ಲ.

## Docker ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

ClawMetry ಅನ್ನು ಕಂಟೇನರ್‌ನಲ್ಲಿ ರನ್ ಮಾಡಬೇಕೇ? ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ! 🐳

**Docker ನೊಂದಿಗೆ ಶೀಘ್ರ ಆರಂಭ:**

```bash
# ಇಮೇಜ್ ಅನ್ನು ನಿರ್ಮಿಸಿ
docker build -t clawmetry .

# ಡೀಫಾಲ್ಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳೊಂದಿಗೆ ರನ್ ಮಾಡಿ
docker run -p 8900:8900 clawmetry

# ಅಥವಾ ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ ಡೈರ್ ಅನ್ನು ಮೌಂಟ್ ಮಾಡಿ (ತೋರಿಸಲಾಗಿದೆ: OpenClaw ನ ~/.openclaw)
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

> **ಗಮನಿಸಿ:** Docker ನಲ್ಲಿ ರನ್ ಮಾಡುವಾಗ, ClawMetry ನಿಮ್ಮ ಸೆಟಪ್ ಅನ್ನು ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುವಂತೆ ನಿಮ್ಮ ಏಜೆಂಟ್‌ನ ಡೇಟಾ + ಲಾಗ್ ಡೈರೆಕ್ಟರಿಗಳನ್ನು (ಉದಾ. `~/.openclaw`, `~/.claude`, `~/.codex`) ಮೌಂಟ್ ಮಾಡಿ.

## ಅಗತ್ಯತೆಗಳು

- Python 3.8+
- Flask (pip ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಇನ್‌ಸ್ಟಾಲ್ ಆಗುತ್ತದೆ)
- ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಒಂದು AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, ಅಥವಾ QM (ಅಥವಾ Docker ಗಾಗಿ ಮೌಂಟ್ ಮಾಡಿದ ವಾಲ್ಯೂಮ್‌ಗಳು)
- Linux ಅಥವಾ macOS

## NemoClaw / OpenShell ಬೆಂಬಲ

ClawMetry ಸ್ವಯಂಚಾಲಿತವಾಗಿ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ಅನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ — sandboxed OpenShell ಕಂಟೇನರ್‌ಗಳಲ್ಲಿ ಏಜೆಂಟ್‌ಗಳನ್ನು ರನ್ ಮಾಡುವ OpenClaw ಗಾಗಿ NVIDIA ಯ ಎಂಟರ್‌ಪ್ರೈಸ್ ಭದ್ರತಾ ವ್ರ್ಯಾಪರ್.

ಹೆಚ್ಚಿನ ಸಂದರ್ಭಗಳಲ್ಲಿ ಯಾವುದೇ ಹೆಚ್ಚುವರಿ ಕಾನ್ಫಿಗರೇಶನ್ ಅಗತ್ಯವಿಲ್ಲ. ಸಿಂಕ್ ಡೀಮನ್ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಹೋಸ್ಟ್‌ನಲ್ಲಿ `~/.openclaw/` ನಲ್ಲಿ ಇರಲಿ ಅಥವಾ OpenShell ಕಂಟೇನರ್‌ನೊಳಗೆ ಇರಲಿ ಸ್ವಯಂ-ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

### ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

ClawMetry ಎರಡು ರೀತಿಯಲ್ಲಿ NemoClaw ಅನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ:

1. **ಬೈನರಿ ಪತ್ತೆ** — `nemoclaw` CLI ಗಾಗಿ ಪರಿಶೀಲಿಸುತ್ತದೆ ಮತ್ತು sandbox ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು `nemoclaw status` ಅನ್ನು ರನ್ ಮಾಡುತ್ತದೆ
2. **ಕಂಟೇನರ್ ಪತ್ತೆ** — `openshell`, `nemoclaw`, ಅಥವಾ `ghcr.io/nvidia/` ಇಮೇಜ್‌ಗಳಿಗಾಗಿ ರನ್ ಆಗುತ್ತಿರುವ Docker ಕಂಟೇನರ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡುತ್ತದೆ, ನಂತರ ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು ಅಥವಾ `docker cp` ಮೂಲಕ ಸೆಷನ್‌ಗಳನ್ನು ಓದುತ್ತದೆ

NemoClaw ಕಂಟೇನರ್‌ಗಳಿಂದ ಸಿಂಕ್ ಮಾಡಿದ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಕ್ಲೌಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ `runtime=nemoclaw` ಮತ್ತು `container_id` ಮೆಟಾಡೇಟಾದೊಂದಿಗೆ ಟ್ಯಾಗ್ ಮಾಡಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ನೀವು ಅವುಗಳನ್ನು ಒಂದೇ ನೋಟದಲ್ಲಿ ಪ್ರಮಾಣಿತ OpenClaw ಸೆಷನ್‌ಗಳಿಂದ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

### ಶಿಫಾರಸು ಮಾಡಿದ ಸೆಟಪ್: HOST ನಲ್ಲಿ ಸಿಂಕ್ ಡೀಮನ್

ಉತ್ತಮ ಅನುಭವಕ್ಕಾಗಿ, ClawMetry ಯ ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು **ಹೋಸ್ಟ್ ಯಂತ್ರ**ದಲ್ಲಿ ರನ್ ಮಾಡಿ (sandbox ಒಳಗೆ ಅಲ್ಲ). ಇದು NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿ ನಿರ್ಬಂಧಗಳನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.

```bash
# ಹೋಸ್ಟ್‌ನಲ್ಲಿ (sandbox ಹೊರಗೆ)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ಸಿಂಕ್ ಡೀಮನ್ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಯಾವುದೇ ರನ್ ಆಗುತ್ತಿರುವ OpenShell ಕಂಟೇನರ್‌ಗಳ ಒಳಗೆ ಸೆಷನ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ.

### ಐಚ್ಛಿಕ: ಸ್ಪಷ್ಟ sandbox ಹೆಸರು

ಸ್ವಯಂ-ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸದಿದ್ದರೆ, ClawMetry ಅನ್ನು ಸರಿಯಾದ sandbox ಗೆ ತೋರಿಸಿ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox ಒಳಗೆ ರನ್ ಮಾಡುವುದು (ಸುಧಾರಿತ)

ನೀವು ಸಿಂಕ್ ಡೀಮನ್ ಅನ್ನು OpenShell sandbox **ಒಳಗೆ** ರನ್ ಮಾಡಬೇಕಾದರೆ, ಅದು ClawMetry ಇಂಜೆಸ್ಟ್ API ಅನ್ನು ತಲುಪಬಹುದಾಗಿ ನಿಮ್ಮ NemoClaw ನೆಟ್‌ವರ್ಕ್ ನೀತಿಗೆ ಈ egress ನಿಯಮವನ್ನು ಸೇರಿಸಿ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ಅನ್ವಯಿಸಲು:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ಪೋರ್ಟ್‌ಗಳು ಮತ್ತು ಎಂಡ್‌ಪಾಯಿಂಟ್‌ಗಳು

| ಎಂಡ್‌ಪಾಯಿಂಟ್ | ಪೋರ್ಟ್ | ಪ್ರೋಟೋಕಾಲ್ | ಅಗತ್ಯವಿದೆಯೇ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ಹೌದು (ಸಿಂಕ್ ಡೀಮನ್ → ಕ್ಲೌಡ್) |
| `localhost:8900` | 8900 | HTTP | ಹೌದು (ಸ್ಥಳೀಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ UI) |
| Docker ಸಾಕೆಟ್ (`/var/run/docker.sock`) | — | Unix ಸಾಕೆಟ್ | ಕಂಟೇನರ್ ಸೆಷನ್ ಶೋಧನೆಗಾಗಿ |

ಸಿಂಕ್ ಡೀಮನ್ ಕೇವಲ `ingest.clawmetry.com` ಗೆ ಔಟ್‌ಬೌಂಡ್ HTTPS ಕರೆಗಳನ್ನು ಮಾತ್ರ ಮಾಡುತ್ತದೆ. ಯಾವುದೇ ಇನ್‌ಬೌಂಡ್ ಪೋರ್ಟ್‌ಗಳು ಅಗತ್ಯವಿಲ್ಲ.

---

## ಕ್ಲೌಡ್ ಡಿಪ್ಲಾಯ್‌ಮೆಂಟ್

SSH ಟನಲ್‌ಗಳು, ರಿವರ್ಸ್ ಪ್ರಾಕ್ಸಿ, ಮತ್ತು Docker ಗಾಗಿ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ನೋಡಿ.

## ಪರೀಕ್ಷೆ

ಈ ಪ್ರಾಜೆಕ್ಟ್ ಅನ್ನು BrowserStack ನೊಂದಿಗೆ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ಟೆಲಿಮೆಟ್ರಿ

ClawMetry ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್-ಲೈಫ್‌ಸೈಕಲ್ ಪಿಂಗ್‌ಗಳನ್ನು
`https://app.clawmetry.com/api/install` ಗೆ ಕಳುಹಿಸುತ್ತದೆ: ಹೊಸ ಯಂತ್ರದಲ್ಲಿ ನೀವು `clawmetry` CLI ಅನ್ನು
ಮೊದಲ ಬಾರಿಗೆ ರನ್ ಮಾಡಿದಾಗ ಒಂದು `install` ಪಿಂಗ್, ಹೊಸ ಆವೃತ್ತಿಗೆ ಅಪ್‌ಗ್ರೇಡ್ ಮಾಡಿದ ನಂತರ ಮೊದಲ ರನ್‌ನಲ್ಲಿ ಒಂದು `update`
ಪಿಂಗ್, ಮತ್ತು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನೊಳಗಿನ ಆನ್‌ಬೋರ್ಡಿಂಗ್ ಆಯ್ಕೆಯನ್ನು ನೀವು ಪೂರ್ಣಗೊಳಿಸಿದಾಗ ಒಂದು `onboarded`
ಪಿಂಗ್. ನಿಜವಾದ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು ಎಣಿಸಲು ನಾವು ಇದನ್ನು ಬಳಸುತ್ತೇವೆ (ಕಚ್ಚಾ PyPI ಡೌನ್‌ಲೋಡ್
ಸಂಖ್ಯೆಗಳು ~98% ಮಿರರ್‌ಗಳು, CI, ಮತ್ತು ಆಟೋ-ಅಪ್‌ಡೇಟ್ ಮರು-ಡೌನ್‌ಲೋಡ್‌ಗಳಾಗಿವೆ) ಮತ್ತು ಯಾವ ಏಜೆಂಟ್ ಫ್ರೇಮ್‌ವರ್ಕ್‌ಗಳು ಮತ್ತು
ಆವೃತ್ತಿಗಳು ವಾಸ್ತವವಾಗಿ ಬಳಕೆಯಲ್ಲಿವೆ ಎಂದು ತಿಳಿಯಲು.

**ಪ್ರತಿ ಆವೃತ್ತಿಗೆ ಪ್ರತಿ ಲೈಫ್‌ಸೈಕಲ್ ಈವೆಂಟ್‌ಗೆ ಗರಿಷ್ಠ ಒಂದು POST**, ಇದನ್ನು ಒಳಗೊಂಡಿದೆ:

| ಫೀಲ್ಡ್ | ಉದಾಹರಣೆ | ಏಕೆ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಿದ ಯಾದೃಚ್ಛಿಕ UUID | ಡುಪ್ಲಿಕೇಟ್ ತೆಗೆಯುವುದು; ನೀವು ಸ್ಪಷ್ಟವಾಗಿ Cloud sync ಅನ್ನು ಸಂಪರ್ಕಿಸುವವರೆಗೆ ಅನಾಮಧೇಯ (ಆಗ ದೃಢೀಕೃತ ಡೀಮನ್ ಹೃದಯಬಡಿತ ಅದನ್ನು ಸಾಗಿಸುತ್ತದೆ, ಈ ಇನ್‌ಸ್ಟಾಲ್ ಅನ್ನು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ) |
| `event` | `install` / `update` / `onboarded` | ಹೊಸ ಇನ್‌ಸ್ಟಾಲ್ vs ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ಒಂದರ ಅಪ್‌ಗ್ರೇಡ್ |
| `version` | `0.12.167` | ಬಳಕೆಯಲ್ಲಿರುವ ಆವೃತ್ತಿಗಳು |
| `os` / `os_version` | `Darwin` / `25.3.0` | ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಬೆಂಬಲ ಆದ್ಯತೆಗಳು |
| `python` | `3.11.15` | Python ಆವೃತ್ತಿ ಬೆಂಬಲ ಮ್ಯಾಟ್ರಿಕ್ಸ್ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ಮುಂದೆ ನಾವು ಯಾವ ಏಜೆಂಟ್‌ಗಳೊಂದಿಗೆ ಸಂಯೋಜಿಸಬೇಕು |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ಮಾನವ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳನ್ನು CI ಶಬ್ದದಿಂದ ಪ್ರತ್ಯೇಕಿಸಿ |

**ನಾವು ಏನನ್ನೂ ಕಳುಹಿಸುವುದಿಲ್ಲ**: IP (ಕ್ಲೌಡ್ ಸರ್ವರ್-ಸೈಡ್‌ನಲ್ಲಿ ವಿನಂತಿಯಿಂದ
ದೇಶ ಕೋಡ್ ಅನ್ನು ಪಡೆಯುತ್ತದೆ, ನಂತರ IP ಅನ್ನು ತಿರಸ್ಕರಿಸುತ್ತದೆ), ಹೋಸ್ಟ್‌ನೇಮ್, ಬಳಕೆದಾರಹೆಸರು, ವರ್ಕ್‌ಸ್ಪೇಸ್
ಪಥ, ಫೈಲ್ ವಿಷಯಗಳು, ನಿಮ್ಮ api_key, ನಿಮ್ಮ ಇಮೇಲ್, ಯಾವುದೇ PII ಅಥವಾ
ವರ್ಕ್‌ಸ್ಪೇಸ್-ನಿರ್ದಿಷ್ಟವಾದದ್ದು. ವೈರ್ ಪೇಲೋಡ್
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ನಲ್ಲಿ ಆಡಿಟ್ ಮಾಡಬಹುದಾಗಿದೆ.

**ಆಪ್ಟ್ ಔಟ್ ಮಾಡಿ** (ಇವುಗಳಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದು ಶಾಶ್ವತವಾಗಿ ಇದನ್ನು ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ಪ್ರತಿ-ಶೆಲ್
export DO_NOT_TRACK=1                          # W3C ಕ್ರಾಸ್-ಟೂಲ್ ಸ್ಟ್ಯಾಂಡರ್ಡ್
touch ~/.clawmetry/notelemetry                 # ಶಾಶ್ವತ ಫೈಲ್ ಮಾರ್ಕರ್
```

ಇಲ್ಲಿ ನೆಟ್‌ವರ್ಕ್ ವಿಫಲತೆ ಎಂದಿಗೂ `clawmetry` ಅನ್ನು ರನ್ ಆಗುವುದನ್ನು ತಡೆಯುವುದಿಲ್ಲ — ಪಿಂಗ್
3 ಸೆಕೆಂಡ್ ಟೈಮ್‌ಔಟ್‌ನೊಂದಿಗೆ ಡೀಮನ್ ಥ್ರೆಡ್‌ನಲ್ಲಿ ಫೈರ್-ಅಂಡ್-ಫರ್ಗೆಟ್ ಆಗಿದೆ.

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
  <strong>🦞 ನಿಮ್ಮ ಏಜೆಂಟ್ ಚಿಂತಿಸುವುದನ್ನು ನೋಡಿ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ನಿಂದ ನಿರ್ಮಿಸಲ್ಪಟ್ಟಿದೆ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ಪರಿಸರ ವ್ಯವಸ್ಥೆಯ ಭಾಗ</sub>
</p>
