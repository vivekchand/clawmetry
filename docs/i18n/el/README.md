<!-- i18n-src:88be2deff5d5 -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Δες τον agent σου να σκέφτεται.** Παρατήρηση σε πραγματικό χρόνο για **30 runtimes AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 ακόμη. Ένας πίνακας ελέγχου για ολόκληρο τον στόλο σου από agents.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική ρύθμιση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900**. Μηδενική ρύθμιση: εντοπίζει τα runtimes agent που ήδη έχεις, τα διαβάζει μόνο για ανάγνωση, και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Λειτουργεί με 30 runtimes agent

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime παίρνει τον ίδιο πίνακα ελέγχου. Τρέξε πολλά ταυτόχρονα και ο επιλογέας στην κεφαλίδα επαναπροσδιορίζει κάθε καρτέλα σε ένα από αυτά.

Έχτισες τον δικό σου agent πάνω σε ένα SDK αντί για κάτι έτοιμο; Ο interceptor παρακολουθεί και τις δικές του κλήσεις LLM. Δες [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι αποκτάς

- **Sessions & transcripts**: τι έκανε κάθε agent, γύρο προς γύρο, με replay
- **Κόστος & tokens**: ανά runtime, μοντέλο, session και ημέρα, με σημαίες ανωμαλιών
- **Flow**: ζωντανό διάγραμμα των μηνυμάτων καθώς κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων σκέψης και κλήσεων εργαλείων τη στιγμή που συμβαίνει
- **Context blowout**: αξιοποίηση του παραθύρου με μέγεθος ανά provider, compaction έναντι εξαναγκασμένου overflow, συν έναν χάρτη ανά runtime για το τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: τα αρχεία και τα skills που φόρτωσε πράγματι κάθε runtime
- **Health & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, όρια ρυθμού, ζωντανή ροή logs
- **Alerts**: όρια προϋπολογισμού, αιχμές σφαλμάτων, agent-offline, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: παύση ριψοκίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Context blowout, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα που αξίζει να απαντηθούν πριν εμπιστευτείς οποιοδήποτε εργαλείο σύγκρισης agents.

**Πώς χειρίζεται το context-window blowout σε διαφορετικά runtimes;**

Ένα ποσοστό αξιοποίησης είναι τόσο ειλικρινές όσο και το μέγεθος με το οποίο διαιρεί. Το ClawMetry προσαρμόζει το μέγεθος του παραθύρου ανά provider από [έναν πίνακα που μπορείς να διαβάσεις και να στείλεις PR](clawmetry/context_windows.py), που καλύπτει Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετρά και τα 30 runtimes με τον χάρακα ενός προμηθευτή. Αυτό έχει σημασία: ένας γύρος 300K GPT-5 βαθμολογημένος με βάση τα 200K της Anthropic διαβάζεται ως ">100%, blown" ενώ στην πραγματικότητα βρίσκεται στο 75% των 400K του GPT-5. Ο ίδιος χάρακας κρύβει έναν πραγματικά υπερχειλισμένο γύρο 130K DeepSeek ως ένα άνετο 65%.

Κάθε παράθυρο συνοδεύεται από την προέλευσή του: `model_table`, `explicit_marker`,
`observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένα μετρητικό στοιχείο χτισμένο πάνω σε μια εικασία δεν αποδίδεται ποτέ με την ίδια αξιοπιστία όσο ένα χτισμένο πάνω σε αναζήτηση.

Το ClawMetry μπορεί να δει τα γεγονότα compaction μόνο σε ορισμένα runtimes. Έτσι το `GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα **μηδέν σημαίνει "έτρεξε καθαρά" ή "είμαστε τυφλοί"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλό, το δηλώνει.
[Πλήρης λεπτομέρεια](docs/CONTEXT_BLOWOUT.md)

**Πόσο κοστίζει η ενοργάνωση (instrumentation);**

| Διαδρομή | Προστίθεται στον agent σου | Προεπιλογή; |
|---|---|---|
| Session-file tailing (και τα 30 runtimes) | **0**. Ξεχωριστή διεργασία, καθόλου κώδικας ClawMetry μέσα στον agent σου | ναι |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ανά κλήση LLM, ή 0.009% μιας κλήσης 5s | όχι |
| Pre-tool hook gate (θερμή cache) | **+44 ms** ανά ελεγχόμενη κλήση εργαλείου, πάνω από ένα κατώφλι interpreter 36 ms | όχι |
| Enforcement proxy | **+9.7 ms** ανά κλήση LLM | όχι |

Κόστος daemon host: **2.762 events/sec** εισαγωγή, **710 bytes/event** στον δίσκο
(67,7 MB ανά 100k events), και **~12% ενός πυρήνα** διαρκώς σε μια απασχολημένη εγκατάσταση. Αυτός ο τελευταίος αριθμός είναι πάνω από τον δικό μας δηλωμένο προϋπολογισμό 5-10%, οπότε δημοσιεύεται ως bug προς επίλυση αντί να παραλειφθεί από τη σελίδα.

Μετρήθηκε σε Apple M2 Pro με το `benchmarks/overhead.py`. Το harness τρέχει
κάθε συνθήκη σε ξεχωριστή διεργασία, εναλλάσσει τη σειρά τους, και **αρνείται
να τυπώσει έναν αριθμό όταν οι γύροι διαφωνούν ως προς το πρόσημό του**. Τρέξ'το στο δικό σου μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των hook gates και του enforcement proxy, και το harness τρέχει σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα που αξίζει να γνωρίζεις: ο proxy κοστίζει περίπου επτά φορές περισσότερο σε Windows απ' ό,τι σε Linux, και ο daemon επί του παρόντος διατηρεί περίπου το 12% ενός πυρήνα, πάνω από τον δικό μας προϋπολογισμό 5-10%. Το ακατέργαστο JSON, η μέθοδος, και τι παραμένει αμέτρητο βρίσκονται στο
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Δωρεάν** | OpenClaw + NVIDIA NemoClaw + Goose, πλήρης πίνακας ελέγχου, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, συγχρονισμός στο cloud | $9 ανά κόμβο / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: approvals, πολιτικές κινδύνου εργαλείων, evals, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, αρχείο ελέγχου (audit log) ανθεκτικό σε παραποίηση | $19 ανά κόμβο / μήνα |

Τα ετήσια πλάνα, το Enterprise και οι τρέχοντες αριθμοί βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα self-hosted κλειδιά αδειοδότησης λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός δωρεάν/πληρωμένου βρίσκεται στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία sessions και logs. **Κανένα δεδομένο session δεν φεύγει από το μηχάνημά σου εκτός αν τρέξεις `clawmetry connect`** — καμία προτροπή (prompt), απάντηση, όρισμα εργαλείου, περιεχόμενο αρχείου ή γραμμή log. Όταν συνδεθείς, το στιγμιότυπο κρυπτογραφείται από άκρο σε άκρο (end-to-end) με ένα κλειδί που δεν φεύγει ποτέ από το μηχάνημά σου, και αποκρυπτογραφείται στο πρόγραμμα περιήγησής σου. Αν ένας κόμβος δεν έχει κλειδί, η μεταφόρτωση παραλείπεται αντί να σταλεί ανεπεξέργαστη, και καμία απάντηση διακομιστή δεν μπορεί να το απενεργοποιήσει αυτό.

Δύο πράγματα εκτελούνται εξ ορισμού πριν συνδεθείς, και τα δύο opt-out και κανένα δεν μεταφέρει δεδομένα session: ένα ανώνυμο ping εγκατάστασης και ένας έλεγχος έκδοσης έναντι του PyPI. Μια προεπιλεγμένη εγκατάσταση επίσης αναζητά τη δημόσια IP σου μία φορά για μια γραμμή banner εκκίνησης. Κάθε προορισμός, τι μεταφέρει και πώς να τον απενεργοποιήσεις είναι καταγεγραμμένα στο
[docs/EGRESS.md](docs/EGRESS.md)· εγκαταστάσεις self-hosted, ανακατευθυνόμενες και air-gapped δεν κάνουν καθόλου προαιρετικές εξωτερικές κλήσεις.

Η αποκρυπτογράφηση γίνεται στο πρόγραμμα περιήγησής σου, με κώδικα που σου σερβίρουμε εμείς. Αυτό παλιά ήταν μια υπόσχεση· τώρα είναι κάτι που μπορείς να ελέγξεις. Κάθε γραμμή που αγγίζει το κλειδί σου βρίσκεται σε ένα μόνο αναγνώσιμο αρχείο, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
που αποστέλλεται μέσα στο wheel και σερβίρεται αυτούσιο, καθηλωμένο με ένα Subresource Integrity hash. Για να επιβεβαιώσεις ότι το πρόγραμμα περιήγησης τρέχει αυτό που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Τι δεν αποδεικνύει αυτό: εμείς σερβίρουμε τη σελίδα που φορτώνει το αρχείο, οπότε θα μπορούσαμε να σερβίρουμε διαφορετική σελίδα. Τα integrity hashes σε προστατεύουν από ένα παραβιασμένο CDN, όχι από τον προμηθευτή. Αυτό που κερδίζεις είναι ότι οποιαδήποτε αντικατάσταση πρέπει να είναι σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική από ένα αρτεφακτ στο PyPI που μπορεί να ανακτήσει ο καθένας. Το self-hosting ή η παραμονή μόνο τοπικά αφαιρεί εντελώς αυτή την εξάρτηση.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή η εντολή μιας γραμμής: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Απαιτεί Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα runtime agent στο ίδιο μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ή άσε τον agent να το ρυθμίσει για σένα. Το skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
διδάσκει στα Claude Code, Codex, Cursor, Gemini CLI, Copilot ή OpenCode να
εγκαταστήσουν το ClawMetry, να αναφέρουν τι κάνουν και τι ξοδεύουν οι agents στο μηχάνημα,
να σταματήσουν ένα session κατ' αίτηση, και να κρατούν ριψοκίνδυνες κλήσεις εργαλείων για έγκριση:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσεις ένα runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά provider, compaction έναντι overflow, κάλυψη ανά runtime |
| [Overhead](docs/OVERHEAD.md) | Τι κοστίζει η ενοργάνωση, μετρημένο, με το harness για να το αναπαραγάγεις |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας βαθμίδων, license CLI |
| [Approvals & πολιτικές](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οτιδήποτε |
| [Φέρε τον δικό σου agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain από άκρο σε άκρο, με εκτελέσιμα παραδείγματα |
| [Παρακολούθηση SDK](docs/SDK_TRACKING.md) | Απόδοση κόστους για agents που έχτισες εσύ ο ίδιος |
| [Κανάλια συνομιλίας](docs/CHANNELS.md) | Οι adapters συνομιλίας που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ρυθμίσεις sandboxed NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος desktop, και πώς να τα απενεργοποιήσεις |

## Στιγμιότυπα οθόνης

Κάθε αριθμός παρακάτω προέρχεται από ένα πραγματικό μηχάνημα, μόνο για ανάγνωση, χωρίς τίποτα προκατασκευασμένο.

**Σου λέει πότε κάτι πάει στραβά, όχι απλώς τι συνέβη.**
Δύο banner ανωμαλιών στην κορυφή: δαπάνη στο 7x του ημερήσιου μέσου όρου, και μια
αιχμή κόστους 4.2x. Από κάτω τους, 324 από 667 πρόσφατα sessions που φέρουν ένα
σήμα σπατάλης, κατηγοριοποιημένα κατά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σου δείχνει πού πήγαν τα χρήματα, σε κάθε παράθυρο χρόνου.**
$252,47 σήμερα, $513,15 αυτή την εβδομάδα, $1.312,92 αυτόν τον μήνα, καθένα με τα
tokens από πίσω του και πόσο από αυτό καλύπτει ήδη η συνδρομή σου. Παρακάτω, περίπου
$1.128/μήνα κατηγοριοποιημένα ως ανακτήσιμα και $17.256/μήνα ήδη εξοικονομημένα από
επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα ροής: εσύ, το κανάλι από το οποίο ήρθε, το gateway, το μοντέλο
που απαντά αυτή τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν καθώς
η δουλειά περνάει μέσα από αυτούς.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε agent στο μηχάνημα, σε έναν πίνακα.**
Τι τρέχει, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη τη διάρκεια ζωής του, πότε
εμφανίστηκε τελευταία φορά, ποιος τον κατέχει, και αν μια συνδρομή καλύπτει τον
λογαριασμό. 14 agents εδώ, 3 sessions εν λειτουργία, 13 αδρανή.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Δείχνει πού πήγε ο χρόνος και τα χρήματα ενός γύρου, εργαλείο προς εργαλείο.**
Ένας γύρος ενός πραγματικού session: 11 εργαλεία σε 11,2 λεπτά για $1,16. Κάθε κλήση
Bash και κλήση μοντέλου παίρνει τη δική της μπάρα στο χρονοδιάγραμμα, ώστε η εντολή
που έτρεξε για 4,1 λεπτά και εκείνη που έτρεξε για 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί τη δουλειά, όχι μόνο τη δαπάνη.**
Ένα Α αυτή την εβδομάδα: 54 εργασίες ολοκληρώθηκαν καθαρά, 2 δύσκολες κόστισαν
$48,57, και οι εκτελέσεις με πολύ λίγη δραστηριότητα για να κριθούν εξαιρούνται από
τον βαθμό αντί να μετρηθούν ως νίκες. Κάθε δύσκολη εκτέλεση παραπέμπει στο δικό της trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από ένα παράθυρο 1M tokens στον τελευταίο γύρο, μια κορύφωση 83,3%, 4
compactions που όλα ενεργοποιήθηκαν προληπτικά αντί κατά την υπερχείλιση, συν
την αξιοποίηση κάθε γύρου από πίσω τους.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Η ανίχνευση λειτουργεί χωρίς να ρυθμίσεις τίποτα.**
Οι ενσωματωμένοι ανιχνευτές είναι ενεργοί από την εγκατάσταση: agent σταμάτησε να
ανταποκρίνεται, τροφοδοσία τηλεμετρίας διακόπηκε, αιχμή κόστους, έκρηξη tokens,
αυξανόμενα σφάλματα, αιχμή σφαλμάτων, όριο προϋπολογισμού, υπογραφή απειλής που
ταιριάζει, εύρημα εργαλείου ασφαλείας, αλλαγή στάσης ασφαλείας. Οι δικοί σου κανόνες
είναι προαιρετικοί από πάνω.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η αναστολή μιας ριψοκίνδυνης κλήσης είναι opt-in, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, force pushes, sudo, μυστικά (secrets), εγκαταστάσεις πακέτων
και εξερχόμενες κλήσεις παίρνουν η καθεμία έναν κανόνα που μπορείς να ενεργοποιήσεις.
Μέχρι να το κάνεις, το ClawMetry παρακολουθεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί
ένας, οι κλήσεις που ταιριάζουν περιμένουν εδώ (ή στο κινητό σου) για έγκριση ή απόρριψη.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Περισσότερα, ανά runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Ιστορικό Αστεριών

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια χρήσης

MIT · Κατασκευάστηκε από τον [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
