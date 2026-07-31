<!-- i18n-src:02b789586c7d -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **14 เอเจนต์รันไทม์**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าใด ๆ ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จแล้ว

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 14 เอเจนต์รันไทม์

ClawMetry เริ่มต้นจากการเป็นระบบสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายมาวัดผล **กองเอเจนต์ทั้งหมดของคุณ** ในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ และการติดตาม จะปรับขอบเขตให้ตรงกับรันไทม์นั้นโดยอัตโนมัติ ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดการแบ่งฟรี/เสียเงินที่ชัดเจน ตารางระดับสิทธิ์ รูปแบบ `/api/entitlement` และคำสั่ง CLI `clawmetry license`

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวสดแสดงข้อความที่ไหลผ่านช่องทาง สมอง เครื่องมือ และย้อนกลับ
- **Overview** — การตรวจสอบสุขภาพระบบ แผนที่ความร้อนของกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — ติดตามโทเคนและค่าใช้จ่ายพร้อมสรุปรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานอยู่ พร้อมโมเดล โทเคน และกิจกรรมล่าสุด
- **Crons** — งานที่ตั้งเวลาไว้พร้อมสถานะ การทำงานครั้งถัดไป และระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์ที่มีการไล่สีตามประเภท
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md และบันทึกประจำวัน
- **Transcripts** — อินเทอร์เฟซแบบฟองข้อความแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ตัวกระตุ้นอัตราความผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **Approvals** — กันการลบแบบทำลายล้าง การ force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ และการเรียกเครือข่ายไว้ด้วยการอนุมัติเพียงคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบสด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — สรุปการใช้โทเคนและเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกเครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดค่าใช้จ่ายตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ตัวกระตุ้นอัตราความผิดพลาด webhook ไปยัง Slack / Discord / PagerDuty / อีเมล
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กันการเรียกเครื่องมือที่มีความเสี่ยงไว้ด้วยการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่อิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนดำเนินการสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook แบบ PreToolUse ที่หยุดการเรียกเครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่จะทำงาน และรอ
การตัดสินใจของคุณ (แตะครั้งเดียวจากโทรศัพท์ของคุณเมื่อเปิดใช้งาน
[การแจ้งเตือนแบบ push บนคลาวด์](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกเฉพาะการเรียกเครื่องมือครั้งนั้น เอเจนต์ยังคงเซสชันไว้และสามารถ
ลองวิธีอื่นได้ การอนุมัติผ่านโทรศัพท์ของคุณจะข้ามพร้อมท์การอนุญาตของ Claude Code เอง
(คุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขมีค่าใช้จ่ายประมาณ 40ms และ
ตกไปยังขั้นตอนการอนุญาตปกติของ Claude Code คุณยังได้รับการแจ้งเตือนบนโทรศัพท์เมื่อ
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

แอป React v2 อยู่ที่ `frontend/` และให้บริการที่ `/v2` เมื่อเซิร์ฟเวอร์
Flask เริ่มทำงานโดยเปิดใช้งาน v2

ใช้เทอร์มินัลสองหน้าต่างระหว่างพัฒนา:

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

หากต้องการสร้างชุดโปรแกรมที่จะรวมส่งไปพร้อมกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

ชุดโปรแกรมสำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์เอเจนต์รันไทม์ของ AI หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวจะมีตัวปรับข้อมูล (adapter) เฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry แดมอนจะนำเข้าข้อมูลเหล่านี้ลงในที่เก็บ DuckDB เดียวกัน + สแนปช็อตคลาวด์ โดยติดแท็กด้วยรันไทม์ และแท็บเล่นย้อนเซสชันจะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเต็มรูปแบบ + คู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้เบื้องต้นเกี่ยวกับตระกูล OpenClaw

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | เนทีฟ | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | ตัวปรับข้อมูลเบต้า | รูปแบบ `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ |
| **NanoClaw** | ตัวปรับข้อมูลเบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) มีบันทึกการสนทนา + จำนวนข้อความ |
| **Hermes** | ตัวปรับข้อมูลเบต้า | SQLite `~/.hermes/state.db` มีบันทึกการสนทนา โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | ตัวปรับข้อมูลเบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ + การคิด การใช้โทเคน |
| **Codex** | ตัวปรับข้อมูลเบต้า | Rollout JSONL `~/.codex/sessions/...` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Cursor** | ตัวปรับข้อมูลเบต้า | SQLite `state.vscdb` บันทึกการสนทนาแบบแชท/composer โมเดล |
| **Aider** | ตัวปรับข้อมูลเบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ มีบันทึกการสนทนา โมเดล จำนวนโทเคน |
| **Goose** | ตัวปรับข้อมูลเบต้า | SQLite `~/.local/share/goose` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ จำนวนโทเคนรวม |
| **opencode** | ตัวปรับข้อมูลเบต้า | SQLite `~/.local/share/opencode` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | ตัวปรับข้อมูลเบต้า | JSONL `~/.qwen/projects/.../chats` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Pi** | ตัวปรับข้อมูลเบต้า | JSONL `~/.pi/agent/sessions` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | ตัวปรับข้อมูลเบต้า | SQLite `~/.deepagents/.state/sessions.db` มีบันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | ตัวปรับข้อมูลเบต้า | SQLite `~/.n8n/database.sqlite` การดำเนินการเวิร์กโฟลว์ การรันโหนด พรอมต์ของ AI Agent โมเดล + โทเคนเมื่อ n8n บันทึกไว้ |
| **Antigravity** | ตัวปรับข้อมูลเบต้า | Brain JSONL ภายใต้ `~/.gemini/<flavor>/brain/` บทสนทนา ขั้นตอนเครื่องมือ การคิด การแบ่งโทเคน Gemini ต่อการสร้าง + ค่าใช้จ่าย การใช้งานจากการสร้างในพื้นหลัง |

"ตัวปรับข้อมูลเบต้า" หมายถึง ClawMetry มีตัวอ่านสำหรับรูปแบบไฟล์จริงบนดิสก์ของรันไทม์นั้น ๆ แต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) ตัวปรับข้อมูลเป็นแบบอ่านอย่างเดียว แต่ละตัวจะสื่อสารตรงไปตรงมาว่ารันไทม์นั้นเก็บข้อมูลอะไรจริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันให้เหลือรันไทม์เดียวเพื่อการเจาะลึกที่สะอาดตา

## ติดตามเอเจนต์ SDK ใดก็ได้ — การระบุค่าใช้จ่ายแบบ out-loop

รันไทม์ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **เอเจนต์การผลิต** ของคุณเอง ไม่ว่าจะเป็นตัวที่คุณสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูปธรรมดาที่ใช้ `httpx` นั้นไม่เขียน ตัวสกัดจับแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับข้อมูลการเรียก LLM ของมันได้ (ค่าใช้จ่าย โทเคน เวลาแฝง ข้อผิดพลาด) ด้วยการแพตช์ `httpx`/`requests` แบบ monkey-patch:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่มีชื่อ** ดังนั้นทุกผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดของตัวเองในแดชบอร์ด ที่สามารถระบุค่าใช้จ่ายได้ ในการ์ด **🔌 Out-loop sources** บนแท็บ Overview เช่น จำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งที่มาไว้หรือ? การเรียกยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะซ่อนไว้

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่ตัวปรับข้อมูลของรันไทม์ป้อนเข้าไป (DuckDB → สแนปช็อตคลาวด์) ดังนั้นแหล่งที่มาแบบ out-loop จะซิงค์กับแดชบอร์ดบนคลาวด์เหมือนกับข้อมูลอื่น ๆ ทั้งหมด แบบเข้ารหัสจากต้นทางถึงปลายทาง

## OpenTelemetry — ไม่ผูกติดกับผู้ให้บริการรายใด ส่งข้อมูลติดตามของคุณไปที่ไหนก็ได้

ClawMetry สื่อสารด้วย **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **มาตรฐาน GenAI semantic conventions** เพื่อให้ข้อมูลติดตามเอเจนต์ของคุณไม่ถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน ไม่ว่าจะเป็นการเรียก LLM เครื่องมือ ซับเอเจนต์ โทเคน ค่าใช้จ่าย เป็น OTLP/HTTP GenAI spans ไปยังตัวรวบรวมข้อมูลใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ส่วนหัวการยืนยันตัวตนและช่วงเวลาการโพลเป็นตัวแปรสภาพแวดล้อมทางเลือก:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** ตัวรับ OTLP ในตัวรองรับข้อมูลการติดตามและเมตริกจากที่อื่นได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้แดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าและเน้นข้อมูลในเครื่อง **พร้อมกับ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมของคุณใช้อยู่แล้ว ไม่มีการผูกติด ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การกำหนดค่า

คนส่วนใหญ่ไม่ต้องตั้งค่าอะไรเลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ crons ของคุณโดยอัตโนมัติ

หากต้องการปรับแต่งเพิ่มเติม:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทางของ OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใดก็ได้ใน Flow เพื่อดูมุมมองแบบฟองแชทสดพร้อมจำนวนข้อความเข้า/ออก

| ช่องทาง | สถานะ | ป็อปอัปสด | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Guild + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ Workspace + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชันจากเว็บ UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI แบบฟองข้อความสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครรับเหตุการณ์ผ่าน WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยตนเอง

## การใช้งานผ่าน Docker

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์ของคุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry ตรวจจับการตั้งค่าของคุณได้โดยอัตโนมัติ

## ข้อกำหนดของระบบ

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- เอเจนต์รันไทม์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n หรือ Antigravity (หรือ volume ที่ mount ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม แดมอนซิงค์จะค้นหาไฟล์เซสชันโดยอัตโนมัติไม่ว่าจะอยู่ที่ `~/.openclaw/` บนโฮสต์ หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ได้สองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อดึงข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหาอิมเมจ `openshell`, `nemoclaw`, หรือ `ghcr.io/nvidia/` แล้วอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และข้อมูลเมทา `container_id` ในแดชบอร์ดคลาวด์ เพื่อให้คุณแยกความแตกต่างจากเซสชัน OpenClaw มาตรฐานได้ในพริบตา

### การตั้งค่าที่แนะนำ: แดมอนซิงค์บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รันแดมอนซิงค์ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้ช่วยหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

แดมอนซิงค์จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ทางเลือก: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณจำเป็นต้องรันแดมอนซิงค์ **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎ egress นี้ในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้เข้าถึง API การนำเข้าข้อมูลของ ClawMetry ได้:

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

| ปลายทาง | พอร์ต | โปรโตคอล | จำเป็น |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (แดมอนซิงค์ → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

แดมอนซิงค์เรียก HTTPS ขาออกเฉพาะไปยัง `ingest.clawmetry.com` เท่านั้น ไม่จำเป็นต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ได้รับการทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## การเก็บข้อมูลทางไกล (Telemetry)

ClawMetry ส่ง ping แบบไม่ระบุตัวตนเกี่ยวกับวงจรชีวิตการติดตั้งไปยัง
`https://app.clawmetry.com/api/install`: หนึ่ง ping `install` ในครั้งแรก
ที่คุณรัน CLI `clawmetry` บนเครื่องใหม่ หนึ่ง ping `update`
ในการรันครั้งแรกหลังจากอัปเกรดเป็นเวอร์ชันใหม่ และหนึ่ง ping `onboarded`
เมื่อคุณทำการเลือกในขั้นตอนแนะนำการใช้งานในแดชบอร์ดเสร็จสิ้น เราใช้ข้อมูลนี้
เพื่อนับจำนวนการติดตั้งจริง (ตัวเลขการดาวน์โหลดดิบจาก PyPI ประมาณ 98% เป็นมิเรอร์ CI
และการดาวน์โหลดซ้ำจากการอัปเดตอัตโนมัติ) และเพื่อเรียนรู้ว่าเฟรมเวิร์กเอเจนต์และ
เวอร์ชันใดที่กำลังถูกใช้งานจริง

**อย่างมากหนึ่ง POST ต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันข้อมูลซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อ Cloud sync อย่างชัดเจน (การส่ง heartbeat ของแดมอนที่ยืนยันตัวตนแล้วจะพกข้อมูลนี้ ทำให้เชื่อมโยงการติดตั้งนี้กับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | ติดตั้งใหม่หรืออัปเกรดของเดิม |
| `version` | `0.12.167` | เวอร์ชันใดที่กำลังใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลต�ฟอร์ม |
| `python` | `3.11.15` | ตารางเวอร์ชัน Python ที่รองรับ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ควรผสานรวมกับเอเจนต์ใดต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์อนุมานรหัสประเทศจากฝั่งเซิร์ฟเวอร์
จากคำขอ แล้วทิ้ง IP นั้น) ชื่อโฮสต์ ชื่อผู้ใช้ เส้นทางพื้นที่ทำงาน เนื้อหาไฟล์
api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็นข้อมูลส่วนบุคคลหรือเฉพาะพื้นที่ทำงาน
เพย์โหลดที่ส่งสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการติดตาม** (วิธีใดวิธีหนึ่งด้านล่างนี้จะปิดใช้งานอย่างถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายในส่วนนี้จะไม่มีทางบล็อกการทำงานของ `clawmetry` เลย
การ ping นี้เป็นแบบ fire-and-forget บนเธรดแดมอนที่มี timeout 3 วินาที

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
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · เป็นส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
