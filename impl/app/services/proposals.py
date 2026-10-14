"""ProposeEnrollmentFiling（加保待辦，建議層事件）與 UC-02 判定查詢。

加保待辦是事實（PLAN.md D-35 P3）：判定內容產生後不改；被取代、各保險結案、雇主不加自願保險是之後的記錄（P2 B）。
"""
from datetime import date, datetime

from bson import ObjectId

from app.db import now, to_date
from app.rules import applicability as ap
from app.rules import versions
from app.rules.warnings import warning
from app.errors import NotFound
from app.store import clean, get_current, record_event, update_with_changelog

SYSTEM = {"role": "system"}


def propose_enrollment_filing(db, s, employment: dict, on: date, *, cause_event_id: ObjectId) -> ObjectId:
    facts = ap.load_facts(db, employment, on, session=s)
    items = ap.determine(db, facts, on, session=s)
    rule_refs = _unique(r for i in items for r in i.rules)
    pid, event_id = ObjectId(), ObjectId()
    record_event(db, s, tenant_id=employment["tenant_id"], type="ProposeEnrollmentFiling",
                 subject=("enrollment_proposals", pid), actor=SYSTEM, rule_versions=rule_refs, derived=True,
                 event_id=event_id)
    db.enrollment_proposals.insert_one(clean({
        "_id": pid, "tenant_id": employment["tenant_id"], "employment_id": employment["entity_id"],
        "hire_id": employment.get("hire_id"), "determined_on": ap.to_dt(on),
        "basis": {"data": facts.data_refs, "headcount": facts.headcount, "rule_versions": rule_refs,
                  "cause_event_id": cause_event_id, "notes": {i.scheme_code: i.notes for i in items if i.notes},
                  "pending": {i.scheme_code: i.pending for i in items if i.pending}},
        "items": [i.to_doc() for i in items], "created_at": now(),
    }), session=s)
    for old in db.enrollment_proposals.find({"tenant_id": employment["tenant_id"], "employment_id": employment["entity_id"],
                                             "_id": {"$ne": pid}, "superseded_by": {"$exists": False}}, session=s):
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


def list_proposals(db, tenant_id, status: str | None, today: date) -> list[dict]:
    """GET /v1/enrollment-proposals：status＝open 只列未被取代、還有未結案的強制或自願項目。R36 逾期未辦 → 警告。"""
    q = {"tenant_id": tenant_id}
    if status == "open":
        q["superseded_by"] = {"$exists": False}
    out = []
    for p in db.enrollment_proposals.find(q).sort("determined_on", 1):
        warns, open_items = [], 0
        for it in p["items"]:
            actionable = it["applicability"] in (ap.MANDATORY, ap.VOLUNTARY) and not it.get("closed_by_enrollment_id") \
                and not it.get("voluntary_declined")
            open_items += actionable
            if actionable and it["applicability"] == ap.MANDATORY and it.get("filing_deadline") \
                    and to_date(it["filing_deadline"]) < today:
                warns.append(warning(None, "R36", "FILING_OVERDUE", {"scheme_code": it["scheme_code"],
                                                                      "filing_deadline": str(to_date(it["filing_deadline"]))}))
        if status == "open" and not open_items:
            continue
        out.append(serialize(p) | {"warnings": warns})
    return out


def applicability_on(db, tenant_id, employment_id: ObjectId, on: date, as_of: datetime | None) -> dict:
    """GET /v1/employments/{id}/applicability：現算，不落地；as_of 只看當時已登錄的版本（03_flows D-10）。"""
    get_current(db, "employments", employment_id, tenant_id)       # 找不到或不屬於呼叫者 → 404／403
    emps = versions.snapshot(db, "employments", {"entity_id": employment_id}, as_of)
    if not emps:
        raise NotFound(f"{as_of} 時系統還沒有這段僱傭關係")
    emp = emps[0]
    facts = ap.load_facts(db, emp, on, as_of)
    items = ap.determine(db, facts, on, as_of)
    return {"employment_id": str(employment_id), "on": on, "as_of": as_of, "headcount": facts.headcount,
            "items": [i.to_api() for i in items]}


def serialize(doc):
    """ObjectId、Decimal128、日期轉成 JSON 可用的值。"""
    from bson import Decimal128
    if isinstance(doc, dict):
        return {("id" if k == "_id" else k): serialize(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [serialize(v) for v in doc]
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, Decimal128):
        return str(doc.to_decimal())
    if isinstance(doc, datetime):
        return doc.date().isoformat() if (doc.hour, doc.minute, doc.second, doc.microsecond) == (0, 0, 0, 0) else doc.isoformat()
    return doc
