<!-- i18n-src:02b789586c7d -->
> Español (LatAm) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Observa cómo piensa tu agente.** Observabilidad en tiempo real para **14 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex y 10 más. Un solo dashboard para toda tu flota de agentes.

> 🌐 **Lee esto en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un solo comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900** y listo.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona con 14 runtimes de agentes

ClawMetry comenzó como observabilidad para OpenClaw, y ahora mide **toda tu flota de agentes** en un solo dashboard, detectando automáticamente cada runtime en tu máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw y NemoClaw son gratuitos en la app de código abierto; los demás runtimes se activan con ClawMetry Cloud o una licencia Pro autoalojada. Cambia de runtime desde el encabezado y cada pestaña, costo, tokens, herramientas, trazas, se reajusta a ese runtime. Consulta **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para conocer la división exacta entre gratuito y de pago, la matriz de niveles, la forma de `/api/entitlement`, y el CLI `clawmetry license`.

## Qué obtienes

- **Flow** — Diagrama animado en vivo que muestra los mensajes fluyendo por los canales, el cerebro, las herramientas y de vuelta
- **Overview** — Chequeos de salud, mapa de calor de actividad, conteo de sesiones, información del modelo
- **Usage** — Seguimiento de tokens y costos con desgloses diarios/semanales/mensuales
- **Sessions** — Sesiones de agente activas con modelo, tokens, última actividad
- **Crons** — Tareas programadas con estado, próxima ejecución, duración
- **Logs** — Streaming de logs en vivo con colores
- **Memory** — Explora SOUL.md, MEMORY.md, AGENTS.md, notas diarias
- **Transcripts** — Interfaz de burbujas de chat para leer historiales de sesiones
- **Alerts** — Límites de presupuesto, disparadores de tasa de error, detección de agente desconectado; se enruta a Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Bloquea eliminaciones destructivas, force pushes, mutaciones de base de datos, sudo, instalaciones de paquetes, llamadas de red detrás de una aprobación con un solo clic

## Capturas de pantalla

### 🧠 Brain — Flujo de eventos del agente en vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Resumen de uso de tokens y sesiones
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de llamadas a herramientas en tiempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desglose de costos por modelo y sesión
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de archivos del workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de seguridad y registro de auditoría
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Límites de presupuesto, disparadores de tasa de error, webhooks a Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloquea llamadas a herramientas riesgosas detrás de una aprobación manual; reglas de protección respaldadas por políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueo previo a la ejecución para Claude Code** — un comando instala un
hook PreToolUse que pausa las llamadas a herramientas que coincidan *antes* de que se ejecuten y espera
tu decisión (un toque desde tu teléfono con
[notificaciones push en la nube](https://app.clawmetry.com/push) habilitadas):

```bash
clawmetry hooks install     # escribe ~/.claude/settings.json (idempotente)
clawmetry hooks status      # qué está conectado + cuántas políticas están activas
clawmetry hooks uninstall   # elimina solo las entradas de ClawMetry
```

Una denegación bloquea solo esa llamada a herramienta; el agente conserva su sesión y puede
intentar otro enfoque. Aprobar desde tu teléfono omite el propio
prompt de permisos de Claude Code (ya respondiste). Las herramientas sin coincidencia cuestan ~40ms y
caen al flujo normal de permisos de Claude Code. También recibes un push en tu teléfono cuando Claude Code está
esperando tu respuesta (notificaciones `permission_prompt` /
`idle_prompt`).

## Instalación

**Comando único (recomendado):**
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

Usa dos terminales durante el desarrollo:

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
`http://localhost:8900`, así la app React puede comunicarse con el servidor Flask local
sin configuración adicional de CORS.

Para compilar el bundle que se distribuye con el paquete de Python:

```bash
cd frontend
npm run build
```

El bundle de producción se escribe en `clawmetry/static/v2/dist/`.

## Compatibilidad de runtimes / agentes

ClawMetry observa muchos runtimes de agentes de IA, no solo OpenClaw. Cada runtime que no sea OpenClaw incluye un adaptador de lectura dedicado que traduce su formato nativo de sesión a las estructuras unificadas de ClawMetry; el daemon las ingiere en el mismo almacén DuckDB + snapshot en la nube, etiquetadas con el runtime, y la pestaña de repetición de sesiones muestra un **selector de runtime** cuando hay más de uno presente. Consulta [`docs/compatibility.md`](docs/compatibility.md) para ver la matriz completa + una guía para agregar runtimes, y [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para la introducción a la familia OpenClaw.

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referencia, detectado automáticamente |
| **PicoClaw** | Adaptador beta | JSONL plano de `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripciones, modelo, llamadas a herramientas. |
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
| **n8n** | Adaptador beta | SQLite `~/.n8n/database.sqlite`. Ejecuciones de flujos de trabajo, ejecuciones de nodos, prompts de AI Agent, modelo + tokens cuando n8n los registra. |
| **Antigravity** | Adaptador beta | JSONL del cerebro bajo `~/.gemini/<flavor>/brain/`. Conversaciones, pasos de herramientas, razonamiento, desglose de tokens de Gemini por generación + costo, consumo de generación en segundo plano. |

"Adaptador beta" significa que ClawMetry distribuye un lector para el formato real en disco de ese runtime, cada uno construido y verificado contra una instalación real en una máquina real (ver `tests/fixtures/runtimes/<rt>/`). Los adaptadores son de solo lectura; cada uno es honesto sobre lo que su runtime realmente almacena (por ejemplo, PicoClaw/NanoClaw/Cursor no escriben el costo de tokens en disco). Cuando corren varios runtimes en un mismo nodo, el selector de runtime acota la vista de sesiones a uno solo para un análisis limpio y detallado.

## Rastrea cualquier agente de SDK — atribución de costos fuera del loop

Los runtimes anteriores escriben todos sus sesiones en disco. Tu propio **agente de producción** (el que construiste con el OpenAI Agents SDK, LangChain, el Vercel AI SDK, LlamaIndex, E2B, o un simple loop de `httpx`) no lo hace. El interceptor sin configuración de ClawMetry igual captura sus llamadas a LLM (costo, tokens, latencia, errores) mediante monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # activa el interceptor
clawmetry.track.set_source("support-agent")   # nombra este producto

# ...tu agente corre con normalidad; cada llamada a LLM ahora se rastrea + atribuye.
```

`set_source()` (o la variable de entorno `CLAWMETRY_SOURCE=support-agent`) etiqueta cada llamada con una **fuente nombrada**, así cada producto que ejecutes aparece como su propia línea de primera clase y con costo atribuible en la tarjeta **🔌 Fuentes fuera del loop** del dashboard en Overview: llamadas, proveedores, latencia, tasa de error por agente. ¿No configuraste una fuente? Las llamadas se siguen rastreando; la tarjeta simplemente permanece oculta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta es la misma capa de datos que alimentan los adaptadores de runtime (DuckDB → snapshot en la nube), así que las fuentes fuera del loop se sincronizan con el dashboard en la nube igual que todo lo demás, cifradas de extremo a extremo.

## OpenTelemetry — neutral respecto al proveedor, envía tus trazas a donde quieras

ClawMetry habla **OpenTelemetry** en ambas direcciones, usando las **convenciones semánticas GenAI**, así que las trazas de tu agente nunca quedan atadas a una sola herramienta.

**Exporta** cada sesión (llamadas a LLM, herramientas, subagentes, tokens, costo) como spans GenAI de OTLP/HTTP hacia cualquier colector (Datadog, Grafana, Honeycomb, o tu propio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalentemente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Los encabezados de autenticación y el intervalo de sondeo son variables de entorno opcionales:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # encabezados HTTP adicionales
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundos (por defecto 60)
```

**Ingesta** — el receptor OTLP integrado acepta trazas y métricas desde cualquier otra fuente en `/v1/traces` y `/v1/metrics` (`pip install clawmetry[otel]` para la ingesta de protobuf).

Obtienes el dashboard de ClawMetry sin configuración y local-first, **y** tus datos en cualquier backend que tu equipo ya use, sin bloqueo de proveedor, sin un segundo agente que instalar.

## Configuración

La mayoría de las personas no necesita ninguna configuración. ClawMetry detecta automáticamente tu workspace, logs, sesiones y crons.

Si necesitas personalizar:

```bash
clawmetry --port 9000              # Puerto personalizado (por defecto: 8900)
clawmetry --host 127.0.0.1         # Vincular solo a localhost
clawmetry --workspace ~/mybot      # Ruta de workspace personalizada
clawmetry --name "Alice"           # Tu nombre en la visualización de Flow
```

Todas las opciones: `clawmetry --help`

## Canales compatibles

ClawMetry muestra actividad en vivo para cada canal de OpenClaw que tengas configurado. Solo los canales que están realmente configurados en tu `openclaw.json` aparecen en el diagrama de Flow; los que no están configurados se ocultan automáticamente.

Haz clic en cualquier nodo de canal en el Flow para ver una vista de burbujas de chat en vivo con conteos de mensajes entrantes/salientes.

| Canal | Estado | Popup en vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensajes, estadísticas, actualización cada 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lee `~/Library/Messages/chat.db` directamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Vía WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Vía signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detección de guild + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detección de workspace + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sesiones de la interfaz web integrada |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaz de burbujas estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage vía la API REST de BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Vía webhooks de Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Vía plugin de bot de Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipo autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, con soporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | Mensajes directos descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat vía conexión IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Suscripción a eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detección automática:** ClawMetry lee tu `~/.openclaw/openclaw.json` y solo renderiza los canales que realmente has configurado. No se requiere configuración manual.

## Despliegue con Docker

¿Quieres correr ClawMetry en un contenedor? ¡Sin problema! 🐳

**Inicio rápido con Docker:**

```bash
# Construir la imagen
docker build -t clawmetry .

# Ejecutar con la configuración por defecto
docker run -p 8900:8900 clawmetry

# O monta el directorio de datos de tu agente (se muestra: ~/.openclaw de OpenClaw)
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

> **Nota:** Al ejecutar en Docker, monta los directorios de datos + logs de tu agente (por ejemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry pueda detectar tu configuración automáticamente.

## Requisitos

- Python 3.8+
- Flask (instalado automáticamente vía pip)
- Un runtime de agente de IA en la misma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, o Antigravity (o volúmenes montados para Docker)
- Linux o macOS

## Soporte para NemoClaw / OpenShell

ClawMetry detecta automáticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), el wrapper de seguridad empresarial de NVIDIA para OpenClaw que ejecuta agentes dentro de contenedores OpenShell en sandbox.

No se necesita configuración adicional en la mayoría de los casos. El daemon de sincronización descubre automáticamente los archivos de sesión, ya sea que vivan en `~/.openclaw/` en el host o dentro de un contenedor OpenShell.

### Cómo funciona

ClawMetry detecta NemoClaw de dos formas:

1. **Detección de binario** — verifica el CLI `nemoclaw` y ejecuta `nemoclaw status` para obtener información del sandbox
2. **Detección de contenedor** — escanea los contenedores Docker en ejecución en busca de imágenes `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, y luego lee las sesiones vía volúmenes montados o `docker cp`

Los archivos de sesión sincronizados desde contenedores NemoClaw se etiquetan con `runtime=nemoclaw` y metadatos de `container_id` en el dashboard en la nube, así puedes distinguirlos de las sesiones estándar de OpenClaw de un vistazo.

### Configuración recomendada: daemon de sincronización en el HOST

Para la mejor experiencia, ejecuta el daemon de sincronización de ClawMetry en la **máquina host** (no dentro del sandbox). Esto evita las restricciones de la política de red de NemoClaw.

```bash
# En el host (fuera del sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

El daemon de sincronización encontrará automáticamente las sesiones dentro de cualquier contenedor OpenShell en ejecución.

### Opcional: nombre de sandbox explícito

Si la detección automática no funciona, apunta ClawMetry al sandbox correcto:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Ejecución dentro del sandbox (avanzado)

Si debes ejecutar el daemon de sincronización **dentro** del sandbox de OpenShell, agrega esta regla de salida a tu política de red de NemoClaw para que pueda alcanzar la API de ingesta de ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Aplica con:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Puertos y endpoints

| Endpoint | Puerto | Protocolo | Requerido |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sí (daemon de sincronización → nube) |
| `localhost:8900` | 8900 | HTTP | Sí (interfaz del dashboard local) |
| Socket de Docker (`/var/run/docker.sock`) | — | Socket Unix | Para descubrimiento de sesiones en contenedores |

El daemon de sincronización solo realiza llamadas HTTPS salientes a `ingest.clawmetry.com`. No se requieren puertos entrantes.

---

## Despliegue en la nube

Consulta la **[Guía de pruebas en la nube](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneles SSH, proxy inverso y Docker.

## Pruebas

Este proyecto se prueba con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetría

ClawMetry envía pings anónimos del ciclo de vida de instalación a
`https://app.clawmetry.com/api/install`: un ping `install` la primera
vez que ejecutas el CLI `clawmetry` en una máquina nueva, un ping `update`
en la primera ejecución después de actualizar a una versión nueva, y un ping
`onboarded` cuando completas la elección de onboarding en el dashboard. Usamos
esto para contar instalaciones reales (los números de descargas crudas de PyPI son ~98% mirrors, CI,
y redescargas de actualización automática) y para saber qué frameworks de agentes y
versiones están realmente en uso.

**Como máximo un POST por evento de ciclo de vida por versión**, que contiene:

| Campo | Ejemplo | Por qué |
|---|---|---|
| `install_id` | UUID aleatorio almacenado en `~/.clawmetry/install_id` | deduplicación; anónimo hasta que conectas explícitamente la sincronización de Cloud (el heartbeat autenticado del daemon lleva entonces este dato, vinculando esta instalación a tu cuenta) |
| `event` | `install` / `update` / `onboarded` | instalación nueva vs actualización de una existente |
| `version` | `0.12.167` | qué versiones están en uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de soporte de plataforma |
| `python` | `3.11.15` | matriz de soporte de versiones de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con qué agentes deberíamos integrarnos a continuación |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalaciones humanas del ruido de CI |

**Qué NO enviamos**: IP (la nube deriva el código de país del lado del servidor
a partir de la solicitud y luego descarta la IP), hostname, nombre de usuario, ruta del workspace,
contenido de archivos, tu api_key, tu email, nada que sea PII o
específico del workspace. La carga útil transmitida es auditable en
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desactivar** (cualquiera de estas opciones lo deshabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # por shell
export DO_NOT_TRACK=1                          # estándar W3C entre herramientas
touch ~/.clawmetry/notelemetry                 # marcador de archivo persistente
```

Un fallo de red aquí nunca bloquea la ejecución de `clawmetry`; el
ping se envía sin esperar respuesta (fire-and-forget) en un hilo del daemon con un timeout de 3 s.

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
  <strong>🦞 Observa cómo piensa tu agente</strong><br>
  <sub>Creado por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte del ecosistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
