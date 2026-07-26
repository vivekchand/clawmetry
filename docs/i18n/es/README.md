<!-- i18n-src:bab48eec552f -->
> Español translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Observa cómo piensa tu agente.** Observabilidad en tiempo real para **14 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex y 10 más. Un solo panel para toda tu flota de agentes.

> 🌐 **Léelo en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900** y listo.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona con 14 runtimes de agentes

ClawMetry comenzó como observabilidad para OpenClaw, y ahora mide **toda tu flota de agentes** en un solo panel, detectando automáticamente cada runtime en tu máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw y NemoClaw son gratuitos en la aplicación de código abierto; los demás runtimes se activan con ClawMetry Cloud o una licencia Pro autoalojada. Cambia de runtime desde el encabezado y cada pestaña (costo, tokens, herramientas, trazas) se reajusta a ese runtime. Consulta **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para ver la división exacta entre gratuito y de pago, la matriz de niveles, la forma de `/api/entitlement` y la CLI `clawmetry license`.

## Qué obtienes

- **Flow**: diagrama animado en vivo que muestra los mensajes fluyendo a través de canales, cerebro, herramientas y de vuelta
- **Overview**: verificaciones de estado, mapa de calor de actividad, conteo de sesiones, información del modelo
- **Usage**: seguimiento de tokens y costos con desgloses diarios/semanales/mensuales
- **Sessions**: sesiones activas de agentes con modelo, tokens, última actividad
- **Crons**: trabajos programados con estado, próxima ejecución, duración
- **Logs**: transmisión de registros en tiempo real con código de colores
- **Memory**: explora SOUL.md, MEMORY.md, AGENTS.md, notas diarias
- **Transcripts**: interfaz de burbujas de chat para leer historiales de sesiones
- **Alerts**: límites de presupuesto, disparadores de tasa de error, detección de agente desconectado; enruta a Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: bloquea eliminaciones destructivas, force pushes, mutaciones de base de datos, sudo, instalaciones de paquetes y llamadas de red detrás de una autorización de un clic

## Capturas de pantalla

### 🧠 Brain — Flujo de eventos del agente en vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Resumen de uso de tokens y sesiones
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de llamadas a herramientas en tiempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desglose de costos por modelo y sesión
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de archivos del espacio de trabajo
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de seguridad y registro de auditoría
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Límites de presupuesto, disparadores de tasa de error, webhooks a Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Bloquea llamadas a herramientas riesgosas detrás de una autorización manual; reglas de protección respaldadas por políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Bloqueo antes de la ejecución para Claude Code**: un comando instala un
hook PreToolUse que pausa las llamadas a herramientas coincidentes *antes* de que se ejecuten y espera
tu decisión (con un solo toque desde tu teléfono con
[notificaciones push en la nube](https://app.clawmetry.com/push) habilitadas):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Un rechazo bloquea solo esa llamada a la herramienta; el agente conserva su sesión y puede
intentar otro enfoque. Aprobar desde tu teléfono omite el propio aviso de
permiso de Claude Code (ya lo respondiste). Las herramientas no coincidentes cuestan ~40ms y
continúan hacia el flujo de permisos normal de Claude Code. También recibes una notificación push en el teléfono cuando el propio Claude Code
está esperando tu respuesta (notificaciones `permission_prompt` /
`idle_prompt`).

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

La aplicación React v2 vive en `frontend/` y se sirve en `/v2` cuando el
servidor Flask se inicia con v2 habilitado.

Usa dos terminales durante el desarrollo:

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

Abre `http://localhost:5173/v2/`. Vite redirige las solicitudes `/api` a
`http://localhost:8900`, para que la aplicación React pueda comunicarse con el servidor Flask local
sin necesidad de configuración CORS adicional.

Para compilar el paquete que se distribuye con el paquete de Python:

```bash
cd frontend
npm run build
```

El paquete de producción se escribe en `clawmetry/static/v2/dist/`.

## Compatibilidad de runtimes / agentes

ClawMetry observa muchos runtimes de agentes de IA, no solo OpenClaw. Cada runtime que no es OpenClaw incluye un adaptador de lectura dedicado que traduce el formato nativo de sus sesiones a las formas unificadas de ClawMetry; el daemon los ingiere en el mismo almacén DuckDB + instantánea en la nube, etiquetados con el runtime, y la pestaña de reproducción de sesiones muestra un **selector de runtime** cuando hay más de uno presente. Consulta [`docs/compatibility.md`](docs/compatibility.md) para ver la matriz completa y una guía para agregar runtimes, y [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para la introducción a la familia OpenClaw.

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

"Adaptador beta" significa que ClawMetry incluye un lector para el formato real en disco de ese runtime, cada uno construido y verificado contra una instalación real en una máquina real (consulta `tests/fixtures/runtimes/<rt>/`). Los adaptadores son de solo lectura; cada uno es transparente sobre lo que su runtime realmente almacena (por ejemplo, PicoClaw/NanoClaw/Cursor no escriben el costo de tokens en disco). Cuando se ejecutan varios runtimes en un nodo, el selector de runtime limita la vista de sesiones a uno para un análisis detallado y claro.

## Rastrea cualquier agente de SDK: atribución de costos fuera del loop

Los runtimes anteriores escriben sesiones en disco. Tu propio **agente de producción**, el que construiste con el SDK de Agentes de OpenAI, LangChain, el SDK de IA de Vercel, LlamaIndex, E2B o un simple bucle `httpx`, no lo hace. El interceptor de cero configuración de ClawMetry aún captura sus llamadas LLM (costo, tokens, latencia, errores) mediante monkey-patching de `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (o la variable de entorno `CLAWMETRY_SOURCE=support-agent`) etiqueta cada llamada con una **fuente nombrada**, de modo que cada producto que ejecutes aparezca como su propia línea, atribuible a costos, en la tarjeta **🔌 Fuentes fuera del loop** del Overview del panel: llamadas, proveedores, latencia, tasa de errores por agente. ¿No configuraste una fuente? Las llamadas se siguen rastreando; la tarjeta simplemente permanece oculta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta es la misma capa de datos que alimentan los adaptadores de runtime (DuckDB → instantánea en la nube), por lo que las fuentes fuera del loop se sincronizan con el panel en la nube igual que todo lo demás, con cifrado de extremo a extremo.

## OpenTelemetry: neutral respecto al proveedor, envía tus trazas a donde quieras

ClawMetry habla **OpenTelemetry** en ambas direcciones, usando las **convenciones semánticas de GenAI**, para que las trazas de tu agente nunca queden atadas a una sola herramienta.

**Exporta** cada sesión (llamadas LLM, herramientas, subagentes, tokens, costo) como trazas GenAI OTLP/HTTP a cualquier colector (Datadog, Grafana, Honeycomb o tu propio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Los encabezados de autenticación y el intervalo de sondeo son variables de entorno opcionales:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingesta**: el receptor OTLP incorporado acepta trazas y métricas de cualquier otra fuente en `/v1/traces` y `/v1/metrics` (`pip install clawmetry[otel]` para la ingesta de protobuf).

Obtienes el panel de ClawMetry con cero configuración y prioridad local, **y** tus datos en el backend que ya usa tu equipo, sin dependencia de proveedor, sin necesidad de instalar un segundo agente.

## Configuración

La mayoría de las personas no necesitan ninguna configuración. ClawMetry detecta automáticamente tu espacio de trabajo, registros, sesiones y crons.

Si necesitas personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas las opciones: `clawmetry --help`

## Canales compatibles

ClawMetry muestra actividad en vivo para cada canal de OpenClaw que tengas configurado. Solo los canales que están realmente configurados en tu `openclaw.json` aparecen en el diagrama Flow; los que no están configurados se ocultan automáticamente.

Haz clic en cualquier nodo de canal en Flow para ver una vista de burbujas de chat en vivo con conteos de mensajes entrantes/salientes.

| Canal | Estado | Ventana en vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensajes, estadísticas, actualización cada 10 s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lee `~/Library/Messages/chat.db` directamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Vía WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Vía signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detección de servidor + canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detección de espacio de trabajo + canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sesiones de la interfaz web incorporada |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaz de burbujas estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage vía la API REST de BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Vía webhooks de la API de Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Vía el complemento de bot de Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipo autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, con soporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de mensajería de LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat vía conexión IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Suscripción a eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API de bots de Zalo |

> **Detección automática:** ClawMetry lee tu `~/.openclaw/openclaw.json` y solo muestra los canales que realmente has configurado. No se requiere configuración manual.

## Despliegue con Docker

¿Quieres ejecutar ClawMetry en un contenedor? ¡No hay problema! 🐳

**Inicio rápido con Docker:**

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

> **Nota:** Al ejecutar en Docker, monta los directorios de datos y registros de tu agente (por ejemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry pueda detectar automáticamente tu configuración.

## Requisitos

- Python 3.8+
- Flask (se instala automáticamente vía pip)
- Un runtime de agente de IA en la misma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi o Deep Agents (o volúmenes montados para Docker)
- Linux o macOS

## Soporte para NemoClaw / OpenShell

ClawMetry detecta automáticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), el envoltorio de seguridad empresarial de NVIDIA para OpenClaw que ejecuta agentes dentro de contenedores OpenShell en sandbox.

En la mayoría de los casos no se necesita configuración adicional. El daemon de sincronización descubre automáticamente los archivos de sesión, ya sea que residan en `~/.openclaw/` en el host o dentro de un contenedor OpenShell.

### Cómo funciona

ClawMetry detecta NemoClaw de dos maneras:

1. **Detección de binario**: verifica la CLI `nemoclaw` y ejecuta `nemoclaw status` para obtener información del sandbox
2. **Detección de contenedor**: escanea los contenedores Docker en ejecución en busca de imágenes `openshell`, `nemoclaw` o `ghcr.io/nvidia/`, y luego lee las sesiones vía montajes de volumen o `docker cp`

Los archivos de sesión sincronizados desde contenedores NemoClaw se etiquetan con `runtime=nemoclaw` y metadatos `container_id` en el panel en la nube, para que puedas distinguirlos de las sesiones estándar de OpenClaw de un vistazo.

### Configuración recomendada: daemon de sincronización en el HOST

Para la mejor experiencia, ejecuta el daemon de sincronización de ClawMetry en la **máquina host** (no dentro del sandbox). Esto evita las restricciones de política de red de NemoClaw.

```bash
# On the host (outside the sandbox)
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

Si debes ejecutar el daemon de sincronización **dentro** del sandbox de OpenShell, agrega esta regla de salida a tu política de red de NemoClaw para que pueda acceder a la API de ingesta de ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Sí (panel local) |
| Socket de Docker (`/var/run/docker.sock`) | — | Socket Unix | Para el descubrimiento de sesiones de contenedores |

El daemon de sincronización solo realiza llamadas HTTPS salientes a `ingest.clawmetry.com`. No se requieren puertos entrantes.

---

## Despliegue en la nube

Consulta la **[Guía de pruebas en la nube](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneles SSH, proxy inverso y Docker.

## Pruebas

Este proyecto se prueba con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetría

ClawMetry envía un único ping anónimo de "primera ejecución" a
`https://app.clawmetry.com/api/install` la primera vez que ejecutas la
CLI `clawmetry` en una máquina nueva. Usamos esto para contar instalaciones (la
única métrica de marketing que tenemos para un proyecto de código abierto) y para saber qué
frameworks de agentes tienen instalados nuestros usuarios.

**Exactamente un POST por instalación**, que contiene:

| Campo | Ejemplo | Por qué |
|---|---|---|
| `install_id` | UUID aleatorio almacenado en `~/.clawmetry/install_id` | deduplicación; no vinculado a tu correo electrónico o api_key |
| `version` | `0.12.167` | qué versiones están en uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de soporte de plataforma |
| `python` | `3.11.15` | matriz de soporte de versiones de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con qué agentes deberíamos integrarnos después |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalaciones humanas del ruido de CI |

**Lo que NO enviamos**: IP (la nube deriva el código de país del lado del servidor
a partir de la solicitud, y luego descarta la IP), nombre de host, nombre de usuario, ruta del
espacio de trabajo, contenido de archivos, tu api_key, tu correo electrónico, nada que sea información personal identificable o
específica del espacio de trabajo. La carga útil transmitida se puede auditar en
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Optar por no participar** (cualquiera de estas opciones lo deshabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un fallo de red aquí nunca impide que `clawmetry` se ejecute; el
ping es de disparar y olvidar (fire-and-forget) en un hilo daemon con un tiempo de espera de 3 s.

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
