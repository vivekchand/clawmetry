<!-- i18n-src:191e9094d7fa -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਹੋਏ ਦੇਖੋ।** **14 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 10 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਨਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ-ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ ਅਤੇ ਬੱਸ, ਕੰਮ ਹੋ ਗਿਆ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਦੀ ਸ਼ੁਰੂਆਤ OpenClaw ਲਈ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ ਵਜੋਂ ਹੋਈ ਸੀ, ਅਤੇ ਹੁਣ ਇਹ ਤੁਹਾਡੇ **ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ** ਨੂੰ ਇੱਕੋ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਮੀਟਰ ਕਰਦਾ ਹੈ, ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹਰੇਕ ਰਨਟਾਈਮ ਨੂੰ ਆਪਣੇ-ਆਪ ਪਛਾਣਦਾ ਹੋਇਆ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ਅਤੇ NemoClaw ਓਪਨ-ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ ਹਨ; ਬਾਕੀ ਰਨਟਾਈਮਾਂ ClawMetry Cloud ਜਾਂ ਸੈਲਫ-ਹੋਸਟਡ Pro ਲਾਇਸੈਂਸ ਨਾਲ ਸਰਗਰਮ ਹੁੰਦੀਆਂ ਹਨ। ਹੈੱਡਰ ਤੋਂ ਰਨਟਾਈਮ ਬਦਲੋ ਅਤੇ ਹਰ ਟੈਬ — ਲਾਗਤ, ਟੋਕਨ, ਟੂਲ, ਟਰੇਸ — ਉਸ ਰਨਟਾਈਮ ਲਈ ਦੁਬਾਰਾ-ਸਕੋਪ ਹੋ ਜਾਂਦੀ ਹੈ। ਸਹੀ ਮੁਫ਼ਤ/ਪੇਡ ਵੰਡ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, `/api/entitlement` ਸ਼ੇਪ, ਅਤੇ `clawmetry license` CLI ਲਈ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ਦੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **Flow** — ਲਾਈਵ ਐਨੀਮੇਟਿਡ ਡਾਇਗ੍ਰਾਮ ਜੋ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਮੈਸੇਜ ਚੈਨਲਾਂ, ਬ੍ਰੇਨ, ਟੂਲਸ ਰਾਹੀਂ ਅਤੇ ਵਾਪਸ ਕਿਵੇਂ ਵਹਿ ਰਹੇ ਹਨ
- **Overview** — ਹੈਲਥ ਚੈੱਕ, ਐਕਟੀਵਿਟੀ ਹੀਟਮੈਪ, ਸੈਸ਼ਨ ਗਿਣਤੀ, ਮਾਡਲ ਜਾਣਕਾਰੀ
- **Usage** — ਰੋਜ਼ਾਨਾ/ਹਫ਼ਤਾਵਾਰ/ਮਹੀਨਾਵਾਰ ਬ੍ਰੇਕਡਾਊਨ ਨਾਲ ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਟਰੈਕਿੰਗ
- **Sessions** — ਮਾਡਲ, ਟੋਕਨ, ਆਖ਼ਰੀ ਗਤੀਵਿਧੀ ਸਮੇਤ ਸਰਗਰਮ ਏਜੰਟ ਸੈਸ਼ਨ
- **Crons** — ਸਥਿਤੀ, ਅਗਲੀ ਰਨ, ਮਿਆਦ ਸਮੇਤ ਨਿਯਤ ਕੀਤੀਆਂ ਜੌਬਾਂ
- **Logs** — ਰੰਗ-ਕੋਡਿਡ ਰੀਅਲ-ਟਾਈਮ ਲੌਗ ਸਟ੍ਰੀਮਿੰਗ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ਰੋਜ਼ਾਨਾ ਨੋਟਸ ਬ੍ਰਾਊਜ਼ ਕਰੋ
- **Transcripts** — ਸੈਸ਼ਨ ਇਤਿਹਾਸ ਪੜ੍ਹਨ ਲਈ ਚੈਟ-ਬੱਬਲ UI
- **Alerts** — ਬਜਟ ਕੈਪ, ਗ਼ਲਤੀ-ਦਰ ਟ੍ਰਿਗਰ, ਏਜੰਟ-ਔਫਲਾਈਨ ਪਛਾਣ; Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਹੁੰਦੇ ਹਨ
- **Approvals** — ਵਿਨਾਸ਼ਕਾਰੀ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, DB ਮਿਊਟੇਸ਼ਨ, sudo, ਪੈਕੇਜ ਇੰਸਟਾਲ, ਨੈੱਟਵਰਕ ਕਾਲਾਂ ਨੂੰ ਇੱਕ-ਕਲਿੱਕ ਸਾਈਨ-ਔਫ ਪਿੱਛੇ ਰੋਕੋ

## ਸਕਰੀਨਸ਼ਾਟ

### 🧠 Brain — ਲਾਈਵ ਏਜੰਟ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ਟੋਕਨ ਵਰਤੋਂ ਅਤੇ ਸੈਸ਼ਨ ਸੰਖੇਪ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ਰੀਅਲ-ਟਾਈਮ ਟੂਲ ਕਾਲ ਫੀਡ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਵਾਰ ਲਾਗਤ ਬ੍ਰੇਕਡਾਊਨ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ਵਰਕਸਪੇਸ ਫਾਈਲ ਬ੍ਰਾਊਜ਼ਰ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ਪੋਸਚਰ ਅਤੇ ਆਡਿਟ ਲੌਗ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ਬਜਟ ਕੈਪ, ਗ਼ਲਤੀ-ਦਰ ਟ੍ਰਿਗਰ, Slack / Discord / PagerDuty / Email ਲਈ ਵੈੱਬਹੁੱਕ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਮੈਨੁਅਲ ਸਾਈਨ-ਔਫ ਪਿੱਛੇ ਰੋਕੋ; ਪਾਲਿਸੀ-ਬੈਕਡ ਸੁਰੱਖਿਆ ਨਿਯਮ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ਲਈ ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਬਲਾਕਿੰਗ** — ਇੱਕ ਕਮਾਂਡ ਇੱਕ
PreToolUse ਹੁੱਕ ਇੰਸਟਾਲ ਕਰਦੀ ਹੈ ਜੋ ਮੇਲ ਖਾਂਦੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕ ਦਿੰਦੀ ਹੈ ਅਤੇ ਤੁਹਾਡੇ ਫ਼ੈਸਲੇ ਦੀ
ਉਡੀਕ ਕਰਦੀ ਹੈ (ਤੁਹਾਡੇ ਫ਼ੋਨ ਤੋਂ ਇੱਕ ਟੈਪ ਨਾਲ, ਜੇ
[ਕਲਾਊਡ ਪੁਸ਼ ਨੋਟੀਫਿਕੇਸ਼ਨ](https://app.clawmetry.com/push) ਸਮਰੱਥ ਹੋਵੇ):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ਇੱਕ ਡਿਨਾਈ ਸਿਰਫ਼ ਉਸ ਇੱਕ ਟੂਲ ਕਾਲ ਨੂੰ ਬਲਾਕ ਕਰਦੀ ਹੈ — ਏਜੰਟ ਆਪਣਾ ਸੈਸ਼ਨ ਬਰਕਰਾਰ ਰੱਖਦਾ ਹੈ ਅਤੇ ਕੋਈ ਹੋਰ ਤਰੀਕਾ
ਅਜ਼ਮਾ ਸਕਦਾ ਹੈ। ਤੁਹਾਡੇ ਫ਼ੋਨ 'ਤੇ ਮਨਜ਼ੂਰੀ ਦੇਣ ਨਾਲ Claude Code ਦਾ ਆਪਣਾ
ਪਰਮਿਸ਼ਨ ਪ੍ਰੌਂਪਟ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ (ਤੁਸੀਂ ਪਹਿਲਾਂ ਹੀ ਜਵਾਬ ਦੇ ਚੁੱਕੇ ਹੋ)। ਬਿਨਾਂ ਮੇਲ ਵਾਲੇ ਟੂਲਾਂ ਦੀ ਲਾਗਤ ~40ms ਹੁੰਦੀ ਹੈ ਅਤੇ
ਉਹ Claude Code ਦੇ ਆਮ ਪਰਮਿਸ਼ਨ ਫਲੋ ਵਿੱਚ ਚਲੇ ਜਾਂਦੇ ਹਨ। ਜਦੋਂ Claude Code ਖ਼ੁਦ ਤੁਹਾਡੀ
ਉਡੀਕ ਕਰ ਰਿਹਾ ਹੋਵੇ (`permission_prompt` / `idle_prompt` ਨੋਟੀਫਿਕੇਸ਼ਨ) ਤਾਂ ਵੀ ਤੁਹਾਨੂੰ ਫ਼ੋਨ ਪੁਸ਼ ਮਿਲਦੀ ਹੈ।

## ਇੰਸਟਾਲ

**ਵੰਨ-ਲਾਈਨਰ (ਸਿਫ਼ਾਰਸ਼ੀ):**
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

## v2 ਫ਼ਰੰਟਐਂਡ ਡਿਵੈਲਪਮੈਂਟ

v2 React ਐਪ `frontend/` ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ ਅਤੇ `/v2` 'ਤੇ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ ਜਦੋਂ Flask
ਸਰਵਰ v2 ਸਮਰੱਥ ਕਰਕੇ ਸ਼ੁਰੂ ਕੀਤਾ ਜਾਂਦਾ ਹੈ।

ਵਿਕਾਸ ਦੌਰਾਨ ਦੋ ਟਰਮੀਨਲ ਵਰਤੋ:

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

`http://localhost:5173/v2/` ਖੋਲ੍ਹੋ। Vite `/api` ਬੇਨਤੀਆਂ ਨੂੰ
`http://localhost:8900` ਵੱਲ ਪ੍ਰੌਕਸੀ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ React ਐਪ ਵਾਧੂ CORS ਸੈੱਟਅੱਪ ਬਿਨਾਂ
ਲੋਕਲ Flask ਸਰਵਰ ਨਾਲ ਗੱਲ ਕਰ ਸਕਦੀ ਹੈ।

Python ਪੈਕੇਜ ਨਾਲ ਸ਼ਿੱਪ ਹੋਣ ਵਾਲਾ ਬੰਡਲ ਬਣਾਉਣ ਲਈ:

```bash
cd frontend
npm run build
```

ਪ੍ਰੋਡਕਸ਼ਨ ਬੰਡਲ `clawmetry/static/v2/dist/` ਵਿੱਚ ਲਿਖਿਆ ਜਾਂਦਾ ਹੈ।

## ਰਨਟਾਈਮ / ਏਜੰਟ ਅਨੁਕੂਲਤਾ

ClawMetry ਸਿਰਫ਼ OpenClaw ਹੀ ਨਹੀਂ, ਸਗੋਂ ਕਈ AI-ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਆਬਜ਼ਰਵ ਕਰਦਾ ਹੈ। ਹਰ ਗੈਰ-OpenClaw ਰਨਟਾਈਮ ਇੱਕ ਸਮਰਪਿਤ ਰੀਡਰ ਅਡੈਪਟਰ ਨਾਲ ਆਉਂਦਾ ਹੈ ਜੋ ਉਸ ਰਨਟਾਈਮ ਦੇ ਨੇਟਿਵ ਸੈਸ਼ਨ ਫਾਰਮੈਟ ਨੂੰ ClawMetry ਦੀਆਂ ਯੂਨੀਫਾਈਡ ਸ਼ੇਪਾਂ ਵਿੱਚ ਬਦਲਦਾ ਹੈ; ਡੀਮਨ ਇਹਨਾਂ ਨੂੰ ਉਸੇ DuckDB ਸਟੋਰ + ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ ਵਿੱਚ ਲੈ ਜਾਂਦਾ ਹੈ, ਰਨਟਾਈਮ ਨਾਲ ਟੈਗ ਕੀਤਾ ਹੋਇਆ, ਅਤੇ ਜਦੋਂ ਇੱਕ ਤੋਂ ਵੱਧ ਰਨਟਾਈਮ ਮੌਜੂਦ ਹੋਣ ਤਾਂ Session replay ਟੈਬ ਇੱਕ **ਰਨਟਾਈਮ ਸਵਿੱਚਰ** ਦਿਖਾਉਂਦੀ ਹੈ। ਪੂਰੇ ਮੈਟ੍ਰਿਕਸ + ਰਨਟਾਈਮ ਜੋੜਨ ਦੀ ਗਾਈਡ ਲਈ [`docs/compatibility.md`](docs/compatibility.md) ਅਤੇ OpenClaw-ਫੈਮਿਲੀ ਪ੍ਰਾਈਮਰ ਲਈ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ਦੇਖੋ।

[Perplexity ਦਾ numbat](https://github.com/perplexityai/numbat) ਏਜੰਟ-ਸੁਰੱਖਿਆ ਟੂਲ ਚਲਾ ਰਹੇ ਹੋ? ClawMetry ਇਸ ਦੀਆਂ ਖੋਜਾਂ ਅਤੇ ਲਾਗੂਕਰਨ ਫ਼ੈਸਲਿਆਂ ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਵਾਧੂ ਸੈੱਟਅੱਪ ਦੇ ਲੈ ਲੈਂਦਾ ਹੈ — [`docs/NUMBAT.md`](docs/NUMBAT.md) ਦੇਖੋ।

| ਰਨਟਾਈਮ / ਏਜੰਟ | ਸਥਿਤੀ | ਨੋਟਸ |
|---|---|---|
| **OpenClaw** | ਨੇਟਿਵ | ਰੈਫਰੈਂਸ ਰਨਟਾਈਮ, ਆਪਣੇ-ਆਪ ਪਛਾਣਿਆ ਜਾਂਦਾ ਹੈ |
| **PicoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਫਲੈਟ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ। |
| **NanoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ-ਸੈਸ਼ਨ SQLite (`data/v2-sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ + ਮੈਸੇਜ ਗਿਣਤੀ। |
| **Hermes** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.hermes/state.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ/ਲਾਗਤ। |
| **Claude Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.claude/projects/.../<id>.jsonl`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ + ਥਿੰਕਿੰਗ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Codex** | ਬੀਟਾ ਅਡੈਪਟਰ | ਰੋਲਆਊਟ JSONL `~/.codex/sessions/...`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Cursor** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `state.vscdb`। ਚੈਟ/ਕੰਪੋਜ਼ਰ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ। |
| **Aider** | ਬੀਟਾ ਅਡੈਪਟਰ | ਹਰ ਪ੍ਰੋਜੈਕਟ ਲਈ `.aider.chat.history.md`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ ਗਿਣਤੀ। |
| **Goose** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/goose`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਟੋਟਲ। |
| **opencode** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/opencode`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Qwen Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.qwen/projects/.../chats`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Pi** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.pi/agent/sessions`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Deep Agents** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.deepagents/.state/sessions.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **n8n** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.n8n/database.sqlite`। ਵਰਕਫਲੋ ਐਗਜ਼ੀਕਿਊਸ਼ਨ, ਨੋਡ ਰਨ, AI Agent ਪ੍ਰੌਂਪਟ, ਜਿੱਥੇ n8n ਰਿਕਾਰਡ ਕਰਦਾ ਹੈ ਉੱਥੇ ਮਾਡਲ + ਟੋਕਨ। |
| **Antigravity** | ਬੀਟਾ ਅਡੈਪਟਰ | `~/.gemini/<flavor>/brain/` ਹੇਠ ਬ੍ਰੇਨ JSONL। ਗੱਲਬਾਤਾਂ, ਟੂਲ ਸਟੈਪ, ਥਿੰਕਿੰਗ, ਪ੍ਰਤੀ-ਜਨਰੇਸ਼ਨ Gemini ਟੋਕਨ ਵੰਡ + ਲਾਗਤ, ਬੈਕਗ੍ਰਾਊਂਡ-ਜਨਰੇਸ਼ਨ ਖ਼ਰਚ। |

"ਬੀਟਾ ਅਡੈਪਟਰ" ਦਾ ਮਤਲਬ ਹੈ ਕਿ ClawMetry ਉਸ ਰਨਟਾਈਮ ਦੇ ਅਸਲ ਔਨ-ਡਿਸਕ ਫਾਰਮੈਟ ਲਈ ਇੱਕ ਰੀਡਰ ਸ਼ਿਪ ਕਰਦਾ ਹੈ, ਹਰ ਇੱਕ ਨੂੰ ਅਸਲ ਮਸ਼ੀਨ 'ਤੇ ਅਸਲ ਇੰਸਟਾਲ ਦੇ ਖ਼ਿਲਾਫ਼ ਬਣਾਇਆ + ਤਸਦੀਕ ਕੀਤਾ ਗਿਆ ਹੈ (ਦੇਖੋ `tests/fixtures/runtimes/<rt>/`)। ਅਡੈਪਟਰ ਰੀਡ-ਓਨਲੀ ਹਨ; ਹਰ ਇੱਕ ਇਸ ਬਾਰੇ ਇਮਾਨਦਾਰ ਹੈ ਕਿ ਉਸ ਦਾ ਰਨਟਾਈਮ ਅਸਲ ਵਿੱਚ ਕੀ ਸਟੋਰ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ, PicoClaw/NanoClaw/Cursor ਟੋਕਨ ਲਾਗਤ ਡਿਸਕ 'ਤੇ ਨਹੀਂ ਲਿਖਦੇ)। ਜਦੋਂ ਇੱਕ ਨੋਡ 'ਤੇ ਕਈ ਰਨਟਾਈਮ ਚੱਲ ਰਹੇ ਹੋਣ, ਤਾਂ ਰਨਟਾਈਮ ਸਵਿੱਚਰ ਸੈਸ਼ਨ ਵਿਊ ਨੂੰ ਸਾਫ਼ ਡੂੰਘੀ-ਪੜਤਾਲ ਲਈ ਇੱਕ ਤੱਕ ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

## ਕਿਸੇ ਵੀ SDK ਏਜੰਟ ਨੂੰ ਟਰੈਕ ਕਰੋ — ਆਊਟ-ਲੂਪ ਲਾਗਤ ਐਟ੍ਰਿਬਿਊਸ਼ਨ

ਉੱਪਰ ਦੱਸੇ ਰਨਟਾਈਮ ਸਾਰੇ ਸੈਸ਼ਨ ਡਿਸਕ 'ਤੇ ਲਿਖਦੇ ਹਨ। ਤੁਹਾਡਾ ਆਪਣਾ **ਪ੍ਰੋਡਕਸ਼ਨ ਏਜੰਟ** — ਉਹ ਜੋ ਤੁਸੀਂ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ਜਾਂ ਸਾਦੇ `httpx` ਲੂਪ 'ਤੇ ਬਣਾਇਆ — ਅਜਿਹਾ ਨਹੀਂ ਕਰਦਾ। ClawMetry ਦਾ ਜ਼ੀਰੋ-ਕੌਨਫਿਗ ਇੰਟਰਸੈਪਟਰ ਫਿਰ ਵੀ `httpx`/`requests` ਨੂੰ ਮੰਕੀ-ਪੈਚ ਕਰਕੇ ਇਸ ਦੀਆਂ LLM ਕਾਲਾਂ (ਲਾਗਤ, ਟੋਕਨ, ਲੇਟੰਸੀ, ਗ਼ਲਤੀਆਂ) ਫੜ ਲੈਂਦਾ ਹੈ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ਜਾਂ `CLAWMETRY_SOURCE=support-agent` env var) ਹਰ ਕਾਲ ਨੂੰ ਇੱਕ **ਨਾਮਿਤ ਸੋਰਸ** ਨਾਲ ਟੈਗ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਤੁਸੀਂ ਜੋ ਵੀ ਪ੍ਰੋਡਕਟ ਚਲਾਉਂਦੇ ਹੋ ਉਹ ਡੈਸ਼ਬੋਰਡ ਦੇ **🔌 Out-loop sources** ਕਾਰਡ ਵਿੱਚ Overview 'ਤੇ ਆਪਣੀ ਹੀ ਪਹਿਲੀ-ਦਰਜੇ ਦੀ, ਲਾਗਤ-ਐਟ੍ਰਿਬਿਊਟੇਬਲ ਲਾਈਨ ਵਜੋਂ ਦਿਖਾਈ ਦਿੰਦਾ ਹੈ — ਹਰ ਏਜੰਟ ਦੀਆਂ ਕਾਲਾਂ, ਪ੍ਰੋਵਾਈਡਰ, ਲੇਟੰਸੀ, ਗ਼ਲਤੀ ਦਰ। ਸੋਰਸ ਸੈੱਟ ਨਹੀਂ ਕੀਤਾ? ਕਾਲਾਂ ਫਿਰ ਵੀ ਟਰੈਕ ਹੁੰਦੀਆਂ ਹਨ; ਕਾਰਡ ਬੱਸ ਲੁਕਿਆ ਰਹਿੰਦਾ ਹੈ।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ਇਹ ਉਹੀ ਡੇਟਾ ਲੇਅਰ ਹੈ ਜੋ ਰਨਟਾਈਮ ਅਡੈਪਟਰ ਫੀਡ ਕਰਦੇ ਹਨ (DuckDB → ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ), ਇਸ ਲਈ ਆਊਟ-ਲੂਪ ਸੋਰਸ ਬਾਕੀ ਸਭ ਕੁਝ ਵਾਂਗ ਹੀ, E2E-ਇਨਕ੍ਰਿਪਟਿਡ, ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਨਾਲ ਸਿੰਕ ਹੁੰਦੇ ਹਨ।

## OpenTelemetry — ਵੈਂਡਰ-ਨਿਊਟ੍ਰਲ, ਆਪਣੇ ਟਰੇਸ ਕਿਤੇ ਵੀ ਭੇਜੋ

ClawMetry ਦੋਵੇਂ ਦਿਸ਼ਾਵਾਂ ਵਿੱਚ **OpenTelemetry** ਬੋਲਦਾ ਹੈ, **GenAI ਸਿਮੈਂਟਿਕ ਕਨਵੈਨਸ਼ਨਾਂ** ਵਰਤ ਕੇ, ਤਾਂ ਜੋ ਤੁਹਾਡੇ ਏਜੰਟ ਟਰੇਸ ਕਦੇ ਵੀ ਇੱਕ ਟੂਲ ਵਿੱਚ ਲੌਕ ਨਾ ਹੋਣ।

**ਐਕਸਪੋਰਟ** ਕਰੋ ਹਰ ਸੈਸ਼ਨ — LLM ਕਾਲਾਂ, ਟੂਲ, ਸਬ-ਏਜੰਟ, ਟੋਕਨ, ਲਾਗਤ — OTLP/HTTP GenAI ਸਪੈਨਾਂ ਵਜੋਂ ਕਿਸੇ ਵੀ ਕਲੈਕਟਰ ਨੂੰ (Datadog, Grafana, Honeycomb, ਜਾਂ ਤੁਹਾਡੇ ਆਪਣੇ OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ਆਥ ਹੈੱਡਰ ਅਤੇ ਪੋਲ ਇੰਟਰਵਲ ਵਿਕਲਪਿਕ env vars ਹਨ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ਇਨਜੈਸਟ** — ਬਿਲਟ-ਇਨ OTLP ਰਿਸੀਵਰ `/v1/traces` ਅਤੇ `/v1/metrics` 'ਤੇ ਕਿਸੇ ਹੋਰ ਵੀ ਥਾਂ ਤੋਂ ਟਰੇਸ ਅਤੇ ਮੈਟ੍ਰਿਕਸ ਸਵੀਕਾਰ ਕਰਦਾ ਹੈ (ਪ੍ਰੋਟੋਬਫ ਇਨਜੈਸਟ ਲਈ `pip install clawmetry[otel]`)।

ਤੁਹਾਨੂੰ ਜ਼ੀਰੋ-ਕੌਨਫਿਗ, ਲੋਕਲ-ਫਸਟ ClawMetry ਡੈਸ਼ਬੋਰਡ **ਅਤੇ** ਤੁਹਾਡਾ ਡੇਟਾ ਜੋ ਵੀ ਬੈਕਐਂਡ ਤੁਹਾਡੀ ਟੀਮ ਪਹਿਲਾਂ ਹੀ ਚਲਾਉਂਦੀ ਹੈ ਉਸ ਵਿੱਚ ਮਿਲਦਾ ਹੈ — ਕੋਈ ਲੌਕ-ਇਨ ਨਹੀਂ, ਕੋਈ ਦੂਜਾ ਏਜੰਟ ਇੰਸਟਾਲ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ।

## ਕੌਨਫਿਗਰੇਸ਼ਨ

ਜ਼ਿਆਦਾਤਰ ਲੋਕਾਂ ਨੂੰ ਕਿਸੇ ਕੌਨਫਿਗ ਦੀ ਲੋੜ ਨਹੀਂ। ClawMetry ਤੁਹਾਡੇ ਵਰਕਸਪੇਸ, ਲੌਗ, ਸੈਸ਼ਨ, ਅਤੇ crons ਨੂੰ ਆਪਣੇ-ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ।

ਜੇ ਤੁਹਾਨੂੰ ਕਸਟਮਾਈਜ਼ ਕਰਨ ਦੀ ਲੋੜ ਹੋਵੇ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ਸਾਰੇ ਵਿਕਲਪ: `clawmetry --help`

## ਸਮਰਥਿਤ ਚੈਨਲ

ClawMetry ਤੁਹਾਡੇ ਦੁਆਰਾ ਕੌਨਫਿਗਰ ਕੀਤੇ ਹਰ OpenClaw ਚੈਨਲ ਲਈ ਲਾਈਵ ਗਤੀਵਿਧੀ ਦਿਖਾਉਂਦਾ ਹੈ। ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਜੋ ਅਸਲ ਵਿੱਚ ਤੁਹਾਡੇ `openclaw.json` ਵਿੱਚ ਸੈੱਟਅੱਪ ਕੀਤੇ ਹਨ Flow ਡਾਇਗ੍ਰਾਮ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ — ਅਣ-ਕੌਨਫਿਗਰਡ ਚੈਨਲ ਆਪਣੇ-ਆਪ ਲੁਕ ਜਾਂਦੇ ਹਨ।

Flow ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੈਨਲ ਨੋਡ 'ਤੇ ਕਲਿੱਕ ਕਰੋ ਤਾਂ ਜੋ ਆਉਣ ਵਾਲੇ/ਜਾਣ ਵਾਲੇ ਮੈਸੇਜ ਗਿਣਤੀ ਸਮੇਤ ਇੱਕ ਲਾਈਵ ਚੈਟ ਬੱਬਲ ਵਿਊ ਦੇਖ ਸਕੋ।

| ਚੈਨਲ | ਸਥਿਤੀ | ਲਾਈਵ ਪੌਪਅੱਪ | ਨੋਟਸ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ਪੂਰਾ | ✅ | ਮੈਸੇਜ, ਅੰਕੜੇ, 10s ਰਿਫ੍ਰੈਸ਼ |
| 💬 **iMessage** | ✅ ਪੂਰਾ | ✅ | `~/Library/Messages/chat.db` ਸਿੱਧਾ ਪੜ੍ਹਦਾ ਹੈ |
| 💚 **WhatsApp** | ✅ ਪੂਰਾ | ✅ | WhatsApp Web (Baileys) ਰਾਹੀਂ |
| 🔵 **Signal** | ✅ ਪੂਰਾ | ✅ | signal-cli ਰਾਹੀਂ |
| 🟣 **Discord** | ✅ ਪੂਰਾ | ✅ | ਗਿਲਡ + ਚੈਨਲ ਪਛਾਣ |
| 🟪 **Slack** | ✅ ਪੂਰਾ | ✅ | ਵਰਕਸਪੇਸ + ਚੈਨਲ ਪਛਾਣ |
| 🌐 **Webchat** | ✅ ਪੂਰਾ | ✅ | ਬਿਲਟ-ਇਨ ਵੈੱਬ UI ਸੈਸ਼ਨ |
| 📡 **IRC** | ✅ ਪੂਰਾ | ✅ | ਟਰਮੀਨਲ-ਸਟਾਈਲ ਬੱਬਲ UI |
| 🍏 **BlueBubbles** | ✅ ਪੂਰਾ | ✅ | BlueBubbles REST API ਰਾਹੀਂ iMessage |
| 🔵 **Google Chat** | ✅ ਪੂਰਾ | ✅ | Chat API ਵੈੱਬਹੁੱਕਾਂ ਰਾਹੀਂ |
| 🟣 **MS Teams** | ✅ ਪੂਰਾ | ✅ | Teams ਬੌਟ ਪਲੱਗਇਨ ਰਾਹੀਂ |
| 🔷 **Mattermost** | ✅ ਪੂਰਾ | ✅ | ਸੈਲਫ-ਹੋਸਟਡ ਟੀਮ ਚੈਟ |
| 🟩 **Matrix** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ, E2EE ਸਮਰਥਨ |
| 🟢 **LINE** | ✅ ਪੂਰਾ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ NIP-04 DM |
| 🟣 **Twitch** | ✅ ਪੂਰਾ | ✅ | IRC ਕਨੈਕਸ਼ਨ ਰਾਹੀਂ ਚੈਟ |
| 🔷 **Feishu/Lark** | ✅ ਪੂਰਾ | ✅ | WebSocket ਈਵੈਂਟ ਸਬਸਕ੍ਰਿਪਸ਼ਨ |
| 🔵 **Zalo** | ✅ ਪੂਰਾ | ✅ | Zalo Bot API |

> **ਆਪਣੇ-ਆਪ ਪਛਾਣ:** ClawMetry ਤੁਹਾਡੀ `~/.openclaw/openclaw.json` ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਰੈਂਡਰ ਕਰਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਅਸਲ ਵਿੱਚ ਕੌਨਫਿਗਰ ਕੀਤੇ ਹਨ। ਕੋਈ ਮੈਨੁਅਲ ਸੈੱਟਅੱਪ ਲੋੜੀਂਦਾ ਨਹੀਂ।

## Docker ਡਿਪਲੌਇਮੈਂਟ

ClawMetry ਨੂੰ ਕੰਟੇਨਰ ਵਿੱਚ ਚਲਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ? ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ! 🐳

**Docker ਨਾਲ ਤੇਜ਼ ਸ਼ੁਰੂਆਤ:**

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

> **ਨੋਟ:** Docker ਵਿੱਚ ਚਲਾਉਂਦੇ ਸਮੇਂ, ਆਪਣੇ ਏਜੰਟ ਦੀ ਡੇਟਾ + ਲੌਗ ਡਾਇਰੈਕਟਰੀਆਂ (ਜਿਵੇਂ `~/.openclaw`, `~/.claude`, `~/.codex`) ਮਾਊਂਟ ਕਰੋ ਤਾਂ ਜੋ ClawMetry ਤੁਹਾਡਾ ਸੈੱਟਅੱਪ ਆਪਣੇ-ਆਪ ਪਛਾਣ ਸਕੇ।

## ਲੋੜਾਂ

- Python 3.8+
- Flask (pip ਰਾਹੀਂ ਆਪਣੇ-ਆਪ ਇੰਸਟਾਲ ਹੁੰਦਾ ਹੈ)
- ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ AI ਏਜੰਟ ਰਨਟਾਈਮ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ਜਾਂ Antigravity (ਜਾਂ Docker ਲਈ ਮਾਊਂਟ ਕੀਤੇ ਵਾਲਿਊਮ)
- Linux ਜਾਂ macOS

## NemoClaw / OpenShell ਸਮਰਥਨ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) ਨੂੰ ਆਪਣੇ-ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ — NVIDIA ਦਾ ਐਂਟਰਪ੍ਰਾਈਜ਼ ਸੁਰੱਖਿਆ ਰੈਪਰ OpenClaw ਲਈ ਜੋ ਏਜੰਟਾਂ ਨੂੰ ਸੈਂਡਬੌਕਸਡ OpenShell ਕੰਟੇਨਰਾਂ ਅੰਦਰ ਚਲਾਉਂਦਾ ਹੈ।

ਜ਼ਿਆਦਾਤਰ ਮਾਮਲਿਆਂ ਵਿੱਚ ਕੋਈ ਵਾਧੂ ਕੌਨਫਿਗਰੇਸ਼ਨ ਲੋੜੀਂਦੀ ਨਹੀਂ। ਸਿੰਕ ਡੀਮਨ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਆਪਣੇ-ਆਪ ਲੱਭ ਲੈਂਦਾ ਹੈ ਭਾਵੇਂ ਉਹ ਹੋਸਟ 'ਤੇ `~/.openclaw/` ਵਿੱਚ ਹੋਣ ਜਾਂ OpenShell ਕੰਟੇਨਰ ਅੰਦਰ।

### ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry NemoClaw ਨੂੰ ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ ਪਛਾਣਦਾ ਹੈ:

1. **ਬਾਈਨਰੀ ਪਛਾਣ** — `nemoclaw` CLI ਲਈ ਚੈੱਕ ਕਰਦਾ ਹੈ ਅਤੇ ਸੈਂਡਬੌਕਸ ਜਾਣਕਾਰੀ ਲੈਣ ਲਈ `nemoclaw status` ਚਲਾਉਂਦਾ ਹੈ
2. **ਕੰਟੇਨਰ ਪਛਾਣ** — ਚੱਲ ਰਹੇ Docker ਕੰਟੇਨਰਾਂ ਨੂੰ `openshell`, `nemoclaw`, ਜਾਂ `ghcr.io/nvidia/` ਇਮੇਜਾਂ ਲਈ ਸਕੈਨ ਕਰਦਾ ਹੈ, ਫਿਰ ਵਾਲਿਊਮ ਮਾਊਂਟ ਜਾਂ `docker cp` ਰਾਹੀਂ ਸੈਸ਼ਨ ਪੜ੍ਹਦਾ ਹੈ

NemoClaw ਕੰਟੇਨਰਾਂ ਤੋਂ ਸਿੰਕ ਹੋਈਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ `runtime=nemoclaw` ਅਤੇ `container_id` ਮੈਟਾਡੇਟਾ ਨਾਲ ਟੈਗ ਕੀਤਾ ਜਾਂਦਾ ਹੈ, ਤਾਂ ਜੋ ਤੁਸੀਂ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਇਹਨਾਂ ਨੂੰ ਸਟੈਂਡਰਡ OpenClaw ਸੈਸ਼ਨਾਂ ਤੋਂ ਵੱਖ ਕਰ ਸਕੋ।

### ਸਿਫ਼ਾਰਸ਼ੀ ਸੈੱਟਅੱਪ: HOST 'ਤੇ ਸਿੰਕ ਡੀਮਨ

ਬਿਹਤਰੀਨ ਅਨੁਭਵ ਲਈ, ClawMetry ਦਾ ਸਿੰਕ ਡੀਮਨ **ਹੋਸਟ ਮਸ਼ੀਨ** 'ਤੇ ਚਲਾਓ (ਸੈਂਡਬੌਕਸ ਅੰਦਰ ਨਹੀਂ)। ਇਸ ਨਾਲ NemoClaw ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਪਾਬੰਦੀਆਂ ਤੋਂ ਬਚਿਆ ਜਾਂਦਾ ਹੈ।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ਸਿੰਕ ਡੀਮਨ ਕਿਸੇ ਵੀ ਚੱਲ ਰਹੇ OpenShell ਕੰਟੇਨਰ ਅੰਦਰ ਸੈਸ਼ਨ ਆਪਣੇ-ਆਪ ਲੱਭ ਲਵੇਗਾ।

### ਵਿਕਲਪਿਕ: ਸਪਸ਼ਟ ਸੈਂਡਬੌਕਸ ਨਾਮ

ਜੇ ਆਪਣੇ-ਆਪ ਪਛਾਣ ਕੰਮ ਨਾ ਕਰੇ, ਤਾਂ ClawMetry ਨੂੰ ਸਹੀ ਸੈਂਡਬੌਕਸ ਵੱਲ ਇਸ਼ਾਰਾ ਕਰੋ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ਸੈਂਡਬੌਕਸ ਅੰਦਰ ਚਲਾਉਣਾ (ਐਡਵਾਂਸਡ)

ਜੇ ਤੁਹਾਨੂੰ ਸਿੰਕ ਡੀਮਨ **ਅੰਦਰ** OpenShell ਸੈਂਡਬੌਕਸ ਵਿੱਚ ਚਲਾਉਣਾ ਹੀ ਪਵੇ, ਤਾਂ ਆਪਣੀ NemoClaw ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਵਿੱਚ ਇਹ egress ਨਿਯਮ ਜੋੜੋ ਤਾਂ ਜੋ ਇਹ ClawMetry ingest API ਤੱਕ ਪਹੁੰਚ ਸਕੇ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ਲਾਗੂ ਕਰੋ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ਪੋਰਟ ਅਤੇ ਐਂਡਪੌਇੰਟ

| ਐਂਡਪੌਇੰਟ | ਪੋਰਟ | ਪ੍ਰੋਟੋਕੋਲ | ਲੋੜੀਂਦਾ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ਹਾਂ (ਸਿੰਕ ਡੀਮਨ → ਕਲਾਊਡ) |
| `localhost:8900` | 8900 | HTTP | ਹਾਂ (ਲੋਕਲ ਡੈਸ਼ਬੋਰਡ UI) |
| Docker ਸੌਕਟ (`/var/run/docker.sock`) | — | Unix ਸੌਕਟ | ਕੰਟੇਨਰ ਸੈਸ਼ਨ ਖੋਜ ਲਈ |

ਸਿੰਕ ਡੀਮਨ ਸਿਰਫ਼ `ingest.clawmetry.com` ਵੱਲ ਬਾਹਰ ਜਾਣ ਵਾਲੀਆਂ HTTPS ਕਾਲਾਂ ਕਰਦਾ ਹੈ। ਕੋਈ ਵੀ ਅੰਦਰ ਆਉਣ ਵਾਲਾ ਪੋਰਟ ਲੋੜੀਂਦਾ ਨਹੀਂ।

---

## ਕਲਾਊਡ ਡਿਪਲੌਇਮੈਂਟ

SSH ਟਨਲ, ਰਿਵਰਸ ਪ੍ਰੌਕਸੀ, ਅਤੇ Docker ਲਈ **[ਕਲਾਊਡ ਟੈਸਟਿੰਗ ਗਾਈਡ](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ਦੇਖੋ।

## ਟੈਸਟਿੰਗ

ਇਹ ਪ੍ਰੋਜੈਕਟ BrowserStack ਨਾਲ ਟੈਸਟ ਕੀਤਾ ਗਿਆ ਹੈ।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ਟੈਲੀਮੈਟਰੀ

ClawMetry `https://app.clawmetry.com/api/install` ਨੂੰ ਅਗਿਆਤ ਇੰਸਟਾਲ-ਲਾਈਫਸਾਈਕਲ ਪਿੰਗ ਭੇਜਦਾ ਹੈ:
ਜਦੋਂ ਤੁਸੀਂ ਕਿਸੇ ਨਵੀਂ ਮਸ਼ੀਨ 'ਤੇ ਪਹਿਲੀ ਵਾਰ `clawmetry` CLI ਚਲਾਉਂਦੇ ਹੋ ਤਾਂ ਇੱਕ `install` ਪਿੰਗ, ਕਿਸੇ ਨਵੇਂ ਵਰਜ਼ਨ ਵਿੱਚ ਅੱਪਗ੍ਰੇਡ ਕਰਨ ਤੋਂ ਬਾਅਦ ਪਹਿਲੀ ਰਨ 'ਤੇ ਇੱਕ `update` ਪਿੰਗ, ਅਤੇ ਜਦੋਂ ਤੁਸੀਂ ਡੈਸ਼ਬੋਰਡ-ਅੰਦਰੂਨੀ ਔਨਬੋਰਡਿੰਗ ਚੋਣ ਪੂਰੀ ਕਰਦੇ ਹੋ ਤਾਂ ਇੱਕ `onboarded` ਪਿੰਗ। ਅਸੀਂ ਇਸ ਦੀ ਵਰਤੋਂ ਅਸਲ ਇੰਸਟਾਲ ਗਿਣਨ ਲਈ ਕਰਦੇ ਹਾਂ (ਕੱਚੇ PyPI ਡਾਊਨਲੋਡ ਅੰਕੜੇ ~98% ਮਿਰਰ, CI, ਅਤੇ ਆਟੋ-ਅੱਪਡੇਟ ਦੁਬਾਰਾ-ਡਾਊਨਲੋਡ ਹੁੰਦੇ ਹਨ) ਅਤੇ ਇਹ ਜਾਣਨ ਲਈ ਕਿ ਕਿਹੜੇ ਏਜੰਟ ਫਰੇਮਵਰਕ ਅਤੇ ਵਰਜ਼ਨ ਅਸਲ ਵਿੱਚ ਵਰਤੋਂ ਵਿੱਚ ਹਨ।

**ਹਰ ਵਰਜ਼ਨ ਲਈ ਹਰ ਲਾਈਫਸਾਈਕਲ ਈਵੈਂਟ ਲਈ ਵੱਧ ਤੋਂ ਵੱਧ ਇੱਕ POST**, ਜਿਸ ਵਿੱਚ ਇਹ ਹੁੰਦਾ ਹੈ:

| ਫੀਲਡ | ਉਦਾਹਰਨ | ਕਿਉਂ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` 'ਤੇ ਸਟੋਰ ਕੀਤਾ ਰੈਂਡਮ UUID | ਡੀਡੁਪ; ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਸਪਸ਼ਟ ਤੌਰ 'ਤੇ Cloud sync ਨਾਲ ਕਨੈਕਟ ਨਹੀਂ ਕਰਦੇ ਓਦੋਂ ਤੱਕ ਅਗਿਆਤ (ਫਿਰ ਪ੍ਰਮਾਣਿਤ ਡੀਮਨ ਹਾਰਟਬੀਟ ਇਸ ਨੂੰ ਲੈ ਜਾਂਦਾ ਹੈ, ਇਸ ਇੰਸਟਾਲ ਨੂੰ ਤੁਹਾਡੇ ਖਾਤੇ ਨਾਲ ਜੋੜਦਾ ਹੈ) |
| `event` | `install` / `update` / `onboarded` | ਨਵੀਂ ਇੰਸਟਾਲ ਬਨਾਮ ਮੌਜੂਦਾ ਦਾ ਅੱਪਗ੍ਰੇਡ |
| `version` | `0.12.167` | ਕਿਹੜੇ ਵਰਜ਼ਨ ਵਰਤੋਂ ਵਿੱਚ ਹਨ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ਪਲੇਟਫਾਰਮ ਸਮਰਥਨ ਤਰਜੀਹਾਂ |
| `python` | `3.11.15` | Python ਵਰਜ਼ਨ ਸਮਰਥਨ ਮੈਟ੍ਰਿਕਸ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ਸਾਨੂੰ ਅੱਗੇ ਕਿਹੜੇ ਏਜੰਟਾਂ ਨਾਲ ਏਕੀਕ੍ਰਿਤ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ਮਨੁੱਖੀ ਇੰਸਟਾਲਾਂ ਨੂੰ CI ਸ਼ੋਰ ਤੋਂ ਵੱਖ ਕਰੋ |

**ਅਸੀਂ ਇਹ ਨਹੀਂ ਭੇਜਦੇ**: IP (ਕਲਾਊਡ ਸਰਵਰ-ਸਾਈਡ ਬੇਨਤੀ ਤੋਂ ਦੇਸ਼ ਕੋਡ
ਕੱਢਦਾ ਹੈ, ਫਿਰ IP ਹਟਾ ਦਿੰਦਾ ਹੈ), ਹੋਸਟਨਾਮ, ਯੂਜ਼ਰਨਾਮ, ਵਰਕਸਪੇਸ
ਪਾਥ, ਫਾਈਲ ਸਮੱਗਰੀ, ਤੁਹਾਡੀ api_key, ਤੁਹਾਡੀ ਈਮੇਲ, ਕੁਝ ਵੀ PII ਜਾਂ
ਵਰਕਸਪੇਸ-ਵਿਸ਼ੇਸ਼। ਵਾਇਰ ਪੇਲੋਡ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ਵਿੱਚ ਆਡਿਟ-ਯੋਗ ਹੈ।

**ਬੰਦ ਕਰੋ** (ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਵੀ ਇੱਕ ਇਸਨੂੰ ਹਮੇਸ਼ਾ ਲਈ ਬੰਦ ਕਰ ਦਿੰਦਾ ਹੈ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ਇੱਥੇ ਨੈੱਟਵਰਕ ਫੇਲ੍ਹ ਹੋਣ ਨਾਲ `clawmetry` ਕਦੇ ਵੀ ਚੱਲਣ ਤੋਂ ਨਹੀਂ ਰੁਕਦਾ —
ਪਿੰਗ ਇੱਕ ਡੀਮਨ ਥਰੈੱਡ 'ਤੇ 3 ਸੈਕਿੰਡ ਟਾਈਮਆਊਟ ਨਾਲ ਫਾਇਰ-ਐਂਡ-ਫੌਰਗੈੱਟ ਹੈ।

## ਸਟਾਰ ਹਿਸਟਰੀ

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
  <strong>🦞 ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਹੋਏ ਦੇਖੋ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ਈਕੋਸਿਸਟਮ ਦਾ ਹਿੱਸਾ</sub>
</p>
