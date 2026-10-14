"""UC-03 登錄實際加保與投保薪資：RecordInsuranceFiling、DeclareInsuredSalary。"""
from datetime import timedelta

from bson import ObjectId

from app.auth import Actor
from app.db import oid, run_in_transaction, to_date, to_dec128, to_dt
from app.errors import Blocked
from app.rules import applicability as ap
from app.rules import versions
from app.rules.warnings import warning
from app.seed import EI, LI
from app.services.hiring import D, DT
from app.store import get_current, get_shared, insert_versioned, record_event, update_with_changelog


def record_insurance_filing(db, actor: Actor, body: dict) -> dict:
    """擋下：R07（投保單位）、R50（回執或標示無回執）；提醒：R61（早於到職日）。結案加保待辦中這種保險的那一列。"""
    if not body.get("receipt_ref") and not body.get("no_receipt"):
        raise Blocked("R50", "RECEIPT_REQUIRED", "要附保險人回執，或標示無回執")
    filed = D(body["filed_on"])

    def tx(s):
        t = actor.tenant_id
        emp = get_current(db, "employments", oid(body["employment_id"]), t, s)
        scheme = get_shared(db, "social_insurance_schemes", oid(body["scheme_id"]), s)
        unit = get_current(db, "insurance_units", oid(body["insurance_unit_id"]), t, s) if body.get("insurance_unit_id") else None
        tw = db.jurisdictions.find_one({"code": "TW"}, session=s)["_id"]
        if scheme["jurisdiction_id"] == tw and unit is None:
            raise Blocked("R07", "UNIT_REQUIRED", "台灣的制度一定要經由投保單位")
        if unit and unit["employer_id"] != emp["employer_id"]:
            raise Blocked("R07", "UNIT_OTHER_EMPLOYER", "投保單位的雇主和僱傭關係的雇主不同")
        if unit and scheme["code"] not in (unit.get("scheme_codes") or []):
            raise Blocked("R07", "UNIT_SCHEME_NOT_COVERED", f"投保單位不涵蓋 {scheme['code']}")

        start = to_date(emp["start_date"])
        effective = D(body.get("effective_from"))
        if effective is None and scheme["code"] in (LI, EI):                  # R31：到職當日通知為當日，否則翌日
            effective = filed if filed == start else filed + timedelta(days=1)
        event_id = ObjectId()
        ent = insert_versioned(db, s, "insurance_enrollments", {
            "tenant_id": t, "employment_id": emp["entity_id"], "scheme_id": scheme["_id"],
            "insurance_unit_id": unit["_id"] if unit else None, "filed_on": to_dt(filed),
            "voluntary": body["voluntary"], "effective_from": to_dt(effective), "receipt_ref": body.get("receipt_ref"),
            "no_receipt": body.get("no_receipt") or None, "status": "Enrolled", "annulled": False,
        }, event_id=event_id)
        warn = []
        if filed < start or (effective and effective < start):
            warn.append(warning(db, "R61", start, "FILED_BEFORE_START", subject=("insurance_enrollments", ent, "filed_on"),
                                warned_value={"filed_on": str(filed), "start_date": str(start)}, session=s))
        record_event(db, s, tenant_id=t, type="RecordInsuranceFiling", subject=("insurance_enrollments", ent),
                     actor=actor.event_actor, occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(effective),
                     event_id=event_id)

        out = {"event_id": str(event_id), "enrollment_id": str(ent), "warnings": warn}
        prop = db.enrollment_proposals.find_one({"tenant_id": t, "employment_id": emp["entity_id"],
                                                 "superseded_by": {"$exists": False}}, session=s)
        if prop:
            items = prop["items"]
            hit = next((it for it in items if it["scheme_code"] == scheme["code"] and not it.get("closed_by_enrollment_id")), None)
            if hit:
                hit["closed_by_enrollment_id"] = ent
                update_with_changelog(db, s, "enrollment_proposals", prop, {"items": items}, event_id=event_id,
                                      actor=actor.event_actor)
                out["enrollment_proposal_id"] = str(prop["_id"])
        return out
    return run_in_transaction(db, tx)


def declare_insured_salary(db, actor: Actor, enrollment_id: str, body: dict) -> dict:
    """DeclareInsuredSalary；R45：申報級距和應申報級距不同 → 提醒（用這筆自己的生效日與分級表版本；逕調不比）。"""
    on = D(body["effective_from"])
    source = body.get("source", "INSURED_SALARY_SOURCE.EMPLOYER_DECLARED")

    def tx(s):
        t = actor.tenant_id
        enr = get_current(db, "insurance_enrollments", oid(enrollment_id), t, s)
        scheme = get_shared(db, "social_insurance_schemes", enr["scheme_id"], s)
        emp = get_current(db, "employments", enr["employment_id"], t, s)
        table = versions.rule(db, ap.GRADE_RULE[scheme["code"]], on, session=s)
        event_id = ObjectId()
        ent = insert_versioned(db, s, "insured_salaries", {
            "tenant_id": t, "enrollment_id": enr["entity_id"], "declared_amount": to_dec128(body["declared_amount"]),
            "grade": body["grade"], "grading_table_version": versions.ref(table) if table else None,
            "declared_on": to_dt(D(body["declared_on"])), "source": source, "effective_from": to_dt(on),
            "receipt_ref": body.get("receipt_ref"), "no_receipt": body.get("no_receipt") or None,
            "status": "Effective", "annulled": False,
        }, event_id=event_id)
        warn = []
        if table and source != "INSURED_SALARY_SOURCE.INSURER_ADJUSTED":
            comp = ap.compensation_on(db, ap.Subject.of_employment(emp), on, session=s)
            bases, r39 = ap.wage_bases(db, comp, on, session=s)
            if bases:
                expected = ap.lookup_grade(table["params"], bases[ap.base_for(r39, scheme["code"])])
                if expected["grade"] != body["grade"]:
                    warn.append(warning(db, "R45", on, "GRADE_MISMATCH", subject=("insured_salaries", ent, "grade"),
                                        warned_value={"declared": body["grade"], "expected": expected["grade"],
                                                      "grading_table": versions.ref(table)}, session=s))
        record_event(db, s, tenant_id=t, type="DeclareInsuredSalary", subject=("insured_salaries", ent),
                     actor=actor.event_actor, occurred_at=DT(body.get("occurred_at")), effective_from=to_dt(on),
                     rule_versions=[versions.ref(table)] if table else None, event_id=event_id)
        return {"event_id": str(event_id), "insured_salary_id": str(ent), "enrollment_id": str(enr["entity_id"]),
                "warnings": warn}
    return run_in_transaction(db, tx)
