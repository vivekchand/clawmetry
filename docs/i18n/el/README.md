<!-- i18n-src:d21bea5161e0 -->
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

**Δες τον πράκτορά σου να σκέφτεται.** Παρατήρηση σε πραγματικό χρόνο για **30 runtimes AI πρακτόρων**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 26 ακόμη. Ένα dashboard για ολόκληρο το στόλο πρακτόρων σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική ρύθμιση. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900**. Μηδενική ρύθμιση: βρίσκει τα runtimes πρακτόρων
που ήδη έχεις, τα διαβάζει μόνο για ανάγνωση και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Λειτουργεί με 30 runtimes πρακτόρων

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Σε επί πληρωμή πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime παίρνει το ίδιο dashboard. Τρέξε πολλά ταυτόχρονα και ο επιλογέας
στην κεφαλίδα επαναπροσαρμόζει κάθε καρτέλα σε ένα από αυτά.

Έφτιαξες τον δικό σου πράκτορα πάνω σε ένα SDK αντί για αυτά; Ο interceptor
παρακολουθεί και τις δικές του κλήσεις LLM. Δες [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι παίρνεις

- **Συνεδρίες & απομαγνητοφωνήσεις**: τι έκανε κάθε πράκτορας, γύρο προς γύρο, με replay
- **Κόστος & tokens**: ανά runtime, μοντέλο, συνεδρία και ημέρα, με σημαίες ανωμαλιών
- **Ροή**: ζωντανό διάγραμμα μηνυμάτων που κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων σκέψης και κλήσεων εργαλείων καθώς συμβαίνει
- **Context blowout**: χρησιμοποίηση παραθύρου προσαρμοσμένη ανά πάροχο, συμπίεση έναντι εξαναγκασμένης υπερχείλισης, συν έναν ανά-runtime χάρτη του τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Μνήμη & δεξιότητες**: τα αρχεία και οι δεξιότητες που πράγματι φόρτωσε κάθε runtime
- **Υγεία & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, όρια ρυθμού, ζωντανή ροή logs
- **Ειδοποιήσεις**: όρια προϋπολογισμού, αιχμές σφαλμάτων, πράκτορας εκτός σύνδεσης, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Εγκρίσεις**: παύση ριψοκίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Context blowout, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα που αξίζει να απαντηθούν πριν εμπιστευτείς οποιοδήποτε εργαλείο σύγκρισης πρακτόρων.

**Πώς χειρίζεται την υπερχείλιση του παραθύρου context σε διαφορετικά runtimes;**

Ένα ποσοστό χρησιμοποίησης είναι τόσο ειλικρινές όσο και αυτό με το οποίο διαιρεί. Το ClawMetry
προσδιορίζει το μέγεθος του παραθύρου ανά πάροχο από [έναν πίνακα που μπορείς να διαβάσεις και να
κάνεις PR](clawmetry/context_windows.py), που καλύπτει Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετράει και τα 26 runtimes με τον
χάρακα ενός προμηθευτή. Αυτό έχει σημασία: ένας γύρος 300K GPT-5 βαθμολογημένος
έναντι των 200K της Anthropic διαβάζεται ως ">100%, blown" ενώ στην πραγματικότητα βρίσκεται στο 75% των
400K του GPT-5. Ο ίδιος χάρακας κρύβει έναν πραγματικά υπερχειλισμένο γύρο 130K DeepSeek
ως ένα άνετο 65%.

Κάθε παράθυρο συνοδεύεται από την προέλευσή του: `model_table`, `explicit_marker`,
`observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένα
μετρητή χτισμένο πάνω σε μια εικασία δεν αποδίδεται ποτέ με την ίδια αυθεντία όπως ένα
χτισμένο πάνω σε μια αναζήτηση.

Το ClawMetry μπορεί να δει γεγονότα συμπίεσης μόνο σε ορισμένα runtimes. Έτσι το
`GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα μηδέν σημαίνει **"έτρεξε
καθαρά" ή "είμαστε τυφλοί"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλός το λέει.
[Πλήρης λεπτομέρεια](docs/CONTEXT_BLOWOUT.md)

**Τι κοστίζει η οργανολογία;**

| Διαδρομή | Προστίθεται στον πράκτορά σου | Προεπιλογή; |
|---|---|---|
| Παρακολούθηση αρχείου συνεδρίας (και τα 30 runtimes) | **0**. Ξεχωριστή διεργασία, χωρίς κώδικα ClawMetry στον πράκτορά σου | ενεργό |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ανά κλήση LLM, ή 0.009% μιας κλήσης 5s | ανενεργό |
| Πύλη pre-tool hook (ζεστή cache) | **+44 ms** ανά κλήση εργαλείου με πύλη, πάνω από ένα πάτωμα διερμηνέα 36 ms | ανενεργό |
| Proxy επιβολής | **+9.7 ms** ανά κλήση LLM | ανενεργό |

Κόστος daemon host: **2.762 γεγονότα/δευτ.** εισαγωγή, **710 bytes/γεγονός** στο δίσκο
(67.7 MB ανά 100k γεγονότα), και **~12% ενός πυρήνα** διαρκώς σε μια απασχολημένη
εγκατάσταση. Αυτός ο τελευταίος αριθμός είναι πάνω από τον δικό μας δηλωμένο προϋπολογισμό 5-10%, οπότε
δημοσιεύεται ως σφάλμα προς επιδίωξη διόρθωσης παρά κρύβεται από τη σελίδα.

Μετρήθηκε σε Apple M2 Pro με το `benchmarks/overhead.py`. Το harness τρέχει
κάθε συνθήκη σε ξεχωριστή διεργασία, εναλλάσσει τη σειρά τους, και **αρνείται
να τυπώσει έναν αριθμό όταν οι γύροι διαφωνούν ως προς το πρόσημό του**. Τρέξε το στο δικό σου
μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των πυλών hook και του proxy επιβολής,
και το harness τρέχει σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα που αξίζει να
γνωρίζεις: ο proxy κοστίζει περίπου επτά φορές περισσότερο σε Windows απ' ό,τι σε Linux, και
το daemon αυτή τη στιγμή διατηρεί περίπου 12% ενός πυρήνα, πάνω από τον δικό μας προϋπολογισμό 5-10%.
Το ακατέργαστο JSON, η μέθοδος, και τι παραμένει αμέτρητο βρίσκονται στο
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, συγχρονισμός cloud | $9 ανά κόμβο / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: εγκρίσεις, πολιτικές κινδύνου εργαλείων, αξιολογήσεις, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, ημερολόγιο ελέγχου ανθεκτικό σε παραποίηση | $19 ανά κόμβο / μήνα |

Ετήσια πλάνα, Enterprise και οι τρέχουσες τιμές βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα κλειδιά αδειοδότησης αυτο-φιλοξενίας
λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός δωρεάν/επί πληρωμή είναι
στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία συνεδριών και logs. **Κανένα δεδομένο συνεδρίας δεν φεύγει από το
μηχάνημά σου εκτός αν τρέξεις `clawmetry connect`** — καθόλου prompts, απαντήσεις, ορίσματα εργαλείων, περιεχόμενα
αρχείων ή γραμμές logs. Όταν συνδέεσαι, το στιγμιότυπο είναι κρυπτογραφημένο άκρη-σε-άκρη
με ένα κλειδί που δεν φεύγει ποτέ από το μηχάνημά σου, και αποκρυπτογραφείται στον περιηγητή σου. Αν ένας
κόμβος δεν έχει κλειδί, η μεταφόρτωση παραλείπεται αντί να σταλεί απροστάτευτη, και καμία
απάντηση διακομιστή δεν μπορεί να το απενεργοποιήσει.

Δύο πράγματα τρέχουν εξ ορισμού πριν συνδεθείς, αμφότερα με δυνατότητα εξαίρεσης και κανένα
δεν μεταφέρει δεδομένα συνεδρίας: ένα ανώνυμο ping εγκατάστασης και έναν έλεγχο έκδοσης έναντι
του PyPI. Μια προεπιλεγμένη εγκατάσταση επίσης αναζητά τη δημόσια IP σου μία φορά για μια γραμμή banner
εκκίνησης. Κάθε προορισμός, τι μεταφέρει και πώς να τον απενεργοποιήσεις είναι καταγεγραμμένος στο
[docs/EGRESS.md](docs/EGRESS.md)· εγκαταστάσεις αυτο-φιλοξενίας, ανακατεύθυνσης και απομόνωσης δικτύου δεν κάνουν
καθόλου προαιρετικές εξερχόμενες κλήσεις.

Η αποκρυπτογράφηση συμβαίνει στον περιηγητή σου, σε κώδικα που σου παρέχουμε. Αυτό ήταν κάποτε
μια υπόσχεση· τώρα είναι κάτι που μπορείς να ελέγξεις. Κάθε γραμμή που αγγίζει το κλειδί σου
βρίσκεται σε ένα αναγνώσιμο αρχείο, το [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
που αποστέλλεται μέσα στο wheel και παρέχεται αυτούσιο, καρφιτσωμένο με ένα hash Subresource
Integrity. Για να επιβεβαιώσεις ότι ο περιηγητής τρέχει αυτό που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Αυτό που δεν αποδεικνύει: εμείς παρέχουμε τη σελίδα που φορτώνει το αρχείο, οπότε θα μπορούσαμε να
παρέχουμε διαφορετική σελίδα. Τα hashes ακεραιότητας σε προστατεύουν από ένα παραβιασμένο CDN,
όχι από τον προμηθευτή. Αυτό που κερδίζεις είναι ότι κάθε αντικατάσταση πρέπει να είναι
σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική από ένα artifact στο PyPI
που ο καθένας μπορεί να ανακτήσει. Η αυτο-φιλοξενία ή η παραμονή μόνο τοπικά αφαιρεί
εντελώς αυτή την εξάρτηση.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή η εντολή μιας γραμμής: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Χρειάζεται Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα runtime πράκτορα στο
ίδιο μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε προσαρμογέας, και πώς να προσθέσεις ένα runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά πάροχο, συμπίεση έναντι υπερχείλισης, κάλυψη ανά runtime |
| [Overhead](docs/OVERHEAD.md) | Τι κοστίζει η οργανολογία, μετρημένο, με το harness για να το αναπαράγεις |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι επί πληρωμή, πίνακας βαθμίδων, license CLI |
| [Εγκρίσεις & πολιτικές](docs/APPROVALS.md) | Πύλη πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από το κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οπουδήποτε |
| [SDK tracking](docs/SDK_TRACKING.md) | Απόδοση κόστους για πράκτορες που έχτισες μόνος σου |
| [Κανάλια συνομιλίας](docs/CHANNELS.md) | Οι προσαρμογείς συνομιλίας που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Απομονωμένες ρυθμίσεις NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Εικόνα, compose, προσαρτήσεις τόμων |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος επιφάνειας εργασίας, και πώς να τα απενεργοποιήσεις |

## Στιγμιότυπα οθόνης

Κάθε αριθμός παρακάτω προέρχεται από ένα πραγματικό μηχάνημα, μόνο για ανάγνωση, χωρίς τίποτα προκατασκευασμένο.

**Σου λέει πότε κάτι πάει στραβά, όχι μόνο τι συνέβη.**
Δύο banner ανωμαλιών στην κορυφή: δαπάνη που τρέχει 7 φορές πάνω από τον ημερήσιο μέσο όρο, και μια
αιχμή κόστους 4.2x. Από κάτω τους, 324 από τις 667 πρόσφατες συνεδρίες που φέρουν ένα σήμα
σπατάλης, κατηγοριοποιημένο ανά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σου δείχνει πού πήγαν τα χρήματα, σε κάθε παράθυρο.**
$252.47 σήμερα, $513.15 αυτή την εβδομάδα, $1.312.92 αυτόν τον μήνα, καθένα με τα tokens
από πίσω του και πόσο από αυτό ήδη καλύπτει η συνδρομή σου. Από κάτω, περίπου $1.128/μήνα
κατηγοριοποιημένα ως ανακτήσιμα και $17.256/μήνα ήδη εξοικονομημένα από επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα ροής: εσύ, το κανάλι από το οποίο έφτασε, η πύλη, το μοντέλο που
απαντά αυτή τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν καθώς η εργασία
κινείται μέσα από αυτούς.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε πράκτορας στο μηχάνημα, σε έναν πίνακα.**
Τι τρέχει, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη τη διάρκεια ζωής του, πότε
εμφανίστηκε τελευταία φορά, ποιος τον κατέχει, και αν μια συνδρομή καλύπτει τον
λογαριασμό. 14 πράκτορες εδώ, 3 συνεδρίες σε λειτουργία, 13 σε ηρεμία.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Σου δείχνει πού πήγε ο χρόνος και τα χρήματα ενός γύρου, εργαλείο προς εργαλείο.**
Ένας γύρος μιας πραγματικής συνεδρίας: 11 εργαλεία σε 11.2 λεπτά για $1.16. Κάθε κλήση
Bash και κλήση μοντέλου παίρνει τη δική της μπάρα στο χρονοδιάγραμμα, ώστε η εντολή που έτρεξε
για 4.1 λεπτά και αυτή που έτρεξε για 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί το έργο, όχι μόνο τη δαπάνη.**
Ένα Α αυτή την εβδομάδα: 54 εργασίες ολοκληρώθηκαν καθαρά, 2 δύσκολες κόστισαν $48.57, και
οι εκτελέσεις με πολύ λίγη δραστηριότητα ώστε να κριθούν εξαιρούνται από τη βαθμολογία αντί να
μετρηθούν ως επιτυχίες. Κάθε δύσκολη εκτέλεση συνδέεται με το ίχνος της.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Σου δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από ένα παράθυρο 1M tokens στον τελευταίο γύρο, μια αιχμή 83.3%, 4 συμπιέσεις
που όλες πυροδοτήθηκαν προληπτικά αντί σε υπερχείλιση, συν τη χρησιμοποίηση κάθε γύρου
από πίσω τους.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Η ανίχνευση τρέχει χωρίς να ρυθμίσεις τίποτα.**
Οι ενσωματωμένοι ανιχνευτές είναι ενεργοί από την εγκατάσταση: ο πράκτορας σιώπησε, η ροή
τηλεμετρίας σταμάτησε, αιχμή κόστους, έκρηξη tokens, αυξανόμενα σφάλματα, αιχμή σφαλμάτων,
όριο προϋπολογισμού, ταιριασμένη υπογραφή απειλής, εύρημα εργαλείου ασφαλείας, αλλαγή στάσης
ασφαλείας. Οι δικοί σου κανόνες είναι προαιρετικοί από πάνω.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η αναστολή μιας ριψοκίνδυνης κλήσης είναι προαιρετική, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, εξαναγκασμένα push, sudo, μυστικά, εγκαταστάσεις πακέτων και εξερχόμενες
κλήσεις παίρνουν το καθένα έναν κανόνα που μπορείς να ενεργοποιήσεις. Μέχρι να το κάνεις, το ClawMetry
παρακολουθεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί ένας, οι κλήσεις που ταιριάζουν περιμένουν εδώ
(ή στο κινητό σου) για έγκριση ή απόρριψη.

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

MIT · Φτιαγμένο από τον [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
