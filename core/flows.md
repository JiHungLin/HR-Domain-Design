# 共用核心：狀態機、事件、更正方式

<!-- 各切片 ③ 的狀態機、事件、更正方式，格式同 03_flows.md
     每個項目標題列帶狀態標記：[候選]／[已驗證]／[已驗證（暫代）]；並寫「出處：<切片>（<步驟> @ <tag>）」「層：core／shared／domain」「被引用：」 -->

## 狀態機（hire-employee）
<!-- 歷史需求：只需現況／需要軌跡／需要重建當時（依 Qnn）。「規則」欄第 ④ 步回填 -->

**狀態怎麼來**：每個狀態都由事件序列解釋（平台 P1）。
- 由日期觸發的轉換（到期、契約起日到達、隨其他事件連動的失效）是依登錄的日期與其他事件**推導**出來的；它依據的日期或事件被更正、註銷時，重新推導，不照原紀錄重播（D-03、D-12）。
- 發現某個改變狀態的事件根本是誤登（例：其實沒來卻登錄到職），用 AnnulEntry（註銷誤登）標記那個事件：被註銷的事件視為沒有發生，狀態依其餘事件重新推導；這不是狀態機上的轉換，所以不會從終態轉出。註銷錯了用 RevokeAnnulment（撤銷註銷）恢復原事件，原本的那一段與掛在上面的紀錄跟著恢復，身分不變（D-03）。
- 只是值打錯（例：到職日打錯）用 CorrectRecord：不直接改變狀態，但依那個值推導的狀態跟著重算（例：證件期限打錯而被判到期，更正期限後回到有效）。
- 更正與註銷都不需要第二個人核准，但一律留下誰、何時、為什麼與證據；會改變人數門檻、保險適用、晚辦天數、工作許可是否發給這個雇主的，以及所有註銷，列為「重大更正」並通知雇主（老闆）（D-02）。

### Hire（錄用） [候選]（歷史需求：需要軌跡，依 hire-employee:Q14）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Hired（已錄用）→ Started（已到職）／Cancelled（到職前取消）
終態：Started、Cancelled

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Hired | DecideHire | 人資 | 人已登錄（新的人或同客戶內既有的人，hire-employee:Q11）；有雇主與約定到職日 | R11、R14 |
| Hired | Hired | RescheduleStart | 人資 | 新的到職日和原本不同；原本的到職日保留（hire-employee:Q14） | R01、R11、R13、R14 |
| Hired | Started | StartEmployment | 人資 | 這個人已經實際開始提供勞務（01_scope D-07）；到職日不早於決定錄用日 | R01、R11、R14、R15、R16、R21 |
| Hired | Cancelled | CancelHire | 人資 | 還沒開始提供勞務；到職日當天沒來也屬這一種（01_scope D-12） | — |

註銷誤登：註銷 CancelHire（其實已經到職）→ 錄用回到 Hired，再登錄 StartEmployment（發生時間為實際到職日）；註銷 StartEmployment（其實從未上班）→ 錄用回到 Hired，再登錄 CancelHire。原本的事件都保留並標為已註銷。

### Employment（僱傭關係） [候選]（歷史需求：需要重建當時，依 hire-employee:Q13、hire-employee:Q15、hire-employee:Q18）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Active（在職）→ Ended（已結束）
終態：Ended

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | StartEmployment | 人資 | 來自一筆 Hired 的錄用 | R04、R05、R06 |
| （無） | Active | RegisterExistingEmployment | 人資 | 到職日早於這個雇主開始由系統管理的日子（D-09）；沒有錄用紀錄（02 D-12） | R02、R04、R05、R06、R08 |
| （無） | Ended | RegisterExistingEmployment | 人資 | 補登已結束的先前一段（例：回任時要找得到，hire-employee:Q11）；到職日與結束日都早於這個雇主開始由系統管理的日子（D-09） | R02、R04、R06、R08 |
| Active | Ended | RecordEarlyDeparture | 人資 | 結束日不早於到職日；本切片只處理到職後立刻離開（01_scope D-12），一般離職由 resignation 定義觸發事件 | R02 |

註銷誤登：註銷建立這段僱傭關係的 StartEmployment 或 RegisterExistingEmployment → 這段僱傭關係視為不存在：不計入人數門檻、年資、勞工名卡（hire-employee:Q12、hire-employee:Q18），紀錄保留並標為已註銷；掛在它上面的契約、投保見下方各狀態機。前提是它後面沒有還沒註銷、又依賴它的事件（例：之後的到職後立刻離開），有的話依相反順序一起註銷（D-03）。同一人在同一雇主不能同時有兩段在職的僱傭關係（第 ④ 步規則，資料矛盾，阻擋）。

說明：需要重建當時，是因為到職日、雇主、工作地點等被更正後，要依更正後的資料重新判定各保險，也要看得出更正前、當時系統知道的判定（hire-employee:Q15），以及當時依哪一版規則（hire-employee:Q13）。所以所有登錄事實的事件都記「得知」時間（D-10）。

### EmploymentContract（勞動契約） [候選]（歷史需求：需要軌跡，依 hire-employee:Q15、hire-employee:Q19）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Signed（已簽訂，尚未生效）→ InForce（生效中）→ Ended（已結束）；Signed → Voided（從未生效即失效）
終態：Ended、Voided

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Signed | SignContract | 人資 | 掛在錄用上（到職前簽，02 D-18）或僱傭關係上 | R03、R18、R19、R20、R59 |
| Signed | InForce | StartEmployment | 系統（隨到職） | 契約起日不晚於到職日；生效時間取契約起日與到職日較晚者 | — |
| Signed | InForce | ContractTermStarts | 系統 | 僱傭關係仍為 Active，且契約起日到達（起日晚於到職日、或續約的新契約） | — |
| Signed | Voided | VoidContract | 系統（隨錄用取消或僱傭關係結束） | 契約掛在被取消的錄用上；或契約起日還沒到，僱傭關係就結束 | — |
| InForce | Ended | RecordEarlyDeparture | 系統（隨僱傭關係結束） | — | — |

註銷誤登：註銷造成 Voided 或 Ended 的事件（例：誤登取消），契約依其餘事件回到 Signed 或 InForce。定期契約到期、續約、視為不定期契約都不在本切片（01_scope 不做），到期的轉換由 resignation 定義。

### WorkAuthorization（工作許可） [候選]（歷史需求：需要重建當時，依 hire-employee:Q16）
- 出處：hire-employee（③ @ hire-employee/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Valid（有效）↔ Expired（已失效）
終態：（無；展延晚登錄時可以回到有效）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordWorkAuthorization | 人資 | 依主管機關核發的許可函登錄；免申請者依身分證件登錄（02 D-06） | R03、R16、R17、R58 |
| Valid | Valid | RecordWorkAuthorization | 人資 | 許可還有效時登錄展延：新增一筆核准紀錄，不改前一筆（02 D-33） | R03、R17、R58 |
| Valid | Expired | ExpireWorkAuthorization | 系統 | 申請許可者：最後一筆核准的迄日屆滿，且沒有已登錄的展延。免申請者沒有到期，身分消失由 EndWorkAuthorization 記錄 | — |
| Valid | Expired | EndWorkAuthorization | 人資 | 免申請者依據的身分已消失，經人資確認（D-08）；許可被廢止的登錄不在本切片 | — |
| Expired | Valid | RecordWorkAuthorization | 人資 | 登錄期限屆滿前已核准、但較晚才登錄的展延；仍是同一筆許可，新增一筆核准紀錄（02 D-33），生效時間為原期限的次日 | R03、R17、R58 |

說明：要重建「到職日那天許可是否有效、發給哪個雇主」（hire-employee:Q16）；展延晚登錄後，到期與恢復兩筆轉換都保留，依發生與得知時間分得出「當時系統以為已失效」和「實際一直有效」（D-10）。申請、廢止、轉換雇主不在本切片（01_scope 不做）。

### IdentityDocument（身分證件） [候選]（歷史需求：需要重建當時，依 hire-employee:Q06、hire-employee:Q10）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Valid（有效）→ Expired（已到期）／Superseded（被新的一筆取代）
終態：Expired、Superseded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordIdentityDocument | 人資 | 依員工出示的證件登錄（不代管證件，01_scope D-20） | R03 |
| Valid | Superseded | RecordIdentityDocument | 人資 | 換發、展延，或居留事由改變而另記一筆（02 D-05）；生效時間為新證件的生效日 | R03 |
| Valid | Expired | ExpireIdentityDocument | 系統 | 有效期限屆滿 | — |

說明：健保、就保、勞退的適用看「某一天」的居留身分（hire-employee:Q06）。居留證展延是新的一份（02 IdentityDocument 卡），所以晚登錄的展延是新的一筆 Valid，前一筆維持 Expired，期間依生效日接續。

### Compensation（約定薪資）[靜態替代] [候選]（歷史需求：需要重建當時，依 hire-employee:Q07、hire-employee:Q17）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Agreed（有效）
終態：（無；被新的約定取代屬 monthly-payroll）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Agreed | AgreeCompensation | 人資 | 掛在錄用上（到職前約定）或僱傭關係上 | R11 |

說明：本切片只有到職時的一筆（02 D-01）；調薪後的版本由 monthly-payroll 定義狀態機。最低工資與投保薪資級距都要依到職日當時的約定判定，所以標「需要重建當時」。

### InsuranceEnrollment（投保） [候選]（歷史需求：需要重建當時，依 hire-employee:Q03、hire-employee:Q15）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Enrolled（已加保）→ Terminated（已退保）
終態：Terminated

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Enrolled | RecordInsuranceFiling | 人資 | 依實際向保險人辦理的結果登錄實際辦理日；保險人核定的生效日可以另外輸入；附申報回執，沒有時標示「無回執」（D-02） | R07、R31、R32、R50、R61 |
| Enrolled | Terminated | （由 resignation 定義：退保） | 人資 | 不在本切片 | — |

說明：
- Terminated 在本切片走不到，由 resignation 定義觸發事件；先列出，避免 resignation 另立一套（D-06）。
- 掛在一段被註銷的僱傭關係上的投保，在保險人那邊仍是真的加保，系統不會自動改變它的狀態；系統產生建議（ProposeEnrollmentFiling）提醒人資向保險人處理，處理方式待 [待專家確認: EQ-017]。投保本身登錯（登在錯的人或錯的制度）用 AnnulEntry 註銷 RecordInsuranceFiling。
- 到職前就先加保：目前投保一定掛在僱傭關係上（02 forEmployment 為 1），到職前記不下來。若 EQ-005 的答覆是「實務上會提早加保」，要回到第 ② 步把投保改為可以掛在錄用上（第 0 級回頭修改）（X-11）。
- 自願或強制：`voluntary` 記的是辦理當時是否以自願身分加保（事實）。之後人數跨過門檻，「現在應為強制」是推導值，由 ProposeEnrollmentFiling 提醒，不改寫當時的紀錄（X-12）。

### InsuredSalary（投保薪資） [候選]（歷史需求：需要重建當時，依 hire-employee:Q13、hire-employee:Q17）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Effective（生效中）→ Superseded（被調整後的投保薪資取代）
終態：Superseded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Effective | DeclareInsuredSalary | 人資 | 屬於一筆 Enrolled 的投保；記錄依據的分級表版本 | R40、R41、R42、R43、R45 |
| Effective | Superseded | （由 social-insurance 定義：調整投保薪資、保險人逕調） | 人資；保險人 | 不在本切片 | — |

### WarningOverride（警告忽略紀錄） [候選]（歷史需求：需要軌跡，依 hire-employee:Q20）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：core
- 被引用：（無）

狀態：Active（有效）→ Lapsed（失效：警告已不成立或內容已改變）／Withdrawn（已撤回）
終態：Lapsed、Withdrawn

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | OverrideWarning | 人資 | 有一個成立中的法規警告；理由可不填（PLAN.md D-27） | R09、R10 |
| Active | Lapsed | LapseWarningOverride | 系統 | 它針對的警告不再成立（資料已改正），或警告內容改變：被警告的值和 warned_value 不同，或**適用於被警告事實的**規則版本或修訂不同（例：實際到職日落在新版最低工資的期間、規則有新的修訂）。對已判定的事實，之後才生效的新版本不影響（D-11） | R51 |
| Active | Withdrawn | WithdrawWarningOverride | 人資 | — | — |

說明：
- 失效後如果警告仍成立（例：月薪改了但仍低於最低工資），會重新列為「未處理的警告」，要再次忽略就是新的一筆。
- 錄用時忽略的警告（針對錄用）：到職時重新評估。被警告的值與適用的規則版本都沒變（例：約定薪資接續掛到僱傭關係、到職日仍在同一版的期間），StartEmployment 為這筆紀錄加上針對僱傭關係的連結，原本針對錄用的連結不改；有變就失效。「目前有哪些員工帶著未處理的警告」看的是僱傭關係，還沒到職的看錄用（hire-employee:Q20）（X-08、X-20）。
- 規則版本不在原處修改：版本內容要更正時，是一個新的修訂，有自己的得知時間；忽略紀錄記住當時依據的版本與修訂（第 ④ 步、平台 P5）。

### PersonalDataArchival（個資封存） [候選]（歷史需求：需要軌跡，依 hire-employee:Q22）
- 出處：hire-employee（③ @ hire-employee/03-v1）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：core
- 被引用：（無）

狀態：Archived（封存中）→ Released（已解除）
終態：Released

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Archived | ArchivePersonalData | 人資 | 保存目的消失（例：到職前取消的人；離職後保存期間屆滿，屬 resignation）；寫明封存的個資類別 | R56 |
| Archived | Released | ReleaseArchival | 人資 | 連到一筆需要這些個資的紀錄：新的錄用（回任，hire-employee:Q11）、個資請求，或註銷誤登的取消；可以只解除部分類別 | R57 |

說明：依法刪除（不只是封存）的做法在第 ⑤ 步依平台 P7 設計（01_scope D-20），本切片不定義刪除的狀態。誰可以查看哪些個資（hire-employee:Q22 前半）是權限設定，不是流程，在第 ④ 步寫規則、第 ⑤ 步依 P7 落實。

### DataSubjectRequest（個資請求） [候選]（歷史需求：需要軌跡，依 hire-employee:Q22）
- 出處：hire-employee（③ @ hire-employee/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：core
- 被引用：（無）

狀態：Received（已收到）→ Completed（已完成）／Rejected（已拒絕）
終態：Completed、Rejected

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Received | ReceiveDataSubjectRequest | 員工（自己提出）；人資（代登錄書面、email、口頭的請求，記收到管道） | 請求來自當事人本人 | — |
| Received | Completed | ResolveDataSubjectRequest | 人資 | 已執行請求的內容（例：更正走 CorrectRecord、停止利用或刪除走 ArchivePersonalData）；部分接受也算完成，結果寫明；員工撤回也記為完成，結果寫「當事人撤回」（D-07）；部分拒絕的部分要寫依據；刪除的內容不能包含保存期間內的資料類別 | R53、R55、R62 |
| Received | Rejected | ResolveDataSubjectRequest | 人資 | 有法定的拒絕理由（例：依業務必要不刪除），寫明理由與依據（refusal_basis，被 R55 擋下的刪除自動帶入）；拒絕會通知雇主（老闆）（D-02） | R46、R62 |

處理期限的延長（ExtendDataSubjectRequest）不改變狀態，仍是 Received：寫明原因與延長後的期限，並以書面通知當事人；在原期限內決定（推定，原文未寫）（R53、R63，D-15）。

## 事件（hire-employee）

| 事件 | 觸發來源 | 層 | 主體 | 改變什麼 | 證據 | 能否撤銷 | 有意義的時間 | 狀態 | 出處 | 被引用 |
|---|---|---|---|---|---|---|---|---|---|---|
| DecideHire（決定錄用） | 人的動作（人資） | 決定 | Hire | （無）→ Hired；有到職前簽的契約、約定薪資時一起掛上 | 錄取通知或對方接受的紀錄 | 不撤銷；改用 CancelHire | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RescheduleStart（到職前改期） | 人的動作（人資） | 決定 | Hire | Hired → Hired；約定到職日改變，原本的值保留 | 改期的理由 | 可以再改期 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| CancelHire（到職前取消） | 人的動作（人資） | 決定 | Hire | Hired → Cancelled；掛在錄用上的契約隨之失效（VoidContract） | 取消原因 | 不可撤銷；再錄用是新的一筆錄用；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| PromptStartConfirmation（提醒確認到職） | 時間或條件到達（約定到職日到了，錄用仍是 Hired） | 建議 | Hire | 不改變狀態 | 約定到職日 | 可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| StartEmployment（到職） | 人的動作（人資確認這個人已開始提供勞務） | 發生 | Hire | Hire Hired → Started；建立 Employment（Active）；契約 Signed → InForce；約定薪資、針對錄用的有效警告忽略接續到僱傭關係 | 實際開始工作的日期；之後 shift-attendance 的上班打卡可以當證據 | 不可撤銷，只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RegisterExistingEmployment（補登既有員工） | 人的動作（人資） | 發生 | Employment | （無）→ Active 或 Ended；同時登錄目前的投保、投保薪資、約定薪資等事實（02 D-12）；標為補登資料 | 既有的人事資料；當時依據說明（historical_basis_note） | 只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordEarlyDeparture（到職後立刻離開） | 人的動作（人資） | 發生 | Employment | Active → Ended；記結束日、原因；契約 InForce → Ended，尚未生效的契約隨之失效（VoidContract） | 結束原因、登記者 | 只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| SignContract（簽訂勞動契約） | 人的動作（人資） | 發生 | EmploymentContract | （無）→ Signed | 書面契約（移工必須書面） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ContractTermStarts（契約起日到達） | 時間或條件到達 | 發生 | EmploymentContract | Signed → InForce | 契約起日 | 起日更正或依據的到職被註銷時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| VoidContract（契約失效） | 其他單位個體的變化（錄用取消；起日前僱傭關係結束） | 發生 | EmploymentContract | Signed → Voided | 取消或結束的紀錄 | 造成它的事件被註銷時，依其餘事件重新推導 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| AgreeCompensation（約定薪資） | 人的動作（人資） | 決定 | Compensation | （無）→ Agreed | 錄取通知或契約上的薪資條件 | 只能更正；調薪屬 monthly-payroll | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordWorkAuthorization（登錄工作許可） | 外部系統或訊息（主管機關核發的許可函或展延核准，由人資登錄） | 發生 | WorkAuthorization | （無）→ Valid；展延時新增一筆核准紀錄：還有效時 Valid → Valid，晚登錄時 Expired → Valid | 許可函文號；免申請者的身分證件 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ExpireWorkAuthorization（工作許可到期） | 時間或條件到達 | 發生 | WorkAuthorization | Valid → Expired（只用於申請許可者） | 最後一筆核准的迄日 | 展延晚登錄時回到 Valid；期限更正時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ProposeAuthorizationReview（提醒確認許可） | 其他單位個體的變化（免申請者依據的身分證件被取代或到期） | 建議 | WorkAuthorization | 不改變狀態；提醒人資確認許可是否仍有效 | 新的身分證件與居留事由 | 可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| EndWorkAuthorization（登錄許可失效） | 人的動作（人資） | 發生 | WorkAuthorization | Valid → Expired | 人資確認依據的身分已消失 [待專家確認: EQ-018] | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordIdentityDocument（登錄身分證件） | 人的動作（人資依員工出示的證件） | 發生 | IdentityDocument | （無）→ Valid；換發或居留事由改變時，前一筆 Valid → Superseded | 證件核對紀錄（不代管證件） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordPersonPeriod（登錄人的身分期間） | 人的動作（人資，依員工出示的戶籍、國籍或給付證明） | 發生 | Person | 不改變狀態；新增一段國籍（取得或喪失）、戶籍或居住登記（設籍或除籍）、已領取的老年給付；是真的改變，不是更正（登錯用 CorrectRecord）（D-18） | 戶籍謄本、國籍證明或給付核定的核對紀錄（不代管文件） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v3） |  |
| ExpireIdentityDocument（證件到期） | 時間或條件到達 | 發生 | IdentityDocument | Valid → Expired | 有效期限 | 期限更正時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ProposeEnrollmentFiling（產生加保待辦） | 其他單位個體的變化（決定錄用、到職、改期、資料更正、註銷誤登；登錄新的身分證件（例：拿到居留證、取得永久居留）；登錄人的身分期間（RecordPersonPeriod：國籍、戶籍新增一段期間、領取老年給付）；雇主的判定條件改變：新增登記紀錄、取得核定課稅或購票證、免辦登記或行業類別改變、改為適用勞基法（維護屬 org-setup）；同一投保單位其他員工的到職或離開改變了人數）；人資記錄待人判斷的決定（記錄後依決定重新判定，D-20）；時間或條件到達（應辦理期限將到或已過；條件日期到了：員工滿 65 歲、新制度的施行日、身分證件的生效日（登錄時還沒生效的證件））（D-16、D-17） | 建議 | Hire 或 Employment | 不改變狀態；列出各保險是否適用、應辦理期限、法定生效日、預計的投保薪資級距；已過期限的標出晚幾天（逾期，不能忽略，辦理後結案）；錄用時（還沒到職）以約定到職日為預計到職日與判定日，結果標「預估」，到職時以實際到職日重新判定並取代（D-19）；需要人判斷的列出讓人資決定：受僱兩個雇主時就保擇一參加，就保標「待人判斷」；「其他」類固定給付算不算入投保薪資，各保險的適用照常判定，受影響的投保薪資級距待人判斷，列出待決定的給付項目（D-20）；系統只看得到系統內的僱傭關係，員工在系統外另有雇主時，人資可以主動記錄擇一參加的決定（D-20）；既有員工的適用改變（例：人數跨過門檻，原本自願的變成強制）一併列出；掛在已註銷僱傭關係上的投保提醒向保險人處理 | 判定用到的資料版本與規則版本 | 不由人作廢：只會被新的判定取代（記取代它的那一筆），或因辦理完成而結案；可自願的保險由雇主選擇不加時，記在這筆待辦上（人、時間）；待人判斷的事項由人資決定後，也記在這筆待辦上（決定、人、時間），新的判定沿用之前的決定（D-19）；記錄決定後立刻依決定重新判定，產生新的待辦取代這一筆（D-20）；所有待辦都保留，記錄依據的資料與規則版本（D-10、X-22） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v5） |  |
| RecordInsuranceFiling（登錄實際辦理加保） | 人的動作（人資在保險人辦完後登錄） | 執行 | InsuranceEnrollment | （無）→ Enrolled；記實際辦理日、是否自願、保險人核定的生效日 | 申報回執或保險人核定資料；沒有時標示「無回執」 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| DeclareInsuredSalary（申報投保薪資） | 人的動作（人資） | 執行 | InsuredSalary | （無）→ Effective；記金額、級距、分級表版本、申報日、來源 | 申報資料 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| OverrideWarning（忽略警告） | 人的動作（人資） | 決定 | WarningOverride | （無）→ Active | 規則與版本、被警告的值、理由（可不填） | 可撤回（WithdrawWarningOverride） | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| LapseWarningOverride（忽略失效） | 其他單位個體的變化（被警告的資料改正或改變；到職時適用的規則版本或修訂和錄用時不同） | 發生 | WarningOverride | Active → Lapsed | 新的值或更正後的規則版本 | — | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| WithdrawWarningOverride（撤回忽略） | 人的動作（人資） | 決定 | WarningOverride | Active → Withdrawn；記撤回者、撤回時間 | — | 不可撤銷；要再忽略就是新的一筆 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ReceiveDataSubjectRequest（收到個資請求） | 人的動作（員工提出；或人資代登錄） | 要求 | DataSubjectRequest | （無）→ Received | 請求內容、收到日期、收到管道 | 員工撤回時記為 Completed（D-07） | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| PromptDataSubjectRequestDeadline（提醒個資請求期限） | 時間或條件到達（法定處理期限將到或已過；延長過的依延長後的期限） | 建議 | DataSubjectRequest | 不改變狀態 | 收到日期、法定期限（第 ④ 步規則） | 可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ExtendDataSubjectRequest（延長個資請求處理期限） | 人的動作（人資） | 決定 | DataSubjectRequest | 不改變狀態（仍是 Received）；新增一筆延長紀錄：延長後的期限、延長原因、書面通知當事人的日期；可以延長多次（D-15） | 寄給當事人的書面通知 | 只能更正 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ResolveDataSubjectRequest（處理個資請求） | 人的動作（人資） | 決定 | DataSubjectRequest | Received → Completed 或 Rejected | 處理結果與理由；拒絕時的依據（被保存期間規則擋下時自動帶入） | 不可撤銷 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ProposeArchival（產生封存建議） | 其他單位個體的變化（到職前取消）；時間或條件到達（保存期間屆滿，屬 resignation） | 建議 | PersonalDataArchival | 不改變狀態；列出建議封存的人與個資類別；人資的處置（封存或暫不封存及理由）記在這筆建議上 | 取消日、保存期間規則 | 可作廢（保留紀錄與處置） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ArchivePersonalData（封存個資） | 人的動作（人資） | 決定 | PersonalDataArchival | （無）→ Archived | 封存的類別與理由 | 改用 ReleaseArchival | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ReleaseArchival（解除封存） | 人的動作（人資） | 決定 | PersonalDataArchival | Archived → Released | 連到的錄用、個資請求或註銷紀錄；解除理由 | 不可撤銷；要再封存是新的一筆 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| CorrectRecord（更正資料） | 人的動作（人資） | 發生 | 任何登錄的事實（見更正方式） | 不直接改變狀態；原值保留，新值生效，依賴它的判定與依日期推導的狀態重新推導；重大更正另產生 NotifySignificantCorrection | 更正理由與證據；更正者、時間（D-02） | 可以再更正 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| AnnulEntry（註銷誤登） | 人的動作（人資） | 發生 | 可註銷的事件（見 D-14 白名單） | 被註銷的事件視為沒發生，相關的狀態依其餘事件重新推導；原事件保留並標為已註銷；註銷前依當時資料產生的判定，依得知時間仍查得到；一律產生 NotifySignificantCorrection | 理由與證據（例：打卡、出勤、保險人回執） | 用 RevokeAnnulment 撤銷 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RevokeAnnulment（撤銷註銷） | 人的動作（人資） | 發生 | 一筆 AnnulEntry | 原事件恢復，它建立的那一段與掛在上面的紀錄跟著恢復，身分不變；狀態重新推導；產生 NotifySignificantCorrection | 理由 | 不可撤銷；要再註銷是新的一筆 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| NotifySignificantCorrection（通知重大更正） | 其他單位個體的變化（重大更正、註銷、撤銷註銷、拒絕個資請求） | 建議 | 被更正或註銷的事實 | 不改變狀態；列出改了什麼、誰改的、理由與證據、受影響的員工與改變的判定，通知雇主（老闆），並列入重大更正清單 | 更正或註銷的紀錄、更正前後的判定 | 不可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |

## 更正方式（hire-employee）

更正與註銷都不需要第二個人核准，能追溯就好（D-02）：一律記錄誰、何時、理由與證據。是不是「重大更正」看**效果**，不看是哪個欄位：會改變任何投保單位的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主的，以及所有註銷與撤銷註銷，系統通知雇主（老闆）並列入重大更正清單（NotifySignificantCorrection）。

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 | 狀態 | 出處 |
|---|---|---|---|---|---|---|
| 錄用與到職資料的值（到職日、工作地點、組織單位、試用期、員工編號） | CorrectRecord | 人資或員工 | 不需核准，留紀錄；到職日的更正一律算重大更正 | 原值保留，記更正者、時間、理由；依更正後的資料重新判定各保險，更正前、當時系統知道的判定仍查得到（Q15）；依賴它的警告忽略紀錄依條件失效 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 雇主 | 不能用 CorrectRecord；AnnulEntry 註銷原本的到職（或補登），再對正確的雇主登錄 | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 換雇主就是另一段僱傭關係（02 D-03）；原紀錄保留並標為已註銷 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 僱傭關係或錄用登錯人（例：重複建了一個人） | CorrectRecord（改指到正確的人） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原本指向的人保留紀錄；兩筆人確認是同一人時的合併做法，第 ⑤ 步設計 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登到職（其實從未提供勞務） | AnnulEntry（註銷 StartEmployment），再登錄 CancelHire | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原到職事件保留並標為已註銷；這段僱傭關係視為不存在，不計入人數、年資、勞工名卡（01_scope D-12、Q14、Q18）；已加保的提醒向保險人處理（EQ-017）；後面依賴它的事件（例：到職後立刻離開）一起註銷 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登取消（其實已經到職） | AnnulEntry（註銷 CancelHire），再登錄 StartEmployment | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原取消事件保留並標為已註銷；錄用回到 Hired、契約依其餘事件重新推導，再到職；已封存的個資由人資解除（ReleaseArchival 連到這筆註銷） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登到職後立刻離開（其實仍在職） | AnnulEntry（註銷 RecordEarlyDeparture） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件保留並標為已註銷；僱傭關係回到 Active；契約依日期重新推導（起日已過的回到 InForce） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤補登的既有員工 | AnnulEntry（註銷 RegisterExistingEmployment） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件保留並標為已註銷；這段僱傭關係視為不存在 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 註銷錯了 | RevokeAnnulment | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件與它建立的紀錄恢復，身分不變 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 人的勞工名卡項目、身分證件、工作許可、契約、約定薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資或員工（員工可經由個資請求，Q22） | 不需核准，留紀錄；重大更正通知雇主 | 原值保留；依賴它的判定、警告與依日期推導的狀態重新推導 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 實際辦理日、保險人核定的生效日、申報的投保薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 要附保險人回執或標示「無回執」；原值保留；晚辦天數從有變成沒有時，通知雇主（老闆）；只更正系統內的登錄錯誤，向保險人申請更正加保日不在本切片（01_scope 不做）；同一生效日先誤報再更正投保薪資，是對同一筆的更正（02 InsuredSalary 卡） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 結束日、結束原因（到職後立刻離開） | CorrectRecord | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原值保留；結束日不能早於到職日（資料矛盾，阻擋） | [候選] | hire-employee（③ @ hire-employee/03-v1） |

不能註銷的事件：OverrideWarning、WithdrawWarningOverride、ExtendDataSubjectRequest、ResolveDataSubjectRequest、ArchivePersonalData、ReleaseArchival，以及所有建議層與由時間或條件觸發的事件（後者是推導的，依據改了就重新推導）。理由見 D-14。

沒有任何一種更正是直接覆蓋舊值或刪除事件：原值、被註銷的事件、更正者、時間、理由、證據都保留，實際保存方式依平台 P2（第 ⑤ 步）。
