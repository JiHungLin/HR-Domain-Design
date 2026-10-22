"""取得「今天」的唯一入口（平台 P4）：依雇主所在地的當地日期，不直接讀伺服器時鐘。

annual-leave-grant 05_mapping D-28、hire-employee 05_mapping D-24：地點是雇主所在地。
地點 → 時區由平台維護對照（P4）；這版還沒有平台的對照表，TIMEZONES 是 [靜態替代]（signoff.md #6）。
測試用 fixed() 固定「今天」。
"""
from contextlib import contextmanager
from datetime import date, datetime
from zoneinfo import ZoneInfo

TIMEZONES = {"TW": "Asia/Taipei"}   # [靜態替代] 代替平台的地點 → 時區對照（P4）；沒有對照的用 UTC

_fixed: date | None = None


def today(db, employer: dict | None = None, session=None) -> date:
    if _fixed is not None:
        return _fixed
    tz = "UTC"
    if employer and employer.get("jurisdiction_id"):
        j = db.jurisdictions.find_one({"_id": employer["jurisdiction_id"]}, session=session)
        tz = TIMEZONES.get((j or {}).get("code"), "UTC")
    return datetime.now(ZoneInfo(tz)).date()


@contextmanager
def fixed(d: date):
    global _fixed
    before, _fixed = _fixed, d
    try:
        yield
    finally:
        _fixed = before


def set_today(d: date | None) -> None:
    global _fixed
    _fixed = d
