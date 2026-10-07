# 共用核心變更紀錄

<!-- 只新增，最新的在最上面。記錄：切片項目以 [候選] 合併、升為 [已驗證]、套用變更提案、平行切片撞號重編。格式同切片 CHANGELOG.md -->

## 2026-10-07　hire-employee/02-v1　②　凍結
- 改了什麼：hire-employee 第 ② 步以 [候選] 合併：entities.md 新增 19 張 Entity 卡（Compensation 為 [靜態替代]，正式定義屬 monthly-payroll）；relations.md 新增 39 條關係；glossary.md 新增 139 列
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v1
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱

## 2026-10-07　hire-employee/02-v2　②　回頭修改（第 0 級）
- 改了什麼：Employer 卡新增屬性 system_managed_from（開始由系統管理的日子），對應驗收問題加 hire-employee:Q21，出處改為 02-v2；glossary.md 新增一列；仍為 [候選]
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v2（D-31；起因 03_flows.md D-09、D-13）
- 產出者：AI（Claude）；審查者：JiHungLin；核心負責人：待審閱
