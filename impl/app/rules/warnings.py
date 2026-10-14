"""「提醒」類規則：回傳警告，不阻擋（PLAN.md D-27）；被忽略的另記 WarningOverride。"""
from datetime import date

from app.db import to_date, to_dec
from app.rules import versions
from app.rules.applicability import is_national, value_on


def warning(rv: dict | None, rule_id: str, message_code: str, warned_value=None) -> dict:
    w = {"rule_id": rule_id, "message_code": message_code}
    if rv:
        w |= {"rule_version": rv["version"], "rule_revision": rv["revision"]}
    if warned_value is not None:
        w["warned_value"] = warned_value
    return w


def minimum_wage(db, employer: dict, compensation: dict | None, start: date, session=None) -> list[dict]:
    """R11、R12：約定工資不低於到職日的每月最低工資；只適用勞基法的雇主；沒有約定薪資 → 資料不足（R60）。"""
    if not value_on(employer.get("labor_standards_act_applicable"), start):
        return []
    r11 = versions.rule(db, "R11", start, session=session)
    if compensation is None:
        return [warning(r11, "R11", "INSUFFICIENT_DATA.COMPENSATION")]
    r12 = versions.rule(db, "R12", start, session=session)
    if r12 is None:
        return [warning(r11, "R11", "NO_RULE_VERSION.R12")]
    minimum = r12["params"]["monthly_minimum_wage"]
    base = to_dec(compensation["monthly_base_salary"])      # 比較基礎 [待專家確認: EQ-019]，R11 params.compare_basis
    if base < minimum:
        return [warning(r12, "R11", "BELOW_MINIMUM_WAGE", {"monthly_base_salary": str(base), "minimum": minimum})]
    return []


def work_authorization(db, person: dict, employer_id, start: date, session=None) -> list[dict]:
    """R14、R15（R16 的居留證件條件未實作）：外國籍員工到職日要有有效的工作許可。"""
    if is_national(person, start) is not False:
        return []
    auths = list(db.work_authorizations.find({"person_id": person["entity_id"], "is_current": True}, session=session))
    for a in auths:
        if a["authorization_basis"] == "AUTHORIZATION_BASIS.EXEMPT_BY_STATUS":
            if to_date(a["valid_from"]) <= start and (a.get("valid_until") is None or start <= to_date(a["valid_until"])):
                return []
        for ap in a.get("approvals") or []:
            if to_date(ap["valid_from"]) <= start <= to_date(ap["valid_until"]):
                if a["authorization_basis"] == "AUTHORIZATION_BASIS.EMPLOYER_PERMIT" and a.get("employer_id") != employer_id:
                    return [warning(None, "R15", "PERMIT_BOUND_TO_OTHER_EMPLOYER")]
                return []
    return [warning(None, "R14", "NO_VALID_WORK_AUTHORIZATION")]
