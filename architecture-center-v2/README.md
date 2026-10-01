# Architecture Center v2

ERP / UC / Infrastructure 사전검토와 기술 의사결정을 관리하는 내부용 MVP입니다.

## 주요 기능
- Architecture Review 등록 및 자동 판정
- Review 이력 SQLite DB 영구 저장
- 상태 관리: NEW / REVIEW / APPROVED / CLOSED
- ADR(Architecture Decision Record)
- Risk Register
- Audit Log
- Dashboard KPI

## 자체 DB
실행 시 `architecture_center.db`가 자동 생성됩니다.

> DB 파일은 Git에 커밋하지 않습니다. 운영 이력은 실행 서버의 영구 스토리지에 보존하고 별도 백업하십시오.

## 실행
```bash
cd architecture-center-v2
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

## 주의
이 프로젝트는 FastAPI 백엔드와 SQLite가 필요하므로 GitHub Pages만으로는 실행할 수 없습니다.
실서비스 전에는 SSO/RBAC, HTTPS, 입력 검증, DB 백업, 비밀정보 관리와 감사정책을 추가해야 합니다.
