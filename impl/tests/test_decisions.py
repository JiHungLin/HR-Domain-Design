"""04 的回頭修改：公教或軍保（D-15）、待人判斷（D-16、D-19、D-20）、逾期（D-17）、錄用時的預估（D-18）。"""
from datetime import date, timedelta

from bson import ObjectId

from app.db import now, to_dt
from app.leave import clock
from tests.conftest import make_org
from tests.test_applicability import EI, LI, LP, M, NA, OAI, START, national

NEEDS = "APPLICABILITY.NEEDS_DECISION"
INSUFFICIENT = "APPLICABILITY.INSUFFICIENT_DATA"


def _hire(api, org, ref, *, allowances=(), person=None):
    return api("decideHire", org["hr"], expect=201, json={
        "employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
        "person": {"person": {"legal_name": "決定", **(person or national(ref))}},
        "compensation": {"effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
                         "monthly_base_salary": "32000", "fixed_monthly_allowances": list(allowances)}}).json()


def _start(api, org, hire, **extra):
    return api("startEmployment", org["hr"], path={"id": hire["hire_id"]}, expect=201,
               json={"start_date": START, "work_location_id": str(org["location"]),
                     "public_or_military_insurance_covered": False, **extra}).json()


def _current(api, org, **params):
    [p] = api("listEnrollmentProposals", org["hr"], params={**params, "open": True}, expect=200).json()["items"]
    return p, {i["scheme_code"]: i for i in p["items"]}


def test_d15_public_or_military_excludes_employment_insurance(api, db, ref):
    org = make_org(db, ref)
    started = _start(api, org, _hire(api, org, ref), public_or_military_insurance_covered=True)
    _, items = _current(api, org, employment_id=started["employment_id"])
    assert items[EI]["applicability"] == NA
    assert items[LI]["applicability"] == M                        # 其他保險不受影響


def test_d16_other_allowance_needs_decision_then_follows_decision(api, db, ref):
    org = make_org(db, ref)
    hire = _hire(api, org, ref, allowances=[{"name": "專案獎金", "category": "ALLOWANCE_CATEGORY.OTHER", "amount": "2400"}])
    started = _start(api, org, hire)
    prop, items = _current(api, org, employment_id=started["employment_id"])
    for code in (LI, EI, OAI, LP):
        assert items[code]["applicability"] == M, code            # 適用照常判定（04_rules D-19）
        assert "expected_grade" not in items[code]                 # 只有級距待人判斷
    assert items[LI]["filing_deadline"] == START
    pending = [{"kind": "ALLOWANCE_INCLUSION", "allowance_name": "專案獎金"}]
    assert prop["needs_decision"] == pending                       # 05_mapping D-22
    applic = api("getApplicability", org["hr"], path={"id": started["employment_id"]}, params={"on": START}, expect=200).json()
    assert applic["needs_decision"] == pending

    out = api("recordProposalDecision", org["hr"], path={"id": prop["enrollment_proposal_id"]}, expect=201,
              json={"kind": "ALLOWANCE_INCLUSION", "allowance_name": "專案獎金", "result": "INCLUDED", "reason": "每月固定發放"}).json()
    new, items = _current(api, org, employment_id=started["employment_id"])
    assert new["enrollment_proposal_id"] == out["proposal_id"] != prop["enrollment_proposal_id"]
    assert [d["result"] for d in new["allowance_decisions"]] == ["INCLUDED"]
    assert "needs_decision" not in new
    for code in (LI, EI, OAI, LP):
        assert items[code]["applicability"] == M, code
    # 32,000＋2,400 算入後的級距，取自分級表來源（勞保就保職保#17 第 5 級 33,301～34,800 元）
    assert items[LI]["expected_amount"] == "34800"

    # 雇主不能記錄決定（只有人資）
    assert api("recordProposalDecision", org["boss"], path={"id": out["proposal_id"]},
               json={"kind": "ALLOWANCE_INCLUSION", "allowance_name": "專案獎金", "result": "EXCLUDED"}).status_code == 403
    # 已被取代的待辦不能再記錄
    r = api("recordProposalDecision", org["hr"], path={"id": prop["enrollment_proposal_id"]},
            json={"kind": "ALLOWANCE_INCLUSION", "allowance_name": "專案獎金", "result": "EXCLUDED"})
    assert r.status_code == 409


def test_d16_two_employers_choose_employment_insurance(api, db, ref):
    org = make_org(db, ref)
    hire = _hire(api, org, ref)
    # 同一客戶的另一個雇主，這個人已在職
    other = db.employers.insert_one({"tenant_id": org["tenant"], "legal_name": "關係企業", "employer_type": "EMPLOYER_TYPE.COMPANY",
                                     "jurisdiction_id": ref["tw"], "created_at": now()}).inserted_id
    from bson import ObjectId
    db.employments.insert_one({"tenant_id": org["tenant"], "entity_id": ObjectId(), "revision": 1, "is_current": True,
                               "recorded_at": now(), "person_id": ObjectId(hire["person_id"]), "employer_id": other,
                               "start_date": to_dt(date(2025, 1, 1)), "status": "Active", "annulled": False, "created_at": now()})
    started = _start(api, org, hire)
    prop, items = _current(api, org, employment_id=started["employment_id"])
    assert items[EI]["applicability"] == NEEDS
    assert items[LI]["applicability"] == M
    out = api("recordProposalDecision", org["hr"], path={"id": prop["enrollment_proposal_id"]}, expect=201,
              json={"kind": "EMPLOYMENT_INSURANCE_CHOICE", "scheme_code": EI, "result": "JOIN"}).json()
    new, items = _current(api, org, employment_id=started["employment_id"])
    assert new["enrollment_proposal_id"] == out["proposal_id"]
    assert items[EI]["applicability"] == M
    assert [d["result"] for d in items[EI]["decisions"]] == ["JOIN"]     # 決定沿用到新的待辦


def test_d20_choice_recorded_without_other_employer_in_system(api, db, ref):
    """系統外另有雇主：系統沒判成待人判斷，人資也能主動記錄擇一參加，之後依決定（04_rules D-20）。"""
    org = make_org(db, ref)
    started = _start(api, org, _hire(api, org, ref))
    prop, items = _current(api, org, employment_id=started["employment_id"])
    assert items[EI]["applicability"] == M
    out = api("recordProposalDecision", org["hr"], path={"id": prop["enrollment_proposal_id"]}, expect=201,
              json={"kind": "EMPLOYMENT_INSURANCE_CHOICE", "scheme_code": EI, "result": "NOT_JOIN",
                    "reason": "員工在系統外的雇主參加就保"}).json()
    new, items = _current(api, org, employment_id=started["employment_id"])
    assert new["enrollment_proposal_id"] == out["proposal_id"]
    assert items[EI]["applicability"] == NA
    assert items[LI]["applicability"] == M                        # 其他保險不受影響


def test_d21_public_or_military_unknown_is_insufficient_data(api, db, ref):
    """公教或軍保未知 → 就保資料不足（04_rules D-21、docs/03 P12）；用 RecordEmploymentPeriod 補值（03_flows D-21）。"""
    org = make_org(db, ref)
    hire = _hire(api, org, ref)
    pre, items = _current(api, org, hire_id=hire["hire_id"])          # 錄用時的預估：還沒登錄
    assert items[EI]["applicability"] == INSUFFICIENT
    assert items[LI]["applicability"] == M                         # 其他保險照常
    # 到職時必填
    r = api("startEmployment", org["hr"], path={"id": hire["hire_id"]},
            json={"start_date": START, "work_location_id": str(org["location"])})
    assert r.status_code == 422
    started = _start(api, org, hire)
    emp_id = started["employment_id"]
    # 模擬 02-v4 之前建立的僱傭關係：沒有這個欄位
    db.employments.update_one({"entity_id": ObjectId(emp_id), "is_current": True},
                              {"$unset": {"public_or_military_insurance_covered": ""}})
    appl = api("getApplicability", org["hr"], path={"id": emp_id}, params={"on": START}, expect=200).json()
    assert {i["scheme_code"]: i for i in appl["items"]}[EI]["applicability"] == INSUFFICIENT
    assert "Employment.public_or_military_insurance_covered" in appl["missing_data"]

    # R64：起日要在僱傭期間內
    r = api("recordEmploymentPeriod", org["hr"], path={"id": emp_id},
            json={"public_or_military_insurance_covered": False, "from": "2026-03-01", "evidence": [{"kind": "聘書"}]})
    assert r.status_code == 409 and r.json()["rule_id"] == "R64"
    out = api("recordEmploymentPeriod", org["hr"], path={"id": emp_id}, expect=201,
              json={"public_or_military_insurance_covered": False, "from": START, "evidence": [{"kind": "聘書"}]}).json()
    assert out["employment_id"] == emp_id
    _, items = _current(api, org, employment_id=emp_id)            # 補值後重新判定
    assert items[EI]["applicability"] == M

    # 職務改變：之後應參加公教或軍保，就保從那天起不適用，之前照舊
    api("recordEmploymentPeriod", org["hr"], path={"id": emp_id}, expect=201,
        json={"public_or_military_insurance_covered": True, "from": "2026-08-01", "evidence": [{"kind": "聘書"}]})
    later = api("getApplicability", org["hr"], path={"id": emp_id}, params={"on": "2026-08-01"}, expect=200).json()
    before = api("getApplicability", org["hr"], path={"id": emp_id}, params={"on": START}, expect=200).json()
    assert {i["scheme_code"]: i for i in later["items"]}[EI]["applicability"] == NA
    assert {i["scheme_code"]: i for i in before["items"]}[EI]["applicability"] == M
    ev = db.events.find_one({"type": "RecordEmploymentPeriod", "subject.id": ObjectId(emp_id)})
    assert ev["evidence"] == [{"kind": "聘書"}]


def test_d17_overdue_is_on_proposal_not_a_warning(api, db, ref):
    org = make_org(db, ref)
    started = _start(api, org, _hire(api, org, ref))
    assert not [w for w in started["warnings"] if w["rule_id"] == "R36"]
    # 「今天」經 clock.today（雇主所在地，hire-employee 05_mapping D-24），不讀伺服器時鐘
    with clock.fixed(date.fromisoformat(START) + timedelta(days=10)):
        _, items = _current(api, org, employment_id=started["employment_id"])
    assert items[LI]["days_overdue"] == 10
    assert "days_overdue" not in items[LP] or items[LP]["days_overdue"] < items[LI]["days_overdue"]
    # 登錄實際辦理後結案，不再逾期
    api("recordInsuranceFiling", org["hr"], expect=201, json={
        "employment_id": started["employment_id"], "scheme_id": str(ref["schemes"][LI]),
        "insurance_unit_id": str(org["units"]["BLI"]), "filed_on": START, "voluntary": False, "no_receipt": True})
    _, items = _current(api, org, employment_id=started["employment_id"])
    assert "days_overdue" not in items[LI]
    assert items[LI]["closed_by_enrollment_id"]


def test_d18_estimate_at_hire_superseded_at_start(api, db, ref):
    org = make_org(db, ref)
    hire = _hire(api, org, ref)
    pre, _ = _current(api, org, hire_id=hire["hire_id"])
    assert pre["estimated"] is True and pre["determined_on"] == START
    started = _start(api, org, hire)
    after = api("listEnrollmentProposals", org["hr"], params={"hire_id": hire["hire_id"]}).json()["items"]
    old = next(p for p in after if p["enrollment_proposal_id"] == pre["enrollment_proposal_id"])
    new = next(p for p in after if p["enrollment_proposal_id"] == started["enrollment_proposal_id"])
    assert old["superseded_by"] == new["enrollment_proposal_id"]
    assert "estimated" not in new or new["estimated"] is False
    assert "days_overdue" not in {k for i in old["items"] for k in i}      # 被取代的待辦不再算逾期
