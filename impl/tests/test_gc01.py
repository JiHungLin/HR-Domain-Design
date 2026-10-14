"""GC01 正常流程：本國籍月薪員工準時到職、當天加保（slices/hire-employee/06_evidence/golden_cases.md）。

流程照 05_mapping 第六區 UC-01～UC-03：每一步只用使用者輸入、參考資料，與前一步回應的欄位。
預期結果取自 golden_cases.md，由 JiHungLin 計算（2026-10-14）；測試不自行計算預期值。
前提：伙食津貼算入月薪資總額（EQ-012）、健保與勞退的生效日為到職日（EQ-003），兩者待專家確認。
"""
from app.seed import EI, LI, LP, NHI, OAI

START = "2026-03-02"
# golden_cases.md GC01 預期結果
EXPECTED_APPLICABILITY = "APPLICABILITY.MANDATORY"                    # 1. 全數強制
EXPECTED_DEADLINE = {LI: START, EI: START, OAI: START,                # 2. 應辦理期限
                     NHI: "2026-03-05", LP: "2026-03-09"}             #    健保寬限 3 日（始日不算入）、勞退 7 日
EXPECTED_EFFECTIVE = START                                            # 2. 五項都在到職當日生效
EXPECTED_DAYS_LATE = 0                                                # 2. 晚辦 0 天
EXPECTED_AMOUNT = "34800"                                             # 3. 五項都申報 34,800


def uc01(api, org, ref, *, employee_number="E013", base="32000", allowances=None):
    """UC-01 第 2（含 1）、1、4、5 步。回傳各步的回應。"""
    h = org["hr"]
    if allowances is None:
        allowances = [{"name": "伙食津貼", "category": "ALLOWANCE_CATEGORY.MEAL", "amount": "2400"}]
    # 第 2 步：錄用，一併帶人、約定薪資、契約
    hire = api("decideHire", h, expect=201, json={
        "employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
        "planned_work_location_id": str(org["location"]),
        "person": {"person": {"legal_name": "GC01 新人", "birth_date": "1997-08-15",
                              "nationalities": [{"country_code": "TW", "acquired_on": "1997-08-15"}],
                              "civil_registrations": [{"jurisdiction_id": str(ref["tw"]), "registered_on": "1997-08-15"}]}},
        "compensation": {"effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
                         "monthly_base_salary": base, "fixed_monthly_allowances": allowances},
        "contract": {"contract_type": "CONTRACT_TYPE.INDEFINITE", "term_start": START, "in_writing": True}}).json()
    # 第 1 步：用第 2 步回應的 person_id 登錄身分證件
    api("recordIdentityDocument", h, path={"id": hire["person_id"]}, expect=201, json={
        "document_kind": "DOCUMENT_KIND.NATIONAL_ID_TW", "issuing_jurisdiction_id": str(ref["tw"]),
        "document_number": "A123456789", "valid_from": "2015-01-01"})
    # 第 4 步：錄用時產生的加保待辦
    pre = api("listEnrollmentProposals", h, params={"hire_id": hire["hire_id"]}, expect=200).json()
    # 第 5 步：登錄到職
    started = api("startEmployment", h, path={"id": hire["hire_id"]}, expect=201, json={
        "start_date": START, "work_location_id": str(org["location"]), "employee_number": employee_number}).json()
    return hire, pre, started


def test_gc01(api, org, ref):
    h = org["hr"]
    hire, pre, started = uc01(api, org, ref)
    assert "compensation_id" in hire and "contract_id" in hire
    assert started["compensation_ids"] == [hire["compensation_id"]]
    assert started["contract_ids"] == [hire["contract_id"]]

    # 4. 不出現低於最低工資的警告（錄用時與到職時）
    assert not [w for w in hire["warnings"] + started["warnings"] if w["rule_id"] == "R11"]

    # UC-01 第 4 步：錄用時就有加保待辦；到職後被到職時的判定取代
    assert len(pre["items"]) == 1 and pre["items"][0]["determined_on"] == START
    props = api("listEnrollmentProposals", h, params={"hire_id": hire["hire_id"]}).json()["items"]
    assert props[0]["superseded_by"] == started["enrollment_proposal_id"]

    # UC-02：到職時的加保待辦
    [prop] = api("listEnrollmentProposals", h, params={"employment_id": started["employment_id"], "open": True}).json()["items"]
    assert prop["enrollment_proposal_id"] == started["enrollment_proposal_id"]
    items = {i["scheme_code"]: i for i in prop["items"]}
    for code in (LI, EI, OAI, NHI, LP):
        assert items[code]["applicability"] == EXPECTED_APPLICABILITY, code
        assert items[code]["filing_deadline"] == EXPECTED_DEADLINE[code], code
        assert items[code]["expected_amount"] == EXPECTED_AMOUNT, code      # 3.
        assert "EQ-012" in items[code]["pending"]
    for code in (LI, EI, OAI):
        assert items[code]["legal_effective_date"] == EXPECTED_EFFECTIVE, code
    for code in (NHI, LP):   # 法定生效日 [待專家確認: EQ-003]：系統不給值，標出待確認
        assert "legal_effective_date" not in items[code]
        assert "EQ-003" in items[code]["pending"]

    # UC-03：五項都在到職當日辦理，保險人核定生效日 2026-03-02
    for code in (LI, EI, OAI, NHI, LP):
        unit = org["units"]["NHIA" if code == NHI else "BLI"]
        enr = api("recordInsuranceFiling", h, expect=201, json={
            "employment_id": started["employment_id"], "scheme_id": str(ref["schemes"][code]),
            "insurance_unit_id": str(unit), "filed_on": START, "voluntary": False, "effective_from": START,
            "receipt_ref": f"GC01-{code}"}).json()
        assert enr["enrollment_proposal_id"] == prop["enrollment_proposal_id"]
        sal = api("declareInsuredSalary", h, path={"id": enr["enrollment_id"]}, expect=201, json={
            "declared_amount": EXPECTED_AMOUNT, "grade": items[code]["expected_grade"], "declared_on": START,
            "effective_from": START}).json()
        assert sal["enrollment_id"] == enr["enrollment_id"]
        assert sal["warnings"] == []          # R45：申報級距與應申報級距相同

    # UC-03 第 3 步：晚辦天數
    appl = api("getApplicability", h, path={"id": started["employment_id"]}, params={"on": START}, expect=200).json()
    late = {i["scheme_code"]: i.get("days_late") for i in appl["items"]}
    for code in (LI, EI, OAI):
        assert late[code] == EXPECTED_DAYS_LATE, code
    for code in (NHI, LP):   # 法定生效日待確認的制度不算晚辦天數（R35）
        assert late[code] is None

    # 全部結案後不再列為未處理
    assert api("listEnrollmentProposals", h, params={"employment_id": started["employment_id"], "open": True}).json()["items"] == []
