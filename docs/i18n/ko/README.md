<!-- i18n-src:dc34072b2955 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**당신의 에이전트가 생각하는 모습을 지켜보세요.** **23개 AI 에이전트 런타임**을 위한 실시간 관찰 가능성 도구: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 및 19개 이상. 전체 에이전트 플릿을 위한 하나의 대시보드.

> 🌐 **다른 언어로 보기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 필요 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열립니다. 설정이 필요 없습니다. 이미 보유하고 있는 에이전트 런타임을 찾아내고, 읽기 전용으로 읽으며, 실행 방식에는 아무런 변경도 가하지 않습니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23개 에이전트 런타임 지원

**오픈소스 앱에서 무료:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**유료 플랜에서:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

모든 런타임은 동일한 대시보드를 제공받습니다. 여러 개를 동시에 실행하면 헤더의 전환기가 모든 탭의 범위를 선택한 런타임에 맞춰 재조정합니다.

SDK로 직접 만든 에이전트를 사용하고 있나요? 인터셉터가 해당 에이전트의 LLM 호출도 추적합니다. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)를 참고하세요.

## 제공하는 기능

- **세션 및 트랜스크립트**: 각 에이전트가 턴별로 수행한 작업, 재생 기능 포함
- **비용 및 토큰**: 런타임, 모델, 세션, 일자별로, 이상 징후 표시와 함께
- **Flow**: 채널, 모델, 도구 사이를 오가는 메시지의 실시간 다이어그램
- **Brain**: 실시간으로 발생하는 추론 및 도구 호출 이벤트 스트림
- **메모리 및 스킬**: 각 런타임이 실제로 로드한 파일과 스킬
- **상태 및 로그**: 디스크, 메모리, 오류율, 요청 제한, 실시간 로그 스트림
- **알림**: 예산 한도, 오류 급증, 에이전트 오프라인 등을 Slack, Discord, PagerDuty, Telegram, 이메일로 전달
- **승인**: 위험한 도구 호출을 실행 *전에* 일시 중지시키고 휴대폰에서 승인 ([방법](docs/APPROVALS.md))

## 가격

| 플랜 | 포함 범위 | 가격 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, 전체 대시보드, 로컬 전용 | $0 |
| **Starter** | 위의 다른 모든 런타임, 플릿 뷰, 클라우드 동기화 | 노드당 월 $9 |
| **Pro** | Starter + 거버넌스: 승인, 도구 위험 정책, 평가, 이상 징후 감지, 비용 최적화, OTel 내보내기 | 노드당 월 $19 |

연간 플랜, Enterprise 및 최신 요금 정보는
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 에서 확인하세요. 자체 호스팅 라이선스
키는 클라우드 없이도 작동합니다 (`clawmetry license`). 정확한 무료/유료 구분은
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)에 있습니다.

## 데이터는 사용자의 기기에 남아 있습니다

ClawMetry는 로컬 세션 파일과 로그를 읽습니다. `clawmetry connect`를 실행하지
않는 한 어떤 것도 기기 밖으로 나가지 않습니다. 그럴 때조차도 스냅샷은
기기 밖으로 절대 나가지 않는 키로 종단 간 암호화되며, 브라우저에서 복호화됩니다.

## 설치

```bash
pip install clawmetry     # then: clawmetry
```

또는 한 줄 명령어: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux 또는 Windows에서 Python 3.8 이상이 필요하며, 같은 기기에
에이전트 런타임이 최소 하나 있어야 합니다. Docker 안내: [docs/DOCKER.md](docs/DOCKER.md).

## 문서

| | |
|---|---|
| [런타임 호환성](docs/compatibility.md) | 각 어댑터가 읽는 내용, 런타임 추가 방법 |
| [Entitlements](docs/ENTITLEMENTS.md) | 무료 대 유료, 등급별 매트릭스, 라이선스 CLI |
| [승인 및 정책](docs/APPROVALS.md) | 실행 전 게이팅, 위험도 산정, 휴대폰 승인 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 어디로든 트레이스 내보내기, 어디서든 OTLP 수집 |
| [SDK 추적](docs/SDK_TRACKING.md) | 직접 만든 에이전트의 비용 귀속 |
| [채팅 채널](docs/CHANNELS.md) | Flow에 표시되는 채팅 어댑터 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 샌드박스화된 NVIDIA NemoClaw 설정 |
| [Docker](docs/DOCKER.md) | 이미지, 컴포즈, 볼륨 마운트 |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | 내부 동작 방식, 소스에서 실행하기 |
| [Telemetry](docs/TELEMETRY.md) | 익명 설치 및 데스크톱 실행 핑, 끄는 방법 |

## 스크린샷

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: 토큰, 세션, 상태 | **Brain**: 실시간 에이전트 이벤트 스트림 |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: 모델 및 세션별 | **Approvals**: 위험한 도구 호출 게이팅 |

런타임별 더 많은 스크린샷: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 라이선스

MIT · 제작: [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
