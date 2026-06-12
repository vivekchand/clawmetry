<!-- i18n-src:48548997be76 -->
> עברית translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ראו את הסוכן שלכם חושב.** מעקב בזמן אמת עבור **12 סביבות ריצה של סוכני בינה מלאכותית**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ועוד 8. לוח בקרה אחד לכל צי הסוכנים שלכם.

> 🌐 **קראו זאת ב:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [עוד →](docs/i18n/)

פקודה אחת. ללא הגדרות. מזהה הכל אוטומטית.

```bash
pip install clawmetry && clawmetry
```

נפתח בכתובת **http://localhost:8900** וזהו.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## תואם ל-12 סביבות ריצה של סוכנים

ClawMetry החל כמערכת מעקב עבור OpenClaw, וכיום מודד את **כל צי הסוכנים שלכם** בלוח בקרה אחד, תוך זיהוי אוטומטי של כל סביבת ריצה במחשב שלכם:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw ו-NemoClaw זמינים בחינם באפליקציה הקוד-פתוחה; שאר סביבות הריצה מופעלות עם ClawMetry Cloud או רישיון Pro עצמאי. החליפו סביבות ריצה מהכותרת וכל לשונית, עלות, טוקנים, כלים, עקבות, תחייב מחדש לאותה סביבה.

## מה תקבלו

- **Flow** — דיאגרמה מונפשת בזמן אמת המציגה הודעות הזורמות דרך ערוצים, המוח, כלים וחזרה
- **Overview** — בדיקות תקינות, מפת חום של פעילות, ספירת סשנים, מידע על מודלים
- **Usage** — מעקב אחר טוקנים ועלויות עם פירוט יומי/שבועי/חודשי
- **Sessions** — סשני סוכן פעילים עם מודל, טוקנים ופעילות אחרונה
- **Crons** — משימות מתוזמנות עם סטטוס, הרצה הבאה ומשך
- **Logs** — הזרמת יומנים בזמן אמת עם קידוד צבע
- **Memory** — עיון ב-SOUL.md, MEMORY.md, AGENTS.md ורשומות יומיות
- **Transcripts** — ממשק בועות צ'אט לקריאת היסטוריות סשן
- **Alerts** — תקרות תקציב, טריגרים לשיעור שגיאות, זיהוי סוכן לא מקוון; ניתוב ל-Slack, Discord, PagerDuty, Telegram ודואר אלקטרוני
- **Approvals** — חסימת מחיקות הרסניות, דחיפות כפויות, שינויים ב-DB, sudo, התקנות חבילות וקריאות רשת מאחורי אישור בלחיצה אחת

## צילומי מסך

### 🧠 Brain — זרם אירועי סוכן בזמן אמת
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — שימוש בטוקנים וסיכום סשנים
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — פיד קריאות כלים בזמן אמת
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — פירוט עלויות לפי מודל וסשן
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — דפדפן קבצי סביבת עבודה
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — מצב אבטחה ויומן ביקורת
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — תקרות תקציב, טריגרים לשיעור שגיאות, webhooks ל-Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — חסימת קריאות כלים מסוכנות מאחורי אישור ידני; כללי הגנה מגובי מדיניות
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## התקנה

**שורה אחת (מומלץ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**מקוד מקור:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## פיתוח ממשק v2

אפליקציית ה-React של v2 נמצאת ב-`frontend/` ומוגשת בנתיב `/v2` כאשר שרת ה-Flask מופעל עם v2 מופעל.

השתמשו בשני טרמינלים בזמן הפיתוח:

```bash
# טרמינל 1: Flask API/server על :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# טרמינל 2: Vite dev server על :5173
cd frontend
nvm use
npm ci
npm run dev
```

פתחו את `http://localhost:5173/v2/`. Vite מכוון בקשות `/api` אל `http://localhost:8900`, כך שאפליקציית ה-React יכולה לתקשר עם שרת ה-Flask המקומי ללא הגדרת CORS נוספת.

לבניית החבילה שמגיעה עם חבילת Python:

```bash
cd frontend
npm run build
```

חבילת הייצור נכתבת ל-`clawmetry/static/v2/dist/`.

## תאימות סביבות ריצה / סוכנים

ClawMetry עוקב אחרי סביבות ריצה רבות של סוכני בינה מלאכותית, לא רק OpenClaw. כל סביבת ריצה שאינה OpenClaw מגיעה עם מתאם קריאה ייעודי שמתרגם את פורמט הסשן הייחודי שלה לצורות המאוחדות של ClawMetry; הדמון קולט אותן לאותו מאגר DuckDB ותמונת מצב ענן, מתויגות עם סביבת הריצה, ולשונית ה-Session מציגה **מחליף סביבות ריצה** כאשר יותר מאחת קיימת. ראו [`docs/compatibility.md`](docs/compatibility.md) למטריצה המלאה ומדריך להוספת סביבות ריצה, ו-[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) למבוא למשפחת OpenClaw.

| סביבת ריצה / סוכן | סטטוס | הערות |
|---|---|---|
| **OpenClaw** | ייעודי | סביבת ריצה ייחוסית, מזוהה אוטומטית |
| **PicoClaw** | מתאם בטא | JSONL שטוח `providers.Message` (`~/.picoclaw/workspace/sessions`). תמלילים, מודל, קריאות כלים. |
| **NanoClaw** | מתאם בטא | SQLite לכל סשן (`data/v2-sessions`). תמלילים וספירות הודעות. |
| **Hermes** | מתאם בטא | SQLite `~/.hermes/state.db`. תמלילים, מודל, טוקנים/עלות. |
| **Claude Code** | מתאם בטא | JSONL `~/.claude/projects/.../<id>.jsonl`. תמלילים, מודל, קריאות כלים וחשיבה, שימוש בטוקנים. |
| **Codex** | מתאם בטא | Rollout JSONL `~/.codex/sessions/...`. תמלילים, מודל, קריאות כלים, שימוש בטוקנים. |
| **Cursor** | מתאם בטא | SQLite `state.vscdb`. תמלילי צ'אט/קומפוזר, מודל. |
| **Aider** | מתאם בטא | `.aider.chat.history.md` לכל פרויקט. תמלילים, מודל, ספירות טוקנים. |
| **Goose** | מתאם בטא | SQLite `~/.local/share/goose`. תמלילים, מודל, קריאות כלים, סכומי טוקנים. |
| **opencode** | מתאם בטא | SQLite `~/.local/share/opencode`. תמלילים, מודל, קריאות כלים, טוקנים ועלות. |
| **Qwen Code** | מתאם בטא | JSONL `~/.qwen/projects/.../chats`. תמלילים, מודל, קריאות כלים, שימוש בטוקנים. |

"מתאם בטא" פירושו ש-ClawMetry מגיע עם קורא לפורמט הדיסק הייחודי של אותה סביבת ריצה, כל אחד נבנה ואומת מול התקנה אמיתית על מחשב אמיתי (ראו `tests/fixtures/runtimes/<rt>/`). המתאמים הם לקריאה בלבד; כל אחד כן לגבי מה שסביבת הריצה שלו אכן מאחסנת (לדוגמה, PicoClaw/NanoClaw/Cursor אינם כותבים עלות טוקן לדיסק). כאשר מספר סביבות ריצה רצות על אותו צומת, מחליף סביבות הריצה מצמצם את תצוגת הסשנים לאחת לצלילה עמוקה נוחה.

## מעקב אחרי כל סוכן SDK, ייחוס עלות חוץ-לולאה

סביבות הריצה לעיל כולן כותבות סשנים לדיסק. **סוכן הייצור שלכם**, זה שבניתם על OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, או לולאת `httpx` פשוטה, לא עושה זאת. מיירט ה-zero-config של ClawMetry עדיין לוכד את קריאות ה-LLM שלו (עלות, טוקנים, זמן תגובה, שגיאות) על ידי תיקוני קוף של `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (או משתנה הסביבה `CLAWMETRY_SOURCE=support-agent`) מתייג כל קריאה עם **מקור בשם**, כך שכל מוצר שאתם מריצים מופיע כשורה ייחוסית-עלות עצמאית בכרטיס **🔌 Out-loop sources** בלוח Overview של לוח הבקרה, כולל קריאות, ספקים, זמן תגובה ושיעור שגיאות לכל סוכן. לא הוגדר מקור? הקריאות עדיין נעקבות; הכרטיס פשוט נשאר מוסתר.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

זוהי אותה שכבת נתונים שמתאמי סביבות הריצה מזינים (DuckDB ותמונת מצב ענן), כך שמקורות חוץ-לולאה מסתנכרנים ללוח הבקרה בענן כמו כל שאר הנתונים, עם הצפנה מקצה לקצה.

## OpenTelemetry — ניטרלי לספק, שלחו את העקבות שלכם לכל מקום

ClawMetry מדבר **OpenTelemetry** בשני הכיוונים, תוך שימוש ב-**GenAI semantic conventions**, כך שעקבות הסוכן שלכם לעולם אינן נעולות בכלי אחד.

**ייצוא** כל סשן, קריאות LLM, כלים, תת-סוכנים, טוקנים ועלות, כ-OTLP/HTTP GenAI spans לכל קולקטור (Datadog, Grafana, Honeycomb, או OTel Collector משלכם):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

כותרות אימות ומרווח בדיקות הם משתני סביבה אופציונליים:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**קליטה** — מקלט ה-OTLP המובנה מקבל עקבות ומדדים מכל מקום אחר בנתיבים `/v1/traces` ו-`/v1/metrics` (`pip install clawmetry[otel]` לקליטת protobuf).

אתם מקבלים את לוח בקרת ClawMetry הזמין מקומית ללא הגדרות **וגם** את הנתונים שלכם בכל backend שהצוות שלכם כבר מפעיל, ללא נעילה ללא צורך להתקין סוכן שני.

## הגדרות תצורה

רוב האנשים אינם זקוקים להגדרות תצורה. ClawMetry מזהה אוטומטית את סביבת העבודה, היומנים, הסשנים והמשימות המתוזמנות שלכם.

אם אתם זקוקים להתאמה אישית:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

כל האפשרויות: `clawmetry --help`

## ערוצים נתמכים

ClawMetry מציג פעילות בזמן אמת עבור כל ערוץ OpenClaw שהגדרתם. רק ערוצים שמוגדרים בפועל ב-`openclaw.json` שלכם מופיעים בדיאגרמת ה-Flow, ערוצים שאינם מוגדרים מוסתרים אוטומטית.

לחצו על כל צומת ערוץ ב-Flow כדי לראות תצוגת בועות צ'אט בזמן אמת עם ספירות הודעות נכנסות/יוצאות.

| ערוץ | סטטוס | חלון קופץ בזמן אמת | הערות |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ מלא | ✅ | הודעות, סטטיסטיקות, רענון כל 10 שניות |
| 💬 **iMessage** | ✅ מלא | ✅ | קורא ישירות מ-`~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ מלא | ✅ | דרך WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ מלא | ✅ | דרך signal-cli |
| 🟣 **Discord** | ✅ מלא | ✅ | זיהוי Guild וערוץ |
| 🟪 **Slack** | ✅ מלא | ✅ | זיהוי Workspace וערוץ |
| 🌐 **Webchat** | ✅ מלא | ✅ | סשני ממשק web מובנה |
| 📡 **IRC** | ✅ מלא | ✅ | ממשק בועות בסגנון טרמינל |
| 🍏 **BlueBubbles** | ✅ מלא | ✅ | iMessage דרך BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ מלא | ✅ | דרך webhooks של Chat API |
| 🟣 **MS Teams** | ✅ מלא | ✅ | דרך תוסף bot של Teams |
| 🔷 **Mattermost** | ✅ מלא | ✅ | צ'אט צוות self-hosted |
| 🟩 **Matrix** | ✅ מלא | ✅ | מבוזר, תמיכת E2EE |
| 🟢 **LINE** | ✅ מלא | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ מלא | ✅ | הודעות ישירות NIP-04 מבוזרות |
| 🟣 **Twitch** | ✅ מלא | ✅ | צ'אט דרך חיבור IRC |
| 🔷 **Feishu/Lark** | ✅ מלא | ✅ | מנוי אירועי WebSocket |
| 🔵 **Zalo** | ✅ מלא | ✅ | Zalo Bot API |

> **זיהוי אוטומטי:** ClawMetry קורא את ה-`~/.openclaw/openclaw.json` שלכם ומרנדר רק את הערוצים שהגדרתם בפועל. אין צורך בהגדרה ידנית.

## פריסת Docker

רוצים להריץ את ClawMetry בתוך קונטיינר? אין בעיה! 🐳

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

> **הערה:** בעת הרצה ב-Docker, הרכיבו את ספריות הנתונים והיומנים של הסוכן שלכם (לדוגמה `~/.openclaw`, `~/.claude`, `~/.codex`) כך ש-ClawMetry יוכל לזהות אוטומטית את ההגדרה שלכם.

## דרישות

- Python 3.8+
- Flask (מותקן אוטומטית דרך pip)
- סביבת ריצה של סוכן בינה מלאכותית על אותו מחשב: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, או PicoClaw (או volumes מורכבים עבור Docker)
- Linux או macOS

## תמיכה ב-NemoClaw / OpenShell

ClawMetry מזהה אוטומטית את [NemoClaw](https://github.com/NVIDIA/NemoClaw), עטיפת האבטחה הארגונית של NVIDIA עבור OpenClaw, המריצה סוכנים בתוך קונטיינרי OpenShell בארגז חול.

ברוב המקרים אין צורך בהגדרה נוספת. דמון הסנכרון מזהה אוטומטית קבצי סשן בין אם הם נמצאים ב-`~/.openclaw/` על המארח ובין אם בתוך קונטיינר OpenShell.

### כיצד זה עובד

ClawMetry מזהה NemoClaw בשתי דרכים:

1. **זיהוי קובץ בינארי** — בודק אם קיים ה-CLI של `nemoclaw` ומריץ `nemoclaw status` לקבלת מידע על ארגז החול
2. **זיהוי קונטיינר** — סורק קונטיינרי Docker פעילים לאיתור תמונות `openshell`, `nemoclaw` או `ghcr.io/nvidia/`, ואז קורא סשנים דרך הרכבות volume או `docker cp`

קבצי סשן שסונכרנו מקונטיינרי NemoClaw מתויגים עם מטא-נתונים `runtime=nemoclaw` ו-`container_id` בלוח הבקרה בענן, כך שתוכלו להבחין בינם לבין סשני OpenClaw רגילים במבט ראשון.

### הגדרה מומלצת: דמון סנכרון על המארח

לחוויה הטובה ביותר, הריצו את דמון הסנכרון של ClawMetry על **מחשב המארח** (לא בתוך ארגז החול). פעולה זו מונעת הגבלות מדיניות הרשת של NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

דמון הסנכרון יאתר אוטומטית סשנים בתוך כל קונטיינרי OpenShell פעילים.

### אופציונלי: שם ארגז חול מפורש

אם הזיהוי האוטומטי אינו פועל, הפנו את ClawMetry לארגז החול הנכון:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### הרצה בתוך ארגז החול (מתקדם)

אם אתם חייבים להריץ את דמון הסנכרון **בתוך** ארגז החול של OpenShell, הוסיפו כלל יציאה זה למדיניות הרשת של NemoClaw שלכם כדי שיוכל להגיע ל-API של קליטת ClawMetry:

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

### יציאות ונקודות קצה

| נקודת קצה | יציאה | פרוטוקול | נדרש |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | כן (דמון סנכרון ← ענן) |
| `localhost:8900` | 8900 | HTTP | כן (ממשק לוח בקרה מקומי) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | לגילוי סשנים בקונטיינר |

דמון הסנכרון מבצע רק קריאות HTTPS יוצאות אל `ingest.clawmetry.com`. אין צורך ביציאות נכנסות.

---

## פריסת ענן

ראו את **[מדריך בדיקות הענן](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** עבור מנהרות SSH, פרוקסי הפוך ו-Docker.

## בדיקות

פרויקט זה נבדק עם BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## טלמטריה

ClawMetry שולח פינג אנונימי אחד של "הרצה ראשונה" אל
`https://app.clawmetry.com/api/install` בפעם הראשונה שאתם מריצים את
ה-CLI של `clawmetry` על מחשב חדש. אנו משתמשים בזה לספירת התקנות (מדד
השיווק היחיד שיש לנו עבור פרויקט קוד פתוח) ולהבנה אילו frameworks
של סוכנים מותקנים אצל המשתמשים שלנו.

**POST אחד בלבד לכל התקנה**, המכיל:

| שדה | דוגמה | מדוע |
|---|---|---|
| `install_id` | UUID אקראי המאוחסן ב-`~/.clawmetry/install_id` | כפילויות; אינו מקושר לדואר האלקטרוני או api_key שלכם |
| `version` | `0.12.167` | אילו גרסאות קיימות בשימוש |
| `os` / `os_version` | `Darwin` / `25.3.0` | עדיפויות תמיכה בפלטפורמות |
| `python` | `3.11.15` | מטריצת תמיכה בגרסאות Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | עם אילו סוכנים כדאי לנו להשתלב בהמשך |
| `is_ci` / `ci_provider` | `true` / `github_actions` | הפרדת התקנות אנושיות מרעש CI |

**מה שאנו לא שולחים**: כתובת IP (הענן גוזר את קוד המדינה בצד השרת
מהבקשה ואז מסיר את ה-IP), שם מארח, שם משתמש, נתיב סביבת עבודה,
תוכן קבצים, api_key שלכם, דואר אלקטרוני שלכם, כל מידע אישי מזהה
או ספציפי לסביבת עבודה. ה-payload הגולמי ניתן לביקורת ב-
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**ביטול הסכמה** (כל אחת מאלה מבטלת אותו לצמיתות):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

כשל ברשת כאן לעולם אינו מונע מ-`clawmetry` לרוץ, הפינג הוא fire-and-forget על thread דמון עם timeout של 3 שניות.

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
  <sub>נבנה על ידי <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · חלק מאקוסיסטם <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
