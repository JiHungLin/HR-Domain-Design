# hire-employee ⑥ 簽核紀錄

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ⑥ 跑起來驗證 |
| 狀態 | 草稿 |
| 版本 | （凍結後填 tag） |
| 讀取的輸入 | 01_scope.md @ 01-v1、03_use_cases.md @ 03-v3、04_rules.md @ 04-v2、05_mapping.md @ 05-v2；實作 @ impl/hire-employee b88a209 |

- 執行者：
- 簽核者：（不得與執行者同一人）
- 日期：
- 實作版本：JiHungLin/HR-Domain-Design，分支 impl/hire-employee @ 392b358（依 02-v4、03-v4、04-v3、05-v3 實作 UC-01～UC-03，10 支 API）
- 結果摘要：P0 可回答率 x/x；黃金案例 x/x 通過；
- 未執行的項目：
- 受 [未核對] 規則影響、不算通過的案例：
- 結論：通過 ／ 不通過

## 實作時發現的設計問題
<!-- 程式中的暫時做法都列在這裡。處理：回到第幾步與版本、EQ 編號、補哪一筆來源；還沒處理的寫「待處理」，有「待處理」不能簽核通過 -->

| # | 問題 | 牽涉 | 實作暫時的做法 | 處理 |
|---|---|---|---|---|
| 1 | 錄用（`POST /hires`）的回應沒有 person_id，下一步登錄證件拿不到人的編號 | 05_mapping、api.yaml | 已依設計修改：`POST /hires` 回應照 DecideHireOut（hire_id、person_id、compensation_id、contract_id）；`/start` 照 StartEmploymentOut；請求可用 person_id 沿用既有的人 | 回到 ⑤：05_mapping D-18、X-16，api.yaml 回應給所有建立項目的編號（05-v2）；程式待依新 api.yaml 改 |
| 2 | 錄用的請求帶不進約定薪資 | 03_flows DecideHire、api.yaml | 已依設計修改：`POST /hires` 可一併帶 compensation、contract，同一交易建立並在錄用時判斷 R11；到職時接續到僱傭關係；`POST /compensations` 保留給錄用後另外約定 | 查 03：DecideHire 本來就帶約定薪資，問題在 api.yaml。回到 ⑤：05_mapping D-17、X-17（05-v2）；程式待改為錄用時一併建立 |
| 3 | R25 只寫了強制的條件，雇主沒有登記、稅籍、執業證照或聘僱許可時沒有結果 | 04_rules R25 | 已依設計修改：R22、R24、R25、R26 依 04-v2 逐項給結果（`app/rules/applicability.py`）；R25 ④ 的公告範圍另列 #12 | 回到 ④：04_rules D-13、X-29，R25 寫出強制、可自願、不適用（04-v2）；公告範圍與不適用待 EQ-023；程式待依新 R25 改 |
| 4 | api.yaml 太寬鬆：請求只寫 object，沒有必填與巢狀結構 | api.yaml | 已依設計修改：刪除 `app/models.py`，請求直接依 api.yaml 檢查（`app/spec.py`）；OpenAPI 的請求、回應、components 取自 api.yaml；測試每次呼叫都依 api.yaml 檢查回應，`tests/test_contract.py` 比對請求與回應格式 | 回到 ⑤：05_mapping D-18、X-18，api.yaml 寫到欄位層級（05-v2）；程式待改為依 api.yaml，`tests/test_contract.py` 重跑 |
| 5 | 五種保險的施行日沒有來源 | SocialInsuranceScheme.effective_from；04_rules R28 | 已依設計修改：`app/seed.py` SCHEMES 改為勞保 1960-02-24、就保 2003-01-01、職保 2022-05-01、健保 1995-03-01、勞退 2005-07-01，source_ref 寫來源條目，全部 [未核對] | 補來源：勞保就保職保#20～#22、全民健康保險#13、勞工退休金#06（2026-10-14，[未核對]）。和程式不同的：勞保條例在臺灣省施行為 1960-02-24（行政院令日期與生效日的關係待核對），程式的 1950-03-01 是條例前的省辦法時期；勞退 2005-07-01 屬解讀。程式待依來源改 |
| 6 | 勞退月提繳分級表只有第 25 級以上的來源 | 04_rules R42 | 已依設計修改：R42 載入全表 62 級；四張分級表都改為載入時從 inputs/ 的來源檔解析，不在程式裡抄數字 | 補來源：inputs/shared/勞工退休金月提繳分級表_115年1月1日.md（使用者提供，全表 62 級）；R42 來源已更新（04-v2）。程式待載入全表；月提繳工資超過 126,300 元的級距目前會判錯 |
| 7 | 哪些固定給付算入投保薪資的計算基礎 | 04_rules R39 | R39 參數暫以「伙食、交通、全勤、職務加給四類都算入」為假設，標待確認 | 待專家回覆 EQ-012；回覆後新增 R39 的修訂，不改程式 |
| 8 | 健保、勞退的法定生效日 | 04_rules R33、R34 | 不給值、晚辦天數不計算，標待確認 | 待專家回覆 EQ-003 |
| 9 | 65 歲界線含不含生日當天 | 04_rules R22、R24、R29 | 參數 max_age: 65 含 65 歲，剛好 65 歲時標待確認 | 待專家回覆 EQ-006 |
| 10 | 勞保人數門檻的計入範圍 | 04_rules R23 | 先以雇主的在職人數計，標待確認 | 待專家回覆 EQ-008 |
| 11 | 最低工資比較用底薪還是含津貼 | 04_rules R11 | R11 參數 compare_basis 先用底薪 | 待專家回覆 EQ-019 |
| 12 | R25 ④「中央主管機關公告的第 6 條以外雇主」可自願，公告範圍沒有資料 | 04_rules R25 | `app/rules/applicability.py`：一律不判成可自願，落到 ⑤ 不適用，pending 標 EQ-023 | 待專家回覆 EQ-023 |
| 13 | R24「依法應參加公教人員保險或軍人保險者」不適用，但 02 沒有屬性可以判斷 | 04_rules R24；02 Person | 已依設計修改：employments 加 `public_or_military_insurance_covered`（帶期間），由 `POST /hires/{id}/start` 的同名欄位帶入；R24 判定日為 true 時就保不適用 | 回到 ② 與 ④：02 D-37（Employment 新增是否應參加公教或軍保）、04_rules D-15（02-v4、04-v3）；程式待依新 tag 改 |
| 14 | 需人工判斷的部分在判定結果中沒有欄位表達：R24 受僱於兩個以上雇主時擇一參加；R39 固定給付類別「其他」算不算入由人判斷 | 04_rules R24、R39；api.yaml ApplicabilityItem、EnrollmentProposal | 已依設計修改：R24 擇一、R39「其他」類固定給付輸出 APPLICABILITY.NEEDS_DECISION；新增 `POST /v1/enrollment-proposals/{id}/decisions`（只有人資），決定記在待辦的 `items[].decisions`、`allowance_decisions`，新的判定沿用；細節另見 #18～#20 | 回到 ③④⑤：04_rules D-16（新分類值「待人判斷」）、03_flows D-19、05_mapping D-21（decisions API）（03-v4、04-v3、05-v3）；程式待改 |
| 15 | R36 逾期未辦是提醒類規則，但 `GET /enrollment-proposals` 的回應（EnrollmentProposalList）沒有 warnings，警告無處回傳，也就無法用 UC-09 忽略 | 04_rules R36；api.yaml listEnrollmentProposals（x-rules 有 R36） | 已依設計修改：不再輸出 R36 警告；逾期天數以 `days_overdue` 呈現在加保待辦與判定查詢，登錄實際辦理後結案 | 回到 ④：04_rules D-17，R36 改為判定，以加保待辦的 days_overdue 呈現、不能忽略（04-v3）；⑤ 同步（05-v3）；程式待改 |
| 16 | 04_rules 版本欄為「—」的規則（R14、R15、R21、R36、R45、R61 等），api.yaml 的 Warning 仍要求 rule_version、rule_revision | 04_rules；api.yaml Warning；P5 | 已依設計修改：版本改為 `hire-employee/04-v3`、修訂 1，程式註明依據 05_mapping D-20 | 回到 ⑤：05_mapping D-20，版本欄為「—」的規則以 04 凍結版本為版本，實作暫時的做法即為正式做法（05-v3）；程式改用 04-v3 |
| 17 | 錄用時（還沒到職）就產生加保待辦（03_flows 觸發來源含決定錄用；05_mapping 第六區 UC-01 第 4 步），但沒寫這時的到職日與判定日用哪一天 | 03_flows ProposeEnrollmentFiling；04_rules R37 | 已依設計修改：錄用時的待辦標 `estimated: true`，到職時以實際到職日重新判定並以 `superseded_by` 取代；程式註明依據 04_rules D-18 | 回到 ③④：03_flows D-19、04_rules D-18，錄用時以約定到職日判定、標預估，到職時重新判定並取代；實作暫時的做法即為正式做法（03-v4、04-v3）；⑤ 加保待辦加 estimated（05-v3） |
| 18 | R39「其他」類固定給付還沒決定時，05 第六區說待判斷的項目在 items 的 applicability＝待人判斷；但未決定的只是級距，保險本身是強制、可自願或不適用其實已判得出來，標成待人判斷後這個結果就看不到（可自願的也就無法讓雇主選擇不加） | 04_rules R39、D-16；05_mapping 第六區 UC-02；api.yaml ApplicabilityItem | 已依設計修改：適用、期限、法定生效日照常判定，只有級距不給；待決定的給付列在待辦與判定查詢的 `needs_decision`；程式註明依據 04_rules D-19、05_mapping D-22 | 回到 ③④⑤：03_flows D-20、04_rules D-19（適用照常判定，只有級距待人判斷）、05_mapping D-22（待辦與判定查詢加 needs_decision，api.yaml 0.4.0）（重新凍結為 hire-employee/03-v5、04-v4、05-v4）；程式待改 |
| 19 | 記錄待人判斷的決定之後要不要立刻重新判定、`ProposalOut.proposal_id` 回哪一筆，沒有寫；03 的加保待辦觸發來源沒有「記錄決定」，也沒有對應的事件，但 ProposalOut 要求 event_id | 03_flows ProposeEnrollmentFiling、D-19；05_mapping D-21；api.yaml recordProposalDecision、ProposalOut | 已依設計修改：暫時的做法即為正式做法（記錄後依決定重新判定，回應新的待辦與重新判定的事件）；程式註明依據 03_flows D-20、05_mapping D-22 | 回到 ③⑤：03_flows D-20（觸發來源加「人資記錄待人判斷的決定」，不另立事件）、05_mapping D-22（回應新的待辦與重新判定的事件）；實作暫時的做法即為正式做法（重新凍結為 hire-employee/03-v5、05-v4） |
| 20 | R24「受僱於兩個以上雇主」只看得到同一客戶內的僱傭關係（P11、PLAN.md D-31 識別範圍為客戶），客戶以外的兼職系統沒有資料 | 04_rules R24、D-16；02 Employment | 已依設計修改：只看系統內的僱傭關係；就保擇一參加不必先判成待人判斷也能記錄，之後依決定；程式註明依據 04_rules D-20 | 回到 ③④⑤：03_flows D-20、04_rules D-20，依 02 X-21 的原則不記錄系統外的雇主，人資可主動記錄擇一參加；api.yaml 說明同步（重新凍結為 hire-employee/03-v5、04-v4、05-v4）；程式待改：擇一參加不必先判成待人判斷也能記錄 |

## 檢查紀錄

<!-- AI 只填「AI 自評」；「審查者確認」由簽核者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每筆黃金案例的系統結果與獨立算出的預期結果一致 | | |
| 黃金案例由 Domain 專家提供或確認，且專家看過系統結果（或標「待專家確認」） | | |
| 每條 P0 驗收問題都能用查詢回答出來（P0 可回答率 100%；P1 記錄可回答率） | | |
| 每個正式 Use Case 至少一條可執行的測試 | | |
| ④ 的前提條件：違反時有照「違反時」欄的處理（擋下、提醒、交給人判斷） | | |
| 有守恆式的地方，在所有測試資料上都成立 | | |
| 有推導值的地方（例：餘額），砍掉重算結果一樣（依平台 P3） | | |
| ③ 的例外路徑（取消、駁回、更正）都有測試；更正後結果符合預期（保存方式依平台 P2） | | |
| 沒有權限的人無法執行受權限保護的動作（例：非店長無法核准請假） | | |
| 測試是在真的資料庫上跑的（不是 AI 自己回報通過） | | |
| 執行者與簽核者是不同的人 | | |
| 通過後，以 PR 將本切片放進 `core/` 的項目升為「已驗證」 | | |
| 沒跑的項目標「未執行」，不是「通過」 | | |
| 受「未核對」規則影響的案例，不算通過 | | |
| 失敗的項目有記錄原因，並回到對應步驟修改 | | |
| 實作時發現的設計問題都已列在 `signoff.md`，並已回頭修改，或寫明處理去向（EQ、補來源）；程式裡沒有未列出的暫時做法 | | |
<!-- CHECKLIST:END -->
