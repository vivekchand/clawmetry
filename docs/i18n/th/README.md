<!-- i18n-src:9767c8001c9c -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูความคิดของเอเจนต์ของคุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **30 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 26 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านเป็นภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างเองโดยอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใด ๆ: มันจะค้นหา agent runtime
ที่คุณมีอยู่แล้ว อ่านแบบ read-only เท่านั้น และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ใช้งานได้กับ 30 agent runtimes

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**บนแพลนแบบเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุก runtime ใช้แดชบอร์ดเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัว
จะปรับทุกแท็บให้อ้างอิงกับ runtime ตัวใดตัวหนึ่งได้

สร้างเอเจนต์ของคุณเองบน SDK แทนหรือเปล่า? ตัว interceptor ก็ติดตามการเรียก LLM
ของมันด้วยเช่นกัน ดูที่ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **Sessions & transcripts**: สิ่งที่เอเจนต์แต่ละตัวทำ ทีละเทิร์น พร้อมการ replay
- **ต้นทุนและโทเคน**: แยกตาม runtime, โมเดล, session และวัน พร้อมสัญญาณผิดปกติ
- **Flow**: แผนภาพแบบเรียลไทม์ของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือต่าง ๆ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบเรียลไทม์
- **Context blowout**: การใช้งานหน้าต่างบริบทที่คำนวณตามผู้ให้บริการแต่ละราย compaction เทียบกับ overflow ที่ถูกบังคับ พร้อมแผนที่ต่อ runtime ว่าเรา *มองไม่เห็น* อะไรบ้าง ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: ไฟล์และสกิลที่แต่ละ runtime โหลดขึ้นมาใช้งานจริง
- **Health & logs**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด rate limit สตรีม log แบบสด
- **Alerts**: เพดานงบประมาณ ข้อผิดพลาดพุ่งสูง เอเจนต์ออฟไลน์ ส่งต่อไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะรัน และอนุมัติได้จากมือถือของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการเฝ้าติดตาม

สองคำถามที่ควรตอบให้ได้ก่อนที่คุณจะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ตัวใดก็ตาม

**มันจัดการกับ context-window blowout ข้าม runtime ต่าง ๆ ได้อย่างไร?**

ค่าเปอร์เซ็นต์การใช้งานจะน่าเชื่อถือได้ก็ต่อเมื่อสิ่งที่นำมาหารนั้นถูกต้อง ClawMetry
คำนวณขนาดหน้าต่างตามผู้ให้บริการแต่ละรายจาก[ตารางที่คุณอ่านและ
ส่ง PR ได้](clawmetry/context_windows.py) ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดทั้ง 26
runtime ด้วยไม้บรรทัดของผู้ให้บริการรายเดียว นั่นสำคัญ: เทิร์นของ GPT-5 ขนาด 300K
ที่ถูกวัดเทียบกับ 200K ของ Anthropic จะอ่านว่า ">100%, blown" ทั้งที่จริงแล้วอยู่ที่
75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็จะซ่อนเทิร์นของ DeepSeek ขนาด 130K
ที่ overflow จริง ๆ ให้ดูเหมือนสบาย ๆ ที่ 65%

หน้าต่างทุกอันมาพร้อมที่มาของมัน: `model_table`, `explicit_marker`,
`observed_floor`, หรือค่า `default` ที่ตรงไปตรงมาเมื่อเราไม่รู้จักโมเดลนั้น
มาตรวัดที่สร้างจากการเดาจะไม่มีวันแสดงผลด้วยความน่าเชื่อถือเท่ากับ
มาตรวัดที่สร้างจากการค้นหาข้อมูลจริง

ClawMetry มองเห็นเหตุการณ์ compaction ได้เฉพาะบาง runtime เท่านั้น ดังนั้น
`GET /api/context-coverage` จึงรายงานต่อ runtime ว่า**ค่า 0 หมายถึง
"ทำงานได้ราบรื่น" หรือ "เรามองไม่เห็น"** ค่า `0` ที่จริง ๆ แล้วหมายถึงมองไม่เห็นก็จะบอกไว้ตรง ๆ
[รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**เครื่องมือวัดนี้มีต้นทุนเท่าไร?**

| เส้นทาง | เพิ่มเข้าไปในเอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การ tail ไฟล์ session (ครบทั้ง 30 runtime) | **0** เป็นโปรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry อยู่ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (แคชอุ่นแล้ว) | **+44 มิลลิวินาที** ต่อการเรียกใช้เครื่องมือที่ถูก gate หนึ่งครั้ง เหนือพื้นฐาน interpreter 36 มิลลิวินาที | ปิด |
| Enforcement proxy | **+9.7 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง | ปิด |

ต้นทุนของโฮสต์เดมอน: รับข้อมูลเข้า **2,762 เหตุการณ์/วินาที** ใช้พื้นที่ดิสก์
**710 ไบต์/เหตุการณ์** (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ประมาณ 12% ของหนึ่งคอร์**
อย่างต่อเนื่องบนการติดตั้งที่มีงานหนัก ตัวเลขหลังนี้เกินงบประมาณ 5-10% ที่เราตั้งไว้เอง
ดังนั้นจึงถูกเผยแพร่ในฐานะบั๊กที่ต้องไล่แก้ ไม่ใช่ถูกละไว้ไม่พูดถึง

วัดบน Apple M2 Pro ด้วย `benchmarks/overhead.py` ฮาร์เนสจะรันแต่ละเงื่อนไข
ในโปรเซสแยกกัน สลับลำดับกันไปมา และ**ปฏิเสธที่จะพิมพ์ตัวเลขออกมาเมื่อ
รอบต่าง ๆ ให้ผลลัพธ์ที่เครื่องหมาย (บวก/ลบ) ไม่ตรงกัน** รันได้เองบนเครื่องของคุณ
ภายในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดผล รวมถึง hook gate และ enforcement proxy ด้วย
และฮาร์เนสรันบน Linux, macOS และ Windows ใน CI มีผลลัพธ์สองอย่างที่ควรรู้ไว้:
proxy มีต้นทุนสูงกว่าบน Windows ประมาณเจ็ดเท่าเมื่อเทียบกับ Linux และตอนนี้
เดมอนใช้งานอย่างต่อเนื่องอยู่ที่ประมาณ 12% ของหนึ่งคอร์ ซึ่งเกินงบประมาณ 5-10%
ที่เราตั้งไว้เอง ข้อมูล JSON ดิบ วิธีการ และสิ่งที่ยังไม่ได้วัดอยู่ที่
[docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แพลน | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ ใช้งานได้เฉพาะในเครื่องเท่านั้น | $0 |
| **Starter** | runtime อื่นทั้งหมดที่กล่าวมาข้างต้น มุมมองแบบ fleet, cloud sync | $9 ต่อโหนด/เดือน |
| **Pro** | Starter + การควบคุมและการประเมินผล: approvals, นโยบายความเสี่ยงของเครื่องมือ, evals, การตรวจจับความผิดปกติ, cost optimizer, การส่งออก OTel, บันทึกการตรวจสอบที่ป้องกันการปลอมแปลง | $19 ต่อโหนด/เดือน |

แพลนรายปี, Enterprise และตัวเลขปัจจุบันดูได้ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** license key แบบ self-hosted
ใช้งานได้โดยไม่ต้องใช้ระบบคลาวด์ (`clawmetry license`) รายละเอียดที่แน่ชัดของการแบ่งฟรี/เสียเงิน
อยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์ session และ log ในเครื่อง **ไม่มีข้อมูล session ใดออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** ไม่ว่าจะเป็นพรอมต์ คำตอบ อาร์กิวเมนต์ของเครื่องมือ
เนื้อหาไฟล์ หรือบรรทัด log ใด ๆ เมื่อคุณเชื่อมต่อ สแนปช็อตจะถูกเข้ารหัสแบบ end-to-end
ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัสในเบราว์เซอร์ของคุณ ถ้าโหนดใดไม่มีคีย์
การอัปโหลดจะถูกข้ามไปแทนที่จะส่งแบบไม่เข้ารหัส และไม่มีการตอบกลับจากเซิร์ฟเวอร์ใดที่จะปิดพฤติกรรมนี้ได้

มีสองสิ่งที่ทำงานโดยค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งสองอย่างเป็นแบบ opt-out และ
ไม่มีสิ่งใดที่พาข้อมูล session ไปด้วย: การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชัน
เทียบกับ PyPI การติดตั้งแบบค่าเริ่มต้นยังค้นหา public IP ของคุณครั้งเดียวสำหรับ
บรรทัดแบนเนอร์ตอนเริ่มต้น ปลายทางแต่ละแห่ง สิ่งที่มันพาไปด้วย และวิธีปิดมัน
ถูกระบุไว้ทั้งหมดใน [docs/EGRESS.md](docs/EGRESS.md); การติดตั้งแบบ self-hosted, repointed
และ air-gapped จะไม่มีการเรียกออกไปภายนอกตามดุลยพินิจเลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราส่งให้คุณ นี่เคยเป็นแค่คำสัญญา
แต่ตอนนี้เป็นสิ่งที่คุณตรวจสอบได้ ทุกบรรทัดที่แตะต้องคีย์ของคุณอยู่ในไฟล์เดียวที่อ่านได้
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งมาพร้อมกับ wheel และถูกให้บริการตรงตามต้นฉบับ พร้อม pin ด้วยแฮช Subresource
Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่ไว้จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่มันไม่ได้พิสูจน์คือ: เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้ ดังนั้นเราจึงอาจ
ให้บริการหน้าเว็บที่แตกต่างออกไปได้ แฮช integrity ปกป้องคุณจาก CDN ที่ถูกบุกรุก
ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้รับคือการเปลี่ยนแปลงใด ๆ จะต้องเกิดขึ้นโดยตั้งใจ
มองเห็นได้ในซอร์สโค้ดของหน้าเว็บ และแตกต่างจากอาร์ทิแฟกต์บน PyPI ที่ใครก็สามารถดึงมาได้
การ self-host หรืออยู่แบบ local-only เท่านั้นจะขจัดการพึ่งพานี้ออกไปได้ทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือใช้คำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องมี Python 3.8 ขึ้นไปบน macOS, Linux หรือ Windows และ agent runtime อย่างน้อยหนึ่งตัว
อยู่บนเครื่องเดียวกัน คำแนะนำสำหรับ Docker: [docs/DOCKER.md](docs/DOCKER.md)

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของ Runtime](docs/compatibility.md) | สิ่งที่แต่ละ adapter อ่าน และวิธีเพิ่ม runtime ใหม่ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างตามผู้ให้บริการแต่ละราย compaction เทียบกับ overflow และความครอบคลุมตาม runtime |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของเครื่องมือวัด พร้อมค่าที่วัดได้จริง และฮาร์เนสสำหรับทำซ้ำ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน, ตารางระดับแพลน, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | การ gate ก่อนการรัน, การให้คะแนนความเสี่ยง, การอนุมัติผ่านมือถือ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก trace ไปที่ไหนก็ได้ รับ OTLP เข้ามาจากอะไรก็ได้ |
| [นำเอเจนต์ของคุณเองมาใช้](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้จริง |
| [SDK tracking](docs/SDK_TRACKING.md) | การนับต้นทุนสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [Chat channels](docs/CHANNELS.md) | ตัวปรับ chat ที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบ sandboxed |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน; การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การ ping แบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

ตัวเลขทุกตัวด้านล่างนี้มาจากเครื่องจริงเครื่องหนึ่ง แบบ read-only ไม่มีการปลูกข้อมูลใด ๆ ล่วงหน้า

**มันบอกคุณเมื่อมีอะไรผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่วิ่งสูงกว่าค่าเฉลี่ยรายวันถึง 7 เท่า
และการพุ่งขึ้นของต้นทุน 4.2 เท่า ด้านล่างนั้น 324 จาก 667 session ล่าสุด
มีสัญญาณของความสูญเปล่า จำแนกตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้คุณเห็นว่าเงินไปไหน ในทุกช่วงเวลา**
$252.47 วันนี้ $513.15 สัปดาห์นี้ $1,312.92 เดือนนี้ พร้อมโทเคนที่อยู่เบื้องหลัง
และจำนวนที่การสมัครสมาชิกของคุณครอบคลุมไปแล้ว ด้านล่างนั้น ประมาณ $1,128/เดือน
ถูกจำแนกว่าสามารถประหยัดคืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้วด้วยการใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดให้เห็นว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
แผนภาพ flow แบบเรียลไทม์: คุณ, ช่องทางที่ข้อความเข้ามา, gateway, โมเดล
ที่กำลังตอบอยู่ตอนนี้ และเครื่องมือทุกตัวที่มันเอื้อมไปใช้ โหนดต่าง ๆ
จะสว่างขึ้นเมื่อมีงานเคลื่อนผ่านมัน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง ในตารางเดียว**
สิ่งที่มันรัน ต้นทุนใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน เวลาที่พบล่าสุด
ใครเป็นเจ้าของ และมีการสมัครสมาชิกครอบคลุมค่าใช้จ่ายหรือไม่ มีเอเจนต์ 14 ตัวที่นี่
3 session กำลังทำงาน 13 ตัวเงียบอยู่

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของแต่ละเทิร์นไปที่ไหน ทีละเครื่องมือ**
หนึ่งเทิร์นของ session จริง: เครื่องมือ 11 ตัวใน 11.2 นาที ด้วยต้นทุน $1.16
การเรียก Bash และการเรียกโมเดลแต่ละครั้งมีแท่งของตัวเองบน timeline ทำให้คำสั่งที่รัน
4.1 นาที กับคำสั่งที่รันแค่ 226 มิลลิวินาที แยกออกจากกันได้ในพริบตา

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้คะแนนงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A ในสัปดาห์นี้: งาน 54 ชิ้นเสร็จสมบูรณ์ งานที่ขรุขระ 2 ชิ้นมีต้นทุน $48.57
และรันที่มีกิจกรรมน้อยเกินกว่าจะตัดสินได้จะถูกตัดออกจากเกรดแทนที่จะถูกนับเป็นผลงาน
งานขรุขระแต่ละชิ้นมีลิงก์ไปยัง trace ของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงให้เห็นว่าทำไม context window ถึงเต็มขึ้นเรื่อย ๆ**
715K จากหน้าต่างขนาด 1M โทเคนในเทิร์นล่าสุด จุดสูงสุดที่ 83.3% การทำ compaction
4 ครั้งที่ล้วนถูกเรียกแบบเชิงรุกไม่ใช่จากการ overflow พร้อมการใช้งานของทุกเทิร์นที่อยู่เบื้องหลัง

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยที่คุณไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป, ฟีดข้อมูลหยุดส่ง,
ต้นทุนพุ่งสูง, โทเคนพุ่งสูง, ข้อผิดพลาดเพิ่มขึ้น, ข้อผิดพลาดพุ่งสูง,
เกินเพดานงบประมาณ, ตรงกับลายเซ็นภัยคุกคาม, พบสิ่งผิดปกติจากเครื่องมือความปลอดภัย,
สถานะความปลอดภัยเปลี่ยนแปลง กฎของคุณเองก็เป็นตัวเลือกเสริมที่เพิ่มเข้าไปได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การหยุดการเรียกที่มีความเสี่ยงเป็นแบบ opt-in และปิดอยู่โดยค่าเริ่มต้น**
การลบแบบ recursive, force push, sudo, ข้อมูลลับ, การติดตั้งแพ็กเกจ และการเรียก
ออกไปภายนอก แต่ละอย่างมีกฎที่คุณเปิดใช้งานได้ จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดู
เฉย ๆ และไม่เปลี่ยนแปลงอะไร เมื่อกฎใดถูกเปิดใช้งาน การเรียกที่ตรงเงื่อนไขจะรอที่นี่
(หรือบนมือถือของคุณ) เพื่อรอการอนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม แยกตาม runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## สัญญาอนุญาต

MIT · สร้างโดย [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
