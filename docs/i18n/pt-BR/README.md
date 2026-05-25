<!-- i18n-src:56ff57310588 -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para agentes de IA do [OpenClaw](https://github.com/openclaw/openclaw).

> 🌐 **Leia isto em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## O Que Você Recebe

- **Flow** — Diagrama animado ao vivo mostrando as mensagens fluindo pelos canais, pelo cérebro, pelas ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informações do modelo
- **Usage** — Rastreamento de tokens e custo com detalhamentos diários/semanais/mensais
- **Sessions** — Sessões ativas do agente com modelo, tokens e última atividade
- **Crons** — Tarefas agendadas com status, próxima execução e duração
- **Logs** — Streaming de logs em tempo real com cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md e notas diárias
- **Transcripts** — Interface de balões de chat para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos por taxa de erro, detecção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram e Email
- **Approvals** — Bloqueie exclusões destrutivas, force pushes, mutações de banco de dados, sudo, instalações de pacotes e chamadas de rede atrás de uma aprovação com um clique

## Capturas de Tela

### 🧠 Brain — Stream ao vivo de eventos do agente
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

### 🚨 Alerts — Limites de orçamento, gatilhos por taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueie chamadas de ferramentas arriscadas atrás de aprovação manual; regras de proteção respaldadas por política
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalação

**Linha única (recomendado):**
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

O app React v2 fica em `frontend/` e é servido em `/v2` quando o servidor
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

Abra `http://localhost:5173/v2/`. O Vite faz proxy das requisições `/api` para
`http://localhost:8900`, então o app React consegue se comunicar com o servidor Flask local
sem configuração extra de CORS.

Para gerar o bundle que acompanha o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é escrito em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtime / Agente

A ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não é o OpenClaw vem com um adaptador de leitura dedicado que traduz o formato de sessão nativo dele para as formas unificadas da ClawMetry; o daemon os ingere no mesmo armazenamento DuckDB + snapshot de nuvem, marcados com o runtime, e a aba de replay de sessão mostra um **seletor de runtime** quando há mais de um presente. Veja [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

| Runtime / Agente | Status | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detectado automaticamente |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
| **NanoClaw** | Adaptador beta | SQLite por sessão (`data/v2-sessions`). Transcrições + contagem de mensagens. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas de ferramentas + raciocínio, uso de tokens. |
| **Codex** | Adaptador beta | JSONL de rollout `~/.codex/sessions/...`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcrições de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagem de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas de ferramentas, totais de tokens. |

"Adaptador beta" significa que a ClawMetry fornece um leitor para o formato real em disco daquele runtime, cada um construído + verificado contra uma instalação real em uma máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são somente leitura; cada um é honesto sobre o que seu runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não gravam o custo de tokens em disco). Quando vários runtimes rodam em um nó, o seletor de runtime delimita a visualização de sessões a um deles para um mergulho profundo e limpo.

## OpenTelemetry — neutro em relação a fornecedores, envie seus traces para qualquer lugar

A ClawMetry fala **OpenTelemetry** nos dois sentidos, usando as **convenções semânticas GenAI**, então os traces do seu agente nunca ficam presos a uma única ferramenta.

**Exporte** cada sessão — chamadas de LLM, ferramentas, sub-agentes, tokens, custo — como spans GenAI OTLP/HTTP para qualquer collector (Datadog, Grafana, Honeycomb ou seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Cabeçalhos de autenticação e o intervalo de polling são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingestão** — o receptor OTLP embutido aceita traces e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão de protobuf).

Você obtém o dashboard da ClawMetry, com zero configuração e local-first, **e** seus dados em qualquer backend que sua equipe já usa, sem aprisionamento e sem um segundo agente para instalar.

## Configuração

A maioria das pessoas não precisa de nenhuma configuração. A ClawMetry detecta automaticamente seu workspace, logs, sessões e crons.

Se você precisar personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas as opções: `clawmetry --help`

## Canais Suportados

A ClawMetry mostra atividade ao vivo de cada canal do OpenClaw que você tem configurado. Apenas os canais que estão de fato configurados no seu `openclaw.json` aparecem no diagrama Flow; os não configurados são ocultados automaticamente.

Clique em qualquer nó de canal no Flow para ver uma visualização ao vivo de balões de chat com a contagem de mensagens recebidas/enviadas.

| Canal | Status | Popup ao Vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detecção de guild + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detecção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões da interface web embutida |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões em estilo de terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipe auto-hospedado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte a E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizadas NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via conexão IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Assinatura de eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detecção automática:** A ClawMetry lê o seu `~/.openclaw/openclaw.json` e só renderiza os canais que você realmente configurou. Nenhuma configuração manual é necessária.

## Implantação com Docker

Quer rodar a ClawMetry em um contêiner? Sem problemas! 🐳

**Início rápido com Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **Nota:** Ao rodar no Docker, certifique-se de montar seu workspace do OpenClaw e os diretórios de log para que a ClawMetry possa detectar automaticamente sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- OpenClaw rodando na mesma máquina (ou volumes montados para Docker)
- Linux ou macOS

## Suporte a NemoClaw / OpenShell

A ClawMetry detecta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw) — o wrapper de segurança corporativa da NVIDIA para o OpenClaw que roda agentes dentro de contêineres OpenShell em sandbox.

Nenhuma configuração extra é necessária na maioria dos casos. O daemon de sincronização descobre automaticamente os arquivos de sessão, estejam eles em `~/.openclaw/` no host ou dentro de um contêiner OpenShell.

### Como funciona

A ClawMetry detecta o NemoClaw de duas maneiras:

1. **Detecção de binário** — verifica a CLI `nemoclaw` e executa `nemoclaw status` para obter informações da sandbox
2. **Detecção de contêiner** — varre os contêineres Docker em execução em busca de imagens `openshell`, `nemoclaw` ou `ghcr.io/nvidia/`, então lê as sessões via montagens de volume ou `docker cp`

Os arquivos de sessão sincronizados de contêineres NemoClaw são marcados com os metadados `runtime=nemoclaw` e `container_id` no dashboard de nuvem, para que você possa distingui-los das sessões padrão do OpenClaw num relance.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, rode o daemon de sincronização da ClawMetry na **máquina host** (não dentro da sandbox). Isso evita as restrições de política de rede do NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente as sessões dentro de qualquer contêiner OpenShell em execução.

### Opcional: nome explícito da sandbox

Se a detecção automática não funcionar, aponte a ClawMetry para a sandbox correta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Rodando dentro da sandbox (avançado)

Se você precisar rodar o daemon de sincronização **dentro** da sandbox OpenShell, adicione esta regra de egress à sua política de rede do NemoClaw para que ele possa alcançar a API de ingestão da ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Sim (interface do dashboard local) |
| Socket do Docker (`/var/run/docker.sock`) | — | Unix socket | Para descoberta de sessões em contêineres |

O daemon de sincronização só faz chamadas HTTPS de saída para `ingest.clawmetry.com`. Nenhuma porta de entrada é necessária.

---

## Implantação na Nuvem

Veja o **[Guia de Testes na Nuvem](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com o BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

A ClawMetry envia um único ping anônimo de "primeira execução" para
`https://app.clawmetry.com/api/install` na primeira vez que você executa a
CLI `clawmetry` em uma nova máquina. Usamos isso para contar instalações (a
única métrica de marketing que temos para um projeto OSS) e para descobrir quais
frameworks de agente nossos usuários têm instalados.

**Exatamente um POST por instalação**, contendo:

| Campo | Exemplo | Por quê |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; não vinculado ao seu email ou api_key |
| `version` | `0.12.167` | quais versões estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com quais agentes devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas do ruído de CI |

**O que NÃO enviamos**: IP (a nuvem deriva o código do país no servidor
a partir da requisição e depois descarta o IP), hostname, nome de usuário, caminho
do workspace, conteúdo de arquivos, sua api_key, seu email, qualquer coisa de PII ou
específica do workspace. O payload de transmissão é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Cancelar a participação** (qualquer um destes a desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Uma falha de rede aqui nunca impede o `clawmetry` de rodar; o
ping é "dispare e esqueça" em uma thread de daemon com timeout de 3 s.

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
