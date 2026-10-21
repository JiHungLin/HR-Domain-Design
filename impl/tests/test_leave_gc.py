"""annual-leave-grant 黃金案例 GC01、GC04、GC06（slices/annual-leave-grant/06_evidence/golden_cases.md）。

流程照 05_mapping 第六區：每一步只用使用者輸入、參考資料，與前一步回應的欄位；排程（GrantLeaveEntitlement、
CloseLeaveYear）用 scheduler.process_employment 在指定的「今天」執行。
預期結果取自 golden_cases.md，由 JiHungLin 計算（2026-10-21）；測試不自行計算預期值。
GC02、GC03、GC05 沒有被挑選（不採用），不測。
"""
from datetime import datetime, timezone

from bson import ObjectId

from tests.leave_helpers import entitlements, hire, leave_org, on, run_day


def _by_acq(items):
    return {i["acquired_on"]: i for i in items}


def test_gc01_anniversary_notice_and_year_end(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]

    # UC-01 第 1 步：預估
    with on("2025-03-02"):
        fc = api("getLeaveForecast", h, path={"id": emp}, params={"until": "2026-04-10"}, expect=200).json()
    assert [i["expected_acquired_on"] for i in fc["items"]] == ["2025-09-02", "2026-03-02"]

    # UC-01 第 2 步：排程給予；UC-04：告知
    run_day(db, emp, "2025-09-02")
    with on("2025-09-20"):
        first = entitlements(api, org, emp)[0]
        api("recordLeaveNotice", org["boss"], path={"id": first["entitlement_id"]}, expect=201,
            json={"notified_on": "2025-09-20", "evidence": [{"kind": "電子郵件"}]})
    # 滿 6 個月那一筆已休 1 日（固定資料 [靜態替代]）
    with on("2026-02-27"):
        api("loadUsedQuantityFixture", h, path={"id": first["entitlement_id"]}, expect=201,
            json={"used_quantity": "1", "reason": "GC01：滿 6 個月那一筆已休 1 日"})
    # UC-05 第 3 步：排程年度終結（可休迄日過完的隔天），同一天給予滿 1 年那一筆
    run_day(db, emp, "2026-03-02")

    with on("2026-04-10"):
        items = _by_acq(entitlements(api, org, emp, on="2026-04-10"))
        detail = api("getLeaveEntitlement", h, path={"id": first["entitlement_id"]}, expect=200).json()

    # ① 查詢日時有兩筆特休
    assert set(items) == {"2025-09-02", "2026-03-02"}
    a, b = items["2025-09-02"], items["2026-03-02"]
    assert (a["quantity"], a["valid_from"], a["valid_to"], a["status"]) == ("3", "2025-09-02", "2026-03-01", "YearEnded")
    assert (b["quantity"], b["valid_from"], b["valid_to"], b["status"]) == ("7", "2026-03-02", "2027-03-01", "Active")
    # ② 告知期限 2025-10-02；2025-09-20 告知，期限內
    assert a["notice_due_on"] == "2025-10-02"
    assert a["notice_status"] == "NOTICE_STATUS.NOTIFIED"
    # ③ 轉為工資 2 日；工資計算基準日 2026-03-01；發給期限 2026-03-31
    convs = detail["conversions"]
    assert len(convs) == 1
    c = convs[0]
    assert (c["quantity"], c["target"], c["wage_basis_date"], c["payment_due_on"]) == \
        ("2", "CONVERSION_TARGET.WAGES", "2026-03-01", "2026-03-31")
    # 系統結果（紀錄用）：直接判定交給薪資、判定當時已知的已休記在事件上
    assert c["status"] == "Determined"
    assert detail["year_end_judgments"][0]["used_quantity_known"] == "1"
    assert db.outbox.find_one({"type": "LeaveConversionDetermined", "conversion_id": ObjectId(c["conversion_id"])})


def test_gc04_start_date_corrected_after_year_end(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]       # 實際 2025-03-01，登錄成 2025-03-02
    run_day(db, emp, "2025-09-02")
    run_day(db, emp, "2026-03-02")                                  # 已休 0、沒有遞延協商 → 轉為工資 3 日
    before = _by_acq(entitlements(api, org, emp, on="2026-04-15"))
    old_conv = api("listLeaveConversions", h, params={"employment_id": emp}, expect=200).json()["items"]
    assert [c["quantity"] for c in old_conv] == ["3"]
    before_correction = datetime.now(timezone.utc)

    # UC-08 第 1、2 步：更正到職日（同一交易重新判定）
    with on("2026-04-15"):
        corr = api("correctRecord", h, expect=201, json={
            "subject": {"collection": "employments", "id": emp}, "field": "start_date", "new_value": "2025-03-01",
            "reason": "到職日登錄錯誤", "evidence": [{"kind": "勞動契約"}]}).json()
        # 第 3 步：用更正回應的 event_id 查通知
        notices = api("listLeaveReassessmentNotices", h, params={"root_event_id": corr["event_id"]}, expect=200).json()["items"]
        after = _by_acq(entitlements(api, org, emp, on="2026-04-15"))

    # ① 更正後的特休明細
    assert set(after) == {"2025-09-01", "2026-03-01"}
    a, b = after["2025-09-01"], after["2026-03-01"]
    assert (a["quantity"], a["valid_from"], a["valid_to"], a["status"]) == ("3", "2025-09-01", "2026-02-28", "YearEnded")
    assert (b["quantity"], b["valid_from"], b["valid_to"], b["status"]) == ("7", "2026-03-01", "2027-02-28", "Active")
    # 兩筆都是對既有紀錄更正，不產生作廢或新增
    assert a["entitlement_id"] == before["2025-09-02"]["entitlement_id"]
    assert b["entitlement_id"] == before["2026-03-02"]["entitlement_id"]
    assert len(notices) == 1
    n = notices[0]
    assert n["added_ids"] == [] and n["voided_ids"] == []
    assert {c["entitlement_id"] for c in n["changed"]} == {a["entitlement_id"], b["entitlement_id"]}

    # ② 差額 0 日；要記錄並交給人確認，不自動覆蓋薪資：已判定的轉換不改、不另記一筆，通知列出原 → 新
    convs = api("listLeaveConversions", h, params={"employment_id": emp}, expect=200).json()["items"]
    assert convs == old_conv
    items = [i for i in n["action_items"] if i["kind"] == "NOTICE_ACTION.CONVERSION_DATES_CHANGED"]
    assert len(items) == 1 and items[0]["entitlement_id"] == a["entitlement_id"]
    assert "2026-03-01 → 2026-02-28" in items[0]["detail"]          # 工資計算基準日：原基準日與新基準日
    assert "2026-03-31 → 2026-03-30" in items[0]["detail"]          # 系統結果（紀錄用）：發給期限

    # ③ 更正前給了什麼查得到：版本紀錄、更正前的時間點、當時的轉換
    detail = api("getLeaveEntitlement", h, path={"id": a["entitlement_id"]}, expect=200).json()
    old_versions = [v["snapshot"] for v in detail["versions"] if v["snapshot"]["acquired_on"] == "2025-09-02"]
    assert old_versions and old_versions[-1]["valid_to"] == "2026-03-01"
    assert {v["event_type"] for v in detail["versions"]} >= {"GrantLeaveEntitlement", "ReassessLeaveEntitlements"}
    then = api("listLeaveEntitlements", h, path={"id": emp},
               params={"on": "2026-04-15", "as_of": before_correction.isoformat()}, expect=200).json()["items"]
    assert {i["acquired_on"] for i in then} == {"2025-09-02", "2026-03-02"}
    assert detail["conversions"][0]["wage_basis_date"] == "2026-03-01"


def test_gc06_last_day_is_six_month_anniversary(api, db, ref):
    org = leave_org(db, ref)
    h = org["hr"]
    emp = hire(api, org, ref, "2025-03-02")["employment_id"]
    run_day(db, emp, "2025-09-02")                                  # 系統還不知道結束日 → 給予

    # UC-09：結束日 2025-09-02 在 2025-09-10 才載入（固定資料 [靜態替代]）
    with on("2025-09-10"):
        api("loadEmploymentEndingFixture", h, path={"id": emp}, expect=201, json={
            "ended_on": "2025-09-02", "end_reason": "END_REASON.RESIGNATION", "reason": "GC06：一般離職"})
        items = entitlements(api, org, emp)

    # ① 有滿 6 個月那一筆；② 3 日；③ 交給離職結算，不作廢
    assert len(items) == 1
    e = items[0]
    assert e["acquired_on"] == "2025-09-02"
    assert e["quantity"] == "3"
    assert e["status"] == "EndedWithEmployment"
    # 系統結果（紀錄用）：之後不再給下一筆、不判定告知（04 D-24）
    run_day(db, emp, "2026-03-05")
    with on("2026-03-05"):
        items = entitlements(api, org, emp)
        warns = api("listLeaveWarnings", h, path={"id": emp}, expect=200).json()
    assert [i["acquired_on"] for i in items] == ["2025-09-02"]
    assert items[0]["notice_status"] == "NOT_APPLICABLE"
    assert not [w for w in warns["items"] if w["warning"]["rule_id"] == "R81"]
