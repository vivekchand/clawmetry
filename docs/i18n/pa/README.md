<!-- i18n-src:7cfb63716507 -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਵੇਖੋ।** **14 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 10 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ਉੱਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ ਅਤੇ ਤੁਹਾਡਾ ਕੰਮ ਹੋ ਗਿਆ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਦੀ ਸ਼ੁਰੂਆਤ OpenClaw ਲਈ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ ਵਜੋਂ ਹੋਈ ਸੀ, ਅਤੇ ਹੁਣ ਇਹ ਇੱਕ ਹੀ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਤੁਹਾਡੇ **ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ** ਨੂੰ ਮੀਟਰ ਕਰਦਾ ਹੈ, ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਉੱਤੇ ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣਦੇ ਹੋਏ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw ਅਤੇ NemoClaw ਓਪਨ-ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ ਹਨ; ਬਾਕੀ ਰਨਟਾਈਮਾਂ ClawMetry Cloud ਜਾਂ ਸੈਲਫ-ਹੋਸਟਡ Pro ਲਾਇਸੈਂਸ ਨਾਲ ਸਰਗਰਮ ਹੁੰਦੀਆਂ ਹਨ। ਹੈਡਰ ਤੋਂ ਰਨਟਾਈਮ ਬਦਲੋ ਅਤੇ ਹਰ ਟੈਬ — ਖਰਚਾ, ਟੋਕਨ, ਟੂਲ, ਟਰੇਸ — ਉਸ ਰਨਟਾਈਮ ਲਈ ਮੁੜ-ਸਕੋਪ ਹੋ ਜਾਂਦੀ ਹੈ। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, `/api/entitlement` ਸ਼ੇਪ, ਅਤੇ `clawmetry license` CLI ਲਈ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ਵੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **Flow** — ਚੈਨਲਾਂ, ਬ੍ਰੇਨ, ਟੂਲਾਂ ਵਿੱਚੋਂ ਹੋ ਕੇ ਅਤੇ ਵਾਪਸ ਵਹਿੰਦੇ ਸੁਨੇਹਿਆਂ ਨੂੰ ਵਿਖਾਉਂਦਾ ਲਾਈਵ ਐਨੀਮੇਟਡ ਡਾਇਗ੍ਰਾਮ
- **Overview** — ਸਿਹਤ ਜਾਂਚਾਂ, ਗਤੀਵਿਧੀ ਹੀਟਮੈਪ, ਸੈਸ਼ਨ ਗਿਣਤੀ, ਮਾਡਲ ਜਾਣਕਾਰੀ
- **Usage** — ਰੋਜ਼ਾਨਾ/ਹਫ਼ਤਾਵਾਰੀ/ਮਹੀਨਾਵਾਰੀ ਵੰਡ ਨਾਲ ਟੋਕਨ ਅਤੇ ਖਰਚੇ ਦੀ ਟਰੈਕਿੰਗ
- **Sessions** — ਮਾਡਲ, ਟੋਕਨ, ਆਖਰੀ ਗਤੀਵਿਧੀ ਨਾਲ ਸਰਗਰਮ ਏਜੰਟ ਸੈਸ਼ਨ
- **Crons** — ਸਥਿਤੀ, ਅਗਲੀ ਦੌੜ, ਮਿਆਦ ਸਮੇਤ ਸ਼ਡਿਊਲਡ ਜੌਬਾਂ
- **Logs** — ਰੰਗ-ਕੋਡਿਡ ਰੀਅਲ-ਟਾਈਮ ਲਾਗ ਸਟ੍ਰੀਮਿੰਗ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ਰੋਜ਼ਾਨਾ ਨੋਟਸ ਬ੍ਰਾਊਜ਼ ਕਰੋ
- **Transcripts** — ਸੈਸ਼ਨ ਇਤਿਹਾਸ ਪੜ੍ਹਨ ਲਈ ਚੈਟ-ਬਬਲ UI
- **Alerts** — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, ਏਜੰਟ-ਆਫ਼ਲਾਈਨ ਖੋਜ; Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਕਰਦਾ ਹੈ
- **Approvals** — ਵਿਨਾਸ਼ਕਾਰੀ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, DB ਬਦਲਾਅ, sudo, ਪੈਕੇਜ ਇੰਸਟਾਲ, ਨੈੱਟਵਰਕ ਕਾਲਾਂ ਨੂੰ ਇੱਕ-ਕਲਿੱਕ ਮਨਜ਼ੂਰੀ ਪਿੱਛੇ ਗੇਟ ਕਰੋ

## ਸਕ੍ਰੀਨਸ਼ਾਟ

### 🧠 Brain — ਲਾਈਵ ਏਜੰਟ ਇਵੈਂਟ ਸਟ੍ਰੀਮ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ਟੋਕਨ ਵਰਤੋਂ ਅਤੇ ਸੈਸ਼ਨ ਸੰਖੇਪ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ਰੀਅਲ-ਟਾਈਮ ਟੂਲ ਕਾਲ ਫੀਡ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਵਾਰ ਖਰਚੇ ਦੀ ਵੰਡ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ਵਰਕਸਪੇਸ ਫਾਈਲ ਬ੍ਰਾਊਜ਼ਰ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ਸਥਿਤੀ ਅਤੇ ਆਡਿਟ ਲਾਗ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, Slack / Discord / PagerDuty / Email ਲਈ ਵੈਬਹੁੱਕ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ਜੋਖਮ ਭਰੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਮੈਨੁਅਲ ਮਨਜ਼ੂਰੀ ਪਿੱਛੇ ਗੇਟ ਕਰੋ; ਪਾਲਿਸੀ-ਸਮਰਥਿਤ ਸੁਰੱਖਿਆ ਨਿਯਮ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ਲਈ ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਬਲੌਕਿੰਗ** — ਇੱਕ ਕਮਾਂਡ ਇੱਕ
PreToolUse ਹੁੱਕ ਇੰਸਟਾਲ ਕਰਦੀ ਹੈ ਜੋ ਮੇਲ ਖਾਂਦੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ *ਚੱਲਣ ਤੋਂ ਪਹਿਲਾਂ* ਰੋਕਦੀ ਹੈ ਅਤੇ ਤੁਹਾਡੇ ਫੈਸਲੇ ਦੀ ਉਡੀਕ ਕਰਦੀ ਹੈ (ਤੁਹਾਡੇ ਫ਼ੋਨ ਤੋਂ ਇੱਕ ਟੈਪ ਵਿੱਚ, ਜਦੋਂ
[ਕਲਾਊਡ ਪੁਸ਼ ਨੋਟੀਫਿਕੇਸ਼ਨਾਂ](https://app.clawmetry.com/push) ਚਾਲੂ ਹੋਣ):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ਇੱਕ ਇਨਕਾਰ ਸਿਰਫ਼ ਉਸ ਇੱਕ ਟੂਲ ਕਾਲ ਨੂੰ ਬਲੌਕ ਕਰਦਾ ਹੈ — ਏਜੰਟ ਆਪਣਾ ਸੈਸ਼ਨ ਬਣਾਈ ਰੱਖਦਾ ਹੈ ਅਤੇ ਕੋਈ ਹੋਰ ਤਰੀਕਾ ਅਜ਼ਮਾ ਸਕਦਾ ਹੈ। ਤੁਹਾਡੇ ਫ਼ੋਨ ਉੱਤੇ ਮਨਜ਼ੂਰੀ ਦੇਣ ਨਾਲ Claude Code ਦਾ ਆਪਣਾ
ਪਰਮਿਸ਼ਨ ਪ੍ਰੌਂਪਟ ਛੱਡਿਆ ਜਾਂਦਾ ਹੈ (ਤੁਸੀਂ ਪਹਿਲਾਂ ਹੀ ਜਵਾਬ ਦੇ ਦਿੱਤਾ ਹੈ)। ਬੇਮੇਲ ਟੂਲਾਂ ਦੀ ਲਾਗਤ ~40ms ਹੈ ਅਤੇ
ਉਹ Claude Code ਦੇ ਆਮ ਪਰਮਿਸ਼ਨ ਫਲੋ ਵਿੱਚ ਚਲੇ ਜਾਂਦੇ ਹਨ। ਤੁਹਾਨੂੰ ਇੱਕ ਫ਼ੋਨ
ਪੁਸ਼ ਵੀ ਮਿਲਦਾ ਹੈ ਜਦੋਂ Claude Code ਖੁਦ ਤੁਹਾਡੀ ਉਡੀਕ ਕਰ ਰਿਹਾ ਹੋਵੇ (`permission_prompt` /
`idle_prompt` ਨੋਟੀਫਿਕੇਸ਼ਨ)।

## ਇੰਸਟਾਲ

**ਵਨ-ਲਾਈਨਰ (ਸਿਫਾਰਸ਼ੀ):**
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

## v2 ਫਰੰਟਐਂਡ ਵਿਕਾਸ

v2 React ਐਪ `frontend/` ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ ਅਤੇ ਜਦੋਂ Flask
ਸਰਵਰ v2 ਸਮਰੱਥ ਨਾਲ ਸ਼ੁਰੂ ਕੀਤਾ ਜਾਂਦਾ ਹੈ ਤਾਂ ਇਹ `/v2` ਉੱਤੇ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।

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
`http://localhost:8900` ਵੱਲ ਪ੍ਰੌਕਸੀ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ React ਐਪ ਬਿਨਾਂ
ਵਾਧੂ CORS ਸੈਟਅੱਪ ਦੇ ਲੋਕਲ Flask ਸਰਵਰ ਨਾਲ ਗੱਲ ਕਰ ਸਕਦੀ ਹੈ।

Python ਪੈਕੇਜ ਨਾਲ ਭੇਜਿਆ ਜਾਣ ਵਾਲਾ ਬੰਡਲ ਬਣਾਉਣ ਲਈ:

```bash
cd frontend
npm run build
```

ਪ੍ਰੋਡਕਸ਼ਨ ਬੰਡਲ `clawmetry/static/v2/dist/` ਵਿੱਚ ਲਿਖਿਆ ਜਾਂਦਾ ਹੈ।

## ਰਨਟਾਈਮ / ਏਜੰਟ ਅਨੁਕੂਲਤਾ

ClawMetry ਸਿਰਫ਼ OpenClaw ਹੀ ਨਹੀਂ, ਸਗੋਂ ਕਈ AI-ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਆਬਜ਼ਰਵ ਕਰਦਾ ਹੈ। ਹਰੇਕ ਗ਼ੈਰ-OpenClaw ਰਨਟਾਈਮ ਇੱਕ ਸਮਰਪਿਤ ਰੀਡਰ ਅਡੈਪਟਰ ਭੇਜਦਾ ਹੈ ਜੋ ਉਸਦੇ ਨੇਟਿਵ ਸੈਸ਼ਨ ਫਾਰਮੈਟ ਨੂੰ ClawMetry ਦੇ ਯੂਨੀਫਾਈਡ ਸ਼ੇਪਾਂ ਵਿੱਚ ਬਦਲਦਾ ਹੈ; ਡੈਮਨ ਇਹਨਾਂ ਨੂੰ ਉਸੇ DuckDB ਸਟੋਰ + ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ ਵਿੱਚ ਇੰਜੈਸਟ ਕਰਦਾ ਹੈ, ਰਨਟਾਈਮ ਨਾਲ ਟੈਗ ਕੀਤਾ ਹੋਇਆ, ਅਤੇ Session replay ਟੈਬ ਇੱਕ **ਰਨਟਾਈਮ ਸਵਿੱਚਰ** ਵਿਖਾਉਂਦੀ ਹੈ ਜਦੋਂ ਇੱਕ ਤੋਂ ਵੱਧ ਮੌਜੂਦ ਹੋਣ। ਪੂਰੇ ਮੈਟ੍ਰਿਕਸ + ਰਨਟਾਈਮ ਜੋੜਨ ਦੀ ਗਾਈਡ ਲਈ [`docs/compatibility.md`](docs/compatibility.md) ਵੇਖੋ, ਅਤੇ OpenClaw-ਪਰਿਵਾਰ ਦੀ ਜਾਣ-ਪਛਾਣ ਲਈ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ਵੇਖੋ।

[Perplexity ਦਾ numbat](https://github.com/perplexityai/numbat) ਏਜੰਟ-ਸੁਰੱਖਿਆ ਟੂਲ ਚਲਾ ਰਹੇ ਹੋ? ClawMetry ਇਸ ਦੀਆਂ ਖੋਜਾਂ ਅਤੇ ਲਾਗੂਕਰਨ ਫੈਸਲਿਆਂ ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਵਾਧੂ ਸੈਟਅੱਪ ਦੇ ਇੰਜੈਸਟ ਕਰਦਾ ਹੈ — [`docs/NUMBAT.md`](docs/NUMBAT.md) ਵੇਖੋ।

| ਰਨਟਾਈਮ / ਏਜੰਟ | ਸਥਿਤੀ | ਨੋਟਸ |
|---|---|---|
| **OpenClaw** | ਨੇਟਿਵ | ਹਵਾਲਾ ਰਨਟਾਈਮ, ਆਪਣੇ ਆਪ ਪਛਾਣਿਆ ਜਾਂਦਾ ਹੈ |
| **PicoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਫਲੈਟ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ। |
| **NanoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਹਰ-ਸੈਸ਼ਨ SQLite (`data/v2-sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ + ਸੁਨੇਹਾ ਗਿਣਤੀ। |
| **Hermes** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.hermes/state.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ/ਖਰਚਾ। |
| **Claude Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.claude/projects/.../<id>.jsonl`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ + ਸੋਚ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Codex** | ਬੀਟਾ ਅਡੈਪਟਰ | Rollout JSONL `~/.codex/sessions/...`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Cursor** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `state.vscdb`। ਚੈਟ/ਕੰਪੋਜ਼ਰ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ। |
| **Aider** | ਬੀਟਾ ਅਡੈਪਟਰ | ਹਰ ਪ੍ਰੋਜੈਕਟ `.aider.chat.history.md`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ ਗਿਣਤੀ। |
| **Goose** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/goose`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਕੁੱਲ ਟੋਕਨ। |
| **opencode** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/opencode`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਖਰਚਾ। |
| **Qwen Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.qwen/projects/.../chats`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Pi** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.pi/agent/sessions`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਖਰਚਾ। |
| **Deep Agents** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.deepagents/.state/sessions.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਖਰਚਾ। |
| **n8n** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.n8n/database.sqlite`। ਵਰਕਫਲੋ ਐਗਜ਼ੀਕਿਊਸ਼ਨ, ਨੋਡ ਦੌੜਾਂ, AI Agent ਪ੍ਰੌਂਪਟ, ਮਾਡਲ + ਟੋਕਨ ਜਿੱਥੇ n8n ਦਰਜ ਕਰਦਾ ਹੈ। |
| **Antigravity** | ਬੀਟਾ ਅਡੈਪਟਰ | `~/.gemini/<flavor>/brain/` ਹੇਠ ਬ੍ਰੇਨ JSONL। ਗੱਲਬਾਤ, ਟੂਲ ਸਟੈੱਪ, ਸੋਚ, ਹਰ-ਜਨਰੇਸ਼ਨ Gemini ਟੋਕਨ ਵੰਡ + ਖਰਚਾ, ਬੈਕਗ੍ਰਾਊਂਡ-ਜਨਰੇਸ਼ਨ ਖਪਤ। |
| **GitHub Copilot** | ਬੀਟਾ ਅਡੈਪਟਰ | Copilot CLI `events.jsonl` `~/.copilot/session-state/` ਹੇਠ + ਹਰ-ਕਾਲ ਵਰਤੋਂ ਲੈਜਰ `session-store.db`। ਗੱਲਬਾਤ, ਟੂਲ ਕਾਲਾਂ, ਮਾਡਲ ਰੂਟਿੰਗ, ਕੈਸ਼-ਸੁਚੇਤ ਟੋਕਨ ਵੰਡ, ਵੈਂਡਰ-ਬਿਲਡ AI-ਕ੍ਰੈਡਿਟ ਖਰਚਾ। |
| **Grok** | ਬੀਟਾ ਅਡੈਪਟਰ | xAI Grok Build CLI (`~/.grok/bin/grok` ਹੇਠ Rust ਬਾਈਨਰੀ): ਗਲੋਬਲ ਇਵੈਂਟ ਲਾਗ `~/.grok/logs/unified.jsonl` + ਹਰ-ਸੈਸ਼ਨ `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`। ਗੱਲਬਾਤ, ਹਰ-ਟਰਨ ਟੋਕਨ ਵੰਡ, ਮਾਡਲ ਰੂਟਿੰਗ, ਅਤੇ CLI ਦਾ ਬਾਹਰ ਜਾਣ ਵਾਲਾ ਰੈਪੋ ਪੇਲੋਡ `~/.grok/upload_queue/` ਹੇਠ ਸਟੇਜ ਕੀਤਾ ਗਿਆ ਤਾਂ ਜੋ ਤੁਸੀਂ ਵੇਖ ਸਕੋ ਕਿ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕੀ ਗਿਆ। |

"ਬੀਟਾ ਅਡੈਪਟਰ" ਦਾ ਮਤਲਬ ਹੈ ਕਿ ClawMetry ਉਸ ਰਨਟਾਈਮ ਦੇ ਅਸਲ ਡਿਸਕ-ਉੱਤੇ-ਫਾਰਮੈਟ ਲਈ ਇੱਕ ਰੀਡਰ ਭੇਜਦਾ ਹੈ, ਹਰੇਕ ਇੱਕ ਅਸਲ ਮਸ਼ੀਨ ਉੱਤੇ ਅਸਲ ਇੰਸਟਾਲ ਨਾਲ ਬਣਾਇਆ + ਤਸਦੀਕ ਕੀਤਾ ਗਿਆ (ਵੇਖੋ `tests/fixtures/runtimes/<rt>/`)। ਅਡੈਪਟਰ ਰੀਡ-ਓਨਲੀ ਹਨ; ਹਰੇਕ ਇਸ ਬਾਰੇ ਇਮਾਨਦਾਰ ਹੈ ਕਿ ਉਸਦਾ ਰਨਟਾਈਮ ਅਸਲ ਵਿੱਚ ਕੀ ਸਟੋਰ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ, PicoClaw/NanoClaw/Cursor ਟੋਕਨ ਖਰਚਾ ਡਿਸਕ ਉੱਤੇ ਨਹੀਂ ਲਿਖਦੇ)। ਜਦੋਂ ਇੱਕ ਨੋਡ ਉੱਤੇ ਕਈ ਰਨਟਾਈਮ ਚੱਲਦੇ ਹਨ, ਰਨਟਾਈਮ ਸਵਿੱਚਰ ਸੈਸ਼ਨ ਦ੍ਰਿਸ਼ ਨੂੰ ਇੱਕ ਸਾਫ਼ ਡੀਪ-ਡਾਈਵ ਲਈ ਇੱਕ ਤੱਕ ਸੀਮਿਤ ਕਰਦਾ ਹੈ।

## ਕਿਸੇ ਵੀ SDK ਏਜੰਟ ਨੂੰ ਟਰੈਕ ਕਰੋ — ਆਊਟ-ਲੂਪ ਖਰਚਾ ਗੁਣਾਂਕਨ

ਉੱਪਰ ਦੱਸੇ ਸਾਰੇ ਰਨਟਾਈਮ ਸੈਸ਼ਨ ਡਿਸਕ ਉੱਤੇ ਲਿਖਦੇ ਹਨ। ਤੁਹਾਡਾ ਆਪਣਾ **ਪ੍ਰੋਡਕਸ਼ਨ ਏਜੰਟ** — ਜੋ ਤੁਸੀਂ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ਜਾਂ ਇੱਕ ਸਾਦੇ `httpx` ਲੂਪ ਉੱਤੇ ਬਣਾਇਆ ਹੈ — ਨਹੀਂ ਲਿਖਦਾ। ClawMetry ਦਾ ਜ਼ੀਰੋ-ਕੌਂਫਿਗ ਇੰਟਰਸੈਪਟਰ ਫਿਰ ਵੀ `httpx`/`requests` ਨੂੰ ਮੰਕੀ-ਪੈਚ ਕਰਕੇ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ (ਖਰਚਾ, ਟੋਕਨ, ਲੇਟੈਂਸੀ, ਗਲਤੀਆਂ) ਫੜਦਾ ਹੈ:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ਜਾਂ `CLAWMETRY_SOURCE=support-agent` env var) ਹਰ ਕਾਲ ਨੂੰ ਇੱਕ **ਨਾਮੀ ਸਰੋਤ** ਨਾਲ ਟੈਗ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਹਰ ਪ੍ਰੋਡਕਟ ਜੋ ਤੁਸੀਂ ਚਲਾਉਂਦੇ ਹੋ, ਡੈਸ਼ਬੋਰਡ ਦੇ Overview ਉੱਤੇ **🔌 Out-loop sources** ਕਾਰਡ ਵਿੱਚ ਆਪਣੀ ਖੁਦ ਦੀ, ਖਰਚਾ-ਗੁਣਾਂਕਨ-ਯੋਗ ਲਾਈਨ ਵਜੋਂ ਦਿਖਾਈ ਦਿੰਦਾ ਹੈ — ਕਾਲਾਂ, ਪ੍ਰਦਾਤਾ, ਲੇਟੈਂਸੀ, ਹਰ ਏਜੰਟ ਦੀ ਗਲਤੀ ਦਰ। ਕੋਈ ਸਰੋਤ ਸੈੱਟ ਨਹੀਂ ਕੀਤਾ? ਕਾਲਾਂ ਫਿਰ ਵੀ ਟਰੈਕ ਹੁੰਦੀਆਂ ਹਨ; ਕਾਰਡ ਬੱਸ ਲੁਕਿਆ ਰਹਿੰਦਾ ਹੈ।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ਇਹ ਉਹੀ ਡਾਟਾ ਲੇਅਰ ਹੈ ਜੋ ਰਨਟਾਈਮ ਅਡੈਪਟਰ ਖੁਆਉਂਦੇ ਹਨ (DuckDB → ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ), ਇਸ ਲਈ ਆਊਟ-ਲੂਪ ਸਰੋਤ ਬਾਕੀ ਸਭ ਵਾਂਗ ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਨਾਲ ਸਿੰਕ ਹੁੰਦੇ ਹਨ, E2E-ਇਨਕ੍ਰਿਪਟਡ।

## OpenTelemetry — ਵੈਂਡਰ-ਨਿਊਟਰਲ, ਆਪਣੇ ਟਰੇਸ ਕਿਤੇ ਵੀ ਭੇਜੋ

ClawMetry **GenAI ਸੈਮੈਂਟਿਕ ਕਨਵੈਨਸ਼ਨਾਂ** ਦੀ ਵਰਤੋਂ ਕਰਦੇ ਹੋਏ, ਦੋਵੇਂ ਦਿਸ਼ਾਵਾਂ ਵਿੱਚ **OpenTelemetry** ਬੋਲਦਾ ਹੈ, ਇਸ ਲਈ ਤੁਹਾਡੇ ਏਜੰਟ ਟਰੇਸ ਕਦੇ ਵੀ ਇੱਕ ਟੂਲ ਵਿੱਚ ਲਾੱਕ ਨਹੀਂ ਹੁੰਦੇ।

ਹਰ ਸੈਸ਼ਨ — LLM ਕਾਲਾਂ, ਟੂਲ, ਸਬ-ਏਜੰਟ, ਟੋਕਨ, ਖਰਚਾ — ਨੂੰ OTLP/HTTP GenAI ਸਪੈਨ ਵਜੋਂ ਕਿਸੇ ਵੀ ਕਲੈਕਟਰ (Datadog, Grafana, Honeycomb, ਜਾਂ ਤੁਹਾਡੇ ਆਪਣੇ OTel Collector) ਲਈ **ਐਕਸਪੋਰਟ** ਕਰੋ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ਆਥ ਹੈਡਰ ਅਤੇ ਪੋਲ ਇੰਟਰਵਲ ਵਿਕਲਪਿਕ env ਵੇਰੀਏਬਲ ਹਨ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ਇੰਜੈਸਟ** — ਬਿਲਟ-ਇਨ OTLP ਰਿਸੀਵਰ `/v1/traces` ਅਤੇ `/v1/metrics` ਉੱਤੇ ਕਿਸੇ ਹੋਰ ਵੀ ਥਾਂ ਤੋਂ ਟਰੇਸ ਅਤੇ ਮੈਟ੍ਰਿਕ ਸਵੀਕਾਰ ਕਰਦਾ ਹੈ (protobuf ਇੰਜੈਸਟ ਲਈ `pip install clawmetry[otel]`)।

ਤੁਹਾਨੂੰ ਜ਼ੀਰੋ-ਕੌਂਫਿਗ, ਲੋਕਲ-ਫਸਟ ClawMetry ਡੈਸ਼ਬੋਰਡ **ਅਤੇ** ਤੁਹਾਡੀ ਟੀਮ ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਚਲਾ ਰਹੀ ਕਿਸੇ ਵੀ ਬੈਕਐਂਡ ਵਿੱਚ ਤੁਹਾਡਾ ਡਾਟਾ ਮਿਲਦਾ ਹੈ — ਕੋਈ ਲਾੱਕ-ਇਨ ਨਹੀਂ, ਦੂਜਾ ਇੰਸਟਾਲ ਕਰਨ ਵਾਲਾ ਏਜੰਟ ਨਹੀਂ।

## ਕੌਂਫਿਗਰੇਸ਼ਨ

ਜ਼ਿਆਦਾਤਰ ਲੋਕਾਂ ਨੂੰ ਕਿਸੇ ਕੌਂਫਿਗ ਦੀ ਲੋੜ ਨਹੀਂ। ClawMetry ਤੁਹਾਡੇ ਵਰਕਸਪੇਸ, ਲਾਗ, ਸੈਸ਼ਨ, ਅਤੇ crons ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

ਜੇ ਤੁਹਾਨੂੰ ਕਸਟਮਾਈਜ਼ ਕਰਨ ਦੀ ਲੋੜ ਹੈ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ਸਭ ਵਿਕਲਪ: `clawmetry --help`

## ਸਮਰਥਿਤ ਚੈਨਲ

ClawMetry ਤੁਹਾਡੇ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਰ OpenClaw ਚੈਨਲ ਲਈ ਲਾਈਵ ਗਤੀਵਿਧੀ ਵਿਖਾਉਂਦਾ ਹੈ। ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਜੋ ਤੁਹਾਡੇ `openclaw.json` ਵਿੱਚ ਅਸਲ ਵਿੱਚ ਸੈੱਟਅੱਪ ਕੀਤੇ ਹਨ Flow ਡਾਇਗ੍ਰਾਮ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ — ਬਿਨਾਂ-ਕੌਂਫਿਗਰ ਵਾਲੇ ਆਪਣੇ ਆਪ ਲੁਕਾਏ ਜਾਂਦੇ ਹਨ।

Flow ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੈਨਲ ਨੋਡ ਉੱਤੇ ਕਲਿੱਕ ਕਰੋ ਤਾਂ ਜੋ ਆਉਣ ਵਾਲੇ/ਜਾਣ ਵਾਲੇ ਸੁਨੇਹਾ ਗਿਣਤੀ ਸਮੇਤ ਇੱਕ ਲਾਈਵ ਚੈਟ ਬਬਲ ਦ੍ਰਿਸ਼ ਵੇਖ ਸਕੋ।

| ਚੈਨਲ | ਸਥਿਤੀ | ਲਾਈਵ ਪੌਪਅੱਪ | ਨੋਟਸ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ਪੂਰਾ | ✅ | ਸੁਨੇਹੇ, ਅੰਕੜੇ, 10s ਰਿਫ੍ਰੈਸ਼ |
| 💬 **iMessage** | ✅ ਪੂਰਾ | ✅ | `~/Library/Messages/chat.db` ਸਿੱਧਾ ਪੜ੍ਹਦਾ ਹੈ |
| 💚 **WhatsApp** | ✅ ਪੂਰਾ | ✅ | WhatsApp Web (Baileys) ਰਾਹੀਂ |
| 🔵 **Signal** | ✅ ਪੂਰਾ | ✅ | signal-cli ਰਾਹੀਂ |
| 🟣 **Discord** | ✅ ਪੂਰਾ | ✅ | ਗਿਲਡ + ਚੈਨਲ ਖੋਜ |
| 🟪 **Slack** | ✅ ਪੂਰਾ | ✅ | ਵਰਕਸਪੇਸ + ਚੈਨਲ ਖੋਜ |
| 🌐 **Webchat** | ✅ ਪੂਰਾ | ✅ | ਬਿਲਟ-ਇਨ ਵੈੱਬ UI ਸੈਸ਼ਨ |
| 📡 **IRC** | ✅ ਪੂਰਾ | ✅ | ਟਰਮੀਨਲ-ਸਟਾਈਲ ਬਬਲ UI |
| 🍏 **BlueBubbles** | ✅ ਪੂਰਾ | ✅ | BlueBubbles REST API ਰਾਹੀਂ iMessage |
| 🔵 **Google Chat** | ✅ ਪੂਰਾ | ✅ | Chat API ਵੈਬਹੁੱਕ ਰਾਹੀਂ |
| 🟣 **MS Teams** | ✅ ਪੂਰਾ | ✅ | Teams ਬੋਟ ਪਲੱਗਇਨ ਰਾਹੀਂ |
| 🔷 **Mattermost** | ✅ ਪੂਰਾ | ✅ | ਸੈਲਫ-ਹੋਸਟਡ ਟੀਮ ਚੈਟ |
| 🟩 **Matrix** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ, E2EE ਸਮਰਥਨ |
| 🟢 **LINE** | ✅ ਪੂਰਾ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ NIP-04 DM |
| 🟣 **Twitch** | ✅ ਪੂਰਾ | ✅ | IRC ਕਨੈਕਸ਼ਨ ਰਾਹੀਂ ਚੈਟ |
| 🔷 **Feishu/Lark** | ✅ ਪੂਰਾ | ✅ | WebSocket ਇਵੈਂਟ ਸਬਸਕ੍ਰਿਪਸ਼ਨ |
| 🔵 **Zalo** | ✅ ਪੂਰਾ | ✅ | Zalo Bot API |

> **ਆਪਣੇ ਆਪ ਪਛਾਣ:** ClawMetry ਤੁਹਾਡਾ `~/.openclaw/openclaw.json` ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਹੀ ਦਿਖਾਉਂਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਅਸਲ ਵਿੱਚ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਨ। ਕੋਈ ਮੈਨੁਅਲ ਸੈੱਟਅੱਪ ਲੋੜੀਂਦਾ ਨਹੀਂ।

## Docker ਡਿਪਲੌਇਮੈਂਟ

ClawMetry ਨੂੰ ਇੱਕ ਕੰਟੇਨਰ ਵਿੱਚ ਚਲਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ? ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ! 🐳

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

> **ਨੋਟ:** Docker ਵਿੱਚ ਚਲਾਉਂਦੇ ਸਮੇਂ, ਆਪਣੇ ਏਜੰਟ ਦੀ ਡਾਟਾ + ਲਾਗ ਡਾਇਰੈਕਟਰੀਆਂ (ਜਿਵੇਂ, `~/.openclaw`, `~/.claude`, `~/.codex`) ਮਾਊਂਟ ਕਰੋ ਤਾਂ ਜੋ ClawMetry ਤੁਹਾਡਾ ਸੈੱਟਅੱਪ ਆਪਣੇ ਆਪ ਪਛਾਣ ਸਕੇ।

## ਲੋੜਾਂ

- Python 3.8+
- Flask (pip ਰਾਹੀਂ ਆਪਣੇ ਆਪ ਇੰਸਟਾਲ ਹੁੰਦਾ ਹੈ)
- ਉਸੇ ਮਸ਼ੀਨ ਉੱਤੇ ਇੱਕ AI ਏਜੰਟ ਰਨਟਾਈਮ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, ਜਾਂ QM (ਜਾਂ Docker ਲਈ ਮਾਊਂਟ ਕੀਤੇ ਵੌਲਿਊਮ)
- Linux ਜਾਂ macOS

## NemoClaw / OpenShell ਸਮਰਥਨ

ClawMetry ਆਪਣੇ ਆਪ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ਨੂੰ ਪਛਾਣਦਾ ਹੈ — NVIDIA ਦਾ ਐਂਟਰਪ੍ਰਾਈਜ਼ ਸੁਰੱਖਿਆ ਰੈਪਰ OpenClaw ਲਈ ਜੋ ਏਜੰਟਾਂ ਨੂੰ ਸੈਂਡਬਾਕਸਡ OpenShell ਕੰਟੇਨਰਾਂ ਦੇ ਅੰਦਰ ਚਲਾਉਂਦਾ ਹੈ।

ਜ਼ਿਆਦਾਤਰ ਮਾਮਲਿਆਂ ਵਿੱਚ ਵਾਧੂ ਕੌਂਫਿਗਰੇਸ਼ਨ ਲੋੜੀਂਦੀ ਨਹੀਂ। ਸਿੰਕ ਡੈਮਨ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਆਪਣੇ ਆਪ ਖੋਜ ਲੈਂਦਾ ਹੈ ਭਾਵੇਂ ਉਹ ਹੋਸਟ ਉੱਤੇ `~/.openclaw/` ਵਿੱਚ ਹੋਣ ਜਾਂ ਕਿਸੇ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ।

### ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ NemoClaw ਪਛਾਣਦਾ ਹੈ:

1. **ਬਾਈਨਰੀ ਖੋਜ** — `nemoclaw` CLI ਦੀ ਜਾਂਚ ਕਰਦਾ ਹੈ ਅਤੇ ਸੈਂਡਬਾਕਸ ਜਾਣਕਾਰੀ ਲੈਣ ਲਈ `nemoclaw status` ਚਲਾਉਂਦਾ ਹੈ
2. **ਕੰਟੇਨਰ ਖੋਜ** — ਚੱਲ ਰਹੇ Docker ਕੰਟੇਨਰਾਂ ਨੂੰ `openshell`, `nemoclaw`, ਜਾਂ `ghcr.io/nvidia/` ਇਮੇਜਾਂ ਲਈ ਸਕੈਨ ਕਰਦਾ ਹੈ, ਫਿਰ ਵੌਲਿਊਮ ਮਾਊਂਟ ਜਾਂ `docker cp` ਰਾਹੀਂ ਸੈਸ਼ਨ ਪੜ੍ਹਦਾ ਹੈ

NemoClaw ਕੰਟੇਨਰਾਂ ਤੋਂ ਸਿੰਕ ਕੀਤੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ `runtime=nemoclaw` ਅਤੇ `container_id` ਮੈਟਾਡਾਟਾ ਨਾਲ ਟੈਗ ਕੀਤਾ ਜਾਂਦਾ ਹੈ, ਤਾਂ ਜੋ ਤੁਸੀਂ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਉਹਨਾਂ ਨੂੰ ਸਟੈਂਡਰਡ OpenClaw ਸੈਸ਼ਨਾਂ ਤੋਂ ਵੱਖ ਕਰ ਸਕੋ।

### ਸਿਫਾਰਸ਼ੀ ਸੈੱਟਅੱਪ: HOST ਉੱਤੇ ਸਿੰਕ ਡੈਮਨ

ਸਭ ਤੋਂ ਵਧੀਆ ਅਨੁਭਵ ਲਈ, ClawMetry ਦਾ ਸਿੰਕ ਡੈਮਨ **ਹੋਸਟ ਮਸ਼ੀਨ** ਉੱਤੇ (ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਨਹੀਂ) ਚਲਾਓ। ਇਹ NemoClaw ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਪਾਬੰਦੀਆਂ ਤੋਂ ਬਚਦਾ ਹੈ।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ਸਿੰਕ ਡੈਮਨ ਆਪਣੇ ਆਪ ਚੱਲ ਰਹੇ ਕਿਸੇ ਵੀ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ ਸੈਸ਼ਨ ਲੱਭ ਲਵੇਗਾ।

### ਵਿਕਲਪਿਕ: ਸਪਸ਼ਟ ਸੈਂਡਬਾਕਸ ਨਾਮ

ਜੇ ਆਪਣੇ ਆਪ ਪਛਾਣ ਕੰਮ ਨਹੀਂ ਕਰਦੀ, ClawMetry ਨੂੰ ਸਹੀ ਸੈਂਡਬਾਕਸ ਵੱਲ ਇਸ਼ਾਰਾ ਕਰੋ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਚਲਾਉਣਾ (ਐਡਵਾਂਸਡ)

ਜੇ ਤੁਹਾਨੂੰ ਸਿੰਕ ਡੈਮਨ **ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ** OpenShell ਵਿੱਚ ਚਲਾਉਣਾ ਹੀ ਹੈ, ਤਾਂ ਆਪਣੀ NemoClaw ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਵਿੱਚ ਇਹ egress ਨਿਯਮ ਸ਼ਾਮਲ ਕਰੋ ਤਾਂ ਜੋ ਇਹ ClawMetry ਇੰਜੈਸਟ API ਤੱਕ ਪਹੁੰਚ ਸਕੇ:

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
| `ingest.clawmetry.com` | 443 | HTTPS | ਹਾਂ (ਸਿੰਕ ਡੈਮਨ → ਕਲਾਊਡ) |
| `localhost:8900` | 8900 | HTTP | ਹਾਂ (ਲੋਕਲ ਡੈਸ਼ਬੋਰਡ UI) |
| Docker ਸਾਕਟ (`/var/run/docker.sock`) | — | Unix ਸਾਕਟ | ਕੰਟੇਨਰ ਸੈਸ਼ਨ ਖੋਜ ਲਈ |

ਸਿੰਕ ਡੈਮਨ ਸਿਰਫ਼ `ingest.clawmetry.com` ਵੱਲ ਬਾਹਰ ਜਾਣ ਵਾਲੀਆਂ HTTPS ਕਾਲਾਂ ਕਰਦਾ ਹੈ। ਕੋਈ ਵੀ ਅੰਦਰ ਆਉਣ ਵਾਲੀ ਪੋਰਟ ਲੋੜੀਂਦੀ ਨਹੀਂ।

---

## ਕਲਾਊਡ ਡਿਪਲੌਇਮੈਂਟ

SSH ਟਨਲ, ਰਿਵਰਸ ਪ੍ਰੌਕਸੀ, ਅਤੇ Docker ਲਈ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ਵੇਖੋ।

## ਟੈਸਟਿੰਗ

ਇਹ ਪ੍ਰੋਜੈਕਟ BrowserStack ਨਾਲ ਟੈਸਟ ਕੀਤਾ ਗਿਆ ਹੈ।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ਟੈਲੀਮੈਟਰੀ

ClawMetry `https://app.clawmetry.com/api/install` ਨੂੰ ਗੁਮਨਾਮ ਇੰਸਟਾਲ-ਲਾਈਫਸਾਈਕਲ
ਪਿੰਗ ਭੇਜਦਾ ਹੈ: ਜਦੋਂ ਤੁਸੀਂ ਕਿਸੇ ਨਵੀਂ ਮਸ਼ੀਨ ਉੱਤੇ ਪਹਿਲੀ ਵਾਰ `clawmetry` CLI ਚਲਾਉਂਦੇ ਹੋ ਤਾਂ ਇੱਕ `install` ਪਿੰਗ, ਇੱਕ ਨਵੇਂ ਵਰਜ਼ਨ ਵਿੱਚ ਅੱਪਗ੍ਰੇਡ ਕਰਨ ਤੋਂ ਬਾਅਦ ਪਹਿਲੀ ਦੌੜ ਉੱਤੇ ਇੱਕ `update`
ਪਿੰਗ, ਅਤੇ ਜਦੋਂ ਤੁਸੀਂ ਇਨ-ਡੈਸ਼ਬੋਰਡ ਓਨਬੋਰਡਿੰਗ ਚੋਣ ਪੂਰੀ ਕਰਦੇ ਹੋ ਤਾਂ ਇੱਕ `onboarded`
ਪਿੰਗ। ਅਸੀਂ ਇਸਦੀ ਵਰਤੋਂ ਅਸਲ ਇੰਸਟਾਲਾਂ ਦੀ ਗਿਣਤੀ ਕਰਨ ਲਈ ਕਰਦੇ ਹਾਂ (ਕੱਚੇ PyPI ਡਾਊਨਲੋਡ ਨੰਬਰ ~98% ਮਿਰਰ, CI,
ਅਤੇ ਆਟੋ-ਅੱਪਡੇਟ ਮੁੜ-ਡਾਊਨਲੋਡ ਹੁੰਦੇ ਹਨ) ਅਤੇ ਇਹ ਜਾਣਨ ਲਈ ਕਿ ਅਸਲ ਵਿੱਚ ਕਿਹੜੇ ਏਜੰਟ ਫਰੇਮਵਰਕ ਅਤੇ
ਵਰਜ਼ਨ ਵਰਤੋਂ ਵਿੱਚ ਹਨ।

**ਹਰ ਲਾਈਫਸਾਈਕਲ ਇਵੈਂਟ ਲਈ ਹਰ ਵਰਜ਼ਨ ਵਿੱਚ ਵੱਧ ਤੋਂ ਵੱਧ ਇੱਕ POST**, ਜਿਸ ਵਿੱਚ ਸ਼ਾਮਲ ਹੈ:

| ਫੀਲਡ | ਉਦਾਹਰਨ | ਕਿਉਂ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ਵਿੱਚ ਸਟੋਰ ਕੀਤਾ ਰੈਂਡਮ UUID | ਡੁਪਲੀਕੇਸ਼ਨ ਹਟਾਉਣਾ; ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਸਪਸ਼ਟ ਤੌਰ ਤੇ Cloud sync ਨਾਲ ਨਹੀਂ ਜੁੜਦੇ ਗੁਮਨਾਮ (ਫਿਰ ਪ੍ਰਮਾਣਿਤ ਡੈਮਨ ਹਾਰਟਬੀਟ ਇਸਨੂੰ ਲੈ ਜਾਂਦਾ ਹੈ, ਇਸ ਇੰਸਟਾਲ ਨੂੰ ਤੁਹਾਡੇ ਖਾਤੇ ਨਾਲ ਜੋੜਦਾ ਹੈ) |
| `event` | `install` / `update` / `onboarded` | ਨਵਾਂ ਇੰਸਟਾਲ ਬਨਾਮ ਮੌਜੂਦਾ ਦਾ ਅੱਪਗ੍ਰੇਡ |
| `version` | `0.12.167` | ਕਿਹੜੇ ਵਰਜ਼ਨ ਵਰਤੋਂ ਵਿੱਚ ਹਨ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ਪਲੇਟਫਾਰਮ ਸਮਰਥਨ ਤਰਜੀਹਾਂ |
| `python` | `3.11.15` | Python ਵਰਜ਼ਨ ਸਮਰਥਨ ਮੈਟ੍ਰਿਕਸ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ਅੱਗੇ ਸਾਨੂੰ ਕਿਹੜੇ ਏਜੰਟਾਂ ਨਾਲ ਏਕੀਕਰਨ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ਮਨੁੱਖੀ ਇੰਸਟਾਲਾਂ ਨੂੰ CI ਸ਼ੋਰ ਤੋਂ ਵੱਖ ਕਰੋ |

**ਅਸੀਂ ਕੀ ਨਹੀਂ ਭੇਜਦੇ**: IP (ਕਲਾਊਡ ਬੇਨਤੀ ਤੋਂ ਸਰਵਰ-ਸਾਈਡ ਦੇਸ਼ ਕੋਡ ਕੱਢਦਾ ਹੈ, ਫਿਰ
IP ਸੁੱਟ ਦਿੰਦਾ ਹੈ), ਹੋਸਟਨਾਮ, ਯੂਜ਼ਰਨਾਮ, ਵਰਕਸਪੇਸ
ਪਾਥ, ਫਾਈਲ ਸਮੱਗਰੀ, ਤੁਹਾਡੀ api_key, ਤੁਹਾਡਾ ਈਮੇਲ, ਕੁਝ ਵੀ PII ਜਾਂ
ਵਰਕਸਪੇਸ-ਵਿਸ਼ੇਸ਼। ਵਾਇਰ ਪੇਲੋਡ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ਵਿੱਚ ਆਡਿਟ ਕਰਨ ਯੋਗ ਹੈ।

**ਆਪਟ ਆਊਟ** (ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਵੀ ਇੱਕ ਇਸਨੂੰ ਸਥਾਈ ਤੌਰ ਤੇ ਬੰਦ ਕਰ ਦਿੰਦਾ ਹੈ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ਇੱਥੇ ਨੈੱਟਵਰਕ ਅਸਫਲਤਾ ਕਦੇ ਵੀ `clawmetry` ਨੂੰ ਚੱਲਣ ਤੋਂ ਨਹੀਂ ਰੋਕਦੀ — ਪਿੰਗ
3s ਟਾਈਮਆਊਟ ਨਾਲ ਇੱਕ ਡੈਮਨ ਥ੍ਰੈੱਡ ਉੱਤੇ ਫਾਇਰ-ਐਂਡ-ਫਰਗੈੱਟ ਹੈ।

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
