"""同時寫入保護與雇主層級的重新判定佇列（05_mapping D-05、D-18）。"""
from datetime import date

from bson import Int64

from app.db import now, run_in_transaction
from app.leave import clock
from app.leave import engine as E
from app.leave.ledger import Ctx


def lock(db, s, tenant_id, scope: str, key_id) -> None:
    """先更新鎖文件，讓同一段僱傭關係（或同一雇主的公司規定）的兩個交易互相衝突、由驅動重試。"""
    db.leave_locks.update_one({"tenant_id": tenant_id, "scope": scope, "key_id": key_id},
                              {"$inc": {"seq": Int64(1)}}, upsert=True, session=s)


def employer_of(db, s, employment: dict) -> dict:
    return db.employers.find_one({"_id": employment["employer_id"]}, session=s)


def begin(ctx: Ctx, employment: dict) -> list:
    """寫入某段僱傭關係的交易一開始：上鎖，並先處理它還沒處理的佇列項目（X-10）。回傳產生的通知編號。"""
    lock(ctx.db, ctx.s, ctx.tenant_id, "EMPLOYMENT", employment["entity_id"])
    out = []
    for item in list(ctx.db.leave_reassessment_queue.find(
            {"tenant_id": ctx.tenant_id, "employment_id": employment["entity_id"], "processed_at": {"$exists": False}},
            session=ctx.s).sort("enqueued_at", 1)):
        sub = Ctx(ctx.db, ctx.s, ctx.tenant_id, ctx.today, root_event_id=item["root_event_id"])
        cur = ctx.db.employments.find_one({"entity_id": employment["entity_id"], "is_current": True}, session=ctx.s)
        notice = E.Notice(cur["entity_id"])
        ev = E.reassess(sub, cur, employer_of(ctx.db, ctx.s, cur), notice,
                        basis_before={"reason": item["reason"]}, basis_after={"reason": item["reason"]})
        nid = notice.flush(sub, ev)
        if nid:
            out.append(nid)
        ctx.db.leave_reassessment_queue.update_one({"_id": item["_id"]}, {"$set": {"processed_at": now()}}, session=ctx.s)
    return out


def enqueue(db, s, tenant_id, employment_id, root_event_id, reason: str) -> None:
    lock(db, s, tenant_id, "EMPLOYMENT", employment_id)
    db.leave_reassessment_queue.insert_one({"tenant_id": tenant_id, "employment_id": employment_id,
                                            "root_event_id": root_event_id, "reason": reason, "enqueued_at": now(),
                                            "attempts": 0}, session=s)


def drain(db, today: date | None = None) -> int:
    """每段僱傭關係各用一個交易處理佇列；失敗的記失敗次數與錯誤，列入待處理清單（X-13）。"""
    pending = db.leave_reassessment_queue.distinct("employment_id", {"processed_at": {"$exists": False}})
    done = 0
    for employment_id in pending:
        emp = db.employments.find_one({"entity_id": employment_id, "is_current": True})

        def tx(s, emp=emp):
            employer = employer_of(db, s, emp)
            ctx = Ctx(db, s, emp["tenant_id"], today or clock.today(db, employer, s))
            return len(begin(ctx, emp))
        try:
            run_in_transaction(db, tx)
            done += 1
        except Exception as e:  # noqa: BLE001 — 記下來交給人看，不讓一段卡住其他段
            db.leave_reassessment_queue.update_many(
                {"employment_id": employment_id, "processed_at": {"$exists": False}},
                {"$inc": {"attempts": 1}, "$set": {"last_error": f"{type(e).__name__}: {e}"}})
    return done
