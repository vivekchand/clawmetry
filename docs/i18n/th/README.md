<!-- i18n-src:48548997be76 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**มองเห็น AI agent ของคุณคิด** ระบบ observability แบบเรียลไทม์สำหรับ **12 รันไทม์ของ AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 8 รายการ แดชบอร์ดเดียวสำหรับกองยาน agent ทั้งหมดของคุณ

> 🌐 **อ่านในภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นั้นเอง

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## รองรับ 12 รันไทม์ของ agent

ClawMetry เริ่มต้นในฐานะ observability สำหรับ OpenClaw และตอนนี้วัดค่า **กองยาน agent ทั้งหมด** ของคุณในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw และ NemoClaw ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้กับ ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์จากส่วนหัวได้ทุกแท็บ ทั้งต้นทุน, token, เครื่องมือ และ trace จะถูกกรองตามรันไทม์นั้น

## สิ่งที่คุณได้รับ

- **Flow** — แผนภาพอนิเมชันสดแสดงข้อความที่ไหลผ่านช่องทาง, brain, เครื่องมือ และกลับมา
- **Overview** — การตรวจสุขภาพ, แผนที่ความหนาแน่นของกิจกรรม, จำนวน session, ข้อมูลโมเดล
- **Usage** — การติดตาม token และต้นทุน พร้อมสรุปรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — session ของ agent ที่กำลังทำงาน พร้อมโมเดล, token, กิจกรรมล่าสุด
- **Crons** — งานที่กำหนดเวลาพร้อมสถานะ, รอบถัดไป, ระยะเวลา
- **Logs** — การสตรีม log แบบเรียลไทม์พร้อมรหัสสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองสนทนาสำหรับอ่านประวัติ session
- **Alerts** — วงเงินงบประมาณ, ตัวกระตุ้นอัตราข้อผิดพลาด, การตรวจจับ agent ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — ควบคุมการลบที่มีผลรุนแรง, การ force push, การแก้ไขฐานข้อมูล, sudo, การติดตั้งแพ็กเกจ, การเรียกเครือข่าย ด้วยการอนุมัติคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์ agent สด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้ token และสรุป session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดต้นทุนตามโมเดลและ session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เบราว์เซอร์ไฟล์ workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะและ audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — วงเงินงบประมาณ, ตัวกระตุ้นอัตราข้อผิดพลาด, webhooks ไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ควบคุมการเรียกใช้เครื่องมือที่มีความเสี่ยงด้วยการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่สนับสนุนโดยนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ติดตั้ง

**คำสั่งเดียว (แนะนำ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**จากซอร์สโค้ด:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## การพัฒนา Frontend v2

แอป React v2 อยู่ใน `frontend/` และให้บริการที่ `/v2` เมื่อเซิร์ฟเวอร์ Flask ถูกเริ่มต้นโดยเปิดใช้งาน v2

ใช้สอง terminal ระหว่างการพัฒนา:

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

เปิด `http://localhost:5173/v2/` Vite จะ proxy คำร้องขอ `/api` ไปยัง `http://localhost:8900` เพื่อให้แอป React สื่อสารกับเซิร์ฟเวอร์ Flask ในเครื่องได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

สร้าง bundle สำหรับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

bundle สำหรับ production จะถูกเขียนไปยัง `clawmetry/static/v2/dist/`

## ความเข้ากันได้กับรันไทม์ / Agent

ClawMetry ตรวจสอบรันไทม์ของ AI agent หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวมี adapter ตัวอ่านเฉพาะที่แปลรูปแบบ session ดั้งเดิมเป็นรูปร่างที่รวมกันของ ClawMetry daemon จะนำเข้าสู่ DuckDB store เดียวกันและ cloud snapshot โดยมีแท็กรันไทม์กำกับ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรายการ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเต็มและคู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับข้อมูลเบื้องต้นเกี่ยวกับตระกูล OpenClaw

| รันไทม์ / Agent | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | Native | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | Beta adapter | JSONL `providers.Message` แบบแบน (`~/.picoclaw/workspace/sessions`) Transcript, โมเดล, การเรียกใช้เครื่องมือ |
| **NanoClaw** | Beta adapter | SQLite ต่อ session (`data/v2-sessions`) Transcript และจำนวนข้อความ |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db` Transcript, โมเดล, token/ต้นทุน |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl` Transcript, โมเดล, การเรียกใช้เครื่องมือและการคิด, การใช้ token |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...` Transcript, โมเดล, การเรียกใช้เครื่องมือ, การใช้ token |
| **Cursor** | Beta adapter | SQLite `state.vscdb` Transcript แชท/composer, โมเดล |
| **Aider** | Beta adapter | `.aider.chat.history.md` ต่อโปรเจกต์ Transcript, โมเดล, จำนวน token |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose` Transcript, โมเดล, การเรียกใช้เครื่องมือ, รวม token |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode` Transcript, โมเดล, การเรียกใช้เครื่องมือ, token และต้นทุน |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats` Transcript, โมเดล, การเรียกใช้เครื่องมือ, การใช้ token |

"Beta adapter" หมายความว่า ClawMetry มี reader สำหรับรูปแบบบนดิสก์จริงของรันไทม์นั้น แต่ละตัวสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) Adapter เป็นแบบอ่านอย่างเดียว แต่ละตัวระบุอย่างตรงไปตรงมาว่ารันไทม์ของมันจัดเก็บอะไรจริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่เขียนต้นทุน token ลงดิสก์) เมื่อรันไทม์หลายตัวทำงานบนโหนดเดียว ตัวสลับรันไทม์จะกรองมุมมอง session ไปยังตัวเดียวเพื่อการวิเคราะห์เชิงลึกที่ชัดเจน

## ติดตาม SDK agent ใด ๆ ก็ได้ด้วยการระบุต้นทุนแบบ out-loop

รันไทม์ข้างต้นทั้งหมดเขียน session ลงดิสก์ **production agent** ของคุณเอง ที่สร้างบน OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา ไม่ได้ทำเช่นนั้น interceptor แบบ zero-config ของ ClawMetry ยังคงจับการเรียก LLM (ต้นทุน, token, latency, ข้อผิดพลาด) โดยการ monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) ติดแท็กการเรียกแต่ละครั้งด้วย **ชื่อแหล่งที่มา** เพื่อให้ทุกผลิตภัณฑ์ที่คุณรันแสดงขึ้นเป็นบรรทัดแรกระดับ first-class ที่ระบุต้นทุนได้ในการ์ด **🔌 Out-loop sources** บน Overview ของแดชบอร์ด โดยแสดงการเรียก, ผู้ให้บริการ, latency, อัตราข้อผิดพลาดต่อ agent ไม่ได้ตั้งแหล่งที่มา? การเรียกยังคงถูกติดตาม แต่การ์ดจะซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือเลเยอร์ข้อมูลเดียวกับที่ runtime adapter ป้อนข้อมูล (DuckDB ไปยัง cloud snapshot) ดังนั้น out-loop source จะซิงค์กับ cloud dashboard เช่นเดียวกับทุกอย่างอื่น แบบเข้ารหัส E2E

## OpenTelemetry — เป็นกลางต่อผู้ขาย ส่ง trace ของคุณไปที่ใดก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** เพื่อให้ trace ของ agent คุณไม่ถูกผูกติดกับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุก session ทั้งการเรียก LLM, เครื่องมือ, sub-agent, token, ต้นทุน ในรูปแบบ OTLP/HTTP GenAI span ไปยัง collector ใด ๆ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth headers และช่วงเวลาการ poll เป็นตัวแปรสภาพแวดล้อมเสริม:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**รับเข้า** — ตัวรับ OTLP ในตัวรับ trace และ metrics จากอะไรก็ได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการรับเข้า protobuf)

คุณได้รับทั้งแดชบอร์ด ClawMetry แบบ zero-config, local-first **และ** ข้อมูลของคุณใน backend ที่ทีมคุณใช้อยู่แล้ว ไม่มีการผูกติด ไม่ต้องติดตั้ง agent ตัวที่สอง

## การตั้งค่า

ส่วนใหญ่ไม่ต้องตั้งค่าใด ๆ ClawMetry ตรวจจับ workspace, log, session และ cron ของคุณอัตโนมัติ

หากคุณต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทาง OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าจริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนที่ไม่ได้ตั้งค่าจะถูกซ่อนอัตโนมัติ

คลิกโหนดช่องทางใด ๆ ใน Flow เพื่อดูมุมมองฟองสนทนาสดพร้อมจำนวนข้อความขาเข้า/ขาออก

| ช่องทาง | สถานะ | Live Popup | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็ม | ✅ | ข้อความ, สถิติ, รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็ม | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็ม | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็ม | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็ม | ✅ | ตรวจจับ Guild และ channel |
| 🟪 **Slack** | ✅ เต็ม | ✅ | ตรวจจับ Workspace และ channel |
| 🌐 **Webchat** | ✅ เต็ม | ✅ | session UI เว็บในตัว |
| 📡 **IRC** | ✅ เต็ม | ✅ | UI ฟองแบบ terminal |
| 🍏 **BlueBubbles** | ✅ เต็ม | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็ม | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็ม | ✅ | ผ่าน Teams bot plugin |
| 🔷 **Mattermost** | ✅ เต็ม | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็ม | ✅ | แบบกระจาย, รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็ม | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็ม | ✅ | NIP-04 DM แบบกระจาย |
| 🟣 **Twitch** | ✅ เต็ม | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็ม | ✅ | การสมัครสมาชิก WebSocket event |
| 🔵 **Zalo** | ✅ เต็ม | ✅ | Zalo Bot API |

> **ตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณและแสดงเฉพาะช่องทางที่คุณตั้งค่าจริง ไม่ต้องตั้งค่าด้วยตนเอง

## การ Deploy ด้วย Docker

ต้องการรัน ClawMetry ในคอนเทนเนอร์หรือไม่? ไม่มีปัญหา! 🐳

**เริ่มต้นอย่างรวดเร็วด้วย Docker:**

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

**ตัวอย่าง Docker Compose:**

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูลและ log ของ agent (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry ตรวจจับการตั้งค่าของคุณอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8 ขึ้นไป
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- รันไทม์ AI agent บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw หรือ PicoClaw (หรือ volume ที่ mount สำหรับ Docker)
- Linux หรือ macOS

## รองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) อัตโนมัติ ซึ่งเป็น security wrapper ระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รัน agent ภายในคอนเทนเนอร์ OpenShell แบบ sandbox

ในกรณีส่วนใหญ่ไม่ต้องตั้งค่าเพิ่มเติม sync daemon ตรวจจับไฟล์ session อัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw สองวิธี:

1. **การตรวจจับ binary** ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อรับข้อมูล sandbox
2. **การตรวจจับคอนเทนเนอร์** สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานสำหรับอิมเมจ `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่าน session ผ่าน volume mount หรือ `docker cp`

ไฟล์ session ที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกแท็กด้วยข้อมูล `runtime=nemoclaw` และ `container_id` ใน cloud dashboard เพื่อให้แยกออกจาก session OpenClaw มาตรฐานได้ทันที

### การตั้งค่าที่แนะนำ: sync daemon บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รัน sync daemon ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายใน sandbox) วิธีนี้หลีกเลี่ยงข้อจำกัดนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon จะค้นหา session ภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่อัตโนมัติ

### ตัวเลือก: ระบุชื่อ sandbox อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยัง sandbox ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายใน sandbox (ขั้นสูง)

หากคุณต้องรัน sync daemon **ภายใน** OpenShell sandbox ให้เพิ่มกฎ egress นี้ในนโยบายเครือข่าย NemoClaw เพื่อให้เข้าถึง ClawMetry ingest API ได้:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ใช้งานด้วย:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### พอร์ตและ endpoint

| Endpoint | พอร์ต | โปรโตคอล | จำเป็น |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (sync daemon ไปยัง cloud) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นพบ session ในคอนเทนเนอร์ |

sync daemon ทำการเรียก HTTPS ขาออกไปยัง `ingest.clawmetry.com` เท่านั้น ไม่ต้องการพอร์ตขาเข้า

---

## การ Deploy บน Cloud

ดู **[คู่มือทดสอบ Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่ง ping แบบไม่ระบุตัวตนครั้งเดียว "first run" ไปยัง `https://app.clawmetry.com/api/install` ในครั้งแรกที่คุณรัน CLI `clawmetry` บนเครื่องใหม่ เราใช้สิ่งนี้เพื่อนับการติดตั้ง (ตัวชี้วัดการตลาดเดียวที่เรามีสำหรับโปรเจกต์ OSS) และเพื่อเรียนรู้ว่า agent framework ใดที่ผู้ใช้ของเราติดตั้งไว้

**POST เดียวต่อการติดตั้ง** ที่ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID แบบสุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันซ้ำ ไม่เชื่อมกับ email หรือ api_key ของคุณ |
| `version` | `0.12.167` | เวอร์ชันใดที่ใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | เมตริกซ์รองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agent ใดที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งโดยคนจาก CI |

**สิ่งที่เราไม่ส่ง**: IP (cloud คำนวณรหัสประเทศฝั่งเซิร์ฟเวอร์จากคำร้องขอแล้วละทิ้ง IP), hostname, ชื่อผู้ใช้, workspace path, เนื้อหาไฟล์, api_key ของคุณ, email ของคุณ หรือข้อมูลที่ระบุตัวตนหรือเฉพาะ workspace payload ของเครือข่ายตรวจสอบได้ที่ [`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ปิดการใช้งาน** (เลือกวิธีใดวิธีหนึ่งเพื่อปิดการใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

การล้มเหลวของเครือข่ายที่นี่จะไม่บล็อกการรัน `clawmetry` เนื่องจาก ping เป็นแบบ fire-and-forget บน daemon thread พร้อม timeout 3 วินาที

## ประวัติดาว

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ใบอนุญาต

MIT

---

<p align="center">
  <strong>🦞 มองเห็น AI agent ของคุณคิด</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
