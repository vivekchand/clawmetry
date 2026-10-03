<!-- i18n-src:b22579578775 -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ένας agent μπορεί να κάνει εκατό tool calls χωρίς να σημειώσει καμία πρόοδο.** Το ClawMetry
διαβάζει τα αρχεία session που ήδη γράφουν οι coding agents σου, και βάζει το χρονοδιάγραμμα,
τα tool calls και όποια δεδομένα token και κόστους εκθέτει το runtime σε μία
προβολή — ώστε να ξεχωρίζεις μια μεγάλη εκτέλεση που δουλεύει από μία που έχει κολλήσει.

Δουλεύει με **33 AI agent runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 29 ακόμα. Ένα dashboard για ολόκληρο τον στόλο agents σου. ([η πλήρης λίστα](SUPPORTED_RUNTIMES.txt), παραγόμενη από τον κατάλογο.)

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Καμία ρύθμιση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900**. Καμία ρύθμιση: βρίσκει τα agent runtimes
που ήδη έχεις, τα διαβάζει μόνο για ανάγνωση, και δεν αλλάζει τίποτα στον τρόπο που τρέχουν.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Πριν εγκαταστήσεις

| | |
|---|---|
| **Τι κάνει** | Διαβάζει τα αρχεία session και τα logs που ήδη γράφουν οι agents σου. Χωρίς SDK, χωρίς αλλαγή κώδικα, χωρίς instrumentation στην εφαρμογή σου. |
| **Τι βλέπεις** | Χρονοδιάγραμμα session, αναπαραγωγή ανά tool, ανάλυση tokens και κόστους, και σήματα πορείας (loop, επαναλαμβανόμενες αποτυχίες) — ανά runtime. |
| **Τι είναι δωρεάν** | Το `pip install clawmetry` διαβάζει τα **OpenClaw, NVIDIA NemoClaw, Goose και Qwen Code** χωρίς λογαριασμό, χωρίς κλειδί και χωρίς κλήση δικτύου. Τα υπόλοιπα 28 — Claude Code, Codex, Cursor και τα λοιπά — διαβάζονται από το κλειστού κώδικα συνοδευτικό `clawmetry-pro`, που έρχεται με τη 7ήμερη δοκιμή ή ένα πλάνο — δες [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) για τον ακριβή διαχωρισμό. |
| **Πώς να ξεκινήσεις** | `pip install clawmetry && clawmetry`, μετά άνοιξε το localhost:8900. Δεν έχεις ακόμα agents σε αυτό το μηχάνημα; Το `clawmetry --sample` ανοίγει με τρία επισημασμένα συνθετικά sessions. |
| **Τι φεύγει από το μηχάνημά σου** | Κανένα δεδομένο session, εκτός αν τρέξεις το `clawmetry connect`. Δύο πράγματα τρέχουν από προεπιλογή, και τα δύο με δυνατότητα απενεργοποίησης και χωρίς κανένα από τα δύο να μεταφέρει περιεχόμενο session: ένα ανώνυμο ping εγκατάστασης και έλεγχος έκδοσης στο PyPI. Κάθε προορισμός καταγράφεται στο [docs/EGRESS.md](docs/EGRESS.md), ανακατασκευασμένος από καταγραφή δικτύου και όχι από ανάγνωση σχολίων. |

Δύο περιορισμοί αξίζει να τους γνωρίζεις πριν κρίνεις το αποτέλεσμα: τα runtimes εκθέτουν πολύ
διαφορετικά δεδομένα (κάποια δεν δημοσιεύουν καθόλου κόστος — [ο πίνακας](docs/compatibility.md)
λέει ποια, ανά runtime), και το να παρατηρείς μια ενέργεια δεν είναι το ίδιο με το να μπορείς
να την μπλοκάρεις ([ποιοι έλεγχοι είναι πραγματικοί, ανά runtime](docs/APPROVALS.md)).


## Δουλεύει με 33 agent runtimes

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime παίρνει το ίδιο dashboard. Τρέξε πολλά ταυτόχρονα και ο επιλογέας στην κεφαλίδα
προσαρμόζει κάθε καρτέλα σε ένα από αυτά.

Έχτισες τον δικό σου agent πάνω σε ένα SDK αντί για κάτι από τα παραπάνω; Ο interceptor παρακολουθεί και τις κλήσεις LLM του.
Δες [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι παίρνεις

- **Sessions & transcripts**: τι έκανε κάθε agent, γύρο προς γύρο, με αναπαραγωγή
- **Κόστος & tokens**: ανά runtime, μοντέλο, session και ημέρα, με σημάνσεις ανωμαλιών
- **Flow**: ζωντανό διάγραμμα των μηνυμάτων που κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων συλλογισμού και tool-call καθώς συμβαίνει
- **Context blowout**: αξιοποίηση παραθύρου μεγεθοποιημένη ανά πάροχο, compaction έναντι εξαναγκασμένου overflow, συν έναν χάρτη ανά runtime για το τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: τα αρχεία και τα skills που πράγματι φόρτωσε κάθε runtime
- **Health & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, rate limits, ζωντανή ροή logs
- **Alerts**: όρια προϋπολογισμού, εξάρσεις σφαλμάτων, agent-offline, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: παύση επικίνδυνων tool calls *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Context blowout, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα αξίζει να απαντηθούν πριν εμπιστευτείς οποιοδήποτε εργαλείο σύγκρισης agents.

**Πώς χειρίζεται το context-window blowout σε διαφορετικά runtimes;**

Ένα ποσοστό αξιοποίησης είναι τόσο ειλικρινές όσο και ο διαιρέτης του. Το ClawMetry
μεγεθοποιεί το παράθυρο ανά πάροχο από [έναν πίνακα που μπορείς να διαβάσεις και να κάνεις
PR](clawmetry/context_windows.py), καλύπτοντας Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετράει και τα 33
runtimes με τον χάρακα ενός μόνο προμηθευτή. Αυτό έχει σημασία: ένα turn 300K GPT-5
βαθμολογημένο με βάση τα 200K της Anthropic διαβάζεται ως ">100%, blown" ενώ στην
πραγματικότητα είναι στο 75% των 400K του GPT-5. Ο ίδιος χάρακας κρύβει ένα πραγματικά
υπερχειλισμένο turn 130K DeepSeek ως ένα άνετο 65%.

Κάθε παράθυρο συνοδεύεται από την προέλευσή του: `model_table`, `explicit_marker`,
`observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένας
μετρητής χτισμένος πάνω σε μια εικασία δεν εμφανίζεται ποτέ με την ίδια αυθεντία με έναν
χτισμένο πάνω σε αναζήτηση.

Το ClawMetry μπορεί να δει τα συμβάντα compaction μόνο σε ορισμένα runtimes. Έτσι το
`GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα **μηδέν σημαίνει
"έτρεξε καθαρά" ή "δεν βλέπουμε"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλό, το λέει.
[Πλήρεις λεπτομέρειες](docs/CONTEXT_BLOWOUT.md)

**Πόσο κοστίζει το instrumentation;**

| Διαδρομή | Προστίθεται στον agent σου | Προεπιλογή; |
|---|---|---|
| Tailing αρχείων session (και τα 33 runtimes) | **0**. Ξεχωριστή διεργασία, χωρίς κώδικα ClawMetry στον agent σου | ενεργό |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** ανά κλήση LLM, ή 0,009% ενός κλήσης 5s | ανενεργό |
| Pre-tool hook gate (ζεστή cache) | **+44 ms** ανά ελεγχόμενη κλήση tool, πάνω από ένα κατώφλι διερμηνέα 36 ms | ανενεργό |
| Enforcement proxy | **+9,7 ms** ανά κλήση LLM | ανενεργό |

Κόστος host daemon: **2.762 events/sec** ingest, **710 bytes/event** στον δίσκο
(67,7 MB ανά 100k events), και **~12% ενός πυρήνα** διαρκώς σε μια απασχολημένη
εγκατάσταση. Αυτός ο τελευταίος αριθμός ξεπερνά το δικό μας δηλωμένο προϋπολογισμό 5-10%,
οπότε δημοσιεύεται ως bug προς διόρθωση αντί να παραλειφθεί από τη σελίδα.

Μετρήθηκε σε Apple M2 Pro με το `benchmarks/overhead.py`. Το harness τρέχει
κάθε συνθήκη σε ξεχωριστή διεργασία, εναλλάσσει τη σειρά τους, και **αρνείται
να τυπώσει έναν αριθμό όταν οι γύροι διαφωνούν ως προς το πρόσημό του**. Τρέξ' το στο δικό σου
μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των hook gates και του enforcement proxy,
και το harness τρέχει σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα αξίζει να τα
γνωρίζεις: ο proxy κοστίζει περίπου επτά φορές περισσότερο σε Windows απ' ό,τι σε Linux, και
ο daemon αυτή τη στιγμή διατηρεί περίπου το 12% ενός πυρήνα, πάνω από τον δικό μας
προϋπολογισμό 5-10%. Το ακατέργαστο JSON, η μέθοδος, και τι παραμένει αμέτρητο βρίσκονται στο
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Δωρεάν** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, cloud sync | $9 ανά node / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: approvals, πολιτικές κινδύνου εργαλείων, evals, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, αλλοιωμένο-αδιαφανές αρχείο ελέγχου | $19 ανά node / μήνα |

Τα ετήσια πλάνα, το Enterprise και οι τρέχουσες τιμές βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα κλειδιά αδειοδότησης self-hosted
λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός δωρεάν/πληρωμένου είναι
στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία session και logs. **Κανένα δεδομένο session δεν φεύγει από το μηχάνημά σου
εκτός αν τρέξεις το `clawmetry connect`** — καθόλου prompts, απαντήσεις, ορίσματα εργαλείων, περιεχόμενα
αρχείων ή γραμμές logs. Όταν συνδεθείς, το snapshot κρυπτογραφείται end-to-end
με ένα κλειδί που δεν φεύγει ποτέ από το μηχάνημά σου, και αποκρυπτογραφείται στον browser σου. Αν ένας
κόμβος δεν έχει κλειδί, η μεταφόρτωση παραλείπεται αντί να σταλεί ανοιχτά, και καμία
απάντηση server δεν μπορεί να το απενεργοποιήσει.

Δύο πράγματα τρέχουν από προεπιλογή πριν συνδεθείς, και τα δύο με δυνατότητα απενεργοποίησης και χωρίς κανένα
να μεταφέρει δεδομένα session: ένα ανώνυμο ping εγκατάστασης και έλεγχος έκδοσης έναντι του
PyPI. Μια προεπιλεγμένη εγκατάσταση επίσης αναζητά τη δημόσια IP σου μία φορά για μια γραμμή banner εκκίνησης.
Κάθε προορισμός, τι μεταφέρει και πώς να τον απενεργοποιήσεις, καταγράφεται στο
[docs/EGRESS.md](docs/EGRESS.md)· οι εγκαταστάσεις self-hosted, ανακατευθυνόμενες και air-gapped
δεν κάνουν καμία προαιρετική εξερχόμενη κλήση καθόλου.

Η αποκρυπτογράφηση συμβαίνει στον browser σου, σε κώδικα που σου παρέχουμε. Αυτό κάποτε ήταν
μια υπόσχεση· τώρα είναι κάτι που μπορείς να ελέγξεις. Κάθε γραμμή που αγγίζει το κλειδί σου
βρίσκεται σε ένα αναγνώσιμο αρχείο, το [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
που αποστέλλεται μέσα στο wheel και εξυπηρετείται αυτούσιο, καρφωμένο με ένα hash Subresource
Integrity. Για να επιβεβαιώσεις ότι ο browser τρέχει αυτό που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Αυτό που δεν αποδεικνύει: εμείς εξυπηρετούμε τη σελίδα που φορτώνει το αρχείο, άρα θα μπορούσαμε να
εξυπηρετήσουμε διαφορετική σελίδα. Τα hashes ακεραιότητας σε προστατεύουν από μια παραβιασμένη CDN,
όχι από τον προμηθευτή. Αυτό που κερδίζεις είναι ότι κάθε αντικατάσταση πρέπει να είναι
σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική από ένα artifact στο PyPI
που μπορεί να ανακτήσει οποιοσδήποτε. Το self-hosting ή η παραμονή μόνο τοπικά αφαιρεί
την εξάρτηση εντελώς.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή η one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Χρειάζεται Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα agent runtime στο
ίδιο μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ή άσε τον agent να το εγκαταστήσει για σένα. Το skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
διδάσκει στα Claude Code, Codex, Cursor, Gemini CLI, Copilot ή OpenCode να
εγκαταστήσουν το ClawMetry, να αναφέρουν τι κάνουν και τι ξοδεύουν οι agents στο μηχάνημα,
να σταματήσουν ένα session κατόπιν αιτήματος, και να κρατούν επικίνδυνα tool calls για έγκριση:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσεις ένα runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά πάροχο, compaction έναντι overflow, κάλυψη ανά runtime |
| [Overhead](docs/OVERHEAD.md) | Τι κοστίζει το instrumentation, μετρημένο, με το harness για αναπαραγωγή |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας επιπέδων, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οπουδήποτε |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain από άκρη σε άκρη, με εκτελέσιμα παραδείγματα |
| [SDK tracking](docs/SDK_TRACKING.md) | Απόδοση κόστους για agents που έχτισες μόνος σου |
| [Chat channels](docs/CHANNELS.md) | Οι chat adapters που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Απομονωμένες (sandboxed) ρυθμίσεις NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Telemetry](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος desktop, και πώς να τα απενεργοποιήσεις |

## Screenshots

Κάθε αριθμός παρακάτω προέρχεται από ένα πραγματικό μηχάνημα, μόνο για ανάγνωση, χωρίς τίποτα προκατασκευασμένο.

**Σου λέει πότε κάτι πάει στραβά, όχι απλώς τι συνέβη.**
Δύο banner ανωμαλιών στην κορυφή: δαπάνη που τρέχει 7 φορές τον ημερήσιο μέσο όρο, και μια
αιχμή κόστους 4,2 φορές. Από κάτω, 324 από τα 667 πρόσφατα sessions φέρουν ένα σήμα
σπατάλης, κατηγοριοποιημένο ανά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σου δείχνει πού πήγαν τα χρήματα, σε κάθε παράθυρο χρόνου.**
$252,47 σήμερα, $513,15 αυτή την εβδομάδα, $1.312,92 αυτόν τον μήνα, το καθένα με τα tokens
από πίσω τους και πόσο από αυτά καλύπτει ήδη η συνδρομή σου. Από κάτω, περίπου
$1.128/μήνα κατηγοριοποιημένα ως ανακτήσιμα και $17.256/μήνα ήδη εξοικονομημένα από
επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα flow: εσύ, το κανάλι από το οποίο έφτασε, το gateway, το μοντέλο
που απαντά αυτή τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν καθώς η εργασία
περνάει μέσα από αυτούς.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε agent στο μηχάνημα, σε έναν πίνακα.**
Τι τρέχει, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη του τη διάρκεια ζωής, πότε
εμφανίστηκε τελευταία φορά, ποιος τον κατέχει, και αν κάποια συνδρομή καλύπτει τον λογαριασμό. 14 agents εδώ, 3 sessions να δουλεύουν, 13 αδρανή.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Δείχνει πού πήγε ο χρόνος και τα χρήματα ενός γύρου, εργαλείο προς εργαλείο.**
Ένας γύρος ενός πραγματικού session: 11 εργαλεία σε 11,2 λεπτά για $1,16. Κάθε κλήση Bash
και κλήση μοντέλου παίρνει τη δική της μπάρα στο χρονοδιάγραμμα, ώστε η εντολή που έτρεξε
για 4,1 λεπτά και αυτή που έτρεξε για 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί τη δουλειά, όχι μόνο τη δαπάνη.**
Ένα Α αυτή την εβδομάδα: 54 εργασίες ολοκληρώθηκαν καθαρά, 2 δύσκολες κόστισαν $48,57, και οι
εκτελέσεις με πολύ λίγη δραστηριότητα για να κριθούν αφήνονται εκτός βαθμολογίας αντί να
μετρηθούν ως επιτυχίες. Κάθε δύσκολη εκτέλεση συνδέεται με το trace της.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από ένα παράθυρο 1M tokens στον τελευταίο γύρο, μια κορύφωση 83,3%, 4 compactions
που πυροδοτήθηκαν όλα προληπτικά αντί λόγω overflow, και η αξιοποίηση κάθε γύρου
από πίσω τους.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Η ανίχνευση λειτουργεί χωρίς να ρυθμίσεις τίποτα.**
Οι ενσωματωμένοι detectors είναι ενεργοί από την εγκατάσταση: ο agent σώπασε, η ροή τηλεμετρίας
σταμάτησε, αιχμή κόστους, έκρηξη tokens, αυξανόμενα σφάλματα, αιχμή σφαλμάτων, όριο
προϋπολογισμού, υπογραφή απειλής που ταιριάξε, εύρημα εργαλείου ασφάλειας, αλλαγή στάσης
ασφάλειας. Οι δικοί σου κανόνες είναι προαιρετικοί επιπλέον.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η αναστολή μιας επικίνδυνης κλήσης είναι προαιρετική, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, force pushes, sudo, μυστικά, εγκαταστάσεις πακέτων και εξερχόμενες
κλήσεις παίρνουν η καθεμία έναν κανόνα που μπορείς να ενεργοποιήσεις. Μέχρι να το κάνεις, το ClawMetry
παρακολουθεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί ένας, οι κλήσεις που ταιριάζουν περιμένουν
εδώ (ή στο κινητό σου) για έγκριση ή απόρριψη.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Περισσότερα, ανά runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Αναγνώριση

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Ιστορικό Αστεριών

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια χρήσης

MIT · Φτιαγμένο από τον [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
