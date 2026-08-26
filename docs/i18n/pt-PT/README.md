<!-- i18n-src:c111f32e69a5 -->
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

**Veja o seu agente a pensar.** Observabilidade em tempo real para **27 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 22. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900**. Zero configuração: encontra os runtimes de
agentes que já tem, lê-os em modo só de leitura e não altera nada na forma como estes funcionam.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 27 runtimes de agentes

**Gratuito na aplicação de código aberto:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Num plano pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Todos os runtimes têm acesso ao mesmo painel. Execute vários em simultâneo e o
seletor no cabeçalho reajusta cada separador para um deles.

Construiu o seu próprio agente com um SDK? O intercetor também regista as suas
chamadas de LLM. Veja [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## O que obtém

- **Sessões e transcrições**: o que cada agente fez, passo a passo, com repetição
- **Custo e tokens**: por runtime, modelo, sessão e dia, com sinalização de anomalias
- **Flow**: diagrama em tempo real das mensagens que circulam entre canais, modelos e ferramentas
- **Brain**: o fluxo de eventos de raciocínio e chamadas de ferramentas à medida que acontecem
- **Memória e skills**: os ficheiros e skills que cada runtime efetivamente carregou
- **Saúde e logs**: disco, memória, taxas de erro, limites de taxa, fluxo de logs em direto
- **Alertas**: limites de orçamento, picos de erro, agente offline, encaminhados para Slack, Discord, PagerDuty, Telegram, Email
- **Aprovações**: pausar chamadas de ferramentas arriscadas *antes* de serem executadas e aprová-las a partir do telemóvel ([como](docs/APPROVALS.md))

## Preços

| Plano | O que cobre | Preço |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, painel completo, apenas local | $0 |
| **Starter** | Todos os outros runtimes acima, vista de frota, sincronização na cloud | $9 por nó / mês |
| **Pro** | Starter + governação: aprovações, políticas de risco de ferramentas, avaliações, deteção de anomalias, otimizador de custos, exportação OTel | $19 por nó / mês |

Os planos anuais, Enterprise e os valores atuais encontram-se em
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. As chaves de licença
autoalojadas funcionam sem a cloud (`clawmetry license`). A divisão exata entre
gratuito e pago está em [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Os seus dados permanecem na sua máquina

O ClawMetry lê ficheiros de sessão e logs locais. Nada sai da sua máquina a
menos que execute `clawmetry connect`. Mesmo nesse caso, a captura é
encriptada de ponta a ponta com uma chave que nunca sai da sua máquina, e é
desencriptada no seu navegador.

## Instalação

```bash
pip install clawmetry     # depois: clawmetry
```

Ou o comando único: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requer Python 3.8+ no macOS, Linux ou Windows, e pelo menos um runtime de
agente na mesma máquina. Instruções para Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentação

| | |
|---|---|
| [Compatibilidade de runtimes](docs/compatibility.md) | O que cada adaptador lê, e como adicionar um runtime |
| [Direitos de acesso](docs/ENTITLEMENTS.md) | Gratuito vs pago, matriz de níveis, CLI de licença |
| [Aprovações e políticas](docs/APPROVALS.md) | Controlo pré-execução, pontuação de risco, aprovações pelo telemóvel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportar traces para qualquer lugar, ingerir OTLP de qualquer fonte |
| [Rastreio de SDK](docs/SDK_TRACKING.md) | Atribuição de custos para agentes construídos por si |
| [Canais de chat](docs/CHANNELS.md) | Os adaptadores de chat apresentados no Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurações de NVIDIA NemoClaw em sandbox |
| [Docker](docs/DOCKER.md) | Imagem, compose, montagens de volumes |
| [Arquitetura](ARCHITECTURE.md) · [Desenvolvimento](docs/DEVELOPMENT.md) | Como funciona por dentro; executar a partir do código-fonte |
| [Telemetria](docs/TELEMETRY.md) | Os pings anónimos de instalação e abertura da aplicação, e como os desativar |

## Capturas de ecrã

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokens, sessões, saúde | **Brain**: fluxo de eventos do agente em direto |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: por modelo e sessão | **Approvals**: bloquear chamadas de ferramentas arriscadas |

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
