<!-- i18n-src:a855a14295b0 -->
> Español translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Un agente puede hacer cien llamadas a herramientas sin avanzar.** ClawMetry
lee los archivos de sesión que tus agentes de código ya escriben, y reúne la línea de tiempo,
las llamadas a herramientas y cualquier dato de tokens y coste que el runtime exponga en una sola
vista, para que puedas distinguir una ejecución larga que está funcionando de una que está atascada.

Funciona con **32 runtimes de agentes de IA**: Claude Code, OpenAI Codex, Hermes, OpenClaw y 28 más. Un solo panel para toda tu flota de agentes. ([la lista completa](SUPPORTED_RUNTIMES.txt), generada a partir del catálogo.)

> 🌐 **Léelo en:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [más →](docs/i18n/)

Un solo comando. Cero configuración. Detecta todo automáticamente.

```bash
pip install clawmetry && clawmetry
```

Se abre en **http://localhost:8900**. Cero configuración: encuentra los runtimes de agentes
que ya tienes, los lee en modo solo lectura y no cambia nada de cómo se ejecutan.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Antes de instalar

| | |
|---|---|
| **Qué hace** | Lee los archivos de sesión y los logs que tus agentes ya escriben. Sin SDK, sin cambios de código, sin instrumentación en tu app. |
| **Qué ves** | Línea de tiempo de sesiones, repetición herramienta por herramienta, desglose de tokens y coste, y señales de trayectoria (bucles, fallos repetidos), por runtime. |
| **Qué es gratis** | `pip install clawmetry` lee **OpenClaw, NVIDIA NemoClaw y Goose** sin cuenta, sin clave y sin llamadas de red. Los otros 27 (Claude Code, Codex, Cursor y el resto) los lee el complemento de código cerrado `clawmetry-pro`, que llega con la prueba de 7 días o con un plan; consulta [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para ver la división exacta. |
| **Cómo empezar** | `pip install clawmetry && clawmetry`, luego abre localhost:8900. ¿Aún no tienes agentes en esta máquina? `clawmetry --sample` se abre con tres sesiones sintéticas etiquetadas. |
| **Qué sale de tu máquina** | Ningún dato de sesión, a menos que ejecutes `clawmetry connect`. Por defecto sí se ejecutan dos cosas, ambas configurables para desactivarlas y ninguna transporta contenido de sesión: un ping anónimo de instalación y una comprobación de versión en PyPI. Cada destino está inventariado en [docs/EGRESS.md](docs/EGRESS.md), reconstruido a partir de una captura de tráfico y no de la lectura de comentarios. |

Hay dos límites que vale la pena conocer antes de juzgar el resultado: los runtimes exponen
datos muy distintos (algunos no publican coste alguno; [la matriz](docs/compatibility.md)
indica cuáles, por runtime), y observar una acción no es lo mismo que poder
bloquearla ([qué controles son reales, por runtime](docs/APPROVALS.md)).


## Funciona con 32 runtimes de agentes

**Gratis en la app de código abierto:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**En un plan de pago:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Cada runtime obtiene el mismo panel. Ejecuta varios a la vez y el selector del encabezado
reencuadra cada pestaña a uno de ellos.

¿Construiste tu propio agente sobre un SDK en lugar de esto? El interceptor también rastrea sus
llamadas a LLM. Consulta [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Qué obtienes

- **Sesiones y transcripciones**: qué hizo cada agente, turno a turno, con reproducción
- **Coste y tokens**: por runtime, modelo, sesión y día, con marcadores de anomalías
- **Flow**: diagrama en vivo de los mensajes moviéndose entre canales, modelos y herramientas
- **Brain**: el flujo de eventos de razonamiento y llamadas a herramientas a medida que ocurre
- **Desbordamiento de contexto**: utilización de la ventana dimensionada por proveedor, compactación frente a desbordamiento forzado, más un mapa por runtime de lo que *no* podemos ver ([cómo](docs/CONTEXT_BLOWOUT.md))
- **Memoria y skills**: los archivos y skills que cada runtime realmente cargó
- **Salud y logs**: disco, memoria, tasas de error, límites de tasa, flujo de logs en vivo
- **Alertas**: topes de presupuesto, picos de errores, agente-fuera-de-línea, enrutadas a Slack, Discord, PagerDuty, Telegram, Email
- **Aprobaciones**: pausa llamadas a herramientas riesgosas *antes* de que se ejecuten y apruébalas desde tu teléfono ([cómo](docs/APPROVALS.md))

## Desbordamiento de contexto, y qué cuesta observar

Dos preguntas que vale la pena responder antes de confiar en cualquier herramienta de comparación de agentes.

**¿Cómo maneja el desbordamiento de la ventana de contexto entre runtimes?**

Un porcentaje de utilización solo es tan honesto como aquello por lo que divide. ClawMetry
dimensiona la ventana por proveedor a partir de [una tabla que puedes leer y
proponer en PR](clawmetry/context_windows.py), que cubre Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama y GLM. No mide los 32
runtimes con la regla de un solo proveedor. Eso importa: un turno de 300K de GPT-5 evaluado
contra los 200K de Anthropic se lee como ">100%, desbordado" cuando en realidad está al 75% de
los 400K de GPT-5. La misma regla oculta un turno de DeepSeek de 130K genuinamente desbordado
como un cómodo 65%.

Cada ventana viene con su procedencia: `model_table`, `explicit_marker`,
`observed_floor`, o un honesto `default` cuando no conocemos el modelo. Un
indicador construido sobre una suposición nunca se muestra con la misma autoridad que uno construido
sobre una consulta real.

ClawMetry solo puede ver eventos de compactación en algunos runtimes. Por eso
`GET /api/context-coverage` informa, por runtime, si un **cero significa
"se ejecutó limpio" o "estamos ciegos"**. Un `0` que en realidad significa ciego lo dice.
[Detalle completo](docs/CONTEXT_BLOWOUT.md)

**¿Cuánto cuesta la instrumentación?**

| Ruta | Añadido a tu agente | ¿Por defecto? |
|---|---|---|
| Seguimiento de archivos de sesión (los 32 runtimes) | **0**. Proceso separado, sin código de ClawMetry en tu agente | activado |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** por llamada a LLM, o 0,009% de una llamada de 5s | desactivado |
| Puerta de hook pre-herramienta (caché caliente) | **+44 ms** por llamada a herramienta con puerta, sobre un piso de intérprete de 36 ms | desactivado |
| Proxy de aplicación | **+9,7 ms** por llamada a LLM | desactivado |

Coste del host del daemon: **2.762 eventos/seg** de ingesta, **710 bytes/evento** en disco
(67,7 MB por 100k eventos), y **~12% de un núcleo** sostenido en una instalación con
mucho tráfico. Ese último número supera nuestro propio presupuesto declarado del 5-10%, así que se
publica como un bug a perseguir en lugar de omitirse de la página.

Medido en un Apple M2 Pro con `benchmarks/overhead.py`. El arnés ejecuta
cada condición en un proceso separado, alterna su orden, y **se niega
a imprimir un número cuando las rondas no coinciden en su signo**. Ejecútalo en tu propia
máquina en un minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Cada ruta se mide, incluidas las puertas de hook y el proxy de aplicación,
y el arnés se ejecuta en Linux, macOS y Windows en CI. Dos resultados que vale la pena
conocer: el proxy cuesta aproximadamente siete veces más en Windows que en Linux, y
el daemon actualmente sostiene alrededor del 12% de un núcleo, por encima de nuestro propio presupuesto del
5-10%. El JSON en bruto, el método, y lo que aún no está medido están en
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Precios

| Plan | Qué cubre | Precio |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, panel completo, solo local | $0 |
| **Starter** | Todos los demás runtimes anteriores, vista de flota, sincronización en la nube | $9 por nodo / mes |
| **Pro** | Starter + control y evaluación: aprobaciones, políticas de riesgo de herramientas, evaluaciones, detección de anomalías, optimizador de costes, exportación a OTel, registro de auditoría a prueba de manipulaciones | $19 por nodo / mes |

Los planes anuales, Enterprise y las cifras actuales están en
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Las claves de licencia autoalojadas
funcionan sin la nube (`clawmetry license`). La división exacta entre gratis y de pago está
en [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Tus datos permanecen en tu máquina

ClawMetry lee archivos de sesión y logs locales. **Ningún dato de sesión sale de tu equipo
a menos que ejecutes `clawmetry connect`**: ni prompts, respuestas, argumentos de herramientas, contenido
de archivos ni líneas de log. Cuando sí te conectas, el snapshot se cifra de extremo a extremo
con una clave que nunca sale de tu máquina, y se descifra en tu navegador. Si un
nodo no tiene clave, la subida se omite en lugar de enviarse en claro, y ninguna
respuesta del servidor puede desactivar eso.

Por defecto sí se ejecutan dos cosas antes de que te conectes, ambas configurables para desactivarlas y ninguna
transporta datos de sesión: un ping anónimo de instalación y una comprobación de versión contra
PyPI. Una instalación por defecto también consulta tu IP pública una vez para una línea de
banner de inicio. Cada destino, lo que transporta y cómo desactivarlo está listado en
[docs/EGRESS.md](docs/EGRESS.md); las instalaciones autoalojadas, redirigidas y aisladas de red
no hacen ninguna llamada saliente discrecional en absoluto.

El descifrado ocurre en tu navegador, en código que te servimos nosotros. Eso solía ser
una promesa; ahora es algo que puedes comprobar. Cada línea que toca tu clave
vive en un único archivo legible, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
que se incluye dentro del wheel y se sirve textualmente, fijado con un hash de Integridad
de Subrecursos. Para confirmar que el navegador ejecuta lo que publicamos:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Lo que eso no demuestra: nosotros servimos la página que carga el archivo, así que podríamos
servir una página distinta. Los hashes de integridad te protegen de un CDN comprometido,
no del proveedor. Lo que ganas es que cualquier sustitución tiene que ser
deliberada, visible en el código fuente de la página, y distinta de un artefacto en PyPI
que cualquiera puede obtener. Autoalojarse o mantenerse solo en local elimina
la dependencia por completo.

## Instalación

```bash
pip install clawmetry     # luego: clawmetry
```

O el comando de una línea: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Necesita Python 3.8+ en macOS, Linux o Windows, y al menos un runtime de agente en
la misma máquina. Instrucciones de Docker: [docs/DOCKER.md](docs/DOCKER.md).

O deja que el agente lo configure por ti. El skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
enseña a Claude Code, Codex, Cursor, Gemini CLI, Copilot u OpenCode a
instalar ClawMetry, informar qué están haciendo y gastando los agentes de la máquina,
detener una sesión bajo petición, y retener llamadas a herramientas riesgosas para aprobación:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentación

| | |
|---|---|
| [Compatibilidad de runtimes](docs/compatibility.md) | Qué lee cada adaptador, y cómo añadir un runtime |
| [Desbordamiento de contexto](docs/CONTEXT_BLOWOUT.md) | Ventanas por proveedor, compactación frente a desbordamiento, cobertura por runtime |
| [Overhead](docs/OVERHEAD.md) | Qué cuesta la instrumentación, medido, con el arnés para reproducirlo |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis frente a de pago, matriz de niveles, CLI de licencia |
| [Aprobaciones y políticas](docs/APPROVALS.md) | Bloqueo previo a la ejecución, puntuación de riesgo, aprobaciones desde el teléfono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporta trazas a cualquier lugar, ingiere OTLP desde cualquier cosa |
| [Trae tu propio agente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain de principio a fin, con ejemplos ejecutables |
| [Seguimiento de SDK](docs/SDK_TRACKING.md) | Atribución de costes para agentes que construiste tú mismo |
| [Canales de chat](docs/CHANNELS.md) | Los adaptadores de chat mostrados en Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configuraciones de NVIDIA NemoClaw en sandbox |
| [Docker](docs/DOCKER.md) | Imagen, compose, montajes de volúmenes |
| [Arquitectura](ARCHITECTURE.md) · [Desarrollo](docs/DEVELOPMENT.md) | Cómo funciona por dentro; ejecución desde el código fuente |
| [Telemetría](docs/TELEMETRY.md) | Los pings anónimos de instalación y de apertura del escritorio, y cómo desactivarlos |

## Capturas de pantalla

Cada número a continuación proviene de una máquina real, en modo solo lectura, sin nada preparado.

**Te dice cuándo algo va mal, no solo lo que pasó.**
Dos banners de anomalías en la parte superior: gasto corriendo 7 veces el promedio diario, y un
pico de coste de 4,2x. Debajo, 324 de 667 sesiones recientes con una
señal de desperdicio, desglosadas por causa.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Te muestra a dónde fue el dinero, en cada ventana.**
$252,47 hoy, $513,15 esta semana, $1.312,92 este mes, cada uno con los tokens
detrás y cuánto de eso ya cubre tu suscripción. Debajo de eso,
alrededor de $1.128/mes desglosados como recuperables y $17.256/mes ya ahorrados por
la reutilización de caché.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Dibuja cómo un mensaje se convierte en una respuesta.**
El diagrama de flujo en vivo: tú, el canal por el que llegó, la puerta de enlace, el modelo
respondiendo en este momento, y cada herramienta a la que recurrió. Los nodos se iluminan a medida que el trabajo
avanza a través de ellos.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Cada agente de la máquina, en una sola tabla.**
Qué ejecuta, qué cuesta en las últimas 24 horas y a lo largo de su vida, cuándo
se vio por última vez, quién lo posee, y si una suscripción está cubriendo la
factura. 14 agentes aquí, 3 sesiones trabajando, 13 en silencio.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Muestra a dónde fue el tiempo y el dinero de un turno, herramienta por herramienta.**
Un turno de una sesión real: 11 herramientas en 11,2 minutos por $1,16. Cada llamada
a Bash y a modelo obtiene su propia barra en la línea de tiempo, para que la orden que se ejecutó
durante 4,1 minutos y la que se ejecutó durante 226ms se distingan de un vistazo.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Califica el trabajo, no solo el gasto.**
Un sobresaliente esta semana: 54 tareas salieron limpias, 2 accidentadas costaron $48,57, y las
ejecuciones con demasiada poca actividad para juzgar quedan fuera de la calificación en lugar de
contarse como aciertos. Cada ejecución accidentada enlaza a su traza.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Muestra por qué la ventana de contexto sigue llenándose.**
715K de una ventana de 1M de tokens en el último turno, un pico del 83,3%, 4 compactaciones
que se dispararon todas de forma proactiva en lugar de por un desbordamiento, y la utilización de
cada turno detrás de eso.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**La detección funciona sin que configures nada.**
Los detectores integrados están activos desde la instalación: el agente se quedó en silencio, el feed de telemetría
se detuvo, pico de coste, ráfaga de tokens, errores en aumento, pico de errores, umbral
de presupuesto, firma de amenaza coincidente, hallazgo de herramienta de seguridad, postura de seguridad
cambiada. Tus propias reglas son opcionales, además de estas.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Retener una llamada riesgosa es opcional, y viene desactivado.**
Los borrados recursivos, los push forzados, sudo, los secretos, las instalaciones de paquetes y las llamadas
salientes obtienen cada uno una regla que puedes activar. Hasta que lo hagas, ClawMetry observa y
no cambia nada. Una vez que una está activa, las llamadas coincidentes esperan aquí (o en tu teléfono)
para una aprobación o un rechazo.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Más, por runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Reconocimiento

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
