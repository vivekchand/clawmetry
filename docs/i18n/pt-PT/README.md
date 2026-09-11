<!-- i18n-src:12b97259721e -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Um agente pode fazer cem chamadas de ferramentas sem fazer qualquer progresso.** O ClawMetry
lê os ficheiros de sessão que os seus agentes de código já escrevem, e junta a linha temporal,
as chamadas de ferramentas e quaisquer dados de tokens e custo que o runtime exponha numa única
vista — para que consiga distinguir uma execução longa que está a funcionar de uma que está encravada.

Funciona com **31 runtimes de agentes de IA** — Claude Code, OpenAI Codex, Hermes, OpenClaw e mais 27. Um único painel para toda a sua frota de agentes. ([a lista completa](SUPPORTED_RUNTIMES.txt), gerada a partir do catálogo.)

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: encontra os runtimes de agentes
que já tem, lê-os em modo só de leitura e não altera nada na forma como funcionam.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Antes de instalar

| | |
|---|---|
| **O que faz** | Lê os ficheiros de sessão e os logs que os seus agentes já escrevem. Sem SDK, sem alterações de código, sem instrumentação na sua aplicação. |
| **O que vê** | Linha temporal da sessão, replay ferramenta a ferramenta, distribuição de tokens e custo, e sinais de trajetória (loops, falhas repetidas) — por runtime. |
| **O que é gratuito** | `pip install clawmetry` lê **OpenClaw, NVIDIA NemoClaw e Goose** sem conta, sem chave e sem qualquer chamada de rede. Os outros 27 — Claude Code, Codex, Cursor e os restantes — são lidos pelo companheiro de código fechado `clawmetry-pro`, disponível com o período de teste de 7 dias ou num plano — consulte [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para a divisão exata. |
| **Como começar** | `pip install clawmetry && clawmetry`, depois abra localhost:8900. Ainda não tem agentes nesta máquina? `clawmetry --sample` abre com três sessões sintéticas identificadas. |
| **O que sai da sua máquina** | Nenhum dado de sessão, a menos que execute `clawmetry connect`. Duas coisas correm por predefinição, ambas com opção de desativar e nenhuma transportando conteúdo de sessão: um ping de instalação anónimo e uma verificação de versão no PyPI. Todos os destinos estão inventariados em [docs/EGRESS.md](docs/EGRESS.md), reconstruído a partir de uma captura de rede em vez de a partir da leitura de comentários. |

Duas limitações que vale a pena conhecer antes de avaliar o resultado: os runtimes expõem
dados muito diferentes (alguns não publicam qualquer custo — [a matriz](docs/compatibility.md)
indica quais, por runtime), e observar uma ação não é o mesmo que conseguir
bloqueá-la ([quais os controlos reais, por runtime](docs/APPROVALS.md)).


## Funciona com 31 runtimes de agentes

**Gratuito na aplicação open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Num plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todos os runtimes têm acesso ao mesmo painel. Execute vários em simultâneo e o
seletor no cabeçalho reajusta cada separador para um deles.

Construiu o seu próprio agente com um SDK em vez disso? O interceptor também
rastreia as suas chamadas de LLM. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que obtém

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com replay
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalização de anomalias
- **Fluxo**: diagrama em tempo real das mensagens a mover-se entre canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas à medida que acontece
- **Estouro de contexto**: utilização da janela dimensionada por fornecedor, compactação vs. overflow forçado, mais um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os ficheiros e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de logs em tempo real
- **Alertas**: limites de orçamento, picos de erro, agente offline, encaminhados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pausar chamadas de ferramentas arriscadas *antes* de serem executadas e aprovar a partir do seu telemóvel ([como](docs/APPROVALS.md))

## Estouro de contexto, e quanto custa observar

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de
comparação de agentes.

**Como é que lida com o estouro da janela de contexto entre runtimes?**

Uma percentagem de utilização só é tão honesta quanto aquilo por que divide. O ClawMetry
dimensiona a janela por fornecedor a partir de [uma tabela que pode ler e
propor via PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Não mede os 31
runtimes com a régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5
avaliado com a régua de 200K da Anthropic lê-se como ">100%, estourado" quando na
verdade está a 75% dos 400K do GPT-5. A mesma régua esconde um turno de 130K do DeepSeek
genuinamente em overflow como um confortável 65%.

Cada janela é fornecida com a sua proveniência: `model_table`, `explicit_marker`,
`observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um
indicador construído sobre uma estimativa nunca é apresentado com a mesma autoridade
que um construído sobre uma consulta a uma tabela.

O ClawMetry só consegue ver eventos de compactação nalguns runtimes. Por isso,
`GET /api/context-coverage` reporta, por runtime, se um **zero significa
"correu bem" ou "estamos às cegas"**. Um `0` que na verdade significa cego, diz-o.
[Detalhe completo](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Predefinição? |
|---|---|---|
| Leitura contínua de ficheiros de sessão (todos os 31 runtimes) | **0**. Processo separado, sem código do ClawMetry no seu agente | ativo |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada de LLM, ou 0,009% de uma chamada de 5s | inativo |
| Porta de bloqueio pré-ferramenta (cache quente) | **+44 ms** por chamada de ferramenta bloqueada, acima de um piso de 36 ms do interpretador | inativo |
| Proxy de enforcement | **+9,7 ms** por chamada de LLM | inativo |

Custo no anfitrião do daemon: **2.762 eventos/seg** de ingestão, **710 bytes/evento**
em disco (67,7 MB por 100 mil eventos), e **~12% de um núcleo** sustentado numa
instalação ocupada. Esse último número está acima do nosso próprio orçamento declarado
de 5-10%, por isso é publicado como um problema a resolver, em vez de omitido da página.

Medido num Apple M2 Pro com `benchmarks/overhead.py`. O harness executa
cada condição num processo separado, alterna a sua ordem e **recusa-se a
imprimir um número quando as rondas discordam quanto ao seu sinal**. Execute-o na sua
própria máquina num minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todos os caminhos são medidos, incluindo as portas de bloqueio e o proxy de
enforcement, e o harness corre em Linux, macOS e Windows na CI. Dois resultados
que vale a pena conhecer: o proxy custa cerca de sete vezes mais no Windows do que
no Linux, e o daemon sustenta atualmente cerca de 12% de um núcleo, acima do nosso
próprio orçamento de 5-10%. O JSON em bruto, o método e o que ainda não está medido
estão em [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, vista de frota, sincronização na cloud | $9 por nó / mês |
| **Pro** | Starter + controlo e avaliação: aprovações, políticas de risco de ferramentas, avaliações, deteção de anomalias, otimizador de custos, exportação OTel, registo de auditoria à prova de adulteração | $19 por nó / mês |

Os planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença
para auto-hospedagem funcionam sem a cloud (`clawmetry license`). A divisão exata
entre gratuito/pago está em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Os seus dados ficam na sua máquina

O ClawMetry lê ficheiros de sessão e logs locais. **Nenhum dado de sessão sai da sua
máquina a menos que execute `clawmetry connect`** — sem prompts, respostas, argumentos
de ferramentas, conteúdo de ficheiros ou linhas de log. Quando se liga, o snapshot é
encriptado de ponta a ponta com uma chave que nunca sai da sua máquina, e desencriptado
no seu navegador. Se um nó não tiver chave, o envio é omitido em vez de enviado em
claro, e nenhuma resposta do servidor pode desligar isso.

Duas coisas correm por predefinição antes de se ligar, ambas com opção de desativar
e nenhuma transportando dados de sessão: um ping de instalação anónimo e uma
verificação de versão contra o PyPI. Uma instalação predefinida também consulta o seu
IP público uma vez para uma linha de banner de arranque. Todos os destinos, o que
transportam e como desligá-los estão listados em
[docs/EGRESS.md](docs/EGRESS.md); instalações auto-hospedadas, redirecionadas e
isoladas de rede não fazem quaisquer chamadas de saída discricionárias.

A desencriptação acontece no seu navegador, em código que lhe fornecemos. Isso
costumava ser uma promessa; agora é algo que pode verificar. Cada linha que toca na
sua chave está num único ficheiro legível,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é incluído dentro do wheel e servido literalmente, fixado com um hash de
Subresource Integrity. Para confirmar que o navegador executa o que publicámos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isto não prova: nós servimos a página que carrega o ficheiro, por isso
poderíamos servir uma página diferente. Os hashes de integridade protegem-no de
um CDN comprometido, não do fornecedor. O que ganha é que qualquer substituição
tem de ser deliberada, visível no código-fonte da página e diferente de um
artefacto no PyPI que qualquer pessoa pode obter. Auto-hospedar ou permanecer
apenas local remove a dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ em macOS, Linux ou Windows, e pelo menos um runtime de agente na
mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ou deixe o agente configurá-lo por si. A skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ensina o Claude Code, Codex, Cursor, Gemini CLI, Copilot ou OpenCode a
instalar o ClawMetry, reportar o que os agentes na máquina estão a fazer e a gastar,
parar uma sessão a pedido, e reter chamadas de ferramentas arriscadas para aprovação:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por fornecedor, compactação vs. overflow, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | O que a instrumentação custa, medido, com o harness para reproduzir |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito vs. pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Bloqueio pré-execução, pontuação de risco, aprovações por telemóvel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lado, ingira OTLP de qualquer coisa |
| [Traga o seu próprio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de ponta a ponta, com exemplos executáveis |
| [Rastreio via SDK](docs/SDK_TRACKING.md) | Atribuição de custos para agentes que construiu você mesmo |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações isoladas (sandboxed) do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volumes |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; execução a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anónimos de instalação e de abertura da app de desktop, e como desativá-los |

## Capturas de ecrã

Todos os números abaixo são de uma máquina real, só de leitura, sem nada preparado.

**Diz-lhe quando algo está errado, não apenas o que aconteceu.**
Dois avisos de anomalia no topo: gasto a correr 7x acima da média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes com um
sinal de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Mostra-lhe para onde foi o dinheiro, em cada janela temporal.**
$252,47 hoje, $513,15 esta semana, $1.312,92 este mês, cada um com os tokens
por trás e quanto já é coberto pela sua subscrição. Abaixo disso, cerca de
$1.128/mês discriminados como recuperáveis e $17.256/mês já poupados pela
reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Desenha como uma mensagem se torna numa resposta.**
O diagrama de fluxo em tempo real: você, o canal por onde chegou, a gateway, o
modelo a responder neste momento, e cada ferramenta que utilizou. Os nós
acendem-se à medida que o trabalho passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Todos os agentes na máquina, numa única tabela.**
O que executa, o que custou nas últimas 24 horas e ao longo da sua vida, quando
foi visto pela última vez, quem é o dono, e se uma subscrição está a cobrir a
fatura. 14 agentes aqui, 3 sessões a trabalhar, 13 em silêncio.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra para onde foi o tempo e o dinheiro de um turno, ferramenta a ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada
chamada Bash e chamada de modelo tem a sua própria barra na linha temporal, para
que o comando que correu durante 4,1 minutos e o que correu em 226ms sejam
distinguidos num relance.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Avalia o trabalho, não apenas o gasto.**
Um A esta semana: 54 tarefas correram bem, 2 mais difíceis custaram $48,57, e as
execuções com atividade insuficiente para avaliar ficam de fora da nota em vez
de serem contadas como vitórias. Cada execução difícil tem ligação ao seu trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra porque é que a janela de contexto continua a encher-se.**
715K de uma janela de 1M tokens no último turno, um pico de 83,3%, 4
compactações que ocorreram todas proativamente em vez de por overflow, e a
utilização de cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A deteção funciona sem que configure nada.**
Os detetores incorporados estão ativos desde a instalação: agente silencioso,
feed de telemetria interrompido, pico de custo, rajada de tokens, erros a
aumentar, pico de erros, limite de orçamento, assinatura de ameaça
correspondida, deteção de ferramenta de segurança, alteração da postura de
segurança. As suas próprias regras são opcionais, por cima.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Reter uma chamada arriscada é opcional, e vem desligado por predefinição.**
Eliminações recursivas, force pushes, sudo, segredos, instalações de pacotes e
chamadas de saída têm todas uma regra que pode ativar. Até o fazer, o
ClawMetry observa e não altera nada. Uma vez ativada, as chamadas
correspondentes aguardam aqui (ou no seu telemóvel) por uma aprovação ou
recusa.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mais, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Reconhecimento

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Histórico de estrelas

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licença

MIT · Criado por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
