<!-- i18n-src:bab48eec552f -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **เอเจนต์ AI 14 รันไทม์**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 รันไทม์ แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าใดๆ ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จ

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 14 รันไทม์เอเจนต์

ClawMetry เริ่มต้นจากการเป็นระบบสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายมาวัดผล **กองเอเจนต์ทั้งหมด** ของคุณในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่นๆ จะใช้งานได้เมื่อมี ClawMetry Cloud หรือไลเซนส์ Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ไม่ว่าจะเป็นต้นทุน โทเคน เครื่องมือ หรือ traces จะปรับขอบเขตไปตามรันไทม์นั้นให้เอง ดูรายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอน ตารางระดับชั้น รูปแบบ `/api/entitlement` และ CLI `clawmetry license` ได้ที่ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวสดแสดงข้อความที่ไหลผ่านช่องทาง สมอง เครื่องมือ และย้อนกลับ
- **Overview** — การตรวจสอบสุขภาพ แผนที่ความร้อนของกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและต้นทุน แยกตามรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่ใช้งานอยู่ พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานตามกำหนดการ พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์ที่มีสีแยกประเภท
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — กั้นการลบแบบทำลายล้าง การ force push การแก้ไขฐานข้อมูล sudo การติดตั้งแพ็กเกจ การเรียกเครือข่าย ไว้หลังการอนุมัติแบบคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์ของเอเจนต์แบบสด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้โทเคนและสรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดต้นทุนแยกตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ท่าทีความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด webhook ไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กั้นการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่อ้างอิงนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนการทำงานสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook PreToolUse ที่หยุดการเรียกใช้เครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่มันจะทำงาน และรอ
การตัดสินใจของคุณ (แตะเดียวจากโทรศัพท์เมื่อเปิดใช้
[การแจ้งเตือนพุชบนคลาวด์](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกเฉพาะการเรียกใช้เครื่องมือครั้งนั้นเท่านั้น เอเจนต์ยังคงเซสชันไว้และสามารถ
ลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์จะข้ามพรอมต์การอนุญาตของ Claude Code เอง
(เพราะคุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขเสียเวลาเพิ่มเพียงประมาณ 40ms และ
ตกลงไปสู่ขั้นตอนการอนุญาตปกติของ Claude Code คุณยังจะได้รับการแจ้งเตือนพุชบนโทรศัพท์เมื่อ Claude Code เอง
กำลังรอคุณอยู่ (การแจ้งเตือน `permission_prompt` / `idle_prompt`)

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

แอป React v2 อยู่ที่ `frontend/` และให้บริการที่ `/v2` เมื่อ
เซิร์ฟเวอร์ Flask ถูกเริ่มต้นด้วยการเปิดใช้ v2

ใช้เทอร์มินัลสองหน้าต่างระหว่างการพัฒนา:

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
`http://localhost:8900` เพื่อให้แอป React สามารถสื่อสารกับเซิร์ฟเวอร์ Flask ในเครื่อง
ได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการสร้างบันเดิลที่จะรวมไปกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

บันเดิลที่ใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์รันไทม์เอเจนต์ AI หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวมีตัวปรับข้อมูล (reader adapter) เฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry เดมอนจะนำเข้าข้อมูลเหล่านี้ลงในสโตร์ DuckDB เดียวกัน + สแนปช็อตบนคลาวด์ โดยติดแท็กด้วยรันไทม์นั้นๆ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดูตารางเปรียบเทียบทั้งหมด + คู่มือการเพิ่มรันไทม์ได้ที่ [`docs/compatibility.md`](docs/compatibility.md) และดูข้อมูลเบื้องต้นเกี่ยวกับตระกูล OpenClaw ได้ที่ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | Native | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | Beta adapter | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) Transcripts, โมเดล, การเรียกใช้เครื่องมือ |
| **NanoClaw** | Beta adapter | SQLite ต่อเซสชัน (`data/v2-sessions`) Transcripts + จำนวนข้อความ |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db` Transcripts, โมเดล, โทเคน/ต้นทุน |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl` Transcripts, โมเดล, การเรียกใช้เครื่องมือ + การคิด, การใช้โทเคน |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, การใช้โทเคน |
| **Cursor** | Beta adapter | SQLite `state.vscdb` Transcripts การแชท/composer, โมเดล |
| **Aider** | Beta adapter | `.aider.chat.history.md` ต่อโปรเจกต์ Transcripts, โมเดล, จำนวนโทเคน |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, ยอดรวมโทเคน |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, โทเคน + ต้นทุน |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, การใช้โทเคน |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, โทเคน + ต้นทุน |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db` Transcripts, โมเดล, การเรียกใช้เครื่องมือ, โทเคน + ต้นทุน |

"Beta adapter" หมายความว่า ClawMetry มีตัวอ่านสำหรับรูปแบบข้อมูลจริงบนดิสก์ของรันไทม์นั้น แต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) ตัวปรับข้อมูลเป็นแบบอ่านอย่างเดียว แต่ละตัวจะซื่อสัตย์ต่อสิ่งที่รันไทม์นั้นเก็บไว้จริง (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนต้นทุนโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันไปที่ตัวเดียวเพื่อการเจาะลึกที่สะอาดตา

## ติดตามเอเจนต์ SDK ใดก็ได้ — การระบุต้นทุนแบบ out-loop

รันไทม์ข้างต้นทั้งหมดเขียนเซสชันลงดิสก์ แต่ **เอเจนต์การผลิต** ของคุณเอง ไม่ว่าจะสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูปแบบ `httpx` ธรรมดา ไม่ทำเช่นนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียกใช้ LLM ของมันได้ (ต้นทุน โทเคน เวลาแฝง ข้อผิดพลาด) ด้วยการ monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่ตั้งชื่อไว้** ทำให้ทุกผลิตภัณฑ์ที่คุณรันปรากฏเป็นบรรทัดข้อมูลชั้นหนึ่งที่ระบุต้นทุนได้ ในการ์ด **🔌 Out-loop sources** บนแท็บ Overview ของแดชบอร์ด ไม่ว่าจะเป็นจำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งที่มาไว้? การเรียกยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะยังคงซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่ตัวปรับข้อมูลรันไทม์ป้อนเข้า (DuckDB → สแนปช็อตบนคลาวด์) ดังนั้นแหล่งที่มาแบบ out-loop จะซิงค์กับแดชบอร์ดบนคลาวด์เช่นเดียวกับข้อมูลอื่นๆ ทั้งหมด แบบเข้ารหัสตั้งแต่ต้นทางถึงปลายทาง

## OpenTelemetry — เป็นกลางต่อผู้ให้บริการ ส่ง traces ของคุณไปที่ไหนก็ได้

ClawMetry สื่อสารด้วย **OpenTelemetry** ได้ทั้งสองทิศทาง โดยใช้ **ข้อตกลงความหมาย GenAI** ดังนั้น traces ของเอเจนต์คุณจะไม่ถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน ไม่ว่าจะเป็นการเรียก LLM เครื่องมือ เอเจนต์ย่อย โทเคน ต้นทุน เป็น OTLP/HTTP GenAI spans ไปยังตัวรวบรวมใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ส่วนหัวการยืนยันตัวตนและช่วงเวลาการโพลเป็นตัวแปรสภาพแวดล้อมเสริม:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** ตัวรับ OTLP ในตัวรับ traces และ metrics จากที่อื่นๆ ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าและทำงานในเครื่องเป็นหลัก **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมของคุณใช้อยู่แล้ว ไม่มีการล็อกอิน ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การตั้งค่า

คนส่วนใหญ่ไม่จำเป็นต้องตั้งค่าใดๆ ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ crons ของคุณโดยอัตโนมัติ

หากคุณต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทางของ OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใดๆ ใน Flow เพื่อดูมุมมองฟองแชทสดพร้อมจำนวนข้อความเข้า/ออก

| ช่องทาง | สถานะ | ป็อปอัปสด | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Guild + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Workspace + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชัน UI เว็บในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ผ่าน WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และแสดงเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่จำเป็นต้องตั้งค่าด้วยตนเอง

## การใช้งานผ่าน Docker

ต้องการรัน ClawMetry ในคอนเทนเนอร์ไหม ไม่มีปัญหา! 🐳

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

## ข้อกำหนด

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- รันไทม์เอเจนต์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi หรือ Deep Agents (หรือ volume ที่ mount ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม เดมอนซิงค์จะค้นหาไฟล์เซสชันโดยอัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์ หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อดึงข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหา image `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และ metadata `container_id` ในแดชบอร์ดบนคลาวด์ เพื่อให้คุณสามารถแยกแยะจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: เดมอนซิงค์บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รันเดมอนซิงค์ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

เดมอนซิงค์จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### เสริม: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณจำเป็นต้องรันเดมอนซิงค์ **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎขาออกนี้ในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้สามารถเข้าถึง API นำเข้าของ ClawMetry ได้:

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

| Endpoint | พอร์ต | โปรโตคอล | จำเป็น |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (เดมอนซิงค์ → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

เดมอนซิงค์จะเรียกออกไปยัง `ingest.clawmetry.com` ผ่าน HTTPS เท่านั้น ไม่จำเป็นต้องมีพอร์ตขาเข้าใดๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ข้อมูลการวัดผลทางไกล (Telemetry)

ClawMetry ส่งปิงแบบไม่ระบุตัวตน "การรันครั้งแรก" เพียงครั้งเดียวไปยัง
`https://app.clawmetry.com/api/install` ในครั้งแรกที่คุณรันคำสั่ง
`clawmetry` CLI บนเครื่องใหม่ เราใช้ข้อมูลนี้เพื่อนับจำนวนการติดตั้ง (ซึ่งเป็น
ตัวชี้วัดด้านการตลาดเพียงตัวเดียวที่เรามีสำหรับโปรเจกต์โอเพนซอร์ส) และเพื่อเรียนรู้ว่า
เฟรมเวิร์กเอเจนต์ใดที่ผู้ใช้ของเราติดตั้งไว้

**POST เพียงครั้งเดียวต่อการติดตั้ง** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันการนับซ้ำ ไม่เชื่อมโยงกับอีเมลหรือ api_key ของคุณ |
| `version` | `0.12.167` | เวอร์ชันใดที่กำลังใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | ตารางการรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ใดที่เราควรผสานการทำงานด้วยต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เรา ไม่ ส่ง**: IP (คลาวด์ดึงรหัสประเทศจากคำขอฝั่งเซิร์ฟเวอร์
แล้วทิ้ง IP ไป) ชื่อโฮสต์ ชื่อผู้ใช้ เส้นทางพื้นที่ทำงาน เนื้อหาไฟล์
api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็น PII หรือเฉพาะเจาะจงกับ
พื้นที่ทำงาน payload ที่ส่งสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการใช้งาน** (วิธีใดวิธีหนึ่งต่อไปนี้จะปิดใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

หากเครือข่ายล้มเหลว จะไม่มีทางบล็อกไม่ให้ `clawmetry` ทำงานได้ เนื่องจาก
การปิงเป็นแบบ fire-and-forget บนเธรดเดมอนที่มี timeout 3 วินาที

## ประวัติดวงดาว (Star History)

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
  <strong>🦞 ดูความคิดของเอเจนต์คุณ</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
