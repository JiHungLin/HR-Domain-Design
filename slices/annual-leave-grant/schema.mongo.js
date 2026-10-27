// annual-leave-grant ⑤ 資料結構（MongoDB，mongosh 腳本）
// 依 05_mapping.md（annual-leave-grant，對照表經使用者確認 2026-10-21）產生；設計文件，不在任何實際資料庫執行。
// 每個集合的 description 寫對應的概念 ID（平台 P8）；[技術] 為不對應業務概念的欄位。
// 型別慣例同 hire-employee/schema.mongo.js：日期（不含時刻）存成 UTC 午夜的 date；數量用 decimal（Decimal128，05_mapping D-14）；
// ref 指另一個概念的 entity_id（hire-employee 05_mapping D-10）。
// 沿用 hire-employee 已建立的集合：events、rule_versions、labels、employments、employers、warning_overrides、change_log、outbox（本檔不重建）。

const ref = { bsonType: "objectId" };
const date = { bsonType: "date" };
const str = { bsonType: "string" };
const int = { bsonType: "int" };
const code = { bsonType: "string", pattern: "^[A-Z][A-Z0-9_]*\\.[A-Z0-9_]+$" };
const qty = { bsonType: "decimal" };
const bool = { bsonType: "bool" };
const monthDay = { bsonType: "object", required: ["month", "day"], properties: { month: { bsonType: "int", minimum: 1, maximum: 12 }, day: { bsonType: "int", minimum: 1, maximum: 31 } } };
const period = (valueSchema) => ({
  bsonType: "array",
  items: { bsonType: "object", required: ["from"], properties: { value: valueSchema, from: date, to: date } },
});
// 依據的規則版本（LeaveEntitlement.basis_rule_versions、LeaveConversion.basis_rule_versions）
const ruleVersionRefs = {
  bsonType: "array",
  items: {
    bsonType: "object", required: ["kind", "version", "revision"],
    properties: { kind: { enum: ["RULE", "COMPANY_POLICY"] }, rule_id: { bsonType: "string", pattern: "^R\\d+$" }, policy_id: ref, version: str, revision: int },
  },
};

// P2 A（只新增）集合共用的版本欄位 [技術]
const versioned = {
  entity_id: ref, revision: { bsonType: "int", minimum: 1 }, supersedes: ref,
  is_current: bool, recorded_at: date, event_id: ref,
};
const tenantScoped = { tenant_id: ref };              // [技術] 客戶隔離
const tech = { created_at: date, updated_at: date, schema_version: int };
const missing = (f) => ({ $eq: [{ $type: f }, "missing"] });

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
const currentOnly = (extraFilter = {}) => ({ partialFilterExpression: { is_current: true, ...extraFilter } });

// ---------- 全平台共用的參考資料（不分客戶） ----------
// LeaveType：只需現況（P2 C，05_mapping D-13）；名稱放 labels（P10）
create("leave_types", "LeaveType", ["code", "status"], {
  code: code, jurisdiction_id: ref,                                   // establishedBy（0..1）
  status: { enum: ["Active", "Deprecated"] },
});
db.leave_types.createIndex({ code: 1 }, { unique: true });
// 初始資料：台灣特休
db.leave_types.insertOne({ code: "LEAVE_TYPE.ANNUAL_LEAVE_TW", status: "Active" });

// ---------- 本切片的業務集合 ----------
// CompanyPolicy：P2 A；tenant_id 是業務關係 belongsToTenant
create("company_policies", "CompanyPolicy", ["tenant_id", "entity_id", "revision", "is_current", "name", "subject", "effective_from", "status"], {
  tenant_id: ref, ...versioned,
  employer_id: ref, leave_type_code: code,                            // ofEmployer、concernsLeaveType（0..1）
  name: str, subject: code, source_note: str, effective_from: date, effective_to: date,
  status: { enum: ["Scheduled", "Effective", "Repealed"] },           // 快取（P1）
}, { expr: { $or: [missing("$effective_to"), { $gte: ["$effective_to", "$effective_from"] }] } }); // R98
db.company_policies.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.company_policies.createIndex({ tenant_id: 1, employer_id: 1, subject: 1, is_current: 1 });

// 公司規定的版本（規則資料，P5；05_mapping D-01）。只新增：修訂（登錄錯誤，corrects_version）另起一筆 revision
create("company_policy_versions", "公司規定的版本（02「不是 Entity」：規則資料）", ["tenant_id", "policy_id", "version", "revision", "effective_from", "params", "recorded_at"], {
  ...tenantScoped, policy_id: ref, version: str, revision: { bsonType: "int", minimum: 1 },
  effective_from: date, recorded_at: date, supersedes: ref, event_id: ref,
  // 參數名稱照 04 參數表；欄位不存在＝「那一版沒有寫」（04 R79 決策表）
  params: {
    bsonType: "object", additionalProperties: false,
    properties: {
      company_extra_days: { bsonType: "array", items: { bsonType: "object", required: ["from_months", "days"], properties: { from_months: int, to_months: int, days: qty } } },
      company_extra_eligibility: { bsonType: "object", properties: { employee_categories: { bsonType: "array", items: code } } },
      company_extra_year_end_treatment: { enum: ["CONVERSION_TARGET.WAGES", "CONVERSION_TARGET.FORFEITED"] },
      company_extra_deferrable: bool,
      company_default_leave_year: { bsonType: "object", required: ["leave_year_basis"], properties: { leave_year_basis: code, year_start: monthDay } },
      // 沒有時用 rule_versions（R70）的值（05_mapping 3.2、D-31）
      fixed_start_year_method: { enum: ["FIXED_START_YEAR_METHOD.EXTEND_TO_YEAR_END", "FIXED_START_YEAR_METHOD.PRORATED"] },
    },
  },
});
db.company_policy_versions.createIndex({ policy_id: 1, version: 1, revision: 1 }, { unique: true });

// LeaveYearAgreement：需要軌跡（P2 B：覆寫＋change_log）
create("leave_year_agreements", "LeaveYearAgreement", ["tenant_id", "employment_id", "leave_type_code", "leave_year_basis", "effective_from", "agreed_on", "status"], {
  ...tenantScoped, employment_id: ref, leave_type_code: code,         // forEmployment、ofLeaveType
  leave_year_basis: code, year_start: monthDay, effective_from: date, agreed_on: date, agreement_note: str,
  ended_from: date,                                                   // EndLeaveYearAgreement 的生效時間（終止日，05_mapping D-11）
  status: { enum: ["Scheduled", "Effective", "Superseded", "Ended"] },
}, { expr: { $or: [missing("$ended_from"), { $gte: ["$ended_from", "$effective_from"] }] } });
db.leave_year_agreements.createIndex({ tenant_id: 1, employment_id: 1, leave_type_code: 1, effective_from: 1 });

// LeaveEntitlement：需要重建當時（P2 A）；推導的數量不落地（05_mapping D-06）
create("leave_entitlements", "LeaveEntitlement", ["tenant_id", "entity_id", "revision", "is_current", "employment_id", "leave_type_code", "source", "origin", "acquired_on", "quantity", "unit", "valid_from", "valid_to", "basis_rule_versions", "status", "voided"], {
  ...tenantScoped, ...versioned,
  employment_id: ref, leave_type_code: code,                          // forEmployment、ofLeaveType
  source: code, origin: code, period_sequence: int, seniority_tier: int,
  acquired_on: date, quantity: qty, unit: code, valid_from: date, valid_to: date,
  leave_year_basis: code,
  basis_rule_versions: ruleVersionRefs, no_rule_version: bool,        // 補登的：無對應規則版本（PLAN.md D-28）
  basis_seniority: { bsonType: "object", required: ["months", "days"], properties: { months: int, days: int } },
  basis_start_date: date, notified_on: date,
  pre_system_used_quantity: qty, registered_original_year_end: date,
  policy_id: ref, deferred_from_id: ref, deferred_under_id: ref,      // grantedUnderPolicy、deferredFrom、deferredUnder
  applied_year_agreement_id: ref, applied_year_default_policy_id: ref, // appliedYearAgreement、appliedYearDefault
  status: { enum: ["Active", "YearEnded", "EndedWithEmployment", "Voided"] },
  voided: bool,                                                       // [技術] 快取：status＝Voided
}, {
  expr: { $and: [
    { $gte: ["$valid_to", "$valid_from"] },                           // R97
    { $gt: ["$quantity", 0] },                                        // R97（依規則給予的天數不大於 0 不建立，R77）
    { $or: [missing("$pre_system_used_quantity"), { $lte: ["$pre_system_used_quantity", "$quantity"] }] }, // R97
    { $or: [missing("$registered_original_year_end"), { $lt: ["$registered_original_year_end", "$valid_from"] }] }, // R97
    { $not: [{ $and: [{ $ne: [{ $type: "$applied_year_agreement_id" }, "missing"] }, { $ne: [{ $type: "$applied_year_default_policy_id" }, "missing"] }] }] }, // R74
  ] },
});
db.leave_entitlements.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
// 依規則給予不重複（05_mapping 3.1）：排程重跑或同時跑不會給兩筆；policy_id 法定的為 null
db.leave_entitlements.createIndex(
  { tenant_id: 1, employment_id: 1, leave_type_code: 1, source: 1, policy_id: 1, period_sequence: 1 },
  { unique: true, partialFilterExpression: { is_current: true, voided: false, origin: "ENTITLEMENT_ORIGIN.RULE_GRANT" } });
// 一筆原特休最多遞延出一筆（02 deferredFrom）
db.leave_entitlements.createIndex({ deferred_from_id: 1 },
  { unique: true, partialFilterExpression: { is_current: true, voided: false, origin: "ENTITLEMENT_ORIGIN.DEFERRED_IN" } });
db.leave_entitlements.createIndex({ tenant_id: 1, employment_id: 1, is_current: 1, valid_to: 1 });
db.leave_entitlements.createIndex({ tenant_id: 1, status: 1, valid_to: 1, is_current: 1 }); // 排程找「應發生而還沒發生」的年度終結

// LeaveDeferralAgreement：需要重建當時（P2 A）；修改與更正都新增版本，event_id 分得出是哪一種（03_flows D-06）
create("leave_deferral_agreements", "LeaveDeferralAgreement", ["tenant_id", "entity_id", "revision", "is_current", "employment_id", "entitlement_id", "agreed_on", "deferred_quantity", "status"], {
  ...tenantScoped, ...versioned,
  employment_id: ref, entitlement_id: ref,                            // forEmployment、defersEntitlement
  agreed_on: date, deferred_quantity: qty, agreement_note: str,
  status: { enum: ["Agreed", "Applied", "Withdrawn", "Lapsed"] },
}, { expr: { $gt: ["$deferred_quantity", 0] } });                     // R82
db.leave_deferral_agreements.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.leave_deferral_agreements.createIndex({ tenant_id: 1, entitlement_id: 1, is_current: 1 }); // R82 同一筆最多一筆有效（service＋leave_locks）

// LeaveConversion：需要重建當時（P2 A）；已判定的內容不改，差額另記（02 D-06）
create("leave_conversions", "LeaveConversion", ["tenant_id", "entity_id", "revision", "is_current", "employment_id", "entitlement_id", "reason", "target", "quantity", "determined_on", "basis_rule_versions", "status"], {
  ...tenantScoped, ...versioned,
  employment_id: ref,                                                 // [技術] 查詢用；可由 entitlement_id 推出
  entitlement_id: ref, corrects_conversion_id: ref, corrects_judgment_event_id: ref, // convertsFrom、correctsConversion（05_mapping X-09）
  reason: code, target: code, quantity: qty, determined_on: date,
  basis_rule_versions: ruleVersionRefs, correction_cause: code,
  wage_basis_date: date, payment_due_on: date,
  status: { enum: ["Provisional", "Determined", "Discarded"] },
  discarded_by_id: ref,                                               // [技術] 快取
}, { expr: { $and: [
  { $ne: ["$quantity", 0] },                                          // R93：0 不產生轉換
  { $or: [{ $ne: ["$target", "CONVERSION_TARGET.FORFEITED"] }, missing("$payment_due_on")] }, // R90：失效的沒有發給期限
] } });
db.leave_conversions.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.leave_conversions.createIndex({ tenant_id: 1, status: 1, payment_due_on: 1, is_current: 1 }); // 薪資切片、待確認清單
db.leave_conversions.createIndex({ tenant_id: 1, entitlement_id: 1, is_current: 1 });

// LeaveConversionRecovery：需要軌跡（P2 A，只新增；改口是新的一筆，02 D-21、05_mapping D-39）
// 還有效的天數、未收回的天數不存（P3）；涵蓋與天數上限由 service 檢查（04 R101、R103）
create("leave_conversion_recoveries", "LeaveConversionRecovery", ["tenant_id", "entity_id", "revision", "is_current", "employment_id", "conversion_id", "method", "quantity", "responded_on", "status"], {
  ...tenantScoped, ...versioned,
  employment_id: ref,                                                 // [技術] 查詢用；可由 conversion_id 推出
  conversion_id: ref, replaces_recovery_id: ref, offset_by_conversion_id: ref, // recoversConversion、replacesRecovery、offsetByConversion
  method: { enum: ["RECOVERY_METHOD.PAYROLL_DEDUCTION", "RECOVERY_METHOD.REPAYMENT_AGREED", "RECOVERY_METHOD.REPAID",
                   "RECOVERY_METHOD.REFUSED", "RECOVERY_METHOD.DEFERRAL_DECLINED", "RECOVERY_METHOD.OFFSET_BY_REJUDGE"] },
  quantity: qty, responded_on: date, evidence_note: str,
  status: { enum: ["Active", "Annulled"] },
}, { expr: { $and: [
  { $gt: ["$quantity", 0] },                                          // R101
  { $or: [{ $eq: ["$method", "RECOVERY_METHOD.OFFSET_BY_REJUDGE"] }, missing("$offset_by_conversion_id")] }, // offsetByConversion 只有撤回的才有
] } });
db.leave_conversion_recoveries.createIndex({ entity_id: 1, is_current: 1 }, { unique: true, ...currentOnly() });
db.leave_conversion_recoveries.createIndex({ tenant_id: 1, conversion_id: 1, is_current: 1 });
db.leave_conversion_recoveries.createIndex({ tenant_id: 1, employment_id: 1, method: 1, is_current: 1 }); // 依方式查（未收回的名單）

// NotifyLeaveReassessment（建議層，不可作廢，05_mapping D-08）：沒有修改或作廢的 API
create("leave_reassessment_notices", "NotifyLeaveReassessment", ["tenant_id", "employment_id", "trigger_event_id", "root_event_id", "notified_at"], {
  ...tenantScoped, employment_id: ref, trigger_event_id: ref, root_event_id: ref,
  changed: { bsonType: "array", items: { bsonType: "object", required: ["entitlement_id"], properties: { entitlement_id: ref, before: { bsonType: "object" }, after: { bsonType: "object" } } } },
  added_ids: { bsonType: "array", items: ref }, voided_ids: { bsonType: "array", items: ref },
  conversion_ids: { bsonType: "array", items: ref }, provisional_conversion_ids: { bsonType: "array", items: ref },
  action_items: { bsonType: "array", items: { bsonType: "object", required: ["kind"], properties: {
    kind: { enum: ["NOTICE_ACTION.USED_ON_VOIDED", "NOTICE_ACTION.RENOTIFY", "NOTICE_ACTION.REDEFER", "NOTICE_ACTION.USED_OVER_QUANTITY",
                   "NOTICE_ACTION.BACKFILL_OVERLAP_OR_GAP", "NOTICE_ACTION.NOTICE_BEFORE_ACQUIRED", "NOTICE_ACTION.DEFERRAL_OVER_UNUSED",
                   "NOTICE_ACTION.CONVERSION_DATES_CHANGED", "NOTICE_ACTION.PERIOD_CHANGED_WITH_USED", "NOTICE_ACTION.TOP_UP_BACKFILL",
                   "NOTICE_ACTION.TOP_UP_ENDED_EMPLOYMENT", "NOTICE_ACTION.RECOVERY_CHANGED_TO_DEDUCTION", "NOTICE_ACTION.RECOVERY_ANNULLED", "NOTICE_ACTION.RECOVERY_OFFSET"] },
    entitlement_id: ref, detail: str, suggested_quantity: qty } } },   // suggested_quantity：補登那一筆的建議天數（04 R100）
  notified_to: { bsonType: "array", items: { enum: ["HR", "EMPLOYER", "EMPLOYEE"] } }   // EMPLOYEE：可休天數改變時（03_flows D-24）, notified_at: date,
});
db.leave_reassessment_notices.createIndex({ tenant_id: 1, root_event_id: 1 });
db.leave_reassessment_notices.createIndex({ tenant_id: 1, employment_id: 1, notified_at: -1 });

// ---------- [靜態替代] 固定資料（05_mapping D-10） ----------
// 已休：annual-leave-request 定義請假事實後取代；P2 B（改正記誰、何時、理由）
create("leave_used_quantity_fixtures", "LeaveEntitlement.used_quantity [靜態替代]", ["tenant_id", "entitlement_id", "used_quantity", "recorded_by", "recorded_at", "reason"], {
  ...tenantScoped, entitlement_id: ref, used_quantity: qty, recorded_by: ref, recorded_at: date, reason: str,
}, { expr: { $gte: ["$used_quantity", 0] } });
db.leave_used_quantity_fixtures.createIndex({ entitlement_id: 1 }, { unique: true });

// 契約約定的工資給付日（04 參數 wage_payment_day、wage_payment_lag_months，04 D-23）：
// monthly-payroll 定義後取代；P2 C；平台維運載入，沒有 API；沒有登錄時用 rule_versions（R90）的值（05_mapping 3.2、D-21、D-31）
// 2026-10-22：payment_deadline_rule 移到 contract_settings（05_mapping D-36）
create("employer_settings", "參數 wage_payment_day、wage_payment_lag_months [靜態替代]", ["tenant_id", "employer_id"], {
  ...tenantScoped, employer_id: ref,
  wage_payment_day: period({ bsonType: "int", minimum: 1, maximum: 31 }),
  wage_payment_lag_months: period({ bsonType: "int", minimum: 0, maximum: 1 }),
});
db.employer_settings.createIndex({ employer_id: 1 }, { unique: true });

// 勞動契約約定的發給期限做法（04 參數 payment_deadline_rule，依勞動契約，04 D-33；05_mapping D-36）：
// P2 B（每一段帶雙方簽字的日子與憑據，舊的不刪）；平台維運載入，沒有 API，載入記 LoadContractSettingsFixture；
// value 為 null＝契約寫明沒有約定，用 rule_versions（R90）的預設；沒有這份契約的文件或那天沒有一段＝資料不足（04 R90、05_mapping D-42）
// 存 04 分類值的完整代碼（05_mapping D-35）；用計算發給期限的錨點那一天查（05_mapping D-32）
create("contract_settings", "參數 payment_deadline_rule（依勞動契約）[靜態替代]", ["tenant_id", "employment_contract_id"], {
  ...tenantScoped, employment_contract_id: ref,
  payment_deadline_rule: {
    bsonType: "array",
    items: { bsonType: "object", required: ["value", "from", "agreed_on"], properties: {
      value: { enum: ["PAYMENT_DEADLINE_RULE.CONTRACT_WAGE_PAYMENT_DAY", "PAYMENT_DEADLINE_RULE.DAYS_AFTER_YEAR_END", null] },
      from: date, to: date, agreed_on: date, basis_note: str } },
  },
});
db.contract_settings.createIndex({ employment_contract_id: 1 }, { unique: true });

// ---------- 平台表 [技術] ----------
create("leave_locks", "[技術] 同一段僱傭關係（或同一雇主的公司規定）的同時寫入保護（05_mapping D-05、D-18）", ["tenant_id", "scope", "key_id"], {
  ...tenantScoped, scope: { enum: ["EMPLOYMENT", "EMPLOYER_POLICY"] }, key_id: ref, seq: { bsonType: "long" },
});
db.leave_locks.createIndex({ tenant_id: 1, scope: 1, key_id: 1 }, { unique: true });

create("leave_reassessment_queue", "[技術] 雇主層級的改變要重新判定的僱傭關係（05_mapping D-18）", ["tenant_id", "employment_id", "root_event_id", "reason", "enqueued_at"], {
  ...tenantScoped, employment_id: ref, root_event_id: ref, reason: str, enqueued_at: date,
  processed_at: date, attempts: int, last_error: str,
});
db.leave_reassessment_queue.createIndex({ tenant_id: 1, employment_id: 1, processed_at: 1 });

create("job_runs", "[技術] 每日排程的執行紀錄（只供維運查；排程不靠它決定要補哪幾天，05_mapping X-04）", ["job", "started_at"], {
  job: str, tenant_id: ref, started_at: date, finished_at: date, employments_processed: int, errors: { bsonType: "array", items: str },
});

// ---------- 既有集合的擴充（hire-employee 建立） ----------
// events：本切片的事件另帶 payload（05_mapping 1.3）。hire-employee 的 $jsonSchema 沒有 additionalProperties: false，
// 不需要 collMod；欄位：payload.year_end（CloseLeaveYear、RejudgeLeaveYearEnd）、payload.reassessment（ReassessLeaveEntitlements）。
db.events.createIndex({ tenant_id: 1, type: 1, "subject.id": 1 });
// labels：26 個分類值的 zh-TW 名稱取自 04_rules 分類值表（P10），由平台維運載入。
