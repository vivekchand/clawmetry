<!-- i18n-src:a855a14295b0 -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**סוכן יכול לבצע מאה קריאות כלים בלי לחולל התקדמות.** ClawMetry
קוראת את קובצי הסשן שסוכני הקוד שלך כותבים כבר בעצמם, ומאגדת את ציר הזמן,
קריאות הכלים וכל נתוני הטוקנים והעלות שה-runtime חושף לתצוגה אחת -
כך שתוכל להבחין בין הרצה ארוכה שעובדת לבין הרצה שנתקעה.

עובד עם **32 runtimes של סוכני AI** - Claude Code, OpenAI Codex, Hermes, OpenClaw ו-28 נוספים. דשבורד אחד לכל צי הסוכנים שלך. ([הרשימה המלאה](SUPPORTED_RUNTIMES.txt), שנוצרת מהקטלוג.)

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. אפס הגדרות. מאתר הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס הגדרות: המערכת מוצאת את ה-runtimes
שכבר מותקנים לך, קוראת אותם בקריאה בלבד, ולא משנה כלום באופן שבו הם רצים.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## לפני שאתם מתקינים

| | |
|---|---|
| **מה זה עושה** | קוראת את קובצי הסשן והלוגים שהסוכנים שלך כותבים כבר בעצמם. אין SDK, אין שינוי קוד, אין אינסטרומנטציה באפליקציה שלכם. |
| **מה אתם רואים** | ציר זמן של הסשן, שידור חוזר כלי-אחר-כלי, פירוט טוקנים ועלות, ואינדיקטורים למגמות (לופים, כשלים חוזרים) - לפי runtime. |
| **מה חינמי** | `pip install clawmetry` קוראת **OpenClaw, NVIDIA NemoClaw ו-Goose** בלי חשבון, בלי מפתח ובלי קריאת רשת. 27 האחרים - Claude Code, Codex, Cursor והשאר - נקראים על ידי המלווה הקוד-סגור `clawmetry-pro`, שמגיע עם תקופת הניסיון של 7 ימים או תוכנית מנוי - ראו [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) לחלוקה המדויקת. |
| **איך מתחילים** | `pip install clawmetry && clawmetry`, ואז פותחים את localhost:8900. אין עדיין סוכנים על המחשב הזה? `clawmetry --sample` נפתח עם שלושה סשנים סינתטיים מתויגים. |
| **מה עוזב את המחשב שלכם** | אין נתוני סשן, אלא אם תריצו `clawmetry connect`. שני דברים כן רצים כברירת מחדל, שניהם ניתנים לביטול ואף אחד מהם לא נושא תוכן סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI. כל יעד רשום ב-[docs/EGRESS.md](docs/EGRESS.md), שנבנה מלכידת תעבורת רשת בפועל ולא מקריאת הערות בקוד. |

שתי מגבלות ששווה להכיר לפני שתשפטו את הפלט: ה-runtimes חושפים נתונים שונים
מאוד (חלקם לא מפרסמים עלות בכלל - [המטריצה](docs/compatibility.md)
מציינת מי, לפי runtime), וצפייה בפעולה אינה זהה ליכולת לחסום אותה
([אילו פקדים אמיתיים, לפי runtime](docs/APPROVALS.md)).


## עובד עם 32 runtimes של סוכנים

**חינם באפליקציית קוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל runtime מקבל את אותו הדשבורד. הריצו כמה בבת אחת, והמחליף בכותרת
יעצב מחדש את ההיקף של כל טאב לאחד מהם.

בניתם סוכן משלכם על גבי SDK במקום זאת? המיירט (interceptor) עוקב גם אחרי
קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה אתם מקבלים

- **סשנים ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שידור חוזר
- **עלות וטוקנים**: לפי runtime, מודל, סשן ויום, עם דגלי חריגות
- **זרימה (Flow)**: דיאגרמה חיה של הודעות שעוברות בין ערוצים, מודלים וכלים
- **מוח (Brain)**: זרם אירועי החשיבה וקריאות הכלים בזמן אמת
- **התפוצצות קונטקסט**: ניצול חלון הקונטקסט בגודל לפי ספק, דחיסה מול גלישה מאולצת, בתוספת מפה לפי runtime של מה שאנחנו *לא יכולים* לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים**: הקבצים והכישורים שכל runtime בפועל טען
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוג חי
- **התראות**: תקציבי מקסימום, קפיצות שגיאות, סוכן-לא-מקוון, מנותב ל-Slack, Discord, PagerDuty, Telegram, Email
- **אישורים**: עיכוב קריאות כלים מסוכנות *לפני* שהן רצות ואישור מהטלפון שלכם ([איך](docs/APPROVALS.md))

## התפוצצות קונטקסט, ומה עולה המעקב

שתי שאלות ששווה לענות עליהן לפני שתסמכו על כל כלי להשוואת סוכנים.

**איך המערכת מתמודדת עם התפוצצות חלון קונטקסט בין runtimes?**

אחוז ניצול הוא הגון בדיוק כמו המכנה שהוא מחולק בו. ClawMetry
קובעת את גודל החלון לפי ספק מ-[טבלה שאפשר לקרוא ולשלוח לה PR](clawmetry/context_windows.py),
המכסה את Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ו-GLM. היא לא מודדת את כל 32
ה-runtimes בסרגל של ספק אחד. זה משנה: תור בגודל 300K של GPT-5 שנבדק
מול ה-200K של Anthropic נקרא ">100%, התפוצץ" כשבפועל הוא ב-75% מה-400K
של GPT-5. אותו סרגל מסתיר תור DeepSeek בגודל 130K שבאמת גלש כ-65%
נוחים.

כל חלון מגיע עם המקור שלו: `model_table`, `explicit_marker`,
`observed_floor`, או `default` הגון כשאנחנו לא מכירים את המודל. מד שנבנה
על השערה לעולם לא מוצג באותה סמכות כמו מד שנבנה על חיפוש בטבלה.

ClawMetry יכולה לראות אירועי דחיסה רק בחלק מה-runtimes. כך ש-
`GET /api/context-coverage` מדווחת, לפי runtime, אם **אפס פירושו
"רץ נקי" או "אנחנו עיוורים"**. אפס שבאמת פירושו עיוורים אומר זאת בבירור.
[פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**מה האינסטרומנטציה עולה?**

| נתיב | נוסף לסוכן שלכם | ברירת מחדל? |
|---|---|---|
| מעקב אחר קובצי סשן (כל 32 ה-runtimes) | **0**. תהליך נפרד, אין קוד ClawMetry בסוכן שלכם | פעיל |
| מיירט HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 מ"ש** לכל קריאת LLM, כלומר 0.009% מקריאה של 5 שניות | כבוי |
| שער hook לפני-כלי (מטמון חם) | **+44 מ"ש** לכל קריאת כלי שנשערת, מעל רצפת מפרש של 36 מ"ש | כבוי |
| פרוקסי אכיפה | **+9.7 מ"ש** לכל קריאת LLM | כבוי |

עלות מארח הדיימון: **2,762 אירועים/שנייה** קליטה, **710 בייטים/אירוע** על
הדיסק (67.7 מגה-בייט לכל 100,000 אירועים), ו-**כ-12% מליבה אחת** באופן
מתמשך על התקנה עמוסה. המספר האחרון הזה חורג מתקציב ה-5-10% שקבענו
לעצמנו, כך שהוא מתפרסם כבאג למעקב ולא מוסתר מהדף.

נמדד על Apple M2 Pro עם `benchmarks/overhead.py`. ה-harness מריץ
כל תנאי בתהליך נפרד, מחליף בין הסדר שלהם, ו**מסרב להדפיס מספר כשהסבבים
לא מסכימים על הסימן שלו**. הריצו אותו על המחשב שלכם בתוך דקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook ופרוקסי האכיפה,
וה-harness רץ על Linux, macOS ו-Windows ב-CI. שתי תוצאות ששווה
להכיר: הפרוקסי עולה בערך שבע פעמים יותר על Windows מאשר על Linux, והדיימון
מחזיק כרגע כ-12% מליבה אחת, מעל תקציב ה-5-10% שלנו. ה-JSON הגולמי, השיטה, ומה
שעדיין לא נמדד נמצאים ב-[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא מכסה | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, דשבורד מלא, מקומי בלבד | $0 |
| **Starter** | כל runtime אחר שלמעלה, תצוגת צי, סנכרון עם הענן | $9 לצומת / חודש |
| **Pro** | Starter + שליטה והערכה: אישורים, מדיניות סיכון-כלים, הערכות, זיהוי חריגות, מייעל עלות, ייצוא OTel, יומן ביקורת חסין-שיבוש | $19 לצומת / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישוי לאירוח עצמי
עובדים בלי הענן (`clawmetry license`). החלוקה המדויקת בין חינם לתשלום
נמצאת ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים על המחשב שלכם

ClawMetry קוראת קובצי סשן ולוגים מקומיים. **שום נתון סשן לא עוזב את המכשיר שלכם
אלא אם תריצו `clawmetry connect`** - לא הנחיות, לא תשובות, לא ארגומנטים של כלים,
לא תוכן קבצים ולא שורות לוג. כשאתם אכן מתחברים, התמונת המצב מוצפנת מקצה לקצה
עם מפתח שלעולם לא עוזב את המחשב שלכם, ומפוענחת בדפדפן שלכם. אם לצומת אין
מפתח, ההעלאה מדולגת ולא נשלחת בגלוי, ואף תגובת שרת לא יכולה לכבות את זה.

שני דברים כן רצים כברירת מחדל לפני שאתם מתחברים, שניהם ניתנים לביטול ואף אחד
מהם לא נושא נתוני סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI. התקנת ברירת
מחדל גם מחפשת את כתובת ה-IP הציבורית שלכם פעם אחת עבור שורת בנר בהפעלה. כל
יעד, מה הוא נושא ואיך לכבות אותו רשומים ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות מאורחות בעצמי, מכוונות מחדש
ומבודדות מרשת אינן מבצעות שום קריאה חוצה-רשת שאינה חיונית.

הפענוח מתבצע בדפדפן שלכם, בקוד שאנחנו מגישים לכם. זו הייתה הבטחה בעבר;
עכשיו זה דבר שאפשר לבדוק. כל שורה שנוגעת במפתח שלכם חיה בקובץ קריא אחד,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שמגיע בתוך ה-wheel ומוגש כלשונו, מקובע עם גיבוב Subresource
Integrity. כדי לאשר שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את העמוד שטוען את הקובץ, כך שיכולנו להגיש
עמוד אחר. גיבובי Integrity מגנים עליכם מ-CDN שנפרץ, לא מהיצרן. מה שאתם
מרוויחים הוא שכל החלפה חייבת להיות מכוונת, נראית בקוד המקור של העמוד, ושונה
מארטיפקט על PyPI שכל אחד יכול להוריד. אירוח עצמי או שהייה מקומית בלבד
מסירים את התלות הזו לחלוטין.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או השורה האחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ על macOS, Linux או Windows, ולפחות runtime סוכן אחד על
אותו מחשב. הנחיות Docker: [docs/DOCKER.md](docs/DOCKER.md).

או תנו לסוכן להגדיר את זה בעצמכם. הכישור [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
מלמד את Claude Code, Codex, Cursor, Gemini CLI, Copilot או OpenCode
להתקין את ClawMetry, לדווח מה הסוכנים על המכשיר עושים ומוציאים,
לעצור סשן אחד לפי דרישה, ולעכב קריאות כלים מסוכנות לאישור:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## תיעוד

| | |
|---|---|
| [תאימות runtime](docs/compatibility.md) | מה כל מתאם קורא, ואיך להוסיף runtime |
| [התפוצצות קונטקסט](docs/CONTEXT_BLOWOUT.md) | חלונות לפי ספק, דחיסה מול גלישה, כיסוי לפי runtime |
| [עומס נוסף (Overhead)](docs/OVERHEAD.md) | מה האינסטרומנטציה עולה, נמדד, עם ה-harness לשחזור |
| [הרשאות (Entitlements)](docs/ENTITLEMENTS.md) | חינם מול בתשלום, מטריצת דרגות, CLI לרישוי |
| [אישורים ומדיניות](docs/APPROVALS.md) | שערים לפני הרצה, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא traces לכל מקום, קליטת OTLP מכל דבר |
| [הביאו את הסוכן שלכם](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain מקצה לקצה, עם דוגמאות שאפשר להריץ |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלות לסוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw במארז מבודד (sandboxed) |
| [Docker](docs/DOCKER.md) | תמונה, compose, הרכבות נפח |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד בפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה האנונימית ופתיחת שולחן העבודה, ואיך לכבות אותם |

## צילומי מסך

כל מספר למטה הוא ממחשב אחד אמיתי, בקריאה בלבד, בלי שום דבר מוזרע.

**המערכת אומרת לכם כשמשהו שגוי, לא רק מה קרה.**
שני בנרי חריגה בראש: הוצאה שרצה 7 פעמים מהממוצע היומי, וקפיצת עלות
של 4.2x. מתחתיהם, 324 מ-667 סשנים אחרונים נושאים סימן לבזבוז, מפורטים
לפי סיבה.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**המערכת מציגה לכם לאן הכסף הלך, בכל חלון זמן.**
$252.47 היום, $513.15 השבוע, $1,312.92 החודש, כל אחד עם הטוקנים
שמאחוריו וכמה מהם המנוי שלכם כבר מכסה. מתחת לזה, בערך $1,128/חודש
מפורטים כמשוחזרים ו-$17,256/חודש שכבר נחסכו על ידי שימוש חזור במטמון.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**המערכת מציגה איך הודעה הופכת לתשובה.**
דיאגרמת הזרימה החיה: אתם, הערוץ שממנו זה הגיע, השער (gateway), המודל
שעונה כרגע, וכל כלי שהוא פנה אליו. צמתים נדלקים כשעבודה זזה בהם.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכשיר, בטבלה אחת.**
מה הוא מריץ, מה הוא עולה ב-24 השעות האחרונות ובמשך חייו, מתי הוא נראה
לאחרונה, מי הבעלים שלו, ואם מנוי מכסה את החשבון. 14 סוכנים כאן, 3 סשנים
עובדים, 13 שקטים.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**המערכת מציגה לאן הזמן והכסף של תור הלכו, כלי אחר כלי.**
תור אחד של סשן אמיתי: 11 כלים ב-11.2 דקות עבור $1.16. כל קריאת Bash
וכל קריאת מודל מקבלות פס משלהן על ציר הזמן, כך שהפקודה שרצה
4.1 דקות והפקודה שרצה 226 מילישניות נבדלות זו מזו במבט אחד.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**המערכת מדרגת את העבודה, לא רק את ההוצאה.**
דירוג A' השבוע: 54 משימות הוחזרו נקיות, 2 גסות עלו $48.57, וההרצות
עם פעילות מעטה מכדי לשפוט אותן הושמטו מהדירוג במקום להיחשב כזכיות. כל
הרצה גסה מקושרת לעקבה (trace) שלה.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**המערכת מציגה מדוע חלון הקונטקסט ממשיך להתמלא.**
715K מחלון של 1M טוקנים בתור האחרון, שיא של 83.3%, 4 דחיסות
שכולן הופעלו באופן פרואקטיבי ולא עקב גלישה, וניצול כל תור שמאחוריהן.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**זיהוי רץ בלי שתגדירו כלום.**
הגלאים המובנים פעילים מההתקנה: הסוכן השתתק, זרימת הטלמטריה
נעצרה, קפיצת עלות, פרץ טוקנים, שגיאות עולות, קפיצת שגיאות, סף
תקציב, זוהתה חתימת איום, ממצא כלי אבטחה, שינוי בעמדת אבטחה.
הכללים שלכם עצמכם הם אופציונליים בנוסף.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**עיכוב קריאה מסוכנת הוא אופציונלי, ומגיע כבוי.**
מחיקות רקורסיביות, force push, sudo, סודות, התקנות חבילות וקריאות
יוצאות מקבלות כל אחת כלל שאפשר להפעיל. עד שתעשו זאת, ClawMetry
צופה ולא משנה כלום. כשאחד מופעל, קריאות מתאימות מחכות כאן (או בטלפון
שלכם) לאישור או דחייה.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

עוד, לפי runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## הכרה

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## היסטוריית כוכבים

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## רישוי

MIT · נבנה על ידי [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
