<!-- i18n-src:61beb8393e2f -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**סוכן יכול לבצע מאה קריאות כלים בלי להתקדם.** ClawMetry
קוראת את קובצי הסשן שסוכני הקוד שלכם כבר כותבים, ומרכזת את ציר הזמן,
קריאות הכלים וכל נתוני הטוקנים והעלות שהריצה חושפת לתצוגה אחת —
כך שתוכלו להבחין בין ריצה ארוכה שעובדת לבין ריצה שנתקעה.

עובד עם **30 ריצות (runtimes) של סוכני AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw ועוד 26. לוח מחוונים אחד לכל צי הסוכנים שלכם. ([הרשימה המלאה](SUPPORTED_RUNTIMES.txt), נוצרת אוטומטית מהקטלוג.)

> 🌐 **קראו את זה ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. בלי הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. בלי הגדרות: היא מוצאת את ריצות הסוכנים
שכבר יש לכם, קוראת אותן בלבד (read-only), ולא משנה דבר באופן שבו הן פועלות.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## לפני שאתם מתקינים

| | |
|---|---|
| **מה זה עושה** | קורא את קובצי הסשן והלוגים שהסוכנים שלכם כבר כותבים. בלי SDK, בלי שינוי קוד, בלי אינסטרומנטציה באפליקציה שלכם. |
| **מה אתם רואים** | ציר זמן של הסשן, שחזור כלי אחר כלי, פירוט טוקנים ועלות, ואותות מסלול (לולאות, כשלים חוזרים) — לכל ריצה. |
| **מה בחינם** | `pip install clawmetry` קוראת את **OpenClaw, NVIDIA NemoClaw ו-Goose** בלי חשבון, בלי מפתח ובלי קריאת רשת. שאר ה-27 — Claude Code, Codex, Cursor והשאר — נקראות על ידי התוסף הסגור `clawmetry-pro`, שמגיע עם תקופת הניסיון של 7 ימים או עם תוכנית — ראו [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) לפירוט המדויק. |
| **איך מתחילים** | `pip install clawmetry && clawmetry`, ואז פותחים localhost:8900. אין עדיין סוכנים על המחשב הזה? `clawmetry --sample` נפתח עם שלושה סשנים סינתטיים מתויגים. |
| **מה יוצא מהמחשב שלכם** | שום נתוני סשן, אלא אם תריצו `clawmetry connect`. שני דברים כן פועלים כברירת מחדל, שניהם ניתנים לכיבוי ואף אחד מהם לא נושא תוכן סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI. כל יעד רשום ב-[docs/EGRESS.md](docs/EGRESS.md), שנבנה מלכידת תעבורת רשת ולא מקריאת הערות בקוד. |

שתי מגבלות שכדאי להכיר לפני שתשפטו את הפלט: ריצות שונות חושפות נתונים
שונים מאוד (חלקן לא מפרסמות עלות בכלל — [המטריצה](docs/compatibility.md)
מציינת אילו, לפי ריצה), ותצפית על פעולה אינה זהה ליכולת לחסום אותה
([אילו פקדים אמיתיים, לפי ריצה](docs/APPROVALS.md)).


## עובד עם 30 ריצות סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל ריצה מקבלת את אותו לוח מחוונים. הריצו כמה בו-זמנית והמתג בכותרת
יתאים מחדש כל לשונית לאחת מהן.

בניתם סוכן משלכם על גבי SDK במקום? המיירט (interceptor) עוקב גם אחרי
קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה אתם מקבלים

- **סשנים ותמלולים**: מה כל סוכן עשה, תור אחר תור, עם שחזור
- **עלות וטוקנים**: לפי ריצה, מודל, סשן ויום, עם סימוני חריגה
- **זרימה (Flow)**: תרשים חי של הודעות שעוברות בין ערוצים, מודלים וכלים
- **מוח (Brain)**: זרם אירועי ההיגיון וקריאות הכלים בזמן אמת
- **התפוצצות הקשר (context)**: ניצול חלון ההקשר לפי ספק, קומפקציה מול גלישה כפויה, וכן מפה לפי ריצה של מה שאנחנו *לא* יכולים לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים (skills)**: הקבצים והכישורים שכל ריצה בפועל טענה
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא זמין, מנותב ל-Slack, Discord, PagerDuty, Telegram, Email
- **אישורים**: השהיית קריאות כלים מסוכנות *לפני* שהן רצות ואישור מהטלפון שלכם ([איך](docs/APPROVALS.md))

## התפוצצות הקשר, ומה עולה לפקח

שתי שאלות ששווה לענות עליהן לפני שתסמכו על כלי כלשהו להשוואת סוכנים.

**איך זה מטפל בהתפוצצות חלון ההקשר בין ריצות שונות?**

אחוז ניצול הגון רק כמו המכנה שלו. ClawMetry קובעת את גודל החלון לפי ספק
מתוך [טבלה שאפשר לקרוא ולשלוח אליה PR](clawmetry/context_windows.py),
המכסה את Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral,
Llama ו-GLM. היא לא מודדת את כל 30 הריצות בסרגל של ספק אחד. וזה משנה:
תור GPT-5 של 300K שנמדד מול ה-200K של Anthropic ייקרא ">100%, התפוצץ"
כשבפועל הוא ב-75% מה-400K של GPT-5. אותו סרגל מסתיר תור DeepSeek של 130K
שבאמת גלש כ-65% נוח.

כל חלון מגיע עם מקורו: `model_table`, `explicit_marker`,
`observed_floor`, או `default` כן ולתומו כשאיננו יודעים מהו המודל. מד
שנבנה על ניחוש לעולם לא יוצג באותה סמכות כמו מד שנבנה על חיפוש בטבלה.

ClawMetry יכולה לראות אירועי קומפקציה רק בחלק מהריצות. לכן
`GET /api/context-coverage` מדווחת, לפי ריצה, האם **אפס פירושו "רץ נקי"
או "אנחנו עיוורים"**. אפס שלמעשה פירושו עיוור אומר זאת במפורש.
[פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**כמה עולה האינסטרומנטציה?**

| נתיב | נוסף לסוכן שלכם | ברירת מחדל? |
|---|---|---|
| מעקב קובצי סשן (כל 30 הריצות) | **0**. תהליך נפרד, בלי קוד ClawMetry בסוכן שלכם | פועל |
| מיירט HTTP (`CLAWMETRY_INTERCEPT=1`) | **‎+0.44 מ״ש** לכל קריאת LLM, או 0.009% מקריאה בת 5 שניות | כבוי |
| שער hook טרום-כלי (מטמון חם) | **‎+44 מ״ש** לכל קריאת כלי שנשערת, מעל רצפת מפרש של 36 מ״ש | כבוי |
| פרוקסי אכיפה | **‎+9.7 מ״ש** לכל קריאת LLM | כבוי |

עלות המארח של הדימון (daemon): **2,762 אירועים/שנייה** קליטה,
**710 בייטים/אירוע** על הדיסק (67.7MB ל-100 אלף אירועים), ו**~12% מליבה
אחת** בעומס יציב על התקנה עמוסה. המספר האחרון הזה חורג מתקציב ה-5-10%
שהצהרנו עליו, ולכן הוא מפורסם כבאג למרדף אחריו ולא מוסתר מהעמוד.

נמדד על Apple M2 Pro עם `benchmarks/overhead.py`. הרתמה (harness) מריצה
כל תרחיש בתהליך נפרד, מחליפה ביניהם בסדר, ו**מסרבת להדפיס מספר כשהסבבים
חלוקים על הסימן שלו**. הריצו אותה על המחשב שלכם תוך דקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook ופרוקסי האכיפה, והרתמה רצה על Linux,
macOS ו-Windows ב-CI. שתי תוצאות ששווה להכיר: הפרוקסי עולה בערך פי שבעה
יותר ב-Windows מאשר ב-Linux, והדימון כרגע שומר על כ-12% מליבה אחת, מעל
תקציב ה-5-10% שלנו. ה-JSON הגולמי, השיטה, ומה שעדיין לא נמדד נמצאים
ב-[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא מכסה | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, לוח מחוונים מלא, מקומי בלבד | $0 |
| **Starter** | כל ריצה נוספת מלמעלה, תצוגת צי, סנכרון ענן | $9 לנוד / חודש |
| **Pro** | Starter + שליטה והערכה: אישורים, מדיניות סיכון-כלים, הערכות (evals), זיהוי חריגות, ממטב עלות, ייצוא OTel, יומן ביקורת עמיד לשיבוש | $19 לנוד / חודש |

תוכניות שנתיות, Enterprise והמחירים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון
לאירוח עצמי עובדים בלי הענן (`clawmetry license`). הפיצול המדויק בין חינם
לתשלום נמצא ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים במחשב שלכם

ClawMetry קוראת קובצי סשן ולוגים מקומיים. **שום נתון סשן לא יוצא מהמכשיר
שלכם אלא אם תריצו `clawmetry connect`** — לא הנחיות (prompts), לא תשובות,
לא ארגומנטים של כלים, לא תוכן קבצים ולא שורות לוג. כשאתם כן מתחברים,
התמונת המצב (snapshot) מוצפנת מקצה לקצה עם מפתח שלעולם לא עוזב את המחשב
שלכם, ומפוענחת בדפדפן שלכם. אם לנוד אין מפתח, ההעלאה מדולגת ולא נשלחת
בבהירות (בלי הצפנה), ואף תגובת שרת לא יכולה לכבות את זה.

שני דברים כן פועלים כברירת מחדל לפני שאתם מתחברים, שניהם ניתנים לכיבוי
ואף אחד לא נושא נתוני סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI.
התקנת ברירת מחדל גם מחפשת את כתובת ה-IP הציבורית שלכם פעם אחת לשורת
באנר בהפעלה. כל יעד, מה הוא נושא ואיך לכבות אותו רשומים ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות באירוח עצמי, מנותבות מחדש
ומבודדות רשת לא מבצעות שום קריאה יוצאת שרירותית בכלל.

הפענוח מתבצע בדפדפן שלכם, בקוד שאנחנו מגישים לכם. פעם זו הייתה הבטחה;
כעת זה משהו שאתם יכולים לבדוק. כל שורה שנוגעת במפתח שלכם נמצאת בקובץ
קריא אחד, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שנשלח בתוך ה-wheel ומוגש מילה במילה, מוצמד עם גיבוב Subresource Integrity.
כדי לוודא שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את הדף שטוען את הקובץ, כך שיכולנו להגיש דף
אחר. גיבובי Integrity מגנים עליכם מ-CDN שנפרץ, לא מהספק עצמו. מה שאתם
מרוויחים הוא שכל החלפה חייבת להיות מכוונת, גלויה במקור הדף, ושונה
מהחפץ (artifact) שב-PyPI שכל אחד יכול להוריד. אירוח עצמי או הישארות
מקומית בלבד מסירים את התלות הזאת לחלוטין.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או שורת ההתקנה האחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ ב-macOS, Linux או Windows, ולפחות ריצת סוכן אחת על אותו
מחשב. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

או תנו לסוכן להתקין עבורכם. הכישור (skill) [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
מלמד את Claude Code, Codex, Cursor, Gemini CLI, Copilot או OpenCode
להתקין את ClawMetry, לדווח מה הסוכנים על המכשיר עושים ומוציאים, לעצור
סשן אחד לפי בקשה, ולהשהות קריאות כלים מסוכנות לאישור:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## תיעוד

| | |
|---|---|
| [תאימות ריצות](docs/compatibility.md) | מה כל מתאם קורא, ואיך להוסיף ריצה |
| [התפוצצות הקשר](docs/CONTEXT_BLOWOUT.md) | חלונות לפי ספק, קומפקציה מול גלישה, כיסוי לפי ריצה |
| [תקורה (Overhead)](docs/OVERHEAD.md) | מה האינסטרומנטציה עולה, נמדד, עם הרתמה לשחזור |
| [זכאויות (Entitlements)](docs/ENTITLEMENTS.md) | חינם מול בתשלום, מטריצת שכבות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | שערור טרום-ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא עקבות (traces) לכל מקום, קליטת OTLP מכל מקום |
| [הביאו את הסוכן שלכם](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain מקצה לקצה, עם דוגמאות שניתן להריץ |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלות לסוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw במבודד (sandboxed) |
| [Docker](docs/DOCKER.md) | תמונה, compose, הרכבת נפחים (volumes) |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה והפתיחה האנונימיים בדסקטופ, ואיך לכבות אותם |

## צילומי מסך

כל מספר למטה הוא ממחשב אמיתי אחד, לקריאה בלבד, בלי שום דבר מוזרע.

**זה אומר לכם מתי משהו לא בסדר, לא רק מה קרה.**
שני באנרי חריגה בראש: הוצאה שרצה פי 7 מהממוצע היומי, וקפיצת עלות של פי
4.2. מתחתם, 324 מתוך 667 סשנים אחרונים נושאים אות בזבוז, מפורט לפי סיבה.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**זה מראה לכם לאן הכסף הלך, בכל חלון זמן.**
$252.47 היום, $513.15 השבוע, $1,312.92 החודש, כל אחד עם הטוקנים שמאחוריו
וכמה מזה כבר מכוסה על ידי המנוי שלכם. מתחת לזה, כ-$1,128 לחודש מפורטים
כניתנים לשחזור וכ-$17,256 לחודש כבר נחסכו על ידי שימוש חוזר במטמון.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**זה מצייר איך הודעה הופכת לתשובה.**
תרשים הזרימה החי: אתם, הערוץ שבו היא הגיעה, השער (gateway), המודל
שעונה כרגע, וכל כלי שהוא פנה אליו. צמתים נדלקים כשהעבודה עוברת דרכם.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכשיר, בטבלה אחת.**
מה הוא מריץ, כמה הוא עולה ב-24 השעות האחרונות ולאורך חייו, מתי נראה
לאחרונה, מי הבעלים שלו, והאם מנוי מכסה את החשבון. 14 סוכנים כאן, 3
סשנים עובדים, 13 שקטים.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**זה מראה לאן הזמן והכסף של תור הלכו, כלי אחר כלי.**
תור אחד של סשן אמיתי: 11 כלים ב-11.2 דקות תמורת $1.16. כל קריאת Bash
וכל קריאת מודל מקבלת פס משלה על ציר הזמן, כך שהפקודה שרצה 4.1 דקות
והפקודה שרצה 226 מ״ש נבדלות במבט חטוף.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**זה מדרג את העבודה, לא רק את ההוצאה.**
ציון A השבוע: 54 משימות חזרו נקיות, 2 גסות עלו $48.57, והריצות עם
פעילות מועטה מדי לשיפוט הושארו מחוץ לציון במקום להיספר כזכיות. כל ריצה
גסה מקושרת לעקבה (trace) שלה.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**זה מראה למה חלון ההקשר ממשיך להתמלא.**
715K מתוך חלון של 1M טוקנים בתור האחרון, שיא של 83.3%, 4 קומפקציות
שכולן הופעלו יזומות ולא בעקבות גלישה, וניצול כל תור שמאחוריהן.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**הזיהוי פועל בלי שתגדירו שום דבר.**
הגלאים המובנים פעילים מההתקנה: סוכן השתתק, זרם הטלמטריה נפסק, קפיצת
עלות, פרץ טוקנים, שגיאות מטפסות, קפיצת שגיאות, סף תקציב, חתימת איום
תואמת, ממצא כלי אבטחה, שינוי בעמדת אבטחה. הכללים שלכם עצמכם אופציונליים
בנוסף.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**השהיית קריאה מסוכנת היא אופציונלית, ומגיעה כבויה.**
מחיקות רקורסיביות, דחיפות בכפייה (force push), sudo, סודות, התקנות
חבילות וקריאות יוצאות מקבלות כל אחת כלל שאפשר להפעיל. עד שתעשו זאת,
ClawMetry צופה ולא משנה דבר. ברגע שאחד מופעל, קריאות תואמות ממתינות
כאן (או בטלפון שלכם) לאישור או דחייה.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

עוד, לפי ריצה: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
