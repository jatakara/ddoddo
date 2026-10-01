from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

class Settings(BaseSettings):
    database_url: str = "sqlite:///./architecture_center_v4.db"
    bootstrap_admin_user: str = "admin"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()

connect_args={"check_same_thread":False} if settings.database_url.startswith("sqlite") else {}
engine=create_engine(settings.database_url,pool_pre_ping=True,connect_args=connect_args)
SessionLocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)
Base=declarative_base()
def utcnow(): return datetime.utcnow()
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    username: Mapped[str]=mapped_column(String(80),unique=True,index=True)
    role: Mapped[str]=mapped_column(String(30),default="SALES")
    active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Opportunity(Base):
    __tablename__="opportunities"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    customer: Mapped[str]=mapped_column(String(200),index=True)
    opportunity_name: Mapped[str]=mapped_column(String(220),default="")
    sales_owner: Mapped[str]=mapped_column(String(80),index=True)
    stage: Mapped[str]=mapped_column(String(40),default="DISCOVERY",index=True)
    users: Mapped[int]=mapped_column(Integer,default=0)
    modules: Mapped[list]=mapped_column(JSON,default=list)
    note: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)

class Architecture(Base):
    __tablename__="architectures"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    architecture_id: Mapped[str]=mapped_column(String(40),unique=True,index=True)
    opportunity_id: Mapped[int]=mapped_column(ForeignKey("opportunities.id",ondelete="CASCADE"),index=True)
    workload_class: Mapped[str]=mapped_column(String(20))
    grade: Mapped[str]=mapped_column(String(30),index=True)
    risk_level: Mapped[str]=mapped_column(String(20))
    sizing: Mapped[dict]=mapped_column(JSON)
    network: Mapped[dict]=mapped_column(JSON)
    recommendation: Mapped[str]=mapped_column(Text)
    customer_message: Mapped[str]=mapped_column(Text)
    inputs: Mapped[dict]=mapped_column(JSON)
    status: Mapped[str]=mapped_column(String(30),default="DRAFT",index=True)
    created_by: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class QuoteRequest(Base):
    __tablename__="quote_requests"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    architecture_id: Mapped[str]=mapped_column(String(40),index=True)
    customer: Mapped[str]=mapped_column(String(200))
    requested_by: Mapped[str]=mapped_column(String(80))
    status: Mapped[str]=mapped_column(String(30),default="REQUESTED",index=True)
    note: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Audit(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    entity_type: Mapped[str]=mapped_column(String(40))
    entity_id: Mapped[str]=mapped_column(String(60))
    action: Mapped[str]=mapped_column(String(50))
    actor: Mapped[str]=mapped_column(String(80))
    detail: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class OpportunityIn(BaseModel):
    customer:str=Field(min_length=1,max_length=200)
    opportunity_name:str=""
    sales_owner:str=""
    stage:str="DISCOVERY"
    users:int=Field(ge=0)
    modules:list[str]=[]
    note:str=""

class WizardIn(BaseModel):
    opportunity_id:int
    users:int=Field(ge=0)
    modules:list[str]=[]
    concurrency:int=Field(ge=0,default=0)
    external_access:bool=False
    mobile:bool=False
    network:str="INTERNET"
    availability:str="STANDARD"
    dr:str="BACKUP"
    growth_percent:int=Field(ge=0,default=10)
    data_size_gb:int=Field(ge=0,default=300)

class QuoteIn(BaseModel):
    architecture_id:str
    note:str=""

class UserIn(BaseModel):
    username:str
    role:str

def row(r): return {c.name:getattr(r,c.name) for c in r.__table__.columns}
def audit(db,t,i,a,actor,detail=None): db.add(Audit(entity_type=t,entity_id=str(i),action=a,actor=actor,detail=detail or {}))

def current_user(x_architecture_user:str|None=Header(default=None),db:Session=Depends(get_db)):
    if not x_architecture_user: raise HTTPException(401,"Missing trusted identity header")
    u=db.query(User).filter(User.username==x_architecture_user,User.active.is_(True)).first()
    if not u: raise HTTPException(403,"User is not provisioned")
    return u

def roles(*allowed):
    def dep(u=Depends(current_user)):
        if u.role not in allowed: raise HTTPException(403,"Insufficient role")
        return u
    return dep

def bootstrap():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        if not db.query(User).filter(User.username==settings.bootstrap_admin_user).first():
            db.add(User(username=settings.bootstrap_admin_user,role="ADMIN"))
        db.commit()
    finally: db.close()
bootstrap()

HEAVY={"SCM","생산","ONEAI"}
def design(w:WizardIn):
    score=0
    if w.users>100: score+=1
    if w.users>500: score+=2
    if w.users>1000: score+=2
    score+=sum(2 for m in w.modules if m in HEAVY)
    if w.concurrency and w.users and w.concurrency/max(w.users,1)>=0.3: score+=1
    if w.external_access: score+=1
    if w.availability in ("HA","MISSION_CRITICAL"): score+=2
    if w.dr not in ("NONE","BACKUP"): score+=1
    if w.growth_percent>=30: score+=1
    workload="S" if score<=2 else "M" if score<=5 else "L" if score<=8 else "XL"
    if workload=="S": cpu,mem,disk="16-24 Core","64-128 GB",f"{max(500,w.data_size_gb*2)} GB"; layout="AP/DB 통합 1대 후보"
    elif workload=="M": cpu,mem,disk="24 Core x 2","128-256 GB x 2",f"{max(1000,w.data_size_gb*2)} GB"; layout="AP/DB 분리 권장"
    elif workload=="L": cpu,mem,disk="24-32 Core x 2~3","256 GB x 2~3",f"{max(1500,w.data_size_gb*3)} GB"; layout="2~3 Node 역할 분리"
    else: cpu,mem,disk="32 Core+ x 3 이상","256 GB+ x 3 이상",f"{max(2000,w.data_size_gb*3)} GB"; layout="전용 Architecture Review"
    k8s_nodes=1 if workload=="S" else 2 if workload=="M" else 3
    storage="Local RAID/Backup" if workload in ("S","M") else "Rook-Ceph 또는 NAS"
    needs_l7=w.external_access or w.users>500 or w.availability in ("HA","MISSION_CRITICAL")
    needs_waf=w.external_access or w.mobile
    needs_dmz=w.external_access
    grade="STANDARD"; risk="LOW"
    reasons=[]
    if workload=="XL": grade="NONSTANDARD";risk="HIGH";reasons.append("대규모/고부하 전용설계")
    elif w.external_access or w.dr not in ("NONE","BACKUP") or w.availability in ("HA","MISSION_CRITICAL"):
        grade="CONDITIONAL";risk="MEDIUM";reasons.append("보안/가용성 조건 확인 필요")
    if "생산" in w.modules or "SCM" in w.modules: reasons.append("업무부하로 AP/DB 분리 우선")
    if w.users<=100 and not HEAVY.intersection(w.modules) and w.availability=="STANDARD": layout="AP/DB 통합 1대 가능"
    evidence_ids=[]
    issue_ids=[]
    if w.users<=100: evidence_ids.append("SIZE-001")
    elif w.users<=500: evidence_ids.append("SIZE-002")
    elif w.users<=1000: evidence_ids.append("SIZE-003")
    elif w.users<=1500: evidence_ids.append("SIZE-004")
    else: evidence_ids.append("SIZE-005")
    evidence_ids.extend(["ERP-001","DR-001"])
    if "UC" in w.modules:
        evidence_ids.extend(["UC-003","NET-002"])
        issue_ids.append("ISSUE-L7-PORT-001")
        if w.users<=300: evidence_ids.append("UC-001")
        elif 400<=w.users<=800: evidence_ids.append("UC-002")
    if "ONEAI" in w.modules:
        evidence_ids.append("ONEAI-001")
        issue_ids.append("ISSUE-ONEAI-SSE-001")
    if w.external_access:
        evidence_ids.extend(["NET-001","NET-004"])
        issue_ids.extend(["ISSUE-SPLIT-DNS-001","ISSUE-L7-PORT-001"])
    if k8s_nodes>=2:
        evidence_ids.append("NET-003")
        issue_ids.append("ISSUE-SERVICE-IP-001")
    if w.users>=1001:
        evidence_ids.append("STO-001")
        issue_ids.append("ISSUE-CEPH-2NODE-001")
    if w.dr not in ("NONE","BACKUP"):
        evidence_ids.append("DR-002")
        issue_ids.append("ISSUE-BACKUP-RESTORE-001")
    if "SCM" in w.modules or "생산" in w.modules:
        issue_ids.append("ISSUE-NFS-IO-001")
    evidence_ids=list(dict.fromkeys(evidence_ids))
    issue_ids=list(dict.fromkeys(issue_ids))
    sizing={"cpu":cpu,"memory":mem,"disk":disk,"layout":layout,"k8s_nodes":k8s_nodes,"storage":storage,"evidence_ids":evidence_ids,"known_issue_ids":issue_ids}
    network={"l7":needs_l7,"waf":needs_waf,"dmz":needs_dmz,"firewall":True}
    rec=f"{layout}; K8s {k8s_nodes} Node; {storage}"
    if reasons: rec += " / " + " · ".join(reasons)
    customer=f"현재 입력 조건 기준 {grade} 구성입니다. 권장 구성은 {layout}이며, 예상 자원은 CPU {cpu}, Memory {mem}, Storage {disk} 수준입니다."
    if needs_waf: customer += " 외부/모바일 접속이 있어 WAF 및 SSL 정책 확인이 필요합니다."
    return workload,grade,risk,sizing,network,rec,customer

ROOT=Path(__file__).resolve().parent
app=FastAPI(title="Architecture Center v4",version="4.0.0")
@app.get("/")
def root(): return FileResponse(ROOT/"index.html")
@app.get("/manifest.webmanifest")
def manifest(): return FileResponse(ROOT/"manifest.webmanifest",media_type="application/manifest+json")
@app.get("/sw.js")
def sw(): return FileResponse(ROOT/"sw.js",media_type="application/javascript")
@app.get("/knowledge-base.json")
def knowledge_base(): return FileResponse(ROOT/"knowledge-base.json",media_type="application/json")
@app.get("/known-issues.json")
def known_issues(): return FileResponse(ROOT/"known-issues.json",media_type="application/json")
@app.get("/api/health")
def health(): return {"status":"ok","version":"4.0.0"}
@app.get("/api/me")
def me(u=Depends(current_user)): return {"username":u.username,"role":u.role}
@app.get("/api/users")
def users(db:Session=Depends(get_db),u=Depends(roles("ADMIN"))): return [row(x) for x in db.query(User).order_by(User.username).all()]
@app.post("/api/users")
def add_user(body:UserIn,db:Session=Depends(get_db),u=Depends(roles("ADMIN"))):
    if body.role not in {"ADMIN","SALES","ARCHITECT","APPROVER","VIEWER"}: raise HTTPException(400,"Invalid role")
    if db.query(User).filter(User.username==body.username).first(): raise HTTPException(409,"Exists")
    x=User(username=body.username,role=body.role);db.add(x);db.flush();audit(db,"user",x.id,"CREATE",u.username,{"role":x.role});db.commit();db.refresh(x);return row(x)
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db),u=Depends(current_user)):
    qs=db.query(QuoteRequest)
    return {"opportunities":db.query(Opportunity).count(),"architectures":db.query(Architecture).count(),"quote_requests":qs.filter(QuoteRequest.status=="REQUESTED").count(),"needs_review":db.query(Architecture).filter(Architecture.grade!="STANDARD",Architecture.status!="APPROVED").count(),"my_work":[row(x) for x in db.query(Opportunity).filter(Opportunity.sales_owner==u.username).order_by(Opportunity.id.desc()).limit(8).all()]}
@app.get("/api/opportunities")
def opportunities(db:Session=Depends(get_db),u=Depends(current_user)): return [row(x) for x in db.query(Opportunity).order_by(Opportunity.id.desc()).all()]
@app.post("/api/opportunities")
def create_opp(body:OpportunityIn,db:Session=Depends(get_db),u=Depends(roles("ADMIN","SALES","ARCHITECT"))):
    data=body.model_dump();data["sales_owner"]=data["sales_owner"] or u.username
    x=Opportunity(**data);db.add(x);db.flush();audit(db,"opportunity",x.id,"CREATE",u.username);db.commit();db.refresh(x);return row(x)
@app.post("/api/architectures")
def create_arch(body:WizardIn,db:Session=Depends(get_db),u=Depends(roles("ADMIN","SALES","ARCHITECT"))):
    opp=db.get(Opportunity,body.opportunity_id)
    if not opp: raise HTTPException(404,"Opportunity not found")
    workload,grade,risk,sizing,network,rec,msg=design(body)
    seq=db.query(Architecture).count()+1
    aid=f"ARC-{datetime.utcnow().strftime('%Y%m%d')}-{seq:04d}"
    x=Architecture(architecture_id=aid,opportunity_id=opp.id,workload_class=workload,grade=grade,risk_level=risk,sizing=sizing,network=network,recommendation=rec,customer_message=msg,inputs=body.model_dump(),status="DRAFT",created_by=u.username)
    db.add(x);db.flush();audit(db,"architecture",aid,"CREATE",u.username,{"grade":grade,"workload":workload});db.commit();db.refresh(x);return row(x)
@app.get("/api/architectures")
def architectures(db:Session=Depends(get_db),u=Depends(current_user)): return [row(x) for x in db.query(Architecture).order_by(Architecture.id.desc()).all()]
@app.post("/api/quotes")
def quote(body:QuoteIn,db:Session=Depends(get_db),u=Depends(roles("ADMIN","SALES","ARCHITECT"))):
    a=db.query(Architecture).filter(Architecture.architecture_id==body.architecture_id).first()
    if not a: raise HTTPException(404,"Architecture ID not found")
    opp=db.get(Opportunity,a.opportunity_id)
    q=QuoteRequest(architecture_id=a.architecture_id,customer=opp.customer,requested_by=u.username,note=body.note)
    db.add(q);a.status="QUOTE_REQUESTED";db.flush();audit(db,"quote",q.id,"REQUEST",u.username,{"architecture_id":a.architecture_id});db.commit();db.refresh(q);return row(q)
@app.get("/api/quotes")
def quotes(db:Session=Depends(get_db),u=Depends(current_user)): return [row(x) for x in db.query(QuoteRequest).order_by(QuoteRequest.id.desc()).all()]
