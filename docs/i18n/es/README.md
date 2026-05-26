<!-- i18n-src:56ff57310588 -->
> Español translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Observa pensar a tu agente.** Observabilidad en tiempo real para agentes de IA de [OpenClaw](https://github.com/openclaw/openclaw).

> 🌐 **Léelo en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Un solo comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900** y listo.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Qué obtienes

- **Flow**: Diagrama animado en vivo que muestra los mensajes fluyendo a través de los canales, el cerebro, las herramientas y de vuelta
- **Overview**: Comprobaciones de salud, mapa de calor de actividad, recuentos de sesiones, información del modelo
- **Usage**: Seguimiento de tokens y costos con desgloses diarios, semanales y mensuales
- **Sessions**: Sesiones de agente activas con modelo, tokens y última actividad
- **Crons**: Trabajos programados con estado, próxima ejecución y duración
- **Logs**: Transmisión de registros en tiempo real con códigos de color
- **Memory**: Explora SOUL.md, MEMORY.md, AGENTS.md y notas diarias
- **Transcripts**: Interfaz de burbujas de chat para leer historiales de sesiones
- **Alerts**: Límites de presupuesto, disparadores por tasa de errores, detección de agente desconectado; enruta a Slack, Discord, PagerDuty, Telegram y correo electrónico
- **Approvals**: Coloca las eliminaciones destructivas, los force push, las mutaciones de base de datos, sudo, las instalaciones de paquetes y las llamadas de red detrás de una aprobación con un solo clic

## Capturas de pantalla

### 🧠 Brain — Flujo de eventos del agente en vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Uso de tokens y resumen de sesiones
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed de llamadas a herramientas en tiempo real
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Desglose de costos por modelo y sesión
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Explorador de archivos del espacio de trabajo
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura y registro de auditoría
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Límites de presupuesto, disparadores por tasa de errores, webhooks a Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Coloca las llamadas a herramientas arriesgadas detrás de una aprobación manual; reglas de protección respaldadas por políticas
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

La aplicación React v2 vive en `frontend/` y se sirve en `/v2` cuando el servidor
Flask se inicia con v2 habilitado.

Usa dos terminales mientras desarrollas:

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
`http://localhost:8900`, de modo que la aplicación React puede comunicarse con el servidor Flask local
sin necesidad de configuración adicional de CORS.

Para construir el bundle que se distribuye con el paquete de Python:

```bash
cd frontend
npm run build
```

El bundle de producción se escribe en `clawmetry/static/v2/dist/`.

## Compatibilidad de runtimes / agentes

ClawMetry observa muchos runtimes de agentes de IA, no solo OpenClaw. Cada runtime que no es OpenClaw incluye un adaptador de lectura dedicado que traduce su formato de sesión nativo a las formas unificadas de ClawMetry; el daemon los ingiere en el mismo almacén DuckDB y snapshot en la nube, etiquetados con el runtime, y la pestaña de reproducción de sesiones muestra un **selector de runtime** cuando hay más de uno presente. Consulta [`docs/compatibility.md`](docs/compatibility.md) para ver la matriz completa y una guía para agregar runtimes, y [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para la introducción a la familia OpenClaw.

| Runtime / Agente | Estado | Notas |
|---|---|---|
| **OpenClaw** | Nativo | Runtime de referencia, detectado automáticamente |
| **PicoClaw** | Adaptador beta | JSONL plano `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripciones, modelo, llamadas a herramientas. |
| **NanoClaw** | Adaptador beta | SQLite por sesión (`data/v2-sessions`). Transcripciones y recuentos de mensajes. |
| **Hermes** | Adaptador beta | SQLite `~/.hermes/state.db`. Transcripciones, modelo, tokens/costo. |
| **Claude Code** | Adaptador beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripciones, modelo, llamadas a herramientas y razonamiento, uso de tokens. |
| **Codex** | Adaptador beta | Rollout JSONL `~/.codex/sessions/...`. Transcripciones, modelo, llamadas a herramientas, uso de tokens. |
| **Cursor** | Adaptador beta | SQLite `state.vscdb`. Transcripciones de chat/composer, modelo. |
| **Aider** | Adaptador beta | `.aider.chat.history.md` por proyecto. Transcripciones, modelo, recuentos de tokens. |
| **Goose** | Adaptador beta | SQLite `~/.local/share/goose`. Transcripciones, modelo, llamadas a herramientas, totales de tokens. |

"Adaptador beta" significa que ClawMetry incluye un lector para el formato real en disco de ese runtime, cada uno construido y verificado contra una instalación real en una máquina real (consulta `tests/fixtures/runtimes/<rt>/`). Los adaptadores son de solo lectura; cada uno es honesto sobre lo que su runtime realmente almacena (por ejemplo, PicoClaw/NanoClaw/Cursor no escriben el costo de tokens en disco). Cuando varios runtimes se ejecutan en un nodo, el selector de runtime limita la vista de sesiones a uno solo para un análisis a fondo más claro.

## OpenTelemetry — neutral respecto al proveedor, envía tus trazas a cualquier lugar

ClawMetry habla **OpenTelemetry** en ambas direcciones, usando las **convenciones semánticas GenAI**, de modo que las trazas de tu agente nunca quedan atadas a una sola herramienta.

**Exporta** cada sesión (llamadas a LLM, herramientas, sub-agentes, tokens, costo) como spans GenAI OTLP/HTTP a cualquier colector (Datadog, Grafana, Honeycomb o tu propio OTel Collector):

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

**Ingiere**: el receptor OTLP incorporado acepta trazas y métricas de cualquier otra cosa en `/v1/traces` y `/v1/metrics` (`pip install clawmetry[otel]` para la ingesta de protobuf).

Obtienes el dashboard de ClawMetry sin configuración y local-first **y además** tus datos en cualquier backend que tu equipo ya use: sin ataduras, sin un segundo agente que instalar.

## Configuración

La mayoría de la gente no necesita ninguna configuración. ClawMetry detecta automáticamente tu espacio de trabajo, registros, sesiones y crons.

Si necesitas personalizar:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Todas las opciones: `clawmetry --help`

## Canales compatibles

ClawMetry muestra la actividad en vivo de cada canal de OpenClaw que tengas configurado. Solo los canales que están realmente configurados en tu `openclaw.json` aparecen en el diagrama de Flow; los no configurados se ocultan automáticamente.

Haz clic en cualquier nodo de canal en el Flow para ver una vista de burbujas de chat en vivo con los recuentos de mensajes entrantes/salientes.

| Canal | Estado | Popup en vivo | Notas |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Mensajes, estadísticas, actualización cada 10 s |
| 💬 **iMessage** | ✅ Completo | ✅ | Lee `~/Library/Messages/chat.db` directamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | A través de WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | A través de signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Detección de guild y canal |
| 🟪 **Slack** | ✅ Completo | ✅ | Detección de workspace y canal |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sesiones de la interfaz web incorporada |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaz de burbujas estilo terminal |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage a través de la API REST de BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | A través de webhooks de la Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | A través del plugin de bot de Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat de equipo autoalojado |
| 🟩 **Matrix** | ✅ Completo | ✅ | Descentralizado, soporte E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | Mensajes directos NIP-04 descentralizados |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat a través de conexión IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Suscripción a eventos por WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Detección automática:** ClawMetry lee tu `~/.openclaw/openclaw.json` y solo renderiza los canales que realmente has configurado. No se requiere configuración manual.

## Despliegue con Docker

¿Quieres ejecutar ClawMetry en un contenedor? ¡No hay problema! 🐳

**Inicio rápido con Docker:**

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

> **Nota:** Cuando lo ejecutes en Docker, asegúrate de montar tu espacio de trabajo de OpenClaw y los directorios de registros para que ClawMetry pueda detectar automáticamente tu configuración.

## Requisitos

- Python 3.8+
- Flask (se instala automáticamente vía pip)
- OpenClaw ejecutándose en la misma máquina (o volúmenes montados para Docker)
- Linux o macOS

## Soporte de NemoClaw / OpenShell

ClawMetry detecta automáticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), el envoltorio de seguridad empresarial de NVIDIA para OpenClaw que ejecuta agentes dentro de contenedores OpenShell aislados (sandbox).

En la mayoría de los casos no se necesita configuración adicional. El daemon de sincronización descubre automáticamente los archivos de sesión, ya sea que vivan en `~/.openclaw/` en el host o dentro de un contenedor OpenShell.

### Cómo funciona

ClawMetry detecta NemoClaw de dos maneras:

1. **Detección del binario**: comprueba la presencia de la CLI `nemoclaw` y ejecuta `nemoclaw status` para obtener información del sandbox
2. **Detección de contenedores**: escanea los contenedores Docker en ejecución en busca de imágenes `openshell`, `nemoclaw` o `ghcr.io/nvidia/`, luego lee las sesiones a través de volúmenes montados o `docker cp`

Los archivos de sesión sincronizados desde contenedores NemoClaw se etiquetan con los metadatos `runtime=nemoclaw` y `container_id` en el dashboard de la nube, de modo que puedes distinguirlos de las sesiones estándar de OpenClaw de un vistazo.

### Configuración recomendada: daemon de sincronización en el HOST

Para la mejor experiencia, ejecuta el daemon de sincronización de ClawMetry en la **máquina host** (no dentro del sandbox). Esto evita las restricciones de la política de red de NemoClaw.

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

Si debes ejecutar el daemon de sincronización **dentro** del sandbox de OpenShell, agrega esta regla de egreso a tu política de red de NemoClaw para que pueda llegar a la API de ingesta de ClawMetry:

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
CLI `clawmetry` en una máquina nueva. Lo usamos para contar instalaciones (la
única métrica de marketing que tenemos para un proyecto de código abierto) y para saber qué
frameworks de agentes tienen instalados nuestros usuarios.

**Exactamente un POST por instalación**, que contiene:

| Campo | Ejemplo | Por qué |
|---|---|---|
| `install_id` | UUID aleatorio almacenado en `~/.clawmetry/install_id` | deduplicación; no vinculado a tu correo electrónico ni api_key |
| `version` | `0.12.167` | qué versiones están en circulación |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioridades de soporte de plataformas |
| `python` | `3.11.15` | matriz de soporte de versiones de Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con qué agentes deberíamos integrarnos a continuación |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separar las instalaciones humanas del ruido de CI |

**Lo que NO enviamos**: IP (la nube deriva el código de país del lado del servidor
a partir de la solicitud y luego descarta la IP), nombre de host, nombre de usuario, ruta del espacio
de trabajo, contenido de archivos, tu api_key, tu correo electrónico, ni nada de información personal o
específica del espacio de trabajo. La carga útil enviada es auditable en
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Cómo desactivarlo** (cualquiera de estas opciones lo deshabilita de forma permanente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un fallo de red aquí nunca impide que `clawmetry` se ejecute: el
ping es del tipo "dispara y olvida" en un hilo de daemon con un tiempo de espera de 3 s.

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
  <strong>🦞 Observa pensar a tu agente</strong><br>
  <sub>Creado por <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte del ecosistema de <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
