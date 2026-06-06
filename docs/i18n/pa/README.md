<!-- i18n-src:48548997be76 -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਵੇਖੋ।** **12 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਨਿਗਰਾਨੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 8 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਸ ਭਾਸ਼ਾ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਕੋਈ ਸੈਟਿੰਗ ਨਹੀਂ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਖੋਜਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ ਅਤੇ ਤੁਸੀਂ ਤਿਆਰ ਹੋ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਨੇ OpenClaw ਲਈ ਨਿਗਰਾਨੀ ਵਜੋਂ ਸ਼ੁਰੂਆਤ ਕੀਤੀ, ਅਤੇ ਹੁਣ ਇੱਕ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਤੁਹਾਡੇ **ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ** ਨੂੰ ਮਾਪਦਾ ਹੈ, ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੇ ਹਰ ਰਨਟਾਈਮ ਆਪਣੇ ਆਪ ਖੋਜਦਾ ਹੈ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw ਅਤੇ NemoClaw ਓਪਨ-ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ ਹਨ; ਬਾਕੀ ਰਨਟਾਈਮ ClawMetry Cloud ਜਾਂ ਸਵੈ-ਹੋਸਟ ਕੀਤੇ Pro ਲਾਇਸੈਂਸ ਨਾਲ ਕਿਰਿਆਸ਼ੀਲ ਹੁੰਦੇ ਹਨ। ਹੈਡਰ ਤੋਂ ਰਨਟਾਈਮ ਬਦਲੋ ਅਤੇ ਹਰ ਟੈਬ — ਲਾਗਤ, ਟੋਕਨ, ਟੂਲ, ਟ੍ਰੇਸ — ਉਸ ਰਨਟਾਈਮ ਲਈ ਮੁੜ-ਸਕੋਪ ਹੋ ਜਾਂਦੀ ਹੈ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **Flow** — ਲਾਈਵ ਐਨੀਮੇਟਡ ਡਾਇਗ੍ਰਾਮ ਜੋ ਚੈਨਲਾਂ, ਦਿਮਾਗ, ਟੂਲਾਂ ਅਤੇ ਵਾਪਸ ਵਹਿੰਦੇ ਸੁਨੇਹੇ ਦਿਖਾਉਂਦਾ ਹੈ
- **Overview** — ਸਿਹਤ ਜਾਂਚਾਂ, ਗਤੀਵਿਧੀ ਹੀਟਮੈਪ, ਸੈਸ਼ਨ ਗਿਣਤੀ, ਮਾਡਲ ਜਾਣਕਾਰੀ
- **Usage** — ਰੋਜ਼ਾਨਾ/ਹਫ਼ਤਾਵਾਰੀ/ਮਹੀਨਾਵਾਰੀ ਵਿਭਾਜਨ ਨਾਲ ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਟਰੈਕਿੰਗ
- **Sessions** — ਮਾਡਲ, ਟੋਕਨ, ਆਖਰੀ ਗਤੀਵਿਧੀ ਸਮੇਤ ਸਰਗਰਮ ਏਜੰਟ ਸੈਸ਼ਨ
- **Crons** — ਸਥਿਤੀ, ਅਗਲੀ ਰਨ, ਮਿਆਦ ਸਮੇਤ ਅਨੁਸੂਚਿਤ ਕੰਮ
- **Logs** — ਰੰਗ-ਕੋਡ ਕੀਤੀ ਰੀਅਲ-ਟਾਈਮ ਲੌਗ ਸਟ੍ਰੀਮਿੰਗ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ਰੋਜ਼ਾਨਾ ਨੋਟ ਬ੍ਰਾਉਜ਼ ਕਰੋ
- **Transcripts** — ਸੈਸ਼ਨ ਇਤਿਹਾਸ ਪੜ੍ਹਨ ਲਈ ਚੈਟ-ਬਬਲ UI
- **Alerts** — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, ਏਜੰਟ-ਔਫਲਾਈਨ ਖੋਜ; Slack, Discord, PagerDuty, Telegram, Email ਤੇ ਭੇਜਦਾ ਹੈ
- **Approvals** — ਵਿਨਾਸ਼ਕਾਰੀ ਮਿਟਾਉਣੇ, ਫੋਰਸ ਪੁਸ਼, DB ਮਿਊਟੇਸ਼ਨ, sudo, ਪੈਕੇਜ ਇੰਸਟਾਲ, ਨੈੱਟਵਰਕ ਕਾਲਾਂ ਨੂੰ ਇੱਕ-ਕਲਿੱਕ ਸਾਈਨ-ਆਫ ਪਿੱਛੇ ਗੇਟ ਕਰੋ

## ਸਕ੍ਰੀਨਸ਼ੌਟ

### 🧠 Brain — ਲਾਈਵ ਏਜੰਟ ਇਵੈਂਟ ਸਟ੍ਰੀਮ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ਟੋਕਨ ਵਰਤੋਂ ਅਤੇ ਸੈਸ਼ਨ ਸੰਖੇਪ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ਰੀਅਲ-ਟਾਈਮ ਟੂਲ ਕਾਲ ਫੀਡ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਅਨੁਸਾਰ ਲਾਗਤ ਵਿਭਾਜਨ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ਵਰਕਸਪੇਸ ਫਾਈਲ ਬ੍ਰਾਉਜ਼ਰ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ਸਥਿਤੀ ਅਤੇ ਆਡਿਟ ਲੌਗ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, Slack / Discord / PagerDuty / Email ਤੇ ਵੈਬਹੁੱਕ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ਜੋਖਮ ਭਰੇ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਹੱਥੀਂ ਸਾਈਨ-ਆਫ ਪਿੱਛੇ ਗੇਟ ਕਰੋ; ਨੀਤੀ-ਸਮਰਥਿਤ ਸੁਰੱਖਿਆ ਨਿਯਮ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ਇੰਸਟਾਲ ਕਰੋ

**ਇੱਕ-ਲਾਈਨ (ਸਿਫਾਰਸ਼ੀ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**ਸੋਰਸ ਤੋਂ:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ਫਰੰਟਐਂਡ ਡਿਵੈਲਪਮੈਂਟ

v2 React ਐਪ `frontend/` ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ ਅਤੇ `/v2` ਤੇ ਪਰੋਸੀ ਜਾਂਦੀ ਹੈ ਜਦੋਂ Flask ਸਰਵਰ v2 ਯੋਗ ਨਾਲ ਸ਼ੁਰੂ ਕੀਤਾ ਜਾਂਦਾ ਹੈ।

ਡਿਵੈਲਪ ਕਰਦੇ ਵੇਲੇ ਦੋ ਟਰਮੀਨਲ ਵਰਤੋ:

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

`http://localhost:5173/v2/` ਖੋਲ੍ਹੋ। Vite, `/api` ਬੇਨਤੀਆਂ ਨੂੰ `http://localhost:8900` ਤੇ ਪ੍ਰੌਕਸੀ ਕਰਦਾ ਹੈ, ਇਸਲਈ React ਐਪ ਬਿਨਾਂ ਵਾਧੂ CORS ਸੈਟਅਪ ਦੇ ਲੋਕਲ Flask ਸਰਵਰ ਨਾਲ ਗੱਲ ਕਰ ਸਕਦੀ ਹੈ।

Python ਪੈਕੇਜ ਨਾਲ ਸ਼ਿਪ ਹੋਣ ਵਾਲਾ ਬੰਡਲ ਬਣਾਉਣ ਲਈ:

```bash
cd frontend
npm run build
```

ਪ੍ਰੋਡਕਸ਼ਨ ਬੰਡਲ `clawmetry/static/v2/dist/` ਵਿੱਚ ਲਿਖਿਆ ਜਾਂਦਾ ਹੈ।

## ਰਨਟਾਈਮ / ਏਜੰਟ ਅਨੁਕੂਲਤਾ

ClawMetry ਕਈ AI-ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਦੀ ਨਿਗਰਾਨੀ ਕਰਦਾ ਹੈ, ਨਾ ਕਿ ਸਿਰਫ਼ OpenClaw। ਹਰ ਗੈਰ-OpenClaw ਰਨਟਾਈਮ ਇੱਕ ਸਮਰਪਿਤ ਰੀਡਰ ਅਡੈਪਟਰ ਭੇਜਦਾ ਹੈ ਜੋ ਇਸਦੇ ਮੂਲ ਸੈਸ਼ਨ ਫਾਰਮੈਟ ਨੂੰ ClawMetry ਦੀਆਂ ਇਕੱਠੀਆਂ ਆਕ੍ਰਿਤੀਆਂ ਵਿੱਚ ਬਦਲਦਾ ਹੈ; ਡੀਮਨ ਉਹਨਾਂ ਨੂੰ ਰਨਟਾਈਮ ਨਾਲ ਟੈਗ ਕਰਕੇ ਉਸੇ DuckDB ਸਟੋਰ ਅਤੇ ਕਲਾਉਡ ਸਨੈਪਸ਼ੌਟ ਵਿੱਚ ਖਿੱਚਦਾ ਹੈ, ਅਤੇ ਸੈਸ਼ਨ ਰੀਪਲੇ ਟੈਬ ਇੱਕ **ਰਨਟਾਈਮ ਸਵਿੱਚਰ** ਦਿਖਾਉਂਦੀ ਹੈ ਜਦੋਂ ਇੱਕ ਤੋਂ ਵੱਧ ਮੌਜੂਦ ਹੋਣ। ਪੂਰੇ ਮੈਟ੍ਰਿਕਸ ਅਤੇ ਰਨਟਾਈਮ ਜੋੜਨ ਦੀ ਗਾਈਡ ਲਈ [`docs/compatibility.md`](docs/compatibility.md) ਵੇਖੋ, ਅਤੇ OpenClaw-ਪਰਿਵਾਰ ਪ੍ਰਾਈਮਰ ਲਈ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ਵੇਖੋ।

| ਰਨਟਾਈਮ / ਏਜੰਟ | ਸਥਿਤੀ | ਨੋਟ |
|---|---|---|
| **OpenClaw** | ਮੂਲ | ਸੰਦਰਭ ਰਨਟਾਈਮ, ਆਪਣੇ ਆਪ ਖੋਜਿਆ ਜਾਂਦਾ ਹੈ |
| **PicoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਫਲੈਟ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ। |
| **NanoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ-ਸੈਸ਼ਨ SQLite (`data/v2-sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ ਅਤੇ ਸੁਨੇਹਾ ਗਿਣਤੀ। |
| **Hermes** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.hermes/state.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ/ਲਾਗਤ। |
| **Claude Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.claude/projects/.../<id>.jsonl`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ ਅਤੇ ਸੋਚ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Codex** | ਬੀਟਾ ਅਡੈਪਟਰ | Rollout JSONL `~/.codex/sessions/...`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Cursor** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `state.vscdb`। ਚੈਟ/ਕੰਪੋਜ਼ਰ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ। |
| **Aider** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ ਪ੍ਰੋਜੈਕਟ `.aider.chat.history.md`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ ਗਿਣਤੀ। |
| **Goose** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/goose`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਕੁੱਲ। |
| **opencode** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/opencode`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਅਤੇ ਲਾਗਤ। |
| **Qwen Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.qwen/projects/.../chats`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |

"ਬੀਟਾ ਅਡੈਪਟਰ" ਦਾ ਮਤਲਬ ਹੈ ਕਿ ClawMetry ਉਸ ਰਨਟਾਈਮ ਦੇ ਅਸਲ ਆਨ-ਡਿਸਕ ਫਾਰਮੈਟ ਲਈ ਇੱਕ ਰੀਡਰ ਭੇਜਦਾ ਹੈ, ਹਰ ਇੱਕ ਅਸਲ ਮਸ਼ੀਨ ਤੇ ਅਸਲ ਇੰਸਟਾਲ ਦੇ ਵਿਰੁੱਧ ਬਣਾਇਆ ਅਤੇ ਪ੍ਰਮਾਣਿਤ ਕੀਤਾ ਗਿਆ ਹੈ (ਵੇਖੋ `tests/fixtures/runtimes/<rt>/`)। ਅਡੈਪਟਰ ਸਿਰਫ਼ ਪੜ੍ਹਦੇ ਹਨ; ਹਰ ਇੱਕ ਇਮਾਨਦਾਰ ਹੈ ਕਿ ਇਸਦਾ ਰਨਟਾਈਮ ਅਸਲ ਵਿੱਚ ਕੀ ਸਟੋਰ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ PicoClaw/NanoClaw/Cursor ਡਿਸਕ ਤੇ ਟੋਕਨ ਲਾਗਤ ਨਹੀਂ ਲਿਖਦੇ)। ਜਦੋਂ ਕਈ ਰਨਟਾਈਮ ਇੱਕ ਨੋਡ ਤੇ ਚੱਲਦੇ ਹਨ, ਰਨਟਾਈਮ ਸਵਿੱਚਰ ਡੂੰਘੀ ਜਾਣਕਾਰੀ ਲਈ ਸੈਸ਼ਨ ਵਿਊ ਨੂੰ ਇੱਕ ਤੱਕ ਸੀਮਤ ਕਰਦਾ ਹੈ।

## ਕਿਸੇ ਵੀ SDK ਏਜੰਟ ਨੂੰ ਟਰੈਕ ਕਰੋ — ਆਉਟ-ਲੂਪ ਲਾਗਤ ਅਟਰੀਬਿਊਸ਼ਨ

ਉੱਪਰ ਦਿੱਤੇ ਰਨਟਾਈਮ ਸਾਰੇ ਸੈਸ਼ਨ ਡਿਸਕ ਤੇ ਲਿਖਦੇ ਹਨ। ਤੁਹਾਡਾ ਆਪਣਾ **ਪ੍ਰੋਡਕਸ਼ਨ ਏਜੰਟ** — ਜੋ ਤੁਸੀਂ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ਜਾਂ ਸਾਦੇ `httpx` ਲੂਪ ਤੇ ਬਣਾਇਆ — ਅਜਿਹਾ ਨਹੀਂ ਕਰਦਾ। ClawMetry ਦਾ ਜ਼ੀਰੋ-ਕਨਫਿਗ ਇੰਟਰਸੈਪਟਰ ਫਿਰ ਵੀ `httpx`/`requests` ਨੂੰ ਮੰਕੀ-ਪੈਚ ਕਰਕੇ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ (ਲਾਗਤ, ਟੋਕਨ, ਲੇਟੈਂਸੀ, ਗਲਤੀਆਂ) ਕੈਪਚਰ ਕਰਦਾ ਹੈ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ਜਾਂ `CLAWMETRY_SOURCE=support-agent` ਐਨਵ ਵੇਰੀਏਬਲ) ਹਰ ਕਾਲ ਨੂੰ ਇੱਕ **ਨਾਮਿਤ ਸੋਰਸ** ਨਾਲ ਟੈਗ ਕਰਦਾ ਹੈ, ਇਸਲਈ ਤੁਹਾਡਾ ਹਰ ਉਤਪਾਦ ਡੈਸ਼ਬੋਰਡ ਦੇ Overview ਤੇ **🔌 Out-loop sources** ਕਾਰਡ ਵਿੱਚ ਆਪਣੀ ਪਹਿਲੀ-ਦਰਜੇ, ਲਾਗਤ-ਅਟਰੀਬਿਊਟਯੋਗ ਲਾਈਨ ਵਜੋਂ ਦਿਖਾਈ ਦਿੰਦਾ ਹੈ — ਪ੍ਰਤੀ ਏਜੰਟ ਕਾਲਾਂ, ਪ੍ਰੋਵਾਈਡਰ, ਲੇਟੈਂਸੀ, ਗਲਤੀ ਦਰ। ਕੋਈ ਸੋਰਸ ਸੈੱਟ ਨਹੀਂ? ਕਾਲਾਂ ਫਿਰ ਵੀ ਟਰੈਕ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ; ਕਾਰਡ ਬੱਸ ਲੁਕਿਆ ਰਹਿੰਦਾ ਹੈ।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ਇਹ ਉਹੀ ਡੇਟਾ ਲੇਅਰ ਹੈ ਜਿਸਨੂੰ ਰਨਟਾਈਮ ਅਡੈਪਟਰ ਫੀਡ ਕਰਦੇ ਹਨ (DuckDB ਤੋਂ ਕਲਾਉਡ ਸਨੈਪਸ਼ੌਟ), ਇਸਲਈ ਆਉਟ-ਲੂਪ ਸੋਰਸ ਕਲਾਉਡ ਡੈਸ਼ਬੋਰਡ ਨਾਲ ਉਸੇ ਤਰ੍ਹਾਂ ਸਿੰਕ ਹੁੰਦੇ ਹਨ ਜਿਵੇਂ ਬਾਕੀ ਸਭ, E2E-ਏਨਕ੍ਰਿਪਟਡ।

## OpenTelemetry — ਵੈਂਡਰ-ਨਿਰਪੱਖ, ਆਪਣੇ ਟ੍ਰੇਸ ਕਿਤੇ ਵੀ ਭੇਜੋ

ClawMetry **GenAI ਸੈਮਾਂਟਿਕ ਕਨਵੈਨਸ਼ਨਾਂ** ਵਰਤਦੇ ਹੋਏ ਦੋਵੇਂ ਦਿਸ਼ਾਵਾਂ ਵਿੱਚ OpenTelemetry ਬੋਲਦਾ ਹੈ, ਇਸਲਈ ਤੁਹਾਡੇ ਏਜੰਟ ਟ੍ਰੇਸ ਕਦੇ ਵੀ ਕਿਸੇ ਇੱਕ ਟੂਲ ਵਿੱਚ ਬੰਦ ਨਹੀਂ ਹੁੰਦੇ।

ਹਰ ਸੈਸ਼ਨ — LLM ਕਾਲਾਂ, ਟੂਲ, ਸਬ-ਏਜੰਟ, ਟੋਕਨ, ਲਾਗਤ — ਨੂੰ OTLP/HTTP GenAI ਸਪੈਨ ਵਜੋਂ ਕਿਸੇ ਵੀ ਕੁਲੈਕਟਰ (Datadog, Grafana, Honeycomb, ਜਾਂ ਤੁਹਾਡਾ ਆਪਣਾ OTel Collector) ਤੇ **ਐਕਸਪੋਰਟ** ਕਰੋ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ਔਥ ਹੈਡਰ ਅਤੇ ਪੋਲ ਇੰਟਰਵਲ ਵਿਕਲਪਿਕ ਐਨਵ ਵੇਰੀਏਬਲ ਹਨ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ਇਨਜੈਸਟ** — ਬਿਲਟ-ਇਨ OTLP ਰਿਸੀਵਰ `/v1/traces` ਅਤੇ `/v1/metrics` ਤੇ ਕਿਸੇ ਵੀ ਚੀਜ਼ ਤੋਂ ਟ੍ਰੇਸ ਅਤੇ ਮੈਟ੍ਰਿਕ ਸਵੀਕਾਰ ਕਰਦਾ ਹੈ (`pip install clawmetry[otel]` ਪ੍ਰੋਟੋਬਫ ਇਨਜੈਸਟ ਲਈ)।

ਤੁਹਾਨੂੰ ਜ਼ੀਰੋ-ਕਨਫਿਗ, ਲੋਕਲ-ਫਸਟ ClawMetry ਡੈਸ਼ਬੋਰਡ **ਅਤੇ** ਜੋ ਵੀ ਬੈਕਐਂਡ ਤੁਹਾਡੀ ਟੀਮ ਪਹਿਲਾਂ ਤੋਂ ਚਲਾਉਂਦੀ ਹੈ ਉਸ ਵਿੱਚ ਤੁਹਾਡਾ ਡੇਟਾ ਮਿਲਦਾ ਹੈ — ਕੋਈ ਲਾਕ-ਇਨ ਨਹੀਂ, ਕੋਈ ਦੂਸਰਾ ਏਜੰਟ ਇੰਸਟਾਲ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ।

## ਕੌਂਫਿਗਰੇਸ਼ਨ

ਜ਼ਿਆਦਾਤਰ ਲੋਕਾਂ ਨੂੰ ਕੋਈ ਕੌਂਫਿਗਰੇਸ਼ਨ ਦੀ ਲੋੜ ਨਹੀਂ। ClawMetry ਤੁਹਾਡਾ ਵਰਕਸਪੇਸ, ਲੌਗ, ਸੈਸ਼ਨ ਅਤੇ cron ਆਪਣੇ ਆਪ ਖੋਜਦਾ ਹੈ।

ਜੇ ਤੁਹਾਨੂੰ ਕਸਟਮਾਈਜ਼ ਕਰਨ ਦੀ ਲੋੜ ਹੈ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ਸਾਰੇ ਵਿਕਲਪ: `clawmetry --help`

## ਸਮਰਥਿਤ ਚੈਨਲ

ClawMetry ਤੁਹਾਡੇ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਰ OpenClaw ਚੈਨਲ ਲਈ ਲਾਈਵ ਗਤੀਵਿਧੀ ਦਿਖਾਉਂਦਾ ਹੈ। ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਜੋ ਅਸਲ ਵਿੱਚ ਤੁਹਾਡੇ `openclaw.json` ਵਿੱਚ ਸੈਟਅਪ ਹਨ Flow ਡਾਇਗ੍ਰਾਮ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ — ਕੌਂਫਿਗਰ ਨਾ ਕੀਤੇ ਆਪਣੇ ਆਪ ਲੁਕਾ ਦਿੱਤੇ ਜਾਂਦੇ ਹਨ।

ਲਾਈਵ ਚੈਟ ਬਬਲ ਵਿਊ ਨਾਲ ਆਉਣ-ਜਾਣ ਵਾਲੇ ਸੁਨੇਹਿਆਂ ਦੀ ਗਿਣਤੀ ਦੇਖਣ ਲਈ Flow ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੈਨਲ ਨੋਡ ਤੇ ਕਲਿੱਕ ਕਰੋ।

| ਚੈਨਲ | ਸਥਿਤੀ | ਲਾਈਵ ਪੌਪਅਪ | ਨੋਟ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ਪੂਰਾ | ✅ | ਸੁਨੇਹੇ, ਅੰਕੜੇ, 10s ਰਿਫਰੈਸ਼ |
| 💬 **iMessage** | ✅ ਪੂਰਾ | ✅ | `~/Library/Messages/chat.db` ਸਿੱਧਾ ਪੜ੍ਹਦਾ ਹੈ |
| 💚 **WhatsApp** | ✅ ਪੂਰਾ | ✅ | WhatsApp Web ਰਾਹੀਂ (Baileys) |
| 🔵 **Signal** | ✅ ਪੂਰਾ | ✅ | signal-cli ਰਾਹੀਂ |
| 🟣 **Discord** | ✅ ਪੂਰਾ | ✅ | Guild ਅਤੇ ਚੈਨਲ ਖੋਜ |
| 🟪 **Slack** | ✅ ਪੂਰਾ | ✅ | Workspace ਅਤੇ ਚੈਨਲ ਖੋਜ |
| 🌐 **Webchat** | ✅ ਪੂਰਾ | ✅ | ਬਿਲਟ-ਇਨ ਵੈੱਬ UI ਸੈਸ਼ਨ |
| 📡 **IRC** | ✅ ਪੂਰਾ | ✅ | ਟਰਮੀਨਲ-ਸਟਾਈਲ ਬਬਲ UI |
| 🍏 **BlueBubbles** | ✅ ਪੂਰਾ | ✅ | BlueBubbles REST API ਰਾਹੀਂ iMessage |
| 🔵 **Google Chat** | ✅ ਪੂਰਾ | ✅ | Chat API ਵੈਬਹੁੱਕ ਰਾਹੀਂ |
| 🟣 **MS Teams** | ✅ ਪੂਰਾ | ✅ | Teams ਬੋਟ ਪਲੱਗਇਨ ਰਾਹੀਂ |
| 🔷 **Mattermost** | ✅ ਪੂਰਾ | ✅ | ਸਵੈ-ਹੋਸਟ ਕੀਤੀ ਟੀਮ ਚੈਟ |
| 🟩 **Matrix** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦ੍ਰੀਕ੍ਰਿਤ, E2EE ਸਮਰਥਨ |
| 🟢 **LINE** | ✅ ਪੂਰਾ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦ੍ਰੀਕ੍ਰਿਤ NIP-04 DMs |
| 🟣 **Twitch** | ✅ ਪੂਰਾ | ✅ | IRC ਕਨੈਕਸ਼ਨ ਰਾਹੀਂ ਚੈਟ |
| 🔷 **Feishu/Lark** | ✅ ਪੂਰਾ | ✅ | WebSocket ਇਵੈਂਟ ਸਬਸਕ੍ਰਿਪਸ਼ਨ |
| 🔵 **Zalo** | ✅ ਪੂਰਾ | ✅ | Zalo Bot API |

> **ਆਟੋ-ਖੋਜ:** ClawMetry ਤੁਹਾਡਾ `~/.openclaw/openclaw.json` ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਦਿਖਾਉਂਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਅਸਲ ਵਿੱਚ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਨ। ਕੋਈ ਹੱਥੀਂ ਸੈਟਅਪ ਦੀ ਲੋੜ ਨਹੀਂ।

## Docker ਡਿਪਲੌਇਮੈਂਟ

ਕੀ ਤੁਸੀਂ ClawMetry ਨੂੰ ਕੰਟੇਨਰ ਵਿੱਚ ਚਲਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ? ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ! 🐳

**Docker ਨਾਲ ਤੁਰੰਤ ਸ਼ੁਰੂਆਤ:**

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

**Docker Compose ਉਦਾਹਰਨ:**

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

> **ਨੋਟ:** Docker ਵਿੱਚ ਚਲਾਉਂਦੇ ਵੇਲੇ, ਆਪਣੇ ਏਜੰਟ ਦੇ ਡੇਟਾ ਅਤੇ ਲੌਗ ਡਾਇਰੈਕਟਰੀਆਂ (ਜਿਵੇਂ `~/.openclaw`, `~/.claude`, `~/.codex`) ਮਾਊਂਟ ਕਰੋ ਤਾਂ ਜੋ ClawMetry ਤੁਹਾਡਾ ਸੈਟਅਪ ਆਪਣੇ ਆਪ ਖੋਜ ਸਕੇ।

## ਲੋੜਾਂ

- Python 3.8+
- Flask (pip ਰਾਹੀਂ ਆਪਣੇ ਆਪ ਇੰਸਟਾਲ ਹੁੰਦਾ ਹੈ)
- ਉਸੇ ਮਸ਼ੀਨ ਤੇ ਇੱਕ AI ਏਜੰਟ ਰਨਟਾਈਮ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, ਜਾਂ PicoClaw (ਜਾਂ Docker ਲਈ ਮਾਊਂਟ ਕੀਤੀਆਂ ਵੌਲਿਊਮਾਂ)
- Linux ਜਾਂ macOS

## NemoClaw / OpenShell ਸਮਰਥਨ

ClawMetry ਆਪਣੇ ਆਪ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ਖੋਜਦਾ ਹੈ — NVIDIA ਦਾ ਐਂਟਰਪ੍ਰਾਈਜ਼ ਸੁਰੱਖਿਆ ਰੈਪਰ ਜੋ OpenClaw ਲਈ ਏਜੰਟ ਸੈਂਡਬਾਕਸਡ OpenShell ਕੰਟੇਨਰਾਂ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ।

ਜ਼ਿਆਦਾਤਰ ਮਾਮਲਿਆਂ ਵਿੱਚ ਕੋਈ ਵਾਧੂ ਕੌਂਫਿਗਰੇਸ਼ਨ ਦੀ ਲੋੜ ਨਹੀਂ। ਸਿੰਕ ਡੀਮਨ ਆਪਣੇ ਆਪ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਖੋਜਦਾ ਹੈ ਭਾਵੇਂ ਉਹ ਹੋਸਟ ਤੇ `~/.openclaw/` ਵਿੱਚ ਹੋਣ ਜਾਂ OpenShell ਕੰਟੇਨਰ ਵਿੱਚ।

### ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry NemoClaw ਨੂੰ ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ ਖੋਜਦਾ ਹੈ:

1. **ਬਾਇਨਰੀ ਖੋਜ** — `nemoclaw` CLI ਦੀ ਜਾਂਚ ਕਰਦਾ ਹੈ ਅਤੇ ਸੈਂਡਬਾਕਸ ਜਾਣਕਾਰੀ ਪ੍ਰਾਪਤ ਕਰਨ ਲਈ `nemoclaw status` ਚਲਾਉਂਦਾ ਹੈ
2. **ਕੰਟੇਨਰ ਖੋਜ** — ਚੱਲ ਰਹੇ Docker ਕੰਟੇਨਰਾਂ ਵਿੱਚ `openshell`, `nemoclaw`, ਜਾਂ `ghcr.io/nvidia/` ਚਿੱਤਰਾਂ ਲਈ ਸਕੈਨ ਕਰਦਾ ਹੈ, ਫਿਰ ਵੌਲਿਊਮ ਮਾਊਂਟਾਂ ਜਾਂ `docker cp` ਰਾਹੀਂ ਸੈਸ਼ਨ ਪੜ੍ਹਦਾ ਹੈ

NemoClaw ਕੰਟੇਨਰਾਂ ਤੋਂ ਸਿੰਕ ਕੀਤੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਕਲਾਉਡ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ `runtime=nemoclaw` ਅਤੇ `container_id` ਮੈਟਾਡੇਟਾ ਨਾਲ ਟੈਗ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ, ਤਾਂ ਜੋ ਤੁਸੀਂ ਉਹਨਾਂ ਨੂੰ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਮਿਆਰੀ OpenClaw ਸੈਸ਼ਨਾਂ ਤੋਂ ਵੱਖ ਕਰ ਸਕੋ।

### ਸਿਫਾਰਸ਼ੀ ਸੈਟਅਪ: ਹੋਸਟ ਤੇ ਸਿੰਕ ਡੀਮਨ

ਸਭ ਤੋਂ ਵਧੀਆ ਤਜ਼ਰਬੇ ਲਈ, ClawMetry ਦਾ ਸਿੰਕ ਡੀਮਨ **ਹੋਸਟ ਮਸ਼ੀਨ** ਤੇ ਚਲਾਓ (ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਨਹੀਂ)। ਇਹ NemoClaw ਨੈੱਟਵਰਕ ਨੀਤੀ ਪਾਬੰਦੀਆਂ ਤੋਂ ਬਚਦਾ ਹੈ।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ਸਿੰਕ ਡੀਮਨ ਆਪਣੇ ਆਪ ਕਿਸੇ ਵੀ ਚੱਲ ਰਹੇ OpenShell ਕੰਟੇਨਰਾਂ ਦੇ ਅੰਦਰ ਸੈਸ਼ਨ ਲੱਭੇਗਾ।

### ਵਿਕਲਪਿਕ: ਸਪੱਸ਼ਟ ਸੈਂਡਬਾਕਸ ਨਾਮ

ਜੇ ਆਟੋ-ਖੋਜ ਕੰਮ ਨਹੀਂ ਕਰਦੀ, ClawMetry ਨੂੰ ਸਹੀ ਸੈਂਡਬਾਕਸ ਵੱਲ ਇਸ਼ਾਰਾ ਕਰੋ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਚਲਾਉਣਾ (ਉੱਨਤ)

ਜੇ ਤੁਹਾਨੂੰ ਸਿੰਕ ਡੀਮਨ **OpenShell ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ** ਚਲਾਉਣਾ ਜ਼ਰੂਰੀ ਹੈ, ਆਪਣੀ NemoClaw ਨੈੱਟਵਰਕ ਨੀਤੀ ਵਿੱਚ ਇਹ ਐਗਰੈੱਸ ਨਿਯਮ ਜੋੜੋ ਤਾਂ ਜੋ ਇਹ ClawMetry ਇਨਜੈਸਟ API ਤੱਕ ਪਹੁੰਚ ਸਕੇ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ਇਸ ਨਾਲ ਲਾਗੂ ਕਰੋ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ਪੋਰਟ ਅਤੇ ਐਂਡਪੌਇੰਟ

| ਐਂਡਪੌਇੰਟ | ਪੋਰਟ | ਪ੍ਰੋਟੋਕੋਲ | ਲੋੜੀਂਦਾ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ਹਾਂ (ਸਿੰਕ ਡੀਮਨ ਤੋਂ ਕਲਾਉਡ) |
| `localhost:8900` | 8900 | HTTP | ਹਾਂ (ਲੋਕਲ ਡੈਸ਼ਬੋਰਡ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | ਕੰਟੇਨਰ ਸੈਸ਼ਨ ਖੋਜ ਲਈ |

ਸਿੰਕ ਡੀਮਨ ਸਿਰਫ਼ `ingest.clawmetry.com` ਤੇ ਆਊਟਬਾਊਂਡ HTTPS ਕਾਲਾਂ ਕਰਦਾ ਹੈ। ਕੋਈ ਇਨਬਾਊਂਡ ਪੋਰਟਾਂ ਦੀ ਲੋੜ ਨਹੀਂ।

---

## ਕਲਾਉਡ ਡਿਪਲੌਇਮੈਂਟ

SSH ਟਨਲ, ਰਿਵਰਸ ਪ੍ਰੌਕਸੀ ਅਤੇ Docker ਲਈ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ਵੇਖੋ।

## ਟੈਸਟਿੰਗ

ਇਸ ਪ੍ਰੋਜੈਕਟ ਨੂੰ BrowserStack ਨਾਲ ਟੈਸਟ ਕੀਤਾ ਗਿਆ ਹੈ।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ਟੈਲੀਮੈਟ੍ਰੀ

ClawMetry ਕਿਸੇ ਨਵੀਂ ਮਸ਼ੀਨ ਤੇ ਪਹਿਲੀ ਵਾਰ `clawmetry` CLI ਚਲਾਉਣ ਤੇ `https://app.clawmetry.com/api/install` ਤੇ ਇੱਕ ਅਗਿਆਤ "ਪਹਿਲੀ ਰਨ" ਪਿੰਗ ਭੇਜਦਾ ਹੈ। ਅਸੀਂ ਇਸਦੀ ਵਰਤੋਂ ਇੰਸਟਾਲ ਗਿਣਨ (OSS ਪ੍ਰੋਜੈਕਟ ਲਈ ਸਾਡਾ ਇੱਕੋ ਮਾਰਕੀਟਿੰਗ ਮੈਟ੍ਰਿਕ) ਅਤੇ ਇਹ ਜਾਣਨ ਲਈ ਕਰਦੇ ਹਾਂ ਕਿ ਸਾਡੇ ਯੂਜ਼ਰਾਂ ਕੋਲ ਕਿਹੜੇ ਏਜੰਟ ਫਰੇਮਵਰਕ ਇੰਸਟਾਲ ਹਨ।

**ਪ੍ਰਤੀ ਇੰਸਟਾਲ ਬਿਲਕੁਲ ਇੱਕ POST**, ਜਿਸ ਵਿੱਚ ਸ਼ਾਮਲ ਹੈ:

| ਫੀਲਡ | ਉਦਾਹਰਨ | ਕਿਉਂ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ਤੇ ਸਟੋਰ ਕੀਤਾ ਰੈਂਡਮ UUID | ਡੁਪਲੀਕੇਟ ਹਟਾਉਣਾ; ਤੁਹਾਡੀ ਈਮੇਲ ਜਾਂ api_key ਨਾਲ ਜੋੜਿਆ ਨਹੀਂ |
| `version` | `0.12.167` | ਕਿਹੜੇ ਵਰਜਨ ਚੱਲ ਰਹੇ ਹਨ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ਪਲੇਟਫਾਰਮ ਸਮਰਥਨ ਤਰਜੀਹਾਂ |
| `python` | `3.11.15` | Python ਵਰਜਨ ਸਮਰਥਨ ਮੈਟ੍ਰਿਕਸ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ਕਿਹੜੇ ਏਜੰਟਾਂ ਨਾਲ ਅਸੀਂ ਅਗਲਾ ਏਕੀਕਰਨ ਕਰੀਏ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ਮਨੁੱਖੀ ਇੰਸਟਾਲਾਂ ਨੂੰ CI ਸ਼ੋਰ ਤੋਂ ਵੱਖ ਕਰੋ |

**ਅਸੀਂ ਕੀ ਨਹੀਂ ਭੇਜਦੇ**: IP (ਕਲਾਉਡ ਬੇਨਤੀ ਤੋਂ ਦੇਸ਼ ਕੋਡ ਸਰਵਰ-ਸਾਈਡ ਕੱਢਦਾ ਹੈ, ਫਿਰ IP ਮਿਟਾਉਂਦਾ ਹੈ), ਹੋਸਟਨੇਮ, ਯੂਜ਼ਰਨੇਮ, ਵਰਕਸਪੇਸ ਪਾਥ, ਫਾਈਲ ਸਮੱਗਰੀ, ਤੁਹਾਡੀ api_key, ਤੁਹਾਡੀ ਈਮੇਲ, ਕੋਈ PII ਜਾਂ ਵਰਕਸਪੇਸ-ਵਿਸ਼ੇਸ਼ ਜਾਣਕਾਰੀ। ਵਾਇਰ ਪੇਲੋਡ [`clawmetry/telemetry.py`](clawmetry/telemetry.py) ਵਿੱਚ ਆਡਿਟਯੋਗ ਹੈ।

**ਆਪਟ ਆਊਟ** (ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਵੀ ਇੱਕ ਇਸਨੂੰ ਸਥਾਈ ਤੌਰ ਤੇ ਅਯੋਗ ਕਰਦਾ ਹੈ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ਇੱਥੇ ਨੈੱਟਵਰਕ ਫੇਲੀਅਰ ਕਦੇ `clawmetry` ਨੂੰ ਚੱਲਣ ਤੋਂ ਨਹੀਂ ਰੋਕਦੀ — ਪਿੰਗ 3 ਸੈਕਿੰਡ ਟਾਈਮਆਊਟ ਵਾਲੇ ਡੀਮਨ ਥ੍ਰੈੱਡ ਤੇ ਫਾਇਰ-ਐਂਡ-ਫੋਰਗੈੱਟ ਹੈ।

## ਸਟਾਰ ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੈਂਸ

MIT

---

<p align="center">
  <strong>🦞 ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਵੇਖੋ</strong><br>
  <sub>ਬਣਾਇਆ <a href="https://github.com/vivekchand">@vivekchand</a> ਦੁਆਰਾ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ਈਕੋਸਿਸਟਮ ਦਾ ਹਿੱਸਾ</sub>
</p>
