<!-- i18n-src:6795052055e2 -->
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

**ดูความคิดของเอเจนต์ของคุณแบบเรียลไทม์** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **26 รันไทม์เอเจนต์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 22 รายการ แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่นได้ที่:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่าใดๆ ตรวจจับทุกอย่างโดยอัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่า: ระบบจะค้นหารันไทม์เอเจนต์
ที่คุณมีอยู่แล้ว อ่านแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 26 รันไทม์เอเจนต์

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**บนแผนแบบชำระเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

ทุกรันไทม์ได้รับแดชบอร์ดแบบเดียวกัน รันได้หลายตัวพร้อมกัน และตัวสลับที่ส่วนหัว
จะปรับขอบเขตของทุกแท็บให้ตรงกับรันไทม์ที่เลือก

สร้างเอเจนต์ของคุณเองด้วย SDK แทนหรือเปล่า? ตัวดักจับ (interceptor) ก็ติดตามการเรียก LLM
ของมันได้เช่นกัน ดูที่ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและบทสนทนา (transcripts)**: สิ่งที่เอเจนต์แต่ละตัวทำ ทีละรอบ พร้อมการเล่นซ้ำ (replay)
- **ค่าใช้จ่ายและโทเคน**: แยกตามรันไทม์ โมเดล เซสชัน และวัน พร้อมการแจ้งเตือนความผิดปกติ
- **Flow**: ไดอะแกรมสดของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบเรียลไทม์
- **หน่วยความจำและทักษะ**: ไฟล์และทักษะที่แต่ละรันไทม์โหลดขึ้นมาใช้จริง
- **สุขภาพระบบและล็อก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด ขีดจำกัดอัตรา สตรีมล็อกสด
- **การแจ้งเตือน**: เพดานงบประมาณ การพุ่งขึ้นของข้อผิดพลาด เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่จะทำงาน และอนุมัติจากโทรศัพท์ของคุณได้ ([วิธีการ](docs/APPROVALS.md))

## ราคา

| แผน | ครอบคลุมอะไรบ้าง | ราคา |
|---|---|---|
| **ฟรี** | OpenClaw + NVIDIA NemoClaw + Goose แดชบอร์ดเต็มรูปแบบ เฉพาะภายในเครื่อง | $0 |
| **Starter** | รันไทม์อื่นๆ ทั้งหมดข้างต้น มุมมองกองเอเจนต์ (fleet) การซิงค์กับคลาวด์ | $9 ต่อโหนด/เดือน |
| **Pro** | Starter รวมกับการกำกับดูแล (governance): การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมิน การตรวจจับความผิดปกติ ตัวปรับค่าใช้จ่ายให้เหมาะสม การส่งออก OTel | $19 ต่อโหนด/เดือน |

แผนรายปี องค์กร (Enterprise) และราคาปัจจุบันดูได้ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ไลเซนส์แบบโฮสต์เองใช้งานได้โดยไม่ต้องพึ่งคลาวด์
(`clawmetry license`) รายละเอียดการแบ่งฟรี/เสียเงินที่แน่นอนอยู่ใน
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่บนเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์เซสชันและล็อกภายในเครื่อง ไม่มีข้อมูลใดออกจากเครื่องของคุณ เว้นแต่
คุณจะรัน `clawmetry connect` และถึงตอนนั้น สแนปช็อตก็ยังถูกเข้ารหัสแบบ end-to-end
ด้วยกุญแจที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัสในเบราว์เซอร์ของคุณเอง

## การติดตั้ง

```bash
pip install clawmetry     # จากนั้น: clawmetry
```

หรือใช้คำสั่งเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8+ บน macOS, Linux หรือ Windows และต้องมีรันไทม์เอเจนต์อย่างน้อยหนึ่งตัวบน
เครื่องเดียวกัน คำแนะนำสำหรับ Docker: [docs/DOCKER.md](docs/DOCKER.md)

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | สิ่งที่แต่ละอแดปเตอร์อ่าน และวิธีเพิ่มรันไทม์ |
| [สิทธิ์การใช้งาน](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับแผน CLI สำหรับไลเซนส์ |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การกำหนดสิทธิ์ก่อนการทำงาน การให้คะแนนความเสี่ยง การอนุมัติจากโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก traces ไปที่ไหนก็ได้ นำเข้า OTLP จากที่ไหนก็ได้ |
| [การติดตามด้วย SDK](docs/SDK_TRACKING.md) | การระบุที่มาของค่าใช้จ่ายสำหรับเอเจนต์ที่คุณสร้างเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | อแดปเตอร์แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมานต์วอลุ่ม |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน การรันจากซอร์สโค้ด |
| [Telemetry](docs/TELEMETRY.md) | การแจ้งเตือนแบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิดมัน |

## ภาพหน้าจอ

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: โทเคน เซสชัน สุขภาพระบบ | **Brain**: สตรีมเหตุการณ์เอเจนต์แบบสด |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: แยกตามโมเดลและเซสชัน | **Approvals**: กั้นการเรียกใช้เครื่องมือที่มีความเสี่ยง |

เพิ่มเติม แยกตามรันไทม์: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

## ประวัติดาว (Star History)

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
