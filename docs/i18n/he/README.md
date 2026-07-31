<!-- i18n-src:02b789586c7d -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ראו את הסוכן שלכם חושב.** תצפית בזמן אמת עבור **14 סביבות ריצה של סוכני AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 10 נוספות. לוח מחוונים אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. אפס תצורה. מזהה הכל אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900** וזהו, סיימתם.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## עובד עם 14 סביבות ריצה של סוכנים

ClawMetry התחיל כפתרון תצפית עבור OpenClaw, וכעת מודד את **כל צי הסוכנים שלכם** בלוח מחוונים אחד, תוך זיהוי אוטומטי של כל סביבת ריצה במכונה שלכם:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ו-NemoClaw חינמיים באפליקציית הקוד הפתוח; שאר סביבות הריצה נפתחות עם ClawMetry Cloud או רישיון Pro בהתקנה עצמית. עברו בין סביבות ריצה מהכותרת, וכל כרטיסייה - עלות, טוקנים, כלים, מעקבים - תעודכן בהתאם לסביבת הריצה הזו. ראו את **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** לפירוט המדויק של החלוקה בין חינמי לתשלום, מטריצת הרמות, מבנה ה-`/api/entitlement`, וכלי ה-CLI `clawmetry license`.

## מה מקבלים

- **Flow** - תרשים אנימציה חי המציג הודעות זורמות דרך ערוצים, המוח, כלים, וחזרה
- **Overview** - בדיקות תקינות, מפת חום של פעילות, ספירת סשנים, פרטי מודל
- **Usage** - מעקב טוקנים ועלויות עם פירוט יומי/שבועי/חודשי
- **Sessions** - סשני סוכן פעילים עם מודל, טוקנים, פעילות אחרונה
- **Crons** - משימות מתוזמנות עם סטטוס, ריצה הבאה, משך זמן
- **Logs** - הזרמת יומנים בזמן אמת עם קידוד צבעים
- **Memory** - עיון בקבצי SOUL.md, MEMORY.md, AGENTS.md, הערות יומיות
- **Transcripts** - ממשק בועות צ'אט לקריאת היסטוריית סשנים
- **Alerts** - תקרות תקציב, טריגרים לפי שיעור שגיאות, זיהוי סוכן במצב לא מקוון; ניתוב ל-Slack, Discord, PagerDuty, Telegram, אימייל
- **Approvals** - חוסמים מחיקות הרסניות, דחיפות כוח, שינויים במסדי נתונים, sudo, התקנות חבילות, קריאות רשת מאחורי אישור בלחיצה אחת

## צילומי מסך

### 🧠 Brain - זרם אירועי סוכן חי
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - שימוש בטוקנים וסיכום סשנים
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - זרם קריאות כלים בזמן אמת
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - פירוט עלויות לפי מודל וסשן
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - דפדפן קבצי סביבת עבודה
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - עמדת אבטחה ויומן ביקורת
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - תקרות תקציב, טריגרים לפי שיעור שגיאות, webhooks ל-Slack / Discord / PagerDuty / אימייל
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - חסימת קריאות כלים מסוכנות מאחורי אישור ידני; כללי הגנה מבוססי מדיניות
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**חסימה טרם ביצוע עבור Claude Code** - פקודה אחת מתקינה
hook מסוג PreToolUse שעוצר קריאות כלים מתאימות *לפני* שהן רצות וממתין
להחלטה שלכם (הקשה אחת מהטלפון עם
[התראות דחיפה בענן](https://app.clawmetry.com/push) מופעלות):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

דחייה חוסמת רק את קריאת הכלי הבודדת ההיא - הסוכן שומר על הסשן שלו ויכול
לנסות גישה אחרת. אישור מהטלפון מדלג על שאילתת ההרשאה של Claude Code עצמו
(כבר עניתם). קריאות כלים שלא תואמות עולות כ-40 מילישניות ו
נופלות חזרה לזרימת ההרשאות הרגילה של Claude Code. אתם גם מקבלים דחיפה
לטלפון כאשר Claude Code עצמו ממתין לכם (התראות `permission_prompt` /
`idle_prompt`).

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

**מקוד המקור:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## פיתוח ה-Frontend של v2

אפליקציית ה-React של v2 נמצאת בתיקייה `frontend/` ומוגשת בנתיב `/v2` כאשר
שרת ה-Flask מופעל עם v2 מופעל.

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
`http://localhost:8900`, כך שאפליקציית ה-React יכולה לתקשר עם שרת ה-Flask
המקומי ללא צורך בהגדרת CORS נוספת.

כדי לבנות את החבילה שמסופקת עם חבילת ה-Python:

```bash
cd frontend
npm run build
```

חבילת הייצור נכתבת אל `clawmetry/static/v2/dist/`.

## תאימות סביבות ריצה / סוכנים

ClawMetry מתצפת על סביבות ריצה רבות של סוכני AI, לא רק OpenClaw. כל סביבת ריצה שאינה OpenClaw מגיעה עם מתאם קריאה ייעודי שמתרגם את פורמט הסשן המקורי שלה לצורות המאוחדות של ClawMetry; הדימון מכניס אותן לאותו מאגר DuckDB + תמונת מצב בענן, מתויגות עם סביבת הריצה, וכרטיסיית שידור החוזר של הסשן מציגה **מחליף סביבות ריצה** כאשר קיימת יותר מאחת. ראו את [`docs/compatibility.md`](docs/compatibility.md) למטריצה המלאה + מדריך להוספת סביבות ריצה, ואת [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) למבוא למשפחת OpenClaw.

| סביבת ריצה / סוכן | סטטוס | הערות |
|---|---|---|
| **OpenClaw** | מובנה | סביבת ריצה מרכזית, מזוהה אוטומטית |
| **PicoClaw** | מתאם בטא | JSONL שטוח מסוג `providers.Message` (`~/.picoclaw/workspace/sessions`). שידור חוזר, מודל, קריאות כלים. |
| **NanoClaw** | מתאם בטא | SQLite פר-סשן (`data/v2-sessions`). שידור חוזר + ספירת הודעות. |
| **Hermes** | מתאם בטא | SQLite ‏`~/.hermes/state.db`. שידור חוזר, מודל, טוקנים/עלות. |
| **Claude Code** | מתאם בטא | JSONL ‏`~/.claude/projects/.../<id>.jsonl`. שידור חוזר, מודל, קריאות כלים + חשיבה, שימוש בטוקנים. |
| **Codex** | מתאם בטא | Rollout JSONL ‏`~/.codex/sessions/...`. שידור חוזר, מודל, קריאות כלים, שימוש בטוקנים. |
| **Cursor** | מתאם בטא | SQLite ‏`state.vscdb`. שידור חוזר של צ'אט/composer, מודל. |
| **Aider** | מתאם בטא | `.aider.chat.history.md` לכל פרויקט. שידור חוזר, מודל, ספירת טוקנים. |
| **Goose** | מתאם בטא | SQLite ‏`~/.local/share/goose`. שידור חוזר, מודל, קריאות כלים, סך טוקנים. |
| **opencode** | מתאם בטא | SQLite ‏`~/.local/share/opencode`. שידור חוזר, מודל, קריאות כלים, טוקנים + עלות. |
| **Qwen Code** | מתאם בטא | JSONL ‏`~/.qwen/projects/.../chats`. שידור חוזר, מודל, קריאות כלים, שימוש בטוקנים. |
| **Pi** | מתאם בטא | JSONL ‏`~/.pi/agent/sessions`. שידור חוזר, מודל, קריאות כלים, טוקנים + עלות. |
| **Deep Agents** | מתאם בטא | SQLite ‏`~/.deepagents/.state/sessions.db`. שידור חוזר, מודל, קריאות כלים, טוקנים + עלות. |
| **n8n** | מתאם בטא | SQLite ‏`~/.n8n/database.sqlite`. הרצות workflow, הרצות node, בקשות AI Agent, מודל + טוקנים היכן ש-n8n מתעד אותם. |
| **Antigravity** | מתאם בטא | Brain JSONL תחת `~/.gemini/<flavor>/brain/`. שיחות, שלבי כלים, חשיבה, פיצול טוקני Gemini פר-generation + עלות, צריכת generation ברקע. |

"מתאם בטא" משמעו ש-ClawMetry מספקת קורא עבור הפורמט האמיתי של סביבת הריצה הזו על הדיסק, כל אחד נבנה + מאומת מול התקנה אמיתית על מכונה אמיתית (ראו `tests/fixtures/runtimes/<rt>/`). המתאמים הם לקריאה בלבד; כל אחד מהם כן לגבי מה שסביבת הריצה שלו באמת שומרת (למשל PicoClaw/NanoClaw/Cursor לא כותבים עלות טוקנים לדיסק). כאשר כמה סביבות ריצה פועלות בצומת אחד, מחליף סביבות הריצה מצמצם את תצוגת הסשנים לאחת בלבד לצלילה נקייה.

## מעקב אחר כל סוכן SDK - ייחוס עלויות out-loop

כל סביבות הריצה שלמעלה כותבות סשנים לדיסק. **סוכן הייצור** שלכם - זה שבניתם על OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, או לולאת `httpx` פשוטה - לא. המיירט חסר-התצורה של ClawMetry עדיין לוכד את קריאות ה-LLM שלו (עלות, טוקנים, זמן תגובה, שגיאות) על ידי monkey-patching ל-`httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (או משתנה הסביבה `CLAWMETRY_SOURCE=support-agent`) מתייג כל קריאה עם **מקור בעל שם**, כך שכל מוצר שאתם מריצים מופיע כשורה משלו, מדרגה ראשונה וניתנת לייחוס עלות, בכרטיסיית **🔌 מקורות out-loop** בלוח המחוונים ב-Overview - קריאות, ספקים, זמן תגובה, שיעור שגיאות לכל סוכן. לא הגדרתם מקור? הקריאות עדיין נמדדות, הכרטיסייה פשוט נשארת מוסתרת.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

זוהי אותה שכבת נתונים שמאכילים אותה מתאמי סביבת הריצה (DuckDB → תמונת מצב בענן), כך שמקורות out-loop מסתנכרנים לענן בדיוק כמו כל השאר, מוצפנים מקצה לקצה.

## OpenTelemetry - נייטרלי ספקים, שלחו את המעקבים שלכם לכל מקום

ClawMetry דוברת **OpenTelemetry** בשני הכיוונים, תוך שימוש ב**מוסכמות הסמנטיות של GenAI**, כך שמעקבי הסוכן שלכם לעולם לא ננעלים בכלי אחד.

**ייצוא** של כל סשן - קריאות LLM, כלים, תת-סוכנים, טוקנים, עלות - כ-spans מסוג OTLP/HTTP GenAI לכל אספן (Datadog, Grafana, Honeycomb, או ה-OTel Collector שלכם):

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

**ייבוא** - מקלט ה-OTLP המובנה מקבל מעקבים ומדדים מכל דבר אחר בנתיבים `/v1/traces` ו-`/v1/metrics` (‏`pip install clawmetry[otel]` לייבוא protobuf).

אתם מקבלים את לוח המחוונים חסר-התצורה, מקומי-תחילה של ClawMetry **וגם** את הנתונים שלכם בכל backend שהצוות שלכם כבר מריץ - ללא נעילה, ללא צורך בסוכן שני להתקנה.

## תצורה

רוב האנשים לא צריכים שום תצורה. ClawMetry מזהה אוטומטית את סביבת העבודה, היומנים, הסשנים והמשימות המתוזמנות שלכם.

אם כן צריך להתאים אישית:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

כל האפשרויות: `clawmetry --help`

## ערוצים נתמכים

ClawMetry מציגה פעילות חיה עבור כל ערוץ OpenClaw שהגדרתם. רק ערוצים שבאמת מוגדרים בקובץ ה-`openclaw.json` שלכם מופיעים בתרשים ה-Flow - ערוצים לא מוגדרים מוסתרים אוטומטית.

לחצו על כל צומת ערוץ ב-Flow כדי לראות תצוגת בועות צ'אט חיה עם ספירת הודעות נכנסות/יוצאות.

| ערוץ | סטטוס | חלון חי | הערות |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ מלא | ✅ | הודעות, סטטיסטיקות, רענון כל 10 שניות |
| 💬 **iMessage** | ✅ מלא | ✅ | קורא ישירות מ-`~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ מלא | ✅ | דרך WhatsApp Web ‏(Baileys) |
| 🔵 **Signal** | ✅ מלא | ✅ | דרך signal-cli |
| 🟣 **Discord** | ✅ מלא | ✅ | זיהוי גילדה + ערוץ |
| 🟪 **Slack** | ✅ מלא | ✅ | זיהוי סביבת עבודה + ערוץ |
| 🌐 **Webchat** | ✅ מלא | ✅ | סשנים מובנים של ממשק אינטרנט |
| 📡 **IRC** | ✅ מלא | ✅ | ממשק בועות בסגנון טרמינל |
| 🍏 **BlueBubbles** | ✅ מלא | ✅ | iMessage דרך BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ מלא | ✅ | דרך webhooks של Chat API |
| 🟣 **MS Teams** | ✅ מלא | ✅ | דרך plugin של בוט Teams |
| 🔷 **Mattermost** | ✅ מלא | ✅ | צ'אט צוות בהתקנה עצמית |
| 🟩 **Matrix** | ✅ מלא | ✅ | מבוזר, תמיכה ב-E2EE |
| 🟢 **LINE** | ✅ מלא | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ מלא | ✅ | הודעות פרטיות מבוזרות NIP-04 |
| 🟣 **Twitch** | ✅ מלא | ✅ | צ'אט דרך חיבור IRC |
| 🔷 **Feishu/Lark** | ✅ מלא | ✅ | מנוי אירועים דרך WebSocket |
| 🔵 **Zalo** | ✅ מלא | ✅ | Zalo Bot API |

> **זיהוי אוטומטי:** ClawMetry קוראת את `~/.openclaw/openclaw.json` שלכם ומציגה רק את הערוצים שבאמת הגדרתם. אין צורך בהגדרה ידנית.

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

> **הערה:** בעת הרצה ב-Docker, חברו את תיקיות הנתונים + היומנים של הסוכן שלכם (למשל `~/.openclaw`, `~/.claude`, `~/.codex`) כדי ש-ClawMetry תוכל לזהות אוטומטית את ההגדרה שלכם.

## דרישות

- Python 3.8+
- Flask (מותקן אוטומטית דרך pip)
- סביבת ריצה של סוכן AI על אותה מכונה: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, או Antigravity (או כרכי mount עבור Docker)
- Linux או macOS

## תמיכה ב-NemoClaw / OpenShell

ClawMetry מזהה אוטומטית את [NemoClaw](https://github.com/NVIDIA/NemoClaw) - עטיפת האבטחה הארגונית של NVIDIA עבור OpenClaw שמריצה סוכנים בתוך קונטיינרי OpenShell מבודדים (sandboxed).

ברוב המקרים לא נדרשת תצורה נוספת. הדימון של הסנכרון מגלה אוטומטית קבצי סשן בין אם הם נמצאים ב-`~/.openclaw/` על המארח ובין אם בתוך קונטיינר OpenShell.

### איך זה עובד

ClawMetry מזהה NemoClaw בשתי דרכים:

1. **זיהוי בינארי** - בודקת קיום של ה-CLI ‏`nemoclaw` ומריצה `nemoclaw status` כדי לקבל מידע על ה-sandbox
2. **זיהוי קונטיינר** - סורקת קונטיינרי Docker פעילים לחיפוש תמונות `openshell`, `nemoclaw`, או `ghcr.io/nvidia/`, ולאחר מכן קוראת סשנים דרך volume mounts או `docker cp`

קבצי סשן שסונכרנו מקונטיינרי NemoClaw מתויגים עם `runtime=nemoclaw` ומטא-דאטה `container_id` בלוח המחוונים בענן, כך שתוכלו להבחין בינם לבין סשני OpenClaw רגילים במבט חטוף.

### הגדרה מומלצת: דימון הסנכרון על ה-HOST

לחוויה הטובה ביותר, הריצו את דימון הסנכרון של ClawMetry על **מכונת המארח** (לא בתוך ה-sandbox). זה מונע הגבלות של מדיניות הרשת של NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

דימון הסנכרון ימצא אוטומטית סשנים בתוך כל קונטיינרי OpenShell שרצים.

### אופציונלי: שם sandbox מפורש

אם הזיהוי האוטומטי לא עובד, כוונו את ClawMetry ל-sandbox הנכון:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### הרצה בתוך ה-sandbox (מתקדם)

אם אתם חייבים להריץ את דימון הסנכרון **בתוך** ה-sandbox של OpenShell, הוסיפו את כלל היציאה (egress) הזה למדיניות הרשת של NemoClaw כדי שיוכל להגיע ל-API הקליטה של ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | כן (דימון סנכרון → ענן) |
| `localhost:8900` | 8900 | HTTP | כן (ממשק לוח מחוונים מקומי) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | לגילוי סשנים בקונטיינרים |

דימון הסנכרון מבצע רק קריאות HTTPS יוצאות אל `ingest.clawmetry.com`. אין צורך בפורטים נכנסים.

---

## פריסה בענן

ראו את **[מדריך בדיקת הענן](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** לתעלות SSH, פרוקסי הפוך, ו-Docker.

## בדיקות

פרויקט זה נבדק עם BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## טלמטריה

ClawMetry שולחת פינגים אנונימיים של מחזור חיי ההתקנה אל
`https://app.clawmetry.com/api/install`: פינג `install` אחד בפעם
הראשונה שאתם מריצים את ה-CLI ‏`clawmetry` על מכונה חדשה, פינג `update`
אחד בהרצה הראשונה אחרי שדרוג לגרסה חדשה, ופינג `onboarded`
אחד כשאתם משלימים את בחירת ה-onboarding בתוך לוח המחוונים. אנחנו משתמשים בזה
כדי לספור התקנות אמיתיות (מספרי ההורדות הגולמיים מ-PyPI הם כ-98% שרתי מראה, CI,
והורדות חוזרות של עדכון אוטומטי) וכדי ללמוד אילו מסגרות סוכנים
וגרסאות באמת קיימות בשטח.

**לכל היותר בקשת POST אחת לכל אירוע מחזור חיים לכל גרסה**, המכילה:

| שדה | דוגמה | למה |
|---|---|---|
| `install_id` | UUID אקראי המאוחסן ב-`~/.clawmetry/install_id` | הסרת כפילויות; אנונימי עד שאתם מחברים במפורש סנכרון Cloud (פעימת הלב המאומתת של הדימון אז נושאת אותו, ומקשרת התקנה זו לחשבון שלכם) |
| `event` | `install` / `update` / `onboarded` | התקנה חדשה לעומת שדרוג של התקנה קיימת |
| `version` | `0.12.167` | אילו גרסאות קיימות בשטח |
| `os` / `os_version` | `Darwin` / `25.3.0` | סדרי עדיפויות של תמיכה בפלטפורמות |
| `python` | `3.11.15` | מטריצת תמיכה בגרסאות Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | עם אילו סוכנים כדאי לנו לשלב הבא |
| `is_ci` / `ci_provider` | `true` / `github_actions` | הפרדה בין התקנות אנושיות לרעש CI |

**מה אנחנו לא שולחים**: כתובת IP (הענן גוזר את קוד המדינה בצד השרת
מתוך הבקשה, ואז משליך את ה-IP), שם מארח, שם משתמש, נתיב סביבת עבודה, תוכן קבצים,
מפתח ה-API שלכם, האימייל שלכם, כל דבר אישי או ספציפי לסביבת עבודה. מטען הרשת
ניתן לביקורת ב-
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**ביטול הצטרפות** (כל אחת מהאפשרויות הבאות מבטלת זאת לצמיתות):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

כשל רשת כאן לעולם לא חוסם את `clawmetry` מלרוץ - הפינג
הוא ירי-ושכח על thread נפרד של הדימון עם timeout של 3 שניות.

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
  <sub>נבנה על ידי <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · חלק מהאקוסיסטם של <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
