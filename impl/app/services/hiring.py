"""UC-01 錄用本國籍員工並到職：DecideHire、RecordIdentityDocument、AgreeCompensation、SignContract、StartEmployment。

每個動作在一個多文件交易中寫入 events 與受影響的集合（PLAN.md D-35）。
"""
from datetime import date, datetime

from bson import Int64, ObjectId

from app.auth import Actor
from app.db import oid, run_in_transaction, to_date, to_dec128, to_dt
from app.errors import Blocked
from app.rules import warnings
from app.services import proposals
from app.store import clean, get_current, get_shared, insert_versioned, record_event, update_with_changelog


def _person_fields(p: dict, tenant_id) -> dict:
    return clean({
        "tenant_id": tenant_id, "legal_name": p.get("legal_name"), "gender": p.get("gender"),
        "birth_date": to_dt(p.get("birth_date")), "education": p.get("education"), "address": p.get("address"),
        "nationalities": [clean({"country_code": n["country_code"], "acquired_on": to_dt(n["acquired_on"]),
                                 "lost_on": to_dt(n.get("lost_on"))}) for n in p.get("nationalities") or []] or None,
        "civil_registrations": [clean({"jurisdiction_id": oid(r["jurisdiction_id"]), "registered_on": to_dt(r["registered_on"]),
                                       "deregistered_on": to_dt(r.get("deregistered_on"))})
                                for r in p.get("civil_registrations") or []] or None,
        "old_age_benefits_received": [{"scheme_code": o["scheme_code"], "received_on": to_dt(o["received_on"])}
                                      for o in p.get("old_age_benefits_received") or []] or None,
    })


def decide_hire(db, actor: Actor, body) -> dict:
    """DecideHire：同一交易建立 Person（05_mapping D-05）與 Hire（Hired）。"""
    def tx(s):
        employer = get_current(db, "employers", oid(body.employer_id), actor.tenant_id, s)
        for ref, coll in ((body.planned_work_location_id, "work_locations"), (body.planned_org_unit_id, "org_units")):
            if ref:
                get_current(db, coll, oid(ref), actor.tenant_id, s)
        hire_id, event_id = ObjectId(), ObjectId()
        person_id = insert_versioned(db, s, "persons", _person_fields(body.person.model_dump(), actor.tenant_id), event_id=event_id)
        contact = body.person.model_dump().get("contact")
        if contact:
            db.person_contacts.insert_one(clean({"tenant_id": actor.tenant_id, "person_id": person_id,
                                                 "phone": contact.get("phone"), "email": contact.get("email")}), session=s)
        warn = warnings.minimum_wage(db, employer, None, body.planned_start_date, s)
        person = db.persons.find_one({"entity_id": person_id, "is_current": True}, session=s)
        warn += warnings.work_authorization(db, person, employer["_id"], body.planned_start_date, s)
        record_event(db, s, tenant_id=actor.tenant_id, type="DecideHire", subject=("hires", hire_id),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(body.decided_on),
                     event_id=event_id)
        db.hires.insert_one(clean({
            "_id": hire_id, "tenant_id": actor.tenant_id, "person_id": person_id, "employer_id": employer["_id"],
            "planned_work_location_id": oid(body.planned_work_location_id) if body.planned_work_location_id else None,
            "planned_org_unit_id": oid(body.planned_org_unit_id) if body.planned_org_unit_id else None,
            "decided_on": to_dt(body.decided_on), "planned_start_date": to_dt(body.planned_start_date),
            "prior_insurance_elsewhere": body.prior_insurance_elsewhere, "status": "Hired", "annulled": False,
        }), session=s)
        return {"entity_id": str(hire_id), "event_id": str(event_id), "person_id": str(person_id), "warnings": warn}
    return run_in_transaction(db, tx)


def record_identity_document(db, actor: Actor, person_id: str, body) -> dict:
    """RecordIdentityDocument（R03 擋下：迄日不早於起日）。"""
    if body.valid_until and body.valid_until < body.valid_from:
        raise Blocked("R03", "DATE_ORDER", "證件迄日早於起日")

    def tx(s):
        person = get_current(db, "persons", oid(person_id), actor.tenant_id, s)
        get_shared(db, "jurisdictions", oid(body.issuing_jurisdiction_id), s)
        event_id = ObjectId()
        ent = insert_versioned(db, s, "identity_documents", {
            "tenant_id": actor.tenant_id, "person_id": person["entity_id"],
            "issuing_jurisdiction_id": oid(body.issuing_jurisdiction_id), "document_kind": body.document_kind,
            "document_number": body.document_number, "valid_from": to_dt(body.valid_from),
            "valid_until": to_dt(body.valid_until), "residence_basis": body.residence_basis,
        }, event_id=event_id)
        record_event(db, s, tenant_id=actor.tenant_id, type="RecordIdentityDocument", subject=("identity_documents", ent),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(body.valid_from),
                     event_id=event_id)
        return {"entity_id": str(ent), "event_id": str(event_id), "warnings": []}
    return run_in_transaction(db, tx)


def _hire_or_employment(db, actor, s, hire_id, employment_id):
    if not (hire_id or employment_id):
        raise Blocked(None, "MISSING_LINK", "要指定 hire_id 或 employment_id")
    hire = get_current(db, "hires", oid(hire_id), actor.tenant_id, s) if hire_id else None
    emp = get_current(db, "employments", oid(employment_id), actor.tenant_id, s) if employment_id else None
    return hire, emp


def agree_compensation(db, actor: Actor, body) -> dict:
    """AgreeCompensation（R11 提醒）。"""
    def tx(s):
        hire, emp = _hire_or_employment(db, actor, s, body.hire_id, body.employment_id)
        event_id = ObjectId()
        fields = {
            "tenant_id": actor.tenant_id, "employment_id": emp["entity_id"] if emp else None,
            "hire_id": hire["_id"] if hire else None, "effective_from": to_dt(body.effective_from),
            "currency": body.currency, "pay_basis": body.pay_basis,
            "monthly_base_salary": to_dec128(body.monthly_base_salary),
            "fixed_monthly_allowances": [{"name": a.name, "category": a.category, "amount": to_dec128(a.amount)}
                                         for a in body.fixed_monthly_allowances] or None,
        }
        ent = insert_versioned(db, s, "compensations", fields, event_id=event_id)
        employer = db.employers.find_one({"_id": (hire or emp)["employer_id"]}, session=s)
        start = to_date((emp or {}).get("start_date") or hire["planned_start_date"])
        comp = db.compensations.find_one({"entity_id": ent, "is_current": True}, session=s)
        warn = warnings.minimum_wage(db, employer, comp, start, s)
        record_event(db, s, tenant_id=actor.tenant_id, type="AgreeCompensation", subject=("compensations", ent),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(body.effective_from),
                     rule_versions=_rule_refs(warn), event_id=event_id)
        return {"entity_id": str(ent), "event_id": str(event_id), "warnings": warn}
    return run_in_transaction(db, tx)


def sign_contract(db, actor: Actor, body) -> dict:
    """SignContract（R03 擋下）。R18～R20、R59 是外籍與定期契約的規則，UC-01 尚未實作。"""
    if body.term_start and body.term_end and body.term_end < body.term_start:
        raise Blocked("R03", "DATE_ORDER", "契約迄日早於起日")

    def tx(s):
        hire, emp = _hire_or_employment(db, actor, s, body.hire_id, body.employment_id)
        event_id, cid = ObjectId(), ObjectId()
        record_event(db, s, tenant_id=actor.tenant_id, type="SignContract", subject=("employment_contracts", cid),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(body.term_start),
                     event_id=event_id)
        db.employment_contracts.insert_one(clean({
            "_id": cid, "tenant_id": actor.tenant_id, "employment_id": emp["entity_id"] if emp else None,
            "hire_id": hire["_id"] if hire else None, "contract_type": body.contract_type,
            "fixed_term_nature": body.fixed_term_nature, "term_start": to_dt(body.term_start),
            "term_end": to_dt(body.term_end), "in_writing": body.in_writing, "status": "Signed", "annulled": False,
        }), session=s)
        return {"entity_id": str(cid), "event_id": str(event_id), "warnings": []}
    return run_in_transaction(db, tx)


def start_employment(db, actor: Actor, hire_id: str, body) -> dict:
    """StartEmployment：Hire Hired → Started，建立 Employment（Active），產生加保待辦（ProposeEnrollmentFiling）。

    擋下：R01、R04、R05、R06；提醒：R11、R14、R15、R21。
    """
    def tx(s):
        hire = get_current(db, "hires", oid(hire_id), actor.tenant_id, s)
        if hire["status"] != "Hired":
            raise Blocked(None, "INVALID_STATE", f"錄用的狀態是 {hire['status']}，不能登錄到職（P1）")
        start = body.start_date
        if start < to_date(hire["decided_on"]):
            raise Blocked("R01", "START_BEFORE_DECISION", "到職日早於決定錄用的日期")
        tenant, person_id, employer_id = actor.tenant_id, hire["person_id"], hire["employer_id"]

        # R04：同一人在同一雇主的各段僱傭關係不重疊；先更新鎖文件，讓同時的交易互相衝突（D-15）
        db.employment_locks.update_one({"tenant_id": tenant, "person_id": person_id, "employer_id": employer_id},
                                       {"$inc": {"seq": Int64(1)}}, upsert=True, session=s)
        for e in db.employments.find({"tenant_id": tenant, "person_id": person_id, "employer_id": employer_id,
                                      "is_current": True, "annulled": False}, session=s):
            if e.get("ended_on") is None or to_date(e["ended_on"]) >= start:
                raise Blocked("R04", "EMPLOYMENT_OVERLAP", f"與既有的僱傭關係 {e['entity_id']} 期間重疊")
        # R05：同一雇主在職的員工編號不重複（唯一索引也會擋，這裡先給清楚的訊息）
        if body.employee_number and db.employments.find_one(
                {"tenant_id": tenant, "employer_id": employer_id, "employee_number": body.employee_number,
                 "is_current": True, "status": "Active", "annulled": False}, session=s):
            raise Blocked("R05", "DUPLICATE_EMPLOYEE_NUMBER", f"員工編號 {body.employee_number} 已有在職者使用")
        # R06：組織單位的雇主要和僱傭關係的雇主相同
        org_unit_id = body.org_unit_id or (str(hire["planned_org_unit_id"]) if hire.get("planned_org_unit_id") else None)
        if org_unit_id:
            ou = get_current(db, "org_units", oid(org_unit_id), tenant, s)
            ou_employer = next((p.get("value") for p in ou.get("employer_id") or []
                                if to_date(p["from"]) <= start and (p.get("to") is None or start <= to_date(p["to"]))), None)
            if ou_employer is not None and ou_employer != employer_id:
                raise Blocked("R06", "ORG_UNIT_OTHER_EMPLOYER", "組織單位屬於另一個雇主")
        wl_id = body.work_location_id or (str(hire["planned_work_location_id"]) if hire.get("planned_work_location_id") else None)
        if wl_id:
            get_current(db, "work_locations", oid(wl_id), tenant, s)

        event_id = ObjectId()
        record_event(db, s, tenant_id=tenant, type="StartEmployment", subject=("hires", hire["_id"]),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(start),
                     event_id=event_id)
        emp_id = insert_versioned(db, s, "employments", {
            "tenant_id": tenant, "person_id": person_id, "employer_id": employer_id, "hire_id": hire["_id"],
            "start_date": to_dt(start), "employee_number": body.employee_number,
            "employee_category": [{"code": "EMPLOYEE_CATEGORY.FULL_TIME", "from": to_dt(start)}],
            "probation_until": to_dt(body.probation_until),
            "org_unit_assignments": [{"org_unit_id": oid(org_unit_id), "from": to_dt(start)}] if org_unit_id else None,
            "work_locations": [{"work_location_id": oid(wl_id), "from": to_dt(start)}] if wl_id else None,
            "status": "Active", "annulled": False,
        }, event_id=event_id)
        update_with_changelog(db, s, "hires", hire, {"status": "Started"}, event_id=event_id, actor=actor.event_actor)

        # 提醒
        employment = db.employments.find_one({"entity_id": emp_id, "is_current": True}, session=s)
        person = db.persons.find_one({"entity_id": person_id, "is_current": True}, session=s)
        employer = db.employers.find_one({"_id": employer_id}, session=s)
        comps = list(db.compensations.find({"tenant_id": tenant, "hire_id": hire["_id"], "is_current": True}, session=s))
        comp = max((c for c in comps if to_date(c["effective_from"]) <= start), key=lambda c: c["effective_from"], default=None)
        warn = warnings.minimum_wage(db, employer, comp, start, s)
        warn += warnings.work_authorization(db, person, employer_id, start, s)
        if not comps:
            warn.append(warnings.warning(None, "R21", "MISSING_COMPENSATION"))
        if not db.employment_contracts.find_one({"tenant_id": tenant, "hire_id": hire["_id"]}, session=s):
            warn.append(warnings.warning(None, "R21", "MISSING_CONTRACT"))

        proposal_id = proposals.propose_enrollment_filing(db, s, employment, start, cause_event_id=event_id)
        return {"entity_id": str(emp_id), "event_id": str(event_id), "enrollment_proposal_id": str(proposal_id),
                "warnings": warn}
    return run_in_transaction(db, tx)


def _rule_refs(warn: list[dict]) -> list[dict] | None:
    refs = [{"rule_id": w["rule_id"], "version": w["rule_version"], "revision": w["rule_revision"]}
            for w in warn if "rule_version" in w]
    return refs or None
