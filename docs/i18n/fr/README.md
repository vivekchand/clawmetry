<!-- i18n-src:48548997be76 -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Voyez votre agent réfléchir.** Observabilité en temps réel pour **12 environnements d'exécution d'agents IA** : [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex et 8 autres. Un seul tableau de bord pour toute votre flotte d'agents.

> 🌐 **Lire dans une autre langue :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Une seule commande. Zéro configuration. Détection automatique de tout.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900** et c'est tout.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatible avec 12 environnements d'exécution d'agents

ClawMetry a débuté comme outil d'observabilité pour OpenClaw, et mesure désormais **toute votre flotte d'agents** dans un seul tableau de bord, en détectant automatiquement chaque environnement d'exécution sur votre machine :

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw et NemoClaw sont gratuits dans l'application open source ; les autres environnements d'exécution s'activent avec ClawMetry Cloud ou une licence Pro auto-hébergée. Changez d'environnement depuis l'en-tête et chaque onglet — coût, jetons, outils, traces — se recentre sur cet environnement.

## Ce que vous obtenez

- **Flow** — Diagramme animé en direct montrant les messages circulant à travers les canaux, le cerveau, les outils, et en retour
- **Overview** — Vérifications de santé, carte thermique d'activité, nombre de sessions, informations sur le modèle
- **Usage** — Suivi des jetons et des coûts avec des ventilations quotidiennes, hebdomadaires et mensuelles
- **Sessions** — Sessions d'agents actives avec modèle, jetons, dernière activité
- **Crons** — Tâches planifiées avec statut, prochaine exécution, durée
- **Logs** — Diffusion de journaux en temps réel avec code couleur
- **Memory** — Parcourir SOUL.md, MEMORY.md, AGENTS.md, notes quotidiennes
- **Transcripts** — Interface en bulles de chat pour lire l'historique des sessions
- **Alerts** — Plafonds budgétaires, déclencheurs de taux d'erreur, détection d'agent hors ligne ; routage vers Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Soumettez les suppressions destructives, les push forcés, les mutations de base de données, sudo, les installations de paquets et les appels réseau à une validation en un clic

## Captures d'écran

### 🧠 Brain — Flux d'événements de l'agent en direct
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilisation des jetons et résumé des sessions
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Flux d'appels d'outils en temps réel
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Répartition des coûts par modèle et par session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navigateur de fichiers de l'espace de travail
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Posture de sécurité et journal d'audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Plafonds budgétaires, déclencheurs de taux d'erreur, webhooks vers Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Soumettez les appels d'outils risqués à une validation manuelle ; règles de protection basées sur des politiques
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Installation

**En une seule ligne (recommandé) :**
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

L'application React v2 se trouve dans `frontend/` et est accessible à `/v2` lorsque le serveur Flask est démarré avec v2 activé.

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

Ouvrez `http://localhost:5173/v2/`. Vite transfère les requêtes `/api` vers `http://localhost:8900`, de sorte que l'application React peut communiquer avec le serveur Flask local sans configuration CORS supplémentaire.

Pour construire le bundle livré avec le paquet Python :

```bash
cd frontend
npm run build
```

Le bundle de production est écrit dans `clawmetry/static/v2/dist/`.

## Compatibilité des environnements d'exécution / agents

ClawMetry observe de nombreux environnements d'exécution d'agents IA, pas seulement OpenClaw. Chaque environnement non-OpenClaw est livré avec un adaptateur de lecture dédié qui traduit son format de session natif en structures unifiées de ClawMetry ; le démon les intègre dans le même magasin DuckDB et l'instantané cloud, marqués avec l'environnement d'exécution, et l'onglet de relecture de session affiche un **sélecteur d'environnement** lorsque plusieurs sont présents. Consultez [`docs/compatibility.md`](docs/compatibility.md) pour la matrice complète et un guide d'ajout d'environnements, et [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) pour une introduction à la famille OpenClaw.

| Environnement / Agent | Statut | Notes |
|---|---|---|
| **OpenClaw** | Natif | Environnement de référence, détection automatique |
| **PicoClaw** | Adaptateur bêta | JSONL `providers.Message` plat (`~/.picoclaw/workspace/sessions`). Transcriptions, modèle, appels d'outils. |
| **NanoClaw** | Adaptateur bêta | SQLite par session (`data/v2-sessions`). Transcriptions et nombre de messages. |
| **Hermes** | Adaptateur bêta | SQLite `~/.hermes/state.db`. Transcriptions, modèle, jetons/coût. |
| **Claude Code** | Adaptateur bêta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcriptions, modèle, appels d'outils et réflexion, utilisation des jetons. |
| **Codex** | Adaptateur bêta | JSONL Rollout `~/.codex/sessions/...`. Transcriptions, modèle, appels d'outils, utilisation des jetons. |
| **Cursor** | Adaptateur bêta | SQLite `state.vscdb`. Transcriptions chat/composer, modèle. |
| **Aider** | Adaptateur bêta | `.aider.chat.history.md` par projet. Transcriptions, modèle, nombre de jetons. |
| **Goose** | Adaptateur bêta | SQLite `~/.local/share/goose`. Transcriptions, modèle, appels d'outils, totaux de jetons. |
| **opencode** | Adaptateur bêta | SQLite `~/.local/share/opencode`. Transcriptions, modèle, appels d'outils, jetons et coût. |
| **Qwen Code** | Adaptateur bêta | JSONL `~/.qwen/projects/.../chats`. Transcriptions, modèle, appels d'outils, utilisation des jetons. |

"Adaptateur bêta" signifie que ClawMetry intègre un lecteur pour le format réel sur disque de cet environnement, chacun construit et vérifié contre une installation réelle sur une vraie machine (voir `tests/fixtures/runtimes/<rt>/`). Les adaptateurs sont en lecture seule ; chacun indique honnêtement ce que son environnement stocke réellement (par exemple, PicoClaw/NanoClaw/Cursor n'écrivent pas le coût en jetons sur disque). Lorsque plusieurs environnements s'exécutent sur un même nœud, le sélecteur d'environnement filtre la vue des sessions sur l'un d'eux pour une analyse approfondie claire.

## Suivre n'importe quel agent SDK — attribution des coûts hors boucle

Les environnements ci-dessus écrivent tous des sessions sur disque. Votre propre **agent de production** — celui que vous avez construit sur l'OpenAI Agents SDK, LangChain, le Vercel AI SDK, LlamaIndex, E2B, ou une simple boucle `httpx` — ne le fait pas. L'intercepteur zéro-configuration de ClawMetry capture tout de même ses appels LLM (coût, jetons, latence, erreurs) en appliquant un monkey-patch sur `httpx`/`requests` :

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou la variable d'environnement `CLAWMETRY_SOURCE=support-agent`) étiquette chaque appel avec une **source nommée**, de sorte que chaque produit que vous exécutez apparaît comme sa propre ligne de premier ordre avec attribution des coûts dans la carte **🔌 Sources hors boucle** du tableau de bord sur Overview — appels, fournisseurs, latence, taux d'erreur par agent. Aucune source définie ? Les appels sont quand même suivis ; la carte reste simplement masquée.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Il s'agit de la même couche de données que celle alimentée par les adaptateurs d'environnement (DuckDB vers instantané cloud), donc les sources hors boucle se synchronisent vers le tableau de bord cloud de la même manière que tout le reste, chiffrées de bout en bout.

## OpenTelemetry — neutre vis-à-vis des fournisseurs, envoyez vos traces où vous voulez

ClawMetry parle **OpenTelemetry** dans les deux sens, en utilisant les **conventions sémantiques GenAI**, de sorte que vos traces d'agents ne sont jamais enfermées dans un seul outil.

**Exportez** chaque session — appels LLM, outils, sous-agents, jetons, coût — sous forme de spans GenAI OTLP/HTTP vers n'importe quel collecteur (Datadog, Grafana, Honeycomb, ou votre propre OTel Collector) :

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

**Ingestion** — le récepteur OTLP intégré accepte les traces et métriques de tout autre système aux adresses `/v1/traces` et `/v1/metrics` (`pip install clawmetry[otel]` pour l'ingestion protobuf).

Vous bénéficiez du tableau de bord ClawMetry zéro-configuration et local **et** de vos données dans le backend que votre équipe utilise déjà — sans enfermement, sans second agent à installer.

## Configuration

La plupart des utilisateurs n'ont besoin d'aucune configuration. ClawMetry détecte automatiquement votre espace de travail, vos journaux, vos sessions et vos crons.

Si vous avez besoin de personnaliser :

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Toutes les options : `clawmetry --help`

## Canaux pris en charge

ClawMetry affiche l'activité en direct pour chaque canal OpenClaw que vous avez configuré. Seuls les canaux réellement configurés dans votre `openclaw.json` apparaissent dans le diagramme Flow — les canaux non configurés sont automatiquement masqués.

Cliquez sur n'importe quel nœud de canal dans le Flow pour voir une vue en bulles de chat en direct avec les compteurs de messages entrants et sortants.

| Canal | Statut | Popup en direct | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Complet | ✅ | Messages, statistiques, actualisation toutes les 10s |
| 💬 **iMessage** | ✅ Complet | ✅ | Lit `~/Library/Messages/chat.db` directement |
| 💚 **WhatsApp** | ✅ Complet | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Complet | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Complet | ✅ | Détection de serveur et de canal |
| 🟪 **Slack** | ✅ Complet | ✅ | Détection d'espace de travail et de canal |
| 🌐 **Webchat** | ✅ Complet | ✅ | Sessions d'interface web intégrée |
| 📡 **IRC** | ✅ Complet | ✅ | Interface en bulles de style terminal |
| 🍏 **BlueBubbles** | ✅ Complet | ✅ | iMessage via l'API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Complet | ✅ | Via les webhooks de l'API Chat |
| 🟣 **MS Teams** | ✅ Complet | ✅ | Via le plugin de bot Teams |
| 🔷 **Mattermost** | ✅ Complet | ✅ | Chat d'équipe auto-hébergé |
| 🟩 **Matrix** | ✅ Complet | ✅ | Décentralisé, support E2EE |
| 🟢 **LINE** | ✅ Complet | ✅ | API de messagerie LINE |
| ⚡ **Nostr** | ✅ Complet | ✅ | Messages privés décentralisés NIP-04 |
| 🟣 **Twitch** | ✅ Complet | ✅ | Chat via connexion IRC |
| 🔷 **Feishu/Lark** | ✅ Complet | ✅ | Abonnement aux événements WebSocket |
| 🔵 **Zalo** | ✅ Complet | ✅ | API Bot Zalo |

> **Détection automatique :** ClawMetry lit votre `~/.openclaw/openclaw.json` et n'affiche que les canaux que vous avez réellement configurés. Aucune configuration manuelle requise.

## Déploiement Docker

Vous voulez exécuter ClawMetry dans un conteneur ? Aucun problème ! 🐳

**Démarrage rapide avec Docker :**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
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

> **Remarque :** Lors de l'exécution dans Docker, montez les répertoires de données et de journaux de votre agent (par exemple `~/.openclaw`, `~/.claude`, `~/.codex`) afin que ClawMetry puisse détecter automatiquement votre configuration.

## Prérequis

- Python 3.8+
- Flask (installé automatiquement via pip)
- Un environnement d'exécution d'agent IA sur la même machine : OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw ou PicoClaw (ou des volumes montés pour Docker)
- Linux ou macOS

## Prise en charge de NemoClaw / OpenShell

ClawMetry détecte automatiquement [NemoClaw](https://github.com/NVIDIA/NemoClaw) — le wrapper de sécurité entreprise de NVIDIA pour OpenClaw qui exécute les agents dans des conteneurs OpenShell sandbox.

Aucune configuration supplémentaire n'est nécessaire dans la plupart des cas. Le démon de synchronisation découvre automatiquement les fichiers de session qu'ils se trouvent dans `~/.openclaw/` sur l'hôte ou à l'intérieur d'un conteneur OpenShell.

### Fonctionnement

ClawMetry détecte NemoClaw de deux manières :

1. **Détection par binaire** — vérifie la présence du CLI `nemoclaw` et exécute `nemoclaw status` pour obtenir les informations du sandbox
2. **Détection par conteneur** — analyse les conteneurs Docker en cours d'exécution pour les images `openshell`, `nemoclaw` ou `ghcr.io/nvidia/`, puis lit les sessions via les montages de volumes ou `docker cp`

Les fichiers de session synchronisés depuis les conteneurs NemoClaw sont étiquetés avec les métadonnées `runtime=nemoclaw` et `container_id` dans le tableau de bord cloud, afin de les distinguer facilement des sessions OpenClaw standard.

### Configuration recommandée : démon de synchronisation sur l'HÔTE

Pour une expérience optimale, exécutez le démon de synchronisation de ClawMetry sur la **machine hôte** (et non à l'intérieur du sandbox). Cela évite les restrictions de politique réseau de NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Le démon de synchronisation trouvera automatiquement les sessions dans les conteneurs OpenShell en cours d'exécution.

### Optionnel : nom de sandbox explicite

Si la détection automatique ne fonctionne pas, pointez ClawMetry vers le bon sandbox :

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Exécution à l'intérieur du sandbox (avancé)

Si vous devez exécuter le démon de synchronisation **à l'intérieur** du sandbox OpenShell, ajoutez cette règle de sortie à votre politique réseau NemoClaw pour qu'il puisse atteindre l'API d'ingestion ClawMetry :

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
| `ingest.clawmetry.com` | 443 | HTTPS | Oui (démon de synchronisation vers cloud) |
| `localhost:8900` | 8900 | HTTP | Oui (interface du tableau de bord local) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Pour la découverte de sessions dans les conteneurs |

Le démon de synchronisation n'effectue que des appels HTTPS sortants vers `ingest.clawmetry.com`. Aucun port entrant n'est requis.

---

## Déploiement cloud

Consultez le **[Guide de test cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** pour les tunnels SSH, le reverse proxy et Docker.

## Tests

Ce projet est testé avec BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Télémétrie

ClawMetry envoie un seul ping anonyme de "première utilisation" à
`https://app.clawmetry.com/api/install` la première fois que vous exécutez le
CLI `clawmetry` sur une nouvelle machine. Nous l'utilisons pour compter les installations (la
seule métrique marketing dont nous disposons pour un projet OSS) et pour savoir quels
frameworks d'agents nos utilisateurs ont installés.

**Exactement un POST par installation**, contenant :

| Champ | Exemple | Pourquoi |
|---|---|---|
| `install_id` | UUID aléatoire stocké dans `~/.clawmetry/install_id` | déduplication ; non lié à votre adresse e-mail ou api_key |
| `version` | `0.12.167` | quelles versions sont utilisées |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorités de support des plateformes |
| `python` | `3.11.15` | matrice de support des versions Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | quels agents nous devrions intégrer ensuite |
| `is_ci` / `ci_provider` | `true` / `github_actions` | distinguer les installations humaines du bruit CI |

**Ce que nous n'envoyons PAS** : l'adresse IP (le cloud dérive le code pays côté serveur à partir de la requête, puis supprime l'IP), le nom d'hôte, le nom d'utilisateur, le chemin de l'espace de travail, le contenu des fichiers, votre api_key, votre adresse e-mail, toute information personnelle ou spécifique à l'espace de travail. La charge utile réseau est auditable dans
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Se désabonner** (l'une ou l'autre de ces méthodes le désactive définitivement) :

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un échec réseau ici ne bloque jamais l'exécution de `clawmetry` — le
ping est envoyé sans attente de réponse dans un thread démon avec un délai d'expiration de 3 s.

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
  <sub>Construit par <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Partie de l'écosystème <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
