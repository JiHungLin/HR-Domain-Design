# hire-employee ⑤ 投影到實作

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ⑤ 投影到實作 |
| 狀態 | 待檢查 |
| 版本 | hire-employee/05-v2（回頭修改中，重新凍結後為 05-v3） |
| 產出者 | AI（Claude）＋ |
| 讀取的輸入 | 02_entities.md @ hire-employee/02-v3（回頭修改中：D-37）；03_flows.md、03_use_cases.md @ hire-employee/03-v3（回頭修改中：D-19）；04_rules.md @ hire-employee/04-v2（回頭修改中：D-15～D-18）；docs/03 平台架構約定（P4、P5、P10 照文件；P1、P2、P3、P6、P7、P8 與資料庫依 PLAN.md D-35；P11 依 PLAN.md D-31） |

<!-- 資料庫為 MongoDB（PLAN.md D-35），本文件的「表」是集合（collection），「欄位」是文件的欄位。
     概念 ID 寫 core/ 的英文識別名稱；技術欄位標 [技術]（P8）。本步先只產出這份對照表，經人確認後才產生 schema.mongo.js 與 api.yaml。 -->

## 一、概念 → 表與欄位

### 1.1 集合

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| Tenant | `tenants` | `name` | org-setup 建立維護，本切片唯讀 [靜態替代] |
| Person | `persons`、`person_contacts` | 見 1.2 | 客戶內一份（P11、PLAN.md D-31）；`persons` 只新增（P2 A），聯絡方式另放 `person_contacts` 直接覆寫（P2 C） |
| IdentityDocument | `identity_documents` | 見 1.2 | 只新增（P2 A） |
| Jurisdiction | `jurisdictions` | `code`、`level`、`parent_id` | 全平台共用參考資料，不分客戶 |
| Employer | `employers` | 見 1.2 | org-setup 建立維護 [靜態替代]；判定條件帶期間 |
| InsuranceUnit | `insurance_units` | `employer_id`、`insurer`、`unit_code`、`established_on`、`scheme_codes` | org-setup [靜態替代]；`insured_headcount_on` 不落地（推導） |
| OrgUnit | `org_units` | `name`、`parent_id`（期間）、`employer_id`（期間） | org-setup [靜態替代] |
| WorkLocation | `work_locations` | `name`、`address`、`jurisdiction_id` | org-setup [靜態替代] |
| Hire | `hires` | 見 1.2 | 覆寫＋變更紀錄（P2 B） |
| Employment | `employments` | 見 1.2 | 只新增（P2 A） |
| EmploymentContract | `employment_contracts` | 見 1.2 | 覆寫＋變更紀錄（P2 B） |
| Compensation | `compensations` | 見 1.2 | 只新增（P2 A）[靜態替代]，monthly-payroll 定義後取代 |
| WorkAuthorization | `work_authorizations` | 見 1.2 | 只新增（P2 A）；每次核准嵌在 `approvals` |
| SocialInsuranceScheme | `social_insurance_schemes` | `jurisdiction_id`、`code`、`insurer`、`effective_from` | 全平台共用參考資料 |
| InsuranceEnrollment | `insurance_enrollments` | 見 1.2 | 只新增（P2 A） |
| InsuredSalary | `insured_salaries` | 見 1.2 | 只新增（P2 A） |
| WarningOverride | `warning_overrides` | 見 1.2 | 覆寫＋變更紀錄（P2 B） |
| PersonalDataArchival | `personal_data_archivals` | 見 1.2 | 覆寫＋變更紀錄（P2 B）；每個類別的解除各記一筆 `releases` |
| DataSubjectRequest | `data_subject_requests` | 見 1.2 | 覆寫＋變更紀錄（P2 B）；延長紀錄嵌在 `extensions` |
| ProposeEnrollmentFiling（事件，建議層） | `enrollment_proposals` | 見 1.2 | 加保待辦是事實（PLAN.md D-35 P3）：判定內容產生後不改；取代、結案、雇主不加自願保險是之後的記錄（P2 B），不刪除 |
| 其他建議層事件：PromptStartConfirmation、ProposeAuthorizationReview、PromptDataSubjectRequestDeadline、ProposeArchival | `proposals` | `kind`（事件名稱）、`subject_ref`、`payload`、`dismissed_by`、`dismissed_at`、`dismiss_reason`、`superseded_by` | 不改變狀態；可作廢，保留作廢紀錄（03_flows 事件表「能否撤銷」） |
| NotifySignificantCorrection（事件，建議層） | `significant_corrections` | `correction_event_id`、`changed`（改了什麼、更正前後的判定）、`affected_employment_ids[]`、`notified_to[]`、`notified_at` | 不可作廢：獨立集合，沒有作廢或修改的 API（03_flows 事件表；D-07） |
| 所有有名字的事件（P1） | `events` | 見 1.3 | 每次動作一筆，狀態由事件推出 |
| 規則與版本（P5） | `rule_versions` | `rule_id`（R01…）、`version`、`revision`、`effective_from`、`effective_to`、`params`（例：每月最低工資、分級表）、`source_ref`、`recorded_at`、`supersedes` | 規則以資料存在，不寫死在程式（P5）；R12、R40～R43 的金額與分級表放 `params`。只新增：登錯時新增一筆修訂，不原地改（03_flows D-11、R51）；全平台共用，由平台管理者維護，不經本切片的 API |
| P7 刪除與遮蔽的紀錄 | `erasure_records` | `person_id`、`trigger`（保存期滿／個資請求）、`data_subject_request_id`、`categories[]`、`collections_processed[]`、`performed_by`、`performed_at`、`retention_basis`（依據的規則與最後一段僱傭關係的結束日） | P7 要求留下「何時、依誰的請求、處理了哪些資料」；見第四節 P7（D-08） |
| 系統使用者帳號與人的對應 | `user_accounts` | `user_id`、`tenant_id`、`person_id`（可空）、`roles[]` | 員工提出個資請求時用來確認「本人」；人資、雇主的角色也在這裡（D-09，待使用者決定） |
| 分類值的多語名稱（P10） | `labels` | `code`（例：`APPLICABILITY.MANDATORY`）、`locale`、`label` | 代碼不隨語言改變；zh-TW 名稱取自 04_rules 分類值表與詞彙對照表 |

### 1.2 業務欄位

型別：`date`＝日期（不含時刻）；`datetime`＝時刻；`ref`＝指到另一個概念的 `entity_id`（不是 `_id`：只新增的集合每次寫入產生新版本文件，`_id` 會變，`entity_id` 不變，D-10）；`code`＝分類值代碼；`[]`＝陣列。

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| Person.legal_name | `persons` | `legal_name`（string） | 勞工名卡項目；經 CorrectRecord 更正（D-05） |
| Person.gender | `persons` | `gender`（code） | 經 CorrectRecord 更正（D-05） |
| Person.birth_date | `persons` | `birth_date`（date） | 經 CorrectRecord 更正（D-05） |
| Person.nationalities | `persons` | `nationalities[]`：`country_code`、`acquired_on`、`lost_on` | 帶期間，判定看某一天的值 |
| Person.education | `persons` | `education`（string） | 經 CorrectRecord 更正（D-05） |
| Person.address | `persons` | `address`（string） | 經 CorrectRecord 更正（D-05） |
| Person.contact | `person_contacts` | `person_id`、`phone`、`email` | 只需現況，直接覆寫（P2 C、P1 單純欄位）；唯一不經事件就能改的人的資料（D-05） |
| Person.old_age_benefits_received | `persons` | `old_age_benefits_received[]`：`scheme_code`、`received_on` | 帶日期 |
| Person.civil_registrations | `persons` | `civil_registrations[]`：`jurisdiction_id`、`registered_on`、`deregistered_on` | 帶期間 |
| Person.age | — | — | 不落地（推導，P3）；由 `birth_date` 與判定日現算（R29） |
| belongsToTenant（Person、Employer、OrgUnit） | `persons`、`employers`、`org_units` | `tenant_id`（ref） | 業務關係；其他集合的 `tenant_id` 是隔離用的技術欄位（第五節） |
| IdentityDocument.document_kind | `identity_documents` | `document_kind`（code） | |
| IdentityDocument.document_number | `identity_documents` | `document_number`（string） | 回任時以此辨識同一人（Q11）：索引 `tenant_id`＋`document_kind`＋`issuing_jurisdiction_id`＋`document_number`，**不唯一**（居留事由改變時同一證號另記一筆，02 D-05） |
| IdentityDocument.valid_from／valid_until | `identity_documents` | `valid_from`、`valid_until`（date） | |
| IdentityDocument.residence_basis | `identity_documents` | `residence_basis`（code） | |
| heldBy、issuedBy | `identity_documents` | `person_id`、`issuing_jurisdiction_id`（ref） | |
| Employer.legal_name、employer_type | `employers` | `legal_name`、`employer_type`（code） | |
| Employer.registrations | `employers` | `registrations[]`：`kind`（code）、`registered_on` | 雇主註冊於台灣時必填（可為空陣列表示「無」） |
| Employer.registration_exempt | `employers` | `registration_exempt[]`：`value`（bool）、`from`、`to` | 帶期間（02 D-32） |
| Employer.tax_assessed_or_invoice_permit | `employers` | `tax_assessed_or_invoice_permit[]`：`value`、`from`、`to` | 帶期間 |
| Employer.labor_insurance_industry_category | `employers` | `labor_insurance_industry_category[]`：`code`、`from`、`to` | 帶期間 |
| Employer.labor_standards_act_applicable | `employers` | `labor_standards_act_applicable[]`：`value`、`from`、`to` | 帶期間 |
| Employer.system_managed_from | `employers` | `system_managed_from`（date） | 補登界線（R08） |
| Employer.headcount_on | — | — | 不落地（推導）；由 `employments` 依實際到職、結束日現算（R23） |
| registeredIn | `employers` | `jurisdiction_id`（ref） | |
| Hire.decided_on、planned_start_date | `hires` | `decided_on`、`planned_start_date`（date） | 改期時舊值留在變更紀錄（P2 B） |
| Hire.cancellation_reason、cancelled_on | `hires` | `cancellation_reason`、`cancelled_on` | |
| Hire.prior_insurance_elsewhere | `hires` | `prior_insurance_elsewhere`（string） | |
| Hire 的狀態 | `hires` | `status`（Hired／Cancelled／Started） | 只能由事件改變（P1）；值是 03 的狀態名稱 |
| ofPerson、byEmployer、plannedWorkLocation、plannedOrgUnit | `hires` | `person_id`、`employer_id`、`planned_work_location_id`、`planned_org_unit_id` | |
| Employment.start_date、ended_on、end_reason | `employments` | `start_date`、`ended_on`（date）、`end_reason`（code） | |
| Employment.employee_number | `employments` | `employee_number`（string） | 同一雇主在職者不重複（R05、D-03） |
| Employment.employee_category | `employments` | `employee_category[]`：`code`、`from`、`to` | 帶期間 |
| Employment.probation_until | `employments` | `probation_until`（date） | |
| Employment.historical_basis_note | `employments` | `historical_basis_note`（string） | 補登時才有 |
| Employment.public_or_military_insurance_covered | `employments` | `public_or_military_insurance_covered[]`：`value`（bool）、`from`、`to` | 帶期間；就保 R24（02 D-37） |
| Employment.seniority | — | — | 不落地（推導） |
| Employment 的狀態 | `employments` | `status`（Active／Ended） | P1 |
| ofPerson、withEmployer、resultedFromHire | `employments` | `person_id`、`employer_id`、`hire_id`（可空） | 補登沒有 `hire_id`（02 D-12） |
| assignedTo、worksAt | `employments` | `org_unit_assignments[]`：`org_unit_id`、`from`、`to`；`work_locations[]`：`work_location_id`、`from`、`to` | 帶期間 |
| EmploymentContract 各屬性 | `employment_contracts` | `contract_type`、`fixed_term_nature`（code）、`term_start`、`term_end`（date）、`in_writing`（bool）、`status` | `term_end` 只記契約上寫的（02 D-36）；移工的實際期限由 R59 現算 |
| governs、concludedForHire | `employment_contracts` | `employment_id`、`hire_id`（可空） | |
| Compensation 各屬性 | `compensations` | `effective_from`、`currency`、`pay_basis`、`monthly_base_salary`（decimal）、`fixed_monthly_allowances[]`：`name`、`category`（code）、`amount`、`status` | 金額用 Decimal128；`monthly_wage_total` 不落地（推導，R39） |
| agreedFor、agreedAtHire | `compensations` | `employment_id`、`hire_id` | |
| WorkAuthorization.authorization_basis、work_category | `work_authorizations` | `authorization_basis`、`work_category`（code） | |
| WorkAuthorization.approvals | `work_authorizations` | `approvals[]`：`permit_number`、`valid_from`、`valid_until`、`recorded_at` | 展延新增一筆，不改前一筆（02 D-33） |
| WorkAuthorization.valid_from／valid_until | `work_authorizations` | `valid_from`、`valid_until` | 只用於免申請者 |
| WorkAuthorization 的狀態 | `work_authorizations` | `status`（Valid／Expired） | P1 |
| heldBy、validIn、boundToEmployer、basedOnDocument、replaces | `work_authorizations` | `person_id`、`jurisdiction_id`、`employer_id`（可空）、`based_on_document_id`（可空）、`replaces_id`（可空） | |
| InsuranceEnrollment 各屬性 | `insurance_enrollments` | `filed_on`（date）、`voluntary`（bool）、`effective_from`（date）、`status`、`receipt_ref`（或 `no_receipt: true`） | `days_late` 不落地（推導，R35）；回執依 R50 |
| forEmployment、inScheme、throughUnit | `insurance_enrollments` | `employment_id`、`scheme_id`、`insurance_unit_id`（可空） | |
| InsuredSalary 各屬性 | `insured_salaries` | `declared_amount`（decimal）、`grade`、`grading_table_version`、`declared_on`、`source`（code）、`effective_from`、`status` | `grading_table_version` 指到 `rule_versions` |
| declaredFor | `insured_salaries` | `enrollment_id` | |
| WarningOverride 各屬性 | `warning_overrides` | `rule_ref`：`rule_id`、`version`、`revision`；`subject_ref`：`collection`、`id`、`field`；`warned_value`、`overridden_by`、`overridden_at`、`reason`、`withdrawn_by`、`withdrawn_at`、`status` | |
| concernsHire、concernsEmployment | `warning_overrides` | `hire_id`、`employment_id`（至少一個，R09） | |
| PersonalDataArchival 各屬性 | `personal_data_archivals` | `person_id`、`data_categories[]`（code）、`archived_on`、`archived_by`；`releases[]`：`categories[]`、`released_on`、`released_by`、`reason`、`link`（錄用、個資請求或註銷的 ref，R57）；`status` | 可以只解除部分類別，每次解除一筆；`status` 依「是否還有類別在封存」推出 |
| DataSubjectRequest 各屬性 | `data_subject_requests` | `person_id`、`request_kind`（code）、`requested_categories[]`（code）、`received_on`、`received_via`、`resolved_on`、`outcome`、`category_outcomes[]`：`category`、`result`；`refusal_basis`：`rule_id`、`rule_version`、`rule_revision`、`legal_basis`、`reason`；`status` | 部分接受時逐類記結果，R55 依類別判斷 |
| DataSubjectRequest.extensions | `data_subject_requests` | `extensions[]`：`extended_deadline`、`reason`、`notified_on`、`recorded_by` | 每次延長一筆（03_flows D-15） |
| ProposeEnrollmentFiling 的內容 | `enrollment_proposals` | `hire_id` 或 `employment_id`；`determined_on`（判定日 d）；`estimated`（錄用時的預估，04_rules D-18）；`allowance_decisions[]`：「其他」類固定給付算不算入的決定（`allowance_name`、`result`、`by`、`at`、`reason`）；`basis`：用到的資料版本與規則版本（含修訂）；`items[]`：`scheme_code`、`applicability`（code）、`filing_deadline`、`legal_effective_date`、`expected_grade`、`days_overdue`、`closed_by_enrollment_id`、`voluntary_declined`：`by`、`at`、`decisions[]`（就保擇一參加的決定）、`days_overdue`（R36 逾期天數）；`superseded_by` | 每種保險各自結案或被雇主拒絕；判定內容不改，結案與拒絕留變更紀錄（P2 B）；不由人作廢（03_flows X-22） |

### 1.3 事件紀錄（`events`，P1、P4）

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| 事件名稱 | `events` | `type`（例：`StartEmployment`） | 03_flows 事件表的 35 個事件 |
| 主體 | `events` | `subject`：`collection`、`id` | |
| 發生時間、得知時間、生效時間 | `events` | `occurred_at`、`recorded_at`、`effective_from` | 依 03_flows 事件表「有意義的時間」，不需要的留空（P4） |
| 誰做的 | `events` | `actor`：`user_id`、`role` | 時間或條件觸發的寫 `system` |
| 證據 | `events` | `evidence[]`、`reason` | |
| 依據的規則版本 | `events` | `rule_versions[]`：`rule_id`、`version`、`revision` | 判定類事件記（P5） |
| 註銷 | `events` | AnnulEntry 事件記 `target_event_id`；RevokeAnnulment 事件記 `target_annulment_id` | 原事件不回寫（`events` 只新增）；一筆事件是否被註銷，依它的註銷與撤銷事件推出，可以來回多次（D-11） |
| 時間或條件觸發的事件 | `events` | `derived`（true）、`invalidated_by_event_id` | 03_flows D-12：依據的日期被更正時，這類事件標為失效，重新推導；不是註銷（D-12） |
| 補登標記 | `events` | `is_backfill`（bool） | RegisterExistingEmployment |

## 二、事件 → API

API 以 REST 描述（OpenAPI 3.1），路徑前綴 `/v1`；每支 API 標 `x-concept`（P8）。每次呼叫在同一個多文件交易中寫入 `events` 與受影響的集合（PLAN.md D-35）。

**所有 API 共同的檢查**（service 層，D-06）：呼叫者的 `tenant_id` 和路徑、內容中**每一個** ref 指到的文件相同；MongoDB 不檢查引用是否存在，由 service 檢查存在且是目前版本；全平台共用的集合（`jurisdictions`、`social_insurance_schemes`、`rule_versions`、`labels`）本切片的 API 只能讀。

| 事件 | API | 權限檢查 |
|---|---|---|
| DecideHire | `POST /v1/hires` | 人資；同一客戶 |
| RescheduleStart | `POST /v1/hires/{id}/reschedule` | 人資；`status`＝Hired |
| CancelHire | `POST /v1/hires/{id}/cancel` | 人資；`status`＝Hired |
| StartEmployment | `POST /v1/hires/{id}/start` | 人資；`status`＝Hired；R01、R04～R06 擋下 |
| RegisterExistingEmployment | `POST /v1/employments/backfill` | 人資；R08 擋下 |
| RecordEarlyDeparture | `POST /v1/employments/{id}/early-departure` | 人資；`status`＝Active |
| SignContract | `POST /v1/employment-contracts` | 人資 |
| AgreeCompensation | `POST /v1/compensations` | 人資 |
| RecordWorkAuthorization | `POST /v1/work-authorizations`（第一次）；`POST /v1/work-authorizations/{id}/approvals`（展延） | 人資 |
| EndWorkAuthorization | `POST /v1/work-authorizations/{id}/end` | 人資；只用於免申請者 |
| RecordIdentityDocument | `POST /v1/persons/{id}/identity-documents` | 人資 |
| RecordPersonPeriod | `POST /v1/persons/{id}/periods` | 人資；產生新版本的 `persons` 並觸發加保待辦 |
| RecordInsuranceFiling | `POST /v1/insurance-enrollments` | 人資；R50 擋下（回執或標示無回執） |
| DeclareInsuredSalary | `POST /v1/insurance-enrollments/{id}/insured-salaries` | 人資 |
| OverrideWarning | `POST /v1/warning-overrides` | 人資；R09、R10 擋下 |
| WithdrawWarningOverride | `POST /v1/warning-overrides/{id}/withdraw` | 人資 |
| ReceiveDataSubjectRequest | `POST /v1/data-subject-requests` | 員工本人（自己的）或人資（代登錄） |
| ExtendDataSubjectRequest | `POST /v1/data-subject-requests/{id}/extensions` | 人資；R63 提醒 |
| ResolveDataSubjectRequest | `POST /v1/data-subject-requests/{id}/resolve` | 人資；R55 擋下刪除保存期間內的類別 |
| ArchivePersonalData | `POST /v1/personal-data-archivals` | 人資 |
| ReleaseArchival | `POST /v1/personal-data-archivals/{id}/release` | 人資；R57 擋下 |
| CorrectRecord | `POST /v1/corrections` | 人資；只能更正 2.2「可更正的欄位」，其餘擋下；R49、R50 擋下；重大更正（R46）產生 `significant_corrections` |
| AnnulEntry | `POST /v1/annulments` | 人資；只接受 03_flows D-14 白名單上的事件 `type`（R47）；R48 擋下 |
| RevokeAnnulment | `POST /v1/annulments/{id}/revoke` | 人資 |
| ContractTermStarts、VoidContract、ExpireWorkAuthorization、ExpireIdentityDocument、LapseWarningOverride | 無 API：系統排程或事件處理器產生 | 系統；寫 `events`，`actor`＝system，`derived`＝true |
| ProposeEnrollmentFiling | 系統產生；`GET /v1/enrollment-proposals`（列出，含預估、逾期天數、待人判斷）、`POST /v1/enrollment-proposals/{id}/decline-voluntary`（雇主選擇不加自願保險）、`POST /v1/enrollment-proposals/{id}/decisions`（待人判斷事項的決定，04_rules D-16） | 讀：人資、雇主；拒絕自願：雇主或人資；決定：人資 |
| PromptStartConfirmation、ProposeAuthorizationReview、PromptDataSubjectRequestDeadline、ProposeArchival | 系統產生；`GET /v1/proposals`、`POST /v1/proposals/{id}/dismiss` | 人資；dismiss 只接受這 4 種 `kind` |
| NotifySignificantCorrection | 系統產生；`GET /v1/significant-corrections` | 雇主（老闆）、人資；只能讀，沒有作廢或修改的 API |
| （查詢）UC-15 勞工名卡 | `GET /v1/employments/{id}/labor-roster` | 處理人事的人資（R52）；已封存的類別不顯示 |
| （查詢）UC-02 判定結果 | `GET /v1/employments/{id}/applicability?on=<判定日>&as_of=<得知時間>` | 人資；現算，不落地；`as_of` 用來查「當時系統知道的判定」（Q15、03_flows D-10），只看 `recorded_at` 早於它的版本與事件 |
| （查詢）人的建立 | 不單獨提供：DecideHire、RegisterExistingEmployment 時同一交易建立 `persons` | 人資 |
| （查詢）回任時找同一人 | `GET /v1/persons/lookup?document_kind=&document_number=` | 人資；只回傳是否存在與 Person 編號，不回傳已封存的類別；查詢寫進稽核紀錄（D-13） |
| （查詢）個資請求的進度與查閱、複製 | `GET /v1/data-subject-requests/{id}`；`GET /v1/persons/{id}/personal-data-export` | 本人（經 `user_accounts` 對應）或人資；匯出只含本人資料、寫入稽核紀錄 |
| （P7）保存期滿後的遮蔽 | `POST /v1/personal-data-erasures` | 人資或排程；R55 擋下仍在保存期間的類別；寫 `erasure_records`（D-08） |

### 2.1 Use Case → API

| UC | 用到的 API |
|---|---|
| UC-01 錄用本國籍員工並到職 | `POST /hires`（同一交易建立人）→ `POST /persons/{id}/identity-documents` → `POST /compensations` → `POST /employment-contracts` → `POST /hires/{id}/start` → `GET /enrollment-proposals` |
| UC-02 判定各保險 | 系統產生 `enrollment_proposals`；`GET /employments/{id}/applicability` |
| UC-03 登錄實際加保與投保薪資 | `POST /insurance-enrollments` → `POST /insurance-enrollments/{id}/insured-salaries` |
| UC-04 錄用外籍員工 | UC-01 ＋ `POST /work-authorizations`、`POST /work-authorizations/{id}/approvals`、`POST /work-authorizations/{id}/end` |
| UC-05 到職前改期 | `POST /hires/{id}/reschedule` |
| UC-06 到職前取消 | `POST /hires/{id}/cancel`；系統產生封存建議 → `POST /personal-data-archivals` |
| UC-07 登錄勞動契約 | `POST /employment-contracts` |
| UC-08 更正與註銷 | `POST /corrections`、`POST /annulments`、`POST /annulments/{id}/revoke`；`GET /significant-corrections` |
| UC-09 忽略警告與撤回 | `POST /warning-overrides`、`POST /warning-overrides/{id}/withdraw` |
| UC-10 到職後立刻離開 | `POST /employments/{id}/early-departure` |
| UC-11 補登雇主開始由系統管理前就到職的員工 | `POST /employments/backfill`（同一交易建立人，並登錄目前的投保、投保薪資、約定薪資） |
| UC-12 回任 | `GET /persons/lookup` → UC-01（沿用同一個人） |
| UC-13 封存與解除 | `POST /personal-data-archivals`、`POST /personal-data-archivals/{id}/release` |
| UC-14 個資請求 | `POST /data-subject-requests` → `GET /data-subject-requests/{id}` → `POST /data-subject-requests/{id}/extensions` → 查閱、複製用 `GET /persons/{id}/personal-data-export`；更正用 `POST /corrections` → `POST /data-subject-requests/{id}/resolve` |
| UC-15 查詢勞工名卡 | `GET /employments/{id}/labor-roster` |

### 2.2 可更正的欄位（CorrectRecord）

只有下列欄位可以用 `POST /v1/corrections` 更正；狀態（`status`）、`tenant_id`、誰與何時（`*_by`、`*_at`）、`events`、`significant_corrections`、`rule_versions` 一律不能更正（D-06）。

| 集合 | 可更正的欄位 | 備註 |
|---|---|---|
| `persons` | `legal_name`、`gender`、`birth_date`、`education`、`address`、`nationalities`、`civil_registrations`、`old_age_benefits_received` | 改變判定的（出生日期、國籍、戶籍、老年給付）依 R46 判斷是否為重大更正，並重新產生加保待辦 |
| `identity_documents` | `document_kind`、`document_number`、`valid_from`、`valid_until`、`residence_basis` | |
| `hires` | `decided_on`、`planned_start_date`、`cancellation_reason`、`cancelled_on`、`prior_insurance_elsewhere` | 雇主不能改（R49） |
| `employments` | `start_date`、`employee_number`、`employee_category`、`probation_until`、`ended_on`、`end_reason`、`historical_basis_note`、`org_unit_assignments`、`work_locations`、`public_or_military_insurance_covered` | 雇主、人不能改（R49；登錯人走更正方式「改指到正確的人」） |
| `employment_contracts` | `contract_type`、`fixed_term_nature`、`term_start`、`term_end`、`in_writing` | |
| `compensations` | `monthly_base_salary`、`fixed_monthly_allowances`、`effective_from` | |
| `work_authorizations` | `authorization_basis`、`work_category`、`approvals[]` 某一筆的打錯值、`valid_from`、`valid_until` | 展延不能用更正，要新增核准（03_flows WorkAuthorization） |
| `insurance_enrollments` | `filed_on`、`voluntary`、`effective_from` | 要附回執或標示無回執（R50） |
| `insured_salaries` | `declared_amount`、`grade`、`declared_on`、`effective_from` | 同上 |
| `data_subject_requests` | `request_kind`、`requested_categories`、`received_via` | `received_on` 不能改：處理期限由它起算（R53） |

新增一段國籍、戶籍期間（例：歸化、出國除籍）不是更正，是登錄新的事實，走 RecordPersonPeriod（`POST /v1/persons/{id}/periods`，D-14）。

## 三、規則 → 落實位置
<!-- db constraint／db trigger／service／人工；MongoDB 沒有 trigger，「db constraint」指集合的驗證規則與唯一索引（PLAN.md D-35） -->

| 規則 | 落實位置 | 說明 |
|---|---|---|
| R02、R03 | db constraint | 同一文件內的日期比較，用集合驗證規則的 `$expr`（例：`ended_on >= start_date`）；service 再檢查一次以回傳清楚的訊息 |
| R05 | db constraint ＋ service | 部分唯一索引：`tenant_id`＋`employer_id`＋`employee_number`，條件 `status`＝Active、`annulled`＝false、`is_current`＝true；補登已結束者的期間重疊由 service 檢查 |
| R09 | db constraint | 驗證規則：`hire_id`、`employment_id` 至少一個 |
| R01、R04、R06、R07、R08、R10 | service | 跨集合比較，在動作的交易中檢查，違反時擋下。R04 要防同時送出：交易中先更新 `employment_locks`（鍵 `tenant_id`＋`person_id`＋`employer_id`，`$inc`），讓兩個同時的交易互相衝突（D-15） |
| R47～R50、R57 | service | 流程規則，違反時擋下（inputs/shared/範圍釐清_擋下的範圍.md）；R57 另檢查連到的錄用、個資請求或註銷屬於同一個人、同一客戶 |
| R55 | service | 處理刪除請求與保存期滿的遮蔽時，比對資料類別與保存期間（以同一人在該客戶最後一段僱傭關係的結束日起算），擋下並自動帶入拒絕的依據（R62） |
| R52 | service（權限） | API 層依角色與資料類別檢查；已封存的類別一般查詢不回傳（P7） |
| R11、R13～R18、R20、R21、R45、R58、R61、R62、R63 | service | 法規檢查，只提醒：回傳警告，使用者可用 OverrideWarning 忽略。04_rules 版本欄為「—」的規則，警告與忽略紀錄的版本用規則所在的 04 凍結版本（D-20） |
| R12、R22～R37、R39～R44、R59、R60 | service | 判定與計算，依 `rule_versions` 取當時的版本現算；結果寫進 `enrollment_proposals` 或查詢時回傳，不落地為事實。R36 逾期是判定，寫在待辦的 `days_overdue`，不是警告（04_rules D-17）；R24、R39 待人判斷的結果依待辦上的決定（04_rules D-16） |
| R46、R51、R53、R56 | service | 判定後產生通知、失效事件、期限提醒、封存建議；R51 比對規則版本與修訂（`rule_versions.revision`） |
| （所有判定與計數） | service | 被註銷的資料一律排除：人數（R23）、勞工名卡（UC-15）、期間不重疊（R04）、員工編號（R05）都只看 `annulled`＝false（D-11） |
| R19 | 人工 | 是否為繼續性工作由人資判斷；系統只在簽定期契約時提醒並要求勾選（EQ-021） |
| R24（擇一參加）、R39（「其他」類固定給付） | 人工 ＋ service | 受僱於兩個以上雇主時，由人決定參加哪一個，記在加保待辦 |

## 四、推導值與歷史需求 → 儲存
<!-- 資料身分：事實／快取／凍結快照；保存方式：A／B／C／— -->

| 概念 | 資料身分（P3） | 保存方式（P2） |
|---|---|---|
| Person（`persons`：勞工名卡項目、國籍、戶籍、老年給付） | 事實 | A：國籍、戶籍、老年給付需要重建當時且決定保險適用（法規），勞工名卡項目跟著同一份文件一起只新增（D-16） |
| Person.contact（`person_contacts`） | 事實 | C |
| IdentityDocument | 事實 | A |
| Employer、InsuranceUnit、OrgUnit、WorkLocation、Tenant | 事實（org-setup） | 由 org-setup 決定；本切片要求判定條件帶期間 |
| Hire | 事實 | B |
| Employment | 事實 | A |
| EmploymentContract | 事實 | B |
| Compensation | 事實 | A |
| WorkAuthorization | 事實 | A |
| InsuranceEnrollment | 事實 | A |
| InsuredSalary | 事實 | A |
| WarningOverride | 事實 | B |
| PersonalDataArchival | 事實 | B |
| DataSubjectRequest | 事實 | B |
| 加保待辦（ProposeEnrollmentFiling） | 事實（記當時的判定與規則版本） | B：判定內容不改；取代、各保險的結案與拒絕寫回並留變更紀錄 |
| 重大更正通知（`significant_corrections`） | 事實 | A |
| 刪除與遮蔽紀錄（`erasure_records`） | 事實 | A |
| 各集合的 `status`、`annulled` | 快取：依 `events`（排除被註銷、已失效的）重算 | — ；P9 要求砍掉重算結果一致 |
| 事件紀錄（`events`） | 事實 | A |
| 各保險的適用、應辦理期限、法定生效日、應申報級距 | 推導值：不存，現算 | — |
| 晚辦天數（InsuranceEnrollment.days_late） | 推導值：不存，現算 | — |
| 年齡、年資、雇主人數、投保單位計入人數、月薪資總額 | 推導值：不存，現算 | — |
| 移工契約的實際期限（R59） | 推導值：不存，現算 | — |
| 法規警告 | 推導值：不存，現算；被忽略的記在 WarningOverride | — |
| 勞工名卡（UC-15） | 推導值：查詢時組出 | — |

**A 只新增的做法（MongoDB）**：每次寫入（事件造成的變化與更正）都新增一份版本文件，欄位 `entity_id`、`revision`、`supersedes`、`is_current`、`recorded_at`、`event_id`；前一份只把 `is_current` 改為 false，內容不動。唯一索引 `entity_id`＋`is_current`（條件 `is_current`＝true）保證只有一份目前版本。其他集合一律用 `entity_id` 指它（D-10）。**B 的做法**：直接更新文件，同時在 `change_log` 新增一筆（不可刪）。

**P7 刪除與遮蔽**：保存期間內只封存（`personal_data_archivals`），一般查詢不回傳；期間過後刪除可識別個人的欄位（例：姓名、證號、住址改為遮蔽值），業務事實（到職日、加保日）保留。保存期間以同一人在該客戶最後一段僱傭關係的結束日起算（同一個人可能在同客戶的另一家公司仍在職）。哪些必須真的刪除 [待專家確認: EQ-022]。

遮蔽要涵蓋所有存有個資複本的地方（D-08，待使用者決定做法）：

| 位置 | 個資在哪 | 遮蔽方式 |
|---|---|---|
| `persons` 的所有版本（A） | 姓名、出生日期、住址等 | 每一份版本都遮蔽，`revision` 不變 |
| `identity_documents` 的所有版本 | 證號 | 同上 |
| `person_contacts` | 電話、email | 刪除 |
| `change_log` | 舊值、新值 | 個資欄位只存參照（指到版本文件），不存明文；遮蔽時不用另外處理 |
| `events` | `evidence[]`、`reason` | 證據只存附件參照；附件與自由文字依類別遮蔽 |
| `enrollment_proposals.basis`、`warning_overrides.warned_value` | 判定用到的值 | 只存參照與非識別值（例：年齡、月薪），不存姓名、證號 |
| `outbox` | 發給其他服務的內容 | 只發 ID 與事件類型，不帶個資 |

## 五、技術欄位與平台表

| 表或欄位 | 用途 |
|---|---|
| `_id`（每個集合） | [技術] 主鍵（ObjectId） |
| `tenant_id`（客戶資料的集合；`persons`、`employers`、`org_units` 的 `tenant_id` 是業務關係） | [技術] 客戶隔離；所有查詢與索引都帶。全平台共用的 `jurisdictions`、`social_insurance_schemes`、`rule_versions`、`labels` 沒有 |
| `entity_id`、`revision`、`supersedes`、`is_current`、`event_id` | [技術] P2 A 的版本欄位 |
| `annulled`（被註銷的事件建立的文件） | [技術] 快取：由註銷與撤銷事件推出，索引與查詢用 |
| `employment_locks` | [技術] 平台表：R04 的同時寫入保護 |
| 稽核紀錄（`audit_log`） | [技術] 平台表：查詢個資、匯出、以證件查人的紀錄 |
| `created_at`、`updated_at`、`schema_version` | [技術] |
| `change_log` | [技術] 平台表：P2 B 的變更紀錄（集合、文件、欄位、舊值、新值、誰、何時、事件） |
| `outbox` | [技術] 平台表：事件發布給其他服務 |
| `x-concept`（OpenAPI）、集合驗證規則的 `description` | [技術] P8：標出對應的概念 ID |

## 六、Use Case 走一遍
<!-- 照每個正式 Use Case 的步驟依序對到 API。從哪裡來：使用者輸入／登入身分／第 n 步回應的 <欄位>／查詢 <API>；
     來自回應的欄位，api.yaml 該 API 的回應格式要有 -->

| Use Case | 步驟 | API | 需要的輸入 | 從哪裡來 |
|---|---|---|---|---|
| UC-01 | 2（含 1） | `POST /v1/hires` | person（新的人：姓名等）、employer_id、decided_on、planned_start_date、planned_work_location_id、compensation、contract | 使用者輸入；employer_id、planned_work_location_id 查 org-setup（雇主、工作地點清單）；回任時 person.person_id 來自 UC-12 `GET /persons/lookup` 回應的 `person_id` |
| UC-01 | 1 | `POST /v1/persons/{id}/identity-documents` | {id}＝person_id；document_kind、issuing_jurisdiction_id、document_number、valid_from | person_id：第 2 步回應的 `person_id`；其餘使用者輸入；issuing_jurisdiction_id 查參考資料 |
| UC-01 | 3 | （第 2 步的回應） | — | 最低工資警告在第 2 步回應的 `warnings`（R11）；要忽略時走 UC-09 |
| UC-01 | 4 | `GET /v1/enrollment-proposals?hire_id=` | hire_id | 第 2 步回應的 `hire_id` |
| UC-01 | 5 | `GET /v1/proposals` → `POST /v1/hires/{id}/start` | {id}＝hire_id；start_date、work_location_id、org_unit_id、employee_number、probation_until | hire_id：第 2 步回應的 `hire_id`，或提醒（PromptStartConfirmation）的 `subject.id`；其餘使用者輸入 |
| UC-01 | 6、7 | （第 5 步的回應） | — | 管轄區由工作地點推出；試用期在第 5 步的 probation_until |
| UC-01 | 8 | 見 UC-03 | employment_id | 第 5 步回應的 `employment_id` |
| UC-02 | 1～6 | 系統產生；`GET /v1/employments/{id}/applicability?on=`、`GET /v1/enrollment-proposals?employment_id=` 或 `?hire_id=`（錄用時的預估） | employment_id 或 hire_id、判定日 | employment_id：UC-01 第 5 步回應；hire_id：UC-01 第 2 步回應；判定日：使用者輸入或今天 |
| UC-02 | 6（待人判斷） | `POST /v1/enrollment-proposals/{id}/decisions` | enrollment_proposal_id、kind、scheme_code 或 allowance_name、result、reason | enrollment_proposal_id：`GET /enrollment-proposals` 回應的 `enrollment_proposal_id`；待判斷的項目在 items 的 `applicability`＝待人判斷；result 由人資輸入 |
| UC-03 | 1 | `POST /v1/insurance-enrollments` | employment_id、scheme_id、insurance_unit_id、filed_on、voluntary、effective_from、receipt_ref 或 no_receipt | employment_id：UC-01 第 5 步回應或加保待辦的 `employment_id`；scheme_id 查參考資料（保險制度）；insurance_unit_id 查 org-setup；其餘使用者依保險人回執輸入 |
| UC-03 | 2 | `POST /v1/insurance-enrollments/{id}/insured-salaries` | {id}＝enrollment_id；declared_amount、grade、declared_on、effective_from | enrollment_id：第 1 步回應的 `enrollment_id`；應報級距可參考加保待辦 items 的 `expected_grade` |
| UC-03 | 3 | `GET /v1/employments/{id}/applicability` | employment_id | 晚辦天數 `days_late`、級距不符的警告在第 2 步回應的 `warnings`（R45） |
| UC-04 | 1 | `POST /v1/persons/{id}/identity-documents` | person_id、居留證資料 | person_id：UC-01 第 2 步回應 |
| UC-04 | 2 | `POST /v1/work-authorizations` | person_id、jurisdiction_id、authorization_basis、work_category、employer_id、approval 或 valid_from、based_on_document_id | person_id：UC-01 第 2 步回應；based_on_document_id：第 1 步回應的 `identity_document_id`；其餘使用者依許可函輸入 |
| UC-04 | 2（展延） | `POST /v1/work-authorizations/{id}/approvals` | {id}＝work_authorization_id；permit_number、valid_from、valid_until | 第 2 步回應的 `work_authorization_id` |
| UC-04 | 3、4 | 同 UC-01 第 2、5 步 | — | 許可相關警告在 `POST /hires/{id}/start` 回應的 `warnings`（R14～R16） |
| UC-04 | 例外 | `POST /v1/work-authorizations/{id}/end`；`GET /v1/proposals` | work_authorization_id | 提醒（ProposeAuthorizationReview）的 `subject.id` |
| UC-05 | 1～3 | `POST /v1/hires/{id}/reschedule` | hire_id、planned_start_date、reason | hire_id：UC-01 第 2 步回應；新的警告在回應的 `warnings`；改期紀錄由 change_log 查 |
| UC-06 | 1～2 | `POST /v1/hires/{id}/cancel` | hire_id、cancelled_on、cancellation_reason | hire_id：UC-01 第 2 步回應 |
| UC-06 | 3 | `GET /v1/proposals` → UC-13 | person_id | 封存建議（ProposeArchival）的 `subject.id` |
| UC-07 | 1 | `POST /v1/employment-contracts` | employment_id 或 hire_id、契約資料 | employment_id：UC-01 第 5 步回應；或 hire_id：UC-01 第 2 步回應；也可在 `POST /hires` 的 contract 一併登錄 |
| UC-07 | 2、3 | （第 1 步的回應） | — | 期間上限、書面的警告在 `warnings`；契約生效由系統依起日推出 |
| UC-08 | 1～2 | `POST /v1/corrections` | subject（collection、id）、field、new_value、reason、evidence | subject.id：被更正的那一筆，來自當初建立它的回應（例：employment_id）；field 只限 2.2 |
| UC-08 | 註銷 | `POST /v1/annulments`、`POST /v1/annulments/{id}/revoke` | target_event_id；annulment_event_id | target_event_id：當初動作回應的 `event_id`；annulment_event_id：註銷回應的 `annulment_event_id` |
| UC-08 | 3～5 | `GET /v1/employments/{id}/applicability?as_of=`、`GET /v1/significant-corrections` | employment_id、as_of | as_of：更正前的時間；重大更正在更正回應的 `significant_correction_id` |
| UC-09 | 1～2 | `POST /v1/warning-overrides` | rule_ref、subject_ref、warned_value、hire_id 或 employment_id、reason | rule_ref、subject_ref、warned_value：觸發警告的那個回應的 `warnings[]`；hire_id 或 employment_id：同一個回應 |
| UC-09 | 撤回 | `POST /v1/warning-overrides/{id}/withdraw` | warning_override_id | 第 1 步回應的 `warning_override_id` |
| UC-10 | 1～3 | `POST /v1/employments/{id}/early-departure` | employment_id、ended_on、end_reason | employment_id：UC-01 第 5 步回應 |
| UC-11 | 1～4 | `POST /v1/employments/backfill` | person、employer_id、start_date、ended_on、work_location_id、historical_basis_note、compensation、contract、enrollments（含 insured_salary） | 使用者輸入；回應給 employment_id、person_id、compensation_id、contract_id、enrollment_ids、insured_salary_ids；證件用 UC-01 第 1 步的 API，person_id 取這個回應 |
| UC-12 | 1 | `GET /v1/persons/lookup` | document_kind、document_number | 使用者輸入；回應 `person_id` 帶入 UC-01 第 2 步的 person.person_id |
| UC-12 | 2～3 | UC-13 解除；UC-01 | person_id | 第 1 步回應的 `person_id` |
| UC-13 | 1～3 | `GET /v1/proposals` → `POST /v1/personal-data-archivals`；`POST /v1/personal-data-archivals/{id}/release` | person_id、data_categories；archival_id、categories、link | person_id：封存建議的 `subject.id`；archival_id：封存回應的 `archival_id`；link：新的錄用（UC-01 第 2 步回應的 `hire_id`）、個資請求或註銷 |
| UC-14 | 1 | `POST /v1/data-subject-requests` | request_kind、requested_categories、received_on、received_via；人資代登錄時 person_id | 員工本人：person_id 由登入身分對應（user_accounts）；人資代登錄：查人或 UC-01 回應的 person_id |
| UC-14 | 2 | `GET /v1/data-subject-requests/{id}`、`POST /v1/data-subject-requests/{id}/extensions` | data_subject_request_id、extended_deadline、reason、notified_on | 第 1 步回應的 `data_subject_request_id`；期限在 `GET` 回應的 `deadline` |
| UC-14 | 3 | `POST /v1/corrections`、`POST /v1/personal-data-archivals`、`GET /v1/persons/{id}/personal-data-export` | 依請求種類 | person_id：第 1 步的請求 |
| UC-14 | 4 | `POST /v1/data-subject-requests/{id}/resolve` | result、outcome、category_outcomes、refusal_basis | data_subject_request_id：第 1 步回應；被 R55 擋下時 refusal_basis 由系統帶入 |
| UC-15 | 1～3 | `GET /v1/employments/{id}/labor-roster` | employment_id | UC-01 第 5 步回應的 `employment_id`，或查詢員工清單（本切片未設計，見 D-19） |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 | 提出／同意 |
|---|---|---|---|---|---|
| D-01 | 資料庫用 MongoDB | PostgreSQL | 使用者選擇 | PLAN.md D-35；inputs/shared/範圍釐清_平台約定_第五步.md | JiHungLin／JiHungLin（2026-10-14） |
| D-01a | API 用 REST＋OpenAPI 3.1；交付物 `schema.sql` 改為 `schema.mongo.js` | GraphQL；維持 `schema.sql` 檔名 | MongoDB 沒有 SQL schema；REST 的動作式路徑對應 03 的事件 | 同上 | AI／JiHungLin（2026-10-14） |
| D-02 | 一個 Entity 一個集合；只屬於它、不會被別處指到的子項目嵌入（工作許可的每次核准、個資請求的延長紀錄、帶期間的屬性） | 子項目也拆成集合 | 嵌入的子項目跟著主體一起讀寫，交易較單純；它們沒有被別處指到 | PLAN.md D-35 | AI／JiHungLin（2026-10-14） |
| D-03 | 有名字的事件都寫進 `events`，狀態欄位由事件推出，API 不提供直接改狀態（P1） | 只更新狀態欄位，不留事件 | 03 的註銷、撤銷註銷要能找到原事件並依其餘事件重新推導 | P1；03_flows D-03 | AI／JiHungLin（2026-10-14，P1「照建議即可」） |
| D-04 | 加保待辦存成 `enrollment_proposals`（每種保險各自結案或被拒絕），可作廢的 4 種建議共用 `proposals` | 全部放 `events` | 加保待辦有自己的內容且會被取代或結案，要能列出未結案的；其他建議只需要提醒與作廢紀錄 | 03_flows X-22；PLAN.md D-35（P3）；X-02、X-11 | AI／JiHungLin（2026-10-14） |
| D-05 | 人在 DecideHire、RegisterExistingEmployment 的同一交易建立，不另設 API；人的屬性除聯絡方式外一律經 CorrectRecord 更正（會判斷重大更正、重新產生加保待辦）；聯絡方式直接改 | 建立人、改勞工名卡項目當作 P1 的單純欄位直接改（初稿） | 03 更正方式寫明勞工名卡項目走 CorrectRecord 並通知重大更正；出生日期、國籍改變保險適用，直接改會繞過通知與加保待辦（X-06） | 03_flows 更正方式；P1；X-06 | AI／JiHungLin（2026-10-14） |
| D-06 | 所有 API 檢查每個 ref 屬於同一客戶、存在且為目前版本；CorrectRecord 只能改白名單上的欄位（2.2），狀態、誰與何時、事件、通知、規則版本不能改；AnnulEntry 只接受白名單上的事件類型 | 更正 API 不限欄位（初稿） | 不限欄位時，人資可以改個資請求的收到日來逃避期限、改狀態繞過 P1、指到別的客戶的資料（X-01） | P1；03_flows D-14；R47、R49；X-01 | AI／JiHungLin（2026-10-14） |
| D-07 | 重大更正通知獨立成 `significant_corrections`，沒有作廢或修改的 API | 和其他建議共用 `proposals`（初稿） | 03 拿掉更正核准，補償就是通知與清單；做更正的人不能把通知作廢（X-02） | 03_flows D-02、事件表；X-02 | AI／JiHungLin（2026-10-14） |
| D-08 | P7 的遮蔽：新增 `POST /v1/personal-data-erasures` 與 `erasure_records`；保存期間以同一人在該客戶最後一段僱傭關係的結束日起算；`change_log`、`events`、`enrollment_proposals`、`warning_overrides`、`outbox` 不存個資明文，只存參照，遮蔽時才處理得完整（使用者照建議） | 只遮蔽主體欄位（初稿）；遮蔽時逐一掃描所有集合改寫 | 個資複本散在變更紀錄、事件證據、判定依據與外送訊息，只遮蔽主體等於沒遮蔽；同一個人在同客戶另一家公司仍在職時不能遮蔽（X-05）。03 已把依法刪除的做法交給第 ⑤ 步依 P7 設計 | P7；03_flows 個資的說明；X-05；EQ-022 | AI／JiHungLin（2026-10-14） |
| D-09 | 系統使用者帳號用 `user_accounts` 對應到 Person（可空），員工提出個資請求、查自己的資料時以此確認本人；已離職、到職前取消的人怎麼取得帳號由平台決定（使用者選 A） | 員工不能自己提出，一律由人資代登錄 | 02 寫明 Person 不是系統使用者帳號；03 允許員工自己提出（X-14） | 02 Person；03_flows DataSubjectRequest；X-14 | AI／JiHungLin（2026-10-14） |
| D-10 | 引用一律指 `entity_id`；只新增的集合每次寫入產生新版本文件，`is_current` 加唯一索引保證只有一份目前版本 | 引用指 `_id`；以 `superseded_at` 為空判斷目前版本（初稿） | 換版後 `_id` 會變，掛在上面的投保、契約、警告忽略會指到舊版本；03 D-03 要求身分不變（X-03） | 03_flows D-03；X-03 | AI／JiHungLin（2026-10-14） |
| D-11 | `events` 只新增，註銷不回寫原事件；被註銷的文件以快取欄位 `annulled` 標示，所有判定與計數排除 | 原事件記 `annulled_by_event_id`（初稿） | 註銷可以來回多次，單一欄位會被蓋掉；被註銷的到職若仍是 Active，會佔住員工編號、被算進人數（X-04） | 03_flows D-03、D-14；X-04 | AI／JiHungLin（2026-10-14） |
| D-12 | 時間或條件觸發的事件標 `derived`，依據的日期被更正時標為失效並重新推導；各集合的 `status` 是快取，由有效的事件重算 | 時間觸發的事件也當成不可動的事實（初稿） | 03 D-12 要求期限更正後狀態回到正確的值；這類事件是推導的，又不能註銷（X-08） | 03_flows D-12、D-14；P3；X-08 | AI／JiHungLin（2026-10-14） |
| D-13 | 回任時以證件找人：只有人資能查，只回傳是否存在與 Person 編號，查詢留稽核紀錄；證件索引不唯一 | 一般查詢 API 用證號篩選（初稿） | 任何登入者都能用身分證號確認某人是否曾在公司，還會看到已封存的資料（X-07） | 02 Person、IdentityDocument、D-05；R52；X-07 | AI／JiHungLin（2026-10-14） |
| D-14 | 新增一段國籍、戶籍期間（歸化、出國除籍、新設籍）在 03 沒有對應的事件，但 03 D-17 把它列為加保待辦的觸發來源。使用者選 A：回頭修改第 ③ 步，新增事件 RecordPersonPeriod（登錄人的身分期間，03_flows D-18） | 用 CorrectRecord 處理，事件類型標「新增期間」 | 這是新的事實，不是更正；用 CorrectRecord 會混淆「登錯」與「真的改變」，重大更正的判斷也會不準 | 03_flows D-17；X-06 | AI／JiHungLin（2026-10-14） |
| D-15 | R04 的同時寫入保護：交易中更新 `employment_locks` 讓同時的交易衝突 | 只在 service 讀取後檢查（初稿） | MongoDB 交易是快照隔離，兩個交易各自讀到「沒有重疊」、各自新增不同文件時不會衝突（X-12） | R04；X-12 | AI／JiHungLin（2026-10-14） |
| D-16 | `persons` 改為只新增（A），聯絡方式拆到 `person_contacts` 直接覆寫 | 人的資料用 B（初稿） | 國籍、戶籍、老年給付在 03 標「需要重建當時」，且決定保險適用（法規），依使用者選的規則應為 A（X-13） | 03_flows 不需要狀態機的東西；PLAN.md D-35（P2）；X-13 | AI／JiHungLin（2026-10-14） |
| D-17 | `POST /hires` 可以一併帶約定薪資（compensation）與勞動契約（contract），同一交易建立；回應給所有建立項目的編號 | 約定薪資只能錄用後另外呼叫 `POST /compensations` | 03_flows DecideHire 本來就寫「有到職前簽的契約、約定薪資時一起掛上」，初版 api.yaml 漏了（實作回報問題 2）；分開呼叫時 R11 的最低工資警告在錄用當下判斷不了 | 03_flows 事件表 DecideHire；X-17 | AI／JiHungLin（2026-10-14） |
| D-18 | api.yaml 的請求與回應寫到欄位層級：必填、巢狀物件；同一個動作建立的每個項目，回應都給編號（例：錄用回 `hire_id`、`person_id`、`compensation_id`、`contract_id`） | 回應只給 `entity_id`、`event_id`（初版） | 實作時錄用拿不到 person_id，下一步登錄證件做不下去（實作回報問題 1）；請求只寫 object，實作只好自己定必填與結構（問題 4）；工具包 @ ee24004 新增第六區與欄位層級的要求 | docs/01 ⑤；X-16、X-18 | AI／JiHungLin（2026-10-14） |
| D-19 | 員工清單查詢（例：依雇主列出在職員工）本切片不設計，UC-15 從前一步回應或其他切片的清單取得 employment_id | 本切片新增清單 API | 03 沒有清單相關的 UC；列表與搜尋屬一般查詢，等需要它的切片（例：組織、出勤）再設計 | 第六區 UC-15 | AI／JiHungLin（2026-10-14） |
| D-20 | 04_rules 版本欄為「—」的規則（沒有版本的業務規則與法規檢查），警告與警告忽略紀錄的版本，用規則所在的 04 凍結版本（例：hire-employee/04-v3）、修訂 1；規則文字在新的凍結版本改變時，之前的忽略依 R51 失效 | 版本欄「—」時警告不帶版本 | api.yaml 的警告格式要求版本（實作回報 signoff.md #16）；R51 要靠版本判斷忽略是否失效，規則文字改了，忽略就該重新評估；實作暫時的做法（填 04-v2）正好符合 | signoff.md #16；R51；P5 | AI／JiHungLin（2026-10-14） |
| D-21 | 待人判斷事項的決定用 `POST /v1/enrollment-proposals/{id}/decisions` 記在加保待辦上；加保待辦加 `estimated`（錄用時的預估）、`days_overdue`（逾期，不能忽略）；`StartEmploymentIn`、補登加 `public_or_military_insurance_covered` | 另設集合記錄決定 | 比照雇主選擇不加自願保險的做法（03_flows D-19）；實作回報 signoff.md #13～#15、#17 | 04_rules D-15～D-18；03_flows D-19 | AI／JiHungLin（2026-10-14） |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|
| X-01 | 通用更正、註銷 API 沒限制集合與欄位，也沒檢查同一客戶：可改個資請求收到日逃避期限、改狀態、指到別的客戶 | AI 挑錯 | 接受，已修改 | D-06：所有 API 檢查 ref；新增 2.2 可更正的欄位 |
| X-02 | 重大更正通知放在可作廢的 proposals，做更正的人能把通知作廢 | AI 挑錯 | 接受，已修改 | D-07：獨立成 significant_corrections，沒有作廢 API |
| X-03 | 只新增換版後 _id 會變，引用會指到舊版本；狀態變化是改原文件還是開新版本沒寫 | AI 挑錯 | 接受，已修改 | D-10：引用指 entity_id；每次寫入都開新版本，is_current 唯一索引 |
| X-04 | 註銷用單一欄位，來回多次會被蓋掉；被註銷的到職仍是 Active，佔住員工編號、算進人數 | AI 挑錯 | 接受，已修改 | D-11：註銷不回寫；annulled 快取；判定與計數排除 |
| X-05 | 遮蔽只做在主體欄位，複本留在變更紀錄、事件證據、判定依據、outbox；同一人在同客戶另一家公司仍在職會被誤遮；沒有遮蔽的 API 與紀錄 | AI 挑錯 | 接受，已修改 | 第四節 P7 列出所有複本位置與遮蔽方式；新增遮蔽 API 與 erasure_records |
| X-06 | D-05 讓人的資料直接修改，繞過重大更正通知與加保待辦；新增國籍、戶籍期間沒有事件 | AI 挑錯 | 接受，已修改 | D-05 改寫：除聯絡方式外一律經 CorrectRecord；新增期間的事件待決定 |
| X-07 | 以證號查人沒有權限、會查到已封存的人；證件索引若做成唯一會擋下同證號的第二筆 | AI 挑錯 | 接受，已修改 | D-13：只有人資能查，只回傳存在與編號，留稽核；索引不唯一 |
| X-08 | 時間觸發的事件存成不可動的事實，日期更正後狀態推不回來；status 的資料身分沒寫；org-setup 的變化怎麼觸發加保待辦沒寫 | AI 挑錯 | 接受，已修改 | D-12：derived 與失效標記，status 為快取；org-setup 的變化透過 outbox 觸發，寫在第五節 outbox |
| X-09 | 封存的解除只能記一次，部分解除會讓全部類別可見；連到的紀錄沒檢查是不是同一人 | AI 挑錯 | 接受，已修改 | releases[] 每次一筆，status 依剩下的類別推出；R57 檢查同一人、同一客戶 |
| X-10 | 規則版本沒有修訂欄位，R51「修訂不同」判斷不了，登錯只能原地改 | AI 挑錯 | 接受，已修改 | rule_versions 加 revision、recorded_at、supersedes，只新增；所有引用記到修訂 |
| X-11 | 加保待辦標 A 卻要回寫；結案、拒絕只記一個值，撐不住多種保險 | AI 挑錯 | 接受，已修改 | 結案與拒絕移到 items[] 每一列；保存方式改 B |
| X-12 | 同時送出的補登可以繞過期間不重疊（快照隔離的寫入偏斜） | AI 挑錯 | 接受，已修改 | D-15：employment_locks |
| X-13 | 查不到「當時系統知道的判定」；人的國籍、戶籍、老年給付用 B 和使用者選的規則不符 | AI 挑錯 | 接受，已修改 | applicability 加 as_of；D-16：persons 改 A |
| X-14 | 員工自己提出個資請求認不出本人；查閱、複製沒有 API；請求沒記涉及哪些類別 | AI 挑錯 | 接受，已修改 | 補 GET 進度、匯出 API；加 requested_categories、category_outcomes |
| X-15 | D-01 的提出者寫錯；D-03 使用者已同意；tenant_id 的說明包含共用集合；UC-11 標題沿用舊的補登界線說法 | AI 挑錯 | 接受，已修改 | D-01 拆成 D-01、D-01a；D-03 寫同意；第五節改寫；UC-11 改用新說法；上游 03_use_cases UC-11 標題與 03_flows 詞彙表的舊說法，使用者同意回頭修正（03_flows D-18） |
| X-16 | 錄用的回應沒有 person_id，下一步登錄證件拿不到人的編號 | 審查者（實作回報，impl/hire-employee @ b88a209） | 接受，已修改 | D-18：api.yaml 回應給所有建立項目的編號；第六區逐步寫出輸入來源 |
| X-17 | 錄用的請求帶不進約定薪資 | 審查者（實作回報） | 接受，已修改 | 查 03：DecideHire 本來就帶約定薪資，問題在 api.yaml（D-17）；不是 R11 的套用對象 |
| X-18 | api.yaml 太寬鬆：請求只寫 object、沒有必填與巢狀結構，實作只好自己定 | 審查者（實作回報） | 接受，已修改 | D-18：api.yaml 改寫到欄位層級（77 個 schema） |
| X-19 | 就保排除公教或軍保者的條件，API 與資料結構沒有欄位 | 審查者（實作回報 signoff.md #13，impl/hire-employee @ c7f2176） | 接受，已修改 | 02 D-37；employments 加欄位；到職與補登的請求加欄位 |
| X-20 | 待人判斷的結果與決定沒有欄位 | 審查者（實作回報 signoff.md #14） | 接受，已修改 | D-21：decisions API 與欄位 |
| X-21 | R36 逾期警告沒有出口 | 審查者（實作回報 signoff.md #15） | 接受，已修改 | 04_rules D-17：改為判定，以 days_overdue 呈現 |
| X-22 | 版本欄為「—」的規則，警告仍要求版本 | 審查者（實作回報 signoff.md #16） | 接受，已修改 | D-20 |
| X-23 | 錄用時的加保待辦用哪一天沒寫 | 審查者（實作回報 signoff.md #17） | 接受，已修改 | 04_rules D-18；加保待辦加 estimated |

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每個 Entity 都有對應的表，或寫明「不落地」「由靜態參數產生」與理由 | ✓ 19 個 Entity 都有集合（1.1）；org-setup 提供的 5 個標 [靜態替代]；推導屬性（年齡、年資、人數、晚辦天數、月薪資總額）寫明不落地（AI 比對 02 的卡片） | |
| 每張業務表、每支 API、每個業務欄位都指得回概念，沒有「多出來、說不出代表什麼」的表；主鍵、建立時間等技術欄位與平台需要的表，標明「技術」即可（平台 P8） | ✓ 1.2 每個欄位列出對應的概念；schema.mongo.js 每個集合的 description、api.yaml 每支 API 的 x-concept 都寫了概念；技術欄位與平台表列在第五節（AI 比對）。P7 的 erasure_records、user_accounts 是平台約定 P7 與 D-09 的需要，不是 03 的概念，已寫明依據 | |
| ② 標為推導值的東西，都已依平台 P3 決定身分 | ✓ 第四節：各保險的適用、期限、級距、晚辦天數、年齡、年資、人數、月薪資總額、移工契約實際期限、法規警告、勞工名卡都標「不存，現算」；狀態與 annulled 標快取（AI 比對 02「不是 Entity」的推導值） | |
| ③ 標出的歷史需求，都已依平台 P2 決定保存方式 | ✓ 第四節逐項：需要重建當時者為 A（Person、證件、僱傭關係、約定薪資、工作許可、投保、投保薪資）；需要軌跡者為 B；聯絡方式為 C（AI 比對 03 的 12 個狀態機與「不需要狀態機的東西」） | |
| ③ 的每個動作與狀態變更都有對應的 API，且符合平台 P1 | ✓ 第二節：35 個事件中，人觸發的 24 個有 API，時間或條件觸發與建議層的由系統產生並有查詢 API；狀態只由事件改變，CorrectRecord 不能改狀態（2.2）（AI 比對 03 事件表） | |
| ④ 的每條規則都已決定落實位置（平台 P6） | ✓ 第三節涵蓋 R01～R63（R54 已取消不列）：db constraint 4 條、人工 2 條、其餘 service（AI 比對 04 規則表） | |
| 每個正式 Use Case 都已在對照表走一遍：每一步的輸入都拿得到；來自前一步回應的，`api.yaml` 該回應有這個欄位 | ✓ 第六區 15 個 UC 逐步對到 API，每一步的輸入都寫出來源；來自回應的欄位（hire_id、person_id、employment_id、enrollment_id、work_authorization_id、identity_document_id、warning_override_id、data_subject_request_id、archival_id、annulment_event_id 等）都在 api.yaml 該 API 的回應格式中（AI 比對）。UC-15 的 employment_id 來自前一步回應或其他切片的清單（D-19） | |
| `api.yaml` 每支 API 的請求與回應都寫到欄位層級，業務欄位對得回對照表第一區；說明（summary）提到的欄位都在格式裡 | ✓ 37 支 API 的請求與回應都是具名 schema（79 個），有 required、巢狀物件的欄位、additionalProperties: false；業務欄位與第一區一致（AI 比對）；summary 提到的約定薪資、契約、建立項目的編號都在格式中 | |
| 已做紙上驗證：每筆黃金案例依設計推演的結果與人工預期一致；不一致的已回頭修改 | ✓ 使用者選用 GC01～GC03 並填預期結果；AI 依設計推演後比對：GC01 一致；GC02、GC03 初次共 3 處不一致，使用者複核後都是預期結果需更正（勞保生效日翌日、移工時間差不警告、健保期限始日不算入），設計不需回頭修改。結果仍有前提待專家確認：EQ-003（健保、勞退生效日）、EQ-012（伙食津貼算不算入） | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
