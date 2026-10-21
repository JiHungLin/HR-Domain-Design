# 共用核心：關係

<!-- 各切片 ② 的關係
     每個項目標題列帶狀態標記：[候選]／[已驗證]／[已驗證（暫代）]；並寫「出處：<切片>（<步驟> @ <tag>）」「層：core／shared／domain」「被引用：」 -->

| 從 | 關係 | 到 | 幾對幾 | 有無期間 | 為什麼 | 狀態 | 出處 | 被引用 |
|---|---|---|---|---|---|---|---|---|
| Person | belongsToTenant（屬於客戶） | Tenant | 1 | 無 | 人的範圍是客戶內（PLAN.md D-19）；同一真實的人在不同客戶是不同的 Person | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employer | belongsToTenant（屬於客戶） | Tenant | 1 | 無 | 一個客戶可以有多個雇主 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| OrgUnit | belongsToTenant（屬於客戶） | Tenant | 1 | 無 | 組織單位屬於客戶 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| OrgUnit | partOf（隸屬於上層） | OrgUnit | 0..1 | 有 | 最上層沒有上層；改組時上層會變 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| OrgUnit | ofEmployer（屬於雇主） | Employer | 0..1 | 有 | 分公司、部門通常屬於一個雇主；集團共用的單位可以不屬於任何雇主（D-03） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employer | registeredIn（註冊於） | Jurisdiction | 1 | 無 | 雇主依某地的法律登記或存在 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuranceUnit | ofEmployer（屬於雇主） | Employer | 1 | 無 | 投保單位以雇主為投保主體（勞保就保職保#01）；一個雇主可以有多個投保單位 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkLocation | locatedIn（位於） | Jurisdiction | 1 | 無 | 指最低一層的管轄區（台灣本版只有一層） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Jurisdiction | partOf（隸屬於上層） | Jurisdiction | 0..1 | 無 | 國家沒有上層；州屬於國家、市屬於州（PLAN.md D-10） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| IdentityDocument | heldBy（屬於） | Person | 1 | 無 | 證件只屬於一個人 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| IdentityDocument | issuedBy（核發於） | Jurisdiction | 1 | 無 | 每份證件由某個管轄區核發 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkAuthorization | heldBy（屬於） | Person | 1 | 無 | 許可屬於人，不屬於僱傭關係（D-06） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkAuthorization | validIn（適用於） | Jurisdiction | 1 | 無 | 許可只在核發的管轄區有效 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkAuthorization | boundToEmployer（綁定雇主） | Employer | 0..1 | 無 | 雇主申請的聘僱許可綁定該雇主；本人申請或免申請的不綁（外國人聘僱#04） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkAuthorization | basedOnDocument（依據證件） | IdentityDocument | 0..1 | 無 | 依身分免申請許可時，依據的是居留證（例：與國人結婚的居留事由）；其他種類不需要 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Hire | ofPerson（錄用的人） | Person | 1 | 無 | 錄用一定針對一個人 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Hire | byEmployer（錄用的雇主） | Employer | 1 | 無 | 錄用一定由一個雇主決定 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employment | ofPerson（員工） | Person | 1 | 無 | 同一人離職再任時是新的一段，舊的不改（hire-employee:Q11） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employment | withEmployer（雇主） | Employer | 1 | 無 | 雇主是 Employer，不是組織單位或客戶；換雇主就是另一段僱傭關係 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employment | resultedFromHire（由錄用而來） | Hire | 0..1 | 無 | 系統上線前就到職的員工沒有錄用紀錄（D-12）；上線後的到職都有 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employment | assignedTo（隸屬組織單位） | OrgUnit | 0..1 | 有 | 小團隊沒有部門；調職時會變（internal-transfer）；組織單位有雇主時要和僱傭關係的雇主相同（第 ④ 步規則，D-03） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Employment | worksAt（工作地點） | WorkLocation | 1 | 有 | 到職時一定有工作地點；調動時會變；本版每段同時只有一個地點 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| EmploymentContract | governs（約定） | Employment | 0..1 | 無 | 到職後一定有；到職前只掛在錄用上（例：移工入境前簽約，之後取消）；一段僱傭關係可以有多份（續約） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| EmploymentContract | concludedForHire（為錄用簽訂） | Hire | 0..1 | 無 | 到職前就簽好的契約掛在錄用上，到職後同一份契約約定僱傭關係；系統上線前的員工沒有錄用（D-18） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Compensation | agreedFor（約定給） | Employment | 0..1 | 有 | 到職後一定有；本切片只有到職時的一筆 [靜態替代] | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Compensation | agreedAtHire（錄用時約定） | Hire | 0..1 | 無 | 錄用時就約定的薪資，最低工資的警告在錄用時就要能判斷（hire-employee:Q07、hire-employee:Q20，D-18） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Hire | plannedWorkLocation（預定工作地點） | WorkLocation | 0..1 | 無 | 錄用時通常已知道在哪裡工作；到職後以僱傭關係的工作地點為準 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| Hire | plannedOrgUnit（預定組織單位） | OrgUnit | 0..1 | 無 | 小團隊沒有組織單位 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuranceEnrollment | forEmployment（為哪段僱傭關係） | Employment | 1 | 無 | 投保依附在僱傭關係上；同一人換雇主就是另一段投保 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuranceEnrollment | inScheme（加入制度） | SocialInsuranceScheme | 1 | 無 | 每段投保只屬於一種制度（D-04） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuranceEnrollment | throughUnit（由投保單位辦理） | InsuranceUnit | 0..1 | 無 | 台灣的制度一定經由投保單位（第 ④ 步規則）；其他管轄區可能沒有這個概念（D-19） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| SocialInsuranceScheme | establishedBy（由…訂定） | Jurisdiction | 1 | 無 | 制度屬於一個管轄區 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuranceUnit | registeredWith（涵蓋哪些制度） | SocialInsuranceScheme | 1..* | 無 | 勞保局的投保單位涵蓋勞保、就保、職保、勞退；健保署的投保單位涵蓋健保 `[未核對]`，待 EQ-009 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| InsuredSalary | declaredFor（屬於哪段投保） | InsuranceEnrollment | 1 | 無 | 每段投保有自己的投保薪資歷史 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| DataSubjectRequest | fromPerson（當事人） | Person | 1 | 無 | 個資請求由當事人提出 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WorkAuthorization | replaces（取代） | WorkAuthorization | 0..1 | 無 | 移工轉換雇主時，新雇主的聘僱許可取代舊的；第一份許可沒有 | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WarningOverride | concernsHire（針對錄用） | Hire | 0..1 | 無 | 到職前的警告（例：錄用時約定的月薪低於最低工資）；和 concernsEmployment 至少有一個（第 ④ 步規則） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| WarningOverride | concernsEmployment（針對僱傭關係） | Employment | 0..1 | 無 | 到職後的警告；用來回答「哪些員工帶著未處理的警告」（hire-employee:Q20） | [候選] | hire-employee（② @ hire-employee/02-v1） | annual-leave-grant（② @ annual-leave-grant/02-v1） |
| PersonalDataArchival | ofPerson（封存誰的個資） | Person | 1 | 無 | 一個人可以有多次封存（例：A 公司離職封存，回任 B 公司時部分解除，之後再封存） | [候選] | hire-employee（② @ hire-employee/02-v1） | |
| LeaveType | establishedBy（由…訂定） | Jurisdiction | 0..1 | 無 | 法令訂定的假別屬於一個管轄區；之後公司自訂的假別沒有管轄區（由公司規定訂定的關係到那時再加），所以不是 1 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| CompanyPolicy | belongsToTenant（屬於客戶） | Tenant | 1 | 無 | 公司規定一定屬於某個客戶 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| CompanyPolicy | ofEmployer（屬於雇主） | Employer | 0..1 | 無 | 通常由某個雇主訂定（工作規則以雇主為單位）；同集團各雇主共用的規定可以不限雇主（同 OrgUnit 的做法，D-11） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| CompanyPolicy | concernsLeaveType（關於假別） | LeaveType | 0..1 | 無 | 特休加給、特休年度預設都針對某個假別；之後其他切片的公司規定（例：加班費倍率）不一定針對假別 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveYearAgreement | forEmployment（為哪段僱傭關係） | Employment | 1 | 無 | 約定是員工在這段僱傭關係中和雇主談的；換雇主是新的一段，要重新約定 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveYearAgreement | ofLeaveType（屬於假別） | LeaveType | 1 | 無 | 年度是對某種假約定的；這版只有特休 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | forEmployment（為哪段僱傭關係） | Employment | 1 | 無 | 特休依同一雇主的年資給，屬於一段僱傭關係；轉任或改組留用時能不能由新的一段承接，待 EQ-010（D-06） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | ofLeaveType（屬於假別） | LeaveType | 1 | 無 | 每一筆都是某一種假；兩種假共用一個額度（例：其他假別併入事假計算）由之後的切片判斷（ENTITY_SKETCH 不確定的地方） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | grantedUnderPolicy（依公司規定給予） | CompanyPolicy | 0..1 | 無 | 來源是公司規定的才有；法定的沒有（annual-leave-grant:Q04、annual-leave-grant:Q09）。依哪一版記在 `basis_rule_versions` | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | deferredFrom（遞延自） | LeaveEntitlement | 0..1 | 無 | 遞延進來的那筆指向原來的一筆；一筆原特休最多遞延出一筆（第 ④ 步規則）；補登遞延的沒有原來那筆可以指（D-05） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | deferredUnder（依遞延協商） | LeaveDeferralAgreement | 0..1 | 無 | 系統遞延進來的那筆一定有，而且只有一筆（一筆原特休只有一筆有效的協商，X-12）；補登遞延的、其他來歷的沒有（D-05） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveDeferralAgreement | forEmployment（為哪段僱傭關係） | Employment | 1 | 無 | 協商是員工在這段僱傭關係中和雇主談的 | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveDeferralAgreement | defersEntitlement（遞延哪一筆） | LeaveEntitlement | 1 | 無 | 每一筆特休延多少是雙方談定的事實（X-13），所以協商一筆對一筆；反過來一筆特休同一時間最多一筆有效的協商（第 ④ 步規則，X-12） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | appliedYearAgreement（依特休年度約定） | LeaveYearAgreement | 0..1 | 無 | 依規則給予、而且員工有個別約定時才有；和 appliedYearDefault 最多一個（第 ④ 步規則；annual-leave-grant:Q03、annual-leave-grant:Q09，D-04） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveEntitlement | appliedYearDefault（依公司預設的特休年度） | CompanyPolicy | 0..1 | 無 | 員工沒有個別約定、套用雇主預設時才有，看得出是套用預設（01_scope D-12）；只能指到事項為「特休年度預設」的規定（第 ④ 步規則）；兩者都沒有時怎麼辦是第 ④ 步的規則（EQ-002） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveConversion | convertsFrom（從哪一筆轉換） | LeaveEntitlement | 1 | 無 | 每次轉換都來自一筆請假權利；一筆可以有多次轉換（年度終結、更正差額、契約終止） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
| LeaveConversion | correctsConversion（更正哪一次轉換） | LeaveConversion | 0..1 | 無 | 更正差額才有，指回被更正的那一次；原判定沒有（D-06） | [候選] | annual-leave-grant（② @ annual-leave-grant/02-v1） | |
