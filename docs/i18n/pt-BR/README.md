<!-- i18n-src:48548997be76 -->
> Português (BR) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Veja seu agente pensar.** Observabilidade em tempo real para **12 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e mais 8. Um único painel para toda a sua frota de agentes.

> 🌐 **Leia em:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mais →](docs/i18n/)

Um comando. Zero configuração. Detecta tudo automaticamente.

```bash
pip install clawmetry && clawmetry
```

Abre em **http://localhost:8900** e pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatível com 12 runtimes de agentes

ClawMetry começou como observabilidade para OpenClaw e agora monitora toda a sua **frota de agentes** em um único painel, detectando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw e NemoClaw são gratuitos no aplicativo de código aberto; os demais runtimes são ativados com ClawMetry Cloud ou uma licença Pro auto-hospedada. Troque de runtime pelo cabeçalho e todas as abas — custo, tokens, ferramentas, rastreamentos — são reescopadas para aquele runtime.

## O que você obtém

- **Flow** — Diagrama animado ao vivo mostrando mensagens fluindo por canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de integridade, mapa de calor de atividade, contagem de sessões, informações de modelo
- **Usage** — Rastreamento de tokens e custos com recortes diários/semanais/mensais
- **Sessions** — Sessões ativas do agente com modelo, tokens e última atividade
- **Crons** — Tarefas agendadas com status, próxima execução e duração
- **Logs** — Streaming de logs em tempo real com coloração por tipo
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md e anotações diárias
- **Transcripts** — Interface de bolhas de chat para leitura do histórico de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erros, detecção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram e e-mail
- **Approvals** — Bloqueie exclusões destrutivas, force pushes, mutações de banco de dados, sudo, instalações de pacotes e chamadas de rede atrás de uma aprovação com um clique

## Capturas de tela

### 🧠 Brain — Stream de eventos do agente ao vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Detalhamento de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de arquivos do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e log de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erros, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueie chamadas de ferramentas arriscadas com aprovação manual; regras de proteção baseadas em políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalação

**Uma linha (recomendado):**
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

O aplicativo React v2 fica em `frontend/` e é servido em `/v2` quando o servidor Flask é iniciado com o v2 habilitado.

Use dois terminais durante o desenvolvimento:

```bash
# Terminal 1: API/servidor Flask em :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Servidor de desenvolvimento Vite em :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abra `http://localhost:5173/v2/`. O Vite faz proxy das requisições `/api` para `http://localhost:8900`, de modo que o aplicativo React consegue se comunicar com o servidor Flask local sem configuração extra de CORS.

Para compilar o pacote que acompanha o pacote Python:

```bash
cd frontend
npm run build
```

O pacote de produção é gravado em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

ClawMetry observa muitos runtimes de agentes de IA, não apenas OpenClaw. Cada runtime não-OpenClaw possui um adaptador de leitura dedicado que traduz seu formato de sessão nativo para as estruturas unificadas do ClawMetry; o daemon os ingere no mesmo armazenamento DuckDB e snapshot em nuvem, marcados com o runtime, e a aba de replay de sessão exibe um **seletor de runtime** quando mais de um está presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa e um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para uma introdução à família OpenClaw.

| Runtime / Agente | Status | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detectado automaticamente |
| **PicoClaw** | Adaptador beta | JSONL `providers.Message` simples (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
| **NanoClaw** | Adaptador beta | SQLite por sessão (`data/v2-sessions`). Transcrições e contagens de mensagens. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas de ferramentas com raciocínio, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcrições de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagens de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas de ferramentas, totais de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcrições, modelo, chamadas de ferramentas, tokens e custo. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcrições, modelo, chamadas de ferramentas, uso de tokens. |

"Adaptador beta" significa que o ClawMetry inclui um leitor para o formato em disco real daquele runtime, cada um construído e verificado contra uma instalação real em uma máquina real (veja `tests/fixtures/runtimes/<rt>/`). Os adaptadores são somente leitura; cada um é honesto sobre o que seu runtime realmente armazena em disco (por exemplo, PicoClaw/NanoClaw/Cursor não gravam custo de tokens no disco). Quando vários runtimes rodam em um único nó, o seletor de runtime escopa a visualização de sessões para um deles, permitindo uma análise aprofundada sem ruído.

## Rastreie qualquer agente SDK — atribuição de custo fora do loop

Os runtimes acima todos gravam sessões em disco. O seu **agente em produção** — aquele que você construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B ou um simples loop `httpx` — não grava. O interceptor zero-config do ClawMetry ainda captura suas chamadas de LLM (custo, tokens, latência, erros) fazendo monkey-patch em `httpx`/`requests`:

```python
import clawmetry.track            # ativa o interceptor
clawmetry.track.set_source("support-agent")   # dê um nome a este produto

# ...seu agente roda normalmente; toda chamada de LLM é rastreada e atribuída.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) marca cada chamada com uma **fonte nomeada**, para que cada produto que você rodar apareça como sua própria linha atribuível de custo no card **🔌 Fontes fora do loop** no Overview — chamadas, provedores, latência, taxa de erros por agente. Sem fonte definida? As chamadas ainda são rastreadas; o card simplesmente permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que os adaptadores de runtime alimentam (DuckDB → snapshot em nuvem), então as fontes fora do loop sincronizam para o painel na nuvem da mesma forma que todo o restante, com criptografia de ponta a ponta.

## OpenTelemetry — neutro em relação a fornecedores, envie seus rastreamentos para qualquer lugar

O ClawMetry fala **OpenTelemetry** nos dois sentidos, usando as **convenções semânticas GenAI**, para que os rastreamentos do seu agente nunca fiquem presos em uma única ferramenta.

**Exporte** cada sessão — chamadas de LLM, ferramentas, subagentes, tokens, custo — como spans GenAI OTLP/HTTP para qualquer coletor (Datadog, Grafana, Honeycomb ou seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalentemente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Cabeçalhos de autenticação e intervalo de envio são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # cabeçalhos HTTP extras
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (padrão 60)
```

**Ingira** — o receptor OTLP embutido aceita rastreamentos e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão via protobuf).

Você obtém o painel ClawMetry zero-config e local **e** seus dados em qualquer backend que sua equipe já utiliza, sem lock-in e sem precisar instalar um segundo agente.

## Configuração

A maioria das pessoas não precisa de nenhuma configuração. ClawMetry detecta automaticamente seu workspace, logs, sessões e crons.

Se precisar personalizar:

```bash
clawmetry --port 9000              # Porta personalizada (padrão: 8900)
clawmetry --host 127.0.0.1         # Vincular apenas ao localhost
clawmetry --workspace ~/mybot      # Caminho de workspace personalizado
clawmetry --name "Alice"           # Seu nome na visualização Flow
```

Todas as opções: `clawmetry --help`

## Canais Suportados

ClawMetry exibe a atividade ao vivo de cada canal OpenClaw que você configurou. Apenas os canais efetivamente configurados no seu `openclaw.json` aparecem no diagrama Flow — os não configurados são automaticamente ocultados.

Clique em qualquer nó de canal no Flow para ver uma visualização de bolhas de chat ao vivo com contagens de mensagens recebidas e enviadas.

| Canal | Status | Popup Ao Vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detecção de guild e canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detecção de workspace e canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões de interface web embutida |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de bolhas no estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipe auto-hospedado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte a E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via conexão IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Assinatura de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detecção automática:** ClawMetry lê seu `~/.openclaw/openclaw.json` e renderiza apenas os canais que você realmente configurou. Nenhuma configuração manual é necessária.

## Implantação com Docker

Quer rodar ClawMetry em um container? Sem problema! 🐳

**Início rápido com Docker:**

```bash
# Construir a imagem
docker build -t clawmetry .

# Rodar com as configurações padrão
docker run -p 8900:8900 clawmetry

# Ou montar o diretório de dados do seu agente (exemplo: ~/.openclaw do OpenClaw)
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

> **Nota:** Ao rodar no Docker, monte os diretórios de dados e logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry consiga detectar automaticamente sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw ou PicoClaw (ou volumes montados para Docker)
- Linux ou macOS

## Suporte a NemoClaw / OpenShell

ClawMetry detecta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw) — o wrapper de segurança empresarial da NVIDIA para OpenClaw, que executa agentes dentro de containers OpenShell em sandbox.

Na maioria dos casos, nenhuma configuração extra é necessária. O daemon de sincronização descobre automaticamente os arquivos de sessão, estejam eles em `~/.openclaw/` no host ou dentro de um container OpenShell.

### Como funciona

ClawMetry detecta NemoClaw de duas formas:

1. **Detecção de binário** — verifica a presença do CLI `nemoclaw` e executa `nemoclaw status` para obter informações do sandbox
2. **Detecção de container** — examina containers Docker em execução em busca de imagens `openshell`, `nemoclaw` ou `ghcr.io/nvidia/`, e lê as sessões via montagens de volume ou `docker cp`

Arquivos de sessão sincronizados de containers NemoClaw são marcados com metadados `runtime=nemoclaw` e `container_id` no painel na nuvem, para que você possa distingui-los das sessões padrão do OpenClaw à primeira vista.

### Configuração recomendada: daemon de sincronização no HOST

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina host** (fora do sandbox). Isso evita restrições de política de rede do NemoClaw.

```bash
# No host (fora do sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente as sessões dentro de quaisquer containers OpenShell em execução.

### Opcional: nome explícito do sandbox

Se a detecção automática não funcionar, aponte o ClawMetry para o sandbox correto:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Rodando dentro do sandbox (avançado)

Se for necessário rodar o daemon de sincronização **dentro** do sandbox OpenShell, adicione esta regra de saída à sua política de rede do NemoClaw para que ele consiga acessar a API de ingestão do ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Sim (interface local do painel) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para descoberta de sessões em containers |

O daemon de sincronização realiza apenas chamadas HTTPS de saída para `ingest.clawmetry.com`. Nenhuma porta de entrada é necessária.

---

## Implantação na Nuvem

Consulte o **[Guia de Testes na Nuvem](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry envia um único ping anônimo de "primeira execução" para
`https://app.clawmetry.com/api/install` na primeira vez que você executa o
CLI `clawmetry` em uma nova máquina. Usamos isso para contar instalações (a
única métrica de marketing que temos para um projeto OSS) e para saber quais
frameworks de agentes nossos usuários têm instalados.

**Exatamente um POST por instalação**, contendo:

| Campo | Exemplo | Por quê |
|---|---|---|
| `install_id` | UUID aleatório armazenado em `~/.clawmetry/install_id` | deduplicação; não vinculado ao seu e-mail ou api_key |
| `version` | `0.12.167` | quais versões estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte a plataformas |
| `python` | `3.11.15` | matriz de suporte a versões do Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com quais agentes devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas do ruído de CI |

**O que NÃO enviamos**: IP (a nuvem deriva o código do país no servidor a partir da requisição e então descarta o IP), hostname, nome de usuário, caminho do workspace, conteúdo de arquivos, sua api_key, seu e-mail, nenhum dado PII ou específico do workspace. O payload transmitido é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Como desativar** (qualquer uma destas opções desativa permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por shell
export DO_NOT_TRACK=1                          # padrão W3C entre ferramentas
touch ~/.clawmetry/notelemetry                 # marcador de arquivo persistente
```

Uma falha de rede aqui nunca impede o `clawmetry` de rodar — o ping é disparado e esquecido em uma thread daemon com timeout de 3 segundos.

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
  <sub>Desenvolvido por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte do ecossistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
