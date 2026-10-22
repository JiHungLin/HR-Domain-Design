"""⑥ signoff 的設計問題回頭修改後（2026-10-22）：#12 R83、#15 C01、#16 遞延等扣回確認、#19 未來的結束日、#6 今天。

GC07～GC09 斷言的預期值取自 golden_cases.md（JiHungLin 計算，2026-10-22），測試不自行計算；
其餘斷言依設計（04 D-26～D-28、05 D-28、D-33）。
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bson import ObjectId

from app.leave import clock
from tests.leave_helpers import entitlements, hire, leave_org, on, run_day


def _six_months_year_ended(api, db, ref, used: str | None = None):
    """2025-03-02 到職、週年制；滿 6 個月那一筆（3 日）已休 used 日，2026-03-02 年度終結。"""
    org = leave_org(db, ref)
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")
    first = entitlements(api, org, emp)[0]
    if used:
        with on("2026-02-27"):
            api("loadUsedQuantityFixture", org["hr"], path={"id": first["entitlement_id"]}, expect=201,
                json={"used_quantity": used, "reason": "已休"})
    run_day(db, emp, "2026-03-02")
    return org, emp, first


def _six(api, org, ent_id) -> tuple:
    """黃金案例「要回答」的順序：額度、還可以休、已休、遞延出去、轉為工資、失效。"""
    e = api("getLeaveEntitlement", org["hr"], path={"id": ent_id}, expect=200).json()["entitlement"]
    q = e["quantities"]
    return (e["quantity"], q["remaining_quantity"], q["used_quantity"], q["deferred_out_quantity"],
            q["converted_quantity"], q["expired_quantity"])


def test_gc07_r83_after_year_end_compares_unused(api, db, ref):
    """#12：已年度終結的用「額度減已休」比（04 D-26），不再每次都成立。"""
    org, emp, first = _six_months_year_ended(api, db, ref, used="1")             # 未休 2，轉為工資 2
    h = org["hr"]
    with on("2026-03-10"):
        d = api("recordLeaveDeferral", h, expect=201, json={"entitlement_id": first["entitlement_id"],
                                                            "agreed_on": "2026-02-25", "deferred_quantity": "2"}).json()
    rules = [w["rule_id"] for w in d["warnings"]]
    assert "R83" not in rules and "R84" in rules
    with on("2026-03-12"):
        a = api("amendLeaveDeferral", h, path={"id": d["deferral_agreement_id"]}, expect=201,
                json={"agreed_on": "2026-03-11", "deferred_quantity": "3"}).json()
    rules = [w["rule_id"] for w in a["warnings"]]
    assert "R83" in rules and "R84" in rules


def test_gc08_c01_negative_until_confirmed(api, db, ref):
    """#15：年度終結後才補登已休，扣回待確認期間還可以休是負數（04 C01、D-28），確認後回到 0。"""
    org, emp, first = _six_months_year_ended(api, db, ref, used="1")
    h = org["hr"]
    with on("2026-04-01"):
        r = api("loadUsedQuantityFixture", h, path={"id": first["entitlement_id"]}, expect=201,
                json={"used_quantity": "2", "reason": "2026-02-27 特休漏登"}).json()
    conv = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Provisional"}, expect=200).json()["items"]
    assert [(c["quantity"], c["correction_cause"]) for c in conv] == [("-1", "CORRECTION_CAUSE.LATE_LEAVE_RECORDED")]
    with on("2026-04-05"):
        assert _six(api, org, first["entitlement_id"]) == ("3", "-1", "2", "0", "2", "0")
    with on("2026-04-10"):
        api("confirmLeaveConversion", h, path={"id": conv[0]["conversion_id"]}, expect=201, json={"reason": "扣回"})
        assert _six(api, org, first["entitlement_id"]) == ("3", "0", "2", "0", "1", "0")
    assert r["reassessment_notice_ids"]


def test_gc09_deferred_in_waits_for_confirmation(api, db, ref):
    """#16：年度終結後才登錄遞延協商，扣回確認前沒有可以休的遞延進來（04 R92、D-27；03_flows D-17）。"""
    org, emp, first = _six_months_year_ended(api, db, ref)                       # 未休 3，轉為工資 3
    h = org["hr"]
    with on("2026-03-10"):
        api("recordLeaveDeferral", h, expect=201, json={"entitlement_id": first["entitlement_id"],
                                                        "agreed_on": "2026-02-25", "deferred_quantity": "2"})
    conv = api("listLeaveConversions", h, params={"employment_id": emp, "status": "Provisional"}, expect=200).json()["items"]
    assert [c["quantity"] for c in conv] == ["-2"]
    with on("2026-03-15"):
        assert not [e for e in entitlements(api, org, emp) if e["origin"] == "ENTITLEMENT_ORIGIN.DEFERRED_IN"]
        assert _six(api, org, first["entitlement_id"]) == ("3", "0", "0", "0", "3", "0")
    with on("2026-03-20"):
        ok = api("confirmLeaveConversion", h, path={"id": conv[0]["conversion_id"]}, expect=201,
                 json={"reason": "已和薪資確認扣回"}).json()
        din = api("getLeaveEntitlement", h, path={"id": ok["deferred_in_entitlement_id"]}, expect=200).json()["entitlement"]
        assert _six(api, org, first["entitlement_id"]) == ("3", "0", "0", "2", "1", "0")
    assert (din["origin"], din["quantity"]) == ("ENTITLEMENT_ORIGIN.DEFERRED_IN", "2")
    assert (din["acquired_on"], din["valid_from"], din["valid_to"]) == ("2026-03-02", "2026-03-02", "2027-03-01")


def test_future_ending_fixture_waits_for_the_day(api, db, ref):
    """#19：結束日在未來時只記結束日，到那天由排程改為 Ended 並停止特休（05_mapping D-33）。"""
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    with on("2025-08-01"):
        api("loadEmploymentEndingFixture", h, path={"id": emp}, expect=201,
            json={"ended_on": "2025-09-30", "end_reason": "END_REASON.RESIGNATION", "reason": "提出離職"})
        again = api("loadEmploymentEndingFixture", h, path={"id": emp},
                    json={"ended_on": "2025-10-31", "end_reason": "END_REASON.RESIGNATION", "reason": "重複"})
    assert again.status_code == 409 and again.json()["message_code"] == "INVALID_STATE"
    run_day(db, emp, "2025-09-02")                                         # 結束日前取得，照樣給予、可以休
    first = entitlements(api, org, emp)[0]
    assert (first["acquired_on"], first["status"]) == ("2025-09-02", "Active")
    assert db.employments.find_one({"entity_id": ObjectId(emp), "is_current": True})["status"] == "Active"
    run_day(db, emp, "2025-09-30")                                         # 結束日那天
    assert db.employments.find_one({"entity_id": ObjectId(emp), "is_current": True})["status"] == "Ended"
    with on("2025-09-30"):
        assert entitlements(api, org, emp)[0]["status"] == "EndedWithEmployment"


def test_today_uses_employer_location(db, ref):
    """#6：今天依雇主所在地（P4）；台灣雇主用 Asia/Taipei，對照不到的用 UTC（[靜態替代]）。"""
    tw = {"jurisdiction_id": ref["tw"]}
    assert clock.today(db, tw) == datetime.now(ZoneInfo("Asia/Taipei")).date()
    assert clock.today(db, {}) == datetime.now(ZoneInfo("UTC")).date()
    with clock.fixed(date(2026, 1, 1)):
        assert clock.today(db, tw) == date(2026, 1, 1)
