"""hire-employee API。執行：uv run uvicorn app.main:app --reload"""
from fastapi import FastAPI

from app import errors, stubs
from app.routers import uc01

app = FastAPI(title="hire-employee API", version="0.1.0",
              description="依 slices/hire-employee/05_mapping.md、api.yaml 實作。已實作 UC-01～UC-03，其餘 API 回 501。")
errors.install(app)
app.include_router(uc01.router)
app.include_router(stubs.router_for_missing(uc01.router))
