<!-- i18n-src:9a05336fbdc1 -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦਾ ਵੇਖੋ।** **14 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 10 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ ਅਤੇ ਤੁਹਾਡਾ ਕੰਮ ਹੋ ਗਿਆ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry ਦੀ ਸ਼ੁਰੂਆਤ OpenClaw ਲਈ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ ਵਜੋਂ ਹੋਈ ਸੀ, ਅਤੇ ਹੁਣ ਇਹ ਤੁਹਾਡੇ **ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ** ਨੂੰ ਇੱਕ ਹੀ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਮੀਟਰ ਕਰਦਾ ਹੈ, ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣਦੇ ਹੋਏ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw ਅਤੇ NemoClaw ਓਪਨ-ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ ਹਨ; ਬਾਕੀ ਰਨਟਾਈਮ ClawMetry Cloud ਜਾਂ ਸੈਲਫ-ਹੋਸਟਡ Pro ਲਾਇਸੈਂਸ ਨਾਲ ਸਰਗਰਮ ਹੋ ਜਾਂਦੇ ਹਨ। ਹੈਡਰ ਤੋਂ ਰਨਟਾਈਮ ਬਦਲੋ ਅਤੇ ਹਰ ਟੈਬ — ਲਾਗਤ, ਟੋਕਨ, ਟੂਲ, ਟਰੇਸ — ਉਸ ਰਨਟਾਈਮ ਲਈ ਮੁੜ-ਸਕੋਪ ਹੋ ਜਾਂਦਾ ਹੈ। ਸਹੀ ਮੁਫ਼ਤ/ਪੇਡ ਵੰਡ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, `/api/entitlement` ਸ਼ਕਲ, ਅਤੇ `clawmetry license` CLI ਲਈ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ਵੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **Flow** — ਚੈਨਲਾਂ, ਬ੍ਰੇਨ, ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘਦੇ ਅਤੇ ਵਾਪਸ ਆਉਂਦੇ ਸੁਨੇਹਿਆਂ ਨੂੰ ਵਿਖਾਉਂਦਾ ਲਾਈਵ ਐਨੀਮੇਟਿਡ ਡਾਇਗ੍ਰਾਮ
- **Overview** — ਹੈਲਥ ਚੈੱਕ, ਗਤੀਵਿਧੀ ਹੀਟਮੈਪ, ਸੈਸ਼ਨ ਗਿਣਤੀ, ਮਾਡਲ ਜਾਣਕਾਰੀ
- **Usage** — ਰੋਜ਼ਾਨਾ/ਹਫ਼ਤਾਵਾਰੀ/ਮਹੀਨਾਵਾਰੀ ਵੰਡ ਨਾਲ ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਟਰੈਕਿੰਗ
- **Sessions** — ਮਾਡਲ, ਟੋਕਨ, ਆਖਰੀ ਗਤੀਵਿਧੀ ਸਮੇਤ ਸਰਗਰਮ ਏਜੰਟ ਸੈਸ਼ਨ
- **Crons** — ਸਥਿਤੀ, ਅਗਲੀ ਰਨ, ਮਿਆਦ ਸਮੇਤ ਤਹਿ-ਸ਼ੁਦਾ ਕੰਮ
- **Logs** — ਰੰਗ-ਕੋਡਿਡ ਰੀਅਲ-ਟਾਈਮ ਲਾਗ ਸਟ੍ਰੀਮਿੰਗ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ਰੋਜ਼ਾਨਾ ਨੋਟਸ ਬ੍ਰਾਊਜ਼ ਕਰੋ
- **Transcripts** — ਸੈਸ਼ਨ ਇਤਿਹਾਸ ਪੜ੍ਹਨ ਲਈ ਚੈਟ-ਬਬਲ UI
- **Alerts** — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, ਏਜੰਟ-ਔਫਲਾਈਨ ਪਛਾਣ; Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਕਰਦਾ ਹੈ
- **Approvals** — ਵਿਨਾਸ਼ਕਾਰੀ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, DB ਬਦਲਾਅ, sudo, ਪੈਕੇਜ ਇੰਸਟਾਲ, ਨੈੱਟਵਰਕ ਕਾਲਾਂ ਨੂੰ ਇੱਕ-ਕਲਿੱਕ ਮਨਜ਼ੂਰੀ ਦੇ ਪਿੱਛੇ ਗੇਟ ਕਰੋ

## ਸਕ੍ਰੀਨਸ਼ਾਟ

### 🧠 Brain — ਲਾਈਵ ਏਜੰਟ ਇਵੈਂਟ ਸਟ੍ਰੀਮ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ਟੋਕਨ ਵਰਤੋਂ ਅਤੇ ਸੈਸ਼ਨ ਸੰਖੇਪ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ਰੀਅਲ-ਟਾਈਮ ਟੂਲ ਕਾਲ ਫੀਡ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਅਨੁਸਾਰ ਲਾਗਤ ਵੰਡ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ਵਰਕਸਪੇਸ ਫਾਈਲ ਬ੍ਰਾਊਜ਼ਰ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ਸਥਿਤੀ ਅਤੇ ਆਡਿਟ ਲਾਗ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ-ਦਰ ਟਰਿੱਗਰ, Slack / Discord / PagerDuty / Email ਲਈ ਵੈੱਬਹੁੱਕ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਹੱਥੀਂ ਮਨਜ਼ੂਰੀ ਦੇ ਪਿੱਛੇ ਗੇਟ ਕਰੋ; ਪਾਲਿਸੀ-ਸਮਰਥਿਤ ਸੁਰੱਖਿਆ ਨਿਯਮ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code ਲਈ ਐਗਜ਼ੀਕਿਊਸ਼ਨ-ਤੋਂ-ਪਹਿਲਾਂ ਬਲੌਕਿੰਗ** — ਇੱਕ ਕਮਾਂਡ ਇੱਕ
PreToolUse ਹੁੱਕ ਇੰਸਟਾਲ ਕਰਦੀ ਹੈ ਜੋ ਮੇਲ ਖਾਂਦੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ *ਚੱਲਣ ਤੋਂ ਪਹਿਲਾਂ* ਰੋਕ ਦਿੰਦੀ ਹੈ ਅਤੇ
ਤੁਹਾਡੇ ਫੈਸਲੇ ਦੀ ਉਡੀਕ ਕਰਦੀ ਹੈ (ਤੁਹਾਡੇ ਫ਼ੋਨ ਤੋਂ ਇੱਕ ਟੈਪ ਵਿੱਚ, ਜੇ
[cloud push notifications](https://app.clawmetry.com/push) ਚਾਲੂ ਹੋਣ):

```bash
clawmetry hooks install     # ~/.claude/settings.json ਲਿਖਦਾ ਹੈ (idempotent)
clawmetry hooks status      # ਕੀ ਜੁੜਿਆ ਹੈ + ਕਿੰਨੀਆਂ ਪਾਲਿਸੀਆਂ ਸਰਗਰਮ ਹਨ
clawmetry hooks uninstall   # ਸਿਰਫ਼ ClawMetry ਦੀਆਂ ਐਂਟਰੀਆਂ ਹਟਾਉਂਦਾ ਹੈ
```

ਇੱਕ ਡੈਨਾਈ ਸਿਰਫ਼ ਉਸ ਇੱਕ ਟੂਲ ਕਾਲ ਨੂੰ ਬਲੌਕ ਕਰਦਾ ਹੈ — ਏਜੰਟ ਆਪਣਾ ਸੈਸ਼ਨ ਰੱਖਦਾ ਹੈ ਅਤੇ
ਕੋਈ ਹੋਰ ਤਰੀਕਾ ਅਜ਼ਮਾ ਸਕਦਾ ਹੈ। ਤੁਹਾਡੇ ਫ਼ੋਨ 'ਤੇ ਮਨਜ਼ੂਰੀ ਦੇਣ ਨਾਲ Claude Code ਦਾ ਆਪਣਾ
ਪਰਮਿਸ਼ਨ ਪ੍ਰੌਂਪਟ ਛੱਡ ਜਾਂਦਾ ਹੈ (ਤੁਸੀਂ ਪਹਿਲਾਂ ਹੀ ਜਵਾਬ ਦੇ ਚੁੱਕੇ ਹੋ)। ਮੇਲ ਨਾ ਖਾਂਦੇ ਟੂਲਾਂ ਦੀ ਲਾਗਤ ~40ms ਹੈ ਅਤੇ
ਉਹ Claude Code ਦੇ ਆਮ ਪਰਮਿਸ਼ਨ ਫਲੋ ਵਿੱਚ ਆ ਜਾਂਦੇ ਹਨ। ਜਦੋਂ Claude Code ਖੁਦ ਤੁਹਾਡੀ ਉਡੀਕ ਕਰ ਰਿਹਾ ਹੋਵੇ
(`permission_prompt` / `idle_prompt` ਨੋਟੀਫਿਕੇਸ਼ਨ) ਤਾਂ ਤੁਹਾਨੂੰ ਫ਼ੋਨ ਪੁਸ਼ ਵੀ ਮਿਲਦਾ ਹੈ।

## ਇੰਸਟਾਲ ਕਰੋ

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

## v2 ਫਰੰਟਐਂਡ ਡਿਵੈਲਪਮੈਂਟ

v2 React ਐਪ `frontend/` ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ ਅਤੇ ਜਦੋਂ Flask
ਸਰਵਰ v2 ਸਮਰੱਥ ਕਰਕੇ ਸ਼ੁਰੂ ਕੀਤਾ ਜਾਂਦਾ ਹੈ ਤਾਂ `/v2` 'ਤੇ ਸਰਵ ਹੁੰਦੀ ਹੈ।

ਡਿਵੈਲਪ ਕਰਦੇ ਸਮੇਂ ਦੋ ਟਰਮੀਨਲ ਵਰਤੋ:

```bash
# ਟਰਮੀਨਲ 1: :8900 'ਤੇ Flask API/ਸਰਵਰ
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ਟਰਮੀਨਲ 2: :5173 'ਤੇ Vite ਡੇਵ ਸਰਵਰ
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ਖੋਲ੍ਹੋ। Vite `/api` ਬੇਨਤੀਆਂ ਨੂੰ
`http://localhost:8900` ਵੱਲ ਪ੍ਰੌਕਸੀ ਕਰਦਾ ਹੈ, ਤਾਂ ਜੋ React ਐਪ ਵਾਧੂ CORS ਸੈੱਟਅੱਪ ਬਿਨਾਂ
ਲੋਕਲ Flask ਸਰਵਰ ਨਾਲ ਗੱਲ ਕਰ ਸਕੇ।

Python ਪੈਕੇਜ ਨਾਲ ਸ਼ਿਪ ਹੋਣ ਵਾਲਾ ਬੰਡਲ ਬਣਾਉਣ ਲਈ:

```bash
cd frontend
npm run build
```

ਪ੍ਰੋਡਕਸ਼ਨ ਬੰਡਲ `clawmetry/static/v2/dist/` ਵਿੱਚ ਲਿਖਿਆ ਜਾਂਦਾ ਹੈ।

## ਰਨਟਾਈਮ / ਏਜੰਟ ਅਨੁਕੂਲਤਾ

ClawMetry ਬਹੁਤ ਸਾਰੇ AI-ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਵੇਖਦਾ ਹੈ, ਸਿਰਫ਼ OpenClaw ਨੂੰ ਨਹੀਂ। ਹਰ ਗੈਰ-OpenClaw ਰਨਟਾਈਮ ਇੱਕ ਸਮਰਪਿਤ ਰੀਡਰ ਅਡੈਪਟਰ ਭੇਜਦਾ ਹੈ ਜੋ ਉਸਦੇ ਮੂਲ ਸੈਸ਼ਨ ਫਾਰਮੈਟ ਨੂੰ ClawMetry ਦੀਆਂ ਇਕਸਾਰ ਸ਼ਕਲਾਂ ਵਿੱਚ ਬਦਲਦਾ ਹੈ; ਡੀਮਨ ਇਹਨਾਂ ਨੂੰ ਉਸੇ DuckDB ਸਟੋਰ + ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ ਵਿੱਚ ਇਨਜੈਸਟ ਕਰਦਾ ਹੈ, ਰਨਟਾਈਮ ਨਾਲ ਟੈਗ ਕੀਤਾ ਹੋਇਆ, ਅਤੇ Session replay ਟੈਬ ਇੱਕ ਤੋਂ ਵੱਧ ਰਨਟਾਈਮ ਮੌਜੂਦ ਹੋਣ 'ਤੇ ਇੱਕ **ਰਨਟਾਈਮ ਸਵਿੱਚਰ** ਵਿਖਾਉਂਦੀ ਹੈ। ਪੂਰੇ ਮੈਟ੍ਰਿਕਸ + ਰਨਟਾਈਮ ਜੋੜਨ ਦੀ ਗਾਈਡ ਲਈ [`docs/compatibility.md`](docs/compatibility.md) ਵੇਖੋ, ਅਤੇ OpenClaw-ਫੈਮਿਲੀ ਪ੍ਰਾਈਮਰ ਲਈ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ਵੇਖੋ।

| ਰਨਟਾਈਮ / ਏਜੰਟ | ਸਥਿਤੀ | ਨੋਟਸ |
|---|---|---|
| **OpenClaw** | ਮੂਲ | ਸੰਦਰਭ ਰਨਟਾਈਮ, ਆਟੋ-ਪਛਾਣਿਆ |
| **PicoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਫਲੈਟ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ। |
| **NanoClaw** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ-ਸੈਸ਼ਨ SQLite (`data/v2-sessions`)। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ + ਸੁਨੇਹਾ ਗਿਣਤੀਆਂ। |
| **Hermes** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.hermes/state.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ/ਲਾਗਤ। |
| **Claude Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.claude/projects/.../<id>.jsonl`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ + ਥਿੰਕਿੰਗ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Codex** | ਬੀਟਾ ਅਡੈਪਟਰ | ਰੋਲਆਊਟ JSONL `~/.codex/sessions/...`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Cursor** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `state.vscdb`। ਚੈਟ/ਕੰਪੋਜ਼ਰ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ। |
| **Aider** | ਬੀਟਾ ਅਡੈਪਟਰ | ਪ੍ਰਤੀ-ਪ੍ਰੋਜੈਕਟ `.aider.chat.history.md`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੋਕਨ ਗਿਣਤੀਆਂ। |
| **Goose** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/goose`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਕੁੱਲ। |
| **opencode** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.local/share/opencode`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Qwen Code** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.qwen/projects/.../chats`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ ਵਰਤੋਂ। |
| **Pi** | ਬੀਟਾ ਅਡੈਪਟਰ | JSONL `~/.pi/agent/sessions`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **Deep Agents** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.deepagents/.state/sessions.db`। ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਮਾਡਲ, ਟੂਲ ਕਾਲਾਂ, ਟੋਕਨ + ਲਾਗਤ। |
| **n8n** | ਬੀਟਾ ਅਡੈਪਟਰ | SQLite `~/.n8n/database.sqlite`। ਵਰਕਫ਼ਲੋ ਐਗਜ਼ੀਕਿਊਸ਼ਨ, ਨੋਡ ਰਨ, AI Agent ਪ੍ਰੌਂਪਟ, ਮਾਡਲ + ਟੋਕਨ ਜਿੱਥੇ n8n ਉਹਨਾਂ ਨੂੰ ਰਿਕਾਰਡ ਕਰਦਾ ਹੈ। |

"ਬੀਟਾ ਅਡੈਪਟਰ" ਦਾ ਮਤਲਬ ਹੈ ਕਿ ClawMetry ਉਸ ਰਨਟਾਈਮ ਦੇ ਅਸਲ ਆਨ-ਡਿਸਕ ਫਾਰਮੈਟ ਲਈ ਇੱਕ ਰੀਡਰ ਭੇਜਦਾ ਹੈ, ਹਰੇਕ ਨੂੰ ਇੱਕ ਅਸਲ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਅਸਲ ਇੰਸਟਾਲ ਦੇ ਵਿਰੁੱਧ ਬਣਾਇਆ + ਤਸਦੀਕ ਕੀਤਾ ਗਿਆ ਹੈ (`tests/fixtures/runtimes/<rt>/` ਵੇਖੋ)। ਅਡੈਪਟਰ ਰੀਡ-ਓਨਲੀ ਹਨ; ਹਰੇਕ ਇਸ ਬਾਰੇ ਇਮਾਨਦਾਰ ਹੈ ਕਿ ਉਸਦਾ ਰਨਟਾਈਮ ਅਸਲ ਵਿੱਚ ਕੀ ਸਟੋਰ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ, PicoClaw/NanoClaw/Cursor ਟੋਕਨ ਲਾਗਤ ਡਿਸਕ 'ਤੇ ਨਹੀਂ ਲਿਖਦੇ)। ਜਦੋਂ ਇੱਕ ਨੋਡ 'ਤੇ ਕਈ ਰਨਟਾਈਮ ਚੱਲਦੇ ਹਨ, ਰਨਟਾਈਮ ਸਵਿੱਚਰ ਇੱਕ ਸਾਫ਼-ਸੁਥਰੀ ਡੀਪ-ਡਾਈਵ ਲਈ ਸੈਸ਼ਨ ਵਿਊ ਨੂੰ ਇੱਕ 'ਤੇ ਸਕੋਪ ਕਰਦਾ ਹੈ।

## ਕਿਸੇ ਵੀ SDK ਏਜੰਟ ਨੂੰ ਟਰੈਕ ਕਰੋ — ਆਊਟ-ਲੂਪ ਲਾਗਤ ਵੰਡ

ਉੱਪਰ ਦੱਸੇ ਸਾਰੇ ਰਨਟਾਈਮ ਸੈਸ਼ਨ ਡਿਸਕ 'ਤੇ ਲਿਖਦੇ ਹਨ। ਤੁਹਾਡਾ ਆਪਣਾ **ਪ੍ਰੋਡਕਸ਼ਨ ਏਜੰਟ** — ਜੋ ਤੁਸੀਂ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, ਜਾਂ ਇੱਕ ਸਧਾਰਨ `httpx` ਲੂਪ 'ਤੇ ਬਣਾਇਆ ਹੈ — ਇਹ ਨਹੀਂ ਲਿਖਦਾ। ClawMetry ਦਾ ਜ਼ੀਰੋ-ਕੌਂਫਿਗ ਇੰਟਰਸੈਪਟਰ `httpx`/`requests` ਨੂੰ ਮੌਂਕੀ-ਪੈਚ ਕਰਕੇ ਵੀ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ (ਲਾਗਤ, ਟੋਕਨ, ਲੇਟੈਂਸੀ, ਗਲਤੀਆਂ) ਨੂੰ ਕੈਪਚਰ ਕਰਦਾ ਹੈ:

```python
import clawmetry.track            # ਇੰਟਰਸੈਪਟਰ ਸਰਗਰਮ ਕਰੋ
clawmetry.track.set_source("support-agent")   # ਇਸ ਪ੍ਰੋਡਕਟ ਦਾ ਨਾਮ ਦਿਓ

# ...ਤੁਹਾਡਾ ਏਜੰਟ ਆਮ ਵਾਂਗ ਚੱਲਦਾ ਹੈ; ਹਰ LLM ਕਾਲ ਹੁਣ ਟਰੈਕ + ਵੰਡੀ ਗਈ ਹੈ।
```

`set_source()` (ਜਾਂ `CLAWMETRY_SOURCE=support-agent` env var) ਹਰ ਕਾਲ ਨੂੰ ਇੱਕ **ਨਾਮ ਵਾਲੇ ਸੋਰਸ** ਨਾਲ ਟੈਗ ਕਰਦਾ ਹੈ, ਤਾਂ ਜੋ ਤੁਹਾਡਾ ਹਰ ਚਲਾਇਆ ਪ੍ਰੋਡਕਟ ਡੈਸ਼ਬੋਰਡ ਦੇ Overview ਦੇ **🔌 Out-loop sources** ਕਾਰਡ ਵਿੱਚ ਆਪਣੀ ਖੁਦ ਦੀ, ਲਾਗਤ-ਵੰਡਣਯੋਗ ਲਾਈਨ ਵਜੋਂ ਦਿਖੇ — ਪ੍ਰਤੀ ਏਜੰਟ ਕਾਲਾਂ, ਪ੍ਰੋਵਾਈਡਰ, ਲੇਟੈਂਸੀ, ਗਲਤੀ ਦਰ। ਕੋਈ ਸੋਰਸ ਸੈੱਟ ਨਹੀਂ ਕੀਤਾ? ਕਾਲਾਂ ਫਿਰ ਵੀ ਟਰੈਕ ਹੁੰਦੀਆਂ ਹਨ; ਕਾਰਡ ਸਿਰਫ਼ ਲੁਕਿਆ ਰਹਿੰਦਾ ਹੈ।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ਇਹ ਉਹੀ ਡਾਟਾ ਲੇਅਰ ਹੈ ਜੋ ਰਨਟਾਈਮ ਅਡੈਪਟਰ ਫੀਡ ਕਰਦੇ ਹਨ (DuckDB → ਕਲਾਊਡ ਸਨੈਪਸ਼ਾਟ), ਇਸ ਲਈ ਆਊਟ-ਲੂਪ ਸੋਰਸ ਬਾਕੀ ਸਭ ਕੁਝ ਵਾਂਗ, E2E-ਇਨਕ੍ਰਿਪਟਿਡ, ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਨਾਲ ਸਿੰਕ ਹੁੰਦੇ ਹਨ।

## OpenTelemetry — ਵੈਂਡਰ-ਨਿਊਟ੍ਰਲ, ਆਪਣੇ ਟਰੇਸ ਕਿਤੇ ਵੀ ਭੇਜੋ

ClawMetry **GenAI ਸਿਮੈਂਟਿਕ ਕਨਵੈਨਸ਼ਨ** ਵਰਤ ਕੇ ਦੋਵੇਂ ਦਿਸ਼ਾਵਾਂ ਵਿੱਚ **OpenTelemetry** ਬੋਲਦਾ ਹੈ, ਤਾਂ ਜੋ ਤੁਹਾਡੇ ਏਜੰਟ ਟਰੇਸ ਕਦੇ ਵੀ ਇੱਕ ਹੀ ਟੂਲ ਵਿੱਚ ਲੌਕ ਨਾ ਹੋਣ।

ਹਰ ਸੈਸ਼ਨ — LLM ਕਾਲਾਂ, ਟੂਲ, ਸਬ-ਏਜੰਟ, ਟੋਕਨ, ਲਾਗਤ — ਨੂੰ ਕਿਸੇ ਵੀ ਕੁਲੈਕਟਰ (Datadog, Grafana, Honeycomb, ਜਾਂ ਤੁਹਾਡਾ ਆਪਣਾ OTel Collector) ਵੱਲ OTLP/HTTP GenAI ਸਪੈਨ ਵਜੋਂ **ਐਕਸਪੋਰਟ** ਕਰੋ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# ਇਸਦੇ ਬਰਾਬਰ:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ਆਥ ਹੈਡਰ ਅਤੇ ਪੋਲ ਇੰਟਰਵਲ ਵਿਕਲਪਿਕ env var ਹਨ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ਵਾਧੂ HTTP ਹੈਡਰ
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ਸਕਿੰਟ (ਮੂਲ 60)
```

**ਇਨਜੈਸਟ** — ਬਿਲਟ-ਇਨ OTLP ਰਿਸੀਵਰ `/v1/traces` ਅਤੇ `/v1/metrics` 'ਤੇ ਕਿਸੇ ਵੀ ਹੋਰ ਸੋਰਸ ਤੋਂ ਟਰੇਸ ਅਤੇ ਮੈਟ੍ਰਿਕਸ ਸਵੀਕਾਰ ਕਰਦਾ ਹੈ (protobuf ਇਨਜੈਸਟ ਲਈ `pip install clawmetry[otel]`)।

ਤੁਹਾਨੂੰ ਜ਼ੀਰੋ-ਕੌਂਫਿਗ, ਲੋਕਲ-ਫਸਟ ClawMetry ਡੈਸ਼ਬੋਰਡ **ਅਤੇ** ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਟੀਮ ਵੱਲੋਂ ਪਹਿਲਾਂ ਤੋਂ ਚਲਾਏ ਜਾ ਰਹੇ ਕਿਸੇ ਵੀ ਬੈਕਐਂਡ ਵਿੱਚ ਮਿਲਦਾ ਹੈ — ਕੋਈ ਲੌਕ-ਇਨ ਨਹੀਂ, ਦੂਜਾ ਏਜੰਟ ਇੰਸਟਾਲ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ।

## ਕੌਂਫਿਗਰੇਸ਼ਨ

ਜ਼ਿਆਦਾਤਰ ਲੋਕਾਂ ਨੂੰ ਕਿਸੇ ਕੌਂਫਿਗ ਦੀ ਲੋੜ ਨਹੀਂ। ClawMetry ਤੁਹਾਡੇ ਵਰਕਸਪੇਸ, ਲੌਗ, ਸੈਸ਼ਨ, ਅਤੇ ਕ੍ਰੌਨ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

ਜੇ ਤੁਹਾਨੂੰ ਕਸਟਮਾਈਜ਼ ਕਰਨ ਦੀ ਲੋੜ ਹੈ:

```bash
clawmetry --port 9000              # ਕਸਟਮ ਪੋਰਟ (ਮੂਲ: 8900)
clawmetry --host 127.0.0.1         # ਸਿਰਫ਼ localhost ਨਾਲ ਬਾਈਂਡ ਕਰੋ
clawmetry --workspace ~/mybot      # ਕਸਟਮ ਵਰਕਸਪੇਸ ਪਾਥ
clawmetry --name "Alice"           # Flow ਵਿਜ਼ੁਅਲਾਈਜ਼ੇਸ਼ਨ ਵਿੱਚ ਤੁਹਾਡਾ ਨਾਮ
```

ਸਾਰੇ ਵਿਕਲਪ: `clawmetry --help`

## ਸਮਰਥਿਤ ਚੈਨਲ

ClawMetry ਤੁਹਾਡੇ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਰ OpenClaw ਚੈਨਲ ਲਈ ਲਾਈਵ ਗਤੀਵਿਧੀ ਵਿਖਾਉਂਦਾ ਹੈ। ਸਿਰਫ਼ ਉਹੀ ਚੈਨਲ ਜੋ ਤੁਹਾਡੇ `openclaw.json` ਵਿੱਚ ਅਸਲ ਵਿੱਚ ਸੈੱਟਅੱਪ ਹਨ Flow ਡਾਇਗ੍ਰਾਮ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ — ਗੈਰ-ਕੌਂਫਿਗਰਡ ਆਪਣੇ ਆਪ ਲੁਕਾ ਦਿੱਤੇ ਜਾਂਦੇ ਹਨ।

Flow ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੈਨਲ ਨੋਡ 'ਤੇ ਕਲਿੱਕ ਕਰੋ ਤਾਂ ਜੋ ਆਉਣ ਵਾਲੇ/ਜਾਣ ਵਾਲੇ ਸੁਨੇਹੇ ਗਿਣਤੀਆਂ ਸਮੇਤ ਲਾਈਵ ਚੈਟ ਬਬਲ ਵਿਊ ਵੇਖ ਸਕੋ।

| ਚੈਨਲ | ਸਥਿਤੀ | ਲਾਈਵ ਪੌਪਅੱਪ | ਨੋਟਸ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ ਪੂਰਾ | ✅ | ਸੁਨੇਹੇ, ਅੰਕੜੇ, 10s ਰਿਫ੍ਰੈਸ਼ |
| 💬 **iMessage** | ✅ ਪੂਰਾ | ✅ | `~/Library/Messages/chat.db` ਸਿੱਧਾ ਪੜ੍ਹਦਾ ਹੈ |
| 💚 **WhatsApp** | ✅ ਪੂਰਾ | ✅ | WhatsApp Web (Baileys) ਰਾਹੀਂ |
| 🔵 **Signal** | ✅ ਪੂਰਾ | ✅ | signal-cli ਰਾਹੀਂ |
| 🟣 **Discord** | ✅ ਪੂਰਾ | ✅ | ਗਿਲਡ + ਚੈਨਲ ਪਛਾਣ |
| 🟪 **Slack** | ✅ ਪੂਰਾ | ✅ | ਵਰਕਸਪੇਸ + ਚੈਨਲ ਪਛਾਣ |
| 🌐 **Webchat** | ✅ ਪੂਰਾ | ✅ | ਬਿਲਟ-ਇਨ ਵੈੱਬ UI ਸੈਸ਼ਨ |
| 📡 **IRC** | ✅ ਪੂਰਾ | ✅ | ਟਰਮੀਨਲ-ਸਟਾਈਲ ਬਬਲ UI |
| 🍏 **BlueBubbles** | ✅ ਪੂਰਾ | ✅ | BlueBubbles REST API ਰਾਹੀਂ iMessage |
| 🔵 **Google Chat** | ✅ ਪੂਰਾ | ✅ | Chat API ਵੈੱਬਹੁੱਕ ਰਾਹੀਂ |
| 🟣 **MS Teams** | ✅ ਪੂਰਾ | ✅ | Teams ਬੌਟ ਪਲੱਗਇਨ ਰਾਹੀਂ |
| 🔷 **Mattermost** | ✅ ਪੂਰਾ | ✅ | ਸੈਲਫ-ਹੋਸਟਡ ਟੀਮ ਚੈਟ |
| 🟩 **Matrix** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ, E2EE ਸਮਰਥਨ |
| 🟢 **LINE** | ✅ ਪੂਰਾ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ ਪੂਰਾ | ✅ | ਵਿਕੇਂਦਰੀਕ੍ਰਿਤ NIP-04 DM |
| 🟣 **Twitch** | ✅ ਪੂਰਾ | ✅ | IRC ਕਨੈਕਸ਼ਨ ਰਾਹੀਂ ਚੈਟ |
| 🔷 **Feishu/Lark** | ✅ ਪੂਰਾ | ✅ | WebSocket ਇਵੈਂਟ ਸਬਸਕ੍ਰਿਪਸ਼ਨ |
| 🔵 **Zalo** | ✅ ਪੂਰਾ | ✅ | Zalo Bot API |

> **ਆਟੋ-ਪਛਾਣ:** ClawMetry ਤੁਹਾਡਾ `~/.openclaw/openclaw.json` ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਉਹੀ ਚੈਨਲ ਰੈਂਡਰ ਕਰਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਅਸਲ ਵਿੱਚ ਕੌਂਫਿਗਰ ਕੀਤੇ ਹਨ। ਕੋਈ ਹੱਥੀਂ ਸੈੱਟਅੱਪ ਲੋੜੀਂਦਾ ਨਹੀਂ।

## Docker ਡਿਪਲਾਏਮੈਂਟ

ClawMetry ਨੂੰ ਕੰਟੇਨਰ ਵਿੱਚ ਚਲਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ? ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ! 🐳

**Docker ਨਾਲ ਤੁਰੰਤ ਸ਼ੁਰੂਆਤ:**

```bash
# ਇਮੇਜ ਬਣਾਓ
docker build -t clawmetry .

# ਮੂਲ ਸੈਟਿੰਗਾਂ ਨਾਲ ਚਲਾਓ
docker run -p 8900:8900 clawmetry

# ਜਾਂ ਆਪਣੇ ਏਜੰਟ ਦੀ ਡਾਟਾ ਡਾਇਰੈਕਟਰੀ ਮਾਊਂਟ ਕਰੋ (ਵਿਖਾਇਆ: OpenClaw ਦਾ ~/.openclaw)
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

> **ਨੋਟ:** Docker ਵਿੱਚ ਚਲਾਉਂਦੇ ਸਮੇਂ, ਆਪਣੇ ਏਜੰਟ ਦੀਆਂ ਡਾਟਾ + ਲੌਗ ਡਾਇਰੈਕਟਰੀਆਂ (ਜਿਵੇਂ, `~/.openclaw`, `~/.claude`, `~/.codex`) ਮਾਊਂਟ ਕਰੋ ਤਾਂ ਜੋ ClawMetry ਤੁਹਾਡੇ ਸੈੱਟਅੱਪ ਨੂੰ ਆਪਣੇ ਆਪ ਪਛਾਣ ਸਕੇ।

## ਲੋੜਾਂ

- Python 3.8+
- Flask (pip ਰਾਹੀਂ ਆਪਣੇ ਆਪ ਇੰਸਟਾਲ ਹੋ ਜਾਂਦਾ ਹੈ)
- ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ AI ਏਜੰਟ ਰਨਟਾਈਮ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, ਜਾਂ n8n (ਜਾਂ Docker ਲਈ ਮਾਊਂਟਡ ਵੌਲਿਊਮ)
- Linux ਜਾਂ macOS

## NemoClaw / OpenShell ਸਮਰਥਨ

ClawMetry ਆਪਣੇ ਆਪ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ਨੂੰ ਪਛਾਣਦਾ ਹੈ — NVIDIA ਦਾ ਐਂਟਰਪ੍ਰਾਈਜ਼ ਸੁਰੱਖਿਆ ਰੈਪਰ OpenClaw ਲਈ ਜੋ ਏਜੰਟਾਂ ਨੂੰ ਸੈਂਡਬਾਕਸਡ OpenShell ਕੰਟੇਨਰਾਂ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ।

ਜ਼ਿਆਦਾਤਰ ਮਾਮਲਿਆਂ ਵਿੱਚ ਵਾਧੂ ਕੌਂਫਿਗਰੇਸ਼ਨ ਦੀ ਲੋੜ ਨਹੀਂ। ਸਿੰਕ ਡੀਮਨ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਆਪਣੇ ਆਪ ਲੱਭਦਾ ਹੈ ਭਾਵੇਂ ਉਹ ਹੋਸਟ 'ਤੇ `~/.openclaw/` ਵਿੱਚ ਹੋਣ ਜਾਂ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ।

### ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ

ClawMetry NemoClaw ਨੂੰ ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ ਪਛਾਣਦਾ ਹੈ:

1. **ਬਾਈਨਰੀ ਪਛਾਣ** — `nemoclaw` CLI ਲਈ ਚੈੱਕ ਕਰਦਾ ਹੈ ਅਤੇ ਸੈਂਡਬਾਕਸ ਜਾਣਕਾਰੀ ਲੈਣ ਲਈ `nemoclaw status` ਚਲਾਉਂਦਾ ਹੈ
2. **ਕੰਟੇਨਰ ਪਛਾਣ** — ਚੱਲ ਰਹੇ Docker ਕੰਟੇਨਰਾਂ ਨੂੰ `openshell`, `nemoclaw`, ਜਾਂ `ghcr.io/nvidia/` ਇਮੇਜਾਂ ਲਈ ਸਕੈਨ ਕਰਦਾ ਹੈ, ਫਿਰ ਵੌਲਿਊਮ ਮਾਊਂਟ ਜਾਂ `docker cp` ਰਾਹੀਂ ਸੈਸ਼ਨ ਪੜ੍ਹਦਾ ਹੈ

NemoClaw ਕੰਟੇਨਰਾਂ ਤੋਂ ਸਿੰਕ ਕੀਤੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਕਲਾਊਡ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ `runtime=nemoclaw` ਅਤੇ `container_id` ਮੈਟਾਡਾਟਾ ਨਾਲ ਟੈਗ ਕੀਤਾ ਜਾਂਦਾ ਹੈ, ਤਾਂ ਜੋ ਤੁਸੀਂ ਇਹਨਾਂ ਨੂੰ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਮਿਆਰੀ OpenClaw ਸੈਸ਼ਨਾਂ ਤੋਂ ਵੱਖ ਦੱਸ ਸਕੋ।

### ਸਿਫ਼ਾਰਸ਼ੀ ਸੈੱਟਅੱਪ: HOST 'ਤੇ ਸਿੰਕ ਡੀਮਨ

ਸਭ ਤੋਂ ਵਧੀਆ ਅਨੁਭਵ ਲਈ, ClawMetry ਦਾ ਸਿੰਕ ਡੀਮਨ **ਹੋਸਟ ਮਸ਼ੀਨ** 'ਤੇ ਚਲਾਓ (ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਨਹੀਂ)। ਇਹ NemoClaw ਦੀਆਂ ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਪਾਬੰਦੀਆਂ ਤੋਂ ਬਚਾਉਂਦਾ ਹੈ।

```bash
# ਹੋਸਟ 'ਤੇ (ਸੈਂਡਬਾਕਸ ਤੋਂ ਬਾਹਰ)
pip install clawmetry
clawmetry connect
clawmetry sync
```

ਸਿੰਕ ਡੀਮਨ ਕਿਸੇ ਵੀ ਚੱਲ ਰਹੇ OpenShell ਕੰਟੇਨਰ ਦੇ ਅੰਦਰ ਸੈਸ਼ਨਾਂ ਨੂੰ ਆਪਣੇ ਆਪ ਲੱਭ ਲਵੇਗਾ।

### ਵਿਕਲਪਿਕ: ਸਪੱਸ਼ਟ ਸੈਂਡਬਾਕਸ ਨਾਮ

ਜੇ ਆਟੋ-ਪਛਾਣ ਕੰਮ ਨਹੀਂ ਕਰਦੀ, ClawMetry ਨੂੰ ਸਹੀ ਸੈਂਡਬਾਕਸ ਵੱਲ ਇਸ਼ਾਰਾ ਕਰੋ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ ਚਲਾਉਣਾ (ਐਡਵਾਂਸਡ)

ਜੇ ਤੁਹਾਨੂੰ ਸਿੰਕ ਡੀਮਨ **OpenShell ਸੈਂਡਬਾਕਸ ਦੇ ਅੰਦਰ** ਚਲਾਉਣਾ ਹੀ ਪਵੇ, ਤਾਂ ਆਪਣੀ NemoClaw ਨੈੱਟਵਰਕ ਪਾਲਿਸੀ ਵਿੱਚ ਇਹ ਈਗ੍ਰੈਸ ਨਿਯਮ ਜੋੜੋ ਤਾਂ ਜੋ ਇਹ ClawMetry ਇਨਜੈਸਟ API ਤੱਕ ਪਹੁੰਚ ਸਕੇ:

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
| `ingest.clawmetry.com` | 443 | HTTPS | ਹਾਂ (ਸਿੰਕ ਡੀਮਨ → ਕਲਾਊਡ) |
| `localhost:8900` | 8900 | HTTP | ਹਾਂ (ਲੋਕਲ ਡੈਸ਼ਬੋਰਡ UI) |
| Docker ਸੌਕਟ (`/var/run/docker.sock`) | — | Unix ਸੌਕਟ | ਕੰਟੇਨਰ ਸੈਸ਼ਨ ਖੋਜ ਲਈ |

ਸਿੰਕ ਡੀਮਨ ਸਿਰਫ਼ `ingest.clawmetry.com` ਵੱਲ ਆਊਟਬਾਊਂਡ HTTPS ਕਾਲਾਂ ਕਰਦਾ ਹੈ। ਕੋਈ ਇਨਬਾਊਂਡ ਪੋਰਟ ਲੋੜੀਂਦੀ ਨਹੀਂ।

---

## ਕਲਾਊਡ ਡਿਪਲਾਏਮੈਂਟ

SSH ਟਨਲ, ਰਿਵਰਸ ਪ੍ਰੌਕਸੀ, ਅਤੇ Docker ਲਈ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ਵੇਖੋ।

## ਟੈਸਟਿੰਗ

ਇਹ ਪ੍ਰੋਜੈਕਟ BrowserStack ਨਾਲ ਟੈਸਟ ਕੀਤਾ ਗਿਆ ਹੈ।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ਟੈਲੀਮੈਟਰੀ

ClawMetry ਇੱਕ ਵਾਰ ਗੁਮਨਾਮ "ਪਹਿਲੀ ਰਨ" ਪਿੰਗ
`https://app.clawmetry.com/api/install` ਨੂੰ ਭੇਜਦਾ ਹੈ ਜਦੋਂ ਤੁਸੀਂ ਇੱਕ ਨਵੀਂ ਮਸ਼ੀਨ 'ਤੇ ਪਹਿਲੀ ਵਾਰ
`clawmetry` CLI ਚਲਾਉਂਦੇ ਹੋ। ਅਸੀਂ ਇਸਦੀ ਵਰਤੋਂ ਇੰਸਟਾਲਾਂ ਗਿਣਨ (OSS ਪ੍ਰੋਜੈਕਟ ਲਈ ਸਾਡਾ
ਇੱਕੋ-ਇੱਕ ਮਾਰਕੀਟਿੰਗ ਮੈਟ੍ਰਿਕ) ਅਤੇ ਇਹ ਜਾਣਨ ਲਈ ਕਰਦੇ ਹਾਂ ਕਿ ਸਾਡੇ ਯੂਜ਼ਰਾਂ ਨੇ ਕਿਹੜੇ
ਏਜੰਟ ਫਰੇਮਵਰਕ ਇੰਸਟਾਲ ਕੀਤੇ ਹਨ।

**ਪ੍ਰਤੀ ਇੰਸਟਾਲ ਬਿਲਕੁਲ ਇੱਕ POST**, ਜਿਸ ਵਿੱਚ ਸ਼ਾਮਲ ਹੈ:

| ਫੀਲਡ | ਉਦਾਹਰਨ | ਕਿਉਂ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` 'ਤੇ ਸਟੋਰ ਕੀਤਾ ਰੈਂਡਮ UUID | ਡੁਪਲੀਕੇਟ ਹਟਾਉਣ ਲਈ; ਤੁਹਾਡੇ ਈਮੇਲ ਜਾਂ api_key ਨਾਲ ਜੁੜਿਆ ਨਹੀਂ |
| `version` | `0.12.167` | ਦੁਨੀਆਂ ਵਿੱਚ ਕਿਹੜੇ ਵਰਜ਼ਨ ਹਨ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ਪਲੇਟਫਾਰਮ ਸਮਰਥਨ ਤਰਜੀਹਾਂ |
| `python` | `3.11.15` | Python ਵਰਜ਼ਨ ਸਮਰਥਨ ਮੈਟ੍ਰਿਕਸ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ਸਾਨੂੰ ਅੱਗੇ ਕਿਹੜੇ ਏਜੰਟਾਂ ਨਾਲ ਏਕੀਕ੍ਰਿਤ ਹੋਣਾ ਚਾਹੀਦਾ ਹੈ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ਮਨੁੱਖੀ ਇੰਸਟਾਲਾਂ ਨੂੰ CI ਸ਼ੋਰ ਤੋਂ ਵੱਖ ਕਰਨ ਲਈ |

**ਅਸੀਂ ਕੀ ਨਹੀਂ ਭੇਜਦੇ**: IP (ਕਲਾਊਡ ਬੇਨਤੀ ਤੋਂ ਸਰਵਰ-ਸਾਈਡ ਦੇਸ਼ ਕੋਡ
ਕੱਢਦਾ ਹੈ, ਫਿਰ IP ਹਟਾ ਦਿੰਦਾ ਹੈ), ਹੋਸਟਨੇਮ, ਯੂਜ਼ਰਨੇਮ, ਵਰਕਸਪੇਸ
ਪਾਥ, ਫਾਈਲ ਸਮੱਗਰੀ, ਤੁਹਾਡੀ api_key, ਤੁਹਾਡਾ ਈਮੇਲ, ਕੁਝ ਵੀ PII ਜਾਂ
ਵਰਕਸਪੇਸ-ਵਿਸ਼ੇਸ਼। ਵਾਇਰ ਪੇਲੋਡ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ਵਿੱਚ ਆਡਿਟ ਕਰਨ ਯੋਗ ਹੈ।

**ਔਪਟ ਆਊਟ** (ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਵੀ ਇੱਕ ਇਸਨੂੰ ਸਥਾਈ ਤੌਰ 'ਤੇ ਬੰਦ ਕਰ ਦਿੰਦਾ ਹੈ):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ਪ੍ਰਤੀ-ਸ਼ੈੱਲ
export DO_NOT_TRACK=1                          # W3C ਕ੍ਰਾਸ-ਟੂਲ ਸਟੈਂਡਰਡ
touch ~/.clawmetry/notelemetry                 # ਸਥਾਈ ਫਾਈਲ ਮਾਰਕਰ
```

ਇੱਥੇ ਨੈੱਟਵਰਕ ਅਸਫਲਤਾ ਕਦੇ ਵੀ `clawmetry` ਨੂੰ ਚੱਲਣ ਤੋਂ ਨਹੀਂ ਰੋਕਦੀ — ਪਿੰਗ
3s ਟਾਈਮਆਊਟ ਨਾਲ ਇੱਕ ਡੀਮਨ ਥ੍ਰੈੱਡ 'ਤੇ ਫਾਇਰ-ਐਂਡ-ਫਾਰਗੈੱਟ ਹੈ।

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
  <strong>🦞 ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦਾ ਵੇਖੋ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ਈਕੋਸਿਸਟਮ ਦਾ ਹਿੱਸਾ</sub>
</p>
