<!-- i18n-src:dc34072b2955 -->
> Español (LatAm) translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ve pensar a tu agente.** Observabilidad en tiempo real para **25 runtimes de agentes de IA**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex y 21 más. Un solo panel para toda tu flota de agentes.

> 🌐 **Lee esto en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un solo comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900**. Cero configuración: encuentra los runtimes de agentes
que ya tienes, los lee en modo de solo lectura y no cambia nada de cómo funcionan.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funciona con 25 runtimes de agentes

**Gratis en la app de código abierto:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**En un plan pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Cada runtime obtiene el mismo panel. Ejecuta varios a la vez y el selector del
encabezado reenfoca cada pestaña hacia uno de ellos.

¿Construiste tu propio agente con un SDK en lugar de esto? El interceptor también
rastrea sus llamadas a LLM. Consulta [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Qué obtienes

- **Sesiones y transcripciones**: qué hizo cada agente, turno por turno, con repetición
- **Costo y tokens**: por runtime, modelo, sesión y día, con marcas de anomalías
- **Flow**: diagrama en vivo de los mensajes que se mueven entre canales, modelos y herramientas
- **Brain**: el flujo de eventos de razonamiento y llamadas a herramientas en tiempo real
- **Memoria y skills**: los archivos y skills que cada runtime realmente cargó
- **Salud y logs**: disco, memoria, tasas de error, límites de tasa, flujo de logs en vivo
- **Alertas**: topes de presupuesto, picos de errores, agente fuera de línea, enrutadas a Slack, Discord, PagerDuty, Telegram, Email
- **Aprobaciones**: pausa llamadas a herramientas riesgosas *antes* de que se ejecuten y apruébalas desde tu teléfono ([cómo](docs/APPROVALS.md))

## Precios

| Plan | Qué cubre | Precio |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, panel completo, solo local | $0 |
| **Starter** | Todos los demás runtimes mencionados arriba, vista de flota, sincronización en la nube | $9 por nodo / mes |
| **Pro** | Starter + gobernanza: aprobaciones, políticas de riesgo de herramientas, evaluaciones, detección de anomalías, optimizador de costos, exportación OTel | $19 por nodo / mes |

Los planes anuales, Enterprise y los precios actuales están en
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Las claves de licencia
autoalojadas funcionan sin la nube (`clawmetry license`). La división exacta entre
gratis y pago está en [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Tus datos se quedan en tu máquina

ClawMetry lee archivos de sesión y logs locales. Nada sale de tu equipo a menos que
ejecutes `clawmetry connect`. Incluso entonces, el snapshot está cifrado de extremo a
extremo con una clave que nunca sale de tu máquina, y se descifra en tu navegador.

## Instalación

```bash
pip install clawmetry     # luego: clawmetry
```

O el comando de una línea: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Requiere Python 3.8+ en macOS, Linux o Windows, y al menos un runtime de agente en
la misma máquina. Instrucciones de Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentación

| | |
|---|---|
| [Compatibilidad de runtimes](docs/compatibility.md) | Qué lee cada adaptador, y cómo agregar un runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis vs. pago, matriz de niveles, CLI de licencias |
| [Aprobaciones y políticas](docs/APPROVALS.md) | Bloqueo previo a la ejecución, puntuación de riesgo, aprobaciones desde el teléfono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporta trazas a cualquier lugar, ingiere OTLP desde cualquier fuente |
| [Seguimiento de SDK](docs/SDK_TRACKING.md) | Atribución de costos para agentes que construiste tú mismo |
| [Canales de chat](docs/CHANNELS.md) | Los adaptadores de chat que se muestran en Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configuraciones de NVIDIA NemoClaw en sandbox |
| [Docker](docs/DOCKER.md) | Imagen, compose, montajes de volúmenes |
| [Arquitectura](ARCHITECTURE.md) · [Desarrollo](docs/DEVELOPMENT.md) | Cómo funciona por dentro; cómo ejecutarlo desde el código fuente |
| [Telemetría](docs/TELEMETRY.md) | Los pings anónimos de instalación y apertura de escritorio, y cómo desactivarlos |

## Capturas de pantalla

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokens, sesiones, salud | **Brain**: flujo de eventos del agente en vivo |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: por modelo y sesión | **Approvals**: bloquea llamadas a herramientas riesgosas |

Más, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Historial de estrellas

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licencia

MIT · Creado por [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
