<!-- i18n-src:0e34918f8f2e -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον agent σου να σκέφτεται.** Παρατηρησιμότητα σε πραγματικό χρόνο για **14 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 10 ακόμη. Ένα dashboard για ολόκληρο τον στόλο agents σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική διαμόρφωση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στη διεύθυνση **http://localhost:8900** και έτοιμο.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 14 agent runtimes

Το ClawMetry ξεκίνησε ως παρατηρησιμότητα για το OpenClaw, και τώρα μετράει ολόκληρο τον **στόλο agents** σου σε ένα dashboard, ανιχνεύοντας αυτόματα κάθε runtime στο μηχάνημά σου:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

Το OpenClaw και το NemoClaw είναι δωρεάν στην open-source εφαρμογή· τα υπόλοιπα runtimes ενεργοποιούνται με το ClawMetry Cloud ή με άδεια Pro σε self-hosted εγκατάσταση. Άλλαξε runtime από το header και κάθε καρτέλα, κόστος, tokens, εργαλεία, ίχνη, προσαρμόζεται αυτόματα σε αυτό το runtime. Δες το **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** για την ακριβή κατανομή δωρεάν/επί πληρωμή, τον πίνακα επιπέδων, τη μορφή του `/api/entitlement` και το CLI `clawmetry license`.

## Τι αποκτάς

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει τα μηνύματα να ρέουν μέσα από κανάλια, brain, εργαλεία και πίσω
- **Overview** — Έλεγχοι υγείας, χάρτης δραστηριότητας, πλήθος συνεδριών, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ημερήσια/εβδομαδιαία/μηνιαία ανάλυση
- **Sessions** — Ενεργές συνεδρίες agent με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Ζωντανή ροή logs με χρωματική κωδικοποίηση
- **Memory** — Περιήγηση στα SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή τύπου chat για ανάγνωση ιστορικού συνεδριών
- **Alerts** — Όρια προϋπολογισμού, ενεργοποιητές ποσοστού σφαλμάτων, εντοπισμός offline agent· δρομολόγηση σε Slack, Discord, PagerDuty, Telegram, Email
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

### 🔐 Security — Στάση ασφαλείας & αρχείο ελέγχου
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Όρια προϋπολογισμού, ενεργοποιητές ποσοστού σφαλμάτων, webhooks προς Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Φραγή ριψοκίνδυνων κλήσεων εργαλείων πίσω από χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Φραγή πριν την εκτέλεση για το Claude Code** — μία εντολή εγκαθιστά ένα
PreToolUse hook που παύει τις αντίστοιχες κλήσεις εργαλείων *πριν* εκτελεστούν και περιμένει
την απόφασή σου (ένα άγγιγμα από το κινητό σου με ενεργοποιημένες τις
[cloud ειδοποιήσεις push](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Μια απόρριψη φράζει μόνο εκείνη τη μία κλήση εργαλείου, ο agent διατηρεί τη
συνεδρία του και μπορεί να δοκιμάσει διαφορετική προσέγγιση. Η έγκριση από το κινητό σου παρακάμπτει
την ενσωματωμένη προτροπή δικαιωμάτων του Claude Code (την έχεις ήδη απαντήσει). Τα εργαλεία που δεν ταιριάζουν κοστίζουν ~40ms και
περνούν στην κανονική ροή δικαιωμάτων του Claude Code. Λαμβάνεις επίσης μια ειδοποίηση push στο κινητό σου όταν το ίδιο το Claude Code
περιμένει την απόφασή σου (ειδοποιήσεις `permission_prompt` /
`idle_prompt`).

## Εγκατάσταση

**One-liner (προτείνεται):**
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

Η εφαρμογή React v2 βρίσκεται στον φάκελο `frontend/` και σερβίρεται στο `/v2` όταν ο Flask
server εκκινείται με ενεργοποιημένο το v2.

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

Άνοιξε το `http://localhost:5173/v2/`. Το Vite προωθεί (proxy) τα αιτήματα `/api` στο
`http://localhost:8900`, ώστε η εφαρμογή React να μπορεί να επικοινωνεί με τον τοπικό Flask server
χωρίς επιπλέον ρύθμιση CORS.

Για να χτίσεις το πακέτο (bundle) που συνοδεύει το πακέτο Python:

```bash
cd frontend
npm run build
```

Το production bundle γράφεται στο `clawmetry/static/v2/dist/`.

## Συμβατότητα Runtime / Agent

Το ClawMetry παρατηρεί πολλά AI-agent runtimes, όχι μόνο το OpenClaw. Κάθε runtime εκτός OpenClaw διαθέτει έναν αφοσιωμένο αναγνώστη (reader adapter) που μεταφράζει τη δική του εγγενή μορφή συνεδρίας στις ενοποιημένες μορφές του ClawMetry· ο daemon τα εισάγει στο ίδιο DuckDB store + cloud snapshot, με ετικέτα το runtime, και η καρτέλα Session replay εμφανίζει έναν **επιλογέα runtime** όταν υπάρχει περισσότερο από ένα. Δες το [`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα + οδηγό προσθήκης runtimes, και το [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην οικογένεια OpenClaw.

Τρέχεις το εργαλείο ασφαλείας agent [numbat της Perplexity](https://github.com/perplexityai/numbat); Το ClawMetry εισάγει τα ευρήματα και τις αποφάσεις επιβολής του απευθείας, δες το [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Εγγενές | Runtime αναφοράς, ανιχνεύεται αυτόματα |
| **PicoClaw** | Beta adapter | Επίπεδο JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripts, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta adapter | SQLite ανά συνεδρία (`data/v2-sessions`). Transcripts + πλήθος μηνυμάτων. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, μοντέλο, κλήσεις εργαλείων + σκέψη, χρήση tokens. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Transcripts chat/composer, μοντέλο. |
| **Aider** | Beta adapter | `.aider.chat.history.md` ανά project. Transcripts, μοντέλο, μέτρηση tokens. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Εκτελέσεις ροών εργασίας, εκτελέσεις κόμβων, προτροπές AI Agent, μοντέλο + tokens όπου το n8n τα καταγράφει. |
| **Antigravity** | Beta adapter | Brain JSONL κάτω από το `~/.gemini/<flavor>/brain/`. Συνομιλίες, βήματα εργαλείων, σκέψη, ανάλυση tokens Gemini ανά παραγωγή + κόστος, κατανάλωση παρασκηνιακής παραγωγής. |
| **GitHub Copilot** | Beta adapter | `events.jsonl` του Copilot CLI κάτω από το `~/.copilot/session-state/` + το βιβλίο χρήσης ανά κλήση `session-store.db`. Συνομιλίες, κλήσεις εργαλείων, δρομολόγηση μοντέλου, ανάλυση tokens με επίγνωση cache, κόστος AI-credit χρεωμένο από τον προμηθευτή. |

"Beta adapter" σημαίνει ότι το ClawMetry διαθέτει αναγνώστη για την πραγματική μορφή αρχείων εκείνου του runtime στον δίσκο, χτισμένο + επαληθευμένο πάνω σε πραγματική εγκατάσταση σε πραγματικό μηχάνημα (δες `tests/fixtures/runtimes/<rt>/`). Οι adapters είναι μόνο για ανάγνωση· ο καθένας είναι ειλικρινής σχετικά με το τι πραγματικά αποθηκεύει το runtime του (π.χ. τα PicoClaw/NanoClaw/Cursor δεν γράφουν κόστος tokens στον δίσκο). Όταν τρέχουν πολλά runtimes σε έναν κόμβο, ο επιλογέας runtime περιορίζει την προβολή συνεδριών σε ένα για καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε SDK agent — απόδοση κόστους εκτός βρόχου

Τα παραπάνω runtimes γράφουν όλα συνεδρίες στον δίσκο. Ο δικός σου **παραγωγικός agent**, αυτός που έφτιαξες με το OpenAI Agents SDK, το LangChain, το Vercel AI SDK, το LlamaIndex, το E2B, ή έναν απλό βρόχο `httpx`, δεν το κάνει. Ο interceptor μηδενικής διαμόρφωσης του ClawMetry εξακολουθεί να συλλαμβάνει τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα) κάνοντας monkey-patch στα `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Η `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`) επισημαίνει κάθε κλήση με μια **ονομασμένη πηγή**, ώστε κάθε προϊόν που τρέχεις να εμφανίζεται ως δική του πρωτεύουσα, με δυνατότητα απόδοσης κόστους γραμμή στην κάρτα **🔌 Πηγές εκτός βρόχου** του Overview στο dashboard, κλήσεις, παρόχους, καθυστέρηση, ποσοστό σφαλμάτων ανά agent. Δεν έχεις ορίσει πηγή; Οι κλήσεις εξακολουθούν να παρακολουθούνται, απλώς η κάρτα παραμένει κρυφή.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι adapters runtime (DuckDB → cloud snapshot), οπότε οι πηγές εκτός βρόχου συγχρονίζονται στο cloud dashboard όπως όλα τα υπόλοιπα, με κρυπτογράφηση E2E.

## OpenTelemetry — ουδέτερο ως προς τον προμηθευτή, στείλε τα ίχνη σου οπουδήποτε

Το ClawMetry μιλά **OpenTelemetry** και προς τις δύο κατευθύνσεις, χρησιμοποιώντας τις **σημασιολογικές συμβάσεις GenAI**, ώστε τα ίχνη του agent σου να μην είναι ποτέ κλειδωμένα σε ένα μόνο εργαλείο.

**Εξαγωγή** κάθε συνεδρίας, κλήσεις LLM, εργαλεία, sub-agents, tokens, κόστος, ως ίχνη OTLP/HTTP GenAI σε οποιονδήποτε collector (Datadog, Grafana, Honeycomb, ή τον δικό σου OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες πιστοποίησης και το διάστημα polling είναι προαιρετικές μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Εισαγωγή** — ο ενσωματωμένος δέκτης OTLP δέχεται ίχνη και μετρικά από οτιδήποτε άλλο στα `/v1/traces` και `/v1/metrics` (`pip install clawmetry[otel]` για εισαγωγή protobuf).

Έχεις το μηδενικής διαμόρφωσης, local-first dashboard του ClawMetry **και** τα δεδομένα σου σε όποιο backend ήδη χρησιμοποιεί η ομάδα σου, χωρίς κλείδωμα (lock-in), χωρίς δεύτερο agent προς εγκατάσταση.

## Διαμόρφωση

Οι περισσότεροι δεν χρειάζονται καμία διαμόρφωση. Το ClawMetry ανιχνεύει αυτόματα τον χώρο εργασίας σου, τα logs, τις συνεδρίες και τα crons.

Αν χρειάζεσαι προσαρμογή:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα κανάλια

Το ClawMetry δείχνει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχεις διαμορφώσει. Μόνο τα κανάλια που είναι πραγματικά ρυθμισμένα στο `openclaw.json` σου εμφανίζονται στο διάγραμμα Flow, τα μη διαμορφωμένα αποκρύπτονται αυτόματα.

Κάνε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δεις μια ζωντανή προβολή chat bubble με μετρήσεις εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση κάθε 10s |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Ανίχνευση guild + καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Ανίχνευση workspace + καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένες συνεδρίες web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | Διεπαφή bubble τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks του Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω plugin bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Self-hosted ομαδική συνομιλία |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, με υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα DMs NIP-04 |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Chat μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή συμβάντων WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματη ανίχνευση:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json` και εμφανίζει μόνο τα κανάλια που έχεις πράγματι διαμορφώσει. Δεν απαιτείται χειροκίνητη ρύθμιση.

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

> **Σημείωση:** Όταν τρέχεις σε Docker, προσάρτησε τους φακέλους δεδομένων + logs του agent σου (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε το ClawMetry να μπορεί να ανιχνεύσει αυτόματα τη ρύθμισή σου.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα AI agent runtime στο ίδιο μηχάνημα: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, ή GitHub Copilot (ή προσαρτημένοι τόμοι για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry ανιχνεύει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw), το εταιρικό περιτύλιγμα ασφαλείας της NVIDIA για το OpenClaw που τρέχει agents μέσα σε sandboxed containers OpenShell.

Δεν χρειάζεται επιπλέον διαμόρφωση στις περισσότερες περιπτώσεις. Ο sync daemon ανακαλύπτει αυτόματα αρχεία συνεδριών είτε βρίσκονται στο `~/.openclaw/` στον host είτε μέσα σε ένα container OpenShell.

### Πώς λειτουργεί

Το ClawMetry ανιχνεύει το NemoClaw με δύο τρόπους:

1. **Ανίχνευση δυαδικού αρχείου** — ελέγχει για το CLI `nemoclaw` και εκτελεί `nemoclaw status` για να λάβει πληροφορίες sandbox
2. **Ανίχνευση container** — σαρώνει τα εκτελούμενα Docker containers για εικόνες `openshell`, `nemoclaw`, ή `ghcr.io/nvidia/`, και στη συνέχεια διαβάζει συνεδρίες μέσω προσαρτήσεων τόμου ή `docker cp`

Τα αρχεία συνεδριών που συγχρονίζονται από containers NemoClaw επισημαίνονται με `runtime=nemoclaw` και μεταδεδομένα `container_id` στο cloud dashboard, ώστε να μπορείς να τα ξεχωρίσεις από τις τυπικές συνεδρίες OpenClaw με μια ματιά.

### Προτεινόμενη ρύθμιση: sync daemon στον HOST

Για την καλύτερη εμπειρία, τρέξε τον sync daemon του ClawMetry στο **μηχάνημα host** (όχι μέσα στο sandbox). Αυτό αποφεύγει τους περιορισμούς πολιτικής δικτύου του NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο sync daemon θα βρει αυτόματα τις συνεδρίες μέσα σε οποιαδήποτε εκτελούμενα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν η αυτόματη ανίχνευση δεν λειτουργεί, κατεύθυνε το ClawMetry στο σωστό sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (προχωρημένο)

Αν πρέπει να τρέξεις τον sync daemon **μέσα** στο sandbox OpenShell, πρόσθεσε αυτόν τον κανόνα εξόδου (egress) στην πολιτική δικτύου NemoClaw ώστε να μπορεί να προσεγγίσει το ingest API του ClawMetry:

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

### Θύρες και τελικά σημεία

| Τελικό σημείο | Θύρα | Πρωτόκολλο | Απαιτείται |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ναι (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Ναι (τοπικό dashboard UI) |
| Υποδοχή Docker (`/var/run/docker.sock`) | — | Unix socket | Για ανακάλυψη συνεδριών container |

Ο sync daemon κάνει μόνο εξερχόμενες κλήσεις HTTPS προς το `ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη σε Cloud

Δες τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, reverse proxy, και Docker.

## Δοκιμές

Αυτό το project δοκιμάζεται με το BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry στέλνει ανώνυμα pings κύκλου ζωής εγκατάστασης στο
`https://app.clawmetry.com/api/install`: ένα ping `install` την πρώτη
φορά που τρέχεις το CLI `clawmetry` σε νέο μηχάνημα, ένα ping `update`
στην πρώτη εκτέλεση μετά την αναβάθμιση σε νέα έκδοση, και ένα ping
`onboarded` όταν ολοκληρώνεις την επιλογή onboarding μέσα στο dashboard. Το χρησιμοποιούμε
για να μετρήσουμε πραγματικές εγκαταστάσεις (οι ακατέργαστοι αριθμοί λήψεων από το PyPI είναι ~98% mirrors, CI,
και επανα-λήψεις αυτόματης ενημέρωσης) και για να μάθουμε ποια agent frameworks και
εκδόσεις χρησιμοποιούνται πραγματικά.

**Το πολύ ένα POST ανά συμβάν κύκλου ζωής ανά έκδοση**, που περιέχει:

| Πεδίο | Παράδειγμα | Γιατί |
|---|---|---|
| `install_id` | τυχαίο UUID αποθηκευμένο στο `~/.clawmetry/install_id` | αποφυγή διπλοεγγραφών· ανώνυμο μέχρι να συνδέσεις ρητά το Cloud sync (το πιστοποιημένο heartbeat του daemon μεταφέρει τότε αυτό το αναγνωριστικό, συνδέοντας αυτήν την εγκατάσταση με τον λογαριασμό σου) |
| `event` | `install` / `update` / `onboarded` | νέα εγκατάσταση έναντι αναβάθμισης υπάρχουσας |
| `version` | `0.12.167` | ποιες εκδόσεις χρησιμοποιούνται |
| `os` / `os_version` | `Darwin` / `25.3.0` | προτεραιότητες υποστήριξης πλατφόρμας |
| `python` | `3.11.15` | πίνακας υποστήριξης εκδόσεων Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | με ποιους agents πρέπει να ενσωματωθούμε στη συνέχεια |
| `is_ci` / `ci_provider` | `true` / `github_actions` | διαχωρισμός ανθρώπινων εγκαταστάσεων από θόρυβο CI |

**Τι ΔΕΝ στέλνουμε**: IP (το cloud εξάγει τον κωδικό χώρας από
την πλευρά του server από το αίτημα, και μετά απορρίπτει την IP), όνομα host, όνομα χρήστη, διαδρομή χώρου εργασίας, περιεχόμενα αρχείων, το api_key σου, το email σου, οτιδήποτε PII ή
σχετικό με τον χώρο εργασίας. Το wire payload είναι ελέγξιμο στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση** (οποιοδήποτε από αυτά την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Μια αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ την εκτέλεση του `clawmetry`, το
ping είναι fire-and-forget σε ένα νήμα daemon με χρονικό όριο 3 δευτερολέπτων.

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
  <sub>Δημιουργήθηκε από τον/την <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
