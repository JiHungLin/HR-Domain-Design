"""GC01 正常流程：本國籍月薪員工準時到職、當天加保（slices/hire-employee/06_evidence/golden_cases.md）。

預期結果取自 golden_cases.md，由 JiHungLin 計算（2026-10-14）；測試不自行計算預期值。
前提：伙食津貼算入月薪資總額（EQ-012）、健保與勞退的生效日為到職日（EQ-003），兩者待專家確認。
"""
from app.seed import EI, LI, LP, NHI, OAI

START = "2026-03-02"
# golden_cases.md GC01 預期結果
EXPECTED_APPLICABILITY = "APPLICABILITY.MANDATORY"                    # 1. 全數強制
EXPECTED_DEADLINE = {LI: START, EI: START, OAI: START,                # 2. 期限
                     NHI: "2026-03-05", LP: "2026-03-09"}             #    （紙上推演；健保始日不算入，使用者於 GC03 複核）
EXPECTED_EFFECTIVE = START                                            # 2. 五項都追溯至到職日
EXPECTED_DAYS_LATE = 0                                                # 2. 晚辦 0 天
EXPECTED_AMOUNT = 34800                                               # 3. 五項都申報 34,800


def gc01_flow(client, org, ref):
    h = org["hr"]
    r = client.post("/v1/hires", headers=h, json={
        "employer_id": str(org["employer"]), "decided_on": "2026-02-16", "planned_start_date": START,
        "person": {"legal_name": "GC01 新人", "birth_date": "1997-08-15",
                   "nationalities": [{"country_code": "TW", "acquired_on": "1997-08-15"}],
                   "civil_registrations": [{"jurisdiction_id": str(ref["tw"]), "registered_on": "1997-08-15"}]}})
    assert r.status_code == 201, r.text
    hire = r.json()
    r = client.post(f"/v1/persons/{hire['person_id']}/identity-documents", headers=h, json={
        "document_kind": "DOCUMENT_KIND.NATIONAL_ID_TW", "issuing_jurisdiction_id": str(ref["tw"]),
        "document_number": "A123456789", "valid_from": "2015-01-01"})
    assert r.status_code == 201, r.text
    r = client.post("/v1/compensations", headers=h, json={
        "hire_id": hire["entity_id"], "effective_from": START, "currency": "TWD", "pay_basis": "PAY_BASIS.MONTHLY",
        "monthly_base_salary": "32000",
        "fixed_monthly_allowances": [{"name": "伙食津貼", "category": "ALLOWANCE_CATEGORY.MEAL", "amount": "2400"}]})
    assert r.status_code == 201, r.text
    comp_warnings = r.json()["warnings"]
    r = client.post("/v1/employment-contracts", headers=h, json={
        "hire_id": hire["entity_id"], "contract_type": "CONTRACT_TYPE.INDEFINITE", "term_start": START, "in_writing": True})
    assert r.status_code == 201, r.text
    r = client.post(f"/v1/hires/{hire['entity_id']}/start", headers=h, json={"start_date": START, "employee_number": "E013"})
    assert r.status_code == 201, r.text
    return hire, r.json(), comp_warnings


def test_gc01(client, org, ref):
    h = org["hr"]
    hire, started, comp_warnings = gc01_flow(client, org, ref)

    # 4. 不出現低於最低工資的警告
    assert not [w for w in comp_warnings + started["warnings"] if w["rule_id"] == "R11"]

    # UC-02：加保待辦
    props = client.get("/v1/enrollment-proposals?status=open", headers=h).json()
    [prop] = [p for p in props if p["employment_id"] == started["entity_id"]]
    items = {i["scheme_code"]: i for i in prop["items"]}
    assert prop["basis"]["headcount"] == 13
    for code in (LI, EI, OAI, NHI, LP):
        assert items[code]["applicability"] == EXPECTED_APPLICABILITY, code
        assert items[code]["filing_deadline"] == EXPECTED_DEADLINE[code], code
    for code in (LI, EI, OAI):
        assert items[code]["legal_effective_date"] == EXPECTED_EFFECTIVE, code
    for code in (NHI, LP):   # 法定生效日 [待專家確認: EQ-003]：系統不給值，標出待確認
        assert "legal_effective_date" not in items[code]
        assert any("EQ-003" in p for p in prop["basis"]["pending"][code])

    # 投保薪資級距（UC-02 判定查詢）
    appl = client.get(f"/v1/employments/{started['entity_id']}/applicability?on={START}", headers=h).json()
    for it in appl["items"]:
        assert it["expected_amount"] == EXPECTED_AMOUNT, it["scheme_code"]
        assert "EQ-012" in it["pending"]

    # UC-03：五項都在到職當日辦理，保險人核定生效日 2026-03-02
    for code in (LI, EI, OAI, NHI, LP):
        unit = org["units"]["NHIA" if code == NHI else "BLI"]
        r = client.post("/v1/insurance-enrollments", headers=h, json={
            "employment_id": started["entity_id"], "scheme_id": str(ref["schemes"][code]),
            "insurance_unit_id": str(unit), "filed_on": START, "effective_from": START, "receipt_ref": f"GC01-{code}"})
        assert r.status_code == 201, r.text
        res = r.json()
        assert res["effective_from"] == EXPECTED_EFFECTIVE
        if code in (LI, EI, OAI):
            assert res["days_late"] == EXPECTED_DAYS_LATE
        else:   # 法定生效日待確認的制度不算晚辦天數（R35）
            assert res["days_late"] is None
        grade = appl["items"][[i["scheme_code"] for i in appl["items"]].index(code)]["expected_grade"]
        r = client.post(f"/v1/insurance-enrollments/{res['entity_id']}/insured-salaries", headers=h, json={
            "declared_amount": str(EXPECTED_AMOUNT), "grade": grade, "declared_on": START, "effective_from": START})
        assert r.status_code == 201, r.text
        assert r.json()["warnings"] == []          # R45：申報級距與應申報級距相同

    # 全部結案後不再列為未處理
    assert not [p for p in client.get("/v1/enrollment-proposals?status=open", headers=h).json()
                if p["employment_id"] == started["entity_id"]]
