<!-- i18n-src:48548997be76 -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δείτε τον πράκτορά σας να σκέφτεται.** Παρατηρησιμότητα σε πραγματικό χρόνο για **12 περιβάλλοντα εκτέλεσης AI πρακτόρων**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 8 ακόμα. Ένα ταμπλό για ολόκληρο τον στόλο πρακτόρων σας.

> 🌐 **Διαβάστε το στη γλώσσα σας:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδέν ρυθμίσεις. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900** και είστε έτοιμοι.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 12 περιβάλλοντα εκτέλεσης πρακτόρων

Το ClawMetry ξεκίνησε ως εργαλείο παρατηρησιμότητας για το OpenClaw, και τώρα μετράει **ολόκληρο τον στόλο πρακτόρων σας** σε ένα ταμπλό, εντοπίζοντας αυτόματα κάθε περιβάλλον εκτέλεσης στον υπολογιστή σας:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

Το OpenClaw και το NemoClaw είναι δωρεάν στην ανοιχτού κώδικα εφαρμογή· τα υπόλοιπα περιβάλλοντα εκτέλεσης ενεργοποιούνται με ClawMetry Cloud ή άδεια αυτο-φιλοξενούμενου Pro. Εναλλάξτε περιβάλλοντα εκτέλεσης από την κεφαλίδα και κάθε καρτέλα — κόστος, tokens, εργαλεία, ίχνη — επαναπροσδιορίζεται στο επιλεγμένο περιβάλλον.

## Τι Περιλαμβάνει

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει μηνύματα να ρέουν μέσα από κανάλια, εγκέφαλο, εργαλεία και πίσω
- **Overview** — Έλεγχοι υγείας, χάρτης δραστηριότητας, αριθμός συνεδριών, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ημερήσιες/εβδομαδιαίες/μηνιαίες αναλύσεις
- **Sessions** — Ενεργές συνεδρίες πράκτορα με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Ροή αρχείων καταγραφής σε πραγματικό χρόνο με χρωματική κωδικοποίηση
- **Memory** — Περιήγηση στα SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή φυσαλίδων συνομιλίας για ανάγνωση ιστορικών συνεδριών
- **Alerts** — Ανώτατα όρια προϋπολογισμού, ενεργοποιητές ποσοστού σφάλματος, ανίχνευση αποσύνδεσης πράκτορα· αποστολή σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Προστασία επικίνδυνων διαγραφών, αναγκαστικών push, μεταλλάξεων βάσης δεδομένων, sudo, εγκαταστάσεων πακέτων, κλήσεων δικτύου πίσω από έγκριση με ένα κλικ

## Στιγμιότυπα Οθόνης

### 🧠 Brain — Ζωντανή ροή συμβάντων πράκτορα
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Χρήση tokens και σύνοψη συνεδριών
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Ροή κλήσεων εργαλείων σε πραγματικό χρόνο
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ανάλυση κόστους ανά μοντέλο και συνεδρία
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Περιηγητής αρχείων χώρου εργασίας
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Στάση ασφαλείας και αρχείο ελέγχου
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Ανώτατα όρια προϋπολογισμού, ενεργοποιητές ποσοστού σφάλματος, webhooks σε Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Προστασία επικίνδυνων κλήσεων εργαλείων με χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Εγκατάσταση

**Μία γραμμή (συνιστάται):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Από πηγαίο κώδικα:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Ανάπτυξη Frontend v2

Η εφαρμογή React v2 βρίσκεται στον φάκελο `frontend/` και εξυπηρετείται στο `/v2` όταν ο διακομιστής Flask εκκινείται με ενεργοποιημένο το v2.

Χρησιμοποιήστε δύο τερματικά κατά την ανάπτυξη:

```bash
# Τερματικό 1: Flask API/server στη θύρα :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Τερματικό 2: Vite dev server στη θύρα :5173
cd frontend
nvm use
npm ci
npm run dev
```

Ανοίξτε το `http://localhost:5173/v2/`. Το Vite προωθεί τα αιτήματα `/api` στο `http://localhost:8900`, ώστε η εφαρμογή React να επικοινωνεί με τον τοπικό διακομιστή Flask χωρίς επιπλέον ρύθμιση CORS.

Για να δημιουργήσετε το bundle που συμπεριλαμβάνεται στο πακέτο Python:

```bash
cd frontend
npm run build
```

Το bundle παραγωγής εγγράφεται στο `clawmetry/static/v2/dist/`.

## Συμβατότητα Περιβαλλόντων Εκτέλεσης / Πρακτόρων

Το ClawMetry παρατηρεί πολλά περιβάλλοντα εκτέλεσης AI πρακτόρων, όχι μόνο το OpenClaw. Κάθε περιβάλλον εκτέλεσης εκτός OpenClaw διαθέτει έναν αποκλειστικό προσαρμογέα ανάγνωσης που μεταφράζει την εγγενή μορφή συνεδρίας του στα ενοποιημένα σχήματα του ClawMetry· ο δαίμονας τα εισάγει στο ίδιο DuckDB store και στιγμιότυπο cloud, με ετικέτα περιβάλλοντος εκτέλεσης, και η καρτέλα επανάληψης συνεδρίας εμφανίζει έναν **διακόπτη περιβάλλοντος εκτέλεσης** όταν υπάρχει περισσότερο από ένα. Δείτε το [`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα και οδηγό προσθήκης περιβαλλόντων εκτέλεσης, και το [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην οικογένεια OpenClaw.

| Περιβάλλον Εκτέλεσης / Πράκτορας | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Εγγενές | Περιβάλλον αναφοράς, αυτόματη ανίχνευση |
| **PicoClaw** | Beta adapter | Επίπεδο `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Μεταγραφές, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta adapter | SQLite ανά συνεδρία (`data/v2-sessions`). Μεταγραφές και αριθμοί μηνυμάτων. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Μεταγραφές, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Μεταγραφές, μοντέλο, κλήσεις εργαλείων και σκέψη, χρήση tokens. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Μεταγραφές, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Μεταγραφές chat/composer, μοντέλο. |
| **Aider** | Beta adapter | `.aider.chat.history.md` ανά έργο. Μεταγραφές, μοντέλο, αριθμοί tokens. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Μεταγραφές, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Μεταγραφές, μοντέλο, κλήσεις εργαλείων, tokens και κόστος. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Μεταγραφές, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |

Το "Beta adapter" σημαίνει ότι το ClawMetry διαθέτει έναν αναγνώστη για την πραγματική μορφή δίσκου του εκάστοτε περιβάλλοντος εκτέλεσης, κατασκευασμένο και επαληθευμένο έναντι πραγματικής εγκατάστασης σε πραγματικό υπολογιστή (δείτε `tests/fixtures/runtimes/<rt>/`). Οι προσαρμογείς είναι μόνο ανάγνωσης· ο καθένας είναι ειλικρινής σχετικά με αυτό που το περιβάλλον εκτέλεσής του αποθηκεύει πραγματικά στο δίσκο (π.χ. το PicoClaw/NanoClaw/Cursor δεν γράφει κόστος tokens στο δίσκο). Όταν τρέχουν πολλά περιβάλλοντα εκτέλεσης σε έναν κόμβο, ο διακόπτης περιβάλλοντος εκτέλεσης περιορίζει την προβολή συνεδριών σε ένα για καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε SDK πράκτορα — εξωτερική απόδοση κόστους

Τα παραπάνω περιβάλλοντα εκτέλεσης γράφουν συνεδρίες στο δίσκο. Ο δικός σας **πράκτορας παραγωγής** — αυτός που κατασκευάσατε με το OpenAI Agents SDK, LangChain, το Vercel AI SDK, LlamaIndex, E2B, ή έναν απλό βρόχο `httpx` — δεν το κάνει. Ο zero-config αναχαιτιστής του ClawMetry εξακολουθεί να καταγράφει τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα) με monkey-patching του `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Το `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`) επισημαίνει κάθε κλήση με μια **ονοματισμένη πηγή**, ώστε κάθε προϊόν που εκτελείτε να εμφανίζεται ως δική του πρωτοβάθμια γραμμή απόδοσης κόστους στο ταμπλό στην κάρτα **🔌 Out-loop sources** της Επισκόπησης — κλήσεις, πάροχοι, καθυστέρηση, ποσοστό σφάλματος ανά πράκτορα. Χωρίς ορισμένη πηγή; Οι κλήσεις εξακολουθούν να παρακολουθούνται· η κάρτα απλώς παραμένει κρυφή.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι προσαρμογείς περιβάλλοντος εκτέλεσης (DuckDB → στιγμιότυπο cloud), οπότε οι εξωτερικές πηγές συγχρονίζονται με το cloud ταμπλό όπως τα υπόλοιπα, κρυπτογραφημένα από άκρο σε άκρο.

## OpenTelemetry — ουδέτερο ως προς τον πάροχο, στείλτε τα ίχνη σας οπουδήποτε

Το ClawMetry μιλά **OpenTelemetry** και στις δύο κατευθύνσεις, χρησιμοποιώντας τις **σημασιολογικές συμβάσεις GenAI**, ώστε τα ίχνη πράκτορά σας να μην κλειδώνονται σε ένα εργαλείο.

**Εξαγωγή** κάθε συνεδρίας — κλήσεις LLM, εργαλεία, υπο-πράκτορες, tokens, κόστος — ως OTLP/HTTP GenAI spans σε οποιονδήποτε συλλέκτη (Datadog, Grafana, Honeycomb, ή τον δικό σας OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες ταυτοποίησης και το διάστημα δημοσκόπησης είναι προαιρετικές μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Εισαγωγή** — ο ενσωματωμένος δέκτης OTLP δέχεται ίχνη και μετρικές από οτιδήποτε άλλο στα `/v1/traces` και `/v1/metrics` (`pip install clawmetry[otel]` για εισαγωγή protobuf).

Αποκτάτε το zero-config, τοπικό ClawMetry ταμπλό **και** τα δεδομένα σας σε οποιοδήποτε backend χρησιμοποιεί ήδη η ομάδα σας — χωρίς δέσμευση, χωρίς δεύτερο πράκτορα για εγκατάσταση.

## Διαμόρφωση

Οι περισσότεροι χρήστες δεν χρειάζονται καμία διαμόρφωση. Το ClawMetry εντοπίζει αυτόματα τον χώρο εργασίας, τα αρχεία καταγραφής, τις συνεδρίες και τα crons σας.

Αν χρειαστεί να προσαρμόσετε κάτι:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα Κανάλια

Το ClawMetry εμφανίζει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχετε διαμορφώσει. Μόνο τα κανάλια που είναι πραγματικά ρυθμισμένα στο `openclaw.json` σας εμφανίζονται στο διάγραμμα Flow — τα μη διαμορφωμένα αποκρύπτονται αυτόματα.

Κάντε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δείτε μια ζωντανή προβολή φυσαλίδων συνομιλίας με αριθμούς εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση κάθε 10 δευτ. |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Ανίχνευση guild και καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Ανίχνευση χώρου εργασίας και καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένες συνεδρίες web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | Διεπαφή φυσαλίδων τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω plugin bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Αυτο-φιλοξενούμενη ομαδική συνομιλία |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα NIP-04 DMs |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Συνομιλία μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή συμβάντος WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματη ανίχνευση:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json` σας και αποδίδει μόνο τα κανάλια που έχετε πραγματικά διαμορφώσει. Δεν απαιτείται χειροκίνητη ρύθμιση.

## Ανάπτυξη με Docker

Θέλετε να εκτελέσετε το ClawMetry σε container; Κανένα πρόβλημα! 🐳

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

> **Σημείωση:** Κατά την εκτέλεση σε Docker, προσαρτήστε τους καταλόγους δεδομένων και αρχείων καταγραφής του πράκτορά σας (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε το ClawMetry να εντοπίσει αυτόματα τη ρύθμισή σας.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα περιβάλλον εκτέλεσης AI πράκτορα στον ίδιο υπολογιστή: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw ή PicoClaw (ή προσαρτημένοι τόμοι για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry εντοπίζει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw) — το εταιρικό περίβλημα ασφαλείας της NVIDIA για το OpenClaw που εκτελεί πράκτορες μέσα σε containers OpenShell με απομόνωση.

Στις περισσότερες περιπτώσεις δεν χρειάζεται επιπλέον διαμόρφωση. Ο δαίμονας συγχρονισμού εντοπίζει αυτόματα τα αρχεία συνεδρίας είτε βρίσκονται στο `~/.openclaw/` του κεντρικού υπολογιστή είτε μέσα σε container OpenShell.

### Πώς λειτουργεί

Το ClawMetry εντοπίζει το NemoClaw με δύο τρόπους:

1. **Ανίχνευση δυαδικού αρχείου** — ελέγχει για το CLI `nemoclaw` και εκτελεί `nemoclaw status` για πληροφορίες sandbox
2. **Ανίχνευση container** — σαρώνει τα εκτελούμενα containers Docker για εικόνες `openshell`, `nemoclaw` ή `ghcr.io/nvidia/`, και στη συνέχεια διαβάζει συνεδρίες μέσω προσαρτημένων τόμων ή `docker cp`

Τα αρχεία συνεδρίας που συγχρονίζονται από containers NemoClaw επισημαίνονται με μεταδεδομένα `runtime=nemoclaw` και `container_id` στο cloud ταμπλό, ώστε να τα ξεχωρίζετε εύκολα από τυπικές συνεδρίες OpenClaw.

### Συνιστώμενη ρύθμιση: δαίμονας συγχρονισμού στον ΚΕΝΤΡΙΚΟ ΥΠΟΛΟΓΙΣΤΗ

Για την καλύτερη εμπειρία, εκτελέστε τον δαίμονα συγχρονισμού του ClawMetry στον **κεντρικό υπολογιστή** (όχι μέσα στο sandbox). Αυτό αποφεύγει τους περιορισμούς πολιτικής δικτύου του NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο δαίμονας συγχρονισμού θα εντοπίσει αυτόματα τις συνεδρίες μέσα σε οποιαδήποτε εκτελούμενα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν η αυτόματη ανίχνευση δεν λειτουργεί, κατευθύνετε το ClawMetry στο σωστό sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (για προχωρημένους)

Αν πρέπει να εκτελέσετε τον δαίμονα συγχρονισμού **μέσα** στο sandbox OpenShell, προσθέστε αυτόν τον κανόνα εξόδου στην πολιτική δικτύου του NemoClaw ώστε να μπορεί να φθάσει το API εισαγωγής του ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Εφαρμόστε με:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Θύρες και σημεία πρόσβασης

| Σημείο πρόσβασης | Θύρα | Πρωτόκολλο | Απαιτείται |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ναι (δαίμονας συγχρ. → cloud) |
| `localhost:8900` | 8900 | HTTP | Ναι (τοπικό UI ταμπλό) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Για ανίχνευση συνεδριών container |

Ο δαίμονας συγχρονισμού πραγματοποιεί μόνο εξερχόμενες κλήσεις HTTPS στο `ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη σε Cloud

Δείτε τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, αντίστροφο proxy και Docker.

## Δοκιμές

Αυτό το έργο δοκιμάζεται με BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry αποστέλλει ένα μοναδικό ανώνυμο ping "πρώτης εκτέλεσης" στο
`https://app.clawmetry.com/api/install` την πρώτη φορά που εκτελείτε το
CLI `clawmetry` σε νέο υπολογιστή. Το χρησιμοποιούμε για να μετράμε εγκαταστάσεις (η
μόνη μετρική μάρκετινγκ που έχουμε για ένα OSS έργο) και για να μαθαίνουμε ποια
frameworks πρακτόρων χρησιμοποιούν οι χρήστες μας.

**Ακριβώς ένα POST ανά εγκατάσταση**, που περιέχει:

| Πεδίο | Παράδειγμα | Γιατί |
|---|---|---|
| `install_id` | τυχαίο UUID αποθηκευμένο στο `~/.clawmetry/install_id` | αποεπανάληψη· δεν συνδέεται με το email ή το api_key σας |
| `version` | `0.12.167` | ποιες εκδόσεις κυκλοφορούν |
| `os` / `os_version` | `Darwin` / `25.3.0` | προτεραιότητες υποστήριξης πλατφόρμας |
| `python` | `3.11.15` | πίνακας υποστήριξης εκδόσεων Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | με ποιους πράκτορες πρέπει να ενσωματωθούμε στη συνέχεια |
| `is_ci` / `ci_provider` | `true` / `github_actions` | διαχωρισμός ανθρώπινων εγκαταστάσεων από θόρυβο CI |

**Τι ΔΕΝ αποστέλλουμε**: IP (το cloud εξάγει τον κωδικό χώρας από την πλευρά του διακομιστή από το αίτημα, στη συνέχεια απορρίπτει την IP), όνομα κεντρικού υπολογιστή, όνομα χρήστη, διαδρομή χώρου εργασίας, περιεχόμενα αρχείων, το api_key σας, το email σας, οτιδήποτε PII ή σχετικό με τον χώρο εργασίας. Το περιεχόμενο του φορτίου ελέγχεται στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση** (οποιαδήποτε από αυτές την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ την εκτέλεση του `clawmetry` — το
ping είναι fire-and-forget σε daemon thread με timeout 3 δευτερολέπτων.

## Ιστορικό Αστεριών

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια Χρήσης

MIT

---

<p align="center">
  <strong>🦞 Δείτε τον πράκτορά σας να σκέφτεται</strong><br>
  <sub>Κατασκευάστηκε από τον <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
