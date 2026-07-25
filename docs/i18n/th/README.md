<!-- i18n-src:8f42d460a973 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** ระบบตรวจสอบแบบเรียลไทม์สำหรับ **รันไทม์ AI เอเจนต์ 14 ตัว**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษานี้:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

หนึ่งคำสั่ง ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จเรียบร้อย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับรันไทม์เอเจนต์ 14 ตัว

ClawMetry เริ่มต้นจากการเป็นระบบตรวจสอบสำหรับ OpenClaw และตอนนี้สามารถวัดผล **กองเอเจนต์ทั้งหมดของคุณ** ในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ไม่ว่าจะเป็นต้นทุน โทเค็น เครื่องมือ หรือ traces จะปรับขอบเขตไปตามรันไทม์นั้นโดยอัตโนมัติ ดูรายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอน ตารางระดับชั้น รูปแบบ `/api/entitlement` และ CLI `clawmetry license` ได้ที่ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวสดแสดงข้อความที่ไหลผ่านช่องทาง, brain, เครื่องมือ และย้อนกลับ
- **Overview** — การตรวจสอบสุขภาพ, heatmap กิจกรรม, จำนวนเซสชัน, ข้อมูลโมเดล
- **Usage** — การติดตามโทเค็นและต้นทุนพร้อมสรุปรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานพร้อมโมเดล, โทเค็น, กิจกรรมล่าสุด
- **Crons** — งานตามกำหนดเวลาพร้อมสถานะ, รอบถัดไป, ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์พร้อมรหัสสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ, ตัวกระตุ้นอัตราข้อผิดพลาด, การตรวจจับเอเจนต์ออฟไลน์; ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — ปิดกั้นการลบข้อมูลที่ทำลายล้าง, force push, การเปลี่ยนแปลงฐานข้อมูล, sudo, การติดตั้งแพ็กเกจ, การเรียกเครือข่าย โดยต้องมีการอนุมัติด้วยคลิกเดียวก่อน

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์ของเอเจนต์แบบสด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — สรุปการใช้งานโทเค็นและเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดต้นทุนตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ, ตัวกระตุ้นอัตราข้อผิดพลาด, webhook ไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ปิดกั้นการเรียกเครื่องมือที่มีความเสี่ยงโดยต้องมีการอนุมัติด้วยตนเอง; กฎการป้องกันที่อิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

แอป React v2 อยู่ใน `frontend/` และจะให้บริการที่ `/v2` เมื่อเริ่มเซิร์ฟเวอร์
Flask โดยเปิดใช้งาน v2

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
`http://localhost:8900` เพื่อให้แอป React สามารถสื่อสารกับเซิร์ฟเวอร์ Flask
ในเครื่องได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการสร้างบันเดิลที่แจกจ่ายพร้อมแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

บันเดิลสำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry ตรวจสอบรันไทม์เอเจนต์ AI หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์แต่ละตัวที่ไม่ใช่ OpenClaw จะมีตัวปรับแปลง (reader adapter) เฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry; daemon จะนำเข้าข้อมูลเหล่านี้ไปยัง DuckDB store + cloud snapshot เดียวกัน โดยติดแท็กด้วยรันไทม์ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดูตารางเต็มพร้อมคู่มือการเพิ่มรันไทม์ได้ที่ [`docs/compatibility.md`](docs/compatibility.md) และดูข้อมูลเบื้องต้นเกี่ยวกับตระกูล OpenClaw ได้ที่ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)

| รันไทม์ / เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | ดั้งเดิม | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | อะแดปเตอร์เบต้า | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ |
| **NanoClaw** | อะแดปเตอร์เบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) มีทรานสคริปต์ + จำนวนข้อความ |
| **Hermes** | อะแดปเตอร์เบต้า | SQLite `~/.hermes/state.db` มีทรานสคริปต์, โมเดล, โทเค็น/ต้นทุน |
| **Claude Code** | อะแดปเตอร์เบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ + การคิด, การใช้โทเค็น |
| **Codex** | อะแดปเตอร์เบต้า | Rollout JSONL `~/.codex/sessions/...` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, การใช้โทเค็น |
| **Cursor** | อะแดปเตอร์เบต้า | SQLite `state.vscdb` มีทรานสคริปต์แชท/composer, โมเดล |
| **Aider** | อะแดปเตอร์เบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ มีทรานสคริปต์, โมเดล, จำนวนโทเค็น |
| **Goose** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/goose` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, ยอดรวมโทเค็น |
| **opencode** | อะแดปเตอร์เบต้า | SQLite `~/.local/share/opencode` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, โทเค็น + ต้นทุน |
| **Qwen Code** | อะแดปเตอร์เบต้า | JSONL `~/.qwen/projects/.../chats` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, การใช้โทเค็น |
| **Pi** | อะแดปเตอร์เบต้า | JSONL `~/.pi/agent/sessions` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, โทเค็น + ต้นทุน |
| **Deep Agents** | อะแดปเตอร์เบต้า | SQLite `~/.deepagents/.state/sessions.db` มีทรานสคริปต์, โมเดล, การเรียกใช้เครื่องมือ, โทเค็น + ต้นทุน |

"อะแดปเตอร์เบต้า" หมายความว่า ClawMetry มีตัวอ่านสำหรับรูปแบบไฟล์จริงบนดิสก์ของรันไทม์นั้น ๆ ซึ่งแต่ละตัวถูกสร้างและตรวจสอบยืนยันกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) อะแดปเตอร์เป็นแบบอ่านอย่างเดียว และแต่ละตัวจะแสดงข้อมูลตรงตามที่รันไทม์นั้นบันทึกไว้จริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้บันทึกต้นทุนโทเค็นลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันไปยังรันไทม์เดียวเพื่อการเจาะลึกที่ชัดเจน

## ติดตามเอเจนต์ SDK ใด ๆ ก็ได้ — การระบุต้นทุนแบบ out-loop

รันไทม์ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **เอเจนต์ที่ใช้งานจริงในโปรดักชัน** ของคุณเอง ไม่ว่าจะสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูปธรรมดาที่ใช้ `httpx` นั้นไม่เขียนข้อมูลลงดิสก์ ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียก LLM ของมันได้ (ต้นทุน, โทเค็น, เวลาแฝง, ข้อผิดพลาด) ด้วยการแพตช์ `httpx`/`requests` แบบ monkey-patch:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะติดแท็กการเรียกแต่ละครั้งด้วย **แหล่งที่มาที่ตั้งชื่อ** ดังนั้นทุกผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดของตัวเองที่สามารถระบุต้นทุนได้ในการ์ด **🔌 Out-loop sources** บนแท็บ Overview ของแดชบอร์ด ไม่ว่าจะเป็นจำนวนการเรียก, ผู้ให้บริการ, เวลาแฝง, อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งที่มาไว้ใช่ไหม? การเรียกยังคงถูกติดตามอยู่ แค่การ์ดจะซ่อนไว้เท่านั้น

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่อะแดปเตอร์รันไทม์ป้อนเข้ามา (DuckDB → cloud snapshot) ดังนั้น out-loop sources จะซิงค์ไปยังแดชบอร์ดคลาวด์เหมือนกับทุกอย่างอื่น โดยเข้ารหัสแบบ E2E

## OpenTelemetry — ไม่ผูกติดกับผู้ให้บริการรายใด ส่งเทรซของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** ดังนั้นเทรซของเอเจนต์คุณจะไม่ถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน ไม่ว่าจะเป็นการเรียก LLM, เครื่องมือ, ซับเอเจนต์, โทเค็น, ต้นทุน เป็น OTLP/HTTP GenAI spans ไปยังตัวรวบรวมใด ๆ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ส่วนหัวการยืนยันตัวตนและช่วงเวลาการโพลเป็นตัวแปรสภาพแวดล้อมที่ไม่บังคับ:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** — ตัวรับ OTLP ในตัวจะรับเทรซและเมตริกจากที่ใดก็ได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry แบบไม่ต้องตั้งค่าที่ทำงานในเครื่องเป็นหลัก **และ** ข้อมูลของคุณในระบบหลังบ้านใดก็ตามที่ทีมของคุณใช้อยู่แล้ว ไม่มีการล็อกอิน ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การตั้งค่า

คนส่วนใหญ่ไม่จำเป็นต้องตั้งค่าใด ๆ ClawMetry จะตรวจจับพื้นที่ทำงาน, ล็อก, เซสชัน และ crons ของคุณโดยอัตโนมัติ

หากต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมสดสำหรับทุกช่องทาง OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในแผนภาพ Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใด ๆ ใน Flow เพื่อดูมุมมองฟองแชทสดพร้อมจำนวนข้อความขาเข้า/ขาออก

| ช่องทาง | สถานะ | ป๊อปอัปสด | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ, สถิติ, รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่านจาก `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับกิลด์ + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับพื้นที่ทำงาน + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชัน web UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI แบบฟองสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และจะแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยตนเอง

## การติดตั้งใช้งานผ่าน Docker

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์คุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry สามารถตรวจจับการตั้งค่าของคุณได้โดยอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งโดยอัตโนมัติผ่าน pip)
- รันไทม์ AI เอเจนต์บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi หรือ Deep Agents (หรือโวลุ่มที่ mount ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ส่วนใหญ่แล้วไม่จำเป็นต้องตั้งค่าเพิ่มเติม sync daemon จะค้นหาไฟล์เซสชันโดยอัตโนมัติไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อรับข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหาอิมเมจ `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่านการ mount โวลุ่มหรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และเมทาดาทา `container_id` ในแดชบอร์ดคลาวด์ เพื่อให้คุณแยกแยะจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: sync daemon บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รัน sync daemon ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่าย NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ตัวเลือกเสริม: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

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

| Endpoint | พอร์ต | โปรโตคอล | จำเป็น |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (sync daemon → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

sync daemon เรียก HTTPS ขาออกไปยัง `ingest.clawmetry.com` เท่านั้น ไม่ต้องเปิดพอร์ตขาเข้าใด ๆ

---

## การติดตั้งใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่งสัญญาณ "รันครั้งแรก" แบบไม่ระบุตัวตนเพียงครั้งเดียวไปยัง
`https://app.clawmetry.com/api/install` ในครั้งแรกที่คุณรัน CLI `clawmetry`
บนเครื่องใหม่ เราใช้ข้อมูลนี้เพื่อนับจำนวนการติดตั้ง (ซึ่งเป็นตัวชี้วัดทางการตลาดเพียงอย่างเดียวที่เรามีสำหรับโปรเจกต์ OSS)
และเพื่อเรียนรู้ว่าผู้ใช้ของเราติดตั้งเฟรมเวิร์กเอเจนต์ตัวใดบ้าง

**POST เพียงหนึ่งครั้งต่อการติดตั้งหนึ่งครั้ง** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันข้อมูลซ้ำ; ไม่เชื่อมโยงกับอีเมลหรือ api_key ของคุณ |
| `version` | `0.12.167` | เวอร์ชันใดบ้างที่ถูกใช้งานอยู่จริง |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | ตารางการรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ตัวใดที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์จะดึงรหัสประเทศฝั่งเซิร์ฟเวอร์จากคำขอ
แล้วทิ้ง IP ไป), ชื่อโฮสต์, ชื่อผู้ใช้, พาธพื้นที่ทำงาน, เนื้อหาไฟล์,
api_key ของคุณ, อีเมลของคุณ, หรือสิ่งใดก็ตามที่เป็น PII หรือเฉพาะพื้นที่ทำงาน
payload ที่ส่งผ่านสายสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**ยกเลิกการใช้งาน** (ทำวิธีใดวิธีหนึ่งต่อไปนี้เพื่อปิดใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายในส่วนนี้จะไม่มีทางบล็อกไม่ให้ `clawmetry` ทำงาน
สัญญาณนี้เป็นแบบ fire-and-forget บน daemon thread ที่มี timeout 3 วินาที

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
  <strong>🦞 ดูความคิดของเอเจนต์คุณ</strong><br>
  <sub>สร้างโดย <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · ส่วนหนึ่งของระบบนิเวศ <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
