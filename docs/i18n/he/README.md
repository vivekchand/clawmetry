<!-- i18n-src:bab48eec552f -->
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

ClawMetry החל כתצפית עבור OpenClaw, וכעת מודד את **כל צי הסוכנים** שלכם בלוח מחוונים אחד, ומזהה אוטומטית כל סביבת ריצה במחשב שלכם:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw ו-NemoClaw חינמיים באפליקציית הקוד הפתוח; יתר סביבות הריצה נפתחות עם ClawMetry Cloud או עם רישיון Pro בהתקנה עצמית. החליפו סביבת ריצה מהכותרת העליונה, וכל לשונית - עלות, טוקנים, כלים, מעקבים - תשתנה בהתאם לסביבה הזו. ראו את **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** לפילוח המדויק בין חינמי לבתשלום, מטריצת הרמות, מבנה `/api/entitlement`, וכלי שורת הפקודה `clawmetry license`.

## מה תקבלו

- **Flow** - דיאגרמה חיה ומונפשת המציגה הודעות זורמות דרך ערוצים, המוח, כלים וחזרה
- **Overview** - בדיקות תקינות, מפת חום של פעילות, ספירת סשנים, פרטי מודל
- **Usage** - מעקב אחר טוקנים ועלויות עם פילוחים יומיים/שבועיים/חודשיים
- **Sessions** - סשני סוכן פעילים עם מודל, טוקנים, פעילות אחרונה
- **Crons** - משימות מתוזמנות עם סטטוס, ריצה הבאה, משך זמן
- **Logs** - הזרמת יומנים בזמן אמת עם קידוד צבעים
- **Memory** - עיינו בקבצי SOUL.md, MEMORY.md, AGENTS.md, הערות יומיות
- **Transcripts** - ממשק בועות צ'אט לקריאת היסטוריית סשנים
- **Alerts** - תקרות תקציב, טריגרים לשיעור שגיאות, זיהוי ניתוק סוכן; מנתב אל Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** - חסימת מחיקות הרסניות, force push, שינויים במסדי נתונים, sudo, התקנות חבילות, וקריאות רשת מאחורי אישור בלחיצה אחת

## צילומי מסך

### 🧠 Brain - זרם אירועים חי של הסוכן
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - שימוש בטוקנים וסיכום סשנים
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - הזנת קריאות כלים בזמן אמת
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - פילוח עלויות לפי מודל וסשן
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - דפדפן קבצי סביבת העבודה
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - תנוחת אבטחה ויומן ביקורת
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - תקרות תקציב, טריגרים לשיעור שגיאות, webhooks ל-Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - חסימת קריאות כלים מסוכנות מאחורי אישור ידני; כללי הגנה מבוססי מדיניות
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**חסימה טרום-ביצוע עבור Claude Code** - פקודה אחת מתקינה
hook מסוג PreToolUse שעוצר קריאות כלים תואמות *לפני* שהן רצות וממתין
להחלטה שלכם (הקשה אחת מהטלפון עם
[התראות דחיפה מהענן](https://app.clawmetry.com/push) מופעלות):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

דחייה חוסמת רק את קריאת הכלי הבודדת ההיא - הסוכן שומר על הסשן שלו ויכול
לנסות גישה אחרת. אישור מהטלפון עוקף את בקשת ההרשאה המובנית של Claude Code
(כבר עניתם). כלים שלא הותאמו עולים כ-40ms ו
עוברים לזרימת ההרשאות הרגילה של Claude Code. תקבלו גם התראת דחיפה לטלפון כאשר
Claude Code עצמו ממתין לכם (התראות `permission_prompt` /
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

**מהמקור:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## פיתוח Frontend v2

אפליקציית ה-React של v2 נמצאת בתיקייה `frontend/` ומוגשת בנתיב `/v2` כאשר
שרת ה-Flask מופעל עם v2 פעיל.

השתמשו בשני מסופים במהלך הפיתוח:

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

פתחו את `http://localhost:5173/v2/`. Vite מנתב בקשות `/api` אל
`http://localhost:8900`, כך שאפליקציית ה-React יכולה לתקשר עם שרת ה-Flask המקומי
ללא הגדרת CORS נוספת.

כדי לבנות את החבילה שמסופקת עם חבילת ה-Python:

```bash
cd frontend
npm run build
```

חבילת הייצור נכתבת לנתיב `clawmetry/static/v2/dist/`.

## תאימות סביבות ריצה / סוכנים

ClawMetry עוקב אחר סביבות ריצה רבות של סוכני AI, לא רק OpenClaw. כל סביבת ריצה שאינה OpenClaw מגיעה עם מתאם קריאה ייעודי שמתרגם את פורמט הסשנים המקורי שלה לצורות המאוחדות של ClawMetry; הדימון מזין אותן לאותו מאגר DuckDB + תמונת מצב ענן, מתויגות לפי סביבת הריצה, ולשונית שחזור הסשנים מציגה **מתג סביבת ריצה** כאשר קיימת יותר מאחת. ראו את [`docs/compatibility.md`](docs/compatibility.md) למטריצה המלאה + מדריך להוספת סביבות ריצה, ואת [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) למבוא למשפחת OpenClaw.

| סביבת ריצה / סוכן | סטטוס | הערות |
|---|---|---|
| **OpenClaw** | ילידי | סביבת ריצה ייחוס, מזוהה אוטומטית |
| **PicoClaw** | מתאם בטא | JSONL שטוח מסוג `providers.Message` (`~/.picoclaw/workspace/sessions`). תמלולים, מודל, קריאות כלים. |
| **NanoClaw** | מתאם בטא | SQLite לכל סשן (`data/v2-sessions`). תמלולים + ספירת הודעות. |
| **Hermes** | מתאם בטא | SQLite `~/.hermes/state.db`. תמלולים, מודל, טוקנים/עלות. |
| **Claude Code** | מתאם בטא | JSONL `~/.claude/projects/.../<id>.jsonl`. תמלולים, מודל, קריאות כלים + חשיבה, שימוש בטוקנים. |
| **Codex** | מתאם בטא | Rollout JSONL ‏`~/.codex/sessions/...`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Cursor** | מתאם בטא | SQLite `state.vscdb`. תמלולי צ'אט/composer, מודל. |
| **Aider** | מתאם בטא | `.aider.chat.history.md` לכל פרויקט. תמלולים, מודל, ספירת טוקנים. |
| **Goose** | מתאם בטא | SQLite `~/.local/share/goose`. תמלולים, מודל, קריאות כלים, סך טוקנים. |
| **opencode** | מתאם בטא | SQLite `~/.local/share/opencode`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Qwen Code** | מתאם בטא | JSONL `~/.qwen/projects/.../chats`. תמלולים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Pi** | מתאם בטא | JSONL `~/.pi/agent/sessions`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |
| **Deep Agents** | מתאם בטא | SQLite `~/.deepagents/.state/sessions.db`. תמלולים, מודל, קריאות כלים, טוקנים + עלות. |

"מתאם בטא" משמעו ש-ClawMetry מספקת קורא לפורמט האמיתי על הדיסק של אותה סביבת ריצה, שכל אחד מהם נבנה ואומת מול התקנה אמיתית על מכונה אמיתית (ראו `tests/fixtures/runtimes/<rt>/`). המתאמים הם לקריאה בלבד; כל אחד מהם כן לגבי מה שסביבת הריצה שלו שומרת בפועל (למשל PicoClaw/NanoClaw/Cursor לא כותבים עלות טוקנים לדיסק). כאשר מספר סביבות ריצה פועלות על צומת אחד, מתג סביבת הריצה ממקד את תצוגת הסשנים לאחת מהן לצלילה ממוקדת ונקייה.

## מעקב אחר כל סוכן SDK - ייחוס עלות מחוץ ללולאה

סביבות הריצה שלמעלה כולן כותבות סשנים לדיסק. הסוכן ה**ייצורי** שלכם - זה שבניתם על OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, או לולאת `httpx` פשוטה - לא עושה זאת. המיירט חסר-התצורה של ClawMetry עדיין תופס את קריאות ה-LLM שלו (עלות, טוקנים, זמן תגובה, שגיאות) באמצעות monkey-patching ל-`httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (או משתנה הסביבה `CLAWMETRY_SOURCE=support-agent`) מתייג כל קריאה עם **מקור בעל שם**, כך שכל מוצר שאתם מריצים מופיע כשורה עצמאית, בת-ייחוס עלות, בכרטיס **🔌 מקורות מחוץ ללולאה** של הלוח בלשונית Overview - קריאות, ספקים, זמן תגובה, שיעור שגיאות לכל סוכן. לא הגדרתם מקור? הקריאות עדיין נעקבות, הכרטיס פשוט נשאר מוסתר.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

זוהי אותה שכבת נתונים שמזינים אליה מתאמי סביבת הריצה (DuckDB → תמונת מצב ענן), כך שמקורות מחוץ ללולאה מסתנכרנים לענן בדיוק כמו כל השאר, מוצפנים מקצה לקצה.

## OpenTelemetry - נטרלי-ספק, שלחו את המעקבים שלכם לכל מקום

ClawMetry דוברת **OpenTelemetry** בשני הכיוונים, תוך שימוש ב**מוסכמות הסמנטיות של GenAI**, כך שמעקבי הסוכן שלכם לעולם לא נעולים לכלי אחד.

**ייצוא** של כל סשן - קריאות LLM, כלים, תת-סוכנים, טוקנים, עלות - כספאני OTLP/HTTP GenAI לכל אספן (Datadog, Grafana, Honeycomb, או OTel Collector משלכם):

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

**קליטה** - מקלט ה-OTLP המובנה קולט מעקבים ומדדים מכל דבר אחר בכתובות `/v1/traces` ו-`/v1/metrics` (‏`pip install clawmetry[otel]` לקליטת protobuf).

תקבלו את לוח המחוונים חסר-התצורה, המקומי-תחילה, של ClawMetry **וגם** את הנתונים שלכם בכל backend שהצוות שלכם כבר מריץ - ללא נעילה, ללא סוכן שני להתקין.

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

ClawMetry מציגה פעילות חיה עבור כל ערוץ OpenClaw שהוגדר אצלכם. רק ערוצים שהוגדרו בפועל בקובץ ה-`openclaw.json` שלכם מופיעים בדיאגרמת ה-Flow - ערוצים לא מוגדרים מוסתרים אוטומטית.

לחצו על כל צומת ערוץ ב-Flow כדי לראות תצוגת בועות צ'אט חיה עם ספירת הודעות נכנסות/יוצאות.

| ערוץ | סטטוס | חלונית חיה | הערות |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ מלא | ✅ | הודעות, סטטיסטיקות, רענון כל 10 שניות |
| 💬 **iMessage** | ✅ מלא | ✅ | קורא ישירות מ-`~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ מלא | ✅ | דרך WhatsApp Web ‏(Baileys) |
| 🔵 **Signal** | ✅ מלא | ✅ | דרך signal-cli |
| 🟣 **Discord** | ✅ מלא | ✅ | זיהוי גילדה + ערוץ |
| 🟪 **Slack** | ✅ מלא | ✅ | זיהוי סביבת עבודה + ערוץ |
| 🌐 **Webchat** | ✅ מלא | ✅ | סשנים של ממשק ווב מובנה |
| 📡 **IRC** | ✅ מלא | ✅ | ממשק בועות בסגנון מסוף |
| 🍏 **BlueBubbles** | ✅ מלא | ✅ | iMessage דרך BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ מלא | ✅ | דרך webhooks של Chat API |
| 🟣 **MS Teams** | ✅ מלא | ✅ | דרך תוסף בוט Teams |
| 🔷 **Mattermost** | ✅ מלא | ✅ | צ'אט צוותי בהתקנה עצמית |
| 🟩 **Matrix** | ✅ מלא | ✅ | מבוזר, תמיכה ב-E2EE |
| 🟢 **LINE** | ✅ מלא | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ מלא | ✅ | הודעות פרטיות מבוזרות NIP-04 |
| 🟣 **Twitch** | ✅ מלא | ✅ | צ'אט דרך חיבור IRC |
| 🔷 **Feishu/Lark** | ✅ מלא | ✅ | מנוי אירועים דרך WebSocket |
| 🔵 **Zalo** | ✅ מלא | ✅ | Zalo Bot API |

> **זיהוי אוטומטי:** ClawMetry קוראת את `~/.openclaw/openclaw.json` שלכם ומציגה רק את הערוצים שאכן הגדרתם. אין צורך בהגדרה ידנית.

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

> **הערה:** בעת הרצה ב-Docker, עגנו את תיקיות הנתונים + היומנים של הסוכן שלכם (למשל `~/.openclaw`, `~/.claude`, `~/.codex`) כדי ש-ClawMetry תוכל לזהות אוטומטית את ההגדרות שלכם.

## דרישות

- Python 3.8+
- Flask (מותקן אוטומטית דרך pip)
- סביבת ריצה של סוכן AI על אותה מכונה: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, או Deep Agents (או כרכים מעוגנים עבור Docker)
- Linux או macOS

## תמיכה ב-NemoClaw / OpenShell

ClawMetry מזהה אוטומטית את [NemoClaw](https://github.com/NVIDIA/NemoClaw) - עוטפת האבטחה הארגונית של NVIDIA עבור OpenClaw שמריצה סוכנים בתוך קונטיינרי OpenShell מבודדים (sandboxed).

ברוב המקרים אין צורך בתצורה נוספת. דימון הסנכרון מגלה אוטומטית קבצי סשנים בין אם הם נמצאים ב-`~/.openclaw/` על המארח או בתוך קונטיינר OpenShell.

### כיצד זה עובד

ClawMetry מזהה את NemoClaw בשתי דרכים:

1. **זיהוי בינארי** - בודקת את קיומו של כלי שורת הפקודה `nemoclaw` ומריצה `nemoclaw status` לקבלת מידע על ה-sandbox
2. **זיהוי קונטיינר** - סורקת קונטיינרי Docker פעילים בחיפוש אחר תמונות `openshell`, `nemoclaw`, או `ghcr.io/nvidia/`, ולאחר מכן קוראת סשנים דרך volume mounts או `docker cp`

קבצי סשן מסונכרנים מקונטיינרי NemoClaw מתויגים עם `runtime=nemoclaw` ומטא-נתוני `container_id` בלוח המחוונים בענן, כך שתוכלו להבחין ביניהם לבין סשני OpenClaw רגילים במבט חטוף.

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

### יציאות (ports) ונקודות קצה

| נקודת קצה | יציאה | פרוטוקול | נדרש |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | כן (דימון סנכרון → ענן) |
| `localhost:8900` | 8900 | HTTP | כן (ממשק לוח המחוונים המקומי) |
| שקע Docker (`/var/run/docker.sock`) | — | Unix socket | לגילוי סשנים בקונטיינרים |

דימון הסנכרון מבצע רק קריאות HTTPS יוצאות אל `ingest.clawmetry.com`. אין צורך ביציאות נכנסות.

---

## פריסה בענן

ראו את **[מדריך בדיקות הענן](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** למנהרות SSH, פרוקסי הפוך, ו-Docker.

## בדיקות

פרויקט זה נבדק עם BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## טלמטריה

ClawMetry שולחת פינג אנונימי יחיד של "הרצה ראשונה" אל
`https://app.clawmetry.com/api/install` בפעם הראשונה שאתם מריצים את
`clawmetry` CLI על מכונה חדשה. אנחנו משתמשים בזה כדי לספור התקנות (המדד
השיווקי היחיד שיש לנו לפרויקט קוד פתוח) וכדי ללמוד באילו מסגרות
סוכנים המשתמשים שלנו התקינו.

**בדיוק POST אחד להתקנה**, המכיל:

| שדה | דוגמה | למה |
|---|---|---|
| `install_id` | UUID אקראי שמאוחסן ב-`~/.clawmetry/install_id` | מניעת כפילויות; לא מקושר לאימייל או ל-api_key שלכם |
| `version` | `0.12.167` | אילו גרסאות נמצאות בשטח |
| `os` / `os_version` | `Darwin` / `25.3.0` | סדרי עדיפויות לתמיכת פלטפורמות |
| `python` | `3.11.15` | מטריצת תמיכה בגרסאות Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | עם אילו סוכנים כדאי לנו להשתלב הלאה |
| `is_ci` / `ci_provider` | `true` / `github_actions` | הפרדת התקנות אנושיות מרעש CI |

**מה שאנחנו לא שולחים**: כתובת IP (הענן מגזר את קוד המדינה בצד השרת
מהבקשה, ואז זורק את ה-IP), שם מארח, שם משתמש, נתיב סביבת עבודה,
תוכן קבצים, ה-api_key שלכם, האימייל שלכם, שום דבר אישי או ייחודי
לסביבת העבודה. מטען התקשורת ניתן לביקורת ב-
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**ביטול הצטרפות** (כל אחת מהאפשרויות הבאות מבטלת זאת לצמיתות):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

תקלת רשת כאן לעולם לא חוסמת את הרצת `clawmetry` - הפינג
הוא fire-and-forget על thread נפרד עם timeout של 3 שניות.

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
