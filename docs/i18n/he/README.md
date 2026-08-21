<!-- i18n-src:dc34072b2955 -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **23 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 19 נוספות. לוח מחוונים אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו את זה ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. אפס הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס הגדרות: הוא מוצא את סביבות הריצה של הסוכנים שכבר מותקנות אצלכם, קורא אותן בקריאה בלבד, ולא משנה דבר באופן שבו הן פועלות.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 23 סביבות ריצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

כל סביבת ריצה מקבלת את אותו לוח המחוונים. הריצו כמה מהן במקביל, ומחליף התצוגה שבכותרת ישנה את ההיקף של כל לשונית לאחת מהן.

בניתם את הסוכן שלכם בעצמכם על גבי SDK? המיירט (interceptor) עוקב גם אחרי קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה מקבלים

- **מפגשים (Sessions) ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שידור חוזר (replay)
- **עלות וטוקנים**: לפי סביבת ריצה, מודל, מפגש ויום, עם דגלי חריגה
- **Flow**: תרשים חי של הודעות הזורמות דרך ערוצים, מודלים וכלים
- **Brain**: זרם אירועי החשיבה וקריאות הכלים בזמן אמת
- **זיכרון וכישורים**: הקבצים והכישורים שכל סביבת ריצה בפועל טענה
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא מחובר, מנותבות ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **אישורים**: השהו קריאות כלים מסוכנות *לפני* שהן רצות ואשרו מהטלפון שלכם ([איך](docs/APPROVALS.md))

## תמחור

| תוכנית | מה היא כוללת | מחיר |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, לוח מחוונים מלא, מקומי בלבד | $0 |
| **Starter** | כל סביבת ריצה נוספת מהרשימה למעלה, תצוגת צי, סנכרון ענן | $9 לצומת / חודש |
| **Pro** | Starter + ממשל: אישורים, מדיניות סיכון כלים, הערכות (evals), זיהוי חריגות, מייעל עלויות, ייצוא OTel | $19 לצומת / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים ב־
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון בהתקנה עצמית
פועלים ללא הענן (`clawmetry license`). החלוקה המדויקת בין חינמי לבתשלום נמצאת
ב־[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים במחשב שלכם

ClawMetry קורא קבצי מפגש ולוגים מקומיים. שום דבר לא עוזב את המחשב שלכם אלא אם כן
תריצו `clawmetry connect`. גם אז, התמונה (snapshot) מוצפנת מקצה לקצה
עם מפתח שלעולם לא עוזב את המחשב שלכם, ומפוענחת בדפדפן שלכם.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או בשורת פקודה אחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ במערכת macOS, Linux או Windows, ולפחות סביבת ריצה אחת של סוכן על
אותו מחשב. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

## תיעוד

| | |
|---|---|
| [תאימות סביבות ריצה](docs/compatibility.md) | מה כל מתאם קורא, וכיצד להוסיף סביבת ריצה |
| [הרשאות (Entitlements)](docs/ENTITLEMENTS.md) | חינמי מול בתשלום, מטריצת דרגות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | חסימה טרם ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא traces לכל מקום, קליטת OTLP מכל מקור |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלויות עבור סוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בארגז חול (sandboxed) |
| [Docker](docs/DOCKER.md) | תמונה, compose, הצמדות נפח (volume mounts) |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה האנונימיים ופתיחת שולחן העבודה, וכיצד לכבות אותם |

## צילומי מסך

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: טוקנים, מפגשים, בריאות | **Brain**: זרם אירועי הסוכן החי |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **עלות**: לפי מודל ומפגש | **אישורים**: חסימת קריאות כלים מסוכנות |

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
