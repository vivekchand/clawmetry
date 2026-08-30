<!-- i18n-src:9767c8001c9c -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para **30 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 26. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Configuração zero. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Configuração zero: ele encontra os runtimes de agentes
que você já tem, os lê em modo somente leitura e não muda nada em como eles funcionam.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funciona com 30 runtimes de agentes

**Gratuito no app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Em um plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todo runtime recebe o mesmo painel. Rode vários ao mesmo tempo e o seletor no
cabeçalho reajusta cada aba para um deles.

Construiu seu próprio agente com um SDK em vez disso? O interceptor rastreia
suas chamadas de LLM também. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que você ganha

- **Sessões e transcrições**: o que cada agente fez, turno por turno, com replay
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalizadores de anomalia
- **Flow**: diagrama ao vivo das mensagens passando por canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas conforme acontece
- **Estouro de contexto**: utilização da janela dimensionada por provedor, compactação vs. estouro forçado, além de um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os arquivos e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de log ao vivo
- **Alertas**: limites de orçamento, picos de erro, agente offline, roteados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pause chamadas de ferramenta arriscadas *antes* de rodarem e aprove pelo celular ([como](docs/APPROVALS.md))

## Estouro de contexto, e quanto custa observar

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como ele lida com o estouro da janela de contexto entre runtimes?**

Uma porcentagem de utilização só é honesta na medida do que ela divide. O ClawMetry
dimensiona a janela por provedor a partir de [uma tabela que você pode ler e
enviar um PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Ele não mede os 26 runtimes com a
régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5 avaliado
contra os 200K da Anthropic lê ">100%, estourado" quando na verdade está em 75%
dos 400K do GPT-5. A mesma régua esconde um turno de 130K do DeepSeek genuinamente
estourado como um confortável 65%.

Toda janela vem com sua procedência: `model_table`, `explicit_marker`,
`observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um
medidor construído sobre um palpite nunca é renderizado com a mesma autoridade
de um construído sobre uma consulta real.

O ClawMetry só consegue ver eventos de compactação em alguns runtimes. Por isso
`GET /api/context-coverage` relata, por runtime, se um **zero significa
"rodou limpo" ou "estamos cegos"**. Um `0` que na verdade significa cego diz isso.
[Detalhes completos](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Padrão? |
|---|---|---|
| Leitura contínua de arquivos de sessão (todos os 30 runtimes) | **0**. Processo separado, nenhum código do ClawMetry no seu agente | ativado |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada de LLM, ou 0,009% de uma chamada de 5s | desativado |
| Gate de hook pré-ferramenta (cache aquecido) | **+44 ms** por chamada de ferramenta com gate, sobre um piso de 36 ms do interpretador | desativado |
| Proxy de enforcement | **+9,7 ms** por chamada de LLM | desativado |

Custo do host do daemon: **2.762 eventos/s** de ingestão, **710 bytes/evento**
em disco (67,7 MB por 100 mil eventos), e **~12% de um core** sustentado em uma
instalação movimentada. Esse último número está acima do nosso próprio
orçamento declarado de 5-10%, então é publicado como um bug a ser perseguido,
não deixado de fora da página.

Medido em um Apple M2 Pro com `benchmarks/overhead.py`. O harness roda cada
condição em um processo separado, alterna a ordem entre elas, e **se recusa a
imprimir um número quando as rodadas discordam sobre seu sinal**. Rode você
mesmo na sua máquina em um minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todo caminho é medido, incluindo os gates de hook e o proxy de enforcement, e
o harness roda em Linux, macOS e Windows no CI. Dois resultados que vale a
pena conhecer: o proxy custa cerca de sete vezes mais no Windows do que no
Linux, e o daemon atualmente sustenta cerca de 12% de um core, acima do nosso
próprio orçamento de 5-10%. O JSON bruto, o método, e o que ainda não foi
medido estão em [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, visão de frota, sincronização em nuvem | $9 por nó / mês |
| **Pro** | Starter + controle e avaliação: aprovações, políticas de risco de ferramentas, avaliações, detecção de anomalias, otimizador de custos, exportação OTel, log de auditoria à prova de adulteração | $19 por nó / mês |

Planos anuais, Enterprise e os números atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Chaves de licença
auto-hospedadas funcionam sem a nuvem (`clawmetry license`). A divisão exata
entre gratuito/pago está em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Seus dados ficam na sua máquina

O ClawMetry lê arquivos de sessão e logs locais. **Nenhum dado de sessão sai da
sua máquina a menos que você rode `clawmetry connect`** — sem prompts, respostas,
argumentos de ferramentas, conteúdo de arquivos ou linhas de log. Quando você
conecta, o snapshot é criptografado de ponta a ponta com uma chave que nunca
sai da sua máquina, e descriptografado no seu navegador. Se um nó não tem uma
chave, o upload é ignorado em vez de enviado sem criptografia, e nenhuma
resposta do servidor pode desligar isso.

Duas coisas rodam por padrão antes de você conectar, ambas opcionais (opt-out)
e nenhuma carregando dados de sessão: um ping anônimo de instalação e uma
verificação de versão contra o PyPI. Uma instalação padrão também consulta seu
IP público uma vez para uma linha de banner de inicialização. Todo destino, o
que ele carrega e como desativá-lo estão listados em
[docs/EGRESS.md](docs/EGRESS.md); instalações auto-hospedadas, redirecionadas
e isoladas (air-gapped) não fazem nenhuma chamada de saída discricionária.

A descriptografia acontece no seu navegador, em código que nós servimos a
você. Isso costumava ser uma promessa; agora é algo que você pode verificar.
Toda linha que toca sua chave vive em um único arquivo legível,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), que é
distribuído dentro do wheel e servido verbatim, fixado com um hash de
Subresource Integrity. Para confirmar que o navegador roda o que publicamos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isso não prova: nós servimos a página que carrega o arquivo, então
poderíamos servir uma página diferente. Hashes de integridade te protegem de
um CDN comprometido, não do fornecedor. O que você ganha é que qualquer
substituição precisa ser deliberada, visível no código-fonte da página, e
diferente de um artefato no PyPI que qualquer um pode buscar. Auto-hospedar
ou permanecer apenas local remove a dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ em macOS, Linux ou Windows, e pelo menos um runtime de
agente na mesma máquina. Instruções do Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Docs

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por provedor, compactação vs. estouro, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | O que a instrumentação custa, medido, com o harness para reproduzir |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito vs. pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Gate de pré-execução, pontuação de risco, aprovações pelo celular |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lugar, ingira OTLP de qualquer coisa |
| [Traga seu próprio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de ponta a ponta, com exemplos executáveis |
| [Rastreamento de SDK](docs/SDK_TRACKING.md) | Atribuição de custo para agentes que você mesmo construiu |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações sandboxed do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volume |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; rodando a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anônimos de instalação e de abertura do desktop, e como desativá-los |

## Capturas de tela

Cada número abaixo vem de uma máquina real, somente leitura, sem nada preparado.

**Ele te diz quando algo está errado, não só o que aconteceu.**
Dois banners de anomalia no topo: gasto rodando 7x acima da média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes carregando um
sinal de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ele mostra para onde foi o dinheiro, em cada janela de tempo.**
$252,47 hoje, $513,15 nesta semana, $1.312,92 neste mês, cada um com os tokens
por trás e quanto disso sua assinatura já cobre. Abaixo disso, cerca de
$1.128/mês discriminados como recuperáveis e $17.256/mês já economizados pela
reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Ele desenha como uma mensagem vira uma resposta.**
O diagrama de fluxo ao vivo: você, o canal pelo qual ela chegou, o gateway, o
modelo respondendo agora mesmo, e cada ferramenta que ele acionou. Os nós
acendem conforme o trabalho passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Cada agente na máquina, em uma única tabela.**
O que roda, quanto custou nas últimas 24 horas e ao longo de sua vida útil,
quando foi visto pela última vez, quem é o dono, e se uma assinatura está
cobrindo a conta. 14 agentes aqui, 3 sessões trabalhando, 13 quietos.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ele mostra para onde foi o tempo e o dinheiro de um turno, ferramenta por ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada
chamada de Bash e chamada de modelo ganha sua própria barra na linha do tempo,
para que o comando que rodou por 4,1 minutos e o que rodou por 226ms sejam
distinguidos num relance.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ele avalia o trabalho, não só o gasto.**
Um A nesta semana: 54 tarefas voltaram limpas, 2 mais difíceis custaram
$48,57, e as execuções com atividade insuficiente para julgar ficam de fora da
nota em vez de serem contadas como vitórias. Cada execução difícil linka para
seu trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ele mostra por que a janela de contexto continua enchendo.**
715K de uma janela de 1M de tokens no último turno, um pico de 83,3%, 4
compactações que dispararam todas proativamente em vez de por estouro, além da
utilização de cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A detecção roda sem você configurar nada.**
Os detectores integrados estão ativos desde a instalação: agente ficou quieto,
feed de telemetria parou, pico de custo, rajada de tokens, erros subindo,
pico de erro, limite de orçamento, assinatura de ameaça correspondida,
descoberta de ferramenta de segurança, postura de segurança alterada. Suas
próprias regras são opcionais, além disso.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Segurar uma chamada arriscada é opcional, e vem desligado.**
Exclusões recursivas, force pushes, sudo, segredos, instalações de pacotes e
chamadas de saída recebem cada uma uma regra que você pode ativar. Até você
ativar, o ClawMetry observa e não muda nada. Uma vez ativada, chamadas
correspondentes esperam aqui (ou no seu celular) por uma aprovação ou uma
negação.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mais, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Histórico de estrelas

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
