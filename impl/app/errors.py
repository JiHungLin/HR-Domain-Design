"""錯誤回應：403 Forbidden、409 Blocked（api.yaml components.responses）。"""
from fastapi import Request
from fastapi.responses import JSONResponse


class Blocked(Exception):
    """違反「擋下」類規則，或狀態不允許這個動作（P1）。"""

    def __init__(self, rule_id: str | None, message_code: str, detail: str = ""):
        self.rule_id, self.message_code, self.detail = rule_id, message_code, detail


class Superseded(Exception):
    """annual-leave-grant：待確認的轉換已被取代（api.yaml Superseded）。"""

    def __init__(self, message_code: str, discarded_by_id=None):
        self.message_code, self.discarded_by_id = message_code, discarded_by_id


class Forbidden(Exception):
    def __init__(self, detail: str = ""):
        self.detail = detail


class NotFound(Exception):
    def __init__(self, detail: str = ""):
        self.detail = detail


def install(app):
    from app.spec import RequestInvalid

    @app.exception_handler(RequestInvalid)
    def _invalid(_: Request, e: RequestInvalid):
        return JSONResponse(status_code=422, content={"detail": e.errors})

    @app.exception_handler(Blocked)
    def _blocked(_: Request, e: Blocked):
        return JSONResponse(status_code=409, content={"rule_id": e.rule_id, "message_code": e.message_code, "detail": e.detail})

    @app.exception_handler(Superseded)
    def _superseded(_: Request, e: Superseded):
        if e.discarded_by_id is None:
            # 暫時：取代後差額為 0、沒有新的一筆時沒有 discarded_by_id，Superseded 格式要求必填（signoff.md #13）
            return JSONResponse(status_code=409, content={"rule_id": None, "message_code": e.message_code,
                                                          "detail": "已被取代，重算後沒有新的轉換"})
        return JSONResponse(status_code=409, content={"message_code": e.message_code, "discarded_by_id": str(e.discarded_by_id)})

    @app.exception_handler(Forbidden)
    def _forbidden(_: Request, e: Forbidden):
        return JSONResponse(status_code=403, content={"detail": e.detail})

    @app.exception_handler(NotFound)
    def _not_found(_: Request, e: NotFound):
        return JSONResponse(status_code=404, content={"detail": e.detail})
