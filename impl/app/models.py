"""請求格式。欄位名稱與 slices/hire-employee/api.yaml 一致（tests/test_contract.py 檢查）。

api.yaml 的請求只列欄位、沒有必填與巢狀結構；這裡依 05_mapping 1.2 補上 UC-01、UC-03 需要的必填與型別。
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

Money = Field(pattern=r"^-?\d+(\.\d+)?$")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Nationality(Strict):
    country_code: str
    acquired_on: date
    lost_on: date | None = None


class CivilRegistration(Strict):
    jurisdiction_id: str
    registered_on: date
    deregistered_on: date | None = None


class OldAgeBenefit(Strict):
    scheme_code: str
    received_on: date


class Contact(Strict):
    phone: str | None = None
    email: str | None = None


class PersonIn(Strict):
    """Person 的屬性（05_mapping 1.2）；contact 存到 person_contacts（P2 C）。"""
    legal_name: str
    gender: str | None = None
    birth_date: date | None = None
    education: str | None = None
    address: str | None = None
    nationalities: list[Nationality] = []
    civil_registrations: list[CivilRegistration] = []
    old_age_benefits_received: list[OldAgeBenefit] = []
    contact: Contact | None = None


class DecideHireIn(Strict):
    person: PersonIn
    employer_id: str
    decided_on: date
    planned_start_date: date
    planned_work_location_id: str | None = None
    planned_org_unit_id: str | None = None
    prior_insurance_elsewhere: str | None = None
    occurred_at: datetime | None = None


class StartEmploymentIn(Strict):
    start_date: date
    employee_number: str | None = None
    work_location_id: str | None = None
    org_unit_id: str | None = None
    probation_until: date | None = None
    occurred_at: datetime | None = None


class Allowance(Strict):
    name: str
    category: str
    amount: str = Money


class AgreeCompensationIn(Strict):
    employment_id: str | None = None
    hire_id: str | None = None
    effective_from: date
    currency: str
    pay_basis: str
    monthly_base_salary: str = Money
    fixed_monthly_allowances: list[Allowance] = []
    occurred_at: datetime | None = None


class SignContractIn(Strict):
    employment_id: str | None = None
    hire_id: str | None = None
    contract_type: str
    fixed_term_nature: str | None = None
    term_start: date | None = None
    term_end: date | None = None
    in_writing: bool | None = None
    occurred_at: datetime | None = None


class RecordIdentityDocumentIn(Strict):
    document_kind: str
    issuing_jurisdiction_id: str
    document_number: str
    valid_from: date
    valid_until: date | None = None
    residence_basis: str | None = None
    occurred_at: datetime | None = None


class RecordInsuranceFilingIn(Strict):
    employment_id: str
    scheme_id: str
    insurance_unit_id: str | None = None
    filed_on: date
    voluntary: bool = False
    effective_from: date | None = None
    receipt_ref: str | None = None
    no_receipt: bool | None = None
    occurred_at: datetime | None = None


class DeclareInsuredSalaryIn(Strict):
    declared_amount: str = Money
    grade: str
    declared_on: date
    source: str = "INSURED_SALARY_SOURCE.EMPLOYER_DECLARED"
    effective_from: date
    occurred_at: datetime | None = None
