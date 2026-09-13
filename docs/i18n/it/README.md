<!-- i18n-src:a855a14295b0 -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Un agente può effettuare cento chiamate a strumenti senza fare alcun progresso.** ClawMetry
legge i file di sessione che i tuoi agenti di coding già scrivono, e riunisce la cronologia,
le chiamate agli strumenti e qualsiasi dato su token e costi che il runtime espone in un'unica
vista, così puoi distinguere un'esecuzione lunga che sta funzionando da una che è bloccata.

Funziona con **32 runtime di agenti AI**: Claude Code, OpenAI Codex, Hermes, OpenClaw e altri 28. Un'unica dashboard per l'intera flotta di agenti. ([elenco completo](SUPPORTED_RUNTIMES.txt), generato dal catalogo.)

> 🌐 **Leggi questo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altre lingue →](docs/i18n/)

Un solo comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900**. Zero configurazione: trova i runtime di agenti
che hai già, li legge in sola lettura e non cambia nulla nel loro funzionamento.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Prima di installare

| | |
|---|---|
| **Cosa fa** | Legge i file di sessione e i log che i tuoi agenti già scrivono. Nessun SDK, nessuna modifica al codice, nessuna strumentazione nella tua app. |
| **Cosa vedi** | Cronologia delle sessioni, replay strumento per strumento, ripartizione di token e costi, e segnali di traiettoria (loop, fallimenti ripetuti), per ogni runtime. |
| **Cosa è gratuito** | `pip install clawmetry` legge **OpenClaw, NVIDIA NemoClaw e Goose** senza account, senza chiave e senza chiamate di rete. Gli altri 27, Claude Code, Codex, Cursor e il resto, vengono letti dal companion a sorgente chiuso `clawmetry-pro`, incluso nella prova gratuita di 7 giorni o in un piano a pagamento: vedi [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) per la ripartizione esatta. |
| **Come iniziare** | `pip install clawmetry && clawmetry`, poi apri localhost:8900. Nessun agente ancora su questa macchina? `clawmetry --sample` si apre su tre sessioni sintetiche etichettate. |
| **Cosa lascia la tua macchina** | Nessun dato di sessione, a meno che tu non esegua `clawmetry connect`. Due cose vengono eseguite di default, entrambe disattivabili e nessuna delle due porta contenuti di sessione: un ping anonimo di installazione e un controllo della versione su PyPI. Ogni destinazione è inventariata in [docs/EGRESS.md](docs/EGRESS.md), ricostruita da una cattura del traffico di rete piuttosto che dalla lettura dei commenti. |

Due limiti che vale la pena conoscere prima di giudicare il risultato: i runtime espongono
dati molto diversi tra loro (alcuni non pubblicano alcun costo: [la matrice](docs/compatibility.md)
indica quali, per ciascun runtime), e osservare un'azione non equivale a poterla
bloccare ([quali controlli sono reali, per ogni runtime](docs/APPROVALS.md)).


## Funziona con 32 runtime di agenti

**Gratuito nell'app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Su piano a pagamento:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Ogni runtime riceve la stessa dashboard. Esegui più runtime contemporaneamente e il
selettore in alto riadatta ogni scheda a uno di essi.

Hai costruito il tuo agente su un SDK invece che su un runtime? L'interceptor traccia
anche le sue chiamate LLM. Vedi [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Cosa ottieni

- **Sessioni e trascrizioni**: cosa ha fatto ogni agente, turno per turno, con replay
- **Costi e token**: per runtime, modello, sessione e giorno, con segnalazioni di anomalie
- **Flow**: diagramma live dei messaggi che si muovono tra canali, modelli e strumenti
- **Brain**: il flusso di eventi di ragionamento e chiamate agli strumenti in tempo reale
- **Context blowout**: utilizzo della finestra dimensionato per provider, compattazione vs overflow forzato, più una mappa per runtime di ciò che *non possiamo* vedere ([come](docs/CONTEXT_BLOWOUT.md))
- **Memoria e skill**: i file e le skill che ogni runtime ha effettivamente caricato
- **Salute e log**: disco, memoria, tassi di errore, rate limit, stream live dei log
- **Alert**: limiti di budget, picchi di errore, agente offline, instradati verso Slack, Discord, PagerDuty, Telegram, Email
- **Approvazioni**: metti in pausa le chiamate a strumenti rischiose *prima* che vengano eseguite e approva dal tuo telefono ([come](docs/APPROVALS.md))

## Context blowout, e quanto costa monitorare

Due domande che vale la pena porsi prima di fidarsi di qualsiasi strumento di confronto tra agenti.

**Come gestisce il blowout della finestra di contesto tra i vari runtime?**

Una percentuale di utilizzo è onesta solo quanto ciò per cui viene divisa. ClawMetry
dimensiona la finestra per provider a partire da [una tabella che puoi leggere e proporre in PR](clawmetry/context_windows.py),
che copre Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Non misura tutti e 32 i
runtime con il righello di un solo fornitore. Questo è rilevante: un turno GPT-5 da 300K
valutato con il righello dei 200K di Anthropic legge ">100%, esaurita" quando in realtà è al 75% dei
400K di GPT-5. Lo stesso righello nasconde un turno DeepSeek da 130K genuinamente in overflow
facendolo sembrare un comodo 65%.

Ogni finestra viene fornita con la sua provenienza: `model_table`, `explicit_marker`,
`observed_floor`, oppure un onesto `default` quando non conosciamo il modello. Un
indicatore costruito su una supposizione non viene mai renderizzato con la stessa autorità di uno costruito su una
ricerca effettiva.

ClawMetry può vedere gli eventi di compattazione solo su alcuni runtime. Quindi
`GET /api/context-coverage` riporta, per ogni runtime, se uno zero significa
"eseguito senza problemi" oppure "siamo ciechi". Uno `0` che in realtà significa cieco lo dichiara esplicitamente.
[Dettagli completi](docs/CONTEXT_BLOWOUT.md)

**Quanto costa la strumentazione?**

| Percorso | Aggiunto al tuo agente | Predefinito? |
|---|---|---|
| Tailing dei file di sessione (tutti e 32 i runtime) | **0**. Processo separato, nessun codice ClawMetry nel tuo agente | attivo |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per chiamata LLM, ovvero lo 0,009% di una chiamata di 5s | disattivo |
| Gate hook pre-tool (cache calda) | **+44 ms** per chiamata a strumento sottoposta a gate, oltre a un minimo dell'interprete di 36 ms | disattivo |
| Proxy di enforcement | **+9,7 ms** per chiamata LLM | disattivo |

Costo dell'host del daemon: **2.762 eventi/sec** in ingestione, **710 byte/evento** su disco
(67,7 MB ogni 100k eventi), e **circa il 12% di un core** in modo sostenuto su un'installazione
impegnata. Quest'ultimo numero supera il nostro budget dichiarato del 5-10%, quindi viene
pubblicato come un bug da inseguire piuttosto che omesso dalla pagina.

Misurato su un Apple M2 Pro con `benchmarks/overhead.py`. Il harness esegue
ogni condizione in un processo separato, ne alterna l'ordine e **si rifiuta di
stampare un numero quando i round non concordano sul suo segno**. Eseguilo sulla tua
macchina in un minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Ogni percorso viene misurato, inclusi i gate hook e il proxy di enforcement,
e il harness gira su Linux, macOS e Windows in CI. Due risultati che vale la pena
conoscere: il proxy costa circa sette volte di più su Windows rispetto a Linux, e
il daemon attualmente sostiene circa il 12% di un core, oltre il nostro budget del
5-10%. I dati JSON grezzi, il metodo e ciò che resta ancora non misurato sono in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prezzi

| Piano | Cosa copre | Prezzo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard completa, solo locale | $0 |
| **Starter** | Tutti gli altri runtime sopra elencati, vista flotta, sincronizzazione cloud | $9 per nodo / mese |
| **Pro** | Starter + controllo e valutazione: approvazioni, policy di rischio degli strumenti, valutazioni, rilevamento anomalie, ottimizzatore dei costi, esportazione OTel, log di audit a prova di manomissione | $19 per nodo / mese |

I piani annuali, Enterprise e i numeri aggiornati sono disponibili su
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Le chiavi di licenza self-hosted
funzionano senza il cloud (`clawmetry license`). La ripartizione esatta tra gratuito e a pagamento è
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## I tuoi dati restano sulla tua macchina

ClawMetry legge file di sessione e log locali. **Nessun dato di sessione lascia la tua macchina
a meno che tu non esegua `clawmetry connect`**, niente prompt, risposte, argomenti degli strumenti, contenuti
di file o righe di log. Quando ti connetti, lo snapshot viene cifrato end-to-end
con una chiave che non lascia mai la tua macchina, e decifrato nel tuo browser. Se un
nodo non ha una chiave, il caricamento viene saltato anziché inviato in chiaro, e nessuna
risposta del server può disattivare questo comportamento.

Due cose vengono eseguite di default prima che tu ti connetta, entrambe disattivabili e nessuna delle due
porta dati di sessione: un ping anonimo di installazione e un controllo di versione rispetto a
PyPI. Un'installazione predefinita cerca anche il tuo IP pubblico una volta per una riga
del banner iniziale. Ogni destinazione, cosa trasporta e come disattivarla è elencato in
[docs/EGRESS.md](docs/EGRESS.md); le installazioni self-hosted, reindirizzate e air-gapped
non effettuano alcuna chiamata in uscita discrezionale.

La decifrazione avviene nel tuo browser, con codice che ti forniamo noi stessi. Un tempo era
una promessa; ora è qualcosa che puoi verificare. Ogni riga che tocca la tua chiave
vive in un unico file leggibile, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
che viene incluso nel wheel e servito parola per parola, ancorato con un hash Subresource
Integrity. Per confermare che il browser esegua ciò che abbiamo pubblicato:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Cosa questo non dimostra: siamo noi a servire la pagina che carica il file, quindi potremmo
servire una pagina diversa. Gli hash di integrità ti proteggono da un CDN compromesso,
non dal fornitore stesso. Ciò che ottieni è che qualsiasi sostituzione deve essere
deliberata, visibile nel sorgente della pagina, e diversa da un artefatto su PyPI
che chiunque può scaricare. Il self-hosting o l'uso esclusivamente locale eliminano
del tutto questa dipendenza.

## Installazione

```bash
pip install clawmetry     # poi: clawmetry
```

Oppure la riga singola: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Richiede Python 3.8+ su macOS, Linux o Windows, e almeno un runtime di agente sulla
stessa macchina. Istruzioni Docker: [docs/DOCKER.md](docs/DOCKER.md).

Oppure lascia che sia l'agente a configurarlo per te. La skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
insegna a Claude Code, Codex, Cursor, Gemini CLI, Copilot o OpenCode a
installare ClawMetry, riportare cosa stanno facendo e spendendo gli agenti sulla macchina,
fermare una sessione su richiesta, e trattenere le chiamate a strumenti rischiose per l'approvazione:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentazione

| | |
|---|---|
| [Compatibilità dei runtime](docs/compatibility.md) | Cosa legge ogni adapter, e come aggiungere un runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Finestre per provider, compattazione vs overflow, copertura per runtime |
| [Overhead](docs/OVERHEAD.md) | Quanto costa la strumentazione, misurato, con il harness per riprodurlo |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito vs a pagamento, matrice dei livelli, CLI delle licenze |
| [Approvazioni e policy](docs/APPROVALS.md) | Gating pre-esecuzione, punteggio di rischio, approvazioni da telefono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Esporta tracce ovunque, ingerisci OTLP da qualsiasi fonte |
| [Porta il tuo agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, con esempi eseguibili |
| [Tracciamento SDK](docs/SDK_TRACKING.md) | Attribuzione dei costi per agenti che hai costruito tu stesso |
| [Canali di chat](docs/CHANNELS.md) | Gli adapter di chat mostrati in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurazioni sandboxed di NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Immagine, compose, mount dei volumi |
| [Architettura](ARCHITECTURE.md) · [Sviluppo](docs/DEVELOPMENT.md) | Come funziona internamente; eseguire dal sorgente |
| [Telemetria](docs/TELEMETRY.md) | I ping anonimi di installazione e di apertura del desktop, e come disattivarli |

## Screenshot

Ogni numero qui sotto proviene da una macchina reale, in sola lettura, senza nulla di preimpostato.

**Ti dice quando qualcosa non va, non solo cosa è successo.**
Due banner di anomalia in alto: spesa che corre a 7 volte la media giornaliera, e un
picco di costo di 4,2 volte. Sotto di essi, 324 delle 667 sessioni recenti che presentano un
segnale di spreco, suddiviso per causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ti mostra dove sono finiti i soldi, in ogni finestra temporale.**
$252,47 oggi, $513,15 questa settimana, $1.312,92 questo mese, ciascuno con i token
dietro di esso e quanto ne copre già il tuo abbonamento. Sotto, circa
$1.128/mese classificati come recuperabili e $17.256/mese già risparmiati grazie
al riutilizzo della cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Disegna come un messaggio diventa una risposta.**
Il diagramma di flusso live: tu, il canale su cui è arrivato, il gateway, il modello
che sta rispondendo in questo momento, e ogni strumento a cui ha fatto ricorso. I nodi si illuminano
man mano che il lavoro li attraversa.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Ogni agente sulla macchina, in un'unica tabella.**
Cosa esegue, quanto costa nelle ultime 24 ore e nell'intero ciclo di vita, quando
è stato visto l'ultima volta, chi lo possiede, e se un abbonamento copre la
spesa. 14 agenti qui, 3 sessioni al lavoro, 13 inattive.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra dove è andato il tempo e il denaro di un turno, strumento per strumento.**
Un turno di una sessione reale: 11 strumenti in 11,2 minuti per $1,16. Ogni chiamata
Bash e ogni chiamata al modello ottiene la propria barra sulla timeline, così il comando che è girato
per 4,1 minuti e quello durato 226ms si distinguono a colpo d'occhio.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Valuta il lavoro, non solo la spesa.**
Una A questa settimana: 54 task sono tornati puliti, 2 difficili sono costati $48,57, e le
esecuzioni con attività troppo scarsa per essere valutate vengono escluse dal voto invece
di essere contate come successi. Ogni esecuzione difficile rimanda alla propria traccia.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra perché la finestra di contesto continua a riempirsi.**
715K di una finestra da 1M di token nell'ultimo turno, un picco dell'83,3%, 4 compattazioni
scattate tutte in modo proattivo piuttosto che per overflow, e l'utilizzo di
ogni turno che ha portato a questo.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Il rilevamento funziona senza che tu configuri nulla.**
I detector integrati sono attivi dall'installazione: agente diventato silenzioso, feed di
telemetria interrotto, picco di costo, ondata di token, errori in aumento, picco di errori, soglia
di budget, firma di minaccia rilevata, risultato di uno strumento di sicurezza, cambiamento della
postura di sicurezza. Le tue regole personalizzate sono opzionali, in aggiunta.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Trattenere una chiamata rischiosa è opzionale, ed è disattivato di default.**
Cancellazioni ricorsive, force push, sudo, segreti, installazioni di pacchetti e chiamate in uscita
ottengono ciascuna una regola che puoi attivare. Finché non lo fai, ClawMetry osserva e
non cambia nulla. Una volta attivata una regola, le chiamate corrispondenti attendono qui (o sul tuo telefono)
un'approvazione o un rifiuto.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Altro, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Riconoscimenti

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Cronologia delle stelle

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licenza

MIT · Creato da [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
