"""測試在真的 MongoDB（replica set）上跑：每次建立一個獨立的測試資料庫，跑完刪掉。"""
import os
import uuid
from datetime import date

import pytest

os.environ.setdefault("HR_DB_NAME", f"hr_test_{uuid.uuid4().hex[:8]}")

from fastapi.testclient import TestClient  # noqa: E402

from app import config, seed  # noqa: E402
from app.db import database, now, to_dt  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def db():
    seed.init(config.DB_NAME, reset=True)
    d = database()
    yield d
    d.client.drop_database(config.DB_NAME)


@pytest.fixture(scope="session")
def client(db):
    return TestClient(app)


@pytest.fixture(scope="session")
def ref(db):
    """參考資料的編號。"""
    return {"tw": db.jurisdictions.find_one({"code": "TW"})["_id"],
            "schemes": {s["code"]: s["_id"] for s in db.social_insurance_schemes.find()}}


def make_org(db, ref, *, name="飲料公司", existing_employees=12, lsa=True,
             category="LI_INDUSTRY.LIA6_02_TW", registered_on=date(2018, 5, 1)):
    """org-setup 提供的資料 [靜態替代]：客戶、雇主、投保單位、帳號，以及既有在職員工。"""
    ts = now()
    tenant = db.tenants.insert_one({"name": name, "created_at": ts}).inserted_id
    employer = db.employers.insert_one({
        "tenant_id": tenant, "legal_name": name, "employer_type": "EMPLOYER_TYPE.COMPANY", "jurisdiction_id": ref["tw"],
        "registrations": [{"kind": "REGISTRATION_KIND.COMPANY_TW", "registered_on": to_dt(registered_on)}],
        "labor_insurance_industry_category": [{"code": category, "from": to_dt(registered_on)}],
        "labor_standards_act_applicable": [{"value": lsa, "from": to_dt(registered_on)}],
        "system_managed_from": to_dt(date(2026, 1, 1)), "created_at": ts}).inserted_id
    location = db.work_locations.insert_one({"tenant_id": tenant, "name": "總店", "jurisdiction_id": ref["tw"],
                                             "created_at": ts}).inserted_id
    units = {
        "BLI": db.insurance_units.insert_one({
            "tenant_id": tenant, "employer_id": employer, "insurer": "INSURER.BLI_TW", "unit_code": f"BLI-{tenant}",
            "scheme_codes": [seed.LI, seed.EI, seed.OAI, seed.LP], "created_at": ts}).inserted_id,
        "NHIA": db.insurance_units.insert_one({
            "tenant_id": tenant, "employer_id": employer, "insurer": "INSURER.NHIA_TW", "unit_code": f"NHI-{tenant}",
            "scheme_codes": [seed.NHI], "created_at": ts}).inserted_id,
    }
    hr_user, employer_user = f"hr-{tenant}", f"boss-{tenant}"
    db.user_accounts.insert_many([
        {"tenant_id": tenant, "user_id": hr_user, "roles": ["HR"], "created_at": ts},
        {"tenant_id": tenant, "user_id": employer_user, "roles": ["EMPLOYER"], "created_at": ts}])
    from bson import ObjectId
    for i in range(existing_employees):
        pid = ObjectId()
        db.persons.insert_one({"tenant_id": tenant, "entity_id": pid, "revision": 1, "is_current": True,
                               "recorded_at": ts, "legal_name": f"既有員工{i + 1}", "created_at": ts})
        db.employments.insert_one({
            "tenant_id": tenant, "entity_id": ObjectId(), "revision": 1, "is_current": True, "recorded_at": ts,
            "person_id": pid, "employer_id": employer, "start_date": to_dt(date(2020, 1, 1)),
            "employee_number": f"E{i + 1:03d}", "status": "Active", "annulled": False, "created_at": ts})
    return {"tenant": tenant, "employer": employer, "units": units, "location": location,
            "hr": {"Authorization": f"Bearer {hr_user}"}, "boss": {"Authorization": f"Bearer {employer_user}"}}


@pytest.fixture
def org(db, ref):
    return make_org(db, ref)


class Api:
    """依 operationId 呼叫 API；成功的回應一律用 api.yaml 的回應格式檢查（05_mapping D-18）。"""

    def __init__(self, client):
        self.client = client

    def __call__(self, op_id: str, headers: dict, *, path: dict | None = None, json=None, params=None, expect=None):
        from app import spec
        method, template, op = spec.operations()[op_id]
        url = template.format(**(path or {}))
        r = self.client.request(method.upper(), url, headers=headers, json=json, params=params)
        if expect is not None:
            assert r.status_code == expect, r.text
        if 200 <= r.status_code < 300:
            errs = spec.errors(spec.response_schema(op_id, r.status_code), r.json())
            assert not errs, (op_id, errs)
        return r


@pytest.fixture(scope="session")
def api(client):
    return Api(client)
