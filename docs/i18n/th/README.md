<!-- i18n-src:c111f32e69a5 -->
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

**ดูสิ่งที่เอเจนต์ของคุณกำลังคิด** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **26 เอเจนต์รันไทม์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 22 ตัว แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษานี้:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

หนึ่งคำสั่ง ไม่ต้องตั้งค่าใด ๆ ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่า: มันจะค้นหาเอเจนต์รันไทม์
ที่คุณมีอยู่แล้ว อ่านแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## ใช้งานได้กับ 26 เอเจนต์รันไทม์

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**บนแพลนที่ต้องเสียเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ทุกรันไทม์ได้รับแดชบอร์ดแบบเดียวกัน รันหลายตัวพร้อมกันได้ และตัวสลับที่ส่วนหัว
จะปรับขอบเขตทุกแท็บให้ตรงกับรันไทม์ที่เลือก

สร้างเอเจนต์ของคุณเองด้วย SDK แทนหรือเปล่า? ตัวสกัดกั้น (interceptor) ก็ติดตาม
การเรียก LLM ของมันได้เช่นกัน ดูที่ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและทรานสคริปต์**: สิ่งที่แต่ละเอเจนต์ทำ ทีละเทิร์น พร้อมการเล่นซ้ำ
- **ต้นทุนและโทเคน**: แยกตามรันไทม์ โมเดล เซสชัน และวัน พร้อมสัญญาณแจ้งเตือนความผิดปกติ
- **Flow**: แผนภาพแบบเรียลไทม์ของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบสด ๆ ตามเวลาจริง
- **หน่วยความจำและทักษะ**: ไฟล์และทักษะที่แต่ละรันไทม์โหลดขึ้นมาใช้จริง
- **สุขภาพระบบและบันทึก**: ดิสก์ หน่วยความจำ อัตราความผิดพลาด ขีดจำกัดอัตรา สตรีมบันทึกแบบสด
- **การแจ้งเตือน**: ขีดจำกัดงบประมาณ ความผิดพลาดพุ่งสูง เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, Email
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่มันจะทำงาน และอนุมัติได้จากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## ราคา

| แพลน | ครอบคลุมอะไร | ราคา |
|---|---|---|
| **ฟรี** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ ในเครื่องเท่านั้น | $0 |
| **Starter** | ทุกรันไทม์อื่น ๆ ข้างต้น มุมมองกองเอเจนต์ การซิงค์กับคลาวด์ | $9 ต่อโหนด / เดือน |
| **Pro** | Starter บวกการกำกับดูแล: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมินผล การตรวจจับความผิดปกติ ตัวปรับต้นทุนให้เหมาะสม การส่งออก OTel | $19 ต่อโหนด / เดือน |

แพลนรายปี Enterprise และตัวเลขราคาปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ไลเซนส์แบบโฮสต์เองใช้งานได้
โดยไม่ต้องพึ่งคลาวด์ (`clawmetry license`) รายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอนอยู่ใน
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเท่านั้น

ClawMetry อ่านไฟล์เซสชันและบันทึกในเครื่อง ไม่มีอะไรออกจากเครื่องของคุณเลย เว้นแต่
คุณจะรัน `clawmetry connect` แม้จะเป็นเช่นนั้น สแนปช็อตก็ถูกเข้ารหัสแบบ end-to-end
ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัสในเบราว์เซอร์ของคุณ

## การติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือใช้คำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องใช้ Python 3.8+ บน macOS, Linux หรือ Windows และต้องมีเอเจนต์รันไทม์อย่างน้อยหนึ่งตัวบน
เครื่องเดียวกัน คำแนะนำ Docker: [docs/DOCKER.md](docs/DOCKER.md)

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | แต่ละอะแดปเตอร์อ่านอะไรบ้าง และวิธีเพิ่มรันไทม์ |
| [สิทธิ์การใช้งาน](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับแพลน CLI ไลเซนส์ |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การควบคุมก่อนดำเนินการ การให้คะแนนความเสี่ยง การอนุมัติผ่านโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออกเทรซไปที่ไหนก็ได้ นำเข้า OTLP จากอะไรก็ได้ |
| [การติดตาม SDK](docs/SDK_TRACKING.md) | การระบุแหล่งที่มาของต้นทุนสำหรับเอเจนต์ที่คุณสร้างขึ้นเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อะแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมานต์วอลุม |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การปิงแบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: โทเคน เซสชัน สุขภาพระบบ | **Agents** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: แยกตามโมเดลและเซสชัน | **Approvals**: ควบคุมการเรียกใช้เครื่องมือที่มีความเสี่ยง |

เพิ่มเติม แยกตามรันไทม์: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

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
