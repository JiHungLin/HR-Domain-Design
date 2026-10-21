"""hire-employee 與 annual-leave-grant API。執行：uv run uvicorn app.main:app --reload"""
from fastapi import FastAPI

from app import errors, spec, stubs
from app.leave import handlers  # noqa: F401 — 註冊特休在 hire-employee 動作上的掛勾（05_mapping D-04）
from app.routers import leave, uc01

app = FastAPI(title="hire-employee、annual-leave-grant API", version=spec.spec()["info"]["version"],
              description="依 slices/hire-employee/、slices/annual-leave-grant/ 的 05_mapping.md、api.yaml 實作；"
                          "還沒實作的 API 回 501（README.md）。")
errors.install(app)
app.include_router(uc01.router)
app.include_router(leave.router)
app.include_router(stubs.router_for_missing(uc01.router, leave.router))


def _openapi():
    """OpenAPI 文件：路由沿用 api.yaml 的請求與回應，components 也直接取自 api.yaml。"""
    if app.openapi_schema is None:
        from fastapi.openapi.utils import get_openapi
        doc = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        for ops in doc["paths"].values():
            for op in ops.values():
                src = spec.operations().get(op.get("operationId"))
                if src:
                    for k in ("requestBody", "responses"):
                        if k in src[2]:
                            op[k] = src[2][k]
        doc["components"] = spec.components()
        doc["security"] = spec.spec().get("security", [])
        app.openapi_schema = doc
    return app.openapi_schema


app.openapi = _openapi
