<!-- i18n-src:9a05336fbdc1 -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον agent σου να σκέφτεται.** Παρατήρηση σε πραγματικό χρόνο για **14 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 10 ακόμα. Ένα dashboard για ολόκληρο τον στόλο agents σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενικές ρυθμίσεις. Αυτόματη ανίχνευση όλων.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900** και έχεις τελειώσει.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 14 agent runtimes

Το ClawMetry ξεκίνησε ως παρατήρηση για το OpenClaw, και τώρα μετράει ολόκληρο τον **στόλο agents** σου σε ένα dashboard, ανιχνεύοντας αυτόματα κάθε runtime στο μηχάνημά σου:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

Τα OpenClaw και NemoClaw είναι δωρεάν στην open-source εφαρμογή· τα υπόλοιπα runtimes ενεργοποιούνται με το ClawMetry Cloud ή με μια self-hosted άδεια Pro. Άλλαξε runtime από την κεφαλίδα και κάθε καρτέλα -κόστος, tokens, εργαλεία, ίχνη- προσαρμόζεται σε αυτό το runtime. Δες το **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** για τον ακριβή διαχωρισμό δωρεάν/επί πληρωμή, τον πίνακα επιπέδων, τη μορφή του `/api/entitlement`, και το CLI `clawmetry license`.

## Τι παίρνεις

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει τα μηνύματα να ρέουν μέσα από κανάλια, brain, εργαλεία, και πίσω
- **Overview** — Έλεγχοι υγείας, heatmap δραστηριότητας, πλήθος συνεδριών, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ημερήσια/εβδομαδιαία/μηνιαία ανάλυση
- **Sessions** — Ενεργές συνεδρίες agent με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Έγχρωμη ροή logs σε πραγματικό χρόνο
- **Memory** — Περιήγηση σε SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή τύπου chat για ανάγνωση ιστορικού συνεδριών
- **Alerts** — Όρια προϋπολογισμού, ενεργοποιητές ρυθμού σφαλμάτων, ανίχνευση offline agent· δρομολόγηση σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Φραγή καταστροφικών διαγραφών, force pushes, μεταβολών βάσης δεδομένων, sudo, εγκαταστάσεων πακέτων, κλήσεων δικτύου πίσω από έγκριση με ένα κλικ

## Στιγμιότυπα

### 🧠 Brain — Ζωντανή ροή συμβάντων agent
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Χρήση tokens & σύνοψη συνεδρίας
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Ροή κλήσεων εργαλείων σε πραγματικό χρόνο
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ανάλυση κόστους ανά μοντέλο & συνεδρία
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Περιηγητής αρχείων χώρου εργασίας
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Στάση ασφάλειας & αρχείο ελέγχου
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Όρια προϋπολογισμού, ενεργοποιητές ρυθμού σφαλμάτων, webhooks προς Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Φραγή ριψοκίνδυνων κλήσεων εργαλείων πίσω από χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Φραγή πριν την εκτέλεση για το Claude Code** — μία εντολή εγκαθιστά ένα
PreToolUse hook που σταματάει τις κλήσεις εργαλείων που ταιριάζουν *πριν* εκτελεστούν και περιμένει
την απόφασή σου (ένα άγγιγμα από το κινητό σου με
[ειδοποιήσεις push στο cloud](https://app.clawmetry.com/push) ενεργοποιημένες):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Μια απόρριψη φράζει μόνο εκείνη τη μία κλήση εργαλείου — ο agent κρατά τη συνεδρία του και μπορεί να
δοκιμάσει άλλη προσέγγιση. Η έγκριση από το κινητό σου παρακάμπτει το δικό του παράθυρο άδειας
του Claude Code (το απάντησες ήδη). Τα εργαλεία που δεν ταιριάζουν κοστίζουν περίπου 40ms και
περνάνε στην κανονική ροή αδειών του Claude Code. Παίρνεις επίσης μια ειδοποίηση push στο κινητό όταν
το ίδιο το Claude Code περιμένει εσένα (ειδοποιήσεις `permission_prompt` /
`idle_prompt`).

## Εγκατάσταση

**Με μία εντολή (προτείνεται):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Από τον πηγαίο κώδικα:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Ανάπτυξη v2 Frontend

Η εφαρμογή React v2 βρίσκεται στο `frontend/` και σερβίρεται στο `/v2` όταν ο Flask
server ξεκινάει με το v2 ενεργοποιημένο.

Χρησιμοποίησε δύο τερματικά κατά την ανάπτυξη:

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

Άνοιξε το `http://localhost:5173/v2/`. Το Vite προωθεί τα αιτήματα `/api` στο
`http://localhost:8900`, ώστε η εφαρμογή React να μπορεί να επικοινωνεί με τον τοπικό Flask server
χωρίς επιπλέον ρύθμιση CORS.

Για να χτίσεις το bundle που συνοδεύει το πακέτο Python:

```bash
cd frontend
npm run build
```

Το production bundle γράφεται στο `clawmetry/static/v2/dist/`.

## Συμβατότητα Runtime / Agent

Το ClawMetry παρατηρεί πολλά AI-agent runtimes, όχι μόνο το OpenClaw. Κάθε runtime εκτός OpenClaw διαθέτει έναν αφοσιωμένο reader adapter που μεταφράζει τη δική του εγγενή μορφή συνεδρίας στα ενοποιημένα σχήματα του ClawMetry· ο daemon τα εισάγει στο ίδιο DuckDB store + στιγμιότυπο cloud, με ετικέτα το runtime, και η καρτέλα Session replay εμφανίζει έναν **επιλογέα runtime** όταν υπάρχει περισσότερο από ένα. Δες το [`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα + έναν οδηγό προσθήκης runtimes, και το [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην οικογένεια OpenClaw.

| Runtime / Agent | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Native | Runtime αναφοράς, αυτόματη ανίχνευση |
| **PicoClaw** | Beta adapter | Επίπεδο `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta adapter | SQLite ανά συνεδρία (`data/v2-sessions`). Transcripts + πλήθος μηνυμάτων. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, μοντέλο, κλήσεις εργαλείων + σκέψη, χρήση tokens. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Transcripts chat/composer, μοντέλο. |
| **Aider** | Beta adapter | `.aider.chat.history.md` ανά έργο. Transcripts, μοντέλο, μετρήσεις tokens. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Εκτελέσεις workflow, εκτελέσεις κόμβων, prompts AI Agent, μοντέλο + tokens όπου το n8n τα καταγράφει. |

"Beta adapter" σημαίνει ότι το ClawMetry παρέχει έναν reader για την πραγματική μορφή αρχείων εκείνου του runtime, χτισμένο + επαληθευμένο πάνω σε πραγματική εγκατάσταση σε πραγματικό μηχάνημα (δες `tests/fixtures/runtimes/<rt>/`). Οι adapters είναι μόνο για ανάγνωση· ο καθένας είναι ειλικρινής για το τι πραγματικά αποθηκεύει το runtime του (π.χ. τα PicoClaw/NanoClaw/Cursor δεν γράφουν κόστος tokens στον δίσκο). Όταν τρέχουν πολλά runtimes σε έναν κόμβο, ο επιλογέας runtime περιορίζει την προβολή συνεδριών σε ένα για μια καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε SDK agent — απόδοση κόστους εκτός βρόχου

Τα παραπάνω runtimes γράφουν όλα συνεδρίες στον δίσκο. Ο δικός σου **agent παραγωγής** — αυτός που έχτισες πάνω στο OpenAI Agents SDK, στο LangChain, στο Vercel AI SDK, στο LlamaIndex, στο E2B, ή σε έναν απλό βρόχο `httpx` — δεν το κάνει. Ο interceptor μηδενικής ρύθμισης του ClawMetry καταγράφει και πάλι τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα) κάνοντας monkey-patch στα `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Η `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`) επισημαίνει κάθε κλήση με μια **ονομασμένη πηγή**, ώστε κάθε προϊόν που τρέχεις να εμφανίζεται ως δική του πρωτοκλασάτη, αποδοτέα σε κόστος γραμμή στην κάρτα **🔌 Πηγές εκτός βρόχου** του Overview στο dashboard — κλήσεις, πάροχοι, καθυστέρηση, ρυθμός σφαλμάτων ανά agent. Δεν έχεις ορίσει πηγή; Οι κλήσεις εξακολουθούν να καταγράφονται, απλώς η κάρτα παραμένει κρυφή.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι adapters runtime (DuckDB → στιγμιότυπο cloud), οπότε οι πηγές εκτός βρόχου συγχρονίζονται με το dashboard cloud όπως όλα τα υπόλοιπα, με κρυπτογράφηση άκρου-σε-άκρο.

## OpenTelemetry — ουδέτερο ως προς τον πάροχο, στείλε τα ίχνη σου όπου θέλεις

Το ClawMetry μιλάει **OpenTelemetry** και προς τις δύο κατευθύνσεις, χρησιμοποιώντας τις **συμβάσεις σημασιολογίας GenAI**, ώστε τα ίχνη του agent σου να μην κλειδώνονται ποτέ σε ένα μόνο εργαλείο.

**Εξαγωγή** κάθε συνεδρίας -κλήσεις LLM, εργαλεία, sub-agents, tokens, κόστος- ως spans OTLP/HTTP GenAI προς οποιονδήποτε collector (Datadog, Grafana, Honeycomb, ή τον δικό σου OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες αυθεντικοποίησης και το διάστημα polling είναι προαιρετικές μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Εισαγωγή** — ο ενσωματωμένος OTLP receiver δέχεται ίχνη και μετρικές από οτιδήποτε άλλο στα `/v1/traces` και `/v1/metrics` (`pip install clawmetry[otel]` για εισαγωγή protobuf).

Παίρνεις το μηδενικής ρύθμισης, τοπικό-πρώτα dashboard ClawMetry **και** τα δεδομένα σου σε όποιο backend ήδη χρησιμοποιεί η ομάδα σου — χωρίς εγκλωβισμό, χωρίς δεύτερο agent για εγκατάσταση.

## Ρύθμιση

Οι περισσότεροι δεν χρειάζονται καμία ρύθμιση. Το ClawMetry ανιχνεύει αυτόματα τον χώρο εργασίας σου, τα logs, τις συνεδρίες, και τα crons.

Αν χρειάζεσαι προσαρμογή:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα Κανάλια

Το ClawMetry δείχνει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχεις ρυθμίσει. Μόνο τα κανάλια που είναι πράγματι ρυθμισμένα στο `openclaw.json` σου εμφανίζονται στο διάγραμμα Flow — τα μη ρυθμισμένα κρύβονται αυτόματα.

Κάνε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δεις μια ζωντανή προβολή φυσαλίδων συνομιλίας με μετρήσεις εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση 10s |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Ανίχνευση guild + καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Ανίχνευση workspace + καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένες συνεδρίες web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | Διεπαφή φυσαλίδων τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω plugin bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Self-hosted ομαδική συνομιλία |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα DMs NIP-04 |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Συνομιλία μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή συμβάντων WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματη ανίχνευση:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json` σου και αποδίδει μόνο τα κανάλια που έχεις πράγματι ρυθμίσει. Δεν απαιτείται χειροκίνητη ρύθμιση.

## Ανάπτυξη με Docker

Θέλεις να τρέξεις το ClawMetry σε container; Κανένα πρόβλημα! 🐳

**Γρήγορο ξεκίνημα με Docker:**

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

**Παράδειγμα Docker Compose:**

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

> **Σημείωση:** Όταν τρέχεις σε Docker, κάνε mount τους φακέλους δεδομένων + logs του agent σου (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε το ClawMetry να μπορεί να ανιχνεύσει αυτόματα τη ρύθμισή σου.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα AI agent runtime στο ίδιο μηχάνημα: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, ή n8n (ή mounted volumes για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry ανιχνεύει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw) — τον εταιρικό περιτύλιγμα ασφαλείας της NVIDIA για το OpenClaw που τρέχει agents μέσα σε sandboxed containers OpenShell.

Δεν χρειάζεται επιπλέον ρύθμιση στις περισσότερες περιπτώσεις. Ο sync daemon ανακαλύπτει αυτόματα τα αρχεία συνεδρίας είτε βρίσκονται στο `~/.openclaw/` στον host είτε μέσα σε ένα container OpenShell.

### Πώς λειτουργεί

Το ClawMetry ανιχνεύει το NemoClaw με δύο τρόπους:

1. **Ανίχνευση binary** — ελέγχει για το CLI `nemoclaw` και τρέχει `nemoclaw status` για να πάρει πληροφορίες sandbox
2. **Ανίχνευση container** — σαρώνει τα τρέχοντα containers Docker για εικόνες `openshell`, `nemoclaw`, ή `ghcr.io/nvidia/`, και στη συνέχεια διαβάζει συνεδρίες μέσω volume mounts ή `docker cp`

Τα αρχεία συνεδρίας που συγχρονίζονται από containers NemoClaw επισημαίνονται με μεταδεδομένα `runtime=nemoclaw` και `container_id` στο dashboard cloud, ώστε να μπορείς να τα ξεχωρίσεις από τις τυπικές συνεδρίες OpenClaw με μια ματιά.

### Προτεινόμενη ρύθμιση: sync daemon στον HOST

Για την καλύτερη εμπειρία, τρέξε τον sync daemon του ClawMetry στον **host μηχάνημα** (όχι μέσα στο sandbox). Αυτό αποφεύγει τους περιορισμούς πολιτικής δικτύου του NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο sync daemon θα βρει αυτόματα συνεδρίες μέσα σε οποιαδήποτε τρέχοντα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν η αυτόματη ανίχνευση δεν λειτουργεί, κατεύθυνε το ClawMetry στο σωστό sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (προχωρημένο)

Αν πρέπει να τρέξεις τον sync daemon **μέσα** στο sandbox OpenShell, πρόσθεσε αυτόν τον κανόνα εξόδου (egress) στην πολιτική δικτύου NemoClaw σου ώστε να μπορεί να φτάσει στο API εισαγωγής του ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Εφάρμοσέ το με:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Θύρες και endpoints

| Endpoint | Θύρα | Πρωτόκολλο | Απαιτείται |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ναι (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Ναι (τοπικό dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Για ανακάλυψη συνεδριών container |

Ο sync daemon κάνει μόνο εξερχόμενες κλήσεις HTTPS προς το `ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη σε Cloud

Δες τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, reverse proxy, και Docker.

## Δοκιμές

Αυτό το έργο δοκιμάζεται με το BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry στέλνει ένα μοναδικό ανώνυμο "first run" ping στο
`https://app.clawmetry.com/api/install` την πρώτη φορά που τρέχεις την
CLI `clawmetry` σε νέο μηχάνημα. Το χρησιμοποιούμε για να μετράμε εγκαταστάσεις (η
μόνη μετρική μάρκετινγκ που έχουμε για ένα έργο OSS) και για να μαθαίνουμε ποιά
frameworks agent έχουν εγκαταστήσει οι χρήστες μας.

**Ακριβώς ένα POST ανά εγκατάσταση**, που περιέχει:

| Πεδίο | Παράδειγμα | Γιατί |
|---|---|---|
| `install_id` | τυχαίο UUID αποθηκευμένο στο `~/.clawmetry/install_id` | αποφυγή διπλοεγγραφών· δεν συνδέεται με το email ή το api_key σου |
| `version` | `0.12.167` | ποιές εκδόσεις κυκλοφορούν |
| `os` / `os_version` | `Darwin` / `25.3.0` | προτεραιότητες υποστήριξης πλατφόρμας |
| `python` | `3.11.15` | πίνακας υποστήριξης εκδόσεων Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | με ποιούς agents πρέπει να ενσωματωθούμε στη συνέχεια |
| `is_ci` / `ci_provider` | `true` / `github_actions` | διαχωρισμός ανθρώπινων εγκαταστάσεων από θόρυβο CI |

**Τι ΔΕΝ στέλνουμε**: IP (το cloud προκύπτει τον κωδικό χώρας από την πλευρά του server
από το αίτημα, και μετά απορρίπτει το IP), hostname, username, διαδρομή χώρου εργασίας,
περιεχόμενο αρχείων, το api_key σου, το email σου, τίποτα PII ή
σχετικό με τον χώρο εργασίας. Το ωφέλιμο φορτίο (wire payload) είναι ελέγξιμο στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση (opt out)** (οποιοδήποτε από αυτά την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Μια αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ την εκτέλεση του `clawmetry` — το
ping γίνεται fire-and-forget σε ένα daemon thread με timeout 3 δευτερολέπτων.

## Ιστορικό Αστεριών

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια χρήσης

MIT

---

<p align="center">
  <strong>🦞 Δες τον agent σου να σκέφτεται</strong><br>
  <sub>Φτιαγμένο από τον <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
