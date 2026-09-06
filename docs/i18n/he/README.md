<!-- i18n-src:88be2deff5d5 -->
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

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **30 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 26 נוספות. לוח מחוונים אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו את זה ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. אפס הגדרות. מזהה הכול אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900**. אפס הגדרות: הוא מוצא את סביבות הריצה של הסוכנים שכבר מותקנות אצלכם, קורא אותן לקריאה בלבד, ולא משנה דבר באופן שבו הן פועלות.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## עובד עם 30 סביבות ריצה של סוכנים

**חינם באפליקציית הקוד הפתוח:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**בתוכנית בתשלום:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

כל סביבת ריצה מקבלת את אותו לוח מחוונים. הריצו כמה סביבות במקביל, והמתג שבכותרת ימקד מחדש כל לשונית לאחת מהן.

בניתם סוכן משלכם על גבי SDK במקום זאת? המיירט (interceptor) עוקב גם אחרי קריאות ה-LLM שלו. ראו [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## מה תקבלו

- **הפעלות ותמלולים**: מה כל סוכן עשה, תור אחר תור, כולל שידור חוזר (replay)
- **עלות וטוקנים**: לפי סביבת ריצה, מודל, הפעלה ויום, עם דגלי חריגה
- **זרימה**: תרשים חי של הודעות הזזות דרך ערוצים, מודלים וכלים
- **מוח**: זרם אירועי ההיגיון וקריאות הכלים בזמן אמת
- **התפוצצות הקשר (context)**: ניצול חלון הקשר לפי ספק, קיצור (compaction) לעומת גלישה כפויה, וכן מפה לפי סביבת ריצה של מה שאנחנו *לא* יכולים לראות ([איך](docs/CONTEXT_BLOWOUT.md))
- **זיכרון וכישורים**: הקבצים והכישורים (skills) שכל סביבת ריצה טענה בפועל
- **בריאות ולוגים**: דיסק, זיכרון, שיעורי שגיאות, מגבלות קצב, זרם לוגים חי
- **התראות**: תקרות תקציב, קפיצות שגיאות, סוכן במצב לא מקוון, מנותב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **אישורים**: השהיית קריאות כלים מסוכנות *לפני* שהן רצות, ואישור מהטלפון שלכם ([איך](docs/APPROVALS.md))

## התפוצצות הקשר, ומה עולה לצפות בה

שתי שאלות ששווה לענות עליהן לפני שסומכים על כלי השוואת סוכנים כלשהו.

**איך זה מטפל בהתפוצצות חלון ההקשר בין סביבות ריצה שונות?**

אחוז ניצול הוא הגון בדיוק כמו המספר שהוא מחולק בו. ClawMetry קובע את גודל החלון לפי ספק, מתוך [טבלה שאפשר לקרוא ולשלוח אליה PR](clawmetry/context_windows.py), המכסה את Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ו-GLM. הוא לא מודד את כל 30 סביבות הריצה עם הסרגל של ספק אחד. זה חשוב: תור של 300K ב-GPT-5 שנמדד מול ה-200K של Anthropic נקרא כ-">100%, התפוצץ", כאשר בפועל הוא עומד על 75% מתוך ה-400K של GPT-5. אותו סרגל מסתיר תור של DeepSeek בגודל 130K שבאמת גלש, ומראה אותו כ-65% נוחים.

כל חלון מגיע עם המקור שלו: `model_table`, `explicit_marker`, `observed_floor`, או `default` כן ולא מזויף כאשר אנחנו לא מכירים את המודל. מד שנבנה על ניחוש לעולם לא מוצג עם אותה סמכות כמו מד שנבנה על בירור אמיתי.

ClawMetry יכול לראות אירועי קיצור (compaction) רק בחלק מסביבות הריצה. לכן `GET /api/context-coverage` מדווח, לפי סביבת ריצה, האם **אפס פירושו "רץ נקי" או "אנחנו עיוורים"**. `0` שבאמת פירושו עיוורון אומר זאת בפירוש. [פירוט מלא](docs/CONTEXT_BLOWOUT.md)

**כמה עולה ההתקנה של הכלים למדידה?**

| נתיב | מתווסף לסוכן שלכם | ברירת מחדל? |
|---|---|---|
| מעקב אחר קובצי הפעלה (Session-file tailing, כל 30 סביבות הריצה) | **0**. תהליך נפרד, ללא קוד ClawMetry בתוך הסוכן שלכם | פעיל |
| מיירט HTTP (`CLAWMETRY_INTERCEPT=1`) | **‎+0.44 מ"ש** לכל קריאת LLM, או 0.009% מקריאה בת 5 שניות | כבוי |
| שער hook לפני-כלי (מטמון חם) | **‎+44 מ"ש** לכל קריאת כלי מגודרת, מעל רצפת מפרש (interpreter) של 36 מ"ש | כבוי |
| פרוקסי אכיפה | **‎+9.7 מ"ש** לכל קריאת LLM | כבוי |

עלות מארח (host) הדימון: **2,762 אירועים/שנייה** קליטה, **710 בייטים/אירוע** על הדיסק (67.7MB לכל 100 אלף אירועים), וכ-**12% מליבה (core) אחת** באופן מתמשך על התקנה עמוסה. המספר האחרון הזה חורג מהתקציב שהצהרנו עליו של 5-10%, ולכן הוא מפורסם כבאג למרדף אחריו ולא הושמט מהעמוד.

נמדד על Apple M2 Pro עם `benchmarks/overhead.py`. הרתמה מריצה כל תנאי בתהליך נפרד, מחליפה את הסדר ביניהם, **ומסרבת להדפיס מספר כאשר הסבבים לא מסכימים על הסימן שלו**. הריצו אותו על המכונה שלכם תוך דקה:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

כל נתיב נמדד, כולל שערי ה-hook והפרוקסי לאכיפה, והרתמה רצה על Linux, macOS ו-Windows ב-CI. שני ממצאים ששווה להכיר: הפרוקסי עולה בערך פי שבעה יותר ב-Windows מאשר ב-Linux, והדימון מקיים כרגע כ-12% מליבה אחת, מעל התקציב שלנו של 5-10%. ה-JSON הגולמי, השיטה, ומה שעדיין לא נמדד נמצאים ב-[docs/OVERHEAD.md](docs/OVERHEAD.md).

## תמחור

| תוכנית | מה היא מכסה | מחיר |
|---|---|---|
| **חינם** | OpenClaw + NVIDIA NemoClaw + Goose, לוח מחוונים מלא, מקומי בלבד | $0 |
| **Starter** | כל שאר סביבות הריצה למעלה, תצוגת צי, סנכרון ענן | $9 לצומת (node) / חודש |
| **Pro** | Starter + בקרה והערכה: אישורים, מדיניות סיכון-כלים, הערכות (evals), זיהוי חריגות, מייעל עלות, ייצוא OTel, יומן ביקורת חסין-שיבוש | $19 לצומת (node) / חודש |

תוכניות שנתיות, Enterprise והמספרים העדכניים נמצאים ב-
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. מפתחות רישיון לאירוח עצמי פועלים ללא הענן (`clawmetry license`). הפיצול המדויק בין חינם לתשלום נמצא ב-[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## הנתונים שלכם נשארים על המכונה שלכם

ClawMetry קורא קובצי הפעלה ולוגים מקומיים. **שום נתוני הפעלה לא עוזבים את המכונה שלכם
אלא אם תריצו `clawmetry connect`** — לא הנחיות (prompts), תשובות, ארגומנטים של כלים, תוכן קבצים
או שורות לוג. כאשר אתם כן מתחברים, התמונה (snapshot) מוצפנת מקצה לקצה
עם מפתח שלעולם לא עוזב את המכונה שלכם, ומפוענחת בדפדפן שלכם. אם לצומת
אין מפתח, ההעלאה מדולגת במקום להישלח בטקסט גלוי, ואף
תגובת שרת לא יכולה לכבות את זה.

שני דברים כן פועלים כברירת מחדל לפני שתתחברו, שניהם ניתנים לביטול (opt-out) ואף אחד מהם
לא נושא נתוני הפעלה: פינג התקנה אנונימי ובדיקת גרסה מול
PyPI. התקנת ברירת מחדל גם מחפשת את כתובת ה-IP הציבורית שלכם פעם אחת עבור שורת באנר
של פתיחה. כל יעד, מה הוא נושא וכיצד לכבות אותו רשום ב-
[docs/EGRESS.md](docs/EGRESS.md); התקנות באירוח עצמי, מנותבות מחדש, ומבודדות רשת
לא מבצעות כלל קריאות יוצאות שאינן הכרחיות.

הפענוח מתבצע בדפדפן שלכם, בקוד שאנחנו מגישים לכם. זו הייתה
פעם הבטחה; עכשיו זה משהו שאפשר לבדוק. כל שורה שנוגעת במפתח שלכם
נמצאת בקובץ קריא אחד, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
שמסופק בתוך ה-wheel ומוגש כלשונו, מוצמד עם ערך גיבוב Subresource
Integrity. כדי לוודא שהדפדפן מריץ את מה שפרסמנו:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

מה שזה לא מוכיח: אנחנו מגישים את העמוד שטוען את הקובץ, כך שיכולנו
להגיש עמוד אחר. גיבובי Integrity מגנים עליכם מ-CDN שנפרץ,
לא מהספק עצמו. מה שאתם מרוויחים הוא שכל החלפה חייבת להיות
מכוונת, גלויה במקור העמוד, ושונה מהחפץ (artifact) ב-PyPI
שכל אחד יכול להוריד. אירוח עצמי או הישארות במצב מקומי בלבד מסירים את
התלות לחלוטין.

## התקנה

```bash
pip install clawmetry     # ואז: clawmetry
```

או שורת ההתקנה החד-פעמית: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

דורש Python 3.8+‎ ב-macOS, Linux או Windows, ולפחות סביבת ריצה אחת של סוכן על
אותה מכונה. הוראות Docker: [docs/DOCKER.md](docs/DOCKER.md).

או תנו לסוכן להתקין את זה בשבילכם. הכישור (skill) [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
מלמד את Claude Code, Codex, Cursor, Gemini CLI, Copilot או OpenCode
להתקין את ClawMetry, לדווח מה הסוכנים על המכונה עושים ומוציאים,
לעצור הפעלה אחת לפי בקשה, ולעכב קריאות כלים מסוכנות לאישור:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## תיעוד

| | |
|---|---|
| [תאימות סביבות ריצה](docs/compatibility.md) | מה כל מתאם (adapter) קורא, וכיצד להוסיף סביבת ריצה |
| [התפוצצות הקשר](docs/CONTEXT_BLOWOUT.md) | חלונות לפי ספק, קיצור לעומת גלישה, כיסוי לפי סביבת ריצה |
| [תקורה (Overhead)](docs/OVERHEAD.md) | מה עולה ההתקנה של כלי המדידה, נמדד, עם הרתמה לשחזור |
| [זכאויות](docs/ENTITLEMENTS.md) | חינם מול תשלום, מטריצת דרגות, CLI לרישיון |
| [אישורים ומדיניות](docs/APPROVALS.md) | שערור לפני ביצוע, ניקוד סיכון, אישורים מהטלפון |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ייצוא עקבות (traces) לכל מקום, קליטת OTLP מכל דבר |
| [הביאו את הסוכן שלכם](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain מקצה לקצה, עם דוגמאות שאפשר להריץ |
| [מעקב SDK](docs/SDK_TRACKING.md) | ייחוס עלויות עבור סוכנים שבניתם בעצמכם |
| [ערוצי צ'אט](docs/CHANNELS.md) | מתאמי הצ'אט המוצגים ב-Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | הגדרות NVIDIA NemoClaw בארגז חול |
| [Docker](docs/DOCKER.md) | תמונה, compose, הרכבות נפח (volume mounts) |
| [ארכיטקטורה](ARCHITECTURE.md) · [פיתוח](docs/DEVELOPMENT.md) | איך זה עובד מבפנים; הרצה מקוד המקור |
| [טלמטריה](docs/TELEMETRY.md) | הפינגים האנונימיים של ההתקנה ופתיחת שולחן העבודה, וכיצד לכבות אותם |

## צילומי מסך

כל מספר להלן מגיע ממכונה אמיתית אחת, לקריאה בלבד, ללא שום דבר מלאכותי.

**זה אומר לכם מתי משהו לא בסדר, לא רק מה קרה.**
שני באנרי חריגה בראש: הוצאה שרצה פי 7 מהממוצע היומי, וקפיצת
עלות של פי 4.2. מתחתם, 324 מתוך 667 הפעלות אחרונות נושאות
אות בזבוז, מפורט לפי סיבה.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**זה מראה לכם לאן הכסף הלך, בכל חלון זמן.**
$252.47 היום, $513.15 השבוע, $1,312.92 החודש, כל אחד עם הטוקנים
שמאחוריו וכמה מזה כבר מכוסה במנוי שלכם. מתחת לזה, בערך $1,128/חודש
המפורטים כניתנים להשבה ו-$17,256/חודש שכבר נחסכו על ידי
שימוש חוזר במטמון (cache).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**זה מצייר איך הודעה הופכת לתשובה.**
תרשים הזרימה החי: אתם, הערוץ שדרכו היא הגיעה, השער (gateway),
המודל שעונה כרגע, וכל כלי שהוא פנה אליו. צמתים נדלקים ככל שהעבודה
זזה דרכם.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**כל סוכן על המכונה, בטבלה אחת.**
מה הוא רץ, מה הוא עלה ב-24 השעות האחרונות ולאורך כל חייו, מתי
נראה לאחרונה, מי הבעלים שלו, והאם מנוי מכסה את
החשבון. 14 סוכנים כאן, 3 הפעלות עובדות, 13 שקטים.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**זה מראה לאן הזמן והכסף של תור הלכו, כלי אחר כלי.**
תור אחד בהפעלה אמיתית: 11 כלים ב-11.2 דקות תמורת $1.16. כל
קריאת Bash וכל קריאת מודל מקבלת פס משלה בציר הזמן, כך שהפקודה שרצה
4.1 דקות והפקודה שרצה 226 מ"ש נבדלות במבט חטוף.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**זה מדרג את העבודה, לא רק את ההוצאה.**
ציון A השבוע: 54 משימות חזרו נקיות, 2 גסות עלו $48.57, וההרצות
עם פעילות מעטה מדי כדי לשפוט אותן הושמטו מהציון במקום
להיספר כניצחונות. כל הרצה גסה מקושרת לעקבה (trace) שלה.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**זה מראה למה חלון ההקשר ממשיך להתמלא.**
715K מתוך חלון של 1M-טוקנים בתור האחרון, שיא של 83.3%, 4 קיצורים
(compactions) שכולם הופעלו באופן יזום ולא עקב גלישה, וניצול
כל תור שמאחוריו.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**הזיהוי פועל בלי שתגדירו כלום.**
הגלאים המובנים פעילים מההתקנה: הסוכן השתתק, זרם הטלמטריה
נעצר, קפיצת עלות, פרץ טוקנים, שגיאות מטפסות, קפיצת שגיאות, סף
תקציב, זוהתה חתימת איום, ממצא של כלי אבטחה, שינוי בעמדת
האבטחה. הכללים שלכם עצמכם אופציונליים בנוסף.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**עיכוב קריאה מסוכנת הוא אופציונלי, ומגיע כבוי.**
מחיקות רקורסיביות, דחיפות בכוח (force push), sudo, סודות, התקנות
חבילות וקריאות יוצאות מקבלות כל אחת כלל שאפשר להפעיל. עד שתפעילו,
ClawMetry צופה ולא משנה דבר. ברגע שאחד מופעל, קריאות
מתאימות ממתינות כאן (או בטלפון שלכם) לאישור או דחייה.

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
