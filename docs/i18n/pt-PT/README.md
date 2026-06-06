<!-- i18n-src:48548997be76 -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja o seu agente a pensar.** Observabilidade em tempo real para **12 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 8. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e está pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatível com 12 runtimes de agentes

ClawMetry começou como observabilidade para OpenClaw e agora monitoriza toda a sua **frota de agentes** num único painel, detetando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw e NemoClaw estão disponíveis gratuitamente na aplicação open-source; os restantes runtimes ficam ativos com ClawMetry Cloud ou uma licença Pro auto-alojada. Mude de runtime a partir do cabeçalho e cada separador — custo, tokens, ferramentas, rastreios — restringe-se a esse runtime.

## O que obtém

- **Flow** — Diagrama animado em tempo real que mostra mensagens a fluir pelos canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de estado, mapa de atividade, contagens de sessões, informações do modelo
- **Usage** — Rastreio de tokens e custos com desagregações diárias/semanais/mensais
- **Sessions** — Sessões de agentes ativas com modelo, tokens e última atividade
- **Crons** — Tarefas agendadas com estado, próxima execução e duração
- **Logs** — Transmissão de registos em tempo real com código de cores
- **Memory** — Navegue em SOUL.md, MEMORY.md, AGENTS.md e notas diárias
- **Transcripts** — Interface de bolhas de chat para leitura do histórico de sessões
- **Alerts** — Limites de orçamento, acionadores de taxa de erros, deteção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Restrinja eliminações destrutivas, pushes forçados, mutações de base de dados, sudo, instalações de pacotes e chamadas de rede por trás de uma aprovação de um clique

## Capturas de ecrã

### 🧠 Brain — Fluxo de eventos do agente em tempo real
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilização de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desagregação de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de ficheiros do espaço de trabalho
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e registo de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, acionadores de taxa de erros, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Restrinja chamadas de ferramentas arriscadas com aprovação manual; regras de proteção baseadas em políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalação

**Num único comando (recomendado):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**A partir do código-fonte:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Desenvolvimento do Frontend v2

A aplicação React v2 encontra-se em `frontend/` e é servida em `/v2` quando o servidor Flask é iniciado com v2 ativado.

Utilize dois terminais durante o desenvolvimento:

```bash
# Terminal 1: API/servidor Flask em :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: servidor de desenvolvimento Vite em :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abra `http://localhost:5173/v2/`. O Vite redireciona os pedidos `/api` para `http://localhost:8900`, para que a aplicação React comunique com o servidor Flask local sem configuração CORS adicional.

Para construir o pacote que acompanha o pacote Python:

```bash
cd frontend
npm run build
```

O pacote de produção é escrito em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

ClawMetry observa muitos runtimes de agentes de IA, não apenas OpenClaw. Cada runtime não-OpenClaw inclui um adaptador de leitura dedicado que traduz o seu formato de sessão nativo para as formas unificadas do ClawMetry; o daemon ingere-os no mesmo armazenamento DuckDB e snapshot na nuvem, marcados com o runtime, e o separador de repetição de sessões apresenta um **seletor de runtime** quando mais do que um está presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa e um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detetado automaticamente |
| **PicoClaw** | Adaptador Beta | JSONL `providers.Message` plano (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
| **NanoClaw** | Adaptador Beta | SQLite por sessão (`data/v2-sessions`). Transcrições e contagens de mensagens. |
| **Hermes** | Adaptador Beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador Beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas de ferramentas e raciocínio, utilização de tokens. |
| **Codex** | Adaptador Beta | JSONL de rollout `~/.codex/sessions/...`. Transcrições, modelo, chamadas de ferramentas, utilização de tokens. |
| **Cursor** | Adaptador Beta | SQLite `state.vscdb`. Transcrições de chat/compositor, modelo. |
| **Aider** | Adaptador Beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagens de tokens. |
| **Goose** | Adaptador Beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas de ferramentas, totais de tokens. |
| **opencode** | Adaptador Beta | SQLite `~/.local/share/opencode`. Transcrições, modelo, chamadas de ferramentas, tokens e custo. |
| **Qwen Code** | Adaptador Beta | JSONL `~/.qwen/projects/.../chats`. Transcrições, modelo, chamadas de ferramentas, utilização de tokens. |

"Adaptador Beta" significa que ClawMetry inclui um leitor para o formato em disco real desse runtime, cada um construído e verificado numa instalação real numa máquina real (ver `tests/fixtures/runtimes/<rt>/`). Os adaptadores são apenas de leitura; cada um é honesto sobre o que o seu runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não escrevem custo de tokens em disco). Quando vários runtimes estão em execução num nó, o seletor de runtime circunscreve a vista de sessões a um para uma análise aprofundada limpa.

## Rastreie qualquer agente SDK — atribuição de custos fora do ciclo

Os runtimes acima escrevem sessões em disco. O seu **agente de produção** próprio, aquele que construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B ou um simples ciclo `httpx`, não o faz. O interceptor de configuração zero do ClawMetry ainda captura as suas chamadas LLM (custo, tokens, latência, erros) por meio de monkey-patching do `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) marca cada chamada com uma **fonte nomeada**, para que cada produto que execute apareça como a sua própria linha de primeira classe com atribuição de custos no cartão **🔌 Out-loop sources** do Overview do painel — chamadas, fornecedores, latência, taxa de erros por agente. Sem fonte definida? As chamadas continuam a ser rastreadas; o cartão simplesmente permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que os adaptadores de runtime alimentam (DuckDB e snapshot na nuvem), pelo que as fontes fora do ciclo sincronizam com o painel na nuvem da mesma forma que tudo o resto, com encriptação ponta a ponta.

## OpenTelemetry — neutro em relação a fornecedores, envie os seus rastreios para qualquer lado

ClawMetry suporta **OpenTelemetry** nos dois sentidos, utilizando as **convenções semânticas GenAI**, para que os rastreios do seu agente nunca fiquem presos a uma única ferramenta.

**Exporte** cada sessão — chamadas LLM, ferramentas, subagentes, tokens, custo — como spans GenAI OTLP/HTTP para qualquer coletor (Datadog, Grafana, Honeycomb ou o seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Os cabeçalhos de autenticação e o intervalo de polling são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingira** — o recetor OTLP integrado aceita rastreios e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão de protobuf).

Obtém o painel ClawMetry de configuração zero, local em primeiro lugar, **e** os seus dados em qualquer backend que a sua equipa já utilize, sem dependência de fornecedor e sem necessidade de instalar um segundo agente.

## Configuração

A maioria das pessoas não precisa de nenhuma configuração. ClawMetry deteta automaticamente o seu espaço de trabalho, registos, sessões e crons.

Se precisar de personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas as opções: `clawmetry --help`

## Canais Suportados

ClawMetry mostra atividade em tempo real para cada canal OpenClaw que tenha configurado. Apenas os canais que estão efetivamente configurados no seu `openclaw.json` aparecem no diagrama Flow; os não configurados são automaticamente ocultados.

Clique em qualquer nó de canal no Flow para ver uma vista de bolhas de chat em tempo real com contagens de mensagens enviadas e recebidas.

| Canal | Estado | Popup em Tempo Real | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Deteção de servidor e canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Deteção de espaço de trabalho e canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões de interface web integrada |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de bolhas com estilo de terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da API Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipa auto-alojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de Mensagens LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via ligação IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Subscrição de eventos WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API de Bot Zalo |

> **Deteção automática:** ClawMetry lê o seu `~/.openclaw/openclaw.json` e apenas apresenta os canais que configurou. Não é necessária qualquer configuração manual.

## Implantação com Docker

Quer executar ClawMetry num contentor? Sem problema! 🐳

**Início rápido com Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Exemplo com Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Nota:** Ao executar no Docker, monte os diretórios de dados e registos do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry possa detetar automaticamente a sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw ou PicoClaw (ou volumes montados para Docker)
- Linux ou macOS

## Suporte a NemoClaw / OpenShell

ClawMetry deteta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para OpenClaw que executa agentes dentro de contentores OpenShell isolados.

Na maioria dos casos, não é necessária qualquer configuração adicional. O daemon de sincronização descobre automaticamente os ficheiros de sessão, quer estejam em `~/.openclaw/` no host ou dentro de um contentor OpenShell.

### Como funciona

ClawMetry deteta NemoClaw de duas formas:

1. **Deteção de binário** — verifica a existência da CLI `nemoclaw` e executa `nemoclaw status` para obter informações sobre a sandbox
2. **Deteção de contentor** — analisa os contentores Docker em execução à procura de imagens `openshell`, `nemoclaw` ou `ghcr.io/nvidia/`, e depois lê as sessões via montagens de volume ou `docker cp`

Os ficheiros de sessão sincronizados a partir de contentores NemoClaw são marcados com metadados `runtime=nemoclaw` e `container_id` no painel na nuvem, para que possa distingui-los das sessões OpenClaw padrão de imediato.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina host** (fora da sandbox). Isto evita as restrições de política de rede do NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente as sessões dentro de quaisquer contentores OpenShell em execução.

### Opcional: nome explícito da sandbox

Se a deteção automática não funcionar, aponte ClawMetry para a sandbox correta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Execução dentro da sandbox (avançado)

Se tiver de executar o daemon de sincronização **dentro** da sandbox OpenShell, adicione esta regra de saída à sua política de rede NemoClaw para que possa alcançar a API de ingestão do ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Aplique com:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Portas e endpoints

| Endpoint | Porta | Protocolo | Necessário |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sim (daemon de sincronização para a nuvem) |
| `localhost:8900` | 8900 | HTTP | Sim (interface do painel local) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Para descoberta de sessões em contentores |

O daemon de sincronização apenas realiza chamadas HTTPS de saída para `ingest.clawmetry.com`. Não são necessárias portas de entrada.

---

## Implantação na Nuvem

Consulte o **[Guia de Testes na Nuvem](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry envia um único ping anónimo de "primeira execução" para `https://app.clawmetry.com/api/install` na primeira vez que executa a CLI `clawmetry` numa nova máquina. Utilizamos isto para contar instalações (a única métrica de marketing que temos para um projeto OSS) e para saber quais os frameworks de agentes que os nossos utilizadores têm instalados.

**Exatamente um POST por instalação**, contendo:

| Campo | Exemplo | Motivo |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; não vinculado ao seu email ou api_key |
| `version` | `0.12.167` | que versões estão em utilização |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com que agentes devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas do ruído de CI |

**O que NÃO enviamos**: IP (a nuvem deriva o código de país no lado do servidor a partir do pedido e depois descarta o IP), nome do host, nome de utilizador, caminho do espaço de trabalho, conteúdo de ficheiros, a sua api_key, o seu email, nada que seja PII ou específico do espaço de trabalho. O payload da ligação é auditável em [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desative** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Uma falha de rede aqui nunca bloqueia a execução do `clawmetry` — o ping é do tipo "disparar e esquecer" numa thread daemon com um timeout de 3 s.

## Histórico de Estrelas

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licença

MIT

---

<p align="center">
  <strong>🦞 Veja o seu agente a pensar</strong><br>
  <sub>Criado por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte do ecossistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
