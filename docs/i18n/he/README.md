<!-- i18n-src:8252f6b1d31d -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **14 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 10 נוספות. לוח מחוונים אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד ←](docs/i18n/)

פקודה אחת. ללא הגדרות. מזהה הכל אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900** וזהו, סיימתם.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 14 סביבות ריצה של סוכנים

ClawMetry התחיל כתצפיתיות עבור OpenClaw, וכעת מודד את **כל צי הסוכנים** שלכם בלוח מחוונים אחד, ומזהה אוטומטית כל סביבת ריצה במחשב שלכם:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw ו-NemoClaw חינמיים באפליקציית הקוד הפתוח; שאר סביבות הריצה נדלקות עם ClawMetry Cloud או רישיון Pro בהתקנה עצמית. החליפו סביבת ריצה מהכותרת העליונה, וכל לשונית - עלות, טוקנים, כלים, מעקבים - תיוצג מחדש בהתאם לסביבת הריצה הזו. ראו את **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** לפירוט המדויק של החלוקה בין חינמי לתשלום, טבלת הרמות, מבנה ה-`/api/entitlement`, וכלי שורת הפקודה `clawmetry license`.

## מה תקבלו

- **Flow** - דיאגרמה מונפשת חיה המציגה הודעות זורמות דרך ערוצים, המוח, כלים, וחזרה
- **Overview** - בדיקות תקינות, מפת חום של פעילות, מספרי הפעלות, מידע על מודלים
- **Usage** - מעקב טוקנים ועלויות עם פילוחים יומיים/שבועיים/חודשיים
- **Sessions** - הפעלות סוכן פעילות עם מודל, טוקנים, פעילות אחרונה
- **Crons** - עבודות מתוזמנות עם סטטוס, ריצה הבאה, משך זמן
- **Logs** - הזרמת יומנים בזמן אמת עם קידוד צבעים
- **Memory** - עיון בקבצי SOUL.md, MEMORY.md, AGENTS.md, הערות יומיות
- **Transcripts** - ממשק בועות צ'אט לקריאת היסטוריית הפעלות
- **Alerts** - תקרות תקציב, טריגרים לשיעור שגיאות, זיהוי סוכן לא מקוון; ניתוב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **Approvals** - חסימת מחיקות הרסניות, force pushes, שינויי מסדי נתונים, sudo, התקנות חבילות, קריאות רשת מאחורי אישור בלחיצה אחת

## צילומי מסך

### 🧠 Brain - זרם אירועי סוכן חי
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - שימוש בטוקנים וסיכום הפעלות
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - הזנת קריאות כלים בזמן אמת
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - פירוט עלויות לפי מודל והפעלה
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - דפדפן קבצי סביבת עבודה
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - עמדת אבטחה ויומן ביקורת
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - תקרות תקציב, טריגרים לשיעור שגיאות, webhooks ל-Slack / Discord / PagerDuty / אימייל
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - חסימת קריאות כלים מסוכנות מאחורי אישור ידני; חוקי הגנה מבוססי מדיניות
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**חסימה טרם-ביצוע עבור Claude Code** - פקודה אחת מתקינה
hook מסוג PreToolUse שעוצר קריאות כלים תואמות *לפני* שהן רצות וממתין
להחלטה שלכם (הקשה אחת מהטלפון עם
[התראות push בענן](https://app.clawmetry.com/push) מופעלות):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

דחייה חוסמת רק את קריאת הכלי הבודדת ההיא - הסוכן שומר את ההפעלה שלו ויכול
לנסות גישה אחרת. אישור מהטלפון מדלג על שאילת ההרשאה של Claude Code עצמה
(כבר עניתם). כלים שלא תואמים עולים כ-40ms ו
נופלים חזרה לזרימת ההרשאות הרגילה של Claude Code. תקבלו גם התראת push לטלפון כאשר
Claude Code עצמו ממתין לכם (התראות `permission_prompt` /
`idle_prompt`).

## התקנה

**שורת פקודה אחת (מומלץ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**מקוד המקור:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## פיתוח Frontend גרסה 2

אפליקציית React v2 ממוקמת ב-`frontend/` ומוגשת בכתובת `/v2` כאשר
שרת Flask מופעל עם v2 מופעל.

השתמשו בשני מסופים בזמן הפיתוח:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

פתחו את `http://localhost:5173/v2/`. Vite מעביר בקשות `/api` אל
`http://localhost:8900`, כך שאפליקציית React יכולה לתקשר עם שרת Flask המקומי
ללא הגדרת CORS נוספת.

כדי לבנות את החבילה שמסופקת עם חבילת ה-Python:

```bash
cd frontend
npm run build
```

חבילת הייצור נכתבת ל-`clawmetry/static/v2/dist/`.

## תאימות סביבות ריצה / סוכנים

ClawMetry עוקב אחר סביבות ריצה רבות של סוכני AI, לא רק OpenClaw. כל סביבת ריצה שאינה OpenClaw מספקת מתאם קורא ייעודי שמתרגם את פורמט ההפעלה הטבעי שלה לצורות המאוחדות של ClawMetry; הדימון מכניס אותן לאותו מאגר DuckDB + תמונת מצב בענן, מתויגות בסביבת הריצה, ולשונית שידור חוזר ההפעלה מציגה **מחליף סביבות ריצה** כאשר קיימת יותר מאחת. ראו את [`docs/compatibility.md`](docs/compatibility.md) לטבלה המלאה + מדריך להוספת סביבות ריצה, ואת [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) למבוא למשפחת OpenClaw.

| סביבת ריצה / סוכן | סטטוס | הערות |
|---|---|---|
| **OpenClaw** | טבעי | סביבת ריצה עיקרית, מזוהה אוטומטית |
| **PicoClaw** | מתאם בטא | JSONL שטוח מסוג `providers.Message` (`~/.picoclaw/workspace/sessions`). תמלולים, מודל, קריאות כלים. |
| **NanoClaw** | מתאם בטא | SQLite לכל הפעלה (`data/v2-sessions`). תמלולים + ספירת הודעות. |
| **Hermes** | מתאם בטא | SQLite ב-`~/.hermes/state.db`. תמלולים, מודל, טוקנים/עלות. |
| **Claude Code** | מתאם בטא | JSONL ב-`~/.claude/projects/.../<id>.jsonl`. תמלולים, מודל, קריאות כלים + חשיבה, שימוש בטוקנים. |
| **Codex** | מתאם בטא | Rollout JSONL ב-`~/.codex/sessions/...`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Cursor** | מתאם בטא | SQLite `state.vscdb`. תמלולי צ'אט/כותב, מודל. |
| **Aider** | מתאם בטא | `.aider.chat.history.md` לכל פרויקט. תמלולים, מודל, ספירות טוקנים. |
| **Goose** | מתאם בטא | SQLite ב-`~/.local/share/goose`. תמלולים, מודל, קריאות כלים, סה"כ טוקנים. |
| **opencode** | מתאם בטא | SQLite ב-`~/.local/share/opencode`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Qwen Code** | מתאם בטא | JSONL ב-`~/.qwen/projects/.../chats`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Pi** | מתאם בטא | JSONL ב-`~/.pi/agent/sessions`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Deep Agents** | מתאם בטא | SQLite ב-`~/.deepagents/.state/sessions.db`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **n8n** | מתאם בטא | SQLite ב-`~/.n8n/database.sqlite`. ריצות זרימת עבודה, ריצות צמתים, בקשות AI Agent, מודל + טוקנים היכן ש-n8n רושם אותם. |

"מתאם בטא" משמעו ש-ClawMetry מספקת קורא לפורמט האמיתי על הדיסק של אותה סביבת ריצה, כל אחד נבנה ואומת מול התקנה אמיתית על מכשיר אמיתי (ראו `tests/fixtures/runtimes/<rt>/`). המתאמים הם לקריאה בלבד; כל אחד כן לגבי מה שסביבת הריצה שלו בפועל שומרת (למשל PicoClaw/NanoClaw/Cursor לא כותבים עלות טוקנים לדיסק). כאשר מספר סביבות ריצה פועלות על צומת אחד, מחליף סביבות הריצה ממקד את תצוגת ההפעלות לאחת, לצלילה עמוקה נקייה.

## מעקב אחר כל סוכן SDK - ייחוס עלות מחוץ ללולאה

סביבות הריצה שלמעלה כולן כותבות הפעלות לדיסק. **סוכן הייצור** שלכם - זה שבניתם על OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, או לולאת `httpx` רגילה - לא. המיירט חסר-ההגדרה של ClawMetry עדיין לוכד את קריאות ה-LLM שלו (עלות, טוקנים, זמן תגובה, שגיאות) על ידי monkey-patching ל-`httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (או משתנה הסביבה `CLAWMETRY_SOURCE=support-agent`) מתייג כל קריאה עם **מקור בעל שם**, כך שכל מוצר שאתם מריצים מופיע כשורה עצמאית וברת-ייחוס-עלות משלו בכרטיס **🔌 מקורות מחוץ ללולאה** בלוח המחוונים ב-Overview - קריאות, ספקים, זמן תגובה, שיעור שגיאות לכל סוכן. לא הוגדר מקור? הקריאות עדיין נעקבות, הכרטיס פשוט נשאר מוסתר.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

זו אותה שכבת נתונים שמזינים אותה מתאמי סביבת הריצה (DuckDB ← תמונת מצב בענן), כך שמקורות מחוץ ללולאה מסתנכרנים עם לוח המחוונים בענן בדיוק כמו כל השאר, מוצפנים מקצה לקצה.

## OpenTelemetry - ניטרלי-ספק, שלחו את המעקבים שלכם לכל מקום

ClawMetry דובר **OpenTelemetry** בשני הכיוונים, באמצעות **מוסכמות סמנטיות GenAI**, כך שמעקבי הסוכן שלכם לעולם לא נעולים לכלי אחד.

**ייצוא** של כל הפעלה - קריאות LLM, כלים, תת-סוכנים, טוקנים, עלות - כמעקבי OTLP/HTTP GenAI לכל אספן (Datadog, Grafana, Honeycomb, או ה-OTel Collector שלכם):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

כותרות אימות ומרווח polling הם משתני סביבה אופציונליים:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ייבוא** - הקולט המובנה של OTLP מקבל מעקבים ומדדים מכל דבר אחר בכתובות `/v1/traces` ו-`/v1/metrics` (`pip install clawmetry[otel]` לייבוא protobuf).

תקבלו את לוח המחוונים חסר-ההגדרה ומקומי-תחילה של ClawMetry **וגם** את הנתונים שלכם בכל backend שהצוות שלכם כבר מריץ - ללא נעילה, ללא סוכן שני להתקין.

## הגדרות

רוב האנשים לא צריכים שום הגדרה. ClawMetry מזהה אוטומטית את סביבת העבודה, היומנים, ההפעלות, וה-crons שלכם.

אם אתם כן צריכים להתאים אישית:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

כל האפשרויות: `clawmetry --help`

## ערוצים נתמכים

ClawMetry מציג פעילות חיה עבור כל ערוץ OpenClaw שהגדרתם. רק ערוצים שמוגדרים בפועל ב-`openclaw.json` שלכם מופיעים בדיאגרמת ה-Flow - ערוצים לא מוגדרים מוסתרים אוטומטית.

לחצו על כל צומת ערוץ ב-Flow כדי לראות תצוגת בועות צ'אט חיה עם ספירות הודעות נכנסות/יוצאות.

| ערוץ | סטטוס | חלונית חיה | הערות |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ מלא | ✅ | הודעות, סטטיסטיקות, רענון כל 10 שניות |
| 💬 **iMessage** | ✅ מלא | ✅ | קורא ישירות מ-`~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ מלא | ✅ | דרך WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ מלא | ✅ | דרך signal-cli |
| 🟣 **Discord** | ✅ מלא | ✅ | זיהוי גילדה + ערוץ |
| 🟪 **Slack** | ✅ מלא | ✅ | זיהוי סביבת עבודה + ערוץ |
| 🌐 **Webchat** | ✅ מלא | ✅ | הפעלות ממשק ווב מובנה |
| 📡 **IRC** | ✅ מלא | ✅ | ממשק בועות בסגנון טרמינל |
| 🍏 **BlueBubbles** | ✅ מלא | ✅ | iMessage דרך BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ מלא | ✅ | דרך webhooks של Chat API |
| 🟣 **MS Teams** | ✅ מלא | ✅ | דרך תוסף בוט Teams |
| 🔷 **Mattermost** | ✅ מלא | ✅ | צ'אט צוותי מתארח עצמאית |
| 🟩 **Matrix** | ✅ מלא | ✅ | מבוזר, תמיכה ב-E2EE |
| 🟢 **LINE** | ✅ מלא | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ מלא | ✅ | הודעות פרטיות מבוזרות NIP-04 |
| 🟣 **Twitch** | ✅ מלא | ✅ | צ'אט דרך חיבור IRC |
| 🔷 **Feishu/Lark** | ✅ מלא | ✅ | הרשמת אירועים WebSocket |
| 🔵 **Zalo** | ✅ מלא | ✅ | Zalo Bot API |

> **זיהוי אוטומטי:** ClawMetry קורא את `~/.openclaw/openclaw.json` שלכם ומרנדר רק את הערוצים שהגדרתם בפועל. אין צורך בהגדרה ידנית.

## פריסת Docker

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

> **הערה:** כאשר מריצים ב-Docker, עגנו את ספריות הנתונים + היומנים של הסוכן שלכם (למשל `~/.openclaw`, `~/.claude`, `~/.codex`) כדי ש-ClawMetry יוכל לזהות אוטומטית את ההגדרה שלכם.

## דרישות

- Python 3.8+
- Flask (מותקן אוטומטית דרך pip)
- סביבת ריצה של סוכן AI על אותו מחשב: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, או n8n (או כרכי נתונים מעוגנים עבור Docker)
- Linux או macOS

## תמיכה ב-NemoClaw / OpenShell

ClawMetry מזהה אוטומטית את [NemoClaw](https://github.com/NVIDIA/NemoClaw) - עטיפת האבטחה הארגונית של NVIDIA עבור OpenClaw שמריצה סוכנים בתוך קונטיינרי OpenShell במעטפת הגנה.

ברוב המקרים אין צורך בהגדרה נוספת. דימון הסנכרון מגלה אוטומטית קבצי הפעלה בין אם הם נמצאים ב-`~/.openclaw/` על המחשב המארח או בתוך קונטיינר OpenShell.

### איך זה עובד

ClawMetry מזהה NemoClaw בשתי דרכים:

1. **זיהוי קובץ הרצה** - בודק את כלי שורת הפקודה `nemoclaw` ומריץ `nemoclaw status` כדי לקבל מידע על ה-sandbox
2. **זיהוי קונטיינר** - סורק קונטיינרי Docker פעילים לחיפוש תמונות `openshell`, `nemoclaw`, או `ghcr.io/nvidia/`, ואז קורא הפעלות דרך עיגוני כרכים או `docker cp`

קבצי הפעלה מסונכרנים מקונטיינרי NemoClaw מתויגים עם `runtime=nemoclaw` ומטא-נתוני `container_id` בלוח המחוונים בענן, כך שתוכלו להבדיל אותם מהפעלות OpenClaw רגילות במבט חטוף.

### הגדרה מומלצת: דימון הסנכרון על המחשב המארח

לחוויה הטובה ביותר, הריצו את דימון הסנכרון של ClawMetry על **המחשב המארח** (לא בתוך ה-sandbox). זה נמנע ממגבלות מדיניות הרשת של NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

דימון הסנכרון ימצא אוטומטית הפעלות בתוך כל קונטיינר OpenShell פעיל.

### אופציונלי: שם sandbox מפורש

אם הזיהוי האוטומטי לא עובד, כוונו את ClawMetry אל ה-sandbox הנכון:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### הרצה בתוך ה-sandbox (מתקדם)

אם אתם חייבים להריץ את דימון הסנכרון **בתוך** ה-sandbox של OpenShell, הוסיפו את חוק היציאה הזה למדיניות הרשת של NemoClaw כדי שיוכל להגיע ל-API הקליטה של ClawMetry:

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
| שקע Docker (`/var/run/docker.sock`) | — | שקע Unix | לגילוי הפעלות קונטיינר |

דימון הסנכרון מבצע רק קריאות HTTPS יוצאות אל `ingest.clawmetry.com`. לא נדרשים פורטים נכנסים.

---

## פריסה בענן

ראו את **[מדריך בדיקת הענן](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** למנהרות SSH, פרוקסי הפוך, ו-Docker.

## בדיקות

פרויקט זה נבדק עם BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## טלמטריה

ClawMetry שולח פינגים אנונימיים של מחזור חיי התקנה אל
`https://app.clawmetry.com/api/install`: פינג `install` אחד בפעם
הראשונה שאתם מריצים את שורת הפקודה `clawmetry` על מחשב חדש, פינג `update` אחד
בהרצה הראשונה לאחר שדרוג לגרסה חדשה, ופינג `onboarded` אחד
כשאתם משלימים את בחירת ההיכרות בתוך לוח המחוונים. אנו משתמשים בזה
כדי לספור התקנות אמיתיות (מספרי ההורדות הגולמיים מ-PyPI הם כ-98% מראות, CI,
והורדות חוזרות של עדכון אוטומטי) וכדי ללמוד אילו מסגרות סוכנים
וגרסאות באמת נמצאות בשטח.

**לכל היותר POST אחד לכל אירוע מחזור חיים לכל גרסה**, המכיל:

| שדה | דוגמה | למה |
|---|---|---|
| `install_id` | UUID אקראי המאוחסן ב-`~/.clawmetry/install_id` | מניעת כפילויות; אנונימי עד שתחברו במפורש סנכרון ענן (פעימת הלב המאומתת של הדימון נושאת אותו אז, ומקשרת התקנה זו לחשבון שלכם) |
| `event` | `install` / `update` / `onboarded` | התקנה חדשה מול שדרוג של התקנה קיימת |
| `version` | `0.12.167` | אילו גרסאות נמצאות בשטח |
| `os` / `os_version` | `Darwin` / `25.3.0` | סדרי עדיפויות לתמיכת פלטפורמה |
| `python` | `3.11.15` | מטריצת תמיכת גרסאות Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | עם אילו סוכנים כדאי לנו לשלב הבא |
| `is_ci` / `ci_provider` | `true` / `github_actions` | הפרדת התקנות אנושיות מרעש CI |

**מה שאנחנו לא שולחים**: IP (הענן גוזר את קוד המדינה בצד השרת
מהבקשה, ואז משליך את ה-IP), שם מארח, שם משתמש, נתיב סביבת עבודה, תוכן קבצים, מפתח ה-API שלכם, האימייל שלכם, כל דבר PII או
ספציפי לסביבת עבודה. מטען העברת הנתונים ניתן לביקורת ב-
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**ביטול הצטרפות** (כל אחת מהאפשרויות הבאות מבטלת זאת לצמיתות):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

כשל רשת כאן לעולם לא חוסם את `clawmetry` מלרוץ - הפינג
הוא שיגור-ושכח בשרשור דימון עם timeout של 3 שניות.

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
  <strong>🦞 ראו את הסוכן שלכם חושב</strong><br>
  <sub>נבנה על ידי <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · חלק מהמערכת האקולוגית של <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
