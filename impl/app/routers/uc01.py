"""UC-01～UC-03 的 API。路徑、operationId、x-concept 與 api.yaml 一致（P8）。"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app import models
from app.auth import Actor, current_actor, hr
from app.db import database, oid
from app.services import hiring, insurance, proposals

router = APIRouter(prefix="/v1")


def _x(concept: str, rules: list[str] | None = None, roles=("HR",)) -> dict:
    return {"x-concept": concept, "x-roles": list(roles), **({"x-rules": rules} if rules else {})}


@router.post("/hires", status_code=201, operation_id="decideHire", openapi_extra=_x("DecideHire", ["R11", "R14"]))
def decide_hire(body: models.DecideHireIn, actor: Actor = Depends(hr)):
    return hiring.decide_hire(database(), actor, body)


@router.post("/hires/{id}/start", status_code=201, operation_id="startEmployment",
             openapi_extra=_x("StartEmployment", ["R01", "R04", "R05", "R06", "R11", "R14", "R15", "R16", "R21"]))
def start_employment(id: str, body: models.StartEmploymentIn, actor: Actor = Depends(hr)):
    return hiring.start_employment(database(), actor, id, body)


@router.post("/persons/{id}/identity-documents", status_code=201, operation_id="recordIdentityDocument",
             openapi_extra=_x("RecordIdentityDocument", ["R03"]))
def record_identity_document(id: str, body: models.RecordIdentityDocumentIn, actor: Actor = Depends(hr)):
    return hiring.record_identity_document(database(), actor, id, body)


@router.post("/compensations", status_code=201, operation_id="agreeCompensation",
             openapi_extra=_x("AgreeCompensation", ["R11", "R39"]))
def agree_compensation(body: models.AgreeCompensationIn, actor: Actor = Depends(hr)):
    return hiring.agree_compensation(database(), actor, body)


@router.post("/employment-contracts", status_code=201, operation_id="signContract",
             openapi_extra=_x("SignContract", ["R03", "R18", "R19", "R20", "R59"]))
def sign_contract(body: models.SignContractIn, actor: Actor = Depends(hr)):
    return hiring.sign_contract(database(), actor, body)


@router.post("/insurance-enrollments", status_code=201, operation_id="recordInsuranceFiling",
             openapi_extra=_x("RecordInsuranceFiling", ["R07", "R50", "R61"]))
def record_insurance_filing(body: models.RecordInsuranceFilingIn, actor: Actor = Depends(hr)):
    return insurance.record_insurance_filing(database(), actor, body)


@router.post("/insurance-enrollments/{id}/insured-salaries", status_code=201, operation_id="declareInsuredSalary",
             openapi_extra=_x("DeclareInsuredSalary", ["R40", "R41", "R42", "R43", "R45"]))
def declare_insured_salary(id: str, body: models.DeclareInsuredSalaryIn, actor: Actor = Depends(hr)):
    return insurance.declare_insured_salary(database(), actor, id, body)


@router.get("/enrollment-proposals", operation_id="listEnrollmentProposals",
            openapi_extra=_x("ProposeEnrollmentFiling", ["R22", "R36"], roles=("HR", "EMPLOYER")))
def list_enrollment_proposals(status: str | None = None, actor: Actor = Depends(current_actor)):
    actor.require("HR", "EMPLOYER")
    return proposals.list_proposals(database(), actor.tenant_id, status, date.today())


@router.get("/employments/{id}/applicability", operation_id="getApplicability",
            openapi_extra=_x("各保險的適用（推導）", ["R22", "R23", "R24", "R25", "R26", "R27", "R28", "R29", "R31", "R32",
                                                   "R33", "R34", "R35", "R40", "R41", "R42", "R43", "R44", "R60"]))
def get_applicability(id: str, on: date = Query(...), as_of: datetime | None = None, actor: Actor = Depends(hr)):
    return proposals.applicability_on(database(), actor.tenant_id, oid(id), on, as_of)
