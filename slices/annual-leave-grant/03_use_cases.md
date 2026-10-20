# annual-leave-grant ③ 正式 Use Case

| 項目 | 內容 |
|---|---|
| 切片 | annual-leave-grant |
| 步驟 | ③ 流程與狀態（Use Case） |
| 狀態 | 已凍結 |
| 版本 | annual-leave-grant/03-v1 |
| 讀取的輸入 | 01_scope.md @ annual-leave-grant/01-v1；02_entities.md @ annual-leave-grant/02-v1；03_flows.md（本步產出） |

<!-- 完成標準與檢查紀錄寫在 03_flows.md -->

## UC-01 週年制依年資給予特休
- 對應草稿：US-D01
- 參與者：人資、系統
- 前提：僱傭關係在職（core 的 StartEmployment 已發生）；這位員工有週年制的特休年度約定，或雇主預設週年制
- 主流程：人資查詢這位員工的特休，看到之後各期的預估（推導：預計取得日、天數、可休期間）→ 滿 6 個月的取得日到達，GrantLeaveEntitlement 給予法定一筆（Active），記下依據 → 告知期限開始計算（見 UC-04）→ 之後每滿一個週年再給予一筆 → 每一筆可休迄日過完時 CloseLeaveYear（見 UC-05）
- 例外：取得日當天僱傭關係已結束 → 不給予（見 UC-09）；取得日早於雇主開始由系統管理的日子 → 不給予，由人補登（見 UC-07）；這位員工沒有約定、雇主也沒有預設 → 第 ④ 步的規則 [待專家確認: EQ-002]
- 用到的 Entity：Employment、LeaveYearAgreement、CompanyPolicy、LeaveType、LeaveEntitlement
- 用到的事件：StartEmployment、GrantLeaveEntitlement、CloseLeaveYear
- 規則：（第 ④ 步回填）

## UC-02 曆年制給予特休
- 對應草稿：US-D02
- 參與者：人資、系統
- 前提：這位員工有曆年制的特休年度約定，或雇主預設曆年制（RecordLeaveYearAgreement 或 EstablishCompanyPolicy 已發生）
- 主流程：取得日到達，GrantLeaveEntitlement 依曆年制的換算給予（Active），記下依據的年度種類與它依據的約定或預設 → 可休迄日是那一年的 12 月 31 日 → 換算後的天數少於依法應給的，成立法規警告（人資改正或 OverrideWarning）
- 例外：到職第一年、跨年度怎麼換算，一筆是否包含兩次符合條件（取得日、告知幾次）[待專家確認: EQ-002]
- 用到的 Entity：Employment、LeaveYearAgreement、CompanyPolicy、LeaveEntitlement、WarningOverride
- 用到的事件：RecordLeaveYearAgreement、GrantLeaveEntitlement、OverrideWarning
- 規則：（第 ④ 步回填）

## UC-03 公司規定多給特休
- 對應草稿：US-D03
- 參與者：人資或雇主（老闆）、系統
- 前提：雇主訂定了特休加給的公司規定（例：滿 1 年多給 2 天；這版以固定資料提供）
- 主流程：EstablishCompanyPolicy（Scheduled 或 Effective）→ 第一次生效日到達，ActivateCompanyPolicy → 員工取得法定特休的同一天，GrantLeaveEntitlement 另給予公司規定的一筆（來源：公司規定，連到那條規定，記下版本）→ 查詢時法定與公司多給分成兩筆
- 例外：公司規定修改（ReviseCompanyPolicy）→ 已給予的依原版本，之後取得的依新版本（Q10）；年度終結時公司加給能不能失效依哪一版 [待專家確認: EQ-013]；生效日或廢止日登錄錯誤，更正後 ReassessLeaveEntitlements 補上或拿掉那段期間的加給（03_flows D-14）；公司規定廢止（RepealCompanyPolicy）→ 已給予的不受影響；公司規定少於法定 → 法規警告；員工類型更正後適用的規定不同 → ReassessLeaveEntitlements（見 UC-08）
- 用到的 Entity：CompanyPolicy、LeaveEntitlement、Employment
- 用到的事件：EstablishCompanyPolicy、ActivateCompanyPolicy、ReviseCompanyPolicy、RepealCompanyPolicy、ExpireCompanyPolicy、GrantLeaveEntitlement、ReassessLeaveEntitlements、CorrectRecord
- 規則：（第 ④ 步回填）

## UC-04 告知員工排定特休
- 對應草稿：US-D06
- 參與者：雇主（老闆）、人資、系統
- 前提：一筆依規則給予的法定特休已取得（GrantLeaveEntitlement）
- 主流程：查詢看到這一筆的告知期限與告知狀態「待告知」→ 雇主告知員工 → 人資或雇主登錄 RecordLeaveNotice（告知日）→ 告知狀態「已告知」
- 例外：過了期限仍沒有登錄 → 告知狀態「逾期未告知」，成立法規警告 → 之後告知並登錄，告知狀態「逾期後告知」；或以 OverrideWarning 忽略並寫理由。告知日打錯 → CorrectRecord。補登的特休不判定告知（01_scope D-09）。符合條件之前就告知算不算數 [待專家確認: EQ-006]
- 用到的 Entity：LeaveEntitlement、WarningOverride
- 用到的事件：GrantLeaveEntitlement、RecordLeaveNotice、OverrideWarning、CorrectRecord
- 規則：（第 ④ 步回填）

## UC-05 年度終結：協商遞延，其餘轉為工資
- 對應草稿：US-D04
- 參與者：人資、員工、雇主（老闆）、系統
- 前提：一筆可以遞延的特休（依規則給予或補登當期）是 Active，年度終結日前有未休額度
- 主流程：員工與雇主協商，談定這一筆延幾天 → 人資登錄 RecordLeaveDeferral（Agreed）→ 年度終結日過完，CloseLeaveYear：那一筆 → YearEnded；依協商產生遞延進來的一筆（Active，可休期間是下一個年度，連回原來那一筆與協商），協商 → Applied；其餘未休額度產生一筆轉換（轉為工資），記工資計算基準日（這一筆的年度終結日）與發給期限 → 薪資切片依轉換計算金額與發放
- 例外：沒有登錄協商 → 未休全部轉為工資；年度終結前重新協商 → AmendLeaveDeferral；雙方取消 → WithdrawLeaveDeferral；公司規定的那筆能不能延、會不會失效 [待專家確認: EQ-005]；發給期限怎麼擇一 [待專家確認: EQ-003]；年度終結前僱傭關係結束 → 見 UC-09
- 用到的 Entity：LeaveEntitlement、LeaveDeferralAgreement、LeaveConversion
- 用到的事件：RecordLeaveDeferral、AmendLeaveDeferral、WithdrawLeaveDeferral、CloseLeaveYear
- 規則：（第 ④ 步回填）

## UC-06 遞延進來的天數到次一年度終結仍沒休
- 對應草稿：US-D05
- 參與者：系統、人資
- 前提：一筆遞延進來的特休（或補登遞延的）是 Active
- 主流程：可休迄日過完，CloseLeaveYear：那一筆 → YearEnded；未休額度全部產生一筆轉換（轉為工資），工資計算基準日是**原年度**的終結日（補登遞延的用人登錄的原年度終結日）
- 例外：人資想再遞延 → RecordLeaveDeferral 的前提不成立（遞延進來的不能再遞延），擋下；次一年度終結前僱傭關係結束 → 見 UC-09
- 用到的 Entity：LeaveEntitlement、LeaveConversion
- 用到的事件：CloseLeaveYear、RecordLeaveDeferral
- 規則：（第 ④ 步回填）

## UC-07 補登系統開始管理前就到職的員工的特休
- 對應草稿：US-D07
- 參與者：人資、系統
- 前提：雇主開始由系統管理的日子已定；員工已補登（core 的 RegisterExistingEmployment），到職日早於開始管理的日子
- 主流程：人資依雇主原有的紀錄，對開始管理那天仍可以休的每一筆，分別登錄 RegisterExistingLeaveEntitlement（例：今年的當期一筆、去年遞延過來的一筆；法定與公司多給分開）：來源、來歷、額度、開始管理前已休、可休期間；補登遞延的另登原年度終結日 → 各筆 Active → 之後取得的由 GrantLeaveEntitlement 依年資給予（見 UC-01）
- 例外：補登的不判定告知期限；補登遞延的那筆不能再遞延；登錯值 → CorrectRecord，整筆登錯 → AnnulEntry，接著 ReassessLeaveEntitlements（已年度終結的轉換記負數差額，待確認）；之後到職日更正時，補登的那筆不參加重新判定、不被作廢，和依規則重算的期間重疊或有空檔時由 NotifyLeaveReassessment 列出（03_flows D-04）
- 用到的 Entity：Employer、Employment、LeaveEntitlement
- 用到的事件：RegisterExistingEmployment、RegisterExistingLeaveEntitlement、GrantLeaveEntitlement、CorrectRecord、AnnulEntry、ReassessLeaveEntitlements、NotifyLeaveReassessment
- 規則：（第 ④ 步回填）

## UC-08 到職日更正後重新判定特休
- 對應草稿：US-D08
- 參與者：人資、雇主（老闆）、系統
- 前提：這位員工已經依原到職日給予過特休（可能已有年度終結的判定與轉換）
- 主流程：人資更正到職日（core 的 CorrectRecord，原值保留）→ ReassessLeaveEntitlements：依新到職日重算每一期，和既有的逐筆比對同一來源、同一可休期間——對得上的就地更正、對不上的作廢、多出來的新增；已年度終結的就地更正後 RejudgeLeaveYearEnd、回到可休或作廢時轉換記差額；新增的一期如果可休迄日已經過了，立刻 CloseLeaveYear，轉換待確認 → NotifyLeaveReassessment 列出更正前後的每一筆、轉換差額、待確認的轉換，以及要人處理的事 → 人資改正已休的固定資料、重新登錄告知日與遞延協商 → 人資確認待確認的轉換（ConfirmLeaveConversion）後交給薪資；增加工資的差額直接交給薪資
- 例外：更正只改變額度、可休期間不變（例：曆年制）→ 就地更正，已休、告知日留在原來那一筆；特休年度約定、員工類型的更正也走同一個流程；作廢的那筆上已休超過新的額度 → 通知列出，由人處理（之後由 annual-leave-request 定義）；原本的告知算不算數 [待專家確認: EQ-012]；多發的轉換工資怎麼處理 [待專家確認: EQ-009]
- 用到的 Entity：Employment、LeaveEntitlement、LeaveDeferralAgreement、LeaveConversion
- 用到的事件：CorrectRecord、ReassessLeaveEntitlements、RejudgeLeaveYearEnd、CloseLeaveYear、NotifyLeaveReassessment、RecordLeaveNotice、RecordLeaveDeferral、ConfirmLeaveConversion
- 規則：（第 ④ 步回填）

## UC-09 還沒滿年資或年度終結前離職
- 對應草稿：US-D09
- 參與者：系統、人資
- 前提：僱傭關係結束（core 的 RecordEarlyDeparture，或這版以固定資料提供的一般離職 [靜態替代]）
- 主流程：EndLeaveEntitlementsWithEmployment：取得日不晚於結束日、可休迄日晚於結束日的每一筆 → EndedWithEmployment，交給 resignation 依契約終止處理；Agreed 的遞延協商 → Lapsed；之後的取得日到達也不再給予（GrantLeaveEntitlement 的前提不成立）
- 例外：還沒滿 6 個月就結束 → 從來沒有給予法定特休；最後工作日剛好是滿 6 個月那天 [待專家確認: EQ-006]；結束日剛好是年度終結日 [待專家確認: EQ-011]；結束日較晚才得知、取得日晚於結束日的那一筆（例：固定資料較晚載入時已經給予）→ 作廢；年度終結判定之後才登錄結束日 → 那次年度終結視為沒有發生：那一筆 YearEnded → EndedWithEmployment，已做的轉換記負數差額（待確認，ConfirmLeaveConversion），遞延進來的那筆作廢，Applied 的協商 → Lapsed（03_flows D-05）；結束被註銷或結束日更正 → ReassessLeaveEntitlements 恢復
- 用到的 Entity：Employment、LeaveEntitlement、LeaveDeferralAgreement、LeaveConversion
- 用到的事件：RecordEarlyDeparture、EndLeaveEntitlementsWithEmployment、GrantLeaveEntitlement、ReassessLeaveEntitlements、ConfirmLeaveConversion
- 規則：（第 ④ 步回填）

## UC-10 員工改用另一種特休年度
- 對應草稿：US-D10
- 參與者：人資、員工、雇主（老闆）、系統
- 前提：雇主原本預設週年制；部分員工同意改用曆年制
- 主流程：雇主訂定新的預設（EstablishCompanyPolicy 或 ReviseCompanyPolicy，事項為特休年度預設）或逐人協商 → 同意的員工由人資登錄 RecordLeaveYearAgreement（曆年制，適用起日例：明年 1 月 1 日，Scheduled）→ 適用起日到達，ActivateLeaveYearAgreement：新約定 Effective、舊約定 Superseded → 之後的給予依曆年制；不同意的員工保留原本的個別約定；雇主改的是預設時，還在套用預設的員工會跟著換，系統對他們成立警告，不同意的由人資登錄一筆維持週年制的個別約定（03_flows D-13）→ 查詢看得出每位員工現在用哪一種、是約定還是套用預設
- 例外：改用的那一年怎麼換算、是否少於依法應給 [待專家確認: EQ-002]，少於時成立法規警告；約定晚登錄、適用起日早於已給予的取得日 → ReassessLeaveEntitlements（03_flows D-10）；工作規則算不算勞雇雙方協商 [待專家確認: EQ-002]；員工想從個別約定回到雇主預設 → EndLeaveYearAgreement
- 用到的 Entity：LeaveYearAgreement、CompanyPolicy、LeaveEntitlement、Employment
- 用到的事件：EstablishCompanyPolicy、ReviseCompanyPolicy、RecordLeaveYearAgreement、ActivateLeaveYearAgreement、EndLeaveYearAgreement、GrantLeaveEntitlement、ReassessLeaveEntitlements、OverrideWarning
- 規則：（第 ④ 步回填）

## UC-11 可能應合併年資的警告
- 對應草稿：US-D11
- 參與者：人資、系統
- 前提：同一個人在同一雇主有前一段已結束的僱傭關係（結束日這版以固定資料提供）
- 主流程：人資登錄新的一段（core 的 StartEmployment）→ 前一段的結束日到這一段的到職日未滿三個月，成立「可能應合併年資」的法規警告（推導）→ 人資確認後以 OverrideWarning 忽略並寫理由，或改正資料；特休這版仍從這一段的到職日起算
- 例外：其實是同一段的續約（不是新的一段）→ 人資改正資料，不該建立新的一段 [待專家確認: EQ-007]；合併的計算由 seniority-recognition 補上，之後依合併後的年資重新判定
- 用到的 Entity：Person、Employment、EmploymentContract、WarningOverride
- 用到的事件：StartEmployment、OverrideWarning、GrantLeaveEntitlement
- 規則：（第 ④ 步回填）

## UC-12 年度終結之後才改變的資料
- 對應草稿：US-D04、US-D05
- 參與者：人資、系統
- 前提：一筆特休已 YearEnded，已有轉換交給薪資
- 主流程：判定用到的資料改變——最後幾天的請假較晚登錄（這版改正已休的固定資料）、遞延協商事後登錄（RecordLeaveDeferral → Applied）、雙方改談（AmendLeaveDeferral）、取消（WithdrawLeaveDeferral）、補登的額度更正（CorrectRecord）→ RejudgeLeaveYearEnd：遞延進來的那一筆新增、更正或作廢；轉換另記一筆差額，指回被更正的那一次並記更正原因；增加工資的直接交給薪資，減少工資的待確認 → NotifyLeaveReassessment 通知人資與雇主 → 人資確認（ConfirmLeaveConversion）→ 薪資切片依差額補發或處理
- 例外：遞延進來的那一筆已經休了一部分又被撤回 → 作廢的那筆上已休的天數由通知列出，人處理；年度終結後才登錄或修改遞延協商（看登錄時間，不論填的協商日）→ 法規警告，不阻擋，算不算數 [待專家確認: EQ-003]；確認前資料又改 → 待確認的那一筆被重算的取代；固定資料的已休改正要記誰、何時、理由，判定當時的已休仍查得到（03_flows D-15）；多發的怎麼處理 [待專家確認: EQ-009]
- 用到的 Entity：LeaveEntitlement、LeaveDeferralAgreement、LeaveConversion
- 用到的事件：RecordLeaveDeferral、AmendLeaveDeferral、WithdrawLeaveDeferral、CorrectRecord、RejudgeLeaveYearEnd、NotifyLeaveReassessment、ConfirmLeaveConversion
- 規則：（第 ④ 步回填）

## 草稿涵蓋檢查

| 草稿 US | 涵蓋它的 UC |
|---|---|
| US-D01 | UC-01 |
| US-D02 | UC-02 |
| US-D03 | UC-03 |
| US-D04 | UC-05、UC-12 |
| US-D05 | UC-06、UC-12 |
| US-D06 | UC-04 |
| US-D07 | UC-07 |
| US-D08 | UC-08 |
| US-D09 | UC-09 |
| US-D10 | UC-10 |
| US-D11 | UC-11 |
