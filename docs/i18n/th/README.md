<!-- i18n-src:9a05336fbdc1 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์ของคุณแบบเรียลไทม์** การสังเกตการณ์แบบเรียลไทม์สำหรับ **14 รันไทม์เอเจนต์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 รันไทม์ แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น ๆ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แล้วก็เสร็จเรียบร้อย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานร่วมกับ 14 รันไทม์เอเจนต์

ClawMetry เริ่มต้นจากการเป็นเครื่องมือสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายไปวัดผล **กองเอเจนต์ทั้งหมดของคุณ** ในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ และ trace จะปรับขอบเขตไปตามรันไทม์นั้นโดยอัตโนมัติ ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดการแบ่งฟรี/เสียเงินที่แน่ชัด ตารางระดับชั้น รูปแบบของ `/api/entitlement` และ CLI `clawmetry license`

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวแบบเรียลไทม์ที่แสดงข้อความไหลผ่านช่องทาง สมอง เครื่องมือ และกลับมา
- **Overview** — การตรวจสอบสถานะ heatmap กิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและค่าใช้จ่าย พร้อมรายละเอียดรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานอยู่ พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานที่ตั้งเวลาไว้ พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์พร้อมรหัสสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **Approvals** — กันการลบแบบทำลายล้าง force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ การเรียกเครือข่าย ไว้หลังการอนุมัติด้วยคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบเรียลไทม์
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้โทเคนและสรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดค่าใช้จ่ายตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ตัวเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด webhook ไปยัง Slack / Discord / PagerDuty / อีเมล
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กันการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่อิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนดำเนินการสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook แบบ PreToolUse ที่หยุดการเรียกใช้เครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่มันจะทำงาน และรอ
การตัดสินใจของคุณ (แตะครั้งเดียวจากโทรศัพท์เมื่อเปิดใช้งาน
[การแจ้งเตือนแบบพุชจากคลาวด์](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกเฉพาะการเรียกใช้เครื่องมือครั้งนั้น เอเจนต์ยังคงรักษาเซสชันไว้ได้และ
ลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์จะข้ามพร้อมต์การอนุญาตของ Claude Code เอง
(เพราะคุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขจะมีค่าใช้จ่ายประมาณ 40ms และ
ตกไปสู่ขั้นตอนการอนุญาตปกติของ Claude Code คุณยังจะได้รับการแจ้งเตือนแบบพุชบนโทรศัพท์เมื่อ Claude Code เอง
กำลังรอคุณอยู่ (การแจ้งเตือน `permission_prompt` / `idle_prompt`)

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
server ถูกเริ่มต้นด้วยการเปิดใช้งาน v2

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

เปิด `http://localhost:5173/v2/` Vite จะพร็อกซีคำขอ `/api` ไปยัง
`http://localhost:8900` ทำให้แอป React สามารถสื่อสารกับ Flask server ในเครื่องได้
โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการสร้างชุดไฟล์ที่ใช้ในแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

ชุดไฟล์สำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์รันไทม์เอเจนต์ AI ได้หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวมี adapter สำหรับอ่านข้อมูลโดยเฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบรวมของ ClawMetry เดมอนจะนำเข้าข้อมูลเหล่านี้ไปยัง DuckDB store + สแนปช็อตคลาวด์ชุดเดียวกัน โดยติดแท็กด้วยรันไทม์นั้น ๆ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบฉบับเต็ม + คู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้พื้นฐานเกี่ยวกับตระกูล OpenClaw

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | Native | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | Beta adapter | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ |
| **NanoClaw** | Beta adapter | SQLite ต่อเซสชัน (`data/v2-sessions`) บทถอดข้อความ + จำนวนข้อความ |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db` บทถอดข้อความ โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ + การคิด การใช้งานโทเคน |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ การใช้งานโทเคน |
| **Cursor** | Beta adapter | SQLite `state.vscdb` บทถอดข้อความแชท/composer โมเดล |
| **Aider** | Beta adapter | `.aider.chat.history.md` ต่อโปรเจกต์ บทถอดข้อความ โมเดล จำนวนโทเคน |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ ยอดรวมโทเคน |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ การใช้งานโทเคน |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db` บทถอดข้อความ โมเดล การเรียกใช้เครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite` การรันเวิร์กโฟลว์ การรันโหนด พรอมต์ AI Agent โมเดล + โทเคนในกรณีที่ n8n บันทึกไว้ |

"Beta adapter" หมายถึง ClawMetry มี reader สำหรับรูปแบบข้อมูลบนดิสก์จริงของรันไทม์นั้น แต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) adapter เป็นแบบอ่านอย่างเดียว แต่ละตัวจะบอกตามจริงว่ารันไทม์นั้นเก็บข้อมูลอะไรไว้จริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตของมุมมองเซสชันไปยังรันไทม์เดียวเพื่อการเจาะลึกที่ชัดเจน

## ติดตามเอเจนต์ SDK ใดก็ได้ — การระบุค่าใช้จ่ายแบบ out-loop

รันไทม์ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **เอเจนต์ที่ใช้งานจริง (production agent)** ของคุณเอง ไม่ว่าจะสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา จะไม่ทำแบบนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงสามารถจับการเรียก LLM ของมัน (ค่าใช้จ่าย โทเคน เวลาแฝง ข้อผิดพลาด) ได้ด้วยการทำ monkey-patch ให้กับ `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่มีชื่อ** ดังนั้นทุกผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดของตัวเองที่ระบุค่าใช้จ่ายได้ในการ์ด **🔌 Out-loop sources** บนหน้า Overview ของแดชบอร์ด แสดงจำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ถ้าไม่ได้ตั้งค่าแหล่งที่มา การเรียกก็ยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะยังคงซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่ adapter ของรันไทม์ป้อนเข้า (DuckDB → สแนปช็อตคลาวด์) ดังนั้นแหล่งที่มาแบบ out-loop จะซิงค์ไปยังแดชบอร์ดคลาวด์เช่นเดียวกับทุกอย่างอื่น โดยเข้ารหัสแบบ end-to-end

## OpenTelemetry — เป็นกลางทางผู้ให้บริการ ส่ง trace ของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** ดังนั้น trace ของเอเจนต์คุณจะไม่ถูกผูกติดกับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน การเรียก LLM เครื่องมือ เอเจนต์ย่อย โทเคน ค่าใช้จ่าย เป็น OTLP/HTTP GenAI spans ไปยัง collector ใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Header สำหรับยืนยันตัวตนและช่วงเวลา poll เป็นตัวแปรสภาพแวดล้อมที่ไม่บังคับ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** — ตัวรับ OTLP ในตัวยอมรับ trace และ metric จากที่อื่นได้ที่ `/v1/traces` และ `/v1/metrics` (ต้อง `pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าและทำงานในเครื่องเป็นหลัก **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมคุณใช้อยู่แล้ว ไม่มีการผูกติด ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การตั้งค่า

คนส่วนใหญ่ไม่จำเป็นต้องตั้งค่าอะไรเลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ cron ของคุณโดยอัตโนมัติ

หากคุณต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมแบบเรียลไทม์สำหรับทุกช่องทาง OpenClaw ที่คุณตั้งค่าไว้ มีเพียงช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` เท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใดก็ได้ใน Flow เพื่อดูมุมมองฟองแชทแบบเรียลไทม์พร้อมจำนวนข้อความขาเข้า/ขาออก

| ช่องทาง | สถานะ | Live Popup | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับกิลด์ + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ workspace + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชันจาก web UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัว NIP-04 แบบกระจายศูนย์ |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และจะแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยตนเอง

## การใช้งานผ่าน Docker

ต้องการรัน ClawMetry ในคอนเทนเนอร์ใช่ไหม ไม่มีปัญหา 🐳

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์คุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry สามารถตรวจจับการตั้งค่าของคุณโดยอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- รันไทม์เอเจนต์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents หรือ n8n (หรือ mounted volume สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบ sandbox

ส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม เดมอนซิงค์จะค้นหาไฟล์เซสชันโดยอัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ได้สองวิธี:

1. **การตรวจจับ binary** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อดึงข้อมูล sandbox
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหา image ที่เป็น `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วยข้อมูลเมตา `runtime=nemoclaw` และ `container_id` ในแดชบอร์ดคลาวด์ เพื่อให้คุณแยกความแตกต่างจากเซสชัน OpenClaw ปกติได้ในทันที

### การตั้งค่าที่แนะนำ: เดมอนซิงค์บน HOST

เพื่อประสบการณ์ที่ดีที่สุด ให้รันเดมอนซิงค์ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายใน sandbox) วิธีนี้จะช่วยหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

เดมอนซิงค์จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ตัวเลือกเสริม: ระบุชื่อ sandbox อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยัง sandbox ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายใน sandbox (ขั้นสูง)

หากคุณจำเป็นต้องรันเดมอนซิงค์ **ภายใน** sandbox ของ OpenShell ให้เพิ่มกฎ egress นี้ในนโยบายเครือข่ายของ NemoClaw เพื่อให้สามารถเข้าถึง ClawMetry ingest API ได้:

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
| `ingest.clawmetry.com` | 443 | HTTPS | จำเป็น (เดมอนซิงค์ → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | จำเป็น (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

เดมอนซิงค์เรียกออกไปยัง `ingest.clawmetry.com` ผ่าน HTTPS เท่านั้น ไม่จำเป็นต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่งสัญญาณ "การรันครั้งแรก" แบบไม่ระบุตัวตนเพียงครั้งเดียวไปยัง
`https://app.clawmetry.com/api/install` เมื่อคุณรัน CLI `clawmetry` เป็นครั้งแรก
บนเครื่องใหม่ เราใช้สิ่งนี้เพื่อนับจำนวนการติดตั้ง (ซึ่งเป็นตัวชี้วัดทางการตลาดเพียงตัวเดียวที่เรามีสำหรับโปรเจกต์โอเพนซอร์ส) และเพื่อเรียนรู้ว่าผู้ใช้ของเราติดตั้งเฟรมเวิร์กเอเจนต์ตัวไหนบ้าง

**หนึ่ง POST ต่อการติดตั้งเท่านั้น** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันการซ้ำ ไม่เชื่อมโยงกับอีเมลหรือ api_key ของคุณ |
| `version` | `0.12.167` | เวอร์ชันไหนบ้างที่ถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | ตารางการรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ตัวไหนที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์ดึงรหัสประเทศจากฝั่งเซิร์ฟเวอร์
จากคำขอ แล้วทิ้ง IP นั้นไป) ชื่อโฮสต์ ชื่อผู้ใช้ เส้นทางพื้นที่ทำงาน
เนื้อหาไฟล์ api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็น PII หรือ
เฉพาะเจาะจงกับพื้นที่ทำงาน payload ที่ส่งสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**การปิดใช้งาน** (เลือกทำวิธีใดวิธีหนึ่งเพื่อปิดใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

หากเกิดข้อผิดพลาดของเครือข่ายตรงนี้ จะไม่มีผลบล็อกการทำงานของ `clawmetry`
เพราะการส่งสัญญาณเป็นแบบ fire-and-forget บน daemon thread ที่มี timeout 3 วินาที

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
  <strong>🦞 ดูความคิดของเอเจนต์ของคุณ</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
