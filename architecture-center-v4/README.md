# Architecture Center v4 — Sales Architecture OS

영업이 고객 상담부터 견적 요청 전까지 매일 사용하는 모바일 중심 Architecture Center PoC입니다.

## 핵심 흐름

Customer / Opportunity → 1분 Architecture Wizard → Rule Engine → Sizing / Security / Network → Architecture ID → Quote Request → Approval / History

## v4 핵심 기능

- Android / iPhone 설치형 PWA
- 고객 / 영업기회 관리
- 1분 Architecture Wizard
- 모듈·동접·외부접속·DR·성장률 기반 Workload Class
- CPU / Memory / Disk / AP-DB / K8s Node 자동 추천
- L7 / WAF / FW / DMZ 자동 판정
- STANDARD / CONDITIONAL / NONSTANDARD 자동 분류
- Architecture ID 자동 발급
- 고객 설명 문구 자동 생성
- 견적 요청 상태 관리
- 영업별 My Work Queue
- 중앙 PostgreSQL 백엔드 구조
- GitHub Pages에서는 LocalStorage 기반 PWA Demo

## 실행

```bash
cd architecture-center-v4
cp .env.example .env
docker compose up -d --build
```

접속: http://localhost:8000

## 인증

PoC 백엔드는 사내 SSO / Reverse Proxy 연동을 전제로 `X-Architecture-User` 신뢰 헤더를 사용합니다. 운영에서는 클라이언트가 해당 헤더를 직접 넣지 못하도록 Backend 직접 접근을 차단하고, 인증 프록시가 외부 헤더를 제거한 뒤 검증된 사용자 식별자만 재주입해야 합니다.

## PWA

GitHub Pages에서는 `manifest.webmanifest` + `sw.js`로 설치형 웹앱으로 동작합니다.

- Android/Chrome: 브라우저 메뉴 → 앱 설치 또는 홈 화면에 추가
- iPhone/Safari: 공유 → 홈 화면에 추가

## Architecture ID

`ARC-YYYYMMDD-NNNN` 형식으로 발급합니다. 견적 요청은 Architecture ID를 기준키로 연결하도록 설계했습니다.


## v4.1 AI Best-Practice Layer

- Deterministic Rule Engine remains the source of sizing/standard decisions.
- AI reviews ambiguity, missing inputs, exception risk and customer explanation.
- AI output uses a strict structured schema instead of free-form chat.
- Every recommendation must return evidence IDs and known-issue IDs.
- AI cannot submit quotes, approve exceptions, modify standards, or alter BOM automatically.
- Historical incidents are maintained as regression eval cases.
- AI runs are written to the audit log with model, prompt version and evidence IDs.
- Routine reviews default to `gpt-6.1-sol`; the model can be changed by environment variable after eval comparison.
- Without `OPENAI_API_KEY`, the endpoint uses a deterministic grounded fallback so the workflow remains usable.

### AI review API

`POST /api/ai/review`

```json
{
  "architecture_id": "ARC-20261002-0001",
  "question": "누락정보와 주요 리스크를 검토해줘."
}
```

The response includes `confidence`, `missing_information`, `risks`, `recommendations`, `evidence_ids`, `known_issue_ids`, `escalation_required`, and `next_actions`.
