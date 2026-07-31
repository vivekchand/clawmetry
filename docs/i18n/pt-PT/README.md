<!-- i18n-src:8252f6b1d31d -->
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

O ClawMetry começou como observabilidade para o OpenClaw e agora mede toda a **sua frota de agentes** num único painel, detetando automaticamente cada runtime na sua máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

O OpenClaw e o NemoClaw são gratuitos na aplicação open-source; os restantes runtimes ficam disponíveis com o ClawMetry Cloud ou com uma licença Pro autoalojada. Mude de runtime a partir do cabeçalho e todos os separadores — custo, tokens, ferramentas, traces — reajustam-se a esse runtime. Consulte **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para a divisão exata entre gratuito/pago, a matriz de níveis, a forma do `/api/entitlement` e o CLI `clawmetry license`.

## O Que Obtém

- **Flow** — Diagrama animado ao vivo que mostra as mensagens a fluir através de canais, cérebro, ferramentas e de volta
- **Overview** — Verificações de saúde, mapa de calor de atividade, contagem de sessões, informação do modelo
- **Usage** — Acompanhamento de tokens e custos com detalhamentos diários/semanais/mensais
- **Sessions** — Sessões de agentes ativas com modelo, tokens, última atividade
- **Crons** — Tarefas agendadas com estado, próxima execução, duração
- **Logs** — Streaming de logs em tempo real com código de cores
- **Memory** — Navegue por SOUL.md, MEMORY.md, AGENTS.md, notas diárias
- **Transcripts** — Interface tipo balões de conversa para ler o histórico das sessões
- **Alerts** — Limites de orçamento, gatilhos de taxa de erro, deteção de agente offline; encaminha para Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloqueia eliminações destrutivas, force pushes, mutações de BD, sudo, instalações de pacotes, chamadas de rede atrás de uma aprovação com um clique

## Capturas de Ecrã

### 🧠 Brain — Fluxo de eventos do agente em tempo real
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens e resumo de sessões
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de chamadas de ferramentas em tempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Detalhamento de custos por modelo e sessão
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Navegador de ficheiros do espaço de trabalho
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de segurança e registo de auditoria
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limites de orçamento, gatilhos de taxa de erro, webhooks para Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloqueia chamadas de ferramentas arriscadas atrás de aprovação manual; regras de proteção baseadas em políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueio pré-execução para o Claude Code** — um único comando instala um
hook PreToolUse que pausa as chamadas de ferramentas correspondentes *antes* de serem executadas e aguarda
a sua decisão (um toque a partir do telemóvel com
[notificações push na cloud](https://app.clawmetry.com/push) ativadas):

```bash
clawmetry hooks install     # escreve ~/.claude/settings.json (idempotente)
clawmetry hooks status      # o que está ligado + quantas políticas estão ativas
clawmetry hooks uninstall   # remove apenas as entradas do ClawMetry
```

Uma negação bloqueia apenas essa chamada de ferramenta; o agente mantém a sua sessão e pode
tentar outra abordagem. Aprovar a partir do telemóvel salta o próprio
pedido de permissão do Claude Code (já respondeu). Ferramentas não correspondidas custam ~40ms e
passam para o fluxo de permissões normal do Claude Code. Também recebe um push no telemóvel quando o próprio Claude Code
está à sua espera (notificações `permission_prompt` /
`idle_prompt`).

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

A aplicação React v2 encontra-se em `frontend/` e é servida em `/v2` quando o
servidor Flask é iniciado com o v2 ativado.

Use dois terminais durante o desenvolvimento:

```bash
# Terminal 1: Servidor/API Flask em :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Servidor de desenvolvimento Vite em :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abra `http://localhost:5173/v2/`. O Vite faz proxy dos pedidos `/api` para
`http://localhost:8900`, para que a aplicação React consiga comunicar com o servidor Flask local
sem configuração extra de CORS.

Para gerar o bundle que é distribuído com o pacote Python:

```bash
cd frontend
npm run build
```

O bundle de produção é escrito em `clawmetry/static/v2/dist/`.

## Compatibilidade de Runtimes / Agentes

O ClawMetry observa muitos runtimes de agentes de IA, não apenas o OpenClaw. Cada runtime que não seja o OpenClaw inclui um adaptador de leitura dedicado que traduz o formato nativo das suas sessões para as formas unificadas do ClawMetry; o daemon ingere-os no mesmo armazenamento DuckDB + snapshot na cloud, etiquetados com o runtime, e o separador de replay de Sessão mostra um **seletor de runtime** quando existe mais do que um presente. Consulte [`docs/compatibility.md`](docs/compatibility.md) para a matriz completa + um guia para adicionar runtimes, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para a introdução à família OpenClaw.

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referência, detetado automaticamente |
| **PicoClaw** | Adaptador beta | JSONL simples `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcrições, modelo, chamadas de ferramentas. |
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
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Execuções de workflow, execuções de nós, prompts do AI Agent, modelo + tokens onde o n8n os regista. |

"Adaptador beta" significa que o ClawMetry inclui um leitor para o formato real em disco desse runtime, cada um construído + verificado numa instalação real, numa máquina real (ver `tests/fixtures/runtimes/<rt>/`). Os adaptadores são apenas de leitura; cada um é transparente sobre o que o respetivo runtime realmente armazena (por exemplo, o PicoClaw/NanoClaw/Cursor não escrevem o custo em tokens no disco). Quando vários runtimes são executados num único nó, o seletor de runtime restringe a vista de sessões a um deles para uma análise limpa e aprofundada.

## Acompanhe qualquer agente SDK — atribuição de custos fora do loop

Os runtimes acima escrevem todos as sessões em disco. O seu próprio **agente de produção** — aquele que construiu com o OpenAI Agents SDK, LangChain, o Vercel AI SDK, LlamaIndex, E2B, ou um simples loop `httpx` — não o faz. O interceptor de configuração zero do ClawMetry ainda assim captura as suas chamadas LLM (custo, tokens, latência, erros) fazendo monkey-patching a `httpx`/`requests`:

```python
import clawmetry.track            # ativa o interceptor
clawmetry.track.set_source("support-agent")   # nomeia este produto

# ...o seu agente executa normalmente; cada chamada LLM é agora acompanhada + atribuída.
```

`set_source()` (ou a variável de ambiente `CLAWMETRY_SOURCE=support-agent`) etiqueta cada chamada com uma **fonte nomeada**, pelo que cada produto que executar aparece como a sua própria linha de primeira classe, atribuível por custo, no cartão **🔌 Fontes fora do loop** do painel Overview — chamadas, fornecedores, latência, taxa de erro por agente. Sem fonte definida? As chamadas continuam a ser acompanhadas; o cartão apenas permanece oculto.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta é a mesma camada de dados que alimenta os adaptadores de runtime (DuckDB → snapshot na cloud), pelo que as fontes fora do loop sincronizam com o painel na cloud tal como tudo o resto, com encriptação de ponta a ponta.

## OpenTelemetry — neutro em relação ao fornecedor, envie os seus traces para qualquer lado

O ClawMetry fala **OpenTelemetry** em ambas as direções, usando as **convenções semânticas GenAI**, para que os traces do seu agente nunca fiquem presos a apenas uma ferramenta.

**Exporte** cada sessão — chamadas LLM, ferramentas, sub-agentes, tokens, custo — como spans OTLP/HTTP GenAI para qualquer coletor (Datadog, Grafana, Honeycomb, ou o seu próprio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Os cabeçalhos de autenticação e o intervalo de sondagem são variáveis de ambiente opcionais:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # cabeçalhos HTTP extra
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (padrão 60)
```

**Ingestão** — o recetor OTLP incorporado aceita traces e métricas de qualquer outra origem em `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` para ingestão via protobuf).

Obtém o painel ClawMetry de configuração zero, local em primeiro lugar, **e** os seus dados no backend que a sua equipa já utiliza; sem aprisionamento a um fornecedor, sem um segundo agente para instalar.

## Configuração

A maioria das pessoas não precisa de qualquer configuração. O ClawMetry deteta automaticamente o seu espaço de trabalho, logs, sessões e crons.

Se precisar mesmo de personalizar:

```bash
clawmetry --port 9000              # Porta personalizada (padrão: 8900)
clawmetry --host 127.0.0.1         # Vincular apenas a localhost
clawmetry --workspace ~/mybot      # Caminho de espaço de trabalho personalizado
clawmetry --name "Alice"           # O seu nome na visualização Flow
```

Todas as opções: `clawmetry --help`

## Canais Suportados

O ClawMetry mostra atividade ao vivo para todos os canais do OpenClaw que tiver configurados. Apenas os canais que estão realmente configurados no seu `openclaw.json` aparecem no diagrama Flow; os não configurados ficam automaticamente ocultos.

Clique em qualquer nó de canal no Flow para ver uma vista de balões de conversa ao vivo com contagens de mensagens recebidas/enviadas.

| Canal | Estado | Popup ao Vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensagens, estatísticas, atualização a cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lê diretamente `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Deteção de guild + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Deteção de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessões da interface web incorporada |
| 📡 **IRC** | ✅ Completo | ✅ | Interface de balões estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST do BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhooks da Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin de bot do Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipa autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, suporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs NIP-04 descentralizadas |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via ligação IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Subscrição de eventos WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Deteção automática:** O ClawMetry lê o seu `~/.openclaw/openclaw.json` e apenas renderiza os canais que realmente configurou. Não é necessária qualquer configuração manual.

## Implantação com Docker

Quer executar o ClawMetry num contentor? Sem problema! 🐳

**Início rápido com Docker:**

```bash
# Construir a imagem
docker build -t clawmetry .

# Executar com configurações padrão
docker run -p 8900:8900 clawmetry

# Ou monte a pasta de dados do seu agente (mostrado: o ~/.openclaw do OpenClaw)
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

> **Nota:** Ao executar no Docker, monte as pastas de dados + logs do seu agente (por exemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que o ClawMetry consiga detetar automaticamente a sua configuração.

## Requisitos

- Python 3.8+
- Flask (instalado automaticamente via pip)
- Um runtime de agente de IA na mesma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, ou n8n (ou volumes montados para Docker)
- Linux ou macOS

## Suporte para NemoClaw / OpenShell

O ClawMetry deteta automaticamente o [NemoClaw](https://github.com/NVIDIA/NemoClaw), o wrapper de segurança empresarial da NVIDIA para o OpenClaw que executa agentes dentro de contentores OpenShell isolados (sandboxed).

Na maioria dos casos não é necessária configuração extra. O daemon de sincronização descobre automaticamente ficheiros de sessão, quer estejam em `~/.openclaw/` no anfitrião, quer dentro de um contentor OpenShell.

### Como funciona

O ClawMetry deteta o NemoClaw de duas formas:

1. **Deteção de binário** — verifica a existência do CLI `nemoclaw` e executa `nemoclaw status` para obter informação da sandbox
2. **Deteção de contentor** — analisa os contentores Docker em execução à procura de imagens `openshell`, `nemoclaw`, ou `ghcr.io/nvidia/`, e depois lê as sessões via montagens de volume ou `docker cp`

Os ficheiros de sessão sincronizados a partir de contentores NemoClaw são etiquetados com `runtime=nemoclaw` e metadados `container_id` no painel na cloud, para que os consiga distinguir de sessões OpenClaw padrão à primeira vista.

### Configuração recomendada: daemon de sincronização no ANFITRIÃO

Para a melhor experiência, execute o daemon de sincronização do ClawMetry na **máquina anfitriã** (não dentro da sandbox). Isto evita restrições de política de rede do NemoClaw.

```bash
# No anfitrião (fora da sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

O daemon de sincronização irá encontrar automaticamente as sessões dentro de quaisquer contentores OpenShell em execução.

### Opcional: nome de sandbox explícito

Se a deteção automática não funcionar, aponte o ClawMetry para a sandbox correta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Execução dentro da sandbox (avançado)

Se precisar de executar o daemon de sincronização **dentro** da sandbox OpenShell, adicione esta regra de saída (egress) à sua política de rede do NemoClaw para que consiga alcançar a API de ingestão do ClawMetry:

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

O daemon de sincronização apenas faz chamadas HTTPS de saída para `ingest.clawmetry.com`. Não é necessária nenhuma porta de entrada.

---

## Implantação na Cloud

Consulte o **[Guia de Testes na Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneis SSH, proxy reverso e Docker.

## Testes

Este projeto é testado com BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

O ClawMetry envia sinais anónimos de ciclo de vida da instalação para
`https://app.clawmetry.com/api/install`: um sinal `install` na primeira
vez que executa o CLI `clawmetry` numa nova máquina, um sinal `update`
na primeira execução após atualizar para uma nova versão, e um sinal
`onboarded` quando conclui a escolha de integração no painel. Usamos isto
para contar instalações reais (os números brutos de downloads do PyPI são ~98% mirrors, CI,
e novos downloads de atualização automática) e para saber quais as frameworks de agentes e
versões que estão realmente a ser usadas.

**No máximo um POST por evento de ciclo de vida por versão**, contendo:

| Campo | Exemplo | Motivo |
|---|---|---|
| `install_id` | UUID aleatório guardado em `~/.clawmetry/install_id` | evitar duplicados; anónimo até ligar explicitamente a sincronização Cloud (o heartbeat autenticado do daemon passa a transportá-lo, ligando esta instalação à sua conta) |
| `event` | `install` / `update` / `onboarded` | instalação nova vs atualização de uma existente |
| `version` | `0.12.167` | quais as versões que estão em uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de suporte de plataforma |
| `python` | `3.11.15` | matriz de suporte de versões Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | com que agentes nos devemos integrar a seguir |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalações humanas de ruído de CI |

**O que NÃO enviamos**: IP (a cloud deriva o código do país do lado do
servidor a partir do pedido, e depois descarta o IP), nome do anfitrião, nome de utilizador, caminho do
espaço de trabalho, conteúdo de ficheiros, a sua api_key, o seu email, nada que seja PII ou
específico do espaço de trabalho. O payload transmitido é auditável em
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desativar** (qualquer uma destas opções desativa-o permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por sessão de shell
export DO_NOT_TRACK=1                          # padrão W3C entre ferramentas
touch ~/.clawmetry/notelemetry                 # marcador de ficheiro persistente
```

Uma falha de rede aqui nunca bloqueia a execução do `clawmetry`; o
sinal é fire-and-forget numa thread de daemon com um tempo limite de 3 s.

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
