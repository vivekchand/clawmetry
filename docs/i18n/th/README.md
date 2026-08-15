<!-- i18n-src:c422fb7dd0da -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **20 รันไทม์เอเจนต์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 16 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านเป็นภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แค่นี้ก็เสร็จ

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 20 รันไทม์เอเจนต์

ClawMetry เริ่มต้นจากการสังเกตการณ์สำหรับ OpenClaw และตอนนี้วัดผลให้กับ **กองเอเจนต์ทั้งหมดของคุณ** ในแดชบอร์ดเดียว โดยตรวจจับแต่ละรันไทม์บนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือไลเซนส์ Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งค่าใช้จ่าย โทเคน เครื่องมือ การติดตาม จะปรับขอบเขตไปตามรันไทม์นั้น ดู **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** สำหรับรายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอน ตารางระดับสิทธิ์ รูปแบบของ `/api/entitlement` และคำสั่ง CLI `clawmetry license`

## คุณจะได้อะไร

- **Flow** — ไดอะแกรมเคลื่อนไหวแบบเรียลไทม์ที่แสดงข้อความไหลผ่านช่องทาง สมอง เครื่องมือ แล้วย้อนกลับมา
- **Overview** — การตรวจสุขภาพ แผนที่ความร้อนของกิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเคนและค่าใช้จ่ายพร้อมสรุปรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานอยู่ พร้อมโมเดล โทเคน กิจกรรมล่าสุด
- **Crons** — งานตามตารางเวลา พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกแบบเรียลไทม์ที่มีสีแยกประเภท
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด การตรวจจับเอเจนต์ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — กันการลบแบบทำลายล้าง การ force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ การเรียกเครือข่าย ไว้หลังการอนุมัติแบบคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบเรียลไทม์
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้โทเคนและสรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกเครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — แจกแจงค่าใช้จ่ายตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — เครื่องมือเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — สถานะความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ทริกเกอร์อัตราข้อผิดพลาด เว็บฮุกไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กันการเรียกเครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง กฎการป้องกันที่มีนโยบายรองรับ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนการทำงานสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook แบบ PreToolUse ที่หยุดการเรียกเครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่มันจะทำงาน และรอ
การตัดสินใจของคุณ (แตะครั้งเดียวจากโทรศัพท์เมื่อเปิดใช้
[การแจ้งเตือนแบบพุชบนคลาวด์](https://app.clawmetry.com/push) ไว้):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกแค่การเรียกเครื่องมือครั้งนั้นครั้งเดียว เอเจนต์ยังคงเซสชันของมันอยู่และสามารถ
ลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์จะข้ามพรอมต์การอนุญาตของ Claude Code เอง
(เพราะคุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขจะใช้เวลาราว ~40ms และ
ตกลงไปในโฟลว์การอนุญาตปกติของ Claude Code คุณยังจะได้รับพุชบนโทรศัพท์เมื่อ Claude Code เอง
กำลังรอคุณอยู่ (การแจ้งเตือน `permission_prompt` /
`idle_prompt`)

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

เปิด `http://localhost:5173/v2/` Vite จะ proxy คำขอ `/api` ไปที่
`http://localhost:8900` ทำให้แอป React สามารถคุยกับ Flask server ในเครื่อง
ได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการ build bundle ที่จะแพ็กไปพร้อมกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

bundle สำหรับใช้งานจริงจะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์ / เอเจนต์

ClawMetry สังเกตการณ์รันไทม์เอเจนต์ AI ได้หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวมีตัวปรับอ่านเฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปทรงข้อมูลรวมของ ClawMetry แดมอนจะนำเข้าสิ่งเหล่านี้เข้าสู่ DuckDB store + สแนปช็อตคลาวด์ตัวเดียวกัน โดยติดแท็กด้วยรันไทม์ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบทั้งหมด + คู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้เบื้องต้นเกี่ยวกับตระกูล OpenClaw

กำลังใช้เครื่องมือความปลอดภัยเอเจนต์ [numbat ของ Perplexity](https://github.com/perplexityai/numbat) อยู่หรือเปล่า? ClawMetry นำเข้าผลการตรวจพบและการตัดสินใจบังคับใช้ของมันได้ทันที ดู [`docs/NUMBAT.md`](docs/NUMBAT.md)

| Runtime / Agent | สถานะ | Live Popup | หมายเหตุ |
|---|---|---|---|
| **OpenClaw** | รองรับโดยตรง | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | ตัวปรับเบต้า | `providers.Message` JSONL แบบแบน (`~/.picoclaw/workspace/sessions`) บันทึกการสนทนา โมเดล การเรียกเครื่องมือ |
| **NanoClaw** | ตัวปรับเบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) บันทึกการสนทนา + จำนวนข้อความ |
| **Hermes** | ตัวปรับเบต้า | SQLite `~/.hermes/state.db` บันทึกการสนทนา โมเดล โทเคน/ค่าใช้จ่าย |
| **Claude Code** | ตัวปรับเบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ + ความคิด การใช้โทเคน |
| **Codex** | ตัวปรับเบต้า | Rollout JSONL `~/.codex/sessions/...` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Cursor** | ตัวปรับเบต้า | SQLite `state.vscdb` บันทึกการสนทนาแบบ Chat/composer โมเดล |
| **Aider** | ตัวปรับเบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ บันทึกการสนทนา โมเดล จำนวนโทเคน |
| **Goose** | ตัวปรับเบต้า | SQLite `~/.local/share/goose` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคนรวม |
| **opencode** | ตัวปรับเบต้า | SQLite `~/.local/share/opencode` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Qwen Code** | ตัวปรับเบต้า | JSONL `~/.qwen/projects/.../chats` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ การใช้โทเคน |
| **Pi** | ตัวปรับเบต้า | JSONL `~/.pi/agent/sessions` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **Deep Agents** | ตัวปรับเบต้า | SQLite `~/.deepagents/.state/sessions.db` บันทึกการสนทนา โมเดล การเรียกเครื่องมือ โทเคน + ค่าใช้จ่าย |
| **n8n** | ตัวปรับเบต้า | SQLite `~/.n8n/database.sqlite` การทำงานของ workflow การรันโหนด พรอมต์ AI Agent โมเดล + โทเคนในกรณีที่ n8n บันทึกไว้ |
| **Antigravity** | ตัวปรับเบต้า | Brain JSONL ใต้ `~/.gemini/<flavor>/brain/` บทสนทนา ขั้นตอนเครื่องมือ ความคิด การแบ่งโทเคน Gemini ต่อการสร้าง + ค่าใช้จ่าย การใช้พลังงานจากการสร้างเบื้องหลัง |
| **GitHub Copilot** | ตัวปรับเบต้า | Copilot CLI `events.jsonl` ใต้ `~/.copilot/session-state/` + บัญชีการใช้งานต่อการเรียก `session-store.db` บทสนทนา การเรียกเครื่องมือ การกำหนดเส้นทางโมเดล การแบ่งโทเคนที่คำนึงถึงแคช ค่าใช้จ่ายเครดิต AI ที่เรียกเก็บโดยผู้ให้บริการ |
| **Grok** | ตัวปรับเบต้า | xAI Grok Build CLI (ไบนารี Rust ใต้ `~/.grok/bin/grok`): บันทึกเหตุการณ์รวม `~/.grok/logs/unified.jsonl` + ต่อเซสชัน `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` บทสนทนา การแบ่งโทเคนต่อรอบ การกำหนดเส้นทางโมเดล และเพย์โหลดรีโปที่ขาออกของ CLI ที่จัดเตรียมไว้ใต้ `~/.grok/upload_queue/` เพื่อให้คุณเห็นว่าอะไรออกจากเครื่องของคุณไปบ้าง |

"ตัวปรับเบต้า" หมายความว่า ClawMetry มีตัวอ่านสำหรับรูปแบบไฟล์บนดิสก์จริงของรันไทม์นั้น แต่ละตัวถูกสร้างขึ้น + ตรวจสอบยืนยันกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) ตัวปรับเป็นแบบอ่านอย่างเดียว และแต่ละตัวจะซื่อสัตย์กับสิ่งที่รันไทม์ของมันเก็บไว้จริง (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนค่าใช้จ่ายโทเคนลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียว ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันไปที่ตัวใดตัวหนึ่งเพื่อการเจาะลึกที่สะอาดตา

## ติดตามเอเจนต์ SDK ใดก็ได้ — การระบุค่าใช้จ่ายนอกลูป

รันไทม์ทั้งหมดด้านบนบันทึกเซสชันลงดิสก์ แต่ **เอเจนต์ที่ใช้งานจริง** ของคุณเอง ไม่ว่าจะสร้างด้วย OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา ไม่ได้ทำแบบนั้น ตัวสกัดกั้นแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียก LLM ของมันได้ (ค่าใช้จ่าย โทเคน เวลาแฝง ข้อผิดพลาด) ด้วยการแพตช์ `httpx`/`requests` แบบ monkey-patch:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) จะแท็กแต่ละการเรียกด้วย **แหล่งที่มีชื่อ** ทำให้ทุกผลิตภัณฑ์ที่คุณรันปรากฏเป็นบรรทัดของตัวเองระดับหนึ่งที่สามารถระบุค่าใช้จ่ายได้ ในการ์ด **🔌 Out-loop sources** บนแท็บ Overview ของแดชบอร์ด ทั้งจำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่าแหล่งไว้เหรอ? การเรียกยังคงถูกติดตามอยู่ เพียงแต่การ์ดจะถูกซ่อนไว้

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่คือชั้นข้อมูลเดียวกับที่ตัวปรับรันไทม์ป้อนเข้า (DuckDB → สแนปช็อตคลาวด์) ดังนั้นแหล่งที่มานอกลูปจึงซิงก์ไปยังแดชบอร์ดคลาวด์เหมือนกับทุกอย่างอื่น แบบเข้ารหัสตั้งแต่ต้นทางถึงปลายทาง

## OpenTelemetry — เป็นกลางต่อผู้ให้บริการ ส่งการติดตามไปที่ไหนก็ได้

ClawMetry พูดภาษา **OpenTelemetry** ได้ทั้งสองทิศทาง โดยใช้ **มาตรฐาน semantic conventions ของ GenAI** ดังนั้นการติดตามเอเจนต์ของคุณจะไม่ถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน ทั้งการเรียก LLM เครื่องมือ เอเจนต์ย่อย โทเคน ค่าใช้จ่าย เป็น OTLP/HTTP GenAI spans ไปยังตัวรวบรวมใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ส่วนหัวการยืนยันตัวตนและช่วงเวลาการดึงข้อมูลเป็นตัวแปรสภาพแวดล้อมที่เลือกใช้ได้:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** ตัวรับ OTLP ในตัวรับ traces, logs และ metrics จากที่อื่นได้ที่ `/v1/traces`, `/v1/logs` และ `/v1/metrics` ชี้แอปที่ตั้งค่า OpenTelemetry ไว้แล้วมาที่นี่:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

การติดตามและล็อกแบบ OTLP/JSON ใช้งานได้บน `pip install clawmetry` ธรรมดา ไม่ต้องมีส่วนเสริม การนำเข้าแบบ Protobuf (และ metrics แบบ OTLP/JSON) ต้องใช้ `pip install clawmetry[otel]` แอปที่กำหนด `service.name` ของตัวเองจะปรากฏเป็นเอเจนต์ของตัวเองในตัวสลับรันไทม์ พร้อมค่าใช้จ่ายและโทเคนของมันเอง

คุณจะได้ทั้งแดชบอร์ด ClawMetry แบบไม่ต้องตั้งค่าและทำงานในเครื่องเป็นหลัก **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมของคุณใช้งานอยู่แล้ว ไม่มีการล็อกอินและไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การกำหนดค่า

คนส่วนใหญ่ไม่ต้องตั้งค่าอะไรเลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ crons ของคุณโดยอัตโนมัติ

หากต้องการปรับแต่ง:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

ตัวเลือกทั้งหมด: `clawmetry --help`

## ช่องทางที่รองรับ

ClawMetry แสดงกิจกรรมแบบเรียลไทม์สำหรับทุกช่องทางของ OpenClaw ที่คุณตั้งค่าไว้ เฉพาะช่องทางที่ตั้งค่าไว้จริงใน `openclaw.json` ของคุณเท่านั้นที่จะปรากฏในไดอะแกรม Flow ส่วนช่องทางที่ยังไม่ได้ตั้งค่าจะถูกซ่อนโดยอัตโนมัติ

คลิกที่โหนดช่องทางใด ๆ ใน Flow เพื่อดูมุมมองฟองแชทแบบเรียลไทม์พร้อมจำนวนข้อความเข้า/ออก

| ช่องทาง | สถานะ | Live Popup | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับกิลด์ + ช่องทาง |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับเวิร์กสเปซ + ช่องทาง |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชัน web UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhooks |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอินบอท Teams |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | กระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัว NIP-04 แบบกระจายศูนย์ |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ผ่าน WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยตนเอง

## การใช้งานบน Docker

อยากรัน ClawMetry ในคอนเทนเนอร์ไหม? ไม่มีปัญหา! 🐳

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์ของคุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry ตรวจจับการตั้งค่าของคุณโดยอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- รันไทม์เอเจนต์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok หรือ QM (หรือ volume ที่ mount ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม แดมอนซิงก์จะค้นหาไฟล์เซสชันโดยอัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ด้วยสองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อดึงข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานอยู่เพื่อหาอิมเมจ `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` จากนั้นอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงก์จากคอนเทนเนอร์ NemoClaw จะถูกแท็กด้วย `runtime=nemoclaw` และข้อมูลเมตา `container_id` ในแดชบอร์ดคลาวด์ ทำให้คุณแยกแยะจากเซสชัน OpenClaw มาตรฐานได้ในทันที

### การตั้งค่าที่แนะนำ: แดมอนซิงก์บน HOST

เพื่อประสบการณ์ที่ดีที่สุด ให้รันแดมอนซิงก์ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

แดมอนซิงก์จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ทางเลือกเสริม: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

หากการตรวจจับอัตโนมัติไม่ทำงาน ให้ชี้ ClawMetry ไปยังแซนด์บ็อกซ์ที่ถูกต้อง:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### การรันภายในแซนด์บ็อกซ์ (ขั้นสูง)

หากคุณจำเป็นต้องรันแดมอนซิงก์ **ภายใน** แซนด์บ็อกซ์ OpenShell ให้เพิ่มกฎ egress นี้เข้าไปในนโยบายเครือข่าย NemoClaw ของคุณ เพื่อให้มันเข้าถึง ClawMetry ingest API ได้:

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
| `ingest.clawmetry.com` | 443 | HTTPS | ใช่ (แดมอนซิงก์ → คลาวด์) |
| `localhost:8900` | 8900 | HTTP | ใช่ (UI แดชบอร์ดในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

แดมอนซิงก์เรียกออกไปยัง `ingest.clawmetry.com` ผ่าน HTTPS เท่านั้น ไม่ต้องมีพอร์ตขาเข้า

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่ง ping วงจรชีวิตการติดตั้งแบบไม่ระบุตัวตนไปที่
`https://app.clawmetry.com/api/install`: ping `install` หนึ่งครั้งในครั้งแรก
ที่คุณรัน CLI `clawmetry` บนเครื่องใหม่ ping `update` หนึ่งครั้งใน
การรันครั้งแรกหลังจากอัปเกรดเป็นเวอร์ชันใหม่ และ ping `onboarded`
หนึ่งครั้งเมื่อคุณทำตัวเลือกการเริ่มต้นใช้งานในแดชบอร์ดเสร็จสิ้น เราใช้สิ่งนี้
เพื่อนับจำนวนการติดตั้งจริง (ตัวเลขการดาวน์โหลดดิบจาก PyPI ประมาณ 98% เป็นมิเรอร์ CI
และการดาวน์โหลดซ้ำจากการอัปเดตอัตโนมัติ) และเพื่อเรียนรู้ว่าเฟรมเวิร์กเอเจนต์และ
เวอร์ชันใดที่ถูกใช้งานจริงอยู่บ้าง

**สูงสุดหนึ่ง POST ต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันการนับซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อการซิงก์คลาวด์อย่างชัดเจน (heartbeat ของแดมอนที่ยืนยันตัวตนแล้วจะนำพามันไป เชื่อมโยงการติดตั้งนี้กับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | การติดตั้งใหม่เทียบกับการอัปเกรดจากของเดิม |
| `version` | `0.12.167` | เวอร์ชันใดบ้างที่ถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญในการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | ตารางการรองรับเวอร์ชัน Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ใดที่เราควรผนวกรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนจาก CI |

**สิ่งที่เราไม่ส่ง**: IP (คลาวด์จะดึงรหัสประเทศจากฝั่งเซิร์ฟเวอร์
จากคำขอ แล้วทิ้ง IP นั้นไป) ชื่อโฮสต์ ชื่อผู้ใช้ พาธพื้นที่ทำงาน
เนื้อหาไฟล์ api_key ของคุณ อีเมลของคุณ หรือสิ่งใดที่เป็นข้อมูลส่วนบุคคลหรือเฉพาะพื้นที่ทำงาน เพย์โหลดที่ส่งผ่านสายสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**เลือกไม่เข้าร่วม** (วิธีใดวิธีหนึ่งต่อไปนี้จะปิดใช้งานถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายที่นี่จะไม่บล็อก `clawmetry` จากการทำงานเลย ping นี้
เป็นแบบยิงแล้วลืมบนเธรดแดมอนที่มี timeout 3 วินาที

## ประวัติดวงดาว

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
