# 全局名詞草圖

<!-- 規劃用的參考，不是 Ontology；正式定義只在 core/。
     只寫：名詞、一句意思、層、主要關係、會用到的切片、正式定義於。不寫屬性、幾對幾、規則。
     層：core／shared／domain。狀態：草圖／已定義／已取消。
     已定義的名詞，「一句意思」改成「見 core/entities.md」。 -->

| 項目 | 內容 |
|---|---|
| 狀態 | 討論中 |
| 最後更新 | 2026-10-05 |
| 依據 | 名詞 33 個：現場資料 9、公開來源 20、推想 4。統計按每列最高一級的依據計（見 PLAN.md D-14）；33 個中有 15 個引用了推想草稿 |

## 名詞

<!-- 依據：inputs/ 的檔案（可加章節），或「推想」 -->

| 名詞 | 一句意思 | 層 | 主要關係 | 會用到的切片 | 正式定義於 | 依據 | 狀態 |
|---|---|---|---|---|---|---|---|
| Tenant（客戶） | 購買並使用本產品的一個客戶；它底下的法人、組織、人事資料都歸屬於它 | core | 擁有 LegalEntity、OrgUnit、CompanyPolicy；是人事資料的歸屬範圍 | 全部 | hire-employee | inputs/shared/範圍釐清_P-02_產品形態.md | 草圖 |
| Person（人） | 一個真實的人，可以沒有僱傭關係而存在（求職者、離職者） | core | 擁有 Employment；可以是另一個 Person 的眷屬（DependentRelation）；可以作出 Approval；可以持有 WorkAuthorization | 全部 | hire-employee | inputs/shared/範圍釐清_P-02_產品形態.md；research/勞動契約與年資.md（勞工名卡 §7） | 草圖 |
| Jurisdiction（司法管轄區） | 訂定勞動、社會保險、稅務規則的地區，可以多層（國家 → 州 → 市） | core | 有上一層 Jurisdiction；WorkLocation 位於其中；LegalEntity 註冊於此；訂定 SocialInsuranceScheme、LeaveType、HolidayCalendar | 全部 | hire-employee | inputs/shared/範圍釐清_P-03_第二個國家.md、範圍釐清_P-11_P-12.md；research/聯邦與紐約.md（聯邦、州、市三層） | 草圖 |
| LegalEntity（法人／雇主） | 以自己名義僱用員工、發薪、投保的主體 | core | 屬於 Tenant；註冊於 Jurisdiction；是 Employment 的雇主；是 InsuranceEnrollment 的投保單位；發放 Payslip | 全部 | hire-employee | inputs/shared/範圍釐清_第一次.md（分公司、多法人）；research/勞動契約與年資.md（雇主 §2）、勞保就保職保.md（投保單位）；drafts/一般組織與法人結構.md | 草圖 |
| OrgUnit（組織單位） | 客戶內部的分公司、部門、團隊等單位；小團隊可以完全沒有 | core | 屬於 Tenant；有上一層 OrgUnit；Employment 隸屬於它；可以位於某個 WorkLocation；包含 Position | hire-employee、annual-leave-request、internal-transfer、second-country-hire | hire-employee | inputs/shared/範圍釐清_第一次.md（大有分公司、小沒有部門）；drafts/一般組織與法人結構.md | 草圖 |
| WorkLocation（工作地點） | 員工實際提供勞務的地點，用來決定適用哪些 Jurisdiction 的規則 | shared | 位於 Jurisdiction；Employment 在此工作；Assignment 派往此處；套用 HolidayCalendar | hire-employee、shift-attendance、second-country-hire、assignment-leave、assignment-payroll、cross-border-transfer | hire-employee | inputs/research/勞動契約與年資.md（細則 §7 工作場所）、聯邦與紐約.md（紐約市 ESSTA 依工作地點適用） | 草圖 |
| Employment（僱傭關係） | 一個人與一個雇主之間的一段僱傭關係，從到職到離職 | shared | 連結 Person 與 LegalEntity；隸屬 OrgUnit；在 WorkLocation 工作；依據 EmploymentContract；有 Compensation、LeaveEntitlement、InsuranceEnrollment；可以有 Assignment；可以承接前一段 Employment（年資承認）；以 Separation 結束 | 全部 | hire-employee | inputs/shared/範圍釐清_P-02_產品形態.md（D-08）；research/勞動契約與年資.md（§2、§9、§10） | 草圖 |
| EmploymentContract（勞動契約） | 雙方約定僱傭條件的契約，可為不定期或定期 | shared | Employment 依據它成立 | hire-employee、resignation、cross-border-transfer | hire-employee | inputs/research/勞動契約與年資.md（§9、細則 §7） | 草圖 |
| SocialInsuranceScheme（社會保險制度） | 一個司法管轄區規定的強制保險或提撥制度（例：勞保、健保、勞工退休金） | domain | 由 Jurisdiction 訂定；InsuranceEnrollment 加入它 | hire-employee、social-insurance、hourly-payroll、resignation、second-country-hire、assignment-payroll | hire-employee | inputs/research/勞保就保職保.md、全民健康保險.md、勞工退休金.md | 草圖 |
| InsuranceEnrollment（投保） | 一段僱傭關係在某個社會保險制度下，從加保到退保的期間 | domain | 屬於 Employment；加入 SocialInsuranceScheme；投保單位是 LegalEntity；可以涵蓋眷屬（DependentRelation）；產生 PayItem | hire-employee、social-insurance、hourly-payroll、resignation、second-country-hire、assignment-payroll | hire-employee | inputs/research/勞保就保職保.md（勞保 §11、職保 §13）、全民健康保險.md（§15、§30）、勞工退休金.md（§18） | 草圖 |
| CompanyPolicy（公司規定） | 客戶在法令範圍內自訂、對員工更有利的規定（例：特休多給） | shared | 由 Tenant 或 LegalEntity 訂定；調整某個 Jurisdiction 的法令規則；適用於全部或部分 Employment；可以定義 LeaveType、HolidayCalendar | annual-leave-grant、annual-leave-request、overtime、monthly-payroll、unpaid-leave-deduction、resignation、second-country-hire | annual-leave-grant | inputs/shared/範圍釐清_P-01_優於法令.md；research/勞動契約與年資.md（§1、§70 工作規則） | 草圖 |
| LeaveType（假別） | 一種假（特休、病假、事假…），由法令或公司規定產生 | domain | 由 Jurisdiction 或 CompanyPolicy 定義；LeaveEntitlement、LeaveRequest 屬於某個假別 | annual-leave-grant、annual-leave-request、unpaid-leave-deduction、second-country-hire、assignment-leave | annual-leave-grant | inputs/research/請假.md | 草圖 |
| LeaveEntitlement（請假權利） | 員工因年資、事件或規定取得的請假權利，有額度與有效期間 | domain | 屬於 Employment；屬於 LeaveType；來源是法令或 CompanyPolicy；被 LeaveOccurrence 扣用；離職時未用完的部分產生 PayItem | annual-leave-grant、annual-leave-request、unpaid-leave-deduction、resignation、second-country-hire、assignment-leave、cross-border-transfer | annual-leave-grant | inputs/research/特別休假.md、聯邦與紐約.md（按工時累積的病假） | 草圖 |
| LeaveRequest（請假申請） | 員工提出的請假申請 | domain | 由 Person 為某段 Employment 提出；指定 LeaveType；經過 Approval；可以附 Evidence | annual-leave-request、unpaid-leave-deduction、internal-transfer、assignment-leave | annual-leave-request | inputs/research/請假.md（請假規則 §10）；drafts/一般請假與簽核流程.md | 草圖 |
| LeaveOccurrence（請假事實） | 實際請假的時段，會扣用請假權利 | domain | 源自 LeaveRequest；扣用 LeaveEntitlement；對應 ShiftAssignment；影響 AttendanceRecord 與 PayItem | annual-leave-request、shift-attendance、monthly-payroll、unpaid-leave-deduction、assignment-leave | annual-leave-request | inputs/drafts/一般請假與簽核流程.md | 草圖 |
| Position（職位） | 組織中的一個職位，包含主管職；用來找出核准人 | shared | 屬於 OrgUnit；由 Employment 擔任 | annual-leave-request、overtime、unpaid-leave-deduction、internal-transfer | annual-leave-request | inputs/drafts/一般組織與法人結構.md | 草圖 |
| Approval（核准） | 有權限的人對一項申請作出的核准或駁回 | shared | 針對 LeaveRequest 或 OvertimeRequest；由 Person 依其 Position 作出 | annual-leave-request、overtime、unpaid-leave-deduction、internal-transfer | annual-leave-request | inputs/research/請假.md（性平法 §21）；drafts/一般請假與簽核流程.md | 草圖 |
| HolidayCalendar（假日曆） | 某地區或公司的國定假日與休息日 | shared | 由 Jurisdiction 或 CompanyPolicy 訂定；套用於 WorkLocation | annual-leave-request、shift-attendance、overtime、second-country-hire、assignment-leave | shift-attendance | inputs/research/工時加班與休假日.md（§37） | 草圖 |
| Shift（班別） | 一種上班時段的定義（例：早班 8–17） | domain | 由 Tenant 訂定；ShiftAssignment 使用它 | shift-attendance、overtime、hourly-payroll | shift-attendance | inputs/drafts/一般排班與打卡實務.md | 草圖 |
| ShiftAssignment（排班） | 某人在某天被排定的班 | domain | 屬於 Employment；使用 Shift；在 WorkLocation | annual-leave-request、shift-attendance、overtime、unpaid-leave-deduction、hourly-payroll | shift-attendance | inputs/research/工時加班與休假日.md（§36）；drafts/一般排班與打卡實務.md | 草圖 |
| ClockEvent（打卡） | 員工上班或下班時記錄的時間點 | domain | 屬於 Employment；對應 ShiftAssignment | shift-attendance、overtime、hourly-payroll | shift-attendance | inputs/research/工時加班與休假日.md（§30 出勤紀錄到分鐘）；drafts/一般排班與打卡實務.md | 草圖 |
| AttendanceRecord（出勤結果） | 某人某天的出勤判定（正常、遲到、早退、缺勤） | domain | 由 ShiftAssignment、ClockEvent、LeaveOccurrence 判定；產生 PayItem | shift-attendance、overtime、monthly-payroll、unpaid-leave-deduction、hourly-payroll | shift-attendance | inputs/research/工時加班與休假日.md（§30）；drafts/一般排班與打卡實務.md | 草圖 |
| OvertimeRequest（加班申請） | 員工在排定工時以外工作的申請與紀錄 | domain | 屬於 Employment；經過 Approval；產生 PayItem | overtime、monthly-payroll | overtime | inputs/research/工時加班與休假日.md（§24、§32）；drafts/一般加班申請實務.md | 草圖 |
| Compensation（約定薪資） | 僱傭關係約定的薪資：計薪方式（月薪或時薪）、金額、幣別，會隨時間調整 | shared | 屬於 Employment；是 Payslip 的計算基礎 | monthly-payroll、social-insurance、hourly-payroll、resignation、second-country-hire、assignment-payroll | monthly-payroll | inputs/research/工資與最低工資.md（§21）、勞動契約與年資.md（細則 §7） | 草圖 |
| PayrollPeriod（計薪期間） | 一次薪資結算涵蓋的期間（例：某年某月） | domain | 由 LegalEntity 結算；包含 Payslip | monthly-payroll、social-insurance、unpaid-leave-deduction、hourly-payroll、resignation、second-country-hire、assignment-payroll | monthly-payroll | inputs/research/工資與最低工資.md（§23） | 草圖 |
| Payslip（薪資單） | 某人在某計薪期間的薪資結果 | domain | 屬於 Employment 與 PayrollPeriod；由 LegalEntity 發放；包含 PayItem | monthly-payroll、social-insurance、unpaid-leave-deduction、hourly-payroll、resignation、second-country-hire、assignment-payroll | monthly-payroll | inputs/research/工資與最低工資.md（細則 §14-1） | 草圖 |
| PayItem（薪資項目） | 薪資單上的一行（底薪、加班費、請假扣款、保險自付額…） | domain | 屬於 Payslip；可以追溯到來源（AttendanceRecord、LeaveOccurrence、OvertimeRequest、InsuranceEnrollment、LeaveEntitlement） | monthly-payroll、social-insurance、unpaid-leave-deduction、hourly-payroll、resignation、second-country-hire、assignment-payroll | monthly-payroll | inputs/research/工資與最低工資.md（細則 §14-1）；drafts/一般薪資結構與計薪流程.md | 草圖 |
| DependentRelation（眷屬關係） | 一個人是另一個人的眷屬（例：健保依附加保） | shared | 連結兩個 Person；被 InsuranceEnrollment 涵蓋 | social-insurance | social-insurance | inputs/research/全民健康保險.md（§2） | 草圖 |
| Evidence（佐證） | 支持一項申請或事實的文件（例：診斷證明） | core | 附於 LeaveRequest | unpaid-leave-deduction | unpaid-leave-deduction | inputs/research/請假.md（請假規則 §10） | 草圖 |
| Separation（離職） | 僱傭關係結束這件事，包含原因與最後工作日 | shared | 結束 Employment；觸發 InsuranceEnrollment 退保、LeaveEntitlement 結算、最後一期 Payslip | resignation、cross-border-transfer | resignation | inputs/shared/範圍釐清_第一次.md（到職離職）；research/離職與資遣.md；drafts/一般離職流程.md | 草圖 |
| WorkAuthorization（工作許可） | 一個人在某個司法管轄區合法工作的資格 | shared | 屬於 Person；針對 Jurisdiction；是成立 Employment 或 Assignment 的前提 | second-country-hire、assignment-leave、cross-border-transfer | second-country-hire | inputs/drafts/一般到職流程.md | 草圖 |
| TaxWithholdingElection（扣繳申報資料） | 員工為了薪資所得扣繳而提供的申報資料（例：美國的 W-4 `[未核對]`） | domain | 屬於 Person；針對 Jurisdiction；影響 PayItem | second-country-hire、assignment-payroll | second-country-hire（待 P-13） | inputs/research/聯邦與紐約.md（W-4）、薪資所得扣繳.md（扣繳率標準 §2 由納稅義務人選定） | 草圖 |
| Assignment（派駐） | 不結束原僱傭關係，員工被派到另一地工作的一段期間 | domain | 屬於 Employment；派往 WorkLocation；可能有當地的 LegalEntity 參與 | assignment-leave、assignment-payroll、cross-border-transfer | assignment-leave | inputs/shared/範圍釐清_第一次.md（外派）；drafts/跨國派駐與轉任一般做法.md | 草圖 |

## 不確定的地方

### 被很多切片用到的名詞：後面的切片需要它們具備什麼
hire-employee 正式定義這些名詞時，要能支撐下列需求；做不到的寫進該切片的「不做」並在這裡註明。

- **Person**
  - 獨立於 Employment 存在（D-08）；同一個人可以先後或同時有多段 Employment（兼職兩個雇主、跨國轉任前後兩段）。
  - 薪資與跨國切片需要能掛上多個國家的身分與稅務識別（台灣身分證或居留證、美國 SSN `[未核對]`），以及稅務居住身分（台灣以居留天數判斷 `[未核對]`）。
  - social-insurance 需要眷屬關係指向另一個 Person。
  - 同一個人在不同 Tenant 之間要不要認得出來，待 P-09；這會決定 Person 的範圍是「客戶內」還是「跨客戶」。
- **Employment**
  - 雇主是 LegalEntity，不是 OrgUnit、也不是 Tenant；薪資、投保、年資都以法人為單位計算。
  - 隸屬的 OrgUnit 會隨時間改變，要保留生效期間與歷史（internal-transfer：生效日前的紀錄不變）。
  - 工作地點（WorkLocation）可以和雇主註冊的國家不同（遠距、派駐），適用規則依工作地點判斷（見 Jurisdiction）。
  - 派駐時 Employment 不結束，另外加一段 Assignment（assignment-leave、assignment-payroll）；跨國轉任時結束舊的、成立新的，新舊之間要能連結，才能承認年資（cross-border-transfer）。
  - 計薪方式（月薪或時薪）與員工類型（P-04）會影響請假、加班、薪資的規則。
  - 年資是推導出來的值，來源包括本段到職日，以及被承認的前一段僱傭關係。
- **LegalEntity**
  - 註冊於一個 Jurisdiction；同時是投保單位、扣繳義務人、發薪主體。
  - 一個 Tenant 可以有多個 LegalEntity，而且可以跨國（台灣公司加美國子公司）。
  - 台灣的分公司通常與總公司是同一個法人 `[未核對]`，用 OrgUnit 表示；美國子公司是另一個法人。
  - 小型客戶可能是獨資商號或個人雇主，不是法人，待 P-14；若要支援，名稱可能改為 Employer（雇主）。
- **OrgUnit**
  - 可有可無：沒有部門的小團隊，Employment 不隸屬任何 OrgUnit 也要能運作；此時核准人從哪裡來，待 P-05。
  - 是樹狀結構，分公司可以有自己的 WorkLocation；結構本身也會隨時間改組。
  - 一個 OrgUnit 可不可以跨 LegalEntity（集團共用的部門），由 hire-employee 第 ② 步決定。
- **Jurisdiction 與適用的規則**
  - 多層（D-10）：一段 Employment 會同時適用好幾層（例：美國聯邦、紐約州、紐約市），台灣只有一層。
  - 適用哪些規則，預計依 WorkLocation 判斷，不依雇主所在國或員工國籍 `[未核對]`；派駐期間可能同時涉及兩國（assignment-leave、assignment-payroll）。
  - 社會保險歸屬可能和勞動法的適用國不同（例：國與國之間的社會安全協定 `[未核對]`），所以 InsuranceEnrollment 透過 SocialInsuranceScheme 連到 Jurisdiction，不直接沿用 Employment 的工作地點。
  - 公司規定在法令之上調整（D-09）；規則會隨時間修改，舊結果要能依當時的版本解釋（docs/03 P5）。

### 其他不確定
- EmploymentContract 要不要和 Employment 合併成一個名詞，由 hire-employee 第 ② 步決定。
- LeaveType 可能是分類值而不是 Entity；如果法令和公司規定都只是在固定清單裡選，用分類值就夠了。由 annual-leave-grant 第 ② 步決定。
- 台灣的變形工時、輪班制度可能需要比 Shift 更多的名詞（例：工時制度）；目前沒有切片涵蓋，到 shift-attendance 第 ① 步再看。
- 台灣的薪資所得扣繳是否算在 social-insurance 的「實發金額」裡，待 P-13；若是，TaxWithholdingElection 改由 social-insurance 正式定義。
- assignment-payroll 的幣別換算可能需要「匯率」這個名詞；目前不列，到該切片第 ① 步再看。
- 同一段 Employment 有多個工作地點（例：一半遠距），目前不列，到 second-country-hire 第 ① 步再看。

### 資料盤點後發現的事（2026-10-05）
- **InsuranceEnrollment 要按制度分開**：勞保自「通知當日」生效（未在到職當日通知者自翌日起），職保自「到職當日」起，健保在三日內辦理、投保當月繳全月，勞退在七日內通知 `[未核對]`（inputs/research/勞保就保職保.md、全民健康保險.md、勞工退休金.md）。hire-employee 的「應加保日」要對每個 SocialInsuranceScheme 分別判斷，不能只有一個加保日。
- **雇主規模會影響規則**：勞保 5 人門檻、工作規則 30 人門檻、紐約州與紐約市病假依 5／100 人分級 `[未核對]`。LegalEntity（或 Tenant）需要能推得「某時點的僱用人數」，由 hire-employee 第 ② 步決定放在哪。
- **LeaveEntitlement 有兩種取得方式**：台灣特休依年資「一次給予」，紐約病假依工時「累積」（每 30 小時 1 小時）`[未核對]`。annual-leave-grant 定義時要留這個空間，不要把「依年資給予」寫死在名詞裡。
- **特休年度可以選**：施行細則 §24 允許週年制、曆年制、會計年度等 `[未核對]`，P-06 從「要不要支援」變成「產品要支援哪幾種」；LeaveEntitlement 的有效期間依公司選的年度制度而定。
- **TaxWithholdingElection 台灣也有**：台灣薪資扣繳可由納稅義務人選擇「依扣繳辦法」或「按 5%」`[未核對]`（inputs/research/薪資所得扣繳.md）。若 P-13 決定算進實發，它改由 social-insurance 正式定義，層可能從 domain 改為 shared。
- **有些申請不能被駁回**：性平法 §21 規定部分假別雇主不得拒絕 `[未核對]`。Approval 不一定都是「可以核准也可以駁回」，由 annual-leave-request 第 ② 步確認。
- **健保眷屬保費**：員工自付按實際眷屬人數（最多三口），雇主負擔按平均眷口數 `[未核對]`（健保法 §18、§29）。DependentRelation 會直接影響 PayItem 的金額。
- **WorkAuthorization 目前只有推想**：工作許可的公開來源（就業服務法）本次沒有蒐集，到 second-country-hire 第 ① 步前補上。

## 變更紀錄
<!-- 只新增，最新的在最上面。每筆：
### <日期>　<事件>
- 改了什麼：
- 依據：
- 舊 → 新：
- 影響：
- 同意者：
-->

### 2026-10-05　公開來源改依新版規則整理
- 改了什麼：「依據」欄與現實資料盤點中的 inputs/research/ 檔名去掉國家前綴（例：台灣_特別休假.md → 特別休假.md、美國_聯邦與紐約.md → 聯邦與紐約.md）；國家改寫在各條目的「適用範圍」欄位，並新增 inputs/research/INDEX.md
- 依據：docs/02 第五節 inputs/research/（工具包更新，commit 404fb49）；使用者對話（2026-10-05）
- 舊 → 新：只改檔名路徑，依據的內容、等級與統計數字不變
- 影響：無；之後引用公開來源改寫條目編號（例：特別休假#01）
- 同意者：（尚未同意）

### 2026-10-05　現實資料盤點，補上依據
- 改了什麼：名詞表加「依據」欄，33 個名詞都補上依據；開頭區加依據統計；「不確定的地方」新增「資料盤點後發現的事」8 點
- 依據：inputs/research/ 11 份公開來源、inputs/drafts/ 9 份推想草稿（待同意）；slices/PLAN.md 的現實資料盤點
- 舊 → 新：名詞沒有標依據 → 現場資料 9、公開來源 20、推想 4；名詞本身沒有增減，層與正式定義於不變
- 影響：hire-employee 第 ② 步定義 InsuranceEnrollment、LegalEntity 時要考慮各保險制度生效規則不同與雇主規模；annual-leave-grant 定義 LeaveEntitlement 時要容納按工時累積
- 同意者：（尚未同意）

### 2026-10-05　初版
- 改了什麼：列出 33 個名詞，涵蓋地圖上 15 條切片；寫出五個關鍵名詞（Person、Employment、LegalEntity、OrgUnit、Jurisdiction）需要支撐的後續需求
- 依據：slices/PLAN.md（2026-10-05 版）、inputs/shared/ 各檔、使用者對草圖格式的要求（對話，2026-10-05）
- 影響：hire-employee 第 ② 步要定義 10 個名詞，並對照本草圖確認撐得起後續切片；新增 P-13、P-14
- 同意者：（尚未同意）
