<!-- i18n-src:8252f6b1d31d -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** สังเกตการณ์แบบเรียลไทม์สำหรับ **14 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 runtimes แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จ

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานร่วมกับ 14 agent runtimes

ClawMetry เริ่มต้นจากการเป็นเครื่องมือสังเกตการณ์สำหรับ OpenClaw และตอนนี้วัดผล **กองเอเจนต์ทั้งหมด** ของคุณในแดชบอร์ดเดียว โดยตรวจจับ runtime แต่ละตัวบนเครื่องของคุณโดยอัตโนมัติ

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วน runtime อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับ runtime ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ และการติดตาม (traces) จะปรับขอบเขตไปตาม runtime นั้นทันที ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดการแบ่งฟรี/เสียเงินที่ชัดเจน ตารางระดับสิทธิ์ โครงสร้าง `/api/entitlement` และคำสั่ง CLI `clawmetry license`

## คุณจะได้อะไรบ้าง

- **Flow** — แผนภาพเคลื่อนไหวสดแสดงข้อความที่ไหลผ่านช่องทาง (channels) สมอง (brain) เครื่องมือ (tools) และย้อนกลับมา
- **Overview** — การตรวจสุขภาพระบบ แผนที่ความหนาแน่นกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและค่าใช้จ่ายพร้อมสรุปรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงาน พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานตามกำหนดเวลาพร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์ที่มีรหัสสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **Approvals** — กั้นการลบแบบทำลายล้าง การ force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ และการเรียกเครือข่าย ไว้หลังการอนุมัติด้วยคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์ของเอเจนต์แบบสด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้งานโทเคนและสรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดค่าใช้จ่ายตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด webhook ไปยัง Slack / Discord / PagerDuty / อีเมล
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กั้นการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่อิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนการทำงานสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook แบบ PreToolUse ที่หยุดการเรียกใช้เครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่มันจะทำงาน และรอ
การตัดสินใจของคุณ (แตะครั้งเดียวจากโทรศัพท์เมื่อเปิดใช้งาน
[การแจ้งเตือนแบบ push บนคลาวด์](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธ (deny) จะบล็อกเฉพาะการเรียกใช้เครื่องมือนั้นครั้งเดียว เอเจนต์ยังคงเซสชันไว้และสามารถ
ลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์จะข้ามพรอมต์ขออนุญาตของ Claude Code เอง
(เพราะคุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขใช้เวลาราว ~40ms และ
ตกไปสู่กระบวนการขออนุญาตปกติของ Claude Code นอกจากนี้คุณยังจะได้รับการแจ้งเตือนบนโทรศัพท์เมื่อ
Claude Code เองกำลังรอคุณอยู่ (การแจ้งเตือน `permission_prompt` / `idle_prompt`)

## การติดตั้ง

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

## การพัฒนา v2 Frontend

แอป React v2 อยู่ที่ `frontend/` และให้บริการที่ `/v2` เมื่อ Flask
server ถูกเริ่มด้วยการเปิดใช้งาน v2

ใช้สองเทอร์มินัลระหว่างพัฒนา:

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

เปิด `http://localhost:5173/v2/` Vite จะพร็อกซีคำขอ `/api` ไปยัง
`http://localhost:8900` ทำให้แอป React สามารถสื่อสารกับ Flask server ในเครื่อง
ได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการ build bundle ที่จะแพ็กไปพร้อมกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

Production bundle จะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของ Runtime / Agent

ClawMetry สังเกตการณ์ AI-agent runtime ได้หลายตัว ไม่ใช่แค่ OpenClaw runtime ที่ไม่ใช่ OpenClaw แต่ละตัวมี adapter สำหรับอ่านข้อมูลโดยเฉพาะ ซึ่งแปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบรวมของ ClawMetry แล้ว daemon จะนำเข้าข้อมูลเหล่านี้เข้าสู่ DuckDB store เดียวกันและสแนปช็อตบนคลาวด์ พร้อมติดแท็กด้วย runtime และแท็บ Session replay จะแสดง **ตัวสลับ runtime** เมื่อมีมากกว่าหนึ่ง runtime อยู่ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบฉบับเต็มและคำแนะนำการเพิ่ม runtime และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้เบื้องต้นเกี่ยวกับตระกูล OpenClaw

| Runtime / Agent | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | เนทิฟ | runtime อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | Beta adapter | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) ประวัติแชท โมเดล การเรียกใช้เครื่องมือ |
| **NanoClaw** | Beta adapter | SQLite ต่อเซสชัน (`data/v2-sessions`) ประวัติแชท + จำนวนข้อความ |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db` ประวัติแชท โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ + การคิด การใช้โทเคน |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ การใช้โทเคน |
| **Cursor** | Beta adapter | SQLite `state.vscdb` ประวัติแชท/composer โมเดล |
| **Aider** | Beta adapter | `.aider.chat.history.md` ต่อโปรเจกต์ ประวัติแชท โมเดล จำนวนโทเคน |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ ยอดรวมโทเคน |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ การใช้โทเคน |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db` ประวัติแชท โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite` การรันเวิร์กโฟลว์ การรันโหนด พรอมต์ AI Agent โมเดล + โทเคน ในกรณีที่ n8n บันทึกไว้ |

"Beta adapter" หมายถึง ClawMetry จัดหาตัวอ่านสำหรับรูปแบบไฟล์บนดิสก์จริงของ runtime นั้น ๆ ซึ่งแต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) adapter เป็นแบบอ่านอย่างเดียว และแต่ละตัวจะบอกตามจริงว่า runtime นั้นเก็บข้อมูลอะไรไว้จริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้บันทึกค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลาย runtime ทำงานบนโหนดเดียวกัน ตัวสลับ runtime จะจำกัดขอบเขตมุมมองเซสชันไปยัง runtime เดียวเพื่อการเจาะลึกที่สะอาด

## ติดตามเอเจนต์ SDK ใด ๆ ก็ได้ การระบุค่าใช้จ่ายแบบ out-loop

runtime ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **production agent** ของคุณเอง ไม่ว่าจะเป็นตัวที่คุณสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา จะไม่ทำแบบนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียกใช้ LLM ของมันได้ (ค่าใช้จ่าย โทเคน เวลาแฝง ข้อผิดพลาด) โดยการ monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่มีชื่อ** ดังนั้นทุกผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดของตัวเองที่ระบุค่าใช้จ่ายได้ในการ์ด **🔌 Out-loop sources** ของแดชบอร์ดบนแท็บ Overview ได้แก่ การเรียกใช้ ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งที่มา? การเรียกยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะยังคงซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกันกับที่ runtime adapter ป้อนเข้า (DuckDB → สแนปช็อตบนคลาวด์) ดังนั้น out-loop sources จึงซิงก์ไปยังแดชบอร์ดบนคลาวด์เหมือนกับทุกอย่างอื่น โดยเข้ารหัสแบบ end-to-end

## OpenTelemetry — เป็นกลางต่อผู้ให้บริการ ส่ง traces ของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** ดังนั้น traces ของเอเจนต์คุณจะไม่ถูกผูกติดกับเครื่องมือใดเครื่องมือหนึ่งเลย

**ส่งออก** ทุกเซสชัน ทั้งการเรียกใช้ LLM เครื่องมือ ซับเอเจนต์ โทเคน ค่าใช้จ่าย เป็น OTLP/HTTP GenAI spans ไปยัง collector ใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Header สำหรับยืนยันตัวตนและช่วงเวลาสำรวจ (poll interval) เป็นตัวแปรสภาพแวดล้อมทางเลือก:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** ตัวรับ OTLP ในตัวรับ traces และ metrics จากที่อื่นได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าและทำงานในเครื่องเป็นหลัก **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมคุณใช้อยู่แล้ว ไม่มีการผูกติด ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การตั้งค่า

คนส่วนใหญ่ไม่ต้องตั้งค่าอะไรเลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ cron ของคุณโดยอัตโนมัติ

หากต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทาง (channel) ของ OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใดก็ได้ใน Flow เพื่อดูมุมมองฟองแชทแบบสด พร้อมจำนวนข้อความเข้า/ออก

| ช่องทาง | สถานะ | Popup แบบสด | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Guild + channel |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Workspace + channel |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชันจาก web UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Teams bot plugin |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | กระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และแสดงเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่จำเป็นต้องตั้งค่าด้วยตนเอง

## การใช้งานผ่าน Docker

อยากรัน ClawMetry ในคอนเทนเนอร์ใช่ไหม ไม่มีปัญหา! 🐳

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์คุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry ตรวจจับการตั้งค่าของคุณโดยอัตโนมัติได้

## ข้อกำหนดเบื้องต้น

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- AI agent runtime บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents หรือ n8n (หรือ mounted volume สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ตัวห่อหุ้มความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์ โดยอัตโนมัติ

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม sync daemon จะค้นหาไฟล์เซสชันโดยอัตโนมัติไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับผ่านไบนารี** — ตรวจสอบว่ามี CLI `nemoclaw` หรือไม่ และรัน `nemoclaw status` เพื่อดึงข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับผ่านคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหา image ที่เป็น `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงก์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และข้อมูลเมตา `container_id` ในแดชบอร์ดบนคลาวด์ เพื่อให้คุณสามารถแยกความแตกต่างจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: sync daemon บน HOST

เพื่อประสบการณ์ที่ดีที่สุด ให้รัน sync daemon ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่าย NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ทางเลือกเสริม: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณจำเป็นต้องรัน sync daemon **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎ egress นี้ในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้เข้าถึง ClawMetry ingest API ได้:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

นำไปใช้ด้วย:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### พอร์ตและ endpoint

| Endpoint | พอร์ต | โปรโตคอล | จำเป็นหรือไม่ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (sync daemon → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (dashboard UI ในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

sync daemon เรียก HTTPS ขาออกเฉพาะไปยัง `ingest.clawmetry.com` เท่านั้น ไม่จำเป็นต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบบนคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่ง ping แบบไม่ระบุตัวตนเกี่ยวกับวงจรชีวิตการติดตั้งไปยัง
`https://app.clawmetry.com/api/install`: ping `install` หนึ่งครั้งในการรันคำสั่ง
`clawmetry` CLI ครั้งแรกบนเครื่องใหม่ ping `update` หนึ่งครั้งในการรันครั้งแรก
หลังจากอัปเกรดเป็นเวอร์ชันใหม่ และ ping `onboarded` หนึ่งครั้งเมื่อคุณทำตัวเลือก
onboarding ในแดชบอร์ดเสร็จสิ้น เราใช้ข้อมูลนี้เพื่อนับจำนวนการติดตั้งจริง
(ตัวเลขดาวน์โหลดดิบจาก PyPI ประมาณ 98% มาจาก mirror, CI และการดาวน์โหลดซ้ำจากการอัปเดตอัตโนมัติ)
และเพื่อเรียนรู้ว่า agent framework และเวอร์ชันใดบ้างที่ถูกใช้งานจริงอยู่

**อย่างมากหนึ่ง POST ต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันข้อมูลซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อ Cloud sync อย่างชัดเจน (heartbeat ของ daemon ที่ยืนยันตัวตนแล้วจะแนบข้อมูลนี้ไป เชื่อมโยงการติดตั้งนี้เข้ากับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | ติดตั้งใหม่เทียบกับการอัปเกรดของที่มีอยู่แล้ว |
| `version` | `0.12.167` | เวอร์ชันใดบ้างที่ถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | เมทริกซ์การรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เราควรผสานรวมกับเอเจนต์ตัวใดต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์จริงออกจาก noise ของ CI |

**สิ่งที่เรา *ไม่* ส่ง**: IP (ฝั่งคลาวด์คำนวณรหัสประเทศจากคำขอฝั่งเซิร์ฟเวอร์
แล้วทิ้ง IP ทันที) hostname ชื่อผู้ใช้ พาธของพื้นที่ทำงาน เนื้อหาไฟล์
api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็น PII หรือเฉพาะเจาะจงกับพื้นที่ทำงาน
payload ที่ส่งจริงสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการส่งข้อมูล** (ทำอย่างใดอย่างหนึ่งต่อไปนี้เพื่อปิดถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

หากเครือข่ายล้มเหลวที่ตรงนี้ จะไม่มีทางบล็อกการทำงานของ `clawmetry` เลย
เพราะ ping นี้เป็นแบบ fire-and-forget บน daemon thread ที่มี timeout 3 วินาที

## ประวัติดาว (Star History)

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
  <strong>🦞 ดูความคิดของเอเจนต์คุณ</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
