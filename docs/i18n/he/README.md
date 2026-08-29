<!-- i18n-src:d21bea5161e0 -->
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

**ראו את הסוכן שלכם חושב.** נראות בזמן אמת עבור **30 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 26 נוספות. לוח בקרה אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד ←](docs/i18n/)

פקודה אחת. אפס תצורה. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס תצורה: הוא מוצא את סביבות הריצה של הסוכנים שכבר יש לכם, קורא אותן בקריאה בלבד, ולא משנה דבר באופן שבו הן פועלות.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## עובד עם 30 סביבות ריצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל סביבת ריצה מקבלת את אותו לוח בקרה. הריצו כמה בבת אחת ומחליף הכותרת יתאים מחדש כל לשונית לאחת מהן.

בניתם סוכן משלכם על גבי SDK במקום זאת? המיירט עוקב גם אחרי קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה תקבלו

- **סשנים ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שחזור
- **עלות וטוקנים**: לפי סביבת ריצה, מודל, סשן ויום, עם דגלי חריגות
- **זרימה (Flow)**: תרשים חי של הודעות הנעות בין ערוצים, מודלים וכלים
- **מוח (Brain)**: זרם אירועי ההיגיון וקריאות הכלים בזמן אמת
- **פיצוץ הקשר (Context blowout)**: ניצול חלון בגודל ספציפי לספק, דחיסה מול גלישה כפויה, ומפה לפי סביבת ריצה של מה שאנחנו *לא* יכולים לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים**: הקבצים והכישורים שכל סביבת ריצה בפועל טענה
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא מקוון, מנותב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **אישורים**: עוצרים קריאות כלים מסוכנות *לפני* שהן רצות ומאשרים מהטלפון שלכם ([איך](docs/APPROVALS.md))

## פיצוץ הקשר, ומה עולה המעקב

שתי שאלות ששווה לענות עליהן לפני שסומכים על כל כלי להשוואת סוכנים.

**איך זה מתמודד עם פיצוץ חלון ההקשר בין סביבות ריצה שונות?**

אחוז ניצול הוא הגון רק כמו המספר שבו הוא מחלק. ClawMetry מגדיר את גודל החלון לפי ספק מתוך [טבלה שאפשר לקרוא ולשלוח עבורה PR](clawmetry/context_windows.py), המכסה את Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ו-GLM. הוא לא מודד את כל 26 סביבות הריצה בסרגל של ספק אחד. זה משנה: תור GPT-5 בגודל 300K שנמדד מול 200K של Anthropic נקרא ">100%, פוצץ" בעוד שהוא בעצם ב-75% מתוך ה-400K של GPT-5. אותו סרגל מסתיר תור DeepSeek בגודל 130K שבאמת גלש כ-65% נוחים.

כל חלון מגיע עם המקור שלו: `model_table`, `explicit_marker`, `observed_floor`, או `default` כן ולא כשאנחנו לא מכירים את המודל. מד שנבנה על ניחוש לעולם לא מוצג באותה סמכות כמו מד שנבנה על חיפוש בטבלה.

ClawMetry יכול לראות אירועי דחיסה רק בחלק מסביבות הריצה. לכן `GET /api/context-coverage` מדווח, לפי סביבת ריצה, אם **אפס פירושו "רץ נקי" או "אנחנו עיוורים"**. `0` שבאמת פירושו עיוור אומר זאת בפירוש. [פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**מה עולה האינסטרומנטציה?**

| נתיב | נוסף לסוכן שלכם | ברירת מחדל? |
|---|---|---|
| מעקב אחר קובצי סשן (כל 30 סביבות הריצה) | **0**. תהליך נפרד, אין קוד ClawMetry בסוכן שלכם | פעיל |
| מיירט HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 מ"ש** לכל קריאת LLM, כלומר 0.009% מקריאה בת 5 שניות | כבוי |
| שער hook לפני-כלי (מטמון חם) | **+44 מ"ש** לכל קריאת כלי משוערת, מעל רצפת מפרש של 36 מ"ש | כבוי |
| פרוקסי אכיפה | **+9.7 מ"ש** לכל קריאת LLM | כבוי |

עלות מארח הדימון: **2,762 אירועים/שנייה** קליטה, **710 בייטים/אירוע** על הדיסק (67.7 מ"ב לכל 100 אלף אירועים), ו-**כ-12% מליבה אחת** באופן מתמשך בהתקנה עמוסה. המספר האחרון הזה חורג מהתקציב המוצהר שלנו של 5-10%, ולכן הוא מפורסם כבאג לרדוף אחריו ולא מוסתר מהדף.

נמדד על Apple M2 Pro באמצעות `benchmarks/overhead.py`. הרתמה מריצה כל תנאי בתהליך נפרד, מתחלפת בסדר שלהם, ו**מסרבת להדפיס מספר כאשר הסבבים לא מסכימים על הסימן שלו**. הריצו זאת על המכונה שלכם תוך דקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook ופרוקסי האכיפה, והרתמה רצה על Linux, macOS ו-Windows ב-CI. שתי תוצאות ששווה לדעת: הפרוקסי עולה בערך פי שבעה יותר ב-Windows מאשר ב-Linux, והדימון כרגע שומר על כ-12% מליבה אחת, מעל תקציב 5-10% שלנו. ה-JSON הגולמי, השיטה, ומה שעדיין לא נמדד נמצאים ב-[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא מכסה | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, לוח בקרה מלא, מקומי בלבד | 0$ |
| **Starter** | כל סביבת ריצה אחרת שלמעלה, תצוגת צי, סנכרון ענן | 9$ לצומת / חודש |
| **Pro** | Starter + בקרה והערכה: אישורים, מדיניות סיכון כלים, הערכות (evals), זיהוי חריגות, אופטימיזציית עלויות, ייצוא OTel, יומן ביקורת עמיד בפני שיבוש | 19$ לצומת / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון בהתקנה עצמית עובדים ללא הענן (`clawmetry license`). הפיצול המדויק בין חינם לתשלום נמצא ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים במחשב שלכם

ClawMetry קורא קובצי סשן ולוגים מקומיים. **שום נתון סשן לא עוזב את המחשב שלכם
אלא אם כן אתם מריצים `clawmetry connect`** — לא הנחיות (prompts), תשובות, ארגומנטים של כלים, תוכן קבצים או שורות לוג. כשאתם כן מתחברים, התמונה (snapshot) מוצפנת מקצה לקצה
עם מפתח שאף פעם לא עוזב את המחשב שלכם, ומפוענחת בדפדפן שלכם. אם
לצומת אין מפתח, ההעלאה מדולגת במקום להישלח בטקסט גלוי, ואף
תגובת שרת לא יכולה לכבות את זה.

שני דברים כן פועלים כברירת מחדל לפני שאתם מתחברים, שניהם ניתנים לביטול ואף אחד מהם
לא נושא נתוני סשן: פינג התקנה אנונימי ובדיקת גרסה מול
PyPI. התקנת ברירת מחדל גם מחפשת את כתובת ה-IP הציבורית שלכם פעם אחת עבור שורת באנר
פתיחה. כל יעד, מה הוא נושא וכיצד לכבות אותו רשום ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות בהתקנה עצמית, מנותבות מחדש, ומבודדות רשת
לא מבצעות שום קריאות יוצאות שיקוליות כלל.

הפענוח מתרחש בדפדפן שלכם, בקוד שאנחנו מגישים לכם. זה היה פעם
הבטחה; עכשיו זה משהו שאתם יכולים לבדוק. כל שורה שנוגעת במפתח שלכם
נמצאת בקובץ קריא אחד, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שנשלח בתוך ה-wheel ומוגש כלשונו, מוצמד (pinned) עם hash של Subresource
Integrity. כדי לוודא שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את העמוד שטוען את הקובץ, כך שיכולנו
להגיש עמוד שונה. hashים של אינטגריטי מגנים עליכם משרת CDN שנפרץ,
לא מהספק. מה שאתם מרוויחים הוא שכל החלפה חייבת להיות
מכוונת, גלויה במקור העמוד, ושונה מארטיפקט ב-PyPI
שכל אחד יכול להוריד. התקנה עצמית או הישארות מקומית בלבד מסירה את
התלות לחלוטין.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או קו הפקודה החד-שורתי: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ על macOS, Linux או Windows, ולפחות סביבת ריצה אחת של סוכן על
אותה מכונה. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

## תיעוד

| | |
|---|---|
| [תאימות סביבות ריצה](docs/compatibility.md) | מה כל מתאם קורא, ואיך להוסיף סביבת ריצה |
| [פיצוץ הקשר](docs/CONTEXT_BLOWOUT.md) | חלונות לפי ספק, דחיסה מול גלישה, כיסוי לפי סביבת ריצה |
| [תקורה (Overhead)](docs/OVERHEAD.md) | מה עולה האינסטרומנטציה, נמדד, עם הרתמה לשחזור |
| [זכאויות](docs/ENTITLEMENTS.md) | חינם מול תשלום, מטריצת רמות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | חסימה טרום-ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | יצוא עקבות (traces) לכל מקום, קליטת OTLP מכל מקום |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלות לסוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בסביבת ארגז חול (sandbox) |
| [Docker](docs/DOCKER.md) | תמונה, compose, הרכבות volume |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד בפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה האנונימיים ופתיחת שולחן העבודה, וכיצד לכבות אותם |

## צילומי מסך

כל מספר למטה הוא ממכונה אמיתית אחת, בקריאה בלבד, ללא שום דבר מלאכותי.

**הוא אומר לכם מתי משהו לא בסדר, לא רק מה קרה.**
שני באנרי חריגה בראש: הוצאה שרצה פי 7 מהממוצע היומי, וקפיצת
עלות פי 4.2. מתחתם, 324 מתוך 667 סשנים אחרונים נושאים סימן
בזבוז, מפורטים לפי סיבה.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**הוא מראה לכם לאן הלך הכסף, בכל חלון זמן.**
$252.47 היום, $513.15 השבוע, $1,312.92 החודש, כל אחד עם הטוקנים
מאחוריו וכמה מזה המנוי שלכם כבר מכסה. מתחת לזה, כ-$1,128/חודש
מפורטים כניתנים להשבה וכ-$17,256/חודש שכבר נחסכו על ידי שימוש חוזר
במטמון (cache reuse).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**הוא מצייר איך הודעה הופכת לתשובה.**
תרשים הזרימה החי: אתם, הערוץ שבו היא הגיעה, השער (gateway), המודל
שעונה כרגע, וכל כלי שהוא פנה אליו. צמתים נדלקים ככל שהעבודה
זזה דרכם.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכונה, בטבלה אחת.**
מה הוא מריץ, כמה הוא עלה ב-24 השעות האחרונות ולאורך חייו, מתי
הוא נראה לאחרונה, מי הבעלים שלו, ואם מנוי מכסה את
החשבון. 14 סוכנים כאן, 3 סשנים עובדים, 13 שקטים.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**הוא מראה לאן הלכו הזמן והכסף של תור, כלי אחרי כלי.**
תור אחד מתוך סשן אמיתי: 11 כלים ב-11.2 דקות תמורת $1.16. כל
קריאת Bash וכל קריאת מודל מקבלות פס משלהן על ציר הזמן, כך
שהפקודה שרצה 4.1 דקות והפקודה שרצה 226 מילישניות נבדלות במבט אחד.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**הוא מדרג את העבודה, לא רק את ההוצאה.**
ציון A השבוע: 54 משימות חזרו נקיות, 2 גסות עלו $48.57, וההרצות
עם פעילות מועטה מדי לשיפוט הושמטו מהציון במקום להיספר
כניצחונות. כל הרצה גסה מקושרת לעקבה (trace) שלה.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**הוא מראה למה חלון ההקשר ממשיך להתמלא.**
715K מתוך חלון של 1M טוקנים בתור האחרון, שיא של 83.3%, 4 דחיסות
שכולן הופעלו יזומה ולא בעקבות גלישה, ותפוסת
כל תור מאחוריו.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**הזיהוי פועל בלי שתצטרכו להגדיר דבר.**
הגלאים המובנים פעילים מההתקנה: הסוכן השתתק, זרם הטלמטריה
נעצר, קפיצת עלות, פרץ טוקנים, שגיאות מטפסות, קפיצת שגיאות, סף
תקציב, חתימת איום זוהתה, ממצא כלי אבטחה, שינוי בעמדת אבטחה.
הכללים שלכם הם אופציונליים בנוסף.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**עצירת קריאה מסוכנת היא אופציונלית, ומגיעה כבויה.**
מחיקות רקורסיביות, force push, sudo, סודות, התקנות חבילות
וקריאות יוצאות מקבלים כל אחד כלל שאפשר להפעיל. עד שתפעילו,
ClawMetry צופה ולא משנה דבר. ברגע שאחד מופעל, קריאות תואמות
ממתינות כאן (או בטלפון שלכם) לאישור או דחייה.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
