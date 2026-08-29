<!-- i18n-src:d21bea5161e0 -->
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

**ดูเอเจนต์ของคุณคิด** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **30 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 26 ตัว แดชบอร์ดเดียวสำหรับเอเจนต์ทั้งฟลีทของคุณ

> 🌐 **อ่านเป็นภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

หนึ่งคำสั่ง ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใด ๆ ระบบจะค้นหา agent runtime
ที่คุณมีอยู่แล้ว อ่านแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันแต่อย่างใด

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## รองรับ agent runtime ถึง 30 ตัว

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ในแผนแบบเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุก runtime ได้แดชบอร์ดแบบเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัว
จะปรับขอบเขตของทุกแท็บให้ตรงกับตัวที่เลือก

สร้างเอเจนต์ของคุณเองด้วย SDK แทนใช่ไหม? interceptor ก็ติดตามการเรียก LLM
ของมันได้เช่นกัน ดู [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: สิ่งที่เอเจนต์แต่ละตัวทำ ทีละเทิร์น พร้อมเล่นซ้ำ
- **ต้นทุนและโทเค็น**: แยกตาม runtime, โมเดล, เซสชัน และวัน พร้อมสัญญาณผิดปกติ
- **Flow**: แผนภาพแบบเรียลไทม์ของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือขณะที่เกิดขึ้นจริง
- **Context blowout**: การใช้งานหน้าต่างบริบทที่คำนวณตามผู้ให้บริการแต่ละราย เทียบระหว่าง compaction กับ overflow ที่ถูกบังคับ พร้อมแผนที่ต่อ runtime ว่าอะไรที่เรา *มองไม่เห็น* ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **Memory และ skills**: ไฟล์และ skill ที่แต่ละ runtime โหลดใช้งานจริง
- **สุขภาพและล็อก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด rate limit สตรีมล็อกแบบสด
- **แจ้งเตือน**: เพดานงบประมาณ ข้อผิดพลาดพุ่งสูง เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะรัน และอนุมัติได้จากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และค่าใช้จ่ายในการเฝ้าดู

สองคำถามที่คุ้มค่าที่จะตอบก่อนที่คุณจะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ตัวใด ๆ

**มันจัดการกับ context-window blowout ข้าม runtime อย่างไร?**

เปอร์เซ็นต์การใช้งานจะซื่อสัตย์ได้ก็ต่อเมื่อสิ่งที่ใช้หารนั้นถูกต้อง ClawMetry
คำนวณขนาดหน้าต่างตามผู้ให้บริการแต่ละรายจาก[ตารางที่คุณอ่านและส่ง PR
ได้](clawmetry/context_windows.py) ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัด runtime ทั้ง 26 ตัว
ด้วยไม้บรรทัดของผู้ให้บริการรายเดียว นั่นสำคัญมาก: เทิร์นของ GPT-5 ขนาด 300K
เมื่อวัดเทียบกับ 200K ของ Anthropic จะอ่านว่า ">100%, blown" ทั้งที่จริงแล้วมันอยู่ที่
75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อนเทิร์นของ DeepSeek ขนาด 130K
ที่ overflow จริง ๆ ให้ดูเหมือนสบาย ๆ ที่ 65%

ทุกหน้าต่างมาพร้อมที่มาของมัน: `model_table`, `explicit_marker`,
`observed_floor` หรือ `default` ที่ตรงไปตรงมาเมื่อเราไม่รู้จักโมเดลนั้น
เกจที่สร้างจากการเดาจะไม่มีวันแสดงผลด้วยความน่าเชื่อถือเท่ากับเกจที่สร้างจากการค้นหาข้อมูลจริง

ClawMetry มองเห็นเหตุการณ์ compaction ได้แค่ใน runtime บางตัวเท่านั้น ดังนั้น
`GET /api/context-coverage` จะรายงานต่อ runtime ว่า **เลขศูนย์หมายถึง
"รันได้สะอาด" หรือ "เรามองไม่เห็น"** เลข `0` ที่จริง ๆ แล้วหมายถึงมองไม่เห็นก็จะบอกไว้
[รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**การติดตั้งเครื่องมือวัดผลมีต้นทุนเท่าไร?**

| เส้นทาง | เพิ่มให้กับเอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การอ่านไฟล์เซสชันแบบ tailing (ครบทั้ง 30 runtime) | **0** เป็นโปรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ต่อการเรียก LLM หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (แคชอุ่นแล้ว) | **+44 ms** ต่อการเรียกใช้เครื่องมือที่ถูก gate เหนือพื้นฐาน interpreter 36 ms | ปิด |
| Enforcement proxy | **+9.7 ms** ต่อการเรียก LLM | ปิด |

ต้นทุนของโฮสต์ daemon: **2,762 เหตุการณ์/วินาที** ในการ ingest **710 ไบต์/เหตุการณ์**
บนดิสก์ (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ราว 12% ของหนึ่งคอร์** อย่างต่อเนื่องบน
การติดตั้งที่ใช้งานหนัก ตัวเลขสุดท้ายนี้เกินงบประมาณ 5-10% ที่เราตั้งไว้เอง ดังนั้นจึง
เผยแพร่เป็นบั๊กที่ต้องตามแก้ ไม่ใช่ถูกละไว้จากหน้านี้

วัดผลบน Apple M2 Pro ด้วย `benchmarks/overhead.py` ฮาร์เนสนี้รันแต่ละเงื่อนไข
ในโปรเซสแยกต่างหาก สลับลำดับกันไปมา และ **ปฏิเสธที่จะพิมพ์ตัวเลขออกมาเมื่อรอบต่าง ๆ
ไม่เห็นตรงกันในเรื่องเครื่องหมาย (บวก/ลบ)** รันบนเครื่องของคุณเองได้ในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดผล รวมถึง hook gate และ enforcement proxy ด้วย และฮาร์เนสนี้รันบน
Linux, macOS และ Windows ใน CI มีสองผลลัพธ์ที่ควรรู้: proxy มีต้นทุนสูงกว่าบน
Windows ประมาณเจ็ดเท่าเมื่อเทียบกับ Linux และ daemon ในปัจจุบันใช้งานต่อเนื่องที่ราว
12% ของหนึ่งคอร์ ซึ่งเกินงบประมาณ 5-10% ที่เราตั้งไว้เอง JSON ดิบ วิธีการ และสิ่งที่ยัง
ไม่ได้วัดอยู่ที่ [docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แผน | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดครบทุกฟีเจอร์ เฉพาะเครื่องนี้เท่านั้น | $0 |
| **Starter** | runtime อื่น ๆ ทั้งหมดข้างต้น มุมมองฟลีท การซิงค์กับคลาวด์ | $9 ต่อโหนด / เดือน |
| **Pro** | Starter บวกการควบคุมและการประเมิน: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ eval การตรวจจับความผิดปกติ ตัวปรับต้นทุนให้เหมาะสม การส่งออก OTel บันทึกการตรวจสอบที่ป้องกันการดัดแปลง | $19 ต่อโหนด / เดือน |

แผนรายปี Enterprise และตัวเลขปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** license key แบบ self-hosted
ใช้งานได้โดยไม่ต้องใช้คลาวด์ (`clawmetry license`) รายละเอียดของการแบ่งฟรี/เสียเงิน
ที่ชัดเจนอยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเอง

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันใดออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** ไม่มีพรอมต์ คำตอบ อาร์กิวเมนต์ของเครื่องมือ
เนื้อหาไฟล์ หรือบรรทัดล็อกใด ๆ ถูกส่งออก เมื่อคุณเชื่อมต่อจริง สแนปช็อตจะถูกเข้ารหัส
แบบ end-to-end ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัสในเบราว์เซอร์ของคุณ
หากโหนดไม่มีคีย์ การอัปโหลดจะถูกข้ามไปแทนที่จะส่งแบบไม่เข้ารหัส และไม่มีการตอบกลับ
จากเซิร์ฟเวอร์ใดที่จะปิดการทำงานนี้ได้

มีสองสิ่งที่ทำงานตามค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งคู่เป็นแบบ opt-out และไม่มี
ตัวไหนพาข้อมูลเซสชันไปด้วย: การ ping ติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันกับ
PyPI การติดตั้งเริ่มต้นยังค้นหา public IP ของคุณครั้งเดียวเพื่อใช้ในบรรทัดแบนเนอร์
ตอนเริ่มต้น ปลายทางทุกแห่ง สิ่งที่มันพาไป และวิธีปิดมันอยู่ใน
[docs/EGRESS.md](docs/EGRESS.md) การติดตั้งแบบ self-hosted, repointed และ
air-gapped จะไม่มีการเรียกออกไปภายนอกตามดุลยพินิจใด ๆ เลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราให้บริการคุณ สิ่งนี้เคยเป็นเพียง
คำสัญญา แต่ตอนนี้เป็นสิ่งที่คุณตรวจสอบได้ ทุกบรรทัดที่แตะต้องคีย์ของคุณอยู่ในไฟล์
ที่อ่านได้ไฟล์เดียว [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งมาพร้อมกับ wheel และถูกให้บริการแบบคำต่อคำ พร้อมปักหมุดด้วยแฮช Subresource
Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่วิธีนี้พิสูจน์ไม่ได้: เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้ ดังนั้นเราจึง
สามารถให้บริการหน้าเว็บที่แตกต่างออกไปได้ แฮช Integrity ปกป้องคุณจาก CDN ที่ถูก
บุกรุก ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้คือการแทนที่ใด ๆ ต้องเป็นการกระทำโดย
เจตนา มองเห็นได้ในซอร์สของหน้าเว็บ และแตกต่างจากอาร์ติแฟกต์บน PyPI ที่ใครก็ดึงมา
ตรวจสอบได้ การโฮสต์เองหรืออยู่แบบ local-only เท่านั้นจะขจัดการพึ่งพานี้ออกไปทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือใช้คำสั่งบรรทัดเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8+ บน macOS, Linux หรือ Windows และมี agent runtime อย่างน้อย
หนึ่งตัวบนเครื่องเดียวกัน คำแนะนำ Docker: [docs/DOCKER.md](docs/DOCKER.md)

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของ Runtime](docs/compatibility.md) | สิ่งที่แต่ละ adapter อ่าน และวิธีเพิ่ม runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างของแต่ละผู้ให้บริการ compaction เทียบกับ overflow ความครอบคลุมต่อ runtime |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของเครื่องมือวัดผล วัดจริง พร้อมฮาร์เนสสำหรับทำซ้ำ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับชั้น license CLI |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การกำหนด gate ก่อนการรัน การให้คะแนนความเสี่ยง การอนุมัติจากโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก trace ไปที่ไหนก็ได้ รับ OTLP จากอะไรก็ได้ |
| [SDK tracking](docs/SDK_TRACKING.md) | การระบุที่มาของต้นทุนสำหรับเอเจนต์ที่คุณสร้างเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมานต์วอลุ่ม |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | มันทำงานอย่างไรภายใน การรันจากซอร์ส |
| [Telemetry](docs/TELEMETRY.md) | การ ping ติดตั้งและการเปิดเดสก์ท็อปแบบไม่ระบุตัวตน และวิธีปิดมัน |

## ภาพหน้าจอ

ตัวเลขทุกตัวด้านล่างมาจากเครื่องจริงหนึ่งเครื่อง แบบอ่านอย่างเดียว ไม่มีการปลูกข้อมูลใด ๆ

**มันบอกคุณเมื่อมีบางอย่างผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่วิ่งสูงกว่าค่าเฉลี่ยรายวันถึง 7 เท่า
และค่าใช้จ่ายพุ่งสูง 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุดมีสัญญาณของ
การสูญเปล่า แจกแจงตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้เห็นว่าเงินไปไหน ในทุกช่วงเวลา**
$252.47 วันนี้ $513.15 สัปดาห์นี้ $1,312.92 เดือนนี้ แต่ละตัวพร้อมโทเค็นที่อยู่เบื้อง
หลัง และสมาชิกภาพของคุณครอบคลุมไปแล้วเท่าไร ด้านล่างนั้น ประมาณ $1,128/เดือน
ที่แจกแจงเป็นสิ่งที่กู้คืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้วจากการใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดให้เห็นว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
แผนภาพ flow แบบสด: คุณ ช่องทางที่ข้อความมาถึง เกตเวย์ โมเดลที่กำลังตอบอยู่ตอนนี้
และเครื่องมือทุกตัวที่มันเรียกใช้ โหนดจะสว่างขึ้นเมื่องานเคลื่อนผ่าน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง ในตารางเดียว**
สิ่งที่มันรัน ต้นทุนใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน เห็นครั้งล่าสุดเมื่อไร
ใครเป็นเจ้าของ และมีสมาชิกภาพครอบคลุมค่าใช้จ่ายหรือไม่ 14 เอเจนต์ที่นี่ 3 เซสชัน
กำลังทำงาน 13 ตัวเงียบอยู่

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของหนึ่งเทิร์นไปไหน แยกตามเครื่องมือ**
หนึ่งเทิร์นของเซสชันจริง: 11 เครื่องมือใน 11.2 นาที คิดเป็น $1.16 การเรียก Bash
และการเรียกโมเดลทุกครั้งมีแท่งของตัวเองบนไทม์ไลน์ ทำให้คำสั่งที่รันนาน 4.1 นาที
กับคำสั่งที่รันแค่ 226ms แยกออกจากกันได้ในพริบตา

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้คะแนนงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A ในสัปดาห์นี้: 54 งานเสร็จสมบูรณ์อย่างสะอาด 2 งานที่ขรุขระคิดเป็นเงิน $48.57
และรันที่มีกิจกรรมน้อยเกินกว่าจะตัดสินได้ถูกตัดออกจากการให้คะแนนแทนที่จะถูกนับเป็น
ชัยชนะ แต่ละรันที่ขรุขระเชื่อมโยงไปยัง trace ของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงให้เห็นว่าทำไม context window ถึงเต็มอยู่เรื่อย ๆ**
715K จากหน้าต่าง 1M โทเค็นในเทิร์นล่าสุด จุดสูงสุดที่ 83.3% การ compaction 4 ครั้ง
ที่ทั้งหมดเกิดขึ้นแบบเชิงรุกแทนที่จะเกิดจาก overflow พร้อมการใช้งานของทุกเทิร์นที่
อยู่เบื้องหลังมัน

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป ฟีดข้อมูลหยุดทำงาน
ค่าใช้จ่ายพุ่งสูง โทเค็นพุ่งสูง ข้อผิดพลาดเพิ่มขึ้น ข้อผิดพลาดพุ่งสูง เกินเพดาน
งบประมาณ ตรงกับลายเซ็นภัยคุกคาม ผลการค้นพบจากเครื่องมือความปลอดภัย
ท่าทีความปลอดภัยเปลี่ยนแปลง กฎของคุณเองเป็นตัวเลือกเสริมเพิ่มเติมได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การหยุดการเรียกที่มีความเสี่ยงเป็นแบบ opt-in และปิดไว้เป็นค่าเริ่มต้นตอนส่งมอบ**
การลบแบบ recursive, force push, sudo, ข้อมูลลับ, การติดตั้งแพ็กเกจ และการเรียก
ออกไปภายนอก แต่ละอย่างมีกฎที่คุณเปิดใช้งานได้ จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดูและ
ไม่เปลี่ยนแปลงอะไรเลย เมื่อเปิดใช้งานแล้ว การเรียกที่ตรงเงื่อนไขจะรอที่นี่ (หรือบน
โทรศัพท์ของคุณ) เพื่อขออนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม แยกตาม runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## ประวัติดาว

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
