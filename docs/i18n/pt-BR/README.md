<!-- i18n-src:dc34072b2955 -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para **23 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 19 outros. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um único comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: ele encontra os runtimes
de agentes que você já tem, os lê em modo somente leitura e não muda nada na forma como eles rodam.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 23 runtimes de agentes

**Gratuito no app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**Em um plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Todo runtime recebe o mesmo painel. Rode vários ao mesmo tempo e o seletor no
cabeçalho reajusta cada aba para um deles.

Construiu seu próprio agente com um SDK em vez disso? O interceptor rastreia
as chamadas de LLM dele também. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que você ganha

- **Sessões e transcrições**: o que cada agente fez, turno a turno, com replay
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalizadores de anomalia
- **Flow**: diagrama ao vivo das mensagens passando por canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas em tempo real
- **Memória e habilidades**: os arquivos e habilidades que cada runtime realmente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, stream de logs ao vivo
- **Alertas**: limites de orçamento, picos de erro, agente offline, roteados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pause chamadas de ferramentas arriscadas *antes* que elas rodem e aprove pelo celular ([como funciona](docs/APPROVALS.md))

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, visão de frota, sincronização em nuvem | $9 por nó / mês |
| **Pro** | Starter + governança: aprovações, políticas de risco de ferramentas, avaliações, detecção de anomalias, otimizador de custos, exportação OTel | $19 por nó / mês |

Planos anuais, Enterprise e os valores atuais estão em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Chaves de licença
autogerenciadas funcionam sem a nuvem (`clawmetry license`). A divisão exata entre
gratuito/pago está em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Seus dados ficam na sua máquina

O ClawMetry lê arquivos de sessão e logs locais. Nada sai da sua máquina, a menos
que você rode `clawmetry connect`. Mesmo assim, o snapshot é criptografado de
ponta a ponta com uma chave que nunca sai da sua máquina, e é descriptografado
no seu navegador.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ no macOS, Linux ou Windows, e pelo menos um runtime de agente na
mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratuito vs pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Bloqueio pré-execução, pontuação de risco, aprovações pelo celular |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporte traces para qualquer lugar, ingira OTLP de qualquer fonte |
| [Rastreamento de SDK](docs/SDK_TRACKING.md) | Atribuição de custo para agentes que você mesmo construiu |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat exibidos no Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações de NVIDIA NemoClaw isoladas (sandbox) |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volume |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executando a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anônimos de instalação e abertura do desktop, e como desativá-los |

## Capturas de tela

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokens, sessões, saúde | **Brain**: fluxo de eventos do agente em tempo real |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Custo**: por modelo e sessão | **Aprovações**: bloqueia chamadas de ferramentas arriscadas |

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

MIT · Criado por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
