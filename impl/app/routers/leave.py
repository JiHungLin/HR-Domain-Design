"""annual-leave-grant 的 API（slices/annual-leave-grant/api.yaml），以及 UC-08 用到的 hire-employee POST /v1/corrections。

請求、回應格式與 x- 欄位直接取自 api.yaml（app/spec.py）。
"""
from datetime import date, datetime

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from app.auth import Actor, current_actor, hr
from app.db import database
from app.leave import actions, queries
from app.services import corrections
from app.spec import RequestInvalid, openapi_extra, validate_request

router = APIRouter(prefix="/v1")
OID = "^[0-9a-f]{24}$"


def _post(path: str, op_id: str):
    return router.post(path, status_code=201, operation_id=op_id, openapi_extra=openapi_extra(op_id))


def _get(path: str, op_id: str):
    return router.get(path, operation_id=op_id, openapi_extra=openapi_extra(op_id))


def _date(v: str | None, name: str) -> date | None:
    try:
        return date.fromisoformat(v) if v else None
    except ValueError as e:
        raise RequestInvalid([f"{name}：{e}"])


def _datetime(v: str | None, name: str) -> datetime | None:
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None
    except ValueError as e:
        raise RequestInvalid([f"{name}：{e}"])


# ---- 寫入 ----

@_post("/leave-entitlements/backfill", "registerExistingLeaveEntitlement")
def register_existing(body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.backfill(database(), actor, validate_request("registerExistingLeaveEntitlement", body))


@_post("/leave-entitlements/{id}/notices", "recordLeaveNotice")
def record_notice(id: str, body: dict = Body(...), actor: Actor = Depends(current_actor)):
    return actions.record_notice(database(), actor, id, validate_request("recordLeaveNotice", body))


@_post("/leave-year-agreements", "recordLeaveYearAgreement")
def record_year_agreement(body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.record_year_agreement(database(), actor, validate_request("recordLeaveYearAgreement", body))


@_post("/leave-year-agreements/{id}/end", "endLeaveYearAgreement")
def end_year_agreement(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.end_year_agreement(database(), actor, id, validate_request("endLeaveYearAgreement", body))


@_post("/company-policies", "establishCompanyPolicy")
def establish_policy(body: dict = Body(...), actor: Actor = Depends(current_actor)):
    return actions.establish_policy(database(), actor, validate_request("establishCompanyPolicy", body))


@_post("/leave-deferral-agreements", "recordLeaveDeferral")
def record_deferral(body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.record_deferral(database(), actor, validate_request("recordLeaveDeferral", body))


@_post("/leave-deferral-agreements/{id}/amend", "amendLeaveDeferral")
def amend_deferral(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.amend_deferral(database(), actor, id, validate_request("amendLeaveDeferral", body))


@_post("/leave-deferral-agreements/{id}/withdraw", "withdrawLeaveDeferral")
def withdraw_deferral(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.withdraw_deferral(database(), actor, id, validate_request("withdrawLeaveDeferral", body))


@_post("/leave-conversions/{id}/confirm", "confirmLeaveConversion")
def confirm_conversion(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.confirm_conversion(database(), actor, id, validate_request("confirmLeaveConversion", body))


@_post("/leave-entitlements/{id}/used-quantity-fixture", "loadUsedQuantityFixture")
def load_used_quantity(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.load_used_quantity(database(), actor, id, validate_request("loadUsedQuantityFixture", body))


@_post("/employments/{id}/ending-fixture", "loadEmploymentEndingFixture")
def load_ending(id: str, body: dict = Body(...), actor: Actor = Depends(hr)):
    return actions.load_ending(database(), actor, id, validate_request("loadEmploymentEndingFixture", body))


@_post("/corrections", "correctRecord")
def correct_record(body: dict = Body(...), actor: Actor = Depends(hr)):
    try:
        return corrections.correct_record(database(), actor, validate_request("correctRecord", body))
    except corrections.NotImplementedYet as e:
        return JSONResponse(status_code=501, content={"detail": e.detail, "operationId": "correctRecord"})


# ---- 查詢 ----

@_get("/employments/{id}/leave-entitlements", "listLeaveEntitlements")
def list_entitlements(id: str, on: str | None = None, leave_type_code: str | None = None, as_of: str | None = None,
                      actor: Actor = Depends(current_actor)):
    return queries.list_entitlements(database(), actor, id, _date(on, "on"), leave_type_code, _datetime(as_of, "as_of"))


@_get("/leave-entitlements/{id}", "getLeaveEntitlement")
def get_entitlement(id: str, as_of: str | None = None, actor: Actor = Depends(current_actor)):
    return queries.get_entitlement(database(), actor, id, _datetime(as_of, "as_of"))


@_get("/employments/{id}/leave-forecast", "getLeaveForecast")
def forecast(id: str, until: str = Query(...), actor: Actor = Depends(current_actor)):
    return queries.forecast(database(), actor, id, _date(until, "until"))


@_get("/employments/{id}/leave-year-basis", "getLeaveYearBasis")
def year_basis(id: str, on: str | None = None, actor: Actor = Depends(current_actor)):
    return queries.year_basis(database(), actor, id, _date(on, "on"))


@_get("/employments/{id}/leave-warnings", "listLeaveWarnings")
def leave_warnings(id: str, actor: Actor = Depends(current_actor)):
    return queries.leave_warnings(database(), actor, id)


@_get("/leave-work-items", "listLeaveWorkItems")
def work_items(employer_id: str = Query(..., pattern=OID), actor: Actor = Depends(current_actor)):
    return queries.work_items(database(), actor, employer_id)


@_get("/leave-conversions", "listLeaveConversions")
def list_conversions(employment_id: str | None = Query(None, pattern=OID), employer_id: str | None = Query(None, pattern=OID),
                     status: str | None = Query(None, pattern="^(Provisional|Determined|Discarded)$"),
                     payment_due_before: str | None = None, actor: Actor = Depends(current_actor)):
    return queries.list_conversions(database(), actor, employment_id, employer_id, status,
                                    _date(payment_due_before, "payment_due_before"))


@_get("/leave-reassessment-notices", "listLeaveReassessmentNotices")
def list_notices(employer_id: str | None = Query(None, pattern=OID), employment_id: str | None = Query(None, pattern=OID),
                 root_event_id: str | None = Query(None, pattern=OID), since: str | None = None,
                 actor: Actor = Depends(current_actor)):
    return queries.list_notices(database(), actor, employer_id, employment_id, root_event_id, _datetime(since, "since"))


@_get("/leave-reassessment-notices/{id}", "getLeaveReassessmentNotice")
def get_notice(id: str, actor: Actor = Depends(current_actor)):
    return queries.get_notice(database(), actor, id)


@_get("/leave-year-agreements", "listLeaveYearAgreements")
def list_year_agreements(employment_id: str = Query(..., pattern=OID), actor: Actor = Depends(current_actor)):
    return queries.list_year_agreements(database(), actor, employment_id)


@_get("/company-policies", "listCompanyPolicies")
def list_policies(employer_id: str | None = Query(None, pattern=OID), subject: str | None = None,
                  actor: Actor = Depends(current_actor)):
    return queries.list_policies(database(), actor, employer_id, subject)


@_get("/company-policies/{id}", "getCompanyPolicy")
def get_policy(id: str, actor: Actor = Depends(current_actor)):
    return queries.get_policy(database(), actor, id)


@_get("/leave-types", "listLeaveTypes")
def list_leave_types(actor: Actor = Depends(current_actor)):
    return queries.list_leave_types(database())
