"""本切片的法規警告與提醒（查詢時現算，05_mapping 3.1、D-12）：R81、R83、R94、R96、R99；資料不足（core R60）。

R71 在 fixed_start_year_method 的預設做法下不會成立（04 R71），這版只實作預設做法，所以不判定。
R76、R78、R84 在觸發它的動作回應（actions.py）。
"""
from decimal import Decimal

from app.db import to_date, to_dec
from app.leave import basis as B
from app.leave import dates
from app.leave import ledger as L
from app.leave.ledger import Ctx
from app.leave.views import notice_info
from app.rules import warnings as W

# 警告與擋下的 message_code 見 05_mapping 2.3（D-30）
NOTICE_OVERDUE, NOTICE_LATE, NOTICE_BEFORE_ACQUIRED = "NOTICE_OVERDUE", "NOTICE_LATE", "NOTICE_BEFORE_ACQUIRED"


def _w(ctx: Ctx, rule_id, message_code, *, subject=None, warned_value=None) -> dict:
    return W.warning(ctx.db, rule_id, ctx.today, message_code, subject=subject, warned_value=warned_value, session=ctx.s)


def for_entitlement(ctx: Ctx, ent: dict) -> list[dict]:
    out = []
    subj = ("leave_entitlements", ent["entity_id"])
    due, status = notice_info(ctx, ent, ctx.today)
    if status == "NOTICE_STATUS.OVERDUE":
        out.append(_w(ctx, "R81", NOTICE_OVERDUE, subject=subj + ("notified_on",), warned_value={"notice_due_on": str(due)}))
    elif status == "NOTICE_STATUS.NOTIFIED_LATE":
        out.append(_w(ctx, "R81", NOTICE_LATE, subject=subj + ("notified_on",),
                      warned_value={"notice_due_on": str(due), "notified_on": str(to_date(ent["notified_on"]))}))
    if status not in ("NOT_APPLICABLE", "INSUFFICIENT_DATA") and ent.get("notified_on") \
            and to_date(ent["notified_on"]) < to_date(ent["acquired_on"]):
        out.append(_w(ctx, "R81", NOTICE_BEFORE_ACQUIRED, subject=subj + ("notified_on",),
                      warned_value={"notified_on": str(to_date(ent["notified_on"])),
                                    "acquired_on": str(to_date(ent["acquired_on"]))}))
    u = L.used(ctx, ent)
    if ent["status"] == "Voided":
        if u > 0:
            out.append(_w(ctx, "R96", "USED_ON_VOIDED", subject=subj, warned_value={"used_quantity": str(u)}))
        return out
    if u > to_dec(ent["quantity"]):
        out.append(_w(ctx, "R96", "USED_OVER_QUANTITY", subject=subj,
                      warned_value={"used_quantity": str(u), "quantity": str(to_dec(ent["quantity"]))}))
    a = L.deferral(ctx, ent["entity_id"], ("Agreed",))
    if a is not None:
        remaining = L.quantities(ctx, ent).remaining
        if to_dec(a["deferred_quantity"]) > remaining:
            out.append(over_remaining(ctx, a, remaining))
    for c in L.conversions(ctx, ent["entity_id"]):
        w = provisional_overdue(ctx, c)
        if w:
            out.append(w)
    return out


def over_remaining(ctx: Ctx, a: dict, remaining: Decimal) -> dict:
    """R83：協商遞延額度超過還可以休的。"""
    return _w(ctx, "R83", "DEFERRAL_OVER_REMAINING", subject=("leave_deferral_agreements", a["entity_id"], "deferred_quantity"),
              warned_value={"deferred_quantity": str(to_dec(a["deferred_quantity"])), "remaining_quantity": str(remaining)})


def provisional_overdue(ctx: Ctx, c: dict) -> dict | None:
    """R94：待確認的轉換沒有確認。"""
    if c["status"] != "Provisional":
        return None
    days = B.rule(ctx.db, "R94", ctx.today, ctx.s)["params"]["provisional_review_days"]
    limit = to_date(c["determined_on"]) + dates.DAY * days
    if c["target"] == L.WAGES and to_dec(c["quantity"]) > 0 and c.get("payment_due_on"):
        limit = max(limit, to_date(c["payment_due_on"]))
    if ctx.today > limit:
        return _w(ctx, "R94", "PROVISIONAL_CONVERSION_OVERDUE", subject=("leave_conversions", c["entity_id"]),
                  warned_value={"review_due_on": str(limit)})
    return None


def merge_seniority(ctx: Ctx, emp: dict) -> list[dict]:
    """R99：同一個人在同一雇主，前一段結束後未滿 seniority_merge_gap_months 個月又訂定新約或到職。"""
    start = to_date(emp.get("start_date"))
    if start is None:
        return []
    signed = [start]
    links = [{"employment_id": emp["entity_id"]}] + ([{"hire_id": emp["hire_id"]}] if emp.get("hire_id") else [])
    contract_ids = [c["_id"] for c in ctx.db.employment_contracts.find({"tenant_id": ctx.tenant_id, "$or": links},
                                                                       session=ctx.s)]
    for e in ctx.db.events.find({"type": "SignContract", "subject.id": {"$in": contract_ids}}, session=ctx.s):
        signed.append(to_date(e.get("occurred_at") or e["recorded_at"]))
    renewed = min(signed)
    months = B.rule(ctx.db, "R99", start, ctx.s)["params"]["seniority_merge_gap_months"]
    out = []
    for prev in ctx.db.employments.find({"tenant_id": ctx.tenant_id, "person_id": emp["person_id"],
                                         "employer_id": emp["employer_id"], "is_current": True,
                                         "entity_id": {"$ne": emp["entity_id"]}, "annulled": {"$ne": True}}, session=ctx.s):
        ended = to_date(prev.get("ended_on"))
        if ended is None or ended >= start:
            continue
        gap_start = ended + dates.DAY
        if renewed <= dates.period_end(gap_start, months):
            out.append(_w(ctx, "R99", "POSSIBLE_SENIORITY_MERGE", subject=("employments", emp["entity_id"]),
                          warned_value={"previous_employment_id": str(prev["entity_id"]), "previous_ended_on": str(ended),
                                        "renewed_on": str(renewed)}))
    return out


def override_id(ctx: Ctx, w: dict, employment_id) -> str | None:
    """已忽略的標出 warning_override_id（core OverrideWarning；忽略何時失效依 core R51，由 hire-employee 處理）。"""
    q = {"tenant_id": ctx.tenant_id, "employment_id": employment_id, "status": "Active", "rule_ref.rule_id": w["rule_id"]}
    if w.get("subject"):
        q["subject_ref.collection"] = w["subject"]["collection"]
    o = ctx.db.warning_overrides.find_one(q, session=ctx.s)
    return str(o["_id"]) if o else None


def for_employment(ctx: Ctx, emp: dict, employer: dict) -> tuple[list[dict], list[dict]]:
    """(警告, 資料不足)。"""
    warns = []
    for ent in L.entitlements(ctx, emp["entity_id"]):
        warns += for_entitlement(ctx, ent)
    warns += merge_seniority(ctx, emp)
    insufficient = B.expected(ctx.db, ctx.s, emp, employer, ctx.today).insufficient
    return warns, insufficient
