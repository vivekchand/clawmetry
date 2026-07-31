<!-- i18n-src:02b789586c7d -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**당신의 에이전트가 생각하는 모습을 보세요.** **14개의 AI 에이전트 런타임**을 위한 실시간 관측 도구입니다: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 등 10개 이상. 당신의 전체 에이전트 플릿을 위한 하나의 대시보드.

> 🌐 **다른 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열리며, 그것으로 끝입니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14개의 에이전트 런타임과 함께 작동합니다

ClawMetry는 OpenClaw를 위한 관측 도구로 시작했고, 이제는 하나의 대시보드에서 사용자의 머신에 있는 각 런타임을 자동으로 감지하며 **전체 에이전트 플릿**을 계측합니다:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw와 NemoClaw는 오픈소스 앱에서 무료이며, 나머지 런타임들은 ClawMetry Cloud 또는 셀프 호스팅 Pro 라이선스로 활성화됩니다. 헤더에서 런타임을 전환하면 비용, 토큰, 도구, 트레이스 등 모든 탭이 해당 런타임에 맞게 다시 범위가 지정됩니다. 정확한 무료/유료 구분, 티어 매트릭스, `/api/entitlement` 형식, `clawmetry license` CLI에 대해서는 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** 를 참고하세요.

## 제공 기능

- **Flow** — 채널, 브레인, 도구를 통해 흐르는 메시지를 보여주는 실시간 애니메이션 다이어그램
- **Overview** — 상태 점검, 활동 히트맵, 세션 수, 모델 정보
- **Usage** — 일/주/월별 분석이 포함된 토큰 및 비용 추적
- **Sessions** — 모델, 토큰, 마지막 활동이 표시되는 활성 에이전트 세션
- **Crons** — 상태, 다음 실행 시각, 소요 시간이 표시되는 예약된 작업
- **Logs** — 색상으로 구분된 실시간 로그 스트리밍
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, 일일 노트 탐색
- **Transcripts** — 세션 기록을 읽기 위한 채팅 버블 UI
- **Alerts** — 예산 한도, 오류율 트리거, 에이전트 오프라인 감지; Slack, Discord, PagerDuty, Telegram, Email로 라우팅
- **Approvals** — 파괴적인 삭제, 강제 푸시, DB 변경, sudo, 패키지 설치, 네트워크 호출을 원클릭 승인 뒤에 게이트

## 스크린샷

### 🧠 Brain — 실시간 에이전트 이벤트 스트림
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — 토큰 사용량 및 세션 요약
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 실시간 도구 호출 피드
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 모델 및 세션별 비용 분석
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 워크스페이스 파일 탐색기
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 보안 상태 및 감사 로그
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 예산 한도, 오류율 트리거, Slack / Discord / PagerDuty / Email로의 웹훅
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 위험한 도구 호출을 수동 승인 뒤에 게이트; 정책 기반 보호 규칙
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code를 위한 실행 전 차단** — 하나의 명령어로 일치하는 도구 호출을
실행 *전에* 일시 정지시키고 사용자의 결정을 기다리는 PreToolUse 훅을
설치합니다 ([클라우드 푸시 알림](https://app.clawmetry.com/push)을 활성화하면
휴대폰에서 탭 한 번으로 처리 가능):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

거부(deny)는 해당 도구 호출 하나만 차단합니다. 에이전트는 세션을 유지하며
다른 방법을 시도할 수 있습니다. 휴대폰에서 승인하면 Claude Code 자체의
권한 프롬프트를 건너뜁니다(이미 답변했으므로). 일치하지 않는 도구는 약
40ms의 비용만 들며 Claude Code의 일반 권한 흐름으로 넘어갑니다. Claude
Code 자체가 사용자의 응답을 기다리고 있을 때도 휴대폰 푸시 알림을 받습니다
(`permission_prompt` / `idle_prompt` 알림).

## 설치

**원라이너(권장):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**소스에서:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 프론트엔드 개발

v2 React 앱은 `frontend/`에 있으며, Flask 서버가 v2가 활성화된 상태로
시작되면 `/v2`에서 제공됩니다.

개발 중에는 두 개의 터미널을 사용하세요:

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

`http://localhost:5173/v2/` 를 여세요. Vite는 `/api` 요청을
`http://localhost:8900` 으로 프록시하므로, React 앱은 별도의 CORS 설정 없이
로컬 Flask 서버와 통신할 수 있습니다.

Python 패키지와 함께 배포되는 번들을 빌드하려면:

```bash
cd frontend
npm run build
```

프로덕션 번들은 `clawmetry/static/v2/dist/` 에 작성됩니다.

## 런타임 / 에이전트 호환성

ClawMetry는 OpenClaw뿐만 아니라 여러 AI 에이전트 런타임을 관측합니다. OpenClaw가 아닌 각 런타임은 해당 런타임의 네이티브 세션 형식을 ClawMetry의 통합 형식으로 변환하는 전용 리더 어댑터를 제공합니다. 데몬은 이를 런타임으로 태그된 동일한 DuckDB 저장소 + 클라우드 스냅샷으로 수집하며, 세션 리플레이 탭은 둘 이상의 런타임이 존재할 때 **런타임 전환기**를 보여줍니다. 전체 매트릭스와 런타임 추가 가이드는 [`docs/compatibility.md`](docs/compatibility.md)를, OpenClaw 계열 개요는 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)를 참고하세요.

| 런타임 / 에이전트 | 상태 | 비고 |
|---|---|---|
| **OpenClaw** | Native | 기준 런타임, 자동 감지됨 |
| **PicoClaw** | Beta adapter | 평면 `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). 기록, 모델, 도구 호출. |
| **NanoClaw** | Beta adapter | 세션별 SQLite (`data/v2-sessions`). 기록 + 메시지 수. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. 기록, 모델, 토큰/비용. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. 기록, 모델, 도구 호출 + 사고 과정, 토큰 사용량. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. 기록, 모델, 도구 호출, 토큰 사용량. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. 채팅/컴포저 기록, 모델. |
| **Aider** | Beta adapter | 프로젝트별 `.aider.chat.history.md`. 기록, 모델, 토큰 수. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. 기록, 모델, 도구 호출, 토큰 총합. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. 기록, 모델, 도구 호출, 토큰 + 비용. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. 기록, 모델, 도구 호출, 토큰 사용량. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. 기록, 모델, 도구 호출, 토큰 + 비용. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. 기록, 모델, 도구 호출, 토큰 + 비용. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. 워크플로 실행, 노드 실행, AI Agent 프롬프트, n8n이 기록하는 경우 모델 + 토큰. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` 하위의 Brain JSONL. 대화, 도구 단계, 사고 과정, 생성별 Gemini 토큰 분할 + 비용, 백그라운드 생성 소모량. |

"Beta adapter"는 ClawMetry가 해당 런타임의 실제 디스크 형식을 위한 리더를 제공한다는 뜻이며, 각각 실제 머신의 실제 설치를 기준으로 빌드 및 검증되었습니다(`tests/fixtures/runtimes/<rt>/` 참고). 어댑터는 읽기 전용이며, 각각 자신의 런타임이 실제로 무엇을 저장하는지에 대해 정직합니다(예: PicoClaw/NanoClaw/Cursor는 토큰 비용을 디스크에 기록하지 않습니다). 한 노드에서 여러 런타임이 실행 중일 때, 런타임 전환기는 세션 뷰의 범위를 하나로 제한하여 깔끔한 심층 분석을 가능하게 합니다.

## 모든 SDK 에이전트 추적 — 아웃루프 비용 귀속

위의 런타임들은 모두 세션을 디스크에 기록합니다. OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, 또는 일반 `httpx` 루프로 만든 사용자의 **프로덕션 에이전트**는 그렇지 않습니다. ClawMetry의 제로 설정 인터셉터는 `httpx`/`requests`를 몽키패칭하여 여전히 해당 에이전트의 LLM 호출(비용, 토큰, 지연 시간, 오류)을 캡처합니다:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(또는 `CLAWMETRY_SOURCE=support-agent` 환경 변수)는 각 호출에 **명명된 소스**로 태그를 지정하므로, 실행하는 모든 제품이 대시보드의 Overview에 있는 **🔌 아웃루프 소스** 카드에서 독립적이고 비용 귀속이 가능한 항목으로 표시됩니다. 각 에이전트별 호출 수, 제공자, 지연 시간, 오류율까지 확인할 수 있습니다. 소스를 설정하지 않으면 호출은 여전히 추적되며, 해당 카드만 숨겨집니다.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

이는 런타임 어댑터가 공급하는 것과 동일한 데이터 레이어(DuckDB → 클라우드 스냅샷)이므로, 아웃루프 소스는 다른 모든 것과 마찬가지로 종단 간 암호화되어 클라우드 대시보드와 동기화됩니다.

## OpenTelemetry — 벤더 중립, 어디로든 트레이스 전송

ClawMetry는 **GenAI 시맨틱 컨벤션**을 사용하여 양방향으로 **OpenTelemetry**를 지원하므로, 사용자의 에이전트 트레이스가 하나의 도구에 종속되지 않습니다.

모든 세션(LLM 호출, 도구, 서브 에이전트, 토큰, 비용)을 OTLP/HTTP GenAI 스팬으로 **내보내기**하여 원하는 컬렉터(Datadog, Grafana, Honeycomb, 또는 자체 OTel Collector)로 전송할 수 있습니다:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

인증 헤더와 폴링 간격은 선택적 환경 변수입니다:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**수집(Ingest)** — 내장 OTLP 리시버는 `/v1/traces` 및 `/v1/metrics`에서 다른 어떤 곳으로부터든 트레이스와 메트릭을 수신합니다(프로토버프 수집을 위해서는 `pip install clawmetry[otel]`).

제로 설정, 로컬 우선 ClawMetry 대시보드와 **함께**, 사용자의 데이터를 팀이 이미 사용 중인 어떤 백엔드로든 보낼 수 있습니다. 종속 없음, 두 번째 에이전트 설치 필요 없음.

## 설정

대부분의 사용자는 별도의 설정이 필요하지 않습니다. ClawMetry는 워크스페이스, 로그, 세션, 크론을 자동으로 감지합니다.

커스터마이징이 필요하다면:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

모든 옵션: `clawmetry --help`

## 지원하는 채널

ClawMetry는 설정된 모든 OpenClaw 채널의 실시간 활동을 보여줍니다. `openclaw.json`에 실제로 설정된 채널만 Flow 다이어그램에 표시되며, 설정되지 않은 채널은 자동으로 숨겨집니다.

Flow에서 채널 노드를 클릭하면 수신/발신 메시지 수와 함께 실시간 채팅 버블 뷰를 볼 수 있습니다.

| 채널 | 상태 | 실시간 팝업 | 비고 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 완전 지원 | ✅ | 메시지, 통계, 10초 새로고침 |
| 💬 **iMessage** | ✅ 완전 지원 | ✅ | `~/Library/Messages/chat.db`를 직접 읽음 |
| 💚 **WhatsApp** | ✅ 완전 지원 | ✅ | WhatsApp Web(Baileys) 경유 |
| 🔵 **Signal** | ✅ 완전 지원 | ✅ | signal-cli 경유 |
| 🟣 **Discord** | ✅ 완전 지원 | ✅ | 길드 + 채널 감지 |
| 🟪 **Slack** | ✅ 완전 지원 | ✅ | 워크스페이스 + 채널 감지 |
| 🌐 **Webchat** | ✅ 완전 지원 | ✅ | 내장 웹 UI 세션 |
| 📡 **IRC** | ✅ 완전 지원 | ✅ | 터미널 스타일 버블 UI |
| 🍏 **BlueBubbles** | ✅ 완전 지원 | ✅ | BlueBubbles REST API를 통한 iMessage |
| 🔵 **Google Chat** | ✅ 완전 지원 | ✅ | Chat API 웹훅 경유 |
| 🟣 **MS Teams** | ✅ 완전 지원 | ✅ | Teams 봇 플러그인 경유 |
| 🔷 **Mattermost** | ✅ 완전 지원 | ✅ | 셀프 호스팅 팀 채팅 |
| 🟩 **Matrix** | ✅ 완전 지원 | ✅ | 탈중앙화, E2EE 지원 |
| 🟢 **LINE** | ✅ 완전 지원 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 완전 지원 | ✅ | 탈중앙화 NIP-04 DM |
| 🟣 **Twitch** | ✅ 완전 지원 | ✅ | IRC 연결을 통한 채팅 |
| 🔷 **Feishu/Lark** | ✅ 완전 지원 | ✅ | WebSocket 이벤트 구독 |
| 🔵 **Zalo** | ✅ 완전 지원 | ✅ | Zalo Bot API |

> **자동 감지:** ClawMetry는 `~/.openclaw/openclaw.json`을 읽어 실제로 설정된 채널만 렌더링합니다. 수동 설정이 필요하지 않습니다.

## Docker 배포

ClawMetry를 컨테이너에서 실행하고 싶으신가요? 문제 없습니다! 🐳

**Docker로 빠르게 시작하기:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose 예시:**

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

> **참고:** Docker에서 실행할 때는 ClawMetry가 사용자의 설정을 자동으로 감지할 수 있도록 에이전트의 데이터 + 로그 디렉토리(예: `~/.openclaw`, `~/.claude`, `~/.codex`)를 마운트하세요.

## 요구 사항

- Python 3.8 이상
- Flask(pip을 통해 자동으로 설치됨)
- 동일한 머신에서 실행 중인 AI 에이전트 런타임: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, 또는 Antigravity (Docker의 경우 마운트된 볼륨도 가능)
- Linux 또는 macOS

## NemoClaw / OpenShell 지원

ClawMetry는 샌드박스 처리된 OpenShell 컨테이너 내부에서 에이전트를 실행하는 NVIDIA의 엔터프라이즈 보안 래퍼인 [NemoClaw](https://github.com/NVIDIA/NemoClaw)를 자동으로 감지합니다.

대부분의 경우 별도의 설정이 필요하지 않습니다. 동기화 데몬은 세션 파일이 호스트의 `~/.openclaw/`에 있든 OpenShell 컨테이너 내부에 있든 자동으로 발견합니다.

### 작동 방식

ClawMetry는 다음 두 가지 방식으로 NemoClaw를 감지합니다:

1. **바이너리 감지** — `nemoclaw` CLI가 있는지 확인하고 `nemoclaw status`를 실행하여 샌드박스 정보를 가져옵니다
2. **컨테이너 감지** — 실행 중인 Docker 컨테이너에서 `openshell`, `nemoclaw`, 또는 `ghcr.io/nvidia/` 이미지를 스캔한 다음, 볼륨 마운트 또는 `docker cp`를 통해 세션을 읽습니다

NemoClaw 컨테이너에서 동기화된 세션 파일은 클라우드 대시보드에서 `runtime=nemoclaw` 및 `container_id` 메타데이터로 태그가 지정되므로, 한눈에 표준 OpenClaw 세션과 구별할 수 있습니다.

### 권장 설정: 호스트에서 실행되는 동기화 데몬

최상의 경험을 위해 ClawMetry의 동기화 데몬을 (샌드박스 내부가 아닌) **호스트 머신**에서 실행하세요. 이렇게 하면 NemoClaw 네트워크 정책 제한을 피할 수 있습니다.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

동기화 데몬은 실행 중인 모든 OpenShell 컨테이너 내부의 세션을 자동으로 찾습니다.

### 선택 사항: 명시적인 샌드박스 이름

자동 감지가 작동하지 않는 경우, ClawMetry가 올바른 샌드박스를 가리키도록 지정하세요:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 샌드박스 내부에서 실행하기(고급)

동기화 데몬을 OpenShell 샌드박스 **내부**에서 실행해야 하는 경우, ClawMetry ingest API에 접근할 수 있도록 NemoClaw 네트워크 정책에 다음 이그레스 규칙을 추가하세요:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

다음으로 적용하세요:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 포트 및 엔드포인트

| 엔드포인트 | 포트 | 프로토콜 | 필수 여부 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 예(동기화 데몬 → 클라우드) |
| `localhost:8900` | 8900 | HTTP | 예(로컬 대시보드 UI) |
| Docker 소켓 (`/var/run/docker.sock`) | — | Unix 소켓 | 컨테이너 세션 발견용 |

동기화 데몬은 `ingest.clawmetry.com`으로만 아웃바운드 HTTPS 호출을 합니다. 인바운드 포트는 필요하지 않습니다.

---

## 클라우드 배포

SSH 터널, 리버스 프록시, Docker에 대해서는 **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** 를 참고하세요.

## 테스트

이 프로젝트는 BrowserStack으로 테스트되었습니다.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 텔레메트리

ClawMetry는 `https://app.clawmetry.com/api/install`로 익명의 설치
생명주기 핑을 전송합니다: 새 머신에서 `clawmetry` CLI를 처음 실행할 때
`install` 핑 한 번, 새 버전으로 업그레이드한 후 첫 실행 시 `update` 핑
한 번, 대시보드 내 온보딩 선택을 완료할 때 `onboarded` 핑 한 번입니다.
이를 통해 실제 설치 수를 집계합니다(원시 PyPI 다운로드 수치는 약 98%가
미러, CI, 자동 업데이트 재다운로드입니다) 그리고 실제로 사용되고 있는
에이전트 프레임워크와 버전을 파악합니다.

**버전당 생명주기 이벤트마다 최대 한 번의 POST**가 전송되며, 다음을
포함합니다:

| 필드 | 예시 | 이유 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`에 저장된 무작위 UUID | 중복 제거; Cloud 동기화를 명시적으로 연결하기 전까지는 익명(그 이후 인증된 데몬 하트비트가 이를 포함하여 이 설치를 사용자 계정에 연결) |
| `event` | `install` / `update` / `onboarded` | 신규 설치인지 기존 설치의 업그레이드인지 |
| `version` | `0.12.167` | 실제로 사용 중인 버전 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 플랫폼 지원 우선순위 |
| `python` | `3.11.15` | Python 버전 지원 매트릭스 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 다음에 통합해야 할 에이전트 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 사람에 의한 설치와 CI 노이즈 구분 |

**전송하지 않는 것**: IP(클라우드는 요청에서 서버 측으로 국가 코드만
추출한 뒤 IP를 폐기), 호스트명, 사용자명, 워크스페이스 경로, 파일 내용,
사용자의 api_key, 이메일, 개인식별정보(PII) 또는 워크스페이스 관련
정보 일체. 전송 페이로드는
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)에서 확인할 수
있습니다.

**옵트아웃**(다음 중 하나라도 실행하면 영구적으로 비활성화됩니다):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

네트워크 실패가 `clawmetry` 실행을 막는 일은 없습니다. 핑은 3초
타임아웃을 가진 데몬 스레드에서 발생하며 결과를 기다리지 않습니다.

## 스타 히스토리

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 라이선스

MIT

---

<p align="center">
  <strong>🦞 당신의 에이전트가 생각하는 모습을 보세요</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
