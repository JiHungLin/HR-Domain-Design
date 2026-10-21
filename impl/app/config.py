"""執行設定。所有值都可用環境變數覆寫。"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SLICE_DIR = REPO_ROOT / "slices" / "hire-employee"

MONGO_URI = os.environ.get("HR_MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.environ.get("HR_DB_NAME", "hr_hire_dev")
API_SPEC = SLICE_DIR / "api.yaml"
SCHEMA_SCRIPT = SLICE_DIR / "schema.mongo.js"
RULES_MD = SLICE_DIR / "04_rules.md"
