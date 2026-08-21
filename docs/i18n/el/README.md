<!-- i18n-src:6795052055e2 -->
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

**Δες τον agent σου να σκέφτεται.** Παρατήρηση σε πραγματικό χρόνο για **26 runtimes AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex και 22 ακόμη. Ένα dashboard για ολόκληρο τον στόλο agent σου.

> 🌐 **Διάβασέ το στα:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [περισσότερα →](docs/i18n/)

Μία εντολή. Μηδενική διαμόρφωση. Αναγνωρίζει τα πάντα αυτόματα.

```bash
pip install clawmetry && clawmetry
```

Ανοίγει στο **http://localhost:8900**. Μηδενική διαμόρφωση: βρίσκει τα runtimes agent που ήδη έχεις, τα διαβάζει μόνο για ανάγνωση, και δεν αλλάζει τίποτα στον τρόπο λειτουργίας τους.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Λειτουργεί με 26 runtimes agent

**Δωρεάν στην open source εφαρμογή:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Σε πληρωμένο πλάνο:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Κάθε runtime παίρνει το ίδιο dashboard. Τρέξε αρκετά ταυτόχρονα και ο επιλογέας στην κεφαλίδα επαναπροσδιορίζει το πεδίο κάθε καρτέλας σε ένα από αυτά.

Έφτιαξες τον δικό σου agent πάνω σε ένα SDK αντί για αυτά; Ο interceptor παρακολουθεί και τις κλήσεις LLM του. Δες [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Τι παίρνεις

- **Sessions & transcripts**: τι έκανε κάθε agent, γύρο με γύρο, με replay
- **Κόστος & tokens**: ανά runtime, μοντέλο, session και ημέρα, με σημαίες ανωμαλιών
- **Flow**: ζωντανό διάγραμμα μηνυμάτων που κινούνται μέσα από κανάλια, μοντέλα και εργαλεία
- **Brain**: η ροή γεγονότων συλλογισμού και κλήσεων εργαλείων καθώς συμβαίνει
- **Memory & skills**: τα αρχεία και τα skills που φόρτωσε πραγματικά κάθε runtime
- **Health & logs**: δίσκος, μνήμη, ποσοστά σφαλμάτων, όρια ρυθμού, ζωντανή ροή logs
- **Alerts**: όρια budget, αιχμές σφαλμάτων, agent-offline, δρομολογημένα σε Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: παύση ριψοκίνδυνων κλήσεων εργαλείων *πριν* εκτελεστούν και έγκριση από το κινητό σου ([πώς](docs/APPROVALS.md))

## Τιμολόγηση

| Πλάνο | Τι καλύπτει | Τιμή |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, πλήρες dashboard, μόνο τοπικά | $0 |
| **Starter** | Κάθε άλλο runtime παραπάνω, προβολή στόλου, cloud sync | $9 ανά κόμβο / μήνα |
| **Pro** | Starter + governance: approvals, πολιτικές κινδύνου εργαλείων, evals, ανίχνευση ανωμαλιών, βελτιστοποιητής κόστους, εξαγωγή OTel | $19 ανά κόμβο / μήνα |

Ετήσια πλάνα, Enterprise και οι τρέχοντες αριθμοί βρίσκονται στο
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Τα κλειδιά αδειοδότησης αυτοφιλοξενίας
λειτουργούν χωρίς το cloud (`clawmetry license`). Ο ακριβής διαχωρισμός δωρεάν/πληρωμένου βρίσκεται
στο [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Τα δεδομένα σου παραμένουν στο μηχάνημά σου

Το ClawMetry διαβάζει τοπικά αρχεία sessions και logs. Τίποτα δεν φεύγει από το μηχάνημά σου εκτός
αν τρέξεις `clawmetry connect`. Ακόμα και τότε, το snapshot είναι κρυπτογραφημένο από άκρο σε άκρο
με ένα κλειδί που δεν φεύγει ποτέ από το μηχάνημά σου, και αποκρυπτογραφείται στο πρόγραμμα περιήγησής σου.

## Εγκατάσταση

```bash
pip install clawmetry     # then: clawmetry
```

Ή η μονογραμμική εντολή: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Χρειάζεται Python 3.8+ σε macOS, Linux ή Windows, και τουλάχιστον ένα runtime agent στο ίδιο
μηχάνημα. Οδηγίες Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Τεκμηρίωση

| | |
|---|---|
| [Συμβατότητα runtime](docs/compatibility.md) | Τι διαβάζει κάθε adapter, και πώς να προσθέσεις ένα runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Δωρεάν έναντι πληρωμένου, πίνακας επιπέδων, license CLI |
| [Approvals & πολιτικές](docs/APPROVALS.md) | Έλεγχος πριν την εκτέλεση, βαθμολόγηση κινδύνου, εγκρίσεις από κινητό |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Εξαγωγή traces οπουδήποτε, εισαγωγή OTLP από οτιδήποτε |
| [SDK tracking](docs/SDK_TRACKING.md) | Απόδοση κόστους για agents που έφτιαξες εσύ ο ίδιος |
| [Κανάλια chat](docs/CHANNELS.md) | Οι adapters chat που εμφανίζονται στο Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Απομονωμένες (sandboxed) ρυθμίσεις NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Αρχιτεκτονική](ARCHITECTURE.md) · [Ανάπτυξη](docs/DEVELOPMENT.md) | Πώς λειτουργεί εσωτερικά· εκτέλεση από τον πηγαίο κώδικα |
| [Τηλεμετρία](docs/TELEMETRY.md) | Τα ανώνυμα pings εγκατάστασης και ανοίγματος desktop, και πώς να τα απενεργοποιήσεις |

## Στιγμιότυπα οθόνης

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokens, sessions, health | **Brain**: ζωντανή ροή γεγονότων agent |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Κόστος**: ανά μοντέλο και session | **Approvals**: έλεγχος ριψοκίνδυνων κλήσεων εργαλείων |

Περισσότερα, ανά runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Ιστορικό αστεριών

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
