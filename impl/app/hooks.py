"""其他切片掛在 hire-employee 動作上的處理：在同一個交易中執行，失敗時整個動作一起失敗。

依 annual-leave-grant 05_mapping D-04 與第二節「core 事件的連鎖」：到職、更正到職日／員工類型／結束日、
到職後立刻離開、註銷與撤銷註銷，要在 hire-employee 的 API 同一交易中執行特休的重新判定與驗證；
hire-employee 的設計文件與 api.yaml 不改，回應格式不變。

annual-leave-grant 的處理在 app/leave/handlers.py 註冊（app/main.py import 時）：到職、更正到職日（POST /v1/corrections
目前只實作 start_date）、EmploymentEnded。註銷、撤銷註銷、到職後立刻離開的 API 還沒實作，實作時照下面的種類呼叫。
"""
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field

from bson import ObjectId

# 事件種類 → 呼叫的位置（annual-leave-grant 05_mapping「core 事件的連鎖」）
EMPLOYMENT_STARTED = "EmploymentStarted"      # StartEmployment（已呼叫）、RegisterExistingEmployment（尚未實作）
EMPLOYMENT_ENDED = "EmploymentEnded"          # RecordEarlyDeparture、LoadEmploymentEndingFixture（尚未實作）
EMPLOYMENT_CORRECTED = "EmploymentCorrected"  # CorrectRecord：employments 的 start_date（已呼叫）、employee_category、ended_on
EVENT_ANNULLED = "EventAnnulled"              # AnnulEntry、RevokeAnnulment：StartEmployment、RegisterExistingEmployment、
                                              # RecordEarlyDeparture 等（尚未實作）
EMPLOYER_CHANGED = "EmployerChanged"          # CorrectRecord、LoadEmployerFixture：employers 的 system_managed_from、
                                              # labor_standards_act_applicable（尚未實作；特休那邊改走佇列分批，D-18）


@dataclass(frozen=True)
class HookEvent:
    kind: str
    tenant_id: ObjectId
    event_id: ObjectId                 # 觸發它的 hire-employee 事件，也是特休通知的 root_event_id
    employment_id: ObjectId | None = None
    employer_id: ObjectId | None = None
    fields: tuple[str, ...] = ()       # 更正時改了哪些欄位
    extra: dict = field(default_factory=dict)


Handler = Callable[[object, object, HookEvent], None]   # (db, session, event)

_handlers: dict[str, list[Handler]] = {}


def register(kind: str, handler: Handler) -> None:
    _handlers.setdefault(kind, []).append(handler)


def unregister(kind: str, handler: Handler) -> None:
    _handlers.get(kind, []).remove(handler)


@contextmanager
def registered(kind: str, handler: Handler):
    register(kind, handler)
    try:
        yield
    finally:
        unregister(kind, handler)


def publish(db, session, event: HookEvent) -> None:
    """在呼叫者的交易（session）中依註冊順序執行；處理丟出例外（例：Blocked）時，整個交易回滾。"""
    for handler in list(_handlers.get(event.kind, ())):
        handler(db, session, event)
