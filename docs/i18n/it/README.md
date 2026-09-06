<!-- i18n-src:88be2deff5d5 -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **30 runtime di agenti IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 26. Un'unica dashboard per l'intera flotta di agenti.

> 🌐 **Leggi in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altre →](docs/i18n/)

Un comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900**. Zero configurazione: trova i runtime di agenti
che già hai, li legge in sola lettura e non cambia nulla nel loro funzionamento.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funziona con 30 runtime di agenti

**Gratis nell'app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Con un piano a pagamento:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Ogni runtime ottiene la stessa dashboard. Esegui più runtime contemporaneamente e il
selettore nell'intestazione riporta ogni scheda su uno di essi.

Hai costruito il tuo agente su un SDK invece? L'interceptor traccia anche le sue
chiamate LLM. Vedi [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Cosa ottieni

- **Sessioni e trascrizioni**: cosa ha fatto ogni agente, turno dopo turno, con replay
- **Costi e token**: per runtime, modello, sessione e giorno, con segnalazioni di anomalie
- **Flow**: diagramma live dei messaggi che si muovono tra canali, modelli e strumenti
- **Brain**: il flusso di eventi di ragionamento e chiamate agli strumenti in tempo reale
- **Esaurimento del contesto**: utilizzo della finestra dimensionato per provider, compattazione vs overflow forzato, più una mappa per runtime di cosa *non possiamo* vedere ([come](docs/CONTEXT_BLOWOUT.md))
- **Memoria e skill**: i file e le skill effettivamente caricati da ogni runtime
- **Salute e log**: disco, memoria, tassi di errore, rate limit, stream di log live
- **Avvisi**: limiti di budget, picchi di errore, agente offline, instradati a Slack, Discord, PagerDuty, Telegram, Email
- **Approvazioni**: metti in pausa le chiamate a strumenti rischiose *prima* che vengano eseguite e approva dal tuo telefono ([come](docs/APPROVALS.md))

## Esaurimento del contesto, e cosa costa osservare

Due domande che vale la pena porsi prima di fidarsi di qualsiasi strumento di confronto tra agenti.

**Come gestisce l'esaurimento della finestra di contesto tra i vari runtime?**

Una percentuale di utilizzo è onesta solo quanto il denominatore da cui è calcolata.
ClawMetry dimensiona la finestra per provider a partire da [una tabella che puoi leggere e
proporre via PR](clawmetry/context_windows.py), che copre Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Non misura tutti i 30
runtime con il righello di un solo fornitore. Questo è importante: un turno GPT-5 da 300K
valutato con il righello di Anthropic da 200K legge ">100%, saturato" quando in realtà è al 75% dei
400K di GPT-5. Lo stesso righello nasconde un turno DeepSeek da 130K genuinamente andato in overflow
facendolo sembrare un comodo 65%.

Ogni finestra viene fornita con la sua provenienza: `model_table`, `explicit_marker`,
`observed_floor`, oppure un onesto `default` quando non conosciamo il modello. Un
indicatore costruito su una supposizione non viene mai renderizzato con la stessa autorità di uno costruito su una
consultazione effettiva.

ClawMetry può vedere gli eventi di compattazione solo su alcuni runtime. Quindi
`GET /api/context-coverage` riporta, per runtime, se uno zero significa
"eseguito pulito" oppure "siamo ciechi". Uno `0` che in realtà significa cieco lo dichiara.
[Dettagli completi](docs/CONTEXT_BLOWOUT.md)

**Quanto costa l'instrumentazione?**

| Percorso | Aggiunto al tuo agente | Predefinito? |
|---|---|---|
| Tailing dei file di sessione (tutti i 30 runtime) | **0**. Processo separato, nessun codice ClawMetry nel tuo agente | attivo |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per chiamata LLM, ovvero lo 0,009% di una chiamata di 5s | disattivo |
| Gate del hook pre-strumento (cache calda) | **+44 ms** per chiamata a strumento sottoposta a gate, oltre a un minimo dell'interprete di 36 ms | disattivo |
| Proxy di enforcement | **+9,7 ms** per chiamata LLM | disattivo |

Costo host del daemon: **2.762 eventi/sec** in ingestione, **710 byte/evento** su disco
(67,7 MB per 100k eventi), e **~12% di un core** in modo sostenuto su un'installazione occupata. Quest'ultimo
numero supera il nostro stesso budget dichiarato del 5-10%, quindi viene pubblicato come un bug da inseguire
piuttosto che essere omesso dalla pagina.

Misurato su un Apple M2 Pro con `benchmarks/overhead.py`. Il banco di prova esegue
ogni condizione in un processo separato, ne alterna l'ordine e **si rifiuta
di stampare un numero quando i round non concordano sul suo segno**. Eseguilo sulla tua
macchina in un minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Ogni percorso viene misurato, inclusi i gate degli hook e il proxy di enforcement,
e il banco di prova gira su Linux, macOS e Windows in CI. Due risultati degni di nota: il
proxy costa circa sette volte di più su Windows rispetto a Linux, e
il daemon attualmente sostiene circa il 12% di un core, oltre il nostro stesso budget del
5-10%. I dati grezzi in JSON, il metodo e ciò che rimane ancora da misurare sono in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prezzi

| Piano | Cosa copre | Prezzo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard completa, solo locale | $0 |
| **Starter** | Tutti gli altri runtime sopra elencati, vista flotta, sincronizzazione cloud | $9 per nodo / mese |
| **Pro** | Starter + controllo e valutazione: approvazioni, policy di rischio sugli strumenti, valutazioni, rilevamento anomalie, ottimizzatore dei costi, esportazione OTel, registro di audit a prova di manomissione | $19 per nodo / mese |

I piani annuali, Enterprise e i prezzi attuali si trovano su
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Le chiavi di licenza self-hosted
funzionano senza il cloud (`clawmetry license`). La suddivisione esatta gratuito/a pagamento è
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## I tuoi dati restano sulla tua macchina

ClawMetry legge file di sessione e log locali. **Nessun dato di sessione lascia il tuo computer
a meno che tu non esegua `clawmetry connect`** — nessun prompt, risposta, argomento di strumento, contenuto
di file o riga di log. Quando ti connetti, lo snapshot viene cifrato end-to-end
con una chiave che non lascia mai la tua macchina, e decifrato nel tuo browser. Se un
nodo non ha una chiave, il caricamento viene saltato invece di essere inviato in chiaro, e nessuna
risposta del server può disattivare questo comportamento.

Due cose vengono eseguite per impostazione predefinita prima di connetterti, entrambe disattivabili e nessuna delle due
trasporta dati di sessione: un ping di installazione anonimo e un controllo versione rispetto a
PyPI. Un'installazione predefinita cerca anche il tuo IP pubblico una volta per una riga del banner
di avvio. Ogni destinazione, cosa trasporta e come disattivarla sono elencati in
[docs/EGRESS.md](docs/EGRESS.md); le installazioni self-hosted, reindirizzate e air-gapped
non effettuano alcuna chiamata in uscita discrezionale.

La decifratura avviene nel tuo browser, in codice che ti forniamo noi. Un tempo era
una promessa; ora è qualcosa che puoi verificare. Ogni riga che tocca la tua chiave
vive in un unico file leggibile, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
che viene incluso nel wheel e servito testualmente, ancorato con un hash Subresource
Integrity. Per confermare che il browser esegue ciò che abbiamo pubblicato:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ciò che questo non dimostra: siamo noi a servire la pagina che carica il file, quindi potremmo
servire una pagina diversa. Gli hash di integrità ti proteggono da una CDN compromessa,
non dal fornitore. Ciò che ottieni è che qualsiasi sostituzione deve essere
deliberata, visibile nel sorgente della pagina, e diversa da un artefatto su PyPI
che chiunque può scaricare. L'auto-hosting o restare solo in locale elimina
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
fermare una sessione su richiesta, e trattenere per l'approvazione le chiamate a strumenti rischiose:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentazione

| | |
|---|---|
| [Compatibilità dei runtime](docs/compatibility.md) | Cosa legge ogni adattatore, e come aggiungere un runtime |
| [Esaurimento del contesto](docs/CONTEXT_BLOWOUT.md) | Finestre per provider, compattazione vs overflow, copertura per runtime |
| [Overhead](docs/OVERHEAD.md) | Quanto costa l'instrumentazione, misurato, con il banco di prova per riprodurlo |
| [Entitlement](docs/ENTITLEMENTS.md) | Gratuito vs a pagamento, matrice dei livelli, CLI di licenza |
| [Approvazioni e policy](docs/APPROVALS.md) | Gating pre-esecuzione, valutazione del rischio, approvazioni da telefono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Esporta trace ovunque, ingerisci OTLP da qualsiasi fonte |
| [Porta il tuo agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, con esempi eseguibili |
| [Tracciamento SDK](docs/SDK_TRACKING.md) | Attribuzione dei costi per agenti costruiti da te |
| [Canali chat](docs/CHANNELS.md) | Gli adattatori chat mostrati in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurazioni sandboxed di NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Immagine, compose, mount dei volumi |
| [Architettura](ARCHITECTURE.md) · [Sviluppo](docs/DEVELOPMENT.md) | Come funziona internamente; esecuzione dal sorgente |
| [Telemetria](docs/TELEMETRY.md) | I ping anonimi di installazione e apertura desktop, e come disattivarli |

## Screenshot

Ogni numero qui sotto proviene da una macchina reale, in sola lettura, senza nulla di preimpostato.

**Ti dice quando qualcosa non va, non solo cosa è successo.**
Due banner di anomalia in alto: spesa che corre a 7 volte la media giornaliera, e un
picco di costo di 4,2x. Sotto di essi, 324 delle 667 sessioni recenti che portano un
segnale di spreco, suddiviso per causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ti mostra dove sono finiti i soldi, in ogni finestra temporale.**
$252,47 oggi, $513,15 questa settimana, $1.312,92 questo mese, ognuno con i token
dietro di esso e quanto di quello è già coperto dal tuo abbonamento. Sotto, circa
$1.128/mese classificati come recuperabili e $17.256/mese già risparmiati grazie
al riutilizzo della cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Disegna come un messaggio diventa una risposta.**
Il diagramma di flusso live: tu, il canale su cui è arrivato, il gateway, il modello
che sta rispondendo in questo momento, e ogni strumento a cui ha fatto ricorso. I nodi si illuminano
man mano che il lavoro li attraversa.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Ogni agente sulla macchina, in un'unica tabella.**
Cosa esegue, quanto costa nelle ultime 24 ore e durante la sua vita, quando
è stato visto l'ultima volta, chi lo possiede, e se un abbonamento sta coprendo il
conto. 14 agenti qui, 3 sessioni al lavoro, 13 silenziose.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra dove sono andati il tempo e i soldi di un turno, strumento per strumento.**
Un turno di una sessione reale: 11 strumenti in 11,2 minuti per $1,16. Ogni chiamata Bash
e chiamata al modello ottiene la propria barra sulla timeline, così il comando che è girato
per 4,1 minuti e quello che è girato per 226ms si distinguono a colpo d'occhio.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Valuta il lavoro, non solo la spesa.**
Una A questa settimana: 54 attività sono tornate pulite, 2 grezze sono costate $48,57, e le
esecuzioni con troppo poca attività per essere giudicate vengono escluse dal voto invece di
essere contate come successi. Ogni esecuzione grezza rimanda alla propria traccia.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra perché la finestra di contesto continua a riempirsi.**
715K di una finestra da 1M di token nell'ultimo turno, un picco dell'83,3%, 4 compattazioni
che sono scattate tutte in modo proattivo piuttosto che per overflow, e l'utilizzo di
ogni turno che ci sta dietro.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Il rilevamento funziona senza che tu configuri nulla.**
I rilevatori integrati sono attivi dall'installazione: agente diventato silenzioso, feed di
telemetria fermo, picco di costo, esplosione di token, errori in aumento, picco di errori, soglia
di budget, firma di minaccia rilevata, riscontro di uno strumento di sicurezza, postura di sicurezza
cambiata. Le tue regole personalizzate sono opzionali in aggiunta.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Trattenere una chiamata rischiosa è opt-in, e viene spedito disattivato.**
Cancellazioni ricorsive, force push, sudo, segreti, installazioni di pacchetti e chiamate
in uscita ottengono ciascuna una regola che puoi attivare. Finché non lo fai, ClawMetry osserva e
non cambia nulla. Una volta attivata, le chiamate corrispondenti attendono qui (o sul tuo telefono)
un'approvazione o un rifiuto.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Altro, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Storico delle Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licenza

MIT · Realizzato da [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
