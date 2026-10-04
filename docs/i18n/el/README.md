<!-- i18n-src:c99ac0512cae -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ένας agent μπορεί να κάνει εκατό κλήσεις εργαλείων χωρίς να σημειώσει καμία πρόοδο.** Το ClawMetry
διαβάζει τα αρχεία session που ήδη γράφουν οι coding agents σου, και βάζει το timeline,
τις κλήσεις εργαλείων και όσα δεδομένα token και κόστους εκθέτει το runtime σε μία
προβολή — ώστε να μπορείς να ξεχωρίσεις ένα μακρό run που δουλεύει από ένα που έχει κολλήσει.

Λειτουργεί με **33 AI agent runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 29 ακόμα. Ένα dashboard για όλον τον στόλο agents σου. ([η πλήρης λίστα](SUPPORTED_RUNTIMES.txt), που παράγεται από τον κατάλογο.)

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική ρύθμιση. Εντοπίζει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900**. Μηδενική ρύθμιση: βρίσκει τα agent runtimes
που έχεις ήδη, τα διαβάζει μόνο για ανάγνωση (read-only), και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Πριν εγκαταστήσεις

| | |
|---|---|
| **Τι κάνει** | Διαβάζει τα αρχεία session και τα logs που ήδη γράφουν οι agents σου. Χωρίς SDK, χωρίς αλλαγή κώδικα, χωρίς instrumentation στην εφαρμογή σου. |
| **Τι βλέπεις** | Timeline session, αναπαραγωγή κλήσεων εργαλείο προς εργαλείο, ανάλυση token και κόστους, και σήματα trajectory (βρόχοι, επαναλαμβανόμενες αποτυχίες) — ανά runtime. |
| **Τι είναι δωρεάν** | Το `pip install clawmetry` διαβάζει τα **OpenClaw, NVIDIA NemoClaw, Goose και Qwen Code** χωρίς λογαριασμό, χωρίς κλειδί και χωρίς κλήση δικτύου. Τα άλλα 28 — Claude Code, Codex, Cursor και τα υπόλοιπα — διαβάζονται από το closed-source συνοδευτικό `clawmetry-pro`, που έρχεται με τη δοκιμή 7 ημερών ή με ένα πλάνο — δες το [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) για τον ακριβή διαχωρισμό. |
| **Πώς ξεκινάς** | `pip install clawmetry && clawmetry`, και μετά άνοιξε το localhost:8900. Δεν έχεις ακόμα agents σε αυτό το μηχάνημα; Το `clawmetry --sample` ανοίγει με τρία επισημασμένα συνθετικά sessions. |
| **Τι φεύγει από το μηχάνημά σου** | Κανένα δεδομένο session, εκτός αν τρέξεις το `clawmetry connect`. Δύο πράγματα τρέχουν από προεπιλογή, και τα δύο με δυνατότητα απενεργοποίησης και χωρίς να μεταφέρουν περιεχόμενο session: ένα ανώνυμο ping εγκατάστασης και ένας έλεγχος έκδοσης στο PyPI. Κάθε προορισμός καταγράφεται στο [docs/EGRESS.md](docs/EGRESS.md), χτισμένο από καταγραφή δικτυακής κίνησης και όχι από ανάγνωση σχολίων. |

Δύο περιορισμοί αξίζει να γνωρίζεις πριν κρίνεις το αποτέλεσμα: τα runtimes εκθέτουν πολύ
διαφορετικά δεδομένα (μερικά δεν δημοσιεύουν κόστος καθόλου — [ο πίνακας](docs/compatibility.md)
λέει ποια, ανά runtime), και η παρατήρηση μιας ενέργειας δεν είναι το ίδιο με την ικανότητα
να τη μπλοκάρεις ([ποιοι έλεγχοι είναι πραγματικοί, ανά runtime](docs/APPROVALS.md)).


## Λειτουργεί με 33 agent runtimes

**Δωρεάν στην εφαρμογή ανοιχτού κώδικα:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime παίρνει το ίδιο dashboard. Τρέξε πολλά ταυτόχρονα και ο επιλογέας στην
κεφαλίδα επανακαθορίζει κάθε tab σε ένα από αυτά.

Έχτισες τον δικό σου agent πάνω σε ένα SDK; Ο interceptor παρακολουθεί και τις
κλήσεις LLM του. Δες το [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι αποκτάς

- **Sessions & transcripts**: τι έκανε κάθε agent, γύρο προς γύρο, με αναπαραγωγή
- **Κόστος & tokens**: ανά runtime, μοντέλο, session και ημέρα, με σημάνσεις ανωμαλιών
- **Flow**: ζωντανό διάγραμμα μηνυμάτων που κινούνται μέσα από channels, μοντέλα και εργαλεία
- **Brain**: η ροή συμβάντων σκέψης και κλήσεων εργαλείων τη στιγμή που συμβαίνει
- **Context blowout**: χρήση παραθύρου με μέγεθος ανά provider, compaction έναντι εξαναγκασμένου overflow, συν έναν χάρτη ανά runtime για ό,τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: τα αρχεία και τα skills που πραγματικά φόρτωσε κάθε runtime
- **Health & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, rate limits, ζωντανή ροή logs
- **Alerts**: όρια προϋπολογισμού, αιχμές σφαλμάτων, agent-offline, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: παύση ριψοκίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Context blowout, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα αξίζει να απαντηθούν πριν εμπιστευτείς οποιοδήποτε εργαλείο σύγκρισης agents.

**Πώς χειρίζεται το context-window blowout μεταξύ runtimes;**

Ένα ποσοστό χρήσης είναι τόσο ειλικρινές όσο ο αριθμητής με τον οποίο διαιρεί. Το ClawMetry
καθορίζει το μέγεθος του παραθύρου ανά provider από [έναν πίνακα που μπορείς να διαβάσεις και να
προτείνεις PR](clawmetry/context_windows.py), που καλύπτει Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετρά όλα τα 33
runtimes με τον κανόνα ενός προμηθευτή. Αυτό έχει σημασία: ένας γύρος 300K GPT-5 που
βαθμολογείται με τον κανόνα των 200K της Anthropic διαβάζεται ως ">100%, blown" όταν στην
πραγματικότητα είναι στο 75% των 400K του GPT-5. Ο ίδιος κανόνας κρύβει έναν γνησίως
υπερχειλισμένο γύρο 130K DeepSeek ως ένα άνετο 65%.

Κάθε παράθυρο έρχεται με την προέλευσή του: `model_table`, `explicit_marker`,
`observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένα
gauge χτισμένο πάνω σε μια υπόθεση δεν αποδίδεται ποτέ με την ίδια αυθεντία με ένα
χτισμένο πάνω σε μια αναζήτηση.

Το ClawMetry μπορεί να δει συμβάντα compaction μόνο σε ορισμένα runtimes. Έτσι το
`GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα μηδέν σημαίνει **"έτρεξε
καθαρά" ή "είμαστε τυφλοί"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλός, το λέει.
[Πλήρης λεπτομέρεια](docs/CONTEXT_BLOWOUT.md)

**Τι κοστίζει το instrumentation;**

| Διαδρομή | Προστέθηκε στον agent σου | Προεπιλογή; |
|---|---|---|
| Session-file tailing (όλα τα 33 runtimes) | **0**. Ξεχωριστή διαδικασία, καθόλου κώδικας ClawMetry στον agent σου | ναι |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ανά κλήση LLM, ή 0.009% μιας κλήσης 5s | όχι |
| Pre-tool hook gate (warm cache) | **+44 ms** ανά gated κλήση εργαλείου, πάνω από ένα όριο διερμηνέα 36 ms | όχι |
| Enforcement proxy | **+9.7 ms** ανά κλήση LLM | όχι |

Κόστος host daemon: **2.762 συμβάντα/δευτ** πρόσληψη, **710 bytes/συμβάν** στο
δίσκο (67,7 MB ανά 100k συμβάντα), και **~12% ενός πυρήνα** σταθερά σε μια
απασχολημένη εγκατάσταση. Αυτός ο τελευταίος αριθμός είναι πάνω από τον δικό μας
δηλωμένο στόχο 5-10%, οπότε δημοσιεύεται ως σφάλμα προς διόρθωση και όχι ως κάτι
που αφαιρείται από τη σελίδα.

Μετρήθηκε σε Apple M2 Pro με το `benchmarks/overhead.py`. Το harness τρέχει κάθε
συνθήκη σε ξεχωριστή διαδικασία, εναλλάσσει τη σειρά τους, και **αρνείται να
εκτυπώσει έναν αριθμό όταν οι γύροι διαφωνούν στο πρόσημό του**. Τρέξε το στο δικό
σου μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των hook gates και του enforcement
proxy, και το harness τρέχει σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα
αξίζει να γνωρίζεις: ο proxy κοστίζει περίπου επτά φορές περισσότερο στα Windows
απ' ό,τι στο Linux, και ο daemon αυτήν τη στιγμή διατηρεί περίπου το 12% ενός
πυρήνα, πάνω από τον δικό μας στόχο 5-10%. Το ανεπεξέργαστο JSON, η μέθοδος, και
τι δεν έχει μετρηθεί ακόμα βρίσκονται στο [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, cloud sync | $9 ανά node / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: approvals, πολιτικές κινδύνου εργαλείων, evals, εντοπισμός ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, αρχείο καταγραφής ελέγχου ανθεκτικό σε παραποίηση | $19 ανά node / μήνα |

Τα ετήσια πλάνα, το Enterprise και οι τρέχοντες αριθμοί βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα αυτοφιλοξενούμενα κλειδιά
άδειας λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός
δωρεάν/πληρωμένου βρίσκεται στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία session και logs. **Κανένα δεδομένο session δεν
φεύγει από το μηχάνημά σου εκτός αν τρέξεις το `clawmetry connect`** — καθόλου prompts,
απαντήσεις, παραμέτρους εργαλείων, περιεχόμενα αρχείων ή γραμμές log. Όταν συνδεθείς,
το στιγμιότυπο είναι κρυπτογραφημένο από άκρο σε άκρο με ένα κλειδί που δεν φεύγει ποτέ
από το μηχάνημά σου, και αποκρυπτογραφείται στο πρόγραμμα περιήγησής σου. Αν ένας κόμβος
δεν έχει κλειδί, η μεταφόρτωση παραλείπεται αντί να σταλεί ανοιχτά, και καμία απάντηση
διακομιστή δεν μπορεί να το απενεργοποιήσει αυτό.

Δύο πράγματα τρέχουν από προεπιλογή πριν συνδεθείς, και τα δύο με δυνατότητα
απενεργοποίησης και χωρίς να μεταφέρουν δεδομένα session: ένα ανώνυμο ping εγκατάστασης
και ένας έλεγχος έκδοσης έναντι του PyPI. Μια προεπιλεγμένη εγκατάσταση επίσης αναζητά
τη δημόσια IP σου μία φορά για μια γραμμή banner εκκίνησης. Κάθε προορισμός, τι
μεταφέρει και πώς να τον απενεργοποιήσεις αναφέρεται στο [docs/EGRESS.md](docs/EGRESS.md);
αυτοφιλοξενούμενες, ανακατευθυνόμενες και απομονωμένες (air-gapped) εγκαταστάσεις δεν
κάνουν καθόλου προαιρετικές εξωτερικές κλήσεις.

Η αποκρυπτογράφηση συμβαίνει στο πρόγραμμα περιήγησής σου, με κώδικα που σου σερβίρουμε.
Αυτό κάποτε ήταν μια υπόσχεση· τώρα είναι κάτι που μπορείς να ελέγξεις. Κάθε γραμμή που
αγγίζει το κλειδί σου βρίσκεται σε ένα αναγνώσιμο αρχείο, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
που αποστέλλεται μέσα στο wheel και σερβίρεται αυτολεξεί, καρφωμένο με ένα hash
Subresource Integrity. Για να επιβεβαιώσεις ότι το πρόγραμμα περιήγησης τρέχει αυτό
που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Τι δεν αποδεικνύει αυτό: εμείς σερβίρουμε τη σελίδα που φορτώνει το αρχείο, οπότε
θα μπορούσαμε να σερβίρουμε διαφορετική σελίδα. Τα hashes integrity σε προστατεύουν
από ένα παραβιασμένο CDN, όχι από τον προμηθευτή. Αυτό που κερδίζεις είναι ότι κάθε
αντικατάσταση πρέπει να είναι σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική
από ένα artifact στο PyPI που μπορεί να ανακτήσει ο καθένας. Η αυτοφιλοξενία ή η
παραμονή μόνο τοπικά αφαιρεί εντελώς την εξάρτηση.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή το one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Χρειάζεται Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα agent runtime
στο ίδιο μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ή άφησε τον agent να το ρυθμίσει για σένα. Το skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
διδάσκει στο Claude Code, Codex, Cursor, Gemini CLI, Copilot ή OpenCode να
εγκαθιστά το ClawMetry, να αναφέρει τι κάνουν και τι ξοδεύουν οι agents στο μηχάνημα,
να σταματά ένα session κατόπιν αιτήματος, και να κρατά ριψοκίνδυνες κλήσεις εργαλείων
για έγκριση:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσεις ένα runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά provider, compaction έναντι overflow, κάλυψη ανά runtime |
| [Overhead](docs/OVERHEAD.md) | Τι κοστίζει το instrumentation, μετρημένο, με το harness για αναπαραγωγή |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας επιπέδων, license CLI |
| [Approvals & πολιτικές](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, πρόσληψη OTLP από οπουδήποτε |
| [Φέρε τον δικό σου agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain από άκρο σε άκρο, με εκτελέσιμα παραδείγματα |
| [SDK tracking](docs/SDK_TRACKING.md) | Απόδοση κόστους για agents που έχτισες εσύ ο ίδιος |
| [Chat channels](docs/CHANNELS.md) | Οι chat adapters που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Απομονωμένες (sandboxed) ρυθμίσεις NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, mounts τόμων |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος της desktop εφαρμογής, και πώς να τα απενεργοποιήσεις |

## Screenshots

Κάθε αριθμός παρακάτω είναι από ένα πραγματικό μηχάνημα, μόνο για ανάγνωση, χωρίς τίποτα προκατασκευασμένο.

**Σου λέει πότε κάτι πάει στραβά, όχι μόνο τι συνέβη.**
Δύο banners ανωμαλιών στην κορυφή: δαπάνη που τρέχει 7x τον ημερήσιο μέσο όρο, και μια
αιχμή κόστους 4,2x. Από κάτω τους, 324 από 667 πρόσφατα sessions που φέρουν σήμα
σπατάλης, αναλυτικά ανά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σου δείχνει πού πήγαν τα χρήματα, σε κάθε παράθυρο.**
$252,47 σήμερα, $513,15 αυτή την εβδομάδα, $1.312,92 αυτόν τον μήνα, καθένα με τα
tokens από πίσω του και πόσο από αυτό ήδη καλύπτει η συνδρομή σου. Από κάτω, περίπου
$1.128/μήνα αναλυτικά ως ανακτήσιμα και $17.256/μήνα που έχουν ήδη εξοικονομηθεί από
επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα ροής: εσύ, το κανάλι από το οποίο έφτασε, το gateway, το μοντέλο
που απαντά αυτήν τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν
καθώς η δουλειά κινείται μέσα τους.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε agent στο μηχάνημα, σε έναν πίνακα.**
Τι τρέχει, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη τη διάρκεια ζωής του, πότε
εμφανίστηκε τελευταία φορά, ποιος τον κατέχει, και αν μια συνδρομή καλύπτει τον
λογαριασμό. 14 agents εδώ, 3 sessions σε λειτουργία, 13 σε ησυχία.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Σου δείχνει πού πήγε ο χρόνος και τα χρήματα ενός γύρου, εργαλείο προς εργαλείο.**
Ένας γύρος ενός πραγματικού session: 11 εργαλεία σε 11,2 λεπτά για $1,16. Κάθε κλήση
Bash και κλήση μοντέλου παίρνει τη δική της μπάρα στο timeline, ώστε η εντολή που
έτρεξε για 4,1 λεπτά και εκείνη που έτρεξε για 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί τη δουλειά, όχι μόνο τη δαπάνη.**
Ένα Α αυτή την εβδομάδα: 54 εργασίες επέστρεψαν καθαρές, 2 δύσκολες κόστισαν $48,57,
και τα runs με πολύ λίγη δραστηριότητα για να κριθούν αφαιρούνται από τη βαθμολόγηση
αντί να μετρηθούν ως νίκες. Κάθε δύσκολο run συνδέεται με το δικό του trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Σου δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από ένα παράθυρο 1M-token στον τελευταίο γύρο, μια κορύφωση 83,3%, 4 compactions
που ενεργοποιήθηκαν όλα προληπτικά αντί σε overflow, και η χρήση κάθε γύρου από πίσω του.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Ο εντοπισμός λειτουργεί χωρίς να ρυθμίσεις τίποτα.**
Οι ενσωματωμένοι ανιχνευτές είναι ενεργοί από την εγκατάσταση: ο agent σταμάτησε να
ανταποκρίνεται, η ροή τηλεμετρίας σταμάτησε, αιχμή κόστους, έκρηξη tokens, σφάλματα
που αυξάνονται, αιχμή σφαλμάτων, όριο προϋπολογισμού, υπογραφή απειλής που ταυτίστηκε,
εύρημα εργαλείου ασφάλειας, αλλαγή θέσης ασφάλειας. Οι δικοί σου κανόνες είναι
προαιρετικοί επιπλέον.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η παρακράτηση μιας ριψοκίνδυνης κλήσης είναι προαιρετική, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, force pushes, sudo, μυστικά (secrets), εγκαταστάσεις πακέτων και
εξωτερικές κλήσεις παίρνουν η καθεμία έναν κανόνα που μπορείς να ενεργοποιήσεις. Μέχρι να
το κάνεις, το ClawMetry παρατηρεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί ένας, οι
κλήσεις που ταιριάζουν περιμένουν εδώ (ή στο κινητό σου) για έγκριση ή απόρριψη.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Περισσότερα, ανά runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Αναγνώριση

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Ιστορικό αστεριών

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
