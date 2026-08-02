<!-- i18n-src:191e9094d7fa -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูการคิดของเอเจนต์ของคุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **14 รันไทม์เอเจนต์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 รันไทม์ แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างโดยอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นั้นก็เสร็จเรียบร้อย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 14 รันไทม์เอเจนต์

ClawMetry เริ่มต้นจากการเป็นระบบสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายมาตรวจวัด **กองเอเจนต์ทั้งหมดของคุณ** ในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ และ trace จะปรับขอบเขตไปตามรันไทม์นั้นโดยอัตโนมัติ ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดการแบ่งฟรี/เสียเงินที่แน่ชัด ตารางระดับสิทธิ์ โครงสร้าง `/api/entitlement` และคำสั่ง CLI `clawmetry license`

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวแบบเรียลไทม์ที่แสดงข้อความไหลผ่านช่องทาง สมอง เครื่องมือ และย้อนกลับมา
- **Overview** — การตรวจสอบสถานะ แผนที่ความร้อนของกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและค่าใช้จ่ายพร้อมรายละเอียดรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานอยู่ พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานตามกำหนดเวลา พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์ที่ระบุสีตามประเภท
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **Approvals** — กั้นการลบแบบทำลายล้าง การ force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ และการเรียกเครือข่าย ไว้หลังการอนุมัติด้วยคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบเรียลไทม์
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — สรุปการใช้โทเคนและเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดค่าใช้จ่ายตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ตัวเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด เว็บฮุกไปยัง Slack / Discord / PagerDuty / อีเมล
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กั้นการเรียกเครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยมือ พร้อมกฎการป้องกันที่รองรับด้วยนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนรันสำหรับ Claude Code** — คำสั่งเดียวติดตั้งฮุก
PreToolUse ที่หยุดการเรียกเครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่จะรัน และรอ
การตัดสินใจของคุณ (แตะเพียงครั้งเดียวจากโทรศัพท์ของคุณเมื่อเปิดใช้งาน
[การแจ้งเตือนแบบ push บนคลาวด์](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกเฉพาะการเรียกเครื่องมือนั้นเพียงครั้งเดียว เอเจนต์ยังคงรักษาเซสชันของตนไว้และสามารถลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์ของคุณจะข้ามพร้อมท์การอนุญาตของ Claude Code เอง (เนื่องจากคุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขจะเสียเวลาเพิ่มเพียง ~40ms และตกไปยังขั้นตอนการอนุญาตปกติของ Claude Code คุณยังจะได้รับการแจ้งเตือนแบบ push บนโทรศัพท์เมื่อ Claude Code เองกำลังรอคุณอยู่ (การแจ้งเตือนประเภท `permission_prompt` / `idle_prompt`)

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

## การพัฒนา Frontend เวอร์ชัน v2

แอป React เวอร์ชัน v2 อยู่ที่ `frontend/` และให้บริการที่ `/v2` เมื่อ
เซิร์ฟเวอร์ Flask ถูกเริ่มต้นโดยเปิดใช้งาน v2

ใช้สองเทอร์มินัลระหว่างการพัฒนา:

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

เปิด `http://localhost:5173/v2/` Vite จะ proxy คำขอ `/api` ไปยัง
`http://localhost:8900` เพื่อให้แอป React สามารถสื่อสารกับเซิร์ฟเวอร์ Flask
บนเครื่องได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการสร้างบันเดิลที่จะแพ็กไปพร้อมกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

บันเดิลสำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์รันไทม์เอเจนต์ AI หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวจะมีตัวอ่านเฉพาะ (adapter) ที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry แดวมอนจะนำเข้าข้อมูลเหล่านี้เข้าสู่ที่เก็บ DuckDB เดียวกันและสแนปช็อตบนคลาวด์ โดยติดแท็กด้วยชื่อรันไทม์ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ในระบบ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบฉบับเต็มพร้อมคู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้พื้นฐานเกี่ยวกับตระกูล OpenClaw

กำลังใช้เครื่องมือความปลอดภัยเอเจนต์ [numbat ของ Perplexity](https://github.com/perplexityai/numbat) อยู่หรือไม่? ClawMetry รองรับการนำเข้าผลการตรวจพบและการตัดสินใจบังคับใช้ของมันได้ทันที ดู [`docs/NUMBAT.md`](docs/NUMBAT.md)

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | เนทีฟ | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | อะแดปเตอร์เบต้า | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) ทรานสคริปต์ โมเดล การเรียกเครื่องมือ |
| **NanoClaw** | อะแดปเตอร์เบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) ทรานสคริปต์ + จำนวนข้อความ |
| **Hermes** | อะแดปเตอร์เบต้า | SQLite `~/.hermes/state.db` ทรานสคริปต์ โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | อะแดปเตอร์เบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ + การคิด การใช้โทเคน |
| **Codex** | อะแดปเตอร์เบต้า | Rollout JSONL `~/.codex/sessions/...` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Cursor** | อะแดปเตอร์เบต้า | SQLite `state.vscdb` ทรานสคริปต์แชท/composer โมเดล |
| **Aider** | อะแดปเตอร์เบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ ทรานสคริปต์ โมเดล จำนวนโทเคน |
| **Goose** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/goose` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ โทเคนรวม |
| **opencode** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/opencode` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | อะแดปเตอร์เบต้า | JSONL `~/.qwen/projects/.../chats` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Pi** | อะแดปเตอร์เบต้า | JSONL `~/.pi/agent/sessions` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | อะแดปเตอร์เบต้า | SQLite `~/.deepagents/.state/sessions.db` ทรานสคริปต์ โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | อะแดปเตอร์เบต้า | SQLite `~/.n8n/database.sqlite` การรันเวิร์กโฟลว์ การรันโหนด พรอมต์ AI Agent โมเดล + โทเคน ในกรณีที่ n8n บันทึกไว้ |
| **Antigravity** | อะแดปเตอร์เบต้า | Brain JSONL ภายใต้ `~/.gemini/<flavor>/brain/` บทสนทนา ขั้นตอนเครื่องมือ การคิด การแบ่งโทเคน Gemini ต่อการสร้าง + ค่าใช้จ่าย การเผาผลาญจากการสร้างพื้นหลัง |

"อะแดปเตอร์เบต้า" หมายถึง ClawMetry มีตัวอ่านสำหรับรูปแบบข้อมูลจริงบนดิสก์ของรันไทม์นั้น แต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) อะแดปเตอร์เป็นแบบอ่านอย่างเดียว และแต่ละตัวจะซื่อสัตย์ต่อสิ่งที่รันไทม์นั้นเก็บไว้จริง (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานอยู่บนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันไปที่รันไทม์เดียวเพื่อการเจาะลึกที่ชัดเจน

## ติดตามเอเจนต์ SDK ใด ๆ ก็ได้ — การระบุค่าใช้จ่ายจากนอกลูป

รันไทม์ข้างต้นทั้งหมดเขียนเซสชันลงดิสก์ แต่ **เอเจนต์การผลิตของคุณเอง** ตัวที่คุณสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา ไม่ได้ทำแบบนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียก LLM ของมันได้ (ค่าใช้จ่าย โทเคน เวลาแฝง ข้อผิดพลาด) ด้วยการ monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่ตั้งชื่อ** เพื่อให้ทุกผลิตภัณฑ์ที่คุณรันปรากฏเป็นบรรทัดของตัวเองที่ระบุค่าใช้จ่ายได้ในการ์ด **🔌 Out-loop sources** บนแท็บ Overview ของแดชบอร์ด แสดงจำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งที่มาไว้? การเรียกก็ยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะยังคงซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่อะแดปเตอร์รันไทม์ป้อนข้อมูลให้ (DuckDB → สแนปช็อตบนคลาวด์) ดังนั้นแหล่งข้อมูลนอกลูปจะซิงค์กับแดชบอร์ดบนคลาวด์เช่นเดียวกับข้อมูลอื่น ๆ ทั้งหมด โดยเข้ารหัสแบบ end-to-end

## OpenTelemetry — ไม่ผูกติดกับผู้ให้บริการรายใด ส่งข้อมูล trace ของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** ดังนั้น trace ของเอเจนต์ของคุณจะไม่ถูกล็อกไว้กับเครื่องมือเดียว

**ส่งออก** ทุกเซสชัน ทั้งการเรียก LLM เครื่องมือ เอเจนต์ย่อย โทเคน ค่าใช้จ่าย ในรูปแบบ OTLP/HTTP GenAI spans ไปยัง collector ใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth header และช่วงเวลาการ poll เป็นตัวแปรสภาพแวดล้อมที่ไม่บังคับ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** — ตัวรับ OTLP ในตัวรองรับ trace และ metric จากที่อื่นได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry แบบไม่ต้องตั้งค่าและเก็บข้อมูลในเครื่องก่อน **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมของคุณใช้อยู่แล้ว ไม่มีการผูกติดผู้ให้บริการ ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การกำหนดค่า

คนส่วนใหญ่ไม่จำเป็นต้องตั้งค่าใด ๆ ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ cron ของคุณโดยอัตโนมัติ

หากต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ดูตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมแบบเรียลไทม์สำหรับทุกช่องทาง OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใด ๆ ใน Flow เพื่อดูมุมมองฟองแชทแบบเรียลไทม์พร้อมจำนวนข้อความขาเข้า/ขาออก

| ช่องทาง | สถานะ | Live Popup | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | การตรวจจับกิลด์ + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | การตรวจจับเวิร์กสเปซ + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชัน UI เว็บในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | DM แบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ผ่าน WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณและแสดงเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยมือ

## การใช้งานผ่าน Docker

ต้องการรัน ClawMetry ในคอนเทนเนอร์ใช่ไหม ไม่มีปัญหา! 🐳

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์ของคุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry สามารถตรวจจับการตั้งค่าของคุณโดยอัตโนมัติได้

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งโดยอัตโนมัติผ่าน pip)
- รันไทม์เอเจนต์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n หรือ Antigravity (หรือ mounted volume สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม แดวมอน sync จะค้นหาไฟล์เซสชันโดยอัตโนมัติไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์ หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อรับข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหาอิมเมจ `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และข้อมูล `container_id` ในแดชบอร์ดบนคลาวด์ เพื่อให้คุณสามารถแยกแยะจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: รันแดวมอน sync บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รันแดวมอน sync ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

แดวมอน sync จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ทางเลือก: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณต้องรันแดวมอน sync **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎ egress นี้ในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้สามารถเข้าถึง API การนำเข้าข้อมูลของ ClawMetry ได้:

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

### พอร์ตและปลายทาง

| ปลายทาง | พอร์ต | โปรโตคอล | จำเป็นหรือไม่ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (แดวมอน sync → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดบนเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

แดวมอน sync จะเรียก HTTPS ขาออกไปยัง `ingest.clawmetry.com` เท่านั้น ไม่จำเป็นต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบบนคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## การเก็บข้อมูลทางไกล (Telemetry)

ClawMetry ส่งการแจ้งเตือนวงจรชีวิตการติดตั้งแบบไม่ระบุตัวตนไปยัง
`https://app.clawmetry.com/api/install`: การแจ้งเตือน `install` หนึ่งครั้งเมื่อ
คุณรัน CLI ของ `clawmetry` บนเครื่องใหม่เป็นครั้งแรก การแจ้งเตือน `update`
หนึ่งครั้งในการรันครั้งแรกหลังอัปเกรดเป็นเวอร์ชันใหม่ และการแจ้งเตือน
`onboarded` หนึ่งครั้งเมื่อคุณทำการเลือกขั้นตอน onboarding ในแดชบอร์ดเสร็จสิ้น
เราใช้ข้อมูลนี้เพื่อนับจำนวนการติดตั้งจริง (ตัวเลขการดาวน์โหลดดิบจาก PyPI นั้น
ประมาณ 98% มาจาก mirror, CI และการดาวน์โหลดซ้ำจากการอัปเดตอัตโนมัติ) และเพื่อ
เรียนรู้ว่าเฟรมเวิร์กเอเจนต์และเวอร์ชันใดที่ถูกใช้งานจริงอยู่

**ส่ง POST อย่างมากที่สุดหนึ่งครั้งต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ซึ่งประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันการนับซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อ Cloud sync อย่างชัดเจน (จากนั้น heartbeat ของแดวมอนที่ผ่านการยืนยันตัวตนจะพกข้อมูลนี้ไป เชื่อมโยงการติดตั้งนี้กับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | การติดตั้งใหม่เทียบกับการอัปเกรดของที่มีอยู่แล้ว |
| `version` | `0.12.167` | เวอร์ชันใดที่ถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | เมทริกซ์การรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ใดที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์จะดึงรหัสประเทศจากฝั่งเซิร์ฟเวอร์จาก
คำขอ แล้วทิ้ง IP ทิ้งไป) ชื่อโฮสต์ ชื่อผู้ใช้ เส้นทางพื้นที่ทำงาน
เนื้อหาไฟล์ api_key ของคุณ อีเมลของคุณ หรือสิ่งใดที่เป็นข้อมูลส่วนบุคคล
หรือเฉพาะพื้นที่ทำงานของคุณ payload ที่ส่งผ่านสายสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการเก็บข้อมูล** (วิธีใดวิธีหนึ่งต่อไปนี้จะปิดใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายที่นี่จะไม่มีทางบล็อกไม่ให้ `clawmetry` ทำงานได้
การแจ้งเตือนนี้เป็นแบบ fire-and-forget บนเธรดของแดวมอนที่มี timeout 3 วินาที

## ประวัติดาว

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## สัญญาอนุญาต

MIT

---

<p align="center">
  <strong>🦞 ดูการคิดของเอเจนต์ของคุณ</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
