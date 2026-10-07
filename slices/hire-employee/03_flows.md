# hire-employee ③ 流程與狀態

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ③ 流程與狀態 |
| 狀態 | 待檢查 |
| 版本 | （凍結後填 tag，例：hire-employee/03-v1） |
| 產出者 | AI（Claude） |
| 讀取的輸入 | 01_scope.md @ hire-employee/01-v1；02_entities.md @ hire-employee/02-v1；slices/PLAN.md D-27、D-28、D-29、D-33 @ 4d051d4；docs/03 P1～P4、P7（平台約定未填，只引用其分類） |

<!-- 本文件的「誰可以做」用業務角色：
     人資＝雇主指定處理人事的人（小雇主可以是老闆本人；PLAN.md P-05 小團隊沒有部門也照樣有人資）
     雇主（老闆）＝雇主的負責人；核准人＝依 D-02 需要第二個人確認時的確認者
     員工＝當事人；系統＝依規則自動產生，只能產生「建議」層的事件，或依登錄的日期與條件推導狀態變化 -->

## 狀態機
<!-- 歷史需求：只需現況／需要軌跡／需要重建當時（依 Qnn）。「規則」欄第 ④ 步回填 -->

**狀態怎麼來**：每個狀態都由事件序列解釋（平台 P1）。
- 由日期觸發的轉換（到期、契約起日到達、隨其他事件連動的失效）是依登錄的日期與其他事件**推導**出來的；它依據的日期或事件被更正、註銷時，重新推導，不照原紀錄重播（D-03、D-12）。
- 發現某個改變狀態的事件根本是誤登（例：其實沒來卻登錄到職），用 AnnulEntry（註銷誤登）標記那個事件：被註銷的事件視為沒有發生，狀態依其餘事件重新推導；這不是狀態機上的轉換，所以不會從終態轉出。註銷錯了用 RevokeAnnulment（撤銷註銷）恢復原事件，原本的那一段與掛在上面的紀錄跟著恢復，身分不變（D-03）。
- 只是值打錯（例：到職日打錯）用 CorrectRecord：不直接改變狀態，但依那個值推導的狀態跟著重算（例：證件期限打錯而被判到期，更正期限後回到有效）。
- 會改變人數門檻、保險適用、晚辦天數的更正與所有註銷，要先提出核准申請（ApprovalRequest），核准後才生效（D-02）。

### Hire（錄用）（歷史需求：需要軌跡，依 Q14）
狀態：Hired（已錄用）→ Started（已到職）／Cancelled（到職前取消）
終態：Started、Cancelled

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Hired | DecideHire | 人資 | 人已登錄（新的人或同客戶內既有的人，Q11）；有雇主與約定到職日 | |
| Hired | Hired | RescheduleStart | 人資 | 新的到職日和原本不同；原本的到職日保留（Q14） | |
| Hired | Started | StartEmployment | 人資 | 這個人已經實際開始提供勞務（01_scope D-07）；到職日不早於決定錄用日 | |
| Hired | Cancelled | CancelHire | 人資 | 還沒開始提供勞務；到職日當天沒來也屬這一種（01_scope D-12） | |

註銷誤登：註銷 CancelHire（其實已經到職）→ 錄用回到 Hired，再登錄 StartEmployment（發生時間為實際到職日）；註銷 StartEmployment（其實從未上班）→ 錄用回到 Hired，再登錄 CancelHire。原本的事件都保留並標為已註銷。

### Employment（僱傭關係）（歷史需求：需要重建當時，依 Q13、Q15、Q18）
狀態：Active（在職）→ Ended（已結束）
終態：Ended

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | StartEmployment | 人資 | 來自一筆 Hired 的錄用 | |
| （無） | Active | RegisterExistingEmployment | 人資 | 到職日早於這個雇主開始由系統管理的日子（D-09）；沒有錄用紀錄（02 D-12） | |
| （無） | Ended | RegisterExistingEmployment | 人資 | 補登已結束的先前一段（例：回任時要找得到，Q11）；到職日與結束日都早於這個雇主開始由系統管理的日子（D-09） | |
| Active | Ended | RecordEarlyDeparture | 人資 | 結束日不早於到職日；本切片只處理到職後立刻離開（01_scope D-12），一般離職由 resignation 定義觸發事件 | |

註銷誤登：註銷建立這段僱傭關係的 StartEmployment 或 RegisterExistingEmployment → 這段僱傭關係視為不存在：不計入人數門檻、年資、勞工名卡（Q12、Q18），紀錄保留並標為已註銷；掛在它上面的契約、投保見下方各狀態機。前提是它後面沒有還沒註銷、又依賴它的事件（例：之後的到職後立刻離開），有的話依相反順序一起註銷（D-03）。同一人在同一雇主不能同時有兩段在職的僱傭關係（第 ④ 步規則，資料矛盾，阻擋）。

說明：需要重建當時，是因為到職日、雇主、工作地點等被更正後，要依更正後的資料重新判定各保險，也要看得出更正前、當時系統知道的判定（Q15），以及當時依哪一版規則（Q13）。所以所有登錄事實的事件都記「得知」時間（D-10）。

### EmploymentContract（勞動契約）（歷史需求：需要軌跡，依 Q15、Q19）
狀態：Signed（已簽訂，尚未生效）→ InForce（生效中）→ Ended（已結束）；Signed → Voided（從未生效即失效）
終態：Ended、Voided

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Signed | SignContract | 人資 | 掛在錄用上（到職前簽，02 D-18）或僱傭關係上 | |
| Signed | InForce | StartEmployment | 系統（隨到職） | 契約起日不晚於到職日；生效時間取契約起日與到職日較晚者 | |
| Signed | InForce | ContractTermStarts | 系統 | 僱傭關係仍為 Active，且契約起日到達（起日晚於到職日、或續約的新契約） | |
| Signed | Voided | VoidContract | 系統（隨錄用取消或僱傭關係結束） | 契約掛在被取消的錄用上；或契約起日還沒到，僱傭關係就結束 | |
| InForce | Ended | RecordEarlyDeparture | 系統（隨僱傭關係結束） | — | |

註銷誤登：註銷造成 Voided 或 Ended 的事件（例：誤登取消），契約依其餘事件回到 Signed 或 InForce。定期契約到期、續約、視為不定期契約都不在本切片（01_scope 不做），到期的轉換由 resignation 定義。

### WorkAuthorization（工作許可）（歷史需求：需要重建當時，依 Q16）
狀態：Valid（有效）↔ Expired（已失效）
終態：（無；展延晚登錄時可以回到有效）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordWorkAuthorization | 人資 | 依主管機關核發的許可函登錄；免申請者依身分證件登錄（02 D-06） | |
| Valid | Expired | ExpireWorkAuthorization | 系統 | 登錄的期限屆滿，且沒有已登錄的展延 | |
| Valid | Expired | EndWorkAuthorization | 人資 | 免申請者依據的身分已消失，經人資確認（D-08）；許可被廢止的登錄不在本切片 | |
| Expired | Valid | RecordWorkAuthorization | 人資 | 登錄期限屆滿前已核准、但較晚才登錄的展延；仍是同一筆，文號留歷史（02 WorkAuthorization 卡），生效時間為原期限的次日 | |

說明：要重建「到職日那天許可是否有效、發給哪個雇主」（Q16）；展延晚登錄後，到期與恢復兩筆轉換都保留，依發生與得知時間分得出「當時系統以為已失效」和「實際一直有效」（D-10）。申請、廢止、轉換雇主不在本切片（01_scope 不做）。

### IdentityDocument（身分證件）（歷史需求：需要重建當時，依 Q06、Q10）
狀態：Valid（有效）→ Expired（已到期）／Superseded（被新的一筆取代）
終態：Expired、Superseded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Valid | RecordIdentityDocument | 人資 | 依員工出示的證件登錄（不代管證件，01_scope D-20） | |
| Valid | Superseded | RecordIdentityDocument | 人資 | 換發、展延，或居留事由改變而另記一筆（02 D-05）；生效時間為新證件的生效日 | |
| Valid | Expired | ExpireIdentityDocument | 系統 | 有效期限屆滿 | |

說明：健保、就保、勞退的適用看「某一天」的居留身分（Q06）。居留證展延是新的一份（02 IdentityDocument 卡），所以晚登錄的展延是新的一筆 Valid，前一筆維持 Expired，期間依生效日接續。

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
| （無） | Enrolled | RecordInsuranceFiling | 人資 | 依實際向保險人辦理的結果登錄實際辦理日；保險人核定的生效日可以另外輸入；附申報回執，沒有時標示「無回執」（D-02） | |
| Enrolled | Terminated | （由 resignation 定義：退保） | 人資 | 不在本切片 | |

說明：
- Terminated 在本切片走不到，由 resignation 定義觸發事件；先列出，避免 resignation 另立一套（D-06）。
- 掛在一段被註銷的僱傭關係上的投保，在保險人那邊仍是真的加保，系統不會自動改變它的狀態；系統產生建議（ProposeEnrollmentFiling）提醒人資向保險人處理，處理方式待 [待專家確認: EQ-017]。投保本身登錯（登在錯的人或錯的制度）用 AnnulEntry 註銷 RecordInsuranceFiling。
- 到職前就先加保：目前投保一定掛在僱傭關係上（02 forEmployment 為 1），到職前記不下來。若 EQ-005 的答覆是「實務上會提早加保」，要回到第 ② 步把投保改為可以掛在錄用上（第 0 級回頭修改）（X-11）。
- 自願或強制：`voluntary` 記的是辦理當時是否以自願身分加保（事實）。之後人數跨過門檻，「現在應為強制」是推導值，由 ProposeEnrollmentFiling 提醒，不改寫當時的紀錄（X-12）。

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
| Active | Lapsed | LapseWarningOverride | 系統 | 它針對的警告不再成立（資料已改正），或警告內容改變：被警告的值和 warned_value 不同，或**適用於被警告事實的**規則版本或修訂不同（例：實際到職日落在新版最低工資的期間、規則有新的修訂）。對已判定的事實，之後才生效的新版本不影響（D-11） | |
| Active | Withdrawn | WithdrawWarningOverride | 人資 | — | |

說明：
- 失效後如果警告仍成立（例：月薪改了但仍低於最低工資），會重新列為「未處理的警告」，要再次忽略就是新的一筆。
- 錄用時忽略的警告（針對錄用）：到職時重新評估。被警告的值與適用的規則版本都沒變（例：約定薪資接續掛到僱傭關係、到職日仍在同一版的期間），StartEmployment 為這筆紀錄加上針對僱傭關係的連結，原本針對錄用的連結不改；有變就失效。「目前有哪些員工帶著未處理的警告」看的是僱傭關係，還沒到職的看錄用（Q20）（X-08、X-20）。
- 規則版本不在原處修改：版本內容要更正時，是一個新的修訂，有自己的得知時間；忽略紀錄記住當時依據的版本與修訂（第 ④ 步、平台 P5）。

### PersonalDataArchival（個資封存）（歷史需求：需要軌跡，依 Q22）
狀態：Archived（封存中）→ Released（已解除）
終態：Released

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Archived | ArchivePersonalData | 人資 | 保存目的消失（例：到職前取消的人；離職後保存期間屆滿，屬 resignation）；寫明封存的個資類別 | |
| Archived | Released | ReleaseArchival | 人資 | 連到一筆需要這些個資的紀錄：新的錄用（回任，Q11）、個資請求，或註銷誤登的取消；可以只解除部分類別 | |

說明：依法刪除（不只是封存）的做法在第 ⑤ 步依平台 P7 設計（01_scope D-20），本切片不定義刪除的狀態。誰可以查看哪些個資（Q22 前半）是權限設定，不是流程，在第 ④ 步寫規則、第 ⑤ 步依 P7 落實。

### DataSubjectRequest（個資請求）（歷史需求：需要軌跡，依 Q22）
狀態：Received（已收到）→ Completed（已完成）／Rejected（已拒絕）
終態：Completed、Rejected

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Received | ReceiveDataSubjectRequest | 員工（自己提出）；人資（代登錄書面、email、口頭的請求，記收到管道） | 請求來自當事人本人 | |
| Received | Completed | ResolveDataSubjectRequest | 人資 | 已執行請求的內容（例：更正走 CorrectRecord、停止利用或刪除走 ArchivePersonalData）；部分接受也算完成，結果寫明；員工撤回也記為完成，結果寫「當事人撤回」（D-07） | |
| Received | Rejected | ResolveDataSubjectRequest | 人資 | 有法定的拒絕理由（例：依業務必要不刪除），寫明理由；已有一筆核准的核准申請（D-02） | |

### ApprovalRequest（核准申請）[待使用者決定：回到第 ② 步新增，D-13]（歷史需求：需要軌跡，依 Q15、Q20、Q22）
狀態：Pending（待核准）→ Approved（已核准）／Rejected（已駁回）／Withdrawn（已撤回）
終態：Approved、Rejected、Withdrawn

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Pending | RequestApproval | 人資 | 要做的動作需要核准（D-02）：寫明動作、對象、新值或要註銷的事件、理由、證據 | |
| Pending | Approved | ApproveRequest | 核准人 | 核准人不是提出人；只有一個人的雇主由老闆本人核准，標為「自行核准」 | |
| Pending | Rejected | RejectRequest | 核准人 | 寫明駁回理由 | |
| Pending | Withdrawn | WithdrawRequest | 提出人 | — | |

說明：核准前，要更正、註銷的東西維持原狀，判定照舊；核准後才執行（CorrectRecord、AnnulEntry、RevokeAnnulment、拒絕個資請求），執行事件連到這筆申請。被駁回、撤回的申請保留，查得到「誰想改什麼」（X-18）。這是流程（動詞）本身的狀態機；依六問第 0 問，它之後有狀態要追蹤，應建成 Entity，需要回到第 ② 步新增（D-13）。

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
| RescheduleStart（到職前改期） | 人的動作（人資） | 決定 | Hire | Hired → Hired；約定到職日改變，原本的值保留 | 改期的理由 | 可以再改期 | 發生、得知、生效 |
| CancelHire（到職前取消） | 人的動作（人資） | 決定 | Hire | Hired → Cancelled；掛在錄用上的契約隨之失效（VoidContract） | 取消原因 | 不可撤銷；再錄用是新的一筆錄用；誤登時用 AnnulEntry | 發生、得知 |
| PromptStartConfirmation（提醒確認到職） | 時間或條件到達（約定到職日到了，錄用仍是 Hired） | 建議 | Hire | 不改變狀態 | 約定到職日 | 可作廢（保留紀錄） | 得知 |
| StartEmployment（到職） | 人的動作（人資確認這個人已開始提供勞務） | 發生 | Hire | Hire Hired → Started；建立 Employment（Active）；契約 Signed → InForce；約定薪資、針對錄用的有效警告忽略接續到僱傭關係 | 實際開始工作的日期；之後 shift-attendance 的上班打卡可以當證據 | 不可撤銷，只能更正；誤登時用 AnnulEntry | 發生、得知 |
| RegisterExistingEmployment（補登既有員工） | 人的動作（人資） | 發生 | Employment | （無）→ Active 或 Ended；同時登錄目前的投保、投保薪資、約定薪資等事實（02 D-12）；標為補登資料 | 既有的人事資料；當時依據說明（historical_basis_note） | 只能更正；誤登時用 AnnulEntry | 發生、得知 |
| RecordEarlyDeparture（到職後立刻離開） | 人的動作（人資） | 發生 | Employment | Active → Ended；記結束日、原因；契約 InForce → Ended，尚未生效的契約隨之失效（VoidContract） | 結束原因、登記者 | 只能更正；誤登時用 AnnulEntry | 發生、得知 |
| SignContract（簽訂勞動契約） | 人的動作（人資） | 發生 | EmploymentContract | （無）→ Signed | 書面契約（移工必須書面） | 只能更正 | 發生、得知、生效 |
| ContractTermStarts（契約起日到達） | 時間或條件到達 | 發生 | EmploymentContract | Signed → InForce | 契約起日 | 起日更正或依據的到職被註銷時重新推導 | 生效、得知 |
| VoidContract（契約失效） | 其他單位個體的變化（錄用取消；起日前僱傭關係結束） | 發生 | EmploymentContract | Signed → Voided | 取消或結束的紀錄 | 造成它的事件被註銷時，依其餘事件重新推導 | 發生、得知 |
| AgreeCompensation（約定薪資） | 人的動作（人資） | 決定 | Compensation | （無）→ Agreed | 錄取通知或契約上的薪資條件 | 只能更正；調薪屬 monthly-payroll | 發生、得知、生效 |
| RecordWorkAuthorization（登錄工作許可） | 外部系統或訊息（主管機關核發的許可函或展延核准，由人資登錄） | 發生 | WorkAuthorization | （無）→ Valid；展延晚登錄時 Expired → Valid | 許可函文號；免申請者的身分證件 | 只能更正 | 發生、得知、生效 |
| ExpireWorkAuthorization（工作許可到期） | 時間或條件到達 | 發生 | WorkAuthorization | Valid → Expired | 登錄的期限 | 展延晚登錄時回到 Valid；期限更正時重新推導 | 生效、得知 |
| ProposeAuthorizationReview（提醒確認許可） | 其他單位個體的變化（免申請者依據的身分證件被取代或到期） | 建議 | WorkAuthorization | 不改變狀態；提醒人資確認許可是否仍有效 | 新的身分證件與居留事由 | 可作廢（保留紀錄） | 得知 |
| EndWorkAuthorization（登錄許可失效） | 人的動作（人資） | 發生 | WorkAuthorization | Valid → Expired | 人資確認依據的身分已消失 [待專家確認: EQ-018] | 只能更正 | 發生、得知、生效 |
| RecordIdentityDocument（登錄身分證件） | 人的動作（人資依員工出示的證件） | 發生 | IdentityDocument | （無）→ Valid；換發或居留事由改變時，前一筆 Valid → Superseded | 證件核對紀錄（不代管證件） | 只能更正 | 發生、得知、生效 |
| ExpireIdentityDocument（證件到期） | 時間或條件到達 | 發生 | IdentityDocument | Valid → Expired | 有效期限 | 期限更正時重新推導 | 生效、得知 |
| ProposeEnrollmentFiling（產生加保待辦） | 其他單位個體的變化（決定錄用、到職、改期、資料更正、註銷誤登；同一投保單位其他員工的到職或離開改變了人數）；時間或條件到達（應辦理期限將到或已過） | 建議 | Hire 或 Employment | 不改變狀態；列出各保險是否適用、應辦理期限、法定生效日、預計的投保薪資級距；已過期限的標出晚幾天；既有員工的適用改變（例：人數跨過門檻，原本自願的變成強制）一併列出；掛在已註銷僱傭關係上的投保提醒向保險人處理 | 判定用到的資料版本與規則版本 | 不由人作廢：只會被新的判定取代（記取代它的那一筆），或因辦理完成而結案；可自願的保險由雇主選擇不加時，記在這筆待辦上（人、時間）；所有待辦都保留，記錄依據的資料與規則版本（D-10、X-22） | 得知 |
| RecordInsuranceFiling（登錄實際辦理加保） | 人的動作（人資在保險人辦完後登錄） | 執行 | InsuranceEnrollment | （無）→ Enrolled；記實際辦理日、是否自願、保險人核定的生效日 | 申報回執或保險人核定資料；沒有時標示「無回執」 | 只能更正 | 發生、得知、生效 |
| DeclareInsuredSalary（申報投保薪資） | 人的動作（人資） | 執行 | InsuredSalary | （無）→ Effective；記金額、級距、分級表版本、申報日、來源 | 申報資料 | 只能更正 | 發生、得知、生效 |
| OverrideWarning（忽略警告） | 人的動作（人資） | 決定 | WarningOverride | （無）→ Active | 規則與版本、被警告的值、理由（可不填） | 可撤回（WithdrawWarningOverride） | 發生、得知 |
| LapseWarningOverride（忽略失效） | 其他單位個體的變化（被警告的資料改正或改變；到職時適用的規則版本或修訂和錄用時不同） | 發生 | WarningOverride | Active → Lapsed | 新的值或更正後的規則版本 | — | 發生、得知 |
| WithdrawWarningOverride（撤回忽略） | 人的動作（人資） | 決定 | WarningOverride | Active → Withdrawn；記撤回者、撤回時間 | — | 不可撤銷；要再忽略就是新的一筆 | 發生、得知 |
| ReceiveDataSubjectRequest（收到個資請求） | 人的動作（員工提出；或人資代登錄） | 要求 | DataSubjectRequest | （無）→ Received | 請求內容、收到日期、收到管道 | 員工撤回時記為 Completed（D-07） | 發生、得知 |
| PromptDataSubjectRequestDeadline（提醒個資請求期限） | 時間或條件到達（法定處理期限將到或已過） | 建議 | DataSubjectRequest | 不改變狀態 | 收到日期、法定期限（第 ④ 步規則） | 可作廢（保留紀錄） | 得知 |
| ResolveDataSubjectRequest（處理個資請求） | 人的動作（人資；拒絕需核准人確認） | 決定 | DataSubjectRequest | Received → Completed 或 Rejected | 處理結果與理由 | 不可撤銷 | 發生、得知 |
| ProposeArchival（產生封存建議） | 其他單位個體的變化（到職前取消）；時間或條件到達（保存期間屆滿，屬 resignation） | 建議 | PersonalDataArchival | 不改變狀態；列出建議封存的人與個資類別；人資的處置（封存或暫不封存及理由）記在這筆建議上 | 取消日、保存期間規則 | 可作廢（保留紀錄與處置） | 得知 |
| ArchivePersonalData（封存個資） | 人的動作（人資） | 決定 | PersonalDataArchival | （無）→ Archived | 封存的類別與理由 | 改用 ReleaseArchival | 發生、得知、生效 |
| ReleaseArchival（解除封存） | 人的動作（人資） | 決定 | PersonalDataArchival | Archived → Released | 連到的錄用、個資請求或註銷紀錄；解除理由 | 不可撤銷；要再封存是新的一筆 | 發生、得知、生效 |
| CorrectRecord（更正資料） | 人的動作（人資；需核准的，在核准申請核准後） | 發生 | 任何登錄的事實（見更正方式） | 不直接改變狀態；原值保留，新值生效，依賴它的判定與依日期推導的狀態重新推導 | 更正理由；更正者、時間；需核准的連到核准申請（D-02） | 可以再更正 | 發生、得知 |
| AnnulEntry（註銷誤登） | 人的動作（人資，在核准申請核准後） | 發生 | 可註銷的事件（見 D-14 白名單） | 被註銷的事件視為沒發生，相關的狀態依其餘事件重新推導；原事件保留並標為已註銷；註銷前依當時資料產生的判定，依得知時間仍查得到 | 連到核准申請；理由與證據（例：打卡、出勤、保險人回執） | 用 RevokeAnnulment 撤銷 | 發生、得知 |
| RevokeAnnulment（撤銷註銷） | 人的動作（人資，在核准申請核准後） | 發生 | 一筆 AnnulEntry | 原事件恢復，它建立的那一段與掛在上面的紀錄跟著恢復，身分不變；狀態重新推導 | 連到核准申請；理由 | 不可撤銷；要再註銷是新的一筆 | 發生、得知 |
| RequestApproval（提出核准申請） | 人的動作（人資） | 要求 | ApprovalRequest | （無）→ Pending | 要做的動作、對象、理由、證據；系統試算的影響 | 用 WithdrawRequest 撤回 | 發生、得知 |
| ApproveRequest（核准） | 人的動作（核准人） | 決定 | ApprovalRequest | Pending → Approved | 核准人、時間；自行核准時標示 | 不可撤銷；核准後執行前發現錯誤，再提出相反的申請 | 發生、得知 |
| RejectRequest（駁回） | 人的動作（核准人） | 決定 | ApprovalRequest | Pending → Rejected | 駁回理由 | 不可撤銷；可以重新提出 | 發生、得知 |
| WithdrawRequest（撤回申請） | 人的動作（提出人） | 要求 | ApprovalRequest | Pending → Withdrawn | — | 不可撤銷 | 發生、得知 |

四種觸發來源都有：人的動作（大部分；需核准的動作分成提出、核准、執行三個事件，D-02）、其他單位個體的變化（VoidContract、ProposeEnrollmentFiling、ProposeAuthorizationReview、LapseWarningOverride、ProposeArchival）、外部系統或訊息（RecordWorkAuthorization）、時間或條件到達（PromptStartConfirmation、ContractTermStarts、ExpireWorkAuthorization、ExpireIdentityDocument、ProposeEnrollmentFiling、PromptDataSubjectRequestDeadline、ProposeArchival）。保險人核定的生效日目前由人資登錄（01_scope D-04，系統不連線勞保局），之後若串接保險人回覆，RecordInsuranceFiling 的觸發來源會改為外部系統或訊息。

## 決策流程
<!-- 訊號 → 證據 → 狀態 → 建議 → 決定；沒有需要判斷的地方寫「無」 -->

### 一、到職後要辦哪些加保
- 訊號：決定錄用、到職、到職前改期、資料更正、註銷誤登；同一投保單位其他員工的到職或離開；或應辦理期限將到、已過。
- 證據：人的國籍、戶籍、證件與居留事由、出生日期、已領的老年給付；雇主型態、登記日、是否適用勞基法；投保單位在當天的計入人數與名單（依實際到職、離開的**發生**日期計算，不是登錄日，Q12）；到職日；約定薪資；當時有效的規則版本與分級表版本（沒有對應版本時標「無對應規則版本」，PLAN.md D-33）。
- 狀態：各保險為強制、可自願或不適用；應辦理期限、法定生效日；應申報的投保薪資級距；已登錄的實際辦理日與差距；既有員工的適用是否改變。
- 建議：ProposeEnrollmentFiling 產生加保待辦（哪幾種、哪天前辦、預計從哪天生效、報哪一級），可自願的列出讓雇主選擇。
- 決定：人資在保險人辦完後登錄（RecordInsuranceFiling、DeclareInsuredSalary）；可自願的由雇主決定加或不加。系統的待辦不會自己建立投保。

### 二、法規警告：改資料，還是照樣存檔
- 訊號：存檔錄用、到職、契約、約定薪資、工作許可、加保資料時，規則檢查不通過。
- 證據：被檢查的值、適用於這個事實的規則與版本（例：約定月薪 28,000 與到職日當時的每月最低工資）。
- 狀態：一個成立中的法規警告（推導值，不另存）。
- 建議：顯示警告與依據的規則。
- 決定：人資改正資料（CorrectRecord，警告消失），或照樣存檔（OverrideWarning，建立警告忽略紀錄）。資料本身矛盾的直接阻擋，不能忽略（01_scope D-17）；哪一條警告、哪一條阻擋，第 ④ 步逐條標出。

### 三、約定到職日到了，有沒有來
- 訊號：約定到職日到了，錄用仍是 Hired。
- 證據：約定到職日；之後可加上 shift-attendance 的上班打卡。
- 狀態：錄用尚未確認到職。
- 建議：PromptStartConfirmation 提醒人資確認。
- 決定：人資登錄到職（StartEmployment，發生時間記實際開始的日期）、改期（RescheduleStart），或取消（CancelHire）。系統不因日期到了就自動視為到職（D-01）。人數門檻以實際到職的發生日期計算，所以晚確認不會讓過去的人數算錯，但會讓加保待辦晚出現；第 ④ 步可設「到職日過了幾天仍未確認」的警告。

### 四、免申請的工作許可是否仍有效
- 訊號：免申請者依據的身分證件被取代或到期（例：離婚後依法繼續居留而另記一筆居留證）。
- 證據：新的證件與居留事由。
- 狀態：許可依據的身分可能已消失。
- 建議：ProposeAuthorizationReview 提醒人資確認。
- 決定：人資確認仍有效（不動作），或登錄失效（EndWorkAuthorization）。系統不自動判定失去工作資格，因為法規解讀待 [待專家確認: EQ-018]（D-08）。

### 五、要不要封存個資
- 訊號：到職前取消；（之後的切片）離職後保存期間屆滿。
- 證據：取消日或離職日、各類個資的保存規則（第 ④ 步）。
- 狀態：保存目的已消失的個資類別。
- 建議：ProposeArchival 列出建議封存的人與類別。
- 決定：人資封存（ArchivePersonalData），或暫不封存並寫理由（記在這筆建議上）。

### 六、會影響其他員工的更正
- 訊號：提出的更正或註銷，會改變某個投保單位在某些日期的計入人數、某人的保險適用或晚辦天數（例：到職日、結束日、出生日期、居留事由、雇主）。
- 證據：更正前後的人數與名單。
- 狀態：其他員工的適用（強制、可自願）可能改變。
- 建議：系統在核准申請上列出受影響的員工與改變的判定（試算，不改變狀態），供核准人判斷；核准後由 ProposeEnrollmentFiling 產生新的待辦，並通知雇主（老闆）。
- 決定：核准人核准或駁回這筆核准申請（D-02），核准後才執行更正或註銷；人資依新的待辦處理。

## 更正方式

需不需要核准，看更正的**效果**，不看是哪個欄位（D-02）：會改變任何投保單位的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主的，以及所有註銷與撤銷註銷，都要先提出核准申請（RequestApproval → ApproveRequest），核准後才執行。系統在申請上試算影響，判斷是否需要核准。

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 |
|---|---|---|---|---|
| 錄用與到職資料的值（到職日、工作地點、組織單位、試用期、員工編號） | CorrectRecord | 人資或員工 | 依效果：到職日一律要；其他改變上述效果時要 | 原值保留，記更正者、時間、理由；依更正後的資料重新判定各保險，更正前、當時系統知道的判定仍查得到（Q15）；依賴它的警告忽略紀錄依條件失效 |
| 雇主 | 不能用 CorrectRecord；AnnulEntry 註銷原本的到職（或補登），再對正確的雇主登錄 | 人資 | 核准人 | 換雇主就是另一段僱傭關係（02 D-03）；原紀錄保留並標為已註銷 |
| 僱傭關係或錄用登錯人（例：重複建了一個人） | CorrectRecord（改指到正確的人） | 人資 | 核准人 | 原本指向的人保留紀錄；兩筆人確認是同一人時的合併做法，第 ⑤ 步設計 |
| 誤登到職（其實從未提供勞務） | AnnulEntry（註銷 StartEmployment），再登錄 CancelHire | 人資 | 核准人 | 原到職事件保留並標為已註銷；這段僱傭關係視為不存在，不計入人數、年資、勞工名卡（01_scope D-12、Q14、Q18）；已加保的提醒向保險人處理（EQ-017）；後面依賴它的事件（例：到職後立刻離開）一起註銷 |
| 誤登取消（其實已經到職） | AnnulEntry（註銷 CancelHire），再登錄 StartEmployment | 人資 | 核准人 | 原取消事件保留並標為已註銷；錄用回到 Hired、契約依其餘事件重新推導，再到職；已封存的個資由人資解除（ReleaseArchival 連到這筆註銷） |
| 誤登到職後立刻離開（其實仍在職） | AnnulEntry（註銷 RecordEarlyDeparture） | 人資 | 核准人 | 原事件保留並標為已註銷；僱傭關係回到 Active；契約依日期重新推導（起日已過的回到 InForce） |
| 誤補登的既有員工 | AnnulEntry（註銷 RegisterExistingEmployment） | 人資 | 核准人 | 原事件保留並標為已註銷；這段僱傭關係視為不存在 |
| 註銷錯了 | RevokeAnnulment | 人資 | 核准人 | 原事件與它建立的紀錄恢復，身分不變 |
| 人的勞工名卡項目、身分證件、工作許可、契約、約定薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資或員工（員工可經由個資請求，Q22） | 依效果：出生日期、國籍、戶籍、居留事由、證件期限、許可期限與雇主、月薪多半會改變保險適用，要核准；姓名、住址等不需要 | 原值保留；依賴它的判定、警告與依日期推導的狀態重新推導 |
| 實際辦理日、保險人核定的生效日、申報的投保薪資 | CorrectRecord；整筆登錯用 AnnulEntry | 人資 | 核准人 | 要附保險人回執或標示「無回執」；原值保留；晚辦天數從有變成沒有時，通知雇主（老闆）；只更正系統內的登錄錯誤，向保險人申請更正加保日不在本切片（01_scope 不做）；同一生效日先誤報再更正投保薪資，是對同一筆的更正（02 InsuredSalary 卡） |
| 結束日、結束原因（到職後立刻離開） | CorrectRecord | 人資 | 結束日：核准人（會改變人數）；原因：不需要 | 原值保留；結束日不能早於到職日（資料矛盾，阻擋） |

不能註銷的事件：OverrideWarning、WithdrawWarningOverride、ResolveDataSubjectRequest、ArchivePersonalData、ReleaseArchival、核准申請的事件，以及所有建議層與由時間或條件觸發的事件（後者是推導的，依據改了就重新推導）。理由見 D-14。

沒有任何一種更正是直接覆蓋舊值或刪除事件：原值、被註銷的事件、更正者、核准人、時間、理由、證據都保留，實際保存方式依平台 P2（第 ⑤ 步）。

## 詞彙對照表新增

| ID | 種類 | 定義 | zh-TW | 對照備註 |
|---|---|---|---|---|
| Hire.Hired | 狀態 | 已決定錄用，還沒開始提供勞務 | 已錄用 | |
| Hire.Started | 狀態 | 這個人已開始提供勞務，錄用轉成僱傭關係 | 已到職 | |
| Hire.Cancelled | 狀態 | 到職前取消 | 到職前取消 | |
| Employment.Active | 狀態 | 僱傭關係進行中 | 在職 | |
| Employment.Ended | 狀態 | 僱傭關係已結束 | 已結束 | |
| EmploymentContract.Signed | 狀態 | 已簽訂，尚未生效 | 已簽訂 | |
| EmploymentContract.InForce | 狀態 | 契約生效中 | 生效中 | |
| EmploymentContract.Ended | 狀態 | 契約已結束 | 已結束 | |
| EmploymentContract.Voided | 狀態 | 從未生效就失效（錄用取消、或起日前僱傭關係就結束） | 已失效 | |
| WorkAuthorization.Valid | 狀態 | 許可有效 | 有效 | |
| WorkAuthorization.Expired | 狀態 | 許可期限屆滿，或依據的身分經確認已消失 | 已失效 | |
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
| DataSubjectRequest.Completed | 狀態 | 已處理完成（含部分接受、當事人撤回） | 已完成 | |
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
| VoidContract | 事件 | 契約從未生效就失效（隨錄用取消或僱傭關係結束） | 契約失效 | |
| AgreeCompensation | 事件 | 約定薪資 | 約定薪資 | |
| RecordWorkAuthorization | 事件 | 登錄主管機關核發的工作許可、展延，或免申請的身分 | 登錄工作許可 | |
| ExpireWorkAuthorization | 事件 | 工作許可到期 | 工作許可到期 | |
| ProposeAuthorizationReview | 事件 | 免申請者依據的身分證件改變，提醒確認許可 | 提醒確認許可 | 建議層 |
| EndWorkAuthorization | 事件 | 人資確認許可依據的身分已消失 | 登錄許可失效 | |
| RecordIdentityDocument | 事件 | 登錄員工出示的身分證件 | 登錄身分證件 | |
| ExpireIdentityDocument | 事件 | 證件有效期限屆滿 | 證件到期 | |
| ProposeEnrollmentFiling | 事件 | 依判定產生加保待辦 | 產生加保待辦 | 建議層 |
| RecordInsuranceFiling | 事件 | 登錄實際向保險人辦理加保的結果 | 登錄實際辦理加保 | |
| DeclareInsuredSalary | 事件 | 申報投保薪資 | 申報投保薪資 | |
| OverrideWarning | 事件 | 看到法規警告後照樣存檔 | 忽略警告 | |
| LapseWarningOverride | 事件 | 警告不再成立或內容改變，忽略失效 | 忽略失效 | |
| WithdrawWarningOverride | 事件 | 撤回忽略的決定 | 撤回忽略 | |
| ReceiveDataSubjectRequest | 事件 | 收到當事人的個資請求 | 收到個資請求 | |
| PromptDataSubjectRequestDeadline | 事件 | 個資請求的法定處理期限將到或已過 | 提醒個資請求期限 | 建議層 |
| ResolveDataSubjectRequest | 事件 | 完成或拒絕個資請求 | 處理個資請求 | |
| ProposeArchival | 事件 | 依保存目的產生封存建議 | 產生封存建議 | 建議層 |
| ArchivePersonalData | 事件 | 封存某人的部分個資 | 封存個資 | |
| ReleaseArchival | 事件 | 解除封存 | 解除封存 | |
| CorrectRecord | 事件 | 更正登錄錯誤的值，原值保留 | 更正資料 | |
| AnnulEntry | 事件 | 註銷一筆誤登的事件，狀態依其餘事件重新推導 | 註銷誤登 | |
| RevokeAnnulment | 事件 | 撤銷一筆註銷，原事件恢復 | 撤銷註銷 | |
| RequestApproval | 事件 | 提出需要核准的更正、註銷或拒絕 | 提出核准申請 | |
| ApproveRequest | 事件 | 核准人核准申請 | 核准 | |
| RejectRequest | 事件 | 核准人駁回申請 | 駁回 | |
| WithdrawRequest | 事件 | 提出人撤回申請 | 撤回申請 | |
| ApprovalRequest | Entity | 一筆需要第二個人核准的更正、註銷或拒絕申請 | 核准申請 | 待使用者決定是否回到第 ② 步新增（D-13） |
| ApprovalRequest.Pending | 狀態 | 待核准 | 待核准 | |
| ApprovalRequest.Approved | 狀態 | 已核准 | 已核准 | |
| ApprovalRequest.Rejected | 狀態 | 已駁回 | 已駁回 | |
| ApprovalRequest.Withdrawn | 狀態 | 提出人已撤回 | 已撤回 | |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 |
|---|---|---|---|---|
| D-01 | 到職（StartEmployment）由人資確認，系統在約定到職日提醒（PromptStartConfirmation），不因日期到了就自動視為到職 | 約定到職日一到自動到職，沒來再取消 | 僱傭關係以開始提供勞務為成立時點（01_scope D-07）；自動到職會把當天沒來的人當成員工，和「到職前取消」混在一起（Q14、Q18） | 01_scope D-07、D-12 |
| D-02 | 需要第二個人核准的，依**效果**判斷：會改變任何投保單位的計入人數、任何人的保險適用、晚辦天數、工作許可是否發給這個雇主的更正，所有註銷與撤銷註銷，以及拒絕個資請求。其餘（例：姓名、住址、結束原因）人資直接更正、留紀錄。需要核准的走核准申請：提出（要求）→ 核准或駁回（決定）→ 執行（發生），核准前狀態不變；只有一個人的雇主由老闆本人核准，標為「自行核准」。**請使用者決定**這個分級與核准人 | 全部不需核准；列舉欄位決定要不要核准 | 中小企業常只有一位人資或老闆（PLAN.md P-05）；但這些更正和註銷一樣會改寫其他員工的判定、抹掉晚辦或拒絕當事人（X-02、X-06、X-09、X-17）；把核准與執行分開，才查得到被駁回的申請（X-18） | Q15、Q20、Q22；PLAN.md P-05；X-02、X-06、X-09、X-17、X-18 |
| D-03 | 誤登的改變狀態事件，用 AnnulEntry 註銷，被註銷的事件視為沒發生、狀態依其餘事件重新推導；不是狀態機上的轉換。三條規則：① 後面有還沒註銷、又依賴它的事件時，依相反順序一起註銷；② 由時間或條件觸發的事件不照原紀錄重播，依新的事件與日期重新評估；③ 註銷前依當時資料產生的判定，依得知時間仍查得到。註銷錯了用 RevokeAnnulment 恢復，身分不變 | 在狀態機加「更正」轉換（從終態轉出）；誤登到職改用到職後立刻離開；誤登取消就重新錄用；註銷錯了重新登錄一次 | 狀態由事件序列解釋（平台 P1），註銷後重新推導，終態不必轉出（X-01）；用離開代替會讓從沒上班的人變成「曾是員工」（Q12、Q18）；重新錄用或重新登錄會產生新的一段，原本掛著的投保、警告忽略、更正全部斷掉（Q14、X-14）；沒有規則時，殘留的後續事件與重播的時間事件會互相衝突（X-15） | 01_scope D-12；Q12、Q14、Q18；X-01、X-02、X-14、X-15 |
| D-04 | 判定各保險的適用、期限、級距，不是事件也不是狀態，是推導值（02 D-04）；系統只產生建議層的加保待辦（ProposeEnrollmentFiling），投保由人資登錄實際辦理結果才建立 | 判定結果自動建立一筆「應加保」的投保 | 投保是實際辦理後的事實（02 InsuranceEnrollment 卡）；建議不改變狀態（docs/01 原則 3） | 02 D-04；docs/01 ③ |
| D-05 | 加保流程的層：決定（DecideHire）→ 發生（StartEmployment）→ 建議（ProposeEnrollmentFiling）→ 執行（RecordInsuranceFiling、DeclareInsuredSalary）；沒有「要求」層（招募、應徵不在範圍） | 把錄用與到職併成一層 | 會停在中間：錄用後可以改期、取消（停在決定）；到職後可能晚辦或沒辦加保（停在發生），所以分開記（docs/01 ③ 判斷法） | Q02、Q03、Q14 |
| D-06 | 投保的 Terminated、投保薪資的 Superseded、契約到期在本切片走不到，狀態先列出，觸發事件由 resignation、social-insurance 定義 | 不列這些狀態，由後續切片新增 | 後續切片引用同一份狀態機，避免各自定義一套（共用核心只有一份） | docs/01 0.3 |
| D-07 | 員工撤回個資請求：記為 Completed，結果寫「當事人撤回」 | 新增 Withdrawn 狀態 | 本切片的驗收問題（Q22）只問處理紀錄；撤回很少見，用結果欄記錄即可，第 ④ 步若要算法定處理期限再看是否要拆 | Q22 |
| D-08 | 工作許可依登錄的期限由時間觸發到期；展延晚登錄可以從 Expired 回到 Valid（仍是同一筆）。免申請者依據的身分改變時，系統只提醒（ProposeAuthorizationReview），由人資決定是否登錄失效（EndWorkAuthorization），不自動判定失去工作資格 | 到期為終態；身分改變時自動失效 | 02 卡片規定展延仍是同一筆；系統自動做出「不能合法工作」的判定屬不利決定，而且法規解讀待 EQ-018（X-04） | 02 WorkAuthorization 卡、D-05；X-04；EQ-018 |
| D-09 | 補登既有員工（RegisterExistingEmployment）只用於到職日早於**這個雇主開始由系統管理的日子**的人；補登成已結束的，結束日也要早於這一天；補登的資料標為補登。這個日子目前不在 02 的 Employer 卡上，**請使用者決定**是否回到第 ② 步新增（D-13）；它的更正要核准 | 不檢查；以客戶開始使用系統的日子為界 | 補登會跳過錄用、最低工資警告與到職確認，可能被拿來繞過流程（X-07）；客戶之後才併購或新增的雇主，員工到職早於雇主納入的日子、但晚於客戶開始使用的日子，以客戶的日子為界會逼人用假的錄用（X-21）。這裡的界線是「錄用有沒有在系統中發生」，和 PLAN.md D-33 的判定界線（有沒有規則版本）是兩件事 | X-07、X-21；02 D-12；PLAN.md D-33 |
| D-10 | 所有登錄事實的事件都記「得知」時間，有生效日的同時記「生效」；作廢的建議（加保待辦等）保留，並記錄它依據的資料與規則版本 | 只記發生時間；建議作廢就刪除 | Q15 要查「更正前的判定」、Q13 要查「當時依哪一版規則」：判定是推導值（02 D-04），要重建「當時系統知道什麼」，就要知道每筆事實何時被系統得知；補登過去的資料不會改寫當時已產生的判定（X-03、X-07）。實際的雙時間保存在第 ⑤ 步依平台 P2、P4 | Q13、Q15；X-03 |
| D-11 | 警告忽略只在被警告的值、或適用於被警告事實的規則版本與修訂改變時失效；錄用時的忽略在到職時重新評估（實際到職日可能落在新版期間）。對已判定的事實，之後才生效的新版本不影響；規則版本不在原處修改，更正是新的修訂 | 規則一換新版就讓所有忽略失效；錄用時的忽略無條件延續到僱傭關係 | 到職時的最低工資檢查依到職日當時的版本（Q13）；新版生效讓舊員工的忽略全部失效，等於用新規則改寫過去（X-05）；但錄用到到職之間跨過新版時，忽略不能延續（X-20）；原地修改版本會讓「當時依哪一版」被事後改寫（X-20）。在職期間的持續檢查（例：每月工資不低於最低工資）是另一個警告，屬 monthly-payroll | Q13、Q20；X-05、X-20 |

| D-12 | 由日期觸發的轉換（工作許可與證件到期、契約起日到達、隨其他事件連動的契約失效）是推導的；CorrectRecord 不直接改變狀態，但依更正後的日期重新推導這些轉換；時間觸發的事件也記得知時間 | 更正只改值，狀態不動 | 期限打錯而被判到期，更正後要能回到有效；否則只能登錄假的展延，歷史失真（X-16） | X-16；D-10 |
| D-13 | 兩件事需要回到已凍結的第 ② 步新增（第 0 級回頭修改），**請使用者決定**：① ApprovalRequest（核准申請）建成 Entity；② Employer 加上「開始由系統管理的日子」。在使用者決定前，本文件先寫出它們的流程，標為待決定 | ① 核准只是更正事件上的一個欄位；② 不記這個日子、補登不檢查 | ① 依六問第 0 問，申請之後有狀態要追蹤（待核准、核准、駁回、撤回），就是 Entity；只當欄位就查不到被駁回的申請（X-18）；② 見 D-09 | X-18、X-21；docs/01 ② 第 0 問 |
| D-14 | AnnulEntry 只能註銷白名單上的事件：DecideHire、RescheduleStart、CancelHire、StartEmployment、RegisterExistingEmployment、RecordEarlyDeparture、SignContract、AgreeCompensation、RecordWorkAuthorization、EndWorkAuthorization、RecordIdentityDocument、RecordInsuranceFiling、DeclareInsuredSalary、ReceiveDataSubjectRequest。不能註銷：OverrideWarning、WithdrawWarningOverride、ResolveDataSubjectRequest、ArchivePersonalData、ReleaseArchival、核准申請的事件、建議層事件、由時間或條件觸發的事件 | 寫「等」，由人判斷 | 白名單上的都是登錄現實事實的事件，登錯了要能讓它不算數；不能註銷的是對紀錄本身的決定，Q20、Q22 的軌跡不能消失，做錯了用新的相反決定處理（例：撤回忽略、解除封存）；時間觸發的事件是推導的，不需要註銷（X-19） | X-19；Q20、Q22 |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|
| X-01 | 「誤登取消」的更正走不通：錄用的終態卻有轉出、僱傭關係建立不了、契約 Voided 回不來、封存的個資沒有還原 | AI 挑錯 | 接受，已修改 | 見 D-03：新增 AnnulEntry，註銷後依其餘事件重新推導；狀態機去掉從終態轉出的更正；更正方式寫明契約回到 Signed、封存由人資解除 |
| X-02 | 「誤登到職」只處理一半（已結束、已加保、契約生效的走不到），而且一個人不需核准就能讓員工從人數門檻消失 | AI 挑錯 | 接受，已修改 | 見 D-02、D-03：註銷可用於 Active 或 Ended；已加保的提醒向保險人處理（EQ-017）；註銷需證據與核准人；新增決策流程六，影響他人的更正會通知 |
| X-03 | 多數事件沒有「得知」時間、加保待辦作廢後不保留，「更正前的判定」重建不出來 | AI 挑錯 | 接受，已修改 | 見 D-10：所有登錄事實的事件加「得知」，作廢的建議保留並記依據的版本 |
| X-04 | 工作許可到期是終態，晚登錄的展延救不回來；免申請身分由系統自動判定失效，屬不利決定 | AI 挑錯 | 接受，已修改 | 見 D-08：Expired → Valid；新增 ProposeAuthorizationReview、EndWorkAuthorization，標 EQ-018 |
| X-05 | 規則一換新版就讓舊員工的警告忽略全部失效，汙染過去 | AI 挑錯 | 接受，已修改 | 見 D-11 |
| X-06 | 實際辦理日不需證據、不需核准就能更正，晚辦的紀錄可以被抹平 | AI 挑錯 | 接受，已修改 | 見 D-02：對外事實要附回執並由核准人確認；晚辦天數消失時通知雇主 |
| X-07 | 補登既有員工可被拿來繞過錄用流程，也能回溯改寫過去的人數 | AI 挑錯 | 接受，已修改 | 見 D-09（客戶開始使用日待使用者決定是否回到 ②）、D-10（補登不改寫當時已產生的判定）；補登資料標為補登；過去日期的人數依實際發生日期計算，計入範圍待 EQ-008 |
| X-08 | 錄用時忽略的警告，到職後跟著消失或重複出現 | AI 挑錯 | 接受，已修改 | WarningOverride 說明與 StartEmployment：被警告的事實沒變時忽略延續；未處理清單同時查錄用與僱傭關係 |
| X-09 | 個資流程的漏洞：任意解除封存、請求可不登錄、沒有期限提醒、暫不封存沒紀錄、觸發來源歸類錯、Q22 的查看權限沒交代 | AI 挑錯 | 接受，已修改 | ReleaseArchival 要連到錄用、個資請求或註銷紀錄；員工可自己提出、記收到管道；新增 PromptDataSubjectRequestDeadline；暫不封存記在建議上；ProposeArchival 改為其他單位個體的變化；拒絕需核准人（D-02）；查看權限交給第 ④⑤ 步 |
| X-10 | 契約起日晚於到職日，又在起日前離開，契約會在已結束的僱傭關係上生效 | AI 挑錯 | 接受，已修改 | ContractTermStarts 前提加「僱傭關係仍為 Active」；新增 Signed → Voided（隨離開）；生效時間取起日與到職日較晚者 |
| X-11 | 到職前就提早加保在模型上記不下來；加保待辦的主體在錄用時還不存在 | AI 挑錯 | 接受，已修改 | ProposeEnrollmentFiling 主體改為 Hire 或 Employment；提早加保若 EQ-005 答「會」，要回第 ② 步改投保的關係，寫在投保狀態機說明與 EQ-005 |
| X-12 | US-D17 原本自願的員工變成強制，沒有流程；人數要依實際到職日計 | AI 挑錯 | 接受，已修改 | voluntary 是辦理當時的事實，「現在應為強制」是推導值，由 ProposeEnrollmentFiling 提醒；人數依發生日期計算（決策流程一、三） |
| X-13 | Q04、Q08、Q10、Q12、Q22 沒有任何 UC 步驟回答 | AI 挑錯 | 接受，已修改 | 03_use_cases.md 補步驟、新增 UC-15 查詢勞工名卡，並新增「驗收問題涵蓋」表 |
| X-14 | 註銷錯了「再登錄一次原事件」會建立新的一段，原本掛著的投保、警告忽略、更正全部斷掉；登錯人沒有更正方式 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-03：新增 RevokeAnnulment；更正方式加「登錯人」 |
| X-15 | 「依其餘事件重新推導」沒有定義：殘留的後續事件、重播的時間事件、錯過的時間事件、註銷前的判定 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-03 三條規則；同一人同一雇主不能同時兩段在職，交給第 ④ 步 |
| X-16 | CorrectRecord「不改變狀態」，期限打錯而被判到期的證件、許可救不回來；時間事件沒有得知時間 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-12 |
| X-17 | 核准分級用列舉欄位，結束日、雇主、出生日期、居留事由的更正會改變他人判定卻不需核准 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-02：改以效果判斷；雇主不能用更正，改走註銷後重新登錄 |
| X-18 | 需要核准的動作沒有把核准與執行分開，被駁回的申請不留痕跡 | AI 挑錯（第二輪） | 接受，已修改 | 新增核准申請的狀態機與四個事件；要建成 Entity 需回到 ②，見 D-13 |
| X-19 | AnnulEntry 能註銷的範圍寫「等」：可以抹掉警告忽略等軌跡，也不確定能否註銷整筆誤登的投保 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-14 白名單 |
| X-20 | 錄用到到職之間跨過最低工資新版，忽略照樣延續；狀態機與事件表的失效條件不一致；規則版本可原地更正 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-11；到職時重新評估，延續改為加上連結、不改原紀錄 |
| X-21 | 補登的界線用客戶開始日，後來才納入的雇主會被逼著假造錄用；補登成已結束可跳過離職流程 | AI 挑錯（第二輪） | 接受，已修改 | 見 D-09：改為雇主開始由系統管理的日子，結束日也要早於它；是否回到 ② 新增見 D-13 |
| X-22 | 加保待辦可以由人作廢且不需理由，可以把晚辦藏起來 | AI 挑錯（第二輪） | 接受，已修改 | 待辦不由人作廢，只會被新判定取代或因辦理完成而結案；雇主選擇不加自願保險時記在待辦上 |
| X-23 | 反例處理宣稱的修改有幾處沒改到：EQ-005、EQ-016 沒有問到被依賴的問題；UC-08、UC-10 的涵蓋不完整；X-08 的說明前後矛盾 | AI 挑錯（第二輪） | 接受，已修改 | 新增 EQ-017（被註銷的僱傭關係的投保）、EQ-018（身分消失後許可是否失效）；補 UC-08、UC-10；X-08 的說明改寫 |

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每個會變狀態的 Entity 都有狀態圖，沒有走不到的狀態 || 部分：12 個狀態機（含待第 ② 步新增的 ApprovalRequest，D-13），結構檢查沒有走不到的狀態、終態沒有轉出；但 InsuranceEnrollment.Terminated、InsuredSalary.Superseded 在本切片走不到，觸發事件由 resignation、social-insurance 定義（D-06）；不需要狀態機的屬性另列歷史需求 | |
| 「核准」和「發生」是分開的兩件事 || ✓ 錄用：決定錄用（決定）與到職（發生）分開，中間可以改期或取消；加保：待辦（建議）與實際辦理（執行）分開；更正與註銷：提出（要求）、核准或駁回（決定）、執行（發生）分開（D-02、D-05） | |
| 會隨時間推進的動詞（流程）都有狀態機，不只名詞 || ✓ 錄用（Hire）就是錄用到到職的流程；個資請求、核准申請、封存都有狀態機；加保流程的各層見 D-05 | |
| 新增的事件與狀態名稱已登錄在詞彙對照表 || ✓ 36 個事件、31 個狀態都已登錄（程式比對狀態機、事件表與詞彙表一致）；另登錄待新增的 ApprovalRequest | |
| 需要判斷的地方有寫出決策流程（訊號 → 證據 → 狀態 → 建議 → 決定）；系統或 AI 的建議不會直接改變狀態 || ✓ 6 個決策流程（加保、法規警告、到職確認、免申請許可、封存、影響他人的更正）；6 個建議層事件都標「不改變狀態」，程式檢查通過；加保待辦不由人作廢（X-22） | |
| 每個事件標了觸發來源；由人觸發的，標了誰有權觸發 || ✓ 四種觸發來源都有；人觸發的寫出角色（人資、核准人、員工、提出人）；需核准的動作要先有核准的申請 | |
| 每個會變狀態的東西都標了歷史需求，並註明依據哪條驗收問題 || ✓ 12 個狀態機都標了歷史需求與依據（Q03、Q06、Q07、Q10、Q13～Q20、Q22）；人的期間屬性、聯絡方式、參考資料另列（「不需要狀態機的東西」） | |
| 有寫更正方式，且沒有任何一步是直接改舊紀錄 || ✓ 值打錯用 CorrectRecord、整筆誤登用 AnnulEntry、註銷錯了用 RevokeAnnulment；原值與被註銷的事件都保留；需不需要核准依效果判斷（D-02，待使用者決定）；不能註銷的事件列白名單（D-14） | |
| 第 ① 步每個草稿 User Story，都至少被一個正式 Use Case 涵蓋 || ✓ 19 個草稿 US 都被涵蓋（03_use_cases.md 草稿涵蓋檢查）；另加「驗收問題涵蓋」表，Q01～Q22 都對到某個 UC 的步驟 | |
| 每個正式 Use Case 都註明了用到的 Entity、事件 || ✓ 15 個 UC 都有；程式比對用到的 Entity、事件都已宣告（ApprovalRequest 待第 ② 步新增），每個事件都至少被一個 UC 用到 | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
