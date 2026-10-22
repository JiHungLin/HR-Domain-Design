"""每日排程（05_mapping D-03）：給予、年度終結、約定開始適用、公司規定生效與廢止、到了的結束日（D-33）。

不靠「執行到哪一天」的游標：每次對每段僱傭關係找出到今天應發生而還沒發生的，補上（X-04）。
用法：uv run python scripts/run_daily.py
"""
from datetime import date

from bson import ObjectId

from app.db import now, run_in_transaction, to_date, to_dt
from app.leave import clock, locks
from app.leave import engine as E
from app.leave.ledger import SYSTEM, Ctx
from app.store import new_version, record_event, update_with_changelog


def agreement_status(a: dict, others: list[dict], today: date) -> str:
    """LeaveYearAgreement 的狀態（快取）：依適用起日、終止日與同一段的較新約定推出。"""
    if a.get("ended_from") is not None or a["status"] == "Ended":
        return "Ended"
    if to_date(a["effective_from"]) > today:
        return "Scheduled"
    later = [o for o in others if o["_id"] != a["_id"] and o.get("ended_from") is None
             and to_date(a["effective_from"]) < to_date(o["effective_from"]) <= today]
    return "Superseded" if later else "Effective"


def refresh_agreements(ctx: Ctx, employment_id) -> None:
    """ActivateLeaveYearAgreement：Scheduled → Effective；前一筆 Effective → Superseded（P2 B）。"""
    agreements = list(ctx.db.leave_year_agreements.find({"tenant_id": ctx.tenant_id, "employment_id": employment_id},
                                                        session=ctx.s))
    for a in agreements:
        st = agreement_status(a, agreements, ctx.today)
        if st == a["status"]:
            continue
        event_id = ObjectId()
        if a["status"] == "Scheduled" and st in ("Effective", "Superseded"):
            record_event(ctx.db, ctx.s, tenant_id=ctx.tenant_id, type="ActivateLeaveYearAgreement",
                         subject=("leave_year_agreements", a["_id"]), actor=SYSTEM, effective_from=a["effective_from"],
                         derived=True, event_id=event_id)
        update_with_changelog(ctx.db, ctx.s, "leave_year_agreements", a, {"status": st}, event_id=event_id, actor=SYSTEM)


def refresh_policies(db, s, tenant_id, employer_id, today: date) -> None:
    """ActivateCompanyPolicy、ExpireCompanyPolicy（P2 A：新版本）。"""
    from app.store import new_version
    for p in db.company_policies.find({"tenant_id": tenant_id, "employer_id": employer_id, "is_current": True}, session=s):
        st = policy_status(p, today)
        if st == p["status"]:
            continue
        typ = "ActivateCompanyPolicy" if st == "Effective" else "ExpireCompanyPolicy"
        eff = p["effective_from"] if st == "Effective" else to_dt(to_date(p["effective_to"]))
        event_id = record_event(db, s, tenant_id=tenant_id, type=typ, subject=("company_policies", p["entity_id"]),
                                actor=SYSTEM, effective_from=eff, derived=True)
        new_version(db, s, "company_policies", p, {"status": st}, event_id=event_id)


def policy_status(p: dict, today: date) -> str:
    if p.get("effective_to") is not None and to_date(p["effective_to"]) < today:
        return "Repealed"
    return "Scheduled" if to_date(p["effective_from"]) > today else "Effective"


def end_employment(ctx: Ctx, emp: dict, fixture_event_id, out: list) -> list:
    """一般離職的結束日到了（[靜態替代]，05_mapping D-33）：employments.status 改為 Ended，EndLeaveEntitlementsWithEmployment。"""
    cur = new_version(ctx.db, ctx.s, "employments", emp, {"status": "Ended"}, event_id=fixture_event_id)
    ctx.root_event_id = fixture_event_id
    notice = E.Notice(emp["entity_id"])
    end_event = E.end_with_employment(ctx, cur, notice)
    nid = notice.flush(ctx, end_event)
    return out + ([nid] if nid else [])


def _due_ending(ctx: Ctx, emp: dict, out: list) -> tuple[dict, list]:
    """載入時結束日還在未來、今天已經到了的（05_mapping D-33）。"""
    ended = to_date(emp.get("ended_on"))
    if emp["status"] != "Active" or ended is None or ended > ctx.today:
        return emp, out
    ev = ctx.db.events.find_one({"type": "LoadEmploymentEndingFixture", "subject.id": emp["entity_id"]},
                                sort=[("recorded_at", -1)], session=ctx.s)
    if ev is None:                       # 結束日不是固定資料載入的（hire-employee 的 RecordEarlyDeparture 已改狀態）
        return emp, out
    out = end_employment(ctx, emp, ev["_id"], out)
    return ctx.db.employments.find_one({"entity_id": emp["entity_id"], "is_current": True}, session=ctx.s), out


def process_employment(db, employment_id, today: date | None = None) -> list:
    """一段僱傭關係一個交易：上鎖、先清佇列、約定狀態、補給予與年度終結。回傳產生的通知編號。"""
    def tx(s):
        emp = db.employments.find_one({"entity_id": employment_id, "is_current": True}, session=s)
        employer = locks.employer_of(db, s, emp)
        ctx = Ctx(db, s, emp["tenant_id"], today or clock.today(db, employer, s))
        out = locks.begin(ctx, emp)
        emp, out = _due_ending(ctx, emp, out)
        refresh_agreements(ctx, employment_id)
        notice = E.Notice(employment_id)
        events = E.catch_up(ctx, emp, employer, notice)
        if events:                       # 年度終結遇到協商遞延額度超過未休、補做的待確認轉換（03_flows 事件表）
            nid = notice.flush(ctx, events[-1])
            out += [nid] if nid else []
        return out
    return run_in_transaction(db, tx)


def run_daily(db, today: date | None = None) -> dict:
    started = now()
    locks.drain(db, today)
    processed, errors = 0, []
    for employer in db.employers.find():
        def ptx(s, employer=employer):
            locks.lock(db, s, employer["tenant_id"], "EMPLOYER_POLICY", employer["_id"])
            refresh_policies(db, s, employer["tenant_id"], employer["_id"], today or clock.today(db, employer, s))
        run_in_transaction(db, ptx)
        for emp in db.employments.find({"employer_id": employer["_id"], "is_current": True,
                                        "annulled": {"$ne": True}}, {"entity_id": 1}):
            try:
                process_employment(db, emp["entity_id"], today)
                processed += 1
            except Exception as e:  # noqa: BLE001 — 記在執行紀錄，其他段照跑
                errors.append(f"{emp['entity_id']}: {type(e).__name__}: {e}")
    db.job_runs.insert_one({"job": "annual-leave-grant daily", "started_at": started, "finished_at": now(),
                            "employments_processed": processed, "errors": errors})
    return {"processed": processed, "errors": errors}
