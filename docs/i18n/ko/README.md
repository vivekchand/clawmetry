<!-- i18n-src:c422fb7dd0da -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**여러분의 에이전트가 생각하는 모습을 직접 확인하세요.** **20개 AI 에이전트 런타임**을 위한 실시간 관측 도구입니다: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 외 16개. 전체 에이전트 플릿을 위한 대시보드 하나로 충분합니다.

> 🌐 **다른 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 바로 열립니다. 이게 전부입니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20개 에이전트 런타임 지원

ClawMetry는 OpenClaw를 위한 관측 도구로 시작했지만, 이제는 하나의 대시보드에서 여러분의 **전체 에이전트 플릿**을 계측하며, 여러분의 머신에 있는 각 런타임을 자동으로 감지합니다:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw와 NemoClaw는 오픈소스 앱에서 무료로 제공되며, 나머지 런타임들은 ClawMetry Cloud나 셀프 호스팅 Pro 라이선스를 통해 활성화됩니다. 헤더에서 런타임을 전환하면 비용, 토큰, 도구, 트레이스 등 모든 탭이 해당 런타임 기준으로 다시 범위가 조정됩니다. 정확한 무료/유료 구분, 티어 매트릭스, `/api/entitlement` 형태, `clawmetry license` CLI에 대해서는 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**를 참고하세요.

## 제공 기능

- **Flow** — 채널, 브레인, 도구를 거쳐 다시 돌아오는 메시지 흐름을 보여주는 실시간 애니메이션 다이어그램
- **Overview** — 상태 점검, 활동 히트맵, 세션 수, 모델 정보
- **Usage** — 일간/주간/월간 세부 내역과 함께 토큰 및 비용 추적
- **Sessions** — 모델, 토큰, 마지막 활동 시각을 포함한 활성 에이전트 세션
- **Crons** — 상태, 다음 실행 시각, 소요 시간이 표시되는 예약 작업
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

### 💰 Tokens — 모델 및 세션별 비용 세부 내역
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 워크스페이스 파일 브라우저
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 보안 상태 및 감사 로그
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 예산 한도, 오류율 트리거, Slack / Discord / PagerDuty / Email로의 웹훅
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 위험한 도구 호출을 수동 승인 뒤에 게이트하는 정책 기반 보호 규칙
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code를 위한 실행 전 차단** — 명령어 하나로 매칭되는 도구 호출을
실행 *전에* 일시 중지하고 여러분의 결정을 기다리는 PreToolUse 훅을 설치합니다
([클라우드 푸시 알림](https://app.clawmetry.com/push)을 활성화하면 휴대폰에서
탭 한 번으로 처리 가능):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

거부(deny)는 해당 도구 호출 하나만 차단합니다. 에이전트는 세션을 유지한 채
다른 방법을 시도할 수 있습니다. 휴대폰에서 승인하면 Claude Code 자체의
권한 프롬프트를 건너뜁니다(이미 답변한 것이므로). 매칭되지 않는 도구는
약 40ms의 비용만 들이고 Claude Code의 일반적인 권한 흐름으로 넘어갑니다.
Claude Code 자체가 여러분을 기다리고 있을 때도 휴대폰 푸시를 받을 수
있습니다(`permission_prompt` / `idle_prompt` 알림).

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

v2 React 앱은 `frontend/`에 있으며, Flask 서버가 v2를 활성화한 채로
시작되면 `/v2`에서 서빙됩니다.

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

`http://localhost:5173/v2/`를 여세요. Vite가 `/api` 요청을
`http://localhost:8900`으로 프록시하므로, React 앱이 별도의 CORS 설정
없이 로컬 Flask 서버와 통신할 수 있습니다.

Python 패키지와 함께 배포되는 번들을 빌드하려면:

```bash
cd frontend
npm run build
```

프로덕션 번들은 `clawmetry/static/v2/dist/`에 작성됩니다.

## 런타임/에이전트 호환성

ClawMetry는 OpenClaw뿐만 아니라 다양한 AI 에이전트 런타임을 관측합니다. OpenClaw가 아닌 각 런타임에는 해당 런타임의 네이티브 세션 형식을 ClawMetry의 통합된 형태로 변환하는 전용 리더 어댑터가 딸려 있습니다. 데몬은 이를 동일한 DuckDB 스토어 + 클라우드 스냅샷에 런타임 태그와 함께 수집하며, 두 개 이상의 런타임이 있을 때 Session replay 탭에 **런타임 전환기**가 표시됩니다. 전체 매트릭스와 런타임 추가 가이드는 [`docs/compatibility.md`](docs/compatibility.md)를, OpenClaw 계열 입문 자료는 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)를 참고하세요.

[Perplexity의 numbat](https://github.com/perplexityai/numbat) 에이전트 보안 도구를 사용 중이신가요? ClawMetry는 별도 설정 없이 numbat의 탐지 결과와 강제 조치 결정을 수집합니다. 자세한 내용은 [`docs/NUMBAT.md`](docs/NUMBAT.md)를 참고하세요.

| 런타임 / 에이전트 | 상태 | 비고 |
|---|---|---|
| **OpenClaw** | Native | 기준 런타임, 자동 감지 |
| **PicoClaw** | Beta adapter | 플랫 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`). 트랜스크립트, 모델, 도구 호출. |
| **NanoClaw** | Beta adapter | 세션별 SQLite(`data/v2-sessions`). 트랜스크립트 + 메시지 수. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. 트랜스크립트, 모델, 토큰/비용. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. 트랜스크립트, 모델, 도구 호출 + thinking, 토큰 사용량. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. 트랜스크립트, 모델, 도구 호출, 토큰 사용량. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. 채팅/컴포저 트랜스크립트, 모델. |
| **Aider** | Beta adapter | 프로젝트별 `.aider.chat.history.md`. 트랜스크립트, 모델, 토큰 수. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. 트랜스크립트, 모델, 도구 호출, 총 토큰. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. 트랜스크립트, 모델, 도구 호출, 토큰 + 비용. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. 트랜스크립트, 모델, 도구 호출, 토큰 사용량. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. 트랜스크립트, 모델, 도구 호출, 토큰 + 비용. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. 트랜스크립트, 모델, 도구 호출, 토큰 + 비용. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. 워크플로 실행, 노드 실행, AI Agent 프롬프트, n8n이 기록하는 경우의 모델 + 토큰. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` 하위의 Brain JSONL. 대화, 도구 단계, thinking, 생성별 Gemini 토큰 분할 + 비용, 백그라운드 생성 소모량. |
| **GitHub Copilot** | Beta adapter | `~/.copilot/session-state/` 하위의 Copilot CLI `events.jsonl` + 호출별 사용량 원장인 `session-store.db`. 대화, 도구 호출, 모델 라우팅, 캐시를 고려한 토큰 분할, 벤더가 청구하는 AI 크레딧 비용. |
| **Grok** | Beta adapter | xAI Grok Build CLI(`~/.grok/bin/grok` 하위의 Rust 바이너리): 전역 이벤트 로그 `~/.grok/logs/unified.jsonl` + 세션별 `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. 대화, 턴별 토큰 분할, 모델 라우팅, 무엇이 머신에서 나갔는지 확인할 수 있도록 `~/.grok/upload_queue/` 아래에 스테이징되는 CLI의 아웃바운드 저장소 페이로드. |

"Beta adapter"는 ClawMetry가 해당 런타임의 실제 디스크 저장 형식을 위한 리더를 제공하며, 각각 실제 머신에 설치된 실제 환경을 기준으로 빌드 및 검증되었음을 의미합니다(`tests/fixtures/runtimes/<rt>/` 참고). 어댑터는 읽기 전용이며, 각 런타임이 실제로 저장하는 데이터에 대해 정직하게 동작합니다(예: PicoClaw/NanoClaw/Cursor는 토큰 비용을 디스크에 기록하지 않습니다). 한 노드에서 여러 런타임이 동시에 실행 중일 때, 런타임 전환기를 사용하면 세션 뷰를 하나로 좁혀 깔끔하게 살펴볼 수 있습니다.

## 어떤 SDK 에이전트든 추적하기, 아웃루프 비용 귀속

위의 런타임들은 모두 세션을 디스크에 기록합니다. 여러분이 직접 만든 **프로덕션 에이전트**, 즉 OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, 또는 순수 `httpx` 루프로 만든 것은 그렇지 않습니다. ClawMetry의 제로 설정 인터셉터는 `httpx`/`requests`를 몽키 패칭하여 여전히 해당 에이전트의 LLM 호출(비용, 토큰, 지연 시간, 오류)을 포착합니다:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(또는 `CLAWMETRY_SOURCE=support-agent` 환경 변수)는 각 호출에 **이름이 붙은 소스**를 태그하므로, 여러분이 운영하는 모든 제품이 대시보드의 Overview에 있는 **🔌 아웃루프 소스** 카드에서 독립적인 1급 비용 귀속 항목으로 표시됩니다. 에이전트별 호출 수, 프로바이더, 지연 시간, 오류율까지 볼 수 있습니다. 소스를 설정하지 않았다면? 호출은 여전히 추적되며, 카드만 숨겨진 상태로 남습니다.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

이는 런타임 어댑터가 공급하는 것과 동일한 데이터 레이어(DuckDB → 클라우드 스냅샷)이므로, 아웃루프 소스도 다른 모든 데이터와 마찬가지로 종단간 암호화된 상태로 클라우드 대시보드에 동기화됩니다.

## OpenTelemetry, 벤더 중립적으로 트레이스를 어디로든 보내기

ClawMetry는 **GenAI 시맨틱 컨벤션**을 사용해 양방향으로 **OpenTelemetry**를 지원하므로, 여러분의 에이전트 트레이스가 하나의 도구에 절대 종속되지 않습니다.

모든 세션(LLM 호출, 도구, 서브 에이전트, 토큰, 비용)을 OTLP/HTTP GenAI 스팬으로 **내보내어** 원하는 컬렉터(Datadog, Grafana, Honeycomb, 또는 자체 OTel Collector)로 전송할 수 있습니다:

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

**수집(Ingest)** — 내장 OTLP 수신기는 `/v1/traces`, `/v1/logs`, `/v1/metrics`에서 다른 어떤 것으로부터든 트레이스, 로그, 메트릭을 받아들입니다. OpenTelemetry로 계측된 앱이라면 어떤 것이든 여기로 향하게 하세요:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON 트레이스와 로그는 별도 추가 설치 없이 `pip install clawmetry`만으로 동작합니다. Protobuf 수집(및 OTLP/JSON 메트릭)에는 `pip install clawmetry[otel]`이 필요합니다. 자체적으로 `service.name`을 설정하는 앱은 런타임 전환기에서 자신만의 비용과 토큰을 가진 독립적인 에이전트로 표시됩니다.

제로 설정, 로컬 우선인 ClawMetry 대시보드를 그대로 사용하면서도, 팀에서 이미 운영 중인 백엔드에 데이터를 함께 보낼 수 있습니다. 종속도 없고, 두 번째 에이전트를 설치할 필요도 없습니다.

## 설정

대부분의 사용자는 설정이 전혀 필요하지 않습니다. ClawMetry는 워크스페이스, 로그, 세션, cron을 자동으로 감지합니다.

커스터마이즈가 필요하다면:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

전체 옵션: `clawmetry --help`

## 지원 채널

ClawMetry는 여러분이 설정한 모든 OpenClaw 채널에 대해 실시간 활동을 보여줍니다. `openclaw.json`에 실제로 설정된 채널만 Flow 다이어그램에 표시되며, 설정되지 않은 채널은 자동으로 숨겨집니다.

Flow에서 채널 노드를 클릭하면 수신/발신 메시지 수와 함께 실시간 채팅 버블 뷰를 볼 수 있습니다.

| 채널 | 상태 | 실시간 팝업 | 비고 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | 메시지, 통계, 10초 새로고침 |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db`를 직접 읽음 |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web(Baileys)을 통해 |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli를 통해 |
| 🟣 **Discord** | ✅ Full | ✅ | 길드 + 채널 감지 |
| 🟪 **Slack** | ✅ Full | ✅ | 워크스페이스 + 채널 감지 |
| 🌐 **Webchat** | ✅ Full | ✅ | 내장 웹 UI 세션 |
| 📡 **IRC** | ✅ Full | ✅ | 터미널 스타일 버블 UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API를 통한 iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API 웹훅을 통해 |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams 봇 플러그인을 통해 |
| 🔷 **Mattermost** | ✅ Full | ✅ | 셀프 호스팅 팀 채팅 |
| 🟩 **Matrix** | ✅ Full | ✅ | 탈중앙화, E2EE 지원 |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | 탈중앙화 NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC 연결을 통한 채팅 |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket 이벤트 구독 |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **자동 감지:** ClawMetry는 `~/.openclaw/openclaw.json`을 읽고, 실제로 설정한 채널만 렌더링합니다. 수동 설정이 필요 없습니다.

## Docker 배포

컨테이너에서 ClawMetry를 실행하고 싶으신가요? 문제없습니다! 🐳

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

> **참고:** Docker에서 실행할 때는 ClawMetry가 여러분의 설정을 자동으로 감지할 수 있도록 에이전트의 데이터 + 로그 디렉터리(예: `~/.openclaw`, `~/.claude`, `~/.codex`)를 마운트하세요.

## 요구 사항

- Python 3.8+
- Flask(pip을 통해 자동 설치됨)
- 동일한 머신에 있는 AI 에이전트 런타임: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, QM(또는 Docker의 경우 마운트된 볼륨)
- Linux 또는 macOS

## NemoClaw / OpenShell 지원

ClawMetry는 [NemoClaw](https://github.com/NVIDIA/NemoClaw)를 자동으로 감지합니다. NemoClaw는 샌드박스화된 OpenShell 컨테이너 안에서 에이전트를 실행하는 NVIDIA의 엔터프라이즈 보안 래퍼입니다.

대부분의 경우 별도 설정이 필요하지 않습니다. 동기화 데몬은 세션 파일이 호스트의 `~/.openclaw/`에 있든 OpenShell 컨테이너 내부에 있든 자동으로 찾아냅니다.

### 동작 방식

ClawMetry는 두 가지 방법으로 NemoClaw를 감지합니다:

1. **바이너리 감지** — `nemoclaw` CLI가 있는지 확인하고 `nemoclaw status`를 실행해 샌드박스 정보를 가져옵니다
2. **컨테이너 감지** — 실행 중인 Docker 컨테이너를 스캔하여 `openshell`, `nemoclaw`, 또는 `ghcr.io/nvidia/` 이미지를 찾은 뒤, 볼륨 마운트나 `docker cp`를 통해 세션을 읽습니다

NemoClaw 컨테이너에서 동기화된 세션 파일은 클라우드 대시보드에서 `runtime=nemoclaw`와 `container_id` 메타데이터로 태그되므로, 표준 OpenClaw 세션과 한눈에 구분할 수 있습니다.

### 권장 설정: 호스트에서 동기화 데몬 실행

최상의 경험을 위해서는 ClawMetry의 동기화 데몬을 (샌드박스 내부가 아닌) **호스트 머신**에서 실행하세요. 이렇게 하면 NemoClaw 네트워크 정책 제한을 피할 수 있습니다.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

동기화 데몬은 실행 중인 OpenShell 컨테이너 안의 세션을 자동으로 찾아냅니다.

### 선택 사항: 명시적인 샌드박스 이름 지정

자동 감지가 동작하지 않는다면, 올바른 샌드박스를 명시적으로 지정하세요:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 샌드박스 내부에서 실행하기(고급)

동기화 데몬을 **반드시** OpenShell 샌드박스 내부에서 실행해야 한다면, NemoClaw 네트워크 정책에 다음 이그레스 규칙을 추가하여 ClawMetry ingest API에 접근할 수 있도록 하세요:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

다음 명령으로 적용합니다:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 포트 및 엔드포인트

| 엔드포인트 | 포트 | 프로토콜 | 필수 여부 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 필수(동기화 데몬 → 클라우드) |
| `localhost:8900` | 8900 | HTTP | 필수(로컬 대시보드 UI) |
| Docker 소켓(`/var/run/docker.sock`) | — | Unix 소켓 | 컨테이너 세션 검색용 |

동기화 데몬은 `ingest.clawmetry.com`으로만 아웃바운드 HTTPS 호출을 합니다. 인바운드 포트는 필요하지 않습니다.

---

## 클라우드 배포

SSH 터널, 리버스 프록시, Docker에 대해서는 **[클라우드 테스트 가이드](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**를 참고하세요.

## 테스트

이 프로젝트는 BrowserStack으로 테스트됩니다.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 텔레메트리

ClawMetry는 익명의 설치 라이프사이클 핑을
`https://app.clawmetry.com/api/install`로 전송합니다: 새 머신에서
`clawmetry` CLI를 처음 실행할 때 `install` 핑 1회, 새 버전으로 업그레이드
후 첫 실행 시 `update` 핑 1회, 대시보드 내 온보딩 선택을 완료할 때
`onboarded` 핑 1회입니다. 이를 통해 실제 설치 수를 집계하고(원시 PyPI
다운로드 수치는 약 98%가 미러, CI, 자동 업데이트 재다운로드입니다),
실제로 어떤 에이전트 프레임워크와 버전이 사용되고 있는지 파악합니다.

**라이프사이클 이벤트 및 버전당 최대 1건의 POST**가 전송되며, 다음
내용을 포함합니다:

| 필드 | 예시 | 이유 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`에 저장된 무작위 UUID | 중복 방지; Cloud sync를 명시적으로 연결하기 전까지는 익명(그 이후 인증된 데몬 하트비트가 이 값을 전달하여 이 설치를 여러분의 계정과 연결합니다) |
| `event` | `install` / `update` / `onboarded` | 새 설치인지 기존 설치의 업그레이드인지 구분 |
| `version` | `0.12.167` | 실제로 사용 중인 버전들 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 플랫폼 지원 우선순위 |
| `python` | `3.11.15` | Python 버전 지원 매트릭스 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 다음으로 통합해야 할 에이전트 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 실제 사용자 설치와 CI 노이즈를 구분 |

**전송하지 않는 것**: IP(클라우드는 요청에서 서버 측으로 국가 코드만
추출한 뒤 IP를 폐기합니다), 호스트명, 사용자명, 워크스페이스 경로,
파일 내용, 여러분의 api_key, 이메일, 그 외 개인 식별 정보나
워크스페이스 관련 정보는 전송하지 않습니다. 전송되는 페이로드는
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)에서 직접 확인할 수
있습니다.

**옵트아웃**(다음 중 하나만 실행해도 영구적으로 비활성화됩니다):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

네트워크 장애가 발생해도 `clawmetry` 실행이 막히는 일은 없습니다.
이 핑은 데몬 스레드에서 3초 타임아웃으로 발사 후 잊는(fire-and-forget)
방식으로 동작합니다.

## Star History

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
  <strong>🦞 여러분의 에이전트가 생각하는 모습을 확인하세요</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a>가 만듦 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 생태계의 일부</sub>
</p>
