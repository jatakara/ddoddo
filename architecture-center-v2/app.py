
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "architecture_center.db"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Architecture Center v2", version="2.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def now():
    return datetime.now().isoformat(timespec="seconds")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS architecture_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            users INTEGER NOT NULL DEFAULT 0,
            service TEXT NOT NULL,
            shape TEXT NOT NULL,
            network TEXT NOT NULL,
            dr TEXT NOT NULL,
            memo TEXT,
            evaluation TEXT NOT NULL,
            recommendation TEXT,
            risk_level TEXT NOT NULL DEFAULT 'LOW',
            status TEXT NOT NULL DEFAULT 'NEW',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checklist_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            result TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(review_id) REFERENCES architecture_reviews(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS decision_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER,
            topic TEXT NOT NULL,
            decision TEXT NOT NULL,
            rationale TEXT,
            risk TEXT,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            owner TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(review_id) REFERENCES architecture_reviews(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER,
            title TEXT NOT NULL,
            likelihood TEXT NOT NULL,
            impact TEXT NOT NULL,
            response TEXT,
            owner TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL,
            FOREIGN KEY(review_id) REFERENCES architecture_reviews(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        """)

init_db()

class ReviewIn(BaseModel):
    customer: str = Field(min_length=1)
    users: int = Field(ge=0)
    service: str
    shape: str
    network: str
    dr: str
    memo: Optional[str] = ""

class ReviewStatusIn(BaseModel):
    status: str

class DecisionIn(BaseModel):
    review_id: Optional[int] = None
    topic: str
    decision: str
    rationale: Optional[str] = ""
    risk: Optional[str] = ""
    status: str = "DRAFT"
    owner: Optional[str] = ""

class RiskIn(BaseModel):
    review_id: Optional[int] = None
    title: str
    likelihood: str
    impact: str
    response: Optional[str] = ""
    owner: Optional[str] = ""
    status: str = "OPEN"

class ChecklistItem(BaseModel):
    category: str
    item: str
    result: str
    note: Optional[str] = ""

class ChecklistIn(BaseModel):
    items: List[ChecklistItem]

def evaluate(review: ReviewIn):
    u = review.users
    evaluation = "표준"
    risk_level = "LOW"
    notes = []

    if u > 1500:
        evaluation = "비표준 / 전용검토"
        risk_level = "HIGH"
        notes.append("1,500 User 초과: 전용 성능·HA·DR 설계 필요")
    elif review.shape == "단일노드" and u > 500:
        evaluation = "비표준 / 예외승인"
        risk_level = "HIGH"
        notes.append("500 User 초과 단일노드: 장애영향·확장성 리스크")
    elif review.network == "폐쇄망" or review.dr != "없음":
        evaluation = "조건부 표준"
        risk_level = "MEDIUM"

    if review.service == "ERP + UC" and review.shape == "통합형" and u > 1000:
        evaluation = "Architecture Review"
        risk_level = "MEDIUM"
        notes.append("ERP+UC 통합 고사용자 구성: 자원경합 검토 필요")

    m = (review.memo or "").lower()
    if "외부" in m or "dmz" in m:
        notes.append("외부노출: WAF/L7/DNAT/SSL 정책 검토 필요")
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    if u <= 100:
        recommendation = "AP/DB 통합 1대 가능 후보"
    elif u <= 500:
        recommendation = "AP/DB 분리 권장"
    elif u <= 1000:
        recommendation = "2-Node 또는 역할 분리 검토"
    elif u <= 1500:
        recommendation = "3-Node Cluster + Rook-Ceph/NAS 검토"
    else:
        recommendation = "전용 설계"

    if notes:
        recommendation += " / " + " · ".join(notes)

    return evaluation, recommendation, risk_level

@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "db": str(DB_PATH.name), "version": "2.0.0"}

@app.get("/api/dashboard")
def dashboard():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM architecture_reviews").fetchone()["c"]
        high = conn.execute("SELECT COUNT(*) c FROM architecture_reviews WHERE risk_level='HIGH' AND status!='CLOSED'").fetchone()["c"]
        open_risks = conn.execute("SELECT COUNT(*) c FROM risks WHERE status='OPEN'").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM architecture_reviews WHERE status IN ('NEW','REVIEW')").fetchone()["c"]
        latest = [dict(r) for r in conn.execute(
            "SELECT * FROM architecture_reviews ORDER BY id DESC LIMIT 8"
        ).fetchall()]
    return {"total_reviews": total, "high_risk": high, "open_risks": open_risks, "pending": pending, "latest": latest}

@app.post("/api/reviews")
def create_review(review: ReviewIn):
    evaluation, recommendation, risk_level = evaluate(review)
    ts = now()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO architecture_reviews
            (customer, users, service, shape, network, dr, memo, evaluation, recommendation, risk_level, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?)
        """, (review.customer, review.users, review.service, review.shape, review.network, review.dr,
              review.memo, evaluation, recommendation, risk_level, ts, ts))
        review_id = cur.lastrowid
        conn.execute("""
            INSERT INTO audit_logs(entity_type, entity_id, action, detail, created_at)
            VALUES('review', ?, 'CREATE', ?, ?)
        """, (review_id, f"{review.customer} / {evaluation}", ts))
    return {"id": review_id, "evaluation": evaluation, "recommendation": recommendation, "risk_level": risk_level}

@app.get("/api/reviews")
def list_reviews():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM architecture_reviews ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.get("/api/reviews/{review_id}")
def get_review(review_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM architecture_reviews WHERE id=?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Review not found")
        check = [dict(r) for r in conn.execute("SELECT * FROM checklist_results WHERE review_id=? ORDER BY id", (review_id,)).fetchall()]
        decisions = [dict(r) for r in conn.execute("SELECT * FROM decision_logs WHERE review_id=? ORDER BY id DESC", (review_id,)).fetchall()]
        risks = [dict(r) for r in conn.execute("SELECT * FROM risks WHERE review_id=? ORDER BY id DESC", (review_id,)).fetchall()]
    data = dict(row)
    data["checklist"] = check
    data["decisions"] = decisions
    data["risks"] = risks
    return data

@app.patch("/api/reviews/{review_id}/status")
def update_review_status(review_id: int, body: ReviewStatusIn):
    ts = now()
    with get_conn() as conn:
        exists = conn.execute("SELECT 1 FROM architecture_reviews WHERE id=?", (review_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Review not found")
        conn.execute("UPDATE architecture_reviews SET status=?, updated_at=? WHERE id=?", (body.status, ts, review_id))
        conn.execute("INSERT INTO audit_logs(entity_type, entity_id, action, detail, created_at) VALUES('review', ?, 'STATUS', ?, ?)",
                     (review_id, body.status, ts))
    return {"ok": True}

@app.post("/api/reviews/{review_id}/checklist")
def save_checklist(review_id: int, body: ChecklistIn):
    ts = now()
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM architecture_reviews WHERE id=?", (review_id,)).fetchone():
            raise HTTPException(404, "Review not found")
        conn.execute("DELETE FROM checklist_results WHERE review_id=?", (review_id,))
        for i in body.items:
            conn.execute("""
                INSERT INTO checklist_results(review_id, category, item, result, note, created_at)
                VALUES(?,?,?,?,?,?)
            """, (review_id, i.category, i.item, i.result, i.note, ts))
        conn.execute("INSERT INTO audit_logs(entity_type, entity_id, action, detail, created_at) VALUES('review', ?, 'CHECKLIST_SAVE', ?, ?)",
                     (review_id, f"{len(body.items)} items", ts))
    return {"ok": True, "count": len(body.items)}

@app.get("/api/decisions")
def list_decisions():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM decision_logs ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/decisions")
def create_decision(d: DecisionIn):
    ts = now()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO decision_logs(review_id, topic, decision, rationale, risk, status, owner, created_at)
            VALUES(?,?,?,?,?,?,?,?)
        """, (d.review_id, d.topic, d.decision, d.rationale, d.risk, d.status, d.owner, ts))
        did = cur.lastrowid
        conn.execute("INSERT INTO audit_logs(entity_type, entity_id, action, detail, created_at) VALUES('decision', ?, 'CREATE', ?, ?)",
                     (did, d.topic, ts))
    return {"id": did}

@app.get("/api/risks")
def list_risks():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM risks ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/risks")
def create_risk(r: RiskIn):
    ts = now()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO risks(review_id, title, likelihood, impact, response, owner, status, created_at)
            VALUES(?,?,?,?,?,?,?,?)
        """, (r.review_id, r.title, r.likelihood, r.impact, r.response, r.owner, r.status, ts))
        rid = cur.lastrowid
        conn.execute("INSERT INTO audit_logs(entity_type, entity_id, action, detail, created_at) VALUES('risk', ?, 'CREATE', ?, ?)",
                     (rid, r.title, ts))
    return {"id": rid}

@app.get("/api/audit")
def list_audit():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]
