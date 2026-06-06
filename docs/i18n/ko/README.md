<!-- i18n-src:48548997be76 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**에이전트의 생각을 눈으로 확인하세요.** **12개 AI 에이전트 런타임**을 위한 실시간 옵저버빌리티: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 외 8개. 전체 에이전트 플리트를 하나의 대시보드에서 관리하세요.

> 🌐 **다른 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

명령어 하나. 설정 없음. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열리면 끝입니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12개 에이전트 런타임 지원

ClawMetry는 OpenClaw의 옵저버빌리티 도구로 시작하여, 이제 하나의 대시보드에서 **전체 에이전트 플리트**를 계측하며 머신의 각 런타임을 자동으로 감지합니다:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw과 NemoClaw은 오픈소스 앱에서 무료로 사용할 수 있으며, 나머지 런타임은 ClawMetry Cloud 또는 자체 호스팅 Pro 라이선스로 활성화됩니다. 헤더에서 런타임을 전환하면 비용, 토큰, 도구, 트레이스 등 모든 탭이 해당 런타임 기준으로 다시 표시됩니다.

## 주요 기능

- **Flow** — 채널, 브레인, 도구를 통해 메시지가 흐르는 실시간 애니메이션 다이어그램
- **Overview** — 상태 점검, 활동 히트맵, 세션 수, 모델 정보
- **Usage** — 일별/주별/월별 분류를 포함한 토큰 및 비용 추적
- **Sessions** — 모델, 토큰, 최근 활동이 표시된 활성 에이전트 세션
- **Crons** — 상태, 다음 실행 시간, 실행 시간이 표시된 예약 작업
- **Logs** — 색상으로 구분된 실시간 로그 스트리밍
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, 일별 노트 탐색
- **Transcripts** — 세션 기록을 읽을 수 있는 채팅 버블 UI
- **Alerts** — 예산 한도, 오류율 트리거, 에이전트 오프라인 감지; Slack, Discord, PagerDuty, Telegram, 이메일로 전달
- **Approvals** — 위험한 삭제, 강제 푸시, DB 변경, sudo, 패키지 설치, 네트워크 호출을 원클릭 승인 뒤에 차단

## 스크린샷

### 🧠 Brain — 실시간 에이전트 이벤트 스트림
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — 토큰 사용량 및 세션 요약
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 실시간 도구 호출 피드
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 모델 및 세션별 비용 분류
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 워크스페이스 파일 브라우저
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 보안 상태 및 감사 로그
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 예산 한도, 오류율 트리거, Slack / Discord / PagerDuty / 이메일 웹훅
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 위험한 도구 호출을 수동 승인 뒤에 차단; 정책 기반 보호 규칙
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 설치

**원라이너 (권장):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**소스에서 설치:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 프론트엔드 개발

v2 React 앱은 `frontend/` 에 위치하며, Flask 서버를 v2 활성화 상태로 시작하면 `/v2` 에서 제공됩니다.

개발 중에는 터미널 두 개를 사용하세요:

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

`http://localhost:5173/v2/` 를 여세요. Vite가 `/api` 요청을 `http://localhost:8900` 으로 프록시하므로, React 앱이 별도의 CORS 설정 없이 로컬 Flask 서버와 통신할 수 있습니다.

Python 패키지와 함께 배포되는 번들을 빌드하려면:

```bash
cd frontend
npm run build
```

프로덕션 번들은 `clawmetry/static/v2/dist/` 에 저장됩니다.

## 런타임 / 에이전트 호환성

ClawMetry는 OpenClaw뿐만 아니라 다양한 AI 에이전트 런타임을 관찰합니다. OpenClaw가 아닌 각 런타임에는 해당 런타임의 네이티브 세션 형식을 ClawMetry의 통합 형식으로 변환하는 전용 리더 어댑터가 포함되어 있으며, 데몬이 동일한 DuckDB 저장소 및 클라우드 스냅샷으로 인제스트할 때 런타임 태그를 붙입니다. 세션 재생 탭에는 두 개 이상의 런타임이 있을 때 **런타임 전환기**가 표시됩니다. 전체 매트릭스와 런타임 추가 가이드는 [`docs/compatibility.md`](docs/compatibility.md)를, OpenClaw 패밀리 개요는 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)를 참고하세요.

| 런타임 / 에이전트 | 상태 | 비고 |
|---|---|---|
| **OpenClaw** | 네이티브 | 레퍼런스 런타임, 자동 감지 |
| **PicoClaw** | 베타 어댑터 | 플랫 `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). 트랜스크립트, 모델, 도구 호출. |
| **NanoClaw** | 베타 어댑터 | 세션별 SQLite (`data/v2-sessions`). 트랜스크립트 및 메시지 수. |
| **Hermes** | 베타 어댑터 | SQLite `~/.hermes/state.db`. 트랜스크립트, 모델, 토큰/비용. |
| **Claude Code** | 베타 어댑터 | JSONL `~/.claude/projects/.../<id>.jsonl`. 트랜스크립트, 모델, 도구 호출 및 사고 과정, 토큰 사용량. |
| **Codex** | 베타 어댑터 | 롤아웃 JSONL `~/.codex/sessions/...`. 트랜스크립트, 모델, 도구 호출, 토큰 사용량. |
| **Cursor** | 베타 어댑터 | SQLite `state.vscdb`. 채팅/컴포저 트랜스크립트, 모델. |
| **Aider** | 베타 어댑터 | 프로젝트별 `.aider.chat.history.md`. 트랜스크립트, 모델, 토큰 수. |
| **Goose** | 베타 어댑터 | SQLite `~/.local/share/goose`. 트랜스크립트, 모델, 도구 호출, 총 토큰. |
| **opencode** | 베타 어댑터 | SQLite `~/.local/share/opencode`. 트랜스크립트, 모델, 도구 호출, 토큰 및 비용. |
| **Qwen Code** | 베타 어댑터 | JSONL `~/.qwen/projects/.../chats`. 트랜스크립트, 모델, 도구 호출, 토큰 사용량. |

"베타 어댑터"는 ClawMetry가 실제 설치 환경에서 검증된 각 런타임의 온디스크 형식을 읽는 리더를 제공한다는 의미입니다 (`tests/fixtures/runtimes/<rt>/` 참고). 어댑터는 읽기 전용이며, 각 런타임이 실제로 저장하는 데이터에 대해 정직하게 표시합니다 (예: PicoClaw/NanoClaw/Cursor는 디스크에 토큰 비용을 기록하지 않음). 하나의 노드에서 여러 런타임이 실행되면 런타임 전환기가 세션 보기를 하나로 범위를 좁혀 깔끔하게 살펴볼 수 있습니다.

## SDK 에이전트 추적 — 아웃루프 비용 귀속

위의 런타임들은 모두 세션을 디스크에 저장합니다. OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, 또는 단순한 `httpx` 루프로 만든 **프로덕션 에이전트**는 그렇지 않습니다. ClawMetry의 제로 컨피그 인터셉터는 `httpx`/`requests` 를 몽키 패칭하여 LLM 호출(비용, 토큰, 지연 시간, 오류)을 여전히 캡처합니다:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (또는 `CLAWMETRY_SOURCE=support-agent` 환경 변수)는 각 호출에 **명명된 소스** 태그를 붙이므로, 실행 중인 모든 제품이 대시보드의 Overview에 있는 **🔌 아웃루프 소스** 카드에 독립적인 비용 귀속 항목으로 표시됩니다. 소스가 설정되지 않으면 호출은 여전히 추적되지만 카드는 숨겨진 상태로 유지됩니다.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

이것은 런타임 어댑터가 사용하는 동일한 데이터 레이어(DuckDB → 클라우드 스냅샷)이므로, 아웃루프 소스도 E2E 암호화된 상태로 클라우드 대시보드에 동기화됩니다.

## OpenTelemetry — 벤더 중립, 트레이스를 어디든 전송

ClawMetry는 **GenAI 시맨틱 컨벤션**을 사용하여 **OpenTelemetry**를 양방향으로 지원하므로, 에이전트 트레이스가 특정 도구에 종속되지 않습니다.

모든 세션(LLM 호출, 도구, 서브에이전트, 토큰, 비용)을 OTLP/HTTP GenAI 스팬으로 임의의 컬렉터(Datadog, Grafana, Honeycomb 또는 자체 OTel Collector)에 **내보내기**:

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

**인제스트** — 내장 OTLP 수신기가 `/v1/traces` 및 `/v1/metrics` 에서 다른 소스의 트레이스와 메트릭을 수신합니다 (protobuf 인제스트에는 `pip install clawmetry[otel]` 필요).

팀이 이미 운영 중인 백엔드에 데이터를 유지하면서 제로 컨피그, 로컬 우선의 ClawMetry 대시보드를 함께 사용할 수 있습니다. 종속성 없음, 추가 에이전트 설치 없음.

## 설정

대부분의 사용자는 설정이 필요 없습니다. ClawMetry가 워크스페이스, 로그, 세션, cron을 자동으로 감지합니다.

커스터마이즈가 필요한 경우:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

전체 옵션: `clawmetry --help`

## 지원 채널

ClawMetry는 설정된 모든 OpenClaw 채널의 실시간 활동을 보여줍니다. `openclaw.json` 에 실제로 설정된 채널만 Flow 다이어그램에 표시되며, 설정되지 않은 채널은 자동으로 숨겨집니다.

Flow에서 채널 노드를 클릭하면 수신/발신 메시지 수가 포함된 실시간 채팅 버블 뷰를 볼 수 있습니다.

| 채널 | 상태 | 실시간 팝업 | 비고 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 완전 지원 | ✅ | 메시지, 통계, 10초 갱신 |
| 💬 **iMessage** | ✅ 완전 지원 | ✅ | `~/Library/Messages/chat.db` 직접 읽기 |
| 💚 **WhatsApp** | ✅ 완전 지원 | ✅ | WhatsApp Web (Baileys) 경유 |
| 🔵 **Signal** | ✅ 완전 지원 | ✅ | signal-cli 경유 |
| 🟣 **Discord** | ✅ 완전 지원 | ✅ | 길드 및 채널 감지 |
| 🟪 **Slack** | ✅ 완전 지원 | ✅ | 워크스페이스 및 채널 감지 |
| 🌐 **Webchat** | ✅ 완전 지원 | ✅ | 내장 웹 UI 세션 |
| 📡 **IRC** | ✅ 완전 지원 | ✅ | 터미널 스타일 버블 UI |
| 🍏 **BlueBubbles** | ✅ 완전 지원 | ✅ | BlueBubbles REST API를 통한 iMessage |
| 🔵 **Google Chat** | ✅ 완전 지원 | ✅ | Chat API 웹훅 경유 |
| 🟣 **MS Teams** | ✅ 완전 지원 | ✅ | Teams 봇 플러그인 경유 |
| 🔷 **Mattermost** | ✅ 완전 지원 | ✅ | 셀프 호스팅 팀 채팅 |
| 🟩 **Matrix** | ✅ 완전 지원 | ✅ | 분산형, E2EE 지원 |
| 🟢 **LINE** | ✅ 완전 지원 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 완전 지원 | ✅ | 분산형 NIP-04 DM |
| 🟣 **Twitch** | ✅ 완전 지원 | ✅ | IRC 연결을 통한 채팅 |
| 🔷 **Feishu/Lark** | ✅ 완전 지원 | ✅ | WebSocket 이벤트 구독 |
| 🔵 **Zalo** | ✅ 완전 지원 | ✅ | Zalo Bot API |

> **자동 감지:** ClawMetry가 `~/.openclaw/openclaw.json` 을 읽어 실제로 설정된 채널만 렌더링합니다. 수동 설정이 필요 없습니다.

## Docker 배포

ClawMetry를 컨테이너에서 실행하고 싶으신가요? 🐳

**Docker 빠른 시작:**

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

> **참고:** Docker에서 실행할 때는 에이전트의 데이터 및 로그 디렉터리(예: `~/.openclaw`, `~/.claude`, `~/.codex`)를 마운트하여 ClawMetry가 환경을 자동으로 감지할 수 있도록 하세요.

## 요구 사항

- Python 3.8 이상
- Flask (pip를 통해 자동 설치)
- 같은 머신에 실행 중인 AI 에이전트 런타임: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, 또는 PicoClaw (Docker의 경우 마운트된 볼륨)
- Linux 또는 macOS

## NemoClaw / OpenShell 지원

ClawMetry는 [NemoClaw](https://github.com/NVIDIA/NemoClaw)를 자동으로 감지합니다. NemoClaw는 샌드박스된 OpenShell 컨테이너 내에서 에이전트를 실행하는 NVIDIA의 엔터프라이즈 보안 래퍼입니다.

대부분의 경우 추가 설정이 필요 없습니다. 동기화 데몬이 호스트의 `~/.openclaw/` 또는 OpenShell 컨테이너 내부에 있는 세션 파일을 자동으로 찾습니다.

### 작동 방식

ClawMetry는 두 가지 방법으로 NemoClaw를 감지합니다:

1. **바이너리 감지** — `nemoclaw` CLI를 확인하고 `nemoclaw status` 를 실행하여 샌드박스 정보를 가져옵니다
2. **컨테이너 감지** — `openshell`, `nemoclaw`, 또는 `ghcr.io/nvidia/` 이미지가 있는 실행 중인 Docker 컨테이너를 스캔한 후, 볼륨 마운트 또는 `docker cp` 를 통해 세션을 읽습니다

NemoClaw 컨테이너에서 동기화된 세션 파일은 클라우드 대시보드에서 `runtime=nemoclaw` 및 `container_id` 메타데이터로 태그되므로, 일반 OpenClaw 세션과 한눈에 구분할 수 있습니다.

### 권장 설정: 호스트에서 동기화 데몬 실행

최상의 경험을 위해 ClawMetry의 동기화 데몬을 샌드박스 내부가 아닌 **호스트 머신**에서 실행하세요. 이렇게 하면 NemoClaw 네트워크 정책 제한을 피할 수 있습니다.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

동기화 데몬이 실행 중인 OpenShell 컨테이너 내부의 세션을 자동으로 찾습니다.

### 선택 사항: 명시적 샌드박스 이름 지정

자동 감지가 작동하지 않는 경우, ClawMetry가 올바른 샌드박스를 가리키도록 설정하세요:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 샌드박스 내부에서 실행 (고급)

동기화 데몬을 OpenShell 샌드박스 **내부**에서 실행해야 하는 경우, ClawMetry 인제스트 API에 접근할 수 있도록 NemoClaw 네트워크 정책에 이 이그레스 규칙을 추가하세요:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

다음 명령으로 적용하세요:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 포트 및 엔드포인트

| 엔드포인트 | 포트 | 프로토콜 | 필수 여부 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 필수 (동기화 데몬 → 클라우드) |
| `localhost:8900` | 8900 | HTTP | 필수 (로컬 대시보드 UI) |
| Docker 소켓 (`/var/run/docker.sock`) | — | Unix 소켓 | 컨테이너 세션 탐색용 |

동기화 데몬은 `ingest.clawmetry.com` 으로만 아웃바운드 HTTPS 호출을 합니다. 인바운드 포트는 필요하지 않습니다.

---

## 클라우드 배포

SSH 터널, 리버스 프록시, Docker에 대한 내용은 **[클라우드 테스트 가이드](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**를 참고하세요.

## 테스트

이 프로젝트는 BrowserStack으로 테스트됩니다.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 텔레메트리

ClawMetry는 새 머신에서 `clawmetry` CLI를 처음 실행할 때 `https://app.clawmetry.com/api/install` 로 단 한 번의 익명 "첫 실행" 핑을 전송합니다. 이를 통해 설치 수(오픈소스 프로젝트가 보유한 유일한 마케팅 지표)와 사용자가 설치한 에이전트 프레임워크를 파악합니다.

**설치당 정확히 하나의 POST** 요청이 전송되며, 포함 내용:

| 필드 | 예시 | 이유 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` 에 저장된 임의의 UUID | 중복 제거용; 이메일이나 api_key와 연결되지 않음 |
| `version` | `0.12.167` | 어떤 버전이 사용 중인지 파악 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 플랫폼 지원 우선순위 |
| `python` | `3.11.15` | Python 버전 지원 매트릭스 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 다음에 통합할 에이전트 결정 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 실제 사용자 설치와 CI 노이즈 구분 |

**전송하지 않는 항목**: IP (클라우드가 요청에서 국가 코드만 추출한 후 IP를 즉시 폐기), 호스트명, 사용자명, 워크스페이스 경로, 파일 내용, api_key, 이메일, PII 또는 워크스페이스 관련 정보. 전송 페이로드는 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 에서 감사할 수 있습니다.

**거부하기** (다음 중 하나를 사용하면 영구적으로 비활성화됨):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

네트워크 오류가 발생해도 `clawmetry` 실행이 차단되지 않습니다. 핑은 3초 타임아웃의 데몬 스레드에서 비동기로 실행됩니다.

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
  <strong>🦞 에이전트의 생각을 눈으로 확인하세요</strong><br>
  <sub>제작: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 에코시스템의 일부</sub>
</p>
