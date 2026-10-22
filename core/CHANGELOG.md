# 共用核心變更紀錄

<!-- 只新增，最新的在最上面。記錄：切片項目以 [候選] 合併、升為 [已驗證]、套用變更提案、平行切片撞號重編。格式同切片 CHANGELOG.md -->

## 2026-10-22　annual-leave-grant/03-v4、annual-leave-grant/04-v3　③④　凍結（回頭修改）
- 改了什麼：flows.md LeaveEntitlement 狀態機（無）→ Active（RejudgeLeaveYearEnd）前提加「不用扣回」，新增（無）→ Active、Active → Active（ConfirmLeaveConversion）兩列；LeaveConversion Provisional → Determined 改寫；事件 RejudgeLeaveYearEnd、ConfirmLeaveConversion、NotifyLeaveReassessment 改寫；兩個狀態機與三個事件的出處改 03-v4。rules.md R66、R76、R83、R86、R87、R92、R97、C01、C02 改寫，出處改 04-v3；分類值新增 8 列（ACQUISITION_DAY_RULE 2、FIXED_START_YEAR_METHOD 2、PAYMENT_DEADLINE_RULE 2、COMPANY_POLICY_VERSION_AT_YEAR_END 2），[候選]。沒有刪除項目，既有項目狀態仍是 [候選]
- 依據：slices/annual-leave-grant/03_flows.md D-17、D-18 @ annual-leave-grant/03-v4；04_rules.md D-26～D-32 @ annual-leave-grant/04-v3（⑥ signoff #1～#22）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-21　hire-employee/03-v7、hire-employee/05-v6、annual-leave-grant/05-v2　③⑤　凍結（回頭修改，格式）
- 改了什麼：只改格式，項目內容、出處、狀態都不變。rules.md 守恆式表的分隔列原本在 C02 之後，移到表頭下（C01、C02 才會被解析）。沒有切片前綴的 Qnn、US-Dnn、UC-nn 依所在項目的出處加前綴：hire-employee 57 處（entities.md Tenant～DataSubjectRequest、flows.md「更正方式（hire-employee）」、relations.md、rules.md R52 的 UC-14、UC-15），annual-leave-grant 48 處（entities.md LeaveType～LeaveConversion、flows.md 兩處 US-D、relations.md、rules.md R75 的 US-D10）
- 依據：tools/lint.py「表格」「core 前綴」檢查（工具包 @ 8b5f2bd）；docs/02 第六節
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-21　annual-leave-grant/03-v3、annual-leave-grant/04-v2　③④　凍結（回頭修改）
- 改了什麼：flows.md CompanyPolicy 狀態機 Effective → Effective（ReviseCompanyPolicy）改寫、新增 Repealed → Repealed（ReviseCompanyPolicy，只限修訂），說明改寫，出處改 03-v3；推導的狀態「告知狀態」列（隨僱傭關係結束、作廢的不判定）；事件 ReviseCompanyPolicy、RejudgeLeaveYearEnd、ReassessLeaveEntitlements、NotifyLeaveReassessment 與更正方式「公司規定」列，出處改 03-v3。rules.md R69、R80、R81、R90、R91、R92、R96 改寫，出處改 04-v2。沒有新增或刪除項目，狀態仍是 [候選]
- 依據：slices/annual-leave-grant/03_flows.md D-16 @ annual-leave-grant/03-v3；04_rules.md D-22～D-25、EQ-014 答覆 @ annual-leave-grant/04-v2
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-21　annual-leave-grant/03-v2、annual-leave-grant/04-v1　③④　凍結
- 改了什麼：rules.md 新增規則 35 列（R65～R99）、守恆式 2 列（C01、C02）、分類值 26 列，皆 [候選]，出處 annual-leave-grant（④ @ annual-leave-grant/04-v1）；規則文字中的 `參數名稱` 與決策表留在出處切片的 04_rules.md（core 格式沒有參數與決策表區）。flows.md「狀態機（annual-leave-grant）」56 列更新（「規則」欄回填；LeaveEntitlement 三列就地更正、LeaveConversion 兩列 CloseLeaveYear、LeaveDeferralAgreement Lapsed → Agreed 的前提改寫），6 個狀態機的出處改為 03-v2；事件 StartEmployment、SignContract 的被引用加上 annual-leave-grant（R99）；Employment 狀態機的「被引用」補上漏掉的冒號（03-v1 合併時的筆誤）。
- 被引用但沒有欄位可記：規則 R02、R51、R60 被 annual-leave-grant 的 ④ 引用（rules.md 規則表沒有「被引用」欄）。
- 依據：slices/annual-leave-grant/04_rules.md @ annual-leave-grant/04-v1（D-01～D-21）；03_flows.md @ annual-leave-grant/03-v2（D-04 改寫）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-20　annual-leave-grant/03-v1　③　凍結
- 改了什麼：flows.md 新增「狀態機（annual-leave-grant）」6 個（LeaveEntitlement、LeaveDeferralAgreement、LeaveYearAgreement、CompanyPolicy、LeaveConversion、LeaveType）、「推導的狀態與預估」、「事件（annual-leave-grant）」20 個、「更正方式（annual-leave-grant）」9 列；glossary.md 新增 40 列（狀態 20、事件 20）；皆 [候選]，出處 annual-leave-grant（③ @ annual-leave-grant/03-v1），驗收問題與 Use Case 寫成 annual-leave-grant:Qnn、annual-leave-grant:UC-nn。被引用加上 annual-leave-grant：狀態機 Employment，事件 OverrideWarning、WithdrawWarningOverride、CorrectRecord、AnnulEntry、RevokeAnnulment。既有項目的內容都沒有修改
- 依據：slices/annual-leave-grant/03_flows.md @ annual-leave-grant/03-v1（D-01～D-15）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-19　annual-leave-grant/02-v1　②　凍結
- 改了什麼：entities.md 新增 6 個 Entity：LeaveType、CompanyPolicy、LeaveYearAgreement、LeaveEntitlement、LeaveDeferralAgreement、LeaveConversion；relations.md 新增 17 條關係；glossary.md 新增 61 列（Entity 6、屬性 45、關係 10）；皆 [候選]，出處 annual-leave-grant（② @ annual-leave-grant/02-v1）。被引用加上 annual-leave-grant：Entity Tenant、Person、Employer、Jurisdiction、Employment、EmploymentContract、WarningOverride，關係 WarningOverride concernsEmployment。既有項目的內容都沒有修改
- 依據：slices/annual-leave-grant/02_entities.md @ annual-leave-grant/02-v1（D-01～D-18）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-16　hire-employee/03-v6、hire-employee/04-v5　③④　凍結（回頭修改）
- 改了什麼：flows.md 新增事件 RecordEmploymentPeriod，更新 StartEmployment、RegisterExistingEmployment（公教或軍保必填）、ProposeEnrollmentFiling（觸發來源），出處 hire-employee/03-v6；glossary.md 新增 RecordEmploymentPeriod；rules.md R24（未知 → 資料不足）、R60 更新，新增 R64，出處 hire-employee/04-v5；皆 [候選]
- 依據：slices/hire-employee 03_flows.md D-21、04_rules.md D-21、D-22（起因：實作回報 signoff.md #21；docs/03 P12）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-16　hire-employee/03-v5、hire-employee/04-v4　③④　凍結（回頭修改）
- 改了什麼：flows.md 事件 ProposeEnrollmentFiling 的觸發來源（加「人資記錄待人判斷的決定」）、說明（待人判斷分兩種、系統外雇主由人資主動記錄）、保存方式（記錄決定後重新判定並取代），出處改為 hire-employee/03-v5；rules.md R24、R39、APPLICABILITY.NEEDS_DECISION 更新，出處改為 hire-employee/04-v4；皆仍為 [候選]
- 依據：slices/hire-employee 03_flows.md D-20、04_rules.md D-19、D-20（起因：實作回報 signoff.md #18～#20）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/02-v4、03-v4、04-v3　②③④　凍結（回頭修改）
- 改了什麼：entities.md Employment 卡新增 public_or_military_insurance_covered，出處 02-v4；glossary.md 新增 1 列；flows.md 事件 ProposeEnrollmentFiling 的說明（預估、待人判斷的決定、逾期），出處 03-v4；rules.md R24、R36（提醒 → 判定）、R39、ALLOWANCE_CATEGORY.OTHER 更新，新增 APPLICABILITY.NEEDS_DECISION，出處 04-v3；皆 [候選]
- 依據：slices/hire-employee 02_entities.md D-37、03_flows.md D-19、04_rules.md D-15～D-18（起因：實作回報 signoff.md #13～#17）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/04-v2　④　凍結（回頭修改）
- 改了什麼：rules.md 的 R22、R24、R25、R26 改寫為寫出所有結果（含不適用、可自願），R42 的來源補上勞退分級表全表；出處改為 04-v2；仍為 [候選]
- 依據：slices/hire-employee/04_rules.md @ hire-employee/04-v2（D-13、D-14；起因是實作回報）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/03-v3　③　凍結（回頭修改）
- 改了什麼：flows.md 事件表新增 RecordPersonPeriod、更新 ProposeEnrollmentFiling 的觸發來源，出處改為 03-v3；glossary.md 新增 RecordPersonPeriod、修改 RegisterExistingEmployment 的定義；仍為 [候選]
- 依據：slices/hire-employee/03_flows.md @ hire-employee/03-v3（D-18）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/04-v1　④　凍結
- 改了什麼：rules.md 新增規則 63 列（R01～R63，R54 為 [已取消: X-12]）、分類值 77 列，皆 [候選]；flows.md 11 個狀態機的「規則」欄由第 ④ 步回填（狀態與轉換不變）
- 依據：slices/hire-employee/04_rules.md @ hire-employee/04-v1
- 規則不登錄在詞彙對照表（依 2026-10-14 流程更新，工具包尚未包含）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/03-v2　③　凍結（回頭修改）
- 改了什麼：flows.md 的 WorkAuthorization、DataSubjectRequest 狀態機更新（新增 Valid → Valid、延長的說明），出處改為 03-v2；事件表更新 5 列、新增 ExtendDataSubjectRequest；不能註銷清單加 ExtendDataSubjectRequest；glossary.md 新增 1 列；仍為 [候選]
- 依據：slices/hire-employee/03_flows.md @ hire-employee/03-v2（D-15～D-17）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/02-v3　②　凍結（回頭修改）
- 改了什麼：entities.md 的 Employer、EmploymentContract、Compensation、WorkAuthorization、DataSubjectRequest 五張卡更新，出處改為 02-v3；glossary.md 新增 7 列、修改 4 列、刪除 2 列（Employer.registered_on、WorkAuthorization.permit_number，被 registrations、approvals 取代；兩者仍是 [候選]，沒有其他切片引用，所以直接改，不走已取代標記）；仍為 [候選]
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v3（D-32～D-36）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-07　hire-employee/02-v1　②　凍結
- 改了什麼：hire-employee 第 ② 步以 [候選] 合併：entities.md 新增 19 張 Entity 卡（Compensation 為 [靜態替代]，正式定義屬 monthly-payroll）；relations.md 新增 39 條關係；glossary.md 新增 139 列
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v1
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-07　hire-employee/02-v2　②　回頭修改（第 0 級）
- 改了什麼：Employer 卡新增屬性 system_managed_from（開始由系統管理的日子），對應驗收問題加 hire-employee:Q21，出處改為 02-v2；glossary.md 新增一列；仍為 [候選]
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v2（D-31；起因 03_flows.md D-09、D-13）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-14　hire-employee/03-v1　③　凍結
- 改了什麼：hire-employee 第 ③ 步以 [候選] 合併：flows.md 新增狀態機 11 個、事件 33 個、更正方式 11 列；glossary.md 新增狀態與事件 60 列；狀態轉換的「規則」欄待第 ④ 步回填
- 依據：slices/hire-employee/03_flows.md @ hire-employee/03-v1
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

