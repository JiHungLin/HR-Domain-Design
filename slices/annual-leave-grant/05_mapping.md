# annual-leave-grant ⑤ 投影到實作

| 項目 | 內容 |
|---|---|
| 切片 | annual-leave-grant |
| 步驟 | ⑤ 投影到實作 |
| 狀態 | 已凍結 |
| 版本 | annual-leave-grant/05-v1 |
| 產出者 | AI（Claude）＋ |
| 讀取的輸入 | 02_entities.md @ annual-leave-grant/02-v1；03_flows.md、03_use_cases.md @ annual-leave-grant/03-v3（本步回頭修改 D-16，一起凍結）；04_rules.md @ annual-leave-grant/04-v2（本步回頭修改 D-22～D-25，一起凍結）；core/ @ b341be2；docs/03 平台架構約定（P4、P5、P10、P12 照文件；P1、P2、P3、P6、P7、P8 與資料庫依 PLAN.md D-35；P11 依 PLAN.md D-31）；slices/hire-employee/05_mapping.md、api.yaml @ hire-employee/05-v5（共用的集合、`events`、更正與註銷、警告忽略的 API 與格式） |

<!-- 資料庫為 MongoDB（PLAN.md D-35），本文件的「表」是集合（collection），「欄位」是文件的欄位。
     概念 ID 寫 core/ 的英文識別名稱；技術欄位標 [技術]（P8）。本步先只產出這份對照表，經人確認後才產生 schema.mongo.js 與 api.yaml。
     沿用 hire-employee 05_mapping 的平台做法：只新增（P2 A）的版本文件與 entity_id 引用（hire-employee D-10）、`events` 只新增、`change_log`（P2 B）、
     多文件交易、每個 ref 檢查同一客戶（hire-employee D-06）、警告格式與版本（hire-employee D-20）。這裡只寫本切片新增或不同的地方。 -->

## 一、概念 → 表與欄位

### 1.1 集合

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| LeaveType | `leave_types` | `code`、`jurisdiction_id`、`status` | 全平台共用的參考資料（同 `jurisdictions`，02 D-10、D-15），由平台維運維護，本切片的 API 只能讀；名稱放 `labels`（P10）；只需現況（P2 C，D-13） |
| CompanyPolicy | `company_policies` | 見 1.2 | 只新增（P2 A）；第一版的內容與之後的版本放 `company_policy_versions` |
| 公司規定的版本（規則資料，02「不是 Entity」） | `company_policy_versions` | `policy_id`、`version`、`revision`、`effective_from`、`params`、`recorded_at`、`supersedes` | 客戶內的規則資料（P5）；`params` 的名稱照 04 參數表（見第三節 3.2）。只新增：內容登錯時新增一筆修訂，不原地改（03_flows ReviseCompanyPolicy「版本更正是新的修訂」）。不放進全平台共用的 `rule_versions`：那是平台管理者維護、不分客戶的（D-01） |
| LeaveYearAgreement | `leave_year_agreements` | 見 1.2 | 覆寫＋變更紀錄（P2 B） |
| LeaveEntitlement | `leave_entitlements` | 見 1.2 | 只新增（P2 A）：就地更正、告知日、狀態改變都新增一份版本文件 |
| LeaveDeferralAgreement | `leave_deferral_agreements` | 見 1.2 | 只新增（P2 A）：修改（AmendLeaveDeferral）與打錯的更正都新增版本 |
| LeaveConversion | `leave_conversions` | 見 1.2 | 只新增（P2 A）；已判定的內容不再改，差額另記一筆（02 D-06） |
| 年度終結的判定內容（CloseLeaveYear、RejudgeLeaveYearEnd） | `events` | `payload.year_end`：見 1.3 | 判定當時已知的已休等記在那次判定的事件上（03_flows D-15、04 自評第 7 條），不另立集合（D-07） |
| NotifyLeaveReassessment（事件，建議層） | `leave_reassessment_notices` | 見 1.2 | 不可作廢：獨立集合，沒有作廢或修改的 API（03_flows 事件表；同 hire-employee 的 `significant_corrections`，D-08） |
| 已休（`LeaveEntitlement.used_quantity`）[靜態替代] | `leave_used_quantity_fixtures` | `entitlement_id`、`used_quantity`、`recorded_by`、`recorded_at`、`reason` | 這版的固定資料（01_scope 範圍外但會用到；02 D-13）；改正要記誰、何時、理由（03_flows 更正方式「已休」），覆寫＋變更紀錄（P2 B）；annual-leave-request 定義請假事實後取代（D-10）。只有一個累計值、沒有日期：查詢帶 `on` 時已休與剩餘一律用目前的累計值，回應標 `used_quantity_basis`＝目前累計（[靜態替代] 的限制）；帶 `as_of` 時依 `change_log` 還原那個時間的值（X-09） |
| 契約約定的工資給付日、發給期限的做法 [靜態替代] | `employer_settings` | `employer_id`、`wage_payment_day[]`、`wage_payment_lag_months[]`、`payment_deadline_rule[]`：各為 `value`、`from`、`to` | 04 參數 `wage_payment_day`、`wage_payment_lag_months`、`payment_deadline_rule`，依雇主（04 D-23）；這版由平台維運載入固定資料，沒有 API；沒有登錄 `payment_deadline_rule` 時用 `rule_versions`（R90）的預設；monthly-payroll 第 ④ 步定義後取代（D-10） |
| 一般離職的結束日 [靜態替代] | `employments`（hire-employee 的集合） | `ended_on`、`end_reason`、`status` | 這版以固定資料提供（01_scope D-14）：用 `POST /v1/employments/{id}/ending-fixture` 寫一筆事件 `LoadEmploymentEndingFixture`，產生新版本的 `employments`，視同 resignation 的離職事件（03_flows EndLeaveEntitlementsWithEmployment 的觸發來源）；resignation 定義後拿掉（D-10） |
| 所有有名字的事件（P1） | `events`（hire-employee 的集合） | 見 1.3 | 本切片的 20 個事件與 1 個固定資料事件寫在同一個集合 |
| 規則與版本（P5） | `rule_versions`（hire-employee 的集合） | `rule_id`（R65…）、`version`、`revision`、`effective_from`、`effective_to`、`params`、`source_ref` | 全平台共用；04 參數表中「依什麼條件變化」為「—」的參數放在用到它的規則的 `params`（第三節 3.2） |
| 分類值的多語名稱（P10） | `labels`（hire-employee 的集合） | `code`（例：`LEAVE_TYPE.ANNUAL_LEAVE_TW`）、`locale`、`label` | 26 個分類值的 zh-TW 名稱取自 04 分類值表 |

### 1.2 業務欄位

型別同 hire-employee 05_mapping 1.2：`date`＝日期；`datetime`＝時刻；`ref`＝指到另一個概念的 `entity_id`；`code`＝分類值代碼；`decimal`＝Decimal128；`[]`＝陣列。數量一律 `decimal`：單位可能是小時，補登與公司多給也可能有半日（02 LeaveEntitlement.unit；D-14）。

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| LeaveType.code | `leave_types` | `code`（code，例：`LEAVE_TYPE.ANNUAL_LEAVE_TW`） | 唯一；其他集合用代碼指它，不用 `_id`（參考資料只有現況，D-13） |
| LeaveType.name | `labels` | `label`（`code`＝假別代碼） | P10：名稱不存在 `leave_types`，依語言取 |
| establishedBy | `leave_types` | `jurisdiction_id`（ref，可空） | 02 關係表：0..1 |
| LeaveType 的狀態 | `leave_types` | `status`（Active／Deprecated） | 03 不設事件，平台維運直接維護（03_flows LeaveType） |
| CompanyPolicy.name、subject、source_note | `company_policies` | `name`（string）、`subject`（code）、`source_note`（string） | |
| CompanyPolicy.effective_from／effective_to | `company_policies` | `effective_from`、`effective_to`（date，可空） | 生效日、廢止日改變時觸發 ReassessLeaveEntitlements（03_flows D-14） |
| belongsToTenant（CompanyPolicy） | `company_policies` | `tenant_id`（ref） | 業務關係（同 hire-employee 的 `persons`、`employers`） |
| ofEmployer、concernsLeaveType | `company_policies` | `employer_id`（ref，可空）、`leave_type_code`（code，可空） | 02 關係表：都是 0..1 |
| CompanyPolicy 的狀態 | `company_policies` | `status`（Scheduled／Effective／Repealed） | P1；快取（第四節） |
| 公司規定的版本內容 | `company_policy_versions` | `params`：`company_extra_days[]`（`from_months`、`to_months`、`days`）、`company_extra_eligibility`（`employee_categories[]`，空＝全部員工）、`company_extra_year_end_treatment`（code：工資／失效，可空＝沒有寫）、`company_extra_deferrable`（bool，可空）、`company_default_leave_year`（`leave_year_basis`、`year_start`） | 名稱照 04 參數表；事項為特休加給的版本只有前四個，事項為特休年度預設的版本只有最後一個；「那一版沒有寫」用欄位不存在表示（04 R79 決策表），不填預設值 |
| LeaveYearAgreement.leave_year_basis、year_start | `leave_year_agreements` | `leave_year_basis`（code）、`year_start`：`month`、`day` | 週年制沒有 `year_start` |
| LeaveYearAgreement.effective_from、agreed_on、agreement_note | `leave_year_agreements` | `effective_from`、`agreed_on`（date）、`agreement_note`（string） | |
| forEmployment、ofLeaveType（LeaveYearAgreement） | `leave_year_agreements` | `employment_id`（ref）、`leave_type_code`（code） | |
| EndLeaveYearAgreement 的生效時間（終止日） | `leave_year_agreements` | `ended_from`（date，可空） | 03_flows 事件表「生效（終止日）」；放在約定上，終止日才能用 CorrectRecord 更正（03_flows 更正方式第 2 列；D-11） |
| LeaveYearAgreement 的狀態 | `leave_year_agreements` | `status`（Scheduled／Effective／Superseded／Ended） | P1；快取 |
| LeaveEntitlement.source、origin | `leave_entitlements` | `source`、`origin`（code） | |
| LeaveEntitlement.period_sequence、seniority_tier | `leave_entitlements` | `period_sequence`（int，可空）、`seniority_tier`（int：滿幾個月，04 D-09，可空） | 依規則給予的才有 |
| LeaveEntitlement.acquired_on、quantity、unit | `leave_entitlements` | `acquired_on`（date）、`quantity`（decimal）、`unit`（code） | |
| LeaveEntitlement.valid_from／valid_to | `leave_entitlements` | `valid_from`、`valid_to`（date） | |
| LeaveEntitlement.leave_year_basis | `leave_entitlements` | `leave_year_basis`（code，可空） | 補登的沒有（04 R87） |
| LeaveEntitlement.basis_rule_versions | `leave_entitlements` | `basis_rule_versions[]`：`kind`（RULE／COMPANY_POLICY）、`rule_id` 或 `policy_id`、`version`、`revision` | 每一種規則一筆（02）；補登的是空陣列＋`no_rule_version: true`（PLAN.md D-28「無對應規則版本」，04 R79 找不到版本） |
| LeaveEntitlement.basis_seniority | `leave_entitlements` | `basis_seniority`：`months`、`days` | 取得日當時算出，凍結使用（02 X-16） |
| LeaveEntitlement.basis_start_date | `leave_entitlements` | `basis_start_date`（date） | |
| LeaveEntitlement.notified_on | `leave_entitlements` | `notified_on`（date，可空） | RecordLeaveNotice 新增一份版本文件；告知狀態不存（第四節） |
| LeaveEntitlement.pre_system_used_quantity、registered_original_year_end | `leave_entitlements` | `pre_system_used_quantity`（decimal）、`registered_original_year_end`（date） | 補登的才有 |
| LeaveEntitlement.notice_due_on、used_quantity、deferred_out_quantity、converted_quantity、expired_quantity、remaining_quantity | — | — | 不落地（推導，P3）；查詢時現算（第四節）。已休由 `leave_used_quantity_fixtures` 加 `pre_system_used_quantity` 算 |
| forEmployment、ofLeaveType（LeaveEntitlement） | `leave_entitlements` | `employment_id`（ref）、`leave_type_code`（code） | |
| grantedUnderPolicy、deferredFrom、deferredUnder | `leave_entitlements` | `policy_id`、`deferred_from_id`、`deferred_under_id`（ref，可空） | |
| appliedYearAgreement、appliedYearDefault | `leave_entitlements` | `applied_year_agreement_id`、`applied_year_default_policy_id`（ref，可空） | 最多一個（R74） |
| LeaveEntitlement 的狀態 | `leave_entitlements` | `status`（Active／YearEnded／EndedWithEmployment／Voided） | P1；快取 |
| LeaveDeferralAgreement.agreed_on、deferred_quantity、agreement_note | `leave_deferral_agreements` | `agreed_on`（date）、`deferred_quantity`（decimal）、`agreement_note`（string） | 修改與更正都新增版本；版本文件記 `event_id`，分得出是 AmendLeaveDeferral 還是 CorrectRecord（03_flows D-06） |
| forEmployment、defersEntitlement | `leave_deferral_agreements` | `employment_id`、`entitlement_id`（ref） | |
| LeaveDeferralAgreement 的狀態 | `leave_deferral_agreements` | `status`（Agreed／Applied／Withdrawn／Lapsed） | P1；快取 |
| LeaveConversion.reason、target、quantity | `leave_conversions` | `reason`、`target`（code）、`quantity`（decimal，差額可為負） | |
| LeaveConversion.determined_on、wage_basis_date、payment_due_on | `leave_conversions` | `determined_on`、`wage_basis_date`、`payment_due_on`（date，後兩者可空） | 判定時算出、凍結（02 X-14）；失效、負數差額沒有發給期限（R90） |
| LeaveConversion.basis_rule_versions、correction_cause | `leave_conversions` | `basis_rule_versions[]`（同上）、`correction_cause`（code，可空） | |
| convertsFrom、correctsConversion | `leave_conversions` | `entitlement_id`、`corrects_conversion_id`（ref，可空）、`corrects_judgment_event_id`（可空） | 差額指回被更正的那一次（03_flows D-06）：原判定有轉換時指那筆轉換；原判定沒有轉換（例：全部遞延、之後協商撤回）時指那次 CloseLeaveYear 或 RejudgeLeaveYearEnd 的事件。差額一律對「應轉換額度減已判定合計」算（R92），所以只指原判定那一次（X-09） |
| LeaveConversion 的狀態 | `leave_conversions` | `status`（Provisional／Determined／Discarded）、`discarded_by_id`（ref，可空：取代它的那一筆） | P1；快取 |
| NotifyLeaveReassessment 的內容 | `leave_reassessment_notices` | `employment_id`、`trigger_event_id`（哪一次重新判定或年度終結）、`root_event_id`（最初由人或排程做的那個動作，例：CorrectRecord；同一次動作連鎖產生的每一份通知都記同一個，X-06）、`changed[]`：`entitlement_id`、`before`、`after`（額度、期間、取得日、狀態）；`added_ids[]`、`voided_ids[]`；`conversion_ids[]`、`provisional_conversion_ids[]`；`action_items[]`：`kind`（code）、`entitlement_id`、`detail`；`notified_to[]`（人資、雇主（老闆））、`notified_at` | `action_items.kind`：作廢的那筆上有已休、要重新登錄告知日、要重新登錄遞延協商、已休大於額度、補登的那筆和依規則重算的期間重疊或有空檔、告知日早於取得日、協商遞延額度超過未休（03_flows 事件表、R81、R86、R96）；用 `NOTICE_ACTION.*` 代碼（只在 ⑤ 用的畫面代碼，不是 04 的分類值，D-08） |

### 1.3 事件紀錄（`events`，P1、P4）

沿用 hire-employee 05_mapping 1.3 的欄位（`type`、`subject`、`occurred_at`、`recorded_at`、`effective_from`、`actor`、`evidence[]`、`reason`、`rule_versions[]`、`derived`、`invalidated_by_event_id`、註銷）。本切片另加：

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| 事件名稱 | `events` | `type` | 03_flows 事件表的 20 個事件；另加固定資料事件 `LoadEmploymentEndingFixture`、`LoadUsedQuantityFixture`、`LoadEmployerFixture`（[靜態替代]，D-10、X-21） |
| 有意義的時間 | `events` | `occurred_at`、`recorded_at`、`effective_from` | 依 03_flows 事件表；例：GrantLeaveEntitlement 的發生是取得日、生效是可休起日；CloseLeaveYear 的發生是年度終結日、得知是判定日；RecordLeaveDeferral 的發生是協商日，登錄時間（`recorded_at`）用來判斷 R84 |
| 年度終結的判定內容 | `events` | `payload.year_end`：`entitlement_id`、`used_quantity_known`（判定當時已知的已休）、`unused_quantity`、`deferral_agreement_ref`（`id`、`version_event_id`：判定時依的那一版協商）、`deferred_in_quantity`、`deferred_in_entitlement_id`、`conversion_ids[]`、`late`（是否為補做的年度終結，R93） | CloseLeaveYear、RejudgeLeaveYearEnd 各記一筆；之後已休改正不會蓋掉（03_flows D-15） |
| 重新判定的對應結果 | `events` | `payload.reassessment`：`basis_before`、`basis_after`（被更正的依據）、`matched[]`（舊 → 新）、`voided_ids[]`、`added_ids[]`、`restored_ids[]` | ReassessLeaveEntitlements；R91 的對應過程要查得到（Q11） |
| 依據的規則版本 | `events` | `rule_versions[]` | 給予、年度終結、重新判定都記；公司規定的版本記 `kind`＝COMPANY_POLICY |
| 由日期觸發的事件 | `events` | `derived`（true） | GrantLeaveEntitlement、CloseLeaveYear 推導出來就是事實（03_flows「狀態怎麼來」），依據改了**不**標失效，由 ReassessLeaveEntitlements、RejudgeLeaveYearEnd 記改變；ActivateLeaveYearAgreement、ActivateCompanyPolicy、ExpireCompanyPolicy 照 hire-employee D-12：依據的日期被更正時標 `invalidated_by_event_id`，重新推導（D-03） |

## 二、事件 → API

API 以 REST 描述（OpenAPI 3.1），路徑前綴 `/v1`；每支 API 標 `x-concept`（P8）。每次呼叫在同一個多文件交易中寫入 `events` 與受影響的集合（PLAN.md D-35）。

**所有 API 共同的檢查**：沿用 hire-employee D-06（每個 ref 同一客戶、存在、是目前版本；全平台共用的 `leave_types`、`rule_versions`、`labels` 只能讀）。本切片另加：

- **同一段僱傭關係一次只做一件事**：本切片每個會寫入的動作（含系統排程，也含經 hire-employee 的更正與註銷 API 改到本切片集合的）在交易中先更新 `leave_locks`（鍵 `tenant_id`＋`employment_id`，`$inc`），讓同一段僱傭關係的兩個交易互相衝突，衝突的重試（D-05）。
- **觸發的連鎖在同一交易**：只影響一段僱傭關係的動作，觸發的 ReassessLeaveEntitlements、RejudgeLeaveYearEnd、補做的 GrantLeaveEntitlement 與 CloseLeaveYear、NotifyLeaveReassessment，和那個動作在同一個交易中完成；回應帶 `reassessment_notice_ids[]`（有產生時）（D-04）。
- **雇主層級的動作分批**：公司規定的訂定、改版、修訂、廢止，公司規定的更正、註銷與撤銷註銷，雇主的 `system_managed_from`、`labor_standards_act_applicable` 改變，會影響這個雇主的每一段僱傭關係。動作本身的交易：寫它自己、拿同一雇主的公司規定鎖，並對每一段受影響的僱傭關係**更新它的 `leave_locks`**、新增一筆 `leave_reassessment_queue`；所以同時進行的任何一段的交易（人或排程）都會和它衝突、重試，不會讀到舊的公司規定（X-11）。之後每一段各用一個交易重新判定。**任何會寫入某段僱傭關係的交易（人的動作、排程、core 事件的連鎖）都在同一交易先處理它還沒處理的佇列項目**（X-10）；處理失敗的項目記失敗次數與錯誤，列入待處理清單，那一段的查詢標 `reassessment_pending`（X-13）（D-18）。
- **註銷與撤銷註銷依事件重算**：被註銷的事件不參加，依其餘事件重算受影響文件的屬性與狀態，寫成新的版本（A）或覆寫並記 `change_log`（B），版本的 `event_id` 指到那次 AnnulEntry 或 RevokeAnnulment；不是只把某一份文件標成 `annulled`。例：告知被註銷後，就地更正產生的較新版本也不再帶那個告知日。對被註銷事件所登錄的值做過的 CorrectRecord 跟著那個事件一起不算。撤銷註銷等於重新做一次那個動作，照原動作的驗證（R72、R73、R80、R97、R98、「還沒有告知日」），不通過就擋下（同 core R04 把 RevokeAnnulment 列入檢查，X-17）（D-17）。
- **一筆一筆的狀態前提**：會改變狀態的動作，前提條件照 03_flows 狀態機的「從」欄；不在任何一列「從」的狀態一律擋下（例：對 EndedWithEmployment 或 Voided 的那一筆登錄遞延協商）。不改變狀態的動作（RecordLeaveNotice、AmendLeaveDeferral 以外的值登錄）寫在各列（X-19）。
- **回應的警告**：同 hire-employee 的 `warnings[]`（`rule_id`、`rule_version`、`rule_revision`、`message_code`、`subject`、`warned_value`）；04 版本欄為「—」的規則，版本填 `annual-leave-grant/04-v1`、修訂 1（hire-employee D-20 的做法，D-12）。

| 事件 | API | 權限檢查 |
|---|---|---|
| RegisterExistingLeaveEntitlement | `POST /v1/leave-entitlements/backfill` | 人資；R97 擋下 |
| RecordLeaveNotice | `POST /v1/leave-entitlements/{id}/notices` | 人資或雇主（老闆）；只接受依規則給予的法定那一筆（R80），`status` 不是 Voided（離職後才登錄離職前的告知也要收，雇主要舉證，X-19），而且還沒有告知日（已有的只能由人資用 CorrectRecord 改，03_flows D-08）；R98 擋下；回應帶 `recorded_at`，晚登錄看得出來（X-02） |
| RecordLeaveYearAgreement | `POST /v1/leave-year-agreements` | 人資；R72、R98 擋下；適用起日早於已給予的取得日時同一交易 ReassessLeaveEntitlements（R75） |
| EndLeaveYearAgreement | `POST /v1/leave-year-agreements/{id}/end` | 人資；`status`＝Scheduled 或 Effective；R98 擋下 |
| EstablishCompanyPolicy | `POST /v1/company-policies`（含第一版內容） | 人資或雇主（老闆）；R73、R98 擋下；R78、R76 提醒 |
| ReviseCompanyPolicy | `POST /v1/company-policies/{id}/versions` | 人資或雇主（老闆）；`status`＝Scheduled 或 Effective；R73 擋下；R78、R76 提醒。帶 `corrects_version`（登錄錯誤的修訂，不是新版本）只限人資（更正只有人資，03_flows D-08；X-02），已廢止的規定也可以修訂（依它給予的特休可能還在可休，X-15），效果見 D-19。新版本的生效日可以在過去，但不影響已給予的（D-20） |
| RepealCompanyPolicy | `POST /v1/company-policies/{id}/repeal` | 人資或雇主（老闆）；`status`＝Scheduled 或 Effective；R98 擋下；R76 提醒 |
| RecordLeaveDeferral | `POST /v1/leave-deferral-agreements` | 人資；那一筆 `status`＝Active（產生 Agreed）或 YearEnded（產生 Applied），其他擋下（X-08）；R82 擋下；R83、R84 提醒；那一筆已 YearEnded 時同一交易 RejudgeLeaveYearEnd |
| AmendLeaveDeferral | `POST /v1/leave-deferral-agreements/{id}/amend` | 人資；`status`＝Agreed 或 Applied；R82 擋下；R83、R84 提醒；Applied 的同一交易 RejudgeLeaveYearEnd |
| WithdrawLeaveDeferral | `POST /v1/leave-deferral-agreements/{id}/withdraw` | 人資；`status`＝Agreed 或 Applied；R84 提醒；Applied 的同一交易 RejudgeLeaveYearEnd |
| ConfirmLeaveConversion | `POST /v1/leave-conversions/{id}/confirm` | 人資；`status`＝Provisional（已被取代的回 409 並給取代它的 `discarded_by_id`）；確認後寫 `outbox` 交給薪資（D-09） |
| GrantLeaveEntitlement、CloseLeaveYear | 無 API：每日排程（D-03） | 系統；`actor`＝system、`derived`＝true；以雇主所在管轄區的日期判斷「今天」（台灣是 Asia/Taipei）。排程不靠「執行到哪一天」的游標，而是每次對每段僱傭關係找出「到今天應發生而還沒發生」的給予與年度終結（例：晚登錄的到職、更正到過去的可休迄日），補上；補做的年度終結依 R93 待確認（X-04） |
| ActivateLeaveYearAgreement、ActivateCompanyPolicy、ExpireCompanyPolicy | 無 API：每日排程，也在登錄或更正它依據的日期的同一交易中立刻推導 | 系統；同上；日期被更正時舊的標失效、在同一交易重新推導（D-03） |
| ReassessLeaveEntitlements、RejudgeLeaveYearEnd、EndLeaveEntitlementsWithEmployment | 無 API：由觸發它的動作在同一交易中執行（D-04） | 系統；觸發來源見下方「core 事件的連鎖」 |
| NotifyLeaveReassessment | 系統產生；`GET /v1/leave-reassessment-notices?employer_id=&employment_id=&root_event_id=&since=`、`GET /v1/leave-reassessment-notices/{id}`；產生時寫 `outbox`（`LeaveReassessmentNotified`），由平台的通知送到人資與雇主（老闆） | 讀：人資、雇主（老闆）；沒有作廢或修改的 API（D-08）；`root_event_id` 查得到同一次動作連鎖產生的每一份（X-06） |
| CorrectRecord、AnnulEntry、RevokeAnnulment（core） | hire-employee 的 `POST /v1/corrections`、`POST /v1/annulments`、`POST /v1/annulments/{id}/revoke` | 人資；本切片的集合可更正的欄位與可註銷的事件見 2.2（D-11） |
| OverrideWarning、WithdrawWarningOverride（core） | hire-employee 的 `POST /v1/warning-overrides`、`POST /v1/warning-overrides/{id}/withdraw` | 人資；本切片的警告都掛在僱傭關係（`employment_id`），R78 除外（見第三節） |
| （查詢）Q01 某一天有哪幾筆 | `GET /v1/employments/{id}/leave-entitlements?on=&leave_type_code=&as_of=` | 人資、雇主（老闆）；每一筆帶推導的數量、告知期限與告知狀態；`as_of` 查「當時系統知道的」（只看 `recorded_at` 早於它的版本與事件，Q09、Q11） |
| （查詢）一筆的明細與歷史 | `GET /v1/leave-entitlements/{id}?as_of=` | 人資、雇主（老闆）；含各版本（誰、何時、哪個事件改的）、依據的規則版本、轉換、年度終結的判定內容、遞延協商 |
| （查詢）之後各期的預估（US-D01、Q02） | `GET /v1/employments/{id}/leave-forecast?until=` | 人資、雇主（老闆）；現算，不建立請假權利 |
| （查詢）某天適用哪一種特休年度（Q03） | `GET /v1/employments/{id}/leave-year-basis?on=` | 人資、雇主（老闆）；回傳年度種類、起始月日、依約定或預設（附 ref）或都沒有 |
| （查詢）法規警告 | `GET /v1/employments/{id}/leave-warnings` | 人資、雇主（老闆）；現算；已忽略的標出 `warning_override_id`；含 `insufficient_data[]`（R60：缺哪個屬性，例：雇主沒有登錄開始由系統管理的日子） |
| （查詢）待處理清單（跨員工） | `GET /v1/leave-work-items?employer_id=` | 人資、雇主（老闆）；現算，不存：還沒忽略的法規警告、資料不足、待確認的轉換、佇列失敗的僱傭關係；通知中看資料就判斷得出是否仍成立的事（R96 的已休大於額度、作廢那筆上仍有已休，R81 的告知日早於取得日），它們是提醒類規則，可以用 OverrideWarning 忽略。看資料判斷不出處理完沒有的（要重新登錄遞延協商、補登那筆和重算期間重疊或有空檔）不列入，只在通知上（D-08，X-07、X-20） |
| （查詢）轉換（薪資切片與待確認清單） | `GET /v1/leave-conversions?employment_id=&status=&payment_due_before=` | 人資、雇主（老闆）；薪資切片用 `status`＝Determined 讀取（D-09） |
| （查詢）假別（參考資料） | `GET /v1/leave-types` | 任何登入者；只能讀 |
| （查詢）特休年度約定、公司規定 | `GET /v1/leave-year-agreements?employment_id=`；`GET /v1/company-policies?employer_id=&subject=`；`GET /v1/company-policies/{id}` | 人資、雇主（老闆）；公司規定的回應含各版本與 R78 的警告 |
| （固定資料）已休 [靜態替代] | `POST /v1/leave-entitlements/{id}/used-quantity-fixture` | 人資；記誰、何時、理由（事件 `LoadUsedQuantityFixture`）；那一筆已 YearEnded 時同一交易 RejudgeLeaveYearEnd（03_flows 更正方式「已休」）（D-10） |
| （固定資料）一般離職的結束日 [靜態替代] | `POST /v1/employments/{id}/ending-fixture` | 人資；`status`＝Active；core R02 擋下；同一交易 EndLeaveEntitlementsWithEmployment（D-10） |

**core 事件的連鎖**（hire-employee 的 API 在同一交易中呼叫本切片的處理，回應格式不變；D-04）：

| core 事件 | 條件 | 本切片做什麼 |
|---|---|---|
| SignContract | — | 不寫入；R99 的警告在查詢時現算 |
| RecordEarlyDeparture | — | EndLeaveEntitlementsWithEmployment |
| CorrectRecord | `employments` 的 `start_date`、`employee_category`、`ended_on`；`leave_year_agreements` 2.2 中觸發重新判定的欄位 | 同一交易 ReassessLeaveEntitlements（`ended_on` 改早時先 EndLeaveEntitlementsWithEmployment） |
| CorrectRecord、AnnulEntry、RevokeAnnulment | `company_policies` 的 `effective_from`、`effective_to`；EstablishCompanyPolicy、RepealCompanyPolicy | 雇主層級：拿公司規定鎖、經 `leave_reassessment_queue` 分批（D-18；X-12） |
| CorrectRecord | `leave_deferral_agreements`、補登那筆的 `pre_system_used_quantity`、`quantity` | 那一筆已 YearEnded 的 RejudgeLeaveYearEnd |
| AnnulEntry、RevokeAnnulment | 目標是 StartEmployment、RegisterExistingEmployment、RecordEarlyDeparture、`LoadEmploymentEndingFixture`，或本切片可註銷的事件（公司規定的除外，見上一列） | 同一交易 ReassessLeaveEntitlements |
| CorrectRecord、AnnulEntry；固定資料事件 `LoadEmployerFixture` | `employers` 的 `system_managed_from`、`labor_standards_act_applicable`（org-setup 的資料） | 雇主層級：經 `leave_reassessment_queue` 分批（D-18）。這版 org-setup 的雇主資料由平台維運載入（[靜態替代]），載入時寫一筆 `LoadEmployerFixture` 事件，當作 `root_event_id`（X-21；同 D-10 的理由） |
| StartEmployment、RegisterExistingEmployment（到職日在過去） | 到職日到今天之間已有取得日 | 同一交易補上已到的 GrantLeaveEntitlement（與已過的 CloseLeaveYear，待確認），不等排程（X-04） |
| CorrectRecord | 本切片集合的欄位（2.2） | 本切片的驗證（R72、R73、R82、R97、R98）與鎖（僱傭關係的 `leave_locks`；公司規定的用公司規定鎖），由 hire-employee 的更正與註銷 API 在同一交易呼叫本切片（D-04） |

### 2.1 Use Case → API

| UC | 用到的 API |
|---|---|
| UC-01 週年制依年資給予特休 | `GET /employments/{id}/leave-forecast` → 排程給予 → `GET /employments/{id}/leave-entitlements` |
| UC-02 曆年制給予特休 | `POST /leave-year-agreements`（或公司規定的預設）→ 排程給予 → `GET /employments/{id}/leave-warnings` → `POST /warning-overrides` |
| UC-03 公司規定多給特休 | `POST /company-policies` → `POST /company-policies/{id}/versions`、`POST /company-policies/{id}/repeal` → 排程給予 → `GET /employments/{id}/leave-entitlements` |
| UC-04 告知員工排定特休 | `GET /employments/{id}/leave-entitlements` → `POST /leave-entitlements/{id}/notices` |
| UC-05 年度終結：協商遞延，其餘轉為工資 | `POST /leave-deferral-agreements`（`/amend`、`/withdraw`）→ 排程年度終結 → `GET /leave-entitlements/{id}`、`GET /leave-conversions` |
| UC-06 遞延進來的天數到次一年度終結仍沒休 | 排程年度終結 → `GET /leave-conversions` |
| UC-07 補登系統開始管理前就到職的員工的特休 | `POST /leave-entitlements/backfill` |
| UC-08 到職日更正後重新判定特休 | `POST /corrections` → `GET /leave-reassessment-notices` → `POST /leave-entitlements/{id}/used-quantity-fixture`、`POST /leave-entitlements/{id}/notices`、`POST /leave-deferral-agreements` → `POST /leave-conversions/{id}/confirm` |
| UC-09 還沒滿年資或年度終結前離職 | `POST /employments/{id}/early-departure`（hire-employee）或 `POST /employments/{id}/ending-fixture` → `GET /employments/{id}/leave-entitlements` |
| UC-10 員工改用另一種特休年度 | `POST /company-policies/{id}/versions` 或 `POST /leave-year-agreements` → 排程開始適用 → `GET /employments/{id}/leave-year-basis`、`GET /employments/{id}/leave-warnings`；回到預設用 `POST /leave-year-agreements/{id}/end` |
| UC-11 可能應合併年資的警告 | `POST /hires/{id}/start`（hire-employee）→ `GET /employments/{id}/leave-warnings` → `POST /warning-overrides` |
| UC-12 年度終結之後才改變的資料 | `POST /leave-entitlements/{id}/used-quantity-fixture`、`POST /leave-deferral-agreements`（`/amend`、`/withdraw`）、`POST /corrections` → `GET /leave-reassessment-notices` → `POST /leave-conversions/{id}/confirm` |

### 2.2 本切片的集合：可更正的欄位與可註銷的事件（CorrectRecord、AnnulEntry）

hire-employee 05_mapping 2.2 的規定同樣適用（狀態、`tenant_id`、誰與何時、`events`、規則版本不能更正）。`POST /v1/corrections` 可更正的欄位是各切片 2.2 的聯集（D-11）。

| 集合 | 可更正的欄位 | 備註 |
|---|---|---|
| `leave_entitlements` | `origin` 為補登當期、補登遞延的：`source`、`policy_id`、`quantity`、`pre_system_used_quantity`、`valid_from`、`valid_to`、`registered_original_year_end`；任何一筆的 `notified_on` | 依規則給予的額度、期間、取得日、依據不能更正（02 D-07：更正它依據的資料）；R97、R98 擋下；補登那筆的值已 YearEnded 的觸發 RejudgeLeaveYearEnd |
| `leave_year_agreements` | `leave_year_basis`、`year_start`、`effective_from`、`ended_from`、`agreed_on`、`agreement_note` | R72、R98 擋下；前四個觸發重新判定 |
| `leave_deferral_agreements` | `agreed_on`、`deferred_quantity`、`agreement_note` | 只限登錄時打錯；雙方重新談用 `/amend`（03_flows D-06）；R82 擋下 |
| `company_policies` | `name`、`source_note`、`effective_from`、`effective_to` | R73、R98 擋下；生效日、廢止日觸發重新判定（03_flows D-14）。版本內容不能用更正，要新增修訂（`POST /company-policies/{id}/versions` 帶 `corrects_version`，只限人資；修訂的效果見 D-19） |
| `leave_conversions` | （沒有） | 已判定的不能改，記差額（03_flows 更正方式） |

可註銷的事件（03_flows「本切片可以註銷的事件」）：RegisterExistingLeaveEntitlement、RecordLeaveNotice、RecordLeaveYearAgreement、EndLeaveYearAgreement、EstablishCompanyPolicy、RepealCompanyPolicy；固定資料事件 `LoadEmploymentEndingFixture` 也可以註銷（載入錯了）。其他事件 `POST /annulments` 擋下（core R47 的白名單加上這幾種）。

## 三、規則 → 落實位置
<!-- db constraint／db trigger／service／人工；MongoDB 沒有 trigger，「db constraint」指集合的驗證規則與唯一索引（PLAN.md D-35） -->

### 3.1 規則

| 規則 | 落實位置 | 說明 |
|---|---|---|
| R65、R66、R69、R70、R77、R80、R87、R89、R90 | service | 計算；依 `rule_versions` 取當時的版本（R66 依取得日當天有效的天數表；R77 依取得日當天有效的公司規定版本），寫進請假權利或轉換並記版本（P5）。給予不重複：部分唯一索引 `tenant_id`＋`employment_id`＋`leave_type_code`＋`source`＋`policy_id`＋`period_sequence`，條件 `origin`＝依規則給予、`is_current`＝true、`voided`＝false（排程重跑或同時跑不會給兩筆） |
| R67、R68、R75、R85、R88、R91、R95 | service | 判定；資料不足（core R60）時不給予、不判定，列在 `GET /leave-warnings` 的 `insufficient_data`，補登資料後由排程或重新判定補上 |
| R79、R93 | service | 判定；結果「待確認」寫成 `status`＝Provisional 的轉換；R79 找不到版本、R93 的待確認由人資確認（ConfirmLeaveConversion） |
| R86、R92 | service | 計算；在同一交易中把還在待確認的轉換改為 Discarded，記 `discarded_by_id` |
| R72、R73 | service | 跨文件的期間不重疊，擋下；R72 靠 `leave_locks`（僱傭關係）防同時送出；R73 用同一雇主的公司規定鎖（鍵 `tenant_id`＋`employer_id`，只有公司規定的動作用，D-05）。公司規定對各段僱傭關係的影響經 `leave_reassessment_queue`，不和排程搶（D-18） |
| R74 | db constraint ＋ service | 驗證規則：`applied_year_agreement_id`、`applied_year_default_policy_id` 不能同時有值；指到的規定事項是特休年度預設由 service 檢查 |
| R82 | service | 擋下；「同一筆同時最多一筆有效的協商」靠 `leave_locks` 與交易中的查詢；額度上限比較 |
| R97 | db constraint ＋ service | 驗證規則：`valid_to` ≥ `valid_from`、`quantity` > 0、`pre_system_used_quantity` ≤ `quantity`、補登遞延的 `registered_original_year_end` < `valid_from`；和到職日、開始由系統管理的日子比較由 service 檢查 |
| R98 | db constraint ＋ service | 同一文件內的（公司規定 `effective_to` ≥ `effective_from`）用驗證規則；和到職日、登錄當天比較由 service 檢查 |
| R71、R76、R81、R83、R84、R94、R96、R99 | service | 法規警告與提醒，只提醒：查詢時現算（由日期到達才成立的 R81、R94 每次查詢依今天判定），也在觸發它的動作回應的 `warnings[]`；可用 OverrideWarning 忽略（掛在 `employment_id`），忽略何時失效依 core R51 |
| R78 | service | 提醒；掛在那條公司規定上（`GET /company-policies/{id}` 的 `warnings[]`），沒有對應的員工，不能用 OverrideWarning 忽略（04 R78；D-12） |
| （所有判定與計數） | service | 被註銷、作廢、取代的不算：推導值只算 `status` 不是 Voided 的請假權利、`status`＝Determined 或 Provisional（正數與失效）的轉換（C01，04 D-14）；被註銷的事件依 D-17 重算後已不在文件裡，不另用 `annulled` 排除（作廢的請假權利仍要算它的轉換與負數差額，C01，X-18） |
| C01、C02 | service ＋ P9 | 每次寫入請假權利或轉換後，在同一交易中檢查那一筆的 C01 與那次判定的 C02，不成立就中止交易（回 500 並記錄，是程式錯誤，不是使用者的錯）；P9 的自動測試另外對全部資料檢查 |

### 3.2 參數放在哪裡（P5）

參數名稱與預設值照 04 參數表，不另取名。

| 參數 | 放在 | 說明 |
|---|---|---|
| `statutory_annual_leave_days` | `rule_versions`（R66）`params` | 有版本與生效日（04 R66 v1） |
| `acquisition_day_rule`、`first_period_months` | `rule_versions`（R65）`params` | R69 讀同一份 |
| `leave_year_basis_when_none` | `rule_versions`（R68）`params` | |
| `fixed_start_year_method` | `rule_versions`（R70）`params` | |
| `notice_period_days` | `rule_versions`（R80）`params` | |
| `payment_days_after_year_end`、`payment_deadline_rule` 的預設 | `rule_versions`（R90）`params` | 全部雇主相同（04 參數表）；`payment_deadline_rule` 依雇主的值放 `employer_settings`（04 D-23），這裡只放沒有登錄時的預設 |
| `provisional_review_days` | `rule_versions`（R94）`params` | 同上 |
| `seniority_merge_gap_months` | `rule_versions`（R99）`params` | |
| `company_policy_version_at_year_end` | `rule_versions`（R79）`params` | 全部客戶相同（04 參數表「—」） |
| `company_extra_days`、`company_extra_eligibility`、`company_extra_year_end_treatment`、`company_extra_deferrable`、`company_default_leave_year` | `company_policy_versions.params` | 依公司規定的版本 |
| `wage_payment_day`、`wage_payment_lag_months`、`payment_deadline_rule`（依雇主的值） | `employer_settings`（[靜態替代]） | 依雇主，帶期間 |

## 四、推導值與歷史需求 → 儲存
<!-- 資料身分：事實／快取／凍結快照；保存方式：A／B／C／— -->

| 概念 | 資料身分（P3） | 保存方式（P2） |
|---|---|---|
| LeaveEntitlement | 事實（依規則給予的推導出來之後就是事實，03_flows「狀態怎麼來」） | A：需要重建當時（03_flows，Q01、Q09、Q10、Q11），影響錢與法規 |
| LeaveDeferralAgreement | 事實 | A：需要重建當時（Q05、Q06），雇主負舉證責任 |
| LeaveConversion | 事實 | A：需要重建當時（Q05、Q08、Q11），交給薪資 |
| CompanyPolicy | 事實 | A：需要重建當時（Q09、Q10） |
| 公司規定的版本（`company_policy_versions`） | 事實（規則資料） | A：只新增修訂（P5） |
| LeaveYearAgreement | 事實 | B：需要軌跡（Q03、Q14）；給予時依哪一種已凍結在請假權利上 |
| LeaveType（`leave_types`） | 事實（全平台參考資料） | C：只需現況（03_flows LeaveType，Q01）；停用只改 `status`，不刪除 |
| 重新判定的通知（`leave_reassessment_notices`） | 事實 | A |
| 年度終結的判定內容（`events.payload.year_end`） | 事實 | A（`events` 只新增） |
| 已休的固定資料（`leave_used_quantity_fixtures`）[靜態替代] | 事實 | B：改正要記誰、何時、理由（03_flows D-15） |
| 工資給付日的固定資料（`employer_settings`）[靜態替代] | 事實 | C：已判定的發給期限凍結在轉換上，不需要回頭查當時的給付日；monthly-payroll 定義後依它的歷史需求重新決定 |
| 各集合的 `status`、`voided`、`discarded_by_id` | 快取：依 `events`（排除被註銷、已失效的）重算 | —；P9 要求砍掉重算結果一致 |
| 還可以休、已休、遞延出去、轉為工資、失效（`remaining_quantity` 等） | 推導值：不存，現算 | —（D-06） |
| 告知期限（`notice_due_on`）、告知狀態 | 推導值：不存，現算 | — |
| 某天適用哪一種特休年度 | 推導值：不存，現算；給予時的結果凍結在請假權利上 | — |
| 之後各期的預估 | 推導值：不存，現算 | — |
| 年資（`Employment.seniority`） | 推導值：不存，現算；給予時的結果凍結在 `basis_seniority` | — |
| 法規警告（R71、R76、R78、R81、R83、R84、R94、R96、R99） | 推導值：不存，現算；被忽略的記在 WarningOverride | — |

**A 只新增的做法**：同 hire-employee 05_mapping 第四節（`entity_id`、`revision`、`supersedes`、`is_current`、`recorded_at`、`event_id`）。就地更正（R91）是同一個 `entity_id` 的新版本，`event_id` 指到那次 ReassessLeaveEntitlements，所以「更正前給了什麼、誰在什麼時候改的」（Q11）由版本與事件查得到。

**P7 刪除與遮蔽**：本切片的集合只存 `employment_id` 等參照，不存姓名、證號；請假權利、轉換是業務事實，保留。自由文字（`agreement_note`、`source_note`、`reason`、`evidence[]`）依 hire-employee 05_mapping 第四節的方式遮蔽（附件只存參照）。

### 既有資料（P12）

| 改動 | 受影響的集合或表 | 未知怎麼表示 | 補值的動作與負責人 |
|---|---|---|---|
| 本切片上線時，已經在職的僱傭關係沒有任何請假權利 | `employments`（只讀）、`leave_entitlements`（新集合） | 不需要表示：取得日早於雇主開始由系統管理的日子的，由人補登（R67、R97）；之後到上線前已到的取得日，排程第一次執行時補上（D-03） | 系統（排程）補給予；補給予後可休迄日已過的，補做年度終結，轉換待確認（R93），人資確認；人資補登開始管理前的（RegisterExistingLeaveEntitlement） |
| 雇主沒有登錄 `system_managed_from` 或 `labor_standards_act_applicable` | `employers`（org-setup [靜態替代]） | 欄位不存在＝未知；給予的判定為資料不足（R67 決策表、core R60），不當成否 | 由 org-setup 補登雇主資料（這版平台維運載入固定資料）；補上後依 core 事件的連鎖重新判定 |

其他：本切片新增的集合在 hire-employee 的開發資料庫中都還沒有資料；hire-employee 的集合沒有新增欄位。

## 五、技術欄位與平台表

| 表或欄位 | 用途 |
|---|---|
| `_id`、`tenant_id`（`company_policies` 的是業務關係）、`entity_id`、`revision`、`supersedes`、`is_current`、`event_id`、`created_at`、`updated_at`、`schema_version` | [技術] 同 hire-employee 05_mapping 第五節 |
| `voided`（`leave_entitlements`） | [技術] 快取：`status`＝Voided 時為 true；部分唯一索引用（MongoDB 的部分索引不能用「不等於」） |
| `discarded_by_id`（`leave_conversions`） | [技術] 快取：取代它的那一筆，由 RejudgeLeaveYearEnd、ReassessLeaveEntitlements 的事件推出 |
| `leave_locks` | [技術] 平台表：同一段僱傭關係（或同一雇主的公司規定）的同時寫入保護（D-05） |
| `leave_reassessment_queue` | [技術] 平台表：雇主層級的改變要重新判定的僱傭關係，`employment_id`、`root_event_id`、`reason`、`processed_at`、`attempts`、`last_error`；任何寫入那一段的交易先清它的佇列（D-18） |
| `outbox` | [技術] 平台表：確認或直接判定的轉換以 `LeaveConversionDetermined`（只帶 `conversion_id`、`employment_id`）發給薪資切片（D-09） |
| 排程的執行紀錄（`job_runs`） | [技術] 平台表：每次執行的時間與處理了哪些僱傭關係，供維運查；排程不靠它決定要補哪幾天（X-04） |
| `x-concept`（OpenAPI）、集合驗證規則的 `description` | [技術] P8：標出對應的概念 ID |

## 六、Use Case 走一遍
<!-- 照每個正式 Use Case 的步驟依序對到 API。從哪裡來：使用者輸入／登入身分／第 n 步回應的 <欄位>／查詢 <API>；
     來自回應的欄位，api.yaml 該 API 的回應格式要有 -->

| Use Case | 步驟 | API | 需要的輸入 | 從哪裡來 |
|---|---|---|---|---|
| UC-01 | 1 | `GET /v1/employments/{id}/leave-forecast?until=` | employment_id、until | employment_id：hire-employee `POST /hires/{id}/start` 回應的 `employment_id`；until：使用者輸入 |
| UC-01 | 2 | （排程 GrantLeaveEntitlement） | — | 系統；依 `employments.start_date` 與 R65～R69 |
| UC-01 | 3 | `GET /v1/employments/{id}/leave-entitlements?on=` | employment_id、on | employment_id：同第 1 步；on：使用者輸入或今天；回應每一筆的 `entitlement_id`、`notice_due_on`、`notice_status` 帶到 UC-04 |
| UC-01 | 4、5 | 同第 2、3 步（每個週年）；年度終結見 UC-05 | — | — |
| UC-02 | 1 | `POST /v1/leave-year-agreements` | employment_id、leave_type_code、leave_year_basis、year_start、effective_from、agreed_on、agreement_note | employment_id：同 UC-01；leave_type_code：查 `GET /v1/leave-types`（參考資料）；其餘使用者輸入；回應 `leave_year_agreement_id`、`status`、`warnings` |
| UC-02 | 2 | （排程 ActivateLeaveYearAgreement、GrantLeaveEntitlement） | — | 系統 |
| UC-02 | 3 | `GET /v1/employments/{id}/leave-warnings` | employment_id | 同第 1 步；R71 的警告帶 `rule_id`、`rule_version`、`rule_revision`、`subject`、`warned_value` |
| UC-02 | 4 | hire-employee `POST /v1/warning-overrides` | rule_ref、subject_ref、warned_value、employment_id、reason | 第 3 步回應的 `warnings[]`；reason 使用者輸入 |
| UC-03 | 1 | `POST /v1/company-policies` | employer_id、leave_type_code、name、subject、source_note、effective_from、first_version（params） | employer_id：查 org-setup（雇主清單）；其餘使用者輸入；回應 `policy_id`、`version`、`status`、`warnings`（R78） |
| UC-03 | 2 | （排程 ActivateCompanyPolicy、GrantLeaveEntitlement） | — | 系統；公司多給的那一筆另成一筆 |
| UC-03 | 3 | `GET /v1/employments/{id}/leave-entitlements` | employment_id | 回應每一筆的 `source`、`policy_id`、`basis_rule_versions` |
| UC-03 | 例外 | `POST /v1/company-policies/{id}/versions`；`POST /v1/company-policies/{id}/repeal`；hire-employee `POST /v1/corrections` | policy_id、effective_from、params；effective_to；subject（`company_policies`、policy_id、`effective_from`）、new_value、reason | policy_id：第 1 步回應的 `policy_id`；更正後的重新判定用回應的 `event_id` 查 `GET /leave-reassessment-notices?root_event_id=` |
| UC-04 | 1 | `GET /v1/employments/{id}/leave-entitlements` | employment_id | 回應的 `notice_due_on`、`notice_status` |
| UC-04 | 2、3 | `POST /v1/leave-entitlements/{id}/notices` | entitlement_id、notified_on、evidence | entitlement_id：第 1 步回應的 `entitlement_id`；其餘使用者輸入；回應 `notice_status`、`warnings` |
| UC-04 | 例外 | `GET /v1/employments/{id}/leave-warnings` → hire-employee `POST /v1/warning-overrides`；`POST /v1/corrections`（`notified_on`） | — | 警告來自 `GET /leave-warnings` 回應；更正的 subject.id＝entitlement_id |
| UC-05 | 1、2 | `POST /v1/leave-deferral-agreements` | entitlement_id、agreed_on、deferred_quantity、agreement_note | entitlement_id：UC-01 第 3 步回應的 `entitlement_id`；其餘使用者輸入；回應 `deferral_agreement_id`、`status`、`warnings` |
| UC-05 | 3 | （排程 CloseLeaveYear） | — | 系統；產生遞延進來的一筆與轉換 |
| UC-05 | 4 | `GET /v1/leave-entitlements/{id}` | entitlement_id | 回應的 `year_end_judgments[]`（`deferred_in_entitlement_id`、`conversion_ids`）、`conversions[]` |
| UC-05 | 5 | `GET /v1/leave-conversions?status=Determined` | employment_id 或 payment_due_before | 薪資切片；回應 `conversion_id`、`quantity`、`wage_basis_date`、`payment_due_on`；也由 `outbox` 收到 |
| UC-05 | 例外 | `POST /v1/leave-deferral-agreements/{id}/amend`；`/withdraw` | deferral_agreement_id、agreed_on、deferred_quantity、reason | 第 1 步回應的 `deferral_agreement_id` |
| UC-06 | 1 | （排程 CloseLeaveYear） | — | 系統；遞延進來的那一筆全部轉為工資，`wage_basis_date` 是原年度終結日 |
| UC-06 | 2 | `GET /v1/leave-conversions?employment_id=` | employment_id | 同 UC-01 |
| UC-06 | 例外 | `POST /v1/leave-deferral-agreements` | entitlement_id（遞延進來的那一筆） | R82 擋下，回 409（Blocked，`rule_id`＝R82） |
| UC-07 | 1、2 | `POST /v1/leave-entitlements/backfill` | employment_id、leave_type_code、source、policy_id、origin、quantity、unit、pre_system_used_quantity、valid_from、valid_to、registered_original_year_end | employment_id：hire-employee `POST /employments/backfill` 回應的 `employment_id`；其餘人資依雇主原有的紀錄輸入；policy_id：`GET /company-policies` 回應；回應 `entitlement_id`（每次一筆） |
| UC-07 | 3 | （排程 GrantLeaveEntitlement） | — | 系統；取得日不早於開始由系統管理的日子的才給予 |
| UC-07 | 例外 | hire-employee `POST /v1/corrections`、`POST /v1/annulments` | subject.id 或 target_event_id | entitlement_id：第 1 步回應；target_event_id：第 1 步回應的 `event_id` |
| UC-08 | 1、2 | hire-employee `POST /v1/corrections` | subject（`employments`、employment_id、`start_date`）、new_value、reason、evidence | employment_id：同 UC-01；其餘使用者輸入；同一交易執行重新判定，回應的 `event_id` 是 CorrectRecord |
| UC-08 | 3 | `GET /v1/leave-reassessment-notices?root_event_id=` | root_event_id | 第 1 步回應的 `event_id`（hire-employee 的回應不變，所以用它查，D-04）；可能回好幾份（結束日改早時先停止特休、再重新判定）；每份回應 `notice_id`、`changed[]`、`provisional_conversion_ids[]`、`action_items[]` |
| UC-08 | 4 | `POST /v1/leave-entitlements/{id}/used-quantity-fixture`；`POST /v1/leave-entitlements/{id}/notices`；`POST /v1/leave-deferral-agreements` | entitlement_id、used_quantity、reason；notified_on；agreed_on、deferred_quantity | entitlement_id：第 3 步回應的 `action_items[].entitlement_id`；其餘人資輸入 |
| UC-08 | 5 | `POST /v1/leave-conversions/{id}/confirm` | conversion_id、reason | 第 3 步回應的 `provisional_conversion_ids`（或第 4 步回應的 `reassessment_notice_ids` 對應的新通知；被取代的回 409 並給 `discarded_by_id`） |
| UC-09 | 1 | hire-employee `POST /v1/employments/{id}/early-departure`，或 `POST /v1/employments/{id}/ending-fixture` | employment_id、ended_on、end_reason | employment_id：同 UC-01；其餘使用者輸入；同一交易 EndLeaveEntitlementsWithEmployment |
| UC-09 | 2 | `GET /v1/employments/{id}/leave-entitlements` | employment_id | 回應每一筆的 `status`（EndedWithEmployment、Voided） |
| UC-09 | 例外 | `GET /v1/leave-reassessment-notices?employment_id=` → `POST /v1/leave-conversions/{id}/confirm` | conversion_id | 通知的 `provisional_conversion_ids`；結束被註銷：hire-employee `POST /v1/annulments`（target_event_id＝第 1 步回應的 `event_id`） |
| UC-10 | 1 | `POST /v1/company-policies/{id}/versions`（事項為特休年度預設）或 `POST /v1/leave-year-agreements` | policy_id、params.company_default_leave_year；或 employment_id、leave_year_basis、year_start、effective_from、agreed_on | policy_id：`GET /company-policies?subject=` 回應；回應 `warnings`（R76：還在套用預設的每位員工） |
| UC-10 | 2 | （排程 ActivateLeaveYearAgreement） | — | 系統 |
| UC-10 | 3 | `GET /v1/employments/{id}/leave-year-basis?on=` | employment_id、on | 回應 `leave_year_basis`、`year_start`、`applied_by`（約定／預設／都沒有）、`leave_year_agreement_id` 或 `policy_id` |
| UC-10 | 例外 | `POST /v1/leave-year-agreements/{id}/end`；`GET /v1/employments/{id}/leave-warnings` | leave_year_agreement_id、ended_from、agreed_on | 第 1 步回應的 `leave_year_agreement_id` 或 `GET /leave-year-agreements` 回應 |
| UC-11 | 1 | hire-employee `POST /v1/hires/{id}/start` | — | 同 hire-employee UC-01 |
| UC-11 | 2 | `GET /v1/employments/{id}/leave-warnings` | employment_id | 第 1 步回應的 `employment_id`；R99 的警告 |
| UC-11 | 3 | hire-employee `POST /v1/warning-overrides` | rule_ref、subject_ref、warned_value、employment_id、reason | 第 2 步回應的 `warnings[]` |
| UC-12 | 1 | `POST /v1/leave-entitlements/{id}/used-quantity-fixture`、`POST /v1/leave-deferral-agreements`（`/amend`、`/withdraw`）、hire-employee `POST /v1/corrections` | entitlement_id 或 deferral_agreement_id；改正的值 | entitlement_id：UC-01 第 3 步回應；deferral_agreement_id：UC-05 第 1 步回應；回應 `reassessment_notice_ids`、`warnings`（R84） |
| UC-12 | 2 | `GET /v1/leave-reassessment-notices/{id}` 或 `?root_event_id=` | notice_id 或 root_event_id | 第 1 步回應的 `reassessment_notice_ids`（corrections 用回應的 `event_id` 當 root_event_id 查） |
| UC-12 | 3 | `POST /v1/leave-conversions/{id}/confirm` | conversion_id | 第 2 步回應的 `provisional_conversion_ids` |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 | 提出／同意 |
|---|---|---|---|---|---|
| D-01 | 每個 Entity 一個集合（同 hire-employee D-02）；公司規定的版本內容另放 `company_policy_versions`（客戶內的規則資料），不放平台共用的 `rule_versions` | 版本嵌在 `company_policies` 裡；放進 `rule_versions` 加 `tenant_id` | 請假權利與轉換要指到「哪一條規定的哪一版」（Q09、Q10），版本要能單獨被指到；`rule_versions` 是平台管理者維護、不分客戶的（hire-employee 05_mapping 1.1），混進客戶資料會讓權限與隔離變複雜 | 02「不是 Entity」公司規定的版本；P5；Q09、Q10 | AI／JiHungLin（2026-10-21） |
| D-02 | 04 參數表的參數：「依什麼條件變化」為「—」的放 `rule_versions` 中用到它的規則的 `params`；依公司規定版本的放 `company_policy_versions.params`；工資給付日放 `employer_settings`（[靜態替代]）。名稱照 04，不另取 | 另立一個參數集合 | hire-employee 已把金額與分級表放在 `rule_versions.params`（hire-employee 05_mapping 1.1），沿用；docs/02 ⑤ 要求參數名稱照 ④ | docs/02 ⑤；P5；hire-employee 05_mapping | AI／JiHungLin（2026-10-21） |
| D-03 | 給予、年度終結、約定開始適用、公司規定生效與廢止由每日排程執行，「今天」以雇主所在管轄區的日期判斷；漏跑的日子下次補（含本切片上線前已到的取得日）。給予與年度終結的事件推導出來就是事實，依據改了不標失效，由重新判定記改變；約定與公司規定的生效、廢止照 hire-employee D-12 標失效、重新推導 | 全部照 hire-employee D-12；請假權利當成快取每次重算 | 03_flows「狀態怎麼來」規定給予與年度終結的結果是事實，更正前的內容要保留（Q11）；照 D-12 標失效會把已交給薪資的轉換也一起推翻 | 03_flows「狀態怎麼來」、D-04、D-11；hire-employee D-12 | AI／JiHungLin（2026-10-21） |
| D-04 | 觸發本切片的 core 事件（更正到職日、員工類型、結束日，註銷到職或結束，到職後立刻離開）在 hire-employee 的 API 同一交易中執行本切片的重新判定；hire-employee 的 api.yaml 不改，人資用回應的 `event_id` 查重新判定的通知 | 經 `outbox` 非同步處理 | 非同步時，更正到判定完成之間排程可能用舊的到職日做年度終結，交給薪資後只能記差額；同一交易才能保證「更正」與「重新判定」一起成立或一起失敗。代價是 hire-employee 的實作要加呼叫本切片的掛勾：重新判定、本切片集合的驗證（R72、R73、R82、R97、R98）與 `leave_locks`（實作的改動，不改 hire-employee 的設計文件；X-05）。雇主層級的改變例外，改走 D-18 | 03_flows 事件表 ReassessLeaveEntitlements、EndLeaveEntitlementsWithEmployment 的觸發來源；PLAN.md D-35（多文件交易） | AI／JiHungLin（2026-10-21） |
| D-05 | 本切片每個寫入動作（含排程）先鎖同一段僱傭關係（`leave_locks`）；公司規定另鎖同一雇主 | 只在 service 讀取後檢查 | MongoDB 交易是快照隔離，兩個交易各自讀到「沒有其他協商」或排程與人資同時處理同一筆時不會衝突（同 hire-employee D-15 的問題）；例：年度終結判定和登錄遞延協商同時發生 | hire-employee D-15；R72、R73、R82 | AI／JiHungLin（2026-10-21） |
| D-06 | 剩餘、已休、遞延出去、轉為工資、失效、告知期限與告知狀態都不存，查詢時現算 | 存成快取欄位 | 平台約定 P3（PLAN.md D-35）：推導值不存；一位員工同時只有幾筆，現算的成本低；存了就要處理重新判定時的同步 | P3；PLAN.md D-35；02「不是 Entity」 | AI／JiHungLin（2026-10-21） |
| D-07 | 年度終結的判定內容（判定當時已知的已休、依哪一版協商、未休、遞延進來與轉換的編號、是否補做）記在 CloseLeaveYear、RejudgeLeaveYearEnd 的事件 `payload.year_end`，查一筆時一起回傳 | 另立「年度終結判定」集合；記在轉換上 | 未休為 0 或全部遞延時沒有轉換，記在轉換上會缺；04 自評第 7 條已說這些取自事件紀錄；`events` 只新增，之後改正已休不會蓋掉（03_flows D-15） | 03_flows D-15；04 自評第 7 條 | AI／JiHungLin（2026-10-21） |
| D-08 | 重新判定的通知存成 `leave_reassessment_notices`，沒有作廢或修改的 API；要人處理的事列成 `action_items`（代碼只在 ⑤ 使用）；處理完不在通知上打勾，看資料本身是否已改正 | 和 hire-employee 的可作廢建議共用 `proposals` | 03_flows 事件表：不可作廢；03 沒有「處理完」的事件，加了就是新的狀態機 | 03_flows 事件表 NotifyLeaveReassessment；hire-employee D-07 | AI／JiHungLin（2026-10-21） |
| D-09 | 轉換交給薪資：直接判定與確認後的轉換寫一筆 `outbox`（`LeaveConversionDetermined`），薪資切片也可以用 `GET /leave-conversions?status=Determined` 查；怎麼消化由 monthly-payroll 決定 | 本切片直接建立薪資項目 | 金額與發放屬 monthly-payroll（01_scope 不做）；PayItem 會引用轉換（02 LeaveConversion 卡） | 01_scope 範圍外但會用到；02 LeaveConversion | AI／JiHungLin（2026-10-21） |
| D-10 | 三個 [靜態替代]：已休用 `leave_used_quantity_fixtures`＋API（改正後已年度終結的同一交易重新判定）；一般離職的結束日用 `POST /employments/{id}/ending-fixture` 寫固定資料事件，產生新版本的 `employments`；工資給付日用 `employer_settings`，由平台維運載入、沒有 API | 都由平台維運直接寫資料庫 | 03_flows 更正方式要求已休的改正記誰、何時、理由，並觸發重新判定；結束日的載入要觸發停止特休，直接寫資料庫會繞過 P1 與連鎖。工資給付日只在判定時讀一次、結果凍結在轉換上 | 01_scope 範圍外但會用到；03_flows 更正方式「已休」、EndLeaveEntitlementsWithEmployment；P1 | AI／JiHungLin（2026-10-21） |
| D-11 | 更正與註銷沿用 hire-employee 的 API，本切片的集合可更正的欄位與可註銷的事件寫在本切片 2.2，`POST /corrections` 的白名單是各切片 2.2 的聯集；特休年度約定的終止日放在約定上（`ended_from`），才能更正 | 改 hire-employee 05_mapping 的 2.2 表；終止日只記在事件上 | CorrectRecord、AnnulEntry 是 core 的事件，只有一支 API；各切片自己的集合由自己列，不必回頭改 hire-employee 已凍結的對照表。03_flows 更正方式要求終止日可以更正，`events` 不能更正（hire-employee 2.2） | 03_flows 更正方式、可註銷的事件；hire-employee 05_mapping 2.2 | AI／JiHungLin（2026-10-21） |
| D-12 | 法規警告查詢時現算，也在觸發它的動作回應；格式與版本照 hire-employee D-20（版本欄「—」的規則填 `annual-leave-grant/04-v1`、修訂 1）；R78 掛在公司規定上，不能忽略 | 存成警告集合 | P3：推導值不存（02「不是 Entity」法規警告）；hire-employee 已定好警告格式與忽略的方式 | hire-employee D-20；04 R78；02 D-16 | AI／JiHungLin（2026-10-21） |
| D-13 | 假別放全平台共用的 `leave_types`，用代碼指它，保存方式 C | 每個客戶一份；用 B 留變更紀錄 | 法令訂定的假別是全平台參考資料（02 D-10、D-15）；03 標只需現況（Q01 只問哪一種假）。公司自訂的假別之後的切片再決定（03_flows LeaveType） | 02 LeaveType 卡、D-10、D-15；03_flows LeaveType；P2 | AI／JiHungLin（2026-10-21） |
| D-14 | 數量一律用 Decimal128 | 整數（台灣法定特休以日計） | 單位可能是小時（02 LeaveEntitlement.unit、D-09），補登與公司多給可能有半日；用整數之後要改型別等於改既有資料（P12） | 02 LeaveEntitlement.unit；P12 | AI／JiHungLin（2026-10-21） |
| D-15 | 查詢權限：人資與雇主（老闆）；員工自己查特休這版不設計 | 員工可以查自己的 | 本切片的 Use Case 參與者沒有員工查詢；員工看自己的特休與請假一起，歸 annual-leave-request | 03_use_cases 參與者；01_scope 不做（請特休） | AI／JiHungLin（2026-10-21） |
| D-16 | 請假權利與它的明細查詢可以帶 `as_of`，只看那個時間以前登錄的版本與事件 | 只回傳目前的版本 | Q11「更正前給了什麼」、Q09「依哪一版」要回答得出當時系統知道的（同 hire-employee applicability 的 `as_of`） | Q09、Q11；hire-employee X-13 | AI／JiHungLin（2026-10-21） |
| D-17 | 註銷與撤銷註銷：依其餘事件重算受影響的文件，寫成新版本（A）或覆寫並記 `change_log`（B），版本的 `event_id` 指到註銷事件；本切片的集合不靠 hire-employee D-11 的文件層級 `annulled` 標記來排除。對被註銷事件的值做過的更正一起不算；撤銷註銷照原動作的驗證，不通過擋下 | 沿用 hire-employee D-11：被註銷的事件建立的文件標 `annulled` | 本切片的文件會被之後的事件再改（就地更正、告知、終止），被註銷的效果會跟著新版本帶下去；B 的約定終止與 A 的廢止沒有一份「由那個事件建立」的文件可以標（X-01）。撤銷註銷不驗證時，註銷 → 重新登錄 → 撤銷註銷就能讓同一天有兩筆約定、一筆特休有兩個告知日（X-17） | X-01、X-17、X-18；03_flows 可註銷的事件；hire-employee D-11；core R04 | AI／JiHungLin（2026-10-21） |
| D-18 | 影響整個雇主的改變（公司規定的訂定、改版、修訂、廢止、更正、註銷，雇主的判定條件）分批：動作的交易寫自己、拿公司規定鎖、更新每段受影響僱傭關係的 `leave_locks` 並各寫一筆 `leave_reassessment_queue`；每段各用一個交易重新判定；任何寫入某段的交易先清它的佇列；失敗的列入待處理清單 | 一個交易做完全部；經 `outbox` 非同步、不保證順序 | 雇主有上千位員工時，一個交易做完全部重新判定會超過 MongoDB 交易的時間與大小限制；非同步又可能讓排程用舊資料先做年度終結（X-05）。只寫佇列不鎖時，快照隔離下排程仍會讀到舊規定（X-11）；只有排程先清佇列時，人的動作仍用舊資料判定、確認轉換（X-10）；佇列卡住沒人看得到時那一段永遠不給（X-13） | X-05、X-10、X-11、X-12、X-13；D-04、D-05；PLAN.md D-35 | AI／JiHungLin（2026-10-21） |
| D-19 | 公司規定版本的「修訂」（`corrects_version`，登錄錯誤）和「新版本」（改版）分開：改版不影響已給予的（Q10、02 D-03）；修訂是依據更正，經 D-18 的佇列對那條規定涵蓋的每段僱傭關係重新判定：取得日落在那一版有效期間的（含因修訂才符合條件、原本沒給的）重新判定，已年度終結的依修訂後的年度終結處理重新判定年度終結，`correction_cause` 為依據更正；已廢止的規定也可以修訂。已回頭修改第 ③ 步（03_flows D-16）與第 ④ 步（04_rules D-22、R91、R92） | 修訂也不影響已給予的，只成立警告；不允許修訂，只能改版 | 03_flows 更正方式把「版本內容登錄錯誤」交給第 ④ 步，④ 沒有寫；打錯 5 天實際 3 天時，不重新判定就會一直多給、多發工資，和到職日打錯的處理不一致（X-03）。只看「依那一版給予的」會漏掉適用對象打錯而沒給的、年度終結處理打錯而額度沒變的（X-15） | X-03、X-15；03_flows 更正方式「公司規定」列、CompanyPolicy 說明；02 D-03 | AI／JiHungLin（2026-10-21） |
| D-20 | 重新判定時公司規定的版本：取得日沒有改變的那一筆，沿用 `basis_rule_versions` 記的版本；取得日改變了，才依新取得日當天有效、而且在原本那次給予之前已經登錄的版本（R77 的「取得日當天有效」在重新判定時的解讀）。新版本的生效日可以在過去，但不會因為之後別的更正而套用到已給予的 | 一律依新取得日當天有效的版本；擋下生效日在過去的新版本 | 老闆新增一版回溯的、天數較少的規定時，當下沒有效果，之後人資更正某人的到職日就被順便套用，等於繞過「修訂只限人資」與「改版不影響已給予的」（X-16）；公告晚登錄是真實情況，不宜擋下。這是對 ④ R77 的解讀，凍結前若要寫進 ④，同 D-19 一起回頭 | X-16；04 R77；02 D-03；Q10 | AI／JiHungLin（2026-10-21） |
| D-21 | 〔2026-10-21，04 D-23〕發給期限的做法與「給付日發哪一期」放在 `employer_settings`（依雇主、帶期間，[靜態替代]），沒有登錄時用 `rule_versions`（R90）的預設；判定時算出的 `payment_due_on` 凍結在轉換上，之後雇主改設定不影響已判定的 | 放 `rule_versions` 全部雇主相同（原寫法）；放公司規定（`company_policy_versions`） | 04 D-23 改為雇主擇一；公司規定是多給特休的內容，發給期限屬薪資，monthly-payroll 定義後一起搬過去較單純；已判定的不變（02 X-14） | 04 D-23；inputs/drafts/特休未休工資發給期限.md | AI／JiHungLin（2026-10-21） |
| D-22 | 〔2026-10-21，04 D-25〕重新判定的通知 `action_items[].kind` 新增 `NOTICE_ACTION.CONVERSION_DATES_CHANGED`：已判定轉換的工資計算基準日或發給期限依新依據會不同時列出，`entitlement_id` 指那一筆，`detail` 記轉換編號與原 → 新；已判定的轉換不改 | 改已判定轉換的日子；另記一筆天數 0 的轉換 | 已判定的轉換已交給薪資（02 X-14 凍結使用）；通知是只新增的紀錄，查得到、人處理 | 04 D-25；06_evidence GC04 | AI／JiHungLin（2026-10-21） |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|
| X-01 | 註銷用文件層級的 `annulled` 撐不住：被註銷的告知日會跟著就地更正的新版本留下來；約定（B）的終止、公司規定的廢止沒有一份由那個事件建立的文件可以標 | AI 挑錯 | 接受，已修改 | D-17；第二節共同的檢查加「註銷與撤銷註銷依事件重算」 |
| X-02 | 雇主（老闆）可以重複呼叫登錄告知覆蓋告知日、用 `corrects_version` 改已生效的加給天數，等於繞過「更正只有人資」 | AI 挑錯 | 接受，已修改 | 登錄告知限還沒有告知日的；`corrects_version` 只限人資（第二節） |
| X-03 | 公司規定版本的修訂（登錄錯誤）對已給予的特休有什麼效果沒有定義，多給的天數與工資永遠不會重新判定 | AI 挑錯 | 接受，已修改 | D-19 提出做法；要回頭補第 ③、④ 步，等人決定 |
| X-04 | 排程靠「執行到哪一天」的游標，晚登錄的到職、更正到過去的可休迄日、約定的起日更正，觸發日已經走過就永遠不給、不終結 | AI 挑錯 | 接受，已修改 | 排程改為每次找「應發生而還沒發生」的；到職與補登的連鎖同一交易補上；約定與公司規定的生效在登錄或更正的同一交易推導（第二節、第五節 `job_runs`） |
| X-05 | 公司規定與排程拿不同的鎖會寫入偏斜（少給加給）；雇主層級的重新判定放進一個交易會超過限制；org-setup 的變化走非同步；經更正 API 改本切片集合時沒寫驗證與上鎖由誰做 | AI 挑錯 | 接受，已修改 | D-18 佇列分批；D-04 補上驗證與上鎖的掛勾；core 事件的連鎖表改寫 |
| X-06 | 通知的 `trigger_event_id` 指重新判定的事件，人資手上只有更正的 `event_id`，查不到；一次動作可能產生好幾份通知 | AI 挑錯 | 接受，已修改 | 通知加 `root_event_id`，查詢可回多份；UC-08、UC-12 改用它 |
| X-07 | 排程產生的待處理事項（待確認、逾期、資料不足、要重新告知）只能逐位員工查，資料不足時特休靜默不給；`notified_to` 沒有送達管道 | AI 挑錯 | 接受，已修改 | 新增 `GET /leave-work-items`（現算）；警告查詢含 `insufficient_data`；通知寫 `outbox` 由平台送達 |
| X-08 | 登錄遞延協商與告知沒寫狀態前提，可以對已作廢或隨離職結束的那一筆登錄 | AI 挑錯 | 接受，已修改 | 第二節共同的檢查加狀態前提；RecordLeaveDeferral、RecordLeaveNotice 寫明可接受的狀態 |
| X-09 | 單一值撐不住：原判定沒有轉換時差額指不回去；已休固定資料只有累計值，`on`、`as_of` 查詢不準；遞延進來那一筆的編號不在判定內容裡 | AI 挑錯 | 接受，已修改 | 轉換加 `corrects_judgment_event_id`；已休固定資料寫明限制與 `as_of` 依 `change_log` 還原；`payload.year_end` 加 `deferred_in_entitlement_id` |
| X-10 | 雇主層級的佇列只有排程會先清：人資改已休、確認轉換、更正到職日仍用舊的公司規定，錢交給薪資後只能記差額 | AI 挑錯 | 接受，已修改 | D-18：任何寫入那一段的交易先清它的佇列 |
| X-11 | 快照隔離下佇列不是鎖：排程交易和公司規定回溯的交易同時進行不衝突，排程照舊規定做年度終結 | AI 挑錯 | 接受，已修改 | D-18：雇主層級的交易更新每段的 `leave_locks` |
| X-12 | core 事件的連鎖表把公司規定的更正、註銷寫成同一交易逐段重新判定，和 D-18 矛盾；更正公司規定時只上僱傭關係的鎖，R73 會被同時的訂定繞過 | AI 挑錯 | 接受，已修改 | 連鎖表拆出公司規定那一列，走佇列並拿公司規定鎖 |
| X-13 | 佇列卡住時那一段每天失敗、永遠不給不終結，而且沒人看得到；查通知分不出「還沒處理」和「沒有改變」 | AI 挑錯 | 接受，已修改 | 佇列記失敗次數與錯誤，列入待處理清單；查詢標 `reassessment_pending` |
| X-14 | 排程延誤一天，正常的年度終結全部變成待確認，要人資逐筆確認，可能拖過發給期限 | AI 挑錯 | 拒絕 | 04 D-20（已同意）：補做的年度終結一律待確認，不看是怎麼來的；排程延誤時偏向安全（不在無人看過時交給薪資），延誤本身屬平台可用性（P13）。是否改 R93 讓排程延誤照正常處理，列入回報請人決定 |
| X-15 | D-19 只重新判定依那一版給予的：適用對象打錯而原本沒給的、年度終結處理打錯而額度沒變的、年度預設打錯的都漏掉；已廢止的規定不能修訂 | AI 挑錯 | 接受，已修改 | D-19 擴大範圍；已廢止的也可以修訂（仍待人決定） |
| X-16 | 老闆新增回溯的新版本，之後別的更正觸發重新判定時被順便套用到已給予的，繞過修訂只限人資 | AI 挑錯 | 接受，已修改 | D-20 |
| X-17 | 撤銷註銷不驗證：註銷 → 重新登錄 → 撤銷註銷，同一天兩筆約定、一筆特休兩個告知日；被註銷的告知若被更正過，重算時算不算沒寫 | AI 挑錯 | 接受，已修改 | D-17：撤銷註銷照原動作驗證；被註銷事件的更正一起不算 |
| X-18 | 3.1、第四節仍用 `annulled` 排除，和 D-17 矛盾；作廢那筆的轉換會被一起漏算，C01 對不上 | AI 挑錯 | 接受，已修改 | 3.1、第四節改寫 |
| X-19 | 登錄告知只接受 Active、YearEnded：離職後才登錄離職前的告知會被擋；RecordLeaveNotice 不改變狀態，套「從」欄規則會整個擋掉 | AI 挑錯 | 接受，已修改 | 狀態前提只用在會改變狀態的動作；登錄告知改為不是 Voided 就收 |
| X-20 | 待處理清單的「近期通知中仍成立」做不到：沒有期限會越積越多，有期限會默默消失；看資料判斷不出處理完的事永遠掛著 | AI 挑錯 | 接受，已修改 | 待處理清單只列看資料判斷得出、可以忽略的提醒；其他只在通知上（D-08） |
| X-21 | org-setup 的雇主資料載入沒有事件，佇列的 `root_event_id` 是空的，也繞過 P1 | AI 挑錯 | 接受，已修改 | 新增固定資料事件 `LoadEmployerFixture` |

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）並列出審查重點；「審查者確認」由非產出者填寫（輸入輸出規範「檢查紀錄」） -->
<!-- CHECKLIST:START -->
### 完成標準（AI 自評）

| 完成標準 | 類 | AI 自評 |
|---|---|---|
| 每個 Entity 都有對應的表，或寫明「不落地」「由靜態參數產生」與理由 | 修正線索 | ✓ 6 個新增 Entity 都有集合（1.1），引用的 core Entity 用 hire-employee 的集合；02 的 45 個屬性都對到欄位或寫明不落地（推導值 6 個），由 AI 用程式比對 02 詞彙表與第一節 |
| 每張業務表、每支 API、每個業務欄位都指得回概念，沒有「多出來、說不出代表什麼」的表；主鍵、建立時間等技術欄位與平台需要的表，標明「技術」即可（平台 P8） | 修正線索 | ✓ 1.2 每個欄位列出對應的概念；`company_policy_versions` 指 02「不是 Entity」的公司規定版本（規則資料）；3 個 [靜態替代] 集合與事件寫明替代哪個切片的什麼；`NOTICE_ACTION.*` 寫明只在 ⑤ 使用；技術欄位與平台表在第五節（AI 比對）。schema.mongo.js 的 description 與 api.yaml 的 x-concept 等對照表確認後產生 |
| ② 標為推導值的東西，都已依平台 P3 決定身分 | 品質檢查 | ✓ 第四節：剩餘、已休、遞延出去、轉為工資、失效、告知期限與狀態、某天的特休年度、預估、年資、法規警告都是「不存，現算」；狀態等為快取（AI 比對 02「不是 Entity」與標 [推導] 的屬性） |
| ③ 標出的歷史需求，都已依平台 P2 決定保存方式 | 關鍵決定 | ✓ 第四節逐項：03 的 6 個狀態機中需要重建當時的 4 個（LeaveEntitlement、LeaveDeferralAgreement、CompanyPolicy、LeaveConversion）為 A；需要軌跡的 LeaveYearAgreement 為 B；只需現況的 LeaveType 為 C；另 2 個 [靜態替代] 集合為 B、C（AI 比對 03 狀態機的歷史需求） |
| ③ 的每個動作與狀態變更都有對應的 API，且符合平台 P1 | 修正線索 | ✓ 03 事件表 20 個事件都在第二節（AI 用程式比對）：人觸發的 11 個各有 API；時間觸發的 5 個由排程產生；其他單位個體觸發的 3 個在觸發它的動作同一交易執行；建議層 1 個有查詢 API。狀態只由事件改變，`status` 不在可更正的欄位（2.2） |
| ④ 的每條規則都已決定落實位置（平台 P6） | 修正線索 | ✓ 第三節 3.1 涵蓋 R65～R99 共 35 條與守恆式 C01、C02（AI 用程式比對；第一次比對漏 R75，已補）；db constraint ＋ service 3 條，其餘 service；沒有「人工」：要人處理的都是規則算出待確認後交給人（R79、R93）。17 個參數的存放位置在 3.2 |
| 每個正式 Use Case 都已在對照表走一遍：每一步的輸入都拿得到；來自前一步回應的，`api.yaml` 該回應有這個欄位 | 品質檢查 | ✓ 第六區 UC-01～UC-12 逐步寫出 API 與輸入來源（AI 用程式確認 12 個都有）；第六區提到的回應欄位都在 api.yaml 該 API 的回應格式中（AI 用程式比對 api.yaml 所有 properties；hire-employee 的回應欄位對照它的 api.yaml）。UC-06 例外改寫為 409 Blocked |
| `api.yaml` 每支 API 的請求與回應都寫到欄位層級，業務欄位對得回對照表第一區；說明（summary）提到的欄位都在格式裡 | 修正線索 | ✓ 26 個操作的請求與回應都是具名 schema（56 個），有 required、巢狀物件的欄位、additionalProperties: false；沒有只寫 type: object 的（AI 用程式檢查，只有 before、after、warned_value 刻意不限）；所有 $ref 都有定義、每個 schema 都有被用到。業務欄位與第一區一致（AI 比對）；summary 提到的告知狀態、期限、推導的數量都在格式中。沒有 OpenAPI 驗證工具可用（openapi_spec_validator 未安裝），結構只由上述程式檢查 |
| 已做紙上驗證：每筆黃金案例依設計推演的結果與人工預期一致；不一致的已回頭修改 | 關鍵決定 | 部分：已推演 GC01、GC04、GC06（JiHungLin 挑選並填預期結果）。GC04 第一次不一致，回頭修改（04 D-25、本檔 D-22）後一致；GC06 一致（推演時發現的告知警告已回頭修改，04 D-24）；GC01 只剩 ② 預期結果那一行的日期待計算者改正（計算過程已是 2025-10-02），③ 依使用者決定情境改回預設 30 日內後一致（由 AI 比對 06_evidence/golden_cases.md） |

### 審查重點（人）

<!-- AI 列出：〔關鍵決定〕要看的清單或位置（精簡版 0.2 的表）、AI 提出的決定、自評為「部分」或 ✗ 的完成標準；抽查那一列由審查者自選，AI 不預選 -->
| # | 要看的 | 在哪裡 | 審查者確認 |
|---|---|---|---|
| 1 | 保存方式選 C（直接覆寫）的項目，和第 ③ 步標「只需現況」的一起看（關鍵決定）：① 假別（`leave_types`）——第 ③ 步標只需現況，全平台共用的參考資料，停用只改狀態不刪除（D-13）；② 工資給付日的固定資料（`employer_settings`）[靜態替代]——發給期限判定時就凍結在轉換上，所以不留舊值；monthly-payroll 正式定義時再決定 | 第四節；D-13、D-10 | ✓ |
| 2 | 〔你已同意，2026-10-21〕公司規定的內容打錯（例：加給打成 5 天，實際是 3 天）後修訂，要不要重新判定已給予的特休？照 D-19 重新判定；已回頭修改第 ③ 步（D-16）與第 ④ 步（D-22），③④ 各有一張差異審查表 | D-19；X-03、X-15 | ✓ |
| 3 | 重新判定時用公司規定的哪一版（D-20）：取得日沒變的那一筆沿用給予時記的版本；老闆新增回溯的新版本，不會因為之後別的更正被順便套用。這是我對第 ④ 步 R77「取得日當天有效的版本」的解讀 | D-20；X-16 | ✓ |
| 4 | **跨切片**：到職日更正、員工類型更正、到職後立刻離開等 hire-employee 的動作，要在同一交易執行特休的重新判定與驗證（D-04）。hire-employee 的設計文件與 API 格式都不改，但它的程式要加呼叫本切片的掛勾；人資用更正回應的 `event_id` 查重新判定的通知 | D-04；第二節「core 事件的連鎖」 | ✓ |
| 5 | 雇主層級的改變（公司規定、雇主資料）分批重新判定，用佇列加鎖避免排程或人資用舊資料判定（D-18）；同一段僱傭關係一次只做一件事（D-05） | 第二節共同的檢查；D-05、D-18；第五節 | ✓ |
| 6 | 註銷改成依其餘事件重算，不再只標記被註銷的文件；撤銷註銷要重新驗證（D-17） | D-17 | ✓ |
| 7 | 排程：每天以雇主所在地的日期，找出「應發生而還沒發生」的給予與年度終結補上；給予與年度終結的結果是事實，依據改了由重新判定記改變（D-03）。拒絕了一個反例（X-14）：排程晚一天跑，年度終結會全部變成待確認，要人資逐筆確認——這是第 ④ 步 D-20（你同意過）的結果，偏安全；要不要改 R93 讓排程延誤照正常處理，由你決定 | D-03；X-14；04 R93、D-20 | ✓ |
| 8 | 三個 [靜態替代]：已休、一般離職的結束日、雇主資料與工資給付日，都用固定資料事件或固定資料集合，記誰、何時、理由並觸發連鎖（D-10） | D-10；1.1；第二節 | ✓ |
| 9 | 其他 AI 提出的決定：D-01 公司規定的版本另放一個集合；D-02 參數放哪裡；D-06 推導值不存；D-07 年度終結的判定內容記在事件上；D-08 通知不可作廢、不設「處理完」；D-09 轉換經 outbox 交給薪資；D-11 更正與註銷沿用 hire-employee 的 API；D-12 警告的格式；D-14 數量用 Decimal；D-15 員工自己查特休這版不做；D-16 查詢可帶 `as_of` | 決定與理由 | ✓ |
| 10 | 自評「部分」：紙上驗證 3 個案例，GC04、GC06 一致（GC04 經回頭修改 D-25），GC01 只剩 ② 預期結果那一行要你改成 2025-10-02；「契約約定的工資給付日」這條發給期限沒有案例驗證，等 EQ-003 答覆後補 | 完成標準第 9 條；06_evidence/golden_cases.md | ✓ |
| 11 | 發給期限改由雇主擇一（04 D-23）：`employer_settings` 多兩個依雇主的值（發給期限的做法、給付日發哪一期），沒有登錄時用預設（D-21） | 1.1 `employer_settings`；3.2；D-21；schema.mongo.js `employer_settings` | ✓ |
| 12 | 紙上驗證後的回頭修改：重新判定的通知多一種要人處理的事（已判定轉換的基準日或發給期限改變，D-22）；告知狀態不判定隨僱傭關係結束、作廢的那一筆（04 D-24，查詢時現算，表與 API 不用改） | D-22；schema.mongo.js、api.yaml 的 `NOTICE_ACTION.CONVERSION_DATES_CHANGED` | ✓ |
| 抽查 | （審查者自選 1～2 條 AI 自評 ✓ 的完成標準，寫出是哪幾條與結果） | `api.yaml` 每支 API 的請求與回應都寫到欄位層級，業務欄位對得回對照表第一區；說明（summary）提到的欄位都在格式裡。  ② 標為推導值的東西，都已依平台 P3 決定身分 | ✓ |
<!-- CHECKLIST:END -->

- 審查者（非產出者）： JiHungLin
- 日期： 20261021
- 結論：通過