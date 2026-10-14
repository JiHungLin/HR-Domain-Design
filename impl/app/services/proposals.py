"""ProposeEnrollmentFiling（加保待辦，建議層事件）與 UC-02 判定查詢。

加保待辦是事實（PLAN.md D-35 P3）：判定內容產生後不改；被取代、各保險結案、雇主不加自願保險是之後的記錄（P2 B）。
"""
from datetime import date, datetime

from bson import ObjectId

from app.db import now, oid, to_date, to_dt
from app.errors import NotFound
from app.rules import applicability as ap
from app.rules import versions
from app.store import clean, get_current, record_event, update_with_changelog

SYSTEM = {"role": "system"}


def propose_enrollment_filing(db, s, subj: ap.Subject, on: date, *, cause_event_id: ObjectId) -> ObjectId:
    facts = ap.load_facts(db, subj, on, session=s)
    items = ap.determine(db, facts, on, session=s)
    all_refs = _unique(r for i in items for r in i.rules)
    pid, event_id = ObjectId(), ObjectId()
    record_event(db, s, tenant_id=subj.tenant_id, type="ProposeEnrollmentFiling",
                 subject=("enrollment_proposals", pid), actor=SYSTEM, rule_versions=all_refs, derived=True,
                 event_id=event_id)
    db.enrollment_proposals.insert_one(clean({
        "_id": pid, "tenant_id": subj.tenant_id, "hire_id": subj.hire_id,
        "employment_id": subj.employment["entity_id"] if subj.employment else None, "determined_on": to_dt(on),
        "basis": {"data": facts.data_refs, "headcount": facts.headcount, "rule_versions": all_refs,
                  "cause_event_id": cause_event_id,
                  "items": {i.scheme_code: clean({"rule_versions": i.rules, "pending": i.pending or None,
                                                  "missing_data": i.missing or None}) for i in items}},
        "items": [i.to_doc() for i in items], "created_at": now(),
    }), session=s)
    # 取代同一錄用或僱傭關係先前的待辦
    links = [{"hire_id": subj.hire_id}] if subj.hire_id else []
    if subj.employment:
        links.append({"employment_id": subj.employment["entity_id"]})
    for old in db.enrollment_proposals.find({"tenant_id": subj.tenant_id, "$or": links, "_id": {"$ne": pid},
                                             "superseded_by": {"$exists": False}}, session=s):
        update_with_changelog(db, s, "enrollment_proposals", old, {"superseded_by": pid}, event_id=event_id, actor=SYSTEM)
    return pid


def _unique(refs):
    seen, out = set(), []
    for r in refs:
        k = (r["rule_id"], r["version"], r["revision"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def _is_open(p: dict) -> bool:
    return "superseded_by" not in p and any(
        it["applicability"] in (ap.MANDATORY, ap.VOLUNTARY) and not it.get("closed_by_enrollment_id")
        and not it.get("voluntary_declined") for it in p["items"])


def list_proposals(db, tenant_id, employment_id: str | None, hire_id: str | None, open_only: bool | None) -> dict:
    """GET /v1/enrollment-proposals → EnrollmentProposalList。

    暫時：R36 逾期未辦的警告，EnrollmentProposalList 沒有欄位可以回傳，未輸出（signoff.md #15）。
    """
    q = {"tenant_id": tenant_id}
    if employment_id:
        q["employment_id"] = oid(employment_id)
    if hire_id:
        q["hire_id"] = oid(hire_id)
    out = []
    for p in db.enrollment_proposals.find(q).sort([("determined_on", 1), ("_id", 1)]):
        if open_only and not _is_open(p):
            continue
        out.append(proposal_view(db, p))
    return {"items": out}


def proposal_view(db, p: dict) -> dict:
    """EnrollmentProposal（api.yaml）：判定內容取自存下的待辦，晚辦天數依結案的投保現算（R35）。"""
    basis_items = p["basis"].get("items", {})
    items = []
    for it in p["items"]:
        b = basis_items.get(it["scheme_code"], {})
        view = {"scheme_code": it["scheme_code"], "applicability": it["applicability"],
                "filing_deadline": _iso(it.get("filing_deadline")), "legal_effective_date": _iso(it.get("legal_effective_date")),
                "expected_grade": it.get("expected_grade"), "expected_amount": _amount(db, it, b),
                "pending": b.get("pending"), "rule_versions": b.get("rule_versions"),
                "closed_by_enrollment_id": str(it["closed_by_enrollment_id"]) if it.get("closed_by_enrollment_id") else None}
        if it.get("closed_by_enrollment_id") and it["applicability"] == ap.MANDATORY:
            enr = db.insurance_enrollments.find_one({"entity_id": it["closed_by_enrollment_id"], "is_current": True})
            if enr and not enr["voluntary"]:
                view["days_late"] = ap.days_late(to_date(it.get("legal_effective_date")), to_date(enr.get("effective_from")))
        if it.get("voluntary_declined"):
            view["voluntary_declined"] = {"by": str(it["voluntary_declined"]["by"]), "at": it["voluntary_declined"]["at"].isoformat()}
        items.append({k: v for k, v in view.items() if v is not None})
    return {k: v for k, v in {
        "enrollment_proposal_id": str(p["_id"]), "hire_id": str(p["hire_id"]) if p.get("hire_id") else None,
        "employment_id": str(p["employment_id"]) if p.get("employment_id") else None,
        "determined_on": _iso(p["determined_on"]), "items": items,
        "superseded_by": str(p["superseded_by"]) if p.get("superseded_by") else None}.items() if v is not None}


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


def applicability_on(db, tenant_id, employment_id: ObjectId, on: date, as_of: datetime | None) -> dict:
    """GET /v1/employments/{id}/applicability → ApplicabilityOut：現算，不落地；as_of 只看當時已登錄的版本（03_flows D-10）。"""
    get_current(db, "employments", employment_id, tenant_id)       # 找不到或不屬於呼叫者 → 404／403
    emps = versions.snapshot(db, "employments", {"entity_id": employment_id}, as_of)
    if not emps:
        raise NotFound(f"{as_of} 時系統還沒有這段僱傭關係")
    subj = ap.Subject.of_employment(emps[0])
    facts = ap.load_facts(db, subj, on, as_of)
    items, missing = [], []
    for i in ap.determine(db, facts, on, as_of):
        missing += [m for m in i.missing if m not in missing]
        items.append(i.to_api(_days_late(db, employment_id, i, as_of)))
    out = {"employment_id": str(employment_id), "on": on.isoformat(), "items": items}
    if as_of:
        out["as_of"] = as_of.isoformat()
    if missing:
        out["missing_data"] = missing
    return out


def _days_late(db, employment_id, item: ap.Item, as_of) -> int | None:
    """R35：這種保險已登錄的強制加保，實際生效日 − 法定生效日。"""
    if item.applicability != ap.MANDATORY or item.legal_effective_date is None:
        return None
    scheme = db.social_insurance_schemes.find_one({"code": item.scheme_code})
    enrs = [e for e in versions.snapshot(db, "insurance_enrollments", {"employment_id": employment_id, "scheme_id": scheme["_id"]}, as_of)
            if not e.get("annulled") and not e["voluntary"]]
    if not enrs:
        return None
    first = min(enrs, key=lambda e: e.get("effective_from") or e["filed_on"])
    return ap.days_late(item.legal_effective_date, to_date(first.get("effective_from")))
