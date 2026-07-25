<!-- i18n-src:8f42d460a973 -->
> 한국어 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**당신의 에이전트가 생각하는 모습을 보세요.** **14개의 AI 에이전트 런타임**을 위한 실시간 관찰 도구입니다: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex 및 그 외 10개. 여러분의 전체 에이전트 플릿을 위한 단 하나의 대시보드입니다.

> 🌐 **다른 언어로 읽기:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [더 보기 →](docs/i18n/)

명령어 하나. 설정은 필요 없습니다. 모든 것을 자동으로 감지합니다.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 에서 열리며, 그걸로 끝입니다.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14개의 에이전트 런타임과 함께 동작합니다

ClawMetry는 OpenClaw를 위한 관찰 도구로 시작했으며, 이제는 **여러분의 전체 에이전트 플릿**을 하나의 대시보드에서 계측하며, 여러분의 머신에서 각 런타임을 자동으로 감지합니다:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw와 NemoClaw는 오픈소스 앱에서 무료로 제공되며, 나머지 런타임들은 ClawMetry Cloud 또는 셀프 호스팅 Pro 라이선스를 통해 활성화됩니다. 헤더에서 런타임을 전환하면 비용, 토큰, 도구, 트레이스 등 모든 탭이 해당 런타임에 맞춰 다시 범위가 지정됩니다. 정확한 무료/유료 구분, 등급 매트릭스, `/api/entitlement` 형식, `clawmetry license` CLI에 대해서는 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** 를 참고하세요.

## 제공되는 기능

- **Flow** — 채널, 브레인, 도구를 거쳐 다시 돌아오는 메시지 흐름을 보여주는 실시간 애니메이션 다이어그램
- **Overview** — 상태 확인, 활동 히트맵, 세션 수, 모델 정보
- **Usage** — 일/주/월 단위 분석이 포함된 토큰 및 비용 추적
- **Sessions** — 모델, 토큰, 최근 활동이 표시되는 활성 에이전트 세션
- **Crons** — 상태, 다음 실행 시간, 소요 시간이 표시되는 예약 작업
- **Logs** — 색상으로 구분된 실시간 로그 스트리밍
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, 일일 노트 탐색
- **Transcripts** — 세션 기록을 읽기 위한 채팅 버블 UI
- **Alerts** — 예산 한도, 오류율 트리거, 에이전트 오프라인 감지; Slack, Discord, PagerDuty, Telegram, Email로 라우팅
- **Approvals** — 파괴적인 삭제, 강제 푸시, DB 변경, sudo, 패키지 설치, 네트워크 호출을 원클릭 승인 뒤에서 차단

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

### ✋ Approvals — 위험한 도구 호출을 수동 승인 뒤에서 차단; 정책 기반 보호 규칙
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 설치

**한 줄 설치 (권장):**
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
시작될 때 `/v2`에서 제공됩니다.

개발 중에는 두 개의 터미널을 사용하세요:

```bash
# 터미널 1: :8900에서 Flask API/서버 실행
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 터미널 2: :5173에서 Vite 개발 서버 실행
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` 를 여세요. Vite는 `/api` 요청을
`http://localhost:8900`으로 프록시하므로, React 앱이 별도의 CORS 설정 없이
로컬 Flask 서버와 통신할 수 있습니다.

Python 패키지와 함께 배포되는 번들을 빌드하려면:

```bash
cd frontend
npm run build
```

프로덕션 번들은 `clawmetry/static/v2/dist/`에 기록됩니다.

## 런타임 / 에이전트 호환성

ClawMetry는 OpenClaw뿐만 아니라 여러 AI 에이전트 런타임을 관찰합니다. OpenClaw가 아닌 각 런타임은 자체 세션 형식을 ClawMetry의 통합된 형태로 변환하는 전용 리더 어댑터를 제공합니다. 데몬은 이를 동일한 DuckDB 저장소 + 클라우드 스냅샷으로 수집하며 런타임 태그가 붙고, Session replay 탭은 둘 이상의 런타임이 존재할 때 **런타임 전환기**를 보여줍니다. 전체 매트릭스와 런타임 추가 가이드는 [`docs/compatibility.md`](docs/compatibility.md)를, OpenClaw 계열 소개는 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)를 참고하세요.

| 런타임 / 에이전트 | 상태 | 비고 |
|---|---|---|
| **OpenClaw** | 네이티브 | 기준 런타임, 자동 감지됨 |
| **PicoClaw** | 베타 어댑터 | 평평한 `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). 전사, 모델, 도구 호출. |
| **NanoClaw** | 베타 어댑터 | 세션별 SQLite (`data/v2-sessions`). 전사 + 메시지 수. |
| **Hermes** | 베타 어댑터 | SQLite `~/.hermes/state.db`. 전사, 모델, 토큰/비용. |
| **Claude Code** | 베타 어댑터 | JSONL `~/.claude/projects/.../<id>.jsonl`. 전사, 모델, 도구 호출 + 사고 과정, 토큰 사용량. |
| **Codex** | 베타 어댑터 | Rollout JSONL `~/.codex/sessions/...`. 전사, 모델, 도구 호출, 토큰 사용량. |
| **Cursor** | 베타 어댑터 | SQLite `state.vscdb`. 채팅/컴포저 전사, 모델. |
| **Aider** | 베타 어댑터 | 프로젝트별 `.aider.chat.history.md`. 전사, 모델, 토큰 수. |
| **Goose** | 베타 어댑터 | SQLite `~/.local/share/goose`. 전사, 모델, 도구 호출, 토큰 총합. |
| **opencode** | 베타 어댑터 | SQLite `~/.local/share/opencode`. 전사, 모델, 도구 호출, 토큰 + 비용. |
| **Qwen Code** | 베타 어댑터 | JSONL `~/.qwen/projects/.../chats`. 전사, 모델, 도구 호출, 토큰 사용량. |
| **Pi** | 베타 어댑터 | JSONL `~/.pi/agent/sessions`. 전사, 모델, 도구 호출, 토큰 + 비용. |
| **Deep Agents** | 베타 어댑터 | SQLite `~/.deepagents/.state/sessions.db`. 전사, 모델, 도구 호출, 토큰 + 비용. |

"베타 어댑터"는 ClawMetry가 실제 설치 환경에서 구축 및 검증된 (`tests/fixtures/runtimes/<rt>/` 참고) 해당 런타임의 실제 온디스크 형식에 대한 리더를 제공한다는 의미입니다. 어댑터는 읽기 전용이며, 각 어댑터는 해당 런타임이 실제로 저장하는 내용에 대해 정직합니다 (예: PicoClaw/NanoClaw/Cursor는 토큰 비용을 디스크에 기록하지 않습니다). 한 노드에서 여러 런타임이 실행 중일 때, 런타임 전환기는 세션 뷰의 범위를 하나로 좁혀 명확한 심층 분석을 가능하게 합니다.

## SDK 기반 에이전트 추적 — out-loop 비용 귀속

위의 런타임들은 모두 세션을 디스크에 기록합니다. 여러분이 OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, 또는 순수한 `httpx` 루프로 구축한 **프로덕션 에이전트**는 그렇지 않습니다. ClawMetry의 설정 없는 인터셉터는 `httpx`/`requests`를 몽키패치하여 여전히 해당 LLM 호출(비용, 토큰, 지연 시간, 오류)을 캡처합니다:

```python
import clawmetry.track            # 인터셉터 활성화
clawmetry.track.set_source("support-agent")   # 이 제품의 이름 지정

# ...여러분의 에이전트는 평소처럼 실행되며, 모든 LLM 호출이 이제 추적 및 귀속됩니다.
```

`set_source()` (또는 `CLAWMETRY_SOURCE=support-agent` 환경 변수)는 각 호출에 **명명된 소스**를 태그하므로, 여러분이 운영하는 각 제품은 대시보드의 Overview에 있는 **🔌 Out-loop sources** 카드에서 독립적인 1등급 비용 귀속 항목으로 나타납니다: 에이전트별 호출 수, 제공업체, 지연 시간, 오류율. 소스를 설정하지 않으면? 호출은 여전히 추적되지만 카드는 숨겨진 상태로 유지됩니다.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

이는 런타임 어댑터가 공급하는 것과 동일한 데이터 계층(DuckDB → 클라우드 스냅샷)이므로, out-loop 소스는 다른 모든 것과 마찬가지로 종단간 암호화되어 클라우드 대시보드에 동기화됩니다.

## OpenTelemetry — 벤더 중립적, 트레이스를 어디로든 전송

ClawMetry는 **GenAI 시맨틱 컨벤션**을 사용하여 양방향으로 **OpenTelemetry**를 지원하므로, 여러분의 에이전트 트레이스는 특정 도구에 절대 종속되지 않습니다.

**내보내기** — 모든 세션(LLM 호출, 도구, 서브 에이전트, 토큰, 비용)을 OTLP/HTTP GenAI 스팬으로 어떤 수집기(Datadog, Grafana, Honeycomb, 또는 여러분만의 OTel Collector)로든 내보낼 수 있습니다:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 동일한 방식:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

인증 헤더와 폴링 간격은 선택적 환경 변수입니다:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 추가 HTTP 헤더
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 초 (기본값 60)
```

**수집** — 내장된 OTLP 수신기는 `/v1/traces` 및 `/v1/metrics`에서 다른 어떤 곳으로부터든 트레이스와 메트릭을 받아들입니다 (protobuf 수집을 위해서는 `pip install clawmetry[otel]`).

여러분은 설정이 필요 없는, 로컬 우선의 ClawMetry 대시보드와 **더불어** 이미 팀에서 사용 중인 어떤 백엔드에도 여러분의 데이터를 가질 수 있습니다. 종속성도 없고, 설치할 두 번째 에이전트도 없습니다.

## 설정

대부분의 사람들은 별도의 설정이 필요하지 않습니다. ClawMetry는 여러분의 워크스페이스, 로그, 세션, cron을 자동으로 감지합니다.

커스터마이징이 필요하다면:

```bash
clawmetry --port 9000              # 사용자 지정 포트 (기본값: 8900)
clawmetry --host 127.0.0.1         # 로컬호스트에만 바인딩
clawmetry --workspace ~/mybot      # 사용자 지정 워크스페이스 경로
clawmetry --name "Alice"           # Flow 시각화에 표시될 여러분의 이름
```

모든 옵션: `clawmetry --help`

## 지원하는 채널

ClawMetry는 여러분이 설정한 모든 OpenClaw 채널의 실시간 활동을 보여줍니다. `openclaw.json`에 실제로 설정된 채널만 Flow 다이어그램에 표시되며, 설정되지 않은 채널은 자동으로 숨겨집니다.

Flow에서 채널 노드를 클릭하면 수신/발신 메시지 수가 표시되는 실시간 채팅 버블 뷰를 볼 수 있습니다.

| 채널 | 상태 | 실시간 팝업 | 비고 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 완전 지원 | ✅ | 메시지, 통계, 10초 갱신 |
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
| 🟩 **Matrix** | ✅ 완전 지원 | ✅ | 분산형, E2EE 지원 |
| 🟢 **LINE** | ✅ 완전 지원 | ✅ | LINE 메시징 API |
| ⚡ **Nostr** | ✅ 완전 지원 | ✅ | 분산형 NIP-04 DM |
| 🟣 **Twitch** | ✅ 완전 지원 | ✅ | IRC 연결을 통한 채팅 |
| 🔷 **Feishu/Lark** | ✅ 완전 지원 | ✅ | 웹소켓 이벤트 구독 |
| 🔵 **Zalo** | ✅ 완전 지원 | ✅ | Zalo Bot API |

> **자동 감지:** ClawMetry는 여러분의 `~/.openclaw/openclaw.json`을 읽고 실제로 설정한 채널만 렌더링합니다. 수동 설정이 필요하지 않습니다.

## Docker 배포

ClawMetry를 컨테이너에서 실행하고 싶으신가요? 문제없습니다! 🐳

**Docker로 빠르게 시작하기:**

```bash
# 이미지 빌드
docker build -t clawmetry .

# 기본 설정으로 실행
docker run -p 8900:8900 clawmetry

# 또는 여러분의 에이전트 데이터 디렉터리를 마운트 (예시: OpenClaw의 ~/.openclaw)
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
- Flask (pip을 통해 자동으로 설치됨)
- 동일한 머신에서 실행되는 AI 에이전트 런타임: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, 또는 Deep Agents (또는 Docker의 경우 마운트된 볼륨)
- Linux 또는 macOS

## NemoClaw / OpenShell 지원

ClawMetry는 [NemoClaw](https://github.com/NVIDIA/NemoClaw)를 자동으로 감지합니다. NemoClaw는 샌드박스화된 OpenShell 컨테이너 내부에서 에이전트를 실행하는 NVIDIA의 엔터프라이즈 보안 래퍼입니다.

대부분의 경우 별도의 설정이 필요하지 않습니다. sync 데몬은 세션 파일이 호스트의 `~/.openclaw/`에 있든 OpenShell 컨테이너 내부에 있든 자동으로 탐색합니다.

### 동작 방식

ClawMetry는 두 가지 방식으로 NemoClaw를 감지합니다:

1. **바이너리 감지** — `nemoclaw` CLI가 있는지 확인하고 `nemoclaw status`를 실행하여 샌드박스 정보를 가져옴
2. **컨테이너 감지** — 실행 중인 Docker 컨테이너를 스캔하여 `openshell`, `nemoclaw`, 또는 `ghcr.io/nvidia/` 이미지를 찾은 뒤, 볼륨 마운트 또는 `docker cp`를 통해 세션을 읽음

NemoClaw 컨테이너에서 동기화된 세션 파일에는 클라우드 대시보드에서 `runtime=nemoclaw`와 `container_id` 메타데이터가 태그되므로, 한눈에 표준 OpenClaw 세션과 구분할 수 있습니다.

### 권장 설정: 호스트에서 sync 데몬 실행

최상의 경험을 위해서는 ClawMetry의 sync 데몬을 (샌드박스 내부가 아닌) **호스트 머신**에서 실행하세요. 이렇게 하면 NemoClaw 네트워크 정책 제한을 피할 수 있습니다.

```bash
# 호스트에서 (샌드박스 외부)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync 데몬은 실행 중인 모든 OpenShell 컨테이너 내부의 세션을 자동으로 찾습니다.

### 선택 사항: 명시적인 샌드박스 이름 지정

자동 감지가 동작하지 않는 경우, ClawMetry가 올바른 샌드박스를 가리키도록 지정하세요:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 샌드박스 내부에서 실행하기 (고급)

sync 데몬을 OpenShell 샌드박스 **내부**에서 실행해야 하는 경우, ClawMetry ingest API에 접근할 수 있도록 NemoClaw 네트워크 정책에 다음 이그레스(egress) 규칙을 추가하세요:

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
| `ingest.clawmetry.com` | 443 | HTTPS | 예 (sync 데몬 → 클라우드) |
| `localhost:8900` | 8900 | HTTP | 예 (로컬 대시보드 UI) |
| Docker 소켓 (`/var/run/docker.sock`) | — | Unix 소켓 | 컨테이너 세션 탐색용 |

sync 데몬은 `ingest.clawmetry.com`으로만 외부 HTTPS 호출을 합니다. 인바운드 포트는 필요하지 않습니다.

---

## 클라우드 배포

SSH 터널, 리버스 프록시, Docker에 대해서는 **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** 를 참고하세요.

## 테스트

이 프로젝트는 BrowserStack으로 테스트됩니다.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 텔레메트리

ClawMetry는 새로운 머신에서 처음으로 `clawmetry` CLI를 실행할 때 단 한 번의 익명 "첫 실행" 핑을
`https://app.clawmetry.com/api/install` 로 전송합니다. 이는 설치 수를 세기 위해 사용되며(OSS 프로젝트로서
저희가 가진 유일한 마케팅 지표입니다), 사용자들이 어떤 에이전트 프레임워크를 설치했는지 파악하기 위해서입니다.

**설치당 정확히 한 번의 POST**로, 다음을 포함합니다:

| 필드 | 예시 | 이유 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`에 저장된 임의의 UUID | 중복 제거용; 여러분의 이메일이나 api_key와 연결되지 않음 |
| `version` | `0.12.167` | 실사용 중인 버전들 파악 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 플랫폼 지원 우선순위 결정 |
| `python` | `3.11.15` | Python 버전 지원 매트릭스 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 저희가 다음으로 통합해야 할 에이전트 파악 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 사람의 설치와 CI 노이즈 구분 |

**저희가 전송하지 않는 것**: IP(클라우드가 서버 측에서 요청으로부터 국가 코드를 도출한 뒤
폐기함), 호스트명, 사용자명, 워크스페이스 경로, 파일 내용, 여러분의 api_key, 여러분의 이메일, 그 외
개인 식별 정보나 워크스페이스 관련 정보. 전송 페이로드는
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)에서 확인할 수 있습니다.

**옵트아웃** (다음 중 하나만으로도 영구적으로 비활성화됩니다):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # 셸별
export DO_NOT_TRACK=1                          # W3C 크로스 툴 표준
touch ~/.clawmetry/notelemetry                 # 영구적인 파일 마커
```

네트워크 오류가 발생해도 `clawmetry` 실행이 차단되지는 않습니다. 이 핑은 데몬 스레드에서
3초 타임아웃으로 실행되는 fire-and-forget 방식입니다.

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
  <strong>🦞 당신의 에이전트가 생각하는 모습을 보세요</strong><br>
  <sub>제작: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 생태계의 일부</sub>
</p>
