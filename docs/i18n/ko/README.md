<!-- i18n-src:56ff57310588 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**에이전트의 사고를 들여다보세요.** [OpenClaw](https://github.com/openclaw/openclaw) AI 에이전트를 위한 실시간 관측 가능성.

> 🌐 **다른 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정 불필요. 모든 것을 자동 감지.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열리며, 그게 전부입니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 제공 기능

- **Flow**: 채널, 브레인, 도구를 거쳐 다시 돌아오는 메시지 흐름을 보여주는 실시간 애니메이션 다이어그램
- **Overview**: 상태 점검, 활동 히트맵, 세션 수, 모델 정보
- **Usage**: 일간/주간/월간 단위로 분류된 토큰 및 비용 추적
- **Sessions**: 모델, 토큰, 마지막 활동이 표시되는 활성 에이전트 세션
- **Crons**: 상태, 다음 실행, 소요 시간이 표시되는 예약 작업
- **Logs**: 색상으로 구분된 실시간 로그 스트리밍
- **Memory**: SOUL.md, MEMORY.md, AGENTS.md, 일일 노트 탐색
- **Transcripts**: 세션 기록을 읽기 위한 채팅 말풍선 UI
- **Alerts**: 예산 상한, 오류율 트리거, 에이전트 오프라인 감지; Slack, Discord, PagerDuty, Telegram, Email로 라우팅
- **Approvals**: 파괴적인 삭제, 강제 푸시, DB 변경, sudo, 패키지 설치, 네트워크 호출을 원클릭 승인 뒤에 두어 차단

## 스크린샷

### 🧠 Brain: 실시간 에이전트 이벤트 스트림
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: 토큰 사용량 및 세션 요약
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: 실시간 도구 호출 피드
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: 모델 및 세션별 비용 분석
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: 워크스페이스 파일 브라우저
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: 보안 태세 및 감사 로그
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: 예산 상한, 오류율 트리거, Slack / Discord / PagerDuty / Email로의 웹훅
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: 위험한 도구 호출을 수동 승인 뒤에 두어 차단; 정책 기반 보호 규칙
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

**소스에서:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 프론트엔드 개발

v2 React 앱은 `frontend/` 에 있으며, Flask 서버가 v2를 활성화한 상태로 시작되면
`/v2` 에서 제공됩니다.

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

`http://localhost:5173/v2/` 를 여세요. Vite는 `/api` 요청을
`http://localhost:8900` 로 프록시하므로, React 앱은 추가 CORS 설정 없이
로컬 Flask 서버와 통신할 수 있습니다.

Python 패키지와 함께 제공되는 번들을 빌드하려면:

```bash
cd frontend
npm run build
```

프로덕션 번들은 `clawmetry/static/v2/dist/` 에 작성됩니다.

## 런타임 / 에이전트 호환성

ClawMetry는 OpenClaw뿐만 아니라 다양한 AI 에이전트 런타임을 관측합니다. OpenClaw가 아닌 각 런타임은 자체 네이티브 세션 형식을 ClawMetry의 통합 형태로 변환하는 전용 리더 어댑터를 제공합니다. 데몬은 이를 런타임으로 태그하여 동일한 DuckDB 저장소 + 클라우드 스냅샷에 수집하며, 둘 이상이 존재할 경우 Session 리플레이 탭에 **런타임 전환기**가 표시됩니다. 전체 매트릭스와 런타임 추가 가이드는 [`docs/compatibility.md`](docs/compatibility.md) 를, OpenClaw 계열 입문서는 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) 를 참고하세요.

| 런타임 / 에이전트 | 상태 | 비고 |
|---|---|---|
| **OpenClaw** | 네이티브 | 레퍼런스 런타임, 자동 감지 |
| **PicoClaw** | 베타 어댑터 | 평면 `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). 트랜스크립트, 모델, 도구 호출. |
| **NanoClaw** | 베타 어댑터 | 세션별 SQLite (`data/v2-sessions`). 트랜스크립트 + 메시지 수. |
| **Hermes** | 베타 어댑터 | SQLite `~/.hermes/state.db`. 트랜스크립트, 모델, 토큰/비용. |
| **Claude Code** | 베타 어댑터 | JSONL `~/.claude/projects/.../<id>.jsonl`. 트랜스크립트, 모델, 도구 호출 + 사고 과정, 토큰 사용량. |
| **Codex** | 베타 어댑터 | 롤아웃 JSONL `~/.codex/sessions/...`. 트랜스크립트, 모델, 도구 호출, 토큰 사용량. |
| **Cursor** | 베타 어댑터 | SQLite `state.vscdb`. 채팅/컴포저 트랜스크립트, 모델. |
| **Aider** | 베타 어댑터 | 프로젝트별 `.aider.chat.history.md`. 트랜스크립트, 모델, 토큰 수. |
| **Goose** | 베타 어댑터 | SQLite `~/.local/share/goose`. 트랜스크립트, 모델, 도구 호출, 토큰 합계. |

"베타 어댑터"는 ClawMetry가 해당 런타임의 실제 디스크 형식을 위한 리더를 제공하며, 각각 실제 머신의 실제 설치 환경에 대해 빌드 + 검증되었음을 의미합니다 (`tests/fixtures/runtimes/<rt>/` 참고). 어댑터는 읽기 전용이며, 각 런타임이 실제로 저장하는 내용에 대해 정직합니다 (예: PicoClaw/NanoClaw/Cursor는 토큰 비용을 디스크에 기록하지 않습니다). 여러 런타임이 하나의 노드에서 실행될 때, 런타임 전환기는 세션 보기를 하나로 한정하여 깔끔하게 심층 분석할 수 있게 합니다.

## OpenTelemetry: 벤더 중립, 트레이스를 어디로든 전송

ClawMetry는 **GenAI 시맨틱 컨벤션**을 사용하여 양방향으로 **OpenTelemetry**를 지원하므로, 에이전트 트레이스가 하나의 도구에 갇히는 일이 없습니다.

모든 세션(LLM 호출, 도구, 서브 에이전트, 토큰, 비용)을 OTLP/HTTP GenAI 스팬으로 임의의 컬렉터(Datadog, Grafana, Honeycomb 또는 자체 OTel Collector)로 **내보내기**:

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

**수집**: 내장 OTLP 리시버는 `/v1/traces` 및 `/v1/metrics` 에서 다른 무엇으로부터든 트레이스와 메트릭을 수신합니다 (protobuf 수집은 `pip install clawmetry[otel]`).

제로 설정, 로컬 우선 ClawMetry 대시보드는 물론, 팀이 이미 운영하는 어떤 백엔드에서든 데이터를 **모두** 확보합니다. 종속도 없고, 추가로 설치할 두 번째 에이전트도 없습니다.

## 설정

대부분의 사용자는 설정이 전혀 필요하지 않습니다. ClawMetry는 워크스페이스, 로그, 세션, cron을 자동 감지합니다.

직접 커스터마이즈해야 하는 경우:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

전체 옵션: `clawmetry --help`

## 지원 채널

ClawMetry는 구성한 모든 OpenClaw 채널의 실시간 활동을 표시합니다. `openclaw.json` 에 실제로 설정된 채널만 Flow 다이어그램에 나타나며, 설정되지 않은 채널은 자동으로 숨겨집니다.

Flow에서 채널 노드를 클릭하면 수신/발신 메시지 수와 함께 실시간 채팅 말풍선 보기를 볼 수 있습니다.

| 채널 | 상태 | 실시간 팝업 | 비고 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 완전 | ✅ | 메시지, 통계, 10초 새로고침 |
| 💬 **iMessage** | ✅ 완전 | ✅ | `~/Library/Messages/chat.db` 직접 읽기 |
| 💚 **WhatsApp** | ✅ 완전 | ✅ | WhatsApp Web (Baileys) 경유 |
| 🔵 **Signal** | ✅ 완전 | ✅ | signal-cli 경유 |
| 🟣 **Discord** | ✅ 완전 | ✅ | 길드 + 채널 감지 |
| 🟪 **Slack** | ✅ 완전 | ✅ | 워크스페이스 + 채널 감지 |
| 🌐 **Webchat** | ✅ 완전 | ✅ | 내장 웹 UI 세션 |
| 📡 **IRC** | ✅ 완전 | ✅ | 터미널 스타일 말풍선 UI |
| 🍏 **BlueBubbles** | ✅ 완전 | ✅ | BlueBubbles REST API를 통한 iMessage |
| 🔵 **Google Chat** | ✅ 완전 | ✅ | Chat API 웹훅 경유 |
| 🟣 **MS Teams** | ✅ 완전 | ✅ | Teams 봇 플러그인 경유 |
| 🔷 **Mattermost** | ✅ 완전 | ✅ | 셀프 호스팅 팀 채팅 |
| 🟩 **Matrix** | ✅ 완전 | ✅ | 탈중앙화, E2EE 지원 |
| 🟢 **LINE** | ✅ 완전 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 완전 | ✅ | 탈중앙화 NIP-04 DM |
| 🟣 **Twitch** | ✅ 완전 | ✅ | IRC 연결을 통한 채팅 |
| 🔷 **Feishu/Lark** | ✅ 완전 | ✅ | WebSocket 이벤트 구독 |
| 🔵 **Zalo** | ✅ 완전 | ✅ | Zalo Bot API |

> **자동 감지:** ClawMetry는 `~/.openclaw/openclaw.json` 을 읽어 실제로 구성한 채널만 렌더링합니다. 수동 설정이 필요하지 않습니다.

## Docker 배포

ClawMetry를 컨테이너에서 실행하고 싶으신가요? 문제없습니다! 🐳

**Docker로 빠르게 시작하기:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **참고:** Docker에서 실행할 때는 ClawMetry가 설정을 자동 감지할 수 있도록 OpenClaw 워크스페이스와 로그 디렉터리를 마운트하세요.

## 요구 사항

- Python 3.8+
- Flask (pip을 통해 자동 설치됨)
- 동일한 머신에서 실행 중인 OpenClaw (또는 Docker의 경우 마운트된 볼륨)
- Linux 또는 macOS

## NemoClaw / OpenShell 지원

ClawMetry는 [NemoClaw](https://github.com/NVIDIA/NemoClaw) 를 자동으로 감지합니다. NemoClaw는 샌드박스화된 OpenShell 컨테이너 내부에서 에이전트를 실행하는 NVIDIA의 OpenClaw용 엔터프라이즈 보안 래퍼입니다.

대부분의 경우 추가 설정이 필요하지 않습니다. 동기화 데몬은 세션 파일이 호스트의 `~/.openclaw/` 에 있든 OpenShell 컨테이너 내부에 있든 자동으로 검색합니다.

### 작동 방식

ClawMetry는 두 가지 방식으로 NemoClaw를 감지합니다:

1. **바이너리 감지**: `nemoclaw` CLI를 확인하고 `nemoclaw status` 를 실행하여 샌드박스 정보를 가져옵니다
2. **컨테이너 감지**: 실행 중인 Docker 컨테이너에서 `openshell`, `nemoclaw` 또는 `ghcr.io/nvidia/` 이미지를 스캔한 다음, 볼륨 마운트 또는 `docker cp` 를 통해 세션을 읽습니다

NemoClaw 컨테이너에서 동기화된 세션 파일은 클라우드 대시보드에서 `runtime=nemoclaw` 및 `container_id` 메타데이터로 태그되므로, 표준 OpenClaw 세션과 한눈에 구별할 수 있습니다.

### 권장 설정: HOST에서 동기화 데몬 실행

최상의 경험을 위해서는 ClawMetry의 동기화 데몬을 (샌드박스 내부가 아닌) **호스트 머신**에서 실행하세요. 이렇게 하면 NemoClaw 네트워크 정책 제한을 피할 수 있습니다.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

동기화 데몬은 실행 중인 모든 OpenShell 컨테이너 내부의 세션을 자동으로 찾습니다.

### 선택 사항: 명시적 샌드박스 이름

자동 감지가 작동하지 않으면 ClawMetry를 올바른 샌드박스로 지정하세요:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 샌드박스 내부에서 실행 (고급)

동기화 데몬을 OpenShell 샌드박스 **내부**에서 실행해야 하는 경우, ClawMetry 수집 API에 도달할 수 있도록 NemoClaw 네트워크 정책에 다음 이그레스 규칙을 추가하세요:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

다음으로 적용:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 포트 및 엔드포인트

| 엔드포인트 | 포트 | 프로토콜 | 필수 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 예 (동기화 데몬 → 클라우드) |
| `localhost:8900` | 8900 | HTTP | 예 (로컬 대시보드 UI) |
| Docker 소켓 (`/var/run/docker.sock`) | - | Unix 소켓 | 컨테이너 세션 검색용 |

동기화 데몬은 `ingest.clawmetry.com` 으로만 아웃바운드 HTTPS 호출을 합니다. 인바운드 포트는 필요하지 않습니다.

---

## 클라우드 배포

SSH 터널, 리버스 프록시, Docker에 대해서는 **[클라우드 테스트 가이드](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** 를 참고하세요.

## 테스트

이 프로젝트는 BrowserStack으로 테스트됩니다.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 텔레메트리

ClawMetry는 새 머신에서 `clawmetry` CLI를 처음 실행할 때
`https://app.clawmetry.com/api/install` 로 익명의 "첫 실행" 핑을 한 번
전송합니다. 이를 통해 설치 수를 집계하고(OSS 프로젝트에서 우리가 가진
유일한 마케팅 지표) 사용자가 어떤 에이전트 프레임워크를 설치했는지
파악합니다.

**설치당 정확히 한 번의 POST**로, 다음을 포함합니다:

| 필드 | 예시 | 이유 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` 에 저장된 무작위 UUID | 중복 제거; 이메일 또는 api_key와 연결되지 않음 |
| `version` | `0.12.167` | 어떤 버전이 사용되고 있는지 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 플랫폼 지원 우선순위 |
| `python` | `3.11.15` | Python 버전 지원 매트릭스 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 다음에 통합해야 할 에이전트 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 사람의 설치와 CI 노이즈를 구분 |

**전송하지 않는 것**: IP(클라우드는 요청에서 서버 측에서 국가 코드를
도출한 다음 IP를 폐기합니다), 호스트명, 사용자명, 워크스페이스 경로,
파일 내용, api_key, 이메일, 기타 모든 PII 또는 워크스페이스 관련 정보.
전송 페이로드는 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 에서
감사할 수 있습니다.

**옵트아웃** (다음 중 하나만으로도 영구히 비활성화됩니다):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

여기서 네트워크 장애가 발생해도 `clawmetry` 실행을 막지 않습니다. 핑은
3초 타임아웃이 설정된 데몬 스레드에서 fire-and-forget 방식으로
전송됩니다.

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
  <strong>🦞 에이전트의 사고를 들여다보세요</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> 제작 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 생태계의 일부</sub>
</p>
