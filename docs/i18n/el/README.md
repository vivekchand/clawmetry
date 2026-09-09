<!-- i18n-src:61beb8393e2f -->
> Ελληνικά translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ένας πράκτορας μπορεί να κάνει εκατό κλήσεις εργαλείων χωρίς να σημειώνει πρόοδο.** Το ClawMetry
διαβάζει τα αρχεία συνεδρίας που οι πράκτορες κωδικοποίησής σας ήδη γράφουν, και τοποθετεί το χρονοδιάγραμμα,
τις κλήσεις εργαλείων και όποια δεδομένα token και κόστους εκθέτει το runtime σε μία ενιαία
προβολή — ώστε να μπορείτε να ξεχωρίσετε μια μακρά εκτέλεση που λειτουργεί από μία που έχει κολλήσει.

Λειτουργεί με **30 runtimes πρακτόρων AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 26 ακόμη. Ένα dashboard για ολόκληρο το στόλο πρακτόρων σας. ([η πλήρης λίστα](SUPPORTED_RUNTIMES.txt), παραγόμενη από τον κατάλογο.)

> 🌐 **Διαβάστε το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενικές ρυθμίσεις. Ανιχνεύει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στη διεύθυνση **http://localhost:8900**. Μηδενικές ρυθμίσεις: βρίσκει τα runtimes πρακτόρων
που ήδη έχετε, τα διαβάζει σε λειτουργία μόνο-ανάγνωσης, και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Πριν εγκαταστήσετε

| | |
|---|---|
| **Τι κάνει** | Διαβάζει τα αρχεία συνεδρίας και τα logs που οι πράκτορές σας ήδη γράφουν. Χωρίς SDK, χωρίς αλλαγή κώδικα, χωρίς instrumentation στην εφαρμογή σας. |
| **Τι βλέπετε** | Χρονοδιάγραμμα συνεδρίας, αναπαραγωγή ανά εργαλείο, ανάλυση tokens και κόστους, και σήματα πορείας (loops, επαναλαμβανόμενες αποτυχίες) — ανά runtime. |
| **Τι είναι δωρεάν** | Η εντολή `pip install clawmetry` διαβάζει τα **OpenClaw, NVIDIA NemoClaw και Goose** χωρίς λογαριασμό, χωρίς κλειδί και χωρίς καμία κλήση δικτύου. Τα υπόλοιπα 27 — Claude Code, Codex, Cursor και τα λοιπά — διαβάζονται από το κλειστού κώδικα συνοδευτικό `clawmetry-pro`, το οποίο διατίθεται με τη 7ήμερη δοκιμαστική περίοδο ή με ένα πλάνο — δείτε το [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) για την ακριβή κατανομή. |
| **Πώς να ξεκινήσετε** | `pip install clawmetry && clawmetry`, και μετά ανοίξτε το localhost:8900. Δεν υπάρχουν ακόμη πράκτορες σε αυτό το μηχάνημα; Το `clawmetry --sample` ανοίγει με τρεις χαρακτηρισμένες συνθετικές συνεδρίες. |
| **Τι φεύγει από το μηχάνημά σας** | Κανένα δεδομένο συνεδρίας, εκτός αν εκτελέσετε την εντολή `clawmetry connect`. Δύο πράγματα εκτελούνται από προεπιλογή, και τα δύο με δυνατότητα απενεργοποίησης και κανένα δεν μεταφέρει περιεχόμενο συνεδρίας: ένα ανώνυμο ping εγκατάστασης και έναν έλεγχο έκδοσης στο PyPI. Κάθε προορισμός καταγράφεται στο [docs/EGRESS.md](docs/EGRESS.md), ανακατασκευασμένο από καταγραφή δικτύου και όχι από ανάγνωση σχολίων κώδικα. |

Δύο περιορισμοί αξίζει να γνωρίζετε πριν κρίνετε το αποτέλεσμα: τα runtimes εκθέτουν πολύ
διαφορετικά δεδομένα (κάποια δεν δημοσιεύουν καθόλου κόστος — [ο πίνακας](docs/compatibility.md)
δείχνει ποια, ανά runtime), και το να παρατηρείς μια ενέργεια δεν είναι το ίδιο με το να μπορείς
να την μπλοκάρεις ([ποιοι έλεγχοι είναι πραγματικοί, ανά runtime](docs/APPROVALS.md)).


## Λειτουργεί με 30 runtimes πρακτόρων

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Κάθε runtime λαμβάνει το ίδιο dashboard. Εκτελέστε πολλά ταυτόχρονα και ο εναλλάκτης στην κεφαλίδα
επαναπροσδιορίζει κάθε καρτέλα σε ένα από αυτά.

Φτιάξατε τον δικό σας πράκτορα πάνω σε ένα SDK αντί για κάτι από τα παραπάνω; Ο interceptor
παρακολουθεί και τις κλήσεις LLM του. Δείτε το [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι αποκτάτε

- **Συνεδρίες & απομαγνητοφωνήσεις**: τι έκανε κάθε πράκτορας, γύρο προς γύρο, με αναπαραγωγή
- **Κόστος & tokens**: ανά runtime, μοντέλο, συνεδρία και ημέρα, με σημαίες ανωμαλιών
- **Ροή**: ζωντανό διάγραμμα μηνυμάτων που κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων σκέψης και κλήσεων εργαλείων καθώς συμβαίνει
- **Υπερχείλιση context**: αξιοποίηση παραθύρου διαστασιολογημένη ανά πάροχο, συμπίεση έναντι εξαναγκασμένης υπερχείλισης, συν έναν χάρτη ανά runtime για το τι *δεν* μπορούμε να δούμε ([πώς](docs/CONTEXT_BLOWOUT.md))
- **Μνήμη & δεξιότητες**: τα αρχεία και οι δεξιότητες που πράγματι φόρτωσε κάθε runtime
- **Υγεία & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, όρια ρυθμού, ζωντανή ροή logs
- **Ειδοποιήσεις**: όρια προϋπολογισμού, αιχμές σφαλμάτων, πράκτορας εκτός σύνδεσης, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Εγκρίσεις**: παύση επικίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σας ([πώς](docs/APPROVALS.md))

## Υπερχείλιση context, και τι κοστίζει η παρακολούθηση

Δύο ερωτήματα αξίζει να απαντηθούν πριν εμπιστευτείτε οποιοδήποτε εργαλείο σύγκρισης πρακτόρων.

**Πώς χειρίζεται την υπερχείλιση του παραθύρου context σε διαφορετικά runtimes;**

Ένα ποσοστό αξιοποίησης είναι τόσο ειλικρινές όσο και ο αριθμός με τον οποίο διαιρεί. Το ClawMetry
διαστασιολογεί το παράθυρο ανά πάροχο από [έναν πίνακα που μπορείτε να διαβάσετε και να
προτείνετε PR](clawmetry/context_windows.py), καλύπτοντας Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama και GLM. Δεν μετρά και τα 30 runtimes με τον χάρακα ενός
προμηθευτή. Αυτό έχει σημασία: ένας γύρος 300K GPT-5 βαθμολογούμενος έναντι των 200K της Anthropic
διαβάζεται ως ">100%, υπερχειλισμένος" ενώ στην πραγματικότητα βρίσκεται στο 75% των 400K του
GPT-5. Ο ίδιος χάρακας κρύβει έναν πραγματικά υπερχειλισμένο γύρο 130K DeepSeek ως ένα άνετο 65%.

Κάθε παράθυρο συνοδεύεται από την προέλευσή του: `model_table`, `explicit_marker`,
`observed_floor`, ή ένα ειλικρινές `default` όταν δεν γνωρίζουμε το μοντέλο. Ένας μετρητής
χτισμένος πάνω σε μια εικασία δεν εμφανίζεται ποτέ με την ίδια αυθεντία με έναν χτισμένο πάνω σε
πραγματική αναζήτηση.

Το ClawMetry μπορεί να δει γεγονότα συμπίεσης μόνο σε ορισμένα runtimes. Έτσι το
`GET /api/context-coverage` αναφέρει, ανά runtime, αν ένα μηδέν **σημαίνει "έτρεξε καθαρά" ή
"είμαστε τυφλοί"**. Ένα `0` που στην πραγματικότητα σημαίνει τυφλό, το λέει.
[Πλήρεις λεπτομέρειες](docs/CONTEXT_BLOWOUT.md)

**Τι κοστίζει το instrumentation;**

| Διαδρομή | Προστίθεται στον πράκτορά σας | Προεπιλογή; |
|---|---|---|
| Παρακολούθηση αρχείων συνεδρίας (και τα 30 runtimes) | **0**. Ξεχωριστή διεργασία, χωρίς κώδικα ClawMetry στον πράκτορά σας | ενεργό |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** ανά κλήση LLM, ή 0,009% μιας κλήσης 5s | ανενεργό |
| Πύλη hook προ-εργαλείου (θερμή cache) | **+44 ms** ανά ελεγχόμενη κλήση εργαλείου, πάνω από έναν πυθμένα 36 ms του διερμηνέα | ανενεργό |
| Proxy επιβολής | **+9,7 ms** ανά κλήση LLM | ανενεργό |

Κόστος φιλοξενίας daemon: **2.762 γεγονότα/δευτ.** εισαγωγή, **710 bytes/γεγονός** στον δίσκο
(67,7 MB ανά 100k γεγονότα), και **~12% ενός πυρήνα** σταθερά σε μια πολυάσχολη εγκατάσταση. Αυτός
ο τελευταίος αριθμός υπερβαίνει τον δικό μας δηλωμένο προϋπολογισμό 5-10%, οπότε δημοσιεύεται ως
bug προς αντιμετώπιση αντί να παραλειφθεί από τη σελίδα.

Μετρήθηκε σε Apple M2 Pro με το `benchmarks/overhead.py`. Το εργαλείο εκτελεί κάθε συνθήκη σε
ξεχωριστή διεργασία, εναλλάσσει τη σειρά τους, και **αρνείται να εκτυπώσει έναν αριθμό όταν οι
γύροι διαφωνούν ως προς το πρόσημό του**. Εκτελέστε το στο δικό σας μηχάνημα σε ένα λεπτό:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Κάθε διαδρομή μετριέται, συμπεριλαμβανομένων των πυλών hook και του proxy επιβολής, και το
εργαλείο εκτελείται σε Linux, macOS και Windows στο CI. Δύο αποτελέσματα αξίζει να γνωρίζετε: ο
proxy κοστίζει περίπου επτά φορές περισσότερο σε Windows απ' ό,τι σε Linux, και ο daemon
σταθεροποιείται προς το παρόν γύρω στο 12% ενός πυρήνα, πάνω από τον δικό μας προϋπολογισμό 5-10%.
Το ακατέργαστο JSON, η μέθοδος, και τι παραμένει αμέτρητο βρίσκονται στο
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Δωρεάν** | OpenClaw + NVIDIA NemoClaw + Goose, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, cloud sync | $9 ανά κόμβο / μήνα |
| **Pro** | Starter + έλεγχος και αξιολόγηση: εγκρίσεις, πολιτικές κινδύνου εργαλείων, αξιολογήσεις, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel, αλλοιωσο-ανθεκτικό αρχείο ελέγχου | $19 ανά κόμβο / μήνα |

Τα ετήσια πλάνα, το Enterprise και οι τρέχουσες τιμές βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα κλειδιά αδειοδότησης
αυτοφιλοξενίας λειτουργούν χωρίς το cloud (`clawmetry license`). Η ακριβής κατανομή
δωρεάν/πληρωμένου βρίσκεται στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σας παραμένουν στο μηχάνημά σας

Το ClawMetry διαβάζει τοπικά αρχεία συνεδρίας και logs. **Κανένα δεδομένο συνεδρίας δεν φεύγει από
τη συσκευή σας εκτός αν εκτελέσετε την εντολή `clawmetry connect`** — κανένα prompt, καμία
απάντηση, κανένα όρισμα εργαλείου, κανένα περιεχόμενο αρχείου ή γραμμή log. Όταν συνδεθείτε, το
στιγμιότυπο κρυπτογραφείται από άκρο σε άκρο με ένα κλειδί που ποτέ δεν φεύγει από το μηχάνημά σας,
και αποκρυπτογραφείται στο πρόγραμμα περιήγησής σας. Αν ένας κόμβος δεν έχει κλειδί, η μεταφόρτωση
παραλείπεται αντί να σταλεί σε καθαρή μορφή, και καμία απάντηση διακομιστή δεν μπορεί να το
απενεργοποιήσει αυτό.

Δύο πράγματα εκτελούνται από προεπιλογή πριν συνδεθείτε, και τα δύο με δυνατότητα απενεργοποίησης
και κανένα δεν μεταφέρει δεδομένα συνεδρίας: ένα ανώνυμο ping εγκατάστασης και έναν έλεγχο έκδοσης
έναντι του PyPI. Μια προεπιλεγμένη εγκατάσταση αναζητά επίσης τη δημόσια IP σας μία φορά για μια
γραμμή banner εκκίνησης. Κάθε προορισμός, τι μεταφέρει και πώς να τον απενεργοποιήσετε αναφέρεται
στο [docs/EGRESS.md](docs/EGRESS.md)· οι εγκαταστάσεις αυτοφιλοξενίας, ανακατεύθυνσης και
απομόνωσης δικτύου δεν πραγματοποιούν καμία προαιρετική εξερχόμενη κλήση.

Η αποκρυπτογράφηση συμβαίνει στο πρόγραμμα περιήγησής σας, σε κώδικα που σας παρέχουμε. Αυτό
συνήθιζε να είναι μια υπόσχεση· τώρα είναι κάτι που μπορείτε να επαληθεύσετε. Κάθε γραμμή που
αγγίζει το κλειδί σας βρίσκεται σε ένα αναγνώσιμο αρχείο,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), το οποίο αποστέλλεται μέσα στο
wheel και εξυπηρετείται αυτούσιο, καρφιτσωμένο με ένα Subresource Integrity hash. Για να
επιβεβαιώσετε ότι το πρόγραμμα περιήγησης εκτελεί αυτό που δημοσιεύσαμε:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Αυτό που δεν αποδεικνύει: εμείς εξυπηρετούμε τη σελίδα που φορτώνει το αρχείο, οπότε θα μπορούσαμε
να εξυπηρετήσουμε διαφορετική σελίδα. Τα hashes ακεραιότητας σας προστατεύουν από ένα
παραβιασμένο CDN, όχι από τον προμηθευτή. Αυτό που κερδίζετε είναι ότι οποιαδήποτε αντικατάσταση
πρέπει να είναι σκόπιμη, ορατή στην πηγή της σελίδας, και διαφορετική από ένα αρχείο στο PyPI που
οποιοσδήποτε μπορεί να ανακτήσει. Η αυτοφιλοξενία ή η παραμονή μόνο τοπικά αφαιρεί εντελώς την
εξάρτηση.

## Εγκατάσταση

```bash
pip install clawmetry     # μετά: clawmetry
```

Ή η μονογραμμική εντολή: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Απαιτεί Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα runtime πράκτορα στο ίδιο
μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ή αφήστε τον πράκτορα να το ρυθμίσει για εσάς. Η δεξιότητα
[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) διδάσκει στα Claude Code, Codex, Cursor,
Gemini CLI, Copilot ή OpenCode να εγκαταστήσουν το ClawMetry, να αναφέρουν τι κάνουν και τι
ξοδεύουν οι πράκτορες στο μηχάνημα, να σταματήσουν μια συνεδρία κατ' αίτηση, και να συγκρατούν
επικίνδυνες κλήσεις εργαλείων για έγκριση:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσετε ένα runtime |
| [Υπερχείλιση context](docs/CONTEXT_BLOWOUT.md) | Παράθυρα ανά πάροχο, συμπίεση έναντι υπερχείλισης, κάλυψη ανά runtime |
| [Επιβάρυνση](docs/OVERHEAD.md) | Τι κοστίζει το instrumentation, μετρημένο, με το εργαλείο για αναπαραγωγή |
| [Δικαιώματα](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας επιπέδων, license CLI |
| [Εγκρίσεις & πολιτικές](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οπουδήποτε |
| [Φέρτε τον δικό σας πράκτορα](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain από άκρο σε άκρο, με εκτελέσιμα παραδείγματα |
| [Παρακολούθηση SDK](docs/SDK_TRACKING.md) | Απόδοση κόστους για πράκτορες που φτιάξατε εσείς |
| [Κανάλια συνομιλίας](docs/CHANNELS.md) | Οι adapters συνομιλίας που εμφανίζονται στη Ροή |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ρυθμίσεις sandboxed NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Εικόνα, compose, τοποθετήσεις τόμων |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος desktop, και πώς να τα απενεργοποιήσετε |

## Στιγμιότυπα

Κάθε αριθμός παρακάτω προέρχεται από ένα πραγματικό μηχάνημα, σε λειτουργία μόνο-ανάγνωσης, χωρίς
τίποτα προσχηματισμένο.

**Σας λέει πότε κάτι πάει στραβά, όχι απλώς τι συνέβη.**
Δύο banner ανωμαλιών στο επάνω μέρος: δαπάνη που τρέχει 7 φορές πάνω από τον ημερήσιο μέσο όρο, και
μια αιχμή κόστους 4,2x. Από κάτω τους, 324 από τις 667 πρόσφατες συνεδρίες φέρουν σήμα σπατάλης,
κατηγοριοποιημένο ανά αιτία.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Σας δείχνει πού πήγαν τα χρήματα, σε κάθε παράθυρο χρόνου.**
$252,47 σήμερα, $513,15 αυτή την εβδομάδα, $1.312,92 αυτόν τον μήνα, το καθένα με τα tokens από
πίσω του και πόσα από αυτά ήδη καλύπτει η συνδρομή σας. Κάτω από αυτό, περίπου $1.128/μήνα
κατηγοριοποιημένα ως ανακτήσιμα και $17.256/μήνα ήδη εξοικονομημένα από επαναχρησιμοποίηση cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Σχεδιάζει πώς ένα μήνυμα γίνεται απάντηση.**
Το ζωντανό διάγραμμα ροής: εσείς, το κανάλι από το οποίο έφτασε, το gateway, το μοντέλο που
απαντά αυτή τη στιγμή, και κάθε εργαλείο που χρησιμοποίησε. Οι κόμβοι ανάβουν καθώς η εργασία
κινείται μέσα τους.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Κάθε πράκτορας στο μηχάνημα, σε έναν πίνακα.**
Τι εκτελεί, τι κοστίζει τις τελευταίες 24 ώρες και σε όλη τη διάρκεια ζωής του, πότε εθεάθη
τελευταία φορά, ποιος τον κατέχει, και αν μια συνδρομή καλύπτει τον λογαριασμό. 14 πράκτορες εδώ,
3 συνεδρίες σε λειτουργία, 13 ήσυχες.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Δείχνει πού πήγε ο χρόνος και τα χρήματα ενός γύρου, εργαλείο προς εργαλείο.**
Ένας γύρος μιας πραγματικής συνεδρίας: 11 εργαλεία σε 11,2 λεπτά για $1,16. Κάθε κλήση Bash και
κλήση μοντέλου λαμβάνει τη δική της μπάρα στο χρονοδιάγραμμα, ώστε η εντολή που έτρεξε για 4,1
λεπτά και εκείνη που έτρεξε για 226ms να ξεχωρίζουν με μια ματιά.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Βαθμολογεί την εργασία, όχι μόνο τη δαπάνη.**
Ένα Α αυτή την εβδομάδα: 54 εργασίες επέστρεψαν καθαρές, 2 δύσκολες κόστισαν $48,57, και οι
εκτελέσεις με πολύ λίγη δραστηριότητα για να κριθούν παραλείπονται από τη βαθμολογία αντί να
μετρηθούν ως επιτυχίες. Κάθε δύσκολη εκτέλεση συνδέεται με το ίχνος της.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Δείχνει γιατί το παράθυρο context συνεχίζει να γεμίζει.**
715K από ένα παράθυρο 1M tokens στον τελευταίο γύρο, μια αιχμή 83,3%, 4 συμπιέσεις που όλες
ενεργοποιήθηκαν προληπτικά αντί κατά την υπερχείλιση, και η αξιοποίηση κάθε γύρου από πίσω τους.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Η ανίχνευση λειτουργεί χωρίς να ρυθμίσετε τίποτα.**
Οι ενσωματωμένοι ανιχνευτές είναι ενεργοί από την εγκατάσταση: πράκτορας σιώπησε, ροή τηλεμετρίας
σταμάτησε, αιχμή κόστους, έκρηξη tokens, σφάλματα αυξάνονται, αιχμή σφαλμάτων, όριο προϋπολογισμού,
υπογραφή απειλής ταιριάστηκε, εύρημα εργαλείου ασφαλείας, αλλαγή στάσης ασφαλείας. Οι δικοί σας
κανόνες είναι προαιρετικοί επιπλέον.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Η συγκράτηση μιας επικίνδυνης κλήσης είναι προαιρετική, και αποστέλλεται απενεργοποιημένη.**
Αναδρομικές διαγραφές, force pushes, sudo, μυστικά, εγκαταστάσεις πακέτων και εξερχόμενες κλήσεις
έχουν το καθένα έναν κανόνα που μπορείτε να ενεργοποιήσετε. Μέχρι να το κάνετε, το ClawMetry
παρακολουθεί και δεν αλλάζει τίποτα. Μόλις ενεργοποιηθεί ένας, οι αντίστοιχες κλήσεις περιμένουν
εδώ (ή στο κινητό σας) για έγκριση ή απόρριψη.

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

## Άδεια

MIT · Δημιουργήθηκε από τον [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
