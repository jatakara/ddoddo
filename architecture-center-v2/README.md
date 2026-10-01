# Architecture Center v2

ERP / UC / Infrastructure 사전검토와 기술 의사결정을 관리하는 내부용 PoC입니다.

## 주요 기능
- Architecture Review 등록 및 자동 판정
- Review 이력 SQLite DB 저장
- 상태 관리: NEW / REVIEW / APPROVED / CLOSED
- ADR(Architecture Decision Record)
- Risk Register
- Audit Log
- Dashboard KPI

## PoC DB 포함
저장소에 `architecture_center.db`를 **의도적으로 포함**했습니다. clone 직후 샘플 Review / ADR / Risk 데이터를 확인할 수 있습니다.

> 운영 전환 시에는 DB 파일을 Git에서 제외하고 별도 영구 스토리지/백업 정책을 적용해야 합니다.

## 실행
```bash
cd architecture-center-v2
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

브라우저: `http://localhost:8000`

## 구조
```text
Browser
  |
FastAPI
  |
SQLite (architecture_center.db)
```

## 보안/확장성
현재 버전은 PoC 기준입니다. 사내 다중 사용자 운영 전에는 SSO/RBAC, HTTPS, 입력 검증, 백업, 비밀정보 관리가 필요합니다. 동시 쓰기가 증가하면 PostgreSQL 전환을 권장합니다.
