# 共用核心：Entity

<!-- 各切片 ② 凍結後合併進來的 Entity 卡，欄位同切片的 Entity 卡；對應驗收問題寫成 <切片>:Qnn
     每個項目標題列帶狀態標記：[候選]／[已驗證]／[已驗證（暫代）]；並寫「出處：<切片>（<步驟> @ <tag>）」「層：core／shared／domain」「被引用：」 -->

### Tenant（客戶） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：購買並使用本產品的一個客戶；它底下的雇主、組織、人與人事資料都歸屬於它
- 身分：由系統指定編號；全平台唯一
- 何時開始：客戶開始使用本產品（簽約或開通）
- 何時結束：客戶停止使用；資料依約定保存或封存
- 不是什麼：不是雇主（Employer）——一個客戶可以有多個雇主，例如同集團的 A、B 兩家公司；不是平台帳號或授權
- 不能跟誰合併：Employer——客戶停用時所有雇主一起停，但單一雇主可以在客戶仍使用時歇業
- 主要屬性：
  - `name`（客戶名稱）
- 對應驗收問題：hire-employee:Q11（同一客戶內認出同一人）、hire-employee:Q22（個資歸屬與封存）
- 備註：建立與維護屬 org-setup，本切片以固定資料提供 [靜態替代]
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### Person（人） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：一個真實的人，在某個客戶內只有一筆；可以沒有任何僱傭關係而存在（被錄用但還沒到職、到職前取消、已離職）
- 身分：由系統指定編號；在客戶內認同一個人（PLAN.md D-31），同一個真實的人在兩家客戶是兩筆。同一客戶內再次錄用時，以身分證件號碼辨識是不是同一人（hire-employee:Q11）
- 何時開始：第一次以這個人的身分被記錄（例：被錄用）
- 何時結束：不結束；離職後個資依規定封存（D-14）
- 不是什麼：不是「員工」——員工是人在某段僱傭關係中的身分（見「不是 Entity」）；不是身分證件；不是系統使用者帳號
- 不能跟誰合併：Employment——離職後僱傭關係結束，人還在；同一人可以先後有多段僱傭關係（hire-employee:Q11）
- 主要屬性：
  - `legal_name`（姓名）
  - `gender`（性別，分類值）
  - `birth_date`（出生日期；判定 65 歲界線，hire-employee:Q06）
  - `nationalities`（國籍，可以多個，各有取得日與喪失日；hire-employee:Q06）
  - `education`（教育程度，勞工名卡項目，hire-employee:Q10）
  - `address`（住址，勞工名卡項目，hire-employee:Q10）
  - `contact`（聯絡方式；只供聯絡用，D-14）
  - `old_age_benefits_received`（已領取的老年給付：哪個制度、哪一天；台灣本版用到勞保老年給付，hire-employee:Q06）
  - `civil_registrations`（在各管轄區的戶籍或居住登記與期間：哪個管轄區、登記日、除籍日；台灣本版用到在台戶籍，美國州稅會用到居住州；hire-employee:Q06、D-05）
  - `age`（年齡）[推導]
- 對應驗收問題：hire-employee:Q01、hire-employee:Q06、hire-employee:Q10、hire-employee:Q11、hire-employee:Q22
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### IdentityDocument（身分證件） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：一份證明人的身分或居留資格的證件紀錄：國民身分證、居留證、永久居留證、護照；居留事由改變時另記一筆，即使證件實體沒有換發（D-05）
- 身分：證件種類＋核發的管轄區＋證號；居留事由改變時另記一筆（D-05），所以同一證號可以有多筆，以生效日區分
- 何時開始：證件核發日
- 何時結束：證件有效期限屆滿、被註銷或換發
- 不是什麼：不是人本身；不是工作許可（WorkAuthorization）——居留證證明可以居留，不等於可以在台工作；不是員工繳交的證件實體（不代管證件，01_scope D-20）
- 不能跟誰合併：Person——人一直在，證件會到期、換發（例：居留證每次展延就是新的一份）；WorkAuthorization——聘僱許可到期時居留證可能還有效，反之亦然
- 主要屬性：
  - `document_kind`（證件種類，分類值：國民身分證、居留證、永久居留證、護照；本版只列台灣用到的四種，之後的切片可以擴充，例：美國的社會安全號碼與駕照由 second-country-hire 補上，大陸、香港、澳門人士的證件在納入範圍時補上（01_scope D-15）。同一人可以有多份不同種類的證件，各記一筆）
  - `document_number`（證號：身分證統一編號、統一證號或護照號碼；hire-employee:Q10）
  - `valid_from`（核發日或生效日；健保從哪天起適用要看它，hire-employee:Q06）
  - `valid_until`（有效期限，沒有期限則空）
  - `residence_basis`（居留事由，分類值，只用於居留證與永久居留證：與國人結婚、與國人結婚後離婚或配偶死亡而依法繼續居留、工作、永久居留等；判定就保、勞退適用，hire-employee:Q06）
- 對應驗收問題：hire-employee:Q06、hire-employee:Q10、hire-employee:Q16
- 被引用：（無）

### Jurisdiction（司法管轄區） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：訂定勞動、社會保險、稅務規則的地區；可以分層（國家 → 州 → 市），本版只有台灣一層
- 身分：代碼（例：TW）；全平台共用的參考資料
- 何時開始：系統開始支援該地區的規則
- 何時結束：系統停止支援該地區（實務上不結束）
- 不是什麼：不是工作地點（WorkLocation）——工作地點位於某個管轄區；不是國籍；不是一套規則本身
- 不能跟誰合併：WorkLocation——一個管轄區有很多工作地點，工作地點遷移不影響管轄區
- 主要屬性：
  - `code`（代碼，例：TW）
  - `level`（層級，分類值：國家、州、市）
- 對應驗收問題：hire-employee:Q04
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### Employer（雇主） [候選]
- 出處：hire-employee（② @ hire-employee/02-v3）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：以自己名義僱用員工、發薪、負擔投保義務的主體；可以是公司、獨資或合夥商號、個人雇主（PLAN.md D-18）
- 身分：由系統指定編號；客戶內。有統一編號的以統一編號輔助辨識，個人雇主可以沒有
- 何時開始：雇主在客戶中被建立（實務上對應登記或設立）
- 何時結束：歇業、解散，或客戶停止管理它
- 不是什麼：不是客戶（Tenant）；不是組織單位（OrgUnit）——分公司、部門屬於組織單位；不是投保單位（InsuranceUnit）——同一個雇主可能有多個投保單位（D-02）
- 不能跟誰合併：Tenant（見 Tenant）；InsuranceUnit——分公司的投保單位可以先撤銷，雇主仍在（D-02）
- 主要屬性：
  - `legal_name`（名稱）
  - `employer_type`（雇主型態，分類值：公司、獨資商號、合夥、個人雇主；hire-employee:Q05）
  - `registrations`（依法辦理的登記：哪一種（公司登記、商業登記、設立稅籍、執業證照）、日期；可以多筆，個人雇主可以沒有；雇主註冊於台灣時，建立時必填（沒有也要明確登錄「無」）；職保、就保適用看它，hire-employee:Q05、D-32）
  - `registration_exempt`（是否依法免辦登記；雇主註冊於台灣時，建立時必填；會改變時保留期間；就保適用看它，hire-employee:Q05、D-32）
  - `tax_assessed_or_invoice_permit`（是否有核定課稅或統一發票購票證；雇主註冊於台灣時，建立時必填；會改變時保留期間（例：新開的店先僱人、之後才取得核定課稅）；依法免辦登記的雇主，就保適用看它，hire-employee:Q05、D-32）
  - `labor_insurance_industry_category`（勞工保險條例 §6 第 1 項屬哪一款，或不屬各款；雇主註冊於台灣時，建立時必填；會改變時保留期間；勞保是強制或可自願看它，hire-employee:Q05、D-32）
  - `system_managed_from`（這個雇主開始由系統管理的日子：之前就到職的員工用補登，之後的到職一律經過錄用；客戶之後才納入的雇主各自有自己的日子；hire-employee:Q21、D-31）
  - `labor_standards_act_applicable`（是否適用勞動基準法；會隨時間改變（例：行業之後才被指定適用），要保留期間；勞退適用看它，hire-employee:Q05、hire-employee:Q13）
  - `headcount_on(date)`（某一天的在職員工人數）[推導]：工作規則、其他國家依雇主規模分級的規則會用到（ENTITY_SKETCH「雇主規模會影響規則」）
- 對應驗收問題：hire-employee:Q01、hire-employee:Q05、hire-employee:Q12、hire-employee:Q16（工作許可是否發給這個雇主）、hire-employee:Q21（補登的界線）
- 備註：建立與維護屬 org-setup，本切片以固定資料提供 [靜態替代]
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### InsuranceUnit（投保單位） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：雇主在某個保險人（勞動部勞工保險局、衛生福利部中央健康保險署）登記、用來替員工辦理加保的單位；有自己的單位代號
- 身分：保險人＋保險人核發的單位代號
- 何時開始：向保險人申請成立投保單位
- 何時結束：投保單位註銷
- 不是什麼：不是雇主本身；不是組織單位——分公司不一定有自己的投保單位；不是保險制度
- 不能跟誰合併：Employer（見 Employer）；OrgUnit——部門改組不影響投保單位，投保單位註銷時部門也可以還在
- 主要屬性：
  - `unit_code`（保險人核發的單位代號）
  - `established_on`（成立日）
  - `insured_headcount_on(date)`（某一天依勞保人數門檻計入的人數）[推導]：hire-employee:Q12，計入範圍待 EQ-008
- 對應驗收問題：hire-employee:Q02、hire-employee:Q05、hire-employee:Q12
- 備註：分公司是否另有投保單位、員工由哪個單位加保，待 [待專家確認: EQ-009]；建立與維護屬 org-setup [靜態替代]
- 被引用：（無）

### OrgUnit（組織單位） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：客戶內部的分公司、部門、團隊等單位，可以分層；小團隊可以完全沒有
- 身分：由系統指定編號；客戶內。名稱可以重複（例：兩家分公司都有「業務部」）
- 何時開始：單位成立
- 何時結束：單位裁撤或併入其他單位
- 不是什麼：不是雇主；不是工作地點——同一部門可以分散在兩個地點；不是職位
- 不能跟誰合併：Employer——部門裁撤時雇主還在；WorkLocation——部門搬家時地點可以留給別的部門
- 主要屬性：
  - `name`（名稱）
- 對應驗收問題：hire-employee:Q01
- 備註：建立與維護屬 org-setup，本切片以固定資料提供 [靜態替代]；是否可以跨雇主見 D-03
- 被引用：（無）

### WorkLocation（工作地點） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：員工實際提供勞務的地點；用來判斷適用哪個司法管轄區的勞動規則
- 身分：由系統指定編號；客戶內
- 何時開始：地點開始被使用（例：門市開幕）
- 何時結束：地點不再使用（例：門市結束營業）
- 不是什麼：不是雇主的登記地址；不是組織單位；不是管轄區
- 不能跟誰合併：OrgUnit（見 OrgUnit）；Jurisdiction（見 Jurisdiction）
- 主要屬性：
  - `name`（名稱，例：台中門市）
  - `address`（地址）
- 對應驗收問題：hire-employee:Q04
- 備註：建立與維護屬 org-setup，本切片以固定資料提供 [靜態替代]
- 被引用：（無）

### Hire（錄用） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：雇主決定錄用某人、約定到職日，到這個人真正開始工作或錄用被取消之間的這段安排
- 身分：由系統指定編號；同一人可以被同一雇主錄用多次（例：取消後再錄用），每次是不同的一筆
- 何時開始：雇主決定錄用（例：發出錄取通知、對方接受）
- 何時結束：這個人開始提供勞務（轉成一段僱傭關係），或在到職前被取消
- 不是什麼：不是僱傭關係——到職前取消的人從來不是員工（01_scope D-07、hire-employee:Q14）；不是招募或面試（不在範圍）；不是勞動契約——但到職前簽好的契約與約定薪資可以先掛在錄用上（D-18）
- 不能跟誰合併：Employment——錄用在到職時就結束了，僱傭關係才開始；被取消的錄用不會產生僱傭關係
- 主要屬性：
  - `decided_on`（決定錄用的日期）
  - `planned_start_date`（約定的到職日；改期時保留原本的值，hire-employee:Q14）
  - `cancellation_reason`（到職前取消的原因）
  - `cancelled_on`（取消日）
  - `prior_insurance_elsewhere`（到職前原本在別處投保的說明，例：依附配偶健保、職業工會勞保；屬於這次錄用，回任時可能不同；hire-employee:Q09，處理方式待 EQ-010）
- 對應驗收問題：hire-employee:Q09、hire-employee:Q14、hire-employee:Q18（和到職後離開分得開）、hire-employee:Q20（到職前的警告）
- 備註：系統上線前就到職的員工沒有錄用紀錄（D-12）
- 被引用：（無）

### Employment（僱傭關係） [候選]
- 出處：hire-employee（② @ hire-employee/02-v4）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：一個人與一個雇主之間的一段僱傭關係，從員工開始提供勞務（到職日）起，到僱傭關係結束為止
- 身分：由系統指定編號；員工編號不是身分，因為不同時期可以重用（D-20）
- 何時開始：員工開始提供勞務的那一天（到職日，01_scope D-07）
- 何時結束：僱傭關係終止（離職的完整處理屬 resignation；本切片只記錄到職後立刻離開的結束日與原因，D-07）
- 不是什麼：不是人；不是錄用（Hire）；不是勞動契約（EmploymentContract）——同一段僱傭關係可以先後有多份契約；不是投保
- 不能跟誰合併：Person（見 Person）；Hire（見 Hire）；EmploymentContract——定期契約到期續約時，僱傭關係不中斷（D-08）
- 主要屬性：
  - `start_date`（到職日；hire-employee:Q01）
  - `employee_number`（員工編號：每段僱傭關係各自給，回任時重給、可以和以前相同；同一時間在職的員工不可重複（第 ④ 步規則，範圍待確認，見 D-20）；同一個編號在不同時期可能代表不同的人）
  - `employee_category`（員工類型，分類值；會隨時間改變，要保留期間；本版只有全職，PLAN.md D-17）
  - `probation_until`（試用期到哪一天，沒有試用期則空；hire-employee:Q08）
  - `ended_on`（僱傭關係結束日，在職中為空；hire-employee:Q18）
  - `end_reason`（結束原因，分類值；hire-employee:Q18）
  - `public_or_military_insurance_covered`（這個職務是否依法應參加公教人員保險或軍人保險，例：私立學校的專任教職員；人資登錄，會改變時保留期間；就保適用看它，D-37）
  - `historical_basis_note`（當時依據說明：既有員工補登時，到職當時依據的文字說明，例：「當時適用勞退舊制」；供人工查證，系統不依它判定；hire-employee:Q21、D-12）
  - `seniority`（年資）[推導]：本切片只由本段到職日算；承認前段年資時，以做年資合併的切片定義的「年資承認」為準（D-28）
- 對應驗收問題：hire-employee:Q01、hire-employee:Q04、hire-employee:Q08、hire-employee:Q11、hire-employee:Q12、hire-employee:Q18、hire-employee:Q21
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### EmploymentContract（勞動契約） [候選]
- 出處：hire-employee（② @ hire-employee/02-v3）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：雇主與員工約定僱傭條件的一份契約，分不定期與定期；定期契約有性質與起訖日
- 身分：由系統指定編號；續約是新的一份
- 何時開始：契約約定的生效日
- 何時結束：不定期契約隨僱傭關係結束；定期契約到期或提前終止（到期的處理屬 resignation）
- 不是什麼：不是僱傭關係；不是約定薪資（Compensation）；不是工作許可
- 不能跟誰合併：Employment（見 Employment）；WorkAuthorization——移工的契約期限沒寫時以許可期限為準，但兩者是不同的東西，許可可以展延而契約要另訂（D-09）
- 主要屬性：
  - `contract_type`（契約類型，分類值：不定期、定期；hire-employee:Q19）
  - `fixed_term_nature`（定期契約的性質，分類值：臨時性、短期性、季節性、特定性；只用於定期，hire-employee:Q19）
  - `term_start`（契約起日）
  - `term_end`（契約上寫的迄日；不定期契約、或契約沒寫期限時為空。移工契約沒寫期限時的實際期限由第 ④ 步規則推出，不存在這裡，hire-employee:Q19、D-36）
  - `in_writing`（是否為書面契約；移工必須是書面，hire-employee:Q19）
- 對應驗收問題：hire-employee:Q19
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### Compensation（約定薪資） [候選] [靜態替代]
- 出處：hire-employee（② @ hire-employee/02-v3）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：僱傭關係約定的薪資：月薪，以及每月固定給付的項目；可以在到職前隨錄用一起約定
- 身分：由系統指定編號；錄用時約定、到職後接續掛到僱傭關係上，仍是同一筆
- 何時開始：約定生效（本切片只有到職時的一筆，但卡片的結構要能有多個版本）
- 何時結束：被新的約定取代（調薪，屬 monthly-payroll）
- 不是什麼：不是實際發的薪資（薪資單）；不是投保薪資（InsuredSalary）——投保薪資是向保險人申報的級距
- 不能跟誰合併：InsuredSalary——調薪不會自動改變已申報的投保薪資，要另外申報（D-10）
- 主要屬性：
  - `effective_from`（這一版約定的生效日；試用期滿調薪時會有新的一版，由 monthly-payroll 處理）
  - `currency`（幣別；本版固定新台幣，跨國切片會用到）
  - `pay_basis`（計薪方式，分類值：月薪、時薪；本版只有月薪，PLAN.md D-17）
  - `monthly_base_salary`（約定月薪；hire-employee:Q07）
  - `fixed_monthly_allowances`（每月固定給付的項目：名稱、類別（分類值，例：伙食津貼、交通津貼、全勤獎金、職務加給、其他）、金額；規則依類別決定算不算入各種薪資基礎，哪些算入待 EQ-012；D-34）
  - `monthly_wage_total`（月薪資總額，決定投保薪資用）[推導]
- 對應驗收問題：hire-employee:Q07、hire-employee:Q17
- 備註：正式定義屬 monthly-payroll（範圍外但會用到）。本切片只建到職時的一筆，供判斷最低工資與投保薪資；monthly-payroll 定義時取代這張卡
- 被引用：（無）

### WorkAuthorization（工作許可） [候選]
- 出處：hire-employee（② @ hire-employee/02-v3）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：一個人在某個司法管轄區合法工作的依據：雇主申請的聘僱許可、本人申請的工作許可，或依身分免申請許可（例：與國人結婚且獲准居留）
- 身分：由系統指定編號；展延時即使換發新的許可文號，仍是同一筆（每一次核准各記一筆核准紀錄，D-33）；轉換雇主時取得的新聘僱許可是新的一筆，以 replaces 連到前一份
- 何時開始：許可生效日；免申請者從取得該身分起
- 何時結束：許可期限屆滿、被廢止；免申請者在身分消失時
- 不是什麼：不是居留證（IdentityDocument）；不是僱傭關係；不是勞動契約
- 不能跟誰合併：IdentityDocument（見 IdentityDocument）；Employment——轉換雇主時，舊雇主的聘僱許可結束，人和新的僱傭關係還在
- 主要屬性：
  - `authorization_basis`（依據，分類值：雇主申請的聘僱許可、本人申請的許可、依身分免申請；hire-employee:Q16）
  - `work_category`（工作類別，分類值：就業服務法 §46 第 1 項各款；免申請者為空；hire-employee:Q16、hire-employee:Q19）
  - `approvals`（每一次核准的紀錄：許可文號、核准的起日、迄日；第一次核准與每次展延各一筆，不覆蓋前一筆；免申請者沒有；hire-employee:Q16、D-33）
  - `valid_from`（免申請者取得該身分的日子；申請許可者不填，期間看 approvals）
  - `valid_until`（免申請者身分消失的日子，還在則空；申請許可者不填，期間看 approvals）
- 對應驗收問題：hire-employee:Q16、hire-employee:Q19
- 備註：申請、展延、廢止不在本切片，只記錄內容（01_scope 不做）
- 被引用：（無）

### SocialInsuranceScheme（社會保險制度） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：某個司法管轄區規定的一種強制保險或退休金提繳制度；台灣本版有勞工保險、就業保險、職業災害保險、全民健康保險、勞工退休金（新制）五種
- 身分：管轄區＋制度代碼（例：TW 的 LABOR_INSURANCE）；全平台共用的參考資料
- 何時開始：制度開始施行（例：獨立的職業災害保險 `[未核對]` 2022 年起）
- 何時結束：制度廢止或被取代
- 不是什麼：不是某個人的投保（InsuranceEnrollment）；不是保險人（勞保局、健保署）；不是一套費率或分級表（那是第 ④ 步的規則資料）
- 不能跟誰合併：InsuranceEnrollment——制度一直在，個人的投保會開始結束
- 主要屬性：
  - `code`（代碼，例：LABOR_INSURANCE）
  - `insurer`（保險人，分類值：勞保局、健保署）
  - `effective_from`（施行日；到職日早於施行日時，判定為「不適用（制度尚未施行）」，不需要規則版本；PLAN.md D-28、D-33）
- 對應驗收問題：hire-employee:Q02、hire-employee:Q05、hire-employee:Q06
- 被引用：（無）

### InsuranceEnrollment（投保） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：一段僱傭關係在某一種社會保險制度下，由某個投保單位實際辦理加保後，到退保為止的期間
- 身分：由系統指定編號；同一段僱傭關係在同一制度退保後再加保，是新的一筆
- 何時開始：雇主實際辦理加保（由人輸入實際辦理日，hire-employee:Q03）
- 何時結束：退保（屬 resignation）
- 不是什麼：不是「應不應該加保」的判定——那是推導值（見「不是 Entity」）；不是投保薪資；不是保險制度；在沒有「投保單位」概念的管轄區（例：美國）也可以存在（D-19）
- 不能跟誰合併：Employment——同一段僱傭關係有好幾種保險，各自加保、退保的日期都不同（D-04）；InsuredSalary——同一段投保中，投保薪資會調整好幾次
- 主要屬性：
  - `filed_on`（實際辦理加保的日期，由人輸入；hire-employee:Q03）
  - `voluntary`（是否為自願加保，例：未滿 5 人的雇主自願加勞保；hire-employee:Q05）
  - `effective_from`（實際生效日：保險人核定的生效日，是事實；沒有特別資訊時通常等於依實際辦理日與規則推得的日期，hire-employee:Q03）
  - `days_late`（和法定生效日差幾天）[推導]：hire-employee:Q03
- 對應驗收問題：hire-employee:Q03、hire-employee:Q05、hire-employee:Q10（勞工名卡的勞保投保日期）
- 被引用：（無）

### InsuredSalary（投保薪資） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：一段投保在某段期間向保險人申報的月投保薪資（健保稱投保金額、勞退稱月提繳工資）
- 身分：由系統指定編號；同一生效日先誤報再更正時，更正是對同一筆的修改（依第 ③ 步更正方式），不是新的一筆
- 何時開始：申報的投保薪資生效
- 何時結束：被調整後的投保薪資取代（調整屬 social-insurance），或投保結束
- 不是什麼：不是約定薪資；不是「依分級表算出來應該報哪一級」——那是推導值；不是保費
- 不能跟誰合併：InsuranceEnrollment（見 InsuranceEnrollment）；Compensation（見 Compensation）
- 主要屬性：
  - `declared_amount`（申報的月投保薪資金額；hire-employee:Q17）
  - `grade`（級距）
  - `grading_table_version`（依據的分級表版本；hire-employee:Q13、hire-employee:Q17）
  - `declared_on`（申報日）
  - `source`（來源，分類值：雇主申報、保險人逕調；勞保就保職保#19）
  - `effective_from`（生效日：保險人核定，是事實）
- 對應驗收問題：hire-employee:Q13、hire-employee:Q17
- 被引用：（無）

### WarningOverride（警告忽略紀錄） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：使用者看到某條法規或規則的警告後，仍決定照樣存檔，這個決定在它所針對的那個警告存在期間有效
- 身分：由系統指定編號；每次忽略是一筆，即使忽略的是同一條規則
- 何時開始：使用者確認忽略警告
- 何時結束：失效——它所針對的警告不再成立（資料已改正）、警告的內容改變（例：改了月薪但仍然偏低、規則換了新版本），或被撤回；紀錄本身保留。前兩種由資料推出，撤回是人的決定，要記錄誰、何時（D-27）
- 不是什麼：不是警告本身——警告是推導值；不是資料更正；不是被阻擋的錯誤（資料自相矛盾會直接阻擋，PLAN.md D-27）
- 不能跟誰合併：被警告的對象（錄用、僱傭關係）——對象之後被改正，忽略紀錄仍要保留；也不是事件「忽略警告」本身——事件只發生一次，這筆紀錄之後會失效或被撤回（D-27）
- 主要屬性：
  - `rule_ref`（被忽略的規則與版本；hire-employee:Q20）
  - `subject_ref`（針對的是哪一筆資料的哪一項，例：約定薪資的月薪）
  - `warned_value`（忽略當時被警告的值；用來判斷之後警告的內容是否已改變）
  - `overridden_by`（誰忽略的：系統使用者）
  - `overridden_at`（何時）
  - `reason`（理由，可不填）
  - `withdrawn_by`（誰撤回的：系統使用者；沒有撤回則空）
  - `withdrawn_at`（何時撤回）
- 對應驗收問題：hire-employee:Q20
- 被引用：annual-leave-grant（② @ annual-leave-grant/02-v1）

### PersonalDataArchival（個資封存） [候選]
- 出處：hire-employee（② @ hire-employee/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：對某人一部分個資的一次封存：這部分個資不再一般使用，只能依法調閱；可以部分或全部解除
- 身分：由系統指定編號
- 何時開始：封存（例：離職後保存目的消失）
- 何時結束：解除封存（例：同一客戶內回任時需要用到）或依法刪除
- 不是什麼：不是刪除；不是個資請求（當事人要求刪除是個資請求，結果可能是封存或刪除）；不是人本身的狀態——同一人的不同類別個資可以有不同的封存時間
- 不能跟誰合併：Person——人一直在，封存會開始與解除；DataSubjectRequest——封存可以不是由當事人請求而起
- 主要屬性：
  - `data_categories`（封存的個資類別，分類值：勞工名卡項目、判定保險用的身分資料、聯絡用資料等，D-14）
  - `archived_on`（封存日）
  - `archived_by`（由誰封存）
  - `released_on`（解除日）
  - `release_reason`（解除原因，例：回任）
- 對應驗收問題：hire-employee:Q22
- 被引用：（無）

### DataSubjectRequest（個資請求） [候選]
- 出處：hire-employee（② @ hire-employee/02-v3）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：core
- 定義：員工（當事人）依個人資料保護法提出的一次請求：查詢或閱覽、複製、補充或更正、停止利用、刪除
- 身分：由系統指定編號
- 何時開始：收到請求
- 何時結束：處理完成或拒絕
- 不是什麼：不是一般的資料更正（人資自己發現打錯而改，hire-employee:Q15）；不是封存（封存是人的個資的狀態）
- 不能跟誰合併：Person——一個人可以提出很多次請求，每次各自開始、結束
- 主要屬性：
  - `request_kind`（請求種類，分類值：查詢閱覽、複製、補充更正、停止利用、刪除；員工個人資料#03）
  - `received_on`（收到日期）
  - `resolved_on`（處理完成日期）
  - `outcome`（處理結果與理由，例：依業務必要不刪除）
  - `refusal_basis`（拒絕或部分拒絕的依據：引用的規則與版本或法條，例：勞工名卡離職後保存五年；只用於拒絕，D-35）
  - `extensions`（延長紀錄，每次延長一筆：延長後的處理期限、延長原因、以書面通知當事人的日期；沒有延長則空；次數不限，總日數受第 ④ 步規則限制，D-35）
- 對應驗收問題：hire-employee:Q22
- 被引用：（無）

### LeaveType（假別） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：一種假（例：台灣的特別休假），由某個管轄區的法令訂定，之後也可以由公司規定訂定
- 身分：代碼；管轄區訂定的假別全平台共用（參考資料，同 Jurisdiction 的做法，PLAN.md D-31）；公司自訂的假別之後在客戶內認同一個
- 何時開始：系統開始支援這種假（法令施行、或公司規定建立）
- 何時結束：法令廢止或公司規定停用；標「已停用」，不刪除（docs/01 0.2 第 1 級）
- 不是什麼：不是一筆請假權利（LeaveEntitlement）——假別是「哪一種假」，請假權利是某位員工某一期拿到的額度；不是公司規定（CompanyPolicy）——公司規定可以對某個假別多給，但假別本身不因此變成另一種；不是取得方式——同一個假別可能因雇主不同而一次給予或依工時累積（D-09）
- 不能跟誰合併：CompanyPolicy——同一個假別可以有好幾條公司規定，公司規定停用時假別還在；跨國的同名假（台灣特休、日本年次有給休暇）是不同管轄區的不同假別，不能合併（docs/01 ② 命名與多語對照）
- 主要屬性：
  - `code`（代碼）
  - `name`（名稱）
- 對應驗收問題：annual-leave-grant:Q01（這位員工有哪幾筆特休）
- 被引用：（無）

### CompanyPolicy（公司規定） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：shared
- 定義：客戶（或客戶底下的某個雇主）在法令允許的範圍內訂定的一條規定，例：「到職滿 1 年多給 2 天特休」「特休年度預設採曆年制」；規定的內容（多給幾天、預設哪一種年度）是規則資料，依版本保存（docs/03 P5）
- 身分：由系統指定編號；客戶內（PLAN.md D-31）。內容修改是同一條規定的新版本（版本與各版的生效日是規則資料，第 ④ 步），不是另一條
- 何時開始：規定第一次生效（`effective_from`）
- 何時結束：規定廢止（`effective_to`）；已經依它給予的特休不受影響
- 不是什麼：不是法令；不是規定的內容本身（天數、條件、版本屬第 ④ 步的規則資料）；不是某位員工和雇主的個別約定（LeaveYearAgreement）——公司規定的特休年度只是預設（01_scope D-12）
- 不能跟誰合併：LeaveYearAgreement——公司改了預設，已經個別約定的員工不跟著改；LeaveType（見 LeaveType）
- 主要屬性：
  - `name`（名稱）
  - `subject`（規定的事項，分類值：特休加給、特休年度預設；其他切片再加。同一雇主、同一假別同一天只能有一條有效的「特休年度預設」，第 ④ 步規則；D-11）
  - `source_note`（依據說明，例：工作規則第 12 條、公司公告；未滿 30 人的雇主不一定有工作規則，勞基法第 70 條，勞動契約與年資#10 `[未核對]`）
  - `effective_from`（第一次生效日；annual-leave-grant:Q10）
  - `effective_to`（廢止日，沒有廢止則空；annual-leave-grant:Q10）
- 對應驗收問題：annual-leave-grant:Q04（公司多給幾天）、annual-leave-grant:Q09（依哪一條公司規定給的）、annual-leave-grant:Q10（公司規定修改後依哪一版）
- 備註：「只能往對員工有利的方向調」的判斷（PLAN.md D-09、P-10）與適用對象（全體或某些員工類型）是第 ④ 步的規則；建立與維護的畫面不在本切片，這版以固定資料提供 [靜態替代]
- 被引用：（無）

### LeaveYearAgreement（特休年度約定） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：某位員工與雇主協商，某種假用哪一種年度計算可以休的期間（週年制或曆年制），從哪天起適用（勞基法施行細則第 24 條第 2 項：「勞工得於勞雇雙方協商之下列期間內，行使特別休假權利」，特別休假#02 `[未核對]`）
- 身分：由系統指定編號；同一段僱傭關係、同一假別，同一天只有一筆有效（第 ④ 步規則）；改用另一種是新的一筆，舊的保留
- 何時開始：約定開始適用的那天（`effective_from`）
- 何時結束：被下一筆約定取代，或僱傭關係結束
- 不是什麼：不是公司規定的預設（CompanyPolicy）——沒有個別約定時才套用預設，而且要看得出是套用的（01_scope D-12）；不是一筆特休；不是「某天適用哪一種」的結果（那是推導值，見「不是 Entity」）
- 不能跟誰合併：Employment——同一段僱傭關係可以改用另一種年度，改之前給的特休依原來的年度（annual-leave-grant:Q03、annual-leave-grant:Q14、annual-leave-grant:US-D10）；CompanyPolicy（見 CompanyPolicy）
- 主要屬性：
  - `leave_year_basis`（年度的種類，分類值：週年制、固定起始日的年度；annual-leave-grant:Q03）
  - `year_start`（固定起始日年度的起始月日；這版只有 1 月 1 日，也就是曆年制；不把 1 月 1 日寫死，之後可以支援會計年度等約定年度（01_scope D-03））
  - `effective_from`（從哪天起適用；annual-leave-grant:Q03）
  - `agreed_on`（協商的日期，由人輸入）
  - `agreement_note`（協商方式的說明，例：個別書面約定；工作規則或公司統一規定算不算協商，待 [待專家確認: EQ-002]）
- 對應驗收問題：annual-leave-grant:Q03、annual-leave-grant:Q14
- 被引用：（無）

### LeaveEntitlement（請假權利） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：某位員工在某段僱傭關係中，拿到的一筆可以休的假：多少、從哪天到哪天可以休、從哪裡來（法令或哪一條公司規定）。本切片處理台灣特休；它是權益帳（PLAN.md D-15）的單位，之後的切片從它扣用、轉換
- 身分：由系統指定編號。依規則給予的：同一段僱傭關係、同一假別、同一來源（法定，或同一條公司規定）、同一個可休期間只有一筆有效。依據改變而重新判定時，新舊怎麼對應（對得上的更正並保留更正前的內容，對不上的作廢與新增）交給第 ③ 步，不用期別寫死（annual-leave-grant:Q11，D-03，X-15）。遞延進來的：每一筆原特休最多一筆。補登的：每次登錄一筆
- 何時開始：員工取得這筆權利的那天（`acquired_on`；勞基法施行細則第 24 條第 1 項「於符合……特別休假條件時，取得特別休假之權利」，特別休假#02 `[未核對]`）；遞延進來的是原年度終結的隔天；補登的是開始由系統管理那天
- 何時結束：可休期間結束（年度終結）時判定未休的去向；僱傭關係在年度終結前結束的，交給 resignation（01_scope D-15）；重新判定後不再成立的那一期、或遞延協商撤回後的遞延進來那一筆，作廢但保留紀錄；作廢的那筆不算進任何推導值，上面已休的怎麼處理交給第 ③、④ 步（X-17）
- 不是什麼：不是剩餘額度（推導值）；不是請假申請或請假事實（annual-leave-request）；不是假別；不是轉為工資或失效的那一批（LeaveConversion）；不是遞延協商（LeaveDeferralAgreement）
- 不能跟誰合併：同一位員工的其他筆——當期的和遞延進來的、法定的和公司多給的，期間、扣用順序與終結時的處理不同（01_scope 交給第 ② 步的觀察第 1、2 點，D-01、D-02）；LeaveConversion——轉換由薪資切片引用、有自己的判定日與依據，一筆特休可能有好幾次轉換（年度終結、更正差額、之後的離職結算）
- 主要屬性：
  - `source`（來源，分類值：法定、公司規定；annual-leave-grant:Q04）
  - `origin`（怎麼來的，分類值：依規則給予、遞延進來、補登當期、補登遞延；之後依工時累積的假別再加，D-09；annual-leave-grant:Q12）
  - `period_sequence`（第幾期，依規則給予的才有；例：週年制第 1 期是滿 6 個月那一筆）
  - `seniority_tier`（依哪一級年資給的，例：滿 6 個月、滿 1 年；依規則給予的才有；annual-leave-grant:Q01）[待專家確認: EQ-002]（曆年制下一筆可能跨兩級）
  - `acquired_on`（取得日：符合特休條件、取得權利的那天；給予時依規則算出，之後凍結使用；annual-leave-grant:Q02、annual-leave-grant:Q07）[待專家確認: EQ-002]（曆年制下一筆可能對應兩次符合條件）
  - `quantity`（額度：給予、遞延進來或補登的數量；annual-leave-grant:Q01、annual-leave-grant:Q04。額度的更正是改正這一筆並保留歷史，第 ③ 步要標成需要重建當時，D-07）
  - `unit`（單位，分類值：日、小時；台灣特休依法以日計，其他假別或其他管轄區可能以小時計；由這一筆衍生的量（已休、遞延、轉換）都沿用它的單位，以小時請以日計的特休時怎麼換算交給 annual-leave-request，D-09、X-19）
  - `valid_from`（可休期間的起日；annual-leave-grant:Q01、annual-leave-grant:Q06）
  - `valid_to`（可休期間的迄日，也就是這一筆的年度終結日（勞基法施行細則第 24-1 條：「年度終結，為前條第二項期間屆滿之日」，特別休假#03 `[未核對]`）；annual-leave-grant:Q01、annual-leave-grant:Q05、annual-leave-grant:Q06）
  - `leave_year_basis`（給予時依哪一種年度；annual-leave-grant:Q03、annual-leave-grant:Q09）
  - `basis_rule_versions`（給予時依據的規則版本，每一種規則一筆：法令的天數表、公司加給規定、特休年度預設；補登的沒有，寫「無對應規則版本」（PLAN.md D-28）；annual-leave-grant:Q09、annual-leave-grant:Q10）
  - `basis_seniority`（取得日當時算出的年資，凍結使用；之後合併前段年資、扣除留停期間時，年資不再只由一個起算日決定，所以記算出的年資，不記起算日；annual-leave-grant:Q02、annual-leave-grant:Q09，D-03、X-16）
  - `basis_start_date`（給予時依據的到職日；這版年資只由它算；之後的年資依據（年資承認、留職停薪）由 seniority-recognition、leave-of-absence 加上；annual-leave-grant:Q09、annual-leave-grant:Q11）
  - `notified_on`（雇主實際告知員工排定特休的日期，由人輸入；只有依規則給予的法定特休要判定（勞基法第 38 條第 3 項，特別休假#01 `[未核對]`），補登的不判定（01_scope D-09）；annual-leave-grant:Q07）[待專家確認: EQ-002]（曆年制下可能要告知兩次）
  - `notice_due_on`（告知期限：取得日起 30 日內，特別休假#02 `[未核對]`）[推導]
  - `pre_system_used_quantity`（補登的：開始由系統管理那天以前已經休的數量，由人登錄；annual-leave-grant:Q12）
  - `registered_original_year_end`（補登遞延的：原年度的終結日，由人登錄；轉為工資時依它計算（特別休假#03 `[未核對]`）；annual-leave-grant:Q05、annual-leave-grant:Q12）
  - `used_quantity`（已休）[推導] [靜態替代]：之後由 annual-leave-request 的請假事實推出；這版以固定資料提供（01_scope「範圍外但會用到」，D-13）；補登的含 `pre_system_used_quantity`
  - `deferred_out_quantity`（遞延出去的：遞延進來、而且沒有作廢的那一筆的額度）[推導]
  - `converted_quantity`（轉為工資的：轉換對象為工資的各次轉換加總，含更正差額）[推導]
  - `expired_quantity`（失效的：轉換對象為失效的各次轉換加總；只可能用在公司規定的特休，待 [待專家確認: EQ-005]）[推導]
  - `remaining_quantity`（還可以休的）[推導]
- 對應驗收問題：annual-leave-grant:Q01、annual-leave-grant:Q02、annual-leave-grant:Q04、annual-leave-grant:Q05、annual-leave-grant:Q06、annual-leave-grant:Q07、annual-leave-grant:Q08、annual-leave-grant:Q09、annual-leave-grant:Q10、annual-leave-grant:Q11、annual-leave-grant:Q12、annual-leave-grant:Q13
- 備註：守恆式（第 ④ 步）：`quantity` ＝ `remaining_quantity` ＋ `used_quantity` ＋ `deferred_out_quantity` ＋ `converted_quantity` ＋ `expired_quantity`。PLAN.md D-15 式子裡的「調整」由轉換的更正差額表示（D-07）
- 被引用：（無）

### LeaveDeferralAgreement（遞延協商） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：員工與雇主協商，把一筆特休在年度終結時沒休完的部分，遞延到下一個年度休（勞基法第 38 條第 4 項：「年度終結未休之日數，經勞雇雙方協商遞延至次一年度實施者」，特別休假#01 `[未核對]`）
- 身分：由系統指定編號；一筆特休同一時間只有一筆有效的遞延協商（第 ④ 步規則）。之後再談（改天數、另簽一份同意書）都是這一筆的修改，保留歷史，不另立一筆（X-12）。一份書面同意涵蓋法定與公司多給的兩筆時，每一筆各記一筆協商，協商日與憑據說明相同（X-13）
- 何時開始：雙方談定（`agreed_on`）；年度終結後才補的協商算不算數，待 [待專家確認: EQ-003]
- 何時結束：不結束（歷史事實）；可以撤回，撤回要記錄誰、何時（第 ③ 步）
- 不是什麼：不是遞延進來的那一筆特休（那是協商在年度終結時產生的結果）；不是特休年度約定
- 不能跟誰合併：LeaveEntitlement——協商在年度終結前就存在，遞延進來的那一筆要到年度終結才出現；協商會修改、撤回，遞延進來的那筆已經被休或轉換；雇主負舉證責任時要拿得出協商本身與修改經過（勞基法第 38 條第 6 項，特別休假#01 `[未核對]`）
- 主要屬性：
  - `agreed_on`（協商的日期，由人輸入；annual-leave-grant:Q05）
  - `deferred_quantity`（這一筆協商遞延的額度，由人輸入；單位沿用那一筆特休；不能超過年度終結時的未休、公司多給的部分能不能延，是第 ④ 步的規則（EQ-005）；annual-leave-grant:Q05，01_scope D-06）
  - `agreement_note`（協商方式與憑據的說明，例：書面同意書）
- 對應驗收問題：annual-leave-grant:Q05、annual-leave-grant:Q06
- 被引用：（無）

### LeaveConversion（請假權利轉換） [候選]
- 出處：annual-leave-grant（② @ annual-leave-grant/02-v1）；文中的 D-nn、X-nn 指該切片 02_entities.md 的決定與反例
- 層：domain
- 定義：一筆請假權利中，有一批額度不再能休，轉成別的東西：工資，或失效（只可能用在公司規定的特休，EQ-005）；記下轉了多少、為什麼轉、依哪一天計算工資，交給薪資切片計算金額與發放（PLAN.md D-38）
- 身分：由系統指定編號；每次判定一筆。判定交給薪資切片後，發現要更正時不改那一筆，另記一筆差額指回它，並記更正原因（D-06、X-18）
- 何時開始：判定的那天（年度終結的判定；契約終止的由 resignation 判定）
- 何時結束：不結束（歷史事實）
- 不是什麼：不是請假權利本身；不是薪資單上的一行（PayItem，monthly-payroll 定義）——PayItem 會引用它；不是金額
- 不能跟誰合併：LeaveEntitlement（見 LeaveEntitlement）；PayItem——轉換是額度與工資基準日的判定，金額要等薪資切片依一日工資計算，而且可以在不同月份發；被更正的那一筆——已經交給薪資的不能改，差額要能另外發或處理（EQ-009）
- 主要屬性：
  - `reason`（原因，分類值：年度終結、契約終止；這版只判定年度終結，契約終止由 resignation 使用；annual-leave-grant:Q05、annual-leave-grant:Q06）
  - `target`（轉成什麼，分類值：工資、失效；PLAN.md D-15 預留之後的其他轉換，例：轉入另一段僱傭關係的特休，待 [待專家確認: EQ-010]）
  - `quantity`（轉換的額度：判定時算出，之後凍結使用；更正差額可以是負數，多發時怎麼處理待 [待專家確認: EQ-009]；annual-leave-grant:Q05、annual-leave-grant:Q08）
  - `determined_on`（判定日；annual-leave-grant:Q05）
  - `basis_rule_versions`（判定時依據的規則版本，例：公司規定的特休能不能過期依哪一版；annual-leave-grant:Q09、annual-leave-grant:Q10）
  - `correction_cause`（更正原因，更正差額才有；分類值：依據更正（例：到職日）、遞延協商修改或撤回、年度終結後才登錄的請假、其他；X-18）
  - `wage_basis_date`（工資計算基準日：年度終結的當期是這一筆的年度終結日；遞延進來的是原年度的終結日；契約終止的當期是契約終止日，由 resignation 使用（勞基法施行細則第 24-1 條，特別休假#03 `[未核對]`）；對象為失效的沒有。判定時依規則算出，之後凍結使用：之後到職日更正改了那一筆的年度終結日，已發的這一次仍依原來的日子，差額另依新的日子（X-14））
  - `payment_due_on`（發給期限：年度終結的是契約約定的工資給付日或年度終結後 30 日內，兩者怎麼擇一待 [待專家確認: EQ-003]；契約終止的依施行細則第 9 條，由 resignation 定義（特別休假#03 `[未核對]`）。判定時算出，之後凍結使用，雇主之後改工資給付日不影響已判定的；更正差額的期限與負數差額怎麼處理是第 ④ 步與 monthly-payroll 的規則（EQ-009，X-14））
- 對應驗收問題：annual-leave-grant:Q05、annual-leave-grant:Q06、annual-leave-grant:Q08、annual-leave-grant:Q11
- 被引用：（無）
