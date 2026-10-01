# Solution Design & Quote Intelligence Platform

## Product thesis

고객 요구사항을 입력하면 판매 가능한 솔루션 구성, BOM, 기술 리스크, 견적 준비 상태와 다음 영업 행동을 자동으로 생성하고 예외 건만 전문가에게 전달하는 B2B AI Presales 플랫폼.

## Buyer

- ERP / UC / MES / CRM / Cloud / Security 솔루션 기업
- SI / MSP / VAR / Distributor
- Pre-Sales / Solution Architect / Sales Engineering 조직
- 견적 품질과 기술검토 리드타임을 관리하는 영업·기술 임원

## Buyer pain

1. 영업이 기술검토를 위해 SA/TA에게 반복 문의
2. 고객 요구사항 누락으로 견적 재작업
3. 담당자별 설계 품질 편차
4. 견적과 실제 구축 사양 불일치
5. 예외 구성의 승인 근거가 남지 않음
6. 과거 장애/실패 경험이 다음 영업에 재사용되지 않음
7. 고객 회신 속도가 느려 경쟁력이 떨어짐

## Core value

**Faster Quote**
고객 문의 → 설계 초안 → BOM → 견적 준비를 수시간/수일에서 수분 단위로 단축.

**Lower Presales Cost**
표준 건은 자동처리하고 SA/TA는 예외·고위험 건에 집중.

**Prevent Bad Quotes**
누락조건, 호환성, HA/DR, 보안, Network, Storage 리스크를 Quote 이전에 차단.

**Increase Revenue**
필수 구성 누락 방지와 합리적 Upsell/Cross-sell 후보를 제시.

**Evidence & Governance**
왜 이 구성이 선택됐는지 Rule, Evidence, Known Issue, 승인 이력을 남김.

## Main workflow

```text
Customer / Opportunity
        ↓
Discovery Intake
        ↓
AI Requirement Extraction
        ↓
Solution Design
        ↓
BOM / License / Service
        ↓
Risk & Compatibility Check
        ↓
Quote Readiness Score
        ↓
STANDARD ─────────→ Quote
CONDITIONAL ──────→ Expert Review
NONSTANDARD ──────→ Architecture Approval
        ↓
Proposal / CRM / CPQ
        ↓
Delivery Handoff
```

## Killer functions

1. Customer discovery copilot
2. Automatic solution design
3. Automatic BOM / license / professional-service mapping
4. Quote Readiness Gate
5. Compatibility and known-issue prevention
6. Evidence-backed recommendation
7. Expert Review Queue
8. Customer proposal generator
9. CRM / CPQ integration
10. Delivery handoff package

## Product rule

AI는 제안과 분석을 수행한다. 가격 승인, 예외 승인, 계약 조건, 표준 변경과 같은 consequential action은 사람이 승인한다.

## MVP success metrics

- Standard quote technical review automation rate ≥ 60%
- Median quote preparation time reduction ≥ 50%
- Rework rate reduction ≥ 30%
- Missing mandatory component rate < 2%
- Expert review ratio ≤ 40%
- Evidence attached to 100% of AI recommendations
- Sales weekly active usage ≥ 70%

## Separation from Architecture Center

| Architecture Center | Solution Design & Quote Intelligence |
|---|---|
| 내부 Architecture Governance | 외부 판매 가능한 B2B Product |
| 표준/예외 통제 | 매출/견적 생산성 |
| TA/SA 중심 | Sales/Pre-Sales 중심 |
| Architecture ID | Opportunity / Design / Quote |
| 표준 준수 | Quote Readiness / Revenue |
| 구축 안정성 | Sales Velocity + Risk Prevention |

## Roadmap

### Phase 1 — Quote Intelligence
Discovery Intake, Design, BOM, Quote Gate, Evidence, Review Queue.

### Phase 2 — Commercial Intelligence
Pricing range, margin guardrail, option comparison, upsell/cross-sell, approval workflow.

### Phase 3 — Connected Presales
CRM/CPQ/ERP/Document integration, proposal generation, customer portal, delivery handoff.

### Phase 4 — Learning System
Win/loss, actual delivery cost, incidents, telemetry를 이용해 Rule/BOM/AI recommendation을 지속 개선.
