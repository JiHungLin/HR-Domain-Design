"""呼叫者身分：bearer token 對應 user_accounts（05_mapping D-09）。

開發用：token 直接是 user_accounts.user_id，沒有簽章驗證。正式的登入方式由平台決定。
"""
from dataclasses import dataclass, field

from bson import ObjectId
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import database
from app.errors import Forbidden


@dataclass
class Actor:
    user_id: str
    account_id: ObjectId
    tenant_id: ObjectId
    roles: list[str] = field(default_factory=list)
    person_id: ObjectId | None = None

    def require(self, *roles: str) -> None:
        if not set(roles) & set(self.roles):
            raise Forbidden(f"需要角色 {'／'.join(roles)}")

    @property
    def event_actor(self) -> dict:
        """events.actor：user_id 指 user_accounts 的 _id。"""
        return {"user_id": self.account_id, "role": self.roles[0]}


bearer = HTTPBearer(auto_error=False)   # api.yaml securitySchemes.bearer


def current_actor(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Actor:
    if cred is None:
        raise Forbidden("缺少 bearer token")
    token = cred.credentials
    acc = database().user_accounts.find_one({"user_id": token})
    if not acc:
        raise Forbidden("帳號不存在")
    return Actor(user_id=token, account_id=acc["_id"], tenant_id=acc["tenant_id"], roles=acc["roles"], person_id=acc.get("person_id"))


def hr(actor: Actor = Depends(current_actor)) -> Actor:
    actor.require("HR")
    return actor
