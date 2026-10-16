"""擋下的規則、狀態（P1）、權限與客戶隔離（D-06、R52），以及事件紀錄與版本（P1、P2、P5）。"""
from datetime import datetime, timedelta, timezone

from tests.conftest import make_org
from tests.test_gc01 import START, uc01


def _hire(api, org, decided="2026-02-16", **extra):
    return api("decideHire", org["hr"], expect=201, json={
        "employer_id": str(org["employer"]), "decided_on": decided, "planned_start_date": START,
        "person": {"person": {"legal_name": "測試", "birth_date": "1990-01-01",
                              "nationalities": [{"country_code": "TW", "acquired_on": "1990-01-01"}]}}, **extra}).json()


def _start(api, org, hire_id, **extra):
    return api("startEmployment", org["hr"], path={"id": hire_id},
               json={"start_date": START, "work_location_id": str(org["location"]),
                     "public_or_military_insurance_covered": False, **extra})


def test_r01_start_before_decision_blocked(api, org):
    hire = _hire(api, org)
    r = _start(api, org, hire["hire_id"], start_date="2026-02-01")
    assert r.status_code == 409 and r.json()["rule_id"] == "R01"


def test_p1_cannot_start_twice(api, org):
    hire = _hire(api, org)
    assert _start(api, org, hire["hire_id"]).status_code == 201
    r = _start(api, org, hire["hire_id"])
    assert r.status_code == 409 and r.json()["message_code"] == "INVALID_STATE"


def test_r05_duplicate_employee_number_blocked(api, org):
    hire = _hire(api, org)
    r = _start(api, org, hire["hire_id"], employee_number="E001")
    assert r.status_code == 409 and r.json()["rule_id"] == "R05"


def test_r11_warns_at_hire_but_does_not_block(api, org):
    hire = _hire(api, org, compensation={"effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
                                         "monthly_base_salary": "29000"})
    [w] = [w for w in hire["warnings"] if w["rule_id"] == "R11"]
    assert w["message_code"] == "BELOW_MINIMUM_WAGE" and w["subject"]["id"] == hire["compensation_id"]
    assert w["warned_value"]["minimum_wage_rule"]["version"] == "v2026"


def test_r21_warns_without_compensation_and_contract(api, org):
    hire = _hire(api, org)
    started = _start(api, org, hire["hire_id"]).json()
    assert {w["message_code"] for w in started["warnings"] if w["rule_id"] == "R21"} == {"MISSING_COMPENSATION", "MISSING_CONTRACT"}


def test_person_ref_exactly_one(api, org):
    r = api("decideHire", org["hr"], json={"employer_id": str(org["employer"]), "decided_on": "2026-02-16",
                                           "planned_start_date": START, "person": {}})
    assert r.status_code == 422


def test_rehire_reuses_person(api, org):
    first = _hire(api, org)
    again = api("decideHire", org["hr"], expect=201, json={
        "employer_id": str(org["employer"]), "decided_on": "2026-02-20", "planned_start_date": START,
        "person": {"person_id": first["person_id"]}}).json()
    assert again["person_id"] == first["person_id"]


def test_r50_and_r07_blocked(api, org, ref):
    _, _, started = uc01(api, org, ref)
    base = {"employment_id": started["employment_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
            "filed_on": START, "voluntary": False}
    r = api("recordInsuranceFiling", org["hr"], json=base | {"insurance_unit_id": str(org["units"]["BLI"])})
    assert r.status_code == 409 and r.json()["rule_id"] == "R50"
    r = api("recordInsuranceFiling", org["hr"], json=base | {"insurance_unit_id": str(org["units"]["NHIA"]), "no_receipt": True})
    assert r.status_code == 409 and r.json()["message_code"] == "UNIT_SCHEME_NOT_COVERED"
    r = api("recordInsuranceFiling", org["hr"], json=base | {"no_receipt": True})
    assert r.status_code == 409 and r.json()["message_code"] == "UNIT_REQUIRED"


def test_r31_late_filing_effective_next_day(api, org, ref):
    _, _, started = uc01(api, org, ref)
    api("recordInsuranceFiling", org["hr"], expect=201, json={
        "employment_id": started["employment_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
        "insurance_unit_id": str(org["units"]["BLI"]), "filed_on": "2026-03-05", "voluntary": False, "no_receipt": True})
    appl = api("getApplicability", org["hr"], path={"id": started["employment_id"]}, params={"on": START}).json()
    [li] = [i for i in appl["items"] if i["scheme_code"] == "SCHEME.LABOR_INSURANCE_TW"]
    assert li["days_late"] == 4        # 實際生效日 3/6（翌日，R31）− 法定生效日 3/2


def test_r61_filed_before_start_warns(api, org, ref):
    _, _, started = uc01(api, org, ref)
    r = api("recordInsuranceFiling", org["hr"], expect=201, json={
        "employment_id": started["employment_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
        "insurance_unit_id": str(org["units"]["BLI"]), "filed_on": "2026-03-01", "voluntary": False, "no_receipt": True})
    assert [w["rule_id"] for w in r.json()["warnings"]] == ["R61"]


def test_r45_grade_mismatch_warns(api, org, ref):
    _, _, started = uc01(api, org, ref)
    enr = api("recordInsuranceFiling", org["hr"], expect=201, json={
        "employment_id": started["employment_id"], "scheme_id": str(ref["schemes"]["SCHEME.LABOR_INSURANCE_TW"]),
        "insurance_unit_id": str(org["units"]["BLI"]), "filed_on": START, "voluntary": False, "no_receipt": True}).json()
    r = api("declareInsuredSalary", org["hr"], path={"id": enr["enrollment_id"]}, expect=201, json={
        "declared_amount": "29500", "grade": "1", "declared_on": START, "effective_from": START})
    assert [w["rule_id"] for w in r.json()["warnings"]] == ["R45"]


def test_roles_and_tenant_isolation(api, org, ref, db):
    body = {"employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
            "person": {"person": {"legal_name": "x"}}}
    assert api("decideHire", org["boss"], json=body).status_code == 403                 # 雇主不能錄用
    assert api("listEnrollmentProposals", org["boss"]).status_code == 200               # 雇主可以讀加保待辦
    other = make_org(db, ref, name="另一家", existing_employees=0)
    assert api("decideHire", other["hr"], json=body).status_code == 403                 # 別的客戶的雇主
    assert api("decideHire", {}, json=body).status_code == 403                          # 沒有 token
    hire = _hire(api, org)
    assert api("recordIdentityDocument", other["hr"], path={"id": hire["person_id"]}, json={
        "document_kind": "DOCUMENT_KIND.NATIONAL_ID_TW", "issuing_jurisdiction_id": str(ref["tw"]),
        "document_number": "B1", "valid_from": "2015-01-01"}).status_code == 403          # 別的客戶的人


def test_unimplemented_returns_501(api, org):
    r = api("cancelHire", org["hr"], path={"id": "0" * 24}, json={})
    assert r.status_code == 501 and r.json()["x-concept"] == "CancelHire"


def test_events_and_versions_recorded(api, org, ref, db):
    hire, _, started = uc01(api, org, ref)
    types = [e["type"] for e in db.events.find({"tenant_id": org["tenant"]}).sort("recorded_at", 1)]
    assert types == ["DecideHire", "ProposeEnrollmentFiling", "RecordIdentityDocument",
                     "StartEmployment", "ProposeEnrollmentFiling"]
    # P2 B：Hire 狀態改變、契約接續到僱傭關係，都留下變更紀錄
    assert db.change_log.find_one({"tenant_id": org["tenant"], "collection": "hires", "fields": ["status"]})
    assert db.change_log.find_one({"tenant_id": org["tenant"], "collection": "employment_contracts", "fields": ["employment_id"]})
    # P2 A：約定薪資接續到僱傭關係是新版本，舊版本保留
    from bson import ObjectId
    revs = sorted(c["revision"] for c in db.compensations.find({"entity_id": ObjectId(hire["compensation_id"])}))
    assert revs == [1, 2]
    # P5：加保待辦記下依據的規則版本
    prop = db.enrollment_proposals.find_one({"_id": ObjectId(started["enrollment_proposal_id"])})
    assert {"rule_id": "R40", "version": "v2026", "revision": 1} in prop["basis"]["rule_versions"]


def test_applicability_as_of_before_start_has_no_employment(api, org, ref):
    before = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    _, _, started = uc01(api, org, ref)
    r = api("getApplicability", org["hr"], path={"id": started["employment_id"]}, params={"on": START, "as_of": before})
    assert r.status_code == 404
