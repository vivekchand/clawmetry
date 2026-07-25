<!-- i18n-src:8f42d460a973 -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**תראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **14 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 10 נוספות. לוח מחוונים אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו את זה ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד ←](docs/i18n/)

פקודה אחת. אפס תצורה. מזהה הכל אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900** וזהו, סיימתם.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 14 סביבות ריצה של סוכנים

ClawMetry התחיל כפתרון תצפית עבור OpenClaw, וכעת הוא מודד את **כל צי הסוכנים שלכם** בלוח מחוונים אחד, תוך זיהוי אוטומטי של כל סביבת ריצה שנמצאת על המכונה שלכם:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw ו-NemoClaw חינמיים באפליקציית הקוד הפתוח; שאר סביבות הריצה נפתחות עם ClawMetry Cloud או רישיון Pro בהתקנה עצמית. עברו בין סביבות ריצה מהכותרת העליונה וכל לשונית — עלות, טוקנים, כלים, עקבות — תיסוב מחדש לאותה סביבת ריצה. ראו את **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** לפירוט המדויק של החלוקה בין חינמי לתשלום, טבלת הרמות, מבנה ה-`/api/entitlement`, וכלי שורת הפקודה `clawmetry license`.

## מה מקבלים

- **Flow** — תרשים מונפש חי המציג הודעות זורמות דרך ערוצים, המוח, כלים וחזרה
- **Overview** — בדיקות תקינות, מפת חום של פעילות, מספרי סשנים, מידע על המודל
- **Usage** — מעקב אחר טוקנים ועלויות עם פירוטים יומיים/שבועיים/חודשיים
- **Sessions** — סשנים פעילים של הסוכן עם מודל, טוקנים, פעילות אחרונה
- **Crons** — משימות מתוזמנות עם סטטוס, ריצה הבאה, משך זמן
- **Logs** — הזרמת יומנים בזמן אמת בקידוד צבעים
- **Memory** — עיון בקבצי SOUL.md, MEMORY.md, AGENTS.md, הערות יומיות
- **Transcripts** — ממשק בועות צ'אט לקריאת היסטוריית סשנים
- **Alerts** — תקרות תקציב, טריגרים לשיעור שגיאות, זיהוי סוכן לא מקוון; מנתב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **Approvals** — חוסם מחיקות הרסניות, דחיפות כוח (force push), שינויים במסדי נתונים, sudo, התקנות חבילות, קריאות רשת מאחורי אישור בלחיצה אחת

## צילומי מסך

### 🧠 Brain — הזרמת אירועי סוכן חיה
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — שימוש בטוקנים וסיכום סשנים
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — הזנת קריאות כלים בזמן אמת
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — פירוט עלויות לפי מודל וסשן
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — דפדפן קבצי סביבת העבודה
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — עמדת אבטחה ויומן ביקורת
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — תקרות תקציב, טריגרים לשיעור שגיאות, webhooks ל-Slack / Discord / PagerDuty / אימייל
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — חסימת קריאות כלים מסוכנות מאחורי אישור ידני; כללי הגנה מבוססי מדיניות
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## התקנה

**פקודה אחת (מומלץ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**מהמקור:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## פיתוח Frontend גרסה 2

אפליקציית ה-React של גרסה 2 נמצאת בתיקייה `frontend/` ומוגשת בנתיב `/v2` כאשר
שרת ה-Flask מופעל עם v2 מאופשר.

השתמשו בשני מסופים בזמן הפיתוח:

```bash
# מסוף 1: Flask API/server בפורט :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# מסוף 2: שרת פיתוח Vite בפורט :5173
cd frontend
nvm use
npm ci
npm run dev
```

פתחו את `http://localhost:5173/v2/`. Vite מנתב בקשות `/api`
אל `http://localhost:8900`, כך שאפליקציית ה-React יכולה לתקשר עם שרת ה-Flask המקומי
ללא הגדרות CORS נוספות.

כדי לבנות את החבילה (bundle) שנשלחת עם חבילת ה-Python:

```bash
cd frontend
npm run build
```

חבילת הייצור נכתבת אל `clawmetry/static/v2/dist/`.

## תאימות סביבות ריצה / סוכנים

ClawMetry מתצפת על סביבות ריצה רבות של סוכני AI, לא רק על OpenClaw. כל סביבת ריצה שאינה OpenClaw כוללת מתאם קורא ייעודי שמתרגם את פורמט הסשנים המקורי שלה לצורות המאוחדות של ClawMetry; הדימון (daemon) קולט אותן לאותו מאגר DuckDB + תמונת מצב בענן, מתויגות בסביבת הריצה, ולשונית שחזור הסשן (Session replay) מציגה **מחליף סביבת ריצה** כאשר קיימת יותר מאחת. ראו את [`docs/compatibility.md`](docs/compatibility.md) לטבלה המלאה + מדריך להוספת סביבות ריצה, ואת [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) למבוא על משפחת OpenClaw.

| סביבת ריצה / סוכן | סטטוס | הערות |
|---|---|---|
| **OpenClaw** | ילידי (Native) | סביבת ריצה ייחוס, מזוהה אוטומטית |
| **PicoClaw** | מתאם בטא | JSONL שטוח של `providers.Message` (‏`~/.picoclaw/workspace/sessions`). תמלולים, מודל, קריאות כלים. |
| **NanoClaw** | מתאם בטא | SQLite לכל סשן (‏`data/v2-sessions`). תמלולים + ספירת הודעות. |
| **Hermes** | מתאם בטא | SQLite ‏`~/.hermes/state.db`. תמלולים, מודל, טוקנים/עלות. |
| **Claude Code** | מתאם בטא | JSONL ‏`~/.claude/projects/.../<id>.jsonl`. תמלולים, מודל, קריאות כלים + חשיבה, שימוש בטוקנים. |
| **Codex** | מתאם בטא | Rollout JSONL ‏`~/.codex/sessions/...`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Cursor** | מתאם בטא | SQLite ‏`state.vscdb`. תמלולי צ'אט/composer, מודל. |
| **Aider** | מתאם בטא | ‏`.aider.chat.history.md` לכל פרויקט. תמלולים, מודל, ספירת טוקנים. |
| **Goose** | מתאם בטא | SQLite ‏`~/.local/share/goose`. תמלולים, מודל, קריאות כלים, סך טוקנים. |
| **opencode** | מתאם בטא | SQLite ‏`~/.local/share/opencode`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Qwen Code** | מתאם בטא | JSONL ‏`~/.qwen/projects/.../chats`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Pi** | מתאם בטא | JSONL ‏`~/.pi/agent/sessions`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Deep Agents** | מתאם בטא | SQLite ‏`~/.deepagents/.state/sessions.db`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |

"מתאם בטא" פירושו ש-ClawMetry מספק קורא עבור הפורמט האמיתי על-הדיסק של אותה סביבת ריצה, שכל אחד מהם נבנה ואומת מול התקנה אמיתית על מכונה אמיתית (ראו `tests/fixtures/runtimes/<rt>/`). המתאמים הם לקריאה בלבד; כל אחד מהם הוגן לגבי מה שסביבת הריצה שלו בפועל שומרת (למשל, PicoClaw/NanoClaw/Cursor לא כותבים עלות טוקנים לדיסק). כאשר מספר סביבות ריצה פועלות על צומת אחד, מחליף סביבת הריצה מצמצם את תצוגת הסשנים לאחת בלבד לצלילה נקייה ומעמיקה.

## מעקב אחר כל סוכן SDK — ייחוס עלות מחוץ ללולאה (out-loop)

סביבות הריצה שלמעלה כולן כותבות סשנים לדיסק. **סוכן הייצור** שלכם — זה שבניתם על OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, או לולאת `httpx` פשוטה — לא. המיירט חסר-התצורה של ClawMetry עדיין לוכד את קריאות ה-LLM שלו (עלות, טוקנים, זמן תגובה, שגיאות) באמצעות תיקון קוף (monkey-patching) של `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

‏`set_source()`‏ (או משתנה הסביבה `CLAWMETRY_SOURCE=support-agent`) מתייג כל קריאה עם **מקור בעל שם**, כך שכל מוצר שאתם מריצים מופיע כשורה משלו, עצמאית וניתנת לייחוס עלות, בכרטיס **🔌 מקורות מחוץ ללולאה** בלוח המחוונים בלשונית Overview — קריאות, ספקים, זמן תגובה, שיעור שגיאות לכל סוכן. לא הוגדר מקור? הקריאות עדיין נעקבות, הכרטיס פשוט נשאר מוסתר.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

זוהי אותה שכבת נתונים שמתאמי סביבות הריצה מזינים (DuckDB ← תמונת מצב בענן), כך שמקורות מחוץ ללולאה מסתנכרנים ללוח המחוונים בענן בדיוק כמו כל דבר אחר, מוצפן מקצה לקצה.

## OpenTelemetry — נייטרלי מבחינת ספק, שלחו את העקבות שלכם לכל מקום

ClawMetry דובר **OpenTelemetry** בשני הכיוונים, תוך שימוש ב**מוסכמות הסמנטיקה של GenAI**, כך שעקבות הסוכן שלכם לעולם לא נעולות לכלי אחד.

**ייצוא** של כל סשן — קריאות LLM, כלים, תת-סוכנים, טוקנים, עלות — כספאנים (spans) של OTLP/HTTP GenAI לכל אספן (Datadog, Grafana, Honeycomb, או אספן OTel משלכם):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

כותרות אימות ומרווח סקר הם משתני סביבה אופציונליים:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**קליטה** — הקולט המובנה של OTLP מקבל עקבות ומדדים מכל דבר אחר בנתיבים `/v1/traces` ו-`/v1/metrics` (‏`pip install clawmetry[otel]` לקליטת protobuf).

אתם מקבלים את לוח המחוונים של ClawMetry, חסר-התצורה ומבוסס-מקומי, **וגם** את הנתונים שלכם בכל backend שהצוות שלכם כבר מריץ, ללא נעילה, ללא סוכן שני להתקין.

## תצורה

רוב האנשים לא צריכים שום תצורה. ClawMetry מזהה אוטומטית את סביבת העבודה, היומנים, הסשנים וה-crons שלכם.

אם אתם כן צריכים להתאים אישית:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

כל האפשרויות: `clawmetry --help`

## ערוצים נתמכים

ClawMetry מציג פעילות חיה עבור כל ערוץ OpenClaw שהגדרתם. רק ערוצים שמוגדרים בפועל ב-`openclaw.json` שלכם מופיעים בתרשים Flow, ערוצים שלא הוגדרו מוסתרים אוטומטית.

לחצו על כל צומת ערוץ ב-Flow כדי לראות תצוגת בועות צ'אט חיה עם ספירת הודעות נכנסות/יוצאות.

| ערוץ | סטטוס | חלון קופץ חי | הערות |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ מלא | ✅ | הודעות, סטטיסטיקות, רענון כל 10 שניות |
| 💬 **iMessage** | ✅ מלא | ✅ | קורא ישירות מ-`~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ מלא | ✅ | דרך WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ מלא | ✅ | דרך signal-cli |
| 🟣 **Discord** | ✅ מלא | ✅ | זיהוי גילדה + ערוץ |
| 🟪 **Slack** | ✅ מלא | ✅ | זיהוי סביבת עבודה + ערוץ |
| 🌐 **Webchat** | ✅ מלא | ✅ | סשנים מובנים של ממשק אינטרנט |
| 📡 **IRC** | ✅ מלא | ✅ | ממשק בועות בסגנון טרמינל |
| 🍏 **BlueBubbles** | ✅ מלא | ✅ | iMessage דרך BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ מלא | ✅ | דרך webhooks של Chat API |
| 🟣 **MS Teams** | ✅ מלא | ✅ | דרך תוסף בוט Teams |
| 🔷 **Mattermost** | ✅ מלא | ✅ | צ'אט צוות בהתקנה עצמית |
| 🟩 **Matrix** | ✅ מלא | ✅ | מבוזר, תמיכה ב-E2EE |
| 🟢 **LINE** | ✅ מלא | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ מלא | ✅ | הודעות פרטיות מבוזרות NIP-04 |
| 🟣 **Twitch** | ✅ מלא | ✅ | צ'אט דרך חיבור IRC |
| 🔷 **Feishu/Lark** | ✅ מלא | ✅ | מנוי אירועים דרך WebSocket |
| 🔵 **Zalo** | ✅ מלא | ✅ | Zalo Bot API |

> **זיהוי אוטומטי:** ClawMetry קורא את `~/.openclaw/openclaw.json` ומציג רק את הערוצים שהגדרתם בפועל. אין צורך בהגדרה ידנית.

## פריסה עם Docker

רוצים להריץ את ClawMetry בקונטיינר? אין בעיה! 🐳

**התחלה מהירה עם Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**דוגמת Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **הערה:** בעת הרצה ב-Docker, עגנו (mount) את תיקיות הנתונים + היומנים של הסוכן שלכם (למשל `~/.openclaw`, `~/.claude`, `~/.codex`) כך ש-ClawMetry יוכל לזהות אוטומטית את ההגדרה שלכם.

## דרישות

- Python 3.8+
- Flask (מותקן אוטומטית דרך pip)
- סביבת ריצה של סוכן AI על אותה מכונה: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, או Deep Agents (או כרכים מעוגנים עבור Docker)
- Linux או macOS

## תמיכה ב-NemoClaw / OpenShell

ClawMetry מזהה אוטומטית את [NemoClaw](https://github.com/NVIDIA/NemoClaw), עטיפת האבטחה הארגונית של NVIDIA עבור OpenClaw, שמריצה סוכנים בתוך קונטיינרים מבודדים (sandboxed) של OpenShell.

ברוב המקרים אין צורך בתצורה נוספת. הדימון של הסנכרון מגלה אוטומטית קבצי סשן בין אם הם נמצאים ב-`~/.openclaw/` על המארח (host) ובין אם בתוך קונטיינר OpenShell.

### כיצד זה עובד

ClawMetry מזהה את NemoClaw בשתי דרכים:

1. **זיהוי בינארי** — בודק את קיום שורת הפקודה `nemoclaw` ומריץ `nemoclaw status` לקבלת מידע על ה-sandbox
2. **זיהוי קונטיינר** — סורק קונטיינרי Docker פעילים בחיפוש אחר תמונות `openshell`, `nemoclaw`, או `ghcr.io/nvidia/`, ואז קורא סשנים דרך כרכים מעוגנים או `docker cp`

קבצי סשן שמסונכרנים מקונטיינרים של NemoClaw מתויגים עם `runtime=nemoclaw` ומטא-נתוני `container_id` בלוח המחוונים בענן, כך שתוכלו להבחין ביניהם לבין סשני OpenClaw רגילים במבט חטוף.

### הגדרה מומלצת: דימון הסנכרון על המארח (HOST)

לחוויה הטובה ביותר, הריצו את דימון הסנכרון של ClawMetry על **מכונת המארח** (לא בתוך ה-sandbox). כך נמנעים ממגבלות מדיניות הרשת של NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

דימון הסנכרון ימצא אוטומטית סשנים בתוך כל קונטיינר OpenShell פעיל.

### אופציונלי: שם sandbox מפורש

אם הזיהוי האוטומטי לא עובד, כוונו את ClawMetry אל ה-sandbox הנכון:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### הרצה בתוך ה-sandbox (מתקדם)

אם אתם חייבים להריץ את דימון הסנכרון **בתוך** ה-sandbox של OpenShell, הוסיפו את כלל היציאה (egress) הבא למדיניות הרשת של NemoClaw כדי שיוכל להגיע ל-API הקליטה של ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

החילו עם:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### פורטים ונקודות קצה

| נקודת קצה | פורט | פרוטוקול | נדרש |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | כן (דימון הסנכרון ← ענן) |
| `localhost:8900` | 8900 | HTTP | כן (ממשק לוח המחוונים המקומי) |
| שקע Docker (`/var/run/docker.sock`) | — | שקע Unix | לגילוי סשנים בקונטיינרים |

דימון הסנכרון מבצע קריאות HTTPS יוצאות בלבד אל `ingest.clawmetry.com`. אין צורך בפורטים נכנסים.

---

## פריסה בענן

ראו את **[מדריך בדיקת הענן](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** עבור מנהרות SSH, פרוקסי הפוך (reverse proxy), ו-Docker.

## בדיקות

פרויקט זה נבדק עם BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## טלמטריה

ClawMetry שולח פינג אנונימי יחיד של "הרצה ראשונה" אל
`https://app.clawmetry.com/api/install` בפעם הראשונה שאתם מריצים את
`clawmetry` CLI על מכונה חדשה. אנחנו משתמשים בזה כדי לספור התקנות (מדד השיווק
היחיד שיש לנו עבור פרויקט קוד פתוח) וכדי ללמוד אילו מסגרות סוכנים המשתמשים שלנו התקינו.

**בדיוק POST אחד להתקנה**, המכיל:

| שדה | דוגמה | למה |
|---|---|---|
| `install_id` | UUID אקראי המאוחסן ב-`~/.clawmetry/install_id` | מניעת כפילויות; לא מקושר לאימייל או ל-api_key שלכם |
| `version` | `0.12.167` | אילו גרסאות נמצאות בשטח |
| `os` / `os_version` | `Darwin` / `25.3.0` | סדרי עדיפויות לתמיכה בפלטפורמות |
| `python` | `3.11.15` | מטריצת תמיכה בגרסאות Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | עם אילו סוכנים עלינו להשתלב הבאים |
| `is_ci` / `ci_provider` | `true` / `github_actions` | הפרדה בין התקנות אנוש לרעש CI |

**מה אנחנו לא שולחים**: כתובת IP (הענן גוזר את קוד המדינה בצד השרת
מתוך הבקשה, ואז משליך את ה-IP), שם מארח, שם משתמש, נתיב סביבת עבודה, תוכן קבצים, ה-api_key שלכם, האימייל שלכם, כל דבר אישי או ספציפי לסביבת העבודה. מטען התקשורת ניתן לביקורת ב-
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**ביטול הסכמה** (כל אחת מהאפשרויות הבאות משביתה זאת לצמיתות):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

כשל רשת כאן לעולם לא חוסם את הרצת `clawmetry`, הפינג הוא ירי-ושכח
בשרשור דימון עם תפוגת זמן של 3 שניות.

## היסטוריית כוכבים

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## רישיון

MIT

---

<p align="center">
  <strong>🦞 תראו את הסוכן שלכם חושב</strong><br>
  <sub>נבנה על ידי <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · חלק ממערכת <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
