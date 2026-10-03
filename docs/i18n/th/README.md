<!-- i18n-src:c99ac0512cae -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**เอเจนต์สามารถเรียกใช้ tool ได้นับร้อยครั้งโดยไม่มีความคืบหน้าเลยก็ได้** ClawMetry
อ่านไฟล์เซสชันที่เอเจนต์โค้ดของคุณเขียนขึ้นอยู่แล้ว และนำไทม์ไลน์
การเรียกใช้ tool และข้อมูลโทเค็นกับต้นทุนที่ runtime เปิดเผยออกมา มารวมไว้ในมุมมองเดียว — เพื่อให้คุณแยกแยะได้ว่างานที่รันไปนาน ๆ นั้นกำลังทำงานได้ผลอยู่ หรือกำลังติดอยู่กับที่

ใช้งานได้กับ **33 AI agent runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw และอีก 29 ตัว แดชบอร์ดเดียวสำหรับฟลีตเอเจนต์ทั้งหมดของคุณ ([รายการทั้งหมด](SUPPORTED_RUNTIMES.txt) สร้างขึ้นจากแคตาล็อก)

> 🌐 **อ่านเวอร์ชันภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

หนึ่งคำสั่ง ไม่ต้องตั้งค่าใด ๆ ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่า: มันจะค้นหา agent runtime
ที่คุณมีอยู่แล้ว อ่านแบบ read-only เท่านั้น และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ก่อนติดตั้ง

| | |
|---|---|
| **มันทำอะไร** | อ่านไฟล์เซสชันและล็อกที่เอเจนต์ของคุณเขียนอยู่แล้ว ไม่ต้องใช้ SDK ไม่ต้องแก้โค้ด ไม่ต้องฝัง instrumentation ในแอปของคุณ |
| **คุณจะเห็นอะไร** | ไทม์ไลน์เซสชัน การเล่นซ้ำทีละ tool การแบ่งโทเค็นและต้นทุน และสัญญาณเชิงพฤติกรรม (การวนซ้ำ ความล้มเหลวที่เกิดซ้ำ) แยกตาม runtime |
| **อะไรที่ใช้ได้ฟรี** | `pip install clawmetry` อ่านข้อมูลจาก **OpenClaw, NVIDIA NemoClaw, Goose และ Qwen Code** ได้โดยไม่ต้องมีบัญชี ไม่ต้องใช้คีย์ และไม่มีการเรียกผ่านเครือข่ายใด ๆ ส่วนอีก 28 ตัว — Claude Code, Codex, Cursor และตัวที่เหลือ — จะถูกอ่านโดยส่วนเสริม `clawmetry-pro` ที่เป็นโค้ดปิด ซึ่งมาพร้อมกับช่วงทดลองใช้ 7 วันหรือแพลนที่สมัครไว้ — ดูรายละเอียดการแบ่งที่แน่นอนได้ที่ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) |
| **วิธีเริ่มต้น** | `pip install clawmetry && clawmetry` จากนั้นเปิด localhost:8900 ยังไม่มีเอเจนต์บนเครื่องนี้ใช่ไหม? `clawmetry --sample` จะเปิดขึ้นด้วยเซสชันสังเคราะห์ที่มีป้ายกำกับไว้สามเซสชัน |
| **อะไรที่ออกจากเครื่องของคุณ** | ไม่มีข้อมูลเซสชันออกไปเลย เว้นแต่คุณจะรัน `clawmetry connect` มีสองอย่างที่รันเป็นค่าเริ่มต้นโดยสามารถปิดได้ และไม่มีเนื้อหาเซสชันติดไปด้วย ได้แก่: การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันจาก PyPI ปลายทางทุกจุดถูกรวบรวมไว้ใน [docs/EGRESS.md](docs/EGRESS.md) ซึ่งสร้างขึ้นใหม่จากการตรวจจับข้อมูลที่ส่งจริง (wire capture) แทนที่จะอ่านจากคอมเมนต์ในโค้ด |

มีข้อจำกัดสองอย่างที่ควรรู้ก่อนตัดสินผลลัพธ์: runtime แต่ละตัวเปิดเผยข้อมูลที่แตกต่างกันมาก
(บางตัวไม่เปิดเผยต้นทุนเลย — [ตารางเปรียบเทียบ](docs/compatibility.md)
จะบอกว่าตัวไหนเป็นแบบไหน) และการสังเกตการณ์การกระทำก็ไม่เหมือนกับการสามารถ
ปิดกั้นมันได้ ([การควบคุมแบบใดที่ใช้งานได้จริง แยกตาม runtime](docs/APPROVALS.md))


## ใช้งานได้กับ 33 agent runtimes

**ใช้ได้ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**อยู่ในแพลนที่ต้องเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุก runtime จะได้แดชบอร์ดแบบเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัว
จะปรับทุกแท็บให้โฟกัสไปที่ runtime ตัวใดตัวหนึ่งได้

สร้างเอเจนต์ของคุณเองด้วย SDK แทนหรือเปล่า? ตัว interceptor ก็ติดตามการเรียก LLM
ของมันได้เหมือนกัน ดู [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: เอเจนต์แต่ละตัวทำอะไรไปบ้าง ทีละเทิร์น พร้อมเล่นซ้ำได้
- **ต้นทุนและโทเค็น**: แยกตาม runtime, โมเดล, เซสชัน และวัน พร้อมสัญญาณความผิดปกติ
- **Flow**: ไดอะแกรมสด ๆ ของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และ tool
- **Brain**: สตรีมอีเวนต์การคิดและการเรียก tool ตามเวลาจริง
- **Context blowout**: การใช้ window ที่คิดขนาดตาม provider, compaction เทียบกับ forced overflow, พร้อมแผนที่ต่อ runtime ว่าเรา *ไม่สามารถ* มองเห็นอะไรบ้าง ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: ไฟล์และ skill ที่ runtime แต่ละตัวโหลดใช้งานจริง
- **Health & logs**: ดิสก์, memory, อัตราข้อผิดพลาด, rate limit, สตรีมล็อกสด
- **Alerts**: เพดานงบประมาณ, ข้อผิดพลาดพุ่งสูง, เอเจนต์ออฟไลน์, ส่งไปที่ Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: หยุดการเรียก tool ที่มีความเสี่ยงไว้ *ก่อน* ที่จะรัน และอนุมัติได้จากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการเฝ้าสังเกต

มีสองคำถามที่ควรหาคำตอบก่อนที่จะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ใด ๆ

**มันจัดการกับ context-window blowout ข้าม runtime ได้อย่างไร?**

เปอร์เซ็นต์การใช้งานจะน่าเชื่อถือได้ก็ต่อเมื่อตัวหารนั้นถูกต้อง ClawMetry
คิดขนาด window ตาม provider จาก [ตารางที่คุณอ่านและ
ส่ง PR ได้](clawmetry/context_windows.py) ซึ่งครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดทั้ง 33
runtime ด้วยไม้บรรทัดของผู้ขายรายเดียว นี่คือเรื่องสำคัญ: เทิร์นของ GPT-5 ที่ 300K
ตัวเลขที่เทียบกับ 200K ของ Anthropic จะอ่านว่า ">100% ล้น" ในขณะที่จริง ๆ
มันอยู่ที่แค่ 75% ของ 400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อนเทิร์น DeepSeek
ที่ 130K ซึ่งล้นจริง ๆ ให้ดูเหมือนสบาย ๆ ที่ 65%

ทุก window จะมาพร้อมแหล่งที่มาของมัน: `model_table`, `explicit_marker`,
`observed_floor`, หรือ `default` ที่ซื่อสัตย์เมื่อเราไม่รู้จักโมเดลนั้น มิเตอร์ที่สร้างจากการเดา
ไม่ควรแสดงผลด้วยความน่าเชื่อถือเท่ากับมิเตอร์ที่สร้างจากการค้นหาจริง

ClawMetry มองเห็นเหตุการณ์ compaction ได้เพียงบาง runtime เท่านั้น ดังนั้น
`GET /api/context-coverage` จะรายงานแยกตาม runtime ว่า **เลขศูนย์หมายถึง
"รันผ่านฉลุย" หรือ "เรามองไม่เห็น"** เลขศูนย์ที่จริง ๆ แล้วหมายถึงมองไม่เห็นจะบอกไว้ตรง ๆ
[รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**แล้ว instrumentation มีต้นทุนเท่าไร?**

| เส้นทาง | สิ่งที่เพิ่มเข้าไปในเอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การ tail ไฟล์เซสชัน (ทั้ง 33 runtime) | **0** โปรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry อยู่ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ต่อการเรียก LLM หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (warm cache) | **+44 ms** ต่อการเรียก tool ที่ถูก gate เกินกว่าพื้นฐาน interpreter floor 36 ms | ปิด |
| Enforcement proxy | **+9.7 ms** ต่อการเรียก LLM | ปิด |

ต้นทุนของ daemon host: รับเข้า **2,762 events/sec**, **710 bytes/event** บนดิสก์
(67.7 MB ต่อ 100,000 อีเวนต์) และ **ราว 12% ของหนึ่งคอร์** ที่ใช้ต่อเนื่องบนการติดตั้งที่มีงานหนัก
ตัวเลขหลังสุดนี้เกินงบ 5-10% ที่เราตั้งไว้เอง ดังนั้นจึงเผยแพร่ไว้ในฐานะบั๊กที่ต้องตามแก้
มากกว่าจะตัดออกจากหน้านี้ไป

วัดบน Apple M2 Pro ด้วย `benchmarks/overhead.py` ชุดทดสอบนี้รันแต่ละเงื่อนไข
แยกโปรเซส สลับลำดับกัน และ **ปฏิเสธที่จะแสดงตัวเลขเมื่อแต่ละรอบให้เครื่องหมาย
ไม่ตรงกัน** รันบนเครื่องของคุณเองได้ภายในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดไว้ รวมถึง hook gate และ enforcement proxy
และชุดทดสอบนี้รันบน Linux, macOS และ Windows ใน CI มีผลลัพธ์สองอย่างที่ควรรู้:
proxy มีต้นทุนสูงกว่าบน Windows ราวเจ็ดเท่าเมื่อเทียบกับ Linux และ
ปัจจุบัน daemon ใช้ทรัพยากรต่อเนื่องราว 12% ของหนึ่งคอร์ ซึ่งเกินงบ 5-10% ของเราเอง
ข้อมูล JSON ดิบ วิธีการ และสิ่งที่ยังไม่ได้วัดอยู่ใน
[docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แพลน | ครอบคลุมอะไร | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, แดชบอร์ดเต็มรูปแบบ, local เท่านั้น | $0 |
| **Starter** | ทุก runtime ที่เหลือข้างต้น, มุมมองฟลีต, การซิงก์ขึ้นคลาวด์ | $9 ต่อโหนด / เดือน |
| **Pro** | Starter + การควบคุมและการประเมินผล: approvals, นโยบายความเสี่ยงของ tool, evals, การตรวจจับความผิดปกติ, ตัวปรับต้นทุนให้เหมาะสม, การส่งออก OTel, บันทึกการตรวจสอบที่ป้องกันการแก้ไข | $19 ต่อโหนด / เดือน |

แพลนรายปี, Enterprise และตัวเลขราคาปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ไลเซนส์แบบ self-hosted
ใช้งานได้โดยไม่ต้องพึ่งคลาวด์ (`clawmetry license`) การแบ่งฟรี/เสียเงินที่แน่นอนอยู่ใน
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** — ไม่มีพรอมต์, คำตอบ, อาร์กิวเมนต์ของ tool, เนื้อหาไฟล์
หรือบรรทัดล็อกใด ๆ เมื่อคุณเชื่อมต่อ สแนปช็อตจะถูกเข้ารหัสแบบ end-to-end
ด้วยคีย์ที่ไม่ออกจากเครื่องของคุณเลย และถูกถอดรหัสในเบราว์เซอร์ของคุณ ถ้าโหนด
ไม่มีคีย์ การอัปโหลดจะถูกข้ามไปเลยแทนที่จะส่งแบบไม่เข้ารหัส และไม่มีคำตอบจาก
เซิร์ฟเวอร์ใด ๆ ที่จะปิดการป้องกันนี้ได้

มีสองอย่างที่รันเป็นค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งสองอย่างปิดได้
และไม่มีข้อมูลเซสชันติดไปด้วย: การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันเทียบกับ
PyPI การติดตั้งแบบปกติยังค้นหา IP สาธารณะของคุณครั้งหนึ่งเพื่อใช้แสดงบรรทัดแบนเนอร์เมื่อเริ่มต้น
ปลายทางทุกจุด สิ่งที่มันส่งไป และวิธีปิดมันมีระบุไว้ใน
[docs/EGRESS.md](docs/EGRESS.md) ส่วนการติดตั้งแบบ self-hosted, repointed และ air-gapped
จะไม่มีการเรียกออกไปภายนอกโดยพลการเลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราส่งให้คุณ เรื่องนี้เคยเป็นเพียง
คำสัญญา แต่ตอนนี้เป็นสิ่งที่คุณตรวจสอบได้แล้ว ทุกบรรทัดที่แตะคีย์ของคุณ
อยู่ในไฟล์ที่อ่านได้เพียงไฟล์เดียว [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งถูกแพ็กไว้ในวีล (wheel) และส่งมาแบบคำต่อคำ พร้อมปักหมุดด้วยแฮช Subresource
Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่วิธีนี้พิสูจน์ไม่ได้: เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้ ดังนั้นเราก็อาจ
ให้บริการหน้าเว็บที่แตกต่างออกไปได้เช่นกัน แฮช Integrity ปกป้องคุณจาก CDN
ที่ถูกโจมตี ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้รับคือการแทนที่ใด ๆ
จะต้องทำโดยเจตนา มองเห็นได้ในซอร์สของหน้าเว็บ และแตกต่างจากอาร์ติแฟกต์บน PyPI
ที่ใครก็ดึงมาดูได้ การโฮสต์เองหรือใช้แบบ local-only เท่านั้นจะตัดความจำเป็นในการพึ่งพานี้ออกไปโดยสิ้นเชิง

## ติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือใช้คำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องมี Python 3.8 ขึ้นไปบน macOS, Linux หรือ Windows และมี agent runtime อย่างน้อยหนึ่งตัวบน
เครื่องเดียวกัน คำแนะนำสำหรับ Docker: [docs/DOCKER.md](docs/DOCKER.md)

หรือให้เอเจนต์ติดตั้งให้คุณเลยก็ได้ สกิล [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
สอนให้ Claude Code, Codex, Cursor, Gemini CLI, Copilot หรือ OpenCode
ติดตั้ง ClawMetry, รายงานว่าเอเจนต์บนเครื่องกำลังทำอะไรและใช้จ่ายไปเท่าไร,
หยุดเซสชันใดเซสชันหนึ่งตามคำขอ, และพักการเรียก tool ที่มีความเสี่ยงไว้เพื่อรออนุมัติ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของ runtime](docs/compatibility.md) | adapter แต่ละตัวอ่านอะไร และวิธีเพิ่ม runtime ใหม่ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | window แยกตาม provider, compaction เทียบกับ overflow, ความครอบคลุมแยกตาม runtime |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของ instrumentation ที่วัดได้จริง พร้อมชุดทดสอบให้ทำซ้ำได้ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน, ตารางระดับแพลน, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | การกั้นก่อนรัน, การให้คะแนนความเสี่ยง, การอนุมัติผ่านโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก trace ไปที่ไหนก็ได้ รับ OTLP เข้ามาจากที่ไหนก็ได้ |
| [นำเอเจนต์ของคุณมาใช้เอง](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้จริง |
| [SDK tracking](docs/SDK_TRACKING.md) | การระบุต้นทุนสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [Chat channels](docs/CHANNELS.md) | ตัวปรับใช้แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบ sandboxed |
| [Docker](docs/DOCKER.md) | อิมเมจ, compose, การ mount volume |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน; การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การ ping แบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพตัวอย่างหน้าจอ

ตัวเลขทุกตัวด้านล่างนี้มาจากเครื่องจริงเครื่องหนึ่ง อ่านแบบ read-only โดยไม่มีการเตรียมข้อมูลไว้ล่วงหน้า

**มันบอกคุณเมื่อมีอะไรผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์ความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่สูงถึง 7 เท่าของค่าเฉลี่ยรายวัน
และต้นทุนที่พุ่งขึ้น 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุดมีสัญญาณการสิ้นเปลือง
ซึ่งแยกตามสาเหตุไว้ให้

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้เห็นว่าเงินไปอยู่ที่ไหน ในทุกช่วงเวลา**
$252.47 วันนี้, $513.15 สัปดาห์นี้, $1,312.92 เดือนนี้ พร้อมโทเค็นที่อยู่เบื้องหลัง
และสมาชิกรายเดือนของคุณครอบคลุมได้มากแค่ไหนแล้ว ด้านล่างนั้น ประมาณ $1,128/เดือน
ที่ระบุไว้ว่าสามารถประหยัดเพิ่มได้ และ $17,256/เดือน ที่ประหยัดไปแล้วจากการใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดให้เห็นว่าข้อความกลายเป็นคำตอบได้อย่างไร**
ไดอะแกรม flow สด ๆ: คุณ, ช่องทางที่ข้อความเข้ามา, เกตเวย์, โมเดล
ที่กำลังตอบอยู่ตอนนี้ และทุก tool ที่มันเอื้อมไปเรียกใช้ โหนดจะสว่างขึ้นเมื่องาน
เคลื่อนผ่านมัน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง อยู่ในตารางเดียว**
มันรันอะไร ต้นทุนในช่วง 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน เห็นครั้งล่าสุดเมื่อไร
ใครเป็นเจ้าของ และสมาชิกรายเดือนครอบคลุมบิลหรือไม่ ที่นี่มีเอเจนต์ 14 ตัว
3 เซสชันกำลังทำงานอยู่ อีก 13 ตัวว่างเงียบ

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของแต่ละเทิร์นไปอยู่ที่ไหน แยกตาม tool**
หนึ่งเทิร์นของเซสชันจริง: 11 tool ใน 11.2 นาที คิดเป็น $1.16 ทุกการเรียก Bash
และการเรียกโมเดลจะได้แถบของตัวเองในไทม์ไลน์ ทำให้คำสั่งที่รันไป
4.1 นาที กับอีกคำสั่งที่รันไปแค่ 226ms แยกแยะได้จากการดูเพียงครั้งเดียว

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้คะแนนผลงาน ไม่ใช่แค่การใช้จ่าย**
สัปดาห์นี้ได้เกรด A: 54 งานกลับมาเรียบร้อยไร้ปัญหา มี 2 งานที่ไม่ราบรื่นคิดเป็นต้นทุน $48.57
และงานที่มีกิจกรรมน้อยเกินไปจนประเมินไม่ได้จะถูกตัดออกจากการให้คะแนน
แทนที่จะนับเป็นชัยชนะ งานที่ไม่ราบรื่นแต่ละงานเชื่อมไปยัง trace ของมันได้

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงเหตุผลว่าทำไม context window ถึงเต็มขึ้นเรื่อย ๆ**
715K จาก window ขนาด 1M โทเค็นในเทิร์นล่าสุด จุดสูงสุดที่ 83.3% การ compaction
4 ครั้งที่เกิดขึ้นแบบเชิงรุกทั้งหมด ไม่ใช่เพราะ overflow พร้อมอัตราการใช้งาน
ของทุกเทิร์นที่อยู่เบื้องหลัง

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยที่คุณไม่ต้องตั้งค่าอะไรเลย**
ตัวตรวจจับที่มีมาในตัวจะเปิดทำงานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป, ฟีด telemetry
หยุดทำงาน, ต้นทุนพุ่งสูง, โทเค็นพุ่งสูง, ข้อผิดพลาดเพิ่มขึ้น, ข้อผิดพลาดพุ่งสูง, เพดานงบประมาณ,
ตรงกับลายเซ็นภัยคุกคาม, ผลการตรวจพบจาก security tool, สถานะความปลอดภัยเปลี่ยนแปลง
กฎของคุณเองก็เป็นตัวเลือกเสริมเพิ่มเติมได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การหยุดการเรียกที่มีความเสี่ยงเป็นตัวเลือกเสริม และปิดไว้เป็นค่าเริ่มต้น**
การลบแบบ recursive, force push, sudo, ข้อมูลลับ (secrets), การติดตั้งแพ็กเกจ และการเรียกออกไปภายนอก
แต่ละอย่างมีกฎที่คุณเปิดใช้งานได้ จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดูเฉยๆ
และไม่เปลี่ยนแปลงอะไรเลย เมื่อเปิดใช้งานแล้ว การเรียกที่ตรงกับกฎจะรออยู่ที่นี่
(หรือบนโทรศัพท์ของคุณ) เพื่อให้คุณอนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม แยกตาม runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## การยอมรับ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## ประวัติดาว (Star History)

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ไลเซนส์

MIT · สร้างโดย [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
