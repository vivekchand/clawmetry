<!-- i18n-src:88be2deff5d5 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**당신의 에이전트가 생각하는 모습을 보세요.** **30개의 AI 에이전트 런타임**을 위한 실시간 관측 도구입니다: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 그리고 26개 이상의 런타임. 여러분의 에이전트 함대 전체를 위한 하나의 대시보드입니다.

> 🌐 **다음 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 제로. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열립니다. 설정이 필요 없습니다: 이미 갖고 있는 에이전트 런타임을 찾아내어 읽기 전용으로 읽어들이며, 그 실행 방식에는 아무 변화도 주지 않습니다.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30개의 에이전트 런타임과 함께 작동합니다

**오픈소스 앱에서 무료:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**유료 플랜에서:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

모든 런타임은 동일한 대시보드를 사용합니다. 여러 개를 동시에 실행하면 헤더의 전환기가 모든 탭의 범위를 그중 하나로 다시 맞춰줍니다.

여러분의 에이전트를 직접 SDK로 만들었나요? 인터셉터가 그 LLM 호출도 함께 추적합니다. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)를 참고하세요.

## 얻을 수 있는 것

- **세션 및 트랜스크립트**: 각 에이전트가 턴 단위로 무엇을 했는지, 리플레이와 함께
- **비용 및 토큰**: 런타임, 모델, 세션, 일자별로, 이상 징후 플래그와 함께
- **Flow**: 채널, 모델, 도구를 오가는 메시지의 실시간 다이어그램
- **Brain**: 실시간으로 벌어지는 추론 및 도구 호출 이벤트 스트림
- **컨텍스트 블로우아웃**: 프로바이더별로 산정된 윈도우 활용률, 압축(compaction) 대 강제 오버플로우, 그리고 런타임별로 우리가 *볼 수 없는* 부분에 대한 지도 ([방법](docs/CONTEXT_BLOWOUT.md))
- **메모리 및 스킬**: 각 런타임이 실제로 로드한 파일과 스킬
- **상태(Health) 및 로그**: 디스크, 메모리, 에러율, 요청 제한(rate limit), 실시간 로그 스트림
- **알림**: 예산 상한, 에러 급증, 에이전트 오프라인 감지, Slack·Discord·PagerDuty·Telegram·이메일로 라우팅
- **승인(Approvals)**: 위험한 도구 호출을 실행 *전에* 일시 정지시키고, 휴대폰에서 승인 ([방법](docs/APPROVALS.md))

## 컨텍스트 블로우아웃, 그리고 관측의 비용

어떤 에이전트 비교 도구든 신뢰하기 전에 답해볼 만한 두 가지 질문이 있습니다.

**런타임 전반에 걸친 컨텍스트 윈도우 블로우아웃을 어떻게 처리하는가?**

활용률(utilization) 퍼센트는 그것이 나누는 분모가 정직한 만큼만 정직합니다. ClawMetry는 [읽고 PR할 수 있는 테이블](clawmetry/context_windows.py)을 바탕으로 프로바이더별로 윈도우 크기를 산정하며, 이 테이블은 Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM을 포함합니다. 즉 30개 런타임 전부를 한 벤더의 잣대로 재지 않습니다. 이는 중요한 차이입니다: 300K 토큰짜리 GPT-5 턴을 Anthropic의 200K 기준으로 채점하면 "100% 초과, 터짐"으로 읽히지만, 실제로는 GPT-5의 400K 기준으로 75%에 불과합니다. 같은 잣대는 실제로 오버플로우된 130K DeepSeek 턴을 편안한 65%로 숨겨버리기도 합니다.

모든 윈도우는 그 출처(provenance)와 함께 제공됩니다: `model_table`, `explicit_marker`, `observed_floor`, 또는 모델을 알 수 없을 때의 정직한 `default`. 추측 위에 세워진 게이지는 조회(lookup) 위에 세워진 게이지와 결코 같은 권위로 표시되지 않습니다.

ClawMetry는 일부 런타임에서만 압축(compaction) 이벤트를 볼 수 있습니다. 그래서 `GET /api/context-coverage`는 런타임별로 **0이 "깨끗하게 실행됨"을 의미하는지, "우리가 보지 못하는 것"을 의미하는지**를 보고합니다. 보지 못함을 의미하는 `0`은 그렇다고 명시됩니다.
[상세 내용](docs/CONTEXT_BLOWOUT.md)

**계측(instrumentation)의 비용은 얼마인가?**

| 경로 | 여러분의 에이전트에 추가되는 비용 | 기본값? |
|---|---|---|
| 세션 파일 테일링 (30개 런타임 전체) | **0**. 별도 프로세스이며, 여러분의 에이전트 안에 ClawMetry 코드가 들어가지 않음 | 켜짐 |
| HTTP 인터셉터 (`CLAWMETRY_INTERCEPT=1`) | LLM 호출당 **+0.44 ms**, 5초짜리 호출의 0.009% | 꺼짐 |
| 사전 도구(pre-tool) 훅 게이트 (웜 캐시) | 게이트된 도구 호출당 **+44 ms**, 36 ms의 인터프리터 기본 지연 위에 추가 | 꺼짐 |
| 강제(enforcement) 프록시 | LLM 호출당 **+9.7 ms** | 꺼짐 |

데몬 호스트 비용: 수집(ingest) **초당 2,762건**, 디스크에 **이벤트당 710바이트** (이벤트 10만 건당 67.7 MB), 그리고 사용량이 많은 설치 환경에서 지속적으로 **코어 1개의 약 12%**. 마지막 수치는 우리가 스스로 밝힌 5~10% 예산을 초과하는 값이므로, 숨기지 않고 뒤쫓아야 할 버그로 공개해둡니다.

Apple M2 Pro에서 `benchmarks/overhead.py`로 측정되었습니다. 이 하니스는 각 조건을 별도의 프로세스에서 실행하고, 순서를 번갈아 바꾸며, **라운드 간 부호(sign)가 일치하지 않으면 수치 출력을 거부**합니다. 여러분 자신의 머신에서 1분 안에 실행해볼 수 있습니다.

```bash
pip install clawmetry && python -m benchmarks.overhead
```

훅 게이트와 강제 프록시를 포함해 모든 경로가 측정되며, 이 하니스는 CI에서 Linux, macOS, Windows 상에서 실행됩니다. 알아둘 만한 두 가지 결과: 이 프록시는 Windows에서 Linux보다 약 일곱 배 더 비용이 들며, 데몬은 현재 코어 1개의 약 12%를 지속적으로 사용하는데 이는 우리가 밝힌 5~10% 예산을 초과합니다. 원본 JSON, 방법론, 그리고 아직 측정되지 않은 부분은 [docs/OVERHEAD.md](docs/OVERHEAD.md)에 있습니다.

## 가격

| 플랜 | 포함 범위 | 가격 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, 전체 대시보드, 로컬 전용 | $0 |
| **Starter** | 위의 다른 모든 런타임, 함대(fleet) 뷰, 클라우드 동기화 | 노드당 월 $9 |
| **Pro** | Starter + 제어 및 평가: 승인, 도구 위험 정책, 평가(evals), 이상 징후 감지, 비용 최적화, OTel 내보내기, 변조 방지 감사 로그 | 노드당 월 $19 |

연간 플랜, Enterprise, 최신 가격 정보는 **[clawmetry.com/pricing](https://clawmetry.com/pricing)**에 있습니다. 자체 호스팅 라이선스 키는 클라우드 없이도 동작합니다 (`clawmetry license`). 정확한 무료/유료 구분은 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)에 있습니다.

## 여러분의 데이터는 여러분의 머신에 머뭅니다

ClawMetry는 로컬 세션 파일과 로그를 읽습니다. **`clawmetry connect`를 실행하지 않는 한 어떤 세션 데이터도 여러분의 머신을 벗어나지 않습니다** — 프롬프트, 응답, 도구 인자, 파일 내용, 로그 라인 그 어느 것도요. 연결(connect)할 경우, 스냅샷은 여러분의 머신을 벗어나지 않는 키로 종단간 암호화(end-to-end encrypted)되며, 브라우저에서 복호화됩니다. 노드에 키가 없으면 업로드는 평문으로 전송되는 대신 건너뛰어지며, 어떤 서버 응답도 이를 끌 수 없습니다.

연결하기 전에도 기본적으로 실행되는 두 가지가 있는데, 둘 다 옵트아웃 가능하며 세션 데이터를 담지 않습니다: 익명 설치 핑과 PyPI 대비 버전 확인입니다. 기본 설치는 또한 시작 배너 문구를 위해 여러분의 공인 IP를 한 번 조회합니다. 모든 목적지, 그것이 담는 내용, 끄는 방법은 [docs/EGRESS.md](docs/EGRESS.md)에 나열되어 있습니다. 자체 호스팅, 재지정(repointed), 에어갭 설치는 아무런 임의적 아웃바운드 호출도 만들지 않습니다.

복호화는 여러분에게 전달하는 코드로, 여러분의 브라우저 안에서 이루어집니다. 예전에는 이것이 하나의 약속이었지만, 이제는 확인 가능한 사실입니다. 여러분의 키에 닿는 모든 줄은 하나의 읽기 쉬운 파일 [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)에 들어 있으며, 이는 wheel 안에 담겨 그대로 제공되고 Subresource Integrity 해시로 고정됩니다. 브라우저가 우리가 배포한 것과 동일한 것을 실행하는지 확인하려면:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

이것이 증명하지 못하는 것: 우리는 이 파일을 불러오는 페이지 자체를 서빙하므로, 다른 페이지를 서빙할 수도 있습니다. 무결성 해시는 손상된 CDN으로부터는 여러분을 보호하지만, 벤더 자신으로부터는 보호하지 못합니다. 여러분이 얻는 것은, 어떤 치환이든 의도적이어야 하고, 페이지 소스에서 드러나야 하며, 누구나 가져올 수 있는 PyPI 상의 아티팩트와는 달라야 한다는 점입니다. 자체 호스팅하거나 로컬 전용으로 머무르면 이 의존성 자체가 사라집니다.

## 설치

```bash
pip install clawmetry     # 그다음: clawmetry
```

또는 원라이너: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows 어디서든 Python 3.8 이상이 필요하며, 같은 머신에 최소 하나의 에이전트 런타임이 있어야 합니다. Docker 안내: [docs/DOCKER.md](docs/DOCKER.md).

혹은 에이전트에게 설치를 맡기세요. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) 스킬은 Claude Code, Codex, Cursor, Gemini CLI, Copilot 또는 OpenCode에게 ClawMetry를 설치하고, 머신 위 에이전트들이 무엇을 하고 얼마를 쓰고 있는지 보고하고, 요청 시 세션 하나를 중지시키고, 위험한 도구 호출을 승인 대기 상태로 붙잡아두는 법을 가르쳐줍니다:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 문서

| | |
|---|---|
| [런타임 호환성](docs/compatibility.md) | 각 어댑터가 무엇을 읽는지, 그리고 런타임을 추가하는 방법 |
| [컨텍스트 블로우아웃](docs/CONTEXT_BLOWOUT.md) | 프로바이더별 윈도우, 압축 대 오버플로우, 런타임별 커버리지 |
| [오버헤드](docs/OVERHEAD.md) | 계측 비용, 실측치, 재현용 하니스 |
| [엔타이틀먼트](docs/ENTITLEMENTS.md) | 무료 대 유료, 티어 매트릭스, 라이선스 CLI |
| [승인 및 정책](docs/APPROVALS.md) | 실행 전 게이팅, 위험도 채점, 휴대폰 승인 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 어디로든 트레이스 내보내기, 무엇에서든 OTLP 수집 |
| [나만의 에이전트 붙이기](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain 전 과정, 실행 가능한 예제 포함 |
| [SDK 추적](docs/SDK_TRACKING.md) | 직접 만든 에이전트에 대한 비용 귀속 |
| [채팅 채널](docs/CHANNELS.md) | Flow에 표시되는 채팅 어댑터들 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 샌드박스화된 NVIDIA NemoClaw 설정 |
| [Docker](docs/DOCKER.md) | 이미지, compose, 볼륨 마운트 |
| [아키텍처](ARCHITECTURE.md) · [개발](docs/DEVELOPMENT.md) | 내부 동작 방식; 소스에서 실행하기 |
| [텔레메트리](docs/TELEMETRY.md) | 익명 설치 및 데스크톱 오픈 핑, 그리고 끄는 방법 |

## 스크린샷

아래의 모든 수치는 실제 하나의 머신에서, 읽기 전용으로, 아무것도 미리 심어두지 않은 상태로 얻은 것입니다.

**문제가 생겼을 때 알려줄 뿐 아니라, 단순히 무슨 일이 일어났는지만 알려주는 게 아닙니다.**
상단에 두 개의 이상 징후 배너: 일평균 대비 7배로 치솟은 지출, 그리고 4.2배의 비용 급증. 그 아래로, 최근 세션 667건 중 324건이 낭비 신호를 담고 있으며 원인별로 항목화되어 있습니다.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**돈이 어디로 갔는지를 모든 기간 창(window)에서 보여줍니다.**
오늘 $252.47, 이번 주 $513.15, 이번 달 $1,312.92, 각각 그 뒤의 토큰 수와 여러분의 구독이 이미 얼마나 커버하고 있는지와 함께. 그 아래로, 회수 가능하다고 항목화된 월 약 $1,128와 캐시 재사용으로 이미 절약된 월 $17,256.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**메시지가 어떻게 답변이 되는지를 그려 보여줍니다.**
실시간 flow 다이어그램: 여러분, 메시지가 도착한 채널, 게이트웨이, 지금 응답 중인 모델, 그리고 그것이 사용한 모든 도구. 작업이 흘러갈 때마다 노드들이 밝아집니다.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**머신 위의 모든 에이전트를, 하나의 표로.**
무엇을 실행 중인지, 지난 24시간과 전체 기간 동안 얼마의 비용이 들었는지, 마지막으로 언제 보였는지, 누구 소유인지, 구독이 그 비용을 감당하고 있는지. 여기 14개의 에이전트, 3개 세션이 작업 중, 13개는 조용합니다.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**한 턴의 시간과 비용이 어디로 갔는지를 도구별로 보여줍니다.**
실제 세션의 한 턴: 11.2분 동안 11개의 도구를 사용해 $1.16. Bash 호출과 모델 호출 각각이 타임라인 위에 자신만의 막대를 가지므로, 4.1분 동안 실행된 명령과 226ms 동안 실행된 명령이 한눈에 구분됩니다.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**지출뿐 아니라 작업 자체를 채점합니다.**
이번 주 A등급: 54개의 작업이 깔끔하게 끝났고, 거친 2건은 $48.57의 비용이 들었으며, 판단하기에 활동량이 너무 적은 실행들은 성공으로 집계되는 대신 채점에서 제외되었습니다. 각 거친 실행은 자신의 트레이스로 연결됩니다.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**컨텍스트 윈도우가 계속 차오르는 이유를 보여줍니다.**
1M 토큰 윈도우 중 최근 턴에서 715K, 83.3%의 피크, 오버플로우가 아니라 모두 선제적으로 발동된 4번의 압축(compaction), 그리고 그 뒤에 있는 모든 턴의 활용률.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**여러분이 아무것도 설정하지 않아도 감지는 작동합니다.**
내장 감지기들은 설치 즉시 켜져 있습니다: 에이전트 무응답, 텔레메트리 피드 중단, 비용 급증, 토큰 폭증, 상승하는 에러, 에러 급증, 예산 임계치, 위협 시그니처 일치, 보안 도구 발견 사항, 보안 태세 변화. 여러분 자신의 규칙은 그 위에 선택적으로 추가할 수 있습니다.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**위험한 호출을 붙잡아두는 것은 옵트인이며, 꺼진 채로 출시됩니다.**
재귀적 삭제, 강제 푸시(force push), sudo, 시크릿, 패키지 설치, 아웃바운드 호출 각각에 켤 수 있는 규칙이 있습니다. 켜기 전까지 ClawMetry는 지켜볼 뿐 아무것도 바꾸지 않습니다. 하나를 켜면, 일치하는 호출은 여기서 (또는 휴대폰에서) 승인 또는 거부를 기다립니다.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

런타임별로 더 많은 스크린샷: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 라이선스

MIT · [@vivekchand](https://github.com/vivekchand)가 만듦 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
