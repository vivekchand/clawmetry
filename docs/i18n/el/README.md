<!-- i18n-src:bab48eec552f -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον agent σου να σκέφτεται.** Παρατηρησιμότητα σε πραγματικό χρόνο για **14 runtimes AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 10 ακόμη. Ένα dashboard για όλο τον στόλο agent σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική ρύθμιση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900** και έτοιμο.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 14 runtimes agent

Το ClawMetry ξεκίνησε ως παρατηρησιμότητα για το OpenClaw, και τώρα μετράει ολόκληρο τον **στόλο agent** σου σε ένα dashboard, ανιχνεύοντας αυτόματα κάθε runtime στο μηχάνημά σου:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

Το OpenClaw και το NemoClaw είναι δωρεάν στην open-source εφαρμογή· τα υπόλοιπα runtimes ενεργοποιούνται με το ClawMetry Cloud ή μια αυτοφιλοξενούμενη άδεια Pro. Άλλαξε runtime από την κεφαλίδα και κάθε καρτέλα, κόστος, tokens, εργαλεία, traces, επαναπροσαρμόζεται σε αυτό το runtime. Δες το **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** για την ακριβή διάκριση δωρεάν/επί πληρωμή, τον πίνακα επιπέδων, τη μορφή του `/api/entitlement`, και το CLI `clawmetry license`.

## Τι αποκτάς

- **Flow** — Ζωντανό κινούμενο διάγραμμα που δείχνει τα μηνύματα να ρέουν μέσα από κανάλια, εγκέφαλο, εργαλεία, και πίσω
- **Overview** — Έλεγχοι υγείας, χάρτης θερμότητας δραστηριότητας, μετρήσεις συνεδριών, πληροφορίες μοντέλου
- **Usage** — Παρακολούθηση tokens και κόστους με ημερήσιες/εβδομαδιαίες/μηνιαίες αναλύσεις
- **Sessions** — Ενεργές συνεδρίες agent με μοντέλο, tokens, τελευταία δραστηριότητα
- **Crons** — Προγραμματισμένες εργασίες με κατάσταση, επόμενη εκτέλεση, διάρκεια
- **Logs** — Ζωντανή ροή logs με χρωματική κωδικοποίηση
- **Memory** — Περιήγηση σε SOUL.md, MEMORY.md, AGENTS.md, ημερήσιες σημειώσεις
- **Transcripts** — Διεπαφή σε φυσαλίδες συνομιλίας για ανάγνωση ιστορικού συνεδριών
- **Alerts** — Όρια προϋπολογισμού, ενεργοποιητές ρυθμού σφαλμάτων, ανίχνευση εκτός σύνδεσης agent· δρομολόγηση σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Φραγή καταστροφικών διαγραφών, force pushes, μεταβολών βάσης δεδομένων, sudo, εγκαταστάσεων πακέτων, κλήσεων δικτύου πίσω από έγκριση με ένα κλικ

## Στιγμιότυπα

### 🧠 Brain — Ζωντανή ροή γεγονότων agent
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

### 🚨 Alerts — Όρια προϋπολογισμού, ενεργοποιητές ρυθμού σφαλμάτων, webhooks προς Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Φραγή ριψοκίνδυνων κλήσεων εργαλείων πίσω από χειροκίνητη έγκριση· κανόνες προστασίας βασισμένοι σε πολιτική
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Φραγή πριν την εκτέλεση για το Claude Code** — μία εντολή εγκαθιστά ένα
hook PreToolUse που παύει τις κλήσεις εργαλείων που ταιριάζουν *πριν* εκτελεστούν και περιμένει
την απόφασή σου (ένα άγγιγμα από το τηλέφωνό σου με
[ειδοποιήσεις push από το cloud](https://app.clawmetry.com/push) ενεργοποιημένες):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Μια απόρριψη φράζει μόνο αυτή τη μία κλήση εργαλείου, ο agent κρατά τη συνεδρία του και μπορεί
να δοκιμάσει άλλη προσέγγιση. Η έγκριση από το τηλέφωνό σου παρακάμπτει το δικό του
prompt δικαιωμάτων του Claude Code (το έχεις ήδη απαντήσει). Τα εργαλεία που δεν ταιριάζουν κοστίζουν ~40ms και
περνούν στην κανονική ροή δικαιωμάτων του Claude Code. Λαμβάνεις επίσης μια ειδοποίηση push στο τηλέφωνο
όταν το ίδιο το Claude Code περιμένει την απάντησή σου (ειδοποιήσεις `permission_prompt` /
`idle_prompt`).

## Εγκατάσταση

**Μονογραμμική εντολή (προτείνεται):**
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

Η εφαρμογή React v2 βρίσκεται στο `frontend/` και εξυπηρετείται στο `/v2` όταν ο
Flask server ξεκινά με ενεργοποιημένο το v2.

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

Άνοιξε το `http://localhost:5173/v2/`. Το Vite προωθεί (proxy) τα αιτήματα `/api` προς
το `http://localhost:8900`, ώστε η εφαρμογή React να μπορεί να επικοινωνεί με τον τοπικό Flask server
χωρίς επιπλέον ρύθμιση CORS.

Για να χτίσεις το bundle που συνοδεύει το πακέτο Python:

```bash
cd frontend
npm run build
```

Το production bundle γράφεται στο `clawmetry/static/v2/dist/`.

## Συμβατότητα Runtime / Agent

Το ClawMetry παρατηρεί πολλά runtimes AI-agent, όχι μόνο το OpenClaw. Κάθε runtime εκτός OpenClaw διαθέτει έναν αποκλειστικό αντάπτορα ανάγνωσης που μεταφράζει τη δική του μορφή συνεδρίας στις ενοποιημένες μορφές του ClawMetry· ο daemon τα εισάγει στο ίδιο αποθετήριο DuckDB + στιγμιότυπο cloud, με ετικέτα το runtime, και η καρτέλα επανάληψης συνεδρίας (Session replay) εμφανίζει έναν **επιλογέα runtime** όταν υπάρχει περισσότερο από ένα. Δες το [`docs/compatibility.md`](docs/compatibility.md) για τον πλήρη πίνακα + οδηγό προσθήκης runtimes, και το [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) για την εισαγωγή στην οικογένεια OpenClaw.

| Runtime / Agent | Κατάσταση | Σημειώσεις |
|---|---|---|
| **OpenClaw** | Εγγενές | Runtime αναφοράς, ανιχνεύεται αυτόματα |
| **PicoClaw** | Beta αντάπτορας | Επίπεδο JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripts, μοντέλο, κλήσεις εργαλείων. |
| **NanoClaw** | Beta αντάπτορας | SQLite ανά συνεδρία (`data/v2-sessions`). Transcripts + μετρήσεις μηνυμάτων. |
| **Hermes** | Beta αντάπτορας | SQLite `~/.hermes/state.db`. Transcripts, μοντέλο, tokens/κόστος. |
| **Claude Code** | Beta αντάπτορας | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, μοντέλο, κλήσεις εργαλείων + σκέψη, χρήση tokens. |
| **Codex** | Beta αντάπτορας | Rollout JSONL `~/.codex/sessions/...`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Cursor** | Beta αντάπτορας | SQLite `state.vscdb`. Transcripts συνομιλίας/composer, μοντέλο. |
| **Aider** | Beta αντάπτορας | `.aider.chat.history.md` ανά έργο. Transcripts, μοντέλο, μετρήσεις tokens. |
| **Goose** | Beta αντάπτορας | SQLite `~/.local/share/goose`. Transcripts, μοντέλο, κλήσεις εργαλείων, σύνολα tokens. |
| **opencode** | Beta αντάπτορας | SQLite `~/.local/share/opencode`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Qwen Code** | Beta αντάπτορας | JSONL `~/.qwen/projects/.../chats`. Transcripts, μοντέλο, κλήσεις εργαλείων, χρήση tokens. |
| **Pi** | Beta αντάπτορας | JSONL `~/.pi/agent/sessions`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |
| **Deep Agents** | Beta αντάπτορας | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, μοντέλο, κλήσεις εργαλείων, tokens + κόστος. |

"Beta αντάπτορας" σημαίνει ότι το ClawMetry διαθέτει έναν αναγνώστη για την πραγματική μορφή αρχείων αυτού του runtime, χτισμένο και επαληθευμένο ο καθένας έναντι πραγματικής εγκατάστασης σε πραγματικό μηχάνημα (δες `tests/fixtures/runtimes/<rt>/`). Οι αντάπτορες είναι μόνο για ανάγνωση· ο καθένας είναι ειλικρινής για το τι πραγματικά αποθηκεύει το runtime του (π.χ. τα PicoClaw/NanoClaw/Cursor δεν γράφουν κόστος tokens στον δίσκο). Όταν τρέχουν πολλά runtimes σε έναν κόμβο, ο επιλογέας runtime περιορίζει την προβολή συνεδριών σε ένα, για μια καθαρή εμβάθυνση.

## Παρακολούθηση οποιουδήποτε SDK agent — απόδοση κόστους εκτός βρόχου

Τα παραπάνω runtimes γράφουν όλα συνεδρίες στον δίσκο. Ο δικός σου **agent παραγωγής** — αυτός που έφτιαξες με το OpenAI Agents SDK, το LangChain, το Vercel AI SDK, το LlamaIndex, το E2B, ή έναν απλό βρόχο `httpx` — δεν το κάνει. Ο ανιχνευτής (interceptor) μηδενικής ρύθμισης του ClawMetry εξακολουθεί να καταγράφει τις κλήσεις LLM του (κόστος, tokens, καθυστέρηση, σφάλματα) κάνοντας monkey-patch στα `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Η `set_source()` (ή η μεταβλητή περιβάλλοντος `CLAWMETRY_SOURCE=support-agent`) επισημαίνει κάθε κλήση με μια **ονομασμένη πηγή**, ώστε κάθε προϊόν που τρέχεις να εμφανίζεται ως δική του, πρωτοκλασάτη, αποδώσιμη ως προς το κόστος γραμμή στην κάρτα **🔌 Πηγές εκτός βρόχου** του Overview στο dashboard, κλήσεις, πάροχοι, καθυστέρηση, ρυθμός σφαλμάτων ανά agent. Δεν έχεις ορίσει πηγή; Οι κλήσεις εξακολουθούν να παρακολουθούνται, απλώς η κάρτα παραμένει κρυφή.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Αυτό είναι το ίδιο επίπεδο δεδομένων που τροφοδοτούν οι αντάπτορες runtime (DuckDB → στιγμιότυπο cloud), οπότε οι πηγές εκτός βρόχου συγχρονίζονται στο cloud dashboard όπως όλα τα υπόλοιπα, με κρυπτογράφηση από άκρο σε άκρο.

## OpenTelemetry — ουδέτερο ως προς τον πάροχο, στείλε τα traces σου οπουδήποτε

Το ClawMetry μιλάει **OpenTelemetry** και προς τις δύο κατευθύνσεις, χρησιμοποιώντας τις **σημασιολογικές συμβάσεις GenAI**, ώστε τα traces του agent σου να μη μένουν ποτέ κλειδωμένα σε ένα μόνο εργαλείο.

**Εξαγωγή** κάθε συνεδρίας, κλήσεις LLM, εργαλεία, sub-agents, tokens, κόστος, ως spans OTLP/HTTP GenAI προς οποιονδήποτε συλλέκτη (Datadog, Grafana, Honeycomb, ή τον δικό σου OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Οι κεφαλίδες αυθεντικοποίησης και το διάστημα ψηφοφορίας (poll interval) είναι προαιρετικές μεταβλητές περιβάλλοντος:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Εισαγωγή** — ο ενσωματωμένος δέκτης OTLP δέχεται traces και metrics από οτιδήποτε άλλο στα `/v1/traces` και `/v1/metrics` (`pip install clawmetry[otel]` για εισαγωγή protobuf).

Αποκτάς το dashboard ClawMetry μηδενικής ρύθμισης, τοπικό εξ ορισμού, **και** τα δεδομένα σου σε όποιο backend ήδη χρησιμοποιεί η ομάδα σου, χωρίς κλείδωμα σε προμηθευτή, χωρίς δεύτερο agent για εγκατάσταση.

## Ρύθμιση

Οι περισσότεροι δεν χρειάζονται καμία ρύθμιση. Το ClawMetry ανιχνεύει αυτόματα τον χώρο εργασίας, τα logs, τις συνεδρίες, και τα crons σου.

Αν χρειάζεσαι προσαρμογή:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Όλες οι επιλογές: `clawmetry --help`

## Υποστηριζόμενα Κανάλια

Το ClawMetry εμφανίζει ζωντανή δραστηριότητα για κάθε κανάλι OpenClaw που έχεις ρυθμίσει. Μόνο τα κανάλια που είναι όντως ρυθμισμένα στο `openclaw.json` σου εμφανίζονται στο διάγραμμα Flow, τα μη ρυθμισμένα αποκρύπτονται αυτόματα.

Κάνε κλικ σε οποιονδήποτε κόμβο καναλιού στο Flow για να δεις μια ζωντανή προβολή φυσαλίδων συνομιλίας με μετρήσεις εισερχόμενων/εξερχόμενων μηνυμάτων.

| Κανάλι | Κατάσταση | Ζωντανό Popup | Σημειώσεις |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Πλήρες | ✅ | Μηνύματα, στατιστικά, ανανέωση 10δ |
| 💬 **iMessage** | ✅ Πλήρες | ✅ | Διαβάζει απευθείας το `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Πλήρες | ✅ | Μέσω WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Πλήρες | ✅ | Μέσω signal-cli |
| 🟣 **Discord** | ✅ Πλήρες | ✅ | Ανίχνευση guild + καναλιού |
| 🟪 **Slack** | ✅ Πλήρες | ✅ | Ανίχνευση workspace + καναλιού |
| 🌐 **Webchat** | ✅ Πλήρες | ✅ | Ενσωματωμένες συνεδρίες web UI |
| 📡 **IRC** | ✅ Πλήρες | ✅ | Διεπαφή φυσαλίδων τύπου τερματικού |
| 🍏 **BlueBubbles** | ✅ Πλήρες | ✅ | iMessage μέσω BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Πλήρες | ✅ | Μέσω webhooks του Chat API |
| 🟣 **MS Teams** | ✅ Πλήρες | ✅ | Μέσω plugin bot Teams |
| 🔷 **Mattermost** | ✅ Πλήρες | ✅ | Αυτοφιλοξενούμενη ομαδική συνομιλία |
| 🟩 **Matrix** | ✅ Πλήρες | ✅ | Αποκεντρωμένο, υποστήριξη E2EE |
| 🟢 **LINE** | ✅ Πλήρες | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Πλήρες | ✅ | Αποκεντρωμένα NIP-04 DMs |
| 🟣 **Twitch** | ✅ Πλήρες | ✅ | Συνομιλία μέσω σύνδεσης IRC |
| 🔷 **Feishu/Lark** | ✅ Πλήρες | ✅ | Συνδρομή γεγονότων WebSocket |
| 🔵 **Zalo** | ✅ Πλήρες | ✅ | Zalo Bot API |

> **Αυτόματη ανίχνευση:** Το ClawMetry διαβάζει το `~/.openclaw/openclaw.json` σου και αποδίδει μόνο τα κανάλια που έχεις όντως ρυθμίσει. Δεν απαιτείται χειροκίνητη ρύθμιση.

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

> **Σημείωση:** Όταν τρέχεις σε Docker, προσάρτησε τους καταλόγους δεδομένων + logs του agent σου (π.χ. `~/.openclaw`, `~/.claude`, `~/.codex`) ώστε το ClawMetry να μπορεί να ανιχνεύσει αυτόματα τη ρύθμισή σου.

## Απαιτήσεις

- Python 3.8+
- Flask (εγκαθίσταται αυτόματα μέσω pip)
- Ένα runtime AI agent στο ίδιο μηχάνημα: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, ή Deep Agents (ή προσαρτημένοι τόμοι για Docker)
- Linux ή macOS

## Υποστήριξη NemoClaw / OpenShell

Το ClawMetry ανιχνεύει αυτόματα το [NemoClaw](https://github.com/NVIDIA/NemoClaw) — το επιχειρησιακό περιτύλιγμα ασφαλείας της NVIDIA για το OpenClaw που τρέχει agents μέσα σε sandboxed containers OpenShell.

Δεν χρειάζεται επιπλέον ρύθμιση στις περισσότερες περιπτώσεις. Ο daemon συγχρονισμού ανακαλύπτει αυτόματα τα αρχεία συνεδρίας είτε βρίσκονται στο `~/.openclaw/` στον host είτε μέσα σε ένα container OpenShell.

### Πώς λειτουργεί

Το ClawMetry ανιχνεύει το NemoClaw με δύο τρόπους:

1. **Ανίχνευση δυαδικού** — ελέγχει για το CLI `nemoclaw` και τρέχει `nemoclaw status` για να πάρει πληροφορίες sandbox
2. **Ανίχνευση container** — σαρώνει τα τρέχοντα containers Docker για εικόνες `openshell`, `nemoclaw`, ή `ghcr.io/nvidia/`, και έπειτα διαβάζει συνεδρίες μέσω προσαρτήσεων τόμων ή `docker cp`

Τα αρχεία συνεδρίας που συγχρονίζονται από containers NemoClaw επισημαίνονται με μεταδεδομένα `runtime=nemoclaw` και `container_id` στο cloud dashboard, ώστε να μπορείς να τα ξεχωρίσεις από τις τυπικές συνεδρίες OpenClaw με μια ματιά.

### Προτεινόμενη ρύθμιση: daemon συγχρονισμού στον HOST

Για την καλύτερη εμπειρία, τρέξε τον daemon συγχρονισμού του ClawMetry στο **μηχάνημα host** (όχι μέσα στο sandbox). Αυτό αποφεύγει τους περιορισμούς πολιτικής δικτύου του NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Ο daemon συγχρονισμού θα βρει αυτόματα συνεδρίες μέσα σε οποιαδήποτε τρέχοντα containers OpenShell.

### Προαιρετικό: ρητό όνομα sandbox

Αν η αυτόματη ανίχνευση δεν λειτουργεί, κατεύθυνε το ClawMetry στο σωστό sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Εκτέλεση μέσα στο sandbox (προχωρημένο)

Αν πρέπει να τρέξεις τον daemon συγχρονισμού **μέσα** στο sandbox OpenShell, πρόσθεσε αυτόν τον κανόνα εξόδου (egress) στην πολιτική δικτύου του NemoClaw ώστε να μπορεί να φτάσει το API εισαγωγής του ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Ναι (τοπικό UI dashboard) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Για ανακάλυψη συνεδριών container |

Ο daemon συγχρονισμού κάνει μόνο εξερχόμενες κλήσεις HTTPS προς το `ingest.clawmetry.com`. Δεν απαιτούνται εισερχόμενες θύρες.

---

## Ανάπτυξη στο Cloud

Δες τον **[Οδηγό Δοκιμών Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** για SSH tunnels, reverse proxy, και Docker.

## Δοκιμές

Αυτό το έργο δοκιμάζεται με το BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Τηλεμετρία

Το ClawMetry στέλνει ένα και μόνο ανώνυμο ping "πρώτης εκτέλεσης" στο
`https://app.clawmetry.com/api/install` την πρώτη φορά που τρέχεις την εντολή
`clawmetry` σε ένα νέο μηχάνημα. Το χρησιμοποιούμε αυτό για να μετράμε εγκαταστάσεις (η
μόνη μετρική μάρκετινγκ που έχουμε για ένα έργο ανοιχτού κώδικα) και για να μάθουμε ποια
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

**Τι ΔΕΝ στέλνουμε**: IP (το cloud προκύπτει τον κωδικό χώρας από τον διακομιστή
από το αίτημα, και έπειτα απορρίπτει την IP), όνομα host, όνομα χρήστη, διαδρομή
χώρου εργασίας, περιεχόμενα αρχείων, το api_key σου, το email σου, οτιδήποτε προσωπικά
αναγνωρίσιμο ή ειδικό για τον χώρο εργασίας σου. Το ωφέλιμο φορτίο (payload) είναι ελέγξιμο στο
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Εξαίρεση** (οποιοδήποτε από αυτά την απενεργοποιεί μόνιμα):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Μια αποτυχία δικτύου εδώ δεν εμποδίζει ποτέ το `clawmetry` να τρέξει — το ping
είναι fire-and-forget σε ένα νήμα daemon με χρονικό όριο 3 δευτερολέπτων.

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
  <strong>🦞 Δες τον agent σου να σκέφτεται</strong><br>
  <sub>Φτιαγμένο από τον <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Μέρος του οικοσυστήματος <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
