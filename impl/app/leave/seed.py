"""annual-leave-grant 的規則版本（P5）：參數名稱與預設值取自 04_rules.md「參數」表，不在程式裡抄數字（05_mapping 3.2）。

04 參數表只寫了可選做法的中文說明，沒有代碼；程式用的代碼見 OPTION_CODES（signoff.md #2）。
"""
import importlib.util
import re
from datetime import date

from app import config

# 04 版本欄為「—」的規則：版本填 annual-leave-grant/04-v1、修訂 1（05_mapping D-12）。04 目前凍結的是 04-v2（signoff.md #3）
RULE_SET = "annual-leave-grant/04-v1"
NO_LOWER_BOUND = date(1900, 1, 1)
# R66 v1 的生效日 04 寫「生效日未查」；暫時當成沒有下限（signoff.md #4）
R66_V1_FROM = NO_LOWER_BOUND

# 暫時：04 參數表的可選做法沒有代碼，程式自己取的（signoff.md #2）
OPTION_CODES = {
    "acquisition_day_rule": {"末日的隔天": "DAY_AFTER_PERIOD_END", "末日當天": "PERIOD_END_DAY"},
    "fixed_start_year_method": {"延到約定年度的最後一天": "EXTEND_TO_YEAR_END"},
    "company_policy_version_at_year_end": {"給予時的版本": "AT_GRANT", "年度終結當天的版本": "AT_YEAR_END"},
    # 這兩個的代碼由 ⑤ 決定（schema.mongo.js employer_settings、company_policy_versions）
    "payment_deadline_rule": {"年度終結後 30 日內": "DAYS_AFTER_YEAR_END", "契約約定的工資給付日": "CONTRACT_WAGE_PAYMENT_DAY"},
    "company_extra_year_end_treatment": {"轉為工資": "CONVERSION_TARGET.WAGES", "失效": "CONVERSION_TARGET.FORFEITED"},
    "company_extra_deferrable": {"可以": True, "不可以": False},
}


def _split_row():
    spec = importlib.util.spec_from_file_location("md2build", config.REPO_ROOT / "tools" / "md2build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.split_row


def parameter_defaults() -> dict[str, str]:
    """04 參數表：參數 → 預設值欄（原文）。"""
    split_row = _split_row()
    text = config.LEAVE_RULES_MD.read_text(encoding="utf-8")
    section = text.split("\n## 參數", 1)[1].split("\n## ", 1)[0]
    rows = [split_row(l) for l in section.splitlines() if l.startswith("|")]
    header = rows[0]
    k, v = header.index("參數"), header.index("預設值")
    return {r[k]: r[v] for r in rows[2:]}


def _strip(cell: str) -> str:
    return re.sub(r"\s*\[[^\]]*\]", "", cell).strip()


def _int(cell: str) -> int:
    return int(re.match(r"\s*(\d+)", cell).group(1))


def _option(name: str, cell: str):
    return OPTION_CODES[name][_strip(cell)]


def statutory_table(cell: str) -> list[dict]:
    """statutory_annual_leave_days：「a 個月／年以上未滿 b 年 n 日」各一區間；「10 年以上每一年加給 1 日，加至 30 日」展開成每年一個區間。

    區間的欄位名稱沿用 company_extra_days 的 from_months、to_months、days（04 沒有定義天數表的格式，signoff.md #1）。
    """
    def months(n, unit):
        return int(n) * (1 if unit == "個月" else 12)
    out = []
    for a, au, b, bu, days in re.findall(r"(\d+)\s*(個月|年)以上未滿\s*(\d+)\s*(個月|年)(?:每年)?\s*(\d+)\s*日", cell):
        out.append({"from_months": months(a, au), "to_months": months(b, bu), "days": int(days)})
    m = re.search(r"(\d+)\s*年以上每一年加給\s*(\d+)\s*日，加至\s*(\d+)\s*日", cell)
    start, step, cap = int(m.group(1)) * 12, int(m.group(2)), int(m.group(3))
    days = out[-1]["days"]
    frm = start
    while True:
        days = min(days + step, cap)                 # [解讀] 從滿 10 年那一筆開始加（04 參數表）
        if days == cap:
            out.append({"from_months": frm, "days": days})
            return out
        out.append({"from_months": frm, "to_months": frm + 12, "days": days})
        frm += 12


def rules() -> list[tuple]:
    p = parameter_defaults()
    src = "slices/annual-leave-grant/04_rules.md 參數表"
    return [
        # rule_id, version, effective_from, effective_to, params, source_ref
        ("R65", RULE_SET, NO_LOWER_BOUND, None,
         {"acquisition_day_rule": _option("acquisition_day_rule", p["acquisition_day_rule"]),
          "first_period_months": _int(p["first_period_months"]), "pending": "EQ-006"},
         f"勞基法 §38、施行細則 §5、民法 §121 [未核對]；{src}"),
        ("R66", "v1", R66_V1_FROM, None,
         {"statutory_annual_leave_days": statutory_table(p["statutory_annual_leave_days"]), "pending": "EQ-008"},
         f"特別休假#01 讀取日 2026-10-05 的現行條文 [未核對]；{src}"),
        ("R68", RULE_SET, NO_LOWER_BOUND, None,
         {"leave_year_basis_when_none": "LEAVE_YEAR_BASIS.ANNIVERSARY", "pending": "EQ-002"}, f"施行細則 §24 [未核對]；{src}"),
        ("R70", RULE_SET, NO_LOWER_BOUND, None,
         {"fixed_start_year_method": _option("fixed_start_year_method", p["fixed_start_year_method"]), "pending": "EQ-002"},
         f"施行細則 §24 [未核對]；{src}"),
        ("R79", RULE_SET, NO_LOWER_BOUND, None,
         {"company_policy_version_at_year_end": _option("company_policy_version_at_year_end",
                                                        p["company_policy_version_at_year_end"]),
          # 暫時：「那一版沒有寫」時的預設，⑤ 3.2 沒有放的地方（signoff.md #5）
          "company_extra_year_end_treatment": _option("company_extra_year_end_treatment",
                                                      p["company_extra_year_end_treatment"]),
          "company_extra_deferrable": _option("company_extra_deferrable", p["company_extra_deferrable"]),
          "pending": "EQ-005、EQ-013"}, f"公司規定 [未核對]；{src}"),
        ("R80", RULE_SET, NO_LOWER_BOUND, None, {"notice_period_days": _int(p["notice_period_days"])},
         f"施行細則 §24 第 3 項、民法 §120 [未核對]；{src}"),
        ("R90", RULE_SET, NO_LOWER_BOUND, None,
         {"payment_days_after_year_end": _int(p["payment_days_after_year_end"]),
          "payment_deadline_rule": _option("payment_deadline_rule", p["payment_deadline_rule"]),
          # 暫時：雇主沒有登錄給付日時的預設，⑤ 3.2 沒有放的地方（signoff.md #5）
          "wage_payment_day": _int(p["wage_payment_day"]), "wage_payment_lag_months": _int(p["wage_payment_lag_months"]),
          "pending": "EQ-003"}, f"施行細則 §24-1 [未核對]；inputs/drafts/特休未休工資發給期限.md（推想）；{src}"),
        ("R94", RULE_SET, NO_LOWER_BOUND, None, {"provisional_review_days": _int(p["provisional_review_days"])},
         f"AI 提出（04 D-17）；{src}"),
        ("R99", RULE_SET, NO_LOWER_BOUND, None, {"seniority_merge_gap_months": _int(p["seniority_merge_gap_months"]),
                                                 "pending": "EQ-007"}, f"勞基法 §10 [未核對]；{src}"),
    ] + [
        # 沒有參數的規則：判定、警告與依據的版本也要引用（P5）
        (rid, RULE_SET, NO_LOWER_BOUND, None, {}, "slices/annual-leave-grant/04_rules.md")
        for rid in ("R67", "R69", "R71", "R72", "R73", "R74", "R75", "R76", "R77", "R78", "R81", "R82", "R83", "R84",
                    "R85", "R86", "R87", "R88", "R89", "R91", "R92", "R93", "R95", "R96", "R97", "R98")
    ]
