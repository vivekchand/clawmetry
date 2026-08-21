<!-- i18n-src:dc34072b2955 -->
> ไทย translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ดูสิ่งที่เอเจนต์ของคุณกำลังคิด** ระบบสังเกตการณ์แบบเรียลไทม์สำหรับ **23 รันไทม์ของเอเจนต์ AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex และอีก 19 รายการ แดชบอร์ดเดียวสำหรับกองเอเจนต์ทั้งหมดของคุณ

> 🌐 **อ่านภาษาอื่น:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [เพิ่มเติม →](docs/i18n/)

คำสั่งเดียว ไม่ต้องตั้งค่า ตรวจจับทุกอย่างให้อัตโนมัติ

```bash
pip install clawmetry && clawmetry
```

เปิดที่ **http://localhost:8900** ไม่ต้องตั้งค่าใด ๆ: มันจะค้นหารันไทม์ของเอเจนต์
ที่คุณมีอยู่แล้ว อ่านข้อมูลแบบอ่านอย่างเดียว และไม่เปลี่ยนแปลงวิธีการทำงานของมันเลย

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ใช้งานได้กับ 23 รันไทม์ของเอเจนต์

**ฟรีในแอปโอเพนซอร์ส:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**ในแผนแบบชำระเงิน:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

ทุกรันไทม์ได้แดชบอร์ดเดียวกัน รันได้พร้อมกันหลายตัว และตัวสลับที่ส่วนหัว
จะปรับขอบเขตทุกแท็บให้ตรงกับรันไทม์ที่เลือก

สร้างเอเจนต์ของคุณเองด้วย SDK แทนหรือเปล่า? ตัวดักจับ (interceptor) ก็ติดตาม
การเรียก LLM ของมันได้เช่นกัน ดูที่ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)

## สิ่งที่คุณจะได้รับ

- **เซสชันและบทถอดความ**: สิ่งที่แต่ละเอเจนต์ทำ ทีละขั้นตอน พร้อมการเล่นซ้ำ
- **ต้นทุนและโทเคน**: แยกตามรันไทม์ โมเดล เซสชัน และวัน พร้อมการตั้งค่าสถานะความผิดปกติ
- **Flow**: ไดอะแกรมสดของข้อความที่เคลื่อนผ่านช่องทาง โมเดล และเครื่องมือ
- **Brain**: สตรีมเหตุการณ์การให้เหตุผลและการเรียกใช้เครื่องมือแบบเรียลไทม์
- **หน่วยความจำและทักษะ**: ไฟล์และทักษะที่แต่ละรันไทม์โหลดขึ้นมาจริง
- **สถานะและบันทึก**: ดิสก์ หน่วยความจำ อัตราข้อผิดพลาด ขีดจำกัดอัตรา สตรีมบันทึกแบบสด
- **การแจ้งเตือน**: เพดานงบประมาณ การพุ่งขึ้นของข้อผิดพลาด เอเจนต์ออฟไลน์ ส่งไปยัง Slack, Discord, PagerDuty, Telegram, อีเมล
- **การอนุมัติ**: หยุดการเรียกใช้เครื่องมือที่มีความเสี่ยง *ก่อน* ที่จะรัน และอนุมัติจากโทรศัพท์ของคุณ ([วิธีการ](docs/APPROVALS.md))

## ราคา

| แผน | ครอบคลุมอะไร | ราคา |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw แดชบอร์ดเต็มรูปแบบ ใช้ในเครื่องเท่านั้น | $0 |
| **Starter** | รันไทม์อื่นทั้งหมดข้างต้น มุมมองกองเอเจนต์ การซิงค์คลาวด์ | $9 ต่อโหนด / เดือน |
| **Pro** | Starter + การกำกับดูแล: การอนุมัติ นโยบายความเสี่ยงของเครื่องมือ การประเมิน การตรวจจับความผิดปกติ ตัวเพิ่มประสิทธิภาพต้นทุน การส่งออก OTel | $19 ต่อโหนด / เดือน |

แผนรายปี Enterprise และตัวเลขปัจจุบันอยู่ที่
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** คีย์ใบอนุญาตแบบโฮสต์เอง
ทำงานได้โดยไม่ต้องใช้คลาวด์ (`clawmetry license`) การแบ่งฟรี/เสียเงินที่แน่นอน
อยู่ใน [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)

## ข้อมูลของคุณอยู่ในเครื่องของคุณเสมอ

ClawMetry อ่านไฟล์เซสชันและบันทึกในเครื่อง ไม่มีอะไรออกจากเครื่องของคุณ
เว้นแต่คุณจะรัน `clawmetry connect` แม้กระทั่งตอนนั้น สแนปช็อตก็ยังถูกเข้ารหัส
แบบ end-to-end ด้วยคีย์ที่ไม่เคยออกจากเครื่องของคุณ และถูกถอดรหัสในเบราว์เซอร์ของคุณ

## การติดตั้ง

```bash
pip install clawmetry     # จากนั้นรัน: clawmetry
```

หรือคำสั่งบรรทัดเดียว: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ต้องการ Python 3.8 ขึ้นไปบน macOS, Linux หรือ Windows และรันไทม์ของเอเจนต์
อย่างน้อยหนึ่งตัวบนเครื่องเดียวกัน คำแนะนำ Docker: [docs/DOCKER.md](docs/DOCKER.md)

## เอกสาร

| | |
|---|---|
| [ความเข้ากันได้ของรันไทม์](docs/compatibility.md) | สิ่งที่แต่ละตัวปรับใช้อ่าน และวิธีเพิ่มรันไทม์ใหม่ |
| [สิทธิ์การใช้งาน](docs/ENTITLEMENTS.md) | ฟรีเทียบกับเสียเงิน ตารางระดับ CLI ใบอนุญาต |
| [การอนุมัติและนโยบาย](docs/APPROVALS.md) | การควบคุมก่อนการทำงาน การให้คะแนนความเสี่ยง การอนุมัติทางโทรศัพท์ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ส่งออก trace ไปที่ไหนก็ได้ นำเข้า OTLP จากทุกที่ |
| [การติดตาม SDK](docs/SDK_TRACKING.md) | การระบุต้นทุนสำหรับเอเจนต์ที่คุณสร้างเอง |
| [ช่องทางแชท](docs/CHANNELS.md) | ตัวปรับใช้แชทที่แสดงใน Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | การตั้งค่า NVIDIA NemoClaw แบบแซนด์บ็อกซ์ |
| [Docker](docs/DOCKER.md) | อิมเมจ compose การเมานต์วอลุ่ม |
| [สถาปัตยกรรม](ARCHITECTURE.md) · [การพัฒนา](docs/DEVELOPMENT.md) | วิธีการทำงานภายใน การรันจากซอร์ส |
| [Telemetry](docs/TELEMETRY.md) | การ ping แบบไม่ระบุตัวตนตอนติดตั้งและตอนเปิดเดสก์ท็อป และวิธีปิด |

## ภาพหน้าจอ

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: โทเคน เซสชัน สถานะ | **Brain**: สตรีมเหตุการณ์ของเอเจนต์แบบสด |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
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

## ใบอนุญาต

MIT · สร้างโดย [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
