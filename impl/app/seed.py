"""全平台共用的參考資料（05_mapping 1.1）：jurisdictions、social_insurance_schemes、rule_versions、labels。

規則以資料存在，不寫死在程式（P5）。數字來源寫在 source_ref；AI 依一般知識補的標 [未核對]。
"""
import re
import subprocess
from datetime import date

from app import config
from app.db import database, now, to_dt
from app.leave import seed as leave_seed

SCHEMES = [
    # code, insurer, effective_from, source_ref（施行日的來源；全部 [未核對]）
    ("SCHEME.LABOR_INSURANCE_TW", "INSURER.BLI_TW", date(1960, 2, 24),
     "勞保就保職保#20 [未核對]：行政院令在臺灣省施行的日期；是令的日期還是生效日待核對"),
    ("SCHEME.EMPLOYMENT_INSURANCE_TW", "INSURER.BLI_TW", date(2003, 1, 1), "勞保就保職保#21 [未核對]"),
    ("SCHEME.OCCUPATIONAL_ACCIDENT_INSURANCE_TW", "INSURER.BLI_TW", date(2022, 5, 1), "勞保就保職保#22 [未核對]"),
    ("SCHEME.NATIONAL_HEALTH_INSURANCE_TW", "INSURER.NHIA_TW", date(1995, 3, 1), "全民健康保險#13 [未核對]"),
    ("SCHEME.LABOR_PENSION_TW", "INSURER.BLI_TW", date(2005, 7, 1),
     "勞工退休金#06 [未核對]；原文為「自公布後一年施行」，日期依民法期間計算推算 [解讀]"),
]
LI, EI, OAI, NHI, LP = (s[0] for s in SCHEMES)

ALLOWANCES = ["ALLOWANCE_CATEGORY.MEAL", "ALLOWANCE_CATEGORY.TRANSPORT",
              "ALLOWANCE_CATEGORY.ATTENDANCE_BONUS", "ALLOWANCE_CATEGORY.POSITION_ALLOWANCE"]

# ---- 分級表：載入時從 inputs/ 的來源解析，不在程式裡抄數字（P5；docs/01 ⑥ 規則資料只能來自 ④ 與 inputs/） ----

def _num(t: str) -> int:
    return int(t.replace(",", "").replace(" ", ""))


def _section(path, heading_prefix: str) -> str:
    text = (config.REPO_ROOT / path).read_text(encoding="utf-8")
    start = text.index(f"## {heading_prefix}")
    nxt = text.find("\n## ", start + 3)
    return text[start: nxt if nxt != -1 else None]


def _quoted_grades(path, heading_prefix: str) -> list[dict]:
    """研究條目原文摘錄的「第 n 級　a 元至 b 元　c 元」或「第 n 級　a 元以下／以上　c 元」。"""
    rows = []
    for line in _section(path, heading_prefix).splitlines():
        m = re.match(r"\s*>\s*第\s*(\d+)\s*級\s+(.+?)\s+([\d,]+)\s*元\s*$", line)
        if not m:
            continue
        grade, rng, amount = m.group(1), m.group(2), _num(m.group(3))
        nums = [_num(x) for x in re.findall(r"[\d,]+", rng)]
        upper = None if "以上" in rng else nums[-1]
        rows.append({"grade": grade, "upper": upper, "amount": amount})
    return rows


def _md_table_grades(path, grade_col: int, amount_col: int, range_col: int) -> list[dict]:
    """使用者提供的分級表（Markdown 表格）。"""
    rows = []
    for line in (config.REPO_ROOT / path).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) <= max(grade_col, amount_col, range_col) or not cells[grade_col].isdigit():
            continue
        rng = cells[range_col]
        upper = None if "以上" in rng else _num(re.findall(r"[\d,]+", rng)[-1])
        rows.append({"grade": cells[grade_col], "upper": upper, "amount": _num(re.findall(r"[\d,]+", cells[amount_col])[0])})
    return rows


def grading_tables() -> dict[str, list[dict]]:
    lp = _md_table_grades("inputs/shared/勞工退休金月提繳分級表_115年1月1日.md", 0, 2, 1)
    nhi = _md_table_grades("inputs/shared/健保投保金額分級表_115年1月1日.md", 1, 2, 3)
    # 健保表第 53 級原檔寫作「254,301-26,3000」（排版錯誤，見來源檔說明）；上限一律取該級的投保金額
    nhi = [g | {"upper": None if g["upper"] is None else g["amount"]} for g in nhi]
    return {
        "R40": _quoted_grades("inputs/research/勞保就保職保.md", "勞保就保職保#17"),
        "R41": _quoted_grades("inputs/research/勞保就保職保.md", "勞保就保職保#18"),
        "R42": lp,
        "R43": nhi,
    }


D2026 = date(2026, 1, 1)
# 04_rules 版本欄為「—」的規則，以規則所在的 04 凍結版本為版本、修訂 1（05_mapping D-20）
RULE_SET = "hire-employee/04-v5"


def rules() -> list[tuple]:
    t = grading_tables()
    return [
        # rule_id, version, effective_from, effective_to, params, source_ref
        ("R12", "v2025", date(2025, 1, 1), date(2025, 12, 31), {"monthly_minimum_wage": 28590}, "勞保就保職保#08 [未核對]"),
        ("R12", "v2026", D2026, None, {"monthly_minimum_wage": 29500}, "工資與最低工資#07 [未核對]"),
        ("R11", RULE_SET, date(1900, 1, 1), None,
         {"compare_basis": "BASE_SALARY", "pending": "EQ-019"}, "最低工資法 §3、§5 [未核對]"),
        ("R14", RULE_SET, date(1900, 1, 1), None, {}, "就業服務法 §43、§48、§51 [未核對]"),
        ("R15", RULE_SET, date(1900, 1, 1), None, {}, "就業服務法 §43 [未核對]"),
        ("R21", RULE_SET, date(1900, 1, 1), None, {}, "業務需求（02 的關係 agreedFor、governs）"),
        ("R36", RULE_SET, date(1900, 1, 1), None, {}, "由 R31～R34 推導；判定，不是警告（04_rules D-17）"),
        ("R45", RULE_SET, date(1900, 1, 1), None, {}, "由 R40～R43 推導；勞保就保職保#19"),
        ("R61", RULE_SET, date(1900, 1, 1), None, {"pending": "EQ-005"}, "業務需求；勞工保險條例 §11 [未核對]"),
        ("R22", "2026-10-05", date(1960, 2, 24), None,
         {"min_age": 15, "max_age": 65, "headcount_threshold": 5,
          "threshold_categories": ["LI_INDUSTRY.LIA6_01_TW", "LI_INDUSTRY.LIA6_02_TW", "LI_INDUSTRY.LIA6_03_TW"],
          "no_threshold_categories": ["LI_INDUSTRY.LIA6_04_TW", "LI_INDUSTRY.LIA6_05_TW"]},
         "勞工保險條例 §6、§8 [未核對]"),
        ("R24", "2026-10-05", date(2003, 1, 1), None,
         {"min_age": 15, "max_age": 65, "residence_basis": ["RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW"]},
         "就業保險法 §5 [未核對]"),
        ("R25", "2026-10-14", date(2022, 5, 1), None,
         {"min_age": 15,
          "registration_kinds": ["REGISTRATION_KIND.COMPANY_TW", "REGISTRATION_KIND.BUSINESS_TW",
                                 "REGISTRATION_KIND.TAX_REGISTRATION_TW", "REGISTRATION_KIND.PRACTICE_LICENSE_TW"],
          "public_sector_categories": ["LI_INDUSTRY.LIA6_04_TW"],
          "notified_voluntary_employers": None},
         "勞工職業災害保險及保護法 §6、§9 [未核對]"),
        ("R26", "2026-10-05", date(1995, 3, 1), None,
         {"residence_document_kinds": ["DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW", "DOCUMENT_KIND.PERMANENT_RESIDENT_CERTIFICATE_TW"]},
         "全民健康保險法 §8、§9 [未核對]"),
        ("R27", "2026-10-05", date(2005, 7, 1), None,
         {"residence_basis": ["RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW", "RESIDENCE_BASIS.CONTINUED_AFTER_DIVORCE_OR_DEATH_TW",
                              "RESIDENCE_BASIS.PERMANENT_TW"]}, "勞工退休金條例 §7 [未核對]"),
        ("R31", "2026-10-05", date(1960, 2, 24), None, {"deadline_offset_days": 0}, "勞工保險條例 §11 [未核對]"),
        ("R32", "2026-10-05", date(2022, 5, 1), None,
         {"deadline_offset_days": 0, "registration_kinds": ["REGISTRATION_KIND.COMPANY_TW", "REGISTRATION_KIND.BUSINESS_TW",
                                                            "REGISTRATION_KIND.TAX_REGISTRATION_TW"]},
         "勞工職業災害保險及保護法 §12、§13 [未核對]"),
        ("R33", "2026-10-05", date(1995, 3, 1), None,
         {"window_days": 3, "first_day_excluded": True, "pending": "EQ-003"}, "全民健康保險法 §15 [未核對]"),
        ("R34", "2026-10-05", date(2005, 7, 1), None,
         {"window_days": 7, "first_day_excluded": True, "pending": "EQ-003"}, "勞工退休金條例 §18 [未核對]"),
        ("R39", RULE_SET, date(1900, 1, 1), None,
         {"bases": {
             "MONTHLY_PAYROLL_TOTAL": {"schemes": [LI, EI, OAI], "included_allowances": ALLOWANCES},
             "MONTHLY_WAGE": {"schemes": [LP], "included_allowances": ALLOWANCES},
             "SALARY_INCOME": {"schemes": [NHI], "included_allowances": ALLOWANCES}},
          "needs_decision": ["ALLOWANCE_CATEGORY.OTHER"], "pending": "EQ-012"},
         "勞工保險條例 §14、職保法 §17、勞退條例 §14、健保法 §20 [未核對]；算入的類別是 EQ-012 回覆前的假設（signoff.md #7）"),
        ("R40", "v2026", D2026, None, {"schemes": [LI, EI], "grades": t["R40"]}, "勞保就保職保#17 [未核對]"),
        ("R41", "v2026", D2026, None, {"schemes": [OAI], "grades": t["R41"]}, "勞保就保職保#18 [未核對]"),
        ("R42", "v2026", D2026, None, {"schemes": [LP], "grades": t["R42"]},
         "inputs/shared/勞工退休金月提繳分級表_115年1月1日.md（使用者提供）[未核對]"),
        ("R43", "v2026", D2026, None, {"schemes": [NHI], "grades": t["R43"]},
         "inputs/shared/健保投保金額分級表_115年1月1日.md（使用者提供）[未核對]"),
        ("R44", RULE_SET, date(1900, 1, 1), None, {"table_date": "START_DATE", "pending": "EQ-012"}, "勞保就保職保#19 [未核對]"),
    ]


def parse_labels(rules_md=None) -> list[dict]:
    """從 04_rules.md 的「分類值」表取出 zh-TW 名稱（P10）。"""
    text = (rules_md or config.RULES_MD).read_text(encoding="utf-8")
    section = text.split("## 分類值", 1)[1].split("\n## ", 1)[0]
    out = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*([A-Z][A-Z0-9_]*\.[A-Z0-9_]+)\s*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|", line)
        if m:
            out.append({"code": m.group(1), "locale": "zh-TW", "label": m.group(2)})
    return out


def create_schema(db_name: str) -> None:
    """用 mongosh 依序執行 hire-employee 與 annual-leave-grant 的 schema.mongo.js（集合驗證規則與索引）。"""
    uri = config.MONGO_URI.replace("/?", f"/{db_name}?") if "/?" in config.MONGO_URI else f"{config.MONGO_URI.rstrip('/')}/{db_name}"
    for script in config.SCHEMA_SCRIPTS:
        subprocess.run(["mongosh", "--quiet", uri, str(script)], check=True)


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
        for rid, ver, f, t, params, src in rules() + leave_seed.rules()])
    labels = {l["code"]: l for l in parse_labels() + parse_labels(config.LEAVE_RULES_MD)}
    db.labels.insert_many([{**l, "created_at": ts} for l in labels.values()])
    # annual-leave-grant 的 schema.mongo.js 已建立台灣特休（leave_types）；補上 establishedBy
    db.leave_types.update_one({"code": "LEAVE_TYPE.ANNUAL_LEAVE_TW"}, {"$set": {"jurisdiction_id": tw, "created_at": ts}})


def init(db_name: str, reset: bool = False) -> None:
    db = database(db_name)
    if reset:
        db.client.drop_database(db_name)
    create_schema(db_name)
    seed_reference(db)
