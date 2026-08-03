<!-- i18n-src:0e34918f8f2e -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูสิ่งที่เอเจนต์ของคุณกำลังคิด** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **14 รันไทม์ของ AI เอเจนต์**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 ตัว แดชบอร์ดเดียวสำหรับฟลีตเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษานี้ได้ที่:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างโดยอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จแล้ว

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## รองรับรันไทม์เอเจนต์ 14 ตัว

ClawMetry เริ่มต้นจากการเป็นระบบสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายมาวัดผล **ฟลีตเอเจนต์ทั้งหมด** ของคุณในแดชบอร์ดเดียว โดยตรวจจับรันไทม์แต่ละตัวบนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ และการติดตาม (traces) จะปรับขอบเขตไปตามรันไทม์นั้นโดยอัตโนมัติ ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดที่ชัดเจนว่าอะไรฟรี/อะไรเสียเงิน ตารางระดับชั้น รูปแบบข้อมูล `/api/entitlement` และคำสั่ง CLI `clawmetry license`

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวแบบเรียลไทม์ที่แสดงข้อความไหลผ่านช่องทาง สมอง เครื่องมือ และย้อนกลับ
- **Overview** — การตรวจสอบสถานะ แผนที่ความร้อนของกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและค่าใช้จ่ายพร้อมรายละเอียดรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่ทำงานอยู่ พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานตามกำหนดเวลา พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — การสตรีมล็อกแบบเรียลไทม์ที่มีรหัสสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบบับเบิลแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — กันการลบไฟล์แบบทำลายล้าง การ force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ และการเรียกเครือข่าย ไว้หลังการอนุมัติแบบคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบเรียลไทม์
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้งานโทเคน & สรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดค่าใช้จ่ายตามโมเดล & เซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัย & บันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด เว็บฮุคไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กันการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง พร้อมกฎการป้องกันที่อิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนดำเนินการสำหรับ Claude Code** — คำสั่งเดียวติดตั้งฮุค
PreToolUse ที่หยุดการเรียกใช้เครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่มันจะทำงาน และรอ
การตัดสินใจของคุณ (แตะเพียงครั้งเดียวจากโทรศัพท์ของคุณด้วย
[การแจ้งเตือนแบบพุชผ่านคลาวด์](https://app.clawmetry.com/push) ที่เปิดใช้งานไว้):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธ (deny) จะบล็อกเฉพาะการเรียกใช้เครื่องมือครั้งนั้นครั้งเดียว เอเจนต์ยังคงเซสชันของตัวเองไว้และสามารถ
ลองวิธีอื่นได้ การอนุมัติผ่านโทรศัพท์ของคุณจะข้ามพร้อมท์การอนุญาตของ Claude Code เอง
(เพราะคุณตอบไปแล้ว) คุณยังได้รับการแจ้งเตือนแบบพุชไปยังโทรศัพท์เมื่อ Claude Code เองกำลัง
รอคุณอยู่ (การแจ้งเตือน `permission_prompt` / `idle_prompt`)

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

## การพัฒนา Frontend v2

แอป React v2 อยู่ใน `frontend/` และให้บริการที่ `/v2` เมื่อเซิร์ฟเวอร์ Flask
ถูกเริ่มต้นด้วยการเปิดใช้งาน v2

ใช้เทอร์มินัลสองหน้าต่างขณะพัฒนา:

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
โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการสร้างบันเดิลที่แนบไปกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

บันเดิลสำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์รันไทม์ของ AI เอเจนต์หลายตัว ไม่ใช่แค่ OpenClaw เท่านั้น รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวจะมีอะแดปเตอร์อ่านเฉพาะที่แปลรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry เดมอนจะนำข้อมูลเหล่านี้เข้าสู่สโตร์ DuckDB เดียวกัน + สแนปช็อตคลาวด์ โดยติดแท็กด้วยรันไทม์ และแท็บเล่นซ้ำเซสชัน (Session replay) จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบฉบับเต็ม + คู่มือการเพิ่มรันไทม์ใหม่ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้เบื้องต้นเกี่ยวกับตระกูล OpenClaw

กำลังใช้เครื่องมือความปลอดภัยเอเจนต์ [numbat ของ Perplexity](https://github.com/perplexityai/numbat) อยู่หรือเปล่า? ClawMetry สามารถนำผลตรวจพบและการตัดสินใจบังคับใช้ของมันเข้ามาใช้ได้ทันที ดู [`docs/NUMBAT.md`](docs/NUMBAT.md)

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | เนทีฟ | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | อะแดปเตอร์เบต้า | JSONL แบบแบนของ `providers.Message` (`~/.picoclaw/workspace/sessions`) ประวัติสนทนา โมเดล การเรียกเครื่องมือ |
| **NanoClaw** | อะแดปเตอร์เบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) ประวัติสนทนา + จำนวนข้อความ |
| **Hermes** | อะแดปเตอร์เบต้า | SQLite `~/.hermes/state.db` ประวัติสนทนา โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | อะแดปเตอร์เบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` ประวัติสนทนา โมเดล การเรียกเครื่องมือ + การคิด การใช้งานโทเคน |
| **Codex** | อะแดปเตอร์เบต้า | Rollout JSONL `~/.codex/sessions/...` ประวัติสนทนา โมเดล การเรียกเครื่องมือ การใช้งานโทเคน |
| **Cursor** | อะแดปเตอร์เบต้า | SQLite `state.vscdb` ประวัติสนทนาแบบ Chat/Composer โมเดล |
| **Aider** | อะแดปเตอร์เบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ ประวัติสนทนา โมเดล จำนวนโทเคน |
| **Goose** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/goose` ประวัติสนทนา โมเดล การเรียกเครื่องมือ รวมโทเคน |
| **opencode** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/opencode` ประวัติสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | อะแดปเตอร์เบต้า | JSONL `~/.qwen/projects/.../chats` ประวัติสนทนา โมเดล การเรียกเครื่องมือ การใช้งานโทเคน |
| **Pi** | อะแดปเตอร์เบต้า | JSONL `~/.pi/agent/sessions` ประวัติสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | อะแดปเตอร์เบต้า | SQLite `~/.deepagents/.state/sessions.db` ประวัติสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | อะแดปเตอร์เบต้า | SQLite `~/.n8n/database.sqlite` การรันเวิร์กโฟลว์ การรันโหนด พรอมต์ของ AI Agent โมเดล + โทเคนในกรณีที่ n8n บันทึกไว้ |
| **Antigravity** | อะแดปเตอร์เบต้า | Brain JSONL ภายใต้ `~/.gemini/<flavor>/brain/` บทสนทนา ขั้นตอนเครื่องมือ การคิด การแบ่งโทเคน Gemini ต่อการสร้างผลลัพธ์ + ค่าใช้จ่าย การใช้งานจากการสร้างผลลัพธ์เบื้องหลัง |
| **GitHub Copilot** | อะแดปเตอร์เบต้า | Copilot CLI `events.jsonl` ภายใต้ `~/.copilot/session-state/` + บัญชีการใช้งานต่อการเรียก `session-store.db` บทสนทนา การเรียกเครื่องมือ การจัดเส้นทางโมเดล การแบ่งโทเคนแบบคำนึงถึงแคช ค่าใช้จ่ายที่เรียกเก็บโดยผู้ให้บริการเป็นเครดิต AI |

"อะแดปเตอร์เบต้า" หมายความว่า ClawMetry มีตัวอ่านสำหรับรูปแบบไฟล์บนดิสก์จริงของรันไทม์นั้น ๆ ซึ่งแต่ละตัวถูกสร้างและตรวจสอบกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) อะแดปเตอร์เป็นแบบอ่านอย่างเดียว และแต่ละตัวจะซื่อสัตย์เกี่ยวกับสิ่งที่รันไทม์นั้นบันทึกไว้จริง (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานอยู่บนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันให้เหลือรันไทม์เดียวเพื่อการเจาะลึกที่สะอาด

## ติดตามเอเจนต์ SDK ใด ๆ ก็ได้ — การระบุค่าใช้จ่ายนอกลูป

รันไทม์ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **เอเจนต์ที่ใช้งานจริง (production)** ของคุณเอง ไม่ว่าจะเป็นตัวที่คุณสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา จะไม่ทำเช่นนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าใด ๆ ของ ClawMetry ยังคงสามารถจับการเรียก LLM ของมันได้ (ค่าใช้จ่าย โทเคน ความหน่วง ข้อผิดพลาด) โดยการมังกี้แพตช์ `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่มีชื่อ** ดังนั้นแต่ละผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดที่ระบุค่าใช้จ่ายได้แยกต่างหากในการ์ด **🔌 แหล่งที่มานอกลูป** บนแท็บ Overview ของแดชบอร์ด แสดงจำนวนการเรียก ผู้ให้บริการ ความหน่วง อัตราข้อผิดพลาดต่อเอเจนต์ ยังไม่ได้ตั้งค่าแหล่งที่มา? การเรียกยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะยังซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่อะแดปเตอร์รันไทม์ป้อนข้อมูล (DuckDB → สแนปช็อตคลาวด์) ดังนั้นแหล่งที่มานอกลูปจะซิงค์ไปยังแดชบอร์ดคลาวด์เหมือนกับข้อมูลอื่น ๆ ทุกประการ โดยเข้ารหัสแบบ E2E

## OpenTelemetry — เป็นกลางต่อผู้ให้บริการ ส่งการติดตาม (traces) ของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **อนุสัญญาความหมาย GenAI (GenAI semantic conventions)** ดังนั้นการติดตามเอเจนต์ของคุณจะไม่มีวันถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน ทั้งการเรียก LLM เครื่องมือ ซับเอเจนต์ โทเคน ค่าใช้จ่าย เป็น GenAI span แบบ OTLP/HTTP ไปยังตัวรวบรวมใด ๆ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

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

**นำเข้า** ตัวรับ OTLP ในตัวจะรับการติดตามและเมตริกจากที่อื่นใดก็ตามที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าใด ๆ และเน้นข้อมูลในเครื่อง **และ** ข้อมูลของคุณในแบ็กเอนด์ใด ๆ ก็ตามที่ทีมของคุณใช้อยู่แล้ว ไม่มีการล็อกอิน ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การกำหนดค่า

คนส่วนใหญ่ไม่จำเป็นต้องกำหนดค่าใด ๆ เลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ cron ของคุณโดยอัตโนมัติ

หากคุณต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทางของ OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใดก็ได้ใน Flow เพื่อดูมุมมองบับเบิลแชทแบบเรียลไทม์ พร้อมจำนวนข้อความขาเข้า/ขาออก

| ช่องทาง | สถานะ | ป็อปอัปสด | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับกิลด์ + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับเวิร์กスペซ + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชัน UI เว็บในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI บับเบิลสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่านเว็บฮุค Chat API |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | กระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และจะแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่จำเป็นต้องตั้งค่าด้วยตนเอง

## การปรับใช้ด้วย Docker

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้เมานต์ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์ของคุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry สามารถตรวจจับการตั้งค่าของคุณโดยอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งโดยอัตโนมัติผ่าน pip)
- รันไทม์ AI เอเจนต์บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity หรือ GitHub Copilot (หรือโวลุ่มที่เมานต์ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

โดยส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติมใด ๆ เดมอนซิงค์จะค้นหาไฟล์เซสชันโดยอัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อรับข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหาอิมเมจ `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่านโวลุ่มที่เมานต์หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วยเมทาดาทา `runtime=nemoclaw` และ `container_id` ในแดชบอร์ดคลาวด์ เพื่อให้คุณสามารถแยกแยะจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: เดมอนซิงค์บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รันเดมอนซิงค์ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) เพื่อหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

เดมอนซิงค์จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ทางเลือก: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณจำเป็นต้องรันเดมอนซิงค์ **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎการรับส่งข้อมูลขาออก (egress) นี้ในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้สามารถเข้าถึง API การนำเข้าของ ClawMetry ได้:

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
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (เดมอนซิงค์ → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

เดมอนซิงค์จะเรียก HTTPS ขาออกไปยัง `ingest.clawmetry.com` เท่านั้น ไม่จำเป็นต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การปรับใช้บนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์ (Cloud Testing Guide)](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ถูกทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## การเก็บข้อมูลเทเลเมทรี

ClawMetry ส่งการปิงแบบไม่ระบุตัวตนเกี่ยวกับวงจรชีวิตการติดตั้งไปที่
`https://app.clawmetry.com/api/install`: การปิง `install` หนึ่งครั้งในการรัน
CLI `clawmetry` ครั้งแรกบนเครื่องใหม่ การปิง `update` หนึ่งครั้งในการรันครั้งแรก
หลังจากอัปเกรดเป็นเวอร์ชันใหม่ และการปิง `onboarded` หนึ่งครั้งเมื่อคุณทำตัวเลือก
onboarding ในแดชบอร์ดเสร็จสิ้น เราใช้ข้อมูลนี้เพื่อนับจำนวนการติดตั้งจริง
(ตัวเลขการดาวน์โหลด PyPI ดิบ ๆ ประมาณ 98% เป็นมิเรอร์ CI และการดาวน์โหลดซ้ำจากการอัปเดตอัตโนมัติ)
และเพื่อเรียนรู้ว่าเฟรมเวิร์กและเวอร์ชันของเอเจนต์ใดกำลังถูกใช้งานอยู่จริง

**สูงสุดหนึ่ง POST ต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ซึ่งประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | การตัดข้อมูลซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อ Cloud sync อย่างชัดเจน (จากนั้น heartbeat ของเดมอนที่ยืนยันตัวตนแล้วจะพกพา ID นี้ไป เชื่อมโยงการติดตั้งนี้กับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | การติดตั้งใหม่ vs การอัปเกรดของที่มีอยู่ |
| `version` | `0.12.167` | เวอร์ชันใดบ้างที่กำลังถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญของการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | เมทริกซ์การรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ใดที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์อนุมานรหัสประเทศฝั่งเซิร์ฟเวอร์
จากคำขอ จากนั้นทิ้ง IP นั้น) ชื่อโฮสต์ ชื่อผู้ใช้ พาธพื้นที่ทำงาน
เนื้อหาไฟล์ api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็น PII หรือเฉพาะ
พื้นที่ทำงาน payload ที่ส่งผ่านสายสามารถตรวจสอบได้ใน
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการเก็บข้อมูล** (ทำอย่างใดอย่างหนึ่งต่อไปนี้เพื่อปิดใช้งานอย่างถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายที่นี่จะไม่มีวันบล็อกไม่ให้ `clawmetry` ทำงานได้ การปิง
เป็นแบบยิงแล้วลืม (fire-and-forget) บนเธรดเดมอนที่มี timeout 3 วินาที

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
  <strong>🦞 ดูสิ่งที่เอเจนต์ของคุณกำลังคิด</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
