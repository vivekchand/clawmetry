<!-- i18n-src:c99ac0512cae -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**סוכן יכול לבצע מאה קריאות לכלים בלי להתקדם בכלל.** ClawMetry
קוראת את קבצי הסשן שסוכני הקוד שלך כותבים כבר בעצמם, ומציבה את ציר הזמן,
קריאות הכלים וכל נתוני הטוקנים והעלות שה-runtime חושף במבט אחד — כך שתוכל להבדיל בין הרצה ארוכה שעובדת לבין הרצה שנתקעה.

עובד עם **33 סוכני ריצה (runtimes) של AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw ו-29 נוספים. דשבורד אחד לכל צי הסוכנים שלך. ([הרשימה המלאה](SUPPORTED_RUNTIMES.txt), שנוצרת מתוך הקטלוג.)

> 🌐 **קרא זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. אפס קונפיגורציה. מגלה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס קונפיגורציה: המערכת מאתרת את סוכני הריצה שכבר יש לך, קוראת אותם לקריאה בלבד, ולא משנה שום דבר באופן שבו הם רצים.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## לפני שמתקינים

| | |
|---|---|
| **מה זה עושה** | קוראת את קבצי הסשן והלוגים שהסוכנים שלך כבר כותבים. בלי SDK, בלי שינוי קוד, בלי instrumentation באפליקציה שלך. |
| **מה אתה רואה** | ציר זמן של הסשן, שחזור (replay) כלי-אחר-כלי, פירוט טוקנים ועלות, וסיגנלים של מסלול (לופים, כשלים חזרתיים) — לפי runtime. |
| **מה חינמי** | `pip install clawmetry` קוראת את **OpenClaw, NVIDIA NemoClaw, Goose ו-Qwen Code** בלי חשבון, בלי מפתח ובלי קריאת רשת. 28 ה-runtimes האחרים — Claude Code, Codex, Cursor והשאר — נקראים על ידי התוסף הסגור-קוד `clawmetry-pro`, שמגיע עם תקופת ניסיון של 7 ימים או עם תוכנית — ראו [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) לפירוט המדויק. |
| **איך מתחילים** | `pip install clawmetry && clawmetry`, ואז פותחים localhost:8900. אין עדיין סוכנים על המכונה הזו? `clawmetry --sample` נפתח עם שלושה סשנים סינתטיים מתויגים. |
| **מה עוזב את המכונה שלך** | שום נתוני סשן, אלא אם תפעיל את `clawmetry connect`. שני דברים פועלים כברירת מחדל, שניהם ניתנים לביטול (opt-out) ואף אחד מהם לא נושא תוכן סשן: פינג אנונימי של התקנה ובדיקת גרסה מול PyPI. כל יעד רשום במלואו ב-[docs/EGRESS.md](docs/EGRESS.md), שנבנה מלכידת תעבורת רשת ולא מקריאת הערות בקוד. |

שתי מגבלות שכדאי להכיר לפני שמעריכים את הפלט: ל-runtimes שונים יש חשיפת נתונים שונה מאוד (חלקם לא מפרסמים עלות כלל — [המטריצה](docs/compatibility.md) מראה מי), וצפייה בפעולה אינה זהה ליכולת לחסום אותה ([אילו פקדים הם אמיתיים, לפי runtime](docs/APPROVALS.md)).


## עובד עם 33 סוכני ריצה

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל runtime מקבל את אותו הדשבורד. הפעל כמה בבת אחת, ומחליף ה-header ממקד מחדש כל טאב לאחד מהם.

בנית סוכן משלך על גבי SDK במקום? ה-interceptor עוקב גם אחרי קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה אתה מקבל

- **סשנים ותמלילים**: מה כל סוכן עשה, תור אחר תור, עם שחזור (replay)
- **עלות וטוקנים**: לפי runtime, מודל, סשן ויום, עם דגלי אנומליה
- **Flow**: דיאגרמה חיה של הודעות הזזות בין ערוצים, מודלים וכלים
- **Brain**: זרם האירועים של ההיגיון וקריאות הכלים בזמן אמת
- **Context blowout**: ניצול חלון הקשר (window) מחושב לפי ספק, קיזוז (compaction) מול גלישה כפויה, ועוד מיפוי לפי runtime של מה שאנחנו *לא* יכולים לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים (Skills)**: הקבצים והכישורים שכל runtime בפועל טען
- **תקינות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, הגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאה, סוכן-לא-מגיב, מנותב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **אישורים**: עצירת קריאות כלים מסוכנות *לפני* שהן רצות ואישור מהטלפון שלך ([איך](docs/APPROVALS.md))

## גלישת הקשר (Context blowout), ומה עולה לעקוב

שתי שאלות שכדאי לענות עליהן לפני שסומכים על כלי השוואת-סוכנים כלשהו.

**איך זה מתמודד עם גלישת חלון הקשר בין runtimes?**

אחוז ניצול הוא ישר כמו המכנה שעליו הוא מחושב. ClawMetry
קובעת את גודל החלון לפי ספק מתוך [טבלה שאפשר לקרוא ולשלוח
PR עליה](clawmetry/context_windows.py), המכסה את Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ו-GLM. היא לא מודדת את כל 33
ה-runtimes בסרגל של ספק אחד. זה משנה: תור של 300K של GPT-5 שנמדד
מול ה-200K של Anthropic נקרא ">100%, blown" כשבפועל הוא ב-75% מתוך
ה-400K של GPT-5. אותו סרגל מסתיר תור אמיתי של DeepSeek בגודל 130K שגלש כ-65% נוח.

כל חלון מגיע עם המקור שלו: `model_table`, `explicit_marker`,
`observed_floor`, או `default` כן ואמיתי כשלא ידוע לנו המודל. מד
שנבנה על ניחוש לא נראה באותה סמכות כמו מד שנבנה על
חיפוש בטבלה.

ClawMetry יכולה לראות אירועי compaction רק בחלק מה-runtimes. אז
`GET /api/context-coverage` מדווחת, לפי runtime, האם **אפס פירושו
"רץ חלק" או "אנחנו עיוורים"**. אפס שבאמת אומר עיוור, אומר זאת.
[פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**מה ה-instrumentation עולה?**

| נתיב | נוסף לסוכן שלך | ברירת מחדל? |
|---|---|---|
| מעקב אחרי קבצי סשן (כל 33 ה-runtimes) | **0**. תהליך נפרד, בלי קוד ClawMetry בסוכן שלך | פעיל |
| Interceptor ל-HTTP (`CLAWMETRY_INTERCEPT=1`) | **‎+0.44 מילישנייה** לכל קריאת LLM, או 0.009% מקריאה של 5 שניות | כבוי |
| שער hook טרום-כלי (cache חם) | **‎+44 מילישנייה** לכל קריאת כלי מגודרת, מעל רצפת interpreter של 36 מילישנייה | כבוי |
| פרוקסי אכיפה | **‎+9.7 מילישנייה** לכל קריאת LLM | כבוי |

עלות ה-daemon המארח: קצב קליטה של **2,762 אירועים/שנייה**, **710
בייט לאירוע** על הדיסק (67.7MB ל-100 אלף אירועים), ו-**כ-12% מליבה אחת**
בעומס מתמשך על התקנה עמוסה. המספר האחרון הזה חוצה את התקציב המוצהר
שלנו של 5-10%, ולכן הוא מתפרסם כבאג לרדוף אחריו, לא מוסתר מהעמוד.

נמדד על Apple M2 Pro עם `benchmarks/overhead.py`. ה-harness מריץ
כל תנאי בתהליך נפרד, מחליף את הסדר ביניהם, ו**מסרב
להציג מספר כשהסבבים לא מסכימים על הסימן שלו**. הרץ אותו על המכונה שלך בדקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook ופרוקסי האכיפה,
וה-harness רץ על Linux, macOS ו-Windows ב-CI. שתי תוצאות שכדאי
להכיר: הפרוקסי עולה בערך שבע פעמים יותר ב-Windows מאשר ב-Linux, ו-
ה-daemon כרגע מחזיק עומס מתמשך של בערך 12% מליבה אחת, מעל תקציב
5-10% שלנו. ה-JSON הגולמי, המתודולוגיה, ומה שעדיין לא נמדד נמצאים ב-
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא מכסה | מחיר |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, דשבורד מלא, מקומי בלבד | $0 |
| **Starter** | כל שאר ה-runtimes שלמעלה, תצוגת צי, סנכרון עם הענן | $9 לנוד / חודש |
| **Pro** | Starter + שליטה והערכה: אישורים, מדיניות סיכון-כלים, evals, זיהוי אנומליות, אופטימיזציית עלות, ייצוא OTel, יומן ביקורת שמוכיח אי-שינוי (tamper-evident) | $19 לנוד / חודש |

תוכניות שנתיות, Enterprise והמחירים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון בהתקנה עצמית
עובדים בלי הענן (`clawmetry license`). החלוקה המדויקת של חינם/בתשלום
נמצאת ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלך נשארים על המכונה שלך

ClawMetry קוראת קבצי סשן ולוגים מקומיים. **שום נתון סשן לא עוזב את המכשיר שלך
אלא אם תפעיל את `clawmetry connect`** — בלי prompts, תגובות, פרמטרים של כלים, תוכן
קבצים או שורות לוג. כשאתה מתחבר, ה-snapshot מוצפן מקצה-לקצה
עם מפתח שלא עוזב את המכונה שלך, ומפוענח בדפדפן שלך. אם לנוד
אין מפתח, ההעלאה מדולגת במקום להישלח בטקסט פתוח, ואף
תגובת שרת לא יכולה לכבות את זה.

שני דברים פועלים כברירת מחדל לפני שמתחברים, שניהם ניתנים לביטול ואף אחד מהם לא
נושא נתוני סשן: פינג אנונימי של התקנה ובדיקת גרסה מול
PyPI. התקנה כברירת מחדל גם מחפשת את כתובת ה-IP הציבורית שלך פעם אחת לשורת
כותרת של פתיחה. כל יעד, מה הוא נושא ואיך לכבות אותו רשום ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות שמתבססות על אירוח עצמי, מכוונות-מחדש ומנותקות-רשת
אינן יוזמות שום קריאות יוצאות שרירותיות.

הפענוח קורה בדפדפן שלך, בקוד שאנחנו מגישים לך. זה היה פעם
הבטחה; כעת זה דבר שאפשר לבדוק. כל שורה שנוגעת במפתח שלך
נמצאת בקובץ קריא אחד, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שמגיע בתוך ה-wheel ומוגש כפי שהוא, מוצמד עם hash Subresource
Integrity. לאמת שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את העמוד שטוען את הקובץ, ולכן אנחנו יכולים
להגיש עמוד אחר. hashי Integrity מגנים עליך מ-CDN פרוץ,
לא מהיצרן. מה שאתה מקבל הוא שכל חילוף חייב להיות
מכוון, גלוי בקוד המקור של העמוד, ושונה מארטיפקט ב-PyPI
שכל אחד יכול להוריד. אירוח עצמי או שימוש מקומי בלבד מסיר את
התלות לחלוטין.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או הפקודה החד-שורתית: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ על macOS, Linux או Windows, ולפחות סוכן ריצה אחד על
אותה מכונה. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

או תן לסוכן להתקין בשבילך. ה-skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
מלמד את Claude Code, Codex, Cursor, Gemini CLI, Copilot או OpenCode
להתקין את ClawMetry, לדווח מה הסוכנים על המכונה עושים ומוציאים,
לעצור סשן אחד לפי דרישה, ולעכב קריאות כלים מסוכנות לאישור:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## תיעוד

| | |
|---|---|
| [תאימות Runtime](docs/compatibility.md) | מה כל מתאם קורא, ואיך מוסיפים runtime |
| [גלישת הקשר (Context blowout)](docs/CONTEXT_BLOWOUT.md) | חלונות לפי ספק, compaction מול גלישה, כיסוי לפי runtime |
| [תקורה (Overhead)](docs/OVERHEAD.md) | מה ה-instrumentation עולה, נמדד, עם ה-harness לשכפול |
| [הרשאות (Entitlements)](docs/ENTITLEMENTS.md) | חינם מול בתשלום, מטריצת רמות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | גידור לפני-ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא traces לכל מקום, קליטת OTLP מכל דבר |
| [הבא את הסוכן שלך בעצמך](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain מקצה לקצה, עם דוגמאות שרצות |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלות לסוכנים שבנית בעצמך |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בסנדבוקס |
| [Docker](docs/DOCKER.md) | אימג', compose, הצמדות volume |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה האנונימית ופתיחת-שולחן-העבודה, ואיך לכבות אותם |

## צילומי מסך

כל מספר למטה הוא ממכונה אמיתית אחת, לקריאה בלבד, בלי שום דבר מוזן בדיעבד.

**זה אומר לך מתי משהו לא בסדר, ולא רק מה קרה.**
שני פסי אנומליה בראש העמוד: הוצאה שרצה ב-7x מהממוצע היומי, ו-
קפיצת עלות של 4.2x. מתחתיהם, 324 מתוך 667 הסשנים האחרונים נושאים
סיגנל של בזבוז, מפורט לפי סיבה.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**זה מראה לך לאן הכסף הלך, בכל חלון זמן.**
$252.47 היום, $513.15 השבוע הזה, $1,312.92 החודש הזה, כל אחד עם הטוקנים
מאחוריו וכמה מזה המנוי שלך כבר מכסה. מתחת לזה,
כ-$1,128 לחודש מפורטים כניתנים להשבה, וכ-$17,256 לחודש שנחסכו כבר
על ידי שימוש חוזר ב-cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**זה מתאר איך הודעה הופכת לתשובה.**
דיאגרמת ה-flow החיה: אתה, הערוץ שבו ההודעה הגיעה, ה-gateway, המודל
שעונה כרגע, וכל כלי שהוא פנה אליו. צמתים נדלקים כשעבודה
עוברת בהם.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכונה, בטבלה אחת.**
מה הוא מריץ, מה הוא עלה ב-24 השעות האחרונות ובמשך כל חייו, מתי
הוא נראה לאחרונה, מי הבעלים שלו, ואם מנוי מכסה את
החשבון. 14 סוכנים כאן, 3 סשנים עובדים, 13 שקטים.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**זה מראה לאן הזמן והכסף של תור הלכו, כלי אחר כלי.**
תור אחד של סשן אמיתי: 11 כלים ב-11.2 דקות עבור $1.16. כל קריאת Bash
וכל קריאת מודל מקבלת פס משלה על ציר הזמן, כך שהפקודה שרצה
4.1 דקות ואחת שרצה 226 מילישנייה נבדלות במבט חטוף.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**זה מעריך את העבודה, לא רק את ההוצאה.**
ציון A השבוע הזה: 54 משימות חזרו נקיות, 2 גרועות עלו $48.57, וה-
הרצות עם פעילות מעטה מכדי לשפוט נשארות מחוץ לציון במקום
להיחשב כזכיות. כל הרצה גרועה מקושרת לtrace שלה.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**זה מראה למה חלון ההקשר ממשיך להתמלא.**
715K מתוך חלון של 1M טוקנים בתור האחרון, שיא של 83.3%, 4 compactions
שכולם הופעלו באופן יזום ולא עקב גלישה, ושימוש כל תור
מאחוריו.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**גילוי רץ בלי שתגדיר שום דבר.**
הגלאים המובנים פעילים מההתקנה: הסוכן השתתק, הזנת טלמטריה
נפסקה, קפיצת עלות, פרץ טוקנים, שגיאות מטפסות, קפיצת שגיאה, סף
תקציב, חתימת איום הותאמה, ממצא כלי אבטחה, שינוי בעמידה אבטחתית.
חוקים משלך הם אופציונליים בנוסף.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**עצירת קריאה מסוכנת היא opt-in, ומגיעה כבויה.**
מחיקות רקורסיביות, force pushes, sudo, סודות, התקנות חבילות וקריאות
יוצאות מקבלים כל אחד חוק שאפשר להפעיל. עד שתעשה את זה, ClawMetry
צופה ולא משנה כלום. כשאחד מופעל, קריאות מתאימות מחכות כאן
(או בטלפון שלך) לאישור או דחייה.

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

## רישיון

MIT · נבנה על ידי [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
