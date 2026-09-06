<!-- i18n-src:88be2deff5d5 -->
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

**ดูความคิดของเอเจนต์คุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **30 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 26 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษานี้ได้ที่:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าใด ๆ ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าอะไรเลย: มันจะค้นหา agent runtime ที่คุณมีอยู่แล้ว
อ่านข้อมูลแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ใช้งานได้กับ 30 agent runtime

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ในแผนแบบเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุก runtime จะได้แดชบอร์ดเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัวจะปรับทุกแท็บ
ให้อยู่ในขอบเขตของ runtime ที่เลือก

สร้างเอเจนต์ของคุณเองบน SDK แทนหรือเปล่า? ตัว interceptor ก็ติดตามการเรียก LLM ของมันได้เช่นกัน
ดูที่ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: สิ่งที่แต่ละเอเจนต์ทำ ทีละเทิร์น พร้อมการเล่นซ้ำ
- **ค่าใช้จ่ายและโทเค็น**: แยกตาม runtime, โมเดล, เซสชัน และวัน พร้อมธงแจ้งความผิดปกติ
- **โฟลว์**: แผนภาพแบบเรียลไทม์ของข้อความที่เคลื่อนผ่านช่องทาง, โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบเรียลไทม์
- **Context blowout**: การใช้งานหน้าต่างบริบทที่วัดตามผู้ให้บริการแต่ละราย, การบีบอัด (compaction) เทียบกับการล้นแบบบังคับ พร้อมแผนที่ต่อ runtime ว่าเรา *มองไม่เห็น* อะไรบ้าง ([วิธีการ](docs/CONTEXT_BLOWOUT.md))
- **หน่วยความจำและทักษะ**: ไฟล์และทักษะที่แต่ละ runtime โหลดใช้งานจริง
- **สุขภาพระบบและล็อก**: ดิสก์, หน่วยความจำ, อัตราข้อผิดพลาด, ขีดจำกัดอัตรา, สตรีมล็อกแบบสด
- **การแจ้งเตือน**: เพดานงบประมาณ, ข้อผิดพลาดพุ่งสูง, เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะทำงาน และอนุมัติได้จากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## Context blowout และต้นทุนของการเฝ้าสังเกต

มีสองคำถามที่ควรตอบให้ได้ก่อนที่คุณจะเชื่อถือเครื่องมือเปรียบเทียบเอเจนต์ใด ๆ

**มันจัดการกับปัญหาหน้าต่างบริบทล้น (context-window blowout) ข้าม runtime ต่าง ๆ อย่างไร?**

เปอร์เซ็นต์การใช้งานจะซื่อสัตย์ได้ก็ต่อเมื่อตัวหารของมันซื่อสัตย์ ClawMetry
กำหนดขนาดหน้าต่างตามผู้ให้บริการแต่ละรายจาก[ตารางที่คุณอ่านและ
ส่ง PR ได้](clawmetry/context_windows.py)
ครอบคลุม Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama และ GLM มันไม่ได้วัดทั้ง 30 runtime
ด้วยไม้บรรทัดของผู้ให้บริการรายเดียว นั่นสำคัญมาก: เทิร์นของ GPT-5 ขนาด 300K โทเค็นที่ถูกวัดเทียบกับ
200K ของ Anthropic จะอ่านได้ว่า ">100% ล้นแล้ว" ทั้งที่จริง ๆ อยู่ที่แค่ 75% ของ
400K ของ GPT-5 ไม้บรรทัดเดียวกันนี้ก็ซ่อนเทิร์นของ DeepSeek ขนาด 130K โทเค็นที่ล้นจริง ๆ
ให้ดูเหมือนสบาย ๆ ที่ 65%

หน้าต่างทุกอันมาพร้อมแหล่งที่มา: `model_table`, `explicit_marker`,
`observed_floor` หรือค่า `default` ที่ตรงไปตรงมาเมื่อเราไม่รู้จักโมเดลนั้น มาตรวัดที่สร้างจาก
การเดาจะไม่ถูกแสดงด้วยความน่าเชื่อถือเดียวกับมาตรวัดที่สร้างจาก
การค้นหาข้อมูลจริง

ClawMetry มองเห็นเหตุการณ์การบีบอัด (compaction) ได้เฉพาะบาง runtime เท่านั้น ดังนั้น
`GET /api/context-coverage` จะรายงานสำหรับแต่ละ runtime ว่า **ค่า 0 หมายถึง
"รันได้ราบรื่น" หรือ "เรามองไม่เห็น"** ค่า `0` ที่จริง ๆ แล้วหมายถึงมองไม่เห็นจะระบุไว้เช่นนั้น
[รายละเอียดทั้งหมด](docs/CONTEXT_BLOWOUT.md)

**การติดตั้งเครื่องมือวัดนี้มีต้นทุนเท่าไร?**

| เส้นทาง | เพิ่มเข้าไปในเอเจนต์ของคุณ | ค่าเริ่มต้น? |
|---|---|---|
| การไล่อ่านไฟล์เซสชัน (ทั้ง 30 runtime) | **0** เป็นโพรเซสแยกต่างหาก ไม่มีโค้ด ClawMetry อยู่ในเอเจนต์ของคุณ | เปิด |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง หรือ 0.009% ของการเรียกที่ใช้เวลา 5 วินาที | ปิด |
| Pre-tool hook gate (แคชอุ่นแล้ว) | **+44 มิลลิวินาที** ต่อการเรียกเครื่องมือที่ถูกเฝ้าดูหนึ่งครั้ง เหนือพื้นฐานของตัวแปลภาษาที่ 36 มิลลิวินาที | ปิด |
| Enforcement proxy | **+9.7 มิลลิวินาที** ต่อการเรียก LLM หนึ่งครั้ง | ปิด |

ต้นทุนของโฮสต์ daemon: การรับข้อมูลเข้า **2,762 เหตุการณ์/วินาที** **710 ไบต์/เหตุการณ์**
บนดิสก์ (67.7 MB ต่อ 100,000 เหตุการณ์) และ **ประมาณ 12% ของหนึ่งคอร์** อย่างต่อเนื่อง
บนการติดตั้งที่มีงานหนัก ตัวเลขสุดท้ายนั้นเกินงบประมาณ 5-10% ที่เราตั้งไว้เอง ดังนั้นมันจึง
ถูกเผยแพร่ในฐานะบั๊กที่ต้องไล่แก้ ไม่ใช่ถูกตัดออกจากหน้านี้

วัดผลบน Apple M2 Pro ด้วย `benchmarks/overhead.py` ชุดทดสอบนี้รันแต่ละเงื่อนไข
ในโพรเซสแยกกัน สลับลำดับของมัน และ **ปฏิเสธที่จะพิมพ์ตัวเลขออกมาเมื่อรอบต่าง ๆ
ไม่เห็นตรงกันในเรื่องเครื่องหมาย (บวก/ลบ)** รันมันบนเครื่องของคุณเองได้ภายในหนึ่งนาที:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ทุกเส้นทางถูกวัดผล รวมถึง hook gate และ enforcement proxy
และชุดทดสอบรันบน Linux, macOS และ Windows ใน CI ผลลัพธ์สองอย่างที่ควรรู้:
proxy มีต้นทุนสูงกว่าบน Windows ประมาณเจ็ดเท่าเมื่อเทียบกับ Linux และ
daemon ในปัจจุบันใช้งานอยู่ที่ประมาณ 12% ของหนึ่งคอร์อย่างต่อเนื่อง ซึ่งเกินงบประมาณ 5-10%
ของเราเอง JSON ดิบ, วิธีการ และสิ่งที่ยังไม่ได้วัด อยู่ใน
[docs/OVERHEAD.md](docs/OVERHEAD.md)

## ราคา

| แผน | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, แดชบอร์ดเต็มรูปแบบ, เฉพาะภายในเครื่อง | $0 |
| **Starter** | ทุก runtime อื่นที่กล่าวมาข้างต้น, มุมมองกองเอเจนต์ (fleet), การซิงค์กับคลาวด์ | $9 ต่อโหนด/เดือน |
| **Pro** | Starter บวกกับการควบคุมและการประเมิน: การอนุมัติ, นโยบายความเสี่ยงของเครื่องมือ, evals, การตรวจจับความผิดปกติ, cost optimizer, การส่งออก OTel, บันทึกตรวจสอบที่ป้องกันการปลอมแปลง | $19 ต่อโหนด/เดือน |

แผนรายปี, Enterprise และตัวเลขล่าสุดอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ใบอนุญาตแบบโฮสต์เอง (self-hosted)
ใช้งานได้โดยไม่ต้องพึ่งคลาวด์ (`clawmetry license`) รายละเอียดที่แน่นอนของการแบ่งฟรี/เสียเงิน
อยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเอง

ClawMetry อ่านไฟล์เซสชันและล็อกในเครื่อง **ไม่มีข้อมูลเซสชันใดออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect`** ไม่มีพรอมต์, คำตอบ, อาร์กิวเมนต์ของเครื่องมือ, เนื้อหาไฟล์
หรือบรรทัดล็อกใด ๆ ถูกส่งออกไป เมื่อคุณเชื่อมต่อ สแนปช็อตจะถูกเข้ารหัสแบบ end-to-end
ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถอดรหัสในเบราว์เซอร์ของคุณ ถ้าโหนดใดไม่มีคีย์
การอัปโหลดจะถูกข้ามไปแทนที่จะส่งแบบไม่เข้ารหัส และไม่มีการตอบกลับจากเซิร์ฟเวอร์ใดที่จะปิดการทำงานนี้ได้

มีสองสิ่งที่ทำงานโดยค่าเริ่มต้นก่อนที่คุณจะเชื่อมต่อ ทั้งคู่สามารถปิดได้และไม่มีสิ่งใด
พาข้อมูลเซสชันไปด้วย: การ ping การติดตั้งแบบไม่ระบุตัวตน และการตรวจสอบเวอร์ชันกับ
PyPI การติดตั้งแบบค่าเริ่มต้นยังค้นหา IP สาธารณะของคุณครั้งหนึ่งสำหรับบรรทัดแบนเนอร์ตอนเริ่มต้น
ปลายทางทุกแห่ง สิ่งที่มันพกพาไป และวิธีปิดมัน ถูกระบุไว้ทั้งหมดใน
[docs/EGRESS.md](docs/EGRESS.md) การติดตั้งแบบโฮสต์เอง, ชี้ปลายทางใหม่ และแบบตัดขาดจากอินเทอร์เน็ต (air-gapped)
จะไม่มีการเรียกออกไปภายนอกตามดุลยพินิจเลย

การถอดรหัสเกิดขึ้นในเบราว์เซอร์ของคุณ ด้วยโค้ดที่เราให้บริการแก่คุณ สิ่งนี้เคยเป็นเพียงคำสัญญา
ตอนนี้มันเป็นสิ่งที่คุณตรวจสอบได้ ทุกบรรทัดที่แตะต้องคีย์ของคุณอยู่ในไฟล์เดียวที่อ่านได้
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
ซึ่งถูกจัดส่งภายใน wheel และให้บริการแบบคำต่อคำ ปักหมุดด้วยแฮช Subresource
Integrity เพื่อยืนยันว่าเบราว์เซอร์รันสิ่งที่เราเผยแพร่จริง:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

สิ่งที่วิธีนี้พิสูจน์ไม่ได้: เราเป็นผู้ให้บริการหน้าเว็บที่โหลดไฟล์นี้ ดังนั้นเราอาจให้บริการ
หน้าเว็บอื่นแทนได้ แฮชความสมบูรณ์ปกป้องคุณจาก CDN ที่ถูกบุกรุก
ไม่ใช่จากผู้ให้บริการเอง สิ่งที่คุณได้รับคือการแทนที่ใด ๆ จะต้อง
เป็นการกระทำโดยเจตนา มองเห็นได้ในซอร์สโค้ดของหน้าเว็บ และแตกต่างจากอาร์ทิแฟกต์บน PyPI
ที่ใครก็สามารถดึงมาตรวจสอบได้ การโฮสต์เองหรืออยู่ในเครื่องเท่านั้นจะขจัด
การพึ่งพานี้ออกไปทั้งหมด

## ติดตั้ง

```bash
pip install clawmetry     # แล้วจึงรัน: clawmetry
```

หรือใช้คำสั่งบรรทัดเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องใช้ Python 3.8 ขึ้นไปบน macOS, Linux หรือ Windows และมี agent runtime อย่างน้อยหนึ่งตัวบน
เครื่องเดียวกัน คำแนะนำสำหรับ Docker: [docs/DOCKER.md](docs/DOCKER.md)

หรือให้เอเจนต์ตั้งค่าให้คุณ ทักษะ [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
สอน Claude Code, Codex, Cursor, Gemini CLI, Copilot หรือ OpenCode ให้
ติดตั้ง ClawMetry, รายงานว่าเอเจนต์บนเครื่องกำลังทำอะไรและใช้จ่ายเท่าไร,
หยุดเซสชันหนึ่งตามคำขอ และกักการเรียกใช้เครื่องมือที่มีความเสี่ยงไว้เพื่อรออนุมัติ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของ Runtime](docs/compatibility.md) | สิ่งที่แต่ละ adapter อ่าน และวิธีเพิ่ม runtime ใหม่ |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | หน้าต่างตามผู้ให้บริการแต่ละราย, การบีบอัดเทียบกับการล้น, ความครอบคลุมต่อ runtime |
| [Overhead](docs/OVERHEAD.md) | ต้นทุนของเครื่องมือวัด วัดผลจริง พร้อมชุดทดสอบเพื่อทำซ้ำ |
| [Entitlements](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน, ตารางระดับแผน, license CLI |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การเฝ้าตรวจก่อนการทำงาน, การให้คะแนนความเสี่ยง, การอนุมัติผ่านโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก trace ไปที่ไหนก็ได้ รับ OTLP จากอะไรก็ได้ |
| [นำเอเจนต์ของคุณเองมาใช้](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain แบบครบวงจร พร้อมตัวอย่างที่รันได้จริง |
| [SDK tracking](docs/SDK_TRACKING.md) | การระบุที่มาของต้นทุนสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงในโฟลว์ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ, compose, การ mount volume |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน; การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การ ping แบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดแอปเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

ตัวเลขทุกตัวด้านล่างมาจากเครื่องจริงหนึ่งเครื่อง อ่านอย่างเดียว โดยไม่มีการปลูกฝังข้อมูลใด ๆ

**มันบอกคุณเมื่อมีบางอย่างผิดปกติ ไม่ใช่แค่บอกว่าเกิดอะไรขึ้น**
แบนเนอร์แจ้งความผิดปกติสองอันที่ด้านบน: การใช้จ่ายที่วิ่งอยู่ที่ 7 เท่าของค่าเฉลี่ยรายวัน และ
ค่าใช้จ่ายพุ่งสูง 4.2 เท่า ด้านล่างนั้น 324 จาก 667 เซสชันล่าสุดมีสัญญาณ
ของการสิ้นเปลือง แจกแจงตามสาเหตุ

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**มันแสดงให้คุณเห็นว่าเงินไปไหน ในทุกช่วงเวลา**
$252.47 วันนี้, $513.15 สัปดาห์นี้, $1,312.92 เดือนนี้ พร้อมโทเค็นที่อยู่เบื้องหลังตัวเลขนั้น
และการสมัครสมาชิกของคุณครอบคลุมไปแล้วเท่าไร ด้านล่างนั้น มีประมาณ $1,128/เดือน ที่แจกแจงว่า
สามารถกู้คืนได้ และ $17,256/เดือน ที่ประหยัดไปแล้วจากการใช้แคชซ้ำ

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**มันวาดให้เห็นว่าข้อความหนึ่งกลายเป็นคำตอบได้อย่างไร**
แผนภาพโฟลว์แบบสด: คุณ, ช่องทางที่มันมาถึง, เกตเวย์, โมเดล
ที่กำลังตอบอยู่ตอนนี้ และเครื่องมือทุกตัวที่มันเอื้อมไปใช้ โหนดต่าง ๆ จะสว่างขึ้นเมื่องาน
เคลื่อนผ่านพวกมัน

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**เอเจนต์ทุกตัวบนเครื่อง ในตารางเดียว**
สิ่งที่มันรัน, ค่าใช้จ่ายใน 24 ชั่วโมงที่ผ่านมาและตลอดอายุการใช้งาน, เห็นครั้งล่าสุดเมื่อไร,
ใครเป็นเจ้าของ และมีการสมัครสมาชิกครอบคลุมค่าใช้จ่ายหรือไม่ มี 14 เอเจนต์ที่นี่ 3 เซสชัน
กำลังทำงานอยู่ 13 เซสชันเงียบ

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**มันแสดงให้เห็นว่าเวลาและเงินของแต่ละเทิร์นไปไหน แยกตามเครื่องมือ**
หนึ่งเทิร์นของเซสชันจริง: 11 เครื่องมือใน 11.2 นาที ด้วยราคา $1.16 การเรียก Bash
และการเรียกโมเดลทุกครั้งได้แถบเวลาของตัวเอง เพื่อให้คำสั่งที่รันไป 4.1 นาที
กับคำสั่งที่รันไป 226 มิลลิวินาที แยกออกจากกันได้ในพริบตา

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**มันให้คะแนนงาน ไม่ใช่แค่การใช้จ่าย**
เกรด A ในสัปดาห์นี้: 54 งานเสร็จเรียบร้อย 2 งานที่ขรุขระคิดเป็นเงิน $48.57 และ
งานที่มีกิจกรรมน้อยเกินกว่าจะตัดสินได้ก็ถูกตัดออกจากการให้เกรด แทนที่จะถูกนับ
เป็นชัยชนะ แต่ละงานที่ขรุขระเชื่อมโยงไปยัง trace ของมัน

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**มันแสดงว่าทำไมหน้าต่างบริบทถึงเต็มขึ้นเรื่อย ๆ**
715K จากหน้าต่าง 1M โทเค็นในเทิร์นล่าสุด จุดสูงสุด 83.3% การบีบอัด 4 ครั้ง
ที่ล้วนเกิดขึ้นแบบเชิงรุกแทนที่จะเป็นเพราะการล้น พร้อมการใช้งานของ
ทุกเทิร์นที่อยู่เบื้องหลังมัน

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**การตรวจจับทำงานได้โดยที่คุณไม่ต้องตั้งค่าอะไร**
ตัวตรวจจับในตัวเปิดใช้งานตั้งแต่ติดตั้ง: เอเจนต์เงียบไป, ฟีด telemetry
หยุดทำงาน, ค่าใช้จ่ายพุ่งสูง, โทเค็นพุ่งกระชาก, ข้อผิดพลาดเพิ่มขึ้น, ข้อผิดพลาดพุ่งสูง, เพดานงบประมาณ,
ตรงกับลายเซ็นภัยคุกคาม, ผลการตรวจพบจากเครื่องมือความปลอดภัย, ท่าทีความปลอดภัย
เปลี่ยนแปลง กฎของคุณเองเป็นตัวเลือกเสริมที่เพิ่มเข้าไปได้

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**การกักการเรียกที่มีความเสี่ยงเป็นทางเลือก และปิดอยู่โดยค่าเริ่มต้น**
การลบแบบเรียกซ้ำ, force push, sudo, ข้อมูลลับ, การติดตั้งแพ็กเกจ และการเรียกออกภายนอก
แต่ละอย่างมีกฎที่คุณสามารถเปิดใช้งานได้ จนกว่าคุณจะเปิด ClawMetry จะเฝ้าดู
และไม่เปลี่ยนแปลงอะไรเลย เมื่อเปิดใช้งานอันหนึ่งแล้ว การเรียกที่ตรงเงื่อนไขจะรอ
อยู่ที่นี่ (หรือบนโทรศัพท์ของคุณ) เพื่อรับการอนุมัติหรือปฏิเสธ

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

เพิ่มเติม แยกตาม runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## ประวัติดวงดาว

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
