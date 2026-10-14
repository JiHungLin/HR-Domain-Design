"""各保險的適用、應辦理期限、法定生效日、應申報級距（04_rules R22～R35、R39～R44、R60）。

結果是推導值（P3）：不落地，只寫進加保待辦（記當時的資料與規則版本）或在查詢時回傳。
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.db import to_date, to_dec, to_dt
from app.rules import versions
from app.seed import EI, LI, LP, NHI, OAI

MANDATORY, VOLUNTARY, NA = "APPLICABILITY.MANDATORY", "APPLICABILITY.VOLUNTARY", "APPLICABILITY.NOT_APPLICABLE"
NOT_YET, NO_RULE, INSUFFICIENT = "APPLICABILITY.NOT_YET_IN_FORCE", "APPLICABILITY.NO_RULE_VERSION", "APPLICABILITY.INSUFFICIENT_DATA"
ROC = "TW"

SCHEME_RULE = {LI: "R22", EI: "R24", OAI: "R25", NHI: "R26", LP: "R27"}
GRADE_RULE = {LI: "R40", EI: "R40", OAI: "R41", LP: "R42", NHI: "R43"}


# ---------------- 判定所需的資料 ----------------

@dataclass
class Facts:
    """判定日 d 用到的資料（as_of 時系統知道的版本）。"""
    employment: dict
    person: dict
    employer: dict
    identity_documents: list[dict]
    compensation: dict | None
    work_authorizations: list[dict]
    headcount: int
    schemes: dict[str, dict]
    data_refs: dict = field(default_factory=dict)


def load_facts(db, employment: dict, on: date, as_of: datetime | None = None, session=None) -> Facts:
    tenant = employment["tenant_id"]
    person = _one(versions.snapshot(db, "persons", {"entity_id": employment["person_id"]}, as_of, session))
    employer = db.employers.find_one({"_id": employment["employer_id"]}, session=session)
    docs = versions.snapshot(db, "identity_documents", {"tenant_id": tenant, "person_id": employment["person_id"]}, as_of, session)
    comp = _compensation_on(db, employment, on, as_of, session)
    auths = versions.snapshot(db, "work_authorizations", {"tenant_id": tenant, "person_id": employment["person_id"]}, as_of, session)
    schemes = {s["code"]: s for s in db.social_insurance_schemes.find({}, session=session)}
    return Facts(
        employment=employment, person=person, employer=employer, identity_documents=docs, compensation=comp,
        work_authorizations=auths, headcount=headcount(db, tenant, employment["employer_id"], on, as_of, session),
        schemes=schemes,
        data_refs={k: v for k, v in {
            "employment": _ver(employment), "person": _ver(person), "compensation": _ver(comp) if comp else None,
            "employer_id": employment["employer_id"]}.items() if v is not None},
    )


def _one(docs):
    return docs[0] if docs else None


def _ver(doc):
    return {"entity_id": doc["entity_id"], "revision": doc["revision"]}


def _compensation_on(db, employment, on, as_of, session):
    """約定薪資：連到這段僱傭關係或它的錄用、判定日已生效者中最晚生效的一筆。"""
    links = [{"employment_id": employment["entity_id"]}]
    if employment.get("hire_id"):
        links.append({"hire_id": employment["hire_id"]})
    comps = [c for c in versions.snapshot(db, "compensations", {"tenant_id": employment["tenant_id"], "$or": links}, as_of, session)
             if to_date(c["effective_from"]) <= on]
    return max(comps, key=lambda c: c["effective_from"], default=None)


def headcount(db, tenant_id, employer_id, on: date, as_of=None, session=None) -> int:
    """R23：判定日那天的在職人數，依實際到職、結束日計算；被註銷的不算（D-11）。計入範圍待 EQ-008。"""
    d = to_dt(on)
    emps = versions.snapshot(db, "employments", {"tenant_id": tenant_id, "employer_id": employer_id}, as_of, session)
    return sum(1 for e in emps if not e.get("annulled") and e["start_date"] <= d
               and (e.get("ended_on") is None or e["ended_on"] >= d))


# ---------------- 小工具 ----------------

def value_on(periods: list[dict] | None, on: date, key="value"):
    for p in periods or []:
        if to_date(p["from"]) <= on and (p.get("to") is None or on <= to_date(p["to"])):
            return p.get(key)
    return None


def age_on(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def is_national(person: dict, on: date) -> bool | None:
    nats = person.get("nationalities")
    if not nats:
        return None
    return any(n["country_code"] == ROC and to_date(n["acquired_on"]) <= on
               and (n.get("lost_on") is None or on <= to_date(n["lost_on"])) for n in nats)


def has_civil_registration(person: dict, tw_id, on: date) -> bool:
    return any(r["jurisdiction_id"] == tw_id and to_date(r["registered_on"]) <= on
               and (r.get("deregistered_on") is None or on <= to_date(r["deregistered_on"]))
               for r in person.get("civil_registrations") or [])


def valid_docs(facts: Facts, on: date) -> list[dict]:
    return [d for d in facts.identity_documents
            if to_date(d["valid_from"]) <= on and (d.get("valid_until") is None or on <= to_date(d["valid_until"]))]


def residence_bases(facts: Facts, on: date) -> set[str]:
    return {d["residence_basis"] for d in valid_docs(facts, on) if d.get("residence_basis")}


# ---------------- 適用（R22～R28） ----------------

@dataclass
class Item:
    scheme_code: str
    applicability: str
    filing_deadline: date | None = None
    legal_effective_date: date | None = None
    expected_grade: str | None = None
    expected_amount: int | None = None
    notes: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    rules: list[dict] = field(default_factory=list)

    def to_doc(self) -> dict:
        """加保待辦 items[] 的一列（schema.mongo.js enrollment_proposals）。"""
        return {k: v for k, v in {
            "scheme_code": self.scheme_code, "applicability": self.applicability,
            "filing_deadline": to_dt(self.filing_deadline), "legal_effective_date": to_dt(self.legal_effective_date),
            "expected_grade": self.expected_grade}.items() if v is not None}

    def to_api(self) -> dict:
        return {"scheme_code": self.scheme_code, "applicability": self.applicability,
                "filing_deadline": self.filing_deadline, "legal_effective_date": self.legal_effective_date,
                "expected_grade": self.expected_grade, "expected_amount": self.expected_amount,
                "notes": self.notes, "pending": self.pending, "rule_versions": self.rules}


def determine(db, facts: Facts, on: date, as_of=None, session=None) -> list[Item]:
    tw = db.jurisdictions.find_one({"code": "TW"}, session=session)["_id"]
    items = []
    for code in (LI, EI, OAI, NHI, LP):
        item = _applicability(db, facts, code, on, tw, as_of, session)
        if item.applicability in (MANDATORY, VOLUNTARY):
            _deadlines(db, facts, item, as_of, session)
            _grade(db, facts, item, as_of, session)
        items.append(item)
    return items


def _applicability(db, facts: Facts, code: str, on: date, tw, as_of, session) -> Item:
    scheme = facts.schemes[code]
    if on < to_date(scheme["effective_from"]):                                  # R28
        return Item(code, NOT_YET, notes=["R28：判定日早於制度施行日"])
    rid = SCHEME_RULE[code]
    rv = versions.rule(db, rid, on, as_of, session)
    if rv is None:
        return Item(code, NO_RULE, notes=[f"R28：{rid} 沒有判定日適用的版本"])
    item = Item(code, NA, rules=[versions.ref(rv)])
    p, person, employer = rv["params"], facts.person, facts.employer

    birth = to_date(person.get("birth_date"))
    national = is_national(person, on)
    missing = [n for n, v in (("出生日期", birth), ("國籍", national)) if v is None]
    if code in (LI, EI, OAI) and birth is None or code in (EI, NHI, LP) and national is None:
        item.applicability = INSUFFICIENT                                       # R60
        item.notes.append("R60：缺 " + "、".join(missing))
        return item
    age = age_on(birth, on) if birth else None

    if code == LI:                                                             # R22、R23、R29
        if age == p["max_age"] or person.get("old_age_benefits_received"):
            item.pending.append("EQ-006")                                      # 65 歲界線、已領老年給付
        if not (p["min_age"] <= age <= p["max_age"]):
            item.notes.append(f"R29：判定日 {age} 歲，不在 {p['min_age']}～{p['max_age']} 歲")
            return item
        cat = value_on(employer.get("labor_insurance_industry_category"), on, key="code")
        if cat is None:
            item.applicability = INSUFFICIENT
            item.notes.append("R60：缺雇主的勞保行業類別")
        elif cat in p["threshold_categories"]:
            item.applicability = MANDATORY if facts.headcount >= p["headcount_threshold"] else VOLUNTARY
            item.pending.append("EQ-008")                                      # 人數計入範圍與層級
            item.notes.append(f"R23：判定日在職 {facts.headcount} 人（門檻 {p['headcount_threshold']}）")
        elif cat in p["no_threshold_categories"]:
            item.applicability = MANDATORY
        else:
            item.applicability = VOLUNTARY
            item.pending.append("EQ-004")                                      # 小雇主、個人雇主的實務
        if person.get("old_age_benefits_received"):
            item.notes.append("已領老年給付者的勞保適用 [待專家確認: EQ-006]")
    elif code == EI:                                                           # R24
        if not (p["min_age"] <= age <= p["max_age"]):
            item.notes.append(f"R24：判定日 {age} 歲，不在 {p['min_age']}～{p['max_age']} 歲")
        elif person.get("old_age_benefits_received"):
            item.notes.append("R24：已領老年給付，不適用")
        elif value_on(employer.get("registration_exempt"), on) and not value_on(employer.get("tax_assessed_or_invoice_permit"), on):
            item.notes.append("R24：雇主依法免辦登記且無核定課稅，不適用")
        elif national or residence_bases(facts, on) & set(p["residence_basis"]):
            item.applicability = MANDATORY
        else:
            item.notes.append("R24：非本國籍，也不是與國人結婚獲准居留")
    elif code == OAI:                                                          # R25
        regs = {r["kind"] for r in employer.get("registrations") or [] if to_date(r["registered_on"]) <= on}
        bound = any(a.get("employer_id") == employer["_id"] for a in facts.work_authorizations)
        if age < p["min_age"]:
            item.notes.append(f"R25：未滿 {p['min_age']} 歲")
        elif regs & set(p["registration_kinds"]) or bound:
            item.applicability = MANDATORY
        else:
            item.notes.append("R25 只寫了強制的條件；雇主沒有登記、稅籍、執業證照或聘僱許可時的結果，設計沒有寫")
    elif code == NHI:                                                          # R26
        kinds = {d["document_kind"] for d in valid_docs(facts, on)}
        if national and has_civil_registration(person, tw, on):
            item.applicability = MANDATORY
        elif not national and kinds & set(p["residence_document_kinds"]):
            item.applicability = MANDATORY
        else:
            item.notes.append("R26：判定日沒有戶籍或有效的居留證明")
    elif code == LP:                                                           # R27
        lsa = value_on(employer.get("labor_standards_act_applicable"), on)
        qualifies = national or bool(residence_bases(facts, on) & set(p["residence_basis"]))
        if not qualifies:
            item.notes.append("R27：身分不在勞退適用範圍，自願提繳也不行")
        elif lsa:
            item.applicability = MANDATORY
        else:
            item.applicability = VOLUNTARY
    return item


# ---------------- 期限與法定生效日（R31～R34、R37） ----------------

def _deadlines(db, facts: Facts, item: Item, as_of, session) -> None:
    if item.applicability != MANDATORY:
        return                                                                 # 自願加保沒有法定生效日（R35）
    start = to_date(facts.employment["start_date"])                           # R37：依到職日
    code = item.scheme_code
    rid = {LI: "R31", EI: "R31", OAI: "R32", NHI: "R33", LP: "R34"}[code]
    rv = versions.rule(db, rid, start, as_of, session)
    if rv is None:
        item.notes.append(f"R28：{rid} 沒有到職日適用的版本")
        return
    item.rules.append(versions.ref(rv))
    p = rv["params"]
    if code in (LI, EI):
        item.filing_deadline = item.legal_effective_date = start + timedelta(days=p["deadline_offset_days"])
    elif code == OAI:
        regs = [to_date(r["registered_on"]) for r in facts.employer.get("registrations") or [] if r["kind"] in p["registration_kinds"]]
        base = max(start, min(regs)) if regs else start
        item.filing_deadline = item.legal_effective_date = base
    else:
        qualified = start
        if code == NHI and not is_national(facts.person, start):
            docs = [to_date(d["valid_from"]) for d in facts.identity_documents]
            qualified = max([start] + [d for d in docs if d])                 # [解讀] R33 外籍取較晚的一天
        item.filing_deadline = qualified + timedelta(days=p["window_days"])   # 始日不算入
        item.legal_effective_date = None
        item.pending.append(p["pending"])


# ---------------- 應申報級距（R39～R44） ----------------

def wage_bases(db, facts: Facts, on: date, as_of=None, session=None):
    """R39：三種薪資基礎。回傳 ({base_name: Decimal}, rule_version, notes)。"""
    comp = facts.compensation
    rv = versions.rule(db, "R39", on, as_of, session)
    if comp is None or rv is None:
        return None, rv, ["R60：沒有約定薪資" if comp is None else "R28：R39 沒有版本"]
    base = to_dec(comp["monthly_base_salary"])
    out, notes = {}, []
    for name, spec in rv["params"]["bases"].items():
        total = base
        for a in comp.get("fixed_monthly_allowances") or []:
            if a["category"] in spec["included_allowances"]:
                total += to_dec(a["amount"])
            elif a["category"] in rv["params"].get("needs_human", []):
                notes.append(f"固定給付「{a['name']}」類別為其他，算不算入由人判斷")
        out[name] = total
    return out, rv, notes


def _grade(db, facts: Facts, item: Item, as_of, session) -> None:
    start = to_date(facts.employment["start_date"])
    r44 = versions.rule(db, "R44", start, as_of, session)                     # R44：預設依到職日的分級表
    table_day = start
    bases, r39, notes = wage_bases(db, facts, table_day, as_of, session)
    item.notes += notes
    if bases is None:
        return
    item.rules.append(versions.ref(r39))
    if facts.compensation.get("fixed_monthly_allowances"):
        item.pending.append("EQ-012")                                          # 哪些固定給付算入（R39）
    if r44:
        item.rules.append(versions.ref(r44))
    base_name = next(n for n, s in r39["params"]["bases"].items() if item.scheme_code in s["schemes"])
    rid = GRADE_RULE[item.scheme_code]
    table = versions.rule(db, rid, table_day, as_of, session)
    if table is None:
        item.notes.append(f"R28：{rid} 沒有 {table_day} 適用的分級表")
        return
    item.rules.append(versions.ref(table))
    g = lookup_grade(table["params"], bases[base_name])
    if g is None:
        item.notes.append(f"{rid}：{bases[base_name]} 元超出已登錄的分級表範圍（{table['params'].get('partial', '')}）")
        return
    item.expected_grade, item.expected_amount = g["grade"], g["amount"]


def lookup_grade(params: dict, amount: Decimal) -> dict | None:
    if params.get("lower_bound") and amount < params["lower_bound"]:
        return None
    for g in params["grades"]:
        if g["upper"] is None or amount <= g["upper"]:
            return g
    return None


def days_late(item_legal_effective: date | None, actual_effective: date | None) -> int | None:
    """R35：實際生效日 − 法定生效日，不足 0 以 0 計；法定生效日待確認的不算。"""
    if item_legal_effective is None or actual_effective is None:
        return None
    return max(0, (actual_effective - item_legal_effective).days)
