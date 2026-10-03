<!-- i18n-src:c99ac0512cae -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Um agente pode fazer uma centena de chamadas a ferramentas sem fazer qualquer progresso.** O ClawMetry
lê os ficheiros de sessão que os seus agentes de código já escrevem e reúne a linha temporal,
as chamadas a ferramentas e todos os dados de tokens e custos que o runtime expõe numa única
vista — para que possa distinguir uma execução longa que está a funcionar de uma que está bloqueada.

Funciona com **33 runtimes de agentes de IA** — Claude Code, OpenAI Codex, Hermes, OpenClaw e mais 29. Um só painel para toda a sua frota de agentes. ([a lista completa](SUPPORTED_RUNTIMES.txt), gerada a partir do catálogo.)

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Configuração zero. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Configuração zero: encontra os runtimes de agentes
que já tem instalados, lê-os apenas em modo de leitura e não altera nada no modo como são executados.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Antes de instalar

| | |
|---|---|
| **O que faz** | Lê os ficheiros de sessão e os registos (logs) que os seus agentes já escrevem. Sem SDK, sem alterações de código, sem instrumentação na sua aplicação. |
| **O que vê** | Linha temporal da sessão, reprodução ferramenta a ferramenta, discriminação de tokens e custos, e sinais de trajetória (ciclos, falhas repetidas) — por runtime. |
| **O que é gratuito** | `pip install clawmetry` lê **OpenClaw, NVIDIA NemoClaw, Goose e Qwen Code** sem conta, sem chave e sem qualquer chamada de rede. Os outros 28 — Claude Code, Codex, Cursor e os restantes — são lidos pelo complemento de código fechado `clawmetry-pro`, disponível com o período de avaliação de 7 dias ou com um plano — consulte [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para a divisão exata. |
| **Como começar** | `pip install clawmetry && clawmetry`, depois abra localhost:8900. Ainda não tem agentes nesta máquina? `clawmetry --sample` abre com três sessões sintéticas identificadas. |
| **O que sai da sua máquina** | Nenhum dado de sessão, a menos que execute `clawmetry connect`. Duas coisas são executadas por predefinição, ambas com opção de desativação e nenhuma transporta conteúdo de sessão: um ping anónimo de instalação e uma verificação de versão no PyPI. Cada destino está inventariado em [docs/EGRESS.md](docs/EGRESS.md), reconstruído a partir de uma captura de rede e não a partir da leitura de comentários. |

Dois limites que vale a pena conhecer antes de avaliar os resultados: os runtimes expõem dados
muito diferentes (alguns não publicam custos de forma alguma — [a matriz](docs/compatibility.md)
indica quais, por runtime), e observar uma ação não é o mesmo que ser capaz de a
bloquear ([quais controlos são reais, por runtime](docs/APPROVALS.md)).


## Funciona com 33 runtimes de agentes

**Gratuito na aplicação open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Num plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todos os runtimes têm o mesmo painel. Execute vários ao mesmo tempo e o seletor no
cabeçalho reorienta cada separador para um deles.

Construiu o seu próprio agente sobre um SDK em vez disso? O interceptor também monitoriza
as suas chamadas a LLMs. Consulte [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que obtém

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com reprodução
- **Custos e tokens**: por runtime, modelo, sessão e dia, com indicadores de anomalias
- **Fluxo**: diagrama em tempo real das mensagens a mover-se através de canais, modelos e ferramentas
- **Brain (Cérebro)**: o fluxo de eventos de raciocínio e chamadas a ferramentas à medida que acontece
- **Rebentamento de contexto**: utilização da janela dimensionada por fornecedor, compactação versus overflow forçado, mais um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os ficheiros e skills que cada runtime efetivamente carregou
- **Saúde e registos**: disco, memória, taxas de erro, limites de taxa, fluxo de registos em tempo real
- **Alertas**: tetos de orçamento, picos de erros, agente offline, encaminhados para Slack, Discord, PagerDuty, Telegram, E-mail
- **Aprovações**: suspenda chamadas a ferramentas arriscadas *antes* de serem executadas e aprove a partir do seu telemóvel ([como](docs/APPROVALS.md))

## Rebentamento de contexto, e quanto custa monitorizá-lo

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como é tratado o rebentamento da janela de contexto entre runtimes?**

Uma percentagem de utilização só é tão honesta quanto aquilo por que é dividida. O ClawMetry
dimensiona a janela por fornecedor a partir de [uma tabela que pode ler e
propor por PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Não mede os 33
runtimes todos com a régua de um único fornecedor. Isto é importante: um turno de 300K do GPT-5 avaliado
com a régua de 200K da Anthropic é lido como ">100%, rebentado" quando está, na realidade, a 75% dos
400K do GPT-5. A mesma régua esconde um turno do DeepSeek genuinamente em overflow de 130K
como um confortável 65%.

Cada janela é publicada com a sua proveniência: `model_table`, `explicit_marker`,
`observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um
indicador construído sobre uma suposição nunca é apresentado com a mesma autoridade que um construído sobre
uma consulta efetiva.

O ClawMetry só consegue ver eventos de compactação em alguns runtimes. Por isso,
`GET /api/context-coverage` reporta, por runtime, se um **zero significa
"correu sem problemas" ou "estamos às escuras"**. Um `0` que na verdade significa "às escuras" diz-o claramente.
[Detalhe completo](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Predefinição? |
|---|---|---|
| Monitorização de ficheiros de sessão (todos os 33 runtimes) | **0**. Processo separado, sem código do ClawMetry no seu agente | ativo |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada a LLM, ou 0,009% de uma chamada de 5s | inativo |
| Porta (gate) pré-ferramenta (cache aquecida) | **+44 ms** por chamada a ferramenta controlada, acima de um mínimo de 36 ms do interpretador | inativo |
| Proxy de aplicação de políticas | **+9,7 ms** por chamada a LLM | inativo |

Custo no anfitrião do daemon: **2.762 eventos/seg** de ingestão, **710 bytes/evento** em disco
(67,7 MB por 100 mil eventos), e **~12% de um núcleo** sustentado numa instalação
movimentada. Esse último número está acima do nosso próprio orçamento declarado de 5 a 10%, por isso é
publicado como uma falha a corrigir, em vez de omitido da página.

Medido num Apple M2 Pro com `benchmarks/overhead.py`. O conjunto de testes executa
cada condição num processo separado, alterna a sua ordem e **recusa-se
a imprimir um número quando as execuções discordam quanto ao seu sinal**. Execute-o na sua própria
máquina num minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todos os caminhos são medidos, incluindo as portas (gates) e o proxy de aplicação de políticas,
e o conjunto de testes é executado em Linux, macOS e Windows no CI. Dois resultados que vale a pena
conhecer: o proxy custa cerca de sete vezes mais no Windows do que no Linux, e
o daemon sustenta atualmente cerca de 12% de um núcleo, acima do nosso próprio orçamento de 5 a 10%.
O JSON em bruto, o método e o que ainda não foi medido estão em
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Gratuito** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, vista de frota, sincronização na cloud | $9 por nó / mês |
| **Pro** | Starter + controlo e avaliação: aprovações, políticas de risco de ferramentas, avaliações (evals), deteção de anomalias, otimizador de custos, exportação OTel, registo de auditoria à prova de adulteração | $19 por nó / mês |

Os planos anuais, a Enterprise e os valores atuais estão disponíveis em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença autoalojadas
funcionam sem a cloud (`clawmetry license`). A divisão exata entre gratuito/pago está
em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Os seus dados ficam na sua máquina

O ClawMetry lê ficheiros de sessão e registos locais. **Nenhum dado de sessão sai da sua máquina
a menos que execute `clawmetry connect`** — nem comandos, respostas, argumentos de ferramentas, conteúdos
de ficheiros ou linhas de registo. Quando se liga, a captura (snapshot) é encriptada de ponta a ponta
com uma chave que nunca sai da sua máquina, e é desencriptada no seu navegador. Se um
nó não tiver chave, o envio é ignorado em vez de enviado em claro, e nenhuma
resposta do servidor pode desativar isso.

Duas coisas são executadas por predefinição antes de se ligar, ambas com opção de desativação e nenhuma
transporta dados de sessão: um ping anónimo de instalação e uma verificação de versão no
PyPI. Uma instalação predefinida também consulta o seu IP público uma vez para uma linha de banner no arranque.
Cada destino, o que transporta e como desativá-lo está listado em
[docs/EGRESS.md](docs/EGRESS.md); instalações autoalojadas, reencaminhadas e isoladas de rede (air-gapped)
não fazem chamadas de saída discricionárias de forma alguma.

A desencriptação acontece no seu navegador, em código que lhe fornecemos. Isto costumava ser
uma promessa; agora é algo que pode verificar. Cada linha que toca na sua chave
vive num único ficheiro legível, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é incluído no wheel e servido literalmente, fixado com um hash de Integridade de Sub-recurso
(Subresource Integrity). Para confirmar que o navegador executa o que publicámos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isto não prova: servimos a página que carrega o ficheiro, por isso poderíamos
servir uma página diferente. Os hashes de integridade protegem-no de uma CDN comprometida,
não do fornecedor. O que ganha é que qualquer substituição tem de ser
deliberada, visível no código-fonte da página, e diferente de um artefacto no PyPI
que qualquer pessoa pode obter. Autoalojar ou permanecer apenas local remove
essa dependência por completo.

## Instalar

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ em macOS, Linux ou Windows, e pelo menos um runtime de agente na
mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ou deixe o agente configurá-lo por si. A skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ensina o Claude Code, Codex, Cursor, Gemini CLI, Copilot ou OpenCode a
instalar o ClawMetry, a reportar o que os agentes na máquina estão a fazer e a gastar,
a parar uma sessão a pedido, e a suster chamadas a ferramentas arriscadas para aprovação:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Rebentamento de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por fornecedor, compactação versus overflow, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | O que custa a instrumentação, medido, com o conjunto de testes para o reproduzir |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito versus pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Controlo pré-execução, pontuação de risco, aprovações pelo telemóvel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lugar, ingira OTLP de qualquer origem |
| [Traga o seu próprio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de ponta a ponta, com exemplos executáveis |
| [Monitorização via SDK](docs/SDK_TRACKING.md) | Atribuição de custos para agentes que construiu você mesmo |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Fluxo |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações isoladas (sandboxed) do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volumes |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona internamente; executar a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anónimos de instalação e de abertura da app de desktop, e como desativá-los |

## Capturas de ecrã

Cada número abaixo provém de uma máquina real, em modo de leitura, sem nada simulado previamente.

**Diz-lhe quando algo está errado, não apenas o que aconteceu.**
Dois avisos de anomalia no topo: despesa a 7x a média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes com um
sinal de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Mostra-lhe para onde foi o dinheiro, em cada janela temporal.**
$252,47 hoje, $513,15 esta semana, $1.312,92 este mês, cada um com os tokens
subjacentes e quanto a sua subscrição já cobre. Abaixo disso,
cerca de $1.128/mês discriminados como recuperáveis e $17.256/mês já poupados pela
reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Desenha como uma mensagem se transforma numa resposta.**
O diagrama de fluxo em tempo real: você, o canal pelo qual chegou, o gateway, o modelo
que está a responder neste momento, e cada ferramenta que utilizou. Os nós iluminam-se à medida
que o trabalho passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Todos os agentes na máquina, numa única tabela.**
O que executa, o que custou nas últimas 24 horas e durante toda a sua vida, quando
foi visto por último, quem é o proprietário, e se uma subscrição está a cobrir a
fatura. 14 agentes aqui, 3 sessões a trabalhar, 13 em silêncio.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra onde foi o tempo e o dinheiro de um turno, ferramenta a ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada chamada
Bash e cada chamada ao modelo tem a sua própria barra na linha temporal, para que o comando que correu
durante 4,1 minutos e o que correu em 226ms se distingam de imediato.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Avalia o trabalho, não apenas a despesa.**
Um A esta semana: 54 tarefas correram bem, 2 mais problemáticas custaram $48,57, e as
execuções com atividade demasiado reduzida para avaliar ficam de fora da nota em vez de
serem contadas como sucessos. Cada execução problemática está associada ao seu trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra por que razão a janela de contexto não para de enchumentar.**
715K de uma janela de 1M tokens no último turno, um pico de 83,3%, 4 compactações
que ocorreram todas de forma proativa em vez de por overflow, e a utilização de
cada turno subjacente.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A deteção funciona sem que configure nada.**
Os detetores incorporados estão ativos desde a instalação: agente ficou em silêncio, o feed de
telemetria parou, pico de custos, explosão de tokens, erros a aumentar, pico de erros, limiar
de orçamento, assinatura de ameaça correspondida, deteção de ferramenta de segurança, mudança na postura
de segurança. As suas próprias regras são opcionais, em complemento.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Suster uma chamada arriscada é opcional, e vem desativado por predefinição.**
Eliminações recursivas, force pushes, sudo, segredos, instalações de pacotes e chamadas de saída
têm cada uma uma regra que pode ativar. Até o fazer, o ClawMetry observa e
não altera nada. Depois de uma estar ativa, as chamadas correspondentes esperam aqui (ou no seu telemóvel)
por uma aprovação ou recusa.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mais, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Reconhecimento

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Histórico de Estrelas

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licença

MIT · Construído por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
