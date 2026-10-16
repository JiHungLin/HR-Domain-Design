"""寫入的共用做法（05_mapping 第四節）。

- P1：每個有名字的動作寫一筆 events。
- P2 A 只新增：每次寫入新增一份版本文件（entity_id、revision、supersedes、is_current、recorded_at、event_id），
  前一份只把 is_current 改為 false（D-10）。
- P2 B 覆寫＋變更紀錄：直接更新，同時新增 change_log。
- D-06：每個 ref 都檢查存在、屬於呼叫者的客戶、且為目前版本。
"""
from bson import ObjectId

from app.db import now
from app.errors import Forbidden, NotFound

VERSIONED = {"persons", "identity_documents", "employments", "compensations", "work_authorizations",
             "insurance_enrollments", "insured_salaries"}


def clean(d: dict) -> dict:
    """拿掉值為 None 的欄位：集合驗證規則不接受 null（例：ref 必須是 objectId）。"""
    return {k: v for k, v in d.items() if v is not None}


def get_current(db, collection: str, entity_id: ObjectId, tenant_id: ObjectId, session=None) -> dict:
    """依概念的 entity_id 取目前版本（D-10）；非版本集合用 _id。不屬於呼叫者客戶的回 403（D-06）。"""
    key = {"entity_id": entity_id, "is_current": True} if collection in VERSIONED else {"_id": entity_id}
    doc = db[collection].find_one(key, session=session)
    if doc is None:
        raise NotFound(f"{collection} 找不到 {entity_id}")
    if doc.get("tenant_id") != tenant_id:
        raise Forbidden(f"{collection} {entity_id} 不屬於呼叫者的客戶")
    return doc


def get_shared(db, collection: str, _id: ObjectId, session=None) -> dict:
    """全平台共用的參考資料（jurisdictions、social_insurance_schemes…），只能讀。"""
    doc = db[collection].find_one({"_id": _id}, session=session)
    if doc is None:
        raise NotFound(f"{collection} 找不到 {_id}")
    return doc


def record_event(db, session, *, tenant_id, type: str, subject: tuple[str, ObjectId], actor: dict,
                 occurred_at=None, effective_from=None, rule_versions=None, reason=None,
                 derived: bool | None = None, event_id: ObjectId | None = None,
                 evidence: list[dict] | None = None) -> ObjectId:
    eid = event_id or ObjectId()
    ts = now()
    db.events.insert_one(clean({
        "_id": eid, "tenant_id": tenant_id, "type": type,
        "subject": {"collection": subject[0], "id": subject[1]},
        "occurred_at": occurred_at, "recorded_at": ts, "effective_from": effective_from,
        "actor": actor, "rule_versions": rule_versions or None, "reason": reason, "derived": derived,
        "evidence": evidence or None,
        "created_at": ts,
    }), session=session)
    db.outbox.insert_one({"tenant_id": tenant_id, "event_id": eid, "type": type, "created_at": ts}, session=session)
    return eid


def insert_versioned(db, session, collection: str, fields: dict, *, event_id: ObjectId,
                     entity_id: ObjectId | None = None) -> ObjectId:
    """P2 A：建立第一個版本。回傳 entity_id。"""
    ent = entity_id or ObjectId()
    ts = now()
    db[collection].insert_one(clean({
        **fields, "entity_id": ent, "revision": 1, "is_current": True,
        "recorded_at": ts, "event_id": event_id, "created_at": ts,
    }), session=session)
    return ent


def new_version(db, session, collection: str, current: dict, changes: dict, *, event_id: ObjectId) -> dict:
    """P2 A：新增下一個版本，前一份只把 is_current 改為 false，內容不動。"""
    ts = now()
    db[collection].update_one({"_id": current["_id"]}, {"$set": {"is_current": False, "updated_at": ts}}, session=session)
    nxt = {k: v for k, v in current.items() if k not in ("_id", "updated_at")}
    nxt.update(changes)
    nxt.update({"revision": current["revision"] + 1, "supersedes": current["_id"], "is_current": True,
                "recorded_at": ts, "event_id": event_id, "created_at": ts})
    nxt = clean(nxt)
    db[collection].insert_one(nxt, session=session)
    return nxt


def update_with_changelog(db, session, collection: str, doc: dict, changes: dict, *, event_id: ObjectId,
                          actor: dict) -> None:
    """P2 B：直接更新，並新增一筆不可刪的 change_log（個資欄位不存明文，只記欄位名稱，D-08）。"""
    ts = now()
    sets = clean(changes)
    unsets = {k: "" for k, v in changes.items() if v is None}
    update = {"$set": {**sets, "updated_at": ts}}
    if unsets:
        update["$unset"] = unsets
    db[collection].update_one({"_id": doc["_id"]}, update, session=session)
    db.change_log.insert_one(clean({
        "tenant_id": doc["tenant_id"], "collection": collection, "document_id": doc["_id"],
        "fields": sorted(changes), "event_id": event_id, "changed_by": actor.get("user_id"), "changed_at": ts,
        "created_at": ts,
    }), session=session)
