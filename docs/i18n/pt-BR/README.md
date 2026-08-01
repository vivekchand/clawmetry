<!-- i18n-src:191e9094d7fa -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para **14 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 10. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 14 runtimes de agentes

O ClawMetry começou como observabilidade para o OpenClaw e agora monitora toda a sua **frota de agentes** em um único painel, detectando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw e NemoClaw são gratuitos no aplicativo de código aberto; os demais runtimes são ativados com o ClawMetry Cloud ou uma licença Pro auto-hospedada. Troque de runtime pelo cabeçalho e cada aba, custo, tokens, ferramentas, traces, se reajusta a esse runtime. Veja **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, o formato de `/api/entitlement` e a CLI `clawmetry license`.

## O que você recebe

- **Flow** — Diagrama animado ao vivo mostrando mensagens fluindo por canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informações do modelo
- **Usage** — Rastreamento de tokens e custos com detalhamento diário/semanal/mensal
- **Sessions** — Sessões ativas do agente com modelo, tokens, última atividade
- **Crons** — Tarefas agendadas com status, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface em formato de balões de chat para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, detecção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, E-mail
- **Approvals** — Bloqueie exclusões destrutivas, force pushes, mutações em banco de dados, sudo, instalações de pacotes, chamadas de rede atrás de uma aprovação com um clique

## Capturas de tela

### 🧠 Brain — Fluxo de eventos ao vivo do agente
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Detalhamento de custo por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de arquivos do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura e log de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / E-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueie chamadas de ferramentas arriscadas atrás de aprovação manual; regras de proteção baseadas em política
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueio pré-execução para o Claude Code** — um comando instala um
hook PreToolUse que pausa chamadas de ferramentas correspondentes *antes* de serem executadas e aguarda
sua decisão (um toque a partir do seu celular com
[notificações push na nuvem](https://app.clawmetry.com/push) habilitadas):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Uma negação bloqueia apenas aquela chamada de ferramenta, o agente mantém sua sessão e pode
tentar outra abordagem. Aprovar pelo celular pula o próprio prompt de
permissão do Claude Code (você já respondeu). Ferramentas não correspondentes custam ~40ms e
caem de volta no fluxo normal de permissão do Claude Code. Você também recebe um push no celular quando o próprio Claude Code está aguardando você (notificações `permission_prompt` /
`idle_prompt`).

## Instalação

**Um comando (recomendado):**
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

O aplicativo React v2 vive em `frontend/` e é servido em `/v2` quando o
servidor Flask é iniciado com o v2 habilitado.

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

Abra `http://localhost:5173/v2/`. O Vite faz proxy das requisições `/api` para
`http://localhost:8900`, então o aplicativo React consegue conversar com o servidor Flask local
sem configuração extra de CORS.

Para gerar o bundle que acompanha o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é gravado em `clawmetry/static/v2/dist/`.

## Compatibilidade de runtime / agente

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw vem com um adaptador leitor dedicado que traduz o formato nativo de sessões daquele runtime para as formas unificadas do ClawMetry; o daemon os ingere no mesmo armazenamento DuckDB + snapshot na nuvem, marcados com o runtime, e a aba Session replay mostra um **seletor de runtime** quando há mais de um presente. Veja [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

Está rodando a ferramenta de segurança de agentes [numbat da Perplexity](https://github.com/perplexityai/numbat)? O ClawMetry ingere suas descobertas e decisões de enforcement prontas para uso, veja [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agente | Status | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detectado automaticamente |
| **PicoClaw** | Adaptador beta | JSONL plano de `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
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
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Execuções de workflow, execuções de nós, prompts de AI Agent, modelo + tokens quando o n8n os registra. |
| **Antigravity** | Adaptador beta | Brain JSONL em `~/.gemini/<flavor>/brain/`. Conversas, etapas de ferramentas, raciocínio, divisão de tokens Gemini por geração + custo, consumo de geração em segundo plano. |

"Adaptador beta" significa que o ClawMetry fornece um leitor para o formato real em disco daquele runtime, cada um construído + verificado em uma instalação real em uma máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são somente leitura; cada um é honesto sobre o que o runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não gravam custo de tokens em disco). Quando vários runtimes rodam em um mesmo node, o seletor de runtime restringe a visualização de sessões a um único para uma investigação limpa.

## Rastreie qualquer agente de SDK — atribuição de custo out-loop

Os runtimes acima gravam sessões em disco. O seu próprio **agente de produção**, aquele que você construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um loop simples de `httpx`, não faz isso. O interceptador zero-config do ClawMetry ainda captura suas chamadas de LLM (custo, tokens, latência, erros) fazendo monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) marca cada chamada com uma **fonte nomeada**, então cada produto que você executa aparece como sua própria linha de primeira classe, atribuível a custo, no card **🔌 Out-loop sources** do Overview no painel, chamadas, provedores, latência, taxa de erro por agente. Nenhuma fonte definida? As chamadas ainda são rastreadas; o card apenas permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que alimenta os adaptadores de runtime (DuckDB → snapshot na nuvem), então as fontes out-loop sincronizam com o painel na nuvem da mesma forma que tudo o mais, com criptografia E2E.

## OpenTelemetry — neutro em relação a fornecedores, envie seus traces para qualquer lugar

O ClawMetry fala **OpenTelemetry** nas duas direções, usando as **convenções semânticas GenAI**, para que os traces do seu agente nunca fiquem presos a uma única ferramenta.

**Exporte** cada sessão, chamadas de LLM, ferramentas, sub-agentes, tokens, custo, como spans GenAI OTLP/HTTP para qualquer coletor (Datadog, Grafana, Honeycomb, ou seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Cabeçalhos de autenticação e intervalo de sondagem são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingestão** — o receptor OTLP embutido aceita traces e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão via protobuf).

Você obtém o painel ClawMetry zero-config e local-first **e** seus dados em qualquer backend que sua equipe já use, sem vínculo obrigatório, sem precisar instalar um segundo agente.

## Configuração

A maioria das pessoas não precisa de nenhuma configuração. O ClawMetry detecta automaticamente seu workspace, logs, sessões e crons.

Se você precisar personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas as opções: `clawmetry --help`

## Canais suportados

O ClawMetry mostra atividade ao vivo para cada canal do OpenClaw que você tiver configurado. Apenas os canais que estão de fato configurados no seu `openclaw.json` aparecem no diagrama Flow, os não configurados são ocultados automaticamente.

Clique em qualquer nó de canal no Flow para ver uma visualização de balões de chat ao vivo com contagens de mensagens recebidas/enviadas.

| Canal | Status | Popup ao vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detecção de servidor + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detecção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões integradas na interface web |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipe auto-hospedado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, com suporte a E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de mensagens do LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizadas NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via conexão IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Assinatura de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detecção automática:** O ClawMetry lê seu `~/.openclaw/openclaw.json` e renderiza apenas os canais que você realmente configurou. Nenhuma configuração manual é necessária.

## Implantação com Docker

Quer rodar o ClawMetry em um container? Sem problemas! 🐳

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

> **Nota:** Ao rodar no Docker, monte os diretórios de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry possa detectar automaticamente sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, ou Antigravity (ou volumes montados para Docker)
- Linux ou macOS

## Suporte a NemoClaw / OpenShell

O ClawMetry detecta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para o OpenClaw que executa agentes dentro de containers OpenShell isolados (sandbox).

Nenhuma configuração extra é necessária na maioria dos casos. O daemon de sincronização descobre automaticamente arquivos de sessão, estejam eles em `~/.openclaw/` no host ou dentro de um container OpenShell.

### Como funciona

O ClawMetry detecta o NemoClaw de duas formas:

1. **Detecção de binário** — verifica a CLI `nemoclaw` e executa `nemoclaw status` para obter informações do sandbox
2. **Detecção de container** — varre containers Docker em execução em busca de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e então lê as sessões via volumes montados ou `docker cp`

Arquivos de sessão sincronizados de containers NemoClaw são marcados com `runtime=nemoclaw` e metadados `container_id` no painel na nuvem, para que você consiga diferenciá-los das sessões padrão do OpenClaw rapidamente.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina host** (não dentro do sandbox). Isso evita restrições de política de rede do NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente sessões dentro de quaisquer containers OpenShell em execução.

### Opcional: nome de sandbox explícito

Se a detecção automática não funcionar, aponte o ClawMetry para o sandbox correto:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Executando dentro do sandbox (avançado)

Se você precisar executar o daemon de sincronização **dentro** do sandbox OpenShell, adicione esta regra de saída (egress) à sua política de rede do NemoClaw para que ele consiga alcançar a API de ingestão do ClawMetry:

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

| Endpoint | Porta | Protocolo | Obrigatório |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sim (daemon de sincronização → nuvem) |
| `localhost:8900` | 8900 | HTTP | Sim (interface do painel local) |
| Socket do Docker (`/var/run/docker.sock`) | — | Socket Unix | Para descoberta de sessões em containers |

O daemon de sincronização faz apenas chamadas HTTPS de saída para `ingest.clawmetry.com`. Nenhuma porta de entrada é necessária.

---

## Implantação na nuvem

Veja o **[Guia de Testes de Nuvem](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com o BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia pings anônimos do ciclo de vida da instalação para
`https://app.clawmetry.com/api/install`: um ping `install` na primeira
vez que você executa a CLI `clawmetry` em uma nova máquina, um ping `update`
na primeira execução após atualizar para uma nova versão, e um ping `onboarded`
quando você conclui a escolha de onboarding no painel. Usamos isso
para contar instalações reais (os números brutos de download do PyPI são ~98% espelhos, CI,
e re-downloads de auto-atualização) e para saber quais frameworks de agente e
versões estão de fato em uso.

**No máximo um POST por evento de ciclo de vida por versão**, contendo:

| Campo | Exemplo | Motivo |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; anônimo até você conectar explicitamente a sincronização com a nuvem (o heartbeat autenticado do daemon então carrega isso, vinculando esta instalação à sua conta) |
| `event` | `install` / `update` / `onboarded` | instalação nova vs. atualização de uma existente |
| `version` | `0.12.167` | quais versões estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versão do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com quais agentes devemos nos integrar em seguida |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a nuvem deriva o código do país no lado do servidor
a partir da requisição, depois descarta o IP), hostname, nome de usuário, caminho do workspace,
conteúdo de arquivos, sua api_key, seu e-mail, nada de PII ou
específico do workspace. O payload transmitido é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desativar** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Uma falha de rede aqui nunca impede a execução do `clawmetry`, o
ping é fire-and-forget em uma thread do daemon com timeout de 3 s.

## Histórico de estrelas

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
  <strong>🦞 Veja seu agente pensar</strong><br>
  <sub>Construído por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte do ecossistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
