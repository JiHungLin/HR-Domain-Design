# hire-employee ⑤ 投影到實作

| 項目 | 內容 |
|---|---|
| 切片 | hire-employee |
| 步驟 | ⑤ 投影到實作 |
| 狀態 | 草稿 |
| 版本 | （凍結後填 tag，例：hire-employee/05-v1） |
| 產出者 | AI（Claude）＋ |
| 讀取的輸入 | 02_entities.md @ hire-employee/02-v3；03_flows.md、03_use_cases.md @ hire-employee/03-v2；04_rules.md @ hire-employee/04-v1；docs/03 平台架構約定（P4、P5、P10 照文件；P1、P2、P3、P6、P7、P8 與資料庫依 PLAN.md D-35；P11 依 PLAN.md D-31） |

<!-- 資料庫為 MongoDB（PLAN.md D-35），本文件的「表」是集合（collection），「欄位」是文件的欄位。
     概念 ID 寫 core/ 的英文識別名稱；技術欄位標 [技術]（P8）。本步先只產出這份對照表，經人確認後才產生 schema.mongo.js 與 api.yaml。 -->

## 一、概念 → 表與欄位

### 1.1 集合

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| Tenant | `tenants` | `name` | org-setup 建立維護，本切片唯讀 [靜態替代] |
| Person | `persons` | 見 1.2 | 客戶內一份（P11、PLAN.md D-31） |
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
| PersonalDataArchival | `personal_data_archivals` | 見 1.2 | 覆寫＋變更紀錄（P2 B） |
| DataSubjectRequest | `data_subject_requests` | 見 1.2 | 覆寫＋變更紀錄（P2 B）；延長紀錄嵌在 `extensions` |
| ProposeEnrollmentFiling（事件，建議層） | `enrollment_proposals` | 見 1.2 | 加保待辦是事實（PLAN.md D-35 P3）：記當時依據的資料與規則版本；被新的判定取代或結案，不刪除 |
| 其他建議層事件：PromptStartConfirmation、ProposeAuthorizationReview、PromptDataSubjectRequestDeadline、ProposeArchival、NotifySignificantCorrection | `proposals` | `kind`（事件名稱）、`subject_ref`、`payload`、`dismissed_by`、`dismissed_at`、`dismiss_reason`、`superseded_by` | 不改變狀態；可作廢的保留作廢紀錄（03_flows 事件表「能否撤銷」）；NotifySignificantCorrection 不可作廢 |
| 所有有名字的事件（P1） | `events` | 見 1.3 | 每次動作一筆，狀態由事件推出 |
| 規則與版本（P5） | `rule_versions` | `rule_id`（R01…）、`version`、`effective_from`、`effective_to`、`params`（例：每月最低工資、分級表）、`source_ref` | 規則以資料存在，不寫死在程式（P5）；R12、R40～R43 的金額與分級表放 `params` |
| 分類值的多語名稱（P10） | `labels` | `code`（例：`APPLICABILITY.MANDATORY`）、`locale`、`label` | 代碼不隨語言改變；zh-TW 名稱取自 04_rules 分類值表與詞彙對照表 |

### 1.2 業務欄位

型別：`date`＝日期（不含時刻）；`datetime`＝時刻；`ref`＝指到另一個集合的 `_id`；`code`＝分類值代碼；`[]`＝陣列。

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| Person.legal_name | `persons` | `legal_name`（string） | 勞工名卡項目；P2 B |
| Person.gender | `persons` | `gender`（code） | P2 B |
| Person.birth_date | `persons` | `birth_date`（date） | P2 B |
| Person.nationalities | `persons` | `nationalities[]`：`country_code`、`acquired_on`、`lost_on` | 帶期間，判定看某一天的值 |
| Person.education | `persons` | `education`（string） | P2 B |
| Person.address | `persons` | `address`（string） | P2 B |
| Person.contact | `persons` | `contact`：`phone`、`email` | 只需現況，直接覆寫（P2 C、P1 單純欄位） |
| Person.old_age_benefits_received | `persons` | `old_age_benefits_received[]`：`scheme_code`、`received_on` | 帶日期 |
| Person.civil_registrations | `persons` | `civil_registrations[]`：`jurisdiction_id`、`registered_on`、`deregistered_on` | 帶期間 |
| Person.age | — | — | 不落地（推導，P3）；由 `birth_date` 與判定日現算（R29） |
| belongsToTenant（Person、Employer、OrgUnit） | `persons`、`employers`、`org_units` | `tenant_id`（ref） | 業務關係；其他集合的 `tenant_id` 是隔離用的技術欄位（第五節） |
| IdentityDocument.document_kind | `identity_documents` | `document_kind`（code） | |
| IdentityDocument.document_number | `identity_documents` | `document_number`（string） | 回任時以此辨識同一人（Q11）：索引 `tenant_id`＋`document_kind`＋`issuing_jurisdiction_id`＋`document_number` |
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
| WarningOverride 各屬性 | `warning_overrides` | `rule_ref`：`rule_id`、`version`；`subject_ref`：`collection`、`id`、`field`；`warned_value`、`overridden_by`、`overridden_at`、`reason`、`withdrawn_by`、`withdrawn_at`、`status` | |
| concernsHire、concernsEmployment | `warning_overrides` | `hire_id`、`employment_id`（至少一個，R09） | |
| PersonalDataArchival 各屬性 | `personal_data_archivals` | `person_id`、`data_categories[]`（code）、`archived_on`、`archived_by`、`released_on`、`release_reason`、`release_link`（錄用、個資請求或註銷的 ref，R57）、`status` | |
| DataSubjectRequest 各屬性 | `data_subject_requests` | `person_id`、`request_kind`（code）、`received_on`、`received_via`、`resolved_on`、`outcome`、`refusal_basis`：`rule_id`、`rule_version`、`legal_basis`、`reason`；`status` | |
| DataSubjectRequest.extensions | `data_subject_requests` | `extensions[]`：`extended_deadline`、`reason`、`notified_on`、`recorded_by` | 每次延長一筆（03_flows D-15） |
| ProposeEnrollmentFiling 的內容 | `enrollment_proposals` | `hire_id` 或 `employment_id`；`determined_on`（判定日 d）；`items[]`：`scheme_code`、`applicability`（code）、`filing_deadline`、`legal_effective_date`、`expected_grade`、`days_overdue`；`basis`：用到的資料版本與 `rule_versions`；`superseded_by`；`closed_by_enrollment_id`；`voluntary_declined`：`by`、`at` | 不由人作廢（03_flows X-22） |

### 1.3 事件紀錄（`events`，P1、P4）

| 概念 | 表 | 欄位 | 備註 |
|---|---|---|---|
| 事件名稱 | `events` | `type`（例：`StartEmployment`） | 03_flows 事件表的 34 個事件 |
| 主體 | `events` | `subject`：`collection`、`id` | |
| 發生時間、得知時間、生效時間 | `events` | `occurred_at`、`recorded_at`、`effective_from` | 依 03_flows 事件表「有意義的時間」，不需要的留空（P4） |
| 誰做的 | `events` | `actor`：`user_id`、`role` | 時間或條件觸發的寫 `system` |
| 證據 | `events` | `evidence[]`、`reason` | |
| 依據的規則版本 | `events` | `rule_versions[]` | 判定類事件記（P5） |
| 註銷 | `events` | `annulled_by_event_id`、`annulment_revoked_by_event_id` | AnnulEntry／RevokeAnnulment（03_flows D-03、D-14） |
| 補登標記 | `events` | `is_backfill`（bool） | RegisterExistingEmployment |

## 二、事件 → API

API 以 REST 描述（OpenAPI 3.1），路徑前綴 `/v1`；每支 API 標 `x-concept`（P8）。每次呼叫在同一個多文件交易中寫入 `events` 與受影響的集合（PLAN.md D-35）。

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
| RecordInsuranceFiling | `POST /v1/insurance-enrollments` | 人資；R50 擋下（回執或標示無回執） |
| DeclareInsuredSalary | `POST /v1/insurance-enrollments/{id}/insured-salaries` | 人資 |
| OverrideWarning | `POST /v1/warning-overrides` | 人資；R09、R10 擋下 |
| WithdrawWarningOverride | `POST /v1/warning-overrides/{id}/withdraw` | 人資 |
| ReceiveDataSubjectRequest | `POST /v1/data-subject-requests` | 員工本人（自己的）或人資（代登錄） |
| ExtendDataSubjectRequest | `POST /v1/data-subject-requests/{id}/extensions` | 人資；R63 提醒 |
| ResolveDataSubjectRequest | `POST /v1/data-subject-requests/{id}/resolve` | 人資；R55 擋下刪除保存期間內的類別 |
| ArchivePersonalData | `POST /v1/personal-data-archivals` | 人資 |
| ReleaseArchival | `POST /v1/personal-data-archivals/{id}/release` | 人資；R57 擋下 |
| CorrectRecord | `POST /v1/corrections` | 人資；R49、R50 擋下；重大更正（R46）產生通知 |
| AnnulEntry | `POST /v1/annulments` | 人資；R47、R48 擋下 |
| RevokeAnnulment | `POST /v1/annulments/{id}/revoke` | 人資 |
| ContractTermStarts、VoidContract、ExpireWorkAuthorization、ExpireIdentityDocument、LapseWarningOverride | 無 API：系統排程或事件處理器產生 | 系統；寫 `events`，`actor`＝system |
| ProposeEnrollmentFiling | 系統產生；`GET /v1/enrollment-proposals`（列出）、`POST /v1/enrollment-proposals/{id}/decline-voluntary`（雇主選擇不加自願保險） | 讀：人資、雇主；拒絕自願：雇主或人資 |
| PromptStartConfirmation、ProposeAuthorizationReview、PromptDataSubjectRequestDeadline、ProposeArchival | 系統產生；`GET /v1/proposals`、`POST /v1/proposals/{id}/dismiss` | 人資 |
| NotifySignificantCorrection | 系統產生；`GET /v1/significant-corrections` | 雇主（老闆）、人資；不可作廢 |
| （查詢）UC-15 勞工名卡 | `GET /v1/employments/{id}/labor-roster` | 處理人事的人資（R52）；已封存的類別不顯示 |
| （查詢）UC-02 判定結果 | `GET /v1/employments/{id}/applicability?on=<date>` | 人資；現算，不落地 |

### 2.1 Use Case → API

| UC | 用到的 API |
|---|---|
| UC-01 錄用本國籍員工並到職 | `POST /persons`（第一次）→ `POST /persons/{id}/identity-documents` → `POST /hires` → `POST /compensations` → `POST /employment-contracts` → `POST /hires/{id}/start` → `GET /enrollment-proposals` |
| UC-02 判定各保險 | 系統產生 `enrollment_proposals`；`GET /employments/{id}/applicability` |
| UC-03 登錄實際加保與投保薪資 | `POST /insurance-enrollments` → `POST /insurance-enrollments/{id}/insured-salaries` |
| UC-04 錄用外籍員工 | UC-01 ＋ `POST /work-authorizations`、`POST /work-authorizations/{id}/approvals`、`POST /work-authorizations/{id}/end` |
| UC-05 到職前改期 | `POST /hires/{id}/reschedule` |
| UC-06 到職前取消 | `POST /hires/{id}/cancel`；系統產生封存建議 → `POST /personal-data-archivals` |
| UC-07 登錄勞動契約 | `POST /employment-contracts` |
| UC-08 更正與註銷 | `POST /corrections`、`POST /annulments`、`POST /annulments/{id}/revoke`；`GET /significant-corrections` |
| UC-09 忽略警告與撤回 | `POST /warning-overrides`、`POST /warning-overrides/{id}/withdraw` |
| UC-10 到職後立刻離開 | `POST /employments/{id}/early-departure` |
| UC-11 補登既有員工 | `POST /persons` → `POST /employments/backfill`（同一交易登錄目前的投保、投保薪資、約定薪資） |
| UC-12 回任 | 以證件號碼查 `GET /persons?document_number=` → UC-01 |
| UC-13 封存與解除 | `POST /personal-data-archivals`、`POST /personal-data-archivals/{id}/release` |
| UC-14 個資請求 | `POST /data-subject-requests` → `POST /data-subject-requests/{id}/extensions` → `POST /data-subject-requests/{id}/resolve` |
| UC-15 查詢勞工名卡 | `GET /employments/{id}/labor-roster` |

`GET /persons?document_number=` 與 `POST /persons` 是 UC 需要、但 03 沒有對應事件的動作：建立人與更新勞工名卡項目屬 P1 的單純欄位（P2 B，變更紀錄可追溯），見 D-05。

## 三、規則 → 落實位置
<!-- db constraint／db trigger／service／人工；MongoDB 沒有 trigger，「db constraint」指集合的驗證規則與唯一索引（PLAN.md D-35） -->

| 規則 | 落實位置 | 說明 |
|---|---|---|
| R02、R03 | db constraint | 同一文件內的日期比較，用集合驗證規則的 `$expr`（例：`ended_on >= start_date`）；service 再檢查一次以回傳清楚的訊息 |
| R05 | db constraint ＋ service | 部分唯一索引：`tenant_id`＋`employer_id`＋`employee_number`，條件 `status`＝Active 且為目前版本；補登已結束者的期間重疊由 service 檢查 |
| R09 | db constraint | 驗證規則：`hire_id`、`employment_id` 至少一個 |
| R01、R04、R06、R07、R08、R10 | service | 跨集合比較，在動作的交易中檢查，違反時擋下 |
| R47～R50、R57 | service | 流程規則，違反時擋下（inputs/shared/範圍釐清_擋下的範圍.md） |
| R55 | service | 處理刪除請求時，比對資料類別與保存期間，擋下並自動帶入拒絕的依據（R62） |
| R52 | service（權限） | API 層依角色與資料類別檢查；已封存的類別一般查詢不回傳（P7） |
| R11、R13～R18、R20、R21、R36、R45、R58、R61、R62、R63 | service | 法規檢查，只提醒：回傳警告，使用者可用 OverrideWarning 忽略 |
| R12、R22～R35、R37～R44、R59、R60 | service | 判定與計算，依 `rule_versions` 取當時的版本現算；結果寫進 `enrollment_proposals` 或查詢時回傳，不落地為事實 |
| R46、R51、R53、R56 | service | 判定後產生通知、失效事件、期限提醒、封存建議 |
| R19 | 人工 | 是否為繼續性工作由人資判斷；系統只在簽定期契約時提醒並要求勾選（EQ-021） |
| R24（擇一參加的部分） | 人工 ＋ service | 受僱於兩個以上雇主時，由人決定參加哪一個，記在加保待辦 |

## 四、推導值與歷史需求 → 儲存
<!-- 資料身分：事實／快取／凍結快照；保存方式：A／B／C／— -->

| 概念 | 資料身分（P3） | 保存方式（P2） |
|---|---|---|
| Person 的勞工名卡項目（姓名、性別、出生日期、教育程度、住址） | 事實 | B |
| Person 的國籍、戶籍、老年給付 | 事實（帶期間） | B（期間本身記錄改變；更正留變更紀錄） |
| Person.contact | 事實 | C |
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
| 加保待辦（ProposeEnrollmentFiling） | 事實（記當時的判定與規則版本） | A：不改，只會被新的一筆取代或結案 |
| 事件紀錄（`events`） | 事實 | A |
| 各保險的適用、應辦理期限、法定生效日、應申報級距 | 推導值：不存，現算 | — |
| 晚辦天數（InsuranceEnrollment.days_late） | 推導值：不存，現算 | — |
| 年齡、年資、雇主人數、投保單位計入人數、月薪資總額 | 推導值：不存，現算 | — |
| 移工契約的實際期限（R59） | 推導值：不存，現算 | — |
| 法規警告 | 推導值：不存，現算；被忽略的記在 WarningOverride | — |
| 勞工名卡（UC-15） | 推導值：查詢時組出 | — |

**A 只新增的做法（MongoDB）**：同一個概念的每次更正新增一份版本文件，欄位 `entity_id`、`revision`、`supersedes`、`superseded_at`、`correction_event_id`；目前版本是 `superseded_at` 為空的那一份。**B 的做法**：直接更新文件，同時在 `change_log` 新增一筆（不可刪）。

**P7 刪除與遮蔽**：保存期間內只封存（`personal_data_archivals`），一般查詢不回傳；期間過後刪除可識別個人的欄位（例：姓名、證號、住址改為遮蔽值），業務事實（到職日、加保日）保留。哪些必須真的刪除 [待專家確認: EQ-022]。

## 五、技術欄位與平台表

| 表或欄位 | 用途 |
|---|---|
| `_id`（每個集合） | [技術] 主鍵（ObjectId） |
| `tenant_id`（Person、Employer、OrgUnit 以外的集合） | [技術] 客戶隔離；所有查詢與索引都帶 |
| `entity_id`、`revision`、`supersedes`、`superseded_at`、`correction_event_id` | [技術] P2 A 的版本欄位 |
| `created_at`、`updated_at`、`schema_version` | [技術] |
| `change_log` | [技術] 平台表：P2 B 的變更紀錄（集合、文件、欄位、舊值、新值、誰、何時、事件） |
| `outbox` | [技術] 平台表：事件發布給其他服務 |
| `x-concept`（OpenAPI）、集合驗證規則的 `description` | [技術] P8：標出對應的概念 ID |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 | 提出／同意 |
|---|---|---|---|---|---|
| D-01 | 資料庫用 MongoDB，交付物 `schema.sql` 改為 `schema.mongo.js`；API 用 REST＋OpenAPI 3.1 | PostgreSQL＋`schema.sql` | 使用者選擇 | PLAN.md D-35；inputs/shared/範圍釐清_平台約定_第五步.md | JiHungLin／JiHungLin（2026-10-14） |
| D-02 | 一個 Entity 一個集合；只屬於它、不會被別處指到的子項目嵌入（工作許可的每次核准、個資請求的延長紀錄、帶期間的屬性） | 子項目也拆成集合 | 嵌入的子項目跟著主體一起讀寫，交易較單純；它們沒有被別處指到 | PLAN.md D-35 | AI／JiHungLin（2026-10-14） |
| D-03 | 有名字的事件都寫進 `events`，狀態欄位由事件推出，API 不提供直接改狀態（P1） | 只更新狀態欄位，不留事件 | 03 的註銷、撤銷註銷要能找到原事件並依其餘事件重新推導 | P1；03_flows D-03 | AI／待確認 |
| D-04 | 加保待辦存成 `enrollment_proposals`，其他建議層事件共用 `proposals` | 全部放 `events` | 加保待辦有自己的內容（各保險的判定、期限、雇主不加自願保險的紀錄）且會被取代或結案，要能列出未結案的；其他建議只需要提醒與作廢紀錄 | 03_flows X-22；PLAN.md D-35（P3） | AI／待確認 |
| D-05 | 建立人（`POST /persons`）、改勞工名卡項目不另設事件，當作 P1 的單純欄位，靠 `change_log` 追溯 | 新增事件 RegisterPerson | 03 沒有建立人的事件，人是在錄用或補登時被登錄；勞工名卡項目的歷史需求是「需要軌跡」（P2 B），變更紀錄就足夠 | 03_flows 不需要狀態機的東西；P1 判斷 | AI／待確認 |
| D-06 | 回任時以證件辨識同一人：索引 `tenant_id`＋證件種類＋核發地＋證號 | 以姓名＋出生日期 | 02 Person 的身分寫明以證件號碼辨識（Q11） | 02 Person、IdentityDocument | AI／待確認 |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）；「審查者確認」由非產出者填寫 -->
<!-- CHECKLIST:START -->
| 完成標準 | AI 自評 | 審查者確認 |
|---|---|---|
| 每個 Entity 都有對應的表，或寫明「不落地」「由靜態參數產生」與理由 | | |
| 每張業務表、每支 API、每個業務欄位都指得回概念，沒有「多出來、說不出代表什麼」的表；主鍵、建立時間等技術欄位與平台需要的表，標明「技術」即可（平台 P8） | | |
| ② 標為推導值的東西，都已依平台 P3 決定身分 | | |
| ③ 標出的歷史需求，都已依平台 P2 決定保存方式 | | |
| ③ 的每個動作與狀態變更都有對應的 API，且符合平台 P1 | | |
| ④ 的每條規則都已決定落實位置（平台 P6） | | |
| 每個正式 Use Case 都能用一組 API 完成 | | |
| 已做紙上驗證：每筆黃金案例依設計推演的結果與人工預期一致；不一致的已回頭修改 | | |
<!-- CHECKLIST:END -->

- 審查者（非產出者）：
- 日期：
- 結論：通過 ／ 退回（原因）
