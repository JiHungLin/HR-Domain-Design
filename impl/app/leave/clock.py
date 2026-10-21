"""「今天」以雇主所在管轄區的日期判斷（05_mapping 第二節 GrantLeaveEntitlement、CloseLeaveYear）。

暫時：管轄區沒有時區的屬性（core Jurisdiction、hire-employee 的 jurisdictions 都沒有），
時區寫在這裡（signoff.md #6）。測試用 fixed() 固定「今天」。
"""
from contextlib import contextmanager
from datetime import date, datetime
from zoneinfo import ZoneInfo

TIMEZONES = {"TW": "Asia/Taipei"}   # 暫時（signoff.md #6）

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
