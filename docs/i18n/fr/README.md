<!-- i18n-src:dc34072b2955 -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Voyez votre agent réfléchir.** Observabilité en temps réel pour **26 runtimes d'agents IA** : [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex et 22 autres. Un seul tableau de bord pour toute votre flotte d'agents.

> 🌐 **Lire ceci en :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une seule commande. Zéro configuration. Détection automatique de tout.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900**. Zéro configuration : il trouve les runtimes d'agents
que vous avez déjà, les lit en lecture seule, et ne change rien à leur fonctionnement.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatible avec 26 runtimes d'agents

**Gratuit dans l'application open source :** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**Sur un plan payant :** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Chaque runtime obtient le même tableau de bord. Exécutez-en plusieurs en même temps et le
sélecteur dans l'en-tête recentre chaque onglet sur l'un d'eux.

Vous avez créé votre propre agent avec un SDK au lieu d'utiliser un runtime existant ? L'intercepteur suit aussi
ses appels LLM. Voir [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ce que vous obtenez

- **Sessions et transcriptions** : ce que chaque agent a fait, tour par tour, avec relecture
- **Coûts et tokens** : par runtime, modèle, session et jour, avec signalement des anomalies
- **Flow** : diagramme en direct des messages circulant à travers les canaux, les modèles et les outils
- **Brain** : le flux d'événements de raisonnement et d'appels d'outils en temps réel
- **Mémoire et compétences** : les fichiers et compétences réellement chargés par chaque runtime
- **Santé et logs** : disque, mémoire, taux d'erreur, limites de débit, flux de logs en direct
- **Alertes** : plafonds budgétaires, pics d'erreurs, agent hors ligne, routées vers Slack, Discord, PagerDuty, Telegram, Email
- **Approbations** : mettez en pause les appels d'outils risqués *avant* leur exécution et approuvez depuis votre téléphone ([comment](docs/APPROVALS.md))

## Tarification

| Plan | Ce qui est couvert | Prix |
|---|---|---|
| **Gratuit** | OpenClaw + NVIDIA NemoClaw, tableau de bord complet, local uniquement | 0 $ |
| **Starter** | Tous les autres runtimes ci-dessus, vue flotte, synchronisation cloud | 9 $ par nœud / mois |
| **Pro** | Starter + gouvernance : approbations, politiques de risque des outils, évaluations, détection d'anomalies, optimiseur de coûts, export OTel | 19 $ par nœud / mois |

Les plans annuels, Enterprise et les tarifs actuels se trouvent sur
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Les clés de licence auto-hébergées
fonctionnent sans le cloud (`clawmetry license`). La répartition exacte gratuit/payant est
détaillée dans [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Vos données restent sur votre machine

ClawMetry lit les fichiers de session et les logs locaux. Rien ne quitte votre machine sauf si
vous exécutez `clawmetry connect`. Et même dans ce cas, l'instantané est chiffré de bout en bout
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
| [Compatibilité des runtimes](docs/compatibility.md) | Ce que lit chaque adaptateur, et comment ajouter un runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuit vs payant, matrice des niveaux, CLI de licence |
| [Approbations et politiques](docs/APPROVALS.md) | Contrôle pré-exécution, notation des risques, approbations par téléphone |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportez des traces n'importe où, ingérez OTLP depuis n'importe quoi |
| [Suivi SDK](docs/SDK_TRACKING.md) | Attribution des coûts pour les agents que vous avez créés vous-même |
| [Canaux de chat](docs/CHANNELS.md) | Les adaptateurs de chat affichés dans Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurations NVIDIA NemoClaw en bac à sable |
| [Docker](docs/DOCKER.md) | Image, compose, montages de volumes |
| [Architecture](ARCHITECTURE.md) · [Développement](docs/DEVELOPMENT.md) | Fonctionnement interne ; exécution depuis les sources |
| [Télémétrie](docs/TELEMETRY.md) | Les pings anonymes d'installation et d'ouverture de l'application, et comment les désactiver |

## Captures d'écran

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview** : tokens, sessions, santé | **Brain** : flux d'événements de l'agent en direct |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Coût** : par modèle et par session | **Approbations** : contrôle des appels d'outils risqués |

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
