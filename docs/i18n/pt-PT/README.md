<!-- i18n-src:88be2deff5d5 -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja o seu agente pensar.** Observabilidade em tempo real para **30 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 26. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Configuração zero. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Configuração zero: encontra os runtimes de agentes que já tem, lê-os apenas em modo de leitura e não altera nada na forma como estes funcionam.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funciona com 30 runtimes de agentes

**Grátis na aplicação open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Num plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todos os runtimes têm o mesmo painel. Execute vários em simultâneo e o seletor no cabeçalho reajusta cada separador a um deles.

Construiu o seu próprio agente com um SDK em vez disso? O interceptor também acompanha as suas chamadas LLM. Consulte [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que obtém

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com repetição
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalização de anomalias
- **Fluxo**: diagrama em tempo real das mensagens a percorrer canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas à medida que acontece
- **Estouro de contexto**: utilização da janela dimensionada por fornecedor, compactação vs. estouro forçado, além de um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os ficheiros e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, fluxo de logs em direto
- **Alertas**: limites de orçamento, picos de erro, agente offline, encaminhados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pausa chamadas de ferramentas arriscadas *antes* de serem executadas e aprova a partir do seu telemóvel ([como](docs/APPROVALS.md))

## Estouro de contexto, e o que custa observar

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como lida com o estouro da janela de contexto entre runtimes?**

Uma percentagem de utilização só é tão honesta quanto o valor pelo qual é dividida. O ClawMetry dimensiona a janela por fornecedor a partir de [uma tabela que pode ler e submeter via PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Não mede os 30 runtimes com a régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5 avaliado com a régua de 200K da Anthropic lê-se como ">100%, estourado" quando na verdade está a 75% dos 400K do GPT-5. A mesma régua esconde um turno de 130K do DeepSeek genuinamente estourado como um confortável 65%.

Cada janela é enviada com a sua proveniência: `model_table`, `explicit_marker`, `observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um indicador construído sobre uma suposição nunca é apresentado com a mesma autoridade de um construído sobre uma consulta.

O ClawMetry só consegue ver eventos de compactação nalguns runtimes. Por isso, `GET /api/context-coverage` reporta, por runtime, se um **zero significa "correu bem" ou "estamos às cegas"**. Um `0` que na verdade significa cego diz-o. [Detalhe completo](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Percurso | Adicionado ao seu agente | Padrão? |
|---|---|---|
| Leitura contínua de ficheiros de sessão (todos os 30 runtimes) | **0**. Processo separado, sem código do ClawMetry no seu agente | ligado |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada LLM, ou 0,009% de uma chamada de 5s | desligado |
| Portão de hook pré-ferramenta (cache aquecida) | **+44 ms** por chamada de ferramenta controlada, sobre um piso de 36 ms do interpretador | desligado |
| Proxy de aplicação | **+9,7 ms** por chamada LLM | desligado |

Custo no host do daemon: **2.762 eventos/seg** de ingestão, **710 bytes/evento** em disco
(67,7 MB por 100 mil eventos), e **~12% de um núcleo** de forma sustentada numa instalação com atividade elevada. Esse último número está acima do nosso próprio orçamento declarado de 5-10%, pelo que é publicado como um bug a resolver e não omitido da página.

Medido num Apple M2 Pro com `benchmarks/overhead.py`. O harness executa
cada condição num processo separado, alterna a sua ordem, e **recusa-se
a imprimir um número quando as rondas discordam quanto ao seu sinal**. Execute-o na sua própria máquina em um minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todos os percursos são medidos, incluindo os portões de hook e o proxy de aplicação, e o harness corre em Linux, macOS e Windows no CI. Dois resultados que vale a pena conhecer: o proxy custa cerca de sete vezes mais no Windows do que no Linux, e o daemon atualmente sustenta cerca de 12% de um núcleo, acima do nosso próprio orçamento de 5-10%. O JSON em bruto, o método, e o que ainda não está medido estão em
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, vista de frota, sincronização na nuvem | $9 por nó / mês |
| **Pro** | Starter + controlo e avaliação: aprovações, políticas de risco de ferramentas, avaliações, deteção de anomalias, otimizador de custos, exportação OTel, registo de auditoria à prova de adulteração | $19 por nó / mês |

Os planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença autoalojadas funcionam sem a nuvem (`clawmetry license`). A divisão exata entre grátis/pago está em
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Os seus dados permanecem na sua máquina

O ClawMetry lê ficheiros de sessão e logs locais. **Nenhum dado de sessão sai da sua máquina, a menos que execute `clawmetry connect`** — nem prompts, respostas, argumentos de ferramentas, conteúdo de ficheiros ou linhas de log. Quando se liga, o snapshot é encriptado de ponta a ponta com uma chave que nunca sai da sua máquina, e desencriptado no seu navegador. Se um nó não tiver chave, o envio é ignorado em vez de enviado em texto simples, e nenhuma resposta do servidor pode desativar isso.

Duas coisas correm por padrão antes de se ligar, ambas opcionais e nenhuma delas transportando dados de sessão: um ping anónimo de instalação e uma verificação de versão contra o PyPI. Uma instalação padrão também consulta o seu IP público uma vez para uma linha de banner de arranque. Cada destino, o que transporta e como o desativar está listado em
[docs/EGRESS.md](docs/EGRESS.md); instalações autoalojadas, reencaminhadas e isoladas (air-gapped) não fazem quaisquer chamadas de saída discricionárias.

A desencriptação acontece no seu navegador, em código que lhe é fornecido por nós. Isto costumava ser uma promessa; agora é algo que pode verificar. Cada linha que toca na sua chave vive num único ficheiro legível, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é distribuído dentro do wheel e servido tal e qual, fixado com um hash de Integridade de Subrecurso. Para confirmar que o navegador executa o que publicámos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isto não prova: nós servimos a página que carrega o ficheiro, pelo que poderíamos servir uma página diferente. Os hashes de integridade protegem-no de uma CDN comprometida, não do fornecedor. O que ganha é que qualquer substituição tem de ser deliberada, visível no código-fonte da página, e diferente de um artefacto no PyPI que qualquer pessoa pode obter. Autoalojar-se ou manter-se apenas local elimina essa dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ em macOS, Linux ou Windows, e pelo menos um runtime de agente na mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

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
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por fornecedor, compactação vs. estouro, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | O que a instrumentação custa, medido, com o harness para o reproduzir |
| [Entitlements](docs/ENTITLEMENTS.md) | Grátis vs. pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Controlo pré-execução, pontuação de risco, aprovações via telemóvel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lado, ingira OTLP de qualquer origem |
| [Traga o seu próprio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de ponta a ponta, com exemplos executáveis |
| [Acompanhamento via SDK](docs/SDK_TRACKING.md) | Atribuição de custos para agentes que construiu você mesmo |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Fluxo |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações do NVIDIA NemoClaw em sandbox |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volumes |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executar a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anónimos de instalação e de abertura da aplicação de ambiente de trabalho, e como os desativar |

## Capturas de ecrã

Cada número abaixo é de uma máquina real, apenas em modo de leitura, sem nada simulado.

**Diz-lhe quando algo está errado, não apenas o que aconteceu.**
Dois avisos de anomalia no topo: gasto a 7x a média diária, e um
pico de custo de 4,2x. Abaixo, 324 de 667 sessões recentes a apresentar um
sinal de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Mostra-lhe para onde foi o dinheiro, em cada janela temporal.**
$252,47 hoje, $513,15 esta semana, $1.312,92 este mês, cada um com os tokens
por trás e quanto disso a sua subscrição já cobre. Abaixo disso,
cerca de $1.128/mês discriminados como recuperáveis e $17.256/mês já poupados por
reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Desenha como uma mensagem se torna numa resposta.**
O diagrama de fluxo em direto: você, o canal onde chegou, o gateway, o modelo
a responder neste momento, e cada ferramenta que este utilizou. Os nós acendem-se à medida que o trabalho
os percorre.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Todos os agentes na máquina, numa única tabela.**
O que executa, o que custou nas últimas 24 horas e ao longo da sua existência, quando
foi visto pela última vez, quem é o dono, e se uma subscrição está a cobrir a
fatura. 14 agentes aqui, 3 sessões a trabalhar, 13 em silêncio.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra para onde foi o tempo e o dinheiro de um turno, ferramenta a ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada
chamada Bash e chamada de modelo tem a sua própria barra na linha do tempo, para que o comando que correu
durante 4,1 minutos e o que correu durante 226ms se distingam à primeira vista.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Avalia o trabalho, não apenas o gasto.**
Um A esta semana: 54 tarefas voltaram limpas, 2 mais problemáticas custaram $48,57, e as
execuções com atividade insuficiente para avaliar são deixadas de fora da nota em vez de
serem contadas como vitórias. Cada execução problemática liga ao seu trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra por que a janela de contexto continua a encher-se.**
715K de uma janela de 1M tokens no último turno, um pico de 83,3%, 4 compactações
que dispararam todas de forma proativa em vez de por estouro, e a utilização de
cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A deteção funciona sem que tenha de configurar nada.**
Os detetores incorporados estão ativos desde a instalação: agente ficou silencioso, o feed de telemetria
parou, pico de custo, explosão de tokens, erros a aumentar, pico de erro, limite de
orçamento, assinatura de ameaça correspondida, deteção de ferramenta de segurança, alteração na postura
de segurança. As suas próprias regras são opcionais, adicionadas por cima.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Reter uma chamada arriscada é opcional, e vem desligado.**
Eliminações recursivas, force pushes, sudo, segredos, instalações de pacotes e chamadas de saída
têm cada um uma regra que pode ativar. Até o fazer, o ClawMetry observa e
não altera nada. Uma vez ativada, as chamadas correspondentes aguardam aqui (ou no seu telemóvel)
por uma aprovação ou uma recusa.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mais, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Histórico de Estrelas

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
