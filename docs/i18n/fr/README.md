<!-- i18n-src:56ff57310588 -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Voyez votre agent réfléchir.** Observabilité en temps réel pour les agents IA [OpenClaw](https://github.com/openclaw/openclaw).

> 🌐 **À lire dans votre langue :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une seule commande. Aucune configuration. Détection automatique de tout.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900** et c'est terminé.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Ce que vous obtenez

- **Flow** — Diagramme animé en direct montrant les messages circulant à travers les canaux, le cerveau, les outils, puis revenant
- **Overview** — Vérifications de santé, carte thermique d'activité, nombre de sessions, infos sur le modèle
- **Usage** — Suivi des tokens et des coûts avec ventilations quotidiennes/hebdomadaires/mensuelles
- **Sessions** — Sessions d'agents actives avec modèle, tokens, dernière activité
- **Crons** — Tâches planifiées avec statut, prochaine exécution, durée
- **Logs** — Diffusion de logs en temps réel avec code couleur
- **Memory** — Parcourez SOUL.md, MEMORY.md, AGENTS.md, notes quotidiennes
- **Transcripts** — Interface en bulles de chat pour lire les historiques de session
- **Alerts** — Plafonds de budget, déclencheurs sur taux d'erreur, détection d'agent hors ligne ; routage vers Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** — Soumettez les suppressions destructrices, les force pushes, les mutations de base de données, sudo, les installations de paquets et les appels réseau à une validation en un clic

## Captures d'écran

### 🧠 Brain — Flux d'événements de l'agent en direct
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilisation des tokens et résumé de session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Flux d'appels d'outils en temps réel
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ventilation des coûts par modèle et par session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navigateur de fichiers du workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Posture et journal d'audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Plafonds de budget, déclencheurs sur taux d'erreur, webhooks vers Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Soumettez les appels d'outils risqués à une validation manuelle ; règles de protection adossées à une politique
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Installation

**One-liner (recommandé) :**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip :**
```bash
pip install clawmetry
clawmetry
```

**Depuis les sources :**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Développement du frontend v2

L'application React v2 réside dans `frontend/` et est servie sur `/v2` lorsque le
serveur Flask est démarré avec v2 activé.

Utilisez deux terminaux pendant le développement :

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

Ouvrez `http://localhost:5173/v2/`. Vite relaie les requêtes `/api` vers
`http://localhost:8900`, afin que l'application React puisse communiquer avec le serveur Flask local
sans configuration CORS supplémentaire.

Pour construire le bundle livré avec le paquet Python :

```bash
cd frontend
npm run build
```

Le bundle de production est écrit dans `clawmetry/static/v2/dist/`.

## Compatibilité des runtimes / agents

ClawMetry observe de nombreux runtimes d'agents IA, pas seulement OpenClaw. Chaque runtime autre qu'OpenClaw est livré avec un adaptateur de lecture dédié qui traduit son format de session natif vers les formats unifiés de ClawMetry ; le daemon les ingère dans le même store DuckDB + snapshot cloud, étiquetés avec le runtime, et l'onglet de relecture de session affiche un **sélecteur de runtime** lorsque plusieurs sont présents. Consultez [`docs/compatibility.md`](docs/compatibility.md) pour la matrice complète + un guide d'ajout de runtimes, et [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) pour l'introduction à la famille OpenClaw.

| Runtime / Agent | Statut | Notes |
|---|---|---|
| **OpenClaw** | Natif | Runtime de référence, détecté automatiquement |
| **PicoClaw** | Adaptateur bêta | JSONL `providers.Message` à plat (`~/.picoclaw/workspace/sessions`). Transcriptions, modèle, appels d'outils. |
| **NanoClaw** | Adaptateur bêta | SQLite par session (`data/v2-sessions`). Transcriptions + nombre de messages. |
| **Hermes** | Adaptateur bêta | SQLite `~/.hermes/state.db`. Transcriptions, modèle, tokens/coût. |
| **Claude Code** | Adaptateur bêta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcriptions, modèle, appels d'outils + raisonnement, utilisation des tokens. |
| **Codex** | Adaptateur bêta | JSONL de rollout `~/.codex/sessions/...`. Transcriptions, modèle, appels d'outils, utilisation des tokens. |
| **Cursor** | Adaptateur bêta | SQLite `state.vscdb`. Transcriptions de chat/composer, modèle. |
| **Aider** | Adaptateur bêta | `.aider.chat.history.md` par projet. Transcriptions, modèle, nombre de tokens. |
| **Goose** | Adaptateur bêta | SQLite `~/.local/share/goose`. Transcriptions, modèle, appels d'outils, totaux de tokens. |

« Adaptateur bêta » signifie que ClawMetry fournit un lecteur pour le format réel sur disque de ce runtime, chacun étant construit + vérifié contre une installation réelle sur une machine réelle (voir `tests/fixtures/runtimes/<rt>/`). Les adaptateurs sont en lecture seule ; chacun est honnête sur ce que son runtime stocke réellement (par exemple, PicoClaw/NanoClaw/Cursor n'écrivent pas le coût en tokens sur disque). Lorsque plusieurs runtimes s'exécutent sur un même nœud, le sélecteur de runtime restreint la vue des sessions à un seul pour une analyse approfondie et nette.

## OpenTelemetry — neutre vis-à-vis des fournisseurs, envoyez vos traces n'importe où

ClawMetry parle **OpenTelemetry** dans les deux sens, en utilisant les **conventions sémantiques GenAI**, de sorte que les traces de votre agent ne sont jamais verrouillées dans un seul outil.

**Exportez** chaque session — appels LLM, outils, sous-agents, tokens, coût — sous forme de spans GenAI OTLP/HTTP vers n'importe quel collecteur (Datadog, Grafana, Honeycomb, ou votre propre collecteur OTel) :

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Les en-têtes d'authentification et l'intervalle d'interrogation sont des variables d'environnement optionnelles :

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingestion** — le récepteur OTLP intégré accepte les traces et les métriques de tout le reste sur `/v1/traces` et `/v1/metrics` (`pip install clawmetry[otel]` pour l'ingestion protobuf).

Vous obtenez le tableau de bord ClawMetry sans configuration, local-first, **et** vos données dans n'importe quel backend que votre équipe utilise déjà : aucun verrouillage, aucun second agent à installer.

## Configuration

La plupart des gens n'ont besoin d'aucune configuration. ClawMetry détecte automatiquement votre workspace, vos logs, vos sessions et vos crons.

Si vous avez besoin de personnaliser :

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Toutes les options : `clawmetry --help`

## Canaux pris en charge

ClawMetry affiche l'activité en direct de chaque canal OpenClaw que vous avez configuré. Seuls les canaux réellement configurés dans votre `openclaw.json` apparaissent dans le diagramme Flow ; ceux qui ne sont pas configurés sont automatiquement masqués.

Cliquez sur n'importe quel nœud de canal dans le Flow pour voir une vue en bulles de chat en direct avec le nombre de messages entrants/sortants.

| Canal | Statut | Popup en direct | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Complet | ✅ | Messages, statistiques, rafraîchissement toutes les 10 s |
| 💬 **iMessage** | ✅ Complet | ✅ | Lit directement `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Complet | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Complet | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Complet | ✅ | Détection de guilde + canal |
| 🟪 **Slack** | ✅ Complet | ✅ | Détection de workspace + canal |
| 🌐 **Webchat** | ✅ Complet | ✅ | Sessions de l'interface web intégrée |
| 📡 **IRC** | ✅ Complet | ✅ | Interface en bulles de style terminal |
| 🍏 **BlueBubbles** | ✅ Complet | ✅ | iMessage via l'API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Complet | ✅ | Via les webhooks de l'API Chat |
| 🟣 **MS Teams** | ✅ Complet | ✅ | Via le plugin bot Teams |
| 🔷 **Mattermost** | ✅ Complet | ✅ | Chat d'équipe auto-hébergé |
| 🟩 **Matrix** | ✅ Complet | ✅ | Décentralisé, prise en charge E2EE |
| 🟢 **LINE** | ✅ Complet | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Complet | ✅ | DMs NIP-04 décentralisés |
| 🟣 **Twitch** | ✅ Complet | ✅ | Chat via connexion IRC |
| 🔷 **Feishu/Lark** | ✅ Complet | ✅ | Abonnement aux événements WebSocket |
| 🔵 **Zalo** | ✅ Complet | ✅ | Zalo Bot API |

> **Détection automatique :** ClawMetry lit votre `~/.openclaw/openclaw.json` et n'affiche que les canaux que vous avez réellement configurés. Aucune configuration manuelle requise.

## Déploiement Docker

Vous voulez exécuter ClawMetry dans un conteneur ? Aucun problème ! 🐳

**Démarrage rapide avec Docker :**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Exemple Docker Compose :**

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

> **Remarque :** Lorsque vous exécutez dans Docker, assurez-vous de monter votre workspace OpenClaw et vos répertoires de logs afin que ClawMetry puisse détecter automatiquement votre installation.

## Prérequis

- Python 3.8+
- Flask (installé automatiquement via pip)
- OpenClaw s'exécutant sur la même machine (ou volumes montés pour Docker)
- Linux ou macOS

## Prise en charge de NemoClaw / OpenShell

ClawMetry détecte automatiquement [NemoClaw](https://github.com/NVIDIA/NemoClaw) — l'enveloppe de sécurité d'entreprise de NVIDIA pour OpenClaw qui exécute les agents à l'intérieur de conteneurs OpenShell en bac à sable.

Aucune configuration supplémentaire n'est nécessaire dans la plupart des cas. Le daemon de synchronisation découvre automatiquement les fichiers de session, qu'ils résident dans `~/.openclaw/` sur l'hôte ou à l'intérieur d'un conteneur OpenShell.

### Comment ça fonctionne

ClawMetry détecte NemoClaw de deux façons :

1. **Détection de binaire** — vérifie la présence du CLI `nemoclaw` et exécute `nemoclaw status` pour obtenir les infos sur le bac à sable
2. **Détection de conteneur** — scanne les conteneurs Docker en cours d'exécution à la recherche d'images `openshell`, `nemoclaw` ou `ghcr.io/nvidia/`, puis lit les sessions via les montages de volume ou `docker cp`

Les fichiers de session synchronisés depuis les conteneurs NemoClaw sont étiquetés avec les métadonnées `runtime=nemoclaw` et `container_id` dans le tableau de bord cloud, afin que vous puissiez les distinguer des sessions OpenClaw standard en un coup d'œil.

### Configuration recommandée : le daemon de synchronisation sur l'HÔTE

Pour une meilleure expérience, exécutez le daemon de synchronisation de ClawMetry sur la **machine hôte** (pas à l'intérieur du bac à sable). Cela évite les restrictions de la politique réseau de NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Le daemon de synchronisation trouvera automatiquement les sessions à l'intérieur de tout conteneur OpenShell en cours d'exécution.

### Optionnel : nom de bac à sable explicite

Si la détection automatique ne fonctionne pas, pointez ClawMetry vers le bon bac à sable :

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Exécution à l'intérieur du bac à sable (avancé)

Si vous devez exécuter le daemon de synchronisation **à l'intérieur** du bac à sable OpenShell, ajoutez cette règle de sortie à votre politique réseau NemoClaw afin qu'il puisse atteindre l'API d'ingestion de ClawMetry :

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Appliquez avec :

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Ports et points de terminaison

| Point de terminaison | Port | Protocole | Requis |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oui (daemon de synchronisation → cloud) |
| `localhost:8900` | 8900 | HTTP | Oui (interface du tableau de bord local) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Pour la découverte des sessions dans les conteneurs |

Le daemon de synchronisation n'effectue que des appels HTTPS sortants vers `ingest.clawmetry.com`. Aucun port entrant n'est requis.

---

## Déploiement cloud

Consultez le **[Guide de test cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** pour les tunnels SSH, le reverse proxy et Docker.

## Tests

Ce projet est testé avec BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Télémétrie

ClawMetry envoie un unique ping anonyme de « première exécution » à
`https://app.clawmetry.com/api/install` la première fois que vous exécutez le
CLI `clawmetry` sur une nouvelle machine. Nous l'utilisons pour compter les installations (la
seule métrique marketing dont nous disposons pour un projet OSS) et pour savoir quels
frameworks d'agents nos utilisateurs ont installés.

**Exactement un POST par installation**, contenant :

| Champ | Exemple | Pourquoi |
|---|---|---|
| `install_id` | UUID aléatoire stocké dans `~/.clawmetry/install_id` | déduplication ; non lié à votre e-mail ou api_key |
| `version` | `0.12.167` | quelles versions sont en circulation |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorités de prise en charge des plateformes |
| `python` | `3.11.15` | matrice de prise en charge des versions de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | avec quels agents nous devrions nous intégrer ensuite |
| `is_ci` / `ci_provider` | `true` / `github_actions` | séparer les installations humaines du bruit CI |

**Ce que nous n'envoyons PAS** : l'IP (le cloud déduit le code pays côté serveur
à partir de la requête, puis supprime l'IP), le nom d'hôte, le nom d'utilisateur, le chemin du workspace,
le contenu des fichiers, votre api_key, votre e-mail, ou toute donnée PII ou
spécifique au workspace. La charge utile transmise est auditable dans
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Désactiver** (n'importe lequel de ceux-ci la désactive définitivement) :

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Une défaillance réseau ici ne bloque jamais l'exécution de `clawmetry` : le
ping est de type « fire-and-forget » sur un thread daemon avec un délai d'expiration de 3 s.

## Historique des étoiles

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licence

MIT

---

<p align="center">
  <strong>🦞 Voyez votre agent réfléchir</strong><br>
  <sub>Construit par <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Fait partie de l'écosystème <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
