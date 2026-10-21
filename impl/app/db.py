"""MongoDB 連線與多文件交易（PLAN.md D-35：跨集合一致性放 service 層，用多文件交易）。"""
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import lru_cache

from bson import Decimal128, ObjectId
from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from app import config


@lru_cache
def client() -> MongoClient:
    return MongoClient(config.MONGO_URI, tz_aware=True)


def database(name: str | None = None):
    return client()[name or config.DB_NAME]


def run_in_transaction(db, fn):
    """在一個交易中執行 fn(session)；暫時性錯誤（例：R04 鎖衝突）由驅動自動重試。"""
    with client().start_session() as session:
        return session.with_transaction(
            lambda s: fn(s),
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"),
        )


# ---- 型別轉換：日期存成 UTC 午夜（schema.mongo.js 型別慣例）；金額用 Decimal128 ----

def to_dt(d: date | None) -> datetime | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.astimezone(timezone.utc)
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def to_date(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc).date()
    return v


def to_dec128(v) -> Decimal128:
    return Decimal128(Decimal(str(v)))


def to_dec(v) -> Decimal | None:
    if v is None:
        return None
    if isinstance(v, Decimal128):
        return v.to_decimal()
    return Decimal(str(v))


def now() -> datetime:
    return datetime.now(timezone.utc)


def oid(v) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if not ObjectId.is_valid(v):
        from app.errors import NotFound
        raise NotFound(f"不是有效的編號：{v}")
    return ObjectId(v)
