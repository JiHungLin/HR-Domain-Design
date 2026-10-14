# 共用核心變更紀錄

<!-- 只新增，最新的在最上面。記錄：切片項目以 [候選] 合併、升為 [已驗證]、套用變更提案、平行切片撞號重編。格式同切片 CHANGELOG.md -->

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

