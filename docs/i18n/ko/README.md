<!-- i18n-src:a855a14295b0 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**에이전트는 진전 없이도 수백 번의 도구 호출을 할 수 있습니다.** ClawMetry는
코딩 에이전트가 이미 작성하고 있는 세션 파일을 읽어서, 타임라인과
도구 호출, 그리고 런타임이 노출하는 토큰 및 비용 데이터를 하나의
화면에 모아줍니다 — 그래서 잘 진행되고 있는 긴 실행과 멈춰버린 실행을
구분할 수 있습니다.

**32개의 AI 에이전트 런타임**과 함께 작동합니다 — Claude Code, OpenAI Codex, Hermes, OpenClaw 외 28개. 여러분의 전체 에이전트 플릿을 위한 하나의 대시보드입니다. ([전체 목록](SUPPORTED_RUNTIMES.txt), 카탈로그로부터 생성됨.)

> 🌐 **다음 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열립니다. 설정이 필요 없습니다: 이미 가지고 있는 에이전트
런타임을 찾아서, 읽기 전용으로 읽고, 실행 방식에는 아무것도 바꾸지 않습니다.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 설치하기 전에

| | |
|---|---|
| **하는 일** | 에이전트가 이미 작성하고 있는 세션 파일과 로그를 읽습니다. SDK도, 코드 변경도, 앱 내 계측도 필요 없습니다. |
| **보이는 것** | 세션 타임라인, 도구별 리플레이, 토큰 및 비용 분석, 그리고 궤적 신호(반복 루프, 반복되는 실패) — 런타임별로 제공됩니다. |
| **무료 범위** | `pip install clawmetry`는 계정도, 키도, 네트워크 호출도 없이 **OpenClaw, NVIDIA NemoClaw, Goose**를 읽습니다. 나머지 27개 — Claude Code, Codex, Cursor 등 — 는 클로즈드 소스인 `clawmetry-pro` 컴패니언이 읽으며, 이는 7일 체험판 또는 플랜과 함께 제공됩니다 — 정확한 구분은 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)를 참고하세요. |
| **시작 방법** | `pip install clawmetry && clawmetry` 실행 후 localhost:8900을 엽니다. 아직 이 머신에 에이전트가 없다면? `clawmetry --sample`을 실행하면 레이블이 붙은 세 개의 합성 세션으로 열립니다. |
| **머신 밖으로 나가는 것** | `clawmetry connect`를 실행하지 않는 한 세션 데이터는 나가지 않습니다. 기본적으로 실행되는 것은 두 가지뿐이며, 둘 다 옵트아웃 가능하고 세션 내용을 포함하지 않습니다: 익명 설치 핑과 PyPI 버전 확인입니다. 모든 목적지는 주석이 아니라 실제 와이어 캡처로부터 재구성되어 [docs/EGRESS.md](docs/EGRESS.md)에 정리되어 있습니다. |

판단하기 전에 알아둘 만한 두 가지 한계가 있습니다: 런타임마다 노출하는 데이터가
크게 다르고(일부는 비용을 전혀 공개하지 않습니다 — 어떤 런타임이 그런지는
[호환성 매트릭스](docs/compatibility.md)를 참고하세요), 어떤 동작을 관찰하는 것과
그것을 실제로 막을 수 있는 것은 별개입니다 ([런타임별로 어떤 제어가 실제로 동작하는지](docs/APPROVALS.md)).


## 32개의 에이전트 런타임과 함께 작동합니다

**오픈소스 앱에서 무료:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**유료 플랜에서:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

모든 런타임은 동일한 대시보드를 제공받습니다. 여러 개를 동시에 실행하면
헤더의 스위처가 모든 탭의 범위를 그중 하나로 재설정합니다.

SDK로 직접 만든 자체 에이전트가 있나요? 인터셉터는 그 LLM 호출도
추적합니다. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)를 참고하세요.

## 제공하는 기능

- **세션 및 트랜스크립트**: 각 에이전트가 턴별로 무엇을 했는지, 리플레이와 함께
- **비용 및 토큰**: 런타임, 모델, 세션, 일자별로, 이상 징후 플래그와 함께
- **Flow**: 채널, 모델, 도구를 오가는 메시지의 실시간 다이어그램
- **Brain**: 실시간으로 발생하는 추론 및 도구 호출 이벤트 스트림
- **컨텍스트 폭발**: 공급자별로 사이즈가 조정된 윈도우 사용률, 압축 대 강제 오버플로우, 그리고 우리가 *볼 수 없는* 부분을 런타임별로 정리한 지도 ([방법](docs/CONTEXT_BLOWOUT.md))
- **메모리 및 스킬**: 각 런타임이 실제로 로드한 파일과 스킬
- **상태 및 로그**: 디스크, 메모리, 오류율, 속도 제한, 실시간 로그 스트림
- **알림**: 예산 상한선, 오류 급증, 에이전트 오프라인, Slack, Discord, PagerDuty, Telegram, 이메일로 라우팅
- **승인**: 위험한 도구 호출을 실행 *전에* 일시 정지하고 휴대폰에서 승인 ([방법](docs/APPROVALS.md))

## 컨텍스트 폭발, 그리고 관찰 비용

어떤 에이전트 비교 도구든 신뢰하기 전에 답해볼 만한 두 가지 질문이 있습니다.

**런타임 전반에서 컨텍스트 윈도우 폭발을 어떻게 처리하나요?**

사용률 퍼센트는 그것이 나누는 분모만큼만 정직합니다. ClawMetry는
[여러분이 읽고 PR할 수 있는 테이블](clawmetry/context_windows.py)을 기준으로
공급자별 윈도우 크기를 산정하며, 여기에는 Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama, GLM이 포함됩니다. 32개의 모든
런타임을 한 벤더의 자로 측정하지 않습니다. 이는 중요합니다: 30만
토큰짜리 GPT-5 턴을 Anthropic의 20만 토큰 기준으로 채점하면
">100%, 폭발"로 읽히지만, 실제로는 GPT-5의 40만 토큰 기준으로 75%에
불과합니다. 같은 자를 쓰면 실제로 오버플로우된 13만 토큰짜리 DeepSeek
턴이 편안한 65%로 숨겨지기도 합니다.

모든 윈도우는 출처와 함께 제공됩니다: `model_table`, `explicit_marker`,
`observed_floor`, 또는 모델을 모를 때의 정직한 `default`입니다. 추측으로
만들어진 게이지는 조회로 만들어진 게이지와 같은 권위를 가지고 표시되지
않습니다.

ClawMetry는 일부 런타임에서만 압축 이벤트를 볼 수 있습니다. 그래서
`GET /api/context-coverage`는 런타임별로 **0이 "정상 실행"을 의미하는지
"보이지 않음"을 의미하는지**를 보고합니다. 실제로는 보이지 않는다는
뜻의 `0`은 그렇다고 밝힙니다.
[전체 내용](docs/CONTEXT_BLOWOUT.md)

**계측 비용은 얼마인가요?**

| 경로 | 에이전트에 추가되는 비용 | 기본값? |
|---|---|---|
| 세션 파일 테일링 (32개 런타임 전체) | **0**. 별도 프로세스이며, 에이전트 안에는 ClawMetry 코드가 없음 | 켜짐 |
| HTTP 인터셉터 (`CLAWMETRY_INTERCEPT=1`) | LLM 호출당 **+0.44ms**, 5초짜리 호출 기준 0.009% | 꺼짐 |
| 사전 도구 훅 게이트 (웜 캐시) | 게이트가 걸린 도구 호출당 **+44ms**, 36ms의 인터프리터 기준선 위에 | 꺼짐 |
| 강제 프록시 | LLM 호출당 **+9.7ms** | 꺼짐 |

데몬 호스트 비용: 수집 **초당 2,762건 이벤트**, 디스크상 **이벤트당
710바이트** (10만 건당 67.7MB), 그리고 활발한 설치 환경에서 지속적으로
**코어 하나의 약 12%**. 이 마지막 수치는 우리가 밝힌 5-10% 예산을
초과하므로, 페이지에서 빼는 대신 추적해야 할 버그로 게시합니다.

Apple M2 Pro에서 `benchmarks/overhead.py`로 측정했습니다. 이 하니스는
각 조건을 별도의 프로세스에서 실행하고, 순서를 번갈아 바꾸며,
**라운드끼리 부호가 일치하지 않으면 숫자를 출력하지 않습니다**. 여러분의
머신에서 1분 안에 직접 실행해 보세요:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

훅 게이트와 강제 프록시를 포함한 모든 경로가 측정되며, 이 하니스는
CI에서 Linux, macOS, Windows에서 실행됩니다. 알아둘 만한 결과 두 가지:
프록시는 Windows에서 Linux보다 약 7배 더 비용이 들고, 데몬은 현재
코어 하나의 약 12%를 지속적으로 사용하여 우리 자체의 5-10% 예산을
초과합니다. 원본 JSON, 방법론, 그리고 아직 측정되지 않은 부분은
[docs/OVERHEAD.md](docs/OVERHEAD.md)에 있습니다.

## 가격 정책

| 플랜 | 포함 범위 | 가격 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, 전체 대시보드, 로컬 전용 | $0 |
| **Starter** | 위의 다른 모든 런타임, 플릿 뷰, 클라우드 동기화 | 노드당 월 $9 |
| **Pro** | Starter + 제어 및 평가: 승인, 도구 위험 정책, 평가, 이상 탐지, 비용 최적화 도구, OTel 내보내기, 변조 방지 감사 로그 | 노드당 월 $19 |

연간 플랜, Enterprise 및 최신 가격은
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**에 있습니다. 자체 호스팅
라이선스 키는 클라우드 없이도 작동합니다 (`clawmetry license`). 정확한
무료/유료 구분은 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)에 있습니다.

## 여러분의 데이터는 여러분의 머신에 머무릅니다

ClawMetry는 로컬 세션 파일과 로그를 읽습니다. **`clawmetry connect`를 실행하지
않는 한 세션 데이터는 여러분의 머신을 벗어나지 않습니다** — 프롬프트, 응답,
도구 인자, 파일 내용, 로그 줄 어느 것도 마찬가지입니다. 연결할 경우, 스냅샷은
여러분의 머신을 벗어나지 않는 키로 종단 간 암호화되며, 브라우저에서 복호화됩니다.
노드에 키가 없으면 업로드는 평문으로 전송되지 않고 건너뛰어지며, 어떤 서버
응답도 이를 끌 수 없습니다.

연결하기 전에도 기본적으로 실행되는 두 가지가 있으며, 둘 다 옵트아웃 가능하고
세션 데이터를 포함하지 않습니다: 익명 설치 핑과 PyPI 버전 확인입니다. 기본
설치는 또한 시작 배너 줄을 위해 공용 IP를 한 번 조회합니다. 모든 목적지와
그것이 담는 내용, 끄는 방법은 [docs/EGRESS.md](docs/EGRESS.md)에 정리되어 있습니다;
자체 호스팅, 재지정, 에어갭 설치는 어떠한 임의의 아웃바운드 호출도 만들지
않습니다.

복호화는 우리가 제공하는 코드 안에서, 여러분의 브라우저에서 일어납니다.
예전에는 이것이 하나의 약속이었지만, 이제는 직접 확인할 수 있는 것입니다.
여러분의 키를 다루는 모든 줄은 하나의 읽기 쉬운 파일
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)에 있으며,
휠 안에 포함되어 그대로 제공되고, Subresource Integrity 해시로 고정됩니다.
브라우저가 우리가 게시한 것을 실행하는지 확인하려면:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

이것이 증명하지 못하는 것: 우리는 이 파일을 로드하는 페이지도 제공하므로,
다른 페이지를 제공할 수도 있습니다. 무결성 해시는 손상된 CDN으로부터는
여러분을 보호하지만, 벤더 자체로부터는 보호하지 못합니다. 여러분이
얻는 것은, 어떤 대체든 의도적이어야 하고, 페이지 소스에서 눈에 보여야
하며, 누구나 가져올 수 있는 PyPI상의 아티팩트와 달라야 한다는 점입니다.
자체 호스팅이나 로컬 전용 사용은 이 의존성을 완전히 제거합니다.

## 설치

```bash
pip install clawmetry     # 그다음: clawmetry
```

또는 원라이너: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows에서 Python 3.8 이상이 필요하며, 같은 머신에 적어도
하나의 에이전트 런타임이 있어야 합니다. Docker 안내: [docs/DOCKER.md](docs/DOCKER.md).

또는 에이전트가 대신 설정하게 할 수도 있습니다. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
스킬은 Claude Code, Codex, Cursor, Gemini CLI, Copilot 또는 OpenCode에게
ClawMetry를 설치하고, 머신 위의 에이전트들이 무엇을 하고 얼마를 쓰고 있는지
보고하고, 요청 시 세션 하나를 중단하고, 위험한 도구 호출을 승인 대기 상태로
붙잡아 두는 방법을 가르칩니다:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 문서

| | |
|---|---|
| [런타임 호환성](docs/compatibility.md) | 각 어댑터가 읽는 것, 그리고 런타임을 추가하는 방법 |
| [컨텍스트 폭발](docs/CONTEXT_BLOWOUT.md) | 공급자별 윈도우, 압축 대 오버플로우, 런타임별 커버리지 |
| [오버헤드](docs/OVERHEAD.md) | 계측 비용, 측정치, 재현 가능한 하니스 |
| [Entitlements](docs/ENTITLEMENTS.md) | 무료 대 유료, 티어 매트릭스, 라이선스 CLI |
| [승인 및 정책](docs/APPROVALS.md) | 실행 전 게이팅, 위험 점수화, 휴대폰 승인 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 어디로든 트레이스 내보내기, 어디서든 OTLP 수집 |
| [자체 에이전트 연결하기](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain 전체 과정, 실행 가능한 예제와 함께 |
| [SDK 추적](docs/SDK_TRACKING.md) | 직접 만든 에이전트에 대한 비용 귀속 |
| [채팅 채널](docs/CHANNELS.md) | Flow에 표시되는 채팅 어댑터들 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 샌드박스화된 NVIDIA NemoClaw 설정 |
| [Docker](docs/DOCKER.md) | 이미지, 컴포즈, 볼륨 마운트 |
| [아키텍처](ARCHITECTURE.md) · [개발](docs/DEVELOPMENT.md) | 내부 동작 방식; 소스에서 실행하기 |
| [텔레메트리](docs/TELEMETRY.md) | 익명 설치 및 데스크톱 열림 핑, 그리고 끄는 방법 |

## 스크린샷

아래의 모든 수치는 실제 머신 한 대에서, 읽기 전용으로, 아무것도 미리 심지 않고
얻은 것입니다.

**무언가 잘못되었을 때 알려줍니다, 단순히 무슨 일이 있었는지가 아니라.**
상단에 두 개의 이상 징후 배너: 일일 평균의 7배에 달하는 지출, 그리고
4.2배의 비용 급증. 그 아래로, 최근 세션 667개 중 324개가 낭비 신호를
띠고 있으며, 원인별로 항목화되어 있습니다.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**돈이 어디로 갔는지 모든 시간대에서 보여줍니다.**
오늘 $252.47, 이번 주 $513.15, 이번 달 $1,312.92, 각각 그 뒤에 있는
토큰과 여러분의 구독이 이미 커버하는 비율과 함께. 그 아래로, 회수 가능한
비용으로 항목화된 약 $1,128/월과 캐시 재사용으로 이미 절약된 $17,256/월.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**메시지가 어떻게 답변이 되는지 그려줍니다.**
실시간 흐름 다이어그램: 여러분, 메시지가 도착한 채널, 게이트웨이, 지금
답변하고 있는 모델, 그리고 그것이 사용한 모든 도구. 작업이 진행됨에 따라
노드가 밝아집니다.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**머신 위의 모든 에이전트를 하나의 표로.**
무엇을 실행하는지, 지난 24시간과 전체 기간 동안 얼마를 썼는지, 마지막으로
언제 목격되었는지, 누가 소유하는지, 구독이 요금을 커버하고 있는지. 여기
14개의 에이전트, 3개의 세션이 작업 중, 13개는 조용함.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**한 턴의 시간과 비용이 도구별로 어디에 쓰였는지 보여줍니다.**
실제 세션의 한 턴: 11.2분 동안 11개의 도구, $1.16. 모든 Bash 호출과
모델 호출은 타임라인에서 각자의 막대를 가지므로, 4.1분 동안 실행된
명령과 226ms 동안 실행된 명령을 한눈에 구별할 수 있습니다.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**지출뿐 아니라 작업 자체를 채점합니다.**
이번 주 A 등급: 54개의 작업이 깔끔하게 마무리되었고, 거친 작업 2개가
$48.57의 비용이 들었으며, 판단하기에 활동이 너무 적은 실행들은 승리로
집계되는 대신 등급에서 제외됩니다. 각 거친 실행은 자신의 트레이스로
연결됩니다.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**컨텍스트 윈도우가 왜 계속 차오르는지 보여줍니다.**
최신 턴에서 100만 토큰 윈도우 중 71만 5천 토큰 사용, 83.3%의 피크,
전부 오버플로우가 아니라 선제적으로 발동한 4번의 압축, 그리고 그
뒤에 있는 모든 턴의 사용률.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**여러분이 아무것도 설정하지 않아도 탐지가 작동합니다.**
내장 탐지기는 설치 시점부터 켜져 있습니다: 에이전트 무응답, 텔레메트리
피드 중단, 비용 급증, 토큰 버스트, 오류 증가, 오류 급증, 예산 임계값,
위협 시그니처 일치, 보안 도구 발견, 보안 태세 변경. 여러분만의 규칙은
그 위에 선택적으로 추가할 수 있습니다.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**위험한 호출을 붙잡아 두는 것은 옵트인이며, 꺼진 채로 출시됩니다.**
재귀적 삭제, 강제 푸시, sudo, 시크릿, 패키지 설치, 아웃바운드 호출은
각각 켤 수 있는 규칙을 가집니다. 켜기 전까지 ClawMetry는 지켜보기만
하고 아무것도 바꾸지 않습니다. 하나를 켜면, 일치하는 호출은 여기서
(또는 여러분의 휴대폰에서) 승인 또는 거부를 기다립니다.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

런타임별로 더 많은 스크린샷: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## 인정받은 기록

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

MIT · [@vivekchand](https://github.com/vivekchand) 제작 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
