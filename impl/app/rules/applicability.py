"""各保險的適用、應辦理期限、法定生效日、應申報級距（04_rules @ 04-v2：R22～R35、R39～R44、R60）。

結果是推導值（P3）：不落地，只寫進加保待辦（記當時的資料與規則版本），或在查詢時現算。
判定的對象是一段僱傭關係，或還沒到職的錄用（以約定到職日為到職日；03_flows ProposeEnrollmentFiling 的觸發來源含決定錄用）。
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.db import to_date, to_dt
from app.rules import versions
from app.seed import EI, LI, LP, NHI, OAI

MANDATORY, VOLUNTARY, NA = "APPLICABILITY.MANDATORY", "APPLICABILITY.VOLUNTARY", "APPLICABILITY.NOT_APPLICABLE"
NEEDS_DECISION = "APPLICABILITY.NEEDS_DECISION"                               # 待人判斷（04_rules D-16）
NOT_YET, NO_RULE, INSUFFICIENT = "APPLICABILITY.NOT_YET_IN_FORCE", "APPLICABILITY.NO_RULE_VERSION", "APPLICABILITY.INSUFFICIENT_DATA"
ROC = "TW"
SCHEME_ORDER = (LI, EI, OAI, NHI, LP)
SCHEME_RULE = {LI: "R22", EI: "R24", OAI: "R25", NHI: "R26", LP: "R27"}
DEADLINE_RULE = {LI: "R31", EI: "R31", OAI: "R32", NHI: "R33", LP: "R34"}
GRADE_RULE = {LI: "R40", EI: "R40", OAI: "R41", LP: "R42", NHI: "R43"}


# ---------------- 判定所需的資料 ----------------

@dataclass
class Subject:
    """判定的對象：僱傭關係，或還沒到職的錄用。"""
    tenant_id: object
    person_id: object
    employer_id: object
    start_date: date
    hire_id: object | None = None
    employment: dict | None = None
    estimated: bool = False

    @property
    def public_or_military(self):
        return (self.employment or {}).get("public_or_military_insurance_covered")

    @classmethod
    def of_employment(cls, e: dict) -> "Subject":
        return cls(e["tenant_id"], e["person_id"], e["employer_id"], to_date(e["start_date"]), e.get("hire_id"), e)

    @classmethod
    def of_hire(cls, h: dict) -> "Subject":
        """錄用時（還沒到職）以約定到職日為預計到職日與判定日，結果是預估（04_rules D-18）。"""
        return cls(h["tenant_id"], h["person_id"], h["employer_id"], to_date(h["planned_start_date"]), h["_id"], estimated=True)


@dataclass
class Decisions:
    """加保待辦上記下的人的決定（04_rules D-16）：新的判定沿用。"""
    employment_insurance: str | None = None          # JOIN／NOT_JOIN
    allowances: dict[str, str] = field(default_factory=dict)   # 固定給付名稱 → INCLUDED／EXCLUDED

    @classmethod
    def of_proposal(cls, p: dict | None) -> "Decisions":
        if not p:
            return cls()
        ei = [d for it in p["items"] if it["scheme_code"] == EI for d in it.get("decisions", [])]
        return cls(employment_insurance=ei[-1]["result"] if ei else None,
                   allowances={d["allowance_name"]: d["result"] for d in p.get("allowance_decisions", [])})


@dataclass
class Facts:
    subject: Subject
    person: dict
    employer: dict
    identity_documents: list[dict]
    compensation: dict | None
    work_authorizations: list[dict]
    headcount: int
    schemes: dict[str, dict]
    tw_id: object
    other_employers: int = 0
    decisions: Decisions = field(default_factory=Decisions)

    @property
    def data_refs(self) -> dict:
        """加保待辦 basis：判定用到的資料版本。"""
        refs = {"person": _ver(self.person), "employer_id": self.employer["_id"]}
        if self.subject.employment:
            refs["employment"] = _ver(self.subject.employment)
        if self.subject.hire_id:
            refs["hire_id"] = self.subject.hire_id
        if self.compensation:
            refs["compensation"] = _ver(self.compensation)
        return refs


def _ver(doc):
    return {"entity_id": doc["entity_id"], "revision": doc["revision"]}


def load_facts(db, subj: Subject, on: date, as_of: datetime | None = None, session=None,
               decisions: Decisions | None = None) -> Facts:
    t = subj.tenant_id
    persons = versions.snapshot(db, "persons", {"entity_id": subj.person_id}, as_of, session)
    return Facts(
        subject=subj, person=persons[0],
        employer=db.employers.find_one({"_id": subj.employer_id}, session=session),
        identity_documents=versions.snapshot(db, "identity_documents", {"tenant_id": t, "person_id": subj.person_id}, as_of, session),
        compensation=compensation_on(db, subj, on, as_of, session),
        work_authorizations=versions.snapshot(db, "work_authorizations", {"tenant_id": t, "person_id": subj.person_id}, as_of, session),
        headcount=headcount(db, t, subj.employer_id, on, as_of, session),
        schemes={s["code"]: s for s in db.social_insurance_schemes.find({}, session=session)},
        tw_id=db.jurisdictions.find_one({"code": "TW"}, session=session)["_id"],
        other_employers=other_employers(db, subj, on, as_of, session),
        decisions=decisions or Decisions(),
    )


def other_employers(db, subj: Subject, on: date, as_of=None, session=None) -> int:
    """判定日同一人在其他雇主的在職僱傭關係數（R24 受僱於兩個以上雇主）。

    暫時：只看得到同一客戶內的僱傭關係，客戶以外的兼職沒有資料（signoff.md #20）。
    """
    d = to_dt(on)
    emps = versions.snapshot(db, "employments", {"tenant_id": subj.tenant_id, "person_id": subj.person_id}, as_of, session)
    return len({e["employer_id"] for e in emps if e["employer_id"] != subj.employer_id and not e.get("annulled")
                and e["start_date"] <= d and (e.get("ended_on") is None or e["ended_on"] >= d)})


def compensation_on(db, subj: Subject, on: date, as_of=None, session=None) -> dict | None:
    """約定薪資：連到這段僱傭關係或它的錄用、判定日已生效者中最晚生效的一筆。"""
    links = []
    if subj.employment:
        links.append({"employment_id": subj.employment["entity_id"]})
    if subj.hire_id:
        links.append({"hire_id": subj.hire_id})
    comps = [c for c in versions.snapshot(db, "compensations", {"tenant_id": subj.tenant_id, "$or": links}, as_of, session)
             if to_date(c["effective_from"]) <= on]
    return max(comps, key=lambda c: c["effective_from"], default=None)


def headcount(db, tenant_id, employer_id, on: date, as_of=None, session=None) -> int:
    """R23：判定日那天的在職人數，依各段僱傭關係實際到職、結束日計算；被註銷的不算（D-11）。計入範圍待 EQ-008。"""
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
    """沒有登錄任何國籍 → None（資料不足）。"""
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
    return [d for d in facts.identity_documents if not d.get("annulled")
            and to_date(d["valid_from"]) <= on and (d.get("valid_until") is None or on <= to_date(d["valid_until"]))]


def residence_bases(facts: Facts, on: date) -> set[str]:
    return {d["residence_basis"] for d in valid_docs(facts, on) if d.get("residence_basis")}


# ---------------- 結果 ----------------

@dataclass
class Item:
    scheme_code: str
    applicability: str
    filing_deadline: date | None = None
    legal_effective_date: date | None = None
    expected_grade: str | None = None
    expected_amount: int | None = None
    pending: list[str] = field(default_factory=list)
    rules: list[dict] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    underlying: str | None = None    # 標成待人判斷之前的適用結果（signoff.md #18）

    def to_doc(self) -> dict:
        """加保待辦 items[] 的一列（05_mapping 1.2）。"""
        return {k: v for k, v in {
            "scheme_code": self.scheme_code, "applicability": self.applicability,
            "filing_deadline": to_dt(self.filing_deadline), "legal_effective_date": to_dt(self.legal_effective_date),
            "expected_grade": self.expected_grade}.items() if v is not None}

    def to_api(self, days_late: int | None = None, days_overdue: int | None = None, decisions=None) -> dict:
        """ApplicabilityItem（api.yaml）。"""
        return {k: v for k, v in {
            "scheme_code": self.scheme_code, "applicability": self.applicability, "decisions": decisions or None,
            "filing_deadline": iso(self.filing_deadline), "legal_effective_date": iso(self.legal_effective_date),
            "expected_grade": self.expected_grade,
            "expected_amount": str(self.expected_amount) if self.expected_amount is not None else None,
            "days_late": days_late, "days_overdue": days_overdue, "pending": self.pending or None,
            "rule_versions": self.rules}.items()
            if v is not None}


def iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def determine(db, facts: Facts, on: date, as_of=None, session=None) -> list[Item]:
    items = []
    for code in SCHEME_ORDER:
        item = _applicability(db, facts, code, on, as_of, session)
        if item.applicability == MANDATORY:
            _deadlines(db, facts, item, as_of, session)
        if item.applicability in (MANDATORY, VOLUNTARY):
            _grade(db, facts, item, as_of, session)
        items.append(item)
    return items


def days_overdue(applicability: str, filing_deadline, today: date, closed: bool) -> int | None:
    """R36：強制保險的應辦理期限已過、還沒登錄實際辦理 → 逾期天數（判定，不是警告；04_rules D-17）。

    applicability 傳標成待人判斷之前的結果（signoff.md #18）。
    """
    deadline = to_date(filing_deadline)
    if applicability != MANDATORY or closed or deadline is None or today <= deadline:
        return None
    return (today - deadline).days


# ---------------- 適用（R22～R28、R60） ----------------

def _applicability(db, facts: Facts, code: str, on: date, as_of, session) -> Item:
    if on < to_date(facts.schemes[code]["effective_from"]):                   # R28
        return Item(code, NOT_YET)
    rid = SCHEME_RULE[code]
    rv = versions.rule(db, rid, on, as_of, session)
    if rv is None:                                                             # R28
        return Item(code, NO_RULE)
    item = Item(code, NA, rules=[versions.ref(rv)])
    p, person, employer = rv["params"], facts.person, facts.employer
    birth = to_date(person.get("birth_date"))
    age = age_on(birth, on) if birth else None
    national = is_national(person, on)

    def insufficient(*what):                                                   # R60
        item.applicability, item.missing = INSUFFICIENT, list(what)
        return item

    if code == LI:                                                             # R22、R23、R29
        if age is None:
            return insufficient("Person.birth_date")
        if age == p["max_age"] or person.get("old_age_benefits_received"):
            item.pending.append("EQ-006")
        if not (p["min_age"] <= age <= p["max_age"]):
            return item                                                        # ③ 不適用
        cat = value_on(employer.get("labor_insurance_industry_category"), on, key="code")
        if cat is None:
            return insufficient("Employer.labor_insurance_industry_category")
        if cat in p["threshold_categories"]:
            item.pending.append("EQ-008")
            item.applicability = MANDATORY if facts.headcount >= p["headcount_threshold"] else VOLUNTARY
        elif cat in p["no_threshold_categories"]:
            item.applicability = MANDATORY
        else:
            item.applicability = VOLUNTARY                                     # ② 不屬 §6 各款
        if item.applicability == VOLUNTARY:
            item.pending.append("EQ-004")

    elif code == EI:                                                           # R24
        missing = [n for n, v in (("Person.birth_date", age), ("Person.nationalities", national)) if v is None]
        if missing:
            return insufficient(*missing)
        if age == p["max_age"]:
            item.pending.append("EQ-006")
        if not (p["min_age"] <= age <= p["max_age"]):
            return item
        if person.get("old_age_benefits_received"):
            return item
        if value_on(facts.subject.public_or_military, on):                    # 應參加公教或軍保（04_rules D-15）
            return item
        if value_on(employer.get("registration_exempt"), on) and not value_on(employer.get("tax_assessed_or_invoice_permit"), on):
            return item
        if national or residence_bases(facts, on) & set(p["residence_basis"]):
            item.applicability = MANDATORY
            if facts.other_employers:                                          # 受僱於兩個以上雇主得擇一參加（D-16）
                choice = facts.decisions.employment_insurance
                item.applicability = {"JOIN": MANDATORY, "NOT_JOIN": NA}.get(choice, NEEDS_DECISION)

    elif code == OAI:                                                          # R25
        regs = {r["kind"] for r in employer.get("registrations") or [] if to_date(r["registered_on"]) <= on}
        permit = any(a.get("employer_id") == employer["_id"] and a.get("authorization_basis") == "AUTHORIZATION_BASIS.EMPLOYER_PERMIT"
                     for a in facts.work_authorizations)
        cat = value_on(employer.get("labor_insurance_industry_category"), on, key="code")
        if regs & set(p["registration_kinds"]) or permit:
            if age is None:
                return insufficient("Person.birth_date")
            if age >= p["min_age"]:
                item.applicability = MANDATORY                                 # ①
            elif value_on(employer.get("labor_standards_act_applicable"), on):
                item.applicability = MANDATORY                                 # ② 未滿 15 歲、依勞基法受僱
        if item.applicability == NA and cat in p["public_sector_categories"]:
            item.applicability = MANDATORY                                     # ③ [解讀] 以勞保行業類別第 4 款判斷
        if item.applicability == NA:
            # 暫時：④ 公告的「第 6 條以外雇主」沒有資料，一律不判成可自願（signoff.md #12）
            item.pending.append("EQ-023")                                      # ⑤ 不適用

    elif code == NHI:                                                          # R26
        if national is None:
            return insufficient("Person.nationalities")
        kinds = {d["document_kind"] for d in valid_docs(facts, on)}
        if national and has_civil_registration(person, facts.tw_id, on):
            item.applicability = MANDATORY
        elif kinds & set(p["residence_document_kinds"]):
            item.applicability = MANDATORY                                     # 外國籍，或本國籍無戶籍，有居留證明

    elif code == LP:                                                           # R27
        if national is None:
            return insufficient("Person.nationalities")
        lsa = value_on(employer.get("labor_standards_act_applicable"), on)
        if national or residence_bases(facts, on) & set(p["residence_basis"]):
            item.applicability = MANDATORY if lsa else VOLUNTARY
    return item


# ---------------- 期限與法定生效日（R31～R34、R37） ----------------

def _deadlines(db, facts: Facts, item: Item, as_of, session) -> None:
    start = facts.subject.start_date                                           # R37：依到職日
    code = item.scheme_code
    rv = versions.rule(db, DEADLINE_RULE[code], start, as_of, session)
    if rv is None:
        return
    item.rules.append(versions.ref(rv))
    p = rv["params"]
    if code in (LI, EI):
        item.filing_deadline = item.legal_effective_date = start + timedelta(days=p["deadline_offset_days"])
    elif code == OAI:
        regs = [to_date(r["registered_on"]) for r in facts.employer.get("registrations") or [] if r["kind"] in p["registration_kinds"]]
        item.filing_deadline = item.legal_effective_date = max(start, min(regs)) if regs else start
    else:
        qualified = start
        if code == NHI and not is_national(facts.person, start):              # [解讀] R33：外籍取到職日與居留證明生效日較晚者
            r26 = versions.rule(db, "R26", start, as_of, session)
            docs = [to_date(d["valid_from"]) for d in facts.identity_documents
                    if d["document_kind"] in r26["params"]["residence_document_kinds"]]
            if docs:
                qualified = max(start, min(docs))
        item.filing_deadline = qualified + timedelta(days=p["window_days"])    # 始日不算入
        item.pending.append(p["pending"])                                      # 法定生效日 EQ-003，不給值


# ---------------- 應申報級距（R39～R44） ----------------

def wage_bases(db, comp: dict | None, on: date, as_of=None, session=None, decisions: "Decisions | None" = None):
    """R39：三種薪資基礎。回傳 ({基礎名稱: 金額}, 規則版本, 待人判斷的固定給付名稱)；沒有約定薪資或待人判斷時金額為 None。"""
    rv = versions.rule(db, "R39", on, as_of, session)
    if comp is None or rv is None:
        return None, rv, []
    base = Decimal(str(comp["monthly_base_salary"].to_decimal()))
    decided = (decisions or Decisions()).allowances
    undecided = [a["name"] for a in comp.get("fixed_monthly_allowances") or []
                 if a["category"] in rv["params"].get("needs_decision", []) and a["name"] not in decided]
    if undecided:
        return None, rv, undecided                                             # 「其他」類待人判斷（04_rules D-16）
    out = {}
    for name, spec in rv["params"]["bases"].items():
        out[name] = base + sum((a["amount"].to_decimal() for a in comp.get("fixed_monthly_allowances") or []
                                if a["category"] in spec["included_allowances"]
                                or decided.get(a["name"]) == "INCLUDED"), Decimal(0))
    return out, rv, []


def base_for(r39: dict, scheme_code: str) -> str:
    return next(n for n, s in r39["params"]["bases"].items() if scheme_code in s["schemes"])


def _grade(db, facts: Facts, item: Item, as_of, session) -> None:
    table_day = facts.subject.start_date                                      # R44：預設依到職日的分級表
    bases, r39, undecided = wage_bases(db, facts.compensation, table_day, as_of, session, facts.decisions)
    if undecided:
        # 暫時：「其他」類固定給付未決定時，把需要級距的項目標成待人判斷，原本的適用結果另存 underlying，
        # 期限與法定生效日照樣給（signoff.md #18）
        item.underlying, item.applicability = item.applicability, NEEDS_DECISION
        item.rules.append(versions.ref(r39))
        return
    if bases is None:
        item.missing.append("Compensation")                                    # R60：級距算不出來
        return
    item.rules.append(versions.ref(r39))
    if facts.compensation.get("fixed_monthly_allowances"):
        item.pending.append(r39["params"]["pending"])                          # EQ-012
    r44 = versions.rule(db, "R44", table_day, as_of, session)
    if r44:
        item.rules.append(versions.ref(r44))
    table = versions.rule(db, GRADE_RULE[item.scheme_code], table_day, as_of, session)
    if table is None:
        return                                                                 # R28：沒有對應的分級表版本
    item.rules.append(versions.ref(table))
    g = lookup_grade(table["params"], bases[base_for(r39, item.scheme_code)])
    item.expected_grade, item.expected_amount = g["grade"], g["amount"]


def lookup_grade(params: dict, amount: Decimal) -> dict:
    for g in params["grades"]:
        if g["upper"] is None or amount <= g["upper"]:
            return g
    return params["grades"][-1]


def days_late(legal_effective: date | None, actual_effective: date | None) -> int | None:
    """R35：實際生效日 − 法定生效日，不足 0 以 0 計；法定生效日待確認或自願加保的不算。"""
    if legal_effective is None or actual_effective is None:
        return None
    return max(0, (actual_effective - legal_effective).days)
