<!-- i18n-src:d21bea5161e0 -->
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

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: encontra os runtimes de agentes
que já tem, lê-os em modo só de leitura e não altera nada no seu funcionamento.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funciona com 30 runtimes de agentes

**Grátis na aplicação de código aberto:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Num plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todos os runtimes têm o mesmo painel. Execute vários ao mesmo tempo e o seletor
no cabeçalho redireciona cada separador para um deles.

Construiu o seu próprio agente com um SDK? O interceptor também acompanha as
chamadas de LLM desse agente. Ver [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que obtém

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com repetição
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalização de anomalias
- **Fluxo**: diagrama ao vivo das mensagens a mover-se por canais, modelos e ferramentas
- **Cérebro (Brain)**: o fluxo de eventos de raciocínio e chamadas de ferramentas em tempo real
- **Estouro de contexto**: utilização da janela dimensionada por fornecedor, compactação vs. estouro forçado, mais um mapa por runtime do que *não* conseguimos ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os ficheiros e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de logs ao vivo
- **Alertas**: limites de orçamento, picos de erro, agente offline, encaminhados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pausar chamadas de ferramentas arriscadas *antes* de serem executadas e aprovar a partir do seu telemóvel ([como](docs/APPROVALS.md))

## Estouro de contexto, e quanto custa observar

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como lida com o estouro da janela de contexto entre runtimes?**

Uma percentagem de utilização só é honesta consoante o valor pelo qual é dividida. O ClawMetry
dimensiona a janela por fornecedor a partir de [uma tabela que pode ler e propor via
PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Não mede os 26
runtimes com a régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5
avaliado com a régua de 200K da Anthropic lê ">100%, estourado" quando na
verdade está a 75% dos 400K do GPT-5. A mesma régua esconde um turno
genuinamente estourado de 130K da DeepSeek como um confortável 65%.

Cada janela vem com a sua proveniência: `model_table`, `explicit_marker`,
`observed_floor`, ou um honesto `default` quando não conhecemos o modelo. Um
medidor construído sobre uma suposição nunca é apresentado com a mesma autoridade
que um construído sobre uma consulta.

O ClawMetry só consegue ver eventos de compactação em alguns runtimes. Por isso
`GET /api/context-coverage` reporta, por runtime, se um **zero significa
"correu limpo" ou "estamos cegos"**. Um `0` que na verdade significa cego diz-o.
[Detalhe completo](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Padrão? |
|---|---|---|
| Leitura contínua de ficheiros de sessão (todos os 30 runtimes) | **0**. Processo separado, sem código do ClawMetry no seu agente | ativado |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada de LLM, ou 0,009% de uma chamada de 5s | desativado |
| Gate de hook pré-ferramenta (cache aquecida) | **+44 ms** por chamada de ferramenta com gate, sobre um piso de 36 ms do interpretador | desativado |
| Proxy de aplicação (enforcement) | **+9,7 ms** por chamada de LLM | desativado |

Custo do daemon no host: **2.762 eventos/seg** de ingestão, **710 bytes/evento** em disco
(67,7 MB por 100 mil eventos), e **~12% de um núcleo** sustentado numa instalação
com bastante atividade. Este último número está acima do nosso próprio orçamento
declarado de 5 a 10%, por isso é publicado como um bug a perseguir em vez de
ser deixado de fora da página.

Medido num Apple M2 Pro com `benchmarks/overhead.py`. O harness executa
cada condição num processo separado, alterna a sua ordem, e **recusa-se
a imprimir um número quando as rondas discordam quanto ao seu sinal**. Execute-o
na sua própria máquina num minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todos os caminhos são medidos, incluindo os gates de hook e o proxy de aplicação,
e o harness corre em Linux, macOS e Windows no CI. Dois resultados que
vale a pena conhecer: o proxy custa cerca de sete vezes mais no Windows do que
no Linux, e o daemon atualmente sustenta cerca de 12% de um núcleo, acima do
nosso próprio orçamento de 5-10%. O JSON bruto, o método e o que ainda está
por medir estão em [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Grátis** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, vista de frota, sincronização na nuvem | $9 por nó / mês |
| **Pro** | Starter + controlo e avaliação: aprovações, políticas de risco de ferramentas, avaliações, deteção de anomalias, otimizador de custos, exportação OTel, registo de auditoria à prova de adulteração | $19 por nó / mês |

Os planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença
autoalojadas funcionam sem a nuvem (`clawmetry license`). A divisão exata entre
grátis/pago está em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Os seus dados ficam na sua máquina

O ClawMetry lê ficheiros de sessão e logs locais. **Nenhum dado de sessão sai da sua
máquina a menos que execute `clawmetry connect`** — nenhum prompt, resposta,
argumento de ferramenta, conteúdo de ficheiro ou linha de log. Quando se liga, o
instantâneo (snapshot) é cifrado de ponta a ponta com uma chave que nunca sai da
sua máquina, e decifrado no seu navegador. Se um nó não tiver chave, o envio é
ignorado em vez de ser enviado em claro, e nenhuma resposta do servidor pode
desativar isso.

Duas coisas correm por defeito antes de se ligar, ambas com opção de recusa e
nenhuma delas transportando dados de sessão: um ping anónimo de instalação e uma
verificação de versão junto do PyPI. Uma instalação padrão também consulta o seu
IP público uma vez para uma linha de banner de arranque. Todos os destinos, o que
transportam e como os desativar estão listados em
[docs/EGRESS.md](docs/EGRESS.md); instalações autoalojadas, redirecionadas e
isoladas (air-gapped) não fazem quaisquer chamadas de saída discricionárias.

A decifragem acontece no seu navegador, em código que lhe fornecemos. Isso costumava
ser uma promessa; agora é algo que pode verificar. Cada linha que toca na sua
chave está num único ficheiro legível, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é distribuído dentro do wheel e servido tal como está, fixado com um hash de
Integridade de Subrecurso (SRI). Para confirmar que o navegador executa o que
publicámos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

O que isto não prova: servimos a página que carrega o ficheiro, por isso
poderíamos servir uma página diferente. Os hashes de integridade protegem-no de
um CDN comprometido, não do fornecedor. O que ganha é que qualquer substituição
tem de ser deliberada, visível no código-fonte da página, e diferente de um
artefacto no PyPI que qualquer pessoa pode obter. Autoalojar ou manter-se
apenas local remove essa dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ em macOS, Linux ou Windows, e pelo menos um runtime de agente
na mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por fornecedor, compactação vs. estouro, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | O que a instrumentação custa, medido, com o harness para reproduzir |
| [Direitos (Entitlements)](docs/ENTITLEMENTS.md) | Grátis vs. pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Bloqueio pré-execução, pontuação de risco, aprovações pelo telemóvel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportar traces para qualquer lugar, ingerir OTLP de qualquer fonte |
| [Acompanhamento via SDK](docs/SDK_TRACKING.md) | Atribuição de custos para agentes que você mesmo construiu |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Fluxo |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações isoladas (sandboxed) do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volumes |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executar a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anónimos de instalação e de abertura do desktop, e como os desativar |

## Capturas de ecrã

Cada número abaixo vem de uma máquina real, em modo só de leitura, sem nada preparado antecipadamente.

**Diz-lhe quando algo está errado, não só o que aconteceu.**
Dois avisos de anomalia no topo: gasto a correr 7x acima da média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes com um
sinal de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Mostra-lhe para onde foi o dinheiro, em cada janela temporal.**
$252,47 hoje, $513,15 esta semana, $1.312,92 este mês, cada um com os tokens
por trás e quanto disso já está coberto pela sua subscrição. Abaixo disso,
cerca de $1.128/mês discriminados como recuperáveis e $17.256/mês já poupados
pela reutilização de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Desenha como uma mensagem se transforma numa resposta.**
O diagrama de fluxo ao vivo: você, o canal por onde chegou, o gateway, o modelo
a responder neste momento, e cada ferramenta que utilizou. Os nós acendem-se
à medida que o trabalho passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Todos os agentes na máquina, numa única tabela.**
O que executa, quanto custou nas últimas 24 horas e ao longo da sua vida útil,
quando foi visto pela última vez, quem é o proprietário, e se uma subscrição
está a cobrir a conta. 14 agentes aqui, 3 sessões a trabalhar, 13 em silêncio.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Mostra para onde foi o tempo e o dinheiro de um turno, ferramenta a ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada
chamada Bash e chamada ao modelo tem a sua própria barra na linha do tempo,
para distinguir num relance o comando que correu durante 4,1 minutos daquele
que correu em 226ms.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Avalia o trabalho, não apenas o gasto.**
Um A esta semana: 54 tarefas correram bem, 2 mais difíceis custaram $48,57, e
as execuções com atividade insuficiente para avaliar ficam de fora da nota em
vez de serem contadas como vitórias. Cada execução difícil tem uma ligação ao
seu traço (trace).

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Mostra por que a janela de contexto continua a encher-se.**
715K de uma janela de 1M de tokens no último turno, um pico de 83,3%, 4
compactações que dispararam todas de forma proativa em vez de por estouro, mais
a utilização de cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A deteção funciona sem precisar de configurar nada.**
Os detetores incorporados estão ativos desde a instalação: agente ficou em
silêncio, feed de telemetria parou, pico de custo, rajada de tokens, erros a
aumentar, pico de erros, limite de orçamento atingido, assinatura de ameaça
correspondida, resultado de ferramenta de segurança, mudança na postura de
segurança. As suas próprias regras são opcionais, por cima destas.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Reter uma chamada arriscada é opcional, e vem desativado.**
Eliminações recursivas, force pushes, sudo, segredos, instalações de pacotes e
chamadas de saída têm cada uma uma regra que pode ativar. Até o fazer, o
ClawMetry observa e não altera nada. Depois de ativar uma, as chamadas
correspondentes esperam aqui (ou no seu telemóvel) por uma aprovação ou recusa.

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
