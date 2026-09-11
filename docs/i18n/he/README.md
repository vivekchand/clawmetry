<!-- i18n-src:12b97259721e -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**סוכן יכול לבצע מאה קריאות כלים בלי להתקדם.** ClawMetry
קורא את קובצי הסשן שסוכני הקידוד שלך כבר כותבים, ומרכז את ציר הזמן,
קריאות הכלים וכל נתוני הטוקנים והעלות שהריצה חושפת לתצוגה אחת —
כדי שתוכל להבחין בין ריצה ארוכה שעובדת לבין אחת שנתקעה.

עובד עם **31 סביבות הרצה של סוכני AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw ועוד 27. לוח בקרה אחד לכל צי הסוכנים שלך. ([הרשימה המלאה](SUPPORTED_RUNTIMES.txt), נוצרת מהקטלוג.)

> 🌐 **קרא בשפה זו:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. בלי הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. בלי הגדרות: הכלי מוצא את סביבות ההרצה
שכבר יש לך, קורא אותן לקריאה בלבד, ולא משנה דבר באופן שבו הן פועלות.

![לוח הבקרה של ClawMetry: כל סביבת הרצה של סוכן AI במכונה אחת עם עלות ל-24 שעות ועלות מצטברת לכל סוכן](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## לפני ההתקנה

| | |
|---|---|
| **מה זה עושה** | קורא את קובצי הסשן והיומנים שהסוכנים שלך כבר כותבים. בלי SDK, בלי שינוי קוד, בלי אינסטרומנטציה באפליקציה שלך. |
| **מה תראה** | ציר זמן של הסשן, שידור חוזר של כל קריאת כלי, פירוט טוקנים ועלות, ואותות מסלול (לולאות, כשלים חוזרים) — לכל סביבת הרצה. |
| **מה חינם** | `pip install clawmetry` קורא את **OpenClaw, NVIDIA NemoClaw ו-Goose** בלי חשבון, בלי מפתח ובלי קריאת רשת. שאר ה-27 — Claude Code, Codex, Cursor והשאר — נקראים על ידי הרכיב הנלווה סגור-הקוד `clawmetry-pro`, שמגיע עם תקופת הניסיון של 7 ימים או תוכנית בתשלום — ראו [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) לפילוח המדויק. |
| **איך מתחילים** | `pip install clawmetry && clawmetry`, ואז פתחו את localhost:8900. אין עדיין סוכנים על המכונה הזו? `clawmetry --sample` נפתח עם שלושה סשנים סינתטיים מתויגים. |
| **מה יוצא מהמכונה שלך** | שום נתוני סשן, אלא אם תריצו `clawmetry connect`. שני דברים כן רצים כברירת מחדל, שניהם ניתנים לביטול ואף אחד מהם לא נושא תוכן סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI. כל יעד רשום ב-[docs/EGRESS.md](docs/EGRESS.md), שנבנה מחדש מלכידת תעבורת רשת ולא מקריאת הערות בקוד. |

שתי מגבלות שכדאי להכיר לפני שבוחנים את הפלט: סביבות הרצה חושפות נתונים שונים
מאוד (חלקן לא מפרסמות עלות כלל — [הטבלה](docs/compatibility.md)
מפרטת מי, לכל סביבת הרצה), ותצפית על פעולה היא לא אותו הדבר כמו יכולת
לחסום אותה ([אילו בקרות אמיתיות, לכל סביבת הרצה](docs/APPROVALS.md)).


## עובד עם 31 סביבות הרצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל סביבת הרצה מקבלת את אותו לוח בקרה. הריצו כמה במקביל ומחליף הכותרת
ישנה את ההיקף של כל לשונית לאחת מהן.

בניתם סוכן משלכם על גבי SDK במקום? המיירט עוקב גם אחרי קריאות ה-LLM שלו.
ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה מקבלים

- **סשנים ותמלולים**: מה כל סוכן עשה, תור אחרי תור, עם שידור חוזר
- **עלות וטוקנים**: לכל סביבת הרצה, מודל, סשן ויום, עם דגלי חריגה
- **זרימה (Flow)**: תרשים חי של הודעות שנעות בין ערוצים, מודלים וכלים
- **מוח (Brain)**: זרם אירועי החשיבה וקריאות הכלים בזמן אמת
- **התפוצצות הקשר (Context blowout)**: ניצול חלון בגודל מותאם לכל ספק, כיווץ (compaction) מול גלישה מאולצת, וגם מפה לכל סביבת הרצה של מה שאנחנו *לא* יכולים לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים (Memory & skills)**: הקבצים והכישורים שכל סביבת הרצה בפועל טענה
- **בריאות ויומנים**: דיסק, זיכרון, שיעורי שגיאות, הגבלות קצב, זרם יומן חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן לא זמין, מנותב ל-Slack, Discord, PagerDuty, Telegram, Email
- **אישורים**: השהיית קריאות כלים מסוכנות *לפני* שהן רצות ואישור מהטלפון שלך ([איך](docs/APPROVALS.md))

## התפוצצות הקשר, ומה עולה לעקוב אחריה

שתי שאלות שכדאי לענות עליהן לפני שסומכים על כלי השוואת סוכנים כלשהו.

**איך זה מטפל בהתפוצצות חלון ההקשר בין סביבות הרצה שונות?**

אחוז ניצול הוא כנה רק כמו המכנה שהוא מחולק בו. ClawMetry
קובע את גודל החלון לכל ספק מ[טבלה שאפשר לקרוא ולשלוח אליה PR](clawmetry/context_windows.py),
המכסה את Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ו-GLM. הוא לא מודד את כל 31
סביבות ההרצה עם סרגל של ספק אחד. זה משנה: תור של 300K טוקנים ב-GPT-5
שנמדד מול ה-200K של Anthropic נקרא ">100%, התפוצץ" כאשר בפועל מדובר ב-75% מתוך
ה-400K של GPT-5. אותו סרגל מסתיר תור DeepSeek שהתפוצץ בפועל ב-130K
כמו 65% נוחים.

כל חלון מגיע עם המקור שלו: `model_table`, `explicit_marker`,
`observed_floor`, או `default` כנה כשלא ידוע לנו המודל. מד שנבנה
על ניחוש לעולם לא מוצג עם אותה סמכות כמו כזה שנבנה על בירור מדויק.

ClawMetry יכול לראות אירועי כיווץ (compaction) רק בחלק מסביבות ההרצה. אז
`GET /api/context-coverage` מדווח, לכל סביבת הרצה, האם **אפס פירושו
"רץ נקי" או "אנחנו עיוורים"**. `0` שבאמת פירושו עיוור אומר את זה בפירוש.
[פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**מה האינסטרומנטציה עולה?**

| נתיב | נוסף לסוכן שלך | ברירת מחדל? |
|---|---|---|
| מעקב אחר קובצי סשן (כל 31 סביבות ההרצה) | **0**. תהליך נפרד, בלי קוד ClawMetry בסוכן שלך | פעיל |
| מיירט HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 מ"ש** לכל קריאת LLM, כלומר 0.009% מקריאה של 5 שניות | כבוי |
| שער hook לפני הפעלת כלי (מטמון חם) | **+44 מ"ש** לכל קריאת כלי משוערת, מעל רצפת מפרש של 36 מ"ש | כבוי |
| פרוקסי אכיפה | **+9.7 מ"ש** לכל קריאת LLM | כבוי |

עלות מארח הדימון: **2,762 אירועים/שנייה** קליטה, **710 בייטים/אירוע** על הדיסק
(67.7 מגה-בייט לכל 100 אלף אירועים), ו-**כ-12% מליבה אחת** בעומס קבוע
בהתקנה עמוסה. המספר האחרון הזה חורג מתקציב היעד שלנו, 5-10%, ולכן הוא
מפורסם כבאג לרדוף אחריו ולא מוסתר מהעמוד.

נמדד על Apple M2 Pro עם `benchmarks/overhead.py`. הרתמה מריצה
כל תרחיש בתהליך נפרד, מחליפה את הסדר ביניהם, ו**מסרבת להדפיס מספר
כאשר הסבבים חלוקים בסימן שלו**. הריצו אותה על המכונה שלכם תוך דקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook ופרוקסי האכיפה,
והרתמה רצה בלינוקס, macOS ו-Windows ב-CI. שתי תוצאות שכדאי להכיר: הפרוקסי
עולה בערך פי שבעה יותר ב-Windows מאשר בלינוקס, והדימון כרגע שומר על
כ-12% מליבה אחת, מעל תקציב היעד שלנו 5-10%. ה-JSON הגולמי, השיטה, ומה
שעדיין לא נמדד נמצאים ב-[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא כוללת | מחיר |
|---|---|---|
| **חינם (Free)** | OpenClaw + NVIDIA NemoClaw + Goose, לוח בקרה מלא, מקומי בלבד | 0$ |
| **Starter** | כל סביבת הרצה אחרת שלמעלה, תצוגת צי, סנכרון ענן | 9$ לנוד / חודש |
| **Pro** | Starter + בקרה והערכה: אישורים, מדיניות סיכון לכלים, הערכות (evals), זיהוי חריגות, אופטימיזציית עלות, ייצוא OTel, יומן ביקורת עמיד בפני שיבוש | 19$ לנוד / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון
לאירוח עצמי עובדים בלי הענן (`clawmetry license`). הפילוח המדויק בין חינם
לתשלום נמצא ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלך נשארים במכונה שלך

ClawMetry קורא קובצי סשן ויומנים מקומיים. **שום נתון סשן לא יוצא מהמכונה שלך
אלא אם תריצו `clawmetry connect`** — לא פרומפטים, תגובות, ארגומנטים של כלים,
תוכן קבצים או שורות יומן. כאשר אתם כן מתחברים, התמונה הנשלחת מוצפנת מקצה
לקצה עם מפתח שלעולם לא עוזב את המכונה שלכם, ומפוענחת בדפדפן שלכם. אם לנוד
אין מפתח, ההעלאה מדולגת במקום להישלח בגלוי, ואף תגובת שרת לא יכולה לכבות
את זה.

שני דברים כן רצים כברירת מחדל לפני שמתחברים, שניהם ניתנים לביטול ואף אחד
מהם לא נושא נתוני סשן: פינג התקנה אנונימי ובדיקת גרסה מול PyPI. התקנת
ברירת מחדל גם מבררת את כתובת ה-IP הציבורית שלכם פעם אחת לצורך שורת באנר
פתיחה. כל יעד, מה הוא נושא ואיך לכבות אותו רשום ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות לאירוח עצמי, מנותבות מחדש ומבודדות
רשת (air-gapped) לא מבצעות שום קריאה יוצאת אופציונלית כלל.

הפענוח קורה בדפדפן שלכם, בקוד שאנחנו מגישים לכם. זו הייתה פעם הבטחה;
עכשיו זה משהו שאפשר לבדוק. כל שורה שנוגעת במפתח שלכם נמצאת בקובץ קריא אחד,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שנשלח בתוך ה-wheel ומוגש כלשונו, מוצמד עם hash של שלמות משאב משנה
(Subresource Integrity). כדי לאשר שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את העמוד שטוען את הקובץ, אז יכולנו להגיש
עמוד אחר. hash-ים של שלמות (Integrity) מגנים עליכם מ-CDN שנפרץ,
לא מהספק עצמו. מה שאתם מרוויחים הוא שכל החלפה חייבת להיות מכוונת,
גלויה במקור העמוד, ושונה מהארטיפקט ב-PyPI שכל אחד יכול להוריד. אירוח
עצמי או הישארות מקומית בלבד מסירים את התלות לגמרי.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או השורה האחת: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+ על macOS, לינוקס או Windows, ולפחות סביבת הרצה של סוכן אחת
על אותה מכונה. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

או תנו לסוכן להגדיר את זה בשבילכם. הכישור [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
מלמד את Claude Code, Codex, Cursor, Gemini CLI, Copilot או OpenCode
להתקין את ClawMetry, לדווח מה הסוכנים על המכונה עושים ומוציאים,
לעצור סשן לפי בקשה, ולהחזיק קריאות כלים מסוכנות לאישור:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## מסמכים

| | |
|---|---|
| [תאימות סביבות הרצה](docs/compatibility.md) | מה כל מתאם קורא, ואיך מוסיפים סביבת הרצה |
| [התפוצצות הקשר](docs/CONTEXT_BLOWOUT.md) | חלונות לכל ספק, כיווץ מול גלישה, כיסוי לכל סביבת הרצה |
| [תקורה (Overhead)](docs/OVERHEAD.md) | מה האינסטרומנטציה עולה, נמדד, עם הרתמה לשחזור |
| [זכאויות (Entitlements)](docs/ENTITLEMENTS.md) | חינם מול תשלום, טבלת רמות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | חסימה טרם ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא עקבות (traces) לכל מקום, קליטת OTLP מכל מקור |
| [הביאו את הסוכן שלכם (Bring your own agent)](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain מקצה לקצה, עם דוגמאות שאפשר להריץ |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלות לסוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw במארז חסום (sandboxed) |
| [Docker](docs/DOCKER.md) | Image, compose, הרכבות של volume |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד בפנים; הרצה מהמקור |
| [טלמטריה](docs/TELEMETRY.md) | פינגי ההתקנה האנונימית ופתיחת שולחן העבודה, ואיך לכבות אותם |

## צילומי מסך

כל מספר למטה מגיע ממכונה אמיתית אחת, לקריאה בלבד, בלי שום דבר שנטע מראש.

**זה אומר לך מתי משהו לא בסדר, לא רק מה קרה.**
שני באנרי חריגה למעלה: הוצאה שרצה פי 7 מהממוצע היומי, וקפיצת עלות
פי 4.2. מתחתיהם, 324 מתוך 667 סשנים אחרונים נושאים אות בזבוז,
מפורט לפי סיבה.

![סקירה כללית: באנרי חריגת הוצאה וקפיצת עלות מעל עבודת סוכן חיה](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**זה מראה לך לאן הכסף הלך, בכל חלון זמן.**
252.47$ היום, 513.15$ השבוע, 1,312.92$ החודש, כל אחד עם הטוקנים
שמאחוריו וכמה מזה כבר מכוסה על ידי המנוי שלכם. מתחת לזה, בערך 1,128$/חודש
מפורטים כניתנים להשבה ו-17,256$/חודש שכבר נחסכו על ידי שימוש חוזר במטמון (cache).

![עלות: היום, השבוע והחודש, עם ציון יעילות ורעיונות חיסכון מפורטים](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**זה מצייר איך הודעה הופכת לתשובה.**
תרשים הזרימה החי: אתם, הערוץ שממנו זה הגיע, השער (gateway), המודל
שעונה עכשיו, וכל כלי שהוא פנה אליו. צמתים נדלקים ככל שהעבודה זזה דרכם.

![זרימה: תרשים חי מכם דרך השער אל המודל והכלים שלו](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכונה, בטבלה אחת.**
מה הוא מריץ, מה הוא עולה ב-24 השעות האחרונות ולאורך חייו, מתי הוא
נראה לאחרונה, מי הבעלים שלו, והאם מנוי מכסה את החשבון. 14 סוכנים כאן,
3 סשנים עובדים, 13 שקטים.

![סוכנים: כל סביבת הרצה על המכונה עם עלות, בעלים, זמן הופעה אחרון ועבודה נוכחית](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**זה מראה לאן הזמן והכסף של תור הלכו, כלי אחר כלי.**
תור אחד של סשן אמיתי: 11 כלים ב-11.2 דקות תמורת 1.16$. כל קריאת
Bash וקריאת מודל מקבלת פס משלה על ציר הזמן, כך שהפקודה שרצה
4.1 דקות והפקודה שרצה 226 מ"ש נבדלות במבט חטוף.

![סשנים: תור אחד של סוכן על ציר זמן, כל קריאת כלי עם משך זמן משלה ועלות התור](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**זה מדרג את העבודה, לא רק את ההוצאה.**
ציון A השבוע: 54 משימות חזרו נקיות, 2 קשות עלו 48.57$, וריצות
עם פעילות מועטה מדי להערכה מוחרגות מהציון במקום להיספר כניצחונות.
כל ריצה קשה מקושרת לעקבה שלה.

![איכות: כרטיס דוח לשבוע עם הריצות הקשות ומה הן עלו](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**זה מראה למה חלון ההקשר ממשיך להתמלא.**
715K מתוך חלון של 1M טוקנים בתור האחרון, שיא של 83.3%, 4 כיווצים
(compactions) שכולם הופעלו יזומה ולא עקב גלישה, וניצול כל תור מאחוריו.

![שימוש בהקשר: ניצול חלון לכל תור, אירועי כיווץ וטוקנים שהוחזרו](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**הזיהוי רץ בלי שתגדירו כלום.**
המזהים המובנים פעילים מההתקנה: הסוכן השתתק, זרימת הטלמטריה
נעצרה, קפיצת עלות, פרץ טוקנים, שגיאות מטפסות, קפיצת שגיאות, סף תקציב,
חתימת איום זוהתה, ממצא של כלי אבטחה, שינוי בעמדת האבטחה. הכללים שלכם
עצמכם אופציונליים בנוסף.

![התראות: מזהים מובנים בתוספת כללים מותאמים אישית אופציונליים](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**החזקת קריאה מסוכנת היא אופציונלית, ומגיעה כבויה.**
מחיקות רקורסיביות, פוש בכפייה (force push), sudo, סודות, התקנות
חבילות וקריאות יוצאות מקבלות כל אחת כלל שאפשר להפעיל. עד שתעשו זאת,
ClawMetry רק צופה ולא משנה כלום. ברגע שאחד מופעל, קריאות תואמות
ממתינות כאן (או בטלפון שלכם) לאישור או דחייה.

![אישורים: כללי הגנה לקריאות כלים מסוכנות, כולם כבויים עד שתפעילו אותם](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

עוד, לכל סביבת הרצה: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## הכרה (Recognition)

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
