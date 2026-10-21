"""annual-leave-grant 的每日排程（05_mapping D-03）：先處理重新判定佇列，再對每段僱傭關係補給予、年度終結。

用法：uv run python scripts/run_daily.py [--db 名稱] [--today YYYY-MM-DD]
--today 只供開發與測試；正式執行時「今天」以雇主所在管轄區的日期判斷。
"""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402
from app.db import database  # noqa: E402
from app.leave import scheduler  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--db", default=config.DB_NAME)
ap.add_argument("--today", type=date.fromisoformat)
a = ap.parse_args()
print(scheduler.run_daily(database(a.db), a.today))
