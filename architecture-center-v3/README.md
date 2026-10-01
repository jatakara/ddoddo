# Architecture Center v3

ERP / UC / Infrastructure 표준화와 예외 통제를 위한 Architecture Governance PoC입니다.

## v3 핵심 변경

- **PostgreSQL**: 다중 사용자/동시 쓰기 대응
- **SSO/Reverse-Proxy Identity Header + RBAC**: ADMIN / ARCHITECT / APPROVER / VIEWER
- **User Provisioning API/UI**: ADMIN이 PoC 사용자와 Role 생성
- **Approval Workflow**: DRAFT → SUBMITTED → APPROVED / REJECTED
- **Versioned Rule Engine**: 판정 기준을 Rule Set 버전으로 관리
- **Rule Traceability**: Review마다 판정에 사용한 Rule 버전을 고정 기록
- **Audit-ready Model**: Review/Approval/ADR/Risk/Rule 변경 이력 확장 기반
- **Docker Compose**: App + PostgreSQL 일괄 실행
- **GitHub Pages Demo**: `index.html`은 LocalStorage 기반으로 백엔드 없이 동작

## Architecture

```text
                 ┌──────────────────┐
Browser / Mobile │ Architecture UI  │
                 └────────┬─────────┘
                          │ HTTPS
                 ┌────────▼─────────┐
                 │ SSO / IAP / RP   │
                 │ inject identity  │
                 └────────┬─────────┘
                          │ X-Architecture-User
                 ┌────────▼─────────┐
                 │ FastAPI API      │
                 ├──────────────────┤
                 │ RBAC             │
                 │ Approval Service │
                 │ Rule Engine      │
                 │ Audit            │
                 └────────┬─────────┘
                          │ SQLAlchemy
                 ┌────────▼─────────┐
                 │ PostgreSQL 16    │
                 └──────────────────┘
```

## Review Governance

```text
DRAFT
  │ Architect submit
  ▼
SUBMITTED
  ├── Approver approve ──> APPROVED
  └── Approver reject  ──> REJECTED ──> re-submit
```

## Repository layout

```text
architecture-center-v3/
├─ index.html          # GitHub Pages / Backend UI
├─ app.py              # FastAPI + RBAC + Rule Engine + Approval
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ .env.example
```

## Run with Docker

```bash
cd architecture-center-v3
cp .env.example .env
docker compose up -d --build
```

접속: `http://localhost:8000`

PoC 기본 사용자: `admin`

백엔드 API는 `X-Architecture-User` 헤더로 사용자 식별자를 받습니다. 운영에서는 이 헤더를 클라이언트가 직접 지정하지 못하도록 차단하고, 신뢰 가능한 SSO/IAP/Reverse Proxy만 주입하도록 구성해야 합니다.

## GitHub Pages

루트 `index.html`은 정적 브라우저 데모입니다. GitHub Pages에서는 백엔드 대신 브라우저 LocalStorage에 데이터를 보존합니다.

실제 PostgreSQL 데이터는 FastAPI 서버를 통해서만 저장됩니다.

## Rule Set 예시

```json
{
  "small_integrated_max_users": 100,
  "single_node_max_users": 500,
  "integrated_erp_uc_review_threshold": 1000,
  "dedicated_design_threshold": 1500,
  "ceph_min_users": 1001,
  "ceph_max_users": 1500
}
```

새 Rule Set은 저장 후 즉시 적용되지 않습니다. **ADMIN이 Activate한 버전만 신규 Review 판정에 사용**됩니다. 기존 Review는 생성 시 사용했던 `rule_set_version`을 유지합니다.

## Security

PoC 상태에서도 작성/승인 권한을 분리했습니다. 운영 전환 시 추가 권고:

- 사내 SSO(OIDC/SAML) 또는 Identity-Aware Proxy가 인증 후 사용자 헤더 주입
- Backend 직접 접근 차단 및 Proxy가 외부 `X-Architecture-User` 헤더 제거/재작성
- HTTPS / Reverse Proxy / WAF 적용
- CORS 정책 명시
- PostgreSQL TLS 및 Backup/PITR
- 감사로그 immutable storage 전송
- 사용자/권한 provisioning을 IAM과 연계

## Scalability

SQLite 대신 PostgreSQL로 전환했으므로 여러 사용자의 동시 등록/승인에 적합합니다. FastAPI 인스턴스는 상태를 서버 메모리에 보관하지 않으므로 수평 확장할 수 있습니다.

다음 단계에서는 Redis 캐시보다 먼저 **DB Connection Pool, API rate limit, SSO, Audit 보존정책**을 적용하는 것이 우선입니다.

## Trade-off

| 선택 | 장점 | 단점 |
|---|---|---|
| PostgreSQL | 동시성, 트랜잭션, 운영 확장성 | 별도 DB 운영 필요 |
| Trusted identity header | 기존 SSO/IAP 연계가 단순 | Proxy 우회 차단이 필수 |
| Versioned Rule Set | 판정 근거 추적 가능 | Rule 변경 관리 프로세스 필요 |
| Approval Gate | 비표준 리스크 통제 | 승인 병목 가능 |
