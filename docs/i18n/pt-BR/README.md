<!-- i18n-src:61beb8393e2f -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Um agente pode fazer cem chamadas de ferramentas sem fazer progresso.** O ClawMetry
lê os arquivos de sessão que seus agentes de código já escrevem, e reúne a linha do tempo,
as chamadas de ferramentas e quaisquer dados de tokens e custo que o runtime exponha em uma
única visão — para que você consiga distinguir uma execução longa que está funcionando de uma que está travada.

Funciona com **30 runtimes de agentes de IA** — Claude Code, OpenAI Codex, Hermes, OpenClaw e mais 26. Um único painel para toda a sua frota de agentes. ([a lista completa](SUPPORTED_RUNTIMES.txt), gerada a partir do catálogo.)

> 🌐 **Leia em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: ele encontra os runtimes de agentes
que você já tem, lê-os em modo somente leitura e não muda nada na forma como eles funcionam.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Antes de instalar

| | |
|---|---|
| **O que faz** | Lê os arquivos de sessão e logs que seus agentes já escrevem. Sem SDK, sem alteração de código, sem instrumentação no seu app. |
| **O que você vê** | Linha do tempo da sessão, replay ferramenta por ferramenta, detalhamento de tokens e custo, e sinais de trajetória (loops, falhas repetidas) — por runtime. |
| **O que é grátis** | `pip install clawmetry` lê **OpenClaw, NVIDIA NemoClaw e Goose** sem conta, sem chave e sem chamada de rede. Os outros 27 — Claude Code, Codex, Cursor e o restante — são lidos pelo complemento de código fechado `clawmetry-pro`, que vem com o teste gratuito de 7 dias ou um plano — veja [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para a divisão exata. |
| **Como começar** | `pip install clawmetry && clawmetry`, depois abra localhost:8900. Ainda não tem agentes nesta máquina? `clawmetry --sample` abre com três sessões sintéticas rotuladas. |
| **O que sai da sua máquina** | Nenhum dado de sessão, a menos que você execute `clawmetry connect`. Duas coisas rodam por padrão, ambas opcionais (opt-out) e nenhuma delas carrega conteúdo de sessão: um ping de instalação anônimo e uma verificação de versão no PyPI. Todo destino está inventariado em [docs/EGRESS.md](docs/EGRESS.md), reconstruído a partir de uma captura de tráfego em vez da leitura de comentários. |

Duas limitações que vale conhecer antes de julgar o resultado: os runtimes expõem dados
muito diferentes (alguns não publicam custo algum — [a matriz](docs/compatibility.md)
mostra quais, por runtime), e observar uma ação não é o mesmo que conseguir
bloqueá-la ([quais controles são reais, por runtime](docs/APPROVALS.md)).


## Funciona com 30 runtimes de agentes

**Grátis no app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Em um plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todo runtime recebe o mesmo painel. Execute vários ao mesmo tempo e o seletor no
cabeçalho reajusta cada aba para um deles.

Construiu seu próprio agente sobre um SDK em vez disso? O interceptador rastreia suas chamadas de LLM
também. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que você ganha

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com replay
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalizadores de anomalia
- **Fluxo**: diagrama ao vivo das mensagens passando por canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas conforme acontece
- **Estouro de contexto**: utilização da janela dimensionada por provedor, compactação vs. overflow forçado, além de um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os arquivos e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de log ao vivo
- **Alertas**: limites de orçamento, picos de erro, agente offline, roteados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pausar chamadas de ferramentas arriscadas *antes* de elas executarem e aprovar pelo celular ([como](docs/APPROVALS.md))

## Estouro de contexto, e quanto custa observar

Duas perguntas que vale responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como isso lida com o estouro da janela de contexto entre runtimes?**

Uma porcentagem de utilização só é tão honesta quanto o valor pelo qual ela divide.
O ClawMetry dimensiona a janela por provedor a partir de [uma tabela que você pode ler e
enviar um PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Ele não mede os 30
runtimes com a régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5
avaliado contra os 200K da Anthropic aparece como ">100%, estourado" quando na verdade está em 75% dos
400K do GPT-5. A mesma régua esconde um turno de 130K do DeepSeek genuinamente estourado
como um confortável 65%.

Toda janela vem com sua procedência: `model_table`, `explicit_marker`,
`observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um
medidor construído sobre um palpite nunca é renderizado com a mesma autoridade que um construído sobre
uma consulta.

O ClawMetry só consegue ver eventos de compactação em alguns runtimes. Por isso
`GET /api/context-coverage` informa, por runtime, se um **zero significa
"rodou limpo" ou "estamos cegos"**. Um `0` que na verdade significa cego diz isso.
[Detalhes completos](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Padrão? |
|---|---|---|
| Leitura contínua de arquivo de sessão (todos os 30 runtimes) | **0**. Processo separado, nenhum código do ClawMetry no seu agente | ativado |
| Interceptador HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada de LLM, ou 0,009% de uma chamada de 5s | desativado |
| Gate de hook pré-ferramenta (cache aquecido) | **+44 ms** por chamada de ferramenta controlada, acima de um piso de interpretador de 36 ms | desativado |
| Proxy de aplicação | **+9,7 ms** por chamada de LLM | desativado |

Custo do host do daemon: **2.762 eventos/s** de ingestão, **710 bytes/evento** em disco
(67,7 MB por 100 mil eventos), e **~12% de um núcleo** sustentado em uma instalação
movimentada. Esse último número está acima do nosso próprio orçamento declarado de 5-10%, então é
publicado como um bug a ser perseguido em vez de ser deixado fora da página.

Medido em um Apple M2 Pro com `benchmarks/overhead.py`. O harness executa
cada condição em um processo separado, alterna a ordem delas, e **se recusa
a imprimir um número quando as rodadas discordam sobre o sinal**. Execute-o na sua própria
máquina em um minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todo caminho é medido, incluindo os gates de hook e o proxy de aplicação,
e o harness roda em Linux, macOS e Windows no CI. Dois resultados que vale
conhecer: o proxy custa cerca de sete vezes mais no Windows do que no Linux, e
o daemon atualmente sustenta cerca de 12% de um núcleo, acima do nosso próprio orçamento de 5-10%.
O JSON bruto, o método e o que ainda não foi medido estão em
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os demais runtimes acima, visão de frota, sincronização em nuvem | $9 por nó / mês |
| **Pro** | Starter + controle e avaliação: aprovações, políticas de risco de ferramentas, avaliações, detecção de anomalias, otimizador de custo, exportação OTel, log de auditoria à prova de adulteração | $19 por nó / mês |

Planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença
autohospedadas funcionam sem a nuvem (`clawmetry license`). A divisão exata entre gratuito e pago está
em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Seus dados permanecem na sua máquina

O ClawMetry lê arquivos de sessão e logs locais. **Nenhum dado de sessão sai da sua máquina
a menos que você execute `clawmetry connect`** — nenhum prompt, resposta, argumento de ferramenta, conteúdo
de arquivo ou linha de log. Quando você conecta, o snapshot é criptografado de ponta a ponta
com uma chave que nunca sai da sua máquina, e descriptografado no seu navegador. Se um
nó não tem chave, o upload é ignorado em vez de ser enviado sem criptografia, e nenhuma
resposta do servidor pode desligar isso.

Duas coisas rodam por padrão antes de você conectar, ambas opcionais (opt-out) e nenhuma
carregando dados de sessão: um ping de instalação anônimo e uma verificação de versão contra o
PyPI. Uma instalação padrão também consulta seu IP público uma vez para uma linha de banner
na inicialização. Cada destino, o que ele carrega e como desativá-lo estão listados em
[docs/EGRESS.md](docs/EGRESS.md); instalações autohospedadas, redirecionadas e isoladas de rede
não fazem nenhuma chamada de saída discricionária.

A descriptografia acontece no seu navegador, em código que nós servimos a você. Isso costumava ser
uma promessa; agora é algo que você pode verificar. Cada linha que toca na sua chave
vive em um único arquivo legível, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é embarcado dentro do wheel e servido literalmente, fixado com um hash de Integridade
de Sub-recurso. Para confirmar que o navegador executa o que publicamos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isso não prova: nós servimos a página que carrega o arquivo, então poderíamos
servir uma página diferente. Hashes de integridade protegem você de um CDN comprometido,
não do fornecedor. O que você ganha é que qualquer substituição precisa ser
deliberada, visível no código-fonte da página, e diferente de um artefato no PyPI
que qualquer pessoa pode buscar. Autohospedar ou permanecer apenas local remove a
dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ no macOS, Linux ou Windows, e pelo menos um runtime de agente na
mesma máquina. Instruções do Docker: [docs/DOCKER.md](docs/DOCKER.md).

Ou deixe o agente configurar para você. A skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ensina o Claude Code, Codex, Cursor, Gemini CLI, Copilot ou OpenCode a
instalar o ClawMetry, relatar o que os agentes na máquina estão fazendo e gastando,
parar uma sessão sob demanda, e reter chamadas de ferramentas arriscadas para aprovação:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por provedor, compactação vs. overflow, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | Quanto custa a instrumentação, medido, com o harness para reproduzir |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito vs. pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Controle pré-execução, pontuação de risco, aprovações pelo celular |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lugar, ingira OTLP de qualquer coisa |
| [Traga seu próprio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de ponta a ponta, com exemplos executáveis |
| [Rastreamento via SDK](docs/SDK_TRACKING.md) | Atribuição de custo para agentes que você mesmo construiu |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Fluxo |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações isoladas (sandboxed) do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volume |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executando a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anônimos de instalação e de abertura do desktop, e como desativá-los |

## Capturas de tela

Todo número abaixo vem de uma máquina real, somente leitura, sem nada simulado.

**Ele te diz quando algo está errado, não apenas o que aconteceu.**
Dois banners de anomalia no topo: gasto rodando 7x acima da média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes carregando um sinal
de desperdício, discriminadas por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ele mostra para onde foi o dinheiro, em cada janela de tempo.**
$252,47 hoje, $513,15 esta semana, $1.312,92 este mês, cada um com os tokens
por trás e quanto disso sua assinatura já cobre. Abaixo disso, cerca de
$1.128/mês discriminados como recuperáveis e $17.256/mês já economizados por
reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Ele desenha como uma mensagem se torna uma resposta.**
O diagrama de fluxo ao vivo: você, o canal pelo qual ela chegou, o gateway, o modelo
respondendo agora mesmo, e cada ferramenta que ele acionou. Os nós se acendem conforme o trabalho
passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Todo agente na máquina, em uma única tabela.**
O que ele executa, quanto custa nas últimas 24 horas e ao longo de sua vida útil, quando
foi visto pela última vez, quem é o dono, e se uma assinatura está cobrindo a
conta. 14 agentes aqui, 3 sessões trabalhando, 13 quietas.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ele mostra para onde foi o tempo e o dinheiro de um turno, ferramenta por ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada chamada
Bash e chamada de modelo recebe sua própria barra na linha do tempo, então o comando que rodou
por 4,1 minutos e o que rodou por 226ms são diferenciados de relance.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ele avalia o trabalho, não apenas o gasto.**
Um A nesta semana: 54 tarefas voltaram limpas, 2 tarefas problemáticas custaram $48,57, e as
execuções com atividade insuficiente para julgar são deixadas de fora da nota em vez de
serem contadas como vitórias. Cada execução problemática tem link para seu trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ele mostra por que a janela de contexto continua enchendo.**
715K de uma janela de 1M de tokens no último turno, um pico de 83,3%, 4 compactações
que dispararam de forma proativa em vez de por overflow, e a utilização de
cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A detecção funciona sem você configurar nada.**
Os detectores integrados estão ativos desde a instalação: agente ficou quieto, feed de telemetria
parou, pico de custo, explosão de tokens, erros subindo, pico de erros, limite
de orçamento atingido, assinatura de ameaça correspondida, achado de ferramenta de segurança, postura de segurança
alterada. Suas próprias regras são opcionais, além dessas.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Reter uma chamada arriscada é opcional (opt-in), e vem desativado.**
Exclusões recursivas, force pushes, sudo, segredos, instalações de pacotes e chamadas de saída
recebem cada uma uma regra que você pode ativar. Até você ativar, o ClawMetry observa e
não muda nada. Depois que uma é ativada, as chamadas correspondentes esperam aqui (ou no seu celular)
por uma aprovação ou negação.

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

MIT · Construído por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
