"""UC-03 登錄實際加保與投保薪資：RecordInsuranceFiling、DeclareInsuredSalary。"""
from datetime import timedelta

from bson import ObjectId

from app.auth import Actor
from app.db import oid, run_in_transaction, to_date, to_dec, to_dec128, to_dt
from app.errors import Blocked
from app.rules import applicability as ap
from app.rules import versions
from app.rules.warnings import warning
from app.seed import EI, LI
from app.store import get_current, get_shared, insert_versioned, record_event, update_with_changelog


def record_insurance_filing(db, actor: Actor, body) -> dict:
    """擋下：R07（投保單位）、R50（回執或標示無回執）；提醒：R61（早於到職日）。回傳現算的晚辦天數（R35，不落地）。"""
    if not body.receipt_ref and not body.no_receipt:
        raise Blocked("R50", "RECEIPT_REQUIRED", "要附保險人回執，或標示無回執")

    def tx(s):
        emp = get_current(db, "employments", oid(body.employment_id), actor.tenant_id, s)
        scheme = get_shared(db, "social_insurance_schemes", oid(body.scheme_id), s)
        unit = None
        if body.insurance_unit_id:
            unit = get_current(db, "insurance_units", oid(body.insurance_unit_id), actor.tenant_id, s)
        tw = db.jurisdictions.find_one({"code": "TW"}, session=s)["_id"]
        if scheme["jurisdiction_id"] == tw and unit is None:
            raise Blocked("R07", "UNIT_REQUIRED", "台灣的制度一定要經由投保單位")
        if unit and unit["employer_id"] != emp["employer_id"]:
            raise Blocked("R07", "UNIT_OTHER_EMPLOYER", "投保單位的雇主和僱傭關係的雇主不同")
        if unit and scheme["code"] not in (unit.get("scheme_codes") or []):
            raise Blocked("R07", "UNIT_SCHEME_NOT_COVERED", f"投保單位不涵蓋 {scheme['code']}")

        start = to_date(emp["start_date"])
        effective = body.effective_from
        if effective is None and scheme["code"] in (LI, EI):                 # R31：到職當日通知為當日，否則翌日
            effective = body.filed_on if body.filed_on == start else body.filed_on + timedelta(days=1)
        warn = []
        if body.filed_on < start or (effective and effective < start):
            warn.append(warning(None, "R61", "FILED_BEFORE_START", {"filed_on": str(body.filed_on)}))

        event_id = ObjectId()
        ent = insert_versioned(db, s, "insurance_enrollments", {
            "tenant_id": actor.tenant_id, "employment_id": emp["entity_id"], "scheme_id": scheme["_id"],
            "insurance_unit_id": unit["_id"] if unit else None, "filed_on": to_dt(body.filed_on),
            "voluntary": body.voluntary, "effective_from": to_dt(effective), "receipt_ref": body.receipt_ref,
            "no_receipt": body.no_receipt or None, "status": "Enrolled", "annulled": False,
        }, event_id=event_id)
        record_event(db, s, tenant_id=actor.tenant_id, type="RecordInsuranceFiling",
                     subject=("insurance_enrollments", ent), actor=actor.event_actor, occurred_at=body.occurred_at,
                     effective_from=to_dt(effective), event_id=event_id)

        # 結案加保待辦中這種保險的那一列（P2 B）
        legal = None
        prop = db.enrollment_proposals.find_one({"tenant_id": actor.tenant_id, "employment_id": emp["entity_id"],
                                                 "superseded_by": {"$exists": False}}, session=s)
        if prop:
            items = prop["items"]
            for it in items:
                if it["scheme_code"] == scheme["code"] and not it.get("closed_by_enrollment_id"):
                    it["closed_by_enrollment_id"] = ent
                    legal = to_date(it.get("legal_effective_date"))
                    break
            update_with_changelog(db, s, "enrollment_proposals", prop, {"items": items}, event_id=event_id,
                                  actor=actor.event_actor)
        late = None if body.voluntary else ap.days_late(legal, effective)     # R35：自願加保不算
        return {"entity_id": str(ent), "event_id": str(event_id), "warnings": warn,
                "effective_from": effective, "days_late": late}
    return run_in_transaction(db, tx)


def declare_insured_salary(db, actor: Actor, enrollment_id: str, body) -> dict:
    """DeclareInsuredSalary；R45：申報級距和應申報級距不同 → 提醒（用這筆自己的生效日與分級表版本；逕調不比）。"""
    def tx(s):
        enr = get_current(db, "insurance_enrollments", oid(enrollment_id), actor.tenant_id, s)
        scheme = get_shared(db, "social_insurance_schemes", enr["scheme_id"], s)
        emp = get_current(db, "employments", enr["employment_id"], actor.tenant_id, s)
        on = body.effective_from
        rid = ap.GRADE_RULE[scheme["code"]]
        table = versions.rule(db, rid, on, session=s)
        warn = []
        if table is None:
            warn.append(warning(None, rid, "NO_RULE_VERSION"))
        elif body.source != "INSURED_SALARY_SOURCE.INSURER_ADJUSTED":
            facts = ap.load_facts(db, emp, on, session=s)
            bases, _, _ = ap.wage_bases(db, facts, on, session=s)
            if bases:
                r39 = versions.rule(db, "R39", on, session=s)
                base_name = next(n for n, sp in r39["params"]["bases"].items() if scheme["code"] in sp["schemes"])
                expected = ap.lookup_grade(table["params"], bases[base_name])
                if expected and expected["grade"] != body.grade:
                    warn.append(warning(table, "R45", "GRADE_MISMATCH",
                                        {"declared": body.grade, "expected": expected["grade"]}))
        event_id = ObjectId()
        ent = insert_versioned(db, s, "insured_salaries", {
            "tenant_id": actor.tenant_id, "enrollment_id": enr["entity_id"],
            "declared_amount": to_dec128(body.declared_amount), "grade": body.grade,
            "grading_table_version": versions.ref(table) if table else None, "declared_on": to_dt(body.declared_on),
            "source": body.source, "effective_from": to_dt(on), "status": "Effective", "annulled": False,
        }, event_id=event_id)
        record_event(db, s, tenant_id=actor.tenant_id, type="DeclareInsuredSalary", subject=("insured_salaries", ent),
                     actor=actor.event_actor, occurred_at=body.occurred_at, effective_from=to_dt(on),
                     rule_versions=[versions.ref(table)] if table else None, event_id=event_id)
        return {"entity_id": str(ent), "event_id": str(event_id), "warnings": warn}
    return run_in_transaction(db, tx)
