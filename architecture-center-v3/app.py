from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

class Settings(BaseSettings):
    database_url: str = "sqlite:///./architecture_center_v3.db"
    bootstrap_admin_user: str = "admin"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
def utcnow(): return datetime.utcnow()
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    username: Mapped[str]=mapped_column(String(80),unique=True,index=True)
    role: Mapped[str]=mapped_column(String(30),default="VIEWER")
    active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
class RuleSet(Base):
    __tablename__="rule_sets"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    version: Mapped[str]=mapped_column(String(40),unique=True)
    description: Mapped[str]=mapped_column(Text,default="")
    rules: Mapped[dict]=mapped_column(JSON)
    active: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
class ArchitectureReview(Base):
    __tablename__="architecture_reviews"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    customer: Mapped[str]=mapped_column(String(200),index=True)
    users: Mapped[int]=mapped_column(Integer,default=0)
    service: Mapped[str]=mapped_column(String(40))
    shape: Mapped[str]=mapped_column(String(60))
    network: Mapped[str]=mapped_column(String(60))
    dr: Mapped[str]=mapped_column(String(60))
    memo: Mapped[str]=mapped_column(Text,default="")
    evaluation: Mapped[str]=mapped_column(String(100))
    recommendation: Mapped[str]=mapped_column(Text,default="")
    risk_level: Mapped[str]=mapped_column(String(20),default="LOW")
    status: Mapped[str]=mapped_column(String(30),default="DRAFT",index=True)
    rule_set_version: Mapped[str]=mapped_column(String(40),default="")
    created_by: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)
class Approval(Base):
    __tablename__="approvals"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    review_id: Mapped[int]=mapped_column(ForeignKey("architecture_reviews.id",ondelete="CASCADE"),index=True)
    action: Mapped[str]=mapped_column(String(30))
    comment: Mapped[str]=mapped_column(Text,default="")
    actor: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
class DecisionLog(Base):
    __tablename__="decision_logs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    review_id: Mapped[int|None]=mapped_column(ForeignKey("architecture_reviews.id",ondelete="SET NULL"),nullable=True)
    topic: Mapped[str]=mapped_column(String(200))
    decision: Mapped[str]=mapped_column(Text)
    rationale: Mapped[str]=mapped_column(Text,default="")
    risk: Mapped[str]=mapped_column(Text,default="")
    status: Mapped[str]=mapped_column(String(30),default="DRAFT")
    owner: Mapped[str]=mapped_column(String(80),default="")
    created_by: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
class Risk(Base):
    __tablename__="risks"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    review_id: Mapped[int|None]=mapped_column(ForeignKey("architecture_reviews.id",ondelete="SET NULL"),nullable=True)
    title: Mapped[str]=mapped_column(String(240))
    likelihood: Mapped[str]=mapped_column(String(20))
    impact: Mapped[str]=mapped_column(String(20))
    response: Mapped[str]=mapped_column(Text,default="")
    owner: Mapped[str]=mapped_column(String(80),default="")
    status: Mapped[str]=mapped_column(String(30),default="OPEN",index=True)
    created_by: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    entity_type: Mapped[str]=mapped_column(String(40),index=True)
    entity_id: Mapped[int|None]=mapped_column(Integer,nullable=True)
    action: Mapped[str]=mapped_column(String(50))
    actor: Mapped[str]=mapped_column(String(80))
    detail: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow,index=True)

class UserCreateIn(BaseModel): username:str=Field(min_length=3,max_length=80); role:str
class ReviewIn(BaseModel): customer:str=Field(min_length=1,max_length=200); users:int=Field(ge=0); service:str; shape:str; network:str; dr:str; memo:str=""
class ActionIn(BaseModel): comment:str=""
class DecisionIn(BaseModel): review_id:int|None=None; topic:str; decision:str; rationale:str=""; risk:str=""; status:str="DRAFT"; owner:str=""
class RiskIn(BaseModel): review_id:int|None=None; title:str; likelihood:str; impact:str; response:str=""; owner:str=""; status:str="OPEN"
class RuleSetIn(BaseModel): version:str; description:str=""; rules:dict

DEFAULT_RULES={"small_integrated_max_users":100,"single_node_max_users":500,"integrated_erp_uc_review_threshold":1000,"dedicated_design_threshold":1500,"ceph_min_users":1001,"ceph_max_users":1500}

def row_to_dict(r): return {c.name:getattr(r,c.name) for c in r.__table__.columns}
def audit(db,entity_type,entity_id,action,actor,detail=None): db.add(AuditLog(entity_type=entity_type,entity_id=entity_id,action=action,actor=actor,detail=detail or {}))

def current_user(x_architecture_user:str|None=Header(default=None),db:Session=Depends(get_db))->User:
    if not x_architecture_user: raise HTTPException(401,"Missing trusted identity header")
    user=db.query(User).filter(User.username==x_architecture_user,User.active.is_(True)).first()
    if not user: raise HTTPException(403,"User is not provisioned")
    return user

def require_roles(*roles):
    def dep(user:User=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403,"Insufficient role")
        return user
    return dep

def active_ruleset(db):
    r=db.query(RuleSet).filter(RuleSet.active.is_(True)).order_by(RuleSet.id.desc()).first()
    if not r:
        r=RuleSet(version="v1.0",description="Bootstrap guardrails",rules=DEFAULT_RULES,active=True,created_by="system")
        db.add(r);db.commit();db.refresh(r)
    return r

def evaluate_review(data,rules):
    u=data.users; evaluation="표준"; risk="LOW"; notes=[]
    if u>rules["dedicated_design_threshold"]: evaluation="비표준 / 전용검토";risk="HIGH";notes.append("대규모 사용자: 전용 성능·HA·DR 설계 필요")
    elif data.shape=="단일노드" and u>rules["single_node_max_users"]: evaluation="비표준 / 예외승인";risk="HIGH";notes.append("단일노드 허용 기준 초과")
    elif data.network=="폐쇄망" or data.dr!="없음": evaluation="조건부 표준";risk="MEDIUM"
    if data.service=="ERP + UC" and data.shape=="통합형" and u>rules["integrated_erp_uc_review_threshold"]: evaluation="Architecture Review";risk="MEDIUM";notes.append("ERP+UC 통합 고사용자 구성: 자원경합 검토")
    memo=(data.memo or "").lower()
    if "dmz" in memo or "외부" in memo:
        notes.append("외부 노출: WAF/L7/DNAT/SSL 정책 검토")
        if risk=="LOW": risk="MEDIUM"
    if u<=rules["small_integrated_max_users"]: rec="AP/DB 통합 1대 가능 후보"
    elif u<=500: rec="AP/DB 분리 권장"
    elif u<=1000: rec="2-Node 또는 역할 분리 검토"
    elif rules["ceph_min_users"]<=u<=rules["ceph_max_users"]: rec="3-Node Cluster + Rook-Ceph/NAS 검토"
    else: rec="전용 설계"
    if notes: rec+=" / "+" · ".join(notes)
    return evaluation,risk,rec

def bootstrap():
    Base.metadata.create_all(bind=engine);db=SessionLocal()
    try:
        if not db.query(User).filter(User.username==settings.bootstrap_admin_user).first(): db.add(User(username=settings.bootstrap_admin_user,role="ADMIN"))
        if not db.query(RuleSet).count(): db.add(RuleSet(version="v1.0",description="Bootstrap guardrails",rules=DEFAULT_RULES,active=True,created_by="system"))
        db.commit()
    finally: db.close()
bootstrap()

ROOT=Path(__file__).resolve().parent
app=FastAPI(title="Architecture Center v3",version="3.0.0")
@app.get("/")
def root(): return FileResponse(ROOT/"index.html")
@app.get("/api/health")
def health(): return {"status":"ok","version":"3.0.0","auth":"trusted-header"}
@app.get("/api/me")
def me(user:User=Depends(current_user)): return {"username":user.username,"role":user.role}
@app.get("/api/users")
def users(db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN"))): return [{"id":u.id,"username":u.username,"role":u.role,"active":u.active,"created_at":u.created_at} for u in db.query(User).order_by(User.id).all()]
@app.post("/api/users")
def create_user(body:UserCreateIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN"))):
    if body.role not in {"ADMIN","ARCHITECT","APPROVER","VIEWER"}: raise HTTPException(400,"Invalid role")
    if db.query(User).filter(User.username==body.username).first(): raise HTTPException(409,"Username already exists")
    r=User(username=body.username,role=body.role);db.add(r);db.flush();audit(db,"user",r.id,"CREATE",user.username,{"username":r.username,"role":r.role});db.commit();db.refresh(r);return row_to_dict(r)
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return {"total_reviews":db.query(ArchitectureReview).count(),"pending_approval":db.query(ArchitectureReview).filter(ArchitectureReview.status=="SUBMITTED").count(),"high_risk":db.query(ArchitectureReview).filter(ArchitectureReview.risk_level=="HIGH",ArchitectureReview.status!="CLOSED").count(),"open_risks":db.query(Risk).filter(Risk.status=="OPEN").count(),"active_ruleset":active_ruleset(db).version,"latest":[row_to_dict(r) for r in db.query(ArchitectureReview).order_by(ArchitectureReview.id.desc()).limit(10).all()]}
@app.post("/api/reviews")
def create_review(body:ReviewIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","ARCHITECT"))):
    rs=active_ruleset(db);e,risk,rec=evaluate_review(body,rs.rules);r=ArchitectureReview(**body.model_dump(),evaluation=e,recommendation=rec,risk_level=risk,status="DRAFT",rule_set_version=rs.version,created_by=user.username);db.add(r);db.flush();audit(db,"review",r.id,"CREATE",user.username,{"evaluation":e,"risk":risk,"ruleset":rs.version});db.commit();db.refresh(r);return row_to_dict(r)
@app.get("/api/reviews")
def reviews(db:Session=Depends(get_db),user:User=Depends(current_user)): return [row_to_dict(r) for r in db.query(ArchitectureReview).order_by(ArchitectureReview.id.desc()).all()]

def transition(review_id,action,status,body,db,user):
    r=db.get(ArchitectureReview,review_id)
    if not r: raise HTTPException(404,"Review not found")
    if action=="SUBMIT" and r.status not in ("DRAFT","REJECTED"): raise HTTPException(409,"Review cannot be submitted")
    if action in ("APPROVE","REJECT") and r.status!="SUBMITTED": raise HTTPException(409,"Only submitted reviews can be approved/rejected")
    r.status=status;db.add(Approval(review_id=r.id,action=action,comment=body.comment,actor=user.username));audit(db,"review",r.id,action,user.username,{"comment":body.comment});db.commit();return {"ok":True,"status":r.status}

@app.post("/api/reviews/{review_id}/submit")
def submit(review_id:int,body:ActionIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","ARCHITECT"))): return transition(review_id,"SUBMIT","SUBMITTED",body,db,user)
@app.post("/api/reviews/{review_id}/approve")
def approve(review_id:int,body:ActionIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","APPROVER"))): return transition(review_id,"APPROVE","APPROVED",body,db,user)
@app.post("/api/reviews/{review_id}/reject")
def reject(review_id:int,body:ActionIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","APPROVER"))): return transition(review_id,"REJECT","REJECTED",body,db,user)
@app.get("/api/approvals")
def approvals(db:Session=Depends(get_db),user:User=Depends(current_user)): return [row_to_dict(r) for r in db.query(Approval).order_by(Approval.id.desc()).all()]
@app.post("/api/decisions")
def create_decision(body:DecisionIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","ARCHITECT"))):
    r=DecisionLog(**body.model_dump(),created_by=user.username);db.add(r);db.flush();audit(db,"decision",r.id,"CREATE",user.username,{"topic":r.topic});db.commit();db.refresh(r);return row_to_dict(r)
@app.get("/api/decisions")
def decisions(db:Session=Depends(get_db),user:User=Depends(current_user)): return [row_to_dict(r) for r in db.query(DecisionLog).order_by(DecisionLog.id.desc()).all()]
@app.post("/api/risks")
def create_risk(body:RiskIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","ARCHITECT"))):
    r=Risk(**body.model_dump(),created_by=user.username);db.add(r);db.flush();audit(db,"risk",r.id,"CREATE",user.username,{"title":r.title});db.commit();db.refresh(r);return row_to_dict(r)
@app.get("/api/risks")
def risks(db:Session=Depends(get_db),user:User=Depends(current_user)): return [row_to_dict(r) for r in db.query(Risk).order_by(Risk.id.desc()).all()]
@app.get("/api/rulesets")
def rulesets(db:Session=Depends(get_db),user:User=Depends(current_user)): return [row_to_dict(r) for r in db.query(RuleSet).order_by(RuleSet.id.desc()).all()]
@app.post("/api/rulesets")
def create_ruleset(body:RuleSetIn,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN"))):
    r=RuleSet(**body.model_dump(),active=False,created_by=user.username);db.add(r);db.flush();audit(db,"ruleset",r.id,"CREATE",user.username,{"version":r.version});db.commit();db.refresh(r);return row_to_dict(r)
@app.post("/api/rulesets/{ruleset_id}/activate")
def activate(ruleset_id:int,db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN"))):
    r=db.get(RuleSet,ruleset_id)
    if not r: raise HTTPException(404,"RuleSet not found")
    db.query(RuleSet).update({RuleSet.active:False});r.active=True;audit(db,"ruleset",r.id,"ACTIVATE",user.username,{"version":r.version});db.commit();return {"ok":True,"version":r.version}
@app.get("/api/audit")
def audits(db:Session=Depends(get_db),user:User=Depends(require_roles("ADMIN","APPROVER"))): return [row_to_dict(r) for r in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()]
