# 共用核心：規則、守恆式、分類值

<!-- 各切片 ④ 的內容，格式同 04_rules.md，另加「狀態」「出處」欄
     每個項目標題列帶狀態標記：[候選]／[已驗證]／[已驗證（暫代）]；並寫「出處：<切片>（<步驟> @ <tag>）」「層：core／shared／domain」「被引用：」 -->

## 規則

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 | 狀態 | 出處 |
|---|---|---|---|---|---|---|---|---|---|---|
| R01 | 到職日（`Employment.start_date`）不早於決定錄用的日期（`Hire.decided_on`） | 前提條件 | StartEmployment | 可自動判斷 | 擋下 | 業務需求（資料矛盾，inputs/shared/範圍釐清_矛盾資料阻擋.md） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R02 | 僱傭關係的結束日（`Employment.ended_on`）不早於到職日（`Employment.start_date`） | 前提條件 | RecordEarlyDeparture、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（資料矛盾，inputs/shared/範圍釐清_矛盾資料阻擋.md；01_scope D-17） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R03 | 出生日期（`Person.birth_date`）不晚於登錄當天；證件（`IdentityDocument.valid_from`、`IdentityDocument.valid_until`）、許可（`WorkAuthorization.approvals` 每一筆的起訖日）、契約（`EmploymentContract.term_start`、`EmploymentContract.term_end`）的迄日不早於起日 | 前提條件 | RecordIdentityDocument、RecordWorkAuthorization、SignContract、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（同上） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R04 | 同一人在同一雇主的各段僱傭關係，期間（`Employment.start_date` 到 `Employment.ended_on`）不重疊（不論在職或已結束） | 前提條件 | StartEmployment、RegisterExistingEmployment、RevokeAnnulment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（03_flows D-03、X-15；本步 X-11） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R05 | 同一時間在職的員工，員工編號（`Employment.employee_number`）不重複；範圍為同一雇主（D-03） | 前提條件 | StartEmployment、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-20；inputs/shared/範圍釐清_員工編號.md） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R06 | 組織單位有所屬雇主時，員工所屬組織單位的雇主要和僱傭關係的雇主相同 | 前提條件 | StartEmployment、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-03） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R07 | 經由投保單位辦理的投保：投保單位的雇主要和僱傭關係的雇主相同，投保單位要涵蓋這個保險制度；台灣的制度一定要經由投保單位 | 前提條件 | RecordInsuranceFiling、CorrectRecord | 可自動判斷 | 擋下 | 勞工保險條例 §6 以雇主為投保單位（勞保就保職保#01）；02 D-19、InsuranceUnit 的 registeredWith 關係 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R08 | 補登既有員工：到職日（`Employment.start_date`）早於這個雇主開始由系統管理的日子（`Employer.system_managed_from`）；補登成已結束的，結束日（`Employment.ended_on`）也要早於這一天 | 前提條件 | RegisterExistingEmployment | 可自動判斷 | 擋下 | 業務需求（03_flows D-09；02 D-31） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R09 | 警告忽略紀錄至少針對錄用或僱傭關係其中之一 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | 業務需求（02 WarningOverride 的關係） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R10 | 只有「提醒」類規則的警告可以忽略；「擋下」類不能忽略 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | PLAN.md D-27；inputs/shared/範圍釐清_法規警告不阻擋.md | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R11 | 約定的工資不低於到職日當時的每月最低工資（R12）；只適用於適用勞基法的雇主（`Employer.labor_standards_act_applicable`）；比較用底薪（`Compensation.monthly_base_salary`）或含每月固定給付（`Compensation.fixed_monthly_allowances`）的工資 [待專家確認: EQ-019]；約定薪資沒登錄時輸出「資料不足」（R60），不靜默跳過 | 前提條件 | DecideHire、RescheduleStart、AgreeCompensation、StartEmployment、CorrectRecord | 看條件（雇主是否適用勞基法） | 提醒 | 最低工資法 §3、§5（工資與最低工資#05、#06）；勞動基準法 §2 工資的定義（勞動契約與年資#02） | 依 R12 的版本；到職日沒有對應版本時依 R28 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R12 | 每月最低工資（依到職日選版本）：v2025：2025-01-01～2025-12-31，28,590 元；v2026：2026-01-01 起，29,500 元 | 計算 | R11 | 可自動判斷 | — | v2025：勞保局說明（勞保就保職保#08）；v2026：勞動部新聞（工資與最低工資#07，新聞寫待行政院核定，核定公告未讀到） | v2025、v2026 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R13 | 約定到職日（`Hire.planned_start_date`）過了 3 天仍未登錄到職或取消，列為未處理的警告（天數依 D-04） | 前提條件 | Hire（PromptStartConfirmation 之後） | 可自動判斷 | 提醒 | 業務需求（03_flows D-01、決策流程三） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R14 | 外國籍員工（`Person.nationalities` 沒有中華民國國籍）到職日要有有效的工作許可（`WorkAuthorization.authorization_basis` 為雇主申請或本人申請，到職日落在某一筆 `WorkAuthorization.approvals` 的期間內），或屬免申請許可的身分（R16） | 前提條件 | DecideHire、RescheduleStart、StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §43、§48、§51（外國人聘僱#01、#03、#04） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R15 | 雇主申請的聘僱許可，綁定的雇主要是這段僱傭關係的雇主 | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §43（外國人聘僱#01） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R16 | 依身分免申請許可的，只限與在台設籍國民結婚且獲准居留者（就業服務法 §48 第 1 項第 2 款）：要有依據的居留證件，到職日當天有效（`IdentityDocument.valid_from`、`IdentityDocument.valid_until`）、居留事由（`IdentityDocument.residence_basis`）為與國人結婚。永久居留、難民、與直系血親共同生活者**不是**免申請，而是本人申請許可（R58） | 前提條件 | RecordWorkAuthorization、StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §48、§51（外國人聘僱#03、#04） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R17 | 雇主申請的聘僱許可，每一次核准（`WorkAuthorization.approvals` 的每一筆）的期間不超過三年；本人申請的許可（`WorkAuthorization.authorization_basis`，就業服務法 §51）不受此限 | 前提條件 | RecordWorkAuthorization | 可自動判斷 | 提醒 | 就業服務法 §51、§52（外國人聘僱#04、#05） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R18 | 從事就業服務法 §46 第 1 項第 8～10 款工作（`WorkAuthorization.work_category`，移工）的勞動契約，要是書面（`EmploymentContract.in_writing`）的定期契約（`EmploymentContract.contract_type`） | 前提條件 | SignContract | 可自動判斷 | 提醒 | 就業服務法 §46（外國人聘僱#02） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R58 | 本人申請的許可（永久居留、難民、與直系血親共同生活者，就業服務法 §51 第 2 項）每一筆核准紀錄（`WorkAuthorization.approvals`）都要有許可文號 | 前提條件 | RecordWorkAuthorization | 可自動判斷 | 提醒 | 就業服務法 §51（外國人聘僱#04） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R59 | 移工契約的實際期限：契約有寫期限的依契約；沒寫的，[解讀: 以簽約當時有效那一次核准（`WorkAuthorization.approvals`）的迄日]為契約期限（法律直接擬制，不是警告）；推出的期限不寫回 `EmploymentContract.term_end`（02 D-36） | 判定 | EmploymentContract（SignContract） | 可自動判斷 | — | 就業服務法 §46（外國人聘僱#02） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R19 | 定期契約要標明性質（`EmploymentContract.fixed_term_nature`）（臨時性、短期性、季節性、特定性，或「依就業服務法 §46 第 3 項」）；有繼續性的工作應為不定期契約；什麼算繼續性工作 [待專家確認: EQ-021]。移工（§46 第 1 項第 8～10 款）的定期契約依特別規定，不適用本條的繼續性判斷 | 前提條件 | SignContract | 需人工判斷（是否為繼續性工作） | 提醒 | 勞動基準法 §9（勞動契約與年資#04）；就業服務法 §46（外國人聘僱#02） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R20 | 定期契約期間（`EmploymentContract.term_start` 到 `EmploymentContract.term_end`）上限：臨時性 6 個月以內；短期性可預期於 6 個月內完成；季節性 9 個月以內；特定性超過 1 年要報主管機關核備。性質為「依就業服務法 §46 第 3 項」的移工契約不適用 | 前提條件 | SignContract | 可自動判斷 | 提醒 | 勞動基準法施行細則 §6（勞動契約與年資#11） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R21 | 到職後，僱傭關係要有約定薪資，也要有至少一筆勞動契約紀錄（不定期契約可以是口頭，記為非書面） | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 業務需求（02 的關係 agreedFor、governs） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R60 | 判定或計算需要的資料沒有登錄（例：約定薪資、出生日期、國籍）時，結果輸出「資料不足」並列出缺哪一項，不輸出強制、可自願或不適用 | 判定 | R11、R22～R28、R31～R44 | 可自動判斷 | — | 業務需求（本步 X-14） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R22 | 勞保（普通事故），判定日 d：① 年滿 15 歲以上、65 歲以下（`Person.age`），受僱於勞工保險條例 §6 第 1 項各款的雇主——第 1～3 款（工廠、礦場、農林漁牧場、交通公用事業；公司、行號；新聞、文化、公益、合作事業）以**僱用 5 人以上**（`Employer.headcount_on`）為條件，第 4、5 款（政府機關與學校、受僱從事漁業生產）沒有人數條件 → 強制；② 第 1～3 款但未滿 5 人、或不屬 §6 各款的雇主（例：個人雇主） → 可自願（§8 第 1 項第 1 款）；③ 未滿 15 歲或超過 65 歲 → 不適用（§6 只涵蓋 15～65 歲；65 歲當天與已領老年給付者 [待專家確認: EQ-006]）[解讀: 未滿 15 歲受僱者在勞保普通事故沒有例外，原文摘錄沒有相關規定]；④ 外國籍員工也依 ①～③ 判定。雇主屬哪一款看 `Employer.labor_insurance_industry_category`（02 D-32）；人數以雇主或投保單位計 [待專家確認: EQ-008]；已領勞保老年給付者（`Person.old_age_benefits_received`）[待專家確認: EQ-006]；個人雇主 [待專家確認: EQ-004] | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主屬哪一款、人數、年齡） | — | 勞工保險條例 §6、§8（勞保就保職保#01、#02） | 勞工保險條例：讀取日 2026-10-05 的現行條文（全文頁修正日期 115-01-21，施行日待核對） | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v2） |
| R23 | 勞保人數門檻：判定日 d 那天的人數，依各段僱傭關係實際到職、結束的發生日期計算（不是登錄日）；在確定以投保單位計之前，先以雇主的在職人數（`Employer.headcount_on`）計算；計入與不計入的範圍 [待專家確認: EQ-008] | 計算 | Employer.headcount_on | 看條件 | — | 勞工保險條例 §6（勞保就保職保#01） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R24 | 就保，判定日 d：年滿 15 歲以上、65 歲以下（`Person.age`）的受僱者，具中華民國國籍（`Person.nationalities`），或與在台設籍國民結婚且獲准居留（`IdentityDocument.residence_basis`） → 強制；下列不適用：這個職務依法應參加公教人員保險或軍人保險者（`Employment.public_or_military_insurance_covered`，02 D-37）、已領勞保老年給付或公保養老給付者（`Person.old_age_benefits_received`）、受僱於依法免辦登記且無核定課稅（或無統一發票購票證）的雇主者（`Employer.registration_exempt`、`Employer.tax_assessed_or_invoice_permit`，02 D-32）；未滿 15 歲或超過 65 歲者（65 歲當天 [待專家確認: EQ-006]）；不具中華民國國籍、也不是與在台設籍國民結婚獲准居留者（例：以工作居留的外籍員工、取得永久居留者）。受僱於兩個以上雇主者得擇一參加 → 待人判斷，人資的決定記在加保待辦上（D-16） | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、居留事由、年齡、老年給付、雇主登記）；擇一的部分需人工判斷 | 交給人判斷（擇一的情形） | 就業保險法 §5（勞保就保職保#10） | 就業保險法：讀取日 2026-10-05 的現行條文（全文頁修正日期 111-01-12）；制度自 2003-01-01 起（勞保就保職保#09） | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v3） |
| R25 | 職保，判定日 d，沒有年齡上限、沒有人數門檻：① 受僱於領有執業證照、已依法登記、設有稅籍（`Employer.registrations`），或經核發聘僱許可（綁定這個雇主的 `WorkAuthorization.authorization_basis` 為雇主申請的聘僱許可）的雇主，年滿 15 歲以上（`Person.age`） → 強制；② 同上雇主，未滿 15 歲、依勞動基準法受僱從事工作者 → 強制（§6 第 3 項）；③ 依法不得參加公教人員保險的政府機關（構）、行政法人、公私立學校的受僱員工 → 強制（§6 第 1 項第 2 款）[解讀: 雇主是否屬此類，以 `Employer.labor_insurance_industry_category` 為第 4 款判斷]；④ 受僱於經中央主管機關公告的「第 6 條第 1 項以外雇主」→ 可自願，參加後不得中途退保（§9 第 1 項第 1 款）；公告的範圍 [待專家確認: EQ-023]；⑤ 不屬以上任何一種（例：沒有登記、稅籍、執業證照，也沒有聘僱許可的個人雇主，且不在公告範圍內）→ 不適用 [待專家確認: EQ-023] | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主登記、執業證照、聘僱許可、公告範圍） | — | 勞工職業災害保險及保護法 §6、§9（勞保就保職保#12、#25）；施行日（勞保就保職保#22） | 勞工職業災害保險及保護法：讀取日 2026-10-05、2026-10-14 的現行條文（公布日 110-04-30，2022-05-01 施行） | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v2） |
| R26 | 健保，判定日 d：本國籍（`Person.nationalities`）且在台設有戶籍（`Person.civil_registrations`）的受僱者 → 強制；在台領有居留證明文件（`IdentityDocument.document_kind`）、有一定雇主的受僱者（外國籍，或本國籍但在台沒有戶籍者）→ 強制（§9）。不適用：外國籍員工在居留證明生效日（`IdentityDocument.valid_from`）之前，從生效日起才合於投保條件；本國籍、在台沒有戶籍、也沒有居留證明者 [解讀: §8 第 1 項第 2 款要求已在臺灣地區設有戶籍，§9 要求領有居留證明文件，兩者都不符時不適用] | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、戶籍、居留證件與生效日） | — | 全民健康保險法 §8、§9（全民健康保險#02、#03） | 全民健康保險法：讀取日 2026-10-05 的現行條文 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v2） |
| R27 | 勞退，判定日 d：① 雇主適用勞基法（`Employer.labor_standards_act_applicable`）、且員工為本國籍（`Person.nationalities`）、與在台設籍國民結婚獲准居留、離婚或配偶死亡後依法繼續居留、或取得永久居留者（`IdentityDocument.residence_basis`） → 雇主強制提繳；② 依私立學校法提撥退休準備金者 → 不適用；③ 本國籍或上述外籍身分，且為實際從事勞動的雇主本人、受委任工作者、不適用勞基法的勞工 → 可自願；④ 其他（例：以工作居留的外籍員工） → 不適用，連自願提繳也不行 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（勞基法適用、國籍、居留事由） | — | 勞工退休金條例 §7（勞工退休金#01） | 勞工退休金條例：讀取日 2026-10-05 的現行條文 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R28 | 判定日早於某制度的施行日（`SocialInsuranceScheme.effective_from`） → 那一天「不適用（制度尚未施行）」；施行前就到職、到施行日仍在職的，依該制度的過渡規定從施行日起判定（例：職保施行前到職、未參加職災保險者，保險效力自職保法施行之日起算）；需要的規則版本系統裡沒有 → 「無對應規則版本」，不用現行規則代替。本條也適用於最低工資（R11）與分級表（R40～R43） | 判定 | Employment（ProposeEnrollmentFiling）、R11、R40～R43 | 可自動判斷 | — | PLAN.md D-28、D-33；02 D-12；勞工職業災害保險及保護法 §13 第 3 項（勞保就保職保#14） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R29 | 年齡（`Person.age`）以判定日 d 與出生日期（`Person.birth_date`）計算；「六十五歲以下」含不含 65 歲生日當天 [待專家確認: EQ-006]；滿 65 歲的那天是條件改變日（重新判定勞保、就保） | 計算 | Person.age | 可自動判斷 | — | 勞工保險條例 §6、就業保險法 §5（勞保就保職保#01、#10） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R30 | 適用哪個司法管轄區的勞動規則，看僱傭關係的工作地點所在的管轄區（本版只有台灣） | 判定 | Employment | 可自動判斷 | — | 業務需求（02 WorkLocation、Jurisdiction；PLAN.md D-10） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R31 | 勞保（含就保）：應辦理期限＝到職當日（`Employment.start_date`）；法定生效日＝到職當日；實際生效日＝實際辦理日（`InsuranceEnrollment.filed_on`，到職當日通知時）或實際辦理日的翌日（非到職當日通知時） | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工保險條例 §11（勞保就保職保#03）；就業保險法 §40 準用（勞保就保職保#11） | 依條文版本 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R32 | 職保：應辦理期限＝到職當日（雇主登記或設稅籍前到職者，為登記或設稅籍當日：取 `Employer.registrations` 中公司登記、商業登記、設立稅籍最早的一筆；執業證照不算，只用於 R25 的適用判定）；法定生效日＝到職當日（同上例外），不因晚辦而延後 | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工職業災害保險及保護法 §12、§13（勞保就保職保#13、#14） | 依條文版本 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R33 | 健保：應辦理期限＝合於投保條件之日起三日內；合於投保條件之日＝本國籍為到職日（`Employment.start_date`），[解讀: 外籍為到職日與居留證明生效日（`IdentityDocument.valid_from`）較晚的那天]；起算含不含當日、法定生效日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 需解釋 | — | 全民健康保險法 §15（全民健康保險#05） | 依 R26 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R34 | 勞退：應通知期限＝到職之日（`Employment.start_date`）起七日內；起算含不含當日、開始提繳日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 需解釋 | — | 勞工退休金條例 §18（勞工退休金#03） | 依 R27 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R35 | 晚辦天數（`InsuranceEnrollment.days_late`）＝實際生效日（`InsuranceEnrollment.effective_from`）− 法定生效日（不足 0 以 0 計）；只適用強制加保（`InsuranceEnrollment.voluntary` 為否；自願加保沒有法定生效日）；法定生效日待專家確認的制度不算 | 計算 | InsuranceEnrollment.days_late | 可自動判斷 | — | 由 R31～R34 推導 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R61 | 實際辦理日（`InsuranceEnrollment.filed_on`）或實際生效日（`InsuranceEnrollment.effective_from`）早於到職日（`Employment.start_date`） → 警告（提早加保，處理方式 [待專家確認: EQ-005]） | 前提條件 | RecordInsuranceFiling、CorrectRecord | 可自動判斷 | 提醒 | 業務需求（本步 X-08）；勞工保險條例 §11（勞保就保職保#03） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R36 | 應辦理期限已過，仍沒有登錄實際辦理的強制保險 → 逾期：在加保待辦標出逾期天數；不是可以忽略的警告，登錄實際辦理後結案（D-17） | 判定 | Employment（ProposeEnrollmentFiling） | 可自動判斷 | — | 由 R31～R34 推導；PLAN.md D-27 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v3） |
| R37 | 期限與生效日依到職日（`Employment.start_date`）計算；[解讀: 到職後立刻離開（`Employment.ended_on`）不影響，加保義務已發生] | 判定 | ProposeEnrollmentFiling | 可自動判斷 | — | 01_scope D-12 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R38 | 試用期（`Employment.probation_until`）不改變到職日、保險生效日與年資起算 | 判定 | Employment | 可自動判斷 | — | 勞動基準法 §84-2、施行細則 §5（勞動契約與年資#07、#08）；inputs/shared/範圍釐清_試用期.md | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R39 | 三種薪資基礎分開計算，各自計入哪些項目 [待專家確認: EQ-012]：勞保、職保用「月薪資總額」；勞退用「每月工資」；健保用「薪資所得」。月薪（`Compensation.monthly_base_salary`）之外，每月固定給付的項目依類別（`Compensation.fixed_monthly_allowances` 的類別，分類值 ALLOWANCE_CATEGORY，02 D-34）決定算不算入；類別為「其他」的項目 → 待人判斷，人資的決定記在加保待辦上（D-16） | 計算 | Compensation（投保薪資的計算基礎） | 需解釋 | — | 勞工保險條例 §14（勞保就保職保#05）；勞工職業災害保險及保護法 §17（勞保就保職保#16）；勞工退休金條例 §14（勞工退休金#02）；全民健康保險法 §20（全民健康保險#08） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v3） |
| R40 | 勞保（含就保）月投保薪資：依勞保投保薪資分級表，以「月薪資總額」（R39）對應的級距 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工保險條例 §14（勞保就保職保#05）；分級表（勞保就保職保#17） | v2026：2026-01-01 起（勞保就保職保#17）；v2025：第 1 級 28,590 元（勞保就保職保#08，全表未蒐集） | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R41 | 職保月投保薪資：依職保投保薪資分級表（21 級，下限等於基本工資），以「月薪資總額」（R39）對應的級距 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工職業災害保險及保護法 §17（勞保就保職保#16）；分級表（勞保就保職保#18） | v2026：2026-01-01 起（勞保就保職保#18）；v2025 全表未蒐集 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R42 | 勞退月提繳工資：依勞退月提繳分級表，以「每月工資」（R39）對應的級距；雇主提繳不低於每月工資 6% | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工退休金條例 §14（勞工退休金#02）；分級表（勞工退休金#05 只摘第 25 級以上；全表 62 級見 inputs/shared/勞工退休金月提繳分級表_115年1月1日.md，使用者提供） | v2026：2026-01-01 起（勞工退休金#05）；v2025 未蒐集 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v2） |
| R43 | 健保投保金額：受僱者以「薪資所得」（R39）為投保金額，依健保投保金額分級表 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 全民健康保險法 §20（全民健康保險#08）；分級表為使用者提供的檔案（inputs/shared/健保投保金額分級表_115年1月1日.md），不是公開來源 | v2026：2026-01-01 起；v2025 未蒐集 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R44 | 到職時用哪一版分級表：預設依到職日；跨年到職、隔年才辦理時依哪一天 [待專家確認: EQ-012] | 判定 | ProposeEnrollmentFiling | 需解釋 | — | 勞保就保職保#19（分級表依年度換版） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R45 | 申報的級距（`InsuredSalary.grade`）和應申報的級距不同 → 警告；比對時用那筆投保薪資自己的生效日（`InsuredSalary.effective_from`）與分級表版本（`InsuredSalary.grading_table_version`），不用現行版本；保險人逕調（`InsuredSalary.source` 為保險人逕調）的不比對 | 前提條件 | DeclareInsuredSalary、CorrectRecord | 可自動判斷 | 提醒 | 由 R40～R43 推導；勞保就保職保#19（逕調）；PLAN.md D-27 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R46 | 重大更正：更正、註銷、撤銷註銷前後，任何投保單位某日的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主有任一改變；拒絕個資請求一律算 → 通知雇主並列入重大更正清單 | 判定 | CorrectRecord、AnnulEntry、RevokeAnnulment、ResolveDataSubjectRequest | 可自動判斷 | — | 業務需求（03_flows D-02；inputs/shared/範圍釐清_更正不需核准.md） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R47 | 只能註銷白名單上的事件（03_flows D-14） | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-14） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R48 | 註銷前，後面沒有還沒註銷、又依賴它的事件；有的話依相反順序一起註銷 | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-03） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R49 | 雇主不能用更正改；要註銷原本的到職或補登，再對正確的雇主登錄 | 前提條件 | CorrectRecord | 可自動判斷 | 擋下 | 業務需求（03_flows 更正方式；02 D-03） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R50 | 實際辦理日、保險人核定的生效日、申報的投保薪資的更正，要附保險人回執或標示「無回執」 | 前提條件 | CorrectRecord、RecordInsuranceFiling | 可自動判斷 | 擋下 | 業務需求（03_flows D-02） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R51 | 警告忽略失效：被警告的值和 `WarningOverride.warned_value` 不同，或適用於被警告事實的規則版本或修訂（`WarningOverride.rule_ref`）不同；錄用時的忽略在到職時重新評估 | 判定 | LapseWarningOverride | 可自動判斷 | — | 業務需求（03_flows D-11） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R52 | 個資只供處理人事的人資，在蒐集的特定目的範圍內查看與利用；越權查看擋下（D-09）；各類個資誰可以看，第 ⑤ 步依平台 P7 落實 | 前提條件 | 查看個資（UC-14、UC-15） | 需解釋 | 擋下 | 個人資料保護法 §19、§20（員工個人資料#05、#06） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R53 | 個資請求（`DataSubjectRequest.request_kind`、`DataSubjectRequest.received_on`）的處理期限：查詢、閱覽、製給複製本，收到後 15 日內決定准駁；補充更正、停止處理利用、刪除，30 日內；延長過的以最後一筆延長紀錄的期限（`DataSubjectRequest.extensions`）為準。日數依民法：收到日不算入、從隔天起算，到末日結束；末日是休息日要不要順延、收到日以哪天為準 [待專家確認: EQ-020] | 計算 | PromptDataSubjectRequestDeadline、ExtendDataSubjectRequest | 需解釋（末日順延、收到日） | — | 個人資料保護法 §10、§11、§13（員工個人資料#08、#04、#09）；民法 §119～§122（期間計算#01～#04） | 個人資料保護法：讀取日 2026-10-14 的現行條文（全文頁修正日期 114-11-11，§13 不在尚未施行的條文中） | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R54 | [已取消: X-12] 當事人的權利不能事先約定放棄或限制：寫不出可檢查的條件，改為第 ⑤ 步的設計原則（系統不提供放棄權利的選項） | — | — | — | — | — | — | — | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R55 | 法定保存期間內不得刪除（可以封存），擋下的是「刪除保存期間內的資料類別」這個動作（`DataSubjectRequest.request_kind` 為刪除，整筆請求或部分接受中的那一部分）：① 勞工名卡的項目，保存到離職（`Employment.ended_on`）後五年；② 勞保、就保、職保、健保、勞退的加退保與投保薪資申報紀錄（InsuranceEnrollment、InsuredSalary），保存到離職後五年。被擋下的部分，拒絕的依據自動帶入本條與依據的條文版本（R62）。期間屆滿後，因勞資爭議或訴訟需要繼續保存的，交給人判斷，寫在拒絕的依據。工資清冊、出勤紀錄等其他法定保存資料由 monthly-payroll、shift-attendance 等切片各自引用 | 前提條件 | ResolveDataSubjectRequest（刪除） | 可自動判斷（期間屆滿後的爭議保留需人工判斷） | 擋下（D-09） | 勞動基準法 §7（勞動契約與年資#03）；個人資料保護法 §11 但書（員工個人資料#04）；勞工保險條例 §10、勞工職業災害保險及保護法 §21 的保存年限（使用者提供的資料，inputs/shared/員工資料法定保存年限與拒絕刪除.md，原文未讀） | 勞動基準法：依勞動契約與年資#03 讀取日的現行條文；勞工保險條例、職保法的保存年限：使用者提供的資料（2026-10-14），原文未讀 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R56 | 到職前取消的人，保存目的消失，取消（`Hire.cancelled_on`）後 30 天產生封存建議（天數依 D-04） | 判定 | ProposeArchival | 可自動判斷 | — | 個人資料保護法 §11（員工個人資料#04） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R57 | 解除封存要連到一筆新的錄用、個資請求或註銷紀錄 | 前提條件 | ReleaseArchival | 可自動判斷 | 擋下 | 業務需求（03_flows X-09） | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R62 | 拒絕或部分拒絕個資請求時，要記拒絕的依據（`DataSubjectRequest.refusal_basis`）：引用的規則與版本或法條，以及具體理由；被 R55 擋下的刪除自動帶入 | 前提條件 | ResolveDataSubjectRequest（Rejected 或部分接受） | 可自動判斷 | 提醒 | 個人資料保護法 §10 但書、§11 但書（員工個人資料#08、#04）；拒絕時說明具體理由與法律依據（inputs/shared/員工資料法定保存年限與拒絕刪除.md）；02 D-35 | — | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| R63 | 延長個資請求的處理期限：[解讀: 要在原期限內決定（原文未寫，依「延長之期間」的文意推定）]；延長後的期限不超過原期限加 15 日（查詢、閱覽、製給複製本）或加 30 日（補充更正、停止處理利用、刪除）；每次延長都要記延長原因與書面通知當事人的日期（`DataSubjectRequest.extensions` 一筆）。原文沒有限制次數，次數不限，以延長的總日數上限判斷（使用者 2026-10-14「延長次數先照法規」） | 前提條件 | ExtendDataSubjectRequest | 可自動判斷 | 提醒 | 個人資料保護法 §13（員工個人資料#09） | 同 R53 | [未核對] | [候選] | hire-employee（④ @ hire-employee/04-v1） |

## 守恆式

| 編號 | 等式 | 套用對象 | 狀態 | 出處 |
|---|---|---|---|---|

## 分類值

| 代碼 | 屬於 | 管轄區 | zh-TW | 對照備註 | 狀態 | 出處 |
|---|---|---|---|---|---|---|
| EMPLOYER_TYPE.COMPANY | EMPLOYER_TYPE | TW | 公司 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| EMPLOYER_TYPE.SOLE_PROPRIETORSHIP | EMPLOYER_TYPE | TW | 獨資商號 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| EMPLOYER_TYPE.PARTNERSHIP | EMPLOYER_TYPE | TW | 合夥 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| EMPLOYER_TYPE.INDIVIDUAL | EMPLOYER_TYPE | TW | 個人雇主 | 例：家庭聘僱家事幫手 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.LIA6_01_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 1 款（工廠、礦場、農林漁牧場、交通公用事業等） | R22；5 人門檻 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.LIA6_02_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 2 款（公司、行號） | R22；5 人門檻 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.LIA6_03_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 3 款（新聞、文化、公益、合作事業） | R22；5 人門檻 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.LIA6_04_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 4 款（政府機關、學校） | R22；沒有人數門檻 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.LIA6_05_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 5 款（受僱從事漁業生產） | R22；沒有人數門檻 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| LI_INDUSTRY.NOT_LISTED_TW | LI_INDUSTRY | TW | 不屬勞工保險條例 §6 第 1 項各款 | R22（可自願） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REGISTRATION_KIND.COMPANY_TW | REGISTRATION_KIND | TW | 公司登記 | R25、R32 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REGISTRATION_KIND.BUSINESS_TW | REGISTRATION_KIND | TW | 商業登記 | R25、R32 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REGISTRATION_KIND.TAX_REGISTRATION_TW | REGISTRATION_KIND | TW | 設立稅籍 | R25、R32 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REGISTRATION_KIND.PRACTICE_LICENSE_TW | REGISTRATION_KIND | TW | 執業證照 | R25（R32 不用） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| ALLOWANCE_CATEGORY.MEAL | ALLOWANCE_CATEGORY | — | 伙食津貼 | R39；算不算入待 EQ-012 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| ALLOWANCE_CATEGORY.TRANSPORT | ALLOWANCE_CATEGORY | — | 交通津貼 | R39 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| ALLOWANCE_CATEGORY.ATTENDANCE_BONUS | ALLOWANCE_CATEGORY | — | 全勤獎金 | R39、R11（EQ-019） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| ALLOWANCE_CATEGORY.POSITION_ALLOWANCE | ALLOWANCE_CATEGORY | — | 職務加給 | R39 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| ALLOWANCE_CATEGORY.OTHER | ALLOWANCE_CATEGORY | — | 其他 | R39；待人判斷 | [候選] | hire-employee（④ @ hire-employee/04-v3） |
| CONTRACT_TYPE.INDEFINITE | CONTRACT_TYPE | — | 不定期契約 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| CONTRACT_TYPE.FIXED_TERM | CONTRACT_TYPE | — | 定期契約 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| FIXED_TERM_NATURE.TEMPORARY_TW | FIXED_TERM_NATURE | TW | 臨時性 | R20 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| FIXED_TERM_NATURE.SHORT_TERM_TW | FIXED_TERM_NATURE | TW | 短期性 | R20 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| FIXED_TERM_NATURE.SEASONAL_TW | FIXED_TERM_NATURE | TW | 季節性 | R20 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| FIXED_TERM_NATURE.SPECIFIC_TW | FIXED_TERM_NATURE | TW | 特定性 | R20 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| FIXED_TERM_NATURE.ESA46_PARA3_TW | FIXED_TERM_NATURE | TW | 依就業服務法 §46 第 3 項（移工） | R18、R19、R20 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DOCUMENT_KIND.NATIONAL_ID_TW | DOCUMENT_KIND | TW | 國民身分證 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 居留證 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DOCUMENT_KIND.PERMANENT_RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 永久居留證 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DOCUMENT_KIND.PASSPORT | DOCUMENT_KIND | — | 護照 | 核發管轄區另記 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW | RESIDENCE_BASIS | TW | 與在台設籍國民結婚獲准居留 | R16、R24、R27 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| RESIDENCE_BASIS.CONTINUED_AFTER_DIVORCE_OR_DEATH_TW | RESIDENCE_BASIS | TW | 與國人結婚後離婚或配偶死亡而依法繼續居留 | R27 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| RESIDENCE_BASIS.EMPLOYMENT_TW | RESIDENCE_BASIS | TW | 工作 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| RESIDENCE_BASIS.PERMANENT_TW | RESIDENCE_BASIS | TW | 永久居留 | R27、R58（本人申請許可，不是免申請） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| AUTHORIZATION_BASIS.EMPLOYER_PERMIT | AUTHORIZATION_BASIS | — | 雇主申請的聘僱許可 | R15 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| AUTHORIZATION_BASIS.SELF_PERMIT | AUTHORIZATION_BASIS | — | 本人申請的許可 | R58 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| AUTHORIZATION_BASIS.EXEMPT_BY_STATUS | AUTHORIZATION_BASIS | — | 依身分免申請 | R16（只限與國人結婚獲准居留） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_01_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 1 款：專門性或技術性之工作 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_02_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 2 款：華僑或外國人經政府核准投資或設立事業之主管 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_03_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 3 款：學校教師 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_04_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 4 款：短期補習班之專任教師 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_05_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 5 款：運動教練及運動員 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_06_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 6 款：宗教、藝術及演藝工作 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_07_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 7 款：商船、工作船及其他經交通部特許船舶之船員 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_08_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 8 款：海洋漁撈工作 | R18（移工） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_09_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 9 款：家庭幫傭、機構看護及家庭看護工作 | R18（移工） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_10_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 10 款：經中央主管機關指定之工作（國家重要建設工程或經濟社會發展需要） | R18（移工） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| WORK_CATEGORY.ESA46_11_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 11 款：經中央主管機關專案核定者 | R14 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| SCHEME.LABOR_INSURANCE_TW | SCHEME | TW | 勞工保險 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| SCHEME.EMPLOYMENT_INSURANCE_TW | SCHEME | TW | 就業保險 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| SCHEME.OCCUPATIONAL_ACCIDENT_INSURANCE_TW | SCHEME | TW | 勞工職業災害保險 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| SCHEME.NATIONAL_HEALTH_INSURANCE_TW | SCHEME | TW | 全民健康保險 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| SCHEME.LABOR_PENSION_TW | SCHEME | TW | 勞工退休金（新制） | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| INSURER.BLI_TW | INSURER | TW | 勞動部勞工保險局 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| INSURER.NHIA_TW | INSURER | TW | 衛生福利部中央健康保險署 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.MANDATORY | APPLICABILITY | — | 強制 | 判定結果（R22～R28） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.VOLUNTARY | APPLICABILITY | — | 可自願 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.NOT_APPLICABLE | APPLICABILITY | — | 不適用 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.NOT_YET_IN_FORCE | APPLICABILITY | — | 不適用（制度尚未施行） | R28 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.NO_RULE_VERSION | APPLICABILITY | — | 無對應規則版本 | R28 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.INSUFFICIENT_DATA | APPLICABILITY | — | 資料不足 | R60 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| APPLICABILITY.NEEDS_DECISION | APPLICABILITY | — | 待人判斷 | R24（擇一參加）、R39（「其他」類固定給付）；D-16 | [候選] | hire-employee（④ @ hire-employee/04-v3） |
| INSURED_SALARY_SOURCE.EMPLOYER_DECLARED | INSURED_SALARY_SOURCE | — | 雇主申報 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| INSURED_SALARY_SOURCE.INSURER_ADJUSTED | INSURED_SALARY_SOURCE | — | 保險人逕調 | 勞保就保職保#19 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| END_REASON.EMPLOYEE_QUIT_EARLY | END_REASON | — | 員工到職後立刻離開 | 本切片只有到職後立刻離開；其他原因由 resignation 擴充 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| END_REASON.EMPLOYER_TERMINATED_EARLY | END_REASON | — | 雇主於到職後立刻終止 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REQUEST_KIND.ACCESS | REQUEST_KIND | — | 查詢或閱覽 | R53、R63（15 日） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REQUEST_KIND.COPY | REQUEST_KIND | — | 製給複製本 | R53、R63（15 日） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REQUEST_KIND.RECTIFY | REQUEST_KIND | — | 補充或更正 | R53、R63（30 日） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REQUEST_KIND.STOP_PROCESSING | REQUEST_KIND | — | 停止蒐集、處理或利用 | R53、R63（30 日） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| REQUEST_KIND.ERASE | REQUEST_KIND | — | 刪除 | R53、R55、R63（30 日） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DATA_CATEGORY.LABOR_ROSTER | DATA_CATEGORY | TW | 勞工名卡項目 | R55 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DATA_CATEGORY.INSURANCE_FILING | DATA_CATEGORY | TW | 加退保與投保薪資申報紀錄 | R55 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DATA_CATEGORY.INSURANCE_ELIGIBILITY | DATA_CATEGORY | — | 判定保險用的身分資料 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| DATA_CATEGORY.CONTACT | DATA_CATEGORY | — | 聯絡用資料 | | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| EMPLOYEE_CATEGORY.FULL_TIME | EMPLOYEE_CATEGORY | — | 全職 | 本版只有全職（PLAN.md D-17） | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| PAY_BASIS.MONTHLY | PAY_BASIS | — | 月薪 | 本版只有月薪 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
| JURISDICTION_LEVEL.COUNTRY | JURISDICTION_LEVEL | — | 國家 | 州、市由 second-country-hire 補上 | [候選] | hire-employee（④ @ hire-employee/04-v1） |
