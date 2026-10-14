"""「提醒」類規則：回傳警告（api.yaml Warning），不阻擋（PLAN.md D-27）；被忽略的另記 WarningOverride。"""
from datetime import date

from app.db import to_date
from app.rules import versions
from app.rules.applicability import is_national, value_on


def warning(db, rule_id: str, on: date, message_code: str, *, subject: tuple | None = None,
            warned_value=None, session=None) -> dict:
    rv = versions.rule(db, rule_id, on, session=session)
    w = {"rule_id": rule_id, "rule_version": rv["version"], "rule_revision": rv["revision"], "message_code": message_code}
    if subject:
        w["subject"] = {"collection": subject[0], "id": str(subject[1])} | ({"field": subject[2]} if len(subject) > 2 else {})
    if warned_value is not None:
        w["warned_value"] = warned_value
    return w


def minimum_wage(db, employer: dict, compensation: dict | None, start: date, session=None) -> list[dict]:
    """R11、R12：約定工資不低於到職日的每月最低工資；只適用勞基法的雇主；沒有約定薪資 → 資料不足（R60）。"""
    if not value_on(employer.get("labor_standards_act_applicable"), start):
        return []
    if compensation is None:
        return [warning(db, "R11", start, "INSUFFICIENT_DATA", warned_value={"missing": ["Compensation"]}, session=session)]
    r12 = versions.rule(db, "R12", start, session=session)
    if r12 is None:
        return [warning(db, "R11", start, "NO_RULE_VERSION", warned_value={"rule_id": "R12"}, session=session)]
    minimum = r12["params"]["monthly_minimum_wage"]
    base = compensation["monthly_base_salary"].to_decimal()   # 比較基礎 [待專家確認: EQ-019]（signoff.md #11）
    if base < minimum:
        return [warning(db, "R11", start, "BELOW_MINIMUM_WAGE",
                        subject=("compensations", compensation["entity_id"], "monthly_base_salary"),
                        warned_value={"monthly_base_salary": str(base), "monthly_minimum_wage": minimum,
                                      "minimum_wage_rule": versions.ref(r12)}, session=session)]
    return []


def work_authorization(db, person: dict, employer_id, start: date, session=None) -> list[dict]:
    """R14、R15：外國籍員工到職日要有有效的工作許可，雇主申請的要綁定這個雇主。

    R16（免申請者的居留證件條件）屬 UC-04，尚未實作。
    """
    if is_national(person, start) is not False:
        return []
    for a in db.work_authorizations.find({"person_id": person["entity_id"], "is_current": True}, session=session):
        if a["authorization_basis"] == "AUTHORIZATION_BASIS.EXEMPT_BY_STATUS":
            if to_date(a["valid_from"]) <= start and (a.get("valid_until") is None or start <= to_date(a["valid_until"])):
                return []
        for ap in a.get("approvals") or []:
            if to_date(ap["valid_from"]) <= start <= to_date(ap["valid_until"]):
                if a["authorization_basis"] == "AUTHORIZATION_BASIS.EMPLOYER_PERMIT" and a.get("employer_id") != employer_id:
                    return [warning(db, "R15", start, "PERMIT_BOUND_TO_OTHER_EMPLOYER",
                                    subject=("work_authorizations", a["entity_id"]), session=session)]
                return []
    return [warning(db, "R14", start, "NO_VALID_WORK_AUTHORIZATION", subject=("persons", person["entity_id"]), session=session)]
