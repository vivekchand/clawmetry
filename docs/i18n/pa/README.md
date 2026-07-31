<!-- i18n-src:02b789586c7d -->
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

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਨਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ਉੱਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ ਅਤੇ ਬੱਸ, ਤੁਹਾਡਾ ਕੰਮ ਹੋ ਗਿਆ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਦੀ ਸ਼ੁਰੂਆਤ OpenClaw ਲਈ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ ਵਜੋਂ ਹੋਈ ਸੀ, ਅਤੇ ਹੁਣ ਇਹ ਇੱਕ ਹੀ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਤੁਹਾਡੇ **ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ** ਨੂੰ ਮੀਟਰ ਕਰਦਾ ਹੈ, ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਉੱਤੇ ਹਰੇਕ ਰਨਟਾਈਮ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣਦੇ ਹੋਏ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ਅਤੇ NemoClaw ਓਪਨ-ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ ਹਨ; ਬਾਕੀ ਰਨਟਾਈਮ ClawMetry Cloud ਜਾਂ ਸੈਲਫ-ਹੋਸਟਡ Pro ਲਾਇਸੰਸ ਨਾਲ ਸਰਗਰਮ ਹੋ ਜਾਂਦੇ ਹਨ। ਹੈਡਰ ਤੋਂ ਰਨਟਾਈਮ ਬਦਲੋ ਅਤੇ ਹਰੇਕ ਟੈਬ, ਖ਼ਰਚਾ, ਟੋਕਨ, ਟੂਲ, ਟਰੇਸ, ਉਸ ਰਨਟਾਈਮ ਲਈ ਮੁੜ-ਸਕੋਪ ਹੋ ਜਾਂਦੀ ਹੈ। ਸਹੀ ਮੁਫ਼ਤ/ਪੇਡ ਵੰਡ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, `/api/entitlement` ਸ਼ੇਪ, ਅਤੇ `clawmetry license` CLI ਲਈ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ਵੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **Flow** — ਚੈਨਲਾਂ, ਬ੍ਰੇਨ, ਟੂਲਾਂ ਵਿੱਚੋਂ ਦੀ ਲੰਘਦੇ ਅਤੇ ਵਾਪਸ ਆਉਂਦੇ ਸੁਨੇਹਿਆਂ ਨੂੰ ਦਿਖਾਉਂਦੀ ਲਾਈਵ ਐਨੀਮੇਟਿਡ ਡਾਇਗ੍ਰਾਮ
- **Overview** — ਸਿਹਤ ਜਾਂਚ, ਗਤੀਵਿਧੀ ਹੀਟਮੈਪ, ਸੈਸ਼ਨ ਗਿਣਤੀਆਂ, ਮਾਡਲ ਜਾਣਕਾਰੀ
- **Usage** — ਰੋਜ਼ਾਨਾ/ਹਫ਼ਤਾਵਾਰੀ/ਮਹੀਨਾਵਾਰੀ ਵੰਡ ਨਾਲ ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਟਰੈਕਿੰਗ
- **Sessions** — ਮਾਡਲ, ਟੋਕਨ, ਆਖਰੀ ਗਤੀਵਿਧੀ ਸਮੇਤ ਸਰਗਰਮ ਏਜੰਟ ਸੈਸ਼ਨ
- **Crons** — ਸਥਿਤੀ, ਅਗਲੀ ਰਨ, ਮਿਆਦ ਸਮੇਤ ਤਹਿ-ਸ਼ੁਦਾ ਜੌਬ
- **Logs** — ਰੰਗ-ਕੋਡਿਡ ਰੀਅਲ-ਟਾਈਮ ਲੌਗ ਸਟ੍ਰੀਮਿੰਗ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ਰੋਜ਼ਾਨਾ ਨੋਟਸ ਬ੍ਰਾਊਜ਼ ਕਰੋ
- **Transcripts** — ਸੈਸ਼ਨ ਇਤਿਹਾਸ ਪੜ੍ਹਨ ਲਈ ਚੈਟ-ਬਬਲ UI
- **Alerts** — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, ਏਜੰਟ-ਔਫਲਾਈਨ ਪਛਾਣ; Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਕਰਦਾ ਹੈ
- **Approvals** — ਨੁਕਸਾਨਦੇਹ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, DB ਬਦਲਾਅ, sudo, ਪੈਕੇਜ ਇੰਸਟਾਲ, ਨੈੱਟਵਰਕ ਕਾਲਾਂ ਨੂੰ ਇੱਕ-ਕਲਿੱਕ ਮਨਜ਼ੂਰੀ ਪਿੱਛੇ ਰੋਕੋ

## ਸਕਰੀਨਸ਼ਾਟ

### 🧠 Brain — ਲਾਈਵ ਏਜੰਟ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ਟੋਕਨ ਵਰਤੋਂ ਅਤੇ ਸੈਸ਼ਨ ਸਾਰ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ਰੀਅਲ-ਟਾਈਮ ਟੂਲ ਕਾਲ ਫੀਡ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਮੁਤਾਬਕ ਲਾਗਤ ਵੰਡ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ਵਰਕਸਪੇਸ ਫਾਈਲ ਬ੍ਰਾਊਜ਼ਰ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ਸਥਿਤੀ ਅਤੇ ਆਡਿਟ ਲੌਗ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, Slack / Discord / PagerDuty / Email ਵੱਲ ਵੈੱਬਹੁੱਕ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਦਸਤੀ ਮਨਜ਼ੂਰੀ ਪਿੱਛੇ ਰੋਕੋ; ਨੀਤੀ-ਸਮਰਥਿਤ ਸੁਰੱਖਿਆ ਨਿਯਮ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ਲਈ ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਬਲਾਕਿੰਗ** — ਇੱਕ ਕਮਾਂਡ ਇੱਕ
PreToolUse ਹੁੱਕ ਇੰਸਟਾਲ ਕਰਦੀ ਹੈ ਜੋ ਮੇਲ ਖਾਂਦੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕਦੀ ਹੈ ਅਤੇ ਤੁਹਾਡੇ
ਫ਼ੈਸਲੇ ਦੀ ਉਡੀਕ ਕਰਦੀ ਹੈ (ਤੁਹਾਡੇ ਫ਼ੋਨ ਤੋਂ ਇੱਕ ਟੈਪ ਨਾਲ, ਜਦੋਂ
[ਕਲਾਊਡ ਪੁਸ਼ ਨੋਟੀਫਿਕੇਸ਼ਨ](https://app.clawmetry.com/push) ਚਾਲੂ ਹੋਵੇ):

```bash
clawmetry hooks install     # ~/.claude/settings.json ਲਿਖਦਾ ਹੈ (idempotent)
clawmetry hooks status      # ਕੀ ਜੁੜਿਆ ਹੈ ਅਤੇ ਕਿੰਨੀਆਂ ਨੀਤੀਆਂ ਸਰਗਰਮ ਹਨ
clawmetry hooks uninstall   # ਸਿਰਫ਼ ClawMetry ਦੀਆਂ ਐਂਟਰੀਆਂ ਹਟਾਉਂਦਾ ਹੈ
```

ਇੱਕ ਇਨਕਾਰ ਸਿਰਫ਼ ਉਸ ਇੱਕ ਟੂਲ ਕਾਲ ਨੂੰ ਰੋਕਦਾ ਹੈ, ਏਜੰਟ ਆਪਣਾ ਸੈਸ਼ਨ ਰੱਖਦਾ ਹੈ ਅਤੇ
ਕੋਈ ਹੋਰ ਤਰੀਕਾ ਅਜ਼ਮਾ ਸਕਦਾ ਹੈ। ਤੁਹਾਡੇ ਫ਼ੋਨ ਉੱਤੇ ਮਨਜ਼ੂਰੀ ਦੇਣ ਨਾਲ Claude Code ਦਾ ਆਪਣਾ
ਪਰਮਿਸ਼ਨ ਪ੍ਰੌਂਪਟ ਛੱਡਿਆ ਜਾਂਦਾ ਹੈ (ਤੁਸੀਂ ਪਹਿਲਾਂ ਹੀ ਜਵਾਬ ਦੇ ਦਿੱਤਾ ਹੈ)। ਬੇਮੇਲ ਟੂਲਾਂ ਦੀ ਲਾਗਤ ~40ms ਹੁੰਦੀ ਹੈ ਅਤੇ
ਉਹ Claude Code ਦੇ ਆਮ ਪਰਮਿਸ਼ਨ ਫਲੋਅ ਵਿੱਚ ਚਲੇ ਜਾਂਦੇ ਹਨ। ਜਦੋਂ Claude Code ਖੁਦ ਤੁਹਾਡੀ
ਉਡੀਕ ਕਰ ਰਿਹਾ ਹੋਵੇ ਤਾਂ ਵੀ ਤੁਹਾਨੂੰ ਫ਼ੋਨ ਪੁਸ਼ ਮਿਲਦਾ ਹੈ (`permission_prompt` /
`idle_prompt` ਨੋਟੀਫਿਕੇਸ਼ਨ)।

## ਇੰਸਟਾਲ

**ਇੱਕ-ਲਾਈਨਰ (ਸਿਫ਼ਾਰਸ਼ੀ):**
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
ਸਰਵਰ v2 ਚਾਲੂ ਹੋ ਕੇ ਸ਼ੁਰੂ ਕੀਤਾ ਜਾਂਦਾ ਹੈ ਤਾਂ `/v2` ਉੱਤੇ ਸਰਵ ਹੁੰਦੀ ਹੈ।

ਵਿਕਾਸ ਕਰਦੇ ਸਮੇਂ ਦੋ ਟਰਮੀਨਲ ਵਰਤੋ:

```bash
# ਟਰਮੀਨਲ 1: :8900 ਉੱਤੇ Flask API/ਸਰਵਰ
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ਟਰਮੀਨਲ 2: :5173 ਉੱਤੇ Vite ਡਿਵ ਸਰਵਰ
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ਖੋਲ੍ਹੋ। Vite `/api` ਬੇਨਤੀਆਂ ਨੂੰ
`http://localhost:8900` ਵੱਲ ਪ੍ਰੌਕਸੀ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ React ਐਪ ਬਿਨਾਂ ਕਿਸੇ ਵਾਧੂ CORS ਸੈੱਟਅੱਪ ਦੇ
ਲੋਕਲ Flask ਸਰਵਰ ਨਾਲ ਗੱਲ ਕਰ ਸਕਦੀ ਹੈ।

Python ਪੈਕੇਜ ਨਾਲ ਸ਼ਿਪ ਹੋਣ ਵਾਲਾ ਬੰਡਲ ਬਣਾਉਣ ਲਈ:

```bash
cd frontend
npm run build
```

ਪ੍ਰੋਡਕਸ਼ਨ ਬੰਡਲ `clawmetry/static/v2/dist/` ਵਿੱਚ ਲਿਖਿਆ ਜਾਂਦਾ ਹੈ।

## ਰਨਟਾਈਮ / ਏਜੰਟ ਅਨੁਕੂਲਤਾ

ClawMetry ਸਿਰਫ਼ OpenClaw ਹੀ ਨਹੀਂ, ਸਗੋਂ ਕਈ AI-ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਆਬਜ਼ਰਵ ਕਰਦਾ ਹੈ। ਹਰੇਕ ਗ਼ੈਰ-OpenClaw ਰਨਟਾਈਮ ਇੱਕ ਸਮਰਪਿਤ ਰੀਡਰ ਅਡੈਪਟਰ ਸ਼ਿਪ ਕਰਦਾ ਹੈ ਜੋ ਉਸਦੇ ਨੇਟਿਵ ਸੈਸ਼ਨ ਫਾਰਮੈਟ ਨੂੰ ClawMetry ਦੇ ਯੂਨੀਫਾਈਡ ਸ਼ੇਪਾਂ ਵਿੱਚ ਬਦਲਦਾ ਹੈ; ਡੈਮਨ ਇਹਨਾਂ ਨੂੰ ਉਸੇ DuckDB ਸਟੋਰ + ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ ਵਿੱਚ ਇੰਜੈਸਟ ਕਰਦਾ ਹੈ, ਰਨਟਾਈਮ ਨਾਲ ਟੈਗ ਕੀਤਾ ਹੋਇਆ, ਅਤੇ ਸੈਸ਼ਨ ਰੀਪਲੇਅ ਟੈਬ ਇੱਕ ਤੋਂ ਵੱਧ ਰਨਟਾਈਮ ਮੌਜੂਦ ਹੋਣ ਉੱਤੇ ਇੱਕ **ਰਨਟਾਈਮ ਸਵਿੱਚਰ** ਦਿਖਾਉਂਦੀ ਹੈ। ਪੂਰੇ ਮੈਟ੍ਰਿਕਸ + ਰਨਟਾਈਮ ਜੋੜਨ ਦੀ ਗਾਈਡ ਲਈ [`docs/compatibility.md`](docs/compatibility.md) ਵੇਖੋ, ਅਤੇ OpenClaw-ਫੈਮਿਲੀ ਪ੍ਰਾਈਮਰ ਲਈ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ਵੇਖੋ।

| ਰਨਟਾਈਮ / ਏਜੰਟ | ਸਥਿਤੀ | ਨੋਟਸ |
|---|---|---|
| **OpenClaw** | ਨੇਟਿਵ | ਰੈਫਰੈਂਸ ਰਨਟਾਈਮ, ਆਪਣੇ ਆਪ ਪਛਾਣਿਆ ਜਾਂਦਾ ਹੈ |
| **PicoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਫਲੈਟ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ। |
| **NanoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ-ਸੈਸ਼ਨ SQLite (`data/v2-sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ + ਸੁਨੇਹਾ ਗਿਣਤੀਆਂ। |
| **Hermes** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.hermes/state.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ/ਲਾਗਤ। |
| **Claude Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.claude/projects/.../<id>.jsonl`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ + ਸੋਚ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Codex** | ਬੀਟਾ ਅਡੈਪਟਰ | ਰੋਲਆਊਟ JSONL `~/.codex/sessions/...`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Cursor** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `state.vscdb`। ਚੈਟ/ਕੰਪੋਜ਼ਰ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ। |
| **Aider** | ਬੀਟਾ ਅਡੈਪਟਰ | ਹਰੇਕ ਪ੍ਰੋਜੈਕਟ ਲਈ `.aider.chat.history.md`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ ਗਿਣਤੀਆਂ। |
| **Goose** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/goose`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਕੁੱਲ। |
| **opencode** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/opencode`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Qwen Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.qwen/projects/.../chats`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Pi** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.pi/agent/sessions`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Deep Agents** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.deepagents/.state/sessions.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **n8n** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.n8n/database.sqlite`। ਵਰਕਫਲੋ ਐਗਜ਼ੀਕਿਊਸ਼ਨ, ਨੋਡ ਰਨ, AI Agent ਪ੍ਰੌਂਪਟ, ਮਾਡਲ + ਟੋਕਨ ਜਿੱਥੇ n8n ਉਹਨਾਂ ਨੂੰ ਰਿਕਾਰਡ ਕਰਦਾ ਹੈ। |
| **Antigravity** | ਬੀਟਾ ਅਡੈਪਟਰ | `~/.gemini/<flavor>/brain/` ਹੇਠਾਂ ਬ੍ਰੇਨ JSONL। ਗੱਲਬਾਤ, ਟੂਲ ਸਟੈਪ, ਸੋਚ, ਪ੍ਰਤੀ-ਜਨਰੇਸ਼ਨ Gemini ਟੋਕਨ ਵੰਡ + ਲਾਗਤ, ਬੈਕਗਰਾਊਂਡ-ਜਨਰੇਸ਼ਨ ਖ਼ਰਚਾ। |

"ਬੀਟਾ ਅਡੈਪਟਰ" ਦਾ ਮਤਲਬ ਹੈ ਕਿ ClawMetry ਉਸ ਰਨਟਾਈਮ ਦੇ ਅਸਲ ਡਿਸਕ-ਉੱਤੇ ਫਾਰਮੈਟ ਲਈ ਇੱਕ ਰੀਡਰ ਸ਼ਿਪ ਕਰਦਾ ਹੈ, ਹਰੇਕ ਨੂੰ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਉੱਤੇ ਅਸਲੀ ਇੰਸਟਾਲ ਦੇ ਵਿਰੁੱਧ ਬਣਾਇਆ + ਪੜਤਾਲਿਆ ਗਿਆ ਹੈ (ਵੇਖੋ `tests/fixtures/runtimes/<rt>/`)। ਅਡੈਪਟਰ ਪੜ੍ਹਨ-ਸਿਰਫ਼ ਹਨ; ਹਰੇਕ ਇਸ ਬਾਰੇ ਇਮਾਨਦਾਰ ਹੈ ਕਿ ਉਸਦਾ ਰਨਟਾਈਮ ਅਸਲ ਵਿੱਚ ਕੀ ਸਟੋਰ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ ਕਿ PicoClaw/NanoClaw/Cursor ਟੋਕਨ ਲਾਗਤ ਡਿਸਕ ਉੱਤੇ ਨਹੀਂ ਲਿਖਦੇ)। ਜਦੋਂ ਇੱਕ ਨੋਡ ਉੱਤੇ ਕਈ ਰਨਟਾਈਮ ਚੱਲਦੇ ਹੋਣ, ਤਾਂ ਰਨਟਾਈਮ ਸਵਿੱਚਰ ਇੱਕ ਸਾਫ਼ ਡੀਪ-ਡਾਈਵ ਲਈ ਸੈਸ਼ਨ ਵਿਊ ਨੂੰ ਇੱਕ ਤੱਕ ਸੀਮਤ ਕਰ ਦਿੰਦਾ ਹੈ।

## ਕਿਸੇ ਵੀ SDK ਏਜੰਟ ਨੂੰ ਟਰੈਕ ਕਰੋ, ਆਊਟ-ਲੂਪ ਲਾਗਤ ਵੰਡ

ਉੱਪਰ ਦੱਸੇ ਰਨਟਾਈਮ ਸਾਰੇ ਸੈਸ਼ਨ ਡਿਸਕ ਉੱਤੇ ਲਿਖਦੇ ਹਨ। ਤੁਹਾਡਾ ਆਪਣਾ **ਪ੍ਰੋਡਕਸ਼ਨ ਏਜੰਟ**, ਜੋ ਤੁਸੀਂ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ਜਾਂ ਇੱਕ ਸਾਦੇ `httpx` ਲੂਪ ਉੱਤੇ ਬਣਾਇਆ ਹੈ, ਅਜਿਹਾ ਨਹੀਂ ਕਰਦਾ। ClawMetry ਦਾ ਜ਼ੀਰੋ-ਕੌਨਫਿਗ ਇੰਟਰਸੈਪਟਰ `httpx`/`requests` ਨੂੰ ਮੌਂਕੀ-ਪੈਚ ਕਰਕੇ ਵੀ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ (ਲਾਗਤ, ਟੋਕਨ, ਲੇਟੈਂਸੀ, ਗਲਤੀਆਂ) ਨੂੰ ਫੜ ਲੈਂਦਾ ਹੈ:

```python
import clawmetry.track            # ਇੰਟਰਸੈਪਟਰ ਸਰਗਰਮ ਕਰੋ
clawmetry.track.set_source("support-agent")   # ਇਸ ਪ੍ਰੋਡਕਟ ਦਾ ਨਾਮ ਰੱਖੋ

# ...ਤੁਹਾਡਾ ਏਜੰਟ ਆਮ ਵਾਂਗ ਚੱਲਦਾ ਹੈ; ਹਰੇਕ LLM ਕਾਲ ਹੁਣ ਟਰੈਕ + ਅਟਰੀਬਿਊਟ ਹੁੰਦੀ ਹੈ।
```

`set_source()` (ਜਾਂ `CLAWMETRY_SOURCE=support-agent` env var) ਹਰੇਕ ਕਾਲ ਨੂੰ ਇੱਕ **ਨਾਮਿਤ ਸੋਰਸ** ਨਾਲ ਟੈਗ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਤੁਹਾਡੇ ਵੱਲੋਂ ਚਲਾਏ ਹਰੇਕ ਪ੍ਰੋਡਕਟ ਦੀ ਡੈਸ਼ਬੋਰਡ ਦੇ Overview ਉੱਤੇ **🔌 ਆਊਟ-ਲੂਪ ਸੋਰਸ** ਕਾਰਡ ਵਿੱਚ ਆਪਣੀ ਵੱਖਰੀ, ਲਾਗਤ-ਅਟਰੀਬਿਊਟੇਬਲ ਲਾਈਨ ਦੇ ਰੂਪ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦੀ ਹੈ, ਹਰੇਕ ਏਜੰਟ ਲਈ ਕਾਲਾਂ, ਪ੍ਰੋਵਾਈਡਰ, ਲੇਟੈਂਸੀ, ਗਲਤੀ ਦਰ। ਕੋਈ ਸੋਰਸ ਸੈੱਟ ਨਹੀਂ ਕੀਤਾ? ਕਾਲਾਂ ਫਿਰ ਵੀ ਟਰੈਕ ਹੁੰਦੀਆਂ ਹਨ; ਕਾਰਡ ਬੱਸ ਲੁਕਿਆ ਰਹਿੰਦਾ ਹੈ।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ਇਹ ਉਹੀ ਡਾਟਾ ਲੇਅਰ ਹੈ ਜੋ ਰਨਟਾਈਮ ਅਡੈਪਟਰ ਵਰਤਦੇ ਹਨ (DuckDB → ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ), ਇਸ ਲਈ ਆਊਟ-ਲੂਪ ਸੋਰਸ ਵੀ ਬਾਕੀ ਸਭ ਵਾਂਗ, E2E-ਇਨਕ੍ਰਿਪਟਿਡ, ਕਲਾਊਡ ਨਾਲ ਸਿੰਕ ਹੁੰਦੇ ਹਨ।

## OpenTelemetry — ਵੈਂਡਰ-ਨਿਊਟ੍ਰਲ, ਆਪਣੇ ਟਰੇਸ ਕਿਤੇ ਵੀ ਭੇਜੋ

ClawMetry **GenAI ਸਿਮੈਂਟਿਕ ਕਨਵੈਨਸ਼ਨਾਂ** ਵਰਤਦੇ ਹੋਏ ਦੋਵੇਂ ਦਿਸ਼ਾਵਾਂ ਵਿੱਚ **OpenTelemetry** ਬੋਲਦਾ ਹੈ, ਇਸ ਲਈ ਤੁਹਾਡੇ ਏਜੰਟ ਟਰੇਸ ਕਦੇ ਵੀ ਇੱਕ ਟੂਲ ਵਿੱਚ ਬੰਦ ਨਹੀਂ ਹੁੰਦੇ।

**ਐਕਸਪੋਰਟ**: ਹਰੇਕ ਸੈਸ਼ਨ, LLM ਕਾਲਾਂ, ਟੂਲ, ਸਬ-ਏਜੰਟ, ਟੋਕਨ, ਲਾਗਤ, ਕਿਸੇ ਵੀ ਕਲੈਕਟਰ (Datadog, Grafana, Honeycomb, ਜਾਂ ਤੁਹਾਡਾ ਆਪਣਾ OTel Collector) ਨੂੰ OTLP/HTTP GenAI ਸਪੈਨਾਂ ਵਜੋਂ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# ਬਰਾਬਰ:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ਆਥ ਹੈਡਰ ਅਤੇ ਪੋਲ ਇੰਟਰਵਲ ਵਿਕਲਪਿਕ env var ਹਨ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ਵਾਧੂ HTTP ਹੈਡਰ
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ਸਕਿੰਟ (ਡਿਫਾਲਟ 60)
```

**ਇੰਜੈਸਟ**: ਬਿਲਟ-ਇਨ OTLP ਰਿਸੀਵਰ `/v1/traces` ਅਤੇ `/v1/metrics` ਉੱਤੇ ਕਿਸੇ ਵੀ ਹੋਰ ਸੋਰਸ ਤੋਂ ਟਰੇਸ ਅਤੇ ਮੈਟ੍ਰਿਕਸ ਸਵੀਕਾਰ ਕਰਦਾ ਹੈ (protobuf ਇੰਜੈਸਟ ਲਈ `pip install clawmetry[otel]`)।

ਤੁਹਾਨੂੰ ਜ਼ੀਰੋ-ਕੌਨਫਿਗ, ਲੋਕਲ-ਫਸਟ ClawMetry ਡੈਸ਼ਬੋਰਡ **ਅਤੇ** ਤੁਹਾਡੀ ਟੀਮ ਵੱਲੋਂ ਪਹਿਲਾਂ ਹੀ ਚਲਾਏ ਜਾ ਰਹੇ ਕਿਸੇ ਵੀ ਬੈਕਐਂਡ ਵਿੱਚ ਤੁਹਾਡਾ ਡਾਟਾ ਮਿਲਦਾ ਹੈ, ਕੋਈ ਲਾਕ-ਇਨ ਨਹੀਂ, ਦੂਜਾ ਏਜੰਟ ਇੰਸਟਾਲ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ।

## ਕੌਨਫਿਗਰੇਸ਼ਨ

ਜ਼ਿਆਦਾਤਰ ਲੋਕਾਂ ਨੂੰ ਕਿਸੇ ਕੌਨਫਿਗ ਦੀ ਲੋੜ ਨਹੀਂ ਪੈਂਦੀ। ClawMetry ਤੁਹਾਡੇ ਵਰਕਸਪੇਸ, ਲੌਗ, ਸੈਸ਼ਨ, ਅਤੇ ਕ੍ਰੌਨ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ।

ਜੇ ਤੁਹਾਨੂੰ ਕਸਟਮਾਈਜ਼ ਕਰਨ ਦੀ ਲੋੜ ਹੈ:

```bash
clawmetry --port 9000              # ਕਸਟਮ ਪੋਰਟ (ਡਿਫਾਲਟ: 8900)
clawmetry --host 127.0.0.1         # ਸਿਰਫ਼ ਲੋਕਲਹੋਸਟ ਨਾਲ ਬਾਈਂਡ ਕਰੋ
clawmetry --workspace ~/mybot      # ਕਸਟਮ ਵਰਕਸਪੇਸ ਪਾਥ
clawmetry --name "Alice"           # Flow ਵਿਜ਼ੁਅਲਾਈਜ਼ੇਸ਼ਨ ਵਿੱਚ ਤੁਹਾਡਾ ਨਾਮ
```

ਸਾਰੇ ਵਿਕਲਪ: `clawmetry --help`

## ਸਮਰਥਿਤ ਚੈਨਲ

ClawMetry ਤੁਹਾਡੇ ਵੱਲੋਂ ਕੌਨਫਿਗਰ ਕੀਤੇ ਹਰੇਕ OpenClaw ਚੈਨਲ ਲਈ ਲਾਈਵ ਗਤੀਵਿਧੀ ਦਿਖਾਉਂਦਾ ਹੈ। Flow ਡਾਇਗ੍ਰਾਮ ਵਿੱਚ ਸਿਰਫ਼ ਉਹ ਚੈਨਲ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ ਜੋ ਅਸਲ ਵਿੱਚ ਤੁਹਾਡੇ `openclaw.json` ਵਿੱਚ ਸੈੱਟਅੱਪ ਹਨ, ਕੌਨਫਿਗਰ ਨਾ ਕੀਤੇ ਹੋਏ ਆਪਣੇ ਆਪ ਲੁਕਾ ਦਿੱਤੇ ਜਾਂਦੇ ਹਨ।

Flow ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੈਨਲ ਨੋਡ ਉੱਤੇ ਕਲਿੱਕ ਕਰਕੇ ਆਉਣ ਵਾਲੇ/ਜਾਣ ਵਾਲੇ ਸੁਨੇਹਾ ਗਿਣਤੀਆਂ ਵਾਲਾ ਲਾਈਵ ਚੈਟ ਬਬਲ ਵਿਊ ਵੇਖੋ।

| ਚੈਨਲ | ਸਥਿਤੀ | ਲਾਈਵ ਪੌਪਅੱਪ | ਨੋਟਸ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ਪੂਰਾ | ✅ | ਸੁਨੇਹੇ, ਅੰਕੜੇ, 10s ਰਿਫ੍ਰੈਸ਼ |
| 💬 **iMessage** | ✅ ਪੂਰਾ | ✅ | ਸਿੱਧਾ `~/Library/Messages/chat.db` ਪੜ੍ਹਦਾ ਹੈ |
| 💚 **WhatsApp** | ✅ ਪੂਰਾ | ✅ | WhatsApp Web (Baileys) ਰਾਹੀਂ |
| 🔵 **Signal** | ✅ ਪੂਰਾ | ✅ | signal-cli ਰਾਹੀਂ |
| 🟣 **Discord** | ✅ ਪੂਰਾ | ✅ | ਗਿਲਡ + ਚੈਨਲ ਪਛਾਣ |
| 🟪 **Slack** | ✅ ਪੂਰਾ | ✅ | ਵਰਕਸਪੇਸ + ਚੈਨਲ ਪਛਾਣ |
| 🌐 **Webchat** | ✅ ਪੂਰਾ | ✅ | ਬਿਲਟ-ਇਨ ਵੈੱਬ UI ਸੈਸ਼ਨ |
| 📡 **IRC** | ✅ ਪੂਰਾ | ✅ | ਟਰਮੀਨਲ-ਸਟਾਈਲ ਬਬਲ UI |
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

> **ਆਪਣੇ ਆਪ ਪਛਾਣ:** ClawMetry ਤੁਹਾਡਾ `~/.openclaw/openclaw.json` ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਉਹੀ ਚੈਨਲ ਰੈਂਡਰ ਕਰਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਅਸਲ ਵਿੱਚ ਕੌਨਫਿਗਰ ਕੀਤੇ ਹਨ। ਕਿਸੇ ਦਸਤੀ ਸੈੱਟਅੱਪ ਦੀ ਲੋੜ ਨਹੀਂ।

## Docker ਡਿਪਲਾਏਮੈਂਟ

ClawMetry ਨੂੰ ਇੱਕ ਕੰਟੇਨਰ ਵਿੱਚ ਚਲਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ? ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ! 🐳

**Docker ਨਾਲ ਤੁਰੰਤ ਸ਼ੁਰੂਆਤ:**

```bash
# ਇਮੇਜ ਬਣਾਓ
docker build -t clawmetry .

# ਡਿਫਾਲਟ ਸੈਟਿੰਗਾਂ ਨਾਲ ਚਲਾਓ
docker run -p 8900:8900 clawmetry

# ਜਾਂ ਆਪਣੇ ਏਜੰਟ ਦੀ ਡਾਟਾ ਡਾਇਰੈਕਟਰੀ ਮਾਊਂਟ ਕਰੋ (ਦਿਖਾਇਆ ਗਿਆ: OpenClaw ਦਾ ~/.openclaw)
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

> **ਨੋਟ:** Docker ਵਿੱਚ ਚਲਾਉਂਦੇ ਸਮੇਂ, ਆਪਣੇ ਏਜੰਟ ਦੀਆਂ ਡਾਟਾ + ਲੌਗ ਡਾਇਰੈਕਟਰੀਆਂ (ਜਿਵੇਂ ਕਿ `~/.openclaw`, `~/.claude`, `~/.codex`) ਮਾਊਂਟ ਕਰੋ ਤਾਂ ਜੋ ClawMetry ਤੁਹਾਡਾ ਸੈੱਟਅੱਪ ਆਪਣੇ ਆਪ ਪਛਾਣ ਸਕੇ।

## ਲੋੜਾਂ

- Python 3.8+
- Flask (pip ਰਾਹੀਂ ਆਪਣੇ ਆਪ ਇੰਸਟਾਲ ਹੁੰਦਾ ਹੈ)
- ਉਸੇ ਮਸ਼ੀਨ ਉੱਤੇ ਇੱਕ AI ਏਜੰਟ ਰਨਟਾਈਮ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ਜਾਂ Antigravity (ਜਾਂ Docker ਲਈ ਮਾਊਂਟ ਕੀਤੇ ਵਾਲਿਊਮ)
- Linux ਜਾਂ macOS

## NemoClaw / OpenShell ਸਮਰਥਨ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ, ਇਹ NVIDIA ਦਾ ਐਂਟਰਪ੍ਰਾਈਜ਼ ਸੁਰੱਖਿਆ ਰੈਪਰ ਹੈ OpenClaw ਲਈ ਜੋ ਏਜੰਟਾਂ ਨੂੰ ਸੈਂਡਬਾਕਸਡ OpenShell ਕੰਟੇਨਰਾਂ ਦੇ ਅੰਦਰ ਚਲਾਉਂਦਾ ਹੈ।

ਜ਼ਿਆਦਾਤਰ ਮਾਮਲਿਆਂ ਵਿੱਚ ਕਿਸੇ ਵਾਧੂ ਕੌਨਫਿਗਰੇਸ਼ਨ ਦੀ ਲੋੜ ਨਹੀਂ। ਸਿੰਕ ਡੈਮਨ ਆਪਣੇ ਆਪ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਲੱਭ ਲੈਂਦਾ ਹੈ ਭਾਵੇਂ ਉਹ ਹੋਸਟ ਉੱਤੇ `~/.openclaw/` ਵਿੱਚ ਹੋਣ ਜਾਂ ਇੱਕ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ।

### ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry NemoClaw ਨੂੰ ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ ਪਛਾਣਦਾ ਹੈ:

1. **ਬਾਈਨਰੀ ਪਛਾਣ** — `nemoclaw` CLI ਲਈ ਜਾਂਚ ਕਰਦਾ ਹੈ ਅਤੇ ਸੈਂਡਬਾਕਸ ਜਾਣਕਾਰੀ ਲੈਣ ਲਈ `nemoclaw status` ਚਲਾਉਂਦਾ ਹੈ
2. **ਕੰਟੇਨਰ ਪਛਾਣ** — ਚੱਲ ਰਹੇ Docker ਕੰਟੇਨਰਾਂ ਨੂੰ `openshell`, `nemoclaw`, ਜਾਂ `ghcr.io/nvidia/` ਇਮੇਜਾਂ ਲਈ ਸਕੈਨ ਕਰਦਾ ਹੈ, ਫਿਰ ਵਾਲਿਊਮ ਮਾਊਂਟਾਂ ਜਾਂ `docker cp` ਰਾਹੀਂ ਸੈਸ਼ਨ ਪੜ੍ਹਦਾ ਹੈ

NemoClaw ਕੰਟੇਨਰਾਂ ਤੋਂ ਸਿੰਕ ਕੀਤੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ `runtime=nemoclaw` ਅਤੇ `container_id` ਮੈਟਾਡਾਟਾ ਨਾਲ ਟੈਗ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ, ਤਾਂ ਜੋ ਤੁਸੀਂ ਇਹਨਾਂ ਨੂੰ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਸਟੈਂਡਰਡ OpenClaw ਸੈਸ਼ਨਾਂ ਤੋਂ ਵੱਖ ਪਛਾਣ ਸਕੋ।

### ਸਿਫ਼ਾਰਸ਼ੀ ਸੈੱਟਅੱਪ: HOST ਉੱਤੇ ਸਿੰਕ ਡੈਮਨ

ਸਭ ਤੋਂ ਵਧੀਆ ਤਜਰਬੇ ਲਈ, ClawMetry ਦਾ ਸਿੰਕ ਡੈਮਨ **ਹੋਸਟ ਮਸ਼ੀਨ** ਉੱਤੇ ਚਲਾਓ (ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਨਹੀਂ)। ਇਹ NemoClaw ਨੈੱਟਵਰਕ ਨੀਤੀ ਪਾਬੰਦੀਆਂ ਤੋਂ ਬਚਦਾ ਹੈ।

```bash
# ਹੋਸਟ ਉੱਤੇ (ਸੈਂਡਬਾਕਸ ਤੋਂ ਬਾਹਰ)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ਸਿੰਕ ਡੈਮਨ ਕਿਸੇ ਵੀ ਚੱਲ ਰਹੇ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ ਸੈਸ਼ਨ ਆਪਣੇ ਆਪ ਲੱਭ ਲਵੇਗਾ।

### ਵਿਕਲਪਿਕ: ਸਪਸ਼ਟ ਸੈਂਡਬਾਕਸ ਨਾਮ

ਜੇ ਆਪਣੇ ਆਪ ਪਛਾਣ ਕੰਮ ਨਹੀਂ ਕਰਦੀ, ਤਾਂ ClawMetry ਨੂੰ ਸਹੀ ਸੈਂਡਬਾਕਸ ਵੱਲ ਇਸ਼ਾਰਾ ਕਰੋ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਚਲਾਉਣਾ (ਐਡਵਾਂਸਡ)

ਜੇ ਤੁਹਾਨੂੰ ਸਿੰਕ ਡੈਮਨ ਨੂੰ OpenShell ਸੈਂਡਬਾਕਸ ਦੇ **ਅੰਦਰ** ਚਲਾਉਣਾ ਹੀ ਪਵੇ, ਤਾਂ ਆਪਣੀ NemoClaw ਨੈੱਟਵਰਕ ਨੀਤੀ ਵਿੱਚ ਇਹ ਐਗਰੈੱਸ ਨਿਯਮ ਜੋੜੋ ਤਾਂ ਜੋ ਇਹ ClawMetry ਇੰਜੈਸਟ API ਤੱਕ ਪਹੁੰਚ ਸਕੇ:

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

ਸਿੰਕ ਡੈਮਨ ਸਿਰਫ਼ `ingest.clawmetry.com` ਵੱਲ ਆਊਟਬਾਊਂਡ HTTPS ਕਾਲਾਂ ਕਰਦਾ ਹੈ। ਕਿਸੇ ਇਨਬਾਊਂਡ ਪੋਰਟ ਦੀ ਲੋੜ ਨਹੀਂ।

---

## ਕਲਾਊਡ ਡਿਪਲਾਏਮੈਂਟ

SSH ਟਨਲ, ਰਿਵਰਸ ਪ੍ਰੌਕਸੀ, ਅਤੇ Docker ਲਈ **[ਕਲਾਊਡ ਟੈਸਟਿੰਗ ਗਾਈਡ](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ਵੇਖੋ।

## ਟੈਸਟਿੰਗ

ਇਸ ਪ੍ਰੋਜੈਕਟ ਦੀ ਜਾਂਚ BrowserStack ਨਾਲ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ਟੈਲੀਮੈਟਰੀ

ClawMetry ਅਗਿਆਤ ਇੰਸਟਾਲ-ਲਾਈਫਸਾਈਕਲ ਪਿੰਗ
`https://app.clawmetry.com/api/install` ਨੂੰ ਭੇਜਦਾ ਹੈ: ਇੱਕ ਨਵੀਂ ਮਸ਼ੀਨ ਉੱਤੇ ਪਹਿਲੀ ਵਾਰ
`clawmetry` CLI ਚਲਾਉਣ ਉੱਤੇ ਇੱਕ `install` ਪਿੰਗ, ਇੱਕ ਨਵੇਂ ਵਰਜ਼ਨ ਵਿੱਚ ਅੱਪਗ੍ਰੇਡ ਹੋਣ ਤੋਂ ਬਾਅਦ ਪਹਿਲੀ ਰਨ ਉੱਤੇ ਇੱਕ `update` ਪਿੰਗ, ਅਤੇ
ਡੈਸ਼ਬੋਰਡ-ਅੰਦਰੂਨੀ ਓਨਬੋਰਡਿੰਗ ਵਿਕਲਪ ਪੂਰਾ ਕਰਨ ਉੱਤੇ ਇੱਕ `onboarded`
ਪਿੰਗ। ਅਸੀਂ ਇਸਦੀ ਵਰਤੋਂ ਅਸਲ ਇੰਸਟਾਲਾਂ ਗਿਣਨ ਲਈ ਕਰਦੇ ਹਾਂ (ਕੱਚੇ PyPI ਡਾਊਨਲੋਡ ਅੰਕੜੇ ~98% ਮਿਰਰ, CI,
ਅਤੇ ਆਟੋ-ਅੱਪਡੇਟ ਮੁੜ-ਡਾਊਨਲੋਡ ਹੁੰਦੇ ਹਨ) ਅਤੇ ਇਹ ਜਾਣਨ ਲਈ ਕਿ ਅਸਲ ਵਿੱਚ ਕਿਹੜੇ ਏਜੰਟ ਫਰੇਮਵਰਕ ਅਤੇ
ਵਰਜ਼ਨ ਵਰਤੋਂ ਵਿੱਚ ਹਨ।

**ਹਰੇਕ ਵਰਜ਼ਨ ਲਈ ਪ੍ਰਤੀ ਲਾਈਫਸਾਈਕਲ ਈਵੈਂਟ ਵੱਧ ਤੋਂ ਵੱਧ ਇੱਕ POST**, ਜਿਸ ਵਿੱਚ ਸ਼ਾਮਲ ਹੈ:

| ਫੀਲਡ | ਉਦਾਹਰਨ | ਕਿਉਂ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ਵਿੱਚ ਸਟੋਰ ਕੀਤਾ ਬੇਤਰਤੀਬ UUID | ਡੁਪਲੀਕੇਸ਼ਨ ਰੋਕਣ ਲਈ; ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਸਪਸ਼ਟ ਤੌਰ ਉੱਤੇ Cloud ਸਿੰਕ ਨਹੀਂ ਜੋੜਦੇ ਓਦੋਂ ਤੱਕ ਅਗਿਆਤ (ਫਿਰ ਪ੍ਰਮਾਣਿਤ ਡੈਮਨ ਹਾਰਟਬੀਟ ਇਸਨੂੰ ਲੈ ਜਾਂਦਾ ਹੈ, ਇਸ ਇੰਸਟਾਲ ਨੂੰ ਤੁਹਾਡੇ ਖਾਤੇ ਨਾਲ ਜੋੜਦਾ ਹੋਇਆ) |
| `event` | `install` / `update` / `onboarded` | ਨਵਾਂ ਇੰਸਟਾਲ ਬਨਾਮ ਮੌਜੂਦਾ ਦਾ ਅੱਪਗ੍ਰੇਡ |
| `version` | `0.12.167` | ਕਿਹੜੇ ਵਰਜ਼ਨ ਵਰਤੋਂ ਵਿੱਚ ਹਨ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ਪਲੇਟਫਾਰਮ ਸਮਰਥਨ ਤਰਜੀਹਾਂ |
| `python` | `3.11.15` | Python ਵਰਜ਼ਨ ਸਮਰਥਨ ਮੈਟ੍ਰਿਕਸ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ਅੱਗੇ ਕਿਹੜੇ ਏਜੰਟਾਂ ਨਾਲ ਸਾਨੂੰ ਏਕੀਕ੍ਰਿਤ ਹੋਣਾ ਚਾਹੀਦਾ ਹੈ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ਮਨੁੱਖੀ ਇੰਸਟਾਲਾਂ ਨੂੰ CI ਸ਼ੋਰ ਤੋਂ ਵੱਖ ਕਰਨ ਲਈ |

**ਅਸੀਂ ਕੀ ਨਹੀਂ ਭੇਜਦੇ**: IP (ਕਲਾਊਡ ਸਰਵਰ-ਸਾਈਡ ਬੇਨਤੀ ਤੋਂ ਦੇਸ਼ ਕੋਡ
ਕੱਢਦਾ ਹੈ, ਫਿਰ IP ਹਟਾ ਦਿੰਦਾ ਹੈ), ਹੋਸਟਨਾਮ, ਯੂਜ਼ਰਨਾਮ, ਵਰਕਸਪੇਸ
ਪਾਥ, ਫਾਈਲ ਸਮੱਗਰੀ, ਤੁਹਾਡੀ api_key, ਤੁਹਾਡੀ ਈਮੇਲ, ਕੁਝ ਵੀ ਜੋ PII ਜਾਂ
ਵਰਕਸਪੇਸ-ਵਿਸ਼ੇਸ਼ ਹੋਵੇ। ਵਾਇਰ ਪੇਲੋਡ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ਵਿੱਚ ਆਡਿਟ ਕਰਨ ਯੋਗ ਹੈ।

**ਔਪਟ ਆਊਟ** (ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਵੀ ਇੱਕ ਇਸਨੂੰ ਸਥਾਈ ਤੌਰ ਉੱਤੇ ਬੰਦ ਕਰ ਦਿੰਦਾ ਹੈ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ਪ੍ਰਤੀ-ਸ਼ੈੱਲ
export DO_NOT_TRACK=1                          # W3C ਕਰਾਸ-ਟੂਲ ਸਟੈਂਡਰਡ
touch ~/.clawmetry/notelemetry                 # ਸਥਾਈ ਫਾਈਲ ਮਾਰਕਰ
```

ਇੱਥੇ ਕੋਈ ਨੈੱਟਵਰਕ ਅਸਫਲਤਾ ਕਦੇ ਵੀ `clawmetry` ਨੂੰ ਚੱਲਣ ਤੋਂ ਨਹੀਂ ਰੋਕਦੀ, ਪਿੰਗ
3 ਸਕਿੰਟ ਦੇ ਟਾਈਮਆਊਟ ਨਾਲ ਇੱਕ ਡੈਮਨ ਥ੍ਰੈੱਡ ਉੱਤੇ ਫਾਇਰ-ਐਂਡ-ਫਰਗੈੱਟ ਹੈ।

## ਸਟਾਰ ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੰਸ

MIT

---

<p align="center">
  <strong>🦞 ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਹੋਏ ਦੇਖੋ</strong><br>
  <sub>ਬਣਾਇਆ <a href="https://github.com/vivekchand">@vivekchand</a> ਵੱਲੋਂ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ਈਕੋਸਿਸਟਮ ਦਾ ਹਿੱਸਾ</sub>
</p>
