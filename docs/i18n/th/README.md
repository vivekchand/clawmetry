<!-- i18n-src:12b97259721e -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**เอเจนต์สามารถเรียกใช้เครื่องมือได้เป็นร้อยครั้งโดยไม่มีความคืบหน้าใดๆ** ClawMetry
อ่านไฟล์เซสชันที่เอเจนต์เขียนโค้ดของคุณเขียนอยู่แล้ว และนำไทม์ไลน์
การเรียกเครื่องมือ และข้อมูลโทเค็นกับต้นทุนที่รันไทม์เปิดเผยมาไว้ในมุมมอง
เดียว เพื่อให้คุณแยกแยะได้ว่ารันที่ยาวนานนั้นกำลังทำงานอยู่ หรือติดขัด

ใช้งานได้กับ **รันไทม์เอเจนต์ AI 31 ตัว** — Claude Code, OpenAI Codex, Hermes, OpenClaw และอีก 27 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ ([รายการทั้งหมด](SUPPORTED_RUNTIMES.txt) สร้างขึ้นจากแคตตาล็อก)

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างโดยอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใดๆ: มันจะค้นหารันไทม์เอเจนต์
ที่คุณมีอยู่แล้ว อ่านแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีที่มันทำงานเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ก่อนติดตั้ง

| | |
|---|---|
| **มันทำอะไร** | อ่านไฟล์เซสชันและล็อกที่เอเจนต์ของคุณเขียนอยู่แล้ว ไม่มี SDK ไม่ต้องแก้โค้ด ไม่ต้องฝัง instrumentation ในแอปของคุณ |
| **สิ่งที่คุณจะเห็น** | ไทม์ไลน์เซสชัน การรีเพลย์ทีละเครื่องมือ รายละเอียดโทเค็นและต้นทุน และสัญญาณของวิถีการทำงาน (การวนซ้ำ ความล้มเหลวซ้ำๆ) ต่อรันไทม์ |
| **สิ่งที่ฟรี** | `pip install clawmetry` อ่านข้อมูลจาก **OpenClaw, NVIDIA NemoClaw และ Goose** โดยไม่ต้องมีบัญชี ไม่ต้องใช้คีย์ และไม่มีการเรียกเครือข่าย อีก 27 ตัวที่เหลือ — Claude Code, Codex, Cursor และตัวอื่นๆ — ถูกอ่านโดยส่วนขยาย `clawmetry-pro` แบบโคลสซอร์ส ซึ่งมาพร้อมกับทดลองใช้ 7 วันหรือแพลน — ดู [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) สำหรับรายละเอียดการแบ่งที่ชัดเจน |
| **วิธีเริ่มต้น** | `pip install clawmetry && clawmetry` จากนั้นเปิด localhost:8900 ยังไม่มีเอเจนต์บนเครื่องนี้ใช่ไหม? `clawmetry --sample` จะเปิดด้วยเซสชันสังเคราะห์ที่มีป้ายกำกับสามชุด |
| **ข้อมูลที่ออกจากเครื่องของคุณ** | ไม่มีข้อมูลเซสชันใดๆ เว้นแต่คุณจะรัน `clawmetry connect` มีสองสิ่งที่ทำงานโดยค่าเริ่มต้น ทั้งคู่สามารถปิดได้และไม่มีเนื้อหาเซสชันติดไปด้วย: การส่งสัญญาณติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันจาก PyPI ปลายทางทุกแห่งถูกรวบรวมไว้ใน [docs/EGRESS.md](docs/EGRESS.md) สร้างขึ้นใหม่จากการดักจับข้อมูลบนสาย ไม่ใช่จากการอ่านคอมเมนต์ |

มีข้อจำกัดสองอย่างที่ควรรู้ก่อนตัดสินผลลัพธ์: รันไทม์แต่ละตัวเปิดเผยข้อมูล
ที่แตกต่างกันมาก (บางตัวไม่เปิดเผยต้นทุนเลย — [ตารางเปรียบเทียบ](docs/compatibility.md)
บอกว่าตัวไหนเป็นอย่างไร ต่อรันไทม์) และการสังเกตการกระทำนั้นไม่เหมือนกับการสามารถ
บล็อกมันได้ ([การควบคุมใดที่ใช้งานได้จริง ต่อรันไทม์](docs/APPROVALS.md))


## ใช้งานได้กับรันไทม์เอเจนต์ 31 ตัว

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**บนแพลนแบบเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุกรันไทม์ได้รับแดชบอร์ดเดียวกัน รันหลายตัวพร้อมกันแล้วตัวสลับที่ส่วนหัว
จะปรับขอบเขตทุกแท็บให้เป็นของตัวใดตัวหนึ่งโดยอัตโนมัติ

สร้างเอเจนต์ของคุณเองบน SDK แทนหรือเปล่า? ตัว interceptor ก็ติดตามการเรียก LLM
ของมันได้เช่นกัน ดู [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: แต่ละเอเจนต์ทำอะไรบ้าง ทีละเทิร์น พร้อมการรีเพลย์
- **ต้นทุนและโทเค็น**: ต่อรันไทม์ โมเดล เซสชัน และวัน พร้อมสัญญาณความผิดปกติ
- **Flow**: แผนภาพสดของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกเครื่องมือแบบเรียลไทม์
- **Context blowout**: การใช้งานหน้าต่างบริบทที่คำนวณตามผู้ให้บริการแต่ละราย การบีบอัด (compaction) เทียบกับการล้นแบบบังคับ พร้อมแผนที่ต่อรันไทม์ว่าอะไรที่เรา *มองไม่เห็น* ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **หน่วยความจำและสกิล**: ไฟล์และสกิลที่แต่ละรันไทม์โหลดขึ้นมาจริง
- **สุขภาพและล็อก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด อัตราจำกัด สตรีมล็อกสด
- **การแจ้งเตือน**: เพดานงบประมาณ ข้อผิดพลาดพุ่งสูง เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **การอนุมัติ**: หยุดการเรียกเครื่องมือที่เสี่ยง *ก่อน* ที่มันจะรัน และอนุมัติจากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการเฝ้าติดตาม

มีสองคำถามที่ควรตอบก่อนที่คุณจะเชื่อใจเครื่องมือเปรียบเทียบเอเจนต์ใดๆ

**มันจัดการกับการล้นของหน้าต่างบริบทข้ามรันไทม์อย่างไร?**

เปอร์เซ็นต์การใช้งานจะซื่อสัตย์ได้ก็ต่อเมื่อสิ่งที่ใช้หารมันถูกต้อง ClawMetry
คำนวณขนาดหน้าต่างตามผู้ให้บริการแต่ละรายจาก[ตารางที่คุณอ่านและ
ส่ง PR ได้](clawmetry/context_windows.py) ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดรันไทม์ทั้ง 31 ตัว
ด้วยไม้บรรทัดของผู้จำหน่ายรายเดียว นั่นสำคัญมาก: เทิร์นของ GPT-5 ขนาด 300K
ที่วัดเทียบกับ 200K ของ Anthropic จะอ่านได้ว่า ">100% ล้นแล้ว" ทั้งที่จริงแล้ว
มันอยู่ที่ 75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อนเทิร์นของ DeepSeek
ขนาด 130K ที่ล้นจริงๆ ให้ดูเหมือนสบายๆ ที่ 65%

ทุกหน้าต่างจะมาพร้อมแหล่งที่มา: `model_table`, `explicit_marker`,
`observed_floor` หรือ `default` ที่ซื่อสัตย์เมื่อเราไม่รู้จักโมเดลนั้น มาตรวัด
ที่สร้างจากการเดาจะไม่แสดงด้วยความน่าเชื่อถือเดียวกันกับที่สร้างจากการค้นหา
ที่แท้จริง

ClawMetry มองเห็นเหตุการณ์การบีบอัด (compaction) ได้เฉพาะในบางรันไทม์เท่านั้น
ดังนั้น `GET /api/context-coverage` จึงรายงานต่อรันไทม์ว่า **เลขศูนย์หมายถึง
"รันได้ราบรื่น" หรือ "เรามองไม่เห็น"** เลข `0` ที่แท้จริงแล้วหมายถึงมองไม่เห็น
ก็จะระบุไว้อย่างนั้น [รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**instrumentation มีต้นทุนเท่าไหร่?**

| เส้นทาง | เพิ่มให้เอเจนต์ของคุณ | ค่าเริ่มต้นหรือไม่? |
|---|---|---|
| การไล่อ่านไฟล์เซสชัน (ครบทั้ง 31 รันไทม์) | **0** เป็นโปรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 มิลลิวินาที** ต่อการเรียก LLM หรือ 0.009% ของการเรียก 5 วินาที | ปิด |
| Pre-tool hook gate (warm cache) | **+44 มิลลิวินาที** ต่อการเรียกเครื่องมือที่ถูกกั้น เหนือกว่าพื้นฐานของอินเทอร์พรีเตอร์ที่ 36 มิลลิวินาที | ปิด |
| Enforcement proxy | **+9.7 มิลลิวินาที** ต่อการเรียก LLM | ปิด |

ต้นทุนของโฮสต์ daemon: การรับข้อมูล **2,762 เหตุการณ์/วินาที**, **710 ไบต์/เหตุการณ์**
บนดิสก์ (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ประมาณ 12% ของหนึ่งคอร์** อย่างต่อเนื่อง
บนการติดตั้งที่มีงานหนัก ตัวเลขสุดท้ายนั้นเกินงบประมาณ 5-10% ที่เราระบุไว้เอง
ดังนั้นจึงเผยแพร่เป็นบั๊กที่ต้องไล่ตามแก้ แทนที่จะละไว้ไม่พูดถึง

วัดบน Apple M2 Pro ด้วย `benchmarks/overhead.py` ฮาร์เนสรันแต่ละเงื่อนไข
ในโปรเซสแยกต่างหาก สลับลำดับของมัน และ **ปฏิเสธที่จะพิมพ์ตัวเลขเมื่อรอบต่างๆ
ไม่ตรงกันในเรื่องเครื่องหมาย (บวก/ลบ)** รันมันบนเครื่องของคุณเองได้ในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัด รวมถึง hook gates และ enforcement proxy และฮาร์เนสนี้
รันบน Linux, macOS และ Windows ใน CI มีผลลัพธ์สองอย่างที่ควรรู้: proxy
มีต้นทุนสูงกว่าประมาณเจ็ดเท่าบน Windows เทียบกับ Linux และ daemon
ในปัจจุบันใช้งานต่อเนื่องประมาณ 12% ของหนึ่งคอร์ ซึ่งเกินงบประมาณ 5-10%
ของเราเอง JSON ดิบ วิธีการ และสิ่งที่ยังไม่ได้วัดอยู่ใน
[docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แพลน | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ เฉพาะในเครื่อง | $0 |
| **Starter** | รันไทม์อื่นๆ ทั้งหมดข้างต้น มุมมองกองเอเจนต์ (fleet view) การซิงค์กับคลาวด์ | $9 ต่อโหน / เดือน |
| **Pro** | Starter + การควบคุมและการประเมินผล: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมิน (evals) การตรวจจับความผิดปกติ ตัวเพิ่มประสิทธิภาพต้นทุน การส่งออก OTel บันทึกตรวจสอบที่ป้องกันการปลอมแปลง | $19 ต่อโหน / เดือน |

แพลนรายปี Enterprise และตัวเลขปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ใบอนุญาตแบบโฮสต์เอง
ใช้งานได้โดยไม่ต้องพึ่งคลาวด์ (`clawmetry license`) การแบ่งฟรี/เสียเงินที่แน่ชัด
อยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันใดออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** — ไม่มีพรอมต์ คำตอบ อาร์กิวเมนต์เครื่องมือ
เนื้อหาไฟล์ หรือบรรทัดล็อกใดๆ เมื่อคุณเชื่อมต่อ สแนปช็อตจะถูกเข้ารหัสแบบ
end-to-end ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถอดรหัสในเบราว์เซอร์ของคุณ
หากโหนดหนึ่งไม่มีคีย์ การอัปโหลดจะถูกข้าม แทนที่จะส่งแบบไม่เข้ารหัส และไม่มี
การตอบกลับจากเซิร์ฟเวอร์ใดที่จะปิดการทำงานนี้ได้

มีสองสิ่งที่ทำงานโดยค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งคู่สามารถปิดได้และ
ไม่มีข้อมูลเซสชันติดไปด้วย: การส่งสัญญาณติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบ
เวอร์ชันเทียบกับ PyPI การติดตั้งแบบค่าเริ่มต้นยังค้นหา IP สาธารณะของคุณครั้งหนึ่ง
สำหรับข้อความแบนเนอร์ตอนเริ่มต้น ปลายทางทุกแห่ง สิ่งที่มันนำไป และวิธีปิดมัน
ถูกระบุไว้ใน [docs/EGRESS.md](docs/EGRESS.md); การติดตั้งแบบโฮสต์เอง เปลี่ยนปลายทาง
และแบบตัดขาดจากเครือข่าย (air-gapped) จะไม่มีการเรียกออกตามดุลยพินิจใดๆ เลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราส่งให้คุณ เรื่องนี้เคยเป็น
แค่คำสัญญา แต่ตอนนี้มันเป็นสิ่งที่คุณตรวจสอบได้ ทุกบรรทัดที่แตะต้องคีย์ของคุณ
อยู่ในไฟล์เดียวที่อ่านได้ [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งมาพร้อมกับ wheel และถูกส่งมาตามที่เป็น (verbatim) พร้อมล็อกไว้ด้วยแฮช
Subresource Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่การกระทำนี้ไม่ได้พิสูจน์: เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้
ดังนั้นเราจึงสามารถให้บริการหน้าเว็บที่ต่างออกไปได้ แฮชความสมบูรณ์ปกป้องคุณ
จาก CDN ที่ถูกบุกรุก ไม่ใช่จากผู้จำหน่ายเอง สิ่งที่คุณได้รับคือการแทนที่ใดๆ
จะต้องเป็นความจงใจ มองเห็นได้ในซอร์สของหน้าเว็บ และแตกต่างจากอาร์ติแฟกต์บน
PyPI ที่ใครก็ดึงมาได้ การโฮสต์เองหรืออยู่ในเครื่องอย่างเดียวจะขจัดการพึ่งพา
นี้ออกไปทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # then: clawmetry
```

หรือคำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8+ บน macOS, Linux หรือ Windows และมีรันไทม์เอเจนต์อย่างน้อยหนึ่งตัว
บนเครื่องเดียวกัน คำแนะนำ Docker: [docs/DOCKER.md](docs/DOCKER.md)

หรือให้เอเจนต์ตั้งค่าให้คุณ สกิล [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
สอน Claude Code, Codex, Cursor, Gemini CLI, Copilot หรือ OpenCode ให้ติดตั้ง
ClawMetry รายงานว่าเอเจนต์บนเครื่องกำลังทำอะไรและใช้จ่ายเท่าไหร่ หยุดเซสชัน
หนึ่งตามคำขอ และหน่วงการเรียกเครื่องมือที่เสี่ยงไว้รออนุมัติ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | แต่ละอะแดปเตอร์อ่านอะไร และวิธีเพิ่มรันไทม์ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างตามผู้ให้บริการแต่ละราย การบีบอัดเทียบกับการล้น ความครอบคลุมต่อรันไทม์ |
| [Overhead](docs/OVERHEAD.md) | instrumentation มีต้นทุนเท่าไหร่ วัดผลจริง พร้อมฮาร์เนสสำหรับทำซ้ำ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับแพลน license CLI |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การกั้นก่อนดำเนินการ การให้คะแนนความเสี่ยง การอนุมัติผ่านโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก traces ไปที่ไหนก็ได้ รับเข้า OTLP จากที่ไหนก็ได้ |
| [นำเอเจนต์ของคุณเองมาใช้](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้ |
| [การติดตาม SDK](docs/SDK_TRACKING.md) | การระบุแหล่งที่มาของต้นทุนสำหรับเอเจนต์ที่คุณสร้างเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมาต์วอลุ่ม |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน การรันจากซอร์ส |
| [Telemetry](docs/TELEMETRY.md) | การส่งสัญญาณติดตั้งแบบไม่ระบุตัวตนและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

ตัวเลขทุกตัวด้านล่างมาจากเครื่องจริงหนึ่งเครื่อง แบบอ่านอย่างเดียว โดยไม่มี
การจัดเตรียมข้อมูลใดๆ ล่วงหน้า

**มันบอกคุณเมื่อมีบางอย่างผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่วิ่งสูงกว่าค่าเฉลี่ยรายวัน
7 เท่า และต้นทุนพุ่งสูง 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุด
มีสัญญาณของความสูญเปล่า แยกตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้คุณเห็นว่าเงินไปที่ไหน ในทุกช่วงเวลา**
$252.47 วันนี้ $513.15 สัปดาห์นี้ $1,312.92 เดือนนี้ แต่ละอย่างพร้อมโทเค็น
เบื้องหลังและสมาชิกของคุณครอบคลุมเท่าไหร่แล้ว ด้านล่างนั้น ประมาณ $1,128/เดือน
ที่แยกไว้ว่ากู้คืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้วจากการใช้ cache ซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
แผนภาพ flow สด: คุณ ช่องทางที่ข้อความมาถึง เกตเวย์ โมเดลที่กำลังตอบอยู่ตอนนี้
และเครื่องมือทุกตัวที่มันเอื้อมไปใช้ โหนดจะสว่างขึ้นเมื่องานเคลื่อนผ่านพวกมัน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง ในตารางเดียว**
มันรันอะไร มันมีต้นทุนเท่าไหร่ใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน
เห็นครั้งล่าสุดเมื่อไหร่ ใครเป็นเจ้าของ และสมาชิกครอบคลุมค่าใช้จ่ายหรือไม่
14 เอเจนต์ที่นี่ 3 เซสชันกำลังทำงาน 13 เซสชันเงียบ

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของเทิร์นหนึ่งไปที่ไหน ทีละเครื่องมือ**
หนึ่งเทิร์นของเซสชันจริง: เครื่องมือ 11 ตัวใน 11.2 นาที ราคา $1.16 การเรียก
Bash และการเรียกโมเดลแต่ละครั้งมีแถบของตัวเองบนไทม์ไลน์ ดังนั้นคำสั่งที่รัน
4.1 นาทีและคำสั่งที่รัน 226 มิลลิวินาทีจะถูกแยกแยะได้ในพริบตา

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้เกรดกับงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A สัปดาห์นี้: 54 งานที่เสร็จอย่างสะอาด 2 งานที่ขรุขระมีต้นทุน $48.57
และรันที่มีกิจกรรมน้อยเกินไปที่จะตัดสินได้ถูกตัดออกจากเกรดแทนที่จะนับเป็น
ชัยชนะ แต่ละรันที่ขรุขระเชื่อมโยงไปยังเทรซของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงว่าทำไมหน้าต่างบริบทถึงเต็มอยู่เรื่อยๆ**
715K จากหน้าต่าง 1M โทเค็นในเทิร์นล่าสุด จุดสูงสุด 83.3% การบีบอัด 4 ครั้ง
ที่ทั้งหมดเกิดขึ้นแบบเชิงรุกแทนที่จะเกิดจากการล้น พร้อมการใช้งานของทุกเทิร์น
เบื้องหลังนั้น

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานโดยที่คุณไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป ฟีดข้อมูลหยุดทำงาน
ต้นทุนพุ่งสูง โทเค็นพุ่งสูง ข้อผิดพลาดเพิ่มขึ้น ข้อผิดพลาดพุ่งสูง เกิน
เพดานงบประมาณ ตรงกับลายเซ็นภัยคุกคาม พบผลการตรวจจากเครื่องมือความปลอดภัย
ท่าทีความปลอดภัยเปลี่ยนแปลง กฎของคุณเองเป็นตัวเลือกเสริมเพิ่มเติมจากนี้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การหน่วงการเรียกที่เสี่ยงเป็นแบบเลือกเปิดใช้ และมาพร้อมสถานะปิดตั้งแต่แรก**
การลบแบบเรียกซ้ำ (recursive delete) การ force push การใช้ sudo ความลับ
(secrets) การติดตั้งแพ็กเกจ และการเรียกออกภายนอก แต่ละอย่างมีกฎที่คุณเปิดใช้
ได้ จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดูและไม่เปลี่ยนแปลงอะไรเลย เมื่อเปิดใช้
แล้ว การเรียกที่ตรงเงื่อนไขจะรอที่นี่ (หรือบนโทรศัพท์ของคุณ) เพื่อรอการ
อนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม ต่อรันไทม์: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

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
