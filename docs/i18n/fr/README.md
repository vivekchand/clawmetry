<!-- i18n-src:c111f32e69a5 -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Voyez votre agent réfléchir.** Observabilité en temps réel pour **29 runtimes d'agents IA** : [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex et 25 autres. Un seul tableau de bord pour toute votre flotte d'agents.

> 🌐 **Lisez ceci en :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une seule commande. Aucune configuration. Tout est détecté automatiquement.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900**. Aucune configuration : l'outil trouve les runtimes d'agents
que vous avez déjà, les lit en lecture seule, et ne change rien à leur fonctionnement.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Compatible avec 29 runtimes d'agents

**Gratuit dans l'application open source :** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sur un plan payant :** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Chaque runtime bénéficie du même tableau de bord. Lancez-en plusieurs à la fois et le
sélecteur d'en-tête recentre chaque onglet sur l'un d'entre eux.

Vous avez construit votre propre agent sur un SDK ? L'intercepteur suit aussi ses
appels LLM. Voir [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ce que vous obtenez

- **Sessions et transcriptions** : ce que chaque agent a fait, tour par tour, avec relecture
- **Coûts et tokens** : par runtime, modèle, session et jour, avec des signalements d'anomalies
- **Flow** : diagramme en direct des messages circulant entre les canaux, les modèles et les outils
- **Brain** : le flux d'événements de raisonnement et d'appels d'outils, en direct
- **Mémoire et compétences** : les fichiers et compétences réellement chargés par chaque runtime
- **Santé et journaux** : disque, mémoire, taux d'erreur, limites de débit, flux de journaux en direct
- **Alertes** : plafonds budgétaires, pics d'erreurs, agent hors ligne, routées vers Slack, Discord, PagerDuty, Telegram, Email
- **Approbations** : mettez en pause les appels d'outils risqués *avant* leur exécution et approuvez-les depuis votre téléphone ([comment](docs/APPROVALS.md))

## Tarification

| Plan | Ce qui est couvert | Prix |
|---|---|---|
| **Gratuit** | OpenClaw + NVIDIA NemoClaw + Goose, tableau de bord complet, local uniquement | 0 $ |
| **Starter** | Tous les autres runtimes ci-dessus, vue flotte, synchronisation cloud | 9 $ par nœud / mois |
| **Pro** | Starter + gouvernance : approbations, politiques de risque des outils, évaluations, détection d'anomalies, optimiseur de coûts, export OTel | 19 $ par nœud / mois |

Les plans annuels, Entreprise et les tarifs actuels se trouvent sur
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Les clés de licence auto-hébergées
fonctionnent sans le cloud (`clawmetry license`). La répartition exacte gratuit/payant se trouve
dans [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Vos données restent sur votre machine

ClawMetry lit les fichiers de session et les journaux locaux. Rien ne quitte votre machine à moins
que vous n'exécutiez `clawmetry connect`. Même dans ce cas, l'instantané est chiffré de bout en bout
avec une clé qui ne quitte jamais votre machine, et déchiffré dans votre navigateur.

## Installation

```bash
pip install clawmetry     # puis : clawmetry
```

Ou la commande en une ligne : `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Nécessite Python 3.8+ sur macOS, Linux ou Windows, et au moins un runtime d'agent sur
la même machine. Instructions Docker : [docs/DOCKER.md](docs/DOCKER.md).

## Documentation

| | |
|---|---|
| [Compatibilité des runtimes](docs/compatibility.md) | Ce que chaque adaptateur lit, et comment ajouter un runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuit vs payant, matrice des niveaux, CLI de licence |
| [Approbations et politiques](docs/APPROVALS.md) | Contrôle pré-exécution, évaluation des risques, approbations par téléphone |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportez des traces n'importe où, ingérez OTLP depuis n'importe quoi |
| [Suivi SDK](docs/SDK_TRACKING.md) | Attribution des coûts pour les agents que vous avez construits vous-même |
| [Canaux de discussion](docs/CHANNELS.md) | Les adaptateurs de chat affichés dans Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurations NVIDIA NemoClaw en bac à sable |
| [Docker](docs/DOCKER.md) | Image, compose, montages de volumes |
| [Architecture](ARCHITECTURE.md) · [Développement](docs/DEVELOPMENT.md) | Comment ça fonctionne en interne ; exécution depuis les sources |
| [Télémétrie](docs/TELEMETRY.md) | Les pings anonymes d'installation et d'ouverture du bureau, et comment les désactiver |

## Captures d'écran

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview** : tokens, sessions, santé | **Agents** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost** : par modèle et par session | **Approvals** : filtre les appels d'outils risqués |

Plus de captures, par runtime : [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Historique des étoiles

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licence

MIT · Créé par [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
