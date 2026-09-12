<!-- i18n-src:a855a14295b0 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**เอเจนต์สามารถเรียกใช้เครื่องมือได้เป็นร้อยครั้งโดยไม่มีความคืบหน้าเลยก็ได้** ClawMetry
อ่านไฟล์เซสชันที่เอเจนต์เขียนโค้ดของคุณสร้างขึ้นอยู่แล้ว แล้วนำไทม์ไลน์
การเรียกใช้เครื่องมือ และข้อมูลโทเคนกับต้นทุนเท่าที่รันไทม์เปิดเผยมารวมไว้ในมุมมองเดียว
เพื่อให้คุณแยกแยะได้ว่างานที่รันมานานนั้นกำลังทำงานได้ดี หรือติดขัดอยู่กันแน่

ใช้งานได้กับ **รันไทม์เอเจนต์ AI 32 ตัว** ได้แก่ Claude Code, OpenAI Codex, Hermes, OpenClaw และอีก 28 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ ([รายการทั้งหมด](SUPPORTED_RUNTIMES.txt) สร้างจากแคตตาล็อกโดยอัตโนมัติ)

> 🌐 **อ่านเป็นภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าอะไรเลย ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใด ๆ ระบบจะค้นหารันไทม์เอเจนต์
ที่คุณมีอยู่แล้ว อ่านแบบ read-only เท่านั้น และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ก่อนติดตั้ง

| | |
|---|---|
| **มันทำอะไรบ้าง** | อ่านไฟล์เซสชันและล็อกที่เอเจนต์ของคุณเขียนอยู่แล้ว ไม่ต้องใช้ SDK ไม่ต้องแก้โค้ด ไม่ต้องฝัง instrumentation ในแอปของคุณ |
| **คุณจะเห็นอะไร** | ไทม์ไลน์เซสชัน การเล่นซ้ำการเรียกใช้เครื่องมือทีละตัว รายละเอียดโทเคนและต้นทุน และสัญญาณของวิถีการทำงาน (การวนซ้ำ ความล้มเหลวซ้ำ ๆ) แยกตามรันไทม์ |
| **สิ่งที่ใช้ฟรี** | `pip install clawmetry` อ่านข้อมูลจาก **OpenClaw, NVIDIA NemoClaw และ Goose** ได้โดยไม่ต้องมีบัญชี ไม่ต้องมีคีย์ และไม่ต้องเรียกเครือข่ายใด ๆ ส่วนอีก 27 ตัวที่เหลือ อย่าง Claude Code, Codex, Cursor และตัวอื่น ๆ จะถูกอ่านโดยส่วนเสริม `clawmetry-pro` แบบ closed-source ซึ่งมาพร้อมกับช่วงทดลองใช้ 7 วันหรือแพ็กเกจแบบมีค่าใช้จ่าย ดูรายละเอียดการแบ่งที่แน่นอนได้ที่ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) |
| **วิธีเริ่มต้น** | `pip install clawmetry && clawmetry` แล้วเปิด localhost:8900 ยังไม่มีเอเจนต์บนเครื่องนี้ใช่ไหม? `clawmetry --sample` จะเปิดโดยแสดงเซสชันสังเคราะห์ที่ติดป้ายไว้สามชุด |
| **ข้อมูลอะไรที่ออกจากเครื่องคุณ** | ไม่มีข้อมูลเซสชันใด ๆ ออกจากเครื่อง เว้นแต่คุณจะรัน `clawmetry connect` มีสองสิ่งที่ทำงานเป็นค่าเริ่มต้น ซึ่งทั้งคู่ปิดได้และไม่มีเนื้อหาเซสชันติดไปด้วย ได้แก่ การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันจาก PyPI ปลายทางทั้งหมดถูกบันทึกไว้ใน [docs/EGRESS.md](docs/EGRESS.md) ซึ่งสร้างขึ้นจากการดักจับข้อมูลบนสาย ไม่ใช่จากการอ่านคอมเมนต์ในโค้ด |

มีข้อจำกัดสองอย่างที่ควรรู้ก่อนตัดสินผลลัพธ์ นั่นคือรันไทม์แต่ละตัวเปิดเผยข้อมูล
ที่แตกต่างกันมาก (บางตัวไม่เผยแพร่ต้นทุนเลย [ตารางเปรียบเทียบ](docs/compatibility.md)
บอกไว้ว่าตัวไหนเป็นแบบใด) และการสังเกตการกระทำก็ไม่เหมือนกับการสามารถ
บล็อกมันได้ ([ตัวควบคุมไหนที่ใช้งานได้จริง แยกตามรันไทม์](docs/APPROVALS.md))


## ใช้งานได้กับรันไทม์เอเจนต์ 32 ตัว

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ในแพ็กเกจแบบมีค่าใช้จ่าย:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุกรันไทม์ใช้แดชบอร์ดเดียวกัน หากรันหลายตัวพร้อมกัน ตัวสลับที่ส่วนหัวจะปรับ
ขอบเขตของทุกแท็บให้ตรงกับตัวที่เลือก

สร้างเอเจนต์ของคุณเองบน SDK แทนใช่ไหม? interceptor ก็ติดตามการเรียก LLM
ของมันได้เช่นกัน ดู [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: สิ่งที่เอเจนต์แต่ละตัวทำ ทีละเทิร์น พร้อมการเล่นซ้ำ
- **ต้นทุนและโทเคน**: แยกตามรันไทม์ โมเดล เซสชัน และวัน พร้อมสัญญาณความผิดปกติ
- **Flow**: ไดอะแกรมแบบสดของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบเรียลไทม์
- **Context blowout**: การใช้งานหน้าต่างบริบทตามขนาดของแต่ละผู้ให้บริการ การอัดข้อมูล (compaction) เทียบกับการล้นแบบบังคับ พร้อมแผนที่ของสิ่งที่เรา *มองไม่เห็น* แยกตามรันไทม์ ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: ไฟล์และสกิลที่แต่ละรันไทม์โหลดขึ้นมาใช้จริง
- **สุขภาพและล็อก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด ขีดจำกัดอัตรา สตรีมล็อกแบบสด
- **การแจ้งเตือน**: เพดานงบประมาณ ข้อผิดพลาดพุ่งสูง เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะรัน และอนุมัติได้จากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการติดตาม

มีคำถามสองข้อที่ควรตอบให้ได้ก่อนที่จะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ใด ๆ

**มันจัดการกับ context-window blowout ข้ามรันไทม์อย่างไร?**

เปอร์เซ็นต์การใช้งานจะซื่อสัตย์ก็ต่อเมื่อตัวหารของมันซื่อสัตย์ ClawMetry
กำหนดขนาดหน้าต่างตามผู้ให้บริการแต่ละรายจาก[ตารางที่คุณอ่านและส่ง
PR ได้](clawmetry/context_windows.py) ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดรันไทม์ทั้ง 32 ตัว
ด้วยไม้บรรทัดของผู้ให้บริการรายเดียว เรื่องนี้สำคัญ เพราะเทิร์นของ GPT-5
ขนาด 300K เมื่อวัดเทียบกับ 200K ของ Anthropic จะอ่านได้ว่า ">100% ล้นแล้ว"
ทั้งที่จริง ๆ อยู่ที่ 75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อน
เทิร์นของ DeepSeek ที่ล้นจริงที่ 130K ให้ดูเหมือนสบาย ๆ ที่ 65%

หน้าต่างทุกอันมาพร้อมแหล่งที่มาของมัน: `model_table`, `explicit_marker`,
`observed_floor` หรือค่า `default` ที่ตรงไปตรงมาเมื่อเราไม่รู้จักโมเดลนั้น
มาตรวัดที่สร้างจากการเดาจะไม่มีวันแสดงผลด้วยความน่าเชื่อถือเท่ากับมาตรวัด
ที่สร้างจากการค้นหาข้อมูลจริง

ClawMetry มองเห็นเหตุการณ์ compaction ได้เฉพาะในบางรันไทม์เท่านั้น ดังนั้น
`GET /api/context-coverage` จึงรายงานแยกตามรันไทม์ว่า **เลข 0 หมายถึง
"รันได้สะอาด" หรือ "เรามองไม่เห็น"** เลข `0` ที่จริง ๆ แล้วหมายถึงมองไม่เห็น
ก็จะบอกไว้ตรง ๆ [รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**การติดตั้ง instrumentation มีต้นทุนเท่าไร?**

| เส้นทาง | เพิ่มให้เอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การ tail ไฟล์เซสชัน (ทั้ง 32 รันไทม์) | **0** เป็นโพรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry อยู่ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (warm cache) | **+44 มิลลิวินาที** ต่อการเรียกเครื่องมือที่ถูกเฝ้าประตูหนึ่งครั้ง เหนือพื้นฐาน interpreter ที่ 36 มิลลิวินาที | ปิด |
| Enforcement proxy | **+9.7 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง | ปิด |

ต้นทุนของโฮสต์ daemon: **2,762 เหตุการณ์/วินาที** ในการรับข้อมูล **710 ไบต์/เหตุการณ์**
บนดิสก์ (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ประมาณ 12% ของหนึ่งคอร์** อย่างต่อเนื่อง
บนการติดตั้งที่มีงานเยอะ ตัวเลขสุดท้ายนี้เกินงบประมาณ 5-10% ที่เราตั้งไว้เอง
จึงถูกเผยแพร่ในฐานะบั๊กที่ต้องตามแก้ไข ไม่ใช่ถูกซ่อนไว้ไม่พูดถึง

วัดบน Apple M2 Pro ด้วย `benchmarks/overhead.py` เครื่องมือทดสอบนี้รันแต่ละ
เงื่อนไขในโพรเซสแยกกัน สลับลำดับกัน และ **ปฏิเสธที่จะพิมพ์ตัวเลขออกมาเมื่อ
รอบทดสอบให้ผลเครื่องหมาย (บวก/ลบ) ที่ขัดแย้งกัน** ลองรันบนเครื่องของคุณเอง
ได้ในเวลาไม่ถึงนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดผล รวมถึง hook gates และ enforcement proxy และเครื่องมือ
ทดสอบนี้รันบน Linux, macOS และ Windows ใน CI มีผลลัพธ์สองข้อที่ควรรู้:
proxy มีต้นทุนสูงกว่าบน Windows ประมาณเจ็ดเท่าเมื่อเทียบกับ Linux และ
daemon ในปัจจุบันใช้ทรัพยากรอย่างต่อเนื่องประมาณ 12% ของหนึ่งคอร์ ซึ่งเกิน
งบประมาณ 5-10% ที่เราตั้งไว้เอง ข้อมูล JSON ดิบ วิธีการทดสอบ และสิ่งที่ยัง
ไม่ได้วัด อยู่ใน [docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แพ็กเกจ | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ ใช้งานได้เฉพาะในเครื่อง | $0 |
| **Starter** | รันไทม์อื่น ๆ ทั้งหมดข้างต้น มุมมองแบบกองเอเจนต์ (fleet view) การซิงค์กับคลาวด์ | $9 ต่อโหนด / เดือน |
| **Pro** | Starter บวกกับการควบคุมและการประเมินผล: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมิน (evals) การตรวจจับความผิดปกติ ตัวปรับต้นทุนให้เหมาะสม การส่งออก OTel บันทึกการตรวจสอบที่ป้องกันการปลอมแปลง | $19 ต่อโหนด / เดือน |

แพ็กเกจรายปี Enterprise และตัวเลขราคาปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ไลเซนส์แบบ
self-hosted ใช้งานได้โดยไม่ต้องพึ่งคลาวด์ (`clawmetry license`) รายละเอียด
การแบ่งฟรี/มีค่าใช้จ่ายที่แน่นอนอยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเอง

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันใด ๆ ออกจากเครื่อง
ของคุณเว้นแต่คุณจะรัน `clawmetry connect`** ไม่มีทั้งพรอมป์ คำตอบ อาร์กิวเมนต์
ของเครื่องมือ เนื้อหาไฟล์ หรือบรรทัดล็อก เมื่อคุณเชื่อมต่อจริง ๆ สแนปช็อตจะถูก
เข้ารหัสแบบ end-to-end ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัส
ในเบราว์เซอร์ของคุณเอง หากโหนดไม่มีคีย์ การอัปโหลดจะถูกข้ามไปแทนที่จะส่งแบบ
ไม่เข้ารหัส และไม่มีการตอบกลับจากเซิร์ฟเวอร์ใดที่จะปิดพฤติกรรมนี้ได้

มีสองสิ่งที่ทำงานเป็นค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งคู่ปิดได้และไม่มีข้อมูล
เซสชันติดไปด้วย ได้แก่ การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชัน
เทียบกับ PyPI การติดตั้งแบบค่าเริ่มต้นยังค้นหา IP สาธารณะของคุณหนึ่งครั้งเพื่อ
แสดงในบรรทัดแบนเนอร์ตอนเริ่มต้น ปลายทางทั้งหมด สิ่งที่มันส่งไป และวิธีปิดมัน
ถูกระบุไว้ใน [docs/EGRESS.md](docs/EGRESS.md) การติดตั้งแบบ self-hosted
เปลี่ยนปลายทาง หรือแบบตัดขาดจากอินเทอร์เน็ต (air-gapped) จะไม่มีการเรียก
ออกไปภายนอกตามดุลยพินิจเลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราส่งให้คุณ สิ่งนี้เคยเป็นเพียง
คำมั่นสัญญา แต่ตอนนี้เป็นสิ่งที่คุณตรวจสอบได้เอง ทุกบรรทัดที่แตะต้องคีย์ของคุณ
อยู่ในไฟล์เดียวที่อ่านได้ [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งมาพร้อมกับ wheel และถูกให้บริการตามต้นฉบับทุกตัวอักษร โดยตรึงไว้ด้วยแฮช
Subresource Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่การตรวจสอบนี้พิสูจน์ไม่ได้คือ เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้
ดังนั้นเราก็อาจให้บริการหน้าเว็บอื่นได้เช่นกัน แฮชความสมบูรณ์ปกป้องคุณจาก CDN
ที่ถูกบุกรุก ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้รับคือ การแทนที่ใด ๆ จะต้อง
เป็นการกระทำโดยเจตนา มองเห็นได้ในซอร์สของหน้าเว็บ และแตกต่างจากอาร์ติแฟกต์
บน PyPI ที่ใครก็ดาวน์โหลดมาตรวจสอบได้ การโฮสต์เองหรือใช้งานแบบ local-only
เท่านั้นจะขจัดการพึ่งพานี้ออกไปทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือคำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8 ขึ้นไปบน macOS, Linux หรือ Windows และมีรันไทม์เอเจนต์
อย่างน้อยหนึ่งตัวอยู่บนเครื่องเดียวกัน คำแนะนำสำหรับ Docker:
[docs/DOCKER.md](docs/DOCKER.md)

หรือให้เอเจนต์ตั้งค่าให้คุณเลยก็ได้ สกิล [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
สอน Claude Code, Codex, Cursor, Gemini CLI, Copilot หรือ OpenCode ให้ติดตั้ง
ClawMetry รายงานว่าเอเจนต์บนเครื่องกำลังทำอะไรและใช้จ่ายเท่าไร หยุดเซสชัน
ใดเซสชันหนึ่งตามคำขอ และกักการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้รอการอนุมัติ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | อะแดปเตอร์แต่ละตัวอ่านอะไรบ้าง และวิธีเพิ่มรันไทม์ใหม่ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างแยกตามผู้ให้บริการ compaction เทียบกับ overflow ความครอบคลุมแยกตามรันไทม์ |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของ instrumentation ที่วัดได้จริง พร้อมเครื่องมือทดสอบให้ทำซ้ำได้ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับมีค่าใช้จ่าย ตารางระดับแพ็กเกจ license CLI |
| [Approvals & policies](docs/APPROVALS.md) | การกักกันก่อนรัน การให้คะแนนความเสี่ยง การอนุมัติผ่านโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก traces ไปที่ไหนก็ได้ รับ OTLP จากที่ไหนก็ได้ |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้จริง |
| [SDK tracking](docs/SDK_TRACKING.md) | การระบุต้นทุนสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [Chat channels](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมาท์วอลุ่ม |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ระบบทำงานอย่างไรภายใน การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การ ping แบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

ตัวเลขทุกตัวด้านล่างมาจากเครื่องจริงหนึ่งเครื่อง อ่านแบบ read-only โดยไม่มี
การใส่ข้อมูลจำลองเลย

**มันบอกคุณเมื่อมีบางอย่างผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันด้านบน: การใช้จ่ายที่สูงกว่าค่าเฉลี่ยรายวันถึง 7 เท่า
และต้นทุนที่พุ่งขึ้น 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุดมีสัญญาณ
ความสิ้นเปลือง แจกแจงตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้เห็นว่าเงินไปไหน ในทุกช่วงเวลา**
$252.47 วันนี้ $513.15 สัปดาห์นี้ $1,312.92 เดือนนี้ พร้อมโทเคนที่อยู่เบื้องหลัง
ตัวเลขและจำนวนที่การสมัครสมาชิกของคุณครอบคลุมอยู่แล้ว ด้านล่างนั้น ประมาณ
$1,128/เดือน ถูกแจกแจงว่าสามารถประหยัดคืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้ว
จากการใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดให้เห็นว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
ไดอะแกรม flow แบบสด: คุณ ช่องทางที่ข้อความเข้ามา เกตเวย์ โมเดลที่กำลังตอบ
อยู่ตอนนี้ และเครื่องมือทุกตัวที่มันเรียกใช้ โหนดจะสว่างขึ้นเมื่องานเคลื่อนผ่าน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง อยู่ในตารางเดียว**
สิ่งที่มันรัน ต้นทุนใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน เห็นล่าสุดเมื่อไร
ใครเป็นเจ้าของ และการสมัครสมาชิกครอบคลุมค่าใช้จ่ายหรือไม่ ที่นี่มีเอเจนต์ 14 ตัว
3 เซสชันกำลังทำงาน 13 ตัวเงียบอยู่

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของแต่ละเทิร์นไปไหน แยกตามเครื่องมือ**
หนึ่งเทิร์นของเซสชันจริง: เครื่องมือ 11 ตัวใน 11.2 นาที คิดเป็น $1.16 การเรียก
Bash และการเรียกโมเดลทุกครั้งมีแท่งของตัวเองบนไทม์ไลน์ ทำให้คำสั่งที่รันไป 4.1
นาทีกับคำสั่งที่รันไป 226 มิลลิวินาที แยกออกจากกันได้ในทันที

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้คะแนนงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A ในสัปดาห์นี้: 54 งานเสร็จเรียบร้อย 2 งานที่มีปัญหาคิดเป็นต้นทุน $48.57
และงานที่มีกิจกรรมน้อยเกินกว่าจะตัดสินได้จะถูกตัดออกจากการให้เกรดแทนที่จะนับ
เป็นความสำเร็จ แต่ละงานที่มีปัญหาเชื่อมโยงไปยัง trace ของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงให้เห็นว่าทำไม context window ถึงเต็มขึ้นเรื่อย ๆ**
715K จากหน้าต่าง 1M โทเคนในเทิร์นล่าสุด จุดสูงสุด 83.3% การอัดข้อมูล 4 ครั้ง
ที่ทั้งหมดเกิดขึ้นเชิงรุกแทนที่จะเกิดจากการล้น พร้อมการใช้งานของทุกเทิร์น
ที่อยู่เบื้องหลัง

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป ฟีดข้อมูลเทเลเมทรีหยุด
ต้นทุนพุ่งสูง โทเคนพุ่งสูง ข้อผิดพลาดเพิ่มขึ้นเรื่อย ๆ ข้อผิดพลาดพุ่งสูง เกินเพดาน
งบประมาณ ตรงกับลายเซ็นภัยคุกคาม พบผลจากเครื่องมือความปลอดภัย ท่าทีความปลอดภัย
เปลี่ยนแปลง กฎของคุณเองเป็นตัวเลือกเสริมเพิ่มเติมได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การกักการเรียกใช้ที่มีความเสี่ยงเป็นแบบเลือกเปิดเอง และปิดไว้เป็นค่าเริ่มต้น**
การลบแบบเรียกซ้ำ (recursive delete) การ force push, sudo, ข้อมูลลับ (secrets)
การติดตั้งแพ็กเกจ และการเรียกออกภายนอก แต่ละอย่างมีกฎที่คุณเปิดใช้งานได้เอง
จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดูเท่านั้นและไม่เปลี่ยนแปลงอะไร เมื่อเปิดกฎ
ใดกฎหนึ่งแล้ว การเรียกที่ตรงเงื่อนไขจะรอที่นี่ (หรือบนโทรศัพท์ของคุณ) เพื่อรอ
การอนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม แยกตามรันไทม์: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## การยอมรับ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## ประวัติดาว

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ใบอนุญาต

MIT · สร้างโดย [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
