# 規劃變更紀錄

<!-- 放在 slices/CHANGELOG.md。記錄切片地圖（slices/PLAN.md）與全局名詞草圖（slices/ENTITY_SKETCH.md）的每次變動；兩份文件本身只放目前的內容。
     只新增，不改舊紀錄；最新的在最上面。
     標題列：日期、改了哪一份（PLAN／SKETCH／兩份都改寫 PLAN、SKETCH）、事件。一件事改到兩份，記一筆。

### <日期>　<PLAN／SKETCH／PLAN、SKETCH>　<事件>
- 改了什麼：
- 依據：
- 舊 → 新：
- 影響：
- 同意者：
-->

### 2026-10-21　PLAN　annual-leave-grant 設計完成（待驗證）
- 改了什麼：PLAN 切片列 annual-leave-grant 的狀態：進行中 → 設計完成（待驗證）
- 依據：annual-leave-grant/05-v1 凍結（同時凍結 03-v3、04-v2）
- 舊 → 新：進行中 → 設計完成（待驗證）；第 ⑥ 步等有系統時再做
- 影響：建議順序的下一條切片可以開始；hire-employee 的程式要加呼叫特休重新判定的掛勾（annual-leave-grant 05_mapping D-04），實作時處理
- 同意者：JiHungLin（2026-10-21，/domain-freeze 3,4,5）

### 2026-10-20　PLAN、SKETCH　新增切片 event-leave（因事件才有的假）
- 改了什麼：PLAN 新增候選切片 event-leave（建議順序 9）、決定 D-39；hourly-payroll 之後 12 條切片的建議順序各加一（9～20 → 10～21）；領域「人資／請假」的切片數 4 → 5；台灣主線變成 1～14（D-03）；開頭區統計 20 條 → 21 條（現場 11 → 12）。SKETCH 的 LeaveType、LeaveEntitlement、LeaveRequest、LeaveOccurrence、Approval、Evidence、PayItem 的「會用到的切片」加上 event-leave；「不確定的地方」新增「因事件才有的假」（要不要先給一筆請假權利、喪假的親屬怎麼表示）
- 依據：inputs/shared/範圍釐清_事件假切片.md；research/請假.md（#02、#03、#06、#08、#11、#13）；審查 annual-leave-grant 第 ③ 步時，使用者問請假權利能不能涵蓋婚假等其他假別
- 舊 → 新：沒有切片負責婚假、喪假、產假、產檢假、陪產檢及陪產假、公傷病假、公假 → 由 event-leave 負責；草圖名詞數不變（49），統計不變
- 影響：event-leave 第 ② 步要驗證 LeaveEntitlement（annual-leave-grant 定義）撐不撐得住按事件給的假，撐不住時走變更提案；research/請假.md 各條的「用在」與 INDEX.md 的「用在」還沒寫 event-leave（已存在的檔案不修改），到 event-leave 第 ① 步時處理
- 同意者：JiHungLin（2026-10-20，對話中要求；AI 提出的建議順序、依賴、大小估計，以及生理假與家庭照顧假留在 unpaid-leave-deduction、全勤獎金歸 monthly-payroll，同日同意）

### 2026-10-19　SKETCH　annual-leave-grant 第 ② 步凍結：6 個名詞改為已定義
- 改了什麼：CompanyPolicy、LeaveType、LeaveEntitlement、LeaveYearAgreement、LeaveDeferralAgreement、LeaveConversion 的狀態 草圖 → 已定義，「一句意思」改為「見 core/entities.md」
- 依據：slices/annual-leave-grant/02_entities.md @ annual-leave-grant/02-v1；core/entities.md
- 舊 → 新：已定義的名詞 +6；名詞總數不變（49）
- 影響：後續切片引用 core/ 的正式定義
- 同意者：JiHungLin（2026-10-19，/domain-freeze 2）

### 2026-10-19　SKETCH　annual-leave-grant 第 ② 步：新增 3 個名詞、調整 4 列
- 改了什麼：新增 LeaveYearAgreement（特休年度約定）、LeaveDeferralAgreement（遞延協商）、LeaveConversion（請假權利轉換），都由 annual-leave-grant 定義；CompanyPolicy 的意思加上「特休年度預設」，關係改為屬於 Tenant、可以限定 Employer、關於某個 LeaveType；LeaveType 判定為 Entity（「其他不確定」那一條註明結果），取得方式不放在假別上；LeaveEntitlement 改為「一筆」為單位、額度有單位，轉為工資或失效的部分改記成 LeaveConversion；PayItem 的追溯來源 LeaveEntitlement → LeaveConversion；「其他不確定」加上依工時累積、以小時請以日計的假、共用額度、轉任或留用時的承接四條
- 依據：slices/annual-leave-grant/02_entities.md D-04、D-05、D-06、D-09、D-10、D-11、D-18；X-05、X-06、X-10、X-12、X-13、X-19
- 舊 → 新：名詞 46 → 49；統計 現場 23、公開 20、推想 3 → 現場 26、公開 20、推想 3；引用推想草稿的仍是 15 個
- 影響：monthly-payroll 定義 PayItem 時引用 LeaveConversion；resignation 的離職折算用同一個 LeaveConversion（原因：契約終止）；annual-leave-request 扣用時要分得出當期與遞延進來的那一筆；second-country-hire、unpaid-leave-deduction、seniority-recognition、cross-border-transfer 的第 ② 步要處理新增的三條不確定
- 同意者：JiHungLin（2026-10-19，第 ② 步審查通過、D-18 同意）

### 2026-10-19　PLAN、SKETCH　開頭區依據統計重新計數
- 改了什麼：PLAN 與 SKETCH 開頭區「依據」的統計，依 D-14（每列最高一級）逐列重新計數；只改統計，切片、名詞與各列依據都沒有改
- 依據：PLAN.md 切片表與 ENTITY_SKETCH.md 名詞表的「依據」欄；D-14
- 舊 → 新：PLAN 切片 18 條（現場 8、公開 9、推想 1；18 條中 12 條引用推想草稿）→ 20 條（現場 11、公開 8、推想 1；20 條中 12 條）。差異來源：新增 seniority-recognition、leave-of-absence 後沒更新（現場 +2）；monthly-payroll 自 2026-10-06（d3f7d6b）依據加入 inputs/shared/範圍釐清_試用期.md 後已屬現場資料，統計一直沒跟著改（公開 −1、現場 +1）。SKETCH 名詞 46 個（現場 21、公開 22、推想 3；「34 個中」15 個引用推想草稿）→ 現場 23、公開 20、推想 3；46 個中 15 個。舊的分項少算 2 個現場資料，「34 個」是更早的名詞數沒跟著改
- 影響：無；只是統計數字
- 同意者：JiHungLin（2026-10-19，對話中要求修正）

### 2026-10-19　PLAN、SKETCH　年度終結的未休特休工資與每年書面通知歸 monthly-payroll
- 改了什麼：PLAN 新增 D-38；annual-leave-grant 列的情境補上年度終結的判定、會碰到的領域加人資／薪資、依據加細則 §24-1；monthly-payroll 列的情境補上特休年度終結轉為工資的天數與每年書面通知、依賴加 annual-leave-grant、依據加特別休假.md（§38 第 5 項、細則 §24-1、§24-2）。SKETCH 的 LeaveEntitlement 改為「年度終結或離職時轉為工資的部分產生 PayItem」、會用到的切片加 monthly-payroll；「特休年度可以選」改為依每位員工與雇主的約定（annual-leave-grant D-12）
- 依據：annual-leave-grant 01_scope X-22、X-24、D-12；research/特別休假.md #01、#03、#04；inputs/shared/範圍釐清_年度終結未休工資歸屬.md
- 舊 → 新：年度終結的未休工資、每年書面通知沒有切片負責 → monthly-payroll；annual-leave-grant 會碰到的領域 人資／人事 → 人資／人事、人資／薪資；特休年度「公司選的」→「每位員工與雇主約定的」
- 影響：monthly-payroll 的業務結果變成 2 個，到它的第 ① 步確認大小；annual-leave-grant 01_scope 的「範圍外但會用到」與完成標準第 1 條和地圖一致；annual-leave-grant 第 ② 步定義 LeaveEntitlement 時要撐得起年度終結轉為工資
- 同意者：JiHungLin（2026-10-19，選方案 A）

### 2026-10-19　PLAN、SKETCH　新增兩條切片的連帶修改
- 改了什麼：草圖新增 SeniorityRecognition（年資承認，由 seniority-recognition 定義）、LeaveOfAbsence（留職停薪，由 leave-of-absence 定義）；LeaveEntitlement、InsuranceEnrollment、EmploymentContract、Separation、Approval 的「會用到的切片」加上兩條新切片；「不確定的地方」改寫年資合併、新增留職停薪；地圖領域表的切片數改為實際值（人事 7、出勤 2、請假 4、薪資 3、跨國任用 4；原本人事、薪資、跨國任用就和切片表對不上）；D-03 的台灣主線範圍註明為 1～13
- 依據：PLAN.md D-36、D-37；使用者要求「需要聯動的地方也一起改」
- 舊 → 新：草圖名詞 44 → 46；領域表 4、2、4、4、3 → 7、2、4、3、4
- 影響：兩條新切片的第 ② 步對照草圖；annual-leave-grant 第 ② 步定義 LeaveEntitlement 時，要撐得起依合併後的年資、留停規則重新判定
- 同意者：JiHungLin（2026-10-19，對話中要求）

### 2026-10-19　PLAN　新增切片 leave-of-absence（留職停薪）
- 改了什麼：地圖新增候選切片 leave-of-absence（建議順序 12）、決定 D-37；resignation 之後 8 條切片的建議順序各加一（12～19 → 13～20）；resignation 的依賴加上 leave-of-absence；領域「人資／請假」的切片數 3 → 4；台灣主線變成 1～13（D-03）
- 依據：inputs/shared/範圍釐清_留職停薪切片.md；審查 annual-leave-grant 第 ① 步 D-07 時，使用者指出留職停薪沒有後續規劃
- 舊 → 新：沒有切片負責留職停薪 → 由 leave-of-absence 負責
- 影響：annual-leave-grant 01_scope D-07 改寫為由 leave-of-absence 補上；之後 social-insurance 的續保、resignation 的年資都要考慮留停
- 同意者：JiHungLin（2026-10-19，對話中選擇；建議順序與依賴的細節是 AI 提出的）

### 2026-10-19　PLAN　新增切片 seniority-recognition（依法應合併的年資）
- 改了什麼：地圖新增候選切片 seniority-recognition（建議順序 11）、決定 D-36；resignation、second-country-hire、assignment-leave、assignment-payroll、cross-border-transfer、org-setup、personnel-record、quota-employment 的建議順序各加一（11～18 → 12～19）；resignation、cross-border-transfer 的依賴加上 seniority-recognition；領域「人資／人事」的切片數 4 → 5；台灣主線變成 1～12（D-03）
- 依據：inputs/shared/範圍釐清_年資合併切片.md；審查 annual-leave-grant 第 ① 步 D-11 時，使用者指出合併年資沒有後續規劃
- 舊 → 新：沒有切片負責台灣境內的年資合併（D-25 只要求保留資料）→ 由 seniority-recognition 負責
- 影響：annual-leave-grant 01_scope D-11 改寫為由 seniority-recognition 補上；resignation 的資遣費、特休與 cross-border-transfer 的年資承認，都改引用它
- 同意者：JiHungLin（2026-10-19，對話中選擇；建議順序與依賴的細節是 AI 提出的）

### 2026-10-19　PLAN　P-06 已回覆：特休週年制與曆年制都支援
- 改了什麼：待釐清 P-06 的狀態 待問 → 已回覆
- 依據：inputs/annual-leave-grant/範圍釐清_第一次.md
- 舊 → 新：待問 → 已回覆（兩種都支援）
- 影響：annual-leave-grant 的規則要有「計算基準」（週年／曆年）；曆年制換算細節寫成專家問題
- 同意者：JiHungLin（2026-10-19，對話中回答）

### 2026-10-19　PLAN　開始 annual-leave-grant
- 改了什麼：切片 annual-leave-grant 的狀態 候選 → 進行中
- 依據：依建議順序的下一條；依賴的 hire-employee 已設計完成（待驗證）
- 舊 → 新：候選 → 進行中
- 影響：建立 slices/annual-leave-grant/，開始第 ① 步；引用 hire-employee 的核心項目標 [引用候選]
- 同意者：JiHungLin（2026-10-19，對話中要求開始另一條切片）

### 2026-10-14　PLAN　hire-employee 設計完成
- 改了什麼：切片 hire-employee 的狀態 進行中 → 設計完成（待驗證）
- 依據：hire-employee 第 ⑤ 步凍結（hire-employee/05-v1）
- 舊 → 新：進行中 → 設計完成（待驗證）；第 ⑥ 步等有系統時再做
- 影響：可以開始下一條切片；依建議順序，下一條是 annual-leave-grant（依賴 hire-employee）
- 同意者：JiHungLin（2026-10-14，對話中同意）

### 2026-10-14　PLAN　第 ⑤ 步需要的平台約定
- 改了什麼：地圖新增決定 D-35（資料庫 MongoDB、API 形式，以及平台約定 P1、P2、P3、P6、P7、P8 的做法）
- 依據：hire-employee 進入第 ⑤ 步時，docs/03 的 P1～P8 未填；inputs/shared/範圍釐清_平台約定_第五步.md
- 舊 → 新：決定 D-01～D-34 → D-01～D-35；切片與名詞不變
- 影響：所有切片的第 ⑤ 步依 D-35 投影；交付物 schema.sql 改為 schema.mongo.js
- 同意者：JiHungLin（2026-10-14，對話中同意）

### 2026-10-14　PLAN、SKETCH　人的特殊身分：新增切片 quota-employment
- 改了什麼：地圖新增候選切片 quota-employment（定額進用，建議順序 18）、待釐清 P-19（問 HC：到職時是否蒐集特殊身分）、P-20（先蒐集定額進用與歲時祭儀的法規原文）、決定 D-34；草圖新增 IndigenousStatus（原住民身分）、DisabilityCertificate（身心障礙證明），「不確定的地方」記下待 quota-employment 第 ② 步決定的事
- 依據：使用者審查 hire-employee 第 ③ 步時提出（inputs/shared/範圍釐清_特殊身分員工.md），選擇 A＋C
- 舊 → 新：切片 17 → 18 條；名詞 42 → 44 個；已凍結的 hire-employee 不變
- 影響：之後的請假切片（歲時祭儀假）、social-insurance（保費補助）引用 quota-employment 定義的名詞；到職表單在 hire-employee 第 ⑤ 步可預留這些欄位，由 quota-employment 定義
- 同意者：JiHungLin（2026-10-14，對話中同意）

### 2026-10-07　PLAN、SKETCH　變更紀錄搬移
- 改了什麼：依工具包更新（規劃文件的變更紀錄改成獨立檔案），把 PLAN.md「變更紀錄」區 36 筆與最後 6 行早期的一行式紀錄、ENTITY_SKETCH.md「變更紀錄」區 16 筆，依日期合併搬到本檔；內容原文照搬，只在標題加上來源（PLAN 或 SKETCH）；同一天的紀錄保留各自原本的先後，PLAN 在前；早期的一行式紀錄原本接在 PLAN 最舊一筆的後面，搬成獨立的一筆放在最底；兩份文件刪除「變更紀錄」區（含範本註解）
- 依據：工具包 @ de81bc9（docs/02「規劃的變更紀錄」、domain-plan「舊格式的紀錄要搬移」）；使用者同意（2026-10-07，對話：「同步，然後更新一下slices的內容」）
- 舊 → 新：PLAN.md 413 行 → 152 行；ENTITY_SKETCH.md 243 行 → 122 行；兩份文件除了刪除紀錄區，內容不變
- 影響：之後地圖與草圖的變動都記在本檔；舊紀錄中寫「草圖與地圖的變更紀錄各記一筆」的，是搬移前的做法，原文保留
- 同意者：JiHungLin（2026-10-07）

### 2026-10-07　PLAN　D-33：規則版本的界線
- 改了什麼：新增 D-33，補充 D-28：能不能判定以有沒有對應的規則版本為界；既有員工加入系統時事實照填；日後補進較早的法規即可判定
- 依據：inputs/shared/範圍釐清_補登員工與規則版本界線.md
- 舊 → 新：D-28 的「系統上線前」→ 「沒有對應規則版本的時點」；D-28 其餘不變
- 影響：hire-employee 02_entities D-12 改寫，Employment.pre_go_live_basis_note 改名為 historical_basis_note；之後各切片的「無對應規則版本」都依這條界線
- 同意者：JiHungLin（2026-10-07，對話中同意）

### 2026-10-07　PLAN　新增切片 personnel-record
- 改了什麼：新增候選切片 personnel-record（獎懲與傷病的登記），建議順序 17；決定 D-32；名詞草圖新增 DisciplinaryRecord、InjuryIllnessRecord
- 依據：hire-employee 第 ② 步審查（D-16）；inputs/research/勞動契約與年資.md（#03、#10）
- 舊 → 新：切片 16 → 17 條；公開來源 8 → 9
- 影響：hire-employee 02_entities D-16 改為由 personnel-record 處理；Q10 的獎懲、傷病由該切片回答
- 同意者：JiHungLin（2026-10-07，對話中同意）

### 2026-10-07　PLAN　名詞草圖：WarningOverride 恢復、新增 PersonalDataArchival
- 改了什麼：名詞草圖的 WarningOverride 恢復為草圖；新增 PersonalDataArchival
- 依據：slices/hire-employee/02_entities.md D-27、D-29
- 舊 → 新：上一筆「WarningOverride 改為事件」作廢；草圖名詞 40 個
- 影響：D-27「忽略警告要留紀錄」由 WarningOverride 記錄；D-29 的封存由 PersonalDataArchival 記錄
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-07　PLAN　名詞草圖：WarningOverride 改為事件
- 改了什麼：名詞草圖的 WarningOverride 標為已取消
- 依據：slices/hire-employee/02_entities.md D-21（六問第 0 問）
- 舊 → 新：名詞 → 事件（hire-employee 第 ③ 步）
- 影響：D-27「忽略警告要留紀錄」不變，改由事件記錄
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-07　PLAN　平台約定 P11 分階段
- 改了什麼：新增 D-31
- 依據：使用者對話（2026-10-07），存為 inputs/shared/範圍釐清_P11_識別範圍與資料性質.md；工具包更新（commit 2dd2880）新增 P11
- 舊 → 新：P11 未填 → 這一階段識別範圍為每家客戶各自一份、不標資料性質；最終目標為混合、上平台前補標
- 影響：各切片第 ② 步的「身分」以客戶內為範圍；屬性不標 [性質]；docs/03 P11 本身請使用者或流程維護者填寫（AI 不修改 docs/）
- 同意者：JiHungLin

### 2026-10-07　SKETCH　hire-employee 第 ② 步凍結：18 個名詞已定義
- 改了什麼：Tenant、Person、Jurisdiction、Employer、OrgUnit、WorkLocation、Employment、EmploymentContract、SocialInsuranceScheme、InsuranceEnrollment、InsuredSalary、IdentityDocument、InsuranceUnit、Hire、WarningOverride、DataSubjectRequest、PersonalDataArchival、WorkAuthorization 狀態 草圖 → 已定義，「一句意思」改為見 core/entities.md
- 依據：slices/hire-employee/02_entities.md @ hire-employee/02-v1
- 舊 → 新：已定義 0 → 18；Compensation 仍為草圖（正式定義屬 monthly-payroll）
- 影響：後續切片引用 core/ 的 [候選] 項目時標 [引用候選]
- 同意者：JiHungLin（2026-10-07，第 ② 步審查通過）

### 2026-10-07　SKETCH　新增 DisciplinaryRecord、InjuryIllnessRecord
- 改了什麼：新增獎懲紀錄、傷病紀錄兩個名詞，由新切片 personnel-record 定義
- 依據：PLAN.md D-32；hire-employee 02_entities D-16
- 舊 → 新：名詞 40 → 42；統計 公開來源 20 → 22
- 影響：勞工名卡的 12 項都有切片負責
- 同意者：JiHungLin（2026-10-07，對話中同意）

### 2026-10-07　SKETCH　WarningOverride 恢復、新增 PersonalDataArchival
- 改了什麼：WarningOverride 狀態 已取消 → 草圖（恢復）；新增 PersonalDataArchival（個資封存），由 hire-employee 定義
- 依據：slices/hire-employee/02_entities.md D-27（忽略之後會失效或撤回，有狀態要追蹤）、D-29（封存有範圍、起訖、解除）；挑錯 X-13、X-19
- 舊 → 新：名詞 39（已取消 1）→ 40；統計 現場 16 → 17
- 影響：上一筆「WarningOverride 改為事件」作廢；resignation 要處理離職後的個資封存
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-07　SKETCH　WarningOverride 改為事件
- 改了什麼：WarningOverride（警告忽略紀錄）狀態 草圖 → 已取消
- 依據：工具包更新（commit 2dd2880）第 ② 步改為六問；第 0 問「發生的事」之後沒有狀態要追蹤者是事件（slices/hire-employee/02_entities.md D-21）
- 舊 → 新：名詞 → 事件，交給 hire-employee 第 ③ 步；統計不變（保留已取消的一列）
- 影響：所有切片的「忽略警告」改用第 ③ 步的事件記錄
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-06　PLAN　hire-employee 第 ② 步：名詞草圖新增 5 個名詞
- 改了什麼：名詞草圖新增 IdentityDocument、InsuranceUnit、Hire、WarningOverride、DataSubjectRequest；切片地圖本身不變
- 依據：slices/hire-employee/02_entities.md D-17
- 舊 → 新：草圖名詞 34 → 39
- 影響：org-setup 之後要維護投保單位；resignation 要處理個資請求與封存；所有切片的規則警告都用 WarningOverride 記錄忽略
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-06　PLAN　使用者算客戶端使用者
- 改了什麼：新增 D-30
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_使用者作為客戶端使用者來源.md
- 舊 → 新：使用者的說明不對應驗收問題的來源 → 以使用者身分描述的需求或情況標「客戶端使用者」
- 影響：hire-employee Q18、Q20、Q21 改標；之後各切片照此標註
- 同意者：JiHungLin

### 2026-10-06　PLAN　個資封存與去識別
- 改了什麼：新增 D-29；現實資料盤點新增「員工個人資料」（已蒐集）
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_個資封存與去識別.md；inputs/research/員工個人資料.md（新增）
- 舊 → 新：沒有規定 → 個資要能封存，上平台時部分去識別
- 影響：hire-employee 新增驗收問題 Q22；resignation（離職後的封存）；之後的平台功能與 P-09 跨客戶連結
- 同意者：JiHungLin

### 2026-10-06　PLAN　法規版本只從系統上線起
- 改了什麼：新增 D-28
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_法規版本與系統上線前資料.md
- 舊 → 新：沒有規定 → 規則版本從系統上線起建立；上線前的資料記文字、不判定
- 影響：所有切片第 ④ 步的規則版本從上線起算；hire-employee 新增驗收問題（補登老員工）；resignation、annual-leave-grant 等需要舊制年資的切片，上線前的部分以文字記錄為準
- 同意者：JiHungLin

### 2026-10-06　PLAN　D-27 補充確認：矛盾資料阻擋
- 改了什麼：D-27 中「資料自相矛盾仍可阻擋」由待確認改為使用者已同意，並註明少見但可能發生的情況只警告
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_矛盾資料阻擋.md
- 舊 → 新：待使用者確認 → 已同意
- 影響：各切片第 ④ 步標出「矛盾、阻擋」與「少見、警告」
- 同意者：JiHungLin

### 2026-10-06　PLAN　法規檢查只警告、不阻擋
- 改了什麼：新增 D-27
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_法規警告不阻擋.md
- 舊 → 新：沒有規定 → 法規與公司規定的檢查預設只警告，忽略時留紀錄
- 影響：所有切片第 ④ 步的規則要標「警告」或「阻擋」；hire-employee 第 ① 步新增驗收問題；名詞草圖可能需要「警告與忽略紀錄」的概念，由 hire-employee 第 ② 步判斷
- 同意者：JiHungLin（「資料自相矛盾仍可阻擋」待確認）

### 2026-10-06　PLAN　hire-employee 情境與範圍對齊
- 改了什麼：hire-employee 情境補上「並能和實際辦理日比對」；依據欄重複列出的勞動契約與年資.md 合併為一筆
- 依據：第 ① 步審查（使用者對話，2026-10-06），對照 slices/hire-employee/01_scope.md 的切片情境
- 舊 → 新：只補文字，意思不變
- 影響：無
- 同意者：JiHungLin

### 2026-10-06　PLAN　P-18 已回覆：移工與定期契約
- 改了什麼：P-18 改為已回覆；新增 D-26；hire-employee 情境加上勞動契約為不定期或定期、外籍員工含移工
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_P-18_移工定期契約.md；inputs/research/勞動契約與年資.md #11（新增）
- 舊 → 新：hire-employee 只做不定期契約 → 不定期與定期都做（期滿處理在 resignation）；大小估計仍為太大
- 影響：hire-employee 第 ① 步再修改；resignation 之後要處理定期契約期滿、續約、視為不定期契約；名詞草圖 EmploymentContract 補上定期契約
- 同意者：JiHungLin

### 2026-10-06　PLAN　健保投保金額分級表已提供
- 改了什麼：現實資料盤點拆成兩列：「健保投保金額分級表」改為已有（inputs/shared/健保投保金額分級表_115年1月1日.md），保險費負擔金額表、費率、平均眷口數仍待提供
- 依據：使用者對話（2026-10-06），提供 115年1月1日分級表.xls
- 舊 → 新：待提供 → 已有（使用者提供，未附網址）
- 影響：hire-employee 的健保級距（Q17）有原文可對照；切片統計不變
- 同意者：JiHungLin（提供資料）

### 2026-10-06　PLAN　hire-employee 第 ① 步審查：「不做」清單調整
- 改了什麼：hire-employee 的情境加入外籍員工與到職時的投保薪資級距，大小估計 剛好 → 太大；monthly-payroll 情境註明含試用期滿調薪；social-insurance 情境註明到職時的級距由 hire-employee 決定；新增切片 org-setup（順序 16）；新增 D-20～D-25、P-18；現實資料盤點新增「外國人聘僱與工作許可」（已蒐集），115 年勞保、勞退分級表改為已蒐集，健保分級表仍待提供；人資／人事切片數 3 → 4
- 依據：使用者對話（2026-10-06），存為 inputs/shared/範圍釐清_hire-employee_不做清單.md；inputs/research/外國人聘僱.md（新增）、勞保就保職保.md #16～#19、勞工退休金.md #05
- 舊 → 新：切片 15 → 16 條；統計 現場 6、公開 8、推想 1 → 現場 7、公開 8、推想 1；D-17「只做全職月薪」仍有效，但外籍員工改為納入（D-20）
- 影響：hire-employee 第 ① 步要改寫，改完狀態維持待檢查；名詞草圖 WorkAuthorization 改由 hire-employee 定義、新增 InsuredSalary；移工的契約類型待 P-18；second-country-hire 原本要補的工作許可資料已由本次蒐集
- 同意者：JiHungLin（D-20～D-25 的選擇）；P-18 待回答

### 2026-10-06　SKETCH　hire-employee 第 ② 步：新增名詞
- 改了什麼：新增 IdentityDocument、InsuranceUnit、Hire、WarningOverride、DataSubjectRequest 五個名詞（由 hire-employee 定義）；Compensation 由 hire-employee 建 [靜態替代] 卡，正式定義仍屬 monthly-payroll；Separation 維持由 resignation 定義
- 依據：slices/hire-employee/02_entities.md D-02、D-05、D-11、D-14、D-17、D-18（三問判斷：這些名詞的結束時間都和人、雇主、僱傭關係不同）
- 舊 → 新：名詞 34 → 39；統計 現場 14、公開 17、推想 3 → 現場 16、公開 20、推想 3
- 影響：hire-employee 第 ② 步正式定義 18 個名詞（含 Compensation 靜態替代卡）；「不確定的地方」中投保單位、Separation 的問題由 02_entities.md D-02、D-07 回答
- 同意者：（第 ② 步凍結時一併確認）

### 2026-10-06　SKETCH　P-18 已回覆：移工與定期契約
- 改了什麼：EmploymentContract 的一句意思補上定期契約的性質與起訖日，主要關係加上和 WorkAuthorization 連動，依據加上新檔；「不確定的地方」移工一點改寫為答覆
- 依據：使用者對話（2026-10-06），inputs/shared/範圍釐清_P-18_移工定期契約.md；PLAN.md D-26
- 舊 → 新：EmploymentContract 依據 公開來源 → 現場資料；統計 現場 13、公開 18 → 現場 14、公開 17
- 影響：hire-employee 第 ② 步定義 EmploymentContract 時要涵蓋定期契約與續約
- 同意者：JiHungLin

### 2026-10-06　SKETCH　hire-employee 第 ① 步審查：「不做」清單調整
- 改了什麼：WorkAuthorization 正式定義於 second-country-hire → hire-employee，一句意思補上起訖日與申請方式，會用到的切片加上 hire-employee、resignation、annual-leave-request；新增 InsuredSalary（投保薪資）；Separation 會用到的切片加上 hire-employee；「不確定的地方」新增一節（外籍員工、工作許可、移工定期契約、投保薪資、Separation、年資資料保留）
- 依據：使用者對話（2026-10-06），inputs/shared/範圍釐清_hire-employee_不做清單.md；inputs/research/外國人聘僱.md、勞保就保職保.md #16～#19、勞工退休金.md #05；PLAN.md D-20～D-25
- 舊 → 新：名詞 33 → 34；統計 現場 13、公開 16、推想 4 → 現場 13、公開 18、推想 3（WorkAuthorization 由推想改為公開來源，InsuredSalary 為公開來源）
- 影響：hire-employee 第 ② 步要定義的名詞增加 WorkAuthorization、InsuredSalary，可能加上 Separation
- 同意者：JiHungLin（D-20～D-25 的選擇）

### 2026-10-05　PLAN　hire-employee 情境依第 ① 步更新
- 改了什麼：hire-employee 的情境改寫，與 slices/hire-employee/01_scope.md 一致
- 依據：slices/hire-employee/01_scope.md（D-06、D-07、X-13）；D-18（Employer）
- 舊 → 新：台灣公司錄用一位全職月薪員工 → 辦理到職 → 僱傭關係（所屬法人、組織、到職日、適用國家規則）成立，勞健保應加保日正確 → 台灣的雇主錄用一位全職月薪員工 → 員工開始提供勞務（到職） → 僱傭關係成立（雇主、所屬組織、到職日、工作地點、適用的司法管轄區、約定月薪），勞保、就保、職保、健保、勞退各自的適用與否、應辦理期限、法定生效日正確
- 影響：大小估計仍為剛好（驗收問題 15 條在上限，見 01_scope.md D-09）；依賴與順序不變
- 同意者：（第 ① 步凍結時一併確認）

### 2026-10-05　PLAN　依新版工具包整理公開來源與推想草稿
- 改了什麼：inputs/research/ 95 筆條目加上「核對：[未核對]」，INDEX.md 加「已核對條目」欄（皆 0）；9 份推想草稿狀態「已同意」改稱「已接受為假設」、開頭說明改為新版文字、移除 [未核對]、有公開來源依據的句子改附條目編號；拿掉 [未核對] 的不確定點補進各草稿的「最不確定的地方」；開頭區統計改為「已接受為假設」
- 依據：docs/02 第五節（工具包更新，commit cba921f）；使用者對話（2026-10-05：選擇「現在一起整理」）
- 舊 → 新：草稿狀態 已同意 → 已接受為假設（接受者與日期不變）；草稿內容的意思不變
- 影響：無；統計數字不變
- 同意者：JiHungLin

### 2026-10-05　PLAN　hire-employee 開始
- 改了什麼：hire-employee 狀態 候選 → 進行中；建立 slices/hire-employee/ 與 core/
- 依據：使用者對話（2026-10-05：「開始跑第一條」）；D-01
- 舊 → 新：候選 → 進行中
- 影響：第 ① 步開始；範圍依 D-17（只做全職月薪）、D-18（Employer）、D-19（Person 客戶內）
- 同意者：JiHungLin

### 2026-10-05　PLAN　hourly-payroll 擱置
- 改了什麼：hourly-payroll 狀態 候選 → 擱置；D-17 理由補上去向
- 依據：使用者對話（2026-10-05，選擇「擱置」），因 D-17 第一階段只做全職月薪
- 舊 → 新：候選 → 擱置（建議順序 9 保留，之後恢復時再排）
- 影響：resignation 的依賴不含 hourly-payroll，不受影響；名詞草圖中只列 hourly-payroll 的地方保留，Shift、ClockEvent 等名詞仍由 shift-attendance 使用
- 同意者：JiHungLin

### 2026-10-05　PLAN　P-04、P-09、P-14 已回覆
- 改了什麼：P-04、P-09、P-14 改為已回覆；新增 D-17（只做全職月薪）、D-18（雇主不限法人，改稱 Employer）、D-19（Person 範圍是客戶內）
- 依據：使用者對話（2026-10-05，選擇題），存為 inputs/shared/範圍釐清_P-04_P-09_P-14.md
- 舊 → 新：三題待問 → 已回覆；切片本身尚未改動
- 影響：hire-employee 以全職月薪為範圍；名詞草圖 LegalEntity 改稱 Employer、Person 範圍確定為客戶內。hourly-payroll（兼職時薪）與 D-17 衝突，是否擱置待使用者決定
- 同意者：JiHungLin

### 2026-10-05　PLAN　已同意
- 改了什麼：狀態 討論中 → 已同意
- 依據：使用者對話（2026-10-05：「同意地圖和草圖」）；地圖引用的 9 份推想草稿都已同意
- 舊 → 新：討論中 → 已同意（與名詞草圖一起同意）
- 影響：可以開始第一條切片 hire-employee；仍待釐清的 P-04、P-06、P-07、P-09、P-10、P-13、P-14 不影響切法與順序
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：跨國派駐與轉任一般做法（9 份全部處理完）
- 改了什麼：inputs/drafts/跨國派駐與轉任一般做法.md 改為已同意
- 依據：使用者對話（2026-10-05：「同意」）
- 舊 → 新：推想草稿 已同意 8／9 → 9／9；地圖引用的推想草稿都已同意
- 影響：地圖與名詞草圖已可由使用者決定是否同意
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：美國薪資發放一般做法
- 改了什麼：inputs/drafts/美國薪資發放一般做法.md 改為已同意
- 依據：使用者對話（2026-10-05：「同意第 8 份」）
- 舊 → 新：推想草稿 已同意 7／9 → 8／9
- 影響：美國相關項目仍標 [未核對]、核心維持候選（D-11）；D-16 的加法是否適用美國，到 second-country-hire 第 ① 步確認（薪資計算方式可能要依司法管轄區或公司設定）
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：一般離職流程
- 改了什麼：inputs/drafts/一般離職流程.md 改為已同意
- 依據：使用者對話（2026-10-05：「同意第 7 份」）
- 舊 → 新：推想草稿 已同意 6／9 → 7／9
- 影響：resignation 第 ① 步可引用；離職當月薪資依 D-16，未休特休折算依勞基法 §38（特別休假#01）與 D-15
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：一般薪資結構與計薪流程
- 改了什麼：inputs/drafts/一般薪資結構與計薪流程.md 改為已同意
- 依據：使用者對話（2026-10-05：「可以，先以P-15 P-17為準」）
- 舊 → 新：推想草稿 已同意 5／9 → 6／9
- 影響：草稿中「事假、病假扣薪」列為扣款的寫法（減法）不採用，以 D-16（P-15、P-17）為準；草稿只作為薪資單常見項目與每月流程的參考
- 同意者：JiHungLin

### 2026-10-05　PLAN　P-05 補充加班；推想草稿審查：一般加班申請實務
- 改了什麼：P-05 答覆補上「加班的核准也一樣靈活」；inputs/drafts/一般加班申請實務.md 改為已同意
- 依據：使用者對話（2026-10-05：「對，小團隊也請假一樣靈活，其他都同意」），補在 inputs/shared/範圍釐清_P-05_小團隊核准.md
- 舊 → 新：加班的核准方式未定 → 與請假相同（老闆、任何同事或只需知會，也可分層級）；推想草稿 已同意 4／9 → 5／9
- 影響：overtime 第 ① 步不必再問核准人；Approval 同時適用請假與加班
- 同意者：JiHungLin

### 2026-10-05　PLAN　P-17 已回覆；推想草稿審查：一般排班與打卡實務
- 改了什麼：P-17 改為已回覆，D-16 補上「全月在職應發等於月薪」；inputs/drafts/一般排班與打卡實務.md 改為已同意
- 依據：使用者對話（2026-10-05：以例子確認選 A；「同意第 4 份」），補在 inputs/shared/範圍釐清_P-17_大小月.md
- 舊 → 新：P-17 待問 → 全月在職等於月薪，部分月份依 ÷30 日額；推想草稿 已同意 3／9 → 4／9
- 影響：monthly-payroll 的黃金案例要包含大月、二月全勤與部分月份；名詞草圖 PayItem 的備註已跟著修改
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：一般請假與簽核流程；P-17 初步答覆
- 改了什麼：inputs/drafts/一般請假與簽核流程.md 改為已同意；P-17 的初步答覆存為 inputs/shared/範圍釐清_P-17_大小月.md，P-17 維持待問，等使用者以數字例子確認意思
- 依據：使用者對話（2026-10-05：「同意第 3 份」；P-17 答覆見檔案）
- 舊 → 新：推想草稿 已同意 2／9 → 3／9
- 影響：核准方式以使用者的說明為準（inputs/shared/範圍釐清_P-05_小團隊核准.md、對話補充_核准分級_薪資加法_權益token.md），草稿只作參考
- 同意者：JiHungLin

### 2026-10-05　PLAN　P-15、P-16 已回覆
- 改了什麼：P-15、P-16 改為已回覆；新增 D-15（權益帳）、D-16（薪資用加法）、P-17（大小月的處理）；unpaid-leave-deduction 的情境由「當月扣薪正確」改為「當月應發正確」（切片代號不變）
- 依據：使用者對話（2026-10-05），存為 inputs/shared/範圍釐清_P-15_P-16.md
- 舊 → 新：薪資計算方式未定 → 加法（月薪 ÷ 30 的日額依日累計）；token 未定 → 這一階段不做，假的額度設計成權益帳
- 影響：monthly-payroll、unpaid-leave-deduction、hourly-payroll、resignation 的結果寫法依 D-16；annual-leave-grant 定義 LeaveEntitlement 時依 D-15；名詞草圖的 LeaveEntitlement、PayItem 已跟著修改
- 同意者：JiHungLin

### 2026-10-05　PLAN　使用者補充：核准分級、薪資用加法、權益 token
- 改了什麼：新增 P-15（HC 說的「薪資用加法」是什麼意思）、P-16（權益 token 這一階段做到什麼程度）；現實資料盤點第一列加上新檔
- 依據：使用者對話（2026-10-05），存為 inputs/shared/對話補充_核准分級_薪資加法_權益token.md
- 舊 → 新：無（只新增待釐清）
- 影響：核准要能分層級、依天數往上呈，annual-leave-request 第 ① 步納入；P-15 會影響 monthly-payroll、unpaid-leave-deduction、hourly-payroll；P-16 會影響 LeaveEntitlement、PayItem 的定義，以及 annual-leave-grant、resignation（特休未休折算工資）
- 同意者：（尚未同意）

### 2026-10-05　PLAN　P-05 已回覆（小團隊的核准）
- 改了什麼：P-05 改為已回覆；現實資料盤點「小團隊的核准實務」由待提供改為已有，第一列加上新檔
- 依據：使用者對話（2026-10-05），存為 inputs/shared/範圍釐清_P-05_小團隊核准.md
- 舊 → 新：核准人待定 → 請假的核准方式要能由公司決定：老闆、任何同事，或只需知會、不需核准
- 影響：annual-leave-request 第 ② 步定義 Approval 時，不能假設一定有主管、一定要核准；名詞草圖的 Approval 已跟著修改。加班的核准方式還沒有答案，到 overtime 第 ① 步再問
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：一般組織與法人結構
- 改了什麼：inputs/drafts/一般組織與法人結構.md 改為已同意
- 依據：使用者對話（2026-10-05：「同意」）
- 舊 → 新：推想草稿 已同意 1／9 → 2／9；開頭區「推想 1（已同意 0）」→「推想 1（已同意 1）」（internal-transfer 唯一的依據即此草稿）
- 影響：草稿中「最不確定的地方」（部門可否跨法人、小團隊是否有組織、集團的表示方式）仍未回答，到 hire-employee 第 ② 步再決定
- 同意者：JiHungLin

### 2026-10-05　PLAN　推想草稿審查：一般到職流程
- 改了什麼：inputs/drafts/一般到職流程.md 改為已同意；使用者補充的試用期做法存為 inputs/shared/範圍釐清_試用期.md，加入現實資料盤點第一列
- 依據：使用者對話（2026-10-05：「大致同意，所以試用期應該算正式聘用，只是試用期過了時候，薪資結構會調整」）
- 舊 → 新：推想草稿 已同意 0／9 → 1／9；切片依據統計不變
- 影響：hire-employee 第 ① 步可引用此草稿（驗收問題來源仍寫 AI）；草稿第 2 點「離職證明有時用來辦勞健保轉出」這句未經確認，到 hire-employee 第 ① 步時不採用，或寫進 questions.md 問 HC
- 同意者：JiHungLin

### 2026-10-05　PLAN　公開來源改依新版規則整理
- 改了什麼：「依據」欄與現實資料盤點中的 inputs/research/ 檔名去掉國家前綴（例：台灣_特別休假.md → 特別休假.md、美國_聯邦與紐約.md → 聯邦與紐約.md）；國家改寫在各條目的「適用範圍」欄位，並新增 inputs/research/INDEX.md
- 依據：docs/02 第五節 inputs/research/（工具包更新，commit 404fb49）；使用者對話（2026-10-05）
- 舊 → 新：只改檔名路徑，依據的內容、等級與統計數字不變
- 影響：無；之後引用公開來源改寫條目編號（例：特別休假#01）
- 同意者：（尚未同意）

### 2026-10-05　PLAN　現實資料盤點（依新版工具包）
- 改了什麼：新增「現實資料盤點」（33 項：已有 2、已蒐集 11、推想草稿 9、待提供 10、找不到 1）；切片表加「依據」欄，15 條切片都補上依據；開頭區加依據統計；新增 D-14（依據的統計方式）
- 依據：使用者對話（2026-10-05：先收集資料，再一起同意地圖與草圖）；新增 inputs/research/ 11 份公開來源、inputs/drafts/ 9 份推想草稿（待同意）
- 舊 → 新：切片沒有標依據 → 每條切片標出依據；現場資料 6、公開來源 8、推想 1；切片本身沒有增減
- 影響：地圖要等引用的 9 份推想草稿都由使用者處理（同意或不同意）後才能同意；待提供的現場資料要在約 HC 時一起提出
- 同意者：（尚未同意）

### 2026-10-05　PLAN　新增全局名詞草圖
- 改了什麼：新增 D-13（另開全局名詞草圖）；新增 P-13（台灣薪資所得扣繳是否算進實發）、P-14（是否支援非法人雇主）
- 依據：使用者對話（2026-10-05：老闆要求先規劃全局 entity，目前沒有既有文件）；slices/ENTITY_SKETCH.md 初版
- 舊 → 新：只有切片地圖 → 切片地圖加全局名詞草圖，兩份一起同意
- 影響：每條切片第 ② 步要對照草圖；hire-employee 第 ② 步預計正式定義 10 個共用名詞
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　P-04、P-09、P-14 已回覆
- 改了什麼：LegalEntity（法人／雇主）改稱 Employer（雇主），一句意思加上「可以是公司法人、獨資或合夥商號、個人雇主」，全文 13 處同步改名（變更紀錄舊條目不改）；Person、Employment、Employer 的依據加上新檔；「不確定的地方」中 Person、Employment、Employer 三點改寫為答覆
- 依據：使用者對話（2026-10-05），inputs/shared/範圍釐清_P-04_P-09_P-14.md；PLAN.md D-17～D-19
- 舊 → 新：LegalEntity → Employer；Person 範圍待定 → 客戶內；員工類型待定 → 第一階段只做全職月薪；統計不變（現場 13、公開 16、推想 4）
- 影響：hire-employee 第 ② 步以 Employer 定義雇主；草圖已同意後的修改，請使用者確認
- 同意者：JiHungLin（P-04、P-09、P-14 的答覆）

### 2026-10-05　SKETCH　已同意
- 改了什麼：狀態 討論中 → 已同意
- 依據：使用者對話（2026-10-05：「同意地圖和草圖」）；地圖引用的 9 份推想草稿都已同意
- 舊 → 新：討論中 → 已同意（與切片地圖一起同意）
- 影響：可以開始第一條切片 hire-employee；仍待釐清的 P-04、P-06、P-07、P-09、P-10、P-13、P-14 不影響切法與順序
- 同意者：JiHungLin

### 2026-10-05　SKETCH　P-17 已回覆
- 改了什麼：「PayItem 用加法」一點補上大小月的處理
- 依據：使用者對話（2026-10-05），inputs/shared/範圍釐清_P-17_大小月.md
- 舊 → 新：大小月待 P-17 → 全月在職等於月薪，部分月份依 ÷30 日額
- 影響：無新增名詞；統計不變
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　P-15、P-16 已回覆
- 改了什麼：LeaveEntitlement、PayItem 的依據加上 inputs/shared/範圍釐清_P-15_P-16.md；「資料盤點後發現的事」新增兩點（權益帳、加法）
- 依據：使用者對話（2026-10-05）；PLAN.md D-15、D-16
- 舊 → 新：LeaveEntitlement、PayItem 依據 公開來源 → 現場資料；統計 現場 11、公開 18 → 現場 13、公開 16
- 影響：annual-leave-grant 第 ② 步定義 LeaveEntitlement 要容納多種來源與轉換；monthly-payroll 第 ② 步定義 PayItem 依加法
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　P-05 已回覆（小團隊的核准）
- 改了什麼：Approval 的「一句意思」與「主管關係」改為可以是核准、駁回或只是知會，核准人不一定來自 Position；依據加上 inputs/shared/範圍釐清_P-05_小團隊核准.md；OrgUnit 的不確定事項更新為 P-05 的答覆
- 依據：使用者對話（2026-10-05）
- 舊 → 新：Approval「由 Person 依其 Position 作出」→「由 Person 作出，可依 Position、由公司指定，或只需知會」；Approval 依據 公開來源 → 現場資料；統計 現場 10、公開 19 → 現場 11、公開 18
- 影響：annual-leave-request 第 ② 步定義 Approval 時要涵蓋「免核准、只知會」；Position 仍保留，但不是找出核准人的唯一方式
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　使用者補充試用期做法
- 改了什麼：Employment、Compensation 的依據加上 inputs/shared/範圍釐清_試用期.md；「不確定的地方」的 Employment 加一點：試用期是同一段僱傭關係中的期間，期滿後薪資調整
- 依據：使用者對話（2026-10-05，審查 inputs/drafts/一般到職流程.md 時補充）
- 舊 → 新：Compensation 依據 公開來源 → 現場資料；統計 現場 9、公開 20 → 現場 10、公開 19
- 影響：hire-employee 第 ② 步定義 Employment 時要能表示試用期間；Compensation 要有生效日與多個版本
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　公開來源改依新版規則整理
- 改了什麼：「依據」欄與現實資料盤點中的 inputs/research/ 檔名去掉國家前綴（例：台灣_特別休假.md → 特別休假.md、美國_聯邦與紐約.md → 聯邦與紐約.md）；國家改寫在各條目的「適用範圍」欄位，並新增 inputs/research/INDEX.md
- 依據：docs/02 第五節 inputs/research/（工具包更新，commit 404fb49）；使用者對話（2026-10-05）
- 舊 → 新：只改檔名路徑，依據的內容、等級與統計數字不變
- 影響：無；之後引用公開來源改寫條目編號（例：特別休假#01）
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　現實資料盤點，補上依據
- 改了什麼：名詞表加「依據」欄，33 個名詞都補上依據；開頭區加依據統計；「不確定的地方」新增「資料盤點後發現的事」8 點
- 依據：inputs/research/ 11 份公開來源、inputs/drafts/ 9 份推想草稿（待同意）；slices/PLAN.md 的現實資料盤點
- 舊 → 新：名詞沒有標依據 → 現場資料 9、公開來源 20、推想 4；名詞本身沒有增減，層與正式定義於不變
- 影響：hire-employee 第 ② 步定義 InsuranceEnrollment、LegalEntity 時要考慮各保險制度生效規則不同與雇主規模；annual-leave-grant 定義 LeaveEntitlement 時要容納按工時累積
- 同意者：（尚未同意）

### 2026-10-05　SKETCH　初版
- 改了什麼：列出 33 個名詞，涵蓋地圖上 15 條切片；寫出五個關鍵名詞（Person、Employment、LegalEntity、OrgUnit、Jurisdiction）需要支撐的後續需求
- 依據：slices/PLAN.md（2026-10-05 版）、inputs/shared/ 各檔、使用者對草圖格式的要求（對話，2026-10-05）
- 影響：hire-employee 第 ② 步要定義 10 個名詞，並對照本草圖確認撐得起後續切片；新增 P-13、P-14
- 同意者：（尚未同意）

### 2026-10-05　PLAN　早期的一行式紀錄
- 2026-10-05：補充 P-08（專家代稱 HC、問題批次處理）；新增 D-12
- 2026-10-05：P-08、P-11、P-12 已回覆（有台灣專家、美國先做紐約市、沒有美國專家）；P-10 改問台灣人資專家；新增 D-11
- 2026-10-05：P-03 已回覆（美國）；第二個國家切片改寫為美國；新增 P-11、P-12、D-10
- 2026-10-05：P-01 已回覆（支援優於法令的公司規定）；新增 P-10、D-09
- 2026-10-05：P-02 已回覆（多租戶產品、混合部署）；更新整體目標與明確不做；新增 P-09、D-07、D-08
- 2026-10-05：初版（依 inputs/shared/初始需求.md、inputs/shared/範圍釐清_第一次.md）
