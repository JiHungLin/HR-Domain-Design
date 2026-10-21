# annual-leave-grant ⑥ 簽核紀錄

| 項目 | 內容 |
|---|---|
| 切片 | annual-leave-grant |
| 步驟 | ⑥ 跑起來驗證 |
| 狀態 | 草稿 |
| 版本 | （凍結後填 tag） |
| 讀取的輸入 | 01_scope.md @ annual-leave-grant/01-v1、03_use_cases.md @ annual-leave-grant/03-v3、04_rules.md @ annual-leave-grant/04-v2、05_mapping.md、api.yaml、schema.mongo.js、06_evidence/golden_cases.md @ annual-leave-grant/05-v2；hire-employee 的實作與 api.yaml @ hire-employee/05-v5；實作 @ impl/annual-leave-grant（未提交） |

- 執行者：AI（Claude）——寫測試，在 MongoDB replica set（本機 Docker 容器）上執行
- 簽核者：（不得與執行者同一人）
- 日期：2026-10-21
- 實作版本：JiHungLin/HR-Domain-Design，分支 impl/annual-leave-grant（從 design/main @ c7987b0 開，尚未 commit）（對應設計 tag：annual-leave-grant/01-v1、02-v1、03-v3、04-v2、05-v2）
- 結果摘要：P0 可回答率 5/5（Q01～Q05）；P1 8/9（Q10 未執行）。黃金案例 3 筆（GC01、GC04、GC06；GC02、GC03、GC05 不採用）系統結果與預期結果一致，但依據的規則都是 [未核對]，不算通過（見下）。自動測試 54 個（hire-employee 37、annual-leave-grant 17），執行紀錄見 results/pytest_2026-10-21.txt、results/系統結果_2026-10-21.md
- 未執行的項目：ReviseCompanyPolicy、RepealCompanyPolicy（回 501）；註銷與撤銷註銷（hire-employee 的 /v1/annulments 回 501）；CorrectRecord 只實作 `employments.start_date`（不含 R46 重大更正的判定、本切片集合的更正）；OverrideWarning（hire-employee 回 501，警告查詢只會標出已存在的忽略）；RecordEarlyDeparture（hire-employee 回 501，掛勾已註冊）；R71（預設做法下不會成立，不判定）；R84 只在動作的回應、不在警告查詢；Q10（規則改版）；雇主資料改變的佇列（LoadEmployerFixture）
- 受 [未核對] 規則影響、不算通過的案例：GC01（R65、R66、R69、R80、R81、R86、R89、R90）、GC04（R65、R91、R92、R93、R96）、GC06（R67、R85、R95）——04_rules 的規則與參數全部 [未核對]
- 結論：通過 ／ 不通過

## 實作時發現的設計問題
<!-- 程式中的暫時做法都列在這裡。處理：回到第幾步與版本、EQ 編號、補哪一筆來源；還沒處理的寫「待處理」，有「待處理」不能簽核通過 -->
<!-- 「問題」開頭的〔〕是分類，方便之後判斷參數表、實作者角度等試用項目的成效：〔參數〕＝04 參數表的名稱、值、格式或存放處；其他照牽涉的步驟。
     程式中的暫時做法都標 `signoff.md #n`（impl/app/leave/、impl/app/errors.py） -->

| # | 問題 | 牽涉 | 實作暫時的做法 | 處理 |
|---|---|---|---|---|
| 1 | 〔參數：格式〕`statutory_annual_leave_days` 的資料類型只寫「年資區間 → 天數」，沒有區間的欄位名稱；「10 年以上每一年加給 1 日，加至 30 日」要自己展開成表 | 04_rules 參數表 statutory_annual_leave_days、R66；05_mapping 3.2 | 區間沿用 `company_extra_days` 的 `from_months`、`to_months`、`days`；載入時從 04 參數表的預設值欄解析，10 年以上展開成每年一個區間，滿 24 年起 30 日（`app/leave/seed.py`） | 待處理：建議回 ④ 參數表（或 ⑤ 3.2）寫明格式，第 0 級 |
| 2 | 〔參數：值〕`acquisition_day_rule`、`fixed_start_year_method`、`company_policy_version_at_year_end` 的可選做法只有中文說明，沒有代碼；`payment_deadline_rule` 的代碼到 ⑤ schema 才出現（`CONTRACT_WAGE_PAYMENT_DAY`、`DAYS_AFTER_YEAR_END`，不是分類值的寫法） | 04_rules 參數表；05_mapping 3.2；schema.mongo.js employer_settings | 程式自己取：`DAY_AFTER_PERIOD_END`／`PERIOD_END_DAY`、`EXTEND_TO_YEAR_END`、`AT_GRANT`／`AT_YEAR_END`（`app/leave/seed.py` OPTION_CODES） | 待處理：建議回 ④ 參數表「合理範圍」寫出每個做法的代碼，⑤ schema 同步，第 0 級 |
| 3 | 〔⑤ 對照〕版本欄為「—」的規則，05 D-12 寫「版本填 annual-leave-grant/04-v1」，但目前凍結的 04 是 04-v2；hire-employee D-20 的做法是「規則所在的 04 凍結版本」 | 05_mapping D-12；hire-employee 05_mapping D-20 | 照 05 D-12 字面填 `annual-leave-grant/04-v1`、修訂 1 | 待處理：回 ⑤ D-12 決定填凍結版本還是固定寫法，第 0 級 |
| 4 | 〔參數：值〕R66 v1 的生效日 04 寫「生效日未查」，但規則版本一定要有生效日；「—」的規則也沒有生效日 | 04_rules R66 版本欄；05_mapping 3.2；EQ-008 | 都用 1900-01-01（當成沒有下限，沿用 hire-employee seed 對「—」規則的做法） | 待處理：補來源（特休天數表現行條文的施行日），或在 ④ 寫明上線前一律用 v1 |
| 5 | 〔參數：存放處〕04 參數表有預設值、⑤ 3.2 卻沒有放預設值的地方：`company_extra_year_end_treatment`、`company_extra_deferrable`（公司規定那一版沒寫時），`wage_payment_day`、`wage_payment_lag_months`（雇主沒有登錄 employer_settings 時） | 04_rules 參數表、R79 決策表、R90；05_mapping 3.2 | 前兩個放 `rule_versions` R79 的 `params`，後兩個放 R90 的 `params`，名稱與值照 04 | 待處理：回 ⑤ 3.2 補上存放處，第 0 級 |
| 6 | 〔⑤ 對照〕「今天」以雇主所在管轄區的日期判斷（台灣 Asia/Taipei），但管轄區（core Jurisdiction、`jurisdictions`）沒有時區 | 05_mapping 第二節（排程）；core Jurisdiction | `app/leave/clock.py` 寫死 TW → Asia/Taipei，其他用 UTC | 待處理：回 ②（core Jurisdiction 加時區，第 2 級，影響 hire-employee）或在 ⑤ 寫明放平台設定 |
| 7 | 〔命名〕警告與擋下的 `message_code`、`used_quantity_basis` 的值（05 只寫「目前累計」）、公司規定版本的名稱（`version`）在 04、05、api.yaml 都沒有定義 | 05_mapping 第二節「回應的警告」、1.1 已休固定資料；api.yaml Warning、DerivedQuantities、PolicyWriteOut | 程式自己取：`NOTICE_OVERDUE`、`NOTICE_LATE`、`NOTICE_BEFORE_ACQUIRED`、`DEFERRAL_OVER_REMAINING`、`DEFERRAL_RECORDED_AFTER_YEAR_END`、`PROVISIONAL_CONVERSION_OVERDUE`、`USED_OVER_QUANTITY`、`USED_ON_VOIDED`、`POSSIBLE_SENIORITY_MERGE`、`DEFAULT_LEAVE_YEAR_CHANGED`、`COMPANY_EXTRA_BELOW_STATUTORY`，擋下的另有 `DATE_ORDER`、`INVALID_STATE` 等；`CURRENT_TOTAL`；第一版叫 `v1`（hire-employee 的訊息代碼也是程式自取） | 待處理：回 ⑤ 決定要不要列代碼表（和 hire-employee 一起），第 0 級 |
| 8 | 〔⑤ 對照〕`employer_settings` 的值帶期間，沒寫用哪一天查 | 05_mapping 1.1 employer_settings、D-21；04_rules R90 | 用計算發給期限的那一天（年度終結日；更正差額用判定日） | 待處理：回 ⑤ D-21（或 monthly-payroll 定義時）寫明 |
| 9 | 〔⑤ schema〕`leave_entitlements.acquired_on` 必填，但補登（BackfillEntitlementIn 沒有取得日）與遞延進來的那一筆（R87 只寫可休期間）都沒有取得日的規則 | schema.mongo.js leave_entitlements；api.yaml BackfillEntitlementIn；04_rules R87、R97 | 都用可休起日 | 待處理：回 ④ R87、R97 寫明，或回 ⑤ 讓 `acquired_on` 可空，第 0 級 |
| 10 | 〔⑤ 代碼〕R96 的「就地更正後可休期間或取得日改變、上面有已休」要列入通知，但 `NOTICE_ACTION.*` 沒有對應的代碼（告知日的有 NOTICE_BEFORE_ACQUIRED） | 04_rules R96；05_mapping 1.2 NotifyLeaveReassessment；schema.mongo.js、api.yaml ActionItem | 只列在通知的 `changed[]`，不列 `action_items` | 待處理：回 ⑤ 補代碼，第 0 級 |
| 11 | 〔⑤ 對照〕已休固定資料「帶 as_of 時依 change_log 還原那個時間的值」做不到：change_log 只記欄位名稱、不記值（hire-employee D-08 的平台做法） | 05_mapping 1.1 leave_used_quantity_fixtures（X-09）；hire-employee D-08 | 從 `LoadUsedQuantityFixture` 事件記的 `payload.used_quantity` 還原 | 待處理：回 ⑤ 改寫還原方式（事件記值），第 0 級 |
| 12 | 〔規則〕R83 用「還可以休」比較，但已年度終結的那一筆還可以休一律是 0（C01），年度終結後才登錄的協商每次都會成立 R83 | 04_rules R83、C01 | 已年度終結的改用未休（額度減已休）比較 | 待處理：回 ④ R83 寫明年度終結後比較什麼，第 0 級 |
| 13 | 〔api.yaml〕待確認的轉換被取代、但重算後差額為 0、沒有新的一筆時，沒有 `discarded_by_id`；Superseded 格式要求必填 | api.yaml Superseded、confirmLeaveConversion 409；04_rules R92 | 這種情況回 409 Blocked 的格式（`message_code`＝CONVERSION_DISCARDED） | 待處理：回 ⑤ api.yaml（`discarded_by_id` 可空，或改用 Blocked），第 0 級 |
| 14 | 〔api.yaml〕`GET /employments/{id}/leave-entitlements` 的 `on`（Q01「某一天有哪幾筆」）沒寫篩選條件：取得日不晚於那天、可休期間包含那天，含不含作廢的？GC01 的預期包含已年度終結的那一筆 | api.yaml listLeaveEntitlements；05_mapping 第二節 Q01 | 取取得日不晚於 `on`、沒有作廢的；狀態用目前的 | 待處理：回 ⑤ api.yaml 寫明，第 0 級 |
| 15 | 〔守恆式〕C01 說待確認中的負數差額不算，又說已年度終結的那一筆還可以休為 0（只有已休多於額度時為負）；有待確認的負數差額時兩者不能同時成立（例：年度終結後補登已休 1 日，確認前還可以休 −1） | 04_rules C01、D-14 | 程式的 C01 檢查改為「還可以休減待確認中的負數差額＝0」（`app/leave/ledger.py`） | 待處理：回 ④ C01 寫明，第 0 級 |
| 16 | 〔規則〕年度終結後才登錄遞延協商（UC-12）：RejudgeLeaveYearEnd 立刻建立遞延進來的那一筆（可以休），扣回的負數差額卻要待確認；確認前員工同時有可休的天數和已交給薪資的工資，正是 04 D-14 想避免的「又休又領」 | 04_rules R92、R93、D-14；03_flows RejudgeLeaveYearEnd | 照設計做：遞延進來的那一筆立刻建立 | 待處理：回 ④ 決定（例：遞延進來的那一筆等負數差額確認後才可以休），第 0 級 |
| 17 | 〔③④⑤ 不一致〕EndLeaveEntitlementsWithEmployment 會產生待確認的轉換（R95），③ 事件表 NotifyLeaveReassessment 的觸發來源沒有它，但 ⑤ UC-09 例外要從通知取 `provisional_conversion_ids`，ending-fixture 的回應也有 `reassessment_notice_ids` | 03_flows 事件表 NotifyLeaveReassessment；05_mapping 第六區 UC-09 | 有改到請假權利或產生轉換就產生通知 | 待處理：回 ③ 事件表補觸發來源，第 0 級 |
| 18 | 〔參數：存放處〕`fixed_start_year_method` 04 寫「依公司規定（特休年度預設）的版本；個別約定沿用雇主預設的做法」，⑤ 3.2 卻放在 `rule_versions` R70（全部相同），`company_default_leave_year` 也沒有這個欄位 | 04_rules 參數表 fixed_start_year_method；05_mapping 3.2 | 用 R70 的值（目前只有一種做法，結果相同） | 待處理：回 ④ 參數表或 ⑤ 3.2 擇一，第 0 級 |
| 19 | 〔⑤ 對照〕結束日的固定資料（ending-fixture）的結束日在未來時，`employments.status` 何時變 Ended 沒有寫 | 05_mapping 1.1 一般離職的結束日、D-10 | 載入時就改為 Ended | 待處理：回 ⑤ D-10 寫明 |
| 20 | 〔⑤ 對照〕`LeaveEntitlement.basis_rule_versions`「每一種規則一筆」沒寫是哪幾條 | 02_entities LeaveEntitlement；05_mapping 1.2 | 記 R65、R66、R68（套用預設時加那一版公司規定）、R69 或 R70；公司加給另加 R77 與公司規定的版本 | 待處理：回 ② 或 ⑤ 寫明，第 0 級 |
| 21 | 〔規則〕R76「沒有個別約定、還在套用預設的員工」沒寫看哪一天的約定 | 04_rules R76 | 看新預設的生效日與今天較晚的那天 | 待處理：回 ④ R76 寫明，第 0 級 |
| 22 | 〔⑤ 對照〕D-18「受影響的僱傭關係」沒有定義 | 05_mapping D-18、第二節「雇主層級的動作分批」 | 雇主的每一段都上鎖；只有已有取得日不早於新規定生效日的那幾段排入佇列（其他的之後給予時自然套用） | 待處理：回 ⑤ D-18 寫明，第 0 級 |

## 檢查紀錄

<!-- AI 只填「AI 自評」；「審查者確認」由簽核者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每筆黃金案例的系統結果與獨立算出的預期結果一致 | 部分：GC01、GC04、GC06 的系統結果與預期結果一致（tests/test_leave_gc.py，斷言的值取自 golden_cases.md；results/系統結果_2026-10-21.md）；GC04 ② 的「交人工確認」以重新判定通知的 CONVERSION_DATES_CHANGED 表示（04 D-25）；系統結果還沒寫回 golden_cases.md（隨 ⑤ 凍結） | |
| 黃金案例由 Domain 專家提供或確認，且專家看過系統結果（或標「待專家確認」） | ✗：三筆的預期結果由 JiHungLin 計算，標待專家確認（EQ-003、EQ-006、EQ-009、EQ-012）；專家沒看過系統結果 | |
| 每條 P0 驗收問題都能用查詢回答出來（P0 可回答率 100%；P1 記錄可回答率） | ✓ P0 5/5：Q01 listLeaveEntitlements、Q02 getLeaveForecast＋listLeaveWarnings（R99）、Q03 getLeaveYearBasis、Q04 listLeaveEntitlements 的 source、Q05 getLeaveEntitlement 的 year_end_judgments、conversions；P1 8/9（Q10 未執行）。answers.md 還沒填 | |
| 每個正式 Use Case 至少一條可執行的測試 | ✓ UC-01～UC-12 各至少一條（UC-01、UC-04、UC-05 含 GC01；UC-08 是 GC04；UC-09 含 GC06）；UC-03、UC-10 的改版與廢止例外沒有實作 | |
| ④ 的前提條件：違反時有照「違反時」欄的處理（擋下、提醒、交給人判斷） | 部分：擋下 R72、R82、R97、R98 有測試，R73、R74 有實作沒測試；提醒 R78、R81、R84、R99 有測試，R76、R83、R94、R96 有實作沒全部測到；交給人判斷（待確認）R93 有測試；R71 不判定 | |
| 有守恆式的地方，在所有測試資料上都成立 | ✓ 每次寫入請假權利或轉換後同一交易檢查 C01、C02；test_zz_conservation_on_all_data 對全部測試資料再檢查一次（C01 的寫法見 #15） | |
| 有推導值的地方（例：餘額），砍掉重算結果一樣（依平台 P3） | 部分：數量、告知期限與狀態、警告都不存，每次現算（05 D-06）；狀態快取（status）由事件重算的檢查沒有寫 | |
| ③ 的例外路徑（取消、駁回、更正）都有測試；更正後結果符合預期（保存方式依平台 P2） | 部分：修改、撤回遞延協商，到職日更正，較晚得知離職，待確認轉換被取代都有測試，更正前的版本查得到（as_of）；註銷、撤銷註銷、公司規定的修訂與廢止沒有實作 | |
| 沒有權限的人無法執行受權限保護的動作（例：非店長無法核准請假） | 部分：雇主（老闆）不能登錄遞延協商、別的客戶查不到，有測試；其他動作的角色檢查有實作沒逐一測 | |
| 測試是在真的資料庫上跑的（不是 AI 自己回報通過） | ✓ 本機 MongoDB replica set，54 個通過，輸出存在 results/pytest_2026-10-21.txt（中途資料庫的開啟檔案數用完，經使用者同意重啟容器後重跑） | |
| 執行者與簽核者是不同的人 | 執行者 AI（Claude）；簽核者待人填 | |
| 通過後，以 PR 將本切片放進 `core/` 的項目升為「已驗證」 | 未做：還沒通過 | |
| 沒跑的項目標「未執行」，不是「通過」 | ✓ 見「未執行的項目」；Q10 標未執行 | |
| 受「未核對」規則影響的案例，不算通過 | ✓ 三筆黃金案例都列在「受 [未核對] 規則影響」 | |
| 失敗的項目有記錄原因，並回到對應步驟修改 | 不適用：沒有失敗的測試；實作時發現的設計問題 22 項都還沒回頭修改 | |
| 實作時發現的設計問題都已列在 `signoff.md`，並已回頭修改，或寫明處理去向（EQ、補來源）；程式裡沒有未列出的暫時做法 | 部分：22 項都列在上表，程式中的暫時做法都標 `signoff.md #n`（AI 用 grep 比對 1～22 都有）；全部「待處理」 | |
<!-- CHECKLIST:END -->
