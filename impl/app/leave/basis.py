"""依規則應給予的特休（04_rules R65～R70、R77）：給予、重新判定與預估共用。只讀資料，不寫入。"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.db import to_date, to_dec
from app.errors import Blocked
from app.leave import dates
from app.rules import versions
from app.rules.applicability import value_on

LEAVE_TYPE = "LEAVE_TYPE.ANNUAL_LEAVE_TW"
STATUTORY, COMPANY = "ENTITLEMENT_SOURCE.STATUTORY", "ENTITLEMENT_SOURCE.COMPANY_POLICY"
RULE_GRANT, DEFERRED_IN = "ENTITLEMENT_ORIGIN.RULE_GRANT", "ENTITLEMENT_ORIGIN.DEFERRED_IN"
REGISTERED_CURRENT, REGISTERED_DEFERRED = "ENTITLEMENT_ORIGIN.REGISTERED_CURRENT", "ENTITLEMENT_ORIGIN.REGISTERED_DEFERRED"
ANNIVERSARY, FIXED_START = "LEAVE_YEAR_BASIS.ANNIVERSARY", "LEAVE_YEAR_BASIS.FIXED_START"
EXTRA, YEAR_DEFAULT = "POLICY_SUBJECT.ANNUAL_LEAVE_EXTRA", "POLICY_SUBJECT.ANNUAL_LEAVE_YEAR_DEFAULT"
DAY_UNIT = "LEAVE_UNIT.DAY"


def rule(db, rule_id: str, on: date, session=None) -> dict:
    rv = versions.rule(db, rule_id, on, session=session)
    if rv is None:
        raise Blocked(rule_id, "NO_RULE_VERSION", f"{rule_id} 在 {on} 沒有規則版本（PLAN.md D-28）")
    return rv


def rref(rv: dict) -> dict:
    return {"kind": "RULE", **versions.ref(rv)}


def pref(v: dict) -> dict:
    return {"kind": "COMPANY_POLICY", "policy_id": v["policy_id"], "version": v["version"], "revision": v["revision"]}


def acquisition(start: date, months: int, rule_code: str) -> date:
    """R65：滿 months 個月的取得日；acquisition_day_rule 決定是末日的隔天或末日當天。"""
    end = dates.period_end(start, months)
    return end + dates.DAY if rule_code == "ACQUISITION_DAY_RULE.DAY_AFTER_PERIOD_END" else end


def threshold(k: int, first_months: int) -> int:
    return first_months if k == 1 else 12 * (k - 1)


def bracket(table: list[dict], months: int):
    for b in table:
        if b["from_months"] <= months and (b.get("to_months") is None or months < b["to_months"]):
            return to_dec(b["days"])
    return None


# ---- R68：某一天適用哪一種特休年度 ----

@dataclass
class YearBasis:
    leave_year_basis: str
    applied_by: str                       # AGREEMENT／EMPLOYER_DEFAULT／NONE（api.yaml YearBasisOut）
    year_start: dict | None = None
    agreement_id: object = None
    policy_id: object = None
    rule_refs: list = field(default_factory=list)


def agreement_on(db, s, emp: dict, on: date) -> dict | None:
    best = None
    for a in db.leave_year_agreements.find({"tenant_id": emp["tenant_id"], "employment_id": emp["entity_id"],
                                            "leave_type_code": LEAVE_TYPE}, session=s):
        if to_date(a["effective_from"]) <= on and (a.get("ended_from") is None or on < to_date(a["ended_from"])):
            if best is None or a["effective_from"] > best["effective_from"]:
                best = a
    return best


def policies_on(db, s, tenant_id, employer_id, subject: str, on: date) -> list[dict]:
    out = []
    for p in db.company_policies.find({"tenant_id": tenant_id, "subject": subject, "is_current": True}, session=s):
        if p.get("employer_id") not in (None, employer_id) or p.get("leave_type_code") not in (None, LEAVE_TYPE):
            continue
        if to_date(p["effective_from"]) <= on and (p.get("effective_to") is None or on <= to_date(p["effective_to"])):
            out.append(p)
    return out


def policy_version(db, s, policy_id, on: date) -> dict | None:
    """on 當天有效的版本（最新的修訂）。"""
    vs = [v for v in db.company_policy_versions.find({"policy_id": policy_id}, session=s) if to_date(v["effective_from"]) <= on]
    if not vs:
        return None
    top = max(vs, key=lambda v: v["effective_from"])
    return max((v for v in vs if v["version"] == top["version"]), key=lambda v: v["revision"])


def year_basis(db, s, emp: dict, on: date) -> YearBasis:
    r68 = rule(db, "R68", on, s)
    a = agreement_on(db, s, emp, on)
    if a:
        return YearBasis(a["leave_year_basis"], "AGREEMENT", a.get("year_start"), agreement_id=a["_id"], rule_refs=[rref(r68)])
    for p in policies_on(db, s, emp["tenant_id"], emp["employer_id"], YEAR_DEFAULT, on):
        v = policy_version(db, s, p["entity_id"], on)
        d = (v or {}).get("params", {}).get("company_default_leave_year")
        if d:
            return YearBasis(d["leave_year_basis"], "EMPLOYER_DEFAULT", d.get("year_start"), policy_id=p["entity_id"],
                             rule_refs=[rref(r68), pref(v)])
    return YearBasis(r68["params"]["leave_year_basis_when_none"], "NONE", rule_refs=[rref(r68)])


def fixed_start_method(db, s, emp: dict, on: date) -> tuple[str, list]:
    """fixed_start_year_method：on 當天雇主有效的特休年度預設那一版有寫就用它，否則用 R70 的（05_mapping 3.2、D-31）。
    個別約定也沿用雇主預設的做法（04 參數表）。回傳 (做法代碼, 依據的規則版本)。"""
    r70 = rule(db, "R70", on, s)
    for p in policies_on(db, s, emp["tenant_id"], emp["employer_id"], YEAR_DEFAULT, on):
        v = policy_version(db, s, p["entity_id"], on)
        method = (v or {}).get("params", {}).get("fixed_start_year_method")
        if method:
            return method, [rref(r70), pref(v)]
    return r70["params"]["fixed_start_year_method"], [rref(r70)]


# ---- R65～R70、R77：依規則應給予的每一期 ----

@dataclass
class Expected:
    items: list[dict]
    insufficient: list[dict]           # [{rule_id, missing[]}]（core R60）
    policy_warnings: list = field(default_factory=list)


def expected(db, s, emp: dict, employer: dict, until: date, *, version_for=None) -> Expected:
    """到 until（含）為止依規則應給予的每一筆（法定一筆、符合的公司加給各一筆）。

    version_for(source, policy_id, period_sequence, acquired_on) → 已給予那一筆記的公司規定版本（05_mapping D-20），沒有回 None。
    """
    items, missing = [], []
    start = to_date(emp.get("start_date"))
    if start is None:
        return Expected([], [{"rule_id": "R67", "missing": ["Employment.start_date"]}])
    if employer.get("system_managed_from") is None:
        missing.append("Employer.system_managed_from")
    if not employer.get("labor_standards_act_applicable"):
        missing.append("Employer.labor_standards_act_applicable")
    if missing:
        return Expected([], [{"rule_id": "R67", "missing": missing}])
    smf = to_date(employer["system_managed_from"])
    ended = to_date(emp.get("ended_on"))
    insufficient = []
    r65 = rule(db, "R65", start, s)
    acq_rule, first = r65["params"]["acquisition_day_rule"], r65["params"]["first_period_months"]
    k = 1
    while True:
        months = threshold(k, first)
        acq = acquisition(start, months, acq_rule)
        if acq > until or (ended and ended < acq):            # R67：結束日早於取得日 → 不給予，之後也不再給
            break
        k += 1
        lsa = value_on(employer.get("labor_standards_act_applicable"), acq)
        if lsa is None:
            insufficient = [{"rule_id": "R67", "missing": ["Employer.labor_standards_act_applicable"]}]
            continue
        if lsa is False or acq < smf:                          # 不適用；早於開始由系統管理的日子 → 由人補登（R97）
            continue
        yb = year_basis(db, s, emp, acq)
        r66 = rule(db, "R66", acq, s)
        qty = bracket(r66["params"]["statutory_annual_leave_days"], months)
        if k - 1 == 1:
            valid_to = dates.period_end(acq, first)                                     # R69 第一筆
            nxt = acquisition(start, 12, acq_rule) - dates.DAY
            if acq_rule == "ACQUISITION_DAY_RULE.PERIOD_END_DAY" and valid_to < nxt:
                valid_to = nxt
        else:
            valid_to = acquisition(start, threshold(k, first), acq_rule) - dates.DAY   # 下一個週年取得日的前一天
        period_refs = [rref(rule(db, "R69", acq, s))]
        if yb.leave_year_basis == FIXED_START:
            method, period_refs = fixed_start_method(db, s, emp, acq)
            if method != "FIXED_START_YEAR_METHOD.EXTEND_TO_YEAR_END":    # 這版沒有規則的做法 → 資料不足（04 參數表）
                insufficient = [{"rule_id": "R70", "missing": ["fixed_start_year_method"]}]
                continue
            valid_to = dates.fixed_year_end(valid_to, yb.year_start or {"month": 1, "day": 1})
        base = {
            "leave_type_code": LEAVE_TYPE, "origin": RULE_GRANT, "period_sequence": k - 1, "seniority_tier": months,
            "acquired_on": acq, "unit": DAY_UNIT, "valid_from": acq, "valid_to": valid_to,
            "leave_year_basis": yb.leave_year_basis, "basis_seniority": {"months": months, "days": 0},
            "basis_start_date": start,
            "applied_year_agreement_id": yb.agreement_id, "applied_year_default_policy_id": yb.policy_id,
        }
        # basis_rule_versions：R65、R66、R68（依預設時加那一版公司規定）、R69 或 R70（05_mapping D-26）
        rules = [rref(r65), rref(r66), *yb.rule_refs, *period_refs]
        items.append({**base, "source": STATUTORY, "policy_id": None, "quantity": qty, "basis_rule_versions": rules})
        r77 = rule(db, "R77", acq, s)
        category = value_on(emp.get("employee_category"), acq, key="code")
        for p in policies_on(db, s, emp["tenant_id"], emp["employer_id"], EXTRA, acq):
            v = None
            if version_for:
                v = version_for(COMPANY, p["entity_id"], k - 1, acq)
            v = v or policy_version(db, s, p["entity_id"], acq)
            if v is None:
                continue
            params = v.get("params", {})
            cats = (params.get("company_extra_eligibility") or {}).get("employee_categories") or []
            if cats and category not in cats:
                continue
            days = bracket(params.get("company_extra_days") or [], months)
            if days is None or days <= 0:                      # 負數由 R78 警告（掛在公司規定上），照法定給
                continue
            items.append({**base, "source": COMPANY, "policy_id": p["entity_id"], "quantity": days,
                          "basis_rule_versions": rules + [rref(r77), pref(v)]})
    return Expected(items, insufficient)


def deferred_in_period(db, s, orig: dict) -> tuple[date, date]:
    """R87：遞延進來那一筆的可休期間。起日是原來那一筆年度終結日的隔天，迄日是次一年度的終結日。"""
    vf = to_date(orig["valid_to"]) + dates.DAY
    if orig.get("leave_year_basis") == FIXED_START:
        return vf, dates.fixed_year_end(vf, _year_start_of(db, s, orig))
    return vf, dates.period_end(vf, 12)                    # 週年制；補登的沒有年度種類時算一年


def _year_start_of(db, s, ent: dict) -> dict:
    if ent.get("applied_year_agreement_id"):
        a = db.leave_year_agreements.find_one({"_id": ent["applied_year_agreement_id"]}, session=s)
        return a.get("year_start") or {"month": 1, "day": 1}
    if ent.get("applied_year_default_policy_id"):
        v = policy_version(db, s, ent["applied_year_default_policy_id"], to_date(ent["acquired_on"]))
        return v["params"]["company_default_leave_year"].get("year_start") or {"month": 1, "day": 1}
    return {"month": 1, "day": 1}


def decimal(v) -> Decimal:
    return to_dec(v) if v is not None else Decimal(0)
