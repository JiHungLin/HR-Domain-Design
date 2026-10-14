"""UC-01～UC-03 的 API。請求、回應格式與 x- 欄位直接取自 api.yaml（app/spec.py）。"""
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Query

from app.auth import Actor, current_actor, hr
from app.db import database, oid
from app.services import hiring, insurance, proposals
from app.spec import RequestInvalid, openapi_extra, validate_request

router = APIRouter(prefix="/v1")


def _post(path: str, op_id: str):
    return router.post(path, status_code=201, operation_id=op_id, openapi_extra=openapi_extra(op_id))


def _get(path: str, op_id: str):
    return router.get(path, operation_id=op_id, openapi_extra=openapi_extra(op_id))


@_post("/hires", "decideHire")
def decide_hire(body: dict = Body(...), actor: Actor = Depends(hr)):
    return hiring.decide_hire(database(), actor, validate_request("decideHire", body))


@_post("/hires/{id}/start", "startEmployment")
def start_employment(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return hiring.start_employment(database(), actor, id, validate_request("startEmployment", body))


@_post("/persons/{id}/identity-documents", "recordIdentityDocument")
def record_identity_document(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return hiring.record_identity_document(database(), actor, id, validate_request("recordIdentityDocument", body))


@_post("/compensations", "agreeCompensation")
def agree_compensation(body: dict = Body(...), actor: Actor = Depends(hr)):
    return hiring.agree_compensation(database(), actor, validate_request("agreeCompensation", body))


@_post("/employment-contracts", "signContract")
def sign_contract(body: dict = Body(...), actor: Actor = Depends(hr)):
    return hiring.sign_contract(database(), actor, validate_request("signContract", body))


@_post("/insurance-enrollments", "recordInsuranceFiling")
def record_insurance_filing(body: dict = Body(...), actor: Actor = Depends(hr)):
    return insurance.record_insurance_filing(database(), actor, validate_request("recordInsuranceFiling", body))


@_post("/insurance-enrollments/{id}/insured-salaries", "declareInsuredSalary")
def declare_insured_salary(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return insurance.declare_insured_salary(database(), actor, id, validate_request("declareInsuredSalary", body))


@_get("/enrollment-proposals", "listEnrollmentProposals")
def list_enrollment_proposals(employment_id: str | None = Query(None, pattern="^[0-9a-f]{24}$"),
                              hire_id: str | None = Query(None, pattern="^[0-9a-f]{24}$"),
                              open: bool | None = None, actor: Actor = Depends(current_actor)):
    actor.require("HR", "EMPLOYER")
    return proposals.list_proposals(database(), actor.tenant_id, employment_id, hire_id, open)


@_get("/employments/{id}/applicability", "getApplicability")
def get_applicability(id: str, on: str = Query(...), as_of: str | None = None, actor: Actor = Depends(hr)):
    from datetime import date
    try:
        d = date.fromisoformat(on)
        a = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else None
    except ValueError as e:
        raise RequestInvalid([f"on／as_of：{e}"])
    return proposals.applicability_on(database(), actor.tenant_id, oid(id), d, a)
