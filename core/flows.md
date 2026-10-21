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
- 被引用：annual-leave-grant

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
| StartEmployment（到職） | 人的動作（人資確認這個人已開始提供勞務） | 發生 | Hire | Hire Hired → Started；建立 Employment（Active），登錄這個職務是否依法應參加公教或軍保（必填，D-21）；契約 Signed → InForce；約定薪資、針對錄用的有效警告忽略接續到僱傭關係 | 實際開始工作的日期；之後 shift-attendance 的上班打卡可以當證據 | 不可撤銷，只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v6） | annual-leave-grant |
| RegisterExistingEmployment（補登既有員工） | 人的動作（人資） | 發生 | Employment | （無）→ Active 或 Ended；同時登錄目前的投保、投保薪資、約定薪資、這個職務是否依法應參加公教或軍保（必填，D-21）等事實（02 D-12）；標為補登資料 | 既有的人事資料；當時依據說明（historical_basis_note） | 只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v6） | |
| RecordEarlyDeparture（到職後立刻離開） | 人的動作（人資） | 發生 | Employment | Active → Ended；記結束日、原因；契約 InForce → Ended，尚未生效的契約隨之失效（VoidContract） | 結束原因、登記者 | 只能更正；誤登時用 AnnulEntry | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| SignContract（簽訂勞動契約） | 人的動作（人資） | 發生 | EmploymentContract | （無）→ Signed | 書面契約（移工必須書面） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| ContractTermStarts（契約起日到達） | 時間或條件到達 | 發生 | EmploymentContract | Signed → InForce | 契約起日 | 起日更正或依據的到職被註銷時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| VoidContract（契約失效） | 其他單位個體的變化（錄用取消；起日前僱傭關係結束） | 發生 | EmploymentContract | Signed → Voided | 取消或結束的紀錄 | 造成它的事件被註銷時，依其餘事件重新推導 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| AgreeCompensation（約定薪資） | 人的動作（人資） | 決定 | Compensation | （無）→ Agreed | 錄取通知或契約上的薪資條件 | 只能更正；調薪屬 monthly-payroll | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordWorkAuthorization（登錄工作許可） | 外部系統或訊息（主管機關核發的許可函或展延核准，由人資登錄） | 發生 | WorkAuthorization | （無）→ Valid；展延時新增一筆核准紀錄：還有效時 Valid → Valid，晚登錄時 Expired → Valid | 許可函文號；免申請者的身分證件 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ExpireWorkAuthorization（工作許可到期） | 時間或條件到達 | 發生 | WorkAuthorization | Valid → Expired（只用於申請許可者） | 最後一筆核准的迄日 | 展延晚登錄時回到 Valid；期限更正時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ProposeAuthorizationReview（提醒確認許可） | 其他單位個體的變化（免申請者依據的身分證件被取代或到期） | 建議 | WorkAuthorization | 不改變狀態；提醒人資確認許可是否仍有效 | 新的身分證件與居留事由 | 可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| EndWorkAuthorization（登錄許可失效） | 人的動作（人資） | 發生 | WorkAuthorization | Valid → Expired | 人資確認依據的身分已消失 [待專家確認: EQ-018] | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordIdentityDocument（登錄身分證件） | 人的動作（人資依員工出示的證件） | 發生 | IdentityDocument | （無）→ Valid；換發或居留事由改變時，前一筆 Valid → Superseded | 證件核對紀錄（不代管證件） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| RecordPersonPeriod（登錄人的身分期間） | 人的動作（人資，依員工出示的戶籍、國籍或給付證明） | 發生 | Person | 不改變狀態；新增一段國籍（取得或喪失）、戶籍或居住登記（設籍或除籍）、已領取的老年給付；是真的改變，不是更正（登錯用 CorrectRecord）（D-18） | 戶籍謄本、國籍證明或給付核定的核對紀錄（不代管文件） | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v3） |  |
| RecordEmploymentPeriod（登錄僱傭關係的期間屬性） | 人的動作（人資） | 發生 | Employment | 不改變狀態；登錄這個職務從哪一天起是否依法應參加公教或軍保（例：私立學校的職員改任專任教職員）；是真的改變或補上未知的值，不是更正（登錯用 CorrectRecord）（D-21） | 人資依聘書、職務說明的核對紀錄 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v6） |  |
| ExpireIdentityDocument（證件到期） | 時間或條件到達 | 發生 | IdentityDocument | Valid → Expired | 有效期限 | 期限更正時重新推導 | 生效、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ProposeEnrollmentFiling（產生加保待辦） | 其他單位個體的變化（決定錄用、到職、改期、資料更正、註銷誤登；登錄新的身分證件（例：拿到居留證、取得永久居留）；登錄人的身分期間（RecordPersonPeriod：國籍、戶籍新增一段期間、領取老年給付）；登錄僱傭關係的期間屬性（RecordEmploymentPeriod：這個職務是否依法應參加公教或軍保，D-21）；雇主的判定條件改變：新增登記紀錄、取得核定課稅或購票證、免辦登記或行業類別改變、改為適用勞基法（維護屬 org-setup）；同一投保單位其他員工的到職或離開改變了人數）；人資記錄待人判斷的決定（記錄後依決定重新判定，D-20）；時間或條件到達（應辦理期限將到或已過；條件日期到了：員工滿 65 歲、新制度的施行日、身分證件的生效日（登錄時還沒生效的證件））（D-16、D-17） | 建議 | Hire 或 Employment | 不改變狀態；列出各保險是否適用、應辦理期限、法定生效日、預計的投保薪資級距；已過期限的標出晚幾天（逾期，不能忽略，辦理後結案）；錄用時（還沒到職）以約定到職日為預計到職日與判定日，結果標「預估」，到職時以實際到職日重新判定並取代（D-19）；需要人判斷的列出讓人資決定：受僱兩個雇主時就保擇一參加，就保標「待人判斷」；「其他」類固定給付算不算入投保薪資，各保險的適用照常判定，受影響的投保薪資級距待人判斷，列出待決定的給付項目（D-20）；系統只看得到系統內的僱傭關係，員工在系統外另有雇主時，人資可以主動記錄擇一參加的決定（D-20）；既有員工的適用改變（例：人數跨過門檻，原本自願的變成強制）一併列出；掛在已註銷僱傭關係上的投保提醒向保險人處理 | 判定用到的資料版本與規則版本 | 不由人作廢：只會被新的判定取代（記取代它的那一筆），或因辦理完成而結案；可自願的保險由雇主選擇不加時，記在這筆待辦上（人、時間）；待人判斷的事項由人資決定後，也記在這筆待辦上（決定、人、時間），新的判定沿用之前的決定（D-19）；記錄決定後立刻依決定重新判定，產生新的待辦取代這一筆（D-20）；所有待辦都保留，記錄依據的資料與規則版本（D-10、X-22） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v6） |  |
| RecordInsuranceFiling（登錄實際辦理加保） | 人的動作（人資在保險人辦完後登錄） | 執行 | InsuranceEnrollment | （無）→ Enrolled；記實際辦理日、是否自願、保險人核定的生效日 | 申報回執或保險人核定資料；沒有時標示「無回執」 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| DeclareInsuredSalary（申報投保薪資） | 人的動作（人資） | 執行 | InsuredSalary | （無）→ Effective；記金額、級距、分級表版本、申報日、來源 | 申報資料 | 只能更正 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| OverrideWarning（忽略警告） | 人的動作（人資） | 決定 | WarningOverride | （無）→ Active | 規則與版本、被警告的值、理由（可不填） | 可撤回（WithdrawWarningOverride） | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| LapseWarningOverride（忽略失效） | 其他單位個體的變化（被警告的資料改正或改變；到職時適用的規則版本或修訂和錄用時不同） | 發生 | WarningOverride | Active → Lapsed | 新的值或更正後的規則版本 | — | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| WithdrawWarningOverride（撤回忽略） | 人的動作（人資） | 決定 | WarningOverride | Active → Withdrawn；記撤回者、撤回時間 | — | 不可撤銷；要再忽略就是新的一筆 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| ReceiveDataSubjectRequest（收到個資請求） | 人的動作（員工提出；或人資代登錄） | 要求 | DataSubjectRequest | （無）→ Received | 請求內容、收到日期、收到管道 | 員工撤回時記為 Completed（D-07） | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| PromptDataSubjectRequestDeadline（提醒個資請求期限） | 時間或條件到達（法定處理期限將到或已過；延長過的依延長後的期限） | 建議 | DataSubjectRequest | 不改變狀態 | 收到日期、法定期限（第 ④ 步規則） | 可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ExtendDataSubjectRequest（延長個資請求處理期限） | 人的動作（人資） | 決定 | DataSubjectRequest | 不改變狀態（仍是 Received）；新增一筆延長紀錄：延長後的期限、延長原因、書面通知當事人的日期；可以延長多次（D-15） | 寄給當事人的書面通知 | 只能更正 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ResolveDataSubjectRequest（處理個資請求） | 人的動作（人資） | 決定 | DataSubjectRequest | Received → Completed 或 Rejected | 處理結果與理由；拒絕時的依據（被保存期間規則擋下時自動帶入） | 不可撤銷 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v2） |  |
| ProposeArchival（產生封存建議） | 其他單位個體的變化（到職前取消）；時間或條件到達（保存期間屆滿，屬 resignation） | 建議 | PersonalDataArchival | 不改變狀態；列出建議封存的人與個資類別；人資的處置（封存或暫不封存及理由）記在這筆建議上 | 取消日、保存期間規則 | 可作廢（保留紀錄與處置） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ArchivePersonalData（封存個資） | 人的動作（人資） | 決定 | PersonalDataArchival | （無）→ Archived | 封存的類別與理由 | 改用 ReleaseArchival | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| ReleaseArchival（解除封存） | 人的動作（人資） | 決定 | PersonalDataArchival | Archived → Released | 連到的錄用、個資請求或註銷紀錄；解除理由 | 不可撤銷；要再封存是新的一筆 | 發生、得知、生效 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |
| CorrectRecord（更正資料） | 人的動作（人資） | 發生 | 任何登錄的事實（見更正方式） | 不直接改變狀態；原值保留，新值生效，依賴它的判定與依日期推導的狀態重新推導；重大更正另產生 NotifySignificantCorrection | 更正理由與證據；更正者、時間（D-02） | 可以再更正 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| AnnulEntry（註銷誤登） | 人的動作（人資） | 發生 | 可註銷的事件（見 D-14 白名單） | 被註銷的事件視為沒發生，相關的狀態依其餘事件重新推導；原事件保留並標為已註銷；註銷前依當時資料產生的判定，依得知時間仍查得到；一律產生 NotifySignificantCorrection | 理由與證據（例：打卡、出勤、保險人回執） | 用 RevokeAnnulment 撤銷 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| RevokeAnnulment（撤銷註銷） | 人的動作（人資） | 發生 | 一筆 AnnulEntry | 原事件恢復，它建立的那一段與掛在上面的紀錄跟著恢復，身分不變；狀態重新推導；產生 NotifySignificantCorrection | 理由 | 不可撤銷；要再註銷是新的一筆 | 發生、得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | annual-leave-grant |
| NotifySignificantCorrection（通知重大更正） | 其他單位個體的變化（重大更正、註銷、撤銷註銷、拒絕個資請求） | 建議 | 被更正或註銷的事實 | 不改變狀態；列出改了什麼、誰改的、理由與證據、受影響的員工與改變的判定，通知雇主（老闆），並列入重大更正清單 | 更正或註銷的紀錄、更正前後的判定 | 不可作廢（保留紀錄） | 得知 | [候選] | hire-employee（③ @ hire-employee/03-v1） | |

## 更正方式（hire-employee）

更正與註銷都不需要第二個人核准，能追溯就好（D-02）：一律記錄誰、何時、理由與證據。是不是「重大更正」看**效果**，不看是哪個欄位：會改變任何投保單位的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主的，以及所有註銷與撤銷註銷，系統通知雇主（老闆）並列入重大更正清單（NotifySignificantCorrection）。

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 | 狀態 | 出處 |
|---|---|---|---|---|---|---|
| 錄用與到職資料的值（到職日、工作地點、組織單位、試用期、員工編號） | CorrectRecord | 人資或員工 | 不需核准，留紀錄；到職日的更正一律算重大更正 | 原值保留，記更正者、時間、理由；依更正後的資料重新判定各保險，更正前、當時系統知道的判定仍查得到（hire-employee:Q15）；依賴它的警告忽略紀錄依條件失效 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 雇主 | 不能用 CorrectRecord；AnnulEntry 註銷原本的到職（或補登），再對正確的雇主登錄 | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 換雇主就是另一段僱傭關係（02 D-03）；原紀錄保留並標為已註銷 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 僱傭關係或錄用登錯人（例：重複建了一個人） | CorrectRecord（改指到正確的人） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原本指向的人保留紀錄；兩筆人確認是同一人時的合併做法，第 ⑤ 步設計 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登到職（其實從未提供勞務） | AnnulEntry（註銷 StartEmployment），再登錄 CancelHire | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原到職事件保留並標為已註銷；這段僱傭關係視為不存在，不計入人數、年資、勞工名卡（01_scope D-12、hire-employee:Q14、hire-employee:Q18）；已加保的提醒向保險人處理（EQ-017）；後面依賴它的事件（例：到職後立刻離開）一起註銷 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登取消（其實已經到職） | AnnulEntry（註銷 CancelHire），再登錄 StartEmployment | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原取消事件保留並標為已註銷；錄用回到 Hired、契約依其餘事件重新推導，再到職；已封存的個資由人資解除（ReleaseArchival 連到這筆註銷） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤登到職後立刻離開（其實仍在職） | AnnulEntry（註銷 RecordEarlyDeparture） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件保留並標為已註銷；僱傭關係回到 Active；契約依日期重新推導（起日已過的回到 InForce） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 誤補登的既有員工 | AnnulEntry（註銷 RegisterExistingEmployment） | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件保留並標為已註銷；這段僱傭關係視為不存在 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 註銷錯了 | RevokeAnnulment | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原事件與它建立的紀錄恢復，身分不變 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 人的勞工名卡項目、身分證件、工作許可、契約、約定薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資或員工（員工可經由個資請求，hire-employee:Q22） | 不需核准，留紀錄；重大更正通知雇主 | 原值保留；依賴它的判定、警告與依日期推導的狀態重新推導 | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 實際辦理日、保險人核定的生效日、申報的投保薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 要附保險人回執或標示「無回執」；原值保留；晚辦天數從有變成沒有時，通知雇主（老闆）；只更正系統內的登錄錯誤，向保險人申請更正加保日不在本切片（01_scope 不做）；同一生效日先誤報再更正投保薪資，是對同一筆的更正（02 InsuredSalary 卡） | [候選] | hire-employee（③ @ hire-employee/03-v1） |
| 結束日、結束原因（到職後立刻離開） | CorrectRecord | 人資 | 不需核准，留紀錄；重大更正通知雇主 | 原值保留；結束日不能早於到職日（資料矛盾，阻擋） | [候選] | hire-employee（③ @ hire-employee/03-v1） |

不能註銷的事件：OverrideWarning、WithdrawWarningOverride、ExtendDataSubjectRequest、ResolveDataSubjectRequest、ArchivePersonalData、ReleaseArchival，以及所有建議層與由時間或條件觸發的事件（後者是推導的，依據改了就重新推導）。理由見 D-14。

沒有任何一種更正是直接覆蓋舊值或刪除事件：原值、被註銷的事件、更正者、時間、理由、證據都保留，實際保存方式依平台 P2（第 ⑤ 步）。

## 狀態機（annual-leave-grant）
<!-- 歷史需求：只需現況／需要軌跡／需要重建當時（依 Qnn）。「規則」欄第 ④ 步回填 -->

**狀態怎麼來**（沿用 core 的做法，core/flows.md「狀態怎麼來」）：
- 每個狀態都由事件序列解釋（平台 P1）。由日期觸發的事件（取得日到達、年度終結、約定或公司規定開始適用、廢止生效）是依登錄的日期與其他事件**推導**出來的；它依據的日期或事件被更正、註銷時，重新推導。
- 但**依規則給予的特休與年度終結的判定，推導出來之後就是事實**（02_entities D-03、D-06）：重新推導不是把舊結果蓋掉，而是透過 ReassessLeaveEntitlements、RejudgeLeaveYearEnd 記下「改了什麼、因為什麼」，更正前的內容保留（D-04）。
- 只是值打錯用 core 的 CorrectRecord；整筆登錯用 core 的 AnnulEntry（本切片可註銷的事件見「更正方式」，D-08）。
- 更正、註銷、較晚得知造成的轉換，凡是對員工不利（負數差額）或依據還沒處理完（重新判定後才補做的年度終結），先停在「待確認」，人資確認後才交給薪資；正常的年度終結與補發的正數差額直接交給薪資（D-11）。

### LeaveEntitlement（請假權利） [候選]（歷史需求：需要重建當時，依 annual-leave-grant:Q01、annual-leave-grant:Q09、annual-leave-grant:Q10、annual-leave-grant:Q11）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Active（可休）→ YearEnded（已年度終結）／EndedWithEmployment（隨僱傭關係結束，交由契約終止處理）／Voided（已作廢）
終態：Voided、EndedWithEmployment（本切片的終態；之後由 resignation 依契約終止轉換）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | GrantLeaveEntitlement | 系統 | 取得日到達（依年資與特休年度算出，annual-leave-grant:Q02）；取得日不早於雇主開始由系統管理的日子（之前的由人補登，01_scope D-09）；當天系統已知的僱傭關係仍在職（之後才得知結束日早於取得日的，見 EndLeaveEntitlementsWithEmployment；結束日剛好是取得日見 EQ-006 ④）；這位員工在取得日有特休年度（個別約定或雇主預設；兩者都沒有時第 ④ 步決定，[待專家確認: EQ-002]）；法定一筆，符合公司規定的每條加給各一筆（02_entities D-02） | R65、R66、R67、R68、R69、R70、R71、R74、R77、R80、R99 |
| （無） | Active | RegisterExistingLeaveEntitlement | 人資 | 僱傭關係的到職日早於雇主開始由系統管理的日子；可休迄日不早於開始由系統管理的日子（那天仍可以休，01_scope D-09）；來歷是補登當期或補登遞延 | R97 |
| （無） | Active | CloseLeaveYear | 系統 | 遞延進來的那一筆：原來那一筆有一筆「已協商」的遞延協商；遞延進來的額度是協商額度與終結時未休兩者較小的，協商本身不改（D-12） | R86、R87 |
| （無） | Active | RejudgeLeaveYearEnd | 系統 | 遞延進來的那一筆：原來那一筆年度終結之後才登錄遞延協商（D-06） | R84、R87、R92 |
| （無） | Active | ReassessLeaveEntitlements | 系統 | 依新依據多出一期，和任何既有的一筆都對不上（D-04）；可休迄日已經過了的，進來之後立刻由 CloseLeaveYear 判定，轉換先停在待確認（D-11） | R91、R93 |
| Active | Active | ReassessLeaveEntitlements | 系統 | 依新依據仍有同一來源（同一條公司規定）、同一期別、而且新舊可休期間有重疊的一筆（④ R91），但額度、年資級別或依據不同：就地更正，更正前的內容保留（02_entities D-07）；遞延進來的那一筆，原來那一筆的年度終結日改變時，可休期間跟著更正 | R91 |
| Active | YearEnded | CloseLeaveYear | 系統 | 可休迄日（年度終結日）已經過完；系統已知的僱傭關係到那天仍在職（結束日剛好是年度終結日的情況見 [待專家確認: EQ-011]） | R85、R86、R88、R89、R90、R93 |
| Active | EndedWithEmployment | EndLeaveEntitlementsWithEmployment | 系統 | 僱傭關係的結束日早於可休迄日，且取得日不晚於結束日（01_scope D-15） | R85 |
| Active | Voided | EndLeaveEntitlementsWithEmployment | 系統 | 結束日較晚才得知，這一筆的取得日晚於結束日：其實從未取得（D-05） | R95 |
| Active | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立，也對不上新的任何一筆（D-04）；或建立它的事件被註銷（RegisterExistingLeaveEntitlement 的 AnnulEntry） | R91 |
| Active | Voided | RejudgeLeaveYearEnd | 系統 | 遞延進來的那一筆：遞延協商撤回，或修改成 0（D-06） | R92 |
| YearEnded | YearEnded | ReassessLeaveEntitlements | 系統 | 依新依據仍是同一來源、同一期別、新舊可休期間有重疊（④ R91），但額度或依據不同：就地更正，接著 RejudgeLeaveYearEnd 記轉換差額 | R91、R92 |
| YearEnded | YearEnded | RejudgeLeaveYearEnd | 系統 | 年度終結判定用到的資料之後改變：已休、遞延協商（修改、撤回、事後才登錄）、這一筆的額度（D-06） | R92、R93 |
| YearEnded | Active | ReassessLeaveEntitlements | 系統 | 依新依據，這一筆的可休迄日還沒到（例：到職日往後更正）；已做的轉換各記一筆負數差額（待確認，D-11） | R91、R93 |
| YearEnded | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立，或建立它的事件被註銷；已做的轉換各記一筆負數差額（待確認） | R91、R93 |
| YearEnded | Voided | EndLeaveEntitlementsWithEmployment | 系統 | 遞延進來的那一筆：年度終結判定之後才得知僱傭關係在原年度終結日之前就結束，那次年度終結其實沒有發生（D-05） | R95 |
| YearEnded | EndedWithEmployment | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結判定之後才得知僱傭關係在年度終結日之前就結束；已做的轉換各記一筆負數差額（待確認），遞延進來的那一筆作廢，整筆交給 resignation（D-05） | R93、R95 |
| EndedWithEmployment | EndedWithEmployment | ReassessLeaveEntitlements | 系統 | 依新依據仍是同一來源、同一期別、新舊可休期間有重疊（④ R91），但額度或依據不同：就地更正；契約終止的轉換由 resignation 處理差額 | R91 |
| EndedWithEmployment | Active | ReassessLeaveEntitlements | 系統 | 僱傭關係的結束被註銷，或結束日更正到可休迄日之後；resignation 已做的契約終止轉換由 resignation 記負數差額（D-05） | R85、R91 |
| EndedWithEmployment | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立 | R91 |

說明：
- 「依規則給予」「遞延進來」「補登當期」「補登遞延」四種來歷用同一個狀態機；不同的是怎麼進到 Active，以及遞延進來與補登遞延的那筆不能再遞延（LeaveDeferralAgreement 的前提條件）。
- 補登的那筆是人登錄的事實，不參加重新判定的比對：依據更正時不會被系統作廢；和依規則重算的期間重疊或中間出現空檔時，由 NotifyLeaveReassessment 列出，人處理（D-04）。
- 需要重建當時：額度、期間、年資級別可能因依據更正而就地更正（02_entities D-07 要求標成需要重建當時），要回答「更正前給了什麼、當時依哪一版、誰在什麼時候改的」（annual-leave-grant:Q09、annual-leave-grant:Q11）；規則改版不觸發重新判定（02_entities D-03，annual-leave-grant:Q10）。
- 作廢的那筆保留紀錄，不算進任何推導值（02_entities X-17）；上面已休的天數、告知日、遞延協商不自動搬到新的一筆，由 NotifyLeaveReassessment 列出，人處理（D-04）。
- 「告知」不是這個狀態機的狀態，是推導的（見「推導的狀態與預估」，D-09）。

### LeaveDeferralAgreement（遞延協商） [候選]（歷史需求：需要重建當時，依 annual-leave-grant:Q05、annual-leave-grant:Q06）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Agreed（已協商，待年度終結）→ Applied（已依它遞延）／Withdrawn（已撤回）／Lapsed（失效：要遞延的那一筆沒有進到年度終結）
終態：Withdrawn、Lapsed

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Agreed | RecordLeaveDeferral | 人資 | 要遞延的那一筆是 Active；來歷是依規則給予或補登當期（遞延進來、補登遞延的不能再遞延，特別休假#01 `[未核對]`）；那一筆沒有其他有效的遞延協商（02_entities D-05）；公司規定的那筆能不能延 [待專家確認: EQ-005]；遞延額度的上限第 ④ 步 | R82、R83、R98 |
| （無） | Applied | RecordLeaveDeferral | 人資 | 要遞延的那一筆已經 YearEnded（年度終結後才登錄）；登錄時間晚於年度終結日一律成立「年度終結後才登錄遞延協商」的警告（不論填的協商日是哪天）；協商日晚於年度終結日的算不算數 [待專家確認: EQ-003]，這版可以登錄、不阻擋；登錄後立刻 RejudgeLeaveYearEnd，減少工資的差額待確認（D-06、D-11） | R82、R84、R92、R98 |
| Agreed | Agreed | AmendLeaveDeferral | 人資 | 雙方重新協商（協商日、遞延額度改變），原內容保留 | R82、R83、R98 |
| Agreed | Withdrawn | WithdrawLeaveDeferral | 人資 | 雙方取消遞延；記撤回者、撤回時間、理由 | — |
| Agreed | Applied | CloseLeaveYear | 系統 | 要遞延的那一筆年度終結 | R86 |
| Agreed | Lapsed | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結之前僱傭關係結束（未休的交給 resignation，01_scope D-15） | R85 |
| Agreed | Lapsed | ReassessLeaveEntitlements | 系統 | 要遞延的那一筆因重新判定而作廢 | R91 |
| Applied | Applied | AmendLeaveDeferral | 人資 | 年度終結後才重新協商 [待專家確認: EQ-003]；同樣成立「年度終結後才登錄」的警告；修改後 RejudgeLeaveYearEnd 更正遞延進來的那一筆並記轉換差額（D-06） | R82、R84、R92、R98 |
| Applied | Withdrawn | WithdrawLeaveDeferral | 人資 | 年度終結後才撤回 [待專家確認: EQ-003]；撤回後 RejudgeLeaveYearEnd：遞延進來的那一筆作廢，原來那一筆的未休改為轉為工資（差額） | R84、R92 |
| Applied | Lapsed | ReassessLeaveEntitlements | 系統 | 原來那一筆因重新判定而作廢；遞延進來的那一筆也作廢 | R91 |
| Applied | Lapsed | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結判定之後才得知僱傭關係在原年度終結日之前就結束；遞延進來的那一筆作廢（D-05） | R95 |
| Lapsed | Agreed | ReassessLeaveEntitlements | 系統 | 讓它失效的原因被更正（僱傭關係的結束被註銷或結束日更正；那一筆恢復對應），而且那一筆還沒做過年度終結判定（看狀態，不看日期；之後補做年度終結時依恢復的協商遞延，④ X-23） | R91 |

說明：
- 需要重建當時，不只是需要軌跡：年度終結的判定依「判定當時已知的協商內容」做，之後協商被修改或撤回，要能說出判定當時是多少、差額是因為哪一次修改（annual-leave-grant:Q05、annual-leave-grant:Q06；雇主負舉證責任，勞基法第 38 條第 6 項，特別休假#01 `[未核對]`）。
- 「修改」和「更正」分開：雙方重新談是 AmendLeaveDeferral（協商日改變）；只是登錄時打錯是 CorrectRecord（協商日不變）。兩者都保留原內容（D-06）。
- 協商遞延的額度大於年度終結時的未休（例：談定延 3 天，之後又休了 2 天，只剩 2 天）：遞延進來的那一筆只建 2 天，協商仍記 3 天，成立「協商遞延額度超過未休」的警告（D-12）。

### LeaveYearAgreement（特休年度約定） [候選]（歷史需求：需要軌跡，依 annual-leave-grant:Q03、annual-leave-grant:Q14）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Scheduled（尚未適用）→ Effective（適用中）→ Superseded（已被下一筆取代）／Ended（已終止，之後回到雇主預設）
終態：Superseded、Ended

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Scheduled | RecordLeaveYearAgreement | 人資 | 適用起日在未來；同一段僱傭關係、同一假別同一天只有一筆有效（第 ④ 步） | R72、R98 |
| （無） | Effective | RecordLeaveYearAgreement | 人資 | 適用起日不在未來；適用起日早於已給予的特休的取得日時，觸發 ReassessLeaveEntitlements（D-10） | R72、R75、R98 |
| Scheduled | Effective | ActivateLeaveYearAgreement | 系統 | 適用起日到達 | R71、R75 |
| Effective | Superseded | ActivateLeaveYearAgreement | 系統 | 同一段僱傭關係、同一假別的下一筆約定開始適用 | R75 |
| Scheduled | Ended | EndLeaveYearAgreement | 人資 | 還沒適用就取消 | R98 |
| Effective | Ended | EndLeaveYearAgreement | 人資 | 雙方協商不再個別約定，之後套用雇主預設；終止日早於已給予的取得日時觸發 ReassessLeaveEntitlements | R75、R98 |

說明：
- 需要軌跡，不需要重建當時：「這位員工某天適用哪一種」由各筆約定的適用起日與終止日就看得出來（annual-leave-grant:Q03）；每一筆特休給予時依哪一種已經凍結在那一筆上（`leave_year_basis` 與 appliedYearAgreement，02_entities D-04），所以約定本身只要知道誰、何時登錄或更正。
- 改用另一種的那一年怎麼換算是第 ④ 步的規則 [待專家確認: EQ-002]；已經給予的特休不因為改用另一種而改變（annual-leave-grant:Q14、annual-leave-grant:US-D10）。
- 僱傭關係結束時約定不另外轉換狀態：結束後不再給予，約定也不會再被用到。
- 雇主改了預設，沒有個別約定的員工之後就套用新的預設；年度是勞雇雙方協商的結果（01_scope D-12），所以預設改變時，對還在套用預設的員工成立警告，不同意的員工由人資替他登錄一筆維持原年度的約定（D-13）。工作規則改預設算不算協商 [待專家確認: EQ-002]。

### CompanyPolicy（公司規定） [候選]（歷史需求：需要重建當時，依 annual-leave-grant:Q09、annual-leave-grant:Q10）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v3）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：shared
- 被引用：（無）

狀態：Scheduled（尚未生效）→ Effective（生效中）→ Repealed（已廢止）
終態：Repealed

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Scheduled | EstablishCompanyPolicy | 人資或雇主（老闆） | 第一次生效日在未來；這版以固定資料提供 [靜態替代]（02_entities CompanyPolicy 卡） | R73、R78、R98 |
| （無） | Effective | EstablishCompanyPolicy | 人資或雇主（老闆） | 第一次生效日不在未來；早於已經給予的特休取得日時，觸發 ReassessLeaveEntitlements（補上那段期間應有的加給，D-14） | R73、R76、R78、R98 |
| Scheduled | Scheduled | ReviseCompanyPolicy | 人資或雇主（老闆） | 還沒生效前修改內容（新的版本） | R73、R78 |
| Scheduled | Effective | ActivateCompanyPolicy | 系統 | 第一次生效日到達 | R76 |
| Effective | Effective | ReviseCompanyPolicy | 人資或雇主（老闆） | 內容修改是同一條規定的新版本，有自己的生效日（版本是規則資料，第 ④ 步，平台 P5）；已經依舊版給予的特休不變（annual-leave-grant:Q10）；年度終結時依哪一版處理見 [待專家確認: EQ-013]。版本內容登錄錯誤時新增一筆修訂（只限人資），是依據更正，接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | R73、R76、R78、R79、R91、R92 |
| Repealed | Repealed | ReviseCompanyPolicy | 人資 | 只限修訂已登錄的版本內容（登錄錯誤）；依它給予的特休可能還在可休；接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | R73、R78、R91、R92 |
| Effective | Effective | RepealCompanyPolicy | 人資或雇主（老闆） | 登錄廢止，廢止日在未來（到那天由 ExpireCompanyPolicy 轉換） | R98 |
| Scheduled | Repealed | RepealCompanyPolicy | 人資或雇主（老闆） | 還沒生效就取消 | R98 |
| Effective | Repealed | RepealCompanyPolicy | 人資或雇主（老闆） | 廢止日不在未來；已經依它給予的特休不受影響 | R76、R98 |
| Effective | Repealed | ExpireCompanyPolicy | 系統 | 廢止日到達 | R76 |

說明：需要重建當時：特休要能說出「依哪一條公司規定的哪一版」給的（annual-leave-grant:Q09），公司規定改版或廢止後，已給予的依原版本（annual-leave-grant:Q10）。公司規定本身的生效日、廢止日是登錄的事實，打錯更正時和到職日一樣觸發重新判定（D-14）；版本內容（多給幾天、適用對象、年度終結處理）登錄錯誤時新增一筆修訂，也是依據更正，觸發重新判定；改版（新的版本）不觸發（02_entities D-03，D-16）。

### LeaveConversion（請假權利轉換） [候選]（歷史需求：需要重建當時，依 annual-leave-grant:Q05、annual-leave-grant:Q08、annual-leave-grant:Q11）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Provisional（待確認）→ Determined（已判定）／Discarded（未確認即被取代）
終態：Determined、Discarded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Determined | CloseLeaveYear | 系統 | 正常的年度終結：那一筆年度終結時有未休額度，沒有遞延的部分轉為工資；公司規定的那筆依公司規定轉為工資（失效的見下一列，[待專家確認: EQ-005]）；遞延進來、補登遞延的那筆全部轉為工資，依原年度終結日計算（02_entities D-05） | R79、R86、R89、R90、R93 |
| （無） | Provisional | CloseLeaveYear | 系統 | 補做的年度終結：判定日晚於可休迄日的隔天（由重新判定新增、恢復，或就地更正後迄日變成過去；結束被註銷或延後後補做），已休、遞延協商還沒由人處理（D-11）；公司多給的轉為失效；公司多給的那一筆找不到依據的版本（④ R93） | R86、R93 |
| （無） | Determined | RejudgeLeaveYearEnd | 系統 | 更正差額，增加員工的工資（正數）：依更正後的資料重新判定，和已判定的總額不同；指回被更正的那一次，記更正原因（02_entities D-06） | R89、R90、R92、R93 |
| （無） | Provisional | RejudgeLeaveYearEnd | 系統 | 更正差額，減少員工的工資（負數）或改為失效（D-11） | R92、R93 |
| （無） | Provisional | ReassessLeaveEntitlements | 系統 | 更正差額：那一筆因重新判定而回到可休、作廢、額度改變，或建立它的事件被註銷、撤銷註銷 | R90、R91、R93 |
| （無） | Provisional | EndLeaveEntitlementsWithEmployment | 系統 | 負數差額：年度終結判定之後才得知僱傭關係在年度終結日之前就結束（D-05） | R90、R93、R95 |
| Provisional | Determined | ConfirmLeaveConversion | 人資 | 人資看過 NotifyLeaveReassessment 列出的事（已休、遞延協商、告知日），確認這一筆；確認後才交給薪資（D-11） | R94 |
| Provisional | Discarded | RejudgeLeaveYearEnd | 系統 | 確認前依據又改變，重新算出的取代它；被取代的保留紀錄 | R92 |
| Provisional | Discarded | ReassessLeaveEntitlements | 系統 | 確認前依據又改變，重新算出的取代它 | R91 |

說明：
- 已判定（Determined）的轉換不再改變（02_entities D-06）：已經交給薪資的那一批不能改，發現要更正時另記一筆差額（可以是負數，多發的怎麼處理 [待專家確認: EQ-009]）。每一筆轉換由哪一次判定產生、判定當時依哪些資料，要查得到（annual-leave-grant:Q05、annual-leave-grant:Q11）。
- 待確認（Provisional）的還沒交給薪資，所以可以被取代（Discarded）而不是記差額；被取代的保留紀錄。待確認期間發給期限照樣計算，確認晚於期限的成立警告（第 ④ 步）。

### LeaveType（假別） [候選]（歷史需求：只需現況，依 annual-leave-grant:Q01）
- 出處：annual-leave-grant（③ @ annual-leave-grant/03-v2）；文中的 D-nn、X-nn 指該切片 03_flows.md 的決定與反例
- 層：domain
- 被引用：（無）

狀態：Active（使用中）→ Deprecated（已停用）
終態：Deprecated

不設事件與轉換表：法令訂定的假別是全平台共用的參考資料（02_entities D-10、D-15），由平台維運直接維護；法令廢止時標為停用，不刪除，已經給予的請假權利照原意解讀（docs/01 0.2 第 1 級）。

說明：只需現況：驗收問題只問「這一筆是哪一種假」（annual-leave-grant:Q01），沒有人問假別的名稱或代碼什麼時候改過；依 docs/01 ③「可以簡化的時候」不做事件（D-07）。公司自訂的假別由之後的切片定義，到時再判斷要不要事件。

## 推導的狀態與預估（annual-leave-grant）
<!-- 不是狀態機：不存、不由事件改變，依據改了就重算（D-09） -->

| 項目 | 可能的值 | 怎麼推出來 | 依哪條 Q |
|---|---|---|---|
| 一筆法定特休的告知狀態（只有依規則給予的法定特休；補登的不判定，01_scope D-09；隨僱傭關係結束、作廢的不判定，④ D-24） | 待告知（期限內）／已告知／逾期未告知／逾期後告知 | 取得日、告知期限（`notice_due_on`）、實際告知日（`notified_on`）與今天；告知日被更正過的看得出來（core CorrectRecord 保留原值）；逾期是法規警告，可以忽略（core OverrideWarning），不阻擋。符合條件之前就告知算不算數 [待專家確認: EQ-006]；曆年制一筆可能要告知兩次 [待專家確認: EQ-002] | annual-leave-grant:Q07 |
| 還可以休的、已休、遞延出去、轉為工資、失效 | 數量 | 02_entities 的推導值；已休這版以固定資料提供 [靜態替代] | annual-leave-grant:Q05、annual-leave-grant:Q08 |
| 某天適用哪一種特休年度 | 週年制、曆年制（固定起始日的年度） | 當天有效的個別約定；沒有就用當天有效的雇主預設 | annual-leave-grant:Q03 |
| 之後各期的預估（還沒取得的） | 預計取得日、天數、可休期間 | 依目前的到職日、特休年度與目前的規則版本試算；只是預估，不建立請假權利，取得日到達才由 GrantLeaveEntitlement 給予（D-01）；規則改版、到職日更正、改用另一種年度後預估會變 | annual-leave-grant:Q01、annual-leave-grant:Q02（annual-leave-grant:US-D01） |
| 法規警告：告知逾期、可能應合併年資、曆年制換算少於法定、公司規定少於法定、年度終結後才登錄遞延協商（看登錄時間）、協商遞延額度超過未休、雇主預設的特休年度改變而員工還在套用預設、待確認的轉換超過發給期限 | 成立／不成立 | 依資料與規則推出，資料改正就消失；忽略時用 core 的 OverrideWarning（02_entities D-16）；判斷條件是第 ④ 步的規則 | annual-leave-grant:Q02、annual-leave-grant:Q05、annual-leave-grant:Q07、annual-leave-grant:Q14 |

## 事件（annual-leave-grant）
<!-- 觸發來源：人的動作／其他單位個體的變化／外部系統或訊息／時間或條件到達
     層：要求／建議／決定／發生／執行（「建議」層不改變狀態）
     有意義的時間：發生／得知／生效 -->

| 事件 | 觸發來源 | 層 | 主體 | 改變什麼 | 證據 | 能否撤銷 | 有意義的時間 | 狀態 | 出處 | 被引用 |
|---|---|---|---|---|---|---|---|---|---|---|
| GrantLeaveEntitlement（給予特休） | 時間或條件到達（取得日到達，且系統已知的僱傭關係當天在職、取得日不早於開始由系統管理的日子） | 發生 | LeaveEntitlement | （無）→ Active；法定一筆，符合的公司加給各一筆；記下依據（規則版本、特休年度與它依據的約定或預設、取得日當時的年資、依據的到職日，02_entities D-03） | 到職日、特休年度約定或雇主預設、規則版本 | 不可撤銷；依據更正時由 ReassessLeaveEntitlements 重新判定 | 發生（取得日）、得知、生效（可休起日） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RegisterExistingLeaveEntitlement（補登仍可休的特休） | 人的動作（人資） | 發生 | LeaveEntitlement | （無）→ Active；登錄來源、來歷（補登當期或補登遞延）、額度、開始管理前已休、可休期間；補登遞延的另登原年度終結日（01_scope D-09） | 雇主原有的紀錄（例：既有的特休表） | 值用 CorrectRecord；整筆登錯用 AnnulEntry（觸發 ReassessLeaveEntitlements） | 發生（開始由系統管理的日子）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RecordLeaveNotice（登錄告知排定特休） | 人的動作（人資或雇主（老闆）） | 發生 | LeaveEntitlement | 不改變狀態；記實際告知日，告知狀態跟著重推 | 告知方式的說明（例：電子郵件、公告） | 值用 CorrectRecord（人資）；整筆登錯用 AnnulEntry（人資） | 發生（告知日）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RecordLeaveYearAgreement（登錄特休年度約定） | 人的動作（人資，依雙方協商的結果） | 決定 | LeaveYearAgreement | （無）→ Scheduled 或 Effective；適用起日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 協商日、協商方式的說明（例：個別書面約定） | 值用 CorrectRecord；整筆登錯用 AnnulEntry；改用另一種是登錄新的一筆 | 發生（協商日）、得知、生效（適用起日） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| ActivateLeaveYearAgreement（約定開始適用） | 時間或條件到達（適用起日到達） | 發生 | LeaveYearAgreement | Scheduled → Effective；同一段僱傭關係、同一假別的前一筆 Effective → Superseded | 適用起日 | 不可撤銷；適用起日更正時重新推導 | 生效 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| EndLeaveYearAgreement（終止特休年度約定） | 人的動作（人資，依雙方協商的結果） | 決定 | LeaveYearAgreement | Scheduled 或 Effective → Ended；之後套用雇主預設；終止日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 協商日、說明 | 值用 CorrectRecord；登錯用 AnnulEntry | 發生（協商日）、得知、生效（終止日） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| EstablishCompanyPolicy（訂定公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | （無）→ Scheduled 或 Effective；第一版的內容（第 ④ 步的規則資料）；生效日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 依據說明（例：工作規則第 12 條、公司公告） | 值用 CorrectRecord；整筆登錯用 AnnulEntry | 發生、得知、生效 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| ReviseCompanyPolicy（修改公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | 不改變狀態；新增一個版本，有自己的生效日；已經依舊版給予的特休不變；事項為特休年度預設的，對還在套用預設的員工成立警告（D-13）；修訂（登錄錯誤，只限人資）觸發 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | 依據說明 | 版本內容要更正是新的修訂（平台 P5，D-16） | 發生、得知、生效 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |  |
| ActivateCompanyPolicy（公司規定生效） | 時間或條件到達（第一次生效日到達） | 發生 | CompanyPolicy | Scheduled → Effective | 第一次生效日 | 不可撤銷；生效日更正時重新推導 | 生效 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RepealCompanyPolicy（廢止公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | 登錄廢止日；廢止日不在未來的 Scheduled 或 Effective → Repealed，在未來的到那天由 ExpireCompanyPolicy 轉換；已給予的特休不受影響 | 依據說明 | 值用 CorrectRecord；整筆登錯用 AnnulEntry | 發生、得知、生效（廢止日） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| ExpireCompanyPolicy（公司規定廢止生效） | 時間或條件到達（廢止日到達） | 發生 | CompanyPolicy | Effective → Repealed | 廢止日 | 不可撤銷；廢止日更正時重新推導 | 生效 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RecordLeaveDeferral（登錄遞延協商） | 人的動作（人資，依勞雇雙方協商的結果） | 決定 | LeaveDeferralAgreement | （無）→ Agreed；年度終結後才登錄的 → Applied，並觸發 RejudgeLeaveYearEnd | 協商日、遞延額度、協商方式與憑據的說明（例：書面同意書） | 用 AmendLeaveDeferral 修改、WithdrawLeaveDeferral 撤回；打錯用 CorrectRecord | 發生（協商日）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| AmendLeaveDeferral（修改遞延協商） | 人的動作（人資，依雙方重新協商的結果） | 決定 | LeaveDeferralAgreement | 不改變狀態（Agreed 或 Applied 不變）；改協商日與遞延額度，原內容保留；已 Applied 的觸發 RejudgeLeaveYearEnd | 新的協商日、憑據說明 | 可以再修改或撤回 | 發生（新的協商日）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| WithdrawLeaveDeferral（撤回遞延協商） | 人的動作（人資，依雙方取消遞延） | 決定 | LeaveDeferralAgreement | Agreed 或 Applied → Withdrawn；已 Applied 的觸發 RejudgeLeaveYearEnd | 撤回理由 | 不可撤銷；要再遞延是新的一筆協商 | 發生、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| CloseLeaveYear（年度終結判定） | 時間或條件到達（一筆請假權利的可休迄日過完，且系統已知的僱傭關係到那天仍在職） | 發生 | LeaveEntitlement | 那一筆 Active → YearEnded；依「已協商」的遞延協商產生遞延進來的一筆（Active，額度見 D-12），協商 Agreed → Applied；其餘未休額度產生轉換（LeaveConversion：轉為工資，或公司規定的失效），記工資計算基準日與發給期限（02_entities D-06）；由重新判定新增的那一筆，轉換是待確認（D-11） | 判定當時已知的已休（記下當時的數字，D-15）、遞延協商的內容、規則版本 | 不可撤銷；判定用到的資料之後改變時由 RejudgeLeaveYearEnd 記差額 | 發生（年度終結日）、得知（判定日） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| RejudgeLeaveYearEnd（重新判定年度終結） | 其他單位個體的變化（已年度終結的那一筆：已休改變（含這版固定資料的改正）、遞延協商修改、撤回或事後登錄、額度就地更正、依據的公司規定版本被修訂（D-16）） | 發生 | LeaveEntitlement | YearEnded 不變；遞延進來的那一筆新增、更正額度或作廢；轉換另記差額，指回被更正的那一次，記更正原因，負數的待確認（D-11）；待確認還沒確認的被取代；產生 NotifyLeaveReassessment | 改變了什麼、判定當時與現在的資料 | 不可撤銷；資料再改變時再重新判定 | 發生（年度終結日）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |  |
| ReassessLeaveEntitlements（依據更正後重新判定特休） | 其他單位個體的變化（到職日更正；特休年度約定登錄、終止、更正或註銷；員工類型等決定適用哪一條公司規定的資料更正；公司規定的生效日、廢止日登錄或更正；公司規定版本內容的修訂（D-16）；僱傭關係的到職或結束被註銷、撤銷註銷；結束日更正；補登的特休被註銷或撤銷註銷） | 發生 | LeaveEntitlement | 依新依據重算每一期，和既有的依規則給予的逐筆對應（D-04）：對得上的就地更正（保留更正前內容；已年度終結的接著 RejudgeLeaveYearEnd）、對不上的作廢、多出來的新增；已年度終結的回到可休或作廢時，轉換記差額（待確認）；遞延協商依對應結果失效或恢復；產生 NotifyLeaveReassessment。規則改版不觸發（02_entities D-03） | 被更正的依據（更正前、更正後）、更正者 | 不可撤銷；依據再更正時再重新判定 | 發生（依據被更正的時間）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |  |
| EndLeaveEntitlementsWithEmployment（僱傭關係結束，停止特休） | 其他單位個體的變化（系統得知僱傭關係 Active → Ended：core 的 RecordEarlyDeparture，或 resignation 定義的離職；這版一般離職以固定資料提供 [靜態替代]，載入結束日視同這個變化） | 發生 | LeaveEntitlement | 取得日不晚於結束日、可休迄日晚於結束日的每一筆 Active → EndedWithEmployment；取得日晚於結束日的（結束日較晚得知）→ Voided；年度終結判定之後才得知的，那一筆 YearEnded → EndedWithEmployment、遞延進來的那筆作廢、Applied 的協商 Lapsed、已做的轉換記負數差額（待確認）；Agreed 的遞延協商 → Lapsed；之後不再給予（01_scope D-15，D-05） | 結束日 | 不可撤銷；結束被註銷或結束日更正時由 ReassessLeaveEntitlements 重新推導 | 發生（結束日）、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| ConfirmLeaveConversion（確認待確認的轉換） | 人的動作（人資） | 決定 | LeaveConversion | Provisional → Determined；確認後交給薪資切片（D-11） | 確認者、時間；人資處理過的事（已休、遞延協商、告知日） | 不可撤銷；確認後發現要更正，另記差額 | 發生、得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） | |
| NotifyLeaveReassessment（通知特休重新判定結果） | 其他單位個體的變化（ReassessLeaveEntitlements、RejudgeLeaveYearEnd 改變了額度、期間、狀態，或產生轉換差額；CloseLeaveYear 遇到協商遞延額度超過未休） | 建議 | LeaveEntitlement | 不改變狀態；列出改了哪幾筆（更正前、更正後）、新增或作廢的、轉換差額與待確認的轉換，以及要人處理的：作廢的那筆上已休的天數、要重新登錄的告知日、要重新登錄的遞延協商、已休超過更正後額度的、補登的那筆和依規則重算的期間重疊或有空檔的、已判定轉換的工資計算基準日或發給期限依新依據會不同的（原 → 新，④ D-25）；通知人資與雇主（老闆）（D-04） | 重新判定的紀錄 | 不可作廢（保留紀錄） | 得知 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |  |

沿用 core 的事件（不重新定義）：CorrectRecord（更正資料）、AnnulEntry（註銷誤登）、RevokeAnnulment（撤銷註銷）、OverrideWarning（忽略警告）、WithdrawWarningOverride（撤回忽略），這些依 core 只有人資可以做；觸發本切片的 core 事件：RecordEarlyDeparture、StartEmployment、RegisterExistingEmployment（D-08）。

## 更正方式（annual-leave-grant）
更正都不需要第二個人核准，能追溯就好（inputs/shared/範圍釐清_更正不需核准.md）：一律記錄誰、何時、理由。沒有任何一種更正是直接覆蓋舊值或刪除事件，實際保存方式依平台 P2（第 ⑤ 步）。對員工不利的轉換差額先停在待確認（D-11）。

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 | 狀態 | 出處 |
|---|---|---|---|---|---|---|
| 到職日、員工類型等給予特休的依據（core 的僱傭關係資料） | CorrectRecord（core），接著 ReassessLeaveEntitlements | 人資或員工 | 不需核准，留紀錄；到職日的更正依 core 是重大更正 | 原值保留；已給予的每一筆依 D-04 對應：就地更正的保留更正前內容，作廢的保留紀錄；已判定的轉換不改，另記差額（02_entities D-06）；NotifyLeaveReassessment 列出結果 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 特休年度約定的內容（年度種類、適用起日、終止日、協商日） | CorrectRecord（core），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原值保留；依它給予的特休依 D-04 重新判定 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 整筆登錯的特休年度約定 | AnnulEntry（core，註銷 RecordLeaveYearAgreement），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原事件保留並標為已註銷；那段期間改用前一筆約定或雇主預設 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 補登的特休（額度、開始管理前已休、可休期間、原年度終結日） | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 RegisterExistingLeaveEntitlement），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原值保留；已年度終結的由 RejudgeLeaveYearEnd 記差額；被註銷的那筆作廢，已做的轉換記負數差額（待確認），上面已休的天數由 NotifyLeaveReassessment 列出；撤銷註銷時恢復，轉換再依 ReassessLeaveEntitlements 記差額 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 實際告知日 | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 RecordLeaveNotice） | 人資或雇主（老闆） | 不需核准，留紀錄（由人資執行） | 原值保留；告知狀態重推，看得出更正過 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 遞延協商登錄時打錯（協商日、額度） | CorrectRecord（core） | 人資 | 不需核准，留紀錄 | 原值保留；已 Applied 的由 RejudgeLeaveYearEnd 記差額。雙方重新談不是更正，用 AmendLeaveDeferral（D-06） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 已判定的轉換（額度、工資計算基準日、發給期限） | RejudgeLeaveYearEnd 或 ReassessLeaveEntitlements 記一筆差額 | 系統（依據改變時）或人資 | 不需核准，留紀錄；負數差額由人資確認後才交給薪資 | 不改原判定；差額指回被更正的那一次，記更正原因（02_entities D-06）；不能用 CorrectRecord 直接改 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 公司規定的名稱、依據說明、生效日、廢止日 | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 EstablishCompanyPolicy） | 人資 | 不需核准，留紀錄 | 原值保留；生效日、廢止日改變時接著 ReassessLeaveEntitlements（D-14）；版本內容的登錄錯誤用 ReviseCompanyPolicy 新增修訂（只限人資），接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |
| 已休（這版的固定資料） | RejudgeLeaveYearEnd（人資改正固定資料 [靜態替代] 後，對已年度終結的那一筆） | 人資 | 不需核准，留紀錄 | 固定資料的改正也記誰、何時、理由；判定當時的已休記在那次判定上，不會被改正蓋掉（D-15）；正式的請假更正由 annual-leave-request 定義 | [候選] | annual-leave-grant（③ @ annual-leave-grant/03-v1） |

本切片可以註銷的事件：RegisterExistingLeaveEntitlement、RecordLeaveNotice、RecordLeaveYearAgreement、EndLeaveYearAgreement、EstablishCompanyPolicy、RepealCompanyPolicy。不能註銷的：遞延協商的三個事件（用修改、撤回、更正處理，D-06）、ReviseCompanyPolicy（版本更正是新的修訂）、ConfirmLeaveConversion（確認後的更正記差額）、所有由時間或條件、其他單位個體的變化觸發的事件（推導的，依據改了就重新推導或記差額）、建議層的 NotifyLeaveReassessment（D-08）。

不能直接改的：依規則給予的特休額度沒有人工加減的動作（02_entities D-07）；覺得給錯時，更正它依據的資料。

