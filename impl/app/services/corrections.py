"""CorrectRecord（POST /v1/corrections，hire-employee 05_mapping 2.2）。

這版只實作 annual-leave-grant UC-08 需要的：`employments` 的 `start_date`。其他欄位回 501。
尚未實作：R46 重大更正的判定（significant_corrections）、其他集合與欄位、本切片集合（annual-leave-grant 05_mapping 2.2）的更正。
"""
from datetime import date

from bson import ObjectId

from app import hooks
from app.auth import Actor
from app.db import oid, run_in_transaction, to_date, to_dt
from app.errors import Blocked, NotFound
from app.rules import applicability as ap
from app.services import proposals
from app.store import get_current, new_version, record_event

IMPLEMENTED = {("employments", "start_date")}


class NotImplementedYet(Exception):
    def __init__(self, detail: str):
        self.detail = detail


def _shift_periods(emp: dict, old: date, new: date) -> dict:
    """帶期間的屬性中，從原到職日開始的那一段跟著改到新的到職日（否則到職日到第一段之間會變成未知）。"""
    out = {}
    for f in ("employee_category", "public_or_military_insurance_covered", "org_unit_assignments", "work_locations"):
        periods = emp.get(f)
        if periods and any(to_date(p["from"]) == old for p in periods):
            out[f] = [{**p, "from": to_dt(new)} if to_date(p["from"]) == old else p for p in periods]
    return out


def correct_record(db, actor: Actor, body: dict) -> dict:
    subj, field = body["subject"], body["field"]
    if (subj["collection"], field) not in IMPLEMENTED:
        raise NotImplementedYet(f"{subj['collection']}.{field} 的更正尚未實作")
    try:
        new = date.fromisoformat(body["new_value"])
    except (TypeError, ValueError):
        from app.spec import RequestInvalid
        raise RequestInvalid(["new_value：start_date 要是日期（YYYY-MM-DD）"])

    def tx(s):
        emp = get_current(db, "employments", oid(subj["id"]), actor.tenant_id, s)
        if emp.get("annulled"):
            raise NotFound(f"employments {subj['id']} 已註銷")
        old = to_date(emp["start_date"])
        if emp.get("ended_on") and to_date(emp["ended_on"]) < new:
            raise Blocked("R02", "END_BEFORE_START", "結束日早於更正後的到職日")
        event_id = ObjectId()
        record_event(db, s, tenant_id=actor.tenant_id, type="CorrectRecord", subject=("employments", emp["entity_id"]),
                     actor=actor.event_actor, reason=body["reason"], evidence=body.get("evidence"), event_id=event_id,
                     payload={"field": field, "before": str(old), "after": str(new)})
        nxt = new_version(db, s, "employments", emp, {"start_date": to_dt(new), **_shift_periods(emp, old, new)},
                          event_id=event_id)
        proposals.propose_enrollment_filing(db, s, ap.Subject.of_employment(nxt), new, cause_event_id=event_id)
        hooks.publish(db, s, hooks.HookEvent(hooks.EMPLOYMENT_CORRECTED, tenant_id=actor.tenant_id, event_id=event_id,
                                             employment_id=emp["entity_id"], employer_id=emp["employer_id"],
                                             fields=(field,),
                                             extra={"before": {"start_date": str(old)}, "after": {"start_date": str(new)}}))
        return {"event_id": str(event_id), "subject_id": str(emp["entity_id"]), "warnings": []}
    return run_in_transaction(db, tx)
