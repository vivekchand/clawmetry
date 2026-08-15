<!-- i18n-src:c422fb7dd0da -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον πράκτορά σου να σκέφτεται.** Παρατηρησιμότητα σε πραγματικό χρόνο για **20 runtimes AI πρακτόρων**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 16 ακόμα. Ένας πίνακας ελέγχου για ολόκληρο τον στόλο πρακτόρων σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Καμία ρύθμιση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900** και έχεις τελειώσει.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 20 runtimes πρακτόρων

Το ClawMetry ξεκίνησε ως παρατηρησιμότητα για το OpenClaw, και τώρα μετράει ολόκληρο τον **στόλο πρακτόρων** σου σε έναν πίνακα ελέγχου, ανιχνεύοντας αυτόματα κάθε runtime στο μηχάνημά σου:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

Το OpenClaw και το NemoClaw είναι δωρεάν στην open-source εφαρμογή· τα υπόλοιπα runtimes ενεργοποιούνται με το ClawMetry Cloud ή με άδεια Pro αυτοφιλοξενίας. Άλλαξε runtime από την κεφαλίδα και κάθε καρτέλα, κόστος, tokens, εργαλεία, ίχνη, προσαρμόζεται σε αυτό το runtime. Δες το **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** για τον ακριβή διαχωρισμό δωρεάν/επί πληρωμή, τον πίνακα επιπέδων, τη μορφή του `/api/entitlement`, και το CLI `clawmetry license`.

## Τι παίρνεις

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει τα μηνύματα να ρέουν μέσα από κανάλια, brain, εργαλεία, και πίσω
- **Overview** — Έλεγχοι υγείας, χάρτης δραστηριότητας, μετρήσεις συνεδριών, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ανάλυση ανά ημέρα/εβδομάδα/μήνα
- **Sessions** — Ενεργές συνεδρίες πράκτορα με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Ροή logs σε πραγματικό χρόνο με έγχρωμη κωδικοποίηση
- **Memory** — Περιήγηση στα SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή τύπου φούσκας συνομιλίας για ανάγνωση ιστορικού συνεδριών
- **Alerts** — Όρια προϋπολογισμού, σκανδάλες ποσοστού σφαλμάτων, εντοπισμός εκτός σύνδεσης πράκτορα· δρομολόγηση σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Φραγμός καταστροφικών διαγραφών, force pushes, μεταλλάξεων βάσης δεδομένων, sudo, εγκαταστάσεων πακέτων, κλήσεων δικτύου πίσω από έγκριση με ένα κλικ

## Στιγμιότυπα οθόνης

### 🧠 Brain — Ζωντανή ροή συμβάντων πράκτορα
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Χρήση tokens & περίληψη συνεδρίας
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Ροή κλήσεων εργαλείων σε πραγματικό χρόνο
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ανάλυση κόστους ανά μοντέλο & συνεδρία
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Περιηγητής αρχείων χώρου εργασίας
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Στάση ασφαλείας & αρχείο καταγραφής ελέγχου
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Όρια προϋπολογισμού, σκανδάλες ποσοστού σφαλμάτων, webhooks σε Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Φραγμός επικίνδυνων κλήσεων εργαλείων πίσω από χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Φραγμός πριν την εκτέλεση για το Claude Code** — μία εντολή εγκαθιστά ένα
PreToolUse hook που θέτει σε παύση τις αντίστοιχες κλήσεις εργαλείων *πριν*
εκτελεστούν και περιμένει την απόφασή σου (ένα άγγιγμα από το τηλέφωνό σου με
ενεργοποιημένες τις [ειδοποιήσεις push μέσω cloud](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ένα deny φράζει μόνο εκείνη τη μία κλήση εργαλείου, ο πράκτορας διατηρεί τη
συνεδρία του και μπορεί να δοκιμάσει άλλη προσέγγιση. Η έγκριση από το
τηλέφωνό σου παρακάμπτει την ίδια την προτροπή δικαιωμάτων του Claude Code
(έχεις ήδη απαντήσει). Τα εργαλεία που δεν ταιριάζουν κοστίζουν ~40ms και
περνούν στην κανονική ροή δικαιωμάτων του Claude Code. Παίρνεις επίσης
ειδοποίηση push στο τηλέφωνο όταν το ίδιο το Claude Code περιμένει από σένα
(ειδοποιήσεις `permission_prompt` / `idle_prompt`).

## Εγκατάσταση

**Μονογραμμική (προτείνεται):**
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

Η εφαρμογή React v2 βρίσκεται στο `frontend/` και εξυπηρετείται στο `/v2` όταν
ο διακομιστής Flask ξεκινά με ενεργοποιημένο το v2.

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
`http://localhost:8900`, ώστε η εφαρμογή React να μπορεί να επικοινωνεί με τον
τοπικό διακομιστή Flask χωρίς επιπλέον ρύθμιση CORS.

Για να χτίσεις το bundle που συνοδεύει το πακέτο Python:

```bash
cd frontend
npm run build
```

Το bundle παραγωγής γράφεται στο `clawmetry/static/v2/dist/`.

## Συμβατότητα Runtime / Πράκτορα

Το ClawMetry παρατηρεί πολλά runtimes πρακτόρων AI, όχι μόνο το OpenClaw. Κάθε
runtime εκτός OpenClaw διαθέτει έναν αποκλειστικό προσαρμογέα ανάγνωσης που
μεταφράζει τη γηγενή μορφή συνεδρίας του στις ενοποιημένες μορφές του
ClawMetry· ο daemon τα εισάγει στο ίδιο κατάστημα DuckDB + στιγμιότυπο cloud,
με ετικέτα το runtime, και η καρτέλα Session replay εμφανίζει έναν
**επιλογέα runtime** όταν υπάρχει περισσότερο από ένα. Δες το
[`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα +
έναν οδηγό για την προσθήκη runtimes, και το
[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην
οικογένεια OpenClaw.

Τρέχεις το εργαλείο ασφάλειας πρακτόρων [numbat της Perplexity](https://github.com/perplexityai/numbat); Το ClawMetry εισάγει τα ευρήματα και τις αποφάσεις επιβολής του από το κουτί, δες το [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Πράκτορας | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Native | Runtime αναφοράς, ανιχνεύεται αυτόματα |
| **PicoClaw** | Beta προσαρμογέας | Επίπεδο `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta προσαρμογέας | SQLite ανά συνεδρία (`data/v2-sessions`). Transcripts + μετρήσεις μηνυμάτων. |
| **Hermes** | Beta προσαρμογέας | SQLite `~/.hermes/state.db`. Transcripts, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta προσαρμογέας | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, μοντέλο, κλήσεις εργαλείων + σκέψη, χρήση tokens. |
| **Codex** | Beta προσαρμογέας | Rollout JSONL `~/.codex/sessions/...`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta προσαρμογέας | SQLite `state.vscdb`. Transcripts chat/composer, μοντέλο. |
| **Aider** | Beta προσαρμογέας | `.aider.chat.history.md` ανά έργο. Transcripts, μοντέλο, μετρήσεις tokens. |
| **Goose** | Beta προσαρμογέας | SQLite `~/.local/share/goose`. Transcripts, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta προσαρμογέας | SQLite `~/.local/share/opencode`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Qwen Code** | Beta προσαρμογέας | JSONL `~/.qwen/projects/.../chats`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Pi** | Beta προσαρμογέας | JSONL `~/.pi/agent/sessions`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Deep Agents** | Beta προσαρμογέας | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **n8n** | Beta προσαρμογέας | SQLite `~/.n8n/database.sqlite`. Εκτελέσεις ροών εργασίας, εκτελέσεις κόμβων, προτροπές AI Agent, μοντέλο + tokens όπου το n8n τα καταγράφει. |
| **Antigravity** | Beta προσαρμογέας | Brain JSONL κάτω από `~/.gemini/<flavor>/brain/`. Συνομιλίες, βήματα εργαλείων, σκέψη, διαχωρισμός tokens Gemini ανά παραγωγή + κόστος, κατανάλωση background-generation. |
| **GitHub Copilot** | Beta προσαρμογέας | Copilot CLI `events.jsonl` κάτω από `~/.copilot/session-state/` + το βιβλίο χρήσης ανά κλήση `session-store.db`. Συνομιλίες, κλήσεις εργαλείων, δρομολόγηση μοντέλου, διαχωρισμός tokens με επίγνωση cache, κόστος AI-credit χρεωμένο από τον προμηθευτή. |
| **Grok** | Beta προσαρμογέας | xAI Grok Build CLI (δυαδικό αρχείο Rust κάτω από `~/.grok/bin/grok`): καθολικό αρχείο καταγραφής συμβάντων `~/.grok/logs/unified.jsonl` + ανά συνεδρία `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Συνομιλίες, διαχωρισμός tokens ανά γύρο, δρομολόγηση μοντέλου, και το εξερχόμενο φορτίο repo του CLI, σε στάδιο κάτω από `~/.grok/upload_queue/`, ώστε να βλέπεις τι έφυγε από το μηχάνημά σου. |

Το "Beta προσαρμογέας" σημαίνει ότι το ClawMetry παρέχει έναν αναγνώστη για
την πραγματική μορφή δίσκου εκείνου του runtime, χτισμένο + επαληθευμένο
έναντι πραγματικής εγκατάστασης σε πραγματικό μηχάνημα (δες
`tests/fixtures/runtimes/<rt>/`). Οι προσαρμογείς είναι μόνο για ανάγνωση·
καθένας είναι ειλικρινής για το τι πραγματικά αποθηκεύει το runtime του
(π.χ. τα PicoClaw/NanoClaw/Cursor δεν γράφουν κόστος tokens στον δίσκο). Όταν
τρέχουν πολλά runtimes σε έναν κόμβο, ο επιλογέας runtime περιορίζει την
προβολή συνεδριών σε ένα για μια καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε πράκτορα SDK — απόδοση κόστους out-loop

Τα παραπάνω runtimes γράφουν όλα συνεδρίες στον δίσκο. Ο δικός σου
**πράκτορας παραγωγής**, αυτός που έφτιαξες με το OpenAI Agents SDK, το
LangChain, το Vercel AI SDK, το LlamaIndex, το E2B, ή έναν απλό βρόχο
`httpx`, δεν το κάνει. Ο προσαρμογέας χωρίς ρύθμιση του ClawMetry εξακολουθεί
να καταγράφει τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα)
κάνοντας monkey-patching στα `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Το `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`)
επισημαίνει κάθε κλήση με μια **επώνυμη πηγή**, ώστε κάθε προϊόν που τρέχεις
να εμφανίζεται ως δική του πρωτοκλασάτη, με δυνατότητα απόδοσης κόστους
γραμμή στην κάρτα **🔌 Πηγές out-loop** του πίνακα ελέγχου στο Overview:
κλήσεις, πάροχοι, καθυστέρηση, ποσοστό σφαλμάτων ανά πράκτορα. Δεν έχει
οριστεί πηγή; Οι κλήσεις εξακολουθούν να παρακολουθούνται, η κάρτα απλώς
παραμένει κρυμμένη.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι προσαρμογείς runtime
(DuckDB → στιγμιότυπο cloud), οπότε οι πηγές out-loop συγχρονίζονται με τον
πίνακα ελέγχου cloud όπως όλα τα υπόλοιπα, με κρυπτογράφηση από άκρο σε άκρο.

## OpenTelemetry — ουδέτερο ως προς τον προμηθευτή, στείλε τα ίχνη σου οπουδήποτε

Το ClawMetry μιλάει **OpenTelemetry** και προς τις δύο κατευθύνσεις,
χρησιμοποιώντας τις **σημασιολογικές συμβάσεις GenAI**, ώστε τα ίχνη του
πράκτορά σου να μην κλειδώνονται ποτέ σε ένα μόνο εργαλείο.

**Εξαγωγή** κάθε συνεδρίας, κλήσεις LLM, εργαλεία, υπο-πράκτορες, tokens,
κόστος, ως OTLP/HTTP GenAI spans σε οποιονδήποτε συλλέκτη (Datadog, Grafana,
Honeycomb, ή τον δικό σου OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες πιστοποίησης και το διάστημα ψηφοφορίας είναι προαιρετικές
μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Εισαγωγή** — ο ενσωματωμένος δέκτης OTLP δέχεται ίχνη, logs, και μετρήσεις
από οτιδήποτε άλλο στα `/v1/traces`, `/v1/logs`, και `/v1/metrics`. Κατεύθυνε
οποιαδήποτε εφαρμογή με OpenTelemetry instrumentation προς αυτόν:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Τα ίχνη και τα logs OTLP/JSON λειτουργούν με απλό `pip install clawmetry`,
χωρίς extras. Η εισαγωγή Protobuf (και οι μετρήσεις OTLP/JSON) χρειάζονται
`pip install clawmetry[otel]`. Μια εφαρμογή που ορίζει το δικό της
`service.name` εμφανίζεται ως δικός της πράκτορας στον επιλογέα runtime, με
το κόστος και τα tokens της.

Παίρνεις τον πίνακα ελέγχου ClawMetry χωρίς ρύθμιση, τοπικό-πρώτα, **και**
τα δεδομένα σου σε όποιο backend ήδη τρέχει η ομάδα σου, χωρίς κλείδωμα,
χωρίς δεύτερο πράκτορα για εγκατάσταση.

## Ρύθμιση

Οι περισσότεροι δεν χρειάζονται καμία ρύθμιση. Το ClawMetry ανιχνεύει
αυτόματα τον χώρο εργασίας, τα logs, τις συνεδρίες, και τα crons σου.

Αν χρειάζεσαι προσαρμογή:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα κανάλια

Το ClawMetry δείχνει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχεις
ρυθμίσει. Μόνο τα κανάλια που είναι πραγματικά ρυθμισμένα στο `openclaw.json`
σου εμφανίζονται στο διάγραμμα Flow, τα μη ρυθμισμένα κρύβονται αυτόματα.

Κάνε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δεις μια ζωντανή
προβολή φούσκας συνομιλίας με μετρήσεις εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση 10s |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Ανίχνευση guild + καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Ανίχνευση χώρου εργασίας + καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένες συνεδρίες web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | UI φούσκας τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω πρόσθετου bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Αυτοφιλοξενούμενη συνομιλία ομάδας |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα NIP-04 DMs |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Συνομιλία μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή συμβάντων WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματη ανίχνευση:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json`
> σου και αποδίδει μόνο τα κανάλια που έχεις πραγματικά ρυθμίσει. Δεν
> απαιτείται χειροκίνητη ρύθμιση.

## Ανάπτυξη με Docker

Θέλεις να τρέξεις το ClawMetry σε container; Κανένα πρόβλημα! 🐳

**Γρήγορη εκκίνηση με Docker:**

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

> **Σημείωση:** Όταν τρέχεις σε Docker, κάνε mount τους καταλόγους δεδομένων
> + logs του πράκτορά σου (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε
> το ClawMetry να μπορεί να ανιχνεύσει αυτόματα τη ρύθμισή σου.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα runtime πράκτορα AI στο ίδιο μηχάνημα: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, ή QM (ή προσαρτημένοι τόμοι για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry ανιχνεύει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw), τον εταιρικό περιτύλιγμα ασφαλείας της NVIDIA για το OpenClaw που τρέχει πράκτορες μέσα σε sandboxed containers OpenShell.

Δεν χρειάζεται επιπλέον ρύθμιση στις περισσότερες περιπτώσεις. Ο daemon
συγχρονισμού ανακαλύπτει αυτόματα αρχεία συνεδρίας είτε βρίσκονται στο
`~/.openclaw/` στον host είτε μέσα σε ένα container OpenShell.

### Πώς λειτουργεί

Το ClawMetry ανιχνεύει το NemoClaw με δύο τρόπους:

1. **Ανίχνευση δυαδικού αρχείου** — ελέγχει για το CLI `nemoclaw` και τρέχει
   `nemoclaw status` για να πάρει πληροφορίες sandbox
2. **Ανίχνευση container** — σαρώνει τα container Docker που τρέχουν για
   εικόνες `openshell`, `nemoclaw`, ή `ghcr.io/nvidia/`, έπειτα διαβάζει τις
   συνεδρίες μέσω προσαρτημένων τόμων ή `docker cp`

Τα αρχεία συνεδρίας που συγχρονίζονται από containers NemoClaw επισημαίνονται
με `runtime=nemoclaw` και μεταδεδομένα `container_id` στον πίνακα ελέγχου
cloud, ώστε να μπορείς να τα ξεχωρίσεις από τυπικές συνεδρίες OpenClaw με μια
ματιά.

### Προτεινόμενη ρύθμιση: daemon συγχρονισμού στον HOST

Για την καλύτερη εμπειρία, τρέξε τον daemon συγχρονισμού του ClawMetry στο
**μηχάνημα host** (όχι μέσα στο sandbox). Αυτό αποφεύγει τους περιορισμούς
πολιτικής δικτύου του NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο daemon συγχρονισμού θα βρει αυτόματα συνεδρίες μέσα σε οποιαδήποτε
τρέχοντα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν η αυτόματη ανίχνευση δεν λειτουργεί, κατεύθυνε το ClawMetry στο σωστό
sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (προχωρημένο)

Αν πρέπει να τρέξεις τον daemon συγχρονισμού **μέσα** στο sandbox OpenShell,
πρόσθεσε αυτόν τον κανόνα εξόδου στην πολιτική δικτύου του NemoClaw ώστε να
μπορεί να φτάσει στο API εισαγωγής του ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ναι (daemon συγχρονισμού → cloud) |
| `localhost:8900` | 8900 | HTTP | Ναι (τοπικό UI πίνακα ελέγχου) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Για ανακάλυψη συνεδριών container |

Ο daemon συγχρονισμού κάνει μόνο εξερχόμενες κλήσεις HTTPS προς
`ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη Cloud

Δες τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, reverse proxy, και Docker.

## Δοκιμές

Αυτό το έργο δοκιμάζεται με το BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry στέλνει ανώνυμα σήματα κύκλου ζωής εγκατάστασης στο
`https://app.clawmetry.com/api/install`: ένα σήμα `install` την πρώτη φορά
που τρέχεις το CLI `clawmetry` σε ένα νέο μηχάνημα, ένα σήμα `update` την
πρώτη εκτέλεση μετά την αναβάθμιση σε νέα έκδοση, και ένα σήμα `onboarded`
όταν ολοκληρώνεις την επιλογή onboarding μέσα στον πίνακα ελέγχου. Το
χρησιμοποιούμε για να μετρήσουμε πραγματικές εγκαταστάσεις (οι ακατέργαστοι
αριθμοί λήψεων PyPI είναι ~98% mirrors, CI, και επανα-λήψεις αυτόματης
ενημέρωσης) και για να μάθουμε ποια πλαίσια πρακτόρων και εκδόσεις είναι
πραγματικά σε χρήση.

**Το πολύ ένα POST ανά συμβάν κύκλου ζωής ανά έκδοση**, που περιέχει:

| Πεδίο | Παράδειγμα | Γιατί |
|---|---|---|
| `install_id` | τυχαίο UUID αποθηκευμένο στο `~/.clawmetry/install_id` | αποφυγή διπλοεγγραφών· ανώνυμο μέχρι να συνδέσεις ρητά το Cloud sync (το πιστοποιημένο heartbeat του daemon φέρει τότε το αναγνωριστικό, συνδέοντας αυτή την εγκατάσταση με τον λογαριασμό σου) |
| `event` | `install` / `update` / `onboarded` | νέα εγκατάσταση έναντι αναβάθμισης υπάρχουσας |
| `version` | `0.12.167` | ποιες εκδόσεις είναι σε χρήση |
| `os` / `os_version` | `Darwin` / `25.3.0` | προτεραιότητες υποστήριξης πλατφόρμας |
| `python` | `3.11.15` | πίνακας υποστήριξης εκδόσεων Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | με ποιους πράκτορες πρέπει να ενσωματωθούμε στη συνέχεια |
| `is_ci` / `ci_provider` | `true` / `github_actions` | διαχωρισμός ανθρώπινων εγκαταστάσεων από θόρυβο CI |

**Τι ΔΕΝ στέλνουμε**: IP (το cloud προκύπτει τον κωδικό χώρας
από το αίτημα στην πλευρά του διακομιστή, έπειτα απορρίπτει το IP),
όνομα host, όνομα χρήστη, διαδρομή χώρου εργασίας, περιεχόμενο αρχείων, το
api_key σου, το email σου, οτιδήποτε προσωπικό ή σχετικό με τον χώρο
εργασίας. Το ωφέλιμο φορτίο επικοινωνίας είναι ελέγξιμο στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση** (οποιοδήποτε από αυτά την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Μια αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ την εκτέλεση του `clawmetry`, το
σήμα είναι fire-and-forget σε νήμα daemon με χρονικό όριο 3 δευτερολέπτων.

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
  <strong>🦞 Δες τον πράκτορά σου να σκέφτεται</strong><br>
  <sub>Χτισμένο από τον <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
