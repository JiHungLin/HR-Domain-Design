"""建立資料庫：執行 schema.mongo.js 並載入參考資料。

用法：uv run python scripts/init_db.py [--reset] [--db 名稱]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config, seed  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--db", default=config.DB_NAME)
ap.add_argument("--reset", action="store_true", help="先刪掉整個資料庫")
a = ap.parse_args()
seed.init(a.db, reset=a.reset)
print(f"已建立 {a.db}")
