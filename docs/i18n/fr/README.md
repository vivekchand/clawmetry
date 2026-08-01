<!-- i18n-src:191e9094d7fa -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Regardez votre agent penser.** Observabilité en temps réel pour **14 runtimes d'agents IA** : [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex et 10 autres. Un seul tableau de bord pour toute votre flotte d'agents.

> 🌐 **Lire ceci en :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une seule commande. Zéro configuration. Détecte tout automatiquement.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900** et c'est terminé.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatible avec 14 runtimes d'agents

ClawMetry a démarré comme solution d'observabilité pour OpenClaw, et mesure désormais **toute votre flotte d'agents** dans un seul tableau de bord, en détectant automatiquement chaque runtime sur votre machine :

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw et NemoClaw sont gratuits dans l'application open source ; les autres runtimes se débloquent avec ClawMetry Cloud ou une licence Pro auto-hébergée. Changez de runtime depuis l'en-tête : chaque onglet (coût, tokens, outils, traces) se réajuste alors à ce runtime. Consultez **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** pour connaître la répartition exacte gratuit/payant, la matrice des paliers, le format de `/api/entitlement`, ainsi que la CLI `clawmetry license`.

## Ce que vous obtenez

- **Flow** : diagramme animé en direct montrant le trajet des messages à travers les canaux, le cerveau, les outils, puis retour
- **Overview** : bilans de santé, carte de chaleur d'activité, nombre de sessions, informations sur le modèle
- **Usage** : suivi des tokens et des coûts avec des répartitions quotidiennes/hebdomadaires/mensuelles
- **Sessions** : sessions actives de l'agent avec modèle, tokens, dernière activité
- **Crons** : tâches planifiées avec statut, prochaine exécution, durée
- **Logs** : flux de logs en temps réel avec code couleur
- **Memory** : parcourez SOUL.md, MEMORY.md, AGENTS.md, les notes quotidiennes
- **Transcripts** : interface à bulles de discussion pour lire l'historique des sessions
- **Alerts** : plafonds de budget, déclencheurs de taux d'erreur, détection d'agent hors ligne ; achemine vers Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** : bloque les suppressions destructrices, les force push, les modifications de base de données, sudo, les installations de paquets et les appels réseau derrière une validation en un clic

## Captures d'écran

### 🧠 Brain : flux d'événements de l'agent en direct
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview : utilisation des tokens et résumé de session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow : flux des appels d'outils en temps réel
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens : répartition des coûts par modèle et par session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory : explorateur de fichiers du workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security : posture de sécurité et journal d'audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts : plafonds de budget, déclencheurs de taux d'erreur, webhooks vers Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals : bloque les appels d'outils risqués derrière une validation manuelle ; règles de protection appuyées par des politiques
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blocage avant exécution pour Claude Code** : une seule commande installe un
hook PreToolUse qui met en pause les appels d'outils correspondants *avant* leur exécution et attend
votre décision (un simple tap depuis votre téléphone si les
[notifications push cloud](https://app.clawmetry.com/push) sont activées) :

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Un refus (deny) bloque uniquement cet appel d'outil : l'agent conserve sa session et peut
essayer une autre approche. Approuver depuis votre téléphone saute l'invite de
permission propre à Claude Code (vous avez déjà répondu). Les outils non concernés coûtent environ 40 ms et
retombent dans le flux de permission normal de Claude Code. Vous recevez aussi une notification push sur votre téléphone quand
Claude Code lui-même attend votre réponse (notifications `permission_prompt` /
`idle_prompt`).

## Installation

**Ligne de commande unique (recommandé) :**
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

L'application React v2 se trouve dans `frontend/` et est servie sur `/v2` quand le serveur
Flask est démarré avec v2 activé.

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

Ouvrez `http://localhost:5173/v2/`. Vite redirige les requêtes `/api` vers
`http://localhost:8900`, afin que l'application React puisse communiquer avec le serveur Flask local
sans configuration CORS supplémentaire.

Pour construire le bundle livré avec le paquet Python :

```bash
cd frontend
npm run build
```

Le bundle de production est écrit dans `clawmetry/static/v2/dist/`.

## Compatibilité des runtimes / agents

ClawMetry observe de nombreux runtimes d'agents IA, pas seulement OpenClaw. Chaque runtime autre qu'OpenClaw dispose d'un adaptateur de lecture dédié qui traduit le format natif de ses sessions vers les formats unifiés de ClawMetry ; le daemon les ingère dans le même magasin DuckDB et le même instantané cloud, étiquetés avec le runtime, et l'onglet de relecture de session affiche un **sélecteur de runtime** quand plus d'un est présent. Consultez [`docs/compatibility.md`](docs/compatibility.md) pour la matrice complète et un guide d'ajout de runtimes, ainsi que [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) pour l'introduction à la famille OpenClaw.

Vous utilisez [numbat de Perplexity](https://github.com/perplexityai/numbat), l'outil de sécurité pour agents ? ClawMetry ingère nativement ses résultats et ses décisions d'application ; voir [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Statut | Notes |
|---|---|---|
| **OpenClaw** | Natif | Runtime de référence, détecté automatiquement |
| **PicoClaw** | Adaptateur bêta | JSONL plat `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcriptions, modèle, appels d'outils. |
| **NanoClaw** | Adaptateur bêta | SQLite par session (`data/v2-sessions`). Transcriptions + nombre de messages. |
| **Hermes** | Adaptateur bêta | SQLite `~/.hermes/state.db`. Transcriptions, modèle, tokens/coût. |
| **Claude Code** | Adaptateur bêta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcriptions, modèle, appels d'outils + raisonnement, utilisation des tokens. |
| **Codex** | Adaptateur bêta | Rollout JSONL `~/.codex/sessions/...`. Transcriptions, modèle, appels d'outils, utilisation des tokens. |
| **Cursor** | Adaptateur bêta | SQLite `state.vscdb`. Transcriptions de chat/composer, modèle. |
| **Aider** | Adaptateur bêta | `.aider.chat.history.md` par projet. Transcriptions, modèle, nombre de tokens. |
| **Goose** | Adaptateur bêta | SQLite `~/.local/share/goose`. Transcriptions, modèle, appels d'outils, totaux de tokens. |
| **opencode** | Adaptateur bêta | SQLite `~/.local/share/opencode`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **Qwen Code** | Adaptateur bêta | JSONL `~/.qwen/projects/.../chats`. Transcriptions, modèle, appels d'outils, utilisation des tokens. |
| **Pi** | Adaptateur bêta | JSONL `~/.pi/agent/sessions`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **Deep Agents** | Adaptateur bêta | SQLite `~/.deepagents/.state/sessions.db`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **n8n** | Adaptateur bêta | SQLite `~/.n8n/database.sqlite`. Exécutions de workflows, exécutions de nœuds, prompts de l'AI Agent, modèle + tokens lorsque n8n les enregistre. |
| **Antigravity** | Adaptateur bêta | Brain JSONL sous `~/.gemini/<flavor>/brain/`. Conversations, étapes d'outils, raisonnement, répartition des tokens Gemini par génération + coût, consommation de génération en arrière-plan. |

« Adaptateur bêta » signifie que ClawMetry fournit un lecteur pour le format réel sur disque de ce runtime, chacun construit et vérifié sur une installation réelle sur une machine réelle (voir `tests/fixtures/runtimes/<rt>/`). Les adaptateurs sont en lecture seule ; chacun est transparent sur ce que son runtime stocke réellement (par exemple, PicoClaw/NanoClaw/Cursor n'écrivent pas le coût des tokens sur disque). Lorsque plusieurs runtimes s'exécutent sur un même nœud, le sélecteur de runtime restreint la vue des sessions à un seul pour une analyse approfondie et ciblée.

## Suivre n'importe quel agent SDK : attribution des coûts hors boucle

Tous les runtimes ci-dessus écrivent leurs sessions sur disque. Votre propre **agent de production** (celui que vous avez construit avec l'OpenAI Agents SDK, LangChain, le Vercel AI SDK, LlamaIndex, E2B, ou une simple boucle `httpx`) ne le fait pas. L'intercepteur sans configuration de ClawMetry capture malgré tout ses appels LLM (coût, tokens, latence, erreurs) en patchant dynamiquement `httpx`/`requests` :

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou la variable d'environnement `CLAWMETRY_SOURCE=support-agent`) étiquette chaque appel avec une **source nommée**, de sorte que chaque produit que vous exécutez apparaît comme sa propre ligne de premier ordre, attribuable en coût, dans la carte **🔌 Sources hors boucle** de l'onglet Overview du tableau de bord : appels, fournisseurs, latence, taux d'erreur par agent. Aucune source définie ? Les appels sont quand même suivis ; la carte reste simplement masquée.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

C'est la même couche de données que celle alimentée par les adaptateurs de runtime (DuckDB → instantané cloud), donc les sources hors boucle se synchronisent avec le tableau de bord cloud comme tout le reste, chiffrées de bout en bout.

## OpenTelemetry : neutre vis-à-vis du fournisseur, envoyez vos traces où vous voulez

ClawMetry parle **OpenTelemetry** dans les deux sens, en utilisant les **conventions sémantiques GenAI**, de sorte que les traces de votre agent ne sont jamais enfermées dans un seul outil.

**Exportez** chaque session (appels LLM, outils, sous-agents, tokens, coût) sous forme de spans GenAI OTLP/HTTP vers n'importe quel collecteur (Datadog, Grafana, Honeycomb, ou votre propre OTel Collector) :

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

**Ingestion** : le récepteur OTLP intégré accepte les traces et métriques de n'importe quelle autre source sur `/v1/traces` et `/v1/metrics` (`pip install clawmetry[otel]` pour l'ingestion protobuf).

Vous obtenez le tableau de bord ClawMetry sans configuration et local d'abord, **et** vos données dans n'importe quel backend déjà utilisé par votre équipe : aucun verrouillage, aucun second agent à installer.

## Configuration

La plupart des gens n'ont besoin d'aucune configuration. ClawMetry détecte automatiquement votre workspace, vos logs, vos sessions et vos crons.

Si vous devez personnaliser :

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Toutes les options : `clawmetry --help`

## Canaux pris en charge

ClawMetry affiche l'activité en direct de chaque canal OpenClaw que vous avez configuré. Seuls les canaux réellement configurés dans votre `openclaw.json` apparaissent dans le diagramme Flow : ceux qui ne sont pas configurés sont automatiquement masqués.

Cliquez sur n'importe quel nœud de canal dans Flow pour voir une vue en bulles de discussion en direct avec le nombre de messages entrants/sortants.

| Canal | Statut | Popup en direct | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Complet | ✅ | Messages, statistiques, actualisation toutes les 10s |
| 💬 **iMessage** | ✅ Complet | ✅ | Lit directement `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Complet | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Complet | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Complet | ✅ | Détection de serveur (guild) + canal |
| 🟪 **Slack** | ✅ Complet | ✅ | Détection de workspace + canal |
| 🌐 **Webchat** | ✅ Complet | ✅ | Sessions intégrées de l'interface web |
| 📡 **IRC** | ✅ Complet | ✅ | Interface en bulles façon terminal |
| 🍏 **BlueBubbles** | ✅ Complet | ✅ | iMessage via l'API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Complet | ✅ | Via les webhooks de la Chat API |
| 🟣 **MS Teams** | ✅ Complet | ✅ | Via le plugin bot Teams |
| 🔷 **Mattermost** | ✅ Complet | ✅ | Chat d'équipe auto-hébergé |
| 🟩 **Matrix** | ✅ Complet | ✅ | Décentralisé, prise en charge E2EE |
| 🟢 **LINE** | ✅ Complet | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Complet | ✅ | Messages directs NIP-04 décentralisés |
| 🟣 **Twitch** | ✅ Complet | ✅ | Chat via connexion IRC |
| 🔷 **Feishu/Lark** | ✅ Complet | ✅ | Abonnement aux événements via WebSocket |
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

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Exemple de Docker Compose :**

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

> **Remarque :** Lors de l'exécution dans Docker, montez les répertoires de données et de logs de votre agent (par exemple `~/.openclaw`, `~/.claude`, `~/.codex`) afin que ClawMetry puisse détecter automatiquement votre configuration.

## Prérequis

- Python 3.8+
- Flask (installé automatiquement via pip)
- Un runtime d'agent IA sur la même machine : OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ou Antigravity (ou des volumes montés pour Docker)
- Linux ou macOS

## Prise en charge de NemoClaw / OpenShell

ClawMetry détecte automatiquement [NemoClaw](https://github.com/NVIDIA/NemoClaw), l'enveloppe de sécurité d'entreprise de NVIDIA pour OpenClaw, qui exécute les agents à l'intérieur de conteneurs OpenShell en bac à sable (sandbox).

Aucune configuration supplémentaire n'est nécessaire dans la plupart des cas. Le daemon de synchronisation découvre automatiquement les fichiers de session, qu'ils se trouvent dans `~/.openclaw/` sur l'hôte ou à l'intérieur d'un conteneur OpenShell.

### Comment ça fonctionne

ClawMetry détecte NemoClaw de deux manières :

1. **Détection du binaire** : vérifie la présence de la CLI `nemoclaw` et exécute `nemoclaw status` pour obtenir les informations du bac à sable
2. **Détection de conteneur** : analyse les conteneurs Docker en cours d'exécution à la recherche d'images `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, puis lit les sessions via des montages de volumes ou `docker cp`

Les fichiers de session synchronisés depuis des conteneurs NemoClaw sont étiquetés avec les métadonnées `runtime=nemoclaw` et `container_id` dans le tableau de bord cloud, afin que vous puissiez les distinguer des sessions OpenClaw standard en un coup d'œil.

### Configuration recommandée : daemon de synchronisation sur l'HÔTE

Pour une expérience optimale, exécutez le daemon de synchronisation de ClawMetry sur la **machine hôte** (pas à l'intérieur du bac à sable). Cela évite les restrictions de politique réseau de NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Le daemon de synchronisation trouvera automatiquement les sessions à l'intérieur de tout conteneur OpenShell en cours d'exécution.

### Optionnel : nom de bac à sable explicite

Si la détection automatique ne fonctionne pas, indiquez à ClawMetry le bon bac à sable :

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

Appliquez-la avec :

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Ports et points de terminaison

| Point de terminaison | Port | Protocole | Requis |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oui (daemon de synchronisation → cloud) |
| `localhost:8900` | 8900 | HTTP | Oui (interface locale du tableau de bord) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Pour la découverte des sessions en conteneur |

Le daemon de synchronisation n'effectue que des appels HTTPS sortants vers `ingest.clawmetry.com`. Aucun port entrant n'est requis.

---

## Déploiement Cloud

Consultez le **[Guide de test Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** pour les tunnels SSH, le proxy inverse et Docker.

## Tests

Ce projet est testé avec BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Télémétrie

ClawMetry envoie des pings anonymes du cycle de vie de l'installation vers
`https://app.clawmetry.com/api/install` : un ping `install` la première
fois que vous exécutez la CLI `clawmetry` sur une nouvelle machine, un ping `update`
lors de la première exécution après une mise à jour vers une nouvelle version, et un ping `onboarded`
lorsque vous terminez le choix d'intégration dans le tableau de bord. Nous utilisons ceci
pour compter les installations réelles (les chiffres bruts de téléchargement PyPI sont composés à ~98 % de miroirs, de CI
et de retéléchargements liés à la mise à jour automatique) et pour savoir quels frameworks d'agents et
quelles versions sont réellement utilisés.

**Au maximum un POST par événement de cycle de vie et par version**, contenant :

| Champ | Exemple | Pourquoi |
|---|---|---|
| `install_id` | UUID aléatoire stocké dans `~/.clawmetry/install_id` | déduplication ; anonyme jusqu'à ce que vous connectiez explicitement la synchronisation Cloud (le heartbeat authentifié du daemon le transporte alors, reliant cette installation à votre compte) |
| `event` | `install` / `update` / `onboarded` | nouvelle installation ou mise à jour d'une installation existante |
| `version` | `0.12.167` | quelles versions sont utilisées en pratique |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorités de prise en charge des plateformes |
| `python` | `3.11.15` | matrice de prise en charge des versions de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | quels agents nous devrions intégrer ensuite |
| `is_ci` / `ci_provider` | `true` / `github_actions` | distinguer les installations humaines du bruit lié au CI |

**Ce que nous n'envoyons PAS** : l'IP (le cloud dérive le code pays côté
serveur à partir de la requête, puis supprime l'IP), le nom d'hôte, le nom d'utilisateur, le chemin
du workspace, le contenu des fichiers, votre api_key, votre email, ni aucune donnée PII ou
spécifique au workspace. La charge utile transmise est auditable dans
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Se désinscrire** (n'importe laquelle de ces options la désactive définitivement) :

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un échec réseau ici ne bloque jamais l'exécution de `clawmetry` : le
ping est envoyé sans attendre de réponse (fire-and-forget) sur un thread du daemon avec un délai d'expiration de 3 s.

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
  <strong>🦞 Regardez votre agent penser</strong><br>
  <sub>Créé par <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Fait partie de l'écosystème <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
