"""annual-leave-grant 測試共用：雇主、員工（經 hire-employee 的 API 到職）、排程與「今天」。"""
from datetime import date

from bson import ObjectId

from app.db import now, to_dt
from app.leave import clock, scheduler
from tests.conftest import make_org


def leave_org(db, ref, *, system_managed_from=date(2025, 1, 1), wage_day=5, lag=1, deadline_rule=None, **kw):
    """黃金案例的共同前提：台灣、適用勞基法、開始由系統管理 2025-01-01、工資給付日每月 5 日發上一個月 [靜態替代]。"""
    org = make_org(db, ref, existing_employees=0, system_managed_from=system_managed_from, **kw)
    frm = to_dt(date(2018, 1, 1))
    st = {"tenant_id": org["tenant"], "employer_id": org["employer"],
          "wage_payment_day": [{"value": wage_day, "from": frm}], "wage_payment_lag_months": [{"value": lag, "from": frm}],
          "created_at": now()}
    if deadline_rule:
        st["payment_deadline_rule"] = [{"value": deadline_rule, "from": frm}]
    db.employer_settings.insert_one(st)
    return org


def hire(api, org, ref, start: str, *, name="特休員工", decided_on=None) -> dict:
    """hire-employee UC-01：錄用並到職（到職的同一交易會補上已到的特休，D-04）。回傳 startEmployment 的回應。"""
    h = org["hr"]
    with clock.fixed(date.fromisoformat(start)):
        hid = api("decideHire", h, expect=201, json={
            "employer_id": str(org["employer"]), "decided_on": decided_on or start, "planned_start_date": start,
            "person": {"person": {"legal_name": name, "birth_date": "1995-01-01",
                                  "nationalities": [{"country_code": "TW", "acquired_on": "1995-01-01"}]}},
            "compensation": {"effective_from": start, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
                             "monthly_base_salary": "36000"},
            "contract": {"contract_type": "CONTRACT_TYPE.INDEFINITE", "term_start": start, "in_writing": True}}).json()["hire_id"]
        return api("startEmployment", h, path={"id": hid}, expect=201, json={
            "start_date": start, "work_location_id": str(org["location"]),
            "public_or_military_insurance_covered": False}).json()


def run_day(db, employment_id: str, day: str) -> list:
    """每日排程對一段僱傭關係（scheduler.process_employment），「今天」是 day。"""
    return scheduler.process_employment(db, ObjectId(employment_id), date.fromisoformat(day))


def on(day: str):
    return clock.fixed(date.fromisoformat(day))


def entitlements(api, org, employment_id: str, **params) -> list[dict]:
    return api("listLeaveEntitlements", org["hr"], path={"id": employment_id}, params=params, expect=200).json()["items"]
