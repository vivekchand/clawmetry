<!-- i18n-src:9767c8001c9c -->
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

**Δες τον agent σου να σκέφτεται.** Παρατήρηση σε πραγματικό χρόνο για **30 runtimes AI agents**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 ακόμη. Ένα dashboard για ολόκληρο τον στόλο agents σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική διαμόρφωση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στη διεύθυνση **http://localhost:8900**. Μηδενική διαμόρφωση: βρίσκει τα runtimes agents που ήδη έχεις, τα διαβάζει μόνο για ανάγνωση, και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Λειτουργεί με 30 runtimes agents

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime λαμβάνει το ίδιο dashboard. Τρέξε πολλά ταυτόχρονα και ο επιλογέας στην κεφαλίδα επαναπροσδιορίζει κάθε καρτέλα σε ένα από αυτά.

Έφτιαξες τον δικό σου agent πάνω σε ένα SDK; Ο interceptor παρακολουθεί και τις δικές του κλήσεις LLM. Δες [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι αποκτάς

- **Sessions & transcripts**: τι έκανε κάθε agent, γύρο προς γύρο, με replay
- **Κόστος & tokens**: ανά runtime, μοντέλο, session και ημέρα, με σημάνσεις ανωμαλιών
- **Flow**: ζωντανό διάγραμμα μηνυμάτων που κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων συλλογισμού και κλήσεων εργαλείων καθώς συμβαίνουν
- **Context blowout**: η χρησιμοποίηση του παραθύρου προσαρμοσμένη ανά πάροχο, compaction έναντι εξαναγκασμένης υπερχείλισης, συν έναν χάρτη ανά runtime για το τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: τα αρχεία και τα skills που πράγματι φόρτωσε κάθε runtime
- **Health & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, όρια ρυθμού, ζωντανή ροή logs
- **Alerts**: όρια προϋπολογισμού, αιχμές σφαλμάτων, agent-offline, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: παύση ριψοκίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Context blowout, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα αξίζει να απαντηθούν πριν εμπιστευτείς οποιοδήποτε εργαλείο σύγκρισης agents.

**Πώς χειρίζεται την υπερχείλιση παραθύρου context σε διαφορετικά runtimes;**

Ένα ποσοστό χρησιμοποίησης είναι τόσο ειλικρινές όσο και ο διαιρέτης του. Το ClawMetry προσαρμόζει το μέγεθος του παραθύρου ανά πάροχο από [έναν πίνακα που μπορείς να διαβάσεις και να προτείνεις αλλαγές](clawmetry/context_windows.py), που καλύπτει Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετρά και τα 30 runtimes με τον χάρακα ενός μόνο προμηθευτή. Αυτό έχει σημασία: ένα turn 300K GPT-5, βαθμολογημένο με βάση τα 200K της Anthropic, εμφανίζεται ως ">100%, blown" ενώ στην πραγματικότητα βρίσκεται στο 75% των 400K του GPT-5. Ο ίδιος χάρακας κρύβει ένα πραγματικά υπερχειλισμένο turn 130K DeepSeek ως ένα άνετο 65%.

Κάθε παράθυρο συνοδεύεται από την προέλευσή του: `model_table`, `explicit_marker`, `observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένας μετρητής χτισμένος πάνω σε μια εικασία δεν εμφανίζεται ποτέ με την ίδια αυθεντία όσο ένας χτισμένος πάνω σε αναζήτηση.

Το ClawMetry μπορεί να δει γεγονότα compaction μόνο σε ορισμένα runtimes. Έτσι το `GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα **μηδέν σημαίνει "έτρεξε καθαρά" ή "είμαστε τυφλοί"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλός, το δηλώνει. [Πλήρης λεπτομέρεια](docs/CONTEXT_BLOWOUT.md)

**Τι κοστίζει η ενοργάνωση (instrumentation);**

| Διαδρομή | Προστίθεται στον agent σου | Προεπιλογή; |
|---|---|---|
| Παρακολούθηση αρχείου session (tailing, και τα 30 runtimes) | **0**. Ξεχωριστή διεργασία, κανένας κώδικας ClawMetry μέσα στον agent σου | ενεργό |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** ανά κλήση LLM, ή 0,009% μιας κλήσης 5s | ανενεργό |
| Pre-tool hook gate (warm cache) | **+44 ms** ανά ελεγχόμενη κλήση εργαλείου, πάνω από ένα κατώφλι διερμηνέα 36 ms | ανενεργό |
| Enforcement proxy | **+9,7 ms** ανά κλήση LLM | ανενεργό |

Κόστος host daemon: **2.762 γεγονότα/δευτ.** ingest, **710 bytes/γεγονός** στον δίσκο (67,7 MB ανά 100k γεγονότα), και **~12% ενός πυρήνα** σε συνεχή λειτουργία σε μια απασχολημένη εγκατάσταση. Αυτός ο τελευταίος αριθμός ξεπερνά τον δικό μας δηλωμένο προϋπολογισμό 5-10%, οπότε δημοσιεύεται ως σφάλμα προς επίλυση αντί να παραλειφθεί από τη σελίδα.

Μετρημένο σε Apple M2 Pro με το `benchmarks/overhead.py`. Το harness τρέχει κάθε συνθήκη σε ξεχωριστή διεργασία, εναλλάσσει τη σειρά τους, και **αρνείται να εκτυπώσει έναν αριθμό όταν οι γύροι διαφωνούν ως προς το πρόσημό του**. Τρέξ' το στο δικό σου μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των hook gates και του enforcement proxy, και το harness τρέχει σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα αξίζει να γνωρίζεις: ο proxy κοστίζει περίπου επτά φορές περισσότερο σε Windows απ' ό,τι σε Linux, και ο daemon επί του παρόντος διατηρεί περίπου το 12% ενός πυρήνα, πάνω από τον δικό μας προϋπολογισμό 5-10%. Τα ακατέργαστα δεδομένα JSON, η μεθοδολογία, και τι παραμένει αμέτρητο βρίσκονται στο [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, cloud sync | $9 ανά κόμβο / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: approvals, πολιτικές κινδύνου εργαλείων, evals, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, αρχείο ελέγχου (audit log) ανθεκτικό σε παραποίηση | $19 ανά κόμβο / μήνα |

Ετήσια πλάνα, Enterprise και οι τρέχοντες αριθμοί βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα κλειδιά αδειοδότησης self-hosted λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός δωρεάν/πληρωμένου βρίσκεται στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία session και logs. **Κανένα δεδομένο session δεν φεύγει από το μηχάνημά σου εκτός αν τρέξεις `clawmetry connect`** — κανένα prompt, καμία απάντηση, κανένα όρισμα εργαλείου, κανένα περιεχόμενο αρχείου ή γραμμή log. Όταν συνδεθείς, το snapshot κρυπτογραφείται από άκρο σε άκρο (end-to-end) με ένα κλειδί που δεν φεύγει ποτέ από το μηχάνημά σου, και αποκρυπτογραφείται στο πρόγραμμα περιήγησής σου. Αν ένας κόμβος δεν έχει κλειδί, η μεταφόρτωση παραλείπεται αντί να σταλεί ανεξέλεγκτα, και καμία απόκριση διακομιστή δεν μπορεί να το απενεργοποιήσει.

Δύο πράγματα τρέχουν από προεπιλογή πριν συνδεθείς, και τα δύο opt-out και κανένα από τα δύο δεν μεταφέρει δεδομένα session: ένα ανώνυμο ping εγκατάστασης και έλεγχος έκδοσης έναντι του PyPI. Μια προεπιλεγμένη εγκατάσταση αναζητά επίσης τη δημόσια IP σου μία φορά για μια γραμμή banner εκκίνησης. Κάθε προορισμός, τι μεταφέρει και πώς να τον απενεργοποιήσεις αναφέρεται στο [docs/EGRESS.md](docs/EGRESS.md)· εγκαταστάσεις self-hosted, με ανακατεύθυνση, ή απομονωμένες (air-gapped) δεν κάνουν καμία προαιρετική εξερχόμενη κλήση.

Η αποκρυπτογράφηση συμβαίνει στο πρόγραμμα περιήγησής σου, σε κώδικα που σου σερβίρουμε εμείς. Αυτό παλιά ήταν μια υπόσχεση· τώρα είναι κάτι που μπορείς να ελέγξεις. Κάθε γραμμή που αγγίζει το κλειδί σου βρίσκεται σε ένα ευανάγνωστο αρχείο, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), το οποίο συμπεριλαμβάνεται μέσα στο wheel και σερβίρεται αυτούσιο, καρφιτσωμένο με ένα Subresource Integrity hash. Για να επιβεβαιώσεις ότι το πρόγραμμα περιήγησης τρέχει αυτό που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Αυτό που δεν αποδεικνύει: εμείς σερβίρουμε τη σελίδα που φορτώνει το αρχείο, άρα θα μπορούσαμε να σερβίρουμε διαφορετική σελίδα. Τα integrity hashes σε προστατεύουν από ένα παραβιασμένο CDN, όχι από τον προμηθευτή. Αυτό που κερδίζεις είναι ότι οποιαδήποτε αντικατάσταση πρέπει να είναι σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική από ένα artifact στο PyPI που ο καθένας μπορεί να ανακτήσει. Το self-hosting ή η παραμονή μόνο τοπικά αφαιρεί εντελώς αυτή την εξάρτηση.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή η εντολή μιας γραμμής: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Χρειάζεται Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα runtime agent στο ίδιο μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσεις ένα runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά πάροχο, compaction έναντι υπερχείλισης, κάλυψη ανά runtime |
| [Overhead](docs/OVERHEAD.md) | Τι κοστίζει η ενοργάνωση, μετρημένο, με το harness για να το αναπαράγεις |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας επιπέδων, license CLI |
| [Approvals & πολιτικές](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από το κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οτιδήποτε |
| [Φέρε τον δικό σου agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain από άκρο σε άκρο, με εκτελέσιμα παραδείγματα |
| [Παρακολούθηση SDK](docs/SDK_TRACKING.md) | Απόδοση κόστους για agents που έφτιαξες μόνος σου |
| [Κανάλια συνομιλίας](docs/CHANNELS.md) | Οι adapters συνομιλίας που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Απομονωμένες (sandboxed) ρυθμίσεις NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος επιφάνειας εργασίας, και πώς να τα απενεργοποιήσεις |

## Στιγμιότυπα οθόνης

Κάθε αριθμός παρακάτω προέρχεται από ένα πραγματικό μηχάνημα, μόνο για ανάγνωση, χωρίς τίποτα προκατασκευασμένο.

**Σου λέει πότε κάτι πάει στραβά, όχι μόνο τι συνέβη.**
Δύο πλαίσια ανωμαλιών στο πάνω μέρος: δαπάνη που τρέχει 7 φορές πάνω από τον ημερήσιο μέσο όρο, και μια αιχμή κόστους 4,2x. Από κάτω, 324 από τα 667 πρόσφατα sessions φέρουν σήμα σπατάλης, αναλυμένα ανά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σου δείχνει πού πήγαν τα χρήματα, σε κάθε χρονικό παράθυρο.**
$252,47 σήμερα, $513,15 αυτή την εβδομάδα, $1.312,92 αυτόν τον μήνα, το καθένα με τα tokens από πίσω του και πόσο από αυτό καλύπτει ήδη η συνδρομή σου. Παρακάτω, περίπου $1.128/μήνα αναλυμένα ως ανακτήσιμα και $17.256/μήνα ήδη εξοικονομημένα από επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα ροής: εσύ, το κανάλι από το οποίο έφτασε, το gateway, το μοντέλο που απαντά αυτή τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν καθώς η εργασία περνάει μέσα από αυτούς.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε agent στο μηχάνημα, σε έναν πίνακα.**
Τι τρέχει, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη τη διάρκεια ζωής του, πότε φάνηκε τελευταία φορά, ποιος τον κατέχει, και αν μια συνδρομή καλύπτει τον λογαριασμό. 14 agents εδώ, 3 sessions σε λειτουργία, 13 ήσυχα.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Δείχνει πού πήγε ο χρόνος και το χρήμα ενός turn, εργαλείο προς εργαλείο.**
Ένα turn από πραγματικό session: 11 εργαλεία σε 11,2 λεπτά για $1,16. Κάθε κλήση Bash και κλήση μοντέλου παίρνει τη δική της μπάρα στο timeline, ώστε η εντολή που έτρεξε 4,1 λεπτά και αυτή που έτρεξε 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί τη δουλειά, όχι μόνο τη δαπάνη.**
Ένα A αυτή την εβδομάδα: 54 εργασίες ολοκληρώθηκαν καθαρά, 2 δύσκολες κόστισαν $48,57, και τα runs με πολύ λίγη δραστηριότητα για να κριθούν εξαιρούνται από τη βαθμολόγηση αντί να μετρηθούν ως επιτυχίες. Κάθε δύσκολο run συνδέεται με το trace του.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από παράθυρο 1M tokens στο τελευταίο turn, αιχμή 83,3%, 4 compactions που όλα ενεργοποιήθηκαν προληπτικά αντί λόγω υπερχείλισης, συν τη χρησιμοποίηση κάθε turn από πίσω τους.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Η ανίχνευση λειτουργεί χωρίς να διαμορφώσεις τίποτα.**
Οι ενσωματωμένοι ανιχνευτές είναι ενεργοί από την εγκατάσταση: ο agent σταμάτησε να αποκρίνεται, η ροή τηλεμετρίας διακόπηκε, αιχμή κόστους, έκρηξη tokens, αύξηση σφαλμάτων, αιχμή σφαλμάτων, κατώφλι προϋπολογισμού, αντιστοίχιση υπογραφής απειλής, εύρημα εργαλείου ασφαλείας, αλλαγή στάσης ασφαλείας. Οι δικοί σου κανόνες είναι προαιρετικοί, επιπλέον.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η αναστολή μιας ριψοκίνδυνης κλήσης είναι opt-in, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, force pushes, sudo, μυστικά (secrets), εγκαταστάσεις πακέτων και εξερχόμενες κλήσεις παίρνουν η καθεμία έναν κανόνα που μπορείς να ενεργοποιήσεις. Μέχρι να το κάνεις, το ClawMetry παρακολουθεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί κάποιος, οι αντίστοιχες κλήσεις περιμένουν εδώ (ή στο κινητό σου) για έγκριση ή απόρριψη.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Περισσότερα, ανά runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Ιστορικό αστεριών (Star History)

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Άδεια χρήσης

MIT · Δημιουργήθηκε από τον [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
