"""api.yaml 中還沒實作的 API：照規格註冊，回 501，讓對外的 API 清單與設計一致。"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.spec import spec


def router_for_missing(*implemented_routers: APIRouter) -> APIRouter:
    implemented = {r.operation_id for rt in implemented_routers for r in rt.routes}
    router = APIRouter()
    for path, ops in spec()["paths"].items():
        for method, op in ops.items():
            if method not in ("get", "post") or op["operationId"] in implemented:
                continue

            router.add_api_route(path, _not_implemented(op), methods=[method.upper()], operation_id=op["operationId"],
                                 summary=op.get("summary"), tags=["尚未實作"],
                                 openapi_extra={k: v for k, v in op.items() if k in ("requestBody", "responses", "parameters") or k.startswith("x-")})
    return router


def _not_implemented(op: dict):
    def handler():
        return JSONResponse(status_code=501, content={
            "detail": "尚未實作", "operationId": op["operationId"], "x-concept": op.get("x-concept")})
    return handler
