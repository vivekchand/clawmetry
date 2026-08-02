<!-- i18n-src:0e34918f8f2e -->
> Português (PT) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja o seu agente a pensar.** Observabilidade em tempo real para **14 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 10. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Deteta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e está feito.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 14 runtimes de agentes

O ClawMetry começou como observabilidade para o OpenClaw e agora mede toda a sua **frota de agentes** num único painel, detetando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

O OpenClaw e o NemoClaw são gratuitos na aplicação open-source; os restantes runtimes são ativados com o ClawMetry Cloud ou uma licença Pro auto-alojada. Mude de runtime a partir do cabeçalho e cada separador (custo, tokens, ferramentas, traces) reajusta-se a esse runtime. Consulte **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, o formato de `/api/entitlement` e a CLI `clawmetry license`.

## O que obtém

- **Flow** — Diagrama animado ao vivo que mostra as mensagens a fluir através de canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informação do modelo
- **Usage** — Acompanhamento de tokens e custos com divisões diárias/semanais/mensais
- **Sessions** — Sessões ativas do agente com modelo, tokens e última atividade
- **Crons** — Tarefas agendadas com estado, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com código de cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface tipo balão de conversa para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, deteção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloqueie eliminações destrutivas, force pushes, mutações de base de dados, sudo, instalações de pacotes e chamadas de rede atrás de uma aprovação com um clique

## Capturas de ecrã

### 🧠 Brain — Fluxo de eventos do agente em tempo real
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Resumo de uso de tokens e sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Divisão de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de ficheiros do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e registo de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueie chamadas de ferramentas arriscadas atrás de aprovação manual; regras de proteção baseadas em política
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueio pré-execução para o Claude Code** — um comando instala um
hook PreToolUse que pausa as chamadas de ferramentas correspondentes *antes*
de serem executadas e aguarda a sua decisão (um toque a partir do seu telemóvel com
as [notificações push na cloud](https://app.clawmetry.com/push) ativadas):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Uma negação bloqueia apenas essa chamada de ferramenta — o agente mantém a sua sessão e pode
tentar outra abordagem. Aprovar a partir do seu telemóvel salta o próprio pedido de
permissão do Claude Code (já respondeu). Ferramentas não correspondidas custam ~40ms e
recorrem ao fluxo de permissão normal do Claude Code. Também recebe uma notificação push
quando o próprio Claude Code está à espera de si (notificações `permission_prompt` /
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

## Desenvolvimento do Frontend v2

A aplicação React v2 está em `frontend/` e é servida em `/v2` quando o servidor
Flask é iniciado com o v2 ativado.

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

Abra `http://localhost:5173/v2/`. O Vite encaminha os pedidos `/api` para
`http://localhost:8900`, para que a aplicação React possa comunicar com o servidor Flask local
sem configuração adicional de CORS.

Para compilar o pacote que é distribuído com o pacote Python:

```bash
cd frontend
npm run build
```

O pacote de produção é escrito em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw tem um adaptador de leitura dedicado que traduz o seu formato de sessão nativo para os formatos unificados do ClawMetry; o daemon integra-os na mesma base de dados DuckDB + snapshot na cloud, etiquetados com o runtime, e o separador de replay de sessões mostra um **seletor de runtime** quando existe mais do que um presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

Está a usar a ferramenta de segurança de agentes [numbat da Perplexity](https://github.com/perplexityai/numbat)? O ClawMetry integra as suas descobertas e decisões de aplicação de forma nativa — veja [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, deteção automática |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
| **NanoClaw** | Adaptador beta | SQLite por sessão (`data/v2-sessions`). Transcrições + contagem de mensagens. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas de ferramentas + pensamento, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcrições de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagem de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas de ferramentas, totais de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Pi** | Adaptador beta | JSONL `~/.pi/agent/sessions`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **Deep Agents** | Adaptador beta | SQLite `~/.deepagents/.state/sessions.db`. Transcrições, modelo, chamadas de ferramentas, tokens + custo. |
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Execuções de workflow, execuções de nós, prompts do AI Agent, modelo + tokens onde o n8n os regista. |
| **Antigravity** | Adaptador beta | Brain JSONL em `~/.gemini/<flavor>/brain/`. Conversas, etapas de ferramentas, pensamento, divisão de tokens Gemini por geração + custo, consumo de gerações em segundo plano. |
| **GitHub Copilot** | Adaptador beta | `events.jsonl` do Copilot CLI em `~/.copilot/session-state/` + o livro-razão de uso por chamada `session-store.db`. Conversas, chamadas de ferramentas, encaminhamento de modelo, divisão de tokens com reconhecimento de cache, custo em créditos de IA faturados pelo fornecedor. |

"Adaptador beta" significa que o ClawMetry disponibiliza um leitor para o formato real em disco desse runtime, cada um construído + verificado contra uma instalação real numa máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são apenas de leitura; cada um é honesto sobre o que o seu runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não escrevem o custo de tokens em disco). Quando vários runtimes correm num nó, o seletor de runtime limita a vista de sessões a um só, para uma análise aprofundada e limpa.

## Acompanhe qualquer agente SDK — atribuição de custos fora do loop

Os runtimes acima referidos escrevem todos sessões em disco. O seu **agente de produção** próprio — aquele que construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um simples loop `httpx` — não o faz. O interceptor sem configuração do ClawMetry continua a capturar as suas chamadas LLM (custo, tokens, latência, erros) através de monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) etiqueta cada chamada com uma **fonte nomeada**, para que cada produto que executa apareça como a sua própria linha de primeira classe, atribuível por custo, no cartão **🔌 Out-loop sources** do painel Overview — chamadas, fornecedores, latência, taxa de erro por agente. Nenhuma fonte definida? As chamadas continuam a ser acompanhadas; o cartão apenas fica oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que os adaptadores de runtime alimentam (DuckDB → snapshot na cloud), pelo que as fontes fora do loop sincronizam com o painel na cloud da mesma forma que tudo o resto, com encriptação de ponta a ponta.

## OpenTelemetry — neutro em relação ao fornecedor, envie os seus traces para qualquer lugar

O ClawMetry fala **OpenTelemetry** em ambas as direções, usando as **convenções semânticas GenAI**, para que os traces do seu agente nunca fiquem presos a uma única ferramenta.

**Exportação** de cada sessão — chamadas LLM, ferramentas, sub-agentes, tokens, custo — como spans OTLP/HTTP GenAI para qualquer coletor (Datadog, Grafana, Honeycomb, ou o seu próprio OTel Collector):

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

**Ingestão** — o recetor OTLP incorporado aceita traces e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão protobuf).

Obtém o painel ClawMetry sem configuração e local-first **e** os seus dados no backend que a sua equipa já utiliza — sem aprisionamento, sem um segundo agente para instalar.

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

O ClawMetry mostra atividade ao vivo para cada canal OpenClaw que tem configurado. Apenas os canais que estão realmente configurados no seu `openclaw.json` aparecem no diagrama Flow — os não configurados são automaticamente ocultados.

Clique em qualquer nó de canal no Flow para ver uma vista de balões de chat ao vivo com contagens de mensagens recebidas/enviadas.

| Canal | Estado | Popup ao vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê diretamente `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Deteção de servidor + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Deteção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões da interface web incorporada |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipa auto-alojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de Mensagens do LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizadas NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via ligação IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Subscrição de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API de Bot do Zalo |

> **Deteção automática:** O ClawMetry lê o seu `~/.openclaw/openclaw.json` e apenas renderiza os canais que realmente configurou. Não é necessária configuração manual.

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

> **Nota:** Ao executar no Docker, monte os diretórios de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry possa detetar automaticamente a sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, ou GitHub Copilot (ou volumes montados para o Docker)
- Linux ou macOS

## Suporte para NemoClaw / OpenShell

O ClawMetry deteta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw) — o invólucro de segurança empresarial da NVIDIA para o OpenClaw que executa agentes dentro de contentores OpenShell isolados (sandboxed).

Na maioria dos casos, não é necessária configuração adicional. O daemon de sincronização descobre automaticamente os ficheiros de sessão, quer estejam em `~/.openclaw/` no anfitrião, quer dentro de um contentor OpenShell.

### Como funciona

O ClawMetry deteta o NemoClaw de duas formas:

1. **Deteção de binário** — verifica se existe a CLI `nemoclaw` e executa `nemoclaw status` para obter informação da sandbox
2. **Deteção de contentor** — analisa os contentores Docker em execução à procura de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e depois lê as sessões via montagens de volume ou `docker cp`

Os ficheiros de sessão sincronizados a partir de contentores NemoClaw são etiquetados com `runtime=nemoclaw` e metadados `container_id` no painel na cloud, para que os possa distinguir das sessões OpenClaw padrão à primeira vista.

### Configuração recomendada: daemon de sincronização no ANFITRIÃO

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina anfitriã** (não dentro da sandbox). Isto evita restrições da política de rede do NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente as sessões dentro de quaisquer contentores OpenShell em execução.

### Opcional: nome explícito da sandbox

Se a deteção automática não funcionar, indique ao ClawMetry a sandbox correta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### A executar dentro da sandbox (avançado)

Se precisar de executar o daemon de sincronização **dentro** da sandbox OpenShell, adicione esta regra de saída (egress) à sua política de rede NemoClaw para que possa alcançar a API de ingestão do ClawMetry:

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
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Para deteção de sessões em contentores |

O daemon de sincronização apenas faz chamadas HTTPS de saída para `ingest.clawmetry.com`. Não são necessárias portas de entrada.

---

## Implementação na Cloud

Consulte o **[Guia de Testes na Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com o BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia pings anónimos do ciclo de vida da instalação para
`https://app.clawmetry.com/api/install`: um ping `install` na primeira
vez que executa a CLI `clawmetry` numa nova máquina, um ping `update`
na primeira execução após atualizar para uma nova versão, e um ping
`onboarded` quando completa a escolha de onboarding no painel. Usamos
isto para contar instalações reais (os números brutos de downloads do
PyPI são ~98% espelhos, CI, e re-downloads de atualização automática)
e para saber quais as frameworks e versões de agentes que estão
realmente a ser usadas.

**No máximo um POST por evento do ciclo de vida por versão**, contendo:

| Campo | Exemplo | Motivo |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; anónimo até ligar explicitamente a sincronização na Cloud (o heartbeat autenticado do daemon passa a transportá-lo, ligando esta instalação à sua conta) |
| `event` | `install` / `update` / `onboarded` | instalação nova vs. atualização de uma existente |
| `version` | `0.12.167` | quais as versões que estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com que agentes devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a cloud deriva o código do país no lado do
servidor a partir do pedido e depois descarta o IP), nome de anfitrião,
nome de utilizador, caminho do workspace, conteúdo de ficheiros, a sua
api_key, o seu email, nada que seja PII ou específico do workspace. O
payload transmitido é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desativar** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Uma falha de rede aqui nunca bloqueia a execução do `clawmetry` — o
ping é fire-and-forget numa thread do daemon com um timeout de 3 s.

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
