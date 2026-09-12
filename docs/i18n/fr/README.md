<!-- i18n-src:12b97259721e -->
> Français translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Un agent peut effectuer une centaine d'appels d'outils sans faire de progrès.** ClawMetry
lit les fichiers de session que vos agents de codage écrivent déjà, et regroupe la chronologie,
les appels d'outils et les données de tokens et de coûts exposées par le runtime dans une seule
vue, afin que vous puissiez distinguer une longue exécution qui progresse de celle qui est bloquée.

Compatible avec **32 runtimes d'agents IA** — Claude Code, OpenAI Codex, Hermes, OpenClaw et 28 autres. Un seul tableau de bord pour toute votre flotte d'agents. ([la liste complète](SUPPORTED_RUNTIMES.txt), générée à partir du catalogue.)

> 🌐 **Lire ceci en :** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [plus →](docs/i18n/)

Une seule commande. Zéro configuration. Détecte tout automatiquement.

```bash
pip install clawmetry && clawmetry
```

S'ouvre sur **http://localhost:8900**. Zéro configuration : il trouve les runtimes d'agents
que vous avez déjà, les lit en lecture seule, et ne change rien à leur fonctionnement.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Avant d'installer

| | |
|---|---|
| **Ce que ça fait** | Lit les fichiers de session et les journaux que vos agents écrivent déjà. Pas de SDK, pas de changement de code, pas d'instrumentation dans votre application. |
| **Ce que vous voyez** | Chronologie des sessions, relecture outil par outil, répartition des tokens et des coûts, et signaux de trajectoire (boucles, échecs répétés) — par runtime. |
| **Ce qui est gratuit** | `pip install clawmetry` lit **OpenClaw, NVIDIA NemoClaw et Goose** sans compte, sans clé et sans appel réseau. Les 29 autres — Claude Code, Codex, Cursor et le reste — sont lus par le compagnon à code source fermé `clawmetry-pro`, disponible avec l'essai de 7 jours ou un abonnement — voir [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) pour la répartition exacte. |
| **Comment commencer** | `pip install clawmetry && clawmetry`, puis ouvrez localhost:8900. Pas encore d'agents sur cette machine ? `clawmetry --sample` s'ouvre sur trois sessions synthétiques étiquetées. |
| **Ce qui quitte votre machine** | Aucune donnée de session, sauf si vous exécutez `clawmetry connect`. Deux choses s'exécutent par défaut, toutes deux désactivables et ne transportant aucun contenu de session : un ping d'installation anonyme et une vérification de version PyPI. Chaque destination est inventoriée dans [docs/EGRESS.md](docs/EGRESS.md), reconstituée à partir d'une capture réseau plutôt que d'une lecture de commentaires. |

Deux limites à connaître avant de juger le résultat : les runtimes exposent des données très
différentes (certains ne publient aucun coût du tout — [la matrice](docs/compatibility.md)
indique lesquels, par runtime), et observer une action n'est pas la même chose que pouvoir
la bloquer ([quels contrôles sont réels, par runtime](docs/APPROVALS.md)).


## Compatible avec 32 runtimes d'agents

**Gratuit dans l'application open source :** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sur un plan payant :** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Chaque runtime bénéficie du même tableau de bord. Exécutez-en plusieurs à la fois et le
sélecteur d'en-tête recentre chaque onglet sur l'un d'eux.

Vous avez construit votre propre agent sur un SDK plutôt ? L'intercepteur suit aussi ses
appels LLM. Voir [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ce que vous obtenez

- **Sessions et transcriptions** : ce que chaque agent a fait, tour par tour, avec relecture
- **Coût et tokens** : par runtime, modèle, session et jour, avec signalement des anomalies
- **Flow** : diagramme en direct des messages circulant entre les canaux, les modèles et les outils
- **Brain** : le flux d'événements de raisonnement et d'appels d'outils en temps réel
- **Débordement de contexte** : utilisation de la fenêtre dimensionnée par fournisseur, compaction vs débordement forcé, plus une carte par runtime de ce que nous *ne pouvons pas* voir ([comment](docs/CONTEXT_BLOWOUT.md))
- **Mémoire et compétences** : les fichiers et compétences réellement chargés par chaque runtime
- **Santé et journaux** : disque, mémoire, taux d'erreurs, limites de débit, flux de journaux en direct
- **Alertes** : plafonds budgétaires, pics d'erreurs, agent hors ligne, routés vers Slack, Discord, PagerDuty, Telegram, Email
- **Approbations** : mettre en pause les appels d'outils risqués *avant* leur exécution et approuver depuis votre téléphone ([comment](docs/APPROVALS.md))

## Débordement de contexte, et le coût de la surveillance

Deux questions qui méritent une réponse avant de faire confiance à un outil de comparaison d'agents.

**Comment gère-t-il le débordement de fenêtre de contexte entre les runtimes ?**

Un pourcentage d'utilisation n'est honnête que si son dénominateur l'est aussi. ClawMetry
dimensionne la fenêtre par fournisseur à partir d'[une table que vous pouvez lire et
proposer en PR](clawmetry/context_windows.py), couvrant Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama et GLM. Il ne mesure pas les 32 runtimes avec la règle
d'un seul fournisseur. C'est important : un tour de 300K sur GPT-5, évalué avec la règle des
200K d'Anthropic, affiche ">100%, débordé" alors qu'il est en réalité à 75% des 400K de GPT-5.
La même règle masque un tour DeepSeek de 130K, réellement en débordement, en un confortable 65%.

Chaque fenêtre est livrée avec sa provenance : `model_table`, `explicit_marker`,
`observed_floor`, ou un honnête `default` lorsque nous ne connaissons pas le modèle. Une
jauge construite sur une supposition ne s'affiche jamais avec la même autorité qu'une jauge
construite sur une recherche fiable.

ClawMetry ne peut voir les événements de compaction que sur certains runtimes. Ainsi,
`GET /api/context-coverage` indique, par runtime, si un zéro signifie **"s'est déroulé
proprement" ou "nous sommes aveugles"**. Un `0` qui signifie réellement aveugle le dit.
[Détails complets](docs/CONTEXT_BLOWOUT.md)

**Quel est le coût de l'instrumentation ?**

| Chemin | Ajouté à votre agent | Par défaut ? |
|---|---|---|
| Suivi des fichiers de session (les 32 runtimes) | **0**. Processus séparé, aucun code ClawMetry dans votre agent | activé |
| Intercepteur HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** par appel LLM, soit 0,009% d'un appel de 5s | désactivé |
| Passerelle de hook pré-outil (cache chaud) | **+44 ms** par appel d'outil filtré, au-delà d'un plancher interpréteur de 36 ms | désactivé |
| Proxy d'application des règles | **+9,7 ms** par appel LLM | désactivé |

Coût pour l'hôte du daemon : **2 762 événements/s** en ingestion, **710 octets/événement**
sur disque (67,7 Mo pour 100 000 événements), et **~12% d'un cœur** en régime soutenu sur
une installation chargée. Ce dernier chiffre dépasse notre propre budget affiché de 5 à 10%,
il est donc publié comme un bug à corriger plutôt qu'omis de la page.

Mesuré sur un Apple M2 Pro avec `benchmarks/overhead.py`. Le harnais exécute chaque condition
dans un processus séparé, alterne leur ordre, et **refuse d'afficher un chiffre lorsque les
séries se contredisent sur son signe**. Exécutez-le sur votre propre machine en une minute :

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Chaque chemin est mesuré, y compris les passerelles de hook et le proxy d'application des
règles, et le harnais s'exécute sur Linux, macOS et Windows en CI. Deux résultats à connaître :
le proxy coûte environ sept fois plus cher sur Windows que sur Linux, et le daemon soutient
actuellement environ 12% d'un cœur, au-delà de notre propre budget de 5 à 10%. Le JSON brut,
la méthode, et ce qui reste non mesuré sont dans [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Tarification

| Plan | Ce qui est couvert | Prix |
|---|---|---|
| **Gratuit** | OpenClaw + NVIDIA NemoClaw + Goose, tableau de bord complet, local uniquement | 0 $ |
| **Starter** | Tous les autres runtimes ci-dessus, vue de flotte, synchronisation cloud | 9 $ par nœud / mois |
| **Pro** | Starter + contrôle et évaluation : approbations, politiques de risque d'outils, évaluations, détection d'anomalies, optimiseur de coûts, export OTel, journal d'audit inviolable | 19 $ par nœud / mois |

Les plans annuels, Entreprise et les chiffres actuels se trouvent sur
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Les clés de licence auto-hébergées
fonctionnent sans le cloud (`clawmetry license`). La répartition exacte gratuit/payant est
dans [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Vos données restent sur votre machine

ClawMetry lit les fichiers de session et journaux locaux. **Aucune donnée de session ne quitte
votre machine sauf si vous exécutez `clawmetry connect`** — ni invites, ni réponses, ni
arguments d'outils, ni contenu de fichiers, ni lignes de journal. Lorsque vous vous connectez
effectivement, l'instantané est chiffré de bout en bout avec une clé qui ne quitte jamais votre
machine, et déchiffré dans votre navigateur. Si un nœud n'a pas de clé, le téléversement est
ignoré plutôt qu'envoyé en clair, et aucune réponse serveur ne peut désactiver cela.

Deux choses s'exécutent par défaut avant que vous ne vous connectiez, toutes deux désactivables
et ne transportant aucune donnée de session : un ping d'installation anonyme et une vérification
de version par rapport à PyPI. Une installation par défaut recherche également votre IP publique
une fois pour une ligne de bannière de démarrage. Chaque destination, ce qu'elle transporte et
comment la désactiver est listé dans [docs/EGRESS.md](docs/EGRESS.md) ; les installations
auto-hébergées, redirigées et isolées du réseau n'effectuent aucun appel sortant discrétionnaire.

Le déchiffrement se fait dans votre navigateur, avec du code que nous vous servons. C'était
autrefois une promesse ; c'est désormais quelque chose que vous pouvez vérifier. Chaque ligne
qui touche votre clé se trouve dans un seul fichier lisible, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
livré dans le wheel et servi tel quel, épinglé avec un hash d'intégrité des sous-ressources.
Pour confirmer que le navigateur exécute ce que nous avons publié :

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ce que cela ne prouve pas : nous servons la page qui charge le fichier, nous pourrions donc
servir une page différente. Les hashs d'intégrité vous protègent d'un CDN compromis, pas de
l'éditeur. Ce que vous y gagnez, c'est que toute substitution doit être délibérée, visible dans
le code source de la page, et différente d'un artefact sur PyPI que n'importe qui peut récupérer.
L'auto-hébergement ou le maintien en local uniquement élimine entièrement cette dépendance.

## Installation

```bash
pip install clawmetry     # puis : clawmetry
```

Ou la commande en une ligne : `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Nécessite Python 3.8+ sur macOS, Linux ou Windows, et au moins un runtime d'agent sur la
même machine. Instructions Docker : [docs/DOCKER.md](docs/DOCKER.md).

Ou laissez l'agent l'installer pour vous. La compétence [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
apprend à Claude Code, Codex, Cursor, Gemini CLI, Copilot ou OpenCode à installer ClawMetry,
à rapporter ce que font les agents sur la machine et ce qu'ils dépensent, à arrêter une session
sur demande, et à retenir les appels d'outils risqués pour approbation :

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentation

| | |
|---|---|
| [Compatibilité des runtimes](docs/compatibility.md) | Ce que chaque adaptateur lit, et comment ajouter un runtime |
| [Débordement de contexte](docs/CONTEXT_BLOWOUT.md) | Fenêtres par fournisseur, compaction vs débordement, couverture par runtime |
| [Surcharge](docs/OVERHEAD.md) | Ce que coûte l'instrumentation, mesuré, avec le harnais pour le reproduire |
| [Droits d'accès](docs/ENTITLEMENTS.md) | Gratuit vs payant, matrice des niveaux, CLI de licence |
| [Approbations et politiques](docs/APPROVALS.md) | Filtrage pré-exécution, notation des risques, approbations par téléphone |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporter des traces n'importe où, ingérer OTLP depuis n'importe quoi |
| [Apportez votre propre agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de bout en bout, avec exemples exécutables |
| [Suivi SDK](docs/SDK_TRACKING.md) | Attribution des coûts pour les agents que vous avez construits vous-même |
| [Canaux de discussion](docs/CHANNELS.md) | Les adaptateurs de chat affichés dans Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurations NVIDIA NemoClaw isolées |
| [Docker](docs/DOCKER.md) | Image, compose, montages de volumes |
| [Architecture](ARCHITECTURE.md) · [Développement](docs/DEVELOPMENT.md) | Fonctionnement interne ; exécution depuis les sources |
| [Télémétrie](docs/TELEMETRY.md) | Les pings anonymes d'installation et d'ouverture du bureau, et comment les désactiver |

## Captures d'écran

Chaque chiffre ci-dessous provient d'une machine réelle, en lecture seule, sans rien de préconfiguré.

**Il vous dit quand quelque chose ne va pas, pas seulement ce qui s'est passé.**
Deux bannières d'anomalie en haut : des dépenses à 7 fois la moyenne quotidienne, et un pic
de coût de 4,2x. En dessous, 324 des 667 sessions récentes portant un signal de gaspillage,
détaillées par cause.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Il vous montre où l'argent est parti, dans chaque fenêtre temporelle.**
252,47 $ aujourd'hui, 513,15 $ cette semaine, 1 312,92 $ ce mois-ci, chacun avec les tokens
derrière et la part déjà couverte par votre abonnement. En dessous, environ 1 128 $/mois
détaillés comme récupérables et 17 256 $/mois déjà économisés par réutilisation du cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Il dessine comment un message devient une réponse.**
Le diagramme de flux en direct : vous, le canal par lequel il est arrivé, la passerelle, le
modèle qui répond en ce moment, et chaque outil qu'il a sollicité. Les nœuds s'allument à
mesure que le travail les traverse.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Chaque agent sur la machine, dans un seul tableau.**
Ce qu'il exécute, ce qu'il coûte sur les dernières 24 heures et sur sa durée de vie, quand
il a été vu pour la dernière fois, qui le possède, et si un abonnement couvre la facture.
14 agents ici, 3 sessions en cours, 13 inactives.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Il montre où le temps et l'argent d'un tour sont partis, outil par outil.**
Un tour d'une session réelle : 11 outils en 11,2 minutes pour 1,16 $. Chaque appel Bash et
appel de modèle obtient sa propre barre sur la chronologie, afin que la commande qui a duré
4,1 minutes et celle qui a duré 226 ms se distinguent d'un coup d'œil.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Il note le travail, pas seulement la dépense.**
Un A cette semaine : 54 tâches revenues propres, 2 tâches difficiles ayant coûté 48,57 $,
et les exécutions avec trop peu d'activité pour être jugées sont exclues de la note plutôt
que comptées comme des réussites. Chaque exécution difficile renvoie à sa trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Il montre pourquoi la fenêtre de contexte continue de se remplir.**
715K sur une fenêtre de 1M de tokens au dernier tour, un pic à 83,3%, 4 compactions
déclenchées de manière proactive plutôt que sur un débordement, et l'utilisation de
chaque tour en amont.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**La détection fonctionne sans que vous ayez à configurer quoi que ce soit.**
Les détecteurs intégrés sont actifs dès l'installation : agent devenu silencieux, flux de
télémétrie arrêté, pic de coût, rafale de tokens, erreurs en hausse, pic d'erreurs, seuil
budgétaire, signature de menace détectée, résultat d'outil de sécurité, changement de
posture de sécurité. Vos propres règles sont optionnelles en complément.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Retenir un appel risqué est optionnel, et livré désactivé.**
Suppressions récursives, force push, sudo, secrets, installations de paquets et appels
sortants ont chacun une règle que vous pouvez activer. Tant que vous ne le faites pas,
ClawMetry observe et ne change rien. Une fois activée, les appels correspondants attendent
ici (ou sur votre téléphone) une approbation ou un refus.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Plus, par runtime : [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Reconnaissance

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
