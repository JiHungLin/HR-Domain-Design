"""擋下的規則、狀態（P1）、權限與客戶隔離（D-06、R52），以及事件紀錄與版本（P1、P2）。"""
from datetime import date

from tests.conftest import make_org
from tests.test_gc01 import START, gc01_flow


def _hire(client, org, ref, decided="2026-02-16", start=START):
    r = client.post("/v1/hires", headers=org["hr"], json={
        "employer_id": str(org["employer"]), "decided_on": decided, "planned_start_date": start,
        "person": {"legal_name": "測試", "birth_date": "1990-01-01",
                   "nationalities": [{"country_code": "TW", "acquired_on": "1990-01-01"}]}})
    assert r.status_code == 201, r.text
    return r.json()


def test_r01_start_before_decision_blocked(client, org, ref):
    hire = _hire(client, org, ref)
    r = client.post(f"/v1/hires/{hire['entity_id']}/start", headers=org["hr"], json={"start_date": "2026-02-01"})
    assert r.status_code == 409 and r.json()["rule_id"] == "R01"


def test_p1_cannot_start_twice(client, org, ref):
    hire = _hire(client, org, ref)
    assert client.post(f"/v1/hires/{hire['entity_id']}/start", headers=org["hr"], json={"start_date": START}).status_code == 201
    r = client.post(f"/v1/hires/{hire['entity_id']}/start", headers=org["hr"], json={"start_date": START})
    assert r.status_code == 409 and r.json()["message_code"] == "INVALID_STATE"


def test_r05_duplicate_employee_number_blocked(client, org, ref):
    hire = _hire(client, org, ref)
    r = client.post(f"/v1/hires/{hire['entity_id']}/start", headers=org["hr"], json={"start_date": START, "employee_number": "E001"})
    assert r.status_code == 409 and r.json()["rule_id"] == "R05"


def test_minimum_wage_warns_but_does_not_block(client, org, ref):
    hire = _hire(client, org, ref)
    r = client.post("/v1/compensations", headers=org["hr"], json={
        "hire_id": hire["entity_id"], "effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
        "monthly_base_salary": "29000"})
    assert r.status_code == 201
    assert [w["rule_id"] for w in r.json()["warnings"]] == ["R11"]
    assert r.json()["warnings"][0]["rule_version"] == "v2026"


def test_r50_and_r07_blocked(client, org, ref, db):
    _, started, _ = gc01_flow(client, org, ref)
    base = {"employment_id": started["entity_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
            "filed_on": START}
    r = client.post("/v1/insurance-enrollments", headers=org["hr"], json=base | {"insurance_unit_id": str(org["units"]["BLI"])})
    assert r.status_code == 409 and r.json()["rule_id"] == "R50"
    r = client.post("/v1/insurance-enrollments", headers=org["hr"], json=base | {"insurance_unit_id": str(org["units"]["NHIA"]), "no_receipt": True})
    assert r.status_code == 409 and r.json()["message_code"] == "UNIT_SCHEME_NOT_COVERED"


def test_r31_late_filing_effective_next_day(client, org, ref):
    _, started, _ = gc01_flow(client, org, ref)
    r = client.post("/v1/insurance-enrollments", headers=org["hr"], json={
        "employment_id": started["entity_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
        "insurance_unit_id": str(org["units"]["BLI"]), "filed_on": "2026-03-05", "no_receipt": True})
    assert r.status_code == 201
    assert r.json()["effective_from"] == "2026-03-06" and r.json()["days_late"] == 4


def test_roles_and_tenant_isolation(client, org, ref, db):
    body = {"employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
            "person": {"legal_name": "x"}}
    assert client.post("/v1/hires", headers=org["boss"], json=body).status_code == 403          # 雇主不能錄用
    assert client.get("/v1/enrollment-proposals", headers=org["boss"]).status_code == 200       # 雇主可以讀加保待辦
    other = make_org(db, ref, name="另一家", existing_employees=0)
    assert client.post("/v1/hires", headers=other["hr"], json=body).status_code == 403          # 別的客戶的雇主
    assert client.post("/v1/hires", json=body).status_code == 403                                # 沒有 token


def test_unimplemented_returns_501(client, org):
    r = client.post("/v1/hires/x/cancel", headers=org["hr"], json={})
    assert r.status_code == 501 and r.json()["x-concept"] == "CancelHire"


def test_events_and_versions_recorded(client, org, ref, db):
    hire, started, _ = gc01_flow(client, org, ref)
    types = [e["type"] for e in db.events.find({"tenant_id": org["tenant"]}).sort("recorded_at", 1)]
    assert types == ["DecideHire", "RecordIdentityDocument", "AgreeCompensation", "SignContract",
                     "StartEmployment", "ProposeEnrollmentFiling"]
    # P2 B：Hire 狀態改變留下變更紀錄
    assert db.change_log.find_one({"collection": "hires", "fields": ["status"]})
    # P5：加保待辦記下依據的規則版本
    prop = db.enrollment_proposals.find_one({"tenant_id": org["tenant"]})
    assert {"rule_id": "R40", "version": "v2026", "revision": 1} in prop["basis"]["rule_versions"]


def test_applicability_as_of_before_start_has_no_employment(client, org, ref):
    from datetime import datetime, timedelta, timezone
    before = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    _, started, _ = gc01_flow(client, org, ref)
    r = client.get(f"/v1/employments/{started['entity_id']}/applicability", headers=org["hr"],
                   params={"on": START, "as_of": before})
    assert r.status_code == 404
