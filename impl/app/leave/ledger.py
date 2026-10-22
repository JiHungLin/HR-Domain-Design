"""請假權利、轉換、遞延協商的讀寫與推導的數量（02 LeaveEntitlement；04 C01、C02；05_mapping 第四節）。"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from bson import ObjectId

from app.db import now, to_date, to_dec, to_dec128, to_dt
from app.leave import basis as B
from app.rules import versions
from app.store import clean, insert_versioned, new_version

ENT, CONV, DEFERRAL = "leave_entitlements", "leave_conversions", "leave_deferral_agreements"
WAGES, FORFEITED = "CONVERSION_TARGET.WAGES", "CONVERSION_TARGET.FORFEITED"
SYSTEM = {"role": "SYSTEM"}                       # events.actor：系統排程與連鎖（05_mapping 第二節「系統」）

_DATE_FIELDS = ("acquired_on", "valid_from", "valid_to", "basis_start_date", "notified_on", "registered_original_year_end",
                "determined_on", "wage_basis_date", "payment_due_on", "agreed_on")
_QTY_FIELDS = ("quantity", "pre_system_used_quantity", "deferred_quantity")


def to_db(fields: dict) -> dict:
    out = {}
    for k, v in fields.items():
        if k in _DATE_FIELDS and isinstance(v, date):
            v = to_dt(v)
        elif k in _QTY_FIELDS and v is not None and not hasattr(v, "to_decimal"):
            v = to_dec128(v)
        out[k] = v
    return out


@dataclass
class Ctx:
    """一個交易中本切片的處理共用的東西。"""
    db: object
    s: object
    tenant_id: ObjectId
    today: date
    root_event_id: ObjectId | None = None
    actor: dict = field(default_factory=lambda: dict(SYSTEM))
    as_of: datetime | None = None          # 查詢「當時系統知道的」（05_mapping D-16）；寫入時一律為空


# ---- 讀取（as_of 有值時取那個時間以前登錄的最新版本，P2 A） ----

def _find(ctx: Ctx, coll: str, filt: dict) -> list[dict]:
    docs = versions.snapshot(ctx.db, coll, filt, ctx.as_of, session=ctx.s)
    return sorted(docs, key=lambda d: (d.get("acquired_on") or d.get("created_at"), d.get("source", ""), d["created_at"]))


def entitlements(ctx: Ctx, employment_id, *, include_voided=True) -> list[dict]:
    docs = _find(ctx, ENT, {"tenant_id": ctx.tenant_id, "employment_id": employment_id})
    return docs if include_voided else [e for e in docs if not e["voided"]]


def entitlement(ctx: Ctx, entity_id) -> dict | None:
    return next(iter(_find(ctx, ENT, {"entity_id": entity_id})), None)


def deferred_in_of(ctx: Ctx, ent: dict) -> dict | None:
    return next((e for e in _find(ctx, ENT, {"deferred_from_id": ent["entity_id"]}) if not e["voided"]), None)


def conversions(ctx: Ctx, ent_id, *, include_discarded=False) -> list[dict]:
    docs = _find(ctx, CONV, {"entitlement_id": ent_id})
    return docs if include_discarded else [c for c in docs if c["status"] != "Discarded"]


def deferrals(ctx: Ctx, ent_id) -> list[dict]:
    return _find(ctx, DEFERRAL, {"entitlement_id": ent_id})


def deferral(ctx: Ctx, ent_id, statuses=("Agreed", "Applied")) -> dict | None:
    """R82：同一筆同時最多一筆沒有撤回、沒有失效的協商。"""
    return next((a for a in deferrals(ctx, ent_id) if a["status"] in statuses), None)


def used(ctx: Ctx, ent: dict) -> Decimal:
    """已休＝固定資料 [靜態替代] ＋ 開始管理前已休（05_mapping 1.2）。

    as_of：固定資料是覆寫＋change_log（P2 B），但 change_log 只記欄位名稱、不記值（hire-employee D-08），
    所以從 LoadUsedQuantityFixture 事件記的值還原（暫時，signoff.md #11）。
    """
    if ctx.as_of is None:
        f = ctx.db.leave_used_quantity_fixtures.find_one({"entitlement_id": ent["entity_id"]}, session=ctx.s)
        v = f["used_quantity"] if f else None
    else:
        e = ctx.db.events.find_one({"type": "LoadUsedQuantityFixture", "subject.id": ent["entity_id"],
                                    "recorded_at": {"$lte": ctx.as_of}}, sort=[("recorded_at", -1)], session=ctx.s)
        v = e["payload"]["used_quantity"] if e else None
    return B.decimal(v) + B.decimal(ent.get("pre_system_used_quantity"))


@dataclass
class Quantities:
    used: Decimal
    deferred_out: Decimal
    converted: Decimal
    expired: Decimal
    remaining: Decimal


def quantities(ctx: Ctx, ent: dict) -> Quantities:
    """C01（04 D-14）：已判定的轉換，以及待確認中的正數（含失效）先扣住；待確認中的負數差額不算。"""
    u = used(ctx, ent)
    din = deferred_in_of(ctx, ent)
    out = to_dec(din["quantity"]) if din else Decimal(0)
    conv = exp = Decimal(0)
    for c in conversions(ctx, ent["entity_id"]):
        q = to_dec(c["quantity"])
        if c["status"] == "Provisional" and q < 0:
            continue
        if c["target"] == FORFEITED:
            exp += q
        else:
            conv += q
    q = to_dec(ent["quantity"])
    return Quantities(u, out, conv, exp, q - u - out - conv - exp)


def check_conservation(ctx: Ctx, ent_id) -> None:
    """C01、C02：每次寫入請假權利或轉換後在同一交易中檢查；不成立是程式錯誤，中止交易（05_mapping 3.1）。"""
    ent = entitlement(ctx, ent_id)
    if ent is None or ent["status"] == "Voided":
        return
    qs = quantities(ctx, ent)
    if ent["status"] == "YearEnded":
        unused = to_dec(ent["quantity"]) - qs.used
        # 暫時：待確認的負數差額不算進 C01（04 D-14），確認前還可以休是負的，和「已年度終結的為 0」互相矛盾（signoff.md #15）
        held = sum((to_dec(c["quantity"]) for c in conversions(ctx, ent_id)
                    if c["status"] == "Provisional" and to_dec(c["quantity"]) < 0), Decimal(0))
        if qs.remaining - held != 0 and not (unused < 0 and qs.remaining - held == unused):
            raise AssertionError(f"C01 不成立：{ent_id} 已年度終結，還可以休 {qs.remaining}")
        if unused >= 0:
            convs = sum((to_dec(c["quantity"]) for c in conversions(ctx, ent_id)), Decimal(0))
            if qs.deferred_out + convs != unused:
                raise AssertionError(f"C02 不成立：{ent_id} 未休 {unused} ≠ 遞延 {qs.deferred_out} ＋ 轉換 {convs}")


# ---- 寫入 ----

def create_entitlement(ctx: Ctx, fields: dict, *, event_id) -> ObjectId:
    doc = to_db({**fields, "tenant_id": ctx.tenant_id, "status": fields.get("status", "Active"), "voided": False})
    return insert_versioned(ctx.db, ctx.s, ENT, clean(doc), event_id=event_id)


def change_entitlement(ctx: Ctx, cur: dict, changes: dict, *, event_id) -> dict:
    changes = to_db(changes)
    if "status" in changes:
        changes["voided"] = changes["status"] == "Voided"
    unset = [k for k, v in changes.items() if v is None]
    nxt = new_version(ctx.db, ctx.s, ENT, cur, {k: v for k, v in changes.items() if v is not None}, event_id=event_id)
    if unset:
        ctx.db[ENT].update_one({"_id": nxt["_id"]}, {"$unset": {k: "" for k in unset}}, session=ctx.s)
        for k in unset:
            nxt.pop(k, None)
    return nxt


def create_conversion(ctx: Ctx, fields: dict, *, event_id) -> ObjectId:
    doc = to_db({**fields, "tenant_id": ctx.tenant_id})
    doc["quantity"] = to_dec128(fields["quantity"])
    cid = insert_versioned(ctx.db, ctx.s, CONV, clean(doc), event_id=event_id)
    if fields["status"] == "Determined":
        to_payroll(ctx, cid, fields["employment_id"], event_id)
    return cid


def change_conversion(ctx: Ctx, cur: dict, changes: dict, *, event_id) -> dict:
    nxt = new_version(ctx.db, ctx.s, CONV, cur, changes, event_id=event_id)
    if changes.get("status") == "Determined":
        to_payroll(ctx, cur["entity_id"], cur["employment_id"], event_id)
    return nxt


def to_payroll(ctx: Ctx, conversion_id, employment_id, event_id) -> None:
    """D-09：直接判定與確認後的轉換交給薪資切片（只帶編號）。"""
    ctx.db.outbox.insert_one({"tenant_id": ctx.tenant_id, "event_id": event_id, "type": "LeaveConversionDetermined",
                              "conversion_id": conversion_id, "employment_id": employment_id, "created_at": now()},
                             session=ctx.s)


def change_deferral(ctx: Ctx, cur: dict, changes: dict, *, event_id) -> dict:
    return new_version(ctx.db, ctx.s, DEFERRAL, cur, to_db(changes), event_id=event_id)


def d(v) -> date | None:
    return to_date(v)
