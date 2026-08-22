<!-- i18n-src:c111f32e69a5 -->
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

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **26 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 22 innych. Jeden panel dla całej twojej floty agentów.

> 🌐 **Czytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje środowiska uruchomieniowe agentów,
które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w sposobie ich działania.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 26 środowiskami uruchomieniowymi agentów

**Bezpłatne w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Każde środowisko uruchomieniowe otrzymuje ten sam panel. Uruchom kilka jednocześnie, a przełącznik
w nagłówku zmieni zakres każdej zakładki na wybrane z nich.

Zbudowałeś własnego agenta na bazie SDK zamiast? Interceptor śledzi również jego wywołania LLM.
Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co zrobił każdy agent, krok po kroku, z możliwością odtworzenia
- **Koszty i tokeny**: według środowiska uruchomieniowego, modelu, sesji i dnia, z oznaczeniami anomalii
- **Flow**: diagram na żywo przedstawiający wiadomości przepływające przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Pamięć i umiejętności**: pliki i umiejętności rzeczywiście wczytane przez każde środowisko uruchomieniowe
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity zapytań, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slacka, Discorda, PagerDuty, Telegramu, e-maila
- **Zatwierdzenia**: wstrzymaj ryzykowne wywołania narzędzi *zanim* zostaną wykonane i zatwierdzaj z telefonu ([jak](docs/APPROVALS.md))

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, pełny panel, tylko lokalnie | 0 USD |
| **Starter** | Wszystkie pozostałe środowiska uruchomieniowe powyżej, widok floty, synchronizacja w chmurze | 9 USD za węzeł / miesiąc |
| **Pro** | Starter + governance: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel | 19 USD za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na stronie
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne do samodzielnego hostingu
działają bez chmury (`clawmetry license`). Dokładny podział na funkcje bezpłatne i płatne znajduje się
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na twoim komputerze

ClawMetry odczytuje lokalne pliki sesji i logi. Nic nie opuszcza twojego urządzenia, chyba że
uruchomisz `clawmetry connect`. Nawet wtedy zrzut danych jest szyfrowany end-to-end kluczem,
który nigdy nie opuszcza twojego komputera, a odszyfrowanie następuje w twojej przeglądarce.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Lub jedna linijka: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Python 3.8+ na macOS, Linuksie lub Windows oraz co najmniej jednego środowiska uruchomieniowego
agenta na tym samym komputerze. Instrukcje dla Dockera: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentacja

| | |
|---|---|
| [Zgodność środowisk uruchomieniowych](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać środowisko uruchomieniowe |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Bezpłatne vs płatne, macierz poziomów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady dowolnie, przyjmuj OTLP z dowolnego źródła |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisywanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu widoczne w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Piaskownicowe konfiguracje NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie wolumenów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa w środku; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe sygnały instalacji i otwarcia aplikacji desktopowej oraz jak je wyłączyć |

## Zrzuty ekranu

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokeny, sesje, zdrowie | **Brain**: strumień zdarzeń agenta na żywo |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Koszt**: według modelu i sesji | **Zatwierdzenia**: bramkowanie ryzykownych wywołań narzędzi |

Więcej, dla każdego środowiska uruchomieniowego: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
