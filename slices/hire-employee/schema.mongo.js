// hire-employee ⑤ 資料結構（MongoDB，mongosh 腳本）
// 依 05_mapping.md（hire-employee，對照表經使用者確認 2026-10-14）產生；設計文件，不在任何實際資料庫執行。
// 每個集合的 description 寫對應的概念 ID（平台 P8）；[技術] 為不對應業務概念的欄位。
// 型別慣例：日期（不含時刻）存成 UTC 午夜的 date；金額用 decimal（Decimal128）；ref 指另一個概念的 entity_id（05_mapping D-10）。

const ref = { bsonType: "objectId" };
const date = { bsonType: "date" };
const str = { bsonType: "string" };
const code = { bsonType: "string", pattern: "^[A-Z][A-Z0-9_]*\\.[A-Z0-9_]+$" };
const money = { bsonType: "decimal" };
const bool = { bsonType: "bool" };
const period = (valueSchema) => ({
  bsonType: "array",
  items: { bsonType: "object", required: ["from"], properties: { value: valueSchema, code: code, from: date, to: date } },
});

// P2 A（只新增）集合共用的版本欄位 [技術]
const versioned = {
  entity_id: ref, revision: { bsonType: "int", minimum: 1 }, supersedes: ref,
  is_current: bool, recorded_at: date, event_id: ref,
};
const tenantScoped = { tenant_id: ref };              // [技術] 客戶隔離
const tech = { created_at: date, updated_at: date, schema_version: { bsonType: "int" } };
const cache = { annulled: bool };
const decision = { bsonType: "object", required: ["kind", "result", "by", "at"], properties: {
  kind: { enum: ["EMPLOYMENT_INSURANCE_CHOICE", "ALLOWANCE_INCLUSION"] }, allowance_name: str, result: str, by: ref, at: date, reason: str } };                     // [技術] 快取：由註銷與撤銷事件推出（05_mapping D-11）

function create(name, concept, required, properties, extra = {}) {
  db.createCollection(name, {
    validator: {
      $jsonSchema: { bsonType: "object", description: concept, required, properties: { ...tech, ...properties } },
      ...(extra.expr ? { $expr: extra.expr } : {}),
    },
    validationLevel: "strict",
    validationAction: "error",
  });
}
const currentOnly = (keys, extraFilter = {}) => ({ partialFilterExpression: { is_current: true, ...extraFilter } });

// ---------- 全平台共用的參考資料（不分客戶） ----------
create("jurisdictions", "Jurisdiction", ["code", "level"], { code: str, level: code, parent_id: ref });
db.jurisdictions.createIndex({ code: 1 }, { unique: true });

create("social_insurance_schemes", "SocialInsuranceScheme", ["jurisdiction_id", "code", "insurer", "effective_from"],
  { jurisdiction_id: ref, code: code, insurer: code, effective_from: date });
db.social_insurance_schemes.createIndex({ code: 1 }, { unique: true });

create("rule_versions", "規則版本（P5）；R01～R63", ["rule_id", "version", "revision", "effective_from", "recorded_at"],
  { rule_id: { bsonType: "string", pattern: "^R\\d+$" }, version: str, revision: { bsonType: "int", minimum: 1 },
    effective_from: date, effective_to: date, params: { bsonType: "object" }, source_ref: str, recorded_at: date, supersedes: ref });
db.rule_versions.createIndex({ rule_id: 1, version: 1, revision: 1 }, { unique: true });

create("labels", "分類值的多語名稱（P10）", ["code", "locale", "label"], { code: str, locale: str, label: str });
db.labels.createIndex({ code: 1, locale: 1 }, { unique: true });

// ---------- org-setup 提供 [靜態替代] ----------
create("tenants", "Tenant", ["name"], { name: str });

create("employers", "Employer", ["tenant_id", "legal_name", "employer_type", "jurisdiction_id"], {
  tenant_id: ref, legal_name: str, employer_type: code, jurisdiction_id: ref,
  registrations: { bsonType: "array", items: { bsonType: "object", required: ["kind", "registered_on"], properties: { kind: code, registered_on: date } } },
  registration_exempt: period(bool), tax_assessed_or_invoice_permit: period(bool),
  labor_insurance_industry_category: period(code), labor_standards_act_applicable: period(bool),
  system_managed_from: date,
});
db.employers.createIndex({ tenant_id: 1 });

create("insurance_units", "InsuranceUnit", ["tenant_id", "employer_id", "insurer", "unit_code"],
  { ...tenantScoped, employer_id: ref, insurer: code, unit_code: str, established_on: date, scheme_codes: { bsonType: "array", items: code } });
db.insurance_units.createIndex({ insurer: 1, unit_code: 1 }, { unique: true });

create("org_units", "OrgUnit", ["tenant_id", "name"],
  { tenant_id: ref, name: str, parent_id: period(ref), employer_id: period(ref) });

create("work_locations", "WorkLocation", ["tenant_id", "name", "jurisdiction_id"],
  { ...tenantScoped, name: str, address: str, jurisdiction_id: ref });

// ---------- 本切片的業務集合 ----------
// Person：P2 A（05_mapping D-16）；聯絡方式另放 person_contacts（P2 C）
create("persons", "Person", ["tenant_id", "entity_id", "revision", "is_current", "legal_name"], {
  tenant_id: ref, ...versioned,
  legal_name: str, gender: code, birth_date: date, education: str, address: str,
  nationalities: { bsonType: "array", items: { bsonType: "object", required: ["country_code", "acquired_on"], properties: { country_code: str, acquired_on: date, lost_on: date } } },
  civil_registrations: { bsonType: "array", items: { bsonType: "object", required: ["jurisdiction_id", "registered_on"], properties: { jurisdiction_id: ref, registered_on: date, deregistered_on: date } } },
  old_age_benefits_received: { bsonType: "array", items: { bsonType: "object", required: ["scheme_code", "received_on"], properties: { scheme_code: code, received_on: date } } },
}, { expr: { $lte: ["$birth_date", "$recorded_at"] } }); // R03：出生日期不晚於登錄當天
db.persons.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.persons.createIndex({ tenant_id: 1, entity_id: 1 });

create("person_contacts", "Person.contact", ["tenant_id", "person_id"], { ...tenantScoped, person_id: ref, phone: str, email: str });
db.person_contacts.createIndex({ person_id: 1 }, { unique: true });

create("identity_documents", "IdentityDocument", ["tenant_id", "entity_id", "revision", "is_current", "person_id", "issuing_jurisdiction_id", "document_kind", "document_number", "valid_from"], {
  ...tenantScoped, ...versioned, person_id: ref, issuing_jurisdiction_id: ref,
  document_kind: code, document_number: str, valid_from: date, valid_until: date, residence_basis: code, status: code,
}, { expr: { $or: [{ $eq: [{ $type: "$valid_until" }, "missing"] }, { $gte: ["$valid_until", "$valid_from"] }] } }); // R03
db.identity_documents.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
// 回任辨識同一人（Q11）：不唯一（同證號可有多筆，02 D-05；05_mapping D-13）
db.identity_documents.createIndex({ tenant_id: 1, document_kind: 1, issuing_jurisdiction_id: 1, document_number: 1 });

create("hires", "Hire", ["tenant_id", "person_id", "employer_id", "decided_on", "planned_start_date", "status"], {
  ...tenantScoped, person_id: ref, employer_id: ref, planned_work_location_id: ref, planned_org_unit_id: ref,
  decided_on: date, planned_start_date: date, cancellation_reason: str, cancelled_on: date, prior_insurance_elsewhere: str,
  status: { enum: ["Hired", "Cancelled", "Started"] }, ...cache,
});
db.hires.createIndex({ tenant_id: 1, status: 1, planned_start_date: 1 });

create("employments", "Employment", ["tenant_id", "entity_id", "revision", "is_current", "person_id", "employer_id", "start_date", "status"], {
  ...tenantScoped, ...versioned, ...cache, person_id: ref, employer_id: ref, hire_id: ref,
  start_date: date, ended_on: date, end_reason: code, employee_number: str,
  employee_category: period(code), probation_until: date, historical_basis_note: str,
  public_or_military_insurance_covered: period(bool), // 02 D-37；就保 R24
  org_unit_assignments: { bsonType: "array", items: { bsonType: "object", properties: { org_unit_id: ref, from: date, to: date } } },
  work_locations: { bsonType: "array", items: { bsonType: "object", properties: { work_location_id: ref, from: date, to: date } } },
  status: { enum: ["Active", "Ended"] },
}, { expr: { $or: [{ $eq: [{ $type: "$ended_on" }, "missing"] }, { $gte: ["$ended_on", "$start_date"] }] } }); // R02
db.employments.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
// R05：同一雇主在職員工編號不重複（D-03）；被註銷的不算（05_mapping D-11）
db.employments.createIndex({ tenant_id: 1, employer_id: 1, employee_number: 1 },
  { unique: true, partialFilterExpression: { is_current: true, status: "Active", annulled: false } });
db.employments.createIndex({ tenant_id: 1, person_id: 1, employer_id: 1, is_current: 1 });

create("employment_locks", "[技術] R04 同時寫入保護（05_mapping D-15）", ["tenant_id", "person_id", "employer_id"],
  { ...tenantScoped, person_id: ref, employer_id: ref, seq: { bsonType: "long" } });
db.employment_locks.createIndex({ tenant_id: 1, person_id: 1, employer_id: 1 }, { unique: true });

create("employment_contracts", "EmploymentContract", ["tenant_id", "contract_type", "status"], {
  ...tenantScoped, ...cache, employment_id: ref, hire_id: ref,
  contract_type: code, fixed_term_nature: code, term_start: date, term_end: date, in_writing: bool,
  status: { enum: ["Signed", "InForce", "Ended", "Voided"] },
}, { expr: { $or: [{ $eq: [{ $type: "$term_end" }, "missing"] }, { $gte: ["$term_end", "$term_start"] }] } }); // R03

create("compensations", "Compensation", ["tenant_id", "entity_id", "revision", "is_current", "effective_from", "currency", "pay_basis", "monthly_base_salary"], {
  ...tenantScoped, ...versioned, employment_id: ref, hire_id: ref,
  effective_from: date, currency: str, pay_basis: code, monthly_base_salary: money,
  fixed_monthly_allowances: { bsonType: "array", items: { bsonType: "object", required: ["name", "category", "amount"], properties: { name: str, category: code, amount: money } } },
  status: code,
});
db.compensations.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });

create("work_authorizations", "WorkAuthorization", ["tenant_id", "entity_id", "revision", "is_current", "person_id", "jurisdiction_id", "authorization_basis", "status"], {
  ...tenantScoped, ...versioned, person_id: ref, jurisdiction_id: ref, employer_id: ref, based_on_document_id: ref, replaces_id: ref,
  authorization_basis: code, work_category: code,
  approvals: { bsonType: "array", items: { bsonType: "object", required: ["valid_from", "valid_until"], properties: { permit_number: str, valid_from: date, valid_until: date, recorded_at: date } } },
  valid_from: date, valid_until: date, // 只用於免申請者（02 D-33）
  status: { enum: ["Valid", "Expired"] },
});
db.work_authorizations.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });

create("insurance_enrollments", "InsuranceEnrollment", ["tenant_id", "entity_id", "revision", "is_current", "employment_id", "scheme_id", "filed_on", "voluntary", "status"], {
  ...tenantScoped, ...versioned, ...cache, employment_id: ref, scheme_id: ref, insurance_unit_id: ref,
  filed_on: date, voluntary: bool, effective_from: date, receipt_ref: str, no_receipt: bool,
  status: { enum: ["Enrolled", "Terminated"] },
});
db.insurance_enrollments.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.insurance_enrollments.createIndex({ tenant_id: 1, employment_id: 1 });

create("insured_salaries", "InsuredSalary", ["tenant_id", "entity_id", "revision", "is_current", "enrollment_id", "declared_amount", "effective_from", "source"], {
  ...tenantScoped, ...versioned, ...cache, enrollment_id: ref,
  declared_amount: money, grade: str, grading_table_version: { bsonType: "object", properties: { rule_id: str, version: str, revision: { bsonType: "int" } } },
  declared_on: date, source: code, effective_from: date, receipt_ref: str, no_receipt: bool,
  status: { enum: ["Effective", "Superseded"] },
});
db.insured_salaries.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });

create("warning_overrides", "WarningOverride", ["tenant_id", "rule_ref", "subject_ref", "overridden_by", "overridden_at", "status"], {
  ...tenantScoped, hire_id: ref, employment_id: ref,
  rule_ref: { bsonType: "object", required: ["rule_id", "version", "revision"], properties: { rule_id: str, version: str, revision: { bsonType: "int" } } },
  subject_ref: { bsonType: "object", required: ["collection", "id"], properties: { collection: str, id: ref, field: str } },
  warned_value: {}, overridden_by: ref, overridden_at: date, reason: str, withdrawn_by: ref, withdrawn_at: date,
  status: { enum: ["Active", "Lapsed", "Withdrawn"] },
}, { expr: { $or: [{ $ne: [{ $type: "$hire_id" }, "missing"] }, { $ne: [{ $type: "$employment_id" }, "missing"] }] } }); // R09

create("personal_data_archivals", "PersonalDataArchival", ["tenant_id", "person_id", "data_categories", "archived_on", "archived_by", "status"], {
  ...tenantScoped, person_id: ref, data_categories: { bsonType: "array", items: code }, archived_on: date, archived_by: ref,
  releases: { bsonType: "array", items: { bsonType: "object", required: ["categories", "released_on", "released_by", "link"], properties: {
    categories: { bsonType: "array", items: code }, released_on: date, released_by: ref, reason: str,
    link: { bsonType: "object", required: ["collection", "id"], properties: { collection: { enum: ["hires", "data_subject_requests", "events"] }, id: ref } } } } }, // R57
  status: { enum: ["Archived", "Released"] },
});
db.personal_data_archivals.createIndex({ tenant_id: 1, person_id: 1 });

create("data_subject_requests", "DataSubjectRequest", ["tenant_id", "person_id", "request_kind", "received_on", "received_via", "status"], {
  ...tenantScoped, person_id: ref, request_kind: code, requested_categories: { bsonType: "array", items: code },
  received_on: date, received_via: str, resolved_on: date, outcome: str,
  category_outcomes: { bsonType: "array", items: { bsonType: "object", properties: { category: code, result: str } } },
  refusal_basis: { bsonType: "object", properties: { rule_id: str, rule_version: str, rule_revision: { bsonType: "int" }, legal_basis: str, reason: str } },
  extensions: { bsonType: "array", items: { bsonType: "object", required: ["extended_deadline", "reason", "notified_on"], properties: { extended_deadline: date, reason: str, notified_on: date, recorded_by: ref } } },
  status: { enum: ["Received", "Completed", "Rejected"] },
});
db.data_subject_requests.createIndex({ tenant_id: 1, status: 1, received_on: 1 });

create("enrollment_proposals", "ProposeEnrollmentFiling（加保待辦）", ["tenant_id", "determined_on", "basis", "items"], {
  ...tenantScoped, hire_id: ref, employment_id: ref, determined_on: date, basis: { bsonType: "object" },
  estimated: bool, // 錄用時以約定到職日判定的預估結果（04_rules D-18）
  allowance_decisions: { bsonType: "array", items: decision }, // 「其他」類固定給付算不算入（04_rules D-16）
  needs_decision: { bsonType: "array", items: { bsonType: "object", required: ["kind", "allowance_name"], properties: {
    kind: { enum: ["ALLOWANCE_INCLUSION"] }, allowance_name: str } } }, // 判定時還沒決定的「其他」類固定給付（04_rules D-19）
  items: { bsonType: "array", items: { bsonType: "object", required: ["scheme_code", "applicability"], properties: {
    scheme_code: code, applicability: code, filing_deadline: date, legal_effective_date: date, expected_grade: str, days_overdue: { bsonType: "int" },
    closed_by_enrollment_id: ref, voluntary_declined: { bsonType: "object", properties: { by: ref, at: date } },
    decisions: { bsonType: "array", items: decision } } } }, // 就保擇一參加（04_rules D-16）
  superseded_by: ref,
});
db.enrollment_proposals.createIndex({ tenant_id: 1, employment_id: 1, superseded_by: 1 });

create("proposals", "PromptStartConfirmation／ProposeAuthorizationReview／PromptDataSubjectRequestDeadline／ProposeArchival", ["tenant_id", "kind", "subject_ref"], {
  ...tenantScoped, kind: { enum: ["PromptStartConfirmation", "ProposeAuthorizationReview", "PromptDataSubjectRequestDeadline", "ProposeArchival"] },
  subject_ref: { bsonType: "object" }, payload: { bsonType: "object" }, dismissed_by: ref, dismissed_at: date, dismiss_reason: str, superseded_by: ref,
});

create("significant_corrections", "NotifySignificantCorrection（不可作廢，05_mapping D-07）", ["tenant_id", "correction_event_id", "changed", "notified_at"], {
  ...tenantScoped, correction_event_id: ref, changed: { bsonType: "object" }, affected_employment_ids: { bsonType: "array", items: ref },
  notified_to: { bsonType: "array", items: ref }, notified_at: date,
});

create("events", "事件紀錄（P1、P4）：03_flows 的 35 個事件", ["tenant_id", "type", "subject", "recorded_at", "actor"], {
  ...tenantScoped, type: str, subject: { bsonType: "object", required: ["collection", "id"], properties: { collection: str, id: ref } },
  occurred_at: date, recorded_at: date, effective_from: date,
  actor: { bsonType: "object", properties: { user_id: ref, role: str } },
  evidence: { bsonType: "array", items: { bsonType: "object", properties: { attachment_ref: str, kind: str } } }, reason: str,
  rule_versions: { bsonType: "array", items: { bsonType: "object", properties: { rule_id: str, version: str, revision: { bsonType: "int" } } } },
  target_event_id: ref, target_annulment_id: ref,          // AnnulEntry／RevokeAnnulment
  derived: bool, invalidated_by_event_id: ref, is_backfill: bool,
});
db.events.createIndex({ tenant_id: 1, "subject.collection": 1, "subject.id": 1, recorded_at: 1 });
db.events.createIndex({ target_event_id: 1 }, { sparse: true });

create("erasure_records", "P7 刪除與遮蔽紀錄（05_mapping D-08）", ["tenant_id", "person_id", "trigger", "categories", "performed_by", "performed_at"], {
  ...tenantScoped, person_id: ref, trigger: { enum: ["RETENTION_EXPIRED", "DATA_SUBJECT_REQUEST"] }, data_subject_request_id: ref,
  categories: { bsonType: "array", items: code }, collections_processed: { bsonType: "array", items: str },
  performed_by: ref, performed_at: date, retention_basis: { bsonType: "object" },
});

create("user_accounts", "系統使用者帳號與 Person 的對應（05_mapping D-09）", ["tenant_id", "user_id", "roles"], {
  ...tenantScoped, user_id: str, person_id: ref, roles: { bsonType: "array", items: { enum: ["HR", "EMPLOYER", "EMPLOYEE"] } },
});
db.user_accounts.createIndex({ tenant_id: 1, user_id: 1 }, { unique: true });

// ---------- 平台表 [技術] ----------
create("change_log", "[技術] P2 B 的變更紀錄；個資欄位只存參照（05_mapping D-08）", ["tenant_id", "collection", "document_id", "event_id", "changed_at"], {
  ...tenantScoped, collection: str, document_id: ref, fields: { bsonType: "array", items: str }, before_ref: ref, after_ref: ref,
  event_id: ref, changed_by: ref, changed_at: date,
});
create("outbox", "[技術] 事件發布；只帶 ID 與事件類型，不帶個資", ["tenant_id", "event_id", "type"], { ...tenantScoped, event_id: ref, type: str, published_at: date });
create("audit_log", "[技術] 查詢個資、匯出、以證件查人的紀錄", ["tenant_id", "action", "actor", "at"], { ...tenantScoped, action: str, actor: ref, target: { bsonType: "object" }, at: date });
