<!-- i18n-src:c111f32e69a5 -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **26 זמני ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 22 נוספים. דאשבורד אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו את זה ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד ←](docs/i18n/)

פקודה אחת. אפס הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס הגדרות: הוא מוצא את זמני הריצה של הסוכנים
שכבר יש לכם, קורא אותם בקריאה בלבד, ולא משנה דבר באופן שבו הם פועלים.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 26 זמני ריצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל זמן ריצה מקבל את אותו הדאשבורד. הריצו כמה מהם בו זמנית והמתג בכותרת
יתאים מחדש כל לשונית לאחד מהם.

בניתם סוכן משלכם על גבי SDK במקום? המיירט עוקב גם אחרי קריאות ה-LLM שלו.
ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה תקבלו

- **הפעלות ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שחזור
- **עלות וטוקנים**: לפי זמן ריצה, מודל, הפעלה ויום, עם סימוני חריגה
- **Flow**: תרשים חי של הודעות שזורמות דרך ערוצים, מודלים וכלים
- **Brain**: זרם אירועי ההיגיון וקריאות הכלים בזמן שהם קורים
- **זיכרון וכישורים**: הקבצים והכישורים שכל זמן ריצה בפועל טען
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא זמין, מנותב ל-Slack, Discord, PagerDuty, Telegram, Email
- **אישורים**: השהו קריאות כלים מסוכנות *לפני* שהן רצות ואשרו מהטלפון שלכם ([איך](docs/APPROVALS.md))

## תמחור

| תוכנית | מה היא כוללת | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, דאשבורד מלא, מקומי בלבד | $0 |
| **Starter** | כל זמן ריצה אחר שלמעלה, תצוגת צי, סנכרון ענן | $9 לצומת / חודש |
| **Pro** | Starter + ממשל: אישורים, מדיניות סיכון כלים, הערכות, זיהוי חריגות, אופטימיזציית עלויות, ייצוא OTel | $19 לצומת / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים בכתובת
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון בהתקנה עצמית
עובדים ללא הענן (`clawmetry license`). החלוקה המדויקת בין חינם לתשלום נמצאת
ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים במחשב שלכם

ClawMetry קורא קובצי הפעלה ולוגים מקומיים. שום דבר לא יוצא מהמכשיר שלכם אלא אם כן
תריצו `clawmetry connect`. גם אז, התמונה המצבית מוצפנת מקצה לקצה
עם מפתח שלעולם לא יוצא מהמכשיר שלכם, ומפוענחת בדפדפן שלכם.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או השורה האחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ ב-macOS, Linux או Windows, ולפחות זמן ריצה אחד של סוכן על
אותו המחשב. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

## תיעוד

| | |
|---|---|
| [תאימות זמני ריצה](docs/compatibility.md) | מה כל מתאם קורא, ואיך להוסיף זמן ריצה |
| [הרשאות](docs/ENTITLEMENTS.md) | חינם מול תשלום, טבלת דרגות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | שערור לפני ביצוע, דירוג סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא traces לכל מקום, קליטת OTLP מכל מקור |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלויות עבור סוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בסביבת ארגז חול |
| [Docker](docs/DOCKER.md) | תמונה, compose, הרכבות נפח |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | הפינגים האנונימיים של התקנה ופתיחת שולחן העבודה, ואיך לכבות אותם |

## צילומי מסך

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **סקירה כללית**: טוקנים, הפעלות, בריאות | **Brain**: זרם אירועי הסוכן החי |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **עלות**: לפי מודל והפעלה | **אישורים**: שערור קריאות כלים מסוכנות |

עוד, לפי זמן ריצה: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## היסטוריית כוכבים

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## רישיון

MIT · נבנה על ידי [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
