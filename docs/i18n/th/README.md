<!-- i18n-src:7cfb63716507 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูสิ่งที่เอเจนต์ของคุณกำลังคิด** สังเกตการณ์แบบเรียลไทม์สำหรับ **รันไทม์เอเจนต์ AI 14 ตัว**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 10 ตัว แดชบอร์ดเดียวสำหรับเอเจนต์ทั้งฟลีทของคุณ

> 🌐 **อ่านภาษานี้:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าอะไร ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** แล้วก็เสร็จเรียบร้อย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ทำงานร่วมกับรันไทม์เอเจนต์ 14 ตัว

ClawMetry เริ่มต้นจากการสังเกตการณ์สำหรับ OpenClaw และตอนนี้ได้ขยายไปวัดผล **ฟลีทเอเจนต์ทั้งหมด** ของคุณในแดชบอร์ดเดียว โดยตรวจจับรันไทม์แต่ละตัวบนเครื่องของคุณโดยอัตโนมัติ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw และ NemoClaw ใช้งานได้ฟรีในแอปโอเพนซอร์ส ส่วนรันไทม์อื่น ๆ จะเปิดใช้งานได้ด้วย ClawMetry Cloud หรือใบอนุญาต Pro แบบโฮสต์เอง สลับรันไทม์ได้จากส่วนหัว และทุกแท็บ ทั้งต้นทุน โทเค็น เครื่องมือ และ trace จะปรับขอบเขตไปตามรันไทม์นั้น ดูรายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอน ตารางระดับชั้น รูปแบบ `/api/entitlement` และ CLI `clawmetry license` ได้ที่ **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**

## สิ่งที่คุณจะได้รับ

- **Flow** — แผนภาพเคลื่อนไหวแบบเรียลไทม์แสดงข้อความที่ไหลผ่านช่องทาง สมอง เครื่องมือ และย้อนกลับ
- **Overview** — การตรวจสอบสุขภาพระบบ heatmap กิจกรรม จำนวนเซสชัน ข้อมูลโมเดล
- **Usage** — การติดตามโทเค็นและต้นทุนพร้อมรายละเอียดรายวัน/รายสัปดาห์/รายเดือน
- **Sessions** — เซสชันเอเจนต์ที่กำลังทำงานอยู่พร้อมโมเดล โทเค็น กิจกรรมล่าสุด
- **Crons** — งานที่ตั้งเวลาไว้พร้อมสถานะ รอบถัดไป ระยะเวลา
- **Logs** — สตรีมล็อกเรียลไทม์แบบมีสี
- **Memory** — เรียกดู SOUL.md, MEMORY.md, AGENTS.md, บันทึกประจำวัน
- **Transcripts** — UI แบบฟองแชทสำหรับอ่านประวัติเซสชัน
- **Alerts** — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด ตรวจจับเอเจนต์ที่ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — กันการลบข้อมูลที่ทำลายล้าง force push การเปลี่ยนแปลงฐานข้อมูล sudo การติดตั้งแพ็กเกจ และการเรียกเครือข่าย ไว้หลังการอนุมัติแบบคลิกเดียว

## ภาพหน้าจอ

### 🧠 Brain — สตรีมเหตุการณ์เอเจนต์แบบสด
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — การใช้งานโทเค็นและสรุปเซสชัน
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ฟีดการเรียกใช้เครื่องมือแบบเรียลไทม์
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — รายละเอียดต้นทุนตามโมเดลและเซสชัน
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ตัวเรียกดูไฟล์ในพื้นที่ทำงาน
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ท่าทีความปลอดภัยและบันทึกการตรวจสอบ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — เพดานงบประมาณ ตัวกระตุ้นอัตราข้อผิดพลาด webhook ไปยัง Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — กันการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้หลังการอนุมัติด้วยตนเอง กฎการป้องกันที่อ้างอิงตามนโยบาย
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**การบล็อกก่อนดำเนินการสำหรับ Claude Code** — คำสั่งเดียวติดตั้ง
hook PreToolUse ที่หยุดการเรียกใช้เครื่องมือที่ตรงเงื่อนไข *ก่อน* ที่จะทำงานจริง และรอ
การตัดสินใจของคุณ (แตะครั้งเดียวจากโทรศัพท์ด้วย
[การแจ้งเตือนแบบพุชบนคลาวด์](https://app.clawmetry.com/push) ที่เปิดใช้งานอยู่):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

การปฏิเสธจะบล็อกเฉพาะการเรียกใช้เครื่องมือครั้งนั้น เอเจนต์ยังคงมีเซสชันของมันอยู่และสามารถ
ลองวิธีอื่นได้ การอนุมัติจากโทรศัพท์ของคุณจะข้ามพร้อมท์การอนุญาตของ Claude Code เอง
(คุณตอบไปแล้ว) เครื่องมือที่ไม่ตรงเงื่อนไขใช้เวลาประมาณ 40ms และ
ตกไปที่โฟลว์การอนุญาตปกติของ Claude Code คุณยังได้รับการแจ้งเตือนบนโทรศัพท์เมื่อ Claude Code เองกำลังรอคุณอยู่
(การแจ้งเตือน `permission_prompt` / `idle_prompt`)

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

แอป React ตัว v2 อยู่ที่ `frontend/` และให้บริการที่ `/v2` เมื่อ Flask
server ถูกเริ่มต้นด้วยการเปิดใช้งาน v2

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

เปิด `http://localhost:5173/v2/` Vite จะ proxy คำขอ `/api` ไปยัง
`http://localhost:8900` ทำให้แอป React สามารถสื่อสารกับ Flask server ในเครื่อง
ได้โดยไม่ต้องตั้งค่า CORS เพิ่มเติม

หากต้องการ build ชุดไฟล์ที่จะแพ็กไปกับแพ็กเกจ Python:

```bash
cd frontend
npm run build
```

ชุดไฟล์ production จะถูกเขียนไปที่ `clawmetry/static/v2/dist/`

## ความเข้ากันได้ของรันไทม์/เอเจนต์

ClawMetry สังเกตการณ์รันไทม์เอเจนต์ AI หลายตัว ไม่ใช่แค่ OpenClaw รันไทม์ที่ไม่ใช่ OpenClaw แต่ละตัวมี reader adapter เฉพาะที่แปลงรูปแบบเซสชันดั้งเดิมของมันให้เป็นรูปแบบมาตรฐานของ ClawMetry โดย daemon จะรวบรวมข้อมูลเหล่านี้เข้าไปยัง DuckDB store + cloud snapshot ตัวเดียวกัน พร้อมติดแท็กรันไทม์ไว้ และแท็บ Session replay จะแสดง **ตัวสลับรันไทม์** เมื่อมีมากกว่าหนึ่งรันไทม์อยู่ ดู [`docs/compatibility.md`](docs/compatibility.md) สำหรับตารางเปรียบเทียบฉบับเต็ม + คู่มือการเพิ่มรันไทม์ และ [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) สำหรับความรู้เบื้องต้นเกี่ยวกับตระกูล OpenClaw

กำลังใช้เครื่องมือความปลอดภัยเอเจนต์ [numbat ของ Perplexity](https://github.com/perplexityai/numbat) อยู่หรือไม่? ClawMetry นำผลการตรวจพบและการตัดสินใจบังคับใช้ของมันเข้ามาได้ทันที ดู [`docs/NUMBAT.md`](docs/NUMBAT.md)

| รันไทม์/เอเจนต์ | สถานะ | หมายเหตุ |
|---|---|---|
| **OpenClaw** | เนทีฟ | รันไทม์อ้างอิง ตรวจจับอัตโนมัติ |
| **PicoClaw** | Adapter เบต้า | `providers.Message` JSONL แบบเรียบ (`~/.picoclaw/workspace/sessions`) ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ |
| **NanoClaw** | Adapter เบต้า | SQLite ต่อเซสชัน (`data/v2-sessions`) ประวัติสนทนา + จำนวนข้อความ |
| **Hermes** | Adapter เบต้า | SQLite `~/.hermes/state.db` ประวัติสนทนา โมเดล โทเค็น/ต้นทุน |
| **Claude Code** | Adapter เบต้า | JSONL `~/.claude/projects/.../<id>.jsonl` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ + การคิด การใช้งานโทเค็น |
| **Codex** | Adapter เบต้า | Rollout JSONL `~/.codex/sessions/...` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ การใช้งานโทเค็น |
| **Cursor** | Adapter เบต้า | SQLite `state.vscdb` ประวัติสนทนาแบบแชท/composer โมเดล |
| **Aider** | Adapter เบต้า | `.aider.chat.history.md` ต่อโปรเจกต์ ประวัติสนทนา โมเดล จำนวนโทเค็น |
| **Goose** | Adapter เบต้า | SQLite `~/.local/share/goose` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ จำนวนโทเค็นรวม |
| **opencode** | Adapter เบต้า | SQLite `~/.local/share/opencode` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ โทเค็น + ต้นทุน |
| **Qwen Code** | Adapter เบต้า | JSONL `~/.qwen/projects/.../chats` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ การใช้งานโทเค็น |
| **Pi** | Adapter เบต้า | JSONL `~/.pi/agent/sessions` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ โทเค็น + ต้นทุน |
| **Deep Agents** | Adapter เบต้า | SQLite `~/.deepagents/.state/sessions.db` ประวัติสนทนา โมเดล การเรียกใช้เครื่องมือ โทเค็น + ต้นทุน |
| **n8n** | Adapter เบต้า | SQLite `~/.n8n/database.sqlite` การรัน workflow การรัน node พรอมต์ AI Agent โมเดล + โทเค็นในกรณีที่ n8n บันทึกไว้ |
| **Antigravity** | Adapter เบต้า | Brain JSONL ภายใต้ `~/.gemini/<flavor>/brain/` บทสนทนา ขั้นตอนเครื่องมือ การคิด การแบ่งโทเค็น Gemini ต่อการสร้างพร้อมต้นทุน การเผาผลาญจากการสร้างในพื้นหลัง |
| **GitHub Copilot** | Adapter เบต้า | Copilot CLI `events.jsonl` ภายใต้ `~/.copilot/session-state/` + สมุดบัญชีการใช้งานต่อการเรียก `session-store.db` บทสนทนา การเรียกใช้เครื่องมือ การจัดเส้นทางโมเดล การแบ่งโทเค็นที่คำนึงถึงแคช ต้นทุนเครดิต AI ที่เรียกเก็บโดยผู้ให้บริการ |
| **Grok** | Adapter เบต้า | xAI Grok Build CLI (ไบนารี Rust ภายใต้ `~/.grok/bin/grok`): บันทึกเหตุการณ์ส่วนกลาง `~/.grok/logs/unified.jsonl` + ต่อเซสชัน `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` บทสนทนา การแบ่งโทเค็นต่อรอบ การจัดเส้นทางโมเดล และ payload ของ repo ที่ CLI ส่งออกซึ่งจัดเตรียมไว้ที่ `~/.grok/upload_queue/` ให้คุณเห็นว่ามีอะไรออกจากเครื่องคุณบ้าง |

"Adapter เบต้า" หมายความว่า ClawMetry มี reader สำหรับรูปแบบไฟล์บนดิสก์จริงของรันไทม์นั้น แต่ละตัวถูกสร้างขึ้นและตรวจสอบยืนยันกับการติดตั้งจริงบนเครื่องจริง (ดู `tests/fixtures/runtimes/<rt>/`) Adapter เป็นแบบอ่านอย่างเดียว แต่ละตัวจะซื่อสัตย์กับสิ่งที่รันไทม์นั้นเก็บไว้จริง ๆ (เช่น PicoClaw/NanoClaw/Cursor ไม่ได้เขียนต้นทุนโทเค็นลงดิสก์) เมื่อมีหลายรันไทม์ทำงานบนโหนดเดียวกัน ตัวสลับรันไทม์จะจำกัดขอบเขตมุมมองเซสชันไปที่ตัวเดียวเพื่อการเจาะลึกที่สะอาดตา

## ติดตามเอเจนต์ SDK ใดก็ได้ — การระบุที่มาของต้นทุนแบบ out-loop

รันไทม์ทั้งหมดข้างต้นเขียนเซสชันลงดิสก์ แต่ **เอเจนต์ production** ของคุณเอง ที่คุณสร้างขึ้นบน OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B หรือลูป `httpx` ธรรมดา ไม่ได้ทำแบบนั้น ตัวดักจับแบบไม่ต้องตั้งค่าของ ClawMetry ยังคงจับการเรียก LLM ของมัน (ต้นทุน โทเค็น เวลาแฝง ข้อผิดพลาด) ได้ด้วยการ monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (หรือตัวแปรสภาพแวดล้อม `CLAWMETRY_SOURCE=support-agent`) ติดแท็กแต่ละการเรียกด้วย **แหล่งที่มาที่มีชื่อ** ดังนั้นทุกผลิตภัณฑ์ที่คุณรันจะปรากฏเป็นบรรทัดของตัวเองที่ระบุต้นทุนได้เต็มรูปแบบใน การ์ด **🔌 Out-loop sources** บนแท็บ Overview ของแดชบอร์ด แสดงจำนวนการเรียก ผู้ให้บริการ เวลาแฝง อัตราข้อผิดพลาดต่อเอเจนต์ ไม่ได้ตั้งค่า source ไว้หรือ? การเรียกก็ยังถูกติดตามอยู่ เพียงแต่การ์ดจะซ่อนอยู่

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

นี่เป็นชั้นข้อมูลเดียวกับที่ runtime adapter ป้อนเข้ามา (DuckDB → cloud snapshot) ดังนั้น out-loop sources จึงซิงค์ไปยังแดชบอร์ดบนคลาวด์เหมือนกับทุกอย่างอื่น แบบเข้ารหัสตั้งแต่ต้นทางถึงปลายทาง

## OpenTelemetry — เป็นกลางต่อผู้ให้บริการ ส่ง trace ของคุณไปที่ไหนก็ได้

ClawMetry รองรับ **OpenTelemetry** ทั้งสองทิศทาง โดยใช้ **GenAI semantic conventions** ดังนั้น trace ของเอเจนต์คุณจะไม่ถูกล็อกไว้กับเครื่องมือใดเครื่องมือหนึ่ง

**ส่งออก** ทุกเซสชัน การเรียก LLM เครื่องมือ เอเจนต์ย่อย โทเค็น ต้นทุน เป็น OTLP/HTTP GenAI spans ไปยัง collector ใดก็ได้ (Datadog, Grafana, Honeycomb หรือ OTel Collector ของคุณเอง):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth header และช่วงเวลา poll เป็นตัวแปรสภาพแวดล้อมที่เลือกใช้ได้:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**นำเข้า** — ตัวรับ OTLP ในตัวรับ trace และ metric จากที่อื่นได้ที่ `/v1/traces` และ `/v1/metrics` (`pip install clawmetry[otel]` สำหรับการนำเข้าแบบ protobuf)

คุณจะได้ทั้งแดชบอร์ด ClawMetry ที่ไม่ต้องตั้งค่าและใช้งานได้แบบโลคัลก่อน **และ** ข้อมูลของคุณในแบ็กเอนด์ใดก็ตามที่ทีมคุณใช้อยู่แล้ว ไม่มีการล็อกอิน ไม่ต้องติดตั้งเอเจนต์ตัวที่สอง

## การตั้งค่า

คนส่วนใหญ่ไม่ต้องตั้งค่าอะไรเลย ClawMetry ตรวจจับพื้นที่ทำงาน ล็อก เซสชัน และ cron ของคุณโดยอัตโนมัติ

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

คลิกที่ node ของช่องทางใด ๆ ใน Flow เพื่อดูมุมมองฟองแชทแบบสดพร้อมจำนวนข้อความเข้า/ออก

| ช่องทาง | สถานะ | Live Popup | หมายเหตุ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ เต็มรูปแบบ | ✅ | ข้อความ สถิติ รีเฟรชทุก 10 วินาที |
| 💬 **iMessage** | ✅ เต็มรูปแบบ | ✅ | อ่าน `~/Library/Messages/chat.db` โดยตรง |
| 💚 **WhatsApp** | ✅ เต็มรูปแบบ | ✅ | ผ่าน WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ เต็มรูปแบบ | ✅ | ผ่าน signal-cli |
| 🟣 **Discord** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ guild + channel |
| 🟪 **Slack** | ✅ เต็มรูปแบบ | ✅ | ตรวจจับ workspace + channel |
| 🌐 **Webchat** | ✅ เต็มรูปแบบ | ✅ | เซสชันจาก web UI ในตัว |
| 📡 **IRC** | ✅ เต็มรูปแบบ | ✅ | UI ฟองแชทสไตล์เทอร์มินัล |
| 🍏 **BlueBubbles** | ✅ เต็มรูปแบบ | ✅ | iMessage ผ่าน BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ เต็มรูปแบบ | ✅ | ผ่าน Chat API webhook |
| 🟣 **MS Teams** | ✅ เต็มรูปแบบ | ✅ | ผ่านปลั๊กอิน Teams bot |
| 🔷 **Mattermost** | ✅ เต็มรูปแบบ | ✅ | แชททีมแบบโฮสต์เอง |
| 🟩 **Matrix** | ✅ เต็มรูปแบบ | ✅ | แบบกระจายศูนย์ รองรับ E2EE |
| 🟢 **LINE** | ✅ เต็มรูปแบบ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ เต็มรูปแบบ | ✅ | ข้อความส่วนตัวแบบกระจายศูนย์ NIP-04 |
| 🟣 **Twitch** | ✅ เต็มรูปแบบ | ✅ | แชทผ่านการเชื่อมต่อ IRC |
| 🔷 **Feishu/Lark** | ✅ เต็มรูปแบบ | ✅ | การสมัครสมาชิกเหตุการณ์ WebSocket |
| 🔵 **Zalo** | ✅ เต็มรูปแบบ | ✅ | Zalo Bot API |

> **การตรวจจับอัตโนมัติ:** ClawMetry อ่าน `~/.openclaw/openclaw.json` ของคุณ และแสดงผลเฉพาะช่องทางที่คุณตั้งค่าไว้จริงเท่านั้น ไม่ต้องตั้งค่าด้วยตนเอง

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

> **หมายเหตุ:** เมื่อรันใน Docker ให้ mount ไดเรกทอรีข้อมูล + ล็อกของเอเจนต์คุณ (เช่น `~/.openclaw`, `~/.claude`, `~/.codex`) เพื่อให้ ClawMetry ตรวจจับการตั้งค่าของคุณได้โดยอัตโนมัติ

## ความต้องการของระบบ

- Python 3.8+
- Flask (ติดตั้งอัตโนมัติผ่าน pip)
- รันไทม์เอเจนต์ AI บนเครื่องเดียวกัน: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok หรือ QM (หรือ volume ที่ mount ไว้สำหรับ Docker)
- Linux หรือ macOS

## การรองรับ NemoClaw / OpenShell

ClawMetry ตรวจจับ [NemoClaw](https://github.com/NVIDIA/NemoClaw) โดยอัตโนมัติ ซึ่งเป็นตัวห่อความปลอดภัยระดับองค์กรของ NVIDIA สำหรับ OpenClaw ที่รันเอเจนต์ภายในคอนเทนเนอร์ OpenShell แบบแซนด์บ็อกซ์

ในกรณีส่วนใหญ่ไม่จำเป็นต้องตั้งค่าเพิ่มเติม sync daemon จะค้นหาไฟล์เซสชันโดยอัตโนมัติ ไม่ว่าจะอยู่ใน `~/.openclaw/` บนโฮสต์หรือภายในคอนเทนเนอร์ OpenShell

### วิธีการทำงาน

ClawMetry ตรวจจับ NemoClaw ได้สองวิธี:

1. **การตรวจจับไบนารี** — ตรวจสอบ CLI `nemoclaw` และรัน `nemoclaw status` เพื่อรับข้อมูลแซนด์บ็อกซ์
2. **การตรวจจับคอนเทนเนอร์** — สแกนคอนเทนเนอร์ Docker ที่กำลังทำงานเพื่อหา image ที่เป็น `openshell`, `nemoclaw` หรือ `ghcr.io/nvidia/` แล้วอ่านเซสชันผ่าน volume mount หรือ `docker cp`

ไฟล์เซสชันที่ซิงค์จากคอนเทนเนอร์ NemoClaw จะถูกติดแท็กด้วย `runtime=nemoclaw` และเมทาดาทา `container_id` ในแดชบอร์ดคลาวด์ เพื่อให้คุณแยกแยะได้จากเซสชัน OpenClaw มาตรฐานได้ในพริบตา

### การตั้งค่าที่แนะนำ: sync daemon บนโฮสต์

เพื่อประสบการณ์ที่ดีที่สุด ให้รัน sync daemon ของ ClawMetry บน **เครื่องโฮสต์** (ไม่ใช่ภายในแซนด์บ็อกซ์) วิธีนี้จะหลีกเลี่ยงข้อจำกัดของนโยบายเครือข่ายของ NemoClaw

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon จะค้นหาเซสชันภายในคอนเทนเนอร์ OpenShell ที่กำลังทำงานอยู่โดยอัตโนมัติ

### ตัวเลือก: ระบุชื่อแซนด์บ็อกซ์อย่างชัดเจน

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
| `localhost:8900` | 8900 | HTTP | ใช่ (แดชบอร์ด UI ในเครื่อง) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | สำหรับการค้นหาเซสชันในคอนเทนเนอร์ |

sync daemon จะเรียก HTTPS ออกไปยัง `ingest.clawmetry.com` เท่านั้น ไม่จำเป็นต้องมีพอร์ตขาเข้าใด ๆ

---

## การใช้งานบนคลาวด์

ดู **[คู่มือการทดสอบคลาวด์](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** สำหรับ SSH tunnel, reverse proxy และ Docker

## การทดสอบ

โปรเจกต์นี้ทดสอบด้วย BrowserStack

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry ส่ง ping แบบไม่ระบุตัวตนเกี่ยวกับวงจรชีวิตการติดตั้งไปยัง
`https://app.clawmetry.com/api/install`: ping `install` หนึ่งครั้งในการรัน
CLI `clawmetry` ครั้งแรกบนเครื่องใหม่ ping `update` หนึ่งครั้งในการรันครั้งแรก
หลังจากอัปเกรดไปเป็นเวอร์ชันใหม่ และ ping `onboarded` หนึ่งครั้งเมื่อคุณทำตัวเลือก
onboarding ในแดชบอร์ดเสร็จสิ้น เราใช้ข้อมูลนี้ในการนับจำนวนการติดตั้งจริง
(ตัวเลขการดาวน์โหลดดิบจาก PyPI ประมาณ 98% เป็น mirror, CI และการดาวน์โหลดซ้ำจาก
auto-update) และเพื่อเรียนรู้ว่าเฟรมเวิร์กและเวอร์ชันของเอเจนต์ใดที่กำลังถูกใช้งานจริง

**สูงสุดหนึ่ง POST ต่อเหตุการณ์วงจรชีวิตต่อเวอร์ชัน** ประกอบด้วย:

| ฟิลด์ | ตัวอย่าง | เหตุผล |
|---|---|---|
| `install_id` | UUID สุ่มที่เก็บไว้ที่ `~/.clawmetry/install_id` | ป้องกันข้อมูลซ้ำ ไม่ระบุตัวตนจนกว่าคุณจะเชื่อมต่อ Cloud sync อย่างชัดเจน (heartbeat ของ daemon ที่ผ่านการยืนยันตัวตนแล้วจึงจะพาข้อมูลนี้ไป เชื่อมโยงการติดตั้งนี้กับบัญชีของคุณ) |
| `event` | `install` / `update` / `onboarded` | การติดตั้งใหม่เทียบกับการอัปเกรดของที่มีอยู่แล้ว |
| `version` | `0.12.167` | เวอร์ชันใดที่กำลังถูกใช้งานอยู่ |
| `os` / `os_version` | `Darwin` / `25.3.0` | ลำดับความสำคัญของการรองรับแพลตฟอร์ม |
| `python` | `3.11.15` | ตารางเวอร์ชัน Python ที่รองรับ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | เอเจนต์ใดที่เราควรผสานรวมต่อไป |
| `is_ci` / `ci_provider` | `true` / `github_actions` | แยกการติดตั้งของมนุษย์ออกจากสัญญาณรบกวนของ CI |

**สิ่งที่เราไม่ส่ง**: IP (ฝั่งคลาวด์คำนวณรหัสประเทศจากคำขอฝั่งเซิร์ฟเวอร์
แล้วทิ้ง IP ทันที) ชื่อโฮสต์ ชื่อผู้ใช้ พาธของพื้นที่ทำงาน เนื้อหาไฟล์
api_key ของคุณ อีเมลของคุณ หรือสิ่งใดก็ตามที่เป็น PII หรือเฉพาะเจาะจงกับพื้นที่ทำงาน
payload ที่ส่งผ่านสายสามารถตรวจสอบได้ที่
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)

**การยกเลิก** (ทำวิธีใดวิธีหนึ่งต่อไปนี้เพื่อปิดถาวร):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ความล้มเหลวของเครือข่ายที่นี่จะไม่มีวันบล็อก `clawmetry` จากการทำงาน ping นี้
เป็นแบบ fire-and-forget บน daemon thread ที่มี timeout 3 วินาที

## ประวัติดวงดาว

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
