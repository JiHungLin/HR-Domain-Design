"""查詢的回應（api.yaml EntitlementView、ConversionView…）與推導值：告知期限與告知狀態（R80、R81），數量（C01）。"""
from datetime import date

from app.db import to_date, to_dec
from app.leave import basis as B
from app.leave import dates
from app.leave import ledger as L
from app.leave.ledger import Ctx

# used_quantity_basis 的值（05_mapping 2.3、D-30）
USED_BASIS_CURRENT = "CURRENT_TOTAL"


def s(v):
    return None if v is None else str(v)


def ds(v):
    return None if v is None else str(to_date(v))


def qs(v):
    return None if v is None else str(to_dec(v))


def compact(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def notice_info(ctx: Ctx, ent: dict, today: date) -> tuple[date | None, str]:
    """R80 告知期限、R81 告知狀態（決策表；04 D-24：隨僱傭關係結束、作廢的不判定）。"""
    if ent["origin"] != B.RULE_GRANT or ent["source"] != B.STATUTORY or ent["status"] in ("EndedWithEmployment", "Voided"):
        return None, "NOT_APPLICABLE"
    acq = to_date(ent.get("acquired_on"))
    if acq is None:
        return None, "INSUFFICIENT_DATA"
    days = B.rule(ctx.db, "R80", acq, ctx.s)["params"]["notice_period_days"]
    due = acq + dates.DAY * days                          # 從取得日的隔天算第 1 日（EQ-014）
    notified = to_date(ent.get("notified_on"))
    if notified is None:
        return due, "NOTICE_STATUS.PENDING" if today <= due else "NOTICE_STATUS.OVERDUE"
    if notified > due:
        return due, "NOTICE_STATUS.NOTIFIED_LATE"
    return due, "NOTICE_STATUS.NOTIFIED"                  # 早於取得日的另成立提醒（warnings.py）


def rule_ref_view(r: dict) -> dict:
    return compact({"kind": r["kind"], "rule_id": r.get("rule_id"), "policy_id": s(r.get("policy_id")),
                    "version": r["version"], "revision": r["revision"]})


def entitlement_view(ctx: Ctx, ent: dict, today: date) -> dict:
    due, status = notice_info(ctx, ent, today)
    q = L.quantities(ctx, ent)
    return compact({
        "entitlement_id": s(ent["entity_id"]), "employment_id": s(ent["employment_id"]),
        "leave_type_code": ent["leave_type_code"], "source": ent["source"], "origin": ent["origin"],
        "period_sequence": ent.get("period_sequence"), "seniority_tier": ent.get("seniority_tier"),
        "acquired_on": ds(ent["acquired_on"]), "quantity": qs(ent["quantity"]), "unit": ent["unit"],
        "valid_from": ds(ent["valid_from"]), "valid_to": ds(ent["valid_to"]), "leave_year_basis": ent.get("leave_year_basis"),
        "basis_rule_versions": [rule_ref_view(r) for r in ent.get("basis_rule_versions") or []],
        "no_rule_version": ent.get("no_rule_version"), "basis_seniority": ent.get("basis_seniority"),
        "basis_start_date": ds(ent.get("basis_start_date")), "notified_on": ds(ent.get("notified_on")),
        "notice_due_on": s(due), "notice_status": status,
        "pre_system_used_quantity": qs(ent.get("pre_system_used_quantity")),
        "registered_original_year_end": ds(ent.get("registered_original_year_end")),
        "policy_id": s(ent.get("policy_id")), "deferred_from_id": s(ent.get("deferred_from_id")),
        "deferred_under_id": s(ent.get("deferred_under_id")),
        "applied_year_agreement_id": s(ent.get("applied_year_agreement_id")),
        "applied_year_default_policy_id": s(ent.get("applied_year_default_policy_id")),
        "status": ent["status"], "revision": ent["revision"],
        "quantities": {"used_quantity": str(q.used), "used_quantity_basis": USED_BASIS_CURRENT,
                       "deferred_out_quantity": str(q.deferred_out), "converted_quantity": str(q.converted),
                       "expired_quantity": str(q.expired), "remaining_quantity": str(q.remaining)},
    })


def conversion_view(c: dict) -> dict:
    return compact({
        "conversion_id": s(c["entity_id"]), "employment_id": s(c["employment_id"]), "entitlement_id": s(c["entitlement_id"]),
        "corrects_conversion_id": s(c.get("corrects_conversion_id")),
        "corrects_judgment_event_id": s(c.get("corrects_judgment_event_id")),
        "reason": c["reason"], "target": c["target"], "quantity": qs(c["quantity"]), "determined_on": ds(c["determined_on"]),
        "basis_rule_versions": [rule_ref_view(r) for r in c.get("basis_rule_versions") or []],
        "correction_cause": c.get("correction_cause"), "wage_basis_date": ds(c.get("wage_basis_date")),
        "payment_due_on": ds(c.get("payment_due_on")), "status": c["status"], "discarded_by_id": s(c.get("discarded_by_id")),
    })


def deferral_view(a: dict) -> dict:
    return compact({"deferral_agreement_id": s(a["entity_id"]), "entitlement_id": s(a["entitlement_id"]),
                    "agreed_on": ds(a["agreed_on"]), "deferred_quantity": qs(a["deferred_quantity"]),
                    "agreement_note": a.get("agreement_note"), "status": a["status"], "revision": a["revision"]})


def year_end_view(e: dict) -> dict:
    y = e["payload"]["year_end"]
    ref = y.get("deferral_agreement_ref")
    return compact({
        "event_id": s(e["_id"]), "event_type": e["type"], "determined_on": str(to_date(e["recorded_at"])),
        "used_quantity_known": y["used_quantity_known"], "unused_quantity": y["unused_quantity"],
        "deferral_agreement_ref": compact({"id": s(ref["id"]), "version_event_id": s(ref.get("version_event_id"))}) if ref else None,
        "deferred_in_quantity": y.get("deferred_in_quantity"), "deferred_in_entitlement_id": s(y.get("deferred_in_entitlement_id")),
        "conversion_ids": [s(c) for c in y["conversion_ids"]], "late": y["late"],
    })


def notice_view(n: dict) -> dict:
    return compact({
        "notice_id": s(n["_id"]), "employment_id": s(n["employment_id"]), "trigger_event_id": s(n["trigger_event_id"]),
        "root_event_id": s(n["root_event_id"]),
        "changed": [compact({"entitlement_id": s(c["entitlement_id"]), "before": c.get("before"), "after": c.get("after")})
                    for c in n.get("changed") or []],
        "added_ids": [s(i) for i in n.get("added_ids") or []], "voided_ids": [s(i) for i in n.get("voided_ids") or []],
        "conversion_ids": [s(i) for i in n.get("conversion_ids") or []],
        "provisional_conversion_ids": [s(i) for i in n.get("provisional_conversion_ids") or []],
        "action_items": [compact({"kind": a["kind"], "entitlement_id": s(a.get("entitlement_id")), "detail": a.get("detail")})
                         for a in n.get("action_items") or []],
        "notified_to": n.get("notified_to"), "notified_at": n["notified_at"].isoformat(),
    })
