<!-- i18n-src:61beb8393e2f -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**เอเจนต์สามารถเรียกใช้เครื่องมือได้เป็นร้อยครั้งโดยไม่มีความคืบหน้าใดๆ** ClawMetry
อ่านไฟล์เซสชันที่เอเจนต์เขียนโค้ดของคุณเขียนขึ้นอยู่แล้ว และนำไทม์ไลน์
การเรียกใช้เครื่องมือ และข้อมูลโทเคนกับค่าใช้จ่ายเท่าที่รันไทม์เปิดเผยมาไว้ในมุมมองเดียว
เพื่อให้คุณสามารถแยกแยะการทำงานที่ยาวนานว่ากำลังไปได้สวยหรือติดอยู่กับที่

ใช้งานร่วมกับ **รันไทม์ AI เอเจนต์ 30 ตัว** — Claude Code, OpenAI Codex, Hermes, OpenClaw และอีก 26 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ ([รายการทั้งหมด](SUPPORTED_RUNTIMES.txt) สร้างขึ้นจากแคตตาล็อก)

> 🌐 **อ่านภาษานี้:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใดๆ ระบบจะค้นหารันไทม์เอเจนต์
ที่คุณมีอยู่แล้ว อ่านแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ก่อนที่คุณจะติดตั้ง

| | |
|---|---|
| **มันทำอะไร** | อ่านไฟล์เซสชันและล็อกที่เอเจนต์ของคุณเขียนขึ้นอยู่แล้ว ไม่มี SDK ไม่ต้องแก้โค้ด ไม่มีการฝังเครื่องมือวัดใดๆ ในแอปของคุณ |
| **คุณเห็นอะไร** | ไทม์ไลน์เซสชัน การเล่นซ้ำทีละเครื่องมือ การแจกแจงโทเคนและค่าใช้จ่าย และสัญญาณเส้นทางการทำงาน (การวนซ้ำ ความล้มเหลวซ้ำๆ) ต่อรันไทม์ |
| **สิ่งที่ฟรี** | `pip install clawmetry` อ่านข้อมูลจาก **OpenClaw, NVIDIA NemoClaw และ Goose** ได้โดยไม่ต้องมีบัญชี ไม่ต้องมีคีย์ และไม่มีการเรียกเครือข่ายใดๆ ส่วนอีก 27 ตัวที่เหลือ ได้แก่ Claude Code, Codex, Cursor และตัวอื่นๆ จะถูกอ่านโดยส่วนเสริม `clawmetry-pro` แบบปิดซอร์ส ซึ่งมาพร้อมกับช่วงทดลองใช้ 7 วันหรือแพลน ดูรายละเอียดการแบ่งที่แน่นอนได้ที่ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) |
| **วิธีเริ่มต้น** | `pip install clawmetry && clawmetry` แล้วเปิด localhost:8900 ยังไม่มีเอเจนต์บนเครื่องนี้ใช่ไหม `clawmetry --sample` จะเปิดขึ้นด้วยเซสชันสังเคราะห์ที่มีป้ายกำกับสามเซสชัน |
| **สิ่งที่ออกจากเครื่องของคุณ** | ไม่มีข้อมูลเซสชัน เว้นแต่คุณจะรัน `clawmetry connect` มีสองสิ่งที่ทำงานตามค่าเริ่มต้น ทั้งคู่สามารถปิดได้และไม่มีเนื้อหาเซสชันติดไปด้วย ได้แก่ การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันจาก PyPI ปลายทางทุกจุดถูกรวบรวมไว้ใน [docs/EGRESS.md](docs/EGRESS.md) ซึ่งสร้างขึ้นจากการดักจับข้อมูลบนสายจริง ไม่ใช่จากการอ่านคอมเมนต์ |

ข้อจำกัดสองข้อที่ควรรู้ก่อนตัดสินผลลัพธ์ คือรันไทม์แต่ละตัวเปิดเผยข้อมูลที่แตกต่างกันมาก
(บางตัวไม่เผยแพร่ค่าใช้จ่ายเลย [ตารางเปรียบเทียบ](docs/compatibility.md)
จะบอกว่าตัวไหนเป็นอย่างไร) และการสังเกตการกระทำก็ไม่เหมือนกับการสามารถ
บล็อกมันได้ ([การควบคุมใดที่ใช้งานได้จริง ต่อรันไทม์](docs/APPROVALS.md))


## ใช้งานร่วมกับรันไทม์เอเจนต์ 30 ตัว

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**บนแพลนแบบเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุกรันไทม์จะได้แดชบอร์ดแบบเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัว
จะปรับขอบเขตทุกแท็บให้เข้ากับรันไทม์ที่เลือกใหม่

สร้างเอเจนต์ของคุณเองด้วย SDK แทนหรือเปล่า ตัว interceptor ก็ติดตามการเรียก LLM
ของมันได้เช่นกัน ดู [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและบทสนทนา**: สิ่งที่เอเจนต์แต่ละตัวทำ ทีละเทิร์น พร้อมการเล่นซ้ำ
- **ค่าใช้จ่ายและโทเคน**: ต่อรันไทม์ โมเดล เซสชัน และวัน พร้อมสัญญาณความผิดปกติ
- **โฟลว์**: แผนภาพสดของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกเครื่องมือแบบเรียลไทม์
- **Context blowout**: การใช้พื้นที่หน้าต่างบริบทตามขนาดของแต่ละผู้ให้บริการ การบีบอัดเทียบกับการล้นแบบบังคับ พร้อมแผนที่ต่อรันไทม์ว่าสิ่งที่เรา *มองไม่เห็น* คืออะไร ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **หน่วยความจำและทักษะ**: ไฟล์และทักษะที่รันไทม์แต่ละตัวโหลดขึ้นมาจริง
- **สุขภาพและล็อก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด อัตราจำกัด สตรีมล็อกสด
- **การแจ้งเตือน**: เพดานงบประมาณ การพุ่งขึ้นของข้อผิดพลาด เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **การอนุมัติ**: หยุดการเรียกเครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะทำงาน และอนุมัติได้จากมือถือของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการเฝ้าดู

มีสองคำถามที่ควรได้คำตอบก่อนที่คุณจะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ใดๆ

**มันจัดการกับการล้นของหน้าต่างบริบทข้ามรันไทม์อย่างไร**

เปอร์เซ็นต์การใช้งานจะน่าเชื่อถือได้ก็ต่อเมื่อสิ่งที่ใช้หารนั้นถูกต้อง ClawMetry
กำหนดขนาดหน้าต่างตามผู้ให้บริการแต่ละราย จาก[ตารางที่คุณสามารถอ่านและ
ส่ง PR ได้](clawmetry/context_windows.py) ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดรันไทม์ทั้ง 30 ตัว
ด้วยไม้บรรทัดของผู้ให้บริการรายเดียว นั่นสำคัญ เพราะเทิร์นขนาด 300K ของ GPT-5
เมื่อเทียบกับ 200K ของ Anthropic จะอ่านได้ว่า ">100%, blown" ทั้งที่จริงแล้วมันอยู่ที่
75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อนเทิร์น 130K ของ DeepSeek
ที่ล้นจริงๆ ให้ดูเหมือนสบายๆ ที่ 65%

ทุกหน้าต่างมาพร้อมที่มาของมัน: `model_table`, `explicit_marker`,
`observed_floor`, หรือ `default` ที่ตรงไปตรงมาเมื่อเราไม่รู้จักโมเดลนั้น มาตรวัด
ที่สร้างจากการเดาจะไม่แสดงผลด้วยความน่าเชื่อถือเท่ากับที่สร้างจากการค้นหาข้อมูลจริง

ClawMetry มองเห็นเหตุการณ์การบีบอัด (compaction) ได้เฉพาะในบางรันไทม์เท่านั้น ดังนั้น
`GET /api/context-coverage` จะรายงานต่อรันไทม์ว่า **เลข 0 หมายถึง "รันได้สะอาด"
หรือ "เรามองไม่เห็น"** เลข `0` ที่จริงๆ แล้วหมายถึงมองไม่เห็นก็จะบอกไว้เช่นนั้น
[รายละเอียดฉบับเต็ม](docs/CONTEXT_BLOWOUT.md)

**เครื่องมือวัดนี้มีต้นทุนเท่าไร**

| เส้นทาง | เพิ่มให้กับเอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การไล่อ่านไฟล์เซสชัน (ทั้ง 30 รันไทม์) | **0** เป็นโพรเซสแยก ไม่มีโค้ด ClawMetry ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ต่อการเรียก LLM หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (แคชอุ่น) | **+44 ms** ต่อการเรียกเครื่องมือที่ถูกกั้น เหนือพื้นฐานตัวแปลภาษาที่ 36 ms | ปิด |
| Enforcement proxy | **+9.7 ms** ต่อการเรียก LLM | ปิด |

ต้นทุนของโฮสต์ daemon: รับข้อมูลเข้า **2,762 เหตุการณ์/วินาที** ใช้พื้นที่ดิสก์
**710 ไบต์/เหตุการณ์** (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ราว 12% ของหนึ่งคอร์**
อย่างต่อเนื่องบนเครื่องที่ติดตั้งใช้งานหนัก ตัวเลขสุดท้ายนี้เกินงบประมาณ 5-10%
ที่เราตั้งไว้เอง จึงเผยแพร่ไว้ในฐานะบั๊กที่ต้องตามแก้ ไม่ใช่ปิดบังไว้

วัดบนเครื่อง Apple M2 Pro ด้วย `benchmarks/overhead.py` เครื่องมือทดสอบนี้รัน
แต่ละเงื่อนไขในโพรเซสแยกกัน สลับลำดับกัน และ **ปฏิเสธที่จะแสดงตัวเลขเมื่อรอบ
การทดสอบให้เครื่องหมายที่ขัดแย้งกัน** รันมันบนเครื่องของคุณเองได้ภายในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดผล รวมถึง hook gates และ enforcement proxy ด้วย
และเครื่องมือทดสอบนี้รันบน Linux, macOS และ Windows ใน CI ผลลัพธ์สองอย่าง
ที่ควรรู้ไว้คือ proxy มีต้นทุนสูงกว่าบน Windows ประมาณเจ็ดเท่าเมื่อเทียบกับ Linux
และ daemon ในปัจจุบันใช้ทรัพยากรอยู่ราว 12% ของหนึ่งคอร์ ซึ่งเกินงบประมาณ 5-10%
ที่เราตั้งไว้เอง ข้อมูล JSON ดิบ วิธีการ และสิ่งที่ยังไม่ได้วัดอยู่ใน
[docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แพลน | ครอบคลุมอะไร | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ เฉพาะในเครื่อง | $0 |
| **Starter** | รันไทม์อื่นๆ ทั้งหมดข้างต้น มุมมองกองเอเจนต์ การซิงค์กับคลาวด์ | $9 ต่อโหนด/เดือน |
| **Pro** | Starter บวกกับการควบคุมและการประเมินผล: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมิน การตรวจจับความผิดปกติ ตัวปรับค่าใช้จ่ายให้เหมาะสม การส่งออก OTel บันทึกการตรวจสอบที่ป้องกันการปลอมแปลง | $19 ต่อโหนด/เดือน |

แพลนรายปี Enterprise และตัวเลขปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ใบอนุญาตแบบโฮสต์เอง
ใช้งานได้โดยไม่ต้องใช้คลาวด์ (`clawmetry license`) การแบ่งฟรี/เสียเงินที่แน่นอน
อยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันใดออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** ไม่มีพรอมป์ คำตอบ อาร์กิวเมนต์ของเครื่องมือ
เนื้อหาไฟล์ หรือบรรทัดล็อก เมื่อคุณเชื่อมต่อจริง สแนปช็อตจะถูกเข้ารหัสแบบ end-to-end
ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณเลย และถอดรหัสในเบราว์เซอร์ของคุณ ถ้าโหนดหนึ่ง
ไม่มีคีย์ การอัปโหลดจะถูกข้ามไปแทนที่จะส่งแบบไม่เข้ารหัส และไม่มีการตอบกลับจาก
เซิร์ฟเวอร์ใดๆ ที่จะปิดกลไกนี้ได้

มีสองสิ่งที่ทำงานตามค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งคู่สามารถปิดได้และไม่มี
ข้อมูลเซสชันติดไปด้วย ได้แก่ การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบ
เวอร์ชันเทียบกับ PyPI การติดตั้งตามค่าเริ่มต้นยังค้นหา public IP ของคุณครั้งเดียว
สำหรับข้อความแบนเนอร์ตอนเริ่มต้น ปลายทางทุกจุด สิ่งที่มันบรรทุกไป และวิธีปิด
ถูกระบุไว้ใน [docs/EGRESS.md](docs/EGRESS.md) การติดตั้งแบบโฮสต์เอง ชี้ปลายทางใหม่
หรือแบบตัดขาดจากเครือข่าย จะไม่มีการเรียกออกที่เป็นทางเลือกเลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราส่งให้คุณ สิ่งนี้เคยเป็นแค่
คำสัญญา แต่ตอนนี้เป็นสิ่งที่คุณตรวจสอบได้ ทุกบรรทัดที่แตะต้องคีย์ของคุณอยู่ในไฟล์
ที่อ่านได้ไฟล์เดียว [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งมาพร้อมกับ wheel และถูกส่งแบบคำต่อคำ พร้อมปักหมุดด้วยแฮช Subresource
Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่การตรวจสอบนี้พิสูจน์ไม่ได้คือ เราเป็นผู้ให้บริการหน้าเพจที่โหลดไฟล์นี้ ดังนั้น
เราจึงสามารถให้บริการหน้าเพจอื่นแทนได้ แฮชความสมบูรณ์ปกป้องคุณจาก CDN ที่ถูกโจมตี
ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้คือ การเปลี่ยนแปลงใดๆ ต้องเป็นการจงใจ
มองเห็นได้ในซอร์สโค้ดของหน้าเพจ และแตกต่างจากอาร์ทิแฟกต์บน PyPI ที่ใครก็ดึงมาดูได้
การโฮสต์เองหรืออยู่ในเครื่องเพียงอย่างเดียวจะขจัดการพึ่งพานี้ออกไปทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # then: clawmetry
```

หรือแบบบรรทัดเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8+ บน macOS, Linux หรือ Windows และมีรันไทม์เอเจนต์อย่างน้อยหนึ่งตัว
บนเครื่องเดียวกัน คำแนะนำ Docker: [docs/DOCKER.md](docs/DOCKER.md)

หรือให้เอเจนต์ตั้งค่าให้คุณเลย ทักษะ [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
จะสอน Claude Code, Codex, Cursor, Gemini CLI, Copilot หรือ OpenCode ให้
ติดตั้ง ClawMetry รายงานว่าเอเจนต์บนเครื่องกำลังทำอะไรและใช้จ่ายเท่าไร
หยุดเซสชันหนึ่งเมื่อมีการร้องขอ และกักการเรียกเครื่องมือที่มีความเสี่ยงไว้เพื่อรอการอนุมัติ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | สิ่งที่แต่ละอะแดปเตอร์อ่าน และวิธีเพิ่มรันไทม์ใหม่ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างบริบทตามผู้ให้บริการ การบีบอัดเทียบกับการล้น ความครอบคลุมต่อรันไทม์ |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของเครื่องมือวัดที่วัดได้จริง พร้อมเครื่องมือทดสอบเพื่อทำซ้ำ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับแพลน CLI ใบอนุญาต |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การกั้นก่อนดำเนินการ การให้คะแนนความเสี่ยง การอนุมัติผ่านมือถือ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก traces ไปที่ไหนก็ได้ รับ OTLP จากอะไรก็ได้ |
| [นำเอเจนต์ของคุณมาเอง](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้จริง |
| [SDK tracking](docs/SDK_TRACKING.md) | การนับค่าใช้จ่ายสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมานท์วอลุ่ม |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ทำงานอย่างไรภายใน การรันจากซอร์ส |
| [Telemetry](docs/TELEMETRY.md) | การ ping การติดตั้งและการเปิดแอปเดสก์ท็อปแบบไม่ระบุตัวตน และวิธีปิดมัน |

## ภาพหน้าจอ

ทุกตัวเลขด้านล่างมาจากเครื่องจริงหนึ่งเครื่อง แบบอ่านอย่างเดียว โดยไม่มีการสร้างข้อมูลเทียมใดๆ

**มันบอกคุณเมื่อมีอะไรผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่วิ่งสูงกว่าค่าเฉลี่ยรายวันถึง 7 เท่า
และค่าใช้จ่ายที่พุ่งขึ้น 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุด
มีสัญญาณความสูญเปล่า จำแนกตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้คุณเห็นว่าเงินไปไหน ในทุกช่วงเวลา**
$252.47 วันนี้ $513.15 สัปดาห์นี้ $1,312.92 เดือนนี้ แต่ละตัวมาพร้อมโทเคน
เบื้องหลัง และจำนวนที่การสมัครสมาชิกของคุณครอบคลุมอยู่แล้ว ด้านล่างนั้น
ประมาณ $1,128/เดือน ที่จำแนกว่ากู้คืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้วจาก
การใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดภาพว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
แผนภาพโฟลว์แบบสด: คุณ ช่องทางที่ข้อความมาถึง เกตเวย์ โมเดลที่กำลังตอบอยู่ตอนนี้
และเครื่องมือทุกตัวที่มันเรียกใช้ โหนดต่างๆ จะสว่างขึ้นเมื่องานเคลื่อนผ่าน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง ในตารางเดียว**
สิ่งที่มันรัน ค่าใช้จ่ายใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน เห็นครั้งล่าสุดเมื่อไร
ใครเป็นเจ้าของ และการสมัครสมาชิกครอบคลุมค่าใช้จ่ายหรือไม่ มีเอเจนต์ 14 ตัวที่นี่
3 เซสชันกำลังทำงาน 13 ตัวเงียบอยู่

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงว่าเวลาและเงินของแต่ละเทิร์นไปที่ไหน ทีละเครื่องมือ**
หนึ่งเทิร์นของเซสชันจริง: เครื่องมือ 11 ตัวใน 11.2 นาที ราคา $1.16 การเรียก Bash
และการเรียกโมเดลแต่ละครั้งจะได้แถบของตัวเองบนไทม์ไลน์ ดังนั้นคำสั่งที่รันไป 4.1 นาที
กับคำสั่งที่รันไป 226ms จึงแยกออกจากกันได้ในทันที

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้เกรดงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A ในสัปดาห์นี้: 54 งานเสร็จสมบูรณ์ 2 งานที่ขรุขระมีค่าใช้จ่าย $48.57 และการรัน
ที่มีกิจกรรมน้อยเกินไปที่จะตัดสินได้ถูกตัดออกจากการให้เกรดแทนที่จะนับเป็นชัยชนะ
แต่ละงานที่ขรุขระมีลิงก์ไปยัง trace ของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงว่าทำไมหน้าต่างบริบทถึงเต็มอยู่เรื่อยๆ**
715K จากหน้าต่าง 1M โทเคนในเทิร์นล่าสุด จุดสูงสุดที่ 83.3% การบีบอัด 4 ครั้ง
ที่ทั้งหมดเกิดขึ้นแบบเชิงรุกแทนที่จะเกิดจากการล้น พร้อมการใช้งานของทุกเทิร์นเบื้องหลัง

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป ฟีดข้อมูลเทเลเมทรีหยุดทำงาน
ค่าใช้จ่ายพุ่งขึ้น การใช้โทเคนพุ่งขึ้น ข้อผิดพลาดเพิ่มขึ้น ข้อผิดพลาดพุ่งขึ้น
เพดานงบประมาณ ลายเซ็นภัยคุกคามที่ตรงกัน ผลตรวจพบจากเครื่องมือความปลอดภัย
สถานะความปลอดภัยเปลี่ยนแปลง กฎของคุณเองเป็นตัวเลือกเสริมเพิ่มเติมได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การกักการเรียกที่มีความเสี่ยงเป็นแบบเลือกเปิดเอง และปิดตามค่าเริ่มต้น**
การลบแบบเรียกซ้ำ, force push, sudo, ข้อมูลลับ, การติดตั้งแพ็กเกจ และการเรียกออก
แต่ละอย่างมีกฎที่คุณเปิดใช้ได้เอง จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดูโดยไม่เปลี่ยนแปลง
อะไรเลย เมื่อเปิดใช้งานแล้ว การเรียกที่ตรงกับเงื่อนไขจะรอที่นี่ (หรือบนมือถือของคุณ)
เพื่อรอการอนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม ต่อรันไทม์: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## การได้รับการยอมรับ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
