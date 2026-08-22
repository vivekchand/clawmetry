<!-- i18n-src:6795052055e2 -->
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

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **26 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 22 נוספות. לוח בקרה אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. בלי הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. בלי הגדרות: הוא מוצא את סביבות הריצה של הסוכנים שכבר יש לכם, קורא אותן בקריאה בלבד, ולא משנה דבר באופן הפעולה שלהן.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 26 סביבות ריצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

כל סביבת ריצה מקבלת את אותו לוח בקרה. הריצו כמה בו זמנית, ומחליף הכותרת יעדכן את היקף כל לשונית לאחת מהן.

בניתם את הסוכן שלכם בעצמכם על בסיס SDK במקום? המיירט עוקב גם אחרי קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה תקבלו

- **הפעלות ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שידור חוזר
- **עלות וטוקנים**: לפי סביבת ריצה, מודל, הפעלה ויום, עם דגלי חריגות
- **זרימה (Flow)**: תרשים חי של הודעות שנעות בין ערוצים, מודלים וכלים
- **מוח (Brain)**: זרם אירועי ההיגיון וקריאות הכלים בזמן אמת
- **זיכרון וכישורים**: הקבצים והכישורים שכל סביבת ריצה טענה בפועל
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא מקוון, מנותבות ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **אישורים**: השהו קריאות כלים מסוכנות *לפני* שהן רצות ואשרו מהטלפון שלכם ([איך](docs/APPROVALS.md))

## תמחור

| תוכנית | מה היא כוללת | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, לוח בקרה מלא, מקומי בלבד | $0 |
| **Starter** | כל סביבת ריצה אחרת שלמעלה, תצוגת צי, סנכרון ענן | $9 לצומת / חודש |
| **Pro** | Starter + ממשל: אישורים, מדיניות סיכון כלים, הערכות, זיהוי חריגות, ממטב עלויות, ייצוא OTel | $19 לצומת / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים בכתובת
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון לאירוח עצמי
עובדים ללא הענן (`clawmetry license`). החלוקה המדויקת בין חינם לתשלום נמצאת
ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים במחשב שלכם

ClawMetry קורא קבצי הפעלה ולוגים מקומיים. שום דבר לא יוצא מהמכשיר שלכם אלא אם
תריצו `clawmetry connect`. גם אז, התמונה המסונכרנת מוצפנת מקצה לקצה
עם מפתח שלעולם לא יוצא מהמכשיר שלכם, ומפוענחת בדפדפן שלכם.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או השורה האחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ ב-macOS, Linux או Windows, ולפחות סביבת ריצה אחת של סוכן על
אותו מחשב. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

## תיעוד

| | |
|---|---|
| [תאימות סביבות ריצה](docs/compatibility.md) | מה כל מתאם קורא, וכיצד להוסיף סביבת ריצה |
| [הרשאות (Entitlements)](docs/ENTITLEMENTS.md) | חינם מול בתשלום, מטריצת דרגות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | סינון לפני הרצה, דירוג סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא traces לכל מקום, קליטת OTLP מכל מקור |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלויות עבור סוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בארגז חול |
| [Docker](docs/DOCKER.md) | תמונה, compose, הצמדות נפח |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה והפתיחה השולחנית האנונימיים, וכיצד לכבות אותם |

## צילומי מסך

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **סקירה כללית**: טוקנים, הפעלות, בריאות | **Brain**: זרם אירועי הסוכן החי |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **עלות**: לפי מודל והפעלה | **אישורים**: סינון קריאות כלים מסוכנות |

עוד, לפי סביבת ריצה: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
