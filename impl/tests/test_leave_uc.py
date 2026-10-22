"""annual-leave-grant 的 Use Case 與例外路徑（03_use_cases UC-02～UC-12；03_flows 的取消、撤回、更正）。

預期值依 04_rules 的規則推出（寫在每個斷言旁），不是黃金案例；黃金案例見 test_leave_gc.py。
"""
from bson import ObjectId

from app.leave import ledger as L
from app.leave import locks
from app.leave.ledger import Ctx
from tests.leave_helpers import entitlements, hire, leave_org, on, run_day


def _one(items, **match):
    out = [i for i in items if all(i.get(k) == v for k, v in match.items())]
    assert len(out) == 1, (match, items)
    return out[0]


# ---- UC-01：到職日在過去，到職的同一交易補上已到的給予與已過的年度終結（05_mapping D-04、X-04） ----

def test_uc01_start_in_past_catches_up_in_same_transaction(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    with on("2026-03-10"):
        hid = api("decideHire", h, expect=201, json={
            "employer_id": str(org["employer"]), "decided_on": "2025-02-20", "planned_start_date": "2025-03-02",
            "person": {"person": {"legal_name": "晚登錄的員工"}}}).json()["hire_id"]
        emp = api("startEmployment", h, path={"id": hid}, expect=201, json={
            "start_date": "2025-03-02", "work_location_id": str(org["location"]),
            "public_or_military_insurance_covered": False}).json()["employment_id"]
        items = entitlements(api, org, emp)
        conv = api("listLeaveConversions", h, params={"employment_id": emp}, expect=200).json()["items"]
    assert [(i["acquired_on"], i["status"]) for i in items] == [("2025-09-02", "YearEnded"), ("2026-03-02", "Active")]
    assert [(c["quantity"], c["status"]) for c in conv] == [("3", "Provisional")]     # 補做的年度終結待確認（R93）


# ---- UC-02 曆年制、UC-10 改用另一種特休年度 ----

def test_uc02_calendar_year_by_agreement(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-07-01")["employment_id"]
    with on("2025-07-01"):
        r = api("recordLeaveYearAgreement", h, expect=201, json={
            "employment_id": emp, "leave_type_code": "LEAVE_TYPE.ANNUAL_LEAVE_TW", "leave_year_basis": "LEAVE_YEAR_BASIS.FIXED_START",
            "year_start": {"month": 1, "day": 1}, "effective_from": "2025-07-01", "agreed_on": "2025-06-20"}).json()
        assert r["status"] == "Effective"
        basis = api("getLeaveYearBasis", h, path={"id": emp}, params={"on": "2025-12-01"}, expect=200).json()
        assert (basis["leave_year_basis"], basis["applied_by"], basis["leave_year_agreement_id"]) == \
            ("LEAVE_YEAR_BASIS.FIXED_START", "AGREEMENT", r["leave_year_agreement_id"])
        # R72：同一天不能有兩筆約定
        dup = api("recordLeaveYearAgreement", h, json={
            "employment_id": emp, "leave_type_code": "LEAVE_TYPE.ANNUAL_LEAVE_TW", "leave_year_basis": "LEAVE_YEAR_BASIS.ANNIVERSARY",
            "effective_from": "2025-07-01", "agreed_on": "2025-06-20"})
        assert dup.status_code == 409 and dup.json()["rule_id"] == "R72"
    run_day(db, emp, "2026-01-01")
    e = entitlements(api, org, emp, on="2026-01-01")[0]
    # R65 取得日 2026-01-01；R70 迄日：週年制迄日 2026-06-30 所在年度的最後一天
    assert (e["acquired_on"], e["quantity"], e["valid_to"], e["leave_year_basis"]) == \
        ("2026-01-01", "3", "2026-12-31", "LEAVE_YEAR_BASIS.FIXED_START")
    assert e["applied_year_agreement_id"] == r["leave_year_agreement_id"]

    # UC-10 例外：回到預設（終止約定），終止日早於已給予的取得日 → 同一交易重新判定（R75）
    with on("2026-02-01"):
        end = api("endLeaveYearAgreement", h, path={"id": r["leave_year_agreement_id"]}, expect=201,
                  json={"ended_from": "2025-12-31", "agreed_on": "2026-02-01"}).json()
    assert end["status"] == "Ended" and len(end["reassessment_notice_ids"]) == 1
    e = entitlements(api, org, emp, on="2026-02-01")[0]
    assert (e["valid_to"], e["leave_year_basis"]) == ("2026-06-30", "LEAVE_YEAR_BASIS.ANNIVERSARY")


def test_uc10_retroactive_agreement_reassesses_in_place(api, db, ref):
    org = leave_org(db, ref)
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    before = entitlements(api, org, emp)[0]
    with on("2025-10-01"):
        r = api("recordLeaveYearAgreement", org["hr"], expect=201, json={
            "employment_id": emp, "leave_type_code": "LEAVE_TYPE.ANNUAL_LEAVE_TW", "leave_year_basis": "LEAVE_YEAR_BASIS.FIXED_START",
            "year_start": {"month": 1, "day": 1}, "effective_from": "2025-03-02", "agreed_on": "2025-09-30"}).json()
        n = api("getLeaveReassessmentNotice", org["hr"], path={"id": r["reassessment_notice_ids"][0]}, expect=200).json()
        after = entitlements(api, org, emp)[0]
    # R75：同一期別、期間重疊 → 就地更正可休期間，同一筆
    assert after["entitlement_id"] == before["entitlement_id"] and after["valid_to"] == "2026-12-31"
    assert n["changed"][0]["before"]["valid_to"] == "2026-03-01" and n["root_event_id"] == r["event_id"]


# ---- UC-03 公司規定多給 ----

def test_uc03_company_extra_and_retroactive_policy(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2026-03-02")                                    # 補上滿 6 個月與滿 1 年
    assert len(entitlements(api, org, emp)) == 2
    with on("2026-04-01"):
        p = api("establishCompanyPolicy", org["boss"], expect=201, json={
            "employer_id": str(org["employer"]), "leave_type_code": "LEAVE_TYPE.ANNUAL_LEAVE_TW", "name": "滿一年多給 2 天",
            "subject": "POLICY_SUBJECT.ANNUAL_LEAVE_EXTRA", "source_note": "工作規則第 12 條", "effective_from": "2025-01-01",
            "first_version": {"company_extra_days": [{"from_months": 12, "days": "2"}]}}).json()
    # D-18：生效日早於已給予的取得日 → 經佇列重新判定
    assert p["status"] == "Effective" and p["reassessment_queued"] == 1
    with on("2026-04-01"):
        assert api("listLeaveEntitlements", h, path={"id": emp}, expect=200).json()["reassessment_pending"] is True
    locks.drain(db)
    with on("2026-04-01"):
        items = entitlements(api, org, emp)
        notices = api("listLeaveReassessmentNotices", h, params={"root_event_id": p["event_id"]}, expect=200).json()["items"]
    extra = _one(items, source="ENTITLEMENT_SOURCE.COMPANY_POLICY")
    # R77：同一天另成一筆，可休期間同法定那一筆，連到那條規定、記下版本
    assert (extra["acquired_on"], extra["quantity"], extra["valid_to"], extra["policy_id"]) == \
        ("2026-03-02", "2", "2027-03-01", p["policy_id"])
    assert any(r["kind"] == "COMPANY_POLICY" and r["version"] == "v1" for r in extra["basis_rule_versions"])
    assert notices and extra["entitlement_id"] in notices[0]["added_ids"]

    # R78：公司規定少於法定只警告，照法定給
    with on("2026-04-01"):
        bad = api("establishCompanyPolicy", h, expect=201, json={
            "employer_id": str(org["employer"]), "name": "打錯的規定", "subject": "POLICY_SUBJECT.ANNUAL_LEAVE_EXTRA",
            "effective_from": "2027-01-01", "first_version": {"company_extra_days": [{"from_months": 12, "days": "-2"}]}}).json()
        assert [w["rule_id"] for w in bad["warnings"]] == ["R78"] and bad["status"] == "Scheduled"
        detail = api("getCompanyPolicy", h, path={"id": bad["policy_id"]}, expect=200).json()
        assert detail["warnings"][0]["rule_id"] == "R78"


# ---- UC-05 協商遞延、UC-06 遞延進來的到次一年度終結 ----

def test_uc05_uc06_deferral(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    first = entitlements(api, org, emp)[0]
    with on("2026-02-20"):
        # 只有人資可以登錄遞延協商
        assert api("recordLeaveDeferral", org["boss"], json={
            "entitlement_id": first["entitlement_id"], "agreed_on": "2026-02-20", "deferred_quantity": "2"}).status_code == 403
        # R82：超過那一筆的額度擋下
        r = api("recordLeaveDeferral", h, json={"entitlement_id": first["entitlement_id"], "agreed_on": "2026-02-20",
                                                "deferred_quantity": "4"})
        assert r.status_code == 409 and r.json()["rule_id"] == "R82"
        d = api("recordLeaveDeferral", h, expect=201, json={"entitlement_id": first["entitlement_id"],
                                                            "agreed_on": "2026-02-20", "deferred_quantity": "1"}).json()
        assert d["status"] == "Agreed" and d["warnings"] == []
        # UC-05 例外：重新協商
        a = api("amendLeaveDeferral", h, path={"id": d["deferral_agreement_id"]}, expect=201,
                json={"agreed_on": "2026-02-20", "deferred_quantity": "2"}).json()
        assert a["status"] == "Agreed"
    run_day(db, emp, "2026-03-02")
    with on("2026-03-02"):
        detail = api("getLeaveEntitlement", h, path={"id": first["entitlement_id"]}, expect=200).json()
    j = detail["year_end_judgments"][0]
    # R86：遞延 2、其餘 1 轉為工資；遞延進來那一筆（R87）
    assert j["deferred_in_quantity"] == "2" and [c["quantity"] for c in detail["conversions"]] == ["1"]
    din = api("getLeaveEntitlement", h, path={"id": j["deferred_in_entitlement_id"]}, expect=200).json()["entitlement"]
    assert (din["origin"], din["quantity"], din["valid_from"], din["valid_to"], din["deferred_from_id"]) == \
        ("ENTITLEMENT_ORIGIN.DEFERRED_IN", "2", "2026-03-02", "2027-03-01", first["entitlement_id"])
    assert detail["entitlement"]["quantities"]["deferred_out_quantity"] == "2"
    assert detail["deferral_agreements"][0]["status"] == "Applied"

    # UC-06 例外：遞延進來的那一筆不能再遞延（R82、R88）
    with on("2026-06-01"):
        r = api("recordLeaveDeferral", h, json={"entitlement_id": din["entitlement_id"], "agreed_on": "2026-06-01",
                                                "deferred_quantity": "1"})
        assert r.status_code == 409 and r.json()["rule_id"] == "R82"
    # UC-06：到次一年度終結仍沒休 → 全部轉為工資，工資計算基準日是原來那一筆的年度終結日（R89）
    run_day(db, emp, "2027-03-02")
    convs = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Determined"}, expect=200).json()["items"]
    c = _one(convs, entitlement_id=din["entitlement_id"])
    assert (c["quantity"], c["wage_basis_date"], c["payment_due_on"]) == ("2", "2026-03-01", "2027-03-31")


def test_withdraw_deferral_after_year_end_rejudges(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    first = entitlements(api, org, emp)[0]
    run_day(db, emp, "2026-03-02")                                    # 沒有協商 → 轉為工資 3
    with on("2026-03-10"):
        # 年度終結後才登錄的協商 → Applied，同一交易重新判定；R84 提醒
        d = api("recordLeaveDeferral", h, expect=201, json={"entitlement_id": first["entitlement_id"],
                                                            "agreed_on": "2026-02-25", "deferred_quantity": "2"}).json()
        assert d["status"] == "Applied" and "R84" in [w["rule_id"] for w in d["warnings"]]
        n = api("getLeaveReassessmentNotice", h, path={"id": d["reassessment_notice_ids"][0]}, expect=200).json()
        # 要扣回已判定的轉換 → 遞延進來那一筆等確認後才建立（04 R92、D-27）
        assert n["added_ids"] == [] and len(n["provisional_conversion_ids"]) == 1
        neg = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Provisional"}, expect=200).json()["items"]
        assert [(c["quantity"], c["correction_cause"]) for c in neg] == [("-2", "CORRECTION_CAUSE.DEFERRAL_CHANGED")]
        # 撤回 → 遞延進來那一筆作廢，待確認的負數差額被取代
        w = api("withdrawLeaveDeferral", h, path={"id": d["deferral_agreement_id"]}, expect=201,
                json={"reason": "員工改變心意"}).json()
        assert w["status"] == "Withdrawn"
        r = api("confirmLeaveConversion", h, path={"id": neg[0]["conversion_id"]}, json={"reason": "確認"})
        # 重算後差額為 0、沒有取代它的那一筆 → Superseded，discarded_by_id 為 null（05_mapping D-23）
        assert r.status_code == 409 and r.json() == {"message_code": "CONVERSION_DISCARDED", "discarded_by_id": None}
        detail = api("getLeaveEntitlement", h, path={"id": first["entitlement_id"]}, expect=200).json()
    assert detail["entitlement"]["quantities"]["converted_quantity"] == "3"
    assert detail["entitlement"]["quantities"]["deferred_out_quantity"] == "0"


# ---- UC-07 補登 ----

def test_uc07_backfill_then_rule_grants(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2023-03-02")["employment_id"]
    body = {"employment_id": emp, "leave_type_code": "LEAVE_TYPE.ANNUAL_LEAVE_TW", "source": "ENTITLEMENT_SOURCE.STATUTORY",
            "origin": "ENTITLEMENT_ORIGIN.REGISTERED_CURRENT", "quantity": "7", "unit": "LEAVE_UNIT.DAY",
            "pre_system_used_quantity": "3", "valid_from": "2024-03-02", "valid_to": "2025-03-01"}
    with on("2025-01-02"):
        # R97：可休迄日早於開始由系統管理的日子擋下
        bad = api("registerExistingLeaveEntitlement", h, json={**body, "valid_to": "2024-12-31"})
        assert bad.status_code == 409 and bad.json()["rule_id"] == "R97"
        b = api("registerExistingLeaveEntitlement", h, expect=201, json=body).json()
    run_day(db, emp, "2025-03-02")
    items = entitlements(api, org, emp, on="2025-03-02")
    reg = _one(items, entitlement_id=b["entitlement_id"])
    rule = _one(items, origin="ENTITLEMENT_ORIGIN.RULE_GRANT")
    # 補登的那筆年度終結：未休 7－3＝4 轉為工資；之後依年資由系統給予（滿 2 年 10 日）
    assert reg["status"] == "YearEnded" and reg["quantities"]["converted_quantity"] == "4" and reg["no_rule_version"] is True
    assert (rule["acquired_on"], rule["quantity"], rule["seniority_tier"]) == ("2025-03-02", "10", 24)
    assert reg["notice_status"] == "NOT_APPLICABLE"                       # R80：補登的不判定告知


# ---- UC-09 離職 ----

def test_uc09_leave_before_six_months_gets_nothing(api, db, ref):
    org = leave_org(db, ref)
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    with on("2025-07-01"):
        api("loadEmploymentEndingFixture", org["hr"], path={"id": emp}, expect=201,
            json={"ended_on": "2025-06-30", "end_reason": "END_REASON.RESIGNATION", "reason": "離職"})
    run_day(db, emp, "2026-03-02")
    assert entitlements(api, org, emp) == []                              # R67：結束日早於取得日 → 從未取得


def test_uc09_end_learned_late_voids_and_reverses(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    run_day(db, emp, "2026-03-02")                                        # 第一筆年度終結轉為工資 3；滿 1 年那一筆
    with on("2026-03-10"):
        r = api("loadEmploymentEndingFixture", h, path={"id": emp}, expect=201,
                json={"ended_on": "2026-02-15", "end_reason": "END_REASON.RESIGNATION", "reason": "較晚才得知離職"}).json()
        n = api("getLeaveReassessmentNotice", h, path={"id": r["reassessment_notice_ids"][0]}, expect=200).json()
        all_items = api("getLeaveEntitlement", h, path={"id": n["voided_ids"][0]}, expect=200).json()["entitlement"]
        items = entitlements(api, org, emp)
    # R95：滿 1 年那一筆取得日晚於結束日 → 作廢；第一筆那次年度終結當作沒有發生 → 交給契約終止，轉換記負數差額（待確認）
    assert all_items["acquired_on"] == "2026-03-02" and all_items["status"] == "Voided"
    first = _one(items, acquired_on="2025-09-02")
    assert first["status"] == "EndedWithEmployment"
    conv = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Provisional"}, expect=200).json()["items"]
    assert [(c["quantity"], c["correction_cause"]) for c in conv] == [("-3", "CORRECTION_CAUSE.LATE_TERMINATION_KNOWN")]
    assert n["provisional_conversion_ids"] == [conv[0]["conversion_id"]]
    # UC-09 例外：人資確認
    with on("2026-03-11"):
        ok = api("confirmLeaveConversion", h, path={"id": conv[0]["conversion_id"]}, expect=201, json={"reason": "已和薪資確認"}).json()
    assert ok["status"] == "Determined"


# ---- UC-11 可能應合併年資 ----

def test_uc11_possible_seniority_merge_warning(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    first = hire(api, org, ref, "2025-01-02", name="回任員工")
    with on("2025-04-01"):
        api("loadEmploymentEndingFixture", h, path={"id": first["employment_id"]}, expect=201,
            json={"ended_on": "2025-03-31", "end_reason": "END_REASON.CONTRACT_EXPIRED", "reason": "定期契約屆滿"})
    with on("2025-06-01"):
        hid = api("decideHire", h, expect=201, json={
            "employer_id": str(org["employer"]), "decided_on": "2025-06-01", "planned_start_date": "2025-06-01",
            "person": {"person_id": first["person_id"]}}).json()["hire_id"]
        second = api("startEmployment", h, path={"id": hid}, expect=201, json={
            "start_date": "2025-06-01", "work_location_id": str(org["location"]),
            "public_or_military_insurance_covered": False}).json()
        w = api("listLeaveWarnings", h, path={"id": second["employment_id"]}, expect=200).json()["items"]
    r99 = [x["warning"] for x in w if x["warning"]["rule_id"] == "R99"]
    assert len(r99) == 1 and r99[0]["warned_value"]["previous_employment_id"] == first["employment_id"]


# ---- UC-12 年度終結之後才改變的資料 ----

def test_uc12_used_quantity_after_year_end(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    first = entitlements(api, org, emp)[0]
    run_day(db, emp, "2026-03-02")
    with on("2026-03-20"):
        r = api("loadUsedQuantityFixture", h, path={"id": first["entitlement_id"]}, expect=201,
                json={"used_quantity": "1", "reason": "年度終結後才補登的請假"}).json()
        n = api("getLeaveReassessmentNotice", h, path={"id": r["reassessment_notice_ids"][0]}, expect=200).json()
        c = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Provisional"}, expect=200).json()["items"][0]
        # R92：差額 -1，待確認（R93），指回原判定的轉換
        assert (c["quantity"], c["correction_cause"]) == ("-1", "CORRECTION_CAUSE.LATE_LEAVE_RECORDED")
        assert c["corrects_conversion_id"] and n["provisional_conversion_ids"] == [c["conversion_id"]]
        api("confirmLeaveConversion", h, path={"id": c["conversion_id"]}, expect=201, json={"reason": "會從下期薪資扣回"})
        q = api("getLeaveEntitlement", h, path={"id": first["entitlement_id"]}, expect=200).json()["entitlement"]["quantities"]
    assert (q["used_quantity"], q["converted_quantity"], q["remaining_quantity"]) == ("1", "2", "0")   # C01


def test_late_year_end_is_provisional_and_superseded(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    first = entitlements(api, org, emp)[0]
    run_day(db, emp, "2026-03-10")                                        # 排程延誤：補做的年度終結 → 待確認（R93、04 D-20）
    with on("2026-03-10"):
        c = api("listLeaveConversions", h, params={"employment_id": emp}, expect=200).json()["items"]
        assert [(x["quantity"], x["status"]) for x in c] == [("3", "Provisional")]
        work = api("listLeaveWorkItems", h, params={"employer_id": str(org["employer"])}, expect=200).json()["items"]
        assert {"kind": "PROVISIONAL_CONVERSION", "employment_id": emp, "conversion_id": c[0]["conversion_id"]} in work
        api("loadUsedQuantityFixture", h, path={"id": first["entitlement_id"]}, expect=201,
            json={"used_quantity": "1", "reason": "補登已休"})
        r = api("confirmLeaveConversion", h, path={"id": c[0]["conversion_id"]}, json={"reason": "確認"})
    # 已被取代：409，給取代它的那一筆
    assert r.status_code == 409 and r.json()["message_code"] == "CONVERSION_DISCARDED"
    new = api("getLeaveEntitlement", h, path={"id": first["entitlement_id"]}, expect=200).json()["conversions"]
    assert r.json()["discarded_by_id"] == _one(new, status="Determined")["conversion_id"]


# ---- 告知（UC-04 例外）與權限 ----

def test_uc04_notice_guards_and_overdue_warning(api, db, ref, ):
    org = leave_org(db, ref)
    other = leave_org(db, ref, name="別家公司")
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    e = entitlements(api, org, emp)[0]
    with on("2025-10-03"):
        w = api("listLeaveWarnings", h, path={"id": emp}, expect=200).json()["items"]
        assert [x["warning"]["message_code"] for x in w] == ["NOTICE_OVERDUE"]          # R81：逾期未告知
        # R98：告知日不能晚於登錄當天
        r = api("recordLeaveNotice", h, path={"id": e["entitlement_id"]}, json={"notified_on": "2025-10-04"})
        assert r.status_code == 409 and r.json()["rule_id"] == "R98"
        n = api("recordLeaveNotice", h, path={"id": e["entitlement_id"]}, expect=201, json={"notified_on": "2025-10-03"}).json()
        assert n["notice_status"] == "NOTICE_STATUS.NOTIFIED_LATE" and n["warnings"][0]["message_code"] == "NOTICE_LATE"
        # 已有告知日的不能再登錄（只能由人資更正）
        assert api("recordLeaveNotice", org["boss"], path={"id": e["entitlement_id"]},
                   json={"notified_on": "2025-10-03"}).status_code == 409
        # 別的客戶看不到
        assert api("getLeaveEntitlement", other["hr"], path={"id": e["entitlement_id"]}).status_code == 403
        assert api("listLeaveTypes", h, expect=200).json()["items"][0]["code"] == "LEAVE_TYPE.ANNUAL_LEAVE_TW"


# ---- P9：守恆式在所有測試資料上成立 ----

def test_zz_conservation_on_all_data(db):
    """C01、C02 在這次測試建立的每一筆沒有作廢的請假權利上都成立（檔名排序最後跑）。"""
    ents = list(db[L.ENT].find({"is_current": True, "voided": False}))
    assert ents
    for e in ents:
        L.check_conservation(Ctx(db, None, e["tenant_id"], None), e["entity_id"])
    # 每一筆依規則給予的，同一期別、同一來源只有一筆有效（05_mapping 3.1 的唯一索引）
    keys = [(e["employment_id"], e["source"], e.get("policy_id"), e.get("period_sequence"))
            for e in ents if e["origin"] == "ENTITLEMENT_ORIGIN.RULE_GRANT"]
    assert len(keys) == len(set(keys))
    assert ObjectId  # noqa: B018
