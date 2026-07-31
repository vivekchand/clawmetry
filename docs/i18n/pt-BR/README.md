<!-- i18n-src:8252f6b1d31d -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para **14 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 10. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 14 runtimes de agentes

O ClawMetry começou como observabilidade para o OpenClaw e agora monitora toda a sua **frota de agentes** em um único painel, detectando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw e NemoClaw são gratuitos no app de código aberto; os demais runtimes são liberados com o ClawMetry Cloud ou uma licença Pro autogerenciada. Troque de runtime pelo cabeçalho e cada aba, custo, tokens, ferramentas, traces, reajusta o escopo para esse runtime. Veja **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, o formato de `/api/entitlement` e a CLI `clawmetry license`.

## O que você recebe

- **Flow** — Diagrama animado ao vivo mostrando mensagens fluindo por canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informações do modelo
- **Usage** — Rastreamento de tokens e custos com detalhamento diário/semanal/mensal
- **Sessions** — Sessões de agentes ativas com modelo, tokens, última atividade
- **Crons** — Jobs agendados com status, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface de balões de chat para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, detecção de agente offline; roteia para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloqueia exclusões destrutivas, force pushes, mutações de banco de dados, sudo, instalações de pacotes, chamadas de rede atrás de uma aprovação com um clique

## Capturas de tela

### 🧠 Brain — Fluxo de eventos do agente ao vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Detalhamento de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de arquivos do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura e log de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueia chamadas de ferramentas arriscadas atrás de aprovação manual; regras de proteção baseadas em política
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueio pré-execução para Claude Code** — um comando instala um
hook PreToolUse que pausa as chamadas de ferramentas correspondentes *antes* de
serem executadas e aguarda sua decisão (um toque a partir do seu celular com
[notificações push na nuvem](https://app.clawmetry.com/push) habilitadas):

```bash
clawmetry hooks install     # escreve ~/.claude/settings.json (idempotente)
clawmetry hooks status      # o que está conectado + quantas políticas estão ativas
clawmetry hooks uninstall   # remove apenas as entradas do ClawMetry
```

Uma negação bloqueia apenas aquela chamada de ferramenta específica, o agente mantém sua sessão e pode
tentar outra abordagem. Aprovar pelo celular pula o próprio prompt de
permissão do Claude Code (você já respondeu). Ferramentas não correspondentes custam ~40ms e
seguem para o fluxo de permissão normal do Claude Code. Você também recebe um push no celular quando o Claude Code
está aguardando sua resposta (notificações `permission_prompt` /
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

## Desenvolvimento do Frontend v2

O app React v2 está em `frontend/` e é servido em `/v2` quando o servidor
Flask é iniciado com o v2 habilitado.

Use dois terminais durante o desenvolvimento:

```bash
# Terminal 1: Flask API/server na porta :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Servidor de desenvolvimento Vite na porta :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abra `http://localhost:5173/v2/`. O Vite faz proxy das requisições `/api` para
`http://localhost:8900`, então o app React consegue conversar com o servidor Flask local
sem configuração extra de CORS.

Para gerar o bundle que é distribuído com o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é gravado em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtime / Agente

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw traz um adaptador leitor dedicado que traduz o formato nativo de sessões desse runtime para os formatos unificados do ClawMetry; o daemon os ingere no mesmo armazenamento DuckDB + snapshot na nuvem, marcados com o runtime, e a aba Session replay mostra um **seletor de runtime** quando mais de um está presente. Veja [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

| Runtime / Agente | Status | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detectado automaticamente |
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
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Execuções de workflow, execuções de nós, prompts do AI Agent, modelo + tokens onde o n8n os registra. |

"Adaptador beta" significa que o ClawMetry distribui um leitor para o formato real em disco daquele runtime, cada um construído + verificado em uma instalação real, em uma máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são somente leitura; cada um é transparente sobre o que o runtime de fato armazena (por exemplo, PicoClaw/NanoClaw/Cursor não gravam o custo de tokens em disco). Quando vários runtimes rodam em um nó, o seletor de runtime restringe a visão de sessões a um deles para uma investigação mais focada.

## Rastreie qualquer agente de SDK — atribuição de custo out-loop

Os runtimes acima escrevem sessões em disco. Já o seu próprio **agente de produção** — aquele que você construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um loop simples com `httpx` — não faz isso. O interceptor sem configuração do ClawMetry ainda captura suas chamadas de LLM (custo, tokens, latência, erros) fazendo monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # ativa o interceptor
clawmetry.track.set_source("support-agent")   # nomeia este produto

# ...seu agente roda normalmente; toda chamada de LLM agora é rastreada + atribuída.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) marca cada chamada com uma **origem nomeada**, de modo que cada produto que você roda aparece como sua própria linha de primeira classe, atribuível por custo, no card **🔌 Out-loop sources** do Overview no painel: chamadas, provedores, latência, taxa de erro por agente. Sem origem definida? As chamadas continuam sendo rastreadas; o card apenas fica oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados alimentada pelos adaptadores de runtime (DuckDB → snapshot na nuvem), então as origens out-loop sincronizam com o painel na nuvem da mesma forma que tudo o mais, com criptografia ponta a ponta.

## OpenTelemetry — neutro em relação a fornecedores, envie seus traces para qualquer lugar

O ClawMetry fala **OpenTelemetry** em ambas as direções, usando as **convenções semânticas GenAI**, então os traces do seu agente nunca ficam presos a uma única ferramenta.

**Exporte** cada sessão — chamadas de LLM, ferramentas, subagentes, tokens, custo — como spans GenAI OTLP/HTTP para qualquer coletor (Datadog, Grafana, Honeycomb, ou seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Cabeçalhos de autenticação e intervalo de sondagem são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # cabeçalhos HTTP extras
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (padrão 60)
```

**Ingestão** — o receptor OTLP embutido aceita traces e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão via protobuf).

Você tem o painel ClawMetry sem configuração e local em primeiro lugar **e** seus dados no backend que sua equipe já usa, sem aprisionamento, sem precisar instalar um segundo agente.

## Configuração

A maioria das pessoas não precisa de nenhuma configuração. O ClawMetry detecta automaticamente seu workspace, logs, sessões e crons.

Se você precisar personalizar:

```bash
clawmetry --port 9000              # Porta personalizada (padrão: 8900)
clawmetry --host 127.0.0.1         # Vincula apenas ao localhost
clawmetry --workspace ~/mybot      # Caminho de workspace personalizado
clawmetry --name "Alice"           # Seu nome na visualização Flow
```

Todas as opções: `clawmetry --help`

## Canais Suportados

O ClawMetry mostra atividade ao vivo para cada canal do OpenClaw que você tiver configurado. Apenas os canais que estão de fato configurados no seu `openclaw.json` aparecem no diagrama Flow; os não configurados ficam automaticamente ocultos.

Clique em qualquer nó de canal no Flow para ver uma visualização em balões de chat ao vivo com contagens de mensagens recebidas/enviadas.

| Canal | Status | Popup ao vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detecção de guild + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detecção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões da interface web embutida |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipe autogerenciado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, com suporte a E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizadas NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via conexão IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Assinatura de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detecção automática:** O ClawMetry lê seu `~/.openclaw/openclaw.json` e renderiza apenas os canais que você de fato configurou. Nenhuma configuração manual é necessária.

## Implantação com Docker

Quer rodar o ClawMetry em um container? Sem problema! 🐳

**Início rápido com Docker:**

```bash
# Construa a imagem
docker build -t clawmetry .

# Execute com configurações padrão
docker run -p 8900:8900 clawmetry

# Ou monte o diretório de dados do seu agente (mostrado: o ~/.openclaw do OpenClaw)
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

> **Observação:** Ao rodar no Docker, monte os diretórios de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry consiga detectar automaticamente sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, ou n8n (ou volumes montados para Docker)
- Linux ou macOS

## Suporte a NemoClaw / OpenShell

O ClawMetry detecta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para o OpenClaw, que executa agentes dentro de containers OpenShell isolados (sandboxed).

Nenhuma configuração extra é necessária na maioria dos casos. O daemon de sincronização descobre automaticamente os arquivos de sessão, estejam eles em `~/.openclaw/` no host ou dentro de um container OpenShell.

### Como funciona

O ClawMetry detecta o NemoClaw de duas formas:

1. **Detecção de binário** — verifica a CLI `nemoclaw` e executa `nemoclaw status` para obter informações do sandbox
2. **Detecção de container** — escaneia containers Docker em execução em busca de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e então lê as sessões via volumes montados ou `docker cp`

Os arquivos de sessão sincronizados a partir de containers NemoClaw são marcados com `runtime=nemoclaw` e metadados `container_id` no painel na nuvem, para que você consiga diferenciá-los das sessões padrão do OpenClaw rapidamente.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina host** (não dentro do sandbox). Isso evita restrições da política de rede do NemoClaw.

```bash
# No host (fora do sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente as sessões dentro de quaisquer containers OpenShell em execução.

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

## Implantação na Nuvem

Veja o **[Guia de Testes na Nuvem](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia pings anônimos de ciclo de vida de instalação para
`https://app.clawmetry.com/api/install`: um ping `install` na primeira
vez que você executa a CLI `clawmetry` em uma máquina nova, um ping `update`
na primeira execução após atualizar para uma nova versão, e um ping `onboarded`
quando você completa a escolha de onboarding no painel. Usamos isso
para contar instalações reais (os números brutos de downloads do PyPI são ~98% mirrors, CI,
e redownloads de auto-atualização) e para saber quais frameworks de agentes e
versões estão de fato em uso.

**No máximo um POST por evento de ciclo de vida por versão**, contendo:

| Campo | Exemplo | Motivo |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; anônimo até você conectar explicitamente a sincronização com a nuvem (o heartbeat autenticado do daemon então carrega isso, vinculando esta instalação à sua conta) |
| `event` | `install` / `update` / `onboarded` | instalação nova vs. atualização de uma existente |
| `version` | `0.12.167` | quais versões estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versão do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com quais agentes devemos integrar em seguida |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separa instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a nuvem deriva o código do país no lado do servidor
a partir da requisição, e então descarta o IP), hostname, nome de usuário, caminho do workspace,
conteúdo de arquivos, sua api_key, seu e-mail, nada de PII ou
específico do workspace. O payload trafegado é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desativar** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por shell
export DO_NOT_TRACK=1                          # padrão W3C entre ferramentas
touch ~/.clawmetry/notelemetry                 # marcador de arquivo persistente
```

Uma falha de rede aqui nunca impede o `clawmetry` de rodar, o
ping é fire-and-forget em uma thread do daemon com timeout de 3s.

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
  <strong>🦞 Veja seu agente pensar</strong><br>
  <sub>Construído por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte do ecossistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
