# hire-employee ④ 規則與限制

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ④ 規則與限制 |
| 狀態 | 草稿 |
| 版本 | （凍結後填 tag，例：hire-employee/04-v1） |
| 產出者 | AI（Claude） |
| 讀取的輸入 | 02_entities.md @ hire-employee/02-v2；03_flows.md、03_use_cases.md @ hire-employee/03-v1；法規與政策原文：inputs/research/勞保就保職保.md、全民健康保險.md、勞工退休金.md、工資與最低工資.md、勞動契約與年資.md、外國人聘僱.md、員工個人資料.md（皆最後確認 2026-10-05～06，未滿 6 個月）；inputs/shared/健保投保金額分級表_115年1月1日.md；PLAN.md D-27、D-28、D-33；inputs/shared/範圍釐清_法規警告不阻擋.md、範圍釐清_矛盾資料阻擋.md、範圍釐清_更正不需核准.md、範圍釐清_試用期.md |

<!-- 規則的「違反時」：擋下＝資料本身矛盾或流程上不可能（使用者已同意，範圍釐清_矛盾資料阻擋.md）；
     提醒＝法規檢查，只警告不阻擋，使用者可以忽略（OverrideWarning），PLAN.md D-27。
     判定、計算類填「—」；它們的結果是推導值，用在加保待辦與警告。 -->

## 規則
<!-- 種類：前提條件／計算／判定。判斷方式：可自動判斷／看條件／需解釋／需人工判斷
     違反時：擋下／提醒／交給人判斷／—。核對：誰，對照什麼，日期；或 [未核對]（AI 給的條號一律先標）
     編號全 repo 唯一：取 core/rules.md 與進行中切片的最大號加一 -->

### 一、資料本身的一致性（擋下）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R01 | 到職日不早於決定錄用的日期 | 前提條件 | StartEmployment | 可自動判斷 | 擋下 | 業務需求（資料矛盾，inputs/shared/範圍釐清_矛盾資料阻擋.md） | — | [未核對] |
| R02 | 僱傭關係的結束日不早於到職日 | 前提條件 | RecordEarlyDeparture、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（同上；01_scope D-17） | — | [未核對] |
| R03 | 出生日期不晚於登錄當天；證件、許可、契約的迄日不早於起日 | 前提條件 | RecordIdentityDocument、RecordWorkAuthorization、SignContract、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（同上） | — | [未核對] |
| R04 | 同一人在同一雇主，同一時間只能有一段在職的僱傭關係 | 前提條件 | StartEmployment、RegisterExistingEmployment、RevokeAnnulment | 可自動判斷 | 擋下 | 業務需求（03_flows D-03、X-15） | — | [未核對] |
| R05 | 同一時間在職的員工，員工編號不重複；範圍為同一雇主 [待使用者決定，見 D-03] | 前提條件 | StartEmployment、RegisterExistingEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-20；inputs/shared/範圍釐清_員工編號.md） | — | [未核對] |
| R06 | 組織單位有所屬雇主時，員工所屬組織單位的雇主要和僱傭關係的雇主相同 | 前提條件 | StartEmployment、CorrectRecord | 可自動判斷 | 擋下 | 業務需求（02 D-03） | — | [未核對] |
| R07 | 經由投保單位辦理的投保，投保單位的雇主要和僱傭關係的雇主相同；台灣的制度一定要經由投保單位 | 前提條件 | RecordInsuranceFiling | 可自動判斷 | 擋下 | 勞工保險條例 §6 以雇主為投保單位（勞保就保職保#01）；02 D-19 | — | [未核對] |
| R08 | 補登既有員工：到職日早於這個雇主開始由系統管理的日子（Employer.system_managed_from）；補登成已結束的，結束日也要早於這一天 | 前提條件 | RegisterExistingEmployment | 可自動判斷 | 擋下 | 業務需求（03_flows D-09；02 D-31） | — | [未核對] |
| R09 | 警告忽略紀錄至少針對錄用或僱傭關係其中之一 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | 業務需求（02 WarningOverride 的關係） | — | [未核對] |
| R10 | 只有「提醒」類規則的警告可以忽略；「擋下」類不能忽略 | 前提條件 | OverrideWarning | 可自動判斷 | 擋下 | PLAN.md D-27；inputs/shared/範圍釐清_法規警告不阻擋.md | — | [未核對] |

### 二、錄用、到職、工作許可、勞動契約（提醒）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R11 | 約定月薪不低於到職日當時的每月最低工資（R12）；只適用於適用勞基法的雇主 | 前提條件 | DecideHire、AgreeCompensation、StartEmployment、CorrectRecord | 看條件（雇主是否適用勞基法） | 提醒 | 最低工資法 §3、§5（工資與最低工資#05、#06） | 依 R12 的版本 | [未核對] |
| R12 | 每月最低工資：2026-01-01 起 29,500 元 | 計算 | R11 | 可自動判斷 | — | 勞動部新聞（工資與最低工資#07；新聞寫待行政院核定，核定公告未讀到） | 2026-01-01 起 | [未核對] |
| R13 | 約定到職日過了 3 天仍未登錄到職或取消，列為未處理的警告（天數 [待使用者決定，見 D-04]） | 前提條件 | Hire（PromptStartConfirmation 之後） | 可自動判斷 | 提醒 | 業務需求（03_flows D-01、決策流程三） | — | [未核對] |
| R14 | 外國籍員工（沒有中華民國國籍）到職日要有有效的工作許可，或屬免申請許可的身分（與在台設籍國民結婚且獲准居留等） | 前提條件 | StartEmployment、DecideHire | 可自動判斷 | 提醒 | 就業服務法 §43、§48、§51（外國人聘僱#01、#03、#04） | — | [未核對] |
| R15 | 雇主申請的聘僱許可，綁定的雇主要是這段僱傭關係的雇主 | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §43（外國人聘僱#01） | — | [未核對] |
| R16 | 依身分免申請許可的工作許可，要有依據的居留證件，且到職日當天證件有效、居留事由屬免申請的情形 | 前提條件 | RecordWorkAuthorization、StartEmployment | 可自動判斷 | 提醒 | 就業服務法 §48、§51（外國人聘僱#03、#04） | — | [未核對] |
| R17 | 聘僱許可期間不超過三年 | 前提條件 | RecordWorkAuthorization | 可自動判斷 | 提醒 | 就業服務法 §52（外國人聘僱#05） | — | [未核對] |
| R18 | 從事就業服務法 §46 第 1 項第 8～10 款工作（移工）的勞動契約，要是書面的定期契約；契約沒寫期限時，以聘僱許可期限為契約期限 | 前提條件 | SignContract | 可自動判斷 | 提醒 | 就業服務法 §46（外國人聘僱#02） | — | [未核對] |
| R19 | 定期契約要標明性質（臨時性、短期性、季節性、特定性）；有繼續性的工作應為不定期契約 | 前提條件 | SignContract | 需人工判斷（是否為繼續性工作） | 提醒 | 勞動基準法 §9（勞動契約與年資#04） | — | [未核對] |
| R20 | 定期契約期間上限：臨時性 6 個月以內；短期性可預期於 6 個月內完成；季節性 9 個月以內；特定性超過 1 年要報主管機關核備 | 前提條件 | SignContract | 可自動判斷 | 提醒 | 勞動基準法施行細則 §6（勞動契約與年資#11） | — | [未核對] |
| R21 | 到職後，僱傭關係要有約定薪資；沒有勞動契約時提醒（不定期契約可以是口頭） | 前提條件 | StartEmployment | 可自動判斷 | 提醒 | 業務需求（02 的關係 agreedFor、governs） | — | [未核對] |

### 三、各保險的適用（判定）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R22 | 勞保（普通事故）：年滿 15 歲以上、65 歲以下，受僱於投保單位僱用 5 人以上的公司、行號、工廠等 → 強制；未滿 5 人 → 可自願；包含外國籍員工。已領勞保老年給付者 [待專家確認: EQ-006] | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主型態、人數、年齡） | — | 勞工保險條例 §6、§8（勞保就保職保#01、#02） | 依條文版本 | [未核對] |
| R23 | 勞保人數門檻：某一天投保單位的計入人數，依各段僱傭關係實際到職、結束的發生日期計算；計入與不計入的範圍 [待專家確認: EQ-008] | 計算 | InsuranceUnit.insured_headcount_on | 看條件 | — | 勞工保險條例 §6（勞保就保職保#01） | — | [未核對] |
| R24 | 就保：年滿 15 歲以上、65 歲以下的受僱者，具中華民國國籍，或與在台設籍國民結婚且獲准居留 → 強制；已領勞保老年給付或公保養老給付者、受僱於依法免辦登記且無核定課稅的雇主者 → 不適用；受僱於兩個以上雇主者擇一 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、居留事由、年齡、老年給付、雇主登記） | — | 就業保險法 §5（勞保就保職保#10） | 依條文版本 | [未核對] |
| R25 | 職保：年滿 15 歲以上，受僱於領有執業證照、已依法登記、設有稅籍，或經核發聘僱許可的雇主 → 強制；沒有年齡上限，也沒有人數門檻 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（雇主登記、聘僱許可） | — | 勞工職業災害保險及保護法 §6（勞保就保職保#12） | 依條文版本 | [未核對] |
| R26 | 健保：本國籍且在台設有戶籍的受僱者 → 強制；在台領有居留證明文件、有一定雇主的受僱者 → 強制（看到職日當天有效的居留證件） | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（國籍、戶籍、居留證件） | — | 全民健康保險法 §8、§9（全民健康保險#02、#03） | 依條文版本 | [未核對] |
| R27 | 勞退：雇主適用勞基法，且員工為本國籍、與在台設籍國民結婚獲准居留、離婚或配偶死亡後依法繼續居留、或取得永久居留者 → 雇主強制提繳；實際從事勞動的雇主本人、不適用勞基法的勞工等 → 可自願 | 判定 | Employment（ProposeEnrollmentFiling） | 看條件（勞基法適用、國籍、居留事由） | — | 勞工退休金條例 §7（勞工退休金#01） | 依條文版本 | [未核對] |
| R28 | 到職日早於某制度的施行日 → 該制度「不適用（制度尚未施行）」；需要的規則版本系統裡沒有 → 「無對應規則版本」，不用現行規則代替 | 判定 | Employment（ProposeEnrollmentFiling） | 可自動判斷 | — | PLAN.md D-28、D-33；02 D-12 | — | [未核對] |
| R29 | 年齡以判定日（到職日）與出生日期計算；「六十五歲以下」含不含 65 歲生日當天 [待專家確認: EQ-006] | 計算 | Person.age | 可自動判斷 | — | 勞工保險條例 §6、就業保險法 §5（勞保就保職保#01、#10） | — | [未核對] |
| R30 | 適用哪個司法管轄區的勞動規則，看僱傭關係的工作地點所在的管轄區（本版只有台灣） | 判定 | Employment | 可自動判斷 | — | 業務需求（02 WorkLocation、Jurisdiction；PLAN.md D-10） | — | [未核對] |

### 四、應辦理期限、法定生效日、晚辦（計算）

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R31 | 勞保（含就保）：應辦理期限＝到職當日；法定生效日＝到職當日；實際生效日＝實際辦理日（到職當日通知時）或實際辦理日的翌日（非到職當日通知時） | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工保險條例 §11（勞保就保職保#03）；就業保險法 §40 準用（勞保就保職保#11） | 依條文版本 | [未核對] |
| R32 | 職保：應辦理期限＝到職當日（雇主登記或設稅籍前到職者，為登記或設稅籍當日）；法定生效日＝到職當日（同上例外），不因晚辦而延後 | 計算 | ProposeEnrollmentFiling、RecordInsuranceFiling | 可自動判斷 | — | 勞工職業災害保險及保護法 §12、§13（勞保就保職保#13、#14） | 依條文版本 | [未核對] |
| R33 | 健保：應辦理期限＝合於投保條件之日（到職日）起三日內；法定生效日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 可自動判斷（期限）；需解釋（生效日） | — | 全民健康保險法 §15（全民健康保險#05） | 依條文版本 | [未核對] |
| R34 | 勞退：應通知期限＝到職之日起七日內；開始提繳日 [待專家確認: EQ-003] | 計算 | ProposeEnrollmentFiling | 可自動判斷（期限）；需解釋（開始提繳日） | — | 勞工退休金條例 §18（勞工退休金#03） | 依條文版本 | [未核對] |
| R35 | 晚辦天數＝實際生效日 − 法定生效日（不足 0 以 0 計）；法定生效日待專家確認的制度不算 | 計算 | InsuranceEnrollment.days_late | 可自動判斷 | — | 由 R31～R34 推導 | — | [未核對] |
| R36 | 應辦理期限已過，仍沒有登錄實際辦理的強制保險 → 警告（逾期未辦） | 前提條件 | Employment（ProposeEnrollmentFiling） | 可自動判斷 | 提醒 | 由 R31～R34 推導；PLAN.md D-27 | — | [未核對] |
| R37 | 期限與生效日依到職日計算；到職後立刻離開不影響（加保義務已發生） | 判定 | ProposeEnrollmentFiling | 可自動判斷 | — | 01_scope D-12 | — | [未核對] |
| R38 | 試用期不改變到職日、保險生效日與年資起算 | 判定 | Employment | 可自動判斷 | — | 勞動基準法 §84-2、施行細則 §5（勞動契約與年資#07、#08）；inputs/shared/範圍釐清_試用期.md | — | [未核對] |

### 五、投保薪資

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R39 | 月薪資總額＝約定月薪＋每月固定給付的項目；哪些項目計入 [待專家確認: EQ-012] | 計算 | Compensation.monthly_wage_total | 需解釋 | — | 勞工保險條例 §14（勞保就保職保#05）；勞動基準法 §2 工資的定義（勞動契約與年資#02） | — | [未核對] |
| R40 | 勞保（含就保）月投保薪資：依勞保投保薪資分級表，以月薪資總額對應的級距申報 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工保險條例 §14（勞保就保職保#05）；分級表（勞保就保職保#17） | 2026-01-01 起（勞保就保職保#17） | [未核對] |
| R41 | 職保月投保薪資：依職保投保薪資分級表（21 級，下限等於基本工資） | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工職業災害保險及保護法 §17（勞保就保職保#16）；分級表（勞保就保職保#18） | 2026-01-01 起（勞保就保職保#18） | [未核對] |
| R42 | 勞退月提繳工資：依勞退月提繳分級表；雇主提繳不低於每月工資 6% | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 勞工退休金條例 §14（勞工退休金#02）；分級表（勞工退休金#05） | 2026-01-01 起（勞工退休金#05） | [未核對] |
| R43 | 健保投保金額：受僱者以薪資所得為投保金額，依健保投保金額分級表 | 計算 | ProposeEnrollmentFiling、DeclareInsuredSalary | 可自動判斷 | — | 全民健康保險法 §20（全民健康保險#08）；分級表為使用者提供的檔案（inputs/shared/健保投保金額分級表_115年1月1日.md），不是公開來源 | 2026-01-01 起 | [未核對] |
| R44 | 到職時用哪一版分級表：預設依到職日；跨年到職、隔年才辦理時依哪一天 [待專家確認: EQ-012] | 判定 | ProposeEnrollmentFiling | 需解釋 | — | 勞保就保職保#19（分級表依年度換版） | — | [未核對] |
| R45 | 申報的級距和應申報的級距不同 → 警告 | 前提條件 | DeclareInsuredSalary、CorrectRecord | 可自動判斷 | 提醒 | 由 R40～R43 推導；PLAN.md D-27 | — | [未核對] |

### 六、更正、註銷、警告忽略

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R46 | 重大更正：更正、註銷、撤銷註銷前後，任何投保單位某日的計入人數、任何人的保險適用、晚辦天數、或工作許可是否發給這個雇主有任一改變；拒絕個資請求一律算 → 通知雇主並列入重大更正清單 | 判定 | CorrectRecord、AnnulEntry、RevokeAnnulment、ResolveDataSubjectRequest | 可自動判斷 | — | 業務需求（03_flows D-02；inputs/shared/範圍釐清_更正不需核准.md） | — | [未核對] |
| R47 | 只能註銷白名單上的事件（03_flows D-14） | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-14） | — | [未核對] |
| R48 | 註銷前，後面沒有還沒註銷、又依賴它的事件；有的話依相反順序一起註銷 | 前提條件 | AnnulEntry | 可自動判斷 | 擋下 | 業務需求（03_flows D-03） | — | [未核對] |
| R49 | 雇主不能用更正改；要註銷原本的到職或補登，再對正確的雇主登錄 | 前提條件 | CorrectRecord | 可自動判斷 | 擋下 | 業務需求（03_flows 更正方式；02 D-03） | — | [未核對] |
| R50 | 實際辦理日、保險人核定的生效日、申報的投保薪資的更正，要附保險人回執或標示「無回執」 | 前提條件 | CorrectRecord、RecordInsuranceFiling | 可自動判斷 | 擋下 | 業務需求（03_flows D-02） | — | [未核對] |
| R51 | 警告忽略失效：被警告的值和 warned_value 不同，或適用於被警告事實的規則版本或修訂不同；錄用時的忽略在到職時重新評估 | 判定 | LapseWarningOverride | 可自動判斷 | — | 業務需求（03_flows D-11） | — | [未核對] |

### 七、個資

| 編號 | 規則 | 種類 | 套用對象 | 判斷方式 | 違反時 | 來源 | 版本／生效日 | 核對 |
|---|---|---|---|---|---|---|---|---|
| R52 | 個資只供處理人事的人資，在蒐集的特定目的範圍內查看與利用；各類個資誰可以看，第 ⑤ 步依平台 P7 落實 | 前提條件 | 查看個資（UC-14、UC-15） | 需解釋 | 擋下 | 個人資料保護法 §19、§20（員工個人資料#05、#06） | — | [未核對] |
| R53 | 個資請求的處理期限：查詢、閱覽、製給複製本 15 日內；補充更正、停止利用、刪除 30 日內；必要時可延長並通知當事人 | 計算 | PromptDataSubjectRequestDeadline | 可自動判斷 | — | 推想：個人資料保護法 §13（原文尚未蒐集，見 D-05） | — | [未核對] |
| R54 | 當事人的查詢、更正、刪除等權利不能事先約定放棄或限制 | 前提條件 | ReceiveDataSubjectRequest | 可自動判斷 | 擋下 | 個人資料保護法 §3（員工個人資料#02） | — | [未核對] |
| R55 | 勞工名卡的項目保存到離職後五年，期間內不得刪除（可以封存） | 前提條件 | ResolveDataSubjectRequest（刪除）、ArchivePersonalData | 可自動判斷 | 擋下 | 勞動基準法 §7（勞動契約與年資#03）；個人資料保護法 §11 但書（員工個人資料#04） | — | [未核對] |
| R56 | 到職前取消的人，保存目的消失，取消後 30 天產生封存建議（天數 [待使用者決定，見 D-04]） | 判定 | ProposeArchival | 可自動判斷 | — | 個人資料保護法 §11（員工個人資料#04） | — | [未核對] |
| R57 | 解除封存要連到一筆新的錄用、個資請求或註銷紀錄 | 前提條件 | ReleaseArchival | 可自動判斷 | 擋下 | 業務需求（03_flows X-09） | — | [未核對] |

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
| CONTRACT_TYPE.INDEFINITE | CONTRACT_TYPE | — | 不定期契約 | |
| CONTRACT_TYPE.FIXED_TERM | CONTRACT_TYPE | — | 定期契約 | |
| FIXED_TERM_NATURE.TEMPORARY_TW | FIXED_TERM_NATURE | TW | 臨時性 | R20 |
| FIXED_TERM_NATURE.SHORT_TERM_TW | FIXED_TERM_NATURE | TW | 短期性 | R20 |
| FIXED_TERM_NATURE.SEASONAL_TW | FIXED_TERM_NATURE | TW | 季節性 | R20 |
| FIXED_TERM_NATURE.SPECIFIC_TW | FIXED_TERM_NATURE | TW | 特定性 | R20 |
| DOCUMENT_KIND.NATIONAL_ID_TW | DOCUMENT_KIND | TW | 國民身分證 | |
| DOCUMENT_KIND.RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 居留證 | |
| DOCUMENT_KIND.PERMANENT_RESIDENT_CERTIFICATE_TW | DOCUMENT_KIND | TW | 永久居留證 | |
| DOCUMENT_KIND.PASSPORT | DOCUMENT_KIND | — | 護照 | 核發管轄區另記 |
| RESIDENCE_BASIS.MARRIAGE_TO_NATIONAL_TW | RESIDENCE_BASIS | TW | 與在台設籍國民結婚獲准居留 | R16、R24、R27 |
| RESIDENCE_BASIS.CONTINUED_AFTER_DIVORCE_OR_DEATH_TW | RESIDENCE_BASIS | TW | 與國人結婚後離婚或配偶死亡而依法繼續居留 | R27 |
| RESIDENCE_BASIS.EMPLOYMENT_TW | RESIDENCE_BASIS | TW | 工作 | |
| RESIDENCE_BASIS.PERMANENT_TW | RESIDENCE_BASIS | TW | 永久居留 | R16、R27 |
| AUTHORIZATION_BASIS.EMPLOYER_PERMIT | AUTHORIZATION_BASIS | — | 雇主申請的聘僱許可 | R15 |
| AUTHORIZATION_BASIS.SELF_PERMIT | AUTHORIZATION_BASIS | — | 本人申請的許可 | |
| AUTHORIZATION_BASIS.EXEMPT_BY_STATUS | AUTHORIZATION_BASIS | — | 依身分免申請 | R16 |
| WORK_CATEGORY.ESA46_01_TW～WORK_CATEGORY.ESA46_11_TW | WORK_CATEGORY | TW | 就業服務法 §46 第 1 項第 1～11 款 | 第 8～10 款為移工（R18）；共 11 個代碼 |
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
| INSURED_SALARY_SOURCE.EMPLOYER_DECLARED | INSURED_SALARY_SOURCE | — | 雇主申報 | |
| INSURED_SALARY_SOURCE.INSURER_ADJUSTED | INSURED_SALARY_SOURCE | — | 保險人逕調 | 勞保就保職保#19 |
| END_REASON.EMPLOYEE_QUIT_EARLY | END_REASON | — | 員工到職後立刻離開 | 本切片只有到職後立刻離開；其他原因由 resignation 擴充 |
| END_REASON.EMPLOYER_TERMINATED_EARLY | END_REASON | — | 雇主於到職後立刻終止 | |
| REQUEST_KIND.ACCESS | REQUEST_KIND | — | 查詢或閱覽 | R53 |
| REQUEST_KIND.COPY | REQUEST_KIND | — | 製給複製本 | R53 |
| REQUEST_KIND.RECTIFY | REQUEST_KIND | — | 補充或更正 | R53 |
| REQUEST_KIND.STOP_PROCESSING | REQUEST_KIND | — | 停止蒐集、處理或利用 | R53 |
| REQUEST_KIND.ERASE | REQUEST_KIND | — | 刪除 | R53、R55 |
| DATA_CATEGORY.LABOR_ROSTER | DATA_CATEGORY | TW | 勞工名卡項目 | R55 |
| DATA_CATEGORY.INSURANCE_ELIGIBILITY | DATA_CATEGORY | — | 判定保險用的身分資料 | |
| DATA_CATEGORY.CONTACT | DATA_CATEGORY | — | 聯絡用資料 | |
| EMPLOYEE_CATEGORY.FULL_TIME | EMPLOYEE_CATEGORY | — | 全職 | 本版只有全職（PLAN.md D-17） |
| PAY_BASIS.MONTHLY | PAY_BASIS | — | 月薪 | 本版只有月薪 |
| JURISDICTION_LEVEL.COUNTRY | JURISDICTION_LEVEL | — | 國家 | 州、市由 second-country-hire 補上 |

## 回填紀錄
- 03_flows.md：各狀態機「規則」欄回填 R01～R57 中的前提條件（見 03_flows.md 的各狀態轉換）
- 03_use_cases.md：UC-01～UC-15 的「規則」回填

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 |
|---|---|---|---|---|
| D-01 | 「違反時」分兩種：資料本身矛盾或流程上不可能的（R01～R10、R47～R50、R52、R54、R55、R57）擋下；法規檢查（最低工資、工作許可、契約、逾期未辦、級距不符）只提醒，可以忽略並留紀錄 | 法規一律擋下 | 使用者要求系統有彈性（PLAN.md D-27）；矛盾資料阻擋已經使用者同意（inputs/shared/範圍釐清_矛盾資料阻擋.md） | PLAN.md D-27；01_scope D-17 |
| D-02 | 各保險的適用、期限、級距寫成判定與計算規則，結果是推導值（02 D-04），只用在加保待辦與警告；投保要人資登錄實際辦理才建立 | 判定結果直接建立投保 | 03_flows D-04 | 02 D-04；03_flows D-04 |
| D-03 | 員工編號不重複的範圍：建議「同一雇主」（同一客戶內兩家公司可以各自有 E001），**請使用者決定**；決定前 R05 以同一雇主寫 | 同一客戶（集團）內都不重複 | 員工編號通常由各公司各自編；集團共用編號的公司可以改成客戶層級 | 02 D-20 |
| D-04 | 兩個業務上的天數先用預設值，**請使用者決定**：R13 到職日過後幾天仍未確認列為警告（預設 3 天）；R56 到職前取消後幾天產生封存建議（預設 30 天） | 不設天數，只在當天提醒 | 沒有法規依據，是產品設定；先給預設值讓第 ⑤ 步能設計，之後可改為客戶設定 | 03_flows 決策流程三、五 |
| D-05 | 個資請求的處理期限（R53）來源標「推想」：全國法規資料庫目前被環境的網路政策擋住（2026-10-14），讀不到個資法 §13 原文；開放後補進 inputs/research/員工個人資料.md，再改來源 | 憑記憶寫成公開來源 | 沒讀過的頁面不能當公開來源（CLAUDE.md 第 4 條） | inputs/research/INDEX.md |
| D-06 | 已領勞保老年給付者再受僱的勞保適用、65 歲界線、健保生效日、勞退開始提繳日、月薪資總額的項目、分級表依哪一天，都標 [待專家確認]，沿用既有的 EQ-003、EQ-006、EQ-008、EQ-012，不另開新題 | 先照 AI 的理解寫死 | 條文沒寫或解讀不一，要人資實務確認 | questions.md |
| D-07 | 不寫守恆式 | 硬寫一條人數守恆 | 本切片沒有需要對帳的數量或金額；保費、薪資的對帳在後續切片 | docs/01 ④ |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每條規則都有種類、套用對象、判斷方式、來源與違反時的處理；會隨時間改變、且舊結果要依當時規則解釋的，有版本與生效日；沒有寫死的數字散落在流程裡 | | |
| 每條有來源的規則都已由人核對（對照法規或公司文件原文，或經人資專業人員確認）；引用公開來源條目的，該條目的原文也已核對；尚未核對的標「未核對」，可以先凍結進入 ⑤，但 ⑥ 中受它影響的案例不能算通過 | | |
| 判斷方式為「需人工判斷」的，經 Domain 專家確認（或標「待專家確認」） | | |
| ③ 每個狀態轉換的前提條件，都已對應到規則編號並回填 `03_flows.md` | | |
| 規則用到的分類值（例：假別、保險級距）都有穩定代碼，並登錄在詞彙對照表 | | |
| 規則會用到的判斷條件（例：這天假是法定的還是公司加給的），在第 ② 步的 Entity 裡存得下 | | |
| 有數量或金額需要對帳的地方（例：假的額度、薪資），已寫出守恆式；沒有的不必硬寫 | | |
| `03_use_cases.md` 每條都已補上規則欄 | | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
