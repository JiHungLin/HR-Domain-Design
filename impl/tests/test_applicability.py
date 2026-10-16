"""各保險的判定（04_rules @ 04-v2）：每一種情況都給明確的結果（D-13、D-14）。

這裡測的是規則的分支，不是黃金案例：預期的結果是規則條文直接寫出的那一種（強制、可自願、不適用），
級距只檢查從分級表來源檔查出的值。
"""
from datetime import date

from app.db import to_dt
from tests.conftest import make_org

START = "2026-03-02"
LI, EI, OAI, NHI, LP = ("SCHEME.LABOR_INSURANCE_TW", "SCHEME.EMPLOYMENT_INSURANCE_TW",
                        "SCHEME.OCCUPATIONAL_ACCIDENT_INSURANCE_TW", "SCHEME.NATIONAL_HEALTH_INSURANCE_TW",
                        "SCHEME.LABOR_PENSION_TW")
M, V, NA = "APPLICABILITY.MANDATORY", "APPLICABILITY.VOLUNTARY", "APPLICABILITY.NOT_APPLICABLE"


def judge(api, org, ref, person: dict, base="32000", docs=()):
    h = org["hr"]
    hire = api("decideHire", h, expect=201, json={
        "employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
        "person": {"person": {"legal_name": "判定", **person}},
        "compensation": {"effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
                         "monthly_base_salary": base}}).json()
    for d in docs:
        api("recordIdentityDocument", h, path={"id": hire["person_id"]}, expect=201,
            json={"issuing_jurisdiction_id": str(ref["tw"]), **d})
    started = api("startEmployment", h, path={"id": hire["hire_id"]}, expect=201,
                  json={"start_date": START, "work_location_id": str(org["location"]),
                        "public_or_military_insurance_covered": False}).json()
    appl = api("getApplicability", h, path={"id": started["employment_id"]}, params={"on": START}, expect=200).json()
    return {i["scheme_code"]: i for i in appl["items"]}, appl


def national(ref, birth="1990-01-01", registered=True):
    p = {"birth_date": birth, "nationalities": [{"country_code": "TW", "acquired_on": birth}]}
    if registered:
        p["civil_registrations"] = [{"jurisdiction_id": str(ref["tw"]), "registered_on": birth}]
    return p


def test_r22_small_company_voluntary(api, db, ref):
    org = make_org(db, ref, name="小店", existing_employees=2)
    items, _ = judge(api, org, ref, national(ref))
    assert items[LI]["applicability"] == V                       # ② 第 2 款未滿 5 人
    assert {"EQ-004", "EQ-008"} <= set(items[LI]["pending"])
    assert items[LI]["expected_grade"]                           # 可自願也給級距


def test_r22_r24_over_65_not_applicable(api, db, ref):
    org = make_org(db, ref, existing_employees=12)
    items, _ = judge(api, org, ref, national(ref, birth="1959-01-01"))   # 判定日 67 歲
    assert items[LI]["applicability"] == NA                     # R22 ③
    assert items[EI]["applicability"] == NA                     # R24
    assert items[OAI]["applicability"] == M                     # R25 沒有年齡上限


def test_r25_without_registration(api, db, ref):
    org = make_org(db, ref, name="個人雇主", existing_employees=0, category="LI_INDUSTRY.NOT_LISTED_TW")
    db.employers.update_one({"_id": org["employer"]}, {"$set": {"registrations": []}})
    items, _ = judge(api, org, ref, national(ref))
    assert items[OAI]["applicability"] == NA                    # ⑤ 不適用；④ 公告範圍沒有資料
    assert items[OAI]["pending"] == ["EQ-023"]


def test_r25_public_sector_mandatory(api, db, ref):
    org = make_org(db, ref, name="學校", existing_employees=0, category="LI_INDUSTRY.LIA6_04_TW")
    db.employers.update_one({"_id": org["employer"]}, {"$set": {"registrations": []}})
    items, _ = judge(api, org, ref, national(ref))
    assert items[OAI]["applicability"] == M                     # ③ [解讀] 第 4 款


def test_r26_national_without_registration_or_residence(api, db, ref):
    org = make_org(db, ref, existing_employees=12)
    items, _ = judge(api, org, ref, national(ref, registered=False))
    assert items[NHI]["applicability"] == NA


def test_r24_r26_r27_foreign_employment_residence(api, db, ref):
    org = make_org(db, ref, existing_employees=12)
    items, _ = judge(api, org, ref, {"birth_date": "1995-05-05",
                                     "nationalities": [{"country_code": "VN", "acquired_on": "1995-05-05"}]},
                     docs=[{"document_kind": "DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW", "document_number": "X1",
                            "valid_from": "2026-01-01", "residence_basis": "RESIDENCE_BASIS.EMPLOYMENT_TW"}])
    assert items[LI]["applicability"] == M                      # ④ 外國籍也依 ①～③
    assert items[EI]["applicability"] == NA                     # 工作居留不適用就保
    assert items[NHI]["applicability"] == M                     # 有居留證明
    assert items[LP]["applicability"] == NA                     # R27 ④ 工作居留不適用勞退


def test_r60_missing_birth_date(api, db, ref):
    org = make_org(db, ref, existing_employees=12)
    items, appl = judge(api, org, ref, {"nationalities": [{"country_code": "TW", "acquired_on": "1990-01-01"}]})
    assert items[LI]["applicability"] == "APPLICABILITY.INSUFFICIENT_DATA"
    assert "Person.birth_date" in appl["missing_data"]


def test_r42_full_table_high_wage(api, db, ref):
    org = make_org(db, ref, existing_employees=12)
    items, _ = judge(api, org, ref, national(ref), base="126301")
    # 勞工退休金月提繳分級表（inputs/shared/…_115年1月1日.md）第 58 級：126,301 元至 131,700 元 → 131,700 元
    assert (items[LP]["expected_grade"], items[LP]["expected_amount"]) == ("58", "131700")
