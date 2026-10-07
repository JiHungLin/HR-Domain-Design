# hire-employee ③ 正式 Use Case

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ③ 流程與狀態（Use Case） |
| 狀態 | 待檢查 |
| 版本 | （與 03_flows.md 一起凍結） |
| 讀取的輸入 | 01_scope.md @ hire-employee/01-v1；02_entities.md @ hire-employee/02-v1；03_flows.md（本步） |

<!-- 完成標準與檢查紀錄寫在 03_flows.md。參與者用業務角色：人資、員工、雇主（老闆）、系統 -->

## UC-01 錄用一位本國籍員工並登記到職
- 對應草稿：US-D01、US-D02、US-D14、US-D15、US-D16、US-D19
- 參與者：人資、雇主（老闆）
- 前提：雇主、組織單位、工作地點、投保單位已有固定資料（org-setup 靜態替代）
- 主流程：
  1. 人資登錄人（Person）與身分證件（RecordIdentityDocument）；同一客戶內已有這個人時沿用（見 UC-12）
  2. DecideHire：記雇主、約定到職日、預定工作地點與組織單位（可以沒有）；AgreeCompensation 記約定月薪與每月固定給付的項目；有書面契約時 SignContract
  3. 系統檢查約定月薪是否低於到職日當時的每月最低工資，不通過時顯示警告（UC-09）
  4. 系統產生加保待辦（ProposeEnrollmentFiling，見 UC-02）
  5. 約定到職日到了，系統提醒確認（PromptStartConfirmation）；人資確認這個人已開始工作，StartEmployment：建立僱傭關係（到職日、雇主、工作地點、組織單位、試用期、員工編號），契約生效，約定薪資與錄用時有效的警告忽略接續掛上
  6. 系統依僱傭關係的工作地點，判定適用哪個司法管轄區的勞動規則（Q04）
  7. 有試用期時記錄到哪一天；試用期不改變到職日、保險生效日與年資起算（Q08，inputs/shared/範圍釐清_試用期.md）
  8. 人資依待辦到保險人辦理加保，回來登錄（UC-03）
- 例外：
  - 到職日前改期 → UC-05；到職前取消 → UC-06
  - 到職日當天就來上班（US-D19）：步驟 2 與步驟 5 可以在同一天完成，事件仍分開記
- 用到的 Entity：Person、IdentityDocument、Hire、Employment、EmploymentContract、Compensation、Employer、OrgUnit、WorkLocation、InsuranceUnit、Jurisdiction
- 用到的事件：RecordIdentityDocument、DecideHire、AgreeCompensation、SignContract、PromptStartConfirmation、StartEmployment、ProposeEnrollmentFiling、RescheduleStart、CancelHire
- 規則：（第 ④ 步回填）

## UC-02 判定各保險的適用、期限、生效日與投保薪資級距
- 對應草稿：US-D01、US-D05、US-D07、US-D09、US-D14、US-D15、US-D16、US-D17、US-D18
- 參與者：系統、人資、雇主（老闆）
- 前提：已有錄用或僱傭關係；約定薪資已登錄
- 主流程：
  1. 訊號：決定錄用、到職、改期或資料更正（其他單位個體的變化），或應辦理期限將到（時間到達）
  2. 系統依人的國籍、戶籍、證件與居留事由、出生日期、已領的老年給付，雇主的型態、登記日、是否適用勞基法，投保單位當天的計入人數，以及到職日當時的規則版本，判定勞保、就保、職保、健保、勞退各為強制、可自願或不適用
  3. 人數依實際到職、離開的發生日期計算，列出計入與不計入的名單（Q12，計入範圍待 [待專家確認: EQ-008]）；人數跨過門檻時，既有員工的適用改變一併列出（US-D17）
  4. 對每一種適用的保險，分開算出應辦理期限與法定生效日（月底到職、前一份工作做到前一天，都依同一套規則，US-D15、US-D16）
  5. 依月薪資總額與各保險自己的分級表，算出應申報的級距，並記下分級表版本（US-D09、US-D14、US-D18）
  6. 產生加保待辦（ProposeEnrollmentFiling）：可自願的列出讓雇主選擇；記錄這次判定依據的資料與規則版本
- 例外：
  - 到職日沒有對應的規則版本（補登的既有員工）→ 標「無對應規則版本」，不用現行規則代替（UC-11）
  - 到職日早於某制度的施行日 → 該制度為「不適用（制度尚未施行）」
  - 員工到職前在別處投保（US-D07）→ 判定照常；原投保情形只記錄說明，對本雇主加保的影響 [待專家確認: EQ-010]
- 用到的 Entity：Person、IdentityDocument、Employer、InsuranceUnit、Employment、Compensation、SocialInsuranceScheme、Jurisdiction、Hire
- 用到的事件：ProposeEnrollmentFiling
- 規則：（第 ④ 步回填）

## UC-03 登錄實際辦理加保與投保薪資
- 對應草稿：US-D04
- 參與者：人資
- 前提：僱傭關係已成立；加保待辦已產生
- 主流程：
  1. 人資在保險人辦完加保後，登錄實際辦理日與是否自願（RecordInsuranceFiling），附申報回執（沒有時標示「無回執」）；有保險人核定的生效日時一併登錄
  2. 人資登錄申報的投保薪資（DeclareInsuredSalary），記金額、級距、分級表版本、申報日
  3. 系統比對實際生效日與法定生效日，算出晚了幾天；申報的級距和應申報的不同時顯示警告
- 例外：
  - 可自願的保險，雇主決定不加 → 記在加保待辦上（人、時間）
  - 晚辦（US-D04）：勞保、就保的實際生效日晚於到職日，系統列出晚幾天；職保、健保、勞退各依自己的規則判斷是否受影響
  - 登錄錯誤 → UC-08
- 用到的 Entity：InsuranceEnrollment、InsuredSalary、Employment、InsuranceUnit、SocialInsuranceScheme
- 用到的事件：RecordInsuranceFiling、DeclareInsuredSalary
- 規則：（第 ④ 步回填）

## UC-04 錄用外籍員工（含移工）
- 對應草稿：US-D08、US-D11、US-D12
- 參與者：人資
- 前提：同 UC-01
- 主流程：
  1. 人資登錄國籍、居留證或永久居留證與居留事由（RecordIdentityDocument）
  2. 登錄工作許可（RecordWorkAuthorization）：依據（雇主申請、本人申請、依身分免申請）、工作類別、文號、起訖日、綁定的雇主
  3. 其餘同 UC-01；移工的書面定期契約見 UC-07
  4. 系統檢查到職日是否落在許可期間內、許可是否發給這個雇主；判定各保險時使用到職日當時有效的證件與居留事由（UC-02）
- 例外：
  - 許可在到職日還沒生效（US-D11）→ 警告，人資可改到職日（UC-05）或照樣存檔（UC-09）
  - 居留事由在到職後改變（例：取得永久居留、離婚後依法繼續居留）→ 登錄新的一筆證件，前一筆 Superseded；之後的判定依新的一筆。免申請者的許可由系統提醒確認（ProposeAuthorizationReview），人資決定是否登錄失效（EndWorkAuthorization）[待專家確認: EQ-018]
  - 許可展延已核准但較晚才登錄 → 許可從已失效回到有效，仍是同一筆
- 用到的 Entity：Person、IdentityDocument、WorkAuthorization、Hire、Employment、EmploymentContract、Employer
- 用到的事件：RecordIdentityDocument、RecordWorkAuthorization、DecideHire、StartEmployment、ExpireWorkAuthorization、ExpireIdentityDocument、ProposeAuthorizationReview、EndWorkAuthorization
- 規則：（第 ④ 步回填）

## UC-05 到職前改期
- 對應草稿：US-D03
- 參與者：人資
- 前提：錄用是 Hired
- 主流程：
  1. 人資改約定到職日（RescheduleStart），填理由
  2. 原本的到職日保留，查得到誰在什麼時候改的
  3. 系統依新的到職日重新產生加保待辦與警告
- 例外：已經提早辦了加保 → 處理方式 [待專家確認: EQ-005]
- 用到的 Entity：Hire
- 用到的事件：RescheduleStart、ProposeEnrollmentFiling
- 規則：（第 ④ 步回填）

## UC-06 到職前取消錄用
- 對應草稿：US-D03
- 參與者：人資
- 前提：錄用是 Hired（到職日當天沒來也算）
- 主流程：
  1. 人資取消錄用（CancelHire），填取消原因
  2. 掛在錄用上的契約失效（VoidContract）；不建立僱傭關係，這個人不算這個雇主的員工
  3. 系統產生封存建議（ProposeArchival），人資決定是否封存這個人的個資（UC-13）
- 例外：
  - 其實已經到職 → 用更正處理（UC-08 誤登取消）
  - 已經提早辦了加保 → [待專家確認: EQ-005]
- 用到的 Entity：Hire、EmploymentContract、PersonalDataArchival
- 用到的事件：CancelHire、VoidContract、ProposeArchival
- 規則：（第 ④ 步回填）

## UC-07 登錄勞動契約並檢查定期契約的期間
- 對應草稿：US-D12、US-D13
- 參與者：人資
- 前提：已有錄用或僱傭關係
- 主流程：
  1. 人資登錄契約（SignContract）：不定期或定期；定期的寫性質與起訖日；是否書面
  2. 系統檢查定期契約的期間是否超過該性質的上限；移工檢查是否為書面定期契約，沒寫期限時以聘僱許可期限為準
  3. 到職時契約生效（隨 StartEmployment）；起日晚於到職日的，起日到達時生效（ContractTermStarts）
- 例外：期間超過上限（US-D13）→ 警告，人資可改正或照樣存檔（UC-09）
- 用到的 Entity：EmploymentContract、Hire、Employment、WorkAuthorization
- 用到的事件：SignContract、ContractTermStarts、StartEmployment
- 規則：（第 ④ 步回填）

## UC-08 更正到職資料與註銷誤登
- 對應草稿：US-D06
- 參與者：人資、核准人；員工（經由個資請求，UC-14）
- 前提：資料已登錄
- 主流程（值打錯）：
  1. 人資提出更正，填理由與證據；系統試算影響（人數、保險適用、晚辦天數、許可是否發給這個雇主）
  2. 有上述影響或更正到職日的，走核准申請（RequestApproval → ApproveRequest）；核准前資料與判定維持原狀（03_flows D-02）。沒有影響的，人資直接更正
  3. 執行更正（CorrectRecord）：原值保留，記更正者、核准人、時間
  4. 系統依更正後的資料重新判定各保險、期限、級距，以及依日期推導的狀態（例：證件期限打錯而被判到期，回到有效）；更正前、當時系統知道的判定仍查得到
  5. 受影響的警告忽略紀錄依條件失效（LapseWarningOverride）；其他員工的判定有改變時，產生新的加保待辦（ProposeEnrollmentFiling）
- 例外（整筆誤登，AnnulEntry，一律走核准申請）：
  - 誤登到職（其實從未上班）→ 註銷到職（後面有到職後立刻離開的一起註銷），再登錄到職前取消；這段僱傭關係不計入人數、年資、勞工名卡；已加保的提醒向保險人處理 [待專家確認: EQ-017]
  - 誤登取消（其實已經到職）→ 註銷取消，錄用回到已錄用、契約依其餘事件重新推導，再登錄到職；已封存的個資由人資解除（UC-13）
  - 誤登到職後立刻離開 → 註銷，僱傭關係回到在職
  - 誤補登的既有員工 → 註銷補登
  - 登錯雇主 → 註銷原本的到職或補登，再對正確的雇主登錄；登錯人 → 更正指向的人（要核准）
  - 註銷錯了 → 撤銷註銷（RevokeAnnulment），原本那一段與掛在上面的紀錄恢復
  - 核准人駁回 → 申請保留，資料不變
- 用到的 Entity：Hire、Employment、EmploymentContract、Compensation、Person、IdentityDocument、WorkAuthorization、InsuranceEnrollment、InsuredSalary、WarningOverride、PersonalDataArchival、ApprovalRequest
- 用到的事件：RequestApproval、ApproveRequest、RejectRequest、WithdrawRequest、CorrectRecord、AnnulEntry、RevokeAnnulment、StartEmployment、CancelHire、ProposeEnrollmentFiling、LapseWarningOverride、ReleaseArchival
- 規則：（第 ④ 步回填）

## UC-09 忽略法規警告，以及撤回
- 對應草稿：US-D11、US-D13
- 參與者：人資
- 前提：存檔時有法規警告成立（例：月薪低於最低工資、許可未生效、定期契約超過上限、晚辦加保）
- 主流程：
  1. 系統顯示警告與依據的規則、版本
  2. 人資選擇照樣存檔（OverrideWarning），理由可不填；系統記規則與版本、被警告的值、忽略者、時間
  3. 系統列出目前有哪些員工（還沒到職的看錄用）帶著未處理的警告；有效的忽略不算未處理。錄用時的忽略在到職時重新評估，沒變的加上針對僱傭關係的連結
- 例外：
  - 資料之後改正或改變，或適用於這個事實的規則版本或修訂不同（例：錄用時忽略，實際到職日落在新版最低工資的期間）→ 忽略失效（LapseWarningOverride）；若警告仍成立，重新列為未處理。對已判定的事實，之後才生效的新版規則不影響
  - 人資撤回忽略（WithdrawWarningOverride）→ 記撤回者、時間，警告重新列為未處理
  - 資料本身矛盾（例：結束日早於到職日）→ 阻擋，不能忽略
- 用到的 Entity：WarningOverride、Hire、Employment
- 用到的事件：OverrideWarning、LapseWarningOverride、WithdrawWarningOverride
- 規則：（第 ④ 步回填）

## UC-10 到職後立刻離開
- 對應草稿：US-D10
- 參與者：人資
- 前提：僱傭關係是 Active
- 主流程：
  1. 人資登錄結束日與原因（RecordEarlyDeparture）；可以晚幾天才登錄，結束日記實際的日期
  2. 僱傭關係改為 Ended，契約隨之結束；這個人仍算曾是這個雇主的員工
  3. 加保判定不變：到職日起的加保義務已發生，期限與生效日照常列出（01_scope D-12）
- 例外：
  - 結束日早於到職日 → 阻擋（資料矛盾）
  - 登錯了（其實仍在職）→ 走核准申請後註銷（UC-08）
  - 更正結束日 → 會改變人數，走核准申請（UC-08）
- 用到的 Entity：Employment、EmploymentContract
- 用到的事件：RecordEarlyDeparture、VoidContract、AnnulEntry
- 規則：（第 ④ 步回填）

## UC-11 補登客戶開始使用系統前就到職的員工
- 對應草稿：（無，依 Q21）
- 參與者：人資
- 前提：這位員工在這個雇主開始由系統管理的日子之前就已到職；補登已結束的一段時，結束日也在這一天之前（03_flows D-09，這個日子的記錄方式待使用者決定，D-13）
- 主流程：
  1. 人資登錄人、證件，以及僱傭關係（RegisterExistingEmployment）：到職日、雇主、工作地點等，沒有錄用紀錄，標為補登資料
  2. 登錄目前的事實：約定薪資、目前的投保（實際加保日）與投保薪資（02 D-12）
  3. 寫一段當時依據的說明（historical_basis_note）
  4. 系統判定到職當時的各項：有對應規則版本的照算，沒有的標「無對應規則版本」（PLAN.md D-33）；加入系統之後的變化照常記錄與判定；補登不改寫補登前已產生的其他員工的判定，那些判定依當時系統知道的資料仍查得到（03_flows D-10）
- 例外：補登已離職的先前一段（回任時要找得到）→ 直接登錄為 Ended
- 用到的 Entity：Person、IdentityDocument、Employment、Compensation、InsuranceEnrollment、InsuredSalary
- 用到的事件：RecordIdentityDocument、RegisterExistingEmployment、RecordInsuranceFiling、DeclareInsuredSalary、AgreeCompensation
- 規則：（第 ④ 步回填）

## UC-12 同一個人再次被錄用（回任）
- 對應草稿：（無，依 Q11）
- 參與者：人資
- 前提：同一客戶內，這個人以前有過一段已結束的僱傭關係（靜態替代提供）
- 主流程：
  1. 人資登錄新錄用時，系統以身分證件號碼認出是同一個人，沿用同一個 Person
  2. 若這個人的個資已封存，人資解除需要的類別（ReleaseArchival，UC-13）
  3. 照 UC-01 建立新的錄用與僱傭關係；已結束的那一段不改動
- 例外：證件號碼換了（例：外籍員工的舊式統一證號換新式）→ 人資確認是同一人後沿用 [待專家確認: EQ-015]
- 用到的 Entity：Person、IdentityDocument、Hire、Employment、PersonalDataArchival
- 用到的事件：DecideHire、StartEmployment、ReleaseArchival
- 規則：（第 ④ 步回填）

## UC-13 封存與解除封存個資
- 對應草稿：（無，依 Q22）
- 參與者：人資、系統
- 前提：保存目的已消失（本切片：到職前取消的人）
- 主流程：
  1. 系統產生封存建議（ProposeArchival）
  2. 人資封存（ArchivePersonalData）：寫明封存的個資類別與理由
  3. 封存後，一般功能看不到這些類別，只能依法調閱
- 例外：
  - 之後需要再使用 → 人資解除需要的類別（ReleaseArchival），必須連到一筆新的錄用、個資請求或註銷紀錄
  - 人資決定暫不封存 → 在這筆建議上記錄處置與理由
- 用到的 Entity：PersonalDataArchival、Person
- 用到的事件：ProposeArchival、ArchivePersonalData、ReleaseArchival
- 規則：（第 ④ 步回填）

## UC-14 處理員工的個資請求
- 對應草稿：（無，依 Q22）
- 參與者：員工、人資
- 前提：員工本人提出
- 主流程：
  1. 員工提出，或人資代登錄書面、email、口頭的請求（ReceiveDataSubjectRequest）：種類、收到日期、收到管道
  2. 法定處理期限將到或已過時，系統提醒（PromptDataSubjectRequestDeadline）
  3. 人資執行：更正走 CorrectRecord；停止利用或刪除走 ArchivePersonalData（刪除的實際做法第 ⑤ 步依平台 P7 設計）；查詢、複製則提供資料
  4. 人資完成請求（ResolveDataSubjectRequest），寫明結果；不接受時寫明法定理由，並先走核准申請（RequestApproval → ApproveRequest）
- 例外：員工撤回 → 記為完成，結果寫「當事人撤回」
- 誰可以查看哪些個資（Q22 前半）是權限設定，不是流程：第 ④ 步寫規則、第 ⑤ 步依平台 P7 落實
- 用到的 Entity：DataSubjectRequest、Person、PersonalDataArchival、ApprovalRequest
- 用到的事件：ReceiveDataSubjectRequest、PromptDataSubjectRequestDeadline、RequestApproval、ApproveRequest、ResolveDataSubjectRequest、CorrectRecord、ArchivePersonalData
- 規則：（第 ④ 步回填）

## UC-15 查詢勞工名卡
- 對應草稿：（無，依 Q10）
- 參與者：人資；勞動檢查時的檢查員（查看）
- 前提：這段僱傭關係沒有被註銷
- 主流程：
  1. 人資查詢某位員工的勞工名卡
  2. 系統從人、身分證件、僱傭關係、約定薪資、投保組出名卡：姓名、性別、出生年月日、本籍或國籍、教育程度、住址、身分證統一編號或統一證號、到職年月日、工資、勞工保險投保日期（記保險人核定的實際生效日 [待專家確認: EQ-015]）
  3. 獎懲、傷病由 personnel-record 切片提供（PLAN.md D-32），本切片顯示為空
- 例外：外籍員工沒有本籍與身分證統一編號 → 顯示國籍與統一證號
- 用到的 Entity：Person、IdentityDocument、Employment、Compensation、InsuranceEnrollment
- 用到的事件：（查詢，不改變狀態）
- 規則：（第 ④ 步回填）

## 驗收問題涵蓋

| 驗收問題 | 由哪個 UC 的哪一步回答 |
|---|---|
| Q01 | UC-01 步驟 5 |
| Q02 | UC-02 步驟 4 |
| Q03 | UC-03 步驟 1、3 |
| Q04 | UC-01 步驟 6 |
| Q05 | UC-02 步驟 2 |
| Q06 | UC-02 步驟 2；UC-04 步驟 4 |
| Q07 | UC-01 步驟 3 |
| Q08 | UC-01 步驟 7 |
| Q09 | UC-02 例外（原投保情形） |
| Q10 | UC-15 |
| Q11 | UC-12 |
| Q12 | UC-02 步驟 3 |
| Q13 | UC-02 步驟 6；UC-09 例外（規則版本） |
| Q14 | UC-05、UC-06 |
| Q15 | UC-08 |
| Q16 | UC-04 步驟 2、4 |
| Q17 | UC-02 步驟 5；UC-03 步驟 2 |
| Q18 | UC-10；UC-08 例外（誤登到職） |
| Q19 | UC-07 |
| Q20 | UC-09 |
| Q21 | UC-11 |
| Q22 | UC-13、UC-14 |

## 草稿涵蓋檢查

| 草稿 US | 涵蓋它的 UC |
|---|---|
| US-D01 | UC-01、UC-02 |
| US-D02 | UC-01 |
| US-D03 | UC-05、UC-06 |
| US-D04 | UC-03 |
| US-D05 | UC-02 |
| US-D06 | UC-08 |
| US-D07 | UC-02 |
| US-D08 | UC-04 |
| US-D09 | UC-02 |
| US-D10 | UC-10 |
| US-D11 | UC-04、UC-09 |
| US-D12 | UC-04、UC-07 |
| US-D13 | UC-07、UC-09 |
| US-D14 | UC-01、UC-02 |
| US-D15 | UC-01、UC-02 |
| US-D16 | UC-01、UC-02 |
| US-D17 | UC-02 |
| US-D18 | UC-02 |
| US-D19 | UC-01 |
