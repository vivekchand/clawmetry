<!-- i18n-src:c422fb7dd0da -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja o seu agente a pensar.** Observabilidade em tempo real para **21 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 16. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e está feito.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 21 runtimes de agentes

O ClawMetry começou como observabilidade para o OpenClaw e agora mede toda a sua **frota de agentes** num único painel, detetando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw e NemoClaw são gratuitos na aplicação de código aberto; os restantes runtimes ativam-se com o ClawMetry Cloud ou com uma licença Pro self-hosted. Mude de runtime a partir do cabeçalho e todos os separadores (custo, tokens, ferramentas, traces) reajustam-se a esse runtime. Consulte **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, o formato de `/api/entitlement` e a CLI `clawmetry license`.

## O que obtém

- **Flow** — Diagrama animado ao vivo que mostra as mensagens a fluir através dos canais, do brain, das ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informação do modelo
- **Usage** — Acompanhamento de tokens e custos com divisões diárias/semanais/mensais
- **Sessions** — Sessões de agentes ativas com modelo, tokens, última atividade
- **Crons** — Tarefas agendadas com estado, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com código de cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface de balões de conversa para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, deteção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloqueia eliminações destrutivas, force pushes, mutações em bases de dados, sudo, instalações de pacotes, chamadas de rede, atrás de uma aprovação com um clique

## Capturas de ecrã

### 🧠 Brain — Fluxo de eventos do agente em tempo real
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Divisão de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de ficheiros do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e registo de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueia chamadas de ferramentas de risco atrás de aprovação manual; regras de proteção baseadas em políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueio pré-execução para o Claude Code** — um único comando instala um
hook PreToolUse que pausa as chamadas de ferramentas correspondentes *antes* de serem executadas e aguarda
pela sua decisão (um toque a partir do telemóvel com
[notificações push na cloud](https://app.clawmetry.com/push) ativadas):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Uma negação bloqueia apenas essa chamada de ferramenta; o agente mantém a sua sessão e pode
tentar outra abordagem. Aprovar no telemóvel salta o próprio pedido de
permissão do Claude Code (já respondeu). Ferramentas sem correspondência custam ~40ms e
seguem para o fluxo de permissões normal do Claude Code. Também recebe uma notificação push no telemóvel quando o próprio Claude Code está à espera de si (notificações `permission_prompt` /
`idle_prompt`).

## Instalação

**Comando único (recomendado):**
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

## Desenvolvimento do frontend v2

A aplicação React v2 reside em `frontend/` e é servida em `/v2` quando o
servidor Flask é iniciado com o v2 ativado.

Use dois terminais durante o desenvolvimento:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abra `http://localhost:5173/v2/`. O Vite faz proxy dos pedidos `/api` para
`http://localhost:8900`, para que a aplicação React possa comunicar com o servidor Flask local
sem necessidade de configuração CORS adicional.

Para compilar o bundle que é distribuído com o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é escrito em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw disponibiliza um adaptador de leitura dedicado que traduz o seu formato nativo de sessão para os formatos unificados do ClawMetry; o daemon ingere-os no mesmo repositório DuckDB + snapshot na cloud, com etiqueta do runtime, e o separador de replay de sessões mostra um **seletor de runtime** quando existe mais do que um presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

Está a usar a ferramenta de segurança de agentes [numbat da Perplexity](https://github.com/perplexityai/numbat)? O ClawMetry ingere os seus resultados e decisões de aplicação de políticas de origem, sem configuração adicional; veja [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detetado automaticamente |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
| **NanoClaw** | Adaptador beta | SQLite por sessão (`data/v2-sessions`). Transcrições + contagem de mensagens. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas de ferramentas + raciocínio, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcrições de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagem de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas de ferramentas, totais de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Pi** | Adaptador beta | JSONL `~/.pi/agent/sessions`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **Deep Agents** | Adaptador beta | SQLite `~/.deepagents/.state/sessions.db`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Execuções de workflow, execuções de nós, prompts do AI Agent, modelo + tokens quando o n8n os regista. |
| **Antigravity** | Adaptador beta | Brain JSONL em `~/.gemini/<flavor>/brain/`. Conversas, passos de ferramentas, raciocínio, divisão de tokens Gemini por geração + custo, consumo de geração em segundo plano. |
| **GitHub Copilot** | Adaptador beta | `events.jsonl` da Copilot CLI em `~/.copilot/session-state/` + o livro-razão de uso por chamada `session-store.db`. Conversas, chamadas de ferramentas, encaminhamento de modelo, divisão de tokens com cache, custo em créditos de IA faturados pelo fornecedor. |
| **Grok** | Adaptador beta | xAI Grok Build CLI (binário Rust em `~/.grok/bin/grok`): registo global de eventos `~/.grok/logs/unified.jsonl` + por sessão `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Conversas, divisão de tokens por turno, encaminhamento de modelo, e o payload de repositório enviado pela CLI, colocado em `~/.grok/upload_queue/`, para que possa ver o que saiu da sua máquina. |

"Adaptador beta" significa que o ClawMetry disponibiliza um leitor para o formato real em disco desse runtime, cada um construído + verificado numa instalação real numa máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são apenas de leitura; cada um é transparente quanto ao que o respetivo runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não escrevem o custo em tokens em disco). Quando vários runtimes correm num só nó, o seletor de runtime restringe a vista de sessões a um deles, para uma análise limpa e aprofundada.

## Acompanhe qualquer agente SDK — atribuição de custos out-loop

Os runtimes acima escrevem todos as sessões em disco. O seu próprio **agente de produção** — aquele que construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um simples loop `httpx` — não o faz. O interceptor de zero configuração do ClawMetry continua a capturar as suas chamadas de LLM (custo, tokens, latência, erros) fazendo monkey-patching a `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) marca cada chamada com uma **origem nomeada**, para que cada produto que executa apareça como a sua própria linha, de primeira classe e com atribuição de custo, no cartão **🔌 Out-loop sources** do painel Overview: chamadas, fornecedores, latência, taxa de erro por agente. Sem origem definida? As chamadas continuam a ser registadas; o cartão apenas permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados alimentada pelos adaptadores de runtime (DuckDB → snapshot na cloud), pelo que as origens out-loop sincronizam com o painel na cloud tal como tudo o resto, com encriptação de ponta a ponta.

## OpenTelemetry — neutro em relação a fornecedores, envie os seus traces para qualquer lado

O ClawMetry fala **OpenTelemetry** em ambas as direções, usando as **convenções semânticas GenAI**, para que os traces do seu agente nunca fiquem presos a uma única ferramenta.

**Exportação** de cada sessão — chamadas de LLM, ferramentas, sub-agentes, tokens, custo — como spans GenAI OTLP/HTTP para qualquer coletor (Datadog, Grafana, Honeycomb, ou o seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Os cabeçalhos de autenticação e o intervalo de sondagem são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingestão** — o recetor OTLP incorporado aceita traces, logs e métricas de qualquer outra fonte em `/v1/traces`, `/v1/logs` e `/v1/metrics`. Aponte qualquer aplicação instrumentada com OpenTelemetry para ele:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Os traces e logs OTLP/JSON funcionam com um simples `pip install clawmetry`, sem extras. A ingestão de Protobuf (e métricas OTLP/JSON) requer `pip install clawmetry[otel]`. Uma aplicação que define o seu próprio `service.name` aparece como o seu próprio agente no seletor de runtime, com o seu custo e tokens.

Obtém o painel ClawMetry de configuração zero e local-first **e** os seus dados no backend que a sua equipa já utiliza; sem dependência de fornecedor, sem necessidade de instalar um segundo agente.

## Configuração

A maioria das pessoas não precisa de qualquer configuração. O ClawMetry deteta automaticamente o seu workspace, logs, sessões e crons.

Se precisar de personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas as opções: `clawmetry --help`

## Canais Suportados

O ClawMetry mostra atividade ao vivo para todos os canais OpenClaw que tiver configurados. Apenas os canais que estão realmente configurados no seu `openclaw.json` aparecem no diagrama Flow; os que não estão configurados são ocultados automaticamente.

Clique em qualquer nó de canal no Flow para ver uma vista de balões de chat ao vivo, com contagens de mensagens recebidas/enviadas.

| Canal | Estado | Popup ao vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Deteção de servidor + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Deteção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões da interface web incorporada |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipa self-hosted |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, com suporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | Mensagens diretas NIP-04 descentralizadas |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via ligação IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Subscrição de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Deteção automática:** O ClawMetry lê o seu `~/.openclaw/openclaw.json` e apenas apresenta os canais que configurou de facto. Não é necessária configuração manual.

## Implementação com Docker

Quer executar o ClawMetry num contentor? Sem problema! 🐳

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

**Exemplo de Docker Compose:**

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

> **Nota:** Ao executar em Docker, monte os diretórios de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry possa detetar automaticamente a sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, ou QM (ou volumes montados para Docker)
- Linux ou macOS

## Suporte para NemoClaw / OpenShell

O ClawMetry deteta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para o OpenClaw, que executa agentes dentro de contentores OpenShell isolados (sandboxed).

Na maioria dos casos, não é necessária configuração adicional. O daemon de sincronização descobre automaticamente os ficheiros de sessão, quer estejam em `~/.openclaw/` no host, quer dentro de um contentor OpenShell.

### Como funciona

O ClawMetry deteta o NemoClaw de duas formas:

1. **Deteção de binário** — verifica a existência da CLI `nemoclaw` e executa `nemoclaw status` para obter informação sobre a sandbox
2. **Deteção de contentor** — analisa os contentores Docker em execução à procura de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e depois lê as sessões através de volumes montados ou de `docker cp`

Os ficheiros de sessão sincronizados a partir de contentores NemoClaw são etiquetados com `runtime=nemoclaw` e metadados `container_id` no painel na cloud, para que consiga distingui-los das sessões OpenClaw normais rapidamente.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina host** (não dentro da sandbox). Isto evita restrições de política de rede do NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização irá encontrar automaticamente as sessões dentro de quaisquer contentores OpenShell em execução.

### Opcional: nome explícito da sandbox

Se a deteção automática não funcionar, aponte o ClawMetry para a sandbox correta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Executar dentro da sandbox (avançado)

Se tiver de executar o daemon de sincronização **dentro** da sandbox OpenShell, adicione esta regra de saída (egress) à sua política de rede do NemoClaw, para que consiga alcançar a API de ingestão do ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Sim (daemon de sincronização → cloud) |
| `localhost:8900` | 8900 | HTTP | Sim (interface do painel local) |
| Socket do Docker (`/var/run/docker.sock`) | — | Socket Unix | Para descoberta de sessões em contentores |

O daemon de sincronização faz apenas chamadas HTTPS de saída para `ingest.clawmetry.com`. Não é necessária nenhuma porta de entrada.

---

## Implementação na Cloud

Consulte o **[Guia de Testes na Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com o BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia pings anónimos do ciclo de vida da instalação para
`https://app.clawmetry.com/api/install`: um ping de `install` na primeira
vez que executa a CLI `clawmetry` numa nova máquina, um ping de `update`
na primeira execução após atualizar para uma nova versão, e um ping de `onboarded`
quando conclui a escolha de onboarding no painel. Usamos isto
para contar instalações reais (os números brutos de downloads do PyPI são ~98% mirrors, CI,
e re-downloads de atualização automática) e para saber quais as frameworks de agentes e
versões que estão realmente em uso.

**No máximo um POST por evento do ciclo de vida por versão**, contendo:

| Campo | Exemplo | Porquê |
|---|---|---|
| `install_id` | UUID aleatório guardado em `~/.clawmetry/install_id` | deduplicação; anónimo até ligar explicitamente a sincronização com a Cloud (o heartbeat autenticado do daemon passa então a incluí-lo, ligando esta instalação à sua conta) |
| `event` | `install` / `update` / `onboarded` | instalação nova vs. atualização de uma existente |
| `version` | `0.12.167` | quais as versões em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com que agentes nos devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a cloud deriva o código do país do lado do
servidor a partir do pedido, e depois descarta o IP), nome do host, nome de utilizador, caminho do
workspace, conteúdo de ficheiros, a sua api_key, o seu email, nada que seja PII ou
específico do workspace. O payload transmitido pode ser auditado em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desativar** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Uma falha de rede aqui nunca bloqueia a execução do `clawmetry`; o
ping é fire-and-forget numa thread do daemon, com um timeout de 3 s.

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
