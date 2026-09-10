from __future__ import annotations
import csv
from datetime import date
from pathlib import Path
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db, make_engine
from backend.loader import DataValidationError, load_canonical_dataset
from backend.main import create_app
from backend.models import Alert, Prediction, Project, ProjectSnapshot, SourceReport

class FakeAssistant:
    def answer(self,db,request_id,question,project_id):
        from backend.assistant_service import build_authoritative_evidence
        evidence=build_authoritative_evidence(db,project_id) if project_id else None
        return {"request_id":request_id,"route":"PROJECT_EVIDENCE" if project_id else "DOCUMENT_RAG","answer":{"answer":"bounded","evidence":evidence},"project_evidence_references":[project_id] if project_id else [],"document_citations":[],"reliability_statement":None,"limitations":[],"fallback_used":False,"fallback_reason":None,"model_version":"fake","rag_index_version":"test","latency_metadata":{"total_seconds":0.0}}

@pytest.fixture
def db_setup(tmp_path):
    engine=make_engine(f"sqlite:///{(tmp_path/'test.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine,expire_on_commit=False)
    with Session.begin() as db:
        db.add_all([Project(canonical_project_id="PRH-1",project_code="1",canonical_name="Alpha Road",agency="NHAI",ministry="Roads",sector="Road",state="Delhi",identity_method="EXACT",identity_status="RESOLVED_EXACT"),SourceReport(reporting_month=date(2026,1,1),source_id="SRC-1",coverage_class="PROJECT_LEVEL",source_present=True,project_level_usable=True,official_project_count=1,schema_family="PAIMANA_V2",source_quality_status="PASS",sha256="a"*64),SourceReport(reporting_month=date(2026,2,1),source_id="SRC-2",coverage_class="AGGREGATE_ONLY",source_present=True,project_level_usable=False,official_project_count=None,schema_family="NO_PROJECT_LEVEL_SCHEMA",source_quality_status="PASS",sha256="b"*64),SourceReport(reporting_month=date(2026,3,1),source_id=None,coverage_class="MISSING_SOURCE",source_present=False,project_level_usable=False,official_project_count=None,schema_family=None,source_quality_status="MISSING",sha256=None),ProjectSnapshot(canonical_project_id="PRH-1",reporting_month=date(2026,1,1),agency="NHAI",project_observation_count=1,months_since_first_observation=0,progress_current=20.0,raw_features={})])
    app=create_app(FakeAssistant())
    def override():
        with Session() as db:yield db
    app.dependency_overrides[get_db]=override
    return app,Session

@pytest.fixture
def client(db_setup):
    with TestClient(db_setup[0]) as c:yield c

def test_health(client): assert client.get("/api/v1/health").json()["database"]=="available"
def test_project_list_pagination(client):
    data=client.get("/api/v1/projects?page=1&page_size=1").json();assert data["total"]==1 and len(data["items"])==1
def test_project_list_search(client): assert client.get("/api/v1/projects?search=Alpha").json()["total"]==1
def test_project_list_filter(client): assert client.get("/api/v1/projects?sector=Rail").json()["total"]==0
def test_project_list_rejects_bad_sort(client): assert client.get("/api/v1/projects?sort=drop_table").status_code==422
def test_project_detail(client): assert client.get("/api/v1/projects/PRH-1").json()["latest_snapshot"]["source"]["source_id"]=="SRC-1"
def test_missing_project(client): assert client.get("/api/v1/projects/NOPE").status_code==404
def test_history_only_observed_rows(client):
    data=client.get("/api/v1/projects/PRH-1/history").json();assert len(data["observations"])==1 and data["interpolated"] is False
def test_history_exposes_unavailable_months(client):
    classes={x["coverage_class"] for x in client.get("/api/v1/projects/PRH-1/history").json()["unavailable_months"]};assert classes=={"AGGREGATE_ONLY","MISSING_SOURCE"}
def test_prediction_unavailable_is_null(client): assert client.get("/api/v1/projects/PRH-1/prediction").json() is None
def test_dashboard_separates_predictions_alerts(client):
    data=client.get("/api/v1/dashboard/summary").json();assert data["predictions"]==0 and data["alerts"]==0
def test_review_queue_fail_closed_without_fake_risk(client):
    data=client.get("/api/v1/review-queue").json();assert data["status"]=="ACTIVE_WITH_PREDICTIONS_WITHHELD" and data["items"][0]["review_state"]=="DATA_VERIFICATION_REQUIRED" and data["items"][0]["priority"] is None
def test_assistant_rejects_authoritative_fields(client): assert client.post("/api/v1/assistant/query",json={"request_id":"r1","question":"Explain this project","risk_band":"HIGH"}).status_code==422
def test_assistant_evidence_built_server_side(client):
    data=client.post("/api/v1/assistant/query",json={"request_id":"r1","question":"Explain this project","canonical_project_id":"PRH-1"}).json();assert data["answer"]["evidence"]["prediction_status"]=="WITHHELD"
def test_assistant_cannot_expose_prediction_when_data_trust_withholds(client,db_setup):
    _,Session=db_setup
    with Session.begin() as db:
        db.add(Prediction(prediction_id="available",canonical_project_id="PRH-1",as_of_month=date(2026,1,1),target="S1",horizon_months=3,prediction_status="AVAILABLE",probability=.99,risk_band="HIGH",reliability_band="HIGH",model_version="test-only",feature_version="Compact-V2",target_version="S1-v1"))
    evidence=client.post("/api/v1/assistant/query",json={"request_id":"trust-guard","question":"Explain this project","canonical_project_id":"PRH-1"}).json()["answer"]["evidence"]
    assert evidence["prediction_status"]=="WITHHELD" and evidence["calibrated_probability"] is None and evidence["risk_band"] is None and "HUMAN_TARGET_VALIDATION_PENDING" in evidence["prediction_eligibility"]["reason_codes"] and "HUMAN_TARGET_VALIDATION_PENDING" not in evidence["data_trust_reason_codes"] and evidence["review_decision"]["review_state"]!='REVIEW_RECOMMENDED'
    api_prediction=client.get('/api/v1/projects/PRH-1/prediction').json();assert api_prediction['prediction_status']=='WITHHELD' and api_prediction['probability'] is None and api_prediction['risk_band'] is None
def test_review_queue_does_not_create_alert_rows(client,db_setup):
    _,Session=db_setup;client.get('/api/v1/review-queue')
    with Session() as db:assert db.scalar(select(func.count()).select_from(Alert))==0
def test_assistant_document_route(client): assert client.post("/api/v1/assistant/query",json={"request_id":"r2","question":"What is PAIMANA?"}).status_code==200
def test_assistant_missing_project(client): assert client.post("/api/v1/assistant/query",json={"request_id":"r3","question":"Explain this project","canonical_project_id":"NOPE"}).status_code==404
def test_invalid_assistant_question(client): assert client.post("/api/v1/assistant/query",json={"request_id":"bad space","question":" "}).status_code==422
def test_disabled_assistant(db_setup):
    _,Session=db_setup;disabled=create_app(None)
    def override():
        with Session() as db:yield db
    disabled.dependency_overrides[get_db]=override
    with TestClient(disabled) as c:assert c.post("/api/v1/assistant/query",json={"request_id":"r","question":"hello there"}).status_code==503

def _write(path,fields,rows):
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def _loader_files(root:Path,bad=False):
    root.mkdir();_write(root/"project_master.csv",["canonical_project_id","canonical_name","identity_method","identity_status"],[{"canonical_project_id":"P1","canonical_name":"One","identity_method":"EXACT","identity_status":"RESOLVED_EXACT"}]);_write(root/"report_month.csv",["reporting_month","coverage_class","source_id","source_present","project_level_usable","official_project_count","schema_family","source_quality_status"],[{"reporting_month":"2026-01","coverage_class":"PROJECT_LEVEL","source_id":"S1","source_present":"TRUE","project_level_usable":"TRUE","official_project_count":"1","schema_family":"X","source_quality_status":"PASS"}]);_write(root/"project_month.csv",["canonical_project_id","reporting_month","reported_physical_progress","reported_cumulative_expenditure","reported_agency","reported_state","sector_raw"],[{"canonical_project_id":"BAD" if bad else "P1","reporting_month":"2026-01","reported_physical_progress":"10","reported_cumulative_expenditure":"1,200.5","reported_agency":"Agency","reported_state":"State","sector_raw":"Road"}])
def test_loader_idempotency(tmp_path):
    engine=make_engine(f"sqlite:///{(tmp_path/'l.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine);folder=tmp_path/"data";_loader_files(folder)
    with Session() as db:
        first=load_canonical_dataset(db,folder);second=load_canonical_dataset(db,folder);assert first["status"]=="LOADED" and second["status"]=="ALREADY_LOADED" and db.scalar(select(func.count()).select_from(ProjectSnapshot))==1
def test_loader_validation_rolls_back(tmp_path):
    engine=make_engine(f"sqlite:///{(tmp_path/'r.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine);folder=tmp_path/"bad";_loader_files(folder,True)
    with Session() as db:
        with pytest.raises(DataValidationError):load_canonical_dataset(db,folder)
        assert db.scalar(select(func.count()).select_from(Project))==0
def test_abstention_constraint(db_setup):
    _,Session=db_setup
    with Session() as db:
        db.add(Prediction(prediction_id="x",canonical_project_id="PRH-1",as_of_month=date(2026,1,1),target="S1",horizon_months=3,prediction_status="ABSTAIN",probability=.9,risk_band="HIGH",reliability_band="ABSTAIN",model_version="m",feature_version="f",target_version="t"))
        with pytest.raises(Exception):db.commit()
def test_loader_excludes_ml_derived_fields(tmp_path):
    engine=make_engine(f"sqlite:///{(tmp_path/'s.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine);folder=tmp_path/"source";_loader_files(folder)
    with Session() as db:
        load_canonical_dataset(db,folder);row=db.scalar(select(ProjectSnapshot));assert row.progress_current==10 and row.expenditure_current==1200.5 and row.progress_velocity is None and row.cost_ratio is None and row.raw_features=={}
def test_alembic_accepts_percent_encoded_database_url():
    url="postgresql+psycopg://app:example%40123@localhost/prahari";config=Config();config.set_main_option("sqlalchemy.url",url.replace("%","%%"));assert config.get_main_option("sqlalchemy.url")==url
def test_prediction_and_alert_are_distinct_tables(): assert Prediction.__table__.name != Alert.__table__.name
