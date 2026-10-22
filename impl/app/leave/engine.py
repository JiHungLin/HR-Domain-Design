"""特休的系統事件：GrantLeaveEntitlement、CloseLeaveYear、RejudgeLeaveYearEnd、ReassessLeaveEntitlements、
EndLeaveEntitlementsWithEmployment，以及它們產生的 NotifyLeaveReassessment（03_flows 事件表；04 R65～R96）。

都在呼叫者的交易（ctx.s）中執行；呼叫者已經先拿到那段僱傭關係的 leave_locks（05_mapping D-05，app/leave/locks.py）。
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from bson import ObjectId

from app.db import now, to_date, to_dec, to_dt
from app.leave import basis as B
from app.leave import dates
from app.leave import ledger as L
from app.leave.ledger import FORFEITED, WAGES, Ctx
from app.rules.applicability import value_on
from app.store import record_event

YEAR_END, TERMINATION = "CONVERSION_REASON.YEAR_END", "CONVERSION_REASON.TERMINATION"
BASIS_CORRECTED = "CORRECTION_CAUSE.BASIS_CORRECTED"
DEFERRAL_CHANGED = "CORRECTION_CAUSE.DEFERRAL_CHANGED"
LATE_LEAVE_RECORDED = "CORRECTION_CAUSE.LATE_LEAVE_RECORDED"
LATE_TERMINATION_KNOWN = "CORRECTION_CAUSE.LATE_TERMINATION_KNOWN"


# ---- NotifyLeaveReassessment（建議層，不可作廢，05_mapping D-08） ----

@dataclass
class Notice:
    employment_id: ObjectId
    changed: list = field(default_factory=list)
    added_ids: list = field(default_factory=list)
    voided_ids: list = field(default_factory=list)
    conversion_ids: list = field(default_factory=list)
    provisional_conversion_ids: list = field(default_factory=list)
    action_items: list = field(default_factory=list)

    def empty(self) -> bool:
        return not (self.changed or self.added_ids or self.voided_ids or self.conversion_ids or self.action_items)

    def conv(self, ids_and_status: list[tuple]) -> None:
        for cid, status in ids_and_status:
            self.conversion_ids.append(cid)
            if status == "Provisional":
                self.provisional_conversion_ids.append(cid)

    def act(self, kind: str, ent_id, detail: str) -> None:
        self.action_items.append({"kind": f"NOTICE_ACTION.{kind}", "entitlement_id": ent_id, "detail": detail})

    def flush(self, ctx: Ctx, trigger_event_id) -> ObjectId | None:
        if self.empty():
            return None
        ts = now()
        nid = ctx.db.leave_reassessment_notices.insert_one({
            "tenant_id": ctx.tenant_id, "employment_id": self.employment_id, "trigger_event_id": trigger_event_id,
            "root_event_id": ctx.root_event_id or trigger_event_id,
            "changed": self.changed, "added_ids": self.added_ids, "voided_ids": self.voided_ids,
            "conversion_ids": self.conversion_ids, "provisional_conversion_ids": self.provisional_conversion_ids,
            "action_items": self.action_items, "notified_to": ["HR", "EMPLOYER"], "notified_at": ts, "created_at": ts,
        }, session=ctx.s).inserted_id
        ctx.db.outbox.insert_one({"tenant_id": ctx.tenant_id, "event_id": trigger_event_id,
                                  "type": "LeaveReassessmentNotified", "notice_id": nid, "created_at": ts}, session=ctx.s)
        return nid


def _snap(ent: dict) -> dict:
    """通知 changed[] 的 before／after：額度、期間、取得日、狀態（05_mapping 1.2）。"""
    return {"quantity": str(to_dec(ent["quantity"])), "acquired_on": str(to_date(ent["acquired_on"])),
            "valid_from": str(to_date(ent["valid_from"])), "valid_to": str(to_date(ent["valid_to"])), "status": ent["status"]}


# ---- 年度終結的處理依據（R79、R89、R90） ----

def year_end_treatment(ctx: Ctx, ent: dict) -> tuple[str, bool, bool, list]:
    """(轉成什麼, 可不可以遞延, 找得到版本, 依據的規則版本)。"""
    r79 = B.rule(ctx.db, "R79", to_date(ent["valid_to"]), ctx.s)
    if ent["source"] == B.STATUTORY:
        return WAGES, True, True, []
    p = r79["params"]
    if p["company_policy_version_at_year_end"] == "AT_GRANT":
        ref = next((r for r in ent.get("basis_rule_versions") or [] if r["kind"] == "COMPANY_POLICY"), None)
        v = ref and ctx.db.company_policy_versions.find_one(
            {"policy_id": ref["policy_id"], "version": ref["version"], "revision": ref["revision"]}, session=ctx.s)
    else:
        v = ent.get("policy_id") and B.policy_version(ctx.db, ctx.s, ent["policy_id"], to_date(ent["valid_to"]))
    if not v:
        return WAGES, False, False, [B.rref(r79)]                # R79 找不到版本 → 資料不足，轉換待確認
    vp = v.get("params", {})
    target = vp.get("company_extra_year_end_treatment", p["company_extra_year_end_treatment"])
    deferrable = vp.get("company_extra_deferrable", p["company_extra_deferrable"])
    return target, deferrable, True, [B.rref(r79), B.pref(v)]


def wage_basis_date(ctx: Ctx, ent: dict) -> date:
    """R89：當期的是這一筆的年度終結日；遞延進來的是原來那一筆的；補登遞延的是登錄的原年度終結日。"""
    if ent["origin"] == B.DEFERRED_IN:
        orig = ctx.db[L.ENT].find_one({"entity_id": ent["deferred_from_id"], "is_current": True}, session=ctx.s)
        return to_date(orig["valid_to"])
    if ent["origin"] == B.REGISTERED_DEFERRED:
        return to_date(ent["registered_original_year_end"])
    return to_date(ent["valid_to"])


def payment_due(ctx: Ctx, employment: dict, base: date) -> tuple[date, dict]:
    """R90：雇主擇一的 payment_deadline_rule；從 base（年度終結日或差額的判定日）算。"""
    r90 = B.rule(ctx.db, "R90", base, ctx.s)
    p = r90["params"]
    st = ctx.db.employer_settings.find_one({"employer_id": employment["employer_id"]}, session=ctx.s) or {}
    # 暫時：依雇主的值取 base 當天有效的那一段（05_mapping 沒寫用哪一天查，signoff.md #8）
    rule_code = value_on(st.get("payment_deadline_rule"), base) or p["payment_deadline_rule"]
    if rule_code == "DAYS_AFTER_YEAR_END":
        return base + dates.DAY * p["payment_days_after_year_end"], B.rref(r90)   # 從隔天算第 1 日（EQ-014）
    day = value_on(st.get("wage_payment_day"), base) or p["wage_payment_day"]
    lag = value_on(st.get("wage_payment_lag_months"), base)
    lag = p["wage_payment_lag_months"] if lag is None else lag
    due = dates.months_later_on_day(base, lag, day)
    if due <= base:
        due = dates.months_later_on_day(base, lag + 1, day)
    return due, B.rref(r90)


def _employment(ctx: Ctx, employment_id) -> dict:
    return ctx.db.employments.find_one({"entity_id": employment_id, "is_current": True}, session=ctx.s)


# ---- 轉換的分配（R86、R92、R93） ----

def settle(ctx: Ctx, ent: dict, target_qty: Decimal, target: str, *, event_id, rule_refs: list, cause: str | None = None,
           late=False, version_found=True, judgment_event_id=None) -> list[tuple]:
    """這一筆的轉換合計調整成 target_qty：待確認的先取代，已判定的不改，差額另記一筆（R86、R92）。回傳 [(轉換編號, 狀態)]。"""
    convs = L.conversions(ctx, ent["entity_id"])
    provisional = [c for c in convs if c["status"] == "Provisional"]
    determined = [c for c in convs if c["status"] == "Determined"]
    diff = target_qty - sum((to_dec(c["quantity"]) for c in determined), Decimal(0))
    out, new_id = [], None
    if diff != 0:
        r93 = B.rule(ctx.db, "R93", ctx.today, ctx.s)
        if cause is None:                                       # 年度終結（R93 決策表）
            status = "Provisional" if (late or target == FORFEITED or not version_found) else "Determined"
        elif cause == LATE_TERMINATION_KNOWN:
            status = "Provisional"
        else:                                                   # 更正差額：正數轉為工資直接判定，其他待確認
            status = "Determined" if (diff > 0 and target == WAGES) else "Provisional"
        emp = _employment(ctx, ent["employment_id"])
        fields = {"employment_id": ent["employment_id"], "entitlement_id": ent["entity_id"], "reason": YEAR_END,
                  "target": target, "quantity": diff, "determined_on": ctx.today, "status": status,
                  "correction_cause": cause}
        refs = list(rule_refs) + [B.rref(B.rule(ctx.db, "R86", ctx.today, ctx.s)), B.rref(r93)]
        if target == WAGES:
            fields["wage_basis_date"] = wage_basis_date(ctx, ent)
            r89 = B.rule(ctx.db, "R89", ctx.today, ctx.s)
            refs.append(B.rref(r89))
            if diff > 0:                                        # 失效、負數差額沒有發給期限（R90）
                base = to_date(ent["valid_to"]) if cause is None else ctx.today
                fields["payment_due_on"], r90 = payment_due(ctx, emp, base)
                refs.append(r90)
        if cause is not None:
            if determined:
                fields["corrects_conversion_id"] = determined[0]["entity_id"]
            elif judgment_event_id:
                fields["corrects_judgment_event_id"] = judgment_event_id
        fields["basis_rule_versions"] = refs
        new_id = L.create_conversion(ctx, fields, event_id=event_id)
        out.append((new_id, status))
    for c in provisional:
        L.change_conversion(ctx, c, {"status": "Discarded", **({"discarded_by_id": new_id} if new_id else {})},
                            event_id=event_id)
    return out


def _judgment_event(ctx: Ctx, ent_id):
    e = ctx.db.events.find_one({"type": {"$in": ["CloseLeaveYear", "RejudgeLeaveYearEnd"]}, "subject.id": ent_id},
                               sort=[("recorded_at", 1)], session=ctx.s)
    return e["_id"] if e else None


# ---- GrantLeaveEntitlement ----

def grant(ctx: Ctx, item: dict, *, event_type="GrantLeaveEntitlement", event_id=None) -> ObjectId:
    """依規則給予一筆（R65～R70、R77）；event_type 為 ReassessLeaveEntitlements 時是重新判定多出來的那一筆。"""
    own_event = event_id is None
    event_id = event_id or ObjectId()
    ent_id = L.create_entitlement(ctx, item, event_id=event_id)
    if own_event:
        record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type=event_type, subject=(L.ENT, ent_id), actor=ctx.actor,
                     occurred_at=to_dt(item["acquired_on"]), effective_from=to_dt(item["valid_from"]),
                     rule_versions=item["basis_rule_versions"], derived=True, event_id=event_id)
    return ent_id


# ---- CloseLeaveYear ----

def close(ctx: Ctx, ent: dict, notice: Notice) -> ObjectId:
    """可休迄日過完後的年度終結（R85、R86、R88～R90、R93）。判定當時已知的已休記在事件上（03_flows D-15）。"""
    valid_to = to_date(ent["valid_to"])
    late = ctx.today > valid_to + dates.DAY                   # R93：補做的年度終結（04 D-20）
    event_id = ObjectId()
    used = L.used(ctx, ent)
    unused = to_dec(ent["quantity"]) - used
    target, deferrable, found, refs = year_end_treatment(ctx, ent)
    agreement = L.deferral(ctx, ent["entity_id"], ("Agreed",))
    deferred, din_id, ref = Decimal(0), None, None
    if agreement:
        ref = {"id": agreement["entity_id"], "version_event_id": agreement["event_id"]}
        if not deferrable:                                       # R79 決策表：那一版不可以遞延 → 協商失效
            L.change_deferral(ctx, agreement, {"status": "Lapsed"}, event_id=event_id)
        else:
            agreed = to_dec(agreement["deferred_quantity"])
            deferred = min(agreed, max(unused, Decimal(0)))       # R86：協商額度與未休兩者較小的
            if agreed > unused:
                notice.act("DEFERRAL_OVER_UNUSED", ent["entity_id"], f"協商遞延 {agreed}，年度終結時未休 {unused}")
            if deferred > 0:
                din_id = _create_deferred_in(ctx, ent, agreement, deferred, event_id)
            L.change_deferral(ctx, agreement, {"status": "Applied"}, event_id=event_id)
    convs = settle(ctx, ent, max(unused - deferred, Decimal(0)), target, event_id=event_id, rule_refs=refs,
                   late=late, version_found=found)
    if late:                                                    # 補做的：轉換待確認，列入通知
        notice.conv(convs)
    L.change_entitlement(ctx, ent, {"status": "YearEnded"}, event_id=event_id)
    rv = [B.rref(B.rule(ctx.db, r, valid_to, ctx.s)) for r in ("R85", "R86", "R89", "R90", "R93")] + refs
    record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type="CloseLeaveYear", subject=(L.ENT, ent["entity_id"]),
                 actor=ctx.actor, occurred_at=to_dt(valid_to), effective_from=to_dt(valid_to + dates.DAY),
                 rule_versions=rv, derived=True, event_id=event_id,
                 payload={"year_end": _year_end_payload(ent, used, unused, ref, deferred, din_id, convs, late)})
    L.check_conservation(ctx, ent["entity_id"])
    return event_id


def _year_end_payload(ent, used, unused, ref, deferred, din_id, convs, late) -> dict:
    out = {"entitlement_id": ent["entity_id"], "used_quantity_known": str(used), "unused_quantity": str(unused),
           "conversion_ids": [c for c, _ in convs], "late": late}
    if ref:
        out |= {"deferral_agreement_ref": ref, "deferred_in_quantity": str(deferred)}
    if din_id:
        out["deferred_in_entitlement_id"] = din_id
    return out


def _create_deferred_in(ctx: Ctx, orig: dict, agreement: dict, qty: Decimal, event_id) -> ObjectId:
    """R87：來源、單位、公司規定與依據的規則版本沿用原來那一筆。"""
    vf, vt = B.deferred_in_period(ctx.db, ctx.s, orig)
    r87 = B.rule(ctx.db, "R87", vf, ctx.s)
    return L.create_entitlement(ctx, {
        "employment_id": orig["employment_id"], "leave_type_code": orig["leave_type_code"], "source": orig["source"],
        "origin": B.DEFERRED_IN, "unit": orig["unit"], "policy_id": orig.get("policy_id"),
        # 暫時：遞延進來那一筆的取得日 04 沒有寫，用可休起日（signoff.md #9）
        "acquired_on": vf, "valid_from": vf, "valid_to": vt, "quantity": qty,
        "leave_year_basis": orig.get("leave_year_basis"),
        "applied_year_agreement_id": orig.get("applied_year_agreement_id"),
        "applied_year_default_policy_id": orig.get("applied_year_default_policy_id"),
        "basis_rule_versions": list(orig.get("basis_rule_versions") or []) + [B.rref(r87)],
        "no_rule_version": orig.get("no_rule_version"),
        "deferred_from_id": orig["entity_id"], "deferred_under_id": agreement["entity_id"],
    }, event_id=event_id)


# ---- RejudgeLeaveYearEnd ----

def rejudge(ctx: Ctx, ent: dict, cause: str, notice: Notice, *, event_id=None) -> ObjectId:
    """年度終結判定用到的資料之後改變（R92、R93、R96、04 D-25）。"""
    event_id = event_id or ObjectId()
    used = L.used(ctx, ent)
    unused = to_dec(ent["quantity"]) - used
    target, deferrable, found, refs = year_end_treatment(ctx, ent)
    agreement = L.deferral(ctx, ent["entity_id"])
    deferred, ref = Decimal(0), None
    if agreement:
        ref = {"id": agreement["entity_id"], "version_event_id": agreement["event_id"]}
        if deferrable:
            deferred = min(to_dec(agreement["deferred_quantity"]), max(unused, Decimal(0)))
            if agreement["status"] == "Agreed":
                L.change_deferral(ctx, agreement, {"status": "Applied"}, event_id=event_id)
    din = L.deferred_in_of(ctx, ent)
    din_id = din["entity_id"] if din else None
    # 照設計：遞延進來那一筆立刻可以休，扣回的負數差額要人確認；確認前天數與工資同時在（signoff.md #16）
    if deferred > 0 and din is None:
        din_id = _create_deferred_in(ctx, ent, agreement, deferred, event_id)
        notice.added_ids.append(din_id)
    elif din is not None and deferred == 0:
        _void(ctx, din, event_id, notice, cause)
        din_id = None
    elif din is not None and to_dec(din["quantity"]) != deferred:
        before = _snap(din)
        din = L.change_entitlement(ctx, din, {"quantity": deferred}, event_id=event_id)
        notice.changed.append({"entitlement_id": din["entity_id"], "before": before, "after": _snap(din)})
        if din["status"] == "YearEnded":
            rejudge(ctx, din, cause, notice)
    convs = settle(ctx, ent, max(unused - deferred, Decimal(0)), target, event_id=event_id, rule_refs=refs, cause=cause,
                   version_found=found, judgment_event_id=_judgment_event(ctx, ent["entity_id"]))
    notice.conv(convs)
    _conversion_dates_changed(ctx, ent, notice)
    if unused < 0:
        notice.act("USED_OVER_QUANTITY", ent["entity_id"], f"已休 {used} 大於額度 {to_dec(ent['quantity'])}")
    valid_to = to_date(ent["valid_to"])
    record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type="RejudgeLeaveYearEnd", subject=(L.ENT, ent["entity_id"]),
                 actor=ctx.actor, occurred_at=to_dt(valid_to), effective_from=to_dt(valid_to + dates.DAY),
                 rule_versions=[B.rref(B.rule(ctx.db, r, ctx.today, ctx.s)) for r in ("R92", "R93")] + refs,
                 derived=True, event_id=event_id, reason=cause,
                 payload={"year_end": _year_end_payload(ent, used, unused, ref, deferred, din_id, convs, False)})
    L.check_conservation(ctx, ent["entity_id"])
    return event_id


def _conversion_dates_changed(ctx: Ctx, ent: dict, notice: Notice) -> None:
    """04 D-25、R96：已判定轉換的工資計算基準日或發給期限依新依據不同 → 不改轉換，列入通知（原 → 新）。"""
    emp = _employment(ctx, ent["employment_id"])
    for c in L.conversions(ctx, ent["entity_id"]):
        if c["status"] != "Determined" or c["target"] != WAGES or c.get("correction_cause"):
            continue
        new_basis = wage_basis_date(ctx, ent)
        new_due = payment_due(ctx, emp, to_date(ent["valid_to"]))[0] if c.get("payment_due_on") else None
        old_basis, old_due = to_date(c.get("wage_basis_date")), to_date(c.get("payment_due_on"))
        if (new_basis, new_due) != (old_basis, old_due):
            notice.act("CONVERSION_DATES_CHANGED", ent["entity_id"],
                       f"轉換 {c['entity_id']}：工資計算基準日 {old_basis} → {new_basis}；發給期限 {old_due} → {new_due}")


def _void(ctx: Ctx, ent: dict, event_id, notice: Notice, cause: str) -> None:
    """作廢一筆；已年度終結的，已做的轉換各記負數差額（待確認）；遞延進來的那一筆跟著作廢。"""
    if ent["status"] == "YearEnded":
        target = WAGES
        for c in L.conversions(ctx, ent["entity_id"]):
            target = c["target"]
        notice.conv(settle(ctx, ent, Decimal(0), target, event_id=event_id, rule_refs=[], cause=cause,
                           judgment_event_id=_judgment_event(ctx, ent["entity_id"])))
    din = L.deferred_in_of(ctx, ent)
    if din is not None:
        _void(ctx, din, event_id, notice, cause)
    agreement = L.deferral(ctx, ent["entity_id"])
    if agreement:
        L.change_deferral(ctx, agreement, {"status": "Lapsed"}, event_id=event_id)
        notice.act("REDEFER", ent["entity_id"], f"遞延協商 {agreement['entity_id']} 已失效")
    u = L.used(ctx, ent)
    if u > 0:
        notice.act("USED_ON_VOIDED", ent["entity_id"], f"作廢的那一筆上已休 {u}")
    if ent.get("notified_on"):
        notice.act("RENOTIFY", ent["entity_id"], f"作廢的那一筆的告知日 {to_date(ent['notified_on'])}")
    L.change_entitlement(ctx, ent, {"status": "Voided"}, event_id=event_id)
    notice.voided_ids.append(ent["entity_id"])


# ---- 排程與連鎖共用：補上到今天應發生而還沒發生的 ----

def catch_up(ctx: Ctx, employment: dict, employer: dict, notice: Notice) -> list:
    """GrantLeaveEntitlement 與 CloseLeaveYear：不靠游標，每次找「到今天應發生而還沒發生」的（05_mapping X-04）。
    回傳寫入的事件編號。"""
    events = []
    if employment.get("annulled"):
        return events
    have = {(e["source"], e.get("policy_id"), e.get("period_sequence"))
            for e in L.entitlements(ctx, employment["entity_id"], include_voided=False) if e["origin"] == B.RULE_GRANT}
    for item in B.expected(ctx.db, ctx.s, employment, employer, ctx.today).items:
        if (item["source"], item["policy_id"], item["period_sequence"]) not in have:
            grant(ctx, {**item, "employment_id": employment["entity_id"]})
    ended = to_date(employment.get("ended_on"))
    for ent in L.entitlements(ctx, employment["entity_id"], include_voided=False):
        vt = to_date(ent["valid_to"])
        if ent["status"] == "Active" and vt < ctx.today and (ended is None or ended >= vt):   # R85：結束日等於年度終結日 → 年度終結
            events.append(close(ctx, ent, notice))
    return events


# ---- EndLeaveEntitlementsWithEmployment ----

def end_with_employment(ctx: Ctx, employment: dict, notice: Notice) -> ObjectId:
    """僱傭關係結束（R85、R95；03_flows D-05）。

    暫時：③ 事件表的 NotifyLeaveReassessment 觸發來源沒有這個事件，⑤ UC-09 例外卻從通知取待確認的轉換；
    這裡改到東西就產生通知（signoff.md #17）。"""
    event_id = ObjectId()
    ended = to_date(employment["ended_on"])
    touched = []
    for ent in L.entitlements(ctx, employment["entity_id"], include_voided=False):
        acq, vt = to_date(ent["acquired_on"]), to_date(ent["valid_to"])
        if ent["status"] not in ("Active", "YearEnded") or vt <= ended:
            continue
        if acq > ended:                                            # 從未取得（R95）
            if ent["status"] == "Active":
                _void(ctx, ent, event_id, notice, LATE_TERMINATION_KNOWN)
                touched.append(ent["entity_id"])
            continue
        before = _snap(ent)
        if ent["status"] == "YearEnded":                           # 年度終結判定之後才得知（R95）
            target = next((c["target"] for c in L.conversions(ctx, ent["entity_id"])), WAGES)
            notice.conv(settle(ctx, ent, Decimal(0), target, event_id=event_id, rule_refs=[],
                               cause=LATE_TERMINATION_KNOWN, judgment_event_id=_judgment_event(ctx, ent["entity_id"])))
            din = L.deferred_in_of(ctx, ent)
            if din is not None:
                _void(ctx, din, event_id, notice, LATE_TERMINATION_KNOWN)
        agreement = L.deferral(ctx, ent["entity_id"])
        if agreement:
            L.change_deferral(ctx, agreement, {"status": "Lapsed"}, event_id=event_id)
        cur = L.change_entitlement(ctx, ent, {"status": "EndedWithEmployment"}, event_id=event_id)
        notice.changed.append({"entitlement_id": ent["entity_id"], "before": before, "after": _snap(cur)})
        touched.append(ent["entity_id"])
    record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type="EndLeaveEntitlementsWithEmployment",
                 subject=("employments", employment["entity_id"]), actor=ctx.actor, occurred_at=to_dt(ended),
                 effective_from=to_dt(ended + dates.DAY),
                 rule_versions=[B.rref(B.rule(ctx.db, r, ended, ctx.s)) for r in ("R85", "R95")], derived=True,
                 event_id=event_id)
    for t in touched:
        L.check_conservation(ctx, t)
    return event_id


# ---- ReassessLeaveEntitlements ----

def _overlap(a: dict, b: dict) -> bool:
    return to_date(a["valid_from"]) <= b["valid_to"] and b["valid_from"] <= to_date(a["valid_to"])


def _voided_by_late_termination(ctx: Ctx, ent: dict) -> bool:
    e = ctx.db.events.find_one({"_id": ent["event_id"]}, session=ctx.s)
    return bool(e and e["type"] == "EndLeaveEntitlementsWithEmployment")


def reassess(ctx: Ctx, employment: dict, employer: dict, notice: Notice, *, basis_before: dict, basis_after: dict) -> ObjectId:
    """依更正後的依據重算到今天為止已取得的每一期，和既有依規則給予的逐筆對應（R91；03_flows D-04；04 D-15、D-21）。"""
    event_id = ObjectId()
    existing = [e for e in L.entitlements(ctx, employment["entity_id"])
                if e["origin"] == B.RULE_GRANT and (e["status"] != "Voided" or _voided_by_late_termination(ctx, e))]

    def version_for(source, policy_id, seq, acq):            # 05_mapping D-20：取得日沒變的沿用給予時記的版本
        for e in existing:
            if (e["source"], e.get("policy_id"), e.get("period_sequence")) == (source, policy_id, seq) \
                    and to_date(e["acquired_on"]) == acq:
                ref = next((r for r in e["basis_rule_versions"] if r["kind"] == "COMPANY_POLICY"), None)
                if ref:
                    return ctx.db.company_policy_versions.find_one(
                        {"policy_id": ref["policy_id"], "version": ref["version"], "revision": ref["revision"]}, session=ctx.s)
        return None

    exp = B.expected(ctx.db, ctx.s, employment, employer, ctx.today, version_for=version_for).items
    matched, voided, added, restored, to_rejudge, to_close = [], [], [], [], [], []
    used_new = set()
    for e in existing:
        idx = next((i for i, n in enumerate(exp) if i not in used_new
                    and (n["source"], n["policy_id"], n["period_sequence"]) == (e["source"], e.get("policy_id"), e.get("period_sequence"))
                    and _overlap(e, n)), None)
        if idx is None:
            if e["status"] != "Voided":
                _void(ctx, e, event_id, notice, BASIS_CORRECTED)
                voided.append(e["entity_id"])
            continue
        used_new.add(idx)
        new = exp[idx]
        keys = ("acquired_on", "valid_from", "valid_to", "quantity", "seniority_tier", "basis_seniority",
                "basis_start_date", "leave_year_basis", "applied_year_agreement_id", "applied_year_default_policy_id",
                "basis_rule_versions")
        changes = {}
        for k in keys:
            old = e.get(k)
            old = to_date(old) if k in ("acquired_on", "valid_from", "valid_to", "basis_start_date") else \
                (to_dec(old) if k == "quantity" else old)
            if old != new.get(k):
                changes[k] = new.get(k)
        status = e["status"]
        ended = to_date(employment.get("ended_on"))
        if status == "Voided":                                   # 結束被註銷或延後：恢復（04 D-21）
            changes["status"], status = "Active", "Active"
            restored.append(e["entity_id"])
        elif status == "EndedWithEmployment" and (ended is None or ended >= new["valid_to"]):
            changes["status"], status = "Active", "Active"
        elif status == "YearEnded" and new["valid_to"] >= ctx.today:   # 可休迄日還沒到：回到可休，已做的轉換記負數差額
            target = next((c["target"] for c in L.conversions(ctx, e["entity_id"])), WAGES)
            notice.conv(settle(ctx, e, Decimal(0), target, event_id=event_id, rule_refs=[], cause=BASIS_CORRECTED,
                               judgment_event_id=_judgment_event(ctx, e["entity_id"])))
            din = L.deferred_in_of(ctx, e)
            if din is not None:
                _void(ctx, din, event_id, notice, BASIS_CORRECTED)
            agreement = L.deferral(ctx, e["entity_id"], ("Applied",))
            if agreement:
                L.change_deferral(ctx, agreement, {"status": "Agreed"}, event_id=event_id)
            changes["status"], status = "Active", "Active"
        if not changes:
            continue
        before = _snap(e)
        cur = L.change_entitlement(ctx, e, changes, event_id=event_id)
        notice.changed.append({"entitlement_id": e["entity_id"], "before": before, "after": _snap(cur)})
        matched.append({"before_id": e["entity_id"], "after_id": e["entity_id"]})
        _changed_items(ctx, e, cur, notice)
        if status == "YearEnded":
            to_rejudge.append(e["entity_id"])
        elif status == "Active" and new["valid_to"] < ctx.today:
            to_close.append(e["entity_id"])
        _follow_deferred_in(ctx, cur, event_id, notice)
    for i, n in enumerate(exp):
        if i in used_new:
            continue
        nid = grant(ctx, {**n, "employment_id": employment["entity_id"]}, event_id=event_id)
        added.append(nid)
        notice.added_ids.append(nid)
        if n["valid_to"] < ctx.today:
            to_close.append(nid)
    rv = [B.rref(B.rule(ctx.db, "R91", ctx.today, ctx.s))]
    record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type="ReassessLeaveEntitlements",
                 subject=("employments", employment["entity_id"]), actor=ctx.actor, rule_versions=rv, derived=True,
                 event_id=event_id, payload={"reassessment": {
                     "basis_before": basis_before, "basis_after": basis_after, "matched": matched,
                     "voided_ids": voided, "added_ids": added, "restored_ids": restored}})
    for ent_id in to_rejudge:
        rejudge(ctx, L.entitlement(ctx, ent_id), BASIS_CORRECTED, notice)
    for ent_id in to_close:                                   # 迄日已過的：立刻補做年度終結，轉換待確認（R93）
        close(ctx, L.entitlement(ctx, ent_id), notice)
    for e in existing:
        L.check_conservation(ctx, e["entity_id"])
    return event_id


def _changed_items(ctx: Ctx, before: dict, after: dict, notice: Notice) -> None:
    """R96、R81：就地更正後要人處理的事。"""
    q = to_dec(after["quantity"])
    u = L.used(ctx, after)
    if u > q:
        notice.act("USED_OVER_QUANTITY", after["entity_id"], f"已休 {u} 大於更正後的額度 {q}")
    if after.get("notified_on") and to_date(after["notified_on"]) < to_date(after["acquired_on"]):
        notice.act("NOTICE_BEFORE_ACQUIRED", after["entity_id"],
                   f"告知日 {to_date(after['notified_on'])} 早於更正後的取得日 {to_date(after['acquired_on'])}")
    # 暫時：就地更正後期間或取得日改變、上面有已休的，NOTICE_ACTION 沒有對應的代碼，只列在 changed[]（signoff.md #10）


def _follow_deferred_in(ctx: Ctx, orig: dict, event_id, notice: Notice) -> None:
    """遞延進來的那一筆跟著原來那一筆（R91：期間依 R87 重算）。"""
    din = L.deferred_in_of(ctx, orig)
    if din is None:
        return
    vf, vt = B.deferred_in_period(ctx.db, ctx.s, orig)
    if (to_date(din["valid_from"]), to_date(din["valid_to"])) != (vf, vt):
        before = _snap(din)
        cur = L.change_entitlement(ctx, din, {"acquired_on": vf, "valid_from": vf, "valid_to": vt}, event_id=event_id)
        notice.changed.append({"entitlement_id": din["entity_id"], "before": before, "after": _snap(cur)})
