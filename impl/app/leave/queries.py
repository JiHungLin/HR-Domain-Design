"""annual-leave-grant 的查詢（05_mapping 第二節「查詢」）：推導值現算，不存（D-06）。"""
from datetime import date, datetime

from app.auth import Actor
from app.db import database, now, oid, to_date, to_dt
from app.errors import NotFound
from app.leave import basis as B
from app.leave import clock, locks
from app.leave import ledger as L
from app.leave import views as V
from app.leave import warnings as LW
from app.leave.ledger import Ctx
from app.store import get_current


def _ctx(db, actor: Actor, employer: dict | None, as_of: datetime | None = None) -> Ctx:
    return Ctx(db, None, actor.tenant_id, clock.today(db, employer), as_of=as_of)


def _employment(db, actor: Actor, employment_id: str):
    actor.require("HR", "EMPLOYER")
    emp = get_current(db, "employments", oid(employment_id), actor.tenant_id)
    return emp, locks.employer_of(db, None, emp)


def _pending(db, employment_id) -> bool:
    """X-13：雇主層級的重新判定還沒處理完。"""
    return db.leave_reassessment_queue.find_one({"employment_id": employment_id, "processed_at": {"$exists": False}}) is not None


def list_entitlements(db, actor: Actor, employment_id: str, on: date | None, leave_type_code: str | None,
                      as_of: datetime | None) -> dict:
    """Q01：這位員工在某一天有哪幾筆特休。

    暫時：「某一天有哪幾筆」取取得日不晚於那一天、沒有作廢的（05_mapping、api.yaml 都沒寫篩選條件，signoff.md #14）。
    """
    emp, employer = _employment(db, actor, employment_id)
    ctx = _ctx(db, actor, employer, as_of)
    on = on or ctx.today
    items = [V.entitlement_view(ctx, e, ctx.today) for e in L.entitlements(ctx, emp["entity_id"])
             if not e["voided"] and to_date(e["acquired_on"]) <= on
             and (leave_type_code is None or e["leave_type_code"] == leave_type_code)]
    return {"items": items, "reassessment_pending": _pending(db, emp["entity_id"])}


def get_entitlement(db, actor: Actor, entitlement_id: str, as_of: datetime | None) -> dict:
    actor.require("HR", "EMPLOYER")
    cur = get_current(db, L.ENT, oid(entitlement_id), actor.tenant_id)
    emp = db.employments.find_one({"entity_id": cur["employment_id"], "is_current": True})
    ctx = _ctx(db, actor, locks.employer_of(db, None, emp), as_of)
    ent = L.entitlement(ctx, cur["entity_id"])
    if ent is None:
        raise NotFound(f"{as_of} 時還沒有這一筆")
    vq = {"entity_id": ent["entity_id"]} | ({"recorded_at": {"$lte": as_of}} if as_of else {})
    versions = []
    for v in db[L.ENT].find(vq).sort("revision", 1):
        e = db.events.find_one({"_id": v["event_id"]}) or {}
        versions.append(V.compact({"revision": v["revision"], "recorded_at": v["recorded_at"].isoformat(),
                                   "event_id": str(v["event_id"]), "event_type": e.get("type", ""),
                                   "actor": (e.get("actor") or {}).get("role"),
                                   "snapshot": V.entitlement_view(ctx, v, ctx.today)}))
    eq = {"type": {"$in": ["CloseLeaveYear", "RejudgeLeaveYearEnd"]}, "subject.id": ent["entity_id"]}
    if as_of:
        eq["recorded_at"] = {"$lte": as_of}
    return {
        "entitlement": V.entitlement_view(ctx, ent, ctx.today), "versions": versions,
        "year_end_judgments": [V.year_end_view(e) for e in db.events.find(eq).sort("recorded_at", 1)],
        "conversions": [V.conversion_view(c) for c in L.conversions(ctx, ent["entity_id"], include_discarded=True)],
        "deferral_agreements": [V.deferral_view(a) for a in L.deferrals(ctx, ent["entity_id"])],
        "warnings": LW.for_entitlement(ctx, ent),
    }


def forecast(db, actor: Actor, employment_id: str, until: date) -> dict:
    """US-D01、Q02：之後各期的預估（現算，不建立請假權利）。"""
    emp, employer = _employment(db, actor, employment_id)
    ctx = _ctx(db, actor, employer)
    exp = B.expected(db, None, emp, employer, until)
    items = [V.compact({
        "source": i["source"], "policy_id": V.s(i["policy_id"]), "period_sequence": i["period_sequence"],
        "expected_acquired_on": str(i["acquired_on"]), "seniority_tier": i["seniority_tier"], "quantity": str(i["quantity"]),
        "valid_from": str(i["valid_from"]), "valid_to": str(i["valid_to"]), "leave_year_basis": i["leave_year_basis"],
        "rule_versions": [V.rule_ref_view(r) for r in i["basis_rule_versions"]]})
        for i in exp.items if i["acquired_on"] > ctx.today]
    return {"employment_id": str(emp["entity_id"]), "computed_at": now().isoformat(), "items": items,
            "insufficient_data": [m for x in exp.insufficient for m in x["missing"]]}


def year_basis(db, actor: Actor, employment_id: str, on: date | None) -> dict:
    """Q03：某一天適用哪一種特休年度（R68）。"""
    emp, employer = _employment(db, actor, employment_id)
    on = on or clock.today(db, employer)
    yb = B.year_basis(db, None, emp, on)
    return V.compact({"employment_id": str(emp["entity_id"]), "on": str(on), "leave_year_basis": yb.leave_year_basis,
                      "year_start": yb.year_start, "applied_by": yb.applied_by,
                      "leave_year_agreement_id": V.s(yb.agreement_id), "policy_id": V.s(yb.policy_id)})


def leave_warnings(db, actor: Actor, employment_id: str) -> dict:
    emp, employer = _employment(db, actor, employment_id)
    ctx = _ctx(db, actor, employer)
    warns, insufficient = LW.for_employment(ctx, emp, employer)
    return {"employment_id": str(emp["entity_id"]),
            "items": [V.compact({"warning": w, "warning_override_id": LW.override_id(ctx, w, emp["entity_id"])}) for w in warns],
            "insufficient_data": insufficient, "reassessment_pending": _pending(db, emp["entity_id"])}


def work_items(db, actor: Actor, employer_id: str) -> dict:
    """跨員工的待處理清單（X-07、X-20）：還沒忽略的警告、資料不足、待確認的轉換、佇列失敗的。"""
    actor.require("HR", "EMPLOYER")
    employer = get_current(db, "employers", oid(employer_id), actor.tenant_id)
    ctx = _ctx(db, actor, employer)
    items = []
    for emp in db.employments.find({"tenant_id": actor.tenant_id, "employer_id": employer["_id"], "is_current": True,
                                    "annulled": {"$ne": True}}):
        eid = str(emp["entity_id"])
        warns, insufficient = LW.for_employment(ctx, emp, employer)
        items += [{"kind": "WARNING", "employment_id": eid, "warning": w} for w in warns
                  if LW.override_id(ctx, w, emp["entity_id"]) is None]
        items += [{"kind": "INSUFFICIENT_DATA", "employment_id": eid, "missing": x["missing"]} for x in insufficient]
        items += [{"kind": "PROVISIONAL_CONVERSION", "employment_id": eid, "conversion_id": str(c["entity_id"])}
                  for c in db[L.CONV].find({"employment_id": emp["entity_id"], "is_current": True, "status": "Provisional"})]
        items += [V.compact({"kind": "QUEUE_FAILED", "employment_id": eid, "last_error": q.get("last_error")})
                  for q in db.leave_reassessment_queue.find({"employment_id": emp["entity_id"], "processed_at": {"$exists": False},
                                                             "attempts": {"$gt": 0}})]
    return {"employer_id": str(employer["_id"]), "computed_at": now().isoformat(), "items": items}


def list_conversions(db, actor: Actor, employment_id, employer_id, status, payment_due_before: date | None) -> dict:
    actor.require("HR", "EMPLOYER")
    q = {"tenant_id": actor.tenant_id, "is_current": True}
    if employment_id:
        q["employment_id"] = get_current(db, "employments", oid(employment_id), actor.tenant_id)["entity_id"]
    if employer_id:
        employer = get_current(db, "employers", oid(employer_id), actor.tenant_id)
        q["employment_id"] = {"$in": db.employments.distinct("entity_id", {"employer_id": employer["_id"]})}
    if status:
        q["status"] = status
    if payment_due_before:
        q["payment_due_on"] = {"$lt": to_dt(payment_due_before)}
    return {"items": [V.conversion_view(c) for c in db[L.CONV].find(q).sort("created_at", 1)]}


def list_notices(db, actor: Actor, employer_id, employment_id, root_event_id, since: datetime | None) -> dict:
    actor.require("HR", "EMPLOYER")
    q = {"tenant_id": actor.tenant_id}
    emps = None
    if employment_id:
        q["employment_id"] = oid(employment_id)
        emps = [oid(employment_id)]
    if employer_id:
        employer = get_current(db, "employers", oid(employer_id), actor.tenant_id)
        emps = db.employments.distinct("entity_id", {"employer_id": employer["_id"]})
        q.setdefault("employment_id", {"$in": emps})
    if root_event_id:
        q["root_event_id"] = oid(root_event_id)
    if since:
        q["notified_at"] = {"$gte": since}
    pq = {"tenant_id": actor.tenant_id, "processed_at": {"$exists": False}}
    if emps is not None:
        pq["employment_id"] = {"$in": emps}
    return {"items": [V.notice_view(n) for n in db.leave_reassessment_notices.find(q).sort("notified_at", 1)],
            "pending_count": db.leave_reassessment_queue.count_documents(pq)}


def get_notice(db, actor: Actor, notice_id: str) -> dict:
    actor.require("HR", "EMPLOYER")
    n = get_current(db, "leave_reassessment_notices", oid(notice_id), actor.tenant_id)
    return V.notice_view(n)


def list_year_agreements(db, actor: Actor, employment_id: str) -> dict:
    emp, _ = _employment(db, actor, employment_id)
    return {"items": [V.compact({
        "leave_year_agreement_id": str(a["_id"]), "employment_id": str(a["employment_id"]),
        "leave_type_code": a["leave_type_code"], "leave_year_basis": a["leave_year_basis"], "year_start": a.get("year_start"),
        "effective_from": V.ds(a["effective_from"]), "ended_from": V.ds(a.get("ended_from")), "agreed_on": V.ds(a["agreed_on"]),
        "agreement_note": a.get("agreement_note"), "status": a["status"]})
        for a in db.leave_year_agreements.find({"tenant_id": actor.tenant_id, "employment_id": emp["entity_id"]})
        .sort("effective_from", 1)]}


def _policy_view(p: dict) -> dict:
    return V.compact({"policy_id": str(p["entity_id"]), "employer_id": V.s(p.get("employer_id")),
                      "leave_type_code": p.get("leave_type_code"), "name": p["name"], "subject": p["subject"],
                      "source_note": p.get("source_note"), "effective_from": V.ds(p["effective_from"]),
                      "effective_to": V.ds(p.get("effective_to")), "status": p["status"]})


def _params_view(p: dict) -> dict:
    out = dict(p)
    if "company_extra_days" in p:
        out["company_extra_days"] = [V.compact({"from_months": b["from_months"], "to_months": b.get("to_months"),
                                                "days": V.qs(b["days"])}) for b in p["company_extra_days"]]
    return out


def list_policies(db, actor: Actor, employer_id: str | None, subject: str | None) -> dict:
    actor.require("HR", "EMPLOYER")
    q = {"tenant_id": actor.tenant_id, "is_current": True}
    if employer_id:
        q["employer_id"] = get_current(db, "employers", oid(employer_id), actor.tenant_id)["_id"]
    if subject:
        q["subject"] = subject
    return {"items": [_policy_view(p) for p in db.company_policies.find(q).sort("effective_from", 1)]}


def get_policy(db, actor: Actor, policy_id: str) -> dict:
    from app.leave.actions import policy_warnings
    actor.require("HR", "EMPLOYER")
    p = get_current(db, "company_policies", oid(policy_id), actor.tenant_id)
    vs = list(db.company_policy_versions.find({"policy_id": p["entity_id"]}).sort([("effective_from", 1), ("revision", 1)]))
    employer = db.employers.find_one({"_id": p["employer_id"]}) if p.get("employer_id") else None
    return {"policy": _policy_view(p),
            "versions": [V.compact({"version": v["version"], "revision": v["revision"],
                                    "effective_from": V.ds(v["effective_from"]), "params": _params_view(v["params"]),
                                    "recorded_at": v["recorded_at"].isoformat()}) for v in vs],
            "warnings": policy_warnings(db, None, p, vs, clock.today(db, employer))}


def list_leave_types(db) -> dict:
    return {"items": [V.compact({"code": t["code"], "jurisdiction_id": V.s(t.get("jurisdiction_id")), "status": t["status"]})
                      for t in db.leave_types.find().sort("code", 1)]}
