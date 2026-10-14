"""規則版本（P5）與「當時系統知道的資料」（as_of，03_flows D-10）。"""
from datetime import date, datetime

from app.db import to_dt


def rule(db, rule_id: str, on: date, as_of: datetime | None = None, session=None) -> dict | None:
    """判定日 on 適用的版本；同一版本有多個修訂時取 as_of 當時最新的修訂。沒有 → None（R28 無對應規則版本）。"""
    q = {"rule_id": rule_id, "effective_from": {"$lte": to_dt(on)},
         "$or": [{"effective_to": {"$exists": False}}, {"effective_to": {"$gte": to_dt(on)}}]}
    if as_of:
        q["recorded_at"] = {"$lte": as_of}
    return db.rule_versions.find_one(q, sort=[("effective_from", -1), ("revision", -1)], session=session)


def ref(rv: dict) -> dict:
    """事件、加保待辦、警告引用的規則版本（含修訂）。"""
    return {"rule_id": rv["rule_id"], "version": rv["version"], "revision": rv["revision"]}


def snapshot(db, collection: str, filt: dict, as_of: datetime | None = None, session=None) -> list[dict]:
    """取符合條件的文件。只新增（P2 A）的集合：as_of 為空取目前版本，否則取 as_of 當時各概念的最新版本。"""
    if as_of is None:
        return list(db[collection].find({**filt, "is_current": True}, session=session))
    pipeline = [
        {"$match": {**filt, "recorded_at": {"$lte": as_of}}},
        {"$sort": {"revision": -1}},
        {"$group": {"_id": "$entity_id", "doc": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$doc"}},
    ]
    return list(db[collection].aggregate(pipeline, session=session))
