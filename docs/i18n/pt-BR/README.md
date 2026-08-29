<!-- i18n-src:d21bea5161e0 -->
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

> 🌐 **Leia isso em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: ele encontra os runtimes de agentes que você já tem, lê-os apenas para leitura e não muda nada na forma como eles funcionam.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funciona com 30 runtimes de agentes

**Gratuito no app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Em um plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todo runtime recebe o mesmo painel. Execute vários ao mesmo tempo e o seletor no cabeçalho reajusta cada aba para um deles.

Construiu seu próprio agente usando um SDK em vez disso? O interceptador também rastreia as chamadas de LLM dele. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que você tem

- **Sessões e transcrições**: o que cada agente fez, turno por turno, com replay
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalizações de anomalia
- **Fluxo**: diagrama ao vivo das mensagens circulando por canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas em tempo real
- **Estouro de contexto**: utilização da janela dimensionada por provedor, compactação versus estouro forçado, além de um mapa por runtime do que *não conseguimos* ver ([como](docs/CONTEXT_BLOWOUT.md))
- **Memória e skills**: os arquivos e skills que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de logs ao vivo
- **Alertas**: limites de orçamento, picos de erro, agente offline, roteados para Slack, Discord, PagerDuty, Telegram, E-mail
- **Aprovações**: pause chamadas de ferramentas arriscadas *antes* que sejam executadas e aprove pelo celular ([como](docs/APPROVALS.md))

## Estouro de contexto, e quanto custa observar

Duas perguntas que vale a pena responder antes de confiar em qualquer ferramenta de comparação de agentes.

**Como ele lida com o estouro da janela de contexto entre runtimes?**

Uma porcentagem de utilização só é honesta conforme o valor pelo qual ela é dividida. O ClawMetry dimensiona a janela por provedor a partir de [uma tabela que você pode ler e enviar um PR](clawmetry/context_windows.py), cobrindo Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama e GLM. Ele não mede os 26 runtimes com a régua de um único fornecedor. Isso importa: um turno de 300K do GPT-5 medido contra os 200K da Anthropic mostra ">100%, estourado" quando na verdade está em 75% dos 400K do GPT-5.
A mesma régua esconde um turno de DeepSeek de 130K genuinamente estourado como um confortável 65%.

Toda janela vem com sua procedência: `model_table`, `explicit_marker`,
`observed_floor`, ou um `default` honesto quando não sabemos o modelo. Um
medidor construído sobre um palpite nunca é exibido com a mesma autoridade que um construído sobre
uma consulta real.

O ClawMetry só consegue ver eventos de compactação em alguns runtimes. Então
`GET /api/context-coverage` informa, por runtime, se um **zero significa
"rodou limpo" ou "estamos cegos"**. Um `0` que na verdade significa cego diz isso.
[Detalhes completos](docs/CONTEXT_BLOWOUT.md)

**Quanto custa a instrumentação?**

| Caminho | Adicionado ao seu agente | Padrão? |
|---|---|---|
| Leitura contínua de arquivos de sessão (todos os 30 runtimes) | **0**. Processo separado, nenhum código do ClawMetry no seu agente | ligado |
| Interceptador HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por chamada de LLM, ou 0,009% de uma chamada de 5s | desligado |
| Gate de hook pré-ferramenta (cache aquecido) | **+44 ms** por chamada de ferramenta bloqueada, sobre um piso de interpretador de 36 ms | desligado |
| Proxy de aplicação de políticas | **+9,7 ms** por chamada de LLM | desligado |

Custo do host do daemon: **2.762 eventos/s** de ingestão, **710 bytes/evento** em disco
(67,7 MB por 100 mil eventos), e **~12% de um núcleo** sustentado em uma instalação movimentada. Esse
último número está acima do nosso próprio orçamento declarado de 5-10%, então é
publicado como um bug a ser resolvido em vez de omitido da página.

Medido em um Apple M2 Pro com `benchmarks/overhead.py`. O harness executa
cada condição em um processo separado, alterna a ordem entre elas, e **se recusa
a exibir um número quando as rodadas discordam sobre seu sinal**. Execute-o na sua própria
máquina em um minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Todo caminho é medido, incluindo os gates de hook e o proxy de aplicação de políticas,
e o harness roda em Linux, macOS e Windows no CI. Dois resultados que vale a pena
conhecer: o proxy custa cerca de sete vezes mais no Windows do que no Linux, e
o daemon atualmente sustenta cerca de 12% de um núcleo, acima do nosso próprio orçamento de 5-10%.
O JSON bruto, o método e o que ainda não foi medido estão em
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Gratuito** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, somente local | $0 |
| **Starter** | Todos os outros runtimes acima, visão de frota, sincronização em nuvem | $9 por nó / mês |
| **Pro** | Starter + controle e avaliação: aprovações, políticas de risco de ferramentas, avaliações, detecção de anomalias, otimizador de custo, exportação OTel, log de auditoria à prova de adulteração | $19 por nó / mês |

Planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Chaves de licença autogerenciadas
funcionam sem a nuvem (`clawmetry license`). A divisão exata entre gratuito e pago está
em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Seus dados permanecem na sua máquina

O ClawMetry lê arquivos de sessão e logs locais. **Nenhum dado de sessão sai da sua máquina
a menos que você execute `clawmetry connect`** — sem prompts, respostas, argumentos de ferramentas, conteúdo de arquivos
ou linhas de log. Quando você conecta, o snapshot é criptografado de ponta a ponta
com uma chave que nunca sai da sua máquina, e descriptografado no seu navegador. Se um
nó não tiver chave, o envio é ignorado em vez de enviado sem criptografia, e nenhuma
resposta do servidor pode desativar isso.

Duas coisas rodam por padrão antes de você conectar, ambas opcionais para desativar e nenhuma
carregando dados de sessão: um ping anônimo de instalação e uma verificação de versão contra
o PyPI. Uma instalação padrão também consulta seu IP público uma vez para uma linha de banner
inicial. Todo destino, o que ele carrega e como desativá-lo estão listados em
[docs/EGRESS.md](docs/EGRESS.md); instalações autogerenciadas, redirecionadas e isoladas de rede
não fazem nenhuma chamada de saída opcional.

A descriptografia acontece no seu navegador, em código que nós fornecemos a você. Isso costumava ser
uma promessa; agora é algo que você pode verificar. Toda linha que toca sua chave
está em um único arquivo legível, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que é enviado dentro do wheel e servido literalmente, fixado com um hash de Integridade de Sub-recurso.
Para confirmar que o navegador executa o que publicamos:

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
que qualquer um pode buscar. Autogerenciar ou permanecer somente local remove a
dependência por completo.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Precisa de Python 3.8+ no macOS, Linux ou Windows, e pelo menos um runtime de agente na
mesma máquina. Instruções do Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Estouro de contexto](docs/CONTEXT_BLOWOUT.md) | Janelas por provedor, compactação versus estouro, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | Quanto custa a instrumentação, medido, com o harness para reproduzir |
| [Direitos de uso](docs/ENTITLEMENTS.md) | Gratuito versus pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Bloqueio pré-execução, pontuação de risco, aprovações pelo celular |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lugar, ingira OTLP de qualquer coisa |
| [Rastreamento via SDK](docs/SDK_TRACKING.md) | Atribuição de custo para agentes que você mesmo construiu |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat mostrados no Fluxo |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações isoladas do NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volume |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executando a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anônimos de instalação e abertura do desktop, e como desativá-los |

## Capturas de tela

Todo número abaixo é de uma máquina real, apenas leitura, sem nada preparado.

**Ele avisa quando algo está errado, não só o que aconteceu.**
Dois banners de anomalia no topo: gasto rodando 7x acima da média diária, e um
pico de custo de 4,2x. Abaixo deles, 324 de 667 sessões recentes carregando um sinal
de desperdício, discriminado por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ele mostra para onde foi o dinheiro, em cada janela.**
$252,47 hoje, $513,15 nesta semana, $1.312,92 neste mês, cada um com os tokens
por trás e quanto disso sua assinatura já cobre. Abaixo disso,
cerca de $1.128/mês discriminados como recuperáveis e $17.256/mês já economizados por
reuso de cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Ele desenha como uma mensagem se torna uma resposta.**
O diagrama de fluxo ao vivo: você, o canal pelo qual ela chegou, o gateway, o modelo
respondendo agora, e cada ferramenta que ele acionou. Os nós se acendem à medida que o trabalho
passa por eles.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Cada agente na máquina, em uma única tabela.**
O que ele executa, quanto custou nas últimas 24 horas e ao longo de sua vida útil, quando
foi visto pela última vez, quem é o dono, e se uma assinatura está cobrindo a
conta. 14 agentes aqui, 3 sessões trabalhando, 13 quietas.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ele mostra para onde foi o tempo e o dinheiro de um turno, ferramenta por ferramenta.**
Um turno de uma sessão real: 11 ferramentas em 11,2 minutos por $1,16. Cada chamada de Bash
e chamada de modelo tem sua própria barra na linha do tempo, então o comando que rodou
por 4,1 minutos e o que rodou por 226ms são diferenciados à primeira vista.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ele avalia o trabalho, não só o gasto.**
Um A nesta semana: 54 tarefas voltaram limpas, 2 mais difíceis custaram $48,57, e as
execuções com atividade insuficiente para julgar são deixadas de fora da nota em vez de
serem contadas como vitórias. Cada execução mais difícil tem link para seu rastro.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ele mostra por que a janela de contexto continua enchendo.**
715K de uma janela de 1M tokens no turno mais recente, um pico de 83,3%, 4 compactações
que dispararam proativamente em vez de por estouro, e a utilização de
cada turno por trás disso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**A detecção funciona sem você configurar nada.**
Os detectores integrados estão ativos desde a instalação: agente ficou quieto, feed de telemetria
parou, pico de custo, explosão de tokens, erros crescendo, pico de erro, limite
de orçamento atingido, assinatura de ameaça correspondida, achado de ferramenta de segurança, postura de segurança
alterada. Suas próprias regras são opcionais, adicionadas por cima.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Reter uma chamada arriscada é opcional, e vem desligado.**
Exclusões recursivas, force pushes, sudo, segredos, instalações de pacotes e chamadas de saída
recebem cada uma uma regra que você pode ativar. Até você ativar, o ClawMetry observa e
não muda nada. Uma vez ativada, chamadas correspondentes esperam aqui (ou no seu celular)
por uma aprovação ou negação.

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

MIT · Construído por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
