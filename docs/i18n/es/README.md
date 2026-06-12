<!-- i18n-src:48548997be76 -->
> Español translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ve a tu agente pensar.** Observabilidad en tiempo real para **12 entornos de ejecución de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex y 8 más. Un panel para toda tu flota de agentes.

> 🌐 **Léelo en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un comando. Sin configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900** y listo.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatible con 12 entornos de ejecución de agentes

ClawMetry comenzó como observabilidad para OpenClaw, y ahora mide toda tu **flota de agentes** en un solo panel, detectando automáticamente cada entorno de ejecución en tu máquina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw y NemoClaw son gratuitos en la aplicación de código abierto; los demás entornos se activan con ClawMetry Cloud o una licencia Pro auto-alojada. Cambia de entorno desde el encabezado y cada pestaña (coste, tokens, herramientas, trazas) se ajusta a ese entorno.

## Qué obtienes

- **Flow** — Diagrama animado en vivo que muestra mensajes fluyendo por canales, cerebro, herramientas y de vuelta
- **Overview** — Verificaciones de salud, mapa de calor de actividad, conteo de sesiones, información del modelo
- **Usage** — Seguimiento de tokens y costes con desgloses diarios, semanales y mensuales
- **Sessions** — Sesiones de agentes activos con modelo, tokens y última actividad
- **Crons** — Trabajos programados con estado, próxima ejecución y duración
- **Logs** — Transmisión de registros en tiempo real con código de colores
- **Memory** — Explorar SOUL.md, MEMORY.md, AGENTS.md y notas diarias
- **Transcripts** — Interfaz de burbujas de chat para leer historiales de sesiones
- **Alerts** — Límites de presupuesto, disparadores por tasa de errores, detección de agente fuera de línea; enrutamiento a Slack, Discord, PagerDuty, Telegram y correo electrónico
- **Approvals** — Controla eliminaciones destructivas, force pushes, mutaciones de BD, sudo, instalaciones de paquetes y llamadas de red con aprobación en un clic

## Capturas de pantalla

### 🧠 Brain — Transmisión de eventos del agente en vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens y resumen de sesiones
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Registro de llamadas a herramientas en tiempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desglose de costes por modelo y sesión
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de archivos del espacio de trabajo
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura de seguridad y registro de auditoría
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Límites de presupuesto, disparadores por tasa de errores, webhooks a Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Controla las llamadas a herramientas arriesgadas con aprobación manual; reglas de protección respaldadas por políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalación

**Una sola línea (recomendado):**
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

La aplicación React v2 se encuentra en `frontend/` y se sirve en `/v2` cuando el servidor Flask se inicia con v2 habilitado.

Usa dos terminales durante el desarrollo:

```bash
# Terminal 1: API/servidor Flask en :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: servidor de desarrollo Vite en :5173
cd frontend
nvm use
npm ci
npm run dev
```

Abre `http://localhost:5173/v2/`. Vite redirige las peticiones `/api` hacia `http://localhost:8900`, por lo que la aplicación React puede comunicarse con el servidor Flask local sin configuración adicional de CORS.

Para compilar el bundle que se distribuye con el paquete Python:

```bash
cd frontend
npm run build
```

El bundle de producción se escribe en `clawmetry/static/v2/dist/`.

## Compatibilidad de entornos de ejecución y agentes

ClawMetry observa muchos entornos de ejecución de agentes de IA, no solo OpenClaw. Cada entorno distinto de OpenClaw incluye un adaptador de lectura dedicado que traduce su formato nativo de sesión a las formas unificadas de ClawMetry; el daemon los ingiere en el mismo almacén DuckDB y la instantánea en la nube, etiquetados con el entorno de ejecución, y la pestaña de reproducción de sesiones muestra un **selector de entorno** cuando hay más de uno presente. Consulta [`docs/compatibility.md`](docs/compatibility.md) para la matriz completa y una guía para agregar entornos, y [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para el manual de la familia OpenClaw.

| Entorno / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Entorno de referencia, detección automática |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripciones, modelo, llamadas a herramientas. |
| **NanoClaw** | Adaptador beta | SQLite por sesión (`data/v2-sessions`). Transcripciones y conteo de mensajes. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcripciones, modelo, tokens y coste. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripciones, modelo, llamadas a herramientas y razonamiento, uso de tokens. |
| **Codex** | Adaptador beta | JSONL de rollout `~/.codex/sessions/...`. Transcripciones, modelo, llamadas a herramientas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcripciones de chat y compositor, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por proyecto. Transcripciones, modelo, conteo de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcripciones, modelo, llamadas a herramientas, totales de tokens. |
| **opencode** | Adaptador beta | SQLite `~/.local/share/opencode`. Transcripciones, modelo, llamadas a herramientas, tokens y coste. |
| **Qwen Code** | Adaptador beta | JSONL `~/.qwen/projects/.../chats`. Transcripciones, modelo, llamadas a herramientas, uso de tokens. |

"Adaptador beta" significa que ClawMetry incluye un lector para el formato en disco real de ese entorno, cada uno construido y verificado contra una instalación real en una máquina real (ver `tests/fixtures/runtimes/<rt>/`). Los adaptadores son de solo lectura; cada uno es honesto sobre lo que su entorno realmente almacena (por ejemplo, PicoClaw, NanoClaw y Cursor no escriben el coste de tokens en disco). Cuando varios entornos se ejecutan en un nodo, el selector de entorno limita la vista de sesiones a uno para un análisis detallado limpio.

## Rastrear cualquier agente SDK — atribución de costes fuera del bucle

Los entornos mencionados anteriormente escriben sesiones en disco. Tu propio **agente de producción** (el que construiste con el SDK de Agentes de OpenAI, LangChain, el SDK de IA de Vercel, LlamaIndex, E2B o un bucle simple de `httpx`) no lo hace. El interceptor de configuración cero de ClawMetry sigue capturando sus llamadas LLM (coste, tokens, latencia, errores) mediante parches a `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (o la variable de entorno `CLAWMETRY_SOURCE=support-agent`) etiqueta cada llamada con una **fuente con nombre**, por lo que cada producto que ejecutes aparece como su propia línea de primera clase, con atribución de costes, en la tarjeta **🔌 Out-loop sources** del panel de Overview: llamadas, proveedores, latencia y tasa de errores por agente. ¿Sin fuente definida? Las llamadas siguen rastreándose; la tarjeta simplemente permanece oculta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Esta es la misma capa de datos que alimentan los adaptadores de entorno (DuckDB y la instantánea en la nube), por lo que las fuentes fuera del bucle se sincronizan al panel en la nube igual que todo lo demás, con cifrado de extremo a extremo.

## OpenTelemetry — neutral al proveedor, envía tus trazas a cualquier lugar

ClawMetry habla **OpenTelemetry** en ambas direcciones, usando las **convenciones semánticas GenAI**, para que las trazas de tus agentes nunca queden atrapadas en una sola herramienta.

**Exporta** cada sesión (llamadas LLM, herramientas, subagentes, tokens y coste) como tramos OTLP/HTTP GenAI a cualquier colector (Datadog, Grafana, Honeycomb o tu propio OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Las cabeceras de autenticación y el intervalo de sondeo son variables de entorno opcionales:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingesta** — el receptor OTLP integrado acepta trazas y métricas de cualquier fuente en `/v1/traces` y `/v1/metrics` (`pip install clawmetry[otel]` para ingestión de protobuf).

Obtienes el panel de ClawMetry local y de configuración cero **y** tus datos en el backend que tu equipo ya utiliza. Sin dependencias del proveedor, sin necesidad de instalar un segundo agente.

## Configuración

La mayoría de las personas no necesitan ninguna configuración. ClawMetry detecta automáticamente tu espacio de trabajo, registros, sesiones y crons.

Si necesitas personalizar algo:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas las opciones: `clawmetry --help`

## Canales compatibles

ClawMetry muestra actividad en vivo para cada canal de OpenClaw que tengas configurado. Solo los canales realmente configurados en tu `openclaw.json` aparecen en el diagrama Flow; los no configurados se ocultan automáticamente.

Haz clic en cualquier nodo de canal en el Flow para ver una vista de burbujas de chat en vivo con conteos de mensajes entrantes y salientes.

| Canal | Estado | Popup en vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensajes, estadísticas, actualización cada 10 s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lee `~/Library/Messages/chat.db` directamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Vía WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Vía signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detección de servidor y canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detección de espacio de trabajo y canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sesiones de interfaz web integrada |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaz de burbujas estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage vía API REST de BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Vía webhooks de la API de Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Vía plugin de bot de Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipo auto-alojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, compatible con E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API de mensajería de LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DMs descentralizados NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat vía conexión IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Suscripción a eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API del Bot de Zalo |

> **Detección automática:** ClawMetry lee tu `~/.openclaw/openclaw.json` y solo renderiza los canales que hayas configurado. No se requiere configuración manual.

## Despliegue con Docker

¿Quieres ejecutar ClawMetry en un contenedor? ¡Sin problema! 🐳

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

**Ejemplo con Docker Compose:**

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

> **Nota:** Al ejecutar con Docker, monta los directorios de datos y registros de tu agente (por ejemplo, `~/.openclaw`, `~/.claude`, `~/.codex`) para que ClawMetry pueda detectar tu configuración automáticamente.

## Requisitos

- Python 3.8 o superior
- Flask (instalado automáticamente vía pip)
- Un entorno de ejecución de agente de IA en la misma máquina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw o PicoClaw (o volúmenes montados para Docker)
- Linux o macOS

## Compatibilidad con NemoClaw y OpenShell

ClawMetry detecta automáticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), el envoltorio de seguridad empresarial de NVIDIA para OpenClaw que ejecuta agentes dentro de contenedores OpenShell con aislamiento de seguridad.

En la mayoría de los casos no se necesita configuración adicional. El daemon de sincronización descubre automáticamente los archivos de sesión tanto si están en `~/.openclaw/` en el host como dentro de un contenedor OpenShell.

### Cómo funciona

ClawMetry detecta NemoClaw de dos maneras:

1. **Detección de binario** — comprueba si existe el CLI `nemoclaw` y ejecuta `nemoclaw status` para obtener información del sandbox
2. **Detección de contenedor** — escanea los contenedores Docker en ejecución en busca de imágenes `openshell`, `nemoclaw` o `ghcr.io/nvidia/`, y luego lee las sesiones mediante montajes de volumen o `docker cp`

Los archivos de sesión sincronizados desde contenedores NemoClaw se etiquetan con los metadatos `runtime=nemoclaw` y `container_id` en el panel en la nube, para que puedas distinguirlos de las sesiones estándar de OpenClaw de un vistazo.

### Configuración recomendada: daemon de sincronización en el HOST

Para la mejor experiencia, ejecuta el daemon de sincronización de ClawMetry en la **máquina host** (no dentro del sandbox). Esto evita las restricciones de política de red de NemoClaw.

```bash
# On the host (outside the sandbox)
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

Si debes ejecutar el daemon de sincronización **dentro** del sandbox OpenShell, agrega esta regla de salida a tu política de red de NemoClaw para que pueda alcanzar la API de ingesta de ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Sí (interfaz del panel local) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Para descubrimiento de sesiones en contenedor |

El daemon de sincronización solo realiza llamadas HTTPS salientes a `ingest.clawmetry.com`. No se requieren puertos de entrada.

---

## Despliegue en la nube

Consulta la **[Guía de pruebas en la nube](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para túneles SSH, proxy inverso y Docker.

## Pruebas

Este proyecto se prueba con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetría

ClawMetry envía un único ping anónimo de "primera ejecución" a
`https://app.clawmetry.com/api/install` la primera vez que ejecutas el
CLI `clawmetry` en una máquina nueva. Usamos esto para contar instalaciones (la
única métrica de marketing que tenemos para un proyecto OSS) y para conocer qué
frameworks de agentes tienen instalados nuestros usuarios.

**Exactamente un POST por instalación**, que contiene:

| Campo | Ejemplo | Por qué |
|---|---|---|
| `install_id` | UUID aleatorio almacenado en `~/.clawmetry/install_id` | deduplicación; no vinculado a tu correo electrónico ni api_key |
| `version` | `0.12.167` | qué versiones están en uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de compatibilidad de plataformas |
| `python` | `3.11.15` | matriz de compatibilidad de versiones de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con qué agentes deberíamos integrarnos a continuación |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar instalaciones humanas del ruido de CI |

**Lo que NO enviamos**: la IP (la nube deriva el código de país en el servidor a partir de la solicitud y luego descarta la IP), el nombre de host, el nombre de usuario, la ruta del espacio de trabajo, el contenido de los archivos, tu api_key, tu correo electrónico ni ningún dato PII o específico del espacio de trabajo. El payload en tránsito es auditable en
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Desactivar** (cualquiera de estas opciones lo deshabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un fallo de red aquí nunca impide que `clawmetry` se ejecute; el ping se realiza en modo "disparar y olvidar" en un hilo daemon con un tiempo de espera de 3 s.

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
  <strong>🦞 Ve a tu agente pensar</strong><br>
  <sub>Creado por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte del ecosistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
