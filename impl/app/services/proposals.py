"""ProposeEnrollmentFiling（加保待辦，建議層事件）、待人判斷的決定，與 UC-02 判定查詢。

加保待辦是事實（PLAN.md D-35 P3）：判定內容產生後不改；被取代、各保險結案、雇主不加自願保險、
待人判斷事項的決定是之後的記錄（P2 B）。新的判定沿用之前的決定（03_flows D-19、04_rules D-16）。
"""
from datetime import date, datetime

from bson import ObjectId

from app.auth import Actor
from app.db import now, oid, run_in_transaction, to_date, to_dt
from app.errors import Blocked, NotFound
from app.rules import applicability as ap
from app.rules import versions
from app.spec import RequestInvalid
from app.store import clean, get_current, record_event, update_with_changelog

SYSTEM = {"role": "system"}
DECISION_RESULTS = {"EMPLOYMENT_INSURANCE_CHOICE": {"JOIN", "NOT_JOIN"}, "ALLOWANCE_INCLUSION": {"INCLUDED", "EXCLUDED"}}


def _links(subj: ap.Subject) -> list[dict]:
    links = [{"hire_id": subj.hire_id}] if subj.hire_id else []
    if subj.employment:
        links.append({"employment_id": subj.employment["entity_id"]})
    return links


def current_proposal(db, tenant_id, links: list[dict], session=None) -> dict | None:
    return db.enrollment_proposals.find_one({"tenant_id": tenant_id, "$or": links, "superseded_by": {"$exists": False}},
                                            sort=[("_id", -1)], session=session)


def propose_enrollment_filing(db, s, subj: ap.Subject, on: date, *, cause_event_id: ObjectId | None,
                              event_id: ObjectId | None = None) -> ObjectId:
    previous = current_proposal(db, subj.tenant_id, _links(subj), s)
    decisions = ap.Decisions.of_proposal(previous)                             # 沿用之前的決定
    facts = ap.load_facts(db, subj, on, session=s, decisions=decisions)
    items = ap.determine(db, facts, on, session=s)
    all_refs = _unique(r for i in items for r in i.rules)
    pid, event_id = ObjectId(), event_id or ObjectId()
    record_event(db, s, tenant_id=subj.tenant_id, type="ProposeEnrollmentFiling",
                 subject=("enrollment_proposals", pid), actor=SYSTEM, rule_versions=all_refs, derived=True,
                 event_id=event_id)
    prev_items = {it["scheme_code"]: it for it in (previous or {}).get("items", [])}
    docs = []
    for i in items:
        d = i.to_doc()
        carried = prev_items.get(i.scheme_code, {}).get("decisions")
        if carried:
            d["decisions"] = carried
        docs.append(d)
    db.enrollment_proposals.insert_one(clean({
        "_id": pid, "tenant_id": subj.tenant_id, "hire_id": subj.hire_id,
        "employment_id": subj.employment["entity_id"] if subj.employment else None, "determined_on": to_dt(on),
        "estimated": subj.estimated,
        "allowance_decisions": (previous or {}).get("allowance_decisions"),
        "basis": {"data": facts.data_refs, "headcount": facts.headcount, "other_employers": facts.other_employers,
                  "rule_versions": all_refs, "cause_event_id": cause_event_id,
                  "items": {i.scheme_code: clean({"rule_versions": i.rules, "pending": i.pending or None,
                                                  "missing_data": i.missing or None, "underlying": i.underlying})
                            for i in items}},
        "items": docs, "created_at": now(),
    }), session=s)
    if previous:
        update_with_changelog(db, s, "enrollment_proposals", previous, {"superseded_by": pid}, event_id=event_id,
                              actor=SYSTEM)
    return pid


def _unique(refs):
    seen, out = set(), []
    for r in refs:
        k = (r["rule_id"], r["version"], r["revision"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


# ---------------- 待人判斷的決定（POST /v1/enrollment-proposals/{id}/decisions） ----------------

def record_decision(db, actor: Actor, proposal_id: str, body: dict) -> dict:
    """記在加保待辦上（04_rules D-16、05_mapping D-21）。

    暫時：記錄決定後立刻依決定重新判定，產生新的待辦取代這一筆，回應的 proposal_id 是新的待辦；
    03 沒有「記錄決定」的事件，回應的 event_id 是重新判定的 ProposeEnrollmentFiling，決定本身記在 change_log（signoff.md #19）。
    """
    kind, result = body["kind"], body["result"]
    if result not in DECISION_RESULTS[kind]:
        raise RequestInvalid([f"result：{kind} 只接受 {'／'.join(sorted(DECISION_RESULTS[kind]))}"])
    if kind == "EMPLOYMENT_INSURANCE_CHOICE" and body.get("scheme_code") != ap.EI:
        raise RequestInvalid([f"scheme_code：擇一參加只用於 {ap.EI}"])
    if kind == "ALLOWANCE_INCLUSION" and not body.get("allowance_name"):
        raise RequestInvalid(["allowance_name：固定給付的決定必填"])

    def tx(s):
        p = get_current(db, "enrollment_proposals", oid(proposal_id), actor.tenant_id, s)
        if "superseded_by" in p:
            raise Blocked(None, "PROPOSAL_SUPERSEDED", f"這筆待辦已被 {p['superseded_by']} 取代")
        decision = clean({"kind": kind, "result": result, "by": actor.account_id, "at": now(),
                          "reason": body.get("reason"), "allowance_name": body.get("allowance_name")})
        subj = _subject_of(db, p, s)
        if kind == "EMPLOYMENT_INSURANCE_CHOICE":
            items = p["items"]
            it = next(i for i in items if i["scheme_code"] == ap.EI)
            if it["applicability"] != ap.NEEDS_DECISION and not it.get("decisions"):
                raise Blocked("R24", "NOT_NEEDS_DECISION", "就保不是待人判斷")
            it.setdefault("decisions", []).append(decision)
            changes = {"items": items}
        else:
            comp = ap.compensation_on(db, subj, to_date(p["determined_on"]), session=s)
            r39 = versions.rule(db, "R39", to_date(p["determined_on"]), session=s)
            names = {a["name"] for a in (comp or {}).get("fixed_monthly_allowances") or []
                     if a["category"] in r39["params"].get("needs_decision", [])}
            if body["allowance_name"] not in names:
                raise Blocked("R39", "NOT_NEEDS_DECISION", f"約定薪資沒有待人判斷的固定給付「{body['allowance_name']}」")
            changes = {"allowance_decisions": [*p.get("allowance_decisions", []), decision]}
        event_id = ObjectId()
        update_with_changelog(db, s, "enrollment_proposals", p, changes, event_id=event_id, actor=actor.event_actor)
        new_id = propose_enrollment_filing(db, s, subj, to_date(p["determined_on"]), cause_event_id=None, event_id=event_id)
        return {"event_id": str(event_id), "proposal_id": str(new_id), "warnings": []}
    return run_in_transaction(db, tx)


def _subject_of(db, p: dict, s) -> ap.Subject:
    if p.get("employment_id"):
        return ap.Subject.of_employment(db.employments.find_one({"entity_id": p["employment_id"], "is_current": True}, session=s))
    return ap.Subject.of_hire(db.hires.find_one({"_id": p["hire_id"]}, session=s))


# ---------------- 查詢 ----------------

def _is_open(p: dict) -> bool:
    basis = p["basis"].get("items", {})
    return "superseded_by" not in p and any(
        (basis.get(it["scheme_code"], {}).get("underlying") or it["applicability"]) in (ap.MANDATORY, ap.VOLUNTARY, ap.NEEDS_DECISION)
        and not it.get("closed_by_enrollment_id") and not it.get("voluntary_declined") for it in p["items"])


def list_proposals(db, tenant_id, employment_id: str | None, hire_id: str | None, open_only: bool | None,
                   today: date) -> dict:
    """GET /v1/enrollment-proposals → EnrollmentProposalList（含預估、逾期天數、待人判斷）。"""
    q = {"tenant_id": tenant_id}
    if employment_id:
        q["employment_id"] = oid(employment_id)
    if hire_id:
        q["hire_id"] = oid(hire_id)
    out = []
    for p in db.enrollment_proposals.find(q).sort([("determined_on", 1), ("_id", 1)]):
        if open_only and not _is_open(p):
            continue
        out.append(proposal_view(db, p, today))
    return {"items": out}


def _decision_view(d: dict) -> dict:
    return {k: (str(v) if k == "by" else v.isoformat() if k == "at" else v) for k, v in d.items()}


def proposal_view(db, p: dict, today: date) -> dict:
    """EnrollmentProposal（api.yaml）：判定內容取自存下的待辦；晚辦、逾期天數現算（R35、R36）。"""
    basis_items = p["basis"].get("items", {})
    items = []
    for it in p["items"]:
        b = basis_items.get(it["scheme_code"], {})
        closed = bool(it.get("closed_by_enrollment_id"))
        view = {"scheme_code": it["scheme_code"], "applicability": it["applicability"],
                "decisions": [_decision_view(d) for d in it.get("decisions", [])] or None,
                "filing_deadline": _iso(it.get("filing_deadline")), "legal_effective_date": _iso(it.get("legal_effective_date")),
                "expected_grade": it.get("expected_grade"), "expected_amount": _amount(db, it, b),
                "days_overdue": None if "superseded_by" in p else
                ap.days_overdue(b.get("underlying") or it["applicability"], it.get("filing_deadline"), today, closed),
                "pending": b.get("pending"), "rule_versions": b.get("rule_versions"),
                "closed_by_enrollment_id": str(it["closed_by_enrollment_id"]) if closed else None}
        if closed and it["applicability"] == ap.MANDATORY:
            enr = db.insurance_enrollments.find_one({"entity_id": it["closed_by_enrollment_id"], "is_current": True})
            if enr and not enr["voluntary"]:
                view["days_late"] = ap.days_late(to_date(it.get("legal_effective_date")), to_date(enr.get("effective_from")))
        if it.get("voluntary_declined"):
            view["voluntary_declined"] = {"by": str(it["voluntary_declined"]["by"]), "at": it["voluntary_declined"]["at"].isoformat()}
        items.append({k: v for k, v in view.items() if v is not None})
    return {k: v for k, v in {
        "enrollment_proposal_id": str(p["_id"]), "hire_id": str(p["hire_id"]) if p.get("hire_id") else None,
        "employment_id": str(p["employment_id"]) if p.get("employment_id") else None,
        "determined_on": _iso(p["determined_on"]), "estimated": p.get("estimated"),
        "allowance_decisions": [_decision_view(d) for d in p.get("allowance_decisions", [])] or None,
        "items": items, "superseded_by": str(p["superseded_by"]) if p.get("superseded_by") else None}.items()
        if v is not None}


def _iso(v):
    return to_date(v).isoformat() if v else None


def _amount(db, item: dict, basis_item: dict) -> str | None:
    """預計的投保薪資：用判定時記下的分級表版本，把級距換成金額。"""
    if not item.get("expected_grade"):
        return None
    table_ref = next((r for r in basis_item.get("rule_versions", []) if r["rule_id"] in ("R40", "R41", "R42", "R43")), None)
    rv = db.rule_versions.find_one(table_ref) if table_ref else None
    g = next((g for g in rv["params"]["grades"] if g["grade"] == item["expected_grade"]), None) if rv else None
    return str(g["amount"]) if g else None


def applicability_on(db, tenant_id, employment_id: ObjectId, on: date, as_of: datetime | None, today: date) -> dict:
    """GET /v1/employments/{id}/applicability → ApplicabilityOut：現算，不落地；沿用加保待辦上的決定；
    as_of 只看當時已登錄的版本（03_flows D-10）。"""
    get_current(db, "employments", employment_id, tenant_id)       # 找不到或不屬於呼叫者 → 404／403
    emps = versions.snapshot(db, "employments", {"entity_id": employment_id}, as_of)
    if not emps:
        raise NotFound(f"{as_of} 時系統還沒有這段僱傭關係")
    subj = ap.Subject.of_employment(emps[0])
    prop = current_proposal(db, tenant_id, _links(subj))
    decisions = ap.Decisions.of_proposal(prop)
    facts = ap.load_facts(db, subj, on, as_of, decisions=decisions)
    prop_items = {it["scheme_code"]: it for it in (prop or {}).get("items", [])}
    items, missing = [], []
    for i in ap.determine(db, facts, on, as_of):
        missing += [m for m in i.missing if m not in missing]
        enr = _first_enrollment(db, employment_id, i.scheme_code, as_of)
        late = ap.days_late(i.legal_effective_date, to_date(enr.get("effective_from"))) \
            if enr and i.applicability == ap.MANDATORY and not enr["voluntary"] else None
        overdue = ap.days_overdue(i.underlying or i.applicability, i.filing_deadline, today, closed=enr is not None)
        decided = [_decision_view(d) for d in prop_items.get(i.scheme_code, {}).get("decisions", [])]
        items.append(i.to_api(late, overdue, decided))
    out = {"employment_id": str(employment_id), "on": on.isoformat(), "items": items}
    if as_of:
        out["as_of"] = as_of.isoformat()
    if missing:
        out["missing_data"] = missing
    return out


def _first_enrollment(db, employment_id, scheme_code, as_of) -> dict | None:
    scheme = db.social_insurance_schemes.find_one({"code": scheme_code})
    enrs = [e for e in versions.snapshot(db, "insurance_enrollments", {"employment_id": employment_id, "scheme_id": scheme["_id"]}, as_of)
            if not e.get("annulled")]
    return min(enrs, key=lambda e: e.get("effective_from") or e["filed_on"], default=None)
