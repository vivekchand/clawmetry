<!-- i18n-src:6795052055e2 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **26 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 22 innych. Jeden panel dla całej floty agentów.

> 🌐 **Przeczytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Wykrywa wszystko automatycznie.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje środowiska uruchomieniowe agentów, które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w ich działaniu.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Współpracuje z 26 środowiskami uruchomieniowymi agentów

**Bezmy w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Każde środowisko uruchomieniowe otrzymuje ten sam panel. Uruchom kilka naraz, a przełącznik w nagłówku przeskaluje każdą zakładkę do jednego z nich.

Zbudowałeś własnego agenta na SDK zamiast tego? Interceptor śledzi też jego wywołania LLM. Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co robił każdy agent, krok po kroku, z możliwością odtworzenia
- **Koszty i tokeny**: według środowiska uruchomieniowego, modelu, sesji i dnia, z flagami anomalii
- **Flow**: diagram na żywo pokazujący przepływ wiadomości między kanałami, modelami i narzędziami
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Pamięć i umiejętności**: pliki i umiejętności, które faktycznie wczytało każde środowisko uruchomieniowe
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity zapytań, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slack, Discord, PagerDuty, Telegram, Email
- **Zatwierdzenia**: wstrzymaj ryzykowne wywołania narzędzi *zanim* się wykonają i zatwierdź je z telefonu ([jak to działa](docs/APPROVALS.md))

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Darmowy** | OpenClaw + NVIDIA NemoClaw + Goose, pełny panel, tylko lokalnie | $0 |
| **Starter** | Każde inne środowisko uruchomieniowe powyżej, widok floty, synchronizacja w chmurze | $9 za węzeł / miesiąc |
| **Pro** | Starter + governance: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel | $19 za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na stronie
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne do samodzielnego hostowania
działają bez chmury (`clawmetry license`). Dokładny podział darmowe/płatne znajduje się
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na twoim komputerze

ClawMetry odczytuje lokalne pliki sesji i logi. Nic nie opuszcza twojego komputera, chyba że
uruchomisz `clawmetry connect`. Nawet wtedy migawka jest szyfrowana end-to-end
kluczem, który nigdy nie opuszcza twojej maszyny, i odszyfrowywana w twojej przeglądarce.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Lub jednolinijkowiec: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Pythona 3.8+ na macOS, Linuksie lub Windowsie oraz co najmniej jednego środowiska uruchomieniowego agenta na
tej samej maszynie. Instrukcje dotyczące Dockera: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentacja

| | |
|---|---|
| [Zgodność środowisk uruchomieniowych](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać nowe środowisko uruchomieniowe |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Darmowe vs płatne, macierz poziomów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady wszędzie, pobieraj OTLP z dowolnego źródła |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu widoczne we Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Konfiguracje NVIDIA NemoClaw w piaskownicy |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie woluminów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa w środku; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe zgłoszenia instalacji i otwarcia aplikacji desktopowej oraz jak je wyłączyć |

## Zrzuty ekranu

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokeny, sesje, zdrowie | **Brain**: strumień zdarzeń agenta na żywo |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: według modelu i sesji | **Approvals**: bramkowanie ryzykownych wywołań narzędzi |

Więcej, według środowiska uruchomieniowego: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Historia gwiazdek

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licencja

MIT · Stworzone przez [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
