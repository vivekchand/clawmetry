<!-- i18n-src:dc34072b2955 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **23 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 19 innych. Jeden panel dla całej floty twoich agentów.

> 🌐 **Przeczytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje środowiska uruchomieniowe agentów, które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w sposobie ich działania.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 23 środowiskami uruchomieniowymi agentów

**Bezmyślnie za darmo w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Każde środowisko uruchomieniowe otrzymuje ten sam panel. Uruchom kilka naraz, a przełącznik w nagłówku przeskaluje każdą zakładkę do jednego z nich.

Zbudowałeś własnego agenta na SDK zamiast tego? Interceptor śledzi również jego wywołania LLM. Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co zrobił każdy agent, tura po turze, z możliwością odtworzenia
- **Koszty i tokeny**: w podziale na środowisko uruchomieniowe, model, sesję i dzień, z flagami anomalii
- **Flow**: żywy diagram wiadomości przepływających przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Pamięć i umiejętności**: pliki i umiejętności, które faktycznie wczytało każde środowisko uruchomieniowe
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity szybkości, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slacka, Discorda, PagerDuty, Telegrama, e-maila
- **Zatwierdzenia**: wstrzymuj ryzykowne wywołania narzędzi *zanim* się wykonają i zatwierdzaj je z telefonu ([jak](docs/APPROVALS.md))

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, pełny panel, tylko lokalnie | 0 USD |
| **Starter** | Wszystkie pozostałe środowiska uruchomieniowe powyżej, widok floty, synchronizacja w chmurze | 9 USD za węzeł / miesiąc |
| **Pro** | Starter + governance: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel | 19 USD za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na stronie
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne do samodzielnego hostowania
działają bez chmury (`clawmetry license`). Dokładny podział na darmowe/płatne funkcje znajduje się
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na twoim komputerze

ClawMetry odczytuje lokalne pliki sesji i logi. Nic nie opuszcza twojego komputera, chyba że
uruchomisz `clawmetry connect`. Nawet wtedy migawka jest szyfrowana end-to-end
kluczem, który nigdy nie opuszcza twojego komputera, i jest odszyfrowywana w twojej przeglądarce.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Lub jedną linią: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Python 3.8+ na macOS, Linuksie lub Windowsie oraz co najmniej jednego środowiska uruchomieniowego agenta na
tej samej maszynie. Instrukcje Dockera: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentacja

| | |
|---|---|
| [Zgodność środowisk uruchomieniowych](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać środowisko uruchomieniowe |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Darmowe vs płatne, macierz poziomów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady wszędzie, przyjmuj OTLP od wszystkiego |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisywanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu pokazywane w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Piaskownicowe konfiguracje NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie wolumenów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa w środku; uruchamianie ze źródła |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe sygnały instalacji i otwarcia aplikacji desktopowej oraz jak je wyłączyć |

## Zrzuty ekranu

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: tokeny, sesje, zdrowie | **Brain**: strumień zdarzeń agenta na żywo |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Koszt**: według modelu i sesji | **Zatwierdzenia**: bramkowanie ryzykownych wywołań narzędzi |

Więcej, w podziale na środowisko uruchomieniowe: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
