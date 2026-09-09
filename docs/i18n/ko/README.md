<!-- i18n-src:61beb8393e2f -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**에이전트는 진전 없이도 백 번의 도구 호출을 할 수 있습니다.** ClawMetry는
여러분의 코딩 에이전트가 이미 작성하고 있는 세션 파일을 읽어, 타임라인과
도구 호출, 그리고 런타임이 노출하는 토큰 및 비용 데이터를 하나의 화면에
모아줍니다 — 그래서 잘 진행되고 있는 긴 실행과 멈춰버린 실행을 구분할 수
있습니다.

**30개의 AI 에이전트 런타임**과 함께 동작합니다 — Claude Code, OpenAI Codex, Hermes, OpenClaw 등 26개 이상. 여러분의 전체 에이전트 플릿을 위한 하나의 대시보드입니다. ([전체 목록](SUPPORTED_RUNTIMES.txt), 카탈로그에서 생성됨.)

> 🌐 **다음 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더보기 →](docs/i18n/)

한 줄 명령. 설정 필요 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열립니다. 설정이 필요 없습니다: 이미 가지고 있는
에이전트 런타임을 찾아내고, 읽기 전용으로 읽으며, 그것들이 실행되는 방식을
전혀 바꾸지 않습니다.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 설치 전에

| | |
|---|---|
| **하는 일** | 여러분의 에이전트가 이미 작성하고 있는 세션 파일과 로그를 읽습니다. SDK도, 코드 변경도, 앱 내부의 계측도 필요 없습니다. |
| **보이는 것** | 세션 타임라인, 도구별 리플레이, 토큰 및 비용 분석, 그리고 궤적 신호(루프, 반복된 실패) — 런타임별로 제공됩니다. |
| **무료로 제공되는 것** | `pip install clawmetry`는 계정도, 키도, 네트워크 호출도 없이 **OpenClaw, NVIDIA NemoClaw, Goose**를 읽습니다. 나머지 27개 — Claude Code, Codex, Cursor 등 — 는 클로즈드소스인 `clawmetry-pro` 컴패니언이 읽으며, 이는 7일 무료 체험 또는 유료 플랜과 함께 제공됩니다 — 정확한 구분은 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)를 참고하세요. |
| **시작 방법** | `pip install clawmetry && clawmetry` 실행 후 localhost:8900을 엽니다. 이 머신에 아직 에이전트가 없나요? `clawmetry --sample`을 실행하면 라벨이 붙은 세 개의 합성 세션으로 열립니다. |
| **여러분의 머신을 떠나는 데이터** | `clawmetry connect`를 실행하지 않는 한 세션 데이터는 없습니다. 기본적으로 두 가지가 실행되며, 둘 다 옵트아웃 가능하고 세션 내용을 포함하지 않습니다: 익명 설치 핑과 PyPI 버전 확인입니다. 모든 목적지는 주석을 읽어서가 아니라 실제 네트워크 캡처로부터 재구성되어 [docs/EGRESS.md](docs/EGRESS.md)에 목록화되어 있습니다. |

결과를 판단하기 전에 알아두면 좋은 두 가지 제한이 있습니다: 런타임들은 매우
다른 데이터를 노출하며(일부는 비용을 전혀 게시하지 않습니다 — [매트릭스](docs/compatibility.md)에서
런타임별로 어떤 것인지 확인할 수 있습니다), 그리고 어떤 행동을 관찰하는 것과
그것을 막을 수 있는 것은 다른 이야기입니다 ([런타임별로 실제 작동하는 제어](docs/APPROVALS.md)).


## 30개의 에이전트 런타임과 함께 동작합니다

**오픈소스 앱에서 무료:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**유료 플랜에서:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

모든 런타임이 동일한 대시보드를 제공받습니다. 여러 개를 동시에 실행하면
헤더의 전환기가 모든 탭의 범위를 그중 하나로 다시 조정합니다.

SDK로 직접 만든 여러분만의 에이전트가 있나요? 인터셉터가 그 LLM 호출도
추적합니다. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)를 참고하세요.

## 얻을 수 있는 것

- **세션 및 트랜스크립트**: 각 에이전트가 턴마다 무엇을 했는지, 리플레이와 함께
- **비용 및 토큰**: 런타임, 모델, 세션, 일자별로, 이상치 플래그와 함께
- **Flow**: 채널, 모델, 도구를 거쳐 이동하는 메시지의 실시간 다이어그램
- **Brain**: 실시간으로 일어나는 추론 및 도구 호출 이벤트 스트림
- **컨텍스트 블로우아웃**: 프로바이더별로 크기가 조정된 윈도우 사용률, 압축(compaction) vs 강제 오버플로우, 그리고 우리가 *볼 수 없는* 것을 런타임별로 매핑 ([방법](docs/CONTEXT_BLOWOUT.md))
- **메모리 및 스킬**: 각 런타임이 실제로 로드한 파일과 스킬
- **상태 및 로그**: 디스크, 메모리, 오류율, 속도 제한, 실시간 로그 스트림
- **알림**: 예산 상한선, 오류 급증, 에이전트 오프라인, Slack, Discord, PagerDuty, Telegram, Email로 라우팅
- **승인**: 위험한 도구 호출을 실행 *전에* 일시 중지하고 휴대폰에서 승인 ([방법](docs/APPROVALS.md))

## 컨텍스트 블로우아웃, 그리고 모니터링에 드는 비용

어떤 에이전트 비교 도구를 믿기 전에 답할 만한 두 가지 질문이 있습니다.

**런타임 간 컨텍스트 윈도우 블로우아웃을 어떻게 처리하나요?**

사용률 퍼센트는 그것이 나누는 분모가 정직한 만큼만 정직합니다. ClawMetry는
[여러분이 읽고 PR할 수 있는 테이블](clawmetry/context_windows.py)을 기반으로
프로바이더별로 윈도우 크기를 조정하며, Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama, GLM을 다룹니다. 30개 런타임 전체를
하나의 벤더 기준으로 재지 않습니다. 이것이 중요한 이유는: 300K 토큰짜리
GPT-5 턴을 Anthropic의 200K 기준으로 채점하면 ">100%, 초과"로 읽히지만,
실제로는 GPT-5의 400K 중 75%일 뿐입니다. 같은 기준으로 실제로 오버플로우된
130K DeepSeek 턴은 편안한 65%로 숨겨집니다.

모든 윈도우는 `model_table`, `explicit_marker`, `observed_floor`, 혹은
모델을 모를 때의 정직한 `default` 중 하나의 출처와 함께 제공됩니다.
추측으로 만들어진 게이지는 조회(lookup)로 만들어진 게이지와 같은 권위로
표시되지 않습니다.

ClawMetry는 일부 런타임에서만 압축(compaction) 이벤트를 볼 수 있습니다.
그래서 `GET /api/context-coverage`는 런타임별로 **0이 "정상적으로 실행됨"을
의미하는지, "우리가 보지 못한다"를 의미하는지**를 보고합니다. 실제로는
보지 못한다는 의미의 `0`은 그렇게 표시됩니다.
[상세 내용](docs/CONTEXT_BLOWOUT.md)

**계측 비용은 얼마인가요?**

| 경로 | 여러분의 에이전트에 추가되는 것 | 기본값? |
|---|---|---|
| 세션 파일 tailing (30개 런타임 전체) | **0**. 별도의 프로세스, 에이전트 안에 ClawMetry 코드 없음 | on |
| HTTP 인터셉터 (`CLAWMETRY_INTERCEPT=1`) | LLM 호출당 **+0.44 ms**, 5초 호출의 0.009% | off |
| 사전 도구 훅 게이트 (웜 캐시) | 게이트된 도구 호출당 **+44 ms**, 36 ms의 인터프리터 하한선 위에 | off |
| 강제(enforcement) 프록시 | LLM 호출당 **+9.7 ms** | off |

데몬 호스트 비용: 수집(ingest) **2,762 이벤트/초**, 디스크상 **이벤트당
710바이트**(10만 이벤트당 67.7 MB), 그리고 바쁜 설치 환경에서 지속적으로
**코어 하나의 약 12%**. 마지막 숫자는 우리가 스스로 정한 5~10% 예산을
초과하는 것이므로, 페이지에서 숨기기보다는 앞으로 해결해야 할 버그로
게시했습니다.

Apple M2 Pro에서 `benchmarks/overhead.py`로 측정했습니다. 이 하니스는 각
조건을 별도의 프로세스에서 실행하고, 순서를 번갈아가며, **라운드 간에
부호가 일치하지 않으면 숫자를 출력하지 않습니다**. 여러분의 머신에서
1분 안에 실행해볼 수 있습니다:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

훅 게이트와 강제 프록시를 포함한 모든 경로가 측정되며, 이 하니스는 CI에서
Linux, macOS, Windows에서 실행됩니다. 알아둘 만한 두 가지 결과: 프록시는
Windows에서 Linux보다 약 7배 더 많은 비용이 들고, 데몬은 현재 코어 하나의
약 12%를 지속적으로 사용하며 이는 우리 자체 5~10% 예산을 초과합니다.
원본 JSON, 방법론, 그리고 아직 측정되지 않은 부분은
[docs/OVERHEAD.md](docs/OVERHEAD.md)에 있습니다.

## 요금제

| 플랜 | 포함 범위 | 가격 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, 전체 대시보드, 로컬 전용 | $0 |
| **Starter** | 위의 다른 모든 런타임, 플릿 뷰, 클라우드 동기화 | 노드당 월 $9 |
| **Pro** | Starter + 제어 및 평가: 승인, 도구 위험 정책, 평가(evals), 이상치 탐지, 비용 최적화기, OTel 내보내기, 변경 불가 감사 로그 | 노드당 월 $19 |

연간 플랜, Enterprise, 그리고 최신 가격은
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**에 있습니다. 자체
호스팅 라이선스 키는 클라우드 없이도 작동합니다 (`clawmetry license`).
정확한 무료/유료 구분은 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)에
있습니다.

## 여러분의 데이터는 여러분의 머신에 머무릅니다

ClawMetry는 로컬 세션 파일과 로그를 읽습니다. **`clawmetry connect`를 실행하지
않는 한 여러분의 박스를 떠나는 세션 데이터는 없습니다** — 프롬프트, 응답,
도구 인자, 파일 내용, 로그 라인 어느 것도 포함되지 않습니다. 연결(connect)을
할 경우, 스냅샷은 여러분의 머신을 떠나지 않는 키로 종단간 암호화되며,
여러분의 브라우저에서 복호화됩니다. 노드에 키가 없으면 업로드는 평문으로
전송되는 대신 건너뛰어지며, 어떤 서버 응답도 이를 끌 수 없습니다.

연결(connect) 전에도 기본적으로 두 가지가 실행되며, 둘 다 옵트아웃 가능하고
세션 데이터를 포함하지 않습니다: 익명 설치 핑과 PyPI에 대한 버전 확인입니다.
기본 설치는 시작 배너 라인을 위해 여러분의 공개 IP도 한 번 조회합니다.
모든 목적지, 그것이 전달하는 내용, 끄는 방법은
[docs/EGRESS.md](docs/EGRESS.md)에 나열되어 있습니다; 자체 호스팅, 재지정,
에어갭 설치는 임의의 아웃바운드 호출을 전혀 하지 않습니다.

복호화는 우리가 제공하는 코드로 여러분의 브라우저에서 일어납니다. 예전에는
그저 약속이었지만, 이제는 확인할 수 있는 것이 되었습니다. 여러분의 키를
다루는 모든 라인은 하나의 읽을 수 있는 파일에 있습니다,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), 이 파일은
wheel 안에 포함되어 그대로(verbatim) 제공되며, Subresource Integrity 해시로
고정되어 있습니다. 브라우저가 우리가 게시한 것을 실행하는지 확인하려면:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

이것이 증명하지 못하는 것: 우리는 이 파일을 로드하는 페이지도 함께
제공하므로, 다른 페이지를 제공할 수도 있습니다. Integrity 해시는 여러분을
손상된 CDN으로부터 보호하지만, 벤더 자체로부터는 보호하지 않습니다.
여러분이 얻는 것은, 어떠한 대체(substitution)도 의도적이어야 하고, 페이지
소스에서 눈에 보여야 하며, 누구나 가져올 수 있는 PyPI상의 아티팩트와
달라야 한다는 점입니다. 자체 호스팅 또는 로컬 전용 사용은 이 의존성을
완전히 제거합니다.

## 설치

```bash
pip install clawmetry     # 그다음: clawmetry
```

또는 한 줄 명령: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows에서 Python 3.8 이상이 필요하며, 같은 머신에 적어도
하나의 에이전트 런타임이 있어야 합니다. Docker 설치 안내:
[docs/DOCKER.md](docs/DOCKER.md).

또는 에이전트가 여러분을 위해 설정하게 하세요. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
스킬은 Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode에게 ClawMetry를
설치하고, 머신에 있는 에이전트들이 무엇을 하고 얼마나 쓰고 있는지 보고하고,
요청에 따라 세션 하나를 정지시키고, 위험한 도구 호출을 승인 대기 상태로
보류하는 방법을 가르칩니다:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 문서

| | |
|---|---|
| [런타임 호환성](docs/compatibility.md) | 각 어댑터가 읽는 것, 그리고 런타임을 추가하는 방법 |
| [컨텍스트 블로우아웃](docs/CONTEXT_BLOWOUT.md) | 프로바이더별 윈도우, 압축 vs 오버플로우, 런타임별 커버리지 |
| [오버헤드](docs/OVERHEAD.md) | 계측 비용, 측정치, 재현 가능한 하니스 |
| [Entitlements](docs/ENTITLEMENTS.md) | 무료 vs 유료, 티어 매트릭스, 라이선스 CLI |
| [승인 및 정책](docs/APPROVALS.md) | 실행 전 게이팅, 위험 점수, 휴대폰 승인 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 어디든 트레이스 내보내기, 무엇에서든 OTLP 수집 |
| [나만의 에이전트 가져오기](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain 전체 과정, 실행 가능한 예제와 함께 |
| [SDK 추적](docs/SDK_TRACKING.md) | 직접 만든 에이전트에 대한 비용 귀속 |
| [채팅 채널](docs/CHANNELS.md) | Flow에 표시되는 채팅 어댑터 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 샌드박스화된 NVIDIA NemoClaw 설정 |
| [Docker](docs/DOCKER.md) | 이미지, compose, 볼륨 마운트 |
| [아키텍처](ARCHITECTURE.md) · [개발](docs/DEVELOPMENT.md) | 내부 동작 방식; 소스에서 실행하기 |
| [텔레메트리](docs/TELEMETRY.md) | 익명 설치 및 데스크톱 오픈 핑, 끄는 방법 |

## 스크린샷

아래 모든 숫자는 아무것도 시딩하지 않은, 읽기 전용의 실제 머신 하나에서
나온 것입니다.

**무엇이 잘못되었는지 알려줄 뿐만 아니라, 무슨 일이 있었는지도 알려줍니다.**
상단의 두 개의 이상치 배너: 지출이 일일 평균의 7배로 실행되고 있으며,
4.2배의 비용 급증. 그 아래에는, 최근 667개 세션 중 324개가 원인별로
항목화된 낭비 신호를 보이고 있습니다.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**돈이 어디로 갔는지 모든 시간 범위에서 보여줍니다.**
오늘 $252.47, 이번 주 $513.15, 이번 달 $1,312.92, 각각 그 뒤에 있는 토큰과
여러분의 구독이 이미 얼마나 커버하는지와 함께. 그 아래에는, 약 $1,128/월이
회수 가능한 것으로 항목화되어 있고 캐시 재사용으로 이미 $17,256/월이
절약되었습니다.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**메시지가 어떻게 답이 되는지를 그려줍니다.**
실시간 flow 다이어그램: 여러분, 메시지가 도착한 채널, 게이트웨이, 현재
답변 중인 모델, 그리고 그것이 사용한 모든 도구. 작업이 통과할 때마다 노드가
켜집니다.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**머신 위의 모든 에이전트를 하나의 표로.**
무엇을 실행하는지, 최근 24시간과 전체 기간의 비용, 마지막으로 확인된 시점,
소유자가 누구인지, 그리고 구독이 요금을 커버하고 있는지. 여기 14개의
에이전트, 3개의 세션이 작업 중, 13개는 조용합니다.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**한 턴의 시간과 비용이 어디로 갔는지 도구별로 보여줍니다.**
실제 세션의 한 턴: 11.2분 동안 11개의 도구, $1.16. 모든 Bash 호출과 모델
호출은 타임라인에 자신만의 바(bar)를 가지므로, 4.1분 동안 실행된 명령과
226ms 동안 실행된 명령을 한눈에 구별할 수 있습니다.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**지출뿐만 아니라 작업의 품질도 채점합니다.**
이번 주 A등급: 54개의 작업이 깨끗하게 완료되었고, 거친(rough) 2개는 $48.57의
비용이 들었으며, 판단하기에는 활동이 너무 적은 실행들은 승리로 계산되는
대신 등급에서 제외됩니다. 각각의 거친 실행은 자신의 트레이스로 링크됩니다.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**컨텍스트 윈도우가 왜 계속 차오르는지 보여줍니다.**
최근 턴에서 1M 토큰 윈도우 중 715K, 83.3%의 피크, 오버플로우가 아니라 모두
선제적으로(proactively) 발생한 4번의 압축(compaction), 그리고 그 뒤의 모든
턴의 사용률.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**어떤 설정도 없이 탐지가 작동합니다.**
내장 탐지기들은 설치와 함께 작동합니다: 에이전트가 조용해짐, 텔레메트리
피드 중단, 비용 급증, 토큰 버스트, 오류 증가, 오류 급증, 예산 임계값,
위협 시그니처 매치, 보안 도구 발견, 보안 태세 변화. 여러분만의 규칙은
그 위에 선택적으로 추가할 수 있습니다.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**위험한 호출을 보류하는 것은 옵트인이며, 꺼진 상태로 제공됩니다.**
재귀적 삭제, 강제 푸시, sudo, 시크릿, 패키지 설치, 아웃바운드 호출 각각은
켤 수 있는 규칙을 가집니다. 켜기 전까지 ClawMetry는 지켜보기만 하고
아무것도 바꾸지 않습니다. 하나를 켜면, 일치하는 호출은 여기서 (또는
여러분의 휴대폰에서) 승인이나 거부를 기다립니다.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

런타임별로 더 보기: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## 인정받은 성과

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star 히스토리

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 라이선스

MIT · [@vivekchand](https://github.com/vivekchand)가 제작 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
