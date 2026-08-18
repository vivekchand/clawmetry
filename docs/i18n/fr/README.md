<!-- i18n-src:c422fb7dd0da -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Voyez votre agent réfléchir.** Observabilité en temps réel pour **22 runtimes d'agents IA** : [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex et 18 autres. Un seul tableau de bord pour toute votre flotte d'agents.

> 🌐 **Lisez ceci en :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une commande. Aucune configuration. Tout est détecté automatiquement.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900** et c'est terminé.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatible avec 22 runtimes d'agents

ClawMetry a démarré comme un outil d'observabilité pour OpenClaw, et mesure désormais **toute votre flotte d'agents** dans un seul tableau de bord, en détectant automatiquement chaque runtime présent sur votre machine :

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw et NemoClaw sont gratuits dans l'application open-source ; les autres runtimes s'activent avec ClawMetry Cloud ou une licence Pro auto-hébergée. Changez de runtime depuis l'en-tête et chaque onglet, coût, tokens, outils, traces, se recalibre sur ce runtime. Consultez **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** pour la répartition exacte gratuit/payant, la matrice des niveaux, la forme de `/api/entitlement`, et la CLI `clawmetry license`.

## Ce que vous obtenez

- **Flow** — Diagramme animé en direct montrant les messages circuler à travers les canaux, le cerveau, les outils, et retour
- **Overview** — Contrôles de santé, carte de chaleur d'activité, nombre de sessions, informations sur le modèle
- **Usage** — Suivi des tokens et des coûts avec répartitions quotidiennes/hebdomadaires/mensuelles
- **Sessions** — Sessions d'agent actives avec modèle, tokens, dernière activité
- **Crons** — Tâches planifiées avec statut, prochaine exécution, durée
- **Logs** — Diffusion de journaux en temps réel avec code couleur
- **Memory** — Parcourir SOUL.md, MEMORY.md, AGENTS.md, notes quotidiennes
- **Transcripts** — Interface en bulles de discussion pour lire l'historique des sessions
- **Alerts** — Plafonds budgétaires, déclencheurs de taux d'erreur, détection d'agent hors ligne ; routage vers Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloquer les suppressions destructrices, les force push, les mutations de base de données, sudo, les installations de paquets, les appels réseau derrière une validation en un clic

## Captures d'écran

### 🧠 Brain — Flux d'événements de l'agent en direct
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Usage des tokens et résumé de session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Flux en temps réel des appels d'outils
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Répartition des coûts par modèle et session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navigateur de fichiers de l'espace de travail
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Posture et journal d'audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Plafonds budgétaires, déclencheurs de taux d'erreur, webhooks vers Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloquer les appels d'outils risqués derrière une validation manuelle ; règles de protection basées sur des politiques
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blocage avant exécution pour Claude Code** — une commande installe un
hook PreToolUse qui met en pause les appels d'outils correspondants *avant* qu'ils ne s'exécutent et attend
votre décision (un tap depuis votre téléphone avec les
[notifications push cloud](https://app.clawmetry.com/push) activées) :

```bash
clawmetry hooks install     # écrit ~/.claude/settings.json (idempotent)
clawmetry hooks status      # ce qui est câblé + combien de politiques sont actives
clawmetry hooks uninstall   # supprime uniquement les entrées de ClawMetry
```

Un refus bloque uniquement cet appel d'outil précis, l'agent conserve sa session et peut
essayer une autre approche. Approuver depuis votre téléphone saute l'invite de
permission propre à Claude Code (vous avez déjà répondu). Les outils non correspondants coûtent environ 40 ms et
retombent dans le flux de permission normal de Claude Code. Vous recevez aussi une notification push sur votre téléphone quand Claude Code lui-même
attend une réponse de votre part (notifications `permission_prompt` /
`idle_prompt`).

## Installation

**En une ligne (recommandé) :**
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

L'application React v2 se trouve dans `frontend/` et est servie sur `/v2` lorsque le
serveur Flask est démarré avec v2 activé.

Utilisez deux terminaux pendant le développement :

```bash
# Terminal 1 : API/serveur Flask sur :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2 : serveur de développement Vite sur :5173
cd frontend
nvm use
npm ci
npm run dev
```

Ouvrez `http://localhost:5173/v2/`. Vite fait suivre les requêtes `/api` vers
`http://localhost:8900`, de sorte que l'application React puisse communiquer avec le serveur Flask local
sans configuration CORS supplémentaire.

Pour construire le bundle livré avec le paquet Python :

```bash
cd frontend
npm run build
```

Le bundle de production est écrit dans `clawmetry/static/v2/dist/`.

## Compatibilité runtime / agent

ClawMetry observe de nombreux runtimes d'agents IA, pas seulement OpenClaw. Chaque runtime autre qu'OpenClaw dispose d'un adaptateur de lecture dédié qui traduit son format de session natif dans les formes unifiées de ClawMetry ; le démon les ingère dans le même magasin DuckDB + snapshot cloud, étiquetés avec le runtime, et l'onglet de relecture de session affiche un **sélecteur de runtime** lorsque plusieurs sont présents. Voir [`docs/compatibility.md`](docs/compatibility.md) pour la matrice complète + un guide d'ajout de runtimes, et [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) pour l'introduction à la famille OpenClaw.

Vous utilisez [numbat de Perplexity](https://github.com/perplexityai/numbat), l'outil de sécurité pour agents ? ClawMetry ingère ses résultats et décisions d'application dès la sortie de la boîte, voir [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Statut | Notes |
|---|---|---|
| **OpenClaw** | Natif | Runtime de référence, détecté automatiquement |
| **PicoClaw** | Adaptateur bêta | JSONL plat `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcriptions, modèle, appels d'outils. |
| **NanoClaw** | Adaptateur bêta | SQLite par session (`data/v2-sessions`). Transcriptions + nombre de messages. |
| **Hermes** | Adaptateur bêta | SQLite `~/.hermes/state.db`. Transcriptions, modèle, tokens/coût. |
| **Claude Code** | Adaptateur bêta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcriptions, modèle, appels d'outils + réflexion, usage de tokens. |
| **Codex** | Adaptateur bêta | Rollout JSONL `~/.codex/sessions/...`. Transcriptions, modèle, appels d'outils, usage de tokens. |
| **Cursor** | Adaptateur bêta | SQLite `state.vscdb`. Transcriptions chat/composer, modèle. |
| **Aider** | Adaptateur bêta | `.aider.chat.history.md` par projet. Transcriptions, modèle, comptage de tokens. |
| **Goose** | Adaptateur bêta | SQLite `~/.local/share/goose`. Transcriptions, modèle, appels d'outils, totaux de tokens. |
| **opencode** | Adaptateur bêta | SQLite `~/.local/share/opencode`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **Qwen Code** | Adaptateur bêta | JSONL `~/.qwen/projects/.../chats`. Transcriptions, modèle, appels d'outils, usage de tokens. |
| **Pi** | Adaptateur bêta | JSONL `~/.pi/agent/sessions`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **Deep Agents** | Adaptateur bêta | SQLite `~/.deepagents/.state/sessions.db`. Transcriptions, modèle, appels d'outils, tokens + coût. |
| **n8n** | Adaptateur bêta | SQLite `~/.n8n/database.sqlite`. Exécutions de workflow, exécutions de nœuds, prompts AI Agent, modèle + tokens lorsque n8n les enregistre. |
| **Antigravity** | Adaptateur bêta | Brain JSONL sous `~/.gemini/<flavor>/brain/`. Conversations, étapes d'outils, réflexion, répartition des tokens Gemini par génération + coût, consommation de génération en arrière-plan. |
| **GitHub Copilot** | Adaptateur bêta | `events.jsonl` de Copilot CLI sous `~/.copilot/session-state/` + le registre d'usage par appel `session-store.db`. Conversations, appels d'outils, routage de modèle, répartition des tokens tenant compte du cache, coût en crédits IA facturés par le fournisseur. |
| **Grok** | Adaptateur bêta | xAI Grok Build CLI (binaire Rust sous `~/.grok/bin/grok`) : journal d'événements global `~/.grok/logs/unified.jsonl` + par session `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Conversations, répartition des tokens par tour, routage de modèle, et la charge utile du dépôt sortante de la CLI mise en attente sous `~/.grok/upload_queue/` pour que vous puissiez voir ce qui a quitté votre machine. |

« Adaptateur bêta » signifie que ClawMetry fournit un lecteur pour le format sur disque réel de ce runtime, chacun construit et vérifié sur une installation réelle sur une machine réelle (voir `tests/fixtures/runtimes/<rt>/`). Les adaptateurs sont en lecture seule ; chacun est transparent sur ce que son runtime stocke réellement (par ex. PicoClaw/NanoClaw/Cursor n'écrivent pas le coût des tokens sur disque). Lorsque plusieurs runtimes s'exécutent sur un même nœud, le sélecteur de runtime limite la vue des sessions à un seul pour une analyse approfondie propre.

## Suivre n'importe quel agent SDK — attribution des coûts hors boucle

Les runtimes ci-dessus écrivent tous les sessions sur disque. Votre propre **agent de production**, celui que vous avez construit sur le SDK OpenAI Agents, LangChain, le SDK Vercel AI, LlamaIndex, E2B, ou une simple boucle `httpx`, ne le fait pas. L'intercepteur zéro-configuration de ClawMetry capture quand même ses appels LLM (coût, tokens, latence, erreurs) en patchant dynamiquement `httpx`/`requests` :

```python
import clawmetry.track            # active l'intercepteur
clawmetry.track.set_source("support-agent")   # nomme ce produit

# ...votre agent s'exécute normalement ; chaque appel LLM est désormais suivi + attribué.
```

`set_source()` (ou la variable d'environnement `CLAWMETRY_SOURCE=support-agent`) étiquette chaque appel avec une **source nommée**, de sorte que chaque produit que vous exécutez apparaît comme sa propre ligne de premier ordre, attribuable en coût, dans la carte **🔌 Sources hors boucle** du tableau de bord sur Overview, appels, fournisseurs, latence, taux d'erreur par agent. Aucune source définie ? Les appels sont quand même suivis ; la carte reste simplement cachée.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

C'est la même couche de données que celle alimentée par les adaptateurs de runtime (DuckDB → snapshot cloud), donc les sources hors boucle se synchronisent avec le tableau de bord cloud comme tout le reste, chiffré de bout en bout.

## OpenTelemetry — neutre vis-à-vis des fournisseurs, envoyez vos traces n'importe où

ClawMetry parle **OpenTelemetry** dans les deux sens, en utilisant les **conventions sémantiques GenAI**, de sorte que les traces de votre agent ne sont jamais enfermées dans un seul outil.

**Exportez** chaque session, appels LLM, outils, sous-agents, tokens, coût, sous forme de spans GenAI OTLP/HTTP vers n'importe quel collecteur (Datadog, Grafana, Honeycomb, ou votre propre collecteur OTel) :

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# de manière équivalente :
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Les en-têtes d'authentification et l'intervalle d'interrogation sont des variables d'environnement optionnelles :

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # en-têtes HTTP supplémentaires
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # secondes (par défaut 60)
```

**Ingérez** — le récepteur OTLP intégré accepte les traces, journaux et métriques de n'importe quoi d'autre sur `/v1/traces`, `/v1/logs`, et `/v1/metrics`. Pointez n'importe quelle application instrumentée avec OpenTelemetry vers lui :

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

L'ingestion de traces et journaux OTLP/JSON fonctionne avec un simple `pip install clawmetry`, sans extras. L'ingestion Protobuf (et les métriques OTLP/JSON) nécessite `pip install clawmetry[otel]`. Une application qui définit son propre `service.name` apparaît comme son propre agent dans le sélecteur de runtime, avec son coût et ses tokens.

Vous obtenez le tableau de bord ClawMetry zéro-configuration, local d'abord, **et** vos données dans le backend que votre équipe utilise déjà, sans enfermement propriétaire, sans second agent à installer.

## Configuration

La plupart des gens n'ont besoin d'aucune configuration. ClawMetry détecte automatiquement votre espace de travail, vos journaux, vos sessions et vos crons.

Si vous avez besoin de personnaliser :

```bash
clawmetry --port 9000              # Port personnalisé (par défaut : 8900)
clawmetry --host 127.0.0.1         # Se lier uniquement à localhost
clawmetry --workspace ~/mybot      # Chemin d'espace de travail personnalisé
clawmetry --name "Alice"           # Votre nom dans la visualisation Flow
```

Toutes les options : `clawmetry --help`

## Canaux pris en charge

ClawMetry affiche l'activité en direct pour chaque canal OpenClaw que vous avez configuré. Seuls les canaux réellement configurés dans votre `openclaw.json` apparaissent dans le diagramme Flow, les canaux non configurés sont automatiquement masqués.

Cliquez sur n'importe quel nœud de canal dans le Flow pour voir une vue en bulles de discussion en direct avec le nombre de messages entrants/sortants.

| Canal | Statut | Popup en direct | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Complet | ✅ | Messages, statistiques, rafraîchissement toutes les 10 s |
| 💬 **iMessage** | ✅ Complet | ✅ | Lit directement `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Complet | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Complet | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Complet | ✅ | Détection de guilde + canal |
| 🟪 **Slack** | ✅ Complet | ✅ | Détection d'espace de travail + canal |
| 🌐 **Webchat** | ✅ Complet | ✅ | Sessions d'interface web intégrée |
| 📡 **IRC** | ✅ Complet | ✅ | Interface en bulles de style terminal |
| 🍏 **BlueBubbles** | ✅ Complet | ✅ | iMessage via l'API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Complet | ✅ | Via les webhooks de l'API Chat |
| 🟣 **MS Teams** | ✅ Complet | ✅ | Via le plugin bot Teams |
| 🔷 **Mattermost** | ✅ Complet | ✅ | Chat d'équipe auto-hébergé |
| 🟩 **Matrix** | ✅ Complet | ✅ | Décentralisé, support E2EE |
| 🟢 **LINE** | ✅ Complet | ✅ | API de messagerie LINE |
| ⚡ **Nostr** | ✅ Complet | ✅ | DM décentralisés NIP-04 |
| 🟣 **Twitch** | ✅ Complet | ✅ | Chat via connexion IRC |
| 🔷 **Feishu/Lark** | ✅ Complet | ✅ | Abonnement aux événements WebSocket |
| 🔵 **Zalo** | ✅ Complet | ✅ | API Zalo Bot |

> **Détection automatique :** ClawMetry lit votre `~/.openclaw/openclaw.json` et n'affiche que les canaux que vous avez réellement configurés. Aucune configuration manuelle requise.

## Déploiement Docker

Vous voulez exécuter ClawMetry dans un conteneur ? Aucun problème ! 🐳

**Démarrage rapide avec Docker :**

```bash
# Construire l'image
docker build -t clawmetry .

# Exécuter avec les paramètres par défaut
docker run -p 8900:8900 clawmetry

# Ou monter le répertoire de données de votre agent (illustré : le ~/.openclaw d'OpenClaw)
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

> **Remarque :** Lors de l'exécution dans Docker, montez les répertoires de données + journaux de votre agent (par ex. `~/.openclaw`, `~/.claude`, `~/.codex`) afin que ClawMetry puisse détecter automatiquement votre configuration.

## Prérequis

- Python 3.8+
- Flask (installé automatiquement via pip)
- Un runtime d'agent IA sur la même machine : OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, ou QM (ou des volumes montés pour Docker)
- Linux ou macOS

## Support NemoClaw / OpenShell

ClawMetry détecte automatiquement [NemoClaw](https://github.com/NVIDIA/NemoClaw), l'enveloppe de sécurité d'entreprise de NVIDIA pour OpenClaw qui exécute les agents dans des conteneurs OpenShell sandboxés.

Aucune configuration supplémentaire n'est nécessaire dans la plupart des cas. Le démon de synchronisation découvre automatiquement les fichiers de session qu'ils se trouvent sur `~/.openclaw/` sur l'hôte ou à l'intérieur d'un conteneur OpenShell.

### Fonctionnement

ClawMetry détecte NemoClaw de deux façons :

1. **Détection de binaire** — vérifie la présence de la CLI `nemoclaw` et exécute `nemoclaw status` pour obtenir les informations sur le sandbox
2. **Détection de conteneur** — scanne les conteneurs Docker en cours d'exécution à la recherche des images `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, puis lit les sessions via des montages de volumes ou `docker cp`

Les fichiers de session synchronisés depuis les conteneurs NemoClaw sont étiquetés avec `runtime=nemoclaw` et les métadonnées `container_id` dans le tableau de bord cloud, afin que vous puissiez les distinguer des sessions OpenClaw standard d'un coup d'œil.

### Configuration recommandée : démon de synchronisation sur l'HÔTE

Pour la meilleure expérience, exécutez le démon de synchronisation de ClawMetry sur la **machine hôte** (pas à l'intérieur du sandbox). Cela évite les restrictions de politique réseau de NemoClaw.

```bash
# Sur l'hôte (en dehors du sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Le démon de synchronisation trouvera automatiquement les sessions à l'intérieur de tout conteneur OpenShell en cours d'exécution.

### Optionnel : nom de sandbox explicite

Si la détection automatique ne fonctionne pas, indiquez à ClawMetry le bon sandbox :

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Exécution à l'intérieur du sandbox (avancé)

Si vous devez exécuter le démon de synchronisation **à l'intérieur** du sandbox OpenShell, ajoutez cette règle de sortie à votre politique réseau NemoClaw afin qu'il puisse atteindre l'API d'ingestion de ClawMetry :

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
| `ingest.clawmetry.com` | 443 | HTTPS | Oui (démon de synchronisation → cloud) |
| `localhost:8900` | 8900 | HTTP | Oui (interface du tableau de bord local) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Pour la découverte de session dans les conteneurs |

Le démon de synchronisation effectue uniquement des appels HTTPS sortants vers `ingest.clawmetry.com`. Aucun port entrant n'est requis.

---

## Déploiement Cloud

Consultez le **[Guide de test Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** pour les tunnels SSH, le proxy inverse, et Docker.

## Tests

Ce projet est testé avec BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Télémétrie

ClawMetry envoie des pings anonymes de cycle de vie d'installation à
`https://app.clawmetry.com/api/install` : un ping `install` la première
fois que vous exécutez la CLI `clawmetry` sur une nouvelle machine, un ping `update`
lors de la première exécution après une mise à niveau vers une nouvelle version, et un ping `onboarded`
lorsque vous terminez le choix d'intégration dans le tableau de bord. Nous utilisons cela
pour compter les installations réelles (les chiffres bruts de téléchargement PyPI sont environ 98 % des miroirs, de la CI,
et des re-téléchargements de mise à jour automatique) et pour savoir quels frameworks d'agents et
quelles versions sont réellement utilisés.

**Au plus un POST par événement de cycle de vie par version**, contenant :

| Champ | Exemple | Pourquoi |
|---|---|---|
| `install_id` | UUID aléatoire stocké dans `~/.clawmetry/install_id` | déduplication ; anonyme jusqu'à ce que vous connectiez explicitement la synchronisation Cloud (le battement de cœur authentifié du démon transporte alors cet identifiant, reliant cette installation à votre compte) |
| `event` | `install` / `update` / `onboarded` | nouvelle installation vs mise à niveau d'une existante |
| `version` | `0.12.167` | quelles versions sont en circulation |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorités de support de plateforme |
| `python` | `3.11.15` | matrice de support des versions Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | quels agents nous devrions intégrer ensuite |
| `is_ci` / `ci_provider` | `true` / `github_actions` | séparer les installations humaines du bruit CI |

**Ce que nous n'envoyons PAS** : IP (le cloud dérive le code pays côté serveur
à partir de la requête, puis rejette l'IP), le nom d'hôte, le nom d'utilisateur, le chemin de l'espace de travail,
le contenu des fichiers, votre api_key, votre email, tout élément identifiable ou
spécifique à l'espace de travail. La charge utile réseau peut être auditée dans
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Se désinscrire** (l'une de ces méthodes la désactive de manière permanente) :

```bash
export CLAWMETRY_NO_TELEMETRY=1                # par shell
export DO_NOT_TRACK=1                          # norme W3C inter-outils
touch ~/.clawmetry/notelemetry                 # marqueur de fichier persistant
```

Un échec réseau ici ne bloque jamais l'exécution de `clawmetry`, le
ping est envoyé sans attente de réponse sur un thread démon avec un délai d'expiration de 3 s.

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
  <sub>Créé par <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Fait partie de l'écosystème <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
