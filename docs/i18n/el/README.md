<!-- i18n-src:8f42d460a973 -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον agent σου να σκέφτεται.** Παρατηρησιμότητα σε πραγματικό χρόνο για **14 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 10 ακόμη. Ένα dashboard για όλο τον στόλο agents σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική ρύθμιση. Εντοπίζει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900** και είσαι έτοιμος.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 14 agent runtimes

Το ClawMetry ξεκίνησε ως παρατηρησιμότητα για το OpenClaw, και τώρα μετράει ολόκληρο τον **στόλο agents** σου σε ένα dashboard, εντοπίζοντας αυτόματα κάθε runtime στο μηχάνημά σου:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

Το OpenClaw και το NemoClaw είναι δωρεάν στην open-source εφαρμογή· τα υπόλοιπα runtimes ενεργοποιούνται με το ClawMetry Cloud ή με μια self-hosted άδεια Pro. Άλλαξε runtime από το header και κάθε καρτέλα, κόστος, tokens, εργαλεία, traces, προσαρμόζεται σε αυτό το runtime. Δες το **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** για τον ακριβή διαχωρισμό δωρεάν/επί πληρωμή, τον πίνακα βαθμίδων, τη μορφή του `/api/entitlement`, και το CLI `clawmetry license`.

## Τι παίρνεις

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει τα μηνύματα να ρέουν μέσα από κανάλια, εγκέφαλο, εργαλεία, και πίσω
- **Overview** — Έλεγχοι υγείας, heatmap δραστηριότητας, μετρήσεις sessions, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ημερήσια/εβδομαδιαία/μηνιαία ανάλυση
- **Sessions** — Ενεργά sessions agent με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Ζωντανή ροή logs με έγχρωμη κωδικοποίηση
- **Memory** — Περιήγηση σε SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή τύπου chat-bubble για ανάγνωση ιστορικού sessions
- **Alerts** — Όρια budget, triggers ρυθμού σφαλμάτων, εντοπισμός offline agent· δρομολόγηση σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Φραγή καταστροφικών διαγραφών, force pushes, μεταβολών βάσης δεδομένων, sudo, εγκαταστάσεων πακέτων, κλήσεων δικτύου πίσω από έγκριση με ένα κλικ

## Στιγμιότυπα

### 🧠 Brain — Ζωντανή ροή γεγονότων agent
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Χρήση tokens & σύνοψη session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Ροή κλήσεων εργαλείων σε πραγματικό χρόνο
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ανάλυση κόστους ανά μοντέλο & session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Περιηγητής αρχείων χώρου εργασίας
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Στάση ασφαλείας & αρχείο ελέγχου
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Όρια budget, triggers ρυθμού σφαλμάτων, webhooks προς Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Φραγή ριψοκίνδυνων κλήσεων εργαλείων πίσω από χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## Ανάπτυξη του v2 Frontend

Η εφαρμογή React v2 βρίσκεται στο `frontend/` και σερβίρεται στο `/v2` όταν
ο Flask server ξεκινά με ενεργοποιημένο το v2.

Χρησιμοποίησε δύο τερματικά κατά την ανάπτυξη:

```bash
# Τερματικό 1: Flask API/server στο :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Τερματικό 2: Vite dev server στο :5173
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

Το ClawMetry παρατηρεί πολλά AI-agent runtimes, όχι μόνο το OpenClaw. Κάθε runtime εκτός OpenClaw διαθέτει έναν αποκλειστικό reader adapter που μεταφράζει τη δική του native μορφή session στα ενοποιημένα σχήματα του ClawMetry· ο daemon τα εισάγει στο ίδιο DuckDB store + cloud snapshot, με ετικέτα το runtime, και η καρτέλα αναπαραγωγής Session δείχνει έναν **επιλογέα runtime** όταν υπάρχει περισσότερο από ένα. Δες το [`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα + έναν οδηγό για την προσθήκη runtimes, και το [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην οικογένεια OpenClaw.

| Runtime / Agent | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Native | Runtime αναφοράς, εντοπίζεται αυτόματα |
| **PicoClaw** | Beta adapter | Επίπεδο `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta adapter | SQLite ανά session (`data/v2-sessions`). Transcripts + μετρήσεις μηνυμάτων. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, μοντέλο, κλήσεις εργαλείων + σκέψη, χρήση tokens. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Transcripts chat/composer, μοντέλο. |
| **Aider** | Beta adapter | `.aider.chat.history.md` ανά project. Transcripts, μοντέλο, μετρήσεις tokens. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |

«Beta adapter» σημαίνει ότι το ClawMetry διαθέτει έναν reader για την πραγματική μορφή αρχείων εκείνου του runtime, χτισμένο και επαληθευμένο σε πραγματική εγκατάσταση σε πραγματικό μηχάνημα (δες `tests/fixtures/runtimes/<rt>/`). Οι adapters είναι μόνο για ανάγνωση· ο καθένας είναι ειλικρινής σχετικά με το τι πραγματικά αποθηκεύει το runtime του (π.χ. το PicoClaw/NanoClaw/Cursor δεν γράφουν κόστος tokens στον δίσκο). Όταν τρέχουν πολλά runtimes σε έναν κόμβο, ο επιλογέας runtime περιορίζει την προβολή sessions σε ένα για μια καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε SDK agent — απόδοση κόστους out-loop

Τα παραπάνω runtimes γράφουν όλα sessions στον δίσκο. Ο δικός σου **agent παραγωγής** — αυτός που έχτισες πάνω στο OpenAI Agents SDK, το LangChain, το Vercel AI SDK, το LlamaIndex, το E2B, ή έναν απλό βρόχο `httpx` — δεν το κάνει. Ο zero-config interceptor του ClawMetry εξακολουθεί να καταγράφει τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα) κάνοντας monkey-patching στα `httpx`/`requests`:

```python
import clawmetry.track            # ενεργοποίηση του interceptor
clawmetry.track.set_source("support-agent")   # ονόμασε αυτό το προϊόν

# ...ο agent σου τρέχει κανονικά· κάθε κλήση LLM τώρα παρακολουθείται + αποδίδεται.
```

Το `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`) ετικετάρει κάθε κλήση με μια **ονομαστική πηγή**, ώστε κάθε προϊόν που τρέχεις να εμφανίζεται ως δική του πρωτοβάθμια, αποδόσιμη σε κόστος γραμμή στην κάρτα **🔌 Out-loop sources** του dashboard στο Overview — κλήσεις, providers, καθυστέρηση, ρυθμός σφαλμάτων ανά agent. Δεν έχεις ορίσει πηγή; Οι κλήσεις εξακολουθούν να παρακολουθούνται· η κάρτα απλώς παραμένει κρυφή.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι adapters runtime (DuckDB → cloud snapshot), οπότε οι out-loop πηγές συγχρονίζονται με το cloud dashboard όπως όλα τα άλλα, κρυπτογραφημένες από άκρο σε άκρο.

## OpenTelemetry — ουδέτερο ως προς τον προμηθευτή, στείλε τα traces σου οπουδήποτε

Το ClawMetry μιλάει **OpenTelemetry** και προς τις δύο κατευθύνσεις, χρησιμοποιώντας τις **GenAI semantic conventions**, ώστε τα traces του agent σου να μην κλειδώνονται ποτέ σε ένα εργαλείο.

**Εξαγωγή** κάθε session, κλήσεις LLM, εργαλεία, sub-agents, tokens, κόστος, ως spans OTLP/HTTP GenAI προς οποιονδήποτε collector (Datadog, Grafana, Honeycomb, ή τον δικό σου OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# ισοδύναμα:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες αυθεντικοποίησης και το διάστημα polling είναι προαιρετικές μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # επιπλέον κεφαλίδες HTTP
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # δευτερόλεπτα (προεπιλογή 60)
```

**Εισαγωγή** — ο ενσωματωμένος OTLP receiver δέχεται traces και metrics από οτιδήποτε άλλο στα `/v1/traces` και `/v1/metrics` (`pip install clawmetry[otel]` για εισαγωγή protobuf).

Παίρνεις το zero-config, local-first dashboard του ClawMetry **και** τα δεδομένα σου σε όποιο backend ήδη χρησιμοποιεί η ομάδα σου — χωρίς lock-in, χωρίς δεύτερο agent για εγκατάσταση.

## Ρύθμιση

Οι περισσότεροι δεν χρειάζονται καμία ρύθμιση. Το ClawMetry εντοπίζει αυτόματα τον χώρο εργασίας, τα logs, τα sessions, και τα crons σου.

Αν χρειάζεσαι προσαρμογή:

```bash
clawmetry --port 9000              # Προσαρμοσμένη θύρα (προεπιλογή: 8900)
clawmetry --host 127.0.0.1         # Σύνδεση μόνο σε localhost
clawmetry --workspace ~/mybot      # Προσαρμοσμένη διαδρομή χώρου εργασίας
clawmetry --name "Alice"           # Το όνομά σου στην απεικόνιση Flow
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα κανάλια

Το ClawMetry δείχνει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχεις ρυθμίσει. Μόνο τα κανάλια που είναι πραγματικά ρυθμισμένα στο `openclaw.json` σου εμφανίζονται στο διάγραμμα Flow — τα μη ρυθμισμένα κρύβονται αυτόματα.

Κάνε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δεις μια ζωντανή προβολή chat bubble με μετρήσεις εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση 10s |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Εντοπισμός guild + καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Εντοπισμός workspace + καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένα sessions web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | Διεπαφή bubble τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω plugin bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Self-hosted team chat |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα NIP-04 DMs |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Chat μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή σε γεγονότα WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματος εντοπισμός:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json` σου και εμφανίζει μόνο τα κανάλια που έχεις πράγματι ρυθμίσει. Δεν απαιτείται χειροκίνητη ρύθμιση.

## Ανάπτυξη με Docker

Θέλεις να τρέξεις το ClawMetry σε container; Κανένα πρόβλημα! 🐳

**Γρήγορη εκκίνηση με Docker:**

```bash
# Χτίσε την εικόνα
docker build -t clawmetry .

# Τρέξε με προεπιλεγμένες ρυθμίσεις
docker run -p 8900:8900 clawmetry

# Ή προσάρτησε τον φάκελο δεδομένων του agent σου (φαίνεται: το ~/.openclaw του OpenClaw)
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

> **Σημείωση:** Όταν τρέχεις σε Docker, προσάρτησε τους φακέλους δεδομένων + logs του agent σου (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε το ClawMetry να μπορεί να εντοπίσει αυτόματα τη ρύθμισή σου.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα AI agent runtime στο ίδιο μηχάνημα: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, ή Deep Agents (ή προσαρτημένοι τόμοι για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry εντοπίζει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw) — το enterprise wrapper ασφαλείας της NVIDIA για το OpenClaw που τρέχει agents μέσα σε sandboxed containers OpenShell.

Δεν απαιτείται επιπλέον ρύθμιση στις περισσότερες περιπτώσεις. Ο sync daemon ανακαλύπτει αυτόματα αρχεία session είτε βρίσκονται στο `~/.openclaw/` στον host είτε μέσα σε ένα container OpenShell.

### Πώς λειτουργεί

Το ClawMetry εντοπίζει το NemoClaw με δύο τρόπους:

1. **Εντοπισμός binary** — ελέγχει για το CLI `nemoclaw` και τρέχει `nemoclaw status` για να πάρει πληροφορίες sandbox
2. **Εντοπισμός container** — σαρώνει τρέχοντα containers Docker για εικόνες `openshell`, `nemoclaw`, ή `ghcr.io/nvidia/`, έπειτα διαβάζει sessions μέσω προσαρτήσεων τόμων ή `docker cp`

Τα αρχεία session που συγχρονίζονται από containers NemoClaw ετικετάρονται με `runtime=nemoclaw` και μεταδεδομένα `container_id` στο cloud dashboard, ώστε να μπορείς να τα ξεχωρίσεις από τυπικά sessions OpenClaw με μια ματιά.

### Προτεινόμενη ρύθμιση: sync daemon στον HOST

Για την καλύτερη εμπειρία, τρέξε τον sync daemon του ClawMetry στο **host μηχάνημα** (όχι μέσα στο sandbox). Αυτό αποφεύγει περιορισμούς πολιτικής δικτύου του NemoClaw.

```bash
# Στον host (εκτός sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο sync daemon θα βρει αυτόματα sessions μέσα σε οποιαδήποτε τρέχοντα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν ο αυτόματος εντοπισμός δεν λειτουργεί, δείξε στο ClawMetry το σωστό sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (προχωρημένο)

Αν πρέπει να τρέξεις τον sync daemon **μέσα** στο sandbox OpenShell, πρόσθεσε αυτόν τον κανόνα egress στην πολιτική δικτύου NemoClaw σου ώστε να μπορεί να φτάσει το API ingest του ClawMetry:

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
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Για ανακάλυψη session containers |

Ο sync daemon κάνει μόνο εξερχόμενες κλήσεις HTTPS προς το `ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη Cloud

Δες τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, reverse proxy, και Docker.

## Δοκιμές

Αυτό το project δοκιμάζεται με το BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry στέλνει ένα μοναδικό ανώνυμο ping "πρώτης εκτέλεσης" στο
`https://app.clawmetry.com/api/install` την πρώτη φορά που τρέχεις το CLI
`clawmetry` σε ένα νέο μηχάνημα. Το χρησιμοποιούμε για να μετράμε εγκαταστάσεις (η
μόνη μετρική marketing που έχουμε για ένα project OSS) και για να μαθαίνουμε ποια
frameworks agent έχουν εγκαταστήσει οι χρήστες μας.

**Ακριβώς ένα POST ανά εγκατάσταση**, που περιέχει:

| Πεδίο | Παράδειγμα | Γιατί |
|---|---|---|
| `install_id` | τυχαίο UUID αποθηκευμένο στο `~/.clawmetry/install_id` | αποφυγή διπλότυπων· δεν συνδέεται με το email ή το api_key σου |
| `version` | `0.12.167` | ποιες εκδόσεις κυκλοφορούν |
| `os` / `os_version` | `Darwin` / `25.3.0` | προτεραιότητες υποστήριξης πλατφόρμας |
| `python` | `3.11.15` | πίνακας υποστήριξης εκδόσεων Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | με ποιους agents πρέπει να ενσωματωθούμε στη συνέχεια |
| `is_ci` / `ci_provider` | `true` / `github_actions` | διαχωρισμός ανθρώπινων εγκαταστάσεων από θόρυβο CI |

**Τι ΔΕΝ στέλνουμε**: IP (το cloud εξάγει τον κωδικό χώρας από την πλευρά του
server από το αίτημα, και μετά απορρίπτει το IP), hostname, username, διαδρομή
χώρου εργασίας, περιεχόμενα αρχείων, το api_key σου, το email σου, οτιδήποτε
PII ή ειδικό για τον χώρο εργασίας. Το wire payload είναι ελέγξιμο στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση** (οποιοδήποτε από τα παρακάτω την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ανά shell
export DO_NOT_TRACK=1                          # πρότυπο W3C cross-tool
touch ~/.clawmetry/notelemetry                 # μόνιμος δείκτης αρχείου
```

Μια αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ την εκτέλεση του `clawmetry` — το
ping είναι fire-and-forget σε ένα daemon thread με timeout 3 δευτερολέπτων.

## Ιστορικό Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια

MIT

---

<p align="center">
  <strong>🦞 Δες τον agent σου να σκέφτεται</strong><br>
  <sub>Χτισμένο από τον <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
