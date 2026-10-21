"""特休的日期計算（04_rules R65、R69、R70、R80、R87、R90），不碰資料庫。

期間依民法 §121（期間計算#03 [未核對]）：以月定期間，以相當日的前一天為末日，沒有相當日時以該月最後一天為末日；
年資自到職日當天起算（施行細則 §5，R65 [解讀]）。
"""
import calendar
from datetime import date, timedelta

DAY = timedelta(days=1)


def last_day(y: int, m: int) -> date:
    return date(y, m, calendar.monthrange(y, m)[1])


def _shift(y: int, m: int, n: int) -> tuple[int, int]:
    k = y * 12 + (m - 1) + n
    return k // 12, k % 12 + 1


def period_end(start: date, months: int) -> date:
    """從 start 當天起算 months 個月的期間末日（民法 §121）。"""
    y, m = _shift(start.year, start.month, months)
    if start.day <= calendar.monthrange(y, m)[1]:
        return date(y, m, start.day) - DAY
    return last_day(y, m)


def months_later_on_day(base: date, months: int, day: int) -> date:
    """base 所在月份之後第 months 個月的第 day 日；那個月沒有那一天時用最後一天（R90）。"""
    y, m = _shift(base.year, base.month, months)
    return date(y, m, min(day, calendar.monthrange(y, m)[1]))


def fixed_year_end(on: date, year_start: dict) -> date:
    """固定起始日年度（起始月日 year_start）中，包含 on 的那個年度的最後一天（R70）。"""
    m, d = year_start["month"], year_start["day"]

    def start_in(y):
        return date(y, m, min(d, calendar.monthrange(y, m)[1]))
    s = start_in(on.year)
    if s > on:
        s = start_in(on.year - 1)
    return start_in(s.year + 1) - DAY
