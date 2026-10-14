"""全平台共用的參考資料（05_mapping 1.1）：jurisdictions、social_insurance_schemes、rule_versions、labels。

規則以資料存在，不寫死在程式（P5）。數字來源寫在 source_ref；AI 依一般知識補的標 [未核對]。
"""
import re
import subprocess
from datetime import date

from app import config
from app.db import database, now, to_dt

SCHEMES = [
    # code, insurer, effective_from, source_ref
    ("SCHEME.LABOR_INSURANCE_TW", "INSURER.BLI_TW", date(1950, 3, 1), "[未核對] AI 依一般知識"),
    ("SCHEME.EMPLOYMENT_INSURANCE_TW", "INSURER.BLI_TW", date(2003, 1, 1), "勞保就保職保#09"),
    ("SCHEME.OCCUPATIONAL_ACCIDENT_INSURANCE_TW", "INSURER.BLI_TW", date(2022, 5, 1), "[未核對] AI 依一般知識（施行日待核對，R25）"),
    ("SCHEME.NATIONAL_HEALTH_INSURANCE_TW", "INSURER.NHIA_TW", date(1995, 3, 1), "[未核對] AI 依一般知識"),
    ("SCHEME.LABOR_PENSION_TW", "INSURER.BLI_TW", date(2005, 7, 1), "[未核對] AI 依一般知識"),
]
LI, EI, OAI, NHI, LP = (s[0] for s in SCHEMES)

ALLOWANCES = ["ALLOWANCE_CATEGORY.MEAL", "ALLOWANCE_CATEGORY.TRANSPORT",
              "ALLOWANCE_CATEGORY.ATTENDANCE_BONUS", "ALLOWANCE_CATEGORY.POSITION_ALLOWANCE"]


def _table(rows):
    """[(上限或 None, 投保金額)] → [{grade, upper, amount}]，grade 從 1 起算，除非另給。"""
    return [{"grade": str(g), "upper": u, "amount": a} for g, (u, a) in enumerate(rows, start=1)]


_LI_ROWS = [(29500, 29500), (30300, 30300), (31800, 31800), (33300, 33300), (34800, 34800), (36300, 36300),
            (38200, 38200), (40100, 40100), (42000, 42000), (43900, 43900), (None, 45800)]
_OAI_ROWS = _LI_ROWS[:10] + [(45800, 45800), (48200, 48200), (50600, 50600), (53000, 53000), (55400, 55400),
                             (57800, 57800), (60800, 60800), (63800, 63800), (66800, 66800), (69800, 69800), (None, 72800)]
_LP_FROM_25 = [29500, 30300, 31800, 33300, 34800, 36300, 38200, 40100, 42000, 43900, 45800, 48200, 50600, 53000,
               55400, 57800, 60800, 63800, 66800, 69800, 72800, 76500, 80200, 83900, 87600, 92100, 96600, 101100,
               105600, 110100, 115500, 120900, 126300]
_NHI_AMOUNTS = [29500, 30300, 31800, 33300, 34800, 36300, 38200, 40100, 42000, 43900, 45800, 48200, 50600, 53000,
                55400, 57800, 60800, 63800, 66800, 69800, 72800, 76500, 80200, 83900, 87600, 92100, 96600, 101100,
                105600, 110100, 115500, 120900, 126300, 131700, 137100, 142500, 147900, 150000, 156400, 162800,
                169200, 175600, 182000, 189500, 197000, 204500, 212000, 219500, 228200, 236900, 245600, 254300,
                263000, 273000, 283000, 293000, 303000, 313000]

D2026 = date(2026, 1, 1)

RULES = [
    # rule_id, version, effective_from, effective_to, params, source_ref
    ("R12", "v2025", date(2025, 1, 1), date(2025, 12, 31), {"monthly_minimum_wage": 28590}, "勞保就保職保#08 [未核對]"),
    ("R12", "v2026", D2026, None, {"monthly_minimum_wage": 29500}, "工資與最低工資#07 [未核對]"),
    ("R11", "2026-10-14", date(1900, 1, 1), None,
     {"compare_basis": "BASE_SALARY", "pending": "EQ-019（比較用底薪或含每月固定給付）"}, "最低工資法 §3、§5 [未核對]"),
    ("R22", "2026-10-05", date(1950, 3, 1), None,
     {"min_age": 15, "max_age": 65, "headcount_threshold": 5,
      "threshold_categories": ["LI_INDUSTRY.LIA6_01_TW", "LI_INDUSTRY.LIA6_02_TW", "LI_INDUSTRY.LIA6_03_TW"],
      "no_threshold_categories": ["LI_INDUSTRY.LIA6_04_TW", "LI_INDUSTRY.LIA6_05_TW"],
      "pending": ["EQ-004", "EQ-006", "EQ-008"]}, "勞工保險條例 §6、§8 [未核對]"),
    ("R24", "2026-10-05", date(2003, 1, 1), None,
     {"min_age": 15, "max_age": 65, "residence_basis": ["RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW"]},
     "就業保險法 §5 [未核對]"),
    ("R25", "2026-10-05", date(2022, 5, 1), None,
     {"min_age": 15, "registration_kinds": ["REGISTRATION_KIND.COMPANY_TW", "REGISTRATION_KIND.BUSINESS_TW",
                                            "REGISTRATION_KIND.TAX_REGISTRATION_TW", "REGISTRATION_KIND.PRACTICE_LICENSE_TW"]},
     "勞工職業災害保險及保護法 §6 [未核對]"),
    ("R26", "2026-10-05", date(1995, 3, 1), None,
     {"residence_document_kinds": ["DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW", "DOCUMENT_KIND.PERMANENT_RESIDENT_CERTIFICATE_TW"]},
     "全民健康保險法 §8、§9 [未核對]"),
    ("R27", "2026-10-05", date(2005, 7, 1), None,
     {"residence_basis": ["RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW", "RESIDENCE_BASIS.CONTINUED_AFTER_DIVORCE_OR_DEATH_TW",
                          "RESIDENCE_BASIS.PERMANENT_TW"]}, "勞工退休金條例 §7 [未核對]"),
    ("R31", "2026-10-05", date(1950, 3, 1), None, {"deadline_offset_days": 0}, "勞工保險條例 §11 [未核對]"),
    ("R32", "2026-10-05", date(2022, 5, 1), None,
     {"deadline_offset_days": 0, "registration_kinds": ["REGISTRATION_KIND.COMPANY_TW", "REGISTRATION_KIND.BUSINESS_TW",
                                                        "REGISTRATION_KIND.TAX_REGISTRATION_TW"]},
     "勞工職業災害保險及保護法 §12、§13 [未核對]"),
    ("R33", "2026-10-05", date(1995, 3, 1), None,
     {"window_days": 3, "first_day_excluded": True, "pending": "EQ-003（法定生效日）"}, "全民健康保險法 §15 [未核對]"),
    ("R34", "2026-10-05", date(2005, 7, 1), None,
     {"window_days": 7, "first_day_excluded": True, "pending": "EQ-003（開始提繳日）"}, "勞工退休金條例 §18 [未核對]"),
    ("R39", "2026-10-14", date(1900, 1, 1), None,
     {"bases": {
         "MONTHLY_PAYROLL_TOTAL": {"schemes": [LI, EI, OAI], "included_allowances": ALLOWANCES},
         "MONTHLY_WAGE": {"schemes": [LP], "included_allowances": ALLOWANCES},
         "SALARY_INCOME": {"schemes": [NHI], "included_allowances": ALLOWANCES}},
      "needs_human": ["ALLOWANCE_CATEGORY.OTHER"],
      "pending": "EQ-012：哪些固定給付算入尚待專家確認；暫以使用者 GC01 預期結果的前提（伙食津貼算入）為假設"},
     "勞工保險條例 §14、職保法 §17、勞退條例 §14、健保法 §20 [未核對]"),
    ("R40", "v2026", D2026, None, {"schemes": [LI, EI], "grades": _table(_LI_ROWS)}, "勞保就保職保#17 [未核對]"),
    ("R41", "v2026", D2026, None, {"schemes": [OAI], "grades": _table(_OAI_ROWS)}, "勞保就保職保#18 [未核對]"),
    ("R42", "v2026", D2026, None,
     {"schemes": [LP], "lower_bound": 28591,
      "grades": [{"grade": str(25 + i), "upper": a, "amount": a} for i, a in enumerate(_LP_FROM_25)],
      "partial": "原始資料只摘錄第 25～57 級（勞工退休金#05）"}, "勞工退休金#05 [未核對]"),
    ("R43", "v2026", D2026, None,
     {"schemes": [NHI], "grades": [{"grade": str(i), "upper": (a if i < len(_NHI_AMOUNTS) else None), "amount": a}
                                   for i, a in enumerate(_NHI_AMOUNTS, start=1)]},
     "inputs/shared/健保投保金額分級表_115年1月1日.md（使用者提供）[未核對]"),
    ("R44", "2026-10-14", date(1900, 1, 1), None, {"table_date": "START_DATE", "pending": "EQ-012"}, "勞保就保職保#19 [未核對]"),
]


def parse_labels() -> list[dict]:
    """從 04_rules.md 的「分類值」表取出 zh-TW 名稱（P10）。"""
    text = config.RULES_MD.read_text(encoding="utf-8")
    section = text.split("## 分類值", 1)[1].split("\n## ", 1)[0]
    out = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*([A-Z][A-Z0-9_]*\.[A-Z0-9_]+)\s*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|", line)
        if m:
            out.append({"code": m.group(1), "locale": "zh-TW", "label": m.group(2)})
    return out


def create_schema(db_name: str) -> None:
    """用 mongosh 執行 slices/hire-employee/schema.mongo.js（集合驗證規則與索引）。"""
    uri = config.MONGO_URI.replace("/?", f"/{db_name}?") if "/?" in config.MONGO_URI else f"{config.MONGO_URI.rstrip('/')}/{db_name}"
    subprocess.run(["mongosh", "--quiet", uri, str(config.SCHEMA_SCRIPT)], check=True)


def seed_reference(db) -> None:
    ts = now()
    tw = db.jurisdictions.insert_one({"code": "TW", "level": "JURISDICTION_LEVEL.COUNTRY", "created_at": ts}).inserted_id
    db.social_insurance_schemes.insert_many([
        {"jurisdiction_id": tw, "code": c, "insurer": ins, "effective_from": to_dt(eff), "source_ref": src, "created_at": ts}
        for c, ins, eff, src in SCHEMES])
    db.rule_versions.insert_many([
        {k: v for k, v in {
            "rule_id": rid, "version": ver, "revision": 1, "effective_from": to_dt(f), "effective_to": to_dt(t),
            "params": params, "source_ref": src, "recorded_at": ts, "created_at": ts}.items() if v is not None}
        for rid, ver, f, t, params, src in RULES])
    db.labels.insert_many([{**l, "created_at": ts} for l in parse_labels()])


def init(db_name: str, reset: bool = False) -> None:
    db = database(db_name)
    if reset:
        db.client.drop_database(db_name)
    create_schema(db_name)
    seed_reference(db)
