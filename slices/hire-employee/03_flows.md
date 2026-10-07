# hire-employee ③ 流程與狀態

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ③ 流程與狀態 |
| 狀態 | 草稿 |
| 版本 | （凍結後填 tag，例：hire-employee/03-v1） |
| 產出者 | AI（Claude） |
| 讀取的輸入 | 01_scope.md @ hire-employee/01-v1；02_entities.md @ hire-employee/02-v1；slices/PLAN.md D-27、D-28、D-29、D-33 @ 4d051d4；docs/03 P1～P4（平台約定未填，只引用其分類） |

<!-- 本文件的「誰可以做」用業務角色：
     人資＝雇主指定處理人事的人（小雇主可以是老闆本人；平台 P-05 小團隊沒有部門也照樣有人資）
     員工＝當事人；系統＝依規則自動產生，只能產生「建議」層的事件或依條件推導的狀態變化 -->

## 狀態機
<!-- 歷史需求：只需現況／需要軌跡／需要重建當時（依 Qnn）。「規則」欄第 ④ 步回填 -->

### Hire（錄用）（歷史需求：需要軌跡，依 Q14）
狀態：Hired（已錄用）→ Started（已到職）／Cancelled（到職前取消）
終態：Started、Cancelled

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Hired | DecideHire | 人資 | 人已登錄（新的人或同客戶內既有的人，Q11）；有雇主與約定到職日 | |
| Hired | Hired | RescheduleStart | 人資 | 新的到職日和原本不同；原本的到職日保留（Q14） | |
| Hired | Started | StartEmployment | 人資 | 這個人已經實際開始提供勞務（01_scope D-07）；到職日不早於決定錄用日 | |
| Hired | Cancelled | CancelHire | 人資 | 還沒開始提供勞務；到職日當天沒來也屬這一種（01_scope D-12） | |
| Started | Cancelled | CorrectRecord（更正誤登到職） | 人資 | 這個人其實從未開始提供勞務；原本的到職紀錄保留並標為錯誤登錄（D-03） | |
| Cancelled | Started | CorrectRecord（更正誤登取消） | 人資 | 這個人其實已經到職；原本的取消紀錄保留並標為錯誤登錄，補登到職（D-03） | |

### Employment（僱傭關係）（歷史需求：需要重建當時，依 Q13、Q15、Q18）
狀態：Active（在職）→ Ended（已結束）；Active → RecordedInError（錯誤登錄）
終態：Ended、RecordedInError

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | StartEmployment | 人資 | 來自一筆 Hired 的錄用 | |
| （無） | Active | RegisterExistingEmployment | 人資 | 客戶開始使用系統前就到職的員工，沒有錄用紀錄（02 D-12） | |
| （無） | Ended | RegisterExistingEmployment | 人資 | 補登已離職的既有員工（例：回任時要找得到的先前一段，Q11） | |
| Active | Ended | RecordEarlyDeparture | 人資 | 結束日不早於到職日；本切片只處理到職後立刻離開（01_scope D-12），一般離職由 resignation 定義觸發事件 | |
| Active | RecordedInError | CorrectRecord（更正誤登到職） | 人資 | 這個人其實從未開始提供勞務；這段僱傭關係不算數，不計入人數與年資（D-03） | |

說明：需要重建當時，是因為到職日、雇主、工作地點等被更正後，要依更正後的資料重新判定各保險，也要看得出更正前的判定（Q15），以及當時依哪一版規則（Q13）。

### EmploymentContract（勞動契約）（歷史需求：需要軌跡，依 Q15、Q19）
狀態：Signed（已簽訂，尚未生效）→ InForce（生效中）→ Ended（已結束）；Signed → Voided（隨錄用取消而失效）
終態：Ended、Voided

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Signed | SignContract | 人資 | 掛在錄用上（到職前簽，02 D-18）或僱傭關係上 | |
| Signed | InForce | StartEmployment | 系統（隨到職） | 契約起日不晚於到職日；起日晚於到職日時，等起日到達（ContractTermStarts） | |
| Signed | InForce | ContractTermStarts | 系統 | 已到職，且契約起日到達（續約的新契約） | |
| Signed | Voided | CancelHire | 系統（隨錄用取消） | 契約掛在被取消的錄用上 | |
| InForce | Ended | RecordEarlyDeparture | 系統（隨僱傭關係結束） | — | |

說明：定期契約到期、續約、視為不定期契約都不在本切片（01_scope 不做），到期的轉換由 resignation 定義。

### WorkAuthorization（工作許可）（歷史需求：需要重建當時，依 Q16）
狀態：Valid（有效）→ Expired（已到期）
終態：Expired

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordWorkAuthorization | 人資 | 依主管機關核發的許可函登錄；免申請者依身分證件登錄（02 D-06） | |
| Valid | Expired | ExpireWorkAuthorization | 系統 | 期限屆滿；免申請者在依據的身分消失時（例：居留事由改變，見 IdentityDocument） | |

說明：要重建「到職日那天許可是否有效、發給哪個雇主」（Q16），所以許可的歷史（含展延換發的文號）要保留。申請、展延、廢止、轉換雇主不在本切片（01_scope 不做），展延時的轉換留給之後的切片。

### IdentityDocument（身分證件）（歷史需求：需要重建當時，依 Q06、Q10）
狀態：Valid（有效）→ Expired（已到期）／Superseded（被新的一筆取代）
終態：Expired、Superseded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordIdentityDocument | 人資 | 依員工出示的證件登錄（不代管證件，01_scope D-20） | |
| Valid | Superseded | RecordIdentityDocument | 人資 | 換發、展延，或居留事由改變而另記一筆（02 D-05） | |
| Valid | Expired | ExpireIdentityDocument | 系統 | 有效期限屆滿 | |

說明：健保、就保、勞退的適用看「某一天」的居留身分（Q06），所以要能重建當時有效的是哪一筆。

### Compensation（約定薪資）[靜態替代]（歷史需求：需要重建當時，依 Q07、Q17）
狀態：Agreed（有效）
終態：（無；被新的約定取代屬 monthly-payroll）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Agreed | AgreeCompensation | 人資 | 掛在錄用上（到職前約定）或僱傭關係上 | |

說明：本切片只有到職時的一筆（02 D-01）；調薪後的版本由 monthly-payroll 定義狀態機。最低工資與投保薪資級距都要依到職日當時的約定判定，所以標「需要重建當時」。

### InsuranceEnrollment（投保）（歷史需求：需要重建當時，依 Q03、Q15）
狀態：Enrolled（已加保）→ Terminated（已退保）
終態：Terminated

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Enrolled | RecordInsuranceFiling | 人資 | 依實際向保險人辦理的結果登錄實際辦理日；保險人核定的生效日可以另外輸入 | |
| Enrolled | Terminated | （由 resignation 定義：退保） | 人資 | 不在本切片 | |

說明：Terminated 在本切片走不到，由 resignation 定義觸發事件；先列出，避免 resignation 另立一套狀態。到職前取消但已提早加保的處理待 [待專家確認: EQ-005]。

### InsuredSalary（投保薪資）（歷史需求：需要重建當時，依 Q13、Q17）
狀態：Effective（生效中）→ Superseded（被調整後的投保薪資取代）
終態：Superseded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Effective | DeclareInsuredSalary | 人資 | 屬於一筆 Enrolled 的投保；記錄依據的分級表版本 | |
| Effective | Superseded | （由 social-insurance 定義：調整投保薪資、保險人逕調） | 人資；保險人 | 不在本切片 | |

### WarningOverride（警告忽略紀錄）（歷史需求：需要軌跡，依 Q20）
狀態：Active（有效）→ Lapsed（失效：警告已不成立或內容已改變）／Withdrawn（已撤回）
終態：Lapsed、Withdrawn

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | OverrideWarning | 人資 | 有一個成立中的法規警告；理由可不填（PLAN.md D-27） | |
| Active | Lapsed | LapseWarningOverride | 系統 | 它針對的警告不再成立（資料已改正），或警告內容改變（被警告的值和 warned_value 不同、規則換了新版本） | |
| Active | Withdrawn | WithdrawWarningOverride | 人資 | — | |

說明：失效後如果警告仍成立（例：月薪改了但仍低於最低工資），會重新出現為「未處理的警告」，要再次忽略就是新的一筆（02 卡片：每次忽略是一筆）。

### PersonalDataArchival（個資封存）（歷史需求：需要軌跡，依 Q22）
狀態：Archived（封存中）→ Released（已解除）
終態：Released

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Archived | ArchivePersonalData | 人資 | 保存目的消失（例：到職前取消的人；離職後保存期間屆滿，屬 resignation）；寫明封存的個資類別 | |
| Archived | Released | ReleaseArchival | 人資 | 有需要再使用的理由（例：同一客戶內回任，Q11），可以只解除部分類別 | |

說明：依法刪除（不只是封存）的做法在第 ⑤ 步依平台 P7 設計（01_scope D-20），本切片不定義刪除的狀態。

### DataSubjectRequest（個資請求）（歷史需求：需要軌跡，依 Q22）
狀態：Received（已收到）→ Completed（已完成）／Rejected（已拒絕）
終態：Completed、Rejected

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Received | ReceiveDataSubjectRequest | 人資（代員工登錄） | 請求來自當事人本人 | |
| Received | Completed | ResolveDataSubjectRequest | 人資 | 已執行請求的內容（例：更正走 CorrectRecord、停止利用或刪除走 ArchivePersonalData）；部分接受也算完成，結果寫明 | |
| Received | Rejected | ResolveDataSubjectRequest | 人資 | 有法定的拒絕理由（例：依業務必要不刪除），寫明理由 | |

### 不需要狀態機的東西

| 對象 | 歷史需求 | 依據 | 說明 |
|---|---|---|---|
| Person 的國籍、戶籍或居住登記、已領取的老年給付 | 需要重建當時 | Q06 | 屬性本身帶取得日、喪失日、登記日、除籍日（02 卡片），判定時取「某一天」的值；改變靠登錄新的期間，不是狀態轉換 |
| Person 的姓名、性別、出生日期、教育程度、住址 | 需要軌跡 | Q10、Q15 | 勞工名卡項目；登錯要能更正並留紀錄 |
| Person 的聯絡方式 | 只需現況 | — | 只供聯絡（02 D-14），直接存目前值，不做事件（docs/01 ③「可以簡化的時候」） |
| Employer 的是否適用勞基法 | 需要重建當時 | Q05、Q13 | 屬性保留期間（02 卡片）；維護屬 org-setup |
| Tenant、Employer 其他屬性、InsuranceUnit、OrgUnit、WorkLocation | 只需現況（本切片） | — | 本切片以固定資料提供，建立與維護的狀態機由 org-setup 定義（01_scope 範圍外但會用到） |
| Jurisdiction、SocialInsuranceScheme | 只需現況 | Q02、Q05 | 全平台共用的參考資料；施行日是屬性（02 D-23） |

## 事件
<!-- 觸發來源：人的動作／其他單位個體的變化／外部系統或訊息／時間或條件到達
     層：要求／建議／決定／發生／執行（「建議」層不改變狀態）
     有意義的時間：發生／得知／生效 -->

| 事件 | 觸發來源 | 層 | 主體 | 改變什麼 | 證據 | 能否撤銷 | 有意義的時間 |
|---|---|---|---|---|---|---|---|
| DecideHire（決定錄用） | 人的動作（人資） | 決定 | Hire | （無）→ Hired；有到職前簽的契約、約定薪資時一起掛上 | 錄取通知或對方接受的紀錄 | 不撤銷；改用 CancelHire | 發生、得知 |
| RescheduleStart（到職前改期） | 人的動作（人資） | 決定 | Hire | Hired → Hired；約定到職日改變，原本的值保留 | 改期的理由 | 可以再改期 | 發生、生效 |
| CancelHire（到職前取消） | 人的動作（人資） | 決定 | Hire | Hired → Cancelled；掛在錄用上的契約 Signed → Voided | 取消原因 | 不可撤銷；再錄用是新的一筆錄用 | 發生、得知 |
| PromptStartConfirmation（提醒確認到職） | 時間或條件到達（約定到職日到了，錄用仍是 Hired） | 建議 | Hire | 不改變狀態 | 約定到職日 | 可作廢 | 得知 |
| StartEmployment（到職） | 人的動作（人資確認這個人已開始提供勞務） | 發生 | Hire | Hire Hired → Started；建立 Employment（Active）；契約 Signed → InForce；約定薪資接續掛到僱傭關係 | 實際開始工作的日期；之後 shift-attendance 的上班打卡可以當證據 | 不可撤銷，只能更正（見更正方式） | 發生、得知 |
| RegisterExistingEmployment（補登既有員工） | 人的動作（人資） | 發生 | Employment | （無）→ Active 或 Ended；同時登錄目前的投保、投保薪資、約定薪資等事實（02 D-12） | 既有的人事資料；當時依據說明（historical_basis_note） | 只能更正 | 發生、得知 |
| RecordEarlyDeparture（到職後立刻離開） | 人的動作（人資） | 發生 | Employment | Active → Ended；記結束日、原因；契約 InForce → Ended | 結束原因、登記者 | 只能更正 | 發生、得知 |
| SignContract（簽訂勞動契約） | 人的動作（人資） | 發生 | EmploymentContract | （無）→ Signed | 書面契約（移工必須書面） | 只能更正 | 發生、生效 |
| ContractTermStarts（契約起日到達） | 時間或條件到達 | 發生 | EmploymentContract | Signed → InForce | 契約起日 | — | 生效 |
| AgreeCompensation（約定薪資） | 人的動作（人資） | 決定 | Compensation | （無）→ Agreed | 錄取通知或契約上的薪資條件 | 只能更正；調薪屬 monthly-payroll | 發生、生效 |
| RecordWorkAuthorization（登錄工作許可） | 外部系統或訊息（主管機關核發的許可函，由人資登錄） | 發生 | WorkAuthorization | （無）→ Valid | 許可函文號；免申請者的身分證件 | 只能更正 | 生效、得知 |
| ExpireWorkAuthorization（工作許可到期） | 時間或條件到達 | 發生 | WorkAuthorization | Valid → Expired | 許可期限；免申請者依據的身分證件已被取代 | — | 生效 |
| RecordIdentityDocument（登錄身分證件） | 人的動作（人資依員工出示的證件） | 發生 | IdentityDocument | （無）→ Valid；換發或居留事由改變時，前一筆 Valid → Superseded | 證件影本或核對紀錄（不代管證件） | 只能更正 | 生效、得知 |
| ExpireIdentityDocument（證件到期） | 時間或條件到達 | 發生 | IdentityDocument | Valid → Expired | 有效期限 | — | 生效 |
| ProposeEnrollmentFiling（產生加保待辦） | 其他單位個體的變化（決定錄用、到職、改期、資料更正）；時間或條件到達（應辦理期限將到或已過） | 建議 | Employment | 不改變狀態；列出各保險是否適用、應辦理期限、法定生效日、預計的投保薪資級距，已過期限的標出晚幾天 | 判定用到的資料與規則版本 | 可作廢（資料改變時重新產生） | 得知 |
| RecordInsuranceFiling（登錄實際辦理加保） | 人的動作（人資在保險人辦完後登錄） | 執行 | InsuranceEnrollment | （無）→ Enrolled；記實際辦理日、是否自願、保險人核定的生效日 | 申報回執或保險人核定資料 | 只能更正 | 發生、生效、得知 |
| DeclareInsuredSalary（申報投保薪資） | 人的動作（人資） | 執行 | InsuredSalary | （無）→ Effective；記金額、級距、分級表版本、申報日、來源 | 申報資料 | 只能更正 | 發生、生效 |
| OverrideWarning（忽略警告） | 人的動作（人資） | 決定 | WarningOverride | （無）→ Active | 規則與版本、被警告的值、理由（可不填） | 可撤回（WithdrawWarningOverride） | 發生 |
| LapseWarningOverride（忽略失效） | 其他單位個體的變化（被警告的資料改正或改變）；時間或條件到達（規則新版本生效） | 發生 | WarningOverride | Active → Lapsed | 新的值或新的規則版本 | — | 發生 |
| WithdrawWarningOverride（撤回忽略） | 人的動作（人資） | 決定 | WarningOverride | Active → Withdrawn；記撤回者、撤回時間 | — | 不可撤銷；要再忽略就是新的一筆 | 發生 |
| ReceiveDataSubjectRequest（收到個資請求） | 人的動作（員工提出，人資登錄） | 要求 | DataSubjectRequest | （無）→ Received | 請求內容、收到日期 | 員工撤回時記為 Completed，結果寫「當事人撤回」（D-07） | 發生、得知 |
| ResolveDataSubjectRequest（處理個資請求） | 人的動作（人資） | 決定 | DataSubjectRequest | Received → Completed 或 Rejected | 處理結果與理由 | 不可撤銷 | 發生 |
| ProposeArchival（產生封存建議） | 時間或條件到達（到職前取消；保存目的消失） | 建議 | PersonalDataArchival | 不改變狀態；列出建議封存的人與個資類別 | 取消日、保存期間規則 | 可作廢 | 得知 |
| ArchivePersonalData（封存個資） | 人的動作（人資） | 決定 | PersonalDataArchival | （無）→ Archived | 封存的類別與理由 | 改用 ReleaseArchival | 發生、生效 |
| ReleaseArchival（解除封存） | 人的動作（人資） | 決定 | PersonalDataArchival | Archived → Released | 解除理由（例：回任） | 不可撤銷；要再封存是新的一筆 | 發生、生效 |
| CorrectRecord（更正資料） | 人的動作（人資） | 發生 | 任何登錄的事實（見更正方式） | 一般不改變狀態；更正誤登到職、誤登取消時改變錄用與僱傭關係的狀態（見狀態機）；原值保留，新值生效，依賴它的判定重新推導 | 更正理由；更正者、時間 | 可以再更正 | 發生、得知 |

四種觸發來源都有：人的動作（大部分）、其他單位個體的變化（ProposeEnrollmentFiling、LapseWarningOverride）、外部系統或訊息（RecordWorkAuthorization）、時間或條件到達（PromptStartConfirmation、ContractTermStarts、ExpireWorkAuthorization、ExpireIdentityDocument、ProposeArchival、ProposeEnrollmentFiling、LapseWarningOverride）。保險人核定的生效日目前由人資登錄（01_scope D-04，系統不連線勞保局），之後若串接保險人回覆，RecordInsuranceFiling 的觸發來源會改為外部系統或訊息。

## 決策流程
<!-- 訊號 → 證據 → 狀態 → 建議 → 決定；沒有需要判斷的地方寫「無」 -->

### 一、到職後要辦哪些加保
- 訊號：決定錄用、到職、到職前改期、到職資料更正；或應辦理期限將到、已過。
- 證據：人的國籍、戶籍、證件與居留事由、出生日期、已領的老年給付；雇主型態、登記日、是否適用勞基法；投保單位在當天的計入人數；到職日；約定薪資；當時有效的規則版本與分級表版本（沒有對應版本時標「無對應規則版本」，PLAN.md D-33）。
- 狀態：各保險為強制、可自願或不適用；應辦理期限、法定生效日；應申報的投保薪資級距；已登錄的實際辦理日與差距。
- 建議：ProposeEnrollmentFiling 產生加保待辦（哪幾種、哪天前辦、預計從哪天生效、報哪一級），可自願的列出讓雇主選擇。
- 決定：人資在保險人辦完後登錄（RecordInsuranceFiling、DeclareInsuredSalary）；可自願的由雇主決定加或不加。系統的待辦不會自己建立投保。

### 二、法規警告：改資料，還是照樣存檔
- 訊號：存檔錄用、到職、契約、約定薪資、工作許可、加保資料時，規則檢查不通過。
- 證據：被檢查的值、規則與版本（例：約定月薪 28,000 與到職日當時的每月最低工資）。
- 狀態：一個成立中的法規警告（推導值，不另存）。
- 建議：顯示警告與依據的規則。
- 決定：人資改正資料（CorrectRecord，警告消失），或照樣存檔（OverrideWarning，建立警告忽略紀錄）。資料本身矛盾的直接阻擋，不能忽略（01_scope D-17）；哪一條警告、哪一條阻擋，第 ④ 步逐條標出。

### 三、約定到職日到了，有沒有來
- 訊號：約定到職日到了，錄用仍是 Hired。
- 證據：約定到職日；之後可加上 shift-attendance 的上班打卡。
- 狀態：錄用尚未確認到職。
- 建議：PromptStartConfirmation 提醒人資確認。
- 決定：人資登錄到職（StartEmployment，可以補登實際開始的日期）、改期（RescheduleStart），或取消（CancelHire）。系統不因日期到了就自動視為到職，因為加保義務從實際開始提供勞務起算（01_scope D-07），自動到職會把沒來的人當成員工（D-01）。

### 四、要不要封存個資
- 訊號：到職前取消；（之後的切片）離職後保存期間屆滿。
- 證據：取消日或離職日、各類個資的保存規則（第 ④ 步）。
- 狀態：保存目的已消失的個資類別。
- 建議：ProposeArchival 列出建議封存的人與類別。
- 決定：人資封存（ArchivePersonalData），或註明理由暫不封存。

## 更正方式

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 |
|---|---|---|---|---|
| 錄用與到職資料（到職日、雇主、工作地點、組織單位、試用期、員工編號） | CorrectRecord | 人資或員工 | 不需核准，留紀錄（D-02） | 原值保留，記更正者、時間、理由；依更正後的資料重新判定各保險，更正前的判定仍查得到（Q15）；依賴它的警告忽略紀錄依條件失效（LapseWarningOverride） |
| 誤登到職（其實到職日當天沒來、從未提供勞務） | CorrectRecord（把 StartEmployment 標為錯誤登錄） | 人資 | 不需核准，留紀錄（D-02） | 原本的到職紀錄與僱傭關係保留並標為錯誤登錄（不是 Ended，也不是離職）；錄用改回 Cancelled 並記取消原因；這個人不算這個雇主的員工（01_scope D-12、Q14、Q18）（D-03） |
| 誤登取消（其實已經到職） | CorrectRecord（把 CancelHire 標為錯誤登錄） | 人資 | 不需核准，留紀錄（D-02） | 原本的取消紀錄保留並標為錯誤登錄，補登 StartEmployment（發生時間為實際到職日）（D-03） |
| 人的勞工名卡項目、身分證件、工作許可、契約、約定薪資 | CorrectRecord | 人資或員工（員工可經由個資請求，Q22） | 不需核准，留紀錄（D-02） | 原值保留；依賴它的判定與警告重新推導 |
| 實際辦理日、保險人核定的生效日 | CorrectRecord | 人資 | 不需核准，留紀錄（D-02） | 只更正系統內的登錄錯誤；向保險人申請更正加保日不在本切片（01_scope 不做） |
| 申報的投保薪資 | CorrectRecord | 人資 | 不需核准，留紀錄（D-02） | 同一生效日先誤報再更正，是對同一筆的更正，不是新的一筆（02 InsuredSalary 卡）；原值保留 |
| 結束日、結束原因（到職後立刻離開） | CorrectRecord | 人資 | 不需核准，留紀錄（D-02） | 原值保留；結束日不能早於到職日（資料矛盾，阻擋） |

沒有任何一種更正是直接覆蓋舊值：原值、更正者、更正時間、理由都保留，實際保存方式依平台 P2（第 ⑤ 步）。

## 詞彙對照表新增

| ID | 種類 | 定義 | zh-TW | 對照備註 |
|---|---|---|---|---|
| Hire.Hired | 狀態 | 已決定錄用，還沒開始提供勞務 | 已錄用 | |
| Hire.Started | 狀態 | 這個人已開始提供勞務，錄用轉成僱傭關係 | 已到職 | |
| Hire.Cancelled | 狀態 | 到職前取消 | 到職前取消 | |
| Employment.Active | 狀態 | 僱傭關係進行中 | 在職 | |
| Employment.Ended | 狀態 | 僱傭關係已結束 | 已結束 | |
| Employment.RecordedInError | 狀態 | 誤登的僱傭關係，這個人其實從未開始提供勞務；保留紀錄但不算數 | 錯誤登錄 | |
| EmploymentContract.Signed | 狀態 | 已簽訂，尚未生效 | 已簽訂 | |
| EmploymentContract.InForce | 狀態 | 契約生效中 | 生效中 | |
| EmploymentContract.Ended | 狀態 | 契約已結束 | 已結束 | |
| EmploymentContract.Voided | 狀態 | 隨錄用取消而失效 | 已失效 | |
| WorkAuthorization.Valid | 狀態 | 許可有效 | 有效 | |
| WorkAuthorization.Expired | 狀態 | 許可期限屆滿或依據的身分消失 | 已到期 | |
| IdentityDocument.Valid | 狀態 | 證件有效 | 有效 | |
| IdentityDocument.Expired | 狀態 | 證件有效期限屆滿 | 已到期 | |
| IdentityDocument.Superseded | 狀態 | 被換發、展延或居留事由改變的新一筆取代 | 已被取代 | |
| Compensation.Agreed | 狀態 | 約定有效 | 有效 | |
| InsuranceEnrollment.Enrolled | 狀態 | 已加保 | 已加保 | |
| InsuranceEnrollment.Terminated | 狀態 | 已退保（由 resignation 觸發） | 已退保 | |
| InsuredSalary.Effective | 狀態 | 投保薪資生效中 | 生效中 | |
| InsuredSalary.Superseded | 狀態 | 被調整後的投保薪資取代（由 social-insurance 觸發） | 已被取代 | |
| WarningOverride.Active | 狀態 | 忽略決定有效 | 有效 | |
| WarningOverride.Lapsed | 狀態 | 警告已不成立或內容已改變 | 失效 | |
| WarningOverride.Withdrawn | 狀態 | 忽略決定被撤回 | 已撤回 | |
| PersonalDataArchival.Archived | 狀態 | 封存中 | 封存中 | |
| PersonalDataArchival.Released | 狀態 | 已解除封存 | 已解除 | |
| DataSubjectRequest.Received | 狀態 | 已收到，處理中 | 已收到 | |
| DataSubjectRequest.Completed | 狀態 | 已處理完成（含部分接受） | 已完成 | |
| DataSubjectRequest.Rejected | 狀態 | 依法拒絕 | 已拒絕 | |
| DecideHire | 事件 | 雇主決定錄用某人並約定到職日 | 決定錄用 | |
| RescheduleStart | 事件 | 到職前改變約定到職日 | 到職前改期 | |
| CancelHire | 事件 | 到職前取消錄用 | 到職前取消 | |
| PromptStartConfirmation | 事件 | 約定到職日到了，提醒確認到職 | 提醒確認到職 | 建議層 |
| StartEmployment | 事件 | 這個人開始提供勞務，僱傭關係成立 | 到職 | |
| RegisterExistingEmployment | 事件 | 補登客戶開始使用系統前就到職的員工 | 補登既有員工 | |
| RecordEarlyDeparture | 事件 | 到職後立刻離開，記錄結束日與原因 | 到職後立刻離開 | |
| SignContract | 事件 | 簽訂勞動契約 | 簽訂勞動契約 | |
| ContractTermStarts | 事件 | 契約起日到達 | 契約起日到達 | |
| AgreeCompensation | 事件 | 約定薪資 | 約定薪資 | |
| RecordWorkAuthorization | 事件 | 登錄主管機關核發的工作許可或免申請的身分 | 登錄工作許可 | |
| ExpireWorkAuthorization | 事件 | 工作許可到期 | 工作許可到期 | |
| RecordIdentityDocument | 事件 | 登錄員工出示的身分證件 | 登錄身分證件 | |
| ExpireIdentityDocument | 事件 | 證件有效期限屆滿 | 證件到期 | |
| ProposeEnrollmentFiling | 事件 | 依判定產生加保待辦 | 產生加保待辦 | 建議層 |
| RecordInsuranceFiling | 事件 | 登錄實際向保險人辦理加保的結果 | 登錄實際辦理加保 | |
| DeclareInsuredSalary | 事件 | 申報投保薪資 | 申報投保薪資 | |
| OverrideWarning | 事件 | 看到法規警告後照樣存檔 | 忽略警告 | |
| LapseWarningOverride | 事件 | 警告不再成立或內容改變，忽略失效 | 忽略失效 | |
| WithdrawWarningOverride | 事件 | 撤回忽略的決定 | 撤回忽略 | |
| ReceiveDataSubjectRequest | 事件 | 收到當事人的個資請求 | 收到個資請求 | |
| ResolveDataSubjectRequest | 事件 | 完成或拒絕個資請求 | 處理個資請求 | |
| ProposeArchival | 事件 | 依保存目的產生封存建議 | 產生封存建議 | 建議層 |
| ArchivePersonalData | 事件 | 封存某人的部分個資 | 封存個資 | |
| ReleaseArchival | 事件 | 解除封存 | 解除封存 | |
| CorrectRecord | 事件 | 更正登錄錯誤的資料，原值保留 | 更正資料 | |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 |
|---|---|---|---|---|
| D-01 | 到職（StartEmployment）由人資確認，系統在約定到職日提醒（PromptStartConfirmation），不因日期到了就自動視為到職 | 約定到職日一到自動到職，沒來再取消 | 僱傭關係以開始提供勞務為成立時點（01_scope D-07）；自動到職會把當天沒來的人當成員工，之後只能「更正」，和「到職前取消」混在一起（Q14、Q18） | 01_scope D-07、D-12 |
| D-02 | 更正（CorrectRecord）不需要另一個人核准，但一律保留原值、更正者、時間、理由 | 更正要主管核准 | 中小企業常只有一位人資或老闆本人（PLAN.md P-05）；Q15 只要求查得到更正前後與誰改的。**請使用者決定**：是否有哪些更正（例：到職日、實際辦理日）要另一人核准 | Q15；PLAN.md P-05 |
| D-03 | 「誤登到職」與「誤登取消」用更正處理，原紀錄標為錯誤登錄、不刪除，不用 RecordEarlyDeparture 或 CancelHire 代替 | 誤登到職改用到職後立刻離開；誤登取消就重新錄用 | 前者會讓從沒上班的人變成「曾是員工」，影響人數門檻與年資（Q12、Q18）；後者會產生第二筆錄用，看不出原本的安排（Q14） | 01_scope D-12；Q14、Q18 |
| D-04 | 判定各保險的適用、期限、級距，不是事件也不是狀態，是推導值（02 D-04）；系統只產生建議層的加保待辦（ProposeEnrollmentFiling），投保由人資登錄實際辦理結果才建立 | 判定結果自動建立一筆「應加保」的投保 | 投保是實際辦理後的事實（02 InsuranceEnrollment 卡）；建議不改變狀態（docs/01 原則 3） | 02 D-04；docs/01 ③ |
| D-05 | 加保流程的五層：決定（DecideHire）→ 發生（StartEmployment）→ 建議（ProposeEnrollmentFiling）→ 執行（RecordInsuranceFiling、DeclareInsuredSalary）；沒有「要求」層（招募、應徵不在範圍） | 把錄用與到職併成一層 | 會停在中間：錄用後可以改期、取消（停在決定）；到職後可能晚辦或沒辦加保（停在發生），所以分開記（docs/01 ③ 判斷法） | Q02、Q03、Q14 |
| D-06 | 投保的 Terminated、投保薪資的 Superseded、契約到期在本切片走不到，狀態先列出，觸發事件由 resignation、social-insurance 定義 | 不列這些狀態，由後續切片新增 | 後續切片引用同一份狀態機，避免各自定義一套（共用核心只有一份） | docs/01 0.3 |
| D-07 | 員工撤回個資請求：記為 Completed，結果寫「當事人撤回」 | 新增 Withdrawn 狀態 | 本切片的驗收問題（Q22）只問處理紀錄；撤回很少見，用結果欄記錄即可，第 ④ 步若要算法定處理期限再看是否要拆 | Q22 |
| D-08 | 工作許可、身分證件的「到期」由時間觸發，但到期日之前登錄展延或新證件時，舊的一筆改為 Superseded（證件）或保留文號歷史（許可，02 卡片） | 到期一律由人登錄 | 期限是已登錄的事實，到了就成立；展延換發的處理不在本切片（01_scope 不做） | 02 D-05、WorkAuthorization 卡 |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每個會變狀態的 Entity 都有狀態圖，沒有走不到的狀態 | | |
| 「核准」和「發生」是分開的兩件事 | | |
| 會隨時間推進的動詞（流程）都有狀態機，不只名詞 | | |
| 新增的事件與狀態名稱已登錄在詞彙對照表 | | |
| 需要判斷的地方有寫出決策流程（訊號 → 證據 → 狀態 → 建議 → 決定）；系統或 AI 的建議不會直接改變狀態 | | |
| 每個事件標了觸發來源；由人觸發的，標了誰有權觸發 | | |
| 每個會變狀態的東西都標了歷史需求，並註明依據哪條驗收問題 | | |
| 有寫更正方式，且沒有任何一步是直接改舊紀錄 | | |
| 第 ① 步每個草稿 User Story，都至少被一個正式 Use Case 涵蓋 | | |
| 每個正式 Use Case 都註明了用到的 Entity、事件 | | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
