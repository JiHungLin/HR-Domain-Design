"""annual-leave-grant 在 hire-employee 動作上的處理（app/hooks.py；05_mapping D-04「core 事件的連鎖」）。

在 hire-employee 的交易中執行；hire-employee 的回應格式不變，人資用回應的 event_id 查重新判定的通知。
import 這個模組就會註冊（app/main.py）。
"""
from app import hooks
from app.leave import clock, locks
from app.leave import engine as E
from app.leave.ledger import SYSTEM, Ctx

# 觸發重新判定的僱傭關係欄位（05_mapping「core 事件的連鎖」CorrectRecord 那一列）
REASSESS_FIELDS = {"start_date", "employee_category", "ended_on"}


def _ctx(db, s, event: hooks.HookEvent):
    emp = db.employments.find_one({"entity_id": event.employment_id, "is_current": True}, session=s)
    employer = locks.employer_of(db, s, emp)
    ctx = Ctx(db, s, event.tenant_id, clock.today(db, employer, s), root_event_id=event.event_id, actor=dict(SYSTEM))
    return ctx, emp, employer


def on_started(db, s, event: hooks.HookEvent) -> None:
    """到職日在過去：同一交易補上已到的 GrantLeaveEntitlement 與已過的 CloseLeaveYear（待確認，X-04）。"""
    ctx, emp, employer = _ctx(db, s, event)
    locks.begin(ctx, emp)
    notice = E.Notice(emp["entity_id"])
    events = E.catch_up(ctx, emp, employer, notice)
    if events:
        notice.flush(ctx, events[-1])


def on_corrected(db, s, event: hooks.HookEvent) -> None:
    """CorrectRecord 改到 start_date、employee_category、ended_on → ReassessLeaveEntitlements（ended_on 改早時先停止特休）。"""
    if not REASSESS_FIELDS & set(event.fields):
        return
    ctx, emp, employer = _ctx(db, s, event)
    locks.begin(ctx, emp)
    if "ended_on" in event.fields and emp.get("ended_on"):
        notice = E.Notice(emp["entity_id"])
        notice.flush(ctx, E.end_with_employment(ctx, emp, notice))
    notice = E.Notice(emp["entity_id"])
    ev = E.reassess(ctx, emp, employer, notice, basis_before=event.extra.get("before", {}),
                    basis_after=event.extra.get("after", {}))
    notice.flush(ctx, ev)


def on_ended(db, s, event: hooks.HookEvent) -> None:
    ctx, emp, employer = _ctx(db, s, event)
    locks.begin(ctx, emp)
    notice = E.Notice(emp["entity_id"])
    notice.flush(ctx, E.end_with_employment(ctx, emp, notice))


hooks.register(hooks.EMPLOYMENT_STARTED, on_started)
hooks.register(hooks.EMPLOYMENT_CORRECTED, on_corrected)
hooks.register(hooks.EMPLOYMENT_ENDED, on_ended)
