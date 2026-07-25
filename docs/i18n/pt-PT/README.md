<!-- i18n-src:8f42d460a973 -->
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

Abre em **http://localhost:8900** e está pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona com 14 runtimes de agentes

O ClawMetry começou como observabilidade para o OpenClaw e agora mede **toda a sua frota de agentes** num único painel, detetando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

O OpenClaw e o NemoClaw são gratuitos na aplicação open-source; os restantes runtimes ficam disponíveis com o ClawMetry Cloud ou uma licença Pro autoalojada. Mude de runtime a partir do cabeçalho e cada separador, custo, tokens, ferramentas, traces, reajusta-se a esse runtime. Consulte **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, o formato de `/api/entitlement` e a CLI `clawmetry license`.

## O que obtém

- **Flow** — Diagrama animado ao vivo que mostra as mensagens a fluir através de canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informação do modelo
- **Usage** — Acompanhamento de tokens e custos com detalhes diários/semanais/mensais
- **Sessions** — Sessões de agente ativas com modelo, tokens, última atividade
- **Crons** — Tarefas agendadas com estado, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com código de cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface em balões de conversa para ler históricos de sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, deteção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloqueia eliminações destrutivas, force pushes, mutações de base de dados, sudo, instalações de pacotes, chamadas de rede atrás de uma aprovação com um clique

## Capturas de ecrã

### 🧠 Brain — Stream ao vivo de eventos do agente
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed em tempo real de chamadas a ferramentas
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Detalhe de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de ficheiros do workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e registo de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueia chamadas a ferramentas arriscadas atrás de aprovação manual; regras de proteção com base em políticas
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

A aplicação React v2 reside em `frontend/` e é servida em `/v2` quando o
servidor Flask é iniciado com a v2 ativada.

Use dois terminais durante o desenvolvimento:

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

Abra `http://localhost:5173/v2/`. O Vite encaminha os pedidos `/api` para
`http://localhost:8900`, para que a aplicação React possa comunicar com o
servidor Flask local sem configuração de CORS adicional.

Para criar o bundle que é distribuído com o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é gravado em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw tem um adaptador de leitura dedicado que traduz o formato nativo das suas sessões para as formas unificadas do ClawMetry; o daemon ingere-os no mesmo repositório DuckDB + snapshot na cloud, etiquetados com o runtime, e o separador de replay de sessões mostra um **seletor de runtime** quando existe mais do que um presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, deteção automática |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas a ferramentas. |
| **NanoClaw** | Adaptador beta | SQLite por sessão (`data/v2-sessions`). Transcrições + contagem de mensagens. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcrições, modelo, tokens/custo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcrições, modelo, chamadas a ferramentas + raciocínio, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcrições, modelo, chamadas a ferramentas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcrições de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por projeto. Transcrições, modelo, contagem de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcrições, modelo, chamadas a ferramentas, totais de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcrições, modelo, chamadas a ferramentas, tokens + custo. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcrições, modelo, chamadas a ferramentas, uso de tokens. |
| **Pi** | Adaptador beta | JSONL `~/.pi/agent/sessions`. Transcrições, modelo, chamadas a ferramentas, tokens + custo. |
| **Deep Agents** | Adaptador beta | SQLite `~/.deepagents/.state/sessions.db`. Transcrições, modelo, chamadas a ferramentas, tokens + custo. |

"Adaptador beta" significa que o ClawMetry disponibiliza um leitor para o formato real em disco desse runtime, cada um construído e verificado com base numa instalação real numa máquina real (ver `tests/fixtures/runtimes/<rt>/`). Os adaptadores são apenas de leitura; cada um é transparente sobre o que o seu runtime realmente armazena (por exemplo, PicoClaw/NanoClaw/Cursor não gravam o custo de tokens em disco). Quando vários runtimes correm num só nó, o seletor de runtime restringe a vista de sessões a um, para uma análise aprofundada mais limpa.

## Acompanhe qualquer agente SDK — atribuição de custos fora do loop

Os runtimes acima escrevem todos as suas sessões em disco. O seu **agente de produção** próprio, aquele que construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um simples loop `httpx`, não o faz. O interceptor de configuração zero do ClawMetry continua a capturar as suas chamadas LLM (custo, tokens, latência, erros) através de monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # ativa o interceptor
clawmetry.track.set_source("support-agent")   # nomeia este produto

# ...o seu agente corre normalmente; cada chamada LLM é agora rastreada + atribuída.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) etiqueta cada chamada com uma **origem nomeada**, de forma que cada produto que executa aparece como a sua própria linha de primeira classe, atribuível a custos, no cartão **🔌 Out-loop sources** do Overview no painel, chamadas, fornecedores, latência, taxa de erro por agente. Nenhuma origem definida? As chamadas continuam a ser rastreadas; o cartão apenas permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que os adaptadores de runtime alimentam (DuckDB → snapshot na cloud), pelo que as origens fora do loop sincronizam com o painel na cloud da mesma forma que tudo o resto, com encriptação ponta a ponta.

## OpenTelemetry — neutro em relação ao fornecedor, envie os seus traces para qualquer lugar

O ClawMetry fala **OpenTelemetry** em ambas as direções, usando as **convenções semânticas GenAI**, para que os traces do seu agente nunca fiquem presos a uma única ferramenta.

**Exporte** cada sessão, chamadas LLM, ferramentas, subagentes, tokens, custo, como spans OTLP/HTTP GenAI para qualquer coletor (Datadog, Grafana, Honeycomb, ou o seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalentemente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Os cabeçalhos de autenticação e o intervalo de sondagem são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # cabeçalhos HTTP extra
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (predefinição 60)
```

**Ingestão** — o recetor OTLP incorporado aceita traces e métricas de qualquer outra fonte em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão protobuf).

Obtém o painel ClawMetry de configuração zero e local-first **e** os seus dados no backend que a sua equipa já utiliza, sem aprisionamento, sem um segundo agente para instalar.

## Configuração

A maioria das pessoas não precisa de qualquer configuração. O ClawMetry deteta automaticamente o seu workspace, logs, sessões e crons.

Se precisar de personalizar:

```bash
clawmetry --port 9000              # Porta personalizada (predefinição: 8900)
clawmetry --host 127.0.0.1         # Vincula apenas ao localhost
clawmetry --workspace ~/mybot      # Caminho de workspace personalizado
clawmetry --name "Alice"           # O seu nome na visualização Flow
```

Todas as opções: `clawmetry --help`

## Canais Suportados

O ClawMetry mostra atividade ao vivo para cada canal OpenClaw que tenha configurado. Apenas os canais que estão realmente configurados no seu `openclaw.json` aparecem no diagrama Flow, os não configurados são automaticamente ocultados.

Clique em qualquer nó de canal no Flow para ver uma vista de balões de chat ao vivo com contagens de mensagens recebidas/enviadas.

| Canal | Estado | Popup ao vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê `~/Library/Messages/chat.db` diretamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Deteção de guild + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Deteção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões de UI web integrada |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipa autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | Mensagens diretas descentralizadas NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via ligação IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Subscrição de eventos via WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Deteção automática:** O ClawMetry lê o seu `~/.openclaw/openclaw.json` e apenas apresenta os canais que efetivamente configurou. Não é necessária configuração manual.

## Implementação com Docker

Quer executar o ClawMetry num contentor? Sem problema! 🐳

**Início rápido com Docker:**

```bash
# Construir a imagem
docker build -t clawmetry .

# Executar com as definições predefinidas
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

> **Nota:** Ao executar no Docker, monte os diretórios de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry possa detetar automaticamente a sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, ou Deep Agents (ou volumes montados para Docker)
- Linux ou macOS

## Suporte para NemoClaw / OpenShell

O ClawMetry deteta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para o OpenClaw que executa agentes dentro de contentores OpenShell isolados (sandboxed).

Na maioria dos casos, não é necessária configuração adicional. O daemon de sincronização descobre automaticamente os ficheiros de sessão, quer residam em `~/.openclaw/` no anfitrião, quer dentro de um contentor OpenShell.

### Como funciona

O ClawMetry deteta o NemoClaw de duas formas:

1. **Deteção de binário** — verifica a CLI `nemoclaw` e executa `nemoclaw status` para obter informação do sandbox
2. **Deteção de contentor** — analisa os contentores Docker em execução à procura de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e depois lê as sessões via volumes montados ou `docker cp`

Os ficheiros de sessão sincronizados a partir de contentores NemoClaw são etiquetados com metadados `runtime=nemoclaw` e `container_id` no painel na cloud, para que os possa distinguir das sessões OpenClaw padrão à primeira vista.

### Configuração recomendada: daemon de sincronização no ANFITRIÃO

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina anfitriã** (não dentro do sandbox). Isto evita as restrições de política de rede do NemoClaw.

```bash
# No anfitrião (fora do sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização encontrará automaticamente sessões dentro de quaisquer contentores OpenShell em execução.

### Opcional: nome de sandbox explícito

Se a deteção automática não funcionar, aponte o ClawMetry para o sandbox correto:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Executar dentro do sandbox (avançado)

Se tiver de executar o daemon de sincronização **dentro** do sandbox OpenShell, adicione esta regra de saída (egress) à sua política de rede do NemoClaw para que consiga alcançar a API de ingestão do ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Sim (UI do painel local) |
| Socket do Docker (`/var/run/docker.sock`) | — | Socket Unix | Para deteção de sessões em contentores |

O daemon de sincronização só faz chamadas HTTPS de saída para `ingest.clawmetry.com`. Não é necessária nenhuma porta de entrada.

---

## Implementação na Cloud

Consulte o **[Guia de Testes na Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia um único ping anónimo de "primeira execução" para
`https://app.clawmetry.com/api/install` na primeira vez que executa a
CLI `clawmetry` numa nova máquina. Usamos isto para contar instalações
(a única métrica de marketing que temos para um projeto OSS) e para
saber quais as frameworks de agentes que os nossos utilizadores têm
instaladas.

**Exatamente um POST por instalação**, contendo:

| Campo | Exemplo | Porquê |
|---|---|---|
| `install_id` | UUID aleatório guardado em `~/.clawmetry/install_id` | deduplicação; não está associado ao seu email ou api_key |
| `version` | `0.12.167` | que versões estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com que agentes nos devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a cloud deriva o código do país no lado do
servidor a partir do pedido, e depois descarta o IP), nome de anfitrião,
nome de utilizador, caminho do workspace, conteúdo de ficheiros, a sua
api_key, o seu email, nada de PII ou específico do workspace. O payload
transmitido é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Recusar participação** (qualquer uma destas opções desativa-a permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por shell
export DO_NOT_TRACK=1                          # padrão W3C entre ferramentas
touch ~/.clawmetry/notelemetry                 # marcador de ficheiro persistente
```

Uma falha de rede aqui nunca bloqueia a execução do `clawmetry`, o ping
é do tipo fire-and-forget numa thread daemon com um timeout de 3 s.

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
