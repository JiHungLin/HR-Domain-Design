"""UC-01 錄用本國籍員工並到職：DecideHire、RecordIdentityDocument、AgreeCompensation、SignContract、StartEmployment。

請求已依 api.yaml 檢查（app/spec.py）；每個動作在一個多文件交易中寫入 events 與受影響的集合（PLAN.md D-35）。
"""
from datetime import date, datetime, timedelta

from bson import Int64, ObjectId

from app import hooks
from app.auth import Actor
from app.db import oid, run_in_transaction, to_date, to_dec128, to_dt
from app.errors import Blocked
from app.rules import applicability as ap
from app.rules import warnings
from app.services import proposals
from app.spec import RequestInvalid
from app.store import clean, get_current, get_shared, insert_versioned, new_version, record_event, update_with_changelog


def D(v: str | None) -> date | None:
    return date.fromisoformat(v) if v else None


def DT(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None


def _person_fields(p: dict, tenant_id) -> dict:
    return clean({
        "tenant_id": tenant_id, "legal_name": p["legal_name"], "gender": p.get("gender"),
        "birth_date": to_dt(D(p.get("birth_date"))), "education": p.get("education"), "address": p.get("address"),
        "nationalities": [clean({"country_code": n["country_code"], "acquired_on": to_dt(D(n["acquired_on"])),
                                 "lost_on": to_dt(D(n.get("lost_on")))}) for n in p.get("nationalities") or []] or None,
        "civil_registrations": [clean({"jurisdiction_id": oid(r["jurisdiction_id"]), "registered_on": to_dt(D(r["registered_on"])),
                                       "deregistered_on": to_dt(D(r.get("deregistered_on")))})
                                for r in p.get("civil_registrations") or []] or None,
        "old_age_benefits_received": [{"scheme_code": o["scheme_code"], "received_on": to_dt(D(o["received_on"]))}
                                      for o in p.get("old_age_benefits_received") or []] or None,
    })


def _compensation_fields(c: dict, tenant_id, *, hire_id=None, employment_id=None) -> dict:
    return {
        "tenant_id": tenant_id, "hire_id": hire_id, "employment_id": employment_id,
        "effective_from": to_dt(D(c["effective_from"])), "currency": c["currency"], "pay_basis": c["pay_basis"],
        "monthly_base_salary": to_dec128(c["monthly_base_salary"]),
        "fixed_monthly_allowances": [{"name": a["name"], "category": a["category"], "amount": to_dec128(a["amount"])}
                                     for a in c.get("fixed_monthly_allowances") or []] or None,
    }


def _contract_doc(c: dict, tenant_id, cid, *, hire_id=None, employment_id=None) -> dict:
    if c.get("term_start") and c.get("term_end") and D(c["term_end"]) < D(c["term_start"]):
        raise Blocked("R03", "DATE_ORDER", "契約迄日早於起日")
    return clean({
        "_id": cid, "tenant_id": tenant_id, "hire_id": hire_id, "employment_id": employment_id,
        "contract_type": c["contract_type"], "fixed_term_nature": c.get("fixed_term_nature"),
        "term_start": to_dt(D(c.get("term_start"))), "term_end": to_dt(D(c.get("term_end"))),
        "in_writing": c["in_writing"], "status": "Signed", "annulled": False,
    })


def decide_hire(db, actor: Actor, body: dict) -> dict:
    """DecideHire：建立或沿用 Person（D-05、UC-12），建立 Hire（Hired）；一併帶的約定薪資、契約同一交易建立（D-17）。

    提醒：R11（有帶約定薪資時在這裡判斷）、R14。產生加保待辦（ProposeEnrollmentFiling，觸發來源：決定錄用）。
    """
    ref = body["person"]
    if ("person_id" in ref) == ("person" in ref):
        raise RequestInvalid(["person：person_id 與 person 擇一（PersonRef）"])
    planned = D(body["planned_start_date"])

    def tx(s):
        t = actor.tenant_id
        employer = get_current(db, "employers", oid(body["employer_id"]), t, s)
        for key, coll in (("planned_work_location_id", "work_locations"), ("planned_org_unit_id", "org_units")):
            if body.get(key):
                get_current(db, coll, oid(body[key]), t, s)
        hire_id, event_id = ObjectId(), ObjectId()
        if "person_id" in ref:
            person_id = get_current(db, "persons", oid(ref["person_id"]), t, s)["entity_id"]
        else:
            p = ref["person"]
            person_id = insert_versioned(db, s, "persons", _person_fields(p, t), event_id=event_id)
            if p.get("contact"):
                db.person_contacts.insert_one(clean({"tenant_id": t, "person_id": person_id, **p["contact"]}), session=s)
        record_event(db, s, tenant_id=t, type="DecideHire", subject=("hires", hire_id), actor=actor.event_actor,
                     occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(D(body["decided_on"])), event_id=event_id)
        hire = clean({
            "_id": hire_id, "tenant_id": t, "person_id": person_id, "employer_id": employer["_id"],
            "planned_work_location_id": oid(body["planned_work_location_id"]) if body.get("planned_work_location_id") else None,
            "planned_org_unit_id": oid(body["planned_org_unit_id"]) if body.get("planned_org_unit_id") else None,
            "decided_on": to_dt(D(body["decided_on"])), "planned_start_date": to_dt(planned),
            "prior_insurance_elsewhere": body.get("prior_insurance_elsewhere"), "status": "Hired", "annulled": False,
        })
        db.hires.insert_one(hire, session=s)
        out = {"event_id": str(event_id), "hire_id": str(hire_id), "person_id": str(person_id)}
        comp = None
        if body.get("compensation"):
            cid = insert_versioned(db, s, "compensations", _compensation_fields(body["compensation"], t, hire_id=hire_id),
                                   event_id=event_id)
            comp = db.compensations.find_one({"entity_id": cid, "is_current": True}, session=s)
            out["compensation_id"] = str(cid)
        if body.get("contract"):
            cid = ObjectId()
            db.employment_contracts.insert_one(_contract_doc(body["contract"], t, cid, hire_id=hire_id), session=s)
            out["contract_id"] = str(cid)
        person = db.persons.find_one({"entity_id": person_id, "is_current": True}, session=s)
        warn = warnings.minimum_wage(db, employer, comp, planned, s)
        warn += warnings.work_authorization(db, person, employer["_id"], planned, s)
        proposals.propose_enrollment_filing(db, s, ap.Subject.of_hire(hire), planned, cause_event_id=event_id)
        return out | {"warnings": warn}
    return run_in_transaction(db, tx)


def record_identity_document(db, actor: Actor, person_id: str, body: dict) -> dict:
    """RecordIdentityDocument（R03 擋下：迄日不早於起日）。"""
    vf, vu = D(body["valid_from"]), D(body.get("valid_until"))
    if vu and vu < vf:
        raise Blocked("R03", "DATE_ORDER", "證件迄日早於起日")

    def tx(s):
        person = get_current(db, "persons", oid(person_id), actor.tenant_id, s)
        get_shared(db, "jurisdictions", oid(body["issuing_jurisdiction_id"]), s)
        event_id = ObjectId()
        ent = insert_versioned(db, s, "identity_documents", {
            "tenant_id": actor.tenant_id, "person_id": person["entity_id"],
            "issuing_jurisdiction_id": oid(body["issuing_jurisdiction_id"]), "document_kind": body["document_kind"],
            "document_number": body["document_number"], "valid_from": to_dt(vf), "valid_until": to_dt(vu),
            "residence_basis": body.get("residence_basis"), "annulled": False,
        }, event_id=event_id)
        record_event(db, s, tenant_id=actor.tenant_id, type="RecordIdentityDocument", subject=("identity_documents", ent),
                     actor=actor.event_actor, occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(vf),
                     event_id=event_id)
        return {"event_id": str(event_id), "identity_document_id": str(ent), "person_id": str(person["entity_id"]),
                "warnings": []}
    return run_in_transaction(db, tx)


def _hire_or_employment(db, actor, s, body):
    if ("hire_id" in body) == ("employment_id" in body):
        raise RequestInvalid(["employment_id 與 hire_id 擇一"])
    if "hire_id" in body:
        return get_current(db, "hires", oid(body["hire_id"]), actor.tenant_id, s), None
    return None, get_current(db, "employments", oid(body["employment_id"]), actor.tenant_id, s)


def agree_compensation(db, actor: Actor, body: dict) -> dict:
    """AgreeCompensation：錄用後才另外約定時使用（R11 提醒）。"""
    def tx(s):
        hire, emp = _hire_or_employment(db, actor, s, body)
        event_id = ObjectId()
        ent = insert_versioned(db, s, "compensations", _compensation_fields(
            body, actor.tenant_id, hire_id=hire["_id"] if hire else None, employment_id=emp["entity_id"] if emp else None),
            event_id=event_id)
        employer = db.employers.find_one({"_id": (hire or emp)["employer_id"]}, session=s)
        start = to_date(emp["start_date"] if emp else hire["planned_start_date"])
        comp = db.compensations.find_one({"entity_id": ent, "is_current": True}, session=s)
        warn = warnings.minimum_wage(db, employer, comp, start, s)
        record_event(db, s, tenant_id=actor.tenant_id, type="AgreeCompensation", subject=("compensations", ent),
                     actor=actor.event_actor, occurred_at=DT(body.get("occurred_at")),
                     effective_from=to_dt(D(body["effective_from"])), rule_versions=_rule_refs(warn), event_id=event_id)
        return {"event_id": str(event_id), "compensation_id": str(ent), "warnings": warn}
    return run_in_transaction(db, tx)


def sign_contract(db, actor: Actor, body: dict) -> dict:
    """SignContract（R03 擋下）。R18～R20、R59 屬外籍與定期契約（UC-04、UC-07），尚未實作。"""
    def tx(s):
        hire, emp = _hire_or_employment(db, actor, s, body)
        event_id, cid = ObjectId(), ObjectId()
        doc = _contract_doc(body, actor.tenant_id, cid, hire_id=hire["_id"] if hire else None,
                            employment_id=emp["entity_id"] if emp else None)
        record_event(db, s, tenant_id=actor.tenant_id, type="SignContract", subject=("employment_contracts", cid),
                     actor=actor.event_actor, occurred_at=DT(body.get("occurred_at")),
                     effective_from=to_dt(D(body.get("term_start"))), event_id=event_id)
        db.employment_contracts.insert_one(doc, session=s)
        return {"event_id": str(event_id), "contract_id": str(cid), "warnings": []}
    return run_in_transaction(db, tx)


def start_employment(db, actor: Actor, hire_id: str, body: dict) -> dict:
    """StartEmployment：Hire Hired → Started，建立 Employment（Active）；錄用時掛的約定薪資、契約接續到僱傭關係；
    重新產生加保待辦並取代錄用時的那一筆。

    擋下：R01、R04、R05、R06；提醒：R11、R14、R15、R21。
    """
    start = D(body["start_date"])
    number = body.get("employee_number")

    def tx(s):
        t = actor.tenant_id
        hire = get_current(db, "hires", oid(hire_id), t, s)
        if hire["status"] != "Hired":
            raise Blocked(None, "INVALID_STATE", f"錄用的狀態是 {hire['status']}，不能登錄到職（P1）")
        if start < to_date(hire["decided_on"]):
            raise Blocked("R01", "START_BEFORE_DECISION", "到職日早於決定錄用的日期")
        person_id, employer_id = hire["person_id"], hire["employer_id"]

        # R04：同一人在同一雇主的各段僱傭關係不重疊；先更新鎖文件，讓同時的交易互相衝突（D-15）
        db.employment_locks.update_one({"tenant_id": t, "person_id": person_id, "employer_id": employer_id},
                                       {"$inc": {"seq": Int64(1)}}, upsert=True, session=s)
        for e in db.employments.find({"tenant_id": t, "person_id": person_id, "employer_id": employer_id,
                                      "is_current": True, "annulled": False}, session=s):
            if e.get("ended_on") is None or to_date(e["ended_on"]) >= start:
                raise Blocked("R04", "EMPLOYMENT_OVERLAP", f"與既有的僱傭關係 {e['entity_id']} 期間重疊")
        # R05：同一雇主在職的員工編號不重複（唯一索引也會擋，這裡先給清楚的訊息）
        if number and db.employments.find_one({"tenant_id": t, "employer_id": employer_id, "employee_number": number,
                                               "is_current": True, "status": "Active", "annulled": False}, session=s):
            raise Blocked("R05", "DUPLICATE_EMPLOYEE_NUMBER", f"員工編號 {number} 已有在職者使用")
        # R06：組織單位的雇主要和僱傭關係的雇主相同
        org_unit_id = body.get("org_unit_id") or (str(hire["planned_org_unit_id"]) if hire.get("planned_org_unit_id") else None)
        if org_unit_id:
            ou = get_current(db, "org_units", oid(org_unit_id), t, s)
            ou_employer = ap.value_on(ou.get("employer_id"), start)
            if ou_employer is not None and ou_employer != employer_id:
                raise Blocked("R06", "ORG_UNIT_OTHER_EMPLOYER", "組織單位屬於另一個雇主")
        wl = get_current(db, "work_locations", oid(body["work_location_id"]), t, s)

        event_id = ObjectId()
        record_event(db, s, tenant_id=t, type="StartEmployment", subject=("hires", hire["_id"]), actor=actor.event_actor,
                     occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(start), event_id=event_id)
        emp_id = insert_versioned(db, s, "employments", {
            "tenant_id": t, "person_id": person_id, "employer_id": employer_id, "hire_id": hire["_id"],
            "start_date": to_dt(start), "employee_number": number,
            "employee_category": [{"code": "EMPLOYEE_CATEGORY.FULL_TIME", "from": to_dt(start)}],
            "probation_until": to_dt(D(body.get("probation_until"))),
            # 02 D-37：這個職務是否依法應參加公教或軍保（帶期間，到職時必填，03_flows D-21）；就保 R24
            "public_or_military_insurance_covered": [{"value": body["public_or_military_insurance_covered"], "from": to_dt(start)}],
            "org_unit_assignments": [{"org_unit_id": oid(org_unit_id), "from": to_dt(start)}] if org_unit_id else None,
            "work_locations": [{"work_location_id": wl["_id"], "from": to_dt(start)}],
            "status": "Active", "annulled": False,
        }, event_id=event_id)
        update_with_changelog(db, s, "hires", hire, {"status": "Started"}, event_id=event_id, actor=actor.event_actor)

        # 錄用時掛的約定薪資（P2 A：新版本）與契約（P2 B）接續到僱傭關係
        comp_ids, contract_ids = [], []
        for c in db.compensations.find({"tenant_id": t, "hire_id": hire["_id"], "is_current": True}, session=s):
            new_version(db, s, "compensations", c, {"employment_id": emp_id}, event_id=event_id)
            comp_ids.append(str(c["entity_id"]))
        for c in db.employment_contracts.find({"tenant_id": t, "hire_id": hire["_id"]}, session=s):
            update_with_changelog(db, s, "employment_contracts", c, {"employment_id": emp_id}, event_id=event_id,
                                  actor=actor.event_actor)
            contract_ids.append(str(c["_id"]))

        employment = db.employments.find_one({"entity_id": emp_id, "is_current": True}, session=s)
        subj = ap.Subject.of_employment(employment)
        person = db.persons.find_one({"entity_id": person_id, "is_current": True}, session=s)
        employer = db.employers.find_one({"_id": employer_id}, session=s)
        warn = warnings.minimum_wage(db, employer, ap.compensation_on(db, subj, start, session=s), start, s)
        warn += warnings.work_authorization(db, person, employer_id, start, s)
        if not comp_ids:
            warn.append(warnings.warning(db, "R21", start, "MISSING_COMPENSATION", subject=("employments", emp_id), session=s))
        if not contract_ids:
            warn.append(warnings.warning(db, "R21", start, "MISSING_CONTRACT", subject=("employments", emp_id), session=s))

        proposal_id = proposals.propose_enrollment_filing(db, s, subj, start, cause_event_id=event_id)
        # annual-leave-grant 05_mapping D-04：到職日在過去時，同一交易補上已到的特休給予
        hooks.publish(db, s, hooks.HookEvent(hooks.EMPLOYMENT_STARTED, tenant_id=t, event_id=event_id,
                                             employment_id=emp_id, employer_id=employer_id))
        return {"event_id": str(event_id), "employment_id": str(emp_id), "hire_id": str(hire["_id"]),
                "person_id": str(person_id), "warnings": warn, "compensation_ids": comp_ids,
                "contract_ids": contract_ids, "enrollment_proposal_id": str(proposal_id)}
    return run_in_transaction(db, tx)


def record_employment_period(db, actor: Actor, employment_id: str, body: dict) -> dict:
    """RecordEmploymentPeriod（POST /v1/employments/{id}/periods，03_flows D-21、05_mapping D-23）：
    這個職務從 from 起是否依法應參加公教或軍保。是真的改變或補上未知的值，不是更正；新增一段，
    前一段的 to 設為新一段 from 的前一天；產生新版本的僱傭關係並觸發加保待辦重新判定。"""
    start = D(body["from"])

    def tx(s):
        emp = get_current(db, "employments", oid(employment_id), actor.tenant_id, s)
        ended = to_date(emp.get("ended_on"))
        if start < to_date(emp["start_date"]) or (ended and start > ended):     # R64：起日要在僱傭期間內
            raise Blocked("R64", "PERIOD_OUTSIDE_EMPLOYMENT", "起日要在僱傭期間內（不早於到職日、不晚於結束日）")
        periods = [p for p in emp.get("public_or_military_insurance_covered") or [] if to_date(p["from"]) < start]
        for p in periods:
            if p.get("to") is None or to_date(p["to"]) >= start:
                p["to"] = to_dt(start - timedelta(days=1))
        periods.append({"value": body["public_or_military_insurance_covered"], "from": to_dt(start)})

        event_id = record_event(db, s, tenant_id=actor.tenant_id, type="RecordEmploymentPeriod",
                                subject=("employments", emp["entity_id"]), actor=actor.event_actor,
                                occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(start),
                                evidence=body["evidence"])
        nxt = new_version(db, s, "employments", emp, {"public_or_military_insurance_covered": periods}, event_id=event_id)
        proposals.propose_enrollment_filing(db, s, ap.Subject.of_employment(nxt), start,              # 條件改變的那一天重新判定
                                            cause_event_id=event_id)
        return {"event_id": str(event_id), "employment_id": str(emp["entity_id"]), "warnings": []}
    return run_in_transaction(db, tx)


def _rule_refs(warn: list[dict]) -> list[dict] | None:
    return [{"rule_id": w["rule_id"], "version": w["rule_version"], "revision": w["rule_revision"]} for w in warn] or None
