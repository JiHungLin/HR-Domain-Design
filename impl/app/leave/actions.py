"""annual-leave-grant 人的動作（05_mapping 第二節）：一個動作一個多文件交易。

每個寫入某段僱傭關係的交易先上鎖、先處理那一段還沒處理的重新判定佇列（D-05、D-18；app/leave/locks.py）；
觸發的連鎖（RejudgeLeaveYearEnd、ReassessLeaveEntitlements、NotifyLeaveReassessment）在同一交易完成（D-04）。
"""
from datetime import date
from decimal import Decimal

from bson import ObjectId

from app.auth import Actor
from app.db import now, oid, run_in_transaction, to_date, to_dec, to_dec128, to_dt
from app.errors import Blocked, NotFound, Superseded
from app.leave import basis as B
from app.leave import clock, locks, scheduler
from app.leave import engine as E
from app.leave import ledger as L
from app.leave import warnings as LW
from app.leave.ledger import Ctx
from app.leave.views import notice_info
from app.rules import warnings as W
from app.spec import RequestInvalid
from app.store import clean, get_current, insert_versioned, new_version, record_event, update_with_changelog


def D(v: str | None) -> date | None:
    return date.fromisoformat(v) if v else None


def Q(v: str) -> Decimal:
    return Decimal(v)


def _ctx(db, s, actor: Actor, employer: dict, root_event_id=None) -> Ctx:
    return Ctx(db, s, actor.tenant_id, clock.today(db, employer, s), root_event_id=root_event_id, actor=actor.event_actor)


def _employment_tx(db, actor: Actor, employment_id, fn):
    """fn(ctx, employment, employer, notice_ids)：僱傭關係層級的動作。"""
    def tx(s):
        emp = get_current(db, "employments", oid(employment_id), actor.tenant_id, s)
        employer = locks.employer_of(db, s, emp)
        ctx = _ctx(db, s, actor, employer)
        notice_ids = locks.begin(ctx, emp)
        emp = db.employments.find_one({"entity_id": emp["entity_id"], "is_current": True}, session=s)
        return fn(ctx, emp, employer, notice_ids)
    return run_in_transaction(db, tx)


def _entitlement_tx(db, actor: Actor, entitlement_id, fn):
    """fn(ctx, entitlement, employment, employer, notice_ids)。"""
    def tx(s):
        ent = get_current(db, L.ENT, oid(entitlement_id), actor.tenant_id, s)
        emp = db.employments.find_one({"entity_id": ent["employment_id"], "is_current": True}, session=s)
        employer = locks.employer_of(db, s, emp)
        ctx = _ctx(db, s, actor, employer)
        notice_ids = locks.begin(ctx, emp)
        ent = L.entitlement(ctx, ent["entity_id"])                 # 佇列可能剛改過這一筆
        return fn(ctx, ent, emp, employer, notice_ids)
    return run_in_transaction(db, tx)


def _flush(ctx: Ctx, notice: E.Notice, trigger, out: list) -> list:
    nid = notice.flush(ctx, trigger)
    return out + ([nid] if nid else [])


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _rule_refs(warn: list[dict]) -> list[dict] | None:
    return [{"rule_id": w["rule_id"], "version": w["rule_version"], "revision": w["rule_revision"]} for w in warn] or None


# ---- RecordLeaveNotice ----

def record_notice(db, actor: Actor, entitlement_id: str, body: dict) -> dict:
    actor.require("HR", "EMPLOYER")
    notified = D(body["notified_on"])

    def fn(ctx, ent, emp, employer, notice_ids):
        if ent["origin"] != B.RULE_GRANT or ent["source"] != B.STATUTORY:     # R80：只有依規則給予的法定那一筆有告知
            raise Blocked("R80", "NOTICE_NOT_APPLICABLE", "只有依規則給予的法定特休要告知")
        if ent["status"] == "Voided":
            raise Blocked(None, "INVALID_STATE", "這一筆已作廢")
        if ent.get("notified_on"):                                            # 已有的只能由人資用 CorrectRecord 改（03_flows D-08）
            raise Blocked(None, "ALREADY_NOTIFIED", "這一筆已有告知日，要改請人資更正")
        if notified < to_date(emp["start_date"]) or notified > ctx.today:
            raise Blocked("R98", "DATE_ORDER", "告知日要不早於到職日、不晚於登錄當天")
        event_id = record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="RecordLeaveNotice",
                                subject=(L.ENT, ent["entity_id"]), actor=ctx.actor, occurred_at=to_dt(notified),
                                evidence=body.get("evidence"))
        cur = L.change_entitlement(ctx, ent, {"notified_on": notified}, event_id=event_id)
        due, status = notice_info(ctx, cur, ctx.today)
        warn = LW.for_entitlement(ctx, cur)
        warn = [w for w in warn if w["rule_id"] == "R81"]
        return {"event_id": str(event_id), "entitlement_id": str(ent["entity_id"]), "notified_on": str(notified),
                "notice_due_on": str(due), "notice_status": status,
                "recorded_at": db.events.find_one({"_id": event_id}, session=ctx.s)["recorded_at"].isoformat(),
                "warnings": warn}
    return _entitlement_tx(db, actor, entitlement_id, fn)


# ---- LoadUsedQuantityFixture [靜態替代] ----

def load_used_quantity(db, actor: Actor, entitlement_id: str, body: dict) -> dict:
    actor.require("HR")
    qty = Q(body["used_quantity"])
    if qty < 0:
        raise Blocked(None, "NEGATIVE_QUANTITY", "已休不能是負數")

    def fn(ctx, ent, emp, employer, notice_ids):
        event_id = record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="LoadUsedQuantityFixture",
                                subject=(L.ENT, ent["entity_id"]), actor=ctx.actor, reason=body["reason"],
                                payload={"used_quantity": str(qty)})
        f = db.leave_used_quantity_fixtures.find_one({"entitlement_id": ent["entity_id"]}, session=ctx.s)
        fields = {"used_quantity": to_dec128(qty), "recorded_by": actor.account_id, "recorded_at": ctx.db.events.find_one(
            {"_id": event_id}, session=ctx.s)["recorded_at"], "reason": body["reason"]}
        if f is None:
            db.leave_used_quantity_fixtures.insert_one({"tenant_id": ctx.tenant_id, "entitlement_id": ent["entity_id"],
                                                        **fields, "created_at": fields["recorded_at"]}, session=ctx.s)
        else:
            update_with_changelog(db, ctx.s, "leave_used_quantity_fixtures", f, fields, event_id=event_id, actor=ctx.actor)
        out = notice_ids
        if ent["status"] == "YearEnded":                                    # 03_flows 更正方式「已休」
            ctx.root_event_id = event_id
            notice = E.Notice(ent["employment_id"])
            rj = E.rejudge(ctx, ent, E.LATE_LEAVE_RECORDED, notice)
            out = _flush(ctx, notice, rj, out)
        warn = [w for w in LW.for_entitlement(ctx, L.entitlement(ctx, ent["entity_id"])) if w["rule_id"] == "R96"]
        return {"event_id": str(event_id), "warnings": warn, "reassessment_notice_ids": _ids(out)}
    return _entitlement_tx(db, actor, entitlement_id, fn)


# ---- LoadEmploymentEndingFixture [靜態替代] ----

def load_ending(db, actor: Actor, employment_id: str, body: dict) -> dict:
    actor.require("HR")
    ended = D(body["ended_on"])

    def fn(ctx, emp, employer, notice_ids):
        if emp["status"] != "Active" or emp.get("ended_on"):
            raise Blocked(None, "INVALID_STATE", f"僱傭關係的狀態是 {emp['status']}" + ("，已有結束日" if emp.get("ended_on") else ""))
        if ended < to_date(emp["start_date"]):
            raise Blocked("R02", "END_BEFORE_START", "結束日早於到職日")
        event_id = record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="LoadEmploymentEndingFixture",
                                subject=("employments", emp["entity_id"]), actor=ctx.actor, occurred_at=to_dt(ended),
                                effective_from=to_dt(ended), reason=body["reason"])
        # 結束日在未來時只記結束日，到那天由每日排程改為 Ended 並停止特休（05_mapping D-33）
        cur = new_version(db, ctx.s, "employments", emp, {"ended_on": to_dt(ended), "end_reason": body["end_reason"]},
                          event_id=event_id)
        out = notice_ids
        if ended <= ctx.today:
            out = scheduler.end_employment(ctx, cur, event_id, out)
        return {"event_id": str(event_id), "employment_id": str(emp["entity_id"]), "reassessment_notice_ids": _ids(out),
                "warnings": []}
    return _employment_tx(db, actor, employment_id, fn)


# ---- RecordLeaveDeferral、AmendLeaveDeferral、WithdrawLeaveDeferral ----

def _deferral_guard(ctx: Ctx, ent: dict, qty: Decimal, agreed_on: date, *, exclude=None) -> None:
    """R82 擋下；R98 協商日不晚於登錄當天。"""
    if ent["origin"] not in (B.RULE_GRANT, B.REGISTERED_CURRENT):        # R88：遞延進來、補登遞延的不能再遞延
        raise Blocked("R82", "NOT_DEFERRABLE_ORIGIN", "遞延進來或補登遞延的那一筆不能再遞延")
    other = L.deferral(ctx, ent["entity_id"])
    if other and other["entity_id"] != exclude:
        raise Blocked("R82", "DEFERRAL_EXISTS", f"這一筆已有協商 {other['entity_id']}")
    if qty <= 0 or qty > to_dec(ent["quantity"]):
        raise Blocked("R82", "DEFERRAL_QUANTITY", "遞延額度要大於 0、不超過那一筆的額度")
    if ent["source"] == B.COMPANY:
        _, deferrable, found, _ = E.year_end_treatment(ctx, ent)
        if not (found and deferrable):
            raise Blocked("R82", "COMPANY_EXTRA_NOT_DEFERRABLE", "給予時那一版的公司規定不可以遞延")
    if agreed_on > ctx.today:
        raise Blocked("R98", "DATE_ORDER", "協商日不能晚於登錄當天")


def _deferral_warnings(ctx: Ctx, ent: dict, agreement: dict | None) -> list[dict]:
    """R83（登錄或修改當時）、R84（登錄時間晚於年度終結日）。"""
    out = []
    if agreement is not None:
        qs = L.quantities(ctx, ent)
        # R83：已年度終結的用「額度減已休」比，不用還可以休（04 D-26）
        base = to_dec(ent["quantity"]) - qs.used if ent["status"] == "YearEnded" else qs.remaining
        if to_dec(agreement["deferred_quantity"]) > base:
            out.append(LW.over_remaining(ctx, agreement, base))
    if ctx.today > to_date(ent["valid_to"]):
        out.append(W.warning(ctx.db, "R84", ctx.today, "DEFERRAL_RECORDED_AFTER_YEAR_END",
                             subject=(L.ENT, ent["entity_id"]), warned_value={"valid_to": str(to_date(ent["valid_to"]))},
                             session=ctx.s))
    return out


def record_deferral(db, actor: Actor, body: dict) -> dict:
    actor.require("HR")
    qty, agreed_on = Q(body["deferred_quantity"]), D(body["agreed_on"])

    def fn(ctx, ent, emp, employer, notice_ids):
        if ent["status"] not in ("Active", "YearEnded"):                   # X-08：狀態前提
            raise Blocked(None, "INVALID_STATE", f"這一筆的狀態是 {ent['status']}")
        _deferral_guard(ctx, ent, qty, agreed_on)
        event_id = ObjectId()
        status = "Agreed" if ent["status"] == "Active" else "Applied"
        aid = insert_versioned(db, ctx.s, L.DEFERRAL, clean({
            "tenant_id": ctx.tenant_id, "employment_id": ent["employment_id"], "entitlement_id": ent["entity_id"],
            "agreed_on": to_dt(agreed_on), "deferred_quantity": to_dec128(qty), "agreement_note": body.get("agreement_note"),
            "status": "Agreed"}), event_id=event_id)
        agreement = db[L.DEFERRAL].find_one({"entity_id": aid, "is_current": True}, session=ctx.s)
        warn = _deferral_warnings(ctx, ent, agreement)
        record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="RecordLeaveDeferral", subject=(L.DEFERRAL, aid),
                     actor=ctx.actor, occurred_at=to_dt(agreed_on), evidence=body.get("evidence"),
                     rule_versions=_rule_refs(warn), event_id=event_id)
        out = notice_ids
        if status == "Applied":                                            # 年度終結後才登錄 → RejudgeLeaveYearEnd
            ctx.root_event_id = event_id
            notice = E.Notice(ent["employment_id"])
            out = _flush(ctx, notice, E.rejudge(ctx, ent, E.DEFERRAL_CHANGED, notice), out)
        agreement = db[L.DEFERRAL].find_one({"entity_id": aid, "is_current": True}, session=ctx.s)
        return {"event_id": str(event_id), "deferral_agreement_id": str(aid), "status": agreement["status"],
                "warnings": warn, "reassessment_notice_ids": _ids(out)}
    return _entitlement_tx(db, actor, body["entitlement_id"], fn)


def _deferral_tx(db, actor: Actor, agreement_id: str, fn):
    a = get_current(db, L.DEFERRAL, oid(agreement_id), actor.tenant_id)

    def wrapped(ctx, ent, emp, employer, notice_ids):
        cur = db[L.DEFERRAL].find_one({"entity_id": a["entity_id"], "is_current": True}, session=ctx.s)
        if cur["status"] not in ("Agreed", "Applied"):
            raise Blocked(None, "INVALID_STATE", f"協商的狀態是 {cur['status']}")
        return fn(ctx, ent, cur, notice_ids)
    return _entitlement_tx(db, actor, str(a["entitlement_id"]), wrapped)


def amend_deferral(db, actor: Actor, agreement_id: str, body: dict) -> dict:
    actor.require("HR")
    qty, agreed_on = Q(body["deferred_quantity"]), D(body["agreed_on"])

    def fn(ctx, ent, agreement, notice_ids):
        _deferral_guard(ctx, ent, qty, agreed_on, exclude=agreement["entity_id"])
        event_id = ObjectId()
        cur = L.change_deferral(ctx, agreement, clean({"agreed_on": agreed_on, "deferred_quantity": qty,
                                                       "agreement_note": body.get("agreement_note")}), event_id=event_id)
        warn = _deferral_warnings(ctx, ent, cur)
        record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="AmendLeaveDeferral", subject=(L.DEFERRAL, agreement["entity_id"]),
                     actor=ctx.actor, occurred_at=to_dt(agreed_on), evidence=body.get("evidence"),
                     rule_versions=_rule_refs(warn), event_id=event_id)
        out = notice_ids
        if agreement["status"] == "Applied":
            ctx.root_event_id = event_id
            notice = E.Notice(ent["employment_id"])
            out = _flush(ctx, notice, E.rejudge(ctx, ent, E.DEFERRAL_CHANGED, notice), out)
        return {"event_id": str(event_id), "deferral_agreement_id": str(agreement["entity_id"]), "status": cur["status"],
                "warnings": warn, "reassessment_notice_ids": _ids(out)}
    return _deferral_tx(db, actor, agreement_id, fn)


def withdraw_deferral(db, actor: Actor, agreement_id: str, body: dict) -> dict:
    actor.require("HR")

    def fn(ctx, ent, agreement, notice_ids):
        event_id = ObjectId()
        cur = L.change_deferral(ctx, agreement, {"status": "Withdrawn"}, event_id=event_id)
        warn = _deferral_warnings(ctx, ent, None)
        record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="WithdrawLeaveDeferral",
                     subject=(L.DEFERRAL, agreement["entity_id"]), actor=ctx.actor, reason=body["reason"],
                     evidence=body.get("evidence"), rule_versions=_rule_refs(warn), event_id=event_id)
        out = notice_ids
        if agreement["status"] == "Applied":
            ctx.root_event_id = event_id
            notice = E.Notice(ent["employment_id"])
            out = _flush(ctx, notice, E.rejudge(ctx, ent, E.DEFERRAL_CHANGED, notice), out)
        return {"event_id": str(event_id), "deferral_agreement_id": str(agreement["entity_id"]), "status": cur["status"],
                "warnings": warn, "reassessment_notice_ids": _ids(out)}
    return _deferral_tx(db, actor, agreement_id, fn)


# ---- ConfirmLeaveConversion ----

def confirm_conversion(db, actor: Actor, conversion_id: str, body: dict) -> dict:
    actor.require("HR")
    c0 = get_current(db, L.CONV, oid(conversion_id), actor.tenant_id)

    def fn(ctx, ent, emp, employer, notice_ids):
        c = db[L.CONV].find_one({"entity_id": c0["entity_id"], "is_current": True}, session=ctx.s)
        if c["status"] == "Discarded":
            raise Superseded("CONVERSION_DISCARDED", c.get("discarded_by_id"))
        if c["status"] != "Provisional":
            raise Blocked(None, "INVALID_STATE", f"轉換的狀態是 {c['status']}")
        event_id = record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="ConfirmLeaveConversion",
                                subject=(L.CONV, c["entity_id"]), actor=ctx.actor, reason=body["reason"],
                                evidence=body.get("evidence"))
        L.change_conversion(ctx, c, {"status": "Determined"}, event_id=event_id)
        notice = E.Notice(ent["employment_id"])
        din_id = E.release_waiting_deferred_in(ctx, c, notice, event_id)     # 04 R92、03_flows D-17
        L.check_conservation(ctx, c["entitlement_id"])
        if din_id:
            L.check_conservation(ctx, din_id)
        return {"event_id": str(event_id), "conversion_id": str(c["entity_id"]), "status": "Determined",
                "deferred_in_entitlement_id": str(din_id) if din_id else None}
    return _entitlement_tx(db, actor, str(c0["entitlement_id"]), fn)


# ---- RecordLeaveYearAgreement、EndLeaveYearAgreement ----

def _reassess_if_retroactive(ctx: Ctx, emp: dict, employer: dict, since: date, root_event_id, why: dict, out: list) -> list:
    """R75：起日（或終止日）早於已給予的取得日時，同一交易重新判定。"""
    if any(e["origin"] == B.RULE_GRANT and not e["voided"] and to_date(e["acquired_on"]) >= since
           for e in L.entitlements(ctx, emp["entity_id"])):
        ctx.root_event_id = root_event_id
        notice = E.Notice(emp["entity_id"])
        ev = E.reassess(ctx, emp, employer, notice, basis_before=why, basis_after=why)
        return _flush(ctx, notice, ev, out)
    return out


def record_year_agreement(db, actor: Actor, body: dict) -> dict:
    actor.require("HR")
    eff, agreed_on = D(body["effective_from"]), D(body["agreed_on"])
    if body["leave_year_basis"] == B.FIXED_START and not body.get("year_start"):
        raise RequestInvalid(["year_start：固定起始日的年度要有起始月日"])

    def fn(ctx, emp, employer, notice_ids):
        if not db.leave_types.find_one({"code": body["leave_type_code"]}, session=ctx.s):
            raise NotFound(f"假別 {body['leave_type_code']} 不存在")
        if eff < to_date(emp["start_date"]) or agreed_on > ctx.today:
            raise Blocked("R98", "DATE_ORDER", "適用起日不早於到職日、協商日不晚於登錄當天")
        for a in db.leave_year_agreements.find({"tenant_id": ctx.tenant_id, "employment_id": emp["entity_id"],
                                                "leave_type_code": body["leave_type_code"]}, session=ctx.s):
            if a["status"] != "Ended" and to_date(a["effective_from"]) == eff:
                raise Blocked("R72", "YEAR_AGREEMENT_OVERLAP", f"同一天已有約定 {a['_id']}")
        event_id, aid = ObjectId(), ObjectId()
        record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="RecordLeaveYearAgreement",
                     subject=("leave_year_agreements", aid), actor=ctx.actor, occurred_at=to_dt(agreed_on),
                     effective_from=to_dt(eff), evidence=body.get("evidence"), event_id=event_id)
        db.leave_year_agreements.insert_one(clean({
            "_id": aid, "tenant_id": ctx.tenant_id, "employment_id": emp["entity_id"],
            "leave_type_code": body["leave_type_code"], "leave_year_basis": body["leave_year_basis"],
            "year_start": body.get("year_start"), "effective_from": to_dt(eff), "agreed_on": to_dt(agreed_on),
            "agreement_note": body.get("agreement_note"), "status": "Scheduled"}), session=ctx.s)
        scheduler.refresh_agreements(ctx, emp["entity_id"])          # ActivateLeaveYearAgreement 在同一交易立刻推導
        out = _reassess_if_retroactive(ctx, emp, employer, eff, event_id,
                                       {"leave_year_agreement_id": aid, "effective_from": str(eff)}, notice_ids)
        a = db.leave_year_agreements.find_one({"_id": aid}, session=ctx.s)
        return {"event_id": str(event_id), "leave_year_agreement_id": str(aid), "status": a["status"], "warnings": [],
                "reassessment_notice_ids": _ids(out)}
    return _employment_tx(db, actor, body["employment_id"], fn)


def end_year_agreement(db, actor: Actor, agreement_id: str, body: dict) -> dict:
    actor.require("HR")
    a0 = db.leave_year_agreements.find_one({"_id": oid(agreement_id)})
    if a0 is None:
        raise NotFound(f"leave_year_agreements 找不到 {agreement_id}")
    get_current(db, "leave_year_agreements", a0["_id"], actor.tenant_id)
    ended_from, agreed_on = D(body["ended_from"]), D(body["agreed_on"])

    def fn(ctx, emp, employer, notice_ids):
        a = db.leave_year_agreements.find_one({"_id": a0["_id"]}, session=ctx.s)
        if a["status"] not in ("Scheduled", "Effective"):
            raise Blocked(None, "INVALID_STATE", f"約定的狀態是 {a['status']}")
        if agreed_on > ctx.today or ended_from < to_date(a["effective_from"]):
            raise Blocked("R98", "DATE_ORDER", "協商日不晚於登錄當天、終止日不早於適用起日")
        event_id = record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="EndLeaveYearAgreement",
                                subject=("leave_year_agreements", a["_id"]), actor=ctx.actor, occurred_at=to_dt(agreed_on),
                                effective_from=to_dt(ended_from), evidence=body.get("evidence"))
        update_with_changelog(db, ctx.s, "leave_year_agreements", a, {"ended_from": to_dt(ended_from), "status": "Ended"},
                              event_id=event_id, actor=ctx.actor)
        out = _reassess_if_retroactive(ctx, emp, employer, ended_from, event_id,
                                       {"leave_year_agreement_id": a["_id"], "ended_from": str(ended_from)}, notice_ids)
        return {"event_id": str(event_id), "leave_year_agreement_id": str(a["_id"]), "status": "Ended", "warnings": [],
                "reassessment_notice_ids": _ids(out)}
    return _employment_tx(db, actor, str(a0["employment_id"]), fn)


# ---- EstablishCompanyPolicy ----

def _params_to_db(p: dict) -> dict:
    out = dict(p)
    if "company_extra_days" in p:
        out["company_extra_days"] = [clean({"from_months": b["from_months"], "to_months": b.get("to_months"),
                                            "days": to_dec128(b["days"])}) for b in p["company_extra_days"]]
    return out


def policy_warnings(db, s, policy: dict, versions: list[dict], on: date) -> list[dict]:
    """R78：公司規定的天數有負數（掛在公司規定上，不能用 OverrideWarning 忽略）。"""
    out = []
    for v in versions:
        for b in v.get("params", {}).get("company_extra_days") or []:
            if to_dec(b["days"]) < 0:
                out.append(W.warning(db, "R78", on, "COMPANY_EXTRA_BELOW_STATUTORY",
                                     subject=("company_policies", policy["entity_id"]),
                                     warned_value={"version": v["version"], "from_months": b["from_months"],
                                                   "days": str(to_dec(b["days"]))}, session=s))
    return out


def establish_policy(db, actor: Actor, body: dict) -> dict:
    actor.require("HR", "EMPLOYER")
    eff, params, subject = D(body["effective_from"]), body["first_version"], body["subject"]
    allowed = {B.EXTRA: {"company_extra_days", "company_extra_eligibility", "company_extra_year_end_treatment",
                         "company_extra_deferrable"}, B.YEAR_DEFAULT: {"company_default_leave_year"}}
    if subject not in allowed or set(params) - allowed[subject]:
        raise RequestInvalid([f"first_version：事項 {subject} 只能有 {sorted(allowed.get(subject, []))}"])

    def tx(s):
        t = actor.tenant_id
        employer = get_current(db, "employers", oid(body["employer_id"]), t, s) if body.get("employer_id") else None
        locks.lock(db, s, t, "EMPLOYER_POLICY", employer["_id"] if employer else t)
        today = clock.today(db, employer, s)
        if subject == B.YEAR_DEFAULT:                                      # R73
            for p in db.company_policies.find({"tenant_id": t, "subject": B.YEAR_DEFAULT, "is_current": True}, session=s):
                same = p.get("employer_id") == (employer or {}).get("_id") and \
                    p.get("leave_type_code") == body.get("leave_type_code")
                if same and (p.get("effective_to") is None or to_date(p["effective_to"]) >= eff):
                    raise Blocked("R73", "YEAR_DEFAULT_OVERLAP", f"和公司規定 {p['entity_id']} 的生效期間重疊")
        event_id = ObjectId()
        pid = insert_versioned(db, s, "company_policies", clean({
            "tenant_id": t, "employer_id": (employer or {}).get("_id"), "leave_type_code": body.get("leave_type_code"),
            "name": body["name"], "subject": subject, "source_note": body.get("source_note"), "effective_from": to_dt(eff),
            "status": scheduler.policy_status({"effective_from": to_dt(eff)}, today)}), event_id=event_id)
        # 公司規定版本的名稱依新增順序 v1、v2……（05_mapping 2.3、D-30）
        db.company_policy_versions.insert_one({
            "tenant_id": t, "policy_id": pid, "version": "v1", "revision": 1, "effective_from": to_dt(eff),
            "params": _params_to_db(params), "recorded_at": now(), "event_id": event_id, "created_at": now()}, session=s)
        record_event(db, s, tenant_id=t, type="EstablishCompanyPolicy", subject=("company_policies", pid), actor=actor.event_actor,
                     effective_from=to_dt(eff), evidence=body.get("evidence"), event_id=event_id)
        policy = db.company_policies.find_one({"entity_id": pid, "is_current": True}, session=s)
        ver = list(db.company_policy_versions.find({"policy_id": pid}, session=s))
        warn = policy_warnings(db, s, policy, ver, today)
        # D-18：影響這個雇主的每一段僱傭關係 → 上鎖、生效日不晚於已給予的取得日的寫一筆佇列
        # 受影響的僱傭關係：全部上鎖，只對已有取得日不早於生效日的那幾段排佇列（05_mapping D-34）
        q = {"tenant_id": t, "is_current": True, "annulled": {"$ne": True}}
        if employer:
            q["employer_id"] = employer["_id"]
        queued = 0
        for emp in db.employments.find(q, session=s):
            locks.lock(db, s, t, "EMPLOYMENT", emp["entity_id"])
            # R76：看生效日與今天較晚的那天（04 D-30）
            if subject == B.YEAR_DEFAULT and emp.get("status") == "Active" and B.agreement_on(db, s, emp, max(eff, today)) is None:
                warn.append(W.warning(db, "R76", today, "DEFAULT_LEAVE_YEAR_CHANGED", subject=("employments", emp["entity_id"]),
                                      warned_value={"policy_id": str(pid), "effective_from": str(eff)}, session=s))
            if db[L.ENT].find_one({"employment_id": emp["entity_id"], "is_current": True, "voided": False,
                                   "origin": B.RULE_GRANT, "acquired_on": {"$gte": to_dt(eff)}}, session=s):
                locks.enqueue(db, s, t, emp["entity_id"], event_id, "EstablishCompanyPolicy")
                queued += 1
        return {"event_id": str(event_id), "policy_id": str(pid), "version": "v1", "revision": 1, "status": policy["status"],
                "warnings": warn, "reassessment_queued": queued}
    return run_in_transaction(db, tx)


# ---- RegisterExistingLeaveEntitlement ----

def backfill(db, actor: Actor, body: dict) -> dict:
    actor.require("HR")
    vf, vt = D(body["valid_from"]), D(body["valid_to"])
    qty, pre = Q(body["quantity"]), Q(body["pre_system_used_quantity"])
    orig_end = D(body.get("registered_original_year_end"))

    def fn(ctx, emp, employer, notice_ids):
        smf = to_date(employer.get("system_managed_from"))
        if smf is None:
            raise Blocked("R97", "INSUFFICIENT_DATA", "雇主沒有登錄開始由系統管理的日子")
        if body["source"] not in (B.STATUTORY, B.COMPANY):
            raise RequestInvalid([f"source：{body['source']} 不是特休的來源"])
        problems = []
        if not to_date(emp["start_date"]) < smf:
            problems.append("到職日要早於雇主開始由系統管理的日子")
        if vt < smf or vt < vf:
            problems.append("可休迄日不早於開始由系統管理的日子、不早於可休起日")
        if qty <= 0 or pre < 0 or pre > qty:
            problems.append("額度要大於 0，開始管理前已休不大於額度")
        if body["origin"] == B.REGISTERED_DEFERRED and (orig_end is None or orig_end >= vf):
            problems.append("補登遞延的要有原年度終結日，而且早於可休起日")
        if problems:
            raise Blocked("R97", "BACKFILL_INVALID", "；".join(problems))
        if body.get("policy_id"):
            get_current(db, "company_policies", oid(body["policy_id"]), ctx.tenant_id, ctx.s)
        event_id = ObjectId()
        ent_id = L.create_entitlement(ctx, {
            "employment_id": emp["entity_id"], "leave_type_code": body["leave_type_code"], "source": body["source"],
            "origin": body["origin"], "unit": body["unit"], "quantity": qty, "pre_system_used_quantity": pre,
            # 補登的取得日是可休起日（04 R97、D-29）
            "acquired_on": vf, "valid_from": vf, "valid_to": vt, "registered_original_year_end": orig_end,
            "policy_id": oid(body["policy_id"]) if body.get("policy_id") else None,
            "basis_rule_versions": [], "no_rule_version": True,
        }, event_id=event_id)
        record_event(db, ctx.s, tenant_id=ctx.tenant_id, type="RegisterExistingLeaveEntitlement", subject=(L.ENT, ent_id),
                     actor=ctx.actor, occurred_at=to_dt(smf), effective_from=to_dt(vf), evidence=body.get("evidence"),
                     event_id=event_id)
        return {"event_id": str(event_id), "entitlement_id": str(ent_id), "status": "Active", "warnings": []}
    return _employment_tx(db, actor, body["employment_id"], fn)
