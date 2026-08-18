<!-- i18n-src:c422fb7dd0da -->
> Español (LatAm) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Mira pensar a tu agente.** Observabilidad en tiempo real para **22 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex y 18 más. Un solo dashboard para toda tu flota de agentes.

> 🌐 **Lee esto en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900** y listo.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona con 22 runtimes de agentes

ClawMetry comenzó como observabilidad para OpenClaw, y ahora mide **toda tu flota de agentes** en un solo dashboard, detectando automáticamente cada runtime en tu máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw y NemoClaw son gratuitos en la app de código abierto; los demás runtimes se habilitan con ClawMetry Cloud o una licencia Pro autoalojada. Cambia de runtime desde el encabezado y cada pestaña (costo, tokens, herramientas, trazas) se reajusta a ese runtime. Consulta **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para ver la división exacta entre gratuito y de pago, la matriz de niveles, la forma de `/api/entitlement` y el CLI `clawmetry license`.

## Qué obtienes

- **Flow** — Diagrama animado en vivo que muestra los mensajes fluyendo por los canales, el cerebro, las herramientas y de vuelta
- **Overview** — Chequeos de salud, mapa de calor de actividad, conteo de sesiones, info del modelo
- **Usage** — Seguimiento de tokens y costos con desgloses diarios/semanales/mensuales
- **Sessions** — Sesiones de agente activas con modelo, tokens, última actividad
- **Crons** — Trabajos programados con estado, próxima ejecución, duración
- **Logs** — Streaming de logs en tiempo real con código de colores
- **Memory** — Explora SOUL.md, MEMORY.md, AGENTS.md, notas diarias
- **Transcripts** — Interfaz de burbujas de chat para leer los historiales de sesión
- **Alerts** — Topes de presupuesto, disparadores de tasa de error, detección de agente fuera de línea; enruta a Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloquea eliminaciones destructivas, force pushes, mutaciones de BD, sudo, instalaciones de paquetes y llamadas de red detrás de una aprobación con un solo clic

## Capturas de pantalla

### 🧠 Brain — Flujo de eventos del agente en vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens y resumen de sesión
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de llamadas a herramientas en tiempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desglose de costos por modelo y sesión
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de archivos del workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de seguridad y registro de auditoría
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Topes de presupuesto, disparadores de tasa de error, webhooks a Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloquea llamadas a herramientas riesgosas detrás de una aprobación manual; reglas de protección respaldadas por políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueo previo a la ejecución para Claude Code** — un solo comando instala un
hook PreToolUse que pausa las llamadas a herramientas coincidentes *antes* de que se ejecuten y espera
tu decisión (un toque desde tu teléfono con
[notificaciones push en la nube](https://app.clawmetry.com/push) habilitadas):

```bash
clawmetry hooks install     # escribe ~/.claude/settings.json (idempotente)
clawmetry hooks status      # qué está conectado y cuántas políticas están activas
clawmetry hooks uninstall   # elimina solo las entradas de ClawMetry
```

Un rechazo bloquea solo esa llamada a herramienta; el agente conserva su sesión y puede
intentar otro enfoque. Aprobar desde tu teléfono evita el propio
prompt de permisos de Claude Code (ya respondiste). Las herramientas sin coincidencia cuestan ~40ms y
caen de vuelta al flujo de permisos normal de Claude Code. También recibes una notificación push en el teléfono cuando el propio Claude Code
está esperando por ti (notificaciones `permission_prompt` / `idle_prompt`).

## Instalación

**Un solo comando (recomendado):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Desde el código fuente:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Desarrollo del frontend v2

La app React v2 vive en `frontend/` y se sirve en `/v2` cuando el servidor
Flask se inicia con v2 habilitado.

Usa dos terminales mientras desarrollas:

```bash
# Terminal 1: servidor Flask API en :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: servidor de desarrollo Vite en :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abre `http://localhost:5173/v2/`. Vite redirige las solicitudes `/api` a
`http://localhost:8900`, de modo que la app React pueda hablar con el servidor Flask local
sin configuración adicional de CORS.

Para construir el bundle que se distribuye con el paquete de Python:

```bash
cd frontend
npm run build
```

El bundle de producción se escribe en `clawmetry/static/v2/dist/`.

## Compatibilidad de runtimes / agentes

ClawMetry observa muchos runtimes de agentes de IA, no solo OpenClaw. Cada runtime distinto de OpenClaw incluye un adaptador de lectura dedicado que traduce el formato nativo de sus sesiones a las formas unificadas de ClawMetry; el daemon las ingiere en el mismo almacén DuckDB + snapshot en la nube, etiquetadas con el runtime, y la pestaña de reproducción de sesión muestra un **selector de runtime** cuando hay más de uno presente. Consulta [`docs/compatibility.md`](docs/compatibility.md) para ver la matriz completa y una guía para agregar runtimes, y [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para la introducción a la familia OpenClaw.

¿Usas la herramienta de seguridad de agentes [numbat de Perplexity](https://github.com/perplexityai/numbat)? ClawMetry ingiere sus hallazgos y decisiones de aplicación de políticas sin configuración adicional; consulta [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referencia, detectado automáticamente |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripciones, modelo, llamadas a herramientas. |
| **NanoClaw** | Adaptador beta | SQLite por sesión (`data/v2-sessions`). Transcripciones + conteo de mensajes. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcripciones, modelo, tokens/costo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripciones, modelo, llamadas a herramientas + razonamiento, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcripciones, modelo, llamadas a herramientas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcripciones de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por proyecto. Transcripciones, modelo, conteo de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcripciones, modelo, llamadas a herramientas, totales de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcripciones, modelo, llamadas a herramientas, tokens + costo. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcripciones, modelo, llamadas a herramientas, uso de tokens. |
| **Pi** | Adaptador beta | JSONL `~/.pi/agent/sessions`. Transcripciones, modelo, llamadas a herramientas, tokens + costo. |
| **Deep Agents** | Adaptador beta | SQLite `~/.deepagents/.state/sessions.db`. Transcripciones, modelo, llamadas a herramientas, tokens + costo. |
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Ejecuciones de workflows, ejecuciones de nodos, prompts del AI Agent, modelo + tokens cuando n8n los registra. |
| **Antigravity** | Adaptador beta | Brain JSONL en `~/.gemini/<flavor>/brain/`. Conversaciones, pasos de herramientas, razonamiento, desglose de tokens de Gemini por generación + costo, consumo de generación en segundo plano. |
| **GitHub Copilot** | Adaptador beta | `events.jsonl` de Copilot CLI en `~/.copilot/session-state/` + el libro de uso por llamada `session-store.db`. Conversaciones, llamadas a herramientas, enrutamiento de modelo, desglose de tokens con caché, costo en créditos de IA facturado por el proveedor. |
| **Grok** | Adaptador beta | xAI Grok Build CLI (binario en Rust en `~/.grok/bin/grok`): registro global de eventos `~/.grok/logs/unified.jsonl` + por sesión `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Conversaciones, desglose de tokens por turno, enrutamiento de modelo, y el payload de repositorio saliente del CLI almacenado en `~/.grok/upload_queue/` para que veas qué salió de tu máquina. |

"Adaptador beta" significa que ClawMetry incluye un lector para el formato real en disco de ese runtime, cada uno construido y verificado contra una instalación real en una máquina real (ver `tests/fixtures/runtimes/<rt>/`). Los adaptadores son de solo lectura; cada uno es honesto sobre lo que su runtime realmente almacena (p. ej., PicoClaw/NanoClaw/Cursor no escriben el costo de tokens en disco). Cuando varios runtimes se ejecutan en un mismo nodo, el selector de runtime acota la vista de sesiones a uno solo para un análisis limpio y detallado.

## Rastrea cualquier agente de SDK: atribución de costos fuera del loop

Los runtimes anteriores escriben sesiones en disco. Tu propio **agente de producción**, el que construiste con el OpenAI Agents SDK, LangChain, el Vercel AI SDK, LlamaIndex, E2B, o un simple loop con `httpx`, no lo hace. El interceptor sin configuración de ClawMetry igual captura sus llamadas a LLM (costo, tokens, latencia, errores) mediante monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # activa el interceptor
clawmetry.track.set_source("support-agent")   # nombra este producto

# ...tu agente se ejecuta con normalidad; cada llamada a LLM ahora se rastrea + atribuye.
```

`set_source()` (o la variable de entorno `CLAWMETRY_SOURCE=support-agent`) etiqueta cada llamada con una **fuente nombrada**, de modo que cada producto que ejecutes aparece como su propia línea de primera clase, atribuible por costo, en la tarjeta **🔌 Out-loop sources** del Overview del dashboard: llamadas, proveedores, latencia, tasa de error por agente. ¿No hay fuente configurada? Las llamadas se siguen rastreando; la tarjeta simplemente permanece oculta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta es la misma capa de datos que alimentan los adaptadores de runtime (DuckDB → snapshot en la nube), así que las fuentes fuera del loop se sincronizan con el dashboard en la nube igual que todo lo demás, con cifrado E2E.

## OpenTelemetry: neutral respecto al proveedor, envía tus trazas a donde quieras

ClawMetry habla **OpenTelemetry** en ambas direcciones, usando las **convenciones semánticas de GenAI**, de modo que las trazas de tu agente nunca quedan atadas a una sola herramienta.

**Exporta** cada sesión (llamadas a LLM, herramientas, subagentes, tokens, costo) como spans OTLP/HTTP de GenAI a cualquier colector (Datadog, Grafana, Honeycomb, o tu propio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Los encabezados de autenticación y el intervalo de sondeo son variables de entorno opcionales:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # encabezados HTTP adicionales
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (por defecto 60)
```

**Ingesta**: el receptor OTLP incluido acepta trazas, logs y métricas de cualquier otra fuente en `/v1/traces`, `/v1/logs`, y `/v1/metrics`. Apunta cualquier app instrumentada con OpenTelemetry hacia él:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Las trazas y logs OTLP/JSON funcionan con un simple `pip install clawmetry`, sin extras. La ingesta de Protobuf (y las métricas OTLP/JSON) requiere `pip install clawmetry[otel]`. Una app que configura su propio `service.name` aparece como su propio agente en el selector de runtime, con su costo y tokens.

Obtienes el dashboard de ClawMetry sin configuración y local-first, **y** tus datos en el backend que ya usa tu equipo, sin lock-in, sin necesidad de instalar un segundo agente.

## Configuración

La mayoría de la gente no necesita ninguna configuración. ClawMetry detecta automáticamente tu workspace, logs, sesiones y crons.

Si necesitas personalizar:

```bash
clawmetry --port 9000              # Puerto personalizado (por defecto: 8900)
clawmetry --host 127.0.0.1         # Vincular solo a localhost
clawmetry --workspace ~/mybot      # Ruta de workspace personalizada
clawmetry --name "Alice"           # Tu nombre en la visualización de Flow
```

Todas las opciones: `clawmetry --help`

## Canales compatibles

ClawMetry muestra actividad en vivo para cada canal de OpenClaw que tengas configurado. Solo los canales que estén realmente configurados en tu `openclaw.json` aparecen en el diagrama de Flow; los no configurados se ocultan automáticamente.

Haz clic en cualquier nodo de canal en Flow para ver una vista de burbujas de chat en vivo con conteos de mensajes entrantes/salientes.

| Canal | Estado | Popup en vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensajes, estadísticas, actualización cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lee `~/Library/Messages/chat.db` directamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Vía WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Vía signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detección de gremio + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detección de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sesiones de la interfaz web integrada |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaz de burbujas estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage vía la API REST de BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Vía webhooks de la API de Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Vía el plugin de bot de Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipo autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, con soporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de mensajería de LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat vía conexión IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Suscripción a eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API de Zalo Bot |

> **Detección automática:** ClawMetry lee tu `~/.openclaw/openclaw.json` y solo renderiza los canales que realmente hayas configurado. No se requiere configuración manual.

## Despliegue con Docker

¿Quieres ejecutar ClawMetry en un contenedor? ¡No hay problema! 🐳

**Inicio rápido con Docker:**

```bash
# Construir la imagen
docker build -t clawmetry .

# Ejecutar con la configuración predeterminada
docker run -p 8900:8900 clawmetry

# O montar el directorio de datos de tu agente (se muestra: el ~/.openclaw de OpenClaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Ejemplo de Docker Compose:**

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

> **Nota:** Al ejecutar en Docker, monta los directorios de datos + logs de tu agente (p. ej., `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry pueda detectar automáticamente tu configuración.

## Requisitos

- Python 3.8+
- Flask (se instala automáticamente vía pip)
- Un runtime de agente de IA en la misma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, o QM (o volúmenes montados para Docker)
- Linux o macOS

## Soporte para NemoClaw / OpenShell

ClawMetry detecta automáticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), el envoltorio de seguridad empresarial de NVIDIA para OpenClaw que ejecuta agentes dentro de contenedores OpenShell en sandbox.

En la mayoría de los casos no se necesita configuración adicional. El daemon de sincronización descubre automáticamente los archivos de sesión, ya sea que estén en `~/.openclaw/` en el host o dentro de un contenedor OpenShell.

### Cómo funciona

ClawMetry detecta NemoClaw de dos maneras:

1. **Detección por binario**: verifica la existencia del CLI `nemoclaw` y ejecuta `nemoclaw status` para obtener la info del sandbox
2. **Detección por contenedor**: escanea los contenedores Docker en ejecución en busca de imágenes `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, y luego lee las sesiones vía montajes de volumen o `docker cp`

Los archivos de sesión sincronizados desde contenedores NemoClaw se etiquetan con `runtime=nemoclaw` y metadatos de `container_id` en el dashboard en la nube, para que puedas distinguirlos de las sesiones estándar de OpenClaw de un vistazo.

### Configuración recomendada: daemon de sincronización en el HOST

Para la mejor experiencia, ejecuta el daemon de sincronización de ClawMetry en la **máquina host** (no dentro del sandbox). Esto evita las restricciones de política de red de NemoClaw.

```bash
# En el host (fuera del sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

El daemon de sincronización encontrará automáticamente las sesiones dentro de cualquier contenedor OpenShell en ejecución.

### Opcional: nombre explícito del sandbox

Si la detección automática no funciona, apunta ClawMetry al sandbox correcto:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Ejecución dentro del sandbox (avanzado)

Si debes ejecutar el daemon de sincronización **dentro** del sandbox de OpenShell, agrega esta regla de salida a tu política de red de NemoClaw para que pueda llegar a la API de ingesta de ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Aplícala con:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Puertos y endpoints

| Endpoint | Puerto | Protocolo | Requerido |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sí (daemon de sincronización → nube) |
| `localhost:8900` | 8900 | HTTP | Sí (interfaz del dashboard local) |
| Socket de Docker (`/var/run/docker.sock`) | — | Socket Unix | Para el descubrimiento de sesiones en contenedores |

El daemon de sincronización solo realiza llamadas HTTPS salientes a `ingest.clawmetry.com`. No se requieren puertos de entrada.

---

## Despliegue en la nube

Consulta la **[Guía de pruebas en la nube](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneles SSH, proxy inverso y Docker.

## Pruebas

Este proyecto se prueba con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetría

ClawMetry envía pings anónimos del ciclo de vida de la instalación a
`https://app.clawmetry.com/api/install`: un ping de `install` la primera
vez que ejecutas el CLI `clawmetry` en una máquina nueva, un ping de `update`
la primera ejecución tras actualizar a una versión nueva, y un ping de `onboarded`
cuando completas la elección de onboarding dentro del dashboard. Usamos esto
para contar instalaciones reales (las cifras crudas de descargas de PyPI son ~98% mirrors, CI,
y redescargas de auto-actualización) y para saber qué frameworks y versiones de agentes
están realmente en uso.

**Como máximo un POST por evento de ciclo de vida por versión**, que contiene:

| Campo | Ejemplo | Por qué |
|---|---|---|
| `install_id` | UUID aleatorio almacenado en `~/.clawmetry/install_id` | deduplicación; anónimo hasta que conectas explícitamente la sincronización en la nube (el heartbeat autenticado del daemon entonces lo transporta, vinculando esta instalación a tu cuenta) |
| `event` | `install` / `update` / `onboarded` | instalación nueva vs. actualización de una existente |
| `version` | `0.12.167` | qué versiones están en uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de soporte de plataforma |
| `python` | `3.11.15` | matriz de soporte de versiones de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con qué agentes deberíamos integrarnos a continuación |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalaciones humanas del ruido de CI |

**Qué NO enviamos**: IP (la nube deriva el código de país del lado del servidor
a partir de la solicitud, y luego descarta la IP), nombre de host, nombre de usuario, ruta del
workspace, contenido de archivos, tu api_key, tu correo electrónico, nada de PII ni
específico del workspace. El payload en tránsito es auditable en
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Cómo optar por no participar** (cualquiera de estas la deshabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por shell
export DO_NOT_TRACK=1                          # estándar W3C entre herramientas
touch ~/.clawmetry/notelemetry                 # marcador de archivo persistente
```

Un fallo de red aquí nunca bloquea la ejecución de `clawmetry`; el
ping es fire-and-forget en un hilo del daemon con un timeout de 3 s.

## Historial de estrellas

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licencia

MIT

---

<p align="center">
  <strong>🦞 Mira pensar a tu agente</strong><br>
  <sub>Creado por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte del ecosistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
