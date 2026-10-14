# hire-employee ④ 規則與限制

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ④ 規則與限制 |
| 狀態 | 待檢查 |
| 版本 | （凍結後填 tag，例：hire-employee/04-v1） |
| 產出者 | AI（Claude） |
| 讀取的輸入 | 02_entities.md @ hire-employee/02-v3（回頭修改 D-32～D-36）；03_flows.md、03_use_cases.md @ hire-employee/03-v2（回頭修改 D-15～D-17）；法規與政策原文：inputs/research/勞保就保職保.md、全民健康保險.md、勞工退休金.md、工資與最低工資.md、勞動契約與年資.md、外國人聘僱.md、員工個人資料.md（皆最後確認 2026-10-05～06，未滿 6 個月）；inputs/shared/健保投保金額分級表_115年1月1日.md；PLAN.md D-27、D-28、D-33；inputs/shared/範圍釐清_法規警告不阻擋.md、範圍釐清_矛盾資料阻擋.md、範圍釐清_更正不需核准.md、範圍釐清_試用期.md、範圍釐清_擋下的範圍.md、員工資料法定保存年限與拒絕刪除.md；inputs/research/員工個人資料.md#08、#09（2026-10-14 讀取） |

<!-- 規則的「違反時」：擋下＝資料本身矛盾、紀錄可不可信的流程規則、做了就無法挽回的刪除與查看（使用者已同意，範圍釐清_矛盾資料阻擋.md、範圍釐清_擋下的範圍.md）；
     提醒＝其他法規檢查，只警告不阻擋，使用者可以忽略（OverrideWarning），PLAN.md D-27。
     判定、計算類填「—」；它們的結果是推導值，用在加保待辦與警告。 -->

## 規則
<!-- 種類：前提條件／計算／判定。判斷方式：可自動判斷／看條件／需解釋／需人工判斷
     違反時：擋下／提醒／交給人判斷／—。核對：誰，對照什麼，日期；或 [未核對]（AI 給的條號一律先標）
     編號全 repo 唯一：取 core/rules.md 與進行中切片的最大號加一 -->

### 一、資料本身的一致性（擋下）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R01 | 到職日（`Employment.start_date`）不早於決定錄用的日期（`Hire.decided_on`） | 前提條件 | StartEmployment | 可自動判斷 | 擋下 | 業務需求（資料矛盾，inputs/shared/範圍釐清_矛盾資料阻擋.md） | — | [未核對] |
| R02 | 僱傭關係的結束日（`Employment.ended_on`）不早於到職日（`Employment.start_date`） | 前提條件 | RecordEarlyDeparture、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（資料矛盾，inputs/shared/範圍釐清_矛盾資料阻擋.md；01_scope D-17） | — | [未核對] |
| R03 | 出生日期（`Person.birth_date`）不晚於登錄當天；證件（`IdentityDocument.valid_from`、`IdentityDocument.valid_until`）、許可（`WorkAuthorization.approvals` 每一筆的起訖日）、契約（`EmploymentContract.term_start`、`EmploymentContract.term_end`）的迄日不早於起日 | 前提條件 | RecordIdentityDocument、RecordWorkAuthorization、SignContract、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（同上） | — | [未核對] |
| R04 | 同一人在同一雇主的各段僱傭關係，期間（`Employment.start_date` 到 `Employment.ended_on`）不重疊（不論在職或已結束） | 前提條件 | StartEmployment、RegisterExistingEmployment、RevokeAnnulment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（03_flows D-03、X-15；本步 X-11） | — | [未核對] |
| R05 | 同一時間在職的員工，員工編號（`Employment.employee_number`）不重複；範圍為同一雇主（D-03） | 前提條件 | StartEmployment、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-20；inputs/shared/範圍釐清_員工編號.md） | — | [未核對] |
| R06 | 組織單位有所屬雇主時，員工所屬組織單位的雇主要和僱傭關係的雇主相同 | 前提條件 | StartEmployment、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-03） | — | [未核對] |
| R07 | 經由投保單位辦理的投保：投保單位的雇主要和僱傭關係的雇主相同，投保單位要涵蓋這個保險制度；台灣的制度一定要經由投保單位 | 前提條件 | RecordInsuranceFiling、CorrectRecord | 可自動判斷 | 擋下 | 勞工保險條例 §6 以雇主為投保單位（勞保就保職保#01）；02 D-19、InsuranceUnit 的 registeredWith 關係 | — | [未核對] |
| R08 | 補登既有員工：到職日（`Employment.start_date`）早於這個雇主開始由系統管理的日子（`Employer.system_managed_from`）；補登成已結束的，結束日（`Employment.ended_on`）也要早於這一天 | 前提條件 | RegisterExistingEmployment | 可自動判斷 | 擋下 | 業務需求（03_flows D-09；02 D-31） | — | [未核對] |
| R09 | 警告忽略紀錄至少針對錄用或僱傭關係其中之一 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | 業務需求（02 WarningOverride 的關係） | — | [未核對] |
| R10 | 只有「提醒」類規則的警告可以忽略；「擋下」類不能忽略 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | PLAN.md D-27；inputs/shared/範圍釐清_法規警告不阻擋.md | — | [未核對] |

### 二、錄用、到職、工作許可、勞動契約（提醒）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R11 | 約定的工資不低於到職日當時的每月最低工資（R12）；只適用於適用勞基法的雇主（`Employer.labor_standards_act_applicable`）；比較用底薪（`Compensation.monthly_base_salary`）或含每月固定給付（`Compensation.fixed_monthly_allowances`）的工資 [待專家確認: EQ-019]；約定薪資沒登錄時輸出「資料不足」（R60），不靜默跳過 | 前提條件 | DecideHire、RescheduleStart、AgreeCompensation、StartEmployment、CorrectRecord | 看條件（雇主是否適用勞基法） | 提醒 | 最低工資法 §3、§5（工資與最低工資#05、#06）；勞動基準法 §2 工資的定義（勞動契約與年資#02） | 依 R12 的版本；到職日沒有對應版本時依 R28 | [未核對] |
| R12 | 每月最低工資（依到職日選版本）：v2025：2025-01-01～2025-12-31，28,590 元；v2026：2026-01-01 起，29,500 元 | 計算 | R11 | 可自動判斷 | — | v2025：勞保局說明（勞保就保職保#08）；v2026：勞動部新聞（工資與最低工資#07，新聞寫待行政院核定，核定公告未讀到） | v2025、v2026 | [未核對] |
| R13 | 約定到職日（`Hire.planned_start_date`）過了 3 天仍未登錄到職或取消，列為未處理的警告（天數依 D-04） | 前提條件 | Hire（PromptStartConfirmation 之後） | 可自動判斷 | 提醒 | 業務需求（03_flows D-01、決策流程三） | — | [未核對] |
| R14 | 外國籍員工（`Person.nationalities` 沒有中華民國國籍）到職日要有有效的工作許可（`WorkAuthorization.authorization_basis` 為雇主申請或本人申請，到職日落在某一筆 `WorkAuthorization.approvals` 的期間內），或屬免申請許可的身分（R16） | 前提條件 | DecideHire、RescheduleStart、StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §43、§48、§51（外國人聘僱#01、#03、#04） | — | [未核對] |
| R15 | 雇主申請的聘僱許可，綁定的雇主要是這段僱傭關係的雇主 | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §43（外國人聘僱#01） | — | [未核對] |
| R16 | 依身分免申請許可的，只限與在台設籍國民結婚且獲准居留者（就業服務法 §48 第 1 項第 2 款）：要有依據的居留證件，到職日當天有效（`IdentityDocument.valid_from`、`IdentityDocument.valid_until`）、居留事由（`IdentityDocument.residence_basis`）為與國人結婚。永久居留、難民、與直系血親共同生活者**不是**免申請，而是本人申請許可（R58） | 前提條件 | RecordWorkAuthorization、StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §48、§51（外國人聘僱#03、#04） | — | [未核對] |
| R17 | 雇主申請的聘僱許可，每一次核准（`WorkAuthorization.approvals` 的每一筆）的期間不超過三年；本人申請的許可（`WorkAuthorization.authorization_basis`，就業服務法 §51）不受此限 | 前提條件 | RecordWorkAuthorization | 可自動判斷 | 提醒 | 就業服務法 §51、§52（外國人聘僱#04、#05） | — | [未核對] |
| R18 | 從事就業服務法 §46 第 1 項第 8～10 款工作（`WorkAuthorization.work_category`，移工）的勞動契約，要是書面（`EmploymentContract.in_writing`）的定期契約（`EmploymentContract.contract_type`） | 前提條件 | SignContract | 可自動判斷 | 提醒 | 就業服務法 §46（外國人聘僱#02） | — | [未核對] |
| R58 | 本人申請的許可（永久居留、難民、與直系血親共同生活者，就業服務法 §51 第 2 項）每一筆核准紀錄（`WorkAuthorization.approvals`）都要有許可文號 | 前提條件 | RecordWorkAuthorization | 可自動判斷 | 提醒 | 就業服務法 §51（外國人聘僱#04） | — | [未核對] |
| R59 | 移工契約的實際期限：契約有寫期限的依契約；沒寫的，[解讀: 以簽約當時有效那一次核准（`WorkAuthorization.approvals`）的迄日]為契約期限（法律直接擬制，不是警告）；推出的期限不寫回 `EmploymentContract.term_end`（02 D-36） | 判定 | EmploymentContract（SignContract） | 可自動判斷 | — | 就業服務法 §46（外國人聘僱#02） | — | [未核對] |
| R19 | 定期契約要標明性質（`EmploymentContract.fixed_term_nature`）（臨時性、短期性、季節性、特定性，或「依就業服務法 §46 第 3 項」）；有繼續性的工作應為不定期契約；什麼算繼續性工作 [待專家確認: EQ-021]。移工（§46 第 1 項第 8～10 款）的定期契約依特別規定，不適用本條的繼續性判斷 | 前提條件 | SignContract | 需人工判斷（是否為繼續性工作） | 提醒 | 勞動基準法 §9（勞動契約與年資#04）；就業服務法 §46（外國人聘僱#02） | — | [未核對] |
| R20 | 定期契約期間（`EmploymentContract.term_start` 到 `EmploymentContract.term_end`）上限：臨時性 6 個月以內；短期性可預期於 6 個月內完成；季節性 9 個月以內；特定性超過 1 年要報主管機關核備。性質為「依就業服務法 §46 第 3 項」的移工契約不適用 | 前提條件 | SignContract | 可自動判斷 | 提醒 | 勞動基準法施行細則 §6（勞動契約與年資#11） | — | [未核對] |
| R21 | 到職後，僱傭關係要有約定薪資，也要有至少一筆勞動契約紀錄（不定期契約可以是口頭，記為非書面） | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 業務需求（02 的關係 agreedFor、governs） | — | [未核對] |
| R60 | 判定或計算需要的資料沒有登錄（例：約定薪資、出生日期、國籍）時，結果輸出「資料不足」並列出缺哪一項，不輸出強制、可自願或不適用 | 判定 | R11、R22～R28、R31～R44 | 可自動判斷 | — | 業務需求（本步 X-14） | — | [未核對] |

### 三、各保險的適用（判定）

適用是「某一天」的狀態，不是到職時的一次性結論（本步 X-01）。以下判定都對**判定日 d** 計算：d 可以是到職日，也可以是條件改變的那一天（取得新的居留證件或永久居留、滿 65 歲、人數跨過門檻、制度施行日、雇主完成登記）；條件改變時重新判定，舊的判定依當時的資料仍查得到（03_flows D-10）。

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R22 | 勞保（普通事故），判定日 d：① 年滿 15 歲以上、65 歲以下（`Person.age`），受僱於勞工保險條例 §6 第 1 項各款的雇主——第 1～3 款（工廠、礦場、農林漁牧場、交通公用事業；公司、行號；新聞、文化、公益、合作事業）以**僱用 5 人以上**（`Employer.headcount_on`）為條件，第 4、5 款（政府機關與學校、受僱從事漁業生產）沒有人數條件 → 強制；② 第 1～3 款但未滿 5 人、或不屬 §6 各款的雇主（例：個人雇主） → 可自願（§8 第 1 項第 1 款）；③ 包含外國籍員工。雇主屬哪一款看 `Employer.labor_insurance_industry_category`（02 D-32）；人數以雇主或投保單位計 [待專家確認: EQ-008]；已領勞保老年給付者（`Person.old_age_benefits_received`）[待專家確認: EQ-006]；個人雇主 [待專家確認: EQ-004] | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主屬哪一款、人數、年齡） | — | 勞工保險條例 §6、§8（勞保就保職保#01、#02） | 勞工保險條例：讀取日 2026-10-05 的現行條文（全文頁修正日期 115-01-21，施行日待核對） | [未核對] |
| R23 | 勞保人數門檻：判定日 d 那天的人數，依各段僱傭關係實際到職、結束的發生日期計算（不是登錄日）；在確定以投保單位計之前，先以雇主的在職人數（`Employer.headcount_on`）計算；計入與不計入的範圍 [待專家確認: EQ-008] | 計算 | Employer.headcount_on | 看條件 | — | 勞工保險條例 §6（勞保就保職保#01） | — | [未核對] |
| R24 | 就保，判定日 d：年滿 15 歲以上、65 歲以下（`Person.age`）的受僱者，具中華民國國籍（`Person.nationalities`），或與在台設籍國民結婚且獲准居留（`IdentityDocument.residence_basis`） → 強制；下列不適用：依法應參加公教人員保險或軍人保險者、已領勞保老年給付或公保養老給付者（`Person.old_age_benefits_received`）、受僱於依法免辦登記且無核定課稅（或無統一發票購票證）的雇主者（`Employer.registration_exempt`、`Employer.tax_assessed_or_invoice_permit`，02 D-32）。受僱於兩個以上雇主者得擇一參加：交給人判斷，記錄選擇 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、居留事由、年齡、老年給付、雇主登記）；擇一的部分需人工判斷 | 交給人判斷（擇一的情形） | 就業保險法 §5（勞保就保職保#10） | 就業保險法：讀取日 2026-10-05 的現行條文（全文頁修正日期 111-01-12）；制度自 2003-01-01 起（勞保就保職保#09） | [未核對] |
| R25 | 職保，判定日 d：年滿 15 歲以上（`Person.age`），受僱於領有執業證照、已依法登記、設有稅籍，或經核發聘僱許可的雇主 → 強制；沒有年齡上限，也沒有人數門檻。雇主的執業證照、登記、稅籍看 `Employer.registrations`（02 D-32）；聘僱許可看是否有綁定這個雇主的工作許可 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主登記、執業證照、聘僱許可） | — | 勞工職業災害保險及保護法 §6（勞保就保職保#12） | 勞工職業災害保險及保護法：讀取日 2026-10-05 的現行條文（公布日 110-04-30，施行日待核對） | [未核對] |
| R26 | 健保，判定日 d：本國籍（`Person.nationalities`）且在台設有戶籍（`Person.civil_registrations`）的受僱者 → 強制；在台領有居留證明文件（`IdentityDocument.document_kind`）、有一定雇主的受僱者 → 強制。外籍員工到職時還沒有居留證明的，從居留證明生效日（`IdentityDocument.valid_from`）起才合於投保條件 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、戶籍、居留證件與生效日） | — | 全民健康保險法 §8、§9（全民健康保險#02、#03） | 全民健康保險法：讀取日 2026-10-05 的現行條文 | [未核對] |
| R27 | 勞退，判定日 d：① 雇主適用勞基法（`Employer.labor_standards_act_applicable`）、且員工為本國籍（`Person.nationalities`）、與在台設籍國民結婚獲准居留、離婚或配偶死亡後依法繼續居留、或取得永久居留者（`IdentityDocument.residence_basis`） → 雇主強制提繳；② 依私立學校法提撥退休準備金者 → 不適用；③ 本國籍或上述外籍身分，且為實際從事勞動的雇主本人、受委任工作者、不適用勞基法的勞工 → 可自願；④ 其他（例：以工作居留的外籍員工） → 不適用，連自願提繳也不行 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（勞基法適用、國籍、居留事由） | — | 勞工退休金條例 §7（勞工退休金#01） | 勞工退休金條例：讀取日 2026-10-05 的現行條文 | [未核對] |
| R28 | 判定日早於某制度的施行日（`SocialInsuranceScheme.effective_from`） → 那一天「不適用（制度尚未施行）」；施行前就到職、到施行日仍在職的，依該制度的過渡規定從施行日起判定（例：職保施行前到職、未參加職災保險者，保險效力自職保法施行之日起算）；需要的規則版本系統裡沒有 → 「無對應規則版本」，不用現行規則代替。本條也適用於最低工資（R11）與分級表（R40～R43） | 判定 | Employment（ProposeEnrollmentFiling）、R11、R40～R43 | 可自動判斷 | — | PLAN.md D-28、D-33；02 D-12；勞工職業災害保險及保護法 §13 第 3 項（勞保就保職保#14） | — | [未核對] |
| R29 | 年齡（`Person.age`）以判定日 d 與出生日期（`Person.birth_date`）計算；「六十五歲以下」含不含 65 歲生日當天 [待專家確認: EQ-006]；滿 65 歲的那天是條件改變日（重新判定勞保、就保） | 計算 | Person.age | 可自動判斷 | — | 勞工保險條例 §6、就業保險法 §5（勞保就保職保#01、#10） | — | [未核對] |
| R30 | 適用哪個司法管轄區的勞動規則，看僱傭關係的工作地點所在的管轄區（本版只有台灣） | 判定 | Employment | 可自動判斷 | — | 業務需求（02 WorkLocation、Jurisdiction；PLAN.md D-10） | — | [未核對] |

### 四、應辦理期限、法定生效日、晚辦（計算）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R31 | 勞保（含就保）：應辦理期限＝到職當日（`Employment.start_date`）；法定生效日＝到職當日；實際生效日＝實際辦理日（`InsuranceEnrollment.filed_on`，到職當日通知時）或實際辦理日的翌日（非到職當日通知時） | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工保險條例 §11（勞保就保職保#03）；就業保險法 §40 準用（勞保就保職保#11） | 依條文版本 | [未核對] |
| R32 | 職保：應辦理期限＝到職當日（雇主登記或設稅籍前到職者，為登記或設稅籍當日：取 `Employer.registrations` 中公司登記、商業登記、設立稅籍最早的一筆；執業證照不算，只用於 R25 的適用判定）；法定生效日＝到職當日（同上例外），不因晚辦而延後 | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工職業災害保險及保護法 §12、§13（勞保就保職保#13、#14） | 依條文版本 | [未核對] |
| R33 | 健保：應辦理期限＝合於投保條件之日起三日內；合於投保條件之日＝本國籍為到職日（`Employment.start_date`），[解讀: 外籍為到職日與居留證明生效日（`IdentityDocument.valid_from`）較晚的那天]；起算含不含當日、法定生效日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 需解釋 | — | 全民健康保險法 §15（全民健康保險#05） | 依 R26 | [未核對] |
| R34 | 勞退：應通知期限＝到職之日（`Employment.start_date`）起七日內；起算含不含當日、開始提繳日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 需解釋 | — | 勞工退休金條例 §18（勞工退休金#03） | 依 R27 | [未核對] |
| R35 | 晚辦天數（`InsuranceEnrollment.days_late`）＝實際生效日（`InsuranceEnrollment.effective_from`）− 法定生效日（不足 0 以 0 計）；只適用強制加保（`InsuranceEnrollment.voluntary` 為否；自願加保沒有法定生效日）；法定生效日待專家確認的制度不算 | 計算 | InsuranceEnrollment.days_late | 可自動判斷 | — | 由 R31～R34 推導 | — | [未核對] |
| R61 | 實際辦理日（`InsuranceEnrollment.filed_on`）或實際生效日（`InsuranceEnrollment.effective_from`）早於到職日（`Employment.start_date`） → 警告（提早加保，處理方式 [待專家確認: EQ-005]） | 前提條件 | RecordInsuranceFiling、CorrectRecord | 可自動判斷 | 提醒 | 業務需求（本步 X-08）；勞工保險條例 §11（勞保就保職保#03） | — | [未核對] |
| R36 | 應辦理期限已過，仍沒有登錄實際辦理的強制保險 → 警告（逾期未辦） | 前提條件 | Employment（ProposeEnrollmentFiling） | 可自動判斷 | 提醒 | 由 R31～R34 推導；PLAN.md D-27 | — | [未核對] |
| R37 | 期限與生效日依到職日（`Employment.start_date`）計算；[解讀: 到職後立刻離開（`Employment.ended_on`）不影響，加保義務已發生] | 判定 | ProposeEnrollmentFiling | 可自動判斷 | — | 01_scope D-12 | — | [未核對] |
| R38 | 試用期（`Employment.probation_until`）不改變到職日、保險生效日與年資起算 | 判定 | Employment | 可自動判斷 | — | 勞動基準法 §84-2、施行細則 §5（勞動契約與年資#07、#08）；inputs/shared/範圍釐清_試用期.md | — | [未核對] |

### 五、投保薪資

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R39 | 三種薪資基礎分開計算，各自計入哪些項目 [待專家確認: EQ-012]：勞保、職保用「月薪資總額」；勞退用「每月工資」；健保用「薪資所得」。月薪（`Compensation.monthly_base_salary`）之外，每月固定給付的項目依類別（`Compensation.fixed_monthly_allowances` 的類別，分類值 ALLOWANCE_CATEGORY，02 D-34）決定算不算入 | 計算 | Compensation（投保薪資的計算基礎） | 需解釋 | — | 勞工保險條例 §14（勞保就保職保#05）；勞工職業災害保險及保護法 §17（勞保就保職保#16）；勞工退休金條例 §14（勞工退休金#02）；全民健康保險法 §20（全民健康保險#08） | — | [未核對] |
| R40 | 勞保（含就保）月投保薪資：依勞保投保薪資分級表，以「月薪資總額」（R39）對應的級距 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工保險條例 §14（勞保就保職保#05）；分級表（勞保就保職保#17） | v2026：2026-01-01 起（勞保就保職保#17）；v2025：第 1 級 28,590 元（勞保就保職保#08，全表未蒐集） | [未核對] |
| R41 | 職保月投保薪資：依職保投保薪資分級表（21 級，下限等於基本工資），以「月薪資總額」（R39）對應的級距 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工職業災害保險及保護法 §17（勞保就保職保#16）；分級表（勞保就保職保#18） | v2026：2026-01-01 起（勞保就保職保#18）；v2025 全表未蒐集 | [未核對] |
| R42 | 勞退月提繳工資：依勞退月提繳分級表，以「每月工資」（R39）對應的級距；雇主提繳不低於每月工資 6% | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工退休金條例 §14（勞工退休金#02）；分級表（勞工退休金#05） | v2026：2026-01-01 起（勞工退休金#05）；v2025 未蒐集 | [未核對] |
| R43 | 健保投保金額：受僱者以「薪資所得」（R39）為投保金額，依健保投保金額分級表 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 全民健康保險法 §20（全民健康保險#08）；分級表為使用者提供的檔案（inputs/shared/健保投保金額分級表_115年1月1日.md），不是公開來源 | v2026：2026-01-01 起；v2025 未蒐集 | [未核對] |
| R44 | 到職時用哪一版分級表：預設依到職日；跨年到職、隔年才辦理時依哪一天 [待專家確認: EQ-012] | 判定 | ProposeEnrollmentFiling | 需解釋 | — | 勞保就保職保#19（分級表依年度換版） | — | [未核對] |
| R45 | 申報的級距（`InsuredSalary.grade`）和應申報的級距不同 → 警告；比對時用那筆投保薪資自己的生效日（`InsuredSalary.effective_from`）與分級表版本（`InsuredSalary.grading_table_version`），不用現行版本；保險人逕調（`InsuredSalary.source` 為保險人逕調）的不比對 | 前提條件 | DeclareInsuredSalary、CorrectRecord | 可自動判斷 | 提醒 | 由 R40～R43 推導；勞保就保職保#19（逕調）；PLAN.md D-27 | — | [未核對] |

### 六、更正、註銷、警告忽略

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R46 | 重大更正：更正、註銷、撤銷註銷前後，任何投保單位某日的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主有任一改變；拒絕個資請求一律算 → 通知雇主並列入重大更正清單 | 判定 | CorrectRecord、AnnulEntry、RevokeAnnulment、ResolveDataSubjectRequest | 可自動判斷 | — | 業務需求（03_flows D-02；inputs/shared/範圍釐清_更正不需核准.md） | — | [未核對] |
| R47 | 只能註銷白名單上的事件（03_flows D-14） | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-14） | — | [未核對] |
| R48 | 註銷前，後面沒有還沒註銷、又依賴它的事件；有的話依相反順序一起註銷 | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-03） | — | [未核對] |
| R49 | 雇主不能用更正改；要註銷原本的到職或補登，再對正確的雇主登錄 | 前提條件 | CorrectRecord | 可自動判斷 | 擋下 | 業務需求（03_flows 更正方式；02 D-03） | — | [未核對] |
| R50 | 實際辦理日、保險人核定的生效日、申報的投保薪資的更正，要附保險人回執或標示「無回執」 | 前提條件 | CorrectRecord、RecordInsuranceFiling | 可自動判斷 | 擋下 | 業務需求（03_flows D-02） | — | [未核對] |
| R51 | 警告忽略失效：被警告的值和 `WarningOverride.warned_value` 不同，或適用於被警告事實的規則版本或修訂（`WarningOverride.rule_ref`）不同；錄用時的忽略在到職時重新評估 | 判定 | LapseWarningOverride | 可自動判斷 | — | 業務需求（03_flows D-11） | — | [未核對] |

### 七、個資

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R52 | 個資只供處理人事的人資，在蒐集的特定目的範圍內查看與利用；越權查看擋下（D-09）；各類個資誰可以看，第 ⑤ 步依平台 P7 落實 | 前提條件 | 查看個資（UC-14、UC-15） | 需解釋 | 擋下 | 個人資料保護法 §19、§20（員工個人資料#05、#06） | — | [未核對] |
| R53 | 個資請求（`DataSubjectRequest.request_kind`、`DataSubjectRequest.received_on`）的處理期限：查詢、閱覽、製給複製本，收到後 15 日內決定准駁；補充更正、停止處理利用、刪除，30 日內；延長過的以最後一筆延長紀錄的期限（`DataSubjectRequest.extensions`）為準。日數依民法：收到日不算入、從隔天起算，到末日結束；末日是休息日要不要順延、收到日以哪天為準 [待專家確認: EQ-020] | 計算 | PromptDataSubjectRequestDeadline、ExtendDataSubjectRequest | 需解釋（末日順延、收到日） | — | 個人資料保護法 §10、§11、§13（員工個人資料#08、#04、#09）；民法 §119～§122（期間計算#01～#04） | 個人資料保護法：讀取日 2026-10-14 的現行條文（全文頁修正日期 114-11-11，§13 不在尚未施行的條文中） | [未核對] |
| R54 | [已取消: X-12] 當事人的權利不能事先約定放棄或限制：寫不出可檢查的條件，改為第 ⑤ 步的設計原則（系統不提供放棄權利的選項） | — | — | — | — | — | — | — |
| R55 | 法定保存期間內不得刪除（可以封存），擋下的是「刪除保存期間內的資料類別」這個動作（`DataSubjectRequest.request_kind` 為刪除，整筆請求或部分接受中的那一部分）：① 勞工名卡的項目，保存到離職（`Employment.ended_on`）後五年；② 勞保、就保、職保、健保、勞退的加退保與投保薪資申報紀錄（InsuranceEnrollment、InsuredSalary），保存到離職後五年。被擋下的部分，拒絕的依據自動帶入本條與依據的條文版本（R62）。期間屆滿後，因勞資爭議或訴訟需要繼續保存的，交給人判斷，寫在拒絕的依據。工資清冊、出勤紀錄等其他法定保存資料由 monthly-payroll、shift-attendance 等切片各自引用 | 前提條件 | ResolveDataSubjectRequest（刪除） | 可自動判斷（期間屆滿後的爭議保留需人工判斷） | 擋下（D-09） | 勞動基準法 §7（勞動契約與年資#03）；個人資料保護法 §11 但書（員工個人資料#04）；勞工保險條例 §10、勞工職業災害保險及保護法 §21 的保存年限（使用者提供的資料，inputs/shared/員工資料法定保存年限與拒絕刪除.md，原文未讀） | 勞動基準法：依勞動契約與年資#03 讀取日的現行條文；勞工保險條例、職保法的保存年限：使用者提供的資料（2026-10-14），原文未讀 | [未核對] |
| R56 | 到職前取消的人，保存目的消失，取消（`Hire.cancelled_on`）後 30 天產生封存建議（天數依 D-04） | 判定 | ProposeArchival | 可自動判斷 | — | 個人資料保護法 §11（員工個人資料#04） | — | [未核對] |
| R57 | 解除封存要連到一筆新的錄用、個資請求或註銷紀錄 | 前提條件 | ReleaseArchival | 可自動判斷 | 擋下 | 業務需求（03_flows X-09） | — | [未核對] |
| R62 | 拒絕或部分拒絕個資請求時，要記拒絕的依據（`DataSubjectRequest.refusal_basis`）：引用的規則與版本或法條，以及具體理由；被 R55 擋下的刪除自動帶入 | 前提條件 | ResolveDataSubjectRequest（Rejected 或部分接受） | 可自動判斷 | 提醒 | 個人資料保護法 §10 但書、§11 但書（員工個人資料#08、#04）；拒絕時說明具體理由與法律依據（inputs/shared/員工資料法定保存年限與拒絕刪除.md）；02 D-35 | — | [未核對] |
| R63 | 延長個資請求的處理期限：[解讀: 要在原期限內決定（原文未寫，依「延長之期間」的文意推定）]；延長後的期限不超過原期限加 15 日（查詢、閱覽、製給複製本）或加 30 日（補充更正、停止處理利用、刪除）；每次延長都要記延長原因與書面通知當事人的日期（`DataSubjectRequest.extensions` 一筆）。原文沒有限制次數，次數不限，以延長的總日數上限判斷（使用者 2026-10-14「延長次數先照法規」） | 前提條件 | ExtendDataSubjectRequest | 可自動判斷 | 提醒 | 個人資料保護法 §13（員工個人資料#09） | 同 R53 | [未核對] |

## 守恆式

本切片沒有需要對帳的數量或金額（保費、薪資的計算在 social-insurance、monthly-payroll）；不硬寫（docs/01 ④）。

| 編號 | 等式 | 套用對象 |
|---|---|---|

## 分類值

| 代碼 | 屬於 | 管轄區 | zh-TW | 對照備註 |
|---|---|---|---|---|
| EMPLOYER_TYPE.COMPANY | EMPLOYER_TYPE | TW | 公司 | |
| EMPLOYER_TYPE.SOLE_PROPRIETORSHIP | EMPLOYER_TYPE | TW | 獨資商號 | |
| EMPLOYER_TYPE.PARTNERSHIP | EMPLOYER_TYPE | TW | 合夥 | |
| EMPLOYER_TYPE.INDIVIDUAL | EMPLOYER_TYPE | TW | 個人雇主 | 例：家庭聘僱家事幫手 |
| LI_INDUSTRY.LIA6_01_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 1 款（工廠、礦場、農林漁牧場、交通公用事業等） | R22；5 人門檻 |
| LI_INDUSTRY.LIA6_02_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 2 款（公司、行號） | R22；5 人門檻 |
| LI_INDUSTRY.LIA6_03_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 3 款（新聞、文化、公益、合作事業） | R22；5 人門檻 |
| LI_INDUSTRY.LIA6_04_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 4 款（政府機關、學校） | R22；沒有人數門檻 |
| LI_INDUSTRY.LIA6_05_TW | LI_INDUSTRY | TW | 勞工保險條例 §6 第 1 項第 5 款（受僱從事漁業生產） | R22；沒有人數門檻 |
| LI_INDUSTRY.NOT_LISTED_TW | LI_INDUSTRY | TW | 不屬勞工保險條例 §6 第 1 項各款 | R22（可自願） |
| REGISTRATION_KIND.COMPANY_TW | REGISTRATION_KIND | TW | 公司登記 | R25、R32 |
| REGISTRATION_KIND.BUSINESS_TW | REGISTRATION_KIND | TW | 商業登記 | R25、R32 |
| REGISTRATION_KIND.TAX_REGISTRATION_TW | REGISTRATION_KIND | TW | 設立稅籍 | R25、R32 |
| REGISTRATION_KIND.PRACTICE_LICENSE_TW | REGISTRATION_KIND | TW | 執業證照 | R25（R32 不用） |
| ALLOWANCE_CATEGORY.MEAL | ALLOWANCE_CATEGORY | — | 伙食津貼 | R39；算不算入待 EQ-012 |
| ALLOWANCE_CATEGORY.TRANSPORT | ALLOWANCE_CATEGORY | — | 交通津貼 | R39 |
| ALLOWANCE_CATEGORY.ATTENDANCE_BONUS | ALLOWANCE_CATEGORY | — | 全勤獎金 | R39、R11（EQ-019） |
| ALLOWANCE_CATEGORY.POSITION_ALLOWANCE | ALLOWANCE_CATEGORY | — | 職務加給 | R39 |
| ALLOWANCE_CATEGORY.OTHER | ALLOWANCE_CATEGORY | — | 其他 | R39；由人判斷 |
| CONTRACT_TYPE.INDEFINITE | CONTRACT_TYPE | — | 不定期契約 | |
| CONTRACT_TYPE.FIXED_TERM | CONTRACT_TYPE | — | 定期契約 | |
| FIXED_TERM_NATURE.TEMPORARY_TW | FIXED_TERM_NATURE | TW | 臨時性 | R20 |
| FIXED_TERM_NATURE.SHORT_TERM_TW | FIXED_TERM_NATURE | TW | 短期性 | R20 |
| FIXED_TERM_NATURE.SEASONAL_TW | FIXED_TERM_NATURE | TW | 季節性 | R20 |
| FIXED_TERM_NATURE.SPECIFIC_TW | FIXED_TERM_NATURE | TW | 特定性 | R20 |
| FIXED_TERM_NATURE.ESA46_PARA3_TW | FIXED_TERM_NATURE | TW | 依就業服務法 §46 第 3 項（移工） | R18、R19、R20 |
| DOCUMENT_KIND.NATIONAL_ID_TW | DOCUMENT_KIND | TW | 國民身分證 | |
| DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 居留證 | |
| DOCUMENT_KIND.PERMANENT_RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 永久居留證 | |
| DOCUMENT_KIND.PASSPORT | DOCUMENT_KIND | — | 護照 | 核發管轄區另記 |
| RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW | RESIDENCE_BASIS | TW | 與在台設籍國民結婚獲准居留 | R16、R24、R27 |
| RESIDENCE_BASIS.CONTINUED_AFTER_DIVORCE_OR_DEATH_TW | RESIDENCE_BASIS | TW | 與國人結婚後離婚或配偶死亡而依法繼續居留 | R27 |
| RESIDENCE_BASIS.EMPLOYMENT_TW | RESIDENCE_BASIS | TW | 工作 | |
| RESIDENCE_BASIS.PERMANENT_TW | RESIDENCE_BASIS | TW | 永久居留 | R27、R58（本人申請許可，不是免申請） |
| AUTHORIZATION_BASIS.EMPLOYER_PERMIT | AUTHORIZATION_BASIS | — | 雇主申請的聘僱許可 | R15 |
| AUTHORIZATION_BASIS.SELF_PERMIT | AUTHORIZATION_BASIS | — | 本人申請的許可 | R58 |
| AUTHORIZATION_BASIS.EXEMPT_BY_STATUS | AUTHORIZATION_BASIS | — | 依身分免申請 | R16（只限與國人結婚獲准居留） |
| WORK_CATEGORY.ESA46_01_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 1 款：專門性或技術性之工作 | R14 |
| WORK_CATEGORY.ESA46_02_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 2 款：華僑或外國人經政府核准投資或設立事業之主管 | R14 |
| WORK_CATEGORY.ESA46_03_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 3 款：學校教師 | R14 |
| WORK_CATEGORY.ESA46_04_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 4 款：短期補習班之專任教師 | R14 |
| WORK_CATEGORY.ESA46_05_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 5 款：運動教練及運動員 | R14 |
| WORK_CATEGORY.ESA46_06_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 6 款：宗教、藝術及演藝工作 | R14 |
| WORK_CATEGORY.ESA46_07_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 7 款：商船、工作船及其他經交通部特許船舶之船員 | R14 |
| WORK_CATEGORY.ESA46_08_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 8 款：海洋漁撈工作 | R18（移工） |
| WORK_CATEGORY.ESA46_09_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 9 款：家庭幫傭、機構看護及家庭看護工作 | R18（移工） |
| WORK_CATEGORY.ESA46_10_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 10 款：經中央主管機關指定之工作（國家重要建設工程或經濟社會發展需要） | R18（移工） |
| WORK_CATEGORY.ESA46_11_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 11 款：經中央主管機關專案核定者 | R14 |
| SCHEME.LABOR_INSURANCE_TW | SCHEME | TW | 勞工保險 | |
| SCHEME.EMPLOYMENT_INSURANCE_TW | SCHEME | TW | 就業保險 | |
| SCHEME.OCCUPATIONAL_ACCIDENT_INSURANCE_TW | SCHEME | TW | 勞工職業災害保險 | |
| SCHEME.NATIONAL_HEALTH_INSURANCE_TW | SCHEME | TW | 全民健康保險 | |
| SCHEME.LABOR_PENSION_TW | SCHEME | TW | 勞工退休金（新制） | |
| INSURER.BLI_TW | INSURER | TW | 勞動部勞工保險局 | |
| INSURER.NHIA_TW | INSURER | TW | 衛生福利部中央健康保險署 | |
| APPLICABILITY.MANDATORY | APPLICABILITY | — | 強制 | 判定結果（R22～R28） |
| APPLICABILITY.VOLUNTARY | APPLICABILITY | — | 可自願 | |
| APPLICABILITY.NOT_APPLICABLE | APPLICABILITY | — | 不適用 | |
| APPLICABILITY.NOT_YET_IN_FORCE | APPLICABILITY | — | 不適用（制度尚未施行） | R28 |
| APPLICABILITY.NO_RULE_VERSION | APPLICABILITY | — | 無對應規則版本 | R28 |
| APPLICABILITY.INSUFFICIENT_DATA | APPLICABILITY | — | 資料不足 | R60 |
| INSURED_SALARY_SOURCE.EMPLOYER_DECLARED | INSURED_SALARY_SOURCE | — | 雇主申報 | |
| INSURED_SALARY_SOURCE.INSURER_ADJUSTED | INSURED_SALARY_SOURCE | — | 保險人逕調 | 勞保就保職保#19 |
| END_REASON.EMPLOYEE_QUIT_EARLY | END_REASON | — | 員工到職後立刻離開 | 本切片只有到職後立刻離開；其他原因由 resignation 擴充 |
| END_REASON.EMPLOYER_TERMINATED_EARLY | END_REASON | — | 雇主於到職後立刻終止 | |
| REQUEST_KIND.ACCESS | REQUEST_KIND | — | 查詢或閱覽 | R53、R63（15 日） |
| REQUEST_KIND.COPY | REQUEST_KIND | — | 製給複製本 | R53、R63（15 日） |
| REQUEST_KIND.RECTIFY | REQUEST_KIND | — | 補充或更正 | R53、R63（30 日） |
| REQUEST_KIND.STOP_PROCESSING | REQUEST_KIND | — | 停止蒐集、處理或利用 | R53、R63（30 日） |
| REQUEST_KIND.ERASE | REQUEST_KIND | — | 刪除 | R53、R55、R63（30 日） |
| DATA_CATEGORY.LABOR_ROSTER | DATA_CATEGORY | TW | 勞工名卡項目 | R55 |
| DATA_CATEGORY.INSURANCE_FILING | DATA_CATEGORY | TW | 加退保與投保薪資申報紀錄 | R55 |
| DATA_CATEGORY.INSURANCE_ELIGIBILITY | DATA_CATEGORY | — | 判定保險用的身分資料 | |
| DATA_CATEGORY.CONTACT | DATA_CATEGORY | — | 聯絡用資料 | |
| EMPLOYEE_CATEGORY.FULL_TIME | EMPLOYEE_CATEGORY | — | 全職 | 本版只有全職（PLAN.md D-17） |
| PAY_BASIS.MONTHLY | PAY_BASIS | — | 月薪 | 本版只有月薪 |
| JURISDICTION_LEVEL.COUNTRY | JURISDICTION_LEVEL | — | 國家 | 州、市由 second-country-hire 補上 |

## 回填紀錄
- 03_flows.md：33 個狀態轉換的「規則」欄回填（第一版 2026-10-14）；挑錯後調整：RescheduleStart 加 R01、R14；補登兩列加 R02、R06；SignContract 加 R59；RecordWorkAuthorization 加 R58；RecordInsuranceFiling 加 R61
- 03_use_cases.md：UC-01～UC-15 的「規則」回填；挑錯後調整：UC-01 加 R60，UC-03 加 R61，UC-04 加 R58、R59，UC-05 加 R01、R14，UC-07 加 R59，UC-11 加 R02、R06
- 回頭修改第 ③ 步（2026-10-14，03_flows D-15、D-16）：新增的 ExtendDataSubjectRequest 不改變狀態，規則 R53、R63 寫在狀態機下方的說明與 UC-14；Rejected、Completed 轉換加 R62，Rejected 拿掉 R55（R55 擋的是刪除的動作）；WorkAuthorization 新增 Valid → Valid（還有效時登錄展延）填 R03、R17、R58，晚登錄展延加 R58；ReceiveDataSubjectRequest 的 R54（已取消）改為「—」；UC-14 的規則改為 R46、R53、R55、R62、R63

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 | 提出／同意 |
|---|---|---|---|---|---|
| D-01 | 「違反時」分兩種：資料本身矛盾的（R01～R10）、流程規則（R47～R50、R57）、做了就無法挽回的兩條法規（R52、R55）擋下（D-09）；其他法規檢查（最低工資、工作許可、契約、逾期未辦、級距不符）只提醒，可以忽略並留紀錄 | 法規一律擋下 | 使用者要求系統有彈性（PLAN.md D-27）；矛盾資料阻擋已經使用者同意（inputs/shared/範圍釐清_矛盾資料阻擋.md） | PLAN.md D-27；01_scope D-17 | AI／JiHungLin（2026-10-14） |
| D-02 | 各保險的適用、期限、級距寫成判定與計算規則，結果是推導值（02 D-04），只用在加保待辦與警告；投保要人資登錄實際辦理才建立 | 判定結果直接建立投保 | 03_flows D-04 | 02 D-04；03_flows D-04 | AI／待確認 |
| D-03 | 員工編號不重複的範圍是「同一雇主」：同一客戶內兩家公司可以各自有 E001（使用者選 A，2026-10-14） | 同一客戶（集團）內都不重複 | 員工編號通常由各公司各自編；集團共用編號的公司可以改成客戶層級 | 02 D-20 | AI／JiHungLin（2026-10-14） |
| D-04 | 兩個業務上的天數：R13 到職日過後 3 天仍未確認列為警告；R56 到職前取消後 30 天產生封存建議（使用者選 A，照預設，2026-10-14） | 不設天數，只在當天提醒 | 沒有法規依據，是產品設定；先給預設值讓第 ⑤ 步能設計，之後可改為客戶設定 | 03_flows 決策流程三、五 | AI／JiHungLin（2026-10-14） |
| D-05 | 個資請求的處理期限（R53、R63）來源為個資法 §10、§13 原文（員工個人資料#08、#09，2026-10-14 讀取）。原本因全國法規資料庫被網路政策擋住而寫成推想草稿 inputs/drafts/個資請求處理期限.md；使用者開放網域後讀到原文，草稿改為「已取代」。原文和草稿的差別：沒有寫「只能延長一次」，只限延長的日數 | 接受推想草稿；請使用者貼條文 | 沒讀過的頁面不能當公開來源（CLAUDE.md 第 4 條）；讀得到原文就不用推想 | inputs/research/INDEX.md；員工個人資料#08、#09 | AI／JiHungLin（2026-10-14） |
| D-06 | 已領勞保老年給付者再受僱的勞保適用、65 歲界線、健保生效日、勞退開始提繳日、月薪資總額的項目、分級表依哪一天，都標待專家確認，沿用既有的 EQ-003、EQ-006、EQ-008、EQ-012，不另開新題 | 先照 AI 的理解寫死 | 條文沒寫或解讀不一，要人資實務確認 | questions.md | AI／待確認 |
| D-07 | 不寫守恆式 | 硬寫一條人數守恆 | 本切片沒有需要對帳的數量或金額；保費、薪資的對帳在後續切片 | docs/01 ④ | AI／待確認 |
| D-08 | 挑錯發現幾項判斷條件第 ② 步存不下，回到已凍結的第 ② 步新增（第 0 級回頭修改；使用者五項都選 A，2026-10-14，見 02 D-32～D-35；term_end 的說明一併改寫，02 D-36；延長個資請求要有事件，第 ③ 步新增 ExtendDataSubjectRequest，03_flows D-15）：① Employer 屬勞工保險條例 §6 第 1 項哪一款（行業類別，R22）；② Employer 的執業證照、依法免辦登記、核定課稅或統一發票購票證（R24、R25）；③ WorkAuthorization 每一次核准的期間與文號（R17）；④ Compensation 每月固定給付項目的分類（R39）；⑤ DataSubjectRequest 的延長期限與通知日（R53）。另外第 ③ 步的 ProposeEnrollmentFiling 觸發來源補上「登錄新的身分證件」「條件日期到達（滿 65 歲、制度施行日）」（R26、R29、R33；使用者選 A，03_flows D-16） | 不回頭，先用雇主型態近似、標待專家確認 | 這些條件都直接決定法律義務（強制或可自願、是否警告）；近似會判錯（X-02、X-03、X-07、X-09） | X-01、X-02、X-03、X-05、X-07、X-09、X-12 | AI／JiHungLin（2026-10-14） |
| D-09 | 「違反時」的擋下，原本 D-01 的範圍比使用者同意的大，請使用者決定後，使用者選 A，7 條都擋下（2026-10-14，inputs/shared/範圍釐清_擋下的範圍.md）：① 流程規則（R47～R50、R57：註銷白名單與順序、雇主不能用更正改、回執、解除封存要有依據）——建議擋下，因為它們管的是紀錄本身是否可信，不是法規判斷；② 法規中「刪除」與「查看」兩條（R55 勞工名卡五年內不得刪除、R52 個資查看權限）——建議擋下，因為刪除不可回復、越權查看無法事後補救；其餘法規檢查維持只提醒 | 全部改成提醒，完全依 01_scope D-17 | 01_scope D-17 寫「法規檢查只警告」，使用者同意擋下的只有資料矛盾（inputs/shared/範圍釐清_矛盾資料阻擋.md）；D-01 自行擴大了範圍（X-12） | 01_scope D-17；X-12 | AI／JiHungLin（2026-10-14） |
| D-10 | 個資請求可以延長幾次：照法規，次數不限、只限總日數；延長紀錄改成多筆（延長後期限、原因、書面通知日）（使用者 2026-10-14「延長次數先照法規」，02 D-35） | — | 原文只限延長的日數，沒有限制次數（員工個人資料#09）；多次延長時單一屬性會蓋掉前一次的書面通知紀錄（X-16） | X-16；02 D-35 | AI／JiHungLin（2026-10-14） |
| D-11 | 02 D-36（契約迄日只記契約上寫的，移工的實際期限由規則推出、不寫回）：AI 依 X-04 提出，使用者同意（2026-10-14，選 A） | 沒寫期限時把聘僱許可期限填進契約迄日 | AI 依 X-04 提出；許可展延或更正後，存進去的值會和許可不一致 | X-04、X-18；02 D-36 | AI／JiHungLin（2026-10-14） |
| D-12 | 加保待辦的觸發來源再補「雇主判定條件改變」（新增登記紀錄、取得核定課稅或購票證、免辦登記或行業類別改變、改為適用勞基法）、「人的國籍或戶籍新增期間」與「身分證件的生效日到了」（使用者選 A，2026-10-14「A補清楚」，03_flows D-17） | — | 和 03_flows D-16 同一類：員工沒做什麼，但適用改了；漏掉會變成晚辦（X-20）。D-16 是使用者選的 A，這次是補漏 | X-20；03_flows D-16 | AI／JiHungLin（2026-10-14） |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|
| X-01 | 保險適用只在到職日判定一次；職保施行前到職者依法自施行日起投保，卻被判不適用；取得永久居留、滿 65 歲、人數跨門檻後的改變判不出來 | AI 挑錯 | 接受，已修改 | R22～R29 改為依判定日 d；R28 加入過渡規定；第 ③ 步觸發來源的補充見 D-08 |
| X-02 | 勞保 5 人門檻：漁業生產等沒有人數條件、個人雇主屬自願，R22 判不出；人數以投保單位計是先替專家回答；沒加保的人歸不到投保單位 | AI 挑錯 | 接受，已修改 | R22 依 §6 各款與 §8 分開寫；R23 先以雇主人數計、層級待 EQ-008；雇主的行業類別待回到 ②（D-08） |
| X-03 | 把永久居留者當成免申請工作許可，和 §51「逕向中央主管機關申請許可」不符；R17 三年上限誤套在本人申請與展延 | AI 挑錯 | 接受，已修改 | R16 只限與國人結婚獲准居留；新增 R58；R17 只適用雇主申請、以每次核准計，每次核准期間待回到 ②（D-08） |
| X-04 | 移工的合法定期契約會被 R19、R20 誤警告；R18 的「以許可期限為契約期限」是法律擬制，不是警告 | AI 挑錯 | 接受，已修改 | R19、R20 排除移工；新增性質代碼「依就業服務法 §46 第 3 項」；R18 拆出 R59（判定）。02 的 term_end 說明「移工沒寫期限時依許可期限」會把推導值存成事實，回到 ② 時一併改寫（D-08） |
| X-05 | 健保期限寫死從到職日起算；外籍員工居留證明晚於到職日時判錯；起算含不含當日原文沒寫 | AI 挑錯 | 接受，已修改 | R26、R33 改依合於投保條件之日；起算方式併入 EQ-003；觸發來源補充見 D-08 |
| X-06 | 勞退自願提繳沒有國籍限制；工作居留的外籍員工沒有結果；漏了私立學校的例外 | AI 挑錯 | 接受，已修改 | R27 依 §7 第 1、2 項逐項寫，四種結果都涵蓋 |
| X-07 | 就保、職保要的雇主條件存不下（依法免辦登記、執業證照）；擇一參加判不出；漏公教、軍保的排除 | AI 挑錯 | 接受，已修改 | R24 補排除條件、擇一交給人判斷；R25 註明；雇主屬性待回到 ②（D-08） |
| X-08 | 提早辦理會算出到職前就生效；自願加保被算成晚辦 | AI 挑錯 | 接受，已修改 | 新增 R61；R35 只適用強制加保 |
| X-09 | 換版後用新版比舊申報；三種法定薪資基礎被混成一個 | AI 挑錯 | 接受，已修改 | R45 用投保薪資自己的版本比對、逕調不比；R39 拆成三種基礎；項目分類待回到 ②（D-08） |
| X-10 | 版本欄寫「依條文版本」太空；R12 只有 2026 一版；R28 沒涵蓋最低工資與分級表；R11 比較的工資基礎不明 | AI 挑錯 | 接受，已修改 | R12 補 v2025（勞保就保職保#08）；各規則的版本欄寫明讀取日與條文狀態；R28 套用到 R11、R40～R43；R11 的比較基礎轉問 EQ-019 |
| X-11 | 補登與更正可以繞過擋下的規則（R02、R04、R06）；改期沒有重跑 R01、R14；R55 和回填不一致 | AI 挑錯 | 接受，已修改 | R04 改為期間不重疊並加 CorrectRecord；R02、R06 加補登；RescheduleStart 回填 R01、R14；R55 套用對象只留刪除 |
| X-12 | 「擋下」超出使用者同意的範圍（R52、R54、R55 是法規；流程規則是 AI 自行擴充）；R54 無法測試；R53 的推想沒有草稿 | AI 挑錯 | 接受，已修改 | R54 取消；R53 寫成推想草稿待接受；擋下範圍請使用者決定（D-09）；延長期限的屬性待回到 ②（D-08） |
| X-13 | R07 只檢查雇主，沒檢查投保單位是否涵蓋該制度 | AI 挑錯 | 接受，已修改 | R07 加上制度涵蓋的檢查 |
| X-14 | 沒有約定薪資時，判定規則會靜默失敗；R21 的口頭契約說法前後不清 | AI 挑錯 | 接受，已修改 | 新增 R60「資料不足」；R21 改寫 |
| X-15 | 回頭修改後：許可還有效時登錄展延沒有狀態轉換，核准紀錄加不進去，人資可能用更正改舊核准的迄日 | AI 挑錯（第二輪，對回頭修改） | 接受，已修改 | 03_flows 新增 Valid → Valid（RecordWorkAuthorization，R03、R17、R58） |
| X-16 | 延長的三個屬性只能存一組；R63 說原文沒限制延長一次，第二次延長會蓋掉第一次的原因與通知日 | AI 挑錯（第二輪） | 接受，已修改 | 使用者選照法規（D-10）：02 改成多筆延長紀錄，R53、R63 同步 |
| X-17 | 改成依判定日 d 之後，UC-02 例外、UC-04 步驟 4 還寫到職日；決策流程一的證據刪掉了到職日，但期限與生效日仍要用 | AI 挑錯（第二輪） | 接受，已修改 | UC-02 例外改為判定日並引 R28；UC-04 改為判定日；證據列到職日與判定日 |
| X-18 | 02 D-36（契約迄日只記契約上寫的）不在使用者決定的事項裡，CHANGELOG 卻寫得像使用者決定的 | AI 挑錯（第二輪） | 接受，已修改 | 02 D-36 依據改為「AI 依 X-04 提出」，使用者確認同意（D-11）；CHANGELOG 另記一筆更正說明 |
| X-19 | 「延長要在原期限內決定」原文沒寫，D-15、R63 寫成像是 §13 的內容 | AI 挑錯（第二輪） | 接受，已修改 | R63、03_flows D-15 與說明改為「原文未寫，依文意推定」，需人做解讀核對 |
| X-20 | 觸發來源仍漏掉雇主判定條件的變化（取得登記、核定課稅、行業類別、改為適用勞基法）、證件生效日到了、戶籍或國籍新增期間 | AI 挑錯（第二輪） | 接受，已修改 | 使用者選 A（D-12）：03_flows D-17 補進觸發來源，決策流程一、UC-02 同步 |
| X-21 | 雇主的免辦登記、核定課稅是單一是或否，沒有期間，判定日 d 判不出；03 卻標「需要重建當時」 | AI 挑錯（第二輪） | 接受，已修改 | 02 兩個屬性加「會改變時保留期間」，行業類別同；03 歷史需求的理由同步 |
| X-22 | CHANGELOG 說 R32 已改寫，實際沒改；R32 與 R25 對登記種類的範圍不一致 | AI 挑錯（第二輪） | 接受，已修改 | R32 改為取公司登記、商業登記、設立稅籍最早一筆，執業證照只用於 R25 |
| X-23 | R55 列在 Rejected 轉換，字面上連拒絕刪除都會被擋；部分接受時擋哪一部分沒寫；版本欄「—」卻說要帶入版本 | AI 挑錯（第二輪） | 接受，已修改 | R55 擋的是「刪除保存期間內的資料類別」這個動作，含部分接受；Rejected 轉換拿掉 R55；版本欄補上 |
| X-24 | 台灣專屬的雇主屬性寫成所有雇主都必填，和 02 D-30 不寫死台灣的原則不一致 | AI 挑錯（第二輪） | 接受，已修改 | 02 改為「雇主註冊於台灣時必填」，詞彙表備註台灣專屬 |
| X-25 | 工作許可的舊說法沒清乾淨：「文號留歷史」、到期看「登錄的期限」、免申請者的到期與 EndWorkAuthorization 重複、UC-07 仍說以許可期限為準 | AI 挑錯（第二輪） | 接受，已修改 | 03 改為新增核准紀錄、到期看最後一筆核准的迄日且只用於申請許可者；UC-07 改依 R59 |
| X-26 | 分類值用一列代表 5 個代碼，違反一個代碼一列 | AI 挑錯（第二輪） | 接受，已修改 | LI_INDUSTRY 拆成 5 列 |
| X-27 | 03 檔頭讀取的輸入仍寫 02-v1；回填紀錄漏寫 Completed 也加了 R62 | AI 挑錯（第二輪） | 接受，已修改 | 檔頭與回填紀錄補正 |
| X-28 | EQ-020 的起算方式查得到法條（民法期間），不該問專家 | AI 挑錯（第二輪） | 接受，已修改 | 讀民法 §119～§122 存成 inputs/research/期間計算.md；R53 依民法起算；EQ-020 只留末日順延與收到日的實務 |

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每條規則都有種類、套用對象、判斷方式、來源與違反時的處理；會隨時間改變、且舊結果要依當時規則解釋的，有版本與生效日；沒有寫死的數字散落在流程裡 | ✓ 63 條（R01～R63，R54 已取消）都有種類、套用對象、判斷方式、違反時、來源；最低工資、分級表、各保險法規寫了版本與讀取日；天數與金額都寫在規則表（R12、R13、R40～R43、R53、R56、R63），03 只引用規則編號 | |
| 每條有來源的規則都已由人核對（對照法規或公司文件原文，或經人資專業人員確認）；引用公開來源條目的，該條目的原文也已核對；尚未核對的標「未核對」，可以先凍結進入 ⑤，但 ⑥ 中受它影響的案例不能算通過 | 部分：63 條都標 [未核對]，尚無人核對；引用的公開來源（8 份主題檔）原文也都未核對。規則中標 [解讀: …] 的 4 處要人做解讀核對：R33（外籍員工合於投保條件之日）、R37（到職後立刻離開不影響加保義務）、R59（以簽約當時有效那一次核准的迄日為契約期限）、R63（延長要在原期限內決定）；R55 的勞保條例、職保法保存年限只有使用者提供的資料，原文未讀。可以先凍結進入 ⑤ | |
| 判斷方式為「需人工判斷」的，經 Domain 專家確認（或標「待專家確認」） | ✓ 需人工判斷的 3 條：R19（繼續性工作，標 EQ-021）、R24（受僱於兩個以上雇主時擇一參加，交給人判斷並記錄選擇）、R55（期間屆滿後因爭議保留，交給人判斷並寫在拒絕的依據） | |
| ③ 每個狀態轉換的前提條件，都已對應到規則編號並回填 `03_flows.md` | ✓ 03_flows 34 個狀態轉換的「規則」欄都已回填（沒有規則的填「—」）；回頭修改新增的轉換也已填（回填紀錄）；不改變狀態的延長事件，規則寫在狀態機下方說明與 UC-14 | |
| 規則用到的分類值（例：假別、保險級距）都有穩定代碼，並登錄在詞彙對照表 | ✓ 分類值 77 列，一個代碼一列（挑錯後把 LI_INDUSTRY、WORK_CATEGORY 的範圍寫法拆開；tools/md2build.py 依格式解析沒有不合格式的列）；都有 zh-TW 名稱與用到的規則 | |
| 規則會用到的判斷條件（例：這天假是法定的還是公司加給的），在第 ② 步的 Entity 裡存得下 | ✓ 挑錯發現存不下的 5 項已回頭修改第 ② 步（02 D-32～D-36）；規則用到的屬性改寫成 `Entity.attribute`，由 tools/md2build.py 從規則文字抓出，tools/check.py「規則判別的屬性須存得下」通過 | |
| 有數量或金額需要對帳的地方（例：假的額度、薪資），已寫出守恆式；沒有的不必硬寫 | ✓ 本切片沒有需要對帳的數量或金額，不寫守恆式（D-07） | |
| `03_use_cases.md` 每條都已補上規則欄 | ✓ 15 個 UC 都有規則欄；回頭修改後 UC-02、UC-04、UC-07、UC-14 已同步 | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
